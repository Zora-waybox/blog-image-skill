# blog-image-skill

[![Validate](https://github.com/Zora-waybox/blog-image-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/Zora-waybox/blog-image-skill/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2)](https://github.com/Zora-waybox/blog-image-skill)

**English** · [简体中文](README.zh-CN.md)

**Aesthetic auto-illustration for blog posts** — a Claude Code / agent-skill plugin by Waybox.

Give it a Markdown or HTML post; it plans the image slots from the post's structure, sources
candidates from **licensed inputs only** (repo asset library, an offline brand card
renderer, optional Pexels/Unsplash or image-gen APIs), scores every candidate with an
**ArtiMuse-style 8-dimension aesthetic rubric** (critique-first, anti-positivity-bias,
composite ≥ 70 + style-fit ≥ 7 gates), exports web-ready `webp/jpg/OG` files, and inserts
hero + section figures **without touching a single word of prose** (insert-only writes,
`.bak` backup, dry-run first, fail closed). Every run emits an `.image-report.md` with
per-dimension scores and license info.

<p align="center">
  <img src="assets/pipeline.svg" alt="blog-smart-images pipeline: Plan → Source → Score → Export → Insert → Report" width="860">
</p>

## Quick start

```
/plugin marketplace add Zora-waybox/blog-image-skill
/blog-image-skill:blog-smart-images content/blog/my-post.md
```

## How it works

1. **Plan** — read the post structure, derive hero / OG / section image slots.
2. **Source** — gather candidates from licensed inputs only (asset library, brand card renderer, optional stock / image-gen APIs).
3. **Score** — grade every candidate with the 8-dimension aesthetic rubric plus a brand style-fit gate; accept only composite ≥ 70 **and** style-fit ≥ 7.
4. **Export** — post-process to web-ready `webp` / `jpg` / OG sizes.
5. **Insert** — write hero + section figures with alt text via insert-only safe writes (`.bak` backup, dry-run first, fail closed); never edits prose.
6. **Report** — emit an `.image-report.md` with per-dimension scores and license info.

## Switchable looks

One post, one line of front matter, a different visual language. Presets steer the
**photo path** — stock queries, gen prompts, grading and the style-fit gate — so the
same pipeline can serve an epic park guide and a quiet essay without you re-teaching
it your taste. (The brand card renderer keeps your card system regardless of preset.)

```yaml
---
title: "Mighty 5 in seven days"
image_style: parks-golden-west
---
```

| Preset | The look | Reach for it when |
|---|---|---|
| `livelike-warm` **(default)** | Golden hour, amber highs and teal shadows, leading-line highways | The blog's home voice — road-trip guides and comparisons |
| `natgeo-doc` | Documentary realism, honest light, true color, weather as subject | The post argues facts: closures, wildlife, border rules |
| `vanlife-film` | Portra-like film curve, morning fog and campfire dusk, candid and lived-in | Community and lifestyle posts, first-person trip diaries |
| `kinfolk-minimal` | Soft overcast, desaturated two-tone, vast negative space | Reflective essays — the coolest of the set, use sparingly |
| `parks-golden-west` | National-park campaign epic: alpenglow, monumental landforms, tiny car for scale | Route guides that need bucket-list pull |
| `ig-editorial` | Punchy teal & orange, bold hooks, crops clean to 4:5 / 9:16 | Social-first posts and OG images |

Unknown preset id? The run warns in the report and falls back to the default rather
than guessing. Adding your own is a copy-paste block in
[`references/style-presets.md`](skills/blog-smart-images/references/style-presets.md):
five fields (light / palette / subjects / composition / mood) plus stock queries, a
gen-prompt core, and negatives.

## What's inside

- `skills/blog-smart-images/SKILL.md` — the workflow (7 steps, hard rules) and the
  Markdown/HTML format table
- `skills/blog-smart-images/scripts/htmlpost.py` — shared HTML primitives, so an
  HTML post gets real heading anchors and `<figure>` inserts instead of silently
  yielding zero figure slots
- `skills/blog-smart-images/references/aesthetic-rubric.md` — the ArtiMuse-derived scoring protocol
- `skills/blog-smart-images/references/style-profile.md` — photo grammar + brand tokens (override per repo)
- `skills/blog-smart-images/references/style-presets.md` — the six switchable looks above (add your own)
- `skills/blog-smart-images/scripts/preview.py` — renders the illustrated post at content width with a filmstrip of every figure, so repetition across the set is visible before publish
- `skills/blog-smart-images/templates/card-base.html` — production-tested brand card layouts (hero, stat cards, countdown, chart, terminal, OG)
- `auto-illustrate.yml.example` + `INTEGRATION.md` — CI drop-in for your blog repo; composes with [cazerme/blog-marketing-skills](https://github.com/cazerme/blog-marketing-skills) (text pass first, image pass second)

## License

MIT — see [LICENSE](LICENSE). Built for roadtripskill.dev; the style profile is swappable, so bring your own brand.
