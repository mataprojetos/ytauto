"""Stickman #001 · "WHO REACHES THE TOP?" (Anger vs Obsession vs Discipline vs Motivation).

Quatro faixas, cada boneco empurra uma pedra encosta acima até à bandeira.
Drop da música aos 17,0 s: a Anger fica vermelha e rebenta pela encosta acima.
Sem áudio (faixa silenciosa): o som é posto pelo dono na app do YouTube.

    python3 stickman/videos/001_climb.py            # render completo -> stickman/out/climb_v1.mp4
    python3 stickman/videos/001_climb.py --frames 0,10,17,25,29.5   # só PNG de controlo
"""
import argparse
import math
import os
import random
import sys

import cairo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib.core import FPS, H, W, Writer, clamp, draw_text, ensure_font, lerp, pchip, ramp, text_width, window  # noqa: E402
from lib.fx import Particles, blur_surface, rock_texture, twinkle  # noqa: E402
from lib import stick as S  # noqa: E402

S.set_scale(1.18)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "out", "climb_v1.mp4")

DURATION = 30.0
DROP = 17.0

# ---------- layout ----------
LANE_TOP = 262
LANE_BOTTOM = int(H * 0.82)          # ~18% de baixo livre (zona do YouTube)
LH = (LANE_BOTTOM - LANE_TOP) / 4
NAMES = ["ANGER", "OBSESSION", "DISCIPLINE", "MOTIVATION"]
RED = (0.80, 0.14, 0.15)
GOLD = (0.86, 0.66, 0.30)
WHITE = (0.95, 0.95, 0.95)
ANGER_RED = (1.0, 0.30, 0.26)

# ---------- terreno (coordenadas locais da faixa) ----------
G0, XP, GP = LH - 26, 860.0, 160.0
R, D = 28.0 * S.K, 82.0 * S.K
X_TOP = XP - D - 12  # anca quando a pedra chega ao cume
FLAG_X = XP + 34


def ground(x):
    up = G0 + (GP - G0) * (x + 20) / (XP + 20)
    down = GP + (x - XP) * 0.85
    k = 10.0
    m = max(up, down)
    y = m + k * math.log(math.exp((up - m) / k) + math.exp((down - m) / k))
    fade = clamp((XP - 60 - x) / 120)
    return y + fade * (2.2 * math.sin(x * 0.045) + 1.4 * math.sin(x * 0.13 + 1.0))


def boulder_center(bx):
    return S.rest_center(ground, bx, R)


def hand_target(c):
    return (c[0] - R * 0.93, c[1] - R * 0.30)


def boulder_angle(bx):
    return bx / R * 1.02


# ---------- trajetórias (x da anca ao longo do tempo) ----------
MOT_X = pchip([(0, 70), (3.5, 330), (6.5, 520), (9.0, 615), (9.8, 640), (30, 640)])
MOT_RELEASE = 9.9
DIS_X = pchip([(0, 60), (26.2, X_TOP - 18), (27.0, X_TOP), (30, X_TOP)])
OBS_X = pchip([(0, 90), (3, 290), (6.0, 480), (6.15, 470), (7.4, 300), (8.4, 300),
               (12, 470), (17, 670), (24, 712), (30, 724)])
ANG_X = pchip([(0, 75), (2, 140), (3.2, 160), (5.5, 250), (7, 265), (9.5, 340), (12.2, 385),
               (13.1, 300), (15, 312), (DROP, 312), (19, 520), (21.4, X_TOP), (22.0, X_TOP + 40),
               (22.6, XP - 8), (30, XP - 8)])
ANG_TOP = 21.4  # a pedra passa o cume


def phases(xfun, cycle):
    """Fase da passada acumulada pela distância percorrida (cycle(t) = px por ciclo)."""
    out, ph, prev = [], 0.0, xfun(0)
    for f in range(int(DURATION * FPS) + 1):
        t = f / FPS
        x = xfun(t)
        ph += 2 * math.pi * (x - prev) / cycle(t)
        prev = x
        out.append(ph)
    return out


