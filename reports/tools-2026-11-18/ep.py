import json,sys
sys.path.insert(0,"/tmp/claude-0/-home-user-croco-media/e987ff4a-4e08-528c-b271-fb23612818b3/scratchpad/main-wt")
from croco import brand
X1="Slow, gentle, in-place moves only, no jumping, no falling, exactly one Croco, no extra limbs or extra fingers, no wide-open mouth."
X2="Soft whole apples only, no biting, no eating, no grabbing, no throwing, no crying, no tears, no angry faces, no wide-open mouth."
G="sunny pastel garden with soft green grass and round flowers"
EP={"20261118-01":[(5,False,X1,f"in a {G}, a close-up of Croco's face and shoulders from the very first frame as he slowly and gently pats the top of his round head with one hand, big sparkly curious eyes and a gentle closed-mouth smile, vertical 9:16, calm steady close-up, slow gentle motion."),
 (5,False,X1,f"in the {G}, Croco slowly lifts one finger and gently touches the tip of his short rounded snout, then gives a gentle closed-mouth smile, vertical 9:16, steady medium close-up, slow gentle motion."),
 (5,False,X1,f"Croco sits on the soft grass in the {G} with his short legs stretched out in front of him and slowly wiggles his little toes, then looks at the camera with a gentle closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion.")],
 "20261118-02":[(4,True,X2,"on a soft checkered picnic blanket in a sunny pastel park, a close-up of Croco's face and shoulders from the very first frame as he holds two shiny soft red apples, one in each hand, Pebble sits next to him on the blanket looking at the apples, Croco looks at Pebble with a gentle closed-mouth smile, vertical 9:16, steady close-up, slow gentle motion."),
 (4,True,X2,"on the soft checkered picnic blanket in the sunny pastel park, Croco slowly and kindly gives one shiny red apple to Pebble and keeps one for himself, Pebble gently holds the apple and gives a kind closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion."),
 (4,True,X2,"Croco and Pebble sit side by side on the soft checkered picnic blanket, each gently holding one shiny red apple, they look at each other and then at the camera with gentle closed-mouth smiles, sunny pastel park, vertical 9:16, steady medium shot, slow gentle motion.")]}
def P(e): return [{"seconds":d,"prompt":brand.scene_prompt(s,pebble=pb,extra_negative=x)} for d,pb,x,s in EP[e]]
if __name__=="__main__":
    if sys.argv[1]=="plan": print(json.dumps({e:P(e) for e in EP}))
    else:
        p=P(sys.argv[1])[int(sys.argv[2])-1]
        print(json.dumps({"prompt":p["prompt"],"image_urls":sys.argv[3:],"duration":p["seconds"],"resolution":"720p","aspect_ratio":"9:16"}))
