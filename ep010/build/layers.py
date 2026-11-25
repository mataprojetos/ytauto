"""EP010 v2 (pedido do dono: mais profundidade): separa cada ilustração em 3 camadas recortadas
  L0 = fundo (espaço/estrelas, objetos removidos e preenchidos, ligeiramente desfocado)
  L1 = objetos (asteroide, Terra, nave, foguetes), personagem removida e preenchida por baixo
  L2 = personagem (rapaz de capuz)
Máscaras: saliência (rembg isnet, anim/*_mask.png) + GrabCut com caixas da personagem.
Uso: python3 build/layers.py  → anim/<nome>_L0.png, _L1.png, _L2.png"""
import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage
sys.path.insert(0, "build")
# caixas da personagem (frações x0,y0,x1,y1) e zonas que de certeza NÃO são a personagem (elipses cx,cy,rx,ry)
CFG = {
    "a1_panico":   dict(box=(0.30, 0.375, 0.70, 0.85), notc=[(0.48, 0.22, 0.30, 0.15), (0.5, 0.93, 0.6, 0.07), (0.5, 0.76, 0.035, 0.05)],
                        fg=[], earth=0.79),
    "a2_genio":    dict(box=(0.25, 0.25, 0.90, 0.82), notc=[(0.27, 0.22, 0.22, 0.10), (0.5, 0.99, 0.6, 0.08)],
                        fg=[(0.41, 0.64, 0.022, 0.06), (0.52, 0.66, 0.022, 0.08)], earth=0.85),
    "a3_foguetes": dict(box=(0.32, 0.12, 0.68, 0.56), notc=[(0.5, 0.72, 0.40, 0.17), (0.37, 0.535, 0.05, 0.03), (0.65, 0.535, 0.04, 0.03), (0.505, 0.55, 0.022, 0.02)],
                        fg=[], earth=None),
    "a4_pintar":   dict(box=(0.33, 0.18, 0.86, 0.68), notc=[(0.25, 0.66, 0.25, 0.14), (0.45, 0.82, 0.4, 0.06), (0.40, 0.52, 0.075, 0.14), (0.555, 0.62, 0.02, 0.04)],
                        fg=[], earth=None),
    "a5_impacto":  dict(box=(0.04, 0.52, 0.82, 0.95), notc=[(0.70, 0.43, 0.20, 0.09), (0.52, 0.18, 0.30, 0.08)], fg=[], earth=None),
    "a6_alivio":   dict(box=(0.22, 0.23, 0.88, 0.82), notc=[(0.88, 0.22, 0.12, 0.09), (0.5, 0.93, 0.6, 0.08)],
                        fg=[(0.55, 0.62, 0.08, 0.025), (0.50, 0.70, 0.03, 0.05), (0.62, 0.70, 0.03, 0.05)], earth=0.575),
}


