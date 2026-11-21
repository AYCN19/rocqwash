#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""claim_watch.py - native resident claim watch tool (rocqwash tools/, ticket 13).
Purpose.  One watch round over a signal config: fetch every signal's source
  once, judge it, and append one honest ledger row per signal to an
  append-only JSONL.  Registrations are data, never errors: keyword hits
  carry the verbatim quote (forwarding to adjudication), a stale
  heartbeat_at registers target silent death (its own outcome class),
  hash_pin and round-over-round digests are the drift baselines (fetch
  failures never enter the drift branch), and TLS/DNS/timeout register
  unverifiable per tools/net_probe.py, never fabricated.
Interface.  python -I tools/claim_watch.py --config <json>
  [--round-label <label>] [--ledger docs/claim-watch-ledger.jsonl]
  [--actor <name>] [--selftest] [--offline-selftest].  The live face is
  the network face; --selftest (alias --offline-selftest) runs the frozen
  canned vector group with zero
  network and exits.
Dependencies.  Python 3 standard library only; sibling imports
  tools/_http_backoff.py (retry judgment and exponential backoff) and
  tools/net_probe.py (classify_unverifiable), resolved through an explicit
  sys.path injection because -I does not add the script directory.
Evidence.  --offline-selftest frozen vectors V1-V10 (canned transport,
  virtual clock, temporary directory; zero network, zero writes outside
  the temporary directory).
Exit-codes.  0 round completed with every signal registered (a
  registration is data) or selftest green; 1 ledger invariant failure
  (append or read-back); 2 usage or schema error; 9 missing input (config
  file absent, ledger directory not writable).
"""
# Extended contract (kept outside the five-field block per the annotation
# standard 30-line header budget).
#
# Config schema rocqwash-claim-watch-config/1 (frozen per ticket 13; the
# three signal forms are all accepted).  Forwarding semantics: a keyword
# hit is a registration for adjudication, never an auto rescan and never
# an auto disclosure; the tool's job ends at the honest registration.
#   {"schema": "rocqwash-claim-watch-config/1",
#    "max_retries": 3,                # NETRED retry cap per fetch (optional)
#    "backoff_base_seconds": 2.0,     # exponential base, delays b*2^i (optional)
#    "signals": [ ... ]}
#   repo-path form: {"id", "kind": "repo-path", "repo", "path",
#     "hash_pin" (optional), "conclusion_keywords": [...]}
#   status-endpoint form: {"id", "kind": "status-endpoint", "url",
#     "phase_field", "done_phases": [...], "conclusion_keywords": [...],
#     "heartbeat_field" (default "heartbeat_at"),
#     "heartbeat_stale_minutes" (default 90)}
#   zulip form: {"id", "kind": "zulip-web-public", "stream", "topic_hint",
#     "conclusion_keywords": [...]}
#   Unknown keys, missing required keys, duplicate ids and a malformed
#   hash_pin are schema errors (exit 2, fail-loud, per-error lines).
#
# Fetch faces of the repo-path kind, keyed by the shape of "repo":
#   owner/repo (contains "/"): GitHub contents API
#     https://api.github.com/repos/<repo>/contents/<path>?ref=HEAD with
#     Accept application/vnd.github+json.  A JSON array response is the
#     directory listing face (the digest covers the sorted name+sha
#     entries, so a new file lands as a digest change); a JSON object with
#     type "file" is the file face (the base64 content decodes to the
#     bytes the digest and the pin cover).  An empty path is the
#     repository root listing.
#   bare host (no "/" but contains ".", e.g. "alpo.ge"): plain GET
#     https://<repo>/<path>, the raw bytes face.
#   bare owner (neither "/" nor "."): GitHub owner listing
#     https://api.github.com/users/<repo>/repos?sort=pushed&per_page=10,
#     the digest covers the sorted full_name+pushed_at entries; the path
#     field is unused on this face (it transcribes the ticket's named
#     watch target and rides until the first live calibration pins the
#     exact repository).
#
# Zulip web-public recipe (built in, ticket 13 acceptance 3): the host is
#   the built-in constant ZULIP_WEB_PUBLIC_HOST; the recipe is one no-auth
#   GET of <host>/llms.txt (the recipe discovery face, its status recorded
#   in the row evidence) followed by one no-auth GET of
#   <host>/api/v1/messages?stream=<stream>&topic=<topic_hint>&num_messages=100
#   (the earlier audit work stream's precedent: the login-wall assumption
#   was falsified for a web-public stream).  A 401 (or 403) on the
#   messages face registers unverifiable honestly (the wall applies on
#   that face; nothing is fabricated), and a 401 on the llms.txt face
#   with a readable messages face is an honest note, never a failure.
#
# NETRED retry face (ticket 13 acceptance 5): per fetch, the retry face is
#   _http_backoff.is_retry_status (403/429/5xx) plus the transient
#   transport faces dns and timeout; each retry sleeps
#   backoff_delays(max_retries, base)[attempt] seconds first (the schedule
#   comes from the config).  A TLS block does not heal inside one round
#   and is not retried; 401/404 and every other status is a semantic face
#   judged by the caller, never retried.  Exhausted retries land as
#   fetch-failed (the target answered) or unverifiable (the path itself
#   was blocked), and the drift branch is unreachable from any fetch
#   failure by construction.
#
# Outcome classes: clean (ok=true), baseline-registered (ok=true, first
#   observation, the digest becomes the local baseline),
#   conclusion-hit (ok=false, quote), phase-flip (ok=false, the phase
#   value verbatim), heartbeat-stale (ok=false, target silent death with
#   the age and threshold in the evidence), heartbeat-unparseable
#   (ok=false, honest), pin-drift (ok=false, expected/actual), round-change
#   (ok=false, digest differs from the previous round's row),
#   fetch-failed (ok=false, target-evidence failure), unverifiable
#   (ok=false, the net_probe reason class in the evidence).
#
# Ledger (ticket 13 acceptance 6): schema rocqwash-claim-watch-round/1,
#   one JSON object per line, append-only (the file is opened in append
#   mode and never rewritten; the round verifies after the append that the
#   pre-existing byte prefix is unchanged and the appended rows parse).
#   Every row carries at_utc, actor and round_label (the actor namespace
#   and the round label of that round); rows of earlier rounds are the
#   per-signal baseline memory.  Corrupt prior lines are skipped and
#   counted, never guessed.
import argparse
import base64
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
import _http_backoff  # noqa: E402  (retry face + exponential backoff)
import net_probe  # noqa: E402  (classify_unverifiable + reason constants)

PROG = "claim_watch"
SCHEMA = "rocqwash-claim-watch-config/1"
LEDGER_SCHEMA = "rocqwash-claim-watch-round/1"
DEFAULT_LEDGER = "docs/claim-watch-ledger.jsonl"
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 2.0
DEFAULT_HEARTBEAT_FIELD = "heartbeat_at"
DEFAULT_HEARTBEAT_STALE_MINUTES = 90
TIMEOUT_SEC = 20
QUOTE_CONTEXT = 120
GITHUB_API = "https://api.github.com"
ZULIP_WEB_PUBLIC_HOST = "https://leanprovercommunity.zulipchat.com"

# Outcome constants (the registration vocabulary of a row).
CLEAN = "clean"
BASELINE = "baseline-registered"
CONCLUSION_HIT = "conclusion-hit"
PHASE_FLIP = "phase-flip"
HEARTBEAT_STALE = "heartbeat-stale"
HEARTBEAT_UNPARSEABLE = "heartbeat-unparseable"
PIN_DRIFT = "pin-drift"
ROUND_CHANGE = "round-change"
FETCH_FAILED = "fetch-failed"
UNVERIFIABLE = net_probe.UNVERIFIABLE  # "unverifiable", the net_probe shape
OK_TRUE = (CLEAN, BASELINE)
# Headline precedence when one round triggers more than one flag on a
# fetched body: the secondary flags ride the row notes verbatim.
OUTCOME_PRECEDENCE = (CONCLUSION_HIT, PHASE_FLIP, HEARTBEAT_STALE,
                      HEARTBEAT_UNPARSEABLE, PIN_DRIFT, ROUND_CHANGE,
                      CLEAN, BASELINE)
DRIFT_OUTCOMES = (PIN_DRIFT, ROUND_CHANGE)


def utc_now():
    """Wall clock (aware UTC datetime); the injection point behind the
    selftest virtual clock."""
    return datetime.now(timezone.utc)


def fmt_utc(dt):
    """Aware datetime -> ISO-8601 Z string (second precision)."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def label_now(dt):
    """Default round label: the run's compact UTC minute stamp."""
    return dt.strftime("%Y%m%dT%H%MZ")


