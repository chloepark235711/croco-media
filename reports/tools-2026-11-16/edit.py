# usage: edit.py EP OUT [gain_dB]
import subprocess,sys
EP,OUT=sys.argv[1],sys.argv[2]; G=sys.argv[3] if len(sys.argv)>3 else "0"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
C=f"/home/user/croco-media/clips/2026-11-16/{EP}/"
CFG={
"20261116-01":dict(dur=12,
  clips=[("v4-scene-01.mp4","trim=0:4,setpts=PTS-STARTPTS"),("v4-scene-02.mp4","trim=0:4,setpts=PTS-STARTPTS"),("v4-scene-03.mp4","trim=0:4,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.2")],
  caps=[(0,2,"Whose turn is it?"),(2,4,"My turn!"),(4,6,"Your turn, Pebble!"),(6,8,"Roll, roll, roll!"),(8,10,"Taking turns is fun!"),(10,12,"Your turn!|Say my turn!")],
  up=[],down=[],bell=[8.2],roll=[4.6,6.3,9.0]),
}[EP]
DUR=CFG["dur"]
def esc(s): return s.replace("'", "’").replace(":", "\\:").replace(",", "\\,")
fc=[];N="scale=1080:1920:flags=lanczos,setsar=1,fps=30"
inp=[]
for k,(f,flt) in enumerate(CFG["clips"]):
    inp+=["-i",C+f]; fc.append(f"[{k}:v]{flt},{N}[v{k}]")
n=len(CFG["clips"]); fc.append("".join(f"[v{k}]" for k in range(n))+f"concat=n={n}:v=1:a=0,trim=0:{DUR},setpts=PTS-STARTPTS[vc]")
dt=[]
for a,b,t in CFG["caps"]:
    ls=t.split("|")
    for k,l in enumerate(ls):
        y=f"h*0.72+{(k-(len(ls)-1)/2)*120:.0f}"
        dt.append(f"drawtext=fontfile={FONT}:text='{esc(l)}':fontcolor=white:fontsize={min(110,int(940/(len(l)*0.62)))}:borderw=9:bordercolor=0x222222:x=(w-text_w)/2:y={y}:enable='between(t,{a},{b-0.001})'")
fc.append("[vc]"+",".join(dt)+"[vout]")
chime="aevalsrc='0.5*sin(2*PI*523.25*t)*lt(t,0.13)+0.5*sin(2*PI*659.25*t)*gte(t,0.13)*lt(t,0.26)+0.5*sin(2*PI*783.99*t)*gte(t,0.26)':s=48000:d=0.5,afade=t=in:d=0.02,afade=t=out:st=0.3:d=0.2"
fc.append(chime+f",apad=whole_dur={DUR}[c]"); lab=["[c]"]; i=0
def add(src,t):
    global i; fc.append(src+f",adelay={int(t*1000)}:all=1,apad=whole_dur={DUR}[s{i}]"); lab.append(f"[s{i}]"); i+=1
for t in CFG["up"]:   add("aevalsrc='0.18*sin(2*PI*(300*t+250*t*t))':s=48000:d=1.2,afade=t=in:d=0.15,afade=t=out:st=0.8:d=0.4",t)
for t in CFG["down"]: add("aevalsrc='0.18*sin(2*PI*(900*t-250*t*t))':s=48000:d=1.2,afade=t=in:d=0.15,afade=t=out:st=0.8:d=0.4",t)
for t in CFG.get("roll",[]): add("anoisesrc=d=1.1:c=brown:a=0.5:r=48000,lowpass=f=300,volume=1.6,afade=t=in:d=0.25,afade=t=out:st=0.6:d=0.5",t)
for t in CFG["bell"]: add("aevalsrc='(0.22*sin(2*PI*1046.5*t)+0.06*sin(2*PI*2093*t))*exp(-5*t)':s=48000:d=0.7,afade=t=in:d=0.01",t)
fc.append(f"anoisesrc=d={DUR}:c=brown:a=0.04:r=48000,lowpass=f=600,afade=t=in:d=1,afade=t=out:st={DUR-1.5}:d=1.5[bed]"); lab.append("[bed]")
fc.append(f"{''.join(lab)}amix=inputs={len(lab)}:normalize=0,atrim=0:{DUR},volume={G}dB,alimiter=limit=0.7:level=false[aout]")
cmd=["ffmpeg","-v","error","-y"]+inp+["-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]","-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-ar","48000","-t",str(DUR),"-movflags","+faststart",OUT]
subprocess.run(cmd,check=True); print(OUT)
