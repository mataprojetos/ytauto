#!/usr/bin/env python3
"""Whatifaholic EP006 — What If You Fell Into a Black Hole?
Teste "só código": tudo desenhado em pycairo, sem imagens geradas. Único gasto: a voz (Bram).
Tom: viagem imersiva na primeira pessoa, calma e hipnótica.
Loop de frase: "Which means, right now…" → "You're falling into a black hole." (último frame = frame 0).
Uso: python3 anim_ep006.py [--frames t1,t2,...]   (sem argumentos: render completo + mistura)"""
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
OUT = f"{ROOT}/whatifaholic_ep006_blackhole.mp4"
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", NARR]))
N_FR = int(round(DUR * FPS))
T_END = N_FR / FPS          # acaba no fim de "right now…" e volta ao "You're falling…" do início
random.seed(6)

# ---------- cores (tema: espaço escuro + disco laranja/dourado) ----------
SPACE1 = (0.015, 0.012, 0.035); SPACE2 = (0.0, 0.0, 0.0)
HOT = (1.0, 0.96, 0.82); GOLD = (1.0, 0.78, 0.32); ORANGE = (1.0, 0.48, 0.1); EMBER = (0.75, 0.16, 0.04)
AMBER = (1.0, 0.71, 0.24); INK = (1, 1, 1); DARK = (0.02, 0.02, 0.03); GREY = (0.55, 0.57, 0.62)
ICE = (0.62, 0.8, 1.0); RED = (1.0, 0.3, 0.2)
CX, CY = 540, 860            # centro do buraco negro (acima das legendas)

# ---------- palavras ----------
words = json.load(open(f"{BLD}/words.json"))
FIX = {"hole,": "hole.", "and": "And", "feels": "feels…", "sun.": "Sun.", "notice,": "notice.", "edge,": "edge.",
       "no": "No", "place,": "place:", "back,": "back.", "not": "Not", "light,": "light.", "which": "Which",
       "now...": "now…", "normal,": "normal.", "but": "But"}
for i, w in enumerate(words):
    t = w["w"]
    if t == "head," and words[i - 2]["w"] == "Turn": t = "head…"
    elif t == "and" and i == 6: t = "And"
    elif t == "no" and words[i - 1]["w"] == "is": pass
    elif t in FIX and t != "and": t = FIX[t]
    w["w"] = t
if words[-1]["e"] > T_END: words[-1]["e"] = T_END


def bare(w): return re.sub(r"[^\w']", "", w).lower()


def at(tok, n=1, key="s"):
    k = 0
    for w in words:
        if bare(w["w"]) == tok:
            k += 1
            if k == n: return w[key]
    raise KeyError(tok)


T = dict(calm=at("calm"), this=at("this"), four=at("four"), sun=at("sun"), brand=at("that"), stars=at("stars") - 0.1,
         bend=at("bend"), light=at("light"), ring=at("ring"), turn=at("turn"), see=at("see"), backhead=at("back"),
         lightaround=at("light", 2) - 0.12, watch=at("watch") - 0.14, earth=at("earth"), years=at("years"),
         pass_=at("pass") - 0.18, edge=at("edge"), bump=at("bump"), sound=at("sound"), notice=at("notice", key="e"),
         wait=at("wait") - 0.5, inhere=at("in") - 0.05, every=at("every"), center=at("center"), noway=at("there"),
         notlight=at("not"), which=at("which"), now=at("now"))


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def seg(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= a)
def lerp(a, b, k): return a + (b - a) * k
def popin(t, a, d=0.22):
    if t < a: return 0.0
    x = clamp((t - a) / d)
    return 1 + 0.25 * math.sin(math.pi * x) * (1 - x) if x < 1 else 1.0


