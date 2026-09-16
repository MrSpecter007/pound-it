# Deploying Pound It to a Hostinger KVM 1

KVM 1 is 1 vCPU, 4 GB RAM, 50 GB NVMe, 4 TB transfer. That is comfortable for
this site — the constraint is the single core, which matters in two places:
the Docker build is slow (budget 10–15 minutes), and gunicorn gets 3 workers
covering I/O waits rather than adding parallelism.

Paths below assume the rename is done: the project root is `src/`, the settings
module is `config.settings.production`.

---

## 0. Two decisions before you start

**Domain.** `pounditdj.com` is on Wix today. Pointing its A record at the VPS
takes the Wix site down at the moment DNS propagates. Deploy to a staging name
first — `new.pounditdj.com` — verify everything, then cut the apex over. The
Caddyfile takes a list of hostnames, so this is a one-line change later.

**Whether Alternative Naissance is still in the code.** If you have not run
`docs/SPLIT_TO_POUNDIT_ONLY.md`, the image still contains that app and its URL
mounts, and `/service-request/` will answer on the Pound It domain. Deploying
before the split works, but do the split first if you can.

---

## 1. Create and secure the server

Hostinger panel → VPS → **Ubuntu 24.04 LTS**, no control panel. Add your SSH
public key during creation so root login by password is never enabled.

```bash
ssh root@YOUR_SERVER_IP

adduser deploy
usermod -aG sudo deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy/

# Refuse password logins and direct root login.
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

apt update && apt upgrade -y
apt install -y unattended-upgrades
dpkg-reconfigure --priority=low unattended-upgrades
```

Open a **second terminal** and confirm `ssh deploy@YOUR_SERVER_IP` works before
closing the root session. Locking yourself out of a fresh VPS is recoverable
only through Hostinger's console.

### Swap

4 GB of RAM is enough to run this, but the Docker build peaks higher. 2 GB of
swap costs 2 GB of disk and prevents the build being OOM-killed:

```bash
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
sysctl vm.swappiness=10 && echo 'vm.swappiness=10' >> /etc/sysctl.conf
```

## 2. Install Docker

```bash
ssh deploy@YOUR_SERVER_IP

curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy
exit        # group membership needs a fresh login
```

Log back in and check `docker compose version` returns v2.x.

## 3. Get the code

The repository is private, so the server needs its own read-only key.

```bash
ssh-keygen -t ed25519 -C "poundit-vps" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

Paste that into GitHub → the `pound-it` repo → Settings → Deploy keys → Add,
**read-only**. A deploy key is scoped to one repository; a personal access
token is not.

```bash
git clone git@github.com:MrSpecter007/pound-it.git ~/poundit
cd ~/poundit
```

## 4. Configure

```bash
cp docs/PRODUCTION_ENV_TEMPLATE.txt .env
chmod 600 .env
docker run --rm python:3.12-slim python -c \
  "import secrets; print(secrets.token_urlsafe(64))"     # SECRET_KEY
openssl rand -base64 24                                   # POSTGRES_PASSWORD
nano .env
```

Every value must be filled. The ones that fail loudly if wrong:

| Variable | Value | If wrong |
|---|---|---|
| `ALLOWED_HOSTS` | `new.pounditdj.com` — comma separated, no scheme | 400 on every request |
| `CSRF_TRUSTED_ORIGINS` | `https://new.pounditdj.com` — **with** scheme | admin login and the inquiry form fail |
| `WAGTAILADMIN_BASE_URL` | `https://new.pounditdj.com` | broken links in notification emails |
| `SECRET_KEY` | the generated value | container refuses to start (deliberate) |
| `SECURE_HSTS_SECONDS` | `300` for now | see step 9 |

Then set the hostname in the Caddyfile — it ships with the apex, and for a
staging deploy you want only the staging name:

```bash
nano Caddyfile        # first line: new.pounditdj.com {
```

## 5. DNS

In your DNS provider, an **A** record for `new` → `YOUR_SERVER_IP`, TTL 300.

```bash
dig +short new.pounditdj.com     # must return your IP before step 6
```

Caddy requests a certificate on first boot. If DNS has not propagated, that
request fails and it backs off — so wait for `dig` to answer correctly.

## 6. Build and start

```bash
cd ~/poundit
docker compose -f docker-compose.prod.yaml up -d --build
docker compose -f docker-compose.prod.yaml ps
```

Ten to fifteen minutes on one core. `postgres` and `caddy` should be `running`,
`app` `running (healthy)` after its 45-second start period.

Migrations do **not** run on start — that is deliberate, so two containers
starting at once cannot race each other:

```bash
docker compose -f docker-compose.prod.yaml run --rm app python manage.py migrate
```

## 7. Load the content

Your local database holds the real Pound It content — pages, the faculty
portraits, the schedule. Move it up rather than re-seeding, so the site arrives
exactly as you last saw it.

