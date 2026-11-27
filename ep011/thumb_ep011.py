"""Capa EP011: ilustração própria nano_banana_pro
(anim/thumb_base.png: o rapaz enterrado até à cintura, em pânico) + "DON'T MOVE" por código.
→ thumbnails/ep011_thumb.jpg"""
import os, cairo, numpy as np
from PIL import Image
W, H = 1080, 1920
SC = 1.18   # ampliada e subida: a cara fica acima do texto central
im = Image.open("anim/thumb_base.png").convert("RGB").resize((int(W * SC), int(W * SC * 2752 / 1536)), Image.LANCZOS)
ox, oy = (im.width - W) // 2, 330
im = im.crop((ox, oy, ox + W, oy + H))
a = np.array(im); buf = np.zeros((H, W, 4), np.uint8); buf[..., :3] = a[..., ::-1]; buf[..., 3] = 255
bg = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, W, H)
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
c.set_source_surface(bg, 0, 0); c.paint()
g = cairo.RadialGradient(540, 1010, 60, 540, 1010, 520); g.add_color_stop_rgba(0, 0, 0, 0, 0.45); g.add_color_stop_rgba(1, 0, 0, 0, 0)
c.set_source(g); c.paint()
def text(s_, x, y, size, col, rot=0.0, oc=(0.03, 0.02, 0.04)):
    c.save(); c.translate(x, y); c.rotate(rot)
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    e = c.text_extents(s_); c.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing); c.text_path(s_)
    c.set_source_rgb(*oc); c.set_line_width(size * 0.2); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke_preserve()
    c.set_source_rgb(*col); c.fill(); c.restore()
# regra do canal: texto centrado no meio da imagem e compacto (~140–150 px, <= 60% da largura) para caber no recorte do Short
text("DON'T", 540, 940, 140, (1, 1, 1), -0.05)
text("MOVE", 540, 1080, 150, (1.0, 0.86, 0.1), -0.05)
s.write_to_png("build/thumb.png")
Image.open("build/thumb.png").convert("RGB").save("../thumbnails/ep011_thumb.jpg", quality=90)
print(os.path.getsize("../thumbnails/ep011_thumb.jpg"))
