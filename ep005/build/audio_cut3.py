"""EP005 v2 dos cortes (pedido do dono: frases a colar umas às outras).
Um só passe a partir da voz original:
  - pausa alvo conforme a pontuação (fim de frase > vírgula > meio de frase), medida DEPOIS do atempo;
  - limites reais da fala por energia (o Whisper corta sibilantes e caudas);
  - mantém a cauda natural da palavra anterior e o ataque da seguinte, corta só silêncio,
    com fades suaves (40–60 ms) em vez de 8 ms;
  - tosse com pausa cómica entre "of…" e "black pepper"; depois voz +10% (atempo, sem mudar o tom)."""
import numpy as np, json, subprocess, re

SR = 48000; TEMPO = 1.1
GAP_SENT, GAP_COMMA, GAP_MID = 0.23, 0.15, 0.08   # segundos, já com o atempo
x = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", "audio/raw/narration_raw.mp3", "-ac", "1",
                                           "-ar", str(SR), "-f", "f32le", "-"]), np.float32).copy()
W = json.load(open("build/words_raw.json"))
FR = int(0.005 * SR)
def db(a, b):
    seg = x[max(0, a):max(a + 1, b)]
    return 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
PEAK = max(db(k, k + 2 * FR) for k in range(0, len(x) - 2 * FR, 2 * FR))
THR = PEAK - 31


def speech_bounds(a, b):
    """fim real da palavra a e início real da palavra b (por energia) dentro do intervalo"""
    lo = int((a["e"] - 0.04) * SR); hi = int((b["s"] + 0.06) * SR)
    fr = list(range(lo, hi, FR)); v = [db(k, k + FR) > THR for k in fr]
    if not any(not q for q in v): return None
    i0 = next(i for i, q in enumerate(v) if not q)                 # 1.º frame quieto
    i1 = len(v) - 1 - next(i for i, q in enumerate(v[::-1]) if not q)  # último frame quieto
    if i1 <= i0: return None
    return fr[i0], fr[i1] + FR


def target(w):
    t = w["w"]
    if re.search(r"[.?!]$|\.\.\.$|…$", t): return GAP_SENT
    if re.search(r"[,:;]$", t): return GAP_COMMA
    return GAP_MID


iof = next(i for i, w in enumerate(W) if w["w"].lower().startswith("of") and W[i + 1]["w"].lower().startswith("black"))
pieces = []; pos = 0; cough_after_piece = None
for i, (a, b) in enumerate(zip(W, W[1:])):
    if i == iof:  # fronteira of|black: ponto de energia mínima
        c = a["e"]; lo, hi = int((c - 0.12) * SR), int((b["s"] + 0.08) * SR); w_ = int(0.015 * SR)
        e = [np.sum(x[k:k + w_] ** 2) for k in range(lo, hi, w_ // 3)]
        sp = lo + int(np.argmin(e)) * (w_ // 3) + w_ // 2
        pieces.append((pos, sp, "cough")); pos = sp; continue
    bd = speech_bounds(a, b)
    if not bd: continue
    q0, q1 = bd
    have = (q1 - q0) / SR; want = target(a) * TEMPO
    if have <= want + 0.02: continue
    keep_a = int(want * 0.6 * SR); keep_b = int(want * 0.4 * SR)
    pieces.append((pos, q0 + keep_a, None)); pos = q1 - keep_b
pieces.append((pos, len(x), None))

cough = np.fromfile("build/cough.f32", np.float32)
out = []; cough_at = None
FO, FI = int(0.06 * SR), int(0.04 * SR)
for k, (a, b, tag) in enumerate(pieces):
    s = x[a:b].copy()
    if k > 0 and len(s) > FI: s[:FI] *= np.sin(np.linspace(0, np.pi / 2, FI)) ** 2
    if k < len(pieces) - 1 and len(s) > FO and tag != "cough": s[-FO:] *= np.cos(np.linspace(0, np.pi / 2, FO)) ** 2
    if tag == "cough":
        f = int(0.02 * SR); s[-f:] *= np.linspace(1, 0, f)
    out.append(s)
    if tag == "cough":   # pausa cómica: ~0,2 s + tosse + ~0,25 s (antes do atempo)
        out.append(np.zeros(int(0.2 * TEMPO * SR), np.float32))
        cough_at = sum(len(o) for o in out) / SR
        out.append(cough * 0.9)
        out.append(np.zeros(int(0.25 * TEMPO * SR), np.float32))
y = np.concatenate(out)
y.astype(np.float32).tofile("build/cut3.f32")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "build/cut3.f32",
                "-af", f"atempo={TEMPO}", "audio/narration.wav"], check=True)
json.dump({"cough_at_pre_tempo": cough_at, "cough_len": len(cough) / SR}, open("build/cough_meta.json", "w"))
print("dur final", round(len(y) / SR / TEMPO, 2), "tosse em", round(cough_at / TEMPO, 2), "cortes", len(pieces) - 1)
