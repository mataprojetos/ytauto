#!/usr/bin/env python3
"""Whatifaholic EP010 — What If YOU Had to Stop an Asteroid?
Ilustração plana (6 imagens nano_banana_pro com a s1 do EP009 como referência, parallax 2.5D por profundidade) + animação por código (pycairo).
Base: EP009. Loop de frase: "…heading for Earth…" → "An asteroid is heading for Earth." (último frame = frame 0).
Uso: python3 anim_ep010.py [--frames t1,t2,...|last] [--mix-only]   (sem argumentos: render completo + mistura)"""
import math, random, re, json, subprocess, sys, os
import cairo
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{ROOT}/../lib")
from brand_scratch import draw_scratch  # noqa: E402

W, H, FPS = 1080, 1920, 30
BLD = f"{ROOT}/build"
NARR = f"{ROOT}/audio/narration.wav"
MUSIC = f"{ROOT}/../music/track01_cosmic_ambient.mp3"
SFX = f"{ROOT}/../lib/sfx"
OUT = f"{ROOT}/whatifaholic_ep010_asteroid.mp4"
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", NARR]))
N_FR = int(round(DUR * FPS))
T_END = N_FR / FPS
random.seed(9)

# ---------- cores do tema (céu, neve, pôr do sol; sem paleta fixa) ----------
INK = (1, 1, 1); DARK = (0.03, 0.05, 0.12); GOLD = (1.0, 0.82, 0.25); ORANGE = (1.0, 0.55, 0.15); RED = (1.0, 0.27, 0.25)
SKY = (0.45, 0.8, 1.0); ICE = (0.75, 0.93, 1.0); GREY = (0.62, 0.64, 0.7); LIME = (0.55, 1.0, 0.45); NAVY = (0.04, 0.07, 0.2)

words = json.load(open(f"{BLD}/words.json"))
if words[-1]["e"] > T_END: words[-1]["e"] = T_END


def bare(w): return re.sub(r"[^\w']", "", w).lower()


def at(tok, n=1, key="s"):
    k = 0
    for w in words:
        if bare(w["w"]) == tok:
            k += 1
            if k == n: return w[key]
    raise KeyError(tok)



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


def sparkle(c, x, y, r, col, a):
    if a <= 0: return
    c.set_source_rgba(*col, a)
    c.move_to(x, y - r); c.curve_to(x, y, x, y, x + r, y); c.curve_to(x, y, x, y, x, y + r)
    c.curve_to(x, y, x, y, x - r, y); c.curve_to(x, y, x, y, x, y - r); c.fill()


# partículas de primeiro plano (parallax): três camadas a velocidades diferentes
PART = [(random.random(), random.random(), random.choice((0.4, 0.7, 1.0)), random.random() * 6.28) for _ in range(46)]


def particles(c, t, col, a=1.0, vx=-18, vy=-10, size=1.0):
    for (px, py, d, ph) in PART:
        x = (px * (W + 200) + vx * d * 3 * t) % (W + 200) - 100
        y = (py * (H + 200) + vy * d * 3 * t) % (H + 200) - 100
        tw = 0.55 + 0.45 * math.sin(t * 3 + ph)
        sparkle(c, x, y, (5 + 9 * d) * size, col, a * tw * (0.35 + 0.5 * d))


def vignette(c, a=0.45):
    g = cairo.RadialGradient(W / 2, H / 2, 500, W / 2, H / 2, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, a)
    c.set_source(g); c.paint()

# ---------- globo (código) ----------
def space_bg(c, t, top=(0.03, 0.02, 0.09), bot=(0.0, 0.0, 0.02), stars=1.0):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bot); c.set_source(g); c.paint()
    rnd = random.Random(3)
    for _ in range(140):
        x, y, r = rnd.random() * W, rnd.random() * H, rnd.random() * 2.2 + 0.6
        tw = 0.5 + 0.5 * math.sin(t * (1 + rnd.random() * 2) + rnd.random() * 6)
        c.set_source_rgba(1, 1, 1, (0.3 + 0.6 * tw) * stars); c.arc(x - t * 6 * r, y, r, 0, 2 * math.pi); c.fill()


# ---------- cenas ----------
def proj_pt(cx, cy, R, rot, lon, lat, tilt=0.41):
    ct, st = math.cos(tilt), math.sin(tilt)
    lo = math.radians(lon) + rot; la = math.radians(lat)
    x = math.cos(la) * math.sin(lo); y = -math.sin(la); z = math.cos(la) * math.cos(lo)
    return cx + R * x, cy + R * (y * ct - z * st * 0.35), z


def pin(c, x, y, k, col=RED):
    if k <= 0: return
    c.save(); c.translate(x, y); c.scale(k, k)
    c.set_source_rgba(0, 0, 0, 0.35); c.arc(0, 4, 14, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(*col, 1); c.arc(0, -46, 26, math.pi * 0.85, math.pi * 2.15); c.line_to(0, 0); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 1); c.arc(0, -46, 10, 0, 2 * math.pi); c.fill()
    c.restore()


def dashed(c, x0, y0, x1, y1, col, a, w=4, dash=18, off=0):
    c.save(); c.set_source_rgba(*col, a); c.set_line_width(w); c.set_dash([dash, dash * 0.7], off)
    c.move_to(x0, y0); c.line_to(x1, y1); c.stroke(); c.restore()



_KEEP = []
NL = 4


def _pool(a):
    h, w = a.shape[:2]
    a = a[:h - h % 2, :w - w % 2]
    return 0.25 * (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2])


