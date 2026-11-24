#!/usr/bin/env python3
"""Whatifaholic EP008 — What If You Jumped Into a Hole Through the Earth?
Estilo do canal: ilustração plana em camadas (4 imagens nano_banana_pro, parallax 2.5D por profundidade)
+ animação por código (pycairo). Base: EP007.
Loop de frase: "Which means, right now…" → "You just jumped…" (último frame = frame 0).
Uso: python3 anim_ep008.py [--frames t1,t2,...|last] [--mix-only]   (sem argumentos: render completo + mistura)"""
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
OUT = f"{ROOT}/whatifaholic_ep008_hole.mp4"
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", NARR]))
N_FR = int(round(DUR * FPS))
T_END = N_FR / FPS
random.seed(8)

# ---------- cores do tema (terra, magma, oceano; sem paleta fixa) ----------
INK = (1, 1, 1); DARK = (0.06, 0.03, 0.02); GOLD = (1.0, 0.84, 0.3); MAGMA = (1.0, 0.5, 0.12); RED = (1.0, 0.25, 0.2)
SEA = (0.35, 0.8, 1.0); GREY = (0.6, 0.62, 0.68); LIME = (0.6, 1.0, 0.45)

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


T = dict(fr=at("for") - 0.1, normal=at("normal"), realize=at("realize"), bottom=at("bottom"), brand=at("that", 2) - 0.08,
         lets=at("let's") - 0.1, magic=at("magic"), noair=at("no", 2), noheat=at("no", 3), because=at("because") - 0.1,
         n5000=at("5000"), fall=at("fall") - 0.25, center=at("center"), n28=at("28000"), feel=at("feel") - 0.32,
         weightless=at("weightless"), then=at("then", 2) - 0.1, flips=at("flips"), now=at("now"), pulling=at("pulling"),
         slow=at("slow") - 0.12, but=at("but") - 0.1, wait=at("wait"), jump=at("jump") - 0.05, united=at("united"),
         n42=at("42"), indian=at("indian"), southwest=at("southwest"), float=at("float"), andthen=at("then", 3) - 0.25,
         again1=at("again"), again2=at("again", 2), forever=at("forever"), which=at("which") - 0.08)



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



CONT_TODAY = [
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



CONT_TODAY += [
    [(114, -22), (122, -18), (131, -12), (137, -12), (142, -11), (146, -19), (153, -25), (151, -34), (144, -39), (138, -35),
     (131, -31), (124, -34), (115, -34), (113, -26)],
    [(45, 55), (60, 70), (100, 77), (140, 72), (178, 68), (160, 60), (140, 50), (122, 40), (120, 30), (108, 20), (105, 10),
     (100, 13), (92, 22), (80, 8), (72, 20), (60, 25), (50, 30), (40, 45)],
]

# ---------- boneco recortado da ilustração do quintal (build/sprite.py) ----------
_sp = np.array(Image.open(f"{ROOT}/anim/faller.png").convert("RGBA"), np.float32)
_sb = np.zeros(_sp.shape, np.uint8); _al = _sp[..., 3:4] / 255
_sb[..., :3] = (_sp[..., 2::-1] * _al).astype(np.uint8); _sb[..., 3] = _sp[..., 3]
SPRITE = cairo.ImageSurface.create_for_data(_sb, cairo.FORMAT_ARGB32, _sp.shape[1], _sp.shape[0])
SP_W, SP_H = _sp.shape[1], _sp.shape[0]
SP_X0, SP_Y0 = 560, 1040                # canto da caixa do recorte na imagem do quintal


def sprite(c, x, y, s, rot=0.0, a=1.0, dark=0.0):
    """desenha o boneco centrado em (x, y) com escala s (1 = tamanho em px da imagem)"""
    if a <= 0 or s <= 0: return
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s); c.translate(-SP_W / 2, -SP_H / 2)
    c.set_source_surface(SPRITE, 0, 0); c.get_source().set_filter(cairo.FILTER_GOOD); c.paint_with_alpha(a)
    if dark > 0:
        c.set_source_rgba(0, 0, 0, dark); c.mask_surface(SPRITE, 0, 0)
    c.restore()


HOLE = (762, 1380)                      # centro do poço na imagem do quintal
SP_C = (SP_X0 + SP_W / 2, SP_Y0 + SP_H / 2)
EARTH_C = (768, 1370); EARTH_R = 925    # Terra em corte (anim/earthcut.png): centro e meia-altura do túnel
OCEAN_HOLE = (717, 1881)


