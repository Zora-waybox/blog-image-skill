# Integration guide — wiring blog-smart-images into your blog automation

**English** · [简体中文](INTEGRATION.zh-CN.md)

Three ways to adopt it, from least to most invasive. The repo layout and safety
conventions deliberately mirror [cazerme/blog-marketing-skills](https://github.com/cazerme/blog-marketing-skills)
(blog-seo-geo), so the two skills chain in one pipeline: **text first (SEO/GEO), images
second (this skill)**. blog-seo-geo promises to preserve every `<img>` and link verbatim;
this skill promises insert-only writes that never touch prose — neither breaks the other.

## A. Standalone workflow (fastest to ship)

Copy `.github/workflows/auto-illustrate.yml` into your **blog site repo** and change two variables:

| Variable | Meaning | Example |
|---|---|---|
| `POSTS_DIR` | Markdown posts directory | `content/blog` |
| `IMAGES_DIR` | Site's static images directory | `public/images` or `static/images` |

Secrets (Settings → Secrets and variables → Actions):

| Key | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Drives claude-code-action to run the skill (spends your existing Claude tokens) |
| `PEXELS_API_KEY` | Recommended | Primary stock source: free, ~200/hour (script caps at 190 for headroom) |
| `UNSPLASH_ACCESS_KEY` | Optional | Backup stock source: free demo ~50/hour (script caps at 45) |
| `IMAGEGEN_API_KEY` + variable `IMAGEGEN_PROVIDER` | Optional | AI-generation path (per-image billing; fills niche scenes stock can't find) |

**Dual-stock auto-failover**: with both keys set, `scripts/fetch_stock.py` pulls from
providers in `STOCK_PROVIDER_ORDER` (default `pexels,unsplash`) in turn; when one hits its
hourly cap (`PEXELS_HOURLY_CAP` / `UNSPLASH_HOURLY_CAP`, tunable — e.g. both 50) or returns
429/403, it **fails over to the next**, tracking usage in a rolling `.stock-usage.json`
window. Unsplash images automatically get a "Photo by X on Unsplash" credit in the caption
per its API terms; Pexels has no attribution requirement, so the photographer info goes into
the report. With no optional keys set, the skill uses only "repo-owned assets / photo library
+ brand-card fallback" — runs offline, zero external dependencies.

## B. Bolt onto your existing blog-generation Action (recommended end state)

In your existing workflow, add a step after "generate/update posts" and before "build/deploy site":

```yaml
      - name: Install illustration skill
        run: |
          mkdir -p .claude/skills
          git clone --depth 1 https://github.com/Zora-waybox/blog-image-skill /tmp/bis
          cp -r /tmp/bis/skills/blog-smart-images .claude/skills/

      - name: Illustrate new posts
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Run the blog-smart-images skill on <path to the md generated this run>,
            --images-dir <site images dir>/<post-slug>. Follow SKILL.md exactly.
```

If your generation step is already claude-code-action / Claude Code: after dropping the skill
into `.claude/skills/`, just append one line to the same prompt — "after generating, run the
blog-smart-images skill on the new post" — no second step needed.

## C. Local / Cowork / Claude Code manual run

```
/plugin marketplace add Zora-waybox/blog-image-skill      # or copy skills/blog-smart-images into .claude/skills/
/blog-image-skill:blog-smart-images content/blog/my-post.md --images-dir public/images/my-post
```

## Site-template notes (roadtripskill.dev)

- The skill writes three front-matter keys by default: `hero_image` / `hero_alt` / `og_image`.
  If your template doesn't consume them yet: the hero is also inlined right after the first
  paragraph (once the template supports the keys, drop the inline copy); `og_image` needs
  `og:image` / `twitter:image` emitted in `<head>`.
- Images are referenced as `images/<post-slug>/<name>.webp` (+ a `.jpg` fallback) — make sure
  that directory is published as a static asset, or point `IMAGES_DIR` at your convention.
- The copyright red line is hard-coded in SKILL.md: social screenshots (the high-light photo
  library) are style reference only — those pixels never ship to the site.

## Ordering when chaining with blog-seo-geo

1. Generate/edit post → 2. `blog-seo-geo` (text, head markup, JSON-LD) →
3. `blog-smart-images` (hero/OG/section images + `.image-report.md`) → 4. build & deploy.

Both skills are dry-run→write, leave a `.bak`, and fail closed — a failure at any step never
corrupts the article.
