"""
Static file storage for this project.

Why this file exists
--------------------
Production serves static files through WhiteNoise with hashed filenames, so
that CSS, JS, fonts and images can be cached by browsers indefinitely. Hashing
is done by Django's ManifestStaticFilesStorage, which rewrites every `url(...)`
reference inside a CSS file to point at the hashed version of its target.

That rewriting is strict: if a stylesheet references a file that is not in the
static tree, `collectstatic` raises and the whole build fails.

Five of the vendor stylesheets inherited with the site theme reference images
that were never committed with them (jQuery UI's icon sprites, owl-carousel's
video play button, bxslider's loader, vegas' overlay, timepicker's sprite).
Those references are already broken today and were broken before this change;
the images do not exist anywhere in the repository. They are cosmetic pieces of
third-party widget CSS, and fabricating ten placeholder binaries inside vendor
libraries would be worse than leaving them missing.

What this class changes
-----------------------
A missing reference becomes a logged warning instead of a failed deployment.
The stylesheet is still collected, still hashed and still served; what is
abandoned is the rewriting pass for that one file, so its dead reference stays
exactly as dead as it is today, and any other references in the same file may
keep their original unhashed names. Nothing that works stops working.

Everything that resolves cleanly -- which is every file this project owns --
is hashed, rewritten and compressed exactly as before.

The warning is deliberately loud. If a stylesheet we own ever shows up in the
deploy log here, that is a real bug to fix, not a line to ignore.
"""

from __future__ import annotations

import logging

from whitenoise.storage import CompressedManifestStaticFilesStorage, MissingFileError

logger = logging.getLogger(__name__)


class TolerantCompressedManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Hash and compress static files; warn, don't fail, on a dead reference."""

    def hashed_name(self, name, content=None, filename=None):
        """Fall back to the plain name when the source file is not there.

        Django raises ValueError here, which turns a missing decorative image
        into a 500 for the whole page. It also means `manage.py test` cannot
        run until someone has run `collectstatic`, because DEBUG is off in
        tests and every {% static %} lookup then goes through this method.

        Neither is worth a broken page. A reference that cannot be resolved
        renders as the unhashed URL -- the same 404 for that one asset that
        the project produced before filenames were hashed.

        Expect a burst of these warnings once per worker process, when
        WhiteNoise first indexes STATIC_ROOT. The inherited site theme
        references a number of vendor files it does not ship (non-minified
        sources, .map files); those were already 404ing before filenames were
        hashed. They are worth cleaning up, but they are not this file's job.
        """
        try:
            return super().hashed_name(name, content, filename)
        except ValueError as exc:
            if "could not be found" not in str(exc):
                raise
            logger.warning(
                "Static reference %r cannot be resolved; serving it unhashed. "
                "Either the file is genuinely missing, or collectstatic has not "
                "run in this environment.",
                name,
            )
            return name

    def post_process(self, *args, **kwargs):
        for name, hashed_name, processed in super().post_process(*args, **kwargs):
            if isinstance(processed, MissingFileError):
                logger.warning(
                    "Static file %s references a file that does not exist, so it "
                    "will be served without a content hash: %s",
                    name,
                    processed.args[0].splitlines()[0] if processed.args else processed,
                )
                continue
            yield name, hashed_name, processed
