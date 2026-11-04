"""Private budget control (lives in the PRIVATE croco-control repo, never here).

Layout inside croco-control:
  approvals/budget.json      {"approved": true, "enabled": true, "daily_cap_usd": "5.00",
                              "valid_from": "YYYY-MM-DD", "valid_until": "YYYY-MM-DD",
                              "approved_by": "...", "approved_at": "..."}
  ledger/YYYY-MM-DD.jsonl    append-only events: reserve / settle / release
  requests/<episode>.json    generation request state
  errors/YYYY-MM-DD.jsonl    error log

Fail-closed: no valid approval => nothing is reserved => nothing is generated.
"""
import json
import os
from decimal import Decimal

SAFETY_MARGIN = Decimal("0.10")  # estimates may drift; keep 10% headroom


class NotApproved(Exception):
    pass


class OverBudget(Exception):
    pass


def load_approval(root, day):
    p = os.path.join(root, "approvals", "budget.json")
    if not os.path.exists(p):
        raise NotApproved("no budget approval record")
    a = json.load(open(p))
    if a.get("approved") is not True or a.get("enabled") is not True:
        raise NotApproved("approval not active (approved/enabled must both be true)")
    if not (a.get("approved_by") and a.get("approved_at")):
        raise NotApproved("approval missing approved_by/approved_at")
    if not (a["valid_from"] <= day <= a["valid_until"]):
        raise NotApproved(f"{day} outside approval window")
    cap = Decimal(str(a["daily_cap_usd"]))
    if cap <= 0 or cap > Decimal("5"):
        raise NotApproved("daily cap must be in (0, 5] USD")
    return cap


def _events(root, day):
    p = os.path.join(root, "ledger", f"{day}.jsonl")
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]


def committed_total(events):
    """Sum of money that is reserved or spent and not released."""
    res, rel, settled = {}, set(), {}
    for e in events:
        if e["type"] == "reserve":
            res[e["episode_id"]] = Decimal(e["usd"])
        elif e["type"] == "release":
            rel.add(e["episode_id"])
        elif e["type"] == "settle":
            settled[e["episode_id"]] = Decimal(e["usd"])
    total = Decimal(0)
    for ep, amt in res.items():
        if ep in rel:
            continue
        total += max(amt, settled.get(ep, Decimal(0)))
    return total


def _append(root, day, event):
    d = os.path.join(root, "ledger")
    os.makedirs(d, exist_ok=True)
    rel = os.path.join("ledger", f"{day}.jsonl")
    with open(os.path.join(root, rel), "a") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")
    return [rel]


def reserve(store, day, episode_id, usd, now):
    """Atomically reserve `usd` for episode_id. Idempotent per episode.
    Returns 'reserved' or 'exists'. Raises NotApproved / OverBudget."""
    usd = Decimal(str(usd))
    out = {}

    def fn(root):
        cap = load_approval(root, day)
        if store.bot_touched("approvals"):
            raise NotApproved("approvals/ was modified by the automation identity; refusing")
        ev = _events(root, day)
        for e in ev:
            if e["type"] == "reserve" and e["episode_id"] == episode_id and not any(
                    x["type"] == "release" and x["episode_id"] == episode_id for x in ev):
                out["r"] = "exists"
                return None
        total = committed_total(ev)
        if (total + usd) * (1 + SAFETY_MARGIN) > cap:
            raise OverBudget(f"committed {total} + {usd} (+10% margin) exceeds cap {cap}")
        out["r"] = "reserved"
        return _append(root, day, {"type": "reserve", "episode_id": episode_id,
                                   "usd": str(usd), "at": now})

    store.transact(fn, f"ledger: reserve {episode_id} ${usd}")
    return out["r"]


def settle(store, day, episode_id, usd, now):
    store.transact(lambda root: _append(root, day, {"type": "settle", "episode_id": episode_id,
                                                    "usd": str(usd), "at": now}),
                   f"ledger: settle {episode_id}")


def release(store, day, episode_id, now, reason):
    """Only call when it is CERTAIN no charge occurred (e.g. request never sent)."""
    store.transact(lambda root: _append(root, day, {"type": "release", "episode_id": episode_id,
                                                    "reason": reason, "at": now}),
                   f"ledger: release {episode_id}")


def log_error(store, day, episode_id, message, now):
    def fn(root):
        os.makedirs(os.path.join(root, "errors"), exist_ok=True)
        rel = os.path.join("errors", f"{day}.jsonl")
        with open(os.path.join(root, rel), "a") as f:
            f.write(json.dumps({"episode_id": episode_id, "error": message[:500], "at": now}) + "\n")
        return [rel]
    store.transact(fn, f"error: {episode_id}")


def reserved_amount(root, day, episode_id):
    for e in _events(root, day):
        if e["type"] == "reserve" and e["episode_id"] == episode_id:
            return Decimal(e["usd"])
    return None


def reconcile_release(store, day, episode_id, now):
    """Release a held reservation ONLY if the CEO placed reconcile/<id>.json
    ({"resolved": "not_charged", "by": ...}). Automation never decides this alone."""
    out = {}

    def fn(root):
        p = os.path.join(root, "reconcile", f"{episode_id}.json")
        if not os.path.exists(p) or json.load(open(p)).get("resolved") != "not_charged":
            out["r"] = "held"
            return None
        out["r"] = "released"
        return _append(root, day, {"type": "release", "episode_id": episode_id,
                                   "reason": "CEO reconciliation: not charged", "at": now})
    store.transact(fn, f"ledger: reconcile {episode_id}")
    return out["r"]
