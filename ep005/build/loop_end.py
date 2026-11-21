"""EP005: fim do loop (ideia do dono). Em vez de repetir "Every time you blink, you get one dollar." no fim,
o vídeo acaba em "…because" e o loop recomeça com "Every time you blink…".
Reaproveita o "because" que o Bram já diz ("scratch my head… because that's $900"): 0 créditos.
Corre depois de audio_cut4.py + align (usa build/words.json da narração cortada)."""
import numpy as np, json, subprocess, re

SR = 48000
NARR = "audio/narration.wav"
x = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", NARR, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]), np.float32).copy()
W = json.load(open("build/words.json"))
bare = lambda w: re.sub(r"[^\w]", "", w).lower()
FR = 240; n = len(x) // FR
e = 20 * np.log10(np.sqrt((x[:n * FR].reshape(n, FR) ** 2).mean(1)) + 1e-9)
xd = np.diff(x, prepend=x[0]); h = 20 * np.log10(np.sqrt((xd[:n * FR].reshape(n, FR) ** 2).mean(1)) + 1e-9)
quiet = (e < e.max() - 46) & (h < h.max() - 46)


def sound_end(t):
    f = int(t * SR / FR)
    while f + 12 < len(quiet) and not quiet[f:f + 12].all(): f += 1
    return f * FR / SR


def sound_start(t, back=0.15):
    f = int(t * SR / FR); lim = f - int(back * SR / FR)
    while f > lim and not quiet[f - 1]: f -= 1
    return f * FR / SR


# fim de "One word."
iw = max(i for i, w in enumerate(W) if bare(w["w"]) == "word")
cut = sound_end(W[iw]["e"]) + 0.03
# "because" (1.ª ocorrência) até ao início de "that's"
ib = next(i for i, w in enumerate(W) if bare(w["w"]) == "because")
b0 = sound_start(W[ib]["s"]); b1 = sound_end(W[ib]["s"]) + 0.02   # fim real do som (o Whisper marca "that's" cedo)
clip = x[int(b0 * SR):int(b1 * SR)].copy()
f = int(0.004 * SR); clip[:f] *= np.linspace(0, 1, f)
f = int(0.03 * SR); clip[-f:] *= np.linspace(1, 0, f)
y = np.concatenate([x[:int(cut * SR)], np.zeros(int(0.24 * SR), np.float32), clip, np.zeros(int(0.06 * SR), np.float32)])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", NARR], input=y.tobytes(), check=True)
json.dump({"because_s": cut + 0.24, "because_e": cut + 0.24 + len(clip) / SR}, open("build/loop_meta.json", "w"))
print(f"corte após 'word.' em {cut:.2f}s · because {b1 - b0:.2f}s · dur final {len(y) / SR:.2f}s")
