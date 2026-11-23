"""EP007: corte de pausas por energia (silêncios < -45 dB do pico) para <=0,12 s + atempo 1.10 (regra do canal).
Só mexe em silêncios com mais de 0,12 s (as oclusivas dentro das palavras são mais curtas)."""
import numpy as np, subprocess
SR = 48000; TEMPO = 1.10; KEEP = 0.11; THR = -38
x = np.frombuffer(subprocess.check_output(["ffmpeg","-v","error","-i","audio/raw/narration_raw.mp3","-ac","1","-ar",str(SR),"-f","f32le","-"]),np.float32).copy()
FR = int(0.01*SR); n = len(x)//FR
e = 20*np.log10(np.sqrt((x[:n*FR].reshape(n,FR)**2).mean(1))+1e-9); e -= e.max()
q = e < THR
runs = []; i = 0
while i < n:
    if q[i]:
        j = i
        while j < n and q[j]: j += 1
        runs.append((i, j)); i = j
    else: i += 1
F = int(0.01*SR); out = []; pos = 0; removed = 0
first_voice = np.flatnonzero(~q)[0]; last_voice = np.flatnonzero(~q)[-1]
for a, b in runs:
    if a <= first_voice or b > last_voice: continue
    if (b-a)*FR/SR <= KEEP+0.01: continue
    c0 = a*FR + int(KEEP/2*SR); c1 = b*FR - int(KEEP/2*SR)
    s = x[pos:c0].copy(); s[-F:] *= np.linspace(1,0,F); out.append(s)
    nb = x[c1:c1+F]*np.linspace(0,1,F); out.append(nb); pos = c1+F; removed += c1-c0
out.append(x[pos:(last_voice+4)*FR])
y = np.concatenate(out)[max(0,(first_voice-1)*FR):]
subprocess.run(["ffmpeg","-v","error","-y","-f","f32le","-ar",str(SR),"-ac","1","-i","-","-af",f"atempo={TEMPO}","audio/narration.wav"],input=y.astype(np.float32).tobytes(),check=True)
print(f"removido {removed/SR:.2f}s · dur {len(y)/SR/TEMPO:.2f}s")
