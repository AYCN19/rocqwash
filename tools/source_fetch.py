#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""source_fetch.py - audit fetch face: pinned, dual-source, trap-sniffing
fetcher for the audit line (rocqwash tools/, v2-B micro-bundle; promoted
from the ad-hoc `attn/_alpoge_rh_audit_20261121/fetch_assets.py` script).

Purpose.  The first leg of every audit: fetch a claim artifact with NETRED
  retry/backoff, verify sha256 where the expected value comes EITHER from
  the caller OR from a CI file fetched at --sha256-source (the
  constant-fetched-from-CI-file-at-source pattern - never hardcoded),
  cross-pin an optional --mirror (both streams must hash-equal), and sniff
  HTML-trap responses under --trap-sniff (the alpo.ge any-path-returns-200
  precedent: TRAP-DETECTED, registered, never silently saved).  Only
  verified bytes reach --out.
Interface.  python -I tools/source_fetch.py --url <u> [--sha256 <expected>]
  [--sha256-source <ci-file-url>] [--mirror <url>] [--trap-sniff]
  [--out <dir>] [--timeout <s>] [--retries <n>] [--backoff-base <sec>]
  | --selftest.  One JSON report line (schema rocqwash-source-fetch/1);
  every counter wrapped {value, basis}; top-level scan_face.
Dependencies.  Python 3 standard library plus the in-tree `_http_backoff`
  (retry + backoff) and `net_probe` (unverifiable classes), imported via
  explicit sys.path injection so `python -I` is clean; the live network
  face is env-gated (ROCQWASH_MCP_ALLOW_NET=1, else rc=111 honest).
Evidence.  --selftest drives canned offline vectors through the injected
  transport (pins, CI-file digests, traps, mirrors, 503x2 schedule, 404,
  dns exhaust, gate rc=111, usage rc=2); precedents fetch_assets.py +
  wave2_fetch.py (CI-constant verification), claim_watch.py (NETRED shape).
Exit-codes.  0 verified (or fetched-unverified, said honestly); 1 red data
  (mismatch/trap/mirror/source/fetch faces - loud, JSON still emitted);
  2 usage; 9 output path unusable; 111 network gated.
