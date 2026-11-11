import json
LOCK = "Croco, a chubby mint-green baby crocodile with a rounded head, short snout, peach-cream belly, rosy cheeks, big chocolate-brown eyes, a gentle closed-mouth smile with no visible teeth, short arms and legs, chunky tail, wearing orange dungaree overalls with two small wooden buttons and a yellow star embroidered on the front pocket. Soft 3D animated preschool style, gentle pastel lighting, friendly and calm."
NEG = "no scary expressions, no sharp teeth, no rows of teeth, no teeth, no open mouth with teeth, no realistic reptile skin, no extra limbs, no text, no letters, no other franchises' characters, no flashing lights, no twinkling flashes, no fast camera moves, no hats or extra clothing, do not change the pocket star design."
SC = {
"20261110-01": [
("in a bright pastel playroom with a wide soft play mat, Croco stands in the middle of the mat with his face clearly visible from the first frame, bends his knees and does one small slow hop in place, landing softly, vertical 9:16, steady full-body shot, slow gentle motion.","No fast movements, no jumping on furniture, no extra arms or legs, stays on the soft mat."),
("on the same wide soft play mat in the bright pastel playroom, Croco slowly waddles side to side in place with his short arms out and his chunky tail swaying gently, vertical 9:16, steady full-body shot, slow gentle motion.","No fast movements, no extra arms or legs, no distorted tail, stays on the soft mat."),
("on the same wide soft play mat in the bright pastel playroom, Croco does two slow gentle stomps in place, then stops, faces the camera and gives a small happy wave, vertical 9:16, steady full-body shot, slow gentle motion.","No fast movements, no shaking camera, no extra arms or legs, stays on the soft mat."),
],
"20261110-02": [
("in a calm pastel playroom, Croco stands on a soft rug holding a big soft yellow star pillow with both hands, his face clearly visible from the first frame, and slowly lifts the pillow up high above his head, looking up at it, vertical 9:16, steady medium shot, slow gentle motion.","Soft pillow only, no throwing, no fast movements."),
("in the calm pastel playroom, Croco slowly lowers the big soft yellow star pillow down low to the soft rug and pats it gently, then lifts it up high again and smiles at the camera, vertical 9:16, steady medium shot, slow gentle motion.","Soft pillow only, no throwing, no fast movements."),
]}
def prompt(ep,i):
    s,x=SC[ep][i]
    return LOCK+" Scene: "+s+" Mouth detail: closed-mouth smile, no teeth visible at any time.\nNegative: "+NEG+" "+x
def body(ep,i):
    return {"prompt":prompt(ep,i),"duration":5,"resolution":"720p","aspect_ratio":"9:16"}
if __name__=="__main__":
    import sys
    print(json.dumps(body(sys.argv[1],int(sys.argv[2])-1)))
