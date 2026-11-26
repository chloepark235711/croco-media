import json,sys
sys.path.insert(0,"/home/user/croco-media")
from croco import brand
X1="The teddy bear is a plain small soft light-brown toy with two small dot eyes, no clothing, no bow, no ribbon, not resembling any franchise bear, the teddy never moves by itself, slow gentle in-place rocking only, no jumping, no falling, no spinning, exactly one Croco and one teddy bear, no extra limbs or extra fingers, no wide-open mouth, no red nose, nothing on Croco's snout, the yellow star stays on the front pocket."
X2="Soft blanket only, no pillow fight, no crying, no tears, no angry faces, no scary dark room, Pebble never goes inside the shell, no red nose, nothing on Croco's snout, the yellow star stays on the front pocket, exactly one Croco and one Pebble, no extra limbs or extra fingers, no wide-open mouth."
R="cozy sunny pastel playroom with a soft round rug and soft pastel cushions"
B="cozy pastel bedroom in the soft warm evening glow of a small round night-light"
EP={"20261126-01":[(4,False,X1,f"in a {R}, a close-up of Croco's face and shoulders from the very first frame as he gently hugs a small soft light-brown teddy bear to his chest with both arms, Croco looks down at the teddy with big sparkly eyes and a gentle closed-mouth smile, vertical 9:16, calm steady close-up, slow gentle motion."),
 (4,False,X1,f"in the {R}, Croco stands on the soft round rug facing the camera from the front, holding the small soft light-brown teddy bear in both arms, and slowly rocks his body gently from side to side in place like rocking a baby, with a gentle closed-mouth smile, vertical 9:16, steady frontal medium shot, slow gentle motion."),
 (4,False,X1,f"in the {R}, Croco faces the camera from the front the whole time, his round face and big sparkly eyes seen from the front, he slowly rocks the small soft light-brown teddy bear from side to side one more time, then stops and gives the teddy a soft gentle hug with a gentle closed-mouth smile, vertical 9:16, steady frontal medium shot, slow gentle motion.")],
 "20261126-02":[(4,True,X2,f"in a {B}, a close-up of Croco's face and shoulders from the very first frame as he holds a soft folded sky-blue blanket in both hands, Pebble sits on a small round cushion bed beside him looking at the blanket, Croco looks at Pebble with a gentle closed-mouth smile, vertical 9:16, steady close-up, slow gentle motion."),
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
