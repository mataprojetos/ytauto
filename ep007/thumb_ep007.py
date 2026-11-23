"""Capa EP007: arco gigante de anéis sobre uma rua europeia + cara de choque (nano_banana_pro, 3.º braço apagado
em build/fix_images.py) e texto "THIS WAS REAL?!" por código. → thumbnails/ep007_thumb.jpg"""
import os, math, cairo, numpy as np
from PIL import Image
W, H = 1080, 1920
im = Image.open("anim/thumb_bg_clean.png").convert("RGB").resize((W, int(W * 2752 / 1536)), Image.LANCZOS)
im = im.crop((0, (im.height - H) // 2 + 40, W, (im.height - H) // 2 + 40 + H))
a = np.array(im); buf = np.zeros((H, W, 4), np.uint8); buf[..., :3] = a[..., ::-1]; buf[..., 3] = 255
bg = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, W, H)
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
c.set_source_surface(bg, 0, 0); c.paint()
g = cairo.LinearGradient(0, 0, 0, 700); g.add_color_stop_rgba(0, 0.05, 0.02, 0.15, 0.75); g.add_color_stop_rgba(1, 0.05, 0.02, 0.15, 0)
c.set_source(g); c.paint()
def text(s_, x, y, size, col, rot=0.0):
    c.save(); c.translate(x, y); c.rotate(rot)
    c.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    e = c.text_extents(s_); c.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing); c.text_path(s_)
    c.set_source_rgb(0.03, 0.02, 0.06); c.set_line_width(size * 0.16); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke_preserve()
    c.set_source_rgb(*col); c.fill(); c.restore()
text("THIS WAS", 540, 250, 170, (1, 1, 1), -0.03)
text("REAL?!", 540, 450, 250, (1.0, 0.83, 0.25), -0.03)
s.write_to_png("build/thumb.png")
os.makedirs("../thumbnails", exist_ok=True)
Image.open("build/thumb.png").convert("RGB").save("../thumbnails/ep007_thumb.jpg", quality=90)
print(os.path.getsize("../thumbnails/ep007_thumb.jpg"))
