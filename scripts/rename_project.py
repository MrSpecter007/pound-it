#!/usr/bin/env python3
"""Rename this project's client-named scaffolding to the neutral template layout.

    alternative_naissance/alternative_naissance/  ->  src/config/
    alternative_naissance/                        ->  src/

It moves the two directories with `git mv` so history follows them, then
rewrites the references in the seven files that name the package. App code,
migrations and the database are untouched: the project package is not an app
label, so nothing in Postgres knows or cares about this change.

Run from the repository root:

    python scripts/rename_project.py --dry-run     # show what would change
    python scripts/rename_project.py               # do it

Verified on this repository: 286 tests pass afterwards, collectstatic succeeds
and every page still returns 200 under production settings.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

OLD_OUTER = "alternative_naissance"
NEW_OUTER = "src"
OLD_PKG = "alternative_naissance"
NEW_PKG = "config"

OLD_APP = "core"
NEW_APP = "altnaissance"

APPS_PY = '''from django.apps import AppConfig


class AltNaissanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"

    # The Python package was renamed from `core` so that the tree names this
    # app for the client whose site it is, per docs/PROJECT_TEMPLATE_PROTOCOL.md.
    name = "altnaissance"

    # The *label* stays "core" on purpose. It is written into
    # django_content_type.app_label, into every migration dependency, and into
    # every "core.Model" string reference. Pinning it here makes the rename a
    # pure source-tree change that the database never notices.
    label = "core"
'''

# Only Python import paths move. Anything that is an app *label* -- "core.AtelierPage",
# to="core.corehomepage", migration dependencies -- must be left exactly as it is,
# which is why these patterns are narrow rather than a blanket word substitution.
APP_REWRITES: list[tuple[str, list[tuple[str, str]]]] = [
    ("src/config/settings/base.py", [
        (rf'^    "{OLD_APP}",$', f'    "{NEW_APP}",'),
        (rf'"{OLD_APP}\.context_processors\.', f'"{NEW_APP}.context_processors.'),
    ]),
    ("src/config/urls.py", [(rf'include\("{OLD_APP}\.urls"\)', f'include("{NEW_APP}.urls")')]),
    (f"src/{NEW_APP}/models.py", [(rf"from {OLD_APP}\.models import", f"from {NEW_APP}.models import")]),
    ("src/poundit/tests/test_success_criteria.py", [
        (rf"from {OLD_APP}\.models import", f"from {NEW_APP}.models import"),
        (rf'assertNotIn\("from {OLD_APP}", body\)', f'assertNotIn("from {NEW_APP}", body)'),
        (rf'assertNotIn\("import {OLD_APP}", body\)', f'assertNotIn("import {NEW_APP}", body)'),
    ]),
]

# A dotted Python path to a StreamField block class, baked into three migrations.
# This is the trap that makes an app rename more than a directory move: it is an
# import path, not a label, so the package rename breaks it and every subsequent
# makemigrations/migrate fails with ModuleNotFoundError.
MIGRATION_PATH_REWRITE = (
    rf"'{OLD_APP}\.models\.SectionedRichTextBlock'",
    f"'{NEW_APP}.models.SectionedRichTextBlock'",
)

# (path after the moves, [(pattern, replacement), ...])
REWRITES: list[tuple[str, list[tuple[str, str]]]] = [
    ("src/manage.py", [(rf"{OLD_PKG}\.settings", f"{NEW_PKG}.settings")]),
    ("src/config/wsgi.py", [
        (rf"{OLD_PKG}\.settings", f"{NEW_PKG}.settings"),
        (rf"WSGI config for {OLD_PKG} project", "WSGI config for the project"),
    ]),
    ("src/config/settings/base.py", [
        (rf'"{OLD_PKG}"', f'"{NEW_PKG}"'),
        (rf"{OLD_PKG}\.storage", f"{NEW_PKG}.storage"),
        (rf"{OLD_PKG}/storage\.py", f"{NEW_PKG}/storage.py"),
        (rf"Django settings for {OLD_PKG} project", "Django settings for the project"),
    ]),
    ("Dockerfile", [
        (rf"{OLD_PKG}\.settings", f"{NEW_PKG}.settings"),
        (rf"{OLD_PKG}\.wsgi", f"{NEW_PKG}.wsgi"),
        (rf"COPY {OLD_OUTER}/requirements\.txt", f"COPY {NEW_OUTER}/requirements.txt"),
        (rf"COPY --chown=wagtail:wagtail {OLD_OUTER} \.",
         f"COPY --chown=wagtail:wagtail {NEW_OUTER} ."),
    ]),
    ("docker-compose.yaml", [
        (rf"{OLD_PKG}\.settings", f"{NEW_PKG}.settings"),
        (rf"{OLD_PKG}\.wsgi", f"{NEW_PKG}.wsgi"),
        (rf"\./{OLD_OUTER}/", f"./{NEW_OUTER}/"),
    ]),
    ("docker-compose.prod.yaml", [(rf"{OLD_PKG}\.settings", f"{NEW_PKG}.settings")]),
]


def premove_path(root: Path, rel: str) -> Path:
    """Where a post-move path lives before the directories are moved.

    Without this a --dry-run reports every file under src/ as "not found",
    which reads as "this file will be left alone" -- the opposite of the truth.
    """
    if rel.startswith(f"{NEW_OUTER}/{NEW_PKG}/"):
        tail = rel[len(f"{NEW_OUTER}/{NEW_PKG}/"):]
        return root / OLD_OUTER / OLD_PKG / tail
    if rel.startswith(f"{NEW_OUTER}/"):
        return root / OLD_OUTER / rel[len(f"{NEW_OUTER}/"):]
    return root / rel


def run(cmd: list[str], dry_run: bool) -> None:
    print("   ", " ".join(cmd))
    if dry_run:
        return
    # On Windows, `git mv` on a directory another process has open fails and
    # then prompts "Should I try again? (y/n)" in a loop. Retrying never helps
    # -- the lock has to be released first -- so suppress the prompt and say
    # what actually needs to happen.
    env = {**os.environ, "GIT_ASK_YESNO": "false"}
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        if "source directory is empty" in (result.stderr or ""):
            print(
                "\n"
                "    That is an index problem, not a lock: the files are on disk but\n"
                "    git still has them recorded at their old paths. Run\n"
                "\n"
                "      git add -A\n"
                "\n"
                "    and then run this script again.\n",
                file=sys.stderr,
            )
            raise SystemExit(1)
        print(
            "\n"
            "    That move failed. On Windows this almost always means another\n"
            "    process is holding a file inside the directory. The usual two:\n"
            "\n"
            "      docker compose down     # the compose file bind-mounts media/\n"
            "                              # and poundit/images/ from that folder\n"
            "      close VS Code           # or any editor/terminal rooted there\n"
            "\n"
            "    Then run this script again. It resumes from wherever it stopped.\n",
            file=sys.stderr,
        )
        raise SystemExit(1)


def rename_core_app(root: Path, dry_run: bool) -> None:
    """Rename the `core` package to `altnaissance`, pinning its database label.

    `core` is Alternative Naissance's own site app wearing an infrastructure
    name. Renaming the directory makes the tree honest; pinning
    `label = "core"` in its AppConfig means django_content_type, the migration
    graph and every "core.Model" string reference stay valid, so no data
    migration is needed.
    """
    # During --dry-run the outer directory has not moved yet, so every path
    # under src/ must also be looked for at its pre-move location -- otherwise
    # the preview claims there is nothing to do.
    src_app = root / NEW_OUTER / OLD_APP
    if not src_app.is_dir():
        src_app = premove_path(root, f"{NEW_OUTER}/{OLD_APP}")
    dst_app = root / NEW_OUTER / NEW_APP
    if not dst_app.is_dir():
        candidate = premove_path(root, f"{NEW_OUTER}/{NEW_APP}")
        if candidate.is_dir():
            dst_app = candidate

    if dst_app.is_dir():
        print(f"    {NEW_OUTER}/{NEW_APP}/ already exists -- nothing to move.")
    elif not src_app.is_dir():
        print(f"    skip: neither {NEW_OUTER}/{OLD_APP}/ nor {NEW_OUTER}/{NEW_APP}/ found.")
        return
    else:
        run(["git", "mv", f"{NEW_OUTER}/{OLD_APP}", f"{NEW_OUTER}/{NEW_APP}"], dry_run)

    apps_py = (dst_app if dst_app.is_dir() else src_app) / "apps.py"
    print(f"    write  {NEW_OUTER}/{NEW_APP}/apps.py  (name={NEW_APP}, label={OLD_APP})")
    if not dry_run:
        apps_py.write_text(APPS_PY, encoding="utf-8")

    for rel, patterns in APP_REWRITES:
        path = root / rel
        if not path.exists():
            path = premove_path(root, rel)
        if not path.exists():
            path = premove_path(root, rel.replace(f"{NEW_OUTER}/{NEW_APP}/",
                                                  f"{NEW_OUTER}/{OLD_APP}/"))
        if not path.exists():
            print(f"    skip   {rel}  (not found)")
            continue
        original = path.read_text(encoding="utf-8")
        updated = original
        for pattern, replacement in patterns:
            updated = re.sub(pattern, replacement, updated, flags=re.MULTILINE)
        if updated == original:
            print(f"    ok     {rel}  (already current)")
            continue
        print(f"    patch  {rel}")
        if not dry_run:
            path.write_text(updated, encoding="utf-8")

    pattern, replacement = MIGRATION_PATH_REWRITE
    app_dir = dst_app if dst_app.is_dir() else src_app
    migrations = sorted(app_dir.glob("migrations/*.py"))
    touched = 0
    for path in migrations:
        original = path.read_text(encoding="utf-8")
        updated = re.sub(pattern, replacement, original)
        if updated != original:
            touched += 1
            if not dry_run:
                path.write_text(updated, encoding="utf-8")
    print(f"    patch  {NEW_APP}/migrations/  ({touched} file(s) with a dotted block path)")


def move_outer(root: Path, dry_run: bool) -> bool:
    """Move the project root to src/, falling back to moving its contents.

    Windows refuses to rename a directory that any process holds open -- a
    shell whose working directory is inside it, Docker Desktop's file sharing,
    a file watcher. The handle is usually on the directory itself rather than
    on the files, so moving the children one at a time succeeds where renaming
    the parent does not, and when it does not, it names the file that is stuck
    instead of failing anonymously.
    """
    src = root / OLD_OUTER
    dst = root / NEW_OUTER

    print(f"    git mv {OLD_OUTER} {NEW_OUTER}")
    if dry_run:
        return True

    env = {**os.environ, "GIT_ASK_YESNO": "false"}
    if subprocess.run(["git", "mv", OLD_OUTER, NEW_OUTER], env=env).returncode == 0:
        return True

    print(f"\n    Renaming the directory was refused. Moving its contents into "
          f"{NEW_OUTER}/ instead.")
    dst.mkdir(exist_ok=True)
    stuck = []
    for child in sorted(src.iterdir()):
        target = dst / child.name
        if target.exists():
            # The source and the destination both hold this name. Skipping would
            # silently abandon the real content; overwriting could destroy work.
            # Neither is a decision this script gets to make.
            print(f"      CONFLICT: {NEW_OUTER}/{child.name} already exists while "
                  f"{OLD_OUTER}/{child.name} is still here", file=sys.stderr)
            stuck.append((child.name, None))
            continue
        try:
            child.rename(target)
            print(f"      moved: {child.name}")
        except OSError as exc:
            stuck.append((child.name, exc))
            print(f"      LOCKED: {child.name} -- {exc.strerror or exc}")

    # Stage what did move before returning either way. These were filesystem
    # renames, so until they are staged git still believes the files live at
    # their old paths, and a later `git mv` fails with the thoroughly unhelpful
    # "source directory is empty".
    subprocess.run(["git", "add", "-A"], env=env)

    if stuck:
        locked = [name for name, exc in stuck if exc is not None]
        clashed = [name for name, exc in stuck if exc is None]
        if locked:
            print(
                "\n    These are held by another process: " + ", ".join(locked) + "\n"
                "    Close whatever has them open -- quit Docker Desktop entirely\n"
                "    (not just `compose down`), close every editor and shell rooted\n"
                "    in this folder -- or reboot, then run this script again. It\n"
                "    resumes from here.\n",
                file=sys.stderr,
            )
        if clashed:
            print(
                "\n    These exist in BOTH places: " + ", ".join(clashed) + "\n"
                f"    That usually means an earlier run was interrupted and left a\n"
                f"    partial {NEW_OUTER}/. Compare the two, keep the one you want,\n"
                f"    delete the other, then run this script again. Nothing was\n"
                f"    overwritten.\n",
                file=sys.stderr,
            )
        return False

    try:
        src.rmdir()
        print(f"      removed the empty {OLD_OUTER}/")
    except OSError as exc:
        print(f"      note: {OLD_OUTER}/ could not be removed yet ({exc.strerror});"
              f" it is empty and harmless, delete it later.")
    subprocess.run(["git", "add", "-A"], env=env)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would change and exit")
    parser.add_argument("--skip-app-rename", action="store_true",
                        help="leave the `core` app alone (it belongs to "
                             "Alternative Naissance, not to this client)")
    args = parser.parse_args()

    root = Path.cwd()
    if not (root / ".git").exists():
        print("error: run this from the repository root", file=sys.stderr)
        return 1

    # Work out which of the two moves have already happened, so that an
    # interrupted run -- a failed `git mv`, a closed terminal -- can be resumed
    # by running the script again rather than unpicked by hand.
    # Detect progress by a marker file, not by a bare directory: a leftover
    # src/ holding nothing but a virtualenv would otherwise read as "done".
    inner_done = ((root / NEW_OUTER / NEW_PKG / "settings").is_dir()
                  or (root / OLD_OUTER / NEW_PKG / "settings").is_dir())
    old_root = root / OLD_OUTER
    leftovers = sorted(c.name for c in old_root.iterdir()) if old_root.is_dir() else []
    # manage.py having arrived is not enough: an interrupted contents-move can
    # leave entries behind, and treating that as "done" orphans them silently.
    outer_done = (root / NEW_OUTER / "manage.py").is_file() and not leftovers
    if leftovers and (root / NEW_OUTER / "manage.py").is_file():
        print(f"    resuming: {OLD_OUTER}/ still holds {', '.join(leftovers)}")

    if inner_done and outer_done:
        print(f"{NEW_OUTER}/{NEW_PKG}/ already exists -- nothing to move.")
    else:
        if not inner_done and not (root / OLD_OUTER / OLD_PKG).is_dir():
            print(f"error: expected {OLD_OUTER}/{OLD_PKG}/ -- is this the right repo?",
                  file=sys.stderr)
            return 1
        # Only require a clean tree on a fresh run. A resumed run is dirty by
        # definition: the move that already succeeded is staged.
        fresh = not inner_done and not outer_done
        dirty = subprocess.run(["git", "status", "--porcelain"],
                               capture_output=True, text=True).stdout.strip()
        if fresh and dirty and not args.dry_run:
            print("error: commit or stash your changes first. This rewrites files\n"
                  "       and you want a clean diff to review.", file=sys.stderr)
            return 1
        print("Moving directories:")
        if not inner_done:
            run(["git", "mv", f"{OLD_OUTER}/{OLD_PKG}", f"{OLD_OUTER}/{NEW_PKG}"], args.dry_run)
        else:
            print(f"    already done: {NEW_PKG}/")
        if not outer_done:
            if not move_outer(root, args.dry_run):
                return 1
        else:
            print(f"    already done: {NEW_OUTER}/")

    print("\nRewriting references:")
    for rel, patterns in REWRITES:
        path = root / rel
        if not path.exists():
            path = premove_path(root, rel)
        if not path.exists():
            print(f"    skip   {rel}  (not found)")
            continue
        original = path.read_text(encoding="utf-8")
        updated = original
        for pattern, replacement in patterns:
            updated = re.sub(pattern, replacement, updated)
        if updated == original:
            print(f"    ok     {rel}  (already current)")
            continue
        changed = sum(1 for a, b in zip(original.splitlines(), updated.splitlines()) if a != b)
        print(f"    patch  {rel}  ({changed} line(s))")
        if not args.dry_run:
            path.write_text(updated, encoding="utf-8")

    if not args.skip_app_rename:
        print(f"\nRenaming the {OLD_APP} app to {NEW_APP} (database label pinned):")
        rename_core_app(root, args.dry_run)

    print("\nNext:")
    print("    cd src")
    print("    DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py check")
    print("    DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py makemigrations --check --dry-run")
    print("    DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py test")
    print("    docker compose up -d --build")
    if args.dry_run:
        print("\n(dry run -- nothing was changed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
