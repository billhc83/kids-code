# `/try` Welcome Splash Overlay — Design Spec

Status: approved

## Context

`templates/try_it_builder.html` already has a step-1-completion email-gate overlay
(`#try-email-gate-overlay`, see [`2026-07-09-try-page-infra-design.md`](2026-07-09-try-page-infra-design.md)).
This spec adds a second, earlier overlay: a one-time welcome/marketing splash shown the
instant `/try` loads, before any interaction with the builder.

## Goal

Greet the anonymous visitor, thank them for their interest, set expectations (no signup
needed to try it), and leave the door open for questions — before they touch the builder.

## Design

- New overlay `#try-welcome-overlay` in `templates/try_it_builder.html`, structurally
  identical to the existing `#try-email-gate-overlay` (fixed, full-screen,
  `rgba(13,17,23,0.85)` backdrop, white rounded card, same font/color tokens already used
  in that modal). No new CSS classes — inline styles matching the existing overlay's
  pattern.
- Copy:
  - Heading: "Welcome to KidsCode! 👋"
  - Body: thanks the visitor for checking KidsCode out, notes this is a real lesson and no
    signup is required to try it, invites questions ("Got questions? We'd love to hear
    from you.") — generic, no specific contact address.
  - Single button: "Let's build! 🚀" — dismisses the overlay.
- Shown immediately on page load (inline script near the top of `<body>`, not gated on
  the block builder finishing loading), so it sits on top of a still-loading builder.
- Dismissal is remembered via `sessionStorage.getItem('try_welcome_dismissed')` — set on
  button click, checked before display. Reappears on a fresh browser session, same
  session-scoping the email gate already uses (that one uses the Flask session; this one
  has no server round-trip so `sessionStorage` is the natural equivalent).
- Purely client-side: no new route, no CSRF concern (no POST), no interaction with the
  existing email-gate logic — this overlay is earlier in the funnel and fully independent
  of it.

## Explicitly out of scope

- Any server-side tracking of splash views/dismissals.
- A/B testing different copy.
- Reusing this overlay pattern on other pages (e.g. `splash.html`).
