# Context: IIOSH Journal Dashboard & Looker Studio Integration

## 📌 Project Overview
The Israel Institute for Occupational Safety and Hygiene (IIOSH) is running an automated data pipeline to track, summarize, and visualize academic literature across **46 core target journals**. 

The goal of this dashboard is to provide the IIOSH research team with a centralized repository of historical academic publications, filtered by subject domain and journal quality tiers.

---

## 📊 Looker Studio Architecture

### 1. Data Source Workflow
* **Backend:** A Python script (`dashboard/scraper.py`) queries the **OpenAlex API** globally for new publications using standard journal ISSNs.
* **Storage:** The raw metadata (Title, Journal Name, DOI Link, Publication Date, Subject Domain, and Journal Quality Grade) is pushed to the "IIOSH Dashboard Data" Google Sheet.
* **Visualization:** Looker Studio connects directly to this Google Sheet as its live data source.
* **⚠️ The "Journal Metadata" tab (maintained by hand):** A second tab in the same Sheet, with two columns, `Journal Name` and `Journal Grade`. It was filled once by `scripts_archive/Grades_addition.py` and is **not** updated by any automation. Looker joins the article rows to this tab by **exact** `Journal Name`, and the grade shown in the dashboard comes from here, not from the scraper's own `Grade` column. **A journal missing from this tab is hidden from the dashboard entirely**, even though its articles are in the Sheet. This was confirmed on 2026-10-04: the 7 journals added that day uploaded 4,353 rows, but the dashboard still showed 22,045 records, the old-journals-only total, until their rows were added here. Afterwards it showed 26,398.

### 2. Embedded Fields & Data Schema
The underlying data table fed into Looker Studio contains the following structured fields:
* `Title`: The academic title of the paper.
* `Journal Name`: The official display name of the publishing journal.
* `DOI / ID Link`: Clickable URL linking directly to the full text on the publisher's site.
* `Publication Date`: Year-Month-Day formatting to track historical trends.
* `Subject Domain`: One of our specific internal IIOSH research categories (e.g., *Occupational Safety, Occupational Health, Occupational Hygiene, Musculoskeletal Health, Applied Psych & Org Behavior, Cognitive Ergonomics & HCI, General & Physical Ergonomics, Public & Environmental Health*).
* `Journal Grade`: The journal's quartile (**Q1**, **Q1/Q2** or **Q2**), joined in from the **Journal Metadata** tab (see above). The scraper also writes a `Grade` column, but the original journals are all marked `Q1` there, and the dashboard doesn't display it.

### 3. Adding a Journal to the Dashboard
1. Add its ISSN to `JOURNAL_MAPPING` in `dashboard/scraper.py`. The newsletter keeps its own separate list in `newsletter/newsletter.py` on purpose, so update both when a journal should be in both.
2. Add a row to the **Journal Metadata** tab, with `Journal Name` exactly as OpenAlex displays it (`primary_location.source.display_name`, e.g. `NEW SOLUTIONS A Journal of Environmental and Occupational Health Policy`) and its grade. Without this row, the journal stays invisible.
3. Verify the ISSN resolves in OpenAlex (`https://api.openalex.org/sources/issn:<ISSN>`). A mistyped ISSN fails silently: the scraper logs `Fetched 0 articles` and carries on. Cognition, Technology & Work sat at 0 for months under the non-existent ISSN 1436-6556 before being corrected to 1435-5558.
4. After the next run, click **Refresh data** in Looker and check that the record count rose by about the number of articles the log reports for the new journal.

### 4. Data Notes
* The scraper pulls everything since 2024, **unfiltered**. That includes the 4 general Public & Environmental Health journals, which the newsletter filters for work relevance but the dashboard does not.
* Occupational Medicine's 2024 *Supplement_1* (~1,460 conference abstracts) is included **deliberately**. The maintainer chose to keep it. Spikes in the "Publish count by date" chart are such bulk issue or supplement dates.

---

## 🛠️ Dashboard Visual Layout & Controls

### Interactivity & Filters
To prevent information overload, the dashboard relies heavily on active user controls:
1. **Subject Domain Filter:** A dropdown menu allowing researchers to isolate specific fields (e.g., showing only *Musculoskeletal Health* articles).
2. **Journal Quality Selector:** A filter to isolate **Q1** (High-Impact Premium) journals vs. **Q2** journals.
3. **Date Range Picker:** Allows the team to filter historical publications by specific months, quarters, or custom date brackets.

