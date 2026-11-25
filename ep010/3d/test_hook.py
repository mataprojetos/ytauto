"""Teste do estilo 3D: gancho (rapaz em pânico em cima da Terra, asteroide em chamas a chegar). Uso: python3 test_hook.py [frame|anim]"""
import sys, os, math, bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib3d import *
sc = reset()
space_world(0.6)
stars(600, 70)
earth((0, 0, -9.0), 9.0)
root, head, arms = boy("boy", (0, 0, 0.0), pose="panic", face="panic")
ast = asteroid("ast", (2.8, 9.0, 6.2), 2.4)
fire = fire_trail(ast, 9.0, 2.2, (0.75, 0.2, 0.62))
fire.parent = ast; fire.matrix_parent_inverse = ast.matrix_world.inverted()
sun_light((math.radians(55), math.radians(10), math.radians(35)), 2.2)
area_light((3, 2, 9), 350, (1, 0.5, 0.15), 6, (0, 0, 1.5))     # luz quente do asteroide
area_light((-4, -3, 3), 120, (0.5, 0.65, 1.0), 4, (0, 0, 1.4))  # contraluz fria
cam, tg = camera((0.6, -7.5, 2.2), (0.3, 0, 2.6), 30)
N = 110
key(cam, 1, location=(1.4, -9.5, 1.4)); key(cam, N, location=(0.3, -5.6, 2.0))
key(tg, 1, location=(0.6, 2, 3.4)); key(tg, N, location=(0.2, 0, 2.3))
key(ast, 1, location=(3.6, 12, 8.0)); key(ast, N, location=(2.2, 6.5, 5.2))
ast.rotation_euler = (0, 0, 0); key(ast, 1, rotation_euler=(0, 0, 0)); key(ast, N, rotation_euler=(0.6, 0.3, 0.9))
# tremor de pânico
for f in range(1, N + 1, 2):
    root.rotation_euler = (0, 0, 0.04 * math.sin(f * 1.7)); root.keyframe_insert("rotation_euler", frame=f)
    head.rotation_euler = (0.05 * math.sin(f * 2.3), 0.06 * math.sin(f * 1.3), 0); head.keyframe_insert("rotation_euler", frame=f)
sc.frame_start, sc.frame_end = 1, N
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_test")
os.makedirs(out, exist_ok=True)
if len(sys.argv) > 1 and sys.argv[1] == "anim":
    sc.render.filepath = out + "/f_"; sc.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(animation=True)
else:
    fr = int(sys.argv[1]) if len(sys.argv) > 1 else N
    sc.frame_set(fr); sc.render.filepath = out + f"/still_{fr}.png"; bpy.ops.render.render(write_still=True)
print("ok")
