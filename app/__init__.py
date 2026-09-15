import os
from flask import Flask
from app.config import config_by_name
from app.extensions import db, login_manager, migrate, csrf, limiter


def create_app(env=None):
    env = env or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name.get(env, config_by_name["development"]))

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["LOCAL_MEDIA_ROOT"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)

    from app.routes.auth import bp as auth_bp
    from app.routes.home import bp as home_bp
    from app.routes.catalog import bp as catalog_bp
    from app.routes.search import bp as search_bp
    from app.routes.player import bp as player_bp
    from app.routes.lists import bp as lists_bp
    from app.routes.requests import bp as requests_bp
    from app.routes.account import bp as account_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.media import bp as media_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(player_bp)
    app.register_blueprint(lists_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(media_bp)

    csrf.exempt(lists_bp)  # AJAX progress/watchlist calls use header-based CSRF token instead

    from app.services.storage import storage
    app.jinja_env.globals["storage"] = storage

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        unread_count = 0
        if current_user.is_authenticated:
            from app.models import Notification
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return {"unread_notification_count": unread_count}

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    return app
