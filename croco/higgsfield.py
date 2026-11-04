"""Higgsfield REST client (Kling 4.0 text-to-video). Standard library only.

Auth: in the cloud environment the network proxy injects the credential for
api.higgsfield.ai, so no header is sent by default. For local use, set
HF_KEY_ID and HF_KEY_SECRET (never print or commit them).
"""
import json
import os
import urllib.error
import urllib.request
from decimal import Decimal

BASE = os.environ.get("HF_BASE", "https://api.higgsfield.ai")
MODEL = "kling-video/v4.0/text-to-video"


class AmbiguousSubmit(Exception):
    """Request may or may not have been accepted. NEVER auto-resubmit."""


class ApiError(Exception):
    def __init__(self, code, detail):
        super().__init__(f"HTTP {code}: {detail}")
        self.code = code


def _headers():
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if os.environ.get("HF_KEY_ID") and os.environ.get("HF_KEY_SECRET"):
        h["Authorization"] = f"Key {os.environ['HF_KEY_ID']}:{os.environ['HF_KEY_SECRET']}"
    return h


def _call(method, url, body=None, timeout=60):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise ApiError(e.code, e.read()[:300].decode("utf-8", "replace"))


def estimate_usd(params):
    """Official price estimate. Raises if the estimate is missing/invalid (fail-closed)."""
    r = _call("POST", f"{BASE}/estimate/{MODEL}", params)
    usd = r.get("usd")
    if usd is None or Decimal(str(usd)) <= 0:
        raise ApiError(0, f"unusable estimate response: {r}")
    return Decimal(str(usd))


def submit(params):
    """Returns request_id. Anything unclear after sending => AmbiguousSubmit."""
    try:
        r = _call("POST", f"{BASE}/{MODEL}", params)
    except ApiError as e:
        if 400 <= e.code < 500:  # rejected before queueing => definitely not charged
            raise
        raise AmbiguousSubmit(str(e))
    except Exception as e:  # timeout / connection reset after send
        raise AmbiguousSubmit(repr(e))
    rid = r.get("request_id")
    if not rid:
        raise AmbiguousSubmit(f"no request_id in response: {str(r)[:200]}")
    return rid


def status(request_id):
    return _call("GET", f"{BASE}/requests/{request_id}/status")


def download(url, dest, timeout=300):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
