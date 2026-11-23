#!/usr/bin/env python3
"""Whatifaholic EP007 — What If Earth Had Rings Like Saturn?
Estilo do canal: ilustração plana em camadas (4 imagens nano_banana_pro) + animação por código (pycairo).
Câmara sempre em movimento (zoom/pan lentos + partículas em primeiro plano a velocidades diferentes = parallax).
Loop de frase: "Which means, one day…" → "Look up." (último frame = frame 0).
Uso: python3 anim_ep007.py [--frames t1,t2,...|last]   (sem argumentos: render completo + mistura)"""
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
OUT = f"{ROOT}/whatifaholic_ep007_rings.mp4"
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", NARR]))
N_FR = int(round(DUR * FPS))
T_END = N_FR / FPS
random.seed(7)

# ---------- cores (sem paleta fixa: as do tema — anéis prateados/dourados, céus de cada cena) ----------
INK = (1, 1, 1); DARK = (0.04, 0.03, 0.08); GOLD = (1.0, 0.82, 0.36); SILVER = (0.88, 0.92, 1.0)
ICE = (0.7, 0.9, 1.0); ORANGE = (1.0, 0.55, 0.2); RED = (1.0, 0.32, 0.25); VIOLET = (0.42, 0.3, 0.75)
GREY = (0.6, 0.62, 0.68)

# ---------- palavras ----------
words = json.load(open(f"{BLD}/words.json"))
FIX = {"up,": "up.", "now,": "now.", "and": "And", "equator": "equator,", "line": "line,", "days,": "days.",
       "longer": "Longer", "rings": "rings", "ago,": "ago.", "which": "Which"}
for i, w in enumerate(words):
    t = w["w"]
    if t == "and": t = "And" if i == 6 else "and"
    elif t == "rings" and i + 1 < len(words) and words[i + 1]["w"] == "around": t = "rings…"
    elif t in FIX: t = FIX[t]
    w["w"] = t.replace("...", "…")
if words[-1]["e"] > T_END: words[-1]["e"] = T_END


def bare(w): return re.sub(r"[^\w']", "", w).lower()


def at(tok, n=1, key="s"):
    k = 0
    for w in words:
        if bare(w["w"]) == tok:
            k += 1
            if k == n: return w[key]
    raise KeyError(tok)


T = dict(earth=at("earth"), every=at("everywhere"), frm=at("from"), europe=at("europe"), arch=at("arch"),
         brand=at("that") - 0.08, night=at("at") - 0.12, bright=at("bright"), dark=at("dark"),
         stand=at("stand") - 0.12, thin=at("thin"), above=at("above"), inw=at("in") - 0.12, shadow=at("shadow"),
         half=at("half"), colder=at("colder"), longer=at("longer"), every2=at("every") - 0.12, sunset=at("sunset"),
         ice=at("ice"), but=at("but") - 0.1, wait=at("wait"), strangest=at("strangest"), scientists=at("scientists") - 0.1,
         really=at("really"), shrink=at("shrink"), eqimg=at("thin") - 0.35, sky=at("sky", 3) - 0.15, rings2=at("rings", 3), n466=at("466"), ago=at("ago"), which=at("which") - 0.08, day=at("day"))


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


# ---------- imagens em camadas (parallax 2.5D a partir de mapas de profundidade) ----------
# Cada ilustração é cortada em 4 camadas pela profundidade (build/depth.py, Depth Anything V2 Small).
# As camadas de trás têm os objetos da frente "apagados" (preenchimento pull-push), para que, quando a
# camada da frente se mexe mais do que a de trás, não apareçam duplicados.
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


NAMES = ("city", "europe", "night", "bedroom", "equator", "winter", "sunset", "ordovician")
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


def chat(c, t, t0, x, y):
    """chat de família a encher-se de fotos do pôr do sol"""
    msgs = [("MOM", "sunset pic #1"), ("DAD", "sunset pic #2"), ("AUNT", "SUNSET!!! (4 pics)"), ("MOM", "did you see it??")]
    for i, (who, txt) in enumerate(msgs):
        tt = t0 + i * 0.32
        if t < tt: break
        k = popin(t, tt, 0.2)
        yy = y + i * 118
        c.save(); c.translate(x, yy); c.scale(k, k)
        c.set_source_rgba(1, 1, 1, 0.95); rr(c, 0, 0, 470, 96, 30); c.fill()
        c.set_source_rgba(*ORANGE, 1); c.rectangle(18, 18, 60, 60); c.fill()           # miniatura da foto
        c.set_source_rgba(1, 0.85, 0.3, 1); c.arc(48, 56, 16, math.pi, 2 * math.pi); c.fill()
        text(c, who, 96, 30, 26, (0.85, 0.35, 0.15), 1, align="l", outline=False)
        text(c, txt, 96, 66, 30, (0.12, 0.12, 0.16), 1, align="l", outline=False)
        c.restore()
    if t >= t0:
        text(c, "FAMILY CHAT", x + 235, y - 50, 40, INK, popin(t, t0, 0.2), ow=0.16)


