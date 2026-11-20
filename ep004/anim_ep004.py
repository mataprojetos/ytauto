#!/usr/bin/env python3
"""Whatifaholic EP004: What if GTA happened in space? Animação por código (pycairo) sobre 7 ilustrações.
Tudo original: estrelas de procurado desenhadas por código (5 pontas simples), sirenes e alarme sintetizados.
Gancho: motor de foguetão + alarme de dois tons + bordas vermelhas; 5 estrelas acendem uma a uma em
"Five stars. Wanted… literally." e no fim sobem e viram estrelas do céu. Último frame = primeiro."""
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
OUT = f"{ROOT}/whatifaholic_ep004_gta_space.mp4"
OFF = 0.35  # o motor arranca no frame 0; a narração entra logo a seguir
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "csv=p=0", NARR]))
T_END = round(OFF + dur + 0.6, 2)
random.seed(4)

REF = L.surf(f"{A}/astro_ref.png"); POLICE = L.surf(f"{A}/police.png"); HIDE = L.surf(f"{A}/hide.png")
RADIO = L.surf(f"{A}/radio.png"); MARS = L.surf(f"{A}/mars.png"); MOON = L.surf(f"{A}/moon.png")
HOUSE = L.surf(f"{A}/house.png")
BLUE = (0.25, 0.45, 1.0)

# ---------- palavras ----------
words = json.load(open(f"{BLD}/words_ep004.json"))
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
    five=at("five stars"), stars_e=at("five stars", end=True), wanted=at("wanted"), lit=at("literally"),
    lit_e=at("literally", end=True), first=at("first problem"), police=at("the police"), slowly=at("slowly"),
    very=at("very slowly"), zero=at("in zero gravity"), float=at("float there"), sirens=at("sirens on"),
    nowhere_e=at("going nowhere", end=True), second=at("second problem"), hide=at("hide a rocket"),
    alleys=at("no alleys"), garages=at("no garages"), just=at("just you"), large=at("very large"),
    obvious=at("very obvious"), obvious_e=at("spaceship", end=True), ride=at("need a new ride"),
    carjack=at("carjacking"), door=at("opening a door"), kmh=at("28000"), bad=at("bad idea"),
    bad_e=at("bad idea", end=True), radio=at("and the radio"), static=at("pure static"),
    nobody=at("nobody can hear"), sing_e=at("sing along", end=True), gas=at("gas station"),
    mars=at("on mars"), seven=at("seven months"), bath_e=at("bathroom", end=True), twist=at("then the twist"),
    escape=at("you escape"), park=at("park on the moon"), satellite=at("a satellite"),
    flash=at("flashes"), fine=at("the fine arrives"), mom=at("your mom's"), house_e=at("house", end=True),
    question=at("would you rather"), rocketA=at("a rocket or"), station=at("entire space station"),
    tell=at("tell me below"), because=at("because you just"),
)
REWARD = T["lit_e"] + 0.05            # estrelas completas no fim de "literally" → sobem para o céu
POP_T = T["house_e"] + 0.08           # pop-up de subscrição logo a seguir a "your mom's house"
STAR_ON = [T["five"] + i * (T["lit"] - T["five"]) / 4.6 for i in range(5)]


# ---------- desenhos por código ----------
def star_path(ctx, x, y, r, rot=0.0):
    ctx.move_to(x + r * math.cos(rot - math.pi / 2), y + r * math.sin(rot - math.pi / 2))
    for i in range(1, 10):
        rr_ = r if i % 2 == 0 else r * 0.45
        ang = rot - math.pi / 2 + i * math.pi / 5
        ctx.line_to(x + rr_ * math.cos(ang), y + rr_ * math.sin(ang))
    ctx.close_path()


def wanted_star(ctx, x, y, r, on, a=1.0, rot=0.0):
    """estrela simples de 5 pontas (desenho nosso): contorno apagado → amarela acesa"""
    if a <= 0.01 or r < 1:
        return
    if on > 0.01:
        glow(ctx, x, y, r * 2.4, SUN, 0.55 * on * a)
    star_path(ctx, x, y, r, rot)
    ctx.set_source_rgba(0.02, 0.04, 0.1, 0.55 * a * (1 - on)); ctx.fill_preserve()
    ctx.set_source_rgba(1.0, 0.86, 0.3, a * on); ctx.fill_preserve()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(0.1, 0.06, 0.0, 0.85 * a * on + 0.0); ctx.set_line_width(max(2, r * 0.12)); ctx.stroke_preserve()
    ctx.set_source_rgba(1, 1, 1, 0.7 * a * (1 - on)); ctx.set_line_width(max(2, r * 0.07)); ctx.stroke()


