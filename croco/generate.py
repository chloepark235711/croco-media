"""20:00 generation worker (V2).

Safe by default: without --live nothing is reserved, submitted or pushed.
Live mode additionally requires a valid budget approval in croco-control.

    python -m croco.generate --date 2026-11-06            # dry run (estimates only, $0)
    python -m croco.generate --date 2026-11-06 --live     # real, paid generation
--date is the publish date D. Episodes planned for D, plus still-PLANNED episodes from
earlier dates that never ran, are processed (oldest first), at most EPISODES_PER_DAY
per run. HOLD episodes are never submitted, re-submitted or polled.
The $5 cap is per America/Denver SPEND day (the day the run happens), shared by all runs.
Env: CROCO_CONTROL_REMOTE (private repo URL), CROCO_WORK (scratch dir).
"""
import argparse
import datetime
import hashlib
import json
import os
import time
from decimal import Decimal

from . import budget, episodes, higgsfield as hf, slots
from .gitstore import GitStore

RES, ASPECT = "720p", "9:16"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def set_status(pub, eid, mutate, msg):
    """CAS update of one episode record. mutate(ep) -> bool(changed)."""
    def fn(root):
        ep = episodes.load(root, eid)
        return [episodes.save(root, ep)] if mutate(ep) else None
    return pub.transact(fn, f"{eid}: {msg}")


def scene_params(ep, s):
    return {"prompt": s["prompt"], "duration": s["duration"], "resolution": RES,
            "aspect_ratio": ASPECT}


def select(all_eps, date, max_new=episodes.EPISODES_PER_DAY):
    """Episodes this run may touch: resume GENERATING ones (poll only), then PLANNED ones
    dated <= D, oldest first; never HOLD; at most EPISODES_PER_DAY new submissions."""
    live_eps = [e for e in all_eps if episodes.is_active(e) and e.get("date", "") <= date]
    resume = [e for e in live_eps if e["status"] == "GENERATING"]
    planned = sorted((e for e in live_eps if e["status"] == "PLANNED"),
                     key=lambda e: (e["date"], e["id"]))
    return resume + planned[:max(0, min(max_new, episodes.EPISODES_PER_DAY))]


def statuses(pub):
    return {e["id"]: e.get("status") for e in episodes.all_episodes(pub.workdir)}


def unconfirmed_gate(pub, ctl, day):
    """Apply any CEO reconcile files, then return the episode ids whose cost on `day` is still unknown."""
    ctl.sync()
    st = statuses(pub)
    pending = budget.unconfirmed(ctl.workdir, day, st)
    for eid in pending:
        budget.apply_reconcile(ctl, day, eid, now())
    ctl.sync()
    return budget.unconfirmed(ctl.workdir, day, st)


def run(date, live, pub, ctl, inbox, work, client=hf, poll_s=15, max_polls=80, spend_day=None,
        approval_verifier=budget.github_verifier, max_new=episodes.EPISODES_PER_DAY):
    day = spend_day or slots.denver_today()
    report = []
    sync_root = pub.workdir
    pub.sync()
    todo = select(episodes.all_episodes(sync_root), date, max_new)
    try:
        ctl.sync()
        cap = budget.load_approval(ctl.workdir, day)
        approval_verifier(ctl)
        approval = (True, f"APPROVAL: valid, cap ${cap}, spend day {day}")
    except Exception as e:
        approval = (False, f"APPROVAL: NOT ACTIVE ({e})")
    if live:
        if not approval[0]:
            return [f"BLOCKED: {approval[1]}"]
        stuck = unconfirmed_gate(pub, ctl, day)
        if stuck:
            return [f"BLOCKED: unconfirmed cost on {day} for {', '.join(stuck)}; owner must add "
                    f"croco-control reconcile/<id>.json (charged + usd, or not_charged)"]
    else:
        report.append(approval[1] + ("" if approval[0] else " -> live run would be BLOCKED"))
        try:
            stuck = budget.unconfirmed(ctl.workdir, day, statuses(pub))
            if stuck:
                report.append(f"UNCONFIRMED COST on {day}: {', '.join(stuck)} -> live run would be BLOCKED")
        except Exception as e:
            report.append(f"LEDGER: unreadable ({type(e).__name__})")
    for ep in todo:
        eid = ep["id"]
        try:
            report.append(f"{eid}: {process(ep, live, pub, ctl, inbox, work, client, day, poll_s, max_polls)}")
        except Exception as e:  # never crash the whole run; record and move on
            report.append(f"{eid}: ERROR {type(e).__name__}: {e}")
            if live:
                try:
                    budget.log_error(ctl, day, eid, f"{type(e).__name__}: {e}", now())
                except Exception:
                    pass
    return report


