#!/usr/bin/env python3
"""Whatifaholic #003: What if you farted in a spacesuit? Animação por código (pycairo) sobre 5 ilustrações.
Gancho: "pffrrt" sintetizado no frame 1 (sem sirene), medidor SMELL LEVEL até ao vermelho; a narração entra depois."""
import math, random, re, json, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cairo
import numpy as np
import neuro_lib as L
from neuro_lib import (W, H, FPS, A, BLD, NAVY, CYAN, CREAM, SUN, INK, PINK, QUIET, GREEN, RED,
                       seg, ease, Cover, glow, text, rr, pop_in)

ROOT = os.path.dirname(os.path.abspath(__file__))
NARR = f"{ROOT}/audio/narration.wav"
MUSIC = f"{ROOT}/../music/track01_cosmic_ambient.mp3"
OUT = f"{ROOT}/whatifaholic_ep003_spacesuit.mp4"
OFF = 0.95  # a narração entra só depois do "pffrrt" (0,85 s)
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "csv=p=0", NARR]))
T_END = round(OFF + dur + 0.6, 2)
random.seed(3)

REF = L.surf(f"{A}/astro_ref.png"); HELM = L.surf(f"{A}/helmet.png"); INSIDE = L.surf(f"{A}/inside.png")
ORBIT = L.surf(f"{A}/orbit.png"); STATION = L.surf(f"{A}/station.png")
DARK = (0.12, 0.22, 0.10); LIME = (0.62, 0.95, 0.35)

# ---------- palavras ----------
words = json.load(open(f"{BLD}/words_ep003.json"))
for w in words:
    w["s"] = round(w["s"] + OFF, 3); w["e"] = round(w["e"] + OFF, 3)


def clean(w):
    return re.sub(r"[^\w']", "", w).lower()


def at(phrase, after=0.0, end=False):
    toks = phrase.lower().split(); cl = [clean(w["w"]) for w in words]
    for i in range(len(words) - len(toks) + 1):
        if words[i]["s"] >= after and all(cl[i + j] == toks[j] for j in range(len(toks))):
            return words[i + len(toks) - 1]["e"] if end else words[i]["s"]
    raise KeyError(phrase)


T = dict(
    suit_end=at("spacesuit", end=True), nowhere=at("nowhere"), first=at("first problem"),
    earth=at("on earth"), rises=at("rises"), drifts=at("drifts"), space=at("in space"), noup=at("no up"),
    floats=at("it just floats"), face=at("face"), second=at("second problem"), hold=at("hold"), nose=at("nose"),
    hands=at("your hands"), gloves=at("giant gloves"), glass=at("behind glass"), glass_e=at("glass", end=True),
    wait=at("but wait"), push=at("push you"), rocket=at("tiny rocket"), tech=at("technically"), yes=at("yes"),
    real=at("realistically"), snail=at("snail"), battery=at("battery"), battery_e=at("battery", end=True),
    scary=at("now the scary"), hydrogen=at("hydrogen"), methane=at("methane"), burn=at("can burn"),
    nasa=at("early nasa"), worried=at("worried"), so=at("so no sparks"), sparks=at("sparks"), please=at("please"),
    please_e=at("please", end=True), good=at("the good news"), filters=at("filters"), charcoal=at("activated charcoal"),
    slowly1=at("that slowly"), smell=at("smell away"), slowA=at("slowly", after=at("smell away")),
    very=at("very slowly"), very_e=at("very slowly", end=True), question=at("would you rather"),
    own=at("your own"), station=at("space station"), tell=at("tell me below"), because=at("because you just"),
)
T["slowA"] = at("slowly", after=T["smell"] + 0.1)
REWARD = T["suit_end"] + 0.05          # medidor chega ao vermelho no fim de "spacesuit."
POP_T = T["very_e"] + 0.08             # pop-up de subscrição logo a seguir a "Very… slowly"


# ---------- desenhos por código ----------
def cloud(ctx, x, y, r, a, t, face=True, seed=0):
    """nuvem verde estilizada com cara de gozo"""
    if a <= 0.01 or r < 2:
        return
    glow(ctx, x, y, r * 1.9, LIME, 0.28 * a)
    puffs = [(-0.55, 0.15, 0.55), (0.0, -0.25, 0.68), (0.55, 0.1, 0.58), (-0.25, 0.35, 0.5), (0.3, 0.38, 0.5)]
    ctx.save()
    for i, (px, py, pr) in enumerate(puffs):
        wob = 1 + 0.06 * math.sin(t * 5 + i * 1.7 + seed)
        ctx.new_sub_path(); ctx.arc(x + px * r, y + py * r, pr * r * wob, 0, 6.283)
    ctx.set_source_rgba(*DARK, 0.85 * a); ctx.set_line_width(max(3, r * 0.09)); ctx.stroke_preserve()
    ctx.set_source_rgba(*LIME, 0.92 * a); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35 * a); ctx.arc(x - 0.2 * r, y - 0.45 * r, 0.18 * r, 0, 6.283); ctx.fill()
    if face and r > 25:
        ctx.set_source_rgba(*DARK, a)
        for sx in (-0.22, 0.22):  # olhos meio fechados (ar de gozo)
            ctx.save(); ctx.translate(x + sx * r, y + 0.02 * r); ctx.scale(1, 0.55)
            ctx.arc(0, 0, 0.08 * r, 0, 6.283); ctx.restore(); ctx.fill()
        ctx.set_line_width(max(2.5, r * 0.06)); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.arc(x + 0.05 * r, y + 0.12 * r, 0.2 * r, 0.25, math.pi - 0.6); ctx.stroke()
    # linhas de cheiro onduladas
    ctx.set_source_rgba(*LIME, 0.7 * a); ctx.set_line_width(max(2, r * 0.05))
    for k in (-1, 0, 1):
        bx = x + k * 0.45 * r; by = y - 0.95 * r
        ctx.move_to(bx, by)
        for j in range(1, 9):
            ctx.line_to(bx + 0.08 * r * math.sin(j * 1.2 + t * 6 + k), by - j * 0.06 * r)
        ctx.stroke()
    ctx.restore()