def chip(ctx, s, x, y, col=CYAN, a=1.0, size=40):
    if a <= 0.01:
        return
    ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(size)
    tw = ctx.text_extents(s)[2]; w_, h_ = tw + 60, size * 1.9
    ctx.set_source_rgba(0.02, 0.04, 0.1, 0.8 * a); rr(ctx, x - w_ / 2, y - h_ / 2, w_, h_, h_ / 2); ctx.fill()
    ctx.set_source_rgba(*col, 0.95 * a); ctx.set_line_width(4); rr(ctx, x - w_ / 2, y - h_ / 2, w_, h_, h_ / 2); ctx.stroke()
    text(ctx, s, x, y + size * 0.36, size, col, a)


def popchip(ctx, t, t0, s, x, y, col=CYAN, size=44, t1=None):
    q = pop_in(t, t0, 0.3)
    if t1 is not None:
        q *= 1 - seg(t, t1, t1 + 0.25)
    if q > 0.01:
        ctx.save(); ctx.translate(x, y); ctx.scale(q, q); chip(ctx, s, 0, 0, col, 1, size); ctx.restore()


def siren(ctx, x, y, r, t, a=1.0, ph=0.0):
    """luzes azul/vermelha alternadas (desenho nosso)"""
    p = (math.sin(t * 2 * math.pi * 2.2 + ph) > 0)
    glow(ctx, x - r * 0.35, y, r * (1.4 if p else 0.8), RED, (0.85 if p else 0.25) * a)
    glow(ctx, x + r * 0.35, y, r * (0.8 if p else 1.4), BLUE, (0.25 if p else 0.85) * a)


def cross(ctx, x, y, s, a=1.0, col=RED):
    if a <= 0.01:
        return
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_source_rgba(*col, a); ctx.set_line_width(s * 0.22)
    ctx.move_to(x - s / 2, y - s / 2); ctx.line_to(x + s / 2, y + s / 2)
    ctx.move_to(x + s / 2, y - s / 2); ctx.line_to(x - s / 2, y + s / 2); ctx.stroke()


def stamp(ctx, s, x, y, t, t0, col=RED, size=110, rot=-0.15):
    """carimbo que cai com impacto"""
    u = t - t0
    if u < 0:
        return
    k = 1 + 1.6 * math.exp(-u * 14) if u < 0.5 else 1.0
    a = min(1, u / 0.06)
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(k, k)
    ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(size)
    tw = ctx.text_extents(s)[2]; w_, h_ = tw + 70, size * 1.45
    ctx.set_source_rgba(0.02, 0.04, 0.1, 0.55 * a); rr(ctx, -w_ / 2, -h_ / 2, w_, h_, 22); ctx.fill()
    ctx.set_source_rgba(*col, a); ctx.set_line_width(12); rr(ctx, -w_ / 2, -h_ / 2, w_, h_, 22); ctx.stroke()
    text(ctx, s, 0, size * 0.36, size, col, a)
    ctx.restore()


def note(ctx, x, y, s, a, col=CYAN):
    """nota musical simples"""
    if a <= 0.01:
        return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.set_source_rgba(*col, a)
    ctx.save(); ctx.translate(0, 0); ctx.scale(1.3, 1); ctx.arc(0, 0, 14, 0, 6.283); ctx.restore(); ctx.fill()
    ctx.rectangle(12, -70, 7, 70); ctx.fill()
    ctx.move_to(19, -70); ctx.curve_to(45, -60, 45, -40, 34, -26); ctx.curve_to(38, -42, 30, -50, 19, -52); ctx.fill()
    ctx.restore()


def speed_lines(ctx, t, a, n=26, seed=1):
    if a <= 0.01:
        return
    rnd = random.Random(seed)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(n):
        y = rnd.uniform(150, 1750); ln = rnd.uniform(160, 520); sp = rnd.uniform(2600, 4200)
        x = (rnd.uniform(0, W + 600) - t * sp) % (W + 700) - 300
        ctx.set_source_rgba(1, 1, 1, a * rnd.uniform(0.25, 0.7)); ctx.set_line_width(rnd.uniform(3, 8))
        ctx.move_to(x, y); ctx.line_to(x + ln, y); ctx.stroke()


def dim(ctx, a):
    if a > 0.01:
        ctx.set_source_rgba(0.01, 0.02, 0.06, a); ctx.paint()


