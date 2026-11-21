"""Assinatura visual da frase de marca "That one made me scratch my head." (Whatifaholic).
Sempre a mesma: cabeça redonda com mão a coçar o topo (3 coçadelas), pontos de interrogação a saltar,
e o texto em duas linhas. Cores livres (cada vídeo passa as suas). Som: lib/sfx/scratch_head.wav no início.

    from brand_scratch import draw_scratch
    draw_scratch(ctx, u, cx, cy, scale=1.0, skin=(...), accent=(...), ink=(1,1,1))   # u = segundos desde o início
Duração recomendada: 1,4–1,8 s.
"""
import math
import cairo


def _ease(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3


def _text(ctx, s, x, y, size, col, a, outline=(0, 0, 0)):
    ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    e = ctx.text_extents(s)
    ctx.move_to(x - e.width / 2 - e.x_bearing, y)
    ctx.text_path(s)
    ctx.set_source_rgba(*outline, a); ctx.set_line_width(size * 0.14); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke_preserve(); ctx.set_source_rgba(*col, a); ctx.fill()


def draw_scratch(ctx, u, cx, cy, scale=1.0, skin=(1.0, 0.82, 0.62), accent=(1.0, 0.8, 0.2), ink=(1, 1, 1),
                 hair=(0.25, 0.16, 0.1), text=True):
    a = _ease(u / 0.18)
    pop = 1 + 0.12 * math.sin(math.pi * min(1, u / 0.25))
    ctx.save(); ctx.translate(cx, cy); ctx.scale(scale * pop, scale * pop)
    # ombros
    ctx.set_source_rgba(*accent, a)
    ctx.move_to(-190, 330); ctx.curve_to(-190, 200, -110, 170, 0, 170); ctx.curve_to(110, 170, 190, 200, 190, 330)
    ctx.close_path(); ctx.fill()
    # cabeça
    ctx.set_source_rgba(*skin, a); ctx.arc(0, 0, 150, 0, 2 * math.pi); ctx.fill()
    ctx.set_source_rgba(*hair, a); ctx.arc(0, -10, 152, math.pi * 1.08, math.pi * 1.92); ctx.close_path(); ctx.fill()
    # olhos (um semicerrado = a pensar) e boca torta
    ctx.set_source_rgba(0.1, 0.07, 0.05, a)
    ctx.arc(-52, 10, 16, 0, 2 * math.pi); ctx.fill()
    ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(32, 8); ctx.line_to(76, 4); ctx.stroke()
    ctx.move_to(-70, -34); ctx.line_to(-30, -44); ctx.stroke()    # sobrancelha levantada
    ctx.move_to(-30, 78); ctx.curve_to(0, 64, 20, 92, 50, 70); ctx.stroke()
    # mão a coçar (3 vaivéns)
    k = math.sin(u * 2 * math.pi * 2.2) if u < 1.4 else 0
    hx, hy = 70 + 38 * k, -150 - 6 * abs(k)
    ctx.set_source_rgba(*skin, a)
    ctx.set_line_width(46); ctx.move_to(175, 260); ctx.curve_to(230, 120, 190, -40, hx + 40, hy + 40); ctx.stroke()  # braço
    ctx.save(); ctx.translate(hx, hy); ctx.rotate(-0.5 + 0.15 * k)
    ctx.arc(0, 0, 42, 0, 2 * math.pi); ctx.fill()
    for i in range(4):
        ctx.set_line_width(20); ctx.move_to(-30 + i * 20, -10); ctx.line_to(-34 + i * 21, -58 + abs(i - 1.5) * 6); ctx.stroke()
    ctx.restore()
    ctx.set_source_rgba(0, 0, 0, 0.25 * a); ctx.set_line_width(3)
    # pontos de interrogação a saltar
    for i, (qx, qy, ph) in enumerate(((-210, -150, 0.0), (210, -230, 0.25), (-150, -260, 0.5))):
        b = _ease((u - 0.15 - ph * 0.6) / 0.2)
        if b > 0:
            _text(ctx, "?", qx, qy - 18 * math.sin(u * 7 + i), 110, accent, a * b)
    ctx.restore()
    if text:
        ta = _ease((u - 0.1) / 0.2)
        _text(ctx, "THAT ONE MADE ME", cx, cy + 420 * scale, 74 * scale, ink, ta)
        _text(ctx, "SCRATCH MY HEAD", cx, cy + 510 * scale, 92 * scale, accent, ta)
