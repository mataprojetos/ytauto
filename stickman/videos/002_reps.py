"""Stickman #002 · "WHO DOES THE MOST REPS?" (Anger vs Obsession vs Discipline vs Motivation).

v2 (pedido do dono): uma barra de ponta a ponta do ecrã e os 4 lado a lado a fazer elevações.
Por cima da barra, sobre cada um: nome, posição ao vivo (1ST..4TH) e contador grande de reps (v4).
Mesmo estilo do #001: fundo preto, bonecos néon, pensamentos que nascem da cabeça e caem para o chão.
História: Motivation dispara e desiste ("TOMORROW..."), Obsession passa à frente e rebenta,
Discipline constante, Anger falha, cai e no drop (17,0 s) volta à barra brutal e fica em 1º isolado.
Sem áudio no ficheiro final (o dono junta o som do Stakillaz na app; drop aos 17,0 s).

    python3 stickman/videos/002_reps.py                          # -> stickman/out/reps_v2.mp4 + folha
    python3 stickman/videos/002_reps.py --music m.mp3            # + pré-visualização com música
    python3 stickman/videos/002_reps.py --frames 0,17 --dump /tmp/f
"""
import argparse
import math
import os
import random
import subprocess
import sys

import cairo
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib.core import FPS, H, W, Writer, clamp, draw_text, ensure_font, lerp, pchip, ramp, text_width  # noqa: E402
from lib.fx import Particles, add_glow, twinkle  # noqa: E402
from lib import stick as S  # noqa: E402
from lib.beats import BeatSync  # noqa: E402
from lib.ui import GOLD, RED, ease_back, make_title  # noqa: E402

S.set_scale(2.0)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VER = "reps_v4"
OUT = os.path.join(ROOT, "out", VER + ".mp4")
MUSIC = os.path.join(ROOT, "music", "stakillaz.mp3")
HANDLE = "@ThePsychArena"

DURATION = 30.0
DROP = 17.0
WIN = 28.0          # luz branca/azulada à volta da Anger
NF = int(DURATION * FPS)

# ---------- layout ----------
TOP = 262                             # fim da zona do título
BAR_Y = 990
FLOOR_Y = 1425
NAMES = ["ANGER", "OBSESSION", "DISCIPLINE", "MOTIVATION"]
XS = {"ANGER": 210, "OBSESSION": 430, "DISCIPLINE": 650, "MOTIVATION": 870}  # simétrico em torno de x=540
COL = {"ANGER": (1.0, 0.16, 0.13), "OBSESSION": (0.74, 0.34, 1.0),
       "DISCIPLINE": (0.12, 0.80, 1.0), "MOTIVATION": (1.0, 0.64, 0.10)}
CNT_Y = 750                           # linha de base do contador (por cima da barra, à altura dos olhos)
NAME_Y = 548
RANK_Y = 600                          # nome, posição e contador por cima da barra, longe dos cantos de baixo


def ground(x):
    return FLOOR_Y


