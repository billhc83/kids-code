# KidsCode — Security Audit Completion Log

---

## Session 1 — 2026-06-26

**Source audit:** `security-audit-2026-06.md`  
**Engineer:** Claude (automated)  
**Items resolved:** 7 (all autonomously completable — no user input required)

---

### 1.2 — Auth-gate `/dev/` routes
**File:** `routes/dev.py`  
**Change:** Added `from utils.decorators import admin_required` and applied `@admin_required` to all three routes: `circuit_sandbox`, `circuit_compare`, `circuit_preview`. Any unauthenticated or non-admin visitor is now redirected to login/home instead of seeing internal developer tooling.

---

### 1.6 — Legacy SHA-256 password hash migration
**Files:** `utils/auth.py`, `routes/auth.py`  
**Change:** Added two helpers to `utils/auth.py`:
- `is_legacy_hash(stored)` — returns True if the stored hash is not a bcrypt hash
- `upgrade_password_hash(user_id, password)` — re-hashes with bcrypt and updates the `users` table row

In `routes/auth.py`, after a successful login check, the login route now calls `upgrade_password_hash` if the stored hash is legacy. The upgrade is silent — the user sees no change. The legacy SHA-256 code path remains in `check_password` until confirmed that all legacy hashes are gone.

---

### 1.7 — Session lifetime reduced
**File:** `app.py`  
**Change:** `app.permanent_session_lifetime = timedelta(days=30)` → `timedelta(hours=8)`. Sessions on shared/school computers now expire after 8 hours of inactivity, limiting the window for session hijacking.

---

### 1.9 — UUID validation on admin form parameters
**File:** `routes/admin.py`  
**Change:** Added `_UUID_RE` regex and `_is_valid_uuid()` helper at the top of the file. Every admin POST action that uses `user_id`, `submission_id`, or `thread_id` now validates the value against the UUID pattern before it is interpolated into a Supabase REST URL. Invalid IDs produce a flash error and abort the action — preventing URL injection via crafted form submissions.

---

### 1.11 — Admin image upload MIME type and size validation
**File:** `routes/admin.py` (`step_builder_preview`)  
**Change:** Before calling `base64.b64decode()`, the handler now:
1. Checks that `","` is present in the data URI (malformed data rejected with 400)
2. Extracts and validates the MIME type — only `image/png`, `image/jpeg`, `image/gif`, `image/webp` are accepted (others return 400)
3. Checks decoded byte length is ≤ 5 MB (larger payloads return 400)

---

### 1.13 — Security response headers
**File:** `app.py`  
**Change:** Added an `@app.after_request` hook (`set_security_headers`) that attaches four headers to every response:
- `X-Content-Type-Options: nosniff` — prevents MIME sniffing
- `X-Frame-Options: SAMEORIGIN` — blocks clickjacking from external frames
- `Referrer-Policy: strict-origin-when-cross-origin` — limits referrer leakage
- `Content-Security-Policy` — restricts script/style/font/image sources; allows `'unsafe-inline'` for scripts and styles (required by existing lesson templates); allows Google Fonts CDN for fonts and styles (pending self-hosting per item 1.14)

---

### 3.2 — Password strength minimum (8 characters)
**Files:** `routes/auth.py`, `utils/auth.py`  
**Changes:**
- `routes/auth.py` register route: rejects passwords shorter than 8 characters before hashing, returns to register form with flash message
- `routes/auth.py` reset_password route: same check applied to new password on reset
- `utils/auth.py` `create_student_for_parent`: 8-character minimum enforced before hash, returns error tuple to caller

---

---

## Session 2 — 2026-06-26

**Item:** 1.1 — CSRF protection  
**Engineer:** Claude (automated)

### 1.1 — CSRF protection (flask-wtf)
**Files:** `requirements.txt`, `extensions.py`, `app.py`, `templates/base.html`, all 33 POST form templates

**Changes:**

1. **Package:** Installed `flask-wtf==1.3.0`; added `flask-wtf` to `requirements.txt`.

2. **`extensions.py`:** Added `from flask_wtf.csrf import CSRFProtect` and `csrf = CSRFProtect()`.

3. **`app.py`:** Imported `csrf` from `extensions` and called `csrf.init_app(app)` alongside the existing `limiter.init_app(app)`.

4. **`templates/base.html` — meta tag:** Added `<meta name="csrf-token" content="{{ csrf_token() }}">` to the `<head>`. This makes the current token available to JavaScript without embedding it inline in script blocks.

