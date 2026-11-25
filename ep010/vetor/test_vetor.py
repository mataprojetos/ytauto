"""EP010 · teste em animação vetorial por código (pedido do dono: estilo mais adulto, tipo motion design; tudo a mexer;
personagem pequena e o perigo enorme). Gancho: o asteroide em chamas a chegar à Terra, o rapaz de capuz em cima do horizonte."""
import math, random, subprocess, os, sys
import cairo, numpy as np
W, H, FPS = 1080, 1920, 30
DUR = 4.6
HERE = os.path.dirname(os.path.abspath(__file__))

def hexc(h, a=1.0):
    h = h.lstrip("#"); return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k

# paleta (sóbria, motion design)
SPACE_TOP, SPACE_BOT = hexc("#0b1026"), hexc("#1b1440")
OCEAN, OCEAN_D, LAND, LAND_D = hexc("#1f6fb2"), hexc("#134a7c"), hexc("#3f9b6b"), hexc("#2b7353")
HOOD, HOOD_D, JEANS, JEANS_D, SKIN, SKIN_D, HAIR, SHOE = (hexc(x) for x in ("#8b5a7c", "#6a4060", "#2f4572", "#22345a", "#f0c39e", "#d29a7a", "#4a2c1a", "#7a2230"))
ROCK, ROCK_L, ROCK_D = hexc("#6e6f76"), hexc("#a9abb2"), hexc("#3a3b42")
FIRE1, FIRE2, FIRE3 = hexc("#ff4d1f"), hexc("#ff9a2e"), hexc("#ffe08a")