# ---------- globo (código) ----------
CONT_TODAY = [  # contornos simplificados (lon, lat) para a Terra de hoje (Europa/África/Américas)
    [(-10, 36), (-9, 43), (-2, 44), (-5, 48), (2, 51), (8, 54), (10, 58), (5, 62), (14, 67), (25, 71), (40, 68), (45, 55),
     (40, 45), (28, 41), (26, 36), (15, 38), (12, 44), (5, 43), (-2, 37)],
    [(-17, 15), (-16, 28), (-6, 36), (10, 37), (25, 32), (34, 31), (43, 12), (51, 12), (40, -5), (40, -16), (33, -26),
     (20, -35), (14, -24), (12, -6), (8, 4), (-8, 5), (-14, 10)],
    [(-80, 9), (-77, -2), (-81, -6), (-70, -18), (-72, -40), (-66, -55), (-58, -38), (-48, -27), (-39, -14), (-35, -6),
     (-50, 0), (-60, 9), (-72, 12)],
    [(-125, 48), (-123, 38), (-110, 23), (-97, 19), (-88, 15), (-80, 9), (-82, 25), (-80, 32), (-70, 42), (-60, 47),
     (-55, 52), (-64, 60), (-80, 63), (-95, 70), (-130, 70), (-165, 66), (-150, 59), (-135, 57)],
    [(-50, 60), (-42, 60), (-20, 70), (-25, 82), (-55, 82), (-70, 76), (-60, 68)],
]
CONT_OLD = [  # Ordovícico (~466 Ma): Gondwana a sul, Laurência e Báltica no equador (formas estilizadas)
    [(-60, -10), (-30, 5), (10, 0), (40, -10), (70, -25), (80, -45), (50, -70), (0, -80), (-50, -70), (-75, -45)],
    [(-120, 20), (-95, 25), (-80, 10), (-90, -10), (-115, -12), (-130, 2)],
    [(-40, 30), (-20, 38), (-8, 28), (-18, 15), (-38, 16)],
    [(100, 15), (118, 20), (125, 5), (110, -5), (98, 2)],
]


def globe(c, cx, cy, R, rot, t, land=(0.42, 0.72, 0.42), sea1=(0.16, 0.5, 0.86), sea2=(0.05, 0.2, 0.5),
          conts=CONT_TODAY, tilt=0.41, sun=(-1, -0.25), ring=1.0, ring_col=(0.92, 0.94, 1.0), shadow=0.0,
          ring_tilt=0.0, a=1.0, glowc=(0.45, 0.75, 1.0), ice_caps=True):
    # halo
    glow(c, cx, cy, R * 1.25, glowc, 0.35 * a, r0=R * 0.9)
    def ring_half(front):
        if ring <= 0: return
        c.save(); c.translate(cx, cy); c.rotate(ring_tilt); c.scale(1, 0.2)
        for r0, r1, al in ((1.35, 1.55, 0.55), (1.58, 1.95, 0.85), (2.0, 2.12, 0.45), (2.16, 2.35, 0.65)):
            c.new_path()
            if front: c.arc(0, 0, R * r1, 0, math.pi); c.arc_negative(0, 0, R * r0, math.pi, 0)
            else: c.arc(0, 0, R * r1, math.pi, 2 * math.pi); c.arc_negative(0, 0, R * r0, 2 * math.pi, math.pi)
            c.close_path()
            c.set_source_rgba(*ring_col, al * ring * a); c.fill()
        c.restore()
    ring_half(False)
    # esfera
    c.save(); c.arc(cx, cy, R, 0, 2 * math.pi); c.clip()
    g = cairo.RadialGradient(cx - R * 0.35, cy - R * 0.4, R * 0.1, cx, cy, R * 1.05)
    g.add_color_stop_rgba(0, *sea1, a); g.add_color_stop_rgba(1, *sea2, a)
    c.set_source(g); c.paint()
    # continentes (projeção ortográfica com eixo inclinado)
    ct, st = math.cos(tilt), math.sin(tilt)
    def proj(lon, lat):
        lo = math.radians(lon) + rot; la = math.radians(lat)
        x = math.cos(la) * math.sin(lo); y = -math.sin(la); z = math.cos(la) * math.cos(lo)
        y2 = y * ct - z * st * 0.35; z2 = z
        return cx + R * x, cy + R * y2, z2
    for poly in conts:
        pts = []
        for i in range(len(poly)):
            (l0, b0), (l1, b1) = poly[i], poly[(i + 1) % len(poly)]
            for k in range(6):
                pts.append(proj(l0 + (l1 - l0) * k / 6, b0 + (b1 - b0) * k / 6))
        vis = [p for p in pts if p[2] > -0.05]
        if len(vis) < 3: continue
        c.new_path()
        for i, p in enumerate(pts):
            x, y, z = p
            if z < 0:  # empurra pontos escondidos para a borda
                d = math.hypot(x - cx, y - cy) or 1; x = cx + (x - cx) / d * R; y = cy + (y - cy) / d * R
            (c.move_to if i == 0 else c.line_to)(x, y)
        c.close_path(); c.set_source_rgba(*land, a); c.fill()
    if ice_caps:
        c.set_source_rgba(0.95, 0.97, 1, 0.9 * a); c.arc(cx, cy - R * 1.02, R * 0.32, 0, 2 * math.pi); c.fill()
        c.arc(cx, cy + R * 1.04, R * 0.3, 0, 2 * math.pi); c.fill()
    # sombra dos anéis sobre metade do planeta (inverno)
    if shadow > 0:
        c.save(); c.translate(cx, cy); c.rotate(-0.18)
        sh = cairo.LinearGradient(0, -R, 0, R * 0.05)
        sh.add_color_stop_rgba(0, 0.02, 0.03, 0.12, 0.85 * shadow * a); sh.add_color_stop_rgba(0.75, 0.02, 0.03, 0.12, 0.75 * shadow * a)
        sh.add_color_stop_rgba(1, 0.02, 0.03, 0.12, 0)
        c.set_source(sh); c.rectangle(-R * 1.2, -R * 1.2, R * 2.4, R * 1.25); c.fill()
        for k in range(5):  # riscas da sombra (as bandas dos anéis)
            yy = -R * 0.85 + k * R * 0.17
            c.set_source_rgba(0, 0, 0.05, 0.22 * shadow * a); c.rectangle(-R * 1.2, yy, R * 2.4, R * 0.06); c.fill()
        c.restore()
    # luz do sol (terminador)
    sx, sy = sun
    lg = cairo.LinearGradient(cx + sx * R, cy + sy * R, cx - sx * R, cy - sy * R)
    lg.add_color_stop_rgba(0, 1, 1, 1, 0.12 * a); lg.add_color_stop_rgba(0.55, 0, 0, 0, 0); lg.add_color_stop_rgba(1, 0, 0, 0.05, 0.55 * a)
    c.set_source(lg); c.paint()
    c.restore()
    ring_half(True)


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


