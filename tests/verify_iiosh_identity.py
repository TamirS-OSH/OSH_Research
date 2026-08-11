"""Verify the edition refactor left the IIOSH edition's rendered output unchanged.

Renders one fixture through the pre-refactor newsletter.py (recovered from git)
and through the current one, then diffs the page HTML and the email HTML
byte-for-byte.

No network, no API key and no Gemini calls: only the pure rendering functions
are exercised, with `google.genai` stubbed out so both modules import cleanly.

    python tests/verify_iiosh_identity.py [git-ref]

The ref defaults to the pre-refactor baseline below, which is the comparison
that actually means something. Passing HEAD once the refactor is committed only
compares the file to itself.

Exit code 0 means the two outputs are identical. Any difference is printed as a
unified diff and exits 1.
"""

import difflib
import importlib.util
import os
import subprocess
import sys
import tempfile
import types

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWSLETTER_DIR = os.path.join(REPO_ROOT, "newsletter")
NEW_MODULE_PATH = os.path.join(NEWSLETTER_DIR, "newsletter.py")

# The last commit before the edition refactor. This is the only comparison that
# proves anything, so it is the default.
BASELINE_REF = "8fc7c99"

# --- Fixture -----------------------------------------------------------------
# Deliberately exercises every rendering branch: several domains, all three
# quartile grades, populated and empty domain summaries, and a global briefing
# containing the injected anchor links that build_email_body rewrites.

GLOBAL_META = {
    "en": (
        "This week's findings show that "
        "<a href='#art-1' style='color: #2563eb; text-decoration: underline;'>shift work raises "
        "injury risk by 14%</a>, while "
        "<a href='#art-3' style='color: #2563eb; text-decoration: underline;'>lifting posture "
        "predicts low-back pain</a>."
    ),
    "he": (
        "ממצאי השבוע מראים כי "
        "<a href='#art-1' style='color: #2563eb; text-decoration: underline;'>עבודה במשמרות "
        "מעלה את סיכון הפגיעה ב-14%</a>."
    ),
}


def _article(idx, grade, journal):
    return {
        "id": f"art-{idx}",
        "title": f"Test Article {idx}: Effects & Outcomes <in> Workers",
        "journal": journal,
        "grade": grade,
        "link": f"https://doi.org/10.1000/test{idx}",
        "summary_en": f"English summary number {idx} with an ampersand & angle < bracket.",
        "summary_he": f"תקציר בעברית מספר {idx} עם תו מיוחד & סוגר.",
    }


NEWSLETTER_DATA = {
    "Occupational Health": {
        "domain_summary_en": "Domain overview in English for occupational health.",
        "domain_summary_he": "סקירת תחום בעברית לבריאות תעסוקתית.",
        "articles": [_article(1, "Q1", "Scandinavian Journal of Work, Environment & Health"),
                     _article(2, "Q2", "Journal of Occupational Health")],
    },
    "General & Physical Ergonomics": {
        "domain_summary_en": "Domain overview in English for ergonomics.",
        "domain_summary_he": "סקירת תחום בעברית לארגונומיה.",
        "articles": [_article(3, "Q1/Q2", "Ergonomics")],
    },
    # Empty summaries must still render the article block but skip the summary card.
    "Musculoskeletal Health": {
        "domain_summary_en": "",
        "domain_summary_he": "",
        "articles": [_article(4, "Q2", "Clinical Biomechanics")],
    },
}

PAGE_URL = "https://tamirs-osh.github.io/OSH_Research/IIOSH_Research_Update_2026-08-11.html"


# --- Module loading ----------------------------------------------------------

def _stub_genai():
    """Install a no-op google.genai so importing either module needs no API key."""
    google = sys.modules.get("google") or types.ModuleType("google")
    genai = types.ModuleType("google.genai")

    class _Client:
        def __init__(self, *args, **kwargs):
            self.models = None

    genai.Client = _Client
    google.genai = genai
    sys.modules["google"] = google
    sys.modules["google.genai"] = genai


def _load_module(path, name):
    """Import a newsletter.py by path.

    The repo's newsletter/ directory goes on sys.path regardless of where the
    file itself lives, so a post-refactor revision recovered into a temp dir can
    still resolve `import editions`.
    """
    added = [d for d in (os.path.dirname(path), NEWSLETTER_DIR) if d not in sys.path]
    for directory in added:
        sys.path.insert(0, directory)
    # The new module parses --edition at import time; keep argv clean so it
    # takes its default (iiosh) rather than this script's arguments.
    saved_argv = sys.argv
    sys.argv = [name]
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.argv = saved_argv
        for directory in added:
            sys.path.remove(directory)


def _render(module):
    """Return (page_html, email_html). Runs in a temp cwd — generate_local_html
    writes a file as a side effect and we don't want it in the repo."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            page_html, _filename = module.generate_local_html(NEWSLETTER_DATA, GLOBAL_META)
            email_html = module.build_email_body(GLOBAL_META, PAGE_URL)
        finally:
            os.chdir(original_cwd)
    return page_html, email_html


def _diff(label, old, new):
    if old == new:
        print(f"  OK   {label}: identical ({len(new)} chars)")
        return True
    print(f"  FAIL {label}: outputs differ")
    delta = difflib.unified_diff(
        (old or "").splitlines(), (new or "").splitlines(),
        fromfile=f"old/{label}", tofile=f"new/{label}", lineterm="", n=2,
    )
    for line in list(delta)[:80]:
        print("       " + line)
    return False


def main():
    ref = sys.argv[1] if len(sys.argv) > 1 else BASELINE_REF
    print(f"Comparing current newsletter.py against ref '{ref}'...\n")
    if subprocess.run(["git", "merge-base", "--is-ancestor", ref, "HEAD"],
                      cwd=REPO_ROOT).returncode == 0:
        same = subprocess.run(
            ["git", "diff", "--quiet", ref, "--", "newsletter/newsletter.py"],
            cwd=REPO_ROOT,
        ).returncode == 0
        if same:
            print(f"'{ref}' has the same newsletter.py as the working tree — "
                  f"this would compare the file to itself. Pass an earlier ref.")
            return 2

    try:
        old_source = subprocess.check_output(
            ["git", "show", f"{ref}:newsletter/newsletter.py"], cwd=REPO_ROOT
        )
    except subprocess.CalledProcessError:
        print(f"Could not read newsletter/newsletter.py at ref '{ref}'.")
        return 2

    _stub_genai()

    with tempfile.TemporaryDirectory() as tmp:
        old_path = os.path.join(tmp, "old_newsletter.py")
        with open(old_path, "wb") as handle:
            handle.write(old_source)

        old_module = _load_module(old_path, "old_newsletter")
        new_module = _load_module(NEW_MODULE_PATH, "new_newsletter")

        if new_module.EDITION["slug"] != "iiosh":
            print("Refusing to compare: the current module did not default to the iiosh edition.")
            return 2

        old_page, old_email = _render(old_module)
        new_page, new_email = _render(new_module)

    print("Results:")
    ok = _diff("page html", old_page, new_page)
    ok = _diff("email html", old_email, new_email) and ok

    print()
    if ok:
        print("PASS - the IIOSH edition renders byte-identically after the refactor.")
        return 0
    print("FAIL - the refactor changed IIOSH output. Do not merge.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
