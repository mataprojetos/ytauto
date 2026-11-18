#!/usr/bin/env python3
"""Protótipo "cena viva" (0 créditos): o robô da secretária ganha movimento dentro da ilustração.
Camadas recortadas por cor (robô branco sobre fundo azul), fundo reconstruído por inpaint,
olhos redesenhados por código no ecrã-cara, braço a escrever, ecrã do computador a correr, estrelas e vapor."""
import math, os, subprocess, sys, random
import cairo, cv2
import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, DUR = 1080, 1920, 30, 6.0
S = 0.7734  # escala de trabalho (1536x2752 -> 1188x2128)
CYAN = (0.30, 0.95, 1.0)
random.seed(3)


def load_scene(path):
    im = np.array(Image.open(path).convert("RGB"))
    big = im.astype(float) / 255
    mx, mn = big.max(2), big.min(2)
    sat = (mx - mn) / (mx + 1e-6)
    m = (mx > 0.62) & (sat < 0.38)
    h0, w0 = m.shape
    box = np.zeros_like(m); box[int(h0 * .38):int(h0 * .72), int(w0 * .40):int(w0 * .86)] = True
    m = nd.binary_fill_holes(nd.binary_closing(m & box, iterations=6))
    lab, n = nd.label(m)
    sizes = nd.sum(m, lab, range(1, n + 1))
    order = np.argsort(sizes)[::-1] + 1
    head = nd.binary_opening(lab == order[0], iterations=2)
    body = nd.binary_opening(lab == order[1], iterations=2)
    return im, head, body


im, head_m, body_m = load_scene(f"{ROOT}/anim/robot_desk.png")
h0, w0 = head_m.shape
ws, hs = int(w0 * S), int(h0 * S)
small = cv2.resize(im, (ws, hs), interpolation=cv2.INTER_AREA)
hm = cv2.resize(head_m.astype(np.uint8), (ws, hs), interpolation=cv2.INTER_NEAREST).astype(bool)
bm = cv2.resize(body_m.astype(np.uint8), (ws, hs), interpolation=cv2.INTER_NEAREST).astype(bool)
arm_x = int(840 * S)
am = bm.copy(); am[:, arm_x:] = False      # antebraço (para a esquerda, sobre o teclado)
tm = bm.copy(); tm[:, :arm_x] = False      # tronco

# olhos originais apagados com a cor do ecrã (para os redesenhar)
EYES = [(903 * S, 1213 * S), (999 * S, 1213 * S)]
face = small.copy()
for ex, ey in EYES:
    cv2.ellipse(face, (int(ex), int(ey)), (int(30 * S), int(42 * S)), 0, 0, 360, (3, 8, 52), -1)
face = cv2.GaussianBlur(face, (0, 0), 1.2)
face = np.where((hm & (np.hypot(*np.mgrid[0:hs, 0:ws][::-1] - np.array([[[951 * S]], [[1213 * S]]])) < 150 * S))[..., None], face, small)

# fundo sem o robô móvel (inpaint), para não aparecerem "fantasmas" quando a cabeça e o braço mexem
hole = nd.binary_dilation(hm | bm, iterations=5).astype(np.uint8) * 255
bg = cv2.inpaint(small, hole, 9, cv2.INPAINT_TELEA)


def to_surface(rgb, mask=None):
    a = np.full(rgb.shape[:2], 255, np.uint8) if mask is None else (cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 0.8) * 255).astype(np.uint8)
    pm = (rgb.astype(np.float32) * (a[..., None] / 255.0)).astype(np.uint8)
    bgra = np.dstack([pm[:, :, 2], pm[:, :, 1], pm[:, :, 0], a]).copy()
    s = cairo.ImageSurface.create_for_data(bgra, cairo.FORMAT_ARGB32, rgb.shape[1], rgb.shape[0])
    return s, bgra


KEEP = []
def surf(rgb, mask=None):
    s, b = to_surface(rgb, mask); KEEP.append(b); return s


S_BG = surf(bg)
S_HEAD = surf(face, hm)
S_ARM = surf(small, am)
S_TORSO = surf(small, tm)
NECK = (1000 * S, 1335 * S)
MON = (372 * S, 1222 * S, 372 * S, 205 * S)  # ecrã do computador (x, y, w, h)
WIN = (200 * S, 830 * S, 1130 * S, 440 * S)  # vidro da janela
STARS = [(WIN[0] + random.random() * WIN[2], WIN[1] + random.random() * WIN[3] * 0.5, random.uniform(2, 5), random.random() * 6.28) for _ in range(26)]
CODE = [(random.randint(1, 4), random.uniform(0.25, 0.9), random.choice([CYAN, (1, 1, 1), (1.0, 0.8, 0.35)])) for _ in range(60)]