# ---------- cenas ----------
def s_hook(ctx, t):
    """0 s: foguetão com motor a tremer; estrelas de procurado acendem uma a uma e sobem para o céu"""
    shake = seg(t, 0.0, 0.35) * (1 - seg(t, REWARD, REWARD + 0.6))
    jx = 7 * shake * math.sin(t * 61); jy = 5 * shake * math.sin(t * 47 + 1)
    k = seg(t, 0.0, T["first"])
    ctx.save(); ctx.translate(jx, jy)
    c = Cover(ctx, REF, 1.0 + 0.10 * k, 768, 1376 + 160 * k)
    ctx.restore()
    # chamas extra dos propulsores (bombeiam com o motor)
    for ix in (420, 768, 1116):
        x, y = c.p(ix, 2560 if ix == 768 else 2470)
        glow(ctx, x, y, 120 * (0.8 + 0.25 * math.sin(t * 40 + ix)), CYAN, 0.45 * shake)
    # estrelas de procurado
    n0 = 5; r0 = 70; gap = 175; y0 = 330
    a = seg(t, 0.06, 0.22)
    if a > 0.01:
        lab = pop_in(t, T["wanted"], 0.3) * (1 - seg(t, REWARD, REWARD + 0.25))
        if lab > 0.01:
            ctx.save(); ctx.translate(540, 500); ctx.scale(lab, lab)
            ctx.set_source_rgba(0.25, 0.02, 0.02, 0.85); rr(ctx, -230, -55, 460, 100, 26); ctx.fill()
            ctx.set_source_rgba(*RED, 1); ctx.set_line_width(5); rr(ctx, -230, -55, 460, 100, 26); ctx.stroke()
            text(ctx, "WANTED", 0, 22, 66, INK, 1)
            ctx.restore()


def s_police(ctx, t):
    """carros de polícia a flutuar parados, sirenes ligadas"""
    t0 = T["first"]
    bob = math.sin((t - t0) * 1.6)
    c = Cover(ctx, POLICE, 1.12 - 0.05 * seg(t, t0, T["second"]), 768, 1150)
    for (ix, iy), ph in (((360, 952), 0.0), ((1020, 960), 1.7)):
        x, y = c.p(ix, iy + 10 * bob)
        siren(ctx, x, y, 80, t, seg(t, T["sirens"] - 0.3, T["sirens"]) * 0.6 + 0.4, ph)
    # velocímetro ridículo
    v = 0.0001 if t < T["very"] else 0.00001
    q = pop_in(t, T["slowly"], 0.3) * (1 - seg(t, T["zero"] - 0.2, T["zero"]))
    if q > 0.01:
        ctx.save(); ctx.translate(540, 470); ctx.scale(q, q)
        chip(ctx, f"POLICE SPEED: {v:.5f} KM/H", 0, 0, SUN, 1, 44); ctx.restore()
    popchip(ctx, t, T["zero"], "ZERO GRAVITY", 540, 470, CYAN, 50, T["second"] - 0.4)
    # "going nowhere": setas a rodar sem sair do sítio
    a = seg(t, T["nowhere_e"] - 0.5, T["nowhere_e"] - 0.2)
    if a > 0.01:
        for k, (ix, iy) in enumerate(((380, 1020), (1100, 1060))):
            x, y = c.p(ix, iy)
            ctx.save(); ctx.translate(x, y + 150); ctx.rotate(t * 4 + k)
            ctx.set_source_rgba(*INK, 0.8 * a); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.arc(0, 0, 50, 0, 4.6); ctx.stroke()
            ctx.move_to(50 * math.cos(4.6) - 14, 50 * math.sin(4.6) - 8); ctx.line_to(50 * math.cos(4.6), 50 * math.sin(4.6))
            ctx.line_to(50 * math.cos(4.6) + 4, 50 * math.sin(4.6) - 22); ctx.stroke()
            ctx.restore()


