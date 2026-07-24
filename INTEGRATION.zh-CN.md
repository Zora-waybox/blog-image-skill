# 集成指南 — 把 blog-smart-images 插进你的博客自动化

[English](INTEGRATION.md) · **简体中文**

三种接入方式，按改动量从小到大。仓库结构与安全约定刻意对齐
[cazerme/blog-marketing-skills](https://github.com/cazerme/blog-marketing-skills)（blog-seo-geo），
两个 skill 可以在同一条流水线里串联：**先文字（SEO/GEO），后配图（本 skill）**。
blog-seo-geo 承诺逐字保留 `<img>` 与链接，本 skill 承诺只做插入、绝不改动正文 —— 两边互不破坏。

## A. 独立 workflow（最快落地）

把 `.github/workflows/auto-illustrate.yml` 拷进**博客站仓库**，改两个变量：

| 变量 | 含义 | 例 |
|---|---|---|
| `POSTS_DIR` | md 博文目录 | `content/blog` |
| `IMAGES_DIR` | 站点静态图片目录 | `public/images` 或 `static/images` |

Secrets（Settings → Secrets and variables → Actions）：

| Key | 必需 | 用途 |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | 驱动 claude-code-action 执行 skill（消耗你们已有的 Claude token） |
| `PEXELS_API_KEY` | 推荐 | 图库主力：免费，~200 次/小时（脚本默认限 190 留余量） |
| `UNSPLASH_ACCESS_KEY` | 可选 | 图库备胎：免费 demo ~50 次/小时（脚本默认限 45） |
| `IMAGEGEN_API_KEY` + variable `IMAGEGEN_PROVIDER` | 可选 | AI 生成通路（按张计费，补图库搜不到的冷门场景） |

**双图库自动切换**：两个 key 都配上时，`scripts/fetch_stock.py` 按
`STOCK_PROVIDER_ORDER`（默认 `pexels,unsplash`）依次取图；某一家小时额度到阀值
（`PEXELS_HOURLY_CAP`/`UNSPLASH_HOURLY_CAP` 可调，比如都设 50）或返回 429/403 时
**自动换下一家**，用量记录在 `.stock-usage.json` 滚动窗口里。Unsplash 的图会按其
API 条款在 caption 自动附 "Photo by X on Unsplash" 署名；Pexels 无署名要求，
摄影师信息记入报告。不配任何可选 key 时，skill 只用「仓库自有素材/照片库 +
品牌卡兜底」，离线可跑、零外部依赖。

## B. 插进你现有的博客生成 Action（推荐的最终形态）

在你现有 workflow「生成/更新博文」的 step 之后、「构建/部署站点」的 step 之前，加一个 step：

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
            Run the blog-smart-images skill on <本次生成的 md 路径>,
            --images-dir <站点图片目录>/<post-slug>. Follow SKILL.md exactly.
```

如果你的生成 step 本来就是 claude-code-action / Claude Code：把 skill 装进
`.claude/skills/` 后，直接在同一个 prompt 里追加一句
「生成完成后，对新文章执行 blog-smart-images skill」即可，无需第二个 step。

## C. 本地 / Cowork / Claude Code 手动跑

```
/plugin marketplace add Zora-waybox/blog-image-skill      # 或把 skills/blog-smart-images 拷进 .claude/skills/
/blog-image-skill:blog-smart-images content/blog/my-post.md --images-dir public/images/my-post
```

## 站点模板注意事项（roadtripskill.dev）

- skill 默认写三个 front-matter 键：`hero_image` / `hero_alt` / `og_image`。
  模板若尚未消费它们：hero 已同时内联在正文首段后（模板支持后删内联即可）；
  `og_image` 需在 `<head>` 里输出 `og:image` / `twitter:image`。
- 图片按 `images/<post-slug>/<name>.webp`（+ .jpg 兜底）引用，请确保该目录被
  站点当静态资源发布，或改 `IMAGES_DIR` 到你的约定位置。
- 版权红线已写死在 SKILL.md：社媒截图（高光照片库）只作风格参照，像素永不进站。

## 与 blog-seo-geo 串联的顺序

1. 生成/修改博文 → 2. `blog-seo-geo`（文字、head markup、JSON-LD）→
3. `blog-smart-images`（hero/OG/段落图 + `.image-report.md`）→ 4. 构建部署。
两个 skill 都是 dry-run→write、留 `.bak`、fail-closed，任何一步失败都不会破坏文章。
