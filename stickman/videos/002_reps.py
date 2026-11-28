"""Stickman #002 · "WHO DOES THE MOST REPS?" (Anger vs Obsession vs Discipline vs Motivation).

Mesmo estilo do #001: fundo preto, 4 faixas, bonecos néon, pensamentos que caem para trás.
Cada um faz flexões; contador grande de reps à direita (fora da coluna dos botões do YouTube)
e indicador de posição ao vivo (1ST..4TH) ao lado do nome.
História: Motivation dispara e desiste ("TOMORROW..."), Obsession passa à frente e rebenta,
Discipline constante, Anger falha, cai e no drop (17,0 s) arranca brutal e fica em 1º isolado.
Sem música nem áudio no ficheiro (o dono junta o som na app; drop aos 17,0 s).

    python3 stickman/videos/002_reps.py                         # -> stickman/out/reps_v1.mp4 + folha
    python3 stickman/videos/002_reps.py --frames 0,17 --dump /tmp/f
"""
import argparse
import math
import os
import random
import sys

import cairo
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib.core import FPS, H, W, Writer, clamp, draw_text, ensure_font, lerp, pchip, ramp, text_width  # noqa: E402
from lib.fx import Particles, add_glow, twinkle  # noqa: E402
from lib import stick as S  # noqa: E402
from lib.beats import BeatSync  # noqa: E402
from lib.ui import GOLD, draw_label, draw_thoughts, make_title  # noqa: E402

S.set_scale(1.9)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VER = "reps_v1"
OUT = os.path.join(ROOT, "out", VER + ".mp4")
MUSIC = os.path.join(ROOT, "music", "stakillaz.mp3")
HANDLE = "@ThePsychArena"

DURATION = 30.0
DROP = 17.0
WIN = 28.0          # luz branca/azulada na faixa da Anger
NF = int(DURATION * FPS)

# ---------- layout ----------
LANE_TOP = 262
LANE_BOTTOM = int(H * 0.82)          # ~18% de baixo livre (zona do YouTube)
LH = (LANE_BOTTOM - LANE_TOP) / 4
NAMES = ["ANGER", "OBSESSION", "DISCIPLINE", "MOTIVATION"]
COL = {"ANGER": (1.0, 0.16, 0.13), "OBSESSION": (0.74, 0.34, 1.0),
       "DISCIPLINE": (0.12, 0.80, 1.0), "MOTIVATION": (1.0, 0.64, 0.10)}
GY = LH * 0.83                        # chão (coordenada local da faixa)
FOOT_X = 220                          # pés do boneco
CNT_X = 760                           # centro do contador (botões do YouTube ficam à direita de ~940)
CNT_Y = LH * 0.60                     # linha de base do número


def ground(x):
    return GY


