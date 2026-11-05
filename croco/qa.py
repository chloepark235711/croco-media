"""08:00 quality / copyright / child-safety checklist (Quality & Copyright Department).

The checklist is filled in by the 08:00 reviewer after actually inspecting the rendered
video (frames, audio). Code cannot judge a video; it only refuses a PASS unless every
item was explicitly confirmed True. Every item is recorded as PASS / FAIL / UNVERIFIED:
an item that was not actually inspected must be left out (or None) and is recorded as
UNVERIFIED, which blocks publishing exactly like FAIL.
"""
REQUIRED = (
    "playback_ok",              # 1 final file opens and plays end to end (ffprobe + full decode)
    "all_scenes_present",       #   every planned scene clip exists, sha256 matches manifest
    "character_on_model",       # 2 matches croco/brand.py lock (mint-green, overalls, star, no teeth)
    "approved_characters_only", #   only Croco (+ Pebble); no other characters, people, brands
    "child_safety",             # 3 no dangerous behaviour to imitate, matches the safety note
    "educational_goal",         # 4 the learning_goal is clearly and correctly shown
    "copyright_trademark",      # 5 no third-party characters/songs/logos; only original/licensed SFX
    "video_quality",            # 6 no glitches / flicker / broken frames / flashing
    "no_text_artifacts",        #   no AI-generated garbled letters in the frames
    "audio_loudness",           # 7 audio present/clean, loudness measured within target
    "vertical_9_16",            # 8 final render is vertical 9:16, Shorts length
    "metadata_appropriate",     # 9 title/description/captions simple English, honest, kid-appropriate
    "no_duplicate",             # 10 not a re-upload: episode/file/source clip unused (also enforced in code)
)


def record(checklist):
    """{item: 'PASS'|'FAIL'|'UNVERIFIED'} for every REQUIRED item."""
    checklist = checklist or {}
    out = {}
    for k in REQUIRED:
        v = checklist.get(k)
        out[k] = "PASS" if v is True else "FAIL" if v is False else "UNVERIFIED"
    return out


def missing_items(checklist):
    return [k for k, v in record(checklist).items() if v != "PASS"]


def evaluate(checklist):
    """Return (passed, notes). Passed only when every REQUIRED item is exactly True."""
    rec = record(checklist)
    failed = [k for k, v in rec.items() if v == "FAIL"]
    unverified = [k for k, v in rec.items() if v == "UNVERIFIED"]
    if failed or unverified:
        parts = []
        if failed:
            parts.append("FAIL: " + ", ".join(failed))
        if unverified:
            parts.append("UNVERIFIED: " + ", ".join(unverified))
        return False, "QA blocked -> " + "; ".join(parts)
    return True, "QA passed: all checklist items confirmed"
