"""Marketing / SEO rules for audience-facing text (checked before planning is accepted
and again before publishing). Rules come from the owner-approved documents only:
brand bible (naming, hashtag rules) and the 08:00 task's marketing addendum (M2).
"""
import re

REQUIRED_HASHTAG = "#CrocosLittleWorld"
FORBIDDEN_WORDS = ["momo", "#momothecroc"]
TITLE_SUFFIX = "| Croco's Little World #Shorts"
TITLE_MAX = 100          # YouTube hard limit
TITLE_SOFT_MAX = 70      # M2: "ideally <= 70 characters" (warning only)
HASHTAGS_MIN, HASHTAGS_MAX = 3, 5
TAGS_MIN, TAGS_MAX = 5, 10
CHILD_DIRECTED_CTA = re.compile(r"\b(subscribe|like and subscribe|hit the bell|comment below)\b", re.I)


def check(ep):
    """Return (errors, warnings) for one episode's SEO package."""
    errs, warns = [], []
    title = ep.get("title") or ""
    desc = ep.get("description") or ""
    tags = ep.get("tags") or []
    hashtags = ep.get("hashtags") or []

    if not title.endswith(TITLE_SUFFIX):
        errs.append(f"title must end with '{TITLE_SUFFIX}' (MX-01 format)")
    if len(title) > TITLE_MAX:
        errs.append(f"title longer than {TITLE_MAX} characters")
    elif len(title) > TITLE_SOFT_MAX:
        warns.append(f"title longer than {TITLE_SOFT_MAX} characters")
    words = re.findall(r"[A-Za-z]{4,}", title.replace(TITLE_SUFFIX, ""))
    if any(w.isupper() for w in words):
        errs.append("no ALL CAPS words in the title")

    all_text = " ".join([title, desc, " ".join(tags), " ".join(hashtags)]).lower()
    for w in FORBIDDEN_WORDS:
        if re.search(rf"(?<![\w#]){re.escape(w)}\b", all_text) or (w.startswith("#") and w in all_text):
            errs.append(f"forbidden name/tag: {w}")
    if CHILD_DIRECTED_CTA.search(desc):
        errs.append("no subscribe/like requests in a made-for-kids description")

    if not HASHTAGS_MIN <= len(hashtags) <= HASHTAGS_MAX:
        errs.append(f"hashtags must be {HASHTAGS_MIN}-{HASHTAGS_MAX}")
    if REQUIRED_HASHTAG not in hashtags:
        errs.append(f"hashtags must include {REQUIRED_HASHTAG}")
    for h in hashtags:
        if not re.fullmatch(r"#[A-Za-z0-9]+", h):
            errs.append(f"bad hashtag (letters/digits only, no apostrophes): {h}")
    if len(set(h.lower() for h in hashtags)) != len(hashtags):
        errs.append("duplicate hashtags")

    if not TAGS_MIN <= len(tags) <= TAGS_MAX:
        errs.append(f"youtube tags must be {TAGS_MIN}-{TAGS_MAX}")
    if ep.get("made_for_kids") is not True:
        errs.append("made_for_kids must be true")
    return errs, warns