# ---------- reps: ritmo (reps/s) -> contagem acumulada ----------
def integrate(rate):
    sub = 8
    out = np.zeros(NF + 1)
    acc, dt = 0.0, 1.0 / (FPS * sub)
    for k in range((NF + 1) * sub):
        if k % sub == 0:
            out[k // sub] = acc
        acc += rate(k * dt) * dt
    return out


MOT_STOP, MOT_LET = 9.4, 9.75         # pára; larga a barra
MOT_RATE = pchip([(0, 2.6), (0.4, 3.3), (3.8, 3.3), (5.0, 2.3), (8.0, 1.3), (9.0, 0.7), (MOT_STOP, 0.0), (30, 0.0)])
OBS_DOWN = 21.6                       # rebenta: larga a barra
OBS_RATE = pchip([(0, 1.9), (4.0, 2.1), (6.0, 3.0), (9.0, 3.1), (DROP, 3.0), (17.6, 3.4), (20.6, 3.3),
                  (21.2, 1.0), (21.45, 0.0), (30, 0.0)])
DIS_RATE = lambda t: 2.2
ANG_RATE = pchip([(0, 0.0), (0.08, 10.0), (0.6, 13.5), (4.0, 13.0), (9.0, 12.0), (WIN - DROP, 9.0), (13, 7.0)])

# Anger antes do drop: reps lentas e falhadas. (início, fim, tipo)
ANG_SEGS = [(0.0, 1.2, "rep"), (1.2, 2.4, "rep"), (2.4, 3.6, "rep"), (3.6, 4.8, "rep"),
            (4.8, 6.7, "fail"), (6.7, 8.0, "rep"), (8.0, 9.3, "rep"), (9.3, 11.0, "fail"),
            (11.0, 12.3, "rep"), (12.3, 12.9, "hang")]
ANG_LET = 12.9                        # larga a barra e cai no chão
ANG_JUMP = 16.7                       # salta de volta para a barra (chega aos 17,0)
ANG_PRE = sum(1 for s in ANG_SEGS if s[2] == "rep")
ANG_START = ANG_PRE + 0.5             # no drop parte do topo (meio da rep)


def ang_pre(t):
    """(profundidade, contagem) da Anger antes do drop (enquanto está na barra)."""
    cnt = 0
    for a, b, kind in ANG_SEGS:
        if t >= b:
            cnt += kind == "rep"
            continue
        if t < a:
            break
        u = (t - a) / (b - a)
        if kind == "rep":
            return 0.5 - 0.5 * math.cos(2 * math.pi * u), cnt
        if kind == "fail":  # sobe a meio, treme, escorrega e fica pendurado (não conta)
            if u < 0.25:
                d = 0.55 * (0.5 - 0.5 * math.cos(math.pi * u / 0.25))
            elif u < 0.62:
                d = 0.55 - 0.1 * ramp(u, 0.25, 0.62) + 0.025 * math.sin(t * 70)
            elif u < 0.72:
                d = lerp(0.45, 0.0, (u - 0.62) / 0.1)
            else:
                d = 0.0
            return d, cnt
        return 0.04 * math.sin(t * 50), cnt  # hang: a tremer antes de largar
    return 0.0, cnt


def precompute():
    global CNT
    CNT = {"MOTIVATION": integrate(MOT_RATE), "OBSESSION": integrate(OBS_RATE), "DISCIPLINE": integrate(DIS_RATE)}
    post = integrate(ANG_RATE)
    fd = int(DROP * FPS)
    ang = np.zeros(NF + 1)
    for f in range(NF + 1):
        t = f / FPS
        ang[f] = ang_pre(t)[1] if t < DROP else ANG_START + post[f - fd]
    CNT["ANGER"] = ang


def reps(name, f):
    return int(math.floor(CNT[name][min(f, NF)] + 1e-6))


def compute_ranks():
    order = list(NAMES[::-1])
    out = []
    for f in range(NF + 1):
        cur = {n: reps(n, f) for n in NAMES}
        prev = {n: i for i, n in enumerate(order)}
        order = sorted(NAMES, key=lambda n: (-cur[n], prev[n]))
        out.append({n: i for i, n in enumerate(order)})
    return out


# ---------- quedas e saltos entre a barra e o chão ----------
def foot_y(p):
    return max(p["footL"][1], p["footR"][1])


def fall(hang, floor, dt):
    """Larga a barra: cai com gravidade até os pés tocarem no chão e assenta na pose do chão."""
    lim = FLOOR_Y - foot_y(hang)
    g = 2800.0
    t_land = math.sqrt(2 * lim / g)
    if dt < t_land:
        return S.offset(hang, 0, 0.5 * g * dt * dt), False
    landed = S.offset(hang, 0, lim)
    return S.blend(landed, floor, ramp(dt - t_land, 0, 0.28)), dt - t_land < 0.05


def phase_depth(c):
    u = c - math.floor(c)
    return 0.5 - 0.5 * math.cos(2 * math.pi * u)


# ---------- estados ----------
def st_motivation(t, f):
    x = XS["MOTIVATION"]
    tired = ramp(t, 4.0, 9.0)
    if t < MOT_LET:
        d = phase_depth(CNT["MOTIVATION"][f]) * (1 - ramp(t, MOT_STOP - 0.2, MOT_STOP + 0.1))
        pose = S.pullup_pose(BAR_Y, x, d, swing=3 * tired * math.sin(t * 3), kick=0.6 * d * (1 + tired))
        landed = False
    else:
        hang = S.pullup_pose(BAR_Y, x, 0.0)
        pose, landed = fall(hang, S.lie_back_pose(FLOOR_Y, x - 40, t), t - MOT_LET)
    return dict(pose=pose, glow=0.8, embers=1.6 - 1.2 * tired, moving=t < MOT_STOP,
                frozen=t > MOT_LET + 0.3, on_bar=t < MOT_LET, landed=landed)


def st_discipline(t, f):
    d = phase_depth(CNT["DISCIPLINE"][f])
    return dict(pose=S.pullup_pose(BAR_Y, XS["DISCIPLINE"], d, kick=0.3 * d), glow=0.8, embers=0.8,
                moving=True, frozen=False, on_bar=True, landed=False)


def st_obsession(t, f, rnd):
    x = XS["OBSESSION"]
    landed = False
    if t < OBS_DOWN:
        strain = ramp(t, 19.5, 21.2)
        d = phase_depth(CNT["OBSESSION"][f]) * (1 - ramp(t, 21.2, 21.5))
        pose = S.pullup_pose(BAR_Y, x, d, kick=0.5 * d + 0.4 * strain, swing=2 * strain * math.sin(t * 9))
    else:
        hang = S.pullup_pose(BAR_Y, x, 0.0, kick=0.3)
        pose, landed = fall(hang, S.sit_pose(ground, x - 30), t - OBS_DOWN)
        if t > OBS_DOWN + 0.6:  # braços a tremer
            k = 1.2
            pose = S.offset(pose, rnd.uniform(-k, k), rnd.uniform(-k * 0.4, k * 0.4))
    return dict(pose=pose, glow=0.85, embers=1.6 + 1.4 * ramp(t, 9, 20) - 2.4 * ramp(t, OBS_DOWN, OBS_DOWN + 0.5),
                moving=t < OBS_DOWN, frozen=t > OBS_DOWN + 0.3, on_bar=t < OBS_DOWN, landed=landed)


def anger_pose(t, f):
    x = XS["ANGER"]
    kneel = S.kneel_pose(FLOOR_Y, x - 20, pound=max(0.0, math.sin((t - 13.6) * 5)) ** 3 if 13.6 < t < 15.2 else 0.0)
    if t < ANG_LET:
        d, _ = ang_pre(t)
        return S.pullup_pose(BAR_Y, x, d, kick=0.5 * d), False
    if t < ANG_JUMP:
        return fall(S.pullup_pose(BAR_Y, x, 0.0), kneel, t - ANG_LET)
    if t < DROP:  # salto de volta para a barra
        u = ramp(t, ANG_JUMP, DROP)
        target = S.pullup_pose(BAR_Y, x, 0.5)
        p = S.blend(kneel, target, u)
        return S.offset(p, 0, -60 * math.sin(math.pi * u)), False
    c = CNT["ANGER"][f]
    d = 0.12 + 0.85 * phase_depth(c)
    return S.pullup_pose(BAR_Y, x, d, kick=0.9 * d, swing=2 * math.sin(t * 31)), False


def st_anger(t, f, rnd):
    rage = t >= DROP
    pose, landed = anger_pose(t, f)
    if ANG_LET + 0.5 <= t < ANG_JUMP:  # tremor leve no chão
        k = 0.8 + 1.4 * ramp(t, 15.0, 16.6)
        pose = S.offset(pose, rnd.uniform(-k, k), rnd.uniform(-k * 0.5, k * 0.5))
    cool = ramp(t, WIN + 0.3, WIN + 1.4)
    if rage:
        color = tuple(lerp(a, b, cool) for a, b in zip((1.0, 0.22, 0.18), (0.92, 0.96, 1.0)))
        gcol = tuple(lerp(a, b, cool) for a, b in zip((1.0, 0.10, 0.06), (0.45, 0.72, 1.0)))
        glow = 1.0 + 0.3 * math.sin(t * 22) * (1 - cool)
    else:
        color, gcol, glow = COL["ANGER"], COL["ANGER"], 0.75
    ghosts = []
    if rage and t < WIN + 0.5:  # rasto do movimento (velocidade brutal)
        for k in (1, 2):
            ff = max(0, f - k)
            ghosts.append(anger_pose(ff / FPS, ff)[0])
    return dict(pose=pose, color=color, gcol=gcol, glow=glow, rage=rage, ghosts=ghosts,
                embers=(4.0 if rage and t < WIN + 0.3 else 1.0), moving=rage or t < ANG_LET, frozen=False,
                on_bar=t < ANG_LET or t >= DROP, landed=landed)


# pensamentos (início, texto, estilo): 'w' branco, 'r' vermelho, 'R' vermelho a tremer com brilho
THOUGHTS = {
    "ANGER": [(5.0, "WHY IS THIS SO HARD?", "r"), (13.3, "I'M TOO WEAK!", "r"),
              (DROP + 0.05, "NEVER AGAIN.", "R"), (21.3, "WATCH ME.", "R")],
    "OBSESSION": [(4.2, "FASTER."), (10.0, "MORE. MORE."), (18.0, "NOT ENOUGH."), (22.0, "MY ARMS...")],
    "DISCIPLINE": [(4.6, "ONE MORE."), (11.2, "ONE MORE."), (19.6, "STAY STEADY."), (25.2, "ONE MORE.")],
    "MOTIVATION": [(0.25, "LET'S GO!"), (10.1, "TOMORROW...")],
}
T_GROW, T_FALL, T_REST = 0.35, 0.6, 1.2


def wrap(txt, n=11):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > n:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    return lines + [cur]


def draw_thoughts(ctx, gctx, name, t, f, heads, rnd):
    """Nascem a crescer da cabeça, ficam por cima e caem até ao chão ao lado do boneco."""
    for item in THOUGHTS[name]:
        t0, txt = item[0], item[1]
        style = item[2] if len(item) > 2 else "w"
        hold = 1.45 + 0.03 * len(txt)
        age = t - t0
        if age < 0 or age > T_GROW + hold + T_FALL + T_REST:
            continue
        lines = wrap(txt)
        size = 34 if style == "R" else 31
        lh = size * 1.08
        alpha, ang = 1.0, 0.0
        hx, hy = heads[f]
        hold_y = min(hy - S.HEAD_R - 40, BAR_Y - 108)
        cx = clamp(XS[name], 105, 975)
        if age < T_GROW + hold:
            e = ease_back(age / T_GROW)
            sc = 0.12 + 0.88 * e
            u = clamp(age / T_GROW)
            x, y = lerp(hx, cx, u), lerp(hy - S.HEAD_R, hold_y, u)
        else:
            fs = min(f, int(round((t0 + T_GROW + hold) * FPS)))
            hy0 = heads[fs][1]
            p0 = (cx, min(hy0 - S.HEAD_R - 40, BAR_Y - 108))
            lx, ly = cx - 55, FLOOR_Y - 4
            land = -0.12 if name != "MOTIVATION" else 0.1
            u = (age - T_GROW - hold) / T_FALL
            if u < 1:
                x = lerp(p0[0], lx, u)
                y = lerp(p0[1], ly, u * u)
                ang = land * u - 0.5 * math.sin(math.pi * u)
                sc = lerp(1.0, 0.8, u)
            else:
                r = age - T_GROW - hold - T_FALL
                x, y = lx, ly - 6 * abs(math.sin(r * 18)) * math.exp(-r * 9)
                ang, sc = land, 0.8
                alpha = 1 - clamp((r - T_REST * 0.4) / (T_REST * 0.6))
        n = len(lines)
        for c, glow_pass in ((ctx, False), (gctx, True)):
            if glow_pass and style != "R":
                continue
            c.save()
            c.translate(x, y)
            c.rotate(ang)
            c.scale(sc, sc)
            for k, ln in enumerate(lines):
                yy = (k - (n - 1)) * lh  # a última linha assenta em y
                if glow_pass:
                    draw_text(c, ln, 0, yy, size, (1, 0.1, 0.06, 0.8 * alpha), 3, "center")
                elif style == "R":
                    jit = lambda i: (rnd.uniform(-2.4, 2.4), rnd.uniform(-2.4, 2.4))
                    draw_text(c, ln, 0, yy, size, (1, 0.22, 0.18, alpha), 3, "center", jitter=jit)
                else:
                    col = (0.95, 0.24, 0.20) if style == "r" else (0.95, 0.95, 0.95)
                    draw_text(c, ln, 2, yy + 3, size, (0, 0, 0, 0.7 * alpha), 2.2, "center")
                    draw_text(c, ln, 0, yy, size, (*col, alpha), 2.2, "center")
            c.restore()


ORD = ["1ST", "2ND", "3RD", "4TH"]


def draw_rank(ctx, gctx, cx, rank, since, col):
    txt = ORD[rank]
    flash = math.exp(-max(0.0, since) / 0.3)
    pop = 1 + 0.55 * math.exp(-max(0.0, since) / 0.18)
    c = GOLD if rank == 0 else (0.86, 0.86, 0.9)
    c = tuple(lerp(a, b, flash) for a, b in zip(c, col))
    sz = 30
    w = text_width(ctx, txt, sz, 1.5)
    ctx.save()
    ctx.translate(cx, RANK_Y)
    ctx.scale(pop, pop)
    ctx.rectangle(-w / 2 - 10, -sz * 0.86, w + 20, sz + 8)
    ctx.set_source_rgba(*c, 0.16 + 0.3 * flash)
    ctx.fill_preserve()
    ctx.set_source_rgba(*c, 0.9)
    ctx.set_line_width(1.8)
    ctx.stroke()
    draw_text(ctx, txt, 0, 0, sz, (*c, 1.0), 1.5, "center")
    ctx.restore()
    if rank == 0 or flash > 0.05:
        gctx.save()
        gctx.translate(cx, RANK_Y)
        gctx.scale(pop, pop)
        draw_text(gctx, txt, 0, 0, sz, (*c, 0.6 + 0.4 * flash), 1.5, "center")
        gctx.restore()


def draw_counter(ctx, gctx, name, n, since, col, frozen, t, rnd, pulse):
    cx = XS[name]
    rage = name == "ANGER" and t >= DROP
    size = 112
    if rage:
        size = lerp(124, 158, ramp(t, DROP, 23.0))
    pop = 1 + (0.05 if rage else 0.18) * math.exp(-max(0.0, since) / 0.09)
    if rage:
        pop += 0.03 * pulse
    c = (0.42, 0.42, 0.46) if frozen else col
    if rage:
        cool = ramp(t, WIN + 0.3, WIN + 1.4)
        c = tuple(lerp(a, b, cool) for a, b in zip((1.0, 0.24, 0.2), (0.95, 0.98, 1.0)))
    jit = (lambda i: (rnd.uniform(-3, 3), rnd.uniform(-3, 3))) if rage and t < WIN + 0.4 else None
    txt = str(n)
    ctx.save()
    ctx.translate(cx, CNT_Y)
    ctx.scale(pop, pop)
    draw_text(ctx, txt, 4, 6, size, (0, 0, 0, 0.7), 2, "center")
    draw_text(ctx, txt, 0, 0, size, (*c, 1.0), 2, "center", jitter=jit)
    ctx.restore()
    if not frozen:
        gctx.save()
        gctx.translate(cx, CNT_Y)
        gctx.scale(pop, pop)
        draw_text(gctx, txt, 0, 0, size, (*c, 0.55 + (0.35 if rage else 0.15) * pulse), 2, "center")
        gctx.restore()
    draw_text(ctx, "REPS", cx, CNT_Y + 38, 22, (*(c if not frozen else (0.4, 0.4, 0.44)), 0.85), 7, "center")


def draw_name(ctx, name):
    cx = XS[name]
    draw_text(ctx, name, cx + 2, NAME_Y + 2, 26, (0, 0, 0, 0.7), 2.4, "center")
    draw_text(ctx, name, cx, NAME_Y, 26, (*RED, 1.0), 2.4, "center")


def draw_bar(ctx, gctx, t, pulse, rage_k):
    """Barra de ponta a ponta com postes; vibra junto às mãos da Anger durante o drop."""
    xa = XS["ANGER"]
    pts = []
    for x in range(20, W - 19, 6):
        amp = rage_k * (2.5 + 5 * pulse) * math.exp(-((x - xa) / 260) ** 2)
        pts.append((x, BAR_Y + amp * math.sin(t * 95 + x * 0.03)))
    for c, wdt, rgba in ((gctx, 9 + 6 * pulse, (0.75, 0.78, 0.9, 0.35 + 0.4 * pulse)),
                         (ctx, 5.0, (0.86, 0.87, 0.92, 1.0))):
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.set_line_width(wdt)
        c.set_source_rgba(*rgba)
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        c.stroke()
    if rage_k > 0:  # brilho vermelho na zona das mãos da Anger
        gctx.set_source_rgba(1, 0.15, 0.08, 0.6 * rage_k)
        gctx.set_line_width(10)
        gctx.move_to(xa - 110, BAR_Y)
        gctx.line_to(xa + 110, BAR_Y)
        gctx.stroke()
    for x in (26, W - 26):  # postes
        ctx.set_source_rgba(0.55, 0.56, 0.62, 0.9)
        ctx.set_line_width(4)
        ctx.move_to(x, BAR_Y - 8)
        ctx.line_to(x, FLOOR_Y)
        ctx.stroke()
        ctx.arc(x, BAR_Y, 7, 0, 2 * math.pi)
        ctx.set_source_rgba(0.86, 0.87, 0.92, 1)
        ctx.fill()


def draw_floor(ctx, gctx, pulse):
    for c, wdt, rgba in ((gctx, 5 + 5 * pulse, (0.6, 0.6, 0.7, 0.25 + 0.4 * pulse)),
                         (ctx, 2.2 + 1.0 * pulse, (0.80, 0.80, 0.84, 0.5 + 0.35 * pulse))):
        c.set_line_width(wdt)
        c.set_source_rgba(*rgba)
        c.move_to(0, FLOOR_Y)
        c.line_to(W, FLOOR_Y)
        c.stroke()


def dim_rect(ctx, gctx, x0, x1, a):
    for c, op in ((ctx, cairo.OPERATOR_OVER), (gctx, cairo.OPERATOR_DEST_OUT)):
        c.save()
        c.set_operator(op)
        c.rectangle(x0, TOP, x1 - x0, H - TOP)
        c.set_source_rgba(0, 0, 0, a)
        c.fill()
        c.restore()


# ---------- câmara: zoom nos momentos importantes (só a cena; o título fica fixo) ----------
# (instante, zoom, foco): foco = nome da personagem (segue o pescoço dela) ou None (plano geral)
CAM = [(0, 1.0, None), (9.35, 1.0, "MOTIVATION"), (9.9, 1.42, "MOTIVATION"), (11.3, 1.42, "MOTIVATION"),
       (11.9, 1.0, None), (12.5, 1.0, "ANGER"), (13.3, 1.32, "ANGER"), (16.7, 1.6, "ANGER"),
       (DROP, 1.78, "ANGER"), (17.95, 1.0, None), (20.85, 1.0, "ANGER"), (21.1, 1.2, "ANGER"),
       (21.45, 1.22, "OBSESSION"), (21.9, 1.38, "OBSESSION"), (23.2, 1.38, "OBSESSION"), (23.9, 1.0, None),
       (27.2, 1.0, "DISCIPLINE"), (27.75, 1.18, "DISCIPLINE"), (28.1, 1.2, "ANGER"), (28.8, 1.38, "ANGER"),
       (30.0, 1.45, "ANGER")]
SCENE_C = (W / 2, (TOP + H) / 2)  # centro da zona visível por baixo do título


def cam_focus(key, poses):
    if key is None:
        return SCENE_C
    return (XS[key], (NAME_Y - 30 + FLOOR_Y + 15) / 2)  # altura fixa: nome, contador, barra e chão sempre à vista


def camera(t, poses):
    """-> (zoom, tx, ty): ecrã = zoom * cena + (tx, ty). Fundo preto: pode sair da cena sem se notar."""
    i = max(0, min(len(CAM) - 2, sum(1 for k in CAM if k[0] <= t) - 1))
    (t0, z0, k0), (t1, z1, k1) = CAM[i], CAM[i + 1]
    u = ramp(t, t0, t1)
    z = lerp(z0, z1, u)
    f0, f1 = cam_focus(k0, poses), cam_focus(k1, poses)
    fx, fy = lerp(f0[0], f1[0], u), lerp(f0[1], f1[1], u)
    k = 0.85 * clamp((z - 1.0) / 0.15)  # quanto mais zoom, mais a personagem vem para o centro
    sx, sy = lerp(fx, SCENE_C[0], k), lerp(fy, SCENE_C[1], k)
    return z, sx - z * fx, sy - z * fy


# ---------- render ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", help="só estes tempos (s), separados por vírgula")
    ap.add_argument("--dump", help="pasta para gravar cada frame renderizado em PNG")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--sheet", default=os.path.join(ROOT, "out", VER + "_frames.png"))
    ap.add_argument("--music", default=MUSIC if os.path.exists(MUSIC) else None,
                    help="música do Stakillaz: pulsação nas batidas reais + pré-visualização (o mp4 final sai sem áudio)")
    ap.add_argument("--bpm", type=float, default=140.0, help="BPM provisório quando não há --music")
    args = ap.parse_args()
    ensure_font()
    precompute()
    ranks = compute_ranks()
    last_inc = {n: [] for n in NAMES}
    last_rank = {n: [] for n in NAMES}
    for n in NAMES:
        li, lr = -9.0, -9.0
        for f in range(NF + 1):
            if f > 0 and reps(n, f) != reps(n, f - 1):
                li = f / FPS
            if f > 0 and ranks[f][n] != ranks[f - 1][n]:
                lr = f / FPS
                if ranks[f][n] < ranks[f - 1][n]:
                    print(f"{f / FPS:5.2f}s  {n} sobe para {ORD[ranks[f][n]]}")
            last_inc[n].append(li)
            last_rank[n].append(lr)
    print("reps finais:", {n: reps(n, NF - 1) for n in NAMES})

    only = {int(round(float(s) * FPS)) for s in args.frames.split(",")} if args.frames else None
    sheet_f = {int(round(s * FPS)): s for s in [0, 9, 17, 22, 29.5]}
    sheet_imgs = {}

    sync = BeatSync.from_audio(args.music, DROP) if args.music else BeatSync.grid(args.bpm, DROP)
    if args.music:
        print(f"música: BPM {sync.bpm}, drop no segundo {sync.info['drop']} -> começar a música no segundo {sync.offset:.2f}")
    heads = {n: [] for n in NAMES}
    title1 = make_title([("WHO DOES THE MOST ", (0.80, 0.80, 0.80), False), ("REPS?", GOLD, True)], TOP, size=76)
    title2 = make_title([("WHICH ONE ARE ", (0.80, 0.80, 0.80), False), ("YOU?", GOLD, True)], TOP)

    rnd = random.Random(7)
    parts = [Particles(100 + i) for i in range(4)]
    sr = random.Random(42)
    sparkles = [dict(x=sr.uniform(0, W), y=sr.uniform(TOP, FLOOR_Y + 120), s=sr.uniform(4, 10),
                     ph=sr.uniform(0, 6.28), v=sr.uniform(8, 25)) for _ in range(70)]

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    glow = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx, gctx = cairo.Context(surf), cairo.Context(glow)
    final = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    fctx = cairo.Context(final)
    writer = None if only else Writer(args.out, silent_audio=False)
    dt = 1 / FPS

    for f in range(NF):
        t = f / FPS
        states = [st_anger(t, f, rnd), st_obsession(t, f, rnd), st_discipline(t, f), st_motivation(t, f)]
        for n, st in zip(NAMES, states):
            heads[n].append(st["pose"]["head"])
        pulse = sync.pulse(t)

        # --- partículas (avançam sempre)
        for i, s in enumerate(states):
            P, name = parts[i], NAMES[i]
            col = s.get("gcol", COL[name])
            ne = s["embers"]
            n = int(ne) + (1 if rnd.random() < ne - int(ne) else 0)
            for _ in range(max(0, n)):
                px, py = S.limb_point(s["pose"], rnd.random(), rnd.random())
                spread = 1.0 + (2.0 if s.get("rage") else 0.0)
                P.emit(px, py, 1, vx=(-50 * spread, 50 * spread), vy=(-80 * spread, -10), life=(0.45, 1.1),
                       size=(1.3, 2.6), color=col, g=-30, kind="ember")
            inc = f > 0 and reps(name, f) != reps(name, f - 1)
            if inc and s["on_bar"]:  # pó de magnésio das mãos a cada rep
                for hk in ("handL", "handR"):
                    hx, hy = s["pose"][hk]
                    P.emit(hx, hy + 4, 2, vx=(-50, 50), vy=(-20, 40), size=(1.2, 2.6), color=(0.9, 0.9, 0.95), g=120)
            if s.get("landed"):
                fx = s["pose"]["footL"]
                P.emit(fx[0] + 20, FLOOR_Y - 2, 4, vx=(-180, 180), vy=(-120, -20), size=(1.4, 3.2))
            if name == "ANGER" and s["rage"] and t < WIN + 0.3:
                hx, hy = s["pose"]["head"]
                if rnd.random() < 0.85:  # suor
                    P.emit(hx, hy - 4, 2, vx=(-170, 170), vy=(-260, -60), life=(0.5, 0.9), size=(2.2, 3.6),
                           color=(0.55, 0.8, 1.0), g=900, kind="sweat")
                if rnd.random() < 0.6:  # faíscas na barra
                    P.emit(XS["ANGER"] + rnd.uniform(-50, 50), BAR_Y, 2, vx=(-220, 220), vy=(-220, 60),
                           life=(0.2, 0.6), size=(1.4, 2.8), color=(1, 0.36, 0.2), g=600, kind="spark")
            if name == "ANGER" and abs(t - DROP) < dt / 2:
                P.emit(XS["ANGER"], BAR_Y, 90, vx=(-420, 420), vy=(-420, 120), life=(0.3, 0.9),
                       size=(1.6, 3.2), color=(1, 0.4, 0.2), g=500, kind="spark")
            if name == "ANGER" and abs(t - ANG_JUMP) < dt / 2:
                P.emit(XS["ANGER"], FLOOR_Y - 4, 30, vx=(-260, 260), vy=(-240, -60), size=(2, 4.5))
            if name == "OBSESSION" and 18.0 < t < OBS_DOWN and rnd.random() < 0.35:
                hx, hy = s["pose"]["head"]
                P.emit(hx, hy - 4, 1, vx=(-90, 90), vy=(-160, -60), life=(0.5, 0.8), size=(1.8, 2.8),
                       color=(0.8, 0.7, 1.0), g=800, kind="sweat")
            P.step(dt)

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
        draw_text(ctx, HANDLE, 30, 247, 20, (0.88, 0.88, 0.9, 0.55), 1.5)

        rage_k = 1.0 if DROP <= t < WIN + 0.3 else 0.0
        draw_floor(ctx, gctx, pulse)
        draw_bar(ctx, gctx, t, pulse, rage_k)

        ang = states[0]
        if ang["rage"]:  # aura vermelha à volta da Anger
            hx, hy = ang["pose"]["hip"]
            a = (0.30 + 0.16 * pulse) * (1 - ramp(t, WIN + 0.4, WIN + 1.4))
            rg = cairo.RadialGradient(hx, hy - 60, 10, hx, hy - 60, 420)
            rg.add_color_stop_rgba(0, 0.9, 0.08, 0.05, a)
            rg.add_color_stop_rgba(1, 0.9, 0.08, 0.05, 0)
            ctx.set_source(rg)
            ctx.paint()

        for i, s in enumerate(states):
            name = NAMES[i]
            shake = (0, 0)
            if name == "ANGER" and DROP <= t < WIN + 0.3:
                k = 2.0 + 6 * pulse
                shake = (rnd.uniform(-k, k), rnd.uniform(-k * 0.6, k * 0.6))
            for c in (ctx, gctx):
                c.save()
                c.translate(*shake)
            parts[i].draw(ctx, gctx)
            color = s.get("color", COL[name])
            gcol = s.get("gcol", COL[name])
            for k, gp in enumerate(s.get("ghosts", [])):
                S.draw_figure(ctx, gp, color=color, alpha=0.28 / (k + 1), core=0)
            S.draw_figure(ctx, s["pose"], color=color, glow=(*gcol, s["glow"]), gctx=gctx)
            if name == "ANGER" and s["rage"]:
                S.draw_figure(gctx, s["pose"], color=tuple(c * 0.6 for c in gcol), width=7 * S.K, core=0)
            draw_counter(ctx, gctx, name, reps(name, f), t - last_inc[name][f], COL[name], s["frozen"], t, rnd, pulse)
            for c in (ctx, gctx):
                c.restore()

        # escurecer os outros na crise e no fim
        dim = 0.55 * ramp(t, 13.6, 14.4) * (1 - ramp(t, DROP - 0.05, DROP + 0.25))
        dim = max(dim, 0.45 * ramp(t, WIN - 0.4, WIN + 0.4))
        if dim > 0:
            dim_rect(ctx, gctx, (XS["ANGER"] + XS["OBSESSION"]) / 2, W, dim)

        # luz branca/azulada à volta da Anger no fim
        Lt = ramp(t, WIN + 0.1, WIN + 1.4)
        if Lt > 0:
            cx, cy = ang["pose"]["neck"]
            rad = cairo.RadialGradient(cx, cy, 0, cx, cy, 120 + 650 * Lt)
            rad.add_color_stop_rgba(0, 0.92, 0.97, 1.0, 0.85 * Lt)
            rad.add_color_stop_rgba(0.12, 0.70, 0.85, 1.0, 0.45 * Lt)
            rad.add_color_stop_rgba(0.5, 0.35, 0.55, 0.95, 0.16 * Lt)
            rad.add_color_stop_rgba(1, 0.2, 0.3, 0.7, 0)
            ctx.set_source(rad)
            ctx.paint()
            for sp in sparkles:
                x = sp["x"] + 10 * math.sin(t * 0.8 + sp["ph"])
                y = TOP + (sp["y"] - TOP - sp["v"] * (t - WIN)) % (FLOOR_Y + 120 - TOP)
                tw = 0.5 + 0.5 * math.sin(t * 4 + sp["ph"] * 3)
                vis = clamp((120 + 650 * Lt - math.hypot(x - cx, y - cy)) / 150)
                if vis > 0:
                    twinkle(ctx, x, y, sp["s"] * (0.6 + 0.5 * tw), (0.75, 0.88, 1.0, (0.35 + 0.65 * tw) * vis))
            S.draw_figure(ctx, ang["pose"], color=(1, 1, 1), glow=(0.55, 0.8, 1.0, 0.35), gctx=gctx)

        for i, s in enumerate(states):
            draw_thoughts(ctx, gctx, NAMES[i], t, f, heads[NAMES[i]], rnd)

        for i, s in enumerate(states):
            name = NAMES[i]
            draw_name(ctx, name)
            draw_rank(ctx, gctx, XS[name], ranks[f][name], t - last_rank[name][f], COL[name])

        if t >= DROP:  # clarão do drop
            fl = math.exp(-(t - DROP) / 0.12) * 0.6
            if fl > 0.01:
                ctx.save()
                ctx.rectangle(0, TOP, W, H - TOP)
                ctx.set_source_rgba(1, 0.82, 0.82, fl)
                ctx.fill()
                ctx.restore()

        add_glow(surf, glow, scale=2, radius=5, gain=1.15 + 1.0 * pulse)

        # linha vermelha sob o título (como as faixas do #001)
        hot = (0.6 + 0.4 * pulse) if DROP <= t < WIN else 0
        ctx.set_source_rgba(min(1, 0.42 + 0.4 * hot + 0.25 * pulse), 0.07 + 0.05 * pulse, 0.07, 0.95)
        ctx.set_line_width(2)
        ctx.move_to(0, TOP)
        ctx.line_to(W, TOP)
        ctx.stroke()

        zp = 1 + (0.012 if t < DROP else 0.026) * pulse
        zc, tx, ty = camera(t, {n: st["pose"] for n, st in zip(NAMES, states)})
        z = zc * zp
        cx0, cy0 = (tx + zc * SCENE_C[0], ty + zc * SCENE_C[1])  # pulsação à volta do centro visível
        tx, ty = cx0 - (cx0 - tx) * zp, cy0 - (cy0 - ty) * zp
        fctx.set_source_rgb(0, 0, 0)
        fctx.paint()
        fctx.save()  # cena (com câmara)
        fctx.rectangle(0, TOP + 1, W, H - TOP)
        fctx.clip()
        fctx.translate(tx, ty)
        fctx.scale(z, z)
        fctx.set_source_surface(surf, 0, 0)
        fctx.paint()
        fctx.restore()
        fctx.save()  # título e linha fixos
        fctx.rectangle(0, 0, W, TOP + 1)
        fctx.clip()
        fctx.set_source_surface(surf, 0, 0)
        fctx.paint()
        fctx.restore()

        if writer:
            writer.write(final)
        if args.dump:
            os.makedirs(args.dump, exist_ok=True)
            final.write_to_png(os.path.join(args.dump, f"t{t:05.2f}.png"))
        if f in sheet_f and not only:
            p = os.path.join(ROOT, "out", f"_sheet_{f}.png")
            final.write_to_png(p)
            sheet_imgs[sheet_f[f]] = p
        if f % 90 == 0:
            print(f"{t:5.1f}s", flush=True)

    if writer:
        writer.close()
        if args.music and sync.offset is not None:
            prev = args.out.replace(".mp4", "_preview_com_musica.mp4")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", args.out, "-ss", f"{sync.offset:.3f}",
                            "-i", args.music, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                            "-b:a", "192k", "-af", "afade=t=out:st=29:d=1", "-t", "30", prev], check=True)
            print("pré-visualização com música:", prev)
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
