#!/usr/bin/env python3
"""Cenas vivas (0 créditos): movimento dentro das ilustrações, por código.

- Robôs: a cabeça é recortada por cor (concha branca + ecrã-cara escuro), o fundo atrás é reconstruído por
  inpaint, e os olhos são apagados e redesenhados por código (piscar, olhar, contente ^ ^, cansado, liso, espantado).
- Recortes genéricos (ex.: avião, tronco, braço) para mover partes da imagem.
- Efeitos por cena (vapor, ecrãs a correr, notas, papagaio...) são funções fx(ctx, t) em coordenadas da imagem.
Tudo trabalha à escala S (1536x2752 -> 1188x2128) e é desenhado com a mesma transformação de paint_cover."""
import math
import cairo, cv2
import numpy as np
from PIL import Image
from scipy import ndimage as nd

S = 0.7734
CYAN = (0.30, 0.95, 1.0)
KEEP = []


def _surf(rgb, alpha=None):
    a = np.full(rgb.shape[:2], 255, np.uint8) if alpha is None else alpha
    pm = (rgb.astype(np.float32) * (a[..., None] / 255.0)).astype(np.uint8)
    bgra = np.dstack([pm[:, :, 2], pm[:, :, 1], pm[:, :, 0], a]).copy()
    KEEP.append(bgra)
    return cairo.ImageSurface.create_for_data(bgra, cairo.FORMAT_ARGB32, rgb.shape[1], rgb.shape[0])


def _soft(mask):
    return (np.clip(cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 0.9), 0, 1) * 255).astype(np.uint8)


def eye_state_default(t):
    return dict(kind="normal", look=(0, 0), blink=(t % 3.1) < 0.13)