def img2scr(base, x0, y0, x, y): return (x - x0) * base, (y - y0) * base


def border(c, t):
    """bordas vermelhas a piscar (gancho com alarme) até à revelação do túnel"""
    a = (0.55 + 0.45 * math.cos(t * 2 * math.pi * 2)) * (1 - seg(t, T["fr"] - 0.3, T["fr"]))
    if a <= 0.01: return
    for k, (w, al) in enumerate(((60, 0.25), (34, 0.45), (14, 0.95))):
        c.set_source_rgba(*RED, al * a); c.set_line_width(w); c.rectangle(0, 0, W, H); c.stroke()


def cam_hook(t):
    t = max(0.0, t)
    p = smooth(t / (T["fr"] + 0.2))
    return 1.0 + 0.85 * p ** 1.3, p


def s_hook(c, t):
    """frame 0: vista de cima do quintal, o boneco já a cair no poço; a câmara mergulha atrás dele"""
    t = max(0.0, t)
    z, p = cam_hook(t)
    base, x0, y0 = draw_par(c, "yard_clean", z, HOLE[0] / 1536, HOLE[1] / 2752, push=0.12 * p)
    hx, hy = img2scr(base, x0, y0, *HOLE)
    s = 1 - 0.62 * p
    ox, oy = (SP_C[0] - HOLE[0]) * s, (SP_C[1] - HOLE[1]) * s
    sx, sy = hx + ox * base, hy + oy * base
    sprite(c, sx, sy, base * s, rot=0.9 * p, dark=0.45 * p)
    k = popin(t, 0.25, 0.25)
    text(c, "12,742 KM", 540, 330, 130, INK, 1, ow=0.13, scale=k)
    text(c, "STRAIGHT DOWN", 540, 455, 60, GOLD, 1, ow=0.16, scale=popin(t, 0.55, 0.25))
    vignette(c, 0.4)


def s_normal(c, t):
    """'For one second, it feels normal…' — a câmara começa à boca do túnel e afasta-se: não tem fundo"""
    u = t - T["fr"]
    out = smooth((t - T["realize"] + 0.2) / (T["bottom"] - T["realize"] + 0.6))
    z = lerp(2.8, 1.0, out) + 0.04 * u
    fy = lerp(0.2, 0.5, out)
    base, x0, y0 = draw_par(c, "earthcut", z, 0.5, fy, push=0.05 * u)
    # o boneco é um ponto a descer pelo túnel
    yy = EARTH_C[1] - EARTH_R + 60 + 120 * u
    x, y = img2scr(base, x0, y0, EARTH_C[0], yy)
    sprite(c, x, y, 0.09 * base * (1 + 1.5 * (1 - out)), rot=t * 2)
    card(c, t, T["fr"] + 0.3, [("THAT \"MISSED A STAIR\"", INK), ("FEELING…", GOLD)], 150, 360, 780, GOLD,
         bg=(0.12, 0.05, 0.03), t1=T["realize"] - 0.1)
    k = popin(t, T["bottom"] - 0.05, 0.3)
    text(c, "NO BOTTOM", 540, 330, 130, INK, 1, ow=0.13, scale=k)
    vignette(c, 0.35)


def s_brand(c, t):
    u = t - T["brand"]
    draw_par(c, "earthcut", 1.05 + 0.03 * u, 0.5, 0.5)
    c.set_source_rgba(0.08, 0.03, 0.02, 0.62); c.paint()
    draw_scratch(c, u, 540, 760, scale=0.95, skin=(1.0, 0.8, 0.62), accent=MAGMA, ink=INK, hair=(0.25, 0.15, 0.1))


def chip(c, t, t0, label, x, y, col):
    if t < t0: return
    k = popin(t, t0, 0.22)
    c.save(); c.translate(x, y); c.scale(k, k)
    c.set_source_rgba(0.08, 0.04, 0.03, 0.88); rr(c, -190, -50, 380, 100, 50); c.fill()
    c.set_source_rgba(*col, 1); c.set_line_width(5); rr(c, -190, -50, 380, 100, 50); c.stroke()
    c.restore()
    text(c, label, x + 30, y, 50, INK, 1, outline=False, scale=k)
    # cruz vermelha
    q = seg(t, t0 + 0.15, t0 + 0.35)
    if q > 0:
        cx, cy = x - 130, y
        c.set_source_rgba(*RED, 1); c.set_line_width(12); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(cx - 26, cy - 26); c.line_to(cx - 26 + 52 * min(1, q * 2), cy - 26 + 52 * min(1, q * 2)); c.stroke()
        if q > 0.5:
            c.move_to(cx + 26, cy - 26); c.line_to(cx + 26 - 52 * (q - 0.5) * 2, cy - 26 + 52 * (q - 0.5) * 2); c.stroke()