# ---- config validation ------------------------------------------------------

_REPO_PATH_REQ = ("id", "kind", "repo", "path", "conclusion_keywords")
_REPO_PATH_OPT = ("hash_pin",)
_STATUS_REQ = ("id", "kind", "url", "phase_field", "done_phases",
               "conclusion_keywords")
_STATUS_OPT = ("heartbeat_field", "heartbeat_stale_minutes")
_ZULIP_REQ = ("id", "kind", "stream", "topic_hint", "conclusion_keywords")

HASH_PIN_RE = re.compile(r"^(sha256:[0-9a-f]{64}|bytes:[0-9]+)$")


def _is_str_list(value):
    return (isinstance(value, list) and value
            and all(isinstance(x, str) and x for x in value))


def _validate_signal(sig, seen_ids, errors, where):
    if not isinstance(sig, dict):
        errors.append("%s: signal is not an object" % where)
        return
    kind = sig.get("kind")
    req = {"repo-path": _REPO_PATH_REQ, "status-endpoint": _STATUS_REQ,
           "zulip-web-public": _ZULIP_REQ}.get(kind)
    if req is None:
        errors.append("%s: unknown signal kind %r (the frozen forms are"
                      " repo-path, status-endpoint, zulip-web-public)"
                      % (where, kind))
        return
    opt = _REPO_PATH_OPT if kind == "repo-path" else _STATUS_OPT
    for key in req:
        if key not in sig:
            errors.append("%s: missing required key %r" % (where, key))
    for key in sig:
        if key not in req and key not in opt:
            errors.append("%s: unknown key %r for kind %s (the schema is"
                          " frozen)" % (where, key, kind))
    sid = sig.get("id")
    if not isinstance(sid, str) or not sid:
        errors.append("%s: id must be a non-empty string" % where)
    elif sid in seen_ids:
        errors.append("%s: duplicate signal id %r" % (where, sid))
    seen_ids.add(sid)
    for key in ("conclusion_keywords",):
        if key in sig and not isinstance(sig[key], list):
            errors.append("%s: %s must be a list (possibly empty)"
                          % (where, key))
        elif key in sig and not all(isinstance(x, str) and x
                                    for x in sig[key]):
            errors.append("%s: %s entries must be non-empty strings"
                          % (where, key))
    if kind == "repo-path":
        repo = sig.get("repo")
        if not isinstance(repo, str) or not repo:
            errors.append("%s: repo must be a non-empty string" % where)
        path = sig.get("path")
        if not isinstance(path, str):
            errors.append("%s: path must be a string (possibly empty)"
                          % where)
        pin = sig.get("hash_pin")
        if pin is not None and (not isinstance(pin, str)
                                or not HASH_PIN_RE.match(pin)):
            errors.append("%s: hash_pin must match sha256:<64 lowercase"
                          " hex> or bytes:<decimal>" % where)
    elif kind == "status-endpoint":
        url = sig.get("url")
        if not isinstance(url, str) or not (url.startswith("http://")
                                            or url.startswith("https://")):
            errors.append("%s: url must be an http(s) URL" % where)
        if "phase_field" in sig and not isinstance(sig["phase_field"], str):
            errors.append("%s: phase_field must be a string (possibly"
                          " empty)" % where)
        if "done_phases" in sig and not isinstance(sig["done_phases"], list):
            errors.append("%s: done_phases must be a list (possibly empty)"
                          % where)
        elif "done_phases" in sig and not all(isinstance(x, str) and x
                                              for x in sig["done_phases"]):
            errors.append("%s: done_phases entries must be non-empty"
                          " strings" % where)
        stale = sig.get("heartbeat_stale_minutes")
        if stale is not None and (not isinstance(stale, (int, float))
                                  or isinstance(stale, bool)
                                  or stale <= 0):
            errors.append("%s: heartbeat_stale_minutes must be a positive"
                          " number" % where)
        field = sig.get("heartbeat_field")
        if field is not None and (not isinstance(field, str) or not field):
            errors.append("%s: heartbeat_field must be a non-empty string"
                          % where)
    elif kind == "zulip-web-public":
        for key in ("stream", "topic_hint"):
            value = sig.get(key)
            if not isinstance(value, str) or not value:
                errors.append("%s: %s must be a non-empty string"
                              % (where, key))


def validate_config(data):
    """Config dict -> (normalized cfg dict, error list).  Pure, zero IO."""
    errors = []
    if not isinstance(data, dict):
        return None, ["config must be a JSON object"]
    if data.get("schema") != SCHEMA:
        errors.append("schema must be %r, got %r"
                      % (SCHEMA, data.get("schema")))
    allowed = {"schema", "max_retries", "backoff_base_seconds", "signals"}
    for key in data:
        if key not in allowed:
            errors.append("unknown top-level key %r (the schema is frozen)"
                          % key)
    max_retries = data.get("max_retries", DEFAULT_MAX_RETRIES)
    if not isinstance(max_retries, int) or isinstance(max_retries, bool) \
            or max_retries < 0:
        errors.append("max_retries must be a non-negative int, got %r"
                      % (max_retries,))
    base = data.get("backoff_base_seconds", DEFAULT_BACKOFF_BASE)
    if not isinstance(base, (int, float)) or isinstance(base, bool) \
            or base <= 0:
        errors.append("backoff_base_seconds must be a positive number,"
                      " got %r" % (base,))
    signals = data.get("signals")
    if not isinstance(signals, list) or not signals:
        errors.append("signals must be a non-empty list")
        return None, errors
    seen = set()
    for i, sig in enumerate(signals):
        _validate_signal(sig, seen, errors, "signals[%d]" % i)
    if errors:
        return None, errors
    return {"schema": SCHEMA, "max_retries": max_retries,
            "backoff_base_seconds": float(base), "signals": signals}, errors


# ---- transport (canned injection point behind the selftest) -----------------

def _urlopen(url, timeout):
    return urllib.request.urlopen(url, timeout=timeout)


def http_fetch(url, timeout=TIMEOUT_SEC, _open=None):
    """One GET shot -> {status, body, error, reason_class}.  status is the
    HTTP status when an answer arrived (HTTPError included) and None for
    transport failures; reason_class is the net_probe unverifiable class
    (tls-blocked | dns | timeout) of a transport failure that says nothing
    about the target, and None for reachable answers and plain failures."""
    opener = _open if _open is not None else _urlopen
    try:
        resp = opener(url, timeout=timeout)
        status = getattr(resp, "status", None)
        if status is None and hasattr(resp, "getcode"):
            status = resp.getcode()
        body = resp.read()
        close = getattr(resp, "close", None)
        if close:
            close()
        return {"status": status, "body": body, "error": None,
                "reason_class": None}
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return {"status": exc.code, "body": body,
                "error": "%s: %s" % (type(exc).__name__, exc),
                "reason_class": None}
    except Exception as exc:  # noqa: BLE001 - classified, never swallowed
        return {"status": None, "body": b"",
                "error": "%s: %s" % (type(exc).__name__, exc),
                "reason_class": net_probe.classify_unverifiable(exc)}


