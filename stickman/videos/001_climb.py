"""Stickman #001 · "WHO REACHES THE TOP?" (Anger vs Obsession vs Discipline vs Motivation).

v2 (pedido do dono): câmara a seguir cada boneco, o cume fica escondido no escuro e só se revela
no fim; só a Anger lá chega. Bonecos néon, cada um com a sua cor, muitas partículas.
Drop da música aos 17,0 s. Sem música no ficheiro (faixa silenciosa).

    python3 stickman/videos/001_climb.py                     # -> stickman/out/climb_v2.mp4 + folha de frames
    python3 stickman/videos/001_climb.py --frames 0,17 --dump /tmp/f   # só PNG
"""
import argparse
import math
import os
import random
import sys

import cairo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib.core import FPS, H, W, Writer, clamp, draw_text, ensure_font, lerp, pchip, ramp, text_width, window  # noqa: E402
from lib.fx import Particles, add_glow, blur_surface, rock_texture, twinkle  # noqa: E402
from lib import stick as S  # noqa: E402

S.set_scale(1.18)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "out", "climb_v2.mp4")

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
GROUND_SCREEN = 0.76                 # altura do chão (fração da faixa) debaixo do boneco
FOG0, FOG1 = 650, 850                # nevoeiro escuro à direita: esconde o que vem aí

R, D = 28.0 * S.K, 82.0 * S.K
SLOPE = 0.26


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
MOT_SUMMIT = MOT_SIT + D + 290       # estava "a 2 passos": só se vê no fim
DIS_X = pchip([(0, 60), (30, 60 + 30 * 31)])
OBS_X = pchip([(0, 90), (3, 300), (6.0, 500), (6.15, 490), (7.4, 300), (8.4, 300),
               (12, 480), (17, 760), (24, 900), (30, 960)])
ANG_SUMMIT = 1180.0
ANG_TOP_X = ANG_SUMMIT - D - 12
ANG_X = pchip([(0, 75), (2, 140), (3.2, 160), (5.5, 250), (7, 265), (9.5, 340), (12.2, 385),
               (13.1, 300), (15, 312), (DROP, 312), (19, 700), (21.4, ANG_TOP_X), (22.0, ANG_TOP_X + 40),
               (22.6, ANG_SUMMIT - 8), (30, ANG_SUMMIT - 8)])
ANG_TOP = 21.4

