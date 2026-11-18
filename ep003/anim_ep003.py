#!/usr/bin/env python3
"""Whatifaholic #003 — What if you took off your helmet in space? (~56 s).
Base: ep002/anim_ep002.py. Fundo preto com estrelas minúsculas (pedido do dono); ilustrações isoladas sobre preto,
recortadas por preenchimento a partir das bordas e animadas por código (flutuar, inchar, rodar, ser puxado),
mais partículas (ar, bolhas), ECG, luz de alarme. Relógio "SECOND x" + barra de O2 sempre no mesmo sítio."""
import math, re, json, subprocess, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cairo, cv2
import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = os.path.dirname(os.path.abspath(__file__))
A, BLD = f"{ROOT}/anim", f"{ROOT}/build"
W, H, FPS = 1080, 1920, 30
NARR = f"{ROOT}/audio/narration.wav"
MUSIC = f"{ROOT}/../music/track01_cosmic_ambient.mp3"
OUT = f"{ROOT}/whatifaholic_ep003_helmet.mp4"
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", NARR]))
T_END = round(dur + 0.5, 2)

INK, CYAN, SUN, QUIET = (1, 1, 1), (0.24, 0.88, 1.0), (1.0, 0.72, 0.25), (0.75, 0.8, 0.9)
RED, GREEN, ORANGE, DARK = (1.0, 0.3, 0.3), (0.35, 1.0, 0.5), (1.0, 0.55, 0.15), (0.03, 0.03, 0.05)
random.seed(5)


def ease(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)


def seg(t, a, b):
    return ease((t - a) / (b - a))


# ---------- recortes (ilustrações sobre preto) ----------
SW, SH = 1188, 2128
KEEP = []


def cutout(name):
    im = np.array(Image.open(f"{A}/{name}.png").convert("RGB").resize((SW, SH), Image.LANCZOS))
    dark = im.max(2) < 22
    lab, _ = nd.label(dark)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bg = np.isin(lab, border[border > 0])
    a = (np.clip(cv2.GaussianBlur((~bg).astype(np.float32), (0, 0), 1.0), 0, 1) * 255).astype(np.uint8)
    pm = (im.astype(np.float32) * (a[..., None] / 255.0)).astype(np.uint8)
    bgra = np.dstack([pm[:, :, 2], pm[:, :, 1], pm[:, :, 0], a]).copy()
    KEEP.append(bgra)
    return cairo.ImageSurface.create_for_data(bgra, cairo.FORMAT_ARGB32, SW, SH)


IMG = {n: cutout(n) for n in "astro_helmet nohelmet tongue thermos swollen unconscious rescue chamber".split()}
K0 = max(W / SW, H / SH)  # escala de cobertura


def subject(ctx, name, z=1.0, dx=0, dy=0, rot=0.0, piv=(0.5, 0.5), sx=1.0, sy=1.0, alpha=1.0, flip=False):
    """desenha a ilustração recortada: zoom z, deslocamento (px do ecrã), rotação à volta de piv (fração da imagem)"""
    s = IMG[name]; k = K0 * z
    ctx.save()
    ctx.translate(W / 2 + dx, H / 2 + dy)
    px, py = (piv[0] - 0.5) * SW * k, (piv[1] - 0.5) * SH * k
    ctx.translate(px, py); ctx.rotate(rot); ctx.scale(sx * (-1 if flip else 1), sy); ctx.translate(-px, -py)
    ctx.scale(k, k); ctx.translate(-SW / 2, -SH / 2)
    ctx.set_source_surface(s, 0, 0); ctx.paint_with_alpha(alpha)
    ctx.restore()


def img_xy(fx, fy, z=1.0, dx=0, dy=0):
    """ponto da imagem (fração) -> ecrã, sem rotação"""
    k = K0 * z
    return W / 2 + dx + (fx - 0.5) * SW * k, H / 2 + dy + (fy - 0.5) * SH * k


def float_(t, amp=14, ph=0.0):
    return amp * math.sin(t * 1.3 + ph), amp * 0.6 * math.sin(t * 0.9 + ph), 0.035 * math.sin(t * 0.7 + ph)


# ---------- palavras e âncoras ----------
words = json.load(open(f"{BLD}/words_ep003.json"))