class Robot:
    """cabeça de robô animável. eyes = [(x,y),(x,y)] em píxeis da imagem original; ew, eh = tamanho do olho."""

    def __init__(self, img, eyes, ew, eh, state=eye_state_default, sway=2.0, bob=3.0, phase=0.0, face_col=None):
        self.eyes = [(x * S, y * S) for x, y in eyes]
        self.ew, self.eh = ew * S / 2, eh * S / 2
        (x1, y1), (x2, y2) = self.eyes
        d = math.hypot(x2 - x1, y2 - y1)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        self.c = (cx, cy); self.d = d
        h, w = img.shape[:2]
        box = np.zeros((h, w), bool)
        bx0, bx1 = int(max(0, cx - 2.05 * d)), int(min(w, cx + 2.05 * d))
        by0, by1 = int(max(0, cy - 1.7 * d)), int(min(h, cy + 1.45 * d))
        box[by0:by1, bx0:bx1] = True
        f = img.astype(float) / 255
        mx, mn = f.max(2), f.min(2)
        sat = (mx - mn) / (mx + 1e-6)
        white = (mx > 0.6) & (sat < 0.36) & (f[..., 2] >= f[..., 0] - 0.02)
        dark = (mx < 0.33) & (f[..., 2] >= f[..., 0])
        cyan = (f[..., 2] > 0.7) & (f[..., 1] > 0.6) & (f[..., 0] < 0.7)
        yy, xx = np.mgrid[0:h, 0:w]
        rr = np.hypot(xx - cx, yy - cy)
        ell = ((xx - cx) / (1.9 * d)) ** 2 + ((yy - (cy - 0.1 * d)) / (1.55 * d)) ** 2 < 1
        m = (white | dark | (cyan & (rr < 1.15 * d))) & box & ell
        m = nd.binary_opening(m, iterations=3)
        lab, _ = nd.label(m)
        m = lab == lab[int(cy), int(cx)]
        m = nd.binary_fill_holes(nd.binary_closing(m, iterations=4))
        self.mask = nd.binary_opening(m, iterations=2)
        self.pivot = (cx, min(by1, cy + 1.25 * d))
        # apagar os olhos originais com a cor do ecrã
        fc = face_col or tuple(int(v) for v in np.median(img[int(cy - 0.05 * d):int(cy + 0.05 * d), int(cx - 0.1 * d):int(cx + 0.1 * d)].reshape(-1, 3), 0))
        face = img.copy()
        for ex, ey in self.eyes:
            cv2.ellipse(face, (int(ex), int(ey)), (int(self.ew * 1.9), int(self.eh * 1.6)), 0, 0, 360, fc, -1)
        face = cv2.GaussianBlur(face, (0, 0), 1.0)
        near = (np.hypot(xx - cx, yy - cy) < 1.05 * d) & self.mask
        self.rgb = np.where(near[..., None], face, img)
        self.state, self.sway, self.bob, self.phase = state, sway, bob, phase
        self.surface = None

    def build(self):
        self.surface = _surf(self.rgb, _soft(self.mask))

    def draw(self, ctx, t, extra_dy=0.0):
        st = self.state(t)
        ang = math.radians(self.sway * math.sin(t * 1.7 + self.phase) + st.get("tilt", 0))
        dy = self.bob * S * math.sin(t * 2.2 + self.phase) + extra_dy + st.get("dy", 0.0)
        ctx.save(); ctx.translate(self.pivot[0], self.pivot[1] + dy); ctx.rotate(ang)
        ctx.translate(-self.pivot[0], -self.pivot[1])
        ctx.set_source_surface(self.surface, 0, 0); ctx.paint()
        self.draw_eyes(ctx, st)
        ctx.restore()

    def draw_eyes(self, ctx, st):
        kind = st.get("kind", "normal")
        lx, ly = st.get("look", (0, 0))
        ew, eh = self.ew, self.eh
        if kind == "wide":
            ew, eh = ew * 1.3, eh * 1.25
        for ex, ey in self.eyes:
            x, y = ex + lx * ew, ey + ly * eh
            g = cairo.RadialGradient(x, y, 0, x, y, eh * 2.0)
            g.add_color_stop_rgba(0, *CYAN, 0.45); g.add_color_stop_rgba(1, *CYAN, 0)
            ctx.set_source(g); ctx.arc(x, y, eh * 2.0, 0, 6.283); ctx.fill()
            ctx.set_source_rgb(*CYAN); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            lw = max(2.5, ew * 0.6)
            if kind == "happy":
                ctx.set_line_width(lw)
                ctx.move_to(x - ew * 1.15, y + eh * 0.25); ctx.line_to(x, y - eh * 0.5); ctx.line_to(x + ew * 1.15, y + eh * 0.25)
                ctx.stroke()
            elif kind == "flat" or st.get("blink"):
                ctx.set_line_width(lw)
                ctx.move_to(x - ew * 1.1, y); ctx.line_to(x + ew * 1.1, y); ctx.stroke()
            elif kind == "tired":
                ctx.save(); ctx.translate(x, y); ctx.scale(ew * 1.25, eh * 0.95); ctx.arc(0, 0, 1, 0, math.pi); ctx.fill()
                ctx.restore()
                ctx.set_line_width(lw * 0.6); ctx.move_to(x - ew * 1.4, y - eh * 0.05); ctx.line_to(x + ew * 1.4, y + eh * 0.12)
                ctx.stroke()
            else:
                ctx.save(); ctx.translate(x, y); ctx.scale(ew, eh); ctx.arc(0, 0, 1, 0, 6.283); ctx.fill(); ctx.restore()


class Part:
    """recorte genérico (máscara em píxeis da imagem à escala S) movido por move(t) -> (dx, dy, ang, pivot)"""

    def __init__(self, img, mask, move):
        self.rgb, self.mask, self.move = img, mask, move
        self.surface = None

    def build(self):
        self.surface = _surf(self.rgb, _soft(self.mask))

    def draw(self, ctx, t):
        dx, dy, ang, piv = self.move(t)
        ctx.save(); ctx.translate(piv[0] + dx, piv[1] + dy); ctx.rotate(ang); ctx.translate(-piv[0], -piv[1])
        ctx.set_source_surface(self.surface, 0, 0); ctx.paint(); ctx.restore()


