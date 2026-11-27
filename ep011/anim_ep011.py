#!/usr/bin/env python3
"""Whatifaholic EP011 — What If You Fell Into Quicksand?
Maquete 2.5D (5 ilustrações nano_banana_pro com a s1 do EP009 como referência, 3 camadas por imagem: build/layers11.py)
+ animação por código (pycairo). Base: EP010 (anim_ep010.py) / EP009. Sem frase de marca (pedido do dono para este vídeo).
Loop de frase: "Which means, the next time you…" → "…just stepped into quicksand." (último frame = frame 0).
Uso: python3 anim_ep011.py [--frames t1,t2,...|last] [--mix-only]   (sem argumentos: render completo + mistura)"""
import math, random, re, json, subprocess, sys, os
import cairo
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
BLD = f"{ROOT}/build"
NARR = f"{ROOT}/audio/narration_loop.wav"
MUSIC = f"{ROOT}/../music/track01_cosmic_ambient.mp3"
OUT = f"{ROOT}/whatifaholic_ep011_quicksand.mp4"
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", NARR]))
N_FR = int(round(DUR * FPS))
T_END = N_FR / FPS
random.seed(11)

# ---------- cores do tema (deserto, areia molhada, céu laranja; sem paleta fixa) ----------
INK = (1, 1, 1); DARK = (0.12, 0.06, 0.03); RED = (0.95, 0.18, 0.15); GREEN = (0.3, 0.9, 0.4)
SAND = (0.95, 0.8, 0.52); MUD = (0.45, 0.3, 0.17); MUD_L = (0.62, 0.45, 0.28); TEAL = (0.25, 0.88, 0.95)
GOLD = (1.0, 0.85, 0.3); WATER = (0.45, 0.78, 1.0); CARD = (0.16, 0.09, 0.05)

words = json.load(open(f"{BLD}/words.json"))
if words[-1]["e"] > T_END: words[-1]["e"] = T_END


def bare(w): return re.sub(r"[^\w']", "", w).lower()
def WS(i): return words[i]["s"]


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


def glow(c, x, y, r, col, a, r0=0):
    if a <= 0: return
    g = cairo.RadialGradient(x, y, r0, x, y, r)
    g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    c.set_source(g); c.arc(x, y, r, 0, 2 * math.pi); c.fill()


def vignette(c, a=0.45):
    g = cairo.RadialGradient(W / 2, H / 2, 500, W / 2, H / 2, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0.08, 0.03, 0, a)
    c.set_source(g); c.paint()


def bigx(c, cx, cy, r, q, a=1.0, w=34):
    """X vermelho desenhado (duas pinceladas com contorno escuro)"""
    if q <= 0 or a <= 0: return
    c.save(); c.set_line_cap(cairo.LINE_CAP_ROUND)
    k1 = min(1, q * 2); k2 = clamp((q - 0.5) * 2)
    for lw, col in ((w + 14, DARK), (w, RED)):
        c.set_source_rgba(*col, a); c.set_line_width(lw)
        c.move_to(cx - r, cy - r); c.line_to(cx - r + 2 * r * k1, cy - r + 2 * r * k1); c.stroke()
        if k2 > 0: c.move_to(cx + r, cy - r); c.line_to(cx + r - 2 * r * k2, cy - r + 2 * r * k2); c.stroke()
    c.restore()


def fail_x(c, t, t0, cx=540, cy=800, r=230, hold=1.0):
    if t < t0: return
    q = seg(t, t0, t0 + 0.22); a = 1 - seg(t, t0 + hold, t0 + hold + 0.3)
    bigx(c, cx, cy, r * (1 + 0.15 * (1 - q)), q, a)


def check(c, x, y, s, col, a, k=1.0, outline=True):
    if k <= 0: return
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    for lw, cc in (((s * 0.18 + 12, DARK), (s * 0.18, col)) if outline else ((s * 0.18, col),)):
        c.set_source_rgba(*cc, a); c.set_line_width(lw)
        c.move_to(x - s * 0.4, y); c.line_to(x - s * 0.1, y + s * 0.3 * min(1, k * 2))
        if k > 0.5: c.line_to(x - s * 0.1 + s * 0.55 * (k - 0.5) * 2, y + s * 0.3 - s * 0.65 * (k - 0.5) * 2)
        c.stroke()


def chip(c, t, t0, label, x, y, col, mark="check", size=50, t1=None):
    """cápsula com visto verde / X vermelho desenhado"""
    if t < t0 or (t1 is not None and t > t1 + 0.25): return
    k = popin(t, t0, 0.22); a = 1 - (seg(t, t1, t1 + 0.25) if t1 is not None else 0)
    c.save(); c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    e = c.text_extents(label); w = e.width + 150; h = size * 1.9
    c.translate(x, y); c.scale(k, k)
    c.set_source_rgba(0, 0, 0, 0.3 * a); rr(c, -w / 2 + 6, -h / 2 + 8, w, h, h / 2); c.fill()
    c.set_source_rgba(*CARD, 0.9 * a); rr(c, -w / 2, -h / 2, w, h, h / 2); c.fill()
    c.set_source_rgba(*col, a); c.set_line_width(5); rr(c, -w / 2, -h / 2, w, h, h / 2); c.stroke()
    c.move_to(-w / 2 + 110 - e.x_bearing, -e.height / 2 - e.y_bearing); c.text_path(label); c.set_source_rgba(*INK, a); c.fill()
    q = seg(t, t0 + 0.1, t0 + 0.35)
    if mark == "check": check(c, -w / 2 + 62, 0, size * 1.0, col, a, q, outline=False)
    elif mark == "x":
        c.set_source_rgba(*col, a); c.set_line_width(10); c.set_line_cap(cairo.LINE_CAP_ROUND); r = size * 0.32
        c.move_to(-w / 2 + 62 - r, -r); c.line_to(-w / 2 + 62 - r + 2 * r * min(1, q * 2), -r + 2 * r * min(1, q * 2)); c.stroke()
        if q > 0.5: c.move_to(-w / 2 + 62 + r, -r); c.line_to(-w / 2 + 62 + r - 2 * r * (q - 0.5) * 2, -r + 2 * r * (q - 0.5) * 2); c.stroke()
    c.restore()


def card(c, t, t0, lines, x, y, w, accent, t1=None, size=46, rot=-0.03):
    """cartão das piadas (relatable)"""
    if t < t0 or (t1 is not None and t > t1 + 0.3): return
    k = popin(t, t0, 0.25); a = 1 - (seg(t, t1, t1 + 0.3) if t1 is not None else 0)
    h = 34 + len(lines) * (size * 1.25)
    c.save(); c.translate(x, y + h / 2); c.rotate(rot); c.scale(k, k); c.translate(-w / 2, -h / 2)
    c.set_source_rgba(0, 0, 0, 0.3 * a); rr(c, 8, 10, w, h, 26); c.fill()
    c.set_source_rgba(*CARD, 0.93 * a); rr(c, 0, 0, w, h, 26); c.fill()
    c.set_source_rgba(*accent, a); c.set_line_width(5); rr(c, 0, 0, w, h, 26); c.stroke()
    for i, (s, col) in enumerate(lines):
        text(c, s, w / 2, 17 + size * 0.68 + i * size * 1.25, size if i == 0 else size * 0.86, col, a, outline=False)
    c.restore()


