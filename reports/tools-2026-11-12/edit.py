import subprocess
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
caps=[(0,2,"Oops!"),(2,4,"The tower fell!"),(4,6,"I'm sorry, Pebble."),(6,8,"That's okay!"),(8,10,"Let's build again!"),(10,12,"Your turn! Say sorry.")]
def esc(s): return s.replace("'", "’").replace(":", "\\:").replace(",", "\\,")
fc=["[0:v]trim=0:4,setpts=PTS-STARTPTS,scale=1080:1920:flags=lanczos,setsar=1,fps=30[v0]",
    "[1:v]trim=0:4,setpts=PTS-STARTPTS,scale=1080:1920:flags=lanczos,setsar=1,fps=30[v1]",
    "[2:v]trim=0.75:2.25,setpts=(PTS-STARTPTS)/0.6,scale=1080:1920:flags=lanczos,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=1.6,trim=0:4,setpts=PTS-STARTPTS[v2]",
    "[v0][v1][v2]concat=n=3:v=1:a=0[vc]"]
dt=[f"drawtext=fontfile={FONT}:text='{esc(t)}':fontcolor=white:fontsize={min(104,int(940/(len(t)*0.66)))}:borderw=9:bordercolor=0x222222:x=(w-text_w)/2:y=h*0.70:enable='between(t,{a},{b-0.001})'" for a,b,t in caps]
fc.append("[vc]"+",".join(dt)+"[vout]")
sfx=[(0,"chime",1.0)]+[(t,"thud",g) for t,g in [(0.3,1.0),(0.6,0.8),(0.95,0.65),(1.3,0.5)]]+[(t,"tok",0.9) for t in (8.2,8.8,9.5,10.2,11.0)]
ins=["-i","scene-01-2c7f2f.mp4","-i","scene-02-ab1087.mp4","-i","scene-3r-ff739f.mp4"]
al=[]
for j,(t,k,g) in enumerate(sfx):
    ins+=["-i",f"{k}.wav"]; idx=3+j
    fc.append(f"[{idx}:a]volume={g},adelay={int(t*1000)}:all=1,apad=whole_dur=12[s{j}]"); al.append(f"[s{j}]")
fc.append("".join(al)+f"amix=inputs={len(al)}:normalize=0,atrim=0:12,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,volume=0.8dB,alimiter=limit=0.89:level=false[aout]")
subprocess.run(["ffmpeg","-v","error","-y",*ins,"-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]",
 "-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-ar","48000","-t","12","-movflags","+faststart","final.mp4"],check=True)
