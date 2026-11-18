"""Pop-up de subscrição aprovado pelo dono (17/11/2026). Desenha um frame transparente com frame(t).
Entra ~2,5 s logo após a revelação principal (~70-75% do vídeo), nunca no início nem no fim (loop).
Na montagem: sobrepor frame(t - inicio) e um pop leve (vol 0.3) no toque (inicio + 1.0 s).
Demo original: corre este ficheiro com o caminho de saída (usa o EP001 v6 como fundo)."""
import cairo, math, subprocess, sys
W,H,FPS=1080,1920,30
SRC="/home/user/ytauto/ep001/whatifaholic_ep001_moon_v6.mp4"; OUT=sys.argv[1]
T0, DUR, P0 = 38.6, 4.6, 1.0   # início do excerto, duração, quando o botão entra
NAVY=(0.03,0.06,0.13); CYAN=(0.24,0.88,1.0); INK=(1,1,1); GREY=(0.55,0.6,0.7)
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def seg(t,a,b): return ease((t-a)/(b-a))
def rr(c,x,y,w,h,r):
    c.new_sub_path(); c.arc(x+w-r,y+r,r,-math.pi/2,0); c.arc(x+w-r,y+h-r,r,0,math.pi/2)
    c.arc(x+r,y+h-r,r,math.pi/2,math.pi); c.arc(x+r,y+r,r,math.pi,1.5*math.pi); c.close_path()
def bell(c,x,y,s,col,a,rot):
    c.save(); c.translate(x,y); c.rotate(rot); c.scale(s,s); c.set_source_rgba(*col,a)
    c.move_to(-14,8); c.curve_to(-14,-6,-12,-18,0,-18); c.curve_to(12,-18,14,-6,14,8); c.line_to(18,12); c.line_to(-18,12); c.close_path(); c.fill()
    c.arc(0,16,5,0,6.283); c.fill(); c.rectangle(-2,-23,4,6); c.fill(); c.restore()
def frame(t):
    s=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H); c=cairo.Context(s)
    u=t-P0
    if u<0 or u>2.6: return s
    inn=seg(u,0,0.35); out=seg(u,2.2,2.55); a=inn*(1-out)
    tap=seg(u,0.85,1.0)                     # carregar
    done=u>1.0
    w,h=640,104; x=(W-w)/2; y=300-40*(1-inn)-30*out
    sc=0.92+0.08*inn - 0.05*math.sin(math.pi*min(1,max(0,(u-0.85)/0.25)))
    c.save(); c.translate(W/2,y+h/2); c.scale(sc,sc); c.translate(-W/2,-(y+h/2))
    c.set_source_rgba(*NAVY,0.82*a); rr(c,x,y,w,h,h/2); c.fill()
    col = GREY if done else CYAN
    c.set_source_rgba(*col,0.95*a); c.set_line_width(4); rr(c,x,y,w,h,h/2); c.stroke()
    wig = 0.35*math.sin((u-1.0)*28)*math.exp(-(u-1.0)*5) if done else 0
    bell(c,x+64,y+h/2-2,1.25,col if not done else INK,a,wig)
    c.select_font_face("Inter Display",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)
    if not done:
        c.set_font_size(40); txt="SUBSCRIBE"; c.set_source_rgba(*INK,a)
        c.move_to(x+110,y+h/2+4); c.show_text(txt)
        c.set_font_size(30); c.set_source_rgba(*CYAN,a); c.move_to(x+340,y+h/2+3); c.show_text("for more what ifs")
    else:
        c.set_font_size(40); c.set_source_rgba(*INK,a); c.move_to(x+110,y+h/2+4); c.show_text("SUBSCRIBED")
        k=seg(u,1.0,1.25); c.set_source_rgba(*CYAN,a); c.set_line_width(7); c.set_line_cap(cairo.LINE_CAP_ROUND)
        cx,cy=x+400,y+h/2-4; c.move_to(cx,cy); c.line_to(cx+14*min(1,k*2),cy+14*min(1,k*2))
        if k>0.5: c.line_to(cx+14+26*(k-0.5)*2,cy+14-30*(k-0.5)*2)
        c.stroke()
    c.restore()
    # dedo / toque: círculo que desce e faz onda
    if 0.5<u<1.5:
        fx=x+w-120; fy=y+h/2
        pa=seg(u,0.5,0.8)*(1-seg(u,1.2,1.5))
        r=34-8*tap
        c.set_source_rgba(1,1,1,0.55*pa*a); c.arc(fx,fy+60*(1-seg(u,0.5,0.85)),r,0,6.283); c.fill()
        if u>0.95:
            q=(u-0.95)/0.5
            c.set_source_rgba(*CYAN,0.6*(1-q)*a); c.set_line_width(4); c.arc(fx,fy,30+90*q,0,6.283); c.stroke()
    return s
pop=f"{OUT}.pop.wav"
subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","aevalsrc='0.5*sin(2*PI*(260+500*exp(-t*35))*t)*exp(-t*22)':s=48000:d=0.2",pop],check=True)
p=subprocess.Popen(["ffmpeg","-v","error","-y","-ss",str(T0),"-t",str(DUR),"-i",SRC,
  "-f","rawvideo","-pix_fmt","bgra","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",pop,
  "-filter_complex",f"[0:v][1:v]overlay=0:0:format=auto[v];[2:a]adelay={int((P0+1.0)*1000)}|{int((P0+1.0)*1000)},volume=0.3[p];[0:a][p]amix=inputs=2:normalize=0:duration=first[a]",
  "-map","[v]","-map","[a]","-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-movflags","+faststart",OUT],stdin=subprocess.PIPE)
for i in range(int(DUR*FPS)): p.stdin.write(bytes(frame(i/FPS).get_data()))
p.stdin.close(); p.wait(); print("ok")
