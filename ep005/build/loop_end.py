"""EP005: fim novo (ideia do dono): "Now tell me: blink, or sneeze? Because…" curto e direto,
e o vídeo acaba no "because", que liga ao "Every time you blink…" do início (loop).
Substitui "Blink money or sneeze money? One word." e a repetição final.
A linha nova (voz Bram, audio/raw/ending_raw.mp3) tem as pausas comprimidas SÓ em silêncio absoluto.
Corre depois de audio_cut4.py + align (usa build/words.json da narração cortada)."""
import numpy as np, json, subprocess, re

SR = 48000; TEMPO = 1.1
NARR = "audio/narration.wav"


def load(p):
    return np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]), np.float32).copy()


def quiet_mask(x, fr=240, rel=46):
    n = len(x) // fr
    e = 20 * np.log10(np.sqrt((x[:n * fr].reshape(n, fr) ** 2).mean(1)) + 1e-9)
    xd = np.diff(x, prepend=x[0]); h = 20 * np.log10(np.sqrt((xd[:n * fr].reshape(n, fr) ** 2).mean(1)) + 1e-9)
    return (e < e.max() - rel) & (h < h.max() - rel)


# --- 1) linha nova: separar em blocos de som e encurtar as pausas entre eles ---
e_raw = load("audio/raw/ending_raw.mp3")
q = quiet_mask(e_raw); FR = 240
runs, f = [], 0                     # blocos de som [a, b) em amostras
while f < len(q):
    if not q[f]:
        g = f
        while g < len(q) and not (q[g:g + 16].all()):   # bloco acaba com ≥80 ms de silêncio
            g += 1
        runs.append((f * FR, g * FR)); f = g
    else:
        f += 1
assert len(runs) == 4, f"esperava 4 blocos de som, encontrei {len(runs)}: {[(a/SR, b/SR) for a, b in runs]}"
GAPS = [0.17, 0.11, 0.24]           # pausas alvo (s) depois do atempo: "me:" | "blink, or" | "sneeze?"
PAD = int(0.012 * SR)
parts, marks = [], []
for k, (a, b) in enumerate(runs):
    a = max(0, a - PAD); b = min(len(e_raw), b + PAD)
    marks.append(sum(len(p) for p in parts) / SR)
    parts.append(e_raw[a:b].copy())
    if k < len(GAPS): parts.append(np.zeros(int(GAPS[k] * TEMPO * SR), np.float32))
marks.append(sum(len(p) for p in parts) / SR)     # fim do "because"
ending = np.concatenate(parts)
end_t = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", f"atempo={TEMPO}",
                        "-f", "f32le", "-"], input=ending.tobytes(), capture_output=True, check=True).stdout
ending_t = np.frombuffer(end_t, np.float32)
marks = [m / TEMPO for m in marks]

# --- 2) narração: cortar depois do número final e colar a linha nova ---
x = load(NARR)
qn = quiet_mask(x)
W = json.load(open("build/words.json"))
bare = lambda w: re.sub(r"[^\w]", "", w).lower()
ib = next(i for i, w in enumerate(W) if bare(w["w"]) in ("000", "5256000") and i > 50)
f = int(W[ib]["e"] * SR / FR)
while f + 12 < len(qn) and not qn[f:f + 12].all(): f += 1
cut = f * FR / SR + 0.03
y = np.concatenate([x[:int(cut * SR)], np.zeros(int(0.26 * SR), np.float32), ending_t, np.zeros(int(0.05 * SR), np.float32)])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", NARR], input=y.tobytes(), check=True)
t0 = cut + 0.26
M = {k: t0 + m for k, m in zip(["now_s", "blink_s", "sneeze_s", "because_s", "because_e"], marks)}
json.dump(M, open("build/loop_meta.json", "w"), indent=1)
print(f"corte após o número em {cut:.2f}s · linha nova {len(ending_t)/SR:.2f}s · dur final {len(y)/SR:.2f}s ·", {k: round(v, 2) for k, v in M.items()})
