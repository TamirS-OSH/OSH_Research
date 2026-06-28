import os
import re
import requests
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google import genai

# --- 1. CONFIGURATION ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PAGE_BASE_URL = os.environ.get("PAGE_BASE_URL", "https://tamirs-osh.github.io/OSH_Research")

# EDITORIAL CONTROL: Maximum number of articles allowed per subject category
MAX_ARTICLES_PER_SUBJECT = 5  

# Calculate the date 7 days ago (Weekly Roundup)
RECENT_DATE = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

# The FULL IIOSH target journals list
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

# --- 2. HELPER FUNCTIONS ---
def unscramble_abstract(inverted_index):
    if not inverted_index:
        return None
    max_index = max([idx for positions in inverted_index.values() for idx in positions])
    words = [""] * (max_index + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words).strip()

def summarize_with_ai(title, abstract):
    if not abstract:
        return {"en": "Abstract unavailable.", "he": "תקציר אינו זמין."}
        
    prompt = f"""
    You are an expert occupational health and safety researcher fluent in English and Hebrew. 
    Read the following academic abstract for the article '{title}'. 
    
    TASK:
    1. Provide a concise, professional 2-sentence summary of the main findings in English. Focus exclusively on novel discoveries and concrete results.
    2. Provide a precise, natural translation/adaptation of those exact 2 sentences into professional high-level Hebrew.
    
    CRITICAL FORMATTING INSTRUCTION: You must separate the responses using labels. Format your output EXACTLY like this:
    English: [Insert English summary here]
    Hebrew: [Insert Hebrew summary here]
    
    Abstract: {abstract}
    """
    
    max_retries = 3
    retry_delay = 15  
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model='gemini-3.1-flash-lite', contents=prompt)
            text = response.text.strip()
            if "English:" in text and "Hebrew:" in text:
                eng_part = text.split("Hebrew:")[0].replace("English:", "").strip()
                heb_part = text.split("Hebrew:")[1].strip()
                return {"en": eng_part, "he": heb_part}
            else:
                return {"en": text, "he": "תרגום עברי לא הופק כנדרש."}
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "429" in error_str:
                print(f"   ⚠️ Server busy or limit reached (Attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"AI Error: {e}")
                return {"en": "Error producing summary.", "he": "שגיאה בהפקת התקציר."}
                
    return {"en": "Summary skipped.", "he": "תקציר דולג עקב עומס שרת."}

def synthesize_domain_summary(subject, articles):
    if not articles:
        return {"en": "", "he": ""}
        
    articles_context = ""
    for i, art in enumerate(articles, 1):
        articles_context += f"Paper {i}: {art['title']}\nKey Finding: {art['summary_en']}\n\n"
        
    prompt = f"""
    You are the Director of Research at an Occupational Health and Safety Institute. 
    Review the following key findings from papers published this week in the domain of '{subject}':
    
    {articles_context}
    
    TASK:
    1. Write a single, high-impact paragraph (2-5 sentences) in English that synthesizes the overarching novel discoveries or trends shown across these papers. Focus strictly on collective findings.
    2. Provide an accurate, professional translation of that exact paragraph into fluent corporate Hebrew.
    
    CRITICAL FORMATTING INSTRUCTION: You must separate responses using labels. Format your output EXACTLY like this:
    English: [Insert English overview here]
    Hebrew: [Insert Hebrew overview here]
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model='gemini-3.1-flash-lite', contents=prompt)
            text = response.text.strip()
            if "English:" in text and "Hebrew:" in text:
                eng_part = text.split("Hebrew:")[0].replace("English:", "").strip()
                heb_part = text.split("Hebrew:")[1].strip()
                return {"en": eng_part, "he": heb_part}
            else:
                return {"en": text, "he": "סיכום מנהלים בעברית אינו זמין."}
        except Exception as e:
            print(f"   ⚠️ Domain synthesis server busy (Attempt {attempt + 1}/{max_retries}). Retrying...")
            time.sleep(15)
    return {"en": "Overview synthesis unavailable.", "he": "סיכום מנהלים אינו זמין זמנית."}

def synthesize_global_meta_briefing(all_articles):
    """Generates a master 1-2 paragraph briefing linking directly to inner anchor IDs."""
    if not all_articles:
        return {"en": "", "he": ""}
        
    articles_context = ""
    for art in all_articles:
        articles_context += f"-[ID: {art['id']}] Title: {art['title']}. Core Discovery: {art['summary_en']}\n"
        
    prompt = f"""
    You are the Chief Scientific Officer of an Occupational Health and Safety Institute. 
    Review all the key research summaries extracted across multiple domains this week:
    
    {articles_context}
    
    TASK:
    1. Write a master trend narrative briefing (maximum 2 paragraphs) in English summarizing the key breakthroughs and takeaways from this weekly digest.
    2. Provide a professional corporate Hebrew translation of this exact briefing (maximum 2 paragraphs).
    
    CRITICAL HYPERLINK INSTRUCTION:
    As you draft the narrative, you MUST weave internal HTML hyperlinks pointing to the corresponding article IDs whenever a discovery is mentioned. Wrap the descriptive finding text inside the anchor link tag. 
    Example: "This week's updates reveal that <a href='#art-1' style='color: #2563eb; text-decoration: underline;'>job strain triggers up to 18.2% of ischemic heart disease cases</a>, while environmental factors..."
    Ensure the Hebrew paragraphs map to the exact same anchor IDs (e.g., <a href='#art-1' style='color: #2563eb; text-decoration: underline;'>...</a>) around the translated discoveries.
    
    CRITICAL FORMATTING INSTRUCTION: Format your output EXACTLY like this:
    English: [Insert English narrative with links]
    Hebrew: [Insert Hebrew narrative with links]
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model='gemini-3.1-flash-lite', contents=prompt)
            text = response.text.strip()
            if "English:" in text and "Hebrew:" in text:
                eng_part = text.split("Hebrew:")[0].replace("English:", "").strip()
                heb_part = text.split("Hebrew:")[1].strip()
                return {"en": eng_part, "he": heb_part}
            else:
                return {"en": text, "he": "לקט מנהלים עברי אינו זמין זמנית."}
        except Exception as e:
            print(f"   ⚠️ Global meta synthesis server busy (Attempt {attempt + 1}/{max_retries}). Retrying...")
            time.sleep(15)
    return {"en": "Global trends summary unavailable.", "he": "תקציר מגמות אינו זמין."}

