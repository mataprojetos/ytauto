"""Sons sintetizados reutilizáveis do Whatifaholic (só código, 0 créditos).
- scratch_head(): som curto da frase de marca "That one made me scratch my head." (SEMPRE o mesmo:
  três arranhadelas rápidas + um 'tok' grave). Guardado em lib/sfx/scratch_head.wav.
- cough(): tosse curta (piada da pimenta, EP005).
- kaching(): caixa registadora curta (contadores de dinheiro).
Correr `python3 lib/brand_sfx.py` regenera os .wav em lib/sfx/."""
import numpy as np, os, subprocess
SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))


def _bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def scratch_head(seed=5):
    rng = np.random.default_rng(seed)
    out = np.zeros(int(0.62 * SR))
    for k, t0 in enumerate((0.0, 0.11, 0.22)):
        n = int(0.085 * SR); t = np.arange(n) / SR
        nz = _bp(rng.standard_normal(n), 2600, 7500)
        env = np.minimum(1, t / 0.006) * np.exp(-t * 28) * (1 + 0.6 * np.sin(2 * np.pi * 70 * t))
        i = int(t0 * SR); out[i:i + n] += nz * env * (0.55 - 0.08 * k)
    n = int(0.25 * SR); t = np.arange(n) / SR   # 'tok' (madeira) no fim
    tok = (np.sin(2 * np.pi * 620 * t) + 0.5 * np.sin(2 * np.pi * 1240 * t)) * np.exp(-t * 32)
    i = int(0.36 * SR); out[i:i + n] += 0.45 * tok
    return (out / np.abs(out).max() * 0.8).astype(np.float32)


def cough(seed=11):
    rng = np.random.default_rng(seed)
    out = np.zeros(int(0.42 * SR))
    for t0, amp, dur in ((0.0, 1.0, 0.16), (0.2, 0.6, 0.13)):
        n = int(dur * SR); t = np.arange(n) / SR
        nz = _bp(rng.standard_normal(n), 300, 2600) + 0.6 * _bp(rng.standard_normal(n), 2600, 5000)
        f0 = 170 - 60 * t / dur
        voice = np.sign(np.sin(2 * np.pi * np.cumsum(f0) / SR)) * 0.25
        voice = _bp(voice, 120, 1800)
        env = np.minimum(1, t / 0.004) * np.exp(-t * 18)
        i = int(t0 * SR); out[i:i + n] += amp * env * (nz + voice)
    return (out / np.abs(out).max() * 0.85).astype(np.float32)


def kaching():
    n = int(0.55 * SR); t = np.arange(n) / SR
    clk = _bp(np.random.default_rng(3).standard_normal(n), 2000, 8000) * np.exp(-t * 120) * 0.6
    bell = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((2093, 0.5), (2637, 0.35), (3136, 0.3), (4186, 0.15)))
    bell = bell * np.exp(-np.maximum(0, t - 0.05) * 7) * (t > 0.05)
    out = clk + bell
    return (out / np.abs(out).max() * 0.8).astype(np.float32)


def save(name, x):
    p = f"{HERE}/sfx/{name}.wav"; os.makedirs(os.path.dirname(p), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", p],
                   input=x.tobytes(), check=True)
    return p


if __name__ == "__main__":
    for n, f in (("scratch_head", scratch_head), ("cough", cough), ("kaching", kaching)):
        print(save(n, f()))