LANES = {
    "ANGER": dict(x=ANG_X, summit=ANG_SUMMIT, seed=3, cycle=lambda t: 74 if t >= DROP else 52),
    "OBSESSION": dict(x=OBS_X, summit=None, seed=5, cycle=lambda t: 70),
    "DISCIPLINE": dict(x=DIS_X, summit=None, seed=7, cycle=lambda t: 50),
    "MOTIVATION": dict(x=MOT_X, summit=MOT_SUMMIT, seed=9, cycle=lambda t: 64 if t < 4 else 44),
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
            cx = follow - HIP_SCREEN_X + (170 * ramp(t, 24.8, 26.2) if nm == "MOTIVATION" else 0)
            cy = g(follow + 40) - GROUND_SCREEN * LH
            L["cam"].append((cx, cy))


def speed(xfun, t):
    return (xfun(t + 0.02) - xfun(t - 0.02)) / 0.04


def hand_target(c):
    return (c[0] - R * 0.93, c[1] - R * 0.30)


def thought(t, t0, t1, txt, style="w"):
    a = window(t, t0, t1, 0.16)
    return (txt, a, style, t - t0) if a > 0 else None


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
    th = [thought(t, 0.3, 2.6, "LET'S GO!"), thought(t, 6.6, 9.4, "I'M SO TIRED..."),
          thought(t, 10.9, 13.5, "I'LL REST A BIT."), thought(t, 26.0, 28.0, "WAIT... WHAT?")]
    return dict(pose=pose, glow=0.8, boulders=[(c, bx / R * 1.02, None)], thoughts=th, x=xh,
                moving=t < MOT_RELEASE, bx=bx, rolling_back=t > MOT_RELEASE, embers=1.0 - 0.7 * tired)


def st_discipline(t, f):
    L = LANES["DISCIPLINE"]
    g = L["g"]
    xh, ph = DIS_X(t), L["ph"][f]
    bx = xh + D
    c = S.rest_center(g, bx, R)
    pose = S.push_pose(g, xh, ph, hand_target(c), lean=41 + heave(ph) * 0.6, stride=14, lift=9)
    th = [thought(t, 2.6, 5.0, "ONE MORE STEP."), thought(t, 11.0, 13.4, "KEEP GOING."),
          thought(t, 23.2, 25.6, "ONE MORE STEP."), thought(t, 27.0, 29.8, "STAY STEADY.")]
    return dict(pose=pose, glow=0.8, boulders=[(c, bx / R * 1.02, None)], thoughts=th, x=xh,
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
    th = [thought(t, 1.2, 3.2, "FASTER."), thought(t, 6.1, 7.6, "NO, NO, NO!"),
          thought(t, 9.0, 11.6, "I CAN'T STOP."), thought(t, 24.2, 26.8, "NOT ENOUGH.")]
    return dict(pose=pose, glow=0.85, boulders=[(c, bx / R * 1.02, None)], thoughts=th, x=xh,
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
    pose = S.blend(push, S.stand_pose(g, xh, arms="up", t=t), ramp(t, 22.0, 22.7))
    if 15.0 <= t < DROP:  # tremor antes do drop
        k = 1.5 * ramp(t, 15.0, 15.4)
        pose = S.offset(pose, rnd.uniform(-k, k), rnd.uniform(-k, k))
        c = (c[0] + rnd.uniform(-k, k) * 0.5, c[1])
    cool = ramp(t, 22.4, 23.8)
    if rage:
        color = tuple(lerp(a, b, cool) for a, b in zip((1.0, 0.22, 0.18), (0.92, 0.96, 1.0)))
        gcol = tuple(lerp(a, b, cool) for a, b in zip((1.0, 0.10, 0.06), (0.45, 0.72, 1.0)))
        glow = 1.0 + 0.3 * math.sin(t * 22) * (1 - cool)
    else:
        color, gcol, glow = COL["ANGER"], COL["ANGER"], 0.75
    bglow = (1.0, 0.25, 0.15, 0.9) if rage and t < ANG_TOP + 0.6 else None
    th = [thought(t, 4.4, 6.8, "WHY WON'T YOU MOVE?", "r"), thought(t, 13.0, 15.0, "I'M TOO SLOW!", "r"),
          thought(t, DROP + 0.12, 19.4, "NOTHING STOPS ME.", "R"),
          thought(t, 19.5, 21.8, "I'LL BREAK THROUGH.", "R")]
    return dict(pose=pose, color=color, gcol=gcol, glow=glow,
                boulders=[(c, bx / R * 1.02, bglow)] if c[0] < ANG_SUMMIT + 500 else [],
                thoughts=th, x=xh, moving=not (15.0 <= t < DROP) and t < 22.0, bx=bx, rage=rage,
                embers=(4.0 if rage and t < 22.3 else 1.2))


# ---------- elementos estáticos ----------
def lane_overlay():
    """Vinheta e sombra no topo da faixa (por cima de tudo, em coordenadas de ecrã)."""
    w, h = W, int(math.ceil(LH))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surf)
    vg = cairo.RadialGradient(w * 0.42, h * 0.6, h * 0.35, w * 0.42, h * 0.6, w * 0.72)
    vg.add_color_stop_rgba(0, 0, 0, 0, 0)
    vg.add_color_stop_rgba(1, 0, 0, 0, 0.7)
    ctx.set_source(vg)
    ctx.paint()
    tg = cairo.LinearGradient(0, 0, 0, 46)
    tg.add_color_stop_rgba(0, 0, 0, 0, 0.6)
    tg.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(tg)
    ctx.rectangle(0, 0, w, 46)
    ctx.fill()
    lg = cairo.LinearGradient(0, 0, 120, 0)
    lg.add_color_stop_rgba(0, 0, 0, 0, 0.55)
    lg.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(lg)
    ctx.rectangle(0, 0, 120, h)
    ctx.fill()
    return surf


def fog_pattern():
    fg = cairo.LinearGradient(FOG0, 0, FOG1, 0)
    for i in range(9):
        u = i / 8
        fg.add_color_stop_rgba(u, 0.0, 0.0, 0.0, 0.985 * (u * u * (3 - 2 * u)))
    return fg


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


def draw_terrain(ctx, g, cam, tex, seed):
    cx, cy = cam
    x0, x1 = int(cx) - 12, int(cx + W) + 12
    ctx.move_to(x0, cy + LH + 20)
    for x in range(x0, x1 + 1, 4):
        ctx.line_to(x, g(x))
    ctx.line_to(x1, cy + LH + 20)
    ctx.close_path()
    pat = cairo.SurfacePattern(tex)
    pat.set_extend(cairo.EXTEND_REPEAT)
    ctx.save()
    ctx.set_source(pat)
    ctx.fill_preserve()
    dg = cairo.LinearGradient(0, cy + LH * 0.55, 0, cy + LH)
    dg.add_color_stop_rgba(0, 0, 0, 0, 0)
    dg.add_color_stop_rgba(1, 0, 0, 0, 0.5)
    ctx.set_source(dg)
    ctx.fill()
    ctx.restore()
    # pedrinhas na superfície (dão a sensação de avanço)
    step = 46
    for i in range(int(x0 / step) - 1, int(x1 / step) + 2):
        r = random.Random(i * 7919 + seed * 31)
        x = i * step + r.uniform(0, step * 0.8)
        s = r.uniform(2.0, 6.5)
        y = g(x)
        ctx.move_to(x - s, y + 1)
        ctx.line_to(x - s * 0.4, y - s * 0.9)
        ctx.line_to(x + s * 0.6, y - s * 0.7)
        ctx.line_to(x + s, y + 1)
        ctx.close_path()
        sh = r.uniform(0.22, 0.4)
        ctx.set_source_rgba(sh, sh * 0.9, sh * 0.85, 0.9)
        ctx.fill()
    for wdt, a in ((7, 0.06), (2.2, 0.5)):
        ctx.set_line_width(wdt)
        ctx.set_source_rgba(0.62, 0.52, 0.46, a)
        ctx.move_to(x0, g(x0))
        for x in range(x0, x1 + 1, 4):
            ctx.line_to(x, g(x))
        ctx.stroke()


def draw_thought(ctx, item, rnd):
    txt, a, style, age = item
    cx, base = 330, 80
    rise = 6 * (1 - ramp(age, 0, 0.2))
    if style == "R":
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
    ap.add_argument("--frames", help="só estes tempos (s), separados por vírgula")
    ap.add_argument("--dump", help="pasta para gravar cada frame renderizado em PNG")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--sheet", default=os.path.join(ROOT, "out", "climb_v2_frames.png"))
    args = ap.parse_args()
    ensure_font()
    precompute()

    only = {int(round(float(s) * FPS)) for s in args.frames.split(",")} if args.frames else None
    sheet_f = {int(round(s * FPS)): s for s in [0, 10, 17, 25, 29.5]}
    sheet_imgs = {}

    sky = [rock_texture(640, 640, 11 + 7 * i, base=(15, 11, 11), var=9) for i in range(4)]
    gtex = [rock_texture(640, 640, 111 + 7 * i, base=(40, 28, 25), var=18) for i in range(4)]
    overlay = lane_overlay()
    fog = fog_pattern()
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
    writer = None if only else Writer(args.out)
    dt = 1 / FPS

    for f in range(NF):
        t = f / FPS
        states = [st_anger(t, f, rnd), st_obsession(t, f), st_discipline(t, f), st_motivation(t, f)]

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
        ctx.set_source_rgb(0.025, 0.022, 0.024)
        ctx.paint()
        gctx.set_operator(cairo.OPERATOR_CLEAR)
        gctx.paint()
        gctx.set_operator(cairo.OPERATOR_OVER)
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
            # céu de rocha com paralaxe
            pat = cairo.SurfacePattern(sky[i])
            pat.set_extend(cairo.EXTEND_REPEAT)
            pat.set_matrix(cairo.Matrix(x0=cam[0] * 0.45, y0=cam[1] * 0.45))
            ctx.set_source(pat)
            ctx.paint()

            shake = (0, 0)
            if name == "ANGER" and DROP <= t < ANG_TOP + 0.5:
                k = 8 * (1 - 0.4 * ramp(t, DROP, ANG_TOP))
                shake = (rnd.uniform(-k, k), rnd.uniform(-k * 0.7, k * 0.7))
            for c in (ctx, gctx):
                c.save()
                c.translate(-cam[0] + shake[0], -cam[1] + shake[1])

            draw_terrain(ctx, g, cam, gtex[i], L["seed"])
            if L["summit"] is not None:
                draw_flag(ctx, gctx, g, L["summit"] + 30, t)

            if name == "ANGER" and s["rage"]:
                hx, hy = s["pose"]["hip"]
                a = 0.34 * (1 - ramp(t, 22.4, 23.6))
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

            reveal = 0.0
            if name == "ANGER":
                reveal = ramp(t, 20.6, 21.8)
                Lt = ramp(t, 22.2, 24.0)
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
                        y = cy + 40 + ((sp["y"] - sp["v"] * (t - 22.2)) % (LH * 1.1)) - LH * 0.85
                        tw = 0.5 + 0.5 * math.sin(t * 4 + sp["ph"] * 3)
                        vis = clamp((120 + 650 * Lt - math.hypot(x - cx, y - cy)) / 150)
                        if vis > 0:
                            twinkle(ctx, x, y, sp["s"] * (0.6 + 0.5 * tw), (0.75, 0.88, 1.0, (0.35 + 0.65 * tw) * vis))
                    S.draw_figure(ctx, s["pose"], color=(1, 1, 1), glow=(0.55, 0.8, 1.0, 0.35), gctx=gctx)
            elif name == "MOTIVATION":
                reveal = ramp(t, 24.8, 25.9)
            for c in (ctx, gctx):
                c.restore()

            # nevoeiro: o que vem à frente fica escondido até à revelação
            if reveal < 1:
                ctx.save()
                ctx.set_source(fog)
                ctx.paint_with_alpha(1 - reveal)
                ctx.restore()
                gctx.save()
                gctx.set_source(fog)
                gctx.set_operator(cairo.OPERATOR_DEST_OUT)
                gctx.paint_with_alpha(1 - reveal)
                gctx.restore()
            ctx.set_source_surface(overlay, 0, 0)
            ctx.paint()

            if name == "ANGER" and t >= DROP:
                fl = math.exp(-(t - DROP) / 0.12) * 0.75
                if fl > 0.01:
                    ctx.set_source_rgba(1, 0.85, 0.85, fl)
                    ctx.paint()

            dim = 0.0
            if name != "ANGER" and 15.0 <= t < DROP:
                dim = 0.55 * ramp(t, 15.0, 15.6)
            if name in ("OBSESSION", "DISCIPLINE"):
                dim = max(dim, 0.3 * ramp(t, 22.3, 23.3))
            if name == "MOTIVATION":
                dim = max(dim, 0.3 * ramp(t, 22.3, 23.3) * (1 - ramp(t, 24.6, 25.2)))
            if dim > 0:
                ctx.set_source_rgba(0, 0, 0, dim)
                ctx.paint()
                gctx.set_operator(cairo.OPERATOR_DEST_OUT)
                gctx.set_source_rgba(0, 0, 0, dim)
                gctx.paint()
                gctx.set_operator(cairo.OPERATOR_OVER)

            for th in s["thoughts"]:
                if th:
                    draw_thought(ctx, th, rnd)
            draw_label(ctx, name)
            for c in (ctx, gctx):
                c.restore()

        add_glow(surf, glow, scale=2, radius=5, gain=1.25)

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
        if f in sheet_f and not only:
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
