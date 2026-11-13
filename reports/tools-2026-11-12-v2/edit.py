import subprocess,sys,os
W="/tmp/claude-0/w"; FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
clips=[("dl/s1.mp4",4),("dl/s2r.mp4",5),("dl/s3.mp4",5)]
caps=[(0,2,"What's in the bush?"),(2,4,"Look! It wiggles!"),(4,6,"A duck!"),(6,9,"Quack, quack, duck!"),(9,11,"Hello, duck!"),(11,14,"Your turn! Say duck!")]
DUR=14
def esc(s): return s.replace("'", "’").replace(":", "\\:").replace(",", "\\,")
inp=[];fc=[]
for i,(c,d) in enumerate(clips):
    inp+=["-i",f"{W}/{c}"]
    fc.append(f"[{i}:v]trim=0:{d},setpts=PTS-STARTPTS,scale=1080:1920:flags=lanczos,setsar=1,fps=30[v{i}]")
fc[2]=("[2:v]split[s3a][s3b];[s3a]trim=0:3.95,setpts=PTS-STARTPTS[s3x];[s3b]trim=4.45:5.04,setpts=PTS-STARTPTS[s3y];"
 "[s3x][s3y]concat=n=2:v=1:a=0,tpad=stop_mode=clone:stop_duration=0.6,trim=0:5,setpts=PTS-STARTPTS,scale=1080:1920:flags=lanczos,setsar=1,fps=30[v2]")
fc.append("[v0][v1][v2]concat=n=3:v=1:a=0[vc]")
dt=[f"drawtext=fontfile={FONT}:text='{esc(t)}':fontcolor=white:fontsize={min(104,int(940/(len(t)*0.62)))}:borderw=9:bordercolor=0x222222:x=(w-text_w)/2:y=h*0.72:enable='between(t,{a},{b-0.001})'" for a,b,t in caps]
fc.append("[vc]"+",".join(dt)+"[vout]")
# audio (all self-synthesized)
chime="aevalsrc='0.5*sin(2*PI*523.25*t)*lt(t,0.13)+0.5*sin(2*PI*659.25*t)*gte(t,0.13)*lt(t,0.26)+0.5*sin(2*PI*783.99*t)*gte(t,0.26)':s=48000:d=0.5,afade=t=in:d=0.02,afade=t=out:st=0.3:d=0.2"
fc.append(chime+f",apad=whole_dur={DUR}[c]")
# leaf rustle: band-passed noise with slow amplitude wobble, 0-4s
fc.append(f"anoisesrc=d=4:c=pink:a=0.35:r=48000,bandpass=f=3500:w=2500,volume='0.25+0.2*sin(2*PI*2.3*t)':eval=frame,afade=t=in:d=0.4,afade=t=out:st=3.4:d=0.6,apad=whole_dur={DUR}[r]")
# soft quack x2 at 4.3 and 4.9: nasal tone (square-ish) with downward pitch
q="aevalsrc='0.25*sgn(sin(2*PI*(520*t-400*t*t)))*sin(PI*t/0.18)':s=48000:d=0.18,lowpass=f=1800,highpass=f=300"
fc.append(q+",adelay=4300:all=1"+f",apad=whole_dur={DUR}[q1]")
fc.append(q+",adelay=4900:all=1"+f",apad=whole_dur={DUR}[q2]")
fc.append(f"[c][r][q1][q2]amix=inputs=4:normalize=0,atrim=0:{DUR},volume={sys.argv[1] if len(sys.argv)>1 else 0}dB,alimiter=limit=0.84:level=false[aout]")
out=f"{W}/out/20261113-01.mp4"
cmd=["ffmpeg","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]","-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-ar","48000","-t",str(DUR),"-movflags","+faststart",out]
subprocess.run(cmd,check=True); print(out)