def rr(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()


def text(c, s, x, y, size, col, a=1.0, align="c", outline=True, ow=0.13, ocol=DARK, scale=1.0, rot=0.0, spacing=0):
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


def glow(c, x, y, r, col, a, r0=0):
    if a <= 0: return
    g = cairo.RadialGradient(x, y, r0, x, y, r)
    g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    c.set_source(g); c.arc(x, y, r, 0, 2 * math.pi); c.fill()


def space_bg(c, a=1.0):
    g = cairo.RadialGradient(CX, CY, 0, CX, CY, 1300)
    g.add_color_stop_rgba(0, 0.05, 0.03, 0.06, a); g.add_color_stop_rgba(0.5, *SPACE1, a); g.add_color_stop_rgba(1, *SPACE2, a)
    c.set_source(g); c.paint()


# ---------- céu com lente gravitacional ----------
STARS = []
for _ in range(520):
    ph = random.uniform(0, 2 * math.pi); u = random.random()
    col = random.choice([INK, INK, INK, ICE, (1, 0.9, 0.75), (1, 0.8, 0.6)])
    STARS.append((ph, u, random.uniform(0.35, 1.0), random.uniform(1.2, 3.4), col, random.uniform(0, 6.28)))
RHO_MIN, RHO_MAX = 25.0, 1500.0
LR = math.log(RHO_MAX / RHO_MIN)


def sky(c, t, cx=CX, cy=CY, Rs=200, thE=300, speed=0.12, a=1.0, spin=0.0, streak=1.0, secondary=True):
    """estrelas a afastar-se do centro (estamos a cair para ele), desviadas pela lente gravitacional.
    Imagem principal: r+ = (ρ + √(ρ²+4θE²))/2 ; secundária no lado oposto: r- = (√(ρ²+4θE²) − ρ)/2."""
    if a <= 0: return
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for ph, u, br, sz, col, tw in STARS:
        q = (u + speed * t / LR * 3.0) % 1.0          # posição radial em escala log (desliza para fora)
        rho = RHO_MIN * math.exp(q * LR)
        fade = smooth(q / 0.12) * smooth((1 - q) / 0.05)
        ang = ph + spin
        s = math.sqrt(rho * rho + 4 * thE * thE)
        imgs = [((rho + s) / 2, ang, 1.0)]
        if secondary and thE > 1:
            imgs.append(((s - rho) / 2, ang + math.pi, 0.75))
        twk = 0.8 + 0.2 * math.sin(t * 3 + tw)
        for r, an, m in imgs:
            if r < Rs * 1.02: continue
            mag = r / max(rho, 1) if m == 1.0 else r / max(rho, 1) * 0.6
            arcw = min(1.6, (sz * (0.6 + 1.6 * clamp(mag - 1, 0, 6)) + streak * speed * 30 * r / 900) / r)
            al = a * br * fade * twk * (m if m == 1.0 else 0.8)
            if al < 0.02: continue
            x, y = cx + r * math.cos(an), cy + r * math.sin(an)
            if not (-60 < x < W + 60 and -60 < y < H + 60): continue
            c.set_source_rgba(*col, clamp(al))
            c.set_line_width(sz * (1.0 if m == 1.0 else 0.8))
            # traço tangencial (arco curvado pela lente) + radial (velocidade)
            rad = streak * speed * 0.45 * r / 6
            c.new_path()
            c.arc(cx, cy, r, an - arcw / 2, an + arcw / 2)
            c.stroke()
            if rad > 2:
                c.set_line_width(sz * 0.7); c.set_source_rgba(*col, clamp(al * 0.6))
                c.move_to(x, y); c.line_to(x - rad * math.cos(an), y - rad * math.sin(an)); c.stroke()


# ---------- disco de acreção ----------
def disk_ring_color(k):
    """k: 0 (interior, quente) → 1 (exterior)"""
    if k < 0.35: return tuple(lerp(HOT[i], GOLD[i], k / 0.35) for i in range(3))
    if k < 0.7: return tuple(lerp(GOLD[i], ORANGE[i], (k - 0.35) / 0.35) for i in range(3))
    return tuple(lerp(ORANGE[i], EMBER[i], (k - 0.7) / 0.3) for i in range(3))


def disk_half(c, cx, cy, Rs, t, a, front, flat=0.2, rot_speed=1.0):
    n = 14
    for i in range(n):
        k = i / (n - 1)
        R = Rs * (1.55 + 1.75 * k)
        col = disk_ring_color(k)
        c.save(); c.translate(cx, cy); c.scale(1, flat); c.new_path()
        if front: c.arc(0, 0, R, 0, math.pi)
        else: c.arc_negative(0, 0, R, 0, -math.pi)
        c.restore()
        lw = Rs * 0.16 * (1.2 - 0.5 * k)
        al = a * (0.95 - 0.55 * k)
        c.set_line_width(lw * 1.8); c.set_source_rgba(*col, al * 0.25); c.stroke_preserve()
        c.set_line_width(lw); c.set_source_rgba(*col, al * 0.55)
        c.set_dash([R * 0.25, R * 0.12 + 8 * i], -t * rot_speed * (260 / (0.6 + k)) * (1 if front else -1))
        c.stroke(); c.set_dash([])


def black_hole(c, cx, cy, Rs, t, a=1.0, disk=1.0, rot=1.0, flat=0.2, halo=1.0):
    """sombra + anel de fotões + disco estilizado (parte de trás lensada por cima e por baixo da sombra)"""
    if disk > 0:
        glow(c, cx, cy, Rs * 4.2, ORANGE, 0.22 * a * disk, r0=Rs)
        disk_half(c, cx, cy, Rs, t, a * disk, front=False, flat=flat, rot_speed=rot)
        # parte de trás do disco, desviada pela lente: arcos à volta da sombra (mais forte em cima e em baixo)
        for j in range(9):
            k = j / 8
            R = Rs * (1.05 + 0.5 * k)
            for sgn in (1, -1):
                c.new_path(); c.arc(cx, cy, R, -math.pi + 0.05, -0.05) if sgn > 0 else c.arc(cx, cy, R * 0.92, 0.05, math.pi - 0.05)
                col = disk_ring_color(k * 0.9)
                c.set_line_width(Rs * 0.07 * (1.3 - k)); c.set_source_rgba(*col, a * disk * halo * (0.75 - 0.6 * k) * (1 if sgn > 0 else 0.55))
                c.set_dash([Rs * 0.5, Rs * 0.08], t * rot * 180 * sgn); c.stroke(); c.set_dash([])
    # sombra
    c.set_source_rgba(0, 0, 0, a); c.arc(cx, cy, Rs, 0, 2 * math.pi); c.fill()
    # anel de fotões (sempre um pouco visível)
    pr = 0.35 + 0.65 * disk
    for lw, al in ((Rs * 0.06, 0.25), (Rs * 0.022, 0.9)):
        c.set_line_width(lw); c.set_source_rgba(*HOT, a * al * pr); c.arc(cx, cy, Rs * 1.025, 0, 2 * math.pi); c.stroke()
    if disk > 0:
        disk_half(c, cx, cy, Rs, t, a * disk, front=True, flat=flat, rot_speed=rot)
        # lado que se aproxima (esquerda) mais brilhante: beaming
        glow(c, cx - Rs * 1.9, cy, Rs * 0.9, HOT, 0.18 * a * disk)


def visor(c, a=1.0):
    """capacete: vinheta curva + reflexo subtil (vista na primeira pessoa)"""
    if a <= 0: return
    g = cairo.RadialGradient(W / 2, H * 0.46, H * 0.36, W / 2, H * 0.46, H * 0.72)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.85 * a)
    c.set_source(g); c.paint()
    c.set_source_rgba(1, 1, 1, 0.05 * a); c.set_line_width(26)
    c.arc(W / 2, H * 0.46, H * 0.55, math.pi * 1.12, math.pi * 1.32); c.stroke()


def hud(c, t, a=1.0):
    """leitura do capacete: distância até à borda (horizonte), conta até 0 em 'You pass the edge'"""
    if a <= 0: return
    tp = T["pass_"] + 0.5
    k = clamp(t / tp)
    km = int(round(4800000 * (1 - k) ** 1.7 / 1000) * 1000) if t < tp else 0
    s = f"{km:,} km" if km > 0 else "0 km"
    c.set_source_rgba(0, 0, 0, 0.45 * a); rr(c, 300, 158, 480, 92, 20); c.fill()
    blink = 0.6 + 0.4 * math.sin(t * 5)
    c.set_source_rgba(*AMBER, 0.75 * a * blink); c.set_line_width(3); rr(c, 300, 158, 480, 92, 20); c.stroke()
    text(c, "DISTANCE TO THE EDGE", 540, 182, 24, AMBER, a * 0.9, outline=False)
    text(c, s, 540, 222, 44, INK, a, outline=False)


# ---------- cenas ----------
def r_hook(t):
    """raio da sombra na cena de abertura (cresce: estamos a cair)"""
    return 175 * math.exp(0.085 * t)


def s_hook(c, t):
    """abertura: já a cair. t pode ser negativo (fim do vídeo → frame 0)."""
    space_bg(c)
    Rs = r_hook(t)
    sky(c, t + 3.0, Rs=Rs, thE=Rs * 1.45, speed=0.22, streak=1.4)
    flash = 0.0
    black_hole(c, CX, CY, Rs, t, disk=0.85 + 0.15 * smooth(t / 1.5), rot=1.0)
    visor(c, 1.0)
    hud(c, max(t, 0))
    # pulso inicial (impacto visual imediato sem alarme)
    if t < 0.5:
        flash = 0.0


