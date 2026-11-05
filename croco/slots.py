"""Publishing slots: 2 Shorts per day at 12:00 and 17:00 America/Denver (owner decision
2026-11-02). Different episodes always get different slots; a slot that is already
taken (by a scheduled/published episode or an existing Metricool post) is never reused.
Test drafts ("[TEST]", "Do Not Publish") never occupy a slot.
"""
import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Denver")
SLOT_TIMES = ("12:00", "17:00")
LEAD = datetime.timedelta(minutes=30)   # never schedule a slot that starts in < 30 min


def denver_today(now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return now.astimezone(TZ).date().isoformat()


def slot_datetime(day, hhmm):
    """Aware datetime for e.g. ('2026-11-05', '12:00') in America/Denver (DST-correct)."""
    d = datetime.date.fromisoformat(day)
    h, m = map(int, hhmm.split(":"))
    return datetime.datetime(d.year, d.month, d.day, h, m, tzinfo=TZ)


def slot_key(day, hhmm):
    return f"{day}T{hhmm}"


def is_test_post(text):
    t = (text or "").lower()
    return "[test]" in t or "do not publish" in t or "pipeline test" in t


def occupied_from_episodes(episodes_):
    return {e["scheduled_slot"] for e in episodes_
            if e.get("scheduled_slot") and e.get("status") in ("SCHEDULED", "PUBLISHED")}


def next_free_slot(occupied, now=None, horizon_days=7):
    """First slot (from today on) that is not occupied and starts at least LEAD from now."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    start = datetime.date.fromisoformat(denver_today(now))
    for i in range(horizon_days):
        day = (start + datetime.timedelta(days=i)).isoformat()
        for hhmm in SLOT_TIMES:
            k = slot_key(day, hhmm)
            if k in occupied:
                continue
            if slot_datetime(day, hhmm) - now < LEAD:
                continue
            return k
    return None


def metricool_datetime(key):
    """'2026-11-05T12:00' -> ('2026-11-05T12:00:00', 'America/Denver') for createScheduledPost."""
    day, hhmm = key.split("T")
    return f"{day}T{hhmm}:00", "America/Denver"
