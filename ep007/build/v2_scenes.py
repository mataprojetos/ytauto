# ---------- cenas ----------
def proj_pt(cx, cy, R, rot, lon, lat, tilt=0.41):
    ct, st = math.cos(tilt), math.sin(tilt)
    lo = math.radians(lon) + rot; la = math.radians(lat)
    x = math.cos(la) * math.sin(lo); y = -math.sin(la); z = math.cos(la) * math.cos(lo)
    return cx + R * x, cy + R * (y * ct - z * st * 0.35), z


def pin(c, x, y, k, col=RED):
    if k <= 0: return
    c.save(); c.translate(x, y); c.scale(k, k)
    c.set_source_rgba(0, 0, 0, 0.35); c.arc(0, 4, 14, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(*col, 1); c.arc(0, -46, 26, math.pi * 0.85, math.pi * 2.15); c.line_to(0, 0); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 1); c.arc(0, -46, 10, 0, 2 * math.pi); c.fill()
    c.restore()


def dashed(c, x0, y0, x1, y1, col, a, w=4, dash=18, off=0):
    c.save(); c.set_source_rgba(*col, a); c.set_line_width(w); c.set_dash([dash, dash * 0.7], off)
    c.move_to(x0, y0); c.line_to(x1, y1); c.stroke(); c.restore()


def cam_hook(t):
    """câmara do gancho: 'Look up' (sobe da rua para o arco); t<0 = estado do frame 0"""
    up = smooth(t / 1.6)
    return 1.10 + 0.05 * smooth((t - 0.4) / 2.0), 0.5, lerp(0.56, 0.38, up)


def s_hook(c, t):
    z, fx, fy = cam_hook(t)
    up = smooth(t / 1.6)
    draw_par(c, "city", z, fx, fy, px=0, py=lerp(-30, 60, up), push=0.05 * smooth(t / 2.3))
    for k in range(3):
        p = ((t * 0.35 + k / 3) % 1.0)
        glow(c, lerp(150, 1150, p), lerp(1350, -150, p), 170, (1, 0.95, 0.8), 0.22)
    particles(c, t, (1, 0.95, 0.85), 0.55, vx=-10, vy=-6, size=0.8)
    k = popin(t, T["earth"] - 0.05, 0.25)
    text(c, "EARTH HAS RINGS", 540, 300, 96, INK, 1, ow=0.14, scale=k)
    vignette(c, 0.35)


def s_everywhere(c, t):
    """'And they're everywhere': corte para o espaço, a câmara afasta-se depressa da Terra com anéis"""
    u = t - T["every"] + 0.25; d = T["frm"] - T["every"] + 0.25
    space_bg(c, t)
    R = lerp(620, 250, ease(u / d))
    globe(c, 540, 860, R, 1.2 + u * 0.9, t, ring=1.0, ring_tilt=-0.22 + 0.1 * u, sun=(-1, -0.3))
    text(c, "EVERYWHERE", 540, 300, 100, GOLD, 1, scale=popin(t, T["every"]), ow=0.14)


def s_europe_map(c, t):
    """esquema: o globo roda até à Europa; linhas de visão do pin até ao anel = o arco que se vê"""
    u = t - T["frm"]; d = T["arch"] - 0.35 - T["frm"]
    space_bg(c, t)
    rot = lerp(1.4, -0.17, smooth(u / (d * 0.7)))
    cx, cy, R = 540, 900, 330
    globe(c, cx, cy, R, rot, t, ring=1.0, ring_tilt=0.0, sun=(-1, -0.3))
    px, py, z = proj_pt(cx, cy, R, rot, 10, 47)
    k = popin(t, T["europe"] - 0.05, 0.25) if z > 0 else 0
    if k > 0:
        # ponto do anel visto da Europa: arco frontal do anel (a sul), realçado
        a = seg(u, 0.55, 0.9)
        c.save(); c.translate(cx, cy); c.scale(1, 0.2)
        c.set_source_rgba(1, 0.95, 0.6, 0.85 * a); c.set_line_width(28)
        c.arc(0, 0, R * 1.75, math.pi * 0.18, math.pi * 0.82); c.stroke(); c.restore()
        for ang in (0.18, 0.5, 0.82):
            rx, ry = cx + R * 1.75 * math.cos(math.pi * ang), cy + R * 1.75 * 0.2 * math.sin(math.pi * ang)
            dashed(c, px, py - 46, rx, ry, (1, 0.95, 0.6), 0.9 * a, off=-t * 60)
        pin(c, px, py, k)
        text(c, "EUROPE", px, py - 120, 64, INK, 1, scale=k, ow=0.16)
        text(c, "YOU SEE THIS PART", 540, 1230, 54, GOLD, a, ow=0.16)


