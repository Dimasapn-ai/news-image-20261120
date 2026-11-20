#!/usr/bin/env python3
"""THE WORLD IN ONE DAY -- Friday 20 November 2026.

Draws a complete newspaper front page as a single 1024x1024 PNG using
nothing but the Python standard library.  The picture is rendered into a
raw RGB pixel buffer with hand-written drawing primitives (lines, boxes,
circles, a small stroke font), then encoded as PNG with zlib/struct.

Run:  python3 main.py
Writes /output/entry.png when /output exists, otherwise ./entry.png.
The output is fully deterministic: same code, same bytes, every run.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- colours
PAPER = (246, 242, 231)
PAPER_SHADE = (238, 231, 214)
INK = (24, 24, 28)
FAINT = (96, 92, 84)
RULE = (60, 58, 52)
RED = (172, 32, 30)
BLUE = (34, 62, 122)
SKY = (216, 226, 236)
GOLD = (214, 164, 32)
WHITE = (252, 252, 250)
GREEN = (52, 110, 58)

# ---------------------------------------------------------------- canvas
px = bytearray(W * H * 3)


def fill_all(col):
    block = bytes(col)
    for i in range(W * H):
        px[i * 3:i * 3 + 3] = block


def put(x, y, col):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i] = col[0]
        px[i + 1] = col[1]
        px[i + 2] = col[2]


def box(x0, y0, x1, y1, col):
    """Filled rectangle, inclusive bounds, clipped to the canvas."""
    xa, xb = max(0, int(x0)), min(W - 1, int(x1))
    ya, yb = max(0, int(y0)), min(H - 1, int(y1))
    if xa > xb or ya > yb:
        return
    row = bytes(col) * (xb - xa + 1)
    for y in range(ya, yb + 1):
        i = (y * W + xa) * 3
        px[i:i + len(row)] = row


def stamp(cx, cy, r, col):
    """Filled disc used as a fat pen nib."""
    r = int(round(r))
    if r <= 0:
        put(int(round(cx)), int(round(cy)), col)
        return
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                put(int(round(cx)) + dx, int(round(cy)) + dy, col)


def line(x0, y0, x1, y1, col, thick=1):
    """Straight segment drawn by walking the longer axis."""
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    r = max(0, (thick - 1) // 2)
    for s in range(steps + 1):
        t = s / steps
        stamp(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, col)


def poly(points, col, thick=1, close=False):
    pts = list(points)
    if close and pts:
        pts.append(pts[0])
    for a, b in zip(pts, pts[1:]):
        line(a[0], a[1], b[0], b[1], col, thick)


def ring(cx, cy, rad, col, thick=1):
    n = max(24, int(rad * 6))
    pts = [(cx + rad * math.cos(2 * math.pi * i / n),
            cy + rad * math.sin(2 * math.pi * i / n))
           for i in range(n + 1)]
    poly(pts, col, thick)


def disc(cx, cy, rad, col):
    for dy in range(-int(rad), int(rad) + 1):
        half = int((rad * rad - dy * dy) ** 0.5)
        box(cx - half, cy + dy, cx + half, cy + dy, col)


def ellipse(cx, cy, rx, ry, col):
    for dy in range(-int(ry), int(ry) + 1):
        t = dy / ry if ry else 0
        half = int(rx * (1 - t * t) ** 0.5)
        box(cx - half, cy + dy, cx + half, cy + dy, col)

# ---------------------------------------------------------------- font
# Hand-authored stroke glyphs on a 5-wide, 7-tall grid (y grows downward).
# Each glyph is a list of polylines; each polyline is a list of (x, y).
GLYPHS = {
    "A": [[(0, 7), (2, 0), (4, 7)], [(1, 5), (3, 5)]],
    "B": [[(0, 7), (0, 0), (3, 0), (4, 1), (4, 3), (3, 3.5), (0, 3.5)],
          [(3, 3.5), (4, 4.5), (4, 6), (3, 7), (0, 7)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 6), (1, 7), (3, 7), (4, 6)]],
    "D": [[(0, 7), (0, 0), (3, 0), (4, 1), (4, 6), (3, 7), (0, 7)]],
    "E": [[(4, 0), (0, 0), (0, 7), (4, 7)], [(0, 3.5), (3, 3.5)]],
    "F": [[(4, 0), (0, 0), (0, 7)], [(0, 3.5), (3, 3.5)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 6), (1, 7), (3, 7),
           (4, 6), (4, 4), (2.5, 4)]],
    "H": [[(0, 0), (0, 7)], [(4, 0), (4, 7)], [(0, 3.5), (4, 3.5)]],
    "I": [[(2, 0), (2, 7)], [(0.5, 0), (3.5, 0)], [(0.5, 7), (3.5, 7)]],
    "J": [[(4, 0), (4, 6), (3, 7), (1, 7), (0, 6)]],
    "K": [[(0, 0), (0, 7)], [(4, 0), (0.5, 3.5)], [(1.5, 2.5), (4, 7)]],
    "L": [[(0, 0), (0, 7), (4, 7)]],
    "M": [[(0, 7), (0, 0), (2, 3), (4, 0), (4, 7)]],
    "N": [[(0, 7), (0, 0), (4, 7), (4, 0)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 6), (3, 7), (1, 7), (0, 6),
           (0, 1), (1, 0)]],
    "P": [[(0, 7), (0, 0), (3, 0), (4, 1), (4, 3), (3, 3.5), (0, 3.5)]],
    "Q": [[(1, 0), (3, 0), (4, 1), (4, 6), (3, 7), (1, 7), (0, 6),
           (0, 1), (1, 0)], [(2.5, 5), (4, 7)]],
    "R": [[(0, 7), (0, 0), (3, 0), (4, 1), (4, 3), (3, 3.5), (0, 3.5)],
          [(2, 3.5), (4, 7)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 3), (1, 3.5), (3, 3.5),
           (4, 4.5), (4, 6), (3, 7), (1, 7), (0, 6)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 7)]],
    "U": [[(0, 0), (0, 6), (1, 7), (3, 7), (4, 6), (4, 0)]],
    "V": [[(0, 0), (2, 7), (4, 0)]],
    "W": [[(0, 0), (1, 7), (2, 3), (3, 7), (4, 0)]],
    "X": [[(0, 0), (4, 7)], [(4, 0), (0, 7)]],
    "Y": [[(0, 0), (2, 3.5)], [(4, 0), (2, 3.5)], [(2, 3.5), (2, 7)]],
    "Z": [[(0, 0), (4, 0), (0, 7), (4, 7)]],
    "0": [[(1, 0), (3, 0), (4, 1), (4, 6), (3, 7), (1, 7), (0, 6),
           (0, 1), (1, 0)]],
    "1": [[(1, 1.5), (2.5, 0), (2.5, 7)], [(0.5, 7), (4, 7)]],
    "2": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2.5), (0, 7), (4, 7)]],
    "3": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2.5), (3, 3.5), (1.5, 3.5)],
          [(3, 3.5), (4, 4.5), (4, 6), (3, 7), (1, 7), (0, 6)]],
    "4": [[(3, 7), (3, 0), (0, 4.5), (4, 4.5)]],
    "5": [[(4, 0), (0, 0), (0, 3.2), (3, 3.2), (4, 4.2), (4, 6),
           (3, 7), (1, 7), (0, 6)]],
    "6": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 6), (1, 7), (3, 7),
           (4, 6), (4, 4), (3, 3.5), (0, 3.5)]],
    "7": [[(0, 0), (4, 0), (2, 7)]],
    "8": [[(1, 0), (3, 0), (4, 1), (4, 2.5), (3, 3.5), (1, 3.5),
           (0, 2.5), (0, 1), (1, 0)],
          [(1, 3.5), (3, 3.5), (4, 4.5), (4, 6), (3, 7), (1, 7),
           (0, 6), (0, 4.5), (1, 3.5)]],
    "9": [[(0, 6), (1, 7), (3, 7), (4, 6), (4, 1), (3, 0), (1, 0),
           (0, 1), (0, 3), (1, 3.5), (4, 3.5)]],
    ".": [[(1.7, 6.4), (2.3, 6.4), (2.3, 7), (1.7, 7), (1.7, 6.4)]],
    ",": [[(2.3, 5.6), (1.8, 7)]],
    "'": [[(2.2, 0), (1.8, 1.6)]],
    ":": [[(1.7, 1.8), (2.3, 1.8), (2.3, 2.4), (1.7, 2.4), (1.7, 1.8)],
          [(1.7, 5.2), (2.3, 5.2), (2.3, 5.8), (1.7, 5.8), (1.7, 5.2)]],
    "-": [[(0.5, 3.5), (3.5, 3.5)]],
    "+": [[(2, 1.5), (2, 5.5)], [(0, 3.5), (4, 3.5)]],
    "%": [[(0, 7), (4, 0)],
          [(0.6, 0.6), (1.4, 0.6), (1.4, 1.4), (0.6, 1.4), (0.6, 0.6)],
          [(2.6, 5.6), (3.4, 5.6), (3.4, 6.4), (2.6, 6.4), (2.6, 5.6)]],
    "&": [[(3.2, 6.8), (1, 4.5), (0.6, 3.2), (1, 1.2), (2.2, 0.2),
           (3.2, 0.8), (2.8, 2.2), (0.8, 4.8), (1.2, 6.2), (2.6, 6.9),
           (4, 6.9)], [(2.6, 4.2), (4, 7)]],
    "/": [[(0.8, 7), (3.2, 0)]],
    "(": [[(3, 0), (1.5, 1), (1, 3.5), (1.5, 6), (3, 7)]],
    ")": [[(1, 0), (2.5, 1), (3, 3.5), (2.5, 6), (1, 7)]],
    "!": [[(2, 0), (2, 4.8)],
          [(1.7, 6.4), (2.3, 6.4), (2.3, 7), (1.7, 7), (1.7, 6.4)]],
}
ADV = 6.0  # glyph advance in grid units (5 wide + 1 space)


def text_w(s, u):
    return (len(s) * ADV - 1) * u if s else 0.0


def draw_text(x, y, s, u, col, thick=None):
    """Draw string s with its cap-height top at y; u = pixels per grid unit."""
    if thick is None:
        thick = max(1, int(round(u * 0.9)))
    cx = float(x)
    for ch in s.upper():
        glyph = GLYPHS.get(ch)
        if glyph:
            for stroke in glyph:
                pts = [(cx + gx * u, y + gy * u) for gx, gy in stroke]
                poly(pts, col, thick)
        cx += ADV * u
    return cx


def draw_centered(cx, y, s, u, col, thick=None):
    return draw_text(cx - text_w(s, u) / 2, y, s, u, col, thick)


def wrap(s, u, max_w):
    """Greedy word wrap for the stroke font's fixed advance."""
    lines, cur = [], ""
    for word in s.split():
        trial = word if not cur else cur + " " + word
        if text_w(trial, u) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def block(x, y, s, u, max_w, col, leading=1.45, thick=None):
    """Wrapped paragraph; returns the y just below the last line."""
    for ln in wrap(s, u, max_w):
        draw_text(x, y, ln, u, col, thick)
        y += 7 * u * leading
    return y

