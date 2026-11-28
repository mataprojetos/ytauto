"""Stickman #001 · "WHO REACHES THE TOP?" (Anger vs Obsession vs Discipline vs Motivation).

v3 (pedido do dono): fundo preto, a encosta é uma linha de ponta a ponta e anda por baixo deles
(escada rolante); a meta só aparece nos últimos ~2 s, quando a Anger lá chega (o único).
Bonecos néon, cada um com a sua cor. Pensamentos nascem da cabeça e caem para trás.
Pulsação suave ao ritmo da música (--music deteta BPM/batidas/drop; sem música usa --bpm).
Drop da música aos 17,0 s. Sem música no ficheiro (faixa silenciosa).

    python3 stickman/videos/001_climb.py                     # -> stickman/out/climb_v3.mp4 + folha de frames
    python3 stickman/videos/001_climb.py --frames 0,17 --dump /tmp/f   # só PNG
"""
import argparse
import math
import os
import random
import sys

import cairo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib.core import FPS, H, W, Writer, clamp, draw_text, ensure_font, lerp, pchip, ramp, text_width  # noqa: E402
from lib.fx import Particles, add_glow, blur_surface, twinkle  # noqa: E402
from lib import stick as S  # noqa: E402
from lib.beats import BeatSync  # noqa: E402

S.set_scale(1.18)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "out", "climb_v3.mp4")

DURATION = 30.0
DROP = 17.0
NF = int(DURATION * FPS)

# ---------- layout ----------
LANE_TOP = 262
LANE_BOTTOM = int(H * 0.82)          # ~18% de baixo livre (zona do YouTube)
LH = (LANE_BOTTOM - LANE_TOP) / 4
NAMES = ["ANGER", "OBSESSION", "DISCIPLINE", "MOTIVATION"]
RED = (0.80, 0.14, 0.15)
GOLD = (0.86, 0.66, 0.30)
COL = {"ANGER": (1.0, 0.16, 0.13), "OBSESSION": (0.74, 0.34, 1.0),
       "DISCIPLINE": (0.12, 0.80, 1.0), "MOTIVATION": (1.0, 0.64, 0.10)}
HIP_SCREEN_X = 470                   # onde a câmara mantém a anca
GROUND_SCREEN = 0.70                 # altura do chão (fração da faixa) debaixo do boneco

R, D = 28.0 * S.K, 82.0 * S.K
SLOPE = 0.16


def make_ground(summit, seed):
    """Encosta infinita a subir para a direita (y para baixo); com `summit` há um cume e descida."""
    ph1, ph2 = seed * 1.7, seed * 0.9

    def up(x):
        fade = 1.0 if summit is None else clamp((summit - 40 - x) / 120)
        return -SLOPE * x + fade * (7 * math.sin(x * 0.019 + ph1) + 3 * math.sin(x * 0.061 + ph2))

    if summit is None:
        return up
    top = up(summit)

    def g(x):
        a, b = up(x), top + (x - summit) * 0.9
        k = 10.0
        m = max(a, b)
        return m + k * math.log(math.exp((a - m) / k) + math.exp((b - m) / k))

    return g


# ---------- trajetórias (x da anca no mundo da faixa) ----------
MOT_SIT = 640
MOT_X = pchip([(0, 70), (3.5, 330), (6.5, 520), (9.0, 615), (9.8, MOT_SIT), (30, MOT_SIT)])
MOT_RELEASE = 9.9
DIS_X = pchip([(0, 60), (30, 60 + 30 * 31)])
OBS_X = pchip([(0, 90), (3, 300), (6.0, 500), (6.15, 490), (7.4, 300), (8.4, 300),
               (12, 480), (17, 760), (24, 900), (30, 960)])
ANG_SUMMIT = 2800.0  # só entra no ecrã nos últimos ~2 s
ANG_TOP_X = ANG_SUMMIT - D - 12
ANG_X = pchip([(0, 75), (2, 140), (3.2, 160), (5.5, 250), (7, 265), (9.5, 340), (12.2, 385),
               (13.1, 300), (15, 312), (DROP, 312), (18, 430), (27.4, ANG_TOP_X), (28.0, ANG_TOP_X + 40),
               (28.5, ANG_SUMMIT - 8), (30, ANG_SUMMIT - 8)])
