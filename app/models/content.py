from datetime import datetime
from app.extensions import db

movie_genres = db.Table(
    "movie_genres",
    db.Column("movie_id", db.Integer, db.ForeignKey("movies.id"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("genres.id"), primary_key=True),
)

show_genres = db.Table(
    "show_genres",
    db.Column("show_id", db.Integer, db.ForeignKey("tv_shows.id"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("genres.id"), primary_key=True),
)

STATUS_CHOICES = ("DRAFT", "PROCESSING", "PUBLISHED", "ARCHIVED")


class Genre(db.Model):
    __tablename__ = "genres"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False)


class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    # These are STORAGE KEYS (e.g. "posters/the-last-kingdom.jpg"), never
    # full URLs. Templates call storage.url_for(key) to resolve them,
    # whether that's a local /media/ path today or a signed Azure SAS
    # URL after you flip STORAGE_BACKEND=azure.
    poster_key = db.Column(db.String(300), nullable=True)
    backdrop_key = db.Column(db.String(300), nullable=True)
    trailer_key = db.Column(db.String(300), nullable=True)
    video_key = db.Column(db.String(300), nullable=True)
    subtitle_key = db.Column(db.String(300), nullable=True)

    release_year = db.Column(db.Integer, nullable=True)
    runtime_minutes = db.Column(db.Integer, nullable=True)
    rating = db.Column(db.Float, default=0.0)  # average user rating, 0-10
    age_rating = db.Column(db.String(10), default="PG-13")
    language = db.Column(db.String(40), default="English")
    country = db.Column(db.String(80), nullable=True)
    cast = db.Column(db.String(400), nullable=True)
    director = db.Column(db.String(120), nullable=True)

    status = db.Column(db.String(20), default="PUBLISHED")
    is_featured = db.Column(db.Boolean, default=False)
    is_trending = db.Column(db.Boolean, default=False)
    processing_state = db.Column(db.String(20), default="READY")  # UPLOADING/PROCESSING/ENCODING/READY/FAILED

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    genres = db.relationship("Genre", secondary=movie_genres, backref="movies")

    @property
    def media_type(self):
        return "movie"


class TVShow(db.Model):
    __tablename__ = "tv_shows"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    poster_key = db.Column(db.String(300), nullable=True)
    backdrop_key = db.Column(db.String(300), nullable=True)
    trailer_key = db.Column(db.String(300), nullable=True)

    first_air_year = db.Column(db.Integer, nullable=True)
    rating = db.Column(db.Float, default=0.0)
    age_rating = db.Column(db.String(10), default="PG-13")
    language = db.Column(db.String(40), default="English")
    country = db.Column(db.String(80), nullable=True)
    cast = db.Column(db.String(400), nullable=True)
    director = db.Column(db.String(120), nullable=True)

    status = db.Column(db.String(20), default="PUBLISHED")
    is_featured = db.Column(db.Boolean, default=False)
    is_trending = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    genres = db.relationship("Genre", secondary=show_genres, backref="shows")
    seasons = db.relationship(
        "Season", backref="show", cascade="all, delete-orphan", order_by="Season.number"
    )

    @property
    def media_type(self):
        return "tv"

    @property
    def season_count(self):
        return len(self.seasons)


class Season(db.Model):
    __tablename__ = "seasons"
    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey("tv_shows.id"), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(120), nullable=True)

    episodes = db.relationship(
        "Episode", backref="season", cascade="all, delete-orphan", order_by="Episode.number"
    )


class Episode(db.Model):
    __tablename__ = "episodes"
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey("seasons.id"), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    thumbnail_key = db.Column(db.String(300), nullable=True)
    video_key = db.Column(db.String(300), nullable=True)
    subtitle_key = db.Column(db.String(300), nullable=True)
    duration_minutes = db.Column(db.Integer, default=45)
    air_date = db.Column(db.Date, nullable=True)
    processing_state = db.Column(db.String(20), default="READY")

    @property
    def media_type(self):
        return "episode"
