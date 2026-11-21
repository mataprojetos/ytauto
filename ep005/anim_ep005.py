#!/usr/bin/env python3
"""Whatifaholic EP005 — What If You Got $1 Every Time You Blinked?
Teste "só código": tudo desenhado em pycairo, sem imagens geradas. Único gasto: a voz (Bram).
Uso: python3 anim_ep005.py [--frames t1,t2,...]   (sem argumentos: render completo + mistura)"""
import math, random, re, json, subprocess, sys, os
import cairo
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{ROOT}/../lib")
from brand_scratch import draw_scratch  # noqa: E402

W, H, FPS = 1080, 1920, 30
BLD = f"{ROOT}/build"
NARR = f"{ROOT}/audio/narration.wav"
MUSIC = f"{ROOT}/../music/track01_cosmic_ambient.mp3"
SFX = f"{ROOT}/../lib/sfx"
OUT = f"{ROOT}/whatifaholic_ep005_blink.mp4"
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", NARR]))
T_END = round(DUR + 0.12, 2)
random.seed(5)

# ---------- cores (tema dinheiro: verdes + dourados) ----------
BG1 = (0.02, 0.17, 0.11); BG2 = (0.01, 0.07, 0.05)
GOLD = (1.0, 0.79, 0.18); GOLD2 = (1.0, 0.92, 0.55); MINT = (0.36, 1.0, 0.62)
BILL = (0.45, 0.78, 0.45); BILLD = (0.16, 0.42, 0.2)
INK = (1, 1, 1); DARK = (0.03, 0.05, 0.04); RED = (1.0, 0.27, 0.25); GREY = (0.55, 0.6, 0.58)
SKIN = (1.0, 0.8, 0.62); SKIND = (0.85, 0.58, 0.42)

# ---------- palavras ----------
raw = json.load(open(f"{BLD}/words.json"))
cough = json.load(open(f"{BLD}/cough_meta.json"))
C_AT = cough["cough_at_pre_tempo"] / 1.1; C_LEN = cough["cough_len"] / 1.1
words = []
for w in raw:
    if words and re.fullmatch(r",\d+\.?", w["w"]):
        words[-1]["w"] += w["w"]; words[-1]["e"] = w["e"]
    else:
        words.append(dict(w))
FIX = {"head": "head…", "head.": "head…", "bedtime,": "bedtime:", "year,": "year…", "Because": "because",
       "fifteen": "15", "So,": "So", "Black": "black"}
out = []
for i, w in enumerate(words):
    w["w"] = FIX.get(w["w"], w["w"])
    if w["w"] == "paid" and out and out[-1]["w"] == "Best":
        out[-1]["w"] = "Best-paid"; out[-1]["e"] = w["e"]; continue
    out.append(w)
words = out


def idx(tok, n=1):
    """índice da n.ª ocorrência da palavra (sem pontuação)"""
    k = 0
    for i, w in enumerate(words):
        if re.sub(r"[^\w$,]", "", w["w"]).lower().rstrip(",") == tok:
            k += 1
            if k == n: return i
    raise KeyError((tok, n))


# correções de tempo à volta da tosse e de "Free money" (o Whisper junta-os)
i_bl = idx("black"); i_of = i_bl - 1
words[i_of]["w"] = "of…"; words[i_of]["e"] = C_AT - 0.1
words[i_bl]["s"] = C_AT + C_LEN + 0.16
i_fr = idx("free")
if words[i_fr + 1]["s"] - words[i_fr]["s"] < 0.15:
    words[i_fr]["e"] = words[i_fr]["s"] + 0.2
    words[i_fr + 1]["s"] = words[i_fr]["e"]; words[i_fr + 1]["e"] = max(words[i_fr + 1]["e"], words[i_fr + 1]["s"] + 0.3)
i_and = idx("and")
if words[i_and + 1]["s"] - words[i_and]["s"] < 0.05:
    words[i_and]["e"] = words[i_and]["s"] + 0.1; words[i_and + 1]["s"] = words[i_and]["e"]
json.dump(words, open(f"{BLD}/words_final.json", "w"), indent=0)


def at(tok, n=1):
    return words[idx(tok, n)]["s"]


T = dict(
    you3=at("you", 3), rate=at("you", 4), fifteen=at("15"), brand=at("that"), because=at("because"),
    n900=at("$900"), hour=at("hour"), nothing=at("for"), lunch=at("by"), rent=at("your"),
    paid=at("paid"), bedtime=at("by", 2), n14=at("$14,400"), meeting=at("that", 2), best=at("bestpaid"),
    wait=at("but"), oneyear=at("after"), sleeping=at("sleeping"), zero=at("zero"), alarm=at("your", 4),
    boss=at("boss"), sneezing=at("sneezing"), eyes=at("eyes"), so=at("so"), snorting=at("snorting"),
    lineof=at("line"), black=words[i_bl]["s"], free=words[i_fr]["s"], andyear=words[i_and]["s"],
    big=at("$5,256,000"), blinkq=at("blink", 3), oneword=at("one", 5), loop=at("every", 3),
)
T["cough"] = C_AT
LOOP_START = T["loop"] - 0.08

# ---------- utilitários ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def seg(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= a)
def popin(t, a, d=0.22):
    """escala com overshoot (0 -> 1.12 -> 1)"""
    if t < a: return 0.0
    x = clamp((t - a) / d)
    return 1 + 0.25 * math.sin(math.pi * x) * (1 - x) if x < 1 else 1.0


def rr(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()


def text(c, s, x, y, size, col, a=1.0, align="c", outline=True, ow=0.13, ocol=DARK, scale=1.0, rot=0.0):
    if a <= 0.004 or scale <= 0.001: return
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(scale, scale)
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    c.set_font_size(size); e = c.text_extents(s)
    dx = {"c": -e.width / 2 - e.x_bearing, "l": -e.x_bearing, "r": -e.width - e.x_bearing}[align]
    dy = -e.height / 2 - e.y_bearing
    c.move_to(dx, dy); c.text_path(s)
    if outline:
        c.set_source_rgba(*ocol, a); c.set_line_width(size * ow); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke_preserve()
    c.set_source_rgba(*col, a); c.fill(); c.restore()


def glow(c, x, y, r, col, a):
    if a <= 0: return
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    c.set_source(g); c.arc(x, y, r, 0, 2 * math.pi); c.fill()


DOLLARS = [(random.uniform(0, W), random.uniform(0, H), random.uniform(30, 90), random.uniform(0.2, 0.8),
            random.uniform(0, 6.28)) for _ in range(26)]


def background(c, t, top=BG1, bot=BG2, signs=True, ga=0.35, gcol=MINT):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bot)
    c.set_source(g); c.paint()
    glow(c, W / 2, 820, 900, gcol, 0.12 * ga / 0.35)
    if signs:
        for (x, y, s, sp, ph) in DOLLARS:
            yy = (y - t * 40 * sp) % (H + 200) - 100
            text(c, "$", x + 20 * math.sin(t * sp + ph), yy, s, MINT, 0.07, outline=False)


def bill(c, x, y, w, rot=0.0, a=1.0):
    h = w * 0.46
    c.save(); c.translate(x, y); c.rotate(rot)
    c.set_source_rgba(*BILLD, a); rr(c, -w / 2, -h / 2, w, h, w * 0.05); c.fill()
    c.set_source_rgba(*BILL, a); rr(c, -w / 2 + w * 0.04, -h / 2 + w * 0.04, w * 0.92, h - w * 0.08, w * 0.03); c.fill()
    c.set_source_rgba(*BILLD, a); c.arc(0, 0, h * 0.3, 0, 2 * math.pi); c.fill()
    c.restore()
    text(c, "$", x, y, h * 0.42, BILL, a, outline=False, rot=rot)