ANG_TOP = 27.4   # a pedra passa o cume: o vencedor chega ~2 s antes do fim
WIN = 28.0

LANES = {
    "ANGER": dict(x=ANG_X, summit=ANG_SUMMIT, seed=3, cycle=lambda t: 74 if t >= DROP else 52),
    "OBSESSION": dict(x=OBS_X, summit=None, seed=5, cycle=lambda t: 70),
    "DISCIPLINE": dict(x=DIS_X, summit=None, seed=7, cycle=lambda t: 50),
    "MOTIVATION": dict(x=MOT_X, summit=None, seed=9, cycle=lambda t: 64 if t < 4 else 44),
}
for nm, L in LANES.items():
    L["g"] = make_ground(L["summit"], L["seed"])


def precompute():
    for nm, L in LANES.items():
        xf, g = L["x"], L["g"]
        ph, prev = 0.0, xf(0)
        L["ph"], L["cam"] = [], []
        follow = xf(0)
        lim = (L["summit"] - 230) if nm == "ANGER" else 1e9
        for f in range(NF + 1):
            t = f / FPS
            x = xf(t)
            ph += 2 * math.pi * (x - prev) / L["cycle"](t)
            prev = x
            L["ph"].append(ph)
            follow += (min(x, lim) - follow) * (0.10 if nm != "ANGER" or t < DROP else 0.16)
            cx = follow - HIP_SCREEN_X
            cy = g(follow + 40) - GROUND_SCREEN * LH
            L["cam"].append((cx, cy))


def speed(xfun, t):
    return (xfun(t + 0.02) - xfun(t - 0.02)) / 0.04


def hand_target(c):
    return (c[0] - R * 0.93, c[1] - R * 0.30)


# pensamentos: (início, texto, estilo) — nascem da cabeça, ficam por cima e caem para trás
THOUGHTS = {
    "ANGER": [(4.2, "WHY WON'T YOU MOVE?", "r"), (13.0, "I'M TOO SLOW!", "r"),
              (DROP + 0.1, "NOTHING STOPS ME.", "R"), (20.6, "I'LL BREAK THROUGH.", "R"), (24.1, "I'M NOT DONE.", "R")],
    "OBSESSION": [(1.2, "FASTER."), (6.05, "NO, NO, NO!"), (9.0, "I CAN'T STOP."), (21.5, "NOT ENOUGH.")],
    "DISCIPLINE": [(2.4, "ONE MORE STEP."), (11.0, "KEEP GOING."), (19.4, "ONE MORE STEP."), (24.8, "STAY STEADY.")],
    "MOTIVATION": [(0.3, "LET'S GO!"), (6.4, "I'M SO TIRED..."), (10.8, "I'LL REST A BIT.")],
}
T_GROW, T_FALL, T_REST = 0.35, 0.55, 1.4


def t_hold(txt):
    return 1.45 + 0.03 * len(txt)


def heave(ph):
    """Balanço do tronco a cada passada (mais movimento)."""
    return 6 * math.sin(2 * ph)


# ---------- estado de cada personagem ----------
def st_motivation(t, f):
    L = LANES["MOTIVATION"]
    g = L["g"]
    xh, ph = MOT_X(t), L["ph"][f]
    tired = ramp(t, 4.0, 8.0)
    bx = xh + D if t < MOT_RELEASE else MOT_SIT + D - 0.5 * 260 * (t - MOT_RELEASE) ** 2
    c = S.rest_center(g, bx, R)
    tgt = hand_target(S.rest_center(g, min(xh + D, MOT_SIT + D), R))
    push = S.push_pose(g, xh, ph, tgt, lean=lerp(40, 50, tired) + heave(ph) * (1 - tired * 0.5),
                       stride=lerp(18, 10, tired), lift=lerp(11, 5, tired))
    pose = S.blend(push, S.sit_pose(g, xh - 4), ramp(t, MOT_RELEASE, MOT_RELEASE + 0.7))
    if t > MOT_RELEASE + 0.7:  # respirar
        b = 1.4 * math.sin(t * 3.0)
        pose = dict(pose)
        for k in ("head", "neck", "elbL", "elbR", "handL", "handR"):
            pose[k] = (pose[k][0], pose[k][1] + b)
    return dict(pose=pose, glow=0.8, boulders=[(c, bx / R * 1.02, None)], x=xh,
                moving=t < MOT_RELEASE, bx=bx, rolling_back=t > MOT_RELEASE, embers=1.0 - 0.7 * tired)