def fetch_netred(url, max_retries, base_seconds, timeout=TIMEOUT_SEC,
                 _open=None, _sleep=None):
    """NETRED retry runner (ticket 13 acceptance 5).  Retry face =
    _http_backoff.is_retry_status (403/429/5xx) plus the transient
    transport faces dns and timeout; a tls-block is a policy face that
    does not heal inside one round; 401/404 and every other status is a
    semantic face for the caller.  Each retry sleeps the config schedule's
    delay first.  Returns {status, body, error, reason_class, attempts,
    statuses, backoff_applied}."""
    do_sleep = _sleep if _sleep is not None else time.sleep
    schedule = _http_backoff.backoff_delays(max_retries, base=base_seconds)
    attempts = 0
    statuses = []
    applied = []
    result = None
    for attempt in range(max_retries + 1):
        attempts += 1
        result = http_fetch(url, timeout=timeout, _open=_open)
        marker = result["status"]
        if marker is None:
            marker = result["reason_class"] or "error"
        statuses.append(marker)
        if result["status"] is not None:
            retryable = _http_backoff.is_retry_status(result["status"])
        elif result["reason_class"] in (net_probe.REASON_TLS_BLOCKED,):
            retryable = False
        elif result["reason_class"] in (net_probe.REASON_DNS,
                                        net_probe.REASON_TIMEOUT):
            retryable = True
        else:
            retryable = False
        if not retryable or attempt >= max_retries:
            break
        delay = schedule[attempt]
        applied.append(delay)
        do_sleep(delay)
    out = dict(result)
    out.update({"attempts": attempts, "statuses": statuses,
                "backoff_applied": applied, "max_retries": max_retries})
    return out


# ---- judgment helpers -------------------------------------------------------

def body_text(body):
    """Bytes -> text for keyword scanning (UTF-8 with replacement; the
    scan never raises on foreign bytes)."""
    return body.decode("utf-8", errors="replace")


def keyword_hit(text, keywords):
    """First case-insensitive hit -> (keyword, verbatim excerpt) or
    (None, None).  The excerpt quotes the body around the match, bounded
    to QUOTE_CONTEXT characters per side and marked with an ellipsis where
    clipped; the keyword itself lands verbatim inside the quote."""
    lowered = text.lower()
    for kw in keywords:
        i = lowered.find(kw.lower())
        if i >= 0:
            lo = max(0, i - QUOTE_CONTEXT)
            hi = min(len(text), i + len(kw) + QUOTE_CONTEXT)
            quote = text[lo:hi]
            if lo > 0:
                quote = "..." + quote
            if hi < len(text):
                quote = quote + "..."
            return kw, quote
    return None, None


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def listing_digest(entries, key_fields):
    """Sorted-entry canonical bytes -> digest bytes.  entries is a JSON
    list (GitHub listing or owner repos); the digest covers the sorted
    'field: value' joins of the key fields, so an added or updated entry
    lands as a digest change."""
    lines = []
    for entry in entries:
        if isinstance(entry, dict):
            lines.append("|".join("%s=%s" % (f, entry.get(f, ""))
                                  for f in key_fields))
        else:
            lines.append(str(entry))
    return ("\n".join(sorted(lines))).encode("utf-8")


def interpret_repo_body(face, payload, body):
    """Repo-path body -> (content bytes the digest and pin cover, the
    bytes the keyword scan reads verbatim, note or None).  face is
    github-contents | host-file | github-owner; payload is the parsed
    JSON (or None when the body is not JSON).  The file face scans the
    decoded file bytes (the verbatim text of the watched file), the
    listing faces scan the raw body (file names are what appears there)."""
    if face == "host-file":
        return body, body, None
    if face == "github-owner":
        if isinstance(payload, list):
            return (listing_digest(payload, ("full_name", "pushed_at")),
                    body, None)
        return body, body, "owner listing did not parse as a JSON array"
    # github-contents: array = directory listing, file object = decoded bytes
    if isinstance(payload, list):
        return listing_digest(payload, ("name", "sha")), body, None
    if isinstance(payload, dict) and payload.get("type") == "file" \
            and isinstance(payload.get("content"), str):
        try:
            decoded = base64.b64decode(payload["content"])
        except Exception:
            return body, body, "file content did not decode from base64"
        return decoded, decoded, None
    return body, body, "contents response was neither a listing nor a file" \
        " object"


def pin_check(pin, content):
    """Config hash_pin vs fetched content -> (matches, expected, actual).
    Forms: sha256:<64 hex> covers the sha256 of the bytes; bytes:<decimal>
    covers the byte count (the ticket's byte-compare baseline form)."""
    if pin.startswith("sha256:"):
        expected = pin
        actual = "sha256:" + sha256_hex(content)
    else:
        expected = pin
        actual = "bytes:%d" % len(content)
    return expected == actual, expected, actual


def resolve_phase(payload, phase_field):
    """Dotted-path resolution of phase_field on a JSON object -> (value,
    True) or (None, False) when the object or an intermediate is missing
    (registered as an honest note, never a failure)."""
    if not phase_field or not isinstance(payload, dict):
        return None, False
    node = payload
    for part in phase_field.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None, False
    return node, True


def parse_heartbeat(value):
    """heartbeat value -> aware UTC datetime or None (unparseable, honest)."""
    if not isinstance(value, str) or not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


# ---- per-signal judgment ----------------------------------------------------

def fetch_account(result):
    """NETRED account that rides every row's evidence (ticket 13
    acceptance 5: every shot, failed shots included, is accounted)."""
    return {"url": result.get("_url", ""), "attempts": result["attempts"],
            "statuses": result["statuses"],
            "backoff_applied": result["backoff_applied"],
            "max_retries": result["max_retries"]}


def _flag(outcome, evidence):
    return {"outcome": outcome, "evidence": evidence}


