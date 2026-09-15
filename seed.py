"""
Populates the database with demo content so the UI looks like a real
streaming catalogue immediately after setup.

Usage:
    python seed.py            # add demo data (safe to re-run, skips existing)
    python seed.py --reset    # wipes and recreates all tables first
"""
from dotenv import load_dotenv
load_dotenv()
import sys
import random
from datetime import date

from app import create_app
from app.extensions import db
from app.models import (
    User, Profile, Genre,Movie, TVShow, Season, Episode, Plan, Subscription,
)
from app.services.placeholder import poster_svg, backdrop_svg

GENRES = ["Action", "Drama", "Comedy", "Sci-Fi", "Horror", "Romance", "Documentary", "Thriller"]

MOVIES = [
    ("The Last Kingdom", 2024, "Action", "A kingdom divided. A warrior torn. Follow Uhtred as he fights for his people and his destiny in a world on the edge of change.", 138, True, True),
    ("John Wick", 2014, "Action", "An ex-hitman comes out of retirement to track down the gangsters that took everything from him.", 101, False, True),
    ("Mad Max Fury Road", 2015, "Action", "In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler in search for her homeland.", 120, False, False),
    ("The Avengers", 2012, "Action", "Earth's mightiest heroes must come together to stop a mischievous god from enslaving humanity.", 143, False, True),
    ("Gladiator", 2000, "Drama", "A former Roman general sets out to exact vengeance against the corrupt emperor who murdered his family.", 155, False, False),
    ("Extraction", 2020, "Action", "A black-market mercenary is hired to rescue a drug lord's kidnapped son.", 116, False, False),
    ("The Dark Knight", 2008, "Action", "Batman faces the Joker, a criminal mastermind who wants to plunge Gotham into anarchy.", 152, False, True),
    ("Forrest Gump", 1994, "Drama", "The presidencies of Kennedy and Johnson, Vietnam, and other history unfold through the perspective of an Alabama man.", 142, False, False),
    ("Shawshank Redemption", 1994, "Drama", "Two imprisoned men bond over years, finding solace and eventual redemption through acts of common decency.", 142, False, False),
    ("Fight Club", 1999, "Drama", "An insomniac office worker and a soap maker form an underground fight club that evolves into something much more.", 139, False, False),
    ("Interstellar", 2014, "Sci-Fi", "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.", 169, False, True),
    ("A Beautiful Mind", 2001, "Drama", "A brilliant mathematician becomes entangled in a mystery that threatens to unravel his mind.", 135, False, False),
]

SHOWS = [
    ("Stranger Things", 2016, "Sci-Fi", "When a young boy vanishes in the small town of Hawkins, a group of friends uncover a mystery involving secret experiments, terrifying creatures and a parallel world.", 8.7, True, 4),
    ("The Witcher", 2019, "Action", "Geralt of Rivia, a solitary monster hunter, struggles to find his place in a world where people often prove more wicked than beasts.", 8.2, True, 3),
    ("Money Heist", 2017, "Thriller", "An unusual group of robbers attempt to carry out the most perfect robbery in Spanish history.", 8.2, True, 5),
    ("Breaking Bad", 2008, "Drama", "A chemistry teacher diagnosed with cancer turns to manufacturing drugs to secure his family's future.", 9.5, True, 5),
    ("The Boys", 2019, "Action", "A group of vigilantes set out to take down corrupt superheroes who abuse their powers.", 8.7, False, 4),
]

CAST_POOL = ["A. Morgan", "J. Reyes", "K. Ibrahim", "S. Novak", "T. Larsen", "M. Okafor", "R. Bianchi"]


def get_or_create_genres():
    lookup = {}
    for name in GENRES:
        g = Genre.query.filter_by(name=name).first()
        if not g:
            from app.utils import slugify
            g = Genre(name=name, slug=slugify(name))
            db.session.add(g)
        lookup[name] = g
    db.session.commit()
    return lookup


def get_or_create_plans():
    free = Plan.query.filter_by(code="FREE").first()
    if not free:
        free = Plan(code="FREE", name="Poloflix Free", price_cents=0, max_quality="720p", max_streams=1, max_profiles=1, has_ads=True)
        db.session.add(free)
    premium = Plan.query.filter_by(code="PREMIUM").first()
    if not premium:
        premium = Plan(code="PREMIUM", name="Poloflix Premium", price_cents=1599, max_quality="1080p", max_streams=4, max_profiles=5, has_ads=False)
        db.session.add(premium)
    db.session.commit()
    return free, premium


