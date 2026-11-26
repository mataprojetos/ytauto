"""EP010: troca as 4 frases (uso: python3 build/splice_smart.py <clip.mp3> "<texto da frase>")
 "And you, being a genius…" por "And you, who are very smart…" (pedido do dono, 25/11/2026).
Gera-se só a frase nova (voz Bram), com o mesmo tratamento (silêncios ≤0,10 s, atempo 1,10, volume igualado),
e encaixa-se nos 4 sítios; words.json é refeito com os tempos deslocados. Original guardado em audio/narration_v_genius.wav."""
import json, subprocess, sys, numpy as np
SR = 48000
def load(p, filt=None):
    cmd = ["ffmpeg", "-v", "error", "-i", p] + (["-af", filt] if filt else []) + ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.check_output(cmd), np.float32).copy()
nar = load("audio/narration_v_genius.wav")
CLIP = sys.argv[1] if len(sys.argv) > 1 else "audio/raw/smart_raw.mp3"
clip = load(CLIP, "silenceremove=start_periods=1:start_threshold=-40dB:stop_periods=-1:stop_threshold=-40dB:stop_duration=0.18,atempo=1.10")   # pausas irónicas até 0,18 s
clip = clip[int(0.005 * SR):]
words = json.load(open("build/words_genius.json"))   # palavras da narração original ("being a genius…")
G = [15, 49, 88, 126]; Aw = [20, 54, 93, 131]
# volume: igualar o RMS da frase original "And you, being a genius…"
s0, e0 = words[15]["s"], words[19]["e"]
r_orig = np.sqrt((nar[int(s0 * SR):int(e0 * SR)] ** 2).mean()); r_clip = np.sqrt((clip ** 2).mean())
clip *= r_orig / r_clip
fade = int(0.008 * SR); clip[:fade] *= np.linspace(0, 1, fade); clip[-fade:] *= np.linspace(1, 0, fade)
# tempos das palavras da frase nova (whisper)
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cpu", compute_type="int8")
a16 = np.interp(np.arange(0, len(clip), SR / 16000), np.arange(len(clip)), clip).astype(np.float32)
segs, _ = m.transcribe(a16, word_timestamps=True, language="en")
cw = [(w.start, w.end) for s in segs for w in s.words]
NEW = (sys.argv[2] if len(sys.argv) > 2 else "And you, who are very smart…").split()
print("palavras na frase nova:", len(cw), [round(x[0], 2) for x in cw])
assert len(cw) == len(NEW), cw
out, new_words, pos, shift = [], [], 0.0, 0.0
cur = 0   # índice na narração original (amostras)
wi = 0
gap = np.zeros(int(0.06 * SR), np.float32)
for g, a in zip(G, Aw):
    a_t = words[g]["s"] - 0.03; b_t = words[a]["s"] - 0.08
    seg = nar[cur:int(a_t * SR)]; out.append(seg)
    while wi < g:
        w = dict(words[wi]); w["s"] += shift; w["e"] += shift; new_words.append(w); wi += 1
    base = sum(len(x) for x in out) / SR
    for (s, e), txt in zip(cw, NEW):
        new_words.append({"w": txt, "s": round(base + s, 3), "e": round(base + e, 3)})
    out.append(clip); out.append(gap)
    ins = (len(clip) + len(gap)) / SR
    shift += ins - (b_t - a_t)
    cur = int(b_t * SR); wi = a
out.append(nar[cur:])
while wi < len(words):
    w = dict(words[wi]); w["s"] += shift; w["e"] += shift; new_words.append(w); wi += 1
y = np.concatenate(out)
for w in new_words: w["s"], w["e"] = round(w["s"], 3), round(w["e"], 3)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "audio/narration.wav"], input=y.astype(np.float32).tobytes(), check=True)
json.dump(new_words, open("build/words.json", "w"), indent=0)
print("nova duração", round(len(y) / SR, 2), "desvio total", round(shift, 2), "palavras", len(new_words))
