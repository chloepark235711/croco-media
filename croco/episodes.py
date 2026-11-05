"""Episode records (public, non-sensitive) at briefings/episodes/<id>.json.

Status machine (each transition is a CAS commit, see gitstore):
PLANNED -> GENERATING -> GENERATED -> EDITED -> QA_PASSED -> SCHEDULED -> PUBLISHED
failures: SKIPPED_BUDGET, FAILED, NEEDS_REVIEW (ambiguous), QA_FAILED
HOLD: frozen by an owner decision. Never submitted, never re-submitted, never polled,
      never edited or published, and it does not occupy one of the day's 2 slots.
No money amounts, approvals or keys are ever stored here.
"""
import json
import os
import re

from . import brand

STATUSES = {"PLANNED", "GENERATING", "GENERATED", "EDITED", "QA_PASSED", "SCHEDULED",
            "PUBLISHED", "SKIPPED_BUDGET", "FAILED", "NEEDS_REVIEW", "QA_FAILED", "HOLD"}
INACTIVE = {"HOLD"}                       # statuses that never count toward the daily plan
ID_RE = re.compile(r"^\d{8}-0[1-9]$")
# crude copyright/safety screen for plans (positive prompt text only; the brand
# Negative line legitimately says "no scary expressions"). Real QA happens at 08:00.
BLOCKLIST = ["disney", "pixar", "pokemon", "mario", "peppa", "cocomelon", "baby shark",
             "paw patrol", "bluey", "spiderman", "marvel", "frozen", "mickey", "pinkfong",
             "babybus", "super simple songs", "ninja turtle", "ninja turtles",
             "gun", "blood", "kill", "knife", "scary", "horror"]
DIR = os.path.join("briefings", "episodes")
MAX_SCENES = 3          # 5s clip ~ $0.668 -> 2 episodes x 3 clips ~ $4.01 (+10% margin 4.41) <= $5
MIN_SCENE_SECONDS = 3
MAX_SCENE_SECONDS = 5
MAX_SECONDS_PER_DAY = 30
EPISODES_PER_DAY = 2


def path(root, eid):
    return os.path.join(root, DIR, f"{eid}.json")


def load(root, eid):
    with open(path(root, eid)) as f:
        return json.load(f)


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
    out = []
    for n in sorted(os.listdir(d)):
        if n.endswith(".json"):
            with open(os.path.join(d, n)) as f:
                out.append(json.load(f))
    return out


def is_hold(ep):
    return ep.get("status") == "HOLD" or ep.get("hold") is True


def is_active(ep):
    return not is_hold(ep) and ep.get("status") not in INACTIVE


def _screen_text(ep):
    """Text that must be free of blocked terms: everything except the brand Negative lines."""
    e = dict(ep)
    e["scenes"] = [dict(s, prompt=brand.positive_part(s.get("prompt", ""))) for s in ep.get("scenes") or []]
    e.pop("character_lock", None)
    e.pop("hold_reason", None)
    e.pop("safety", None)     # safety notes describe what NOT to do ("no hot water", ...)
    return json.dumps(e, ensure_ascii=False).lower()


def validate(ep, existing=(), brand_check=True):
    """Return list of problems (empty = ok). HOLD records are frozen: only id/status are checked."""
    errs = []
    if not ID_RE.match(ep.get("id", "")):
        errs.append("id must look like YYYYMMDD-01")
    if ep.get("status") not in STATUSES:
        errs.append("bad status")
    if is_hold(ep):
        return errs
    for k in ("date", "title", "description", "learning_goal", "topic_key"):
        if not ep.get(k):
            errs.append(f"missing {k}")
    if not ep.get("tags"):
        errs.append("missing tags")
    scenes = ep.get("scenes") or []
    if not scenes:
        errs.append("no scenes")
    if len(scenes) > MAX_SCENES:
        errs.append(f"max {MAX_SCENES} scenes per episode (budget)")
    for i, s in enumerate(scenes, 1):
        d = s.get("duration")
        if not s.get("prompt") or not isinstance(d, int) or isinstance(d, bool) \
                or not MIN_SCENE_SECONDS <= d <= MAX_SCENE_SECONDS:
            errs.append(f"scene {i}: needs prompt and integer duration 3-5")
        elif brand_check:
            errs += [f"scene {i}: {p}" for p in brand.check_scene(s["prompt"])]
    if brand_check and ep.get("character_lock") != brand.CHARACTER_LOCK:
        errs.append("character_lock must equal the brand-bible character lock verbatim")
    text = _screen_text(ep)
    errs += [f"blocked term: {w}" for w in BLOCKLIST if re.search(rf"\b{re.escape(w)}\b", text)]
    for o in existing:
        if o.get("id") == ep.get("id"):
            continue
        if o.get("topic_key") == ep.get("topic_key"):
            errs.append(f"duplicate topic_key with {o['id']}")
        if ep.get("source_episode") and o.get("source_episode") == ep.get("source_episode"):
            errs.append(f"duplicate source_episode {ep['source_episode']} with {o['id']}")
    return errs


def scene_seconds(ep):
    return sum(s.get("duration", 0) for s in ep.get("scenes") or [])
