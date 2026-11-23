import json,sys
sys.path.insert(0,"/home/user/croco-media")
from croco import brand
X1="No realistic pig, no mud, no clothing on the piglet, no other franchises' pig characters, the piglet does not talk, no snout close-up of the piglet, exactly one Croco, no extra limbs or extra fingers, no wide-open mouth."
X2="No more than three spots on Pebble's shell, no polka dots. No crying, no tears, no angry faces, no grabbing, no squeezing, exactly one Croco and one Pebble, no extra limbs, no wide-open mouth."
F="sunny pastel farm meadow with a low wooden fence and a round golden haystack"
R="cozy pastel playroom with a soft rug"
EP={"20261123-01":[(4,False,X1,f"in a {F}, a close-up of Croco's face and shoulders from the very first frame as he leans on the low wooden fence and cups one hand by his ear with curious big sparkly eyes and a gentle closed-mouth smile, a small curly pink piglet tail peeks out from behind the round haystack, vertical 9:16, calm steady close-up, slow gentle motion."),
 (4,False,X1,f"in the {F}, a small round friendly cartoon piglet with soft pink skin, small floppy ears and a curly tail slowly trots out from behind the round haystack onto the clean grass, Croco faces the camera and gently claps his hands with a gentle closed-mouth smile, vertical 9:16, steady frontal medium shot, slow gentle motion."),
 (4,False,X1,f"in the {F}, Croco faces the camera from the front the whole time, his round face and big sparkly eyes seen from the front, he stands beside a small round pink cartoon piglet that is fully visible and faces the camera too, Croco gives a little wave with a gentle closed-mouth smile and the piglet gently wiggles its curly tail, vertical 9:16, steady frontal medium shot, slow gentle motion.")],
 "20261123-02":[(4,True,X2,f"in a {R}, a close-up of Croco's face and shoulders from the very first frame, Croco looks with kind caring big sparkly eyes at Pebble who sits beside him on the soft rug looking a little sad with slightly droopy eyes and a small closed-mouth frown, no tears, vertical 9:16, steady close-up, slow gentle motion."),
 (4,True,X2,f"on the soft rug in the {R}, Croco slowly leans over and gives Pebble a soft gentle hug with his short arms, Pebble's face starts to brighten into a gentle closed-mouth smile, Croco has a kind closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion."),
 (4,True,X2,f"on the soft rug in the {R}, Croco and Pebble sit side by side, both facing the camera with gentle closed-mouth smiles, Croco gives a little wave, Pebble's smooth lavender shell has only three large sky-blue round spots, vertical 9:16, steady frontal medium shot, slow gentle motion.")]}
def P(e): return [{"seconds":d,"prompt":brand.scene_prompt(s,pebble=pb,extra_negative=x)} for d,pb,x,s in EP[e]]
if __name__=="__main__":
    if sys.argv[1]=="plan": print(json.dumps({e:P(e) for e in EP},indent=1))
    else:
        p=P(sys.argv[1])[int(sys.argv[2])-1]
        print(json.dumps({"prompt":p["prompt"],"image_urls":sys.argv[3:],"duration":p["seconds"],"resolution":"720p","aspect_ratio":"9:16"}))