def s_mass(c, t):
    u = t - T["this"]
    space_bg(c)
    Rs = r_hook(T["this"]) * (1 - 0.35 * seg(u, 0, 0.5))
    cx = CX
    sky(c, t + 3.0, Rs=Rs, thE=Rs * 1.45, speed=0.1)
    black_hole(c, cx, CY - 60 * seg(u, 0, 0.5), Rs, t, disk=1.0)
    # o Sol, minúsculo, ao lado
    sx, sy = 845, 1190
    sa = seg(u, 0.3, 0.6)
    glow(c, sx, sy, 60, GOLD, 0.6 * sa)
    c.set_source_rgba(1, 0.9, 0.5, sa); c.arc(sx, sy, 9, 0, 2 * math.pi); c.fill()
    text(c, "THE SUN", sx, sy + 46, 30, GOLD, sa, outline=False)
    c.set_source_rgba(1, 1, 1, 0.5 * sa); c.set_line_width(2); c.set_dash([6, 6])
    c.move_to(sx - 24, sy - 12); c.line_to(cx + 160, CY + 60); c.stroke(); c.set_dash([])
    k = seg(t, T["four"], T["sun"])
    n = int(4_000_000 * (k ** 2.2))
    sc = popin(t, T["four"] - 0.05)
    text(c, f"{n:,}×", 540, 330, 112, GOLD, sc > 0, scale=sc, ow=0.1)
    text(c, "HEAVIER THAN THE SUN", 540, 430, 46, INK, seg(t, T["sun"] - 0.3, T["sun"]), outline=True)
    visor(c, 0.8); hud(c, t, 0.0)


def s_brand(c, t):
    u = t - T["brand"]
    space_bg(c)
    Rs = 120
    sky(c, t, Rs=Rs, thE=Rs * 1.4, speed=0.06, a=0.6)
    black_hole(c, CX, 620, Rs, t, a=0.5, disk=0.7)
    draw_scratch(c, u, 540, 820, scale=0.95, skin=(0.96, 0.78, 0.62), accent=AMBER, ink=INK)


def s_bend(c, t):
    """as estrelas começam a curvar: a lente cresce"""
    u = t - T["stars"]
    space_bg(c)
    Rs = 190 + 30 * seg(u, 0, 2.4)
    th = Rs * lerp(0.6, 1.9, smooth(u / 2.0))
    sky(c, t, Rs=Rs, thE=th, speed=0.05, streak=0.4)
    # anel de Einstein fraco a formar-se
    c.set_source_rgba(*ICE, 0.18 * smooth(u / 2)); c.set_line_width(5); c.arc(CX, CY, th, 0, 2 * math.pi); c.stroke()
    black_hole(c, CX, CY, Rs, t, disk=0.0)
    # guias: linhas de luz a curvar à volta
    k = seg(u, 0.3, 1.6)
    for i in range(7):
        y0 = CY - 420 + i * 140
        if abs(y0 - CY) < 60: continue
        c.new_path(); c.move_to(-20, y0)
        b = Rs * 1.7 * (1 if y0 > CY else -1)
        dy = (y0 - CY)
        pull = k * Rs * 2.2 * 1 / (1 + (abs(dy) / Rs) ** 1.4) * (1 if dy > 0 else -1)
        c.curve_to(CX - 300, y0, CX - 120, y0 + pull, CX, y0 + pull * 1.25)
        c.curve_to(CX + 120, y0 + pull, CX + 300, y0, W + 20, y0)
        c.set_source_rgba(*ICE, 0.28 * k); c.set_line_width(3); c.set_dash([18, 12], -t * 120); c.stroke(); c.set_dash([])
    visor(c); hud(c, t)


def s_ring(c, t):
    u = t - T["light"]
    space_bg(c)
    Rs = 220 + 25 * seg(u, 0, 3)
    sky(c, t, Rs=Rs, thE=Rs * 1.9, speed=0.05, streak=0.3)
    d = seg(u, 0.0, 1.8)
    black_hole(c, CX, CY, Rs, t, disk=d, rot=1.2)
    if t > T["ring"] - 0.1:
        f = seg(t, T["ring"] - 0.1, T["ring"] + 0.4) * (1 - 0.6 * seg(t, T["ring"] + 0.4, T["ring"] + 1.2))
        glow(c, CX, CY, Rs * 3.2, ORANGE, 0.35 * f, r0=Rs)
    visor(c); hud(c, t)


def astronaut_back(c, x, y, s, a=1.0, rim=ORANGE):
    """nuca de um astronauta (capacete visto por trás), com luz de contorno do anel"""
    c.save(); c.translate(x, y); c.scale(s, s)
    # ombros + mochila
    c.set_source_rgba(0.12, 0.12, 0.15, a)
    c.move_to(-260, 420); c.curve_to(-250, 220, -170, 170, 0, 165); c.curve_to(170, 170, 250, 220, 260, 420); c.close_path(); c.fill()
    c.set_source_rgba(0.2, 0.2, 0.24, a); rr(c, -150, 150, 300, 230, 30); c.fill()
    c.set_source_rgba(0.3, 0.3, 0.35, a); rr(c, -100, 200, 200, 26, 10); c.fill(); rr(c, -100, 250, 200, 26, 10); c.fill()
    # capacete
    g = cairo.RadialGradient(-40, -60, 20, 0, 0, 175)
    g.add_color_stop_rgba(0, 0.42, 0.42, 0.48, a); g.add_color_stop_rgba(1, 0.1, 0.1, 0.13, a)
    c.set_source(g); c.arc(0, 0, 165, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.06, 0.06, 0.08, a); c.set_line_width(14); c.arc(0, 0, 165, math.pi * 0.15, math.pi * 0.85); c.stroke()
    # luz de contorno (o anel atrás)
    for lw, al in ((22, 0.25), (8, 0.9)):
        c.set_line_width(lw); c.set_source_rgba(*rim, a * al)
        c.arc(0, 0, 166, math.pi * 1.05, math.pi * 1.95); c.stroke()
        c.arc(0, 0, 166, -0.35, 0.25); c.stroke()
        c.new_path(); c.arc(0, 0, 166, math.pi - 0.25, math.pi + 0.35); c.stroke()
    c.restore()


def s_turn(c, t):
    """vira a cabeça: pan da câmara → à frente, a tua própria nuca, dentro do anel de luz"""
    u = t - T["turn"]
    pan = smooth(u / 0.85)
    space_bg(c)
    Rs = 245
    # vista antiga a sair para a esquerda, nova a entrar pela direita (rotação da câmara)
    for off, view in ((-pan * W * 1.15, 0), ((1 - pan) * W * 1.15, 1)):
        if abs(off) > W * 1.1: continue
        c.save(); c.translate(off, 0)
        if view == 0:
            sky(c, t, Rs=Rs, thE=Rs * 1.9, speed=0.05, spin=-pan * 0.6, streak=0.3)
            black_hole(c, CX, CY, Rs, t, disk=1.0)
        else:
            sky(c, t, Rs=Rs, thE=Rs * 1.9, speed=0.05, spin=(1 - pan) * 0.6, streak=0.3)
            black_hole(c, CX, CY, Rs, t, disk=1.0)
            k = seg(t, T["see"] - 0.2, T["backhead"])
            glow(c, CX, CY, 330, GOLD, 0.25 * k)
            astronaut_back(c, CX, CY - 10, 0.62 * (0.85 + 0.15 * k), a=k)
        c.restore()
    if 0.05 < u < 0.85:   # rasto de movimento
        c.set_source_rgba(1, 1, 1, 0.08 * math.sin(math.pi * u / 0.85)); c.paint()
    visor(c); hud(c, t)
    if t > T["backhead"]:
        text(c, "THAT'S YOU", 540, 470, 64, AMBER, seg(t, T["backhead"], T["backhead"] + 0.25), scale=popin(t, T["backhead"]))