def clean(w):
    return re.sub(r"[^\w']", "", w).lower()


def at(phrase, after=0.0):
    toks = phrase.lower().split(); cl = [clean(w["w"]) for w in words]
    for i in range(len(words) - len(toks) + 1):
        if words[i]["s"] >= after and all(cl[i + j] == toks[j] for j in range(len(toks))):
            return words[i]["s"]
    raise KeyError(phrase)


T = dict(space=at("space"), s1=at("second one"), explode=at("explode"), hollywood=at("hollywood"), air=at("but the air"),
         hold=at("hold your breath"), tear=at("tear"), s3=at("second three"), spit=at("spit"), boil=at("boil"),
         body=at("body temperature"), s5=at("second five"), freeze=at("freeze"), cold=at("cold"), empty=at("empty"),
         heat=at("heat"), thermos=at("like a thermos"), inside=at("inside"), s9=at("second nine"), swell=at("swell"),
         suit=at("your suit"), literally=at("literally"), s15=at("second fifteen"), brain=at("your brain"),
         lights=at("lights out"), twist=at("and here's"), alive=at("alive"), pulled=at("get pulled"), n90=at("90"),
         survive=at("survive"), happened=at("it actually"), y1966=at("1966"), nasa=at("nasa"), woke=at("he woke"),
         memory=at("his last"), spit2=at("spit", after=44), boiling=at("boiling"), would=at("would you rather"),
         boss=at("boss"), tellme=at("tell me below"), because=at("because you have"))
ZERO = T["space"]
SECONDS = [(T["s1"], 1), (T["s3"], 3), (T["s5"], 5), (T["s9"], 9), (T["s15"], 15)]

# ---------- estrelas (pontos minúsculos; periódicas para o último frame = primeiro) ----------
STARS = [(random.uniform(0, W), random.uniform(0, H), random.uniform(0.5, 1.5), random.random() * 6.283,
          random.randint(1, 3)) for _ in range(420)]


def starfield(ctx, t):
    ctx.set_source_rgb(0, 0, 0); ctx.paint()
    w = 2 * math.pi / T_END
    for x, y, r, ph, k in STARS:
        a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(k * 6 * w * t + ph))
        xx = x + 6 * r * math.sin(w * t + ph)
        ctx.set_source_rgba(1, 1, 1, a); ctx.arc(xx, y, r, 0, 6.283); ctx.fill()


# ---------- utilitários de texto ----------
def rr(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def text(ctx, s, x, y, size, col=INK, a=1.0, align="c", bold=True):
    if a <= 0.01:
        return
    ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    xb, yb, tw, th, _, _ = ctx.text_extents(s)
    ox = {"c": tw / 2, "l": 0, "r": tw}[align]
    ctx.move_to(x - ox - xb, y); ctx.text_path(s)
    ctx.set_source_rgba(0, 0, 0, 0.6 * a); ctx.set_line_width(size * 0.12); ctx.stroke_preserve()
    ctx.set_source_rgba(*col, a); ctx.fill()


def extents(ctx, s, size):
    ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(size)
    return ctx.text_extents(s)[2]


def pop(t, t0, d=0.16):
    x = (t - t0) / d
    return 0 if x <= 0 else 1 + 0.5 * (1 - ease(min(x, 1)))


def tag(ctx, s, x, y, size, col, a, sc=1.0):
    if a <= 0.01:
        return
    tw = extents(ctx, s, size)
    ctx.save(); ctx.translate(x, y - size * 0.35); ctx.scale(sc, sc); ctx.translate(-x, -(y - size * 0.35))
    ctx.set_source_rgba(*DARK, 0.8 * a); rr(ctx, x - tw / 2 - size * 0.55, y - size * 1.08, tw + size * 1.1, size * 1.45, size * 0.45)
    ctx.fill_preserve(); ctx.set_source_rgba(*col, 0.9 * a); ctx.set_line_width(3); ctx.stroke()
    text(ctx, s, x, y, size, col, a); ctx.restore()


def stamp(ctx, s, x, y, size, col, t, t0, rot=-0.07, t1=None):
    sc = pop(t, t0)
    if sc <= 0:
        return
    a = min(1, (t - t0) / 0.08) * (1 - (seg(t, t1 - 0.2, t1) if t1 else 0))
    if a <= 0.01:
        return
    tw = extents(ctx, s, size)
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc)
    ctx.set_source_rgba(*DARK, 0.75 * a); rr(ctx, -tw / 2 - 34, -size * 0.95, tw + 68, size * 1.35, 18); ctx.fill()
    ctx.set_source_rgba(*col, a); ctx.set_line_width(7); rr(ctx, -tw / 2 - 34, -size * 0.95, tw + 68, size * 1.35, 18); ctx.stroke()
    text(ctx, s, 0, size * 0.05, size, col, a); ctx.restore()


