"""08:00 quality / copyright / child-safety checklist (Quality & Copyright Department).

The checklist is filled in by the 08:00 reviewer after actually inspecting the rendered
video (frames, audio). Code cannot judge a video; it only refuses a PASS unless every
item was explicitly confirmed True.
"""
REQUIRED = (
    "all_scenes_present",       # every planned scene clip exists, sha256 matches manifest
    "vertical_9_16",            # final render is vertical 9:16
    "video_quality",            # no glitches / flicker / broken frames / flashing
    "audio_loudness",           # loudness checked; only original or properly licensed SFX
    "character_on_model",       # matches croco/brand.py lock (mint-green, overalls, star, no teeth)
    "approved_characters_only", # only Croco (+ Pebble); no other characters, people, brands
    "copyright_trademark",      # no third-party characters/songs/logos/trademarks
    "child_safety",             # no dangerous behaviour to imitate, matches the safety note
    "educational_goal",         # the learning_goal is clearly shown
    "no_text_artifacts",        # no AI-generated garbled letters in the frames
)


def missing_items(checklist):
    checklist = checklist or {}
    return [k for k in REQUIRED if checklist.get(k) is not True]


def evaluate(checklist):
    """Return (passed, notes). Passed only when every REQUIRED item is exactly True."""
    miss = missing_items(checklist)
    if miss:
        return False, "QA blocked: not confirmed -> " + ", ".join(miss)
    return True, "QA passed: all checklist items confirmed"
