---
name: blog-smart-images
description: 'Illustrate a local blog post (Markdown/HTML) end-to-end: plan image slots from the post structure, source candidates from licensed inputs only, score them with an ArtiMuse-style 8-dimension aesthetic rubric + brand style-fit gate, export web-ready webp/jpg/OG files, and insert hero + section figures with alt text using insert-only safe writes and an image report. Use when a post needs a hero image, OG image, section illustrations, or "auto-illustrate the blog" comes up.'
version: "0.1.0"
license: MIT
---

# Blog Smart Images — aesthetic auto-illustration for blog posts

Turn a text-only post into an illustrated one, in the voice of the brand, without
ever touching the prose. Deterministic scripts do every file mutation; your job is
editorial judgment: what each slot needs, which candidate earns the slot, and why.

## Invocation

```
/blog-image-skill:blog-smart-images <path/to/post.md> [--images-dir <dir>] [--max-figures 5]
```

Defaults: `--images-dir images/<post-slug>/` relative to the post; hero + OG + up
to 4 section figures (cap total inline figures at 5, one per ~500–800 words).

## Hard rules (read before anything else)

1. **Licensed sources only.** Candidates may come from: (a) the repo's own asset
   library (`assets/`, `static/`, brand renders), (b) the brand card renderer in
   `templates/`, (c) a stock API with explicit license metadata (Pexels/Unsplash,
   keys in env), (d) an image-gen API if configured. NEVER use social-media
   screenshots, scraped images, or files whose license you cannot name in the
   report. Reference/moodboard folders (e.g. 高光照片) inform style tags only —
   their pixels never enter the post.
2. **Insert-only.** This skill adds front-matter keys, figure blocks, and files.
   It never rewrites, reflows, or deletes existing text. All writes go through
   `scripts/insert_images.py` (dry-run first, then `--write`; creates `.bak`;
   fails closed on any anchor mismatch).
3. **Every image ships with alt text** (descriptive, honest, keyword-aware, no
   stuffing) and a one-line caption unless the surrounding text already captions it.
3b. **Photo-first, no burned-in text.** Hero and section figures are PHOTOGRAPHS
   (real or generated): scenery, roads, people, wildlife — matched to the places
   and content of the section they illustrate, with no text, logos, or UI baked
   into the pixels (captions live in markdown, not in the image). Designed cards
   are allowed only for: the OG/social image (a title there is useful), a slot
   whose content is inherently a diagram (e.g. a chart the text references), or a
   last-resort fallback when every photo path fails the gates — and even then the
   card must stay text-light.
4. **No bare scores.** Every accepted/rejected candidate gets the 8-dimension
   breakdown with a one-line reason per weak dimension (see rubric). Judgments go
   in the report.
5. **Fail closed.** If a step fails twice, stop, leave the post untouched, write
   what happened to the report, and say so.

## Workflow

### Step 0 — Preflight
- Confirm the post file exists and parses (front matter block, heading tree):
  `python3 scripts/extract_slots.py <post> --check`
- Detect available sources: asset library dir(s); `PEXELS_API_KEY` /
  `UNSPLASH_ACCESS_KEY`; image-gen config (`IMAGEGEN_PROVIDER`, `IMAGEGEN_API_KEY`).
  Missing optional sources are fine — the brand card renderer always works offline.
- Read `references/style-profile.md` (brand tokens + subject taxonomy) and
  `references/aesthetic-rubric.md` (scoring protocol). If the target repo carries
  its own `style-profile.md` next to the content dir, it overrides the bundled one.
- Resolve the active look: front-matter `image_style: <preset-id>` →
  `references/style-presets.md`; unknown id ⇒ warn in report, use the default.
  The preset steers the photo path (queries, gen prompts, grading, style-fit);
  the brand card renderer always keeps the brand system.

### Step 1 — Image plan
Run `python3 scripts/extract_slots.py <post> --out image-plan.json`, then refine it
yourself: for each slot (hero, og, one per major H2 up to the cap) write
- `subject`: what the image should SAY (one sentence, from the section's argument —
  not a decoration request);
- `locations`: place names/entities the section actually mentions (Zion, Going-to-
  the-Sun, PCH, a bison, a border crossing…) — these drive stock queries and gen
  prompts so the picture matches the prose, not just the theme;