def s_hide(ctx, t):
    """foguetão enorme 'escondido' atrás de um caixote minúsculo"""
    t0 = T["second"]
    c = Cover(ctx, HIDE, 1.0 + 0.06 * seg(t, t0, T["ride"]), 768, 1300)
    # holofote de busca a varrer
    sw = math.sin((t - t0) * 1.4)
    ctx.save(); ctx.move_to(540 + sw * 80, -40); ctx.line_to(540 + sw * 520 - 180, 1500); ctx.line_to(540 + sw * 520 + 180, 1500)
    ctx.close_path(); g = cairo.LinearGradient(0, 0, 0, 1500)
    g.add_color_stop_rgba(0, 1, 1, 0.85, 0.28); g.add_color_stop_rgba(1, 1, 1, 0.85, 0.0)
    ctx.set_source(g); ctx.fill(); ctx.restore()
    popchip(ctx, t, T["alleys"], "NO ALLEYS", 300, 330, RED, 40, T["large"] - 0.2)
    popchip(ctx, t, T["garages"], "NO GARAGES", 780, 330, RED, 40, T["large"] - 0.2)
    for x, k in ((300, "alleys"), (780, "garages")):
        cross(ctx, x + 150 if x < 500 else x + 160, 330, 46, seg(t, T[k] + 0.2, T[k] + 0.3) * (1 - seg(t, T["large"] - 0.2, T["large"])))
    # seta gigante "VERY OBVIOUS"
    q = pop_in(t, T["obvious"], 0.35)
    if q > 0.01:
        x, y = c.p(1180, 800)
        ctx.save(); ctx.translate(x + 10 * math.sin(t * 12), y); ctx.scale(q, q); ctx.rotate(0.5)
        ctx.set_source_rgba(*SUN, 1)
        ctx.move_to(-40, -170); ctx.line_to(40, -170); ctx.line_to(40, 0); ctx.line_to(95, 0); ctx.line_to(0, 110)
        ctx.line_to(-95, 0); ctx.line_to(-40, 0); ctx.close_path(); ctx.fill_preserve()
        ctx.set_source_rgba(0.2, 0.1, 0, 1); ctx.set_line_width(6); ctx.stroke(); ctx.restore()
        ctx.save(); ctx.translate(540, 460); ctx.scale(q, q); chip(ctx, "VERY OBVIOUS", 0, 0, SUN, 1, 60); ctx.restore()


def s_carjack(ctx, t):
    """trocar de carro a 28 000 km/h: linhas de velocidade, contador e carimbo BAD IDEA"""
    t0 = T["ride"]
    sh = 4 * math.sin(t * 53) * seg(t, T["door"], T["door"] + 0.3)
    ctx.save(); ctx.translate(sh, 0)
    Cover(ctx, POLICE, 2.3, 1100, 1040)
    ctx.restore()
    speed_lines(ctx, t, 0.4 + 0.6 * seg(t, T["carjack"], T["door"]))
    v = int(28000 * seg(t, T["door"] - 0.2, T["kmh"] + 0.4) ** 0.6)
    q = pop_in(t, T["door"] - 0.2, 0.3)
    if q > 0.01:
        ctx.save(); ctx.translate(540, 430); ctx.scale(q, q)
        ctx.set_source_rgba(0.02, 0.04, 0.1, 0.82); rr(ctx, -330, -95, 660, 190, 34); ctx.fill()
        ctx.set_source_rgba(*CYAN, 1); ctx.set_line_width(5); rr(ctx, -330, -95, 660, 190, 34); ctx.stroke()
        text(ctx, f"{v:,}", 0, 30, 110, INK, 1); text(ctx, "KM/H", 0, 82, 40, CYAN, 1)
        ctx.restore()
    popchip(ctx, t, T["ride"], "NEED A NEW RIDE?", 540, 680, CYAN, 46, T["door"] - 0.3)
    stamp(ctx, "BAD IDEA", 540, 760, t, T["bad"])


def s_radio(ctx, t):
    """rádio só com estática; notas a cantar que desaparecem"""
    t0 = T["radio"]
    c = Cover(ctx, RADIO, 1.05 + 0.05 * seg(t, t0, T["gas"]), 700, 1500)
    # estática no ecrã do rádio
    x0, y0 = c.p(668, 1844); x1, y1 = c.p(808, 2012)
    rnd = random.Random(int(t * 30))
    for _ in range(260):
        px = rnd.uniform(x0, x1); py = rnd.uniform(y0, y1); g_ = rnd.random()
        ctx.set_source_rgba(g_, g_, g_, 0.8); ctx.rectangle(px, py, 5, 4); ctx.fill()
    popchip(ctx, t, T["static"], "PURE STATIC", 540, 360, QUIET, 48, T["nobody"] - 0.2)
    # notas a sair da boca que encolhem (ninguém ouve)
    if t > T["nobody"] - 0.6:
        mx, my = c.p(900, 1560)
        for i in range(5):
            u = ((t - T["nobody"]) * 0.7 + i * 0.2) % 1
            a = (1 - u) * seg(t, T["nobody"] - 0.6, T["nobody"] - 0.2)
            note(ctx, mx - 250 * u - 40 * i % 120, my - 420 * u - 20 * math.sin(t * 4 + i), 1.1 * (1 - 0.6 * u), a, (CYAN, SUN, PINK)[i % 3])
    popchip(ctx, t, T["nobody"], "NO SOUND IN SPACE", 540, 360, CYAN, 48)
    q = pop_in(t, T["nobody"] + 0.25, 0.3)
    if q > 0.01:
        ctx.save(); ctx.translate(540, 520); ctx.scale(q, q)
        text(ctx, "0 dB", 0, 30, 90, RED, 1); ctx.restore()


