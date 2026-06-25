# Context: IIOSH Automated Weekly Newsletter Pipeline

## 📌 Project Overview
The Israel Institute for Occupational Safety and Hygiene (IIOSH) utilizes an automated Python pipeline (`newsletter/newsletter.py`) to generate a weekly, bilingual (English & Hebrew) research newsletter. The script queries the **OpenAlex API** for fresh academic papers across 39 target journals, processes the abstracts using the **Google Gemini API**, and outputs a highly polished, responsive HTML file designed to be copy-pasted directly into Microsoft Outlook.

---

## ⚙️ Architecture & Tech Stack
* **Data Source:** OpenAlex API (Filtered by ISSN, Published within the last 7 days, Sorted by `publication_date:desc`).
* **AI Engine:** Google Gemini API (`gemini-3.1-flash-lite`).
    * *Note:* The `flash-lite` model is currently in use. If RTL Hebrew token load causes frequent `429 Resource Exhausted` errors, consider upgrading to the heavier `flash` variant.
* **Language:** Python 3.x
* **Output:** Standalone HTML file with inline CSS.

---

## 🛡️ Core Pipeline Logic & Safeguards

To prevent API throttling, token exhaustion, and email fatigue, the pipeline operates under strict editorial and engineering rules:
1.  **The Q1 Gatekeeper:** The script strictly filters for high-impact journals designated as `"Grade": "Q1"` in the internal mapping dictionary.
2.  **Category Capping:** To prevent overwhelming the reader, the script caps processing at `MAX_ARTICLES_PER_SUBJECT = 5`. Once 5 valid articles with abstracts are processed for a domain (e.g., *Occupational Safety*), it skips remaining results for that category and moves on.
3.  **Self-Healing Rate Limits:** * The script includes a forced `time.sleep(12)` between individual Gemini calls to respect the free-tier Requests-Per-Minute (RPM) limits.
    * It features an automatic 3-attempt retry loop that catches `503` (Server Busy) and `429` (Quota/Token Exceeded) errors, pausing for 15 seconds before retrying.

---

## 🧠 The 3-Tier AI Generation Hierarchy

The pipeline generates content in three distinct layers to create a "Narrative News Briefing":

1.  **Article Level (Base):** Extracts a crisp, results-oriented 2-sentence summary of the abstract in English, followed by a professional corporate Hebrew translation. 
2.  **Domain Level (Category):** Once all articles for a category are processed, the AI synthesizes them into a single bilingual "Executive Summary" paragraph that identifies trends within that specific domain.
3.  **Global Level (Master Briefing):** Finally, the AI reads *all* extracted data and generates a 1-2 paragraph global briefing summarizing the entire week. 
    * *Crucial Feature:* This global briefing injects HTML anchor links (e.g., `<a href="#art-1">`) directly into the narrative text, allowing users to click a finding and jump straight to the relevant article profile below.

---

## 🎨 UI/UX & HTML Design Specifications

The output is a single `IIOSH_Research_Update_YYYY-MM-DD.html` file built with strict inline CSS to bypass corporate email firewall strippers. 

**Key Visual Elements:**
* **Global Layout:** Crisp off-white container, Apple-system fonts, soft drop shadows (`box-shadow`), and a max-width of `850px` for readability.
* **Master Meta Briefing:** A top-level gray box containing the interactive global trends summary.
* **Domain Headers:** Bold slate-blue titles (e.g., *Occupational Health*).
* **Executive Summary Cards:** Floating premium cards (`#f8fafc` background) with a sky-blue top border (`#0284c7`) to visually separate them from individual articles.
* **Section Dividers:** A specific, indented sub-header reading **"ARTICLES / מאמרים מדעיים"** positioned directly below the executive summary.
* **Article Profiles:** Light gray background cards (`#fafafa`) with a heavy blue left-border accent. Contains the English text (LTR) and the Hebrew text (RTL `dir="rtl"` aligned right).

---

## 📄 Current State of the Codebase
*(Note for the AI: The script is currently fully functional, stable, and executing the 3-tier generation perfectly. Any future modifications must preserve the existing retry logic, the `gemini-3.1-flash-lite` model mapping, the `MAX_ARTICLES_PER_SUBJECT` limits, and the exact inline CSS structures outlined above.)*