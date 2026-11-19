import subprocess,sys
EP=sys.argv[1]; OUT=sys.argv[2]; G=sys.argv[3] if len(sys.argv)>3 else "0"
I="/home/user/inbox/clips/2026-11-19/"+EP+"/"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
bell=lambda f=1046.5:f"aevalsrc='(0.22*sin(2*PI*{f}*t)+0.06*sin(2*PI*{2*f}*t))*exp(-5*t)':s=48000:d=0.7,afade=t=in:d=0.01"
tap="aevalsrc='0.35*sin(2*PI*180*t)*exp(-28*t)':s=48000:d=0.25,lowpass=f=1200"
boop="aevalsrc='0.25*sin(2*PI*(600*t+500*t*t))*exp(-9*t)':s=48000:d=0.35"
pluck=lambda f:f"aevalsrc='0.22*sin(2*PI*{f}*t)*exp(-7*t)':s=48000:d=0.6"
if EP=="20261119-01":
    SEGS=[(0,4.0),(0,4.0),(0,4.0)]; DUR=13.2
    caps=[(0,2,"Who is hiding?"),(2,4,"Look! Long ears!"),(4,5.5,"Peek, peek!"),(5.5,8,"A bunny!|A bunny!"),(8,10,"Hello, bunny!"),(10,13.2,"Your turn!|Say bunny!")]
    sfx=[(boop,2.2),(tap,5.0),(tap,5.5),(tap,6.0),(bell(),8.1),(pluck(784),10.1)]
else:
    SEGS=[(0,2.45),(0,4.0),(0,4.0)]; DUR=11.65
    caps=[(0,2.45,"A flower for me?"),(2.45,4.2,"For you, Croco!"),(4.2,6.45,"Thank you, Pebble!"),(6.45,8.45,"You're welcome!"),(8.45,11.65,"Your turn!|Say thank you!")]
    sfx=[(pluck(659),2.6),(bell(),4.3),(pluck(523),6.6),(pluck(659),6.75),(pluck(784),6.9),(bell(),8.6)]
def esc(s): return s.replace("'", "’").replace(":", "\\:").replace(",", "\\,")
N="scale=1080:1920:flags=lanczos,setsar=1,fps=30"
fc=[]
for k,(a,b) in enumerate(SEGS):
    pad=",tpad=stop_mode=clone:stop_duration=1.3" if k==2 else ""
    fc.append(f"[{k}:v]trim={a}:{b},setpts=PTS-STARTPTS{pad},{N}[v{k}]")
fc.append(f"[v0][v1][v2]concat=n=3:v=1:a=0,trim=0:{DUR},setpts=PTS-STARTPTS[vc]")
dt=[]
for a,b,t in caps:
    ls=t.split("|")
    for k,l in enumerate(ls):
        y=f"h*0.72+{(k-(len(ls)-1)/2)*120:.0f}"
        dt.append(f"drawtext=fontfile={FONT}:text='{esc(l)}':fontcolor=white:fontsize={min(110,int(940/(len(l)*0.62)))}:borderw=9:bordercolor=0x222222:x=(w-text_w)/2:y={y}:enable='between(t,{a},{b-0.001})'")
fc.append("[vc]"+",".join(dt)+"[vout]")
chime="aevalsrc='0.5*sin(2*PI*523.25*t)*lt(t,0.13)+0.5*sin(2*PI*659.25*t)*gte(t,0.13)*lt(t,0.26)+0.5*sin(2*PI*783.99*t)*gte(t,0.26)':s=48000:d=0.5,afade=t=in:d=0.02,afade=t=out:st=0.3:d=0.2"
fc.append(chime+f",apad=whole_dur={DUR}[c]"); lab=["[c]"]
for i,(src,t) in enumerate(sfx):
    fc.append(src+f",adelay={int(t*1000)}:all=1,apad=whole_dur={DUR}[s{i}]"); lab.append(f"[s{i}]")
fc.append(f"anoisesrc=d={DUR}:c=brown:a=0.04:r=48000,lowpass=f=600,afade=t=in:d=1,afade=t=out:st={DUR-1.5}:d=1.5[bed]"); lab.append("[bed]")
fc.append(f"{''.join(lab)}amix=inputs={len(lab)}:normalize=0,atrim=0:{DUR},volume={G}dB,alimiter=limit=0.7:level=false[aout]")
cmd=["ffmpeg","-v","error","-y"]+sum([["-i",I+f"scene-0{k}.mp4"] for k in (1,2,3)],[])+["-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]","-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-ar","48000","-t",str(DUR),"-movflags","+faststart",OUT]
subprocess.run(cmd,check=True); print(OUT)