def eyes(ctx, t):
    """olhos: olham para o ecrã, piscam, viram-se para a câmara contentes"""
    look = -12 * S * (1 - min(1, max(0, (t - 2.3) / 0.25))) if t < 4.2 else -12 * S * min(1, (t - 4.2) / 0.25)
    happy = 2.4 < t < 4.0
    blink = any(0 <= t - b < 0.14 for b in (1.1, 4.8))
    for ex, ey in EYES:
        x = ex + look
        ctx.save()
        g = cairo.RadialGradient(x, ey, 0, x, ey, 46 * S)
        g.add_color_stop_rgba(0, *CYAN, 0.45); g.add_color_stop_rgba(1, *CYAN, 0)
        ctx.set_source(g); ctx.arc(x, ey, 46 * S, 0, 6.283); ctx.fill()
        ctx.set_source_rgb(*CYAN)
        if happy:  # ^ ^
            ctx.set_line_width(9 * S); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(x - 17 * S, ey + 6 * S); ctx.line_to(x, ey - 12 * S); ctx.line_to(x + 17 * S, ey + 6 * S); ctx.stroke()
        else:
            sy = 0.12 if blink else 1.0
            ctx.translate(x, ey); ctx.scale(15 * S, 24 * S * sy); ctx.arc(0, 0, 1, 0, 6.283); ctx.fill()
        ctx.restore()


def monitor(ctx, t):
    x, y, w, h = MON
    ctx.save(); ctx.rectangle(x, y, w, h); ctx.clip()
    ctx.set_source_rgba(0.02, 0.06, 0.16, 0.92); ctx.paint()
    scroll = t * 70 * S
    lh = 15 * S
    for i, (ind, ln, col) in enumerate(CODE):
        yy = y + 10 * S + i * lh - scroll % (len(CODE) * lh)
        if yy < y - lh or yy > y + h:
            continue
        ctx.set_source_rgba(*col, 0.85)
        ctx.rectangle(x + 10 * S + ind * 14 * S, yy, (w - 40 * S) * ln * 0.75, 6 * S); ctx.fill()
    p = (t * 0.22) % 1
    ctx.set_source_rgba(1, 1, 1, 0.25); ctx.rectangle(x + 10 * S, y + h - 18 * S, w - 20 * S, 7 * S); ctx.fill()
    ctx.set_source_rgba(*CYAN, 1); ctx.rectangle(x + 10 * S, y + h - 18 * S, (w - 20 * S) * p, 7 * S); ctx.fill()
    ctx.restore()


def steam(ctx, t):
    mx, my = 412 * S, 1530 * S  # caneca
    for k in range(3):
        ph = (t * 0.6 + k / 3) % 1
        ctx.set_source_rgba(1, 1, 1, 0.35 * math.sin(ph * math.pi))
        ctx.set_line_width(5 * S); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for j in range(12):
            yy = my - (ph * 90 + j * 5) * S
            xx = mx + (k - 1) * 12 * S + 8 * S * math.sin(yy / (14 * S) + t * 3)
            ctx.line_to(xx, yy)
        ctx.stroke()


def scene(ctx, t):
    ctx.set_source_surface(S_BG, 0, 0); ctx.paint()
    for x, y, r, ph in STARS:
        a = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(t * 3 + ph))
        ctx.set_source_rgba(0.7, 0.95, 1, a); ctx.arc(x, y, r * S, 0, 6.283); ctx.fill()
    monitor(ctx, t)
    steam(ctx, t)
    breathe = 3 * S * math.sin(t * 2.2)
    typing = 0 if 2.3 < t < 4.2 else 4 * S * abs(math.sin(t * 22))
    ctx.set_source_surface(S_TORSO, 0, breathe); ctx.paint()
    ctx.set_source_surface(S_ARM, 0, breathe * 0.5 - typing); ctx.paint()
    # cabeça: inclina e acena ao ritmo; vira-se um pouco para a câmara no meio
    ang = math.radians(2.0 * math.sin(t * 1.7) + (-5 if 2.4 < t < 4.0 else 0) * min(1, abs(t - 2.4) / 0.2, abs(4.0 - t) / 0.2))
    ctx.save(); ctx.translate(NECK[0], NECK[1] + breathe * 1.4); ctx.rotate(ang); ctx.translate(-NECK[0], -NECK[1])
    ctx.set_source_surface(S_HEAD, 0, 0); ctx.paint()
    eyes(ctx, t)
    ctx.restore()


def frame(t):
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(out)
    z = 1.45 + 0.08 * t / DUR
    k = max(W / ws, H / hs) * z
    c.translate(W / 2, H / 2); c.scale(k, k); c.translate(-ws * 0.47, -hs * 0.47)
    scene(c, t)
    return np.ndarray((H, W, 4), np.uint8, out.get_data())[:, :, [2, 1, 0]].tobytes()


if __name__ == "__main__":
    out = sys.argv[1]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(frame(i / FPS))
    p.stdin.close(); p.wait(); print("OK", out)