def _fill(img, w):
    """preenche os píxeis com peso 0 a partir dos vizinhos (pirâmide pull-push), a 1/4 da resolução"""
    small = np.array(Image.fromarray(img.astype(np.uint8)).resize((img.shape[1] // 4, img.shape[0] // 4), Image.BILINEAR), np.float32)
    ws = np.array(Image.fromarray((w * 255).astype(np.uint8)).resize((img.shape[1] // 4, img.shape[0] // 4), Image.BILINEAR), np.float32) / 255
    A, Wt = [small * ws[..., None]], [ws]
    while min(A[-1].shape[:2]) > 4:
        A.append(_pool(A[-1])); Wt.append(_pool(Wt[-1]))
    col = A[-1] / np.maximum(Wt[-1], 1e-4)[..., None]
    for a, wt in zip(reversed(A[:-1]), reversed(Wt[:-1])):
        up = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((a.shape[1], a.shape[0]), Image.BILINEAR), np.float32)
        own = a / np.maximum(wt, 1e-4)[..., None]
        k = np.clip(wt * 4, 0, 1)[..., None]
        col = own * k + up * (1 - k)
    return np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((img.shape[1], img.shape[0]), Image.BILINEAR), np.float32)


def _surf(rgb, alpha):
    h, w = alpha.shape
    buf = np.zeros((h, w, 4), np.uint8)
    pm = rgb * alpha[..., None]
    buf[..., 0] = pm[..., 2]; buf[..., 1] = pm[..., 1]; buf[..., 2] = pm[..., 0]; buf[..., 3] = alpha * 255
    s = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h)
    _KEEP.append(buf)
    return s


def load_layers(name):
    im = np.array(Image.open(f"{ROOT}/anim/{name}.png").convert("RGB"), np.float32)
    d = np.array(Image.open(f"{ROOT}/anim/{name}_depth.png").convert("L"), np.float32) / 255
    ths = [0.0] + list(np.quantile(d, [0.5, 0.75, 0.9]))
    out = []
    for k in range(NL):
        alpha = np.ones_like(d) if k == 0 else np.clip((d - ths[k]) / 0.025 + 0.5, 0, 1)
        if k < NL - 1:
            keep = (d < ths[k + 1] + 0.035).astype(np.float32)   # píxeis originais por baixo da borda suave da camada seguinte
            rgb = im * keep[..., None] + _fill(im, keep) * (1 - keep[..., None])
        else:
            rgb = im
        out.append(_surf(rgb, alpha))
    return out

LAY = {}


def layers(name):
    if name not in LAY: LAY[name] = load_layers(name)
    return LAY[name]


# ---------- v2 (pedido do dono, 25/11/2026: "não tem profundidade nenhuma"): maquete 2.5D a sério ----------
# Cada ilustração é separada em 3 camadas recortadas (build/layers.py): fundo desfocado, objetos, personagem.
# A câmara anda sempre (deriva contínua + movimentos de cada cena); cada camada desloca-se e aproxima-se
# segundo a sua distância; cada camada projeta sombra suave na de trás; brilhos desfocados em primeiro plano.
DEPTH = {   # fator de parallax por camada (fundo, objetos, personagem); personagem em cima de um objeto = valores próximos
    "a1_panico": (0.18, 0.55, 1.0), "a2_genio": (0.18, 0.5, 1.0), "a3_foguetes": (0.18, 0.82, 1.0),
    "a4_pintar": (0.18, 0.82, 1.0), "a5_impacto": (0.18, 0.5, 1.0), "a6_alivio": (0.18, 0.85, 1.0)}
DRIFT_T = 0.0; DRIFT_MIX = 0.0; LAST = (0.0, 0.0, 0.0)
LAY3 = {}


def _load_rgba(path, gain=1.0, shadow=False):
    im = np.array(Image.open(path).convert("RGBA"), np.float32)
    rgb, al = im[..., :3] * gain, im[..., 3] / 255
    s = _surf(np.clip(rgb, 0, 255), al)
    if not shadow: return s, None
    from scipy import ndimage as _nd
    sh = _nd.gaussian_filter(al[::4, ::4], 5.0)
    return s, (_surf(np.zeros(sh.shape + (3,), np.float32), np.clip(sh * 1.15, 0, 1)), 4)


def layers3(name):
    if name not in LAY3:
        L0, _ = _load_rgba(f"{ROOT}/anim/{name}_L0.png", 0.80)
        L1, S1 = _load_rgba(f"{ROOT}/anim/{name}_L1.png", 0.97, True)
        L2, S2 = _load_rgba(f"{ROOT}/anim/{name}_L2.png", 1.0, True)
        LAY3[name] = [(L0, None), (L1, S1), (L2, S2)]
    return LAY3[name]


def drift(t):
    dx = 60 * math.sin(0.55 * t) + 18 * math.sin(1.30 * t + 1.0)
    dy = 32 * math.sin(0.42 * t + 0.7) + 9 * math.sin(1.1 * t)
    dz = 0.025 * math.sin(0.33 * t + 0.4)
    return dx, dy, dz


def draw_par(c, name, zoom, fx, fy, px=0.0, py=0.0, push=0.0, a=1.0):
    """maquete 2.5D: px/py = deslocação da câmara (px de ecrã, amplificada), push = dolly (aproxima mais as camadas da frente)"""
    L = layers3(name); f = DEPTH[name]
    d1 = drift(DRIFT_T); d0 = drift(0.0)
    dx, dy, dz = [lerp(u, v, DRIFT_MIX) for u, v in zip(d1, d0)]
    ox, oy, oz = px * 1.9 + dx, py * 1.9 + dy, push * 1.6 + dz
    iw, ih = L[0][0].get_width(), L[0][0].get_height()
    base = max(W / iw, H / ih) * zoom * 1.12            # margem para o parallax não mostrar bordas
    vw, vh = W / base, H / base
    x0 = clamp(fx * iw - vw / 2, 0, iw - vw); y0 = clamp(fy * ih - vh / 2, 0, ih - vh)
    def tf(k, extra=(0, 0)):
        sc = 1 + oz * f[k]
        c.translate(W / 2 + ox * f[k] + extra[0], H / 2 + oy * f[k] + extra[1]); c.scale(sc, sc); c.translate(-W / 2, -H / 2)
        c.scale(base, base); c.translate(-x0, -y0)
    for k, (s, sh) in enumerate(L):
        if sh is not None:   # sombra suave na camada de trás (luz de cima à esquerda)
            ss, dn = sh
            c.save(); tf(k, (16 + 10 * k, 26 + 12 * k)); c.scale(dn, dn)
            c.set_source_surface(ss, 0, 0); c.get_source().set_filter(cairo.FILTER_BILINEAR); c.paint_with_alpha(0.5 * a); c.restore()
        c.save(); tf(k)
        c.set_source_surface(s, 0, 0); c.get_source().set_filter(cairo.FILTER_GOOD)
        c.paint_with_alpha(a); c.restore()
    global LAST
    LAST = (ox * f[1], oy * f[1], oz * f[1])
    bokeh(c, ox, oy, a)
    return base, x0, y0


BOK = [(random.random(), random.random(), random.uniform(40, 120), random.choice(((1, 0.85, 0.6), (1, 1, 1), (0.7, 0.8, 1)))) for _ in range(9)]


def bokeh(c, ox, oy, a=1.0):
    """partículas grandes e desfocadas MUITO perto da câmara (mexem-se mais do que a personagem)"""
    for (bx, by, r, col) in BOK:
        x = (bx * (W + 400) + ox * 1.7 + DRIFT_T * 9 * (1 - DRIFT_MIX)) % (W + 400) - 200
        y = (by * (H + 400) + oy * 1.7) % (H + 400) - 200
        g = cairo.RadialGradient(x, y, r * 0.2, x, y, r)
        g.add_color_stop_rgba(0, *col, 0.16 * a); g.add_color_stop_rgba(0.7, *col, 0.08 * a); g.add_color_stop_rgba(1, *col, 0)
        c.set_source(g); c.arc(x, y, r, 0, 6.283); c.fill()



# ---------- cartões (piadas relatable) ----------
def card(c, t, t0, lines, x, y, w, accent, bg=(0.07, 0.06, 0.12), t1=None, size=44, rot=-0.03):
    if t < t0 or (t1 is not None and t > t1 + 0.3): return
    k = popin(t, t0, 0.25); out = seg(t, t1, t1 + 0.3) if t1 is not None else 0
    a = 1 - out
    h = 30 + len(lines) * (size * 1.25)
    c.save(); c.translate(x + w / 2, y + h / 2); c.rotate(rot); c.scale(k, k); c.translate(-w / 2, -h / 2)
    c.set_source_rgba(0, 0, 0, 0.3 * a); rr(c, 8, 10, w, h, 26); c.fill()
    c.set_source_rgba(*bg, 0.92 * a); rr(c, 0, 0, w, h, 26); c.fill()
    c.set_source_rgba(*accent, a); c.set_line_width(5); rr(c, 0, 0, w, h, 26); c.stroke()
    for i, (s, col) in enumerate(lines):
        text(c, s, w / 2, 15 + size * 0.68 + i * size * 1.25, size if i == 0 else size * 0.86, col, a, outline=False)
    c.restore()





def img2scr(base, x0, y0, x, y): return (x - x0) * base, (y - y0) * base


def chip(c, t, t0, label, x, y, col, mark="check", w=400, size=46, bg=(0.04, 0.07, 0.16)):
    """etiqueta em cápsula com visto (verde) ou X (vermelho) desenhados por código"""
    if t < t0: return
    k = popin(t, t0, 0.22)
    c.save(); c.translate(x, y); c.scale(k, k)
    c.set_source_rgba(*bg, 0.9); rr(c, -w / 2, -48, w, 96, 48); c.fill()
    c.set_source_rgba(*col, 1); c.set_line_width(5); rr(c, -w / 2, -48, w, 96, 48); c.stroke()
    c.restore()
    text(c, label, x + 32 * k, y, size, INK, 1, outline=False, scale=k)
    q = seg(t, t0 + 0.12, t0 + 0.35)
    mx = x - w / 2 * k + 52 * k
    if mark == "check": check(c, mx, y, 50 * k, col, 1, q)
    elif mark == "x": xmark(c, mx, y, 22 * k, col, q)


def xmark(c, cx, cy, r, col, q, w=12):
    if q <= 0: return
    c.set_source_rgba(*col, 1); c.set_line_width(w); c.set_line_cap(cairo.LINE_CAP_ROUND)
    k1 = min(1, q * 2)
    c.move_to(cx - r, cy - r); c.line_to(cx - r + 2 * r * k1, cy - r + 2 * r * k1); c.stroke()
    if q > 0.5:
        k2 = (q - 0.5) * 2
        c.move_to(cx + r, cy - r); c.line_to(cx + r - 2 * r * k2, cy - r + 2 * r * k2); c.stroke()


def wind_lines(c, t, a=1.0, speed=1.0, n=26, col=(1, 1, 1), seed=4, up=True):
    rnd = random.Random(seed)
    for i in range(n):
        x = rnd.random() * W; L = 120 + rnd.random() * 260; v = (900 + rnd.random() * 900) * speed
        ph = rnd.random() * (H + L)
        y = (ph - t * v) % (H + L) - L if up else (ph + t * v) % (H + L) - L
        g = cairo.LinearGradient(x, y, x, y + L)
        g.add_color_stop_rgba(0, *col, 0); g.add_color_stop_rgba(0.5, *col, 0.45 * a); g.add_color_stop_rgba(1, *col, 0)
        c.set_source(g); c.set_line_width(2 + rnd.random() * 3); c.move_to(x, y); c.line_to(x, y + L); c.stroke()


def snowfall(c, t, a=1.0, n=70, seed=7):
    rnd = random.Random(seed)
    for i in range(n):
        x0 = rnd.random() * W; y0 = rnd.random() * H; r = 2 + rnd.random() * 6; v = 40 + r * 18
        x = (x0 + 30 * math.sin(t * 0.8 + i)) % W; y = (y0 + v * t) % (H + 20) - 10
        c.set_source_rgba(1, 1, 1, a * (0.45 + 0.08 * r)); c.arc(x, y, r, 0, 2 * math.pi); c.fill()


# =====================================================================
# EP010: o mesmo rapaz de capuz (ref. ep009/anim/s1_queda_aviao.png) em 6 ilustrações; tudo o resto por código.
# =====================================================================
IW, IH = 1536, 2752
def WS(i): return words[i]["s"]
G = [WS(15), WS(49), WS(88), WS(126)]          # "And you, being a genius…"
A = [WS(20), WS(54), WS(93), WS(131)]          # decide / land / paint / park
FAIL = [WS(29), WS(66), WS(122), WS(146)]      # doesn't work / doesn't work either / don't have / same problem
T = dict(thousand=WS(41), still=WS(47), youve=WS(38), rockets=WS(64), asteroid=WS(71), spinning=WS(73), washing=WS(76),
         rockets2=WS(79), every=WS(82), it_=WS(85), sunlight=WS(98), works=WS(104), but=WS(105), fifty=WS(118),
         have=WS(123), spaceship=WS(133), gravity=WS(140), pulls=WS(142), tiny=WS(152), decades=WS(153), then=WS(155),
         harder=WS(162), earlier=WS(165), so=WS(166), crash=WS(168), years=WS(174), because=WS(178), nudge=WS(181),
         thousands=WS(187), reaches=WS(194), real=WS(196), y2022=WS(200), nasa=WS(201), dart=WS(209), changed=WS(211),
         orbit=WS(214), brand=WS(215) - 0.06, which=WS(222))
PLANS = ["A", "B", "C", "D"]
ROCK = (0.74, 0.46, 0.25); ROCK_D = (0.45, 0.25, 0.13); FIRE = (1.0, 0.62, 0.2); GREEN = (0.35, 0.95, 0.45)
HOOD = (0.82, 0.62, 0.74); SKIN = (0.98, 0.8, 0.64); HAIR = (0.45, 0.27, 0.14)


def to_scr(base, x0, y0, fx, fy): return (fx * IW - x0) * base, (fy * IH - y0) * base


def view(c, name, z, fx, fy, t, px=0.0, py=0.0, push=0.0, rot=0.0, shake=0.0, a=1.0):
    sx = shake * (math.sin(t * 19.0) + 0.6 * math.sin(t * 31.0)); sy = shake * math.cos(t * 23.0)
    c.save(); c.translate(W / 2 + sx, H / 2 + sy); c.rotate(rot); c.translate(-W / 2, -H / 2)
    base, x0, y0 = draw_par(c, name, z, fx, fy, px=px, py=py, push=push, a=a)
    c.restore()
    lx, ly, lz = LAST
    def P(ix, iy):
        x, y = to_scr(base, x0, y0, ix, iy); x -= W / 2; y -= H / 2
        x, y = x * (1 + lz) + lx, y * (1 + lz) + ly
        cr, sr = math.cos(rot), math.sin(rot)
        return W / 2 + sx + x * cr - y * sr, H / 2 + sy + x * sr + y * cr
    return P


def dim(c, a, col=(0.02, 0.02, 0.08)):
    c.set_source_rgba(*col, a); c.paint()


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


def fail_x(c, t, t0, cx=540, cy=800, r=230, hold=1.1):
    if t < t0: return
    q = seg(t, t0, t0 + 0.22); a = 1 - seg(t, t0 + hold, t0 + hold + 0.3)
    s = 1 + 0.15 * (1 - q)
    bigx(c, cx, cy, r * s, q, a)


def stamp(c, t, t0, label, x, y, col, size=120, rot=-0.07, sub=None, mark=None):
    """carimbo 'PLAN X' a cair com força (escala 1,7 → 1)"""
    if t < t0: return
    u = t - t0; k = 1 + 0.7 * (1 - ease(u / 0.16)); a = clamp(u / 0.08)
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(k, k)
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    e = c.text_extents(label); w = e.width + size * 0.7 + (size * 1.05 if mark else 0); h = size * 1.35
    c.set_source_rgba(0, 0, 0, 0.35 * a); rr(c, -w / 2 + 8, -h / 2 + 10, w, h, 22); c.fill()
    c.set_source_rgba(0.04, 0.04, 0.12, 0.88 * a); rr(c, -w / 2, -h / 2, w, h, 22); c.fill()
    c.set_source_rgba(*col, a); c.set_line_width(9); rr(c, -w / 2, -h / 2, w, h, 22); c.stroke()
    tx = -w / 2 + size * 0.35 + (size * 1.05 if mark else 0)
    c.move_to(tx - e.x_bearing, -e.height / 2 - e.y_bearing); c.text_path(label); c.set_source_rgba(*col, a); c.fill()
    if mark == "check": check(c, -w / 2 + size * 0.75, 0, size * 0.9, GREEN, a, seg(u, 0.12, 0.35))
    c.restore()
    if sub: text(c, sub, x, y + size * 0.95, size * 0.42, INK, a, ow=0.16, rot=rot)


def plan_chip(c, t, k, failed=None):
    """etiqueta pequena no topo durante cada plano: 'PLAN B · ROCKETS' (X quando falha)"""
    lab = ["PLAN A · NUKE", "PLAN B · ROCKETS", "PLAN C · PAINT IT", "PLAN D · GRAVITY"][k]
    c.save(); c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(46)
    e = c.text_extents(lab); w = e.width + 120; x = (W - w) / 2; y = 205
    c.set_source_rgba(0.04, 0.04, 0.12, 0.85); rr(c, x, y, w, 84, 42); c.fill()
    c.set_source_rgba(*GOLD, 1); c.set_line_width(4); rr(c, x, y, w, 84, 42); c.stroke()
    c.move_to(x + 92 - e.x_bearing, y + 42 - e.height / 2 - e.y_bearing); c.text_path(lab); c.set_source_rgba(*INK, 1); c.fill()
    c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(4); rr(c, x + 24, y + 20, 44, 44, 9); c.stroke()
    if failed is not None and t >= failed: xmark(c, x + 46, y + 42, 15, RED, seg(t, failed, failed + 0.2), w=9)
    c.restore()


def rock(c, x, y, r, rot, seed, a=1.0):
    rnd = random.Random(seed); n = 9
    pts = [(math.cos(rot + i * 6.283 / n) * r * (0.75 + 0.3 * rnd.random()), math.sin(rot + i * 6.283 / n) * r * (0.75 + 0.3 * rnd.random())) for i in range(n)]
    c.save(); c.translate(x, y)
    c.set_source_rgba(0, 0, 0, 0.3 * a); c.move_to(pts[0][0] + r * 0.12, pts[0][1] + r * 0.15)
    for px_, py_ in pts[1:]: c.line_to(px_ + r * 0.12, py_ + r * 0.15)
    c.close_path(); c.fill()
    c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(*p)
    c.close_path(); c.set_source_rgba(*ROCK, a); c.fill_preserve()
    c.set_source_rgba(*ROCK_D, a); c.set_line_width(max(1.5, r * 0.08)); c.stroke()
    c.set_source_rgba(*ROCK_D, 0.8 * a)
    for j in range(2):
        cx_, cy_ = (rnd.random() - 0.5) * r, (rnd.random() - 0.5) * r
        c.arc(cx_, cy_, r * (0.12 + 0.1 * rnd.random()), 0, 6.283); c.fill()
    c.restore()


def bulb(c, x, y, t, t0, s=1.0):
    """faísca de ideia junto ao dedo (gráfico por código)"""
    if t < t0: return
    u = t - t0; k = popin(t, t0, 0.25) * s
    glow(c, x, y, 120 * k, GOLD, 0.45 * (0.7 + 0.3 * math.sin(u * 12)))
    for i in range(8):
        ang = i * 0.785 + u * 0.8
        r0, r1 = 50 * k, (85 + 12 * math.sin(u * 14 + i)) * k
        c.set_source_rgba(*GOLD, 0.95); c.set_line_width(7 * k); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(x + math.cos(ang) * r0, y + math.sin(ang) * r0); c.line_to(x + math.cos(ang) * r1, y + math.sin(ang) * r1); c.stroke()
    sparkle(c, x, y, 34 * k, (1, 1, 0.9), 1)


def arrow(c, x0, y0, x1, y1, col, a=1.0, w=10, head=26):
    if a <= 0: return
    ang = math.atan2(y1 - y0, x1 - x0)
    for lw, cc in ((w + 8, DARK), (w, col)):
        c.set_source_rgba(*cc, a); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(x0, y0); c.line_to(x1 - math.cos(ang) * head * 0.6, y1 - math.sin(ang) * head * 0.6); c.stroke()
    c.save(); c.translate(x1, y1); c.rotate(ang)
    c.move_to(4, 0); c.line_to(-head, -head * 0.62); c.line_to(-head, head * 0.62); c.close_path()
    c.set_source_rgba(*DARK, a); c.set_line_width(8); c.stroke_preserve(); c.set_source_rgba(*col, a); c.fill()
    c.restore()


def embers(c, t, x, y, a=1.0, n=26, seed=5):
    rnd = random.Random(seed)
    for i in range(n):
        ph = rnd.random(); ang = -0.6 + rnd.random() * 2.6; v = 0.35 + rnd.random() * 0.5
        L = (t * v + ph) % 1
        d = 160 + L * 520
        sparkle(c, x + math.cos(ang) * d, y + math.sin(ang) * d * 0.9, (6 + 10 * rnd.random()) * (1 - L), FIRE, a * (1 - L))


# ---------- gancho: o asteroide vem aí (a1), "STOP IT." desde o frame 0 ----------
def hook_cam(t):
    p = smooth(t / 3.8)
    return dict(z=1.10 + 0.10 * p, fx=0.5, fy=0.41 - 0.03 * p, px=-16 * p, py=30 * p, push=0.07 * p, rot=0.01 * math.sin(t * 1.7), shake=5)


def stop_it(c, t, a=1.0):
    k = 1 + 0.03 * math.sin(t * 6)
    text(c, "STOP IT.", 540, 1255, 170, INK, a, ow=0.16, scale=k, rot=-0.04)


def s_hook(c, t, cam=None):
    cm = cam or hook_cam(t)
    P = view(c, "a1_panico", cm["z"], cm["fx"], cm["fy"], t, cm["px"], cm["py"], cm["push"], cm["rot"], cm["shake"])
    ax, ay = P(0.48, 0.26)
    glow(c, ax, ay, 520, FIRE, 0.18 + 0.06 * math.sin(t * 9))
    embers(c, t, ax, ay, 0.8)
    vignette(c, 0.4)
    stop_it(c, t)


# ---------- "And you, being a genius…": a MESMA pose (a2), a mesma faísca, PLAN A/B/C/D ----------
def make_genius(k):
    def s_genius(c, t):
        u = t - G[k]
        P = view(c, "a2_genio", 1.30 + 0.05 * u, 0.5, 0.36, t, px=-10 * u, py=0, push=0.05 * u)
        dim(c, 0.12)
        fx, fy = P(0.43, 0.335)
        bulb(c, fx - 40, fy - 120, t, G[k] + 0.05)
        stamp(c, t, G[k] + 0.12, f"PLAN {PLANS[k]}", 540, 330, GOLD, 150, rot=-0.07)
        vignette(c, 0.35)
    s_genius.__name__ = f"s_genius{k}"
    return s_genius


# ---------- plano A: bomba nuclear → mil pedaços ----------
FRAGS = [(random.uniform(0, 6.283), random.random(), random.uniform(0.6, 1.4), random.randint(0, 999)) for _ in range(90)]


def s_nuke(c, t):
    u = t - A[0]; TE = FAIL[0] - 0.05
    P = view(c, "a2_genio", 1.02, 0.5, 0.40, t, px=8 * u, py=10 * u, push=0.02 * u, shake=8 * clamp(1 - (t - TE) / 1.2) if t > TE else 0)
    ax, ay = P(0.27, 0.25)
    if t < TE:   # míssil
        q = smooth(clamp(u / (TE - A[0])))
        x0, y0 = W + 80, 1500; mx, my = lerp(x0, ax, q), lerp(y0, ay, q) - 260 * math.sin(math.pi * q)
        ang = math.atan2(ay - y0, ax - x0) - 0.9 * math.cos(math.pi * q)
        for j in range(14):
            d = j * 22; sparkle(c, mx - math.cos(ang) * d, my - math.sin(ang) * d, 22 - j, FIRE, 0.8 - j * 0.05)
        c.save(); c.translate(mx, my); c.rotate(ang)
        c.set_source_rgba(0.95, 0.95, 0.97, 1); rr(c, -60, -14, 100, 28, 14); c.fill()
        c.set_source_rgba(*RED, 1); c.move_to(40, -14); c.line_to(70, 0); c.line_to(40, 14); c.close_path(); c.fill()
        c.move_to(-60, -14); c.line_to(-80, -30); c.line_to(-40, -14); c.fill(); c.move_to(-60, 14); c.line_to(-80, 30); c.line_to(-40, 14); c.fill()
        c.restore()
        text(c, "NUKE", mx, my - 60, 44, INK, 1)
    else:
        v = t - TE
        R = 80 + 420 * ease(v / 0.6)
        glow(c, ax, ay, R * 1.5, (1, 0.95, 0.8), 0.9 * clamp(1 - v / 1.4))
        glow(c, ax, ay, R, FIRE, 0.95 * clamp(1 - v / 2.2))
        glow(c, ax, ay, R * 0.8, (0.55, 0.5, 0.5), 0.6 * clamp((v - 0.4) / 0.6) * clamp(1 - (v - 1.5) / 1.5))
        for (ang, ph, sp, sd) in FRAGS[:60]:
            d = (70 + 520 * ease(v / 1.8) * sp) * (0.4 + ph)
            rock(c, ax + math.cos(ang) * d, ay + math.sin(ang) * d, 8 + 16 * ph, v * sp + ang, sd, clamp(v / 0.3))
        if v < 0.2: dim(c, 0.6 * (1 - v / 0.2), (1, 0.98, 0.9))
    plan_chip(c, t, 0, FAIL[0])
    fail_x(c, t, FAIL[0], 540, 1000, 200)
    vignette(c, 0.35)


def s_frag(c, t):
    u = t - T["youve"]
    P = view(c, "a1_panico", 1.18 + 0.04 * u, 0.5, 0.40, t, px=-6 * u, py=8 * u, push=0.03 * u, shake=7)
    ax, ay = P(0.48, 0.26)
    glow(c, ax, ay, 560, (0.5, 0.45, 0.45), 0.55)
    glow(c, ax, ay, 420, FIRE, 0.25)
    for (ang, ph, sp, sd) in FRAGS:
        L = (u * 0.42 * sp + ph) % 1
        if u < 0.4: L = L * (0.4 + 1.5 * u)
        d = 60 + (L ** 2) * 1100; r = 8 + (L ** 2) * 110
        rock(c, ax + math.cos(ang) * d, ay + math.sin(ang) * d * 1.05, r, ang + u * sp * 2, sd, clamp(L * 6))
    # contador de pedaços e "STILL COMING"
    if t >= T["thousand"]:
        n = int(1 + 999 * ease((t - T["thousand"]) / 0.6))
        text(c, f"{n:,} ROCKS", 540, 1150, 110, INK, 1, ow=0.16, scale=popin(t, T["thousand"]), rot=-0.03)
    if t >= T["still"]:
        text(c, "STILL COMING", 540, 1280, 92, RED, 1, ow=0.17, scale=popin(t, T["still"]), rot=-0.03)
    plan_chip(c, t, 0, FAIL[0])
    vignette(c, 0.45)


# ---------- plano B: foguetes num asteroide que gira ----------
ROCKETS = [(0.21, 0.42), (0.86, 0.40), (0.97, 0.53), (0.22, 0.80), (0.83, 0.82)]
AC3 = (0.5, 0.66)


def s_rockets(c, t):
    u = t - A[1]
    sp = max(0, t - T["asteroid"])
    rot = 0.25 * sp * sp
    P = view(c, "a3_foguetes", 1.06 + 0.03 * u, 0.5, 0.50, t, px=6 * u, py=-8 * u, push=0.04 * u, rot=rot, shake=3)
    cx, cy = P(*AC3)
    if t >= T["rockets"] - 0.2:
        a = seg(t, T["rockets"] - 0.2, T["rockets"] + 0.2)
        for i, (rx, ry) in enumerate(ROCKETS):
            x, y = P(rx, ry)
            glow(c, x + (x - cx) * 0.25, y + (y - cy) * 0.25, 110, FIRE, a * (0.35 + 0.2 * math.sin(t * 25 + i)))
            arrow(c, x, y, lerp(x, cx, 0.45), lerp(y, cy, 0.45), GOLD, a * 0.95)
        text(c, "PUSH!", 540, 1190, 100, GOLD, a, ow=0.16, scale=popin(t, T["rockets"]), rot=-0.03)
    plan_chip(c, t, 1, FAIL[1])
    fail_x(c, t, FAIL[1], 540, 900, 220)
    vignette(c, 0.35)


_RAW = {}


def raw_surf(name):
    if name not in _RAW:
        im = np.array(Image.open(f"{ROOT}/anim/{name}.png").convert("RGB"), np.float32)
        _RAW[name] = _surf(im, np.ones(im.shape[:2], np.float32))
    return _RAW[name]


_b3 = np.array(Image.open(f"{ROOT}/anim/a3_foguetes.png").convert("RGB"), np.float32)
BG3 = tuple((np.concatenate([_b3[:40].reshape(-1, 3), _b3[-40:].reshape(-1, 3), _b3[:, :40].reshape(-1, 3), _b3[:, -40:].reshape(-1, 3)]).mean(0) / 255).tolist())
del _b3


def s_wash(c, t):
    """'spinning like a washing machine': o asteroide (com o rapaz e os foguetes) a girar dentro da porta de uma máquina"""
    u = t - T["spinning"]
    sp0 = T["spinning"] - T["asteroid"]
    ang = 0.25 * (sp0 + u) ** 2 * 1.0 + 2.2 * u * u
    zin = ease(u / 0.5)
    # máquina de lavar (papel recortado claro)
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.93, 0.94, 0.96); g.add_color_stop_rgb(1, 0.80, 0.82, 0.87)
    c.set_source(g); c.paint()
    c.set_source_rgba(0.70, 0.73, 0.79, 1); rr(c, 60, 150, 960, 230, 30); c.fill()
    c.set_source_rgba(0.12, 0.16, 0.22, 1); rr(c, 470, 205, 400, 120, 18); c.fill()
    rpm = int(400 + 1200 * clamp(u / 3))
    text(c, f"SPIN {rpm}", 670, 265, 56, (0.45, 1.0, 0.6), 1, outline=False)
    for i, kx in enumerate((150, 290)):
        c.set_source_rgba(0.95, 0.96, 0.98, 1); c.arc(kx + 20, 265, 50, 0, 6.283); c.fill()
        c.save(); c.translate(kx + 20, 265); c.rotate(u * (2 + i) + i)
        c.set_source_rgba(0.4, 0.43, 0.5, 1); c.set_line_width(10); c.move_to(0, 0); c.line_to(0, -38); c.stroke(); c.restore()
    CX, CY, R = 540, 930, 370 * (0.85 + 0.15 * zin)
    c.set_source_rgba(0, 0, 0, 0.18); c.arc(CX + 10, CY + 16, R + 70, 0, 6.283); c.fill()
    c.set_source_rgba(0.62, 0.65, 0.71, 1); c.arc(CX, CY, R + 70, 0, 6.283); c.fill()
    c.set_source_rgba(0.96, 0.97, 0.99, 1); c.arc(CX, CY, R + 40, 0, 6.283); c.fill()
    # interior: ilustração a3 a girar (inclui o rapaz)
    c.save(); c.arc(CX, CY, R, 0, 6.283); c.clip()
    c.set_source_rgb(*BG3); c.paint()
    L0 = raw_surf("a3_foguetes"); sc = 0.34
    c.translate(CX, CY); c.rotate(ang); c.scale(sc, sc); c.translate(-AC3[0] * IW, -AC3[1] * IH)
    c.set_source_surface(L0, 0, 0); c.get_source().set_filter(cairo.FILTER_GOOD); c.paint()
    # setas a empurrar em todas as direções (rodam com o asteroide)
    if t >= T["rockets2"] - 0.1:
        a = seg(t, T["rockets2"] - 0.1, T["rockets2"] + 0.2)
        for (rx, ry) in ROCKETS:
            x, y = rx * IW, ry * IH; cx_, cy_ = AC3[0] * IW, AC3[1] * IH
            arrow(c, x, y, lerp(x, cx_, 0.5), lerp(y, cy_, 0.5), GOLD, a, w=34, head=80)
    c.restore()
    # vidro: reflexo
    c.save(); c.arc(CX, CY, R, 0, 6.283); c.clip()
    gl = cairo.LinearGradient(CX - R, CY - R, CX + R, CY + R)
    gl.add_color_stop_rgba(0, 1, 1, 1, 0.28); gl.add_color_stop_rgba(0.35, 1, 1, 1, 0.0); gl.add_color_stop_rgba(1, 1, 1, 1, 0.08)
    c.set_source(gl); c.paint(); c.restore()
    c.set_source_rgba(0.5, 0.53, 0.6, 1); c.set_line_width(10); c.arc(CX, CY, R, 0, 6.283); c.stroke()
    if t >= T["washing"]:
        text(c, "WASHING MACHINE MODE", 540, 455, 58, (0.15, 0.2, 0.32), 1, ow=0.0, outline=False, scale=popin(t, T["washing"]))


def make_react(label, xt):
    """cara de desilusão (a1, grande plano da cara) + X + rótulo"""
    def s_react(c, t):
        u = t - xt
        P = view(c, "a1_panico", 1.85 + 0.06 * u, 0.5, 0.44, t, px=0, py=0, push=0.02 * u, shake=6 * clamp(1 - u / 0.6) + 2)
        c.set_source_rgba(0.6, 0.0, 0.05, 0.12); c.paint()
        vignette(c, 0.55)
        bigx(c, 540, 330, 120, 1.0, 1.0, w=26)
        text(c, label, 540, 1250, 108, RED, 1, ow=0.17, scale=popin(t, xt + 0.02), rot=-0.03)
    return s_react


# ---------- plano C: pintar de branco (efeito Yarkovsky) ----------
def s_paint(c, t):
    u = t - A[2]
    P = view(c, "a4_pintar", 1.05 + 0.025 * u, 0.48, 0.45, t, px=-5 * u, py=6 * u, push=0.03 * u)
    sx, sy = P(0.22, 0.10); wx, wy = P(0.13, 0.55); ex, ey = P(0.66, 0.66)
    if t >= T["sunlight"] - 0.1:
        a = seg(t, T["sunlight"] - 0.1, T["sunlight"] + 0.3)
        glow(c, sx, sy, 300, GOLD, 0.35 * a)
        for i in range(5):
            tx, ty = wx + (i - 2) * 40, wy + (i - 2) * 70
            dashed(c, sx + 50, sy + 60, tx, ty, GOLD, 0.85 * a, w=7, dash=26, off=-t * 160)
        k = seg(t, T["sunlight"] + 0.4, T["sunlight"] + 0.9)
        if k > 0:
            arrow(c, ex + 10, ey, ex + 10 + 70 * k, ey + 30 * k, GOLD, k, w=8, head=24)
            text(c, "push", ex + 60, ey - 50, 44, GOLD, k)
    if t >= T["works"]:
        a = 1 - seg(t, T["fifty"] - 0.3, T["fifty"])
        c.save(); c.set_source_rgba(0.04, 0.04, 0.12, 0.88 * a); rr(c, 150, 1110, 780, 210, 30); c.fill()
        c.set_source_rgba(*GREEN, a); c.set_line_width(5); rr(c, 150, 1110, 780, 210, 30); c.stroke(); c.restore()
        check(c, 215, 1170, 60, GREEN, a, seg(t, T["works"], T["works"] + 0.25))
        text(c, "IT WORKS…", 270, 1170, 60, INK, a, align="l", outline=False)
        if t >= T["but"]:
            pr = 0.0001 * (t - T["but"])
            c.set_source_rgba(1, 1, 1, 0.2 * a); rr(c, 190, 1235, 700, 44, 22); c.fill()
            c.set_source_rgba(*GOLD, a); rr(c, 190, 1235, 14 + 6 * math.sin(t * 3) ** 2, 44, 22); c.fill()
            text(c, f"OFF COURSE: {0.0001 + pr:.4f}%", 540, 1257, 34, INK, a, outline=False)
    if t >= T["fifty"]:
        k = popin(t, T["fifty"], 0.25)
        yr = 2026 + int(50 * ease((t - T["fifty"]) / 1.0))
        c.save(); c.translate(540, 1170); c.scale(k, k)
        c.set_source_rgba(0.96, 0.95, 0.92, 1); rr(c, -330, -120, 660, 240, 26); c.fill()
        c.set_source_rgba(*RED, 1); rr(c, -330, -120, 660, 64, 26); c.fill(); c.rectangle(-330, -80, 660, 24); c.fill()
        c.restore()
        text(c, "50 YEARS", 540, 1150 + 0, 116 * k, DARK, 1, outline=False)
        text(c, f"{yr}", 540, 1245, 48 * k, (0.35, 0.35, 0.4), 1, outline=False)
        # relógio a girar
        cx, cy = 840, 1040
        c.set_source_rgba(1, 1, 1, k); c.arc(cx, cy, 70 * k, 0, 6.283); c.fill()
        c.set_source_rgba(*DARK, k); c.set_line_width(8); c.arc(cx, cy, 70 * k, 0, 6.283); c.stroke()
        for hand, L, sp in ((0, 52, 9), (1, 36, 0.8)):
            an = (t - T["fifty"]) * sp
            c.move_to(cx, cy); c.line_to(cx + math.sin(an) * L * k, cy - math.cos(an) * L * k); c.stroke()
    plan_chip(c, t, 2, FAIL[2])
    fail_x(c, t, FAIL[2], 540, 820, 200)
    vignette(c, 0.35)


# ---------- plano D: trator gravitacional (esquema por código por cima de a2) ----------
def ship(c, x, y, s, a=1.0, rot=0.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.set_source_rgba(0.3, 0.45, 0.85, a); c.rectangle(-120, -18, 80, 36); c.rectangle(40, -18, 80, 36); c.fill()
    c.set_source_rgba(0.85, 0.9, 1, a); c.set_line_width(2)
    for xx in (-100, -80, -60, 60, 80, 100): c.move_to(xx, -18); c.line_to(xx, 18); c.stroke()
    c.set_source_rgba(0.6, 0.62, 0.68, a); c.rectangle(-40, -4, 80, 8); c.fill()
    c.set_source_rgba(0.94, 0.94, 0.96, a); rr(c, -34, -30, 68, 60, 10); c.fill()
    c.set_source_rgba(0.3, 0.45, 0.85, a); c.arc(0, 0, 12, 0, 6.283); c.fill()
    c.restore()


def s_tractor(c, t):
    u = t - A[3]
    view(c, "a2_genio", 1.0, 0.5, 0.44, t, px=-6 * u, py=4 * u, push=0.02 * u)
    dim(c, 0.35)
    k = popin(t, A[3] - 0.05, 0.3)
    c.save(); c.translate(540, 520); c.scale(k, k); c.translate(-540, -520)
    c.set_source_rgba(0.05, 0.12, 0.30, 0.94); rr(c, 70, 310, 940, 420, 30); c.fill()
    c.set_source_rgba(0.5, 0.7, 1, 0.18); c.set_line_width(2)
    for gx in range(70, 1010, 47): c.move_to(gx, 310); c.line_to(gx, 730); c.stroke()
    for gy in range(310, 730, 47): c.move_to(70, gy); c.line_to(1010, gy); c.stroke()
    c.set_source_rgba(*SKY, 1); c.set_line_width(5); rr(c, 70, 310, 940, 420, 30); c.stroke()
    pull = 4 * seg(t, T["pulls"], T["pulls"] + 2.0)
    rock(c, 330 + pull, 540, 120, 0.3, 77)
    if t >= T["spaceship"] - 0.1:
        q = ease((t - T["spaceship"] + 0.1) / 0.6)
        ship(c, lerp(1150, 740, q), 520 + 6 * math.sin(t * 2), 1.0)
    if t >= T["gravity"]:
        a = seg(t, T["gravity"], T["gravity"] + 0.3)
        for i in range(3):
            ph = ((t - T["gravity"]) * 0.8 + i / 3) % 1
            c.set_source_rgba(*SKY, a * (1 - ph)); c.set_line_width(4)
            c.arc(740, 520, 40 + ph * 300, math.pi * 0.8, math.pi * 1.2); c.stroke()
        text(c, "GRAVITY", 560, 375, 46, SKY, a, outline=False)
    if t >= T["pulls"]:
        arrow(c, 470, 640, 492, 640, GOLD, 1, w=6, head=14)
    if t >= T["tiny"]:
        q = popin(t, T["tiny"], 0.25)
        c.set_source_rgba(1, 1, 1, 0.95); c.set_line_width(10); c.arc(480, 640, 70 * q, 0, 6.283); c.stroke()
        c.move_to(480 + 50 * q, 640 + 50 * q); c.line_to(480 + 110 * q, 640 + 110 * q); c.set_line_width(18); c.stroke()
        text(c, "TINY", 640, 690, 64 * q, GOLD, 1, ow=0.16)
    c.restore()
    plan_chip(c, t, 3, FAIL[3])
    fail_x(c, t, FAIL[3], 540, 900, 200)
    vignette(c, 0.35)


# ---------- viragem: "the secret isn't pushing harder. It's pushing earlier." ----------
def s_turn(c, t):
    u = t - T["then"]; D = T["so"] - T["then"]
    z = 1.30 + 0.55 * smooth(u / D)
    view(c, "a2_genio", z, 0.5, 0.35, t, px=0, py=0, push=0.04 * u)
    dim(c, 0.22)
    g = cairo.RadialGradient(540, 760, 250, 540, 760, 1000)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0.01, 0.01, 0.05, 0.8); c.set_source(g); c.paint()
    if t >= T["harder"] - 0.05:
        k = popin(t, T["harder"] - 0.05)
        text(c, "PUSH HARDER", 540, 270, 92, (0.8, 0.82, 0.88), 1, ow=0.15, scale=k, rot=-0.03)
        q = seg(t, T["harder"] + 0.3, T["harder"] + 0.55)
        if q > 0:
            c.set_source_rgba(*RED, 1); c.set_line_width(16); c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.move_to(200, 285); c.line_to(200 + 680 * q, 255); c.stroke()
    if t >= T["earlier"] - 0.05:
        k = popin(t, T["earlier"] - 0.05, 0.3)
        glow(c, 540, 1240, 420 * k, GREEN, 0.25)
        text(c, "PUSH EARLIER", 540, 1240, 132, GREEN, 1, ow=0.16, scale=k, rot=-0.03)


# ---------- plano E: a nave pequena bate anos antes (a5) ----------
def s_dart(c, t):
    u = t - T["so"]; D = T["because"] - T["so"]; p = smooth(u / D)
    P = view(c, "a5_impacto", lerp(1.30, 1.05, p), lerp(0.60, 0.52, p), lerp(0.30, 0.44, p), t, px=8 * u, py=-6 * u, push=0.03 * u)
    ix, iy = P(0.62, 0.30)
    if t >= T["crash"] - 0.05:
        v = t - T["crash"] + 0.05
        glow(c, ix, iy, 380, (1, 0.95, 0.75), 0.8 * math.exp(-v * 2.5) + 0.2)
        if v < 0.15: dim(c, 0.5 * (1 - v / 0.15), (1, 1, 0.95))
    stamp(c, t, T["so"] + 0.05, "PLAN E", 330, 300 if p < 0.5 else 300, GOLD, 120, rot=-0.06, mark="check")
    if t >= T["years"]:
        k = popin(t, T["years"])
        c.save(); c.translate(540, 1240); c.rotate(-0.03); c.scale(k, k)
        c.set_source_rgba(0.04, 0.04, 0.12, 0.9); rr(c, -390, -70, 780, 140, 70); c.fill()
        c.set_source_rgba(*GREEN, 1); c.set_line_width(5); rr(c, -390, -70, 780, 140, 70); c.stroke(); c.restore()
        text(c, "YEARS BEFORE IMPACT", 540, 1240, 62 * k, INK, 1, outline=False, rot=-0.03)
    vignette(c, 0.35)


# ---------- trajetória: um toque pequeno longe = milhares de km (a6) ----------
def s_traj(c, t):
    u = t - T["because"]
    P = view(c, "a6_alivio", 1.04 + 0.02 * u, 0.5, 0.46, t, px=-4 * u, py=4 * u, push=0.02 * u)
    dim(c, 0.12)
    S = (140, 120); E = P(0.30, 0.66); Ax, Ay = P(0.885, 0.255)
    a = seg(t, T["because"], T["because"] + 0.3)
    q = seg(t, T["because"], T["because"] + 0.8)
    dashed(c, S[0], S[1], lerp(S[0], E[0], q), lerp(S[1], E[1], q), RED, 0.85 * a, w=7, dash=22)
    if q >= 1: bigx(c, E[0], E[1], 34, 1.0, 0.9, w=12)
    if t >= T["nudge"]:
        v = t - T["nudge"]
        sparkle(c, S[0] + 10, S[1] + 10, 50 * popin(t, T["nudge"]), (1, 1, 0.85), 1)
        text(c, "TINY NUDGE", S[0] + 30, S[1] + 105, 50, INK, 1, align="l", scale=popin(t, T["nudge"]))
        g = ease(v / 1.4)
        c.set_source_rgba(*GREEN, 0.95); c.set_line_width(9); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(*S); c.line_to(lerp(S[0], Ax, g), lerp(S[1], Ay, g)); c.stroke()
    if t >= T["thousands"]:
        k = popin(t, T["thousands"])
        q2 = seg(t, T["thousands"], T["thousands"] + 0.5)
        c.save(); c.set_source_rgba(*GOLD, 1); c.set_line_width(6); c.set_dash([14, 10])
        c.move_to(E[0], E[1]); c.line_to(lerp(E[0], Ax, q2), lerp(E[1], Ay, q2)); c.stroke(); c.restore()
        c.save(); c.translate(540, 1250); c.rotate(-0.03); c.scale(k, k)
        c.set_source_rgba(0.04, 0.04, 0.12, 0.9); rr(c, -400, -70, 800, 140, 70); c.fill()
        c.set_source_rgba(*GOLD, 1); c.set_line_width(5); rr(c, -400, -70, 800, 140, 70); c.stroke(); c.restore()
        text(c, "THOUSANDS OF KM", 540, 1250, 66 * k, GOLD, 1, outline=False, rot=-0.03)
    if t >= T["reaches"]:
        text(c, "MISSED!", Ax - 150, Ay + 140, 72, GREEN, 1, ow=0.17, scale=popin(t, T["reaches"]), rot=-0.08)
    vignette(c, 0.3)


# ---------- é real: 2022 · NASA DART (a5) ----------
def s_real(c, t):
    u = t - T["real"]
    P = view(c, "a5_impacto", 1.0 + 0.025 * u, 0.55, 0.40, t, px=-6 * u, py=-4 * u, push=0.03 * u)
    sx_, sy_ = P(0.47, 0.17); ix, iy = P(0.62, 0.30)
    glow(c, ix, iy, 300, (1, 0.95, 0.75), 0.25 + 0.08 * math.sin(t * 7))
    if t >= T["y2022"]:
        stamp(c, t, T["y2022"], "2022", 300, 290, GOLD, 120, rot=-0.06)
    if t >= T["nasa"]:
        text(c, "NASA · DART", 330, 410, 64, INK, 1, ow=0.17, scale=popin(t, T["nasa"]), rot=-0.06)
    if t >= T["dart"]:
        k = popin(t, T["dart"])
        c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(4); c.move_to(sx_ - 20, sy_ + 30); c.line_to(sx_ - 120, sy_ + 170); c.stroke()
        text(c, "DART", sx_ - 150, sy_ + 210, 60, GOLD, 1, ow=0.17, scale=k)
    if t >= T["changed"]:
        k = popin(t, T["changed"])
        c.save(); c.translate(540, 1180); c.rotate(-0.03); c.scale(k, k)
        c.set_source_rgba(0.04, 0.04, 0.12, 0.92); rr(c, -400, -150, 800, 300, 40); c.fill()
        c.set_source_rgba(*GOLD, 1); c.set_line_width(6); rr(c, -400, -150, 800, 300, 40); c.stroke(); c.restore()
        text(c, "ORBIT CHANGED", 540, 1100, 62 * k, INK, 1, outline=False, rot=-0.03)
        if t >= T["orbit"] - 0.05:
            k2 = popin(t, T["orbit"] - 0.05, 0.3)
            glow(c, 540, 1220, 380 * k2, GOLD, 0.3 * math.exp(-(t - T["orbit"]) * 1.5))
            text(c, "−32 MIN", 540, 1215, 150 * k2, GOLD, 1, ow=0.14, rot=-0.03)
    vignette(c, 0.35)


def s_brand(c, t):
    u = t - T["brand"]
    view(c, "a5_impacto", 1.17, 0.55, 0.40, t, px=-30, push=0.08)
    dim(c, 0.62)
    draw_scratch(c, u, 540, 760, scale=0.95, skin=SKIN, accent=HOOD, ink=INK, hair=HAIR)   # cores do rapaz


# ---------- final: "Which means, next time an asteroid is heading for Earth…" → frame 0 ----------
def s_end(c, t):
    global DRIFT_T, DRIFT_MIX
    if t >= T_END - 1.5 / FPS:   # último frame = frame 0
        DRIFT_T, DRIFT_MIX = 0.0, 0.0
        s_hook(c, 0.0); return
    TR0 = T["which"]; D = T_END - 1 / FPS - TR0
    e = smooth(clamp((t - TR0) / D))
    DRIFT_MIX = e
    c0 = hook_cam(0.0)
    cs = dict(z=1.35, fx=0.5, fy=0.40, px=0, py=0, push=0.0, rot=0.0, shake=3)
    cm = {k: lerp(cs[k], c0[k], e) for k in c0}
    P = view(c, "a1_panico", cm["z"], cm["fx"], cm["fy"], t, cm["px"], cm["py"], cm["push"], cm["rot"], cm["shake"])
    ax, ay = P(0.48, 0.26)
    glow(c, ax, ay, 520, FIRE, 0.18 + 0.06 * math.sin(t * 9))
    embers(c, t, ax, ay, 0.8)
    vignette(c, 0.4)
    stop_it(c, t, seg(t, SUB_T0 + SUB_D - 0.05, T_END - 1.5 / FPS) if t < T_END - 1.5 / FPS else 1)


SCENES = [(0.0, G[0], s_hook), (G[0], A[0], make_genius(0)), (A[0], T["youve"], s_nuke), (T["youve"], G[1], s_frag),
          (G[1], A[1], make_genius(1)), (A[1], T["spinning"], s_rockets), (T["spinning"], T["it_"], s_wash),
          (T["it_"], G[2], make_react("GOES NOWHERE", T["it_"])),
          (G[2], A[2], make_genius(2)), (A[2], T["have"], s_paint), (T["have"], G[3], make_react("NO TIME", T["have"])),
          (G[3], A[3], make_genius(3)), (A[3], T["decades"], s_tractor), (T["decades"], T["then"], make_react("DECADES", T["decades"])),
          (T["then"], T["so"], s_turn), (T["so"], T["because"], s_dart), (T["because"], T["real"], s_traj),
          (T["real"], T["brand"], s_real), (T["brand"], T["which"], s_brand), (T["which"], 99, s_end)]
NO_PUNCH = {s_brand, s_end, s_wash}
SUB_T0 = T["which"] - 0.05          # pop-up logo a seguir a "That one made me scratch my head"
SUB_D = T_END - 0.42 - SUB_T0        # acaba antes do último frame (último frame = frame 0)
SUB_Y = 1190                        # por baixo da cara do rapaz, acima das legendas e longe do asteroide




def badge(c, t): pass
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
    """pop-up de subscrição (baseado em lib/subscribe_popup.py, cores do espaço/fogo)"""
    u = t - SUB_T0
    if u < 0 or u > SUB_D: return
    inn = seg(u, 0, 0.3); out = seg(u, SUB_D - 0.3, SUB_D); a = inn * (1 - out)
    done = u > 1.0
    w, h = 660, 104; x = (W - w) / 2; y = SUB_Y - 40 * (1 - inn) - 30 * out
    sc = 0.92 + 0.08 * inn - 0.05 * math.sin(math.pi * clamp((u - 0.85) / 0.25))
    c.save(); c.translate(W / 2, y + h / 2); c.scale(sc, sc); c.translate(-W / 2, -(y + h / 2))
    c.set_source_rgba(0.03, 0.06, 0.18, 0.9 * a); rr(c, x, y, w, h, h / 2); c.fill()
    col = GREY if done else GOLD
    c.set_source_rgba(*col, 0.95 * a); c.set_line_width(4); rr(c, x, y, w, h, h / 2); c.stroke()
    wig = 0.35 * math.sin((u - 1.0) * 28) * math.exp(-(u - 1.0) * 5) if done else 0
    bell_icon(c, x + 64, y + h / 2 - 2, 1.25, INK if done else GOLD, a, wig)
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
                ctx.set_source_rgba(1, 1, 1, 0.18 * (1 - ease(x))); ctx.paint()
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
WEAK = {"a", "an", "the", "to", "of", "for", "on", "in", "it", "and", "but", "is", "your", "you", "or", "by", "that", "my", "me", "no", "one"}
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


HL, WH = "&H0022D8FF&", "&H00FFFFFF&"   # destaque amarelo (BGR): contrasta com o magma, o oceano e o espaço
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




# ---------- som ----------
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
    def a(name): return f"{SFX}/{name}.wav"
    swish = wav("swish", sfx_whoosh(0.45, 500, 2600, 3))
    whoosh = wav("whoosh", sfx_whoosh(1.0, 150, 1400, 2))
    t_ = np.arange(int(0.2 * SR)) / SR
    pop = wav("pop_soft", 0.5 * np.sin(2 * np.pi * (260 + 500 * np.exp(-t_ * 35)) * t_) * np.exp(-t_ * 22))
    t_ = np.arange(int(0.9 * SR)) / SR
    ding = wav("ding", 0.35 * (np.sin(2 * np.pi * 1568 * t_) + 0.4 * np.sin(2 * np.pi * 3136 * t_)) * np.exp(-t_ * 6))
    t_ = np.arange(int(2.2 * SR)) / SR
    boom = wav("boom", 0.9 * np.sin(2 * np.pi * (38 + 50 * np.exp(-t_ * 5)) * t_) * np.exp(-t_ * 1.8))
    t_ = np.arange(int(1.6 * SR)) / SR
    shimmer = wav("shimmer", 0.25 * sum(np.sin(2 * np.pi * f * t_) for f in (880, 1320, 1760, 2640)) / 4 * np.exp(-t_ * 2.2) * np.minimum(1, t_ / 0.01))
    # EP010: "ding" de ideia igual em cada "being a genius" (pedido do guião) e som curto de falhanço igual em cada X
    t_ = np.arange(int(0.7 * SR)) / SR
    idea = wav("idea", 0.3 * sum(np.sin(2 * np.pi * f * t_) * np.exp(-t_ * 7) * (t_ >= d) for f, d in ((1318.5, 0), (1975.5, 0.07))) * np.minimum(1, t_ / 0.004))
    t_ = np.arange(int(0.75 * SR)) / SR
    f_ = np.where(t_ < 0.3, 330 - 40 * t_ / 0.3, 247 - 60 * np.clip((t_ - 0.3) / 0.45, 0, 1))
    ph = 2 * np.pi * np.cumsum(f_) / SR
    env = np.where(t_ < 0.3, np.sin(np.pi * t_ / 0.3) ** 0.5, np.sin(np.pi * np.clip((t_ - 0.3) / 0.45, 0, 1)) ** 0.5) * (1 + 0.25 * np.sin(2 * np.pi * 6 * t_))
    fail = wav("fail", 0.35 * (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)) * env)
    t_ = np.arange(int(0.5 * SR)) / SR
    thump = wav("thump", 0.8 * np.sin(2 * np.pi * (60 + 90 * np.exp(-t_ * 18)) * t_) * np.exp(-t_ * 7))
    E = [(a("scratch_head"), T["brand"], 0.6)]
    E += [(idea, g + 0.04, 0.22) for g in G]
    E += [(fail, x, 0.2) for x in FAIL]
    E += [(boom, FAIL[0] - 0.1, 0.12)]                       # explosão da bomba (baixa)
    E += [(swish, x - 0.12, 0.16) for x in (T["spinning"], T["then"], T["so"])]
    E += [(pop, T["thousand"] - 0.05, 0.16), (pop, T["fifty"] - 0.05, 0.16), (pop, T["y2022"] - 0.05, 0.16), (pop, SUB_T0 + 1.0, 0.14)]
    E += [(thump, T["crash"] - 0.03, 0.22)]
    E += [(boom, T["orbit"] - 0.1, 0.3), (shimmer, T["orbit"] - 0.05, 0.2)]   # revelação principal
    ins, ch, lab = [], [], []
    for f_, x, v in E:
        i = 3 + len(lab); ins += ["-i", f_]; d = int(max(0, x) * 1000)
        ch.append(f"[{i}:a]adelay={d}|{d},volume={v}[e{len(lab)}]"); lab.append(f"[e{len(lab)}]")
    sfx = ";".join(ch) + ";" + "".join(lab) + f"amix=inputs={len(lab)}:normalize=0[sfx]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw_video, "-i", NARR, "-stream_loop", "-1", "-i", MUSIC, *ins,
                    "-filter_complex",
                    f"[0:v]subtitles={ASS},format=yuv420p[v];"
                    "[1:a]asplit=2[n1][nk];"
                    f"[2:a]atrim=0:{T_END:.3f},volume='if(between(t,{T['then']:.2f},{T['so']:.2f}),0.05,0.12)':eval=frame[m];"
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
    raw_v = f"{BLD}/raw.mp4"
    if "--mix-only" not in sys.argv:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p", raw_v], stdin=subprocess.PIPE)
        for i in range(N_FR):
            p.stdin.write(frame(i / FPS))
        p.stdin.close(); p.wait()
    mix(raw_v)
    print("OK", OUT, T_END)