def glow(ctx, x, y, r, col, a):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    ctx.set_source(g); ctx.arc(x, y, r, 0, 6.283); ctx.fill()


PUFFS = [(random.uniform(-0.5, 0.5), random.uniform(0.6, 1.4), random.random()) for _ in range(40)]
BUBS = [(random.uniform(-1, 1), random.uniform(0.5, 1.5), random.random(), random.uniform(4, 11)) for _ in range(45)]


def puffs(ctx, t, x, y, a, dirx=1.0):
    """ar a sair da boca"""
    for ang, sp, ph in PUFFS:
        p = (t * 0.9 * sp + ph) % 1
        r = 8 + 40 * p
        xx = x + dirx * p * 380 * math.cos(ang) ; yy = y + p * 380 * math.sin(ang) - 30 * p
        ctx.set_source_rgba(0.9, 0.95, 1, a * 0.35 * (1 - p)); ctx.arc(xx, yy, r, 0, 6.283); ctx.fill()


def bubbles(ctx, t, x, y, spread, a, rise=260):
    for dx, sp, ph, r in BUBS:
        p = (t * 0.8 * sp + ph) % 1
        xx = x + dx * spread + 10 * math.sin(t * 5 + ph * 9); yy = y - p * rise
        ctx.set_source_rgba(1, 0.85, 0.9, a * (1 - p)); ctx.set_line_width(2.5)
        ctx.arc(xx, yy, r * (0.6 + p), 0, 6.283); ctx.stroke()


# ---------- cenas ----------
Y_TAG = 520


def hook_text(ctx, t, a=1.0):
    sc = 1 + 0.06 * math.sin(t * 20) * (0 < t < ZERO)
    text(ctx, "15", 540, 470, 260 * sc, RED, a)
    text(ctx, "SECONDS LEFT", 540, 560, 62, INK, a)


def s_hook(ctx, t):
    starfield(ctx, t)
    fx, fy, fr = float_(t)
    sh = 6 * seg(t, ZERO - 1.0, ZERO)
    subject(ctx, "astro_helmet", 1.0, fx + sh * math.sin(t * 80), fy + 230, fr)
    hook_text(ctx, t)


def s_nohelmet(ctx, t):
    starfield(ctx, t)
    fx, fy, fr = float_(t, 10, 1.0)
    z = 1.35 + 0.06 * seg(t, ZERO, T["s3"])
    shake = 10 * max(0, 1 - (t - T["explode"]) / 0.4) if t > T["explode"] else 0
    dx, dy = fx + shake * math.sin(t * 90), fy + 260
    subject(ctx, "nohelmet", z, dx, dy, fr)
    glow(ctx, W / 2, H / 2, 900, (1, 1, 1), 0.8 * max(0, 1 - (t - ZERO) / 0.25))
    stamp(ctx, "NO EXPLOSION", 540, Y_TAG + 40, 88, CYAN, t, T["explode"] + 0.1, t1=T["air"])
    mx, my = img_xy(0.60, 0.35, z, dx, dy)
    puffs(ctx, t, mx, my, seg(t, T["air"], T["air"] + 0.3) * (1 - seg(t, T["s3"] - 0.3, T["s3"])))
    tag(ctx, "DON'T HOLD YOUR BREATH", 540, Y_TAG, 54, RED, seg(t, T["hold"], T["hold"] + 0.15), pop(t, T["hold"]) or 1)


