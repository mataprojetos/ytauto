"""Capa EP010 v3 (estilo vetorial do vídeo): asteroide cinzento enorme a vir contra a câmara, o rapaz pequeno em pânico,
"DON'T NUKE IT!" → thumbnails/ep010_thumb.jpg (0 créditos)"""
import os, sys, cairo
sys.path.insert(0, "vetor")
import vec
from PIL import Image
W, H = 1080, 1920
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
vec.space(c, 1.0, warm=0.6)
vec.corona(c, 560, 820, 560, 1.3, 1.0); vec.asteroid(c, 560, 820, 560, 0.4, 1.0)
ER = 1900; vec.earth(c, 540, 1500 + ER, ER, 0.0)
vec.glow(c, 560, 1500, 1100, vec.FIRE2, 0.35)
vec.guy(c, 300, 1506, 300, 1.0, pose="panic", face="panic", look=0.8, rim=1.0, blink=False)
vec.finish(c, None, 0)
def text(s_, x, y, size, col, rot=0.0, oc=(0.03, 0.02, 0.04)):
    c.save(); c.translate(x, y); c.rotate(rot)
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    e = c.text_extents(s_); c.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing); c.text_path(s_)
    c.set_source_rgb(*oc); c.set_line_width(size * 0.2); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke_preserve()
    c.set_source_rgb(*col); c.fill(); c.restore()
text("DON'T", 540, 175, 210, (1, 1, 1), -0.05)
text("NUKE IT!", 540, 390, 230, (1.0, 0.86, 0.1), -0.05)
s.write_to_png("build/thumb_v.png")
Image.open("build/thumb_v.png").convert("RGB").save("../thumbnails/ep010_thumb.jpg", quality=90)
print(os.path.getsize("../thumbnails/ep010_thumb.jpg"))
