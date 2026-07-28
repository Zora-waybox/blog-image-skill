#!/usr/bin/env python3
"""extract_slots.py — parse a Markdown or HTML post into an image-slot plan (stdlib only).

Usage:
  python3 extract_slots.py post.md --check            # validate parse, exit 0/1
  python3 extract_slots.py post.html --out plan.json  # write slot skeleton
Options: --max-figures N (default 4 inline figures besides hero/og)

Format follows the file extension (.html/.htm ⇒ HTML, everything else Markdown).
The emitted plan carries "format", and anchors are written in that format's own
vocabulary — "## Heading" for Markdown, the heading's visible text for HTML —
so insert_images.py can match them without re-deriving the format.
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

import htmlpost

def slugify(s):
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    return re.sub(r"[-\s]+", "-", s)[:80] or "post"

def parse_html(text):
    """Same tuple shape as parse(): (fm, body, heads, imgs, words).

    A full document exposes <title> as a pseudo front-matter key so the plan can
    name the post; a fragment has no metadata to read and reports none. Headings
    come back as (level, visible_text, offset) to match the Markdown path.
    """
    fm = {}
    title = htmlpost._TITLE_RE.search(text)
    if title:
        fm["title"] = " ".join(htmlpost.strip_tags(title.group(1)).split())
    body = htmlpost.body_inner(text)
    heads = [(lvl, label, start) for lvl, label, start, _ in htmlpost.headings(body)]
    return fm, body, heads, htmlpost.img_srcs(body), htmlpost.word_count(body)

def parse(path):
    text = Path(path).read_text(encoding="utf-8")
    if htmlpost.is_html(path):
        return parse_html(text)
    fm, body, fm_span = {}, text, None
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        fm_span = m.span()
        body = text[m.end():]
        for line in m.group(1).splitlines():
            kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if kv: fm[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    # strip code fences so headings inside fences don't count
    fenceless = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), body, flags=re.S)
    heads = [(len(h.group(1)), h.group(2).strip(), h.start())
             for h in re.finditer(r"^(#{1,4})\s+(.+)$", fenceless, re.M)]
    imgs = re.findall(r"!\[[^\]]*\]\([^)]+\)", fenceless)
    words = len(re.findall(r"\w+", fenceless))
    return fm, body, heads, imgs, words

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("post"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--out"); ap.add_argument("--max-figures", type=int, default=4)
    a = ap.parse_args()
    try:
        fm, body, heads, imgs, words = parse(a.post)
    except Exception as e:
        print(f"PARSE FAIL: {e}"); sys.exit(1)
    is_html = htmlpost.is_html(a.post)
    fmt = "html" if is_html else "markdown"
    if a.check:
        shape = ""
        if is_html:
            full = htmlpost.is_full_document(Path(a.post).read_text(encoding="utf-8"))
            shape = f" html_shape={'document' if full else 'fragment'}"
        print(f"ok: format={fmt}{shape} front_matter_keys={list(fm)} headings={len(heads)} "
              f"existing_images={len(imgs)} words={words}")
        sys.exit(0)
    title = fm.get("title") or next((t for l, t, _ in heads if l == 1), Path(a.post).stem)
    slug = slugify(fm.get("slug", "").split("/")[-1] or title)
    # Anchors speak the post's own format: insert_images.py matches a literal
    # "## Heading" line in Markdown, and an <h2> whose visible text equals the
    # anchor in HTML.
    h2s = [t if is_html else f"## {t}" for l, t, _ in heads if l == 2]
    budget = min(a.max_figures, max(1, words // 550))
    slots = [
        {"slot": "hero", "aspect": "16:9", "subject": "", "tags": [], "layout": "hero"},
        {"slot": "og", "aspect": "1200x630", "subject": "", "tags": [], "layout": "og"},
    ] + [
        {"slot": f"fig-{i+1}", "anchor_heading": h, "aspect": "16:9",
         "subject": "", "tags": [], "layout": ""}
        for i, h in enumerate(h2s[:budget])
    ]
    plan = {"post": a.post, "format": fmt, "slug": slug, "title": title,
            "existing_images": len(imgs), "words": words,
            "note": "Agent: fill subject/tags/layout per SKILL.md step 1; "
                    "drop slots the text already serves.",
            "slots": slots}
    out = a.out or "image-plan.json"
    Path(out).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(slots)} slot skeletons, figure budget {budget})")

if __name__ == "__main__":
    main()
