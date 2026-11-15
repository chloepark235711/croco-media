import json,sys
LOCK = "Croco, a chubby mint-green baby crocodile with a rounded head, short snout, peach-cream belly, rosy cheeks, big chocolate-brown eyes, a gentle closed-mouth smile with no visible teeth, short arms and legs, chunky tail, wearing orange dungaree overalls with two small wooden buttons and a yellow star embroidered on the front pocket. Soft 3D animated preschool style, gentle pastel lighting, friendly and calm."
NEG = "no scary expressions, no sharp teeth, no rows of teeth, no teeth, no open mouth with teeth, no realistic reptile skin, no extra limbs, no text, no letters, no other franchises' characters, no flashing lights, no twinkling flashes, no fast camera moves, no hats or extra clothing, do not change the pocket star design."
X3 = "No letters, no numbers, no star shapes, no ribbons or strings, shapes must be clearly a circle, a square and a triangle. No studs, no bumps, no building-brick blocks."
X5 = "No jumping, no falling, no climbing, no other characters, no props, no water, Croco stays on flat soft grass."
SC = {
"20261115-01":[
 (5,"in a cozy pastel playroom, a close-up of Croco's face and shoulders from the very first frame as he sits on a soft rug right beside a small plain pastel box with a lid, Croco slowly lifts the lid with both hands and a big soft round red circle cushion rises into view from the box, Croco looks at it with curious round eyes, vertical 9:16, calm steady close-up, slow gentle motion.",X3),
 (5,"in the cozy pastel playroom, Croco sits on the soft rug beside the open plain pastel box and the big soft round red circle cushion, he slowly takes a big smooth soft blue square cushion with four equal straight sides and a flat plain surface out of the box and holds it up with both hands, happy round eyes, vertical 9:16, steady medium shot, slow gentle motion.",X3),
 (5,"in the cozy pastel playroom, Croco gently places a big smooth soft green triangle cushion with three straight sides on the soft rug next to a big soft round red circle cushion and a big smooth soft blue square cushion, all three shapes side by side in a neat row, then Croco looks at the camera with a happy closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion.",X3)],
"20261115-01-r3":[
 (5,"in the cozy pastel playroom, Croco sits on the soft rug and holds up with both hands a big flat soft green triangle cushion with exactly three straight sides and three corners, one corner pointing straight up, like a big green triangle sign, next to a big soft round red circle cushion and a big smooth soft blue square cushion lying on the rug, then Croco lowers the triangle beside them and looks at the camera with a happy closed-mouth smile, vertical 9:16, steady medium shot, slow gentle motion.",X3)],
"20261115-02":[
 (4,"in a sunny pastel meadow with soft green grass, a close-up of Croco's face and shoulders from the very first frame as he looks at the camera with bright round eyes, then he slowly raises both short arms up high above his head, the camera gently and slowly pulls back, vertical 9:16, calm steady close-up, slow gentle motion.",X5),
 (4,"in the sunny pastel meadow, Croco stands on the soft green grass and slowly stretches up tall on his tiptoes with both arms high above his head, making himself as big as he can, happy round eyes, vertical 9:16, steady full-body medium shot, slow gentle motion.",X5),
 (5,"in the sunny pastel meadow, Croco slowly crouches down and curls up into a small round ball on the soft green grass, hugging his knees, then he gently lifts his head and looks at the camera with a happy closed-mouth smile, vertical 9:16, steady full-body medium shot, slow gentle motion.",X5)]}
def prompt(ep,i):
    d,s,x=SC[ep][i]
    return LOCK+" Scene: "+s+" Mouth detail: closed-mouth smile, no teeth visible at any time.\nNegative: "+NEG+" "+x
def body(ep,i,refs):
    return {"prompt":prompt(ep,i),"image_urls":refs,"duration":SC[ep][i][0],"resolution":"720p","aspect_ratio":"9:16"}
if __name__=="__main__":
    print(json.dumps(body(sys.argv[1],int(sys.argv[2])-1,sys.argv[3:])))
