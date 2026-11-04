"""python3 -m croco.plan_check YYYY-MM-DD  -> validates that day's plans (exit 1 on problems)."""
import sys
from . import episodes

def main(date, root="."):
    eps = [e for e in episodes.all_episodes(root) if e["date"] == date]
    bad = 0
    if len(eps) != episodes.EPISODES_PER_DAY:
        print(f"expected {} episodes for {date}, found {len(eps)}".format(episodes.EPISODES_PER_DAY)); bad = 1
    for e in eps:
        others = [o for o in episodes.all_episodes(root) if o["id"] != e["id"]]
        for p in episodes.validate(e, others):
            print(f"{e['id']}: {p}"); bad = 1
    print("OK" if not bad else "PROBLEMS"); return bad

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
