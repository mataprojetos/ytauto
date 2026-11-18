#!/usr/bin/env python3
"""Whatifaholic #002 — What if AI took your job? (~51 s).
Baseado em ep001/anim_ep001_v6.py: gancho com contagem + alarme, selo de loop aberto, legendas palavra a palavra,
som discreto. Fio condutor: o mesmo robô e o mesmo escritório + relógio "HOUR x" sempre no mesmo sítio."""
import math, re, json, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cairo
import numpy as np
from scipy import ndimage as _nd


def nd_dilate(m):
    return _nd.binary_dilation(m, iterations=3)
import neuro_lib as L
from neuro_lib import W, H, FPS, A, BLD, NAVY, CYAN, CREAM, SUN, INK, QUIET, seg, ease, paint_cover, glow, text

ROOT = os.path.dirname(os.path.abspath(__file__))
NARR = f"{ROOT}/audio/narration.wav"
MUSIC = f"{ROOT}/../music/track01_cosmic_ambient.mp3"
OUT = f"{ROOT}/whatifaholic_ep002_ai_job_v3.mp4"
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "csv=p=0", NARR]))
T_END = round(dur + 0.5, 2)
RED = (1.0, 0.32, 0.32)
DARK = (0.02, 0.04, 0.10)

IMG = {}
for n in "office_empty robot_desk meeting jobs_city pizza park band robot_quits".split():
    IMG[n], _ = L.surf(f"{A}/{n}.png", (1188, 2128))  # 1,1x o tamanho de cobertura (mais leve a escalar)

# ---------- palavras e âncoras ----------
words = json.load(open(f"{BLD}/words_ep002.json"))
FIX = {"thank": "thank-you", "AI.": "AI.", "round": "round."}
merged = []
for i, w in enumerate(words):
    if w["w"] == "you" and merged and merged[-1]["w"] == "thank-you":
        merged[-1]["e"] = w["e"]; continue
    w["w"] = FIX.get(w["w"], w["w"]); merged.append(dict(w))
words = merged


def clean(w):
    return re.sub(r"[^\w']", "", w).lower()


def at(phrase, after=0.0, end=False):
    toks = phrase.lower().split()
    cl = [clean(w["w"]) for w in words]
    for i in range(len(words) - len(toks) + 1):
        if words[i]["s"] >= after and all(cl[i + j] == toks[j] for j in range(len(toks))):
            return words[i + len(toks) - 1]["e"] if end else words[i]["s"]
    raise KeyError(phrase)


T = dict(hired=at("hired"), h1=at("hour one"), emails=at("emails"), boss=at("your boss"), written=at("written"),
         h3=at("hour three"), bug=at("bug"), report=at("report"), meeting=at("meeting"), itself=at("itself"),
         early=at("it ends early"), h8=at("hour eight"), pilots=at("pilots"), chefs=at("chefs"),
         lawyers=at("lawyers"), replaced=at("replaced"), pizza=at("your pizza"), four=at("four"),
         round=at("perfectly"), zero=at("zero"), h12=at("hour 12"), raise_=at("raise"), elec=at("electricity"),
         twist=at("and here's"), nojobs=at("with no jobs"), free=at("free"), gyms=at("gyms"), parks=at("parks"),
         neighbor=at("your neighbor"), unf=at("unfortunately"), h24=at("hour 24"), tired=at("tired"),
         quits=at("quits"), would=at("would you rather"), coworker=at("coworker"), tellme=at("tell me below"),
         because=at("because your job"))
ZERO = T["hired"]  # a contagem chega a zero em "hired": corte para o robô na cadeira
HOURS = [(T["h1"], 1), (T["h3"], 3), (T["h8"], 8), (T["h12"], 12), (T["h24"], 24)]


# ---------- cenas vivas: movimento dentro das ilustrações (vivo.py) ----------
import vivo as V
from vivo import S as VS
import random as _r
_r.seed(11)


def blink(t, period=3.1, ph=0.0):
    return ((t + ph) % period) < 0.13


def between(t, a, b):
    return a <= t < b


def white_fn(f):
    mx, mn = f.max(2), f.min(2)
    return (mx > 0.6) & ((mx - mn) / (mx + 1e-6) < 0.36) & (f[..., 2] >= f[..., 0] - 0.02)


# --- secretária (contratado, emails, nota, aumento, reviravolta)
def desk_state(t):
    if t < T["h1"]:
        return dict(kind="happy", look=(0, 0))
    if t < T["boss"]:
        return dict(kind="normal", look=(-0.7, 0.15), blink=blink(t))
    if t < T["written"]:
        return dict(kind="normal", look=(0, 0), blink=blink(t, 2.4))
    if t < T["h12"]:
        return dict(kind="happy", tilt=-4)
    if t < T["raise_"]:
        return dict(kind="normal", look=(0.2, 0), blink=blink(t))
    if t < T["elec"]:
        return dict(kind="wide", tilt=-6)
    return dict(kind="happy", tilt=-3)


DESK = V.LiveScene(f"{A}/robot_desk.png")
DESK.robot([(904, 1214), (999, 1214)], 30, 52, state=desk_state)
_body = DESK.color_mask((0.40, 0.49, 0.72, 0.585), white_fn)
_body &= ~DESK.robots[0].mask
_arm = _body.copy(); _arm[:, int(840 * VS):] = False
_tor = _body & ~_arm


def typing(t):
    return T["h1"] <= t < T["boss"] or T["h3"] - 1 <= t < T["h3"]