def judge_content(payload, body, sig, content, scan_bytes, note, prev_digest,
                  now):
    """Shared content face over a fetched body -> flags list.  The drift
    branch needs `content` (bytes the baseline covers); a fetch failure
    never reaches this function, which is the explicit fetch-failure is
    not drift separation (ticket 13 acceptance 5)."""
    flags = []
    text = body_text(scan_bytes if scan_bytes is not None else body)
    keywords = sig.get("conclusion_keywords") or []
    kw, quote = keyword_hit(text, keywords)
    if kw is not None:
        flags.append(_flag(CONCLUSION_HIT, {"keyword": kw, "quote": quote}))
    kind = sig["kind"]
    if kind == "status-endpoint":
        phase_field = sig.get("phase_field", "")
        if phase_field:
            phase, ok = resolve_phase(payload, phase_field)
            if ok:
                phase_str = phase if isinstance(phase, str) \
                    else json.dumps(phase)
                if phase_str in (sig.get("done_phases") or []):
                    flags.append(_flag(PHASE_FLIP,
                                       {"field": phase_field,
                                        "value": phase_str}))
            else:
                flags.append(_flag("phase-unavailable",
                                   {"field": phase_field,
                                    "note": "field did not resolve; the"
                                            " phase face is not judged"}))
        hb_field = sig.get("heartbeat_field", DEFAULT_HEARTBEAT_FIELD)
        stale_min = sig.get("heartbeat_stale_minutes",
                            DEFAULT_HEARTBEAT_STALE_MINUTES)
        if isinstance(payload, dict) and hb_field in payload:
            hb = parse_heartbeat(payload.get(hb_field))
            if hb is None:
                flags.append(_flag(HEARTBEAT_UNPARSEABLE,
                                   {"field": hb_field,
                                    "value": payload.get(hb_field)}))
            else:
                age_min = (now - hb).total_seconds() / 60.0
                if age_min < 0:
                    flags.append(_flag("heartbeat-future",
                                       {"field": hb_field,
                                        "value": payload.get(hb_field),
                                        "note": "heartbeat is in the future"
                                                " (clock skew); staleness is"
                                                " not judged"}))
                elif age_min > stale_min:
                    flags.append(_flag(HEARTBEAT_STALE,
                                       {"field": hb_field,
                                        "value": payload.get(hb_field),
                                        "age_minutes": round(age_min, 2),
                                        "stale_minutes": stale_min,
                                        "note": "target silent death: the"
                                                " heartbeat stopped beyond"
                                                " the threshold; an honest"
                                                " record, not a false alarm"}))
        elif isinstance(payload, dict):
            flags.append(_flag("heartbeat-absent",
                               {"field": hb_field,
                                "note": "heartbeat field absent; liveness"
                                        " is not judged on this endpoint"}))
    if note is not None:
        flags.append(_flag("body-unusable", {"note": note}))
        return flags
    if content is None:
        return flags
    digest = sha256_hex(content)
    pin = sig.get("hash_pin")
    if pin:
        matches, expected, actual = pin_check(pin, content)
        if not matches:
            flags.append(_flag(PIN_DRIFT, {"expected": expected,
                                           "actual": actual}))
            return flags
        flags.append(_flag(CLEAN, {"pin": expected}))
        return flags
    if prev_digest is not None:
        if digest != prev_digest:
            flags.append(_flag(ROUND_CHANGE,
                               {"previous_digest": prev_digest,
                                "digest": digest}))
        else:
            flags.append(_flag(CLEAN, {"digest": digest}))
        return flags
    flags.append(_flag(BASELINE, {"digest": digest,
                                  "note": "first observation; the digest is"
                                          " registered as the local"
                                          " baseline"}))
    return flags


def order_flags(flags):
    """Headline = the first flag by OUTCOME_PRECEDENCE; the rest ride the
    row notes verbatim.  Unknown classes sort last (honest notes)."""
    def rank(flag):
        outcome = flag["outcome"]
        return OUTCOME_PRECEDENCE.index(outcome) \
            if outcome in OUTCOME_PRECEDENCE else len(OUTCOME_PRECEDENCE)
    return sorted(flags, key=rank)


def _transport_block_row(row, result, extra_note=None):
    """Shared registration of a blocked or failed fetch: unverifiable when
    the failure classifies as such (the net_probe shapes, ticket 13
    acceptance 4; nothing about the target is claimed), fetch-failed
    otherwise, and the drift branch is never entered from a fetch failure
    (ticket 13 acceptance 5)."""
    if result["status"] is None and result["reason_class"] is not None:
        row["outcome"] = UNVERIFIABLE
        row["ok"] = False
        row["evidence"] = {"reason_class": result["reason_class"],
                           "error": result["error"],
                           "fetch": row["fetch"],
                           "note": "the fetch path itself was blocked;"
                                   " nothing about the target is claimed"}
        return row
    row["outcome"] = FETCH_FAILED
    row["ok"] = False
    evidence = {"fetch": row["fetch"],
                "note": "fetch failure; the drift branch is not entered"
                        " (ticket 13 acceptance 5)"}
    if result["status"] is not None:
        evidence["status"] = result["status"]
    if result["error"]:
        evidence["error"] = result["error"]
    if extra_note:
        evidence["note"] = extra_note
    row["evidence"] = evidence
    return row


def check_repo_path(sig, cfg, prev_digest, now, _open, _sleep):
    repo = sig["repo"]
    path = (sig.get("path") or "").lstrip("/")
    if "/" in repo:
        face = "github-contents"
        suffix = ("?ref=HEAD" if not path else "/%s?ref=HEAD" % path)
        url = "%s/repos/%s/contents%s" % (GITHUB_API, repo, suffix)
    elif "." in repo:
        face = "host-file"
        url = "https://%s/%s" % (repo, path)
    else:
        face = "github-owner"
        url = "%s/users/%s/repos?sort=pushed&per_page=10" % (GITHUB_API, repo)
    result = fetch_netred(url, cfg["max_retries"], cfg["backoff_base_seconds"],
                          _open=_open, _sleep=_sleep)
    result["_url"] = url
    row = {"signal_id": sig["id"], "kind": sig["kind"], "face": face,
           "fetch": fetch_account(result)}
    if result["status"] is None or result["status"] != 200:
        return _transport_block_row(row, result)
    try:
        payload = json.loads(result["body"].decode("utf-8", "replace"))
    except ValueError:
        payload = None
    content, scan_bytes, note = interpret_repo_body(face, payload,
                                                    result["body"])
    flags = judge_content(payload, result["body"], sig, content, scan_bytes,
                          note, prev_digest, now)
    return _finish_row(row, flags, result, content)


def check_status_endpoint(sig, cfg, prev_digest, now, _open, _sleep):
    url = sig["url"]
    result = fetch_netred(url, cfg["max_retries"], cfg["backoff_base_seconds"],
                          _open=_open, _sleep=_sleep)
    result["_url"] = url
    row = {"signal_id": sig["id"], "kind": sig["kind"],
           "fetch": fetch_account(result)}
    if result["status"] is None or result["status"] != 200:
        return _transport_block_row(row, result)
    try:
        payload = json.loads(result["body"].decode("utf-8", "replace"))
    except ValueError:
        payload = None
    if payload is None:
        flags = [_flag("body-unusable",
                       {"note": "status endpoint body did not parse as"
                                " JSON"})]
        scan_bytes = result["body"]
    else:
        scan_bytes = result["body"]
        flags = judge_content(payload, result["body"], sig, result["body"],
                              scan_bytes, None, prev_digest, now)
    return _finish_row(row, flags, result, result["body"])


def check_zulip(sig, cfg, prev_digest, now, _open, _sleep):
    """The built-in web-public recipe: no-auth llms.txt face then no-auth
    messages face.  A 401/403 on the messages face registers unverifiable
    honestly (ticket 13 acceptance 3); a 401 on llms.txt alone is an
    honest note."""
    stream = urllib.parse.quote(sig["stream"], safe="")
    topic = urllib.parse.quote(sig["topic_hint"], safe="")
    llms_url = ZULIP_WEB_PUBLIC_HOST + "/llms.txt"
    msgs_url = ("%s/api/v1/messages?stream=%s&topic=%s&num_messages=100"
                % (ZULIP_WEB_PUBLIC_HOST, stream, topic))
    llms = fetch_netred(llms_url, cfg["max_retries"],
                        cfg["backoff_base_seconds"], _open=_open,
                        _sleep=_sleep)
    llms["_url"] = llms_url
    msgs = fetch_netred(msgs_url, cfg["max_retries"],
                        cfg["backoff_base_seconds"], _open=_open,
                        _sleep=_sleep)
    msgs["_url"] = msgs_url
    row = {"signal_id": sig["id"], "kind": sig["kind"],
           "fetch": {"recipe": "zulip-web-public no-auth (llms.txt then"
                               " api/v1/messages)",
                     "llms_face": fetch_account(llms),
                     "messages_face": fetch_account(msgs)}}
    notes = []
    if llms["status"] is not None and llms["status"] != 200:
        notes.append("llms.txt face answered %s (recorded honestly)"
                     % llms["status"])
    if msgs["status"] is None and msgs["reason_class"] is not None:
        row["outcome"] = UNVERIFIABLE
        row["ok"] = False
        row["evidence"] = {"reason_class": msgs["reason_class"],
                           "error": msgs["error"], "recipe_notes": notes,
                           "fetch": row["fetch"],
                           "note": "the fetch path itself was blocked;"
                                   " nothing about the target is claimed"}
        return row
    if msgs["status"] in (401, 403):
        row["outcome"] = UNVERIFIABLE
        row["ok"] = False
        row["evidence"] = {"status": msgs["status"],
                           "recipe_notes": notes,
                           "fetch": row["fetch"],
                           "note": "the web-public recipe was refused on"
                                   " the messages face; the login wall"
                                   " applies there; registered"
                                   " unverifiable, nothing fabricated"}
        return row
    if msgs["status"] is None or msgs["status"] != 200:
        return _transport_block_row(row, msgs,
                                    extra_note="the zulip messages face"
                                               " failed; recipe notes: %s"
                                               % ("; ".join(notes) or
                                                  "none"))
    try:
        payload = json.loads(msgs["body"].decode("utf-8", "replace"))
    except ValueError:
        payload = None
    if payload is None:
        flags = [_flag("body-unusable",
                       {"note": "messages body did not parse as JSON"})]
    else:
        flags = judge_content(payload, msgs["body"], sig, msgs["body"],
                              msgs["body"], None, prev_digest, now)
    if notes:
        for flag in flags:
            flag.setdefault("evidence", {})["recipe_notes"] = list(notes)
    return _finish_row(row, flags, msgs, msgs["body"])


