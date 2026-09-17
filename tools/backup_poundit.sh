#!/bin/bash
# Run as deploy; keep backups private because they contain credentials and submissions.
set -euo pipefail
umask 077
cd /home/deploy/poundit
backup_dir=/home/deploy/backups
mkdir -p "$backup_dir"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
docker compose -f docker-compose.prod.yaml exec -T postgres \
  sh -c 'pg_dump -Fc --no-owner --no-acl -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  > "$backup_dir/db-$stamp.dump.partial"
mv "$backup_dir/db-$stamp.dump.partial" "$backup_dir/db-$stamp.dump"
tar -czf "$backup_dir/media-$stamp.tar.gz" media
tar -czf "$backup_dir/config-$stamp.tar.gz" .env Caddyfile docker-compose.prod.yaml DEPLOYED_REVISION
# Keep the most recent 14 days. Match only artifacts created by this script.
find "$backup_dir" -maxdepth 1 -type f \
  \( -name 'db-*.dump' -o -name 'media-*.tar.gz' -o -name 'config-*.tar.gz' \) \
  -mtime +14 -delete
