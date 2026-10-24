# External components and reuse disclosure

## Application and assistance

Inkloom application source and documentation were created/modified with substantial OpenAI Codex assistance, including design, implementation, synthetic fixtures and automated checks. Earlier foundation code in this same project is reused and extended; historical checkpoints are recorded in `docs/IMPLEMENTATION_STATUS.md`. No interviews, independent user feedback, official event dates or participant contributions are invented.

Application-authored source is offered under GNU AGPLv3 (`LICENSE`) following the user's approval. Third-party code keeps its own copyright and licence. The project-local frontend design skill is reused guidance from Anthropic's public skills repository; it is not an application template. Standard framework scaffolding, APIs and libraries are disclosed below.

## Main components

| Component | Actual role | Licence/source disclosure |
|---|---|---|
| Next.js, React, TypeScript | Web interface and same-origin API proxy | MIT / Apache-2.0 as specified by installed packages |
| FastAPI, Pydantic, HTTPX | API validation, sessions/business endpoints and provider HTTP | MIT / BSD-3-Clause as specified by installed packages |
| PostgreSQL, psycopg | Durable records, transactions, tenant RLS | PostgreSQL licence; psycopg LGPL-3.0 |
| embedded-postgres | Project-local development database launcher | Installed package licence; beta npm wrapper, not hosted infrastructure |
| LangGraph / LangChain components | Bounded review graph | MIT; tracing disabled by launchers |
| Official AG-UI Python and TypeScript SDKs | Typed persisted progress streaming | MIT; events cannot authorise business decisions |
| SuperDoc **2.26.0** | Self-hosted browser Word-style editing | AGPL-3.0; retained notice in `docs/licenses/SUPERDOC-NOTICE` |
| @superdoc/docx-engine **0.25.0** | SuperDoc dependency for DOCX processing | **Proprietary, separately licensed**, not open source. Retained licence/notice in `docs/licenses/`. Current integration uses public SuperDoc APIs; no reverse engineering or substitute engine. Review its terms for any redistribution/deployment. |
| pypdf, python-docx | PDF extraction; DOCX fixture/source tools | BSD-3-Clause / MIT respectively |
| Pillow **13.0.0** | Bounded local image decoding | HPND-style Pillow licence |
| Windows.Media.Ocr | Optional local OCR through PowerShell | Windows platform component; installed engine/language required |
| pdfjs-dist **5.4.296** | Pinned editor PDF dependency | Apache-2.0; root override avoids the identified later-version advisory range |
| Argon2, Playwright, axe-core, Ruff | Password hashing, browser/accessibility checks, lint | Installed package terms apply |
| Lucide | Interface icons | ISC |

Exact JavaScript versions and transitive licences are in `package-lock.json` and installed package metadata; Python versions are pinned in `services/api/requirements.txt`. Original notices are preserved by package installation. The app licence does not relicense the proprietary engine or company materials.

## AI service and data

OpenRouter is the external inference router. Configuration accepts only free routes with enforced zero-price/ZDR/no-collection controls and schema support. A successful synthetic review used `xingchen-agi/xing4.0-29b-a4b:free`, endpoint provider **Phala**, reported cost **0**. Provider/model identity is saved on successful runs. This is an observed successful route, not an availability guarantee or local model.

No fine-tuning, company-data training or outside dataset purchase was performed. Tests and the 50-case evaluation set use fictional developer-labelled content. Offline provider doubles are explicitly marked and do not measure model accuracy. Real company files and API keys are not submission/source artifacts. Privacy controls and remaining limits are described in `docs/ARCHITECTURE.md`.

The latest npm audit retained four transitive AG-UI/Zod advisory entries after the PDF dependency override. They were not suppressed or fixed with an unverified incompatible major upgrade. No vulnerability-free or production-security claim is made.
