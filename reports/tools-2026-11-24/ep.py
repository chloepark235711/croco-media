import json,sys
sys.path.insert(0,"/home/user/croco-media")
from croco import brand
X1="No tall horse, no long thin legs, no dark mane, no realistic horse, no saddle, no reins, no riding, no rearing, no galloping, no clothing on the pony, no unicorn horn, no wings, no other franchises' pony or horse characters, the pony does not talk, exactly one Croco and one pony, no extra limbs or extra fingers, no wide-open mouth."
X2="No red nose, no clown nose, nothing on Croco's face or snout, Croco's snout is mint-green. Mouth stays closed the whole time. Slow, gentle, in-place moves only, no jumping, no flying, Croco's feet stay on the grass, no falling, no wings or feathers on Croco, exactly one Croco and one small bird, no extra limbs or extra fingers, no other franchises' bird characters, no wide-open mouth."
F="sunny pastel farm meadow with a low wooden fence and a round golden haystack"
G="sunny pastel garden with soft green grass and round flower bushes"
EP={"20261124-01":[(4,False,X1,f"in a {F}, a close-up of Croco's face and shoulders from the very first frame as he leans on the low wooden fence and cups one hand by his ear with curious big sparkly eyes and a gentle closed-mouth smile, a soft cream-colored pony mane and one small rounded caramel ear peek out from behind the round haystack, vertical 9:16, calm steady close-up, slow gentle motion."),
 (4,False,X1,f"in the {F}, a small round friendly cartoon pony with a soft caramel coat, a fluffy cream mane and big gentle eyes slowly walks out from behind the round haystack onto the clean grass, Croco faces the camera and gently claps his hands with a gentle closed-mouth smile, vertical 9:16, steady frontal medium shot, slow gentle motion."),
 (4,False,X1,f"in the {F}, Croco faces the camera from the front the whole time, his round face and big sparkly eyes seen from the front, he stands beside the same small round chubby cartoon pony with short stubby legs, a soft caramel coat and a fluffy cream mane, about as tall as Croco, fully visible and facing the camera too, Croco gives a little wave with a gentle closed-mouth smile and the pony gently nods its head, vertical 9:16, steady frontal medium shot, slow gentle motion.")],
 "20261124-02":[(4,False,X2,f"in a {G}, a close-up of Croco's face and shoulders from the very first frame, a small round sky-blue cartoon bird sits on a round flower bush right beside him and slowly flaps its little wings, Croco watches the bird with curious big sparkly eyes and a gentle closed-mouth smile, vertical 9:16, calm steady close-up, slow gentle motion."),
 (4,False,X2,f"in the {G}, Croco stands on the soft grass facing the camera from the front and slowly flaps his short arms up and down at his sides like little wings, the small round sky-blue bird on the flower bush beside him flaps its wings too, Croco has a gentle closed-mouth smile, vertical 9:16, steady frontal medium shot, slow gentle motion."),
 (4,False,X2,f"in the {G}, Croco faces the camera from the front the whole time, he slowly lowers his short arms to his sides and stands still, then gives a little wave to the camera with a gentle closed-mouth smile, the small round sky-blue bird sits calmly on the flower bush beside him, vertical 9:16, steady frontal medium shot, slow gentle motion.")]}
def P(e): return [{"seconds":d,"prompt":brand.scene_prompt(s,pebble=pb,extra_negative=x)} for d,pb,x,s in EP[e]]
if __name__=="__main__":
    if sys.argv[1]=="plan": print(json.dumps({e:P(e) for e in EP},indent=1))
    else:
        p=P(sys.argv[1])[int(sys.argv[2])-1]
        print(json.dumps({"prompt":p["prompt"],"image_urls":sys.argv[3:],"duration":p["seconds"],"resolution":"720p","aspect_ratio":"9:16"}))
