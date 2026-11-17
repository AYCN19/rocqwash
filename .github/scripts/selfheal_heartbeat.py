#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selfheal_heartbeat.py - append-only heartbeat ledger writer (JSONL).

    Purpose.  Append one tick line (UTC timestamp + status) to a JSONL heartbeat
    file; existing lines are never rewritten or truncated; a gap strictly over
    the alert threshold (default 90 minutes = three missed ticks of the */30
    schedule) appends an ALERT line ahead of the tick.  Read-only by default
    (the write happens only under `--apply`).

    Interface.  `python3 .github/scripts/selfheal_heartbeat.py --file
    docs/heartbeat.jsonl --apply [--status ok] [--alert-minutes 90]
    [--source workflow_dispatch] [--now <iso8601>] [--selftest]`; called by the
    `workflow_dispatch` heartbeat step of `.github/workflows/selfheal.yml`;
    `--now` feeds offline vectors only, CI never passes it.

    Dependencies.  Python 3 stdlib only (argparse, datetime, io, json, os,
    shutil, sys, tempfile); zero third-party imports; no network; the only
    write face is the caller-named `--file` (plus temp dirs under `--selftest`).

    Evidence.  `--selftest` asserts in a private temp dir: default zero-write,
    append-only byte stability, line schema, alert on both sides of the
    threshold boundary, and fail-loud refusal on a corrupt ledger; matrix
    rows H1/H2/H3/H4 in `tests/test_destructive_matrix.py` pin the same.

    Exit-codes.  0 = tick appended under `--apply` (ALERT line included when
    due), planned lines printed read-only, or selftest passed; 2 = usage error
    (missing `--file`, bad `--now`/`--alert-minutes`); 9 = fail-loud on a
    corrupt ledger with zero bytes written.
"""
import argparse
import io
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone

SCHEMA = "rocqwash.heartbeat/1"
KIND_TICK = "tick"
KIND_ALERT = "alert"
DEFAULT_ALERT_MINUTES = 90.0
DEFAULT_STATUS = "ok"
DEFAULT_SOURCE = "workflow_dispatch"


class UsageError(Exception):
    """Bad CLI input; maps to exit 2."""


class FailLoud(Exception):
    """Corrupt or unreadable input data; maps to exit 9 with zero writes."""


def parse_iso(text, what):
    """Parse an ISO 8601 timestamp; naive input is read as UTC.  The trailing
    `Z` suffix is normalized to `+00:00` because `datetime.fromisoformat`
    rejects it before Python 3.11."""
    t = text.strip()
    if t.endswith(("Z", "z")):
        t = t[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(t)
    except ValueError:
        raise UsageError("bad %s timestamp (want ISO 8601): %r" % (what, text))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def fmt_iso(dt):
    """Canonical ledger timestamp form: second precision, UTC, `Z` suffix."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def last_tick(path):
    """Return the most recent tick datetime in the ledger, or None.

    Scans backwards from the last non-empty line and stops at the first
    tick record; `alert` records above it are annotations, never tick
    sources.  A line that is neither blank nor a schema-valid JSON object
    raises FailLoud: appending behind a corrupt line would silently grow
    an unreadable ledger, so nothing is written on that path.
    """
    if not os.path.exists(path):
        return None
    with io.open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            raise FailLoud("heartbeat line is not valid JSON: %r" % line[:120])
        if not isinstance(rec, dict) or rec.get("schema") != SCHEMA:
            raise FailLoud("heartbeat line schema mismatch: %r" % line[:120])
        if rec.get("kind") == KIND_TICK:
            try:
                return parse_iso(rec["tick"], "ledger tick")
            except UsageError as exc:
                raise FailLoud(str(exc))
    return None


def planned_records(now, prev, status, source, alert_minutes):
    """Return the records to append this run: an ALERT line first when the
    gap since the previous tick is strictly over `alert_minutes`, then the
    tick line.  A negative gap (clock skew or an out-of-order `--now`) is
    not an alert: only silence past the threshold is loss of contact."""
    tick = {
        "schema": SCHEMA,
        "kind": KIND_TICK,
        "tick": fmt_iso(now),
        "status": status,
        "source": source,
    }
    if prev is None:
        return [tick]
    gap_minutes = (now - prev).total_seconds() / 60.0
    if gap_minutes > alert_minutes:
        alert = {
            "schema": SCHEMA,
            "kind": KIND_ALERT,
            "tick": fmt_iso(now),
            "since": fmt_iso(prev),
            "gap_minutes": round(gap_minutes, 6),
            "threshold_minutes": alert_minutes,
            "status": "loss-of-contact",
        }
        return [alert, tick]
    return [tick]


