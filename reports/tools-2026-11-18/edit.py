import subprocess,sys
EP=sys.argv[1]; OUT=sys.argv[2]; G=sys.argv[3] if len(sys.argv)>3 else "0"
I="/home/user/inbox/clips/2026-11-18/"+EP+"/"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
bell=lambda f=1046.5:f"aevalsrc='(0.22*sin(2*PI*{f}*t)+0.06*sin(2*PI*{2*f}*t))*exp(-5*t)':s=48000:d=0.7,afade=t=in:d=0.01"
tap="aevalsrc='0.35*sin(2*PI*180*t)*exp(-28*t)':s=48000:d=0.25,lowpass=f=1200"
boop="aevalsrc='0.25*sin(2*PI*(600*t+500*t*t))*exp(-9*t)':s=48000:d=0.35"
trill="aevalsrc='0.12*sin(2*PI*(700+150*sin(2*PI*7*t))*t)*(1-exp(-6*t))':s=48000:d=2.2,afade=t=out:st=1.6:d=0.6"
pluck=lambda f:f"aevalsrc='0.22*sin(2*PI*{f}*t)*exp(-7*t)':s=48000:d=0.6"
if EP=="20261118-01":
    SEG=5; DUR=16; caps=[(0,2.5,"Can you pat|your head?"),(2.5,5,"Pat, pat, head!"),(5,7.5,"Touch your nose!"),(7.5,10,"Touch, touch, nose!"),(10,12.5,"Wiggle your toes!"),(12.5,14,"Wiggle, wiggle!"),(14,16,"Your turn!|Pat, touch, wiggle!")]
    sfx=[(tap,t) for t in (1.0,1.6,2.6,3.2,3.8)]+[(boop,6.6),(boop,8.2),(trill,10.6),(bell(),14.0)]
else:
    SEG=4; DUR=13; caps=[(0,2,"Two apples!"),(2,4,"Let's share!"),(4,6,"One for you!"),(6,8,"One for Pebble!"),(8,10,"One for me, too!"),(10,13,"Your turn!|Say one for you!")]
    sfx=[(pluck(784),4.6),(pluck(659),6.3),(bell(),8.1)]
def esc(s): return s.replace("'", "’").replace(":", "\\:").replace(",", "\\,")
N="scale=1080:1920:flags=lanczos,setsar=1,fps=30"
fc=[f"[0:v]trim=0:{SEG},setpts=PTS-STARTPTS,{N}[v0]",f"[1:v]trim=0:{SEG},setpts=PTS-STARTPTS,{N}[v1]",
    f"[2:v]trim=0:{SEG},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1.2,{N}[v2]",
    f"[v0][v1][v2]concat=n=3:v=1:a=0,trim=0:{DUR},setpts=PTS-STARTPTS[vc]"]
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