def s_europe(c, t):
    u = t - T["arch"] + 0.35; d = T["brand"] - T["arch"] + 0.35
    p = smooth(u / d)
    draw_par(c, "europe", 1.06 + 0.06 * p, 0.5, 0.42 - 0.06 * p, px=lerp(40, -40, p), py=lerp(0, 30, p), push=0.08 * p)
    for k in range(3):
        q = ((t * 0.3 + k / 3) % 1.0)
        glow(c, lerp(120, 1180, q), lerp(1250, -100, q) + 0 * k, 150, (1, 0.95, 0.85), 0.2)
    particles(c, t, (1, 0.93, 0.8), 0.45, vx=-8, vy=-4, size=0.7)
    text(c, "HORIZON TO HORIZON", 540, 300, 74, INK, 1, scale=popin(t, T["arch"] + 0.9), ow=0.15)
    vignette(c, 0.3)


def s_brand(c, t):
    u = t - T["brand"]
    draw_par(c, "europe", 1.12 + 0.02 * u, 0.5, 0.36, px=-40 - 20 * u, py=30, push=0.08)
    c.set_source_rgba(0.05, 0.03, 0.12, 0.62); c.paint()
    draw_scratch(c, u, 540, 760, scale=0.95, skin=(1.0, 0.8, 0.62), accent=GOLD, ink=INK, hair=(0.2, 0.13, 0.1))


def s_night(c, t):
    u = t - T["night"]; d = T["bright"] - T["night"]
    p = smooth(u / d)
    draw_par(c, "night", 1.12 - 0.06 * p, 0.5, 0.45, px=lerp(-50, 50, p), py=0, push=0.06 * p)
    glow(c, 640, 520, 700, (0.85, 0.95, 1), 0.18 + 0.06 * math.sin(t * 2.4))
    particles(c, t, SILVER, 0.5, vx=-14, vy=4, size=0.7)
    a = seg(u, 0.3, 0.6)
    x0, y0 = 260, 300
    c.set_source_rgba(0.05, 0.06, 0.15, 0.8 * a); rr(c, x0, y0, 560, 92, 46); c.fill()
    text(c, "DARKNESS", x0 + 40, y0 + 46, 34, SILVER, a, align="l", outline=False)
    lv = 0.06 + 0.04 * math.sin(t * 9)
    c.set_source_rgba(0.2, 0.22, 0.35, a); rr(c, x0 + 240, y0 + 30, 280, 32, 16); c.fill()
    c.set_source_rgba(*ICE, a); rr(c, x0 + 240, y0 + 30, 280 * lv * 3, 32, 16); c.fill()
    text(c, "0%", x0 + 590, y0 + 46, 40, INK, a, align="l") if False else None
    vignette(c, 0.35)


def s_bedroom(c, t):
    u = t - T["bright"]; d = T["stand"] - T["bright"]
    p = smooth(u / d)
    draw_par(c, "bedroom", 1.05 + 0.1 * p, 0.55, 0.55, px=lerp(30, -30, p), py=lerp(-20, 20, p), push=0.1 * p)
    # a janela pisca de luz (o céu nunca escurece)
    glow(c, 420, 520, 520, (0.92, 0.96, 1), 0.2 + 0.08 * math.sin(t * 5))
    card(c, t, T["bright"] + 0.7, [("SLEEP SCHEDULE:", INK), ("CANCELLED", RED)], 120, 300, 560, RED, t1=T["stand"] - 0.05)
    vignette(c, 0.4)


