from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Watchlist, WatchProgress, Movie, TVShow, Rating

bp = Blueprint("lists", __name__)


@bp.route("/my-list")
@login_required
def my_list():
    items = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.created_at.desc()).all()
    resolved = []
    for item in items:
        media = Movie.query.get(item.media_id) if item.media_type == "movie" else TVShow.query.get(item.media_id)
        if media:
            resolved.append({"media": media, "media_type": item.media_type, "added_at": item.created_at})
    return render_template("my_list.html", items=resolved)


@bp.route("/api/watchlist/toggle", methods=["POST"])
@login_required
def toggle_watchlist():
    data = request.get_json(force=True, silent=True) or {}
    media_type = data.get("media_type")
    media_id = data.get("media_id")
    if media_type not in ("movie", "tv") or not media_id:
        return jsonify({"error": "invalid payload"}), 400

    existing = Watchlist.query.filter_by(user_id=current_user.id, media_type=media_type, media_id=media_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"in_list": False})

    db.session.add(Watchlist(user_id=current_user.id, media_type=media_type, media_id=media_id))
    db.session.commit()
    return jsonify({"in_list": True})


@bp.route("/api/progress", methods=["POST"])
@login_required
def save_progress():
    data = request.get_json(force=True, silent=True) or {}
    media_type = data.get("media_type")
    media_id = data.get("media_id")
    position = int(data.get("position", 0))
    duration = int(data.get("duration", 0))
    if media_type not in ("movie", "episode") or not media_id:
        return jsonify({"error": "invalid payload"}), 400

    progress = WatchProgress.query.filter_by(user_id=current_user.id, media_type=media_type, media_id=media_id).first()
    if not progress:
        progress = WatchProgress(user_id=current_user.id, media_type=media_type, media_id=media_id)
        db.session.add(progress)

    progress.position_seconds = position
    progress.duration_seconds = duration or progress.duration_seconds
    if duration and position / max(duration, 1) >= 0.9:
        progress.completed = True
    db.session.commit()
    return jsonify({"ok": True, "completed": progress.completed})


@bp.route("/api/rating", methods=["POST"])
@login_required
def save_rating():
    data = request.get_json(force=True, silent=True) or {}
    media_type = data.get("media_type")
    media_id = data.get("media_id")
    score = data.get("score")
    if media_type not in ("movie", "tv") or not media_id or not score:
        return jsonify({"error": "invalid payload"}), 400

    rating = Rating.query.filter_by(user_id=current_user.id, media_type=media_type, media_id=media_id).first()
    if not rating:
        rating = Rating(user_id=current_user.id, media_type=media_type, media_id=media_id, score=float(score))
        db.session.add(rating)
    else:
        rating.score = float(score)
    db.session.commit()

    # keep the title's average rating in sync
    model = Movie if media_type == "movie" else TVShow
    media = model.query.get(media_id)
    if media:
        all_scores = [r.score for r in Rating.query.filter_by(media_type=media_type, media_id=media_id, is_hidden=False).all()]
        media.rating = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0
        db.session.commit()

    return jsonify({"ok": True, "average": media.rating if media else None})
