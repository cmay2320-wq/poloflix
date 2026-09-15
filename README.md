# Poloflix

A Netflix-style streaming platform: browsing, search, watch progress, My List,
movie requests, ratings, an admin panel for content management, and a
storage layer that's ready for Azure Blob Storage whenever you are.

This is Phase 1-2 (and a chunk of Phase 3/4/6) from the full spec: the
foundation, content system, and admin tools are built and working end to
end on a local SQLite database and local file storage. FFmpeg/HLS
transcoding, payments, and 2FA are **not** wired up yet - see "What's not
built yet" below.

---

## 1. Quick start

```bash
cd poloflix
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit SECRET_KEY at minimum

python seed.py                   # creates demo movies/shows + an admin user
python run.py                    # http://localhost:5000
```

The seed script prints an admin login:

```
username: admin
password: ChangeMe123!
```

Sign in with that account, then visit `/admin/` to manage content. Change
that password immediately if this ever leaves your machine.

The demo catalogue uses generated placeholder poster/backdrop artwork so
the site looks populated right away - replace it any time via
**Admin → Movies/Shows → Edit → upload a real poster**.

---

## 2. Adding your own movies/shows right now (no cloud setup needed)

1. Go to `/admin/movies/new` (or `/admin/shows/new`).
2. Fill in the details, upload a poster/backdrop, and upload the video file.
3. Save. The file is written to `instance/media/<container>/...` and served
   straight from Flask at `/media/<container>/<file>`.

This is genuinely fine for a small/personal deployment. Move to Blob
Storage when you need real scale, multiple app instances, or a CDN.

---

## 3. Adding Azure Blob Storage later

Everything in this codebase asks the storage layer for a URL - nothing
builds a file path by hand. That's what makes this a one-setting change.

**Where this lives:** `app/services/storage.py`. Read the big comment at
the top of that file for the full picture; short version below.

### Step by step

1. **Create the storage account and containers** (Azure CLI, or the portal).
   Recommended container names (matches `AZURE_CONTAINERS` in
   `app/config.py` - edit that dict if you name yours differently):

   ```
   media-movies      media-tv       media-trailers    media-subtitles
   images-posters    images-backdrops  images-logos    images-avatars
   site-banners      site-ui-assets
   ```

   ```bash
   az storage account create -n poloflixmedia -g my-resource-group -l eastus --sku Standard_LRS
   az storage container create --account-name poloflixmedia -n media-movies
   # ...repeat for each container above. Keep them PRIVATE (no public read access) -
   # the app hands out short-lived signed URLs instead.
   ```

2. **Install the SDK:**

   ```bash
   pip install azure-storage-blob
   echo "azure-storage-blob==12.22.0" >> requirements.txt
   ```

3. **Set two environment variables** (in `.env` or your host's config):

   ```
   STORAGE_BACKEND=azure
   AZURE_STORAGE_ACCOUNT=poloflixmedia
   AZURE_STORAGE_CONNECTION_STRING=<copy from Azure Portal → Storage Account → Access keys>
   ```

4. **Restart the app.**

That's it. From this point on:

- `storage.url_for(key, container)` returns a signed, read-only SAS URL
  (expires after `AZURE_SAS_TTL_SECONDS`, default 1 hour) pointing directly
  at Blob Storage instead of a local `/media/...` path.
- `storage.save(file, container)` in the admin upload routes writes
  straight to Blob Storage instead of disk.
- No route, template, or model code changes - they all already go through
  `storage`.

For production-scale delivery, put Azure Front Door or a CDN in front of
the storage account and point users there instead of the storage account
directly - the doc's original architecture diagram covers this.

**Never** put your Azure connection string or keys in frontend JavaScript
or in a public repo - `.env` is already gitignored.

---

## 4. Switching the database when you deploy

Same principle: every table access goes through SQLAlchemy models, never
raw engine-specific SQL, so switching databases is one environment
variable.

Today, with nothing set, you get a local SQLite file at
`instance/poloflix.db` - zero setup, perfect for development.

When you're ready to deploy on Postgres (recommended) or MySQL:

```bash
# Postgres
pip install psycopg2-binary
# in .env:
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/poloflix

# --- or MySQL ---
pip install PyMySQL
# in .env:
DATABASE_URL=mysql+pymysql://user:password@host:3306/poloflix
```

Then re-run against the new database:

```bash
python seed.py --reset     # creates tables + demo data on the NEW database
# or, if you have real data to bring over, use Flask-Migrate instead of --reset:
flask db init && flask db migrate && flask db upgrade
```

`app/config.py` is the only file that reads `DATABASE_URL` - nothing else
needs to change.

---

## 5. Project structure

```
poloflix/
  app/
    __init__.py          Flask application factory
    config.py             All environment-driven settings (DB, storage, plans)
    extensions.py          Shared Flask extension instances
    models/                 SQLAlchemy models, one file per domain
    routes/                 Blueprints: auth, home, catalog, search, player,
                            lists (watchlist/progress/ratings), requests,
                            account, admin, media (local file serving)
    services/
      storage.py            Storage abstraction (local disk today, Azure later)
      placeholder.py        Generates demo poster/backdrop artwork
    templates/              Jinja2 templates, dark-blue Poloflix theme
    static/
      css/main.css          Public site styling
      css/admin.css         Admin panel styling
      js/app.js             Toasts, live search, My List toggle
      js/home.js             Hero carousel
      js/detail.js            Star rating widget
      js/player.js             Video player (HLS.js + custom controls)
  seed.py                  Demo data generator
  run.py                   Dev server entry point
  requirements.txt
  .env.example
```

---

## 6. What's built vs. what's not (yet)

**Working now:**
- Registration / login / logout, password hashing, CSRF protection, rate
  limiting on login
- Multiple profiles per account (with plan-based limits)
- Movie & TV catalogue, genres, search with live suggestions
- Movie/show detail pages, seasons & episodes, star ratings
- Custom video player (HTML5 + HLS.js when you serve `.m3u8`, resume
  playback, quality menu, keyboard shortcuts, auto-play next episode)
- Continue Watching, My List, watch progress tracking
- Movie request system with cooldown/duplicate checks and community upvoting
- Full admin panel: dashboard stats, movie/show/episode CRUD with file
  uploads, user management (suspend/unsuspend), request moderation with
  auto-notification when a request is added
- Storage abstraction ready for Azure Blob Storage (see section 3)
- Database ready for Postgres/MySQL (see section 4)

**Documented but not implemented yet** (next phases from the original
spec - the architecture leaves room for all of these, none require
restructuring what's here):
- FFmpeg transcoding / real multi-bitrate HLS pipeline (today: upload
  whatever file you have; the player still works, quality menu becomes
  functional automatically once you actually serve `.m3u8` renditions)
- Payment provider integration (subscription/plan models and fields
  already exist - `Subscription.provider`, `provider_customer_id`, etc.)
- Email verification / password reset emails
- Admin 2FA
- Background job processing for uploads
- Analytics charts (dashboard shows the raw counts already)

Build these in the order suggested in the original planning doc's
"Recommended Starting Point" section - the foundation here supports all
of them without rework.

---

## 7. Security notes

- Change `SECRET_KEY` before deploying anywhere real.
- Change the seeded admin password immediately.
- Keep Blob Storage containers private; the app only ever hands out
  short-lived signed URLs.
- `.env` and `instance/` (your local DB + media) are gitignored - never
  commit them.
- Only upload/distribute media you have the rights to.
