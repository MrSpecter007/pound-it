# Use an official Python runtime based on Debian 12 "bookworm" as a parent image.
FROM python:3.12-slim-bookworm

# Add user that will be used in the container.
RUN useradd wagtail

# Port used by this container to serve HTTP.
EXPOSE 8000

# 1. Force Python stdout and stderr streams to be unbuffered.
# 2. PORT matches EXPOSE above.
# 3. Default to PRODUCTION settings. wsgi.py falls back to the dev module via
#    setdefault, so without this line a deployed container would run with
#    DEBUG=True, a committed SECRET_KEY and ALLOWED_HOSTS=["*"]. The safe
#    setting has to be the default; the environment can still override it.
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# Install system packages required by Wagtail and Django.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

# Install the application server.
# (pinned to a modern release: gunicorn 20.0.4 depends on pkg_resources,
# which recent setuptools no longer ships.)
RUN pip install "gunicorn==23.0.0"

# Install the project requirements.
COPY src/requirements.txt /
RUN pip install -r /requirements.txt

# Use /app folder as a directory where the source code is stored.
WORKDIR /app

RUN chown wagtail:wagtail /app

# Copy the source code of the project into the container.
COPY --chown=wagtail:wagtail src .

# Use user "wagtail" to run the build commands below and the server itself.
USER wagtail

# Collect static files, hashed and compressed by WhiteNoise.
# SECRET_KEY is required for the settings module to import at all; this value
# is used only by this build step and never at runtime.
RUN SECRET_KEY="build-step-only-not-used-at-runtime" \
    python manage.py collectstatic --noinput --clear

# Runtime command.
#
# Migrations are NOT run here. Running them on every container start races with
# anything else starting at the same time, and makes rollbacks awkward. Run
# them as an explicit step in the deploy:
#     docker compose -f docker-compose.prod.yaml run --rm app python manage.py migrate
#
# Workers: on a single vCPU these cover I/O waits rather than adding
# parallelism, so three is a reasonable ceiling.
CMD gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-3} \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
