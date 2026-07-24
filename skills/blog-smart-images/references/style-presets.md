# Style presets — switchable looks for the image pass

How selection works (checked in this order):
1. Post front matter: `image_style: <preset-id>` — per-post override.
2. Repo-level `style-profile.md` naming a `default_preset`.
3. Fallback: `livelike-warm`.

Every preset supplies the same five blocks the workflow consumes: **light / palette /
subjects / composition / mood**, plus ready-to-use **stock queries**, a **gen-prompt
core** (for the image-gen path), and **negatives** (auto-cap Composition ≤ 60 in the
rubric). The brand card renderer keeps the Waybox espresso/amber system regardless of
preset — presets steer the PHOTO path (stock/gen/own-photo selection and grading).
Score with the same 8-dimension rubric in `aesthetic-rubric.md`; only style-fit is
judged against the active preset.

---

## livelike-warm (default)
The blog's home look — see `style-profile.md` photo grammar.
- light: golden hour, long shadows, layered haze; blue hour ok
- palette: amber/gold highs, teal-leaning shadows, saturated-not-neon
- subjects: coastal road, desert vanishing point, canyon, lake reflection, dashcam POV
- composition: leading lines, S-curves, natural framing, text-safe negative space
- mood: freedom, cinematic, drivable-aspirational
- stock: "coastal highway golden hour aerial", "desert road sunset vanishing point"
- gen core: "editorial travel photograph, golden hour low sun, warm amber grade, teal shadows, leading-line highway, cinematic, no people close-up"
- negatives: flat midday light, traffic, washed skies, suburbia

## natgeo-doc
Documentary realism — for posts arguing facts (closures, wildlife, borders).
- light: honest natural light, any hour; weather as subject
- palette: neutral-warm, true-to-life saturation, minimal grading
- subjects: wildlife crossings, rangers/gates, storm fronts, real road conditions
- composition: decisive-moment framing, environmental context, eye-level
- mood: witness, credibility, scale of nature
- stock: "bison crossing road yellowstone", "mountain pass snow gate closed sign"
- gen core: "documentary photograph, natural light, true color, photojournalism, environmental storytelling"
- negatives: heavy filters, HDR halos, staged stock-smile scenes

## vanlife-film
Film-emulation road life — for community/lifestyle posts.
- light: morning fog, campfire dusk, window light
- palette: Portra-like film curve, soft warm mids, gentle grain welcome
- subjects: camper interiors, coffee on tailgate, roadside camps, hands on wheel
- composition: candid, lived-in clutter ok, 35mm feel
- mood: cozy, unhurried, first-person
- stock: "campervan morning fog forest film photo", "road trip coffee tailgate candid"
- gen core: "35mm film photograph, portra grain, candid vanlife scene, soft morning light"
- negatives: sterile showroom vans, influencer-posed shots

## kinfolk-minimal
Cool minimal editorial — for reflective/philosophy-of-travel posts (use sparingly; coolest of the set).
- light: soft overcast, open shade
- palette: desaturated, cool-neutral, two-tone restraint
- subjects: single road in fog, lone signpost, empty motel, one object
- composition: huge negative space, centered or rule-of-thirds single subject
- mood: quiet, contemplative
- stock: "empty road fog minimal", "lone motel sign overcast"
- gen core: "minimal editorial photograph, soft overcast light, desaturated palette, vast negative space, single subject"
- negatives: busy frames, warm saturation (off-preset), clutter

## parks-golden-west
National-park campaign epic — for route-guide posts (Mighty 5, Going-to-the-Sun).
- light: saturated golden hour, alpenglow, god rays
- palette: deep ambers, red rock, indigo dusk sky
- subjects: monumental landforms, switchbacks from above, tiny car/figure for scale
- composition: grand vista, high vantage, foreground anchor
- mood: awe, bucket-list pull
- stock: "zion canyon golden hour grand vista", "switchback mountain road aerial sunset tiny car"
- gen core: "epic landscape photograph, national park tourism campaign style, golden hour alpenglow, monumental scale, tiny vehicle for scale"
- negatives: flat postcard light, crowds, visitor-center framing

## ig-editorial
The IG/TikTok viral travel look — distilled from the Waybox 高光 taxonomy (screenshots
inform TAGS only; never reuse their pixels). For social-first posts and OG images.
- light: punchy golden hour or bold blue hour; tunnel-exit glow
- palette: hard teal&orange, lifted saturation, crisp contrast
- subjects: Big-Sur-type bridges, turquoise coves, red-rock tunnels, milky-way roads
- composition: strong hook in first glance; center-punch or hard leading line; crops well to 4:5/9:16
- mood: "add to bucket list" impulse
- stock: "bixby bridge sunset drone", "utah red rock tunnel road", "turquoise cove coastal road"
- gen core: "viral travel photograph style, punchy teal and orange grade, bold golden hour, dramatic composition, social-media hero shot"
- negatives: UI overlays/watermarks (hard reject), muddy midtones, tilted horizons

---

Adding a preset: copy any block, give it an id, fill the five blocks + queries +
negatives. Keep ids kebab-case. If a post names an unknown preset, warn in the
report and fall back to the default rather than guessing.