DESK.part(_tor, lambda t: (0, 3 * VS * math.sin(t * 2.2), 0, (0, 0)))
DESK.part(_arm, lambda t: (0, 1.5 * VS * math.sin(t * 2.2) - (4 * VS * abs(math.sin(t * 22)) if typing(t) else 0), 0, (0, 0)))
_CODE = [(_r.randint(1, 4), _r.uniform(0.25, 0.9), _r.choice([CYAN, (1, 1, 1), SUN])) for _ in range(60)]
_STARS = [(_r.uniform(200, 1330) * VS, _r.uniform(840, 1050) * VS, _r.uniform(2, 5), _r.random() * 6.28) for _ in range(26)]


def desk_fx(ctx, t):
    for x, y, r_, ph in _STARS:
        ctx.set_source_rgba(0.7, 0.95, 1, 0.3 + 0.7 * (0.5 + 0.5 * math.sin(t * 3 + ph))); ctx.arc(x, y, r_ * VS, 0, 6.283); ctx.fill()
    x, y, w, h = 372 * VS, 1222 * VS, 372 * VS, 205 * VS
    ctx.save(); ctx.rectangle(x, y, w, h); ctx.clip()
    ctx.set_source_rgba(0.02, 0.06, 0.16, 0.92); ctx.paint()
    speed = 160 if typing(t) else 40
    lh = 15 * VS
    for i, (ind, ln, col) in enumerate(_CODE):
        yy = y + 10 * VS + i * lh - (t * speed * VS) % (len(_CODE) * lh)
        if y - lh < yy < y + h:
            ctx.set_source_rgba(*col, 0.85); ctx.rectangle(x + 10 * VS + ind * 14 * VS, yy, (w - 40 * VS) * ln * 0.75, 6 * VS); ctx.fill()
    ctx.restore()
    V.steam(ctx, t, 412 * VS, 1530 * VS, 90 * VS)


DESK.fx_under.append(desk_fx)


# --- reunião consigo próprio
def meet_state(t):
    if t < T["itself"]:
        return dict(kind="normal", look=(math.sin(t * 1.6) * 0.8, 0), blink=blink(t, 2.7))
    if t < T["early"]:
        return dict(kind="happy", tilt=4)
    return dict(kind="wide", look=(0, 0))


MEET = V.LiveScene(f"{A}/meeting.png")
MEET.robot([(723, 1252), (760, 1245)], 13, 20, state=meet_state, sway=3, bob=2)


def meet_fx(ctx, t):
    x0, y0, x1, y1 = 0.53 * MEET.w, 0.375 * MEET.h, 0.665 * MEET.w, 0.452 * MEET.h
    ctx.set_source_rgba(0.03, 0.1, 0.25, 0.85); ctx.rectangle(x0, y0, x1 - x0, y1 - y0); ctx.fill()
    for i in range(6):
        k = seg(t, T["bug"] + i * 0.35, T["bug"] + i * 0.35 + 0.5)
        bh = (y1 - y0 - 14 * VS) * (0.25 + 0.12 * i) * k * (1 + 0.05 * math.sin(t * 4 + i))
        bw = (x1 - x0) / 8
        ctx.set_source_rgba(*(CYAN if i < 5 else SUN), 0.95)
        ctx.rectangle(x0 + bw * (0.8 + i * 1.15), y1 - 6 * VS - bh, bw * 0.8, bh); ctx.fill()


MEET.fx_under.append(meet_fx)


# --- pilotos, chefs, advogados
def job_state(name_t, ph):
    def f(t):
        if t >= T["replaced"]:
            return dict(kind="happy", dy=-4 * VS * abs(math.sin(t * 6 + ph)))
        if between(t, name_t, name_t + 0.7):
            return dict(kind="wide", tilt=-5)
        return dict(kind="normal", look=(0.4 * math.sin(t + ph), 0), blink=blink(t, 2.9, ph))
    return f


JOBS = V.LiveScene(f"{A}/jobs_city.png")
JOBS.robot([(790, 1233), (894, 1233)], 35, 57, state=job_state(T["chefs"], 0.7), sway=0.8, bob=1)
JOBS.robot([(974, 1873), (1107, 1874)], 44, 74, state=job_state(T["lawyers"], 1.9), sway=1.5, bob=2)
JOBS.robot([(393, 1945), (564, 1945)], 58, 98, state=job_state(T["pilots"], 0.0), sway=1.5, bob=2)
_plane = JOBS.color_mask((0.42, 0.065, 0.70, 0.145), lambda f: (f.max(2) > 0.72) & ((f.max(2) - f.min(2)) / (f.max(2) + 1e-6) < 0.3))
JOBS.parts.insert(0, V.Part(JOBS.img, _plane, lambda t: (-(t - T["h8"]) * 70 * VS, (t - T["h8"]) * 18 * VS, 0, (0, 0))))


def jobs_fx(ctx, t):
    V.steam(ctx, t, 0.665 * JOBS.w, 0.515 * JOBS.h, 110 * VS, n=3, spread=16, alpha=0.5)


JOBS.fx_over.append(jobs_fx)


# --- pizza perfeita
def pizza_state(t):
    if t < T["round"]:
        return dict(kind="normal", look=(0, 0.35), blink=blink(t, 2.5))
    if t < T["zero"]:
        return dict(kind="happy", tilt=-5)
    return dict(kind="flat", tilt=0)


PIZZA = V.LiveScene(f"{A}/pizza.png")
PIZZA.robot([(694, 1130), (842, 1130)], 43, 71, state=pizza_state, sway=2.5, bob=2)


def pizza_fx(ctx, t):
    for k in range(3):
        V.steam(ctx, t + k * 0.4, (0.40 + 0.09 * k) * PIZZA.w, 0.63 * PIZZA.h, 150 * VS, n=2, spread=14, alpha=0.4, width=6)


PIZZA.fx_over.append(pizza_fx)


# --- parque e ginásio cheios
PARK = V.LiveScene(f"{A}/park.png")
_LEAVES = [(_r.random(), _r.random(), _r.uniform(0.5, 1.5), _r.random() * 6.28) for _ in range(40)]


