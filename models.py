from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db

PLAN_LABELS = {
    "free": "Free",
    "student": "Student",
    "pro": "Pro",
    "team": "Team",
}


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # nullable for Google sign-ins
    auth_provider = db.Column(db.String(20), default="local")  # local | google
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Plan / billing (demo only — no real payment processor wired up yet)
    plan = db.Column(db.String(20), default="free")  # free | student | pro | team
    billing_cycle = db.Column(db.String(10), nullable=True)  # monthly | annual
    plan_selected_at = db.Column(db.DateTime, nullable=True)

    scans = db.relationship("Scan", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def plan_label(self):
        return PLAN_LABELS.get(self.plan, self.plan.title())

    @property
    def scan_limit_per_day(self):
        return {"free": 3, "student": 15, "pro": 100, "team": 500}.get(self.plan, 3)


class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_uid = db.Column(db.String(36), unique=True, nullable=False)  # uuid used by the API
    target_url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending | running | done | failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    findings_count = db.Column(db.Integer, default=0)
    findings_json = db.Column(db.Text, nullable=True)  # persisted findings, so scan history survives restarts
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