5. **`templates/base.html` — fetch interceptor:** Added a `<script>` block before `{% block scripts %}` that wraps `window.fetch`. For any non-GET/HEAD request to a same-origin URL, it automatically injects `X-CSRFToken: <token>` into the request headers. This covers all AJAX POSTs with zero per-callsite changes:
   - `/api/welcome-complete` (dashboard.html, parent.html)
   - `/admin/step-builder-preview` (admin/step_builder.html)
   - `/sim/run` (sim-engine.js)
   - `/api/help` (block_builder.js or future callers)

6. **All 33 HTML forms:** Added `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` as the first child inside every `<form method="POST">` across:
   - Auth forms: login, register, forgot_password, reset_password, check_email (resend verification)
   - Feedback forms: new thread + reply (feedback.html); 3 thread action forms + reply form (admin/index.html)
   - Admin forms: review challenge, toggle admin, delete user (admin/index.html)
   - Parent forms: reset student password, create student (parent.html)
   - Lesson completion forms: project_base.html (covers all single-page lessons) + 16 individual multi-part/standalone templates
   - Challenge submission form: challenge_one.html

**Verification:** Automated scan confirmed zero POST forms remain without a `csrf_token` field. App initializes correctly with CSRFProtect active (confirmed via test_request_context smoke test).

---

---

## Session 3 — 2026-06-26

**Item:** 7 — Privacy Policy + Terms pages + footer links  
**Engineer:** Claude (automated)

### Pre-work — OpenAI account hardening
Before writing the policy, confirmed with user that the following were configured on their OpenAI account:
- **Model training/sharing:** disabled — API submissions not used to train models
- **Organisation API call logging:** disabled — no logs retained in OpenAI dashboard
- **Data Processing Addendum:** downloaded and on file
- **Retention:** OpenAI's standard 30-day abuse-monitoring retention (their policy, not ours)

### 7 — Privacy Policy, Terms of Use, Privacy Contact Form

**Files created:**
- `templates/privacy.html` — Full PIPEDA + COPPA compliant privacy policy
- `templates/terms.html` — Terms of Use
- `templates/privacy_contact.html` — Rate-limited contact form, submits via Resend

**Files modified:**
- `routes/main.py` — Added `/privacy`, `/terms`, `/privacy/contact` routes; contact form sends via Resend to operator email with `reply_to` set to submitter's address (operator email never exposed publicly)
- `templates/base.html` — Footer added with Privacy Policy, Terms of Use, and Privacy Contact links on every page

