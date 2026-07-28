#!/usr/bin/env python3
"""insert_images.py — insert-only, fail-closed image insertion for Markdown and HTML posts.

Plan JSON shape (see examples/insert-plan.example.json, insert-plan.html.example.json):
{
  "frontmatter": {"hero_image": "...", "hero_alt": "...", "og_image": "..."},
  "head_meta":   {"og:image": "...", "twitter:image": "..."},
  "inserts": [
    {"after_heading": "## Exact H2 text", "block": "![alt](path)\n*caption*"},
    {"after_text": "exact unique paragraph snippet", "block": "..."}
  ]
}
Rules enforced here: anchors must match EXACTLY ONCE; existing text is never
modified (pure insertions); referenced local image files must exist; dry-run by
default (unified diff to stdout); --write makes .bak then writes atomically.

Format follows the file extension (.html/.htm ⇒ HTML, everything else Markdown):

  Markdown  "frontmatter" writes keys into the --- block; anchors match a literal
            "## Heading" line; blocks are Markdown.
  HTML      "head_meta" writes <meta> before </head> and needs a FULL document;
            anchors match an <h1>..<h6> by visible text, or a literal snippet;
            blocks are HTML (<figure><img …><figcaption>…</figcaption></figure>).

An HTML *fragment* has no <head> to write to. Rather than invent one, this
refuses head metadata on a fragment: those values belong in the report, for the
site template or post registry to consume — the same call blog-seo-geo makes.
"""
import argparse, difflib, json, os, re, sys, tempfile
from pathlib import Path

import htmlpost

def die(msg):
    print(f"REFUSED: {msg}"); sys.exit(1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("post"); ap.add_argument("--plan", required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--allow-missing-files", action="store_true")
    a = ap.parse_args()
    post = Path(a.post); plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    original = post.read_text(encoding="utf-8")
    text = original
    is_html = htmlpost.is_html(post)

    fm = plan.get("frontmatter") or {}
    head_meta = plan.get("head_meta") or {}
    if is_html and fm:
        die("HTML post cannot take 'frontmatter' — use 'head_meta' on a full "
            "document, or put the values in the report for a fragment")
    if not is_html and head_meta:
        die("Markdown post cannot take 'head_meta' — use 'frontmatter'")

    # 1a) Markdown front-matter keys (add-only; refuse to overwrite an existing key)
    if fm:
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m: die("post has no front matter block but plan sets frontmatter keys")
        block = m.group(1)
        for k, v in fm.items():
            if re.search(rf"^{re.escape(k)}\s*:", block, re.M):
                die(f"front-matter key already exists: {k} (insert-only policy)")
            block += f'\n{k}: {json.dumps(v, ensure_ascii=False) if any(c in v for c in ":#") else v}'
        text = f"---\n{block}\n---\n" + text[m.end():]

    # 1b) HTML head metadata (add-only, full documents only)
    meta_tags = []
    if head_meta:
        if not htmlpost.is_full_document(text):
            die("post is an HTML fragment with no <head> — head metadata belongs "
                "in the report for the site template/registry, not in the fragment")
        close = re.search(r"</head\s*>", text, re.I)
        if not close: die("HTML document has no </head> to insert metadata before")
        for k, v in head_meta.items():
            if htmlpost.has_head_meta(text, k):
                die(f"head meta already exists: {k} (insert-only policy)")
            meta_tags.append(htmlpost.head_meta_tag(k, v))
        addition = "".join(t + "\n" for t in meta_tags)
        text = text[:close.start()] + addition + text[close.start():]

    # 2) body insertions
    for ins in plan.get("inserts", []):
        blk = ins.get("block", "").rstrip()
        if not blk: die("empty block in insert")
        if "after_heading" in ins:
            anchor = ins["after_heading"].strip()
            if is_html:
                hits = [h for h in htmlpost.headings(text) if h[1] == anchor]
                if len(hits) != 1: die(f"heading anchor matched {len(hits)}x: {anchor!r}")
                pos = htmlpost.block_end(text, hits[0][3])
            else:
                pat = re.compile(rf"^{re.escape(anchor)}\s*$", re.M)
                hits = list(pat.finditer(text))
                if len(hits) != 1: die(f"heading anchor matched {len(hits)}x: {anchor!r}")
                pos = text.index("\n", hits[0].end() - 1) + 1 if "\n" in text[hits[0].end()-1:] else len(text)
                # skip the paragraph right under the heading so the figure follows prose
                nxt = text.find("\n\n", pos)
                pos = (nxt + 2) if nxt != -1 else len(text)
        elif "after_text" in ins:
            snip = ins["after_text"]
            if text.count(snip) != 1: die(f"text anchor matched {text.count(snip)}x: {snip[:60]!r}")
            end = text.index(snip) + len(snip)
            if is_html:
                pos = htmlpost.block_end(text, end)
            else:
                nxt = text.find("\n\n", end)
                pos = (nxt + 2) if nxt != -1 else len(text)
        else:
            die("insert needs after_heading or after_text")
        text = (text[:pos] + "\n" + blk + text[pos:]) if is_html else \
               (text[:pos] + blk + "\n\n" + text[pos:])

    # 3) integrity: original text must survive as a subsequence of blocks
    stripped_new = text
    for ins in plan.get("inserts", []):
        blk = ins["block"].rstrip()
        stripped_new = stripped_new.replace(("\n" + blk) if is_html else (blk + "\n\n"), "", 1)
    for t in meta_tags:
        stripped_new = stripped_new.replace(t + "\n", "", 1)
    if fm:
        for k, v in fm.items():
            stripped_new = re.sub(rf"^{re.escape(k)}:.*\n", "", stripped_new, count=1, flags=re.M)
    if stripped_new != original:
        die("integrity check failed — a non-insert change was produced; aborting")

    # 4) referenced local images must exist
    if not a.allow_missing_files:
        blocks = "\n".join(i["block"] for i in plan.get("inserts", []))
        refs = htmlpost.img_srcs(blocks) if is_html else \
               re.findall(r"!\[[^\]]*\]\(([^) \"]+)", blocks)
        for rel in refs:
            if not rel.startswith(("http://", "https://")) and not (post.parent / rel).exists():
                die(f"image file not found next to post: {rel}")

    diff = "".join(difflib.unified_diff(original.splitlines(True), text.splitlines(True),
                                        "a/" + post.name, "b/" + post.name))
    if not a.write:
        print(diff or "(no changes)"); print("\nDRY-RUN ok — rerun with --write to apply.")
        return
    bak = post.with_suffix(post.suffix + ".bak")
    bak.write_text(original, encoding="utf-8")
    fd, tmp = tempfile.mkstemp(dir=post.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f: f.write(text)
    os.replace(tmp, post)
    meta_note = f"{len(fm)} front-matter keys" if not is_html else f"{len(meta_tags)} head meta tags"
    print(f"wrote {post} (+{len(plan.get('inserts', []))} figures, "
          f"{meta_note}); backup at {bak.name}")

if __name__ == "__main__":
    main()
