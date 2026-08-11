import argparse
import json
import os
import re
import requests
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google import genai

import editions

# --- 1. CONFIGURATION ---
# Everything edition-specific (journals, tiering, branding, recipients) lives in
# newsletter/editions/<slug>.py. The rest of this file is edition-agnostic.
_parser = argparse.ArgumentParser(description="Generate and send a research newsletter edition.")
_parser.add_argument(
    "--edition",
    default="iiosh",
    help=f"Edition to build ({', '.join(editions.AVAILABLE)}). Default: iiosh",
)
_args, _ = _parser.parse_known_args()
EDITION = editions.load(_args.edition)
print(f"Building edition: {EDITION['slug']}", flush=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PAGE_BASE_URL = os.environ.get("PAGE_BASE_URL", EDITION["page_base_url_default"])

# EDITORIAL CONTROL: Maximum number of articles allowed per subject category
MAX_ARTICLES_PER_SUBJECT = EDITION["max_articles_per_subject"]

# Relevance filtering, in two classes of term:
#   core    — inherently on-topic anchors ("occupational exposure", "asbestos");
#             one match is enough to keep an article.
#   context — only meaningful with corroboration ("climate change", "latency");
#             these need KEYWORD_MIN_SCORE matches between them.
#
# Measured over 90 days of real abstracts, this rule suppresses broad-scope
# journals as hard as a flat score>=2 (2% pass rate) while keeping three times
# as much genuinely relevant material from the focused journals (43% vs 13%).
# A flat score>=1 was far too loose: it passed 47% of Nature Climate Change,
# including a paper on marine species conservation that matched "climate change".
#
# All inert when both lists are empty, which is why the IIOSH edition is
# unaffected by this stage.
KEYWORDS_CORE = EDITION.get("keywords_core", [])
KEYWORDS_CONTEXT = EDITION.get("keywords_context", [])
KEYWORDS = KEYWORDS_CORE + KEYWORDS_CONTEXT
KEYWORDS_CORE_SET = set(KEYWORDS_CORE)
KEYWORD_MIN_SCORE = EDITION.get("keyword_min_score", 0)

# A subject gate applied on top of the topic terms above. An edition whose
# subject is *occupational* anything needs this: topic terms alone will happily
# admit a climate paper with no work content, or an oncology paper with no
# exposure content. Empty means no gate.
OCCUPATIONAL_ANCHORS = EDITION.get("occupational_anchors", [])

# Persisted dedupe state for tracked-author feeds (see gather_author_candidates).
SEEN_STATE_PATH = os.path.join("state", f"{EDITION['slug']}_seen.json")

# Calculate the date 7 days ago (Weekly Roundup)
RECENT_DATE = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# OpenAlex politeness: supplying a contact email puts us in the faster, more
# reliable "polite pool" (far less likely to be rate-limited on shared CI IPs).
OPENALEX_MAILTO = os.environ.get("OPENALEX_MAILTO", "").strip()
REQUEST_HEADERS = {
    "User-Agent": f"IIOSH-Research-Newsletter/1.0 (mailto:{OPENALEX_MAILTO or 'contact-unset'})"
}

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

# Target journals for this edition: ISSN -> {Subject, Grade}
JOURNAL_MAPPING = EDITION["journals"]

# --- 2. HELPER FUNCTIONS ---
def fetch_openalex(url, issn, subject, max_retries=4):
    """GET an OpenAlex URL with retry/backoff. Returns a 200 Response or None.

    Logs every attempt with a [DIAG] prefix so failures are traceable in the
    CI logs (HTTP status + result count, plus the response body on non-200).
    Retries transient failures (429 Too Many Requests, 5xx) with exponential
    backoff, honoring a Retry-After header when present.
    """
    backoff = 5
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=20)
        except Exception as e:
            print(f"[DIAG] ISSN {issn} ({subject}) attempt {attempt}/{max_retries} -> EXCEPTION: {e}", flush=True)
            if attempt == max_retries:
                return None
            time.sleep(backoff)
            backoff *= 2
            continue

        n = len(resp.json().get('results', [])) if resp.status_code == 200 else 0
        print(f"[DIAG] ISSN {issn} ({subject}) attempt {attempt}/{max_retries} -> HTTP {resp.status_code}, {n} results", flush=True)

        if resp.status_code == 200:
            return resp

        print(f"[DIAG]   non-200 body (first 300 chars): {resp.text[:300]}", flush=True)
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
            retry_after = resp.headers.get("Retry-After", "")
            wait = int(retry_after) if retry_after.isdigit() else backoff
            print(f"[DIAG]   transient status, retrying in {wait}s...", flush=True)
            time.sleep(wait)
            backoff *= 2
            continue
        return None
    return None

