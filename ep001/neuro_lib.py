#!/usr/bin/env python3
"""Neuronaut — biblioteca de desenho partilhada (camadas, Terra, Lua, texto, brilho)."""
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


bg, _ = surf(f"{A}/sky_city.png")
reef, _ = surf(f"{A}/reef.png")
MOON_R = 210
moon, moon_px = surf(f"{A}/moon.png", (MOON_R * 2 + 40, MOON_R * 2 + 40))
small_moon, _ = surf(f"{A}/moon.png", (150, 150))
tiny_moon, _ = surf(f"{A}/moon.png", (90, 90))
world, _ = surf(f"{A}/world.png")
MX, MY = 540, 780

pts = []
c0 = MOON_R + 20
for _ in range(2600):
    a = random.random() * 6.283; r = MOON_R * math.sqrt(random.random()) * 0.97
    x, y = c0 + r * math.cos(a), c0 + r * math.sin(a)
    pts.append((x - c0, y - c0, tuple(moon_px[int(y), int(x)][:3] / 255.0), random.uniform(-1, 1),
                random.uniform(0.6, 1.4), random.uniform(1.4, 3.6)))
stars = [(random.uniform(0, W), random.uniform(0, H * 0.62), random.uniform(0.8, 2.6),
          random.uniform(0, 6.28), random.uniform(0.6, 2.2)) for _ in range(140)]
eggs = [(random.uniform(60, W - 60), random.uniform(0, 1), random.uniform(2, 5), random.uniform(0.5, 1.5),
         random.uniform(0, 6.28)) for _ in range(420)]


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


def draw_moon(ctx, x, y, s, r, alpha=1.0, clip_x=None):
    if alpha <= 0.01:
        return
    ctx.save(); ctx.arc(x, y, r, 0, 6.283); ctx.clip()
    if clip_x is not None:
        ctx.rectangle(clip_x, 0, W, H); ctx.clip()
    w = s.get_width(); sc = 2 * r / (w - 40 * w / (2 * MOON_R + 40)) if s is moon else 2 * r / w
    ctx.translate(x, y); ctx.scale(sc, sc); ctx.set_source_surface(s, -w / 2, -w / 2)
    ctx.paint_with_alpha(alpha); ctx.restore()


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


def earth(ctx, x, y, r, a=1.0, rot=0.0):
    if a <= 0.01:
        return
    glow(ctx, x, y, r * 1.4, CYAN, 0.25 * a)
    ctx.save(); ctx.arc(x, y, r, 0, 6.283); ctx.clip()
    mh = 2 * r; mw = mh * world.get_width() / world.get_height()
    k = mh / world.get_height()
    off = -(rot % 1.0) * mw
    for i in (0, 1):
        ctx.save(); ctx.translate(x - r * 1.2 + off + i * mw, y - r); ctx.scale(k, k)
        ctx.set_source_surface(world, 0, 0); ctx.paint_with_alpha(a); ctx.restore()
    g = cairo.RadialGradient(x - r * 0.35, y - r * 0.35, r * 0.1, x, y, r)  # volume
    g.add_color_stop_rgba(0, 1, 1, 1, 0.10 * a); g.add_color_stop_rgba(0.7, 0, 0, 0, 0.0)
    g.add_color_stop_rgba(1, 0, 0, 0.05, 0.65 * a)
    ctx.set_source(g); ctx.paint(); ctx.restore()
    ctx.set_source_rgba(*CYAN, 0.75 * a); ctx.set_line_width(3); ctx.arc(x, y, r, 0, 6.283); ctx.stroke()


def bulge(ctx, x, y, r, ang, k, col=CYAN, a=0.45):
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.scale(r * (1 + k), r * (1 - k * 0.35))
    ctx.arc(0, 0, 1, 0, 6.283); ctx.restore()
    ctx.set_source_rgba(*col, a); ctx.fill_preserve()
    ctx.set_source_rgba(*col, min(1, a + 0.35)); ctx.set_line_width(3); ctx.stroke()


def sky(ctx, top=(0.05, 0.08, 0.2), bot=NAVY):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bot)
    ctx.set_source(g); ctx.paint()


