import json,sys
sys.path.insert(0,"/tmp/claude-0/-home-user-croco-media/b01fe258-1fb0-538d-8167-c666722c8183/scratchpad/main-wt")
from croco import brand
X1="Slow, gentle, in-place moves only, no jumping, no running, no falling, exactly one Croco, no extra limbs or extra fingers, no motion blur, no wide-open mouth."
X2="No throwing, no grabbing, no falling, no crying, no tears, no angry faces, no wide-open mouth."
G="sunny pastel garden with soft green grass and round flowers"
R="cozy pastel playroom with a soft rug"
EP={"20261120-01":[(4,False,X1,f"in a {G}, a close-up of Croco's face and shoulders from the very first frame as he holds both hands up in front of his chest and claps them together very slowly, one slow soft clap at a time, with big sparkly eyes and a gentle closed-mouth smile, vertical 9:16, calm steady close-up, slow gentle motion."),
 (4,False,X1,f"in the {G}, Croco stands on the soft grass and claps his hands quickly with many small light quick claps in front of his chest, his body stays in place, gentle closed-mouth smile, vertical 9:16, steady medium shot, camera does not move."),
 (4,False,X1,f"in the {G}, Croco stands on the soft grass and slowly waves one hand at the camera in a big slow gentle wave, then holds both hands together with a gentle closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion.")],
 "20261120-02":[(4,True,X2,f"in a {R}, a close-up of Croco's face and shoulders from the very first frame as he leans both hands on a big round soft yellow floor cushion that is bigger than him and gently tries to push it, the cushion does not move, Croco looks puzzled with big sparkly eyes and a gentle closed-mouth smile, Pebble sits nearby on the rug watching, vertical 9:16, steady close-up, slow gentle motion."),
 (4,True,X2,f"in the {R}, Pebble slowly walks to the big round soft yellow floor cushion and gently pushes it with the side of his shell while Croco pushes it with both hands, together they slowly slide the soft cushion across the rug, gentle closed-mouth smiles, vertical 9:16, steady medium shot, slow gentle motion."),
 (4,True,X2,f"in the {R}, Croco and Pebble sit side by side on top of the big round soft yellow floor cushion, Croco gives Pebble a soft gentle hug, then they both look at the camera with gentle closed-mouth smiles, vertical 9:16, steady medium shot, slow gentle motion.")]}
def P(e): return [{"seconds":d,"prompt":brand.scene_prompt(s,pebble=pb,extra_negative=x)} for d,pb,x,s in EP[e]]
if __name__=="__main__":
    if sys.argv[1]=="plan": print(json.dumps({e:P(e) for e in EP}))
    else:
        p=P(sys.argv[1])[int(sys.argv[2])-1]
        print(json.dumps({"prompt":p["prompt"],"image_urls":sys.argv[3:],"duration":p["seconds"],"resolution":"720p","aspect_ratio":"9:16"}))