def s_mars(ctx, t):
    """bomba de gasolina em Marte; placa '7 MONTHS'"""
    t0 = T["gas"]
    c = Cover(ctx, MARS, 1.0 + 0.06 * seg(t, t0, T["twist"]), 768, 1300)
    # texto na placa em branco
    x0, y0 = c.p(808, 860); x1, y1 = c.p(1376, 1180)
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    a = seg(t, t0 + 0.05, t0 + 0.3)
    ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    for s_, yy, sz, col in (("GAS", cy_ - 18, 86, (0.75, 0.2, 0.12)), ("LAST STOP", cy_ + 58, 40, (0.2, 0.25, 0.35))):
        ctx.set_font_size(sz); xb, yb, tw, th, _, _ = ctx.text_extents(s_)
        ctx.move_to(cx_ - tw / 2 - xb, yy + th / 2); ctx.set_source_rgba(*col, a); ctx.show_text(s_)
    popchip(ctx, t, T["mars"], "NEAREST: MARS", 540, 330, SUN, 46, T["seven"] - 0.15)
    # placa grande "7 MONTHS"
    q = pop_in(t, T["seven"], 0.35)
    if q > 0.01:
        ctx.save(); ctx.translate(540, 400); ctx.scale(q, q); ctx.rotate(-0.04)
        ctx.set_source_rgba(0.1, 0.45, 0.25, 1); rr(ctx, -300, -110, 600, 220, 26); ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 1); ctx.set_line_width(8); rr(ctx, -285, -95, 570, 190, 18); ctx.stroke()
        text(ctx, "7 MONTHS", 0, 30, 104, INK, 1); text(ctx, "NEXT FUEL", 0, -55, 34, INK, 1)
        ctx.restore()
    # medidor de combustível a zero
    a = seg(t, t0 + 0.2, t0 + 0.5)
    if a > 0.01:
        gx, gy = 540, 1520
        ctx.set_source_rgba(0.02, 0.04, 0.1, 0.8 * a); ctx.arc(gx, gy, 120, math.pi, 2 * math.pi); ctx.close_path(); ctx.fill()
        ctx.set_line_width(10); ctx.set_source_rgba(*RED, a); ctx.arc(gx, gy, 95, math.pi, math.pi * 1.25); ctx.stroke()
        ctx.set_source_rgba(*INK, a); ctx.arc(gx, gy, 95, math.pi * 1.3, 2 * math.pi); ctx.stroke()
        text(ctx, "E", gx - 85, gy - 20, 34, RED, a); text(ctx, "F", gx + 85, gy - 20, 34, INK, a)
        ang = math.pi * 1.06 + 0.05 * math.sin(t * 9)
        ctx.set_source_rgba(*SUN, a); ctx.set_line_width(8); ctx.move_to(gx, gy)
        ctx.line_to(gx + 90 * math.cos(ang), gy + 90 * math.sin(ang)); ctx.stroke()


def s_moon(ctx, t):
    """estaciona na Lua; satélite-radar dispara flash branco"""
    t0 = T["twist"]
    c = Cover(ctx, MOON, 1.0 + 0.1 * seg(t, t0, T["fine"]), 768, 1150)
    lx, ly = c.p(820, 620)
    # luz vermelha do radar a piscar + feixe de deteção
    blink = 0.5 + 0.5 * (math.sin(t * 12) > 0)
    glow(ctx, lx, ly, 90, RED, 0.5 * blink * seg(t, T["satellite"] - 0.3, T["satellite"]))
    a = seg(t, T["satellite"], T["satellite"] + 0.3) * (1 - seg(t, T["flash"] + 0.3, T["flash"] + 0.6))
    if a > 0.01:
        rx, ry = c.p(500, 1608)
        ctx.move_to(lx, ly); ctx.line_to(rx - 160, ry); ctx.line_to(rx + 160, ry); ctx.close_path()
        ctx.set_source_rgba(*RED, 0.18 * a); ctx.fill()
    popchip(ctx, t, T["escape"], "ESCAPED!", 540, 340, GREEN, 50, T["satellite"] - 0.1)
    popchip(ctx, t, T["satellite"], "SPEED CAMERA", 540, 340, RED, 50)
    # flash branco
    u = t - T["flash"]
    if 0 <= u < 0.7:
        glow(ctx, lx, ly, 900, INK, 0.9 * math.exp(-u * 5))
        ctx.set_source_rgba(1, 1, 1, 0.95 * math.exp(-u * 7)); ctx.paint()


