"""Pre-generation gate (V3, owner order 2026-11-16).

Runs BEFORE any paid Higgsfield request. Every check returns a list of problems;
any problem => do not generate, write the reason to the report.

    python3 -m croco.preflight plan.json      (exit 1 on any problem)

plan.json = {"spend_day": "YYYY-MM-DD", "ledger": "ledger/ledger.csv",
             "reference_root": ".", "references": ["reference/croco-face.png"],
             "published_titles": [...], "published_topics": [...],
             "occupied_slots": ["YYYY-MM-DDTHH:MM"], "now": "ISO-8601 with offset",
             "same_day_lead_minutes": 60, "retries_allowed": n,
             "price_per_second": "0.1257",
             "episodes": [{"id", "title", "topic", "slot", "scenes": [{"seconds", "prompt"}]}]}

Lessons encoded here (see LESSONS):
  L1 2026-11-13/16: reference/croco-face-2.png itself shows 4 small teeth -> Kling copies a
     row of 4-8 teeth regardless of the text ("exactly two teeth" does not override it).
     4/4 clips FAILED on 2026-11-16 ($2.01). => banned as a generation reference.
  L2 2026-11-16: a positive prompt that asks for visible teeth ("smile showing ... teeth")
     together with any toothy reference produced rows of teeth. => positive prompt must not
     request teeth; mouth line must be the closed-mouth line.
  L3 2026-11-14/15: croco-face.png only + closed-mouth lock + "closed-mouth smile" wording
     => 0 visible teeth in most clips (PASS). This is the verified configuration.
  L4 2026-11-16 S3: "happy smiles" / "look at the camera" endings drifted into a wide-open
     mouth; "happy closed-mouth smile" (11-15 S3) did not.
"""
import csv
import datetime
import hashlib
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

# --- references -------------------------------------------------------------
ALLOWED_REFERENCES = {
    "reference/croco-face.png": "fc7d52460e1c992f0083a8477c82287732f4c34b359ea3f5590ae2587b290141",
}
BANNED_REFERENCES = {
    "reference/croco-face-2.png": "L1: image shows 4 teeth -> rows of teeth (owner removed it 2026-11-16)",
    "reference/archive-croco-face-oops-v1.png": "archived v1 face, never use",
}

DAILY_CAP = Decimal("5.00")
LEDGER_FIELDS = ("date", "episode_id", "scene", "model", "seconds", "resolution",
                 "request_id", "status", "price_usd")

# --- prompt rules ------------------------------------------------------------
REQUIRED_MOUTH = ("Mouth detail: closed-mouth smile, no teeth visible at any time.",
                  "Mouth detail: closed-mouth smiles for both characters, no teeth visible at any time.")
REQUIRED_LOCK_PARTS = ("mint-green baby crocodile", "rounded head", "short snout", "rosy cheeks",
                       "chocolate-brown eyes", "closed-mouth smile with no visible teeth",
                       "orange dungaree overalls", "two small wooden buttons",
                       "yellow star embroidered on the front pocket")
REQUIRED_NEGATIVE_PARTS = ("no sharp teeth", "no rows of teeth", "no teeth", "no open mouth")
PEBBLE_PARTS = ("lavender baby turtle", "exactly three soft sky-blue round spots", "no clothing")
# open-mouth / toothy actions in the POSITIVE part of a prompt (L2, L4)
OPEN_MOUTH_TERMS = [
    r"open(?:ed|s|ing)? (?:his |her |its |their )?mouth", r"wide[- ]open", r"\bteeth\b", r"\btooth\b",
    r"\blaugh", r"\bgiggl", r"\bgrin", r"\byawn", r"\broar", r"\bshout", r"\bsing(?:s|ing)?\b",
    r"\bcheer", r"\bsays?\b", r"\btalk", r"\bspeak", r"\bbite", r"\bchew", r"\beat(?:s|ing)?\b",
    r"\bmoo(?:s|ing)?\b(?! sound)", r"\bbig smile", r"\bhappy smiles?\b",
]
SMILE_OK = re.compile(r"closed-mouth smiles?")


def positive(prompt):
    return prompt.split("Negative:")[0]


def check_references(refs, root="."):
    errs = []
    if not refs:
        errs.append("no face reference (verified config needs reference/croco-face.png)")
    for r in refs:
        if r in BANNED_REFERENCES:
            errs.append(f"banned reference {r}: {BANNED_REFERENCES[r]}")
            continue
        if r not in ALLOWED_REFERENCES:
            errs.append(f"unapproved reference {r}")
            continue
        p = os.path.join(root, r)
        if not os.path.isfile(p):
            errs.append(f"reference file missing: {r}")
            continue
        with open(p, "rb") as fh:
            h = hashlib.sha256(fh.read()).hexdigest()
        if h != ALLOWED_REFERENCES[r]:
            errs.append(f"reference sha256 mismatch: {r}")
    return errs


