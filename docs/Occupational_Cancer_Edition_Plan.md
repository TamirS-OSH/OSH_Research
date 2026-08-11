# Plan: Occupational Cancer Research Edition (second newsletter)

**Status:** Planned — not yet built.
**Requested by:** a researcher on the IIOSH team, via `וכנסים רשימת_כתבי_עת_למעקב_שבועי_–_גרסה_נקייה.docx` (dated 11 Aug 2026, drafted with Undermind).
**Relationship to existing work:** a second *edition* of the existing newsletter pipeline, not a separate system. See [IIOSH_Newsletter_Pipeline_Context.md](IIOSH_Newsletter_Pipeline_Context.md) for the pipeline this builds on.

---

## 1. Scope — the source document describes three products

The Word file bundles three distinct asks. Only the first is a newsletter; the other two are change-detection scrapers that happen to share a cover page. **Phase 1 is the journals edition only.**

| # | Ask | Source type | Reuse from current pipeline | Status |
|---|---|---|---|---|
| 1 | 64 journals across 5 themes + 21 filter keywords + an author feed | OpenAlex API | ~85% | **This plan** |
| 2 | 7 regulatory bodies (OSHA, NIOSH, ILO, EU Commission/EUR-Lex/EU-OSHA, Israeli MoH, Ministry of Labor, Bituach Leumi) | Government APIs / RSS / scraping | ~0% | Deferred — §10 |
| 3 | 25 conference series watched for *Call for Abstracts / Papers / Sessions / Proposals / Late-Breaking* | Society mailing lists | **No code** | Actionable now — §10 |

Phase ordering follows the source document, which places `מקורות רגולטוריים למעקב נפרד` at the end of the journals material, before section ו.

---

## 2. Settled decisions

| Decision | Resolution | Rationale |
|---|---|---|
| Separate repo or same? | **Same repo**, config-driven editions | A second repo means a second fine-grained PAT and a second Apps Script trigger. The README already flags PAT expiry as a silent-failure risk; doubling it is the dominant long-term cost. |
| Scope of monitoring | **Journals + keywords exactly as the doc specifies**, plus a dedicated author feed (§6) | No topic-wide OpenAlex search beyond her journal list. |
| Language | **Bilingual EN/HE**, same as the IIOSH edition | Consistency with the existing product. |
| Overlap with IIOSH edition | **Accepted, no dedupe** | ~12 journals appear in both lists, but the thematic framing and summaries differ. |
| Tier semantics | **A/B/C is one global scheme** covering journals *and* conferences — see §4 | Defined once in `מטרת הרשימה`, above all sections. |
| "Private" edition | Means **separate audience**, not confidential | Confirmed by the maintainer. No special handling needed for the config or the output — see §9.1. |
| Scheduling | **Third job in the existing workflow**, gated on the IIOSH job + a 300s buffer — see §7 | Sequencing is a guarantee; a timed trigger is only an estimate of runtime. |

---

## 3. Journal list — 64 unique titles

Counts: **31 A** (33 entries less 2 cross-listed), **31 B**, **2 C**.
*Annals of Work Exposures and Health* and *Scandinavian Journal of Work, Environment & Health* appear in both theme א and theme ב; each is configured once.

### א. Lung cancer, occupational exposures, epidemiology (20)
**A:** American Journal of Respiratory and Critical Care Medicine · Environmental Health Perspectives · Cancer Epidemiology, Biomarkers & Prevention · Epidemiology · Occupational and Environmental Medicine · American Journal of Industrial Medicine · Annals of Work Exposures and Health · Journal of Exposure Science & Environmental Epidemiology · Scandinavian Journal of Work, Environment & Health · International Journal of Hygiene and Environmental Health · International Archives of Occupational and Environmental Health · Journal of Occupational and Environmental Medicine · Journal of Occupational Health · Occupational Medicine
**B:** Lung Cancer · Thorax · European Respiratory Journal · International Journal of Cancer · Molecular Oncology · Journal of Occupational Medicine and Toxicology

### ב. Occupation & exposure documentation in medical records (10)
**A:** Journal of the American Medical Informatics Association · Journal of Biomedical Informatics · BMJ Health & Care Informatics · *(+ Annals of Work Exposures and Health, Scandinavian Journal of Work, Environment & Health — cross-listed)*
**B:** International Journal of Medical Informatics · JMIR Medical Informatics · Implementation Science · Learning Health Systems · International Journal of Population Data Science