def unscramble_abstract(inverted_index):
    if not inverted_index:
        return None
    max_index = max([idx for positions in inverted_index.values() for idx in positions])
    words = [""] * (max_index + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words).strip()

# Character class spanning U+2010..U+2015 (hyphen, non-breaking hyphen, figure
# dash, en dash, em dash, horizontal bar) plus the ASCII hyphen. The first and
# last characters of the range are literal, so take care if editing this line.
DASH_PATTERN = re.compile("[‐-―\\-]")


def normalize_text(text):
    """Lowercase and flatten punctuation so keyword matching is robust.

    Collapses hyphens and en/em dashes to spaces, which makes 'never-smokers'
    match 'never smokers' and the doc's 'exposure–response' (en dash) match a
    paper's 'exposure-response'. The result is space-padded so callers can test
    for ' term ' and get word-boundary matching for free.
    """
    # ‐-― covers hyphen, non-breaking hyphen, figure/en/em dash and
    # horizontal bar; spelled as escapes so the source can't be mangled by an
    # editor silently normalising the literal characters.
    lowered = DASH_PATTERN.sub(" ", text.lower())
    return " " + re.sub(r"[^a-z0-9]+", " ", lowered).strip() + " "


def keyword_score(title, abstract):
    """Score an article against the edition's keyword lists.

    Returns (total distinct matches, core matches, occupational-anchor matches,
    matched terms). Editions with no keywords always score 0 and are never
    filtered — see gather_candidates.
    """
    if not KEYWORDS:
        return 0, 0, 0, []
    haystack = normalize_text(f"{title} {abstract}")
    matched = [term for term in KEYWORDS if f" {term} " in haystack]
    core_hits = sum(1 for term in matched if term in KEYWORDS_CORE_SET)
    occ_hits = sum(1 for anchor in OCCUPATIONAL_ANCHORS if f" {anchor} " in haystack)
    return len(matched), core_hits, occ_hits, matched


def is_relevant(score, core_hits, occ_hits):
    """Subject gate, then topic rule.

    The gate exists because topic terms alone are not sufficient evidence: a
    paper matching 'climate change' and 'air pollution' can be about a national
    health-system plan with no work content at all. Requiring an occupational
    anchor first cut broad-journal noise from 3.0% to 1.3% while costing only
    four points of recall on the focused journals.
    """
    if OCCUPATIONAL_ANCHORS and occ_hits < 1:
        return False
    return core_hits >= 1 or score >= KEYWORD_MIN_SCORE


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
# "fallback" editions only: when a domain yields this many usable primary-tier
# articles or fewer, widen the search to that domain's lower-graded journals.
FALLBACK_THRESHOLD = EDITION["selection"].get("threshold", 2)