def arrow(c, x0, y0, x1, y1, col, a=1.0, w=12, head=30):
    if a <= 0: return
    ang = math.atan2(y1 - y0, x1 - x0)
    for lw, cc in ((w + 10, DARK), (w, col)):
        c.set_source_rgba(*cc, a); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(x0, y0); c.line_to(x1 - head * 0.5 * math.cos(ang), y1 - head * 0.5 * math.sin(ang)); c.stroke()
    for grow, cc in ((8, DARK), (0, col)):
        hh = head + grow
        c.set_source_rgba(*cc, a); c.move_to(x1 + grow * 0.5 * math.cos(ang), y1 + grow * 0.5 * math.sin(ang))
        c.line_to(x1 - hh * math.cos(ang - 0.5), y1 - hh * math.sin(ang - 0.5))
        c.line_to(x1 - hh * math.cos(ang + 0.5), y1 - hh * math.sin(ang + 0.5)); c.close_path(); c.fill()


# ---------- maquete 2.5D (base: EP010 v2) ----------
_KEEP = []


def _surf(rgb, alpha):
    h, w = alpha.shape
    buf = np.zeros((h, w, 4), np.uint8)
    pm = rgb * alpha[..., None]
    buf[..., 0] = pm[..., 2]; buf[..., 1] = pm[..., 1]; buf[..., 2] = pm[..., 0]; buf[..., 3] = alpha * 255
    s = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h)
    _KEEP.append(buf)
    return s


def _load_rgba(path, gain=1.0, shadow=False):
    im = np.array(Image.open(path).convert("RGBA"), np.float32)
    rgb, al = im[..., :3] * gain, im[..., 3] / 255
    s = _surf(np.clip(rgb, 0, 255), al)
    if not shadow or al.max() < 0.5: return s, None
    from scipy import ndimage as _nd
    sh = _nd.gaussian_filter(al[::4, ::4], 5.0)
    return s, (_surf(np.zeros(sh.shape + (3,), np.float32), np.clip(sh * 1.15, 0, 1)), 4)


LAY3 = {}


def layers3(name):
    if name not in LAY3:
        L0, _ = _load_rgba(f"{ROOT}/anim/{name}_L0.png", 0.9)
        L1, _ = _load_rgba(f"{ROOT}/anim/{name}_L1.png", 1.0)
        L2, S2 = _load_rgba(f"{ROOT}/anim/{name}_L2.png", 1.0, True)
        LAY3[name] = [(L0, None), (L1, None), (L2, S2)]
    return LAY3[name]


IW, IH = 1536, 2752
DEPTH = (0.2, 0.55, 1.0)       # fundo longe, chão, personagem
DRIFT_T = 0.0; DRIFT_MIX = 0.0
CLIP_Y = {"q1_afundar": 2122}   # linha da areia (px da imagem) por baixo da qual a personagem desaparece (afundar)


def drift(t):
    dx = 50 * math.sin(0.55 * t) + 14 * math.sin(1.30 * t + 1.0)
    dy = 26 * math.sin(0.42 * t + 0.7) + 8 * math.sin(1.1 * t)
    dz = 0.022 * math.sin(0.33 * t + 0.4)
    return dx, dy, dz


def view(c, name, zoom, fx, fy, px=0.0, py=0.0, push=0.0, rot=0.0, shake=0.0, t=0.0, sink=0.0, cdx=0.0, crot=0.0, piv=(0.5, 0.6), a=1.0):
    """desenha a maquete e devolve P(ix, iy) → coordenadas de ecrã (do plano da personagem)
    sink = px da imagem que a personagem desce (recortada pela linha da areia); cdx/crot = mexe só a personagem"""
    L = layers3(name)
    d1 = drift(DRIFT_T); d0 = drift(0.0)
    dx, dy, dz = [lerp(u, v, DRIFT_MIX) for u, v in zip(d1, d0)]
    ox, oy, oz = px * 1.9 + dx, py * 1.9 + dy, push * 1.6 + dz
    base = max(W / IW, H / IH) * zoom * 1.12
    vw, vh = W / base, H / base
    x0 = clamp(fx * IW - vw / 2, 0, IW - vw); y0 = clamp(fy * IH - vh / 2, 0, IH - vh)
    sx = shake * (math.sin(t * 19.0) + 0.6 * math.sin(t * 31.0)); sy = shake * math.cos(t * 23.0)
    c.save(); c.translate(W / 2 + sx, H / 2 + sy); c.rotate(rot); c.translate(-W / 2, -H / 2)

    def tf(k, extra=(0, 0)):
        sc = 1 + oz * DEPTH[k]
        c.translate(W / 2 + ox * DEPTH[k] + extra[0], H / 2 + oy * DEPTH[k] + extra[1]); c.scale(sc, sc); c.translate(-W / 2, -H / 2)
        c.scale(base, base); c.translate(-x0, -y0)

    def char_tf():
        c.translate(piv[0] * IW + cdx, piv[1] * IH + sink); c.rotate(crot); c.translate(-piv[0] * IW, -piv[1] * IH)

    for k, (s, sh) in enumerate(L):
        clip = k == 2 and name in CLIP_Y
        if sh is not None:
            ss, dn = sh
            c.save(); tf(k, (10 + 6 * k, 16 + 8 * k))
            if clip: c.rectangle(0, 0, IW, CLIP_Y[name]); c.clip()
            char_tf(); c.scale(dn, dn)
            c.set_source_surface(ss, 0, 0); c.get_source().set_filter(cairo.FILTER_BILINEAR); c.paint_with_alpha(0.3 * a); c.restore()
        c.save(); tf(k)
        if k == 2:
            if clip: c.rectangle(0, 0, IW, CLIP_Y[name]); c.clip()
            char_tf()
        c.set_source_surface(s, 0, 0); c.get_source().set_filter(cairo.FILTER_GOOD)
        c.paint_with_alpha(a); c.restore()
    c.restore()
    lx, ly, lz = ox, oy, oz

    def P(ix, iy):
        x, y = (ix * IW - x0) * base, (iy * IH - y0) * base
        x -= W / 2; y -= H / 2
        x, y = x * (1 + lz) + lx, y * (1 + lz) + ly
        cr, sr = math.cos(rot), math.sin(rot)
        return W / 2 + sx + x * cr - y * sr, H / 2 + sy + x * sr + y * cr
    P.base = base * (1 + lz)
    dust(c, ox, oy, a)
    return P


DUST = [(random.random(), random.random(), random.uniform(2, 7), random.random() * 6.28) for _ in range(60)]
BOK = [(random.random(), random.random(), random.uniform(40, 110)) for _ in range(8)]


def dust(c, ox, oy, a=1.0):
    """grãos de areia a flutuar no ar (primeiro plano, parallax maior) + bokeh quente"""
    for (bx, by, r, ph) in DUST:
        x = (bx * (W + 200) + ox * 1.4 + DRIFT_T * 22 * (1 - DRIFT_MIX)) % (W + 200) - 100
        y = (by * (H + 200) + oy * 1.4 + 6 * math.sin(DRIFT_T * 1.3 + ph)) % (H + 200) - 100
        c.set_source_rgba(1, 0.9, 0.7, 0.35 * a); c.arc(x, y, r * 0.6, 0, 6.283); c.fill()
    for (bx, by, r) in BOK:
        x = (bx * (W + 400) + ox * 1.7 + DRIFT_T * 9 * (1 - DRIFT_MIX)) % (W + 400) - 200
        y = (by * (H + 400) + oy * 1.7) % (H + 400) - 200
        g = cairo.RadialGradient(x, y, r * 0.2, x, y, r)
        g.add_color_stop_rgba(0, 1, 0.85, 0.55, 0.14 * a); g.add_color_stop_rgba(1, 1, 0.85, 0.55, 0)
        c.set_source(g); c.arc(x, y, r, 0, 6.283); c.fill()


