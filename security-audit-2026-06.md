# KidsCode — Security, Privacy & Platform Audit
**Date:** June 2026  
**Scope:** Full codebase review — security, compliance, privacy, companion software

---

## Summary

KidsCode collects and processes personal data for children (ages 8–14), including authentication credentials, lesson progress, activity logs, submitted code, and support messages. It integrates with Supabase, OpenAI, Resend, and Discord. This audit covers all active routes, templates, client-side JS, and configuration.

---

## 1. Security Issues

### Critical

**1.1 — No CSRF protection anywhere** ✅ FIXED 2026-06-26
Every form (login, register, password reset, parent dashboard, feedback, admin actions) is vulnerable to cross-site request forgery. `flask-wtf` + `CSRFProtect(app)` closes this. Every HTML form needs a `{{ csrf_token() }}` field; AJAX routes need the token in headers.  
Fix: Installed `flask-wtf`, initialized `CSRFProtect` in `extensions.py` + `app.py`, added CSRF meta tag and global fetch interceptor to `base.html`, and added `{{ csrf_token() }}` hidden inputs to all 33 POST forms across all templates.  
Files: `templates/*.html`, `extensions.py`, `app.py`

**1.2 — `/dev/` routes are publicly accessible** ✅ FIXED 2026-06-26
`routes/dev.py` has zero auth decorators. Circuit previews, builder sandboxes, and developer comparison tools are accessible to anyone without a login.  
Fix: Add `@login_required` (or `@admin_required`) to every route.  
File: `routes/dev.py`

**1.3 — Admin actions have no audit trail**
Deleting accounts, toggling `is_admin`, approving/rejecting challenge submissions — none are logged. A compromised or rogue admin session leaves no evidence.  
Fix: Add `audit_logs` table (`admin_id, action, target_type, target_id, detail_json, created_at`) and write on every destructive admin action.  
File: `routes/admin.py`

**1.4 — Rate limiting is in-memory and not persistent**
`storage_uri="memory://"` means rate limits reset on every deploy or restart and don't work across multiple processes. Auth endpoints (login, register, password reset) are the highest-risk targets.  
Fix: Switch to Redis or a Supabase-backed store.  
File: `extensions.py`, `app.py`

---

### High

**1.5 — SUPABASE_ANON_KEY exposed to the browser (core architectural issue)** ✅ FIXED 2026-06-26
`block_builder.js` receives `SUPABASE_ANON_KEY` from the server and makes direct REST calls to Supabase to save/load user code. The key is visible in DevTools to anyone.

The deeper problem: the app uses Flask sessions, not Supabase Auth. This means `auth.uid()` is NULL for all anon-key requests. RLS policies that rely on `auth.uid()` cannot identify the user and therefore cannot enforce per-user row access on `block_saves`.

**Fix: proxy all block_saves operations through Flask.**
- Replace the 3 fetch calls in `block_builder.js` (lines 205, 218, 284) with calls to `/api/blocks/save` and `/api/blocks/load`
- Flask verifies session, writes/reads via service key on the server
- Remove `supabase_key` from `build_config()` and the frontend config entirely
- The anon key never reaches the browser

Files: `static/js/block_builder.js`, `utils/block_builder_config.py`, `routes/builder.py`, `config.py`

**1.6 — Legacy SHA-256 password hashing** ✅ FIXED 2026-06-26
Old password hashes use `sha256(salt + password)` — cryptographically weak. Indicates a prior user cohort with insecure credential storage.  
Fix: On next successful login with a legacy hash, silently re-hash with bcrypt and update the DB record. Remove the legacy path once all known legacy hashes are gone.  
File: `utils/auth.py`

**1.7 — Session lifetime is 30 days** ✅ FIXED 2026-06-26
For a children's platform where shared computers are common, 30 days is excessive.  
Fix: Reduce to 8 hours active session or 7 days maximum with idle timeout.  
File: `app.py`

**1.8 — Student code sent to OpenAI without user consent**
`/api/help` streams student sketch code, error symptoms, and lesson context to the OpenAI API. There is no consent gate, no disclosure in the UI, and no opt-out mechanism. This is a COPPA requirement, not optional.  
File: `routes/help.py`