def coin(c, x, y, r, a=1.0, spin=0.0):
    sx = max(0.15, abs(math.cos(spin)))
    c.save(); c.translate(x, y); c.scale(sx, 1)
    c.set_source_rgba(0.75, 0.52, 0.05, a); c.arc(0, 0, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(*GOLD, a); c.arc(0, 0, r * 0.84, 0, 2 * math.pi); c.fill()
    c.restore()
    if sx > 0.5: text(c, "$", x, y, r * 1.1, (0.75, 0.52, 0.05), a * (sx - 0.5) * 2, outline=False)


RAIN = [(random.uniform(-50, W + 50), random.uniform(0, 1), random.uniform(120, 220), random.uniform(0.6, 1.4),
         random.uniform(0, 6.28)) for _ in range(34)]


def bill_rain(c, t, t0, a=1.0, n=34, speed=1.0):
    for (x, y0, w, sp, ph) in RAIN[:n]:
        u = t - t0
        y = (y0 * (H + 400) + u * 700 * sp * speed) % (H + 400) - 200
        bill(c, x + 40 * math.sin(u * 2 + ph), y, w, 0.5 * math.sin(u * 1.7 * sp + ph), a * 0.9)


def blink_open(u, times, close=0.06, open_=0.1):
    o = 1.0
    for b in times:
        d = u - b
        if 0 <= d < close: o = min(o, 1 - d / close)
        elif close <= d < close + open_: o = min(o, (d - close) / open_)
    return smooth(o) if o < 1 else 1.0


def eye(c, x, y, r, o, dx=0.0, dy=0.0, a=1.0, iris=MINT, lashes=True):
    """olho estilizado: pupila com $; o = abertura 0..1"""
    o = max(o, 0.0)
    hu = 0.78 * r * o; hl = 0.62 * r * max(o, 0.0)
    def almond():
        c.move_to(x - r, y); c.curve_to(x - 0.45 * r, y - hu * 1.25, x + 0.45 * r, y - hu * 1.25, x + r, y)
        c.curve_to(x + 0.45 * r, y + hl * 1.25, x - 0.45 * r, y + hl * 1.25, x - r, y); c.close_path()
    glow(c, x, y, r * 1.6, GOLD, 0.18 * a)
    if o > 0.03:
        c.save(); almond(); c.clip()
        c.set_source_rgba(0.98, 0.98, 0.95, a); c.paint()
        ix, iy = x + dx * r, y + dy * r
        g = cairo.RadialGradient(ix, iy, 0, ix, iy, r * 0.46)
        g.add_color_stop_rgba(0, *GOLD2, a); g.add_color_stop_rgba(0.45, *iris, a); g.add_color_stop_rgba(1, 0.05, 0.4, 0.2, a)
        c.set_source(g); c.arc(ix, iy, r * 0.46, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(0.02, 0.05, 0.03, a); c.arc(ix, iy, r * 0.22, 0, 2 * math.pi); c.fill()
        text(c, "$", ix, iy, r * 0.32, GOLD, a, outline=False)
        c.set_source_rgba(1, 1, 1, 0.9 * a); c.arc(ix - r * 0.15, iy - r * 0.17, r * 0.08, 0, 2 * math.pi); c.fill()
        # pálpebra (sombra superior)
        c.set_source_rgba(0, 0, 0, 0.12 * a); c.rectangle(x - r, y - r, 2 * r, r * 0.25 + (1 - o) * r * 0.5); c.fill()
        c.restore()
    c.set_source_rgba(*DARK, a); c.set_line_width(r * 0.07); c.set_line_join(cairo.LINE_JOIN_ROUND)
    if o > 0.03:
        almond(); c.stroke()
    else:
        c.move_to(x - r, y); c.curve_to(x - 0.4 * r, y + 0.25 * r, x + 0.4 * r, y + 0.25 * r, x + r, y); c.stroke()
    if lashes:
        c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_width(r * 0.055)
        for k in range(7):
            s = (k + 1) / 8
            if o > 0.03:
                px = (1 - s) ** 3 * (x - r) + 3 * (1 - s) ** 2 * s * (x - 0.45 * r) + 3 * (1 - s) * s ** 2 * (x + 0.45 * r) + s ** 3 * (x + r)
                py = (1 - s) ** 3 * y + 3 * (1 - s) ** 2 * s * (y - hu * 1.25) + 3 * (1 - s) * s ** 2 * (y - hu * 1.25) + s ** 3 * y
                ang = -math.pi / 2 + (s - 0.5) * 1.6
                c.move_to(px, py); c.line_to(px + math.cos(ang) * r * 0.2, py + math.sin(ang) * r * 0.2 * (0.4 + 0.6 * o))
            else:
                px = x - r + 2 * r * s; py = y + 0.19 * r * math.sin(math.pi * s)
                ang = math.pi / 2 + (s - 0.5) * 1.2
                c.move_to(px, py); c.line_to(px + math.cos(ang) * r * 0.16, py + math.sin(ang) * r * 0.16)
        c.stroke()


def counter_box(c, s, x, y, size, col=GOLD, a=1.0, scale=1.0, box=True, bcol=(0, 0, 0)):
    if scale <= 0.001 or a <= 0.004: return
    if box:
        c.save(); c.translate(x, y); c.scale(scale, scale)
        c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
        e = c.text_extents(s); w = e.width + size * 0.7; h = size * 1.35
        c.set_source_rgba(*bcol, 0.55 * a); rr(c, -w / 2, -h / 2, w, h, h * 0.28); c.fill()
        c.set_source_rgba(*col, 0.9 * a); c.set_line_width(5); rr(c, -w / 2, -h / 2, w, h, h * 0.28); c.stroke()
        c.restore()
    text(c, s, x, y, size, col, a, scale=scale)


def money(v): return f"${int(round(v)):,}"


def check(c, x, y, s, col, a, k=1.0):
    c.save(); c.set_source_rgba(*col, a); c.set_line_width(s * 0.22); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.move_to(x - s * 0.5, y); c.line_to(x - s * 0.5 + s * 0.4 * min(1, k * 2), y + s * 0.4 * min(1, k * 2))
    if k > 0.5: c.line_to(x - s * 0.1 + s * 0.7 * (k - 0.5) * 2, y + s * 0.4 - s * 0.8 * (k - 0.5) * 2)
    c.stroke(); c.restore()


def clock_face(c, x, y, r, hh, mm, a=1.0, rim=GOLD):
    c.set_source_rgba(*rim, a); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.97, 0.97, 0.93, a); c.arc(x, y, r * 0.86, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(*DARK, a)
    for k in range(12):
        an = k * math.pi / 6; c.set_line_width(r * 0.05 if k % 3 == 0 else r * 0.025)
        c.move_to(x + math.sin(an) * r * 0.72, y - math.cos(an) * r * 0.72); c.line_to(x + math.sin(an) * r * 0.8, y - math.cos(an) * r * 0.8); c.stroke()
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    ah = (hh % 12 + mm / 60) * math.pi / 6; am = mm * math.pi / 30
    c.set_line_width(r * 0.08); c.move_to(x, y); c.line_to(x + math.sin(ah) * r * 0.45, y - math.cos(ah) * r * 0.45); c.stroke()
    c.set_line_width(r * 0.05); c.move_to(x, y); c.line_to(x + math.sin(am) * r * 0.68, y - math.cos(am) * r * 0.68); c.stroke()
    c.arc(x, y, r * 0.06, 0, 2 * math.pi); c.fill()


def head(c, x, y, r, a=1.0, eyes="open", mouth="flat", skin=SKIN, hair=(0.25, 0.16, 0.1), blink=1.0):
    c.set_source_rgba(*skin, a); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(*hair, a); c.arc(x, y - r * 0.05, r * 1.01, math.pi * 1.05, math.pi * 1.95); c.close_path(); c.fill()
    c.set_source_rgba(*DARK, a); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_width(r * 0.08)
    ex = r * 0.36; ey = y + r * 0.05
    for sx in (-1, 1):
        if eyes == "open" and blink > 0.2:
            c.save(); c.translate(x + sx * ex, ey); c.scale(1, blink); c.arc(0, 0, r * 0.11, 0, 2 * math.pi); c.restore(); c.fill()
        elif eyes == "bored":
            c.arc(x + sx * ex, ey + r * 0.03, r * 0.1, 0, math.pi); c.fill()
            c.move_to(x + sx * ex - r * 0.14, ey); c.line_to(x + sx * ex + r * 0.14, ey); c.stroke()
        elif eyes == "squint":
            c.move_to(x + sx * ex - r * 0.15, ey - r * 0.08); c.line_to(x + sx * ex + r * 0.02 * sx, ey); c.line_to(x + sx * ex - r * 0.15, ey + r * 0.08)
            c.stroke() if sx < 0 else None
            if sx > 0:
                c.move_to(x + sx * ex + r * 0.15, ey - r * 0.08); c.line_to(x + sx * ex - r * 0.02, ey); c.line_to(x + sx * ex + r * 0.15, ey + r * 0.08); c.stroke()
        else:  # closed / side
            c.move_to(x + sx * ex - r * 0.13, ey); c.curve_to(x + sx * ex - r * 0.05, ey + r * 0.08, x + sx * ex + r * 0.05, ey + r * 0.08, x + sx * ex + r * 0.13, ey); c.stroke()
    my = y + r * 0.5
    if mouth == "flat":
        c.move_to(x - r * 0.2, my); c.line_to(x + r * 0.2, my); c.stroke()
    elif mouth == "o":
        c.arc(x, my, r * 0.16, 0, 2 * math.pi); c.fill()
    elif mouth == "smile":
        c.arc(x, my - r * 0.12, r * 0.25, 0.15 * math.pi, 0.85 * math.pi); c.stroke()
    elif mouth == "smirk":
        c.move_to(x - r * 0.2, my); c.curve_to(x, my + r * 0.05, x + r * 0.15, my, x + r * 0.25, my - r * 0.1); c.stroke()


def burst(c, x, y, r, col, a, n=12, rot=0.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.set_source_rgba(*col, a)
    for k in range(2 * n):
        an = k * math.pi / n; rr_ = r if k % 2 == 0 else r * 0.68
        (c.move_to if k == 0 else c.line_to)(math.cos(an) * rr_, math.sin(an) * rr_)
    c.close_path(); c.fill(); c.restore()


def floaters(c, t, items, col=MINT, size=70):
    """'+$1' que sobem e desaparecem: items = lista de (t0, x, y)"""
    for (t0, x, y) in items:
        u = t - t0
        if 0 <= u < 0.9:
            text(c, "+$1", x, y - 160 * ease(u / 0.9), size, col, 1 - clamp((u - 0.5) / 0.4), scale=popin(t, t0, 0.15))


# ---------- cenas ----------
HOOK_BLINKS = [0.10, 0.40, 0.72]
COINS = [(random.uniform(80, W - 80), random.uniform(250, 1500), random.uniform(28, 46), random.uniform(0, 6.28)) for _ in range(14)]


def s_hook(c, t, u=None):
    """gancho (também o fim do loop, com u negativo): olho a piscar, $1 PER BLINK, contador"""
    if u is None: u = t
    background(c, u, ga=0.5)
    for (x, y, r, ph) in COINS:
        coin(c, x + 14 * math.sin(u * 1.3 + ph), y + 22 * math.sin(u * 1.1 + ph), r, 0.55, spin=u * 2.5 + ph)
    o = blink_open(u, HOOK_BLINKS)
    eye(c, 540, 860, 330, o, dx=0.08 * math.sin(u * 1.7), dy=0.04 * math.sin(u * 2.3))
    n = sum(1 for b in HOOK_BLINKS if u >= b + 0.06)
    last = max([b + 0.06 for b in HOOK_BLINKS if u >= b + 0.06], default=-9)
    wob = 1 + 0.03 * math.sin(u * 7)
    text(c, "$1 PER BLINK", 540, 360, 128, GOLD, 1.0, scale=wob, ow=0.16)
    sc = 1 + 0.35 * math.exp(-(u - last) * 9) if u >= last else 1
    counter_box(c, f"${n}", 540, 1290 - 40, 150, MINT if n else INK, 1.0, scale=sc)
    # moedas a saltar do olho para o contador
    for b in HOOK_BLINKS:
        d = u - b - 0.06
        if 0 <= d < 0.45:
            k = ease(d / 0.45)
            coin(c, 540 + 260 * math.sin(b * 9) * (1 - k), 860 + (1250 - 860) * k - 260 * math.sin(math.pi * k), 46, 1 - k * 0.3, spin=d * 20)
            glow(c, 540, 860, 420, GOLD2, 0.5 * (1 - d / 0.45))


def s_rate(c, t):
    t0 = T["rate"]; u = t - t0
    background(c, t)
    cx, cy, R = 540, 820, 330
    p = clamp(u / 1.9)
    c.set_source_rgba(1, 1, 1, 0.12); c.set_line_width(26); c.arc(cx, cy, R, 0, 2 * math.pi); c.stroke()
    c.set_source_rgba(*GOLD, 1); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.arc(cx, cy, R, -math.pi / 2, -math.pi / 2 + 2 * math.pi * p); c.stroke()
    shown = int(clamp((t - T["fifteen"] + 0.35) / 1.2) * 15)
    for k in range(15):
        an = -math.pi / 2 + k * 2 * math.pi / 15
        ex, ey = cx + math.cos(an) * (R + 0), cy + math.sin(an) * (R + 0)
        if k < shown:
            s = popin(t, T["fifteen"] - 0.35 + k * 0.08, 0.16)
            c.save(); c.translate(ex, ey); c.scale(s, s)
            eye(c, 0, 0, 44, blink_open(u, [0.3 + k * 0.11]), lashes=False)
            c.restore()
    num = int(clamp((t - T["fifteen"] + 0.1) / 0.45) * 15)
    text(c, f"{num}", cx, cy - 30, 300, GOLD, seg(t, T["fifteen"] - 0.25, T["fifteen"]), scale=popin(t, T["fifteen"] - 0.2, 0.25))
    text(c, "BLINKS / MIN", cx, cy + 150, 64, INK, seg(t, T["fifteen"], T["fifteen"] + 0.2))
    text(c, "BLINKS ADD UP...", 540, 330, 80, MINT, seg(t, t0, t0 + 0.2) * (1 - seg(t, T["fifteen"] - 0.1, T["fifteen"] + 0.1)))
    text(c, "AVERAGE HUMAN", 540, 330, 80, MINT, seg(t, T["fifteen"] + 0.05, T["fifteen"] + 0.25))


def s_brand(c, t):
    u = t - T["brand"]
    background(c, t, top=(0.05, 0.2, 0.14), ga=0.5, gcol=GOLD)
    draw_scratch(c, u, 540, 700, 1.0, skin=SKIN, accent=GOLD, ink=INK)


def s_900(c, t):
    t0 = T["because"]
    background(c, t)
    a_rain = seg(t, T["n900"] - 0.1, T["n900"] + 0.3)
    if a_rain > 0: bill_rain(c, t, T["n900"], a_rain * 0.75)
    # 15 x 60
    eq_a = seg(t, t0, t0 + 0.15) * (1 - seg(t, T["n900"] - 0.1, T["n900"] + 0.1))
    text(c, "15 × 60 MIN", 540, 760, 130, INK, eq_a, scale=popin(t, t0, 0.2))
    text(c, "= ?", 540, 920, 130, GOLD, eq_a * seg(t, t0 + 0.4, t0 + 0.6))
    v = 900 * clamp((t - T["n900"]) / 0.55)
    if t >= T["n900"] - 0.05:
        sh = 6 * math.exp(-(t - T["n900"]) * 4) * math.sin(t * 80)
        y_num = 700 - 160 * seg(t, T["nothing"] - 0.1, T["nothing"] + 0.2)
        counter_box(c, money(v), 540 + sh, y_num, 210, GOLD, 1.0, scale=popin(t, T["n900"] - 0.05, 0.25))
        text(c, "PER HOUR", 540, y_num + 200, 90, INK, seg(t, T["hour"] - 0.1, T["hour"] + 0.1), scale=popin(t, T["hour"] - 0.1))
    # sofá: "for doing nothing"
    k = seg(t, T["nothing"] - 0.1, T["nothing"] + 0.25)
    if k > 0:
        y0 = 1080 + 500 * (1 - k)
        c.set_source_rgba(0.55, 0.22, 0.2, 1); rr(c, 250, y0, 580, 150, 40); c.fill()
        c.set_source_rgba(0.68, 0.3, 0.26, 1); rr(c, 200, y0 - 40, 110, 210, 40); c.fill(); rr(c, 770, y0 - 40, 110, 210, 40); c.fill()
        c.set_source_rgba(0.68, 0.3, 0.26, 1); rr(c, 300, y0 - 90, 480, 110, 40); c.fill()
        # pessoa deitada
        c.set_source_rgba(0.25, 0.45, 0.85, 1); rr(c, 380, y0 - 30, 330, 80, 40); c.fill()
        head(c, 340, y0 - 5, 62, 1, eyes="closed", mouth="smile")
        text(c, "z", 300 + 30 * math.sin(t * 3), y0 - 110 - 40 * ((t * 1.2) % 1), 60, INK, 0.8, outline=False)
        text(c, "FOR DOING NOTHING", 540, y0 + 230, 76, MINT, k)


def house(c, x, y, s, a=1.0):
    c.set_source_rgba(0.95, 0.9, 0.8, a); c.rectangle(x - 170 * s, y - 120 * s, 340 * s, 240 * s); c.fill()
    c.set_source_rgba(0.75, 0.25, 0.2, a)
    c.move_to(x - 210 * s, y - 110 * s); c.line_to(x, y - 290 * s); c.line_to(x + 210 * s, y - 110 * s); c.close_path(); c.fill()
    c.set_source_rgba(0.4, 0.25, 0.15, a); rr(c, x - 40 * s, y - 10 * s, 80 * s, 130 * s, 10 * s); c.fill()
    c.set_source_rgba(0.55, 0.8, 1.0, a)
    for dx in (-115, 115): rr(c, x + (dx - 40) * s, y - 70 * s, 80 * s, 70 * s, 8 * s); c.fill()


def s_rent(c, t):
    t0 = T["lunch"]
    background(c, t, top=(0.06, 0.24, 0.16))
    k = seg(t, t0, t0 + 0.5)
    hh = 7 + 5 * k
    clock_face(c, 540, 470, 150 * popin(t, t0 - 0.05, 0.2), int(hh), (hh % 1) * 60)
    text(c, "12:00 · LUNCH", 540, 680, 70, INK, seg(t, t0 + 0.2, t0 + 0.4))
    hk = seg(t, T["rent"] - 0.15, T["rent"] + 0.15)
    if hk > 0:
        house(c, 540, 1080 - 300 * (1 - hk) * 0, 1.15 * popin(t, T["rent"] - 0.15, 0.25), 1.0)
    sk = clamp((t - T["paid"] + 0.05) / 0.18)
    if sk > 0:
        s = 1 + 1.4 * (1 - ease(sk))
        c.save(); c.translate(540, 1000); c.rotate(-0.12); c.scale(s, s)
        c.set_source_rgba(0.08, 0.6, 0.3, 0.92 * ease(sk)); rr(c, -330, -80, 660, 160, 26); c.fill()
        c.set_source_rgba(1, 1, 1, ease(sk)); c.set_line_width(8); rr(c, -318, -68, 636, 136, 20); c.stroke()
        c.restore()
        text(c, "RENT PAID", 500, 1000 + 20, 100, INK, ease(sk), outline=False, scale=s, rot=-0.12)
        check(c, 810, 950, 70, INK, ease(sk), clamp((t - T["paid"] - 0.1) / 0.2))


def s_bed(c, t):
    t0 = T["bedtime"]
    background(c, t, top=(0.04, 0.1, 0.16), bot=(0.01, 0.04, 0.06), gcol=GOLD)
    k = seg(t, t0, t0 + 0.25)
    glow(c, 820, 360, 220, GOLD2, 0.35 * k)
    c.set_source_rgba(*GOLD2, k); c.arc(820, 360, 90, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.04, 0.1, 0.16, k); c.arc(860, 330, 82, 0, 2 * math.pi); c.fill()
    text(c, "BEDTIME", 300, 360, 80, INK, k)
    # pilha de notas a crescer
    v = 14400 * clamp((t - t0 - 0.1) / (T["n14"] + 0.6 - t0 - 0.1)) ** 1.5
    n = int(v / 600)
    for i in range(n):
        bill(c, 540 + 8 * math.sin(i * 1.7), 1280 - i * 15, 360, 0.04 * math.sin(i * 2.3), 1)
    counter_box(c, money(v), 540, 640, 190, GOLD, seg(t, t0 + 0.05, t0 + 0.25), scale=popin(t, T["n14"] - 0.1, 0.25) if t >= T["n14"] - 0.1 else 1.0)
    text(c, "16 AWAKE HOURS × $900", 540, 810, 52, MINT, seg(t, T["n14"] + 0.3, T["n14"] + 0.5))


def s_meeting(c, t):
    t0 = T["meeting"]; u = t - t0
    background(c, t, top=(0.18, 0.22, 0.2), bot=(0.08, 0.1, 0.09), signs=False, ga=0.2)
    # parede: ecrã com gráfico chato
    c.set_source_rgba(0.92, 0.93, 0.9, 1); rr(c, 120, 520, 520, 320, 14); c.fill()
    text(c, "Q3 SYNERGY", 380, 570, 44, (0.3, 0.3, 0.3), 1, outline=False)
    c.set_source_rgba(0.6, 0.65, 0.7, 1)
    for i, hgt in enumerate((60, 110, 80, 140, 100)):
        c.rectangle(170 + i * 90, 800 - hgt, 60, hgt); c.fill()
    # relógio de parede a girar
    spin = u * 60
    clock_face(c, 840, 640, 150, spin / 60, spin % 60)
    # mesa e pessoas aborrecidas
    for i, x in enumerate((250, 540, 830)):
        bl = blink_open(u, [0.4 + i * 0.3, 1.1 + i * 0.35, 1.9 + i * 0.25])
        c.set_source_rgba(*((0.3, 0.4, 0.7), (0.6, 0.3, 0.35), (0.3, 0.55, 0.4))[i], 1); rr(c, x - 110, 1000, 220, 200, 60); c.fill()
        head(c, x, 950, 85, 1, eyes="bored" if bl > 0.5 else "closed", mouth="flat",
             skin=(SKIN, (0.78, 0.55, 0.4), (0.95, 0.75, 0.6))[i])
    for i, x in enumerate((250, 540, 830)):
        for b in (0.4 + i * 0.3, 1.1 + i * 0.35, 1.9 + i * 0.25):
            d = u - b
            if 0 <= d < 0.7: text(c, "+$1", x, 840 - 120 * ease(d / 0.7), 54, GOLD, 1 - clamp((d - 0.4) / 0.3))
    c.set_source_rgba(0.45, 0.3, 0.2, 1); c.rectangle(0, 1130, W, 60); c.fill()
    text(c, "BORING MONDAY MEETING", 540, 380, 72, INK, seg(t, t0, t0 + 0.2) * (1 - seg(t, T["best"] - 0.1, T["best"] + 0.05)))
    # contador a disparar
    v = 900 * clamp(u / 2.6) + 37 * math.sin(u * 13) ** 2
    counter_box(c, money(v), 540, 1300 - 60, 110, GOLD, 1)
    bk = seg(t, T["best"] - 0.05, T["best"] + 0.15)
    if bk > 0:
        c.save(); c.translate(540, 390); c.rotate(-0.05)
        c.set_source_rgba(*GOLD, bk); rr(c, -470, -95, 940, 190, 30); c.fill(); c.restore()
        text(c, "BEST-PAID HOUR", 540, 360, 92, DARK, bk, outline=False, rot=-0.05, scale=popin(t, T["best"] - 0.05))
        text(c, "OF YOUR LIFE", 540, 440, 60, DARK, bk, outline=False, rot=-0.05)


def s_tease(c, t):
    t0 = T["wait"]; u = t - t0
    background(c, t, ga=0.5, gcol=GOLD)
    # cofre com número escondido
    k = popin(t, t0, 0.25)
    c.save(); c.translate(540, 840); c.scale(k, k)
    c.set_source_rgba(0.35, 0.38, 0.4, 1); rr(c, -340, -300, 680, 600, 40); c.fill()
    c.set_source_rgba(0.22, 0.24, 0.26, 1); rr(c, -300, -260, 600, 520, 30); c.fill()
    c.set_source_rgba(0.5, 0.54, 0.56, 1); c.arc(0, 40, 140, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.22, 0.24, 0.26, 1); c.set_line_width(14)
    for j in range(6):
        an = j * math.pi / 3 + u * 2.5
        c.move_to(0, 40); c.line_to(math.cos(an) * 120, 40 + math.sin(an) * 120); c.stroke()
    c.restore()
    rnd = random.Random(int(t * 12))
    scr = "$" + ",".join(["".join(rnd.choice("0123456789?") for _ in range(3)) for _ in range(2)])
    scr = "$?," + scr[1:]
    counter_box(c, scr, 540, 560 - 20, 120, GOLD, k * 0.95)
    # calendário 365
    ck = seg(t, T["oneyear"] - 0.1, T["oneyear"] + 0.2)
    if ck > 0:
        c.save(); c.translate(540, 1210); c.rotate(0.06); c.scale(ck, ck)
        c.set_source_rgba(1, 1, 1, 1); rr(c, -160, -120, 320, 250, 20); c.fill()
        c.set_source_rgba(*RED, 1); rr(c, -160, -120, 320, 70, 20); c.fill(); c.rectangle(-160, -80, 320, 30); c.fill()
        c.restore()
        text(c, "1 YEAR", 540, 1112, 46, INK, ck, outline=False, rot=0.06)
        text(c, "365", 545, 1240, 110, DARK, ck, outline=False, rot=0.06)
    text(c, "WAIT FOR IT...", 540, 330, 84, MINT, seg(t, t0, t0 + 0.2))


def s_sleep(c, t):
    t0 = T["sleeping"]; u = t - t0
    background(c, t, top=(0.05, 0.07, 0.15), bot=(0.02, 0.02, 0.06), signs=False, ga=0.15)
    # cama
    c.set_source_rgba(0.45, 0.3, 0.2, 1); rr(c, 140, 900, 80, 380, 20); c.fill(); rr(c, 860, 1000, 80, 280, 20); c.fill()
    c.set_source_rgba(0.95, 0.95, 0.98, 1); rr(c, 200, 960, 220, 100, 40); c.fill()
    head(c, 320, 940, 80, 1, eyes="closed", mouth="o")
    c.set_source_rgba(0.35, 0.45, 0.85, 1); rr(c, 200, 1010, 700, 150, 50); c.fill()
    c.set_source_rgba(0.3, 0.38, 0.75, 1); rr(c, 160, 1140, 760, 70, 20); c.fill()
    for i in range(3):
        ph = (u * 0.8 + i / 3) % 1
        text(c, "Z", 420 + 120 * ph + i * 10, 860 - 240 * ph, 60 + 50 * ph, INK, 0.9 * (1 - ph), outline=False)
    # contador parado
    a = seg(t, t0, t0 + 0.2)
    counter_box(c, "0 $/h", 540, 480, 170, GREY, a, bcol=(0.1, 0, 0))
    c.set_source_rgba(*GREY, a); c.set_line_width(6)
    c.move_to(240, 650); c.line_to(840, 650); c.stroke()  # linha plana (sem rendimento)
    text(c, "8 HOURS", 540, 740, 70, INK, seg(t, T["sleeping"] + 0.4, T["sleeping"] + 0.6))
    zk = seg(t, T["zero"] - 0.05, T["zero"] + 0.1)
    if zk > 0:
        text(c, "ZERO INCOME", 540, 330, 96, RED, zk, scale=popin(t, T["zero"] - 0.05))


def alarm_clock(c, x, y, s, t, a=1.0, ring=True):
    sh = 10 * math.sin(t * 60) if ring else 0
    c.save(); c.translate(x + sh, y); c.scale(s, s); c.rotate(0.06 * math.sin(t * 60) if ring else 0)
    c.set_source_rgba(*GOLD, a)
    for sx in (-1, 1):
        c.arc(sx * 150, -200, 70, math.pi, 2 * math.pi); c.fill()
    c.set_source_rgba(0.85, 0.15, 0.15, a); c.arc(0, 0, 250, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(*DARK, a); c.set_line_width(20)
    for sx in (-1, 1): c.move_to(sx * 150, 220); c.line_to(sx * 200, 300); c.stroke()
    c.restore()
    clock_face(c, x + sh, y, 210 * s, 6, 30 - 30 * 0, a, rim=(0.85, 0.15, 0.15))
    # sobrancelhas zangadas
    c.save(); c.translate(x + sh, y); c.scale(s, s)
    c.set_source_rgba(*DARK, a); c.set_line_width(22); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(-120, -80); c.line_to(-40, -40); c.stroke(); c.move_to(120, -80); c.line_to(40, -40); c.stroke()
    # gravata
    c.set_source_rgba(0.15, 0.25, 0.75, a)
    c.move_to(-36, 250); c.line_to(36, 250); c.line_to(20, 290); c.close_path(); c.fill()
    c.move_to(-20, 285); c.line_to(20, 285); c.line_to(45, 470); c.line_to(0, 520); c.line_to(-45, 470); c.close_path(); c.fill()
    c.restore()
    if ring:
        for k in range(3):
            q = (t * 3 + k / 3) % 1
            c.set_source_rgba(*GOLD2, (1 - q) * a); c.set_line_width(8)
            c.arc(x, y - 30, 280 * s + 120 * q, -2.6, -0.5); c.stroke()


def s_boss(c, t):
    t0 = T["alarm"]
    background(c, t, top=(0.16, 0.08, 0.06), bot=(0.05, 0.02, 0.02), signs=False, gcol=RED, ga=0.3)
    alarm_clock(c, 540, 850, 1.0 * popin(t, t0, 0.2), t)
    bk = seg(t, T["boss"] - 0.25, T["boss"])
    text(c, "YOUR NEW BOSS", 540, 330, 104, GOLD, bk, scale=popin(t, T["boss"] - 0.25))
    text(c, "6:30 AM. NO SNOOZE.", 540, 1330 - 60, 60, INK, seg(t, t0 + 0.4, t0 + 0.6))


PEP = [(random.uniform(-1, 1), random.uniform(0, 1), random.uniform(3, 9), random.uniform(0.5, 1.5)) for _ in range(260)]


def shaker(c, x, y, s, rot, a=1.0, label=True):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.set_source_rgba(0.6, 0.62, 0.64, a); rr(c, -80, -170, 160, 70, 30); c.fill()
    c.set_source_rgba(0.2, 0.2, 0.2, a)
    for i in range(-2, 3):
        for j in range(2): c.arc(i * 26, -150 + j * 24, 5, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.93, 0.93, 0.95, 0.95 * a); rr(c, -90, -110, 180, 290, 40); c.fill()
    c.set_source_rgba(0.12, 0.12, 0.12, a); rr(c, -80, 0, 160, 170, 30); c.fill()   # pimenta lá dentro
    c.restore()
    if label: text(c, "PEPPER", x, y + 30 * s, 34 * s, INK, a, rot=rot)


def s_sneeze(c, t):
    t0 = T["sneezing"]; u = t - t0
    background(c, t, top=(0.06, 0.22, 0.15))
    sneezes = [t0 + 0.15, T["eyes"] + 0.35, T["eyes"] + 1.0]
    face(c, t, sneezes, 540, 900, 300)
    text(c, "EYES CLOSED = +$1", 540, 1330 - 70, 70, GOLD, seg(t, T["eyes"], T["eyes"] + 0.2))
    floaters(c, t, [(s + 0.05, 540 + 230 * (1 if i % 2 else -1), 560) for i, s in enumerate(sneezes)], GOLD, 90)


def face(c, t, sneezes, x, y, r, extra_eyes=None):
    """rosto grande: antes do espirro inspira (olhos semicerrados), no espirro fecha os olhos + ATCHOO"""
    state = "open"; dx = dy = 0.0
    for s in sneezes:
        if s - 0.35 <= t < s: state = "pre"
        elif s <= t < s + 0.3: state = "sneeze"; dx = 14 * math.sin(t * 70); dy = 26 * math.exp(-(t - s) * 8)
    if extra_eyes: state = extra_eyes
    if state == "cough":
        dx = 10 * math.sin(t * 55); dy = -14 * abs(math.sin(t * 18))
    c.save(); c.translate(dx, dy)
    c.set_source_rgba(*SKIN, 1); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.25, 0.16, 0.1, 1); c.arc(x, y - r * 0.08, r * 1.01, math.pi * 1.08, math.pi * 1.92); c.close_path(); c.fill()
    c.set_source_rgba(*SKIND, 1); c.arc(x, y + r * 0.18, r * 0.12, 0, 2 * math.pi); c.fill()  # nariz
    if state == "sneeze":
        c.set_source_rgba(1, 0.4, 0.4, 0.5); c.arc(x, y + r * 0.18, r * 0.12, 0, 2 * math.pi); c.fill()
    ex = r * 0.38; ey = y - r * 0.08
    if state in ("open", "side"):
        for sx in (-1, 1):
            eye(c, x + sx * ex, ey, r * 0.26, 1.0, dx=(0.35 if state == "side" else 0.0), lashes=False)
    elif state == "pre":
        for sx in (-1, 1): eye(c, x + sx * ex, ey, r * 0.26, 0.35, dy=-0.2, lashes=False)
    elif state == "cough":
        c.set_source_rgba(*DARK, 1); c.set_line_width(r * 0.06); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for sx in (-1, 1):
            c.move_to(x + sx * ex - r * 0.16, ey + r * 0.02); c.curve_to(x + sx * ex - r * 0.05, ey - r * 0.08, x + sx * ex + r * 0.05, ey - r * 0.08, x + sx * ex + r * 0.16, ey + r * 0.02); c.stroke()
    else:
        c.set_source_rgba(*DARK, 1); c.set_line_width(r * 0.06); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for sx in (-1, 1):
            c.move_to(x + sx * ex - r * 0.2, ey - r * 0.08 * -1); c.line_to(x + sx * ex + r * 0.05 * sx, ey - r * 0.02)
            c.line_to(x + sx * ex - r * 0.2 * -1 * 0 - r * 0.2 + (r * 0.4 if sx > 0 else 0), ey + r * 0.1); c.stroke()
    my = y + r * 0.52
    c.set_source_rgba(*DARK, 1); c.set_line_width(r * 0.05)
    if state == "cough":
        c.save(); c.translate(x, my); c.scale(1.0, 0.75); c.arc(0, 0, r * 0.15, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgba(*SKIND, 1); c.arc(x + r * 0.32, my + r * 0.12, r * 0.17, 0, 2 * math.pi); c.fill()   # punho à frente da boca
    elif state == "sneeze":
        c.save(); c.translate(x, my); c.scale(1.3, 0.8); c.arc(0, 0, r * 0.16, 0, 2 * math.pi); c.restore(); c.fill()
    elif state == "pre":
        c.arc(x, my, r * 0.1, 0, 2 * math.pi); c.fill()
    elif state == "side":
        c.move_to(x - r * 0.2, my); c.curve_to(x, my + r * 0.04, x + r * 0.15, my, x + r * 0.25, my - r * 0.08); c.stroke()
    else:
        c.arc(x, my - r * 0.1, r * 0.22, 0.2 * math.pi, 0.8 * math.pi); c.stroke()
    c.restore()
    for s in sneezes:
        d = t - s
        if 0 <= d < 0.45:
            k = ease(d / 0.15)
            burst(c, x, y - r - 60, 190 * k, GOLD2, 1 - clamp((d - 0.3) / 0.15), rot=d)
            text(c, "ATCHOO!", x, y - r - 60, 84, DARK, 1 - clamp((d - 0.3) / 0.15), outline=False, scale=k, rot=-0.08)


def s_pepper(c, t):
    t0 = T["so"]
    background(c, t, top=(0.06, 0.22, 0.15))
    sneezes = [T["snorting"] + 0.2, T["lineof"] + 0.1, T["black"] + 0.35, T["free"] + 0.05]
    cough_on = T["cough"] - 0.3 <= t < T["black"]
    coughing = T["cough"] <= t < T["cough"] + C_LEN * 0.8
    face(c, t, sneezes, 520, 1040, 240, extra_eyes=("cough" if coughing else "side") if cough_on else None)
    if coughing:
        d = t - T["cough"]
        for j in range(5):
            q = clamp(d / 0.45 - j * 0.08)
            if q > 0: glow(c, 640 + 160 * q + j * 14, 1150 - 40 * q - j * 10, 30 + 50 * q, (0.85, 0.85, 0.85), 0.5 * (1 - q))
        text(c, "*COUGH*", 760, 900, 78, INK, 1 - clamp((d - C_LEN * 0.6) / 0.15), scale=popin(t, T["cough"], 0.15), rot=-0.12)
    # pimenteiro a abanar por cima
    shaking = not cough_on
    rot = 2.5 + (0.25 * math.sin(t * 28) if shaking else 0.0)
    sx_ = 760 + (15 * math.sin(t * 28) if shaking else 0)
    sk = popin(t, t0, 0.25)
    shaker(c, sx_, 610, 1.1 * sk, rot, label=False)
    # pó de pimenta cinzento a cair
    if shaking and t > t0 + 0.15:
        for (px, ph, sz, sp) in PEP:
            q = (ph + (t - t0) * 0.9 * sp) % 1
            gx = 690 + px * (40 + 200 * q) - 120 * q; gy = 720 + 200 * q
            c.set_source_rgba(0.22, 0.22, 0.22, 0.85 * (1 - q)); c.arc(gx, gy, sz * (0.6 + 0.6 * q), 0, 2 * math.pi); c.fill()
        glow(c, 560, 870, 260, (0.45, 0.45, 0.45), 0.35)
    floaters(c, t, [(s + 0.05, 520 + 220 * (1 if i % 2 else -1), 650) for i, s in enumerate(sneezes)], GOLD, 84)
    # contagem
    n = sum(1 for s in sneezes if t >= s)
    text(c, "ALL DAY LONG", 540, 330, 84, MINT, seg(t, t0, t0 + 0.2) * (1 - seg(t, T["cough"] - 0.3, T["cough"] - 0.1)))
    if cough_on and not coughing:
        text(c, "...", 540, 330, 120, INK, 1)
    bk = seg(t, T["black"] - 0.05, T["black"] + 0.12)
    text(c, "BLACK PEPPER", 540, 330, 104, GOLD, bk * (1 - seg(t, T["free"] - 0.1, T["free"])), scale=popin(t, T["black"] - 0.05))
    fk = seg(t, T["free"] - 0.05, T["free"] + 0.12)
    if fk > 0:
        text(c, "FREE MONEY", 540, 330, 112, MINT, fk, scale=popin(t, T["free"] - 0.05))
        for j in range(10):
            d = t - T["free"]
            an = j * 0.63
            coin(c, 540 + math.cos(an) * 420 * ease(d / 0.5), 1000 + math.sin(an) * 300 * ease(d / 0.5) - 200 * d, 40, 1 - clamp((d - 0.5) / 0.3), spin=d * 12 + j)
    if n: counter_box(c, f"+${n}", 880, 1180, 80, GOLD, 1, scale=popin(t, max(s for s in sneezes if t >= s), 0.2))


CONF = [(random.uniform(-1, 1), random.uniform(-1, 0.3), random.uniform(10, 26), random.choice([GOLD, GOLD2, MINT, (1, 1, 1), (1, 0.6, 0.1)]),
         random.uniform(0, 6.28), random.uniform(0.6, 1.4)) for _ in range(320)]


def s_year(c, t):
    t0 = T["andyear"]; big = T["big"]
    background(c, t, ga=0.6, gcol=GOLD)
    if t < big:
        # calendário a folhear 1 -> 365
        p = clamp((t - t0) / (big - t0 - 0.05))
        day = max(1, int(1 + 364 * p ** 1.6))
        c.save(); c.translate(540, 820); c.rotate(0.03 * math.sin(t * 30))
        c.set_source_rgba(1, 1, 1, 1); rr(c, -260, -220, 520, 440, 30); c.fill()
        c.set_source_rgba(*RED, 1); rr(c, -260, -220, 520, 110, 30); c.fill(); c.rectangle(-260, -150, 520, 40); c.fill()
        c.restore()
        text(c, "DAY", 540, 655, 60, INK, 1, outline=False)
        text(c, f"{day}", 540, 860, 230, DARK, 1, outline=False)
        text(c, "AFTER ONE YEAR...", 540, 330, 84, MINT, seg(t, t0, t0 + 0.2))
        return
    d = t - big
    glow(c, 540, 820, 900, GOLD2, 0.55 * math.exp(-d * 1.5) + 0.15)
    # raios
    c.save(); c.translate(540, 820); c.rotate(d * 0.4)
    for k in range(16):
        c.set_source_rgba(*GOLD, 0.10); c.move_to(0, 0)
        c.arc(0, 0, 1400, k * math.pi / 8, k * math.pi / 8 + math.pi / 16); c.close_path(); c.fill()
    c.restore()
    # notas e moedas a explodir
    for i, (vx, vy, sz, col, ph, sp) in enumerate(CONF):
        x = 540 + vx * 900 * sp * (1 - math.exp(-d * 3)); y = 820 + vy * 1000 * sp * (1 - math.exp(-d * 3)) + 260 * d * d
        if y > H + 50: continue
        c.save(); c.translate(x, y); c.rotate(ph + d * 6 * sp)
        c.set_source_rgba(*col, 1); c.rectangle(-sz / 2, -sz / 4, sz, sz / 2); c.fill(); c.restore()
    sc = popin(t, big - 0.02, 0.3) * (1 + 0.025 * math.sin(d * 9))
    sh = 12 * math.exp(-d * 5) * math.sin(d * 90)
    text(c, money(5256000 * min(1, 0.35 + 0.65 * ease(d / 0.6))), 540 + sh, 820, 168, GOLD, 1, scale=sc, ow=0.16)
    text(c, "IN ONE YEAR", 540, 990, 80, INK, seg(t, big + 0.3, big + 0.5))
    text(c, "$14,400 × 365 DAYS", 540, 1100 - 20, 56, MINT, seg(t, big + 0.8, big + 1.0))
    text(c, "JUST FOR BLINKING", 540, 330, 84, MINT, seg(t, big + 1.2, big + 1.4))


def s_ask(c, t):
    t0 = T["blinkq"]; u = t - t0
    background(c, t, ga=0.4)
    fl = int(u * 4) % 2
    for i, (lab, x, col) in enumerate((("BLINK", 300, MINT), ("SNEEZE", 780, GOLD))):
        on = (fl == i)
        s = popin(t, t0 + i * 0.25, 0.22) * (1.08 if on else 0.95)
        if s <= 0: continue
        c.save(); c.translate(x, 800); c.scale(s, s)
        c.set_source_rgba(*(col if on else (0.2, 0.3, 0.25)), 1); rr(c, -220, -240, 440, 480, 50); c.fill()
        c.restore()
        if i == 0:
            c.save(); c.translate(x, 720); c.scale(s, s); eye(c, 0, 0, 140, blink_open(u, [0.5, 1.3]), lashes=True); c.restore()
        else:
            c.save(); c.translate(x, 700); c.scale(s * 0.7, s * 0.7); shaker(c, 0, 0, 1.0, 0.25 * math.sin(t * 20), label=False); c.restore()
        text(c, lab, x, 800 + 170 * s, 84, DARK if on else INK, popin(t, t0 + i * 0.25, 0.22) and 1, outline=not on)
    text(c, "OR", 540, 800, 80, INK, seg(t, t0 + 0.2, t0 + 0.35))
    text(c, "BLINK OR SNEEZE?", 540, 340, 96, INK, seg(t, t0, t0 + 0.15))
    ok = T["oneword"]
    n = int(clamp((t - ok) / 0.3) * 9)
    text(c, "ONE WORD."[:n], 540, 1210, 110, GOLD, 1 if n else 0)


def s_loop(c, t):
    s_hook(c, t, u=t - T_END)


SCENES = [
    (0.0, T["rate"], s_hook), (T["rate"], T["brand"], s_rate), (T["brand"], T["because"], s_brand),
    (T["because"], T["lunch"], s_900), (T["lunch"], T["bedtime"], s_rent), (T["bedtime"], T["meeting"], s_bed),
    (T["meeting"], T["wait"], s_meeting), (T["wait"], T["sleeping"], s_tease), (T["sleeping"], T["alarm"], s_sleep),
    (T["alarm"], T["sneezing"], s_boss), (T["sneezing"], T["so"], s_sneeze), (T["so"], T["andyear"], s_pepper),
    (T["andyear"], T["blinkq"], s_year), (T["blinkq"], LOOP_START, s_ask), (LOOP_START, 99, s_loop),
]

# ---------- sobreposições ----------
ALARM_END = HOOK_BLINKS[-1] + 0.12   # recompensa: $3 no ecrã
SUB_T0 = T["boss"] + 0.25            # pop-up de subscrição logo depois de "Your alarm clock is now your boss"
BADGE = (T["wait"], T["big"])


def alarm_border(c, t):
    if T_END - 0.2 <= t:   # fim do loop: a borda volta a acender para o último frame = primeiro
        a = 0.9 * seg(t, T_END - 0.2, T_END - 1 / FPS)
    elif t >= ALARM_END: return
    else:
        on = (t % 0.25) < 0.125
        a = (0.9 if on else 0.35) * (1 - seg(t, ALARM_END - 0.1, ALARM_END))
    c.set_source_rgba(*RED, a); c.set_line_width(26); c.rectangle(13, 13, W - 26, H - 26); c.stroke()
    g = cairo.LinearGradient(0, 0, 0, 160); g.add_color_stop_rgba(0, *RED, 0.35 * a); g.add_color_stop_rgba(1, *RED, 0)
    c.set_source(g); c.rectangle(0, 0, W, 160); c.fill()


def badge(c, t):
    a0, a1 = BADGE
    if not (a0 <= t < a1 + 0.35): return
    k = popin(t, a0, 0.25); out = seg(t, a1, a1 + 0.3)
    a = 1 - out
    c.save(); c.translate(540, 200); c.scale(k * (1 + 0.4 * out), k * (1 + 0.4 * out))
    c.set_source_rgba(0, 0, 0, 0.6 * a); rr(c, -300, -42, 600, 84, 42); c.fill()
    pulse = 0.6 + 0.4 * math.sin(t * 6)
    c.set_source_rgba(*GOLD, a * pulse); c.set_line_width(5); rr(c, -300, -42, 600, 84, 42); c.stroke()
    # cadeado
    c.set_source_rgba(*GOLD, a); rr(c, -265, -12, 36, 30, 6); c.fill()
    c.set_line_width(6); c.arc(-247, -12, 12, math.pi, 2 * math.pi); c.stroke()
    c.restore()
    text(c, "YEAR TOTAL · COMING UP", 555, 200, 38, INK, a * (k > 0), outline=False, scale=k)


def bell_icon(c, x, y, s, col, a, rot):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s); c.set_source_rgba(*col, a)
    c.move_to(-14, 8); c.curve_to(-14, -6, -12, -18, 0, -18); c.curve_to(12, -18, 14, -6, 14, 8); c.line_to(18, 12); c.line_to(-18, 12); c.close_path(); c.fill()
    c.arc(0, 16, 5, 0, 6.283); c.fill(); c.rectangle(-2, -23, 4, 6); c.fill(); c.restore()


def subscribe(c, t):
    """pop-up de subscrição (baseado em lib/subscribe_popup.py, cores do tema)"""
    u = t - SUB_T0
    if u < 0 or u > 2.6: return
    inn = seg(u, 0, 0.35); out = seg(u, 2.2, 2.55); a = inn * (1 - out)
    done = u > 1.0
    w, h = 660, 104; x = (W - w) / 2; y = 330 - 40 * (1 - inn) - 30 * out
    sc = 0.92 + 0.08 * inn - 0.05 * math.sin(math.pi * clamp((u - 0.85) / 0.25))
    c.save(); c.translate(W / 2, y + h / 2); c.scale(sc, sc); c.translate(-W / 2, -(y + h / 2))
    c.set_source_rgba(0.02, 0.1, 0.06, 0.88 * a); rr(c, x, y, w, h, h / 2); c.fill()
    col = GREY if done else GOLD
    c.set_source_rgba(*col, 0.95 * a); c.set_line_width(4); rr(c, x, y, w, h, h / 2); c.stroke()
    wig = 0.35 * math.sin((u - 1.0) * 28) * math.exp(-(u - 1.0) * 5) if done else 0
    bell_icon(c, x + 64, y + h / 2 - 2, 1.25, INK if done else GOLD, a, wig)
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    if not done:
        c.set_font_size(40); c.set_source_rgba(*INK, a); c.move_to(x + 110, y + h / 2 + 14); c.show_text("SUBSCRIBE")
        c.set_font_size(30); c.set_source_rgba(*MINT, a); c.move_to(x + 345, y + h / 2 + 11); c.show_text("for more what ifs")
    else:
        c.set_font_size(40); c.set_source_rgba(*INK, a); c.move_to(x + 110, y + h / 2 + 14); c.show_text("SUBSCRIBED")
        check(c, x + 410, y + h / 2 - 2, 40, MINT, a, clamp((u - 1.0) / 0.25))
    c.restore()
    if 0.5 < u < 1.5:
        fx = x + w - 120; fy = y + h / 2
        pa = seg(u, 0.5, 0.8) * (1 - seg(u, 1.2, 1.5)); tap = seg(u, 0.85, 1.0)
        c.set_source_rgba(1, 1, 1, 0.55 * pa * a); c.arc(fx, fy + 60 * (1 - seg(u, 0.5, 0.85)), 34 - 8 * tap, 0, 6.283); c.fill()
        if u > 0.95:
            q = (u - 0.95) / 0.5
            c.set_source_rgba(*MINT, 0.6 * (1 - q) * a); c.set_line_width(4); c.arc(fx, fy, 30 + 90 * q, 0, 6.283); c.stroke()


def render_scene(fn, t):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_GOOD)
    fn(c, t); return s


def frame_surface(t):
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); ctx = cairo.Context(out)
    for i, (a, b, fn) in enumerate(SCENES):
        if a <= t < b:
            cur = render_scene(fn, t)
            x = (t - a) / 0.16
            if i > 0 and x < 1 and fn is not s_loop:   # entrada com zoom rápido (punch)
                z = 1.12 - 0.12 * ease(x)
                ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2)
                ctx.set_source_surface(cur, 0, 0); ctx.paint(); ctx.restore()
                ctx.set_source_rgba(1, 1, 1, 0.25 * (1 - x)); ctx.paint()
            else:
                ctx.set_source_surface(cur, 0, 0); ctx.paint()
            break
    alarm_border(ctx, t)
    badge(ctx, t)
    subscribe(ctx, t)
    return out


