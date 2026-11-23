#!/usr/bin/env python3
"""Draws one 1024x1024 PNG summing up Monday 23 November 2026 world news.

Pure standard library. No network, no system fonts: every letter is drawn
from the small 5x7 bitmap font defined below, and the PNG bytes are encoded
by hand (zlib + CRC). Output is fully deterministic.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (245, 239, 226)
INK = (22, 28, 38)
NAVY = (20, 33, 61)
NAVY2 = (28, 46, 84)
RED = (178, 34, 34)
GOLD = (232, 184, 75)
WHITE = (255, 255, 255)
GREY = (90, 96, 108)
LIGHT = (226, 232, 240)
SKY = (176, 209, 230)
GREEN = (46, 125, 50)
ORANGE = (230, 126, 34)
FLAME = (243, 156, 18)
DARKGREY = (52, 58, 64)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows of 5 pixels, '#' = on, '.' = off.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
}


def text_width(text, scale):
    """Pixel width of text at the given scale (6 px per char incl. gap)."""
    return len(text) * 6 * scale - scale


def wrap(text, scale, max_width):
    """Word-wrap text into lines that fit max_width pixels."""
    lines = []
    for chunk in text.split('\n'):
        words = chunk.split(' ')
        line = ''
        for word in words:
            trial = word if not line else line + ' ' + word
            if text_width(trial, scale) <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.fill_rect(x - t // 2, y - t // 2, t, t, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def triangle(self, pts, color):
        (x0, y0), (x1, y1), (x2, y2) = pts
        ymin, ymax = min(y0, y1, y2), max(y0, y1, y2)
        for y in range(ymin, ymax + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= y < max(ay, by):
                    xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                xa, xb = int(min(xs)), int(max(xs))
                self.fill_rect(xa, y, xb - xa + 1, 1, color)

    def draw_char(self, x, y, ch, scale, color):
        glyph = FONT.get(ch.upper(), FONT[' '])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    self.fill_rect(x + col * scale, y + row * scale,
                                   scale, scale, color)

    def draw_text(self, x, y, text, scale, color, align='left'):
        """Draw one line; returns the pixel width drawn."""
        text = text.upper()
        if align == 'center':
            x -= text_width(text, scale) // 2
        elif align == 'right':
            x -= text_width(text, scale)
        cx = x
        for ch in text:
            self.draw_char(cx, y, ch, scale, color)
            cx += 6 * scale
        return text_width(text, scale)

    def draw_block(self, x, y, text, scale, color, max_width, line_gap=4):
        """Wrapped text block; returns total height used."""
        lines = wrap(text, scale, max_width)
        for i, ln in enumerate(lines):
            self.draw_text(x, y + i * (7 * scale + line_gap), ln, scale, color)
        return len(lines) * (7 * scale + line_gap)


# ------------------------------------------------------------- mini scenes
def icon_globe(cv, x, y, s):
    """Broken-climate globe: blue earth, green land, red crack."""
    cv.fill_rect(x, y, s, s, (214, 234, 244))
    cv.circle(x + s // 2, y + s // 2, s // 2 - 6, (52, 120, 190))
    cv.circle(x + s // 2 - 14, y + s // 2 - 10, 12, GREEN)
    cv.circle(x + s // 2 + 16, y + s // 2 + 12, 10, GREEN)
    cv.line(x + s // 2 - 18, y + 12, x + s // 2 + 20, y + s - 12, RED, 5)


def icon_ship(cv, x, y, s):
    """Ship on fire on waves."""
    cv.fill_rect(x, y, s, s, (200, 222, 235))
    cv.fill_rect(x + 8, y + s - 26, s - 16, 10, (44, 90, 140))
    cv.fill_rect(x + 8, y + s - 16, s - 16, 6, (30, 64, 110))
    cv.fill_rect(x + s // 2 - 8, y + s - 62, 16, 36, (90, 60, 40))
    cv.fill_rect(x + s // 2 - 2, y + s - 84, 4, 24, INK)
    cv.triangle([(x + s // 2 - 22, y + s - 62), (x + s // 2 - 6, y + s - 96),
                 (x + s // 2 + 2, y + s - 62)], FLAME)
    cv.triangle([(x + s // 2 + 2, y + s - 62), (x + s // 2 + 16, y + s - 90),
                 (x + s // 2 + 26, y + s - 62)], ORANGE)
    cv.fill_rect(x + 6, y + s - 8, s - 12, 4, WHITE)


def icon_strike(cv, x, y, s):
    """Damaged building with smoke and a drone above."""
    cv.fill_rect(x, y, s, s, (226, 226, 220))
    cv.fill_rect(x + 18, y + s - 58, 30, 58, DARKGREY)
    cv.fill_rect(x + 56, y + s - 80, 30, 80, (70, 76, 84))
    cv.fill_rect(x + 56, y + s - 80, 30, 10, RED)
    for wy in (y + s - 48, y + s - 30):
        cv.fill_rect(x + 24, wy, 18, 8, GOLD)
        cv.fill_rect(x + 62, wy, 18, 8, GOLD)
    cv.circle(x + 34, y + 22, 10, GREY)
    cv.circle(x + 46, y + 14, 8, GREY)
    cv.fill_rect(x + s - 44, y + 16, 26, 4, INK)
    cv.fill_rect(x + s - 34, y + 8, 6, 20, INK)
    cv.circle(x + s - 46, y + 18, 5, INK)
    cv.circle(x + s - 16, y + 18, 5, INK)


def icon_factory(cv, x, y, s):
    """Factory with chimneys and flames."""
    cv.fill_rect(x, y, s, s, (232, 224, 210))
    cv.fill_rect(x + 12, y + s - 52, 34, 52, (120, 66, 44))
    cv.fill_rect(x + 50, y + s - 40, 44, 40, (150, 84, 52))
    cv.fill_rect(x + 20, y + s - 88, 10, 40, DARKGREY)
    cv.fill_rect(x + 34, y + s - 80, 10, 32, DARKGREY)
    cv.triangle([(x + 16, y + s - 52), (x + 26, y + s - 84),
                 (x + 36, y + s - 52)], FLAME)
    cv.triangle([(x + 58, y + s - 40), (x + 70, y + s - 66),
                 (x + 82, y + s - 40)], ORANGE)
    cv.circle(x + s - 22, y + 18, 9, GREY)
    cv.circle(x + s - 34, y + 10, 7, GREY)


def icon_cap(cv, x, y, s):
    """Graduation cap over an exam paper."""
    cv.fill_rect(x, y, s, s, (220, 230, 240))
    cv.fill_rect(x + 16, y + s - 44, s - 32, 40, WHITE)
    cv.rect(x + 16, y + s - 44, s - 32, 40, INK, 2)
    cv.fill_rect(x + 24, y + s - 36, s - 48, 4, GREY)
    cv.fill_rect(x + 24, y + s - 26, s - 60, 4, GREY)
    cv.fill_rect(x + 24, y + s - 16, s - 48, 4, RED)
    cv.triangle([(x + s // 2 - 40, y + 26), (x + s // 2, y + 8),
                 (x + s // 2 + 40, y + 26)], INK)
    cv.triangle([(x + s // 2 - 40, y + 26), (x + s // 2, y + 44),
                 (x + s // 2 + 40, y + 26)], NAVY2)
    cv.fill_rect(x + s // 2 - 14, y + 40, 28, 12, INK)
    cv.line(x + s // 2 + 40, y + 26, x + s // 2 + 40, y + 52, GOLD, 3)
    cv.circle(x + s // 2 + 40, y + 56, 5, GOLD)


def icon_flags(cv, x, y, s):
    """Two meeting flags on poles (Nepal crimson, India tricolour)."""
    cv.fill_rect(x, y, s, s, (226, 236, 226))
    cv.fill_rect(x + 26, y + 18, 4, s - 30, INK)
    cv.fill_rect(x + 66, y + 18, 4, s - 30, INK)
    cv.fill_rect(x + 30, y + 18, 30, 12, (220, 20, 60))
    cv.fill_rect(x + 30, y + 30, 30, 12, (220, 20, 60))
    cv.triangle([(x + 30, y + 42), (x + 60, y + 42), (x + 30, y + 54)],
                (220, 20, 60))
    cv.fill_rect(x + 70, y + 18, 30, 10, (255, 153, 51))
    cv.fill_rect(x + 70, y + 28, 30, 10, WHITE)
    cv.fill_rect(x + 70, y + 38, 30, 10, (19, 136, 8))
    cv.circle(x + 85, y + 33, 4, NAVY)


def lead_scene(cv, x, y, w, h):
    """G20 summit skyline: sun, towers, flags, ground."""
    cv.fill_rect(x, y, w, h, SKY)
    cv.circle(x + w - 52, y + 44, 30, GOLD)
    cv.circle(x + w - 52, y + 44, 22, (244, 208, 110))
    # skyline silhouettes
    heights = [0.42, 0.62, 0.34, 0.72, 0.50, 0.66, 0.38, 0.58]
    bw = w // len(heights)
    for i, frac in enumerate(heights):
        bh = int(h * frac)
        bx = x + i * bw + 4
        cv.fill_rect(bx, y + h - bh - 26, bw - 8, bh, NAVY)
        for wy in range(y + h - bh - 16, y + h - 30, 18):
            cv.fill_rect(bx + 5, wy, 6, 8, GOLD)
    # flags on the two tallest towers
    for fx, fcol in ((x + 3 * bw + bw // 2, GREEN),
                     (x + 5 * bw + bw // 2, RED)):
        cv.fill_rect(fx, y + 22, 3, 62, INK)
        cv.fill_rect(fx + 3, y + 22, 30, 12, fcol)
        cv.fill_rect(fx + 3, y + 34, 30, 12, GOLD)
    cv.fill_rect(x, y + h - 26, w, 26, (34, 58, 44))
    cv.fill_rect(x, y + h - 26, w, 4, GOLD)


# ------------------------------------------------------------------ page
def build():
    cv = Canvas(W, H, PAPER)
    cv.rect(0, 0, W, H, INK, 4)

    # ---- masthead
    cv.fill_rect(4, 4, W - 8, 118, NAVY)
    cv.draw_text(W // 2, 22, "WORLD NEWS", 7, WHITE, align='center')
    cv.draw_text(W // 2, 84, "MONDAY 23 NOVEMBER 2026", 3, GOLD, align='center')
    cv.fill_rect(4, 122, W - 8, 6, RED)

    # ---- lead story: G20
    lx, ly, lw, lh = 24, 140, 976, 252
    cv.fill_rect(lx, ly, lw, lh, WHITE)
    cv.rect(lx, ly, lw, lh, INK, 2)
    cv.fill_rect(lx, ly, lw, 10, RED)
    cv.draw_text(lx + 20, ly + 26, "LEAD STORY", 2, RED)
    cv.draw_block(lx + 20, ly + 58,
                  "G20 MEETS IN AFRICA - FIRST SUMMIT ON AFRICAN SOIL",
                  4, INK, 580, line_gap=8)
    cv.draw_block(lx + 20, ly + 182,
                  "LEADERS MEET 22-23 NOV IN JOHANNESBURG.\n"
                  "FIRST G20 IN AFRICA. HOST RAMAPHOSA. US ABSENT.",
                  2, GREY, 580, line_gap=6)
    lead_scene(cv, lx + 624, ly + 24, 328, lh - 48)

    # ---- grid of six stories
    stories = [
        ("CLIMATE", "COP31 COLLAPSES - NO CLIMATE DEAL",
         "ANTALYA TALKS END WITH NO DEAL. LONGEST COP ON RECORD.",
         icon_globe, RED),
        ("BALTIC SEA", "RUSSIAN SHIP BURNS OFF FINLAND",
         "STILL BURNING AFTER A DRONE ATTACK IN THE BALTIC.",
         icon_ship, NAVY2),
        ("UKRAINE", "14 MISSING AFTER KYIV DRONE STRIKE",
         "DRONE HIT A BUILDING IN THE KYIV REGION, ZELENSKIY SAYS.",
         icon_strike, DARKGREY),
        ("INDONESIA", "FACTORY FIRE IN INDONESIA",
         "AT LEAST 3 DEAD, DOZENS MISSING. RESCUERS RECOVER BODIES.",
         icon_factory, ORANGE),
        ("SOUTH KOREA", "MINISTER QUITS IN AI EXAM SCANDAL",
         "S. KOREA EDUCATION CHIEF RESIGNS AFTER CHEATING ROW.",
         icon_cap, NAVY2),
        ("ASIA", "NEPAL PM MEETS MODI IN DELHI",
         "BILATERAL TALKS ON A 22-23 NOV STATE VISIT TO NEW DELHI.",
         icon_flags, GREEN),
    ]
    gx, gy = 24, 408
    pw, ph, gap = 476, 152, 24
    for i, (tag, head, sub, icon, accent) in enumerate(stories):
        px = gx + (i % 2) * (pw + gap)
        py = gy + (i // 2) * (ph + 10)
        cv.fill_rect(px, py, pw, ph, WHITE)
        cv.rect(px, py, pw, ph, INK, 2)
        cv.fill_rect(px, py, 8, ph, accent)
        icon(cv, px + 16, py + 16, 118)
        tx = px + 146
        cv.draw_text(tx, py + 12, tag, 2, accent)
        hl = wrap(head, 3, pw - 166)
        hy = py + 36
        for j, ln in enumerate(hl):
            cv.draw_text(tx, hy + j * 25, ln, 3, INK)
        cv.draw_block(tx, hy + len(hl) * 25 + 6, sub, 2, GREY,
                      pw - 166, line_gap=4)

    # ---- footer strip: also today
    fx, fy, fw, fh = 24, 884, 976, 116
    cv.fill_rect(fx, fy, fw, fh, NAVY)
    cv.draw_text(fx + 20, fy + 14, "ALSO TODAY", 2, GOLD)
    footer = [
        "MEXICO CAPTURES CARTEL BOSS 'EL CHAPO ISIDRO' - 11 KILLED IN SINALOA",
        "UN TALKS ON LETHAL AI WEAPONS TO CONTINUE",
        "INDIA POST RECORD 720/9 IN WELLINGTON TEST",
    ]
    for i, item in enumerate(footer):
        yy = fy + 38 + i * 24
        cv.circle(fx + 28, yy + 7, 4, RED)
        cv.draw_text(fx + 44, yy, item, 2, WHITE)
    return cv


# -------------------------------------------------------------- PNG write
def write_png(cv, path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        out += struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', comp)
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def main():
    outdir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    write_png(cv, os.path.join(outdir, 'entry.png'))


if __name__ == '__main__':
    main()
