# Handover Walkthrough

How to pass this automation to a new maintainer so it keeps running after the departing maintainer's work email and personal Google account are deleted.

**Who does what:** **Departing** = the current maintainer, who still has every login. **Successor** = the new maintainer. Several steps need both people at the same time (one has the old 2FA device, the other sets up the new one). Plan a joint session of about three hours, or two shorter ones.

> This repository is public. Never write passwords, tokens, recovery codes or the recipient list into this file or anywhere else in the repo.

## Progress

**As of 2026-10-04 (evening):** Parts 1–4 have been worked through, and the account is renamed to `iiosh-research` (lowercase). **Next: Part 5 (weekly trigger), not started.** Open items, in order:

1. **Done:** the old trigger's URL reads `iiosh-research` (confirmed 2026-10-04). **Don't press Run in the old script.** With `triggerWeeklyNewsletter` selected it's a real send, and with `setGithubToken` selected it erases the saved token, which stops the Sunday run.
2. **No dry run has run since the rename and the Part 3 variables.** Run one ([Part 10](#part-10--verify)) and check both jobs are green.
3. **Done, not yet tested:** the Google login in Part 3, step 4 was corrected to `iiosh-research/OSH_Research` in lowercase (2026-10-04). If the dry run's dashboard job fails at *Authenticate to Google Cloud*, re-check the attribute condition and the service account's *Workload Identity User* entry.
4. **Check which way the Sheet moved to `iiosh.news`** (Part 6). If the old `journal-dashboard-bot@research-497406…` service account appears in its Share dialog, ownership was transferred (Plan A). If not, it's a copy (Plan B), and the job and Looker are still using the old Sheet. Then do Part 7 to match.

---

## The idea in one paragraph

Most of the automation already runs on two accounts that were created just for it: the GitHub account **`TamirS-OSH`**, which is renamed to **`IIOSH-Research`** in Part 4, and the Gmail account **`iiosh.news@gmail.com`**. They are handed over by changing their email, password and 2FA to the successor. Everything else currently lives on the departing maintainer's **personal** Google account: the Google Cloud project the dashboard job signs in through, the Sheet, the Looker report, the weekly trigger, and possibly the Gemini key. Those are moved onto, or rebuilt in, `iiosh.news@gmail.com`. After that, nothing depends on any one person, and the next handover only repeats the account steps.

## What depends on what

| Piece | Where it lives now | Moves to | Part |
|---|---|---|---|
| Repo, Actions, secrets, GitHub Pages | GitHub account `TamirS-OSH` | Same account, renamed `IIOSH-Research`, new owner | 1, 4 |
| Newsletter sender (Gmail SMTP) | `iiosh.news@gmail.com` | Same account, new owner | 2 |
| Dashboard job's Google login (Cloud project `research-497406`) | Personal Google account, inside an institute Cloud organization | Rebuilt in a new project owned by `iiosh.news@gmail.com` | 3 |
| Weekly trigger (Apps Script "IIOSH Weekly Trigger") | Personal Google account | Recreated in `iiosh.news@gmail.com` | 5 |
| Google Sheet "IIOSH Dashboard Data" | Personal Google account | `iiosh.news@gmail.com` | 6 |
| Looker Studio report + data sources | Personal Google account | `iiosh.news@gmail.com` | 7 |
| Gemini API key | Check (probably personal account) | `iiosh.news@gmail.com` | 8 |
| `newsletter/recipients.txt`, the two journal-list `.docx` files | Departing maintainer's computer only (git-ignored) | Handed over directly | 9 |

**Order matters for Parts 3–5.** Part 3 (new Google Cloud project) must be finished and tested before Part 4 (rename), and Part 5 (trigger) should follow Part 4 in the same sitting. If Parts 4 and 5 must be split, Part 4 says what to do in between.

## When to do it

- **Midweek, never Saturday night or Sunday.** The trigger fires Sunday morning, Israel time.
- **At least two weeks before the departing maintainer's last day.** This leaves room for one real Sunday run under the new setup (Part 10) while the old accounts still exist as a fallback.
- **Before starting, decide where passwords and recovery codes go.** The best place is the institute's password manager or IT, so the next handover doesn't depend on one person either.

---

## Part 1 — GitHub account: email, password, 2FA

**Who: both, together.**

1. **Email: use `iiosh.news@gmail.com`.** Whoever holds the Gmail account can then also recover the GitHub account, and GitHub's alerts for failed runs reach an inbox that is forwarded to the maintainer (Part 2, step 5). The trigger starts runs as this account, so those alerts go to its email. Go to github.com → Settings → Emails, then:
   - [ ] Add `iiosh.news@gmail.com` and verify it from that inbox.
   - [ ] Set it as **Primary email address**.
   - [ ] Remove the departing maintainer's work address. Past commits stay; they just stop linking to the avatar.
   - [ ] Settings → **Notifications** → **Default notification email**: choose `iiosh.news@gmail.com`. This is set separately from the primary email.
2. **Password.** Settings → Password and authentication:
   - [ ] Change the password and store the new one with IT.
3. **Two-factor authentication. Do this carefully: without 2FA access, GitHub support will not restore the account.** Under Settings → Password and authentication → Two-factor methods:
   - [ ] **Authenticator app → Edit**: the successor scans the new QR code with their own app and enters a code.
   - [ ] Remove the departing maintainer's **passkeys**, **security keys** and **SMS number**, if any. If GitHub Mobile is set up on the old phone, sign out of it there.
   - [ ] **Recovery codes → Regenerate**, and store them with IT. The old codes stop working.
   - [ ] Successor: sign out, then sign back in using only the new 2FA, to prove it works.
4. **Remove the departing maintainer's access:**
   - [ ] Settings → **Sessions**: revoke every session except the successor's.
   - [ ] Settings → **SSH and GPG keys**: delete keys belonging to the old computer.
   - [ ] Settings → **Applications → Authorized OAuth Apps**: revoke what the old computer used (VS Code, Git Credential Manager and similar).
   - [ ] Do **not** delete any token under Developer settings → Personal access tokens yet. The current weekly trigger uses one until Part 5 is done.
5. **Display name:** Settings → Public profile → Name (currently "IIOSH"). Change it freely; nothing depends on it.

Nothing in Part 1 affects the weekly run.

## Part 2 — Gmail account `iiosh.news@gmail.com`

**Who: both, together.** Sign in on the **successor's** device while the departing maintainer can still approve the new sign-in on the old phone.

1. **Recovery details.** myaccount.google.com → Security, then:
   - [ ] **Recovery email**: change it to the successor's or the shared mailbox.
   - [ ] **Recovery phone**: change it to the successor's.
2. **2-Step Verification. Do not turn it off, not even briefly.** Turning it off deletes every app password, and turning it back on doesn't restore them. If that happens, turn it back on and do step 4.
   - [ ] Add the successor's authenticator app or phone, then remove the old phone and old passkeys.
   - [ ] **Backup codes → Get new codes**, and store them with IT.
3. **Password — after this step the newsletter cannot send email until step 4 is done.**
   - [ ] Change the password. **Google revokes every app password when the password changes.**
4. **New app password, immediately:**
   - [ ] myaccount.google.com/apppasswords → create one named e.g. `GitHub newsletter`, and copy the 16 characters.
   - [ ] On GitHub, go to repo → Settings → Secrets and variables → Actions → **`GMAIL_APP_PASSWORD` → Update**, paste it, and save. Don't store it anywhere else; it can always be regenerated.
5. **Forwarding.** Security alerts, the trigger's failure emails and GitHub's failed-run alerts all arrive in this inbox, so someone must actually see them.
   - [ ] Gmail → Settings → See all settings → **Forwarding and POP/IMAP** → add the successor's address, confirm the code sent there, and choose "Forward a copy".
6. **Test the sender:**
   - [ ] Run a dry run (see [Part 10](#part-10--verify)). The email should arrive from `iiosh.news@gmail.com`.

## Part 3 — New Google Cloud project for the dashboard job

**Who: successor (or departing), signed in as `iiosh.news@gmail.com`. The departing maintainer shares the Sheet in step 5.**

**Why rebuild instead of transfer:** the dashboard job writes to the Sheet by signing in to Google through the Cloud project `research-497406`. That project sits under the departing maintainer's personal Google account, inside an institute Google Cloud organization. A project can't be moved out of an organization, and such organizations usually refuse gmail.com members. So the same small setup is rebuilt in a new project owned by `iiosh.news@gmail.com`: one service account plus one "trust GitHub" setting (Workload Identity Federation). It's free, needs no billing, and takes about 20 minutes. The old project can then disappear with the personal account without affecting anything.

The workflow reads the project details from two **repository variables** (step 6). Until those are set, it keeps using the old project, so nothing changes until the new one is ready and tested.

1. **Create the project.**
   - [ ] Go to console.cloud.google.com, signed in as `iiosh.news@gmail.com`. Accept the terms the first time; skip any free-trial or billing offer, since it's not needed.
   - [ ] Project picker (top bar) → **New project** → name `iiosh-automation` → Location: **No organization** → Create. Select the new project.
   - [ ] Home → **Dashboard** → *Project info* card: write down the **Project ID** (e.g. `iiosh-automation-123456`) and the **Project number** (12 digits).
2. **Turn on the APIs it uses.** APIs & Services → **Library**; search for and **Enable** each of:
   - [ ] IAM Service Account Credentials API
   - [ ] Security Token Service API
   - [ ] Google Sheets API
   - [ ] Google Drive API (the job finds the Sheet by name through Drive)
3. **Service account.** IAM & Admin → **Service Accounts** → **Create service account**:
   - [ ] Name `journal-dashboard-bot` → Create and continue → skip the role and user steps → **Done**.
   - [ ] Note its email: `journal-dashboard-bot@<PROJECT_ID>.iam.gserviceaccount.com`.
4. **Let GitHub sign in as it (Workload Identity Federation).** IAM & Admin → **Workload Identity Federation** → **Create pool** (or *Get started*):
   - [ ] Pool name `github-actions-pool` (check the ID below it is also `github-actions-pool`) → Continue.
   - [ ] Provider: **OpenID Connect (OIDC)** · Provider name `github-provider` (ID `github-provider`) · Issuer URL `https://token.actions.githubusercontent.com` · Audiences: **Default audience** → Continue.
   - [ ] Attribute mapping: `google.subject` = `assertion.sub`; **Add mapping**: `attribute.repository` = `assertion.repository`.
   - [ ] **Attribute conditions → Add condition**. Allow both the current and the new account name, since the rename (Part 4) comes after this:
     `assertion.repository in ['TamirS-OSH/OSH_Research', 'iiosh-research/OSH_Research']`
   - [ ] Save.
   - [ ] On the pool's page → **Grant access** → *Grant access using service account impersonation* → Service account `journal-dashboard-bot` → Select principals: **Only identities matching the filter** → Attribute name `repository`, value `TamirS-OSH/OSH_Research` → Save. If a "Configure your application" window appears, close it.
   - [ ] Repeat **Grant access** with the value `iiosh-research/OSH_Research`. **Google compares these names letter for letter, including upper/lower case, and the account name is all lowercase (`iiosh-research`).**
5. **Share the Sheet with the new service account.**
   - [ ] Whoever can share the Sheet (the departing maintainer until Part 6 is done) opens *IIOSH Dashboard Data* → **Share** → add `journal-dashboard-bot@<PROJECT_ID>.iam.gserviceaccount.com` as **Editor** → untick "Notify people" → Share.
6. **Point the workflow at the new project.** On GitHub: repo → Settings → Secrets and variables → Actions → **Variables** tab → **New repository variable**, twice:
   - [ ] `GCP_WIF_PROVIDER` = `projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider`. Use the 12-digit number from step 1, not the ID.
   - [ ] `GCP_SERVICE_ACCOUNT` = `journal-dashboard-bot@<PROJECT_ID>.iam.gserviceaccount.com`
7. **Test:**
   - [ ] Run a dry run ([Part 10](#part-10--verify)). The **update-dashboard** job must be green. If *Authenticate to Google Cloud* fails, re-check steps 4 and 6 (typos in the number or names are the usual cause). If it fails opening `'IIOSH Dashboard Data'`, re-check steps 2 and 5. To fall back to the old project at any time, delete the two variables.
8. **Once the dry run passes:**
   - [ ] Remove the **old** service account (`journal-dashboard-bot@research-497406…`) from the Sheet's sharing. The old project `research-497406` can be left to disappear with the personal account.

## Part 4 — Rename the GitHub account to `IIOSH-Research`

**Who: both, together. Part 3 must be done and its dry run green first.**

**What the rename changes:**

| | Before | After |
|---|---|---|
| Newsletter web address | `tamirs-osh.github.io/OSH_Research` | `iiosh-research.github.io/OSH_Research` |
| Repo page | `github.com/TamirS-OSH/OSH_Research` | `github.com/IIOSH-Research/OSH_Research` (the old address redirects) |
| Links in **emails sent before the rename** | work | **broken**. GitHub doesn't redirect the old Pages address. Every past edition is still online at the new address |
| Dashboard job's Google login | — | keeps working, because Part 3 already allows both names |
| Weekly trigger's URL | `.../repos/TamirS-OSH/...` | must use `IIOSH-Research` (Part 5) |
| Links in new newsletters | — | switch automatically. The workflow builds the address from the account name, so no code change is needed |
| Secrets, variables, tokens, Sheet, Looker, Gmail | — | unaffected |

The old name `TamirS-OSH` becomes free for anyone to register. If someone does, the old repo address stops redirecting. The risk is low; it's mentioned so a strange 404 at the old address isn't a mystery.

1. **Rename:**
   - [ ] github.com → Settings → **Account → Change username** → `IIOSH-Research` → confirm through the warnings.
2. **Right after renaming:**
   - [ ] Open `https://iiosh-research.github.io/OSH_Research/`. It shows the latest edition, though it may take a few minutes to appear.
   - [ ] Run a dry run ([Part 10](#part-10--verify)). The *Read dry-run address* step should log `Links point to https://iiosh-research.github.io/OSH_Research/preview`, **both jobs must be green**, and the email's button must open.
   - [ ] If Part 5 is **not** done in this sitting: as the departing maintainer, open the old *IIOSH Weekly Trigger* script, change `TamirS-OSH` to `IIOSH-Research` in the URL, and save. Otherwise Sunday's run may not start.
   - [ ] Update the old name in the docs. Use GitHub's search in the repo for `tamirs-osh` (`README.md` and the default in `newsletter/newsletter.py`, which only matters when running locally), edit each one on GitHub, and commit.
   - [ ] On any computer with a copy of the repo: `git remote set-url origin https://github.com/IIOSH-Research/OSH_Research.git`. Optional, since the old address redirects.
3. **After the first successful real Sunday run ([Part 10](#part-10--verify)), tighten the Google login to the new name only.** In the new project (signed in as `iiosh.news@gmail.com`):
   - [ ] IAM & Admin → Workload Identity Federation → `github-actions-pool` → `github-provider` → Edit → change the attribute condition to `assertion.repository == 'iiosh-research/OSH_Research'` → Save.
   - [ ] IAM & Admin → Service Accounts → `journal-dashboard-bot` → **Principals with access**: delete the entry ending in `attribute.repository/TamirS-OSH/OSH_Research`.

## Part 5 — Weekly trigger (Apps Script)

**Who: successor, signed in as `iiosh.news@gmail.com`. The departing maintainer is needed for the first and last steps.**

The trigger can't be transferred: an Apps Script trigger always runs as the person who created it. So a new one is created, and the old one is deleted in the same sitting.

1. **Look at the old trigger first.** Signed in as the departing maintainer, open script.google.com → *IIOSH Weekly Trigger* → **Triggers** (clock icon).
   - [ ] Write down its **day and time window**, so the new one fires at the same time.
2. **New GitHub token.** Signed in to GitHub as `IIOSH-Research`, go to Settings → Developer settings → Personal access tokens → **Fine-grained tokens → Generate new token**:
   - Name: `Apps Script weekly trigger`
   - Expiration: the longest offered. **Write the expiry date into the [Maintenance](#maintenance) table below.**
   - Resource owner: `IIOSH-Research`. Repository access: **Only select repositories → `OSH_Research`**.
   - Permissions → Repository permissions → **Actions: Read and write**. Nothing else.
   - [ ] Generate it and copy the token. It is shown only once.
3. **New Apps Script project.** Signed in as `iiosh.news@gmail.com`, go to script.google.com → **New project**:
   - [ ] Rename it to `IIOSH Weekly Trigger`.
   - [ ] **Project Settings** (gear icon) → set **Time zone** to `(GMT+03:00) Jerusalem`.
   - [ ] **Project Settings → Script Properties → Add script property**: name `GITHUB_PAT`, value = the token from step 2. Save.
   - [ ] Back in **Editor**, replace everything in `Code.gs` with the code below. In `testDryRun`, put the successor's own email address. Save.

   ```javascript
   // Fired by the weekly trigger: a REAL run that emails the full recipient list.
   function triggerWeeklyNewsletter() {
     dispatch_({});
   }

   // For testing: a DRY RUN. Only the address below gets the newsletter.
   function testDryRun() {
     dispatch_({ dry_run_email: 'PUT-YOUR-EMAIL-HERE' });
   }

   function dispatch_(inputs) {
     var token = PropertiesService.getScriptProperties().getProperty('GITHUB_PAT');
     var url = 'https://api.github.com/repos/IIOSH-Research/OSH_Research/actions/workflows/weekly_update.yml/dispatches';
     var response = UrlFetchApp.fetch(url, {
       method: 'post',
       contentType: 'application/json',
       headers: {
         'Authorization': 'Bearer ' + token,
         'Accept': 'application/vnd.github+json',
         'X-GitHub-Api-Version': '2022-11-28'
       },
       payload: JSON.stringify({ ref: 'main', inputs: inputs }),
       muteHttpExceptions: true
     });
     var code = response.getResponseCode();
     Logger.log(code + ' ' + response.getContentText()); // 204 = success
     // Throwing makes the trigger's failure email fire (e.g. when the token expires).
     if (code !== 204) {
       throw new Error('GitHub refused the run (HTTP ' + code + '): ' + response.getContentText());
     }
   }
   ```

   This keeps the original behaviour, with two additions. `testDryRun` allows a safe test. The `throw` makes a refused request (for example, an expired token) count as a failure, so the failure email actually arrives. The previous version only logged the error, so it would have failed silently.

4. **Test it. Never test with `triggerWeeklyNewsletter`: that is a real send to everyone.**
   - [ ] In the function dropdown, choose **`testDryRun`** → **Run**. The first time, Google asks for permission: Review permissions → choose `iiosh.news@gmail.com` → Advanced → *Go to IIOSH Weekly Trigger (unsafe)* → Allow. This warning is normal for your own scripts.
   - [ ] The execution log should show `204`.
   - [ ] On GitHub → Actions, a run named **"IIOSH Weekly Automation (dry run)"** appears within a minute. Let it finish (Part 10 lists what to check).
5. **Create the weekly trigger.** Triggers (clock icon) → **Add Trigger**:
   - Function: `triggerWeeklyNewsletter` · Deployment: Head · Event source: **Time-driven** · Type: **Week timer** · Day and time: **as written down in step 1**
   - Failure notification settings: **Notify me immediately**
   - [ ] Save.
6. **Delete the old trigger in the same sitting, or the newsletter goes out twice on Sunday.**
   - [ ] Signed in as the departing maintainer, go to the old *IIOSH Weekly Trigger* → Triggers → ⋮ → **Delete trigger**.
   - [ ] On GitHub (as `IIOSH-Research`) → Personal access tokens → Fine-grained tokens: **delete the old token**, i.e. the one that isn't `Apps Script weekly trigger`.

## Part 6 — Google Sheet "IIOSH Dashboard Data"

**Who: departing maintainer, then successor.**

The dashboard job finds the Sheet **by its exact name** and writes to it as the service account from Part 3 (`journal-dashboard-bot@<PROJECT_ID>.iam.gserviceaccount.com`). Keep the name, and keep that account as Editor.

**Plan A — transfer ownership:**
- [ ] Departing: open the Sheet → **Share** → add `iiosh.news@gmail.com` as **Editor** → Send.
- [ ] Departing: in the same dialog, open the dropdown next to `iiosh.news@gmail.com` → **Transfer ownership** → Send invitation.
- [ ] Successor: in the `iiosh.news` inbox (or Drive → Shared with me), **accept** the ownership request.
- [ ] Check the Share dialog: `iiosh.news@gmail.com` is the Owner, and the Part 3 service account is still an **Editor**.

**Plan B — use this only if Google refuses the transfer** (it can block transfers from a work account to a gmail.com account):
- [ ] Successor, signed in as `iiosh.news`: open the Sheet → **File → Make a copy**. All tabs are copied, including **Journal Metadata**.
- [ ] Rename the copy to exactly `IIOSH Dashboard Data`.
- [ ] Share the copy with the Part 3 service account as **Editor**. Untick "Notify people".
- [ ] Departing: **remove the service account from the old Sheet.** Otherwise the job sees two Sheets with the same name and may write to the wrong one.
- [ ] Point Looker at the new Sheet ([Part 7](#part-7--looker-studio-dashboard), Plan B).

## Part 7 — Looker Studio dashboard

**Who: departing maintainer, then successor.**

The report reads the Sheet through **data sources**, at least two: the article tab and the Journal Metadata tab, which are joined. A data source using **"Owner's credentials"** reads the Sheet *as its owner*. If that owner is deleted, the dashboard goes blank even though the Sheet is fine. So the report, every data source **and** their credentials all have to move.

**Plan A — transfer ownership:**
- [ ] Departing: in Looker Studio, open the report → **Share** → add `iiosh.news@gmail.com` as **Editor** → then, next to it, **Make owner**.
- [ ] Departing: from the Looker Studio home page → **Data sources**, do the same for **each** data source the report uses. In the report, Resource → Manage added data sources lists them.
- [ ] Successor, signed in as `iiosh.news`: open each data source → click **Data credentials** (top left) → choose **Owner's credentials** → Update. The data source now reads the Sheet as `iiosh.news`.
- [ ] Open the report and check the record count matches what it showed before.

**Plan B — if the transfer is refused, or the Sheet was copied in Part 6:**
- [ ] Successor, as `iiosh.news`: open the report → ⋮ → **Make a copy**. Looker offers new data sources; create them from the **new** Sheet (both tabs).
- [ ] Check the copy shows the same record count and that filters work.
- [ ] **The dashboard link changes.** Update it in [README.md](README.md) (top line) and tell the people who use it.

## Part 8 — Gemini API key

**Who: departing maintainer checks; successor replaces it if needed.**

- [ ] Departing, signed in to the **personal** Google account: open aistudio.google.com → **Get API key**. If the key is listed there, it belongs to that account (possibly to the old Cloud project) and must be replaced. Note whether its plan says **Free** or **Paid**.
- [ ] Successor, signed in as `iiosh.news`: aistudio.google.com → Get API key → **Create API key**. It can go in the `iiosh-automation` project from Part 3. If the old key was on a paid plan, set up billing for the new one too. Otherwise the free tier's limits may make summaries fail.
- [ ] On GitHub → repo Settings → Secrets → **`GEMINI_API_KEY` → Update** with the new key.
- [ ] Run a dry run and check that the email contains AI summaries.

## Part 9 — Files that live only on the departing maintainer's computer

These are git-ignored and exist nowhere else. Send them through an internal channel, **not** through this repo.

- [ ] `newsletter/recipients.txt`: the recipient list, one address per line. GitHub never shows the `RECIPIENT_LIST` secret again, so this file is the only copy. See the README's *GitHub Secrets Required* section for how to update recipients.
- [ ] The two journal-list Word files in the repo folder: `ירחונים לסקירה שוטפת מה חדש בתחומינו.docx` and `וכנסים רשימת_כתבי_עת_למעקב_שבועי_–_גרסה_נקייה.docx`.
- [ ] **Not** `credentials.json`. It is an old login file the automation no longer uses. Delete it.

**Unfinished work to know about:** branch `feat/occ-cancer-edition` holds a second newsletter edition for a researcher's occupational-cancer literature feed. It is not live. Its design and current state are in `docs/Occupational_Cancer_Edition_Plan.md` **on that branch**. `main` has moved on since, so merging needs manual reconciliation. The branch also still hardcodes the old `tamirs-osh` address and the old Cloud project in its workflow.

## Part 10 — Verify

**Dry run** (safe at any time, except within about 30 minutes of the Sunday trigger):
- [ ] Actions → **IIOSH Weekly Automation** → **Run workflow** → type your own address in **dry_run_email** → Run. If the field isn't visible, press Ctrl+F5 first. **Never click Run with the field empty:** that is a real send.
- [ ] Both jobs turn green.
- [ ] An email titled **[DRY RUN] …** arrives from `iiosh.news@gmail.com`, with AI summaries, and its link opens a page under `/preview/`.

**The first real Sunday after the handover:**
- [ ] A run named **IIOSH Weekly Automation** (without "(dry run)") appears Sunday morning, started by the new trigger. If no run appears, see [Troubleshooting](#troubleshooting).
- [ ] The *Read dry-run address* step logs `Real run … Links point to https://iiosh-research.github.io/OSH_Research`, and the newsletter step logs `Email sent successfully to N recipients`.
- [ ] `iiosh-research.github.io/OSH_Research` shows the new edition.
- [ ] In Looker, **Refresh data**: the record count went up.

**Only after that Sunday passes:**
- [ ] Part 4, step 3: tighten the Google login to the new name only.
- [ ] Departing: remove your own access from the Sheet and the Looker report and data sources.
- [ ] Departing: delete the old Apps Script project from the personal account.
- [ ] Departing: remove the GitHub login saved on your computer (Windows → Credential Manager → Windows Credentials → `git:https://github.com`).

---

## Maintenance

| What | When | How |
|---|---|---|
| **GitHub token for the trigger** | **Expires on: ____________** (fill in at Part 5) | A few weeks before: make a new token with the same settings (Part 5, step 2), paste it into the Apps Script's `GITHUB_PAT` script property, run `testDryRun`, then delete the old token. **If it expires, the newsletter just stops**, and the only sign is the failure email. |
| Sign in to `iiosh.news@gmail.com` | At least once a year, e.g. when renewing the token | Google deletes personal accounts that go unused for 2 years. |
| Recipient list | When people join or leave | README → *GitHub Secrets Required*. |
| Adding a journal | When needed | README → *Adding a Journal*. Four places, including the Sheet's Journal Metadata tab. |
| Gemini model | If Google retires `gemini-3.1-flash-lite` (summaries fail with a "model not found" error) | Change the model name in `newsletter/newsletter.py` (3 places). |
| Renaming the GitHub account again | Avoid if possible | First add the new name to the Google login (Part 3, step 4: the condition and a second Grant access), then repeat Part 4, and update the URL in the Apps Script. Links in emails already sent will break. |
| Next handover | When the maintainer changes | Hand over `iiosh.news@gmail.com` (Part 2: recovery details, 2FA, password, new app password, forwarding), move GitHub's 2FA and password (Part 1, steps 2–4), then do Part 10. Everything else already lives on the two automation accounts. |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No run at all on Sunday | The trigger failed: token expired or revoked, wrong account name in its URL, or the trigger was deleted | Read the failure email in `iiosh.news`, or Apps Script → Executions. HTTP 401 means renew the token (Maintenance). HTTP 404 means check the URL says `IIOSH-Research`. |
| Two runs on Sunday | The old trigger still exists | Part 5, step 6. |
| *Authenticate to Google Cloud* step fails | The Google login doesn't allow the current account name, or the repository variables have a typo | Part 3, steps 4 and 6. |
| Dashboard job fails opening `'IIOSH Dashboard Data'` | Sheet renamed, the service account lost Editor access, or the Drive/Sheets APIs are off | Part 3, steps 2 and 5, and Part 6. |
| Newsletter step: `Username and Password not accepted` | The Gmail password changed or 2-Step Verification was turned off, which revoked the app password | Part 2, step 4. |
| Newsletter arrives without AI summaries | Gemini key invalid, out of quota, or model retired | Part 8, and the Maintenance row on the Gemini model. |
| "Read the full update" in an old email gives 404 | The email predates the rename | Expected. The edition is at the same path on `iiosh-research.github.io/OSH_Research/`. |
| Dashboard empty or "can't access data" | A data source still uses a deleted account's credentials | Part 7: Data credentials. |
| A new journal's articles don't show in Looker | Missing from the Journal Metadata tab | README → *Adding a Journal*. |
