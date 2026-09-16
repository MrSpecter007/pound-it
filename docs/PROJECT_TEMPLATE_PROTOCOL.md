# Project template protocol

How a new client site is derived from this codebase without inheriting another
client's name.

## The problem this solves

This repository began as Alternative Naissance and was reused to build Pound It.
The client's name ended up in places that are structural rather than editorial:

| Where | Value | Consequence |
|---|---|---|
| Git repo | `Alternative-Naissance` | Collides with the real Alternative Naissance repo |
| Outer directory | `alternative_naissance/` | Two levels of the tree named after a client |
| Django project package | `alternative_naissance` | `DJANGO_SETTINGS_MODULE`, `wsgi.py`, every deploy file |
| App | `core` | Alternative Naissance's own site app, under an infrastructure name |
| Settings | `WAGTAIL_SITE_NAME`, `noreply@alternative-naissance.ca` | Pound It would send mail as another client |

Renaming per client does not scale: every derived project needs the same
surgery, and any step missed leaves the previous client's name in production.

**The protocol's goal is that deriving a project requires no renaming at all.**
The shared skeleton carries no client name, so there is nothing to rename.

## Three tiers

Every file belongs to exactly one tier. If you cannot say which, the file is in
the wrong place.

### Tier 1 — Template

Shared by every client. Contains no client name, no client content, no client
branding.

```
src/config/            Django project package: settings, urls, wsgi, storage
src/emails/            EmailTemplate model + registry (apps register their own)
src/search/            Wagtail search view
src/manage.py
Dockerfile  docker-compose.yaml  docker-compose.prod.yaml  Caddyfile
src/requirements.txt
```

Changing a Tier 1 file is a change to *every* client. Treat it accordingly.

### Tier 2 — Client app

One Django app per client site. It owns that client's page models, snippets,
templates, static assets, management commands and tests.

```
src/poundit/           Pound It
src/core/              Alternative Naissance  (misnamed; see below)
```

A client app never imports from another client app. Today `poundit` imports
nothing from `core`, `servicerequests` or `emails`, and vice versa — keep it
that way. That decoupling is what makes a client app liftable into its own
repository later.

### Tier 3 — Environment

Everything that differs per deployment: hostnames, secrets, database
credentials, SMTP, `WAGTAILADMIN_BASE_URL`, the sender address. These live in
`.env` and nowhere else. See `docs/PRODUCTION_ENV_TEMPLATE.txt`.

A Tier 1 file may read an environment variable. It may not carry a default that
names a client.

## Naming rules

1. **The project package is `config`.** Never a client name. Every derived
   project uses the same `DJANGO_SETTINGS_MODULE=config.settings.production`,
   so deploy files, CI and documentation are identical across clients.
2. **The project root directory is `src/`.** No directory above an app is named
   after a client.
3. **One app per client site, named for the client.** `poundit`, not `core`,
   not `main`, not `website`.
4. **Infrastructure apps get infrastructure names and hold no client content.**
   If an app called `core` contains one client's home page, the name is lying.
5. **The repository is named for the client.** `pound-it`. That is the only
   place the client's name belongs in the structure.
6. **Settings carry no client default.** `os.getenv("DEFAULT_FROM_EMAIL", "")`,
   never `os.getenv("DEFAULT_FROM_EMAIL", "noreply@some-client.ca")`. An empty
   default that fails loudly beats a default that silently belongs to someone
   else.

## Deriving a new client project

1. Clone the template branch (see "Maintaining the template" below) into a repo
   named for the client.
2. `python manage.py startapp <client>` inside `src/`, and add it to
   `INSTALLED_APPS`.
3. Give the app its own `templates/<client>/` and `static/<client>/` trees.
   Never put client templates in the shared `src/templates/` root.
4. Mount its URLs, if it needs any beyond Wagtail page serving. Do not mount a
   client's URLs at `/` unless that client is the only site in the deployment.
5. Copy `docs/PRODUCTION_ENV_TEMPLATE.txt` to `.env` and fill it in.
6. Run the verification checklist below.

No step renames anything.

## Renaming an existing app — the expensive case

`core` is Alternative Naissance's site app wearing an infrastructure name, and
it is the one violation this protocol cannot fix with a text substitution.

A Django app's **label** is stored in the database: `django_content_type.app_label`,
every migration's dependency graph, and every `ForeignKey` target written as
`"core.Thing"`. Renaming the directory alone breaks all three.

The cheap, safe move is to rename the *directory* and pin the *label*:

```python
# src/altnaissance/apps.py
class AltNaissanceConfig(AppConfig):
    name = "altnaissance"   # the Python package, now honest
    label = "core"          # the database label, unchanged
```

The tree reads correctly, and the database never notices. A true label rename
means a data migration over `django_content_type` plus `RenameModel` operations,
and it is only worth doing if the app is being lifted into its own repository.

**This has not been done.** It touches Alternative Naissance, not Pound It, and
it should be a deliberate change made against that project with its own tests.

## Maintaining the template

Keep a `template` branch that contains Tier 1 only — no client app. Client
repositories are created from it, and Tier 1 improvements are merged back into
it so the next project inherits them.

The alternative — copying the last client's repo and deleting their app — is how
this repository got into its current state.

## Verification checklist

Run after any rename, and before the first deploy of a derived project.

```bash
# 1. No client name survives outside its own app and migrations
grep -rn "<old-client-name>" --include="*.py" --include="*.yaml" --include="*.html" src/ \
  | grep -v "/migrations/" | grep -v "src/<their-app>/"

# 2. Django agrees the project is coherent
DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py check
DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py makemigrations --check --dry-run

# 3. The suite passes
DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py test

# 4. The production path builds and serves
DJANGO_SETTINGS_MODULE=config.settings.production SECRET_KEY=build \
  python manage.py collectstatic --noinput --clear
DJANGO_SETTINGS_MODULE=config.settings.production ... python manage.py check --deploy

# 5. The container builds and the site answers
docker compose up -d --build && curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8000/
```

Step 1 is the one people skip. It is the one that catches the leak.