def make_admin(free_plan):
    admin = User.query.filter_by(username="admin").first()
    if admin:
        return admin
    admin = User(full_name="CJ May", username="admin", email="admin@poloflix.local", role="SUPER_ADMIN", email_verified=True)
    admin.set_password("ChangeMe123!")
    db.session.add(admin)
    db.session.flush()
    db.session.add(Profile(user_id=admin.id, name="CJ"))
    db.session.add(Subscription(user_id=admin.id, plan_id=free_plan.id, status="ACTIVE"))
    db.session.commit()
    print("Created admin user -> username: admin  password: ChangeMe123!")
    return admin


def artwork_for(title):
    from app.services.storage import storage
    from app.utils import slugify
    slug = slugify(title)
    poster_key = f"{slug}.svg"
    backdrop_key = f"{slug}-backdrop.svg"
    if not storage.exists(poster_key, "posters"):
        storage.save_bytes(poster_svg(title).encode(), "posters", poster_key)
    if not storage.exists(backdrop_key, "backdrops"):
        storage.save_bytes(backdrop_svg(title).encode(), "backdrops", backdrop_key)
    return poster_key, backdrop_key


def seed_movies(genre_lookup):
    from app.utils import slugify
    for title, year, genre_name, desc, runtime, featured, trending in MOVIES:
        if Movie.query.filter_by(title=title).first():
            continue
        poster_key, backdrop_key = artwork_for(title)
        movie = Movie(
            title=title,
            slug=slugify(title),
            description=desc,
            poster_key=poster_key,
            backdrop_key=backdrop_key,
            release_year=year,
            runtime_minutes=runtime,
            rating=round(random.uniform(6.5, 9.4), 1),
            age_rating=random.choice(["PG-13", "R", "PG"]),
            cast=", ".join(random.sample(CAST_POOL, 3)),
            director=random.choice(CAST_POOL),
            is_featured=featured,
            is_trending=trending,
            status="PUBLISHED",
        )
        movie.genres = [genre_lookup[genre_name]]
        db.session.add(movie)
    db.session.commit()


def seed_shows(genre_lookup):
    from app.utils import slugify
    for title, year, genre_name, desc, rating, trending, n_seasons in SHOWS:
        if TVShow.query.filter_by(title=title).first():
            continue
        poster_key, backdrop_key = artwork_for(title)
        show = TVShow(
            title=title,
            slug=slugify(title),
            description=desc,
            poster_key=poster_key,
            backdrop_key=backdrop_key,
            first_air_year=year,
            rating=rating,
            age_rating=random.choice(["PG-13", "R", "TV-MA"]),
            cast=", ".join(random.sample(CAST_POOL, 3)),
            director=random.choice(CAST_POOL),
            is_featured=trending,
            is_trending=trending,
            status="PUBLISHED",
        )
        show.genres = [genre_lookup[genre_name]]
        db.session.add(show)
        db.session.flush()

        for s_num in range(1, n_seasons + 1):
            season = Season(show_id=show.id, number=s_num, title=f"Season {s_num}")
            db.session.add(season)
            db.session.flush()
            episode_count = 8 if s_num == 1 else random.randint(6, 10)
            for e_num in range(1, episode_count + 1):
                db.session.add(Episode(
                    season_id=season.id,
                    number=e_num,
                    title=f"Chapter {e_num}",
                    description=f"Episode {e_num} of {title} Season {s_num}.",
                    duration_minutes=random.randint(42, 58),
                    air_date=date(year + s_num - 1, 1, 1),
                ))
    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        if "--reset" in sys.argv:
            db.drop_all()
            print("Dropped all tables.")
        db.create_all()

        genre_lookup = get_or_create_genres()
        free_plan, _ = get_or_create_plans()
        make_admin(free_plan)
        seed_movies(genre_lookup)
        seed_shows(genre_lookup)

        print(f"Done. {Movie.query.count()} movies, {TVShow.query.count()} shows in the database.")


if __name__ == "__main__":
    main()
