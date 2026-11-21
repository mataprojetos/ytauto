import sys, json
from faster_whisper import WhisperModel
m=WhisperModel("small.en",device="cpu",compute_type="int8")
import numpy as np, subprocess
aud=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',sys.argv[1],'-ac','1','-ar','16000','-f','f32le','-']),np.float32)
segs,_=m.transcribe(aud,word_timestamps=True,language="en",initial_prompt="Every time you blink, you get one dollar. $900 an hour. $14,400. $5,256,000. Black pepper.")
out=[{"w":w.word.strip(),"s":round(w.start,3),"e":round(w.end,3)} for s in segs for w in s.words]
json.dump(out,open(sys.argv[2],"w"),indent=0)
for a,b in zip(out,out[1:]):
    print(f'{a["w"]:>14} {a["s"]:6.2f}-{a["e"]:6.2f}  gap {b["s"]-a["e"]:.2f}')