def gather_candidates(journal_entries, subject):
    """Fetch + extract displayable article candidates from a list of journals.

    journal_entries: list of (issn, grade) tuples to query, in priority order.
    Returns candidate dicts (title/journal/link/abstract/grade) preserving order.
    A candidate must have a usable abstract to count — that is the same gate the
    display uses. AI summarization is deliberately deferred to the caller so we
    don't spend Gemini calls on articles that end up trimmed by the per-domain cap.
    """
    candidates = []
    for issn, grade in journal_entries:
        url = f"https://api.openalex.org/works?filter=primary_location.source.issn:{issn},from_publication_date:{RECENT_DATE}&sort=publication_date:desc&per_page=15"
        if OPENALEX_MAILTO:
            url += f"&mailto={OPENALEX_MAILTO}"

        response = fetch_openalex(url, issn, subject)
        if response is None:
            print(f"   ⚠️ Gave up on ISSN {issn} ({subject}) after retries. Skipping.", flush=True)
            continue

        for work in response.json().get('results', []):
            raw_abstract = unscramble_abstract(work.get('abstract_inverted_index'))
            if not raw_abstract:
                continue

            title = work.get('title', 'Untitled')

            # Relevance gate. Runs before any Gemini call, so an off-topic paper
            # never costs a summarization request. Inert when the edition has no
            # keywords, which is why the IIOSH edition is unaffected.
            if KEYWORDS:
                score, core_hits, occ_hits, matched = keyword_score(title, raw_abstract)
                keep = is_relevant(score, core_hits, occ_hits)
                # Every candidate is logged, rejects included, so the rule can be
                # retuned from observed scores rather than guessed at. occ=0 on a
                # dropped row means it failed the subject gate, not the topic rule.
                print(
                    f"[KW] {'KEEP' if keep else 'DROP'} score={score} core={core_hits} "
                    f"occ={occ_hits} min={KEYWORD_MIN_SCORE} "
                    f"terms=[{', '.join(matched[:6])}] :: {title[:70]}",
                    flush=True,
                )
                if not keep:
                    continue

            candidates.append({
                "title": title,
                "journal": work.get('primary_location', {}).get('source', {}).get('display_name', 'Unknown Journal'),
                "link": work.get('doi', work.get('id')),
                "abstract": raw_abstract,
                "grade": grade,
            })
        time.sleep(3)
    return candidates


def build_subject_tiers():
    """Group journals by subject and split them into a primary and fallback tier.

    Driven by the edition's `selection` config:

      mode="fallback" — query the `primary` grades first and widen to the rest
                        only when a subject comes back thin. This is the original
                        IIOSH behaviour (Q1, widening to Q1/Q2 then Q2).
      mode="ranked"   — query every grade in `include` on each run, ordered by
                        `rank_order`, with no fallback stage. Grades outside
                        `include` are skipped entirely, which is how tier C stays
                        configured but out of the weekly run.

    Returns (subjects_order, tier1, tier2); tier2 is empty in ranked mode.
    """
    selection = EDITION["selection"]
    mode = selection["mode"]

    if mode == "fallback":
        primary = selection["primary"]
        fallback_order = selection.get("fallback_order", [])
    else:
        primary = selection["include"]
        fallback_order = []

    rank_order = selection.get("rank_order", primary)

    subjects_order = []
    tier1, tier2 = {}, {}
    for issn, info in JOURNAL_MAPPING.items():
        subject, grade = info["Subject"], info["Grade"]
        if subject not in tier1:
            subjects_order.append(subject)
            tier1[subject], tier2[subject] = [], []
        if grade in primary:
            tier1[subject].append((issn, grade))
        elif mode == "fallback":
            tier2[subject].append((issn, grade))

    # sorted() is stable, so journals keep their configured order within a grade.
    if mode == "fallback":
        for subject in tier2:
            tier2[subject].sort(
                key=lambda e: fallback_order.index(e[1]) if e[1] in fallback_order else len(fallback_order)
            )
    else:
        for subject in tier1:
            tier1[subject].sort(
                key=lambda e: rank_order.index(e[1]) if e[1] in rank_order else len(rank_order)
            )

    return subjects_order, tier1, tier2


