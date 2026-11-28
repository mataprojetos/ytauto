"""Elementos de ecrã partilhados (vindos do #001): título com brilho, etiqueta da faixa e pensamentos
que nascem da cabeça, ficam por cima e caem para trás até ao chão."""
import math

import cairo

from .core import W, clamp, draw_text, lerp, text_width
from .fx import blur_surface
from . import stick as S

RED = (0.80, 0.14, 0.15)
GOLD = (0.86, 0.66, 0.30)


def make_title(parts, height, size=80, spacing=3.5, base=205, sx=0.94):
    """parts: [(texto, cor, brilho?)]. Devolve uma superfície W x height."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, height)
    glow = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, height)
    ctx, gctx = cairo.Context(surf), cairo.Context(glow)
    total = sum(text_width(ctx, p[0], size, spacing) for p in parts) * sx
    x = (W - total) / 2 / sx
    for c in (ctx, gctx):
        c.scale(sx, 1)
    for txt, col, glw in parts:
        draw_text(ctx, txt, x + 3, base + 4, size, (0, 0, 0, 0.6), spacing)
        if glw:
            draw_text(gctx, txt, x, base, size, (*col, 1.0), spacing)
        x += draw_text(ctx, txt, x, base, size, (*col, 1.0), spacing) + spacing
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, height)
    o = cairo.Context(out)
    o.set_source_surface(blur_surface(glow, 14), 0, 0)
    o.paint_with_alpha(0.9)
    o.set_source_surface(blur_surface(glow, 5), 0, 0)
    o.paint_with_alpha(0.5)
    o.set_source_surface(surf, 0, 0)
    o.paint()
    return out


def draw_label(ctx, name):
    """Triângulo + nome a vermelho no canto da faixa. Devolve a largura do nome."""
    ctx.move_to(14, 25)
    ctx.line_to(22, 30)
    ctx.line_to(14, 35)
    ctx.close_path()
    ctx.set_source_rgba(*RED, 0.9)
    ctx.fill()
    draw_text(ctx, name, 32, 40, 25, (0, 0, 0, 0.7), 2.4)
    return draw_text(ctx, name, 30, 38, 25, (*RED, 1.0), 2.4)


def ease_back(u):
    u = clamp(u)
    k = 1.9
    return 1 + (k + 1) * (u - 1) ** 3 + k * (u - 1) ** 2


T_GROW, T_FALL, T_REST = 0.35, 0.55, 1.4


def t_hold(txt):
    return 1.45 + 0.03 * len(txt)


def draw_thoughts(ctx, gctx, thoughts, t, f, heads, g, rnd, fps, back=130, rise=44):
    """thoughts: [(início, texto[, estilo])], estilo 'w' branco, 'r' vermelho, 'R' vermelho a tremer
    com brilho. heads: lista de posições da cabeça por frame. g(x): altura do chão."""
    for item in thoughts:
        t0, txt = item[0], item[1]
        style = item[2] if len(item) > 2 else "w"
        hold = t_hold(txt)
        age = t - t0
        if age < 0 or age > T_GROW + hold + T_FALL + T_REST:
            continue
        size = 38 if style == "R" else 34
        alpha, ang = 1.0, 0.0
        head = heads[f]
        if age < T_GROW + hold:
            e = ease_back(age / T_GROW)
            sc = 0.12 + 0.88 * e
            x, y = head[0], head[1] - S.HEAD_R - 6 - rise * clamp(age / T_GROW)
        else:
            fs = min(f, int(round((t0 + T_GROW + hold) * fps)))
            hx, hy = heads[fs]
            p0 = (hx, hy - S.HEAD_R - 6 - rise)
            lx = hx - back
            ly = g(lx) - 3
            land_ang = math.atan2(g(lx + 6) - g(lx - 6), 12)
            u = (age - T_GROW - hold) / T_FALL
            if u < 1:
                x = lerp(p0[0], lx, u)
                y = lerp(p0[1], ly, u * u) - 14 * math.sin(math.pi * u) * (1 - u)
                ang = land_ang * u - 0.5 * math.sin(math.pi * u)
                sc = lerp(1.0, 0.85, u)
            else:
                r = age - T_GROW - hold - T_FALL
                x, y = lx, ly - 6 * abs(math.sin(r * 18)) * math.exp(-r * 9)
                ang, sc = land_ang, 0.85
                alpha = 1 - clamp((r - T_REST * 0.4) / (T_REST * 0.6))
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(ang)
        ctx.scale(sc, sc)
        if style == "R":
            jit = lambda i: (rnd.uniform(-2.4, 2.4), rnd.uniform(-2.4, 2.4))
            draw_text(ctx, txt, 0, 0, size, (1, 0.22, 0.18, alpha), 3, "center", jitter=jit)
            gctx.save()
            gctx.translate(x, y)
            gctx.rotate(ang)
            gctx.scale(sc, sc)
            draw_text(gctx, txt, 0, 0, size, (1, 0.1, 0.06, 0.8 * alpha), 3, "center")
            gctx.restore()
        else:
            col = (0.95, 0.24, 0.20) if style == "r" else (0.95, 0.95, 0.95)
            draw_text(ctx, txt, 2, 3, size, (0, 0, 0, 0.7 * alpha), 2.4, "center")
            draw_text(ctx, txt, 0, 0, size, (*col, alpha), 2.4, "center")
        ctx.restore()
