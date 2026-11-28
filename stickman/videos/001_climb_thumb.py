"""Capa (thumbnail) do Stickman #001 "Who reaches the top?" — 1080x1920, tudo por código.

    python3 stickman/videos/001_climb_thumb.py   # -> stickman/out/climb_thumb.jpg (+ .png)
"""
import math
import os
import random
import sys

import cairo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib.core import H, W, draw_text, ensure_font, text_width  # noqa: E402
from lib.fx import add_glow, twinkle  # noqa: E402
from lib import stick as S  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "out", "climb_thumb.jpg")
GOLD = (0.95, 0.72, 0.28)
COL = {"ANGER": (1.0, 0.16, 0.13), "OBSESSION": (0.74, 0.34, 1.0),
       "DISCIPLINE": (0.12, 0.80, 1.0), "MOTIVATION": (1.0, 0.64, 0.10)}

# encosta: do canto inferior esquerdo até ao cume (direita), com descida depois
X0, Y0 = -40, 1720
XP, YP = 850, 1300


def ground(x):
    up = Y0 + (YP - Y0) * (x - X0) / (XP - X0) + 6 * math.sin(x * 0.02)
    down = YP + (x - XP) * 1.1
    k = 14.0
    m = max(up, down)
    return m + k * math.log(math.exp((up - m) / k) + math.exp((down - m) / k))


def line(ctx, gctx):
    for c, wdt, rgba in ((gctx, 16, (1.0, 0.5, 0.4, 0.55)), (ctx, 4, (0.9, 0.9, 0.95, 0.9))):
        c.set_line_width(wdt)
        c.set_source_rgba(*rgba)
        c.move_to(-20, ground(-20))
        for x in range(-20, W + 21, 4):
            c.line_to(x, ground(x))
        c.stroke()


def figure_at(ctx, gctx, name, xh, scale, mode, glow_k=1.0, ph=0.8):
    S.set_scale(scale)
    R, D = 28 * scale, 82 * scale
    col = COL[name]
    if mode == "sit":
        pose = S.sit_pose(ground, xh)
        c = None
    else:
        c = S.rest_center(ground, xh + D, R)
        tgt = (c[0] - R * 0.93, c[1] - R * 0.30)
        lean = 56 if mode == "rage" else 46
        pose = S.push_pose(ground, xh, ph, tgt, lean=lean, stride=22 if mode == "rage" else 16, lift=12)
        S.draw_boulder(ctx, c, R, 0.7, glow=(1.0, 0.3, 0.15, 1.0) if mode == "rage" else None)
    S.draw_figure(ctx, pose, color=col, glow=(*col, glow_k), gctx=gctx)
    if mode == "rage":
        S.draw_figure(gctx, pose, color=tuple(v * 0.8 for v in col), width=8 * scale, core=0)
    return pose, c


def tag(ctx, gctx, x, y, txt, col, size):
    draw_text(ctx, txt, x + 3, y + 4, size, (0, 0, 0, 0.8), 2, "center")
    draw_text(ctx, txt, x, y, size, (*col, 1), 2, "center")
    draw_text(gctx, txt, x, y, size, (*col, 0.7), 2, "center")


def outlined(ctx, txt, x, y, size, col, spacing=4, sx=0.92, glow=None):
    ctx.save()
    ctx.scale(sx, 1)
    x /= sx
    w = text_width(ctx, txt, size, spacing)
    ctx.select_font_face("Oswald", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    xx = x - w / 2
    for ch in txt:
        ctx.move_to(xx, y)
        ctx.text_path(ch)
        xx += ctx.text_extents(ch).x_advance + spacing
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(0, 0, 0, 1)
    ctx.set_line_width(16)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*col, 1)
    ctx.fill()
    ctx.restore()