- `tags`: 3–6 taxonomy tags from the style profile (scene/light/composition/palette);
- `layout` hint if the brand renderer is the likely source (`hero`, `stat-cards`,
  `timeline`, `chart`, `terminal`, `quote`);
- `aspect`: 16:9 for hero/figures, 1200×630 for OG.
Skip slots the text already serves (an existing image, a dense table that IS the
visual). Fewer, better images beat full coverage.

### Step 2 — Source candidates (per slot, in priority order — photos first)
1. **Own photo library** — trip photos / dashcam highlight frames the repo owns
   (`photos/`, `assets/photos/`, or dir passed via `--photo-dir`). Match on the
   slot's `locations` + `tags`.
2. **Stock APIs** (if any key present) — real photography via
   `python3 scripts/fetch_stock.py --query "<locations + tags>" --n 3 --out candidates/`.
   The script chains providers (default order `pexels,unsplash`, override with
   `STOCK_PROVIDER_ORDER`) and fails over automatically when one hits its hourly
   cap (Pexels 190/h, Unsplash 45/h — safety margins under the official free
   tiers, tunable via `*_HOURLY_CAP`) or answers 429/403. Each download gets a
   `.json` sidecar with photographer/license; if the sidecar says
   `credit_caption_required: true` (Unsplash), append its `credit_caption`
   ("Photo by X on Unsplash") to the figure caption.
3. **Image-gen API** (if configured) — prompt = subject + `locations` + preset
   gen-core tokens; run the rubric's AIGC artifact hunt before accepting.
4. **Brand card renderer** (restricted — see rule 3b): OG image, inherently-
   diagram slots, or fallback. `templates/card-base.html` +
   `python3 scripts/render_cards.py --html <filled.html> --frames <ids> --out raw/`.
   Cards must only state facts already present in the post (same no-fabrication
   rule as blog-seo-geo).
Aim for 2–3 candidates per slot when sources allow it. If no photo source is
available at all for a photo slot, prefer leaving the slot empty over filling the
post with text cards — then say so in the report.

### Step 3 — Score (the ArtiMuse pass)
For each candidate, view the image and score it with
`references/aesthetic-rubric.md`: 8 dimensions, 0–100 each, composite = weighted
mean; plus **style-fit 0–10** against the style profile. Protocol highlights:
critique BEFORE scoring (find at least one concrete flaw per image — the
positivity-bias antidote); score the render, not the intention; type-aware
standards (photo vs. designed card vs. AIGC).
**Gates: composite ≥ 70 AND style-fit ≥ 7.** One re-source/re-render round for
failed slots; if still failing, fall back to the brand card renderer, and if even
that fails the gate, leave the slot empty and log it — an empty slot beats a weak
image.

### Step 4 — Post-process
`python3 scripts/postprocess.py --in <winner> --slug <post-slug> --name <slot-name>
[--og]` → 1600w `.webp` (+`.jpg` fallback, target ≤ 150 KB) into the images dir;
`--og` adds the 1200×630 jpg crop.

### Step 5 — Insert (safe writes)
Build `insert-plan.json` (see `examples/`): front-matter keys
(`hero_image`, `hero_alt`, `og_image` — key names configurable per site template),
plus figure blocks `![alt](path "title")` + `*caption*` anchored AFTER named
headings/paragraph fingerprints. Then:
```
python3 scripts/insert_images.py <post> --plan insert-plan.json          # dry-run, prints diff
python3 scripts/insert_images.py <post> --plan insert-plan.json --write  # .bak + atomic write
```

### Step 6 — Report & verify
Write `<post>.image-report.md`: slot table (source, license, 8-dim scores,
style-fit, alt text), rejected candidates with reasons, empty slots, and template
suggestions (e.g. "site template should render hero_image from front matter").
Verify: re-parse the post (`--check`), confirm image paths resolve, eyeball each
final image once more at export size for label collisions or compression artifacts.

## Composing with blog-marketing-skills

Run `blog-seo-geo` BEFORE this skill (it preserves `<img>`/links verbatim, so its
pass is safe on an illustrated post too, but text-first ordering gives it clean
blocks to audit). In CI, chain the two steps; see `.github/workflows/auto-illustrate.yml`
and `INTEGRATION.md` at the plugin root.

## Dependencies

Python 3.10+, Pillow (`pip install pillow`); Playwright + Chromium only when the
brand card renderer is used (`pip install playwright && playwright install chromium`).
Stock/image-gen sources activate solely via env keys — no keys, no calls.