def glove(ctx, x, y, s, ang=0.0, a=1.0):
    """luva gigante branca com punho ciano (dedos para cima)"""
    if a <= 0.01:
        return
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.scale(s, s)
    ctx.set_source_rgba(0, 0, 0, 0.25 * a); rr(ctx, -78, -96, 170, 210, 70); ctx.fill()
    ctx.set_source_rgba(0.97, 0.98, 1, a); rr(ctx, -85, -110, 170, 210, 70); ctx.fill()
    ctx.save(); ctx.translate(-92, 0); ctx.rotate(-0.5); ctx.scale(1, 1.7); ctx.arc(0, 0, 32, 0, 6.283); ctx.restore(); ctx.fill()
    ctx.set_source_rgba(0.78, 0.84, 0.93, a); ctx.set_line_width(5)
    for fx in (-30, 10, 48):
        ctx.move_to(fx, -100); ctx.line_to(fx, -40); ctx.stroke()
    ctx.set_source_rgba(*CYAN, a); rr(ctx, -80, 80, 160, 60, 18); ctx.fill()
    ctx.set_source_rgba(0.1, 0.5, 0.6, a); ctx.set_line_width(4); rr(ctx, -80, 80, 160, 60, 18); ctx.stroke()
    ctx.restore()


def flame(ctx, x, y, s, t, a=1.0):
    if a <= 0.01:
        return
    f = 1 + 0.12 * math.sin(t * 23) + 0.06 * math.sin(t * 37)
    for col, k in (((1.0, 0.45, 0.15), 1.0), ((1.0, 0.8, 0.25), 0.62), ((1, 0.97, 0.8), 0.3)):
        ctx.save(); ctx.translate(x, y); ctx.scale(s * k, s * k * f)
        ctx.move_to(0, -34); ctx.curve_to(16, -14, 22, 0, 18, 12); ctx.curve_to(14, 24, -14, 24, -18, 12)
        ctx.curve_to(-22, 0, -10, -10, 0, -34); ctx.close_path(); ctx.restore()
        ctx.set_source_rgba(*col, a); ctx.fill()


def snail(ctx, x, y, s, t, a=1.0):
    """caracol com bateria fraca"""
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.set_source_rgba(0.80, 0.86, 0.95, a)  # corpo
    ctx.move_to(-90, 30); ctx.curve_to(-60, 50, 80, 50, 110, 30); ctx.curve_to(120, 10, 100, -10, 90, -10)
    ctx.line_to(-80, 10); ctx.close_path(); ctx.fill()
    ctx.set_line_width(6); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for ex, ey in ((95, -55), (120, -45)):  # antenas
        ctx.move_to(98, -8); ctx.line_to(ex, ey + 4 * math.sin(t * 3 + ex)); ctx.stroke()
        ctx.arc(ex, ey + 4 * math.sin(t * 3 + ex), 8, 0, 6.283); ctx.fill()
    ctx.set_source_rgba(*SUN, a); ctx.arc(0, -20, 62, 0, 6.283); ctx.fill()  # concha
    ctx.set_source_rgba(0.75, 0.45, 0.15, a); ctx.set_line_width(7)
    for i in range(60):
        ang = i * 0.22; r = 6 + i * 0.9
        (ctx.move_to if i == 0 else ctx.line_to)(r * math.cos(ang), -20 + r * math.sin(ang))
    ctx.stroke()
    # bateria fraca a piscar
    bx, by = -40, -150
    ctx.set_source_rgba(*INK, a); ctx.set_line_width(6); rr(ctx, bx, by, 90, 44, 8); ctx.stroke()
    ctx.rectangle(bx + 90, by + 13, 9, 18); ctx.fill()
    blink = 0.35 + 0.65 * (math.sin(t * 9) > 0)
    ctx.set_source_rgba(*RED, a * blink); ctx.rectangle(bx + 8, by + 8, 16, 28); ctx.fill()
    ctx.restore()


def spark(ctx, x, y, s, t, a=1.0):
    if a <= 0.01:
        return
    glow(ctx, x, y, 90 * s, SUN, 0.6 * a)
    ctx.save(); ctx.translate(x, y); ctx.rotate(t * 7); ctx.scale(s, s)
    n = 8
    ctx.move_to(0, -50)
    for i in range(1, 2 * n + 1):
        r = 50 if i % 2 == 0 else 16 + 6 * math.sin(t * 50 + i)
        ang = -math.pi / 2 + i * math.pi / n
        ctx.line_to(r * math.cos(ang), r * math.sin(ang))
    ctx.close_path(); ctx.set_source_rgba(1, 0.95, 0.5, a); ctx.fill_preserve()
    ctx.set_source_rgba(1, 0.6, 0.1, a); ctx.set_line_width(4); ctx.stroke()
    ctx.restore()


def chip(ctx, s, x, y, col=CYAN, a=1.0, size=40):
    if a <= 0.01:
        return
    ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(size)
    tw = ctx.text_extents(s)[2]; w_, h_ = tw + 60, size * 1.9
    ctx.set_source_rgba(0.02, 0.04, 0.1, 0.78 * a); rr(ctx, x - w_ / 2, y - h_ / 2, w_, h_, h_ / 2); ctx.fill()
    ctx.set_source_rgba(*col, 0.95 * a); ctx.set_line_width(4); rr(ctx, x - w_ / 2, y - h_ / 2, w_, h_, h_ / 2); ctx.stroke()
    text(ctx, s, x, y + size * 0.36, size, col, a)


def ring(ctx, x, y, t, t0, col=INK, maxr=140):
    u = (t - t0) / 0.45
    if 0 <= u <= 1:
        ctx.set_source_rgba(*col, 0.8 * (1 - u)); ctx.set_line_width(7 * (1 - u) + 1)
        ctx.arc(x, y, 20 + maxr * ease(u), 0, 6.283); ctx.stroke()


