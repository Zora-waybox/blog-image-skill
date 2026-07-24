# Aesthetic scoring rubric (ArtiMuse-style, judge = the agent)

Derived from ArtiMuse (CVPR 2026, arXiv:2507.14533) — the 8-attribute expert
framework and its training insights — adapted for a VLM-as-judge setting where the
agent (not a fine-tuned model) does the scoring. The three insights we operationalize:
**(1)** a bare score is worthless — attribute breakdown + written critique or it
didn't happen; **(2)** generic VLMs have positivity bias — the protocol below
forces criticism first; **(3)** whole-image judgment — evaluate composition and
color on the full frame before zooming into details.

## The 8 dimensions (score each 0–100)

| # | Dimension | What to check |
|---|-----------|----------------|
| 1 | Composition & Design | balance, contrast, rhythm; focal point; unity/harmony |
| 2 | Visual Elements & Structure | color/geometry/space/light interaction; structural clarity |
| 3 | Technical Execution | focus, exposure, lighting control, resolution, render cleanliness |
| 4 | Originality & Creativity | concept and execution beyond the generic |
| 5 | Theme & Communication | is the subject unmistakable; does it say what the slot needs |
| 6 | Emotion & Viewer Response | evoked mood; would a reader pause on it |
| 7 | Overall Gestalt | the whole-frame impression, coherence of all elements |
| 8 | Comprehensive | holistic weighing of impact, message, depth |

**Composite** = mean of dims 1–7, then reconcile with dim 8 (they should agree
within ~5 points; if not, re-examine). Scale anchors: 90+ exceptional / 80–89
strong / 70–79 publishable / 55–69 weak (reject) / <55 poor (reject).

## Protocol (in order)

1. **Type the image first** — photograph / designed card / chart / AIGC — and
   apply type-aware standards: intentional blur in a photo is not a technical
   fault; a designed card is judged hard on typography, alignment, and label
   collisions; AIGC gets an explicit artifact hunt (hands, text, geometry,
   texture seams).
2. **Criticize before scoring.** Write 1–3 concrete flaws (crop, collision,
   muddiness, cliché, dead space). "No flaws found" is not an allowed output for
   the first pass — this is the positivity-bias antidote.
3. Score the 8 dimensions with a one-line justification each (one clause is fine).
4. **Style-fit 0–10** against `style-profile.md` (palette, light, mood, brand
   tokens). An image can be beautiful and still wrong for the blog — style-fit is
   a separate gate, not a 9th dimension.
5. Verdict: **accept** (composite ≥ 70 AND style-fit ≥ 7) / **re-source** /
   **reject**. Ties between candidates: prefer the one whose weakest dimension is
   higher (max-min), then the more on-subject one (dim 5).

## Score-keeping discipline

- Judge the rendered pixels at delivery size (1600w), not the concept.
- Negative exemplars from the style profile (flat midday light, cluttered UI,
  washed-out sky, generic suburbia) cap Composition at 60 unless deliberately
  subverted.
- Record every candidate's row in the report — including rejects. Rejects with
  reasons are the dataset that makes the next run smarter (per the "primer-style
  annotation" idea in the ArtiMuse data pipeline).
- If two independent judgments are cheap (e.g. a second agent pass in CI), average
  them; disagreement > 15 points on any dimension → look again (the aesthetic-
  subjectivity caveat from the ArtiMuse cross-dataset results).
