# Brand Content Review — confirmed workflow redesign

Date: 24 October 2026. User asked to build and answered the clarification questions. This document records that requested workflow and the implementation choices below; it is not a completion report. Existing build authorisation, free-only OpenRouter, project-only writes and company privacy requirements continue.

## Confirmed intent and choices

Make company knowledge setup and everyday review understandable without exposing internal rule administration. Title: **Brand Content Review**. White interface, dark text, restrained borders, three main tabs: **Rules**, **New review**, **Tracking**. Team/account/privacy controls remain in a secondary Settings menu. Preserve existing data, accounts and human approvals.

Rules is **one page with all setup sections visible**, as selected by the user. The alternative short wizard was rejected. A full document editor/dashboard replacement would add unnecessary interaction; retain the existing editor and approval backend behind the simpler shell.

A company selects its default checks once: Products & prices, Claims & facts, Tone, Language & terminology, Required wording, Colours & fonts, Logos & visual examples, Accessibility. Several source documents and separately uploaded logos/images form one collection. Evidence can be integrated across sources; each individual file need not contain every category. Missing guidance is reported for that requested category, while supported categories proceed. Distinguish “Source missing” after completed extraction from “Not checked” after incomplete reading/provider failure.

Users upload additional sources into the **same visible version**. New or overlapping rules are staged as proposals. A human reviews proposed fields/excerpts and explicitly confirms additions/replacements before authoritative rules change. Overlap uses stable fact identity, including product/currency/unit/effective dates; changing INR 100 to INR 150 shows old/new evidence and requires replacement confirmation. A generic source upload never silently replaces prices. Explicit **New version** starts empty, including its sources/rules/check defaults; old versions remain available.

Static images, advertisements and social posts receive evaluation only. No image rewriting. Video is explicitly unsupported. Editable text retains compare/apply/save/recheck corrections with references. Every source-based conclusion and correction shows its actual approved text excerpt or reference image; missing evidence is labelled and never given an invented citation.

## One-page workflow

Rules page sections: (1) “What should we check?” defaults plus optional expectations, (2) “Company sources” multi-document/image uploads and coverage, (3) “Review what was found” proposed values with highlighted literal excerpts, old/new comparison, include/exclude controls and one explicit confirmation action, (4) confirmed current rules with edit/history disclosures. Source cards show filename, page/paragraph, excerpt and image when available. Do not dump 30 arbitrary paragraphs into the rule list. Existing manual rules remain supported with truthful “Company-entered rule” provenance.

New review: choose Email, Social media, Ads & visuals, Website, Documents or Other; Social media additionally selects LinkedIn, Instagram, X, Facebook, Threads, TikTok, YouTube or Pinterest. Format and publication destination are independent: social posts can include images. Every category/platform has hover/focus/tap help describing actual accepted inputs. Paste text or upload DOCX/PDF/PNG/JPEG. Show company check defaults, allow a subset and optional task instructions. Save selected checks and instructions with the draft/review; they cannot authorise or override approved facts.

Review workspace keeps document/text/original image alongside findings. Each requested category reports Checked, Issues found, Source missing, Unsupported or Not checked. A check lacking sources must never be counted as passed. Selected text corrections are explicitly applied and rechecked. Images show reference/candidate regions and evidence, with uncertain visual/font identity marked advisory. Reviewer control remains exact-version/hash-bound and excludes self-approval.

Tracking combines the content library, status filters and assigned approvals; opening an item exposes findings, comments and revision/decision history. No extra overview/activity/insights tabs. Old URLs resolve to useful equivalent views without deleting records.

## Tutorial and realistic sample

First sign-in after this feature offers a one-time, dismissible example tutorial; replay from Help. No mandatory tour blocking ordinary work. A separate fictional example creates Northstar Botanics sources, an approved-price paragraph, explicit voice/palette guidance, a logo/reference graphic and deliberately incorrect copy. Guide through selecting checks, seeing source coverage, confirming rules, reviewing content, applying a text correction and seeing Tracking. Sample results are actual current checks or clearly labelled instructional examples; never disguised mock AI. Tutorial completion is persisted per user. Company materials are never silently mixed with sample knowledge.

## Implementation choices and boundaries

Reuse Next.js/FastAPI/PostgreSQL, existing RLS, sessions, AG-UI, local browser DOCX editor, citations and approvals. Add immutable **knowledge snapshots** underneath the visible version. Each confirmed change creates a snapshot of approved rules/assets/defaults. Review/preview/rewrite/approval pins include snapshot identity; updates invalidate pending requests and mark earlier checks stale, including updates during a running job. Legacy review data is backfilled to its historically immutable version rules; no history is rewritten to a new price.

Intake uses bounded source extraction and background AI proposals validated against literal stored excerpts. Process the full supported source collection in bounded chunks, with visible progress and request-budget limits. Search/coverage uses the aggregate collection; unsuccessful/partial chunks are not treated as absent guidance. Existing limits are disclosed; target source intake up to 100 PDF pages/200,000 extracted characters initially, 5 MB per file. Users can split larger sources and add them to the same version. No silently truncated first-30-section authority.

Visual sources: uploaded PNG/JPEG references and extractable DOCX/PDF images, linked to immutable source IDs/page/part. Local palette comparison/OCR supports verifiable fields. Free vision inference requires capability, zero pricing and the current ZDR/no-collection controls; otherwise show the precise unavailable category while running supported checks. Do not infer an exact font family from image pixels as a confirmed fact. Raw source images require explicit outbound preview and consent; text-only redaction does not protect an image. No paid/privacy fallback.

## Required verification

Meaningful regression checks cover aggregate sources with a missing category, malformed/forged excerpts, partial intake, same-visible-version price replacement requiring confirmation, stale approval/rewrite after snapshot changes, clean history, empty new versions, tenant isolation, selected-check/task persistence, image-reference comparisons, unsupported video, tutorial isolation/idempotency and no self-approval. Browser checks cover the three-tab white flow, information help on focus/tap, source highlighting, explicit confirmation, text correction/recheck and Tracking. Tests label synthetic providers and preserve real route failures. Existing 79 backend tests remain a regression baseline, not proof of the new workflow.