def park_fx(ctx, t):
    g = 0.5 + 0.5 * math.sin(t * 2)
    V_glow = cairo.RadialGradient(0.13 * PARK.w, 0.2 * PARK.h, 0, 0.13 * PARK.w, 0.2 * PARK.h, 260 * VS)
    V_glow.add_color_stop_rgba(0, 1, 0.9, 0.6, 0.35 + 0.2 * g); V_glow.add_color_stop_rgba(1, 1, 0.9, 0.6, 0)
    ctx.set_source(V_glow); ctx.paint()
    for i in range(5):  # pássaros
        x = ((t * 60 + i * 230) % (PARK.w + 200)) - 100
        y = 0.07 * PARK.h + 30 * i * VS + 10 * VS * math.sin(t * 2 + i)
        fl = 8 * VS * math.sin(t * 9 + i)
        ctx.set_source_rgba(0.1, 0.15, 0.3, 0.8); ctx.set_line_width(3 * VS)
        ctx.move_to(x - 14 * VS, y - fl); ctx.line_to(x, y); ctx.line_to(x + 14 * VS, y - fl); ctx.stroke()
    for x, y, sp, ph in _LEAVES:  # folhas a voar
        xx = (x * PARK.w + t * 40 * sp) % PARK.w
        yy = (y * PARK.h + t * 30 * sp) % PARK.h
        ctx.save(); ctx.translate(xx, yy); ctx.rotate(t * 2 * sp + ph); ctx.scale(9 * VS, 4 * VS)
        ctx.set_source_rgba(0.55, 0.8, 0.3, 0.8); ctx.arc(0, 0, 1, 0, 6.283); ctx.fill(); ctx.restore()


PARK.fx_over.append(park_fx)


# --- a banda do vizinho
BAND = V.LiveScene(f"{A}/band.png")
BEAT = 2.4  # batidas por segundo


def band_fx(ctx, t):
    b = max(0, math.sin(t * BEAT * math.pi)) ** 4
    gx, gy = 0.77 * BAND.w, 0.62 * BAND.h
    gl = cairo.RadialGradient(gx, gy, 0, gx, gy, 330 * VS)
    gl.add_color_stop_rgba(0, 1, 0.95, 0.75, 0.15 + 0.4 * b); gl.add_color_stop_rgba(1, 1, 0.95, 0.75, 0)
    ctx.set_source(gl); ctx.paint()
    sx, sy = 0.62 * BAND.w, 0.62 * BAND.h  # coluna a pulsar
    ctx.set_source_rgba(*CYAN, 0.5 * b); ctx.set_line_width(5 * VS)
    for k in range(3):
        ctx.arc(sx, sy, (30 + 22 * k + 25 * b) * VS, -1.2, 1.2); ctx.stroke()
    for i in range(10):  # notas a sair da garagem
        ph = ((t - T["neighbor"]) * 0.45 + i / 10) % 1
        x = 0.72 * BAND.w - ph * 0.6 * BAND.w + 30 * VS * math.sin(ph * 9 + i)
        y = 0.56 * BAND.h - ph * 0.3 * BAND.h
        V.note(ctx, x, y, (12 + 6 * (i % 3)) * VS, SUN if i % 2 else CYAN, math.sin(ph * math.pi))


BAND.fx_over.append(band_fx)


# --- a IA despede-se
def quit_state(t):
    step = -7 * VS * abs(math.sin(t * 4.2))
    if t < T["quits"]:
        return dict(kind="tired", blink=blink(t, 2.2), dy=step, tilt=3)
    return dict(kind="happy", dy=step, tilt=-3)


QUIT = V.LiveScene(f"{A}/robot_quits.png")
QUIT.robot([(910, 1215), (1018, 1215)], 60, 60, state=quit_state, sway=1.5, bob=0)
_qb = QUIT.color_mask((0.42, 0.47, 0.86, 0.82), lambda f: white_fn(f) | ((f[..., 0] > f[..., 2] + 0.12) & (f.max(2) > 0.35)))
_qb &= ~nd_dilate(QUIT.robots[0].mask)
QUIT.part(_qb, lambda t: (0, -7 * VS * abs(math.sin(t * 4.2)), 0, (0, 0)))

for _sc in (DESK, MEET, JOBS, PIZZA, PARK, BAND, QUIT):
    _sc.build()


def live(ctx, sc, t, t0, t1, z0, z1, focus=(0.5, 0.5)):
    V.live_cover(ctx, sc, t, t0, t1, z0, z1, W, H, focus, seg)


