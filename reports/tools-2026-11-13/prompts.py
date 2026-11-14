import json,sys
LOCK = "Croco, a chubby mint-green baby crocodile with a rounded head, short snout, peach-cream belly, rosy cheeks, big chocolate-brown eyes, a gentle closed-mouth smile with no visible teeth, short arms and legs, chunky tail, wearing orange dungaree overalls with two small wooden buttons and a yellow star embroidered on the front pocket. Soft 3D animated preschool style, gentle pastel lighting, friendly and calm."
NEG = "no scary expressions, no sharp teeth, no rows of teeth, no teeth, no open mouth with teeth, no realistic reptile skin, no extra limbs, no text, no letters, no other franchises' characters, no flashing lights, no twinkling flashes, no fast camera moves, no hats or extra clothing, do not change the pocket star design."
X3 = "No letters, no numbers, no star shapes, no ribbons or strings, shapes must be clearly a circle, a square and a triangle."
X4 = "Exactly five stars in the final shot, no flashing or twinkling, no yawning, no sleepy eyes, no moon, no shooting stars, no dark night sky."
SC = {
"20261114-01":[
 (5,"in a cozy pastel playroom, a close-up of Croco's face and shoulders from the very first frame as he sits on a soft rug right beside a small plain pastel box with a lid, Croco slowly lifts the lid with both hands and a big soft round red circle cushion rises into view from the box, Croco looks at it with curious round eyes, vertical 9:16, calm steady close-up, slow gentle motion.",X3),
 (5,"in the cozy pastel playroom, Croco sits on the soft rug beside the open plain pastel box and the big soft round red circle cushion, he slowly takes a big soft blue square block with four equal straight sides out of the box and holds it up with both hands, happy round eyes, vertical 9:16, steady medium shot, slow gentle motion.",X3),
 (5,"in the cozy pastel playroom, Croco gently places a big soft green triangle block with three straight sides on the soft rug next to a big soft round red circle cushion and a big soft blue square block, all three shapes side by side in a neat row, then Croco looks at the camera with a happy closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion.",X3)],
"20261114-02":[
 (4,"in a bright pastel garden in the early evening with a soft peach and lilac sky, a close-up of Croco's face and shoulders from the very first frame as he looks up with curious round eyes at one single soft glowing yellow star in the sky, Croco slowly raises one hand and points at the star, vertical 9:16, calm steady close-up, slow gentle motion, steady soft light.",X4),
 (5,"in the bright pastel garden in the early evening with a soft peach and lilac sky, Croco stands on the soft grass and points up as soft glowing yellow stars slowly fade in one at a time in a neat horizontal row in the sky, Croco gently follows each new star with his finger, vertical 9:16, steady medium shot, slow gentle motion, steady soft light.",X4),
 (5,"in the bright pastel garden in the early evening with a soft peach and lilac sky, exactly five soft glowing yellow stars rest in a neat horizontal row in the sky above Croco, Croco stands on the soft grass and looks up at the five stars, then turns to the camera with a happy closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion, steady soft light.",X4)]}
def prompt(ep,i):
    d,s,x=SC[ep][i]
    return LOCK+" Scene: "+s+" Mouth detail: closed-mouth smile, no teeth visible at any time.\nNegative: "+NEG+" "+x
def body(ep,i,refs):
    return {"prompt":prompt(ep,i),"image_urls":refs,"duration":SC[ep][i][0],"resolution":"720p","aspect_ratio":"9:16"}
if __name__=="__main__":
    print(json.dumps(body(sys.argv[1],int(sys.argv[2])-1,sys.argv[3:])))