def process(ep, live, pub, ctl, inbox, work, client, day, poll_s, max_polls):
    eid = ep["id"]
    if episodes.is_hold(ep):            # defence in depth; select() already skips HOLD
        return "HOLD (never submitted or polled)"
    probs = episodes.validate(ep)
    if probs:
        if live:
            set_status(pub, eid, lambda e: e.update(status="FAILED", error="invalid: " + "; ".join(probs)) or True, "invalid plan")
        return "INVALID " + "; ".join(probs)

    reqs = ep.get("requests", {})
    if ep["status"] == "GENERATING" and len(reqs) < len(ep["scenes"]):
        # some submits never recorded a request id: do NOT resubmit.
        if live:
            set_status(pub, eid, lambda e: e.update(status="NEEDS_REVIEW", error="incomplete submit state") or True, "needs review")
        return "NEEDS_REVIEW (incomplete submit state, no resubmit)"

    if ep["status"] == "PLANNED":
        est = [client.estimate_usd(scene_params(ep, s)) for s in ep["scenes"]]
        total = sum(est, Decimal(0))
        if not live:
            return f"DRY-RUN estimate ${total} for {len(est)} scenes (nothing reserved or sent)"
        stuck = unconfirmed_gate(pub, ctl, day)
        if stuck:   # an earlier episode in this run failed ambiguously: stop spending today
            return f"BLOCKED (unconfirmed cost on {day} for {', '.join(stuck)}); stays PLANNED"
        try:
            budget.reserve(ctl, day, eid, total, now())
        except budget.OverBudget as e:
            set_status(pub, eid, lambda e_: e_.update(status="SKIPPED_BUDGET") or True, "skipped budget")
            return f"SKIPPED_BUDGET ({e})"
        # "exists": an earlier/concurrent run reserved; the claim CAS below
        # decides which single worker may submit.
        # claim: only the worker whose push wins proceeds
        won = set_status(pub, eid, lambda e: (e["status"] == "PLANNED") and (e.update(status="GENERATING", requests={}) or True), "claim for generation")
        if not won:
            return "SKIP (claimed elsewhere)"
        for i, s in enumerate(ep["scenes"], 1):
            try:
                rid = client.submit(scene_params(ep, s))
            except hf.ApiError as e:  # 4xx rejected; reservation is HELD until CEO reconcile
                msg = str(e)[:200]
                budget.log_error(ctl, day, eid, f"rejected scene {i}: {msg}", now())
                set_status(pub, eid, lambda e_: e_.update(status="FAILED", error=msg) or True, "rejected")
                return f"FAILED (rejected: {msg}); reservation held until reconcile"
            except hf.AmbiguousSubmit as e:  # keep reservation, no retry
                set_status(pub, eid, lambda e_: e_.update(status="NEEDS_REVIEW", error="ambiguous submit") or True, "ambiguous submit")
                budget.log_error(ctl, day, eid, f"ambiguous submit scene {i}: {e}", now())
                return "NEEDS_REVIEW (ambiguous submit; reservation kept, no resubmit)"
            set_status(pub, eid, lambda e_, i=i, rid=rid: e_["requests"].__setitem__(str(i), rid) or True, f"request id scene {i}")
            budget.record_request(ctl, eid, lambda r, i=i, rid=rid: r.setdefault("scenes", {}).__setitem__(
                str(i), {"request_id": rid, "submitted_at": now(), "model": hf.MODEL, "status": "submitted"}))

    # GENERATING: poll only, download, hash, deliver.
    pub.sync()
    ep = episodes.load(pub.workdir, eid)
    if not live:
        return "DRY-RUN (would poll existing requests)"
    clips = []
    outdir = os.path.join(work, "clips", ep["date"], eid)
    os.makedirs(outdir, exist_ok=True)
    for i, s in enumerate(ep["scenes"], 1):
        rid = ep["requests"][str(i)]
        for _ in range(max_polls):
            st = client.status(rid)
            if st.get("status") in ("completed", "failed", "nsfw", "canceled"):
                break
            time.sleep(poll_s)
        else:
            return "STILL GENERATING (will resume next run; no resubmit)"
        if st["status"] != "completed":
            set_status(pub, eid, lambda e_: e_.update(status="FAILED", error=f"scene {i}: {st['status']}") or True, "generation failed")
            budget.log_error(ctl, day, eid, f"scene {i}: {st['status']}", now())
            return f"FAILED (scene {i}: {st['status']}); reservation held until reconcile"
        f = os.path.join(outdir, f"scene-{i:02d}.mp4")
        client.download(st["video"]["url"], f)  # immediately, before URL expiry
        clips.append({"scene": i, "file": f, "sha256": sha256(f), "request_id": rid,
                      "bytes": os.path.getsize(f), "video_url": st["video"]["url"]})
    deliver(inbox, ep, clips)
    ctl.sync()
    prices = budget.find_reserved(ctl.workdir, eid)
    if prices is not None:
        budget.settle(ctl, prices[0], eid, prices[1], now())

    def done(r):
        for c in clips:
            r.setdefault("scenes", {}).setdefault(str(c["scene"]), {}).update(
                request_id=c["request_id"], status="completed", video_url=c["video_url"],
                sha256=c["sha256"], bytes=c["bytes"])
        r["cost_usd"] = str(prices[1]) if prices else None
        r["cost_basis"] = "estimate (provider returns no actual charge)"
        r["completed_at"] = now()
    budget.record_request(ctl, eid, done)
    asset_paths = [os.path.join("clips", ep["date"], eid, os.path.basename(c["file"])) for c in clips]
    shas = {str(c["scene"]): c["sha256"] for c in clips}
    set_status(pub, eid, lambda e_: e_.update(status="GENERATED", asset_paths=asset_paths, sha256=shas,
                                               clips=[os.path.relpath(c["file"], work) for c in clips]) or True, "generated")
    return f"GENERATED ({len(clips)} clips delivered to inbox)"


