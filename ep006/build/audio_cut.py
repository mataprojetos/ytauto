"""EP006: cortes de pausas sem tocar em palavras (método do EP005 audio_cut4) + atempo.
Tom calmo/hipnótico (pedido do dono): atempo 1.06 e pausas um pouco mais longas entre frases."""
import numpy as np, json, subprocess, re
SR = 48000; TEMPO = 1.06
GAP_SENT, GAP_ELL, GAP_COMMA, GAP_MID = 0.27, 0.34, 0.17, 0.09
PRE, POST = 0.06, 0.09
x = np.frombuffer(subprocess.check_output(["ffmpeg","-v","error","-i","audio/raw/narration_raw.mp3","-ac","1","-ar",str(SR),"-f","f32le","-"]),np.float32).copy()
W = json.load(open("build/words_raw.json"))
# "feels..." do Whisper inclui a pausa até "calm": limitar a palavra a 0,5 s para a pausa poder encolher
for i, w in enumerate(W):
    if w["e"] - w["s"] > 0.8: w["e"] = w["s"] + 0.5
    if w["e"] <= w["s"]: w["e"] = w["s"] + 0.35
FR = int(0.005*SR); nfr = len(x)//FR
edb = 20*np.log10(np.sqrt((x[:nfr*FR].reshape(nfr,FR)**2).mean(1))+1e-9)
xd = np.diff(x, prepend=x[0]); hdb = 20*np.log10(np.sqrt((xd[:nfr*FR].reshape(nfr,FR)**2).mean(1))+1e-9)
SIL = edb.max()-46; HSIL = hdb.max()-46
quiet_fr = (edb < SIL) & (hdb < HSIL)
prot = np.zeros(len(x), bool)
for w in W:
    a = max(0,int((w["s"]-PRE)*SR)); b = min(len(x),int((w["e"]+POST)*SR)); prot[a:b] = True
    f = b//FR
    while f < nfr and not quiet_fr[f] and (f*FR-b) < 0.3*SR: f += 1
    prot[b:min(len(x), f*FR+FR)] = True
    f = a//FR
    while f > 0 and not quiet_fr[f-1] and (a-f*FR) < 0.2*SR: f -= 1
    prot[max(0,f*FR-FR):a] = True
def target(t):
    if re.search(r"(\.\.\.|…)$", t): return GAP_ELL
    if re.search(r"[.?!]$", t): return GAP_SENT
    if re.search(r"[,:;]$", t): return GAP_COMMA
    return GAP_MID
quiet = np.r_[np.repeat(quiet_fr, FR), np.zeros(len(x)-nfr*FR, bool)]
cuts = []
for a, b in zip(W, W[1:]):
    lo, hi = int(a["s"]*SR), int(b["e"]*SR)
    seg = (~prot[lo:hi]) & quiet[lo:hi]
    if not seg.any(): continue
    idxs = np.flatnonzero(seg); br = np.flatnonzero(np.diff(idxs) > 1)
    st = np.r_[idxs[0], idxs[br+1]]; en = np.r_[idxs[br], idxs[-1]]+1
    k = int(np.argmax(en-st)); q0, q1 = lo+st[k], lo+en[k]
    want = (GAP_ELL if a["w"].lower().startswith("feels") else target(a["w"]))*TEMPO
    excess = (q1-q0)/SR + PRE + POST - want
    if excess < 0.03: continue
    rm = int(min(excess, (q1-q0)/SR-0.04)*SR)
    if rm <= 0: continue
    mid = (q0+q1)//2; cuts.append((mid-rm//2, mid-rm//2+rm))
for c0, c1 in cuts:
    assert not prot[c0:c1].any() and quiet[c0:c1].all()
F = int(0.012*SR); out = []; pos = 0
for c0, c1 in sorted(cuts):
    s = x[pos:c0].copy(); s[-F:] *= np.linspace(1,0,F); out.append(s)
    pos = c1; nb = x[pos:pos+F]*np.linspace(0,1,F); out.append(nb); pos += F
out.append(x[pos:])
y = np.concatenate(out)
# cortar o silêncio final depois de "now…" (o vídeo acaba em suspenso e volta ao início)
q = np.flatnonzero(~quiet_fr[:len(y)//FR]); y = y[:min(len(y), (q[-1]+3)*FR)]
# e o silêncio inicial
y = y[max(0,(np.flatnonzero(~quiet_fr)[0]-2)*FR):] if False else y
subprocess.run(["ffmpeg","-v","error","-y","-f","f32le","-ar",str(SR),"-ac","1","-i","-","-af",f"atempo={TEMPO}","audio/narration.wav"],input=y.astype(np.float32).tobytes(),check=True)
print(f"cortes {len(cuts)} · removido {sum(c1-c0 for c0,c1 in cuts)/SR:.2f}s · dur {len(y)/SR/TEMPO:.2f}s")
