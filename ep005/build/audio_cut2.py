"""2.º passe: encolhe as pausas entre palavras (Whisper) para 0,12 s; tosse entre 'of' e 'black'; +10%."""
import numpy as np, json, subprocess
SR=48000
x=np.frombuffer(subprocess.check_output(["ffmpeg","-v","error","-i","audio/raw/trim.wav","-f","f32le","-"]),np.float32).copy()
W=json.load(open("build/words_trim.json"))
fr0=int(0.01*SR); PEAK=max(20*np.log10(np.sqrt(np.mean(x[k:k+fr0]**2))+1e-9) for k in range(0,len(x)-fr0,fr0))
cuts=[]  # (a,b) amostras a remover
for a,b in zip(W,W[1:]):
    g=b["s"]-a["e"]
    if g>0.13:
        # só corta a parte realmente silenciosa do intervalo (sibilantes como o 'Sn' começam antes do Whisper)
        lo=int((a["e"]-0.02)*SR); hi=int((b["s"]+0.02)*SR); fr=int(0.005*SR)
        q=[20*np.log10(np.sqrt(np.mean(x[k:k+fr]**2))+1e-9) for k in range(lo,hi,fr)]
        quiet=[v<PEAK-30 for v in q]
        if not any(quiet): continue
        i0=quiet.index(True); i1=len(quiet)-1-quiet[::-1].index(True)
        s0=lo+i0*fr+int(0.05*SR); s1=lo+(i1+1)*fr-int(0.05*SR)
        if s1-s0>int(0.03*SR): cuts.append((s0,s1))
# fronteira of|black: mínimo de energia
iof=[i for i,w in enumerate(W) if w["w"]=="of" and W[i+1]["w"].lower().startswith("black")][0]
c=W[iof]["e"]; lo,hi=int((c-0.15)*SR),int((c+0.12)*SR); win=int(0.015*SR)
e=[np.sum(x[k:k+win]**2) for k in range(lo,hi,win//3)]
split=lo+int(np.argmin(e))*(win//3)+win//2
print("split of|black at",split/SR)
# montar com crossfades curtos
pieces=[]; pos=0; fade=int(0.008*SR)
for a,b in cuts+[(len(x),len(x))]:
    if split>pos and split<a:
        pieces.append(("seg",pos,split)); pieces.append(("cough",)); pos=split
    pieces.append(("seg",pos,a)); pos=b
out=[]
cough=np.fromfile("build/cough.f32",np.float32)
for p in pieces:
    if p[0]=="cough":
        out.append(("cough",len(out))); continue
    s=x[p[1]:p[2]].copy()
    if len(s)>2*fade:
        s[:fade]*=np.linspace(0,1,fade); s[-fade:]*=np.linspace(1,0,fade)
    out.append(s)
# tosse: 0,18 s pausa + tosse + ~0,22 s pausa  (pausa cómica total ~0,4 s + tosse)
res=[]; cough_at=None
for o in out:
    if isinstance(o,tuple):
        res.append(np.zeros(int(0.16*SR),np.float32)); cough_at=sum(len(r) for r in res)/SR
        res.append(np.zeros(len(cough),np.float32))  # tosse entra como SFX na mistura? não: vai na voz
        res[-1]=cough*0.9
        res.append(np.zeros(int(0.24*SR),np.float32))
    else: res.append(o)
y=np.concatenate(res)
y.astype(np.float32).tofile("build/cut2.f32")
subprocess.run(["ffmpeg","-v","error","-y","-f","f32le","-ar",str(SR),"-ac","1","-i","build/cut2.f32",
  "-af","atempo=1.1","audio/narration.wav"],check=True)
json.dump({"cough_at_pre_tempo":cough_at,"cough_len":len(cough)/SR},open("build/cough_meta.json","w"))
print("dur",len(y)/SR/1.1,"cough at",cough_at/1.1)