def s_around(c, t):
    """a luz deu a volta toda: diagrama do raio a contornar o buraco negro e voltar a ti"""
    u = t - T["lightaround"]
    space_bg(c)
    Rs = 190
    sky(c, t, Rs=Rs, thE=Rs * 1.6, speed=0.04, a=0.7, streak=0.2)
    black_hole(c, CX, CY, Rs, t, disk=0.55)
    # tu (ponto) em baixo
    yx, yy = CX, CY + 420
    c.set_source_rgba(*INK, 0.9); c.arc(yx, yy, 16, 0, 2 * math.pi); c.fill()
    text(c, "YOU", yx + 62, yy + 2, 34, INK, 0.9, outline=False)
    # raio: sai de ti, sobe pela esquerda, dá a volta (esfera de fotões) e regressa pela direita
    k = clamp(u / 1.5)
    R = Rs * 1.5
    pts = []
    n = 120
    for i in range(n + 1):
        s = i / n
        if s < 0.25:
            q = s / 0.25; px = lerp(yx - 30, CX - R, smooth(q)); py = lerp(yy - 10, CY + 40, q)
        elif s < 0.75:
            q = (s - 0.25) / 0.5; an = math.pi - 0.2 + q * (math.pi + 0.4)
            px = CX + R * math.cos(an); py = CY + 40 * (1 - q) + R * math.sin(-an) * -1 if False else CY + R * math.sin(an) * -1 + 40 * (1 - abs(2 * q - 1))
            px = CX + R * math.cos(math.pi - q * math.pi * 1.0 - 0.0)
            py = CY - R * math.sin(math.pi - q * math.pi)
        else:
            q = (s - 0.75) / 0.25; px = lerp(CX + R, yx + 30, smooth(q)); py = lerp(CY, yy - 10, q)
        pts.append((px, py))
    m = int(k * n)
    if m > 1:
        for lw, al in ((16, 0.18), (5, 0.95)):
            c.new_path(); c.move_to(*pts[0])
            for p in pts[1:m]: c.line_to(*p)
            c.set_source_rgba(*GOLD, al); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
        hx, hy = pts[m - 1]
        glow(c, hx, hy, 40, HOT, 0.9)
    if k >= 1:
        text(c, "360°", 540, 330, 120, GOLD, seg(u, 1.5, 1.75), scale=popin(t, T["lightaround"] + 1.5))
    visor(c); hud(c, t)


def clock(c, x, y, r, sec_ang, min_ang, hr_ang, rim, a=1.0, blur=0.0):
    c.set_source_rgba(0.04, 0.04, 0.06, 0.9 * a); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(*rim, a); c.set_line_width(10); c.arc(x, y, r, 0, 2 * math.pi); c.stroke()
    for i in range(12):
        an = i * math.pi / 6
        c.set_line_width(6 if i % 3 == 0 else 3); c.set_source_rgba(1, 1, 1, 0.8 * a)
        c.move_to(x + r * 0.82 * math.sin(an), y - r * 0.82 * math.cos(an)); c.line_to(x + r * 0.92 * math.sin(an), y - r * 0.92 * math.cos(an)); c.stroke()
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for ang, L, lw, col in ((hr_ang, 0.5, 12, INK), (min_ang, 0.72, 8, INK), (sec_ang, 0.82, 4, rim)):
        if blur > 0.3 and col is INK:   # ponteiros a voar: leque de rasto
            for j in range(6):
                aa = ang - j * 0.35 * blur
                c.set_source_rgba(1, 1, 1, a * 0.5 * (1 - j / 6)); c.set_line_width(lw)
                c.move_to(x, y); c.line_to(x + r * L * math.sin(aa), y - r * L * math.cos(aa)); c.stroke()
        else:
            c.set_source_rgba(*col, a); c.set_line_width(lw)
            c.move_to(x, y); c.line_to(x + r * L * math.sin(ang), y - r * L * math.cos(ang)); c.stroke()
    c.set_source_rgba(*INK, a); c.arc(x, y, 9, 0, 2 * math.pi); c.fill()


def s_watch(c, t):
    u = t - T["watch"]
    space_bg(c)
    Rs = 260
    sky(c, t, Rs=Rs, thE=Rs * 1.8, speed=0.04, a=0.5)
    black_hole(c, CX, CY + 40, Rs, t, a=0.45, disk=0.6)
    c.set_source_rgba(0, 0, 0, 0.35); c.paint()
    # o teu relógio (normal)
    a1 = seg(u, 0, 0.3)
    s1 = popin(t, T["watch"])
    c.save(); c.translate(290, 800); c.scale(max(s1, 1e-3), max(s1, 1e-3))
    sec = math.floor(u) * math.pi / 30 + (math.pi / 30) * ease((u % 1) / 0.12)
    clock(c, 0, 0, 175, sec, 1.9, 5.3, AMBER, a1)
    c.restore()
    text(c, "YOU", 290, 1030, 56, AMBER, a1)
    text(c, "NORMAL", 290, 1090, 32, INK, a1 * 0.8, outline=False)
    # relógio da Terra (a voar)
    ea = seg(t, T["earth"] - 0.15, T["earth"] + 0.15)
    s2 = popin(t, T["earth"] - 0.15)
    v = seg(t, T["earth"], T["years"] + 0.6)
    ue = max(0, t - T["earth"])
    spin = ue * ue * 9 * (1 + 3 * v)
    c.save(); c.translate(790, 800); c.scale(max(s2, 1e-3), max(s2, 1e-3))
    clock(c, 0, 0, 175, spin * 12, spin, spin / 12 * 5, ICE, ea, blur=v)
    c.restore()
    text(c, "EARTH", 790, 1030, 56, ICE, ea)
    yr = 2026 + int((ue ** 2.4) * 22)
    text(c, f"YEAR {yr}", 790, 1090, 34, INK, ea * seg(t, T["years"] - 0.3, T["years"]), outline=False)
    # planetinha Terra a girar por cima
    if ea > 0:
        ex, ey = 790, 560
        c.set_source_rgba(0.2, 0.45, 0.95, ea); c.arc(ex, ey, 48, 0, 2 * math.pi); c.fill()
        c.save(); c.arc(ex, ey, 48, 0, 2 * math.pi); c.clip()
        c.set_source_rgba(0.25, 0.75, 0.35, ea)
        for j in range(3):
            px = ex - 60 + ((spin * 8 + j * 45) % 150)
            c.arc(px, ey - 12 + j * 14, 16, 0, 2 * math.pi); c.fill()
        c.restore()
    visor(c, 0.6); hud(c, t)


