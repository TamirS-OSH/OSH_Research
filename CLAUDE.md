# CLAUDE.md

Context for anyone, human or Claude, picking up this repo. The previous maintainer left IIOSH in October 2026 and handed the automation over. This file holds what isn't obvious from the code.

## First steps for the new analyst (do these before anything else)

The handover in October 2026 left two gaps that only you can close:

1. **Get into both automation accounts and make their 2FA yours.** The accounts are GitHub **`iiosh-research`** and Gmail **`iiosh.news@gmail.com`**. The git-ignored `secrets.txt` in the server copy of this folder has the Cloud project details and the trigger's token, but **may not have the account passwords or the 2FA recovery/backup codes**. If it doesn't, get them from IIOSH IT or the previous maintainer **before their accounts are deleted**. Then make 2FA yours, and store the new codes with IT:
   - **GitHub had no 2FA at all at handover (2026-10-05)**, so only its password protects it. Turn 2FA on with your own authenticator app (Settings → Password and authentication → Enable two-factor authentication), and save the recovery codes.
   - **Gmail has 2-Step Verification on, set up by the previous maintainer.** Replace their device with yours (Google prompt / Authenticator), and update the recovery phone and email (HANDOVER.md Part 2, steps 1–2). Don't turn 2-Step Verification off, because that deletes the app password the newsletter sends with. Without these, nobody can fix anything if a password or phone is lost.
2. **Replace the Gemini key with one from your own Google account. Deadline: before the previous maintainer's account `tamirs-google@osh.org.il` is deleted.** The `GEMINI_API_KEY` secret still holds their personal free-tier key. Keys from `iiosh.news` don't work, because Google gives that account no free tier. If this is missed, the newsletter still goes out, but every summary reads *"summary unavailable"*. Steps: HANDOVER.md → Progress, open item 1.
3. **Check that the weekly run works.** It runs on Sunday mornings; HANDOVER.md Part 10 has what to look for. The first real run after the handover is 2026-10-11.
4. **Read "Rules that are easy to break" in CLAUDE.md** before running anything. In particular, leaving `dry_run_email` empty in *Run workflow* emails every recipient.

**Read first:**
- [HANDOVER.md](HANDOVER.md) → **Progress** (top of the file): what's done and what's still open. It's kept current; update it when you finish something.
- [README.md](README.md): what the pipelines do, adding a journal, recipients, dry runs.
- [docs/](docs/): background on the dashboard and the newsletter pipeline.

## Where everything lives (no secrets here — the repo is public)

| Thing | Where |
|---|---|
| Repo, Actions, Pages | GitHub account **`iiosh-research`** (a machine account made for this; its email is `iiosh.news@gmail.com`). Repo `iiosh-research/OSH_Research`. Newsletter at `https://iiosh-research.github.io/OSH_Research/` |
| Email sender + all Google-side items | Gmail account **`iiosh.news@gmail.com`**, also a machine account |
| Dashboard job's Google login | Google Cloud project **`iiosh-automation`** (owned by `iiosh.news`), service account `journal-dashboard-bot@iiosh-automation.iam.gserviceaccount.com`, Workload Identity pool `github-actions-pool` / provider `github-provider`. The workflow reads repository **variables** `GCP_WIF_PROVIDER` and `GCP_SERVICE_ACCOUNT` |
| Dashboard data | Google Sheet **"IIOSH Dashboard Data"** in `iiosh.news`'s Drive. Tabs: `גיליון1` (articles, rewritten weekly) and `Journal Metadata` (maintained by hand) |
| Dashboard | Looker Studio report `https://datastudio.google.com/reporting/b69400b8-a132-4605-a1f9-e37d0e2ca3ee`, owned by `iiosh.news`, shared "anyone with the link". Its two data sources are embedded in the report |
| Weekly trigger | Apps Script **"IIOSH Weekly Trigger"** in `iiosh.news`. Fires Sunday morning, Israel time. Its GitHub token never expires |
| GitHub secrets | `GEMINI_API_KEY`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `RECIPIENT_LIST` |
| **Gemini key: the maintainer's own** | `GEMINI_API_KEY` is a free-tier key from **the current maintainer's own Google account**. This was decided in 2026-10 because Google refuses free-tier keys from `iiosh.news` ("project has been denied access", tier *Unavailable*), and that account would need billing. As of 2026-10-05 the key is still the previous maintainer's (`tamirs-google@osh.org.il`), **which dies when that account is deleted**, so the new analyst must replace it with their own. Steps: HANDOVER.md → Progress, open item 1 |
| Passwords, recovery codes, 2FA | **Not in the repo.** They're in a git-ignored `secrets.txt` in the organization-server copy of this folder, and with IIOSH IT |
| Recipient list source | git-ignored `newsletter/recipients.txt` (only in the server copy, not on GitHub) |

**Gone or going with the previous maintainer's accounts. Don't use these:** Cloud project `research-497406`, the old Sheet and the old Looker report (`…/reporting/f82c0682-…`) in the work account, and the `tamirs-osh.github.io` address (now 404). Links in emails sent before 2026-10-05 point there.

## Rules that are easy to break