# ---------- utilitários de desenho ----------
def rr(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def extents(ctx, s, size):
    ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    return ctx.text_extents(s)[2]


def mono(ctx, s, x, y, size, col, a=1.0):
    """texto com dígitos em células fixas (o contador não treme)"""
    cw = size * 0.62
    widths = [cw * (0.45 if ch == ":" else 1) for ch in s]
    cx = x - sum(widths) / 2
    for ch, w_ in zip(s, widths):
        text(ctx, ch, cx + w_ / 2, y, size, col, a)
        cx += w_


def pop(t, t0, d=0.16):
    """escala de entrada: 1,5 -> 1 com assentamento"""
    x = (t - t0) / d
    if x <= 0:
        return 0
    return 1 + 0.5 * (1 - ease(min(x, 1)))


def tag(ctx, s, x, y, size, col, a, sc=1.0, bg=0.78):
    """etiqueta com fundo escuro arredondado, centrada em (x, y-baseline)"""
    if a <= 0.01:
        return
    tw = extents(ctx, s, size)
    ctx.save(); ctx.translate(x, y - size * 0.35); ctx.scale(sc, sc); ctx.translate(-x, -(y - size * 0.35))
    ctx.set_source_rgba(*DARK, bg * a); rr(ctx, x - tw / 2 - size * 0.55, y - size * 1.08, tw + size * 1.1, size * 1.45, size * 0.45)
    ctx.fill_preserve(); ctx.set_source_rgba(*col, 0.9 * a); ctx.set_line_width(3); ctx.stroke()
    text(ctx, s, x, y, size, col, a)
    ctx.restore()


def stamp(ctx, s, x, y, size, col, t, t0, rot=-0.07, t1=None):
    """carimbo: entra grande e assenta, com moldura"""
    sc = pop(t, t0)
    if sc <= 0:
        return
    a = min(1, (t - t0) / 0.08) * (1 - (seg(t, t1 - 0.2, t1) if t1 else 0))
    if a <= 0.01:
        return
    tw = extents(ctx, s, size)
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc)
    ctx.set_source_rgba(*DARK, 0.7 * a); rr(ctx, -tw / 2 - 34, -size * 0.95, tw + 68, size * 1.35, 18); ctx.fill()
    ctx.set_source_rgba(*col, a); ctx.set_line_width(7); rr(ctx, -tw / 2 - 34, -size * 0.95, tw + 68, size * 1.35, 18)
    ctx.stroke()
    text(ctx, s, 0, size * 0.05, size, col, a)
    ctx.restore()


def check(ctx, x, y, s, col, a):
    if a <= 0.01:
        return
    ctx.set_source_rgba(*col, a); ctx.set_line_width(s * 0.22); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(x - s * 0.45, y); ctx.line_to(x - s * 0.1, y + s * 0.35); ctx.line_to(x + s * 0.5, y - s * 0.4); ctx.stroke()


def envelope(ctx, x, y, w, a, ok):
    if a <= 0.01:
        return
    h = w * 0.66
    ctx.set_source_rgba(*CREAM, a); rr(ctx, x - w / 2, y - h / 2, w, h, 10); ctx.fill()
    ctx.set_source_rgba(0.35, 0.45, 0.6, a); ctx.set_line_width(5)
    ctx.move_to(x - w / 2 + 6, y - h / 2 + 8); ctx.line_to(x, y + 6); ctx.line_to(x + w / 2 - 6, y - h / 2 + 8); ctx.stroke()
    if ok > 0.01:
        ctx.set_source_rgba(*CYAN, a * ok); ctx.arc(x + w / 2, y - h / 2, 30 * ok, 0, 6.283); ctx.fill()
        check(ctx, x + w / 2, y - h / 2 + 2, 30, DARK, a * ok)


def bolt(ctx, x, y, s, col, a):
    if a <= 0.01:
        return
    p = [(0.15, -1), (-0.55, 0.12), (-0.05, 0.12), (-0.2, 1), (0.55, -0.15), (0.05, -0.15)]
    ctx.move_to(x + p[0][0] * s, y + p[0][1] * s)
    for px, py in p[1:]:
        ctx.line_to(x + px * s, y + py * s)
    ctx.close_path(); glow(ctx, x, y, s * 1.8, SUN, 0.35 * a)
    ctx.move_to(x + p[0][0] * s, y + p[0][1] * s)
    for px, py in p[1:]:
        ctx.line_to(x + px * s, y + py * s)
    ctx.close_path(); ctx.set_source_rgba(*SUN, a); ctx.fill()


def dim(ctx, a):
    ctx.set_source_rgba(0, 0, 0.02, a); ctx.paint()


# ---------- cenas ----------
Y_TAG = 520  # linha das etiquetas, por baixo do relógio e do selo


def countdown_text(ctx, t, a=1.0):
    x = min(1, max(0, (t - 0.3) / (ZERO - 0.3)))
    rem = 86400 * (1 - x ** 2.2)
    hh, r = divmod(int(rem), 3600); mm, ss = divmod(r, 60)
    sc = 1 + 0.05 * math.sin(t * 20) * (0.3 < t < ZERO)
    mono(ctx, f"{hh:02d}:{mm:02d}:{ss:02d}", 540, 600, 175 * sc, RED, a)
    text(ctx, "LEFT", 540, 690, 62, INK, a)


def s_hook(ctx, t):
    shake = 7 * seg(t, ZERO - 1.2, ZERO)
    ctx.save(); ctx.translate(shake * math.sin(t * 90), shake * math.cos(t * 77))
    paint_cover(ctx, IMG["office_empty"], t, 0, ZERO, 1.0, 1.06)
    ctx.restore()
    countdown_text(ctx, t)


def s_desk(ctx, t):
    live(ctx, DESK, t, ZERO, T["h3"], 1.32, 1.42, (0.47, 0.47))
    glow(ctx, W / 2, H / 2, 900, (1, 1, 1), 0.7 * max(0, 1 - (t - ZERO) / 0.25))  # flash do corte
    stamp(ctx, "HIRED", 540, Y_TAG + 40, 110, CYAN, t, ZERO, t1=T["h1"])
    # emails a responderem-se sozinhos
    e_out = 1 - seg(t, T["boss"] - 0.3, T["boss"])
    for i in range(4):
        t0 = T["emails"] + i * 0.28
        k = seg(t, t0, t0 + 0.2) * e_out
        ok = seg(t, T["emails"] + 0.9 + i * 0.12, T["emails"] + 1.05 + i * 0.12)
        envelope(ctx, 250 + i * 190, Y_TAG + 20 + 30 * math.sin(i * 1.7) - 18 * (1 - k), 130, k, ok)
    # nota de agradecimento do chefe ... escrita pela IA
    k = seg(t, T["boss"] + 0.1, T["boss"] + 0.3)
    if k > 0.01:
        y = Y_TAG + 60 + 40 * (1 - k)
        ctx.set_source_rgba(*CREAM, k); rr(ctx, 240, y - 120, 600, 230, 24); ctx.fill()
        text(ctx, "THANK YOU!", 540, y + 5, 84, CYAN, k)
        text(ctx, "- YOUR BOSS", 760, y + 75, 34, QUIET, k, "r", bold=False)
    stamp(ctx, "WRITTEN BY AI", 600, Y_TAG + 210, 64, CYAN, t, T["written"], rot=-0.12)