def check_prompt(prompt, pebble=None):
    """Brand / mouth / outfit consistency of one scene prompt."""
    errs = []
    pos = positive(prompt)
    for part in REQUIRED_LOCK_PARTS:
        if part not in pos:
            errs.append(f"character lock part missing: {part!r}")
    if not any(m in pos for m in REQUIRED_MOUTH):
        errs.append("closed-mouth Mouth detail line missing (L2/L3)")
    if "Negative:" not in prompt:
        errs.append("Negative line missing")
    else:
        neg = prompt.split("Negative:", 1)[1]
        for part in REQUIRED_NEGATIVE_PARTS:
            if part not in neg:
                errs.append(f"negative part missing: {part!r}")
    # teeth/open-mouth requests: ignore the approved lock/mouth wording itself
    scan = pos
    for ok in ("closed-mouth smile with no visible teeth", "no teeth visible at any time",
               "a gentle closed-mouth smile"):
        scan = scan.replace(ok, "")
    scan = SMILE_OK.sub("", scan).lower()
    for t in OPEN_MOUTH_TERMS:
        m = re.search(t, scan)
        if m:
            errs.append(f"open-mouth/teeth wording in positive prompt: {m.group(0)!r} (L2/L4)")
    if pebble is None:
        pebble = "Pebble" in pos
    if pebble:
        for part in PEBBLE_PARTS:
            if part not in pos:
                errs.append(f"Pebble lock part missing: {part!r}")
    return errs


def ledger_total(path, day):
    total = Decimal("0")
    if not os.path.isfile(path):
        return total
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("date") == day and row.get("status") != "not_charged":
                total += Decimal(row.get("price_usd") or "0")
    return total


def episode_cost(ep, pps, retries):
    """(base, max) cost; max adds the `retries` most expensive scenes."""
    secs = sorted((int(s["seconds"]) for s in ep["scenes"]), reverse=True)
    base = sum(secs) * pps
    extra = sum(secs[:retries]) * pps
    q = Decimal("0.0001")
    return base.quantize(q, ROUND_HALF_UP), (base + extra).quantize(q, ROUND_HALF_UP)


def check_budget(spent, eps, pps, retries, cap=DAILY_CAP):
    errs, run = [], spent
    if pps is None or pps <= 0:
        return ["price per second unknown -> do not generate"], run
    for ep in eps:
        _, mx = episode_cost(ep, pps, retries)
        if run + mx > cap:
            errs.append(f"{ep['id']}: max cost ${mx} + spent ${run} > cap ${cap}")
        run += mx
    return errs, run


def check_duplicates(eps, published_titles, published_topics):
    errs = []
    pt = {t.strip().lower() for t in published_titles}
    pk = {t.strip().lower() for t in published_topics}
    seen = set()
    for ep in eps:
        if ep["title"].strip().lower() in pt:
            errs.append(f"{ep['id']}: title already published")
        if ep.get("topic", "").strip().lower() in pk:
            errs.append(f"{ep['id']}: topic already published")
        if ep["title"] in seen:
            errs.append(f"{ep['id']}: duplicate title in this plan")
        seen.add(ep["title"])
    return errs


def check_slots(eps, occupied, now, lead_minutes=60):
    errs, used = [], set(occupied)
    for ep in eps:
        s = ep.get("slot")
        if not s:
            errs.append(f"{ep['id']}: no slot")
            continue
        day, _, hhmm = s.partition("T")
        if hhmm not in ("12:00", "17:00"):
            errs.append(f"{ep['id']}: slot {s} is not 12:00/17:00")
        dt = datetime.datetime.fromisoformat(s).replace(tzinfo=now.tzinfo)
        if dt - now < datetime.timedelta(minutes=lead_minutes):
            errs.append(f"{ep['id']}: slot {s} is less than {lead_minutes} min ahead")
        if s in used:
            errs.append(f"{ep['id']}: slot {s} already occupied")
        used.add(s)
    return errs


def run(plan):
    root = plan.get("reference_root", ".")
    probs = {}
    probs["1_reference_conflict"] = check_references(plan.get("references", []), root)
    probs["2_3_prompt_mouth_face_outfit"] = [
        f"{ep['id']} scene {i + 1}: {e}" for ep in plan["episodes"]
        for i, s in enumerate(ep["scenes"]) for e in check_prompt(s["prompt"])]
    files = [p for p in (plan.get("ledger"),) if p and not os.path.isfile(p)]
    probs["4_files"] = [f"missing file: {p}" for p in files]
    probs["5_duplicates"] = check_duplicates(plan["episodes"], plan.get("published_titles", []),
                                             plan.get("published_topics", []))
    pps = Decimal(plan["price_per_second"]) if plan.get("price_per_second") else None
    spent = ledger_total(plan.get("ledger", ""), plan["spend_day"])
    berr, tot = check_budget(spent, plan["episodes"], pps, int(plan.get("retries_allowed", 0)))
    probs["6_budget"] = berr
    now = datetime.datetime.fromisoformat(plan["now"])
    probs["7_slots"] = check_slots(plan["episodes"], plan.get("occupied_slots", []), now,
                                   int(plan.get("same_day_lead_minutes", 60)))
    return {"ok": not any(probs.values()), "spent": str(spent), "max_after": str(tot),
            "problems": probs}


if __name__ == "__main__":
    res = run(json.load(open(sys.argv[1])))
    print(json.dumps(res, indent=1, ensure_ascii=False))
    sys.exit(0 if res["ok"] else 1)