PH = {
    "MOTIVATION": phases(MOT_X, lambda t: 64 if t < 4 else 44),
    "DISCIPLINE": phases(DIS_X, lambda t: 46),
    "OBSESSION": phases(OBS_X, lambda t: 70),
    "ANGER": phases(ANG_X, lambda t: 70 if t >= DROP else 52),
}


def speed(xfun, t):
    return (xfun(t + 0.02) - xfun(t - 0.02)) / 0.04


# ---------- estado de cada personagem ----------
# devolve dict: pose, color, glow, boulder (c, ang, alpha, glow), thoughts [(texto, alpha, estilo)]

def thought(t, t0, t1, txt, style="w"):
    a = window(t, t0, t1, 0.16)
    return (txt, a, style, t - t0) if a > 0 else None


def st_motivation(t, f):
    xh = MOT_X(t)
    ph = PH["MOTIVATION"][f]
    tired = ramp(t, 4.0, 8.0)
    if t < MOT_RELEASE:
        bx = xh + D
    else:
        bx = 640 + D - 0.5 * 260 * (t - MOT_RELEASE) ** 2
    c = boulder_center(bx)
    tgt = hand_target(boulder_center(min(xh + D, 640 + D)))
    push = S.push_pose(ground, xh, ph, tgt, lean=lerp(40, 50, tired), stride=lerp(17, 10, tired),
                       lift=lerp(10, 5, tired))
    sit = S.sit_pose(ground, xh - 4)
    sit = S.offset(sit, 0, 0)
    w = ramp(t, MOT_RELEASE, MOT_RELEASE + 0.7)
    pose = S.blend(push, sit, w)
    if w >= 1:  # respirar
        b = 1.2 * math.sin(t * 3.0)
        pose = dict(pose)
        for k in ("head", "neck", "elbL", "elbR", "handL", "handR"):
            pose[k] = (pose[k][0], pose[k][1] + b)
    th = [thought(t, 0.3, 2.6, "LET'S GO!"), thought(t, 6.6, 9.4, "I'M SO TIRED..."),
          thought(t, 10.9, 13.5, "I'LL REST A BIT.")]
    return dict(pose=pose, color=WHITE, glow=None, boulders=[(c, boulder_angle(bx), 1.0, None)],
                thoughts=th, x=xh, moving=t < MOT_RELEASE, bx=bx, rolling_back=t > MOT_RELEASE)


def st_discipline(t, f):
    xh = DIS_X(t)
    ph = PH["DISCIPLINE"][f]
    bx = xh + D
    c = boulder_center(bx)
    push = S.push_pose(ground, xh, ph, hand_target(c), lean=40, stride=13, lift=8)
    stand = S.stand_pose(ground, xh + 20, arms="rest")
    pose = S.blend(push, stand, ramp(t, 27.0, 27.9))
    th = [thought(t, 2.6, 5.0, "ONE MORE STEP."), thought(t, 11.0, 13.4, "KEEP GOING."),
          thought(t, 23.2, 25.6, "ONE MORE STEP."), thought(t, 27.4, 29.8, "WORTH IT.")]
    return dict(pose=pose, color=WHITE, glow=None, boulders=[(c, boulder_angle(bx), 1.0, None)],
                thoughts=th, x=xh, moving=t < 27.0, bx=bx)


def st_obsession(t, f):
    xh = OBS_X(t)
    ph = PH["OBSESSION"][f]
    bx = xh + D
    c = boulder_center(bx)
    late = ramp(t, 17, 22)
    push = S.push_pose(ground, xh, ph, hand_target(c), lean=lerp(46, 52, late),
                       stride=lerp(19, 10, late), lift=lerp(11, 6, late))
    wf = ramp(t, 6.0, 6.22) * (1 - ramp(t, 7.5, 8.3))
    pose = S.blend(push, S.fallen_pose(ground, xh, flail=t * 15), wf) if wf > 0 else push
    th = [thought(t, 1.2, 3.2, "FASTER."), thought(t, 6.1, 7.6, "NO, NO, NO!"),
          thought(t, 9.0, 11.6, "I CAN'T STOP."), thought(t, 24.2, 26.8, "ALMOST...")]
    return dict(pose=pose, color=WHITE, glow=None, boulders=[(c, boulder_angle(bx), 1.0, None)],
                thoughts=th, x=xh, moving=wf == 0, bx=bx, slip=wf)