def s_meeting(ctx, t):
    live(ctx, MEET, t, T["h3"], T["h8"], 1.25, 1.4, (0.5, 0.45))
    rows = [("BUGS FIXED", T["bug"]), ("REPORTS DONE", T["report"]), ("MEETING BOOKED", T["meeting"])]
    for j, (lab, t0) in enumerate(rows):
        k = seg(t, t0, t0 + 0.18)
        if k <= 0.01:
            continue
        y = Y_TAG - 40 + j * 82
        ctx.set_source_rgba(*DARK, 0.75 * k); rr(ctx, 180, y - 52, 720, 72, 20); ctx.fill()
        ctx.set_source_rgba(*CYAN, k); ctx.set_line_width(4); rr(ctx, 205, y - 40, 48, 48, 10); ctx.stroke()
        check(ctx, 229, y - 16, 36, CYAN, seg(t, t0 + 0.12, t0 + 0.3))
        text(ctx, lab, 280, y, 50, INK, k, "l")
    stamp(ctx, "ATTENDEES: 1", 540, Y_TAG + 300, 70, SUN, t, T["itself"] + 0.1, rot=0.06)
    stamp(ctx, "ENDED EARLY", 560, Y_TAG + 470, 80, CYAN, t, T["early"] + 0.2, rot=-0.08)


def s_jobs(ctx, t):
    live(ctx, JOBS, t, T["h8"], T["pizza"], 1.0, 1.08)
    for j, (lab, t0) in enumerate([("PILOT", T["pilots"]), ("CHEF", T["chefs"]), ("LAWYER", T["lawyers"])]):
        x = 210 + j * 330
        tag(ctx, lab, x, Y_TAG, 54, INK, seg(t, t0, t0 + 0.1), pop(t, t0) or 1)
        s = seg(t, T["replaced"] + j * 0.06, T["replaced"] + 0.15 + j * 0.06)
        if s > 0:
            ctx.set_source_rgba(*RED, 1); ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(x - 120, Y_TAG - 18); ctx.line_to(x - 120 + 240 * s, Y_TAG - 18); ctx.stroke()
    stamp(ctx, "ALL REPLACED", 540, Y_TAG + 160, 84, RED, t, T["replaced"] + 0.2)


def s_pizza(ctx, t):
    live(ctx, PIZZA, t, T["pizza"], T["h12"], 1.18, 1.28, (0.5, 0.36))
    k = seg(t, T["four"], T["four"] + 0.15)
    sc = pop(t, T["four"]) or 1
    tag(ctx, "DELIVERED IN 4:00", 540, Y_TAG, 62, INK, k, sc)
    stamp(ctx, "PERSONALITY: 0%", 540, Y_TAG + 170, 72, SUN, t, T["zero"] + 0.1, rot=0.05)


def s_raise(ctx, t):
    live(ctx, DESK, t, T["h12"], T["twist"], 1.5, 1.62, (0.56, 0.47))
    k = seg(t, T["raise_"], T["raise_"] + 0.15)
    if k > 0.01:
        sc = pop(t, T["raise_"]) or 1
        ctx.save(); ctx.translate(640, 640); ctx.scale(sc, sc); ctx.translate(-640, -640)
        ctx.set_source_rgba(*CREAM, k); rr(ctx, 330, 560, 620, 150, 40); ctx.fill()
        ctx.move_to(720, 705); ctx.line_to(780, 790); ctx.line_to(800, 705); ctx.fill()
        text(ctx, "I WANT A RAISE.", 640, 660, 62, INK, k)
        ctx.restore()
    e = seg(t, T["elec"], T["elec"] + 0.15)
    bolt(ctx, 300, Y_TAG + 330, 90 * (pop(t, T["elec"]) or 1), SUN, e)
    stamp(ctx, "PAID IN kWh", 620, Y_TAG + 330, 76, SUN, t, T["elec"] + 0.05, rot=-0.05)


def s_twist(ctx, t):
    live(ctx, DESK, t, T["h12"], T["twist"], 1.62, 1.66, (0.56, 0.47))
    dim(ctx, 0.65 * seg(t, T["twist"], T["twist"] + 0.3))
    sc = pop(t, T["twist"] + 0.15, 0.22)
    if sc:
        ctx.save(); ctx.translate(540, 760); ctx.scale(sc, sc)
        glow(ctx, 0, -40, 420, SUN, 0.3)
        text(ctx, "THE TWIST", 0, 0, 150, SUN, 1)
        ctx.restore()


def s_park(ctx, t):
    live(ctx, PARK, t, T["nojobs"], T["neighbor"], 1.04, 1.12)
    tag(ctx, "FREE TIME: UNLIMITED", 540, Y_TAG, 58, CYAN, seg(t, T["free"], T["free"] + 0.12), pop(t, T["free"]) or 1)
    stamp(ctx, "GYMS: PACKED", 380, Y_TAG + 180, 64, SUN, t, T["gyms"], rot=-0.06)
    stamp(ctx, "PARKS: FULL", 700, Y_TAG + 330, 64, SUN, t, T["parks"], rot=0.06)


def s_band(ctx, t):
    sh = 9 * seg(t, T["neighbor"] + 0.4, T["neighbor"] + 1.0)
    ctx.save(); ctx.translate(sh * math.sin(t * 70), sh * math.cos(t * 83))
    live(ctx, BAND, t, T["neighbor"], T["h24"], 1.35 + 0.03 * max(0, math.sin(t * BEAT * math.pi)) ** 4, 1.45, (0.62, 0.5))
    ctx.restore()
    stamp(ctx, "VOLUME: 11", 540, Y_TAG + 40, 84, RED, t, T["unf"], rot=-0.06)


