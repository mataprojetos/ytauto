#!/usr/bin/env python3
"""Whatifaholic #001 v6 — versão curta (~48 s): alarme de emergência no gancho, sem a parte da inclinação,
corais corrigidos (a Lua é uma das pistas, não a única). Baseado no v5."""
import math, random, re, json, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cairo
import numpy as np
import neuro_lib as L
from neuro_lib import (W, H, FPS, A, BLD, NAVY, CYAN, CREAM, SUN, INK, PINK, QUIET, GREEN, MX, MY, MOON_R,
                       seg, ease, paint_cover, twinkle, glow, draw_moon, text, earth, bulge, sky, pts, eggs)

ROOT = os.path.dirname(os.path.abspath(__file__))
NARR = f"{ROOT}/audio/narration_v6.wav"
MUSIC = f"{ROOT}/../music/track01_cosmic_ambient.mp3"
OUT = f"{ROOT}/whatifaholic_ep001_moon_v6.mp4"
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "csv=p=0", NARR]))
T_END = round(dur + 0.5, 2)
RED = (1.0, 0.32, 0.32)

werewolf, _ = L.surf(f"{A}/werewolf.png")
surfer, _ = L.surf(f"{A}/surfer.png")
finger, _ = L.surf(f"{A}/finger.png")

# ---------- palavras e âncoras ----------
words = json.load(open(f"{BLD}/words_v6.json"))
FIX = {"timed": "time", "breaks": "brakes", "you": "You", "moon.": "Moon.", "breaking": "braking", "sun": "Sun", "sun?": "Sun?", "So,": "So", "that's": "that"}
merged = []
for i, w in enumerate(words):
    if w["w"] == "that's" and i + 1 < len(words) and words[i + 1]["w"] == "strange":
        w["w"] = "that"
    elif w["w"] != "that's":
        w["w"] = FIX.get(w["w"], w["w"])
    if merged and re.fullmatch(r"\.\d+", w["w"]):
        merged[-1]["w"] += w["w"]; merged[-1]["e"] = w["e"]
    else:
        merged.append(dict(w))
words = merged


def at(phrase, after=0.0):
    """tempo de início da 1.ª ocorrência da frase (palavras) depois de 'after'"""
    toks = phrase.lower().split()
    clean = [re.sub(r"[^\w'.]", "", w["w"]).lower().rstrip(".") for w in words]
    for i in range(len(words) - len(toks) + 1):
        if words[i]["s"] >= after and all(clean[i + j] == toks[j] for j in range(len(toks))):
            return words[i]["s"]
    raise KeyError(phrase)


T = dict(
    light=at("because if it vanished"), first13=at("1.3"), after=at("after that"), strangest=at("strangest"),
    tides=at("first"), sunpull=at("the sun pulls"), half=at("half as hard"), sea=at("high tides"),
    surfers=at("surfers"), devastated=at("devastated"), easy=at("every night"),
    nofull=at("no full moon"), wolves=at("werewolves"), unemployed=at("unemployed"),
    corals=at("corals"), nosignal=at("they'd lose"),
    weirder=at("now it gets weirder"), braking=at("the moon's pull"), billion=at("1.4"), eighteen=at("18"),
    monday=at("a monday"), honestly=at("honestly"),
    promised=at("and that strange"), leaving=at("the moon is leaving"),
    three8=at("3.8"), roughly=at("as fast as"), grow=at("grow"), question=at("one year without"),
    tellme=at("tell me below"), tonight=at("because if it ever"), last13=at("1.3", after=40),
)
T["ever"] = at("ever", after=T["nofull"])
T["animals"] = T["corals"]
T["lasers"] = at("about", after=T["leaving"])

SHATTER = next(w["e"] for w in words if re.sub(r"[^\w]", "", w["w"]).lower() == "moon")
T["shatter"] = SHATTER
C0 = SHATTER - 1.3
# deixar a Lua estilhaçar à vista antes de passar à cena da luz
T["light"] = max(T["light"], SHATTER + 0.7)


# ---------- cenas ----------
def s_countdown(ctx, t):
    """gancho: contador 1.30 -> 0.00 e a Lua estilhaça no zero"""
    shake = 6 * seg(t, C0, SHATTER) * (t < SHATTER)
    dx, dy = shake * math.sin(t * 90), shake * math.cos(t * 77)
    ctx.save(); ctx.translate(dx, dy)
    paint_cover(ctx, L.bg, t, 0, T["light"], 1.0, 1.05)
    twinkle(ctx, t, 0.6)
    if t < SHATTER:
        glow(ctx, MX, MY, MOON_R * 1.9, CREAM, 0.22 + 0.1 * seg(t, C0, SHATTER))
        draw_moon(ctx, MX, MY, L.moon, MOON_R, 1.0)
    else:
        tr = t - SHATTER
        for (px, py, col, vy, sp, size) in pts:
            d = math.hypot(px, py) + 1e-3
            ux, uy = px / d, py / d
            dist = (380 + 520 * sp) * (1 - math.exp(-tr * 3.2))
            a = max(0, 1 - tr / 1.5)
            if a <= 0.01:
                continue
            ctx.set_source_rgba(*col, a)
            ctx.arc(MX + px + ux * dist + vy * 40 * tr, MY + py + uy * dist + 90 * tr * tr, size * (1.1 - 0.5 * tr / 1.5), 0, 6.283)
            ctx.fill()
        glow(ctx, MX, MY, MOON_R * 2.6, (1, 1, 1), 0.9 * max(0, 1 - tr / 0.25))
    ctx.restore()
    if t < SHATTER + 0.05:
        v = 1.3 if t < C0 else max(0.0, 1.3 - (t - C0))
        sc = 1 + 0.06 * math.sin(t * 20) * (t >= C0)
        text(ctx, f"{v:.2f}", 540, 430, 210 * sc, RED, 1.0)
        text(ctx, "SECONDS LEFT", 540, 505, 50, INK, 1.0)
    else:
        g = seg(t, SHATTER + 0.15, SHATTER + 0.35) * (1 - seg(t, T["light"] - 0.3, T["light"]))
        text(ctx, "THE MOON IS GONE.", 540, 450, 96, INK, g)



