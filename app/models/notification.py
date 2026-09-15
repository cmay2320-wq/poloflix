from datetime import datetime
from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    kind = db.Column(db.String(40), default="general")  # new_content, request_added, security, announcement...
    title = db.Column(db.String(150), nullable=False)
    body = db.Column(db.String(400), nullable=True)
    link = db.Column(db.String(300), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