def _finish_row(row, flags, result, content):
    """Ordered flags -> headline outcome + verbatim notes; the digest and
    byte size of the covered content ride every fetched row."""
    ordered = order_flags(flags)
    headline = ordered[0]
    row["outcome"] = headline["outcome"]
    row["ok"] = headline["outcome"] in OK_TRUE
    row["notes"] = ["%s: %s" % (f["outcome"],
                                json.dumps(f.get("evidence", {}),
                                           ensure_ascii=False,
                                           sort_keys=True))
                    for f in ordered[1:]]
    evidence = dict(headline.get("evidence", {}))
    evidence["fetch"] = row["fetch"]
    row["evidence"] = evidence
    if content is not None:
        row["digest"] = sha256_hex(content)
        row["digest_algo"] = "sha256"
        row["size_bytes"] = len(content)
    return row


CHECKERS = {"repo-path": check_repo_path,
            "status-endpoint": check_status_endpoint,
            "zulip-web-public": check_zulip}


# ---- ledger (append-only, ticket 13 acceptance 6) ---------------------------

def read_baselines(path):
    """Ledger -> (baselines {signal_id: digest}, total, bad_lines).  The
    last row carrying a digest per signal id is the baseline memory;
    corrupt lines are skipped and counted, never guessed."""
    baselines = {}
    total = 0
    bad = 0
    if not os.path.isfile(path):
        return baselines, total, bad
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                row = json.loads(line)
            except ValueError:
                bad += 1
                continue
            if not isinstance(row, dict) \
                    or row.get("schema") != LEDGER_SCHEMA:
                bad += 1
                continue
            digest = row.get("digest")
            if isinstance(digest, str) and digest:
                baselines[row.get("signal_id")] = digest
    return baselines, total, bad


def append_rows(path, rows):
    """Append-only write; returns the exact pre-append byte snapshot so
    the read-back invariant can prove the prefix never changed."""
    pre_bytes = b""
    if os.path.isfile(path):
        with io.open(path, "rb") as fh:
            pre_bytes = fh.read()
    else:
        parent = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(parent):
            raise OSError("ledger directory does not exist: %s" % parent)
    with io.open(path, "a", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True)
                     + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return pre_bytes


def verify_append(path, pre_bytes, count):
    """Read-back invariant (append-only proof): the pre-existing byte
    prefix is byte-identical after the append, and the appended lines
    parse as ledger rows carrying at_utc, actor and round_label.  Returns
    an error string or None."""
    try:
        with io.open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        return "ledger read-back failed: %s" % exc
    if len(data) < len(pre_bytes) or data[:len(pre_bytes)] != pre_bytes:
        return "the pre-append ledger prefix changed (append-only violation)"
    tail = data[len(pre_bytes):].decode("utf-8", errors="replace")
    lines = [l for l in tail.split("\n") if l.strip()]
    if len(lines) != count:
        return "appended line count %d != expected %d" % (len(lines), count)
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            return "an appended line does not parse as JSON: %r" % line[:80]
        if not isinstance(row, dict) or row.get("schema") != LEDGER_SCHEMA:
            return "an appended line is not a %s row" % LEDGER_SCHEMA
        for key in ("at_utc", "actor", "round_label"):
            if key not in row:
                return "an appended row lacks the %s key" % key
    return None


# ---- round runner -----------------------------------------------------------

def run_round(cfg, args, now=None, _open=None, _sleep=None):
    """One watch round -> process exit code.  Every signal produces one
    honest row; a registration is data and never an error."""
    now = now if now is not None else utc_now()
    ledger = args.ledger
    baselines, total, bad_prior = read_baselines(ledger)
    rows = []
    counts = {}
    for sig in cfg["signals"]:
        sig = dict(sig)
        prev = baselines.get(sig["id"])
        row = CHECKERS[sig["kind"]](sig, cfg, prev, now, _open=_open,
                                    _sleep=_sleep)
        row["schema"] = LEDGER_SCHEMA
        row["at_utc"] = fmt_utc(now)
        row["actor"] = args.actor
        row["round_label"] = args.round_label
        rows.append(row)
        counts[row["outcome"]] = counts.get(row["outcome"], 0) + 1
    print("=== CLAIM-WATCH ===")
    print("signals=%d actor=%s round_label=%s ledger=%s"
          % (len(rows), args.actor, args.round_label, ledger))
    for row in rows:
        print("signal %s outcome=%s ok=%s%s"
              % (row["signal_id"], row["outcome"], row["ok"],
                 (" digest=%s" % row["digest"][:12])
                 if row.get("digest") else ""))
    ok_count = sum(1 for r in rows if r["ok"])
    dist = " ".join("%s=%d" % (k, counts[k]) for k in sorted(counts))
    print("summary: signals=%d ok=%d %s" % (len(rows), ok_count, dist))
    pre_bytes = append_rows(ledger, rows)
    err = verify_append(ledger, pre_bytes, len(rows))
    if err:
        print("FAIL-LOUD: ledger invariant red: %s" % err, file=sys.stderr)
        return 1
    print("ledger: %s rows_appended=%d prior_lines=%d bad_lines_prior=%d"
          " append-only invariant verified" % (ledger, len(rows), total,
                                               bad_prior))
    return 0


# ---- offline selftest -------------------------------------------------------

class FakeResp(object):
    """Canned response (urlopen stand-in, zero network)."""

    def __init__(self, status, body=b""):
        self.status = status
        self._body = body if isinstance(body, bytes) else body.encode("utf-8")

    def read(self):
        return self._body

    def close(self):
        pass


def canned_open(steps):
    """steps: list of (status, body) or Exception instances, consumed in
    order per fetch call (each fetch_netred call consumes its own
    sequence); a plain Exception raises on every shot."""
    seq = list(steps)

    def _open(url, timeout=None):
        if not seq:
            raise AssertionError("canned transport exhausted for %s" % url)
        step = seq.pop(0)
        if isinstance(step, Exception):
            raise step
        return FakeResp(step[0], step[1])

    return _open


def url_open(routes):
    """URL-routed canned transport: {url: steps-list}; each GET consumes
    one step of its route."""
    state = {u: list(s) for u, s in routes.items()}

    def _open(url, timeout=None):
        seq = state.get(url)
        if seq is None:
            raise AssertionError("unexpected canned URL %s" % url)
        step = seq.pop(0)
        if isinstance(step, Exception):
            raise step
        return FakeResp(step[0], step[1])

    return _open


