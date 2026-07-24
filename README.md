# blog-image-skill

[![Validate](https://github.com/Zora-waybox/blog-image-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/Zora-waybox/blog-image-skill/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2)](https://github.com/Zora-waybox/blog-image-skill)

**English** · [简体中文](README.zh-CN.md)

**Aesthetic auto-illustration for blog posts** — a Claude Code / agent-skill plugin by Waybox.

Give it a Markdown post; it plans the image slots from the post's structure, sources
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

## What's inside

- `skills/blog-smart-images/SKILL.md` — the workflow (7 steps, hard rules)
- `skills/blog-smart-images/references/aesthetic-rubric.md` — the ArtiMuse-derived scoring protocol
- `skills/blog-smart-images/references/style-profile.md` — photo grammar + brand tokens (override per repo)
- `skills/blog-smart-images/templates/card-base.html` — production-tested brand card layouts (hero, stat cards, countdown, chart, terminal, OG)
- `auto-illustrate.yml.example` + `INTEGRATION.md` — CI drop-in for your blog repo; composes with [cazerme/blog-marketing-skills](https://github.com/cazerme/blog-marketing-skills) (text pass first, image pass second)

## License

MIT — see [LICENSE](LICENSE). Built for roadtripskill.dev; the style profile is swappable, so bring your own brand.