def s_cross(c, t):
    """esquema em corte: a Terra de lado, o anel no plano do equador. O observador desce da Europa (45°N)
    até ao equador: a fatia de anel que vê passa de um arco largo a uma linha fina por cima da cabeça."""
    u = t - T["stand"]
    space_bg(c, t, top=(0.02, 0.05, 0.12), bot=(0.0, 0.01, 0.04))
    cx, cy, R = 360, 940, 250
    lat = lerp(45, 0, smooth((t - T["stand"] - 0.3) / (T["shrink"] - T["stand"])))
    # anel de perfil (dos dois lados)
    for sgn in (1, -1):
        x0, x1 = cx + sgn * R * 1.4, cx + sgn * R * 2.6
        c.set_source_rgba(*SILVER, 0.95); c.set_line_width(14); c.move_to(x0, cy); c.line_to(x1, cy); c.stroke()
    # planeta
    g = cairo.RadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.1, cx, cy, R)
    g.add_color_stop_rgb(0, 0.2, 0.55, 0.9); g.add_color_stop_rgb(1, 0.05, 0.2, 0.5)
    c.set_source(g); c.arc(cx, cy, R, 0, 2 * math.pi); c.fill()
    dashed(c, cx - R * 1.1, cy, cx + R * 1.1, cy, (1, 1, 1), 0.35, w=3)
    text(c, "EQUATOR", cx - R * 0.55, cy + 30, 30, INK, 0.7, outline=False)
    # observador
    la = math.radians(lat)
    ox, oy = cx + R * math.cos(la), cy - R * math.sin(la)
    nx, ny = math.cos(la), -math.sin(la)
    # fatia do anel que vê (cunha de visão até às duas pontas do anel do seu lado)
    ex0, ex1 = cx + R * 1.4, cx + R * 2.6
    c.set_source_rgba(1, 0.85, 0.35, 0.28); c.move_to(ox, oy); c.line_to(ex0, cy); c.line_to(ex1, cy); c.close_path(); c.fill()
    for ex in (ex0, ex1): dashed(c, ox, oy, ex, cy, GOLD, 0.95, w=4, off=-t * 50)
    # boneco
    c.save(); c.translate(ox, oy); c.rotate(math.atan2(ny, nx) + math.pi / 2)
    c.set_source_rgba(*RED, 1); c.set_line_width(8); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(0, 0); c.line_to(0, -44); c.stroke(); c.arc(0, -58, 13, 0, 2 * math.pi); c.fill(); c.restore()
    text(c, f"{int(round(lat))}°N" if lat > 0.5 else "0°", ox + nx * 110 - 10, oy + ny * 110 - 10, 46, INK, 1, ow=0.16)
    # o que vê: ícone do céu (arco → linha)
    k = clamp(lat / 45)
    bx, by = 540, 380
    c.set_source_rgba(0.1, 0.2, 0.4, 0.85); rr(c, bx - 240, by - 150, 480, 260, 40); c.fill()
    c.set_source_rgba(*SILVER, 1); c.set_line_width(lerp(6, 34, k))
    if k > 0.05:
        c.save(); c.translate(bx, by + 90); c.scale(1, max(0.05, k))
        c.arc(0, 0, 190, math.pi * 1.05, math.pi * 1.95); c.restore(); c.stroke()
    else:
        c.move_to(bx, by + 100); c.line_to(bx, by - 140); c.stroke()
    c.set_source_rgba(0.35, 0.6, 0.35, 1); c.rectangle(bx - 240, by + 70, 480, 40); c.fill()
    text(c, "ARCH" if k > 0.35 else ("THIN LINE" if k < 0.08 else "…"), bx, by - 190, 56, GOLD, 1, ow=0.16)


def s_equator(c, t):
    u = t - T["eqimg"]; d = T["inw"] - T["eqimg"]
    p = smooth(u / d)
    fy = 0.55 - 0.2 * p
    base, x0, y0 = draw_par(c, "equator", 1.06 + 0.06 * p, 0.5, fy, px=lerp(20, -20, p), py=lerp(-40, 40, p), push=0.06 * p)
    lx = (768 - x0) * base
    a = 0.8
    c.set_source_rgba(1, 1, 1, 0.6 * a); c.set_line_width(4); c.move_to(lx, -10); c.line_to(lx, (2190 - y0) * base); c.stroke()
    for k in range(2):
        q = (t * 0.6 + k / 2) % 1
        glow(c, lx, lerp((2190 - y0) * base, -50, q), 60, (1, 1, 1), 0.55 * a)
    particles(c, t, (1, 1, 1), 0.35, vx=-12, vy=0, size=0.6)
    k = popin(t, T["eqimg"] + 0.15, 0.25)
    text(c, "STRAIGHT ABOVE YOU", 540, 300, 70, INK, 1, scale=k, ow=0.16)
    card(c, t, T["above"] - 0.1, [("EQUATOR PEOPLE:", INK), ("\"WHAT RINGS?\"", GOLD)], 90, 820, 560, GOLD,
         bg=(0.02, 0.25, 0.4), t1=T["inw"] - 0.05, rot=0.03)
    vignette(c, 0.25)