def s_magic(c, t):
    """túnel mágico: sem ar, sem calor; o boneco desce pelo túnel com brilhos"""
    u = t - T["lets"]; d = T["because"] - T["lets"]
    p = smooth(u / d)
    base, x0, y0 = draw_par(c, "earthcut", 2.2 + 0.3 * p, 0.5, lerp(0.3, 0.38, p), px=lerp(30, -30, p), push=0.08 * p)
    yy = EARTH_C[1] - EARTH_R * 0.62 + EARTH_R * 0.3 * p
    x, y = img2scr(base, x0, y0, EARTH_C[0], yy)
    rnd = random.Random(5)
    for i in range(26):
        ph = (t * (0.5 + rnd.random()) + rnd.random()) % 1
        sparkle(c, x + (rnd.random() - 0.5) * 120, y - 500 + ph * 1000, 6 + 10 * rnd.random(), (0.85, 0.75, 1.0), 0.8 * math.sin(math.pi * ph))
    glow(c, x, y, 160, (0.75, 0.6, 1.0), 0.35)
    sprite(c, x, y, 0.34, rot=0.3 * math.sin(t * 3))
    text(c, "MAGIC TUNNEL", 540, 330, 100, (0.85, 0.75, 1.0), 1, ow=0.14, scale=popin(t, T["magic"] - 0.05))
    chip(c, t, T["noair"] - 0.05, "NO AIR", 300, 1180, SEA)
    chip(c, t, T["noheat"] - 0.05, "NO HEAT", 780, 1180, MAGMA)
    vignette(c, 0.35)