def meter(ctx, x, y, w, h, v, a, t, label="SMELL LEVEL"):
    """barra segmentada verde → amarelo → vermelho"""
    if a <= 0.01:
        return
    ctx.set_source_rgba(0.02, 0.04, 0.1, 0.8 * a); rr(ctx, x - 16, y - 70, w + 32, h + 92, 22); ctx.fill()
    text(ctx, label, x, y - 22, 38, INK, a, "l")
    text(ctx, f"{int(round(v * 100))}%", x + w, y - 22, 38, RED if v > 0.8 else SUN if v > 0.5 else LIME, a, "r")
    n = 14
    for i in range(n):
        q = (i + 0.5) / n
        col = LIME if q < 0.45 else SUN if q < 0.75 else RED
        on = q <= v
        fl = 1.0 if not (on and v >= 0.99) else 0.55 + 0.45 * (math.sin(t * 30) > 0)
        ctx.set_source_rgba(*col, a * (0.95 * fl if on else 0.15))
        sw = w / n
        rr(ctx, x + i * sw + 3, y, sw - 6, h, 6); ctx.fill()


# ---------- cenas ----------
def ref_cover(ctx, t, z=1.0, fx=None, fy=None, rot=0.0, sx=W / 2, sy=H / 2):
    return Cover(ctx, REF, z, fx, fy, sx, sy, rot)


HX, HY = 875, 710  # capacete em astro_ref.png


def s_hook(ctx, t):
    """0 s: astronauta calmo → 'pffrrt' → medidor até ao vermelho → nuvem rebenta"""
    jolt = 14 * math.exp(-t * 9) * math.sin(t * 70) if t < 0.6 else 0
    k = seg(t, 0.15, REWARD + 0.6)
    z = 1.0 + 0.22 * k
    fx = 768 + (HX - 768) * k; fy = 1376 + (HY + 120 - 1376) * k
    flail = 0.0
    if t > T["nowhere"] - 0.1:
        flail = 0.035 * math.sin((t - T["nowhere"]) * 22) * (1 - seg(t, T["first"] - 0.3, T["first"]))
    ctx.save(); ctx.translate(jolt, 0)
    c = ref_cover(ctx, t, z, fx, fy, flail)
    ctx.restore()
    hx, hy = c.p(HX, HY); hr = c.r(170)
    # baforada pequena (atrás) que cresce até à recompensa, depois rebenta à volta do capacete
    if t < REWARD:
        g = seg(t, 0.05, REWARD)
        bx, by = c.p(HX - 260 + 150 * g, HY + 470 - 330 * g)
        cloud(ctx, bx, by, 30 + 70 * g, seg(t, 0.03, 0.15), t, face=g > 0.4)
    else:
        u = t - REWARD
        r = hr * (1.25 + 0.5 * math.exp(-u * 4) * math.cos(u * 14) * 0.6)
        ang = u * 2.2
        cloud(ctx, hx + 0.9 * hr * math.cos(ang), hy + 0.35 * hr * math.sin(ang) + 30, r * 0.55, 1, t)
        glow(ctx, hx, hy, hr * 4, LIME, 0.75 * math.exp(-u * 5))
    if t > T["nowhere"]:  # linhas de pânico
        a = seg(t, T["nowhere"], T["nowhere"] + 0.2) * (1 - seg(t, T["first"] - 0.3, T["first"]))
        ctx.set_source_rgba(*INK, 0.8 * a); ctx.set_line_width(6); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(5):
            ang = -2.6 + i * 0.35; j = 8 * math.sin(t * 30 + i)
            ctx.move_to(hx + (hr + 30 + j) * math.cos(ang), hy + (hr + 30 + j) * math.sin(ang))
            ctx.line_to(hx + (hr + 80 + j) * math.cos(ang), hy + (hr + 80 + j) * math.sin(ang)); ctx.stroke()
    # painel de alerta + medidor (sem nada no frame 0, para o loop)
    a = seg(t, 0.12, 0.3) * (1 - seg(t, T["first"] - 0.35, T["first"] - 0.05))
    v = min(1.0, seg(t, 0.25, REWARD) ** 0.8) if t < REWARD else 1.0
    if a > 0.01:
        blink = 0.6 + 0.4 * (math.sin(t * 2 * math.pi / ALARM_P) > 0) if t < REWARD else 1.0
        ctx.set_source_rgba(0.25, 0.02, 0.02, 0.85 * a); rr(ctx, 120, 240, 840, 96, 30); ctx.fill()
        ctx.set_source_rgba(*RED, a * blink); ctx.set_line_width(5); rr(ctx, 120, 240, 840, 96, 30); ctx.stroke()
        # triângulo de aviso
        ctx.move_to(178, 268); ctx.line_to(208, 318); ctx.line_to(148, 318); ctx.close_path()
        ctx.set_source_rgba(*SUN, a * blink); ctx.fill()
        text(ctx, "!", 178, 314, 36, NAVY, a, bold=True)
        text(ctx, "SUIT ALERT · AIR QUALITY", 560, 306, 46, INK, a)
        meter(ctx, 150, 440, 780, 54, v, a, t)
        if t >= REWARD:
            sc = pop_in(t, REWARD, 0.3)
            ctx.save(); ctx.translate(540, 640); ctx.rotate(-0.12); ctx.scale(sc, sc)
            ctx.set_source_rgba(*RED, 0.9 * a); ctx.set_line_width(10); rr(ctx, -250, -70, 500, 120, 20); ctx.stroke()
            text(ctx, "MAX!", 0, 28, 110, RED, a)
            ctx.restore()


