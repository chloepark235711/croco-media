import json,sys
sys.path.insert(0,"/tmp/claude-0/-home-user-croco-media/b3454472-bdf1-5140-8934-19f5e6a30c2d/scratchpad/main-wt")
from croco import brand
X1="Exactly one Croco, no extra limbs or extra fingers, no other animals, no frogs, no insects, no eating, no biting, no wide-open mouth, the leaf and apple are plain solid green."
X2="No throwing, no grabbing, no falling, no crying, no tears, no angry faces, no wide-open mouth, no letters or numbers on the blocks, soft blocks only."
G="sunny pastel garden under a small round friendly tree with soft green grass"
R="cozy pastel playroom with a soft rug"
EP={"20261121-01":[(4,False,X1,f"in a {G}, a close-up of Croco's face and shoulders from the very first frame as he holds up one big bright green leaf in front of him and looks at it with curious big sparkly eyes and a gentle closed-mouth smile, vertical 9:16, calm steady close-up, slow gentle motion."),
 (4,False,X1,f"in the {G}, Croco slowly bends down and picks up one shiny round green apple from the soft grass with both hands and holds it up with a gentle closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion."),
 (4,False,X1,f"in the {G}, Croco stands on the soft grass holding the big green leaf in one hand and the round green apple in the other hand, he slowly lifts them up side by side and looks at the camera with a gentle closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion.")],
 "20261121-02":[(4,True,X2,f"in a {R}, a close-up of Croco's face and shoulders from the very first frame as he looks down at many big soft colorful toy blocks scattered all over the rug, Croco looks surprised with big sparkly eyes and a gentle closed-mouth smile, Pebble sits nearby on the rug next to an empty round woven basket, vertical 9:16, steady close-up, slow gentle motion."),
 (4,True,X2,f"in the {R}, Croco faces the camera, his round face seen from the front, he slowly picks up one big soft toy block with both hands and gently puts it into the round woven basket in front of him, Pebble sits beside the basket facing the camera and gently nudges another soft block toward it, gentle closed-mouth smiles, vertical 9:16, steady frontal medium shot, slow gentle motion."),
 (4,True,X2,f"in the tidy {R}, the round woven basket is full of soft colorful toy blocks and the rug is clean, Croco and Pebble sit side by side next to the basket and look at the camera with gentle closed-mouth smiles, vertical 9:16, steady medium shot, slow gentle motion.")]}
def P(e): return [{"seconds":d,"prompt":brand.scene_prompt(s,pebble=pb,extra_negative=x)} for d,pb,x,s in EP[e]]
if __name__=="__main__":
    if sys.argv[1]=="plan": print(json.dumps({e:P(e) for e in EP}))
    else:
        p=P(sys.argv[1])[int(sys.argv[2])-1]
        print(json.dumps({"prompt":p["prompt"],"image_urls":sys.argv[3:],"duration":p["seconds"],"resolution":"720p","aspect_ratio":"9:16"}))