def fill(img, keep):
    """preenche onde keep=0 a partir dos vizinhos (pirâmide pull-push)"""
    img = img.astype(np.float32); w = keep.astype(np.float32)
    A, Wt = [img * w[..., None]], [w]
    while min(A[-1].shape[:2]) > 4:
        a, ww = A[-1], Wt[-1]
        h, wd = a.shape[0] // 2 * 2, a.shape[1] // 2 * 2
        A.append(a[:h, :wd].reshape(h // 2, 2, wd // 2, 2, 3).sum((1, 3)))
        Wt.append(ww[:h, :wd].reshape(h // 2, 2, wd // 2, 2).sum((1, 3)))
    col = A[-1] / np.maximum(Wt[-1], 1e-6)[..., None]
    for a, ww in zip(reversed(A[:-1]), reversed(Wt[:-1])):
        up = cv2.resize(col, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_LINEAR)
        k = np.clip(ww, 0, 1)[..., None]
        col = a / np.maximum(ww, 1e-6)[..., None] * k + up * (1 - k)
    return col


for name, cf in CFG.items():
    im = np.array(Image.open(f"anim/{name}.png").convert("RGB"))
    H, W = im.shape[:2]
    S = np.array(Image.open(f"anim/{name}_mask.png").convert("L"), np.float32) / 255
    # GrabCut a 1/2 resolução
    sc = 0.5; hs, ws = int(H * sc), int(W * sc)
    small = cv2.resize(im, (ws, hs), interpolation=cv2.INTER_AREA)
    Ss = cv2.resize(S, (ws, hs))
    gc = np.full((hs, ws), cv2.GC_BGD, np.uint8)
    x0, y0, x1, y1 = [int(v * (ws if i % 2 == 0 else hs)) for i, v in enumerate(cf["box"])]
    box = np.zeros((hs, ws), bool); box[y0:y1, x0:x1] = True
    gc[box & (Ss > 0.5)] = cv2.GC_PR_FGD
    gc[box & (Ss <= 0.5)] = cv2.GC_PR_BGD
    yy, xx = np.mgrid[0:hs, 0:ws]
    for (cx, cy, rx, ry) in cf["notc"]:
        e = ((xx - cx * ws) / (rx * ws)) ** 2 + ((yy - cy * hs) / (ry * hs)) ** 2 < 1
        gc[e] = cv2.GC_BGD
    # núcleo seguro: centro da caixa com saliência alta
    cxb, cyb = (x0 + x1) // 2, (y0 + y1) // 2
    core = box & (Ss > 0.9) & (abs(xx - cxb) < (x1 - x0) * 0.12) & (abs(yy - cyb) < (y1 - y0) * 0.3)
    gc[core] = cv2.GC_FGD
    for (cx, cy, rx, ry) in cf["fg"]:
        e = ((xx - cx * ws) / (rx * ws)) ** 2 + ((yy - cy * hs) / (ry * hs)) ** 2 < 1
        gc[e] = cv2.GC_FGD
    bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(cv2.cvtColor(small, cv2.COLOR_RGB2BGR), gc, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    C = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)
    # maior componente ligada + componentes grandes perto dela
    lab, n = ndimage.label(C)
    if n > 1:
        sizes = ndimage.sum(C, lab, range(1, n + 1))
        keep = [i + 1 for i, s in enumerate(sizes) if s > sizes.max() * 0.04]
        C = np.isin(lab, keep).astype(np.uint8)
    C = ndimage.binary_fill_holes(C).astype(np.float32)
    C = cv2.resize(C, (W, H), interpolation=cv2.INTER_LINEAR)
    C = cv2.GaussianBlur(np.clip((C - 0.5) * 3 + 0.5, 0, 1), (0, 0), 1.2)
    Sf = cv2.GaussianBlur(np.clip((S - 0.5) * 3 + 0.5, 0, 1), (0, 0), 1.2)
    if cf["earth"]:   # a Terra (em baixo) entra na camada dos objetos
        v = cv2.cvtColor(im, cv2.COLOR_RGB2HSV)[..., 2].astype(np.float32)
        E = ((v > 80) & (np.arange(H)[:, None] > cf["earth"] * H)).astype(np.uint8)
        E = cv2.morphologyEx(E, cv2.MORPH_OPEN, np.ones((9, 9))); lab, n = ndimage.label(E)
        if n: E = (lab == (np.argmax(ndimage.sum(E, lab, range(1, n + 1))) + 1))
        E = ndimage.binary_fill_holes(E).astype(np.float32)
        S = np.maximum(S, cv2.GaussianBlur(E, (0, 0), 1.5))
        Sf = cv2.GaussianBlur(np.clip((S - 0.5) * 3 + 0.5, 0, 1), (0, 0), 1.2)
    Sf = np.maximum(Sf, C)
    # L0: fundo sem objetos, desfocado (profundidade de campo)
    keep0 = cv2.dilate((Sf < 0.05).astype(np.uint8), None, iterations=0) * (cv2.dilate((Sf > 0.05).astype(np.uint8), np.ones((9, 9))) == 0)
    L0 = fill(im, keep0)
    L0 = cv2.GaussianBlur(L0, (0, 0), 3.0)
    # L1: objetos, com a personagem preenchida por baixo
    notC = (cv2.dilate((C > 0.05).astype(np.uint8), np.ones((15, 15))) == 0)
    L1rgb = fill(im, notC * (Sf > 0.5))
    L1rgb = np.where(notC[..., None], im, L1rgb)
    a1 = np.clip(Sf, 0, 1)
    obj = np.clip(Sf - C, 0, 1)
    a1 = np.maximum(obj, C * (cv2.GaussianBlur(obj, (0, 0), 25) > 0.08))   # por baixo da personagem só onde havia objeto à volta
    def save(rgb, a, fn):
        out = np.dstack([np.clip(rgb, 0, 255), np.clip(a * 255, 0, 255)]).astype(np.uint8)
        Image.fromarray(out, "RGBA").save(fn)
    save(L0, np.ones((H, W)), f"anim/{name}_L0.png")
    save(L1rgb, a1, f"anim/{name}_L1.png")
    save(im.astype(np.float32), C, f"anim/{name}_L2.png")
    print(name, "ok", round(C.mean(), 3), round(obj.mean(), 3))
