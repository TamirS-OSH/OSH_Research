import requests
import pandas as pd
import gspread
import google.auth
import time
import datetime

# --- 1. CONFIGURATION ---
GOOGLE_SHEET_NAME = "IIOSH Dashboard Data"

# Calculate the current year dynamically for the API filter
CURRENT_YEAR = datetime.datetime.now().year
YEAR_FILTER = f"2024-{CURRENT_YEAR}"

JOURNAL_MAPPING = {
    # 1. Occupational Health
    "0355-3140": {"subject": "Occupational Health", "grade": "Q1"},
    "1351-0711": {"subject": "Occupational Health", "grade": "Q1"},
    "1076-2752": {"subject": "Occupational Health", "grade": "Q1"},
    "1097-0274": {"subject": "Occupational Health", "grade": "Q1"},
    "1432-1246": {"subject": "Occupational Health", "grade": "Q1"},
    "1348-9585": {"subject": "Occupational Health", "grade": "Q1"},
    "2165-0969": {"subject": "Occupational Health", "grade": "Q1"},

    # 2. Occupational Safety
    "0925-7535": {"subject": "Occupational Safety", "grade": "Q1"},
    "0022-4375": {"subject": "Occupational Safety", "grade": "Q1"},
    "0001-4575": {"subject": "Occupational Safety", "grade": "Q1"},
    "2093-7997": {"subject": "Occupational Safety", "grade": "Q1"},
    "0950-4230": {"subject": "Occupational Safety", "grade": "Q1"},
    "1080-3548": {"subject": "Occupational Safety", "grade": "Q1"},

    # 3. Occupational Hygiene
    "2398-7316": {"subject": "Occupational Hygiene", "grade": "Q1"},
    "1545-9632": {"subject": "Occupational Hygiene", "grade": "Q1"},
    "1438-4639": {"subject": "Occupational Hygiene", "grade": "Q1"},
    "1559-064X": {"subject": "Occupational Hygiene", "grade": "Q1"},

    # 4. Dedicated Occupational Health & Stress Journals
    "1939-1307": {"subject": "Occ. Health & Stress", "grade": "Q1"},
    "1464-5335": {"subject": "Occ. Health & Stress", "grade": "Q1"},

    # 5. Top-Tier Applied Psychology & Organizational Behavior
    "0021-9010": {"subject": "Applied Psych & Org Behavior", "grade": "Q1"},
    "1099-1379": {"subject": "Applied Psych & Org Behavior", "grade": "Q1"},
    "0001-8791": {"subject": "Applied Psych & Org Behavior", "grade": "Q1"},
    "0149-2063": {"subject": "Applied Psych & Org Behavior", "grade": "Q1"},
    "0018-7267": {"subject": "Applied Psych & Org Behavior", "grade": "Q1"},

    # 6. General & Physical Ergonomics
    "0003-6870": {"subject": "General & Physical Ergonomics", "grade": "Q1"},
    "0018-7208": {"subject": "General & Physical Ergonomics", "grade": "Q1"},
    "0014-0139": {"subject": "General & Physical Ergonomics", "grade": "Q1"},
    "0169-8141": {"subject": "General & Physical Ergonomics", "grade": "Q1"},
    "1463-922X": {"subject": "General & Physical Ergonomics", "grade": "Q1"},

    # 7. Musculoskeletal Health & Biomechanics
    "1053-0487": {"subject": "Musculoskeletal Health", "grade": "Q1"},
    "0021-9290": {"subject": "Musculoskeletal Health", "grade": "Q1"},
    "0268-0033": {"subject": "Musculoskeletal Health", "grade": "Q1"},
    "1471-2474": {"subject": "Musculoskeletal Health", "grade": "Q1"},
    "0966-6362": {"subject": "Musculoskeletal Health", "grade": "Q1"},

    # 8. Cognitive Ergonomics & Human-System Interaction
    "1071-5819": {"subject": "Cognitive Ergonomics & HCI", "grade": "Q1"},
    "2168-2291": {"subject": "Cognitive Ergonomics & HCI", "grade": "Q1"},
    "1044-7318": {"subject": "Cognitive Ergonomics & HCI", "grade": "Q1"},
    "1436-6556": {"subject": "Cognitive Ergonomics & HCI", "grade": "Q1"},
    "1520-6564": {"subject": "Cognitive Ergonomics & HCI", "grade": "Q1"}
}

def fetch_all_recent_articles(issn, config):
    """Fetches ALL articles from 2024 to present for a specific ISSN using pagination."""
    subject = config["subject"]
    grade = config["grade"]
    print(f"Querying OpenAlex for {subject} (ISSN: {issn})...")
    
    parsed_articles = []
    cursor = "*" 
    
    while cursor:
        url = f"https://api.openalex.org/works?filter=primary_location.source.issn:{issn},publication_year:{YEAR_FILTER}&per_page=200&cursor={cursor}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"  -> Error fetching data for ISSN {issn}")
            break
            
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            break
            
        for work in results:
            parsed_articles.append({
                "Subject Domain": subject,
                "Journal Name": work.get('primary_location', {}).get('source', {}).get('display_name', 'Unknown Journal'),
                "Article Title": work.get('title', 'Untitled'),
                "Publication Date": work.get('publication_date', ''),
                "Grade": grade,
                "Citations": work.get('cited_by_count', 0),
                "Article Link": work.get('doi', work.get('id'))
            })
            
        cursor = data.get('meta', {}).get('next_cursor', None)
        time.sleep(1)
        
    print(f"  -> Fetched {len(parsed_articles)} articles.")
    return parsed_articles

def update_google_sheet(dataframe):
    """Pushes the Pandas DataFrame to Google Sheets using Workload Identity (ADC)."""
    print(f"\nConnecting to Google Sheets to upload {len(dataframe)} rows...")
    
    credentials, _ = google.auth.default(scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    
    client = gspread.authorize(credentials)
    sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    
    sheet.clear()
    sheet.update([dataframe.columns.values.tolist()] + dataframe.values.tolist())
    print(f"Successfully uploaded {len(dataframe)} rows to '{GOOGLE_SHEET_NAME}'!")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    all_data = []
    
    print(f"Starting data pull for {len(JOURNAL_MAPPING)} journals from {YEAR_FILTER}...")
    
    for issn, config in JOURNAL_MAPPING.items():
        articles = fetch_all_recent_articles(issn, config)
        all_data.extend(articles)
        
    df = pd.DataFrame(all_data)
    
    if not df.empty:
        df.fillna("", inplace=True)
        df = df.sort_values(by=['Journal Name', 'Publication Date'], ascending=[True, False])
        update_google_sheet(df)
    else:
        print("Pipeline execution yielded no records.")