"""Competitor-channel research for the 17:00 marketing meeting (YouTube Data API v3, read-only).

    python3 -m croco.competitors run  --state DIR [--out DIR] [--reevaluate] [--date YYYY-MM-DD]
    python3 -m croco.competitors plan --state DIR          # quota plan only, no API call

What it does
- Weekly (or when no selection exists / --reevaluate): discovers candidate channels across
  six scopes, scores them on content similarity, audience (made-for-kids share), recent
  upload activity and public video performance, keeps 10 candidates and tracks the top 5.
- Daily: refreshes the 5 tracked channels (recent uploads + public stats) and runs one
  small trend search, then writes report.md (Korean meeting section) and data.json.

Only public data that the API actually returns is reported. Retention, CTR and
subscriber conversion of other channels are NOT available through this API and are
never estimated. Subscriber change is reported only against a previously stored
public snapshot.

Safety
- Key, two modes:
  * CROCO_YT_AUTH=proxy (cloud): no key in the VM at all. The cloud environment's
    network secret (host www.googleapis.com, header X-Goog-Api-Key) is attached by
    Anthropic's agent proxy after the request leaves the session.
  * default (local): env YOUTUBE_API_KEY, else the file in CROCO_YOUTUBE_ENV (default
    ~/.config/croco/youtube.env).
  The key is sent only in the X-Goog-Api-Key header, never in a URL, never printed, never
  written to state/cache; any echo in an error body is redacted.
- Fail-safe: a network/auth/quota error (HTTP 0/400 keyInvalid/401/403/429) opens a circuit
  breaker -> no further network calls in this run; 3 consecutive other errors do the same.
  A run-time budget (CROCO_YT_DEADLINE_SEC, default 300 s) stops new calls. `run` never
  raises: it prints "BLOCKED: ..." (exit 3) and still saves the ledger, so the meeting
  continues without this section.
- Quota: official costs (developers.google.com/youtube/v3/determine_quota_cost, page
  updated 2026-11-03): list methods 1 unit; search.list 1 unit per call from its own
  bucket of 100 calls/day; invalid requests still cost >= 1; reset at midnight PT.
  Internal caps (owner order 2026-11-09): 500 units/day total, search calls <= 20/day.
  Every call is logged in the state ledger; a call that would cross a cap is refused.
- Cache + de-duplication: identical requests (key excluded) are served from the state
  cache within their TTL and cost 0 units.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import ssl
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

API = "https://www.googleapis.com/youtube/v3/"
PT = ZoneInfo("America/Los_Angeles")      # YouTube quota day
MT = ZoneInfo("America/Denver")           # Croco operating day
COST = {"search": 1, "channels": 1, "playlistItems": 1, "videos": 1}
DAILY_UNIT_CAP = int(os.environ.get("CROCO_YT_DAILY_CAP", "500"))
DAILY_SEARCH_CAP = int(os.environ.get("CROCO_YT_SEARCH_CAP", "20"))
TTL_HOURS = {"search": 20, "channels": 20, "playlistItems": 6, "videos": 6}
DEADLINE_SEC = int(os.environ.get("CROCO_YT_DEADLINE_SEC", "300"))
AUTH_MODE = os.environ.get("CROCO_YT_AUTH", "key")      # "key" | "proxy"
FATAL_CODES = {0, 401, 403, 429}
REEVALUATE_DAYS = 7
N_CANDIDATES, N_TRACKED = 10, 5
MID_SIZE_MAX_SUBS = 1_000_000
SHORTS_MAX_SECONDS = 180               # YouTube Shorts length limit (since 2024-10)            # "성장 중인 중소형" boundary (public, rounded counts)
OWN_CHANNEL_MARKERS = ("croco's little world", "crocos little world")

# Six owner-defined scopes. Each is one search.list call (type=video, Shorts length,
# last 30 days, safeSearch strict) -> channels that actually post such content now.
SCOPES = [
    ("글로벌 키즈 애니메이션", "kids cartoon animation shorts"),
    ("동물 캐릭터 Shorts", "cute animal cartoon shorts for kids"),
    ("어린이 교육용 애니메이션", "preschool learning animation toddlers"),
    ("짧은 스토리 가족 친화", "short story cartoon for kids family friendly"),
    ("성장 중인 중소형 키즈 채널", "new 3d animated kids channel shorts"),
]
# Scope 6 ("대형 키즈 브랜드의 콘텐츠 전략"): resolved by handle, 1 unit each.
BRAND_HANDLES = ["@CoComelon", "@Pinkfong", "@BabyBus", "@SuperSimpleSongs", "@LittleBabyBum"]
DAILY_TREND_QUERY = "kids shorts cartoon"

# Title/description keyword classification (automatic, label it as such in reports).
TOPICS = {
    "동물": r"animal|croc|dino|duck|cat|dog|puppy|kitten|bunny|rabbit|bear|panda|elephant|lion|fish|shark|turtle|frog|pig|cow|farm|zoo",
    "색·숫자·글자": r"colou?r|number|count|abc|alphabet|letter|shape|phonics",
    "생활습관": r"wash|brush|teeth|potty|bath|sleep|bed ?time|eat|dinner|clean|tidy|dress|healthy",
    "감정·친구·예절": r"sorry|share|sharing|friend|kind|feel|emotion|happy|sad|angry|thank|please|turn",
    "탈것": r"car|truck|bus|train|plane|tractor|fire ?truck|police|vehicle",
    "음식": r"fruit|apple|banana|strawberry|ice ?cream|cake|cook|food|snack|vegetable",
    "놀이·안전": r"play|toy|playground|ball|block|hide|seek|safety|careful|doctor|boo ?boo",
}
FORMATS = {
    "노래·동요": r"songs?|sing|nursery|rhymes?|music|dance",
    "학습": r"learn|educational|lesson|for toddlers|preschool|kindergarten",
    "스토리": r"story|adventure|episode|surprise|oops|lost|found|rescue",
    "율동·따라하기": r"move|dance|exercise|yoga|follow|copy|stretch|freeze",
}
SIMILARITY_TERMS = r"animal|baby|cute|toddler|preschool|kids|story|learn|friend|kind|croc|turtle|3d|animation|cartoon"


def _ssl_context():
    """System CA bundle; falls back to certifi or macOS /etc/ssl/cert.pem (python.org builds ship no CAs)."""
    cafile = os.environ.get("SSL_CERT_FILE")
    if not cafile:
        try:
            import certifi
            cafile = certifi.where()
        except ImportError:
            if not ssl.get_default_verify_paths().cafile and os.path.exists("/etc/ssl/cert.pem"):
                cafile = "/etc/ssl/cert.pem"
    return ssl.create_default_context(cafile=cafile)


class QuotaCapReached(RuntimeError):
    """Internal cap, deadline or open circuit: stop calling, keep what we have."""


class ApiError(RuntimeError):
    def __init__(self, code, reason):
        super().__init__(f"HTTP {code}: {reason}")
        self.code, self.reason = code, reason


# ---------------------------------------------------------------- key handling
def load_key():
    k = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if k:
        return k
    p = os.path.expanduser(os.environ.get("CROCO_YOUTUBE_ENV", "~/.config/croco/youtube.env"))
    try:
        with open(p) as f:
            for line in f:
                m = re.match(r"\s*(?:export\s+)?YOUTUBE_API_KEY\s*=\s*(.*)$", line)
                if m:
                    return m.group(1).strip().strip("'\"")
    except OSError:
        pass
    return ""


def redact(text, key):
    text = str(text)
    if key:
        text = text.replace(key, "[REDACTED]")
    return re.sub(r"AIza[0-9A-Za-z_\-]{30,}", "[REDACTED]", text)


# ---------------------------------------------------------------- state
def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def load_state(state_dir):
    p = os.path.join(state_dir, "state.json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {"version": 1, "ledger": {}, "cache": {}, "selection": None, "snapshots": {}}


def save_state(state_dir, state):
    os.makedirs(state_dir, exist_ok=True)
    # prune: ledger 35 days, cache entries already expired
    days = sorted(state["ledger"])[-35:]
    state["ledger"] = {d: state["ledger"][d] for d in days}
    t = now_utc()
    state["cache"] = {k: v for k, v in state["cache"].items()
                      if dt.datetime.fromisoformat(v["expires"]) > t}
    tmp = os.path.join(state_dir, "state.json.tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, os.path.join(state_dir, "state.json"))


# ---------------------------------------------------------------- client
class Client:
    """Read-only YouTube Data API client with quota ledger, caps, cache and de-dup."""

    def __init__(self, state, key=None, transport=None, auth=None, deadline_sec=None):
        self.state = state
        self.auth = auth or AUTH_MODE
        self.key = "" if self.auth == "proxy" else (key if key is not None else load_key())
        self.transport = transport or self._http
        self.started = now_utc()
        self.deadline = self.started + dt.timedelta(seconds=deadline_sec or DEADLINE_SEC)
        self.circuit = None          # reason string once open
        self.consecutive_errors = 0

    def _day(self):
        d = now_utc().astimezone(PT).date().isoformat()
        return self.state["ledger"].setdefault(d, {"units": 0, "search_calls": 0, "calls": []})

    def usage(self):
        d = self._day()
        return {"pt_day": now_utc().astimezone(PT).date().isoformat(), "units": d["units"],
                "search_calls": d["search_calls"], "unit_cap": DAILY_UNIT_CAP,
                "search_cap": DAILY_SEARCH_CAP,
                "cache_hits": sum(1 for c in d["calls"] if c.get("cached")),
                "failed_calls": sum(1 for c in d["calls"] if c.get("ok") is False),
                "auth_mode": self.auth, "circuit": self.circuit}

    def _http(self, endpoint, params):
        if os.environ.get("CROCO_OFFLINE") == "1":
            raise RuntimeError("CROCO_OFFLINE=1: network disabled")
        url = API + endpoint + "?" + urllib.parse.urlencode(params)
        headers = {"Accept": "application/json"}
        if self.key:                       # proxy mode: header is added outside the VM
            headers["X-Goog-Api-Key"] = self.key
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30, context=_ssl_context()) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read()[:2000].decode("utf-8", "replace")
            try:
                err = json.loads(body)["error"]
                reason = ",".join(x.get("reason", "") for x in err.get("errors", [])) or err.get("message", "")
            except Exception:
                reason = body[:200]
            raise ApiError(e.code, redact(reason, self.key))
        except urllib.error.URLError as e:
            raise ApiError(0, redact(e.reason, self.key))
        except (TimeoutError, OSError, ValueError) as e:      # socket timeout / reset / bad JSON
            raise ApiError(0, redact(f"{type(e).__name__}: {e}", self.key))

    def get(self, endpoint, **params):
        params = {k: v for k, v in sorted(params.items()) if v is not None}
        ck = hashlib.sha256((endpoint + "?" + urllib.parse.urlencode(params)).encode()).hexdigest()[:24]
        day = self._day()
        hit = self.state["cache"].get(ck)
        if hit and dt.datetime.fromisoformat(hit["expires"]) > now_utc():
            day["calls"].append({"t": now_utc().isoformat(timespec="seconds"), "endpoint": endpoint,
                                 "units": 0, "cached": True})
            return hit["data"]
        cost = COST[endpoint]
        if day["units"] + cost > DAILY_UNIT_CAP:
            raise QuotaCapReached(f"daily unit cap {DAILY_UNIT_CAP} reached ({day['units']} used)")
        if endpoint == "search" and day["search_calls"] + 1 > DAILY_SEARCH_CAP:
            raise QuotaCapReached(f"daily search cap {DAILY_SEARCH_CAP} reached")
        if self.circuit:
            raise QuotaCapReached(f"circuit open: {self.circuit}")
        if now_utc() > self.deadline:
            raise QuotaCapReached(f"run deadline {DEADLINE_SEC}s reached")
        if not self.key and self.auth != "proxy":
            raise ApiError(0, "YOUTUBE_API_KEY not available")
        # quota is spent even when the call fails -> record before calling
        day["units"] += cost
        day["search_calls"] += endpoint == "search"
        entry = {"t": now_utc().isoformat(timespec="seconds"), "endpoint": endpoint, "units": cost,
                 "cached": False, "ok": False}
        day["calls"].append(entry)
        try:
            data = self.transport(endpoint, params)
        except ApiError as e:
            entry["error"] = f"{e.code}:{str(e.reason)[:80]}"
            self.consecutive_errors += 1
            if e.code in FATAL_CODES or "key" in str(e.reason).lower() or self.consecutive_errors >= 3:
                self.circuit = f"{endpoint} HTTP {e.code} {str(e.reason)[:80]}"
            raise
        self.consecutive_errors = 0
        entry["ok"] = True
        exp = now_utc() + dt.timedelta(hours=TTL_HOURS[endpoint])
        self.state["cache"][ck] = {"expires": exp.isoformat(), "data": data}
        return data


# ---------------------------------------------------------------- data helpers
def parse_duration(iso):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return None
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def classify(text, table):
    """Whole-word match (plural s/es allowed) so 'car' does not match 'cartoon' or 'bus' 'BabyBus'."""
    t = (text or "").lower()
    return [k for k, rx in table.items() if re.search(r"\b(?:" + rx + r")(?:e?s)?\b", t)]


def is_english(sn):
    """API audio/metadata language if given, else title script (Croco's audience is English-speaking)."""
    lang = (sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "").lower()
    if lang:
        return lang.startswith("en")
    letters = [ch for ch in sn.get("title", "") if ch.isalpha()]
    return bool(letters) and sum(ch.isascii() for ch in letters) / len(letters) >= 0.9


def _int(x):
    return int(x) if x not in (None, "") else None


def video_row(v):
    st, sn = v.get("statistics", {}), v.get("snippet", {})
    views, likes = _int(st.get("viewCount")), _int(st.get("likeCount"))
    text = sn.get("title", "")   # title only: descriptions carry boilerplate ("thank you", "play") that skews every channel
    return {
        "id": v["id"], "channel_id": sn.get("channelId"), "channel": sn.get("channelTitle"),
        "title": sn.get("title"), "published": sn.get("publishedAt"),
        "views": views, "likes": likes,
        "like_view_ratio": round(likes / views, 4) if views and likes is not None else None,
        "seconds": parse_duration(v.get("contentDetails", {}).get("duration")),
        "made_for_kids": v.get("status", {}).get("madeForKids"),
        "english": is_english(sn),
        "topics": classify(text, TOPICS), "formats": classify(text, FORMATS),
        "url": f"https://www.youtube.com/watch?v={v['id']}",
    }


def fetch_videos(c, ids):
    out = []
    for i in range(0, len(ids), 50):
        r = c.get("videos", part="snippet,statistics,contentDetails,status", id=",".join(ids[i:i + 50]),
                  maxResults=50)
        out += [video_row(v) for v in r.get("items", [])]
    return out


def fetch_channels(c, ids):
    out = {}
    for i in range(0, len(ids), 50):
        r = c.get("channels", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]),
                  maxResults=50)
        for ch in r.get("items", []):
            st = ch.get("statistics", {})
            out[ch["id"]] = {
                "id": ch["id"], "title": ch["snippet"]["title"],
                "handle": ch["snippet"].get("customUrl"),
                "subscribers": None if st.get("hiddenSubscriberCount") else _int(st.get("subscriberCount")),
                "video_count": _int(st.get("videoCount")),
                "uploads": ch.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads"),
                "url": f"https://www.youtube.com/channel/{ch['id']}",
            }
    return out


