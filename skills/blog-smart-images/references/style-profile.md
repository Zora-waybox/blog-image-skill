# Style profile — RoadTrip Navigator blog (override per-repo by shipping your own)

> Looks are switchable: see `style-presets.md` (livelike-warm · natgeo-doc ·
> vanlife-film · kinfolk-minimal · parks-golden-west · ig-editorial). A post picks
> one via front matter `image_style: <preset-id>`; this file defines the default
> (`default_preset: livelike-warm`) and the brand card system, which never changes.

Two layers: a **photo grammar** (what wins when the source is a photograph — stock
or generated) and a **brand system** (what the card renderer uses). Both distilled
from: livelikeitstheweekend.com road-trip guides (editorial reference), the Waybox
readme-hero series (brand DNA), and the Waybox social-aesthetics taxonomy
(高光照片 playbook — used for its TAGS, never its pixels).

## Prime directive

Figures are **photographs of real-feeling scenes** — roads, landscapes, people,
wildlife — chosen to match the places and content of the section (Zion section →
Zion; EV section → charging stop on a coastal highway; wildlife caution → bison on
the road). **Never burn text, logos, or UI into a figure**; words belong in the
markdown caption. The brand card system below exists for the OG image and true
diagrams only.

## Photo grammar (the "livelike" look)

- **Light**: golden hour first — low warm sun, long shadows, layered haze; blue
  hour and storm-light acceptable; flat midday light is a negative.
- **Color**: warm, saturated but not neon; amber/gold highlights, teal-leaning
  shadows (teal&orange), consistent grade across a post.
- **Subjects** (taxonomy tags — combine 2–3 per query/prompt): coastal road ·
  ocean cliff highway · mountain pass / hairpin turns · forest tunnel road ·
  desert highway vanishing point · canyon road · lake reflection · snow road ·
  iconic bridge · dashcam POV · scale contrast (big landscape, small car).
- **Composition**: leading lines and vanishing points; S-curves; natural framing
  (tunnel exits, tree canopies); generous negative space for text overlay on heroes.
- **Mood**: freedom, epic/cinematic, solitude; aspirational but drivable — a road
  you could actually be on.
- **Aspect**: 16:9 hero and figures; 1200×630 OG; portrait only for pin-style extras.
- **Negatives** (auto-cap composition ≤ 60): traffic jams, dirty-windshield smears,
  overexposed white skies, featureless suburbia, visible app UI / watermarks /
  like-counts, AIGC artifacts.

## Brand system (card renderer tokens)

- Surface: espresso `#16100a → #241609` gradient; vignette + 5% film grain.
- Ink: cream `#f2e5d0`; muted `#c9ab86`; faint `#8a6f52`.
- Accents: gold `#e8b26a` (decor/headline), data amber `#bd843c`, teal `#1f9e85`
  (chips, charge/positive markers) — the amber/teal data pair validates for CVD
  on the dark surface.
- Type: serif display (Liberation/DejaVu Serif — italic for editorial emphasis) +
  mono caps labels with wide tracking.
- Motifs: dashed route line with numbered stop dots; booking-countdown rows;
  terminal window; Waybox teal pill bottom-right; footer strip
  `ROADTRIP NAVIGATOR · ROADTRIPSKILL.DEV`.
- Voice on cards: verdict-style lines ("A date is advice."), mono caps kickers,
  facts only from the post being illustrated.

## Similar published looks (for stock queries / gen prompts)

golden-hour American West editorial (think national-park tourism campaigns),
teal&orange cinematic road photography, vanlife documentary, large-format
landscape with tiny vehicle for scale. Avoid: clip-art, flat corporate vector
people, pastel minimalism (off-brand here).
