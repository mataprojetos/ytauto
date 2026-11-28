"""Branding do canal The Psych Arena (@ThePsychArena): perfil 800x800 (3 opções) e banner 2560x1440.

Tudo por código (pycairo). Fonte: Anton (OFL), cópia em stickman/branding/fonts/ (instalar em ~/.fonts).
Uso: python3 stickman/branding/make_branding.py
"""
import math
import os

import cairo

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "Anton"

BG = (0.043, 0.039, 0.039)        # quase preto
BG2 = (0.085, 0.075, 0.072)       # brilho de fundo
WHITE = (0.95, 0.94, 0.91)
RED = (0.56, 0.11, 0.11)          # vermelho-escuro
RED_HI = (0.78, 0.17, 0.15)
GOLD = (0.82, 0.65, 0.30)
GREY = (0.45, 0.43, 0.41)


def rgb(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


def bg(ctx, w, h, glow=None, glow_r=None, glow_col=BG2):
    rgb(ctx, BG)
    ctx.paint()
    cx, cy = glow or (w / 2, h / 2)
    r = glow_r or max(w, h) * 0.6
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
    g.add_color_stop_rgba(0, *glow_col, 1)
    g.add_color_stop_rgba(1, *BG, 1)
    ctx.set_source(g)
    ctx.paint()


def hooded(ctx, x, y, s, lw, col=WHITE, pose="stand", face=False, outline=0.0):
    """Stickman de capuz. (x, y) = pés no chão; s = altura total.
    outline > 0: desenha só o contorno preto (chamar antes do boneco a cores)."""
    ctx.save()
    if outline:
        col = (0, 0, 0)
        lw = lw + 2 * outline
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_width(lw)
    rgb(ctx, col)
    hr = s * 0.095                     # raio da cabeça
    hip = (x, y - s * 0.45)
    neck = (x, y - s * 0.76)
    head = (x, y - s * 0.76 - hr * 1.15)
    # capuz: contorno com bico atrás + abertura escura da cara
    ctx.save()
    ctx.translate(*head)
    ctx.new_path()
    ctx.move_to(-hr * 1.05, hr * 0.9)
    ctx.curve_to(-hr * 1.45, -hr * 0.4, -hr * 0.9, -hr * 1.55, hr * 0.05, -hr * 1.5)
    ctx.curve_to(hr * 0.95, -hr * 1.45, hr * 1.35, -hr * 0.5, hr * 1.1, hr * 0.85)
    ctx.close_path()
    if outline:
        ctx.set_line_width(2 * outline)
        ctx.stroke_preserve()
    ctx.fill()
    if face:
        rgb(ctx, BG)
        ctx.arc(hr * 0.22, hr * 0.05, hr * 0.62, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()
    rgb(ctx, col)
    # tronco
    ctx.move_to(*neck)
    ctx.line_to(*hip)
    ctx.stroke()
    sh = (x, y - s * 0.70)
    if pose == "stand":
        arms = [((x - s * 0.13, y - s * 0.56), (x - s * 0.15, y - s * 0.42)),
                ((x + s * 0.13, y - s * 0.56), (x + s * 0.15, y - s * 0.42))]
        legs = [((x - s * 0.08, y - s * 0.23), (x - s * 0.12, y)),
                ((x + s * 0.08, y - s * 0.23), (x + s * 0.12, y))]
    elif pose == "win":   # braço erguido
        arms = [((x - s * 0.14, y - s * 0.58), (x - s * 0.17, y - s * 0.44)),
                ((x + s * 0.13, y - s * 0.84), (x + s * 0.18, y - s * 1.02))]
        legs = [((x - s * 0.09, y - s * 0.23), (x - s * 0.14, y)),
                ((x + s * 0.09, y - s * 0.23), (x + s * 0.14, y))]
    elif pose == "run":
        arms = [((x - s * 0.12, y - s * 0.60), (x - s * 0.20, y - s * 0.70)),
                ((x + s * 0.12, y - s * 0.56), (x + s * 0.22, y - s * 0.62))]
        legs = [((x + s * 0.14, y - s * 0.28), (x + s * 0.10, y - s * 0.05)),
                ((x - s * 0.06, y - s * 0.22), (x - s * 0.22, y - s * 0.12))]
    elif pose == "climb":  # picareta erguida
        arms = [((x + s * 0.10, y - s * 0.84), (x + s * 0.20, y - s * 0.98)),
                ((x - s * 0.13, y - s * 0.57), (x - s * 0.16, y - s * 0.44))]
        legs = [((x - s * 0.06, y - s * 0.24), (x - s * 0.13, y)),
                ((x + s * 0.12, y - s * 0.25), (x + s * 0.12, y))]
    elif pose == "tired":  # ajoelhado
        hip2 = (x, y - s * 0.30)
        ctx.move_to(*neck)
        ctx.line_to(*hip2)
        ctx.stroke()
        arms = [((x - s * 0.10, y - s * 0.48), (x - s * 0.14, y - s * 0.30)),
                ((x + s * 0.10, y - s * 0.48), (x + s * 0.13, y - s * 0.30))]
        legs = [((x - s * 0.16, y - s * 0.18), (x - s * 0.10, y)),
                ((x + s * 0.14, y - s * 0.10), (x + s * 0.28, y))]
        hip = hip2
    for e, h in arms:
        ctx.move_to(*sh)
        ctx.line_to(*e)
        ctx.line_to(*h)
        ctx.stroke()
    for k, f in legs:
        ctx.move_to(*hip)
        ctx.line_to(*k)
        ctx.line_to(*f)
        ctx.stroke()
    if pose == "climb":   # picareta
        hx, hy = x + s * 0.20, y - s * 0.98
        ctx.set_line_width(lw * 0.8)
        rgb(ctx, col if outline else GOLD)
        ctx.move_to(hx, hy)
        ctx.line_to(hx - s * 0.10, hy - s * 0.12)
        ctx.stroke()
        ctx.move_to(hx - s * 0.20, hy - s * 0.06)
        ctx.curve_to(hx - s * 0.12, hy - s * 0.17, hx - s * 0.04, hy - s * 0.16, hx + s * 0.02, hy - s * 0.10)
        ctx.stroke()
    ctx.restore()


def text(ctx, s, x, y, size, col, align="center", spacing=0.0, font=FONT, alpha=1.0):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    widths = [ctx.text_extents(ch).x_advance for ch in s]
    total = sum(widths) + spacing * size * (len(s) - 1)
    if align == "center":
        x -= total / 2
    elif align == "right":
        x -= total
    rgb(ctx, col, alpha)
    for ch, w in zip(s, widths):
        ctx.move_to(x, y)
        ctx.show_text(ch)
        x += w + spacing * size
    return total


def diamond(ctx, x, y, r, col):
    rgb(ctx, col)
    ctx.move_to(x, y - r)
    ctx.line_to(x + r * 0.7, y)
    ctx.line_to(x, y + r)
    ctx.line_to(x - r * 0.7, y)
    ctx.close_path()
    ctx.fill()


# ---------------------------------------------------------------- perfis
def profile_a(ctx, S=800):
    """Campeão: stickman de capuz com braço erguido dentro de um anel dourado (a arena)."""
    bg(ctx, S, S, glow=(S / 2, S * 0.62), glow_r=S * 0.55, glow_col=(0.20, 0.06, 0.05))
    ctx.set_line_width(S * 0.028)
    rgb(ctx, GOLD)
    ctx.arc(S / 2, S / 2, S * 0.40, 0, 2 * math.pi)
    ctx.stroke()
    # chão vermelho
    ctx.set_line_width(S * 0.022)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    rgb(ctx, RED_HI)
    ctx.move_to(S * 0.25, S * 0.74)
    ctx.line_to(S * 0.75, S * 0.74)
    ctx.stroke()
    hooded(ctx, S * 0.48, S * 0.735, S * 0.50, S * 0.040, pose="win")
    diamond(ctx, S * 0.57, S * 0.17, S * 0.045, GOLD)


def profile_b(ctx, S=800):
    """Duelo: dois stickmen frente a frente (branco vs vermelho) com faísca dourada."""
    bg(ctx, S, S, glow=(S / 2, S * 0.5), glow_r=S * 0.5, glow_col=(0.16, 0.12, 0.06))
    rgb(ctx, GOLD)
    cx, cy = S / 2, S * 0.40
    for i in range(8):
        a = i * math.pi / 4
        r1, r2 = S * 0.03, S * (0.11 if i % 2 == 0 else 0.07)
        ctx.set_line_width(S * 0.018)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(cx + r1 * math.cos(a), cy + r1 * math.sin(a))
        ctx.line_to(cx + r2 * math.cos(a), cy + r2 * math.sin(a))
        ctx.stroke()
    ctx.save()
    hooded(ctx, S * 0.30, S * 0.80, S * 0.56, S * 0.042, col=WHITE, pose="stand")
    ctx.restore()
    ctx.save()
    ctx.translate(S, 0)
    ctx.scale(-1, 1)
    hooded(ctx, S * 0.30, S * 0.80, S * 0.56, S * 0.042, col=RED_HI, pose="stand")
    ctx.restore()
    rgb(ctx, GOLD)
    ctx.set_line_width(S * 0.016)
    ctx.move_to(S * 0.14, S * 0.82)
    ctx.line_to(S * 0.86, S * 0.82)
    ctx.stroke()


def profile_c(ctx, S=800):
    """Monograma: 'PA' condensado com o capuz no lugar do topo do A, risca vermelha."""
    bg(ctx, S, S, glow=(S / 2, S * 0.45), glow_r=S * 0.6)
    size = S * 0.62
    ctx.select_font_face(FONT)
    ctx.set_font_size(size)
    wp = ctx.text_extents("P").x_advance
    wa = ctx.text_extents("A").x_advance
    gap = -S * 0.005
    x0 = S / 2 - (wp + wa + gap) / 2
    base = S * 0.73
    rgb(ctx, WHITE)
    ctx.move_to(x0, base)
    ctx.show_text("P")
    rgb(ctx, GOLD)
    ctx.move_to(x0 + wp + gap, base)
    ctx.show_text("A")
    # faixa vermelha por baixo
    rgb(ctx, RED_HI)
    ctx.rectangle(S * 0.20, S * 0.79, S * 0.60, S * 0.035)
    ctx.fill()
    # mini stickman de capuz a "subir" o A
    hooded(ctx, x0 + wp + gap + wa * 0.52, base - size * 0.80, S * 0.17, S * 0.016, pose="win")


def hood_head(ctx, cx, cy, hr, col, outline=0.0):
    """Cabeça com capuz (virada para a direita). outline > 0: só o contorno preto dessa espessura."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.new_path()
    ctx.move_to(-hr * 1.05, hr * 0.9)
    ctx.curve_to(-hr * 1.45, -hr * 0.4, -hr * 0.9, -hr * 1.55, hr * 0.05, -hr * 1.5)
    ctx.curve_to(hr * 0.95, -hr * 1.45, hr * 1.35, -hr * 0.5, hr * 1.1, hr * 0.85)
    ctx.close_path()
    if outline:
        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(outline * 2)
        ctx.stroke_preserve()
        ctx.fill()
    else:
        rgb(ctx, col)
        ctx.fill()
    ctx.restore()


GREEN = (0.42, 1.0, 0.45)   # verde vivo claro
PURPLE = (0.70, 0.45, 1.0)  # roxo
BLUE = (0.30, 0.72, 1.0)    # azul


def fencer(ctx, S, col, lw, outline=0.0):
    """Stickman de capuz em investida para a direita, espada erguida para o centro.
    outline > 0 desenha só o contorno preto (chamar antes, com a mesma geometria)."""
    P = lambda x, y: (x * S, y * S)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if outline:
        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(lw + outline * 2)
    else:
        rgb(ctx, col)
        ctx.set_line_width(lw)
    hip, neck, sh = P(0.22, 0.57), P(0.29, 0.39), P(0.28, 0.42)
    for pts in ([neck, hip],
                [hip, P(0.33, 0.68), P(0.37, 0.81)],      # perna da frente
                [hip, P(0.14, 0.69), P(0.07, 0.81)],      # perna de trás
                [sh, P(0.35, 0.41), P(0.40, 0.34)],       # braço da espada
                [sh, P(0.19, 0.46), P(0.12, 0.40)]):      # braço de equilíbrio
        ctx.move_to(*pts[0])
        for q in pts[1:]:
            ctx.line_to(*q)
        ctx.stroke()
    hood_head(ctx, *P(0.315, 0.30), S * 0.058, col, outline)
    if outline:
        return
    # espada: lâmina dourada néon (halo em camadas + núcleo claro) + guarda dourada
    hx, hy = P(0.40, 0.34)
    tx, ty = P(0.70, 0.07)
    for wmul, a in ((3.6, 0.07), (2.6, 0.12), (1.8, 0.22), (1.15, 0.55)):
        ctx.set_line_width(lw * wmul)
        ctx.set_source_rgba(1.0, 0.76, 0.22, a)
        ctx.move_to(hx, hy)
        ctx.line_to(tx, ty)
        ctx.stroke()
    ctx.set_line_width(lw * 0.62)
    ctx.set_source_rgb(1.0, 0.84, 0.40)
    ctx.move_to(hx, hy)
    ctx.line_to(tx, ty)
    ctx.stroke()
    ctx.set_line_width(lw * 0.22)
    ctx.set_source_rgb(1.0, 0.97, 0.82)
    ctx.move_to(hx, hy)
    ctx.line_to(tx, ty)
    ctx.stroke()
    dx, dy = (tx - hx), (ty - hy)
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    gx, gy = hx + ux * S * 0.02, hy + uy * S * 0.02
    ctx.set_line_width(lw * 0.7)
    rgb(ctx, GOLD)
    ctx.move_to(gx - uy * S * 0.032, gy + ux * S * 0.032)
    ctx.line_to(gx + uy * S * 0.032, gy - ux * S * 0.032)
    ctx.stroke()


def stacked_title(ctx, S, top, bottom, lines):
    """Nome em várias linhas, centrado em x = S/2, entre top e bottom. lines = [(texto, largura, cor)]."""
    ctx.select_font_face(FONT)
    items = []
    for t, wfrac, col in lines:
        ctx.set_font_size(100)
        e = ctx.text_extents(t)
        size = 100 * (wfrac * S) / e.width
        ctx.set_font_size(size)
        items.append((t, size, col, ctx.text_extents(t)))
    gap = S * 0.018
    total = sum(e.height for *_, e in items) + gap * (len(items) - 1)
    y = top + ((bottom - top) - total) / 2
    for t, size, col, e in items:
        ctx.set_font_size(size)
        x = S / 2 - e.width / 2 - e.x_bearing
        ctx.move_to(x, y - e.y_bearing)
        ctx.text_path(t)
        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(S * 0.012)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
        rgb(ctx, col)
        ctx.fill()
        y += e.height + gap


def profile_d(ctx, S=800):
    """Duelo de espadas: verde vs vermelho com contorno preto, lâminas douradas néon,
    nome do canal em 3 linhas entre o choque das espadas e o chão."""
    bg(ctx, S, S, glow=(S / 2, S * 0.26), glow_r=S * 0.55, glow_col=(0.19, 0.13, 0.06))
    lw = S * 0.044
    ol = S * 0.012
    k = 0.80                                   # encolher tudo para caber no círculo
    ctx.translate(S * (1 - k) / 2, S * (1 - k) / 2 + S * 0.03)
    ctx.scale(k, k)

    def both(outline):
        ctx.save()
        fencer(ctx, S, GREEN, lw, outline)
        ctx.restore()
        ctx.save()
        ctx.translate(S, 0)
        ctx.scale(-1, 1)
        fencer(ctx, S, RED_HI, lw, outline)
        ctx.restore()

    both(ol)
    both(0)
    # nome do canal: do choque das espadas até ao chão
    stacked_title(ctx, S, S * 0.36, S * 0.80,
                  [("THE", 0.11, WHITE), ("PSYCH", 0.22, WHITE), ("ARENA", 0.22, GOLD)])
    # chão branco
    rgb(ctx, WHITE)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(S * 0.016)
    ctx.move_to(S * 0.02, S * 0.825)
    ctx.line_to(S * 0.98, S * 0.825)
    ctx.stroke()


# ---------------------------------------------------------------- banner
def banner(ctx, W=2560, H=1440):
    bg(ctx, W, H, glow=(W / 2, H / 2), glow_r=W * 0.45, glow_col=(0.13, 0.08, 0.06))
    sx, sy, sw, sh = (W - 1546) / 2, (H - 423) / 2, 1546, 423
    # linhas finas de pista (só visíveis em TV) sem figuras
    for ly in (180, 330, 1110, 1260):
        rgb(ctx, GREY, 0.18)
        ctx.set_line_width(2)
        ctx.move_to(0, ly)
        ctx.line_to(W, ly)
        ctx.stroke()
    # faixa visível em computador: chão + bonecos à esquerda e à direita da zona segura
    ground = sy + sh - 70
    rgb(ctx, GREY, 0.45)
    ctx.set_line_width(3)
    for x1, x2 in ((40, sx - 40), (sx + sw + 40, W - 40)):
        ctx.move_to(x1, ground)
        ctx.line_to(x2, ground)
        ctx.stroke()
    figs = [(120, "MOTIVATION", "tired", GREEN), (285, "OBSESSION", "run", PURPLE),
            (445, "ANGER", "stand", RED_HI), (2140, "DISCIPLINE", "climb", BLUE)]
    for x, name, pose, col in figs:
        hooded(ctx, x, ground - 3, 170, 5.5, col=col, pose=pose, outline=3.0)
        hooded(ctx, x, ground - 3, 170, 5.5, col=col, pose=pose)
        text(ctx, name, x, ground - 230, 22, RED_HI, spacing=0.12)
    # o prémio: diamantes dourados à direita
    for (dx, dy, r) in [(2330, ground - 60, 34), (2400, ground - 120, 20), (2270, ground - 150, 14), (2440, ground - 40, 12)]:
        diamond(ctx, dx, dy, r, GOLD)
    # zona segura: 1546x423 centrada
    cy = sy + sh / 2
    # título
    ctx.select_font_face(FONT)
    size = 185
    ctx.set_font_size(size)
    t1, t2 = "THE PSYCH ", "ARENA"
    w1 = ctx.text_extents(t1).x_advance
    w2 = ctx.text_extents(t2).x_advance
    x0 = W / 2 - (w1 + w2) / 2
    base = cy + 55
    rgb(ctx, WHITE)
    ctx.move_to(x0, base)
    ctx.show_text(t1)
    rgb(ctx, GOLD)
    ctx.move_to(x0 + w1, base)
    ctx.show_text(t2)
    # linha vermelha + tagline
    rgb(ctx, RED_HI)
    ctx.rectangle(W / 2 - 330, base + 32, 660, 7)
    ctx.fill()
    text(ctx, "YOUR MIND. ONE ARENA. ONLY ONE WINS.", W / 2, base + 105, 46, WHITE, spacing=0.10, alpha=0.9)
    # topo da zona segura: rótulo pequeno
    text(ctx, "MOTIVATION  vs  DISCIPLINE  vs  OBSESSION", W / 2, sy + 62, 34, RED_HI, spacing=0.12)
    return (sx, sy, sw, sh)


# ---------------------------------------------------------------- pré-visualizações
def render(fn, w, h):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    ctx = cairo.Context(surf)
    r = fn(ctx)
    return surf, r


def circle_preview(surfs, path):
    """Cada opção: em círculo grande (300) e em 98/48/32 px, sobre fundo claro e escuro."""
    W, rowh = 1400, 380
    out = cairo.ImageSurface(cairo.FORMAT_RGB24, W, rowh * len(surfs) + 60)
    c = cairo.Context(out)
    c.set_source_rgb(0.93, 0.93, 0.93)
    c.paint()
    c.set_source_rgb(0.06, 0.06, 0.06)
    c.rectangle(W / 2 + 120, 0, W, out.get_height())
    c.fill()
    for i, (label, s) in enumerate(surfs):
        y0 = 40 + i * rowh
        text(c, label, 30, y0 + 30, 34, (0.2, 0.2, 0.2), align="left", font="Inter")
        for (cx, d) in [(200, 300), (470, 98), (590, 48), (660, 32), (880, 98), (1000, 48), (1070, 32), (1180, 98)]:
            if cx == 1180:
                continue
            c.save()
            cy = y0 + 200
            c.arc(cx, cy, d / 2, 0, 2 * math.pi)
            c.clip()
            sc = d / 800
            c.translate(cx - d / 2, cy - d / 2)
            c.scale(sc, sc)
            c.set_source_surface(s, 0, 0)
            c.get_source().set_filter(cairo.FILTER_GOOD)
            c.paint()
            c.restore()
    out.write_to_png(path)


def banner_preview(surf, safe, path):
    W, H = 2560, 1440
    out = cairo.ImageSurface(cairo.FORMAT_RGB24, W // 2, H // 2 + 420)
    c = cairo.Context(out)
    c.set_source_rgb(0.12, 0.12, 0.12)
    c.paint()
    c.save()
    c.scale(0.5, 0.5)
    c.set_source_surface(surf, 0, 0)
    c.paint()
    sx, sy, sw, sh = safe
    c.set_source_rgba(0.2, 0.9, 0.3, 0.9)
    c.set_line_width(4)
    c.rectangle(sx, sy, sw, sh)
    c.stroke()
    # zona TV/desktop típica (2560x423)
    c.set_source_rgba(0.3, 0.6, 1, 0.7)
    c.set_dash([16, 10])
    c.rectangle(0, sy, W, sh)
    c.stroke()
    c.restore()
    text(c, "verde = zona segura 1546x423 (telemóvel)   azul = faixa desktop 2560x423", 20, H // 2 + 36, 22, (0.9, 0.9, 0.9), align="left", font="Inter")
    # recorte telemóvel em tamanho real-ish
    c.save()
    c.translate(20, H // 2 + 60)
    sc = 1240 / 1546
    c.scale(sc, sc)
    c.set_source_surface(surf, -sx, -sy)
    c.rectangle(0, 0, sw, sh)
    c.fill()
    c.restore()
    out.write_to_png(path)


def main():
    profs = [("A · campeão no anel", profile_a), ("B · duelo branco vs vermelho", profile_b), ("C · monograma PA", profile_c), ("D · duelo de espadas", profile_d)]
    surfs = []
    for (label, fn), tag in zip(profs, "abcd"):
        s, _ = render(lambda ctx, fn=fn: fn(ctx), 800, 800)
        s.write_to_png(os.path.join(OUT, f"perfil_{tag}.png"))
        surfs.append((label, s))
    circle_preview(surfs, os.path.join(OUT, "preview_perfis.png"))
    b, safe = render(banner, 2560, 1440)
    b.write_to_png(os.path.join(OUT, "banner.png"))
    banner_preview(b, safe, os.path.join(OUT, "preview_banner.png"))
    print("ok")


if __name__ == "__main__":
    main()
