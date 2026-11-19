#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_http_backoff.py — shared HTTP rate-limit backoff helper for the three
retrying tools (rocqwash tools/, v37 resilience layer).

Purpose.  The retry-status judgment, the exponential-backoff delay table and
  the Retry-After header parser live here once and are imported by
  `tools/ci_triage.py`, `tools/pushci.py` and `tools/cw_sentinel.py`, so the
  three inline copies cannot drift again.  Pure functions only: zero IO, zero
  wall clock, zero randomness; identical arguments give identical results;
  --selftest pins the frozen vectors.
Interface.  Module import, not a CLI (tools/ is a flat directory with no
  __init__ package, so each importer injects its own directory into sys.path
  first): is_retry_status(code) judges the 403/429/5xx retry face (every
  other status, including the 401/404/409 semantic faces, is the caller's
  judgment, not a retry); backoff_delays(retry_max, base=2.0) maps a retry
  cap n to the exponential delay-seconds table [base*2^0, base*2^1, ...] of
  length exactly n (n=3, base=2 -> [2, 4, 8]; n=0 -> []; negative n or
  non-int -> ValueError); parse_retry_after(val) maps an RFC 7231
  delay-seconds form to a float >= 0 and returns None for None/empty/
  non-numeric/negative/HTTP-date forms (an HTTP-date needs wall-clock
  conversion and is not guessed, so the caller falls back to the exponential
  delay).
Dependencies.  Python 3 standard library only.
Evidence.  python3 tools/_http_backoff.py --selftest runs the frozen vectors
  offline (zero network, zero IO); the importers' selftests assert the same
  frozen vectors (`tools/ci_triage.py`, `tools/pushci.py`,
  `tools/cw_sentinel.py`).
Exit-codes.  0 = --selftest vectors all pass; 2 = invoked without --selftest.
"""
# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard): the retry runner
# convention is owned by each looping tool; this module only judges statuses
# and computes delays.  Per attempt: a retry-face status with retries left
# sleeps parse_retry_after(header) seconds or backoff_delays(retry_max)
# [attempt], then resends; exhausted retries re-raise the original error
# unchanged (fail-loud policy per tool: ci_triage 9, pushci hands the
# (code, body) pair to semantic judgment, cw_sentinel 9).  Injector canned
# paths never retry: a canned response is a deterministic offline test face.
import sys

PROG = "_http_backoff"

DEFAULT_BASE = 2.0            # exponential backoff base seconds (base 2s set by the issuing task instruction)
RETRY_STATUSES = frozenset((403, 429))


def is_retry_status(code):
    """Response status -> whether it is in the retry face (403/429/5xx).
    Non-int/None -> False."""
    if not isinstance(code, int) or isinstance(code, bool):
        return False
    return code in RETRY_STATUSES or (500 <= code <= 599)


def backoff_delays(retry_max, base=DEFAULT_BASE):
    """Retry cap n -> exponential delay-seconds table (length n; retry i
    sleeps base*2^i before it fires).
    Precedent: retry_max=3, base=2 -> [2.0, 4.0, 8.0] (the issuing task's
    403x3 -> [2, 4, 8]).
    n=0 -> []; negative n / non-int -> ValueError (fail-loud)."""
    if not isinstance(retry_max, int) or isinstance(retry_max, bool) \
            or retry_max < 0:
        raise ValueError("retry_max must be a non-negative int, got %r"
                         % (retry_max,))
    return [float(base) * (2 ** i) for i in range(retry_max)]


def parse_retry_after(value):
    """Retry-After delay-seconds form -> float >= 0; None/empty/non-numeric/
    negative/HTTP-date forms -> None (the caller falls back to the
    exponential delay).  Pure string parsing, zero wall clock."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    if f < 0:
        return None
    return f


def selftest():
    """Frozen vector set (pure functions, zero network, zero IO): backoff
    sequence precedent 403x3 -> [2, 4, 8] / caps 0, 1, negative, non-int
    fail loud / retry-face positive-negative judgment for 403, 429, 5xx /
    Retry-After seconds honored, HTTP-date not guessed and falling back to
    the exponential delay."""
    assert backoff_delays(3) == [2.0, 4.0, 8.0], backoff_delays(3)
    assert backoff_delays(0) == []
    assert backoff_delays(1) == [2.0]
    assert backoff_delays(2, base=1.0) == [1.0, 2.0]
    for bad in (-1, "3", 1.5, None, True):
        try:
            backoff_delays(bad)
            assert False, "retry_max=%r must raise ValueError" % (bad,)
        except ValueError:
            pass
    assert is_retry_status(403) and is_retry_status(429)
    for c in (500, 502, 503, 504, 599):
        assert is_retry_status(c), c
    for c in (200, 201, 301, 400, 401, 404, 409, 422, 499, 600, None, "503"):
        assert not is_retry_status(c), c
    assert parse_retry_after("60") == 60.0
    assert parse_retry_after(" 15 ") == 15.0
    assert parse_retry_after("0") == 0.0
    for bad in (None, "", "-5", "abc",
                "Wed, 21 Oct 2026 07:28:00 GMT"):
        assert parse_retry_after(bad) is None, bad
    print("_HTTP-BACKOFF-SELFTEST PASS: backoff sequence 403x3 -> [2,4,8] / "
          "caps 0, 1, negative, non-int fail loud / retry face 403, 429, 5xx "
          "positive-negative judged / Retry-After seconds honored, HTTP-date "
          "not guessed, falls back to exponential: all pass")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    print("FAIL-LOUD: --selftest is required (shared library, no CLI face)",
          file=sys.stderr)
    sys.exit(2)