def s_edge(c, t):
    """a borda: a escuridão enche o ecrã, o horizonte passa... e nada acontece"""
    u = t - T["pass_"]
    c.set_source_rgb(0, 0, 0); c.paint()
    k = smooth(u / 0.9)
    Rs = lerp(300, 1500, k ** 1.6)
    if k < 1:
        c.save()
        space_bg(c, 1 - k)
        sky(c, t, Rs=Rs, thE=Rs * 1.6, speed=0.1, a=1 - k, streak=1.0)
        black_hole(c, CX, CY, Rs, t, disk=1 - k)
        c.restore()
    # linha do horizonte de eventos a passar por ti
    hr = lerp(200, 1600, smooth(u / 1.1))
    ha = (1 - seg(u, 0.8, 1.4))
    c.set_source_rgba(*AMBER, 0.85 * ha); c.set_line_width(4); c.set_dash([22, 14], t * 40)
    c.arc(CX, CY, hr, 0, 2 * math.pi); c.stroke(); c.set_dash([])
    text(c, "EVENT HORIZON", CX, CY - hr - 34 if CY - hr - 34 > 120 else 330, 40, AMBER, ha * (CY - hr > 40), outline=False)
    # depois: o universo lá fora encolhe para uma janela de luz atrás de ti (ao centro, pequena)
    if u > 0.9:
        wa = seg(u, 0.9, 1.6)
        wr = lerp(260, 95, smooth((u - 0.9) / 2.5))
        c.save(); c.arc(CX, 760, wr, 0, 2 * math.pi); c.clip()
        space_bg(c, wa)
        sky(c, t, cx=CX, cy=760, Rs=0, thE=0, speed=0.02, a=wa, streak=0, secondary=False)
        c.restore()
        c.set_source_rgba(*GOLD, 0.6 * wa); c.set_line_width(5); c.arc(CX, 760, wr, 0, 2 * math.pi); c.stroke()
        glow(c, CX, 760, wr * 1.6, ORANGE, 0.12 * wa, r0=wr)
    visor(c, 0.7)
    if u < 1.8:
        hud(c, t, 1 - seg(u, 1.2, 1.8))
    # "nada": pequenos rótulos calmos
    if t > T["bump"]:
        text(c, "0 BUMP", 300, 1180, 44, GREY, seg(t, T["bump"], T["bump"] + 0.2) * (1 - seg(t, T["wait"], T["wait"] + 0.3)), outline=False)
    if t > T["sound"]:
        text(c, "0 dB", 780, 1180, 44, GREY, seg(t, T["sound"], T["sound"] + 0.2) * (1 - seg(t, T["wait"], T["wait"] + 0.3)), outline=False)


# linhas de queda para o centro (cada direção leva ao mesmo sítio)
LINES = [(i * 2 * math.pi / 28 + random.uniform(-0.05, 0.05), random.uniform(0.6, 1.0)) for i in range(28)]


