# Changelog

Notable changes to this project. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `scripts/preview.py` — renders an illustrated post to a standalone HTML preview
  at content width, with a filmstrip of every figure in document order. Figures
  are scored one at a time but read in sequence, so repetition (two identical
  compositions, three consecutive sunsets, a hero the first figure echoes) is
  invisible until the set is seen together. Wired into SKILL.md Step 6. Uses
  `markdown` when installed and a built-in converter otherwise; warns about image
  paths that do not resolve.

## [0.1.1] — 2026-07-24

### Fixed

- `fetch_stock.py` now sends a `User-Agent`. Pexels sits behind a CDN that answers
  403 to the default `Python-urllib` agent, and the failover logic reported that as
  rate limiting — so a run with a valid Pexels key silently completed on Unsplash
  instead, picking up its mandatory-credit obligation along the way. If you have a
  Pexels key, this is the difference between it working and it never being used.
- The plugin zip packaged a CI workflow that still cloned the old `Waybox-AI`
  path. It is now built from `auto-illustrate.yml.example`, which carries the
  current repository URL.

### Added

- README (EN + zh-CN): a "Switchable looks" section documenting the six style
  presets — what each look is, when to reach for it, the front-matter selector,
  the unknown-id fallback, and how to add your own. `style-presets.md` was also
  missing from the file inventory.

### Changed

- `dist/` rebuilt from the current tree so both artifacts carry the fix above.

## [0.1.0] — 2026-07-23

First release.

### Added

- `blog-smart-images` skill: derive an image plan from the post structure, source
  candidates from licensed inputs only, score each with an ArtiMuse-style
  8-dimension rubric plus a style-fit gate (composite ≥ 70 **and** style-fit ≥ 7),
  export web-ready `webp`/`jpg`/OG files, insert hero and section figures with alt
  text via insert-only safe writes, and emit an `.image-report.md` recording every
  accepted and rejected candidate.
- Six style presets, brand card templates, CI drop-in, bilingual README and
  INTEGRATION docs.

[0.1.1]: https://github.com/Zora-waybox/blog-image-skill/releases/tag/v0.1.1
[0.1.0]: https://github.com/Zora-waybox/blog-image-skill/releases/tag/v0.1.0
