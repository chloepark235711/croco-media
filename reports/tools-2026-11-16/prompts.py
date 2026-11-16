import json,sys
LOCK = "Croco, a super cute chubby mint-green baby crocodile with a big rounded head in baby proportions, a short rounded snout, peach-cream belly, extra-chubby rosy cheeks, big sparkly round chocolate-brown eyes with soft white highlights, a sweet happy smile showing two tiny rounded ivory baby teeth on the upper jaw, short arms and legs, chunky tail, wearing orange dungaree overalls with two small wooden buttons and a yellow star embroidered on the front pocket. Soft 3D animated preschool style, gentle pastel lighting, friendly and calm."
MOUTH = "Mouth detail: sweet smile with exactly two tiny rounded ivory baby teeth on the upper jaw, small, blunt and soft-looking, no other teeth."
PEBBLE = "Pebble, a small round lavender baby turtle with a cream-colored belly, a smooth lavender shell with exactly three soft sky-blue round spots, big round gray eyes, short stubby legs, a gentle closed-mouth smile, and no clothing or accessories. Soft 3D animated preschool style, gentle pastel lighting, friendly and calm."
NEG = "no scary expressions, no sharp teeth, no pointed fangs, no rows of teeth, no more than two teeth, no wide-open jaws, no realistic reptile skin, no extra limbs, no text, no letters, no other franchises' characters, no flashing lights, no twinkling flashes, no fast camera moves, no hats or extra clothing, do not change the pocket star design, Pebble has no teeth."
XP1 = "No clothing or accessories on Pebble, no sharp beak, do not change Pebble's lavender color or the three sky-blue shell spots, no resemblance to other franchises' turtle characters. Soft ball only, no throwing, no grabbing, no crying, no tears, no angry faces."
XP2 = "No realistic cow, no horns, no bell, no clothing on the cow, no other franchises' cow characters, the cow does not talk, no mud."
XP3 = "Slow, gentle, in-place moves only, no jumping, no falling, exactly one Croco, no extra limbs or extra fingers."
SC = {
"20261116-01":[
 (4,True,"in a cozy pastel playroom, a close-up of Croco's face and shoulders from the very first frame as he holds a big soft red ball, Pebble sits next to him on a soft rug looking at the ball, Croco looks at Pebble with a sweet smile, vertical 9:16, steady close-up, slow gentle motion.",XP1),
 (4,True,"on the soft rug in the cozy pastel playroom, Croco gently rolls the big soft red ball along the rug to Pebble, Pebble stops it with his short stubby legs and gives a kind smile, vertical 9:16, steady medium shot, slow gentle motion.",XP1),
 (4,True,"Pebble slowly rolls the big soft red ball back to Croco, Croco catches it, then both look at the camera with happy smiles, cozy pastel playroom, vertical 9:16, steady medium shot, slow gentle motion.",XP1)],
"20261117-01":[
 (4,False,"in a sunny pastel farm meadow with a low wooden fence, a close-up of Croco's face and shoulders from the very first frame as he leans on the fence and cups one hand by his ear with curious big sparkly eyes, a soft brown-and-white ear peeks out from behind a round haystack, vertical 9:16, calm steady close-up, slow gentle motion.",XP2),
 (5,False,"a small round friendly cartoon cow with soft brown and white patches slowly walks out from behind the round haystack onto the grass, Croco claps his hands with a sweet smile, sunny pastel farm meadow, vertical 9:16, steady medium shot, slow gentle motion.",XP2),
 (5,False,"Croco stands beside the small friendly cartoon cow and gives a little wave, the cow gently nods, then Croco turns to the camera with a sweet smile, sunny pastel farm meadow, vertical 9:16, steady medium shot.",XP2)],
"20261117-02":[
 (4,False,"in a sunny pastel garden, a close-up of Croco's face and shoulders from the very first frame as he gently pats the top of his head with one hand and smiles a sweet smile, vertical 9:16, calm steady close-up, slow gentle motion.",XP3),
 (4,False,"in the sunny pastel garden, Croco gently touches the tip of his short snout with one finger and smiles a sweet smile, vertical 9:16, steady medium close-up, slow gentle motion.",XP3),
 (4,False,"in the sunny pastel garden, Croco sits on soft green grass and slowly wiggles his little toes, then smiles a sweet smile at the camera, vertical 9:16, steady full-body medium shot, slow gentle motion.",XP3)]}
def prompt(ep,i):
    d,peb,s,x=SC[ep][i]
    return LOCK+(" "+PEBBLE if peb else "")+" Scene: "+s+" "+MOUTH+"\nNegative: "+NEG+" "+x
def body(ep,i,refs):
    return {"prompt":prompt(ep,i),"image_urls":refs,"duration":SC[ep][i][0],"resolution":"720p","aspect_ratio":"9:16"}
if __name__=="__main__":
    print(json.dumps(body(sys.argv[1],int(sys.argv[2])-1,sys.argv[3:])))