def s_house(ctx, t):
    """a multa chega a casa da mãe"""
    t0 = T["fine"]
    c = Cover(ctx, HOUSE, 1.0 + 0.06 * seg(t, t0, T["question"]), 768, 1350)
    q = pop_in(t, T["mom"], 0.35)
    if q > 0.01:
        ctx.save(); ctx.translate(540, 560); ctx.scale(q, q); ctx.rotate(0.05)
        ctx.set_source_rgba(0.98, 0.97, 0.92, 1); rr(ctx, -330, -170, 660, 340, 18); ctx.fill()
        ctx.set_source_rgba(*RED, 1); ctx.rectangle(-330, -170, 660, 70); ctx.fill()
        ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(42); ctx.set_source_rgba(1, 1, 1, 1); ctx.move_to(-300, -120); ctx.show_text("SPEEDING FINE")
        ctx.set_source_rgba(0.1, 0.1, 0.15, 1); ctx.set_font_size(34)
        ctx.move_to(-300, -40); ctx.show_text("Location: The Moon")
        ctx.move_to(-300, 10); ctx.show_text("Speed: 28,000 km/h")
        ctx.set_font_size(30); ctx.move_to(-300, 60); ctx.show_text("Send to: Mom")
        ctx.restore()
        stamp(ctx, "PAY NOW", 700, 690, t, T["mom"] + 0.35, RED, 60, 0.2)
    # mãe furiosa: janela acende a vermelho
    a = seg(t, T["house_e"] - 0.2, T["house_e"])
    if a > 0.01:
        wx, wy = c.p(1180, 1680)
        glow(ctx, wx, wy, 160, RED, 0.55 * a * (0.7 + 0.3 * math.sin(t * 10)))


def s_poll(ctx, t):
    Cover(ctx, REF, 1.0 + 0.04 * seg(t, T["question"], T["because"]), 768, 1376)
    dim(ctx, 0.45)
    for i, (lab, l1, l2, key, col) in enumerate((("A", "A ROCKET", "small & fast", "rocketA", CYAN),
                                                 ("B", "THE STATION", "the whole thing", "station", SUN))):
        q = pop_in(t, T[key], 0.3)
        if q <= 0:
            continue
        cx_ = 280 + i * 520; cy_ = 760
        ctx.save(); ctx.translate(cx_, cy_); ctx.scale(q, q)
        ctx.set_source_rgba(0.02, 0.04, 0.1, 0.88); rr(ctx, -215, -110, 430, 200, 30); ctx.fill()
        ctx.set_source_rgba(*col, 0.95); ctx.set_line_width(5); rr(ctx, -215, -110, 430, 200, 30); ctx.stroke()
        text(ctx, lab, -160, 30, 110, col, 1)
        text(ctx, l1, 40, -18, 40, INK, 1)
        text(ctx, l2, 40, 36, 32, col, 1)
        ctx.restore()
    text(ctx, "OR", 540, 775, 50, INK, seg(t, T["station"], T["station"] + 0.2))
    q = pop_in(t, T["tell"], 0.3)
    if q > 0:
        text(ctx, "TELL ME BELOW", 540, 960, 58 * q, INK, 1 - seg(t, T["because"] - 0.3, T["because"]))


def s_end(ctx, t):
    """volta ao foguetão do início: o último frame é igual ao primeiro"""
    k = 1 - seg(t, T["because"], T_END - 0.35)
    Cover(ctx, REF, 1.0 + 0.10 * k, 768, 1376 + 160 * k)


SCENES = [(0, s_hook, "cut"), (T["first"], s_police, "zoom"), (T["second"], s_hide, "push"),
          (T["ride"], s_carjack, "push"), (T["radio"], s_radio, "circle"), (T["gas"], s_mars, "zoom"),
          (T["twist"], s_moon, "circle"), (T["fine"], s_house, "push"), (T["question"], s_poll, "zoom"),
          (T["because"], s_end, "circle")]
