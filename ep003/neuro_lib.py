#!/usr/bin/env python3
"""Biblioteca de desenho do EP003 (derivada de ep001/neuro_lib.py, sem os recursos da Lua)."""
import math, os
import cairo
import numpy as np
from PIL import Image

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.abspath(__file__))
A = f"{ROOT}/anim"; BLD = f"{ROOT}/build"
NAVY = (0.03, 0.06, 0.13); CYAN = (0.24, 0.88, 1.0); CREAM = (0.96, 0.93, 0.84)
SUN = (1.0, 0.78, 0.35); INK = (1, 1, 1); PINK = (1.0, 0.55, 0.65); QUIET = (0.75, 0.82, 0.95)
GREEN = (0.55, 0.92, 0.32); RED = (1.0, 0.32, 0.32)
KEEP = []


def surf(path, size=None):
    im = Image.open(path).convert("RGBA")
    if size:
        im = im.resize(size, Image.LANCZOS)
    arr = np.array(im); bgra = arr[:, :, [2, 1, 0, 3]].copy(); KEEP.append(bgra)
    return cairo.ImageSurface.create_for_data(bgra, cairo.FORMAT_ARGB32, im.width, im.height)


def ease(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)


def seg(t, a, b):
    return ease((t - a) / (b - a))


class Cover:
    """pinta uma ilustração a cobrir o ecrã: ponto focal (fx,fy) da imagem em (sx,sy), zoom z"""
    def __init__(self, ctx, s, z=1.0, fx=None, fy=None, sx=W / 2, sy=H / 2, rot=0.0, alpha=1.0):
        self.k = max(W / s.get_width(), H / s.get_height()) * z
        self.fx = s.get_width() / 2 if fx is None else fx; self.fy = s.get_height() / 2 if fy is None else fy
        self.sx, self.sy = sx, sy
        ctx.save(); ctx.translate(sx, sy); ctx.rotate(rot); ctx.scale(self.k, self.k)
        ctx.translate(-self.fx, -self.fy); ctx.set_source_surface(s, 0, 0); ctx.paint_with_alpha(alpha); ctx.restore()

    def p(self, ix, iy):
        return self.sx + (ix - self.fx) * self.k, self.sy + (iy - self.fy) * self.k

    def r(self, ir):
        return ir * self.k


def glow(ctx, x, y, r, col, a=0.6):
    if a <= 0.005:
        return
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
    return tw


def rr(ctx, x, y, w, h, r):
    ctx.new_sub_path(); ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); ctx.close_path()


def pop_in(t, t0, d=0.25):
    """escala com salto para entradas"""
    x = (t - t0) / d
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return ease(x) + 0.25 * math.sin(x * math.pi)
