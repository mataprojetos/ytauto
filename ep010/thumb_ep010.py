"""Capa EP010: ilustração a2 (pose de génio com o asteroide atrás) + "PLAN A FAILED" por código (sem gerar imagens).
→ thumbnails/ep010_thumb.jpg"""
import os, math, cairo, numpy as np
from PIL import Image
W, H = 1080, 1920
im = Image.open("anim/a2_genio.png").convert("RGB")
z = 1.12; iw, ih = int(W * z), int(W * z * im.height / im.width)
im = im.resize((iw, ih), Image.LANCZOS)
cx, cy = int(iw * 0.5), int(ih * 0.5)
im = im.crop((cx - W // 2, cy - H // 2 - 60, cx + W // 2, cy + H // 2 - 60))
a = np.array(im); buf = np.zeros((H, W, 4), np.uint8); buf[..., :3] = a[..., ::-1]; buf[..., 3] = 255
bg = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, W, H)
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
c.set_source_surface(bg, 0, 0); c.paint()
g = cairo.LinearGradient(0, 1000, 0, 1700); g.add_color_stop_rgba(0, 0.02, 0.01, 0.08, 0); g.add_color_stop_rgba(1, 0.02, 0.01, 0.08, 0.7)
c.set_source(g); c.paint()
def text(s_, x, y, size, col, rot=0.0, oc=(0.05, 0.03, 0.08)):
    c.save(); c.translate(x, y); c.rotate(rot)
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    e = c.text_extents(s_); c.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing); c.text_path(s_)
    c.set_source_rgb(*oc); c.set_line_width(size * 0.17); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke_preserve()
    c.set_source_rgb(*col); c.fill(); c.restore()
text("PLAN A", 540, 1180, 220, (1, 1, 1), -0.04)
text("FAILED", 540, 1420, 250, (1.0, 0.27, 0.25), -0.04)
# X vermelho desenhado ao lado do texto
c.set_line_cap(cairo.LINE_CAP_ROUND)
for lw, col in ((48, (0.05, 0.03, 0.08)), (30, (1.0, 0.27, 0.25))):
    c.set_source_rgb(*col); c.set_line_width(lw)
    c.move_to(860, 860); c.line_to(1010, 1010); c.move_to(1010, 860); c.line_to(860, 1010); c.stroke()
s.write_to_png("build/thumb.png")
Image.open("build/thumb.png").convert("RGB").save("../thumbnails/ep010_thumb.jpg", quality=90)
print(os.path.getsize("../thumbnails/ep010_thumb.jpg"))
