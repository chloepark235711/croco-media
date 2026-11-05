"""python3 -m croco.plan_check YYYY-MM-DD [root]  -> validates that day's plans (exit 1 on problems).

Checks: exactly EPISODES_PER_DAY active (non-HOLD) episodes, total scene seconds <= 30,
brand-bible character lock in every scene, copyright/safety blocklist, unique
topic_key / source_episode across ALL episodes (HOLD included), marketing/SEO rules.
"""
import sys

from . import episodes, marketing, slots


def main(date, root="."):
    every = episodes.all_episodes(root)
    eps = [e for e in every if e.get("date") == date]
    active = [e for e in eps if episodes.is_active(e)]
    bad = 0
    for e in eps:
        if not episodes.is_active(e):
            print(f"{e['id']}: HOLD (not counted, never generated or published)")
    if len(active) != episodes.EPISODES_PER_DAY:
        print(f"expected {episodes.EPISODES_PER_DAY} active episodes for {date}, found {len(active)}")
        bad = 1
    secs = sum(episodes.scene_seconds(e) for e in active)
    if secs > episodes.MAX_SECONDS_PER_DAY:
        print(f"total scene seconds {secs} > {episodes.MAX_SECONDS_PER_DAY} (daily budget)")
        bad = 1
    targets = [e.get("target_slot") for e in active if e.get("target_slot")]
    if len(targets) != len(set(targets)):
        print(f"two active episodes share a target_slot: {targets}")
        bad = 1
    for t in targets:
        day, _, hhmm = t.partition("T")
        if day != date or hhmm not in slots.SLOT_TIMES:
            print(f"target_slot {t} must be {date}T12:00 or {date}T17:00 (America/Denver)")
            bad = 1
    for e in active:
        others = [o for o in every if o["id"] != e["id"]]
        for p in episodes.validate(e, others):
            print(f"{e['id']}: {p}")
            bad = 1
        if e.get("status") == "PLANNED":
            errs, warns = marketing.check(e)
            for p in errs:
                print(f"{e['id']}: marketing: {p}")
                bad = 1
            for w in warns:
                print(f"{e['id']}: warning: {w}")
    print("OK" if not bad else "PROBLEMS")
    return bad


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], *(sys.argv[2:3] or ["."])))