def recent_uploads(c, playlist, max_items=50):
    if not playlist:
        return []
    r = c.get("playlistItems", part="contentDetails", playlistId=playlist, maxResults=max_items)
    return [it["contentDetails"]["videoId"] for it in r.get("items", [])]


def channel_metrics(ch, vids, ref):
    """ref = aware datetime (report time)."""
    def age_days(v):
        return (ref - dt.datetime.fromisoformat(v["published"].replace("Z", "+00:00"))).total_seconds() / 86400
    vids = sorted(vids, key=lambda v: v["published"] or "", reverse=True)
    v7 = [v for v in vids if age_days(v) <= 7]
    v30 = [v for v in vids if age_days(v) <= 30]
    views30 = [v["views"] for v in v30 if v["views"] is not None]
    ratios = [v["like_view_ratio"] for v in v30 if v["like_view_ratio"] is not None]
    secs = [v["seconds"] for v in v30 if v["seconds"] is not None]
    mfk = [v["made_for_kids"] for v in vids if v["made_for_kids"] is not None]
    eng = [v.get("english") for v in vids if v.get("english") is not None]
    spread = None
    if len(views30) >= 2:
        med = statistics.median(views30)
        spread = {"median": int(med), "max": max(views30), "min": min(views30),
                  "max_over_median": round(max(views30) / med, 2) if med else None}
    topics, formats = {}, {}
    for v in v30:
        for t in v["topics"]:
            topics[t] = topics.get(t, 0) + 1
        for f in v["formats"]:
            formats[f] = formats.get(f, 0) + 1
    return {
        **ch,
        "uploads_7d": len(v7), "uploads_30d": len(v30),
        "uploads_30d_capped": len(vids) >= 50 and len(v30) == len(vids),
        "median_views_30d": int(statistics.median(views30)) if views30 else None,
        "median_like_view_ratio_30d": round(statistics.median(ratios), 4) if ratios else None,
        "median_seconds_30d": int(statistics.median(secs)) if secs else None,
        "shorts_share_30d": round(sum(1 for s in secs if s <= 180) / len(secs), 2) if secs else None,
        "made_for_kids_share": round(sum(mfk) / len(mfk), 2) if mfk else None,
        "english_share": round(sum(eng) / len(eng), 2) if eng else None,
        "performance_spread_30d": spread,
        "topics_30d": dict(sorted(topics.items(), key=lambda x: -x[1])),
        "formats_30d": dict(sorted(formats.items(), key=lambda x: -x[1])),
        "videos_recent": vids[:15],
    }


