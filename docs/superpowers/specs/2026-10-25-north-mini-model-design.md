# North Mini Code deployment

User selected `cohere/north-mini-code:free`, then explicitly approved retaining the no-training filter without a ZDR guarantee, with disclosure and fresh owner consent. A real synthetic function-call probe returned HTTP 200, Cohere, cost 0. The ZDR probe returned HTTP 404.

Use the existing adapter with a narrow model-specific function-result transport because this model advertises tools/tool_choice but no response_format. Define only `emit_result`; require exactly one call with that name and validate its JSON arguments using the existing Pydantic schema. Never execute tools, expose reasoning, accept plain-text fallback or weaken evidence/approval checks. Existing schema-capable model behavior stays unchanged.

Require server-side `OPENROUTER_ALLOW_PROVIDER_RETENTION=true` for this exact model. Keep data_collection deny, zero prices, no fallback and existing bounded attempts. Use a new policy identifier for this combination, so previous free/ZDR consents cannot authorize it. Disclose provider retention in settings and outbound preview, displaying current-policy consent accurately. Existing image flow stays ZDR; North Mini Code is text only.

Verify the failing transport/security tests before implementation, then all API tests, typecheck/build, a real synthetic review, ARM Docker build, private AWS deployment, public live review and persisted session/draft checks. Secrets remain outside image/archive/SSM command bodies. No new paid service or top-up is needed for the verified model.