def cam_hook(t):
    """câmara do gancho: 'Look up' (sobe da rua para o arco); t<0 = estado do frame 0"""
    up = smooth(t / 1.6)
    return 1.10 + 0.05 * smooth((t - 0.4) / 2.0), 0.5, lerp(0.56, 0.38, up)


def s_hook(c, t):
    z, fx, fy = cam_hook(t)
    up = smooth(t / 1.6)
    draw_par(c, "city", z, fx, fy, px=0, py=lerp(-30, 60, up), push=0.05 * smooth(t / 2.3))
    for k in range(3):
        p = ((t * 0.35 + k / 3) % 1.0)
        glow(c, lerp(150, 1150, p), lerp(1350, -150, p), 170, (1, 0.95, 0.8), 0.22)
    particles(c, t, (1, 0.95, 0.85), 0.55, vx=-10, vy=-6, size=0.8)
    k = popin(t, T["earth"] - 0.05, 0.25)
    text(c, "EARTH HAS RINGS", 540, 300, 96, INK, 1, ow=0.14, scale=k)
    vignette(c, 0.35)


def s_everywhere(c, t):
    """'And they're everywhere': corte para o espaço, a câmara afasta-se depressa da Terra com anéis"""
    u = t - T["every"] + 0.25; d = T["frm"] - T["every"] + 0.25
    space_bg(c, t)
    R = lerp(620, 250, ease(u / d))
    globe(c, 540, 860, R, 1.2 + u * 0.9, t, ring=1.0, ring_tilt=-0.22 + 0.1 * u, sun=(-1, -0.3))
    text(c, "EVERYWHERE", 540, 300, 100, GOLD, 1, scale=popin(t, T["every"]), ow=0.14)


def s_europe_map(c, t):
    """esquema: o globo roda até à Europa; linhas de visão do pin até ao anel = o arco que se vê"""
    u = t - T["frm"]; d = T["arch"] - 0.35 - T["frm"]
    space_bg(c, t)
    rot = lerp(1.4, -0.17, smooth(u / (d * 0.7)))
    cx, cy, R = 540, 900, 330
    globe(c, cx, cy, R, rot, t, ring=1.0, ring_tilt=0.0, sun=(-1, -0.3))
    px, py, z = proj_pt(cx, cy, R, rot, 10, 47)
    k = popin(t, T["europe"] - 0.05, 0.25) if z > 0 else 0
    if k > 0:
        # ponto do anel visto da Europa: arco frontal do anel (a sul), realçado
        a = seg(u, 0.55, 0.9)
        c.save(); c.translate(cx, cy); c.scale(1, 0.2)
        c.set_source_rgba(1, 0.95, 0.6, 0.85 * a); c.set_line_width(28)
        c.arc(0, 0, R * 1.75, math.pi * 0.18, math.pi * 0.82); c.stroke(); c.restore()
        for ang in (0.18, 0.5, 0.82):
            rx, ry = cx + R * 1.75 * math.cos(math.pi * ang), cy + R * 1.75 * 0.2 * math.sin(math.pi * ang)
            dashed(c, px, py - 46, rx, ry, (1, 0.95, 0.6), 0.9 * a, off=-t * 60)
        pin(c, px, py, k)
        text(c, "EUROPE", px, py - 120, 64, INK, 1, scale=k, ow=0.16)
        text(c, "YOU SEE THIS PART", 540, 1230, 54, GOLD, a, ow=0.16)


