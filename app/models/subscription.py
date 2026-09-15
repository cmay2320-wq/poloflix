from datetime import datetime
from app.extensions import db


class Plan(db.Model):
    __tablename__ = "plans"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # FREE / PREMIUM
    name = db.Column(db.String(60), nullable=False)
    price_cents = db.Column(db.Integer, default=0)
    max_quality = db.Column(db.String(10), default="720p")
    max_streams = db.Column(db.Integer, default=1)
    max_profiles = db.Column(db.Integer, default=1)
    has_ads = db.Column(db.Boolean, default=True)

    subscriptions = db.relationship("Subscription", backref="plan")


class Subscription(db.Model):
    __tablename__ = "subscriptions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    status = db.Column(db.String(20), default="ACTIVE")  # ACTIVE / CANCELLED / PAST_DUE
    provider = db.Column(db.String(30), nullable=True)  # e.g. "stripe" - added when you integrate one
    provider_customer_id = db.Column(db.String(120), nullable=True)
    provider_subscription_id = db.Column(db.String(120), nullable=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    renewal_date = db.Column(db.DateTime, nullable=True)
    cancellation_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
