# UI artwork provenance

## 31 October: button accent assets and consistent controls

Generated with the built-in `image_gen` tool with `transparent_background=true`.
No photos, people, brand documents or credentials were supplied. Each original
2172 × 724 RGBA PNG is retained in the generated-image output directory. The app
uses resized 1086 × 362 transparent WebP copies (quality 85) for fast loading. CSS composites
the artwork beneath a strong surface tint; button labels remain live text.

### button-ribbon

File: `apps/web/public/art/button-ribbon.webp`

Final prompt:

Use case: stylized-concept. Asset type: transparent decorative texture behind an interactive web button, wide horizontal composition about 4:1. Generate a refined very soft glowing cobalt-blue and ruby-red ribbon of microscopic glitter, gently twisting together, luminous blue toward one end and crimson toward the other, lots of empty transparent space across the middle for a readable button label. Diffused edges fade completely into genuine transparency. Restrained premium atmosphere matching a clean brand governance app with blurry red and blue streak hero artwork. The two wisps lie mainly along the bottom-left and top-right edges. No solid background, no rectangle, no border, no actual button, no text, no logo, no icons, no people, no watermark. Smooth soft bloom and subtle particles, not sharp fireworks. Actual transparent background required.

### button-halo

File: `apps/web/public/art/button-halo.webp`

Final prompt:

Use case: stylized-concept. Asset type: transparent abstract halo texture for quiet secondary UI buttons and panel accents, horizontal composition about 4:1. A sparse fine mist of blue and red glitter with two very blurry curved light wisps, an airy cobalt-blue glow and a smaller ruby-red glow, low density and soft edge transparency. Keep the central 65 percent almost empty transparent so text overlays remain readable. Elegant understated companion to glowing red-blue ribbon artwork. Fully transparent surrounding background. No solid background, no rectangle, no border, no actual button, no text, no logo, no icons, no people, no watermark. No crisp starbursts; diffuse silk-like glowing particles only.

## 31 October refinement: transparent soft overlays (active variants)

The user requested blurry artwork and transparent backgrounds for both themes.
These edits were generated with the built-in `image_gen` tool with
`transparent_background=true`, referencing the original generated PNGs below.
Both files were inspected and verified as RGBA with fully transparent negative
space and partially transparent glow pixels. The app displays them through Next
Image with an additional static CSS blur and theme-appropriate opacity. The
original opaque variants remain unused alternatives. No people or actual photos
were provided or generated.

Active files:

- `apps/web/public/art/red-blue-glitter-hero-soft.png` (1122 × 1402)
- `apps/web/public/art/red-blue-glitter-banner-soft.png` (2172 × 724)

Final hero edit prompt:

Edit this portrait artwork into a reusable translucent UI background overlay. Preserve the elegant twisting crimson-red and electric-blue ribbons and their overall S-curve arrangement. Remove ALL the black/navy background and replace it with genuine transparent alpha, including all empty negative space. Soften and defocus the ribbon edges and glitter particles into luminous frosted light trails with a moderate soft-focus blur, no hard star-shaped glints, while retaining recognisable delicate glitter texture and the red/blue twisting form. Feather the outer glow naturally into transparent pixels; no dark halo or white matte. Keep the left and upper-left mostly empty and fully transparent for UI copy. Designed to look good composited onto BOTH pale light-theme and midnight dark-theme surfaces. No checkerboard baked into the image, no text, no logos, no people. Output a portrait PNG with genuine transparency.

Final banner edit prompt:

Edit this wide red-and-blue glitter ribbon artwork into a softly blurred TRANSPARENT decorative background overlay. Preserve the wide horizontal twisting ribbon shape and red/crimson and electric/cobalt blue palette. Remove the entire dark navy/black backdrop completely; all negative space must be genuine transparent alpha. Defocus the glitter and luminous strands into a soft dreamy glow, with blurred feathered edges, gentle fine particle texture and no sharp starburst spikes. Keep the upper-left and left-center mostly empty and transparent for web section headings. No dark or white matte, no solid-colored background, no checkerboard baked in. Make the glow translucent and feather it into alpha so this same PNG blends equally well over pale light-theme and deep dark-theme web surfaces. No text, logos, people or interface. Maintain the panoramic landscape composition.

## Original variants

Generated on 30 October 2026 with the built-in `image_gen` tool. Original PNGs
are copied into the project. No real-person images, reference photos or company
documents were supplied. The artwork contains no embedded UI text or logos.

## Portrait glitter hero

File: `apps/web/public/art/red-blue-glitter-hero.png`

Final prompt:

Use case: stylized-concept. Asset type: portrait background artwork for a premium document-review app login hero, approximately 4:5 portrait composition. Primary request: glowing red and electric blue streaks of glitter twisting together. Scene: deep midnight navy, almost black background. Subject: two elegant thin flowing ribbons made from thousands of tiny luminous glitter particles, one vivid crimson-red and one cobalt/electric-blue, twisting around one another in a loose sculptural S-curve, with a few sharp sparkling fragments and a delicate light trail. Rich luminous color, finely resolved glitter grains, restrained bloom, high contrast, beautiful depth, polished abstract photographic light sculpture. Composition: the luminous twist mostly in the lower-right and middle-right, quiet dark negative space across the upper-left and left-center for readable website text. Ribbons extend out of frame naturally. No text, no lettering, no logo, no people, no objects, no interface, no border, no watermark. Actual artwork asset, not a website mockup.

## Wide glitter banner

File: `apps/web/public/art/red-blue-glitter-banner.png`

Final prompt:

Use case: stylized-concept. Asset type: wide panoramic decorative website section background, approximately 3:1 landscape. Primary request: glowing crimson red and electric blue streaks of glitter twisting together on a deep midnight navy background. Two slender fluid particle ribbons weave around each other horizontally in a loose elegant twist, with fine sparkling grains, a few bright tiny star glints, rich restrained glow, and depth like a long-exposure abstract light sculpture. Concentrate the intertwined glitter streaks in the right half and along the lower edge, fading into ample clean dark negative space across the left half for a short heading. Beautiful crisp detail; energetic but uncluttered. Related in look to a luxurious dark red-and-blue glitter login hero. No text, letters, logo, UI, frames, people, objects, or watermark. A finished reusable bitmap background asset, not a mockup.
