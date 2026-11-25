#!/usr/bin/env python3
"""Whatifaholic EP009 — What If You Fell Out of a Plane Without a Parachute?
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
OUT = f"{ROOT}/whatifaholic_ep009_parachute.mp4"
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


T = dict(no=at("no"), first=at("first") - 0.1, ten=at("ten"), fifty=at("fifty"), air=at("air"), pass_=at("pass"),
         honestly=at("honestly"), best=at("best"), wake=at("wake") - 0.12, now=at("now") - 0.1, n200=at("200"),
         top=at("top"), spread=at("spread") - 0.1, starfish=at("starfish"), slows=at("slows"), water=at("water") - 0.1,
         bad=at("bad"), concrete=at("concrete"), snow=at("snow"), trees=at("trees"), really=at("really"),
         soft=at("soft"), sounds=at("sounds") - 0.05, n1944=at("1944"), six=at("six"), pine=at("pine"),
         deep=at("deep"), sprained=at("sprained"), brand=at("that", 1) - 0.08, and72=at("and", 4) - 0.08,
         n1972=at("1972"), ten2=at("ten", 2), trapped=at("trapped"), survived=at("survived"), world=at("world"),
         so=at("so") - 0.08, exactly=at("exactly"), what=at("what", 2), do=at("do"), ifyou=at("if") - 0.05)

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


# ---------- gancho: cais do avião (s1), frame 0 já em queda ----------
def cam1(t):
    """câmara do gancho: zoom a afastar, tremor e rotação (frame 0 já em movimento)"""
    p = smooth(t / 5.4)
    z = 1.24 - 0.14 * p
    rot = 0.035 * math.sin(t * 7.3 + 0.6) + 0.018 * math.sin(t * 12.9)
    sx = 9 * math.sin(t * 21.0) + 5 * math.sin(t * 33.0); sy = 7 * math.cos(t * 17.0)
    return z, rot, sx, sy, p


def timer_txt(t):
    v = max(0.0, 180.0 - t); m = int(v // 60); s = v - m * 60
    return f"{m}:{s:05.2f}"


def s_hook(c, t, camt=None):
    t = max(0.0, t)
    z, rot, sx, sy, p = cam1(t if camt is None else camt)
    c.save(); c.translate(W / 2 + sx, H / 2 + sy); c.rotate(rot); c.translate(-W / 2, -H / 2)
    draw_par(c, "s1_queda_aviao", z, 0.5, 0.44, px=-30 * p, py=120 * p + 20, push=0.10 * p)
    c.restore()
    wind_lines(c, t, 0.55, 0.8)
    # cronómetro de 3:00 a descer (desde o frame 0)
    c.save(); c.set_source_rgba(0.02, 0.04, 0.12, 0.72); rr(c, 300, 225, 480, 150, 34); c.fill()
    c.set_source_rgba(*RED, 0.9); c.set_line_width(5); rr(c, 300, 225, 480, 150, 34); c.stroke(); c.restore()
    c.set_source_rgba(*RED, 0.6 + 0.4 * math.sin(t * 8)); c.arc(345, 300, 13, 0, 2 * math.pi); c.fill()
    text(c, timer_txt(t), 560, 300, 104, INK, 1, outline=False)
    k = popin(t, T["no"] - 0.05, 0.25)
    text(c, "NO PARACHUTE", 540, 460, 96, ORANGE, 1, ow=0.15, scale=k, rot=-0.03)
    vignette(c, 0.35)


# ---------- 10 km, -50 °C, desmaio cómico (código) ----------
def guy(c, x, y, s, t, eyes=1.0, rot=0.0, flail=1.0, mouth="o", hood=(0.5, 0.36, 0.42)):
    """boneco em queda (inspirado no da ilustração s1): capuz malva, calças de ganga, cabelo castanho"""
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    skin = (0.98, 0.8, 0.64); jeans = (0.22, 0.32, 0.5); hair = (0.45, 0.27, 0.14)
    w1 = math.sin(t * 9) * 0.35 * flail; w2 = math.sin(t * 9 + 2) * 0.35 * flail
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    # pernas
    for sgn, wv in ((-1, w1), (1, w2)):
        c.set_source_rgb(*jeans); c.set_line_width(44)
        c.move_to(sgn * 30, 120); c.line_to(sgn * (70 + 30 * wv), 230); c.line_to(sgn * (95 + 40 * wv), 330); c.stroke()
        c.set_source_rgb(0.55, 0.2, 0.2); c.arc(sgn * (98 + 40 * wv), 345, 26, 0, 2 * math.pi); c.fill()
    # braços (no ar, a abanar)
    for sgn, wv in ((-1, w2), (1, w1)):
        c.set_source_rgb(*hood); c.set_line_width(40)
        c.move_to(sgn * 60, -20); c.line_to(sgn * (130 + 20 * wv), -90 - 30 * wv); c.line_to(sgn * (150 + 30 * wv), -190 - 20 * wv); c.stroke()
        c.set_source_rgb(*skin); c.arc(sgn * (152 + 30 * wv), -205 - 20 * wv, 24, 0, 2 * math.pi); c.fill()
    # tronco (capuz)
    c.set_source_rgb(*hood); rr(c, -78, -60, 156, 200, 50); c.fill()
    c.set_source_rgba(0, 0, 0, 0.15); c.rectangle(-78, 95, 156, 14); c.fill()
    # cabeça
    c.set_source_rgb(*skin); c.arc(0, -125, 78, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*hair)
    c.move_to(-80, -135); c.curve_to(-90, -230, 60, -250, 82, -150); c.curve_to(60, -185, 20, -170, 0, -195)
    c.curve_to(-20, -170, -50, -190, -80, -135); c.fill()
    # olhos (pálpebras animadas)
    for ex in (-30, 30):
        c.set_source_rgb(1, 1, 1); c.arc(ex, -125, 22, 0, 2 * math.pi); c.fill()
        if eyes > 0.05:
            c.set_source_rgb(0.1, 0.07, 0.05); c.arc(ex + 3, -122, 9 * (0.6 + 0.4 * eyes), 0, 2 * math.pi); c.fill()
        lid = 1 - eyes
        if lid > 0:
            c.save(); c.arc(ex, -125, 23, 0, 2 * math.pi); c.clip()
            c.set_source_rgb(*skin); c.rectangle(ex - 25, -150, 50, 50 * lid); c.fill(); c.restore()
            c.set_source_rgb(0.3, 0.18, 0.12); c.set_line_width(4)
            c.move_to(ex - 22, -148 + 46 * lid); c.line_to(ex + 22, -148 + 46 * lid); c.stroke()
    c.set_source_rgb(0.35, 0.1, 0.1)
    if mouth == "o": c.arc(0, -80, 16, 0, 2 * math.pi); c.fill()
    else:
        c.set_line_width(6); c.move_to(-18, -82); c.curve_to(-6, -74, 6, -74, 18, -82); c.stroke()
    c.restore()


def thermo(c, x, y, k, a=1.0):
    """termómetro a descer até -50 °C (k: 0 → 1)"""
    c.set_source_rgba(0.04, 0.07, 0.16, 0.85 * a); rr(c, x - 50, y - 210, 100, 300, 50); c.fill()
    c.set_source_rgba(1, 1, 1, 0.9 * a); c.set_line_width(4); rr(c, x - 22, y - 180, 44, 220, 22); c.stroke()
    lvl = lerp(170, 18, k)
    c.set_source_rgba(*ICE, a); rr(c, x - 12, y + 40 - lvl, 24, lvl, 12); c.fill(); c.arc(x, y + 52, 30, 0, 2 * math.pi); c.fill()


def frost(c, a):
    if a <= 0: return
    for (cx, cy) in ((0, 0), (W, 0), (0, H), (W, H)):
        glow(c, cx, cy, 520, ICE, 0.55 * a)
    rnd = random.Random(2)
    for i in range(40):
        cx, cy = rnd.choice(((0, 0), (W, 0), (0, H), (W, H)))
        ang = rnd.random() * 6.28; d = rnd.random() * 300
        x = abs(cx - abs(math.cos(ang)) * d); y = abs(cy - abs(math.sin(ang)) * d)
        sparkle(c, x, y, 8 + rnd.random() * 14, (1, 1, 1), 0.7 * a)


def sky_high(c, t, k_dark=1.0):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *[lerp(a, b, k_dark) for a, b in zip((0.2, 0.5, 0.9), (0.02, 0.04, 0.16))])
    g.add_color_stop_rgb(1, *[lerp(a, b, k_dark) for a, b in zip((0.5, 0.82, 1.0), (0.18, 0.36, 0.72))])
    c.set_source(g); c.paint()
    rnd = random.Random(5)
    for _ in range(70):
        x, y, r = rnd.random() * W, rnd.random() * H * 0.6, rnd.random() * 2 + 0.6
        c.set_source_rgba(1, 1, 1, 0.5 * k_dark); c.arc(x, y, r, 0, 2 * math.pi); c.fill()


def cloud(c, x, y, s, a=1.0, col=(1, 1, 1)):
    c.set_source_rgba(*col, a)
    for dx, dy, r in ((-90, 10, 60), (-30, -25, 80), (50, -10, 70), (110, 15, 50), (0, 25, 70)):
        c.arc(x + dx * s, y + dy * s, r * s, 0, 2 * math.pi); c.fill()


def s_altitude(c, t):
    """'First problem…' até '…on the way down.'"""
    u = t - T["first"]
    wake = seg(t, T["wake"], T["wake"] + 0.15)
    sky_high(c, t, 1.0 - 0.5 * seg(t, T["wake"], T["now"]))
    # nuvens a subir (estamos a cair); depois de acordar sobem mais depressa
    rnd = random.Random(11)
    fast = 1 + 3 * seg(t, T["wake"], T["wake"] + 0.6)
    for i in range(9):
        x = rnd.random() * W; y0 = rnd.random() * (H + 600); s = 0.6 + rnd.random() * 1.2
        y = (y0 - u * (160 + 120 * s) * fast) % (H + 600) - 300
        cloud(c, x, y, s, 0.55 + 0.3 * (s > 1))
    wind_lines(c, t, 0.4 + 0.5 * wake, 0.7 + 1.0 * wake, seed=8)
    frost(c, seg(t, T["fifty"], T["fifty"] + 0.4) * (1 - seg(t, T["wake"] + 0.3, T["now"])))
    # o boneco: a tremer de frio, desmaia (olhos fecham), Zzz, acorda de olhos esbugalhados
    sleep = seg(t, T["pass_"], T["pass_"] + 0.5) * (1 - wake)
    eyes = 1 - sleep
    gx = 540 + 14 * math.sin(t * 30) * seg(t, T["fifty"], T["fifty"] + 0.3) * (1 - sleep)
    gy = 960 + 20 * math.sin(t * 2)
    rot = 0.15 * math.sin(u * 1.3) + 0.6 * sleep * math.sin(t * 1.2)
    scl = 0.95 * (1 + 0.15 * popin(t, T["wake"], 0.3) * (t < T["wake"] + 0.3) * 0)
    guy(c, gx, gy, scl * (1 + 0.12 * wake * (1 - seg(t, T["wake"] + 0.2, T["wake"] + 0.5))), t,
        eyes=eyes if wake == 0 else 1.25, rot=rot * (1 - wake), flail=1 - 0.85 * sleep, mouth="smile" if sleep > 0.5 else "o")
    if wake > 0 and t < T["now"]:
        text(c, "!", 540 + 170, 700, 170, GOLD, 1, ow=0.12, scale=popin(t, T["wake"], 0.25), rot=0.2)
    # Zzz
    if sleep > 0.2:
        for i in range(3):
            ph = ((t - T["pass_"]) * 0.8 + i / 3) % 1
            text(c, "Z", 660 + 90 * ph + 20 * i, 760 - 260 * ph, 70 + 40 * ph, INK, (1 - ph) * sleep, ow=0.14, rot=0.2)
    # altímetro (topo à esquerda) e termómetro (topo à direita)
    ka = popin(t, T["ten"] - 0.08, 0.25)
    if ka > 0:
        alt = 10.0 if t < T["wake"] else lerp(10.0, 4.0, smooth((t - T["wake"]) / (T["now"] - T["wake"] + 0.3)))
        c.save(); c.translate(270, 330); c.scale(ka, ka)
        c.set_source_rgba(0.04, 0.07, 0.16, 0.85); rr(c, -200, -95, 400, 190, 40); c.fill()
        c.set_source_rgba(*SKY, 1); c.set_line_width(5); rr(c, -200, -95, 400, 190, 40); c.stroke()
        c.restore()
        text(c, "ALTITUDE", 270, 330 - 52 * ka, 34, SKY, 1, outline=False, scale=ka)
        text(c, f"{alt:.0f} KM" if alt >= 9.95 else f"{alt:.1f} KM", 270, 330 + 25 * ka, 88, INK, 1, outline=False, scale=ka)
    kt = popin(t, T["fifty"] - 0.08, 0.25)
    if kt > 0:
        thermo(c, 930, 380, seg(t, T["fifty"] - 0.1, T["fifty"] + 0.5), 1)
        text(c, "-50°C", 730, 330, 92, ICE, 1, ow=0.15, scale=kt)
    if t >= T["air"] - 0.1:
        k = popin(t, T["air"] - 0.1, 0.22)
        lvl = 1 - 0.8 * seg(t, T["air"] - 0.1, T["air"] + 0.6)
        if t > T["wake"]: lvl = lerp(lvl, 0.75, seg(t, T["wake"], T["now"]))
        c.save(); c.translate(540, 560); c.scale(k, k)
        c.set_source_rgba(0.04, 0.07, 0.16, 0.85); rr(c, -230, -42, 460, 84, 42); c.fill()
        c.set_source_rgba(*(RED if lvl < 0.4 else LIME), 1); rr(c, -60, -18, 270 * lvl, 36, 18); c.fill()
        c.set_source_rgba(1, 1, 1, 0.6); c.set_line_width(3); rr(c, -60, -18, 270, 36, 18); c.stroke()
        c.restore()
        text(c, "AIR", 540 - 150 * k, 560, 44, INK, 1, outline=False, scale=k)
    card(c, t, T["best"] - 0.05, [("BEST NAP", GOLD), ("OF YOUR LIFE", INK)], 210, 1180, 660, GOLD,
         bg=(0.05, 0.07, 0.2), t1=T["wake"] + 0.1, size=60, rot=0.03)
    vignette(c, 0.4)


# ---------- 200 km/h, estrela (s2) ----------
def gauge(c, x, y, val, a=1.0, vmax=250, label=True):
    R = 165; k = clamp(val / vmax)
    c.save(); c.translate(x, y)
    c.set_source_rgba(0.04, 0.07, 0.16, 0.85 * a); c.arc(0, 0, R + 34, math.pi, 2 * math.pi); c.close_path(); c.fill()
    c.set_line_width(26); c.set_source_rgba(0.3, 0.35, 0.45, a); c.arc(0, 0, R, math.pi, 2 * math.pi); c.stroke()
    g = cairo.LinearGradient(-R, 0, R, 0); g.add_color_stop_rgba(0, *LIME, a); g.add_color_stop_rgba(0.6, *GOLD, a); g.add_color_stop_rgba(1, *RED, a)
    c.set_source(g); c.arc(0, 0, R, math.pi, math.pi + math.pi * k); c.stroke()
    ang = math.pi + math.pi * k
    c.set_source_rgba(1, 1, 1, a); c.set_line_width(8); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(0, 0); c.line_to(math.cos(ang) * (R - 30), math.sin(ang) * (R - 30)); c.stroke(); c.arc(0, 0, 14, 0, 2 * math.pi); c.fill()
    c.restore()
    if label: text(c, f"{min(200, int(round(val)))} KM/H", x, y + 62, 70, INK, a, ow=0.16)


def star_outline(c, cx, cy, R, a, k):
    if a <= 0 or k <= 0: return
    pts = []
    for i in range(10):
        r = R if i % 2 == 0 else R * 0.45; an = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + r * math.cos(an), cy + r * math.sin(an)))
    c.save(); c.set_source_rgba(*GOLD, a); c.set_line_width(8); c.set_dash([26, 16], -k * 200); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(*p)
    c.close_path(); c.stroke(); c.restore()


def s_star(c, t):
    u = t - T["now"]; D = T["water"] - T["now"]
    p = smooth(u / D)
    z = 1.17 + 0.16 * p
    sh = 6 * math.sin(t * 25) * (1 - seg(t, T["spread"], T["spread"] + 0.6))
    c.save(); c.translate(sh, 0)
    base, x0, y0 = draw_par(c, "s2_estrela", z, 0.5, lerp(0.33, 0.28, p), px=10 * math.sin(u), py=-40 * p, push=0.12 * p)
    c.restore()
    wind_lines(c, t, 0.75, 1.6, n=34, seed=3)
    # velocímetro: sobe até 200 e fixa ("top speed")
    v = 200 * ease((t - T["now"]) / (T["n200"] + 0.3 - T["now"]))
    v += 1.5 * math.sin(t * 20) * (t > T["n200"])
    ka = 1 - seg(t, T["water"] - 0.3, T["water"])
    gauge(c, 540, 1250, v, ka)
    k = popin(t, T["top"] - 0.05, 0.25) * (1 - seg(t, T["slows"] - 0.3, T["slows"] - 0.1)) if t >= T["top"] - 0.05 else 0
    if k > 0.01:
        k = popin(t, T["top"] - 0.05, 0.25) * (1 - seg(t, T["slows"] - 0.3, T["slows"] - 0.1))
        c.save(); c.translate(540, 1000); c.rotate(-0.06); c.scale(k, k)
        c.set_source_rgba(*RED, 0.92); rr(c, -210, -50, 420, 100, 22); c.fill()
        c.set_source_rgba(1, 1, 1, 1); c.set_line_width(5); rr(c, -196, -38, 392, 76, 16); c.stroke(); c.restore()
        text(c, "TOP SPEED", 540, 1000, 62, INK, 1, outline=False, scale=k, rot=-0.06)
    # a estrela-do-mar desenhada à volta do boneco
    gx, gy = img2scr(base, x0, y0, 0.5 * 1536, 0.2 * 2752)
    ks = seg(t, T["spread"] + 0.2, T["starfish"] + 0.2)
    star_outline(c, gx, gy + 150, 400, ks, u)
    if t >= T["starfish"]:
        text(c, "STARFISH MODE", 540, 330, 92, GOLD, 1, ow=0.15, scale=popin(t, T["starfish"], 0.25), rot=-0.03)
    if t >= T["slows"] - 0.1:   # setas da resistência do ar (para cima)
        k = seg(t, T["slows"] - 0.1, T["slows"] + 0.3)
        for dx in (-260, 0, 260):
            ax, ay = gx + dx, gy + 470 - 40 * k + 18 * math.sin(t * 8 + dx)
            c.set_source_rgba(*SKY, 0.95 * k); c.set_line_width(14); c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.move_to(ax, ay + 90); c.line_to(ax, ay); c.stroke()
            c.move_to(ax - 30, ay + 30); c.line_to(ax, ay); c.line_to(ax + 30, ay + 30); c.stroke()
        text(c, "AIR PUSHES BACK", 540, 1000, 70, SKY, k, ow=0.16)
    vignette(c, 0.35)


# ---------- menu de aterragem (código) ----------
def tile(c, x, y, w, h, kind, k, morph=0.0, a=1.0):
    """azulejo do menu; kind: water / snow / trees / hill. morph (água → cimento)"""
    if k <= 0: return
    c.save(); c.translate(x + w / 2, y + h / 2); c.scale(k, k); c.translate(-w / 2, -h / 2)
    c.set_source_rgba(0, 0, 0, 0.3); rr(c, 8, 12, w, h, 34); c.fill()
    c.save(); rr(c, 0, 0, w, h, 34); c.clip()
    if kind == "water":
        top = [lerp(a_, b_, morph) for a_, b_ in zip((0.2, 0.6, 0.95), (0.62, 0.62, 0.64))]
        bot = [lerp(a_, b_, morph) for a_, b_ in zip((0.05, 0.3, 0.7), (0.45, 0.45, 0.48))]
        g = cairo.LinearGradient(0, 0, 0, h); g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bot); c.set_source(g); c.paint()
        tt = time_now[0]
        for i in range(4):   # ondas (desaparecem com o cimento)
            yy = 70 + i * 55
            c.set_source_rgba(1, 1, 1, 0.55 * (1 - morph)); c.set_line_width(7)
            c.move_to(0, yy)
            for xx in range(0, int(w) + 10, 10): c.line_to(xx, yy + 10 * math.sin(xx / 30 + tt * 4 + i))
            c.stroke()
        if morph > 0:   # fissuras e grão do cimento
            c.set_source_rgba(0.25, 0.25, 0.27, morph); c.set_line_width(5)
            c.move_to(30, 40); c.line_to(120, 110); c.line_to(100, 190); c.line_to(170, 260); c.stroke()
            c.move_to(w - 40, 30); c.line_to(w - 120, 140); c.line_to(w - 70, 230); c.stroke()
            rnd = random.Random(1)
            for _ in range(120):
                c.set_source_rgba(0.3, 0.3, 0.32, 0.5 * morph); c.arc(rnd.random() * w, rnd.random() * h, 2.5, 0, 6.3); c.fill()
    elif kind == "snow":
        g = cairo.LinearGradient(0, 0, 0, h); g.add_color_stop_rgb(0, 0.55, 0.75, 0.95); g.add_color_stop_rgb(1, 0.8, 0.9, 1); c.set_source(g); c.paint()
        c.set_source_rgb(1, 1, 1)
        c.move_to(0, h * 0.62); c.curve_to(w * 0.3, h * 0.45, w * 0.6, h * 0.7, w, h * 0.55); c.line_to(w, h); c.line_to(0, h); c.close_path(); c.fill()
        rnd = random.Random(3)
        for _ in range(26): c.arc(rnd.random() * w, (rnd.random() * h * 0.6 + time_now[0] * 40) % (h * 0.6), 4, 0, 6.3); c.fill()
    elif kind == "trees":
        g = cairo.LinearGradient(0, 0, 0, h); g.add_color_stop_rgb(0, 0.6, 0.8, 0.98); g.add_color_stop_rgb(1, 0.85, 0.93, 1); c.set_source(g); c.paint()
        for tx, ts_, sh in ((0.25, 1.0, 0.0), (0.55, 1.25, 0.03), (0.82, 0.9, 0.0)):
            bx, by = w * tx, h * 0.92
            c.set_source_rgb(0.4, 0.25, 0.12); c.rectangle(bx - 10, by - 30, 20, 30); c.fill()
            c.set_source_rgb(0.12 + sh, 0.42, 0.25)
            for j in range(3):
                yy = by - 30 - j * 55 * ts_
                c.move_to(bx - 70 * ts_ * (1 - j * 0.2), yy); c.line_to(bx, yy - 90 * ts_); c.line_to(bx + 70 * ts_ * (1 - j * 0.2), yy); c.close_path(); c.fill()
    elif kind == "hill":
        g = cairo.LinearGradient(0, 0, 0, h); g.add_color_stop_rgb(0, 0.65, 0.85, 1); g.add_color_stop_rgb(1, 0.9, 0.96, 1); c.set_source(g); c.paint()
        b = 1 + 0.06 * math.sin(time_now[0] * 10) * (morph > 0)   # colina "fofa" a saltitar
        c.save(); c.translate(w / 2, h); c.scale(1 / b, b); c.translate(-w / 2, -h)
        c.set_source_rgb(0.45, 0.8, 0.4)
        c.move_to(-10, h); c.curve_to(w * 0.1, h * 0.25, w * 0.9, h * 0.25, w + 10, h); c.close_path(); c.fill()
        c.set_source_rgba(1, 1, 1, 0.35)   # costuras de almofada
        c.set_line_width(5); c.move_to(w * 0.3, h * 0.55); c.curve_to(w * 0.45, h * 0.5, w * 0.55, h * 0.5, w * 0.7, h * 0.55); c.stroke()
        c.restore()
    c.restore()
    c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(5); rr(c, 0, 0, w, h, 34); c.stroke()
    c.restore()


time_now = [0.0]
TILES = [("water", 120, 430), ("snow", 570, 430), ("trees", 120, 830), ("hill", 570, 830)]


def s_menu(c, t):
    time_now[0] = t
    u = t - T["water"]
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.16, 0.42, 0.85); g.add_color_stop_rgb(1, 0.55, 0.82, 1); c.set_source(g); c.paint()
    rnd = random.Random(21)
    for i in range(7):
        x = rnd.random() * W; y0 = rnd.random() * (H + 600); s = 0.6 + rnd.random()
        cloud(c, x, (y0 - u * 260 * s) % (H + 600) - 300, s, 0.35)
    wind_lines(c, t, 0.35, 1.0, seed=12)
    text(c, "PICK YOUR LANDING", 540, 330, 80, INK, 1, ow=0.15, scale=popin(t, T["water"], 0.25))
    tw, th = 390, 370
    times = dict(water=T["water"], snow=T["snow"] - 0.1, trees=T["trees"] - 0.1, hill=T["really"] - 0.1)
    for kind, x, y in TILES:
        k = popin(t, times[kind], 0.25)
        morph = seg(t, T["concrete"] - 0.1, T["concrete"] + 0.35) if kind == "water" else (float(t > T["really"]) if kind == "hill" else 0)
        tile(c, x, y, tw, th, kind, k, morph)
        if k <= 0: continue
        lab = {"water": "CONCRETE" if morph > 0.5 else "WATER", "snow": "SNOW", "trees": "TREES", "hill": "SOFT HILL"}[kind]
        c.save(); c.translate(x + tw / 2, y + th - 46); c.scale(k, k)
        c.set_source_rgba(0.03, 0.05, 0.14, 0.82); rr(c, -150, -34, 300, 68, 34); c.fill(); c.restore()
        text(c, lab, x + tw / 2, y + th - 46, 44 if lab != "CONCRETE" else 40, INK, 1, outline=False, scale=k)
        # selo ✓ / ✗ desenhado
        mt = {"water": T["bad"], "snow": T["snow"] + 0.15, "trees": T["trees"] + 0.15, "hill": T["soft"]}[kind]
        if t >= mt:
            q = seg(t, mt, mt + 0.25); cx, cy = x + tw - 52, y + 52
            c.set_source_rgba(*(RED if kind == "water" else (0.15, 0.7, 0.3)), 1); c.arc(cx, cy, 44 * popin(t, mt, 0.2), 0, 2 * math.pi); c.fill()
            if kind == "water": xmark(c, cx, cy, 18, INK, q, w=10)
            else: check(c, cx + 4, cy - 4, 52, INK, 1, q)
    if t >= T["concrete"]:   # piada: a água "parte-se" como cimento
        card(c, t, T["concrete"], [("SPLASH?", INK), ("MORE LIKE CRUNCH", GOLD)], 170, 1240, 740, GOLD, bg=(0.05, 0.07, 0.2), t1=T["snow"] - 0.2, size=50)
    if t >= T["really"]:
        card(c, t, T["soft"], [("LIKE YOUR BED", INK), ("ON A MONDAY MORNING", GOLD)], 130, 1240, 820, GOLD, bg=(0.05, 0.07, 0.2), t1=T["sounds"] - 0.05, size=48)
    if t >= T["sounds"]:
        k = popin(t, T["sounds"], 0.2)
        c.set_source_rgba(0, 0, 0, 0.35 * min(1, k)); c.paint()
        text(c, "IMPOSSIBLE?", 540, 860, 130, GOLD, 1, ow=0.14, scale=k, rot=-0.05)
    vignette(c, 0.35)


# ---------- 1944: o piloto na neve (s3) ----------
def s_pilot(c, t):
    u = t - T["sounds"] - 0.4; D = T["brand"] - T["sounds"]
    p = smooth(max(0, u) / D)
    z = 1.26 + 0.22 * p
    draw_par(c, "s3_piloto_neve", z, lerp(0.5, 0.56, p), lerp(0.48, 0.6, p), px=-20 * p, py=-30 * p, push=0.1 * p)
    snowfall(c, t, 0.8)
    if t >= T["n1944"] - 0.1:
        text(c, "1944", 540, 330, 170, GOLD, 1, ow=0.12, scale=popin(t, T["n1944"] - 0.1, 0.28))
    if t >= T["six"] - 0.1:
        k = popin(t, T["six"] - 0.1, 0.25)
        text(c, "18,000 FT FALL", 540, 490, 70, INK, 1, ow=0.16, scale=k)
    chip(c, t, T["pine"] - 0.05, "PINE TREES", 300, 640, LIME, w=420)
    chip(c, t, T["deep"] - 0.05, "DEEP SNOW", 780, 640, LIME, w=400)
    if t >= T["sprained"] - 0.1:   # resultado: só uma entorse (ligadura desenhada)
        k = popin(t, T["sprained"] - 0.1, 0.25)
        c.save(); c.translate(540, 1270); c.rotate(-0.03); c.scale(k, k)
        c.set_source_rgba(0.05, 0.07, 0.2, 0.9); rr(c, -370, -70, 740, 140, 34); c.fill()
        c.set_source_rgba(*GOLD, 1); c.set_line_width(5); rr(c, -370, -70, 740, 140, 34); c.stroke()
        c.save(); c.translate(-290, 0); c.rotate(-0.6)   # ligadura
        c.set_source_rgb(0.98, 0.9, 0.78); rr(c, -60, -24, 120, 48, 20); c.fill()
        c.set_source_rgb(0.9, 0.75, 0.6); rr(c, -20, -24, 40, 48, 6); c.fill()
        c.set_source_rgba(0.6, 0.45, 0.35, 0.7)
        for dx in (-10, 0, 10):
            for dy in (-10, 0, 10): c.arc(dx, dy, 2.5, 0, 6.3); c.fill()
        c.restore(); c.restore()
        text(c, "DAMAGE: 1 SPRAINED LEG", 580, 1270, 44, INK, 1, outline=False, scale=k, rot=-0.03)
    vignette(c, 0.4)


def s_brand(c, t):
    u = t - T["brand"]
    draw_par(c, "s3_piloto_neve", 1.48 + 0.03 * u, 0.56, 0.6, px=-20, py=-30, push=0.1)
    snowfall(c, t, 0.6)
    c.set_source_rgba(0.03, 0.04, 0.12, 0.62); c.paint()
    draw_scratch(c, u, 540, 760, scale=0.95, skin=(1.0, 0.82, 0.66), accent=SKY, ink=INK, hair=(0.45, 0.27, 0.14))


# ---------- 1972: recorde (código; sem acidente nem destroços) ----------
EVEREST = 8849; REC = 10160


def s_record(c, t):
    u = t - T["and72"]
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.04, 0.16); g.add_color_stop_rgb(0.7, 0.2, 0.25, 0.55)
    g.add_color_stop_rgb(1, 0.95, 0.55, 0.35); c.set_source(g); c.paint()
    rnd = random.Random(8)
    for _ in range(90):
        x, y, r = rnd.random() * W, rnd.random() * H * 0.7, rnd.random() * 2 + 0.6
        c.set_source_rgba(1, 1, 1, 0.3 + 0.4 * abs(math.sin(t * 2 + x))); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    out = seg(t, T["survived"] - 0.15, T["survived"] + 0.2)
    # "1972"
    if t >= T["n1972"] - 0.1:
        mv = seg(t, T["ten2"] - 0.3, T["ten2"])
        text(c, "1972", 540, 560 - 110 * mv, 170, GOLD, 1, ow=0.12, scale=popin(t, T["n1972"] - 0.1, 0.28) * (1 - 0.3 * mv))
    # régua de altitude a subir até 10 160 m; Everest como referência
    a = 1 - out
    if a > 0 and t >= T["n1972"] + 0.4:
        ka = seg(t, T["n1972"] + 0.4, T["n1972"] + 0.8) * a
        y0, y1 = 1360, 760; X = 330
        def ym(m): return y0 - (y0 - y1) * m / REC
        c.set_source_rgba(1, 1, 1, 0.85 * ka); c.set_line_width(6); c.move_to(X, y0); c.line_to(X, y1 - 30); c.stroke()
        for m in range(0, REC + 1, 2000):
            c.move_to(X - 22, ym(m)); c.line_to(X + 22, ym(m)); c.stroke()
            text(c, f"{m // 1000} KM", X - 40, ym(m), 30, INK, 0.8 * ka, align="r", outline=False)
        # montanha (Everest) à direita da régua
        ex = 640
        c.set_source_rgba(0.75, 0.82, 0.95, 0.9 * ka); c.move_to(ex - 260, y0); c.line_to(ex - 40, ym(EVEREST)); c.line_to(ex + 10, ym(EVEREST) + 50)
        c.line_to(ex + 60, ym(EVEREST) + 20); c.line_to(ex + 280, y0); c.close_path(); c.fill()
        c.set_source_rgba(1, 1, 1, ka); c.move_to(ex - 105, ym(EVEREST) + 140); c.line_to(ex - 40, ym(EVEREST)); c.line_to(ex + 10, ym(EVEREST) + 50)
        c.line_to(ex + 60, ym(EVEREST) + 20); c.line_to(ex + 120, ym(EVEREST) + 150); c.close_path(); c.fill()
        dashed(c, X, ym(EVEREST), ex + 300, ym(EVEREST), INK, 0.5 * ka, w=3)
        text(c, "EVEREST", ex + 190, ym(EVEREST) + 70, 38, INK, 0.95 * ka, ow=0.18)
        text(c, "8,849 M", ex + 190, ym(EVEREST) + 115, 34, INK, 0.95 * ka, ow=0.18)
        m = REC * ease((t - T["ten2"] + 0.1) / (T["trapped"] + 0.5 - T["ten2"]))
        yy = ym(m)
        c.set_source_rgba(*GOLD, ka); c.move_to(X + 4, yy); c.line_to(X + 40, yy - 22); c.line_to(X + 40, yy + 22); c.close_path(); c.fill()
        c.set_source_rgba(*GOLD, 0.9 * ka); c.set_line_width(10); c.move_to(X, y0); c.line_to(X, yy); c.stroke()
        text(c, f"{int(round(m / 10) * 10):,} M", X + 60, yy, 72, GOLD, ka, align="l", ow=0.15)
        if m > EVEREST:
            text(c, "HIGHER THAN EVEREST", 540, 1450 - 0 * ka, 50, INK, ka * seg(t, T["trapped"], T["trapped"] + 0.2), ow=0.16) if False else None
            chip(c, t, T["trapped"] + 0.25, "HIGHER THAN EVEREST", 540, 610, GOLD, mark=None, w=640, size=44)
    if t >= T["survived"] - 0.15:
        k = popin(t, T["survived"] - 0.15, 0.25) * (1 - seg(t, T["world"] - 0.25, T["world"]))
        if k > 0:
            c.set_source_rgba(0.15, 0.7, 0.3, 1); c.arc(540, 760, 120 * k, 0, 2 * math.pi); c.fill()
            check(c, 552, 748, 150 * k, INK, 1, seg(t, T["survived"], T["survived"] + 0.3))
            text(c, "SHE SURVIVED", 540, 1000, 120, LIME, 1, ow=0.13, scale=k)
    if t >= T["world"] - 0.2:   # troféu do recorde mundial
        k = popin(t, T["world"] - 0.2, 0.3)
        glow(c, 540, 900, 520, GOLD, 0.45 * min(1, k))
        for i in range(10):
            an = i * math.pi / 5 + t * 0.6
            sparkle(c, 540 + 340 * math.cos(an), 900 + 300 * math.sin(an), 22, GOLD, 0.8 * min(1, k))
        c.save(); c.translate(540, 900); c.scale(k, k)
        c.set_source_rgb(1.0, 0.78, 0.2)
        c.move_to(-150, -230); c.line_to(150, -230); c.curve_to(150, -40, 80, 30, 0, 40); c.curve_to(-80, 30, -150, -40, -150, -230); c.fill()
        c.set_line_width(26); c.arc(-150, -150, 70, math.pi * 0.5, math.pi * 1.5); c.stroke(); c.arc(150, -150, 70, -math.pi * 0.5, math.pi * 0.5); c.stroke()
        c.rectangle(-28, 30, 56, 100); c.fill(); rr(c, -120, 120, 240, 60, 14); c.fill()
        c.set_source_rgb(0.75, 0.5, 0.08); rr(c, -150, 180, 300, 70, 14); c.fill()
        c.set_source_rgba(1, 1, 1, 0.45); c.move_to(-100, -210); c.curve_to(-100, -100, -70, -40, -30, -10); c.set_line_width(14); c.stroke()
        c.restore()
        text(c, "10,160 M", 540, 760 + 0 * k, 54, DARK, min(1, k), outline=False, scale=k) if False else None
        text(c, "WORLD RECORD", 540, 1260, 112, GOLD, 1, ow=0.13, scale=popin(t, T["world"] - 0.05, 0.28))
        text(c, "HIGHEST FALL SURVIVED · 10,160 M", 540, 1370, 40, INK, 1, ow=0.16, scale=popin(t, T["world"] + 0.15, 0.25))
    vignette(c, 0.35)


# ---------- final: de volta ao avião, lista de verificação, loop para o frame 0 ----------
def s_end(c, t):
    """'So next time…': de volta ao avião com a lista; em '…if you…' a câmara volta continuamente à do frame 0."""
    u = t - T["so"]; TR0 = T["ifyou"]
    if t >= T_END - 1.5 / FPS:   # último frame = frame 0
        s_hook(c, 0.0); return
    D = T_END - 1 / FPS - TR0
    e = smooth(clamp((t - TR0) / D))
    z0, r0, sx0, sy0, _ = cam1(0.0)
    zc = 1.0 + 0.04 * min(u, TR0 - T["so"])
    z = lerp(zc, z0, e); rot = lerp(0.02 * math.sin(t * 5), r0, e); sx = lerp(0, sx0, e); sy = lerp(0, sy0, e)
    c.save(); c.translate(W / 2 + sx, H / 2 + sy); c.rotate(rot); c.translate(-W / 2, -H / 2)
    draw_par(c, "s1_queda_aviao", z, 0.5, lerp(0.40, 0.44, e), px=lerp(10 * math.sin(u * 2), 0, e), py=lerp(40, 20, e), push=lerp(0.05, 0, e))
    c.restore()
    wind_lines(c, t, 0.55, 0.8)
    c.set_source_rgba(0.02, 0.04, 0.12, 0.25 * (1 - e)); c.paint()
    k = popin(t, T["so"] + 0.1, 0.3) * (1 - seg(t, TR0 - 0.05, TR0 + 0.25))
    if k > 0.01:
        c.save(); c.translate(540, 850); c.rotate(-0.03); c.scale(k, k)
        c.set_source_rgba(0.04, 0.07, 0.18, 0.92); rr(c, -380, -250, 760, 500, 40); c.fill()
        c.set_source_rgba(*GOLD, 1); c.set_line_width(6); rr(c, -380, -250, 760, 500, 40); c.stroke()
        text(c, "FALL PLAN", 0, -180, 64, GOLD, 1, outline=False)
        items = [("STARFISH POSE", T["exactly"] - 0.15), ("SKIP THE WATER", T["what"] - 0.05), ("AIM FOR SNOW", T["do"] - 0.05)]
        for i, (s_, t0) in enumerate(items):
            yy = -60 + i * 110
            c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(5); rr(c, -340, yy - 32, 64, 64, 12); c.stroke()
            if t >= t0: check(c, -304, yy - 4, 64, LIME, 1, seg(t, t0, t0 + 0.2))
            text(c, s_, -240, yy, 54, INK if t >= t0 else (0.75, 0.78, 0.85), 1, align="l", outline=False)
        c.restore()
    if e > 0:   # o cronómetro volta a 3:00 (como no frame 0)
        c.save(); c.set_source_rgba(0.02, 0.04, 0.12, 0.72 * e); rr(c, 300, 225, 480, 150, 34); c.fill()
        c.set_source_rgba(*RED, 0.9 * e); c.set_line_width(5); rr(c, 300, 225, 480, 150, 34); c.stroke(); c.restore()
        text(c, timer_txt(0), 560, 300, 104, INK, e, outline=False)
    vignette(c, 0.35)


SCENES = [
    (0.0, T["first"], s_hook), (T["first"], T["now"], s_altitude), (T["now"], T["water"], s_star),
    (T["water"], T["sounds"] + 0.45, s_menu), (T["sounds"] + 0.45, T["brand"], s_pilot), (T["brand"], T["and72"], s_brand),
    (T["and72"], T["so"], s_record), (T["so"], 99, s_end),
]
NO_PUNCH = {s_brand, s_end}
SUB_T0 = T["and72"] + 0.05          # pop-up logo a seguir a "That one made me scratch my head", no topo (fora do essencial)


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
    """pop-up de subscrição (baseado em lib/subscribe_popup.py, cores do céu)"""
    u = t - SUB_T0
    if u < 0 or u > 2.6: return
    inn = seg(u, 0, 0.35); out = seg(u, 2.2, 2.55); a = inn * (1 - out)
    done = u > 1.0
    w, h = 660, 104; x = (W - w) / 2; y = 330 - 40 * (1 - inn) - 30 * out
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
    # vento contínuo do princípio ao fim, com volume e brilho a seguir a velocidade da queda
    n = int(T_END * SR); tt = np.arange(n) / SR
    rng = np.random.default_rng(9)
    def band(lo, hi):
        X = np.fft.rfft(rng.standard_normal(n)); fq = np.fft.rfftfreq(n, 1 / SR); X[(fq < lo) | (fq > hi)] = 0
        y = np.fft.irfft(X, n); return y / np.abs(y).max()
    low, high = band(70, 700), band(700, 2600)
    key = [(0, 0.55), (T["first"], 0.5), (T["pass_"], 0.5), (T["pass_"] + 0.4, 0.25), (T["wake"], 0.25), (T["wake"] + 0.3, 0.75),
           (T["now"], 0.8), (T["n200"] + 0.3, 1.0), (T["water"] - 0.2, 0.95), (T["water"] + 0.2, 0.45), (T["sounds"], 0.4),
           (T["sounds"] + 0.45, 0.08), (T["and72"], 0.08), (T["so"] - 0.1, 0.1), (T["so"] + 0.3, 0.45), (T_END, 0.55)]
    g = np.interp(tt, [k[0] for k in key], [k[1] for k in key])
    gust = 0.8 + 0.2 * np.sin(2 * np.pi * 0.6 * tt) * np.sin(2 * np.pi * 0.23 * tt + 1)
    wind = (low * 0.8 + high * 0.35 * g) * g * gust
    wind[:int(0.03 * SR)] *= np.linspace(0, 1, int(0.03 * SR)) * 0 + 1   # sem fade: o loop liga o fim ao início
    wind_p = wav("wind", wind / np.abs(wind).max() * 0.6)
    E = [(wind_p, 0.0, 0.32), (a("scratch_head"), T["brand"], 0.6)]
    E += [(swish, x - 0.12, 0.16) for x in (T["now"], T["water"], T["sounds"] + 0.45, T["and72"])]
    E += [(ding, x, 0.13) for x in (T["best"], T["concrete"] + 0.1, T["soft"] + 0.05)]   # piadas (pedido do guião), baixo
    E += [(pop, T["n200"] - 0.05, 0.18), (pop, T["n1944"] - 0.05, 0.16), (pop, SUB_T0 + 1.0, 0.16)]
    E += [(boom, T["world"] - 0.2, 0.32), (shimmer, T["world"] - 0.15, 0.22)]
    ins, ch, lab = [], [], []
    for f_, x, v in E:
        i = 3 + len(lab); ins += ["-i", f_]; d = int(max(0, x) * 1000)
        ch.append(f"[{i}:a]adelay={d}|{d},volume={v}[e{len(lab)}]"); lab.append(f"[e{len(lab)}]")
    sfx = ";".join(ch) + ";" + "".join(lab) + f"amix=inputs={len(lab)}:normalize=0[sfx]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw_video, "-i", NARR, "-stream_loop", "-1", "-i", MUSIC, *ins,
                    "-filter_complex",
                    f"[0:v]subtitles={ASS},format=yuv420p[v];"
                    "[1:a]asplit=2[n1][nk];"
                    f"[2:a]atrim=0:{T_END:.3f},volume=0.2[m];"
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
