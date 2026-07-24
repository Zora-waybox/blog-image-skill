#!/usr/bin/env python3
"""preview.py — render an illustrated post to a standalone HTML preview.

Figures get judged one at a time, but they get *read* in a column, in sequence.
Two images with the same composition, or three warm sunsets in a row, only look
wrong in layout. This renders the post at realistic content width, plus a
filmstrip of every figure in document order so repetition is visible at a glance.

Usage:
  python3 preview.py <post.md> [-o out.html] [--width 760] [--open]

The output must sit next to the post so relative image paths resolve; that is
the default. Uses the `markdown` package when available and falls back to a
built-in converter covering the subset this skill emits, so it works with no
third-party dependency at all.
"""
import argparse, html, os, re, subprocess, sys
from pathlib import Path

CSS = """
:root { color-scheme: light dark; --ink:#1b1512; --muted:#6b5b4d; --bg:#fbf8f4;
        --rule:#e5dbcd; --accent:#b06a2c; --soft:#f2ece3; }
@media (prefers-color-scheme: dark) {
  :root { --ink:#f2e5d0; --muted:#bda88c; --bg:#16100a; --rule:#3a2c1f;
          --accent:#e8b26a; --soft:#241a11; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
       font: 17px/1.7 -apple-system, BlinkMacSystemFont, "PingFang SC",
             "Helvetica Neue", Segoe UI, sans-serif; }
.bar { position:sticky; top:0; z-index:5; background:var(--accent); color:#fff;
       font-size:13px; padding:7px 14px; text-align:center; }
.wrap { max-width: var(--w, 760px); margin:0 auto; padding:32px 20px 96px; }
.fm { border:1px solid var(--rule); background:var(--soft); border-radius:10px;
      padding:14px 16px; margin:0 0 36px; font-size:13.5px; color:var(--muted); }
.fm div { margin:3px 0; word-break:break-word; }
.fm b { color:var(--ink); font-weight:600; }
.strip { border:1px solid var(--rule); border-radius:10px; padding:14px 16px;
         margin:0 0 40px; background:var(--soft); }
.strip h4 { margin:0 0 4px; font-size:12px; letter-spacing:.09em;
            text-transform:uppercase; color:var(--muted); font-weight:600; }
.strip p { margin:0 0 12px; font-size:12.5px; color:var(--muted); }
.strip .row { display:flex; gap:10px; overflow-x:auto; padding-bottom:4px; }
.strip figure { margin:0; flex:0 0 172px; }
.strip img { width:172px; height:97px; object-fit:cover; border-radius:6px;
             display:block; border:1px solid var(--rule); }
.strip figcaption { font-size:11px; color:var(--muted); margin-top:5px;
                    line-height:1.35; word-break:break-word; }
h1 { font-size:34px; line-height:1.25; letter-spacing:-.01em; margin:0 0 24px; }
h2 { font-size:25px; margin:52px 0 14px; padding-top:14px;
     border-top:1px solid var(--rule); }
h3 { font-size:20px; margin:34px 0 10px; }
h4 { font-size:17px; margin:26px 0 8px; }
p { margin:0 0 18px; }
img { max-width:100%; height:auto; display:block; border-radius:8px;
      margin:28px auto 8px; }
figure { margin:0; }
figcaption, img + em, p > img + em { display:block; text-align:center;
      color:var(--muted); font-size:14px; font-style:italic; margin:0 auto 30px; }
table { width:100%; border-collapse:collapse; margin:22px 0; font-size:14.5px;
        display:block; overflow-x:auto; }
th, td { border:1px solid var(--rule); padding:9px 11px; text-align:left;
         vertical-align:top; }
th { background:var(--soft); }
pre { background:var(--soft); padding:14px 16px; border-radius:8px;
      overflow-x:auto; font-size:13.5px; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:.92em; }
:not(pre) > code { background:var(--soft); padding:1px 5px; border-radius:4px; }
blockquote { border-left:3px solid var(--accent); margin:0 0 18px;
             padding:2px 0 2px 16px; color:var(--muted); }
hr { border:0; border-top:1px solid var(--rule); margin:40px 0; }
a { color:var(--accent); }
li { margin:5px 0; }
"""

IMG_RE = re.compile(r'!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)(?:\s+"(?P<title>[^"]*)")?\)')


# ---------------------------------------------------------------- front matter
def split_front_matter(text):
    if text.startswith("---"):
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if m:
            return m.group(1), text[m.end():]
    return "", text


def front_matter_html(fm):
    if not fm:
        return ""
    rows = []
    for line in fm.splitlines():
        if ":" in line and not line.startswith((" ", "-", "#")):
            k, v = line.split(":", 1)
            rows.append(f"<div><b>{html.escape(k.strip())}</b>: "
                        f"{html.escape(v.strip())}</div>")
    return '<div class="fm">' + "".join(rows) + "</div>" if rows else ""


