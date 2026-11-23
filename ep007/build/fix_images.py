"""Limpeza por código (0 créditos):
1) equator.png: a v1 trazia o astronauta da imagem de referência (EP003) no céu; apaga-o com interpolação
   horizontal linha a linha (o céu é um gradiente liso).
2) thumb_bg_clean.png: a capa tinha um terceiro braço a apontar; apagado da mesma forma."""
import numpy as np
from PIL import Image

def fill_rows(a, mask):
    out = a.copy().astype(float)
    for y in range(a.shape[0]):
        m = mask[y]
        if not m.any(): continue
        xs = np.flatnonzero(~m)
        for c in range(3):
            out[y, m, c] = np.interp(np.flatnonzero(m), xs, out[y, xs, c])
    return out.clip(0, 255).astype(np.uint8)

a = np.array(Image.open("anim/equator_v1_astronauta.png").convert("RGB")).astype(float)
H, W, _ = a.shape
# o halo do astronauta escurece meio céu: substituir o céu à esquerda da linha (y<1780) pela mediana
# de cada linha do lado direito limpo (x 850-1300), com transição suave junto à linha prateada
med = np.median(a[:1780, 850:1300], axis=1)            # (1780, 3)
b = a.copy()
w = np.clip((750 - np.arange(W)) / 6.0, 0, 1)[None, :, None]   # 1 à esquerda, 0 a partir de x=750 (linha em 752-784)
b[:1780] = a[:1780] * (1 - w) + med[:, None, :] * w
# transição vertical para y 1700-1780
v = np.clip((1780 - np.arange(1780)) / 80.0, 0, 1)[:, None, None]
b[:1780] = a[:1780] + (b[:1780] - a[:1780]) * v
b = b.clip(0, 255).astype(np.uint8)
Image.fromarray(b).save("anim/equator.png")

t = np.array(Image.open("anim/thumb_bg.png").convert("RGB")).astype(int)
H, W, _ = t.shape
yy, xx = np.mgrid[0:H, 0:W]
r, g, bb = t[..., 0], t[..., 1], t[..., 2]
skin = (r > 170) & (g > 120) & (g < 215) & (bb < 190) & (r - bb > 40)
navy = (bb > r + 8) & (r < 90)
region = (xx > 690) & (xx < 880) & (yy > 1720) & (yy < 2150)
tmask = region & (skin | navy)
# dilatar
from scipy.ndimage import binary_dilation, binary_fill_holes
tmask = binary_fill_holes(binary_dilation(tmask, iterations=6)) & region
# à esquerda do braço está o cabelo (escuro): preencher cada linha com o píxel à direita (céu/prédio ao fundo)
tt = t.astype(np.uint8).copy()
for y in range(H):
    m = tmask[y]
    if not m.any(): continue
    xr = np.flatnonzero(m).max() + 3
    tt[y, m] = t[y, xr]
Image.fromarray(tt).save("anim/thumb_bg_clean.png")
print("ok", tmask.sum())