### ג. Return to work, occupational rehabilitation, cancer survivorship (11)
**A:** Journal of Occupational Rehabilitation · Journal of Cancer Survivorship · Archives of Physical Medicine and Rehabilitation
**B:** Clinical Rehabilitation · Disability and Rehabilitation · Journal of Rehabilitation Medicine · Acta Oncologica · Supportive Care in Cancer · Psycho-Oncology · Critical Reviews in Oncology/Hematology
**C:** WORK

### ד. Climate change and worker health (11)
**A:** Nature Climate Change · The Lancet Planetary Health · Global Environmental Change · Environment International · Journal of Occupational and Environmental Hygiene · Safety and Health at Work
**B:** Environmental Research · Climate Policy · The Journal of Climate Change and Health · Temperature · PLOS Global Public Health

### ה. Policy, regulation, health systems (14)
**A:** Health Affairs · Milbank Quarterly · Social Science & Medicine · Health Policy and Planning · Health Services Research
**B:** The Lancet Public Health · American Journal of Public Health · Health Policy · Journal of Cancer Policy · European Journal of Public Health · Journal of Health Services Research & Policy · Journal of Public Health Policy · Safety Science
**C:** Medicina Truda i Promyshlennaya Ekologiya

---

## 4. Tier model (A/B/C)

Defined once in `מטרת הרשימה`, above every section, and applied to both journals and conferences. Cadence is part of the definition, not a separate rule:

- **A** — `ליבת המעקב השבועי` — the core of *weekly* monitoring; direct, high relevance.
- **B** — `מעקב ממוקד` — important journals, partial match or broader scope.
- **C** — `כדאי לבדוק תקופתית או כאשר מתבצע חיפוש ממוקד` — explicitly **not** weekly; periodic or on-demand.

| Tier | Journals (this plan) | Conferences (deferred) |
|---|---|---|
| A | Weekly, ranked first | Site check every 2 weeks |
| B | Weekly, ranked below A | Site check monthly |
| C | Excluded from the weekly run; configured for on-demand use | *(unused — no conference is graded C)* |

The separate `כלל מעקב תפעולי` rule at the end of section ו (A biweekly, B monthly) does **not** redefine the tiers — it applies them to conference websites, which have their own intervals.

**Selection rule for journals:** query A and B together each week, rank A first, let the per-theme cap fill A-first. The doc calls B `כתבי־עת חשובים` — important, not backup — and the risk of B's broader scope is already handled by keyword filtering (§5): a *Lancet Public Health* paper only surfaces if it passes the filter, and if it does it is genuinely relevant.

