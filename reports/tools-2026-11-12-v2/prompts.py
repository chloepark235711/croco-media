import json,sys
LOCK = "Croco, a chubby mint-green baby crocodile with a rounded head, short snout, peach-cream belly, rosy cheeks, big chocolate-brown eyes, a gentle closed-mouth smile with no visible teeth, short arms and legs, chunky tail, wearing orange dungaree overalls with two small wooden buttons and a yellow star embroidered on the front pocket. Soft 3D animated preschool style, gentle pastel lighting, friendly and calm."
NEG = "no scary expressions, no sharp teeth, no rows of teeth, no teeth, no open mouth with teeth, no realistic reptile skin, no extra limbs, no text, no letters, no other franchises' characters, no flashing lights, no twinkling flashes, no fast camera moves, no hats or extra clothing, do not change the pocket star design."
X1 = "No water, no pond, no realistic bird, no clothing or accessories on the duck, no other franchises' duck characters, the duck does not talk."
SC = {"20261113-01":[
 (4,"in a sunny pastel garden, a close-up of Croco's face and shoulders from the very first frame as he kneels on soft grass right beside a round flower bush, the leaves gently wiggle and a tiny fluffy white tail peeks out between the leaves, Croco leans in with curious round eyes, vertical 9:16, calm steady close-up, slow gentle motion.",X1),
 (5,"a small fluffy white cartoon duck with a soft orange bill slowly waddles out from behind the round flower bush onto the grass, Croco watches with happy round eyes and clasps his hands, sunny pastel garden, vertical 9:16, steady medium shot, slow gentle motion.",X1),
 (5,"Croco sits on the grass and gives a little wave to the small fluffy white cartoon duck, the duck gently tilts its head, then Croco turns to the camera with a happy smile, sunny pastel garden with a round flower bush, vertical 9:16, steady medium shot.",X1)]}
def prompt(ep,i):
    d,s,x=SC[ep][i]
    return LOCK+" Scene: "+s+" Mouth detail: closed-mouth smile, no teeth visible at any time.\nNegative: "+NEG+" "+x
def body(ep,i,ref):
    return {"prompt":prompt(ep,i),"image_urls":[ref],"duration":SC[ep][i][0],"resolution":"720p","aspect_ratio":"9:16"}
if __name__=="__main__":
    print(json.dumps(body(sys.argv[1],int(sys.argv[2])-1,sys.argv[3])))
