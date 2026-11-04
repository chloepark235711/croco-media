"""Episode records (public, non-sensitive) at briefings/episodes/<id>.json.

Status machine (each transition is a CAS commit, see gitstore):
PLANNED -> GENERATING -> GENERATED -> EDITED -> QA_PASSED -> SCHEDULED
failures: SKIPPED_BUDGET, FAILED, NEEDS_REVIEW (ambiguous), QA_FAILED
No money amounts, approvals or keys are ever stored here.
"""
import json
import os
import re

STATUSES = {"PLANNED", "GENERATING", "GENERATED", "EDITED", "QA_PASSED", "SCHEDULED",
            "SKIPPED_BUDGET", "FAILED", "NEEDS_REVIEW", "QA_FAILED"}
ID_RE = re.compile(r"^\d{8}-0[1-9]$")
# crude copyright/safety screen for plans; real QA happens again at 08:00
BLOCKLIST = ["disney", "pixar", "pokemon", "mario", "peppa", "cocomelon", "baby shark",
             "paw patrol", "bluey", "spiderman", "marvel", "frozen", "mickey",
             "gun", "blood", "kill", "knife", "scary", "horror"]
DIR = os.path.join("briefings", "episodes")


def path(root, eid):
    return os.path.join(root, DIR, f"{eid}.json")


def load(root, eid):
    return json.load(open(path(root, eid)))


def save(root, ep):
    os.makedirs(os.path.join(root, DIR), exist_ok=True)
    p = path(root, ep["id"])
    with open(p, "w") as f:
        json.dump(ep, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    return os.path.relpath(p, root)


def all_episodes(root):
    d = os.path.join(root, DIR)
    if not os.path.isdir(d):
        return []
    return [json.load(open(os.path.join(d, n))) for n in sorted(os.listdir(d))
            if n.endswith(".json")]


def validate(ep, existing=()):
    """Return list of problems (empty = ok)."""
    errs = []
    if not ID_RE.match(ep.get("id", "")):
        errs.append("id must look like YYYYMMDD-01")
    if ep.get("status") not in STATUSES:
        errs.append("bad status")
    for k in ("date", "title", "description", "learning_goal", "topic_key"):
        if not ep.get(k):
            errs.append(f"missing {k}")
    if not ep.get("tags"):
        errs.append("missing tags")
    scenes = ep.get("scenes") or []
    if not scenes:
        errs.append("no scenes")
    for i, s in enumerate(scenes, 1):
        d = s.get("duration")
        if not s.get("prompt") or not isinstance(d, int) or not 3 <= d <= 30:
            errs.append(f"scene {i}: needs prompt and integer duration 3-30")
    text = json.dumps(ep, ensure_ascii=False).lower()
    errs += [f"blocked term: {w}" for w in BLOCKLIST if re.search(rf"\b{re.escape(w)}\b", text)]
    for o in existing:
        if o["id"] != ep.get("id") and o.get("topic_key") == ep.get("topic_key"):
            errs.append(f"duplicate topic_key with {o['id']}")
    return errs