def s_dissolve(ctx, t):
    paint_cover(ctx, L.bg, t, 0, T["light"], 1.0, 1.05)
    twinkle(ctx, t, 0.6)
    t0, t1 = 0.7, T["light"] - 0.3
    glow(ctx, MX, MY, MOON_R * 1.9, CREAM, 0.22 * (1 - seg(t, t0, t1)))
    front = MX - MOON_R - 10 + (2 * MOON_R + 30) * seg(t, t0, t1)
    draw_moon(ctx, MX, MY, L.moon, MOON_R, 1.0, clip_x=front if t > t0 else None)
    if t < t0:
        return
    span = t1 - t0
    for (px, py, col, vy, sp, size) in pts:
        gx = MX + px
        if gx > front:
            continue
        tr = t - (t0 + (gx - (MX - MOON_R)) / (2 * MOON_R + 30) * span)
        if tr < 0:
            continue
        a = max(0, 1 - tr / 1.6)
        ctx.set_source_rgba(*col, a)
        ctx.arc(gx - sp * 280 * tr - 50 * tr * tr, MY + py + vy * 130 * tr - 70 * tr, size * (1 - 0.4 * tr / 1.6), 0, 6.283)
        ctx.fill()


def s_light(ctx, t):
    sky(ctx); twinkle(ctx, t, 0.5)
    t0 = T["light"]; ex, ey, mx, my = 300, 1500, 820, 470
    k = seg(t, t0, t0 + 0.3)
    earth(ctx, ex, ey, 150, k, rot=t * 0.05)
    draw_moon(ctx, mx, my, L.small_moon, 70, k)
    ctx.set_dash([10, 14]); ctx.set_line_width(3); ctx.set_source_rgba(1, 1, 1, 0.35 * k)
    ctx.move_to(mx, my); ctx.line_to(ex, ey); ctx.stroke(); ctx.set_dash([])
    text(ctx, "384,400 km", 640, 1030, 44, QUIET, 0.9 * k, "l", bold=False)
    p = seg(t, t0 + 0.15, t0 + 1.3)
    on = t0 + 0.15 < t < t0 + 1.45
    for i in range(12):
        q = max(0, p - i * 0.015)
        glow(ctx, mx + (ex - mx) * q, my + (ey - my) * q, 34 - i * 2, CREAM, 0.5 * (1 - i / 12) * on)
    if on:
        glow(ctx, mx + (ex - mx) * p, my + (ey - my) * p, 70, CREAM, 0.8)
    text(ctx, f"{1.3 * p:.1f} s", 540, 330, 160, CYAN if p >= 1 else INK, k)
    text(ctx, "LIGHT TRAVEL TIME", 540, 405, 46, QUIET, k, bold=False)


def s_strange(ctx, t):
    t0, t1 = T["after"], T["tides"]
    paint_cover(ctx, L.bg, t, t0, t1, 1.05, 1.16)
    ctx.set_source_rgba(0, 0, 0.02, 0.4 * seg(t, t0, t0 + 1.2)); ctx.paint()
    twinkle(ctx, t * 1.6, 1.0)
    ctx.set_source_rgba(*CYAN, 0.55 * (1 - seg(t, t0 + 0.2, t1 - 0.5))); ctx.set_line_width(4)
    ctx.set_dash([6, 18]); ctx.arc(MX, MY, MOON_R * (1 + 0.15 * seg(t, t0, t1)), 0, 6.283); ctx.stroke()
    ctx.set_dash([])
    # "?" gigante a pulsar enquanto se fala da parte mais estranha
    q = seg(t, T["strangest"], T["strangest"] + 0.3)
    text(ctx, "?", MX, MY + 90, 300 * (1 + 0.05 * math.sin(t * 6)), CYAN, q)


