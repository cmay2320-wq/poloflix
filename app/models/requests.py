from datetime import datetime
from app.extensions import db

REQUEST_STATUSES = ("PENDING", "REVIEWING", "APPROVED", "PROCESSING", "ADDED", "DECLINED")


class MovieRequest(db.Model):
    __tablename__ = "movie_requests"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    media_type = db.Column(db.String(10), default="movie")  # movie / tv
    release_year = db.Column(db.Integer, nullable=True)
    reference_link = db.Column(db.String(300), nullable=True)  # imdb/tmdb link
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="PENDING")
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    votes = db.relationship("RequestVote", backref="request", cascade="all, delete-orphan")

    @property
    def vote_count(self):
        return len(self.votes)


class RequestVote(db.Model):
    __tablename__ = "request_votes"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("movie_requests.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("request_id", "user_id", name="uq_request_vote"),)