def append_records(path, records):
    """The one write face: append mode, one pass, never a truncate and never
    a rewrite of existing bytes."""
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "a", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")


def run(args):
    """One heartbeat pass: read the ledger, plan the lines, print them, and
    append only under `--apply` (the single write gate)."""
    if not args.file:
        raise UsageError("--file is required (the heartbeat ledger path)")
    if args.alert_minutes <= 0:
        raise UsageError("--alert-minutes must be positive")
    if args.now:
        now = parse_iso(args.now, "--now")
    else:
        now = datetime.now(timezone.utc).replace(microsecond=0)
    records = planned_records(now, last_tick(args.file), args.status,
                              args.source, args.alert_minutes)
    for rec in records:
        sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")
    if args.apply:
        append_records(args.file, records)
    return 0


def selftest():
    """Offline vectors in a private temp dir; one PASS/FAIL line per vector,
    exit 0 only when every vector holds (fail-loud, never a simulated pass)."""
    root = tempfile.mkdtemp(prefix="selfheal_heartbeat_selftest_")
    results = []

    def ns(f, now=None, apply=False, status=DEFAULT_STATUS,
           alert_minutes=DEFAULT_ALERT_MINUTES):
        return argparse.Namespace(file=f, apply=apply, status=status,
                                  source=DEFAULT_SOURCE,
                                  alert_minutes=alert_minutes, now=now,
                                  selftest=False)

    def read_bytes(p):
        with io.open(p, "rb") as fh:
            return fh.read()

    def parse(p):
        return [json.loads(x)
                for x in read_bytes(p).decode("utf-8").splitlines()]

    def check(name, fn):
        try:
            fn()
            results.append((name, True, ""))
        except Exception as exc:
            results.append((name, False, repr(exc)))

    def v_dry_run_zero_write():
        f = os.path.join(root, "dry.jsonl")
        rc = run(ns(f, now="2026-01-01T00:00:00Z"))
        assert rc == 0
        assert not os.path.exists(f), "read-only run must not create the ledger"

    def v_append_only_stability():
        f = os.path.join(root, "append.jsonl")
        run(ns(f, now="2026-01-01T00:00:00Z", apply=True))
        b1 = read_bytes(f)
        recs = parse(f)
        assert len(recs) == 1, "one apply run must append exactly one line"
        assert recs[0]["schema"] == SCHEMA and recs[0]["kind"] == KIND_TICK \
            and recs[0]["tick"] == "2026-01-01T00:00:00Z" \
            and recs[0]["status"] == DEFAULT_STATUS, recs
        run(ns(f, now="2026-01-01T00:10:00Z", apply=True))
        b2 = read_bytes(f)
        assert b2.startswith(b1), "prior ledger bytes must stay byte-identical"
        recs = parse(f)
        assert len(recs) == 2 and all(r["kind"] == KIND_TICK for r in recs)

    def v_alert_boundary():
        f = os.path.join(root, "at.jsonl")
        run(ns(f, now="2026-01-01T00:00:00Z", apply=True))
        run(ns(f, now="2026-01-01T01:30:00Z", apply=True))
        recs = parse(f)
        assert len(recs) == 2 and all(r["kind"] == KIND_TICK for r in recs), \
            "a gap of exactly 90 minutes must stay silent: %s" % recs
        g = os.path.join(root, "past.jsonl")
        run(ns(g, now="2026-01-01T00:00:00Z", apply=True))
        run(ns(g, now="2026-01-01T01:30:01Z", apply=True))
        recs = parse(g)
        assert len(recs) == 3, recs
        assert recs[1]["kind"] == KIND_ALERT and recs[2]["kind"] == KIND_TICK, \
            "the ALERT line must land ahead of the tick: %s" % recs
        assert recs[1]["since"] == "2026-01-01T00:00:00Z" \
            and recs[1]["gap_minutes"] > 90 \
            and recs[1]["status"] == "loss-of-contact" \
            and recs[1]["threshold_minutes"] == 90, recs[1]

    def v_alert_not_a_tick_source():
        f = os.path.join(root, "src.jsonl")
        run(ns(f, now="2026-01-01T00:00:00Z", apply=True))
        run(ns(f, now="2026-01-01T02:00:00Z", apply=True))
        run(ns(f, now="2026-01-01T02:29:00Z", apply=True))
        recs = parse(f)
        alerts = [r for r in recs if r["kind"] == KIND_ALERT]
        assert len(alerts) == 1, "alert must not become a tick source: %s" % recs

    def v_fail_loud_corrupt():
        f = os.path.join(root, "corrupt.jsonl")
        run(ns(f, now="2026-01-01T00:00:00Z", apply=True))
        with io.open(f, "a", encoding="utf-8") as fh:
            fh.write("not-json\n")
        before = read_bytes(f)
        try:
            run(ns(f, now="2026-01-01T01:00:00Z", apply=True))
            raise AssertionError("corrupt ledger must fail loud, not append")
        except FailLoud:
            pass
        assert read_bytes(f) == before, "refused run must write zero bytes"
        g = os.path.join(root, "wrongschema.jsonl")
        with io.open(g, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"schema": "other/1", "kind": KIND_TICK}) + "\n")
        before = read_bytes(g)
        try:
            run(ns(g, now="2026-01-01T01:00:00Z", apply=True))
            raise AssertionError("schema mismatch must fail loud, not append")
        except FailLoud:
            pass
        assert read_bytes(g) == before

    def v_usage_errors():
        f = os.path.join(root, "u1.jsonl")
        try:
            run(ns(f, now="not-a-date", apply=True))
            raise AssertionError("bad --now must raise UsageError")
        except UsageError:
            pass
        assert not os.path.exists(f)
        f = os.path.join(root, "u2.jsonl")
        try:
            run(ns(f, alert_minutes=0, apply=True))
            raise AssertionError("nonpositive --alert-minutes must raise UsageError")
        except UsageError:
            pass
        assert not os.path.exists(f)
        try:
            run(ns(""))
            raise AssertionError("empty --file must raise UsageError")
        except UsageError:
            pass

    try:
        for name, fn in (("dry-run-zero-write", v_dry_run_zero_write),
                         ("append-only-stability", v_append_only_stability),
                         ("alert-boundary", v_alert_boundary),
                         ("alert-not-a-tick-source", v_alert_not_a_tick_source),
                         ("fail-loud-corrupt", v_fail_loud_corrupt),
                         ("usage-errors", v_usage_errors)):
            check(name, fn)
        for name, ok, detail in results:
            sys.stdout.write("%s %s%s\n" % ("PASS" if ok else "FAIL", name,
                                            "" if ok else ": " + detail))
        if all(ok for _, ok, _ in results):
            sys.stdout.write("SELHEARTBEAT SELFTEST PASS: 6 vectors\n")
            return 0
        return 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main(argv=None):
    p = argparse.ArgumentParser(
        description="append-only heartbeat tick ledger writer")
    p.add_argument("--file", default=None,
                   help="heartbeat ledger path (append-only JSONL)")
    p.add_argument("--apply", action="store_true",
                   help="perform the append (default: read-only plan)")
    p.add_argument("--status", default=DEFAULT_STATUS,
                   help="status carried by the tick line (default: ok)")
    p.add_argument("--source", default=DEFAULT_SOURCE,
                   help="tick source label (default: workflow_dispatch)")
    p.add_argument("--alert-minutes", type=float,
                   default=DEFAULT_ALERT_MINUTES,
                   help="loss-of-contact threshold in minutes (default: 90)")
    p.add_argument("--now", default=None,
                   help="ISO 8601 now override (offline vectors only)")
    p.add_argument("--selftest", action="store_true",
                   help="run the offline vectors in a private temp dir")
    args = p.parse_args(argv)
    if args.selftest:
        return selftest()
    try:
        return run(args)
    except UsageError as exc:
        sys.stderr.write("usage: %s\n" % exc)
        return 2
    except FailLoud as exc:
        sys.stderr.write("fail-loud: %s\n" % exc)
        return 9


if __name__ == "__main__":
    sys.exit(main())