def load_seen_state():
    """Return the persisted (work_ids, title_keys) already sent by this edition."""
    try:
        with open(SEEN_STATE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return set(data.get("work_ids", [])), set(data.get("title_keys", []))
    except (FileNotFoundError, ValueError):
        return set(), set()


def save_seen_state(work_ids, title_keys):
    os.makedirs(os.path.dirname(SEEN_STATE_PATH), exist_ok=True)
    with open(SEEN_STATE_PATH, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "work_ids": sorted(work_ids),
                "title_keys": sorted(title_keys),
                "updated": datetime.now().strftime("%Y-%m-%d"),
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )


def gather_author_candidates(author, seen_ids, seen_titles):
    """Fetch a tracked researcher's recent publications, minus anything already sent.

    Deliberately independent of the journal list, the tier ranking and the
    keyword filter: the point is to catch everything this person publishes,
    including in venues that are not on the list at all.

    The window is 30 days rather than the journal feed's 7. An individual
    researcher publishes only a handful of articles a year, so a weekly window
    would be empty on almost every run. That makes dedupe mandatory — otherwise
    the same paper reappears for four consecutive weeks.

    Records are restricted to real articles with abstracts. OpenAlex also
    returns conference abstracts and companion "Data from ..." / "Supplementary
    Figure from ..." stubs for the same work, which are noise in a digest.
    """
    window_days = author.get("window_days", 30)
    since = (datetime.now() - timedelta(days=window_days)).strftime('%Y-%m-%d')
    filters = [
        f"author.id:{author['openalex_id']}",
        f"from_publication_date:{since}",
    ]
    if author.get("types"):
        filters.append("type:" + "|".join(author["types"]))
    if author.get("require_abstract", True):
        filters.append("has_abstract:true")

    url = (
        "https://api.openalex.org/works?filter=" + ",".join(filters)
        + "&sort=publication_date:desc&per_page=25"
    )
    if OPENALEX_MAILTO:
        url += f"&mailto={OPENALEX_MAILTO}"

    label = author["name"]
    response = fetch_openalex(url, author["openalex_id"], label)
    if response is None:
        print(f"   ⚠️ Gave up on tracked author {label} after retries. Skipping.", flush=True)
        return []

    candidates = []
    for work in response.json().get('results', []):
        work_id = (work.get('id') or '').replace('https://openalex.org/', '')
        raw_abstract = unscramble_abstract(work.get('abstract_inverted_index'))
        if not raw_abstract:
            continue

        title = work.get('title', 'Untitled')
        # Dedupe on both the OpenAlex ID and a normalised title: the same paper
        # can appear under two IDs (e.g. an editorial carried by two venues),
        # which an ID-only seen-set would let through twice.
        title_key = normalize_text(title).strip()
        if work_id in seen_ids or title_key in seen_titles:
            print(f"[AUTHOR] SEEN  {label}: {title[:70]}", flush=True)
            continue

        print(f"[AUTHOR] NEW   {label}: {title[:70]}", flush=True)
        candidates.append({
            "title": title,
            "journal": work.get('primary_location', {}).get('source', {}).get('display_name', 'Unknown Journal'),
            "link": work.get('doi', work.get('id')),
            "abstract": raw_abstract,
            "grade": "",
            "work_id": work_id,
            "title_key": title_key,
        })

    return candidates


def fetch_and_summarize():
    selection_mode = EDITION["selection"]["mode"]
    strategy = (
        "tiered Q1 -> Q1/Q2+Q2 fallback" if selection_mode == "fallback"
        else "ranked " + "+".join(EDITION["selection"]["include"])
    )
    print(f"Starting bilingual weekly data pull ({strategy}, Max {MAX_ARTICLES_PER_SUBJECT} per category)...")
    print(f"Fetching articles published since {RECENT_DATE}...\n")

    subjects_order, tier1, tier2 = build_subject_tiers()

    newsletter_data = {}
    flat_articles_list = []
    total_articles_processed = 0

    for subject in subjects_order:
        print(f"\n--- Domain: {subject} ---")
        candidates = gather_candidates(tier1[subject], subject)
        print(f"[DIAG] Domain '{subject}': {len(candidates)} usable primary-tier article(s).", flush=True)

        if selection_mode == "fallback":
            if len(candidates) <= FALLBACK_THRESHOLD and tier2[subject]:
                print(f"[DIAG] Domain '{subject}' at/under threshold ({FALLBACK_THRESHOLD}); widening to Q1/Q2 + Q2.", flush=True)
                candidates += gather_candidates(tier2[subject], subject)
            elif len(candidates) <= FALLBACK_THRESHOLD:
                print(f"[DIAG] Domain '{subject}' at/under threshold but has no lower-graded journals to fall back to.", flush=True)

        selected = candidates[:MAX_ARTICLES_PER_SUBJECT]
        if not selected:
            continue

        newsletter_data[subject] = {"domain_summary_en": "", "domain_summary_he": "", "articles": []}
        for cand in selected:
            total_articles_processed += 1
            article_id = f"art-{total_articles_processed}"
            print(f"[{total_articles_processed}] Processing ({subject}) [{cand['grade']}]: {cand['title'][:40]}...")
            bilingual_summaries = summarize_with_ai(cand["title"], cand["abstract"])

            article_node = {
                "id": article_id,
                "title": cand["title"],
                "journal": cand["journal"],
                "grade": cand["grade"],
                "link": cand["link"],
                "summary_en": bilingual_summaries["en"],
                "summary_he": bilingual_summaries["he"],
            }

            newsletter_data[subject]["articles"].append(article_node)
            flat_articles_list.append(article_node)
            time.sleep(12)

    # Tracked-author feed. Each author becomes its own section, appended after
    # the themed domains. No-op for editions with no tracked_authors.
    tracked_authors = EDITION.get("tracked_authors", [])
    if tracked_authors:
        seen_ids, seen_titles = load_seen_state()
        newly_sent_ids, newly_sent_titles = set(), set()

        for author in tracked_authors:
            section = author.get("section_title", f"Tracked Researcher: {author['name']}")
            print(f"\n--- {section} ---")
            author_candidates = gather_author_candidates(author, seen_ids, seen_titles)
            if not author_candidates:
                window = author.get("window_days", 30)
                print(f"[DIAG] No unseen publications for {author['name']} in the last {window} days.", flush=True)
                continue

            newsletter_data[section] = {"domain_summary_en": "", "domain_summary_he": "", "articles": []}
            # Anything over the cap is left unmarked, so it surfaces next run
            # instead of being silently dropped.
            for cand in author_candidates[:MAX_ARTICLES_PER_SUBJECT]:
                total_articles_processed += 1
                article_id = f"art-{total_articles_processed}"
                print(f"[{total_articles_processed}] Processing ({author['name']}): {cand['title'][:40]}...")
                bilingual_summaries = summarize_with_ai(cand["title"], cand["abstract"])

                article_node = {
                    "id": article_id,
                    "title": cand["title"],
                    "journal": cand["journal"],
                    "grade": cand["grade"],
                    "link": cand["link"],
                    "summary_en": bilingual_summaries["en"],
                    "summary_he": bilingual_summaries["he"],
                }

                newsletter_data[section]["articles"].append(article_node)
                flat_articles_list.append(article_node)
                newly_sent_ids.add(cand["work_id"])
                newly_sent_titles.add(cand["title_key"])
                time.sleep(12)

        save_seen_state(seen_ids | newly_sent_ids, seen_titles | newly_sent_titles)
        print(f"[DIAG] Seen-state written to {SEEN_STATE_PATH} "
              f"({len(seen_ids | newly_sent_ids)} work ids).", flush=True)

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
def grade_badge_html(grade):
    """Return a small coloured pill showing the journal's grade for this edition.

    Quartile grades (Q1/Q1-Q2/Q2) and monitoring tiers (A/B/C) share one palette;
    the keys don't collide, so an edition uses whichever vocabulary it configures.
    Articles with no grade — tracked-author entries, which sit outside the tier
    system — render no badge at all.
    """
    if not grade:
        return ""
    palette = {
        "Q1":    ("#dbeafe", "#1d4ed8", "#1e3a8a"),  # blue
        "Q1/Q2": ("#cffafe", "#0e7490", "#155e75"),  # cyan (hybrid)
        "Q2":    ("#fef3c7", "#b45309", "#92400e"),  # amber
        "A":     ("#dbeafe", "#1d4ed8", "#1e3a8a"),  # blue  — core weekly
        "B":     ("#cffafe", "#0e7490", "#155e75"),  # cyan  — focused
        "C":     ("#fef3c7", "#b45309", "#92400e"),  # amber — periodic
    }
    bg, border, text = palette.get(grade, ("#f1f5f9", "#94a3b8", "#475569"))
    return (
        f"<span title=\"{EDITION['badge_tooltip']}\" style=\"display: inline-block; "
        f"padding: 3px 11px; background-color: {bg}; border: 1px solid {border}; "
        f"color: {text}; border-radius: 999px; font-size: 11px; font-weight: 800; "
        f"letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap;\">{grade}</span>"
    )


def generate_local_html(newsletter_data, global_meta):
    if not newsletter_data:
        print("No new articles to generate this week.")
        return None, None

    print("Building HTML layout with premium global summary deck...")
    
    html_content = f"""
    <html>
    <body dir="ltr" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.6; max-width: 850px; margin: 40px auto; padding: 25px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <h2 style="color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 12px; margin-top: 0; font-size: 26px; font-weight: 800;">{EDITION['title_en']} <span style="color: #94a3b8; font-weight: 300; font-size: 20px; margin: 0 10px;">|</span> {EDITION['title_he']}</h2>
        
        <div style="margin: 20px 0 35px 0; padding: 22px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; color: #0f172a; font-size: 14.5px; line-height: 1.65;">
            <h3 style="margin-top: 0; margin-bottom: 14px; color: #1e3a8a; font-size: 17px; font-weight: 800; border-bottom: 1px solid #cbd5e1; padding-bottom: 6px;">Weekly Digest & Main Trends / תמצית מגמות שבועי</h3>
            <p style="margin: 0 0 16px 0; text-align: justify;">{global_meta['en']}</p>
            <hr style="border: 0; border-top: 1px dashed #cbd5e1; margin: 16px 0;">
            <p dir="rtl" style="margin: 0; text-align: right; font-weight: 500; font-size: 15px; line-height: 1.7;">{global_meta['he']}</p>
        </div>
        
        <p style="color: #475569; font-size: 15px; margin-bottom: 30px;">{EDITION['intro_html']}</p>
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

                <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px;">
                    <a href="{article['link']}" style="color: #2563eb; text-decoration: none; font-weight: 700; font-size: 13.5px; display: inline-block;">[Read Full Article]</a>
                    {grade_badge_html(article.get('grade', ''))}
                </div>
            </div>
            """
            
    html_content += """
        <br>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin-top: 40px;">
        <p style="font-size: 12px; color: #94a3b8; text-align: center; margin-top: 15px;">This update is generated automatically. For historical data, please visit the IIOSH Research Dashboard.</p>
    </body>
    </html>
    """
    
    filename = f"{EDITION['file_prefix']}_{datetime.now().strftime('%Y-%m-%d')}.html"
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

    # Held as a literal (including its leading newline and indentation) so the
    # IIOSH email is byte-identical; editions without a dashboard omit the block.
    dashboard_button = ""
    if EDITION["show_dashboard_button"]:
        dashboard_button = """
        <br><br>
        <a href="https://datastudio.google.com/reporting/f82c0682-5cf7-4201-a9fb-907573f9fee2" style="display: inline-block; padding: 12px 24px; background-color: #f8fafc; color: #15803d; text-decoration: none; border: 2px solid #15803d; border-radius: 6px; font-weight: 700; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">Check the Literature Dashboard  לבדיקת דשבורד הספרות המחקרית</a>"""

    return f"""<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 12px; margin-top: 0; font-size: 22px; font-weight: 800;">{EDITION['title_en']} <span style="color: #94a3b8; font-weight: 300; font-size: 16px; margin: 0 8px;">|</span> {EDITION['title_he']}</h2>

    <div style="margin: 20px 0; padding: 18px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; color: #0f172a; font-size: 14px; line-height: 1.65;">
        <h3 style="margin-top: 0; margin-bottom: 10px; color: #1e3a8a; font-size: 15px; font-weight: 800; border-bottom: 1px solid #cbd5e1; padding-bottom: 6px;">Weekly Digest & Main Trends / תמצית מגמות שבועי</h3>
        <p style="margin: 0 0 14px 0; text-align: justify;">{en_text}</p>
        <hr style="border: 0; border-top: 1px dashed #cbd5e1; margin: 14px 0;">
        <p dir="rtl" style="margin: 0; text-align: right; font-weight: 500; font-size: 14px; line-height: 1.7;">{he_text}</p>
    </div>

    <div style="text-align: center; margin: 30px 0;">
        <a href="{page_url}" style="display: inline-block; padding: 12px 24px; background-color: #f8fafc; color: #2563eb; text-decoration: none; border: 2px solid #2563eb; border-radius: 6px; font-weight: 700; font-size: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">Read the Full Update  לקריאת הסקירה המלאה</a>{dashboard_button}
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
    msg['From'] = f"{EDITION['email_from_name']} <{gmail_user}>"
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

        recipient_str = os.environ.get(EDITION["recipient_env"], "")
        recipients = [r.strip() for r in recipient_str.split(",") if r.strip()]

        if recipients:
            send_email(
                EDITION["email_subject"],
                email_body,
                recipients
            )
        else:
            print(f"No recipients configured in {EDITION['recipient_env']}. Skipping email send.")