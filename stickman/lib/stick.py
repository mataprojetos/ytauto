"""Boneco stickman (cinemática simples), poses e pedra redonda sobre um terreno y = ground(x)."""
import math

import cairo

# proporções (px); K escala o boneco inteiro
K = 1.0
HEAD_R = 12
TORSO = 40
THIGH = 26
SHIN = 26
UPPER = 21
FORE = 21


def set_scale(k):
    """Muda o tamanho do boneco (chamar antes de gerar poses)."""
    global K, HEAD_R, TORSO, THIGH, SHIN, UPPER, FORE
    K = k
    HEAD_R, TORSO, THIGH, SHIN, UPPER, FORE = 12 * k, 40 * k, 26 * k, 26 * k, 21 * k, 21 * k


def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def v_mul(a, k):
    return (a[0] * k, a[1] * k)


def v_len(a):
    return math.hypot(a[0], a[1])


def dirv(deg):
    """Direção a partir da vertical (0 = para cima, +90 = para a direita), y para baixo."""
    r = math.radians(deg)
    return (math.sin(r), -math.cos(r))


def ik2(a, target, l1, l2, bend=1):
    """Articulação do meio de uma cadeia de 2 ossos (joelho/cotovelo). bend=±1 escolhe o lado."""
    d = v_sub(target, a)
    dist = v_len(d)
    dist = max(1e-3, min(dist, l1 + l2 - 1e-3))
    ux, uy = d[0] / max(1e-6, v_len(d)), d[1] / max(1e-6, v_len(d))
    x = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    hgt = math.sqrt(max(0.0, l1 * l1 - x * x))
    # perpendicular
    px, py = -uy * bend, ux * bend
    end = (a[0] + ux * min(v_len(d), l1 + l2), a[1] + uy * min(v_len(d), l1 + l2))
    joint = (a[0] + ux * x + px * hgt, a[1] + uy * x + py * hgt)
    return joint, end


def slope_at(ground, x, dx=3.0):
    return math.atan2(ground(x - dx) - ground(x + dx), 2 * dx)  # >0 a subir para a direita


def rest_center(ground, x, r):
    """Centro de um círculo de raio r pousado no terreno na abcissa x (exato com amostragem)."""
    best = 1e9
    n = 24
    for i in range(n + 1):
        xi = x - r + 2 * r * i / n
        dy = math.sqrt(max(0.0, r * r - (xi - x) ** 2))
        best = min(best, ground(xi) - dy)
    return (x, best)


# ---------- poses: dicionários de pontos ----------
KEYS = ["head", "neck", "hip", "kneeL", "footL", "kneeR", "footR", "elbL", "handL", "elbR", "handR"]


def blend(p, q, a):
    if a <= 0:
        return p
    if a >= 1:
        return q
    return {k: (p[k][0] + (q[k][0] - p[k][0]) * a, p[k][1] + (q[k][1] - p[k][1]) * a) for k in KEYS}


def offset(p, dx, dy):
    return {k: (v[0] + dx, v[1] + dy) for k, v in p.items()}


def _legs(ground, hip, xh, phase, stride, lift, back=-12):
    out = {}
    for name, ph in (("L", phase), ("R", phase + math.pi)):
        fx = xh + K * (back + stride * math.sin(ph))
        fy = ground(fx) - K * lift * max(0.0, math.cos(ph))
        knee, foot = ik2(hip, (fx, fy), THIGH, SHIN, bend=-1)  # joelho para a frente (+x)
        out["knee" + name], out["foot" + name] = knee, foot
    return out


def push_pose(ground, xh, phase, target, lean=40, stride=15, lift=9, crouch=0.0):
    """A empurrar algo em `target` (ponto de contacto das mãos)."""
    bob = 2.0 * abs(math.sin(phase))
    hip = (xh, ground(xh) - K * (45 - crouch * 8 - bob))
    neck = v_add(hip, v_mul(dirv(lean), TORSO))
    head = v_add(neck, v_mul(dirv(lean - 18), HEAD_R + 4 * K))
    p = {"hip": hip, "neck": neck, "head": head}
    p.update(_legs(ground, hip, xh, phase, stride, lift))
    for name, dy in (("L", -5 * K), ("R", 4 * K)):
        elb, hand = ik2(neck, (target[0], target[1] + dy), UPPER, FORE, bend=1)
        p["elb" + name], p["hand" + name] = elb, hand
    return p