def s_europe(c, t):
    u = t - T["arch"] + 0.35; d = T["brand"] - T["arch"] + 0.35
    p = smooth(u / d)
    draw_par(c, "europe", 1.06 + 0.06 * p, 0.5, 0.42 - 0.06 * p, px=lerp(40, -40, p), py=lerp(0, 30, p), push=0.08 * p)
    for k in range(3):
        q = ((t * 0.3 + k / 3) % 1.0)
        glow(c, lerp(120, 1180, q), lerp(1250, -100, q) + 0 * k, 150, (1, 0.95, 0.85), 0.2)
    particles(c, t, (1, 0.93, 0.8), 0.45, vx=-8, vy=-4, size=0.7)
    text(c, "HORIZON TO HORIZON", 540, 300, 74, INK, 1, scale=popin(t, T["arch"] + 0.9), ow=0.15)
    vignette(c, 0.3)


def s_brand(c, t):
    u = t - T["brand"]
    draw_par(c, "europe", 1.12 + 0.02 * u, 0.5, 0.36, px=-40 - 20 * u, py=30, push=0.08)
    c.set_source_rgba(0.05, 0.03, 0.12, 0.62); c.paint()
    draw_scratch(c, u, 540, 760, scale=0.95, skin=(1.0, 0.8, 0.62), accent=GOLD, ink=INK, hair=(0.2, 0.13, 0.1))


def s_night(c, t):
    u = t - T["night"]; d = T["bright"] - T["night"]
    p = smooth(u / d)
    draw_par(c, "night", 1.12 - 0.06 * p, 0.5, 0.45, px=lerp(-50, 50, p), py=0, push=0.06 * p)
    glow(c, 640, 520, 700, (0.85, 0.95, 1), 0.18 + 0.06 * math.sin(t * 2.4))
    particles(c, t, SILVER, 0.5, vx=-14, vy=4, size=0.7)
    a = seg(u, 0.3, 0.6)
    x0, y0 = 260, 300
    c.set_source_rgba(0.05, 0.06, 0.15, 0.8 * a); rr(c, x0, y0, 560, 92, 46); c.fill()
    text(c, "DARKNESS", x0 + 40, y0 + 46, 34, SILVER, a, align="l", outline=False)
    lv = 0.06 + 0.04 * math.sin(t * 9)
    c.set_source_rgba(0.2, 0.22, 0.35, a); rr(c, x0 + 240, y0 + 30, 280, 32, 16); c.fill()
    c.set_source_rgba(*ICE, a); rr(c, x0 + 240, y0 + 30, 280 * lv * 3, 32, 16); c.fill()
    text(c, "0%", x0 + 590, y0 + 46, 40, INK, a, align="l") if False else None
    vignette(c, 0.35)


def s_bedroom(c, t):
    u = t - T["bright"]; d = T["stand"] - T["bright"]
    p = smooth(u / d)
    draw_par(c, "bedroom", 1.05 + 0.1 * p, 0.55, 0.55, px=lerp(30, -30, p), py=lerp(-20, 20, p), push=0.1 * p)
    # a janela pisca de luz (o céu nunca escurece)
    glow(c, 420, 520, 520, (0.92, 0.96, 1), 0.2 + 0.08 * math.sin(t * 5))
    card(c, t, T["bright"] + 0.7, [("SLEEP SCHEDULE:", INK), ("CANCELLED", RED)], 120, 300, 560, RED, t1=T["stand"] - 0.05)
    vignette(c, 0.4)