def inset_card(ctx, t, a):
    """cartão 'ON EARTH' (a nuvem sobe e vai-se embora) → 'IN SPACE' (sem cima)"""
    if a <= 0.01:
        return
    x, y, w_, h_ = 650, 700, 380, 470
    ctx.set_source_rgba(0.02, 0.04, 0.1, 0.82 * a); rr(ctx, x, y, w_, h_, 34); ctx.fill()
    ctx.set_source_rgba(*CYAN, 0.9 * a); ctx.set_line_width(4); rr(ctx, x, y, w_, h_, 34); ctx.stroke()
    ctx.save(); rr(ctx, x, y, w_, h_, 34); ctx.clip()
    space = seg(t, T["space"] - 0.1, T["space"] + 0.2)
    if space < 1:
        ea = a * (1 - space)
        text(ctx, "ON EARTH", x + w_ / 2, y + 66, 44, SUN, ea)
        ctx.set_source_rgba(0.25, 0.55, 0.35, ea); ctx.rectangle(x, y + h_ - 70, w_, 70); ctx.fill()
        u = max(0, t - T["rises"] + 0.2)
        cy_ = y + h_ - 120 - 170 * u; cx_ = x + w_ / 2 + 70 * max(0, t - T["drifts"])
        cloud(ctx, cx_, cy_, 50, ea * max(0, 1 - max(0, t - T["drifts"]) * 0.7), t, face=True, seed=2)
        ctx.set_source_rgba(*SUN, ea); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ax = x + 60; ctx.move_to(ax, y + h_ - 110); ctx.line_to(ax, y + 150); ctx.stroke()
        ctx.move_to(ax - 22, y + 175); ctx.line_to(ax, y + 150); ctx.line_to(ax + 22, y + 175); ctx.stroke()
    if space > 0:
        sa = a * space
        text(ctx, "IN SPACE", x + w_ / 2, y + 66, 44, CYAN, sa)
        cx_, cy_ = x + w_ / 2, y + h_ / 2 + 40
        ctx.set_source_rgba(*CYAN, sa); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(4):
            ang = t * 2.5 + i * math.pi / 2
            ex, ey = cx_ + 130 * math.cos(ang), cy_ + 130 * math.sin(ang)
            ctx.move_to(cx_ + 40 * math.cos(ang), cy_ + 40 * math.sin(ang)); ctx.line_to(ex, ey); ctx.stroke()
            for s in (-1, 1):
                ctx.move_to(ex, ey); ctx.line_to(ex - 26 * math.cos(ang + s * 0.5), ey - 26 * math.sin(ang + s * 0.5)); ctx.stroke()
        q = pop_in(t, T["noup"], 0.3)
        if q > 0:
            text(ctx, "UP = ?", cx_, y + h_ - 40, 58 * q, INK, sa)
    ctx.restore()


def s_earth(ctx, t):
    c = ref_cover(ctx, t, 1.15 + 0.05 * seg(t, T["first"], T["space"]), 760, 1000, sx=330, sy=H / 2)
    hx, hy = c.p(HX, HY)
    ang = (t - T["first"]) * 1.4
    cloud(ctx, hx - 40 + 150 * math.cos(ang), hy + 60 + 50 * math.sin(ang), 70, 1, t)
    chip(ctx, "PROBLEM 1 · IT STAYS", 540, 400, CYAN, seg(t, T["first"], T["first"] + 0.25))
    inset_card(ctx, t, seg(t, T["earth"] - 0.2, T["earth"] + 0.1))


GX, GY, GR = 768, 1100, 600  # capacete em helmet.png


def s_face(ctx, t):
    """'it just floats… around your face': nuvem em órbita à volta do capacete, cada vez mais perto"""
    z = 1.0 + 0.08 * seg(t, T["space"], T["second"])
    c = Cover(ctx, HELM, z, GX, GY, W / 2, 800)
    hx, hy = c.p(GX, GY); hr = c.r(GR)
    close = seg(t, T["floats"], T["face"])
    ang = (t - T["space"]) * (1.6 + 1.2 * close)
    rx = hr * (1.15 - 0.55 * close); ry = hr * (0.5 - 0.25 * close)
    front = math.sin(ang) > 0
    r = 80 + 40 * close + 18 * math.sin(ang)
    cloud(ctx, hx + rx * math.cos(ang), hy + 40 + ry * math.sin(ang), r, 0.75 + 0.25 * front, t)
    q = pop_in(t, T["face"], 0.3)
    if q > 0:
        ctx.save(); ctx.translate(540, 330); ctx.scale(q, q); chip(ctx, "AROUND YOUR FACE", 0, 0, LIME, 1, 52); ctx.restore()


def s_gloves(ctx, t):
    """luvas gigantes a bater no vidro ('toc')"""
    hits = [T["hold"] + 0.1, T["nose"] + 0.15, T["gloves"] + 0.25]
    shake = 0
    for hT in hits:
        u = t - hT
        if 0 <= u < 0.3:
            shake = max(shake, 10 * (1 - u / 0.3))
    c = Cover(ctx, HELM, 1.12, GX, GY + 60, W / 2 + shake * math.sin(t * 80), 800)
    hx, hy = c.p(GX, GY); hr = c.r(GR)
    cloud(ctx, hx - 120 + 20 * math.sin(t * 2), hy + 140 + 15 * math.cos(t * 2.4), 70, 1, t)
    chip(ctx, "PROBLEM 2 · CAN'T HOLD YOUR NOSE", 540, 330, CYAN, seg(t, T["second"], T["second"] + 0.25), 38)
    # luva que entra por baixo e bate no vidro, à vez esquerda/direita
    for i, hT in enumerate(hits):
        side = -1 if i % 2 == 0 else 1
        u = t - (hT - 0.35)
        if -0.05 < u < 0.9:
            go = ease(u / 0.35) if u < 0.35 else 1 - 0.25 * ease((u - 0.35) / 0.2) if u < 0.55 else 0.75 * (1 - ease((u - 0.55) / 0.35))
            gx = hx + side * (hr * 0.62); gy = hy + hr * 0.35 + 600 * (1 - go)
            glove(ctx, gx, gy, 1.25 if i == 2 else 1.0, side * 0.35, 1)
            ring(ctx, hx + side * hr * 0.5, hy + hr * 0.2, t, hT, INK)
            if 0 <= t - hT < 0.5:
                text(ctx, "TOC", hx + side * hr * 0.55, hy - hr * 0.05, 64, INK, 1 - (t - hT) / 0.5)
    # 'Behind glass.': brilho a varrer o vidro
    u = seg(t, T["glass"], T["glass"] + 0.5)
    if 0 < u < 1:
        ctx.save(); ctx.arc(hx, hy, hr * 0.98, 0, 6.283); ctx.clip()
        bx = hx - hr * 1.3 + 2.6 * hr * u
        g = cairo.LinearGradient(bx - 90, 0, bx + 90, 0)
        g.add_color_stop_rgba(0, 1, 1, 1, 0); g.add_color_stop_rgba(0.5, 1, 1, 1, 0.55); g.add_color_stop_rgba(1, 1, 1, 1, 0)
        ctx.set_source(g); ctx.rotate(0.0); ctx.rectangle(bx - 90, hy - hr, 180, 2 * hr); ctx.fill(); ctx.restore()
    q = pop_in(t, T["glass"], 0.3)
    if q > 0:
        ctx.save(); ctx.translate(540, 470); ctx.scale(q, q); chip(ctx, "BEHIND GLASS", 0, 0, INK, 1, 48); ctx.restore()


