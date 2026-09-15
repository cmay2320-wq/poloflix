"""
Storage abstraction layer.
=================================================================

Every part of the app that needs a URL for a poster, backdrop, avatar,
video, or subtitle file calls:

    storage.url_for(key, container="posters")

...and never builds a file path or URL by hand. `key` is a small
string stored in the database (e.g. "the-last-kingdom.jpg"), not a
full path.

Today STORAGE_BACKEND=local, so files live on disk under
instance/media/<container>/<key> and are served by Flask itself
through the /media/<container>/<filename> route in app/routes/media.py.

WHEN YOU'RE READY TO ADD AZURE BLOB STORAGE:
1. `pip install azure-storage-blob`
2. Create your Storage Account + containers (see README "Adding Azure
   Blob Storage" section for exact names/commands).
3. Set these environment variables:
       STORAGE_BACKEND=azure
       AZURE_STORAGE_CONNECTION_STRING=<from the Azure portal>
4. Restart the app.

That's it - no route, template, or model changes. Every page already
calls storage.url_for(...), which will start returning short-lived
signed SAS URLs pointing at Blob Storage/CDN instead of local paths.
Uploads (app/routes/admin.py) already call storage.save(...), which
will start writing to Blob Storage instead of disk.
"""
import os
import uuid
from datetime import datetime, timedelta

from flask import current_app, url_for


class LocalStorageBackend:
    """Default backend: files on the local disk, served by Flask."""

    def _root(self):
        return current_app.config["LOCAL_MEDIA_ROOT"]

    def _ensure_dir(self, container):
        path = os.path.join(self._root(), container)
        os.makedirs(path, exist_ok=True)
        return path

    def save(self, file_storage, container, filename=None):
        """Save an uploaded werkzeug FileStorage. Returns the storage key."""
        directory = self._ensure_dir(container)
        ext = ""
        if "." in file_storage.filename:
            ext = "." + file_storage.filename.rsplit(".", 1)[1].lower()
        key = filename or f"{uuid.uuid4().hex}{ext}"
        file_storage.save(os.path.join(directory, key))
        return key

    def save_bytes(self, data: bytes, container, filename):
        directory = self._ensure_dir(container)
        with open(os.path.join(directory, filename), "wb") as f:
            f.write(data)
        return filename

    def delete(self, key, container):
        if not key:
            return
        path = os.path.join(self._root(), container, key)
        if os.path.exists(path):
            os.remove(path)

    def url_for(self, key, container):
        if not key:
            return None
        return url_for("media.serve", container=container, filename=key)

    def exists(self, key, container):
        if not key:
            return False
        return os.path.exists(os.path.join(self._root(), container, key))


class AzureBlobStorageBackend:
    """
    Production backend: Azure Blob Storage with short-lived SAS URLs.

    Import of the azure SDK is deferred into __init__ so that local
    development (STORAGE_BACKEND=local) never requires the package
    to be installed.
    """

    def __init__(self):
        try:
            from azure.storage.blob import (
                BlobServiceClient,
                generate_blob_sas,
                BlobSasPermissions,
            )
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "STORAGE_BACKEND=azure requires the azure-storage-blob package. "
                "Run: pip install azure-storage-blob"
            ) from exc

        self._generate_blob_sas = generate_blob_sas
        self._BlobSasPermissions = BlobSasPermissions

        conn_str = current_app.config["AZURE_STORAGE_CONNECTION_STRING"]
        if not conn_str:
            raise RuntimeError(
                "AZURE_STORAGE_CONNECTION_STRING is not set. Add it to your "
                "environment before enabling STORAGE_BACKEND=azure."
            )
        self.client = BlobServiceClient.from_connection_string(conn_str)
        self.account_name = current_app.config["AZURE_STORAGE_ACCOUNT"]
        self.account_key = self.client.credential.account_key
        self.containers = current_app.config["AZURE_CONTAINERS"]
        self.sas_ttl = current_app.config["AZURE_SAS_TTL_SECONDS"]

    def _container_name(self, container):
        return self.containers.get(container, container)

    def save(self, file_storage, container, filename=None):
        ext = ""
        if "." in file_storage.filename:
            ext = "." + file_storage.filename.rsplit(".", 1)[1].lower()
        key = filename or f"{uuid.uuid4().hex}{ext}"
        blob_client = self.client.get_blob_client(
            container=self._container_name(container), blob=key
        )
        blob_client.upload_blob(file_storage.stream, overwrite=True)
        return key

    def save_bytes(self, data: bytes, container, filename):
        blob_client = self.client.get_blob_client(
            container=self._container_name(container), blob=filename
        )
        blob_client.upload_blob(data, overwrite=True)
        return filename

    def delete(self, key, container):
        if not key:
            return
        blob_client = self.client.get_blob_client(
            container=self._container_name(container), blob=key
        )
        if blob_client.exists():
            blob_client.delete_blob()

    def url_for(self, key, container):
        """Returns a short-lived, read-only SAS URL for private media."""
        if not key:
            return None
        container_name = self._container_name(container)
        sas_token = self._generate_blob_sas(
            account_name=self.account_name,
            container_name=container_name,
            blob_name=key,
            account_key=self.account_key,
            permission=self._BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(seconds=self.sas_ttl),
        )
        return f"https://{self.account_name}.blob.core.windows.net/{container_name}/{key}?{sas_token}"

    def exists(self, key, container):
        if not key:
            return False
        blob_client = self.client.get_blob_client(
            container=self._container_name(container), blob=key
        )
        return blob_client.exists()


_backend_cache = {}


def get_storage():
    """Returns the active storage backend, chosen by STORAGE_BACKEND."""
    backend_name = current_app.config["STORAGE_BACKEND"]
    if backend_name not in _backend_cache:
        if backend_name == "azure":
            _backend_cache[backend_name] = AzureBlobStorageBackend()
        else:
            _backend_cache[backend_name] = LocalStorageBackend()
    return _backend_cache[backend_name]


class _StorageProxy:
    """Lets templates/routes just do `from app.services.storage import storage`."""

    def __getattr__(self, name):
        return getattr(get_storage(), name)


storage = _StorageProxy()