def ripples(c, cx, cy, t, rx=180, ry=40, n=3, a=1.0, speed=0.8, col=(1, 0.95, 0.85)):
    for i in range(n):
        q = ((t * speed + i / n) % 1.0)
        c.save(); c.translate(cx, cy); c.scale(1, ry / rx)
        c.set_source_rgba(*col, 0.55 * (1 - q) * a); c.set_line_width(5 * rx / ry * 0.25)
        c.arc(0, 0, rx * (0.5 + 0.9 * q), 0, 6.283); c.restore(); c.stroke()


def bubbles(c, cx, cy, t, w=200, a=1.0, n=8, seed=3, rate=1.0):
    rnd = random.Random(seed)
    for i in range(n):
        x = cx + (rnd.random() - 0.5) * w; ph = rnd.random(); r = 6 + rnd.random() * 10
        q = (t * rate * (0.6 + rnd.random() * 0.6) + ph) % 1.0
        c.set_source_rgba(*MUD_L, a * (1 - q)); c.set_line_width(3)
        c.arc(x, cy - 4 * q, r * (0.4 + q), 0, 6.283); c.stroke()


# =====================================================================
# Tempos (palavras do guião, build/words.json)
# =====================================================================
T = dict(so1=WS(7), pull=WS(13), legs=WS(15), doesnt=WS(23), because=WS(25), sand=WS(31), liquid=WS(34), sink=WS(39), faster=WS(41),
         so2=WS(42), help=WS(46), friend=WS(47), pulls=WS(53), doesnt2=WS(55), grips=WS(61), pulling=WS(66), lifting=WS(75), car=WS(77),
         gives=WS(80), arm=WS(83), so3=WS(87), stop=WS(89), weird=WS(95), stopped=WS(97), waist=WS(102), because3=WS(103), twice=WS(107),
         heavy=WS(109), cant=WS(114), float=WS(120), it_=WS(122), so4=WS(123), lean=WS(125), pool=WS(132), spread=WS(134), wiggle=WS(139),
         slowly=WS(142), water=WS(144), little=WS(149), free=WS(155), slide=WS(158), the_=WS(164), lied=WS(166), swallow=WS(169),
         unless=WS(171), fight=WS(173), which=WS(175))

# afundar (q1): o mesmo valor no frame 0 e no último frame
SINK0 = 0.0


def sink_q1(t):
    if t < T["which"]:
        s = SINK0 + 14 * t                                   # devagar, sempre
        s += 70 * seg(t, T["legs"], T["doesnt"])             # a puxar: afunda mais
        s += 110 * seg(t, T["sink"], T["faster"] + 0.6)      # "you sink even faster"
        return s
    return SINK0


# ---------- 1. gancho: enterrado até aos joelhos, a afundar · "SINKING" desde o frame 0 ----------
def cam_hook(t):
    return dict(z=1.25 - 0.02 * t, fx=0.5, fy=0.5, px=0, py=0, push=0.012 * t)


def sinking_label(c, t, a=1.0, x=540, y=250):
    if a <= 0: return
    bob = 6 * math.sin(t * 5)
    text(c, "SINKING", x, y + bob, 150, RED, a, ow=0.16, ocol=(1, 1, 1))
    for sx in (x - 360, x + 360):
        yy = y - 40 + 22 * ((t * 1.6) % 1.0)
        arrow(c, sx, yy, sx, yy + 95, RED, a, w=13, head=36)


def sand_fx(c, P, t, sink, a=1.0, fast=0.0):
    sx, sy = P(0.5, CLIP_Y["q1_afundar"] / IH)
    ripples(c, sx, sy + 8, t, rx=230, ry=48, n=3, a=a * (0.7 + 0.6 * fast), speed=0.7 + 1.2 * fast)
    bubbles(c, sx, sy + 10, t, w=330, a=a, n=10, rate=1.0 + 2 * fast)


def s_hook(c, t, cm=None):
    cm = cm or cam_hook(t)
    sk = sink_q1(t)
    P = view(c, "q1_afundar", cm["z"], cm["fx"], cm["fy"], cm["px"], cm["py"], cm["push"], t=t, sink=sk)
    sand_fx(c, P, t, sk)
    vignette(c, 0.35)
    sinking_label(c, t)


# ---------- 2. "you pull your legs out as hard as you can" ----------
def s_pull(c, t):
    u = t - T["so1"]
    tug = max(0, math.sin((t - T["pull"]) * 9)) * 26 * (T["pull"] <= t)   # puxões
    P = view(c, "q1_afundar", 1.3 + 0.03 * u, 0.5, 0.58, t=t, sink=sink_q1(t) - tug, shake=3 * (t > T["pull"]), push=0.01 * u)
    sand_fx(c, P, t, 0)
    vignette(c, 0.35)
    if t > T["pull"]:
        lx, ly = P(0.42, 0.66); rx_, ry_ = P(0.58, 0.66)
        k = seg(t, T["pull"], T["pull"] + 0.25); bob = 14 * math.sin(t * 9)
        arrow(c, lx - 120, ly + 40 - bob, lx - 120, ly - 160 - bob, GOLD, k, w=14, head=40)
        arrow(c, rx_ + 120, ry_ + 40 - bob, rx_ + 120, ry_ - 160 - bob, GOLD, k, w=14, head=40)
        text(c, "PULL!", 540, 330, 140, GOLD, k, ow=0.15, scale=popin(t, T["pull"]))
    card(c, t, T["legs"] + 0.25, [("LEG DAY:", INK), ("SKIPPED", RED)], 790, 470, 400, RED, size=50, rot=0.05)


# ---------- 3. não funciona: a areia liquefaz (esquema dos grãos) e afundas mais depressa ----------
GRAINS = [(random.random(), random.random()) for _ in range(46)]


def grains_diagram(c, t, cx, cy, R, liq):
    """lupa: grãos de areia presos (sólido) → mexes → a água separa-os (líquido)"""
    c.save(); c.arc(cx, cy, R, 0, 6.283); c.clip()
    c.set_source_rgb(*lerp_col(MUD_L, (0.5, 0.62, 0.72), liq)); c.paint()
    for i, (gx, gy) in enumerate(GRAINS):
        a0 = gx * 6.283; r0 = math.sqrt(gy) * R * 0.95
        x = cx + r0 * math.cos(a0); y = cy + r0 * math.sin(a0)
        jig = liq * 26
        x += jig * math.sin(t * 7 + i); y += jig * math.cos(t * 6 + i * 1.7) + liq * 30 * math.sin(t * 2 + i)
        c.set_source_rgb(*SAND); c.arc(x, y, R * 0.12 * (1 - 0.25 * liq), 0, 6.283); c.fill()
        c.set_source_rgba(*DARK, 0.5); c.set_line_width(3); c.arc(x, y, R * 0.12 * (1 - 0.25 * liq), 0, 6.283); c.stroke()
    if liq > 0.05:
        for i in range(8):
            q = (t * 0.8 + i / 8) % 1.0
            c.set_source_rgba(*WATER, 0.7 * liq); c.arc(cx + (i - 4) * R * 0.22, cy + R - 2 * R * q, 9, 0, 6.283); c.fill()
    c.restore()
    c.set_source_rgba(*DARK, 1); c.set_line_width(22); c.arc(cx, cy, R, 0, 6.283); c.stroke()
    c.set_source_rgba(1, 1, 1, 1); c.set_line_width(10); c.arc(cx, cy, R, 0, 6.283); c.stroke()


