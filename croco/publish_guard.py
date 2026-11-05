"""08:00 production/publishing guard. Never generates; only consumes GENERATED episodes.

claim_edit -> mark_qa -> claim_publish -> record_metricool -> record_published
(each one a CAS commit on main). Guarantees:
- HOLD / QA_FAILED / NEEDS_REVIEW / any non-GENERATED episode can never be edited or published.
- One episode_id is scheduled at most once (status + youtube_post_id + metricool_post_id).
- Two episodes never share a slot (12:00 / 17:00 America/Denver) and never share a final
  file (sha256) or a source clip.
"""
from . import episodes, marketing, qa, slots


class NotAllowed(Exception):
    pass


def _set(pub, eid, mutate, msg):
    def fn(root):
        ep = episodes.load(root, eid)
        others = [o for o in episodes.all_episodes(root) if o["id"] != eid]
        mutate(ep, others)
        return [episodes.save(root, ep)]
    return pub.transact(fn, f"{eid}: {msg}")


def _refuse_hold(ep):
    if episodes.is_hold(ep):
        raise NotAllowed(f"{ep['id']} is HOLD (owner decision); never edited or published")


def claim_edit(pub, eid):
    def m(ep, others):
        _refuse_hold(ep)
        if ep["status"] != "GENERATED":
            raise NotAllowed(f"{eid} is {ep['status']}, not GENERATED")
        ep["status"] = "EDITED"
    _set(pub, eid, m, "editing")


def mark_qa(pub, eid, passed, notes, checklist=None):
    """passed=True is accepted only with a complete checklist (croco.qa.REQUIRED all True).
    passed=False always records QA_FAILED (blocking)."""
    if passed:
        ok, why = qa.evaluate(checklist)
        if not ok:
            raise NotAllowed(why)

    def m(ep, others):
        _refuse_hold(ep)
        if ep["status"] != "EDITED":
            raise NotAllowed(f"{eid} is {ep['status']}, not EDITED")
        ep["status"] = "QA_PASSED" if passed else "QA_FAILED"
        ep["qa_status"] = ep["status"]
        ep["qa_notes"] = (notes or "")[:300]
        if checklist is not None:
            ep["qa_checklist"] = {k: checklist.get(k) is True for k in qa.REQUIRED}
    _set(pub, eid, m, "qa " + ("passed" if passed else "FAILED"))


def claim_publish(pub, eid, slot, final_sha256):
    """Call BEFORE calling Metricool. Atomically reserves the slot for this episode.
    slot: 'YYYY-MM-DDTHH:MM' (one of croco.slots.SLOT_TIMES)."""
    day, _, hhmm = slot.partition("T")
    if hhmm not in slots.SLOT_TIMES:
        raise NotAllowed(f"slot must be one of {slots.SLOT_TIMES} America/Denver")
    if not final_sha256 or len(final_sha256) != 64:
        raise NotAllowed("final_sha256 of the rendered video is required")

    def m(ep, others):
        _refuse_hold(ep)
        if ep["status"] != "QA_PASSED" or ep.get("youtube_post_id") or ep.get("metricool_post_id"):
            raise NotAllowed(f"{eid} not publishable ({ep['status']})")
        errs, _ = marketing.check(ep)
        if errs:
            raise NotAllowed("marketing rules: " + "; ".join(errs))
        if slot in slots.occupied_from_episodes(others):
            raise NotAllowed(f"slot {slot} already taken by another episode")
        mine = set((ep.get("sha256") or {}).values())
        for o in others:
            if o.get("final_sha256") == final_sha256:
                raise NotAllowed(f"same final video already used by {o['id']}")
            if mine & set((o.get("sha256") or {}).values()):
                raise NotAllowed(f"source clip already used by {o['id']}")
        ep["status"] = "SCHEDULED"      # claimed; only a human resets it (see publish_failed)
        ep["publish_claimed"] = True
        ep["scheduled_slot"] = slot
        ep["final_sha256"] = final_sha256
    _set(pub, eid, m, f"claim publish {slot}")


def record_metricool(pub, eid, post_id, uuid=None):
    def m(ep, others):
        if ep["status"] != "SCHEDULED" or not ep.get("publish_claimed"):
            raise NotAllowed(f"{eid} has no publish claim")
        if ep.get("metricool_post_id") and ep["metricool_post_id"] != post_id:
            raise NotAllowed(f"{eid} already has Metricool post {ep['metricool_post_id']}")
        ep["metricool_post_id"] = post_id
        if uuid is not None:
            ep["metricool_post_uuid"] = uuid
    _set(pub, eid, m, "metricool post recorded")


def publish_failed(pub, eid, reason):
    """Metricool call failed or was ambiguous: park for a human (no automatic retry,
    because the post may exist). Slot stays reserved until a human resolves it."""
    def m(ep, others):
        if ep["status"] != "SCHEDULED":
            raise NotAllowed(f"{eid} is {ep['status']}, not SCHEDULED")
        ep["status"] = "NEEDS_REVIEW"
        ep["error"] = ("publish: " + (reason or ""))[:200]
    _set(pub, eid, m, "publish failed -> needs review")


def record_published(pub, eid, youtube_video_id):
    """Only after Metricool shows PUBLISHED with a YouTube video id (a schedule is not a publication)."""
    def m(ep, others):
        if ep["status"] not in ("SCHEDULED", "PUBLISHED") or not ep.get("publish_claimed"):
            raise NotAllowed(f"{eid} is {ep['status']}; nothing was scheduled")
        if ep.get("youtube_post_id") and ep["youtube_post_id"] != youtube_video_id:
            raise NotAllowed(f"{eid} already published as {ep['youtube_post_id']}")
        for o in others:
            if o.get("youtube_post_id") == youtube_video_id:
                raise NotAllowed(f"YouTube id already recorded for {o['id']}")
        ep["youtube_post_id"] = youtube_video_id
        ep["status"] = "PUBLISHED"
    _set(pub, eid, m, "published id recorded")
