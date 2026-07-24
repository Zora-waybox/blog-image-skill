#!/usr/bin/env python3
"""insert_images.py — insert-only, fail-closed image insertion for Markdown posts.

Plan JSON shape (see examples/insert-plan.example.json):
{
  "frontmatter": {"hero_image": "...", "hero_alt": "...", "og_image": "..."},
  "inserts": [
    {"after_heading": "## Exact H2 text", "block": "![alt](path)\n*caption*"},
    {"after_text": "exact unique paragraph snippet", "block": "..."}
  ]
}
Rules enforced here: anchors must match EXACTLY ONCE; existing text is never
modified (pure insertions); referenced local image files must exist; dry-run by
default (unified diff to stdout); --write makes .bak then writes atomically.
"""
import argparse, difflib, json, os, re, sys, tempfile
from pathlib import Path

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

    # 1) front-matter keys (add-only; refuse to overwrite an existing key)
    fm = plan.get("frontmatter") or {}
    if fm:
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m: die("post has no front matter block but plan sets frontmatter keys")
        block = m.group(1)
        for k, v in fm.items():
            if re.search(rf"^{re.escape(k)}\s*:", block, re.M):
                die(f"front-matter key already exists: {k} (insert-only policy)")
            block += f'\n{k}: {json.dumps(v, ensure_ascii=False) if any(c in v for c in ":#") else v}'
        text = f"---\n{block}\n---\n" + text[m.end():]

    # 2) body insertions
    for ins in plan.get("inserts", []):
        blk = ins.get("block", "").rstrip()
        if not blk: die("empty block in insert")
        if "after_heading" in ins:
            pat = re.compile(rf"^{re.escape(ins['after_heading'].strip())}\s*$", re.M)
            hits = list(pat.finditer(text))
            if len(hits) != 1: die(f"heading anchor matched {len(hits)}x: {ins['after_heading']!r}")
            pos = text.index("\n", hits[0].end() - 1) + 1 if "\n" in text[hits[0].end()-1:] else len(text)
            # skip the paragraph right under the heading so the figure follows prose
            nxt = text.find("\n\n", pos)
            pos = (nxt + 2) if nxt != -1 else len(text)
        elif "after_text" in ins:
            snip = ins["after_text"]
            if text.count(snip) != 1: die(f"text anchor matched {text.count(snip)}x: {snip[:60]!r}")
            end = text.index(snip) + len(snip)
            nxt = text.find("\n\n", end)
            pos = (nxt + 2) if nxt != -1 else len(text)
        else:
            die("insert needs after_heading or after_text")
        text = text[:pos] + blk + "\n\n" + text[pos:]

    # 3) integrity: original text must survive as a subsequence of blocks
    stripped_new = text
    for ins in plan.get("inserts", []):
        stripped_new = stripped_new.replace(ins["block"].rstrip() + "\n\n", "", 1)
    if fm:
        for k, v in fm.items():
            stripped_new = re.sub(rf"^{re.escape(k)}:.*\n", "", stripped_new, count=1, flags=re.M)
    if stripped_new != original:
        die("integrity check failed — a non-insert change was produced; aborting")

    # 4) referenced local images must exist
    if not a.allow_missing_files:
        for rel in re.findall(r"!\[[^\]]*\]\(([^) \"]+)", "\n".join(i["block"] for i in plan.get("inserts", []))):
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
    print(f"wrote {post} (+{len(plan.get('inserts', []))} figures, "
          f"{len(fm)} front-matter keys); backup at {bak.name}")

if __name__ == "__main__":
    main()
