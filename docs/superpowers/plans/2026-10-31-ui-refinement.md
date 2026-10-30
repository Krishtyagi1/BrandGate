# Compact UI and Transparent Artwork Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make the app less blocky and spaced out, with soft transparent glitter art and usable light/dark themes, verified locally.

**Architecture:** Keep the existing three-tab workflow and backend contracts. Add a small appearance control, theme tokens and a final refinement stylesheet; use locally generated transparent assets through Next's image pipeline. Preserve real editor/evidence surfaces and approval states.

**Tech Stack:** Existing Next.js/React/TypeScript/CSS, Next Image, Playwright/axe, built-in image generation.

**Spec:** `docs/superpowers/specs/2026-10-30-ui-refinement-design.md`, approved with the 31 October transparency/blur/both-theme refinement.

## Global Constraints

- Run locally first; do not commit, push or deploy the refresh.
- Preserve all backend approval, privacy and source-evidence behavior.
- No real-person photos, new UI library, remote fonts or continuous glitter animation.
- Keep original generated variants; save transparent edits as sibling files.
- Continue in this authorised project folder; preserve existing work and local sessions.

## Review Focus

- Theme choice persists on reload and remains usable when browser storage fails.
- System preference has a safe initial value without a hydration mismatch.
- Artwork has actual alpha, quiet text areas and no pointer/focus interference.
- Dense layouts retain touch targets, source readability and 390px overflow safety.
- Dark mode preserves meaningful notices, focused controls and the document editor's readable paper.

### Task 1: Assets and appearance behavior

**Files:** generated sibling PNGs under `apps/web/public/art/`; `components/theme-toggle.tsx`, `app/layout.tsx`, `components/auth.tsx`, `components/workspace.tsx`; `scripts/test-theme-ui.mjs`.

- [x] Verify actual alpha in generated edits and record prompts/provenance.
- [x] Add browser tests for theme switching, reload persistence, system preference and unavailable storage; confirm they fail before implementation.
- [x] Add safe pre-paint theme selection and a labelled control on login/workspace; theme selection changes styling only.
- [x] Run theme tests to green, including login form/register navigation and axe scans.

### Task 2: Compact local visual refresh

**Files:** `app/refinement.css`, semantic-token adjustments to `app/simple.css`, `components/auth.tsx`, `components/ui.tsx`, `components/document-chat.tsx`, `docs/UI_ASSETS.md`.

- [x] Reduce header/page/section spacing; remove redundant outlines and soften surface grouping without hiding labels/actions.
- [x] Integrate transparent art on login and short page introductions, with blur/opacity appropriate to both themes.
- [x] Group dashboard summaries more tightly and bound chat history with an accessible scroll region.
- [x] Inspect desktop/mobile screenshots and both themes; fix contrast, overflow and layering defects.

### Task 3: Verify and hand over local preview

- [x] Run `npm run typecheck`, `npm run build`, theme checks and existing synthetic workflow/browser/axe checks.
- [x] Request a focused read-only review of theme lifecycle and accessibility; fix material issues with regressions where behavioral.
- [x] Update implementation status/decisions with commands, outcomes, asset paths and limits; leave local app available at port 3000.

## Progress ledger

Plan and design read. User authorised implementation (“yes”) with transparency,
blur and both-theme refinements. In-place execution follows the existing build
ledger; no commit/push/deployment. The local API (8000) and web (3000) were
started in the preceding turn. Generated original variants remain untouched.


Completion — 31 October 2026: transparent alpha verified on both new PNGs;
initial theme behavior test failed on the absent control, then passed after
implementation. Seven appearance checks/four selected axe scans passed. Expanded
workflow 38 checks/16 selected axe scans passed. Dark evidence contrast failed
first and passed with semantic foregrounds; the blocked-storage sign-in reset
failed first and passed with browser in-memory state. Cross-tab sync and system
preference changes passed. DOCX probes 4/4 passed in light and 4/4 in dark.
Typecheck, final production build and diff whitespace check passed. Desktop and
390px screenshots inspected. Independent read-only review's material findings
were fixed; no deferred material findings. No deployment/commit/push.

Ruling: retain the current DOCX paper and document colours in both appearances;
cost if wrong is less visual uniformity, chosen to protect document readability.
Ruling: in-memory theme fallback lasts for client navigation when storage fails;
a full reload may use the system preference, which is documented rather than
claiming persistence that unavailable storage cannot provide.