def frame(t):
    s = frame_surface(t)
    return np.ndarray((H, W, 4), np.uint8, s.get_data())[:, :, [2, 1, 0]].tobytes()


# ---------- legendas (ASS, palavra a palavra) ----------
WEAK = {"a", "an", "the", "to", "of", "for", "on", "in", "it", "and", "but", "is", "your", "you", "or", "by", "that", "that's", "my", "me"}


def bare(w): return re.sub(r"[^\w'$,]", "", w).lower()


groups, cur = [], []
for w in words:
    cand = cur + [w]
    if cur and (len(cand) > 3 or len(" ".join(x["w"] for x in cand)) > 16):
        if len(cur) > 1 and bare(cur[-1]["w"]) in WEAK:
            carry = cur.pop(); groups.append(cur); cur = [carry, w]
        else:
            groups.append(cur); cur = [w]
    else:
        cur = cand
    if re.search(r"[.?!:…]$", w["w"]) or (w["w"].endswith(",") and not re.fullmatch(r"\$[\d,]+", w["w"])):
        groups.append(cur); cur = []
if cur: groups.append(cur)


def ts(x):
    h, r = divmod(max(x, 0), 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


HL, WH = "&H003DD2FF&", "&H00FFFFFF&"   # destaque amarelo-dourado (BGR)
ev = []
for gi, g in enumerate(groups):
    g_end = min(groups[gi + 1][0]["s"], g[-1]["e"] + 0.4) if gi + 1 < len(groups) else T_END
    for k, w in enumerate(g):
        s = w["s"]; e = g[k + 1]["s"] if k + 1 < len(g) else g_end
        if e <= s: continue
        pop = "{\\fscx110\\fscy110\\t(0,80,\\fscx100\\fscy100)}" if k == 0 else ""
        txt = " ".join((f"{{\\c{HL}}}{x['w'].upper()}{{\\c{WH}}}" if j == k else x["w"].upper()) for j, x in enumerate(g))
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},Cap,,0,0,0,,{pop}{txt}")
ev.append(f"Dialogue: 2,{ts(0)},{ts(T_END)},Mark,,0,0,0,,@whatifaholics")
ASS = f"{BLD}/captions.ass"
open(ASS, "w").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display,80,&H00FFFFFF,&H00FFFFFF,&H00101010,&H78000000,-1,0,0,0,100,100,0,0,1,7,3,2,90,140,470,1
Style: Mark,Inter Display,38,&H8CFFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,3,0,7,60,60,110,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n")


