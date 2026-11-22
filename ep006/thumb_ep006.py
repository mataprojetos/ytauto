"""Capa EP006 (só código): vista de dentro do buraco negro — anel de luz enorme (o universo lá fora),
linhas a cair para o centro, astronauta minúsculo, texto "NO WAY BACK". → thumbnails/ep006_thumb.jpg"""
import math, os, sys, cairo
from PIL import Image
sys.argv = [sys.argv[0]]
import anim_ep006 as A
W, H = 1080, 1920
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
c.set_source_rgb(0, 0, 0); c.paint()
g = cairo.RadialGradient(540, 980, 0, 540, 980, 1100)
g.add_color_stop_rgba(0, 0.25, 0.09, 0.02, 1); g.add_color_stop_rgba(1, 0, 0, 0, 1); c.set_source(g); c.paint()
A.CX, A.CY = 540, 1000
A.converge(c, 3.0, 0.0, a=0.8, swirl=1.9)
# anel de luz enorme
R = 430
A.glow(c, 540, 1000, R * 1.6, A.ORANGE, 0.55, r0=R * 0.7)
for lw, col, al in ((90, A.EMBER, 0.5), (50, A.ORANGE, 0.75), (22, A.GOLD, 0.95), (8, A.HOT, 1.0)):
    c.set_line_width(lw); c.set_source_rgba(*col, al); c.arc(540, 1000, R, 0, 2 * math.pi); c.stroke()
c.save(); c.arc(540, 1000, R - 50, 0, 2 * math.pi); c.clip()
c.set_source_rgba(0, 0, 0, 0.82); c.paint()
A.converge(c, 3.0, 0.0, a=0.45, swirl=2.6)
c.restore()
# astronauta minúsculo a cair (de costas)
c.save(); c.translate(540, 1010); c.rotate(-0.35)
A.astronaut_back(c, 0, 0, 0.32, a=1.0, rim=A.GOLD)
c.restore()
A.text(c, "NO WAY", 540, 300, 210, A.INK, 1, ow=0.12, ocol=(0, 0, 0))
A.text(c, "BACK", 540, 500, 250, A.RED, 1, ow=0.12, ocol=(0, 0, 0))
A.text(c, "NOT EVEN LIGHT", 540, 1600, 86, A.AMBER, 1, ow=0.14, ocol=(0, 0, 0))
os.makedirs("../thumbnails", exist_ok=True)
s.write_to_png("build/thumb.png")
Image.open("build/thumb.png").convert("RGB").save("../thumbnails/ep006_thumb.jpg", quality=90)
print(os.path.getsize("../thumbnails/ep006_thumb.jpg"))
