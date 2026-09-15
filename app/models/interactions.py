from datetime import datetime
from app.extensions import db


class Watchlist(db.Model):
    __tablename__ = "watchlist"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)  # "movie" or "tv"
    media_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "media_type", "media_id", name="uq_watchlist_item"),)


class WatchProgress(db.Model):
    __tablename__ = "watch_progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)  # "movie" or "episode"
    media_id = db.Column(db.Integer, nullable=False)
    position_seconds = db.Column(db.Integer, default=0)
    duration_seconds = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    last_watched_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "media_type", "media_id", name="uq_progress_item"),)

    @property
    def percent(self):
        if not self.duration_seconds:
            return 0
        return min(100, int(100 * self.position_seconds / self.duration_seconds))


class Rating(db.Model):
    __tablename__ = "ratings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)
    media_id = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)  # 0-10
    review_text = db.Column(db.Text, nullable=True)
    is_hidden = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "media_type", "media_id", name="uq_rating_item"),)