def s_tides(ctx, t):
    sky(ctx); twinkle(ctx, t, 0.4)
    t0 = T["tides"]; ex, ey, er = 540, 860, 170
    k = seg(t, t0, t0 + 0.4)
    sa = seg(t, T["sunpull"], T["sunpull"] + 0.5)
    glow(ctx, -40, ey, 380, SUN, 0.55 * sa)
    ctx.set_source_rgba(*SUN, sa); ctx.arc(-120, ey, 190, 0, 6.283); ctx.fill()
    fade = seg(t, T["sea"] - 0.7, T["sea"] - 0.1)
    moon_a = k * (1 - fade)
    mxp = 900 + 120 * fade
    draw_moon(ctx, mxp, ey, L.small_moon, 62, moon_a)
    big = 0.42 * (1 - fade); small = 0.20 * seg(t, T["half"] - 0.2, T["half"] + 0.4)
    if big > 0.02:
        bulge(ctx, ex, ey, er * 1.12, 0, big, CYAN, 0.35 * k)
    if small > 0.02:
        bulge(ctx, ex, ey, er * 1.06, 0, small, SUN, 0.30)
    earth(ctx, ex, ey, er, k, rot=t * 0.04)
    # seta da Lua a puxar o oceano
    pa = k * (1 - seg(t, T["half"] - 0.4, T["half"]))
    arrow(ctx, 760, ey - 140, 690, ey - 60, CYAN, pa)
    text(ctx, "MOON", mxp, ey + 125, 46, CREAM, moon_a)
    text(ctx, "SUN", 120, ey + 265, 46, SUN, sa)
    text(ctx, "≈ ½ AS HARD", 220, ey - 255, 58, SUN, seg(t, T["half"], T["half"] + 0.3), "l")
    text(ctx, "OCEAN BULGE", ex, ey - 300, 46, CYAN, k * (1 - seg(t, T["half"] - 0.4, T["half"])))


def arrow(ctx, x0, y0, x1, y1, col, a, w=7):
    if a <= 0.01:
        return
    ang = math.atan2(y1 - y0, x1 - x0)
    ctx.set_source_rgba(*col, a); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0, y0); ctx.line_to(x1, y1); ctx.stroke()
    for s in (-1, 1):
        ctx.move_to(x1, y1); ctx.line_to(x1 - 34 * math.cos(ang + s * 0.5), y1 - 34 * math.sin(ang + s * 0.5))
        ctx.stroke()


def s_sealevel(ctx, t):
    sky(ctx, (0.06, 0.1, 0.24), (0.04, 0.07, 0.16)); twinkle(ctx, t, 0.35)
    t0 = T["sea"]; k = seg(t, t0, t0 + 0.3)
    today, after = 1000, 1190
    lvl = today + (after - today) * seg(t, t0 + 0.4, T["surfers"] - 0.4)
    ctx.set_source_rgba(0.09, 0.12, 0.2, 1)
    ctx.move_to(720, 1500); ctx.line_to(760, 700); ctx.line_to(900, 640); ctx.line_to(1080, 660)
    ctx.line_to(1080, 1500); ctx.close_path(); ctx.fill()
    ctx.set_source_rgba(*CYAN, 0.9 * k); ctx.set_line_width(4); ctx.set_dash([14, 10])
    ctx.move_to(60, today); ctx.line_to(1040, today); ctx.stroke(); ctx.set_dash([])
    text(ctx, "HIGH TIDE TODAY", 700, today - 24, 44, CYAN, k, "r")
    ctx.move_to(0, H)
    for x in range(0, W + 10, 10):
        ctx.line_to(x, lvl + 10 * math.sin(x / 60 + t * 3) + 5 * math.sin(x / 23 - t * 4.2))
    ctx.line_to(W, H); ctx.close_path()
    g = cairo.LinearGradient(0, lvl, 0, H)
    g.add_color_stop_rgba(0, 0.12, 0.45, 0.75, 0.95); g.add_color_stop_rgba(1, 0.02, 0.08, 0.2, 1)
    ctx.set_source(g); ctx.fill()
    by = lvl - 18 + 6 * math.sin(t * 2.5)
    ctx.save(); ctx.translate(190, by); ctx.rotate(0.06 * math.sin(t * 2.1))
    ctx.set_source_rgba(0.95, 0.55, 0.35, 1)
    ctx.move_to(-90, 0); ctx.line_to(90, 0); ctx.line_to(60, 40); ctx.line_to(-60, 40); ctx.close_path(); ctx.fill()
    ctx.set_source_rgba(0.9, 0.9, 0.95, 1); ctx.rectangle(-4, -110, 8, 110); ctx.fill()
    ctx.move_to(4, -105); ctx.line_to(70, -10); ctx.line_to(4, -10); ctx.close_path(); ctx.fill()
    ctx.restore()
    d = seg(t, t0 + 0.6, t0 + 1.0)
    arrow(ctx, 860, today + 30, 860, lvl - 40, SUN, d, 9)
    text(ctx, "WITHOUT THE MOON", 820, after - 50, 44, SUN, seg(t, t0 + 1.0, t0 + 1.4), "r")


def s_surfer(ctx, t):
    paint_cover(ctx, surfer, t, T["surfers"], T["easy"], 1.0, 1.10)
    text(ctx, "0 WAVES", 540, 420, 110, INK, seg(t, T["devastated"], T["devastated"] + 0.2))


