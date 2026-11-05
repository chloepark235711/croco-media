import json, os, shutil, subprocess, tempfile, threading, unittest
from decimal import Decimal

os.environ["CROCO_OFFLINE"] = "1"   # no real Higgsfield / network call can happen in tests

from croco import brand, budget, episodes, generate, higgsfield as hf
from croco.gitstore import GitStore

DAY = "2026-11-05"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _no_network(*a, **k):
    raise AssertionError("tests must never call the real Higgsfield API")


hf._call = _no_network
hf.download = _no_network


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
    e = {"id": f"20261105-0{n}", "date": DAY, "status": status,
         "title": f"Croco Tries {topic}! | Croco's Little World #Shorts",
         "description": "Croco tries something new.\nFor parents: simple words.",
         "tags": ["Croco's Little World", "Croco", "preschool learning", "kids animation", topic],
         "hashtags": ["#CrocosLittleWorld", "#KidsShorts", "#Learning"], "made_for_kids": True,
         "learning_goal": "sharing", "topic_key": topic, "source_episode": f"EP-{topic}",
         "character_lock": brand.CHARACTER_LOCK,
         "scenes": [{"n": 1, "prompt": brand.scene_prompt("Croco rolls a soft ball."), "duration": 5}]}
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

    def world(self, episodes_=(), approval=APPROVAL, ctl_files=None):
        files = {"README.md": "x"}
        for e in episodes_:
            files[f"briefings/episodes/{e['id']}.json"] = json.dumps(e)
        pub = make_remote(self.t, "pub", files, ("main", "inbox"))
        cf = dict({"approvals/budget.json": approval} if approval else {"README": "x"}, **(ctl_files or {}))
        ctl = make_remote(self.t, "ctl", cf)
        mk = lambda n, r, b="main": GitStore(os.path.join(self.t, n), r, b)
        return mk("pub", pub), mk("ctl", ctl), mk("inbox", pub, "inbox"), pub, ctl

    def run_gen(self, w, client, live=True, verifier=lambda store: None):
        pub, ctl, inbox = w[:3]
        return generate.run(DAY, live, pub, ctl, inbox, os.path.join(self.t, "work"),
                            client=client, poll_s=0, max_polls=2, spend_day=DAY,
                            approval_verifier=verifier)


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
        self.assertTrue(any("DRY-RUN" in o for o in out)); self.assertEqual(c.submits, 0)

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

    def test_rejected_submit_HOLDS_budget_until_reconcile(self):
        w = self.world([ep(1, "a")]); c = FakeHF(mode="reject")
        self.assertIn("FAILED", self.run_gen(w, c)[0])
        w[1].sync()
        self.assertGreater(budget.committed_total(budget._events(w[1].workdir, DAY)), 0)
        self.assertEqual(budget.reconcile_release(w[1], DAY, "20261105-01", "n"), "held")

    def test_provider_failure_stops_safely(self):
        w = self.world([ep(1, "a")]); c = FakeHF(mode="fail")
        self.assertIn("FAILED", self.run_gen(w, c)[0])
        w[0].sync()
        self.assertEqual(episodes.load(w[0].workdir, "20261105-01")["status"], "FAILED")

    def test_only_planned_processed(self):
        w = self.world([ep(1, "a", "GENERATED"), ep(2, "b", "SCHEDULED")]); c = FakeHF()
        self.assertEqual(self.run_gen(w, c), []); self.assertEqual(c.submits, 0)

    def test_invalid_plan_rejected_before_spend(self):
        bad = ep(1, "a"); bad["scenes"][0]["prompt"] = brand.scene_prompt("mickey fights with a knife")
        w = self.world([bad]); c = FakeHF()
        self.assertIn("INVALID", self.run_gen(w, c)[0]); self.assertEqual(c.submits, 0)