"""
# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard):
#   * Precedence of the status token when several faces fire on one run:
#     fetch-failed/unverifiable (primary leg) > trap-detected > source pins >
#     sha-mismatch > mirror-mismatch; the winning token decides the exit
#     code, every other face still rides its report section.
#   * Only fully verified bytes are written to --out (and only when --out is
#     given).  Mismatch, trap, and mirror-mismatch bytes are registered in
#     the report and never land on disk - "registered, not silently saved"
#     binds every red face.
#   * The --sha256-source file is scanned for 64-hex sha256 tokens: exactly
#     one distinct token = the expected digest; more than one distinct token
#     = source-ambiguous (fail loud, the tokens listed); none =
#     source-digest-missing (fail loud).  The tool never carries a constant
#     digest.
#   * The trap sniff is signature-based (Content-Type text/html, an HTML
#     document head, or an "<html" tag inside the first 4KiB); a clean
#     trap_check is a negative finding of that sniff, not byte-level proof -
#     the sha256 pin is the binding evidence.
#   * 401/404 and every non-retry status is a semantic face (no retry, no
#     simulation); 403/429/5xx and the transient transport faces dns/timeout
#     retry per _http_backoff; tls-blocked never retries (policy face).

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
import _http_backoff  # noqa: E402  (retry face + exponential backoff)
import net_probe  # noqa: E402  (classify_unverifiable + reason constants)

PROG = "source_fetch"
SCHEMA = "rocqwash-source-fetch/1"
NET_GATE_ENV = "ROCQWASH_MCP_ALLOW_NET"
GATED_RC = 111
DEFAULT_TIMEOUT = 180
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_BASE = 2.0
SNIFF_WINDOW = 4096
HEX64_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")
USER_AGENT = "rocqwash-source-fetch/1 (audit line)"

# Status tokens (the verdict vocabulary of a run; one wins per run).
FETCHED_VERIFIED = "fetched-verified"
FETCHED_UNVERIFIED = "fetched-unverified"
SHA_MISMATCH = "sha-mismatch"
TRAP_DETECTED = "trap-detected"
MIRROR_MISMATCH = "mirror-mismatch"
SOURCE_AMBIGUOUS = "source-ambiguous"
SOURCE_DIGEST_MISSING = "source-digest-missing"
FETCH_FAILED = "fetch-failed"
UNVERIFIABLE = net_probe.UNVERIFIABLE
NET_GATED = "net-gated"

RED_STATUSES = (SHA_MISMATCH, TRAP_DETECTED, MIRROR_MISMATCH,
                SOURCE_AMBIGUOUS, SOURCE_DIGEST_MISSING,
                FETCH_FAILED, UNVERIFIABLE)


def w(value, basis):
    """Wrap one field as {value, basis}: no bare counter leaves the tool."""
    return {"value": value, "basis": basis}


class CannedResponse(object):
    """Minimal response object for the injected offline transport (the
    selftest's canned-fixture carrier; mirrors the urllib surface used
    here: status, read, headers.get, close)."""

    def __init__(self, status, body, content_type=None):
        self.status = status
        self._body = body
        self.headers = {"Content-Type": content_type} \
            if content_type is not None else {}
        self._closed = False

    def read(self, _n=None):
        body, self._body = self._body, b""
        return body

    def close(self):
        self._closed = True


# ---- transport (canned injection point behind the selftest) -----------------

def _urlopen(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=timeout)


def http_fetch(url, timeout=DEFAULT_TIMEOUT, _open=None):
    """One GET shot -> {status, body, content_type, error, reason_class}.

    status is the HTTP status when an answer arrived (HTTPError included)
    and None for transport failures; reason_class is the net_probe
    unverifiable class (tls-blocked | dns | timeout) of a transport failure
    that says nothing about the target, None otherwise."""
    opener = _open if _open is not None else _urlopen
    try:
        resp = opener(url, timeout=timeout)
        status = getattr(resp, "status", None)
        if status is None and hasattr(resp, "getcode"):
            status = resp.getcode()
        body = resp.read()
        headers = getattr(resp, "headers", None)
        content_type = headers.get("Content-Type") if headers else None
        close = getattr(resp, "close", None)
        if close:
            close()
        return {"status": status, "body": body, "content_type": content_type,
                "error": None, "reason_class": None}
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return {"status": exc.code, "body": body, "content_type": None,
                "error": "%s: %s" % (type(exc).__name__, exc),
                "reason_class": None}
    except Exception as exc:  # noqa: BLE001 - classified, never swallowed
        return {"status": None, "body": b"", "content_type": None,
                "error": "%s: %s" % (type(exc).__name__, exc),
                "reason_class": net_probe.classify_unverifiable(exc)}


def fetch_netred(url, max_retries, base_seconds, timeout=DEFAULT_TIMEOUT,
                 _open=None, _sleep=None):
    """NETRED retry runner (ticket 13 acceptance 5 shape, shared with
    claim_watch).  Retry face = _http_backoff.is_retry_status (403/429/5xx)
    plus the transient transport faces dns and timeout; a tls-block is a
    policy face that never retries; every other status (401/404/...) is a
    semantic face for the caller.  Each retry sleeps the exponential
    schedule's delay first.  Returns the http_fetch result plus
    {attempts, statuses, backoff_applied}."""
    do_sleep = _sleep if _sleep is not None else (lambda _s: None)
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


def sha256_hex(data):
    """Bytes -> the lowercase sha256 hex digest (hashlib, streaming-free:
    bodies are already fully in memory at this point)."""
    return hashlib.sha256(data).hexdigest()


# ---- trap sniff --------------------------------------------------------------

def sniff_html_trap(body, content_type):
    """HTML-trap signatures over one fetched body -> the hits list (empty =
    clean).  Signatures: (1) the Content-Type header marks text/html;
    (2) the body opens (after optional BOM/whitespace) with an HTML
    doctype or <html; (3) an "<html" tag appears inside the first
    SNIFF_WINDOW bytes.  Signature-based, never byte-level proof (the
    scan_face equivalents field says so)."""
    hits = []
    if content_type and "text/html" in str(content_type).lower():
        hits.append("content-type-marks-text-html")
    if body:
        head = body[:SNIFF_WINDOW].lstrip()
        if head.startswith(b"\xef\xbb\xbf"):
            head = head[3:].lstrip()
        low = head.lower()
        if low.startswith(b"<!doctype html") or low.startswith(b"<html"):
            hits.append("html-document-head")
        if b"<html" in body[:SNIFF_WINDOW].lower():
            hits.append("html-tag-in-first-window")
    return hits


def extract_digests(text):
    """Source-file text -> the sorted distinct 64-hex sha256 tokens found
    (the CI-file constant candidates).  Empty list = no digest present."""
    return sorted(set(t.lower() for t in HEX64_RE.findall(text or "")))


# ---- report assembly ---------------------------------------------------------

SCAN_SCANNED = (
    "the fetched primary response body (all bytes), the mirror response"
    " body when --mirror is given, and the --sha256-source file body when"
    " given; single GET per face, no crawl"
)
SCAN_NOT_SCANNED = (
    "anything else on the URL hosts (no directory listing, no linked-URL"
    " follow), response headers beyond Content-Type, and local files:"
    " nothing on disk is read except the report write"
)
SCAN_NEGATIVE_FINDING = (
    "a clean trap_check is a negative finding of this signature sniff, not"
    " an absolute claim; the sha256 pin (caller flag or --sha256-source"
    " CI file) is the binding evidence, the sniff never is"
)
SCAN_EQUIVALENTS = (
    "not exhaustive; the trap sniff is signature-based (Content-Type"
    " text/html, HTML document head, html tag in the first %d bytes) and"
    " the digest extraction scans 64-hex tokens only" % SNIFF_WINDOW
)


def build_report(opts, primary, mirror, source, expected, trap, saved_to,
                 status):
    """Assemble the single JSON report line (schema
    rocqwash-source-fetch/1): every top-level field wrapped {value, basis}
    except scan_face, whose four fields are the coverage statement."""
    def account(face):
        acc = face if isinstance(face, dict) else {}
        return {
            "status": acc.get("status"),
            "content_type": acc.get("content_type"),
            "error": acc.get("error"),
            "reason_class": acc.get("reason_class"),
            "attempts": acc.get("attempts"),
            "statuses": acc.get("statuses"),
            "backoff_applied": acc.get("backoff_applied"),
        }

    primary_sha = sha256_hex(primary["body"]) if primary and primary["body"] is not None else None
    mirror_sha = sha256_hex(mirror["body"]) if mirror and mirror["body"] is not None else None
    source_text = (source["body"].decode("utf-8", errors="replace")
                   if source and source.get("body") is not None else None)
    if opts.get("sha256"):
        sha_source = w({"source": "caller-flag", "url": None,
                        "digest": opts["sha256"].lower()},
                       "expected digest taken verbatim from the caller's"
                       " --sha256 flag; never hardcoded in this tool")
    elif opts.get("sha256_source"):
        sha_source = w({"source": "ci-file", "url": opts["sha256_source"],
                        "digest": expected},
                       "expected digest taken from the single 64-hex token"
                       " found in the file fetched from --sha256-source"
                       " (the constant-fetched-from-CI-file-at-source"
                       " pattern); never hardcoded in this tool")
    else:
        sha_source = w({"source": "none", "url": None, "digest": None},
                       "no expected digest supplied (no --sha256, no"
                       " --sha256-source); the run is honest-unverified"
                       " when a fetch lands")
    report = {
        "schema": SCHEMA,
        "url": w(opts.get("url"),
                 "the primary fetch target as given (--url)"),
        "mirror": w(opts.get("mirror"),
                    "the mirror fetch target as given (--mirror); null ="
                    " no dual-source cross-pin was requested"),
        "bytes": w(len(primary["body"]) if primary and primary["body"] is not None else None,
                   "raw byte count of the primary response body; null ="
                   " the primary leg never produced bytes"),
        "mirror_bytes": w(len(mirror["body"]) if mirror and mirror["body"] is not None else None,
                          "raw byte count of the mirror response body; null"
                          " = no mirror was fetched"),
        "sha256": w(primary_sha,
                    "sha256 hex digest of the primary response body as"
                    " received (hashlib.sha256); null = no bytes"),
        "mirror_sha256": w(mirror_sha,
                           "sha256 hex digest of the mirror response body;"
                           " the cross-pin requires equality with sha256"),
        "expected_sha256": w(expected,
                             "the expected digest in force after the"
                             " sha_source resolution; null = none"),
        "sha_source": sha_source,
        "trap_check": w(trap,
                        "the HTML-trap sniff face: sniff_enabled, and the"
                        " signature hits per fetched body (primary /"
                        " mirror / sha256-source); clean hits lists are a"
                        " negative finding of the sniff, not proof of"
                        " byte-level truth"),
        "fetch_account": w({"primary": account(primary),
                            "mirror": account(mirror) if mirror else None,
                            "source": account(source) if source else None},
                           "per-leg NETRED account: HTTP status,"
                           " classification, attempts, the status trail"
                           " and the backoff delays actually applied"),
        "saved_to": w(saved_to,
                      "path the verified bytes were written to; null ="
                      " nothing reached disk (only fully verified bytes"
                      " are saved, and only with --out)"),
        "status": w(status,
                    "the verdict token of this run: " + ", ".join(
                        (FETCHED_VERIFIED, FETCHED_UNVERIFIED) + RED_STATUSES
                        + (NET_GATED,))
                    + "; red tokens exit 1, fetched-unverified exits 0"
                    " and says so honestly"),
        "scan_face": {
            "scanned": SCAN_SCANNED,
            "not_scanned": SCAN_NOT_SCANNED,
            "negative_finding": SCAN_NEGATIVE_FINDING,
            "equivalents": SCAN_EQUIVALENTS,
        },
    }
    return report


def save_verified(body, out_dir, url):
    """Write verified bytes to out_dir/<url basename>; returns the path.
    The caller only invokes this on a green face (verified or
    honest-unverified fetch, trap clean)."""
    name = os.path.basename(urllib.parse.urlparse(url).path) or "fetched.bin"
    path = os.path.join(out_dir, name)
    with open(path, "wb") as fh:
        fh.write(body)
    return path


def run(opts, _open=None, _sleep=None):
    """The fetch face core.  opts keys: url, sha256, sha256_source, mirror,
    trap_sniff, out, timeout, retries, backoff_base.  Returns
    (report, exit_code).  _open/_sleep are the canned injection points."""
    # 0. the live network face is env-gated (honest rc=111, no simulation)
    if _open is None and os.environ.get(NET_GATE_ENV) != "1":
        report = build_report(opts, None, None, None, None,
                              {"sniff_enabled": bool(opts.get("trap_sniff")),
                               "primary_hits": None, "mirror_hits": None,
                               "source_hits": None},
                              None, NET_GATED)
        return report, GATED_RC

    timeout = opts.get("timeout", DEFAULT_TIMEOUT)
    retries = opts.get("retries", DEFAULT_RETRIES)
    base = opts.get("backoff_base", DEFAULT_BACKOFF_BASE)
    trap_enabled = bool(opts.get("trap_sniff"))

    def sniff(face):
        return sniff_html_trap(face["body"], face.get("content_type")) \
            if trap_enabled else None

    # 1. resolve the expected digest (caller flag wins; else the CI file)
    expected = None
    source_face = None
    src_sniff = None
    if not opts.get("sha256") and opts.get("sha256_source"):
        source_face = fetch_netred(opts["sha256_source"], retries, base,
                                   timeout=timeout, _open=_open, _sleep=_sleep)
        src_sniff = sniff(source_face)
        if source_face["status"] != 200:
            # a source file that did not answer 200 is a fetch failure of
            # the pin leg; keep its account and fail loud
            if source_face["status"] is None and source_face["reason_class"]:
                status = UNVERIFIABLE
            else:
                status = FETCH_FAILED
            report = build_report(opts, None, None, source_face, None,
                                  {"sniff_enabled": trap_enabled,
                                   "primary_hits": None, "mirror_hits": None,
                                   "source_hits": src_sniff},
                                  None, status)
            return report, 1
        digests = extract_digests(
            source_face["body"].decode("utf-8", errors="replace"))
        if not digests:
            report = build_report(opts, None, None, source_face, None,
                                  {"sniff_enabled": trap_enabled,
                                   "primary_hits": None, "mirror_hits": None,
                                   "source_hits": src_sniff},
                                  None, SOURCE_DIGEST_MISSING)
            return report, 1
        if len(digests) > 1:
            report = build_report(opts, None, None, source_face, None,
                                  {"sniff_enabled": trap_enabled,
                                   "primary_hits": None, "mirror_hits": None,
                                   "source_hits": src_sniff},
                                  None, SOURCE_AMBIGUOUS)
            return report, 1
        expected = digests[0]

    if opts.get("sha256"):
        expected = opts["sha256"].lower()

    # 2. the primary leg
    primary = fetch_netred(opts["url"], retries, base, timeout=timeout,
                           _open=_open, _sleep=_sleep)
    primary_hits = sniff(primary)
    if primary["status"] != 200:
        if primary["status"] is None and primary["reason_class"]:
            status = UNVERIFIABLE
        else:
            status = FETCH_FAILED
        report = build_report(opts, primary, None, source_face, expected,
                              {"sniff_enabled": trap_enabled,
                               "primary_hits": primary_hits,
                               "mirror_hits": None, "source_hits": None},
                              None, status)
        return report, 1

    primary_sha = sha256_hex(primary["body"])
    status = None
    saved_to = None

    # 3. trap face (registered, never silently saved past)
    if trap_enabled and primary_hits:
        status = TRAP_DETECTED

    # 4. the mirror cross-pin face (both streams must hash-equal)
    mirror_face = None
    mirror_hits = None
    if opts.get("mirror"):
        mirror_face = fetch_netred(opts["mirror"], retries, base,
                                   timeout=timeout, _open=_open,
                                   _sleep=_sleep)
        mirror_hits = sniff(mirror_face)
        if not status and mirror_face["status"] != 200:
            status = MIRROR_MISMATCH
        elif not status and mirror_hits:
            status = TRAP_DETECTED
        elif not status and sha256_hex(mirror_face["body"]) != primary_sha:
            status = MIRROR_MISMATCH

    # 5. the sha256 pin face
    if not status and expected is not None and primary_sha != expected:
        status = SHA_MISMATCH

    # 6. the save face (only green bytes; trap/mismatch never reach disk)
    if status is None:
        status = FETCHED_VERIFIED if expected is not None \
            else FETCHED_UNVERIFIED
        if opts.get("out"):
            out_dir = opts["out"]
            os.makedirs(out_dir, exist_ok=True)
            saved_to = save_verified(primary["body"], out_dir, opts["url"])

    trap = {"sniff_enabled": trap_enabled,
            "primary_hits": primary_hits,
            "mirror_hits": mirror_hits,
            "source_hits": src_sniff}
    report = build_report(opts, primary, mirror_face, source_face, expected,
                          trap, saved_to, status)
    return report, (1 if status in RED_STATUSES else 0)


# ---- selftest ----------------------------------------------------------------

def subprocess_run(argv, env=None):
    """Run one child (the suite convention: merged stdout/stderr, decoded
    leniently).  argv already carries the interpreter flags."""
    import subprocess
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=env)
    p.stdout = p.stdout.decode("utf-8", errors="replace") \
        if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p


def selftest():
    """Offline canned-fixture vector set: the transport is injected (zero
    network), the schedule sleeps are stubbed (zero wall clock), and the
    digests are computed from the canned bodies at run time (the tool never
    carries a constant)."""
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="source_fetch_self_")
    fails = []

    def check(name, ok, detail=""):
        if ok:
            print("[PASS] %s" % name)
        else:
            fails.append(name)
            print("[FAIL] %s %s" % (name, detail))

    def sh(data):
        return hashlib.sha256(data).hexdigest()

    # canned fixture world (digests computed at run time, never constants)
    body_a = b"rocqwash canned fixture alpha payload\n" * 8
    body_b = b"rocqwash canned fixture beta payload differs\n" * 8
    trap_body = (b"<!DOCTYPE html><html><head><title>trap</title></head>"
                 b"<body>any path returns 200</body></html>\n")
    ci_text = "# checks.yml canned fixture\njoined_archive_sha256: %s\n" \
              % sh(body_a)
    ci_ambiguous = ("a: %s\nb: %s\n" % (sh(body_a), sh(body_b)))
    ci_empty = "# no digest lives here\n"

    urls = {
        "u://fixture/alpha.bin": (200, body_a, "application/octet-stream"),
        "u://fixture/beta.bin": (200, body_b, "application/octet-stream"),
        "u://fixture/trap.bin": (200, trap_body, "application/octet-stream"),
        "u://fixture/trap-ct.bin": (200, trap_body, "text/html"),
        "u://fixture/notfound.bin": (404, b"gone", None),
        "u://fixture/ci.yml": (200, ci_text.encode("utf-8"), "text/plain"),
        "u://fixture/ci-ambiguous.yml": (200, ci_ambiguous.encode("utf-8"), "text/plain"),
        "u://fixture/ci-empty.yml": (200, ci_empty.encode("utf-8"), "text/plain"),
    }

    def canned_open_factory(responses, fail_first=None):
        """Build an injected opener: per-URL canned answers, optional
        fail_first = [(url, kind)...] consumed in order before the canned
        answer answers (kind '503' or 'dns')."""
        state = {"i": 0}

        def opener(url, timeout=None):
            if fail_first and state["i"] < len(fail_first):
                furl, kind = fail_first[state["i"]]
                state["i"] += 1
                if kind == "503":
                    return CannedResponse(503, b"try again", None)
                raise urllib.error.URLError(
                    OSError(-2, "Name or service not known"))
            if url not in responses:
                raise urllib.error.URLError("canned miss %s" % url)
            status, body, ctype = responses[url]
            return CannedResponse(status, body, ctype)
        return opener

    slept = []

    def base_opts(**kw):
        opts = {"url": "u://fixture/alpha.bin", "timeout": 5,
                "retries": 3, "backoff_base": 2.0}
        opts.update(kw)
        return opts

    try:
        # 1. caller-pin verified + saved: rc 0, bytes land on disk intact,
        #    the shape contract holds (every counter wrapped; scan_face four)
        out1 = os.path.join(tmp, "out1")
        rep, rc = run(base_opts(sha256=sh(body_a), out=out1),
                      _open=canned_open_factory(urls), _sleep=slept.append)
        check("caller-pin rc0", rc == 0, "rc=%s" % rc)
        check("caller-pin status",
              rep["status"]["value"] == FETCHED_VERIFIED, rep["status"])
        check("caller-pin bytes",
              rep["bytes"]["value"] == len(body_a), rep["bytes"])
        check("caller-pin sha",
              rep["sha256"]["value"] == sh(body_a), rep["sha256"])
        check("caller-pin source-flag",
              rep["sha_source"]["value"]["source"] == "caller-flag",
              rep["sha_source"])
        saved = os.path.join(out1, "alpha.bin")
        check("caller-pin saved", os.path.isfile(saved), saved)
        with open(saved, "rb") as fh:
            check("caller-pin saved-bytes", fh.read() == body_a)
        bare = [k for k in rep if k not in ("scan_face", "schema")
                and not (isinstance(rep[k], dict)
                         and "value" in rep[k] and "basis" in rep[k])]
        check("value-basis-shape", bare == [], "bare keys: %s" % bare)
        face = rep["scan_face"]
        check("scan-face-fields",
              sorted(face) == ["equivalents", "negative_finding",
                               "not_scanned", "scanned"], sorted(face))
        check("scan-face-sniff-window",
              ("first %d bytes" % SNIFF_WINDOW) in face["equivalents"],
              face["equivalents"])

        # 2. caller-pin mismatch: rc 1 sha-mismatch, nothing saved
        rep, rc = run(base_opts(sha256=sh(body_b)),
                      _open=canned_open_factory(urls), _sleep=slept.append)
        check("mismatch rc1", rc == 1 and rep["status"]["value"] == SHA_MISMATCH,
              (rc, rep["status"]))
        check("mismatch not-saved", rep["saved_to"]["value"] is None,
              rep["saved_to"])

        # 3. CI-file pin verified: the expected digest is taken from the
        #    fetched source file (the constant never lives in the tool)
        rep, rc = run(base_opts(sha256_source="u://fixture/ci.yml"),
                      _open=canned_open_factory(urls), _sleep=slept.append)
        check("ci-pin rc0", rc == 0 and rep["status"]["value"] == FETCHED_VERIFIED,
              (rc, rep["status"]))
        check("ci-pin sha_source",
              rep["sha_source"]["value"]["source"] == "ci-file"
              and rep["sha_source"]["value"]["digest"] == sh(body_a)
              and rep["sha_source"]["value"]["url"] == "u://fixture/ci.yml",
              rep["sha_source"])
        check("ci-pin expected",
              rep["expected_sha256"]["value"] == sh(body_a),
              rep["expected_sha256"])

        # 4. CI-file ambiguous (two distinct 64-hex tokens): rc 1 loud
        rep, rc = run(base_opts(sha256_source="u://fixture/ci-ambiguous.yml"),
                      _open=canned_open_factory(urls), _sleep=slept.append)
        check("ci-ambiguous rc1",
              rc == 1 and rep["status"]["value"] == SOURCE_AMBIGUOUS,
              (rc, rep["status"]))

        # 5. CI-file without any digest: rc 1 source-digest-missing
        rep, rc = run(base_opts(sha256_source="u://fixture/ci-empty.yml"),
                      _open=canned_open_factory(urls), _sleep=slept.append)
        check("ci-missing rc1",
              rc == 1 and rep["status"]["value"] == SOURCE_DIGEST_MISSING,
              (rc, rep["status"]))

        # 6. trap sniff: an HTML body where a binary was expected is
        #    TRAP-DETECTED, registered, and never saved; with the sniff off
        #    the same body passes through honestly un-sniffed
        rep, rc = run(base_opts(url="u://fixture/trap.bin",
                                sha256=sh(trap_body), trap_sniff=True),
                      _open=canned_open_factory(urls), _sleep=slept.append)
        check("trap rc1", rc == 1 and rep["status"]["value"] == TRAP_DETECTED,
              (rc, rep["status"]))
        check("trap hits",
              rep["trap_check"]["value"]["primary_hits"]
              == ["html-document-head", "html-tag-in-first-window"],
              rep["trap_check"])
        check("trap not-saved", rep["saved_to"]["value"] is None)
        rep, rc = run(base_opts(url="u://fixture/trap.bin",
                                sha256=sh(trap_body), trap_sniff=False),
                      _open=canned_open_factory(urls), _sleep=slept.append)
        check("trap-off honest",
              rc == 0 and rep["trap_check"]["value"]["sniff_enabled"] is False
              and rep["trap_check"]["value"]["primary_hits"] is None,
              (rc, rep["trap_check"]))
        rep, rc = run(base_opts(url="u://fixture/trap-ct.bin",
                                sha256=sh(trap_body), trap_sniff=True),
                      _open=canned_open_factory(urls), _sleep=slept.append)
        check("trap-content-type hit",
              rc == 1 and "content-type-marks-text-html"
              in rep["trap_check"]["value"]["primary_hits"],
              rep["trap_check"])

        # 7. mirror cross-pin: hash-equal mirror verifies, differing mirror
        #    is a mirror-mismatch red, nothing saved either way
        rep, rc = run(base_opts(mirror="u://fixture/alpha.bin",
                                sha256=sh(body_a)),
                      _open=canned_open_factory(urls), _sleep=slept.append)
        check("mirror-match rc0",
              rc == 0 and rep["mirror_sha256"]["value"] == sh(body_a),
              (rc, rep["mirror_sha256"]))
        rep, rc = run(base_opts(mirror="u://fixture/beta.bin",
                                sha256=sh(body_a)),
                      _open=canned_open_factory(urls), _sleep=slept.append)
        check("mirror-mismatch rc1",
              rc == 1 and rep["status"]["value"] == MIRROR_MISMATCH
              and rep["saved_to"]["value"] is None,
              (rc, rep["status"]))

        # 8. NETRED discipline: 503,503 then green retried on schedule
        #    (base 2 -> 2s,4s actually applied, attempts=3); 404 never
        #    retries; a dns transport failure exhausts into unverifiable
        opener = canned_open_factory(urls, fail_first=[("x", "503"), ("x", "503")])
        slept.clear()
        rep, rc = run(base_opts(sha256=sh(body_a), retries=3,
                                backoff_base=2.0),
                      _open=opener, _sleep=slept.append)
        check("retry-503 rc0", rc == 0, (rc, rep["status"]))
        check("retry-503 account",
              rep["fetch_account"]["value"]["primary"]["attempts"] == 3
              and rep["fetch_account"]["value"]["primary"]["statuses"]
              == [503, 503, 200]
              and rep["fetch_account"]["value"]["primary"]["backoff_applied"]
              == [2.0, 4.0],
              rep["fetch_account"])
        check("retry-sleeps-stubbed", slept == [2.0, 4.0], slept)
        rep, rc = run(base_opts(url="u://fixture/notfound.bin"),
                      _open=canned_open_factory(urls), _sleep=slept.append)
        check("no-retry-404",
              rc == 1 and rep["status"]["value"] == FETCH_FAILED
              and rep["fetch_account"]["value"]["primary"]["attempts"] == 1,
              (rc, rep["fetch_account"]))
        opener = canned_open_factory(urls, fail_first=[("x", "dns")] * 4)
        rep, rc = run(base_opts(retries=3),
                      _open=opener, _sleep=slept.append)
        check("dns-exhaust-unverifiable",
              rc == 1 and rep["status"]["value"] == UNVERIFIABLE
              and rep["fetch_account"]["value"]["primary"]["reason_class"]
              == "dns",
              (rc, rep["fetch_account"]))

        # 9. honest-unverified: a fetch with no pin at all lands rc 0 but
        #    says fetched-unverified (no simulated certainty)
        rep, rc = run(base_opts(), _open=canned_open_factory(urls),
                      _sleep=slept.append)
        check("unverified-honest",
              rc == 0 and rep["status"]["value"] == FETCHED_UNVERIFIED
              and rep["expected_sha256"]["value"] is None,
              (rc, rep["status"]))

        # 10. CLI faces: net gate rc=111 (env-gated, reported not
        #     simulated); usage rc=2 without --url
        script = os.path.join(_TOOLS_DIR, PROG + ".py")
        env = dict(os.environ)
        env.pop(NET_GATE_ENV, None)
        p = subprocess_run([sys.executable, "-I", "-B", script,
                            "--url", "https://example.invalid/x.bin"], env=env)
        check("gate rc111", p.returncode == GATED_RC,
              "rc=%s out=%s" % (p.returncode, p.stdout[:200]))
        check("gate honest-json", '"net-gated"' in p.stdout
              and "ROCQWASH_MCP_ALLOW_NET" in p.stdout, p.stdout[:300])
        p = subprocess_run([sys.executable, "-I", "-B", script,
                            "--sha256", "deadbeef"], env=env)
        check("usage rc2", p.returncode == 2, "rc=%s" % p.returncode)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("[SELFTEST] source_fetch red: %d vector(s) failed: %s"
              % (len(fails), ", ".join(fails)))
        return 1
    print("[SELFTEST] source_fetch green: caller-pin verify+mismatch/"
          "ci-file pin single+ambiguous+missing/trap sniff on+off+content-type/"
          "mirror cross-pin match+mismatch/503x2 retry schedule/404 no-retry/"
          "dns exhaust unverifiable/honest-unverified/net-gate rc111/"
          "usage rc2 - all vectors pass offline")
    return 0


def main(argv=None):
    """CLI entry; returns the process exit code."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="audit fetch face: NETRED fetch, sha256 pin from the"
                    " caller or a CI file at source, mirror cross-pin,"
                    " HTML-trap sniff; one JSON report line")
    ap.add_argument("--url", default=None, metavar="URL",
                    help="primary fetch target (required)")
    ap.add_argument("--sha256", default=None, metavar="HEX64",
                    help="expected sha256 from the caller (lowercase hex;"
                         " never a tool constant)")
    ap.add_argument("--sha256-source", default=None, metavar="URL",
                    help="URL of the CI file carrying the expected sha256"
                         " as its single 64-hex token (the"
                         " constant-fetched-from-CI-file-at-source"
                         " pattern)")
    ap.add_argument("--mirror", default=None, metavar="URL",
                    help="mirror fetch target; both byte streams must"
                         " hash-equal (dual-source cross-pin)")
    ap.add_argument("--trap-sniff", action="store_true",
                    help="sniff fetched bodies for HTML-trap responses"
                         " (any-path-returns-200 precedent); a hit is"
                         " TRAP-DETECTED and never saved")
    ap.add_argument("--out", default=None, metavar="DIR",
                    help="directory the verified bytes are written to"
                         " (created if missing; only green bytes land)")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    metavar="SEC", help="per-attempt timeout seconds"
                    " (default %s)" % DEFAULT_TIMEOUT)
    ap.add_argument("--retries", type=int, default=DEFAULT_RETRIES,
                    metavar="N", help="NETRED retry cap (default %s)"
                    % DEFAULT_RETRIES)
    ap.add_argument("--backoff-base", type=float, default=DEFAULT_BACKOFF_BASE,
                    metavar="SEC", help="exponential backoff base seconds"
                    " (default %s)" % DEFAULT_BACKOFF_BASE)
    args = ap.parse_args(argv)

    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not args.url:
        print("FAIL-LOUD: --url is required (nothing to fetch; the --out"
              " face also refuses to invent a target)", file=sys.stderr)
        return 2
    if args.sha256 and args.sha256_source:
        print("FAIL-LOUD: give the expected sha256 from one authority"
              " only: --sha256 (caller) or --sha256-source (CI file),"
              " never both", file=sys.stderr)
        return 2
    if args.sha256 is not None and not HEX64_RE.fullmatch(args.sha256.strip()):
        print("FAIL-LOUD: --sha256 must be a 64-hex digest, got %r"
              % args.sha256, file=sys.stderr)
        return 2

    opts = {"url": args.url, "sha256": args.sha256,
            "sha256_source": args.sha256_source, "mirror": args.mirror,
            "trap_sniff": args.trap_sniff, "out": args.out,
            "timeout": args.timeout, "retries": args.retries,
            "backoff_base": args.backoff_base}
    report, rc = run(opts)
    payload = json.dumps(report, ensure_ascii=False)
    print(payload)
    if rc == GATED_RC:
        print("FAIL-LOUD: the live network face is gated: set"
              " %s=1 to fetch %s (reported, not simulated)"
              % (NET_GATE_ENV, args.url), file=sys.stderr)
    elif rc == 1:
        print("FAIL-LOUD: verification red as data: status=%s (the JSON"
              " line above carries the full account; no bytes reached"
              " disk)" % report["status"]["value"], file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
