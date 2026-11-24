import subprocess
from PIL import Image, ImageDraw, ImageFont
V='whatifaholic_ep008_hole.mp4'; FPS=30
N=int(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v','-show_entries','stream=nb_read_frames','-of','csv=p=0',V]))
ts=[0,1.5,4.0,6.0,7.0,9.5,12.5,15.0,17.3,19.8,22.3,23.6,24.5,27.0,30.4,32.5,34.0,36.0,37.6,38.6,(N-1)/FPS]
f=ImageFont.truetype('/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf',20); ims=[]
for t in ts:
    fn=int(round(t*FPS)); p=f'build/cs_{fn:04d}.png'
    subprocess.run(['ffmpeg','-v','error','-y','-i',V,'-vf',f'select=eq(n\\,{fn})','-vframes','1',p],check=True)
    im=Image.open(p).resize((270,480)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,270,28],fill=(0,0,0)); d.text((6,3),f'{t:.2f}s'+(' FRAME 0' if fn==0 else (' ÚLTIMO' if fn==N-1 else (' POP-UP' if t in (23.6,24.5) else ''))),fill=(255,200,80),font=f)
    ims.append(im)
sheet=Image.new('RGB',(7*270,3*480))
for i,im in enumerate(ims): sheet.paste(im,((i%7)*270,(i//7)*480))
sheet.save('folha_controlo_ep008.jpg',quality=82); print(N)
