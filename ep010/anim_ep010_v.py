#!/usr/bin/env python3
"""Whatifaholic EP010 v3 — What If YOU Had to Stop an Asteroid?  (animação vetorial por código, 0 créditos)
Pedido do dono (25/11/2026): estilo mais adulto tipo motion design, tudo a mexer, personagem pequena e perigo enorme;
asteroide cinzento a vir contra a câmara no gancho. Reaproveita de anim_ep010.py: tempos (words.json), textos/carimbos/X,
legendas, pop-up de subscrição, frase de marca e mistura de som.  Uso: python3 anim_ep010_v.py [--frames t1,t2|last]"""
import math, random, sys, os
import cairo, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{HERE}/vetor")
import anim_ep010 as A
import vec
from vec import guy, glow, blob, asteroid, corona, rocket, ship, space, earth, hexc, lerp, clamp, ease, smooth
W, H = A.W, A.H
T, G, AA, FAIL, WS = A.T, A.G, A.A, A.FAIL, A.WS
text, stamp, bigx, fail_x, plan_chip, check, arrow, popin, seg = A.text, A.stamp, A.bigx, A.fail_x, A.plan_chip, A.check, A.arrow, A.popin, A.seg
GOLD, RED, INK, GREEN, DARK = A.GOLD, A.RED, A.INK, A.GREEN, A.DARK
A.OUT = f"{HERE}/whatifaholic_ep010_asteroid_v3.mp4"
HZ = 1386          # linha do horizonte (Terra) nos planos abertos
DUR_HOOK = 4.6


def cam(c, z, cx, cy, dx=0.0, dy=0.0):
    c.translate(W / 2 + dx, H / 2 + dy); c.scale(z, z); c.translate(-cx, -cy)


def shake(t, k):
    return 16 * k * math.sin(t * 61), 14 * k * math.cos(t * 53)


# ---------------- gancho (aprovado pelo dono) ----------------
def s_hook(c, t, th=None):
    th = t if th is None else th
    k = clamp(th / DUR_HOOK) ** 2; z = 1.0 + 0.06 * smooth(th / DUR_HOOK)
    sx, sy = shake(t, k); dx = 14 * math.sin(th * 0.7) + sx; dy = 8 * math.sin(th * 0.5) + sy
    space(c, t, dx, dy)
    c.save(); cam(c, z, W / 2, H / 2, dx, dy)
    q = clamp(th / DUR_HOOK)
    AR = 170 * math.exp(math.log(1300 / 170) * (th / 3.6))
    ax, ay = 560 + 30 * math.sin(th * 0.9), lerp(560, 760, q ** 2)
    heat = 0.6 + 0.4 * q
    for i in range(46):
        rr = random.Random(i); a = rr.random() * 6.283; ph = (t * (0.7 + rr.random()) + rr.random()) % 1
        d0 = AR * 1.2 + ph ** 2 * 1400; ln = 40 + ph * 260
        c.set_source_rgba(1, 0.85, 0.65, 0.35 * ph * (0.4 + q)); c.set_line_width(1 + ph * 3)
        c.move_to(ax + math.cos(a) * d0, ay + math.sin(a) * d0); c.line_to(ax + math.cos(a) * (d0 + ln), ay + math.sin(a) * (d0 + ln)); c.stroke()
    corona(c, ax, ay, AR, t, heat)
    asteroid(c, ax, ay, AR, th * 0.25, heat)
    ER = 1900; earth(c, 540, HZ + ER, ER, t * 0.03)
    glow(c, ax, HZ, 1100, vec.FIRE2, 0.1 + 0.3 * q)
    arms = smooth((th - 1.3) / 0.8); look = smooth((th - 0.2) / 0.6)
    guy(c, 330, HZ + 6, 185, t, pose="panic" if arms > 0.5 else "stand", face="panic" if arms > 0.3 else "neutral",
        look=look, lean=-0.08 * arms, shake=1.2 * arms, rim=0.4 + 0.6 * q, blink=False)
    c.restore()
    if th >= WS(13):
        text(c, "STOP IT.", 540, 330, 150, INK, 1, ow=0.16, scale=popin(th, WS(13)), rot=-0.04)
    vec.finish(c, None, t)


# ---------------- "And you, being a genius…" (a mesma pose em todos) ----------------
def bulb(c, x, y, t, t0):
    if t < t0: return
    u = t - t0; k = popin(t, t0, 0.25)
    glow(c, x, y, 130 * k, GOLD, 0.45 * (0.7 + 0.3 * math.sin(u * 12)))
    for i in range(8):
        a = i * 0.785 + u * 0.8; r0, r1 = 45 * k, (80 + 10 * math.sin(u * 14 + i)) * k
        c.set_source_rgba(*GOLD, 0.95); c.set_line_width(7 * k); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(x + math.cos(a) * r0, y + math.sin(a) * r0); c.line_to(x + math.cos(a) * r1, y + math.sin(a) * r1); c.stroke()