def lerp_col(a, b, k): return tuple(lerp(x, y, k) for x, y in zip(a, b))


def s_liquid(c, t):
    u = t - T["doesnt"]
    fast = seg(t, T["sink"], T["faster"])
    P = view(c, "q1_afundar", 1.38 + 0.02 * u, 0.5, 0.6, t=t, sink=sink_q1(t), shake=2 + 6 * fast, push=0.012 * u)
    sand_fx(c, P, t, 0, fast=0.4 + fast)
    vignette(c, 0.4)
    fail_x(c, t, T["doesnt"] + 0.1, 540, 650, 210, hold=0.9)
    if t > T["sand"] - 0.1:
        k = popin(t, T["sand"] - 0.1, 0.3)
        liq = seg(t, T["liquid"] - 0.2, T["liquid"] + 0.6)
        c.save(); c.translate(540, 560); c.scale(k, k); c.translate(-540, -560)
        sx, sy = P(0.5, CLIP_Y["q1_afundar"] / IH)
        c.set_source_rgba(1, 1, 1, 0.8); c.set_line_width(6); c.set_dash([16, 12])
        c.move_to(sx + 60, sy - 10); c.line_to(540 + 150, 560 + 150); c.stroke(); c.set_dash([])
        grains_diagram(c, t, 540, 560, 210, liq)
        lab = "SOLID" if liq < 0.5 else "LIQUID"
        text(c, lab, 540, 840, 78, SAND if liq < 0.5 else WATER, 1, ow=0.16, scale=popin(t, T["liquid"] - 0.2 if liq >= 0.5 else T["sand"]))
        c.restore()
    if t > T["sink"]:
        text(c, "SINKING FASTER", 540, 300, 104, RED, 1, ow=0.16, ocol=(1, 1, 1), scale=popin(t, T["sink"]), rot=-0.03)


# ---------- 4. "So you yell for help." ----------
def s_help(c, t):
    u = t - T["so2"]
    P = view(c, "q1_afundar", 1.3 + 0.05 * u, 0.5, 0.45, t=t, sink=sink_q1(t), shake=4 * (t > T["help"] - 0.2), push=0.01 * u)
    sand_fx(c, P, t, 0)
    vignette(c, 0.35)
    if t > WS(44) - 0.05:
        k = popin(t, WS(44) - 0.05, 0.25); hx, hy = P(0.62, 0.27)
        c.save(); c.translate(hx + 170, hy - 170); c.scale(k, k); c.rotate(0.06)
        c.set_source_rgba(1, 1, 1, 0.97)
        pts = [(math.cos(a) * (230 + (36 if i % 2 else 0)), math.sin(a) * (120 + (24 if i % 2 else 0))) for i, a in enumerate(np.linspace(0, 6.283, 22, endpoint=False))]
        c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]; c.close_path(); c.fill_preserve()
        c.set_source_rgba(*DARK, 1); c.set_line_width(8); c.stroke()
        c.restore()
        text(c, "HELP!!", hx + 170, hy - 170, 108, RED, 1, outline=False, scale=k, rot=0.06)


# ---------- 5. o amigo puxa (q2) → não funciona → "= LIFTING A CAR" ----------
def s_friend(c, t):
    u = t - T["friend"]
    tug = (math.sin(u * 8) * 0.5 + 0.5) * 18
    P = view(c, "q2_amigo", 1.22 + 0.02 * u, 0.5, 0.5, t=t, cdx=tug, crot=-0.01 * math.sin(u * 8), piv=(0.5, 0.72), shake=2, push=0.01 * u)
    sx, sy = P(0.33, 0.73)
    ripples(c, sx, sy, t, rx=150, ry=34, n=3, a=0.8)
    vignette(c, 0.35)
    if t > T["pulls"]:
        k = seg(t, T["pulls"], T["pulls"] + 0.2); hx, hy = P(0.62, 0.47)
        for i in range(3):
            q = (t * 2 + i / 3) % 1
            arrow(c, hx + 40 + q * 30, hy - 10 + i * 40, hx + 170 + q * 30, hy - 30 + i * 40, INK, k * (1 - q), w=8, head=22)
    fail_x(c, t, T["doesnt2"] + 0.08, 540, 640, 200, hold=0.9)


def car_icon(c, x, y, s, a=1.0, col=(0.85, 0.2, 0.2)):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.set_source_rgba(*col, a)
    rr(c, -160, -40, 320, 80, 26); c.fill()
    c.move_to(-95, -40); c.line_to(-60, -100); c.line_to(70, -100); c.line_to(110, -40); c.close_path(); c.fill()
    c.set_source_rgba(0.75, 0.9, 1.0, a); c.move_to(-78, -46); c.line_to(-52, -88); c.line_to(0, -88); c.line_to(0, -46); c.close_path(); c.fill()
    c.move_to(12, -46); c.line_to(12, -88); c.line_to(62, -88); c.line_to(92, -46); c.close_path(); c.fill()
    for wx in (-90, 90):
        c.set_source_rgba(0.12, 0.12, 0.14, a); c.arc(wx, 40, 36, 0, 6.283); c.fill()
        c.set_source_rgba(0.75, 0.75, 0.8, a); c.arc(wx, 40, 15, 0, 6.283); c.fill()
    c.set_source_rgba(1, 0.95, 0.6, a); c.arc(150, -14, 10, 0, 6.283); c.fill()
    c.restore()


def s_car(c, t):
    u = t - T["grips"]
    strain = seg(t, T["pulling"], T["pulling"] + 0.4)
    P = view(c, "q2_amigo", 1.5 + 0.03 * u, 0.36, 0.62, t=t, cdx=8 * math.sin(u * 14) * strain, piv=(0.5, 0.72), shake=2 + 3 * strain, push=0.01 * u)
    sx, sy = P(0.33, 0.73)
    ripples(c, sx, sy, t, rx=150, ry=34, n=3, a=0.8)
    vignette(c, 0.4)
    if t > T["grips"]:   # a areia agarra: "mãos" de areia à volta das pernas
        k = seg(t, T["grips"], T["grips"] + 0.3)
        lx, ly = P(0.33, 0.715)
        for i, dx in enumerate((-70, 0, 70)):
            c.set_source_rgba(*MUD, k); c.set_line_width(22); c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.move_to(lx + dx, ly + 30); c.curve_to(lx + dx - 30, ly - 30 * k, lx + dx + 20, ly - 60 * k, lx + dx + 5, ly - 80 * k); c.stroke()
        text(c, "GRIP", lx, ly - 170, 84, SAND, k, ow=0.17, scale=popin(t, T["grips"]))
    if t > T["pulling"]:   # 1 pé = levantar um carro
        k = popin(t, T["pulling"], 0.25)
        c.save(); c.translate(540, 470); c.scale(k, k); c.translate(-540, -470)
        c.set_source_rgba(*CARD, 0.92); rr(c, 140, 250, 800, 440, 40); c.fill()
        c.set_source_rgba(*GOLD, 1); c.set_line_width(6); rr(c, 140, 250, 800, 440, 40); c.stroke()
        text(c, "1 FOOT", 300, 470, 66, INK, 1, outline=False)
        text(c, "=", 470, 470, 90, GOLD, 1, outline=False)
        lift = 70 * seg(t, T["lifting"], T["lifting"] + 0.5) + 6 * math.sin(t * 20) * (t > T["lifting"])
        car_icon(c, 700, 520 - lift, 0.95)
        if t > T["lifting"]:
            for sgn in (-1, 1):   # traços de esforço
                for i in range(3):
                    c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(6)
                    c.move_to(700 + sgn * (175 + i * 10), 460 - lift - i * 26); c.line_to(700 + sgn * (205 + i * 10), 450 - lift - i * 26); c.stroke()
        c.restore()
        if t > T["lifting"]:
            text(c, "= LIFTING A CAR", 540, 780, 84, GOLD, 1, ow=0.16, scale=popin(t, T["lifting"]))


