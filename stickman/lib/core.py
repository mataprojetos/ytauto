"""Base partilhada dos vídeos stickman: tamanho, fontes, easing, curvas, texto e saída ffmpeg."""
import math
import os
import shutil
import subprocess

import cairo
import numpy as np

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "Oswald"


def ensure_font():
    """Instala a Oswald Bold (OFL) do repositório em ~/.fonts para o cairo a encontrar."""
    dst = os.path.expanduser("~/.fonts/Oswald-Bold.ttf")
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(HERE, "fonts", "Oswald-Bold.ttf"), dst)
        subprocess.run(["fc-cache", "-f"], check=False)


# ---------- matemática ----------
def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ramp(t, t0, t1):
    """0 antes de t0, 1 depois de t1, suave no meio."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return smooth((t - t0) / (t1 - t0))


def window(t, t0, t1, fade=0.18):
    """1 dentro de [t0,t1] com fades rápidos nas pontas."""
    return min(ramp(t, t0, t0 + fade), 1 - ramp(t, t1 - fade, t1))


def pchip(keys):
    """Curva monótona (Fritsch–Carlson) por chaves [(t, v), ...] -> função f(t)."""
    ts = np.array([k[0] for k in keys], float)
    vs = np.array([k[1] for k in keys], float)
    n = len(ts)
    if n == 1:
        return lambda t: float(vs[0])
    h = np.diff(ts)
    d = np.diff(vs) / h
    m = np.zeros(n)
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(t):
        if t <= ts[0]:
            return float(vs[0])
        if t >= ts[-1]:
            return float(vs[-1])
        i = int(np.searchsorted(ts, t) - 1)
        s = (t - ts[i]) / h[i]
        h00 = 2 * s**3 - 3 * s**2 + 1
        h10 = s**3 - 2 * s**2 + s
        h01 = -2 * s**3 + 3 * s**2
        h11 = s**3 - s**2
        return float(h00 * vs[i] + h10 * h[i] * m[i] + h01 * vs[i + 1] + h11 * h[i] * m[i + 1])

    return f


# ---------- texto ----------
def text_width(ctx, text, size, spacing=0.0):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    w = 0.0
    for ch in text:
        w += ctx.text_extents(ch).x_advance + spacing
    return w - spacing if text else 0.0


def draw_text(ctx, text, x, y, size, rgba, spacing=0.0, align="left", jitter=None):
    """Texto Oswald Bold com espaçamento entre letras. y = linha de base.
    jitter: função(i) -> (dx, dy) para letras a tremer."""
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    w = text_width(ctx, text, size, spacing)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    ctx.set_source_rgba(*rgba)
    for i, ch in enumerate(text):
        dx, dy = jitter(i) if jitter else (0, 0)
        ctx.move_to(x + dx, y + dy)
        ctx.show_text(ch)
        x += ctx.text_extents(ch).x_advance + spacing
    return w


# ---------- saída ----------
class Writer:
    """Envia frames cairo (ARGB32) ao ffmpeg -> H.264 30 fps com faixa de áudio silenciosa."""

    def __init__(self, path, silent_audio=True, crf=19):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        if silent_audio:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                    "-c:a", "aac", "-b:a", "64k"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", path]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, surface):
        surface.flush()
        self.p.stdin.write(bytes(surface.get_data()))

    def close(self):
        self.p.stdin.close()
        self.p.wait()