def make_genius(k):
    def s_genius(c, t):
        u = t - G[k]; z = 1.0 + 0.04 * u
        space(c, t, -10 * u, 0, warm=0.4)
        c.save(); cam(c, z, W / 2, 1000)
        corona(c, 830, 380, 210, t, 0.7); asteroid(c, 830, 380, 210, t * 0.2, 0.6)
        ER = 2600; earth(c, 540, 1560 + ER, ER, t * 0.03)
        guy(c, 520, 1566, 720, t, pose="genius", face="smug", rim=0.5)
        c.restore()
        bulb(c, 610, 820, t, G[k] + 0.05)
        stamp(c, t, G[k] + 0.12, f"PLAN {A.PLANS[k]}", 540, 300, GOLD, 150, rot=-0.07)
        vec.finish(c, None, t)
    s_genius.__name__ = f"s_genius{k}"
    return s_genius


# ---------------- plano A: bomba → mil pedaços ----------------
FR = [(random.uniform(0, 6.283), random.random(), random.uniform(0.6, 1.4), i) for i in range(80)]


def rockbit(c, x, y, r, seed, heat=0.0):
    c.set_source_rgba(*vec.ROCK[:3], 1); blob(c, x, y, r, 7, seed, 0.5); c.fill()
    c.set_source_rgba(*vec.ROCK_D[:3], 1); blob(c, x - r * 0.25, y + r * 0.25, r * 0.65, 6, seed + 1, 0.5); c.fill()
    c.set_source_rgba(*vec.ROCK_L[:3], 0.8); blob(c, x + r * 0.25, y - r * 0.3, r * 0.4, 6, seed + 2, 0.5); c.fill()
    if heat > 0:
        c.set_source_rgba(1, 0.55, 0.15, 0.8 * heat); c.set_line_width(max(1.0, r * 0.14)); c.arc(x, y, r * 0.95, -2.2, -0.2); c.stroke()


def s_nuke(c, t):
    u = t - AA[0]; TE = FAIL[0] - 0.05
    k = clamp(1 - (t - TE) / 1.0) if t > TE else 0; sx, sy = shake(t, k * 0.8)
    space(c, t, -8 * u + sx, sy, warm=0.3)
    c.save(); cam(c, 1.0 + 0.02 * u, W / 2, H / 2, sx, sy)
    ax, ay, AR = 620, 560, 230
    ER = 1900; earth(c, 540, HZ + ER, ER, t * 0.03)
    if t < TE:
        corona(c, ax, ay, AR, t, 0.7); asteroid(c, ax, ay, AR, t * 0.2, 0.6)
        q = smooth(clamp(u / (TE - AA[0])))
        x0, y0 = 360, HZ - 10; mx, my = lerp(x0, ax, q), lerp(y0, ay, q) - 220 * math.sin(math.pi * q)
        ang = math.atan2(ay - y0 - 220 * math.pi * math.cos(math.pi * q) * 0.3, ax - x0)
        for j in range(16):
            sm = j / 16; px = lerp(x0, ax, max(0, q - sm * 0.25)); py = lerp(y0, ay, max(0, q - sm * 0.25)) - 220 * math.sin(math.pi * max(0, q - sm * 0.25))
            c.set_source_rgba(0.85, 0.85, 0.9, 0.35 * (1 - sm)); c.arc(px, py, 6 + 14 * sm, 0, 6.283); c.fill()
        c.save(); c.translate(mx, my); c.rotate(ang)
        c.set_source_rgba(0.92, 0.92, 0.95, 1); A.rr(c, -34, -8, 60, 16, 8); c.fill()
        c.set_source_rgba(*RED, 1); c.move_to(24, -8); c.line_to(42, 0); c.line_to(24, 8); c.close_path(); c.fill()
        c.set_source_rgba(1, 0.7, 0.2, 1); c.move_to(-34, -5); c.line_to(-52 - 6 * math.sin(t * 40), 0); c.line_to(-34, 5); c.fill()
        c.restore()
    else:
        v = t - TE
        R = 80 + 460 * ease(v / 0.5)
        glow(c, ax, ay, R * 1.6, (1, 0.97, 0.85), 0.95 * clamp(1 - v / 1.2))
        glow(c, ax, ay, R, vec.FIRE2, 0.9 * clamp(1 - v / 2.0))
        for (a, ph, sp, sd) in FR[:60]:
            d = (40 + 560 * ease(v / 2.2) * sp) * (0.35 + ph)
            rockbit(c, ax + math.cos(a) * d, ay + math.sin(a) * d, 10 + 22 * ph, 700 + sd, 1.0 - clamp(v / 2))
        if v < 0.18: c.set_source_rgba(1, 0.98, 0.9, 0.7 * (1 - v / 0.18)); c.paint()
    guy(c, 300, HZ + 6, 175, t, pose="remote", face="smug" if t < TE else "panic", look=0.6, rim=0.4)
    c.restore()
    plan_chip(c, t, 0, FAIL[0]); fail_x(c, t, FAIL[0], 540, 980, 190)
    vec.finish(c, None, t)