def sit_pose(ground, xh):
    """Sentado, cansado, cabeça em baixo e braços nos joelhos."""
    gy = ground(xh)
    hip = (xh, gy - 7 * K)
    neck = v_add(hip, v_mul(dirv(28), TORSO))
    head = v_add(neck, v_mul(dirv(70), HEAD_R + 3 * K))
    fL = (xh + 44 * K, ground(xh + 44 * K) - 2)
    fR = (xh + 38 * K, ground(xh + 38 * K) - 2)
    kL, fL = ik2(hip, fL, THIGH, SHIN, bend=-1)
    kR, fR = ik2(hip, fR, THIGH, SHIN, bend=-1)
    p = {"hip": hip, "neck": neck, "head": head, "kneeL": kL, "footL": fL, "kneeR": kR, "footR": fR}
    for name, k in (("L", kL), ("R", kR)):
        elb, hand = ik2(neck, (k[0] + 2 * K, k[1] + 4 * K), UPPER, FORE, bend=-1)
        p["elb" + name], p["hand" + name] = elb, hand
    return p


def fallen_pose(ground, xh, flail=0.0):
    """Caído de costas, cabeça para baixo da encosta, pernas e braços no ar."""
    th = slope_at(ground, xh)
    u = (math.cos(th), -math.sin(th))
    n = (-math.sin(th), -math.cos(th))
    hip = v_add((xh, ground(xh)), v_mul(n, 7 * K))
    neck = v_add(v_add(hip, v_mul(u, -TORSO)), v_mul(n, K * (6)))
    head = v_add(v_add(neck, v_mul(u, -(HEAD_R + 3 * K))), v_mul(n, K * (4)))
    w = math.sin(flail)
    kL = v_add(v_add(hip, v_mul(u, K * (14))), v_mul(n, K * (22 + 4 * w)))
    fL = v_add(v_add(hip, v_mul(u, K * (38))), v_mul(n, K * (26 - 6 * w)))
    kR = v_add(v_add(hip, v_mul(u, K * (20))), v_mul(n, K * (14 - 3 * w)))
    fR = v_add(v_add(hip, v_mul(u, K * (44))), v_mul(n, K * (8 + 5 * w)))
    eL = v_add(v_add(neck, v_mul(u, K * (6))), v_mul(n, K * (20 + 5 * w)))
    hL = v_add(v_add(neck, v_mul(u, K * (-8))), v_mul(n, K * (38 + 6 * w)))
    eR = v_add(v_add(neck, v_mul(u, K * (14))), v_mul(n, K * (16 - 4 * w)))
    hR = v_add(v_add(neck, v_mul(u, K * (22))), v_mul(n, K * (33 - 5 * w)))
    return {"hip": hip, "neck": neck, "head": head, "kneeL": kL, "footL": fL, "kneeR": kR,
            "footR": fR, "elbL": eL, "handL": hL, "elbR": eR, "handR": hR}


def stand_pose(ground, xh, arms="down", t=0.0):
    """De pé. arms: 'down', 'up' (vitória) ou 'rest' (uma mão na pedra à frente)."""
    gy = min(ground(xh - 9 * K), ground(xh + 9 * K))
    hip = (xh, gy - 50 * K)
    neck = (xh + K, hip[1] - TORSO)
    head = (xh + 2 * K, neck[1] - HEAD_R - 4 * K)
    kL, fL = ik2(hip, (xh - 9 * K, ground(xh - 9 * K)), THIGH, SHIN, bend=-1)
    kR, fR = ik2(hip, (xh + 9 * K, ground(xh + 9 * K)), THIGH, SHIN, bend=-1)
    p = {"hip": hip, "neck": neck, "head": head, "kneeL": kL, "footL": fL, "kneeR": kR, "footR": fR}
    if arms == "up":
        s = 3 * math.sin(t * 5)
        p["elbL"], p["handL"] = (xh - 14 * K, neck[1] - 16 * K), (xh - 22 * K, neck[1] - 36 * K + s)
        p["elbR"], p["handR"] = (xh + 16 * K, neck[1] - 16 * K), (xh + 24 * K, neck[1] - 36 * K - s)
    elif arms == "rest":
        p["elbL"], p["handL"] = (xh - 6 * K, neck[1] + 20 * K), (xh - 4 * K, neck[1] + 41 * K)
        p["elbR"], p["handR"] = (xh + 16 * K, neck[1] + 14 * K), (xh + 32 * K, neck[1] + 24 * K)
    else:
        p["elbL"], p["handL"] = (xh - 6 * K, neck[1] + 20 * K), (xh - 8 * K, neck[1] + 41 * K)
        p["elbR"], p["handR"] = (xh + 7 * K, neck[1] + 20 * K), (xh + 9 * K, neck[1] + 41 * K)
    return p


