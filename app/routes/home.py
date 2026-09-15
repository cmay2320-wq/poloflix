from flask import Blueprint, render_template
from flask_login import current_user
from app.models import Movie, TVShow, WatchProgress, Genre

bp = Blueprint("home", __name__)


@bp.route("/")
def index():
    featured = Movie.query.filter_by(is_featured=True, status="PUBLISHED").order_by(Movie.id.desc()).limit(6).all()
    if not featured:
        featured = Movie.query.filter_by(status="PUBLISHED").order_by(Movie.id.desc()).limit(6).all()

    trending_movies = Movie.query.filter_by(is_trending=True, status="PUBLISHED").limit(12).all()
    trending_shows = TVShow.query.filter_by(is_trending=True, status="PUBLISHED").limit(12).all()
    trending = (trending_movies + trending_shows)[:14]

    popular_movies = Movie.query.filter_by(status="PUBLISHED").order_by(Movie.rating.desc()).limit(12).all()
    popular_shows = TVShow.query.filter_by(status="PUBLISHED").order_by(TVShow.rating.desc()).limit(12).all()
    recent = Movie.query.filter_by(status="PUBLISHED").order_by(Movie.created_at.desc()).limit(12).all()

    continue_watching = []
    if current_user.is_authenticated:
        progress_rows = (
            WatchProgress.query.filter_by(user_id=current_user.id, completed=False)
            .order_by(WatchProgress.last_watched_at.desc())
            .limit(8)
            .all()
        )
        for p in progress_rows:
            if p.media_type == "movie":
                media = Movie.query.get(p.media_id)
                label = media.title if media else None
                sub = None
            else:
                from app.models import Episode
                ep = Episode.query.get(p.media_id)
                media = ep.season.show if ep else None
                label = media.title if media else None
                sub = f"S{ep.season.number} E{ep.number} \u00b7 {ep.duration_minutes}m" if ep else None
            if media:
                continue_watching.append({"media": media, "progress": p, "label": label, "sub": sub})

    genre_rows = []
    for g in Genre.query.limit(6).all():
        movies_in_genre = [m for m in g.movies if m.status == "PUBLISHED"][:12]
        if movies_in_genre:
            genre_rows.append((g.name, movies_in_genre))

    return render_template(
        "home.html",
        featured=featured,
        trending=trending,
        popular_movies=popular_movies,
        popular_shows=popular_shows,
        recent=recent,
        continue_watching=continue_watching,
        genre_rows=genre_rows,
    )
