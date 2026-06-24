import requests
import pandas as pd
import gspread
import time
import datetime

# --- 1. CONFIGURATION ---
GOOGLE_SHEET_NAME = "IIOSH Dashboard Data"

# Calculate the current year dynamically for the API filter
CURRENT_YEAR = datetime.datetime.now().year
YEAR_FILTER = f"2024-{CURRENT_YEAR}"

JOURNAL_MAPPING = {
    # 1. Occupational Health
    "0355-3140": "Occupational Health",
    "1351-0711": "Occupational Health",
    "1076-2752": "Occupational Health",
    "1097-0274": "Occupational Health",
    "1432-1246": "Occupational Health",
    "1348-9585": "Occupational Health",
    "2165-0969": "Occupational Health",

    # 2. Occupational Safety
    "0925-7535": "Occupational Safety",
    "0022-4375": "Occupational Safety",
    "0001-4575": "Occupational Safety",
    "2093-7997": "Occupational Safety",
    "0950-4230": "Occupational Safety",
    "1080-3548": "Occupational Safety",

    # 3. Occupational Hygiene
    "2398-7316": "Occupational Hygiene",
    "1545-9632": "Occupational Hygiene",
    "1438-4639": "Occupational Hygiene",
    "1559-064X": "Occupational Hygiene",

    # 4. Dedicated Occupational Health & Stress Journals
    "1939-1307": "Occ. Health & Stress",
    "1464-5335": "Occ. Health & Stress",

    # 5. Top-Tier Applied Psychology & Organizational Behavior
    "0021-9010": "Applied Psych & Org Behavior",
    "1099-1379": "Applied Psych & Org Behavior",
    "0001-8791": "Applied Psych & Org Behavior",
    "0149-2063": "Applied Psych & Org Behavior",
    "0018-7267": "Applied Psych & Org Behavior",

    # 6. General & Physical Ergonomics
    "0003-6870": "General & Physical Ergonomics",
    "0018-7208": "General & Physical Ergonomics",
    "0014-0139": "General & Physical Ergonomics",
    "0169-8141": "General & Physical Ergonomics",
    "1463-922X": "General & Physical Ergonomics",

    # 7. Musculoskeletal Health & Biomechanics
    "1053-0487": "Musculoskeletal Health",
    "0021-9290": "Musculoskeletal Health",
    "0268-0033": "Musculoskeletal Health",
    "1471-2474": "Musculoskeletal Health",
    "0966-6362": "Musculoskeletal Health",

    # 8. Cognitive Ergonomics & Human-System Interaction
    "1071-5819": "Cognitive Ergonomics & HCI",
    "2168-2291": "Cognitive Ergonomics & HCI",
    "1044-7318": "Cognitive Ergonomics & HCI",
    "1436-6556": "Cognitive Ergonomics & HCI",
    "1520-6564": "Cognitive Ergonomics & HCI"
}

def fetch_all_recent_articles(issn, subject):
    """Fetches ALL articles from 2024 to present for a specific ISSN using pagination."""
    print(f"Querying OpenAlex for {subject} (ISSN: {issn})...")
    
    parsed_articles = []
    cursor = "*"  # OpenAlex uses '*' to denote the first page of results
    
    # Loop through pages until there is no next_cursor
    while cursor:
        url = f"https://api.openalex.org/works?filter=primary_location.source.issn:{issn},publication_year:{YEAR_FILTER}&per_page=200&cursor={cursor}"
        
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"  -> Error fetching data for ISSN {issn}")
            break
            
        data = response.json()
        results = data.get('results', [])
        
        # Break the loop if we hit an empty page
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
            
        # Get the cursor for the next page. If it's None, the loop will break.
        cursor = data.get('meta', {}).get('next_cursor', None)
        
        # Be polite to the API between page requests
        time.sleep(1)
        
    print(f"  -> Fetched {len(parsed_articles)} articles.")
    return parsed_articles

def update_google_sheet(dataframe):
    """Pushes the Pandas DataFrame to Google Sheets using User OAuth."""
    print(f"\nConnecting to Google Sheets to upload {len(dataframe)} rows...")
    
    client = gspread.oauth()
    sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    
    sheet.clear()
    
    # Write new data (headers + rows)
    sheet.update([dataframe.columns.values.tolist()] + dataframe.values.tolist())
    print(f"Successfully uploaded {len(dataframe)} rows to '{GOOGLE_SHEET_NAME}'!")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    all_data = []
    
    print(f"Starting data pull for {len(JOURNAL_MAPPING)} journals from {YEAR_FILTER}...")
    
    for issn, subject in JOURNAL_MAPPING.items():
        articles = fetch_all_recent_articles(issn, subject)
        all_data.extend(articles)
        
    df = pd.DataFrame(all_data)
    
    if not df.empty:
        # THE FIX: Replace all NaN (missing) values with an empty string
        df.fillna("", inplace=True)
        
        # Sort the entire dataframe by Journal Name, then Date (newest first)
        df = df.sort_values(by=['Journal Name', 'Publication Date'], ascending=[True, False])
        
        update_google_sheet(df)
    else:
        print("Pipeline execution yielded no records.")