class TestPermissions(Base):
    def test_worker_cannot_write_approvals(self):
        w = self.world(); ctl = GitStore(w[1].workdir, w[4], "main", allowed=("ledger/", "errors/", "requests/"))
        def evil(root):
            open(os.path.join(root, "approvals", "budget.json"), "w").write("{}")
            return ["approvals/budget.json"]
        with self.assertRaises(PermissionError): ctl.transact(evil, "x")
        ctl.sync()
        self.assertEqual(open(os.path.join(ctl.workdir, "approvals", "budget.json")).read(), APPROVAL)

    def test_bot_edited_approval_is_rejected(self):
        w = self.world(); ctl = w[1]
        ctl.transact(lambda r: (open(os.path.join(r, "approvals", "budget.json"), "w").write(APPROVAL + " "), ["approvals/budget.json"])[1], "bot edit")
        with self.assertRaises(budget.NotApproved): budget.reserve(ctl, DAY, "E1", "1", "n")

    def test_reconcile_requires_ceo_file(self):
        w = self.world(); ctl = w[1]
        budget.reserve(ctl, DAY, "E1", "1", "n")
        self.assertEqual(budget.reconcile_release(ctl, DAY, "E1", "n"), "held")
        ctl.transact(lambda r: (os.makedirs(os.path.join(r, "reconcile"), exist_ok=True), open(os.path.join(r, "reconcile", "E1.json"), "w").write('{"resolved":"not_charged"}'), ["reconcile/E1.json"])[2], "ceo")
        self.assertEqual(budget.reconcile_release(ctl, DAY, "E1", "n"), "released")


class TestBudgetDefaults(unittest.TestCase):
    def test_default_plan_fits_cap(self):
        per = Decimal("0.668"); total = per * 3 * 2
        self.assertLessEqual(total * Decimal("1.1"), Decimal("5"))
        self.assertGreater(per * 4 * 2 * Decimal("1.1"), Decimal("5"))
        e = ep(1, "a"); e["scenes"] = [{"n": i, "prompt": "p", "duration": 5} for i in range(4)]
        self.assertTrue(any("max 3" in x for x in episodes.validate(e)))


class TestPlanValidation(unittest.TestCase):
    def test_duplicate_topic(self):
        self.assertTrue(episodes.validate(ep(2, "same"), [ep(1, "same")]))
        self.assertEqual(episodes.validate(ep(2, "other"), [ep(1, "same")]), [])




class TestPublishGuard(Base):
    def test_no_double_publish_and_qa_gate(self):
        from croco import publish_guard as pg
        w = self.world([ep(1, "a", "GENERATED"), ep(2, "b", "GENERATED")]); pub = w[0]
        pg.claim_edit(pub, "20261105-01")
        with self.assertRaises(pg.NotAllowed): pg.claim_edit(pub, "20261105-01")
        pg.mark_qa(pub, "20261105-01", True, "ok", checklist=FULL_QA)
        pg.claim_publish(pub, "20261105-01", "2030-01-07T12:00", "a" * 64)
        with self.assertRaises(pg.NotAllowed): pg.claim_publish(pub, "20261105-01", "2030-01-07T17:00", "b" * 64)
        pg.claim_edit(pub, "20261105-02"); pg.mark_qa(pub, "20261105-02", False, "copyright risk")
        with self.assertRaises(pg.NotAllowed): pg.claim_publish(pub, "20261105-02", "2030-01-07T17:00", "b" * 64)


# ---------------------------------------------------------------- V2 recovery tests
from croco import marketing, plan_check, publish_guard as pg, qa, slots  # noqa: E402
import datetime  # noqa: E402
import io  # noqa: E402
import contextlib  # noqa: E402

FULL_QA = {k: True for k in qa.REQUIRED}
OLD_01_PROMPT = ("Cute 3D cartoon for toddlers: Croco, a friendly green baby crocodile with a yellow belly "
                 "and a red scarf, happily hands a colorful toy ball to a small smiling bunny in a sunny meadow")


class CountingHF(FakeHF):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.polled = []

    def status(self, rid):
        self.polled.append(rid); return super().status(rid)


class TestBrandBible(unittest.TestCase):
    def test_off_model_prompt_rejected(self):
        e = ep(1, "a"); e["scenes"][0]["prompt"] = OLD_01_PROMPT
        self.assertTrue(any("character lock" in x for x in episodes.validate(e)))

    def test_scarf_rejected_even_with_lock(self):
        e = ep(1, "a"); e["scenes"][0]["prompt"] = brand.scene_prompt("Croco wears a red scarf and waves.")
        self.assertTrue(any("scarf" in x for x in episodes.validate(e)))

    def test_negative_line_may_say_scary(self):
        self.assertIn("no scary expressions", brand.NEGATIVE)
        self.assertEqual(episodes.validate(ep(1, "a")), [])

    def test_pebble_requires_pebble_lock(self):
        bad = brand.scene_prompt("Croco waves to Pebble.")
        self.assertTrue(any("Pebble lock" in x for x in brand.check_scene(bad)))
        self.assertEqual(brand.check_scene(brand.scene_prompt("Croco waves to Pebble.", pebble=True)), [])

    def test_character_lock_field_required(self):
        e = ep(1, "a"); e["character_lock"] = "a green crocodile"
        self.assertTrue(any("character_lock" in x for x in episodes.validate(e)))