def s_tongue(ctx, t):
    starfield(ctx, t)
    fx, fy, fr = float_(t, 6, 2.0)
    z = 1.0 + 0.05 * seg(t, T["s3"], T["s5"])
    subject(ctx, "tongue", z, fx, fy + 80, fr * 0.4)
    bx, by = img_xy(0.54, 0.64, z, fx, fy + 80)
    bubbles(ctx, t, bx, by, 90, seg(t, T["boil"] - 0.3, T["boil"] + 0.2))
    stamp(ctx, "37°C", 830, Y_TAG + 40, 110, SUN, t, T["body"] + 0.1, rot=0.08)


def s_cold(ctx, t):
    starfield(ctx, t)
    fx, fy, fr = float_(t, 16, 3.0)
    z = 1.1
    subject(ctx, "nohelmet", z, fx - 40, fy + 150, fr, flip=True)
    tag(ctx, "SPACE: -270°C", 540, Y_TAG, 62, CYAN, seg(t, T["cold"], T["cold"] + 0.15), pop(t, T["cold"]) or 1)
    k = seg(t, T["empty"], T["empty"] + 0.4)  # o calor fica: aura laranja
    if k > 0:
        cx, cy = img_xy(0.55, 0.55, z, fx - 40, fy + 150)
        for i in range(3):
            ctx.set_source_rgba(*ORANGE, 0.5 * k * (0.6 + 0.4 * math.sin(t * 4 + i)))
            ctx.set_line_width(6); ctx.arc(cx, cy, 430 + 40 * i + 15 * math.sin(t * 3 + i), 0, 6.283); ctx.stroke()
        stamp(ctx, "HEAT STAYS IN", 540, Y_TAG + 160, 76, ORANGE, t, T["heat"])


def s_thermos(ctx, t):
    starfield(ctx, t)
    fx, fy, fr = float_(t, 14, 4.0)
    subject(ctx, "thermos", 1.12, fx, fy + 90, fr + 0.05 * math.sin(t * 2))


def s_swollen(ctx, t):
    starfield(ctx, t)
    fx, fy, fr = float_(t, 10, 5.0)
    g = seg(t, T["swell"] - 0.2, T["swell"] + 1.6)
    wob = 0.025 * math.sin(t * 9) * g
    z = 1.0 + 0.16 * g
    subject(ctx, "swollen", z, fx, fy + 100, fr, sx=1 + wob, sy=1 - wob)
    stamp(ctx, "LITERALLY.", 540, Y_TAG + 40, 100, SUN, t, T["literally"] + 0.05)


def s_out(ctx, t):
    starfield(ctx, t)
    fx, fy, fr = float_(t, 18, 6.0)
    rot = 0.25 * (t - T["s15"])
    subject(ctx, "unconscious", 1.05, fx, fy + 80, fr + rot)
    o = seg(t, T["lights"], T["lights"] + 0.25)  # luzes apagam
    if o > 0:
        ctx.set_source_rgba(0, 0, 0, 0.82 * o); ctx.paint()
        text(ctx, "LIGHTS OUT", 540, 900, 110, QUIET, o)


def ecg(ctx, t, x0, y0, w, a):
    if a <= 0.01:
        return
    ctx.set_source_rgba(*GREEN, a); ctx.set_line_width(6); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.new_path()
    for i in range(160):
        u = i / 159; ph = (u * 3 - t * 1.2) % 1
        beat = (-120 * math.exp(-((ph - 0.5) / 0.02) ** 2) + 50 * math.exp(-((ph - 0.54) / 0.02) ** 2))
        ctx.line_to(x0 + u * w, y0 + beat)
    ctx.stroke()


def s_twist(ctx, t):
    starfield(ctx, t)
    fx, fy, fr = float_(t, 18, 6.0)
    subject(ctx, "unconscious", 1.05, fx, fy + 80, fr + 0.25 * (t - T["s15"]))
    ctx.set_source_rgba(0, 0, 0, 0.82 * (1 - seg(t, T["alive"], T["alive"] + 0.4))); ctx.paint()
    sc = pop(t, T["twist"] + 0.15, 0.22)
    if sc and t < T["alive"]:
        ctx.save(); ctx.translate(540, 800); ctx.scale(sc, sc); glow(ctx, 0, -40, 420, SUN, 0.3)
        text(ctx, "THE TWIST", 0, 0, 150, SUN, 1); ctx.restore()
    ecg(ctx, t, 140, Y_TAG + 60, 800, seg(t, T["alive"], T["alive"] + 0.2))
    tag(ctx, "STILL ALIVE", 540, Y_TAG + 230, 64, GREEN, seg(t, T["alive"], T["alive"] + 0.15), pop(t, T["alive"]) or 1)


