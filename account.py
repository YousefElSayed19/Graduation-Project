from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models import Scan
from plans import PLANS, get_plan

account_bp = Blueprint("account", __name__)


@account_bp.route("/account")
@login_required
def index():
    total_scans = Scan.query.filter_by(user_id=current_user.id).count()
    current_plan = get_plan(current_user.plan) or get_plan("free")
    return render_template(
        "account.html",
        current_plan=current_plan,
        total_scans=total_scans,
        plans=PLANS,
    )


@account_bp.route("/account/plan", methods=["POST"])
@login_required
def set_plan():
    plan_id = request.form.get("plan_id", "free")
    billing_cycle = request.form.get("billing_cycle", "monthly")

    if not get_plan(plan_id):
        flash("That plan doesn't exist.", "danger")
        return redirect(url_for("main.pricing"))

    if billing_cycle not in ("monthly", "annual"):
        billing_cycle = "monthly"

    current_user.plan = plan_id
    current_user.billing_cycle = billing_cycle if plan_id != "free" else None
    current_user.plan_selected_at = datetime.utcnow()
    db.session.commit()

    plan_name = get_plan(plan_id)["name"]
    flash(
        f"You're now on the {plan_name} plan ({billing_cycle}). "
        "This is a demo — no real payment was processed.",
        "success",
    )
    return redirect(url_for("account.index"))
