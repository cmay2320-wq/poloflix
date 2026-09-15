from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, limiter
from app.models import User, Profile, Plan, Subscription

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        terms = request.form.get("terms")

        error = None
        if not all([full_name, username, email, password, confirm]):
            error = "Please fill in every field."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif not terms:
            error = "You must accept the Terms to create an account."
        elif User.query.filter_by(username=username).first():
            error = "That username is already taken."
        elif User.query.filter_by(email=email).first():
            error = "That email is already registered."

        if error:
            flash(error, "error")
            return render_template("auth/register.html", form=request.form)

        user = User(full_name=full_name, username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        free_plan = Plan.query.filter_by(code="FREE").first()
        if free_plan:
            db.session.add(Subscription(user_id=user.id, plan_id=free_plan.id, status="ACTIVE"))

        db.session.add(Profile(user_id=user.id, name=full_name.split(" ")[0] or username))
        db.session.commit()

        login_user(user)
        flash("Welcome to Poloflix!", "success")
        return redirect(url_for("home.index"))

    return render_template("auth/register.html", form={})


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (User.email == identifier) | (User.username == identifier)
        ).first()

        if user and not user.is_suspended and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            next_url = request.args.get("next")
            return redirect(next_url or url_for("home.index"))

        flash("Incorrect email/username or password.", "error")

    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("home.index"))
