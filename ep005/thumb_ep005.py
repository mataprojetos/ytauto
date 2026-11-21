"""Capa EP005 feita só em código: olho enorme com notas a sair + "$5,256,000 A YEAR?"."""
import math, random, sys, os
sys.argv = [sys.argv[0]]
ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ROOT)
import cairo
import anim_ep005 as A
from PIL import Image
W, H = 1080, 1920
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
g = cairo.RadialGradient(540, 900, 50, 540, 900, 1300)
g.add_color_stop_rgb(0, 0.1, 0.45, 0.25); g.add_color_stop_rgb(1, 0.01, 0.08, 0.05); c.set_source(g); c.paint()
c.save(); c.translate(540, 900)
for k in range(20):
    c.set_source_rgba(1, 0.85, 0.3, 0.09); c.move_to(0, 0); c.arc(0, 0, 1600, k * math.pi / 10, k * math.pi / 10 + math.pi / 20); c.close_path(); c.fill()
c.restore()
random.seed(3)
# notas a voar para fora do olho
for i in range(22):
    an = random.uniform(0, 2 * math.pi); d = random.uniform(380, 720)
    A.bill(c, 540 + math.cos(an) * d, 900 + math.sin(an) * d * 1.1, random.uniform(170, 260), an + random.uniform(-0.4, 0.4), 1)
for i in range(10):
    an = random.uniform(0, 2 * math.pi); d = random.uniform(300, 560)
    A.coin(c, 540 + math.cos(an) * d, 900 + math.sin(an) * d, random.uniform(40, 60), 1, spin=random.uniform(0, 1))
A.glow(c, 540, 900, 600, (1, 0.95, 0.6), 0.55)
A.eye(c, 540, 900, 400, 1.0, dx=0.0, dy=0.0)
# veias vermelhas (olho arregalado)
c.set_source_rgba(0.9, 0.2, 0.2, 0.55); c.set_line_width(4)
for sx in (-1, 1):
    for k in range(3):
        c.move_to(540 + sx * 360, 900 + (k - 1) * 40); c.curve_to(540 + sx * 320, 900 + (k - 1) * 50, 540 + sx * 290, 880 + k * 30, 540 + sx * 250, 890 + (k - 1) * 30); c.stroke()
A.text(c, "$5,256,000", 540, 330, 170, A.GOLD, 1, ow=0.18, rot=-0.04)
A.text(c, "A YEAR?", 540, 510, 190, (1, 1, 1), 1, ow=0.18, rot=-0.04)
A.text(c, "JUST FOR BLINKING", 540, 1460, 92, A.MINT, 1, ow=0.18)
s.write_to_png(f"{ROOT}/build/thumb.png")
out = f"{ROOT}/../thumbnails/ep005_thumb.jpg"
Image.open(f"{ROOT}/build/thumb.png").convert("RGB").save(out, quality=90)
print(out, os.path.getsize(out))
