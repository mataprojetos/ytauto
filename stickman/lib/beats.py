"""Análise da música: BPM, batidas e o drop principal (librosa).

    python3 stickman/lib/beats.py musica.mp3            # mostra BPM, drop e primeiras batidas

No vídeo: `sync = BeatSync.from_audio(path, drop_at=17.0)` alinha a música para o drop cair
aos 17,0 s do vídeo; `sync.pulse(t)` dá 0..1 (pico em cada batida) para a pulsação suave.
"""
import json
import math
import sys

import numpy as np


def analyze(path):
    import librosa
    y, sr = librosa.load(path, sr=22050, mono=True)
    hop = 512
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop, units="frames")
    beats = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)
    bpm = float(np.atleast_1d(tempo)[0])

    # energia dos graves (kick/sub) e total, por janela
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    low = S[freqs < 150].sum(axis=0)
    tot = S.sum(axis=0)
    fps = sr / hop
    w = int(4 * fps)  # 4 s antes vs 4 s depois

    def smooth(a):
        k = np.ones(int(0.25 * fps)) / int(0.25 * fps)
        return np.convolve(a, k, mode="same")

    low, tot = smooth(low), smooth(tot)
    score = np.zeros_like(low)
    for i in range(w, len(low) - w):
        before = low[i - w:i].mean() + 0.5 * tot[i - w:i].mean() + 1e-6
        after = low[i:i + w].mean() + 0.5 * tot[i:i + w].mean()
        score[i] = after / before * math.sqrt(after)  # salto grande E parte forte a seguir
    i = int(np.argmax(score))
    drop = i / fps
    if len(beats):
        drop = float(beats[np.argmin(np.abs(beats - drop))])  # encaixa na batida
    return dict(bpm=round(bpm, 2), drop=round(drop, 3), beats=[round(float(b), 3) for b in beats],
                duration=round(len(y) / sr, 2))


class BeatSync:
    """Batidas no tempo do VÍDEO. offset = segundo da música que corresponde a t=0 do vídeo."""

    def __init__(self, beats_video, bpm, drop_video):
        self.beats = np.array(sorted(beats_video))
        self.bpm = bpm
        self.drop = drop_video

    @classmethod
    def from_audio(cls, path, drop_at=17.0):
        a = analyze(path)
        offset = a["drop"] - drop_at
        bv = [b - offset for b in a["beats"]]
        s = cls(bv, a["bpm"], drop_at)
        s.offset, s.info = offset, a
        return s

    @classmethod
    def grid(cls, bpm, drop_at=17.0, duration=31.0):
        """Sem música: grelha regular de batidas alinhada para cair uma batida no drop."""
        period = 60.0 / bpm
        n0 = -int(drop_at / period) - 1
        bv = [drop_at + k * period for k in range(n0, int((duration - drop_at) / period) + 2)]
        s = cls(bv, bpm, drop_at)
        s.offset, s.info = None, dict(bpm=bpm)
        return s

    def pulse(self, t, decay=0.16):
        """1 no instante da batida, a decair exponencialmente até à seguinte."""
        idx = np.searchsorted(self.beats, t, side="right") - 1
        if idx < 0:
            return 0.0
        return math.exp(-(t - self.beats[idx]) / decay)

    def beat_index(self, t):
        return int(np.searchsorted(self.beats, t, side="right") - 1)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        a = analyze(p)
        print(p)
        print(json.dumps(dict(bpm=a["bpm"], drop=a["drop"], duration=a["duration"],
                              primeiras_batidas=a["beats"][:8]), ensure_ascii=False))