def s_cross(c, t):
    """esquema em corte: a Terra de lado, o anel no plano do equador. O observador desce da Europa (45°N)
    até ao equador: a fatia de anel que vê passa de um arco largo a uma linha fina por cima da cabeça."""
    u = t - T["stand"]
    space_bg(c, t, top=(0.02, 0.05, 0.12), bot=(0.0, 0.01, 0.04))
    cx, cy, R = 360, 940, 250
    lat = lerp(45, 0, smooth((t - T["stand"] - 0.3) / (T["shrink"] - T["stand"])))
    # anel de perfil (dos dois lados)
    for sgn in (1, -1):
        x0, x1 = cx + sgn * R * 1.4, cx + sgn * R * 2.6
        c.set_source_rgba(*SILVER, 0.95); c.set_line_width(14); c.move_to(x0, cy); c.line_to(x1, cy); c.stroke()
    # planeta
    g = cairo.RadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.1, cx, cy, R)
    g.add_color_stop_rgb(0, 0.2, 0.55, 0.9); g.add_color_stop_rgb(1, 0.05, 0.2, 0.5)
    c.set_source(g); c.arc(cx, cy, R, 0, 2 * math.pi); c.fill()
    dashed(c, cx - R * 1.1, cy, cx + R * 1.1, cy, (1, 1, 1), 0.35, w=3)
    text(c, "EQUATOR", cx - R * 0.55, cy + 30, 30, INK, 0.7, outline=False)
    # observador
    la = math.radians(lat)
    ox, oy = cx + R * math.cos(la), cy - R * math.sin(la)
    nx, ny = math.cos(la), -math.sin(la)
    # fatia do anel que vê (cunha de visão até às duas pontas do anel do seu lado)
    ex0, ex1 = cx + R * 1.4, cx + R * 2.6
    c.set_source_rgba(1, 0.85, 0.35, 0.28); c.move_to(ox, oy); c.line_to(ex0, cy); c.line_to(ex1, cy); c.close_path(); c.fill()
    for ex in (ex0, ex1): dashed(c, ox, oy, ex, cy, GOLD, 0.95, w=4, off=-t * 50)
    # boneco
    c.save(); c.translate(ox, oy); c.rotate(math.atan2(ny, nx) + math.pi / 2)
    c.set_source_rgba(*RED, 1); c.set_line_width(8); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(0, 0); c.line_to(0, -44); c.stroke(); c.arc(0, -58, 13, 0, 2 * math.pi); c.fill(); c.restore()
    text(c, f"{int(round(lat))}°N" if lat > 0.5 else "0°", ox + nx * 110 - 10, oy + ny * 110 - 10, 46, INK, 1, ow=0.16)
    # o que vê: ícone do céu (arco → linha)
    k = clamp(lat / 45)
    bx, by = 540, 380
    c.set_source_rgba(0.1, 0.2, 0.4, 0.85); rr(c, bx - 240, by - 150, 480, 260, 40); c.fill()
    c.set_source_rgba(*SILVER, 1); c.set_line_width(lerp(6, 34, k))
    if k > 0.05:
        c.save(); c.translate(bx, by + 90); c.scale(1, max(0.05, k))
        c.arc(0, 0, 190, math.pi * 1.05, math.pi * 1.95); c.restore(); c.stroke()
    else:
        c.move_to(bx, by + 100); c.line_to(bx, by - 140); c.stroke()
    c.set_source_rgba(0.35, 0.6, 0.35, 1); c.rectangle(bx - 240, by + 70, 480, 40); c.fill()
    text(c, "ARCH" if k > 0.35 else ("THIN LINE" if k < 0.08 else "…"), bx, by - 190, 56, GOLD, 1, ow=0.16)


def s_equator(c, t):
    u = t - T["eqimg"]; d = T["inw"] - T["eqimg"]
    p = smooth(u / d)
    fy = 0.55 - 0.2 * p
    base, x0, y0 = draw_par(c, "equator", 1.06 + 0.06 * p, 0.5, fy, px=lerp(20, -20, p), py=lerp(-40, 40, p), push=0.06 * p)
    lx = (768 - x0) * base
    a = 0.8
    c.set_source_rgba(1, 1, 1, 0.6 * a); c.set_line_width(4); c.move_to(lx, -10); c.line_to(lx, (2190 - y0) * base); c.stroke()
    for k in range(2):
        q = (t * 0.6 + k / 2) % 1
        glow(c, lx, lerp((2190 - y0) * base, -50, q), 60, (1, 1, 1), 0.55 * a)
    particles(c, t, (1, 1, 1), 0.35, vx=-12, vy=0, size=0.6)
    k = popin(t, T["eqimg"] + 0.15, 0.25)
    text(c, "STRAIGHT ABOVE YOU", 540, 300, 70, INK, 1, scale=k, ow=0.16)
    card(c, t, T["above"] - 0.1, [("EQUATOR PEOPLE:", INK), ("\"WHAT RINGS?\"", GOLD)], 90, 820, 560, GOLD,
         bg=(0.02, 0.25, 0.4), t1=T["inw"] - 0.05, rot=0.03)
    vignette(c, 0.25)


def s_season(c, t):
    """esquema: o Sol à esquerda, raios; no inverno do norte o anel tapa o Sol a metade do planeta"""
    u = t - T["inw"]
    space_bg(c, t)
    glow(c, -60, 820, 520, (1, 0.85, 0.4), 0.85, r0=60)
    c.set_source_rgba(1, 0.9, 0.5, 1); c.arc(-60, 820, 150, 0, 2 * math.pi); c.fill()
    text(c, "SUN", 70, 560, 50, GOLD, 1, ow=0.16)
    cx, cy, R = 660, 820, 250
    sh = seg(t, T["shadow"], T["shadow"] + 0.8)
    # raios
    for i in range(9):
        y = cy - R * 1.1 + i * R * 0.28
        blocked = y < cy - R * 0.05 and sh > 0
        xend = cx - R * 1.35 if blocked else cx - R * math.sqrt(max(0, 1 - ((y - cy) / R) ** 2))
        off = (t * 300 + i * 40) % 80
        c.save(); c.set_source_rgba(1, 0.9, 0.5, 0.75); c.set_line_width(5); c.set_dash([40, 40], -off)
        c.move_to(110, y); c.line_to(xend, y); c.stroke(); c.restore()
        if blocked:
            c.set_source_rgba(1, 0.9, 0.5, 0.9 * sh); c.arc(xend, y, 9, 0, 2 * math.pi); c.fill()
    globe(c, cx, cy, R, -0.3 + u * 0.15, t, shadow=sh, ring=1.0, ring_tilt=-0.35, sun=(-1, 0.0))
    text(c, "RING SHADOW", cx, cy - R - 120, 58, ICE, sh, ow=0.16)
    text(c, "WINTER", 540, 300, 96, ICE, 1, scale=popin(t, T["inw"] + 0.1), ow=0.14)


