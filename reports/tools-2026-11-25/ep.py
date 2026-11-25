import json,sys
sys.path.insert(0,"/home/user/croco-media")
from croco import brand
X1="No realistic bird, no sharp beak, no long tail, no clothing on the bird, no wings or feathers on Croco, no other franchises' bird characters, the bird does not talk, the bird does not fly at the camera, exactly one Croco and one small bird, no extra limbs or extra fingers, no wide-open mouth, no red nose, nothing on Croco's snout, the yellow star stays on the front pocket."
X2="Soft blanket only, no pillow fight, no crying, no tears, no angry faces, no scary dark room, Pebble never goes inside the shell, no red nose, nothing on Croco's snout, the yellow star stays on the front pocket, exactly one Croco and one Pebble, no extra limbs or extra fingers, no wide-open mouth."
G="sunny pastel garden with soft green grass and round pink flower bushes"
B="cozy pastel bedroom in the soft warm evening glow of a small round night-light"
EP={"20261125-01":[(4,False,X1,f"in a {G}, a close-up of Croco's face and shoulders from the very first frame as he cups one hand by his ear with curious big sparkly eyes and a gentle closed-mouth smile, a tiny sky-blue tail of a little bird peeks out from the top of a round pink flower bush beside him, vertical 9:16, calm steady close-up, slow gentle motion."),
 (4,False,X1,f"in the {G}, a small round chubby sky-blue cartoon bird with a tiny soft orange beak and big gentle eyes slowly hops out onto the top of the round pink flower bush, Croco faces the camera and gently claps his hands with a gentle closed-mouth smile, vertical 9:16, steady frontal medium shot, slow gentle motion."),
 (4,False,X1,f"in the {G}, Croco faces the camera from the front the whole time, his round face and big sparkly eyes seen from the front, he stands beside the round pink flower bush where the same small round chubby sky-blue bird sits calmly, Croco gently nods his head with a gentle closed-mouth smile and the little bird gently bobs its head, vertical 9:16, steady frontal medium shot, slow gentle motion.")],
 "20261125-02":[(4,True,X2,f"in a {B}, a close-up of Croco's face and shoulders from the very first frame as he holds a soft folded sky-blue blanket in both hands, Pebble sits on a small round cushion bed beside him looking at the blanket, Croco looks at Pebble with a gentle closed-mouth smile, vertical 9:16, steady close-up, slow gentle motion."),
 (4,True,X2,f"in the {B}, Croco gently spreads the soft sky-blue blanket over Pebble on the small round cushion bed and softly tucks the edges, Pebble's head peeks out and Pebble gives a kind closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion."),
 (4,True,X2,f"in the {B}, Pebble rests snugly under the soft sky-blue blanket on the small round cushion bed and slowly closes its eyes with a peaceful closed-mouth smile, Croco sits beside the bed facing the camera from the front with a gentle closed-mouth smile, vertical 9:16, steady frontal medium shot, slow gentle motion.")]}
def P(e): return [{"seconds":d,"prompt":brand.scene_prompt(s,pebble=pb,extra_negative=x)} for d,pb,x,s in EP[e]]
if __name__=="__main__":
    if sys.argv[1]=="plan": print(json.dumps({e:P(e) for e in EP},indent=1))
    elif sys.argv[1]=="check":
        for e in EP:
            for i,p in enumerate(P(e)): print(e,i+1,brand.check_scene(p["prompt"]) or "OK", len(p["prompt"]))
    else:
        p=P(sys.argv[1])[int(sys.argv[2])-1]
        print(json.dumps({"prompt":p["prompt"],"image_urls":sys.argv[3:],"duration":p["seconds"],"resolution":"720p","aspect_ratio":"9:16"}))
