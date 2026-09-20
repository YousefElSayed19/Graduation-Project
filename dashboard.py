import json
import threading
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user

from extensions import db
from models import Scan
from scan_manager import scan_manager
from main import run_scan

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    recent_scans = (
        Scan.query.filter_by(user_id=current_user.id)
        .order_by(Scan.started_at.desc())
        .limit(10)
        .all()
    )
    scans_today = _scans_used_today(current_user.id)
    return render_template(
        "dashboard.html",
        recent_scans=recent_scans,
        scans_today=scans_today,
        scan_limit=current_user.scan_limit_per_day,
    )


@dashboard_bp.route("/dashboard/scans/<scan_uid>")
@login_required
def scan_detail(scan_uid):
    scan_record = Scan.query.filter_by(scan_uid=scan_uid, user_id=current_user.id).first()
    if not scan_record:
        abort(404)

    findings = json.loads(scan_record.findings_json) if scan_record.findings_json else []

    # if the scan is still live in memory (server hasn't restarted since), prefer live logs
    live_state = scan_manager.get_state(scan_uid)
    logs = live_state["logs"] if live_state else []

    return render_template("scan_detail.html", scan=scan_record, findings=findings, logs=logs)


def _scans_used_today(user_id):
    since = datetime.utcnow() - timedelta(hours=24)
    return Scan.query.filter(Scan.user_id == user_id, Scan.started_at >= since).count()


@dashboard_bp.route("/api/scan/start", methods=["POST"])
@login_required
def start_scan():
    target_url = request.json.get("target_url", "").strip()

    if not target_url:
        return jsonify({"error": "Please enter a target URL"}), 400

    if not target_url.startswith(("http://", "https://")):
        target_url = "http://" + target_url

    scans_today = _scans_used_today(current_user.id)
    if scans_today >= current_user.scan_limit_per_day:
        return jsonify({
            "error": (
                f"You've hit your {current_user.plan_label} plan's daily limit "
                f"({current_user.scan_limit_per_day} scans/24h). Upgrade on the Pricing page for more."
            )
        }), 403

    scan_uid = scan_manager.create_scan(target_url, current_user.id)

    scan_record = Scan(scan_uid=scan_uid, target_url=target_url, status="running", user_id=current_user.id)
    db.session.add(scan_record)
    db.session.commit()

    # run the scan on a separate thread so the dashboard stays responsive
    thread = threading.Thread(target=_run_and_persist, args=(target_url, scan_uid), daemon=True)
    thread.start()

    return jsonify({"scan_uid": scan_uid})


def _run_and_persist(target_url, scan_uid):
    """Runs on a background thread; updates the DB with the final result once the scan finishes."""
    from app import create_app  # avoid a circular import

    app = create_app()
    with app.app_context():
        findings = run_scan(target_url, scan_uid)

        scan_record = Scan.query.filter_by(scan_uid=scan_uid).first()
        if scan_record:
            scan_record.status = "done"
            scan_record.findings_count = len(findings)
            scan_record.findings_json = json.dumps(findings)
            scan_record.finished_at = datetime.utcnow()
            db.session.commit()


@dashboard_bp.route("/api/scan/<scan_uid>/logs")
@login_required
def get_logs(scan_uid):
    since = int(request.args.get("since", 0))
    logs, next_index, status = scan_manager.get_logs_since(scan_uid, since)
    return jsonify({"logs": logs, "next_index": next_index, "status": status})


@dashboard_bp.route("/api/scan/<scan_uid>/results")
@login_required
def get_results(scan_uid):
    state = scan_manager.get_state(scan_uid)
    if state:
        return jsonify({"status": state["status"], "findings": state["findings"]})

    # fall back to the persisted DB record (e.g. after a server restart)
    scan_record = Scan.query.filter_by(scan_uid=scan_uid, user_id=current_user.id).first()
    if not scan_record:
        return jsonify({"error": "Scan not found"}), 404

    findings = json.loads(scan_record.findings_json) if scan_record.findings_json else []
    return jsonify({"status": scan_record.status, "findings": findings})