def st_discipline(t, f):
    L = LANES["DISCIPLINE"]
    g = L["g"]
    xh, ph = DIS_X(t), L["ph"][f]
    bx = xh + D
    c = S.rest_center(g, bx, R)
    pose = S.push_pose(g, xh, ph, hand_target(c), lean=41 + heave(ph) * 0.6, stride=14, lift=9)
    return dict(pose=pose, glow=0.8, boulders=[(c, bx / R * 1.02, None)], x=xh,
                moving=True, bx=bx, embers=0.8)


def st_obsession(t, f):
    L = LANES["OBSESSION"]
    g = L["g"]
    xh, ph = OBS_X(t), L["ph"][f]
    bx = xh + D
    c = S.rest_center(g, bx, R)
    late = ramp(t, 17, 24)
    push = S.push_pose(g, xh, ph, hand_target(c), lean=lerp(46, 52, late) + heave(ph) * 1.2,
                       stride=lerp(20, 12, late), lift=lerp(12, 7, late))
    wf = ramp(t, 6.0, 6.22) * (1 - ramp(t, 7.5, 8.3))
    pose = S.blend(push, S.fallen_pose(g, xh, flail=t * 15), wf) if wf > 0 else push
    return dict(pose=pose, glow=0.85, boulders=[(c, bx / R * 1.02, None)], x=xh,
                moving=wf == 0, bx=bx, embers=1.3)


def st_anger(t, f, rnd):
    L = LANES["ANGER"]
    g = L["g"]
    xh, ph = ANG_X(t), L["ph"][f]
    rage = t >= DROP
    if t < ANG_TOP:
        bx = xh + D
    else:
        dt = t - ANG_TOP
        bx = ANG_TOP_X + D + 260 * dt + 0.5 * 1100 * dt * dt
    c = S.rest_center(g, bx, R)
    if t >= ANG_TOP and bx > ANG_SUMMIT + 40:  # cai do outro lado
        c = (c[0], c[1] + 0.5 * 900 * max(0, t - ANG_TOP - 0.25) ** 2)
    tgt = hand_target(S.rest_center(g, min(xh + D, ANG_TOP_X + D), R))
    if rage:
        push = S.push_pose(g, xh, ph, tgt, lean=54 + heave(ph) * 1.5, stride=25, lift=16, crouch=0.6)
    elif 12.2 <= t < 13.1:  # a pedra rola para trás e empurra-o
        push = S.push_pose(g, xh, ph, tgt, lean=24, stride=12, lift=6)
    else:
        shove = 5 * max(0, math.sin(t * 7)) if 13.1 <= t < 15 else 0  # empurrões irritados
        push = S.push_pose(g, xh, ph, tgt, lean=lerp(40, 46, ramp(t, 13.1, 14)) + heave(ph) + shove,
                           stride=16, lift=10)
    pose = S.blend(push, S.stand_pose(g, xh, arms="up", t=t), ramp(t, WIN, WIN + 0.6))
    if 15.0 <= t < DROP:  # tremor antes do drop
        k = 1.5 * ramp(t, 15.0, 15.4)
        pose = S.offset(pose, rnd.uniform(-k, k), rnd.uniform(-k, k))
        c = (c[0] + rnd.uniform(-k, k) * 0.5, c[1])
    cool = ramp(t, WIN + 0.3, WIN + 1.4)
    if rage:
        color = tuple(lerp(a, b, cool) for a, b in zip((1.0, 0.22, 0.18), (0.92, 0.96, 1.0)))
        gcol = tuple(lerp(a, b, cool) for a, b in zip((1.0, 0.10, 0.06), (0.45, 0.72, 1.0)))
        glow = 1.0 + 0.3 * math.sin(t * 22) * (1 - cool)
    else:
        color, gcol, glow = COL["ANGER"], COL["ANGER"], 0.75
    bglow = (1.0, 0.25, 0.15, 0.9) if rage and t < ANG_TOP + 0.6 else None
    return dict(pose=pose, color=color, gcol=gcol, glow=glow,
                boulders=[(c, bx / R * 1.02, bglow)] if c[0] < ANG_SUMMIT + 500 else [],
                x=xh, moving=not (15.0 <= t < DROP) and t < WIN, bx=bx, rage=rage,
                embers=(4.0 if rage and t < WIN + 0.3 else 1.2))


