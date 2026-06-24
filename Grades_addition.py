import requests
import pandas as pd
import gspread
import time

GOOGLE_SHEET_NAME = "IIOSH Dashboard Data"

# The complete list of IIOSH target journals with Subject and Grade mapping
JOURNAL_MAPPING = {
    "0355-3140": {"Subject": "Occupational Health", "Grade": "Q1"}, 
    "1351-0711": {"Subject": "Occupational Health", "Grade": "Q1"}, 
    "1076-2752": {"Subject": "Occupational Health", "Grade": "Q2"}, 
    "1097-0274": {"Subject": "Occupational Health", "Grade": "Q2"}, 
    "1432-1246": {"Subject": "Occupational Health", "Grade": "Q2"}, 
    "1348-9585": {"Subject": "Occupational Health", "Grade": "Q2"}, 
    "2165-0969": {"Subject": "Occupational Health", "Grade": "Q2"}, 
    "0925-7535": {"Subject": "Occupational Safety", "Grade": "Q1"}, 
    "0022-4375": {"Subject": "Occupational Safety", "Grade": "Q1"}, 
    "0001-4575": {"Subject": "Occupational Safety", "Grade": "Q1"}, 
    "2093-7997": {"Subject": "Occupational Safety", "Grade": "Q1"}, 
    "0950-4230": {"Subject": "Occupational Safety", "Grade": "Q1"}, 
    "1080-3548": {"Subject": "Occupational Safety", "Grade": "Q2"}, 
    "2398-7316": {"Subject": "Occupational Hygiene", "Grade": "Q1"}, 
    "1545-9632": {"Subject": "Occupational Hygiene", "Grade": "Q1"}, 
    "1438-4639": {"Subject": "Occupational Hygiene", "Grade": "Q1"}, 
    "1559-064X": {"Subject": "Occupational Hygiene", "Grade": "Q1"}, 
    "1939-1307": {"Subject": "Occ. Health & Stress", "Grade": "Q1"}, 
    "1464-5335": {"Subject": "Occ. Health & Stress", "Grade": "Q1"}, 
    "0021-9010": {"Subject": "Applied Psych & Org Behavior", "Grade": "Q1"}, 
    "1099-1379": {"Subject": "Applied Psych & Org Behavior", "Grade": "Q1"}, 
    "0001-8791": {"Subject": "Applied Psych & Org Behavior", "Grade": "Q1"}, 
    "0149-2063": {"Subject": "Applied Psych & Org Behavior", "Grade": "Q1"}, 
    "0018-7267": {"Subject": "Applied Psych & Org Behavior", "Grade": "Q1"}, 
    "0003-6870": {"Subject": "General & Physical Ergonomics", "Grade": "Q1"}, 
    "0018-7208": {"Subject": "General & Physical Ergonomics", "Grade": "Q1"}, 
    "0014-0139": {"Subject": "General & Physical Ergonomics", "Grade": "Q1/Q2"}, 
    "0169-8141": {"Subject": "General & Physical Ergonomics", "Grade": "Q2"}, 
    "1463-922X": {"Subject": "General & Physical Ergonomics", "Grade": "Q2"}, 
    "1053-0487": {"Subject": "Musculoskeletal Health", "Grade": "Q1"}, 
    "0021-9290": {"Subject": "Musculoskeletal Health", "Grade": "Q1/Q2"}, 
    "0268-0033": {"Subject": "Musculoskeletal Health", "Grade": "Q2"}, 
    "1471-2474": {"Subject": "Musculoskeletal Health", "Grade": "Q2"}, 
    "0966-6362": {"Subject": "Musculoskeletal Health", "Grade": "Q2"}, 
    "1071-5819": {"Subject": "Cognitive Ergonomics & HCI", "Grade": "Q1"}, 
    "2168-2291": {"Subject": "Cognitive Ergonomics & HCI", "Grade": "Q1"}, 
    "1044-7318": {"Subject": "Cognitive Ergonomics & HCI", "Grade": "Q1"}, 
    "1436-6556": {"Subject": "Cognitive Ergonomics & HCI", "Grade": "Q1/Q2"}, 
    "1520-6564": {"Subject": "Cognitive Ergonomics & HCI", "Grade": "Q2"}
}

def get_metadata():
    metadata_list = []
    print("Fetching exact Journal Names from OpenAlex...")
    
    for issn, info in JOURNAL_MAPPING.items():
        # Fetch just 1 article to grab the exact string for 'Journal Name'
        url = f"https://api.openalex.org/works?filter=primary_location.source.issn:{issn}&per_page=1"
        response = requests.get(url)
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                journal_name = results[0].get('primary_location', {}).get('source', {}).get('display_name', 'Unknown')
                metadata_list.append({
                    "Journal Name": journal_name,
                    "Journal Grade": info["Grade"]
                })
        time.sleep(1)
        
    return metadata_list

def upload_metadata(dataframe):
    print("Connecting to Google Sheets...")
    client = gspread.oauth()
    spreadsheet = client.open(GOOGLE_SHEET_NAME)
    
    # Check if 'Journal Metadata' tab exists, if not, create it
    try:
        worksheet = spreadsheet.worksheet("Journal Metadata")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title="Journal Metadata", rows="100", cols="5")
        
    worksheet.clear()
    worksheet.update([dataframe.columns.values.tolist()] + dataframe.values.tolist())
    print("Metadata table created successfully!")

if __name__ == "__main__":
    meta_data = get_metadata()
    df = pd.DataFrame(meta_data)
    upload_metadata(df)