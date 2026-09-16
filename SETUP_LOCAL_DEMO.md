# Alternative Naissance — Local Demo Setup (Docker, Windows)

Everything runs in Docker — no local Python/venv needed. The included
`demo_database_dump.sql` already has all migrations marked consistent
against the current codebase, so there's no migration troubleshooting:
restore it and go.

## Prerequisites

- Docker Desktop, running

## Files to add to your local clone

Drop these two files (from this download) into the root of your
`Alternative-Naissance` folder, replacing/adding as needed:

- `docker-compose.yaml` — replaces the repo's own; adds an `app` service
  that builds and runs the site itself (the repo previously only started
  Postgres/pgAdmin/Mailhog, not the app)
- `demo_database_dump.sql` — the working demo database

## Steps (PowerShell)

```powershell
cd path\to\Alternative-Naissance

# 1. Start Postgres only, and wait for it to be healthy
docker compose up -d postgres
docker compose ps   # wait until postgres shows "healthy"

# 2. Restore the working demo database into it
Get-Content demo_database_dump.sql | docker compose exec -T postgres psql -U myuser -d mydatabase

# 3. Build and start the app (plus pgAdmin) — first build takes a minute or two
docker compose up -d --build

# 4. Check it's up
docker compose logs -f app   # Ctrl+C to stop tailing once you see gunicorn running
```

Then open:
- **Public site:** http://localhost:8000/
- **Wagtail admin:** http://localhost:8000/admin/
- **pgAdmin** (optional DB browser): http://localhost:20080/ — login `com@com.com` / `secret`, then add a server pointing at host `postgres`, port `5432`, db `mydatabase`, user `myuser`, password `secret`

## Demo login

- Username: `guy-emmanuel`
- Password: `Demo2026!`

This is the site's real existing superuser account, with its password
reset to the value above for the demo.

## Stopping / restarting

```powershell
docker compose down          # stop everything, keep data
docker compose up -d         # start again later (no --build needed unless code changed)
```

## Known limitation: images

The repository's `media/` folder is (correctly) empty in git — uploaded
images are never committed to source control. The database references 14
real images, but the actual image **files** live only on wherever this
site is actually deployed/hosted, not in this repo or its dump. So pages
will render with **broken image placeholders** until real image files are
copied into `alternative_naissance/media/original_images/` (matching the
filenames referenced in `wagtailimages_image` in the admin). If you have
those files somewhere (a backup, the live server, cloud storage), copying
them in before the demo will fix this. Everything else — page content,
navigation, admin editing — works without them.

## What was fixed to make this work

The database dump on the original `dump.sql` (from ~Oct 2025) predates a
chunk of the current codebase: the `Menu`/`MenuItem` system, job postings,
newsletter signups, a `SiteSettings.address` field, a reworked
`servicerequests` app (client intake forms), and a `Testimonial` model
restructuring (dropped `TestimonialSection`, added `category` and
`is_approved`). The migration history on disk had also been squashed at
some point, so the old dump's migration bookkeeping didn't line up with
the current migration files at all.

`demo_database_dump.sql` is the result of reconciling all of that: every
table and column the current code expects now exists, all real content
(75 pages, 40 testimonials, users) was preserved, and the migration
history is marked fully consistent.

## Notes

- This runs in Django's `dev` settings (`DEBUG=True`) inside the
  container — fine for a local demo, not for exposing this externally.
- The `servicerequests` app's client-intake tables came in empty (the
  original dump had zero rows there), so that part of the demo will show
  an empty state unless you create sample entries through the admin or the
  public form.
- I could not build or run this Docker setup myself — the environment I
  worked in doesn't allow running a Docker daemon, so the `app` service
  is based on the project's existing `Dockerfile` and the exact settings
  I verified work (I ran the equivalent Python/Postgres setup directly and
  confirmed the homepage, several content pages, and the admin login all
  load correctly). If `docker compose up -d --build` hits an issue on your
  machine, send me the output and I'll fix it.
