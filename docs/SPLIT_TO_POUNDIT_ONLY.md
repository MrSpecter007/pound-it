# Making this repository Pound It only

This repository was Alternative Naissance's. It now becomes Pound It's. The
Pound It site must come through unchanged — same pages, same images, same look.

Alternative Naissance's code and content leave. **Its data leaves via the dump
you take in step 2, and that dump is the only copy.** Do not skip it.

## Order matters

Code and data are coupled, and the coupling only runs one way. While
Alternative Naissance's pages exist in `wagtailcore_page`, their rows point at
content types owned by the `core` app. Remove the app first and the Wagtail page
explorer stops loading, because Django cannot resolve what those pages are.

So: **data first, code second.** Every step below is in that order.

---

## 1. Commit what you have

```bash
git add -A && git commit -m "Pound It: deployment config, template protocol, rename"
```

You want the split to be its own reviewable commit, and the scripts refuse to
run on a dirty tree.

## 2. Take the dump — this is Alternative Naissance's only copy

```bash
docker compose exec -T postgres pg_dump -U myuser mydatabase > ../alternative-naissance-full.sql
ls -lh ../alternative-naissance-full.sql
```

Write it **outside** the repository. `.gitignore` excludes `*.sql`, and this one
contains password hashes and personal data — it must never be committed. Keep it
wherever Alternative Naissance's new repository will be able to reach it.

Confirm the file is a plausible size (roughly 1.5 MB) before continuing.

## 3. Delete the Alternative Naissance site and its pages

```bash
docker compose exec app python manage.py shell
```

```python
from wagtail.models import Site, Page

an = Site.objects.get(hostname="alternative-naissance.localhost")
root = an.root_page
print(root, root.get_descendants(inclusive=True).count(), "pages")   # expect ~74

# Read that number. If it is anywhere near Pound It's page count, stop.
pound_it = Site.objects.get(is_default_site=True)
assert pound_it.root_page.pk != root.pk, "refusing: that is Pound It's root"

an.delete()
root.delete()

print("remaining pages:", Page.objects.count())
for s in Site.objects.all():
    print(s.hostname, s.port, s.is_default_site, s.root_page)
```

Only one site should remain, and it must be Pound It's, still default.

**Check the site before going further.** Load the Pound It pages in a browser —
home, schedule, faculty, programs, events, and the legal pages. Images should
still be there: deleting pages does not delete anything from the image library,
and no Pound It image belongs to the pages you just removed.

## 4. Drop the tables

Still with the apps installed, so Django can unwind their migrations:

```bash
docker compose exec app python manage.py migrate core zero
docker compose exec app python manage.py migrate servicerequests zero
docker compose exec app python manage.py remove_stale_contenttypes
```

`core` is the app label — the directory is `src/altnaissance`, but its
`AppConfig` pins `label = "core"` so the database name never changed.

`remove_stale_contenttypes` will list what it is about to delete and ask. Read
the list. It should name only `core` and `servicerequests` models.

## 5. Remove the code

```bash
python scripts/finish_poundit_split.py --dry-run
python scripts/finish_poundit_split.py
```

This removes `src/altnaissance/`, `src/servicerequests/`, the inherited theme
templates and its 1.3 MB of vendor CSS, and edits `INSTALLED_APPS`, the context
processor list and two URL mounts.

It refuses to run unless Pound It's own `404.html` and `500.html` are in place.
That check is not ceremony: the inherited `404.html` extends the theme's
`base.html`, which includes `partials/header.html`, which loads `menu_tags` from
the app you just deleted. Without the replacements, every 404 on the live site
raises `KeyError: 'menu_tags'` and returns a 500 instead.

## 6. Verify

```bash
cd src
DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py check
DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py makemigrations --check --dry-run
DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py test poundit
cd .. && docker compose up -d --build
```

Expect: no issues, no changes detected, 284 tests OK.

Then walk the site: every Pound It page, the faculty portraits, the schedule
grid, the Wagtail admin, and a deliberate 404 (`/no-such-page/`) to confirm the
new error template renders.

## 7. Rename the remote

The repository is still called `Alternative-Naissance` on GitHub. Rename it to
`pound-it` in the repository settings, then:

```bash
git remote set-url origin https://github.com/MrSpecter007/pound-it.git
```

---

## What was verified, and what was not

The code half was verified: with both apps uninstalled, Pound It's suite passes
284 tests, `check` is clean and `makemigrations --check` reports no changes. The
`menu_tags` failure above was found that way rather than in production.

The database half was **not** run. My sandbox copy of the database predates the
portrait import — it has 14 images, none attached to a faculty member — so it is
not your data and a rehearsal against it would have proved nothing about yours.
Steps 3 and 4 are written from the schema, not from an executed run. That is
exactly why step 2 is not optional and step 3 asks you to read the page count
before deleting anything.

## If something goes wrong

The dump from step 2 restores everything:

```bash
docker compose down -v            # discards the database volume
docker compose up -d postgres
docker compose exec -T postgres psql -U myuser mydatabase < ../alternative-naissance-full.sql
```

Then `git checkout .` to undo the code changes.