# ---------- 6. o amigo desiste · o teu braço quase também (bateria) ----------
def battery(c, x, y, s, level, a=1.0, col=RED):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.set_source_rgba(*CARD, 0.92 * a); rr(c, -120, -55, 240, 110, 18); c.fill()
    c.set_source_rgba(1, 1, 1, a); c.set_line_width(8); rr(c, -120, -55, 240, 110, 18); c.stroke()
    rr(c, 120, -22, 18, 44, 6); c.fill()
    c.set_source_rgba(*col, a); rr(c, -104, -39, 208 * max(0.04, level), 78, 10); c.fill()
    c.restore()


def s_giveup(c, t):
    u = t - WS(78)
    slump = seg(t, T["gives"], T["gives"] + 0.5)
    P = view(c, "q2_amigo", 1.3 - 0.02 * u, 0.5, 0.5, t=t, cdx=-12 * slump, crot=0.025 * slump, piv=(0.5, 0.72), push=-0.008 * u)
    vignette(c, 0.4)
    if t > T["gives"]:   # bandeira branca do amigo
        k = popin(t, T["gives"], 0.25); fx, fy = P(0.72, 0.3)
        c.save(); c.translate(fx, fy - 60); c.scale(k, k)
        c.set_source_rgba(*DARK, 1); c.set_line_width(10); c.move_to(0, 160); c.line_to(0, -100); c.stroke()
        wv = 12 * math.sin(t * 8)
        c.set_source_rgba(1, 1, 1, 1); c.move_to(0, -100); c.curve_to(60, -120 + wv, 110, -80 - wv, 160, -100 + wv)
        c.line_to(160, -10 + wv); c.curve_to(110, 10 - wv, 60, -30 + wv, 0, -10); c.close_path(); c.fill_preserve()
        c.set_source_rgba(*DARK, 1); c.set_line_width(5); c.stroke(); c.restore()
        text(c, "FRIEND: GAVE UP", 540, 300, 84, INK, 1, ow=0.16, scale=popin(t, T["gives"]), rot=-0.03)
    if t > T["arm"]:   # piada relatable: a bateria do braço
        lvl = lerp(0.35, 0.03, seg(t, T["arm"] + 0.2, T["arm"] + 1.0))
        k = popin(t, T["arm"], 0.25)
        c.save(); c.translate(540, 1150); c.scale(k, k); c.translate(-540, -1150)
        battery(c, 470, 1180, 1.15, lvl, col=RED if lvl < 0.15 else GOLD)
        text(c, f"{max(1, int(round(lvl * 100)))}%", 720, 1180, 72, RED, 1, ow=0.16)
        text(c, "ARM BATTERY", 540, 1075, 58, INK, 1, ow=0.16)
        c.restore()


# ---------- 7. paras de mexer (q3): param à cintura ----------
def s_still(c, t):
    u = t - T["so3"]
    P = view(c, "q3_cintura", 1.18 + 0.025 * u, 0.5, 0.52, t=t, push=0.01 * u)
    vignette(c, 0.35)
    if t > T["stop"]:
        chip(c, t, T["stop"], "STOP MOVING", 540, 300, GREEN, "check", t1=T["weird"] - 0.1)
    if t > T["weird"]:
        k = popin(t, T["weird"], 0.3); qx, qy = P(0.73, 0.37)
        text(c, "?", qx, qy + 6 * math.sin(t * 4), 200, GOLD, 1, ow=0.14, scale=k, rot=0.12)
    if t > T["stopped"]:   # linha da cintura com "STOPPED"
        k = seg(t, T["stopped"], T["stopped"] + 0.35)
        lx, ly = P(0.2, 0.652); rx_, ry_ = P(0.8, 0.652)
        c.save(); c.set_source_rgba(*GREEN, k); c.set_line_width(8); c.set_dash([26, 16])
        c.move_to(lx, ly); c.line_to(lx + (rx_ - lx) * k, ry_); c.stroke(); c.restore()
        text(c, "STOPPED", 540, 300, 120, GREEN, 1, ow=0.15, scale=popin(t, T["stopped"]), rot=-0.03)
    if t > T["waist"]:
        chip(c, t, T["waist"], "AT YOUR WAIST", 540, 1300, GREEN, "check", size=46)


# ---------- 8. a areia pesa 2× o teu corpo: balança → flutuas ----------
def s_heavy(c, t):
    u = t - T["because3"]
    P = view(c, "q3_cintura", 1.3 + 0.02 * u, 0.5, 0.45, t=t, push=0.01 * u, sink=-10 * seg(t, T["float"], T["float"] + 0.6))
    c.set_source_rgba(0.1, 0.05, 0.02, 0.35 * seg(t, T["because3"], T["because3"] + 0.3) * (1 - seg(t, T["float"] - 0.3, T["float"]))); c.paint()
    vignette(c, 0.4)
    if T["because3"] + 0.1 < t < T["float"] + 0.1:   # balança
        k = popin(t, T["because3"] + 0.1, 0.3); a = 1 - seg(t, T["float"] - 0.2, T["float"] + 0.1)
        tilt = 0.28 * seg(t, T["twice"], T["heavy"] + 0.3) + 0.02 * math.sin(t * 3)
        cx, cy = 540, 400
        c.save(); c.translate(cx, cy); c.scale(k, k)
        c.set_source_rgba(*DARK, a); rr(c, -16, 0, 32, 300, 10); c.fill(); rr(c, -110, 290, 220, 34, 14); c.fill()
        c.set_source_rgba(*GOLD, a); c.arc(0, 0, 22, 0, 6.283); c.fill()
        c.rotate(-tilt)
        c.set_source_rgba(*GOLD, a); c.set_line_width(16); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(-330, 0); c.line_to(330, 0); c.stroke()
        for sgn in (-1, 1):
            px_, py_ = sgn * 330, 0
            c.save(); c.translate(px_, py_); c.rotate(tilt)
            c.set_source_rgba(1, 1, 1, a); c.set_line_width(4)
            c.move_to(0, 0); c.line_to(-100, 150); c.move_to(0, 0); c.line_to(100, 150); c.stroke()
            c.set_source_rgba(*GOLD, a); c.move_to(-130, 150); c.line_to(130, 150); c.line_to(100, 175); c.line_to(-100, 175); c.close_path(); c.fill()
            if sgn < 0:   # sand: 2 blocos
                for j in range(2):
                    c.set_source_rgba(*MUD_L, a); rr(c, -110 + j * 112, 40, 104, 108, 12); c.fill()
                    c.set_source_rgba(*DARK, a); c.set_line_width(4); rr(c, -110 + j * 112, 40, 104, 108, 12); c.stroke()
                text(c, "SAND", 0, 94, 40, INK, a)
            else:          # um só bloco (sem boneco por código: regra da personagem única)
                c.set_source_rgba(*(0.6, 0.45, 0.55), a); rr(c, -52, 40, 104, 108, 12); c.fill()
                c.set_source_rgba(*DARK, a); c.set_line_width(4); rr(c, -52, 40, 104, 108, 12); c.stroke()
                text(c, "YOU", 0, 94, 40, INK, a)
            c.restore()
        c.restore()
        if t > T["twice"]:
            text(c, "SAND 2× HEAVIER", 540, 230, 96, GOLD, a, ow=0.16, scale=popin(t, T["twice"]), rot=-0.03)
    if t > T["cant"] and t < T["float"]:
        text(c, "CAN'T SINK", 540, 1120, 92, INK, 1 - seg(t, T["float"] - 0.2, T["float"]), ow=0.17, scale=popin(t, T["cant"]))
    if t > T["float"] - 0.1:   # flutua: setas para cima
        k = seg(t, T["float"] - 0.1, T["float"] + 0.3)
        for i, dx in enumerate((-260, 0, 260)):
            yy = 1150 - 40 * ((t * 1.2 + i * 0.3) % 1.0)
            arrow(c, 540 + dx, yy + 120, 540 + dx, yy - 40, TEAL, k, w=14, head=40)
        text(c, "YOU FLOAT", 540, 330, 130, TEAL, k, ow=0.15, scale=popin(t, T["float"] - 0.1), rot=-0.03)