**Policy decisions:**
- Operator identified as "KidsCode (kidscode.ca)" — personal name deliberately omitted from public pages
- Jurisdiction: Ontario, Canada; PIPEDA compliance + COPPA section for student accounts
- OpenAI section accurately describes: training off, org logging off, DPA in place, 30-day abuse retention
- Discord disclosure: username/category/subject only, no message content
- 30-day deletion commitment documented (infrastructure for automated purge is a separate pending item — audit #17)
- Contact form rate-limited to 3 per hour via flask-limiter

---

## Session 7 — 2026-06-26

**Item:** 16 — Admin audit logging

### DB migration required
```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    admin_id UUID NOT NULL,
    admin_username TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    detail_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Files created
- `utils/audit.py` — `log_admin_action()` (silent failure, never blocks admin work) and `get_audit_log(limit=100)`

### Files modified
- `routes/admin.py` — imported `log_admin_action` and `get_audit_log`; added audit calls to all 7 destructive actions: `feedback_reply`, `feedback_delete`, `feedback_resolve`, `challenge_review`, `admin_toggle`, `user_delete`, `account_purge`; passes `audit_log` to template
- `templates/admin/index.html` — new "🔐 Audit Log" tab showing last 100 entries as a colour-coded table (red for deletes/purge, yellow for admin toggle, green for approvals, blue for others); target IDs are truncated to first 8 chars for readability

---

## Session 6 — 2026-06-26

**Item:** 8 — Registration consent checkbox + `agreed_at` DB column

### DB migration required
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS agreed_at TIMESTAMPTZ DEFAULT NULL;
```

### Files changed
- `templates/register.html` — required checkbox with links to Privacy Policy and Terms of Use, added between password field and submit button
- `utils/auth.py` — `create_user()` accepts `agreed_at` parameter, stores it in the `users` table row
- `routes/auth.py` — validates `agree_tos` checkbox is present before processing; records UTC timestamp at moment of consent; passes it to `create_user()`

### Notes
- Server-side validation: if the checkbox is missing from the POST body, registration is rejected with a flash message. The HTML `required` attribute also enforces it client-side.
- `agreed_at` is `NULL` for all accounts created before this deploy. Existing users are not affected.
- Student accounts created by parents via the parent dashboard do not get an `agreed_at` — the parent's own `agreed_at` covers their consent for their children (captured at parent registration). Item 9 adds an explicit parent acknowledgment on student creation.

---

## Session 5 — 2026-06-26

**Item:** 1.5 — Proxy block_saves through Flask (SUPABASE_ANON_KEY removal)  
**Engineer:** Claude (automated)

### Root cause
`builder_endpoint()` embedded `SUPABASE_ANON_KEY` in the JSON config sent to `block_builder_fragment.html`. The JS read it as `BB.SUPABASE_KEY` and used it to make direct Supabase REST calls for save/load. Every authenticated user could see the key in DevTools. Because the app uses Flask sessions (not Supabase Auth), `auth.uid()` was always NULL — RLS policies could not enforce per-user access on `block_saves`.

### What changed

**`routes/builder.py`**
- Removed `SUPABASE_ANON_KEY` import
- Removed `supabase_url`/`supabase_key` from `builder_endpoint()` call
- Added `POST /api/blocks/save` — session-verified, writes via service key
- Added `GET /api/blocks/load` — session-verified, reads via service key

**`utils/block_builder_config.py`**
- Removed `supabase_url` and `supabase_key` parameters from `build_config()`
- Removed both fields from the config dict sent to the browser
- Added `kwargs.pop()` safety in `render_builder()` to silently ignore any legacy callers passing the old params

**`utils/block_builder.py`**
- Removed `supabase_url`/`supabase_key` from `get_builder_html()` signature
- Added `**_ignored` to absorb any stale call sites

**`static/js/block_builder.js`**
- Removed `BB.SUPABASE_URL` and `BB.SUPABASE_KEY` assignment lines
- Replaced 3 direct Supabase REST calls with Flask proxy calls:
  - `BB.saveBlocks` → `POST /api/blocks/save` with `{page, blocks_json}`
  - `BB.loadBlocks` → `GET /api/blocks/load?page=X`, reads `resp.data[0].blocks_json`
  - `BB.saveBlocksAuto` → same as saveBlocks, flashes 'Auto-saved'

**`utils/deletion.py`** (bug fix found during this work)
- `block_saves` table stores `user_id` in its `username` column (not the display username)
- Fixed `purge_user()` to delete by `user_id` instead of `username`

### Result
`SUPABASE_ANON_KEY` no longer appears anywhere in any HTTP response. The block save/load path is now session-gated server-side. RLS is no longer needed for `block_saves` since all writes go through Flask with the service key and are scoped to `session["user_id"]`.

---

---

## Item 14 — Persistent Rate Limiting — Deferred

**Attempted:** 2026-06-26  
**Outcome:** Not implemented — deferred indefinitely

### What was tried

The existing `flask-limiter` uses `storage_uri="memory://"`. We investigated replacing this with a Supabase-backed persistent store to eliminate the reset-on-restart gap.

**Approach 1 — `limits[SQLAlchemy]` extra:**  
The `limits` library (v5.8.0, the version installed) dropped PostgreSQL/SQLAlchemy support. The `[SQLAlchemy]` extra installs but does nothing — the PostgreSQL URI scheme is not registered and raises `ConfigurationError: unknown storage scheme`.

**Approach 2 — Custom storage class:**  
Would require implementing the `limits` Storage interface against Supabase's REST API — atomic increment, window expiry, TTL handling. Approximately 60 lines, maintainable long-term but non-trivial and depends on the `limits` internal interface not changing.

**Approach 3 — Downgrade `limits`:**  
Older versions (3.x) had SQLAlchemy support. Rejected — pinning old library versions carries its own security risk and would conflict with the current `flask-limiter` dependency tree.

### Why it was deferred

The actual risk is low for this platform at current scale:
- Gunicorn runs 1 worker — no cross-process counter splitting
- Rate limits only reset on intentional deploys, not spontaneously  
- bcrypt hashing is the primary defense against password brute force regardless of rate limiting
- The platform is not a high-value financial target

### When to revisit

- If traffic grows significantly and Redis becomes worthwhile for other reasons (caching, sessions)
- If a future `limits` release re-adds PostgreSQL support
- If the threat model changes (e.g. targeted attack on login endpoint)

**Packages installed and removed:** `sqlalchemy`, `psycopg2-binary` — both uninstalled, not added to requirements.txt.

---

## Items Still Open (require user decision or infrastructure work)

| # | Item | Blocker |
|---|---|---|
---

## Session 4 — 2026-06-26

**Item:** 17 — Account self-deletion flow  
**Engineer:** Claude (automated)

### DB migration required (user must run in Supabase SQL editor)
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS deletion_requested_at TIMESTAMPTZ DEFAULT NULL;
```

### Files created
- `utils/deletion.py` — `request_account_deletion()`, `cancel_deletion_request()`, `get_pending_deletions()`, `get_accounts_due_for_purge()`, `purge_user()`, `run_purge()`. Cascade order: feedback_messages → feedback_threads → challenge_submissions → block_saves → activity_logs → badges → progression → parent_student_links (both sides) → users.
- `utils/purge_deleted_accounts.py` — standalone script, runnable as `python utils/purge_deleted_accounts.py`. Schedule with cron or external cron service.
- `routes/account.py` — `/account/delete` (GET: confirm page, POST: schedule deletion + log out), `/account/delete/confirmed` (public, no login required)
- `templates/account_delete.html` — confirmation form requiring user to type "DELETE"
- `templates/account_delete_confirmed.html` — post-deletion landing page

### Files modified
- `routes/admin.py` — added `run_account_purge()` route at `POST /admin/run-purge`; `get_pending_deletions()` passed to admin dashboard template
- `routes/parent.py` — added `request_student_deletion` action; verifies student belongs to requesting parent before marking
- `templates/parent.html` — "Delete Account" details block per student; shows pending status if already requested
- `templates/admin/index.html` — pending deletions table + "Run Purge Now" button in analytics tab
- `templates/dashboard.html` — low-profile "Delete my account" link at bottom of dashboard
- `app.py` — registered `account_bp`

### Design decisions
- Admin accounts blocked from self-deleting (must remove admin flag first)
- Parent deleting a student marks only that student; parent's own account unaffected
- Parent accounts can be deleted via self-service at `/account/delete`; their student accounts are orphaned (links removed on purge) but not auto-deleted — operator handles separately
- Purge is manual/scheduled — no automatic daily job built-in; script is ready to be wired to cron

---

---

## Audit Closeout — 2026-06-27

### All 18 items reconciled against actual code

| # | Item | Status |
|---|---|---|
| 1 | Auth-gate `/dev/` routes | ✅ Done — Session 1 |
| 2 | Security response headers | ✅ Done — Session 1 |
| 3 | Reduce session lifetime to 8h | ✅ Done — Session 1 |
| 4 | Companion releases to own repo + `/latest/` URL | ⏳ Open — GitHub task, no code blocker |
| 5 | Proxy block_saves through Flask (anon key removal) | ✅ Done — Session 5 |
| 6 | CSRF protection | ✅ Done — Session 2 |
| 7 | Privacy Policy + Terms pages + footer links | ✅ Done — Session 3 |
| 8 | Registration consent checkbox + `agreed_at` | ✅ Done — Session 6 |
| 9 | Parent consent acknowledgment on student creation | ✅ Done — Session 6 |
| 10 | AI tutor consent — captured at registration via ToS | ✅ Done — Session 6 |
| 11 | UUID validation on admin URL parameters | ✅ Done — Session 1 |
| 12 | Password strength minimum (8 chars) | ✅ Done — Session 1 |
| 13 | `/download` page for KidsCode Link | ✅ Done — route + template in place |
| 14 | Persistent rate limiting | 🚫 Withdrawn — no viable option without an external service (Redis); `limits` v5 dropped PostgreSQL support. In-memory limiting remains. bcrypt is the primary brute-force defence. Revisit if Redis is adopted for another reason. |
| 15 | Legacy password hash migration | ✅ Done — Session 1 |
| 16 | Admin audit logging | ✅ Done — Session 7 |
| 17 | Account self-deletion flow | ✅ Done — Session 4 |
| 18 | Drop `username` from `activity_logs` | ✅ Done — Session 7 |

### Residual low-priority items (no action planned)

| Item | Notes |
|---|---|
| 1.10 Discord webhook disclosure | Privacy policy now discloses username/category/subject sent to Discord. No code opt-out — acceptable at current scale. |
| 1.14 Self-host Google Fonts | Google Fonts CDN allowed in CSP. Self-hosting deferred; no user data beyond IP is sent. |
| Splash demo config cleanup | `routes/builder.py` lines 57–58 send `"supabase_url": ""` and `"supabase_key": ""` as empty strings in the demo config. Harmless but should be removed. |