def converge(c, t, t0, a=1.0, swirl=1.6, center_pull=0.0):
    """linhas de estrelas a cair em espiral para o centro, com setas a correr nelas"""
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for i, (an0, br) in enumerate(LINES):
        pts = []
        for j in range(60):
            s = j / 59                        # 0 = borda do ecrã, 1 = centro
            r = 1150 * (1 - s) ** 1.15 * (1 - center_pull) + 2
            an = an0 + swirl * s ** 1.6 + 0.08 * math.sin(t * 0.7 + i)
            pts.append((CX + r * math.cos(an), CY + r * math.sin(an)))
        c.new_path(); c.move_to(*pts[0])
        for p in pts[1:]: c.line_to(*p)
        col = GOLD if i % 3 else ICE
        c.set_source_rgba(*col, 0.32 * a * br); c.set_line_width(3); c.stroke()
        # setas a correr para dentro
        for m in range(2):
            q = ((t - t0) * 0.5 + m * 0.5 + i * 0.137) % 1.0
            jj = int(q ** 0.8 * 58)
            (x0, y0), (x1, y1) = pts[jj], pts[jj + 1]
            ang = math.atan2(y1 - y0, x1 - x0)
            al = a * br * smooth(q / 0.15) * (1 - smooth((q - 0.85) / 0.15))
            sz = 22 * (1 - q * 0.7)
            c.save(); c.translate(x1, y1); c.rotate(ang)
            c.move_to(sz, 0); c.line_to(-sz * 0.8, sz * 0.6); c.line_to(-sz * 0.4, 0); c.line_to(-sz * 0.8, -sz * 0.6); c.close_path()
            c.set_source_rgba(*col, al); c.fill(); c.restore()
    # o centro
    glow(c, CX, CY, 140, ORANGE, 0.35 * a)
    c.set_source_rgba(0, 0, 0, a); c.arc(CX, CY, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(*HOT, 0.7 * a); c.set_line_width(3); c.arc(CX, CY, 36, 0, 2 * math.pi); c.stroke()


def s_tease(c, t):
    u = t - T["wait"]
    c.set_source_rgb(0, 0, 0); c.paint()
    # a janela lá de fora continua atrás (pequena) e as primeiras linhas aparecem a medo
    wr = 95 - 30 * smooth(u / 3)
    c.save(); c.arc(CX, 760 - 120 * smooth(u / 3), wr, 0, 2 * math.pi); c.clip(); space_bg(c, 0.8)
    sky(c, t, cx=CX, cy=760, Rs=0, thE=0, speed=0.02, a=0.8, streak=0, secondary=False); c.restore()
    c.set_source_rgba(*GOLD, 0.5); c.set_line_width(4); c.arc(CX, 760 - 120 * smooth(u / 3), wr, 0, 2 * math.pi); c.stroke()
    a = 0.25 * smooth(u / 2.5)
    c.save(); c.translate(0, 0); converge(c, t, T["wait"], a=a, swirl=0.6); c.restore()
    text(c, "?", CX, CY + 10, 140, AMBER, 0.6 + 0.3 * math.sin(t * 4), scale=popin(t, T["wait"] + 0.2))
    visor(c, 0.6)


def s_inside(c, t):
    u = t - T["inhere"]
    c.set_source_rgb(0, 0, 0); c.paint()
    g = cairo.RadialGradient(CX, CY, 0, CX, CY, 1100)
    g.add_color_stop_rgba(0, 0.18, 0.07, 0.02, 1); g.add_color_stop_rgba(1, 0, 0, 0, 1)
    c.set_source(g); c.paint()
    a = seg(u, 0, 0.5)
    converge(c, t, T["inhere"], a=a, swirl=lerp(0.6, 2.2, smooth(u / 3)))
    # "every way you turn": uma seta-tu a rodar; cada direção curva para o centro
    if T["every"] <= t < T["center"] + 0.4:
        v = t - T["every"]
        ang = v * 2.4
        px, py = CX + 330 * math.cos(ang + 0.9), CY + 330 * math.sin(ang + 0.9)
        pa = seg(v, 0, 0.2) * (1 - seg(t, T["center"], T["center"] + 0.4))
        c.set_source_rgba(*INK, pa); c.arc(px, py, 14, 0, 2 * math.pi); c.fill()
        for d in range(3):
            da = ang + d * 2.1
            c.new_path(); c.move_to(px, py)
            ex, ey = px + 160 * math.cos(da), py + 160 * math.sin(da)
            c.curve_to(ex, ey, (ex + CX) / 2, (ey + CY) / 2, CX, CY)
            c.set_source_rgba(*AMBER, 0.8 * pa); c.set_line_width(5); c.set_dash([14, 10], -t * 160); c.stroke(); c.set_dash([])
    if t >= T["center"]:
        k = seg(t, T["center"], T["center"] + 0.3)
        f = (1 - seg(t, T["center"] + 0.3, T["center"] + 1.0))
        glow(c, CX, CY, 260, HOT, 0.5 * k * f)
        text(c, "THE CENTER", CX, CY + 110, 48, HOT, k * (1 - seg(t, T["noway"] - 0.2, T["noway"])), outline=True)
    if t >= T["noway"]:
        text(c, "NO WAY BACK", 540, 360, 108, RED, 1, scale=popin(t, T["noway"]), ow=0.1)
    if t >= T["notlight"]:
        # um raio de luz tenta sair... e curva de volta para o centro
        v = clamp((t - T["notlight"]) / 1.0)
        pts = []
        for j in range(80):
            s = j / 79
            r = 520 * math.sin(math.pi * s) ** 0.8
            an = -math.pi / 2 + 0.25 + 1.6 * s
            pts.append((CX + r * math.cos(an), CY + r * math.sin(an)))
        m = max(2, int(v * 80))
        for lw, al in ((18, 0.2), (6, 1.0)):
            c.new_path(); c.move_to(*pts[0])
            for p in pts[1:m]: c.line_to(*p)
            c.set_source_rgba(*HOT, al); c.set_line_width(lw); c.stroke()
        glow(c, *pts[m - 1], 46, HOT, 0.9)
        text(c, "NOT EVEN LIGHT", 540, 470, 66, HOT, 1, scale=popin(t, T["notlight"]))
    visor(c, 0.5)


def s_end(c, t):
    """'Which means, right now…': tudo é puxado para o centro, a escuridão do centro enche o ecrã
    e nos últimos frames volta a abrir-se exatamente no frame 0 (s_hook em t negativo)."""
    u = t - T["which"]
    TR = 0.42                          # duração da transformação final
    tr0 = T_END - TR
    if t < tr0:
        c.set_source_rgb(0, 0, 0); c.paint()
        g = cairo.RadialGradient(CX, CY, 0, CX, CY, 1100)
        g.add_color_stop_rgba(0, 0.18, 0.07, 0.02, 1); g.add_color_stop_rgba(1, 0, 0, 0, 1)
        c.set_source(g); c.paint()
        p = smooth(u / (tr0 - T["which"]))
        converge(c, t, T["inhere"], a=1 - 0.3 * p, swirl=2.2 + 2.0 * p, center_pull=0.0)
        text(c, "NO WAY BACK", 540, 360, 108, RED, 1 - seg(u, 0, 0.35), ow=0.1)
        text(c, "NOT EVEN LIGHT", 540, 470, 66, HOT, 1 - seg(u, 0, 0.35))
        # a escuridão do centro cresce
        dr = lerp(34, 1300, smooth((u - 0.2) / (tr0 - T["which"] - 0.2)) ** 1.8)
        c.set_source_rgb(0, 0, 0); c.arc(CX, CY, dr, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(*HOT, 0.5 * (1 - p)); c.set_line_width(3); c.arc(CX, CY, dr + 2, 0, 2 * math.pi); c.stroke()
        visor(c, 0.5)
    else:
        # o escuro encolhe até à sombra do buraco negro do frame 0 → último frame = frame 0 (continua o movimento)
        th = t - T_END                   # negativo: o mesmo relógio da abertura
        s_hook(c, th)
        k = (t - tr0) / (TR - 1 / FPS)   # 0 → 1 no último frame
        k = clamp(k)
        R0 = r_hook(th)
        dr = lerp(1300, R0, ease(k))
        if k < 1:
            c.set_source_rgba(0, 0, 0, 1 - k ** 3)
            c.arc(CX, CY, dr, 0, 2 * math.pi); c.fill()


SCENES = [
    (0.0, T["this"], s_hook), (T["this"], T["brand"], s_mass), (T["brand"], T["stars"], s_brand),
    (T["stars"], T["light"], s_bend), (T["light"], T["turn"], s_ring), (T["turn"], T["lightaround"], s_turn),
    (T["lightaround"], T["watch"], s_around), (T["watch"], T["pass_"], s_watch), (T["pass_"], T["wait"], s_edge),
    (T["wait"], T["inhere"], s_tease), (T["inhere"], T["which"], s_inside), (T["which"], 99, s_end),
]
NO_PUNCH = {s_edge, s_end, s_turn}

# ---------- sobreposições ----------
SUB_T0 = T["sound"] - 0.55           # pop-up de subscrição antes de "But wait until you see" (sobre o escuro, sem tapar o anel)
BADGE = (T["wait"] + 0.35, T["inhere"])


def badge(c, t):
    a0, a1 = BADGE
    if not (a0 <= t < a1 + 0.35): return
    k = popin(t, a0, 0.25); out = seg(t, a1, a1 + 0.3); a = 1 - out
    c.save(); c.translate(540, 200); c.scale(k * (1 + 0.4 * out), k * (1 + 0.4 * out))
    c.set_source_rgba(0, 0, 0, 0.65 * a); rr(c, -330, -42, 660, 84, 42); c.fill()
    pulse = 0.6 + 0.4 * math.sin(t * 6)
    c.set_source_rgba(*AMBER, a * pulse); c.set_line_width(5); rr(c, -330, -42, 660, 84, 42); c.stroke()
    c.set_source_rgba(*AMBER, a); rr(c, -295, -12, 36, 30, 6); c.fill()
    c.set_line_width(6); c.arc(-277, -12, 12, math.pi, 2 * math.pi); c.stroke()
    c.restore()
    text(c, "WHAT'S INSIDE · COMING UP", 560, 200, 38, INK, a * (k > 0), outline=False, scale=k)


def bell_icon(c, x, y, s, col, a, rot):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s); c.set_source_rgba(*col, a)
    c.move_to(-14, 8); c.curve_to(-14, -6, -12, -18, 0, -18); c.curve_to(12, -18, 14, -6, 14, 8); c.line_to(18, 12); c.line_to(-18, 12); c.close_path(); c.fill()
    c.arc(0, 16, 5, 0, 6.283); c.fill(); c.rectangle(-2, -23, 4, 6); c.fill(); c.restore()


def check(c, x, y, s, col, a, k=1.0):
    c.set_source_rgba(*col, a); c.set_line_width(s * 0.18); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(x - s * 0.4, y); c.line_to(x - s * 0.1, y + s * 0.3 * min(1, k * 2))
    if k > 0.5: c.line_to(x - s * 0.1 + s * 0.55 * (k - 0.5) * 2, y + s * 0.3 - s * 0.65 * (k - 0.5) * 2)
    c.stroke()


def subscribe(c, t):
    """pop-up de subscrição (baseado em lib/subscribe_popup.py, cores do tema)"""
    u = t - SUB_T0
    if u < 0 or u > 2.6: return
    inn = seg(u, 0, 0.35); out = seg(u, 2.2, 2.55); a = inn * (1 - out)
    done = u > 1.0
    w, h = 660, 104; x = (W - w) / 2; y = 330 - 40 * (1 - inn) - 30 * out
    sc = 0.92 + 0.08 * inn - 0.05 * math.sin(math.pi * clamp((u - 0.85) / 0.25))
    c.save(); c.translate(W / 2, y + h / 2); c.scale(sc, sc); c.translate(-W / 2, -(y + h / 2))
    c.set_source_rgba(0.06, 0.03, 0.01, 0.9 * a); rr(c, x, y, w, h, h / 2); c.fill()
    col = GREY if done else AMBER
    c.set_source_rgba(*col, 0.95 * a); c.set_line_width(4); rr(c, x, y, w, h, h / 2); c.stroke()
    wig = 0.35 * math.sin((u - 1.0) * 28) * math.exp(-(u - 1.0) * 5) if done else 0
    bell_icon(c, x + 64, y + h / 2 - 2, 1.25, INK if done else AMBER, a, wig)
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    if not done:
        c.set_font_size(40); c.set_source_rgba(*INK, a); c.move_to(x + 110, y + h / 2 + 14); c.show_text("SUBSCRIBE")
        c.set_font_size(30); c.set_source_rgba(*GOLD, a); c.move_to(x + 345, y + h / 2 + 11); c.show_text("for more what ifs")
    else:
        c.set_font_size(40); c.set_source_rgba(*INK, a); c.move_to(x + 110, y + h / 2 + 14); c.show_text("SUBSCRIBED")
        check(c, x + 410, y + h / 2 - 2, 40, GOLD, a, clamp((u - 1.0) / 0.25))
    c.restore()
    if 0.5 < u < 1.5:
        fx = x + w - 120; fy = y + h / 2
        pa = seg(u, 0.5, 0.8) * (1 - seg(u, 1.2, 1.5)); tap = seg(u, 0.85, 1.0)
        c.set_source_rgba(1, 1, 1, 0.55 * pa * a); c.arc(fx, fy + 60 * (1 - seg(u, 0.5, 0.85)), 34 - 8 * tap, 0, 6.283); c.fill()
        if u > 0.95:
            q = (u - 0.95) / 0.5
            c.set_source_rgba(*GOLD, 0.6 * (1 - q) * a); c.set_line_width(4); c.arc(fx, fy, 30 + 90 * q, 0, 6.283); c.stroke()


def render_scene(fn, t):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_GOOD)
    fn(c, t); return s