def s_rocket(ctx, t):
    """mini-propulsão: avança 1 cm e um caracol com bateria fraca ultrapassa-o"""
    move = seg(t, T["yes"], T["yes"] + 0.4)
    c = Cover(ctx, ORBIT, 1.15, 538 - 12 * move, 1265, 380, 900)
    ax, ay = c.p(538 + 12 * move, 1265)  # o astronauta é parte da imagem; aqui só o 'centro'
    ax, ay = c.p(538, 1265)
    chip(ctx, "TINY ROCKET?", 540, 360, SUN, seg(t, T["rocket"] - 0.1, T["rocket"] + 0.15), 50)
    # baforadas de propulsão atrás (à esquerda)
    if T["push"] - 0.1 < t < T["real"] + 0.5:
        for i in range(5):
            ph = ((t - T["push"]) * 1.6 + i / 5) % 1
            a = (1 - ph) * seg(t, T["push"] - 0.1, T["push"] + 0.2) * (1 - seg(t, T["real"], T["real"] + 0.5))
            cloud(ctx, ax - 120 - 220 * ph, ay + 60 + 25 * math.sin(i * 2), 26 + 30 * ph, a * 0.9, t, face=False, seed=i)
    # régua "+1 cm"
    q = pop_in(t, T["yes"], 0.3) * (1 - seg(t, T["snail"] + 0.6, T["snail"] + 0.9))
    if q > 0.01:
        ctx.set_source_rgba(*CYAN, q); ctx.set_line_width(5)
        y0 = ay + 210
        ctx.move_to(ax - 30, y0); ctx.line_to(ax + 30, y0); ctx.stroke()
        for xx in (ax - 30, ax + 30):
            ctx.move_to(xx, y0 - 16); ctx.line_to(xx, y0 + 16); ctx.stroke()
        text(ctx, "+1 cm", ax, y0 + 70, 56 * q, CYAN, 1)
    # caracol a ultrapassar
    u = seg(t, T["real"] + 0.1, T["battery_e"] + 0.2)
    if t > T["real"]:
        sx = -200 + (W + 150) * (u * 0.85 + 0.15 * min(1, max(0, (t - T["battery_e"]) * 0.1)))
        snail(ctx, sx, ay + 420, 1.15, t, 1)
        text(ctx, "LOW BATTERY", sx, ay + 230, 34, RED, seg(t, T["battery"] - 0.1, T["battery"] + 0.2))


def s_scary(ctx, t):
    """hidrogénio e metano (com chamas), engenheiros preocupados, faísca apagada à pressa"""
    c = Cover(ctx, HELM, 1.0 + 0.06 * seg(t, T["scary"], T["good"]), GX, GY, W / 2, 820)
    pulse = 0.5 + 0.5 * math.sin(t * 4)
    ctx.set_source_rgba(0.35, 0.0, 0.02, 0.28 + 0.12 * pulse); ctx.paint()
    hx, hy = c.p(GX, GY); hr = c.r(GR)
    cx_, cy_ = hx - hr * 0.45, hy + hr * 0.25
    cloud(ctx, cx_, cy_, 110, 1, t)
    q = pop_in(t, T["scary"], 0.3)
    if q > 0:
        ctx.save(); ctx.translate(540, 300); ctx.scale(q, q); chip(ctx, "THE SCARY PART", 0, 0, RED, 1, 50); ctx.restore()
    for i, (key, lab) in enumerate((("hydrogen", "HYDROGEN"), ("methane", "METHANE"))):
        p = pop_in(t, T[key], 0.3)
        if p <= 0:
            continue
        y = 470 + i * 120
        ctx.save(); ctx.translate(560, y); ctx.scale(p, p)
        ctx.set_source_rgba(0.02, 0.04, 0.1, 0.8); rr(ctx, -40, -50, 460, 100, 50); ctx.fill()
        ctx.set_source_rgba(1, 0.55, 0.2, 0.95); ctx.set_line_width(4); rr(ctx, -40, -50, 460, 100, 50); ctx.stroke()
        text(ctx, lab, 20, 16, 48, INK, 1, "l")
        flame(ctx, 370, 12, 1.15, t + i, 1)
        ctx.restore()
    text(ctx, "= CAN BURN", 790, 750, 50, SUN, seg(t, T["burn"], T["burn"] + 0.2))
    # nota 'early NASA engineers'
    p = pop_in(t, T["nasa"], 0.3) * (1 - seg(t, T["so"] - 0.2, T["so"]))
    if p > 0.01:
        ctx.save(); ctx.translate(540, 1050); ctx.rotate(-0.05); ctx.scale(p, p)
        ctx.set_source_rgba(0.96, 0.93, 0.84, 0.95); rr(ctx, -330, -80, 660, 160, 14); ctx.fill()
        text(ctx, "1960s NASA ENGINEERS:", 0, -12, 40, NAVY, 1)
        text(ctx, "\"…SHOULD WE WORRY?\"", 0, 48, 44, (0.75, 0.15, 0.1), 1)
        ctx.restore()
    # faísca que aparece e é apagada por uma luva
    sp_x, sp_y = cx_ + 190, cy_ - 60
    on = seg(t, T["so"], T["so"] + 0.1) * (1 - seg(t, T["please"] - 0.05, T["please"] + 0.05))
    spark(ctx, sp_x, sp_y, 1.0, t, on)
    u = t - (T["please"] - 0.35)
    if -0.02 < u < 0.9:
        go = ease(u / 0.35) if u < 0.35 else 1 - ease((u - 0.45) / 0.45)
        glove(ctx, sp_x + 40, sp_y + 30 + 650 * (1 - go), 0.9, 0.3, 1)
    sm = t - T["please"]
    if 0 < sm < 1.0:  # fumo
        for i in range(6):
            ang = i * 1.05
            glow(ctx, sp_x + 90 * sm * math.cos(ang), sp_y - 60 * sm + 40 * sm * math.sin(ang), 60, (0.8, 0.8, 0.85), 0.5 * (1 - sm))
    q = pop_in(t, T["please_e"], 0.3)
    if q > 0:
        text(ctx, "PHEW.", 540, 1080, 80 * q, INK, 1 - seg(t, T["good"] - 0.3, T["good"]))


