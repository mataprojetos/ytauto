#!/usr/bin/env python3
"""Palavras com tempos (faster-whisper small.en). Uso: transcribe.py narration.wav out.json"""
import sys, json, subprocess
import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cpu", compute_type="int8")
pcm = np.frombuffer(subprocess.check_output(["ffmpeg","-v","error","-i",sys.argv[1],"-ac","1","-ar","16000","-f","f32le","-"]), np.float32)
segs, _ = m.transcribe(pcm, word_timestamps=True, language="en",
    initial_prompt="You just stole a rocket. Five stars. Wanted… literally. Carjacking in space means opening a door at 28,000 km per hour.")
out = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]
json.dump(out, open(sys.argv[2], "w"), indent=0)
print(len(out), " ".join(x["w"] for x in out))
