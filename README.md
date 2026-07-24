# blog-image-skill

**Aesthetic auto-illustration for blog posts** — a Claude Code / agent-skill plugin by Waybox.

Give it a Markdown post; it plans the image slots from the post's structure,
sources candidates from **licensed inputs only** (repo asset library, an offline
brand card renderer, optional Pexels/Unsplash or image-gen APIs), scores every
candidate with an **ArtiMuse-style 8-dimension aesthetic rubric** (critique-first,
anti-positivity-bias, composite ≥ 70 + style-fit ≥ 7 gates), exports web-ready
`webp/jpg/OG` files, and inserts hero + section figures **without touching a single
word of prose** (insert-only writes, `.bak` backup, dry-run first, fail closed).
Every run emits an `.image-report.md` with per-dimension scores and license info.

```
/plugin marketplace add Waybox-AI/blog-image-skill
/blog-image-skill:blog-smart-images content/blog/my-post.md
```

- `skills/blog-smart-images/SKILL.md` — the workflow (7 steps, hard rules)
- `references/aesthetic-rubric.md` — the ArtiMuse-derived scoring protocol
- `references/style-profile.md` — photo grammar + brand tokens (override per repo)
- `templates/card-base.html` — production-tested brand card layouts (hero, stat
  cards, countdown, chart, terminal, OG)
- `.github/workflows/auto-illustrate.yml` + `INTEGRATION.md` — CI drop-in; composes
  with [cazerme/blog-marketing-skills](https://github.com/cazerme/blog-marketing-skills)
  (text pass first, image pass second)

MIT. Built for roadtripskill.dev; the style profile is swappable — bring your own brand.
