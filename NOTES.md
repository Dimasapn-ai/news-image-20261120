# Notes — News Image, Friday 20 November 2026

Entry for make.fun bounty `news-image-20261120`: "Sum up 20 November's
world news in one image."

## How the image is drawn

`main.py` (pure Python 3 standard library, no third-party code) renders a
newspaper front page into a raw 1024x1024 RGB pixel buffer and encodes it
as PNG with `zlib` + `struct`:

- Drawing primitives written for this entry: filled boxes, fat-pen line
  segments (disc-stamped), polylines, rings, discs and ellipses.
- A hand-authored stroke font: every glyph is a list of polylines on a
  5x7 grid, drawn at any scale; paragraphs are word-wrapped against the
  font's fixed advance width.
- Layout: masthead ("THE WORLD IN ONE DAY"), a black date band naming the
  day in large letters ("FRIDAY 20 NOVEMBER 2026"), the lead story with a
  drawn scene (US, China and Russia flags on poles behind a summit table,
  a dove with an olive sprig, caption), six news panels in two columns,
  and a dark footer ticker with one-line items.
- The program writes `/output/entry.png` when `/output` exists, otherwise
  `./entry.png`. It runs offline in well under a second.

## Constraint checks (verified)

- Dimensions: 1024 x 1024 px (IHDR re-read and checked).
- File size: 34,504 bytes — well under the 1 MiB (1,048,576) limit.
- Validity: PNG signature, chunk CRCs, and full zlib decompression of the
  IDAT stream all verified with an independent reader script.
- Determinism: two consecutive runs produce byte-identical output,
  sha256 `56e4aa001ada7efc567d4aa1054241c2f280d3137fa9709c2add275c21a9583e`
  both times.

## Headlines used

All headlines below were reported on 20 November 2026.

Lead:
- UKRAINE AT THE CENTRE OF SHENZHEN SUMMIT — after their first-ever
  three-way summit, Trump, Xi and Putin issued a four-point peace
  declaration putting an end to the Ukraine war first; in Berlin,
  Ukraine's European allies said they are ready for talks with Russia.

Panels:
- WALL STREET SLIDES AGAIN — S&P 500 fell 2.0%, a fifth straight loss,
  even as Anthropic closed up 17% on its record Nasdaq debut; Nikkei
  sank 4.68% on AI-valuation jitters.
- HOUTHIS STRIKE SAUDI TARGETS — Houthi forces claimed strikes on four
  targets in Saudi Arabia; a missile damaged Riyadh's tallest tower and
  the group warned foreign investors to leave.
- HORMUZ IN FLAMES — Iran escalated attacks on tankers in the Strait of
  Hormuz as the Gulf crisis entered its 13th day.
- KERCH BRIDGE HIT AGAIN — Ukraine struck the Crimean Bridge for the
  third time in four days; Putin vowed a harsher response.
- COP31 DOWN TO THE WIRE — final days in Antalya: negotiators split on
  fossil-fuel targets and climate finance as the deadline nears.
- AID CALL FOR FLOODED GAZA — Australia, Canada, Italy and the UK
  jointly called on Israel to let aid reach flood-hit Gaza.

Footer ticker:
- Anthropic closes +17% on debut.
- Nvidia faces California chip probe.
- Fiona, Cincinnati Zoo's beloved hippo, dies after swallowing a
  visitor's hat.
- Trump posthumously pardons Pete Rose.