def s_filters(ctx, t):
    """vista de dentro do capacete: filtros de carvão 'comem' a nuvem, devagar"""
    c = Cover(ctx, INSIDE, 1.0, None, None)
    eat = seg(t, T["filters"], T["very_e"] + 0.3)
    r = 170 * (1 - 0.55 * eat)
    cx_, cy_ = 540 + 20 * math.sin(t * 1.3), 760 + 15 * math.cos(t * 1.1)
    cloud(ctx, cx_, cy_, r, 1, t)
    # filtros (cartuchos de carvão) à esquerda e à direita
    fa = seg(t, T["filters"] - 0.2, T["filters"] + 0.2)
    for side in (-1, 1):
        fx = 540 + side * 390; fy = 820
        if fa <= 0.01:
            continue
        ctx.save(); ctx.translate(fx, fy)
        ctx.set_source_rgba(0.85, 0.9, 0.97, fa); rr(ctx, -70, -150, 140, 300, 30); ctx.fill()
        ctx.set_source_rgba(0.12, 0.13, 0.16, fa); rr(ctx, -54, -130, 108, 260, 20); ctx.fill()
        random.seed(11 + side)
        for i in range(26):  # pedaços de carvão
            px, py = random.uniform(-44, 44), random.uniform(-118, 118)
            ctx.set_source_rgba(0.25, 0.26, 0.3, fa); ctx.arc(px, py, random.uniform(7, 13), 0, 6.283); ctx.fill()
        ctx.restore()
        # fluxo de partículas verdes da nuvem para o filtro
        if t > T["filters"]:
            for i in range(10):
                ph = ((t - T["filters"]) * 0.7 + i / 10) % 1
                x = cx_ + (fx - cx_) * ph; y = cy_ + (fy - cy_) * ph + 40 * math.sin(ph * 6 + i)
                ctx.set_source_rgba(*LIME, 0.8 * fa * (1 - ph * 0.6)); ctx.arc(x, y, 10 - 5 * ph, 0, 6.283); ctx.fill()
    ca = seg(t, T["charcoal"], T["charcoal"] + 0.25)
    chip(ctx, "ACTIVATED CHARCOAL", 540, 1090, INK, ca * (1 - seg(t, T["slowA"] - 0.3, T["slowA"])), 42)
    chip(ctx, "THE GOOD NEWS", 540, 330, LIME, seg(t, T["good"], T["good"] + 0.25) * (1 - seg(t, T["slowly1"], T["slowly1"] + 0.3)), 48)
    # barra de cheiro a descer como um download antigo
    da = seg(t, T["slowly1"], T["slowly1"] + 0.3) * (1 - seg(t, POP_T - 0.2, POP_T + 0.1))
    if da > 0.01:
        x, y, w_ = 140, 420, 800
        ctx.set_source_rgba(0.85, 0.87, 0.9, 0.95 * da); rr(ctx, x - 20, y - 120, w_ + 40, 260, 10); ctx.fill()
        ctx.set_source_rgba(0.1, 0.25, 0.6, da); ctx.rectangle(x - 20, y - 120, w_ + 40, 54); ctx.fill()
        ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(32); ctx.set_source_rgba(1, 1, 1, da); ctx.move_to(x, y - 82); ctx.show_text("Removing smell...")
        v = 1 - 0.03 * seg(t, T["slowly1"], T["very_e"] + 0.4)  # 100% → 97%
        ctx.set_source_rgba(0.6, 0.62, 0.66, da); ctx.rectangle(x, y - 20, w_, 56); ctx.fill()
        n = int(v * 26)
        for i in range(n):
            ctx.set_source_rgba(*LIME, da); ctx.rectangle(x + 4 + i * (w_ / 26), y - 16, w_ / 26 - 6, 48); ctx.fill()
        ctx.set_font_size(34); ctx.set_source_rgba(0.1, 0.1, 0.15, da)
        ctx.move_to(x, y + 86); ctx.show_text(f"Smell level: {v * 100:.0f}%")
        tl = "calculating..." if t < T["slowA"] else "2 days" if t < T["very"] else "forever"
        ctx.move_to(x + 430, y + 86); ctx.show_text(f"Time left: {tl}")
    for key, lab, yy in (("slowA", "SLOWLY.", 1000), ("very", "VERY… SLOWLY.", 1090)):
        q = pop_in(t, T[key], 0.3) * (1 - seg(t, POP_T, POP_T + 0.3))
        if q > 0.01:
            text(ctx, lab, 540, yy, 80 * q, SUN, 1)


def s_poll(ctx, t):
    Cover(ctx, STATION, 1.0 + 0.04 * seg(t, T["question"], T["because"]), None, None)
    for i, (lab, l1, l2, key, col) in enumerate((("A", "YOUR SUIT", "+ YOUR OWN", "own", CYAN),
                                                 ("B", "THE STATION", "+ SOMEONE ELSE'S", "station", SUN))):
        q = pop_in(t, T[key], 0.3)
        if q <= 0:
            continue
        cx_ = 280 + i * 520; cy_ = 1010
        ctx.save(); ctx.translate(cx_, cy_); ctx.scale(q, q)
        ctx.set_source_rgba(0.02, 0.04, 0.1, 0.85); rr(ctx, -215, -110, 430, 200, 30); ctx.fill()
        ctx.set_source_rgba(*col, 0.95); ctx.set_line_width(5); rr(ctx, -215, -110, 430, 200, 30); ctx.stroke()
        text(ctx, lab, -160, 30, 110, col, 1)
        text(ctx, l1, 40, -18, 40, INK, 1)
        text(ctx, l2, 40, 36, 32, col, 1)
        cloud(ctx, 165, -100, 34, 1, t, face=False, seed=i)
        ctx.restore()
    q = pop_in(t, T["tell"], 0.3)
    if q > 0:
        text(ctx, "TELL ME BELOW", 540, 1170, 54 * q, INK, 1 - seg(t, T["because"] - 0.3, T["because"]))
    text(ctx, "OR", 540, 1025, 50, INK, seg(t, T["station"], T["station"] + 0.2))


