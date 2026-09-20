from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db, oauth
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=username).first():
            flash("This username is already taken.", "danger")
            return redirect(url_for("auth.register"))

        user = User(username=username, email=email, auth_provider="local")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created successfully!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Incorrect email or password.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("dashboard.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("main.landing"))


# ---------------- Google OAuth ----------------
# Requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env for this to
# actually work (see .env.example).

@auth_bp.route("/login/google")
def login_google():
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        flash("Google login isn't configured yet — set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env", "warning")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/login/google/callback")
def google_callback():
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        return redirect(url_for("auth.login"))

    token = oauth.google.authorize_access_token()
    user_info = token.get("userinfo")

    if not user_info:
        flash("Google sign-in failed.", "danger")
        return redirect(url_for("auth.login"))

    email = user_info["email"].lower()
    user = User.query.filter_by(email=email).first()

    if not user:
        base_username = user_info.get("name", email.split("@")[0]).replace(" ", "_")
        username = base_username
        suffix = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{suffix}"
            suffix += 1

        user = User(username=username, email=email, auth_provider="google")
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for("dashboard.index"))