def score(m, search_hits):
    """0–100, four documented components (25 each). Inputs are public API values only."""
    text = " ".join(v["title"] or "" for v in m["videos_recent"]).lower() + " " + (m["title"] or "").lower()
    sim_terms = set(re.findall(SIMILARITY_TERMS, text))
    animal = 1 if m["topics_30d"].get("동물") else 0
    similarity = min(25, len(sim_terms) * 2.5 + animal * 5 + 25 * (m["shorts_share_30d"] or 0) * 0.3)
    # audience = made-for-kids share x language fit (Croco publishes in English): 40% floor for global reference
    audience = 25 * (m["made_for_kids_share"] or 0) * (0.4 + 0.6 * (m.get("english_share") or 0))
    activity = min(25, m["uploads_30d"] * 25 / 20)   # 20+ uploads in 30 days = full
    med = m["median_views_30d"] or 0
    perf = 0 if not med else min(25, 25 * (len(str(med)) - 2) / 6)  # 1e3 ->~4, 1e8 -> 25 (log10 scale)
    parts = {"콘텐츠 유사성": round(similarity, 1), "시청 대상(아동용×영어)": round(audience, 1),
             "최근 업로드 활동": round(activity, 1), "공개 영상 성과": round(max(perf, 0), 1)}
    return round(sum(parts.values()) + min(5, search_hits), 1), parts