class LiveScene:
    def __init__(self, path):
        im = np.array(Image.open(path).convert("RGB"))
        self.h0, self.w0 = im.shape[:2]
        self.w, self.h = int(self.w0 * S), int(self.h0 * S)
        self.img = cv2.resize(im, (self.w, self.h), interpolation=cv2.INTER_AREA)
        self.robots, self.parts, self.fx_under, self.fx_over = [], [], [], []
        self.bg = None

    def fx(self, x, y):  # fração -> píxeis de trabalho
        return x * self.w, y * self.h

    def robot(self, eyes, ew, eh, **kw):
        r = Robot(self.img, eyes, ew, eh, **kw); self.robots.append(r); return r

    def part(self, mask, move):
        p = Part(self.img, mask, move); self.parts.append(p); return p

    def color_mask(self, box, fn):
        """box em frações (x0,y0,x1,y1); fn(f) -> bool array a partir da imagem em [0,1]"""
        x0, y0, x1, y1 = (int(box[0] * self.w), int(box[1] * self.h), int(box[2] * self.w), int(box[3] * self.h))
        f = self.img.astype(float) / 255
        m = np.zeros((self.h, self.w), bool)
        m[y0:y1, x0:x1] = fn(f[y0:y1, x0:x1])
        return nd.binary_fill_holes(nd.binary_closing(m, iterations=2))

    def build(self):
        hole = np.zeros((self.h, self.w), bool)
        for r in self.robots:
            hole |= r.mask
        for p in self.parts:
            hole |= p.mask
        hole = nd.binary_dilation(hole, iterations=5).astype(np.uint8) * 255
        bg = cv2.inpaint(self.img, hole, 9, cv2.INPAINT_TELEA) if hole.any() else self.img
        self.bg = _surf(bg)
        for o in self.robots + self.parts:
            o.build()
        return self

    def draw(self, ctx, t):
        ctx.set_source_surface(self.bg, 0, 0); ctx.paint()
        for f in self.fx_under:
            f(ctx, t)
        for p in self.parts:
            p.draw(ctx, t)
        for r in self.robots:
            r.draw(ctx, t)
        for f in self.fx_over:
            f(ctx, t)


def live_cover(ctx, sc, t, t0, t1, z0, z1, W, H, focus=(0.5, 0.5), seg=None):
    """como paint_cover, mas para uma LiveScene (com foco opcional)"""
    z = z0 + (z1 - z0) * (seg(t, t0, t1) if seg else 0)
    k = max(W / sc.w, H / sc.h) * z
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(k, k)
    fx, fy = focus
    cx = min(max(fx * sc.w, W / 2 / k), sc.w - W / 2 / k)
    cy = min(max(fy * sc.h, H / 2 / k), sc.h - H / 2 / k)
    ctx.translate(-cx, -cy)
    sc.draw(ctx, t)
    ctx.restore()


# ---------- efeitos reutilizáveis ----------
def steam(ctx, t, x, y, height, n=3, spread=12, alpha=0.35, width=5):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(n):
        ph = (t * 0.6 + k / n) % 1
        ctx.set_source_rgba(1, 1, 1, alpha * math.sin(ph * math.pi)); ctx.set_line_width(width * S)
        ctx.new_path()
        for j in range(12):
            yy = y - (ph * height + j * height / 18)
            xx = x + (k - (n - 1) / 2) * spread * S + 8 * S * math.sin(yy / (14 * S) + t * 3)
            ctx.line_to(xx, yy)
        ctx.stroke()


def note(ctx, x, y, s, col, a):
    ctx.set_source_rgba(*col, a)
    ctx.save(); ctx.translate(x, y); ctx.rotate(-0.35); ctx.scale(s * 1.25, s); ctx.arc(0, 0, 1, 0, 6.283); ctx.restore(); ctx.fill()
    ctx.set_line_width(s * 0.28); ctx.move_to(x + s * 1.05, y - s * 0.2); ctx.line_to(x + s * 1.05, y - s * 3.4)
    ctx.line_to(x + s * 2.2, y - s * 2.7); ctx.stroke()
