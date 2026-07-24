#!/usr/bin/env python3
"""extract_slots.py — parse a Markdown post into an image-slot plan (stdlib only).

Usage:
  python3 extract_slots.py post.md --check            # validate parse, exit 0/1
  python3 extract_slots.py post.md --out plan.json    # write slot skeleton
Options: --max-figures N (default 4 inline figures besides hero/og)
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

def slugify(s):
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    return re.sub(r"[-\s]+", "-", s)[:80] or "post"

def parse(path):
    text = Path(path).read_text(encoding="utf-8")
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
    if a.check:
        print(f"ok: front_matter_keys={list(fm)} headings={len(heads)} "
              f"existing_images={len(imgs)} words={words}")
        sys.exit(0)
    title = fm.get("title") or next((t for l, t, _ in heads if l == 1), Path(a.post).stem)
    slug = slugify(fm.get("slug", "").split("/")[-1] or title)
    h2s = [f"## {t}" for l, t, _ in heads if l == 2]
    budget = min(a.max_figures, max(1, words // 550))
    slots = [
        {"slot": "hero", "aspect": "16:9", "subject": "", "tags": [], "layout": "hero"},
        {"slot": "og", "aspect": "1200x630", "subject": "", "tags": [], "layout": "og"},
    ] + [
        {"slot": f"fig-{i+1}", "anchor_heading": h, "aspect": "16:9",
         "subject": "", "tags": [], "layout": ""}
        for i, h in enumerate(h2s[:budget])
    ]
    plan = {"post": a.post, "slug": slug, "title": title,
            "existing_images": len(imgs), "words": words,
            "note": "Agent: fill subject/tags/layout per SKILL.md step 1; "
                    "drop slots the text already serves.",
            "slots": slots}
    out = a.out or "image-plan.json"
    Path(out).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(slots)} slot skeletons, figure budget {budget})")

if __name__ == "__main__":
    main()