def st_anger(t, f, rnd):
    xh = ANG_X(t)
    ph = PH["ANGER"][f]
    rage = t >= DROP
    if t < ANG_TOP:
        bx = xh + D
    else:
        dt = t - ANG_TOP
        bx = X_TOP + D + 260 * dt + 0.5 * 1100 * dt * dt
    c = boulder_center(bx)
    if t >= ANG_TOP and bx > XP + 40:  # cai do outro lado
        dt = t - ANG_TOP
        c = (c[0], c[1] + 0.5 * 900 * max(0, dt - 0.25) ** 2)
    tgt = hand_target(boulder_center(min(xh + D, X_TOP + D)))
    if rage:
        push = S.push_pose(ground, xh, ph, tgt, lean=54, stride=24, lift=15, crouch=0.6)
    elif 12.2 <= t < 13.1:  # a pedra rola para trás e empurra-o
        push = S.push_pose(ground, xh, ph, tgt, lean=24, stride=12, lift=6)
    else:
        push = S.push_pose(ground, xh, ph, tgt, lean=lerp(40, 46, ramp(t, 13.1, 14)), stride=16, lift=10)
    pose = S.blend(push, S.stand_pose(ground, xh, arms="up", t=t), ramp(t, 22.0, 22.7))
    # tremor antes do drop
    if 15.0 <= t < DROP:
        k = 1.4 * ramp(t, 15.0, 15.4)
        pose = S.offset(pose, rnd.uniform(-k, k), rnd.uniform(-k, k))
        c = (c[0] + rnd.uniform(-k, k) * 0.5, c[1])
    # cor: branco -> vermelho no drop -> branco-azulado no cume
    if rage:
        cool = ramp(t, 22.4, 23.8)
        color = tuple(lerp(a, b, cool) for a, b in zip(ANGER_RED, (0.97, 0.98, 1.0)))
        gcol = tuple(lerp(a, b, cool) for a, b in zip((1.0, 0.12, 0.10), (0.55, 0.78, 1.0)))
        glow = (*gcol, 1.0 + 0.25 * math.sin(t * 20) * (1 - cool))
    else:
        color, glow = WHITE, None
    bglow = (1.0, 0.25, 0.15, 0.9) if rage and t < ANG_TOP + 0.6 else None
    th = [thought(t, 4.4, 6.8, "WHY WON'T YOU MOVE?", "r"), thought(t, 13.0, 15.0, "I'M TOO SLOW!", "r"),
          thought(t, DROP + 0.12, 19.4, "NOTHING STOPS ME.", "R"),
          thought(t, 19.5, 21.8, "I'LL BREAK THROUGH.", "R")]
    return dict(pose=pose, color=color, glow=glow,
                boulders=[(c, boulder_angle(bx), 1.0, bglow)] if c[0] < W + 60 else [],
                thoughts=th, x=xh, moving=not (15.0 <= t < DROP) and t < 22.0, bx=bx, rage=rage)


# ---------- elementos estáticos ----------
def make_lane_bg(seed):
    w, h = W, int(math.ceil(LH))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surf)
    ctx.set_source_surface(rock_texture(w, h, seed, base=(15, 11, 11), var=9), 0, 0)
    ctx.paint()
    # terreno
    ctx.move_to(-5, h + 5)
    for x in range(-5, w + 6, 3):
        ctx.line_to(x, ground(x))
    ctx.line_to(w + 5, h + 5)
    ctx.close_path()
    ctx.save()
    ctx.clip()
    ctx.set_source_surface(rock_texture(w, h, seed + 99, base=(38, 27, 24), var=17), 0, 0)
    ctx.paint()
    # escurece em profundidade
    g = cairo.LinearGradient(0, GP, 0, h)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.45)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    # aresta da encosta
    for wdt, a in ((6, 0.06), (2.2, 0.45)):
        ctx.set_line_width(wdt)
        ctx.set_source_rgba(0.62, 0.52, 0.46, a)
        ctx.move_to(-5, ground(-5))
        for x in range(-5, w + 6, 3):
            ctx.line_to(x, ground(x))
        ctx.stroke()
    # vinheta
    vg = cairo.RadialGradient(w * 0.45, h * 0.55, h * 0.3, w * 0.45, h * 0.55, w * 0.75)
    vg.add_color_stop_rgba(0, 0, 0, 0, 0)
    vg.add_color_stop_rgba(1, 0, 0, 0, 0.72)
    ctx.set_source(vg)
    ctx.paint()
    tg = cairo.LinearGradient(0, 0, 0, 40)
    tg.add_color_stop_rgba(0, 0, 0, 0, 0.55)
    tg.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(tg)
    ctx.rectangle(0, 0, w, 40)
    ctx.fill()
    return surf


