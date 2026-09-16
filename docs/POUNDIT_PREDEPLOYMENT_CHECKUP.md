# Pound It — Pre-Deployment Checkup

**Target:** Hostinger KVM 1 — 1 vCPU, 4 GB RAM, 50 GB disk, 4 TB transfer
**Reviewed:** the deployment-critical configuration as it stands in the repo today
**Verdict: NO-GO as configured.** Eight blocking issues. None are hard to fix; all of them bite on day one.

Findings marked **verified** were reproduced by running the app under `settings.production`, not inferred from reading the code.

---

## A. Blocking — fix before the first deploy

### A1. The container runs development settings in production

`wsgi.py` ends with:

```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alternative_naissance.settings.dev")
```

and the Dockerfile never sets `DJANGO_SETTINGS_MODULE`. So unless the environment provides it, the production container loads `settings/dev.py`, which means:

- `DEBUG = True` — full tracebacks, settings and SQL exposed to anyone who triggers an error
- `SECRET_KEY = "django-insecure-0k(u8qb7urcpn$..."` — hardcoded, and in the repo, so anyone with the source can forge session cookies and password-reset tokens
- `ALLOWED_HOSTS = ["*"]` — accepts any Host header

This one issue is the difference between a hardened deployment and an open one. Everything else in this section is downstream of it.

**Fix:** set it explicitly in the image, so the default is safe rather than convenient.

```dockerfile
ENV DJANGO_SETTINGS_MODULE=alternative_naissance.settings.production
```

### A2. Static and media files 404 under production settings — **verified**

`urls.py` registers the static and media routes only when `DEBUG` is true:

```python
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Running under `settings.production`, `/` returns 200 but `/static/...` and `/media/...` both return **404**. Gunicorn does not serve files. The site would come up with no CSS, no JavaScript, no faculty portraits, no logo — and an unstyled Wagtail admin.

**Fix:** WhiteNoise for static, the reverse proxy for media. Add `whitenoise` to requirements, then in `base.py`:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # immediately after SecurityMiddleware
    ...
]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
```

The manifest backend also gives you hashed filenames, which A15 covers. Media stays on disk and is served by Caddy — see §D.

Note `production.py` currently sets the deprecated `STATICFILES_STORAGE` alongside `base.py`'s `STORAGES`; on Django 5.2 the `STORAGES` dict wins and the old setting is ignored. Remove the dead line to avoid the next person trusting it.

### A3. `ALLOWED_HOSTS` cannot express more than one host — **verified**

```python
ALLOWED_HOSTS = [os.getenv("ALLOWED_HOSTS", "")]
```

This wraps the whole environment variable in a one-element list. Setting `ALLOWED_HOSTS=pounditdj.com,www.pounditdj.com` produces `['pounditdj.com,www.pounditdj.com']` — a single host that matches nothing. Verified: **both** hostnames then return **400 Bad Request**. The site is down, with a message that does not obviously point at this line.

**Fix:**

```python
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
```

### A4. `docker-compose.yaml` is a development file

Three problems, all of which become internet-facing the moment this runs on a public IP.

**pgadmin is in the default profile and publishes port 20080**, with `PGADMIN_DEFAULT_EMAIL: com@com.com` and `PGADMIN_DEFAULT_PASSWORD: secret`. That is a database administration console, on the public internet, behind a six-letter password. It must not exist on the server at all.

**Postgres publishes 25432 to the host.** On a VPS without a firewall that is the database itself, reachable from anywhere, with the credentials below.

**The database credentials are `myuser` / `secret`,** hardcoded in the compose file rather than read from the environment.

**Fix:** a separate `docker-compose.prod.yaml` — see §D. Postgres publishes no ports at all (the app reaches it over the compose network); pgadmin and mailhog are absent; credentials come from `.env`.

### A5. `ALLOWED_HOSTS: "*"` is set in the app service

Even after fixing A3, the compose file passes `ALLOWED_HOSTS: "*"` into the container, which overrides it. Remove it from the production compose and set the real hostnames.

### A6. Two database dumps are baked into the image — **verified**

`alternative_naissance/dump.sql` (1.3 MB) and `alternative_naissance/backup_before_home.sql` (198 KB) sit inside the directory the Dockerfile copies:

```dockerfile
COPY --chown=wagtail:wagtail alternative_naissance .
```

`.dockerignore` does not exclude `*.sql`, so both land at `/app/` in the image. Inspecting `dump.sql` shows it contains `auth_user` with password hashes, and `core_inscription` — Alternative Naissance's membership signups, carrying names, email addresses, postal addresses and phone numbers.

Anyone who can pull the image, or exec into the container, gets that file. If the image is ever pushed to a registry, so is the data.

**Fix:** add to `.dockerignore`:

```
*.sql
*.dump
alternative_naissance/poundit/images/
```

and move the dumps out of the application directory entirely. The last line also stops the supplied source portraits being carried in every image build; they are only needed once, at import time.

### A7. No TLS, and no settings to support it