def s_frag(c, t):
    u = t - T["youve"]; sx, sy = shake(t, 0.25)
    space(c, t, sx, sy, warm=0.5)
    c.save(); cam(c, 1.0, W / 2, H / 2, sx, sy)
    pts = []
    for (a, ph, sp, sd) in FR:
        L = (u * 0.38 * sp + ph) % 1
        if u < 0.5: L *= (0.3 + 1.4 * u)
        d = 30 + (L ** 2) * 1100; r = 6 + (L ** 2.2) * 150
        pts.append((r, 560 + math.cos(a) * d, 620 + math.sin(a) * d * 1.05, sd, L))
    for (r, x, y, sd, L) in sorted(pts):
        if r > 40: corona(c, x, y, r, t + sd, 0.5)
        rockbit(c, x, y, r, 900 + sd, 0.8)
    ER = 1900; earth(c, 540, HZ + ER, ER, t * 0.03)
    guy(c, 300, HZ + 6, 175, t, pose="panic", face="panic", look=0.7, shake=1.2, rim=0.7, blink=False)
    c.restore()
    if t >= T["thousand"]:
        n = int(1 + 999 * ease((t - T["thousand"]) / 0.6))
        text(c, f"{n:,} ROCKS", 540, 1120, 110, INK, 1, ow=0.16, scale=popin(t, T["thousand"]), rot=-0.03)
    if t >= T["still"]:
        text(c, "STILL COMING", 540, 1250, 92, RED, 1, ow=0.17, scale=popin(t, T["still"]), rot=-0.03)
    plan_chip(c, t, 0, FAIL[0])
    vec.finish(c, None, t)


# ---------------- plano B: foguetes num asteroide que gira ----------------
RKT = [(-0.5, 3.1), (0.6, -0.4), (1.45, 0.4), (2.4, 1.9), (3.6, -2.4)]   # (ângulo na borda, direção para onde aponta)


def rock_group(c, cx, cy, AR, ang, t, fire=0.0, arrows=0.0, boy_pose="remote", boy_face="smug", paint=0.0):
    c.save(); c.translate(cx, cy); c.rotate(ang)
    asteroid(c, 0, 0, AR, 0.3, 0.0)
    for (pa, pd) in RKT:   # foguetes presos à borda (por cima da rocha), cada um a apontar para um lado
        x, y = math.cos(pa) * AR * 0.9, math.sin(pa) * AR * 0.9
        rocket(c, x, y, AR / 300, pa + pd * 0.35 + math.pi, t, fire)
    if paint > 0:   # metade esquerda a ficar branca
        c.save(); pts = [(math.cos(a + 0.3) * AR * k, math.sin(a + 0.3) * AR * k) for a, k in vec.AP]
        c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]; c.close_path(); c.clip()
        edge = -AR + 2 * AR * 0.5 * paint
        c.set_source_rgba(0.95, 0.95, 0.96, 1); c.rectangle(-AR * 1.3, -AR * 1.3, edge + AR * 1.3, AR * 2.6); c.fill()
        for i in range(6):
            dx = -AR + (i + 0.5) * (edge + AR) / 6; dl = 30 + 25 * math.sin(i * 2.1)
            c.arc(dx, AR * 0.2 + dl * paint, 9, 0, 6.283); c.fill(); c.rectangle(dx - 9, -AR, 18, AR * 1.2 + dl * paint); c.fill()
        c.set_source_rgba(0, 0, 0, 0.12); c.rectangle(edge - 6, -AR * 1.3, 6, AR * 2.6); c.fill()
        c.restore()
    if arrows > 0:
        for (pa, pd) in RKT:
            x, y = math.cos(pa) * AR * 0.98, math.sin(pa) * AR * 0.98
            x, y = math.cos(pa) * AR * 0.9, math.sin(pa) * AR * 0.9
            d = pa + pd * 0.35 + math.pi   # empurra para onde o foguete aponta (a chama sai para fora)
            arrow(c, x, y, x + math.cos(d) * AR * 0.45, y + math.sin(d) * AR * 0.45, GOLD, arrows, w=10 * AR / 300 + 4, head=22 * AR / 300 + 8)
    guy(c, 0 if paint == 0 else 40, -AR * 0.93, AR * 0.75, t, pose=boy_pose, face=boy_face, rim=0.2)
    c.restore()