def s_phases(ctx, t):
    t0 = T["easy"]
    paint_cover(ctx, L.bg, t, t0, T["wolves"], 1.0, 1.06)
    ctx.set_source_rgba(0, 0, 0.03, 0.25 + 0.45 * seg(t, t0, t0 + 1.2)); ctx.paint()
    twinkle(ctx, t, 1.0)
    cx0, y0, gap, r = 120, 560, 120, 46
    for i in range(8):
        appear = seg(t, t0 + 0.15 + i * 0.07, t0 + 0.45 + i * 0.07)
        vanish = seg(t, T["nofull"] + i * 0.1, T["nofull"] + 0.3 + i * 0.1)
        a = appear * (1 - vanish)
        if a <= 0.01:
            continue
        x = cx0 + i * gap
        ctx.set_source_rgba(0.15, 0.17, 0.25, a); ctx.arc(x, y0, r, 0, 6.283); ctx.fill()
        ctx.save(); ctx.arc(x, y0, r, 0, 6.283); ctx.clip()
        lit = math.cos(i / 8.0 * 2 * math.pi)
        half = (x, y0 - r, r, 2 * r) if i < 4 else (x - r, y0 - r, r, 2 * r)
        if lit < 0:
            ctx.set_source_rgba(*CREAM, a); ctx.save(); ctx.translate(x, y0); ctx.scale(max(.001, -lit) * r, r)
            ctx.arc(0, 0, 1, 0, 6.283); ctx.restore(); ctx.fill()
            ctx.rectangle(*half); ctx.fill()
        else:
            ctx.set_source_rgba(*CREAM, a); ctx.rectangle(*half); ctx.fill()
            ctx.set_source_rgba(0.15, 0.17, 0.25, a); ctx.save(); ctx.translate(x, y0)
            ctx.scale(max(.001, lit) * r, r); ctx.arc(0, 0, 1, 0, 6.283); ctx.restore(); ctx.fill()
        ctx.restore()
    text(ctx, "MOON PHASES", 540, 470, 46, QUIET, seg(t, t0 + 0.15, t0 + 0.5) * (1 - seg(t, T["nofull"], T["nofull"] + 0.3)), bold=False)
    e = seg(t, T["ever"], T["ever"] + 0.25)
    text(ctx, "NEW MOON", 540, 590, 110, INK, e)
    text(ctx, "EVERY NIGHT", 540, 680, 54, CYAN, e)


def s_wolf(ctx, t):
    t0 = T["wolves"]

    def sign(c):  # escrever no cartaz em branco (coordenadas da imagem)
        c.save(); c.translate(975, 1585); c.rotate(-0.05)
        for j, line in enumerate(("WILL HOWL", "FOR MOON")):
            c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            c.set_font_size(58); xb, yb, tw, th, _, _ = c.text_extents(line)
            c.move_to(-tw / 2 - xb, -10 + j * 70); c.set_source_rgba(0.22, 0.15, 0.08, 0.9); c.show_text(line)
        c.restore()
    paint_cover(ctx, werewolf, t, t0, T["animals"], 1.02, 1.12, draw_extra=sign)
    s = seg(t, T["unemployed"], T["unemployed"] + 0.15)
    if s > 0:  # carimbo
        ctx.save(); ctx.translate(540, 520); ctx.rotate(-0.18); sc = 1.6 - 0.6 * s; ctx.scale(sc, sc)
        ctx.set_source_rgba(*RED, 0.9 * s); ctx.set_line_width(10)
        ctx.rectangle(-330, -80, 660, 140); ctx.stroke()
        ctx.restore()
        ctx.save(); ctx.translate(540, 520); ctx.rotate(-0.18); ctx.scale(sc, sc)
        text(ctx, "UNEMPLOYED", 0, 32, 100, RED, s); ctx.restore()


def s_reef(ctx, t):
    t0 = T["animals"]
    paint_cover(ctx, L.reef, t, t0, T["weirder"], 1.0, 1.08)
    k = seg(t, t0 + 0.1, t0 + 0.5)
    off = seg(t, T["nosignal"], T["nosignal"] + 0.6)
    ix, iy, ir = 860, 380, 70
    draw_moon(ctx, ix, iy, L.tiny_moon, 45, k * (1 - off))
    prog = ((t - t0) / 2.0) % 1.0
    ctx.set_line_width(8); ctx.set_source_rgba(*CYAN, 0.25 * k); ctx.arc(ix, iy, ir, 0, 6.283); ctx.stroke()
    ctx.set_source_rgba(*CYAN, 0.95 * k * (1 - off))
    ctx.arc(ix, iy, ir, -math.pi / 2, -math.pi / 2 + 6.283 * prog); ctx.stroke()
    text(ctx, "LUNAR CALENDAR", ix - 30, iy + 125, 40, CYAN, k * (1 - off))
    q = seg(t, T["nosignal"] + 0.3, T["nosignal"] + 0.6)
    text(ctx, "MOON CUE LOST", ix - 30, iy + 125, 40, SUN, q)
    text(ctx, "WATER TEMP + DAYLIGHT STILL WORK", 540, 1390, 38, QUIET, q, bold=False)
    rise = seg(t, T["corals"], T["corals"] + 0.8) * (1 - off * 0.5)
    for x, ph, r, sp, w in eggs:
        y = 1700 - ((ph + (t - T["corals"]) * 0.14 * sp) % 1.0) * 1300
        a = rise * (0.85 if y > 450 else max(0, (y - 300) / 150))
        if a > 0.02:
            ctx.set_source_rgba(*PINK, a); ctx.arc(x + 14 * math.sin(t * 1.3 + w), y, r, 0, 6.283); ctx.fill()


