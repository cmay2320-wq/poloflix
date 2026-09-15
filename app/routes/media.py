from flask import Blueprint, current_app, send_from_directory, abort
import os

bp = Blueprint("media", __name__)


@bp.route("/media/<container>/<path:filename>")
def serve(container, filename):
    """
    Serves locally-stored media. Only reachable when STORAGE_BACKEND=local.
    Once you switch to Azure, storage.url_for() returns direct signed
    Blob Storage URLs and this route is simply unused (safe to leave in
    place).
    """
    if current_app.config["STORAGE_BACKEND"] != "local":
        abort(404)
    root = os.path.join(current_app.config["LOCAL_MEDIA_ROOT"], container)
    if not os.path.isdir(root):
        abort(404)
    return send_from_directory(root, filename)
