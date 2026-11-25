import subprocess
from PIL import Image, ImageDraw, ImageFont
V='whatifaholic_ep010_asteroid.mp4'; FPS=30
N=int(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v','-show_entries','stream=nb_read_frames','-of','csv=p=0',V]))
ts=[0,1.5,4.4,6.0,7.3,11.5,14.4,16.9,17.7,20.5,23.4,24.9,27.5,29.6,33.0,34.5,39.0,42.9,43.6,45.8,47.6,48.6,53.5,55.9,58.8,63.0,64.0,65.2,66.3,(N-1)/FPS]
f=ImageFont.truetype('/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf',20); ims=[]
for t in ts:
    fn=int(round(t*FPS)); p=f'build/cs_{fn:04d}.png'
    subprocess.run(['ffmpeg','-v','error','-y','-i',V,'-vf',f'select=eq(n\\,{fn})','-vframes','1',p],check=True)
    im=Image.open(p).resize((270,480)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,270,28],fill=(0,0,0)); d.text((6,3),f'{t:.2f}s'+(' FRAME 0' if fn==0 else (' ÚLTIMO' if fn==N-1 else (' POP-UP' if t in (65.2,66.3) else (' GENIUS' if t in (4.4,14.4,24.9) else '')))),fill=(255,200,80),font=f)
    ims.append(im)
sheet=Image.new('RGB',(8*270,4*480))
for i,im in enumerate(ims): sheet.paste(im,((i%8)*270,(i//8)*480))
sheet.save('folha_controlo_ep010.jpg',quality=82); print(N)
