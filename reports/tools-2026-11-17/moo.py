import json,sys
sys.path.insert(0,"/tmp/claude-0/-home-user-croco-media/5effeaa7-d171-59fb-95dc-dd1d5c51e2d6/scratchpad/main-wt")
from croco import brand
X="No realistic cow, no horns, no bell, no clothing on the cow, no other franchises' cow characters, the cow does not talk, no mud, no wide-open mouth."
SC=[(5,"in a sunny pastel farm meadow with a low wooden fence, a close-up of Croco's face and shoulders from the very first frame as he leans on the fence and cups one hand by his ear with curious big sparkly eyes and a gentle closed-mouth smile, a soft brown-and-white ear peeks out from behind a round haystack, vertical 9:16, calm steady close-up, slow gentle motion."),
 (5,"a small round friendly cartoon cow with soft brown and white patches slowly walks out from behind the round haystack onto the grass and stands beside Croco, Croco softly claps his hands and gives the cow a little wave with a gentle closed-mouth smile, the cow gently nods, sunny pastel farm meadow, vertical 9:16, steady medium shot, slow gentle motion.")]
P=[{"seconds":d,"prompt":brand.scene_prompt(s,extra_negative=X)} for d,s in SC]
if __name__=="__main__":
    if sys.argv[1]=="plan": print(json.dumps(P))
    else:
        i=int(sys.argv[1])-1; print(json.dumps({"prompt":P[i]["prompt"],"image_urls":sys.argv[2:],"duration":P[i]["seconds"],"resolution":"720p","aspect_ratio":"9:16"}))