# ---------- desenho ----------
def _path(ctx, p):
    ctx.move_to(*p["neck"])
    ctx.line_to(*p["hip"])
    for s in ("L", "R"):
        ctx.move_to(*p["hip"])
        ctx.line_to(*p["knee" + s])
        ctx.line_to(*p["foot" + s])
        ctx.move_to(*p["neck"])
        ctx.line_to(*p["elb" + s])
        ctx.line_to(*p["hand" + s])


def draw_figure(ctx, p, color=(0.96, 0.96, 0.96), width=None, glow=None, alpha=1.0):
    """glow = (r, g, b, força) desenha halos largos por baixo do traço."""
    width = width or 3.4 * K
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if glow:
        gr, gg, gb, k = glow
        for wdt, a in ((26, 0.05), (16, 0.09), (9, 0.18)):
            ctx.set_source_rgba(gr, gg, gb, a * k * alpha)
            ctx.set_line_width(wdt)
            _path(ctx, p)
            ctx.stroke()
            ctx.arc(p["head"][0], p["head"][1], HEAD_R + wdt / 2, 0, 2 * math.pi)
            ctx.fill()
    ctx.set_source_rgba(*color, alpha)
    ctx.set_line_width(width)
    _path(ctx, p)
    ctx.stroke()
    ctx.arc(p["head"][0], p["head"][1], HEAD_R, 0, 2 * math.pi)
    ctx.fill()


def draw_boulder(ctx, c, r, angle, tint=(0.36, 0.33, 0.32), alpha=1.0, glow=None):
    x, y = c
    if glow:
        gr, gg, gb, k = glow
        rad = cairo.RadialGradient(x, y, r * 0.6, x, y, r * 2.2)
        rad.add_color_stop_rgba(0, gr, gg, gb, 0.35 * k * alpha)
        rad.add_color_stop_rgba(1, gr, gg, gb, 0)
        ctx.set_source(rad)
        ctx.arc(x, y, r * 2.2, 0, 2 * math.pi)
        ctx.fill()
    g = cairo.RadialGradient(x - r * 0.35, y - r * 0.4, r * 0.1, x, y, r * 1.05)
    tr, tg, tb = tint
    g.add_color_stop_rgba(0, tr * 1.7, tg * 1.7, tb * 1.7, alpha)
    g.add_color_stop_rgba(1, tr * 0.55, tg * 0.55, tb * 0.55, alpha)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()
    # fissuras a rodar
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(angle)
    ctx.set_source_rgba(0.08, 0.07, 0.07, 0.75 * alpha)
    ctx.set_line_width(2)
    ctx.move_to(-r * 0.55, -r * 0.2)
    ctx.line_to(-r * 0.1, -r * 0.05)
    ctx.line_to(r * 0.15, -r * 0.45)
    ctx.move_to(-r * 0.1, -r * 0.05)
    ctx.line_to(r * 0.05, r * 0.5)
    ctx.move_to(r * 0.35, r * 0.1)
    ctx.line_to(r * 0.7, r * 0.25)
    ctx.stroke()
    ctx.restore()
    ctx.set_source_rgba(0.82, 0.80, 0.78, 0.55 * alpha)
    ctx.set_line_width(1.6)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.stroke()