def s_rockets(c, t):
    u = t - AA[1]; sp = max(0, t - T["asteroid"]); ang = 0.3 * sp * sp
    space(c, t, 6 * u, 0)
    c.save(); cam(c, 1.0 + 0.02 * u, W / 2, H / 2)
    fire = seg(t, T["rockets"] - 0.25, T["rockets"] + 0.15)
    rock_group(c, 540, 1180, 470, ang, t, fire=fire, arrows=fire)
    c.restore()
    if fire > 0: text(c, "PUSH!", 820, 560, 100, GOLD, fire, ow=0.16, scale=popin(t, T["rockets"]), rot=-0.03)
    plan_chip(c, t, 1, FAIL[1]); fail_x(c, t, FAIL[1], 540, 700, 200)
    vec.finish(c, None, t)


def s_wash(c, t):
    u = t - T["spinning"]; sp0 = T["spinning"] - T["asteroid"]
    ang = 0.3 * (sp0 + u) ** 2 + 2.4 * u * u
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.9, 0.91, 0.93); g.add_color_stop_rgb(1, 0.74, 0.76, 0.8); c.set_source(g); c.paint()
    c.set_source_rgba(0.66, 0.69, 0.75, 1); A.rr(c, 60, 150, 960, 230, 30); c.fill()
    c.set_source_rgba(0.1, 0.13, 0.18, 1); A.rr(c, 470, 205, 400, 120, 18); c.fill()
    text(c, f"SPIN {int(400 + 1200 * clamp(u / 3))}", 670, 265, 56, (0.45, 1.0, 0.6), 1, outline=False)
    for i, kx in enumerate((150, 290)):
        c.set_source_rgba(0.95, 0.96, 0.98, 1); c.arc(kx + 20, 265, 50, 0, 6.283); c.fill()
        c.save(); c.translate(kx + 20, 265); c.rotate(u * (2 + i) + i); c.set_source_rgba(0.4, 0.43, 0.5, 1); c.set_line_width(10)
        c.move_to(0, 0); c.line_to(0, -38); c.stroke(); c.restore()
    text(c, "WASHING MACHINE MODE", 540, 455, 58, (0.15, 0.2, 0.32), 1, outline=False, scale=popin(t, T["washing"]) if t >= T["washing"] else 0)
    CX, CY, R = 540, 930, 370 * (0.85 + 0.15 * ease(u / 0.5))
    c.set_source_rgba(0, 0, 0, 0.18); c.arc(CX + 10, CY + 16, R + 70, 0, 6.283); c.fill()
    c.set_source_rgba(0.6, 0.63, 0.69, 1); c.arc(CX, CY, R + 70, 0, 6.283); c.fill()
    c.set_source_rgba(0.96, 0.97, 0.99, 1); c.arc(CX, CY, R + 40, 0, 6.283); c.fill()
    c.save(); c.arc(CX, CY, R, 0, 6.283); c.clip()
    space(c, t)
    rock_group(c, CX, CY + 40, R * 0.5, ang, t, fire=1.0, arrows=seg(t, T["rockets2"] - 0.1, T["rockets2"] + 0.2))
    gl = cairo.LinearGradient(CX - R, CY - R, CX + R, CY + R)
    gl.add_color_stop_rgba(0, 1, 1, 1, 0.25); gl.add_color_stop_rgba(0.35, 1, 1, 1, 0); gl.add_color_stop_rgba(1, 1, 1, 1, 0.06)
    c.set_source(gl); c.paint(); c.restore()
    c.set_source_rgba(0.5, 0.53, 0.6, 1); c.set_line_width(10); c.arc(CX, CY, R, 0, 6.283); c.stroke()


def make_react(label, xt):
    """grande plano da cara de desilusão + X + rótulo"""
    def s_react(c, t):
        u = t - xt; k = clamp(1 - u / 0.5); sx, sy = shake(t, 0.5 * k)
        g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.16, 0.06, 0.1); g.add_color_stop_rgb(1, 0.06, 0.03, 0.08); c.set_source(g); c.paint()
        glow(c, 540, 900, 900, (0.6, 0.15, 0.2), 0.25)
        c.save(); c.translate(sx, sy)
        z = 26 + 0.8 * u
        guy(c, 540, 930 + 84 * z, 100 * z, t, pose="stand", face="sad", blink=False)
        c.restore()
        bigx(c, 540, 300, 115, 1.0, 1.0, w=26)
        text(c, label, 540, 1290, 108, RED, 1, ow=0.17, scale=popin(t, xt + 0.02), rot=-0.03)
        vec.finish(c, None, t, 0.65)
    return s_react