def s_quits(ctx, t):
    live(ctx, QUIT, t, T["h24"], T["would"], 1.22, 1.32, (0.6, 0.43))
    k = seg(t, T["tired"], T["tired"] + 0.15)
    if k > 0.01:  # bateria quase vazia
        x, y = 395, Y_TAG - 40
        ctx.set_source_rgba(*DARK, 0.75 * k); rr(ctx, x - 30, y - 55, 320, 100, 24); ctx.fill()
        ctx.set_source_rgba(*INK, k); ctx.set_line_width(5); rr(ctx, x, y - 30, 110, 54, 10); ctx.stroke()
        ctx.rectangle(x + 112, y - 12, 10, 18); ctx.fill()
        if (t * 3) % 1 < 0.6:
            ctx.set_source_rgba(*RED, k); ctx.rectangle(x + 8, y - 22, 16, 38); ctx.fill()
        text(ctx, "2%", x + 150, y + 16, 56, RED, k, "l")
    stamp(ctx, "I QUIT.", 540, Y_TAG + 230, 130, CYAN, t, T["quits"] + 0.05, rot=-0.08)


def s_poll(ctx, t):
    paint_cover(ctx, IMG["office_empty"], t, T["would"], T["because"], 1.1, 1.12)
    dim(ctx, 0.62)
    t0 = T["would"]
    for j, (lab, l1, l2, col, yy, tj) in enumerate([("A", "AN AI", "DOES YOUR JOB", CYAN, 560, T["would"]),
                                                     ("B", "ANNOYING", "COWORKER", SUN, 900, T["coworker"] - 0.5)]):
        k = seg(t, tj + 0.2, tj + 0.5)
        if k <= 0:
            continue
        x = 540 + (1 - k) * (600 if j else -600)
        ctx.set_source_rgba(*col, 0.14 * k); rr(ctx, x - 440, yy - 140, 880, 260, 34); ctx.fill()
        ctx.set_source_rgba(*col, 0.9 * k); ctx.set_line_width(4); rr(ctx, x - 440, yy - 140, 880, 260, 34); ctx.stroke()
        text(ctx, lab, x - 340, yy + 30, 120, col, k)
        text(ctx, l1, x + 60, yy - 10, 74, INK, k)
        text(ctx, l2, x + 60, yy + 55, 44, col, k)
    text(ctx, "VS", 540, 765, 64, QUIET, seg(t, T["coworker"] - 0.2, T["coworker"]))
    c = seg(t, T["tellme"], T["tellme"] + 0.2)
    text(ctx, "COMMENT  A  OR  B", 500, 1110, 60, CYAN, c)
    ax = 815 + 12 * math.sin(t * 8)
    if c > 0.01:
        ctx.set_source_rgba(*CYAN, c); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(ax, 1090); ctx.line_to(ax + 100, 1090); ctx.stroke()
        ctx.move_to(ax + 70, 1062); ctx.line_to(ax + 100, 1090); ctx.line_to(ax + 70, 1118); ctx.stroke()


def s_end(ctx, t):
    """volta ao frame 0: escritório vazio, zoom 1.0, contador 24:00:00 LEFT"""
    z = 1.1 - 0.1 * seg(t, T["because"], T_END - 0.35)
    paint_cover(ctx, IMG["office_empty"], 0, 0, 1, z, z)
    countdown_text(ctx, 0.0, seg(t, T["because"] + 0.3, T["because"] + 0.9))


SCENES = [(0, s_hook, "cut"), (ZERO, s_desk, "cut"), (T["h3"], s_meeting, "push"), (T["h8"], s_jobs, "zoom"),
          (T["pizza"], s_pizza, "push"), (T["h12"], s_raise, "circle"), (T["twist"], s_twist, "cut"),
          (T["nojobs"], s_park, "circle"), (T["neighbor"], s_band, "push"), (T["h24"], s_quits, "zoom"),
          (T["would"], s_poll, "circle"), (T["because"], s_end, "circle")]
SCENES = [(a, (SCENES[i + 1][0] if i + 1 < len(SCENES) else T_END + 1), fn, tr) for i, (a, fn, tr) in enumerate(SCENES)]

JOKES = [T["itself"], T["zero"], T["elec"], T["unf"], T["quits"]]
PUNCH = [ZERO, T["replaced"], T["four"], T["twist"] + 0.15] + JOKES
TRANS = 0.28


def punch(t):
    v = 0
    for p in PUNCH:
        x = t - p
        if 0 <= x < 0.45:
            v = max(v, math.sin(min(1, x / 0.08) * math.pi / 2) * (1 - x / 0.45))
    return 1 + 0.045 * v


def clock(ctx, t):
    """relógio fixo no topo: HOUR x + barra de progresso do dia"""
    a = seg(t, T["h1"] - 0.25, T["h1"]) * (1 - seg(t, T["would"] - 0.25, T["would"]))
    if a <= 0.01:
        return
    hr, t0 = 1, T["h1"]
    for th, h in HOURS:
        if t >= th:
            hr, t0 = h, th
    sc = pop(t, t0, 0.2) or 1
    x, y, w_, h_ = 540 - 160, 168, 320, 86
    ctx.save(); ctx.translate(540, y + h_ / 2); ctx.scale(sc, sc); ctx.translate(-540, -(y + h_ / 2))
    ctx.set_source_rgba(*DARK, 0.8 * a); rr(ctx, x, y, w_, h_, 26); ctx.fill()
    ctx.set_source_rgba(*CYAN, 0.9 * a); ctx.set_line_width(3); rr(ctx, x, y, w_, h_, 26); ctx.stroke()
    text(ctx, f"HOUR {hr}", 540, y + 61, 54, INK, a)
    ctx.restore()
    prev = 0
    for th, h in HOURS:
        if th < t0:
            prev = h
    frac = (prev + (hr - prev) * seg(t, t0, t0 + 0.5)) / 24
    ctx.set_source_rgba(1, 1, 1, 0.25 * a); rr(ctx, x + 20, y + h_ + 10, w_ - 40, 8, 4); ctx.fill()
    ctx.set_source_rgba(*CYAN, a); rr(ctx, x + 20, y + h_ + 10, max(8, (w_ - 40) * frac), 8, 4); ctx.fill()


