import os
from datetime import timedelta

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    # ---------------------------------------------------------------
    # CORE
    # ---------------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production")

    # ---------------------------------------------------------------
    # DATABASE
    # ---------------------------------------------------------------
    # This is the ONLY place the database engine is chosen. Today it defaults
    # to a local SQLite file so the app runs with zero setup. When you're
    # ready to deploy, set DATABASE_URL in your environment, e.g.:
    #
    #   postgresql+psycopg2://user:password@host:5432/poloflix
    #   mysql+pymysql://user:password@host:3306/poloflix
    #
    # Because everything in this app talks to the database through
    # SQLAlchemy models (never raw engine-specific SQL), swapping the
    # engine is a one-line env var change - no code or model changes
    # needed. Just `pip install psycopg2-binary` (or your driver of
    # choice) and update DATABASE_URL. See README "Switching the
    # database" section.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'poloflix.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # ---------------------------------------------------------------
    # STORAGE (posters, backdrops, avatars, video, subtitles...)
    # ---------------------------------------------------------------
    # "local"  -> files live on disk under instance/media and are served
    #             straight from Flask. Zero setup, great for development.
    # "azure"  -> files live in Azure Blob Storage containers and are
    #             served through short-lived SAS URLs. Flip this switch
    #             (and fill in the AZURE_* vars below) whenever your
    #             blob storage account is ready - no route or template
    #             code changes needed, because every page asks
    #             `storage.url_for(path)` instead of building URLs itself.
    STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")

    LOCAL_MEDIA_ROOT = os.environ.get(
        "LOCAL_MEDIA_ROOT", os.path.join(basedir, "instance", "media")
    )
    LOCAL_MEDIA_URL_PREFIX = "/media"

    # Filled in later, when you create your Azure Storage account.
    AZURE_STORAGE_ACCOUNT = os.environ.get("AZURE_STORAGE_ACCOUNT", "")
    AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    AZURE_SAS_TTL_SECONDS = int(os.environ.get("AZURE_SAS_TTL_SECONDS", "3600"))
    # Container names, matching the doc's recommended layout.
    AZURE_CONTAINERS = {
        "movies": "media-movies",
        "tv": "media-tv",
        "trailers": "media-trailers",
        "subtitles": "media-subtitles",
        "posters": "images-posters",
        "backdrops": "images-backdrops",
        "logos": "images-logos",
        "avatars": "images-avatars",
        "banners": "site-banners",
        "ui": "site-ui-assets",
    }

    # ---------------------------------------------------------------
    # UPLOADS
    # ---------------------------------------------------------------
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024 * 1024  # 4GB ceiling for admin uploads
    ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp"}
    ALLOWED_VIDEO_EXT = {"mp4", "mov", "mkv", "m3u8", "ts"}
    ALLOWED_SUBTITLE_EXT = {"vtt", "srt"}

    # ---------------------------------------------------------------
    # SESSIONS / SECURITY
    # ---------------------------------------------------------------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)
    WTF_CSRF_TIME_LIMIT = None

    # ---------------------------------------------------------------
    # PLANS (free / premium defaults - editable from the admin later)
    # ---------------------------------------------------------------
    PLAN_LIMITS = {
        "FREE": {"max_quality": "720p", "max_streams": 1, "max_profiles": 1, "ads": True},
        "PREMIUM": {"max_quality": "1080p", "max_streams": 4, "max_profiles": 5, "ads": False},
    }


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {"development": DevConfig, "production": ProdConfig}
