"""Database models."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def utcnow():
    """Naive UTC timestamp (stored without tzinfo)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Metric(db.Model):
    __tablename__ = "metrics"

    id = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    cpu = db.Column(db.Float, nullable=False)
    memory = db.Column(db.Float, nullable=False)
    disk = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "timestamp": self.ts.isoformat() + "Z",
            "cpu": self.cpu,
            "memory": self.memory,
            "disk": self.disk,
        }