# ---------------- plano C: pintar de branco ----------------
def s_paint(c, t):
    u = t - AA[2]
    space(c, t, -5 * u, 0, warm=0.0)
    glow(c, 170, 250, 420, (1, 0.9, 0.5), 0.45)
    c.save(); c.translate(170, 250); c.rotate(t * 0.2)
    for i in range(12):
        c.set_source_rgba(1, 0.85, 0.4, 0.9); c.move_to(0, 0); c.arc(0, 0, 150, i * 0.5236 - 0.08, i * 0.5236 + 0.08); c.close_path(); c.fill()
    c.restore(); c.set_source_rgba(1, 0.92, 0.55, 1); c.arc(170, 250, 95, 0, 6.283); c.fill()
    paint = seg(t, AA[2], AA[2] + 2.4)
    c.save(); cam(c, 1.0 + 0.02 * u, W / 2, H / 2)
    rock_group(c, 560, 1250, 500, 0.0, t, fire=0, boy_pose="paint", boy_face="happy", paint=paint)
    c.restore()
    if t >= T["sunlight"] - 0.1:
        a = seg(t, T["sunlight"] - 0.1, T["sunlight"] + 0.3)
        for i in range(5):
            A.dashed(c, 230, 330, 200 + i * 60, 900 + i * 50, GOLD, 0.85 * a, w=7, dash=26, off=-t * 160)
        kk = seg(t, T["sunlight"] + 0.4, T["sunlight"] + 0.9)
        if kk > 0:
            arrow(c, 1000, 1150, 1000 + 50 * kk, 1150 + 20 * kk, GOLD, kk, w=8, head=22)
            text(c, "push", 990, 1100, 44, GOLD, kk)
    if t >= T["works"]:
        a = 1 - seg(t, T["fifty"] - 0.3, T["fifty"])
        c.save(); c.set_source_rgba(0.04, 0.04, 0.12, 0.88 * a); A.rr(c, 150, 470, 780, 210, 30); c.fill()
        c.set_source_rgba(*GREEN, a); c.set_line_width(5); A.rr(c, 150, 470, 780, 210, 30); c.stroke(); c.restore()
        check(c, 215, 530, 60, GREEN, a, seg(t, T["works"], T["works"] + 0.25))
        text(c, "IT WORKS…", 270, 530, 60, INK, a, align="l", outline=False)
        if t >= T["but"]:
            c.set_source_rgba(1, 1, 1, 0.2 * a); A.rr(c, 190, 595, 700, 44, 22); c.fill()
            c.set_source_rgba(*GOLD, a); A.rr(c, 190, 595, 14 + 6 * math.sin(t * 3) ** 2, 44, 22); c.fill()
            text(c, f"OFF COURSE: {0.0001 + 0.0001 * (t - T['but']):.4f}%", 540, 617, 34, INK, a, outline=False)
    if t >= T["fifty"]:
        kk = popin(t, T["fifty"], 0.25); yr = 2026 + int(50 * ease((t - T["fifty"]) / 1.0))
        c.save(); c.translate(540, 560); c.scale(kk, kk)
        c.set_source_rgba(0.96, 0.95, 0.92, 1); A.rr(c, -330, -120, 660, 240, 26); c.fill()
        c.set_source_rgba(*RED, 1); A.rr(c, -330, -120, 660, 64, 26); c.fill(); c.rectangle(-330, -80, 660, 24); c.fill(); c.restore()
        text(c, "50 YEARS", 540, 540, 116 * kk, DARK, 1, outline=False)
        text(c, f"{yr}", 540, 635, 48 * kk, (0.35, 0.35, 0.4), 1, outline=False)
    plan_chip(c, t, 2, FAIL[2]); fail_x(c, t, FAIL[2], 540, 820, 200)
    vec.finish(c, None, t)


# ---------------- plano D: trator gravitacional ----------------
def s_tractor(c, t):
    u = t - AA[3]
    space(c, t, -6 * u, 0)
    c.save(); cam(c, 1.0 + 0.015 * u, W / 2, H / 2)
    pull = 5 * seg(t, T["pulls"], T["pulls"] + 2.5)
    corona(c, 330 + pull, 720, 210, t, 0.5); asteroid(c, 330 + pull, 720, 210, t * 0.15, 0.4)
    if t >= T["spaceship"] - 0.2:
        q = ease((t - T["spaceship"] + 0.2) / 0.8)
        ship(c, lerp(1250, 760, q), 700 + 6 * math.sin(t * 2), 2.4, thrust=1 - q, t=t)
    if t >= T["gravity"]:
        a = seg(t, T["gravity"], T["gravity"] + 0.3)
        for i in range(4):
            ph = ((t - T["gravity"]) * 0.7 + i / 4) % 1
            c.set_source_rgba(0.55, 0.8, 1, a * (1 - ph) * 0.9); c.set_line_width(5); c.arc(760, 700, 60 + ph * 330, math.pi * 0.8, math.pi * 1.2); c.stroke()
        text(c, "GRAVITY", 600, 520, 50, (0.55, 0.8, 1), a, ow=0.15)
    if t >= T["pulls"]:
        arrow(c, 560, 860, 586, 860, GOLD, 1, w=6, head=14)
    if t >= T["tiny"]:
        q = popin(t, T["tiny"], 0.25)
        c.set_source_rgba(1, 1, 1, 0.95); c.set_line_width(10); c.arc(574, 860, 70 * q, 0, 6.283); c.stroke()
        c.move_to(574 + 50 * q, 860 + 50 * q); c.line_to(574 + 110 * q, 860 + 110 * q); c.set_line_width(18); c.stroke()
        text(c, "TINY", 740, 920, 70 * q, GOLD, 1, ow=0.16)
    ER = 1900; earth(c, 540, HZ + 120 + ER, ER, t * 0.03)
    guy(c, 260, HZ + 126, 170, t, pose="think", face="think", look=0.5)
    c.restore()
    plan_chip(c, t, 3, FAIL[3]); fail_x(c, t, FAIL[3], 540, 980, 200)
    vec.finish(c, None, t)


