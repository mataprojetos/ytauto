import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel
m=WhisperModel("small.en",device="cpu",compute_type="int8")
aud=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',sys.argv[1],'-ac','1','-ar','16000','-f','f32le','-']),np.float32)
segs,_=m.transcribe(aud,word_timestamps=True,language="en",condition_on_previous_text=False,vad_filter=False)
out=[{"w":w.word.strip(),"s":round(w.start,3),"e":round(w.end,3)} for s in segs for w in s.words]
json.dump(out,open(sys.argv[2],"w"),indent=0)
print(len(out)); print(" ".join(f'{w["w"]}[{w["s"]:.2f}-{w["e"]:.2f}]' for w in out))
