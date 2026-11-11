import subprocess, sys, json, os
W=os.path.dirname(os.path.abspath(__file__))
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
EPS={
 "A":{"clips":["A_1","A_2","A_3"],"dur":15,
      "caps":[(0,3,"Can you hop?"),(3,5,"Hop!"),(5,10,"Waddle, waddle!"),(10,13,"Stomp, stomp!"),(13,15,"Your turn!")],
      "sfx":[(0.15,"chime"),(3,"up"),(5,"chime"),(10,"down"),(13,"chime")]},
 "B":{"clips":["B_1",("B_2r",4.16)],"dur":10,
      "caps":[(0,5,"Up!"),(5,8,"Down!"),(8,10,"Up high, down low!")],
      "sfx":[(0.15,"up"),(5,"down"),(8,"chime")]},
}
# original synthesized SFX (sine tones), all rights ours
def sfx_expr(kind):
    if kind=="chime":   # two soft bell notes
        return "0.5*sin(2*PI*1046.5*t)*exp(-6*t)+0.35*sin(2*PI*1318.5*t)*exp(-6*t)*gte(t,0.12)", 0.9
    if kind=="up":      # gentle rising glide
        return "0.6*sin(2*PI*(400*t+500*t*t))*sin(PI*t/0.7)", 0.7
    if kind=="down":    # gentle falling glide
        return "0.6*sin(2*PI*(900*t-500*t*t))*sin(PI*t/0.7)", 0.7
def esc(s): return s.replace("'", "’").replace(":", "\\:").replace(",", "\\,")
def build(ep):
    e=EPS[ep]; inp=[]; fc=[]
    for i,c in enumerate(e["clips"]):
        name,cut=(c if isinstance(c,tuple) else (c,None))
        inp+=["-i",f"{W}/dl/{name}.mp4"]
        tr=f"trim=0:{cut},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={5.0-cut:.3f}," if cut else "trim=0:5,setpts=PTS-STARTPTS,"
        fc.append(f"[{i}:v]{tr}scale=1080:1920:flags=lanczos,setsar=1,fps=30[v{i}]")
    n=len(e["clips"])
    fc.append("".join(f"[v{i}]" for i in range(n))+f"concat=n={n}:v=1:a=0[vc]")
    dt=[]
    for (a,b,t) in e["caps"]:
        dt.append(f"drawtext=fontfile={FONT}:text='{esc(t)}':fontcolor=white:fontsize={min(104,int(940/(len(t)*0.66)))}:borderw=9:bordercolor=0x222222:x=(w-text_w)/2:y=h*0.70:enable='between(t,{a},{b-0.001})'")
    fc.append("[vc]"+",".join(dt)+"[vout]")
    al=[]
    for j,(t0,k) in enumerate(e["sfx"]):
        ex,d=sfx_expr(k)
        fc.append(f"aevalsrc='{ex}':s=48000:d={d},afade=t=out:st={d-0.15}:d=0.15,adelay={int(t0*1000)}:all=1,apad=whole_dur={e['dur']}[s{j}]")
        al.append(f"[s{j}]")
    fc.append("".join(al)+f"amix=inputs={len(al)}:normalize=0,atrim=0:{e['dur']},volume={e.get('gain',0)}dB,alimiter=limit=0.84:level=false[aout]")
    out=f"{W}/out/{ep}.mp4"
    cmd=["ffmpeg","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]",
         "-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p","-r","30",
         "-c:a","aac","-b:a","192k","-ar","48000","-t",str(e["dur"]),"-movflags","+faststart",out]
    subprocess.run(cmd,check=True); print("wrote",out)
G=json.loads(os.environ.get('GAINS','{}'))
for ep in sys.argv[1:]:
    EPS[ep]['gain']=G.get(ep,0); build(ep)
