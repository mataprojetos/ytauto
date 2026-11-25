"""EP010 · biblioteca de animação vetorial (pycairo), estilo motion design adulto (pedido do dono, 25/11/2026):
formas limpas, cores sóbrias, luz quente do fogo, grão suave; personagem com proporções normais (o rapaz de capuz)."""
import math, random
import cairo, numpy as np
W, H = 1080, 1920

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


# ---------- personagem (proporções normais) ----------
POSES = {   # mãos (esquerda, direita) em unidades locais (pés em 0,0; altura 100; y negativo = para cima)
    "stand": ((-14, -40), (14, -40)), "panic": ((-8, -88), (8, -88)), "genius": ((-16, -50), (8, -92)),
    "cheer": ((-22, -112), (22, -112)), "relief": ((-14, -40), (3, -95)), "paint": ((14, -60), (24, -66)),
    "remote": ((-5, -58), (7, -58)), "think": ((2, -55), (4, -78)), "shrug": ((-26, -62), (26, -62)),
}
ELBOW_OUT = {"genius": (1.0, 1.4), "panic": (1.2, 1.2), "shrug": (1.4, 1.4)}


def guy(c, x, y, s, t, pose="stand", face="neutral", look=0.0, lean=0.0, shake=0.0, rim=0.0, blink=True, flip=False):
    """o rapaz de capuz. x,y = pés; s = altura em px. pose: ver POSES. face: neutral|panic|smug|sad|happy|relief|think"""
    c.save(); c.translate(x + shake * math.sin(t * 55), y); c.rotate(lean); u = s / 100.0; c.scale(-u if flip else u, u)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.save(); c.scale(1, 0.18); c.set_source_rgba(0, 0, 0, 0.32); c.arc(0, 0, 22, 0, 6.283); c.fill(); c.restore()
    for sx in (-1, 1):   # pernas
        c.set_source_rgba(*(JEANS if sx < 0 else JEANS_D)); c.set_line_width(9); c.move_to(5 * sx, -42); c.line_to(6 * sx, -6); c.stroke()
        c.set_source_rgba(*SHOE); c.save(); c.translate(7 * sx, -3); c.scale(1.6, 0.8); c.arc(0, 0, 5, 0, 6.283); c.restore(); c.fill()
        c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(1.2); c.move_to(7 * sx - 7, -0.6); c.line_to(7 * sx + 7, -0.6); c.stroke()
    hands = POSES[pose]; eo = ELBOW_OUT.get(pose, (1.0, 1.0))
    def arm(i, front):
        sx = -1 if i == 0 else 1
        sh = (11 * sx, -68); ha = hands[i]
        mx, my = (sh[0] + ha[0]) / 2, (sh[1] + ha[1]) / 2
        el = (mx + 7 * sx * eo[i], my + 4)
        c.set_source_rgba(*(HOOD if front else HOOD_D)); c.set_line_width(8)
        c.move_to(*sh); c.line_to(*el); c.line_to(*ha); c.stroke()
        c.set_source_rgba(*SKIN); c.arc(ha[0], ha[1], 4.2, 0, 6.283); c.fill()
    arm(0, False)
    c.set_source_rgba(*HOOD); c.move_to(-14, -44); c.curve_to(-16, -60, -14, -72, 0, -74); c.curve_to(14, -72, 16, -60, 14, -44); c.close_path(); c.fill()
    c.set_source_rgba(*HOOD_D); c.move_to(4, -44); c.curve_to(10, -58, 12, -70, 0, -74); c.curve_to(14, -72, 16, -60, 14, -44); c.close_path(); c.fill()
    c.set_source_rgba(*HOOD_D); c.move_to(-9, -73); c.curve_to(-6, -79, 6, -79, 9, -73); c.set_line_width(3); c.stroke()
    c.set_source_rgba(1, 1, 1, 0.85); c.set_line_width(1.2)
    for sx in (-1, 1): c.move_to(3 * sx, -70); c.line_to(3.5 * sx, -60); c.stroke()
    c.set_source_rgba(*HOOD_D); c.move_to(-7, -52); c.line_to(7, -52); c.line_to(6, -46); c.line_to(-6, -46); c.close_path(); c.fill()
    if rim > 0:
        c.set_source_rgba(1, 0.6, 0.25, 0.6 * rim); c.set_line_width(2.4); c.move_to(14, -46); c.curve_to(16, -60, 14, -72, 2, -74); c.stroke()
    if pose == "remote":   # comando vermelho com antena
        c.set_source_rgba(0.75, 0.15, 0.15, 1); c.rectangle(-6, -64, 14, 9); c.fill()
        c.set_source_rgba(0.2, 0.2, 0.22, 1); c.set_line_width(1.2); c.move_to(6, -64); c.line_to(9, -76); c.stroke()
    arm(1, True)
    if pose == "paint":   # cabo do rolo (as mãos seguram-no)
        c.set_source_rgba(0.75, 0.6, 0.4, 1); c.set_line_width(2.5); c.move_to(26, -68); c.line_to(52, -10); c.stroke()
        c.set_source_rgba(0.95, 0.95, 0.97, 1); c.save(); c.translate(54, -6); c.rotate(0.4); c.rectangle(-9, -4, 18, 8); c.restore(); c.fill()
    # cabeça
    c.save(); c.translate(0, -84); c.rotate(-0.35 * look if face != "think" else 0.12)
    c.set_source_rgba(*SKIN); c.arc(0, 0, 10.5, 0, 6.283); c.fill()
    c.set_source_rgba(*SKIN_D); c.arc(0, 0, 10.5, -1.2, 1.2); c.arc_negative(-3, 0, 10.5, 1.0, -1.0); c.close_path(); c.fill()
    c.set_source_rgba(*SKIN); c.arc(-10.2, 0.5, 2.2, 0, 6.283); c.fill(); c.set_source_rgba(*SKIN_D); c.arc(10.2, 0.5, 2.2, 0, 6.283); c.fill()
    c.set_source_rgba(*HAIR)   # cabelo despenteado com franja para o lado
    c.move_to(-11.2, 0); c.curve_to(-12.5, -8, -10, -12, -7, -13.5); c.line_to(-6, -17.5); c.line_to(-2.5, -14.5)
    c.line_to(0.5, -18.5); c.line_to(3, -14.5); c.line_to(7, -16.5); c.line_to(7.5, -12.5); c.curve_to(10.5, -11, 11.8, -6, 11.2, -2)
    c.curve_to(8, -6.5, 3, -7.5, -1, -6.2); c.curve_to(-5, -5.5, -8.5, -4, -11.2, 0); c.close_path(); c.fill()
    lx, ly = 1.5 * look, -2.5 * look
    ink = (0.08, 0.06, 0.06, 1); c.set_source_rgba(*ink)
    closed = blink and (t % 3.7) < 0.12
    for sx in (-1, 1):
        ex, ey = 3.8 * sx + lx, -1 + ly
        if face in ("relief",) or closed:
            c.set_line_width(1.1); c.arc(ex, ey - 0.5, 1.6, 0.3, 2.8); c.stroke()
        elif face == "smug":
            c.arc(ex, ey + 0.4, 1.3, 0, 6.283); c.fill()
            c.set_source_rgba(*SKIN); c.rectangle(ex - 2, ey - 2.4, 4, 2.2); c.fill(); c.set_source_rgba(*ink)
            c.set_line_width(0.9); c.move_to(ex - 1.8, ey - 0.3); c.line_to(ex + 1.8, ey - 0.3); c.stroke()
        elif face == "panic":
            c.set_source_rgba(1, 1, 1, 1); c.arc(ex, ey, 2.3, 0, 6.283); c.fill(); c.set_source_rgba(*ink); c.arc(ex, ey, 1.1, 0, 6.283); c.fill()
        else:
            c.arc(ex, ey, 1.4, 0, 6.283); c.fill()
    c.set_line_width(1.1)   # sobrancelhas
    for sx in (-1, 1):
        bx = 1.5 * look
        if face == "sad": c.move_to(2 * sx + bx, -6.2 + ly); c.line_to(5.6 * sx + bx, -4.6 + ly)
        elif face == "panic": c.move_to(2 * sx + bx, -7.2 + ly); c.line_to(5.6 * sx + bx, -7.6 + ly)
        elif face == "smug": c.move_to(2 * sx + bx, -5 + ly - (0.8 if sx > 0 else 0)); c.line_to(5.6 * sx + bx, -5.6 + ly - (1.2 if sx > 0 else 0))
        elif face == "think": c.move_to(2 * sx + bx, -5.4 + ly - 0.6 * (sx > 0)); c.line_to(5.6 * sx + bx, -5.2 + ly)
        else: c.move_to(2 * sx + bx, -5 + ly); c.line_to(5.6 * sx + bx, -5.2 + ly)
        c.stroke()
    mx, my = 0.8 * look, 5 - look
    c.set_source_rgba(0.35, 0.08, 0.1, 1); c.set_line_width(1.1)
    if face == "panic": c.save(); c.translate(mx, my); c.scale(1, 1.4); c.arc(0, 0, 2.2, 0, 6.283); c.restore(); c.fill()
    elif face == "sad": c.arc(mx, my + 2.2, 2.6, 3.6, 5.8); c.stroke()
    elif face in ("happy", "relief"): c.arc(mx, my - 1.2, 3, 0.4, 2.7); c.stroke()
    elif face == "smug": c.move_to(mx - 2.5, my); c.curve_to(mx, my + 1.2, mx + 2, my + 0.5, mx + 3.4, my - 1.4); c.stroke()
    elif face == "think": c.move_to(mx - 1.5, my + 0.3); c.line_to(mx + 2, my - 0.3); c.stroke()
    else: c.move_to(mx - 2, my); c.line_to(mx + 2, my); c.stroke()
    if face == "relief":   # gota de suor
        c.set_source_rgba(0.6, 0.85, 1, 0.95); c.move_to(9, -9); c.curve_to(7, -5, 8, -3, 9.5, -3); c.curve_to(11, -3, 12, -5, 9, -9); c.fill()
    if rim > 0: c.set_source_rgba(1, 0.6, 0.25, 0.55 * rim); c.set_line_width(1.8); c.arc(0, 0, 10.5, -1.4, 0.6); c.stroke()
    c.restore(); c.restore()