**1.9 — Admin route URL parameters not validated** ✅ FIXED 2026-06-26
`user_id`, `submission_id`, and `thread_id` are interpolated directly into Supabase REST URL queries (e.g. `?id=eq.{user_id}`) without being validated as UUIDs first.  
File: `routes/admin.py`

---

### Medium

**1.10 — Discord webhook leaks usernames and feedback content**
Every feedback submission sends `username`, `category`, and `subject` to an external Discord server. Users are not informed of this in any policy or UI disclosure.  
File: `utils/feedback.py`

**1.11 — Admin image upload has no type validation** ✅ FIXED 2026-06-26
`/admin/step-builder-preview` accepts `image_src` and calls `base64.b64decode()` without validating MIME type or file size.  
File: `routes/admin.py`

**1.12 — Activity logs store `username` redundantly**
`activity_logs` stores both `user_id` and `username`, creating a second linkage path. Drop `username` from this table — join to `users` at query time when needed.

**1.13 — No security response headers** ✅ FIXED 2026-06-26
No `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, or `Referrer-Policy` headers are set.  
Fix: Added `after_request` hook in `app.py` setting CSP, `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`.

**1.14 — Google Fonts loaded from external CDN**
`base.html` loads Poppins from `fonts.googleapis.com`, sending user IP addresses to Google on every page load. Consider self-hosting the font files.

---

## 2. Privacy Policy — Required Content & Placement

### What the policy must cover

| Section | Content |
|---|---|
| Who we are | Legal entity name, contact email, jurisdiction |
| What we collect | Email, username, password hash, lesson progress, activity time, submitted code, feedback/support messages, session cookie, `kclink_installed` localStorage flag |
| Why we collect it | Account creation, progress tracking, AI tutoring, email notifications |
| Third parties | Supabase (database hosting), Resend (email), OpenAI (AI tutor — **must be explicit**), Discord (internal admin notifications only) |
| Children under 13 (COPPA) | Parental consent requirement, what data is stored for child accounts, parent right to review and delete |
| AI tutoring disclosure | Student code and questions are processed by OpenAI; include a reference to OpenAI's data processing agreement |
| Data retention | How long data is kept; what happens on account deletion |
| User rights | How to request access, correction, or deletion of personal data |
| Cookies & local storage | Session cookie + `kclink_installed` flag |
| Contact | Privacy request email address |

### Where to add it in the app

1. **Footer on every page** — two links (`Privacy Policy`, `Terms of Use`) in `templates/base.html`
2. **Registration form** — checkbox: *"I have read and agree to the Privacy Policy and Terms of Use"*; store `agreed_at` timestamp in `users` table
3. **Parent dashboard** — separate acknowledgment before creating a student account: *"I confirm I am the parent/guardian of this child and consent to data collection on their behalf"*; store `parent_consent_given_at`
4. **First AI Help request** — one-time modal: *"Your code and question will be sent to OpenAI to generate a hint. Continue?"* Set a session or localStorage flag so it only shows once
5. **Dedicated routes** — `/privacy` and `/terms` served from new templates; link from footer

---

## 3. Other Compliance & UX Shortfalls

**3.1 — No account self-deletion flow**
COPPA and GDPR both give users (and parents, for children) the right to request deletion. No self-service path exists. Minimum viable: a support email link. Better: a button in account settings with a confirmation step. Requires cascading across `users`, `progression`, `activity_logs`, `badges`, `block_saves`, `feedback_threads`, `feedback_messages`, `challenge_submissions`, `parent_student_links`. Soft-delete (`deleted_at` flag) is the safer implementation — reversible if a deletion was accidental.

**3.2 — No password strength requirements** ✅ FIXED 2026-06-26
Registration and parent-created student accounts accept any password length. Added minimum 8-character enforcement server-side in `routes/auth.py` (register + reset_password) and `utils/auth.py` (create_student_for_parent).

**3.3 — Student account email is intentionally fake**
Student accounts are created with `{username}.{uuid}@kidscode.internal` because children typically don't have their own email addresses — this is correct by design. The one gap: if a parent loses access to their own account, they can recover via the standard forgot-password flow on their email address. **Parent account recovery is fully functional.** The only remaining edge case is if a parent permanently loses access to their email provider — no recovery path exists in that scenario beyond manual admin intervention.

**3.4 — No `agreed_to_tos` timestamp in `users` table**
There is currently no record that any user accepted any terms, which matters legally if terms ever need to be enforced.

---

## 4. Companion Software — KidsCode Link

### Current state
KidsCode Link releases are hosted under the main `kids-code` GitHub repo:  
`https://github.com/billhc83/kids-code/releases/download/KidsCode_Link/KidsCode.Link.Setup.1.0.0.exe`

