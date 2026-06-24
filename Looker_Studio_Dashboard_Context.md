# Context: IIOSH Journal Dashboard & Looker Studio Integration

## 📌 Project Overview
The Israel Institute for Occupational Safety and Hygiene (IIOSH) is running an automated data pipeline to track, summarize, and visualize academic literature across **39 core target journals**. 

The goal of this dashboard is to provide the IIOSH research team with a centralized repository of historical academic publications, filtered by subject domain and journal quality tiers.

---

## 📊 Looker Studio Architecture

### 1. Data Source Workflow
* **Backend:** A Python script queries the **OpenAlex API** globally for new publications using standard journal ISSNs.
* **Storage:** The raw metadata (Title, Journal Name, DOI Link, Publication Date, Subject Domain, and Journal Quality Grade) is appended to a central tracking storage layer (e.g., CSV / Google Sheets).
* **Visualization:** Looker Studio connects directly to this storage layer as its live data source.

### 2. Embedded Fields & Data Schema
The underlying data table fed into Looker Studio contains the following structured fields:
* `Title`: The academic title of the paper.
* `Journal Name`: The official display name of the publishing journal.
* `DOI / ID Link`: Clickable URL linking directly to the full text on the publisher's site.
* `Publication Date`: Year-Month-Day formatting to track historical trends.
* `Subject Domain`: One of our specific internal IIOSH research categories (e.g., *Occupational Safety, Occupational Health, Occupational Hygiene, Musculoskeletal Health, Applied Psych & Org Behavior, Cognitive Ergonomics & HCI, General & Physical Ergonomics*).
* `Grade`: The journal ranking metrics (**Q1** or **Q2**) mapped internally via specialized journal dictionaries.

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

## 🔄 Relationship to the Weekly Newsletter Script
While the **Looker Studio Dashboard** acts as the permanent, searchable *historical archive* for the institute, it runs side-by-side with an automated **Weekly Newsletter Script**. 
* The script aggressively pulls data from the last 7 days, utilizes **Gemini 2.5-flash-lite** to extract results-oriented 2-sentence English summaries from abstracts, and exports an HTML layout.
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
[x] Workflow File (weekly_update.yml): Drafted the YAML file to run automatically every Monday at midnight UTC and manually on demand.

[x] OIDC Permissions: Added the critical id-token: write and contents: read permissions to the YAML job.

[x] Auth Step Added: Integrated the google-github-actions/auth@v2 step into the pipeline using the WIF provider string and Service Account email.

⏳ Phase 4: Final Action Items (Pending)
We are at the finish line. To complete the automation, you need to execute these final steps in your repository:

[ ] Commit Files: Push the following three files to your GitHub repository:

scraper.py (The updated Python script)

requirements.txt (Containing: requests, pandas, gspread, google-auth)

.github/workflows/weekly_update.yml (The GitHub Actions configuration)

[ ] Test the Action: Go to the Actions tab in your GitHub repository, select the "Weekly Looker Studio Data Pull" workflow, and click Run workflow to test it manually.

[ ] Verify: Check the Looker Studio dashboard to ensure the data updated correctly without errors.