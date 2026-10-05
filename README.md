# Research Automation

Automated research monitoring pipeline for browsing occupational safety and hygiene literature. Tracks new academic publications across 46 target journals in occupational health, safety, ergonomics, and related fields — then delivers insights via a weekly newsletter ([Example](https://iiosh-research.github.io/OSH_Research/IIOSH_Research_Update_2026-06-25.html)) and a live [Dashboard](https://datastudio.google.com/reporting/b69400b8-a132-4605-a1f9-e37d0e2ca3ee).

## What It Does

### Weekly Newsletter
A Python pipeline that runs every Sunday morning on GitHub Actions (triggered externally — see [Scheduling](#scheduling-automated-trigger)):
1. Queries the [OpenAlex API](https://openalex.org/) for papers published in the last 7 days across Q1-ranked journals
2. Generates bilingual (English/Hebrew) summaries using the Google Gemini API, structured in three tiers:
   - **Article-level** — 2-sentence findings summary per paper
   - **Domain-level** — executive summary per research category
   - **Global-level** — master trend briefing with hyperlinks to individual articles
3. Publishes the full interactive newsletter to [GitHub Pages](https://iiosh-research.github.io/OSH_Research/)
4. Sends a teaser email to the distribution list with the digest and a link to the full update

### Looker Studio Dashboard
A weekly scraper that fetches article metadata (title, journal, DOI, publication date, subject domain, quality grade) from OpenAlex and pushes it to a Google Sheet. This Sheet feeds a Looker Studio dashboard that serves as a searchable historical archive for the research team.

## Research Domains Covered

| Domain | Journals Tracked |
|---|---|
| Occupational Health | 10 |
| Occupational Safety | 6 |
| Occupational Hygiene | 4 |
| Occupational Health & Stress | 2 |
| Applied Psychology & Organizational Behavior | 5 |
| General & Physical Ergonomics | 5 |
| Musculoskeletal Health & Biomechanics | 5 |
| Cognitive Ergonomics & HCI | 5 |
| Public & Environmental Health | 4 |

The Public & Environmental Health journals (Respirology, Medical Journal of Australia, Journal of Climate Change and Health, ANZ Journal of Public Health) are general rather than occupational. The dashboard archives all their articles; the newsletter keeps only work-related ones — a work term (e.g. *workers*, *occupational*, *silica*) in the title, or at least 3 in the abstract (`is_work_related()` in `newsletter.py`). Expect this domain in roughly one newsletter every 4–6 weeks.

### Adding a Journal
The newsletter and the dashboard keep **separate** journal lists on purpose, so each automation can differ (grades, filters). Adding a journal to both takes four places:
1. `newsletter/newsletter.py` → `JOURNAL_MAPPING` (`Subject`, `Grade`, and `"WorkFilter": True` for a non-occupational journal).
2. `dashboard/scraper.py` → `JOURNAL_MAPPING`.
3. The **Journal Metadata** tab of the *IIOSH Dashboard Data* Google Sheet: one row with the journal's exact OpenAlex display name and grade. **Without it, the journal is invisible in Looker Studio.** See [the dashboard doc](docs/Looker_Studio_Dashboard_Context.md).
4. The journal counts in this README and in `docs/`.

Check every ISSN at `https://api.openalex.org/sources/issn:<ISSN>` first, because a wrong ISSN fails silently and returns 0 articles. Grades come from SJR (scimagojr.com). Within each grade tier, the newsletter takes articles round-robin across a domain's journals, so adding a journal doesn't let it crowd out the others.

## Repository Structure

```
.github/workflows/
  weekly_update.yml        # GitHub Actions workflow (both pipelines); fired weekly by an external Apps Script trigger via workflow_dispatch
dashboard/
  scraper.py               # OpenAlex → Google Sheets pipeline for Looker Studio
  requirements.txt
newsletter/
  newsletter.py            # OpenAlex → Gemini → HTML + email pipeline
  requirements.txt
  copy_recipients.ps1      # Validates recipients.txt and copies it for the RECIPIENT_LIST secret
  recipients.txt           # (git-ignored, local only) the recipient list, one address per line
docs/
  Looker_Studio_Dashboard_Context.md
  IIOSH_Newsletter_Pipeline_Context.md
scripts_archive/           # Superseded scripts kept for reference
HANDOVER.md                # Passing the automation to a new maintainer, plus progress, maintenance and troubleshooting
CLAUDE.md                  # Context for whoever picks this up next (human or Claude): where things live, easy-to-break rules, unfinished work
```

## Tech Stack

- **Data Source:** [OpenAlex API](https://openalex.org/) (open scholarly metadata)
- **AI Engine:** Google Gemini API (`gemini-3.1-flash-lite`)
- **Dashboard Storage:** Google Sheets → Looker Studio
- **Newsletter Hosting:** GitHub Pages
- **Email Delivery:** Gmail SMTP
- **CI/CD:** GitHub Actions (execution)
- **Scheduler:** Google Apps Script time-driven trigger → GitHub `workflow_dispatch` API
- **Auth:** Workload Identity Federation (dashboard), API keys via GitHub Secrets (newsletter), fine-grained GitHub PAT (Apps Script trigger)

## Setup

### Prerequisites
- Python 3.10+
- Google Cloud project with Workload Identity Federation configured (for the dashboard pipeline)
- Gemini API key
- Gmail account with 2FA enabled and an App Password generated

### GitHub Secrets Required

| Secret | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key |
| `GMAIL_USER` | Sender Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not the account password) |
| `RECIPIENT_LIST` | Comma-separated recipient email addresses |

GitHub never shows a secret's value again, and updating it replaces the whole list. Keep the list in `newsletter/recipients.txt` (git-ignored, one address per line), then run `.\newsletter\copy_recipients.ps1` to check it and copy the comma-separated value for pasting into the secret.

### GitHub Pages
Enable Pages in repo Settings → Pages → Deploy from branch → `gh-pages` / `/ (root)`.

### Scheduling (Automated Trigger)

GitHub Actions' native `schedule:` (cron) trigger proved **unreliable** for this repo — it never fired a single scheduled run despite a valid, active workflow on the default branch. Weekly execution is therefore driven **externally**:

1. A **Google Apps Script** project (`IIOSH Weekly Trigger`, owned by `iiosh.news@gmail.com`) runs on a time-driven **Week timer** trigger — Sunday morning, Israel time.
2. The script reads a GitHub **fine-grained Personal Access Token** — stored in the project's Script Properties (never hardcoded), scoped to this repo only with `Actions: Read and write` — and sends a `POST` to GitHub's [`workflow_dispatch`](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event) endpoint for `weekly_update.yml`.
3. GitHub then runs the workflow exactly as if the **Run workflow** button had been clicked.

The workflow's `on:` block intentionally contains **only** `workflow_dispatch:` (no `schedule:`), so the Apps Script trigger is the single source of truth and there is no risk of a duplicate send if GitHub's own scheduler ever starts firing again.

The script's full code, and how to recreate it, are in [HANDOVER.md → Part 5](HANDOVER.md#part-5--weekly-trigger-apps-script). It has two functions:
- `triggerWeeklyNewsletter`: what the weekly trigger runs. **A real send to everyone**, so never run it by hand.
- `testDryRun`: sends a dry run to one address. Use this to test the trigger.

A refused request makes the script throw, and the trigger has *Notify me immediately* on, so a failure emails `iiosh.news@gmail.com`. The token was created on 2026-10-05 with **no expiry**, so it only needs replacing if it's revoked or exposed (see HANDOVER.md → *Maintenance*).

### Dry Run (Manual Testing)

Actions → **IIOSH Weekly Automation** → **Run workflow** → enter your address in **dry_run_email**. The dashboard updates as usual (a full rewrite, safe to repeat) and the newsletter is generated with real AI summaries, but the email — subject prefixed `[DRY RUN]` — goes **only to that address**, and the page is published under `/preview/` instead of replacing the public homepage, so the email's links work. The log says `DRY RUN: sending only to the dry-run address (a real run would go to N recipients)`; the address itself is masked in the (public) logs. Leaving the field empty is a real run, which is also what the Apps Script trigger does.

- **If the `dry_run_email` field doesn't appear** in the Run workflow form, hard-refresh the page (Ctrl+F5). The form can be stale after the workflow file changes. Don't click Run without seeing the field.
- **Stopping a mistaken real run:** the email is the last thing the newsletter step does, typically **10–15 minutes** after the run starts. Open the run and click **Cancel workflow** before then, and no one is emailed. Cancelling is safe for the dashboard and Pages too: the next run rewrites the Sheet, and Pages publishes only after the email. A real run is recognisable by its name, which lacks "(dry run)", and by the *Read dry-run address* step logging "Real run".

## License

This project is maintained by Tamir Shelomi