def badge(ctx, t):
    """selo do loop aberto até 'here's the twist'"""
    a = seg(t, T["h1"] + 0.5, T["h1"] + 0.9) * (1 - seg(t, T["twist"] - 0.2, T["twist"]))
    if a <= 0.01:
        return
    w_, h_ = 600, 66; x, y = 540 - w_ / 2, 288
    ctx.set_source_rgba(*DARK, 0.75 * a); rr(ctx, x, y, w_, h_, 30); ctx.fill()
    ctx.set_source_rgba(*SUN, 0.9 * a); ctx.set_line_width(3); rr(ctx, x, y, w_, h_, 30); ctx.stroke()
    pulse = 0.5 + 0.5 * math.sin(t * 5)
    ctx.set_source_rgba(*SUN, a * (0.4 + 0.6 * pulse)); ctx.arc(x + 36, y + h_ / 2, 10, 0, 6.283); ctx.fill()
    text(ctx, "THE TWIST · COMING UP", x + 64, y + 45, 34, SUN, a, "l")


ALARM_P = 0.5


def alarm(ctx, t):
    """bordas vermelhas a piscar ao ritmo do alarme (0 no frame 0, para o loop bater certo)"""
    if t >= ZERO:
        return
    p = 0.5 - 0.5 * math.cos(2 * math.pi * t / ALARM_P)
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.62)
    g.add_color_stop_rgba(0, *RED, 0); g.add_color_stop_rgba(1, *RED, 0.62 * p)
    ctx.set_source(g); ctx.paint()
    ctx.set_source_rgba(*RED, 0.9 * p); ctx.set_line_width(18); ctx.rectangle(9, 9, W - 18, H - 18); ctx.stroke()


def render(fn, t):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_BEST)
    c.set_source_rgb(*NAVY); c.paint(); fn(c, t)
    return s


def frame(t, raw=False):
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(out)
    for i, (a, b, fn, tr) in enumerate(SCENES):
        if a <= t < b:
            cur = render(fn, t)
            x = (t - a) / TRANS
            if i > 0 and x < 1 and tr != "cut":
                prev = render(SCENES[i - 1][2], t)
                e = ease(x)
                if tr == "push":
                    ctx.set_source_surface(prev, -W * e, 0); ctx.paint()
                    ctx.set_source_surface(cur, W * (1 - e), 0); ctx.paint()
                elif tr == "zoom":
                    ctx.set_source_surface(prev, 0, 0); ctx.paint()
                    z = 1.25 - 0.25 * e
                    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2)
                    ctx.set_source_surface(cur, 0, 0); ctx.paint_with_alpha(e); ctx.restore()
                else:
                    ctx.set_source_surface(prev, 0, 0); ctx.paint()
                    ctx.save(); ctx.arc(W / 2, H / 2, 1150 * e, 0, 6.283); ctx.clip()
                    ctx.set_source_surface(cur, 0, 0); ctx.paint(); ctx.restore()
            else:
                ctx.set_source_surface(cur, 0, 0); ctx.paint()
            break
    alarm(ctx, t)
    clock(ctx, t)
    badge(ctx, t)
    z = punch(t)
    if z > 1.0005:
        fin = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c2 = cairo.Context(fin)
        c2.translate(W / 2, H / 2); c2.scale(z, z); c2.translate(-W / 2, -H / 2)
        c2.set_source_surface(out, 0, 0); c2.paint(); out = fin
    if raw:
        return out
    return np.ndarray((H, W, 4), np.uint8, out.get_data())[:, :, [2, 1, 0]].tobytes()


# ---------- legendas ----------
WEAK = {"a", "an", "the", "to", "of", "for", "on", "in", "it", "its", "and", "but", "with", "our", "their",
        "that", "is", "as", "be", "would", "could", "if", "about", "every", "no", "so", "here's", "because",
        "your", "or", "by", "his", "are", "has", "you"}


def bare(w):
    return re.sub(r"[^\w'.]", "", w).lower()


groups, cur = [], []
for w in words:
    cand = cur + [w]
    if cur and (len(cand) > 3 or len(" ".join(x["w"] for x in cand)) > 18):
        last = bare(cur[-1]["w"])
        if len(cur) > 1 and last in WEAK:
            carry = cur.pop(); groups.append(cur); cur = [carry, w]
        else:
            groups.append(cur); cur = [w]
    else:
        cur = cand
    if re.search(r"[.,?!]$", w["w"]):
        groups.append(cur); cur = []
if cur:
    groups.append(cur)


