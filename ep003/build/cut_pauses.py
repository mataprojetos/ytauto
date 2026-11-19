#!/usr/bin/env python3
"""Corta pausas da narração para <=0,12 s e aplica +10% (atempo). Uso: cut_pauses.py in.mp3 out.wav"""
import sys, subprocess, numpy as np
src, out = sys.argv[1], sys.argv[2]
SR = 48000; MAXP = 0.12
raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"])
x = np.frombuffer(raw, np.float32).copy()
win = int(0.01 * SR); n = len(x) // win
rms = np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1) + 1e-12)
db = 20 * np.log10(rms); thr = -40.0
loud = db > thr
keep = np.ones(n, bool); i = 0; maxw = int(MAXP / 0.01)
while i < n:
    if not loud[i]:
        j = i
        while j < n and not loud[j]: j += 1
        if j - i > maxw:
            lead = 0 if i == 0 else maxw // 2
            tail = 0 if j == n else maxw - maxw // 2
            if i == 0: tail = 2
            keep[i + lead:j - tail] = False
        i = j
    else: i += 1
segs = []; i = 0
while i < n:
    if keep[i]:
        j = i
        while j < n and keep[j]: j += 1
        segs.append(x[i * win:j * win]); i = j
    else: i += 1
fade = int(0.004 * SR); outs = []
for s in segs:
    s = s.copy()
    if len(s) > 2 * fade:
        s[:fade] *= np.linspace(0, 1, fade); s[-fade:] *= np.linspace(1, 0, fade)
    outs.append(s)
y = np.concatenate(outs)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                "-af", "atempo=1.10", "-c:a", "pcm_s16le", out], input=y.tobytes(), check=True)
print(f"{len(x)/SR:.2f}s -> {len(y)/SR:.2f}s (antes do atempo), thr {thr:.1f} dB")
