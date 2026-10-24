# Northstar Botanics — sample brand guidelines

**Fictional demonstration material.** This company, product, price and supporting facts are invented for testing Inkloom. They are not evidence about any real product. Version 1; sample effective date: 1 January 2026.

## Brand and product

- Brand spelling: **Northstar Botanics**.
- Product name: **Cloudberry Daily Cleanser**.
- Product size: **150ml**.
- Sample approved price: **INR 799 per 150ml**, effective 1 January 2026. Compare prices only when the product, currency, unit and effective period match.
- Approved benefit: **A gentle rinse-off cleanser that removes surface oil.**
- No clinical trial results, medical treatment claims, guaranteed outcomes or competitor rankings are approved in this sample.

## Voice and terminology

Write in a calm, clear and helpful voice. Use short sentences and specific wording. Avoid fear, exaggerated promises, shouting and unnecessary urgency. Preserve the creator's purpose when proposing a correction.

Prohibited wording:

| Wording | Suggested direction |
|---|---|
| `miracle` | Describe the approved cleansing benefit. |
| `guaranteed` | State only the approved factual benefit, without promising an outcome. |
| `cure acne` | Remove the treatment claim; this sample has no supporting clinical evidence. |

Required exact disclaimer on sample product content:

> Results vary. Read the product label before use.

## Channel and accessibility guidance

For Instagram, use a concise caption, one clear call to action and at most three relevant hashtags. These are contextual guidelines, not a guarantee of automatic enforcement.

Use descriptive link labels and plain language. Do not communicate essential meaning through emoji or colour alone. Supply meaningful alt text for informative images. The current prototype reviews text and verified image transcripts; a human must inspect image appearance and layout.

## Sample visual references — manual inspection

- Primary colour: teal `#167569`.
- Main text colour: ink `#162841` on a white or pale background.
- Suggested font: Arial or another legible sans-serif.
- Keep the wordmark readable and proportional. Do not stretch it or place it on a busy background.

These are fictional visual directions, not a claim that automatic logo/font/contrast checks have been implemented.

## How to use this sample

1. Open **Brand knowledge** in your `newcomp` organisation. Sample rules were added to its existing empty Version 1 draft.
2. Review the sample rules, approve the ones you accept, then activate the version. Draft rules are not used by reviews.
3. Start a content review and paste `review-with-issues.txt`.
4. Save, inspect the outbound payload, then start the check. The API key and processing policy must be configured. A free-provider capacity error remains an incomplete check.
5. Compare findings with the expectations below. Edit manually or explicitly apply a safe correction, then save and recheck.
6. Use a different authorised reviewer for final content approval.

### Deliberately problematic example

See `review-with-issues.txt`. Expected deterministic findings after rule activation: wrong sample price, three prohibited phrases and missing exact disclaimer. A promise such as “cure acne in 24 hours” also needs evidence; it must not be presented as a verified factual conclusion. Tone findings depend on actual model output.

### Corrected example

See `review-clean.txt`. It uses the exact product/size/price, approved benefit and required disclaimer. It is a useful control, not a pre-certified AI pass. A real check and human review are still required.

`northstar-rules.json` contains the matching reusable rule definitions, initially unapproved. Editing these local files does not automatically change the application's saved rules.