**On your Windows machine:**

```powershell
cd C:\Users\15145\Documents\GitHub\Alternative-Naissance
docker compose exec -T postgres pg_dump -U myuser --no-owner --no-acl mydatabase > poundit-content.sql
scp poundit-content.sql deploy@YOUR_SERVER_IP:~/
scp -r src\media\* deploy@YOUR_SERVER_IP:~/poundit/media/
```

`--no-owner --no-acl` matters: the server's database user is not `myuser`, and
without those flags the restore throws ownership errors on every object.

**On the server:**

```bash
mkdir -p ~/poundit/media
docker compose -f docker-compose.prod.yaml exec -T postgres \
  psql -U "$(grep POSTGRES_USER .env | cut -d= -f2)" \
       -d "$(grep POSTGRES_DB .env | cut -d= -f2)" < ~/poundit-content.sql

docker compose -f docker-compose.prod.yaml run --rm app python manage.py migrate
shred -u ~/poundit-content.sql        # it contains password hashes
```

Then point Wagtail's Site record at the real hostname, or the pages will render
with `localhost` URLs:

```bash
docker compose -f docker-compose.prod.yaml run --rm app python manage.py shell
```

```python
from wagtail.models import Site
s = Site.objects.get(is_default_site=True)
s.hostname, s.port = "new.pounditdj.com", 443
s.save()
print(s)
```

## 8. Verify

```bash
curl -sI https://new.pounditdj.com/ | head -3          # 200, and HTTPS worked
curl -sI https://new.pounditdj.com/static/poundit/poundit.css | head -3
docker compose -f docker-compose.prod.yaml logs app --tail 50
```

In a browser, walk: home, schedule (the grid and the colour key), faculty (the
portraits — these come from the media copy, so a missing image means step 7's
`scp` did not land), programs, events, the legal pages, a deliberate 404, the
Wagtail admin login, and submit the school inquiry form.

Expect a burst of `Static reference ... cannot be resolved` warnings once per
worker at startup. Those are the inherited theme's missing vendor files and are
harmless — see `src/config/storage.py`.

## 9. Harden, once it is proven

After a day of the certificate working, raise HSTS from 5 minutes to a year.
Do not do this earlier: browsers cache it, and it is painful to walk back.

```bash
sed -i 's/^SECURE_HSTS_SECONDS=.*/SECURE_HSTS_SECONDS=31536000/' .env
docker compose -f docker-compose.prod.yaml up -d
```

## 10. Backups

Nothing here is backed up by Hostinger unless you bought that option. The
database is the part you cannot recreate.

```bash
mkdir -p ~/backups
cat > ~/backup-poundit.sh <<'EOF'
#!/bin/bash
set -euo pipefail
cd ~/poundit
DAY=$(date +%F)
docker compose -f docker-compose.prod.yaml exec -T postgres \
  pg_dump -U "$(grep POSTGRES_USER .env | cut -d= -f2)" \
          "$(grep POSTGRES_DB .env | cut -d= -f2)" | gzip > ~/backups/db-$DAY.sql.gz
tar czf ~/backups/media-$DAY.tar.gz -C ~/poundit media
find ~/backups -name '*.gz' -mtime +14 -delete
EOF
chmod +x ~/backup-poundit.sh
( crontab -l 2>/dev/null; echo "15 3 * * * ~/backup-poundit.sh" ) | crontab -
```

A backup on the same disk as the thing it backs up is half a backup. Copy
`~/backups` off the VPS periodically — `scp`, or Hostinger's snapshots.

## 11. Deploying a change

```bash
cd ~/poundit
git pull
docker compose -f docker-compose.prod.yaml up -d --build
docker compose -f docker-compose.prod.yaml run --rm app python manage.py migrate
```

Static files are collected during the build, so no separate step. Run the
backup script first if the change touches models.

## 12. Cutting the domain over

Once staging is proven:

```bash
nano Caddyfile     # pounditdj.com, www.pounditdj.com, new.pounditdj.com {
nano .env          # add both to ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS
docker compose -f docker-compose.prod.yaml up -d
```

Update the Wagtail Site hostname as in step 7, then move the apex and `www` A
records off Wix to the server. Keep `new.` working for a while — it costs
nothing and gives you a way in if something is wrong with the apex.

Redirects from the old Wix URLs are already seeded
(`seed_poundit_redirects`); confirm a few resolve after the cutover.

## If it goes wrong

```bash
docker compose -f docker-compose.prod.yaml logs app --tail 100
docker compose -f docker-compose.prod.yaml logs caddy --tail 50
docker compose -f docker-compose.prod.yaml down        # keeps the db volume
```

`down -v` destroys the database volume. Restore is `gunzip -c backup.sql.gz |
docker compose -f docker-compose.prod.yaml exec -T postgres psql -U ... -d ...`.