def s_end(ctx, t):
    """volta ao astronauta calmo: o último frame é igual ao primeiro"""
    k = 1 - seg(t, T["because"], T_END - 0.35)
    ref_cover(ctx, t, 1.0 + 0.12 * k, 768 + (HX - 768) * 0.5 * k, 1376 + (HY - 1376) * 0.5 * k)


SCENES = [(0, s_hook, "cut"), (T["first"], s_earth, "zoom"), (T["space"], s_face, "circle"),
          (T["second"], s_gloves, "push"), (T["wait"], s_rocket, "zoom"), (T["scary"], s_scary, "circle"),
          (T["good"], s_filters, "push"), (T["question"], s_poll, "zoom"), (T["because"], s_end, "circle")]
SCENES = [(a, (SCENES[i + 1][0] if i + 1 < len(SCENES) else T_END + 1), fn, tr) for i, (a, fn, tr) in enumerate(SCENES)]
PUNCH = [REWARD, T["face"], T["glass"], T["yes"], T["battery"], T["burn"], T["please"], T["very"]]
TRANS = 0.28
ALARM_P = 0.5


def punch(t):
    v = 0
    for p in PUNCH:
        x = t - p
        if 0 <= x < 0.45:
            v = max(v, math.sin(min(1, x / 0.08) * math.pi / 2) * (1 - x / 0.45))
    return 1 + 0.045 * v


def badge(ctx, t):
    """selo do loop aberto: 'THE SCARY PART · COMING UP' até 'Now the scary part'"""
    a = seg(t, T["first"] + 0.6, T["first"] + 1.0) * (1 - seg(t, T["scary"] - 0.3, T["scary"]))
    if a <= 0.01:
        return
    w_, h_ = 720, 80; x, y = 540 - w_ / 2, 196
    ctx.set_source_rgba(0.02, 0.04, 0.1, 0.75 * a); rr(ctx, x, y, w_, h_, 34); ctx.fill()
    ctx.set_source_rgba(*RED, 0.9 * a); ctx.set_line_width(3); rr(ctx, x, y, w_, h_, 34); ctx.stroke()
    pulse = 0.5 + 0.5 * math.sin(t * 5)
    ctx.set_source_rgba(*RED, a * (0.4 + 0.6 * pulse)); ctx.arc(x + 40, y + h_ / 2, 11, 0, 6.283); ctx.fill()
    text(ctx, "THE SCARY PART · COMING UP", x + 72, y + 53, 37, RED, a, "l")


def alarm(ctx, t):
    return  # EP003: sem sirene nem bordas vermelhas (decisão do dono, 19/11/2026)
    """bordas vermelhas a piscar ao ritmo do alarme, do fim do 'pffrrt' até à recompensa"""
    if t >= REWARD or t < 0.3:
        return
    p = 0.5 - 0.5 * math.cos(2 * math.pi * (t - 0.3) / ALARM_P)
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.62)
    g.add_color_stop_rgba(0, *RED, 0); g.add_color_stop_rgba(1, *RED, 0.62 * p)
    ctx.set_source(g); ctx.paint()
    ctx.set_source_rgba(*RED, 0.9 * p); ctx.set_line_width(18); ctx.rectangle(9, 9, W - 18, H - 18); ctx.stroke()


# pop-up de subscrição: reutiliza frame() de lib/subscribe_popup.py (código de referência aprovado)
_src = open(f"{ROOT}/../lib/subscribe_popup.py").read().split('pop=f"')[0].replace("OUT=sys.argv[1]", "OUT=None")
SUB = {}; exec(compile(_src, "subscribe_popup", "exec"), SUB)
SUB_P0 = SUB["P0"]  # no frame() original o botão entra em t = P0


def subscribe(ctx, t):
    u = t - POP_T
    if -0.05 < u < 2.7:
        ctx.set_source_surface(SUB["frame"](u + SUB_P0), 0, 0); ctx.paint()


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
    badge(ctx, t)
    z = punch(t)
    if z > 1.0005:
        fin = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c2 = cairo.Context(fin)
        c2.translate(W / 2, H / 2); c2.scale(z, z); c2.translate(-W / 2, -H / 2)
        c2.set_source_surface(out, 0, 0); c2.paint(); out = fin; ctx = cairo.Context(out)
    subscribe(ctx, t)  # fora do punch-zoom
    if raw:
        return out
    return np.ndarray((H, W, 4), np.uint8, out.get_data())[:, :, [2, 1, 0]].tobytes()


# ---------- legendas ----------
WEAK = {"a", "an", "the", "to", "of", "for", "on", "in", "it", "its", "and", "but", "with", "that", "is", "as",
        "be", "would", "could", "if", "about", "no", "so", "your", "or", "you", "can't", "it's", "there's", "like"}
groups, cur = [], []
for w in words:
    cand = cur + [w]
    if cur and (len(cand) > 3 or len(" ".join(x["w"] for x in cand)) > 18):
        last = clean(cur[-1]["w"])
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
    g_end = min(groups[gi + 1][0]["s"], g[-1]["e"] + 0.5) if gi + 1 < len(groups) else min(T_END - 0.25, g[-1]["e"] + 0.4)
    for k, w in enumerate(g):
        s = w["s"]; e = g[k + 1]["s"] if k + 1 < len(g) else g_end
        pop = "{\\fscx108\\fscy108\\t(0,90,\\fscx100\\fscy100)}" if k == 0 else ""
        txt = " ".join((f"{{\\c{CY}}}{x['w'].upper()}{{\\c{WH}}}" if j == k else x["w"].upper()) for j, x in enumerate(g))
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},Cap,,0,0,0,,{pop}{txt}")
ev += [f"Dialogue: 2,{ts(0)},{ts(T_END)},Mark,,0,0,0,,@whatifaholics"]
open(f"{BLD}/captions.ass", "w").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,90,90,640,1
Style: Mark,Inter Display,40,&H8CFFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,3,0,7,60,60,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n")