def s_season(c, t):
    """esquema: o Sol à esquerda, raios; no inverno do norte o anel tapa o Sol a metade do planeta"""
    u = t - T["inw"]
    space_bg(c, t)
    glow(c, -60, 820, 520, (1, 0.85, 0.4), 0.85, r0=60)
    c.set_source_rgba(1, 0.9, 0.5, 1); c.arc(-60, 820, 150, 0, 2 * math.pi); c.fill()
    text(c, "SUN", 70, 560, 50, GOLD, 1, ow=0.16)
    cx, cy, R = 660, 820, 250
    sh = seg(t, T["shadow"], T["shadow"] + 0.8)
    # raios
    for i in range(9):
        y = cy - R * 1.1 + i * R * 0.28
        blocked = y < cy - R * 0.05 and sh > 0
        xend = cx - R * 1.35 if blocked else cx - R * math.sqrt(max(0, 1 - ((y - cy) / R) ** 2))
        off = (t * 300 + i * 40) % 80
        c.save(); c.set_source_rgba(1, 0.9, 0.5, 0.75); c.set_line_width(5); c.set_dash([40, 40], -off)
        c.move_to(110, y); c.line_to(xend, y); c.stroke(); c.restore()
        if blocked:
            c.set_source_rgba(1, 0.9, 0.5, 0.9 * sh); c.arc(xend, y, 9, 0, 2 * math.pi); c.fill()
    globe(c, cx, cy, R, -0.3 + u * 0.15, t, shadow=sh, ring=1.0, ring_tilt=-0.35, sun=(-1, 0.0))
    text(c, "RING SHADOW", cx, cy - R - 120, 58, ICE, sh, ow=0.16)
    text(c, "WINTER", 540, 300, 96, ICE, 1, scale=popin(t, T["inw"] + 0.1), ow=0.14)


def s_you(c, t):
    u = t - T["half"] + 0.3
    space_bg(c, t)
    R = 380 + 30 * u
    rot = -0.17 + 0.05 * u
    globe(c, 540, 880, R, rot, t, shadow=1.0, ring=1.0, ring_tilt=-0.18, sun=(-1, 0.05))
    px, py, z = proj_pt(540, 880, R, rot, 10, 47)
    k = popin(t, T["half"] - 0.1, 0.25)
    pin(c, px, py, k)
    text(c, "YOU", px, py - 130, 64, INK, 1, scale=k, ow=0.16)


def s_winterimg(c, t):
    u = t - T["colder"] + 0.05; d = T["every2"] - T["colder"] + 0.05
    p = smooth(u / d)
    draw_par(c, "winter", 1.06 + 0.08 * p, 0.5, 0.5, px=lerp(-30, 30, p), py=0, push=0.1 * p)
    # sombra dos anéis: riscas diagonais escuras a deslizar
    c.save(); c.rotate(-0.35)
    for i in range(-3, 9):
        y = i * 300 + (t * 25) % 300
        c.set_source_rgba(0.06, 0.08, 0.2, 0.26); c.rectangle(-600, y, 2600, 120); c.fill()
    c.restore()
    particles(c, t, (0.95, 0.97, 1), 0.85, vx=-6, vy=30, size=0.9)
    text(c, "COLDER DAYS", 540, 300, 84, ICE, 1, scale=popin(t, T["colder"] - 0.05), ow=0.15)
    text(c, "LONGER NIGHTS", 540, 405, 84, (0.8, 0.75, 1.0), 1, scale=popin(t, T["longer"] - 0.05), ow=0.15)
    card(c, t, T["longer"] + 0.2, [("HEATING BILL:", INK), ("x3", RED)], 560, 560, 420, RED, rot=0.04)
    vignette(c, 0.35)