# ---------- 9. solução (q4): deitas-te de costas, braços abertos, pernas devagar ----------
def s_floatback(c, t):
    u = t - T["so4"]
    rock_ = 0.02 * math.sin(t * 1.6)
    wig = 10 * math.sin((t - T["wiggle"]) * 4.5) * seg(t, T["wiggle"], T["wiggle"] + 0.3)
    P = view(c, "q4_flutuar", 1.2 + 0.02 * u, 0.5, 0.52, t=t, crot=rock_, cdx=wig, piv=(0.5, 0.52), push=0.008 * u,
             sink=8 * math.sin(t * 1.6))
    lx, ly = P(0.2, 0.67)
    ripples(c, lx, ly, t, rx=110, ry=30, n=2, a=0.7 + 0.5 * (t > T["wiggle"]), speed=0.5 + 0.6 * (t > T["wiggle"]))
    vignette(c, 0.3)
    stamp_check(c, t, T["lean"], 450)
    chip(c, t, T["lean"], "LEAN BACK", 540, 1300, GREEN, "check", t1=T["spread"] - 0.1)
    chip(c, t, T["spread"], "SPREAD ARMS", 540, 1300, GREEN, "check", t1=T["wiggle"] - 0.1)
    chip(c, t, T["wiggle"], "WIGGLE SLOWLY", 540, 1300, GREEN, "check", t1=T["water"] - 0.1)
    card(c, t, T["pool"] - 0.1, [("SUNDAY", INK), ("MODE: ON", GOLD)], 800, 430, 380, GOLD, size=48, rot=0.05, t1=T["wiggle"] - 0.2)
    if t > T["water"] - 0.1:   # água a voltar para a areia, à volta das pernas
        k = seg(t, T["water"] - 0.1, T["water"] + 0.4)
        for i in range(10):
            q = (t * 0.9 + i / 10) % 1.0; ang = i * 0.63
            x = lx + math.cos(ang) * (220 - 170 * q); y = ly + math.sin(ang) * (90 - 70 * q)
            c.set_source_rgba(*WATER, 0.9 * k * (1 - q * 0.6)); c.arc(x, y, 12, 0, 6.283); c.fill()
        text(c, "WATER IN = SAND LOOSENS", 540, 1300, 62, WATER, k, ow=0.18, scale=popin(t, T["water"] - 0.1))


def stamp_check(c, t, t0, y):
    if t < t0: return
    k = popin(t, t0, 0.25)
    c.save(); c.translate(540, y); c.scale(k, k)
    c.set_source_rgba(0.1, 0.35, 0.12, 0.9); c.arc(0, 0, 80, 0, 6.283); c.fill()
    c.set_source_rgba(1, 1, 1, 1); c.set_line_width(8); c.arc(0, 0, 80, 0, 6.283); c.stroke()
    check(c, 0, 0, 100, INK, 1, seg(t, t0 + 0.1, t0 + 0.35), outline=False)
    c.restore()


# ---------- 10. pouco a pouco, as pernas soltam-se e deslizas para fora (q5) ----------
def s_slide(c, t):
    u = t - T["little"]
    P = view(c, "q5_sair", 1.15 + 0.06 * seg(t, T["slide"], T["slide"] + 1.4), 0.5 + 0.06 * seg(t, T["slide"], T["slide"] + 1.4), 0.55,
             t=t, push=0.012 * u, px=-30 * seg(t, T["slide"], T["slide"] + 1.4))
    vignette(c, 0.3)
    stamp_check(c, t, T["free"], 300)
    if t > T["free"]:
        text(c, "FREE!", 540, 450, 150, GREEN, 1, ow=0.15, scale=popin(t, T["free"]), rot=-0.04)
    if t < T["free"]:
        k = seg(t, T["little"], T["little"] + 0.6)
        prog = seg(t, T["little"], T["free"])
        c.set_source_rgba(*CARD, 0.88 * k); rr(c, 240, 1260, 600, 54, 27); c.fill()
        c.set_source_rgba(*GREEN, k); rr(c, 248, 1268, 584 * max(0.05, prog), 38, 19); c.fill()
        text(c, "LEGS FREE", 540, 1205, 54, INK, k, ow=0.18)


# ---------- 11. "The movies lied." ----------
def s_movies(c, t):
    u = t - T["the_"]
    c.set_source_rgb(0.08, 0.05, 0.04); c.paint()
    # ecrã de cinema com a cena do gancho (a preto e branco, grão) + carimbo
    c.save(); c.translate(540, 760); sc = 0.62 + 0.03 * u; c.scale(sc, sc); c.translate(-540, -960)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cc = cairo.Context(s)
    s_hook_raw(cc, 0.4 + u * 0.7)   # a cena do gancho (câmara e afundar do início)
    c.rectangle(0, 0, W, H); c.clip()
    c.set_source_surface(s, 0, 0); c.paint()
    c.set_source_rgba(0.5, 0.45, 0.4, 1); c.set_operator(cairo.OPERATOR_HSL_SATURATION); c.paint(); c.set_operator(cairo.OPERATOR_OVER)
    c.set_source_rgba(0, 0, 0, 0.25); c.paint()
    c.reset_clip(); c.restore()
    # película (perfurações) à volta
    x0, x1, y0, y1 = 540 - sc * 540 - 70, 540 + sc * 540 + 70, 760 - sc * 960 - 10, 760 + sc * 960 + 10
    c.set_source_rgba(0.02, 0.02, 0.02, 1)
    c.rectangle(x0, y0, 70, y1 - y0); c.fill(); c.rectangle(x1 - 70, y0, 70, y1 - y0); c.fill()
    off = (u * 220) % 90
    for yy in np.arange(y0 - 90 + off, y1, 90):
        for xx in (x0 + 18, x1 - 52):
            c.set_source_rgba(0.95, 0.9, 0.8, 1); rr(c, xx, yy, 34, 46, 8); c.fill()
    text(c, "THE END?", 540, 400, 70, INK, 0.9 * (1 - seg(t, T["lied"], T["lied"] + 0.2)), outline=False)
    if t > T["lied"]:
        u2 = t - T["lied"]; k = 1 + 0.8 * (1 - ease(u2 / 0.16)); a = clamp(u2 / 0.08)
        c.save(); c.translate(540, 760); c.rotate(-0.12); c.scale(k, k)
        c.set_source_rgba(*RED, a); c.set_line_width(14); rr(c, -440, -150, 880, 300, 30); c.stroke()
        c.restore()
        text(c, "THE MOVIES", 540, 700, 120, RED, a, ow=0.12, ocol=(1, 1, 1), scale=k, rot=-0.12)
        text(c, "LIED", 540, 840, 150, RED, a, ow=0.12, ocol=(1, 1, 1), scale=k, rot=-0.12)
    if t > T["unless"]:
        chip(c, t, T["fight"] - 0.1, "FIGHT IT = SINK", 540, 1300, RED, "x")