def deliver(inbox, ep, clips):
    """Copy clips + SHA256 manifest into clips/<date>/<id>/ on the inbox branch."""
    def fn(root):
        d = os.path.join("clips", ep["date"], ep["id"])
        os.makedirs(os.path.join(root, d), exist_ok=True)
        paths = []
        for c in clips:
            rel = os.path.join(d, os.path.basename(c["file"]))
            with open(c["file"], "rb") as s, open(os.path.join(root, rel), "wb") as t:
                t.write(s.read())
            paths.append(rel)
        man = {"episode_id": ep["id"], "date": ep["date"], "hold": False, "test": False, "clips": [
            {"file": os.path.basename(c["file"]), "sha256": c["sha256"], "bytes": c["bytes"],
             "request_id": c["request_id"]} for c in clips]}
        mp = os.path.join(d, "manifest.json")
        with open(os.path.join(root, mp), "w") as f:
            json.dump(man, f, indent=2)
        return paths + [mp]
    inbox.transact(fn, f"clips: {ep['id']}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--max-episodes", type=int, default=episodes.EPISODES_PER_DAY,
                    help="new submissions this run (Phase D limited test: 1)")
    a = ap.parse_args(argv)
    work = os.environ.get("CROCO_WORK", "/tmp/croco-work")
    pub_remote = os.environ.get("CROCO_PUBLIC_REMOTE", "https://github.com/chloepark235711/croco-media")
    ctl_remote = os.environ.get("CROCO_CONTROL_REMOTE", "https://github.com/chloepark235711/croco-control")
    pub = GitStore(os.path.join(work, "pub"), pub_remote, os.environ.get("CROCO_PUBLIC_BRANCH", "main"))
    ctl = GitStore(os.path.join(work, "ctl"), ctl_remote, "main",
                   allowed=("ledger/", "errors/", "requests/"))
    inbox = GitStore(os.path.join(work, "inbox"), pub_remote, "inbox")
    for line in run(a.date, a.live, pub, ctl, inbox, work, max_new=a.max_episodes):
        print(line)


if __name__ == "__main__":
    main()