SCENES = [(a, (SCENES[i + 1][0] if i + 1 < len(SCENES) else T_END + 1), fn, tr) for i, (a, fn, tr) in enumerate(SCENES)]
DINGS = [T["nowhere_e"], T["obvious_e"], T["bad_e"], T["sing_e"], T["bath_e"], T["house_e"]]
PUNCH = [REWARD, T["obvious"], T["bad"], T["seven"], T["flash"], T["mom"]]
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
    """selo do loop aberto: 'THE TWIST · COMING UP' até 'Then the twist'"""
    a = seg(t, T["first"] + 0.6, T["first"] + 1.0) * (1 - seg(t, T["twist"] - 0.3, T["twist"]))
    if a <= 0.01:
        return
    w_, h_ = 600, 80; x, y = 540 - w_ / 2, 196
    ctx.set_source_rgba(0.02, 0.04, 0.1, 0.75 * a); rr(ctx, x, y, w_, h_, 34); ctx.fill()
    ctx.set_source_rgba(*SUN, 0.9 * a); ctx.set_line_width(3); rr(ctx, x, y, w_, h_, 34); ctx.stroke()
    pulse = 0.5 + 0.5 * math.sin(t * 5)
    wanted_star(ctx, x + 44, y + h_ / 2, 20, 0.5 + 0.5 * pulse, a)
    text(ctx, "THE TWIST · COMING UP", x + 80, y + 53, 37, SUN, a, "l")


def stars_overlay(ctx, t):
    """estrelas de procurado: por cima de tudo, para a subida continuar depois do corte de cena"""
    if t > REWARD + 1.7:
        return
    n0 = 5; r0 = 70; gap = 175; y0 = 330
    a = seg(t, 0.06, 0.22)
    if a <= 0.01:
        return
    for i in range(n0):
        x = 540 + (i - 2) * gap; y = y0
        on = seg(t, STAR_ON[i], STAR_ON[i] + 0.08)
        sc = pop_in(t, STAR_ON[i], 0.25) if t > STAR_ON[i] else 1.0
        rr_ = r0 * (0.75 + 0.25 * sc)
        if t >= REWARD:  # sobem e viram estrelas do céu
            u = seg(t, REWARD, REWARD + 0.75)
            tx = 540 + (i - 2) * 215 + (40 if i % 2 else -30); ty = 110 + 45 * (i % 3)
            x = x + (tx - x) * u; y = y + (ty - y) * u - 90 * math.sin(u * math.pi)
            rr_ = r0 * (1 - 0.88 * u)
            tw = 1 - seg(t, REWARD + 0.75, REWARD + 1.6)
            wanted_star(ctx, x, y, rr_, 1, a * (0.35 + 0.65 * tw), u * 2.5)
            if u >= 1:  # brilho de estrela do céu
                glow(ctx, x, y, 34, INK, 0.5 * tw * (0.6 + 0.4 * math.sin(t * 9 + i)))
        else:
            wanted_star(ctx, x, y, rr_, on, a)


def alarm(ctx, t):
    """bordas vermelhas a piscar ao ritmo do alarme de dois tons, até à recompensa"""
    if t >= REWARD + 0.3:
        return
    fade = 1 - seg(t, REWARD, REWARD + 0.3)
    p = (0.5 - 0.5 * math.cos(2 * math.pi * t / ALARM_P)) * fade
    if p < 0.005:
        return
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.62)
    g.add_color_stop_rgba(0, *RED, 0); g.add_color_stop_rgba(1, *RED, 0.6 * p)
    ctx.set_source(g); ctx.paint()
    ctx.set_source_rgba(*RED, 0.9 * p); ctx.set_line_width(18); ctx.rectangle(9, 9, W - 18, H - 18); ctx.stroke()


# pop-up de subscrição: reutiliza frame() de lib/subscribe_popup.py (código de referência aprovado)
_src = open(f"{ROOT}/../lib/subscribe_popup.py").read().split('pop=f"')[0].replace("OUT=sys.argv[1]", "OUT=None")
SUB = {}; exec(compile(_src, "subscribe_popup", "exec"), SUB)
SUB_P0 = SUB["P0"]


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
    stars_overlay(ctx, t)
    badge(ctx, t)
    z = punch(t)
    if z > 1.0005:
        fin = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c2 = cairo.Context(fin)
        c2.translate(W / 2, H / 2); c2.scale(z, z); c2.translate(-W / 2, -H / 2)
        c2.set_source_surface(out, 0, 0); c2.paint(); out = fin; ctx = cairo.Context(out)
    subscribe(ctx, t)
    if raw:
        return out
    return np.ndarray((H, W, 4), np.uint8, out.get_data())[:, :, [2, 1, 0]].tobytes()


