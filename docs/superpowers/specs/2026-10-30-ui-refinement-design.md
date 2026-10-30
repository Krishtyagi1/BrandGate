# Compact, softer UI with red-and-blue glitter artwork

Date: 30 October 2026
Status: approved on 31 October 2026 with the user's refinement: blurry artwork,
transparent backgrounds and support for both themes. Local preview only.

## Intent

The user finds the UI too blocky and spaced out. Make it more comfortable to
use, generate twisting glowing red/blue glitter assets, and run locally first.
This request does not authorise another production release.

## Approaches

1. Recommended: retain light working screens, add a dark illustrated login hero,
   and use a short artwork accent on a few introductory sections. Tighten spacing,
   soften corners and consolidate bordered groups. This follows the current
   layout while giving the requested artwork a deliberate place.
2. Dark throughout: extend the dark artwork palette into Rules, reviews and
   Tracking. Visually more dramatic, but changes the established reading surfaces
   and needs a broader contrast/interaction review.

Use the compact layout from option 1, with both light and dark appearances. Add a
small theme switch, remember explicit choices locally, and otherwise follow the
system preference. Use the same transparent, softly blurred artwork in both.

## Concrete proposed changes

- Keep the existing Rules / New review / Tracking navigation. Reduce the header
  height from 83px toward 64px; reduce page top padding from 38px toward 24px.
- Reduce typical section spacing from 32px toward 20–24px, with consistent 8px
  increments. Retain enough separation for headings, forms and finding evidence.
- Use a very light cool page background, white reading surfaces, thin subtle
  dividers and 10–14px corners. Remove redundant nested outlines instead of
  wrapping every subsection in another card. Reserve small shadows for menus.
- Keep the existing locally available sans-serif type for controls/body. Replace
  the large serif login headline with a balanced sans-serif heading and concise
  review-focused copy. No external font requests.
- Create a split login: dark glitter artwork hero with readable white copy,
  a simple light sign-in form, and a smaller art header on mobile. Keep image
  decoration outside form fields, source quotations, editor text and error text.
- The user's later refinement supersedes the opaque art direction: use newly
  generated transparent overlays on theme-appropriate backgrounds, with a soft
  display blur. Preserve the original PNGs as unused variants. Keep all text on
  sufficiently quiet backgrounds in both appearances.
- Give page introductions a restrained short art accent where useful; do not
  wallpaper every section. Red is decorative in artwork and remains distinct
  from explicit error text/status badges.
- Make dashboard numbers more compact and related results feel like one grouped
  overview. Keep detailed breakdowns and daily activity easy to expand. Reduce
  repeated framing around the attention list and saved-work list.
- Bound chat history in a readable scroll region, retain source expanders, and
  make the question/action area easy to find. Preserve keyboard access and clear
  focus, disabled states, progress and errors.

Palette proposal: background #F6F7FB, surface #FFFFFF, ink #192238, muted #626C80,
accent blue #3158D5, dark artwork base #050B1B. Red glitter stays in the assets;
validation colours retain explicit text labels. No flashing or continuous glitter
animation; the generated artwork is static.

## Assets and constraints

Generated with the built-in image-generation tool, without people or real photos:

- `apps/web/public/art/red-blue-glitter-hero.png`: portrait twist, dark negative
  space for login text.
- `apps/web/public/art/red-blue-glitter-banner.png`: wide twist for a short
  introductory strip.

Keep originals and prompt provenance in `docs/UI_ASSETS.md`. Before integrating,
select a practical delivery size/format without unnecessarily increasing page
weight. Use local assets, descriptive context in the UI and empty alt text for
pure decoration. No new UI library or product workflow changes are necessary.

## Local verification

Read the installed Next.js CSS/image documentation before editing. Run the actual
app locally at port 3000; use the separate synthetic browser-test app/database
for automation. Inspect desktop and 390px screenshots of login, Rules, document
review/chat and Tracking; check text contrast, focus, overflow and form behavior.
Run existing relevant browser/axe checks, typecheck and production build. Add
behavioral tests only if actual interaction changes warrant them. Keep tests
distinct from model-quality claims. Update implementation notes with exact
commands and outcomes. Do not commit, push or deploy this refresh without the
user's later release instruction.