# ---------- elementos estáticos ----------
def make_title(parts, size=80, spacing=3.5, base=205):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, LANE_TOP)
    glow = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, LANE_TOP)
    ctx, gctx = cairo.Context(surf), cairo.Context(glow)
    sx = 0.94
    total = sum(text_width(ctx, p[0], size, spacing) for p in parts) * sx
    x = (W - total) / 2 / sx
    for c in (ctx, gctx):
        c.scale(sx, 1)
    for txt, col, glw in parts:
        draw_text(ctx, txt, x + 3, base + 4, size, (0, 0, 0, 0.6), spacing)
        if glw:
            draw_text(gctx, txt, x, base, size, (*col, 1.0), spacing)
        x += draw_text(ctx, txt, x, base, size, (*col, 1.0), spacing) + spacing
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, LANE_TOP)
    o = cairo.Context(out)
    o.set_source_surface(blur_surface(glow, 14), 0, 0)
    o.paint_with_alpha(0.9)
    o.set_source_surface(blur_surface(glow, 5), 0, 0)
    o.paint_with_alpha(0.5)
    o.set_source_surface(surf, 0, 0)
    o.paint()
    return out


def draw_flag(ctx, gctx, g, x0, t):
    y0 = g(x0)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(0.85, 0.83, 0.80, 0.9)
    ctx.set_line_width(2.8)
    ctx.move_to(x0, y0)
    ctx.line_to(x0, y0 - 62)
    ctx.stroke()
    for c, a in ((ctx, 0.95), (gctx, 0.7)):
        c.move_to(x0, y0 - 62)
        for i in range(11):
            u = i / 10
            c.line_to(x0 + 36 * u, y0 - 62 + 9 * u + 3 * math.sin(t * 6 - u * 4) * u)
        for i in range(10, -1, -1):
            u = i / 10
            c.line_to(x0 + 36 * u, y0 - 42 - 9 * u + 3 * math.sin(t * 6 - u * 4) * u)
        c.close_path()
        c.set_source_rgba(*GOLD, a)
        c.fill()


def draw_line(ctx, gctx, g, cam, col, pulse):
    """Fundo preto: a encosta é só uma linha fina, de ponta a ponta da faixa."""
    cx = cam[0]
    x0, x1 = int(cx) - 12, int(cx + W) + 12
    for c, wdt, rgba in ((gctx, 5, (*col, 0.30 + 0.25 * pulse)),
                         (ctx, 2.2, (0.80, 0.80, 0.84, 0.55 + 0.25 * pulse))):
        c.set_line_width(wdt)
        c.set_source_rgba(*rgba)
        c.move_to(x0, g(x0))
        for x in range(x0, x1 + 1, 4):
            c.line_to(x, g(x))
        c.stroke()


def ease_back(u):
    u = clamp(u)
    k = 1.9
    return 1 + (k + 1) * (u - 1) ** 3 + k * (u - 1) ** 2