class TestDuplicates(unittest.TestCase):
    def test_same_source_episode_new_id_rejected(self):
        a = ep(2, "x", source_episode="EP-0001"); b = ep(3, "y", source_episode="EP-0001")
        self.assertTrue(any("source_episode" in x for x in episodes.validate(b, [a])))


class TestHold(Base):
    def hold_ep(self):
        return ep(1, "hold", "HOLD", hold=True, requests={"1": "old-request-id"},
                  scenes=[{"n": 1, "prompt": OLD_01_PROMPT, "duration": 5}])

    def test_hold_never_submitted_or_polled(self):
        w = self.world([self.hold_ep(), ep(2, "b")]); c = CountingHF()
        out = self.run_gen(w, c); self.run_gen(w, c)
        self.assertEqual(c.submits, 1)                      # only 20261105-02
        self.assertNotIn("old-request-id", c.polled)        # old request id never reused
        self.assertFalse(any("20261105-01" in o for o in out))
        w[0].sync()
        self.assertEqual(episodes.load(w[0].workdir, "20261105-01")["status"], "HOLD")

    def test_hold_flag_wins_over_generating_status(self):
        # the original 20261105-01 was GENERATING with a request id; hold=true must freeze it
        h = self.hold_ep(); h["status"] = "GENERATING"
        w = self.world([h]); c = CountingHF()
        self.run_gen(w, c); self.run_gen(w, c)
        self.assertEqual((c.submits, c.polled), (0, []))

    def test_hold_cannot_be_published(self):
        h = self.hold_ep(); h["status"] = "GENERATED"      # even if someone flips the status
        w = self.world([h])
        with self.assertRaises(pg.NotAllowed): pg.claim_edit(w[0], "20261105-01")


class TestGeneratedRecord(Base):
    def test_sha256_and_paths_recorded(self):
        w = self.world([ep(1, "a")]); self.run_gen(w, FakeHF())
        w[0].sync(); e = episodes.load(w[0].workdir, "20261105-01")
        self.assertEqual(len(e["sha256"]["1"]), 64)
        self.assertEqual(e["asset_paths"], [f"clips/{DAY}/20261105-01/scene-01.mp4"])
        w[2].sync()
        man = json.load(open(os.path.join(w[2].workdir, "clips", DAY, "20261105-01", "manifest.json")))
        self.assertEqual((man["hold"], man["test"]), (False, False))
        self.assertEqual(man["clips"][0]["sha256"], e["sha256"]["1"])

    def test_overdue_planned_picked_and_max_two_per_run(self):
        old = ep(1, "a", date="2026-11-04"); w = self.world([old, ep(2, "b"), ep(3, "c")])
        c = FakeHF("0.50"); out = self.run_gen(w, c)
        self.assertEqual(c.submits, 2)
        self.assertTrue(out[0].startswith("20261105-01"))   # oldest first
        w[0].sync(); self.assertEqual(episodes.load(w[0].workdir, "20261105-03")["status"], "PLANNED")

    def test_ledger_uses_spend_day(self):
        w = self.world([ep(1, "a", date="2026-11-06")]); pub, ctl, inbox = w[:3]
        generate.run("2026-11-06", True, pub, ctl, inbox, os.path.join(self.t, "work"),
                     client=FakeHF(), poll_s=0, max_polls=2, spend_day=DAY, approval_verifier=lambda s: None)
        ctl.sync()
        self.assertTrue(os.path.exists(os.path.join(ctl.workdir, "ledger", f"{DAY}.jsonl")))
        self.assertFalse(os.path.exists(os.path.join(ctl.workdir, "ledger", "2026-11-06.jsonl")))