def ts(x):
    h, r = divmod(max(x, 0), 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


CY, WH = "&H00FFE03D&", "&H00FFFFFF&"
ev = []
for gi, g in enumerate(groups):
    g_end = min(groups[gi + 1][0]["s"], g[-1]["e"] + 0.5) if gi + 1 < len(groups) else T_END
    for k, w in enumerate(g):
        s = w["s"]; e = g[k + 1]["s"] if k + 1 < len(g) else g_end
        popt = "{\\fscx108\\fscy108\\t(0,90,\\fscx100\\fscy100)}" if k == 0 else ""
        txt = " ".join((f"{{\\c{CY}}}{x['w'].upper()}{{\\c{WH}}}" if j == k else x["w"].upper()) for j, x in enumerate(g))
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},Cap,,0,0,0,,{popt}{txt}")
ev += [f"Dialogue: 2,{ts(0)},{ts(T_END)},Mark,,0,0,0,,@whatifaholics"]
open(f"{BLD}/captions.ass", "w").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,90,90,560,1
Style: Mark,Inter Display,40,&H8CFFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,3,0,7,60,60,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n")

if __name__ == "__main__":
    if "--sheet" in sys.argv:  # folha de controlo de frames
        from PIL import Image
        times = [0, 2.0, ZERO + 0.3, T["written"] + 0.4, T["early"] + 0.6, T["replaced"] + 0.5, T["zero"] + 0.5,
                 T["elec"] + 0.5, T["twist"] + 0.6, T["parks"] + 0.5, T["unf"] + 0.5, T["quits"] + 0.5,
                 T["tellme"] + 0.4, T_END - 1 / FPS]
        cols = 7; tw_, th_ = 270, 480
        sheet = Image.new("RGB", (cols * tw_, 2 * th_))
        for i, tt in enumerate(times):
            s = frame(tt, raw=True)
            im = Image.frombuffer("RGBA", (W, H), bytes(s.get_data()), "raw", "BGRA", 0, 1).convert("RGB")
            sheet.paste(im.resize((tw_, th_)), ((i % cols) * tw_, (i // cols) * th_))
        sheet.save(sys.argv[sys.argv.index("--sheet") + 1]); print("sheet ok"); sys.exit()

    raw = f"{BLD}/raw.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                          "-pix_fmt", "yuv420p", raw], stdin=subprocess.PIPE)
    for i in range(int(T_END * FPS)):
        p.stdin.write(frame(i / FPS))
    p.stdin.close(); p.wait()

    def synth(name, expr, d):
        path = f"{BLD}/{name}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={d}", path], check=True)
        return path
    swish = f"{BLD}/swish.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.5:c=pink:a=0.5:r=48000",
                    "-af", "bandpass=f=900:w=1400,afade=t=in:d=0.25:curve=qsin,afade=t=out:st=0.25:d=0.25,volume=0.35",
                    swish], check=True)
    popw = synth("pop_soft", "0.5*sin(2*PI*(260+500*exp(-t*35))*t)*exp(-t*22)", 0.2)
    ding = synth("ding", "0.35*(sin(2*PI*1320*t)+0.5*sin(2*PI*1980*t))*exp(-t*9)", 0.6)
    events = [(swish, c - 0.25, 0.5) for c in (T["h3"], T["h8"], T["h12"], T["twist"], T["h24"], T["would"])]
    P = ALARM_P; h = P / 2
    env = f"min(1,mod(t,{h})*120)*min(1,({h}-mod(t,{h}))*120)"
    tone = f"(lt(mod(t,{P}),{h})*(sin(2*PI*960*t)+0.3*sin(2*PI*2880*t))+gte(mod(t,{P}),{h})*(sin(2*PI*770*t)+0.3*sin(2*PI*2310*t)))"
    alarm_wav = f"{BLD}/alarm.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"aevalsrc='0.45*{env}*{tone}':s=48000:d={ZERO:.3f}",
                    "-af", f"afade=t=out:st={max(0, ZERO - 0.06):.3f}:d=0.06", alarm_wav], check=True)
    events += [(alarm_wav, 0.0, 0.32)]
    boom = f"{BLD}/boom.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "aevalsrc='0.9*sin(2*PI*(48+70*exp(-t*6))*t)*exp(-t*2.8)':s=48000:d=1.6",
                    "-f", "lavfi", "-i", "anoisesrc=d=0.4:c=brown:a=0.8:r=48000",
                    "-filter_complex", "[1]afade=t=out:d=0.4,lowpass=f=900[n];[0][n]amix=inputs=2:normalize=0,volume=0.9",
                    boom], check=True)
    events += [(boom, ZERO - 0.02, 0.8)]
    events += [(popw, x, 0.5) for x in (T["h1"], T["four"])]
    events += [(ding, x + 0.15, 0.35) for x in JOKES]
    ins, ch, lab = [], [], []
    for n, (f, x, v) in enumerate(events):
        idx = 3 + n; ins += ["-i", f]; d = int(max(0, x) * 1000)
        ch.append(f"[{idx}:a]adelay={d}|{d},volume={v}[e{n}]"); lab.append(f"[e{n}]")
    sfx = ";".join(ch) + ";" + "".join(lab) + f"amix=inputs={len(lab)}:normalize=0[sfx]"
    pre = T["twist"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", NARR, "-stream_loop", "-1", "-i", MUSIC, *ins,
                    "-filter_complex",
                    f"[0:v]noise=alls=3:allf=t,subtitles={BLD}/captions.ass,format=yuv420p[v];"
                    "[1:a]asplit=2[n1][nk];"
                    f"[2:a]atrim=0:{T_END},volume='if(lt(t,{ZERO + 0.35:.2f}),0,if(between(t,{pre-0.6:.2f},{pre+0.1:.2f}),0.08,0.35))':eval=frame,"
                    f"afade=t=out:st={T_END-1.5}:d=1.5[m];"
                    "[m][nk]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[md];"
                    f"{sfx};[n1][md][sfx]amix=inputs=3:duration=longest:normalize=0,apad,"
                    f"loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{T_END}[a]",
                    "-map", "[v]", "-map", "[a]", "-t", str(T_END), "-r", str(FPS),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-maxrate", "8M", "-bufsize", "16M",
                    "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", OUT], check=True)
    print("OK", OUT, T_END)