def s_rescue(ctx, t):
    starfield(ctx, t)
    p = seg(t, T["pulled"], T["pulled"] + 2.5)
    dy = 160 - 120 * p + 6 * math.sin(t * 2)
    _, ycut = img_xy(0.5, 0.80, 1.0, 0, dy)  # esconde o membro estranho por baixo dos pés
    ctx.save(); ctx.rectangle(0, 0, W, ycut); ctx.clip()
    subject(ctx, "rescue", 1.0, 0, dy, 0)
    ctx.restore()
    k = seg(t, T["n90"], T["n90"] + 0.15)
    if k > 0:
        left = max(0, 90 - (t - T["n90"]) * 8)
        tag(ctx, f"{int(left) // 60}:{int(left) % 60:02d} TO SAVE YOU", 540, Y_TAG + 380, 64, SUN, k, pop(t, T["n90"]) or 1)


def s_chamber(ctx, t):
    starfield(ctx, t)
    fx, fy, fr = float_(t, 5, 7.0)
    subject(ctx, "chamber", 1.0, fx, fy + 120, fr * 0.3)
    lx, ly = img_xy(0.5, 0.163, 1.0, fx, fy + 120)
    glow(ctx, lx, ly, 160, RED, 0.6 * (0.5 + 0.5 * math.sin(t * 8)))
    stamp(ctx, "1966", 540, Y_TAG + 10, 120, SUN, t, T["y1966"], t1=T["woke"])
    tag(ctx, "WOKE UP FINE", 540, Y_TAG, 64, GREEN, seg(t, T["woke"], T["woke"] + 0.15), pop(t, T["woke"]) or 1)
    px, py = img_xy(0.55, 0.62, 1.0, fx, fy + 120)
    bubbles(ctx, t, px, py, 60, seg(t, T["spit2"], T["spit2"] + 0.3), rise=180)


def s_poll(ctx, t):
    starfield(ctx, t)
    for j, (lab, l1, l2, col, yy, tj) in enumerate([("A", "15 SECONDS", "IN SPACE, NO HELMET", CYAN, 560, T["would"]),
                                                     ("B", "15 MINUTES", "IN AN ELEVATOR WITH YOUR BOSS", SUN, 900, T["boss"] - 1.4)]):
        k = seg(t, tj + 0.2, tj + 0.5)
        if k <= 0:
            continue
        x = 540 + (1 - k) * (600 if j else -600)
        ctx.set_source_rgba(*col, 0.14 * k); rr(ctx, x - 450, yy - 140, 900, 260, 34); ctx.fill()
        ctx.set_source_rgba(*col, 0.9 * k); ctx.set_line_width(4); rr(ctx, x - 450, yy - 140, 900, 260, 34); ctx.stroke()
        text(ctx, lab, x - 350, yy + 30, 120, col, k)
        text(ctx, l1, x + 60, yy - 10, 74, INK, k)
        sz = 40 if len(l2) < 22 else 30
        text(ctx, l2, x + 60, yy + 55, sz, col, k)
    text(ctx, "VS", 540, 765, 64, QUIET, seg(t, T["boss"] - 1.6, T["boss"] - 1.4))
    c = seg(t, T["tellme"], T["tellme"] + 0.2)
    text(ctx, "COMMENT  A  OR  B", 500, 1110, 60, CYAN, c)
    ax = 815 + 12 * math.sin(t * 8)
    if c > 0.01:
        ctx.set_source_rgba(*CYAN, c); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(ax, 1090); ctx.line_to(ax + 100, 1090); ctx.stroke()
        ctx.move_to(ax + 70, 1062); ctx.line_to(ax + 100, 1090); ctx.line_to(ax + 70, 1118); ctx.stroke()