The install/detect modal in `templates/components/arduino_interface.html` already handles the download flow correctly. GitHub Releases is the right hosting choice — free bandwidth, version tagging, no CDN cost.

### Recommended changes

**4.1 — Move to a dedicated repository**
Create a `kidscode-link` (or `kclink`) repository for the companion app. Benefits: independent versioning, cleaner release history, own README with install screenshots, main repo's release page stays clean.  
Update the two URLs in `templates/components/arduino_interface.html` (lines 784, 795).

**4.2 — Use GitHub's `/releases/latest/download/` URL pattern**
Replace the hardcoded version in the download URL with GitHub's stable latest-release redirect:  
`https://github.com/billhc83/kidscode-link/releases/latest/download/KidsCode.Link.Setup.exe`  
This means updating the HTML once at release instead of each version bump.

**4.3 — Add a `/download` page**
Right now, the only way to discover KidsCode Link is to attempt to flash code and hit the offline modal. Add a `/download` page that explains what KidsCode Link is, system requirements (Windows), what it does (bridges browser to Arduino), and a clear download button. Link it from the sidebar or Help page.

---

## 5. Prioritised Action List

| # | Item | Effort | Risk if skipped |
|---|---|---|---|
| # | Item | Effort | Risk if skipped | Status |
|---|---|---|---|---|
| 1 | Auth-gate `/dev/` routes | Trivial | Medium | ✅ Done 2026-06-26 |
| 2 | Security response headers | Trivial | Medium | ✅ Done 2026-06-26 |
| 3 | Reduce session lifetime | Trivial | Medium | ✅ Done 2026-06-26 |
| 4 | Move companion releases to dedicated repo + `/latest/` URL | Trivial | Low | ✅ Done 2026-06-26 |
| 5 | **Proxy block_saves through Flask (anon key removal)** | **Moderate — 3–4h** | **High** | ✅ Done 2026-06-26 |
| 6 | CSRF protection (`flask-wtf`) | Moderate — half day | High | ✅ Done 2026-06-26 |
| 7 | Privacy Policy + Terms pages + footer links | Moderate (mostly writing) | High — legal | ✅ Done 2026-06-26 |
| 8 | Registration consent checkbox + `agreed_at` DB column | Small | High — legal | ✅ Done 2026-06-26 |
| 9 | Parent consent acknowledgment on student creation | Small | High — COPPA | ✅ Done 2026-06-26 |
| 10 | AI tutor one-time consent modal | Small — 2h | High — COPPA | ✅ Done 2026-06-26 |
| 11 | UUID validation on admin URL parameters | Small | Medium | ✅ Done 2026-06-26 |
| 12 | Password strength minimum (8 chars) | Small | Medium | ✅ Done 2026-06-26 |
| 13 | `/download` page for KidsCode Link | Small — 1h | Low | ✅ Done 2026-06-26 |
| 14 | Persistent rate limiting | Moderate — infrastructure | Medium | ⏸ Deferred — see log |
| 15 | Legacy password hash migration | Moderate — half day + careful testing | Medium | ✅ Done 2026-06-26 |
| 16 | Admin audit logging | Moderate — half day | Medium | ✅ Done 2026-06-26 |
| 17 | Account self-deletion flow | Large — 1–2 days + testing | Medium — legal | ✅ Done 2026-06-26 |
| 18 | Drop `username` column from `activity_logs` | Small | Low | ✅ Done 2026-06-26 |
| 19 | Admin image upload MIME/size validation | Small | Medium | ✅ Done 2026-06-26 |

---

*Generated June 2026 from full codebase review.*
