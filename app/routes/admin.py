from functools import wraps
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.utils import slugify
from app.extensions import db
from app.models import (
    User, Movie, TVShow, Season, Episode, Genre, MovieRequest,
    Subscription, Notification,
)
from app.models.admin import log_admin_action
from app.services.storage import storage

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(404)  # never reveal that /admin exists to non-admins
        return fn(*args, **kwargs)
    return wrapper


@bp.route("/")
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    paid_users = Subscription.query.filter_by(status="ACTIVE").join(Subscription.plan).filter_by(code="PREMIUM").count()
    total_movies = Movie.query.count()
    total_shows = TVShow.query.count()
    total_requests = MovieRequest.query.filter(MovieRequest.status.in_(["PENDING", "REVIEWING"])).count()

    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_7d = User.query.filter(User.created_at >= week_ago).count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(6).all()
    recent_requests = MovieRequest.query.order_by(MovieRequest.created_at.desc()).limit(6).all()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        paid_users=paid_users,
        total_movies=total_movies,
        total_shows=total_shows,
        total_requests=total_requests,
        new_users_7d=new_users_7d,
        recent_users=recent_users,
        recent_requests=recent_requests,
    )


# ---------------------------------------------------------------------
# MOVIES
# ---------------------------------------------------------------------
@bp.route("/movies")
@login_required
@admin_required
def movies():
    all_movies = Movie.query.order_by(Movie.created_at.desc()).all()
    return render_template("admin/movies.html", movies=all_movies)


@bp.route("/movies/new", methods=["GET", "POST"])
@login_required
@admin_required
def movie_new():
    genres = Genre.query.order_by(Genre.name).all()
    if request.method == "POST":
        movie = Movie(title="")
        _save_movie_form(movie, genres)
        db.session.add(movie)
        db.session.commit()
        log_admin_action(current_user.id, "create_movie", "movie", movie.id, movie.title)
        flash(f'"{movie.title}" created.', "success")
        return redirect(url_for("admin.movies"))
    return render_template("admin/movie_form.html", movie=None, genres=genres)