def s_end(ctx, t):
    """volta ao frame 0: astronauta com capacete, mesma posição (float_ é periódico o suficiente), '15 SECONDS LEFT'"""
    starfield(ctx, t)
    k = seg(t, T["because"], T_END - 0.35)
    fx, fy, fr = float_(t)
    f0 = float_(0.0)
    subject(ctx, "astro_helmet", 1.0, fx + (f0[0] - fx) * k, fy + 230 + (f0[1] - fy) * k, fr + (f0[2] - fr) * k,
            alpha=seg(t, T["because"], T["because"] + 0.5))
    hook_text(ctx, 0.0, seg(t, T["because"] + 0.3, T["because"] + 0.9))


SCENES = [(0, s_hook, "cut"), (ZERO, s_nohelmet, "cut"), (T["s3"], s_tongue, "zoom"), (T["s5"], s_cold, "push"),
          (T["thermos"], s_thermos, "zoom"), (T["s9"], s_swollen, "push"), (T["s15"], s_out, "zoom"),
          (T["twist"], s_twist, "cut"), (T["pulled"], s_rescue, "circle"), (T["happened"], s_chamber, "push"),
          (T["would"], s_poll, "circle"), (T["because"], s_end, "circle")]
SCENES = [(a, (SCENES[i + 1][0] if i + 1 < len(SCENES) else T_END + 1), fn, tr) for i, (a, fn, tr) in enumerate(SCENES)]

JOKES = [T["hollywood"], T["inside"], T["literally"], T["lights"], T["boiling"]]
PUNCH = [ZERO, T["explode"], T["body"], T["twist"] + 0.15, T["n90"], T["y1966"]] + JOKES
TRANS = 0.28


def punch(t):
    v = 0
    for p in PUNCH:
        x = t - p
        if 0 <= x < 0.45:
            v = max(v, math.sin(min(1, x / 0.08) * math.pi / 2) * (1 - x / 0.45))
    return 1 + 0.045 * v


def clock(ctx, t):
    """relógio fixo: SECOND x + barra de oxigénio a descer até 'lights out'"""
    a = seg(t, T["s1"] - 0.25, T["s1"]) * (1 - seg(t, T["twist"] - 0.25, T["twist"]))
    if a <= 0.01:
        return
    sec, t0 = 1, T["s1"]
    for th, s in SECONDS:
        if t >= th:
            sec, t0 = s, th
    sc = pop(t, t0, 0.2) or 1
    x, y, w_, h_ = 540 - 170, 168, 340, 86
    ctx.save(); ctx.translate(540, y + h_ / 2); ctx.scale(sc, sc); ctx.translate(-540, -(y + h_ / 2))
    ctx.set_source_rgba(*DARK, 0.85 * a); rr(ctx, x, y, w_, h_, 26); ctx.fill()
    ctx.set_source_rgba(*RED, 0.9 * a); ctx.set_line_width(3); rr(ctx, x, y, w_, h_, 26); ctx.stroke()
    text(ctx, f"SECOND {sec}", 540, y + 61, 54, INK, a); ctx.restore()
    o2 = 1 - seg(t, T["s1"], T["lights"])
    col = GREEN if o2 > 0.5 else (SUN if o2 > 0.2 else RED)
    text(ctx, "O2", x + 6, y + h_ + 34, 26, QUIET, a, "l")
    ctx.set_source_rgba(1, 1, 1, 0.25 * a); rr(ctx, x + 50, y + h_ + 14, w_ - 56, 12, 6); ctx.fill()
    ctx.set_source_rgba(*col, a); rr(ctx, x + 50, y + h_ + 14, max(10, (w_ - 56) * o2), 12, 6); ctx.fill()


def badge(ctx, t):
    a = seg(t, T["s1"] + 0.5, T["s1"] + 0.9) * (1 - seg(t, T["twist"] - 0.2, T["twist"]))
    if a <= 0.01:
        return
    w_, h_ = 600, 66; x, y = 540 - w_ / 2, 300
    ctx.set_source_rgba(*DARK, 0.8 * a); rr(ctx, x, y, w_, h_, 30); ctx.fill()
    ctx.set_source_rgba(*SUN, 0.9 * a); ctx.set_line_width(3); rr(ctx, x, y, w_, h_, 30); ctx.stroke()
    ctx.set_source_rgba(*SUN, a * (0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 5)))); ctx.arc(x + 36, y + h_ / 2, 10, 0, 6.283); ctx.fill()
    text(ctx, "THE TWIST · COMING UP", x + 64, y + 45, 34, SUN, a, "l")


