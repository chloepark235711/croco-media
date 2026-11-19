import json,sys
sys.path.insert(0,"/tmp/claude-0/-home-user-croco-media/b4302259-90f3-54f3-bab6-df33d15223bc/scratchpad/main-wt")
from croco import brand
X1="No realistic rabbit, no clothing on the bunny, no other franchises' rabbit characters, the bunny does not talk, exactly one bunny, no eating, no wide-open mouth."
X2="No eating the flower, no pulling plants, no grabbing, no crying, no tears, no angry faces, no wide-open mouth."
G="sunny pastel garden with soft green grass and round flowers"
EP={"20261119-01":[(4,False,X1,f"in a {G}, a close-up of Croco's face and shoulders from the very first frame as he peeks curiously at a big round terracotta flower pot with big sparkly eyes and a gentle closed-mouth smile, two soft long white bunny ears slowly peek up from behind the flower pot, vertical 9:16, calm steady close-up, slow gentle motion."),
 (4,False,X1,f"in the {G}, a small fluffy white cartoon bunny with a pink nose slowly hops out from behind the big round terracotta flower pot onto the soft grass, Croco gently claps his hands with a gentle closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion."),
 (4,False,X1,f"Croco sits on the soft grass beside the small fluffy white bunny in the {G} and gives a little wave, the bunny gently wiggles its pink nose, then Croco looks at the camera with a gentle closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion.")],
 "20261119-02":[(4,True,X2,f"in a {G}, a close-up of Croco's face and shoulders from the very first frame as he looks with happy surprised big sparkly eyes at one small yellow daisy flower lying on the grass, Pebble sits next to him and gently nudges the small yellow daisy toward Croco with his short stubby front leg, gentle closed-mouth smiles, vertical 9:16, steady close-up, slow gentle motion."),
 (4,True,X2,f"in the {G}, Croco gently picks up the small yellow daisy flower and holds it close to his chest, he gives Pebble a kind closed-mouth smile and a small thank-you nod, Pebble smiles back with a gentle closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion."),
 (4,True,X2,f"Croco and Pebble sit side by side on the soft grass in the {G}, Croco holds the small yellow daisy flower, they lean together in a soft gentle hug, then look at the camera with gentle closed-mouth smiles, vertical 9:16, steady medium shot, slow gentle motion.")]}
def P(e): return [{"seconds":d,"prompt":brand.scene_prompt(s,pebble=pb,extra_negative=x)} for d,pb,x,s in EP[e]]
if __name__=="__main__":
    if sys.argv[1]=="plan": print(json.dumps({e:P(e) for e in EP}))
    else:
        p=P(sys.argv[1])[int(sys.argv[2])-1]
        print(json.dumps({"prompt":p["prompt"],"image_urls":sys.argv[3:],"duration":p["seconds"],"resolution":"720p","aspect_ratio":"9:16"}))
