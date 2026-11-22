import json,sys
sys.path.insert(0,"/home/user/croco-media")
from croco import brand
X1="No realistic sheep, no horns, no bell, no clothing on the sheep, no other franchises' sheep characters, the sheep does not talk, no black sheep, exactly one Croco, no extra limbs or extra fingers, no wide-open mouth, no mud."
X2="Slow, gentle, in-place moves only, no jumping, no falling, no spinning, exactly one Croco, no extra limbs or extra fingers, no other animals, no wide-open mouth, no strong wind, no falling leaves storm."
F="sunny pastel farm meadow with a low wooden fence and a round golden haystack"
G="sunny pastel garden with soft green grass and one small round friendly tree"
EP={"20261122-01":[(4,False,X1,f"in a {F}, a close-up of Croco's face and shoulders from the very first frame as he leans on the low wooden fence and cups one hand by his ear with curious big sparkly eyes and a gentle closed-mouth smile, a soft fluffy white woolly tuft peeks out from behind the round haystack, vertical 9:16, calm steady close-up, slow gentle motion."),
 (4,False,X1,f"in the {F}, a small round friendly cartoon sheep with fluffy white wool, a soft cream face and small round ears slowly walks out from behind the round haystack onto the grass, Croco faces the camera and gently claps his hands with a gentle closed-mouth smile, vertical 9:16, steady frontal medium shot, slow gentle motion."),
 (4,False,X1,f"in the {F}, Croco stands beside the small round fluffy white cartoon sheep and gives a little wave, the sheep gently nods, then Croco turns his round face to the camera with a gentle closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion.")],
 "20261122-02":[(4,False,X2,f"in a {G}, a close-up of Croco's face and shoulders from the very first frame as he stands in front of the small round tree and slowly raises both arms up high like soft tree branches, big sparkly eyes and a gentle closed-mouth smile, vertical 9:16, calm steady close-up, slow gentle motion."),
 (4,False,X2,f"in the {G}, Croco faces the camera, his round face seen from the front, he stands in place with both arms up high and slowly sways side to side like a little tree in a soft breeze, a few leaves on the tree behind him gently move, gentle closed-mouth smile, vertical 9:16, steady frontal medium shot, slow gentle motion."),
 (4,False,X2,f"in the {G}, Croco stops swaying, slowly lowers his arms and gives a little wave to the camera with a gentle closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion.")]}
def P(e): return [{"seconds":d,"prompt":brand.scene_prompt(s,pebble=pb,extra_negative=x)} for d,pb,x,s in EP[e]]
if __name__=="__main__":
    if sys.argv[1]=="plan": print(json.dumps({e:P(e) for e in EP},indent=1))
    else:
        p=P(sys.argv[1])[int(sys.argv[2])-1]
        print(json.dumps({"prompt":p["prompt"],"image_urls":sys.argv[3:],"duration":p["seconds"],"resolution":"720p","aspect_ratio":"9:16"}))