ALARM_P = 0.5


def alarm(ctx, t):
    if t >= ZERO:
        return
    p = 0.5 - 0.5 * math.cos(2 * math.pi * t / ALARM_P)
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.62)
    g.add_color_stop_rgba(0, *RED, 0); g.add_color_stop_rgba(1, *RED, 0.62 * p)
    ctx.set_source(g); ctx.paint()
    ctx.set_source_rgba(*RED, 0.9 * p); ctx.set_line_width(18); ctx.rectangle(9, 9, W - 18, H - 18); ctx.stroke()


def render(fn, t):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_BEST); fn(c, t)
    return s


def frame(t, raw=False):
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(out)
    for i, (a, b, fn, tr) in enumerate(SCENES):
        if a <= t < b:
            cur = render(fn, t)
            x = (t - a) / TRANS
            if i > 0 and x < 1 and tr != "cut":
                prev = render(SCENES[i - 1][2], t); e = ease(x)
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
    alarm(ctx, t); clock(ctx, t); badge(ctx, t)
    z = punch(t)
    if z > 1.0005:
        fin = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c2 = cairo.Context(fin)
        c2.set_source_rgb(0, 0, 0); c2.paint()
        c2.translate(W / 2, H / 2); c2.scale(z, z); c2.translate(-W / 2, -H / 2)
        c2.set_source_surface(out, 0, 0); c2.paint(); out = fin
    if raw:
        return out
    return np.ndarray((H, W, 4), np.uint8, out.get_data())[:, :, [2, 1, 0]].tobytes()


# ---------- legendas ----------
WEAK = {"a", "an", "the", "to", "of", "for", "on", "in", "it", "its", "and", "but", "with", "is", "as", "be", "would",
        "if", "about", "so", "here's", "because", "your", "or", "by", "his", "are", "has", "you", "you're", "was", "within"}
FIX = {"fifteen,": "15,", "Second": "Second"}
for w in words:
    w["w"] = FIX.get(w["w"], w["w"])

groups, cur = [], []
for w in words:
    cand = cur + [w]
    if cur and (len(cand) > 3 or len(" ".join(x["w"] for x in cand)) > 18):
        if len(cur) > 1 and re.sub(r"[^\w']", "", cur[-1]["w"]).lower() in WEAK:
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
    g_end = min(groups[gi + 1][0]["s"], g[-1]["e"] + 0.5) if gi + 1 < len(groups) else T_END
    for k, w in enumerate(g):
        s = w["s"]; e = g[k + 1]["s"] if k + 1 < len(g) else g_end
        popt = "{\\fscx108\\fscy108\\t(0,90,\\fscx100\\fscy100)}" if k == 0 else ""
        txt = " ".join((f"{{\\c{CY}}}{x['w'].upper()}{{\\c{WH}}}" if j == k else x["w"].upper()) for j, x in enumerate(g))
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},Cap,,0,0,0,,{popt}{txt}")
ev += [f"Dialogue: 2,{ts(0)},{ts(T_END)},Mark,,0,0,0,,@whatifaholics"]
open(f"{BLD}/captions.ass", "w").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,90,90,560,1
Style: Mark,Inter Display,40,&H8CFFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,3,0,7,60,60,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n")