def draw_thoughts(ctx, gctx, name, t, f, heads, g, rnd):
    """Pensamentos em coordenadas do mundo: nascem a crescer da cabeça, ficam por cima,
    caem para trás até ao chão e ficam lá (a câmara deixa-os para trás) até desaparecerem."""
    for item in THOUGHTS[name]:
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
            x, y = head[0], head[1] - S.HEAD_R - 6 - 44 * clamp(age / T_GROW)
        else:
            fs = min(f, int(round((t0 + T_GROW + hold) * FPS)))
            hx, hy = heads[fs]
            p0 = (hx, hy - S.HEAD_R - 50)
            lx = hx - 130
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
                alpha = 1 - ramp(r, T_REST * 0.4, T_REST)
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
    ap.add_argument("--frames", help="só estes tempos (s), separados por vírgula")
    ap.add_argument("--dump", help="pasta para gravar cada frame renderizado em PNG")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--sheet", default=os.path.join(ROOT, "out", "climb_v3_frames.png"))
    ap.add_argument("--music", help="ficheiro da música: deteta BPM, batidas e drop (alinha o drop aos 17 s)")
    ap.add_argument("--bpm", type=float, default=140.0, help="BPM provisório quando não há --music")
    args = ap.parse_args()
    ensure_font()
    precompute()

    only = {int(round(float(s) * FPS)) for s in args.frames.split(",")} if args.frames else None
    sheet_f = {int(round(s * FPS)): s for s in [0, 10, 17, 25, 29.5]}
    sheet_imgs = {}

    sync = BeatSync.from_audio(args.music, DROP) if args.music else BeatSync.grid(args.bpm, DROP)
    if args.music:
        print(f"música: BPM {sync.bpm}, drop no segundo {sync.info['drop']} -> começar a música no "
              f"segundo {sync.offset:.2f}")
    heads = {n: [] for n in NAMES}
    title1 = make_title([("WHO REACHES THE ", (0.80, 0.80, 0.80), False), ("TOP?", GOLD, True)])
    title2 = make_title([("WHICH ONE ARE ", (0.80, 0.80, 0.80), False), ("YOU?", GOLD, True)])

    rnd = random.Random(7)
    parts = [Particles(100 + i) for i in range(4)]
    sr = random.Random(42)
    sparkles = [dict(x=sr.uniform(-650, 400), y=sr.uniform(-LH * 0.85, LH * 0.1), s=sr.uniform(4, 10),
                     ph=sr.uniform(0, 6.28), v=sr.uniform(8, 25)) for _ in range(50)]

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    glow = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx, gctx = cairo.Context(surf), cairo.Context(glow)
    final = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    fctx = cairo.Context(final)
    writer = None if only else Writer(args.out)
    dt = 1 / FPS

    for f in range(NF):
        t = f / FPS
        states = [st_anger(t, f, rnd), st_obsession(t, f), st_discipline(t, f), st_motivation(t, f)]
        for n, st in zip(NAMES, states):
            heads[n].append(st["pose"]["head"])
        pulse = sync.pulse(t)

        # --- partículas (avançam sempre: o estado é igual com ou sem --frames)
        for i, s in enumerate(states):
            P, name = parts[i], NAMES[i]
            L = LANES[name]
            g = L["g"]
            col = s.get("gcol", COL[name])
            v = abs(speed(L["x"], t))
            bc = s["boulders"][0][0] if s["boulders"] else None
            # brasas néon a sair do boneco
            ne = s["embers"]
            n = int(ne) + (1 if rnd.random() < ne - int(ne) else 0)
            for _ in range(n):
                px, py = S.limb_point(s["pose"], rnd.random(), rnd.random())
                spread = 1.0 + (2.0 if s.get("rage") else 0.0)
                P.emit(px, py, 1, vx=(-60 * spread, 20 * spread), vy=(-80 * spread, -10), life=(0.45, 1.1),
                       size=(1.3, 2.6), color=col, g=-30, kind="ember")
            if s["moving"] and v > 4:
                if rnd.random() < min(1.0, v / 60):
                    fx = s["pose"]["footL"] if math.sin(L["ph"][f]) < 0 else s["pose"]["footR"]
                    P.emit(fx[0], fx[1] - 2, 2, vx=(-70, -10), vy=(-70, -10), size=(1.3, 3.0))
                if bc and rnd.random() < min(0.9, v / 70):
                    P.emit(bc[0] - 4, bc[1] + R - 3, 1, vx=(-110, -30), vy=(-90, -20), size=(1.8, 3.6),
                           color=(0.58, 0.5, 0.45), kind="rock", life=(0.8, 1.6))
            if name == "OBSESSION" and abs(t - 6.05) < dt / 2:
                P.emit(s["x"], g(s["x"]) - 4, 30, vx=(-120, 40), vy=(-160, -20), size=(1.5, 3.4))
            if name == "MOTIVATION" and s.get("rolling_back") and bc and rnd.random() < 0.8:
                P.emit(bc[0] + 8, bc[1] + R - 2, 2, vx=(0, 70), vy=(-70, -10), size=(1.2, 2.6))
            if name == "ANGER":
                if abs(t - DROP) < dt / 2:
                    P.emit(bc[0] - R, bc[1], 70, vx=(-320, 260), vy=(-380, -40), life=(0.3, 0.9),
                           size=(1.6, 3.2), color=(1, 0.4, 0.2), g=500, kind="spark")
                    P.emit(bc[0], bc[1] + R - 4, 20, vx=(-200, 80), vy=(-240, -60), size=(2, 4.5),
                           color=(0.6, 0.5, 0.45), kind="rock")
                if s["rage"] and t < ANG_TOP and bc:
                    P.emit(bc[0] - R * 0.8, bc[1] - 4, 4, vx=(-260, 90), vy=(-260, -30), life=(0.2, 0.6),
                           size=(1.4, 2.8), color=(1, 0.36, 0.2), g=500, kind="spark")
                    P.emit(bc[0] - 4, bc[1] + R - 4, 2, vx=(-260, -60), vy=(-200, -40), size=(2, 4.2),
                           color=(0.6, 0.5, 0.45), kind="rock")
                    fx = s["pose"]["footL"]
                    P.emit(fx[0], fx[1] - 2, 3, vx=(-160, -30), vy=(-100, -20), size=(1.5, 3.2))
                if abs(t - (ANG_TOP + 0.3)) < dt / 2:
                    P.emit(ANG_SUMMIT + 20, g(ANG_SUMMIT) - 6, 24, vx=(-60, 260), vy=(-240, -40), size=(2, 4.5),
                           color=(0.6, 0.5, 0.45), kind="rock")
            P.step(dt, g)

        if only is not None and f not in only:
            continue

        # --- fundo e título
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        gctx.set_operator(cairo.OPERATOR_CLEAR)
        gctx.paint()
        gctx.set_operator(cairo.OPERATOR_OVER)
        sw = ramp(t, 28.7, 28.9)
        if sw < 1:
            ctx.set_source_surface(title1, 0, 0)
            ctx.paint_with_alpha(1 - sw)
        if sw > 0:
            pop = 1 + 0.06 * (1 - ramp(t, 28.8, 29.15))
            ctx.save()
            ctx.translate(W / 2, 180)
            ctx.scale(pop, pop)
            ctx.translate(-W / 2, -180)
            ctx.set_source_surface(title2, 0, 0)
            ctx.paint_with_alpha(sw)
            ctx.restore()
        draw_text(ctx, "@channel", 30, 248, 17, (0.85, 0.85, 0.85, 0.16), 1.5)

        # --- faixas
        for i, s in enumerate(states):
            name = NAMES[i]
            L = LANES[name]
            g = L["g"]
            cam = L["cam"][f]
            top = LANE_TOP + i * LH
            for c in (ctx, gctx):
                c.save()
                c.translate(0, top)
                c.rectangle(0, 0, W, LH)
                c.clip()
            shake = (0, 0)
            if name == "ANGER" and DROP <= t < ANG_TOP + 0.5:
                k = 2.5 + 8 * pulse  # treme ao ritmo das batidas
                shake = (rnd.uniform(-k, k), rnd.uniform(-k * 0.7, k * 0.7))
            for c in (ctx, gctx):
                c.save()
                c.translate(-cam[0] + shake[0], -cam[1] + shake[1])

            draw_line(ctx, gctx, g, cam, s.get("gcol", COL[name]), pulse)
            if L["summit"] is not None:
                draw_flag(ctx, gctx, g, L["summit"] + 30, t)

            if name == "ANGER" and s["rage"]:
                hx, hy = s["pose"]["hip"]
                a = (0.26 + 0.14 * pulse) * (1 - ramp(t, WIN + 0.4, WIN + 1.4))
                rg = cairo.RadialGradient(hx, hy, 10, hx, hy, 240)
                rg.add_color_stop_rgba(0, 0.9, 0.08, 0.05, a)
                rg.add_color_stop_rgba(1, 0.9, 0.08, 0.05, 0)
                ctx.set_source(rg)
                ctx.paint()

            for c, ang, bg in s["boulders"]:
                S.draw_boulder(ctx, c, R, ang, glow=bg)
            parts[i].draw(ctx, gctx)
            color = s.get("color", COL[name])
            gcol = s.get("gcol", COL[name])
            S.draw_figure(ctx, s["pose"], color=color, glow=(*gcol, s["glow"]), gctx=gctx)
            if name == "ANGER" and s["rage"]:  # halo extra a pulsar
                S.draw_figure(gctx, s["pose"], color=tuple(c * 0.6 for c in gcol), width=7 * S.K, core=0)

            if name == "ANGER":
                Lt = ramp(t, WIN + 0.1, WIN + 1.4)
                if Lt > 0:
                    cx, cy = s["pose"]["neck"]
                    rad = cairo.RadialGradient(cx, cy, 0, cx, cy, 120 + 650 * Lt)
                    rad.add_color_stop_rgba(0, 0.92, 0.97, 1.0, 0.85 * Lt)
                    rad.add_color_stop_rgba(0.12, 0.70, 0.85, 1.0, 0.45 * Lt)
                    rad.add_color_stop_rgba(0.5, 0.35, 0.55, 0.95, 0.16 * Lt)
                    rad.add_color_stop_rgba(1, 0.2, 0.3, 0.7, 0)
                    ctx.set_source(rad)
                    ctx.paint()
                    for sp in sparkles:
                        x = cx + sp["x"] + 10 * math.sin(t * 0.8 + sp["ph"])
                        y = cy + 40 + ((sp["y"] - sp["v"] * (t - WIN)) % (LH * 1.1)) - LH * 0.85
                        tw = 0.5 + 0.5 * math.sin(t * 4 + sp["ph"] * 3)
                        vis = clamp((120 + 650 * Lt - math.hypot(x - cx, y - cy)) / 150)
                        if vis > 0:
                            twinkle(ctx, x, y, sp["s"] * (0.6 + 0.5 * tw), (0.75, 0.88, 1.0, (0.35 + 0.65 * tw) * vis))
                    S.draw_figure(ctx, s["pose"], color=(1, 1, 1), glow=(0.55, 0.8, 1.0, 0.35), gctx=gctx)
            draw_thoughts(ctx, gctx, name, t, f, heads[name], g, rnd)
            for c in (ctx, gctx):
                c.restore()

            if name == "ANGER" and t >= DROP:
                fl = math.exp(-(t - DROP) / 0.12) * 0.75
                if fl > 0.01:
                    ctx.set_source_rgba(1, 0.85, 0.85, fl)
                    ctx.paint()

            dim = 0.0
            if name != "ANGER" and 15.0 <= t < DROP:
                dim = 0.55 * ramp(t, 15.0, 15.6)
            if name != "ANGER":
                dim = max(dim, 0.4 * ramp(t, WIN - 0.4, WIN + 0.4))
            if dim > 0:
                ctx.set_source_rgba(0, 0, 0, dim)
                ctx.paint()
                gctx.set_operator(cairo.OPERATOR_DEST_OUT)
                gctx.set_source_rgba(0, 0, 0, dim)
                gctx.paint()
                gctx.set_operator(cairo.OPERATOR_OVER)

            draw_label(ctx, name)
            for c in (ctx, gctx):
                c.restore()

        add_glow(surf, glow, scale=2, radius=5, gain=1.2 + 0.45 * pulse)

        for i in range(5):
            y = LANE_TOP + i * LH
            hot = (0.6 + 0.4 * pulse) if (i in (0, 1) and DROP <= t < WIN) else 0
            ctx.set_source_rgba(0.42 + 0.4 * hot, 0.07, 0.07, 0.95)
            ctx.set_line_width(2)
            ctx.move_to(0, y)
            ctx.line_to(W, y)
            ctx.stroke()

        # pulsação suave do vídeo inteiro em cada batida (mais forte depois do drop)
        z = 1 + (0.004 if t < DROP else 0.010) * pulse
        fctx.set_source_rgb(0, 0, 0)
        fctx.paint()
        fctx.save()
        fctx.translate(W / 2, H * 0.45)
        fctx.scale(z, z)
        fctx.translate(-W / 2, -H * 0.45)
        fctx.set_source_surface(surf, 0, 0)
        fctx.paint()
        fctx.restore()

        if writer:
            writer.write(final)
        if args.dump:
            os.makedirs(args.dump, exist_ok=True)
            final.write_to_png(os.path.join(args.dump, f"t{t:05.2f}.png"))
        if f in sheet_f and not only:
            p = os.path.join(os.path.dirname(args.sheet), f"_f{f:03d}.png")
            final.write_to_png(p)
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