def build_audio_and_mux(raw):
    def synth(name, expr, d, af=None):
        path = f"{BLD}/{name}.wav"
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={d}"]
        if af:
            cmd += ["-af", af]
        subprocess.run(cmd + [path], check=True)
        return path
    swish = f"{BLD}/swish.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.5:c=pink:a=0.5:r=48000",
                    "-af", "bandpass=f=900:w=1400,afade=t=in:d=0.25:curve=qsin,afade=t=out:st=0.25:d=0.25,volume=0.35",
                    swish], check=True)
    pop = synth("pop_soft", "0.5*sin(2*PI*(260+500*exp(-t*35))*t)*exp(-t*22)", 0.2)
    ding = synth("ding", "0.35*(sin(2*PI*1320*t)+0.5*sin(2*PI*1980*t))*exp(-t*9)", 0.6)
    toc = synth("toc", "0.6*sin(2*PI*(620+300*exp(-t*80))*t)*exp(-t*55)", 0.12, "lowpass=f=2500")
    crackle = f"{BLD}/crackle.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.5:c=white:a=0.6:r=48000",
                    "-af", "highpass=f=3000,volume='0.6*gt(sin(2*PI*23*t),0.6)':eval=frame,afade=t=out:st=0.3:d=0.2",
                    crackle], check=True)
    pssh = f"{BLD}/pssh.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.6:c=white:a=0.5:r=48000",
                    "-af", "bandpass=f=4000:w=3000,afade=t=in:d=0.03,afade=t=out:st=0.15:d=0.45,volume=0.5", pssh], check=True)
    poof = f"{BLD}/poof.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "aevalsrc='0.8*sin(2*PI*(55+90*exp(-t*8))*t)*exp(-t*4)':s=48000:d=1.0",
                    "-f", "lavfi", "-i", "anoisesrc=d=0.5:c=pink:a=0.6:r=48000",
                    "-filter_complex", "[1]afade=t=out:d=0.5,lowpass=f=1500[n];[0][n]amix=inputs=2:normalize=0", poof], check=True)
    fart = f"{ROOT}/audio/pffrrt.wav"  # build/fart_synth.py (sintetizado, sem sirene)
    events = [(fart, 0.0, 1.0), (poof, REWARD - 0.02, 0.6)]
    events += [(swish, c - 0.25, 0.5) for c in (T["first"], T["space"], T["second"], T["wait"], T["scary"], T["good"], T["question"], T["because"])]
    events += [(pop, x, 0.5) for x in (T["yes"], T["hydrogen"], T["methane"], T["nasa"], T["own"], T["station"])]
    events += [(ding, x, 0.35) for x in (T["face"] + 0.3, T["glass_e"], T["battery_e"], T["please_e"], T["very_e"])]
    events += [(toc, x, 0.55) for x in (T["hold"] + 0.1, T["nose"] + 0.15, T["gloves"] + 0.25)]
    events += [(crackle, T["so"], 0.35), (pssh, T["please"], 0.45), (pop, POP_T + 1.0, 0.3)]
    ins, ch, lab = [], [], []
    for n, (f, x, v) in enumerate(events):
        if v <= 0:
            continue
        idx = 3 + len(lab); ins += ["-i", f]; d = int(max(0, x) * 1000)
        ch.append(f"[{idx}:a]adelay={d}|{d},volume={v}[e{len(lab)}]"); lab.append(f"[e{len(lab)}]")
    sfx = ";".join(ch) + ";" + "".join(lab) + f"amix=inputs={len(lab)}:normalize=0[sfx]"
    od = int(OFF * 1000)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", NARR, "-stream_loop", "-1", "-i", MUSIC, *ins,
                    "-filter_complex",
                    f"[0:v]noise=alls=3:allf=t,subtitles={BLD}/captions.ass,format=yuv420p[v];"
                    f"[1:a]adelay={od}|{od},asplit=2[n1][nk];"
                    f"[2:a]atrim=0:{T_END},volume='if(lt(t,{REWARD + 0.3:.2f}),0,if(between(t,{T['scary'] - 0.5:.2f},{T['scary'] + 0.1:.2f}),0.08,0.35))':eval=frame,"
                    f"afade=t=out:st={T_END - 1.2}:d=1.2[m];"
                    "[m][nk]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[md];"
                    f"{sfx};[n1][md][sfx]amix=inputs=3:duration=longest:normalize=0,apad,"
                    f"loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{T_END}[a]",
                    "-map", "[v]", "-map", "[a]", "-t", str(T_END), "-r", str(FPS),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-maxrate", "8M", "-bufsize", "16M",
                    "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", OUT], check=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--sheet":  # folha de controlo
        from PIL import Image
        ts_ = [float(x) for x in sys.argv[2].split(",")]
        ims = []
        for x in ts_:
            s = frame(x, raw=True); arr = np.ndarray((H, W, 4), np.uint8, s.get_data())[:, :, [2, 1, 0]]
            ims.append(Image.fromarray(arr.copy()).resize((270, 480)))
        cols = 6; rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (270 * cols, 480 * rows))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
        sheet.save(sys.argv[3]); print(T_END, {k: round(v, 2) for k, v in T.items()})
        sys.exit()
    raw = f"{BLD}/raw.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                          "-pix_fmt", "yuv420p", raw], stdin=subprocess.PIPE)
    for i in range(int(T_END * FPS)):
        p.stdin.write(frame(i / FPS))
    p.stdin.close(); p.wait()
    build_audio_and_mux(raw)
    print("OK", OUT, T_END)
