#!/usr/bin/env python3
"""Whatifaholic EP010 — What If YOU Had to Stop an Asteroid?
Ilustração plana (3 imagens aprovadas nano_banana_pro, parallax 2.5D por profundidade) + animação por código (pycairo).
Base: EP008. Loop de frase: "…if you…" → "You just fell out of a plane." (último frame = frame 0).
Uso: python3 anim_ep009.py [--frames t1,t2,...|last] [--mix-only]   (sem argumentos: render completo + mistura)"""
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


#T#

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


def draw_par(c, name, zoom, fx, fy, px=0.0, py=0.0, push=0.0, a=1.0):
    """ilustração em camadas: zoom e ponto focal como numa câmara; px/py = deslocamento (px de ecrã) da camada
    mais próxima (as outras deslocam-se proporcionalmente); push = zoom extra da camada mais próxima (dolly)."""
    L = layers(name)
    px, py, push = px * 0.6, py * 0.6, push * 0.6     # amplitude moderada: menos artefactos nas bordas
    iw, ih = L[0].get_width(), L[0].get_height()
    base = max(W / iw, H / ih) * zoom * 1.06            # margem para o parallax não mostrar bordas
    vw, vh = W / base, H / base
    x0 = clamp(fx * iw - vw / 2, 0, iw - vw); y0 = clamp(fy * ih - vh / 2, 0, ih - vh)
    for k, s in enumerate(L):
        f = k / (NL - 1)
        sc = 1 + push * f
        c.save(); c.translate(W / 2 + px * f, H / 2 + py * f); c.scale(sc, sc); c.translate(-W / 2, -H / 2)
        c.scale(base, base); c.translate(-x0, -y0)
        c.set_source_surface(s, 0, 0); c.get_source().set_filter(cairo.FILTER_GOOD)
        c.paint_with_alpha(a); c.restore()
    return base, x0, y0



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