# --- 3. FETCHING AND PROCESSING ---
def fetch_and_summarize():
    print(f"Starting bilingual weekly data pull (Q1 Journals & Max {MAX_ARTICLES_PER_SUBJECT} per category)...")
    print(f"Fetching articles published since {RECENT_DATE}...\n")
    
    newsletter_data = {}
    flat_articles_list = []
    total_articles_processed = 0
    
    for issn, journal_info in JOURNAL_MAPPING.items():
        if journal_info["Grade"] != "Q1":
            continue
            
        subject = journal_info["Subject"]
        
        if subject in newsletter_data and len(newsletter_data[subject]["articles"]) >= MAX_ARTICLES_PER_SUBJECT:
            continue
            
        url = f"https://api.openalex.org/works?filter=primary_location.source.issn:{issn},from_publication_date:{RECENT_DATE}&sort=publication_date:desc&per_page=15"
        
        try:
            response = requests.get(url, timeout=15)
        except Exception as e:
            print(f"Network error fetching ISSN {issn}: {e}. Skipping.")
            continue
            
        if response.status_code == 200:
            results = response.json().get('results', [])
            
            if results and subject not in newsletter_data:
                newsletter_data[subject] = {"domain_summary_en": "", "domain_summary_he": "", "articles": []}
                
            for work in results:
                if len(newsletter_data[subject]["articles"]) >= MAX_ARTICLES_PER_SUBJECT:
                    print(f"   ⏭️ Cap of {MAX_ARTICLES_PER_SUBJECT} reached for category '{subject}'. Moving to next category.")
                    break
                    
                title = work.get('title', 'Untitled')
                journal_name = work.get('primary_location', {}).get('source', {}).get('display_name', 'Unknown Journal')
                link = work.get('doi', work.get('id'))
                
                raw_abstract = unscramble_abstract(work.get('abstract_inverted_index'))
                
                if raw_abstract:
                    article_id = f"art-{total_articles_processed + 1}"
                    print(f"[{total_articles_processed + 1}] Processing ({subject}): {title[:40]}...")
                    bilingual_summaries = summarize_with_ai(title, raw_abstract)
                    
                    article_node = {
                        "id": article_id,
                        "title": title,
                        "journal": journal_name,
                        "link": link,
                        "summary_en": bilingual_summaries["en"],
                        "summary_he": bilingual_summaries["he"]
                    }
                    
                    newsletter_data[subject]["articles"].append(article_node)
                    flat_articles_list.append(article_node)
                    
                    total_articles_processed += 1
                    time.sleep(12)  
                    
        time.sleep(3)
    
    print("\n" + "="*40)
    print("🧠 Generating Bilingual Category Executive Overviews...")
    print("="*40)
    for subject, domain_data in newsletter_data.items():
        if domain_data["articles"]:
            print(f"Synthesizing overview for: '{subject}'...")
            syn_data = synthesize_domain_summary(subject, domain_data["articles"])
            domain_data["domain_summary_en"] = syn_data["en"]
            domain_data["domain_summary_he"] = syn_data["he"]
            time.sleep(12) 
            
    print("\n" + "="*40)
    print("🌐 Compiling Global Linked Meta-Briefing Header...")
    print("="*40)
    global_meta_briefing = synthesize_global_meta_briefing(flat_articles_list)
            
    print(f"\nProcessing complete! Total curated articles summarized: {total_articles_processed}")
    return newsletter_data, global_meta_briefing

