#!/usr/bin/env python3
"""Whatifaholic — biblioteca de desenho partilhada (camadas, texto, brilho). Cópia do ep001 sem os recursos da Lua."""
import math, random, subprocess, os
import cairo
import numpy as np
from PIL import Image

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.abspath(__file__))
A = f"{ROOT}/anim"; BLD = f"{ROOT}/build"
T_END = 999
random.seed(7); np.random.seed(7)

NAVY = (0.03, 0.06, 0.13); CYAN = (0.24, 0.88, 1.0); CREAM = (0.96, 0.93, 0.84)
SUN = (1.0, 0.78, 0.35); INK = (1, 1, 1); PINK = (1.0, 0.55, 0.65); QUIET = (0.75, 0.82, 0.95)
GREEN = (0.35, 1.0, 0.45)


def load_surface(path, size=None):
    im = Image.open(path).convert("RGBA")
    if size:
        im = im.resize(size, Image.LANCZOS)
    arr = np.array(im); bgra = arr[:, :, [2, 1, 0, 3]].copy()
    return cairo.ImageSurface.create_for_data(bgra, cairo.FORMAT_ARGB32, im.width, im.height), bgra, arr


KEEP = []  # manter buffers vivos


def surf(path, size=None):
    s, buf, arr = load_surface(path, size); KEEP.append(buf); return s, arr


stars = [(random.uniform(0, W), random.uniform(0, H * 0.62), random.uniform(0.8, 2.6),
          random.uniform(0, 6.28), random.uniform(0.6, 2.2)) for _ in range(140)]


# ---------- utilitários ----------
def ease(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)


def seg(t, a, b):
    return ease((t - a) / (b - a))


def paint_cover(ctx, s, t, t0, t1, z0, z1, dy=0, draw_extra=None):
    z = z0 + (z1 - z0) * seg(t, t0, t1)
    k = max(W / s.get_width(), H / s.get_height()) * z
    ctx.save(); ctx.translate(W / 2, H / 2 + dy); ctx.scale(k, k)
    ctx.translate(-s.get_width() / 2, -s.get_height() / 2)
    ctx.set_source_surface(s, 0, 0); ctx.paint()
    if draw_extra:
        draw_extra(ctx)
    ctx.restore()


def twinkle(ctx, t, alpha=1.0):
    for x, y, r, ph, sp in stars:
        a = alpha * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * sp * 2 + ph)))
        ctx.set_source_rgba(1, 1, 1, a * 0.8); ctx.arc(x, y, r * 0.7, 0, 6.283); ctx.fill()


def glow(ctx, x, y, r, col, a=0.6):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    ctx.set_source(g); ctx.arc(x, y, r, 0, 6.283); ctx.fill()


def text(ctx, s, x, y, size, col=INK, a=1.0, align="c", bold=True):
    if a <= 0.01:
        return
    ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    xb, yb, tw, th, _, _ = ctx.text_extents(s)
    ox = {"c": tw / 2, "l": 0, "r": tw}[align]
    ctx.move_to(x - ox - xb, y); ctx.text_path(s)
    ctx.set_source_rgba(0, 0, 0, 0.55 * a); ctx.set_line_width(size * 0.12); ctx.stroke_preserve()
    ctx.set_source_rgba(*col, a); ctx.fill()


def pop_scale(t, t0):
    """entrada com 'salto' para textos"""
    x = (t - t0) / 0.25
    if x <= 0:
        return 0
    if x >= 1:
        return 1
    return 1 + 0.18 * math.sin(x * math.pi) * (1 - x) + (x - 1) * 0  # sobe e assenta


def sky(ctx, top=(0.05, 0.08, 0.2), bot=NAVY):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bot)
    ctx.set_source(g); ctx.paint()