def mix(raw_video):
    def a(name): return f"{SFX}/{name}.wav"
    P = 0.5; h = P / 2
    env = f"min(1,mod(t,{h})*120)*min(1,({h}-mod(t,{h}))*120)"
    tone = f"(lt(mod(t,{P}),{h})*(sin(2*PI*960*t)+0.3*sin(2*PI*2880*t))+gte(mod(t,{P}),{h})*(sin(2*PI*770*t)+0.3*sin(2*PI*2310*t)))"
    alarm = f"{BLD}/alarm.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='0.45*{env}*{tone}':s=48000:d={ALARM_END:.3f}",
                    "-af", f"afade=t=out:st={ALARM_END - 0.08:.3f}:d=0.08", alarm], check=True)
    def synth(name, expr, d):
        p = f"{BLD}/{name}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={d}", p], check=True); return p
    swish = f"{BLD}/swish.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.5:c=pink:a=0.5:r=48000",
                    "-af", "bandpass=f=900:w=1400,afade=t=in:d=0.25:curve=qsin,afade=t=out:st=0.25:d=0.25,volume=0.35", swish], check=True)
    pop = synth("pop_soft", "0.5*sin(2*PI*(260+500*exp(-t*35))*t)*exp(-t*22)", 0.2)
    ding = synth("ding", "0.35*(sin(2*PI*1320*t)+0.5*sin(2*PI*1980*t))*exp(-t*9)", 0.6)
    tick = synth("tick", "0.45*sin(2*PI*2200*t)*exp(-t*90)", 0.06)
    ring = synth("ring", "0.3*sin(2*PI*2400*t)*(0.5+0.5*sin(2*PI*28*t))*exp(-t*1.2)", 1.2)
    boom = f"{BLD}/boom.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "aevalsrc='0.9*sin(2*PI*(48+70*exp(-t*6))*t)*exp(-t*2.8)':s=48000:d=1.6",
                    "-af", "volume=0.8", boom], check=True)
    E = [(alarm, 0.0, 0.3)]
    E += [(a("kaching"), b + 0.05, 0.55) for b in HOOK_BLINKS]
    E += [(a("scratch_head"), T["brand"], 0.7)]
    E += [(swish, x - 0.2, 0.45) for x in (T["because"], T["meeting"], T["sleeping"], T["sneezing"], T["andyear"])]
    E += [(pop, x, 0.45) for x in (T["fifteen"], T["n900"], T["n14"], T["oneyear"])]
    E += [(a("kaching"), x, 0.35) for x in (T["n900"] + 0.55, T["n14"] + 0.7)]
    E += [(ding, x, 0.35) for x in (T["paid"], T["best"] + 0.1, T["boss"], T["free"])]
    E += [(ring, T["alarm"], 0.25)]
    days = [T["andyear"] + (T["big"] - T["andyear"]) * k / 9 for k in range(9)]
    E += [(tick, x, 0.4) for x in days]
    E += [(boom, T["big"] - 0.02, 0.8), (a("kaching"), T["big"] + 0.02, 0.6)]
    E += [(pop, SUB_T0 + 1.0, 0.3)]
    E += [(pop, T["blinkq"] + x, 0.3) for x in (0.0, 0.25)]
    E += [(a("kaching"), LOOP_START + 0.0, 0.0)]  # placeholder silencioso
    ins, ch, lab = [], [], []
    for n, (f, x, v) in enumerate(E):
        if v <= 0: continue
        i = 3 + len(lab); ins += ["-i", f]; d = int(max(0, x) * 1000)
        ch.append(f"[{i}:a]adelay={d}|{d},volume={v}[e{len(lab)}]"); lab.append(f"[e{len(lab)}]")
    sfx = ";".join(ch) + ";" + "".join(lab) + f"amix=inputs={len(lab)}:normalize=0[sfx]"
    big = T["big"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw_video, "-i", NARR, "-stream_loop", "-1", "-i", MUSIC, *ins,
                    "-filter_complex",
                    f"[0:v]subtitles={ASS},format=yuv420p[v];"
                    "[1:a]asplit=2[n1][nk];"
                    f"[2:a]atrim=0:{T_END},volume='if(lt(t,{ALARM_END:.2f}),0.12,if(between(t,{big-0.7:.2f},{big:.2f}),0.06,0.32))':eval=frame,"
                    f"afade=t=out:st={T_END-0.6}:d=0.6[m];"
                    "[m][nk]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[md];"
                    f"{sfx};[n1][md][sfx]amix=inputs=3:duration=longest:normalize=0,apad,"
                    f"loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{T_END}[a]",
                    "-map", "[v]", "-map", "[a]", "-t", str(T_END), "-r", str(FPS),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "10M", "-bufsize", "20M",
                    "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", OUT], check=True)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--frames":
        for tt in sys.argv[2].split(","):
            frame_surface(float(tt)).write_to_png(f"{BLD}/f_{float(tt):06.2f}.png")
        print("frames ok"); sys.exit()
    print("T_END", T_END, {k: round(v, 2) for k, v in T.items()})
    raw_v = f"{BLD}/raw.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", raw_v], stdin=subprocess.PIPE)
    N = int(round(T_END * FPS))
    for i in range(N):
        p.stdin.write(frame(i / FPS))
    p.stdin.close(); p.wait()
    mix(raw_v)
    print("OK", OUT, T_END)
