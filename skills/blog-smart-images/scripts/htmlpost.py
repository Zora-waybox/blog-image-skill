#!/usr/bin/env python3
"""htmlpost.py — HTML post primitives shared by the format-aware scripts (stdlib only).

The skill accepts Markdown and HTML posts. Markdown stays inline in each script;
HTML needs a little shared machinery — heading spans, tag-stripped text, image
sources — that would otherwise be copied into three scripts and drift.

An HTML post is one of two shapes, and the difference matters in exactly one
place (head metadata):

  full document  — has <html>/<head>/<body>; head metadata can be inserted
  body fragment  — what template-driven sites commit (<p>, <section>, <h2> and
                   nothing else); there is no <head> to write to, so head-level
                   values belong in the report, not guessed into the file

Deliberately regex-based, not html.parser: every consumer needs *byte offsets
into the original text* so insertion stays a pure splice and the fail-closed
integrity check can still compare against the original. A tree parser would
force a re-serialisation and lose that guarantee.
"""
import html as _html
import re

HTML_SUFFIXES = (".html", ".htm")

# Block-level closers, in the order we care about them: after a heading (or an
# anchor snippet) a figure should land after the first complete block, not
# glued to the heading. Mirrors the Markdown path's "skip to the next blank line".
BLOCK_CLOSERS = ("</p>", "</ul>", "</ol>", "</table>", "</blockquote>",
                 "</figure>", "</pre>", "</dl>")

_HEADING_RE = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1\s*>", re.S | re.I)
_IMG_SRC_RE = re.compile(r"""<img\b[^>]*?\bsrc\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""",
                         re.S | re.I)
_DROP_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.S | re.I)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
_TAG_RE = re.compile(r"<[^>]+>", re.S)
_BODY_RE = re.compile(r"<body\b[^>]*>(.*)</body\s*>", re.S | re.I)
_TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title\s*>", re.S | re.I)


def is_html(path):
    """Format is decided by extension — explicit, and never sniffs content."""
    return str(path).lower().endswith(HTML_SUFFIXES)


def is_full_document(text):
    return bool(re.search(r"<(?:html|head|body)\b", text, re.I))


def body_inner(text):
    """Inner HTML of <body> for a full document; the text itself for a fragment."""
    m = _BODY_RE.search(text)
    return m.group(1) if m else text


def strip_tags(s):
    """Visible text: comments, script/style and tags out, entities decoded."""
    s = _COMMENT_RE.sub(" ", s)
    s = _DROP_RE.sub(" ", s)
    s = _TAG_RE.sub(" ", s)
    return _html.unescape(s)


def headings(text):
    """[(level, visible_text, start, end)] for <h1>..<h6>, in document order.

    start/end span the whole element, so callers can splice after it.
    """
    out = []
    for m in _HEADING_RE.finditer(text):
        label = " ".join(strip_tags(m.group(2)).split())
        out.append((int(m.group(1)), label, m.start(), m.end()))
    return out


def img_srcs(text):
    """Every <img src> value, in document order."""
    return [(m.group(1) or m.group(2) or m.group(3) or "")
            for m in _IMG_SRC_RE.finditer(text)]


def word_count(text):
    return len(re.findall(r"\w+", strip_tags(text)))


def block_end(text, from_idx):
    """Index just past the first block closer at/after from_idx.

    Returns from_idx unchanged when none is found, so the caller splices
    immediately after the anchor rather than running to end of file.
    """
    best = -1
    for closer in BLOCK_CLOSERS:
        i = text.lower().find(closer, from_idx)
        if i != -1 and (best == -1 or i < best):
            best = i + len(closer)
    return best if best != -1 else from_idx


def head_meta_tag(key, value):
    """og:/article:/fb: use property=; everything else (twitter:, description) name=."""
    attr = "property" if key.split(":")[0] in ("og", "article", "fb") else "name"
    return '<meta {}="{}" content="{}" />'.format(
        attr, _html.escape(key, quote=True), _html.escape(value, quote=True))


def has_head_meta(text, key):
    attr = "property" if key.split(":")[0] in ("og", "article", "fb") else "name"
    return re.search(
        r"<meta\b[^>]*\b{}\s*=\s*[\"']{}[\"']".format(attr, re.escape(key)),
        text, re.I) is not None
