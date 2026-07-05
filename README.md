# Research Automation

Automated research monitoring pipeline for browsing occupational safety and hygiene literature. Tracks new academic publications across 39 target journals in occupational health, safety, ergonomics, and related fields — then delivers insights via a weekly newsletter ([Example](https://tamirs-osh.github.io/OSH_Research/IIOSH_Research_Update_2026-06-25.html)) and a live [Dashboard](https://datastudio.google.com/reporting/f82c0682-5cf7-4201-a9fb-907573f9fee2).

## What It Does

### Weekly Newsletter
A Python pipeline that runs every Sunday morning on GitHub Actions (triggered externally — see [Scheduling](#scheduling-automated-trigger)):
1. Queries the [OpenAlex API](https://openalex.org/) for papers published in the last 7 days across Q1-ranked journals
2. Generates bilingual (English/Hebrew) summaries using the Google Gemini API, structured in three tiers:
   - **Article-level** — 2-sentence findings summary per paper
   - **Domain-level** — executive summary per research category
   - **Global-level** — master trend briefing with hyperlinks to individual articles
3. Publishes the full interactive newsletter to [GitHub Pages](https://tamirs-osh.github.io/OSH_Research/)
4. Sends a teaser email to the distribution list with the digest and a link to the full update

### Looker Studio Dashboard
A weekly scraper that fetches article metadata (title, journal, DOI, publication date, subject domain, quality grade) from OpenAlex and pushes it to a Google Sheet. This Sheet feeds a Looker Studio dashboard that serves as a searchable historical archive for the research team.

## Research Domains Covered

| Domain | Journals Tracked |
|---|---|
| Occupational Health | 7 |
| Occupational Safety | 6 |
| Occupational Hygiene | 4 |
| Occupational Health & Stress | 2 |
| Applied Psychology & Organizational Behavior | 5 |
| General & Physical Ergonomics | 5 |
| Musculoskeletal Health & Biomechanics | 5 |
| Cognitive Ergonomics & HCI | 5 |

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
docs/
  Looker_Studio_Dashboard_Context.md
  IIOSH_Newsletter_Pipeline_Context.md
scripts_archive/           # Superseded scripts kept for reference
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

### GitHub Pages
Enable Pages in repo Settings → Pages → Deploy from branch → `gh-pages` / `/ (root)`.

### Scheduling (Automated Trigger)

GitHub Actions' native `schedule:` (cron) trigger proved **unreliable** for this repo — it never fired a single scheduled run despite a valid, active workflow on the default branch. Weekly execution is therefore driven **externally**:

1. A **Google Apps Script** project (`IIOSH Weekly Trigger`, owned by the maintainer's Google account) runs on a time-driven **Week timer** trigger — Sunday morning, Israel time.
2. The script reads a GitHub **fine-grained Personal Access Token** — stored in the project's Script Properties (never hardcoded), scoped to this repo only with `Actions: Read and write` — and sends a `POST` to GitHub's [`workflow_dispatch`](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event) endpoint for `weekly_update.yml`.
3. GitHub then runs the workflow exactly as if the **Run workflow** button had been clicked.

The workflow's `on:` block intentionally contains **only** `workflow_dispatch:` (no `schedule:`), so the Apps Script trigger is the single source of truth and there is no risk of a duplicate send if GitHub's own scheduler ever starts firing again.

The core of the Apps Script project:

```javascript
function triggerWeeklyNewsletter() {
  var token = PropertiesService.getScriptProperties().getProperty('GITHUB_PAT');
  var url = 'https://api.github.com/repos/TamirS-OSH/OSH_Research/actions/workflows/weekly_update.yml/dispatches';
  var options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28'
    },
    payload: JSON.stringify({ ref: 'main' }),
    muteHttpExceptions: true
  };
  var response = UrlFetchApp.fetch(url, options);
  Logger.log(response.getResponseCode()); // 204 = success
}
```

> **⚠️ Maintenance — the token expires.** Fine-grained GitHub PATs last up to ~1 year. When this one expires the Apps Script trigger will start failing and the newsletter will **silently stop going out**. To stay ahead of it:
> - Enable the trigger's **failure-notification email** (Apps Script → Triggers → the trigger → *Notify me immediately*) so a lapse is caught early.
> - Before expiry, generate a fresh PAT (same scope), paste it into the `setGithubToken` helper, run that function once, then blank the literal back out of the source.

## License

This project is maintained by Tamir Shelomi