# ---------- 12. "Which means, the next time you…" → frame 0 ----------
def s_end(c, t):
    global DRIFT_MIX
    k = smooth((t - T["which"]) / (T_END - T["which"]))
    DRIFT_MIX = k
    cm0 = cam_hook(0.0)
    cm = dict(z=lerp(1.45, cm0["z"], k), fx=0.5, fy=lerp(0.56, 0.5, k), px=0, py=0, push=lerp(0.02, cm0["push"], k))
    sk = lerp(170, SINK0, k)
    P = view(c, "q1_afundar", cm["z"], cm["fx"], cm["fy"], cm["px"], cm["py"], cm["push"], t=t, sink=sk)
    sand_fx(c, P, t, sk)
    vignette(c, 0.35)
    sinking_label(c, t, a=seg(t, T_END - 0.55, T_END - 1 / FPS))


def s_hook_raw(c, t):
    global DRIFT_T
    keep = DRIFT_T; DRIFT_T = t
    s_hook(c, t); DRIFT_T = keep


SCENES = [(0.0, T["so1"], s_hook), (T["so1"], T["doesnt"], s_pull), (T["doesnt"], T["so2"], s_liquid), (T["so2"], T["friend"], s_help),
          (T["friend"], T["grips"], s_friend), (T["grips"], WS(78), s_car), (WS(78), T["so3"], s_giveup), (T["so3"], T["because3"], s_still),
          (T["because3"], T["so4"], s_heavy), (T["so4"], T["little"], s_floatback), (T["little"], T["the_"], s_slide),
          (T["the_"], T["which"], s_movies), (T["which"], 99, s_end)]
NO_PUNCH = {s_end}
SUB_T0 = T["it_"] + 0.25          # pop-up logo a seguir a "You float in it."
SUB_D = 2.5
SUB_Y = 210                       # no topo (fora das legendas e da cena)


def bell_icon(c, x, y, s, col, a, rot):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s); c.set_source_rgba(*col, a)
    c.move_to(-14, 8); c.curve_to(-14, -6, -12, -18, 0, -18); c.curve_to(12, -18, 14, -6, 14, 8); c.line_to(18, 12); c.line_to(-18, 12); c.close_path(); c.fill()
    c.arc(0, 16, 5, 0, 6.283); c.fill(); c.rectangle(-2, -23, 4, 6); c.fill(); c.restore()


def subscribe(c, t):
    """pop-up de subscrição (baseado em lib/subscribe_popup.py; cores do deserto)"""
    u = t - SUB_T0
    if u < 0 or u > SUB_D: return
    inn = seg(u, 0, 0.3); out = seg(u, SUB_D - 0.3, SUB_D); a = inn * (1 - out)
    done = u > 1.0
    w, h = 660, 104; x = (W - w) / 2; y = SUB_Y - 40 * (1 - inn) - 30 * out
    sc = 0.92 + 0.08 * inn - 0.05 * math.sin(math.pi * clamp((u - 0.85) / 0.25))
    c.save(); c.translate(W / 2, y + h / 2); c.scale(sc, sc); c.translate(-W / 2, -(y + h / 2))
    c.set_source_rgba(*CARD, 0.92 * a); rr(c, x, y, w, h, h / 2); c.fill()
    col = (0.7, 0.65, 0.6) if done else TEAL
    c.set_source_rgba(*col, 0.95 * a); c.set_line_width(4); rr(c, x, y, w, h, h / 2); c.stroke()
    wig = 0.35 * math.sin((u - 1.0) * 28) * math.exp(-(u - 1.0) * 5) if done else 0
    bell_icon(c, x + 64, y + h / 2 - 2, 1.25, INK if done else TEAL, a, wig)
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    if not done:
        c.set_font_size(40); c.set_source_rgba(*INK, a); c.move_to(x + 110, y + h / 2 + 14); c.show_text("SUBSCRIBE")
        c.set_font_size(30); c.set_source_rgba(*TEAL, a); c.move_to(x + 345, y + h / 2 + 11); c.show_text("for more what ifs")
    else:
        c.set_font_size(40); c.set_source_rgba(*INK, a); c.move_to(x + 110, y + h / 2 + 14); c.show_text("SUBSCRIBED")
        check(c, x + 410, y + h / 2 - 2, 40, TEAL, a, clamp((u - 1.0) / 0.25), outline=False)
    c.restore()
    if 0.5 < u < 1.5:
        fx = x + w - 120; fy = y + h / 2
        pa = seg(u, 0.5, 0.8) * (1 - seg(u, 1.2, 1.5)); tap = seg(u, 0.85, 1.0)
        c.set_source_rgba(1, 1, 1, 0.55 * pa * a); c.arc(fx, fy + 60 * (1 - seg(u, 0.5, 0.85)), 34 - 8 * tap, 0, 6.283); c.fill()
        if u > 0.95:
            q = (u - 0.95) / 0.5
            c.set_source_rgba(*TEAL, 0.6 * (1 - q) * a); c.set_line_width(4); c.arc(fx, fy, 30 + 90 * q, 0, 6.283); c.stroke()


def render_scene(fn, t):
    global DRIFT_T, DRIFT_MIX
    DRIFT_T, DRIFT_MIX = t, 0.0
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_GOOD)
    fn(c, t); return s


def frame_surface(t):
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); ctx = cairo.Context(out)
    for i, (a, b, fn) in enumerate(SCENES):
        if a <= t < b:
            cur = render_scene(fn, t)
            x = (t - a) / 0.25
            if i > 0 and x < 1 and fn not in NO_PUNCH:   # entrada com zoom em cada corte
                z = 1.08 - 0.08 * ease(x)
                ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2)
                ctx.set_source_surface(cur, 0, 0); ctx.paint(); ctx.restore()
                ctx.set_source_rgba(1, 1, 1, 0.15 * (1 - ease(x))); ctx.paint()
            else:
                ctx.set_source_surface(cur, 0, 0); ctx.paint()
            break
    subscribe(ctx, t)
    return out


def frame(t):
    s = frame_surface(t)
    return np.ndarray((H, W, 4), np.uint8, s.get_data())[:, :, [2, 1, 0]].tobytes()


# ---------- legendas (ASS, palavra a palavra) ----------
WEAK = {"a", "an", "the", "to", "of", "for", "on", "in", "it", "and", "but", "is", "your", "you", "or", "by", "that", "my", "me", "no", "one", "as"}
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


