"""Mapas de profundidade (Depth Anything V2 Small, CPU) para animar as ilustrações em camadas (parallax 2.5D).
Uso: python3 build/depth.py anim/city.png ...  → anim/<nome>_depth.png (0 = longe, 255 = perto)"""
import sys, numpy as np, torch
from PIL import Image
from transformers import pipeline
pipe = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device="cpu")
for p in sys.argv[1:]:
    im = Image.open(p).convert("RGB")
    d = np.array(pipe(im.resize((768, int(768 * im.height / im.width))))["predicted_depth"].squeeze(), dtype=np.float32) if False else None
    out = pipe(im.resize((768, int(768 * im.height / im.width))))
    d = np.array(out["depth"], dtype=np.float32)
    d = (d - d.min()) / (d.max() - d.min() + 1e-6)
    Image.fromarray((d * 255).astype(np.uint8)).resize(im.size, Image.BILINEAR).save(p.replace(".png", "_depth.png"))
    print(p, "ok")