There is no reverse proxy and no certificate. Separately, none of Django's transport-security settings are configured — **verified** as `SECURE_SSL_REDIRECT: False`, `SESSION_COOKIE_SECURE: False`, `SECURE_HSTS_SECONDS: 0`.

Session cookies and the Wagtail admin login would cross the network in plaintext.

**Fix:** §D puts Caddy in front for automatic certificates. Then in `production.py`:

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
```

Set `SECURE_HSTS_SECONDS` to something small (say 300) for the first day, then raise it. HSTS is hard to walk back.

### A8. `CSRF_TRUSTED_ORIGINS` is empty — **verified**

Django 4+ requires the origin to be listed for cross-origin POSTs over HTTPS. Left empty, the Wagtail admin login and the school inquiry form will both reject submissions once TLS is in front.

```python
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]
```

Set it to `https://pounditdj.com,https://www.pounditdj.com`.

---

## B. High — fix in the first week

**B1. `WAGTAILADMIN_BASE_URL = "http://example.com"`** — verified. Notification emails and some admin links will point at example.com. Set it to the real origin.

**B2. No restart policy.** Nothing in the compose file restarts on failure or reboot. A VPS reboot leaves the site down until someone notices. Add `restart: unless-stopped` to both services.

**B3. No backups.** Postgres lives in a named Docker volume with no dump schedule. A `docker compose down -v` typed in the wrong directory destroys the site. See §D for a cron'd `pg_dump`.

**B4. The demo superuser must not travel.** `admin` / `Demo2026!` was created for the local demo. Create the real account on the server with a generated password and confirm the demo one does not exist.

**B5. Email is unconfigured for production.** `EMAIL_HOST` defaults to `localhost:21025` — that is Mailhog. School inquiry notifications will fail silently (by design: the code logs and carries on, so the inquiry is never lost, but nobody is told). Point it at a real SMTP relay and set `ADMIN_EMAIL`, or set the studio's Public email in Pound It settings.

**B6. `DEFAULT_FROM_EMAIL` defaults to `noreply@alternative-naissance.ca`** — the wrong domain for this site. Set it per-site.

---

## C. Medium — worth doing, not blocking

**C1. `migrate` runs on every container start.** Already caused a failure in testing: two concurrent migrations raced and the container exited on a duplicate table. Fine on one instance if nothing else starts alongside it, but it makes rollbacks awkward. Consider moving it to a one-shot step in the deploy script.

**C2. No healthcheck on the app service.** Postgres has one; the app does not, so Docker cannot tell a wedged gunicorn from a healthy one.

**C3. Gunicorn runs with default settings** — one sync worker, no timeout, no access log. See §E for the recommended flags.

**C4. The Wagtail admin is at the default `/admin/`.** Moving it to an unguessable path removes most automated login attempts. One line in `urls.py`.

**C5. No rate limiting on the school inquiry form.** It has a honeypot, which stops naive bots. A determined one can still fill the table and send you mail. `django-ratelimit`, or a Caddy rate limit on that path.

**C6. Disk growth.** 50 GB is ample for the content, but Docker build cache and old images accumulate quickly when you rebuild on the box. Schedule `docker image prune -af --filter "until=168h"`.

**C7. The five orphan templates** flagged after Codex's pass (`event_detail_page.html`, `faculty_detail_page.html`, `program_detail_page.html`, `waiver_page.html`, `form_submitted.html`) reference model fields that do not exist and three of them still link to the old Wix site. Unreachable today, but they will fail the `test_no_template_points_at_the_old_host` check and will mislead the next person. Delete or rewrite before launch.

---

## D. Recommended production shape

Smallest number of moving parts that is actually safe on one small box.

```
Internet ──▶ Caddy (TLS, :80/:443) ──▶ gunicorn (app, internal) ──▶ Postgres (internal)
                     │
                     └── serves /media/ straight from disk
```

Caddy rather than nginx plus certbot: certificates are automatic and there is one fewer moving part to renew. WhiteNoise handles `/static/` inside the app, so Caddy only needs the media directory.

**`docker-compose.prod.yaml`** — sketch, not a drop-in; the domain and paths are yours to set:

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    # no ports: the database is reachable only on the compose network

  app:
    build: .
    environment:
      DJANGO_SETTINGS_MODULE: alternative_naissance.settings.production
      SECRET_KEY: ${SECRET_KEY}
      ALLOWED_HOSTS: ${ALLOWED_HOSTS}
      CSRF_TRUSTED_ORIGINS: ${CSRF_TRUSTED_ORIGINS}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_HOST: postgres
      POSTGRES_PORT: "5432"
      EMAIL_HOST: ${EMAIL_HOST}
      EMAIL_PORT: ${EMAIL_PORT}
      EMAIL_HOST_USER: ${EMAIL_HOST_USER}
      EMAIL_HOST_PASSWORD: ${EMAIL_HOST_PASSWORD}
      DEFAULT_FROM_EMAIL: ${DEFAULT_FROM_EMAIL}
      ADMIN_EMAIL: ${ADMIN_EMAIL}
    volumes:
      - ./media:/app/media
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/')\""]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    # no ports: Caddy reaches it on the compose network

  caddy:
    image: caddy:2
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./media:/srv/media:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - app
    restart: unless-stopped