HL, WH = "&H00F0E040&", "&H00FFFFFF&"   # destaque turquesa (BGR): contrasta com a areia e o céu laranja
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
Style: Cap,Inter Display,80,&H00FFFFFF,&H00FFFFFF,&H00101010,&H78000000,-1,0,0,0,100,100,0,0,1,7,3,2,90,140,430,1
Style: Mark,Inter Display,38,&H8CFFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,3,0,7,60,60,110,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n")


# ---------- som (regra: ~10–15 efeitos, volumes baixos, sem dings; base EP010) ----------
SR = 48000


def wav(name, x):
    p = f"{BLD}/{name}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", p],
                   input=np.asarray(x, np.float32).tobytes(), check=True)
    return p


def sfx_whoosh(d=1.0, lo=200, hi=1800, seed=1):
    n = int(d * SR); t = np.arange(n) / SR
    nz = np.random.default_rng(seed).standard_normal(n)
    X = np.fft.rfft(nz); f = np.fft.rfftfreq(n, 1 / SR); X[(f < lo) | (f > hi)] = 0; nz = np.fft.irfft(X, n)
    env = np.sin(np.pi * t / d) ** 2
    return nz * env / np.abs(nz * env).max() * 0.6


def mix(raw_video):
    swish = wav("swish", sfx_whoosh(0.45, 500, 2600, 3))
    t_ = np.arange(int(0.2 * SR)) / SR
    pop = wav("pop_soft", 0.5 * np.sin(2 * np.pi * (260 + 500 * np.exp(-t_ * 35)) * t_) * np.exp(-t_ * 22))
    t_ = np.arange(int(1.4 * SR)) / SR
    shimmer = wav("shimmer", 0.25 * sum(np.sin(2 * np.pi * f * t_) for f in (660, 990, 1320, 1980)) / 4 * np.exp(-t_ * 2.2) * np.minimum(1, t_ / 0.01))
    t_ = np.arange(int(0.75 * SR)) / SR
    f_ = np.where(t_ < 0.3, 330 - 40 * t_ / 0.3, 247 - 60 * np.clip((t_ - 0.3) / 0.45, 0, 1))
    ph = 2 * np.pi * np.cumsum(f_) / SR
    env = np.where(t_ < 0.3, np.sin(np.pi * t_ / 0.3) ** 0.5, np.sin(np.pi * np.clip((t_ - 0.3) / 0.45, 0, 1)) ** 0.5) * (1 + 0.25 * np.sin(2 * np.pi * 6 * t_))
    # pedido do dono (27/11/2026): o "fail" antigo (trombone a descer) era horrível e chato → toque curto, grave e suave
    # escolha do dono (27/11/2026): "Games, Video, Negative Answer, Disconnected" (Epidemic Sound, via Higgsfield)
    fail = f"{ROOT}/../lib/sfx/x_resposta_errada.mp3"
    t_ = np.arange(int(0.5 * SR)) / SR
    thump = wav("thump", 0.8 * np.sin(2 * np.pi * (60 + 90 * np.exp(-t_ * 18)) * t_) * np.exp(-t_ * 7))
    # areia molhada: ruído grave filtrado com "glub" (um único som contínuo no gancho e outro no "sink even faster")
    n = int(2.6 * SR); t_ = np.arange(n) / SR
    nz = np.random.default_rng(5).standard_normal(n); X = np.fft.rfft(nz); f = np.fft.rfftfreq(n, 1 / SR); X[(f < 80) | (f > 600)] = 0
    nz = np.fft.irfft(X, n); glub = np.sin(2 * np.pi * (180 + 120 * np.sin(2 * np.pi * 3 * t_)) * t_) * (np.sin(2 * np.pi * 2.2 * t_) > 0.6)
    squelch = wav("squelch", (0.5 * nz / np.abs(nz).max() + 0.25 * glub) * np.sin(np.pi * t_ / 2.6) ** 2)
    # check (solução): dois tons suaves a subir
    t_ = np.arange(int(0.5 * SR)) / SR
    ok = wav("ok", 0.3 * sum(np.sin(2 * np.pi * f * t_) * np.exp(-t_ * 8) * (t_ >= d) for f, d in ((784, 0), (1175, 0.08))) * np.minimum(1, t_ / 0.004))
    E = [(squelch, 0.0, 0.18), (squelch, T["sink"] - 0.2, 0.22)]
    E += [(fail, T["doesnt"] + 0.1, 0.5), (fail, T["doesnt2"] + 0.08, 0.5)]
    E += [(pop, T["lifting"] - 0.05, 0.16), (thump, T["lifting"] + 0.1, 0.18), (pop, T["twice"] - 0.05, 0.16), (pop, SUB_T0 + 1.0, 0.14)]
    E += [(swish, T["so3"] - 0.12, 0.14), (swish, T["so4"] - 0.12, 0.14), (swish, T["the_"] - 0.12, 0.14)]
    E += [(ok, T["lean"], 0.18), (ok, T["free"], 0.2)]
    E += [(thump, T["lied"] - 0.02, 0.3), (shimmer, T["free"] + 0.05, 0.16)]   # carimbo "THE MOVIES LIED" = impacto principal
    ins, ch, lab = [], [], []
    for f_, x, v in E:
        i = 3 + len(lab); ins += ["-i", f_]; d = int(max(0, x) * 1000)
        ch.append(f"[{i}:a]adelay={d}|{d},volume={v}[e{len(lab)}]"); lab.append(f"[e{len(lab)}]")
    sfx = ";".join(ch) + ";" + "".join(lab) + f"amix=inputs={len(lab)}:normalize=0[sfx]"
    if raw_video is None:   # --audio-only: mantém a imagem do vídeo já feito e refaz só a mistura
        src = OUT.replace(".mp4", "_prev.mp4"); os.replace(OUT, src)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", NARR, "-stream_loop", "-1", "-i", MUSIC, *ins,
                        "-filter_complex",
                        "[1:a]asplit=2[n1][nk];"
                        f"[2:a]atrim=0:{T_END:.3f},volume=0.12[m];"
                        "[m][nk]sidechaincompress=threshold=0.04:ratio=5:attack=30:release=400[md];"
                        f"{sfx};[n1][md][sfx]amix=inputs=3:duration=longest:normalize=0,apad,"
                        f"loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{T_END:.3f}[a]",
                        "-map", "0:v", "-map", "[a]", "-t", f"{T_END:.3f}", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", OUT], check=True)
        os.remove(src); return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw_video, "-i", NARR, "-stream_loop", "-1", "-i", MUSIC, *ins,
                    "-filter_complex",
                    f"[0:v]subtitles={ASS},format=yuv420p[v];"
                    "[1:a]asplit=2[n1][nk];"
                    f"[2:a]atrim=0:{T_END:.3f},volume=0.12[m];"
                    "[m][nk]sidechaincompress=threshold=0.04:ratio=5:attack=30:release=400[md];"
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
    if "--audio-only" in sys.argv:
        mix(None); print("OK (só áudio)", OUT); sys.exit()
    raw_v = f"{BLD}/raw.mp4"
    if "--mix-only" not in sys.argv:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p", raw_v], stdin=subprocess.PIPE)
        for i in range(N_FR):
            p.stdin.write(frame(i / FPS))
        p.stdin.close(); p.wait()
    mix(raw_v)
    print("OK", OUT, T_END)
