"""EP005: corta pausas (>0,12 s -> 0,12 s) por energia; depois voz +10% (atempo)."""
import numpy as np, subprocess, sys, json
SR=48000
raw=subprocess.check_output(["ffmpeg","-v","error","-i","audio/raw/narration_raw.mp3","-ac","1","-ar",str(SR),"-f","f32le","-"])
x=np.frombuffer(raw,np.float32).copy()
win=int(0.01*SR); n=len(x)//win
rms=np.sqrt((x[:n*win].reshape(n,win)**2).mean(1)+1e-12)
db=20*np.log10(rms); thr=db.max()-42
sil=db<thr
keep=np.ones(n,bool); i=0; MAXG=12  # 0.12 s
runs=[]
while i<n:
    if sil[i]:
        j=i
        while j<n and sil[j]: j+=1
        runs.append((i,j))
        if j-i>MAXG:
            a=i+MAXG//2; b=j-MAXG//2
            if i==0: a=0; b=j-3
            if j==n: a=i+3; b=n
            keep[a:b]=False
        i=j
    else: i+=1
mask=np.repeat(keep,win); mask=np.concatenate([mask,np.ones(len(x)-len(mask),bool)])
y=x[mask]
np.save("build/trim_map.npy",np.cumsum(keep))  # para mapear tempos se preciso
y.astype(np.float32).tofile("build/trim.f32")
subprocess.run(["ffmpeg","-v","error","-y","-f","f32le","-ar",str(SR),"-ac","1","-i","build/trim.f32","audio/raw/trim.wav"],check=True)
print(len(x)/SR, len(y)/SR)