def s_sunset(c, t):
    u = t - T["every2"]; d = T["sky"] - T["every2"]
    p = smooth(u / d)
    draw_par(c, "sunset", 1.06 + 0.06 * p, 0.45, 0.45, px=lerp(-40, 30, p), py=0, push=0.06 * p)
    particles(c, t, (1, 0.9, 0.6), 0.75, vx=-16, vy=-8, size=0.9)
    glow(c, 820, 900, 300, (1, 0.6, 0.3), 0.18 + 0.05 * math.sin(t * 3))
    chat(c, t, T["sunset"] + 0.15, 90, 640)
    vignette(c, 0.3)


def hexa(c, x, y, r, rot, col, a):
    c.save(); c.translate(x, y); c.rotate(rot); c.set_source_rgba(*col, a); c.set_line_width(max(2, r * 0.12))
    for i in range(6):
        ang = i * math.pi / 3
        c.move_to(0, 0); c.line_to(r * math.cos(ang), r * math.sin(ang))
        for s in (0.5,):
            bx, by = r * s * math.cos(ang), r * s * math.sin(ang)
            c.move_to(bx, by); c.line_to(bx + r * 0.25 * math.cos(ang + 0.8), by + r * 0.25 * math.sin(ang + 0.8))
            c.move_to(bx, by); c.line_to(bx + r * 0.25 * math.cos(ang - 0.8), by + r * 0.25 * math.sin(ang - 0.8))
    c.stroke(); c.restore()


def s_ice(c, t):
    """grande plano dos anéis ao pôr do sol: são feitos de gelo"""
    u = t - T["sky"]; d = T["but"] - T["sky"]
    p = smooth(u / d)
    draw_par(c, "sunset", 2.1 + 0.3 * p, 0.72, 0.2, px=lerp(30, -30, p), py=0, push=0.1 * p)
    rnd = random.Random(4)
    for i in range(14):
        x = rnd.random() * W; y = rnd.random() * 1300 + 150; r = 30 + rnd.random() * 60
        k = seg(t, T["ice"] - 0.6 + i * 0.04, T["ice"] - 0.3 + i * 0.04)
        hexa(c, x + 20 * math.sin(t + i), y - 30 * u, r * k, t * 0.6 + i, (0.92, 0.97, 1), 0.85 * k)
    text(c, "ICE", 540, 300, 130, ICE, 1, scale=popin(t, T["ice"] - 0.05), ow=0.12)
    vignette(c, 0.3)


def s_tease(c, t):
    """'But wait until you hear the strangest part': a Terra gira para trás e o contador de anos dispara"""
    u = t - T["but"]; d = T["scientists"] - T["but"]
    space_bg(c, t)
    globe(c, 540, 900, 300, 0.6 - u * 3.0 * (1 + u), t, ring=0.0, sun=(-1, -0.2))
    c.set_source_rgba(0, 0, 0, 0.2); c.paint()
    # contador a andar para trás (sem revelar o número)
    yr = int(2026 - (10 ** (1 + 7.5 * smooth(u / d))))
    s = f"{yr:,}" if yr > 0 else f"{-yr:,} BC"
    text(c, "REWINDING…", 540, 1260, 50, GOLD, seg(u, 0.1, 0.3), ow=0.16)
    text(c, s, 540, 1350, 76, INK, seg(u, 0.1, 0.3), ow=0.14)


def s_ordo(c, t):
    u = t - T["scientists"]; d = T["rings2"] - T["scientists"]
    p = smooth(u / d)
    draw_par(c, "ordovician", 1.06 + 0.08 * p, 0.5, lerp(0.6, 0.4, p), px=lerp(30, -30, p), py=lerp(-30, 30, p), push=0.1 * p)
    particles(c, t, (0.9, 1, 1), 0.35, vx=6, vy=-14, size=0.6)
    text(c, "IT WAS REAL", 540, 300, 100, GOLD, 1, scale=popin(t, T["really"] - 0.05), ow=0.14)
    vignette(c, 0.3)


