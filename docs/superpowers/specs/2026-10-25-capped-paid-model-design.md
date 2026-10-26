# Capped paid text model

The user approved up to USD 1 for a working model and chose to add OpenRouter's minimum USD 5 prepaid balance. These are separate amounts; app inference must remain capped at USD 1.

## Approach
Retain OpenRouter and its existing structured-output, redaction, evidence and owner-consent flow. A free route currently returns upstream 429. AWS Nova probes returned daily-token throttling and zero account quotas; a new provider integration would not resolve access. Select the explicit low-cost `google/gemini-2.5-flash-lite` for text only, after a real successful probe. Free routing remains the default.

An explicit `OPENROUTER_PAID_BUDGET_USD=1` opts into capped paid text inference. Accept only that model with catalogue input/output prices at most USD 0.10/0.40 per million tokens. Before every paid request, read the key metadata and reject absent, resetting, exhausted, or greater-than-USD-1 total caps. Reserve USD 0.02 of remaining cap for each bounded request. Retain ZDR/no-training routing, JSON schema, no fallback, 2500 output tokens and ten-attempt session limit. Paid image inference is outside this change; existing free vision selection remains unchanged.

Use a new paid policy version so previous free-processing consent does not authorize paid processing. UI identifies the selected model and avoids claiming every route is free. Never include keys in source archives, Docker images, command payloads or reports. Transfer the secret via a temporary encrypted SSM parameter and remove its narrowly scoped permission afterward.

## Verification
Tests reject paid mode by default, excessive prices, missing/resetting/over-budget key caps and insufficient remaining budget before dispatch. A contract test checks price ceilings, privacy flags and structured validation. Then run all API tests, typecheck/build, container build, secure AWS rollout and a real public synthetic review. Record provider failures honestly; no automatic approval and no model-accuracy claim.