def s_you(c, t):
    u = t - T["half"] + 0.3
    space_bg(c, t)
    R = 380 + 30 * u
    rot = -0.17 + 0.05 * u
    globe(c, 540, 880, R, rot, t, shadow=1.0, ring=1.0, ring_tilt=-0.18, sun=(-1, 0.05))
    px, py, z = proj_pt(540, 880, R, rot, 10, 47)
    k = popin(t, T["half"] - 0.1, 0.25)
    pin(c, px, py, k)
    text(c, "YOU", px, py - 130, 64, INK, 1, scale=k, ow=0.16)


def s_winterimg(c, t):
    u = t - T["colder"] + 0.05; d = T["every2"] - T["colder"] + 0.05
    p = smooth(u / d)
    draw_par(c, "winter", 1.06 + 0.08 * p, 0.5, 0.5, px=lerp(-30, 30, p), py=0, push=0.1 * p)
    # sombra dos anéis: riscas diagonais escuras a deslizar
    c.save(); c.rotate(-0.35)
    for i in range(-3, 9):
        y = i * 300 + (t * 25) % 300
        c.set_source_rgba(0.05, 0.06, 0.18, 0.3); c.rectangle(-600, y, 2600, 120); c.fill()
    c.restore()
    particles(c, t, (0.95, 0.97, 1), 0.85, vx=-6, vy=30, size=0.9)
    text(c, "COLDER DAYS", 540, 300, 84, ICE, 1, scale=popin(t, T["colder"] - 0.05), ow=0.15)
    text(c, "LONGER NIGHTS", 540, 405, 84, (0.8, 0.75, 1.0), 1, scale=popin(t, T["longer"] - 0.05), ow=0.15)
    card(c, t, T["longer"] + 0.2, [("HEATING BILL:", INK), ("x3", RED)], 560, 560, 420, RED, rot=0.04)
    vignette(c, 0.35)


def s_sunset(c, t):
    u = t - T["every2"]; d = T["sky"] - T["every2"]
    p = smooth(u / d)
    draw_par(c, "sunset", 1.06 + 0.06 * p, 0.45, 0.45, px=lerp(-40, 30, p), py=0, push=0.06 * p)
    particles(c, t, (1, 0.9, 0.6), 0.75, vx=-16, vy=-8, size=0.9)
    glow(c, 820, 900, 300, (1, 0.6, 0.3), 0.18 + 0.05 * math.sin(t * 3))
    chat(c, t, T["sunset"] + 0.15, 90, 640)
    vignette(c, 0.3)


def hexa(c, x, y, r, rot, col, a):
    c.save(); c.translate(x, y); c.rotate(rot); c.set_source_rgba(*col, a); c.set_line_width(max(2, r * 0.12))
    for i in range(6):
        ang = i * math.pi / 3
        c.move_to(0, 0); c.line_to(r * math.cos(ang), r * math.sin(ang))
        for s in (0.5,):
            bx, by = r * s * math.cos(ang), r * s * math.sin(ang)
            c.move_to(bx, by); c.line_to(bx + r * 0.25 * math.cos(ang + 0.8), by + r * 0.25 * math.sin(ang + 0.8))
            c.move_to(bx, by); c.line_to(bx + r * 0.25 * math.cos(ang - 0.8), by + r * 0.25 * math.sin(ang - 0.8))
    c.stroke(); c.restore()


def s_ice(c, t):
    """grande plano dos anéis ao pôr do sol: são feitos de gelo"""
    u = t - T["sky"]; d = T["but"] - T["sky"]
    p = smooth(u / d)
    draw_par(c, "sunset", 2.1 + 0.3 * p, 0.72, 0.2, px=lerp(30, -30, p), py=0, push=0.1 * p)
    rnd = random.Random(4)
    for i in range(14):
        x = rnd.random() * W; y = rnd.random() * 1300 + 150; r = 30 + rnd.random() * 60
        k = seg(t, T["ice"] - 0.6 + i * 0.04, T["ice"] - 0.3 + i * 0.04)
        hexa(c, x + 20 * math.sin(t + i), y - 30 * u, r * k, t * 0.6 + i, (0.92, 0.97, 1), 0.85 * k)
    text(c, "ICE", 540, 560, 130, ICE, 1, scale=popin(t, T["ice"] - 0.05), ow=0.12)
    vignette(c, 0.3)


