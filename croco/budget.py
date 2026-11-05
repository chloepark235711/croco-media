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
import re
import subprocess
from decimal import Decimal

SAFETY_MARGIN = Decimal("0.10")  # estimates may drift; keep 10% headroom
OWNER_LOGIN = os.environ.get("CROCO_OWNER_LOGIN", "chloepark235711")
# An approval that an agent wrote "on behalf of" the CEO is not an approval.
AGENT_MARKERS = ("recorded by claude", "not a github-verified", "claude code", "on behalf of")
UNCONFIRMED_STATUSES = {"HOLD", "FAILED", "NEEDS_REVIEW"}


class NotApproved(Exception):
    pass


class OverBudget(Exception):
    pass


def load_approval(root, day):
    p = os.path.join(root, "approvals", "budget.json")
    if not os.path.exists(p):
        raise NotApproved("no budget approval record")
    with open(p) as f:
        a = json.load(f)
    if a.get("approved") is not True or a.get("enabled") is not True:
        raise NotApproved("approval not active (approved/enabled must both be true)")
    if not (a.get("approved_by") and a.get("approved_at")):
        raise NotApproved("approval missing approved_by/approved_at")
    if any(m in str(a["approved_by"]).lower() for m in AGENT_MARKERS):
        raise NotApproved("approval was recorded by an agent, not committed by the owner")
    if not (a["valid_from"] <= day <= a["valid_until"]):
        raise NotApproved(f"{day} outside approval window")
    cap = Decimal(str(a["daily_cap_usd"]))
    if cap <= 0 or cap > Decimal("5"):
        raise NotApproved("daily cap must be in (0, 5] USD")
    return cap


def _repo_slug(remote):
    m = re.search(r"github\.com[/:]([^/]+/[^/]+?)(?:\.git)?$", remote or "")
    return m.group(1) if m else None


def github_verifier(store):
    """Fail-closed provenance check: the latest commit that touched approvals/budget.json
    must be a GitHub-verified (signed) commit authored by the owner's GitHub account.
    Commits made in the GitHub web UI by the owner are signed by GitHub automatically."""
    sha = store._git("log", "-1", "--format=%H", "--", "approvals/budget.json", check=False).stdout.strip()
    slug = _repo_slug(store.remote)
    if not sha or not slug:
        raise NotApproved("cannot locate the approval commit")
    try:
        r = subprocess.run(["gh", "api", f"repos/{slug}/commits/{sha}",
                            "--jq", "[.commit.verification.verified, (.author.login // \"\")] | @tsv"],
                           capture_output=True, text=True, timeout=60)
    except Exception as e:
        raise NotApproved(f"cannot verify approval commit ({type(e).__name__})")
    if r.returncode != 0:
        raise NotApproved("cannot verify approval commit via GitHub API")
    verified, login = (r.stdout.strip().split("\t") + [""])[:2]
    if verified != "true" or login.lower() != OWNER_LOGIN.lower():
        raise NotApproved(f"approval commit {sha[:7]} is not a verified commit by {OWNER_LOGIN}")


def _events(root, day):
    p = os.path.join(root, "ledger", f"{day}.jsonl")
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [json.loads(l) for l in f if l.strip()]


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


def settle(store, day, episode_id, usd, now, basis="estimate (provider returns no actual charge)"):
    store.transact(lambda root: _append(root, day, {"type": "settle", "episode_id": episode_id,
                                                    "usd": str(usd), "basis": basis, "at": now}),
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


def find_reserved(root, episode_id):
    """(ledger_day, usd) of the episode's latest un-released reservation in any ledger file.
    A GENERATING episode may finish on a later day than the one it was reserved on."""
    d = os.path.join(root, "ledger")
    if not os.path.isdir(d):
        return None
    found = None
    for n in sorted(os.listdir(d)):
        if not n.endswith(".jsonl"):
            continue
        day = n[:-len(".jsonl")]
        ev = _events(root, day)
        if any(e["type"] == "release" and e["episode_id"] == episode_id for e in ev):
            continue
        for e in ev:
            if e["type"] == "reserve" and e["episode_id"] == episode_id:
                found = (day, Decimal(e["usd"]))
    return found


def unconfirmed(root, day, statuses):
    """Reservations on `day` whose real cost is unknown: neither settled nor released, and the
    episode is HOLD / FAILED / NEEDS_REVIEW (or unknown). While any exist, the safe remaining
    budget for that day cannot be computed, so no new paid request may be sent that day."""
    ev = _events(root, day)
    done = {e["episode_id"] for e in ev if e["type"] in ("settle", "release")}
    out = []
    for e in ev:
        if e["type"] == "reserve" and e["episode_id"] not in done:
            if statuses.get(e["episode_id"], "UNKNOWN") in UNCONFIRMED_STATUSES | {"UNKNOWN"}:
                out.append(e["episode_id"])
    return sorted(set(out))


def apply_reconcile(store, day, episode_id, now):
    """CEO-written reconcile/<id>.json resolves an unconfirmed reservation:
    {"resolved": "not_charged"} -> release; {"resolved": "charged", "usd": "0.40"} -> settle."""
    out = {}

    def fn(root):
        p = os.path.join(root, "reconcile", f"{episode_id}.json")
        if not os.path.exists(p):
            out["r"] = "held"
            return None
        with open(p) as f:
            rec = json.load(f)
        if rec.get("resolved") == "not_charged":
            out["r"] = "released"
            return _append(root, day, {"type": "release", "episode_id": episode_id,
                                       "reason": "CEO reconciliation: not charged", "at": now})
        if rec.get("resolved") == "charged" and rec.get("usd") is not None:
            out["r"] = "settled"
            return _append(root, day, {"type": "settle", "episode_id": episode_id, "usd": str(Decimal(str(rec["usd"]))),
                                       "basis": "CEO reconciliation: actual charge", "at": now})
        out["r"] = "held"
        return None
    store.transact(fn, f"ledger: reconcile {episode_id}")
    return out["r"]


def record_request(store, episode_id, update):
    """Private request record requests/<id>.json (request ids, video URLs, hashes, cost basis)."""
    def fn(root):
        os.makedirs(os.path.join(root, "requests"), exist_ok=True)
        rel = os.path.join("requests", f"{episode_id}.json")
        p = os.path.join(root, rel)
        rec = {"episode_id": episode_id}
        if os.path.exists(p):
            with open(p) as f:
                rec = json.load(f)
        update(rec)
        with open(p, "w") as f:
            json.dump(rec, f, indent=2, sort_keys=True)
            f.write("\n")
        return [rel]
    store.transact(fn, f"requests: {episode_id}")


def reconcile_release(store, day, episode_id, now):
    """Release a held reservation ONLY if the CEO placed reconcile/<id>.json
    ({"resolved": "not_charged", "by": ...}). Automation never decides this alone."""
    out = {}

    def fn(root):
        p = os.path.join(root, "reconcile", f"{episode_id}.json")
        resolved = None
        if os.path.exists(p):
            with open(p) as f:
                resolved = json.load(f).get("resolved")
        if resolved != "not_charged":
            out["r"] = "held"
            return None
        out["r"] = "released"
        return _append(root, day, {"type": "release", "episode_id": episode_id,
                                   "reason": "CEO reconciliation: not charged", "at": now})
    store.transact(fn, f"ledger: reconcile {episode_id}")
    return out["r"]
