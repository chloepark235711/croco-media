import json, os, shutil, subprocess, tempfile, threading, unittest
from decimal import Decimal

from croco import budget, episodes, generate, higgsfield as hf
from croco.gitstore import GitStore

DAY = "2026-11-05"


def sh(*a, cwd=None):
    subprocess.run(a, cwd=cwd, check=True, capture_output=True)


def make_remote(base, name, files, branches=("main",)):
    bare = os.path.join(base, name + ".git")
    seed = os.path.join(base, name + "-seed")
    sh("git", "init", "-q", "--bare", "-b", "main", bare)
    sh("git", "init", "-q", "-b", "main", seed)
    for rel, text in files.items():
        p = os.path.join(seed, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(text)
    sh("git", "-C", seed, "add", "-A")
    sh("git", "-C", seed, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
    for b in branches:
        sh("git", "-C", seed, "push", "-q", bare, f"HEAD:refs/heads/{b}")
    return bare


APPROVAL = json.dumps({"approved": True, "enabled": True, "daily_cap_usd": "5.00",
                       "valid_from": "2026-11-01", "valid_until": "2026-11-30",
                       "approved_by": "ceo", "approved_at": "2026-11-04T00:00:00Z"})


def ep(n, topic, status="PLANNED", **kw):
    e = {"id": f"20261105-0{n}", "date": DAY, "status": status, "title": "t", "description": "d",
         "tags": ["kids"], "learning_goal": "sharing", "topic_key": topic,
         "scenes": [{"n": 1, "prompt": "a green crocodile shares a toy", "duration": 5}]}
    e.update(kw)
    return e


class FakeHF:
    """Mock provider. Counts paid submissions."""
    def __init__(self, usd="1.00", mode="ok"):
        self.usd, self.mode, self.submits, self.n = Decimal(usd), mode, 0, 0

    def estimate_usd(self, p): return self.usd

    def submit(self, p):
        self.submits += 1
        if self.mode == "ambiguous":
            raise hf.AmbiguousSubmit("timeout after send")
        if self.mode == "reject":
            raise hf.ApiError(422, "bad")
        self.n += 1
        return f"req-{self.n}"

    def status(self, rid):
        return {"status": "failed" if self.mode == "fail" else "completed",
                "video": {"url": "mock://v"}}

    def download(self, url, dest):
        open(dest, "wb").write(b"fakevideo" + dest.encode())


class Base(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.t, True)

    def world(self, episodes_=(), approval=APPROVAL):
        files = {"README.md": "x"}
        for e in episodes_:
            files[f"briefings/episodes/{e['id']}.json"] = json.dumps(e)
        pub = make_remote(self.t, "pub", files, ("main", "inbox"))
        ctl = make_remote(self.t, "ctl", {"approvals/budget.json": approval} if approval else {"README": "x"})
        mk = lambda n, r, b="main": GitStore(os.path.join(self.t, n), r, b)
        return mk("pub", pub), mk("ctl", ctl), mk("inbox", pub, "inbox"), pub, ctl

    def run_gen(self, w, client, live=True):
        pub, ctl, inbox = w[:3]
        return generate.run(DAY, live, pub, ctl, inbox, os.path.join(self.t, "work"),
                            client=client, poll_s=0, max_polls=2)


class TestBudget(Base):
    def test_no_approval_blocks_everything(self):
        w = self.world([ep(1, "a")], approval=None)
        c = FakeHF()
        self.assertIn("BLOCKED", self.run_gen(w, c)[0])
        self.assertEqual(c.submits, 0)

    def test_expired_or_disabled_approval_blocks(self):
        for patch in ({"enabled": False}, {"valid_until": "2026-11-01"}, {"daily_cap_usd": "50"}):
            w = self.world([ep(1, "a")], approval=json.dumps({**json.loads(APPROVAL), **patch}))
            c = FakeHF()
            self.assertIn("BLOCKED", self.run_gen(w, c)[0], patch)
            self.assertEqual(c.submits, 0)
            shutil.rmtree(self.t); self.t = tempfile.mkdtemp()

    def test_dry_run_spends_nothing(self):
        w = self.world([ep(1, "a")]); c = FakeHF()
        out = self.run_gen(w, c, live=False)
        self.assertIn("DRY-RUN", out[0]); self.assertEqual(c.submits, 0)

    def test_cap_enforced_with_margin(self):
        # 2 episodes x $2.40 = 4.80; with 10% margin 5.28 > 5 => second skipped
        w = self.world([ep(1, "a"), ep(2, "b")]); c = FakeHF("2.40")
        out = self.run_gen(w, c)
        self.assertEqual(c.submits, 1)
        self.assertTrue(any("SKIPPED_BUDGET" in o for o in out))

    def test_concurrent_reservations_never_exceed_cap(self):
        w = self.world(approval=APPROVAL); ctl_remote = w[4]
        results = []
        def worker(i):
            s = GitStore(os.path.join(self.t, f"w{i}"), ctl_remote, "main")
            try:
                results.append(budget.reserve(s, DAY, f"E{i}", "1.50", "now"))
            except budget.OverBudget:
                results.append("over")
        th = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        [x.start() for x in th]; [x.join() for x in th]
        self.assertEqual(results.count("reserved"), 3)  # 3*1.5*1.1=4.95 <= 5 < 4 -> 6.6
        s = GitStore(os.path.join(self.t, "chk"), ctl_remote, "main"); s.sync()
        self.assertLessEqual(budget.committed_total(budget._events(s.workdir, DAY)), Decimal("5"))

    def test_reserve_idempotent(self):
        w = self.world(); ctl = w[1]
        self.assertEqual(budget.reserve(ctl, DAY, "E1", "1", "n"), "reserved")
        self.assertEqual(budget.reserve(ctl, DAY, "E1", "1", "n"), "exists")


class TestPipeline(Base):
    def test_happy_path_and_no_duplicate_generation(self):
        w = self.world([ep(1, "a")]); c = FakeHF()
        out = self.run_gen(w, c)
        self.assertIn("GENERATED", out[0]); self.assertEqual(c.submits, 1)
        w[0].sync()
        self.assertEqual(episodes.load(w[0].workdir, "20261105-01")["status"], "GENERATED")
        w[2].sync()
        man = json.load(open(os.path.join(w[2].workdir, "clips", DAY, "20261105-01", "manifest.json")))
        self.assertEqual(len(man["clips"][0]["sha256"]), 64)
        self.run_gen(w, c)  # rerun: must not regenerate
        self.assertEqual(c.submits, 1)

    def test_ambiguous_submit_never_resubmits(self):
        w = self.world([ep(1, "a")]); c = FakeHF(mode="ambiguous")
        out = self.run_gen(w, c)
        self.assertIn("NEEDS_REVIEW", out[0])
        self.run_gen(w, c); self.run_gen(w, c)
        self.assertEqual(c.submits, 1)

    def test_rejected_submit_releases_budget(self):
        w = self.world([ep(1, "a")]); c = FakeHF(mode="reject")
        self.assertIn("FAILED", self.run_gen(w, c)[0])
        w[1].sync()
        self.assertEqual(budget.committed_total(budget._events(w[1].workdir, DAY)), 0)

    def test_provider_failure_stops_safely(self):
        w = self.world([ep(1, "a")]); c = FakeHF(mode="fail")
        self.assertIn("FAILED", self.run_gen(w, c)[0])
        w[0].sync()
        self.assertEqual(episodes.load(w[0].workdir, "20261105-01")["status"], "FAILED")

    def test_only_planned_processed(self):
        w = self.world([ep(1, "a", "GENERATED"), ep(2, "b", "SCHEDULED")]); c = FakeHF()
        self.assertEqual(self.run_gen(w, c), []); self.assertEqual(c.submits, 0)

    def test_invalid_plan_rejected_before_spend(self):
        bad = ep(1, "a"); bad["scenes"][0]["prompt"] = "mickey fights with a knife"
        w = self.world([bad]); c = FakeHF()
        self.assertIn("INVALID", self.run_gen(w, c)[0]); self.assertEqual(c.submits, 0)


class TestPlanValidation(unittest.TestCase):
    def test_duplicate_topic(self):
        self.assertTrue(episodes.validate(ep(2, "same"), [ep(1, "same")]))
        self.assertEqual(episodes.validate(ep(2, "other"), [ep(1, "same")]), [])


if __name__ == "__main__":
    unittest.main()


class TestPublishGuard(Base):
    def test_no_double_publish_and_qa_gate(self):
        from croco import publish_guard as pg
        w = self.world([ep(1, "a", "GENERATED"), ep(2, "b", "GENERATED")]); pub = w[0]
        pg.claim_edit(pub, "20261105-01")
        with self.assertRaises(pg.NotAllowed): pg.claim_edit(pub, "20261105-01")
        pg.mark_qa(pub, "20261105-01", True, "ok")
        pg.claim_publish(pub, "20261105-01")
        with self.assertRaises(pg.NotAllowed): pg.claim_publish(pub, "20261105-01")
        pg.claim_edit(pub, "20261105-02"); pg.mark_qa(pub, "20261105-02", False, "copyright risk")
        with self.assertRaises(pg.NotAllowed): pg.claim_publish(pub, "20261105-02")
