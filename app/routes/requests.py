from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import MovieRequest, RequestVote

bp = Blueprint("requests", __name__, url_prefix="/requests")

COOLDOWN_MINUTES = 10


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        media_type = request.form.get("media_type", "movie")
        release_year = request.form.get("release_year", type=int)
        reference_link = request.form.get("reference_link", "").strip()
        reason = request.form.get("reason", "").strip()

        if not title:
            flash("Please enter a title.", "error")
            return redirect(url_for("requests.index"))

        recent_cutoff = datetime.utcnow() - timedelta(minutes=COOLDOWN_MINUTES)
        recent = MovieRequest.query.filter(
            MovieRequest.user_id == current_user.id, MovieRequest.created_at >= recent_cutoff
        ).first()
        if recent:
            flash(f"Please wait a few minutes before submitting another request.", "error")
            return redirect(url_for("requests.index"))

        duplicate = MovieRequest.query.filter(MovieRequest.title.ilike(title)).first()
        if duplicate:
            flash("A similar request already exists - you can upvote it instead.", "info")
            return redirect(url_for("requests.index"))

        req = MovieRequest(
            user_id=current_user.id,
            title=title,
            media_type=media_type,
            release_year=release_year,
            reference_link=reference_link or None,
            reason=reason or None,
        )
        db.session.add(req)
        db.session.commit()
        flash("Your request has been submitted!", "success")
        return redirect(url_for("requests.index"))

    my_requests = MovieRequest.query.filter_by(user_id=current_user.id).order_by(MovieRequest.created_at.desc()).all()
    community_requests = (
        MovieRequest.query.filter(MovieRequest.status.in_(["PENDING", "REVIEWING", "APPROVED", "PROCESSING"]))
        .order_by(MovieRequest.created_at.desc())
        .limit(30)
        .all()
    )
    voted_ids = {v.request_id for v in RequestVote.query.filter_by(user_id=current_user.id).all()}

    return render_template(
        "requests.html", my_requests=my_requests, community_requests=community_requests, voted_ids=voted_ids
    )


@bp.route("/<int:request_id>/vote", methods=["POST"])
@login_required
def vote(request_id):
    req = MovieRequest.query.get_or_404(request_id)
    existing = RequestVote.query.filter_by(request_id=req.id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Vote removed.", "info")
    else:
        db.session.add(RequestVote(request_id=req.id, user_id=current_user.id))
        db.session.commit()
        flash("Upvoted!", "success")
    return redirect(url_for("requests.index"))
