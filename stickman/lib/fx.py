"""Efeitos: textura de rocha, desfoque (brilho), partículas e cintilações."""
import math
import random

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def np_to_surface(arr):
    """arr HxWx4 uint8 RGBA (pré-multiplicado) -> ImageSurface ARGB32."""
    h, w = arr.shape[:2]
    bgra = np.ascontiguousarray(arr[:, :, [2, 1, 0, 3]])
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    stride = surf.get_stride()
    buf = np.ndarray((h, stride // 4, 4), np.uint8, surf.get_data())
    buf[:, :w] = bgra
    surf.mark_dirty()
    return surf


def surface_to_np(surf):
    surf.flush()
    h, w = surf.get_height(), surf.get_width()
    buf = np.ndarray((h, surf.get_stride() // 4, 4), np.uint8, surf.get_data())
    return buf[:, :w][:, :, [2, 1, 0, 3]].copy()


def blur_surface(surf, radius):
    """Gaussiano sobre uma superfície ARGB32 (para brilhos)."""
    arr = surface_to_np(surf)
    img = Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(radius))
    return np_to_surface(np.asarray(img))


def rock_texture(w, h, seed, base=(22, 16, 15), var=14, warm=(1.0, 0.86, 0.80)):
    """Rocha escura de calhaus suaves (estilo mina/encosta da referência)."""
    rnd = random.Random(seed)
    img = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(img)
    for _ in range(int(w * h / 900)):
        x, y = rnd.uniform(-20, w + 20), rnd.uniform(-20, h + 20)
        r = rnd.uniform(9, 26)
        k = rnd.uniform(-var, var)
        c = tuple(int(max(0, min(255, base[i] + k * warm[i]))) for i in range(3))
        d.ellipse([x - r * 1.25, y - r, x + r * 1.25, y + r], fill=c)
    img = img.filter(ImageFilter.GaussianBlur(3.2))
    # ruído fino
    a = np.asarray(img).astype(np.float32)
    rng = np.random.default_rng(seed)
    a += rng.normal(0, 2.2, a.shape[:2])[:, :, None]
    a = np.clip(a, 0, 255).astype(np.uint8)
    rgba = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    return np_to_surface(rgba)


class Particles:
    """Pó, pedrinhas e faíscas com gravidade. Estado avançado frame a frame."""

    def __init__(self, seed):
        self.rnd = random.Random(seed)
        self.items = []

    def emit(self, x, y, n, vx=(-60, 20), vy=(-90, -20), life=(0.4, 0.9),
             size=(1.2, 3.0), color=(0.75, 0.72, 0.70), g=420, kind="dust"):
        r = self.rnd
        for _ in range(n):
            self.items.append(dict(x=x + r.uniform(-4, 4), y=y + r.uniform(-3, 3),
                                   vx=r.uniform(*vx), vy=r.uniform(*vy),
                                   life=r.uniform(*life), age=0.0, size=r.uniform(*size),
                                   color=color, g=g, kind=kind, rot=r.uniform(0, 6.28)))

    def step(self, dt, ground=None):
        keep = []
        for p in self.items:
            p["age"] += dt
            if p["age"] >= p["life"]:
                continue
            p["vy"] += p["g"] * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if ground is not None and p["kind"] == "rock":
                gy = ground(p["x"])
                if p["y"] > gy - p["size"]:
                    p["y"] = gy - p["size"]
                    p["vy"] *= -0.3
                    p["vx"] *= 0.6
            keep.append(p)
        self.items = keep

    def draw(self, ctx):
        for p in self.items:
            a = 1 - p["age"] / p["life"]
            cr, cg, cb = p["color"]
            if p["kind"] == "spark":
                ctx.set_source_rgba(cr, cg, cb, a)
                ctx.set_line_width(p["size"])
                ctx.move_to(p["x"], p["y"])
                ctx.line_to(p["x"] - p["vx"] * 0.025, p["y"] - p["vy"] * 0.025)
                ctx.stroke()
            elif p["kind"] == "rock":
                ctx.save()
                ctx.translate(p["x"], p["y"])
                ctx.rotate(p["rot"] + p["age"] * 6)
                s = p["size"]
                ctx.move_to(-s, s * 0.6)
                ctx.line_to(0, -s)
                ctx.line_to(s, s * 0.5)
                ctx.close_path()
                ctx.set_source_rgba(cr, cg, cb, min(1, a * 1.6))
                ctx.fill()
                ctx.restore()
            else:
                ctx.set_source_rgba(cr, cg, cb, a * 0.55)
                ctx.arc(p["x"], p["y"], p["size"], 0, 2 * math.pi)
                ctx.fill()


def twinkle(ctx, x, y, size, rgba):
    """Estrela de 4 pontas com núcleo brilhante."""
    r, g, b, a = rgba
    rad = cairo.RadialGradient(x, y, 0, x, y, size * 2.2)
    rad.add_color_stop_rgba(0, r, g, b, a * 0.55)
    rad.add_color_stop_rgba(1, r, g, b, 0)
    ctx.set_source(rad)
    ctx.arc(x, y, size * 2.2, 0, 2 * math.pi)
    ctx.fill()
    ctx.move_to(x, y - size)
    ctx.curve_to(x + size * 0.12, y - size * 0.12, x + size * 0.12, y - size * 0.12, x + size, y)
    ctx.curve_to(x + size * 0.12, y + size * 0.12, x + size * 0.12, y + size * 0.12, x, y + size)
    ctx.curve_to(x - size * 0.12, y + size * 0.12, x - size * 0.12, y + size * 0.12, x - size, y)
    ctx.curve_to(x - size * 0.12, y - size * 0.12, x - size * 0.12, y - size * 0.12, x, y - size)
    ctx.set_source_rgba(min(1, r + 0.2), min(1, g + 0.2), min(1, b + 0.2), a)
    ctx.fill()
