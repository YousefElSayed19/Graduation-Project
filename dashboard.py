import threading

from flask import Blueprint, render_template, request, jsonify, url_for, redirect, flash
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
    return render_template("dashboard.html", recent_scans=recent_scans)


@dashboard_bp.route("/api/scan/start", methods=["POST"])
@login_required
def start_scan():
    target_url = request.json.get("target_url", "").strip()

    if not target_url:
        return jsonify({"error": "Please enter a target URL"}), 400

    if not target_url.startswith(("http://", "https://")):
        target_url = "http://" + target_url

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
    if not state:
        return jsonify({"error": "Scan not found"}), 404
    return jsonify({"status": state["status"], "findings": state["findings"]})
