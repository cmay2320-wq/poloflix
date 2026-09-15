from datetime import datetime
from app.extensions import db


class AdminAuditLog(db.Model):
    __tablename__ = "admin_audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(120), nullable=False)
    target_type = db.Column(db.String(60), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.String(400), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship("User")


def log_admin_action(admin_id, action, target_type=None, target_id=None, details=None):
    entry = AdminAuditLog(
        admin_id=admin_id, action=action, target_type=target_type, target_id=target_id, details=details
    )
    db.session.add(entry)
    db.session.commit()
    return entry