- **The repo is public.** Never commit `secrets.txt`, `recipients.txt` or any credentials (`.gitignore` covers them, so don't force-add). Never print an email address or secret in a workflow step; the dry-run address is masked on purpose.
- **Real vs. dry run.** *Run workflow* with `dry_run_email` empty, or running `triggerWeeklyNewsletter` in Apps Script, is a **real send to every recipient**. Test with `dry_run_email` = your address, or with `testDryRun` in Apps Script. To stop a mistaken real run, cancel it within ~10 minutes; the email is the last step.
- **Two separate journal lists, on purpose.** `JOURNAL_MAPPING` in `newsletter/newsletter.py` and the one in `dashboard/scraper.py` are deliberately separate so each pipeline can differ (grades, filters). The previous maintainer declined merging them into a shared file, so edit both when journals change. They already differ: the newsletter work-filters the general journals, while the dashboard archives everything unfiltered, including conference-abstract supplements, which is intended. A new journal also needs a row in the Sheet's `Journal Metadata` tab, or Looker hides it. See README → *Adding a Journal*.
- **Check ISSNs before adding a journal** at `https://api.openalex.org/sources/issn:<ISSN>`. A wrong ISSN silently returns 0 articles.
- **Google's login check is case-sensitive.** The Workload Identity condition and principal must say `iiosh-research/OSH_Research` in lowercase.
- **The dashboard job finds the Sheet by its exact name.** Keep exactly one Sheet called "IIOSH Dashboard Data" shared with the service account.
- **Gmail app password.** Changing the `iiosh.news` password, or turning 2-Step Verification off even briefly, deletes the app password. Then make a new one and update `GMAIL_APP_PASSWORD`.
- **Don't rename the GitHub account or repo** without HANDOVER.md Part 4. It breaks Pages links, the Google login and the trigger URL.
- **The dashboard link is hardcoded** in `newsletter/newsletter.py` (the "Check the Literature Dashboard" button) and in the README.
- **Tune the newsletter from data, not by guessing.** Changes to filters such as `WORK_TERMS_MIN_HITS` or relevance terms have repeatedly behaved differently from intuition. Test against real abstracts and compare what's gained or lost.

## Local setup notes

- The `.venv` folder that came with the copied repo was built on another machine and doesn't work. Delete it and run `python -m venv .venv`, then `pip install -r dashboard/requirements.txt -r newsletter/requirements.txt`.
- Set your own git identity (`git config --global user.name/user.email`); the history carries the previous maintainer's.
- Run status can be read without logging in: `https://api.github.com/repos/iiosh-research/OSH_Research/actions/runs`. Step **logs** need a logged-in browser.
- Windows PowerShell 5.1 gotcha: `Invoke-RestMethod` silently returns empty objects for deeply nested JSON, e.g. OpenAlex `/works`. Use `Invoke-WebRequest -UseBasicParsing | ConvertFrom-Json`, and slim responses with OpenAlex's `select=`.
- The previous machine had no `gh` or `jq`. Don't assume them.

## What to check on Sunday 2026-10-11

This is the first real run after the handover, and the first with the 7 journals added on 2026-10-04 (HANDOVER.md Part 10 has the full checklist):
- A run named **IIOSH Weekly Automation** (without "(dry run)") appears Sunday morning.
- *Read dry-run address* logs `Real run: … Links point to https://iiosh-research.github.io/OSH_Research`.
- The newsletter step logs `Email sent successfully to 9 recipients`.
- In Looker, after **Refresh data**, the record count is above 26,398 (the count on 2026-10-04). It should rise by roughly the number of new articles, about 150 more for *Cognition, Technology & Work*, whose ISSN was fixed.
- Afterwards, tighten the Google login to the new name only (HANDOVER.md Part 4, step 3).

## Unfinished work

**Occupational cancer edition** (branch `feat/occ-cancer-edition`, not live). This is a second newsletter for an IIOSH researcher's occupational-cancer literature monitoring, built as a second *edition* of this pipeline. Her spec is the Word file `וכנסים רשימת_כתבי_עת_למעקב_שבועי_–_גרסה_נקייה.docx` (git-ignored; in the server copy). The design and measurements are in `docs/Occupational_Cancer_Edition_Plan.md` **on that branch**, which is the source of truth. Context that isn't in the repo:
- "Private" meant a *separate audience*, not confidential, so publishing on GitHub Pages is fine.
- Her document bundles three products. Only the journal monitoring is built. Regulatory-source monitoring isn't built. Conference calls-for-abstracts turned out to be a mailing-list subscription task, not an engineering one.
- Relevance filtering was the whole difficulty. It took four measured iterations, and the pipeline logs every candidate's `score` / `core` / `occ` / matched terms so it can be tuned from data.
- Volume is deliberately low (~2–3 articles a week). Whether that's the right trade-off is the researcher's call, and it **hasn't been put to her yet**.
- **Merging into `main` will conflict.** `main` gained, in `newsletter.py`: 7 new journals; the Cognition, Technology & Work ISSN fix (1436-6556 → 1435-5558); the per-journal `"WorkFilter": True` flag with `WORK_TERMS` / `is_work_related()`; `issn` on each candidate; `interleave_by_journal()` (round-robin in both tiers); a `DRY_RUN_EMAIL` branch. All of these must be carried into the branch's `editions/iiosh.py` and its edition-aware code. The workflow on `main` has the `dry_run_email` input, the derived Pages URL and the `GCP_*` variables, while the branch has `run_dashboard` / `run_iiosh` / `run_occ` booleans; reconcile by hand. The branch also still has the old `tamirs-osh` address, the old Cloud project and the old dashboard link.

**An idea, not built:** a confirmation word for manual real runs, so *Run workflow* would require typing `SEND`, after a near-miss where a stale Run form hid the `dry_run_email` field. The Apps Script payload would then become `{ref:'main', inputs:{confirm:'SEND'}}`.

**Local branch `feat/add-journals-and-recipients-helper`** is fully merged into `main` and can be deleted.