def main():
    ensure_font()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    glow = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx, gctx = cairo.Context(surf), cairo.Context(glow)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()

    # luz no cume
    cx, cy = XP + 10, YP - 160
    rad = cairo.RadialGradient(cx, cy, 0, cx, cy, 760)
    rad.add_color_stop_rgba(0, 0.92, 0.97, 1.0, 0.55)
    rad.add_color_stop_rgba(0.15, 0.6, 0.78, 1.0, 0.28)
    rad.add_color_stop_rgba(0.55, 0.3, 0.45, 0.9, 0.08)
    rad.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(rad)
    ctx.paint()
    r = random.Random(3)
    for _ in range(42):
        a, d = r.uniform(0, 6.28), r.uniform(80, 560)
        twinkle(ctx, cx + math.cos(a) * d, cy + math.sin(a) * d * 0.8, r.uniform(4, 11),
                (0.78, 0.9, 1.0, r.uniform(0.4, 1)))

    line(ctx, gctx)

    # bandeira dourada no cume
    fx, fy = XP + 40, ground(XP + 40)
    ctx.set_source_rgba(0.9, 0.9, 0.9, 1)
    ctx.set_line_width(6)
    ctx.move_to(fx, fy)
    ctx.line_to(fx, fy - 150)
    ctx.stroke()
    for c in (ctx, gctx):
        c.move_to(fx, fy - 150)
        c.line_to(fx + 90, fy - 128)
        c.line_to(fx, fy - 102)
        c.close_path()
        c.set_source_rgba(*GOLD, 1)
        c.fill()

    # bonecos: Motivation sentada lá em baixo, Discipline e Obsession a meio, Anger quase no topo
    tags = []
    p, _ = figure_at(ctx, gctx, "MOTIVATION", 45, 1.45, "sit", 0.9)
    tags.append((p["head"], "50%", COL["MOTIVATION"], 50))
    p, _ = figure_at(ctx, gctx, "DISCIPLINE", 175, 1.45, "push", 0.9, ph=2.2)
    tags.append((p["head"], "65%", COL["DISCIPLINE"], 52))
    p, _ = figure_at(ctx, gctx, "OBSESSION", 345, 1.6, "push", 1.0, ph=0.3)
    tags.append((p["head"], "90%", COL["OBSESSION"], 56))
    pa, ca = figure_at(ctx, gctx, "ANGER", 575, 2.5, "rage", 1.3, ph=1.1)

    # faíscas vermelhas da Anger
    for _ in range(80):
        x = pa["hip"][0] + r.gauss(-70, 70)
        y = pa["hip"][1] + r.gauss(-20, 55)
        s = r.uniform(1.5, 4.5)
        for c, k in ((ctx, 1), (gctx, 1.4)):
            c.set_source_rgba(1, 0.35 + r.uniform(0, 0.3), 0.2, r.uniform(0.4, 1))
            c.arc(x, y, s * k, 0, 6.29)
            c.fill()
    for (hx, hy), txt, col, sz in tags:
        tag(ctx, gctx, hx, hy - 45, txt, col, sz)
    tag(ctx, gctx, pa["head"][0] - 20, pa["head"][1] - 62, "99%", COL["ANGER"], 84)

    add_glow(surf, glow, scale=2, radius=7, gain=1.6)

    # título: 3 palavras grandes com contorno
    outlined(ctx, "WHO REACHES", W / 2, 520, 150, (0.93, 0.93, 0.93))
    tg = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    tctx = cairo.Context(tg)
    draw_text(tctx, "THE TOP?", W / 2, 710, 190, (*GOLD, 1), 6, "center")
    add_glow(surf, tg, scale=2, radius=14, gain=0.9)
    outlined(ctx, "THE TOP?", W / 2, 710, 190, GOLD, spacing=6)
    draw_text(ctx, "ONLY ONE MAKES IT", W / 2, 800, 54, (1, 0.3, 0.26, 1), 6, "center")
    draw_text(ctx, "@ThePsychArena", 40, 1880, 34, (0.9, 0.9, 0.92, 0.75), 2)

    png = OUT.replace(".jpg", "_tmp.png")
    surf.write_to_png(png)
    from PIL import Image
    Image.open(png).convert("RGB").save(OUT, quality=90, optimize=True)
    os.remove(png)
    print(OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
