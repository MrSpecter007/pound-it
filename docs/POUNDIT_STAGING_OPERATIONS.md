# Pound It deployment

Primary: `https://pounditdj.com` on `2.25.225.27`.
`www.pounditdj.com` redirects permanently to the primary, preserving paths and queries.
`https://new.pounditdj.com` remains available as requested, serving the same app and
database. It is an alternate address, not an independent server or backup.

Main-domain cutover verified on 2026-09-18 UTC: DNS resolves to the VPS, both
main-domain certificates are active, and pages and real admin sign-in work on both
the primary and alternate domains. Wagtail Site and WAGTAILADMIN_BASE_URL use
`pounditdj.com`. The alternate domain retains `noindex, nofollow`; public HTML on
the primary is indexable. Sitemap URLs use the primary domain. Email DNS was retained.
A post-cutover backup was taken. App code release: `29f96e5`; domain configuration:
`e161eaa`. Admin credentials are unchanged by the cutover.

Verified on 2026-09-17: staging is live over HTTPS. Application release `a8c26fe`
includes frontend/admin branding and `+ GST` labels on displayed program and event
prices. Seventeen routes and 35 assets passed HTTP checks; real admin sign-in with
CSRF, the HTTPS redirect and custom 404 passed. Mobile navigation works without
horizontal overflow; six faculty portraits render. Django production checks passed.
The first backup was restored into a separate temporary database and verified:
34 programs, 15 page-tree records (including the root), one admin, zero legacy
registrations. The temporary restore database was removed after verification.

The server uses Ubuntu 26.04, Docker's official apt repository, PostgreSQL 16,
Gunicorn and Caddy. SSH keys work for `deploy` and `root`; SSH password login is
disabled. Hostinger's console still supports the root password.

Application directory: `/home/deploy/poundit`. Secrets are in `.env` with mode 600.
`DEPLOYED_REVISION` records the uploaded Git commit. Initial deployment uses a
`git archive` release, not a server clone with a GitHub private key.

## Content transfer

Do not transfer a complete local database or media directory: the development
database also contains Alternative Naissance data and registrations.

`tools/export_poundit_content.py` exports only Pound It pages, structured public
content, site settings, scoped redirects and referenced images. Users, sessions,
submissions, revisions, audit records and the other site are excluded. It refuses
unpublished changes and StreamField content requiring additional media review.

`tools/import_poundit_content.py` accepts this export only into a freshly migrated
database with no accounts or application records. It imports atomically and creates
new published revisions. Never run it to overwrite an existing deployment.

Database migrations run before this scoped fixture import. That is different from
restoring a full PostgreSQL dump, which must target an empty database.

## Updating code

Commit and push changes first. Create a `git archive --format=tar.gz` of the commit,
upload it with `scp`, and inspect the archive. On the server, run a backup, extract
the release into the app directory (the archive excludes `.env` and uploaded media),
then run:

```bash
cd /home/deploy/poundit
docker compose -f docker-compose.prod.yaml build app
docker compose -f docker-compose.prod.yaml run --rm app python manage.py migrate --noinput
docker compose -f docker-compose.prod.yaml up -d
docker compose -f docker-compose.prod.yaml ps
```

Record the deployed commit in `DEPLOYED_REVISION` and verify public pages, static
assets, portraits, admin login and the 404 page. Do not use `down -v`.

## Backups

`tools/backup_poundit.sh` writes private database, media and configuration backups
to `/home/deploy/backups` and retains 14 days. The systemd timer
`poundit-backup.timer` runs daily at 03:15 UTC. Run the script manually before updates.
These are local VPS backups; off-server copies must be arranged separately.

Restore a database dump into a new empty database with `pg_restore --no-owner
--no-acl --exit-on-error`, then run migrations for the chosen release. Restore the
matching media and configuration archives. Verify the new database before directing
the app to it; do not restore over the running database.

## Remaining configuration

SMTP credentials and a sender address are required for notification and password
reset delivery. Saved school inquiries can still be managed in the admin.
Legal pages currently have no entered body copy; complete these and review the
tentative calendar dates and remaining faculty content. The main domain was switched
at the user's explicit request with these content items still pending.
Keep `X-Robots-Tag: noindex, nofollow` scoped to the alternate hostname. Do not apply
it to public HTML on the primary domain. Admin and sitemap responses may independently
carry noindex headers from Django/Wagtail.