volumes:
  db_data:
  caddy_data:
  caddy_config:
```

**`Caddyfile`:**

```
pounditdj.com, www.pounditdj.com {
    encode gzip zstd
    handle_path /media/* {
        root * /srv/media
        file_server
        header Cache-Control "public, max-age=2592000"
    }
    handle {
        reverse_proxy app:8000
    }
}
```

**Backups** — `pg_dump` nightly, keep 14 days, and put a copy somewhere that is not this VPS:

```bash
0 3 * * * cd /srv/poundit && docker compose -f docker-compose.prod.yaml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > backups/poundit-$(date +\%F).sql.gz \
  && find backups -name '*.sql.gz' -mtime +14 -delete
```

A backup that only exists on the machine it is backing up is not a backup. Sync the directory off-box.

---

## E. Sizing on a KVM 1

1 vCPU, 4 GB RAM, 50 GB disk is **adequate** for this site, which is a content site with modest traffic and no heavy computation. Memory is comfortable; the single core is the constraint.

Rough steady-state budget:

| | Memory |
|---|---|
| Postgres (tuned, below) | ~700 MB |
| Gunicorn, 3 workers | ~600 MB |
| Caddy | ~50 MB |
| Docker daemon | ~150 MB |
| OS | ~400 MB |
| **Total** | **~1.9 GB of 4 GB** |

That leaves headroom for the page cache, which is what Postgres actually wants.

**Gunicorn** — with one core, workers exist to cover I/O waits, not parallel CPU:

```dockerfile
CMD gunicorn alternative_naissance.wsgi:application \
    --bind 0.0.0.0:8000 --workers 3 --timeout 60 \
    --access-logfile - --error-logfile -
```

**Postgres** — the defaults assume a much larger machine is sharing the box. For a dedicated 4 GB VPS:

```
shared_buffers = 512MB
effective_cache_size = 2GB
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 50
```

**Two things that will bite on one core.** Building the image on the VPS takes several minutes and will make the site unresponsive while it runs — build elsewhere and push to a registry, or accept a maintenance window. And add swap; Hostinger VPS images often ship with none, and a swapless box OOM-kills rather than degrades:

```bash
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

---

## F. Deployment runbook

1. Fix A1 through A8. Nothing below matters until these are done.
2. Provision the VPS. Create a non-root user, add swap, enable the firewall — allow 22, 80, 443 and nothing else.
3. Install Docker and the compose plugin.
4. Point DNS at the VPS and let it propagate. Caddy needs the A record resolving before it can get a certificate.
5. Create `/srv/poundit/.env` with a freshly generated `SECRET_KEY`, a strong database password, the real hostnames and SMTP credentials. `chmod 600`. Never commit it.
6. Deploy the code. Build and start with `docker-compose.prod.yaml`.
7. Run migrations, then `import_poundit`, then `import_poundit_images --source-dir` pointed at the portraits.
8. Create the real superuser. Confirm `admin` / `Demo2026!` does not exist.
9. Restore or re-enter content as appropriate.
10. Verify, deliberately: HTTPS and the redirect from HTTP; a legacy URL such as `/kidsreccrews` returning 301 to `/programs/kids-teen/`; `/static/` and `/media/` both returning 200; a school inquiry submitting and arriving by email; the admin login over HTTPS; `/sitemap.xml`.
11. Turn on backups and confirm a dump actually restores. An untested backup is a guess.
12. Raise `SECURE_HSTS_SECONDS` once you are confident.

---

## G. Still outstanding from the build

Not deployment issues, but they should not go live unfinished. All are visible on the admin dashboard panel.

- Nine faculty biographies to paste in verbatim
- Four legal pages empty — waiver, privacy, refund, terms
- Three weekly sessions with no instructor: PIBA Thursday 5:15, Open House Thursday 6:00, Choreography Cleaning Friday 5:15
- Two portraits missing: Leiran, plus Breton and Genie who have none published
- Twenty calendar dates still flagged tentative
- Two crews uncategorised: The Broskies, Boss Mega Crew Adv.
- `/afterschool` redirect unconfirmed
- Studio public email, maps URL and waiver URL unset
- **The admin page that would not load** — never diagnosed. Do not deploy without knowing what that was; if it is a render error it will reappear on the server.

---

## Summary

The application itself is in good shape: 286 tests, no missing migrations, no runtime dependency on the old host. What is not ready is the deployment configuration, which is still the development setup — a container that would run with `DEBUG=True` and a published secret key, no way to serve its own CSS, a hostname setting that cannot express two hostnames, a database console on a public port with a trivial password, and personal data baked into the image.

None of it is difficult. All of it matters more than anything else on the list.
