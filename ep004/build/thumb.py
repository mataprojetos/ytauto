#!/usr/bin/env python3
"""Capa do EP004: ilustração nano_banana_pro + 5 estrelas desenhadas por nós + texto grande com contorno."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cairo
import neuro_lib as L
from neuro_lib import W, H, A, Cover, glow, SUN, RED
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{ROOT}/../thumbnails/ep004_thumb.jpg"
BLUE = (0.25, 0.45, 1.0)
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
Cover(c, L.surf(f"{A}/thumb_bg.png"), 1.06, 768, 1500)
glow(c, 200, 1000, 520, RED, 0.35); glow(c, 900, 900, 520, BLUE, 0.35)
g = cairo.LinearGradient(0, 0, 0, 760); g.add_color_stop_rgba(0, 0, 0, 0.02, 0.75); g.add_color_stop_rgba(1, 0, 0, 0.02, 0)
c.set_source(g); c.paint()


def star(x, y, r):
    c.move_to(x, y - r)
    for i in range(1, 10):
        rr = r if i % 2 == 0 else r * 0.45; a = -math.pi / 2 + i * math.pi / 5
        c.line_to(x + rr * math.cos(a), y + rr * math.sin(a))
    c.close_path()


for i in range(5):
    x = 540 + (i - 2) * 190; y = 640
    glow(c, x, y, 160, SUN, 0.5)
    star(x, y, 82); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgb(0.1, 0.05, 0); c.set_line_width(16); c.stroke_preserve()
    c.set_source_rgb(1, 0.86, 0.3); c.fill()


def big(txt, y, size, col):
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    xb, yb, tw, th, _, _ = c.text_extents(txt)
    c.move_to(540 - tw / 2 - xb, y); c.text_path(txt)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgb(0, 0, 0); c.set_line_width(size * 0.16); c.stroke_preserve()
    c.set_source_rgb(*col); c.fill()


big("5 STARS", 330, 220, (1, 0.86, 0.3))
big("IN SPACE", 510, 170, (1, 1, 1))
from PIL import Image
import numpy as np
arr = np.ndarray((H, W, 4), np.uint8, s.get_data())[:, :, [2, 1, 0]].copy()
Image.fromarray(arr).save(OUT, quality=88)
print(OUT, os.path.getsize(OUT))