def s_time(ctx, t):
    sky(ctx); twinkle(ctx, t, 0.4)
    t0 = T["weirder"]
    rewind = seg(t, T["billion"] - 0.2, T["eighteen"])
    ex, ey, er = 540, 840, 200
    earth(ctx, ex, ey, er, seg(t, t0, t0 + 0.4), rot=t * (0.06 + 0.28 * rewind))
    md = 400 - 70 * rewind
    draw_moon(ctx, ex + md, ey - 260 + 40 * rewind, L.small_moon, 55 + 8 * rewind, seg(t, t0 + 0.2, t0 + 0.6))
    # setas de travão na rotação
    b = seg(t, T["braking"], T["braking"] + 0.3) * (1 - seg(t, T["billion"] - 0.3, T["billion"]))
    ctx.set_source_rgba(*SUN, b); ctx.set_line_width(8)
    ctx.arc(ex, ey, er + 50, math.pi * 1.1, math.pi * 1.6); ctx.stroke()
    text(ctx, "BRAKING", ex - 200, ey - 270, 46, SUN, b)
    a = seg(t, t0 + 0.4, t0 + 0.9)
    hours = 24 - 6 * seg(t, T["billion"] + 1.2, T["eighteen"] + 0.3)
    cx, cy, cr = 540, 1520, 120
    ctx.set_source_rgba(*CYAN, 0.3 * a); ctx.set_line_width(10); ctx.arc(cx, cy, cr, 0, 6.283); ctx.stroke()
    ctx.set_source_rgba(*CYAN, a); ctx.arc(cx, cy, cr, -math.pi / 2, -math.pi / 2 + 6.283 * hours / 24); ctx.stroke()
    text(ctx, f"{hours:.0f} h", cx, cy + 22, 70, INK if hours > 18.5 else CYAN, a)
    text(ctx, "ONE DAY", cx, cy + cr + 70, 40, QUIET, a, bold=False)
    yrs = 1.4 * seg(t, T["billion"], T["billion"] + 1.0)
    text(ctx, f"−{yrs:.1f} BILLION YEARS", 540, 520, 58, SUN, a * (yrs > 0.01))


def s_monday(ctx, t):
    sky(ctx); twinkle(ctx, t, 0.4)
    t0 = T["monday"]; k = seg(t, t0, t0 + 0.25)
    # folha de calendário
    x0, y0, w, h = 240, 370, 600, 640
    ctx.save(); ctx.translate(540, 690); ctx.rotate(-0.04 * (1 - k)); ctx.scale(0.8 + 0.2 * k, 0.8 + 0.2 * k)
    ctx.translate(-540, -690)
    ctx.set_source_rgba(0.95, 0.95, 0.97, k); rr(ctx, x0, y0, w, h, 36); ctx.fill()
    ctx.set_source_rgba(*RED, k); rr(ctx, x0, y0, w, 150, 36); ctx.fill(); ctx.rectangle(x0, y0 + 110, w, 40); ctx.fill()
    text(ctx, "MONDAY", 540, y0 + 105, 84, INK, k)
    strike = seg(t, t0 + 0.6, t0 + 0.9)
    ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(170); ctx.set_source_rgba(0.12, 0.14, 0.22, k * (1 - 0.6 * strike))
    xb, yb, tw, th, _, _ = ctx.text_extents("24 h"); ctx.move_to(540 - tw / 2 - xb, y0 + 360); ctx.show_text("24 h")
    if strike > 0:
        ctx.set_source_rgba(*RED, strike); ctx.set_line_width(12)
        ctx.move_to(540 - tw / 2, y0 + 300); ctx.line_to(540 - tw / 2 + tw * strike, y0 + 300); ctx.stroke()
    n = seg(t, t0 + 0.9, t0 + 1.1)
    ctx.set_font_size(120); ctx.set_source_rgba(0.1, 0.55, 0.75, n)
    xb, yb, tw2, th, _, _ = ctx.text_extents("18 h"); ctx.move_to(540 - tw2 / 2 - xb, y0 + 540); ctx.show_text("18 h")
    ctx.restore()
    s = seg(t, T["honestly"] + 0.3, T["honestly"] + 0.45)
    if s > 0:
        ctx.save(); ctx.translate(540, 1120); ctx.rotate(-0.08); sc = 1.5 - 0.5 * s; ctx.scale(sc, sc)
        text(ctx, "−6 H OF MONDAY", 0, 0, 80, CYAN, s); ctx.restore()


def rr(ctx, x, y, w, h, r):
    ctx.new_sub_path(); ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); ctx.close_path()