# ---------- cenário reutilizável ----------
def space(c, t, dx=0.0, dy=0.0, warm=0.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgba(0, *SPACE_TOP); g.add_color_stop_rgba(1, *SPACE_BOT); c.set_source(g); c.paint()
    glow(c, 820 + dx * 0.2, 500, 700, hexc("#5a2a7a"), 0.25); glow(c, 200, 1100, 600, hexc("#1e3a7a"), 0.25)
    if warm > 0: glow(c, 600, 500, 1100, FIRE2, 0.12 * warm)
    for (x, y, d, ph, b) in STARS:
        xx = (x + dx * d * 0.5 - t * 6 * d) % W; yy = (y + dy * d * 0.5) % H
        a = (0.35 + 0.5 * b) * (0.7 + 0.3 * math.sin(t * 2 + ph))
        c.set_source_rgba(1, 0.96, 0.9, a); c.arc(xx, yy, 0.8 + 1.6 * d * b, 0, 6.283); c.fill()


def horizon(c, t, y=1386, R=1900):
    earth(c, 540, y + R, R, t * 0.03)


def finish(c, s, t, vig=0.55):
    vg = cairo.RadialGradient(W / 2, H / 2, 600, W / 2, H / 2, 1300); vg.add_color_stop_rgba(0, 0, 0, 0, 0); vg.add_color_stop_rgba(1, 0, 0, 0.05, vig)
    c.set_source(vg); c.paint()


def add_grain(arr_bgra, t):
    gr = np.repeat(np.repeat(np.roll(grain, int(t * 97) % 50, 1), 2, 0), 2, 1).astype(np.int16) - 128
    rgb = arr_bgra[:, :, :3].astype(np.int16) + (gr[..., None] * 0.05).astype(np.int16)
    arr_bgra[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)


def ship(c, x, y, s, a=1.0, rot=0.0, thrust=0.0, t=0.0):
    """nave genérica (sem logótipos): corpo branco, painéis solares azuis"""
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    if thrust > 0:
        for k, col in enumerate((FIRE1, FIRE2, FIRE3)):
            L = (40 - k * 10) * thrust * (0.85 + 0.15 * math.sin(t * 40 + k))
            c.move_to(-30, -6 + k * 2); c.line_to(-30 - L, 0); c.line_to(-30, 6 - k * 2); c.close_path(); c.set_source_rgba(*col[:3], a); c.fill()
    for sy in (-1, 1):
        c.set_source_rgba(0.75, 0.77, 0.82, a); c.rectangle(-4, sy * 14, 8, sy * 18); c.fill()
        c.set_source_rgba(*hexc("#2a5db0")[:3], a); c.rectangle(-22, sy * 32 - (24 if sy < 0 else 0), 44, 24); c.fill()
        c.set_source_rgba(*hexc("#7fb0ff")[:3], 0.6 * a); c.set_line_width(1)
        for i in range(1, 4): c.move_to(-22 + i * 11, sy * 32 - (24 if sy < 0 else 0)); c.line_to(-22 + i * 11, sy * 32 + (0 if sy < 0 else 24)); c.stroke()
    c.set_source_rgba(0.93, 0.93, 0.95, a); c.rectangle(-30, -14, 54, 28); c.fill()
    c.set_source_rgba(0.72, 0.74, 0.8, a); c.rectangle(-30, 4, 54, 10); c.fill()
    c.set_source_rgba(0.85, 0.7, 0.3, a); c.move_to(24, -10); c.line_to(36, 0); c.line_to(24, 10); c.close_path(); c.fill()
    c.restore()


def rocket(c, x, y, s, ang, t, fire=1.0):
    """foguete preso ao asteroide: aponta para 'ang' (a chama sai para trás)"""
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    if fire > 0:
        for k, col in enumerate((FIRE1, FIRE2, FIRE3)):
            L = (60 - k * 16) * fire * (0.85 + 0.15 * math.sin(t * 37 + k + x))
            c.move_to(-20, -9 + k * 3); c.line_to(-20 - L, 0); c.line_to(-20, 9 - k * 3); c.close_path(); c.set_source_rgba(*col[:3], 0.95); c.fill()
    c.set_source_rgba(0.88, 0.88, 0.9, 1); c.move_to(-20, -10); c.line_to(14, -10); c.curve_to(26, -10, 32, -3, 34, 0); c.curve_to(32, 3, 26, 10, 14, 10); c.line_to(-20, 10); c.close_path(); c.fill()
    c.set_source_rgba(0.65, 0.66, 0.72, 1); c.rectangle(-20, 2, 34, 8); c.fill()
    c.set_source_rgba(*hexc("#c0392b")[:3], 1); c.move_to(-20, -10); c.line_to(-28, -18); c.line_to(-12, -10); c.fill(); c.move_to(-20, 10); c.line_to(-28, 18); c.line_to(-12, 10); c.fill()
    c.restore()