### Data Visualization Components
* **The Main Table:** A clean table showcasing `Publication Date`, `Journal Name`, and `Title`. The `Title` or an adjacent column is configured as a clickable hyperlink using the DOI field, allowing researchers to open papers instantly.
* **Volume Metrics (KPI Scorecards):** Dynamic counters at the top showing the total number of articles tracked within the current filtered view.
* **Category Breakdown Charts:** Pie charts or horizontal bar charts showing the distribution of recent publications across the different subject domains.

---

## 📂 scripts_archive/
The `scripts_archive/` folder contains old, superseded scripts kept in the repo for reference. These are **not** part of any active pipeline. They include earlier versions of the scraper (daily and weekly variants using `gspread.oauth()`), a one-off journal metadata uploader (`Grades_addition.py`, which created the **Journal Metadata** tab; it uses interactive OAuth, so adding rows by hand is simpler), and an HTML CSS redesigner.

---

## 🔄 Relationship to the Weekly Newsletter Script
While the **Looker Studio Dashboard** acts as the permanent, searchable *historical archive* for the institute, it runs side-by-side with an automated **Weekly Newsletter Script**. 
* The script aggressively pulls data from the last 7 days, utilizes **Gemini 3.1-flash-lite** to extract results-oriented 2-sentence English summaries from abstracts, and exports an HTML layout.
* The Looker Studio dashboard acts as the deep-dive backup when researchers want to look back further than the 7-day email window.


🚀 Status Report: IIOSH Dashboard Automation

✅ Phase 1: Script & Data Prep (Completed)
[x] Looker Studio UI Fix: Identified the fix for the "Grade" and "Journal Name" filter dependency.

[x] Python Script Update (scraper.py): Added the required Grade field mapping to match the Looker Studio schema.

[x] Authentication Pivot: Switched the script from human-in-the-loop OAuth (gspread.oauth()) to Application Default Credentials (google.auth.default()) to run headlessly.

✅ Phase 2: Security & Google Cloud Setup (Completed)
[x] Workload Identity Federation (WIF): Created a WIF pool and provider (github-provider) to bypass the organization's block on static JSON keys.

[x] OIDC Mapping: Mapped GitHub tokens to Google Cloud (google.subject -> assertion.sub and attribute.repository -> assertion.repository).

[x] Security Constraints: Locked down the WIF provider so only your specific GitHub repository can authenticate.

[x] Service Account Impersonation: Configured the federated identity to impersonate your specific Google Service Account.

[x] Sheet Permissions: Granted the Service Account email explicit Editor access to the "IIOSH Dashboard Data" Google Sheet.

✅ Phase 3: GitHub Actions Setup (Completed)
[x] Workflow File (weekly_update.yml): Drafted the YAML file to run on demand via workflow_dispatch (and, originally, a weekly cron schedule — since removed; see Phase 5).

[x] OIDC Permissions: Added the critical id-token: write and contents: read permissions to the YAML job.

[x] Auth Step Added: Integrated the google-github-actions/auth@v2 step into the pipeline using the WIF provider string and Service Account email.

✅ Phase 4: Deployment (Completed)
[x] Commit Files: Pushed dashboard/scraper.py, dashboard/requirements.txt, and .github/workflows/weekly_update.yml to the GitHub repository.

[x] Test the Action: Runs weekly. A manual end-to-end dry run was verified on 2026-10-04 (see the README's *Dry Run* section).

[x] Verify: Dashboard confirmed updating on 2026-10-04, after the Journal Metadata rows for the new journals were added.

✅ Phase 5: Scheduling Pivot — External Trigger (Completed)
[x] Root Cause: GitHub Actions' native `schedule:` (cron) trigger never fired for this repo — confirmed by a diagnostic test showing 0 schedule-event runs across multiple clean cron ticks, despite a valid, active workflow on the default branch. Manual `workflow_dispatch` runs always worked, so the pipeline code was never the problem.

[x] External Scheduler: Built a Google Apps Script project (`IIOSH Weekly Trigger`) with a time-driven Week-timer trigger (Sunday morning, Israel time) that POSTs to GitHub's `workflow_dispatch` API using a fine-grained PAT stored in Script Properties. (Cloud Scheduler was ruled out — it requires billing enabled on the org's GCP project.)

[x] Verification: Confirmed the full chain end-to-end (manual run + an unattended one-time trigger both fired the workflow successfully via the API).

[x] Cleanup: Removed the dead `schedule:` line from `weekly_update.yml`, leaving only `workflow_dispatch:`, so Apps Script is the single source of truth and there is no duplicate-send risk.

[!] Maintenance Watch: The fine-grained PAT expires (~1 year max). When it does, the trigger fails silently and the newsletter/dashboard stop updating. Enable the Apps Script trigger's failure-notification email and regenerate the token before expiry. See the README's *Scheduling* section for full details.