# ---------- legendas ----------
WEAK = {"a", "an", "the", "to", "of", "for", "on", "in", "it", "its", "and", "but", "with", "that", "is", "as",
        "be", "would", "could", "if", "about", "no", "so", "your", "or", "you", "can't", "it's", "there's", "like", "at"}
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
    if re.search(r"[.,?!:…]$", w["w"]):
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

    def noise(name, d, color, af):
        path = f"{BLD}/{name}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anoisesrc=d={d}:c={color}:a=0.6:r=48000",
                        "-af", af, path], check=True)
        return path
    swish = noise("swish", 0.5, "pink", "bandpass=f=900:w=1400,afade=t=in:d=0.25:curve=qsin,afade=t=out:st=0.25:d=0.25,volume=0.3")
    pop = synth("pop_soft", "0.5*sin(2*PI*(260+500*exp(-t*35))*t)*exp(-t*22)", 0.2)
    ding = synth("ding", "0.35*(sin(2*PI*1320*t)+0.5*sin(2*PI*1980*t))*exp(-t*9)", 0.6)
    # motor de foguetão: ronco grave + ruído castanho filtrado (sintetizado)
    eng_n = noise("engine_n", 3.2, "brown", "lowpass=f=420,volume=2.2")
    eng_r = synth("engine_r", "0.5*sin(2*PI*(48+6*sin(2*PI*7*t))*t)*(0.7+0.3*sin(2*PI*13*t))", 3.2)
    engine = f"{BLD}/engine.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", eng_n, "-i", eng_r, "-filter_complex",
                    "[0][1]amix=inputs=2:normalize=0,afade=t=in:d=0.12,afade=t=out:st=2.2:d=1.0", engine], check=True)
    # alarme de emergência de dois tons (960/770 Hz, 0,25 s cada)
    alarm_w = synth("alarm", "0.22*(gt(sin(2*PI*(if(lt(mod(t,0.5),0.25),960,770))*t),0)*2-1)*(0.6+0.4*sin(2*PI*4*t))",
                    round(REWARD + 0.2, 2), f"lowpass=f=3500,afade=t=out:st={REWARD - 0.1:.2f}:d=0.3")
    # sirene de polícia genérica (varrimento), discreta
    wail = synth("wail", "0.18*sin(2*PI*(700*t+120*sin(2*PI*0.9*t)/(2*PI*0.9)*2*PI))", 3.0,
                 "lowpass=f=2500,afade=t=in:d=0.5,afade=t=out:st=2.0:d=1.0")
    twinkle = synth("twinkle", "0.25*(sin(2*PI*2093*t)+sin(2*PI*2637*t)*exp(-t*3))*exp(-t*6)", 0.8)
    shutter = noise("shutter", 0.3, "white", "highpass=f=1500,afade=t=out:st=0.02:d=0.2,volume=0.9")
    thud = synth("thud", "0.8*sin(2*PI*(70+120*exp(-t*30))*t)*exp(-t*12)", 0.4)
    static = noise("static", 1.4, "white", "highpass=f=1200,volume=0.25,afade=t=in:d=0.1,afade=t=out:st=1.0:d=0.4")
    events = [(engine, 0.0, 0.9), (alarm_w, 0.0, 0.55)]
    events += [(pop, x, 0.55) for x in STAR_ON]
    events += [(twinkle, REWARD, 0.5), (wail, T["sirens"] - 0.8, 0.35), (static, T["static"], 0.4)]
    events += [(swish, c - 0.25, 0.5) for c in (T["first"], T["second"], T["ride"], T["radio"], T["gas"], T["twist"], T["fine"], T["question"], T["because"])]
    events += [(pop, x, 0.45) for x in (T["slowly"], T["alleys"], T["garages"], T["door"], T["seven"], T["rocketA"], T["station"])]
    events += [(ding, x, 0.35) for x in DINGS]
    events += [(thud, T["bad"], 0.6), (thud, T["mom"] + 0.35, 0.4), (shutter, T["flash"], 0.8), (pop, POP_T + 1.0, 0.3)]
    ins, ch, lab = [], [], []
    for n, (f, x, v) in enumerate(events):
        idx = 3 + len(lab); ins += ["-i", f]; d = int(max(0, x) * 1000)
        ch.append(f"[{idx}:a]adelay={d}|{d},volume={v}[e{len(lab)}]"); lab.append(f"[e{len(lab)}]")
    sfx = ";".join(ch) + ";" + "".join(lab) + f"amix=inputs={len(lab)}:normalize=0[sfx]"
    od = int(OFF * 1000)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", NARR, "-stream_loop", "-1", "-i", MUSIC, *ins,
                    "-filter_complex",
                    f"[0:v]noise=alls=3:allf=t,subtitles={BLD}/captions.ass,format=yuv420p[v];"
                    f"[1:a]adelay={od}|{od},asplit=2[n1][nk];"
                    f"[2:a]atrim=0:{T_END},volume='if(lt(t,{REWARD + 0.3:.2f}),0,if(between(t,{T['twist'] - 0.5:.2f},{T['twist'] + 0.1:.2f}),0.08,0.35))':eval=frame,"
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
