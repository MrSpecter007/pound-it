# Pound It staging deployment

Target: `https://new.pounditdj.com` on `2.25.225.27`.
The apex and `www` stay on Wix until a separate approved cutover.

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
Staging emits `X-Robots-Tag: noindex, nofollow`. Remove that header during the
approved production-domain cutover and update Caddy, allowed hosts, CSRF origins,
the admin base URL and Wagtail Site together.
