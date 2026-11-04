"""08:00 production/publishing guard. Never generates; only consumes GENERATED episodes.

claim_edit -> mark_qa -> claim_publish -> record_published  (each a CAS commit)
An episode with youtube_post_id or status SCHEDULED can never be published twice.
"""
from . import episodes


class NotAllowed(Exception):
    pass


def _set(pub, eid, mutate, msg):
    def fn(root):
        ep = episodes.load(root, eid)
        mutate(ep)
        return [episodes.save(root, ep)]
    return pub.transact(fn, f"{eid}: {msg}")


def claim_edit(pub, eid):
    def m(ep):
        if ep["status"] != "GENERATED":
            raise NotAllowed(f"{eid} is {ep['status']}, not GENERATED")
        ep["status"] = "EDITED"
    _set(pub, eid, m, "editing")


def mark_qa(pub, eid, passed, notes):
    def m(ep):
        if ep["status"] != "EDITED":
            raise NotAllowed(f"{eid} is {ep['status']}, not EDITED")
        ep["status"] = "QA_PASSED" if passed else "QA_FAILED"
        ep["qa_notes"] = notes[:300]
    _set(pub, eid, m, "qa " + ("passed" if passed else "FAILED"))


def claim_publish(pub, eid):
    """Call BEFORE calling Metricool. Only QA_PASSED without a post id may proceed."""
    def m(ep):
        if ep["status"] != "QA_PASSED" or ep.get("youtube_post_id"):
            raise NotAllowed(f"{eid} not publishable ({ep['status']})")
        ep["status"] = "SCHEDULED"      # claimed; flips back only via record_published failure path
        ep["publish_claimed"] = True
    _set(pub, eid, m, "claim publish")


def record_published(pub, eid, post_id):
    def m(ep):
        ep["youtube_post_id"] = post_id
    _set(pub, eid, m, "published id recorded")