def s_reveal(c, t):
    """Terra do Ordovícico com anel; '466 MILLION YEARS AGO'"""
    u = t - T["rings2"]
    space_bg(c, t, top=(0.06, 0.03, 0.08), bot=(0.01, 0.0, 0.02))
    ring = seg(t, T["rings2"], T["rings2"] + 0.4)
    R = 300 + 30 * smooth(u / 3)
    globe(c, 540, 740, R, 0.3 + u * 0.15, t, land=(0.62, 0.48, 0.32), sea1=(0.15, 0.48, 0.6), sea2=(0.04, 0.16, 0.25),
          conts=CONT_OLD, ring=ring, ring_col=(0.95, 0.85, 0.7), ring_tilt=0.12, glowc=(1.0, 0.7, 0.4), ice_caps=False)
    rnd = random.Random(9)
    for _ in range(60):
        ang = rnd.random() * 6.28 + t * 0.3; rr_ = R * (1.4 + rnd.random() * 0.9)
        x = 540 + math.cos(ang) * rr_; y = 740 + math.sin(ang) * rr_ * 0.2 + math.cos(ang) * rr_ * 0.12
        sparkle(c, x, y, 4 + rnd.random() * 7, (1, 0.95, 0.85), ring * (0.4 + 0.6 * abs(math.sin(t * 4 + ang))))
    text(c, "IT WAS REAL", 540, 300, 92, GOLD, 1, ow=0.14)
    if t >= T["n466"] - 0.05:
        k = popin(t, T["n466"] - 0.05, 0.3)
        text(c, "466", 540, 1130, 220, INK, 1, scale=k, ow=0.1)
        text(c, "MILLION YEARS AGO", 540, 1275, 68, GOLD, 1, scale=popin(t, T["n466"] + 0.5), ow=0.15)


def s_end(c, t):
    """'Which means, one day…': a Terra de hoje com um anel fantasma; a câmara mergulha e, nos últimos
    frames, a rua do frame 0 abre-se (último frame = frame 0, cam_hook em t negativo)."""
    u = t - T["which"]
    TR = 0.5
    tr0 = T_END - TR
    space_bg(c, t)
    zoom = 1 + 2.6 * smooth((u - 0.4) / (T_END - T["which"] - 0.4)) ** 2
    R = 300 * zoom
    ghost = 0.35 + 0.15 * math.sin(t * 8)
    globe(c, 540, 860 + R * 0.5 * (zoom - 1) / 2.6, R, 0.2 + u * 0.1, t, ring=ghost * seg(u, 0, 0.4), sun=(-1, -0.2))
    text(c, "ONE DAY…?", 540, 330, 96, INK, seg(u, 0.5, 0.8) * (1 - seg(t, tr0 - 0.1, tr0 + 0.1)), ow=0.14)
    if t >= tr0:
        k = clamp((t - tr0) / (TR - 1 / FPS))
        th = t - T_END
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cc = cairo.Context(s); s_hook(cc, th)
        sc = lerp(0.55, 1.0, ease(k))
        c.save(); c.translate(W / 2, H / 2); c.scale(sc, sc); c.translate(-W / 2, -H / 2)
        c.set_source_surface(s, 0, 0); c.paint_with_alpha(ease(k) if k < 1 else 1.0); c.restore()


SCENES = [
    (0.0, T["every"] - 0.25, s_hook), (T["every"] - 0.25, T["frm"], s_everywhere), (T["frm"], T["arch"] - 0.35, s_europe_map),
    (T["arch"] - 0.35, T["brand"], s_europe), (T["brand"], T["night"], s_brand), (T["night"], T["bright"], s_night),
    (T["bright"], T["stand"], s_bedroom), (T["stand"], T["eqimg"], s_cross), (T["eqimg"], T["inw"], s_equator),
    (T["inw"], T["half"] - 0.3, s_season), (T["half"] - 0.3, T["colder"] - 0.05, s_you),
    (T["colder"] - 0.05, T["every2"], s_winterimg), (T["every2"], T["sky"], s_sunset), (T["sky"], T["but"], s_ice),
    (T["but"], T["scientists"], s_tease), (T["scientists"], T["rings2"], s_ordo), (T["rings2"], T["which"], s_reveal),
    (T["which"], 99, s_end),
]
NO_PUNCH = {s_brand, s_end}
CHAPTERS = [T["frm"], T["night"], T["stand"], T["inw"], T["every2"], T["but"], T["scientists"]]

