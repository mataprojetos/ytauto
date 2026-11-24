"""Apaga o boneco desenhado na ilustração do oceano (para o mergulho final, onde o boneco é o recorte animado)
→ anim/ocean_clean.png (preenchimento pull-push a partir do mar à volta)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
im = np.array(Image.open("anim/ocean.png").convert("RGB"), np.float32)
OX, OY = 450, 1150
poly = [(320, 105), (385, 105), (395, 165), (440, 165), (480, 185), (545, 160), (605, 170), (595, 235), (505, 320), (445, 445),
        (380, 445), (205, 475), (170, 505), (115, 440), (165, 415), (230, 400), (175, 375), (115, 365), (115, 290), (180, 295),
        (265, 300), (325, 240), (315, 170)]
m = Image.new("L", (im.shape[1], im.shape[0]), 0)
ImageDraw.Draw(m).polygon([(x + OX, y + OY) for x, y in poly], fill=255)
ImageDraw.Draw(m).ellipse((OX + 495, OY + 250, OX + 580, OY + 340), fill=255)
m = m.filter(ImageFilter.MaxFilter(15))
w = np.array(m, np.float32) / 255
keep = 1 - w
def pool(a):
    h, ww = a.shape[:2]; a = a[:h - h % 2, :ww - ww % 2]
    return 0.25 * (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2])
A, Wt = [im * keep[..., None]], [keep]
while min(A[-1].shape[:2]) > 4: A.append(pool(A[-1])); Wt.append(pool(Wt[-1]))
col = A[-1] / np.maximum(Wt[-1], 1e-4)[..., None]
for a, wt in zip(reversed(A[:-1]), reversed(Wt[:-1])):
    up = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((a.shape[1], a.shape[0]), Image.BILINEAR), np.float32)
    own = a / np.maximum(wt, 1e-4)[..., None]; k = np.clip(wt * 4, 0, 1)[..., None]
    col = own * k + up * (1 - k)
col = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((im.shape[1], im.shape[0])), np.float32)
ws = np.array(m.filter(ImageFilter.GaussianBlur(4)), np.float32)[..., None] / 255
out = im * (1 - ws) + col * ws
Image.fromarray(out.astype(np.uint8)).save("anim/ocean_clean.png")
Image.fromarray(out.astype(np.uint8)).crop((450, 1150, 1250, 1750)).save("/tmp/claude-0/c.png")
