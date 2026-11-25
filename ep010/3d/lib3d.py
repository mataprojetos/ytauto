"""EP010 3D (pedido do dono: visual 3D como a referência 'ConstruindoOMundoBR'): biblioteca Blender (bpy, Cycles CPU).
Personagem: o mesmo rapaz (cabelo castanho espetado, capuz malva com cordões brancos, calças de ganga, ténis bordô),
feito como boneco 3D estilizado (cabeça grande, olhos grandes) para poder ser animado e posto em qualquer cena."""
import bpy, math, random
from mathutils import Vector, Euler

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.cycles.samples = 12; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 3; sc.cycles.transparent_max_bounces = 8; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 1; sc.cycles.transmission_bounces = 1
    sc.render.resolution_x = 720; sc.render.resolution_y = 1280; sc.render.fps = 30
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    return sc

def L(c):
    """sRGB (como se escolhe num desenho) → linear (o que o Blender espera)"""
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def mat(name, col, rough=0.6, emit=0.0, metal=0.0):
    col = L(col)
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def noise_mat(name, c1, c2, scale=6.0, rough=0.8, detail=6, bump=0.25, ramp=(0.45, 0.6)):
    c1, c2 = L(c1), L(c2)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = rough
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
    r = nt.nodes.new("ShaderNodeValToRGB"); r.color_ramp.elements[0].position = ramp[0]; r.color_ramp.elements[1].position = ramp[1]
    r.color_ramp.elements[0].color = (*c1, 1); r.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(n.outputs["Fac"], r.inputs["Fac"]); nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
    nt.links.new(n.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def smooth(o, sub=2):
    for p in o.data.polygons: p.use_smooth = True
    if sub:
        m = o.modifiers.new("sub", 'SUBSURF'); m.levels = sub; m.render_levels = sub
    return o

def setp(o, parent):
    bpy.context.view_layer.update()
    o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()


def sphere(name, loc, r, m, scale=(1, 1, 1), parent=None, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: setp(o, parent)
    return o

def capsule(name, a, b, r, m, parent=None):
    a, b = Vector(a), Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(a + b) / 2, vertices=24)
    o = bpy.context.object; o.name = name
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    o.data.materials.append(m); smooth(o, 0)
    for end in (a, b):
        sphere(name + "_e", end, r, m, parent=parent)
    if parent: setp(o, parent)
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    bpy.ops.object.empty_add(location=loc); e = bpy.context.object; e.name = name
    if parent: setp(e, parent)
    return e

# ---------------- personagem ----------------
SKIN = (0.96, 0.72, 0.56); HAIR = (0.33, 0.19, 0.09); HOOD = (0.55, 0.38, 0.46); JEANS = (0.17, 0.25, 0.42)
SHOE = (0.45, 0.12, 0.16); WHITE = (0.95, 0.95, 0.95); INK = (0.04, 0.03, 0.03)

def boy(name="boy", loc=(0, 0, 0), pose="panic", face="panic"):
    """boneco estilo brinquedo (~2.5 de altura, cabeça grande); origem nos pés.
    pose: panic | genius | stand | cheer | relief | paint | remote ; face: panic | smug | happy | relief | worried"""
    M = dict(skin=mat("skin", SKIN, 0.5), hair=mat("hair", HAIR, 0.65), hood=noise_mat("hood", HOOD, tuple(c * 0.9 for c in HOOD), 50, 0.85, 3, 0.05),
             jeans=noise_mat("jeans", JEANS, tuple(c * 0.85 for c in JEANS), 70, 0.8, 3, 0.05), shoe=mat("shoe", SHOE, 0.45),
             white=mat("white", WHITE, 0.35), ink=mat("ink", INK, 0.25), mouth=mat("mouth", (0.42, 0.06, 0.08), 0.5),
             tongue=mat("tongue", (0.92, 0.42, 0.45), 0.5), gloss=mat("eyegloss", (1, 1, 1), 0.1), cheek=mat("cheek", (0.98, 0.55, 0.5), 0.6))
    root = empty(name, loc)
    for sx in (-1, 1):   # pernas curtas + ténis
        capsule(f"leg{sx}", (0.16 * sx, 0, 0.22), (0.15 * sx, 0, 0.62), 0.13, M["jeans"], root)
        sphere(f"shoe{sx}", (0.17 * sx, -0.07, 0.1), 0.15, M["shoe"], (1.05, 1.5, 0.72), root)
        sphere(f"sole{sx}", (0.17 * sx, -0.07, 0.03), 0.15, M["white"], (1.1, 1.55, 0.3), root)
    sphere("hip", (0, 0, 0.72), 0.32, M["jeans"], (1, 0.82, 0.55), root)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.36, depth=0.62, location=(0, 0, 1.08), vertices=32)
    tor = bpy.context.object; tor.name = "torso"; tor.scale = (1, 0.82, 1); tor.data.materials.append(M["hood"])
    bv = tor.modifiers.new("bev", 'BEVEL'); bv.width = 0.14; bv.segments = 6; smooth(tor, 1); setp(tor, root)
    sphere("pocket", (0, -0.29, 0.95), 0.2, M["hood"], (1.15, 0.3, 0.55), root)
    bpy.ops.mesh.primitive_torus_add(location=(0, 0.04, 1.42), major_radius=0.27, minor_radius=0.1)
    tr = bpy.context.object; tr.name = "hoodring"; tr.data.materials.append(M["hood"]); smooth(tr, 1); setp(tr, root)
    for sx in (-1, 1):
        capsule(f"string{sx}", (0.08 * sx, -0.3, 1.36), (0.09 * sx, -0.33, 1.12), 0.02, M["white"], root)
    P = {
        "panic":  [((0.36, 0, 1.3), (0.5, -0.25, 1.3), (0.38, -0.36, 1.82)), ((-0.36, 0, 1.3), (-0.5, -0.25, 1.3), (-0.38, -0.36, 1.82))],
        "genius": [((0.36, 0, 1.3), (0.58, -0.2, 1.55), (0.36, -0.38, 2.1)), ((-0.36, 0, 1.3), (-0.6, -0.05, 1.05), (-0.4, -0.15, 0.92))],
        "stand":  [((0.36, 0, 1.3), (0.46, 0, 1.02), (0.48, -0.05, 0.75)), ((-0.36, 0, 1.3), (-0.46, 0, 1.02), (-0.48, -0.05, 0.75))],
        "cheer":  [((0.36, 0, 1.3), (0.62, 0, 1.65), (0.6, -0.05, 2.1)), ((-0.36, 0, 1.3), (-0.62, 0, 1.65), (-0.6, -0.05, 2.1))],
        "relief": [((0.36, 0, 1.3), (0.62, -0.2, 1.6), (0.18, -0.45, 2.25)), ((-0.36, 0, 1.3), (-0.48, 0, 1.02), (-0.5, -0.05, 0.78))],
        "remote": [((0.36, 0, 1.3), (0.42, -0.3, 1.08), (0.12, -0.5, 1.15)), ((-0.36, 0, 1.3), (-0.42, -0.3, 1.08), (-0.12, -0.5, 1.15))],
        "paint":  [((0.36, 0, 1.3), (0.5, -0.35, 1.12), (0.25, -0.6, 1.02)), ((-0.36, 0, 1.3), (-0.4, -0.35, 1.1), (-0.1, -0.6, 1.25))],
    }[pose]
    arms = []
    for i, (sh, el, ha) in enumerate(P):
        capsule(f"uarm{i}", sh, el, 0.1, M["hood"], root); capsule(f"farm{i}", el, ha, 0.095, M["hood"], root)
        arms.append(sphere(f"hand{i}", ha, 0.12, M["skin"], (1, 0.8, 1.05), root))
    HZ = 2.0
    head = empty("head", (0, 0, HZ), root)
    sphere("skull", (0, 0, HZ), 0.6, M["skin"], (1, 0.93, 0.96), head)
    for sx in (-1, 1):
        sphere(f"ear{sx}", (0.58 * sx, 0.02, HZ - 0.02), 0.12, M["skin"], (0.55, 0.8, 1), head)
        sphere(f"cheek{sx}", (0.33 * sx, -0.47, HZ - 0.17), 0.09, M["cheek"], (1, 0.4, 0.7), head)
    sphere("haircap", (0, 0.08, HZ + 0.15), 0.62, M["hair"], (1.03, 0.98, 0.82), head)
    sphere("fringe", (0.05, -0.38, HZ + 0.36), 0.32, M["hair"], (1.5, 0.6, 0.45), head)
    rnd = random.Random(3)
    for i in range(7):   # madeixas espetadas
        a = -0.75 + i * 0.25
        bpy.ops.mesh.primitive_cone_add(radius1=0.17, depth=0.5, location=(0.42 * math.sin(a), -0.1 + 0.05 * rnd.random(), HZ + 0.6 + 0.04 * rnd.random()))
        c = bpy.context.object; c.rotation_euler = (math.radians(-40 - 12 * rnd.random()), math.radians(35 * math.sin(a)), 0)
        c.data.materials.append(M["hair"]); smooth(c, 1); setp(c, head)
    eye_open = {"panic": 1.3, "worried": 1.15, "smug": 0.5, "relief": 0.2, "happy": 1.0}[face]
    for sx in (-1, 1):
        sphere(f"eyew{sx}", (0.21 * sx, -0.5, HZ + 0.03), 0.17, M["white"], (1, 0.5, eye_open), head)
        if face != "relief":
            pr = 0.065 if face == "panic" else 0.085
            sphere(f"pupil{sx}", (0.2 * sx, -0.58, HZ + 0.03 - (0.03 if face == "smug" else 0)), pr, M["ink"], (1, 0.45, 1), head)
            sphere(f"glint{sx}", (0.18 * sx, -0.62, HZ + 0.06), 0.022, M["gloss"], parent=head)
        else:
            capsule(f"lid{sx}", (0.11 * sx, -0.58, HZ + 0.01), (0.31 * sx, -0.54, HZ + 0.03), 0.025, M["ink"], head)
        tilt = {"panic": 0.09, "worried": 0.1, "smug": -0.07, "happy": 0.0, "relief": 0.05}[face]
        lift = 0.06 if face == "panic" else 0.0
        capsule(f"brow{sx}", (0.1 * sx, -0.56, HZ + 0.27 + lift + tilt), (0.32 * sx, -0.5, HZ + 0.25 + lift - tilt), 0.035, M["hair"], head)
    sphere("nose", (0, -0.6, HZ - 0.08), 0.065, M["skin"], (1, 0.8, 1), head)
    if face in ("panic", "worried"):
        sphere("mouth", (0, -0.53, HZ - 0.3), 0.13, M["mouth"], (1, 0.45, 1.25 if face == "panic" else 0.6), head)
        sphere("teeth", (0, -0.58, HZ - 0.2), 0.09, M["white"], (1.1, 0.4, 0.3), head)
        sphere("tongue", (0, -0.58, HZ - 0.38), 0.075, M["tongue"], (1, 0.45, 0.45), head)
    else:
        w_ = 0.2 if face != "smug" else 0.17
        bpy.ops.mesh.primitive_torus_add(location=(0, -0.53, HZ - 0.2), major_radius=w_, minor_radius=0.04, rotation=(math.radians(78), 0, 0))
        m_ = bpy.context.object; m_.name = "smile"; m_.data.materials.append(M["mouth"]); setp(m_, head)
        m_.scale = (1.0, 1.0, 0.5 if face != "smug" else 0.35)
        if face == "smug": m_.rotation_euler = (math.radians(78), math.radians(10), 0)
    return root, head, arms


