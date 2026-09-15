from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Profile
from app.services.storage import storage

bp = Blueprint("account", __name__, url_prefix="/account")


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        form = request.form.get("form_name")

        if form == "profile_info":
            current_user.full_name = request.form.get("full_name", current_user.full_name).strip()
            db.session.commit()
            flash("Account details updated.", "success")

        elif form == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_new_password", "")
            if not current_user.check_password(current_pw):
                flash("Current password is incorrect.", "error")
            elif len(new_pw) < 8:
                flash("New password must be at least 8 characters.", "error")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.", "error")
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash("Password changed.", "success")

        elif form == "avatar":
            file = request.files.get("avatar")
            if file and file.filename:
                key = storage.save(file, "avatars")
                profile = current_user.profiles[0] if current_user.profiles else None
                if profile:
                    profile.avatar_path = key
                    db.session.commit()
                flash("Profile photo updated.", "success")

        return redirect(url_for("account.index"))

    return render_template("account.html")


@bp.route("/profiles/add", methods=["POST"])
@login_required
def add_profile():
    limit = current_user.subscription.plan.max_profiles if (current_user.subscription and current_user.subscription.plan) else 1
    if len(current_user.profiles) >= limit:
        flash(f"Your plan allows up to {limit} profile(s). Upgrade to add more.", "error")
        return redirect(url_for("account.index"))

    name = request.form.get("name", "").strip()
    is_kids = bool(request.form.get("is_kids"))
    if name:
        db.session.add(Profile(user_id=current_user.id, name=name, is_kids=is_kids, maturity_level="ALL" if is_kids else "MATURE"))
        db.session.commit()
        flash("Profile added.", "success")
    return redirect(url_for("account.index"))


@bp.route("/profiles/<int:profile_id>/delete", methods=["POST"])
@login_required
def delete_profile(profile_id):
    profile = Profile.query.filter_by(id=profile_id, user_id=current_user.id).first_or_404()
    if len(current_user.profiles) <= 1:
        flash("You must keep at least one profile.", "error")
    else:
        db.session.delete(profile)
        db.session.commit()
        flash("Profile removed.", "info")
    return redirect(url_for("account.index"))