def s_twist(ctx, t):
    sky(ctx); twinkle(ctx, t, 0.5)
    t0 = T["promised"]; k = seg(t, t0, t0 + 0.4)
    ex, ey, er = 280, 1500, 140
    drift = seg(t, T["leaving"], T["roughly"])
    mx, my, mr = 780 + 70 * drift, 600 - 70 * drift, 70 - 14 * drift
    earth(ctx, ex, ey, er, k, rot=t * 0.05)
    draw_moon(ctx, mx, my, L.small_moon, mr, k)
    las = seg(t, T["lasers"], T["lasers"] + 0.3)
    if las > 0:
        ctx.set_source_rgba(*GREEN, 0.25 * las); ctx.set_line_width(16)
        ctx.move_to(ex + 60, ey - 110); ctx.line_to(mx, my); ctx.stroke()
        ctx.set_source_rgba(*GREEN, 0.95 * las); ctx.set_line_width(4)
        ctx.move_to(ex + 60, ey - 110); ctx.line_to(mx, my); ctx.stroke()
        glow(ctx, mx, my, 60, GREEN, 0.5 * las)
    text(ctx, "MEASURED BY LASER", 640, 1080, 44, GREEN, seg(t, T["lasers"] + 0.3, T["lasers"] + 0.6) * (1 - seg(t, T["three8"] - 0.3, T["three8"])), bold=False)
    if t > T["three8"]:
        yrs = (t - T["three8"]) * 30
        text(ctx, f"+{yrs * 3.8:,.0f} cm", 660, 1060, 70, CYAN, seg(t, T["three8"], T["three8"] + 0.3))
        text(ctx, f"after {yrs:,.0f} years", 660, 1120, 40, QUIET, seg(t, T["three8"], T["three8"] + 0.3), bold=False)
    # o selo do loop aberto "abre" aqui
    r = seg(t, t0, t0 + 0.5)
    text(ctx, "THE STRANGEST PART", 540, 330, 64, SUN, r * (1 - seg(t, T["leaving"] + 0.8, T["leaving"] + 1.1)))


def s_finger(ctx, t):
    t0 = T["roughly"]
    paint_cover(ctx, finger, t, t0, T["question"], 1.0, 1.08)
    a = seg(t, t0 + 0.3, t0 + 0.6)
    arrow(ctx, 760, 520, 560, 690, CYAN, a)
    text(ctx, "SAME SPEED", 780, 490, 60, CYAN, a)


def s_poll(ctx, t):
    sky(ctx); twinkle(ctx, t, 0.5)
    t0 = T["question"]
    for j, (lab, l1, l2, col, yy, ic) in enumerate([("A", "1 YEAR", "WITHOUT THE MOON", CREAM, 620, "moon"),
                                                     ("B", "1 WEEK", "WITHOUT THE SUN", SUN, 980, "sun")]):
        k = seg(t, t0 + 0.4 + j * 0.25, t0 + 0.7 + j * 0.25)
        if k <= 0:
            continue
        x = 540 + (1 - k) * (600 if j else -600)
        ctx.set_source_rgba(*col, 0.12 * k); rr(ctx, x - 440, yy - 140, 880, 280, 34); ctx.fill()
        ctx.set_source_rgba(*col, 0.9 * k); ctx.set_line_width(4); rr(ctx, x - 440, yy - 140, 880, 280, 34); ctx.stroke()
        text(ctx, lab, x - 340, yy + 40, 120, col, k)
        text(ctx, l1, x + 60, yy - 10, 74, INK, k)
        text(ctx, l2, x + 60, yy + 60, 44, col, k)
        if ic == "moon":
            draw_moon(ctx, x - 340, yy - 90, L.tiny_moon, 0.01, 0)  # sem ícone extra
    v = seg(t, t0 + 0.9, t0 + 1.1)
    text(ctx, "VS", 540, 820, 70, QUIET, v)
    c = seg(t, T["tellme"], T["tellme"] + 0.2)
    bob = 12 * math.sin(t * 8)
    text(ctx, "COMMENT  A  OR  B", 500, 1180 - 0, 64, CYAN, c)
    arrow(ctx, 830, 1150, 950 + bob, 1150, CYAN, c)


def s_end(ctx, t):
    z = 1.06 - 0.06 * seg(t, T["tonight"], T_END - 0.3)
    paint_cover(ctx, L.bg, 0, 0, 1, z, z)
    twinkle(ctx, t, 0.6)
    a = seg(t, T["tonight"] + 0.1, T["tonight"] + 0.8)
    glow(ctx, MX, MY, MOON_R * 1.9, CREAM, 0.22 * a)
    draw_moon(ctx, MX, MY, L.moon, MOON_R * (0.9 + 0.1 * a), a)


SCENES = [(0, s_countdown, "cut"), (T["light"], s_light, "zoom"), (T["after"], s_strange, "circle"),
          (T["tides"], s_tides, "push"), (T["sea"], s_sealevel, "zoom"), (T["surfers"], s_surfer, "push"),
          (T["easy"], s_phases, "circle"), (T["wolves"], s_wolf, "zoom"), (T["animals"], s_reef, "push"),
          (T["weirder"], s_time, "circle"), (T["monday"], s_monday, "zoom"),
          (T["promised"], s_twist, "circle"),
          (T["roughly"], s_finger, "push"), (T["question"], s_poll, "zoom"), (T["tonight"], s_end, "circle")]
SCENES = [(a, (SCENES[i + 1][0] if i + 1 < len(SCENES) else T_END + 1), fn, tr) for i, (a, fn, tr) in enumerate(SCENES)]

PUNCH = [SHATTER, T["half"], T["surfers"], T["nofull"], T["wolves"], T["nosignal"],
         T["eighteen"], T["honestly"], T["leaving"], T["three8"], T["last13"]]
TRANS = 0.28


def punch(t):
    v = 0
    for p in PUNCH:
        x = t - p
        if 0 <= x < 0.45:
            v = max(v, math.sin(min(1, x / 0.08) * math.pi / 2) * (1 - x / 0.45))
    return 1 + 0.045 * v


