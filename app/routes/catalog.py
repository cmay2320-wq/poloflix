from flask import Blueprint, render_template, request, abort
from flask_login import current_user
from app.models import Movie, TVShow, Genre, Rating, Watchlist

bp = Blueprint("catalog", __name__)


@bp.route("/movies")
def movies():
    genre_slug = request.args.get("genre")
    query = Movie.query.filter_by(status="PUBLISHED")
    if genre_slug:
        query = query.join(Movie.genres).filter(Genre.slug == genre_slug)
    all_movies = query.order_by(Movie.created_at.desc()).all()

    genres = Genre.query.order_by(Genre.name).all()
    by_genre = []
    for g in genres:
        items = [m for m in g.movies if m.status == "PUBLISHED"]
        if items:
            by_genre.append((g, items))

    return render_template(
        "catalog.html",
        kind="movies",
        title="Movies",
        items=all_movies,
        genres=genres,
        by_genre=by_genre,
        active_genre=genre_slug,
    )


@bp.route("/tv-shows")
def shows():
    genre_slug = request.args.get("genre")
    query = TVShow.query.filter_by(status="PUBLISHED")
    if genre_slug:
        query = query.join(TVShow.genres).filter(Genre.slug == genre_slug)
    all_shows = query.order_by(TVShow.created_at.desc()).all()

    genres = Genre.query.order_by(Genre.name).all()
    by_genre = []
    for g in genres:
        items = [s for s in g.shows if s.status == "PUBLISHED"]
        if items:
            by_genre.append((g, items))

    return render_template(
        "catalog.html",
        kind="tv",
        title="TV Shows",
        items=all_shows,
        genres=genres,
        by_genre=by_genre,
        active_genre=genre_slug,
    )


@bp.route("/movie/<slug>")
def movie_detail(slug):
    movie = Movie.query.filter_by(slug=slug).first_or_404()
    in_list = False
    user_rating = None
    if current_user.is_authenticated:
        in_list = Watchlist.query.filter_by(user_id=current_user.id, media_type="movie", media_id=movie.id).first() is not None
        user_rating = Rating.query.filter_by(user_id=current_user.id, media_type="movie", media_id=movie.id).first()

    related = (
        Movie.query.filter(Movie.id != movie.id, Movie.status == "PUBLISHED")
        .filter(Movie.genres.any(Genre.id.in_([g.id for g in movie.genres])) if movie.genres else True)
        .limit(8)
        .all()
    )
    reviews = Rating.query.filter_by(media_type="movie", media_id=movie.id, is_hidden=False).filter(Rating.review_text.isnot(None)).limit(10).all()

    return render_template(
        "movie_detail.html", movie=movie, in_list=in_list, user_rating=user_rating, related=related, reviews=reviews
    )


@bp.route("/tv/<slug>")
def show_detail(slug):
    show = TVShow.query.filter_by(slug=slug).first_or_404()
    season_number = request.args.get("season", type=int)
    season = None
    if show.seasons:
        season = next((s for s in show.seasons if s.number == season_number), show.seasons[0])

    in_list = False
    watched_episode_ids = set()
    if current_user.is_authenticated:
        in_list = Watchlist.query.filter_by(user_id=current_user.id, media_type="tv", media_id=show.id).first() is not None
        from app.models import WatchProgress
        ep_ids = [e.id for s in show.seasons for e in s.episodes]
        if ep_ids:
            progress = WatchProgress.query.filter(
                WatchProgress.user_id == current_user.id,
                WatchProgress.media_type == "episode",
                WatchProgress.media_id.in_(ep_ids),
            ).all()
            watched_episode_ids = {p.media_id for p in progress if p.completed}

    related = (
        TVShow.query.filter(TVShow.id != show.id, TVShow.status == "PUBLISHED")
        .filter(TVShow.genres.any(Genre.id.in_([g.id for g in show.genres])) if show.genres else True)
        .limit(8)
        .all()
    )

    return render_template(
        "show_detail.html", show=show, season=season, in_list=in_list, watched_episode_ids=watched_episode_ids, related=related
    )
