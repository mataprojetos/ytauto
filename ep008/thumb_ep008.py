"""Capa EP008: boneco a cair no túnel com o núcleo a brilhar ao fundo (nano_banana_pro) + "NO BOTTOM" por código.
→ thumbnails/ep008_thumb.jpg"""
import os, cairo, numpy as np
from PIL import Image
W, H = 1080, 1920
im = Image.open("anim/thumb_bg.png").convert("RGB").resize((W, int(W * 2752 / 1536)), Image.LANCZOS)
im = im.crop((0, (im.height - H) // 2, W, (im.height - H) // 2 + H))
a = np.array(im); buf = np.zeros((H, W, 4), np.uint8); buf[..., :3] = a[..., ::-1]; buf[..., 3] = 255
bg = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, W, H)
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
c.set_source_surface(bg, 0, 0); c.paint()
g = cairo.RadialGradient(540, 1640, 50, 540, 1640, 520)   # reforça o brilho do núcleo
g.add_color_stop_rgba(0, 1, 0.75, 0.3, 0.45); g.add_color_stop_rgba(1, 1, 0.5, 0.1, 0)
c.set_source(g); c.paint()
def text(s_, x, y, size, col, rot=0.0):
    c.save(); c.translate(x, y); c.rotate(rot)
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    e = c.text_extents(s_); c.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing); c.text_path(s_)
    c.set_source_rgb(0.05, 0.02, 0.01); c.set_line_width(size * 0.17); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke_preserve()
    c.set_source_rgb(*col); c.fill(); c.restore()
text("NO", 540, 790, 260, (1, 1, 1), -0.03)
text("BOTTOM", 540, 1010, 230, (1.0, 0.62, 0.15), -0.03)
s.write_to_png("build/thumb.png")
Image.open("build/thumb.png").convert("RGB").save("../thumbnails/ep008_thumb.jpg", quality=90)
print(os.path.getsize("../thumbnails/ep008_thumb.jpg"))