def badge(ctx, t):
    """selo do loop aberto: visível entre 'strangest' e a revelação"""
    a = seg(t, T["strangest"] + 0.4, T["strangest"] + 0.8) * (1 - seg(t, T["promised"] - 0.3, T["promised"]))
    if a <= 0.01:
        return
    w_, h_ = 760, 84; x, y = 540 - w_ / 2, 210
    ctx.set_source_rgba(0.02, 0.04, 0.1, 0.75 * a); rr(ctx, x, y, w_, h_, 35); ctx.fill()
    ctx.set_source_rgba(*SUN, 0.9 * a); ctx.set_line_width(3); rr(ctx, x, y, w_, h_, 35); ctx.stroke()
    pulse = 0.5 + 0.5 * math.sin(t * 5)
    ctx.set_source_rgba(*SUN, a * (0.4 + 0.6 * pulse)); ctx.arc(x + 42, y + h_ / 2, 11, 0, 6.283); ctx.fill()
    text(ctx, "THE STRANGEST PART · COMING UP", x + 76, y + 55, 38, SUN, a, "l")


def alarm(ctx, t):
    """gancho: bordas vermelhas a piscar ao ritmo do alarme (0 no frame 0, para o loop bater certo)"""
    if t >= SHATTER:
        return
    p = 0.5 - 0.5 * math.cos(2 * math.pi * t / ALARM_P)
    a = 0.62 * p
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.62)
    g.add_color_stop_rgba(0, *RED, 0); g.add_color_stop_rgba(1, *RED, a)
    ctx.set_source(g); ctx.paint()
    ctx.set_source_rgba(*RED, 0.9 * p); ctx.set_line_width(18); ctx.rectangle(9, 9, W - 18, H - 18); ctx.stroke()


ALARM_P = 0.5  # período do alarme (s): tom alto + tom baixo


def render(fn, t):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_BEST)
    c.set_source_rgb(*NAVY); c.paint(); fn(c, t)
    return s


def frame(t):
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(out)
    for i, (a, b, fn, tr) in enumerate(SCENES):
        if a <= t < b:
            cur = render(fn, t)
            x = (t - a) / TRANS
            if i > 0 and x < 1 and tr != "cut":
                prev = render(SCENES[i - 1][2], t)
                e = ease(x)
                if tr == "push":  # empurra a cena anterior para a esquerda
                    ctx.set_source_surface(prev, -W * e, 0); ctx.paint()
                    ctx.set_source_surface(cur, W * (1 - e), 0); ctx.paint()
                elif tr == "zoom":  # a nova cena cresce sobre a anterior
                    ctx.set_source_surface(prev, 0, 0); ctx.paint()
                    z = 1.25 - 0.25 * e
                    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2)
                    ctx.set_source_surface(cur, 0, 0); ctx.paint_with_alpha(e); ctx.restore()
                else:  # circle: revelação circular a partir do centro
                    ctx.set_source_surface(prev, 0, 0); ctx.paint()
                    ctx.save(); ctx.arc(W / 2, H / 2, 1150 * e, 0, 6.283); ctx.clip()
                    ctx.set_source_surface(cur, 0, 0); ctx.paint(); ctx.restore()
            else:
                ctx.set_source_surface(cur, 0, 0); ctx.paint()
            break
    alarm(ctx, t)
    badge(ctx, t)
    # punch-zoom final sobre o frame composto
    z = punch(t)
    if z > 1.0005:
        fin = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c2 = cairo.Context(fin)
        c2.translate(W / 2, H / 2); c2.scale(z, z); c2.translate(-W / 2, -H / 2)
        c2.set_source_surface(out, 0, 0); c2.paint(); out = fin
    return np.ndarray((H, W, 4), np.uint8, out.get_data())[:, :, [2, 1, 0]].tobytes()


# ---------- legendas ----------
WEAK = {"a", "an", "the", "to", "of", "for", "on", "in", "it", "its", "and", "but", "with", "our", "their",
        "that", "is", "as", "be", "would", "could", "you'd", "if", "about", "only", "every", "no", "so",
        "there's", "here's", "because", "without", "over", "far", "more", "your", "we've", "or", "one"}


def bare(w):
    return re.sub(r"[^\w'.]", "", w).lower()


groups, cur = [], []
for w in words:
    cand = cur + [w]
    if cur and (len(cand) > 3 or len(" ".join(x["w"] for x in cand)) > 18):
        last = bare(cur[-1]["w"])
        if len(cur) > 1 and (last in WEAK or re.fullmatch(r"\d+(\.\d+)?", last)):
            carry = cur.pop(); groups.append(cur); cur = [carry, w]
        else:
            groups.append(cur); cur = [w]
    else:
        cur = cand
    if re.search(r"[.,?!]$", w["w"]) and not re.fullmatch(r"\d+(\.\d+)?", w["w"]):
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
        pop = "{\\fscx108\\fscy108\\t(0,90,\\fscx100\\fscy100)}" if k == 0 else ""
        txt = " ".join((f"{{\\c{CY}}}{x['w'].upper()}{{\\c{WH}}}" if j == k else x["w"].upper()) for j, x in enumerate(g))
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},Cap,,0,0,0,,{pop}{txt}")
facts = [(T["eighteen"], T["monday"] - 0.1, "18-HOUR DAYS"),
         (T["three8"], T["roughly"] - 0.1, "3.8 CM / YEAR")]