# ---------------------------------------------------------------- scene


def flag_us(x, y, w, h):
    box(x, y, x + w, y + h, WHITE)
    stripe = h / 7.0
    for i in range(0, 7, 2):
        box(x, y + i * stripe, x + w, y + (i + 1) * stripe - 1, RED)
    cw, chh = int(w * 0.42), int(stripe * 4)
    box(x, y, x + cw, y + chh, BLUE)
    for r in range(3):
        for c in range(4):
            stamp(x + 6 + c * (cw - 8) / 3, y + 5 + r * (chh - 8) / 2, 1, WHITE)
    poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], INK, 1, close=True)


def flag_china(x, y, w, h):
    box(x, y, x + w, y + h, RED)
    stamp(x + w * 0.2, y + h * 0.26, 4, GOLD)
    for dx, dy in ((0.42, 0.12), (0.48, 0.3), (0.48, 0.5), (0.4, 0.66)):
        stamp(x + w * dx, y + h * dy, 2, GOLD)
    poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], INK, 1, close=True)


def flag_russia(x, y, w, h):
    third = h / 3.0
    box(x, y, x + w, y + third, WHITE)
    box(x, y + third, x + w, y + 2 * third, BLUE)
    box(x, y + 2 * third, x + w, y + h, RED)
    poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], INK, 1, close=True)


