import json,sys
LOCK="Croco, a super cute chubby mint-green baby crocodile with a big rounded head in baby proportions, a short rounded snout, peach-cream belly, extra-chubby rosy cheeks, big sparkly round chocolate-brown eyes with soft white highlights, a sweet happy smile showing two tiny rounded ivory baby teeth on the upper jaw, short arms and legs, chunky tail, wearing orange dungaree overalls with two small wooden buttons and a yellow star embroidered on the front pocket. Soft 3D animated preschool style, gentle pastel lighting, friendly and calm."
MOUTH="Mouth detail: sweet smile with exactly two tiny rounded ivory baby teeth on the upper jaw, small, blunt and soft-looking, no other teeth."
PEBBLE="Pebble, a small round lavender baby turtle with a cream-colored belly, a smooth lavender shell with exactly three soft sky-blue round spots, big round gray eyes, short stubby legs, a gentle closed-mouth smile, and no clothing or accessories. Soft 3D animated preschool style, gentle pastel lighting, friendly and calm."
NEG="no scary expressions, no sharp teeth, no pointed fangs, no rows of teeth, no more than two teeth, no wide-open jaws, no realistic reptile skin, no extra limbs, no text, no letters, no other franchises' characters, no flashing lights, no twinkling flashes, no fast camera moves, no hats or extra clothing, do not change the pocket star design, Pebble has no teeth."
def build(scene,pebble,extra): return LOCK+(" "+PEBBLE if pebble else "")+" Scene: "+scene+" "+MOUTH+"\nNegative: "+NEG+" "+extra
COMMON="no red nose, nothing on Croco's snout, the yellow star stays on the front pocket, no extra limbs or extra fingers, no lower teeth, no waving."
X1="The teddy bear is a plain small soft light-brown toy with two small dot eyes, no clothing, no bow, no ribbon, not resembling any franchise bear, the teddy never moves by itself, slow gentle in-place rocking only, no jumping, no falling, no spinning, exactly one Croco and one teddy bear, "+COMMON
X2="Soft blanket only, no pillow fight, no crying, no tears, no angry faces, no scary dark room, Pebble never goes inside the shell, exactly one Croco and one Pebble, "+COMMON
X3="The bird is a small round sky-blue cartoon bird, not resembling any franchise bird, it stays on the flower bush, Croco never flies and never leaves the ground, no jumping, no falling, exactly one Croco and one bird, "+COMMON
R="cozy sunny pastel playroom with a soft round rug and soft pastel cushions"
B="cozy pastel bedroom in the soft warm evening glow of a small round night-light"
G="sunny pastel garden with soft green grass and round flower bushes"
EP={"20261126-01":[(4,False,X1,f"in a {R}, a close-up of Croco's face and shoulders from the very first frame as he gently hugs a small soft light-brown teddy bear to his chest with both arms, Croco looks down at the teddy with big sparkly eyes and a sweet smile, vertical 9:16, calm steady close-up, slow gentle motion."),
 (4,False,X1,f"in the {R}, Croco stands on the soft round rug facing the camera from the front, holding the small soft light-brown teddy bear in both arms, and slowly rocks his body gently from side to side in place like rocking a baby, with a sweet smile, vertical 9:16, steady frontal medium shot, slow gentle motion."),
 (4,False,X1,f"in the {R}, Croco faces the camera from the front the whole time, his round face and big sparkly eyes seen from the front, he slowly rocks the small soft light-brown teddy bear from side to side one more time, then stops and gives the teddy a soft gentle hug with a sweet smile, vertical 9:16, steady frontal medium shot, slow gentle motion.")],
 "20261126-02":[None,
 (4,True,X2,f"in the {B}, Croco gently spreads the soft sky-blue blanket over Pebble on the small round cushion bed and softly tucks the edges, Pebble's head peeks out and Pebble gives a kind closed-mouth smile, Croco has a sweet smile, vertical 9:16, steady medium shot, slow gentle motion."),
 (4,True,X2,f"in the {B}, Pebble rests snugly under the soft sky-blue blanket on the small round cushion bed and slowly closes its eyes with a peaceful closed-mouth smile, Croco sits beside the bed facing the camera from the front with a sweet smile, vertical 9:16, steady frontal medium shot, slow gentle motion.")],
 "20261128-01":[None,
 (4,False,X3,f"in the {G}, Croco stands on the soft grass facing the camera from the front and slowly flaps his short arms up and down at his sides like little wings, the small round sky-blue bird on the flower bush beside him flaps its wings too, Croco has a sweet smile, vertical 9:16, steady frontal medium shot, slow gentle motion."),
 (4,False,X3,f"in the {G}, Croco faces the camera from the front the whole time, he slowly lowers his short arms down to his sides and stands still with a sweet smile, the small round sky-blue bird sits calmly on the flower bush beside him, vertical 9:16, steady frontal medium shot, slow gentle motion.")]}
if __name__=="__main__":
    if sys.argv[1]=="plan": print(json.dumps({e:[None if s is None else build(s[3],s[1],s[2]) for s in EP[e]] for e in EP},indent=1))
    else:
        d,pb,x,s=EP[sys.argv[1]][int(sys.argv[2])-1]
        print(json.dumps({"prompt":build(s,pb,x),"image_urls":sys.argv[3:],"duration":d,"resolution":"720p","aspect_ratio":"9:16"}))
