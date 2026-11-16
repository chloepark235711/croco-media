import json,sys
sys.path.insert(0,"/home/user/main-wt")
from croco import brand
X="Soft ball only, no throwing, no grabbing, no crying, no tears, no angry faces, no wide-open mouth."
SC=[(4,"in a cozy pastel playroom, a close-up of Croco's face and shoulders from the very first frame as he holds a big soft red ball, Pebble sits next to him on a soft rug looking at the ball, Croco looks at Pebble with a gentle closed-mouth smile, vertical 9:16, steady close-up, slow gentle motion."),
 (4,"on the soft rug in the cozy pastel playroom, Croco gently rolls the big soft red ball along the rug to Pebble, Pebble stops it with his short stubby legs and gives a kind closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion."),
 (4,"Pebble slowly rolls the big soft red ball back to Croco, Croco catches it, then both look at the camera with gentle closed-mouth smiles, cozy pastel playroom, vertical 9:16, steady medium shot, slow gentle motion.")]
P=[{"seconds":d,"prompt":brand.scene_prompt(s,pebble=True,extra_negative=X)} for d,s in SC]
if __name__=="__main__":
    if sys.argv[1]=="plan": print(json.dumps(P))
    else:
        i=int(sys.argv[1])-1; print(json.dumps({"prompt":P[i]["prompt"],"image_urls":sys.argv[2:],"duration":P[i]["seconds"],"resolution":"720p","aspect_ratio":"9:16"}))
