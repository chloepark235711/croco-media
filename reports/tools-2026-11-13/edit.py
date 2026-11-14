# 20261114-02 Stars: S1 0-4, S2-retry 0-5, S3-retry 0-3.0 slowed to 4.0 s + 1.0 s hold (mouth opens after 3.5 s -> cut)
import subprocess,sys
C="/home/user/inbox/clips/2026-11-14/20261114-02/"; FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT=sys.argv[1]; DUR=14
caps=[(0,2.4,"Look! A star!"),(2.4,4.8,"Let's count the stars!"),(4.8,5.7,"One!"),(5.7,6.6,"Two!"),(6.6,7.5,"Three!"),(7.5,8.3,"Four!"),(8.3,9,"Five!"),(9,11.5,"Five stars!"),(11.5,14,"Count with me! Your turn!")]
def esc(s): return s.replace("'", "’").replace(":", "\\:").replace(",", "\\,")
fc=[]
N="scale=1080:1920:flags=lanczos,setsar=1,fps=30"
fc.append(f"[0:v]trim=0:4,setpts=PTS-STARTPTS,{N}[v0]")
fc.append(f"[1:v]trim=0:5,setpts=PTS-STARTPTS,{N}[v1]")
fc.append(f"[2:v]trim=0:3.0,setpts=(PTS-STARTPTS)*4/3,{N},tpad=stop_mode=clone:stop_duration=1.0,trim=0:5,setpts=PTS-STARTPTS[v2]")
fc.append("[v0][v1][v2]concat=n=3:v=1:a=0[vc]")
LINES={"Let's count the stars!":["Let's count","the stars!"],"Count with me! Your turn!":["Count with me!","Your turn!"]}
dt=[]
for a,b,t in caps:
    ls=LINES.get(t,[t])
    for k,l in enumerate(ls):
        y=f"h*0.72+{(k-(len(ls)-1)/2)*120:.0f}"
        dt.append(f"drawtext=fontfile={FONT}:text='{esc(l)}':fontcolor=white:fontsize={min(110,int(940/(len(l)*0.62)))}:borderw=9:bordercolor=0x222222:x=(w-text_w)/2:y={y}:enable='between(t,{a},{b-0.001})'")
fc.append("[vc]"+",".join(dt)+"[vout]")
chime="aevalsrc='0.5*sin(2*PI*523.25*t)*lt(t,0.13)+0.5*sin(2*PI*659.25*t)*gte(t,0.13)*lt(t,0.26)+0.5*sin(2*PI*783.99*t)*gte(t,0.26)':s=48000:d=0.5,afade=t=in:d=0.02,afade=t=out:st=0.3:d=0.2"
fc.append(chime+f",apad=whole_dur={DUR}[c]")
# soft single bell (same pitch each star, decaying sine + octave partial) at each star appearance
times=[2.0,4.8,5.7,6.6,7.5,8.3]
bell="aevalsrc='(0.22*sin(2*PI*1046.5*t)+0.06*sin(2*PI*2093*t))*exp(-5*t)':s=48000:d=0.7,afade=t=in:d=0.01"
lab=[]
for i,t in enumerate(times):
    fc.append(bell+f",adelay={int(t*1000)}:all=1,apad=whole_dur={DUR}[b{i}]"); lab.append(f"[b{i}]")
# very soft evening air bed
fc.append(f"anoisesrc=d={DUR}:c=brown:a=0.05:r=48000,lowpass=f=600,afade=t=in:d=1,afade=t=out:st={DUR-1.5}:d=1.5[bed]")
fc.append(f"[c]{''.join(lab)}[bed]amix=inputs={len(times)+2}:normalize=0,atrim=0:{DUR},volume={sys.argv[2] if len(sys.argv)>2 else 0}dB,alimiter=limit=0.7:level=false[aout]")
cmd=["ffmpeg","-v","error","-y","-i",C+"scene-01.mp4","-i",C+"scene-02-retry.mp4","-i",C+"scene-03-retry.mp4","-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]","-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-ar","48000","-t",str(DUR),"-movflags","+faststart",OUT]
subprocess.run(cmd,check=True); print(OUT)
