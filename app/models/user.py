from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager

ROLE_CHOICES = ("SUPER_ADMIN", "ADMIN", "CONTENT_MANAGER", "MODERATOR", "SUPPORT")


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    is_active_account = db.Column(db.Boolean, default=True)
    is_suspended = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)

    # Simple single-role field for now; upgrade to a many-to-many
    # user_roles table later if you need combinable roles.
    role = db.Column(db.String(30), nullable=True)  # None = regular user
    is_admin_2fa_enabled = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    profiles = db.relationship("Profile", backref="user", cascade="all, delete-orphan")
    watchlist_items = db.relationship("Watchlist", backref="user", cascade="all, delete-orphan")
    watch_progress = db.relationship("WatchProgress", backref="user", cascade="all, delete-orphan")
    ratings = db.relationship("Rating", backref="user", cascade="all, delete-orphan")
    requests = db.relationship("MovieRequest", backref="user", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", cascade="all, delete-orphan")
    subscription = db.relationship("Subscription", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self):
        return self.role in ROLE_CHOICES

    @property
    def plan_code(self):
        if self.subscription and self.subscription.status == "ACTIVE":
            return self.subscription.plan.code if self.subscription.plan else "FREE"
        return "FREE"

    def __repr__(self):
        return f"<User {self.username}>"


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(60), nullable=False)
    avatar_path = db.Column(db.String(255), nullable=True)  # storage key, not raw URL
    language = db.Column(db.String(10), default="en")
    is_kids = db.Column(db.Boolean, default=False)
    maturity_level = db.Column(db.String(20), default="ALL")  # ALL, TEEN, MATURE
    pin_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_pin(self, raw_pin):
        self.pin_hash = generate_password_hash(raw_pin) if raw_pin else None

    def check_pin(self, raw_pin):
        return bool(self.pin_hash) and check_password_hash(self.pin_hash, raw_pin)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
