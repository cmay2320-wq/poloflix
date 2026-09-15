from flask import Blueprint, render_template, request, jsonify
from app.models import Movie, TVShow

bp = Blueprint("search", __name__)


@bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    media_filter = request.args.get("type", "all")  # all / movies / tv

    movies, shows = [], []
    if q:
        like = f"%{q}%"
        if media_filter in ("all", "movies"):
            movies = Movie.query.filter(Movie.status == "PUBLISHED", Movie.title.ilike(like)).limit(24).all()
        if media_filter in ("all", "tv"):
            shows = TVShow.query.filter(TVShow.status == "PUBLISHED", TVShow.title.ilike(like)).limit(24).all()

    return render_template("search.html", q=q, movies=movies, shows=shows, media_filter=media_filter)


@bp.route("/api/search/suggest")
def suggest():
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify([])
    like = f"%{q}%"
    movies = Movie.query.filter(Movie.status == "PUBLISHED", Movie.title.ilike(like)).limit(5).all()
    shows = TVShow.query.filter(TVShow.status == "PUBLISHED", TVShow.title.ilike(like)).limit(5).all()
    results = [
        {"title": m.title, "url": f"/movie/{m.slug}", "year": m.release_year, "type": "Movie"} for m in movies
    ] + [
        {"title": s.title, "url": f"/tv/{s.slug}", "year": s.first_air_year, "type": "TV Show"} for s in shows
    ]
    return jsonify(results[:8])