DOVE = (176, 192, 208)
DOVE_DARK = (148, 168, 188)


def dove(cx, cy, s):
    """Simple dove: body, raised wing, head, beak, olive sprig."""
    ellipse(cx, cy, 30 * s, 13 * s, DOVE)
    poly([(cx - 6 * s, cy - 4 * s), (cx - 26 * s, cy - 30 * s),
          (cx - 2 * s, cy - 16 * s), (cx + 12 * s, cy - 4 * s)], DOVE_DARK)
    disc(cx + 30 * s, cy - 10 * s, 8 * s, DOVE)
    poly([(cx + 37 * s, cy - 11 * s), (cx + 46 * s, cy - 8 * s),
          (cx + 37 * s, cy - 6 * s)], GOLD)
    line(cx + 40 * s, cy - 7 * s, cx + 56 * s, cy - 2 * s, GREEN, max(1, int(2 * s)))
    stamp(cx + 52 * s, cy - 6 * s, 2.5 * s, GREEN)
    stamp(cx + 57 * s, cy - 1 * s, 2.5 * s, GREEN)
    poly([(cx - 30 * s, cy), (cx - 44 * s, cy - 6 * s), (cx - 42 * s, cy + 4 * s),
          (cx - 30 * s, cy + 3 * s)], DOVE)


