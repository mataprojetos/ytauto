"""EP005 v3 dos cortes (pedido do dono: fluidez sim, mas sem comer palavras).
Regra rígida: NENHUM corte pode tocar numa palavra. Cada palavra fica protegida com margem
(Whisper -60 ms / +90 ms), mais a cauda e o ataque reais medidos por energia (limiar baixo: -46 dB do pico).
Só se remove silêncio verdadeiro entre zonas protegidas (respirações longas só no excesso).
Pausa alvo conforme a pontuação (medida depois do atempo). Fades de 12 ms, sempre em silêncio.
No fim: verificação automática de que nenhuma amostra protegida foi removida."""
import numpy as np, json, subprocess, re

SR = 48000; TEMPO = 1.1
GAP_SENT, GAP_COMMA, GAP_MID = 0.24, 0.16, 0.09    # pausa alvo (s) depois do atempo
PRE, POST = 0.06, 0.09                             # margem de proteção à volta de cada palavra (Whisper)
x = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", "audio/raw/narration_raw.mp3", "-ac", "1",
                                           "-ar", str(SR), "-f", "f32le", "-"]), np.float32).copy()
W = json.load(open("build/words_raw.json"))
FR = int(0.005 * SR)
nfr = len(x) // FR
edb = 20 * np.log10(np.sqrt((x[:nfr * FR].reshape(nfr, FR) ** 2).mean(1)) + 1e-9)
PEAK = edb.max(); SIL = PEAK - 46

# 1) zonas protegidas
prot = np.zeros(len(x), bool)
for w in W:
    a = max(0, int((w["s"] - PRE) * SR)); b = min(len(x), int((w["e"] + POST) * SR))
    prot[a:b] = True
    # cauda real: estende enquanto houver som acima do silêncio (até +0,3 s)
    f = b // FR
    while f < nfr and edb[f] > SIL and (f * FR - b) < 0.2 * SR: f += 1
    prot[b:min(len(x), f * FR + FR)] = True
    # ataque real: recua enquanto houver som (até -0,2 s)
    f = a // FR
    while f > 0 and edb[f - 1] > SIL and (a - f * FR) < 0.12 * SR: f -= 1
    prot[max(0, f * FR - FR):a] = True


def target(w):
    t = w["w"]
    if re.search(r"[.?!]$|\.\.\.$|…$", t): return GAP_SENT
    if re.search(r"[,:;]$", t): return GAP_COMMA
    return GAP_MID


# 2) cortes: em cada intervalo entre palavras, a parte NÃO protegida é silêncio removível
iof = next(i for i, w in enumerate(W) if w["w"].lower().startswith("of") and W[i + 1]["w"].lower().startswith("black"))
cuts = []; split = None
for i, (a, b) in enumerate(zip(W, W[1:])):
    lo, hi = int(a["s"] * SR), int(b["e"] * SR)
    if i == iof:   # ponto de inserção da tosse: energia mínima entre "of" e "black" (não remove nada)
        c0, c1 = int((a["e"] - 0.1) * SR), int((b["s"] + 0.05) * SR)
        e = [np.sum(x[k:k + FR * 3] ** 2) for k in range(c0, c1, FR)]
        split = c0 + int(np.argmin(e)) * FR + FR
        continue
    seg = ~prot[lo:hi]
    if not seg.any(): continue
    idxs = np.flatnonzero(seg)
    # maior bloco contínuo não protegido
    br = np.flatnonzero(np.diff(idxs) > 1)
    starts = np.r_[idxs[0], idxs[br + 1]]; ends = np.r_[idxs[br], idxs[-1]] + 1
    k = int(np.argmax(ends - starts)); q0, q1 = lo + starts[k], lo + ends[k]
    # pausa atual = silêncio livre + parte quieta das margens (≈ PRE+POST); cortar só o excesso
    have = (q1 - q0) / SR + PRE + POST
    want = target(a) * TEMPO
    excess = have - want
    if excess < 0.03: continue
    rm = int(min(excess, (q1 - q0) / SR - 0.04) * SR)
    if rm <= 0: continue
    mid = (q0 + q1) // 2
    cuts.append((mid - rm // 2, mid - rm // 2 + rm))

# 3) verificação: nenhum corte toca em zona protegida
for c0, c1 in cuts:
    assert not prot[c0:c1].any(), f"corte em zona protegida: {c0/SR:.2f}-{c1/SR:.2f}"

# 4) montar (fades de 20 ms só nas junções, que estão em silêncio) + tosse com pausa cómica
cough = np.fromfile("build/cough.f32", np.float32)
F = int(0.012 * SR)
out = []; pos = 0; cough_at = None
events = sorted([(c0, c1, "cut") for c0, c1 in cuts] + [(split, split, "cough")])
for c0, c1, tag in events:
    s = x[pos:c0].copy()
    if tag == "cut":
        if len(s) > F: s[-F:] *= np.linspace(1, 0, F)
        out.append(s); pos = c1
        nxt_fade = True
    else:
        out.append(s); pos = c0
        out.append(np.zeros(int(0.2 * TEMPO * SR), np.float32))
        cough_at = sum(len(o) for o in out) / SR
        out.append(cough)
        out.append(np.zeros(int(0.25 * TEMPO * SR), np.float32))
        continue
    # fade-in no início do bloco seguinte (também silêncio)
    nb = x[pos:pos + F].copy() * np.linspace(0, 1, F); out.append(nb); pos += F
out.append(x[pos:])
y = np.concatenate(out)
y.astype(np.float32).tofile("build/cut4.f32")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "build/cut4.f32",
                "-af", f"atempo={TEMPO}", "audio/narration.wav"], check=True)
json.dump({"cough_at_pre_tempo": cough_at, "cough_len": len(cough) / SR}, open("build/cough_meta.json", "w"))
removed = sum(c1 - c0 for c0, c1 in cuts) / SR
print(f"cortes {len(cuts)} · removido {removed:.2f} s · protegido intacto: OK · dur final {len(y)/SR/TEMPO:.2f} s · tosse {cough_at/TEMPO:.2f} s")
