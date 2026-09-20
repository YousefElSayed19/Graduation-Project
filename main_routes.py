from flask import Blueprint, render_template

from plans import PLANS

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def landing():
    return render_template("index.html")


@main_bp.route("/features")
def features():
    return render_template("features.html")


@main_bp.route("/pricing")
def pricing():
    return render_template("pricing.html", plans=PLANS)


@main_bp.route("/about")
def about():
    return render_template("about.html")