def s_tease(c, t):
    """'But wait until you hear the strangest part': a Terra gira para trás e o contador de anos dispara"""
    u = t - T["but"]; d = T["scientists"] - T["but"]
    space_bg(c, t)
    globe(c, 540, 800, 300, 0.6 - u * 3.0 * (1 + u), t, ring=0.0, sun=(-1, -0.2))
    c.set_source_rgba(0, 0, 0, 0.2); c.paint()
    # contador a andar para trás (sem revelar o número)
    yr = int(2026 - (10 ** (1 + 7.5 * smooth(u / d))))
    s = f"{yr:,}" if yr > 0 else f"{-yr:,} BC"
    text(c, "REWINDING…", 540, 1185, 50, GOLD, seg(u, 0.1, 0.3), ow=0.16)
    text(c, s, 540, 1270, 76, INK, seg(u, 0.1, 0.3), ow=0.14)


def s_ordo(c, t):
    u = t - T["scientists"]; d = T["rings2"] - T["scientists"]
    p = smooth(u / d)
    draw_par(c, "ordovician", 1.06 + 0.08 * p, 0.5, lerp(0.6, 0.4, p), px=lerp(30, -30, p), py=lerp(-30, 30, p), push=0.1 * p)
    particles(c, t, (0.9, 1, 1), 0.35, vx=6, vy=-14, size=0.6)
    text(c, "IT WAS REAL", 540, 340, 100, GOLD, 1, scale=popin(t, T["really"] - 0.05), ow=0.14)
    vignette(c, 0.3)


def s_reveal(c, t):
    """Terra do Ordovícico com anel; '466 MILLION YEARS AGO'"""
    u = t - T["rings2"]
    space_bg(c, t, top=(0.06, 0.03, 0.08), bot=(0.01, 0.0, 0.02))
    ring = seg(t, T["rings2"], T["rings2"] + 0.4)
    R = 300 + 30 * smooth(u / 3)
    globe(c, 540, 740, R, 0.3 + u * 0.15, t, land=(0.62, 0.48, 0.32), sea1=(0.15, 0.48, 0.6), sea2=(0.04, 0.16, 0.25),
          conts=CONT_OLD, ring=ring, ring_col=(0.95, 0.85, 0.7), ring_tilt=0.12, glowc=(1.0, 0.7, 0.4), ice_caps=False)
    rnd = random.Random(9)
    for _ in range(60):
        ang = rnd.random() * 6.28 + t * 0.3; rr_ = R * (1.4 + rnd.random() * 0.9)
        x = 540 + math.cos(ang) * rr_; y = 740 + math.sin(ang) * rr_ * 0.2 + math.cos(ang) * rr_ * 0.12
        sparkle(c, x, y, 4 + rnd.random() * 7, (1, 0.95, 0.85), ring * (0.4 + 0.6 * abs(math.sin(t * 4 + ang))))
    text(c, "IT WAS REAL", 540, 340, 92, GOLD, 1, ow=0.14)
    if t >= T["n466"] - 0.05:
        k = popin(t, T["n466"] - 0.05, 0.3)
        text(c, "466", 540, 1130, 220, INK, 1, scale=k, ow=0.1)
        text(c, "MILLION YEARS AGO", 540, 1275, 68, GOLD, 1, scale=popin(t, T["n466"] + 0.5), ow=0.15)


def s_end(c, t):
    """'Which means, one day…': a Terra de hoje com um anel fantasma; a câmara mergulha e, nos últimos
    frames, a rua do frame 0 abre-se (último frame = frame 0, cam_hook em t negativo)."""
    u = t - T["which"]
    TR = 0.5
    tr0 = T_END - TR
    space_bg(c, t)
    zoom = 1 + 2.6 * smooth((u - 0.4) / (T_END - T["which"] - 0.4)) ** 2
    R = 300 * zoom
    ghost = 0.35 + 0.15 * math.sin(t * 8)
    globe(c, 540, 860 + R * 0.5 * (zoom - 1) / 2.6, R, 0.2 + u * 0.1, t, ring=ghost * seg(u, 0, 0.4), sun=(-1, -0.2))
    text(c, "ONE DAY…?", 540, 330, 96, INK, seg(u, 0.5, 0.8) * (1 - seg(t, tr0 - 0.1, tr0 + 0.1)), ow=0.14)
    if t >= tr0:
        k = clamp((t - tr0) / (TR - 1 / FPS))
        th = t - T_END
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cc = cairo.Context(s); s_hook(cc, th)
        sc = lerp(0.55, 1.0, ease(k))
        c.save(); c.translate(W / 2, H / 2); c.scale(sc, sc); c.translate(-W / 2, -H / 2)
        c.set_source_surface(s, 0, 0); c.paint_with_alpha(ease(k) if k < 1 else 1.0); c.restore()