class TestPlanCheck(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.t, True)

    def write(self, *eps):
        d = os.path.join(self.t, "briefings", "episodes"); os.makedirs(d, exist_ok=True)
        for e in eps:
            json.dump(e, open(os.path.join(d, e["id"] + ".json"), "w"))

    def check(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return plan_check.main(DAY, self.t)

    def test_hold_does_not_take_a_slot(self):
        self.write(ep(1, "h", "HOLD", hold=True), ep(2, "a"), ep(3, "b"))
        self.assertEqual(self.check(), 0)

    def test_wrong_count_fails(self):
        self.write(ep(1, "h", "HOLD", hold=True), ep(2, "a"))
        self.assertEqual(self.check(), 1)

    def test_real_plan_for_2026_11_06(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(plan_check.main("2026-11-06", REPO), 0)
        self.assertEqual(episodes.load(REPO, "20261105-02")["target_slot"], "2026-11-06T12:00")
        self.assertEqual(episodes.load(REPO, "20261105-03")["target_slot"], "2026-11-06T17:00")
        one = episodes.load(REPO, "20261105-01")
        self.assertEqual(one["status"], "HOLD")
        self.assertEqual(one["requests"], {"1": "01a1a7fc-58de-7ed1-9953-b2572114fab4"})  # preserved, not reused
        for i in ("02", "03"):
            e = episodes.load(REPO, f"20261105-{i}")
            self.assertEqual(e["character_lock"], brand.CHARACTER_LOCK)
            self.assertEqual(marketing.check(e)[0], [])

    def test_all_modules_compile(self):
        import py_compile
        for n in os.listdir(os.path.join(REPO, "croco")):
            if n.endswith(".py"):
                py_compile.compile(os.path.join(REPO, "croco", n), doraise=True,
                                   cfile=os.path.join(self.t, n + "c"))


class TestMarketing(unittest.TestCase):
    def test_rules(self):
        e = ep(1, "a"); self.assertEqual(marketing.check(e)[0], [])
        for k, v, frag in (("title", "Momo Shares! | Croco's Little World #Shorts", "momo"),
                           ("hashtags", ["#KidsShorts", "#Fun", "#Play"], "#CrocosLittleWorld"),
                           ("hashtags", ["#CrocosLittleWorld", "#Croco's", "#Play"], "bad hashtag"),
                           ("description", "Like and subscribe!", "subscribe"),
                           ("made_for_kids", False, "made_for_kids")):
            bad = dict(e, **{k: v})
            self.assertTrue(any(frag in x for x in marketing.check(bad)[0]), (k, v))


class TestSlots(unittest.TestCase):
    def test_denver_times_follow_dst(self):
        utc = datetime.timezone.utc
        self.assertEqual(slots.slot_datetime("2026-11-05", "12:00").astimezone(utc).hour, 19)  # MST
        self.assertEqual(slots.slot_datetime("2026-07-01", "17:00").astimezone(utc).hour, 23)  # MDT

    def test_next_free_slot(self):
        now = datetime.datetime(2026, 11, 5, 15, 0, tzinfo=datetime.timezone.utc)   # 08:00 MST
        self.assertEqual(slots.next_free_slot(set(), now), "2026-11-05T12:00")
        self.assertEqual(slots.next_free_slot({"2026-11-05T12:00"}, now), "2026-11-05T17:00")
        late = datetime.datetime(2026, 11, 5, 23, 45, tzinfo=datetime.timezone.utc)  # 16:45 MST
        self.assertEqual(slots.next_free_slot(set(), late), "2026-11-06T12:00")
        self.assertTrue(slots.is_test_post("[TEST] Pipeline Test - Do Not Publish"))


class TestPublishV2(Base):
    def ready(self, w, eid):
        pg.claim_edit(w[0], eid); pg.mark_qa(w[0], eid, True, "ok", checklist=FULL_QA)

    def test_incomplete_checklist_cannot_pass(self):
        w = self.world([ep(1, "a", "GENERATED")]); pg.claim_edit(w[0], "20261105-01")
        with self.assertRaises(pg.NotAllowed):
            pg.mark_qa(w[0], "20261105-01", True, "ok", checklist=dict(FULL_QA, copyright_trademark=False))
        with self.assertRaises(pg.NotAllowed): pg.mark_qa(w[0], "20261105-01", True, "ok")

    def test_two_episodes_never_share_slot_or_file(self):
        w = self.world([ep(1, "a", "GENERATED"), ep(2, "b", "GENERATED")])
        self.ready(w, "20261105-01"); self.ready(w, "20261105-02")
        pg.claim_publish(w[0], "20261105-01", "2030-01-07T12:00", "a" * 64)
        with self.assertRaises(pg.NotAllowed): pg.claim_publish(w[0], "20261105-02", "2030-01-07T12:00", "b" * 64)
        with self.assertRaises(pg.NotAllowed): pg.claim_publish(w[0], "20261105-02", "2030-01-07T17:00", "a" * 64)
        with self.assertRaises(pg.NotAllowed): pg.claim_publish(w[0], "20261105-02", "2030-01-07T09:00", "b" * 64)
        pg.claim_publish(w[0], "20261105-02", "2030-01-07T17:00", "b" * 64)

    def test_published_only_after_schedule_and_once(self):
        w = self.world([ep(1, "a", "GENERATED"), ep(2, "b", "GENERATED")])
        with self.assertRaises(pg.NotAllowed): pg.record_published(w[0], "20261105-01", "yt1")
        self.ready(w, "20261105-01")
        pg.claim_publish(w[0], "20261105-01", "2030-01-07T12:00", "a" * 64)
        pg.record_metricool(w[0], "20261105-01", "416000001", "uuid-1")
        with self.assertRaises(pg.NotAllowed): pg.record_metricool(w[0], "20261105-01", "416000002")
        pg.record_published(w[0], "20261105-01", "yt1")
        with self.assertRaises(pg.NotAllowed): pg.record_published(w[0], "20261105-01", "yt2")
        w[0].sync(); self.assertEqual(episodes.load(w[0].workdir, "20261105-01")["status"], "PUBLISHED")

    def test_publish_failure_parks_for_review(self):
        w = self.world([ep(1, "a", "GENERATED")]); self.ready(w, "20261105-01")
        pg.claim_publish(w[0], "20261105-01", "2030-01-07T12:00", "a" * 64)
        pg.publish_failed(w[0], "20261105-01", "metricool timeout")
        with self.assertRaises(pg.NotAllowed): pg.claim_publish(w[0], "20261105-01", "2030-01-07T17:00", "a" * 64)


class TestOffline(unittest.TestCase):
    def test_real_client_is_blocked_in_tests(self):
        import importlib
        real = importlib.reload(importlib.import_module("croco.higgsfield"))
        try:
            with self.assertRaises(real.OfflineMode): real.estimate_usd({"prompt": "x"})
            with self.assertRaises(real.OfflineMode): real.submit({"prompt": "x"})
        finally:
            real._call = _no_network; real.download = _no_network


AGENT_APPROVAL = json.dumps({**json.loads(APPROVAL), "approved_by":
    "CEO (instruction given in Claude Code chat; recorded by Claude Code, NOT a GitHub-verified CEO commit)"})
HELD_LEDGER = {f"ledger/{DAY}.jsonl": json.dumps({"at": "x", "episode_id": "20261105-01", "type": "reserve", "usd": "0.668"}) + "\n"}


class TestApprovalProvenance(Base):
    def test_agent_recorded_approval_blocks(self):
        w = self.world([ep(2, "a")], approval=AGENT_APPROVAL); c = FakeHF()
        out = self.run_gen(w, c)
        self.assertIn("BLOCKED", out[0]); self.assertIn("agent", out[0]); self.assertEqual(c.submits, 0)

    def test_unverified_commit_blocks(self):
        def deny(store): raise budget.NotApproved("not a verified commit by owner")
        w = self.world([ep(2, "a")]); c = FakeHF()
        self.assertIn("BLOCKED", self.run_gen(w, c, verifier=deny)[0]); self.assertEqual(c.submits, 0)
        out = self.run_gen(w, c, live=False, verifier=deny)
        self.assertTrue(any("NOT ACTIVE" in o for o in out)); self.assertEqual(c.submits, 0)

    def test_repo_slug(self):
        self.assertEqual(budget._repo_slug("https://github.com/chloepark235711/croco-control"), "chloepark235711/croco-control")
        self.assertIsNone(budget._repo_slug("/tmp/x/ctl.git"))


class TestUnconfirmedCost(Base):
    def hold(self):
        return ep(1, "hold", "HOLD", hold=True, requests={"1": "old"}, scenes=[{"n": 1, "prompt": OLD_01_PROMPT, "duration": 5}])

    def test_unconfirmed_hold_cost_blocks_that_day(self):
        w = self.world([self.hold(), ep(2, "a")], ctl_files=HELD_LEDGER); c = FakeHF()
        out = self.run_gen(w, c)
        self.assertIn("unconfirmed cost", out[0]); self.assertEqual(c.submits, 0)
        self.assertTrue(any("UNCONFIRMED" in o for o in self.run_gen(w, c, live=False)))

    def test_ceo_reconcile_charged_unblocks(self):
        rec = {"reconcile/20261105-01.json": json.dumps({"resolved": "charged", "usd": "0.40", "by": "ceo"})}
        w = self.world([self.hold(), ep(2, "a")], ctl_files={**HELD_LEDGER, **rec}); c = FakeHF()
        out = self.run_gen(w, c)
        self.assertEqual(c.submits, 1, out)
        w[1].sync()
        ev = budget._events(w[1].workdir, DAY)
        self.assertTrue(any(e["type"] == "settle" and e["episode_id"] == "20261105-01" and e["usd"] == "0.40" for e in ev))

    def test_failure_mid_run_stops_spending_that_day(self):
        class RejectFirst(FakeHF):
            def submit(self, p):
                self.submits += 1
                if self.submits == 1: raise hf.ApiError(422, "bad")
                return "req-x"
        w = self.world([ep(2, "a"), ep(3, "b")]); c = RejectFirst()
        out = self.run_gen(w, c)
        self.assertEqual(c.submits, 1, out)
        w[0].sync(); self.assertEqual(episodes.load(w[0].workdir, "20261105-03")["status"], "PLANNED")


class TestLimitedRun(Base):
    def test_max_episodes_one(self):
        w = self.world([ep(2, "a"), ep(3, "b")]); c = FakeHF("0.50"); pub, ctl, inbox = w[:3]
        generate.run(DAY, True, pub, ctl, inbox, os.path.join(self.t, "work"), client=c, poll_s=0, max_polls=2,
                     spend_day=DAY, approval_verifier=lambda s: None, max_new=1)
        self.assertEqual(c.submits, 1)


class TestRequestRecord(Base):
    def test_private_request_record(self):
        w = self.world([ep(1, "a")]); self.run_gen(w, FakeHF())
        w[1].sync()
        r = json.load(open(os.path.join(w[1].workdir, "requests", "20261105-01.json")))
        s1 = r["scenes"]["1"]
        self.assertEqual((s1["request_id"], s1["status"], s1["video_url"]), ("req-1", "completed", "mock://v"))
        self.assertEqual(len(s1["sha256"]), 64); self.assertEqual(r["cost_usd"], "1.00")
        self.assertIn("estimate", r["cost_basis"])


class TestQARecord(unittest.TestCase):
    def test_unverified_is_recorded_and_blocks(self):
        part = dict(FULL_QA); del part["audio_loudness"]; part["copyright_trademark"] = False
        rec = qa.record(part)
        self.assertEqual((rec["audio_loudness"], rec["copyright_trademark"], rec["playback_ok"]), ("UNVERIFIED", "FAIL", "PASS"))
        ok, why = qa.evaluate(part); self.assertFalse(ok); self.assertIn("UNVERIFIED: audio_loudness", why)
        self.assertEqual(qa.evaluate(FULL_QA)[0], True)
        self.assertEqual(len(qa.REQUIRED), 13)


class TestSlotChoice(Base):
    NOW = datetime.datetime(2030, 1, 7, 15, 0, tzinfo=datetime.timezone.utc)   # 08:00 MST

    def test_target_slot_used_when_free(self):
        w = self.world([ep(2, "a", "QA_PASSED", target_slot="2030-01-07T12:00")])
        self.assertEqual(pg.choose_slot(w[0], "20261105-02", now=self.NOW), "2030-01-07T12:00")

    def test_past_target_replanned_to_next_free(self):
        late = datetime.datetime(2030, 1, 7, 23, 45, tzinfo=datetime.timezone.utc)   # 16:45 MST
        w = self.world([ep(2, "a", "QA_PASSED", target_slot="2030-01-07T12:00")])
        self.assertEqual(pg.choose_slot(w[0], "20261105-02", now=late), "2030-01-08T12:00")

    def test_metricool_occupied_target_replanned(self):
        w = self.world([ep(2, "a", "QA_PASSED", target_slot="2030-01-07T12:00"),
                        ep(3, "b", "QA_PASSED", target_slot="2030-01-07T17:00")])
        got = pg.choose_slot(w[0], "20261105-02", occupied_external={"2030-01-07T12:00"}, now=self.NOW)
        self.assertEqual(got, "2030-01-08T12:00")   # 17:00 is reserved as -03's target

    def test_claim_refuses_past_slot(self):
        w = self.world([ep(1, "a", "GENERATED")]); pg.claim_edit(w[0], "20261105-01")
        pg.mark_qa(w[0], "20261105-01", True, "ok", checklist=FULL_QA)
        with self.assertRaises(pg.NotAllowed): pg.claim_publish(w[0], "20261105-01", "2020-01-01T12:00", "a" * 64)


if __name__ == "__main__":
    unittest.main()