# ---------------- espaço ----------------
def space_world(strength=1.0):
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True; nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 180
    gr = nt.nodes.new("ShaderNodeTexGradient"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.035
    mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0; mr.clamp = True
    nt.links.new(tc.outputs["Generated"], vo.inputs["Vector"]); nt.links.new(vo.outputs["Distance"], mr.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    mix.inputs["A"].default_value = (0.002, 0.002, 0.01, 1); mix.inputs["B"].default_value = (1, 0.95, 0.85, 1)
    p = nt.nodes.new("ShaderNodeMath"); p.operation = 'POWER'; p.inputs[1].default_value = 6
    nt.links.new(mr.outputs["Result"], p.inputs[0]); nt.links.new(p.outputs[0], mix.inputs["Factor"])
    # nebulosa roxa suave
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6
    nr = nt.nodes.new("ShaderNodeValToRGB"); nr.color_ramp.elements[0].color = (0.002, 0.002, 0.012, 1); nr.color_ramp.elements[1].color = (0.035, 0.008, 0.06, 1)
    nr.color_ramp.elements[0].position = 0.45; nr.color_ramp.elements[1].position = 0.8
    nt.links.new(tc.outputs["Generated"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], nr.inputs["Fac"])
    nt.links.new(nr.outputs["Color"], mix.inputs["A"])
    nt.links.new(mix.outputs["Result"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = strength
    return w

def earth(loc, r):
    m = bpy.data.materials.new("earth"); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.55
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 3.2; n.inputs["Detail"].default_value = 8; n.inputs["Roughness"].default_value = 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB"); E = ramp.color_ramp.elements
    E[0].position = 0.52; E[0].color = (*L((0.08, 0.38, 0.85)), 1); E[1].position = 0.53; E[1].color = (*L((0.3, 0.7, 0.28)), 1)
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    o = sphere("earth", loc, r, m, seg=96)
    mc = bpy.data.materials.new("clouds"); mc.use_nodes = True; nt = mc.node_tree
    bc = nt.nodes["Principled BSDF"]; bc.inputs["Base Color"].default_value = (1, 1, 1, 1)
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 4; n2.inputs["Detail"].default_value = 6
    r2 = nt.nodes.new("ShaderNodeValToRGB"); r2.color_ramp.elements[0].position = 0.55; r2.color_ramp.elements[1].position = 0.65
    nt.links.new(n2.outputs["Fac"], r2.inputs["Fac"]); nt.links.new(r2.outputs["Color"], bc.inputs["Alpha"])
    c = None
    # atmosfera (halo azul)
    ma = mat("atmo", (0.3, 0.6, 1.0), 1, emit=1.5); ma.blend_method = 'BLEND' if hasattr(ma, 'blend_method') else None
    return o, c

def crater_mat(name, c1=(0.42, 0.2, 0.08), c2=(0.85, 0.48, 0.2), scale=2.2):
    c1, c2 = L(c1), L(c2)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.85
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale; vo.inputs["Randomness"].default_value = 0.9
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    # cratera: tigela dentro (dist pequena) e borda levantada
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.12; mr.inputs["From Max"].default_value = 0.32
    nt.links.new(vo.outputs["Distance"], mr.inputs["Value"])
    rim = nt.nodes.new("ShaderNodeMath"); rim.operation = 'PINGPONG'; rim.inputs[1].default_value = 0.5
    nt.links.new(mr.outputs["Result"], rim.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale * 3; nz.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    h = nt.nodes.new("ShaderNodeMath"); h.operation = 'ADD'
    nt.links.new(mr.outputs["Result"], h.inputs[0])
    s = nt.nodes.new("ShaderNodeMath"); s.operation = 'MULTIPLY'; s.inputs[1].default_value = 0.35
    nt.links.new(nz.outputs["Fac"], s.inputs[0]); nt.links.new(s.outputs[0], h.inputs[1])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.9; bp.inputs["Distance"].default_value = 0.2
    nt.links.new(h.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); E = ramp.color_ramp.elements
    E[0].position = 0.0; E[0].color = (*c1, 1); E[1].position = 0.9; E[1].color = (*c2, 1)
    cm = nt.nodes.new("ShaderNodeMath"); cm.operation = 'MULTIPLY_ADD'; cm.inputs[1].default_value = 0.8; cm.inputs[2].default_value = 0.0
    nt.links.new(h.outputs[0], cm.inputs[0]); nt.links.new(cm.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def asteroid(name, loc, r, seed=1, fire=False):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=5, location=loc)
    o = bpy.context.object; o.name = name
    tex2 = bpy.data.textures.new(name + "t2", 'CLOUDS'); tex2.noise_scale = 0.9 * r
    d2 = o.modifiers.new("lumps", 'DISPLACE'); d2.texture = tex2; d2.strength = 0.22 * r; d2.mid_level = 0.5
    o.scale = (1.0, 0.9, 0.85)
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(crater_mat(name + "m", scale=1.6 / r * 2.4))
    return o


def stars(n=500, dist=70, seed=2, size=0.12):
    """estrelas: pequenas esferas emissivas espalhadas numa casca à volta da cena"""
    import random as _r
    rnd = _r.Random(seed); m = mat("star", (1, 0.95, 0.85), 1, emit=12)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=size, subdivisions=1); base = bpy.context.object; base.data.materials.append(m)
    me = base.data
    for i in range(n):
        th = rnd.uniform(0, 6.283); ph = math.acos(rnd.uniform(-1, 1)); d = dist * rnd.uniform(0.8, 1.2)
        o = bpy.data.objects.new(f"star{i}", me); bpy.context.scene.collection.objects.link(o)
        o.location = (d * math.sin(ph) * math.cos(th), d * math.sin(ph) * math.sin(th), d * math.cos(ph))
        s = rnd.uniform(0.5, 2.2); o.scale = (s, s, s)
    bpy.data.objects.remove(base)


def fire_trail(target, length, r, direction=(1, 1, 1)):
    """cauda de fogo: cone com emissão e ruído, atrás do asteroide (oposto ao movimento)"""
    m = bpy.data.materials.new("fire"); m.use_nodes = True; nt = m.node_tree
    out = nt.nodes["Material Output"]; nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3; nz.inputs["Detail"].default_value = 4
    ramp = nt.nodes.new("ShaderNodeValToRGB"); E = ramp.color_ramp.elements
    E[0].position = 0.0; E[0].color = (1, 0.75, 0.25, 1); E[1].position = 0.7; E[1].color = (0.8, 0.12, 0.01, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 3
    al = nt.nodes.new("ShaderNodeMath"); al.operation = 'MULTIPLY'
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs["Z"], inv.inputs[1]); nt.links.new(inv.outputs[0], al.inputs[0]); nt.links.new(nz.outputs["Fac"], al.inputs[1])
    nt.links.new(tc.outputs["Generated"], nz.inputs["Vector"])
    nt.links.new(al.outputs[0], mx.inputs["Fac"]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r * 0.15, depth=length, vertices=48)
    c = bpy.context.object; c.name = "fire"; c.data.materials.append(m); smooth(c, 1)
    dv = Vector(direction).normalized()
    c.rotation_mode = 'QUATERNION'; c.rotation_quaternion = dv.to_track_quat('Z', 'Y')
    c.location = Vector(target.location) + dv * (length / 2 - r * 0.3)
    return c

def sun_light(rot=(0.9, 0.2, 0.6), energy=3.5, col=(1, 0.93, 0.85)):
    bpy.ops.object.light_add(type='SUN', rotation=rot); l = bpy.context.object; l.data.energy = energy; l.data.color = col
    l.data.angle = math.radians(8); return l

def area_light(loc, energy, col, size=5, target=(0, 0, 1)):
    bpy.ops.object.light_add(type='AREA', location=loc); l = bpy.context.object
    l.data.energy = energy; l.data.color = col; l.data.size = size
    d = Vector(target) - Vector(loc); l.rotation_mode = 'QUATERNION'; l.rotation_quaternion = d.to_track_quat('-Z', 'Y'); return l

def camera(loc, target, lens=35):
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.data.lens = lens
    bpy.context.scene.camera = c
    tg = empty("camtarget", target)
    tc = c.constraints.new('TRACK_TO'); tc.target = tg; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
    c.data.dof.use_dof = True; c.data.dof.focus_object = tg; c.data.dof.aperture_fstop = 2.8
    return c, tg

def key(o, frame, **kw):
    for k, v in kw.items():
        setattr(o, k, v); o.keyframe_insert(data_path=k, frame=frame)
