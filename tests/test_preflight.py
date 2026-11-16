import datetime, os, tempfile, unittest
from decimal import Decimal
from zoneinfo import ZoneInfo

from croco import brand, preflight as pf

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TZ = ZoneInfo("America/Denver")

# v3 teeth LOCK that failed 4/4 on 2026-11-16 (kept verbatim as a regression sample)
V3_TEETH_LOCK = ("Croco, a super cute chubby mint-green baby crocodile with a big rounded head in baby "
                 "proportions, a short rounded snout, peach-cream belly, extra-chubby rosy cheeks, big "
                 "sparkly round chocolate-brown eyes with soft white highlights, a sweet happy smile "
                 "showing two tiny rounded ivory baby teeth on the upper jaw, short arms and legs, chunky "
                 "tail, wearing orange dungaree overalls with two small wooden buttons and a yellow star "
                 "embroidered on the front pocket.")


def good(scene="Croco sits on a soft rug with a gentle closed-mouth smile, vertical 9:16.", pebble=False):
    return brand.scene_prompt(scene, pebble=pebble)


class Refs(unittest.TestCase):
    def test_face2_banned(self):
        e = pf.check_references(["reference/croco-face-2.png", "reference/croco-face.png"], "/nonexistent")
        self.assertTrue(any("banned reference reference/croco-face-2.png" in x for x in e))

    def test_unknown_and_empty(self):
        self.assertTrue(pf.check_references([], "."))
        self.assertTrue(pf.check_references(["reference/x.png"], "."))

    def test_sha_mismatch_and_ok(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "reference"))
        with open(os.path.join(d, "reference/croco-face.png"), "wb") as fh:
            fh.write(b"fake")
        self.assertIn("sha256 mismatch", " ".join(pf.check_references(["reference/croco-face.png"], d)))
        real = os.environ.get("CROCO_REF_ROOT")
        if real:
            self.assertEqual(pf.check_references(["reference/croco-face.png"], real), [])


class Prompts(unittest.TestCase):
    def test_brand_prompt_passes(self):
        self.assertEqual(pf.check_prompt(good()), [])
        self.assertEqual(pf.check_prompt(good("Pebble and Croco sit together, vertical 9:16.", True)), [])

    def test_teeth_lock_rejected(self):
        p = V3_TEETH_LOCK + " Scene: Croco smiles. Mouth detail: sweet smile with exactly two tiny teeth.\nNegative: no sharp teeth"
        e = " ".join(pf.check_prompt(p))
        self.assertIn("closed-mouth Mouth detail line missing", e)
        self.assertIn("teeth", e)

    def test_open_mouth_actions_rejected(self):
        for s in ("Croco laughs at the ball", "both look at the camera with happy smiles",
                  "Croco opens his mouth wide", "Croco sings a song", "the cow says hello",
                  "Croco gives a big smile"):
            self.assertTrue(pf.check_prompt(good(s)), s)

    def test_closed_mouth_smiles_ok(self):
        self.assertEqual(pf.check_prompt(good("both look at the camera with gentle closed-mouth smiles")), [])

    def test_outfit_part_missing(self):
        p = good().replace("yellow star embroidered on the front pocket", "red heart")
        self.assertTrue(any("yellow star" in x for x in pf.check_prompt(p)))

    def test_pebble_lock_required(self):
        p = brand.scene_prompt("Pebble sits next to Croco, vertical 9:16.", pebble=False)
        self.assertTrue(any("Pebble lock" in x for x in pf.check_prompt(p)))


class Budget(unittest.TestCase):
    def ep(self, secs, i="e"):
        return {"id": i, "title": i, "scenes": [{"seconds": s, "prompt": ""} for s in secs]}

    def test_cost(self):
        base, mx = pf.episode_cost(self.ep([4, 4, 4]), Decimal("0.1257"), 2)
        self.assertEqual((base, mx), (Decimal("1.5084"), Decimal("2.5140")))

    def test_cap(self):
        spent = Decimal("2.0112")
        self.assertEqual(pf.check_budget(spent, [self.ep([4, 4, 4])], Decimal("0.1257"), 2)[0], [])
        self.assertTrue(pf.check_budget(spent, [self.ep([4, 4, 4])], Decimal("0.1257"), 3)[0])
        self.assertTrue(pf.check_budget(spent, [self.ep([4, 4, 4]), self.ep([4, 5, 5])],
                                        Decimal("0.1257"), 0)[0])

    def test_unknown_price_blocks(self):
        self.assertTrue(pf.check_budget(Decimal(0), [self.ep([4])], None, 0)[0])

    def test_ledger_total(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
        f.write(",".join(pf.LEDGER_FIELDS) + "\n")
        f.write("2026-11-16,a,1,m,4,720p,r1,completed,0.5028\n")
        f.write("2026-11-16,a,2,m,4,720p,r2,not_charged,0.5028\n")
        f.write("2026-11-15,a,1,m,4,720p,r3,completed,0.5028\n")
        f.close()
        self.assertEqual(pf.ledger_total(f.name, "2026-11-16"), Decimal("0.5028"))


class DupSlots(unittest.TestCase):
    def test_dup(self):
        e = pf.check_duplicates([{"id": "a", "title": "T1", "topic": "cow"}], ["t1"], ["Cow"])
        self.assertEqual(len(e), 2)

    def test_slots(self):
        now = datetime.datetime(2026, 11, 16, 11, 40, tzinfo=TZ)
        mk = lambda s: [{"id": "a", "slot": s}]
        self.assertTrue(pf.check_slots(mk("2026-11-16T12:00"), [], now))          # < 60 min
        self.assertEqual(pf.check_slots(mk("2026-11-16T17:00"), [], now), [])
        self.assertTrue(pf.check_slots(mk("2026-11-16T17:00"), ["2026-11-16T17:00"], now))
        self.assertTrue(pf.check_slots(mk("2026-11-16T15:00"), [], now))


if __name__ == "__main__":
    unittest.main()