def thermo(c, x, y, k, a=1.0):
    c.save(); c.translate(x, y)
    c.set_source_rgba(1, 1, 1, 0.95 * a); rr(c, -26, -300, 52, 320, 26); c.fill(); c.arc(0, 40, 50, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(*RED, a); c.arc(0, 40, 36, 0, 2 * math.pi); c.fill()
    hh = 290 * k; rr(c, -14, 20 - hh, 28, hh + 10, 14); c.fill()
    c.restore()


def s_heat(c, t):
    """'down here, it's over 5,000 degrees' — a câmara desce até ao núcleo a brilhar"""
    u = t - T["because"]; d = T["fall"] - T["because"]
    p = smooth(u / d)
    draw_par(c, "earthcut", lerp(1.6, 2.6, p), 0.5, 0.5, py=lerp(-40, 20, p), push=0.1 * p)
    glow(c, 540, 960, 520, (1, 0.8, 0.35), 0.35 + 0.15 * math.sin(t * 7))
    for i in range(10):   # ondas de calor
        q = (t * 0.8 + i / 10) % 1
        c.set_source_rgba(1, 0.9, 0.5, 0.35 * (1 - q)); c.set_line_width(4); c.arc(540, 960, 120 + 600 * q, 0, 2 * math.pi); c.stroke()
    k = seg(t, T["n5000"] - 0.6, T["n5000"] + 0.3)
    thermo(c, 880, 700, k, seg(u, 0, 0.25))
    pk = popin(t, T["n5000"] - 0.05, 0.3)
    text(c, "5,000°C", 540, 330, 150, (1, 0.92, 0.6), 1, ow=0.12, scale=pk)
    text(c, "INNER CORE", 540, 465, 56, MAGMA, 1, ow=0.16, scale=popin(t, T["n5000"] + 0.35))
    vignette(c, 0.3)


# ---------- túnel em perspetiva (código) ----------
ROCK = [(0.45, 0.3, 0.2), (0.75, 0.32, 0.14), (1.0, 0.55, 0.15), (1.0, 0.85, 0.45)]


def rock_col(p, shade):
    p = clamp(p) * (len(ROCK) - 1); i = min(int(p), len(ROCK) - 2); f = p - i
    col = [lerp(a, b, f) for a, b in zip(ROCK[i], ROCK[i + 1])]
    return [x * shade for x in col]


def tunnel(c, t, phase, deep, speed):
    """anéis do túnel a passar pela câmara (vista para baixo); deep 0 = crosta, 1 = núcleo; speed = linhas de velocidade"""
    N = 28
    zs = sorted((((i - phase) % N) + 0.3 for i in range(N)))
    c.set_source_rgb(*rock_col(deep, 0.8)); c.paint()
    for z in zs:                                  # perto (raio grande) primeiro, longe por cima
        r = 560 / z
        idx = int(math.floor(z + phase + 0.5)) % 2
        sh = (0.5 + 0.45 * idx) * clamp(1.15 - z / N)
        c.set_source_rgb(*rock_col(deep + z / N * 0.5, sh)); c.arc(540, 900, r, 0, 2 * math.pi); c.fill_preserve()
        c.set_source_rgba(0.1, 0.04, 0.02, 0.35 * clamp(1.2 - z / N)); c.set_line_width(max(1.5, 10 / z)); c.stroke()
    glow(c, 540, 900, 300, rock_col(deep + 0.5, 1.25), 0.95)
    rnd = random.Random(2)
    for i in range(int(18 + 50 * speed)):   # linhas de velocidade radiais
        ang = rnd.random() * 2 * math.pi; q = (rnd.random() + t * (1.2 + 3.5 * speed)) % 1
        r0 = 120 + 1000 * q ** 2; r1 = r0 + 60 + 320 * speed * q
        c.set_source_rgba(1, 0.97, 0.9, 0.75 * q); c.set_line_width(2 + 6 * q); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(540 + math.cos(ang) * r0, 900 + math.sin(ang) * r0); c.line_to(540 + math.cos(ang) * r1, 900 + math.sin(ang) * r1); c.stroke()


def gauge(c, x, y, val, a=1.0, shake=0.0):
    if a <= 0: return
    R = 170; vmax = 30000; k = clamp(val / vmax)
    c.save(); c.translate(x + shake * math.sin(val * 0.37), y)
    c.set_source_rgba(0.06, 0.03, 0.02, 0.85 * a); c.arc(0, 0, R + 30, math.pi, 2 * math.pi); c.close_path(); c.fill()
    c.set_line_width(26)
    c.set_source_rgba(0.3, 0.25, 0.22, a); c.arc(0, 0, R, math.pi, 2 * math.pi); c.stroke()
    g = cairo.LinearGradient(-R, 0, R, 0); g.add_color_stop_rgba(0, *LIME, a); g.add_color_stop_rgba(0.6, *GOLD, a); g.add_color_stop_rgba(1, *RED, a)
    c.set_source(g); c.arc(0, 0, R, math.pi, math.pi + math.pi * k); c.stroke()
    ang = math.pi + math.pi * k
    c.set_source_rgba(1, 1, 1, a); c.set_line_width(8); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(0, 0); c.line_to(math.cos(ang) * (R - 30), math.sin(ang) * (R - 30)); c.stroke(); c.arc(0, 0, 14, 0, 2 * math.pi); c.fill()
    c.restore()
    v = int(round(val / 100.0) * 100)
    text(c, f"{v:,} KM/H", x, y + 60, 64, INK, a, ow=0.16)


def minimap(c, x, y, frac, a=1.0, R=105):
    """corte da Terra em miniatura com o ponto do boneco (frac: 0 = EUA, 0.5 = centro, 1 = Índico)"""
    if a <= 0: return
    for r, col in ((1.0, (0.35, 0.55, 0.3)), (0.93, (0.8, 0.35, 0.15)), (0.55, (1.0, 0.6, 0.2)), (0.25, (1, 0.92, 0.6))):
        c.set_source_rgba(*col, a); c.arc(x, y, R * r, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.05, 0.02, 0.02, a); c.set_line_width(6); c.move_to(x, y - R); c.line_to(x, y + R); c.stroke()
    c.set_source_rgba(1, 1, 1, a); c.set_line_width(3); c.arc(x, y, R, 0, 2 * math.pi); c.stroke()
    yy = y - R + 2 * R * frac
    glow(c, x, yy, 30, (1, 1, 1), 0.7 * a); c.set_source_rgba(*RED, a); c.arc(x, yy, 11, 0, 2 * math.pi); c.fill()


def speed_up(t):
    u = (t - T["fall"]) / (T["n28"] - T["fall"])
    return 28000 * (0.3 + 0.7 * smooth(u)) if u < 1 else 28000


def s_fall(c, t):
    """'You fall faster… and faster. At the center… 28,000 km/h'"""
    u = t - T["fall"]
    sp = speed_up(t) / 28000
    phase = 2.0 * u + 3.0 * u * u
    tunnel(c, t, phase, lerp(0.15, 0.85, smooth(u / (T["n28"] - T["fall"]))), sp)
    sh = 6 * sp
    sprite(c, 540 + sh * math.sin(t * 40), 900 + sh * math.cos(t * 33), 0.6, rot=t * (1.5 + 3 * sp))
    gauge(c, 540, 1290 - 60, speed_up(t), seg(u, 0, 0.25), shake=4 * (t > T["n28"]))
    frac = lerp(0.12, 0.5, smooth((t - T["fall"]) / (T["center"] - T["fall"] + 0.3)))
    minimap(c, 900, 460, frac)
    text(c, "FASTER", 540, 330, 100, GOLD, 1, ow=0.14, scale=popin(t, T["fall"] + 0.3) * (t < T["center"] - 0.2))
    if t >= T["center"] - 0.2:
        text(c, "CENTER OF THE EARTH", 470, 330, 66, INK, 1, ow=0.16, scale=popin(t, T["center"] - 0.2))
    if t >= T["n28"] - 0.05:
        c.set_source_rgba(1, 0.95, 0.8, 0.5 * (1 - seg(t, T["n28"], T["n28"] + 0.35))); c.paint()


def s_weightless(c, t):
    u = t - T["feel"]; d = T["then"] - T["feel"]
    p = smooth(u / d)
    draw_par(c, "core", 1.08 + 0.08 * p, 0.5, 0.46, px=lerp(-30, 30, p), py=8 * math.sin(t * 2), push=0.1 * p)
    particles(c, t, (1, 0.85, 0.5), 0.6, vx=4, vy=-6, size=0.8)
    card(c, t, T["feel"] + 0.2, [("YOUR PHONE:", INK), ("\"NO SIGNAL\"", RED)], 130, 1000, 520, RED, bg=(0.15, 0.05, 0.03), rot=-0.04)
    text(c, "WEIGHTLESS", 540, 330, 112, INK, 1, ow=0.13, scale=popin(t, T["weightless"] - 0.05))
    vignette(c, 0.3)


def arrow(c, x, y, ang, L, col, a=1.0, w=16):
    if a <= 0: return
    c.save(); c.translate(x, y); c.rotate(ang)
    c.set_source_rgba(0, 0, 0, 0.4 * a); c.set_line_width(w + 8); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(0, 0); c.line_to(L - 30, 0); c.stroke()
    c.set_source_rgba(*col, a); c.set_line_width(w); c.move_to(0, 0); c.line_to(L - 30, 0); c.stroke()
    c.move_to(L + 8, 0); c.line_to(L - 44, -34); c.line_to(L - 44, 34); c.close_path(); c.fill()
    c.restore()


def s_gravity(c, t):
    """esquema: o boneco passa o centro; as setas da gravidade invertem-se (passam a puxá-lo para trás)"""
    u = t - T["then"]
    base, x0, y0 = draw_par(c, "earthcut", 1.02 + 0.02 * u, 0.5, 0.5)
    c.set_source_rgba(0, 0, 0, 0.25); c.paint()
    cx, cy = img2scr(base, x0, y0, *EARTH_C); R = EARTH_R * base
    # posição: passa o centro em 'flips' e abranda
    tf = T["flips"]
    pos = 0.08 * (t - tf) * 3 if t < tf else 0.62 * (1 - math.exp(-(t - tf) * 0.9))
    y = cy + R * pos
    sprite(c, cx, y, 0.2, rot=t * 1.2)
    fl = seg(t, tf - 0.1, tf + 0.35)
    ang = lerp(math.pi / 2, -math.pi / 2, fl)                 # para baixo → para cima (sempre para o centro)
    for dx in (-150, 150):
        arrow(c, cx + dx, y - 90 * math.sin(ang) * 0.0 - 90 * (1 if fl > 0.5 else 0) + 45, ang, 170, GOLD if fl < 0.5 else RED)
    c.set_source_rgba(1, 1, 1, 0.9); c.arc(cx, cy, 10, 0, 2 * math.pi); c.fill()
    text(c, "GRAVITY FLIPS", 540, 470, 96, GOLD, 1, ow=0.14, scale=popin(t, tf - 0.05))
    if t >= T["pulling"] - 0.1:
        text(c, "PULLING YOU BACK", 540, 1290, 70, RED, 1, ow=0.16, scale=popin(t, T["pulling"] - 0.1))


def s_slow(c, t):
    """'You slow down… and slow down…' — o túnel abranda, o velocímetro desce"""
    u = t - T["slow"]; d = T["but"] - T["slow"]
    p = smooth(u / d)
    phase = 10 + 5 * u - 1.6 * u * u
    v = lerp(24000, 2500, p)
    tunnel(c, t, phase, lerp(0.8, 0.2, p), v / 28000)
    sprite(c, 540, 900, 0.6, rot=t * 0.6)
    gauge(c, 540, 1230, v, 1.0)
    minimap(c, 900, 760, lerp(0.75, 0.97, p))
    card(c, t, T["slow"] + 0.4, [("LIKE THE LAST HOUR", INK), ("BEFORE THE WEEKEND", GOLD)], 110, 470, 640, GOLD,
         bg=(0.12, 0.05, 0.03), rot=0.03, size=42)


def s_tease(c, t):
    u = t - T["but"]
    space_bg(c, t)
    globe(c, 540, 860, 330, 2.0 - u * 6.0, t, sun=(-1, -0.2), ring=0.0, glowc=(0.5, 0.8, 1.0))
    text(c, "?", 540, 860, 360, INK, 0.9 * seg(u, 0.2, 0.5), ow=0.08, scale=popin(t, T["but"] + 0.2, 0.3))


US = (-98, 39); ANTI = (82, -39)


def s_globe(c, t):
    """EUA → antípoda: o globo roda até ao Índico, linha a atravessar a Terra, relógio 42 MIN"""
    u = t - T["jump"]
    space_bg(c, t)
    r0 = -math.radians(US[0]); r1 = -math.radians(ANTI[0])
    q = smooth((t - T["n42"] + 0.1) / (T["indian"] - T["n42"] - 0.1))
    rot = lerp(r0, r1, q)
    cx, cy, R = 540, 900, 360
    globe(c, cx, cy, R, rot, t, sun=(-1, -0.2), ring=0.0, glowc=(0.5, 0.8, 1.0), tilt=0.3)
    ux, uy, uz = proj_pt(cx, cy, R, rot, *US, tilt=0.3)
    ax, ay, az = proj_pt(cx, cy, R, rot, *ANTI, tilt=0.3)
    # linha através da Terra
    lk = seg(t, T["n42"] - 0.1, T["n42"] + 0.4)
    if lk > 0:
        ex, ey = lerp(ux, ax, lk), lerp(uy, ay, lk)
        dashed(c, ux, uy, ex, ey, GOLD, 0.9, w=6, off=-t * 80)
    if uz > -0.1:
        pin(c, ux, uy, popin(t, T["united"] - 0.05, 0.25))
        text(c, "USA", ux, uy - 120, 60, INK, 1, scale=popin(t, T["united"] - 0.05, 0.25), ow=0.16)
    if az > 0.2:
        kk = popin(t, T["indian"] - 0.35, 0.25)
        pin(c, ax, ay, kk, col=SEA)
    # relógio 42 MIN
    if t >= T["n42"] - 0.15:
        mins = int(round(42 * seg(t, T["n42"] - 0.15, T["n42"] + 0.6)))
        x, y = 540, 1330 - 40
        k = popin(t, T["n42"] - 0.15, 0.25)
        c.save(); c.translate(x - 200, y); c.scale(k, k)
        c.set_source_rgba(1, 1, 1, 0.95); c.arc(0, 0, 62, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(0.1, 0.1, 0.15, 1); c.set_line_width(7); c.set_line_cap(cairo.LINE_CAP_ROUND)
        a = -math.pi / 2 + 2 * math.pi * mins / 60
        c.move_to(0, 0); c.line_to(math.cos(a) * 46, math.sin(a) * 46); c.stroke()
        c.move_to(0, 0); c.line_to(0, -30); c.stroke(); c.restore()
        text(c, f"{mins} MIN", x + 60, y, 110, INK, 1, ow=0.13, scale=k)


def s_ocean(c, t):
    """revelação: o boneco sai do túnel no meio do Índico"""
    u = t - T["indian"]; d = T["andthen"] - T["indian"]
    p = smooth(u / d)
    bob = 10 * math.sin(t * 2.2)
    draw_par(c, "ocean", 1.12 - 0.07 * p, 0.5, 0.5, px=lerp(-30, 30, p), py=bob, push=0.08 * p)
    particles(c, t, (1, 1, 1), 0.35, vx=-10, vy=-4, size=0.6)
    c.set_source_rgba(1, 1, 1, 0.6 * (1 - seg(u, 0, 0.35))); c.paint()
    text(c, "INDIAN OCEAN", 540, 330, 112, INK, 1, ow=0.13, scale=popin(t, T["indian"] - 0.02, 0.3))
    text(c, "SW OF AUSTRALIA", 540, 450, 62, SEA, 1, ow=0.17, scale=popin(t, T["southwest"]))
    if t >= T["float"]:
        k = popin(t, T["float"], 0.25); left = 1 - clamp((t - T["float"] - 0.3) / 1.0)
        c.save(); c.translate(870, 640); c.scale(k, k)
        c.set_source_rgba(0.02, 0.15, 0.3, 0.85); c.arc(0, 0, 90, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(*SEA, 1); c.set_line_width(12); c.arc(0, 0, 76, -math.pi / 2, -math.pi / 2 + 2 * math.pi * left); c.stroke()
        c.restore()
        text(c, "1 s", 870, 640, 56, INK, 1, outline=False, scale=k)
    vignette(c, 0.25)


def s_forever(c, t):
    """'And then you fall back in. Again. And again. Forever.' — vaivém pelo túnel, contador de viagens"""
    u = t - T["andthen"]
    base, x0, y0 = draw_par(c, "earthcut", 1.04 + 0.02 * u, 0.5, 0.5, push=0.02 * u)
    c.set_source_rgba(0, 0, 0, 0.2); c.paint()
    cx, cy = img2scr(base, x0, y0, *EARTH_C); R = EARTH_R * base * 0.97
    ph = 1.1 * u + 0.55 * u * u                        # cada vez mais rápido (efeito visual)
    y = cy + R * math.cos(math.pi * ph)
    for k in range(6):                                 # rasto
        yk = cy + R * math.cos(math.pi * (ph - 0.03 * k))
        c.set_source_rgba(1, 0.85, 0.4, 0.25 * (1 - k / 6)); c.arc(cx, yk, 30 - 3 * k, 0, 2 * math.pi); c.fill()
    sprite(c, cx, y, 0.16, rot=t * 3)
    trips = 1 + int(ph)
    if t < T["forever"] - 0.05:
        text(c, f"TRIP #{trips}", 540, 330, 100, GOLD, 1, ow=0.14, scale=popin(t, T["andthen"] + 0.2))
    else:
        text(c, "FOREVER", 540, 330, 120, GOLD, 1, ow=0.13, scale=popin(t, T["forever"] - 0.05))
        text(c, "∞", 540, 470, 120, INK, 1, ow=0.1, scale=popin(t, T["forever"] + 0.05))
    card(c, t, T["again1"] - 0.1, [("LIKE HITTING", INK), ("SNOOZE", RED)], 560, 1040, 420, RED, bg=(0.12, 0.05, 0.03),
         rot=0.04, t1=T["which"] - 0.1)


def s_end(c, t):
    """'Which means, right now…': o boneco volta a cair no buraco do oceano (mergulho da câmara);
    nos últimos frames o quintal do frame 0 abre-se (último frame = frame 0)."""
    u = t - T["which"]; D = T_END - T["which"]
    TR = 0.5; tr0 = T_END - TR
    p = smooth(u / D)
    z = 1.25 + 3.4 * p ** 1.4
    base, x0, y0 = draw_par(c, "ocean_clean", z, OCEAN_HOLE[0] / 1536, (OCEAN_HOLE[1] + 20) / 2752, push=0.1 * p)
    hx, hy = img2scr(base, x0, y0, *OCEAN_HOLE)
    q = smooth(u / (D - TR))
    sprite(c, lerp(hx + 60, hx, q), lerp(hy - 520, hy, q), lerp(0.55, 0.12, q) * base / 0.8, rot=2.5 * q, dark=0.5 * q)
    c.set_source_rgba(0, 0, 0, 0.35 * p); c.paint()
    if t >= tr0:
        k = clamp((t - tr0) / (TR - 1 / FPS))
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cc = cairo.Context(s); s_hook(cc, 0.0)
        sc = lerp(0.55, 1.0, ease(k))
        c.save(); c.translate(W / 2, H / 2); c.scale(sc, sc); c.translate(-W / 2, -H / 2)
        c.set_source_surface(s, 0, 0); c.paint_with_alpha(ease(k) if k < 1 else 1.0); c.restore()


SCENES = [
    (0.0, T["fr"], s_hook), (T["fr"], T["brand"], s_normal), (T["brand"], T["lets"], s_brand), (T["lets"], T["because"], s_magic),
    (T["because"], T["fall"], s_heat), (T["fall"], T["feel"], s_fall), (T["feel"], T["then"], s_weightless),
    (T["then"], T["slow"], s_gravity), (T["slow"], T["but"], s_slow), (T["but"], T["jump"], s_tease),
    (T["jump"], T["indian"], s_globe), (T["indian"], T["andthen"], s_ocean), (T["andthen"], T["which"], s_forever),
    (T["which"], 99, s_end),
]
NO_PUNCH = {s_brand, s_end}
CHAPTERS = [T["fr"], T["lets"], T["fall"], T["then"], T["but"], T["jump"], T["andthen"]]

SUB_T0 = T["but"] - 2.65            # pop-up de subscrição antes de "But wait until you see"
BADGE = (T["wait"], T["indian"])


def badge(c, t):
    a0, a1 = BADGE
    if not (a0 <= t < a1 + 0.35): return
    k = popin(t, a0, 0.25); out = seg(t, a1, a1 + 0.3); a = 1 - out
    c.save(); c.translate(540, 200); c.scale(k * (1 + 0.4 * out), k * (1 + 0.4 * out))
    c.set_source_rgba(0, 0, 0, 0.7 * a); rr(c, -370, -42, 740, 84, 42); c.fill()
    pulse = 0.6 + 0.4 * math.sin(t * 6)
    c.set_source_rgba(*SEA, a * pulse); c.set_line_width(5); rr(c, -370, -42, 740, 84, 42); c.stroke()
    c.set_source_rgba(*SEA, a); rr(c, -338, -12, 36, 30, 6); c.fill()
    c.set_line_width(6); c.arc(-320, -12, 12, math.pi, 2 * math.pi); c.stroke()
    c.restore()
    text(c, "WHERE YOU END UP · COMING UP", 555, 200, 36, INK, a * (k > 0), outline=False, scale=k)


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


HL, WH = "&H0022E0FF&", "&H00FFFFFF&"   # destaque amarelo (BGR): contrasta com o magma, o oceano e o espaço
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
    # Som limpo (pedido do dono, 24/11/2026): sem alarme no gancho e poucos efeitos, só nos momentos-chave.
    # vento da queda: um único som contínuo e grave, em vez de whooshes repetidos
    def wind(d, rise=0.6, seed=5):
        n = int(d * SR); tt = np.arange(n) / SR
        nz = np.random.default_rng(seed).standard_normal(n)
        X = np.fft.rfft(nz); fq = np.fft.rfftfreq(n, 1 / SR); X[(fq < 80) | (fq > 900)] = 0; nz = np.fft.irfft(X, n)
        env = np.minimum(1, tt / rise) * np.minimum(1, (d - tt) / 0.5) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * tt))
        return nz * env / np.abs(nz * env).max() * 0.6
    fall_wind = wind(T["feel"] - T["fall"] + 0.4, rise=1.2)
    E = [(whoosh, 0.0, 0.22), (a("scratch_head"), T["brand"], 0.6)]
    E += [(swish, x - 0.12, 0.18) for x in (T["fr"], T["then"], T["jump"])]
    E += [(wav("fall_wind", fall_wind), T["fall"], 0.25)]
    E += [(pop, T["n5000"] - 0.05, 0.18), (pop, T["n28"] - 0.05, 0.2), (pop, SUB_T0 + 1.0, 0.18)]
    E += [(whoosh, T["but"], 0.2), (pop, T["n42"] - 0.15, 0.16)]
    E += [(boom, T["indian"] - 0.03, 0.4), (shimmer, T["indian"], 0.22), (whoosh, T_END - 0.9, 0.18)]
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