# ------------------------------------------------------------------- filmstrip
def filmstrip(body, post_dir):
    """Every figure in document order — the point of the whole script."""
    shots = []
    for m in IMG_RE.finditer(body):
        src, alt = m.group("src"), m.group("alt")
        label = (alt[:70] + "…") if len(alt) > 70 else (alt or Path(src).name)
        missing = "" if (post_dir / src).exists() else " ⚠ missing"
        shots.append((src, label + missing))
    if len(shots) < 2:
        return ""
    cards = "".join(
        f'<figure><img src="{html.escape(s)}" alt=""><figcaption>{i}. '
        f'{html.escape(l)}</figcaption></figure>'
        for i, (s, l) in enumerate(shots, 1))
    return ('<div class="strip"><h4>Figures in order</h4>'
            '<p>Scan for repetition: same composition twice, three sunsets in a '
            'row, or a hero that echoes the first section figure.</p>'
            f'<div class="row">{cards}</div></div>')


# ------------------------------------------------------- minimal md fallback
def _inline(s):
    s = html.escape(s)
    s = IMG_RE.sub(
        lambda m: f'<img src="{m.group("src")}" alt="{m.group("alt")}">', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
    return s


def _table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    if len(cells) >= 2 and all(set(c) <= set("-: ") for c in cells[1]):
        head, body_rows = cells[0], cells[2:]
    else:
        head, body_rows = None, cells
    out = ["<table>"]
    if head:
        out.append("<thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in head)
                   + "</tr></thead>")
    out.append("<tbody>")
    for row in body_rows:
        out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def render_basic(md):
    """Covers the subset this skill emits. Used when `markdown` is absent."""
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i]); i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(block)) + "</code></pre>")
        elif line.startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i]); i += 1
            out.append(_table(rows))
        elif re.match(r"^#{1,6} ", line):
            lvl = len(line) - len(line.lstrip("#"))
            out.append(f"<h{lvl}>{_inline(line[lvl:].strip())}</h{lvl}>"); i += 1
        elif re.match(r"^(-{3,}|\*{3,})$", line.strip()):
            out.append("<hr>"); i += 1
        elif re.match(r"^\s*([-*+]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.", line))
            items = []
            while i < len(lines) and re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*+]|\d+\.)\s+", "", lines[i])); i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(t)}</li>" for t in items)
                       + f"</{tag}>")
        elif line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i].lstrip("> ")); i += 1
            out.append(f"<blockquote>{_inline(' '.join(quote))}</blockquote>")
        elif line.strip() == "":
            i += 1
        elif line.startswith("<!--"):
            i += 1
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(
                    ("#", "|", ">", "```")):
                para.append(lines[i]); i += 1
            text = "\n".join(para)
            # a lone image + its italic caption becomes a <figure>
            m = IMG_RE.fullmatch(para[0].strip()) if para else None
            if m and len(para) >= 2 and para[1].strip().startswith("*"):
                cap = para[1].strip().strip("*")
                out.append(f'<figure><img src="{m.group("src")}" '
                           f'alt="{html.escape(m.group("alt"))}">'
                           f'<figcaption>{_inline(cap)}</figcaption></figure>')
            else:
                out.append(f"<p>{_inline(text)}</p>")
    return "\n".join(out)


def render(md):
    try:
        import markdown  # optional; better fidelity when installed
        return markdown.markdown(
            md, extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    except ImportError:
        return render_basic(md)


# ------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("post")
    ap.add_argument("-o", "--out")
    ap.add_argument("--width", type=int, default=760,
                    help="content column width in px (default 760)")
    ap.add_argument("--open", action="store_true", help="open in the browser")
    a = ap.parse_args()

    src = Path(a.post).resolve()
    if not src.exists():
        sys.exit(f"no such post: {src}")
    out = Path(a.out).resolve() if a.out else src.with_suffix(".preview.html")
    if out.parent != src.parent:
        sys.exit("the preview must sit next to the post so relative image "
                 "paths resolve — drop -o or point it at the same directory")

    fm, body = split_front_matter(src.read_text(encoding="utf-8"))
    missing = [m.group("src") for m in IMG_RE.finditer(body)
               if not (src.parent / m.group("src")).exists()]

    page = (
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(src.stem)} — preview</title>"
        f"<style>{CSS}</style></head><body>"
        f"<div class='bar'>local preview · not your site's styling · "
        f"{html.escape(src.name)}</div>"
        f"<div class='wrap' style='--w:{a.width}px'>"
        f"{front_matter_html(fm)}{filmstrip(body, src.parent)}{render(body)}"
        f"</div></body></html>")
    out.write_text(page, encoding="utf-8")

    print(out)
    if missing:
        print(f"warning: {len(missing)} image path(s) do not resolve: "
              + ", ".join(missing[:5]), file=sys.stderr)
    if a.open:
        subprocess.run(["open" if sys.platform == "darwin" else "xdg-open",
                        str(out)], check=False)


if __name__ == "__main__":
    main()