# ---------------- viragem ----------------
def s_turn(c, t):
    u = t - T["then"]; D = T["so"] - T["then"]
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.04, 0.05, 0.12); g.add_color_stop_rgb(1, 0.02, 0.02, 0.06); c.set_source(g); c.paint()
    glow(c, 540, 820, 700, (0.3, 0.35, 0.7), 0.25)
    z = 22 + 6 * smooth(u / D)
    guy(c, 540, 930 + 84 * z, 100 * z, t, pose="think", face="think")
    if t >= T["earlier"] - 0.1:
        glow(c, 540, 380, 380 * popin(t, T["earlier"] - 0.1, 0.3), GOLD, 0.35)
    if t >= T["harder"] - 0.05:
        text(c, "PUSH HARDER", 540, 270, 92, (0.8, 0.82, 0.88), 1, ow=0.15, scale=popin(t, T["harder"] - 0.05), rot=-0.03)
        q = seg(t, T["harder"] + 0.3, T["harder"] + 0.55)
        if q > 0:
            c.set_source_rgba(*RED, 1); c.set_line_width(16); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(200, 285); c.line_to(200 + 680 * q, 255); c.stroke()
    if t >= T["earlier"] - 0.05:
        kk = popin(t, T["earlier"] - 0.05, 0.3)
        text(c, "PUSH EARLIER", 540, 1290, 132, GREEN, 1, ow=0.16, scale=kk, rot=-0.03)
    vec.finish(c, None, t, 0.7)


# ---------------- plano E: nave pequena, anos antes ----------------
def s_dart(c, t):
    u = t - T["so"]
    space(c, t, 4 * u, 0)
    c.save(); cam(c, 1.0 + 0.03 * u, W / 2, H / 2)
    TI = T["crash"] + 0.25
    nud = 18 * ease((t - TI) / 1.5) if t > TI else 0
    ax, ay = 660 + nud, 620 - nud * 0.3
    corona(c, ax, ay, 160, t, 0.35); asteroid(c, ax, ay, 160, t * 0.15, 0.3)
    if t < TI:
        q = ease(clamp((t - T["so"]) / (TI - T["so"])))
        sx_, sy_ = lerp(-80, ax - 150, q), lerp(1150, ay + 60, q)
        ship(c, sx_, sy_, 1.2, rot=math.atan2(ay + 60 - 1150, ax - 150 + 80), thrust=1.0, t=t)
    else:
        v = t - TI
        glow(c, ax - 150, ay + 50, 260, (1, 0.96, 0.8), 0.9 * math.exp(-v * 2.2))
        for i in range(14):
            a = random.Random(i).uniform(2.2, 4.2); d = 30 + 220 * ease(v / 1.2)
            rockbit(c, ax - 150 + math.cos(a) * d, ay + 50 + math.sin(a) * d, 6 + 5 * random.Random(i + 9).random(), 1200 + i, 1 - clamp(v))
        if v < 0.12: c.set_source_rgba(1, 1, 0.95, 0.5 * (1 - v / 0.12)); c.paint()
    ER = 2400; earth(c, 540, 1620 + ER, ER, t * 0.03)
    guy(c, 260, 1626, 150, t, pose="cheer" if t > TI + 0.2 else "stand", face="happy" if t > TI + 0.2 else "neutral", look=0.6)
    c.restore()
    stamp(c, t, T["so"] + 0.05, "PLAN E", 330, 300, GOLD, 120, rot=-0.06, mark="check")
    if t >= T["years"]:
        kk = popin(t, T["years"])
        c.save(); c.translate(540, 1240); c.rotate(-0.03); c.scale(kk, kk)
        c.set_source_rgba(0.04, 0.04, 0.12, 0.9); A.rr(c, -390, -70, 780, 140, 70); c.fill()
        c.set_source_rgba(*GREEN, 1); c.set_line_width(5); A.rr(c, -390, -70, 780, 140, 70); c.stroke(); c.restore()
        text(c, "YEARS BEFORE IMPACT", 540, 1240, 62 * kk, INK, 1, outline=False, rot=-0.03)
    vec.finish(c, None, t)


