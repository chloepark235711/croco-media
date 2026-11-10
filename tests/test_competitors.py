import contextlib
import datetime as dt
import io
import json
import os
import tempfile
import unittest
from unittest import mock

os.environ["CROCO_OFFLINE"] = "1"

from croco import competitors as C

FAKE_KEY = "AIza" + "X" * 35
NOW = dt.datetime(2026, 11, 10, 0, 0, tzinfo=dt.timezone.utc)


def iso(days_ago):
    return (NOW - dt.timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


class FakeYT:
    """Minimal fake of the 4 read-only endpoints. Counts real (non-cached) calls."""

    def __init__(self, subs=500_000):
        self.calls = []
        self.subs = subs
        self.channels = {f"UC{i}": f"Kids Channel {i}" for i in range(12)}
        self.channels["UCown"] = "Croco's Little World"

    def __call__(self, endpoint, params):
        assert FAKE_KEY not in json.dumps(params), "key must never be a URL parameter"
        self.calls.append((endpoint, params))
        if endpoint == "search":
            items = [{"id": {"videoId": f"v{cid}_{n}"}, "snippet": {"channelId": cid}}
                     for cid in self.channels for n in range(2)]
            return {"items": items}
        if endpoint == "channels":
            if "forHandle" in params:
                return {"items": [{"id": "UC0"}]}
            ids = params["id"].split(",")
            return {"items": [{"id": i, "snippet": {"title": self.channels.get(i, i), "customUrl": "@x"},
                               "statistics": {"subscriberCount": str(self.subs), "videoCount": "100"},
                               "contentDetails": {"relatedPlaylists": {"uploads": "UU" + i}}} for i in ids]}
        if endpoint == "playlistItems":
            cid = params["playlistId"][2:]
            return {"items": [{"contentDetails": {"videoId": f"v{cid}_{n}"}} for n in range(6)]}
        if endpoint == "videos":
            out = []
            for vid in params["id"].split(","):
                n = int(vid.rsplit("_", 1)[1])
                cid = vid[1:].rsplit("_", 1)[0]
                out.append({"id": vid,
                            "snippet": {"channelId": cid, "channelTitle": self.channels.get(cid, cid),
                                        "title": f"Baby Duck Learns Colors Story {n}", "description": "Thank you for watching!",
                                        "publishedAt": iso(n * 3 + 0.5)},
                            "statistics": {"viewCount": str(1000 * (n + 1)), "likeCount": str(10 * (n + 1))},
                            "contentDetails": {"duration": "PT45S"}, "status": {"madeForKids": True}})
            return {"items": out}
        raise AssertionError(endpoint)


class CompetitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.p = mock.patch.object(C, "now_utc", return_value=NOW)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def client(self, fake, state=None):
        return C.Client(state or C.load_state(self.tmp), key=FAKE_KEY, transport=fake)

    def test_cache_dedup_costs_zero(self):
        fake = FakeYT()
        c = self.client(fake)
        c.get("videos", id="vUC1_0", part="snippet")
        c.get("videos", part="snippet", id="vUC1_0")       # same request, other param order
        self.assertEqual(len(fake.calls), 1)
        u = c.usage()
        self.assertEqual((u["units"], u["cache_hits"]), (1, 1))

    def test_unit_cap_refuses_before_calling(self):
        fake = FakeYT()
        c = self.client(fake)
        with mock.patch.object(C, "DAILY_UNIT_CAP", 2):
            c.get("videos", id="vUC1_0")
            c.get("videos", id="vUC1_1")
            with self.assertRaises(C.QuotaCapReached):
                c.get("videos", id="vUC1_2")
        self.assertEqual(len(fake.calls), 2)

    def test_search_cap(self):
        fake = FakeYT()
        c = self.client(fake)
        with mock.patch.object(C, "DAILY_SEARCH_CAP", 1):
            c.get("search", q="a")
            with self.assertRaises(C.QuotaCapReached):
                c.get("search", q="b")

    def test_failed_call_still_counts_quota(self):
        def boom(e, p):
            raise C.ApiError(403, "quotaExceeded")
        c = self.client(boom)
        with self.assertRaises(C.ApiError):
            c.get("videos", id="vUC1_0")
        self.assertEqual(c.usage()["units"], 1)

    def test_key_never_in_state_or_report(self):
        fake = FakeYT()
        res = C.run(self.tmp, client=self.client(fake))
        blob = open(os.path.join(self.tmp, "state.json")).read() + json.dumps(res) + C.render(res)
        self.assertNotIn(FAKE_KEY, blob)
        self.assertEqual(C.redact(f"bad key {FAKE_KEY}", FAKE_KEY), "bad key [REDACTED]")
        self.assertEqual(C.redact(f"x {FAKE_KEY}", ""), "x [REDACTED]")

    def test_selection_10_candidates_5_tracked_excludes_own(self):
        res = C.run(self.tmp, client=self.client(FakeYT()))
        sel = res["selection"]
        self.assertEqual(len(sel["candidates"]), 10)
        self.assertEqual(len(sel["tracked"]), 5)
        self.assertNotIn("UCown", [m["id"] for m in sel["candidates"]])
        self.assertTrue(res["reevaluated"])
        self.assertLessEqual(res["quota"]["units"], 500)

    def test_subscriber_change_only_with_previous_snapshot(self):
        r1 = C.run(self.tmp, client=self.client(FakeYT(subs=500_000)), today="2026-11-09")
        self.assertTrue(all(m["subscriber_change"] is None for m in r1["tracked"]))
        r1b = C.run(self.tmp, client=self.client(FakeYT(subs=500_000), C.load_state(self.tmp)), today="2026-11-09")
        self.assertTrue(all(m["subscriber_change"] is None for m in r1b["tracked"]), "same-day snapshot is not a baseline")
        st = C.load_state(self.tmp)
        with mock.patch.object(C, "now_utc", return_value=NOW + dt.timedelta(days=1)):  # cache (20h) expired
            r2 = C.run(self.tmp, client=self.client(FakeYT(subs=510_000), st), today="2026-11-10")
        self.assertTrue(all(m["subscriber_change"]["delta"] == 10_000 for m in r2["tracked"]))
        self.assertFalse(r2["reevaluated"])                      # weekly, not daily

    def test_hidden_subscribers_not_reported_as_zero(self):
        fake = FakeYT()
        orig = fake.__call__

        def hidden(e, p):
            r = orig(e, p)
            if e == "channels" and "id" in p:
                for it in r["items"]:
                    it["statistics"] = {"hiddenSubscriberCount": True, "videoCount": "5"}
            return r
        res = C.run(self.tmp, client=self.client(hidden))
        self.assertTrue(all(m["subscribers"] is None for m in res["tracked"]))
        self.assertIn("비공개", C.render(res))

    def test_weekly_reevaluation(self):
        C.run(self.tmp, client=self.client(FakeYT()))
        with mock.patch.object(C, "now_utc", return_value=NOW + dt.timedelta(days=7, hours=1)):
            r = C.run(self.tmp, client=self.client(FakeYT(), C.load_state(self.tmp)))
        self.assertTrue(r["reevaluated"])

    def test_metrics(self):
        self.assertEqual(C.parse_duration("PT1M5S"), 65)
        self.assertEqual(C.parse_duration("P0D"), 0)
        res = C.run(self.tmp, client=self.client(FakeYT()))
        m = res["tracked"][0]
        self.assertEqual((m["uploads_7d"], m["uploads_30d"]), (3, 6))  # ages 0.5,3.5,6.5,9.5,12.5,15.5
        self.assertEqual(m["median_like_view_ratio_30d"], 0.01)
        self.assertEqual(m["performance_spread_30d"]["max_over_median"], round(6000 / 3500, 2))
        self.assertIn("동물", m["topics_30d"])
        self.assertNotIn("감정·친구·예절", m["topics_30d"])   # description boilerplate ignored
        report = C.render(res)
        for h in ("추적 중인 경쟁 채널", "선정 근거", "주목할 경쟁 영상 TOP 5", "오늘의 글로벌 트렌드 TOP 3", "추정하지 않음"):
            self.assertIn(h, report)

    def test_classifier_whole_words(self):
        self.assertEqual(C.classify("Kids Cartoon | BabyBus", C.TOPICS), [])
        self.assertEqual(C.classify("Fire Trucks and Cars", C.TOPICS), ["탈것"])
        self.assertIn("노래·동요", C.classify("Nursery Rhymes", C.FORMATS))

    def test_top_videos_shorts_only(self):
        res = C.run(self.tmp, client=self.client(FakeYT()))
        res["tracked"][0]["videos_recent"][0]["seconds"] = 3600
        self.assertTrue(all(v["seconds"] <= 180 for v in C.top_videos(res)))

    def test_rerun_same_day_hits_cache(self):
        fake = FakeYT()
        C.run(self.tmp, client=self.client(fake))
        n = len(fake.calls)
        with mock.patch.object(C, "now_utc", return_value=NOW + dt.timedelta(minutes=30)):
            C.run(self.tmp, client=self.client(fake, C.load_state(self.tmp)), reevaluate=True)
        self.assertEqual(len(fake.calls), n, "same-day rerun must be served from cache")

    def test_language_fit(self):
        self.assertTrue(C.is_english({"title": "Croco Says Sorry", "defaultAudioLanguage": "en-US"}))
        self.assertFalse(C.is_english({"title": "Croco", "defaultAudioLanguage": "hi"}))
        self.assertFalse(C.is_english({"title": "मैं तोता मैं तोता"}))
        self.assertTrue(C.is_english({"title": "Baby Duck Learns Colors"}))

    def test_proxy_mode_sends_no_key_header(self):
        seen = {}

        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b'{"items": []}'

        def fake_urlopen(req, timeout=None, context=None):
            seen["headers"] = {k.lower(): v for k, v in req.header_items()}
            seen["url"] = req.full_url
            return Resp()
        with mock.patch.dict(os.environ, {"CROCO_OFFLINE": "0", "YOUTUBE_API_KEY": FAKE_KEY}), \
                mock.patch.object(C.urllib.request, "urlopen", fake_urlopen):
            C.Client(C.load_state(self.tmp), auth="proxy").get("videos", id="vUC1_0")
            self.assertNotIn("x-goog-api-key", seen["headers"])          # proxy attaches it outside the VM
            self.assertNotIn(FAKE_KEY, seen["url"])
            C.Client(C.load_state(self.tmp), key=FAKE_KEY).get("videos", id="vUC1_1")
            self.assertEqual(seen["headers"]["x-goog-api-key"], FAKE_KEY)  # local mode: header only
            self.assertNotIn(FAKE_KEY, seen["url"])

    def test_circuit_breaker_stops_after_auth_error(self):
        calls = []

        def forbidden(e, p):
            calls.append(e)
            raise C.ApiError(403, "forbidden")
        res = C.run(self.tmp, client=self.client(forbidden))
        self.assertEqual(len(calls), 1, "after a 403 no further network call may happen")
        self.assertTrue(res["quota"]["circuit"])
        self.assertEqual(res["tracked"], [])
        self.assertIn("호출 중단", C.render(res))

    def test_three_consecutive_errors_open_circuit(self):
        calls = []

        def flaky(e, p):
            calls.append(e)
            raise C.ApiError(500, "backendError")
        C.run(self.tmp, client=self.client(flaky))
        self.assertEqual(len(calls), 3)

    def test_deadline_stops_new_calls(self):
        fake = FakeYT()
        c = C.Client(C.load_state(self.tmp), key=FAKE_KEY, transport=fake, deadline_sec=1)
        with mock.patch.object(C, "now_utc", return_value=NOW + dt.timedelta(seconds=5)):
            with self.assertRaises(C.QuotaCapReached):
                c.get("videos", id="vUC1_0")
        self.assertEqual(fake.calls, [])

    def test_main_never_raises_and_reports_blocked(self):
        def boom(*a, **k):
            raise RuntimeError(f"unexpected {FAKE_KEY}")
        out = io.StringIO()
        with mock.patch.object(C, "run", boom), mock.patch.object(C, "load_key", return_value=FAKE_KEY), \
                contextlib.redirect_stdout(out):
            rc = C.main(["run", "--state", self.tmp])
        self.assertEqual(rc, 3)
        self.assertIn("BLOCKED", out.getvalue())
        self.assertNotIn(FAKE_KEY, out.getvalue())

    def test_main_blocked_when_nothing_collected(self):
        def down(e, p):
            raise C.ApiError(0, "URLError: no route")
        real = C.Client
        out = io.StringIO()
        with mock.patch.object(C, "load_key", return_value=FAKE_KEY), \
                mock.patch.object(C, "Client", lambda st: real(st, key=FAKE_KEY, transport=down)), \
                contextlib.redirect_stdout(out):
            rc = C.main(["run", "--state", self.tmp])
        self.assertEqual(rc, 3)
        self.assertIn("BLOCKED: no data collected", out.getvalue())
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "state.json")), "ledger must still be saved")

    def test_offline_guard(self):
        c = C.Client(C.load_state(self.tmp), key=FAKE_KEY)
        with self.assertRaises(RuntimeError):
            c.get("videos", id="vUC1_0")


if __name__ == "__main__":
    unittest.main()
