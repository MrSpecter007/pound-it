#!/usr/bin/env python3
"""Remove the Alternative Naissance code from this repository.

Run this ONLY after the database phase in docs/SPLIT_TO_POUNDIT_ONLY.md, which
deletes that site's pages and drops its tables. Running it first leaves rows in
wagtailcore_page whose content types point at apps that no longer exist, and the
Wagtail page explorer will not load.

This step is pure source-tree surgery:

    src/altnaissance/        removed   (Alternative Naissance's site app)
    src/servicerequests/     removed   (its service-request intake)
    src/templates/*.html     removed   (the inherited theme; Pound It's own
    src/templates/partials/            templates live in templates/poundit/)
    src/static/vendors/      removed   (1.3 MB of theme vendor assets)
    src/static/css/
    config/settings/base.py  edited    (INSTALLED_APPS, context processor)
    config/urls.py           edited    (two mounts)

Pound It's 404 and 500 templates must already be in place -- the inherited ones
load a template tag library from the app being removed, so every 404 would raise
`KeyError: 'menu_tags'` once it is gone.

    python scripts/finish_poundit_split.py --dry-run
    python scripts/finish_poundit_split.py
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

APP_DIRS = ["src/altnaissance", "src/servicerequests"]
THEME_GLOBS = ["src/templates/*.html", "src/templates/partials"]
THEME_DIRS = ["src/static/vendors", "src/static/css"]
KEEP_TEMPLATES = {"404.html", "500.html"}


def sh(cmd: list[str], dry_run: bool) -> None:
    print("   ", " ".join(cmd))
    if not dry_run:
        subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-theme", action="store_true",
                    help="remove the apps but leave the inherited theme files "
                         "in place (use if anything still references them)")
    args = ap.parse_args()

    root = Path.cwd()
    if not (root / ".git").exists() or not (root / "src").is_dir():
        print("error: run from the repository root, after scripts/rename_project.py",
              file=sys.stderr)
        return 1

    for name in ("404.html", "500.html"):
        path = root / "src" / "templates" / name
        if not path.exists():
            print(f"error: src/templates/{name} is missing. Pound It needs its own\n"
                  f"       error pages before the theme is removed.", file=sys.stderr)
            return 1
        if "poundit" not in path.read_text(encoding="utf-8").lower():
            print(f"error: src/templates/{name} still looks like the inherited\n"
                  f"       theme's version. Replace it first.", file=sys.stderr)
            return 1

    if subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                      text=True).stdout.strip() and not args.dry_run:
        print("error: commit or stash first -- you want a reviewable diff.", file=sys.stderr)
        return 1

    print("Removing the Alternative Naissance apps:")
    for rel in APP_DIRS:
        if (root / rel).exists():
            sh(["git", "rm", "-r", "-q", rel], args.dry_run)
        else:
            print(f"    already gone: {rel}")

    if args.keep_theme:
        print("\nLeaving the inherited theme in place (--keep-theme).")
    else:
        print("\nRemoving the inherited theme:")
        for path in sorted((root / "src" / "templates").glob("*.html")):
            if path.name in KEEP_TEMPLATES:
                print(f"    keeping  src/templates/{path.name}")
                continue
            sh(["git", "rm", "-q", f"src/templates/{path.name}"], args.dry_run)
        for rel in ["src/templates/partials", *THEME_DIRS]:
            if (root / rel).exists():
                sh(["git", "rm", "-r", "-q", rel], args.dry_run)

    print("\nEditing settings and urls:")
    base = root / "src/config/settings/base.py"
    text = base.read_text(encoding="utf-8")
    for line in ('    "altnaissance",\n', '    "servicerequests",\n'):
        text = text.replace(line, "")
    text = re.sub(r'\n *"altnaissance\.context_processors\.menu_context",\s*(?=\n)', "", text)
    if text != base.read_text(encoding="utf-8"):
        print("    patch  src/config/settings/base.py")
        if not args.dry_run:
            base.write_text(text, encoding="utf-8")
    else:
        print("    ok     src/config/settings/base.py (already current)")

    urls = root / "src/config/urls.py"
    text = original = urls.read_text(encoding="utf-8")
    text = text.replace("from servicerequests import urls as servicerequests_urls\n", "")
    text = re.sub(r'\n *path\("service-request/", include\(servicerequests_urls\)\),', "", text)
    text = re.sub(r'\n *path\("", include\("altnaissance\.urls"\)\),', "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if text != original:
        print("    patch  src/config/urls.py")
        if not args.dry_run:
            urls.write_text(text, encoding="utf-8")
    else:
        print("    ok     src/config/urls.py (already current)")

    print("\nNext:")
    print("    cd src")
    print("    DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py check")
    print("    DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py test poundit")
    print("    docker compose up -d --build   # then visit http://localhost:8000/")
    if args.dry_run:
        print("\n(dry run -- nothing was changed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