# ---------------- trajetória: um toque pequeno = milhares de km ----------------
def s_traj(c, t):
    u = t - T["because"]
    space(c, t, -4 * u, 0)
    EX, EY, ER = 470, 1180, 230
    earth(c, EX, EY, ER, t * 0.05)
    S = (190, 160)
    hit = (EX - 40, EY - ER + 10)
    def green(s):   # caminho desviado: passa à direita da Terra
        return (lerp(S[0], 980, s) + 160 * math.sin(math.pi * s) * 0.0, lerp(S[1], 1350, s))
    a = seg(t, T["because"], T["because"] + 0.3); q = seg(t, T["because"], T["because"] + 0.8)
    A.dashed(c, S[0], S[1], lerp(S[0], hit[0], q), lerp(S[1], hit[1], q), RED, 0.85 * a, w=7, dash=22)
    if q >= 1: bigx(c, hit[0], hit[1], 30, 1.0, 0.9, w=11)
    pos = S; sz = 40
    if t >= T["nudge"]:
        v = t - T["nudge"]
        A.sparkle(c, S[0] + 10, S[1] + 10, 50 * popin(t, T["nudge"]), (1, 1, 0.85), 1)
        text(c, "TINY NUDGE", S[0] + 40, S[1] - 70, 50, INK, 1, align="l", scale=popin(t, T["nudge"]))
        gq = ease(v / 3.8)
        c.set_source_rgba(*GREEN, 0.95); c.set_line_width(8); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(*S)
        for i in range(1, 31):
            p = green(gq * i / 30); c.line_to(*p)
        c.stroke()
        pos = green(gq); sz = 40 + 50 * gq
    corona(c, pos[0], pos[1], sz, t, 0.5); asteroid(c, pos[0], pos[1], sz, t * 0.3, 0.4)
    if t >= T["thousands"]:
        kk = popin(t, T["thousands"]); q2 = seg(t, T["thousands"], T["thousands"] + 0.5)
        gp = green(0.78)
        c.save(); c.set_source_rgba(*GOLD, 1); c.set_line_width(6); c.set_dash([14, 10])
        c.move_to(EX + ER * 0.7, EY - ER * 0.7); c.line_to(lerp(EX + ER * 0.7, gp[0], q2), lerp(EY - ER * 0.7, gp[1], q2)); c.stroke(); c.restore()
        c.save(); c.translate(540, 1560); c.rotate(-0.03); c.scale(kk, kk)
        c.set_source_rgba(0.04, 0.04, 0.12, 0.9); A.rr(c, -400, -70, 800, 140, 70); c.fill()
        c.set_source_rgba(*GOLD, 1); c.set_line_width(5); A.rr(c, -400, -70, 800, 140, 70); c.stroke(); c.restore()
        text(c, "THOUSANDS OF KM", 540, 1560, 66 * kk, GOLD, 1, outline=False, rot=-0.03)
    if t >= T["reaches"]:
        text(c, "MISSED!", 800, 1000, 80, GREEN, 1, ow=0.17, scale=popin(t, T["reaches"]), rot=-0.08)
    guy(c, EX, EY - ER + 4, 95, t, pose="relief" if t > T["reaches"] else "stand", face="relief" if t > T["reaches"] else "neutral", look=0.7)
    vec.finish(c, None, t)


