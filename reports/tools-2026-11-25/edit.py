import subprocess,sys
EP=sys.argv[1]; OUT=sys.argv[2]; G=sys.argv[3] if len(sys.argv)>3 else "0"
S="/tmp/claude-0/-home-user-croco-media/c551f312-2234-5404-add7-84a5b7941e9a/scratchpad/tts/"
I="/home/user/inbox/clips/2026-11-25/"+EP+"/"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
bell=lambda f=1046.5:f"aevalsrc='(0.22*sin(2*PI*{f}*t)+0.06*sin(2*PI*{2*f}*t))*exp(-5*t)':s=48000:d=0.7,afade=t=in:d=0.01"
tap="aevalsrc='0.35*sin(2*PI*180*t)*exp(-28*t)':s=48000:d=0.25,lowpass=f=1200"
boop="aevalsrc='0.25*sin(2*PI*(600*t+500*t*t))*exp(-9*t)':s=48000:d=0.35"
pluck=lambda f:f"aevalsrc='0.22*sin(2*PI*{f}*t)*exp(-7*t)':s=48000:d=0.6"
rustle="anoisesrc=d=0.8:c=pink:a=0.10:r=48000,highpass=f=1500,lowpass=f=6000,afade=t=in:d=0.2,afade=t=out:st=0.4:d=0.4"
baa="aevalsrc='0.20*(sin(2*PI*(300*t+2.2*sin(2*PI*7*t)))+0.5*sin(2*PI*(600*t+4.4*sin(2*PI*7*t)))+0.25*sin(2*PI*(900*t+6.6*sin(2*PI*7*t))))*(1-exp(-25*t))*exp(-3.2*t)':s=48000:d=0.6,lowpass=f=2200,afade=t=out:st=0.45:d=0.15"
wind="anoisesrc=d=3.6:c=pink:a=0.12:r=48000,bandpass=f=700:w=500,afade=t=in:d=1.2,afade=t=out:st=2.2:d=1.4"
DUR=12.0
oink="aevalsrc='0.30*(sin(2*PI*(170*t+3*sin(2*PI*30*t)))+0.6*sin(2*PI*(340*t+6*sin(2*PI*30*t)))+0.3*sin(2*PI*(510*t)))*(1-exp(-40*t))*exp(-9*t)':s=48000:d=0.28,lowpass=f=1400,afade=t=out:st=0.2:d=0.08"
hug="aevalsrc='0.18*sin(2*PI*392*t)+0.12*sin(2*PI*493.88*t)+0.10*sin(2*PI*587.33*t)':s=48000:d=1.4,afade=t=in:d=0.5,afade=t=out:st=0.6:d=0.8"
neigh="aevalsrc='0.22*(sin(2*PI*(520*t-260*t*t+18*sin(2*PI*11*t)))+0.5*sin(2*PI*(1040*t-520*t*t+36*sin(2*PI*11*t))))*(1-exp(-30*t))*exp(-2.6*t)':s=48000:d=0.75,lowpass=f=2600,afade=t=out:st=0.55:d=0.2"
clop="aevalsrc='0.4*sin(2*PI*900*t)*exp(-60*t)':s=48000:d=0.12,highpass=f=300"
SEGS=[(0,4.0),(0,4.0),(0,4.0)]
caps=[(0,2,"Who says tweet?"),(2,4,"Listen! Tweet, tweet!"),(4,6,"A little bird!"),(6,8,"Tweet, tweet, bird!"),(8,10,"Hello, bird!"),(10,12,"Your turn!|Say tweet!")]
tweet="aevalsrc='0.16*sin(2*PI*(2600*t+9000*t*t))*(1-exp(-60*t))*exp(-14*t)':s=48000:d=0.18,afade=t=out:st=0.12:d=0.06"
sfx=[(rustle,0.6),(rustle,2.0),(tweet,3.35),(tweet,3.6),(pluck(784),4.05),(tweet,7.45),(tweet,7.7),(bell(),8.05),(pluck(659),10.05)]
vstart=[0.45,2.15,4.15,6.15,8.15,10.15]
def esc(s): return s.replace("'", "’").replace(":", "\\:").replace(",", "\\,")
N="scale=1080:1920:flags=lanczos,setsar=1,fps=30"
fc=[]; pad=DUR-sum(b-a for a,b in SEGS)
for k,(a,b) in enumerate(SEGS):
    p=f",tpad=stop_mode=clone:stop_duration={pad+0.1:.2f}" if k==2 else ""
    fc.append(f"[{k}:v]trim={a}:{b},setpts=PTS-STARTPTS{p},{N}[v{k}]")
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
    fc.append(src+f",volume=0.6,adelay={int(t*1000)}:all=1,apad=whole_dur={DUR}[s{i}]"); lab.append(f"[s{i}]")
fc.append(f"anoisesrc=d={DUR}:c=brown:a=0.03:r=48000,lowpass=f=600,afade=t=in:d=1,afade=t=out:st={DUR-1.5}:d=1.5[bed]"); lab.append("[bed]")
e=EP[-2:]
for i,t in enumerate(vstart):
    fc.append(f"[{3+i}:a]aresample=48000,aformat=channel_layouts=stereo,volume=2.2,adelay={int(t*1000)}:all=1,apad=whole_dur={DUR}[t{i}]"); lab.append(f"[t{i}]")
fc.append(f"{''.join(lab)}amix=inputs={len(lab)}:normalize=0,atrim=0:{DUR},volume={G}dB,alimiter=limit=0.85:level=false[aout]")
ins=sum([["-i",I+f"scene-0{k}.mp4"] for k in (1,2,3)],[])+sum([["-i",S+f"{e}-{i}.mp3"] for i in range(6)],[])
cmd=["ffmpeg","-v","error","-y"]+ins+["-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]","-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-t",str(DUR),"-movflags","+faststart",OUT]
subprocess.run(cmd,check=True); print(OUT)