rnd = random.Random(7)
STARS = [(rnd.random() * W, rnd.random() * H, rnd.choice((0.3, 0.6, 1.0)), rnd.random() * 6.28, rnd.random()) for _ in range(260)]
grain = (np.random.default_rng(1).random((H // 2, W // 2)) * 255).astype(np.uint8)

def blob(c, cx, cy, r, n, seed, wob=0.35):
    rr = random.Random(seed); pts = []
    for i in range(n):
        a = i / n * 6.283; k = 1 + wob * (rr.random() - 0.5)
        pts.append((cx + math.cos(a) * r * k, cy + math.sin(a) * r * k))
    c.move_to(*(((pts[-1][0] + pts[0][0]) / 2), ((pts[-1][1] + pts[0][1]) / 2)))
    for i in range(n):
        p, q = pts[i], pts[(i + 1) % n]
        c.curve_to(p[0], p[1], p[0], p[1], (p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    c.close_path()

def glow(c, x, y, r, col, a):
    g = cairo.RadialGradient(x, y, 0, x, y, r); g.add_color_stop_rgba(0, *col[:3], a); g.add_color_stop_rgba(1, *col[:3], 0)
    c.set_source(g); c.arc(x, y, r, 0, 6.283); c.fill()

# ---------- Terra ----------
CONT = [(rnd.uniform(0, 6.283), rnd.uniform(-0.5, 0.5), rnd.uniform(0.18, 0.4), rnd.randint(0, 999)) for _ in range(9)]
def earth(c, cx, cy, R, rot, light=(-0.5, -0.8)):
    c.save(); c.arc(cx, cy, R, 0, 6.283); c.clip()
    c.set_source_rgba(*OCEAN); c.paint()
    for i, (lon, lat, s, sd) in enumerate(CONT):
        span = 2600
        px = cx - span / 2 + ((lon / 6.283) * span + rot * 900) % span
        py = cy - R + 120 + (lat + 0.5) * 420
        rr = s * 420
        c.save(); c.translate(px, py); c.scale(1, 0.55)
        c.set_source_rgba(*LAND); blob(c, 0, 0, rr, 10, sd, 0.6); c.fill()
        c.set_source_rgba(*LAND_D); blob(c, rr * 0.2, rr * 0.25, rr * 0.6, 8, sd + 1, 0.6); c.fill()
        c.restore()
    c.set_source_rgba(1, 1, 1, 0.22)   # nuvens finas
    for i in range(6):
        px = (i * 430 + rot * 1300) % 2600 + cx - 1300; py = cy - R + 90 + (i % 3) * 140
        c.save(); c.translate(px, py); c.scale(1, 0.25); blob(c, 0, 0, 160, 9, 300 + i, 0.5); c.restore(); c.fill()
    # sombra do lado escuro (terminador)
    g = cairo.LinearGradient(cx + light[0] * R, cy + light[1] * R, cx - light[0] * R, cy - light[1] * R)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(0.55, 0, 0, 0, 0.05); g.add_color_stop_rgba(1, 0.02, 0.02, 0.1, 0.75)
    c.set_source(g); c.paint()
    c.restore()
    # atmosfera
    for i in range(3):
        c.set_source_rgba(0.45, 0.75, 1.0, 0.18 - i * 0.05); c.set_line_width(14 + i * 22); c.arc(cx, cy, R + 6 + i * 10, 0, 6.283); c.stroke()

# ---------- asteroide (low-poly com facetas e crateras) ----------
AP = [(i / 15 * 6.283, 1 + 0.22 * (random.Random(i * 3 + 1).random() - 0.5)) for i in range(15)]
CRAT = [(random.Random(50 + i).uniform(-0.55, 0.55), random.Random(80 + i).uniform(-0.55, 0.55), random.Random(90 + i).uniform(0.08, 0.2)) for i in range(7)]
def asteroid(c, cx, cy, R, rot, heat=0.0):
    pts = [(cx + math.cos(a + rot) * R * k, cy + math.sin(a + rot) * R * k) for a, k in AP]
    def path():
        c.move_to((pts[-1][0] + pts[0][0]) / 2, (pts[-1][1] + pts[0][1]) / 2)
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            c.curve_to(p[0], p[1], p[0], p[1], (p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        c.close_path()
    path(); c.set_source_rgba(*ROCK); c.fill()
    c.save(); path(); c.clip()
    # planos grandes de luz (lado do fogo, cima-direita) e de sombra (baixo-esquerda)
    c.set_source_rgba(*ROCK_L[:3], 0.9); blob(c, cx + R * 0.35, cy - R * 0.35, R * 0.85, 9, 5, 0.3); c.fill()
    c.set_source_rgba(0.85, 0.86, 0.9, 0.25); blob(c, cx + R * 0.55, cy - R * 0.55, R * 0.45, 8, 6, 0.3); c.fill()
    c.set_source_rgba(*ROCK_D[:3], 0.85); blob(c, cx - R * 0.55, cy + R * 0.5, R * 0.9, 9, 7, 0.3); c.fill()
    for (u, v, s) in CRAT:   # crateras: cova escura + sombra interior + borda clara do lado da luz
        a = math.atan2(v, u) + rot; d = math.hypot(u, v) * R
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d; r = s * R
        c.save(); c.translate(x, y); c.rotate(rot * 0.3)
        c.set_source_rgba(0.8, 0.82, 0.88, 0.35); c.save(); c.scale(1, 0.82); c.arc(r * 0.12, -r * 0.12, r * 1.12, 0, 6.283); c.restore(); c.fill()
        c.set_source_rgba(*ROCK_D[:3], 1); c.save(); c.scale(1, 0.82); c.arc(0, 0, r, 0, 6.283); c.restore(); c.fill()
        c.set_source_rgba(0.08, 0.08, 0.1, 0.6); c.save(); c.scale(1, 0.82); c.arc(-r * 0.25, r * 0.2, r * 0.7, 0, 6.283); c.restore(); c.fill()
        c.restore()
    if heat > 0:   # borda incandescente DENTRO da silhueta (a face que rasga o ar)
        g = cairo.RadialGradient(cx - R * 0.1, cy - R * 0.2, R * 0.55, cx, cy, R * 1.15)
        g.add_color_stop_rgba(0, 1, 0.5, 0.1, 0); g.add_color_stop_rgba(1, 1, 0.5, 0.12, 0.7 * heat)
        c.set_source(g); c.paint()
    c.restore()

def corona(c, cx, cy, R, t, heat=1.0):
    """asteroide quase de frente: cauda de fogo ESTREITA e curta a espreitar por trás (cima-direita) + brilho quente"""
    glow(c, cx, cy, R * 1.35, FIRE1, 0.22 * heat)
    ang = -0.8; ux, uy = math.cos(ang), math.sin(ang); vx, vy = -uy, ux
    for k, (col, wk, lk) in enumerate(((FIRE1, 0.78, 1.9), (FIRE2, 0.6, 1.55), (FIRE3, 0.38, 1.15))):
        n = 16; L = R * lk * heat; pts_a, pts_b = [], []
        for i in range(n + 1):
            s = i / n; wob = math.sin(s * 10 - t * 16 + k * 1.7) * 0.07 * s * R
            w = R * wk * (1 - s) ** 1.3
            pts_a.append((cx + ux * L * s + vx * (w + wob), cy + uy * L * s + vy * (w + wob)))
            pts_b.append((cx + ux * L * s - vx * (w - wob), cy + uy * L * s - vy * (w - wob)))
        c.move_to(*pts_a[0])
        for pp in pts_a[1:]: c.line_to(*pp)
        for pp in reversed(pts_b): c.line_to(*pp)
        c.close_path(); c.set_source_rgba(*col[:3], 0.92); c.fill()
    for i in range(10):   # faúlhas finas a soltar-se da cauda
        rr = random.Random(400 + i); ph = (t * (1.2 + rr.random()) + rr.random()) % 1
        s = 0.3 + ph * 1.4; off = (rr.random() - 0.5) * R * 0.9
        x, y = cx + ux * R * s * 1.6 + vx * off, cy + uy * R * s * 1.6 + vy * off
        c.set_source_rgba(1, 0.75, 0.3, (1 - ph) * 0.9); c.arc(x, y, R * 0.025 * (1 - ph) + 1.5, 0, 6.283); c.fill()


def rim_heat(c, cx, cy, R, heat):
    """borda incandescente do lado de baixo (a face que rasga o ar)"""
    g = cairo.RadialGradient(cx, cy - R * 0.25, R * 0.75, cx, cy, R * 1.02)
    g.add_color_stop_rgba(0, 1, 0.5, 0.1, 0); g.add_color_stop_rgba(1, 1, 0.55, 0.15, 0.75 * heat)
    c.set_source(g); c.arc(cx, cy, R * 1.02, 0, 6.283); c.fill()


# ---------- personagem (proporções normais, pequena na cena) ----------
def guy(c, x, y, s, t, arms=0.0, look=0.0, lean=0.0, shake=0.0, rim=0.0):
    """x,y = pés; s = altura em px. arms 0 (em baixo) → 1 (mãos na cabeça); look 0 (frente) → 1 (a olhar para cima à direita)"""
    c.save(); c.translate(x + shake * math.sin(t * 55), y); c.rotate(lean); u = s / 100.0; c.scale(u, u)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    # sombra no chão
    c.save(); c.scale(1, 0.18); c.set_source_rgba(0, 0, 0, 0.35); c.arc(0, 0, 22, 0, 6.283); c.fill(); c.restore()
    # pernas
    for sx in (-1, 1):
        c.set_source_rgba(*JEANS); c.set_line_width(9); c.move_to(5 * sx, -42); c.line_to(6 * sx, -6); c.stroke()
        c.set_source_rgba(*SHOE); c.save(); c.translate(7 * sx, -3); c.scale(1.6, 0.8); c.arc(0, 0, 5, 0, 6.283); c.restore(); c.fill()
    # braços (atrás do corpo o esquerdo)
    def arm(sx, front):
        sh = (11 * sx, -68)
        a_up = lerp(0.15, 2.5, arms)   # ângulo a partir de baixo
        el = (sh[0] + math.sin(a_up * 0.55) * 14 * sx, sh[1] + math.cos(a_up * 0.55) * 16)
        ha = (lerp(el[0] + 2 * sx, 7 * sx, arms), lerp(el[1] + 16, -86, arms))
        c.set_source_rgba(*(HOOD if front else HOOD_D)); c.set_line_width(8)
        c.move_to(*sh); c.line_to(*el); c.line_to(*ha); c.stroke()
        c.set_source_rgba(*SKIN); c.arc(ha[0], ha[1], 4.2, 0, 6.283); c.fill()
    arm(-1, False)
    # tronco (capuz)
    c.set_source_rgba(*HOOD); c.move_to(-14, -44); c.curve_to(-16, -60, -14, -72, 0, -74); c.curve_to(14, -72, 16, -60, 14, -44); c.close_path(); c.fill()
    c.set_source_rgba(*HOOD_D); c.move_to(4, -44); c.curve_to(10, -58, 12, -70, 0, -74); c.curve_to(14, -72, 16, -60, 14, -44); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.85); c.set_line_width(1.2)
    for sx in (-1, 1): c.move_to(3 * sx, -70); c.line_to(3.5 * sx, -60); c.stroke()
    if rim > 0:   # contraluz quente do fogo (lado direito)
        c.set_source_rgba(1, 0.6, 0.25, 0.6 * rim); c.set_line_width(2.4); c.move_to(14, -46); c.curve_to(16, -60, 14, -72, 2, -74); c.stroke()
    arm(1, True)
    # cabeça
    c.save(); c.translate(0, -84); c.rotate(-0.35 * look)
    c.set_source_rgba(*SKIN); c.arc(0, 0, 10.5, 0, 6.283); c.fill()
    c.set_source_rgba(*SKIN_D); c.arc(0, 0, 10.5, -1.2, 1.2); c.arc_negative(-3, 0, 10.5, 1.0, -1.0); c.close_path(); c.fill()
    c.set_source_rgba(*HAIR); c.move_to(-11, -1); c.curve_to(-12, -14, 10, -16, 11, -3)
    for i in range(5): c.line_to(8 - i * 4, -12 - (i % 2) * 4)
    c.close_path(); c.fill()
    ey = -1 - 2.5 * look
    c.set_source_rgba(0.08, 0.06, 0.06, 1)
    for sx in (-1, 1): c.arc(3.8 * sx + 1.5 * look, ey, 1.4, 0, 6.283); c.fill()
    c.set_line_width(1.1)
    for sx in (-1, 1): c.move_to(2 * sx + 1.5 * look, ey - 3.5 - arms * 1.2); c.line_to(5.5 * sx + 1.5 * look, ey - 3 - arms * 0.4 * sx); c.stroke()
    c.set_source_rgba(0.35, 0.08, 0.1, 1); c.save(); c.translate(1 * look, 5 - look); c.scale(1, 0.6 + 0.9 * arms); c.arc(0, 0, 2.2, 0, 6.283); c.restore(); c.fill()
    if rim > 0: c.set_source_rgba(1, 0.6, 0.25, 0.55 * rim); c.set_line_width(1.8); c.arc(0, 0, 10.5, -1.4, 0.6); c.stroke()
    c.restore(); c.restore()

def frame(t):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_GOOD)
    # câmara: aproxima devagar, deriva
    k = clamp(t / DUR) ** 2; z = 1.0 + 0.06 * smooth(t / DUR)
    dx = 14 * math.sin(t * 0.7) + 16 * k * math.sin(t * 61); dy = 8 * math.sin(t * 0.5) + 14 * k * math.cos(t * 53)
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgba(0, *SPACE_TOP); g.add_color_stop_rgba(1, *SPACE_BOT); c.set_source(g); c.paint()
    # nebulosa suave
    glow(c, 820 + dx * 0.2, 500, 700, hexc("#5a2a7a"), 0.25); glow(c, 200, 1100, 600, hexc("#1e3a7a"), 0.25)
    for (x, y, d, ph, b) in STARS:   # estrelas em 3 profundidades
        xx = (x + dx * d * 0.5 - t * 6 * d) % W; yy = (y + dy * d * 0.5) % H
        a = (0.35 + 0.5 * b) * (0.7 + 0.3 * math.sin(t * 2 + ph))
        c.set_source_rgba(1, 0.96, 0.9, a); c.arc(xx, yy, 0.8 + 1.6 * d * b, 0, 6.283); c.fill()
    c.save(); c.translate(W / 2 + dx, H / 2 + dy); c.scale(z, z); c.translate(-W / 2, -H / 2)
    # asteroide de frente: começa pequeno e longe e cresce em aceleração (vem contra a câmara)
    q = clamp(t / DUR)
    AR = 55 * math.exp(math.log(1150 / 55) * q ** 1.6)
    ax, ay = 560 + 30 * math.sin(t * 0.9), lerp(560, 760, q ** 2)
    heat = 0.6 + 0.4 * q
    # rastos de velocidade radiais (a câmara a ser "atravessada")
    for i in range(46):
        rr = random.Random(i); a = rr.random() * 6.283; ph = (t * (0.7 + rr.random()) + rr.random()) % 1
        d0 = AR * 1.2 + ph ** 2 * 1400; ln = 40 + ph * 260
        c.set_source_rgba(1, 0.85, 0.65, 0.35 * ph * (0.4 + q)); c.set_line_width(1 + ph * 3)
        c.move_to(ax + math.cos(a) * d0, ay + math.sin(a) * d0); c.line_to(ax + math.cos(a) * (d0 + ln), ay + math.sin(a) * (d0 + ln)); c.stroke()
    corona(c, ax, ay, AR, t, heat)
    asteroid(c, ax, ay, AR, t * 0.25, heat)
    # pedaços a passar pela câmara
    for i in range(22):
        rr = random.Random(200 + i); a = rr.random() * 6.283; ph = (t * (0.35 + rr.random() * 0.3) + rr.random()) % 1
        d = AR * (1.1 + ph ** 2 * 4.0); rs = (4 + rr.random() * 10) * (0.5 + ph * 3)
        x, y = ax + math.cos(a) * d, ay + math.sin(a) * d
        c.set_source_rgba(*ROCK[:3], 1); blob(c, x, y, rs, 6, 300 + i, 0.5); c.fill()
        c.set_source_rgba(*ROCK_D[:3], 1); blob(c, x - rs * 0.25, y + rs * 0.25, rs * 0.65, 6, 500 + i, 0.5); c.fill()
        c.set_source_rgba(1, 0.6, 0.2, 0.7); c.set_line_width(max(1, rs * 0.18)); c.arc(x, y, rs * 0.9, -2.0, -0.4); c.stroke()
    p = q
    # Terra (grande, em baixo) + luz quente do asteroide a crescer
    ER = 1900; ecx, ecy = 540, 1380 + ER
    earth(c, ecx, ecy, ER, t * 0.03)
    glow(c, ax, ecy - ER, 1100, FIRE2, 0.1 + 0.3 * p)
    # o rapaz, pequeno, em cima do horizonte
    arms = smooth((t - 1.3) / 0.8); look = smooth((t - 0.2) / 0.6)
    guy(c, 330, 1392, 185, t, arms=arms, look=look, lean=-0.08 * arms, shake=1.2 * arms, rim=0.4 + 0.6 * p)
    c.restore()
    # vinheta + grão
    vg = cairo.RadialGradient(W / 2, H / 2, 600, W / 2, H / 2, 1300); vg.add_color_stop_rgba(0, 0, 0, 0, 0); vg.add_color_stop_rgba(1, 0, 0, 0.05, 0.55)
    c.set_source(vg); c.paint()
    a = np.ndarray((H, W, 4), np.uint8, s.get_data())
    gr = np.repeat(np.repeat(np.roll(grain, int(t * 97) % 50, 1), 2, 0), 2, 1).astype(np.int16) - 128
    rgb = a[:, :, :3].astype(np.int16) + (gr[..., None] * 0.05).astype(np.int16)
    return np.clip(rgb, 0, 255).astype(np.uint8)[:, :, [2, 1, 0]].tobytes()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for tt in sys.argv[1].split(","):
            from PIL import Image
            Image.frombytes("RGB", (W, H), frame(float(tt))).save(f"{HERE}/v_{float(tt):.2f}.png")
        sys.exit()
    out = f"{HERE}/teste_vetor_gancho.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", f"{HERE}/../audio/narration.wav", "-t", str(DUR), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)): p.stdin.write(frame(i / FPS))
    p.stdin.close(); p.wait(); print("ok", out)