def lead_scene(x0, y0, x1, y1):
    box(x0, y0, x1, y1, SKY)
    disc((x0 + x1) // 2, y0 + 14, 9, GOLD)
    # summit table
    table_y = y1 - 32
    box(x0 + 14, table_y, x1 - 14, y1 - 6, (104, 78, 52))
    box(x0 + 14, table_y, x1 - 14, table_y + 5, (128, 98, 66))
    # three flags on poles behind the table
    fw, fh = 76, 44
    xs = [x0 + 26, (x0 + x1) // 2 - fw // 2, x1 - 26 - fw]
    for fx, draw in zip(xs, (flag_us, flag_china, flag_russia)):
        line(fx - 4, table_y + 4, fx - 4, y0 + 24, INK, 2)
        draw(fx, y0 + 24, fw, fh)
    dove((x0 + x1) // 2, y1 - 50, 0.8)
    poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], RULE, 2, close=True)
    draw_centered((x0 + x1) / 2, y1 - 24, "SHENZHEN: THREE FLAGS, ONE TABLE",
                  1.5, PAPER)

# ---------------------------------------------------------------- page
M = 40                 # page margin
RIGHT = W - M


def rule(y, thick=2, col=RULE, x0=M, x1=RIGHT):
    box(x0, y, x1, y + thick - 1, col)


def build_page():
    fill_all(PAPER)
    # page frame
    poly([(18, 18), (W - 19, 18), (W - 19, H - 19), (18, H - 19)], RULE, 2, close=True)
    poly([(24, 24), (W - 25, 24), (W - 25, H - 25), (24, H - 25)], RULE, 1, close=True)

    # ---- masthead
    draw_centered(W / 2, 40, "THE WORLD IN ONE DAY", 7.6, INK)
    rule(112, 3)
    rule(118, 1)
    draw_text(M + 2, 126, "VOL. I - NO. 237", 1.7, FAINT)
    draw_centered(W / 2, 124, "GLOBAL EDITION - PRINTED BY PROGRAM", 1.7, FAINT)
    r = "ONE PAGE, ONE DAY"
    draw_text(RIGHT - 2 - text_w(r, 1.7), 126, r, 1.7, FAINT)

    # ---- date line, the biggest thing after the name
    box(M, 148, RIGHT, 204, INK)
    draw_centered(W / 2, 158, "FRIDAY 20 NOVEMBER 2026", 6.4, PAPER)
    rule(214, 2)

    # ---- lead story
    draw_text(M + 2, 224, "SHENZHEN SUMMIT - THE LEAD STORY", 2.3, RED)
    y = 254
    for ln in wrap("UKRAINE AT THE CENTRE OF SHENZHEN SUMMIT", 5.0, RIGHT - M):
        draw_text(M + 2, y, ln, 5.0, INK)
        y += 7 * 5.0 * 1.3
    lead_deck = ("After their first-ever three-way summit, Trump, Xi and Putin "
                 "issued a four-point peace declaration putting an end to the "
                 "Ukraine war first. In Berlin, Ukraine's European allies "
                 "said they are ready for talks with Russia.")
    block(M + 2, y + 4, lead_deck, 2.05, 560, INK)
    lead_scene(606, y + 2, RIGHT - 2, y + 128)
    rule(478, 2)

    # ---- news panels, two columns of three
    panels = [
        ("WALL STREET SLIDES AGAIN",
         "S&P 500 fell 2.0%, a fifth straight loss, even as Anthropic "
         "closed up 17% on its record Nasdaq debut. Nikkei sank 4.68% "
         "on AI-valuation jitters."),
        ("HOUTHIS STRIKE SAUDI TARGETS",
         "Houthi forces claimed strikes on four targets in Saudi "
         "Arabia. A missile damaged Riyadh's tallest tower and the "
         "group warned foreign investors to leave."),
        ("HORMUZ IN FLAMES",
         "Iran escalated attacks on tankers in the Strait of Hormuz "
         "as the Gulf crisis entered its 13th day."),
        ("KERCH BRIDGE HIT AGAIN",
         "Ukraine struck the Crimean Bridge for the third time in "
         "four days. Putin vowed a harsher response."),
        ("COP31 DOWN TO THE WIRE",
         "Final days in Antalya: negotiators split on fossil-fuel "
         "targets and climate finance as the deadline nears."),
        ("AID CALL FOR FLOODED GAZA",
         "Australia, Canada, Italy and the UK jointly called on "
         "Israel to let aid reach flood-hit Gaza."),
    ]
    col_w = (RIGHT - M - 24) // 2
    top = 494
    row_h = 138
    for i, (head, deck) in enumerate(panels):
        cx = M + (i % 2) * (col_w + 24)
        cy = top + (i // 2) * row_h
        box(cx, cy + 2, cx + 10, cy + 12, RED)
        hy = block(cx + 18, cy, head, 2.6, col_w - 18, INK, leading=1.25)
        block(cx + 2, hy + 3, deck, 1.78, col_w - 4, INK, leading=1.4)
        if i % 2 == 0 and i + 1 < len(panels):
            line(cx + col_w + 12, cy, cx + col_w + 12, cy + row_h - 16, RULE, 1)
        if i // 2 < 2:
            rule(cy + row_h - 8, 1, RULE, cx, cx + col_w)

    # ---- footer ticker
    fy = 920
    box(M, fy, RIGHT, 986, INK)
    draw_centered(W / 2, fy + 9, "ALSO TODAY - THE WIRE IN ONE LINE EACH", 2.0, GOLD)
    ticker = ("Anthropic closes +17% on debut - Nvidia faces California chip "
              "probe - Fiona, Cincinnati Zoo's beloved hippo, dies after "
              "swallowing a visitor's hat - Trump posthumously pardons "
              "Pete Rose")
    ty = fy + 33
    for ln in wrap(ticker, 1.5, RIGHT - M - 30):
        draw_centered(W / 2, ty, ln, 1.5, PAPER)
        ty += 7 * 1.5 * 1.4
    draw_centered(W / 2, 989, "THE WORLD IN ONE DAY - FRIDAY 20 NOVEMBER 2026 - END OF FRONT PAGE",
                  1.35, FAINT)

# ---------------------------------------------------------------- png out


def png_bytes():
    raw = bytearray()
    rowlen = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += px[y * rowlen:(y + 1) * rowlen]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    build_page()
    data = png_bytes()
    outdir = "/output" if os.path.isdir("/output") else "."
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print("wrote", path, len(data), "bytes")


if __name__ == "__main__":
    main()
