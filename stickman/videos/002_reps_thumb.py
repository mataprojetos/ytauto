"""Capa (thumbnail) do Stickman #002 "Who does the most reps?" — 1080x1920, tudo por código.

    python3 stickman/videos/002_reps_thumb.py   # -> stickman/out/002_thumb.jpg
"""
import math
import os
import random
import sys

import cairo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib.core import H, W, draw_text, ensure_font  # noqa: E402
from lib.fx import add_glow, twinkle  # noqa: E402
from lib import stick as S  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module  # noqa: E402

thumb1 = import_module("001_climb_thumb")  # reutiliza o texto com contorno e as etiquetas
outlined, tag = thumb1.outlined, thumb1.tag

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "out", "002_thumb.jpg")
GOLD = (0.95, 0.72, 0.28)
COL = {"ANGER": (1.0, 0.16, 0.13), "OBSESSION": (0.74, 0.34, 1.0),
       "DISCIPLINE": (0.12, 0.80, 1.0), "MOTIVATION": (1.0, 0.64, 0.10)}
BAR_Y, FLOOR_Y = 1270, 1730


def main():
    ensure_font()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    glow = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx, gctx = cairo.Context(surf), cairo.Context(glow)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    r = random.Random(5)

    # aura vermelha atrás da Anger
    ax = 330
    rg = cairo.RadialGradient(ax, BAR_Y + 120, 20, ax, BAR_Y + 120, 560)
    rg.add_color_stop_rgba(0, 0.95, 0.1, 0.05, 0.55)
    rg.add_color_stop_rgba(1, 0.95, 0.1, 0.05, 0)
    ctx.set_source(rg)
    ctx.paint()

    # barra de ponta a ponta + postes + chão
    for c, wdt, rgba in ((gctx, 20, (1.0, 0.45, 0.35, 0.6)), (ctx, 8, (0.9, 0.9, 0.95, 1))):
        c.set_line_width(wdt)
        c.set_source_rgba(*rgba)
        c.move_to(20, BAR_Y)
        c.line_to(W - 20, BAR_Y)
        c.stroke()
    for x in (34, W - 34):
        ctx.set_source_rgba(0.55, 0.56, 0.62, 0.9)
        ctx.set_line_width(6)
        ctx.move_to(x, BAR_Y)
        ctx.line_to(x, FLOOR_Y)
        ctx.stroke()
    ctx.set_source_rgba(0.8, 0.8, 0.84, 0.6)
    ctx.set_line_width(3)
    ctx.move_to(0, FLOOR_Y)
    ctx.line_to(W, FLOOR_Y)
    ctx.stroke()

    # outros: Obsession e Discipline penduradas, Motivation deitada no chão
    S.set_scale(1.7)
    p_obs = S.pullup_pose(BAR_Y, 600, 0.35, kick=0.4)
    S.draw_figure(ctx, p_obs, color=COL["OBSESSION"], glow=(*COL["OBSESSION"], 0.9), gctx=gctx)
    p_dis = S.pullup_pose(BAR_Y, 800, 0.7, kick=0.3)
    S.draw_figure(ctx, p_dis, color=COL["DISCIPLINE"], glow=(*COL["DISCIPLINE"], 0.9), gctx=gctx)
    p_mot = S.lie_back_pose(FLOOR_Y, 930, 0)
    S.draw_figure(ctx, p_mot, color=COL["MOTIVATION"], glow=(*COL["MOTIVATION"], 0.9), gctx=gctx)

    # Anger grande, queixo acima da barra, com rasto e faíscas
    S.set_scale(2.9)
    pa = S.pullup_pose(BAR_Y, ax, 0.95, kick=0.9, grip=22)
    ghost = S.pullup_pose(BAR_Y, ax, 0.45, kick=0.5, grip=22)
    S.draw_figure(ctx, ghost, color=COL["ANGER"], alpha=0.28, core=0)
    S.draw_figure(ctx, pa, color=(1.0, 0.24, 0.2), glow=(1.0, 0.1, 0.06, 1.3), gctx=gctx)
    S.draw_figure(gctx, pa, color=(0.8, 0.1, 0.05), width=9 * S.K, core=0)
    for _ in range(110):
        x = ax + r.gauss(0, 130)
        y = BAR_Y + r.gauss(40, 120)
        s = r.uniform(1.5, 5)
        for c, k in ((ctx, 1), (gctx, 1.5)):
            c.set_source_rgba(1, 0.3 + r.uniform(0, 0.35), 0.18, r.uniform(0.4, 1))
            c.arc(x, y, s * k, 0, 6.29)
            c.fill()
    for _ in range(14):  # suor
        a = r.uniform(-2.6, -0.5)
        d = r.uniform(70, 150)
        x, y = pa["head"][0] + math.cos(a) * d, pa["head"][1] + math.sin(a) * d
        ctx.set_source_rgba(0.7, 0.88, 1.0, 0.9)
        ctx.arc(x, y, r.uniform(3, 6), 0, 6.29)
        ctx.fill()

    # contadores
    tag(ctx, gctx, 600, BAR_Y - 150, "60", COL["OBSESSION"], 64)
    tag(ctx, gctx, 800, BAR_Y - 190, "64", COL["DISCIPLINE"], 64)
    tag(ctx, gctx, 930, FLOOR_Y - 90, "22", COL["MOTIVATION"], 56)
    tag(ctx, gctx, ax, BAR_Y - 270, "156", (1.0, 0.24, 0.2), 150)
    draw_text(ctx, "REPS", ax, BAR_Y - 225, 40, (1.0, 0.35, 0.3, 1), 10, "center")

    # luz branca/azulada no topo da Anger
    for _ in range(26):
        a, d = r.uniform(0, 6.28), r.uniform(120, 420)
        twinkle(ctx, ax + math.cos(a) * d, BAR_Y - 60 + math.sin(a) * d * 0.7, r.uniform(4, 10),
                (0.8, 0.9, 1.0, r.uniform(0.4, 1)))

    add_glow(surf, glow, scale=2, radius=7, gain=1.6)

    # título
    outlined(ctx, "WHO DOES", W / 2, 330, 150, (0.93, 0.93, 0.93))
    tg = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    tctx = cairo.Context(tg)
    draw_text(tctx, "REPS?", W / 2, 690, 210, (*GOLD, 1), 6, "center")
    add_glow(surf, tg, scale=2, radius=14, gain=0.9)
    outlined(ctx, "THE MOST", W / 2, 490, 150, (0.93, 0.93, 0.93))
    outlined(ctx, "REPS?", W / 2, 690, 210, GOLD, spacing=6)
    draw_text(ctx, "ONLY ONE NEVER STOPS", W / 2, 780, 54, (1, 0.3, 0.26, 1), 6, "center")
    draw_text(ctx, "@ThePsychArena", 40, 1880, 34, (0.9, 0.9, 0.92, 0.75), 2)

    png = OUT.replace(".jpg", "_tmp.png")
    surf.write_to_png(png)
    from PIL import Image
    Image.open(png).convert("RGB").save(OUT, quality=90, optimize=True)
    os.remove(png)
    print(OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
