# IIOSH Research Automation

Automated research monitoring pipeline for the **Israel Institute for Occupational Safety and Hygiene (IIOSH)**. Tracks new academic publications across 39 target journals in occupational health, safety, ergonomics, and related fields — then delivers insights via a weekly newsletter ([Example](https://tamirs-osh.github.io/OSH_Research/IIOSH_Research_Update_2026-06-25.html)) and a live [Dashboard](https://datastudio.google.com/reporting/f82c0682-5cf7-4201-a9fb-907573f9fee2).

## What It Does

### Weekly Newsletter
A Python pipeline that runs every Sunday morning via GitHub Actions:
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
  weekly_update.yml        # GitHub Actions: runs both pipelines on a weekly schedule
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
- **CI/CD:** GitHub Actions
- **Auth:** Workload Identity Federation (dashboard), API keys via GitHub Secrets (newsletter)

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

## License

This project is maintained by the Israel Institute for Occupational Safety and Hygiene.
