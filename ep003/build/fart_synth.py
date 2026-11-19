"""'pffrrt' cómico sintetizado: zumbido de lábios (impulsos com batimento irregular), tom a descer e guincho final."""
import numpy as np, wave, sys
sr = 48000; D = 0.85; rng = np.random.default_rng(5)
t = np.arange(int(sr * D)) / sr
f0 = 150 - 65 * np.clip(t / 0.62, 0, 1) + 9 * np.sin(2 * np.pi * 7 * t)
f0 += np.interp(t, np.linspace(0, D, 40), rng.normal(0, 6, 40))
f0 = np.where(t > 0.66, 85 + 160 * ((t - 0.66) / 0.19) ** 1.5, f0)  # guincho no fim
ph = 2 * np.pi * np.cumsum(f0) / sr
buzz = sum(np.sin(k * ph) / k ** 0.9 for k in range(1, 14))  # rico em harmónicos
flap_f = 27 + 6 * np.sin(2 * np.pi * 3 * t)
flap = 0.35 + 0.65 * np.abs(np.sin(np.pi * np.cumsum(flap_f) / sr)) ** 0.6
noise = rng.normal(0, 1, t.size); noise = np.convolve(noise, np.ones(12) / 12, "same")
sig = buzz * flap + 0.9 * noise * flap
env = np.minimum(1, t / 0.012) * np.where(t > 0.66, 0.55 * (1 - (t - 0.66) / 0.19) ** 0.7, 1.0)
sig *= env
sig /= np.abs(sig).max()
w = wave.open(sys.argv[1], "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
w.writeframes((sig * 0.95 * 32767).astype(np.int16).tobytes()); w.close()
