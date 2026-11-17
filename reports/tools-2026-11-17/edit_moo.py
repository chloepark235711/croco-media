import subprocess,sys
OUT=sys.argv[1]; G=sys.argv[2] if len(sys.argv)>2 else "0"
S="/tmp/claude-0/-home-user-croco-media/5effeaa7-d171-59fb-95dc-dd1d5c51e2d6/scratchpad/clips/"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; DUR=11
caps=[(0,2.5,"Who says moo?"),(2.5,5.5,"Listen! Moo!"),(5.5,7.5,"A cow!"),(7.5,9,"Moo, moo, cow!"),(9,11,"Your turn!|Say moo!")]
def esc(s): return s.replace("'", "’").replace(":", "\\:").replace(",", "\\,")
N="scale=1080:1920:flags=lanczos,setsar=1,fps=30"
fc=[f"[0:v]trim=0:5,setpts=PTS-STARTPTS,{N}[v0]",f"[1:v]trim=0:5,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1.2,{N}[v1]",
    f"[v0][v1]concat=n=2:v=1:a=0,trim=0:{DUR},setpts=PTS-STARTPTS[vc]"]
dt=[]
for a,b,t in caps:
    ls=t.split("|")
    for k,l in enumerate(ls):
        y=f"h*0.72+{(k-(len(ls)-1)/2)*120:.0f}"
        dt.append(f"drawtext=fontfile={FONT}:text='{esc(l)}':fontcolor=white:fontsize={min(110,int(940/(len(l)*0.62)))}:borderw=9:bordercolor=0x222222:x=(w-text_w)/2:y={y}:enable='between(t,{a},{b-0.001})'")
fc.append("[vc]"+",".join(dt)+"[vout]")
chime="aevalsrc='0.5*sin(2*PI*523.25*t)*lt(t,0.13)+0.5*sin(2*PI*659.25*t)*gte(t,0.13)*lt(t,0.26)+0.5*sin(2*PI*783.99*t)*gte(t,0.26)':s=48000:d=0.5,afade=t=in:d=0.02,afade=t=out:st=0.3:d=0.2"
fc.append(chime+f",apad=whole_dur={DUR}[c]"); lab=["[c]"]; i=0
def add(src,t):
    global i; fc.append(src+f",adelay={int(t*1000)}:all=1,apad=whole_dur={DUR}[s{i}]"); lab.append(f"[s{i}]"); i+=1
# soft synthesized low "moo" hum: gliding 130->95 Hz with harmonics, slow envelope (no samples)
moo="aevalsrc='0.30*sin(2*PI*(130*t-8*t*t))+0.15*sin(4*PI*(130*t-8*t*t))+0.07*sin(6*PI*(130*t-8*t*t))':s=48000:d=1.3,lowpass=f=900,afade=t=in:d=0.25,afade=t=out:st=0.8:d=0.5"
for t in (2.7,7.6,8.4): add(moo,t)
add("anoisesrc=d=4.5:c=pink:a=0.06:r=48000,highpass=f=2500,lowpass=f=7000,afade=t=in:d=0.6,afade=t=out:st=3.4:d=1.1",0.4)  # grass rustle
add("aevalsrc='(0.22*sin(2*PI*1046.5*t)+0.06*sin(2*PI*2093*t))*exp(-5*t)':s=48000:d=0.7,afade=t=in:d=0.01",5.6)  # soft reveal bell
fc.append(f"anoisesrc=d={DUR}:c=brown:a=0.04:r=48000,lowpass=f=600,afade=t=in:d=1,afade=t=out:st={DUR-1.5}:d=1.5[bed]"); lab.append("[bed]")
fc.append(f"{''.join(lab)}amix=inputs={len(lab)}:normalize=0,atrim=0:{DUR},volume={G}dB,alimiter=limit=0.7:level=false[aout]")
cmd=["ffmpeg","-v","error","-y","-i",S+"scene-01.mp4","-i",S+"scene-02.mp4","-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]","-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-ar","48000","-t",str(DUR),"-movflags","+faststart",OUT]
subprocess.run(cmd,check=True); print(OUT)