def make_title(parts, size=80, spacing=3.5, base=205):
    """parts: [(texto, cor, brilho?)] -> superfície com o título centrado."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, LANE_TOP)
    glow = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, LANE_TOP)
    ctx, gctx = cairo.Context(surf), cairo.Context(glow)
    sx = 0.94  # condensa ligeiramente
    total = sum(text_width(ctx, p[0], size, spacing) for p in parts) * sx
    x = (W - total) / 2 / sx
    for c in (ctx, gctx):
        c.scale(sx, 1)
    for txt, col, glw in parts:
        draw_text(ctx, txt, x + 3, base + 4, size, (0, 0, 0, 0.6), spacing)  # sombra
        if glw:
            draw_text(gctx, txt, x, base, size, (*col, 1.0), spacing)
        x += draw_text(ctx, txt, x, base, size, (*col, 1.0), spacing) + spacing
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, LANE_TOP)
    o = cairo.Context(out)
    bl = blur_surface(glow, 14)
    o.set_source_surface(bl, 0, 0)
    o.paint_with_alpha(0.9)
    o.set_source_surface(blur_surface(glow, 5), 0, 0)
    o.paint_with_alpha(0.5)
    o.set_source_surface(surf, 0, 0)
    o.paint()
    return out


def draw_flag(ctx, t, color=GOLD):
    x0, y0 = FLAG_X, ground(FLAG_X)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(0.85, 0.83, 0.80, 0.9)
    ctx.set_line_width(2.6)
    ctx.move_to(x0, y0)
    ctx.line_to(x0, y0 - 58)
    ctx.stroke()
    ctx.move_to(x0, y0 - 58)
    n = 10
    for i in range(n + 1):
        u = i / n
        ctx.line_to(x0 + 34 * u, y0 - 58 + 9 * u + 3 * math.sin(t * 6 - u * 4) * u)
    for i in range(n, -1, -1):
        u = i / n
        ctx.line_to(x0 + 34 * u, y0 - 38 - 9 * u + 3 * math.sin(t * 6 - u * 4) * u)
    ctx.close_path()
    ctx.set_source_rgba(*color, 0.95)
    ctx.fill()


def draw_thought(ctx, item, rnd):
    txt, a, style, age = item
    cx, base = 360, 82
    rise = 6 * (1 - ramp(age, 0, 0.2))
    if style == "R":  # raiva pós-drop: maior, a tremer, com brilho vermelho
        size = 42
        jit = lambda i: (rnd.uniform(-2.6, 2.6), rnd.uniform(-2.6, 2.6))
        for k, al in ((7, 0.10), (4, 0.16)):
            for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                draw_text(ctx, txt, cx + dx, base + dy, size, (1, 0.1, 0.08, al * a), 3, "center")
        draw_text(ctx, txt, cx, base, size, (1, 0.22, 0.18, a), 3, "center", jitter=jit)
        return
    size = 36
    col = (0.93, 0.20, 0.18) if style == "r" else (0.94, 0.94, 0.94)
    draw_text(ctx, txt, cx + 2, base + rise + 3, size, (0, 0, 0, 0.6 * a), 2.6, "center")
    draw_text(ctx, txt, cx, base + rise, size, (*col, a), 2.6, "center")


def draw_label(ctx, name):
    ctx.move_to(14, 25)
    ctx.line_to(22, 30)
    ctx.line_to(14, 35)
    ctx.close_path()
    ctx.set_source_rgba(*RED, 0.9)
    ctx.fill()
    draw_text(ctx, name, 32, 40, 25, (0, 0, 0, 0.7), 2.4)
    draw_text(ctx, name, 30, 38, 25, (*RED, 1.0), 2.4)


# ---------- render ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", help="só estes tempos (s) em PNG, separados por vírgula")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--dump", help="pasta para gravar cada frame de --frames em PNG")
    ap.add_argument("--sheet", default=os.path.join(ROOT, "out", "climb_v1_frames.png"))
    args = ap.parse_args()
    ensure_font()

    only = None
    if args.frames:
        only = {int(round(float(s) * FPS)) for s in args.frames.split(",")}
    sheet_t = [0, 10, 17, 25, 29.5]
    sheet_f = {int(round(s * FPS)): s for s in sheet_t}
    sheet_imgs = {}

    bgs = [make_lane_bg(11 + 7 * i) for i in range(4)]
    title1 = make_title([("WHO REACHES THE ", (0.80, 0.80, 0.80), False), ("TOP?", GOLD, True)])
    title2 = make_title([("WHICH ONE ARE ", (0.80, 0.80, 0.80), False), ("YOU?", GOLD, True)])

    rnd = random.Random(7)
    parts = [Particles(100 + i) for i in range(4)]
    sparkles = [dict(x=random.Random(i).uniform(380, 1080), y=random.Random(i * 3 + 1).uniform(20, LH - 20),
                     s=random.Random(i * 7 + 2).uniform(4, 10), ph=random.Random(i * 5).uniform(0, 6.28),
                     v=random.Random(i * 11).uniform(8, 25)) for i in range(46)]

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    writer = None if only else Writer(args.out)
    nframes = int(DURATION * FPS)
    dt = 1 / FPS

    for f in range(nframes):
        t = f / FPS
        states = [st_anger(t, f, rnd), st_obsession(t, f), st_discipline(t, f), st_motivation(t, f)]

        # --- partículas (avançam sempre, para o estado ser igual com ou sem --frames)
        for i, s in enumerate(states):
            P = parts[i]
            name = NAMES[i]
            xf = {"ANGER": ANG_X, "OBSESSION": OBS_X, "DISCIPLINE": DIS_X, "MOTIVATION": MOT_X}[name]
            v = abs(speed(xf, t))
            if s["moving"] and v > 4 and rnd.random() < min(0.9, v / 90):
                fx = s["pose"]["footL"] if math.sin(PH[name][f]) < 0 else s["pose"]["footR"]
                P.emit(fx[0], fx[1] - 2, 1, vx=(-50, -10), vy=(-50, -10), size=(1.2, 2.6))
            if s["moving"] and v > 4 and rnd.random() < min(0.5, v / 160):
                bc = s["boulders"][0][0] if s["boulders"] else None
                if bc:
                    P.emit(bc[0] - 6, bc[1] + R - 3, 1, vx=(-70, -20), vy=(-60, -10), size=(1.5, 2.6),
                           color=(0.55, 0.48, 0.44), kind="rock")
            if name == "OBSESSION" and abs(t - 6.05) < dt / 2:
                P.emit(s["x"], ground(s["x"]) - 4, 22, vx=(-90, 30), vy=(-120, -20), size=(1.5, 3.2))
            if name == "MOTIVATION" and s.get("rolling_back") and s["bx"] > -40 and rnd.random() < 0.7:
                bc = s["boulders"][0][0]
                P.emit(bc[0] + 8, bc[1] + R - 2, 1, vx=(0, 50), vy=(-60, -10), size=(1.2, 2.4))
            if name == "ANGER":
                if abs(t - DROP) < dt / 2:
                    bc = s["boulders"][0][0]
                    P.emit(bc[0] - R, bc[1], 45, vx=(-260, 200), vy=(-320, -40), life=(0.3, 0.8),
                           size=(1.6, 3.0), color=(1, 0.45, 0.25), g=500, kind="spark")
                    P.emit(bc[0], bc[1] + R - 4, 14, vx=(-160, 60), vy=(-200, -60), size=(2, 4),
                           color=(0.6, 0.5, 0.45), kind="rock")
                if s["rage"] and t < ANG_TOP and s["boulders"]:
                    bc = s["boulders"][0][0]
                    P.emit(bc[0] - R * 0.8, bc[1] - 4, 3, vx=(-220, 80), vy=(-220, -30), life=(0.2, 0.55),
                           size=(1.4, 2.6), color=(1, 0.38, 0.22), g=500, kind="spark")
                    if rnd.random() < 0.6:
                        P.emit(bc[0] - 4, bc[1] + R - 4, 1, vx=(-200, -60), vy=(-160, -40), size=(2, 3.8),
                               color=(0.6, 0.5, 0.45), kind="rock")
                    fx = s["pose"]["footL"]
                    P.emit(fx[0], fx[1] - 2, 2, vx=(-120, -30), vy=(-80, -20), size=(1.5, 3.0))
                if abs(t - (ANG_TOP + 0.3)) < dt / 2:
                    P.emit(XP + 20, GP - 6, 18, vx=(-40, 220), vy=(-200, -40), size=(2, 4),
                           color=(0.6, 0.5, 0.45), kind="rock")
            P.step(dt, ground)

        if only is not None and f not in only:
            continue

        # --- fundo e título
        ctx.set_source_rgb(0.025, 0.022, 0.024)
        ctx.paint()
        sw = ramp(t, 27.9, 28.12)
        if sw < 1:
            ctx.set_source_surface(title1, 0, 0)
            ctx.paint_with_alpha(1 - sw)
        if sw > 0:
            pop = 1 + 0.06 * (1 - ramp(t, 28.0, 28.35))
            ctx.save()
            ctx.translate(W / 2, 180)
            ctx.scale(pop, pop)
            ctx.translate(-W / 2, -180)
            ctx.set_source_surface(title2, 0, 0)
            ctx.paint_with_alpha(sw)
            ctx.restore()
        # marca provisória, muito discreta
        draw_text(ctx, "@channel", 30, 248, 17, (0.85, 0.85, 0.85, 0.16), 1.5)

        # --- faixas
        for i, s in enumerate(states):
            top = LANE_TOP + i * LH
            ctx.save()
            ctx.translate(0, top)
            ctx.rectangle(0, 0, W, LH)
            ctx.clip()
            ctx.save()
            if NAMES[i] == "ANGER" and DROP <= t < ANG_TOP + 0.5:
                k = 7 * (1 - 0.4 * ramp(t, DROP, ANG_TOP))
                ctx.translate(rnd.uniform(-k, k), rnd.uniform(-k * 0.7, k * 0.7))
            ctx.set_source_surface(bgs[i], 0, 0)
            ctx.paint()

            if NAMES[i] == "ANGER" and s["rage"]:
                # aura vermelha a seguir o boneco
                hx, hy = s["pose"]["hip"]
                a = 0.32 * (1 - ramp(t, 22.4, 23.6))
                rg = cairo.RadialGradient(hx, hy, 10, hx, hy, 230)
                rg.add_color_stop_rgba(0, 0.9, 0.08, 0.05, a)
                rg.add_color_stop_rgba(1, 0.9, 0.08, 0.05, 0)
                ctx.set_source(rg)
                ctx.paint()

            draw_flag(ctx, t)
            for c, ang, al, bg in s["boulders"]:
                S.draw_boulder(ctx, c, R, ang, alpha=al, glow=bg)
            parts[i].draw(ctx)
            S.draw_figure(ctx, s["pose"], color=s["color"], glow=s["glow"])

            if NAMES[i] == "ANGER":
                # luz branca-azulada no cume
                L = ramp(t, 22.2, 24.0)
                if L > 0:
                    cx, cy = s["pose"]["neck"]
                    rad = cairo.RadialGradient(cx, cy, 0, cx, cy, 120 + 650 * L)
                    rad.add_color_stop_rgba(0, 0.92, 0.97, 1.0, 0.85 * L)
                    rad.add_color_stop_rgba(0.12, 0.70, 0.85, 1.0, 0.45 * L)
                    rad.add_color_stop_rgba(0.5, 0.35, 0.55, 0.95, 0.16 * L)
                    rad.add_color_stop_rgba(1, 0.2, 0.3, 0.7, 0)
                    ctx.set_source(rad)
                    ctx.paint()
                    for sp in sparkles:
                        x = sp["x"] + 10 * math.sin(t * 0.8 + sp["ph"])
                        y = (sp["y"] - sp["v"] * (t - 22.2)) % LH
                        tw = 0.5 + 0.5 * math.sin(t * 4 + sp["ph"] * 3)
                        dist = math.hypot(x - cx, y - cy)
                        vis = clamp((120 + 650 * L - dist) / 150)
                        if vis > 0:
                            twinkle(ctx, x, y, sp["s"] * (0.6 + 0.5 * tw),
                                    (0.75, 0.88, 1.0, (0.35 + 0.65 * tw) * vis))
                    S.draw_figure(ctx, s["pose"], color=(1, 1, 1), glow=(0.6, 0.82, 1.0, 1.4))
                # flash do drop
                if t >= DROP:
                    fl = math.exp(-(t - DROP) / 0.12) * 0.75
                    if fl > 0.01:
                        ctx.set_source_rgba(1, 0.85, 0.85, fl)
                        ctx.paint()
            ctx.restore()

            # escurecer: tensão antes do drop e personagens que ficaram para trás
            dim = 0.0
            if NAMES[i] != "ANGER" and 15.0 <= t < DROP:
                dim = 0.5 * ramp(t, 15.0, 15.6)
            if NAMES[i] in ("MOTIVATION", "OBSESSION"):
                dim = max(dim, 0.4 * ramp(t, 22.3, 23.3))
            if dim > 0:
                ctx.set_source_rgba(0, 0, 0, dim)
                ctx.paint()

            for th in s["thoughts"]:
                if th:
                    draw_thought(ctx, th, rnd)
            draw_label(ctx, NAMES[i])
            ctx.restore()

        # separadores vermelho-escuros
        for i in range(5):
            y = LANE_TOP + i * LH
            hot = 1 if (i in (0, 1) and DROP <= t < 22.0) else 0
            ctx.set_source_rgba(0.42 + 0.4 * hot, 0.07, 0.07, 0.95)
            ctx.set_line_width(2)
            ctx.move_to(0, y)
            ctx.line_to(W, y)
            ctx.stroke()

        if writer:
            writer.write(surf)
        if args.dump:
            os.makedirs(args.dump, exist_ok=True)
            surf.write_to_png(os.path.join(args.dump, f"t{t:05.2f}.png"))
        if f in sheet_f:
            p = os.path.join(os.path.dirname(args.sheet), f"_f{f:03d}.png")
            surf.write_to_png(p)
            sheet_imgs[sheet_f[f]] = p
        if f % 90 == 0:
            print(f"{t:5.1f}s", flush=True)

    if writer:
        writer.close()
    if sheet_imgs:
        make_sheet(sheet_imgs, args.sheet)


def make_sheet(imgs, path):
    from PIL import Image, ImageDraw, ImageFont
    keys = sorted(imgs)
    tw, th = 360, 640
    sheet = Image.new("RGB", (tw * len(keys) + 10 * (len(keys) + 1), th + 60), (20, 20, 20))
    font = ImageFont.truetype(os.path.expanduser("~/.fonts/Oswald-Bold.ttf"), 30)
    d = ImageDraw.Draw(sheet)
    for j, k in enumerate(keys):
        im = Image.open(imgs[k]).convert("RGB").resize((tw, th), Image.LANCZOS)
        x = 10 + j * (tw + 10)
        sheet.paste(im, (x, 50))
        d.text((x + 4, 8), f"{k:g} s", fill=(230, 230, 230), font=font)
        os.remove(imgs[k])
    sheet.save(path)
    print("folha:", path)


if __name__ == "__main__":
    main()