# ---------- reps: ritmo (reps/s) -> contagem acumulada ----------
def integrate(rate, t0=0.0, start=0.0):
    sub = 8
    n = NF * sub + sub
    out = np.zeros(NF + 1)
    acc, dt = start, 1.0 / (FPS * sub)
    for k in range(n):
        t = t0 + k * dt
        if k % sub == 0 and k // sub <= NF:
            out[k // sub] = acc
        acc += rate(t) * dt
    return out


MOT_STOP = 9.4
MOT_RATE = pchip([(0, 2.6), (0.4, 3.3), (3.8, 3.3), (5.0, 2.3), (8.0, 1.3), (9.0, 0.7), (MOT_STOP, 0.0), (30, 0.0)])
OBS_DOWN = 21.6                       # rebenta: cai no chão
OBS_RATE = pchip([(0, 1.9), (4.0, 2.1), (6.0, 3.0), (9.0, 3.1), (DROP, 3.0), (17.6, 3.4), (20.8, 3.3),
                  (21.3, 1.0), (OBS_DOWN, 0.0), (30, 0.0)])
DIS_RATE = lambda t: 2.2
ANG_RATE = pchip([(DROP, 0.0), (17.08, 10.0), (17.6, 13.5), (21.0, 13.0), (26.0, 12.0), (WIN, 9.0), (30, 7.0)])

# Anger antes do drop: reps lentas e falhadas. (início, fim, tipo)
ANG_SEGS = [(0.0, 1.2, "rep"), (1.2, 2.4, "rep"), (2.4, 3.6, "rep"), (3.6, 4.8, "rep"),
            (4.8, 6.7, "fail"), (6.7, 8.0, "rep"), (8.0, 9.3, "rep"), (9.3, 11.0, "fail"),
            (11.0, 12.3, "rep"), (12.3, 13.3, "fall")]
ANG_PRE = sum(1 for s in ANG_SEGS if s[2] == "rep")   # reps contadas antes do drop
ANG_START = ANG_PRE + 0.5                              # no drop parte do fundo (meio da rep)


def ang_pre(t):
    """(profundidade, contagem) da Anger antes do drop."""
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
        if kind == "fail":  # desce, tenta subir a tremer, cai, volta a pôr-se em cima (não conta)
            if u < 0.25:
                d = 0.5 - 0.5 * math.cos(math.pi * u / 0.25)
            elif u < 0.6:
                d = 1 - 0.45 * math.sin(math.pi * 0.5 * (u - 0.25) / 0.35) + 0.03 * math.sin(t * 70)
            elif u < 0.7:
                d = lerp(0.55, 1.22, (u - 0.6) / 0.1)
            else:
                d = 1.22 * (1 - ramp(u, 0.72, 1.0))
            return d, cnt
        # fall: desce e desaba de barriga
        d = 0.5 - 0.5 * math.cos(math.pi * clamp(u / 0.5))
        return d + 0.3 * ramp(u, 0.45, 0.75), cnt
    return 1.3, cnt


def precompute():
    global CNT
    CNT = {
        "MOTIVATION": integrate(MOT_RATE),
        "OBSESSION": integrate(OBS_RATE),
        "DISCIPLINE": integrate(DIS_RATE),
    }
    ang = np.zeros(NF + 1)
    post = integrate(lambda t: ANG_RATE(t + DROP) if t + DROP <= 30 else 7.0)
    fd = int(DROP * FPS)
    for f in range(NF + 1):
        t = f / FPS
        ang[f] = ang_pre(t)[1] if t < DROP else ANG_START + post[f - fd]
    CNT["ANGER"] = ang


def reps(name, f):
    return int(math.floor(CNT[name][min(f, NF)] + 1e-6))


# ---------- posições ao vivo ----------
def compute_ranks():
    order = list(NAMES[::-1])  # ordem inicial (empates resolvidos pela ordem anterior)
    RANKS = []
    for f in range(NF + 1):
        cur = {n: reps(n, f) for n in NAMES}
        prev = {n: i for i, n in enumerate(order)}
        order = sorted(NAMES, key=lambda n: (-cur[n], prev[n]))
        RANKS.append({n: i for i, n in enumerate(order)})
    return RANKS


# ---------- estados ----------
def phase_depth(c):
    u = c - math.floor(c)
    return 0.5 - 0.5 * math.cos(2 * math.pi * u)


def st_motivation(t, f):
    c = CNT["MOTIVATION"][f]
    tired = ramp(t, 4.0, 9.0)
    d = phase_depth(c)
    push = S.pushup_pose(GY, FOOT_X, d, sag=0.8 * tired)
    lie = S.lie_back_pose(GY, FOOT_X + 70, t)
    pose = S.blend(push, lie, ramp(t, MOT_STOP + 0.1, MOT_STOP + 0.9))
    return dict(pose=pose, glow=0.8, embers=1.6 - 1.2 * tired, moving=t < MOT_STOP, frozen=t > MOT_STOP + 0.5)


def st_discipline(t, f):
    d = phase_depth(CNT["DISCIPLINE"][f])
    return dict(pose=S.pushup_pose(GY, FOOT_X, d), glow=0.8, embers=0.8, moving=True, frozen=False)


def st_obsession(t, f, rnd):
    c = CNT["OBSESSION"][f]
    down = ramp(t, OBS_DOWN - 0.35, OBS_DOWN + 0.15)
    d = phase_depth(c)
    d = lerp(d, 1.3, down)
    pose = S.pushup_pose(GY, FOOT_X, d, sag=0.3 * ramp(t, 19.5, 21.0))
    if t > OBS_DOWN:  # no chão, braços a tremer, ainda tenta
        k = 1.4
        try_up = 0.12 * max(0, math.sin((t - OBS_DOWN) * 2.4)) ** 4
        pose = S.pushup_pose(GY, FOOT_X, 1.3 - try_up * 3)
        pose = S.offset(pose, rnd.uniform(-k, k), rnd.uniform(-k * 0.5, k * 0.5))
    return dict(pose=pose, glow=0.85, embers=1.6 + 1.4 * ramp(t, 9, 20) - 2.2 * down,
                moving=t < OBS_DOWN, frozen=t > OBS_DOWN + 0.3)


def anger_pose(t, f):
    if t < DROP:
        d, _ = ang_pre(t)
        d = lerp(d, 1.0, ramp(t, 16.82, DROP))  # sobe do chão mesmo antes do drop
        return S.pushup_pose(GY, FOOT_X, d)
    c = CNT["ANGER"][f]
    d = phase_depth(c)
    d = 0.15 + 0.8 * d  # amplitude mais curta e brutal
    return S.pushup_pose(GY, FOOT_X, d)


def st_anger(t, f, rnd):
    rage = t >= DROP
    pose = anger_pose(t, f)
    if 13.3 <= t < DROP:  # tremor leve no chão
        k = 0.8 + 1.2 * ramp(t, 15.0, 16.8)
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
            ghosts.append(anger_pose(ff / FPS, ff))
    return dict(pose=pose, color=color, gcol=gcol, glow=glow, rage=rage, ghosts=ghosts,
                embers=(4.0 if rage and t < WIN + 0.3 else 1.0), moving=rage, frozen=False)


# pensamentos (início, texto, estilo)
THOUGHTS = {
    "ANGER": [(5.0, "WHY IS THIS SO HARD?", "r"), (13.25, "I'M TOO WEAK!", "r"),
              (DROP + 0.05, "NEVER AGAIN.", "R"), (21.4, "WATCH ME.", "R")],
    "OBSESSION": [(4.2, "FASTER."), (10.0, "MORE. MORE."), (18.0, "NOT ENOUGH."), (21.9, "MY ARMS...")],
    "DISCIPLINE": [(4.6, "ONE MORE."), (11.2, "ONE MORE."), (19.6, "STAY STEADY."), (25.4, "ONE MORE.")],
    "MOTIVATION": [(0.25, "LET'S GO!"), (9.7, "TOMORROW...")],
}

ORD = ["1ST", "2ND", "3RD", "4TH"]


def draw_rank(ctx, gctx, x, rank, since, col, t):
    txt = ORD[rank]
    pop = 1 + 0.55 * math.exp(-max(0.0, since) / 0.18)
    c = GOLD if rank == 0 else (0.86, 0.86, 0.9)
    flash = math.exp(-max(0.0, since) / 0.3)
    c = tuple(lerp(a, b, flash) for a, b in zip(c, col))
    sz = 27
    ctx.save()
    ctx.translate(x, 30)
    ctx.scale(pop, pop)
    # pastilha
    w = text_width(ctx, txt, sz, 1.5) + 16
    ctx.rectangle(-8, -sz * 0.5 - 6, w, sz + 6)
    ctx.set_source_rgba(*c, 0.16 + 0.3 * flash)
    ctx.fill()
    ctx.rectangle(-8, -sz * 0.5 - 6, w, sz + 6)
    ctx.set_source_rgba(*c, 0.9)
    ctx.set_line_width(1.6)
    ctx.stroke()
    draw_text(ctx, txt, 0, sz * 0.36 + 2, sz, (*c, 1.0), 1.5)
    ctx.restore()
    if rank == 0 or flash > 0.05:
        gctx.save()
        gctx.translate(x, 30)
        gctx.scale(pop, pop)
        draw_text(gctx, txt, 0, sz * 0.36 + 2, sz, (*c, 0.6 + 0.4 * flash), 1.5)
        gctx.restore()


def draw_counter(ctx, gctx, name, n, since, col, frozen, t, rnd, pulse):
    rage = name == "ANGER" and t >= DROP
    size = 128
    if rage:
        size = lerp(140, 210, ramp(t, DROP, 23.0))
    pop = 1 + (0.06 if rage else 0.16) * math.exp(-max(0.0, since) / 0.09)
    if rage:
        pop += 0.03 * pulse
    c = (0.42, 0.42, 0.46) if frozen else col
    if rage:
        cool = ramp(t, WIN + 0.3, WIN + 1.4)
        c = tuple(lerp(a, b, cool) for a, b in zip((1.0, 0.24, 0.2), (0.95, 0.98, 1.0)))
    txt = str(n)
    jit = None
    if rage and t < WIN + 0.4:
        jit = lambda i: (rnd.uniform(-3, 3), rnd.uniform(-3, 3))
    ctx.save()
    ctx.translate(CNT_X, CNT_Y)
    ctx.scale(pop, pop)
    draw_text(ctx, txt, 4, 6, size, (0, 0, 0, 0.7), 2, "center")
    draw_text(ctx, txt, 0, 0, size, (*c, 1.0), 2, "center", jitter=jit)
    ctx.restore()
    if not frozen:
        gctx.save()
        gctx.translate(CNT_X, CNT_Y)
        gctx.scale(pop, pop)
        draw_text(gctx, txt, 0, 0, size, (*c, 0.55 + (0.35 if rage else 0.15) * pulse), 2, "center")
        gctx.restore()
    lab = "REPS"
    draw_text(ctx, lab, CNT_X, CNT_Y + 40, 26, (*(c if not frozen else (0.4, 0.4, 0.44)), 0.85), 8, "center")


def draw_floor(ctx, gctx, col, pulse, hot=0.0):
    for c, wdt, rgba in ((gctx, 5 + 5 * pulse + 4 * hot, (*col, 0.30 + 0.55 * pulse + 0.3 * hot)),
                         (ctx, 2.2 + 1.2 * pulse, (0.80, 0.80, 0.84, 0.55 + 0.4 * pulse))):
        c.set_line_width(wdt)
        c.set_source_rgba(*rgba)
        c.move_to(-20, GY)
        c.line_to(W + 20, GY)
        c.stroke()


# ---------- render ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", help="só estes tempos (s), separados por vírgula")
    ap.add_argument("--dump", help="pasta para gravar cada frame renderizado em PNG")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--sheet", default=os.path.join(ROOT, "out", VER + "_frames.png"))
    ap.add_argument("--music", default=MUSIC if os.path.exists(MUSIC) else None,
                    help="música só para a pulsação/pré-visualização (o mp4 final sai sem áudio)")
    ap.add_argument("--bpm", type=float, default=140.0, help="BPM provisório quando não há --music")
    args = ap.parse_args()
    ensure_font()
    precompute()
    RANKS = compute_ranks()
    # instantes em que cada contador/posição mudou (para os pops)
    last_inc = {n: [] for n in NAMES}
    last_rank = {n: [] for n in NAMES}
    for n in NAMES:
        li, lr = -9.0, -9.0
        for f in range(NF + 1):
            if f > 0 and reps(n, f) != reps(n, f - 1):
                li = f / FPS
            if f > 0 and RANKS[f][n] != RANKS[f - 1][n]:
                lr = f / FPS
                if RANKS[f][n] < RANKS[f - 1][n]:
                    print(f"{f / FPS:5.2f}s  {n} sobe para {ORD[RANKS[f][n]]}")
            last_inc[n].append(li)
            last_rank[n].append(lr)
    print("reps finais:", {n: reps(n, NF - 1) for n in NAMES})

    only = {int(round(float(s) * FPS)) for s in args.frames.split(",")} if args.frames else None
    sheet_f = {int(round(s * FPS)): s for s in [0, 9, 17, 22, 29.5]}
    sheet_imgs = {}

    sync = BeatSync.from_audio(args.music, DROP) if args.music else BeatSync.grid(args.bpm, DROP)
    heads = {n: [] for n in NAMES}
    title1 = make_title([("WHO DOES THE MOST ", (0.80, 0.80, 0.80), False), ("REPS?", GOLD, True)],
                        LANE_TOP, size=76)
    title2 = make_title([("WHICH ONE ARE ", (0.80, 0.80, 0.80), False), ("YOU?", GOLD, True)], LANE_TOP)

    rnd = random.Random(7)
    parts = [Particles(100 + i) for i in range(4)]
    sr = random.Random(42)
    sparkles = [dict(x=sr.uniform(-300, 950), y=sr.uniform(0, LH), s=sr.uniform(4, 10),
                     ph=sr.uniform(0, 6.28), v=sr.uniform(8, 25)) for _ in range(55)]

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
                P.emit(px, py, 1, vx=(-60 * spread, 20 * spread), vy=(-80 * spread, -10), life=(0.45, 1.1),
                       size=(1.3, 2.6), color=col, g=-30, kind="ember")
            inc = f > 0 and reps(name, f) != reps(name, f - 1)
            if inc and s["moving"]:  # pó das mãos a cada rep
                hx, hy = s["pose"]["handR"]
                P.emit(hx, GY - 2, 3, vx=(-60, 60), vy=(-50, -10), size=(1.2, 2.6))
            if name == "ANGER" and s["rage"] and t < WIN + 0.3:
                hx, hy = s["pose"]["head"]
                if rnd.random() < 0.8:  # suor
                    P.emit(hx, hy - 4, 2, vx=(-160, 120), vy=(-260, -80), life=(0.5, 0.9), size=(2.2, 3.6),
                           color=(0.55, 0.8, 1.0), g=900, kind="sweat")
                P.emit(s["pose"]["handR"][0], GY - 2, 2, vx=(-160, 160), vy=(-140, -20), size=(1.4, 3.0))
                if rnd.random() < 0.5:
                    P.emit(s["pose"]["hip"][0], s["pose"]["hip"][1], 2, vx=(-220, 120), vy=(-220, -30),
                           life=(0.2, 0.6), size=(1.4, 2.8), color=(1, 0.36, 0.2), g=500, kind="spark")
            if name == "ANGER" and abs(t - DROP) < dt / 2:
                cx, cy = s["pose"]["neck"]
                P.emit(cx, cy, 80, vx=(-380, 380), vy=(-400, -40), life=(0.3, 0.9),
                       size=(1.6, 3.2), color=(1, 0.4, 0.2), g=500, kind="spark")
                P.emit(cx, GY - 4, 30, vx=(-260, 260), vy=(-240, -60), size=(2, 4.5))
            if name == "OBSESSION" and abs(t - OBS_DOWN) < dt / 2:
                cx, cy = s["pose"]["neck"]
                P.emit(cx, GY - 4, 24, vx=(-200, 200), vy=(-160, -30), size=(1.5, 3.5))
            if name == "OBSESSION" and 18.0 < t < OBS_DOWN and rnd.random() < 0.35:
                hx, hy = s["pose"]["head"]
                P.emit(hx, hy - 4, 1, vx=(-90, 60), vy=(-160, -60), life=(0.5, 0.8), size=(1.8, 2.8),
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

        # --- faixas
        for i, s in enumerate(states):
            name = NAMES[i]
            top = LANE_TOP + i * LH
            for c in (ctx, gctx):
                c.save()
                c.translate(0, top)
                c.rectangle(0, 0, W, LH)
                c.clip()
            shake = (0, 0)
            if name == "ANGER" and DROP <= t < WIN + 0.3:
                k = 2.0 + 7 * pulse
                shake = (rnd.uniform(-k, k), rnd.uniform(-k * 0.7, k * 0.7))
            elif name == "ANGER" and 15.0 <= t < DROP:
                k = 1.2 * ramp(t, 15.0, 16.0)
                shake = (rnd.uniform(-k, k), rnd.uniform(-k, k))
            for c in (ctx, gctx):
                c.save()
                c.translate(shake[0], shake[1])

            gcol = s.get("gcol", COL[name])
            draw_floor(ctx, gctx, gcol, pulse, hot=(1.0 if s.get("rage") and t < WIN else 0.0))

            if name == "ANGER" and s["rage"]:
                hx, hy = s["pose"]["hip"]
                a = (0.26 + 0.14 * pulse) * (1 - ramp(t, WIN + 0.4, WIN + 1.4))
                rg = cairo.RadialGradient(hx + 40, hy, 10, hx + 40, hy, 300)
                rg.add_color_stop_rgba(0, 0.9, 0.08, 0.05, a)
                rg.add_color_stop_rgba(1, 0.9, 0.08, 0.05, 0)
                ctx.set_source(rg)
                ctx.paint()

            parts[i].draw(ctx, gctx)
            color = s.get("color", COL[name])
            for k, gp in enumerate(s.get("ghosts", [])):
                S.draw_figure(ctx, gp, color=color, alpha=0.28 / (k + 1), core=0)
            S.draw_figure(ctx, s["pose"], color=color, glow=(*gcol, s["glow"]), gctx=gctx)
            if name == "ANGER" and s["rage"]:  # halo extra a pulsar
                S.draw_figure(gctx, s["pose"], color=tuple(c * 0.6 for c in gcol), width=7 * S.K, core=0)

            if name == "ANGER":  # luz branca/azulada no fim
                Lt = ramp(t, WIN + 0.1, WIN + 1.4)
                if Lt > 0:
                    cx, cy = s["pose"]["neck"]
                    rad = cairo.RadialGradient(cx, cy, 0, cx, cy, 120 + 900 * Lt)
                    rad.add_color_stop_rgba(0, 0.92, 0.97, 1.0, 0.85 * Lt)
                    rad.add_color_stop_rgba(0.12, 0.70, 0.85, 1.0, 0.45 * Lt)
                    rad.add_color_stop_rgba(0.5, 0.35, 0.55, 0.95, 0.16 * Lt)
                    rad.add_color_stop_rgba(1, 0.2, 0.3, 0.7, 0)
                    ctx.set_source(rad)
                    ctx.paint()
                    for sp in sparkles:
                        x = sp["x"] + 10 * math.sin(t * 0.8 + sp["ph"])
                        y = (sp["y"] - sp["v"] * (t - WIN)) % LH
                        tw = 0.5 + 0.5 * math.sin(t * 4 + sp["ph"] * 3)
                        vis = clamp((120 + 900 * Lt - math.hypot(x - cx, y - cy)) / 150)
                        if vis > 0:
                            twinkle(ctx, x, y, sp["s"] * (0.6 + 0.5 * tw), (0.75, 0.88, 1.0, (0.35 + 0.65 * tw) * vis))
                    S.draw_figure(ctx, s["pose"], color=(1, 1, 1), glow=(0.55, 0.8, 1.0, 0.35), gctx=gctx)

            draw_counter(ctx, gctx, name, reps(name, f), t - last_inc[name][f], COL[name], s["frozen"],
                         t, rnd, pulse)
            draw_thoughts(ctx, gctx, THOUGHTS[name], t, f, heads[name], ground, rnd, FPS, back=150, rise=30)
            for c in (ctx, gctx):
                c.restore()

            if name == "ANGER" and t >= DROP:
                fl = math.exp(-(t - DROP) / 0.12) * 0.75
                if fl > 0.01:
                    ctx.set_source_rgba(1, 0.85, 0.85, fl)
                    ctx.paint()

            dim = 0.0
            if name != "ANGER" and 13.6 <= t < DROP:
                dim = 0.55 * ramp(t, 13.6, 14.4)
            if name != "ANGER":
                dim = max(dim, 0.4 * ramp(t, WIN - 0.4, WIN + 0.4))
            if dim > 0:
                ctx.set_source_rgba(0, 0, 0, dim)
                ctx.paint()
                gctx.set_operator(cairo.OPERATOR_DEST_OUT)
                gctx.set_source_rgba(0, 0, 0, dim)
                gctx.paint()
                gctx.set_operator(cairo.OPERATOR_OVER)

            lw = draw_label(ctx, name)
            draw_rank(ctx, gctx, 30 + lw + 22, RANKS[f][name], t - last_rank[name][f], COL[name], t)
            for c in (ctx, gctx):
                c.restore()

        add_glow(surf, glow, scale=2, radius=5, gain=1.15 + 1.0 * pulse)

        for i in range(5):
            y = LANE_TOP + i * LH
            hot = (0.6 + 0.4 * pulse) if (i in (0, 1) and DROP <= t < WIN) else 0
            ctx.set_source_rgba(min(1, 0.42 + 0.4 * hot + 0.25 * pulse), 0.07 + 0.05 * pulse, 0.07, 0.95)
            ctx.set_line_width(2)
            ctx.move_to(0, y)
            ctx.line_to(W, y)
            ctx.stroke()

        z = 1 + (0.012 if t < DROP else 0.026) * pulse
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
            p = os.path.join(ROOT, "out", f"_sheet_{f}.png")
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