ev += [f"Dialogue: 1,{ts(a)},{ts(b)},Fact,,0,0,0,,{{\\fad(120,150)}}{x}" for a, b, x in facts]
ev += [f"Dialogue: 2,{ts(0)},{ts(T_END)},Mark,,0,0,0,,@whatifaholics"]
open(f"{A}/v6_captions.ass", "w").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,90,90,640,1
Style: Title,Inter Display,104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,8,4,8,80,80,330,1
Style: Tag,Inter Display,38,&H00FFE03D,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,6,0,1,3,0,8,80,80,200,1
Style: Fact,Inter Display,120,&H00FFE03D,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,2,0,1,8,4,8,80,80,420,1
Style: Mark,Inter Display,40,&H8CFFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,3,0,7,60,60,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n")

if __name__ == "__main__":
    raw = f"{A}/v6_raw.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                          "-pix_fmt", "yuv420p", raw], stdin=subprocess.PIPE)
    for i in range(int(T_END * FPS)):
        p.stdin.write(frame(i / FPS))
    p.stdin.close(); p.wait()

    # som: swish suave só nos capítulos, pops leves nos números, ding curto nas piadas
    def synth(name, expr, d):
        path = f"{BLD}/{name}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={d}", path], check=True)
        return path
    swish = f"{BLD}/swish.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.5:c=pink:a=0.5:r=48000",
                    "-af", "bandpass=f=900:w=1400,afade=t=in:d=0.25:curve=qsin,afade=t=out:st=0.25:d=0.25,volume=0.35",
                    swish], check=True)
    pop = synth("pop_soft", "0.5*sin(2*PI*(260+500*exp(-t*35))*t)*exp(-t*22)", 0.2)
    ding = synth("ding", "0.35*(sin(2*PI*1320*t)+0.5*sin(2*PI*1980*t))*exp(-t*9)", 0.6)
    events = [(swish, c - 0.25, 0.5) for c in (T["tides"], T["weirder"], T["promised"], T["question"])]
    # alarme de emergência de dois tons (alto/baixo) até a Lua estilhaçar
    P = ALARM_P; h = P / 2
    env = f"min(1,mod(t,{h})*120)*min(1,({h}-mod(t,{h}))*120)"
    tone = f"(lt(mod(t,{P}),{h})*(sin(2*PI*960*t)+0.3*sin(2*PI*2880*t))+gte(mod(t,{P}),{h})*(sin(2*PI*770*t)+0.3*sin(2*PI*2310*t)))"
    alarm_wav = f"{BLD}/alarm.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"aevalsrc='0.45*{env}*{tone}':s=48000:d={SHATTER:.3f}",
                    "-af", f"afade=t=out:st={max(0, SHATTER - 0.06):.3f}:d=0.06", alarm_wav], check=True)
    events += [(alarm_wav, 0.0, 0.32)]
    boom = f"{BLD}/boom.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "aevalsrc='0.9*sin(2*PI*(48+70*exp(-t*6))*t)*exp(-t*2.8)':s=48000:d=1.6",
                    "-f", "lavfi", "-i", "anoisesrc=d=0.4:c=brown:a=0.8:r=48000",
                    "-filter_complex", "[1]afade=t=out:d=0.4,lowpass=f=900[n];[0][n]amix=inputs=2:normalize=0,volume=0.9",
                    boom], check=True)
    tick = synth("tick", "0.45*sin(2*PI*2200*t)*exp(-t*90)", 0.06)
    events += [(boom, SHATTER - 0.02, 0.9)]
    events += [(pop, x, 0.5) for x in (T["half"], T["eighteen"], T["three8"], T["last13"])]
    events += [(ding, x, 0.35) for x in (T["devastated"], T["unemployed"], T["honestly"] + 0.3, T["grow"])]
    ins, ch, lab = [], [], []
    for n, (f, x, v) in enumerate(events):
        idx = 3 + n; ins += ["-i", f]; d = int(max(0, x) * 1000)
        ch.append(f"[{idx}:a]adelay={d}|{d},volume={v}[e{n}]"); lab.append(f"[e{n}]")
    sfx = ";".join(ch) + ";" + "".join(lab) + f"amix=inputs={len(lab)}:normalize=0[sfx]"
    pre = T["promised"]  # silêncio de música antes da revelação
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", NARR, "-stream_loop", "-1", "-i", MUSIC, *ins,
                    "-filter_complex",
                    f"[0:v]noise=alls=3:allf=t,subtitles={A}/v6_captions.ass,format=yuv420p[v];"
                    "[1:a]asplit=2[n1][nk];"
                    f"[2:a]atrim=0:{T_END},volume='if(lt(t,{SHATTER + 0.35:.2f}),0,if(between(t,{pre-0.6:.2f},{pre+0.1:.2f}),0.08,0.35))':eval=frame,"
                    f"afade=t=out:st={T_END-1.5}:d=1.5[m];"
                    "[m][nk]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[md];"
                    f"{sfx};[n1][md][sfx]amix=inputs=3:duration=longest:normalize=0,apad,"
                    f"loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{T_END}[a]",
                    "-map", "[v]", "-map", "[a]", "-t", str(T_END), "-r", str(FPS),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-maxrate", "8M", "-bufsize", "16M",
                    "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", OUT], check=True)
    print("OK", OUT, T_END)