if __name__ == "__main__":
    if "--sheet" in sys.argv:
        times = [0, 2.0, ZERO + 0.4, T["air"] + 0.8, T["boil"] + 0.6, T["heat"] + 0.4, T["inside"] + 0.3,
                 T["literally"] + 0.4, T["lights"] + 0.5, T["alive"] + 0.5, T["n90"] + 0.6, T["woke"] + 0.4,
                 T["tellme"] + 0.4, T_END - 1 / FPS]
        tw_, th_ = 270, 480
        sheet = Image.new("RGB", (7 * tw_, 2 * th_))
        for i, tt in enumerate(times):
            s = frame(tt, raw=True)
            im = Image.frombuffer("RGBA", (W, H), bytes(s.get_data()), "raw", "BGRA", 0, 1).convert("RGB")
            sheet.paste(im.resize((tw_, th_)), ((i % 7) * tw_, (i // 7) * th_))
        sheet.save(sys.argv[sys.argv.index("--sheet") + 1]); print("sheet ok"); sys.exit()

    raw = f"{BLD}/raw.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                          "-pix_fmt", "yuv420p", raw], stdin=subprocess.PIPE)
    for i in range(int(T_END * FPS)):
        p.stdin.write(frame(i / FPS))
    p.stdin.close(); p.wait()

    def synth(name, expr, d):
        path = f"{BLD}/{name}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={d}", path], check=True)
        return path
    swish = f"{BLD}/swish.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.5:c=pink:a=0.5:r=48000",
                    "-af", "bandpass=f=900:w=1400,afade=t=in:d=0.25:curve=qsin,afade=t=out:st=0.25:d=0.25,volume=0.35", swish], check=True)
    popw = synth("pop_soft", "0.5*sin(2*PI*(260+500*exp(-t*35))*t)*exp(-t*22)", 0.2)
    ding = synth("ding", "0.35*(sin(2*PI*1320*t)+0.5*sin(2*PI*1980*t))*exp(-t*9)", 0.6)
    events = [(swish, c - 0.25, 0.5) for c in (T["s3"], T["s5"], T["s9"], T["s15"], T["twist"], T["would"])]
    P = ALARM_P; h = P / 2
    env = f"min(1,mod(t,{h})*120)*min(1,({h}-mod(t,{h}))*120)"
    tone = f"(lt(mod(t,{P}),{h})*(sin(2*PI*960*t)+0.3*sin(2*PI*2880*t))+gte(mod(t,{P}),{h})*(sin(2*PI*770*t)+0.3*sin(2*PI*2310*t)))"
    alarm_wav = f"{BLD}/alarm.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='0.45*{env}*{tone}':s=48000:d={ZERO:.3f}",
                    "-af", f"afade=t=out:st={max(0, ZERO - 0.06):.3f}:d=0.06", alarm_wav], check=True)
    events += [(alarm_wav, 0.0, 0.32)]
    boom = f"{BLD}/boom.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "aevalsrc='0.9*sin(2*PI*(48+70*exp(-t*6))*t)*exp(-t*2.8)':s=48000:d=1.6",
                    "-f", "lavfi", "-i", "anoisesrc=d=0.4:c=brown:a=0.8:r=48000",
                    "-filter_complex", "[1]afade=t=out:d=0.4,lowpass=f=900[n];[0][n]amix=inputs=2:normalize=0,volume=0.9", boom], check=True)
    events += [(boom, ZERO - 0.02, 0.6)]
    events += [(popw, x, 0.5) for x in (T["s1"], T["body"], T["n90"], T["y1966"])]
    events += [(ding, x + 0.15, 0.35) for x in JOKES]
    ins, ch, lab = [], [], []
    for n, (f, x, v) in enumerate(events):
        idx = 3 + n; ins += ["-i", f]; d = int(max(0, x) * 1000)
        ch.append(f"[{idx}:a]adelay={d}|{d},volume={v}[e{n}]"); lab.append(f"[e{n}]")
    sfx = ";".join(ch) + ";" + "".join(lab) + f"amix=inputs={len(lab)}:normalize=0[sfx]"
    pre = T["twist"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", NARR, "-stream_loop", "-1", "-i", MUSIC, *ins,
                    "-filter_complex",
                    f"[0:v]noise=alls=2:allf=t,subtitles={BLD}/captions.ass,format=yuv420p[v];"
                    "[1:a]asplit=2[n1][nk];"
                    f"[2:a]atrim=0:{T_END},volume='if(lt(t,{ZERO + 0.35:.2f}),0,if(between(t,{pre-0.6:.2f},{pre+0.1:.2f}),0.08,0.35))':eval=frame,"
                    f"afade=t=out:st={T_END-1.5}:d=1.5[m];"
                    "[m][nk]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[md];"
                    f"{sfx};[n1][md][sfx]amix=inputs=3:duration=longest:normalize=0,apad,"
                    f"loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{T_END}[a]",
                    "-map", "[v]", "-map", "[a]", "-t", str(T_END), "-r", str(FPS),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-maxrate", "8M", "-bufsize", "16M",
                    "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", OUT], check=True)
    print("OK", OUT, T_END)