SCENES = [
    (0.0, T["every"] - 0.25, s_hook), (T["every"] - 0.25, T["frm"], s_everywhere), (T["frm"], T["arch"] - 0.35, s_europe_map),
    (T["arch"] - 0.35, T["brand"], s_europe), (T["brand"], T["night"], s_brand), (T["night"], T["bright"], s_night),
    (T["bright"], T["stand"], s_bedroom), (T["stand"], T["eqimg"], s_cross), (T["eqimg"], T["inw"], s_equator),
    (T["inw"], T["half"] - 0.3, s_season), (T["half"] - 0.3, T["colder"] - 0.05, s_you),
    (T["colder"] - 0.05, T["every2"], s_winterimg), (T["every2"], T["sky"], s_sunset), (T["sky"], T["but"], s_ice),
    (T["but"], T["scientists"], s_tease), (T["scientists"], T["rings2"], s_ordo), (T["rings2"], T["which"], s_reveal),
    (T["which"], 99, s_end),
]
NO_PUNCH = {s_brand, s_end}
CHAPTERS = [T["frm"], T["night"], T["stand"], T["inw"], T["every2"], T["but"], T["scientists"]]


# ---------- sobreposições ----------
SUB_T0 = T["but"] - 2.65            # pop-up de subscrição antes de "But wait until you hear" (sobre o pôr do sol)
BADGE = (T["wait"], T["n466"])


def badge(c, t):
    a0, a1 = BADGE
    if not (a0 <= t < a1 + 0.35): return
    k = popin(t, a0, 0.25); out = seg(t, a1, a1 + 0.3); a = 1 - out
    c.save(); c.translate(540, 200); c.scale(k * (1 + 0.4 * out), k * (1 + 0.4 * out))
    c.set_source_rgba(0, 0, 0, 0.7 * a); rr(c, -350, -42, 700, 84, 42); c.fill()
    pulse = 0.6 + 0.4 * math.sin(t * 6)
    c.set_source_rgba(*GOLD, a * pulse); c.set_line_width(5); rr(c, -350, -42, 700, 84, 42); c.stroke()
    c.set_source_rgba(*GOLD, a); rr(c, -318, -12, 36, 30, 6); c.fill()
    c.set_line_width(6); c.arc(-300, -12, 12, math.pi, 2 * math.pi); c.stroke()
    c.restore()
    text(c, "THE STRANGEST PART · COMING UP", 565, 200, 36, INK, a * (k > 0), outline=False, scale=k)


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
    """pop-up de subscrição (baseado em lib/subscribe_popup.py, cores do pôr do sol)"""
    u = t - SUB_T0
    if u < 0 or u > 2.6: return
    inn = seg(u, 0, 0.35); out = seg(u, 2.2, 2.55); a = inn * (1 - out)
    done = u > 1.0
    w, h = 660, 104; x = (W - w) / 2; y = 330 - 40 * (1 - inn) - 30 * out
    sc = 0.92 + 0.08 * inn - 0.05 * math.sin(math.pi * clamp((u - 0.85) / 0.25))
    c.save(); c.translate(W / 2, y + h / 2); c.scale(sc, sc); c.translate(-W / 2, -(y + h / 2))
    c.set_source_rgba(0.18, 0.04, 0.12, 0.9 * a); rr(c, x, y, w, h, h / 2); c.fill()
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


HL, WH = "&H0040D8FF&", "&H00FFFFFF&"   # destaque dourado (BGR) — contrasta com céus violeta, azuis e laranja
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
    E = [(shimmer, 0.0, 0.55), (boom, 0.0, 0.25)]                          # impacto no frame 0 (o arco já está lá)
    E += [(pop, T["earth"] - 0.05, 0.25), (whoosh, T["every"] - 0.35, 0.3), (a("scratch_head"), T["brand"], 0.7)]
    E += [(swish, x - 0.12, 0.3) for x in CHAPTERS]
    E += [(pop, T["europe"] - 0.05, 0.25), (shimmer, T["arch"] - 0.35, 0.3)]
    E += [(ding, T["bright"] + 0.7, 0.3), (ding, T["above"] - 0.1, 0.3), (ding, T["longer"] + 0.2, 0.3)]
    E += [(shimmer, T["eqimg"], 0.3), (whoosh, T["shadow"], 0.25)]
    E += [(pop, T["sunset"] + 0.15 + 0.32 * k, 0.18) for k in range(4)] + [(ding, T["sunset"] + 1.15, 0.25)]
    E += [(shimmer, T["ice"] - 0.3, 0.35), (pop, SUB_T0 + 1.0, 0.25)]
    E += [(whoosh, T["but"], 0.35), (shimmer, T["really"], 0.4)]
    E += [(boom, T["n466"] - 0.03, 0.5), (pop, T["n466"] - 0.05, 0.35)]
    E += [(whoosh, T_END - 0.9, 0.3)]
    ins, ch, lab = [], [], []
    for f, x, v in E:
        i = 3 + len(lab); ins += ["-i", f]; d = int(max(0, x) * 1000)
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