def frame_surface(t):
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); ctx = cairo.Context(out)
    for i, (a, b, fn) in enumerate(SCENES):
        if a <= t < b:
            cur = render_scene(fn, t)
            x = (t - a) / 0.3
            if i > 0 and x < 1 and fn not in NO_PUNCH:   # entrada suave (calmo): zoom lento + fundido curto
                z = 1.05 - 0.05 * ease(x)
                ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2)
                ctx.set_source_surface(cur, 0, 0); ctx.paint(); ctx.restore()
                ctx.set_source_rgba(0, 0, 0, 0.5 * (1 - ease(x))); ctx.paint()
            else:
                ctx.set_source_surface(cur, 0, 0); ctx.paint()
            break
    badge(ctx, t)
    subscribe(ctx, t)
    return out


def frame(t):
    s = frame_surface(t)
    return np.ndarray((H, W, 4), np.uint8, s.get_data())[:, :, [2, 1, 0]].tobytes()


# ---------- legendas (ASS, palavra a palavra) ----------
WEAK = {"a", "an", "the", "to", "of", "for", "on", "in", "it", "and", "but", "is", "your", "you", "or", "by", "that", "my", "me", "no"}
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
    if re.search(r"[.?!:…,]$", w["w"]):
        groups.append(cur); cur = []
if cur: groups.append(cur)


def ts(x):
    h, r = divmod(max(x, 0), 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


HL, WH = "&H003CB4FF&", "&H00FFFFFF&"   # destaque âmbar (BGR) — contraste quente sobre o espaço escuro
ev = []
for gi, g in enumerate(groups):
    g_end = min(groups[gi + 1][0]["s"], g[-1]["e"] + 0.4) if gi + 1 < len(groups) else T_END
    for k, w in enumerate(g):
        s = w["s"]; e = g[k + 1]["s"] if k + 1 < len(g) else g_end
        if e <= s: continue
        pop = "{\\fscx108\\fscy108\\t(0,100,\\fscx100\\fscy100)}" if k == 0 else ""
        txt = " ".join((f"{{\\c{HL}}}{x['w'].upper()}{{\\c{WH}}}" if j == k else x["w"].upper()) for j, x in enumerate(g))
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},Cap,,0,0,0,,{pop}{txt}")
ev.append(f"Dialogue: 2,{ts(0)},{ts(T_END + 0.1)},Mark,,0,0,0,,@whatifaholics")
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


# ---------- som ----------
SR = 48000


def wav(name, x):
    p = f"{BLD}/{name}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", p],
                   input=np.asarray(x, np.float32).tobytes(), check=True)
    return p


def lowpass_var(x, cut0, cut1, block=4096):
    """filtro passa-baixo que fecha ao longo do tempo (cada vez mais abafado), por blocos com sobreposição"""
    out = np.zeros(len(x) + block); win = np.hanning(block); hop = block // 2
    n = len(x)
    for i in range(0, n, hop):
        seg_ = x[i:i + block]
        if len(seg_) < block: seg_ = np.pad(seg_, (0, block - len(seg_)))
        k = i / n; fc = cut0 * (cut1 / cut0) ** k
        X = np.fft.rfft(seg_ * win); f = np.fft.rfftfreq(block, 1 / SR)
        X *= 1 / np.sqrt(1 + (f / fc) ** 4)
        out[i:i + block] += np.fft.irfft(X, block)
    return out[:n] / 1.0