> This differs from the existing IIOSH edition, which uses a thin-domain fallback ([`FALLBACK_THRESHOLD`](../newsletter/newsletter.py#L252)) to widen from Q1 into Q1/Q2+Q2. Both strategies must coexist — see §8.

---

## 5. Keyword filtering — the main new capability

The current pipeline does **no** relevance filtering. [`gather_candidates`](../newsletter/newsletter.py#L255) takes the newest works per ISSN and never inspects the topic. That is fine for *Scandinavian Journal of Work, Environment & Health*, where everything is on-topic. It fails on this list, which includes *Nature Climate Change*, *Health Affairs*, *Social Science & Medicine*, *The Lancet Public Health* and *Environment International* — high-volume journals publishing almost nothing about occupational lung cancer. Without filtering the edition delivers five irrelevant health-policy papers a week.

The 21 keyword lines under `מילות סינון לאלגוריתם`:

```
occupational lung cancer
lung cancer in never-smokers
low smoking exposure and occupational carcinogens
combined, cumulative and sequential occupational exposures
asbestos, silica, diesel exhaust, PAH, nickel, chromium and welding fumes
joint effects, additive interaction and multiplicative interaction
exposure–response, dose–response and cumulative exposure
latency, time since exposure and time since last exposure
occupational cancer surveillance after exposure
occupational disease notification, compensation and recognition
exposure registries, record retention and administrative data linkage
industry and occupation in electronic health records
Occupational Data for Health, EHR, coding and NLP
job-exposure matrices and occupational exposome
return to work after cancer
work ability, work retention and workplace accommodations
occupational rehabilitation and disability management
climate change and occupational heat stress
wildfire smoke, air pollution, UV and extreme weather at work
occupational exposure limits and regulatory policy
implementation of occupational health policy
```

### Design — as built

Scoring runs **locally on title + abstract, before any Gemini call** — deterministic, debuggable, and it *saves* quota by never summarizing a paper that fails the filter.

1. **Term expansion.** Several lines are comma-lists, not single phrases — `asbestos, silica, diesel exhaust, PAH, nickel, chromium and welding fumes` is seven terms. Expansion was done **once, by hand, and stored explicitly in the config**, with the original 21 lines kept as a comment for traceability. Auto-splitting at runtime was rejected: it is a silent-failure path when a phrase splits wrongly. 63 terms resulted.
2. **Normalization.** Lowercase; collapse en-dashes and hyphens to spaces (the doc uses `exposure–response` with an en-dash, papers use `exposure-response`); strip punctuation. This also makes `never-smokers` / `never smokers` match.
3. **Two term classes, not one flat threshold.** See below.
4. **Calibration logging.** Every candidate is logged with its score, core count and matched terms — rejects included — so the rule can be retuned from observed output.
5. **Empty themes** are omitted from the newsletter; the existing `if not selected: continue` already handles this.

### The rule, and how it got here

Three iterations, each driven by measurement rather than intuition. Tested against **90 days of real abstracts** across deliberately broad journals and focused ones, plus the first live run's actual week.

| Rule | Broad | Focused | Verdict |
|---|---|---|---|
| `score >= 1` | 14% | 62% | Far too loose |
| `score >= 2` | 2% | 13% | Too tight |
| `>=1 core, or >=2 total` | 3.0% | 55% | Shipped, then failed live |
| **`>=1 occupational anchor` AND (`>=1 core` or `>=2 total`)** | **1.3%** | **51%** | **In use** |

**Iteration 1 → 2.** A flat `>= 1` passed 47% of *Nature Climate Change*, including a paper on *marine species conservation* matched via "climate change". Raising to `>= 2` fixed that but discarded obviously relevant work — *"Reducing respirable silica exposure among brick kiln workers"* scores 1. So terms were split into **core** (inherently occupational; one match suffices) and **context** (common outside her field; needs two).

**Iteration 2 → 3, from the first live run.** That rule selected 5 articles, of which two were wrong and three obvious hits were missed entirely. Both defects were real:

- *Vocabulary gaps, not rule failure.* `occupational exposure` was a term but plain `occupational health` was not, so *"Occupational health risks among live-in caregivers"* scored **zero**. Same for `pneumoconiosis`, `pesticide`, `mesothelioma`, `silicosis`. Adding 15 missing anchors lifted focused-journal recall from 43% to 55% at no cost to broad journals.
- *Topic terms alone must never admit.* The run selected *"Developing a strategic plan for a climate-resilient health system"* — no work content whatsoever — on `climate change` + `air pollution`. Her subject is not climate, or policy, or oncology; it is **occupational** climate, policy and oncology.

So a **subject gate** now runs before the topic rule: an article must match one of 21 occupational anchors (`occupational`, `worker`, `workplace`, `shift work`, `return to work`…) or it is rejected outright, however well it scores on topic. Effect: *Nature Climate Change* 7% → 0%, *PLOS Global Public Health* 4% → 0%, *Health Affairs* 2% → 0%, for four points of recall on the focused journals.

On the live run's week this keeps exactly the 8 relevant articles and drops both bad ones.

> **`workforce` is deliberately not an anchor.** In health-policy writing it means hospital staffing levels — it was the single anchor that let the climate-resilient-health-system paper through on a first attempt at the gate.

> A context-only path survives (`>=2 context terms` with an occupational anchor) so a paper phrased as "workers · heat stress · climate change", without the literal term `occupational heat`, is still caught.

---

## 6. Author feed — tracked researchers

A standalone section reviewing **new publications by a specific researcher**, independent of the journal hierarchy, the A/B/C tiers, and the keyword filter. First tracked author: **Ann Olsson** (IARC/WHO).

### Why this is separate from the journal list

The doc's line `יש לוודא שהכתבי־עת הבאים כלולים במעקב` asks that the journals Olsson publishes in be present in the monitoring list — and all 8 are, via §3: AJRCCM, Epidemiology, CEBP, EHP, OEM, JOEM (A) · Molecular Oncology (B) · Medicina Truda i Promyshlennaya Ekologiya (C).

The author feed is an **additional, orthogonal channel**: it catches everything she publishes, including in journals nowhere on the list. It also dissolves what looked like an internal contradiction in the doc — *Medicina Truda* stays tier C and outside the weekly journal run, but if Olsson publishes there the author feed surfaces it regardless.

### Design

- **Author resolved — `A5064971907`.** Not by name search: "Ann Olsson" returns many OpenAlex candidates. Resolved instead from two DOIs in the doc's own reference list — `10.1289/EHP13380` (SYNERGY, *EHP* 2024) and `10.31089/1026-9428-2021-61-3-140-154` — which both point to the same author, ORCID `0000-0001-6498-2259`, affiliated to *Centre international de recherche sur le cancer* (IARC under its French name). 226 works.
- **Known caveat: the cluster is contaminated, historically.** Its oldest entries are 1930s–50s agronomy (*"Supplementary sowing in leys"*, pea-seed maturity) and 1980s Epstein–Barr virus genetics — other people named Olsson merged into one author record. All output in the last year is genuinely hers, so a rolling window is safe. **Never use this ID for a historical query.**
- **Query:** works filtered by `author.id` and publication date.
- **Type filter is essential.** Of 14 records in a sample 365-day window, only **5 were real articles**; the rest were conference abstracts and AACR-style *"Data from…"* / *"Supplementary Figure from…"* companion stubs. Restricted to `type:article` with `has_abstract:true`.
- **Window: 60 days, not 7.** At ~5 articles a year, a weekly window would be empty essentially always. The window governs how much OpenAlex **indexing lag** is tolerated, not how much she sees — dedupe means nothing is ever shown twice, so the extra reach is free. Expect the section to be legitimately absent for months at a stretch: as of 11 Aug 2026 her most recent article was 1 Apr 2026.
- **Dedupe is mandatory**, on both work ID **and normalized title** — the same editorial appears under two IDs (2026-01-28 and 2026-04-01), which an ID-only seen-set would let through twice. Persisted to `state/occ_cancer_seen.json` and committed back by the workflow. Anything over the per-section cap is left unmarked so it surfaces next run rather than being silently dropped.
- **No keyword filter, no tier ranking.** She wants everything Olsson publishes, and the venue may not be on the journal list at all — which is the point of the feed.
- **Generalized config.** A `tracked_authors` list rather than an Olsson special case; "track this researcher" is an obviously repeatable request at a research institute.
- **Cost:** typically 0–3 Gemini calls per week, often zero.

---

## 7. Scheduling

A third job in [`weekly_update.yml`](../.github/workflows/weekly_update.yml), dependent on the existing newsletter job.

```yaml
send-newsletter-occ:
  needs: send-newsletter
  if: always()          # runs even if the IIOSH edition fails — ordering without coupling
  runs-on: ubuntu-latest
  steps:
    - name: Cool-off before second edition
      run: sleep 300
    # ... checkout, setup-python, install, run with --edition occ_cancer
```

**Why `needs:` and not a second timed trigger.** GitHub Actions runs jobs in parallel by default — `update-dashboard` and `send-newsletter` already do. Without `needs:`, both editions would hit one `GEMINI_API_KEY` concurrently at ~10 RPM, against a key the [12-second sleeps](../newsletter/newsletter.py#L345) hold at ~5. A *timed* trigger is worse than useless here: it estimates the first run's duration, and the IIOSH run floors at ~11 minutes and realistically takes 12–18, so a short offset fires into the middle of it and produces exactly the concurrency it was meant to avoid. `needs:` is a fact about completion, not an estimate.

**What the 300s buffer does and doesn't do.** It adds margin for any sliding-window quota accounting on top of the natural 40–90s runner teardown/spin-up/`pip install` gap. It does **not** help with a daily-quota (RPD) limit — same day, same bucket. If RPD ever becomes binding, the fix is a separate workflow on a different day, which is a config change once the code is edition-parameterized.

### Budget

| | ISSN fetches | Article summaries | Domain summaries | Floor | Realistic |
|---|---|---|---|---|---|
| IIOSH edition | 24 × 3s = 72s | ≤40 × 12s = 480s | 8 × 12s = 96s | ~11 min | 12–18 min |
| Occ-cancer edition | 62 × 3s = 186s | ≤25 × 12s = 300s (+0–3 author-feed) | 5 × 12s = 60s | ~9 min | 10–14 min |

Total workflow with the 300s buffer: **~27–37 min**, far inside the 6-hour job limit. Gemini load rises from ≤49 to ≤83 calls/week, none concurrent, each spaced ≥12s.

---

## 8. Architecture — config-driven editions

The pipeline is already ~90% pure functions; all edition-specific state sits in module-level constants at the top of [`newsletter.py`](../newsletter/newsletter.py). The refactor extracts that config and leaves the logic untouched.

```
newsletter/
  newsletter.py          # edition-agnostic core; invoked as --edition <slug>
  editions/
    iiosh.py             # existing 39 journals, Q1-fallback selection
    occ_cancer.py        # 64 journals + keywords + tracked authors
state/
  occ_cancer_seen.json   # author-feed dedupe (§6)
```

### Edition config schema

| Key | IIOSH | Occ-cancer |
|---|---|---|
| `slug` | `iiosh` | `occ_cancer` |
| `journals` | 39 × `{Subject, Grade}` | 64 × `{Subject, Tier}` |
| `selection` | `{mode: "fallback", primary: ["Q1"], fallback: ["Q1/Q2","Q2"], threshold: 2}` | `{mode: "ranked", include: ["A","B"], rank_order: ["A","B"]}` |
| `keywords` | *(empty — no filtering)* | expanded term list (§5) |
| `keyword_min_score` | — | 1, then tuned |
| `tracked_authors` | *(empty)* | `[{name: "Ann Olsson", openalex_id: …, window_days: 30}]` |
| `max_articles_per_subject` | 5 | 5 |
| `publish_to_pages` | `true` | see §9.1 |
| `recipient_env` | `RECIPIENT_LIST` | `RECIPIENT_LIST_OCC` (new secret) |
| `branding` | existing | distinct title/accent |

Two selection strategies coexist deliberately: the IIOSH edition's behavior must not change. Absent `keywords` and `tracked_authors`, both new stages are no-ops, so the IIOSH path is untouched by §5 and §6.

**Verification gate:** the refactor is behaviour-preserving for the IIOSH edition. Run it before and after against the same week and diff the generated HTML byte-for-byte. [IIOSH_Newsletter_Pipeline_Context.md](IIOSH_Newsletter_Pipeline_Context.md) requires the retry logic, `gemini-3.1-flash-lite` mapping, per-subject caps and exact inline CSS be preserved — an extract-config refactor preserves all four.

---

## 9. Open items

### 9.1 RESOLVED — publishing to GitHub Pages
Email-only was originally chosen to keep the edition confidential; "private" turned out to mean *separate audience*, so that rationale fell away. This edition **publishes to Pages under `/occ`**, with file prefix `OccCancer_Research_Update_`, so the two editions never contend for `index.html` (the IIOSH [prep step](../.github/workflows/weekly_update.yml#L67) globs its own prefix and uses `keep_files: true`).

### 9.2 RESOLVED — ISSN resolution
All 64 names resolved against OpenAlex `/sources`; 58 matched exactly. **Six did not, and in every case the naive top hit was a different real journal** — exactly the silent failure this step existed to catch:

| Doc name | Wrong top hit | Verified |
|---|---|---|
| Epidemiology | `0002-9262` *American Journal of Epidemiology* | `1044-3983` |
| Journal of Occupational Health | `1076-8998` *J. Occupational Health **Psychology*** | `1341-9145` |
| Int. J. of Population Data Science | *no result* | `2399-4908` — actual title is "**for**", not "of" |
| Temperature | `0022-2291` *J. Low **Temperature** Physics* | `2332-8940` |
| Health Services Research | `1472-6963` ***BMC** Health Services Research* | `0017-9124` |
| Medicina Truda i Promyshlennaya Ekologiya | *no result* | `1026-9428` — indexed under its English title |

Each correction was confirmed by direct ISSN lookup returning the right title and publisher. 64 distinct ISSN-Ls, no duplicates, no gaps.

### 9.3 RESOLVED — Ann Olsson author ID
`A5064971907`, cross-verified from two DOIs. See §6 for the contamination and record-type caveats that came out of the check.

### 9.4 Gemini quota headroom
Worth checking the actual console figures for the account rather than assuming; ≤83 calls/week spaced ≥12s should be comfortable, but RPD is the one limit sequencing cannot help.

### 9.5 Keyword rule — still needs her judgement
The rule has now survived one live run and been corrected by it (§5), but calibration against historical abstracts is not the same as her reading the output. Every candidate is logged with `score`, `core`, `occ` and matched terms — an `occ=0` on a dropped row means it failed the subject gate rather than the topic rule, which makes the two failure modes distinguishable in the log.

Open questions for the first review with her:
- **Shift work.** Added to core because IARC classifies circadian-disrupting shift work as probably carcinogenic. Two of the live run's articles came in this way (*"Night work, sleep disruption and long-COVID"*, *"Genomic Landscape … Night Shift Work"*). Relevant, or noise?
- **Non-cancer occupational outcomes.** *"Occupational exposure to pesticides increases the risk of ALS"* and *"Job strain and ischemic heart disease"* both pass. Squarely occupational, but not cancer. In or out?
- **Themes ב and ה produced zero** in the live run. Partly a thin week, but worth watching whether the informatics and policy vocabularies are too narrow.

### 9.6 `RECIPIENT_LIST_OCC` secret
Must be created in repo settings before the first run. Absent it, the pipeline generates and publishes the newsletter but skips the send with a logged warning rather than failing.

---

## 10. Deferred — phases 2 and 3

Neither reuses the OpenAlex pipeline. The unit of interest is an **event** ("a rule was published", "a call opened") rather than a record, so there is no stable key like an ISSN and nothing to query.

Phase 2 solves that with code and persistent state. **Phase 3 escapes it entirely** by using the societies' own mailing lists as the event source — see below.

### Why this is a different problem shape from journals
- **Detecting a state change, not fetching records.** No registry, no stable identifier.
- **Low yield by design.** 25 conferences × ~1 call/year ≈ one event a fortnight. Most checks find nothing, and that is correct behaviour rather than a fault.
- **URLs rot annually.** `wclc2026…` → `wclc2027…`. The doc already compensates by linking *society* pages rather than single-conference pages.
- **Every source is bespoke** — different layout per site, redesigned every few years.

### Phase 2 — Regulatory tracker
Sources: OSHA · NIOSH · ILO · European Commission / EUR-Lex / EU-OSHA · Israeli Ministry of Health · Israeli Ministry of Labor · Bituach Leumi.

Sequenced ahead of conferences because real APIs exist here, event frequency is higher, and it feeds theme ה directly.

- **US — strongest.** The Federal Register offers a free JSON API filterable by agency, date and search term; both OSHA and NIOSH rulemaking flows through it. Highest-value source in the document, and structured data rather than scraping.
- **EU — workable.** EUR-Lex exposes machine-readable access; EU-OSHA publishes feeds.
- **Israel — the hard part.** MoH, Ministry of Labor and Bituach Leumi will likely need real scraping; gov.il is JS-heavy and inconsistent about feeds. Content is Hebrew, so the §5 keyword list does not transfer and needs a Hebrew equivalent.

**First step is a discovery pass, not a build.** Feed endpoints rot, so for each of the 7 bodies establish what machine-readable surface exists *today* and produce a source-inventory table: source · access type (API / RSS / HTML) · auth required · language · confidence. Design follows that table.

Machinery this phase needs:
- **State store** — `last_seen` / `last_checked` per source, persisted in the repo, reusing what §6 builds for the author feed.
- **Cadence in the state file, not in cron.** GitHub's `schedule:` does not fire for this repo — the entire reason the Apps Script trigger exists. Run the watcher weekly off the **existing single trigger** and skip any source whose `last_checked` says it isn't due. Cadence becomes code: no new triggers, no second PAT.
- **LLM extraction with provenance.** Where a page must be interpreted, Gemini (already wired up) reads it and returns structured fields. Two hard rules: the model must **quote the source sentence** a date or determination came from, and the digest always links the source. The digest reports the model's reading; it never asserts a fact on its own authority.

### Phase 3 — Conference calls for abstracts (§ו) — **zero code**

The doc names the right channel itself: `להירשם לרשימות תפוצה או לעדכוני הכנס כאשר אפשרות זו קיימת`. Societies email their members the moment a call opens — authoritative, deadline included, no inference, free. That is precisely the event she wants, so there is nothing to scrape and nothing to classify.

Implementation is Gmail configuration on `iiosh.news@gmail.com`, not a pipeline:

1. **Subscribe** the account to all 25 society lists (table below).
2. **Verify her address** as a forwarding address — Settings → Forwarding and POP/IMAP → Add a forwarding address. She clicks one confirmation link; that is the only time she is in the loop.
3. **Filter A — forward the calls.** Match on the doc's trigger phrases rather than senders: `"call for abstracts" OR "call for papers" OR "call for sessions" OR "call for proposals" OR "late-breaking"`. Action: *Forward to* her address. Sender-based rules can't be written up front — the sending domains aren't known until mail arrives, and societies usually send via Mailchimp/Cvent/Informz, so the From domain won't match the society's website anyway.
4. **Filter B — quarantine the rest.** Match the society senders once known; apply a `Conference-lists` label with *Skip Inbox*.

**Deliberately biased toward over-forwarding.** A false positive costs her a glance; a false negative costs her a submission window. Start broad, tighten only once the real senders are visible.

**Why Filter B matters.** Sharing the newsletter's sending account means 25 lists' worth of mail landing where delivery failures and replies also land — and a buried bounce is how you stop noticing that a recipient's address died. Skip-Inbox labelling keeps the main Inbox operationally readable, which is what makes sharing the account safe rather than merely convenient.

**Why forward rather than fold into the weekly digest.** Deadlines are time-sensitive; a batched digest could sit on a call for six days. Push immediately. Gmail also keeps the original, so the IIOSH account accumulates a searchable archive for free.

#### Practical notes for the signup pass
- Some lists are gated behind society membership — expect roughly 15–20 of 25 to be openly subscribable; the rest may need IIOSH membership or her own subscription.
- Most use double opt-in, so whoever runs the signups needs live access to the mailbox *during* the session.
- EPICOH is a scientific committee within ICOH, so one subscription may cover both.
- ILO appears in both phase 2 (regulatory) and phase 3 (World Congress) — one subscription, two purposes.
- Handing the address to 25 organisations brings general marketing mail too; Filter B absorbs it.
- Public CFP aggregators (WikiCFP and similar) skew heavily to computer science and are thin for occupational health and epidemiology — spot-check at most, don't build on them.

#### Residual gap
For any society with no usable list, fall back to a **fetch + LLM extraction** sweep on its site — *not* page diffing, which reports "something changed" and buries the signal under cookie banners and sponsor carousels, requiring ~25 hand-maintained CSS selectors. Some sites are JS-rendered and return an empty shell to `requests`; log which yield no usable text and add a headless browser only for that handful. Decide this **after** observing what the lists actually deliver over 2–3 months, not before.

#### Subscription tracker

| Conference | Tier | Organising body | List? | Subscribed |
|---|---|---|---|---|
| ICOH International Congress on Occupational Health | A | ICOH | ☐ | ☐ |
| EPICOH International Symposium | A | ICOH (scientific committee) | ☐ | ☐ |
| ISEE Annual Conference | A | Int'l Society for Environmental Epidemiology | ☐ | ☐ |
| ISES Annual Meeting | A | Int'l Society of Exposure Science | ☐ | ☐ |
| IOHA International Scientific Conference | A | Int'l Occupational Hygiene Association | ☐ | ☐ |
| AIHA Connect / AIHce EXP | B | American Industrial Hygiene Association | ☐ | ☐ |
| BOHS Workplace Health Protection Conference | B | British Occupational Hygiene Society | ☐ | ☐ |
| IASLC World Conference on Lung Cancer | A | IASLC | ☐ | ☐ |
| ATS International Conference | A | American Thoracic Society | ☐ | ☐ |
| ERS International Congress | A | European Respiratory Society | ☐ | ☐ |
| UICC World Cancer Congress | B | Union for International Cancer Control | ☐ | ☐ |
| AMIA Annual Symposium | A | American Medical Informatics Association | ☐ | ☐ |
| MedInfo World Congress | A | IMIA | ☐ | ☐ |
| Global Implementation Conference | B | Global Implementation Society | ☐ | ☐ |
| Advances in Learning Health System Sciences | B | LHS Sciences Conference organisers | ☐ | ☐ |
| ISPRM World Congress | A | Int'l Society of Physical & Rehabilitation Medicine | ☐ | ☐ |
| ACRM Annual Conference & EXPO | A | American Congress of Rehabilitation Medicine | ☐ | ☐ |
| AAPM&R Annual Assembly | B | American Academy of Physical Medicine & Rehabilitation | ☐ | ☐ |
| Work, Stress, and Health Conference | B | SOHP (with APA / NIOSH) | ☐ | ☐ |
| Planetary Health Annual Meeting | A | Planetary Health Alliance | ☐ | ☐ |
| World Congress on Public Health | A | WFPHA | ☐ | ☐ |
| AcademyHealth Annual Research Meeting | A | AcademyHealth | ☐ | ☐ |
| APHA Annual Meeting and Expo | B | American Public Health Association | ☐ | ☐ |
| WHO Global Conferences on Health and Climate Change | B | WHO | ☐ | ☐ |
| World Congress on Safety and Health at Work | B | ILO (with ISSA) | ☐ | ☐ |

> **Document the filters when they are created.** These live outside the repo, exactly like the Apps Script trigger the README documents for the same reason. Undocumented Gmail filters are invisible: if one is edited or breaks, nobody will know why forwarding stopped. Record the forwarding address and both filter definitions here once configured.

### Suggested overall order
Finish phase 1 · run the conference signups in parallel right away (no code, immediate value, independent of everything else) · regulatory discovery pass, then build outward from the Federal Register · revisit the conference residual gap only after 2–3 months of observing what the lists deliver.

---

## 11. Build order

1. ~~Resolve 64 journal names → ISSNs; hand-verify.~~ **Done** — §9.2.
2. ~~Resolve Ann Olsson's OpenAlex Author ID via DOI.~~ **Done** — `A5064971907`, §9.3.
3. ~~Extract the edition config from `newsletter.py`; verify IIOSH output is byte-identical.~~ **Done** — verified by `tests/verify_iiosh_identity.py`, page and email HTML both identical.
4. ~~Add keyword scoring as an optional, no-op-when-absent stage.~~ **Done** — two-class rule, §5.
5. ~~Add the author feed with its persisted seen-set.~~ **Done** — §6.
6. ~~Add the `occ_cancer` edition config.~~ **Done.** The `RECIPIENT_LIST_OCC` secret is still outstanding — §9.6.
7. ~~Add the third workflow job with `needs:` + `sleep 300`.~~ **Done.**
8. **Next:** create the secret, then trigger one manual run and read the `[KW]` / `[AUTHOR]` / `[DIAG]` lines before letting it go out weekly.
9. Run 2–3 weeks with full candidate logging; review the rule with the researcher — §9.5.
10. Update the README once it ships (new edition, `RECIPIENT_LIST_OCC`, `/occ` Pages path, `state/` directory).

### Verification status

| Check | Result |
|---|---|
| All modified Python compiles | pass |
| IIOSH page HTML unchanged | **byte-identical** (11,981 chars) |
| IIOSH email HTML unchanged | **byte-identical** (2,896 chars) |
| occ_cancer: 64 journals, 5 themes, 62 queried (31 A + 31 B) | pass |
| occ_cancer: tier C excluded from the weekly run | pass |
| occ_cancer: A ranked before B in every theme | pass |
| Relevance rule keeps/drops the expected cases | pass |
| Tracked-author query against live OpenAlex | pass |
| Seen-state save/load round trip | pass |
| Rendering: own prefix, own branding, no IIOSH leakage, no dashboard button | pass |

Re-run the identity check at any time. It defaults to the pre-refactor baseline
(`8fc7c99`), which is the only comparison that proves anything; pass a different
ref to override, and it refuses rather than silently comparing a file to itself:

```
python tests/verify_iiosh_identity.py
```
