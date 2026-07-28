#!/usr/bin/env python3
"""End-to-end tests for the format-aware scripts (stdlib only, no deps).

The scripts are invoked exactly the way SKILL.md invokes them — as subprocesses
with real files — because that is the contract that matters. A unit test that
imported the functions could pass while the documented command line was broken.

Run: python3 -m unittest discover tests
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "blog-smart-images" / "scripts"

MD_POST = """\
---
title: Mighty 5 in seven days
slug: mighty-5
---

Intro paragraph that sets up the drive.

## The route

First paragraph under the route heading.

Second paragraph under the route heading.

## Timing

When to go and why it matters.
"""

HTML_FRAGMENT = """\
<p class="lead">The Overseas Highway runs 113 miles to Key West.</p>

<section id="what-it-is">
<h2>What the Overseas Highway actually is</h2>
<p>The highway exists because a railroad died in 1935.</p>
<p>The practical shape: US 1 leaves the mainland at Florida City.</p>
</section>

<section id="timing">
<h2>When to drive the Keys</h2>
<p>Winter is high season for a reason.</p>
</section>
"""

HTML_DOCUMENT = """\
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>Mighty 5 in seven days</title>
<meta name="description" content="A Utah loop." />
</head>
<body>
<h1>Mighty 5 in seven days</h1>
<p>Intro paragraph that sets up the drive.</p>
<h2>The route</h2>
<p>First paragraph under the route heading.</p>
<p>Second paragraph under the route heading.</p>
</body>
</html>
"""

FIG_HTML = ('<figure><img src="img/a.webp" alt="A road at dusk">'
            '<figcaption>A road at dusk.</figcaption></figure>')
FIG_MD = "![A road at dusk](img/a.webp)\n*A road at dusk.*"


def run(script, *args):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / "img").mkdir()
        (self.d / "img" / "a.webp").write_bytes(b"not-a-real-image")
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, text):
        p = self.d / name
        p.write_text(text, encoding="utf-8")
        return p

    def plan(self, obj, name="plan.json"):
        p = self.d / name
        p.write_text(json.dumps(obj), encoding="utf-8")
        return p


class TestExtractSlots(Base):
    def test_markdown_unchanged(self):
        post = self.write("post.md", MD_POST)
        rc, out = run("extract_slots.py", post, "--check")
        self.assertEqual(rc, 0, out)
        self.assertIn("format=markdown", out)
        self.assertIn("headings=2", out)

    def test_markdown_anchors_keep_hash_prefix(self):
        post = self.write("post.md", MD_POST)
        out_json = self.d / "p.json"
        rc, out = run("extract_slots.py", post, "--out", out_json)
        self.assertEqual(rc, 0, out)
        plan = json.loads(out_json.read_text())
        self.assertEqual(plan["format"], "markdown")
        anchors = [s["anchor_heading"] for s in plan["slots"] if "anchor_heading" in s]
        self.assertTrue(all(a.startswith("## ") for a in anchors), anchors)

    def test_html_fragment_finds_headings(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        rc, out = run("extract_slots.py", post, "--check")
        self.assertEqual(rc, 0, out)
        self.assertIn("format=html", out)
        self.assertIn("html_shape=fragment", out)
        self.assertIn("headings=2", out)

    def test_html_anchors_are_bare_text(self):
        """The regression this whole change exists for: HTML used to yield zero
        figure slots because nothing matched the Markdown '## ' heading regex.

        The figure budget is words // 550, so this short fixture earns exactly
        one slot — see test_html_budget_scales_with_words for the other half.
        """
        post = self.write("keys.html", HTML_FRAGMENT)
        out_json = self.d / "p.json"
        rc, out = run("extract_slots.py", post, "--out", out_json)
        self.assertEqual(rc, 0, out)
        plan = json.loads(out_json.read_text())
        anchors = [s["anchor_heading"] for s in plan["slots"] if "anchor_heading" in s]
        self.assertEqual(anchors, ["What the Overseas Highway actually is"])
        self.assertFalse([a for a in anchors if a.startswith("#")],
                         "HTML anchors must be bare heading text, not '## …'")

    def test_html_budget_scales_with_words(self):
        """A post long enough to earn them gets one slot per H2, in order."""
        filler = "<p>" + ("The road runs on for miles and miles. " * 40) + "</p>\n"
        body = ("<h2>First heading</h2>\n" + filler * 4 +
                "<h2>Second heading</h2>\n" + filler * 4 +
                "<h2>Third heading</h2>\n" + filler * 4)
        post = self.write("long.html", body)
        out_json = self.d / "p.json"
        rc, out = run("extract_slots.py", post, "--out", out_json)
        self.assertEqual(rc, 0, out)
        plan = json.loads(out_json.read_text())
        anchors = [s["anchor_heading"] for s in plan["slots"] if "anchor_heading" in s]
        self.assertEqual(anchors,
                         ["First heading", "Second heading", "Third heading"])

    def test_html_document_shape_and_title(self):
        post = self.write("post.html", HTML_DOCUMENT)
        rc, out = run("extract_slots.py", post, "--check")
        self.assertEqual(rc, 0, out)
        self.assertIn("html_shape=document", out)
        out_json = self.d / "p.json"
        run("extract_slots.py", post, "--out", out_json)
        self.assertEqual(json.loads(out_json.read_text())["title"],
                         "Mighty 5 in seven days")

    def test_html_word_count_excludes_markup(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        rc, out = run("extract_slots.py", post, "--check")
        words = int(out.split("words=")[1].split()[0])
        self.assertLess(words, 60, "tag names must not be counted as words")
        self.assertGreater(words, 30)


class TestInsertHTML(Base):
    def test_figure_lands_after_first_paragraph(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        plan = self.plan({"inserts": [
            {"after_heading": "What the Overseas Highway actually is",
             "block": FIG_HTML}]})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 0, out)
        text = post.read_text()
        h2 = text.index("<h2>What the Overseas")
        p1 = text.index("<p>The highway exists")
        fig = text.index("<figure>")
        p2 = text.index("<p>The practical shape")
        self.assertLess(h2, p1)
        self.assertLess(p1, fig, "figure must follow prose, not the heading")
        self.assertLess(fig, p2)

    def test_write_is_pure_insertion_and_backs_up(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        plan = self.plan({"inserts": [
            {"after_heading": "When to drive the Keys", "block": FIG_HTML}]})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 0, out)
        bak = self.d / "keys.html.bak"
        self.assertTrue(bak.exists())
        self.assertEqual(bak.read_text(), HTML_FRAGMENT)
        # removing exactly the inserted block must restore the original byte-for-byte
        self.assertEqual(post.read_text().replace("\n" + FIG_HTML, "", 1),
                         HTML_FRAGMENT)

    def test_dry_run_does_not_touch_the_file(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        plan = self.plan({"inserts": [
            {"after_heading": "When to drive the Keys", "block": FIG_HTML}]})
        rc, out = run("insert_images.py", post, "--plan", plan)
        self.assertEqual(rc, 0, out)
        self.assertIn("DRY-RUN ok", out)
        self.assertEqual(post.read_text(), HTML_FRAGMENT)
        self.assertFalse((self.d / "keys.html.bak").exists())

    def test_after_text_anchor(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        plan = self.plan({"inserts": [
            {"after_text": "a railroad died in 1935", "block": FIG_HTML}]})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 0, out)
        text = post.read_text()
        self.assertLess(text.index("<figure>"), text.index("<p>The practical shape"))

    def test_missing_heading_anchor_refused(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        plan = self.plan({"inserts": [
            {"after_heading": "No such heading", "block": FIG_HTML}]})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 1)
        self.assertIn("matched 0x", out)
        self.assertEqual(post.read_text(), HTML_FRAGMENT)

    def test_ambiguous_heading_anchor_refused(self):
        post = self.write("dup.html",
                          "<h2>Same</h2><p>one</p><h2>Same</h2><p>two</p>")
        plan = self.plan({"inserts": [
            {"after_heading": "Same", "block": FIG_HTML}]})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 1)
        self.assertIn("matched 2x", out)

    def test_missing_image_refused(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        plan = self.plan({"inserts": [
            {"after_heading": "When to drive the Keys",
             "block": '<figure><img src="img/nope.webp" alt="x"></figure>'}]})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 1)
        self.assertIn("image file not found", out)
        self.assertEqual(post.read_text(), HTML_FRAGMENT)

    def test_remote_image_allowed(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        plan = self.plan({"inserts": [
            {"after_heading": "When to drive the Keys",
             "block": '<figure><img src="https://ex.com/a.webp" alt="x"></figure>'}]})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 0, out)

    def test_frontmatter_refused_on_html(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        plan = self.plan({"frontmatter": {"hero_image": "img/a.webp"}})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 1)
        self.assertIn("cannot take 'frontmatter'", out)


class TestHeadMeta(Base):
    def test_inserted_before_head_close(self):
        post = self.write("post.html", HTML_DOCUMENT)
        plan = self.plan({"head_meta": {"og:image": "img/a.webp",
                                        "twitter:image": "img/a.webp"}})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 0, out)
        text = post.read_text()
        self.assertIn('<meta property="og:image" content="img/a.webp" />', text)
        self.assertIn('<meta name="twitter:image" content="img/a.webp" />', text)
        self.assertLess(text.index("og:image"), text.index("</head>"))

    def test_refused_on_fragment(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        plan = self.plan({"head_meta": {"og:image": "img/a.webp"}})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 1)
        self.assertIn("fragment", out)
        self.assertEqual(post.read_text(), HTML_FRAGMENT)

    def test_existing_key_not_overwritten(self):
        post = self.write("post.html", HTML_DOCUMENT)
        plan = self.plan({"head_meta": {"description": "Something else."}})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 1)
        self.assertIn("already exists", out)
        self.assertEqual(post.read_text(), HTML_DOCUMENT)

    def test_refused_on_markdown(self):
        post = self.write("post.md", MD_POST)
        plan = self.plan({"head_meta": {"og:image": "img/a.webp"}})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 1)
        self.assertIn("cannot take 'head_meta'", out)


class TestMarkdownRegression(Base):
    """The Markdown path must be byte-for-byte what it was before HTML support."""

    def test_frontmatter_and_figure(self):
        post = self.write("post.md", MD_POST)
        plan = self.plan({"frontmatter": {"hero_image": "img/a.webp"},
                          "inserts": [{"after_heading": "## The route",
                                       "block": FIG_MD}]})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 0, out)
        text = post.read_text()
        self.assertIn("hero_image: img/a.webp", text)
        self.assertLess(text.index("First paragraph under the route"),
                        text.index("![A road at dusk]"))
        self.assertLess(text.index("![A road at dusk]"),
                        text.index("Second paragraph under the route"))

    def test_duplicate_frontmatter_key_refused(self):
        post = self.write("post.md", MD_POST)
        plan = self.plan({"frontmatter": {"title": "Hijacked"}})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 1)
        self.assertIn("already exists", out)

    def test_missing_frontmatter_block_refused(self):
        post = self.write("bare.md", "# No front matter\n\nBody.\n")
        plan = self.plan({"frontmatter": {"hero_image": "img/a.webp"}})
        rc, out = run("insert_images.py", post, "--plan", plan, "--write")
        self.assertEqual(rc, 1)
        self.assertIn("no front matter block", out)


class TestPreview(Base):
    def test_html_body_is_not_re_rendered(self):
        post = self.write("keys.html", HTML_FRAGMENT)
        rc, out = run("preview.py", post)
        self.assertEqual(rc, 0, out)
        page = (self.d / "keys.preview.html").read_text()
        self.assertIn('<section id="what-it-is">', page,
                      "HTML must be embedded as-is, not converted")
        self.assertNotIn("&lt;section", page, "HTML must not be escaped as text")

    def test_html_document_contributes_only_its_body(self):
        post = self.write("post.html", HTML_DOCUMENT)
        rc, out = run("preview.py", post)
        self.assertEqual(rc, 0, out)
        page = (self.d / "post.preview.html").read_text()
        self.assertNotIn("<!doctype html>\n<html>", page[200:],
                         "the post's own <html>/<head> must not be nested")
        self.assertIn("<h2>The route</h2>", page)

    def test_markdown_still_converts(self):
        post = self.write("post.md", MD_POST)
        rc, out = run("preview.py", post)
        self.assertEqual(rc, 0, out)
        page = (self.d / "post.preview.html").read_text()
        self.assertIn("The route", page)
        self.assertNotIn("## The route", page, "Markdown must be converted")


if __name__ == "__main__":
    unittest.main()
