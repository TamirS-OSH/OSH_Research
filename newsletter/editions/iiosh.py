"""IIOSH institutional weekly edition — the original newsletter.

Every value here is lifted verbatim from the pre-refactor newsletter.py so this
edition's output stays byte-identical. Do not "tidy" the strings: the HTML is
compared against a golden file by tests/verify_iiosh_identity.py.
"""

EDITION = {
    "slug": "iiosh",
    "file_prefix": "IIOSH_Research_Update",
    "page_base_url_default": "https://tamirs-osh.github.io/OSH_Research",
    "recipient_env": "RECIPIENT_LIST",
    "email_subject": "IIOSH Weekly Research Update | לקט מחקרים שבועי",
    # Note: intentionally NOT the same string as title_en — the original From
    # header omitted "Weekly". Kept verbatim to preserve existing behaviour.
    "email_from_name": "IIOSH Research Update",
    "title_en": "IIOSH Weekly Research Update",
    "title_he": "לקט מחקרים שבועי",
    "intro_html": (
        "Here are the top discoveries published in high-impact journals over the past 7 days "
        "&mdash; primarily Q1, widening to Q1/Q2 and Q2 where weekly coverage is thin &mdash; "
        "categorized by subject domain. Each article is tagged with its journal quartile ranking:"
    ),
    "badge_tooltip": "Journal quartile ranking",
    "show_dashboard_button": True,

    "max_articles_per_subject": 5,

    # Original behaviour: query the Q1 tier first and widen to Q1/Q2 + Q2 only
    # when a domain yields `threshold` or fewer usable articles.
    "selection": {
        "mode": "fallback",
        "primary": ["Q1"],
        "fallback_order": ["Q1/Q2", "Q2"],
        "threshold": 2,
    },

    # No relevance filtering and no author feed — both stages no-op when empty.
    # Every journal on this list is on-topic by construction, so there is nothing
    # for a keyword filter to do.
    "keywords_core": [],
    "keywords_context": [],
    "keyword_min_score": 0,
    "tracked_authors": [],

    "journals": {
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
        "1520-6564": {"Subject": "Cognitive Ergonomics & HCI", "Grade": "Q2"},
    },
}
