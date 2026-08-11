"""Occupational cancer research edition.

Built from the researcher's specification (see
docs/Occupational_Cancer_Edition_Plan.md). 64 journals across 5 themes, graded
A/B/C, filtered by keyword relevance, plus a tracked-author feed.

Journal ISSNs were resolved against the OpenAlex /sources endpoint and each
non-exact match was verified by direct ISSN lookup — six of the naive top hits
were the wrong journal (e.g. "Epidemiology" matched *American Journal of
Epidemiology*, "Health Services Research" matched *BMC* Health Services
Research). Comments below record the title each ISSN actually resolves to.
"""

EDITION = {
    "slug": "occ_cancer",
    "file_prefix": "OccCancer_Research_Update",
    "page_base_url_default": "https://tamirs-osh.github.io/OSH_Research/occ",
    "recipient_env": "RECIPIENT_LIST_OCC",
    "email_subject": "Occupational Cancer Research Update | לקט מחקר סרטן תעסוקתי",
    "email_from_name": "Occupational Cancer Research Update",
    "title_en": "Occupational Cancer Research Update",
    "title_he": "לקט מחקר סרטן תעסוקתי",
    "intro_html": (
        "New publications from the past 7 days across the tracked journal list "
        "&mdash; tier A first, widening to tier B &mdash; filtered for topical relevance "
        "and grouped by research theme. Each article is tagged with its monitoring tier:"
    ),
    "badge_tooltip": "Monitoring tier (A = core weekly, B = focused, C = periodic)",
    "show_dashboard_button": False,

    "max_articles_per_subject": 5,

    # A and B are both queried every week and ranked A-first; the per-theme cap
    # fills from A before B. C is configured but excluded from the weekly run —
    # the source doc defines tier C as "periodic or during a targeted search".
    "selection": {
        "mode": "ranked",
        "include": ["A", "B"],
        "rank_order": ["A", "B", "C"],
    },

    # Relevance filter. Scored locally on title + abstract BEFORE any Gemini call,
    # so off-topic papers never consume quota. Without this, broad-scope journals
    # on the list (Nature Climate Change, Health Affairs, Social Science &
    # Medicine, The Lancet Public Health) would flood the edition.
    #
    # Derived once, by hand, from the 21 lines under "מילות סינון לאלגוריתם" in
    # the source doc. Comma-lists there were expanded into separate terms rather
    # than split at runtime, which would be a silent-failure path. Terms are
    # stored pre-normalised: lowercase, dashes collapsed to spaces.
    #
    # Original doc lines, for traceability:
    #   occupational lung cancer
    #   lung cancer in never-smokers
    #   low smoking exposure and occupational carcinogens
    #   combined, cumulative and sequential occupational exposures
    #   asbestos, silica, diesel exhaust, PAH, nickel, chromium and welding fumes
    #   joint effects, additive interaction and multiplicative interaction
    #   exposure–response, dose–response and cumulative exposure
    #   latency, time since exposure and time since last exposure
    #   occupational cancer surveillance after exposure
    #   occupational disease notification, compensation and recognition
    #   exposure registries, record retention and administrative data linkage
    #   industry and occupation in electronic health records
    #   Occupational Data for Health, EHR, coding and NLP
    #   job-exposure matrices and occupational exposome
    #   return to work after cancer
    #   work ability, work retention and workplace accommodations
    #   occupational rehabilitation and disability management
    #   climate change and occupational heat stress
    #   wildfire smoke, air pollution, UV and extreme weather at work
    #   occupational exposure limits and regulatory policy
    #   implementation of occupational health policy
    #
    # Terms are scoped PER THEME, taken from the "Monitoring topics" column the
    # source doc gives for every journal. A single global list was tried first
    # and failed in the first live run: a term qualifying for any theme admitted
    # an article to every theme, so seven of eight articles were filed under
    # "Lung Cancer & Occupational Exposures" and not one was about lung cancer
    # (job strain and heart disease, night work and long-COVID, diabetes
    # absenteeism, occupational health of caregivers).
    #
    # The theme an article is filed under is decided by its journal, so its
    # content has to earn that heading.
    #
    # Within each theme:
    #   core    — unmistakably that theme's subject; one match is enough.
    #   context — real signal but weaker; needs keyword_min_score matches.
    # The global occupational_anchors gate applies on top of both.
    "themes": {
        # א — the central research question: lung cancer from occupational
        # carcinogens, combined exposures, never-smokers, latency. Exposure
        # methodology (JEMs, exposome) is context rather than core: a JEM paper
        # about ischaemic heart disease is methodologically interesting but is
        # not this theme's subject, and needs a second term to qualify.
        "Lung Cancer & Occupational Exposures": {
            # No context-only path for this theme. Its context list contains
            # exposure methodology (job exposure matrices, exposure assessment,
            # exposome), and two of those pair with each other to admit a paper
            # with no cancer or carcinogen content — which is exactly how a
            # job-strain / ischaemic-heart-disease paper reached a lung cancer
            # heading. An article must name a cancer, a carcinogen, or one of
            # her agents to appear here.
            "require_core": True,
            "core": [
                "lung cancer",
                "occupational lung cancer",
                "occupational cancer",
                "occupational carcinogen",
                "lung carcinogen",
                "carcinogen",
                "carcinogenic",
                "asbestos",
                "asbestosis",
                "mesothelioma",
                "silica",
                "silicosis",
                "diesel exhaust",
                "polycyclic aromatic hydrocarbon",
                "welding fume",
                "hexavalent chromium",
                "pneumoconiosis",
                "occupational lung disease",
                "occupational respiratory disease",
                "never smoker",
            ],
            "context": [
                "cancer",
                "nickel",
                "chromium",
                "pah",
                "exposure response",
                "dose response",
                "cumulative exposure",
                "combined exposure",
                "sequential exposure",
                "joint effect",
                "additive interaction",
                "multiplicative interaction",
                "latency",
                "time since exposure",
                "time since last exposure",
                "occupational exposure",
                "exposure assessment",
                "exposure measurement",
                "job exposure matrix",
                "job exposure matrices",
                "occupational exposome",
                "exposome",
                "cancer surveillance",
                "cancer epidemiology",
                "occupational disease",
                "respirable dust",
                "airborne exposure",
            ],
        },
        # ב — Occupational Data for Health: getting industry and occupation into
        # health records and reusing them for research.
        "Occupational Data in Health Records": {
            "core": [
                "occupational data for health",
                "industry and occupation",
                "occupation coding",
                "job coding",
                "occupational history",
                "work history",
            ],
            "context": [
                "electronic health record",
                "ehr",
                "medical record",
                "health record",
                "natural language processing",
                "nlp",
                "record linkage",
                "data linkage",
                "administrative data",
                "interoperability",
                "clinical informatics",
                "health informatics",
                "data quality",
                "registry",
                "registries",
                "structured data",
                "coding",
            ],
        },
        # ג — return to work, work retention and rehabilitation, including after
        # cancer.
        "Return to Work & Rehabilitation": {
            "core": [
                "return to work",
                "work ability",
                "work retention",
                "workplace accommodation",
                "occupational rehabilitation",
                "vocational rehabilitation",
                "disability management",
                "work participation",
                "work disability",
                "sick leave",
                "sickness absence",
                "fitness for work",
            ],
            "context": [
                "cancer survivorship",
                "survivorship",
                "employment outcome",
                "employment",
                "rehabilitation",
                "functional capacity",
                "work capacity",
                "occupational therapy",
                "workplace intervention",
            ],
        },
        # ד — climate change as it reaches workers: heat, wildfire smoke, UV,
        # extreme weather.
        "Climate Change & Worker Health": {
            "core": [
                "occupational heat",
                "heat stress",
                "heat strain",
                "heat exposure",
                "wildfire smoke",
                "outdoor worker",
                "outdoor workers",
                "thermal strain",
                "thermal comfort",
                "work capacity",
            ],
            "context": [
                "climate change",
                "extreme heat",
                "extreme weather",
                "ambient temperature",
                "air pollution",
                "ultraviolet",
                "uv radiation",
                "heat wave",
                "heatwave",
                "productivity loss",
                "adaptation",
            ],
        },
        # ה — regulation, exposure limits, disease recognition and compensation.
        "Policy, Regulation & Health Systems": {
            "core": [
                "occupational exposure limit",
                "occupational health policy",
                "occupational safety and health",
                "occupational health service",
                "occupational health surveillance",
                "disease notification",
                "disease recognition",
                "workers compensation",
                "occupational injury",
                "occupational disease",
            ],
            "context": [
                "exposure limit",
                "regulation",
                "regulatory",
                "legislation",
                "enforcement",
                "compensation",
                "health policy",
                "prevention policy",
                "surveillance",
                "governance",
                "labour inspection",
                "labor inspection",
            ],
        },
    },
    # Context-only articles need this many matches within their own theme.
    # A single core match bypasses it.
    "keyword_min_score": 2,

    # Subject gate, applied BEFORE the topic rule above: an article must show
    # some occupational content or it is rejected outright, however well it
    # scores on topic.
    #
    # Added after the first live run selected "Developing a strategic plan for a
    # climate-resilient health system" — no work content at all, admitted purely
    # by "climate change" + "air pollution". Her subject is not climate, or
    # policy, or oncology; it is *occupational* climate, policy and oncology.
    #
    # Effect over 90 days: broad-journal noise 3.0% -> 1.3% (Nature Climate
    # Change 7% -> 0%, PLOS Global Public Health 4% -> 0%, Health Affairs
    # 2% -> 0%) for four points of recall on the focused journals.
    #
    # NOTE: "workforce" is deliberately absent. In health-policy writing it
    # means hospital staffing levels, and it was the single anchor that let the
    # climate-resilient-health-system paper through on a first attempt.
    "occupational_anchors": [
        "occupational",
        "occupation",
        "worker",
        "workers",
        "workplace",
        "work related",
        "working conditions",
        "at work",
        "employee",
        "employees",
        "employment",
        "job exposure",
        "job strain",
        "return to work",
        "work ability",
        "miner",
        "miners",
        "farmer",
        "farmers",
        "shift work",
        "night shift",
    ],

    # Standalone section, independent of the journal list, tiers and keyword
    # filter — it should catch anything she publishes, including in venues that
    # are not on the list at all.
    #
    # Author ID resolved from two DOIs in the doc's own reference list rather
    # than by name search ("Ann Olsson" returns many OpenAlex candidates); both
    # resolved to the same ID, ORCID and IARC affiliation.
    #
    # NOTE: the OpenAlex author cluster contains historical contamination from
    # other people named Olsson (its oldest works are 1930s-50s agronomy and
    # 1980s virology). Recent output is all genuinely hers, so a rolling window
    # is safe, but never use this ID for a historical query.
    #
    # The type/abstract filter matters: of 14 records in a sample 365-day
    # window, only 5 were real articles — the rest were conference abstracts and
    # AACR-style "Data from ..." / "Supplementary Figure from ..." companions.
    "tracked_authors": [
        {
            "name": "Ann Olsson",
            "openalex_id": "A5064971907",
            "orcid": "0000-0001-6498-2259",
            "affiliation": "IARC / WHO",
            # 60 rather than 30: her real cadence is ~5 articles a year (the
            # section is legitimately absent most weeks), so the window governs
            # how much OpenAlex indexing lag is tolerated, not how much she sees.
            # Dedupe makes the extra reach free — nothing is ever shown twice.
            "window_days": 60,
            "types": ["article"],
            "require_abstract": True,
            "section_title": "Tracked Researcher: Ann Olsson",
        }
    ],

    "journals": {
        # --- Lung Cancer & Occupational Exposures ---
        "1073-449X": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # American Journal of Respiratory and Critical Care Medicine
        "0091-6765": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # Environmental Health Perspectives
        "1055-9965": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # Cancer Epidemiology Biomarkers & Prevention
        "1044-3983": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # Epidemiology  [corrected: top hit was Am J Epidemiology]
        "0007-1072": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # Occupational and Environmental Medicine
        "0271-3586": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # American Journal of Industrial Medicine
        "2398-7308": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # Annals of Work Exposures and Health
        "1559-0631": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # Journal of Exposure Science & Environmental Epidemiology
        "0355-3140": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # Scandinavian Journal of Work Environment & Health
        "1438-4639": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # International Journal of Hygiene and Environmental Health
        "0340-0131": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # International Archives of Occupational and Environmental Health
        "1076-2752": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # Journal of Occupational and Environmental Medicine
        "1341-9145": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # Journal of Occupational Health  [corrected: top hit was J Occup Health Psychology]
        "0962-7480": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "A"},  # Occupational Medicine
        "0169-5002": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "B"},  # Lung Cancer
        "0040-6376": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "B"},  # Thorax
        "0903-1936": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "B"},  # European Respiratory Journal
        "0020-7136": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "B"},  # International Journal of Cancer
        "1574-7891": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "B"},  # Molecular Oncology
        "1745-6673": {"Subject": "Lung Cancer & Occupational Exposures", "Grade": "B"},  # Journal of Occupational Medicine and Toxicology

        # --- Occupational Data in Health Records ---
        "1067-5027": {"Subject": "Occupational Data in Health Records", "Grade": "A"},  # Journal of the American Medical Informatics Association
        "1532-0464": {"Subject": "Occupational Data in Health Records", "Grade": "A"},  # Journal of Biomedical Informatics
        "2632-1009": {"Subject": "Occupational Data in Health Records", "Grade": "A"},  # BMJ Health & Care Informatics
        "1386-5056": {"Subject": "Occupational Data in Health Records", "Grade": "B"},  # International Journal of Medical Informatics
        "2291-9694": {"Subject": "Occupational Data in Health Records", "Grade": "B"},  # JMIR Medical Informatics
        "1748-5908": {"Subject": "Occupational Data in Health Records", "Grade": "B"},  # Implementation Science
        "2379-6146": {"Subject": "Occupational Data in Health Records", "Grade": "B"},  # Learning Health Systems
        "2399-4908": {"Subject": "Occupational Data in Health Records", "Grade": "B"},  # International Journal for Population Data Science  [doc said "of"; actual title is "for"]

        # --- Return to Work & Rehabilitation ---
        "1053-0487": {"Subject": "Return to Work & Rehabilitation", "Grade": "A"},  # Journal of Occupational Rehabilitation
        "1932-2259": {"Subject": "Return to Work & Rehabilitation", "Grade": "A"},  # Journal of Cancer Survivorship
        "0003-9993": {"Subject": "Return to Work & Rehabilitation", "Grade": "A"},  # Archives of Physical Medicine and Rehabilitation
        "0269-2155": {"Subject": "Return to Work & Rehabilitation", "Grade": "B"},  # Clinical Rehabilitation
        "0963-8288": {"Subject": "Return to Work & Rehabilitation", "Grade": "B"},  # Disability and Rehabilitation
        "1650-1977": {"Subject": "Return to Work & Rehabilitation", "Grade": "B"},  # Journal of Rehabilitation Medicine
        "0284-186X": {"Subject": "Return to Work & Rehabilitation", "Grade": "B"},  # Acta Oncologica
        "0941-4355": {"Subject": "Return to Work & Rehabilitation", "Grade": "B"},  # Supportive Care in Cancer
        "1057-9249": {"Subject": "Return to Work & Rehabilitation", "Grade": "B"},  # Psycho-Oncology
        "1040-8428": {"Subject": "Return to Work & Rehabilitation", "Grade": "B"},  # Critical Reviews in Oncology/Hematology
        "1051-9815": {"Subject": "Return to Work & Rehabilitation", "Grade": "C"},  # Work

        # --- Climate Change & Worker Health ---
        "1758-678X": {"Subject": "Climate Change & Worker Health", "Grade": "A"},  # Nature Climate Change
        "2542-5196": {"Subject": "Climate Change & Worker Health", "Grade": "A"},  # The Lancet Planetary Health
        "0959-3780": {"Subject": "Climate Change & Worker Health", "Grade": "A"},  # Global Environmental Change
        "0160-4120": {"Subject": "Climate Change & Worker Health", "Grade": "A"},  # Environment International
        "1545-9624": {"Subject": "Climate Change & Worker Health", "Grade": "A"},  # Journal of Occupational and Environmental Hygiene
        "2093-7911": {"Subject": "Climate Change & Worker Health", "Grade": "A"},  # Safety and Health at Work
        "0013-9351": {"Subject": "Climate Change & Worker Health", "Grade": "B"},  # Environmental Research
        "1469-3062": {"Subject": "Climate Change & Worker Health", "Grade": "B"},  # Climate Policy
        "2667-2782": {"Subject": "Climate Change & Worker Health", "Grade": "B"},  # The Journal of Climate Change and Health
        "2332-8940": {"Subject": "Climate Change & Worker Health", "Grade": "B"},  # Temperature  [corrected: top hit was J Low Temperature Physics]
        "2767-3375": {"Subject": "Climate Change & Worker Health", "Grade": "B"},  # PLOS Global Public Health

        # --- Policy, Regulation & Health Systems ---
        "0278-2715": {"Subject": "Policy, Regulation & Health Systems", "Grade": "A"},  # Health Affairs
        "0887-378X": {"Subject": "Policy, Regulation & Health Systems", "Grade": "A"},  # Milbank Quarterly
        "0277-9536": {"Subject": "Policy, Regulation & Health Systems", "Grade": "A"},  # Social Science & Medicine
        "0268-1080": {"Subject": "Policy, Regulation & Health Systems", "Grade": "A"},  # Health Policy and Planning
        "0017-9124": {"Subject": "Policy, Regulation & Health Systems", "Grade": "A"},  # Health Services Research  [corrected: top hit was BMC Health Services Research]
        "2468-2667": {"Subject": "Policy, Regulation & Health Systems", "Grade": "B"},  # The Lancet Public Health
        "0090-0036": {"Subject": "Policy, Regulation & Health Systems", "Grade": "B"},  # American Journal of Public Health
        "0168-8510": {"Subject": "Policy, Regulation & Health Systems", "Grade": "B"},  # Health Policy
        "2213-5383": {"Subject": "Policy, Regulation & Health Systems", "Grade": "B"},  # Journal of Cancer Policy
        "1101-1262": {"Subject": "Policy, Regulation & Health Systems", "Grade": "B"},  # European Journal of Public Health
        "1355-8196": {"Subject": "Policy, Regulation & Health Systems", "Grade": "B"},  # Journal of Health Services Research & Policy
        "0197-5897": {"Subject": "Policy, Regulation & Health Systems", "Grade": "B"},  # Journal of Public Health Policy
        "0925-7535": {"Subject": "Policy, Regulation & Health Systems", "Grade": "B"},  # Safety Science
        "1026-9428": {"Subject": "Policy, Regulation & Health Systems", "Grade": "C"},  # Russian Journal of Occupational Health and Industrial Ecology  [Medicina Truda]
    },
}
