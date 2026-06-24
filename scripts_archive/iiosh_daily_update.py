import requests
import pandas as pd
import gspread
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
GOOGLE_SHEET_NAME = "IIOSH Dashboard Data"

# Calculate the date 1 day ago to catch recent publications and account for indexing delays
RECENT_DATE = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

# The complete list of IIOSH target journals
JOURNAL_MAPPING = {
    # 1. Occupational Health
    "0355-3140": "Occupational Health", "1351-0711": "Occupational Health", "1076-2752": "Occupational Health",
    "1097-0274": "Occupational Health", "1432-1246": "Occupational Health", "1348-9585": "Occupational Health", "2165-0969": "Occupational Health",
    # 2. Occupational Safety
    "0925-7535": "Occupational Safety", "0022-4375": "Occupational Safety", "0001-4575": "Occupational Safety",
    "2093-7997": "Occupational Safety", "0950-4230": "Occupational Safety", "1080-3548": "Occupational Safety",
    # 3. Occupational Hygiene
    "2398-7316": "Occupational Hygiene", "1545-9632": "Occupational Hygiene", "1438-4639": "Occupational Hygiene", "1559-064X": "Occupational Hygiene",
    # 4. Dedicated Occupational Health & Stress Journals
    "1939-1307": "Occ. Health & Stress", "1464-5335": "Occ. Health & Stress",
    # 5. Top-Tier Applied Psychology & Organizational Behavior
    "0021-9010": "Applied Psych & Org Behavior", "1099-1379": "Applied Psych & Org Behavior", "0001-8791": "Applied Psych & Org Behavior",
    "0149-2063": "Applied Psych & Org Behavior", "0018-7267": "Applied Psych & Org Behavior",
    # 6. General & Physical Ergonomics
    "0003-6870": "General & Physical Ergonomics", "0018-7208": "General & Physical Ergonomics", "0014-0139": "General & Physical Ergonomics",
    "0169-8141": "General & Physical Ergonomics", "1463-922X": "General & Physical Ergonomics",
    # 7. Musculoskeletal Health & Biomechanics
    "1053-0487": "Musculoskeletal Health", "0021-9290": "Musculoskeletal Health", "0268-0033": "Musculoskeletal Health",
    "1471-2474": "Musculoskeletal Health", "0966-6362": "Musculoskeletal Health",
    # 8. Cognitive Ergonomics & Human-System Interaction
    "1071-5819": "Cognitive Ergonomics & HCI", "2168-2291": "Cognitive Ergonomics & HCI", "1044-7318": "Cognitive Ergonomics & HCI",
    "1436-6556": "Cognitive Ergonomics & HCI", "1520-6564": "Cognitive Ergonomics & HCI"
}

def fetch_daily_articles(issn, subject):
    """Fetches articles published from a specific recent date to present."""
    print(f"Querying OpenAlex for {subject} (ISSN: {issn}) since {RECENT_DATE}...")
    
    parsed_articles = []
    cursor = "*" 
    
    while cursor:
        # Changed the filter to from_publication_date
        url = f"https://api.openalex.org/works?filter=primary_location.source.issn:{issn},from_publication_date:{RECENT_DATE}&per_page=200&cursor={cursor}"
        
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
                "Citations": work.get('cited_by_count', 0),
                "Article Link": work.get('doi', work.get('id'))
            })
            
        cursor = data.get('meta', {}).get('next_cursor', None)
        time.sleep(1)
        
    if len(parsed_articles) > 0:
        print(f"  -> Found {len(parsed_articles)} new article(s).")
    return parsed_articles

def append_to_google_sheet(dataframe):
    """Appends the Pandas DataFrame to the bottom of the Google Sheet."""
    print(f"\nConnecting to Google Sheets to append {len(dataframe)} new rows...")
    
    client = gspread.oauth()
    sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    
    # We DO NOT clear the sheet. We append the values directly to the bottom.
    sheet.append_rows(dataframe.values.tolist())
    print(f"Successfully appended {len(dataframe)} rows to '{GOOGLE_SHEET_NAME}'!")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    all_data = []
    
    print(f"Starting DAILY data pull for {len(JOURNAL_MAPPING)} journals looking back to {RECENT_DATE}...")
    
    for issn, subject in JOURNAL_MAPPING.items():
        articles = fetch_daily_articles(issn, subject)
        all_data.extend(articles)
        
    df = pd.DataFrame(all_data)
    
    if not df.empty:
        # Fill missing data to prevent JSON crash
        df.fillna("", inplace=True)
        
        # Sort the new data before appending
        df = df.sort_values(by=['Journal Name', 'Publication Date'], ascending=[True, False])
        
        append_to_google_sheet(df)
    else:
        print("Pipeline execution yielded no new records. No updates made to the sheet.")