def drone():
    """grave ambiente (só código): dois senos graves com batimento lento + ruído castanho, cada vez mais abafado.
    Começa e acaba no mesmo nível (loop). Silêncio súbito ao passar a borda."""
    n = int(T_END * SR); t = np.arange(n) / SR
    base = 0.5 * np.sin(2 * np.pi * 41.2 * t) + 0.35 * np.sin(2 * np.pi * 61.8 * t + 0.4 * np.sin(2 * np.pi * 0.11 * t)) \
        + 0.18 * np.sin(2 * np.pi * 82.4 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * t))
    rng = np.random.default_rng(6)
    br = np.cumsum(rng.standard_normal(n)); br -= np.convolve(br, np.ones(4801) / 4801, "same"); br /= np.abs(br).max()
    air = rng.standard_normal(n) * 0.25
    x = base * 0.55 + br * 0.5 + air
    x = lowpass_var(x, 2400, 260)
    x = x / np.abs(x).max() * 0.6
    # silêncio súbito na borda (o choque é o nada), volta abafado em "But wait"
    g = np.ones(n)
    e0, e1 = T["edge"] + 0.15, T["wait"] + 0.2
    i0, i1 = int(e0 * SR), int(e1 * SR)
    g[i0:i1] = 0.0
    fi = int(0.03 * SR); g[i0 - fi:i0] = np.linspace(1, 0, fi)
    fo = int(1.2 * SR); g[i1:i1 + fo] = np.linspace(0, 1, fo) ** 2
    return wav("drone", x * g)


def sfx_whoosh(d=1.0, lo=200, hi=1800, seed=1):
    n = int(d * SR); t = np.arange(n) / SR
    nz = np.random.default_rng(seed).standard_normal(n)
    X = np.fft.rfft(nz); f = np.fft.rfftfreq(n, 1 / SR); X[(f < lo) | (f > hi)] = 0; nz = np.fft.irfft(X, n)
    env = np.sin(np.pi * t / d) ** 2
    return nz * env / np.abs(nz * env).max() * 0.6


def mix(raw_video):
    def a(name): return f"{SFX}/{name}.wav"
    dr = drone()
    whoosh = wav("whoosh", sfx_whoosh(1.0, 150, 1400, 2))
    swish = wav("swish", sfx_whoosh(0.5, 500, 2500, 3))
    t_ = np.arange(int(0.2 * SR)) / SR
    pop = wav("pop_soft", 0.5 * np.sin(2 * np.pi * (260 + 500 * np.exp(-t_ * 35)) * t_) * np.exp(-t_ * 22))
    t_ = np.arange(int(0.06 * SR)) / SR
    tick = wav("tick", 0.45 * np.sin(2 * np.pi * 2200 * t_) * np.exp(-t_ * 90))
    t_ = np.arange(int(2.2 * SR)) / SR
    boom = wav("boom", 0.9 * np.sin(2 * np.pi * (38 + 50 * np.exp(-t_ * 5)) * t_) * np.exp(-t_ * 1.8))
    t_ = np.arange(int(1.6 * SR)) / SR
    shimmer = wav("shimmer", 0.25 * sum(np.sin(2 * np.pi * f * t_) for f in (880, 1320, 1760)) / 3 * np.sin(np.pi * t_ / 1.6) ** 2)
    E = [(a("scratch_head"), T["brand"], 0.7)]
    E += [(pop, T["four"], 0.4), (pop, T["sun"] - 0.05, 0.25)]
    E += [(swish, T["stars"] - 0.15, 0.3), (shimmer, T["ring"] - 0.2, 0.5)]
    E += [(whoosh, T["turn"], 0.45), (shimmer, T["lightaround"] + 1.4, 0.4)]
    E += [(swish, T["watch"] - 0.15, 0.3)]
    E += [(tick, T["watch"] + k, 0.35) for k in range(0, int(T["pass_"] - T["watch"]))]
    E += [(tick, T["earth"] + 0.05 * k + 0.002 * k * k, 0.18) for k in range(0, 40) if T["earth"] + 0.05 * k + 0.002 * k * k < T["pass_"] - 0.2]
    E += [(whoosh, T["pass_"] - 0.2, 0.4)]
    E += [(pop, SUB_T0 + 1.0, 0.25)]
    E += [(swish, T["inhere"] - 0.15, 0.3), (boom, T["noway"] - 0.02, 0.45), (shimmer, T["notlight"], 0.35)]
    ins, ch, lab = [], [], []
    for f, x, v in E:
        i = 3 + len(lab); ins += ["-i", f]; d = int(max(0, x) * 1000)
        ch.append(f"[{i}:a]adelay={d}|{d},volume={v}[e{len(lab)}]"); lab.append(f"[e{len(lab)}]")
    sfx = ";".join(ch) + ";" + "".join(lab) + f"amix=inputs={len(lab)}:normalize=0[sfx]"
    e0, e1 = T["edge"] + 0.15, T["wait"] + 0.2
    dri = 3 + len(lab)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw_video, "-i", NARR, "-stream_loop", "-1", "-i", MUSIC, *ins, "-i", dr,
                    "-filter_complex",
                    f"[0:v]subtitles={ASS},format=yuv420p[v];"
                    "[1:a]asplit=2[n1][nk];"
                    f"[2:a]atrim=0:{T_END:.3f},lowpass=f=1800,"
                    f"volume='if(between(t,{e0:.2f},{e1:.2f}),0,if(lt(t,{e1:.2f}+1.2)*gt(t,{e1:.2f}),0.14*(t-{e1:.2f})/1.2,0.14))':eval=frame[m];"
                    f"[{dri}:a]volume=0.32[d];[m][d]amix=inputs=2:normalize=0[bed];"
                    "[bed][nk]sidechaincompress=threshold=0.04:ratio=5:attack=30:release=400[md];"
                    f"{sfx};[n1][md][sfx]amix=inputs=3:duration=longest:normalize=0,apad,"
                    f"loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{T_END:.3f}[a]",
                    "-map", "[v]", "-map", "[a]", "-t", f"{T_END:.3f}", "-r", str(FPS),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M",
                    "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", OUT], check=True)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--frames":
        for tt in sys.argv[2].split(","):
            tv = float(tt) if tt != "last" else (N_FR - 1) / FPS
            frame_surface(tv).write_to_png(f"{BLD}/f_{tv:06.2f}.png")
        print("frames ok"); sys.exit()
    print("T_END", T_END, {k: round(v, 2) for k, v in T.items()})
    raw_v = f"{BLD}/raw.mp4"
    if "--mix-only" not in sys.argv:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p", raw_v], stdin=subprocess.PIPE)
        for i in range(N_FR):
            p.stdin.write(frame(i / FPS))
        p.stdin.close(); p.wait()
    mix(raw_v)
    print("OK", OUT, T_END)
