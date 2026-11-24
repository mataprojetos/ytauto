"""Recorta o boneco da ilustração do quintal (fundo do poço quase preto) → anim/faller.png (RGBA)
e gera anim/yard_clean.png (poço vazio, o boneco é desenhado por cima em código)."""
import numpy as np
from PIL import Image, ImageFilter
im = np.array(Image.open("anim/yard.png").convert("RGB"), np.float32)
X0, Y0, X1, Y1 = 560, 1040, 1180, 1620
box = im[Y0:Y1, X0:X1]
m = (box.max(2) > 52).astype(np.uint8) * 255
mi = Image.fromarray(m).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
# só a maior mancha ligada (o boneco)
from scipy import ndimage
lab, n = ndimage.label(np.array(mi) > 0); sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
keep = (lab == (1 + int(np.argmax(sizes)))).astype(np.float32)
keep = ndimage.binary_fill_holes(keep).astype(np.float32)
alpha = np.array(Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
ys, xs = np.nonzero(keep); print("bbox", xs.min() + X0, ys.min() + Y0, xs.max() + X0, ys.max() + Y0)
rgba = np.dstack([box, alpha * 255]).astype(np.uint8)
Image.fromarray(rgba).save("anim/faller.png")
# poço limpo: troca os píxeis do boneco pela escuridão envolvente (média radial)
big = ndimage.binary_dilation(keep > 0, iterations=20)
clean = im.copy(); sub = clean[Y0:Y1, X0:X1]
bg = ndimage.median_filter(np.where(big[..., None], np.nan, sub), size=1)
ring = ndimage.binary_dilation(big, iterations=12) & ~big
col = sub[ring].mean(0)
blur = np.array(Image.fromarray(np.where(big[..., None], col, sub).astype(np.uint8)).filter(ImageFilter.GaussianBlur(25)), np.float32)
w = np.array(Image.fromarray((big * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255
clean[Y0:Y1, X0:X1] = sub * (1 - w) + blur * w
Image.fromarray(clean.astype(np.uint8)).save("anim/yard_clean.png")