@bp.route("/movies/<int:movie_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def movie_edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    genres = Genre.query.order_by(Genre.name).all()
    if request.method == "POST":
        _save_movie_form(movie, genres)
        db.session.commit()
        log_admin_action(current_user.id, "edit_movie", "movie", movie.id, movie.title)
        flash(f'"{movie.title}" updated.', "success")
        return redirect(url_for("admin.movies"))
    return render_template("admin/movie_form.html", movie=movie, genres=genres)


def _unique_slug(model, base_slug, current_id=None):
    slug = base_slug
    n = 2
    while True:
        existing = model.query.filter_by(slug=slug).first()
        if not existing or existing.id == current_id:
            return slug
        slug = f"{base_slug}-{n}"
        n += 1


def _save_movie_form(movie, all_genres):
    movie.title = request.form.get("title", "").strip()
    if movie.title:
        movie.slug = _unique_slug(Movie, slugify(movie.title), movie.id)
    movie.description = request.form.get("description", "").strip()
    movie.release_year = request.form.get("release_year", type=int)
    movie.runtime_minutes = request.form.get("runtime_minutes", type=int)
    movie.age_rating = request.form.get("age_rating", "PG-13")
    movie.language = request.form.get("language", "English")
    movie.country = request.form.get("country", "").strip() or None
    movie.cast = request.form.get("cast", "").strip() or None
    movie.director = request.form.get("director", "").strip() or None
    movie.status = request.form.get("status", "PUBLISHED")
    movie.is_featured = bool(request.form.get("is_featured"))
    movie.is_trending = bool(request.form.get("is_trending"))

    genre_ids = request.form.getlist("genres")
    movie.genres = [g for g in all_genres if str(g.id) in genre_ids]

    poster = request.files.get("poster")
    if poster and poster.filename:
        movie.poster_key = storage.save(poster, "posters")
    backdrop = request.files.get("backdrop")
    if backdrop and backdrop.filename:
        movie.backdrop_key = storage.save(backdrop, "backdrops")
    trailer = request.files.get("trailer")
    if trailer and trailer.filename:
        movie.trailer_key = storage.save(trailer, "trailers")
    video = request.files.get("video")
    if video and video.filename:
        movie.video_key = storage.save(video, "movies")
        movie.processing_state = "READY"  # a real pipeline would set PROCESSING then flip this via a background job
    subtitle = request.files.get("subtitle")
    if subtitle and subtitle.filename:
        movie.subtitle_key = storage.save(subtitle, "subtitles")


@bp.route("/movies/<int:movie_id>/delete", methods=["POST"])
@login_required
@admin_required
def movie_delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    title = movie.title
    db.session.delete(movie)
    db.session.commit()
    log_admin_action(current_user.id, "delete_movie", "movie", movie_id, title)
    flash(f'"{title}" deleted.', "info")
    return redirect(url_for("admin.movies"))


# ---------------------------------------------------------------------
# TV SHOWS
# ---------------------------------------------------------------------
@bp.route("/shows")
@login_required
@admin_required
def shows():
    all_shows = TVShow.query.order_by(TVShow.created_at.desc()).all()
    return render_template("admin/shows.html", shows=all_shows)


@bp.route("/shows/new", methods=["GET", "POST"])
@login_required
@admin_required
def show_new():
    genres = Genre.query.order_by(Genre.name).all()
    if request.method == "POST":
        show = TVShow(title="")
        _save_show_form(show, genres)
        db.session.add(show)
        db.session.commit()
        log_admin_action(current_user.id, "create_show", "tv_show", show.id, show.title)
        flash(f'"{show.title}" created. Now add seasons and episodes.', "success")
        return redirect(url_for("admin.show_edit", show_id=show.id))
    return render_template("admin/show_form.html", show=None, genres=genres)


@bp.route("/shows/<int:show_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def show_edit(show_id):
    show = TVShow.query.get_or_404(show_id)
    genres = Genre.query.order_by(Genre.name).all()
    if request.method == "POST":
        _save_show_form(show, genres)
        db.session.commit()
        flash(f'"{show.title}" updated.', "success")
        return redirect(url_for("admin.show_edit", show_id=show.id))
    return render_template("admin/show_form.html", show=show, genres=genres)


def _save_show_form(show, all_genres):
    show.title = request.form.get("title", "").strip()
    if show.title:
        show.slug = _unique_slug(TVShow, slugify(show.title), show.id)
    show.description = request.form.get("description", "").strip()
    show.first_air_year = request.form.get("first_air_year", type=int)
    show.age_rating = request.form.get("age_rating", "PG-13")
    show.language = request.form.get("language", "English")
    show.cast = request.form.get("cast", "").strip() or None
    show.director = request.form.get("director", "").strip() or None
    show.status = request.form.get("status", "PUBLISHED")
    show.is_featured = bool(request.form.get("is_featured"))
    show.is_trending = bool(request.form.get("is_trending"))

    genre_ids = request.form.getlist("genres")
    show.genres = [g for g in all_genres if str(g.id) in genre_ids]

    poster = request.files.get("poster")
    if poster and poster.filename:
        show.poster_key = storage.save(poster, "posters")
    backdrop = request.files.get("backdrop")
    if backdrop and backdrop.filename:
        show.backdrop_key = storage.save(backdrop, "backdrops")


@bp.route("/shows/<int:show_id>/seasons/add", methods=["POST"])
@login_required
@admin_required
def season_add(show_id):
    show = TVShow.query.get_or_404(show_id)
    number = max([s.number for s in show.seasons], default=0) + 1
    db.session.add(Season(show_id=show.id, number=number, title=f"Season {number}"))
    db.session.commit()
    flash(f"Season {number} added.", "success")
    return redirect(url_for("admin.show_edit", show_id=show.id))


@bp.route("/seasons/<int:season_id>/episodes/add", methods=["POST"])
@login_required
@admin_required
def episode_add(season_id):
    season = Season.query.get_or_404(season_id)
    number = max([e.number for e in season.episodes], default=0) + 1
    title = request.form.get("title", f"Episode {number}").strip()
    description = request.form.get("description", "").strip()
    duration = request.form.get("duration_minutes", type=int) or 45

    episode = Episode(season_id=season.id, number=number, title=title, description=description, duration_minutes=duration)

    video = request.files.get("video")
    if video and video.filename:
        episode.video_key = storage.save(video, "tv")
    thumb = request.files.get("thumbnail")
    if thumb and thumb.filename:
        episode.thumbnail_key = storage.save(thumb, "posters")

    db.session.add(episode)
    db.session.commit()
    flash(f'"{title}" added to Season {season.number}.', "success")
    return redirect(url_for("admin.show_edit", show_id=season.show_id))


@bp.route("/shows/<int:show_id>/delete", methods=["POST"])
@login_required
@admin_required
def show_delete(show_id):
    show = TVShow.query.get_or_404(show_id)
    title = show.title
    db.session.delete(show)
    db.session.commit()
    log_admin_action(current_user.id, "delete_show", "tv_show", show_id, title)
    flash(f'"{title}" deleted.', "info")
    return redirect(url_for("admin.shows"))


# ---------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------
@bp.route("/users")
@login_required
@admin_required
def users():
    q = request.args.get("q", "").strip()
    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter((User.username.ilike(like)) | (User.email.ilike(like)) | (User.full_name.ilike(like)))
    all_users = query.order_by(User.created_at.desc()).limit(200).all()
    return render_template("admin/users.html", users=all_users, q=q)


@bp.route("/users/<int:user_id>/toggle-suspend", methods=["POST"])
@login_required
@admin_required
def toggle_suspend(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot suspend your own account.", "error")
        return redirect(url_for("admin.users"))
    user.is_suspended = not user.is_suspended
    db.session.commit()
    log_admin_action(current_user.id, "toggle_suspend", "user", user.id, str(user.is_suspended))
    flash(f'{user.username} {"suspended" if user.is_suspended else "unsuspended"}.', "info")
    return redirect(url_for("admin.users"))


# ---------------------------------------------------------------------
# REQUESTS
# ---------------------------------------------------------------------
@bp.route("/requests")
@login_required
@admin_required
def requests_view():
    all_requests = MovieRequest.query.order_by(MovieRequest.created_at.desc()).all()
    return render_template("admin/requests.html", requests=all_requests)


@bp.route("/requests/<int:request_id>/status", methods=["POST"])
@login_required
@admin_required
def request_status(request_id):
    req = MovieRequest.query.get_or_404(request_id)
    new_status = request.form.get("status")
    if new_status in ("PENDING", "REVIEWING", "APPROVED", "PROCESSING", "ADDED", "DECLINED"):
        req.status = new_status
        req.admin_notes = request.form.get("admin_notes", req.admin_notes)
        db.session.commit()

        if new_status == "ADDED":
            db.session.add(Notification(
                user_id=req.user_id,
                kind="request_added",
                title="Your requested title is here!",
                body=f'"{req.title}" was just added to Poloflix.',
                link="/movies",
            ))
            db.session.commit()

        log_admin_action(current_user.id, "update_request_status", "movie_request", req.id, new_status)
        flash("Request updated.", "success")
    return redirect(url_for("admin.requests_view"))
