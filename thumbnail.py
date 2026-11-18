#!/usr/bin/env python3
"""Whatifaholic — miniatura (thumbnail) de um Short, por código (0 créditos).

Regras de clique aplicadas:
  * 1 sujeito grande e legível (zoom na ilustração), fundo escurecido nas bordas;
  * 2–4 palavras enormes, maiúsculas, amarelo/branco com contorno preto grosso;
  * 1 etiqueta de urgência/número (ex.: "24H LEFT") num bloco vermelho;
  * tudo dentro do quadrado central (os ecrãs de canal/pesquisa cortam o 9:16);
  * cores saturadas e contraste alto (lê-se num telemóvel a 2 cm de largura).

Uso:
  python3 thumbnail.py --image ep002/anim/robot_desk.png --focus 0.66 0.42 --zoom 1.9 \
      --top "AI TOOK" --bottom "YOUR JOB" --tag "24H LEFT" --out ep002/publish/thumbnail.jpg
"""
import argparse
import cairo
import numpy as np
from PIL import Image, ImageEnhance

W, H = 1080, 1920
YELLOW, WHITE, RED, BLACK = (1.0, 0.86, 0.1), (1, 1, 1), (0.93, 0.13, 0.17), (0, 0, 0)


def fit(ctx, s, size, maxw):
    ctx.select_font_face("Inter Display", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    while True:
        ctx.set_font_size(size)
        if ctx.text_extents(s)[2] <= maxw or size < 40:
            return size
        size -= 4


def big(ctx, s, cy, size, col, maxw=980, rot=0.0):
    size = fit(ctx, s, size, maxw)
    xb, yb, tw, th, _, _ = ctx.text_extents(s)
    ctx.save(); ctx.translate(W / 2, cy); ctx.rotate(rot)
    ctx.move_to(-tw / 2 - xb, th / 2); ctx.text_path(s)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgb(*BLACK); ctx.set_line_width(size * 0.22); ctx.stroke_preserve()
    ctx.set_source_rgb(*col); ctx.fill()
    ctx.restore()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--focus", nargs=2, type=float, default=(0.5, 0.45), help="centro do sujeito (fração x y)")
    ap.add_argument("--zoom", type=float, default=1.6)
    ap.add_argument("--top", required=True)
    ap.add_argument("--bottom", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    im = Image.open(a.image).convert("RGB")
    im = ImageEnhance.Color(im).enhance(1.35)
    im = ImageEnhance.Contrast(im).enhance(1.2)
    k = max(W / im.width, H / im.height) * a.zoom
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    cx, cy = a.focus[0] * im.width, a.focus[1] * im.height
    x0 = int(min(max(cx - W / 2, 0), im.width - W)); y0 = int(min(max(cy - H / 2, 0), im.height - H))
    im = im.crop((x0, y0, x0 + W, y0 + H))
    arr = np.dstack([np.array(im)[:, :, ::-1], np.full((H, W), 255, np.uint8)]).copy()
    bg = cairo.ImageSurface.create_for_data(arr, cairo.FORMAT_ARGB32, W, H)

    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(out)
    ctx.set_source_surface(bg, 0, 0); ctx.paint()
    g = cairo.RadialGradient(W / 2, H / 2, W * 0.35, W / 2, H / 2, H * 0.62)  # vinheta
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.75)
    ctx.set_source(g); ctx.paint()
    for y0_, y1_ in ((0, 0.42), (1, 0.58)):  # faixas escuras atrás do texto
        lg = cairo.LinearGradient(0, H * y0_, 0, H * y1_)
        lg.add_color_stop_rgba(0, 0, 0, 0, 0.7); lg.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(lg); ctx.paint()

    big(ctx, a.top, 560, 210, YELLOW)
    if a.bottom:
        big(ctx, a.bottom, 1400, 210, WHITE)
    if a.tag:
        size = fit(ctx, a.tag, 96, 760)
        tw = ctx.text_extents(a.tag)[2]
        ctx.save(); ctx.translate(W / 2, 760); ctx.rotate(-0.05)
        ctx.set_source_rgb(*RED); ctx.rectangle(-tw / 2 - 36, -size * 0.85, tw + 72, size * 1.25); ctx.fill()
        ctx.set_source_rgb(*WHITE); ctx.move_to(-tw / 2 - ctx.text_extents(a.tag)[0], size * 0.25)
        ctx.show_text(a.tag); ctx.restore()

    data = np.ndarray((H, W, 4), np.uint8, out.get_data())[:, :, [2, 1, 0]]
    Image.fromarray(data.copy()).save(a.out, quality=90, optimize=True)
    print("OK", a.out)


if __name__ == "__main__":
    main()