def _is_own(ch):
    return any(x in (ch.get("title") or "").lower() for x in OWN_CHANNEL_MARKERS)


# ---------------------------------------------------------------- discovery (weekly)
def discover(c, ref):
    after = (ref - dt.timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z")  # day-rounded -> cacheable
    hits, scope_of, notes = {}, {}, []
    for label, q in SCOPES:
        try:
            r = c.get("search", part="snippet", type="video", q=q, videoDuration="short",
                      publishedAfter=after, order="viewCount", safeSearch="strict",
                      relevanceLanguage="en", maxResults=50)
        except (ApiError, QuotaCapReached) as e:
            notes.append(f"{label}: 검색 실패 ({e})")
            continue
        for it in r.get("items", []):
            cid = it["snippet"]["channelId"]
            hits[cid] = hits.get(cid, 0) + 1
            scope_of.setdefault(cid, set()).add(label)
    for h in BRAND_HANDLES:
        try:
            r = c.get("channels", part="id", forHandle=h)
        except (ApiError, QuotaCapReached) as e:
            notes.append(f"{h}: 조회 실패 ({e})")
            continue
        for it in r.get("items", []):
            hits.setdefault(it["id"], 0)
            scope_of.setdefault(it["id"], set()).add("대형 키즈 브랜드")
    # keep channels seen in >=2 results or brands, cap 24 for detailed look
    pool = sorted(hits, key=lambda k: (-("대형 키즈 브랜드" in scope_of[k]), -hits[k]))
    pool = [k for k in pool if hits[k] >= 2 or "대형 키즈 브랜드" in scope_of[k]][:24]
    chans = fetch_channels(c, pool)
    evaluated = []
    for cid, ch in chans.items():
        if _is_own(ch):
            continue
        try:
            vids = fetch_videos(c, recent_uploads(c, ch["uploads"]))
        except (ApiError, QuotaCapReached) as e:
            notes.append(f"{ch['title']}: 영상 조회 실패 ({e})")
            continue
        m = channel_metrics(ch, vids, ref)
        if not m["uploads_30d"]:
            notes.append(f"{ch['title']}: 최근 30일 업로드 없음 → 제외")
            continue
        s, parts = score(m, hits.get(cid, 0))
        m.update(score=s, score_parts=parts, scopes=sorted(scope_of.get(cid, [])), search_hits=hits.get(cid, 0))
        evaluated.append(m)
    evaluated.sort(key=lambda m: -m["score"])
    candidates = evaluated[:N_CANDIDATES]
    # tracked: top 5 by score, but guarantee >=2 mid-size and >=1 large brand when available
    mid = [m for m in candidates if m["subscribers"] is not None and m["subscribers"] < MID_SIZE_MAX_SUBS]
    big = [m for m in candidates if "대형 키즈 브랜드" in m["scopes"]]
    tracked = []
    for m in mid[:2] + big[:1] + candidates:
        if m not in tracked and len(tracked) < N_TRACKED:
            tracked.append(m)
    tracked.sort(key=lambda m: -m["score"])
    return {"selected_at": ref.isoformat(timespec="seconds"),
            "candidates": [_slim(m) for m in candidates],
            "tracked": [m["id"] for m in tracked], "evaluated": len(evaluated), "notes": notes}


def _slim(m):
    keep = ("id", "title", "handle", "url", "subscribers", "uploads_7d", "uploads_30d",
            "median_views_30d", "median_like_view_ratio_30d", "made_for_kids_share", "english_share", "shorts_share_30d",
            "topics_30d", "formats_30d", "score", "score_parts", "scopes", "search_hits")
    return {k: m.get(k) for k in keep}


def rationale(m):
    p = m["score_parts"]
    size = "중소형(구독자 100만 미만)" if (m["subscribers"] or 0) < MID_SIZE_MAX_SUBS else "대형"
    top_t = ", ".join(list(m["topics_30d"])[:2]) or "분류 없음"
    top_f = ", ".join(list(m["formats_30d"])[:2]) or "분류 없음"
    return (f"유사성 {p['콘텐츠 유사성']}/25 (주제: {top_t} · 형식: {top_f}) · "
            f"시청 대상 {p['시청 대상(아동용×영어)']}/25 (아동용 표시 {_pct(m['made_for_kids_share'])}, 영어 {_pct(m.get('english_share'))}) · "
            f"활동 {p['최근 업로드 활동']}/25 (30일 {m['uploads_30d']}편) · "
            f"성과 {p['공개 영상 성과']}/25 (30일 중앙 조회수 {_n(m['median_views_30d'])}) · {size} · "
            f"발견 경로: {', '.join(m['scopes'])}")


# ---------------------------------------------------------------- daily run
def run(state_dir, reevaluate=False, today=None, client=None):
    state = load_state(state_dir)
    c = client or Client(state)
    if client is not None:
        c.state = state
    ref = now_utc()
    today = today or ref.astimezone(MT).date().isoformat()
    notes = []
    sel = state.get("selection")
    due = (not sel or reevaluate or
           (ref - dt.datetime.fromisoformat(sel["selected_at"])).days >= REEVALUATE_DAYS)
    reevaluated = False
    if due:
        try:
            new = discover(c, ref)
            if new["tracked"]:
                prev = set(sel["tracked"]) if sel else set()
                new["changes"] = {"added": [i for i in new["tracked"] if i not in prev],
                                  "removed": [i for i in prev if i not in new["tracked"]]}
                state["selection"] = sel = new
                reevaluated = True
            else:
                notes.append("재평가 결과 추적 후보 없음 → 이전 목록 유지")
            notes += new["notes"]
        except (QuotaCapReached, ApiError) as e:
            notes.append(f"재평가 중단: {e} → 이전 목록 유지")
    tracked = []
    chans = {}
    if sel:
        try:
            chans = fetch_channels(c, sel["tracked"])
        except (ApiError, QuotaCapReached) as e:
            notes.append(f"추적 채널 조회 실패: {e}")
    if sel and chans:
        for cid in sel["tracked"]:
            ch = chans.get(cid)
            if not ch:
                notes.append(f"{cid}: 채널 조회 불가")
                continue
            try:
                vids = fetch_videos(c, recent_uploads(c, ch["uploads"]))
            except (ApiError, QuotaCapReached) as e:
                notes.append(f"{ch['title']}: 영상 조회 실패 ({e})")
                vids = []
            m = channel_metrics(ch, vids, ref)
            cand = next((x for x in sel["candidates"] if x["id"] == cid), {})
            m.update(score=cand.get("score"), score_parts=cand.get("score_parts"), scopes=cand.get("scopes", []))
            prev = state["snapshots"].get(cid)
            m["subscriber_change"] = None
            if (prev and prev.get("date", "") < today and prev.get("subscribers") is not None
                    and m["subscribers"] is not None):          # only against an EARLIER day's public value
                m["subscriber_change"] = {"since": prev["date"], "from": prev["subscribers"],
                                          "delta": m["subscribers"] - prev["subscribers"]}
            if m["subscribers"] is not None and (not prev or prev.get("date") != today):
                state["snapshots"][cid] = {"t": ref.isoformat(timespec="seconds"), "date": today,
                                           "subscribers": m["subscribers"]}
            tracked.append(m)
    trend = []
    try:
        after = (ref - dt.timedelta(days=3)).strftime("%Y-%m-%dT00:00:00Z")
        r = c.get("search", part="snippet", type="video", q=DAILY_TREND_QUERY, videoDuration="short",
                  publishedAfter=after, order="viewCount", safeSearch="strict", relevanceLanguage="en",
                  maxResults=25)
        ids = [it["id"]["videoId"] for it in r.get("items", []) if it.get("id", {}).get("videoId")]
        trend = [v for v in fetch_videos(c, ids) if v["made_for_kids"]]
    except (ApiError, QuotaCapReached) as e:
        notes.append(f"트렌드 검색 실패: {e}")
    result = {"date": today, "generated_at": ref.isoformat(timespec="seconds"),
              "reevaluated": reevaluated, "selection": sel, "tracked": tracked, "trend_videos": trend,
              "quota": c.usage(), "notes": notes}
    save_state(state_dir, state)
    return result


# ---------------------------------------------------------------- report
def _n(x):
    return "비공개" if x is None else f"{x:,}"


def _pct(x):
    return "DATA UNAVAILABLE" if x is None else f"{x * 100:.0f}%"


def _ratio(x):
    return "비공개" if x is None else f"{x * 100:.2f}%"


def top_videos(result, n=5, days=7):
    ref = dt.datetime.fromisoformat(result["generated_at"])
    seen, rows = set(), []
    for v in [v for m in result["tracked"] for v in m["videos_recent"]] + result["trend_videos"]:
        if v["id"] in seen or v["views"] is None or (v["seconds"] or 0) > SHORTS_MAX_SECONDS:
            continue
        age = (ref - dt.datetime.fromisoformat(v["published"].replace("Z", "+00:00"))).total_seconds() / 86400
        if age <= days:
            seen.add(v["id"])
            rows.append({**v, "age_days": round(max(age, 0.04), 1),
                         "views_per_day": int(v["views"] / max(age, 1))})
    return sorted(rows, key=lambda v: -v["views_per_day"])[:n]


def trend_topics(result, n=3):
    agg = {}
    pool = result["trend_videos"] + [v for m in result["tracked"] for v in m["videos_recent"][:5]]
    for v in [v for v in pool if (v["seconds"] or 0) <= SHORTS_MAX_SECONDS]:
        for t in v["topics"] + v["formats"]:
            a = agg.setdefault(t, {"views": 0, "videos": 0, "examples": []})
            a["views"] += v["views"] or 0
            a["videos"] += 1
            if len(a["examples"]) < 2:
                a["examples"].append(v)
    return sorted(agg.items(), key=lambda x: -x[1]["views"])[:n]


def render(result):
    q, sel = result["quota"], result["selection"] or {}
    L = [f"### 경쟁 채널 조사 (YouTube Data API v3 · {result['date']})",
         f"수집 {result['generated_at']} · 공개 API 값만 사용 · 주제/형식은 영상 제목 키워드 자동 분류 · "
         f"시청 지속률·클릭률·구독 전환율은 API 미제공 → **추정하지 않음**",
         "",
         f"**쿼터:** 오늘(PT {q['pt_day']}) {q['units']} / 내부 상한 {q['unit_cap']} units · "
         f"search 호출 {q['search_calls']} / {q['search_cap']}회 · 캐시 적중 {q['cache_hits']}회 "
         f"(공식 기본 할당: 일반 10,000 units/일, search.list 100회/일) · 실패 호출 {q.get('failed_calls', 0)}회"
         + (f" · ⚠️ 호출 중단: {q['circuit']}" if q.get("circuit") else ""),
         "**사용량 구분:** 위 값은 외부 YouTube Data API 사용량만입니다. 이 스크립트는 Claude를 호출하지 않으며, Claude 사용량은 회의 세션이 따로 기록합니다.",
         ""]
    if result["reevaluated"]:
        ch = sel.get("changes", {})
        L.append(f"**목록 재평가 실행** ({sel['selected_at']}, 후보 평가 {sel['evaluated']}개) · "
                 f"추가 {len(ch.get('added', []))} · 제외 {len(ch.get('removed', []))}")
    elif sel:
        L.append(f"추적 목록 기준일 {sel['selected_at'][:10]} (7일마다 재평가)")
    L += ["", "#### 추적 중인 경쟁 채널 (5)",
          "| 채널 | 구독자(공개) | 구독자 변화 | 7일/30일 업로드 | 30일 중앙 조회수 | 좋아요/조회 | 중앙 길이 | 성과 편차(최대/중앙) | 주요 주제·형식 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for m in result["tracked"]:
        chg = m["subscriber_change"]
        chg_s = (f"{chg['delta']:+,} ({chg['since']} 대비, 공개값은 반올림됨)" if chg else "비교 기준 없음(첫 저장)")
        sp = m["performance_spread_30d"]
        sp_s = f"{sp['max_over_median']}× ({_n(sp['max'])}/{_n(sp['median'])})" if sp and sp["max_over_median"] else "—"
        tf = ", ".join(list(m["topics_30d"])[:2] + list(m["formats_30d"])[:1]) or "—"
        cap = "+" if m.get("uploads_30d_capped") else ""
        L.append(f"| [{m['title']}]({m['url']}) | {_n(m['subscribers'])} | {chg_s} | "
                 f"{m['uploads_7d']}/{m['uploads_30d']}{cap} | {_n(m['median_views_30d'])} | "
                 f"{_ratio(m['median_like_view_ratio_30d'])} | {m['median_seconds_30d'] or '—'}초 | {sp_s} | {tf} |")
    L += ["", "#### 선정 근거 (후보 10 → 추적 5)"]
    tracked_ids = set(sel.get("tracked", []))
    for i, m in enumerate(sel.get("candidates", []), 1):
        mark = "✅ 추적" if m["id"] in tracked_ids else "후보"
        L.append(f"{i}. **{m['title']}** ({mark}, 점수 {m['score']}) — {rationale(m)}")
    L += ["", "#### 주목할 경쟁 영상 TOP 5 (최근 7일 Shorts ≤180초, 하루 평균 조회수 순)",
          "| # | 영상 | 채널 | 게시 | 조회수 | 좋아요 | 좋아요/조회 | 길이 | 주제·형식 |", "|---|---|---|---|---|---|---|---|---|"]
    for i, v in enumerate(top_videos(result), 1):
        L.append(f"| {i} | [{v['title']}]({v['url']}) | {v['channel']} | {v['published'][:10]} ({v['age_days']}일 전) | "
                 f"{_n(v['views'])} | {_n(v['likes'])} | {_ratio(v['like_view_ratio'])} | {v['seconds']}초 | "
                 f"{', '.join(v['topics'] + v['formats']) or '—'} |")
    L += ["", "#### 오늘의 글로벌 트렌드 TOP 3 (자동 집계 · 최근 3일 아동용 Shorts 검색 + 추적 채널 최신 Shorts, 조회수 합계 순)"]
    for i, (t, a) in enumerate(trend_topics(result), 1):
        ex = " / ".join(f"[{e['title'][:50]}]({e['url']})" for e in a["examples"])
        L.append(f"{i}. **{t}** — 영상 {a['videos']}편, 합계 조회수 {a['views']:,} · 예: {ex}")
    if result["notes"]:
        L += ["", "#### 수집 메모"] + [f"- {n}" for n in result["notes"]]
    L += ["", "_경쟁 채널의 캐릭터·노래·대사·디자인은 복제하지 않는다. 위 자료는 형식·길이·주제 패턴 참고용이다._"]
    return "\n".join(L)


def plan_units(state_dir):
    st = load_state(state_dir)
    sel = st.get("selection")
    due = not sel or (now_utc() - dt.datetime.fromisoformat(sel["selected_at"])).days >= REEVALUATE_DAYS
    daily = 1 + 2 * N_TRACKED + 1 + 1          # channels + (playlist+videos)×5 + trend search + videos
    disc = len(SCOPES) + len(BRAND_HANDLES) + 1 + 2 * 24
    return {"reevaluation_due": due, "max_units_today": daily + (disc if due else 0),
            "search_calls_today": 1 + (len(SCOPES) if due else 0), "cap": DAILY_UNIT_CAP}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="croco.competitors")
    ap.add_argument("cmd", choices=["run", "plan"])
    ap.add_argument("--state", required=True)
    ap.add_argument("--out")
    ap.add_argument("--reevaluate", action="store_true")
    ap.add_argument("--date")
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        print(json.dumps(plan_units(a.state), ensure_ascii=False))
        return 0
    if AUTH_MODE != "proxy" and not load_key():
        print("BLOCKED: YOUTUBE_API_KEY not available (env, CROCO_YOUTUBE_ENV file, or CROCO_YT_AUTH=proxy)")
        return 2
    try:
        res = run(a.state, reevaluate=a.reevaluate, today=a.date)
    except Exception as e:                      # never block the meeting; never leak the key
        print("BLOCKED: " + redact(f"{type(e).__name__}: {e}", load_key()))
        return 3
    if not res["tracked"] and not res["trend_videos"]:
        q = res["quota"]
        print("BLOCKED: no data collected (" + redact("; ".join(res["notes"])[:300], load_key())
              + f") units={q['units']}/{q['unit_cap']} circuit={q['circuit']}")
        return 3
    out = a.out or a.state
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "report.md"), "w") as f:
        f.write(render(res) + "\n")
    with open(os.path.join(out, "data.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    q = res["quota"]
    print(f"OK tracked={len(res['tracked'])} reevaluated={res['reevaluated']} "
          f"units={q['units']}/{q['unit_cap']} search={q['search_calls']}/{q['search_cap']} "
          f"cache_hits={q['cache_hits']} notes={len(res['notes'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