# --- 4. LOCAL HTML GENERATION ---
def generate_local_html(newsletter_data, global_meta):
    if not newsletter_data:
        print("No new articles to generate this week.")
        return None, None

    print("Building HTML layout with premium global summary deck...")
    
    html_content = f"""
    <html>
    <body dir="ltr" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.6; max-width: 850px; margin: 40px auto; padding: 25px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <h2 style="color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 12px; margin-top: 0; font-size: 26px; font-weight: 800;">IIOSH Weekly Research Update <span style="color: #94a3b8; font-weight: 300; font-size: 20px; margin: 0 10px;">|</span> לקט מחקרים שבועי</h2>
        
        <div style="margin: 20px 0 35px 0; padding: 22px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; color: #0f172a; font-size: 14.5px; line-height: 1.65;">
            <h3 style="margin-top: 0; margin-bottom: 14px; color: #1e3a8a; font-size: 17px; font-weight: 800; border-bottom: 1px solid #cbd5e1; padding-bottom: 6px;">Weekly Digest & Main Trends / תמצית מגמות שבועי</h3>
            <p style="margin: 0 0 16px 0; text-align: justify;">{global_meta['en']}</p>
            <hr style="border: 0; border-top: 1px dashed #cbd5e1; margin: 16px 0;">
            <p dir="rtl" style="margin: 0; text-align: right; font-weight: 500; font-size: 15px; line-height: 1.7;">{global_meta['he']}</p>
        </div>
        
        <p style="color: #475569; font-size: 15px; margin-bottom: 30px;">Here are the top discoveries published in high-impact Q1 journals over the past 7 days, categorized by subject domain:</p>
    """
    
    for subject, domain_data in newsletter_data.items():
        articles = domain_data["articles"]
        if not articles:  
            continue
            
        html_content += f"<h3 style='color: #1e3a8a; margin-top: 40px; margin-bottom: 15px; font-size: 22px; font-weight: 700; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;'>{subject}</h3>"
        
        if domain_data["domain_summary_en"] or domain_data["domain_summary_he"]:
            html_content += f"""
            <div style="margin: 15px 0 30px 0; padding: 22px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-top: 4px solid #0284c7; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); color: #334155; font-size: 14.5px; line-height: 1.65;">
                <p style="margin: 0 0 14px 0;"><strong style="color: #0369a1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Executive Summary:</strong> {domain_data['domain_summary_en']}</p>
                <hr style="border: 0; border-top: 1px dashed #cbd5e1; margin: 16px 0;">
                <p dir="rtl" style="margin: 0; text-align: right; font-weight: 500; color: #1e293b; font-size: 15px;"><strong style="color: #0369a1; font-weight: 700;">תמצית מנהלים:</strong> {domain_data['domain_summary_he']}</p>
            </div>
            """
            
        html_content += f"""
        <div style="margin: 35px 0 20px 15px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px;">
            <span style="color: #475569; font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; display: inline-block;">Articles / מאמרים מדעיים</span>
        </div>
        """
            
        for article in articles:
            html_content += f"""
            <div id="{article['id']}" style="margin-bottom: 25px; padding: 20px; background-color: #fafafa; border: 1px solid #f1f5f9; border-left: 5px solid #2563eb; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.01);">
                <h4 style="margin: 0 0 8px 0; color: #0f172a; font-size: 16px; font-weight: 700; line-height: 1.4;">{article['title']}</h4>
                <p style="margin: 0 0 16px 0; font-size: 13px; color: #64748b; letter-spacing: 0.3px;"><strong style="color: #475569;">Journal:</strong> {article['journal']}</p>
                
                <p style="margin: 0 0 14px 0; font-size: 14.5px; color: #334155; text-align: justify;">{article['summary_en']}</p>
                <p dir="rtl" style="margin: 0 0 18px 0; font-size: 14.5px; color: #1e293b; text-align: right; line-height: 1.6;">{article['summary_he']}</p>
                
                <a href="{article['link']}" style="color: #2563eb; text-decoration: none; font-weight: 700; font-size: 13.5px; display: inline-block;">[Read Full Article]</a>
            </div>
            """
            
    html_content += """
        <br>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin-top: 40px;">
        <p style="font-size: 12px; color: #94a3b8; text-align: center; margin-top: 15px;">This update is generated automatically. For historical data, please visit the IIOSH Research Dashboard.</p>
    </body>
    </html>
    """
    
    filename = f"IIOSH_Research_Update_{datetime.now().strftime('%Y-%m-%d')}.html"
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(html_content)
        print("\n" + "="*50)
        print(f"Newsletter saved: {filename}")
        print("="*50)
    except Exception as e:
        print(f"Failed to save local file: {e}")

    return html_content, filename