def _cfg(signals, max_retries=3, base=2.0):
    return {"schema": SCHEMA, "max_retries": max_retries,
            "backoff_base_seconds": base, "signals": signals}


class _Args(object):
    def __init__(self, ledger, actor="test-actor", round_label="RT"):
        self.config = None
        self.ledger = ledger
        self.actor = actor
        self.round_label = round_label


def selftest():
    """Frozen vector group (zero network, canned transport, virtual clock,
    zero writes outside one temporary directory):
    V1 config schema matrix: the three frozen forms accepted; unknown
       kind / missing key / unknown key / bad hash_pin / duplicate id /
       empty signals / wrong schema all rejected
    V2 keyword hit and pins (host-file face): keyword hit quotes the
       matching text verbatim with ok=false; sha256 pin match cleans;
       bytes pin mismatch is pin-drift
    V3 baseline and round-change (contents listing face): first round
       registers the baseline; a changed listing is round-change; the
       same listing cleans
    V4 status endpoint: phase flip quotes the phase value; stale
       heartbeat registers target silent death (own class, virtual
       clock); a fresh heartbeat and an absent heartbeat field do not
       alarm
    V5 zulip recipe: no-auth URL shape, llms.txt then messages; keyword
       hit on messages; 401 registers unverifiable honestly; llms 401
       with readable messages is an honest note
    V6 unverifiable classification: canned TLS / DNS / timeout failures
       register unverifiable with the net_probe reason class, never a
       claim about the target
    V7 NETRED: 429 backoff schedule from config then success; 404 is a
       no-retry semantic face and never enters the drift branch; dns
       retries then unverifiable; exhausted 429s land fetch-failed
    V8 ledger: append-only prefix invariant, every row carries actor /
       round_label / at_utc, corrupt prior lines skipped and counted
    V9 CLI faces: --help 0; live round without --config 9; missing
       config file 9; schema drift 2; --offline-selftest green
    V10 verbatim quote bounds: clipped excerpts carry the ellipsis marks
        and the keyword verbatim
    """
    failures = []

    def check(name, cond, detail=""):
        if not cond:
            failures.append("%s: %s" % (name, detail or "assertion red"))

    slept = []
    nosleep = lambda s: slept.append(s)
    vnow = datetime(2026, 11, 21, 12, 0, 0, tzinfo=timezone.utc)
    kw_family = ["full compilation passed", "kernel replay passed",
                 "author retraction"]

    # ---- V1 schema matrix ----
    good_repo = {"id": "s1", "kind": "repo-path", "repo": "o/r",
                 "path": "p.json", "conclusion_keywords": ["kw"]}
    good_status = {"id": "s2", "kind": "status-endpoint", "url": "https://x",
                   "phase_field": "phase", "done_phases": [],
                   "conclusion_keywords": []}
    good_zulip = {"id": "s3", "kind": "zulip-web-public", "stream": "general",
                  "topic_hint": "113488", "conclusion_keywords": ["kw"]}
    cfg, errs = validate_config(_cfg([good_repo, good_status, good_zulip]))
    check("V1 three frozen forms", cfg is not None and not errs, str(errs))
    for bad in ({"id": "x", "kind": "rss", "url": "https://x"},
                dict(good_repo, id=None),
                {"id": "y", "kind": "repo-path", "repo": "o/r",
                 "path": "p", "conclusion_keywords": [], "surprise": 1},
                dict(good_repo, hash_pin="md5:abc"),
                {"id": "s1", "kind": "repo-path", "repo": "o2/r2",
                 "path": "p", "conclusion_keywords": []}):
        _, errs = validate_config(_cfg([good_repo, bad])
                                  if bad.get("id") == "s1" else _cfg([bad]))
        check("V1 rejects %r" % (bad.get("kind"),), bool(errs), "accepted")
    _, errs = validate_config(_cfg([]))
    check("V1 empty signals rejected", bool(errs))
    _, errs = validate_config({"schema": "other/1", "signals": [good_repo]})
    check("V1 wrong schema rejected", bool(errs))
    _, errs = validate_config(_cfg([good_repo], max_retries=-1))
    check("V1 negative retries rejected", bool(errs))

    # ---- V2 keyword hit + pins (host-file face) ----
    sig_kw = {"id": "kw1", "kind": "repo-path", "repo": "example.org",
              "path": "remark.pdf", "conclusion_keywords": kw_family}
    body = ("The author writes that the full compilation passed and the "
            "kernel replay passed; no retraction was filed.")
    row = check_repo_path(sig_kw, _cfg([sig_kw]), None, vnow,
                          _open=url_open({"https://example.org/remark.pdf":
                                          [(200, body)]}), _sleep=nosleep)
    check("V2 conclusion-hit", row["outcome"] == CONCLUSION_HIT
          and row["ok"] is False, row["outcome"])
    check("V2 quote verbatim", "full compilation passed"
          in row["evidence"]["quote"], row["evidence"].get("quote", ""))
    body_clean = "Nothing to report in this file."
    sig_pin = dict(sig_kw, hash_pin="sha256:" + sha256_hex(
        body_clean.encode("utf-8")), conclusion_keywords=[])
    row = check_repo_path(sig_pin, _cfg([sig_pin]), None, vnow,
                          _open=url_open({"https://example.org/remark.pdf":
                                          [(200, body_clean)]}),
                          _sleep=nosleep)
    check("V2 sha256 pin match cleans", row["outcome"] == CLEAN
          and row["ok"] is True, row["outcome"])
    sig_bytes = dict(sig_kw, hash_pin="bytes:245114", conclusion_keywords=[])
    row = check_repo_path(sig_bytes, _cfg([sig_bytes]), None, vnow,
                          _open=url_open({"https://example.org/remark.pdf":
                                          [(200, body_clean)]}),
                          _sleep=nosleep)
    check("V2 bytes pin mismatch is pin-drift", row["outcome"] == PIN_DRIFT
          and row["ok"] is False, row["outcome"])
    check("V2 pin evidence", row["evidence"]["expected"] == "bytes:245114"
          and row["evidence"]["actual"].startswith("bytes:"),
          str(row["evidence"]))

    # ---- V3 baseline and round-change (contents listing face) ----
    list_a = [{"name": "NOTES.md", "sha": "aaa", "type": "file"},
              {"name": "run.log", "sha": "bbb", "type": "file"}]
    list_b = list_a + [{"name": "comparator_out.json", "sha": "ccc",
                        "type": "file"}]
    sig_dir = {"id": "d1", "kind": "repo-path",
               "repo": "deicyde/riemann-hypothesis", "path": "verification",
               "conclusion_keywords": []}
    cfg_dir = _cfg([sig_dir])
    row1 = check_repo_path(sig_dir, cfg_dir, None, vnow,
                           _open=url_open({sig_url(sig_dir): [(200, json.dumps(list_a))]}),
                           _sleep=nosleep)
    check("V3 baseline registered", row1["outcome"] == BASELINE
          and row1["ok"] is True and row1.get("digest"), row1["outcome"])
    row2 = check_repo_path(sig_dir, cfg_dir, row1["digest"], vnow,
                           _open=url_open({sig_url(sig_dir): [(200, json.dumps(list_b))]}),
                           _sleep=nosleep)
    check("V3 new file is round-change", row2["outcome"] == ROUND_CHANGE
          and row2["ok"] is False, row2["outcome"])
    row3 = check_repo_path(sig_dir, cfg_dir, row1["digest"], vnow,
                           _open=url_open({sig_url(sig_dir): [(200, json.dumps(list_a))]}),
                           _sleep=nosleep)
    check("V3 unchanged listing cleans", row3["outcome"] == CLEAN
          and row3["ok"] is True, row3["outcome"])

    # ---- V4 status endpoint: phase flip + heartbeat faces ----
    hb_fresh = fmt_utc(datetime(2026, 11, 21, 11, 30, 0, tzinfo=timezone.utc))
    hb_stale = fmt_utc(datetime(2026, 11, 21, 9, 0, 0, tzinfo=timezone.utc))
    sig_st = {"id": "st1", "kind": "status-endpoint",
              "url": "http://106.14.11.164/api/status",
              "phase_field": "phase", "done_phases": ["audit", "complete"],
              "conclusion_keywords": []}
    cfg_st = _cfg([sig_st])
    st_url = sig_st["url"]

    def st_body(phase, hb):
        return json.dumps({"phase": phase, "heartbeat_at": hb,
                           "detail": "phase tracker"})

    row = check_status_endpoint(sig_st, cfg_st, None, vnow,
                                _open=url_open({st_url: [(200, st_body("audit", hb_fresh))]}),
                                _sleep=nosleep)
    check("V4 phase flip", row["outcome"] == PHASE_FLIP and row["ok"] is False
          and row["evidence"]["value"] == "audit", row["outcome"])
    row = check_status_endpoint(sig_st, cfg_st, None, vnow,
                                _open=url_open({st_url: [(200, st_body("verify", hb_stale))]}),
                                _sleep=nosleep)
    check("V4 heartbeat stale is own class", row["outcome"] == HEARTBEAT_STALE
          and row["ok"] is False, row["outcome"])
    check("V4 stale evidence", row["evidence"]["age_minutes"] == 180.0
          and row["evidence"]["stale_minutes"] == 90
          and "silent death" in row["evidence"]["note"],
          str(row["evidence"]))
    row = check_status_endpoint(sig_st, cfg_st, None, vnow,
                                _open=url_open({st_url: [(200, st_body("verify", hb_fresh))]}),
                                _sleep=nosleep)
    check("V4 fresh heartbeat does not alarm", row["ok"] is True
          and row["outcome"] in (CLEAN, BASELINE), row["outcome"])
    body_nohb = json.dumps({"phase": "verify"})
    row = check_status_endpoint(sig_st, cfg_st, None, vnow,
                                _open=url_open({st_url: [(200, body_nohb)]}),
                                _sleep=nosleep)
    check("V4 absent heartbeat is a note, not an alarm",
          row["ok"] is True and row["outcome"] in (CLEAN, BASELINE)
          and any("heartbeat-absent" in n for n in row["notes"]),
          "%s %s" % (row["outcome"], row["notes"]))

    # ---- V5 zulip recipe ----
    host = ZULIP_WEB_PUBLIC_HOST
    sig_z = {"id": "z1", "kind": "zulip-web-public", "stream": "general",
             "topic_hint": "113488",
             "conclusion_keywords": ["kernel replay passed"]}
    cfg_z = _cfg([sig_z])
    llms_url = host + "/llms.txt"
    msgs_url = host + "/api/v1/messages?stream=general&topic=113488&num_messages=100"
    check("V5 recipe URLs are no-auth", "Authorization" not in msgs_url
          and msgs_url.startswith("https://"), msgs_url)
    msgs_hit = json.dumps({"messages": [{"content": "the kernel replay "
                                                     "passed on my machine"}]})
    routes = {llms_url: [(200, "# lean zulip llms")],
              msgs_url: [(200, msgs_hit)]}
    row = check_zulip(sig_z, cfg_z, None, vnow, _open=url_open(routes),
                      _sleep=nosleep)
    check("V5 zulip keyword hit", row["outcome"] == CONCLUSION_HIT
          and row["ok"] is False, row["outcome"])
    check("V5 quote carries the verbatim message",
          "kernel replay passed" in row["evidence"]["quote"],
          row["evidence"].get("quote", ""))
    routes = {llms_url: [(200, "# lean zulip llms")], msgs_url: [(401, b"")]}
    row = check_zulip(sig_z, cfg_z, None, vnow, _open=url_open(routes),
                      _sleep=nosleep)
    check("V5 401 registers unverifiable honestly",
          row["outcome"] == UNVERIFIABLE and row["ok"] is False
          and "nothing fabricated" in row["evidence"]["note"],
          row["outcome"])
    routes = {llms_url: [(401, b"")], msgs_url: [(200, msgs_hit)]}
    row = check_zulip(sig_z, cfg_z, None, vnow, _open=url_open(routes),
                      _sleep=nosleep)
    check("V5 llms 401 with readable messages keeps the headline",
          row["outcome"] == CONCLUSION_HIT
          and any("llms.txt face answered 401" in n for n in row["notes"]),
          "%s %s" % (row["outcome"], row["notes"]))

    # ---- V6 unverifiable classification (net_probe shapes) ----
    import socket
    import ssl
    cfg_zero = _cfg([sig_st], max_retries=0, base=1.0)
    tls = urllib.error.URLError(ssl.SSLError("SSL: HANDSHAKE_FAILURE_ALERT"))
    dns = urllib.error.URLError(socket.gaierror(
        8, "nodename nor servname provided"))
    tot = socket.timeout("timed out")
    for name, exc, want in (("tls", tls, net_probe.REASON_TLS_BLOCKED),
                            ("dns", dns, net_probe.REASON_DNS),
                            ("timeout", tot, net_probe.REASON_TIMEOUT)):
        row = check_status_endpoint(sig_st, cfg_zero, None, vnow,
                                    _open=canned_open([exc]), _sleep=nosleep)
        check("V6 %s unverifiable" % name, row["outcome"] == UNVERIFIABLE
              and row["ok"] is False
              and row["evidence"]["reason_class"] == want,
              "%s %s" % (row["outcome"], row["evidence"].get("reason_class")))

    # ---- V7 NETRED ----
    cfg_fast = _cfg([sig_st], max_retries=2, base=1.0)
    row = check_status_endpoint(sig_st, cfg_fast, None, vnow,
                                _open=url_open({st_url: [(429, b""), (429, b""),
                                                         (200, st_body("verify", hb_fresh))]}),
                                _sleep=nosleep)
    check("V7 429 backoff then success", row["ok"] is True
          and row["outcome"] in (CLEAN, BASELINE)
          and row["fetch"]["attempts"] == 3
          and row["fetch"]["backoff_applied"] == [1.0, 2.0]
          and row["fetch"]["statuses"] == [429, 429, 200],
          str(row["fetch"]))
    row = check_status_endpoint(sig_st, cfg_fast, None, vnow,
                                _open=url_open({st_url: [(404, b"")]}),
                                _sleep=nosleep)
    check("V7 404 no retry, never drift", row["outcome"] == FETCH_FAILED
          and row["fetch"]["attempts"] == 1
          and row["outcome"] not in DRIFT_OUTCOMES
          and row["fetch"]["statuses"] == [404], str(row["fetch"]))
    row = check_status_endpoint(sig_st, cfg_fast, None, vnow,
                                _open=url_open({st_url: [dns, dns, dns]}),
                                _sleep=nosleep)
    check("V7 dns retries then unverifiable",
          row["outcome"] == UNVERIFIABLE
          and row["fetch"]["attempts"] == 3
          and row["evidence"]["reason_class"] == net_probe.REASON_DNS,
          str(row["fetch"]))
    row = check_status_endpoint(sig_st, cfg_fast, None, vnow,
                                _open=url_open({st_url: [(429, b""), (429, b""),
                                                         (429, b"")]}),
                                _sleep=nosleep)
    check("V7 exhausted 429s fetch-failed", row["outcome"] == FETCH_FAILED
          and row["fetch"]["attempts"] == 3
          and row["outcome"] not in DRIFT_OUTCOMES, str(row["fetch"]))

    # ---- V8 ledger append-only + baselines + bad lines ----
    tmp = tempfile.mkdtemp(prefix="claim_watch_self_")
    try:
        ledger = os.path.join(tmp, "led.jsonl")
        args = _Args(ledger)
        sig_ld = {"id": "l1", "kind": "repo-path", "repo": "example.org",
                  "path": "f.txt", "conclusion_keywords": []}
        cfg_ld = _cfg([sig_ld])
        ld_url = "https://example.org/f.txt"
        rc = run_round(cfg_ld, args, now=vnow,
                       _open=url_open({ld_url: [(200, "v1 body")]}),
                       _sleep=nosleep)
        check("V8 first round rc 0", rc == 0, str(rc))
        with io.open(ledger, "rb") as fh:
            snap = fh.read()
        with io.open(ledger, "r", encoding="utf-8") as fh:
            first_rows = [json.loads(l) for l in fh if l.strip()]
        check("V8 row keys", all(("actor" in r and "round_label" in r
                                  and "at_utc" in r and "schema" in r)
                                 for r in first_rows), str(first_rows)[:120])
        check("V8 actor namespace", all(r["actor"] == "test-actor"
                                        for r in first_rows))
        rc = run_round(cfg_ld, args, now=vnow,
                       _open=url_open({ld_url: [(200, "v1 body")]}),
                       _sleep=nosleep)
        check("V8 second round rc 0", rc == 0, str(rc))
        with io.open(ledger, "rb") as fh:
            grown = fh.read()
        check("V8 append-only prefix", grown.startswith(snap)
              and len(grown) > len(snap), "prefix changed")
        with io.open(ledger, "r", encoding="utf-8") as fh:
            lines = [l for l in fh if l.strip()]
        last = json.loads(lines[-1])
        check("V8 unchanged body cleans via ledger memory",
              last["outcome"] == CLEAN and last["ok"] is True,
              last["outcome"])
        with io.open(ledger, "a", encoding="utf-8") as fh:
            fh.write("not json at all\n")
        base, total, bad = read_baselines(ledger)
        check("V8 corrupt line skipped and counted", bad == 1 and total == 3,
              "bad=%d total=%d" % (bad, total))
        check("V8 baseline memory survives bad lines",
              base.get("l1") == last.get("digest"), str(base))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---- V9 CLI faces ----
    p = run_args(["--help"])
    check("V9 help", p.returncode == 0 and "usage" in p.stdout,
          p.stdout[-120:])
    p = run_args([])
    check("V9 live round without config is rc 9", p.returncode == 9,
          "%d %s" % (p.returncode, p.stdout[-120:]))
    p = run_args(["--config", "no_such_config_file.json"])
    check("V9 missing config file is rc 9", p.returncode == 9,
          "%d %s" % (p.returncode, p.stdout[-120:]))
    tmp = tempfile.mkdtemp(prefix="claim_watch_self_")
    try:
        bad_cfg = os.path.join(tmp, "bad.json")
        with io.open(bad_cfg, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"schema": "nope/9", "signals": []}))
        p = run_args(["--config", bad_cfg])
        check("V9 schema drift is rc 2", p.returncode == 2,
              "%d %s" % (p.returncode, p.stdout[-200:]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---- V10 quote bounds ----
    pad = "x" * 500
    body10 = pad + "the author retraction appeared here" + pad
    kw10, quote10 = keyword_hit(body10, ["author retraction"])
    check("V10 clipped both sides", quote10.startswith("...")
          and quote10.endswith("...") and "author retraction" in quote10,
          quote10[:60])
    short = "author retraction only"
    kw10b, quote10b = keyword_hit(short, ["author retraction"])
    check("V10 unclipped quote has no marks",
          not quote10b.startswith("...") and not quote10b.endswith("...")
          and quote10b == short, quote10b)

    if failures:
        for line in failures:
            print("CLAIM-WATCH-SELFTEST FAIL %s" % line, file=sys.stderr)
        return 1
    print("CLAIM-WATCH-SELFTEST PASS: schema matrix (three frozen forms,"
          " rejections)/keyword hit verbatim quote + sha256 and bytes"
          " pins/baseline and round-change/phase flip + heartbeat silent"
          " death + absent field/zulip no-auth recipe + honest"
          " unverifiable/unverifiable tls dns timeout/NETRED backoff"
          " schedule + no-retry semantic faces + never-drift/ledger"
          " append-only + actor round label at_utc + bad lines/cli faces/"
          "quote bounds - ten sections all pass")
    return 0


def sig_url(sig):
    """Canned-route URL key for a repo-path signal (mirrors the fetch
    face builder; selftest helper only)."""
    repo = sig["repo"]
    path = (sig.get("path") or "").lstrip("/")
    if "/" in repo:
        suffix = "?ref=HEAD" if not path else "/%s?ref=HEAD" % path
        return "%s/repos/%s/contents%s" % (GITHUB_API, repo, suffix)
    if "." in repo:
        return "https://%s/%s" % (repo, path)
    return "%s/users/%s/repos?sort=pushed&per_page=10" % (GITHUB_API, repo)


def run_args(argv):
    """Selftest helper: run this tool in a subprocess (stdout and stderr
    merged), the net_probe convention."""
    import subprocess
    e = dict(os.environ)
    p = subprocess.run([sys.executable, "-B",
                        os.path.join(_TOOLS_DIR, PROG + ".py")] + list(argv),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=e)
    p.stdout = p.stdout.decode("utf-8", errors="replace") \
        if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(
        prog=PROG + ".py",
        description="native resident claim watch: one round over a signal"
                    " config, honest per-signal ledger rows (ticket 13;"
                    " the live face is the network face)")
    ap.add_argument("--config", default=None, metavar="JSON",
                    help="signal config file (schema"
                         " rocqwash-claim-watch-config/1); required for a"
                         " live round")
    ap.add_argument("--round-label", dest="round_label", default=None,
                    metavar="LABEL",
                    help="watch round label carried on every ledger row"
                         " (default: the run's UTC minute stamp)")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, metavar="JSONL",
                    help="append-only round ledger (default"
                         " docs/claim-watch-ledger.jsonl)")
    ap.add_argument("--actor", default="claim_watch", metavar="NAME",
                    help="actor namespace carried on every ledger row"
                         " (default claim_watch)")
    ap.add_argument("--selftest", "--offline-selftest",
                    dest="offline_selftest", action="store_true",
                    help="run the frozen canned vector group (zero network)"
                         " and exit")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if args.offline_selftest:
        return selftest()
    if not args.config:
        print("FAIL-LOUD: --config is required for a live round (the"
              " offline selftest face is --offline-selftest)",
              file=sys.stderr)
        return 9
    if not os.path.isfile(args.config):
        print("FAIL-LOUD: config file not found: %s" % args.config,
              file=sys.stderr)
        return 9
    try:
        with io.open(args.config, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        print("FAIL-LOUD: config read failed: %s" % exc, file=sys.stderr)
        return 9
    cfg, errors = validate_config(data)
    if errors:
        for err in errors:
            print("SCHEMA-ERROR: %s" % err, file=sys.stderr)
        return 2
    if not args.round_label:
        args.round_label = label_now(utc_now())
    ledger_dir = os.path.dirname(os.path.abspath(args.ledger))
    if not os.path.isdir(ledger_dir):
        print("FAIL-LOUD: ledger directory does not exist: %s" % ledger_dir,
              file=sys.stderr)
        return 9
    return run_round(cfg, args)


if __name__ == "__main__":
    sys.exit(main())
