"""Edition configs for the research newsletter pipeline.

Each edition is a module exposing an ``EDITION`` dict. ``newsletter.py`` is
edition-agnostic and selects one at runtime via ``--edition <slug>``.

Adding an edition means adding a module here — no changes to the core pipeline.
Optional stages (keyword filtering, tracked-author feeds) are no-ops when the
edition leaves their keys empty, so existing editions are unaffected.
"""

import importlib

AVAILABLE = ("iiosh", "occ_cancer")


def load(slug):
    """Return the EDITION dict for ``slug``, or exit with a usable message."""
    if slug not in AVAILABLE:
        raise SystemExit(
            f"Unknown edition '{slug}'. Available editions: {', '.join(AVAILABLE)}"
        )
    module = importlib.import_module(f"editions.{slug}")
    edition = module.EDITION

    # Fail loudly at startup rather than producing a half-configured newsletter.
    for key in ("slug", "file_prefix", "recipient_env", "journals", "selection"):
        if not edition.get(key):
            raise SystemExit(f"Edition '{slug}' is missing required key '{key}'.")
    return edition