# --- 5. EMAIL DISTRIBUTION ---
def build_email_body(global_meta, page_url):
    en_text = re.sub(
        r"href=['\"]#(art-\d+)['\"]",
        lambda m: f'href="{page_url}#{m.group(1)}"',
        global_meta.get('en', '')
    )
    he_text = re.sub(
        r"href=['\"]#(art-\d+)['\"]",
        lambda m: f'href="{page_url}#{m.group(1)}"',
        global_meta.get('he', '')
    )

    return f"""<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 12px; margin-top: 0; font-size: 22px; font-weight: 800;">IIOSH Weekly Research Update <span style="color: #94a3b8; font-weight: 300; font-size: 16px; margin: 0 8px;">|</span> לקט מחקרים שבועי</h2>

    <div style="margin: 20px 0; padding: 18px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; color: #0f172a; font-size: 14px; line-height: 1.65;">
        <h3 style="margin-top: 0; margin-bottom: 10px; color: #1e3a8a; font-size: 15px; font-weight: 800; border-bottom: 1px solid #cbd5e1; padding-bottom: 6px;">Weekly Digest & Main Trends / תמצית מגמות שבועי</h3>
        <p style="margin: 0 0 14px 0; text-align: justify;">{en_text}</p>
        <hr style="border: 0; border-top: 1px dashed #cbd5e1; margin: 14px 0;">
        <p dir="rtl" style="margin: 0; text-align: right; font-weight: 500; font-size: 14px; line-height: 1.7;">{he_text}</p>
    </div>

    <div style="text-align: center; margin: 30px 0;">
        <a href="{page_url}" style="display: inline-block; padding: 12px 24px; background-color: #f8fafc; color: #2563eb; text-decoration: none; border: 2px solid #2563eb; border-radius: 6px; font-weight: 700; font-size: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">Read the Full Update &#8594; | &#8592; לקריאת הסקירה המלאה</a>
        <br><br>
        <a href="https://datastudio.google.com/reporting/f82c0682-5cf7-4201-a9fb-907573f9fee2" style="display: inline-block; padding: 12px 24px; background-color: #f8fafc; color: #15803d; text-decoration: none; border: 2px solid #15803d; border-radius: 6px; font-weight: 700; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">Check the literature dashboard | לבדיקת דשבורד הספרות המחקרית</a>
    </div>

    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin-top: 30px;">
    <p style="font-size: 11px; color: #94a3b8; text-align: center; margin-top: 12px;">This update is generated automatically by the IIOSH Research Pipeline.</p>
</body>
</html>"""

def send_email(subject, html_body, recipients):
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_password:
        print("Email credentials not configured. Skipping email send.")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"IIOSH Research Update <{gmail_user}>"
    msg['To'] = gmail_user

    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_password)
            all_recipients = [gmail_user] + recipients
            server.sendmail(gmail_user, all_recipients, msg.as_string())
        print(f"Email sent successfully to {len(recipients)} recipients.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    data_payload, meta_brief = fetch_and_summarize()
    html_content, filename = generate_local_html(data_payload, meta_brief)

    if html_content and filename:
        page_url = f"{PAGE_BASE_URL}/{filename}"
        email_body = build_email_body(meta_brief, page_url)

        recipient_str = os.environ.get("RECIPIENT_LIST", "")
        recipients = [r.strip() for r in recipient_str.split(",") if r.strip()]

        if recipients:
            send_email(
                "IIOSH Weekly Research Update | לקט מחקרים שבועי",
                email_body,
                recipients
            )
        else:
            print("No recipients configured. Skipping email send.")