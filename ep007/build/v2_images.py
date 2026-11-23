# ---------- imagens em camadas (parallax 2.5D a partir de mapas de profundidade) ----------
# Cada ilustração é cortada em 4 camadas pela profundidade (build/depth.py, Depth Anything V2 Small).
# As camadas de trás têm os objetos da frente "apagados" (preenchimento pull-push), para que, quando a
# camada da frente se mexe mais do que a de trás, não apareçam duplicados.
_KEEP = []
NL = 4


def _pool(a):
    h, w = a.shape[:2]
    a = a[:h - h % 2, :w - w % 2]
    return 0.25 * (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2])


def _fill(img, w):
    """preenche os píxeis com peso 0 a partir dos vizinhos (pirâmide pull-push), a 1/4 da resolução"""
    small = np.array(Image.fromarray(img.astype(np.uint8)).resize((img.shape[1] // 4, img.shape[0] // 4), Image.BILINEAR), np.float32)
    ws = np.array(Image.fromarray((w * 255).astype(np.uint8)).resize((img.shape[1] // 4, img.shape[0] // 4), Image.BILINEAR), np.float32) / 255
    A, Wt = [small * ws[..., None]], [ws]
    while min(A[-1].shape[:2]) > 4:
        A.append(_pool(A[-1])); Wt.append(_pool(Wt[-1]))
    col = A[-1] / np.maximum(Wt[-1], 1e-4)[..., None]
    for a, wt in zip(reversed(A[:-1]), reversed(Wt[:-1])):
        up = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((a.shape[1], a.shape[0]), Image.BILINEAR), np.float32)
        own = a / np.maximum(wt, 1e-4)[..., None]
        k = np.clip(wt * 4, 0, 1)[..., None]
        col = own * k + up * (1 - k)
    return np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((img.shape[1], img.shape[0]), Image.BILINEAR), np.float32)


def _surf(rgb, alpha):
    h, w = alpha.shape
    buf = np.zeros((h, w, 4), np.uint8)
    pm = rgb * alpha[..., None]
    buf[..., 0] = pm[..., 2]; buf[..., 1] = pm[..., 1]; buf[..., 2] = pm[..., 0]; buf[..., 3] = alpha * 255
    s = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h)
    _KEEP.append(buf)
    return s


def load_layers(name):
    im = np.array(Image.open(f"{ROOT}/anim/{name}.png").convert("RGB"), np.float32)
    d = np.array(Image.open(f"{ROOT}/anim/{name}_depth.png").convert("L"), np.float32) / 255
    ths = [0.0] + list(np.quantile(d, [0.5, 0.75, 0.9]))
    out = []
    for k in range(NL):
        alpha = np.ones_like(d) if k == 0 else np.clip((d - ths[k]) / 0.025 + 0.5, 0, 1)
        if k < NL - 1:
            keep = (d < ths[k + 1] - 0.01).astype(np.float32)
            rgb = im * keep[..., None] + _fill(im, keep) * (1 - keep[..., None])
        else:
            rgb = im
        out.append(_surf(rgb, alpha))
    return out


NAMES = ("city", "europe", "night", "bedroom", "equator", "winter", "sunset", "ordovician")
LAY = {}


def layers(name):
    if name not in LAY: LAY[name] = load_layers(name)
    return LAY[name]


def draw_par(c, name, zoom, fx, fy, px=0.0, py=0.0, push=0.0, a=1.0):
    """ilustração em camadas: zoom e ponto focal como numa câmara; px/py = deslocamento (px de ecrã) da camada
    mais próxima (as outras deslocam-se proporcionalmente); push = zoom extra da camada mais próxima (dolly)."""
    L = layers(name)
    iw, ih = L[0].get_width(), L[0].get_height()
    base = max(W / iw, H / ih) * zoom * 1.06            # margem para o parallax não mostrar bordas
    vw, vh = W / base, H / base
    x0 = clamp(fx * iw - vw / 2, 0, iw - vw); y0 = clamp(fy * ih - vh / 2, 0, ih - vh)
    for k, s in enumerate(L):
        f = k / (NL - 1)
        sc = 1 + push * f
        c.save(); c.translate(W / 2 + px * f, H / 2 + py * f); c.scale(sc, sc); c.translate(-W / 2, -H / 2)
        c.scale(base, base); c.translate(-x0, -y0)
        c.set_source_surface(s, 0, 0); c.get_source().set_filter(cairo.FILTER_GOOD)
        c.paint_with_alpha(a); c.restore()
    return base, x0, y0


