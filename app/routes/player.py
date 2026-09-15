from flask import Blueprint, render_template, abort
from flask_login import current_user, login_required
from app.models import Movie, Episode, WatchProgress
from app.services.storage import storage

bp = Blueprint("player", __name__)


def _resume_position(media_type, media_id):
    if not current_user.is_authenticated:
        return 0
    p = WatchProgress.query.filter_by(user_id=current_user.id, media_type=media_type, media_id=media_id).first()
    return p.position_seconds if p and not p.completed else 0


@bp.route("/watch/movie/<slug>")
@login_required
def watch_movie(slug):
    movie = Movie.query.filter_by(slug=slug).first_or_404()
    if not movie.video_key:
        abort(404)
    video_url = storage.url_for(movie.video_key, "movies")
    subtitle_url = storage.url_for(movie.subtitle_key, "subtitles") if movie.subtitle_key else None
    resume_at = _resume_position("movie", movie.id)

    return render_template(
        "player.html",
        title=movie.title,
        subtitle_text=f"{movie.release_year} \u00b7 {movie.runtime_minutes} min" if movie.runtime_minutes else "",
        video_url=video_url,
        subtitle_url=subtitle_url,
        resume_at=resume_at,
        progress_media_type="movie",
        progress_media_id=movie.id,
        back_url=f"/movie/{movie.slug}",
        next_url=None,
    )


@bp.route("/watch/episode/<int:episode_id>")
@login_required
def watch_episode(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    if not episode.video_key:
        abort(404)
    show = episode.season.show
    video_url = storage.url_for(episode.video_key, "tv")
    subtitle_url = storage.url_for(episode.subtitle_key, "subtitles") if episode.subtitle_key else None
    resume_at = _resume_position("episode", episode.id)

    # find next episode (same season, next number; else next season ep 1)
    next_ep = next((e for e in episode.season.episodes if e.number == episode.number + 1), None)
    if not next_ep:
        next_season = next((s for s in show.seasons if s.number == episode.season.number + 1), None)
        if next_season and next_season.episodes:
            next_ep = next_season.episodes[0]

    return render_template(
        "player.html",
        title=f"{show.title}",
        subtitle_text=f"S{episode.season.number} E{episode.number} \u00b7 {episode.title}",
        video_url=video_url,
        subtitle_url=subtitle_url,
        resume_at=resume_at,
        progress_media_type="episode",
        progress_media_id=episode.id,
        back_url=f"/tv/{show.slug}?season={episode.season.number}",
        next_url=f"/watch/episode/{next_ep.id}" if next_ep else None,
    )