# ---------------- é real: DART (2022) ----------------
def s_real(c, t):
    u = t - T["real"]
    space(c, t, -5 * u, 0)
    c.save(); cam(c, 1.0 + 0.02 * u, W / 2, H / 2)
    DX, DY = 540, 860
    old = (380, 120); new = (310, 100); ch = seg(t, T["changed"], T["changed"] + 0.8)
    rx, ry = lerp(old[0], new[0], ch), lerp(old[1], new[1], ch)
    c.save(); c.set_source_rgba(1, 1, 1, 0.35); c.set_line_width(3); c.set_dash([12, 10]); c.save(); c.translate(DX, DY); c.scale(old[0], old[1]); c.arc(0, 0, 1, 0, 6.283); c.restore(); c.stroke(); c.restore()
    if ch > 0:
        c.save(); c.set_source_rgba(*GREEN, 0.9 * ch); c.set_line_width(5); c.save(); c.translate(DX, DY); c.scale(new[0], new[1]); c.arc(0, 0, 1, 0, 6.283); c.restore(); c.stroke(); c.restore()
    om = 0.9 + 0.25 * ch
    ma = -1.0 + u * om
    mx, my = DX + math.cos(ma) * rx, DY + math.sin(ma) * ry
    behind = math.sin(ma) < 0
    if behind: asteroid(c, mx, my, 55, t * 0.5, 0)
    asteroid(c, DX, DY, 230, t * 0.08, 0)
    if not behind: asteroid(c, mx, my, 55, t * 0.5, 0)
    TI = T["nasa"] + 0.3
    if t < TI:
        q = ease(clamp((t - T["real"]) / (TI - T["real"])))
        ship(c, lerp(1250, mx + 60, q), lerp(300, my - 40, q), 1.4, rot=math.atan2(my - 40 - 300, mx + 60 - 1250), thrust=1, t=t)
    else:
        v = t - TI; glow(c, mx, my, 200, (1, 0.96, 0.8), 0.9 * math.exp(-v * 2.5))
    ER = 2400; earth(c, 540, 1660 + ER, ER, t * 0.03)
    guy(c, 220, 1666, 150, t, pose="cheer" if t > TI + 0.3 else "stand", face="happy", look=0.6)
    c.restore()
    if t >= T["y2022"]: stamp(c, t, T["y2022"], "2022", 300, 290, GOLD, 120, rot=-0.06)
    if t >= T["nasa"]: text(c, "NASA · DART", 330, 410, 64, INK, 1, ow=0.17, scale=popin(t, T["nasa"]), rot=-0.06)
    if t >= T["dart"]:
        text(c, "DIMORPHOS", mx, my - 95, 40, INK, 1, ow=0.2, scale=popin(t, T["dart"]))
    if t >= T["orbit"] - 0.05:
        k2 = popin(t, T["orbit"] - 0.05, 0.3)
        glow(c, 540, 1300, 380 * k2, GOLD, 0.3 * math.exp(-(t - T["orbit"]) * 1.5))
        c.save(); c.translate(540, 1290); c.rotate(-0.03); c.scale(k2, k2)
        c.set_source_rgba(0.04, 0.04, 0.12, 0.92); A.rr(c, -380, -110, 760, 220, 40); c.fill()
        c.set_source_rgba(*GOLD, 1); c.set_line_width(6); A.rr(c, -380, -110, 760, 220, 40); c.stroke(); c.restore()
        text(c, "ORBIT", 540, 1225, 50 * k2, INK, 1, outline=False, rot=-0.03)
        text(c, "−32 MIN", 540, 1310, 140 * k2, GOLD, 1, ow=0.12, rot=-0.03)
    vec.finish(c, None, t)


def s_brand(c, t):
    u = t - T["brand"]
    s_real(c, T["brand"] - 0.01)
    c.set_source_rgba(0.02, 0.02, 0.06, 0.65); c.paint()
    A.draw_scratch(c, u, 540, 760, scale=0.95, skin=vec.SKIN[:3], accent=vec.HOOD[:3], ink=INK, hair=vec.HAIR[:3])


def s_end(c, t):
    """'Which means, next time an asteroid is heading for Earth…' → volta ao gancho (último frame = frame 0)"""
    if t >= A.T_END - 1.5 / A.FPS:
        s_hook(c, 0.0, 0.0); return
    e = clamp((t - T["which"]) / (A.T_END - 1 / A.FPS - T["which"]))
    s_hook(c, t, lerp(-1.6, 0.0, e))


SCENES = [(0.0, G[0], s_hook), (G[0], AA[0], make_genius(0)), (AA[0], T["youve"], s_nuke), (T["youve"], G[1], s_frag),
          (G[1], AA[1], make_genius(1)), (AA[1], T["spinning"], s_rockets), (T["spinning"], T["it_"], s_wash),
          (T["it_"], G[2], make_react("GOES NOWHERE", T["it_"])),
          (G[2], AA[2], make_genius(2)), (AA[2], T["have"], s_paint), (T["have"], G[3], make_react("NO TIME", T["have"])),
          (G[3], AA[3], make_genius(3)), (AA[3], T["decades"], s_tractor), (T["decades"], T["then"], make_react("DECADES", T["decades"])),
          (T["then"], T["so"], s_turn), (T["so"], T["because"], s_dart), (T["because"], T["real"], s_traj),
          (T["real"], T["brand"], s_real), (T["brand"], T["which"], s_brand), (T["which"], 99, s_end)]
A.SCENES = SCENES
A.NO_PUNCH = {s_brand, s_end, s_wash}
A.SUB_Y = 1190


def frame(t):
    s = A.frame_surface(t)
    arr = np.ndarray((H, W, 4), np.uint8, s.get_data())
    vec.add_grain(arr, t)
    return arr[:, :, [2, 1, 0]].tobytes()
A.frame = frame


if __name__ == "__main__":
    import subprocess
    if len(sys.argv) > 2 and sys.argv[1] == "--frames":
        from PIL import Image
        for tt in sys.argv[2].split(","):
            tv = float(tt) if tt != "last" else (A.N_FR - 1) / A.FPS
            Image.frombytes("RGB", (W, H), frame(tv)).save(f"{A.BLD}/v_{tv:06.2f}.png")
        print("frames ok"); sys.exit()
    raw_v = f"{A.BLD}/raw_v.mp4"
    if "--mix-only" not in sys.argv:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(A.FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p", raw_v], stdin=subprocess.PIPE)
        for i in range(A.N_FR): p.stdin.write(frame(i / A.FPS))
        p.stdin.close(); p.wait()
    A.mix(raw_v)
    print("OK", A.OUT, A.T_END)
