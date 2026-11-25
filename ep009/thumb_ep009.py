"""Capa EP009: ilustração aprovada s1 (queda do avião) + "3 MINUTES LEFT" por código (sem gerar imagens).
→ thumbnails/ep009_thumb.jpg"""
import os, math, cairo, numpy as np
from PIL import Image
W, H = 1080, 1920
im = Image.open("anim/s1_queda_aviao.png").convert("RGB")
z = 1.18; iw, ih = int(W * z), int(W * z * im.height / im.width)
im = im.resize((iw, ih), Image.LANCZOS)
cx, cy = int(iw * 0.5), int(ih * 0.46)
im = im.crop((cx - W // 2, cy - H // 2 + 230, cx + W // 2, cy + H // 2 + 230))
a = np.array(im); buf = np.zeros((H, W, 4), np.uint8); buf[..., :3] = a[..., ::-1]; buf[..., 3] = 255
bg = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, W, H)
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
c.set_source_surface(bg, 0, 0); c.paint()
g = cairo.RadialGradient(540, 1060, 100, 540, 1060, 700); g.add_color_stop_rgba(0, 0.02, 0.04, 0.15, 0.35); g.add_color_stop_rgba(1, 0.02, 0.04, 0.15, 0)
c.set_source(g); c.paint()
def text(s_, x, y, size, col, rot=0.0, oc=(0.05, 0.03, 0.08)):
    c.save(); c.translate(x, y); c.rotate(rot)
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    e = c.text_extents(s_); c.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing); c.text_path(s_)
    c.set_source_rgb(*oc); c.set_line_width(size * 0.17); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke_preserve()
    c.set_source_rgb(*col); c.fill(); c.restore()
text("3 MINUTES", 540, 960, 190, (1, 1, 1), -0.03)
text("LEFT", 540, 1160, 240, (1.0, 0.55, 0.15), -0.03)
s.write_to_png("build/thumb.png")
Image.open("build/thumb.png").convert("RGB").save("../thumbnails/ep009_thumb.jpg", quality=90)
print(os.path.getsize("../thumbnails/ep009_thumb.jpg"))
