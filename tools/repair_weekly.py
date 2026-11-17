#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repair_weekly: repair-outcome ledger weekly distribution face (E6).

    Purpose.  Aggregates the repair-outcome ledger (docs/repair-ledger.jsonl,
      append-only JSONL) into the weekly distribution face: the per-red
      outcome census under the E6 vocabulary, class and ticket
      distributions, and the ISO-week slice of --date.  /1 rows carry the
      free-form outcome field and are normalized (the token before the
      first parenthesis; unrecognized tokens stay data); /2 rows carry
      repair-outcome verbatim under the enforced vocabulary.  Read-only
      over the ledger; --out and --json are the only write faces.
    Interface.  cw.sh repair-weekly [--ledger P] [--date YYYY-MM-DD]
      [--out FILE] [--json P] | --record --class CLASS --target T
      --repair-outcome VALUE [--ticket K] [--evidence-file J] [--reason S]
      [--apply] | --selftest.  Report schema rocqwash-repair-weekly/1;
      record rows rocqwash-repair-ledger/2 (append-only, no dedup).  A
      missing outcome field on a /1 row is data; a missing repair-outcome
      field on a /2 row is fail-loud.
    Dependencies.  Python 3 stdlib only (argparse, datetime, io, json, os,
      sys, time); bash 3.2 compatible through cw.sh; the default ledger
      path resolves repo-relative from the script location; zero network;
      zero subprocess.
    Evidence.  --selftest covers the /1-to-E6 normalization, the /2
      vocabulary gate, window slicing, byte-identical reruns, the
      fail-loud paths, and the record refusals; the write faces are
      pinned by the K rows of tests/test_destructive_matrix.py.
    Exit-codes.  0 = report produced (an absent default-path ledger is a
      zero-row report); 1 = selftest red; 2 = usage error, malformed row,
      or vocabulary refusal; 9 = missing input (an explicitly named
      --ledger or --evidence-file path absent).
"""
# Extended contract (kept outside the five-field block; budget discipline):
#
# E6 outcome vocabulary.  Every red case is accounted with one ledger row
# whose repair-outcome value is one of:
#   repaired                          the repair was applied in place;
#   escalated(evidence-package)       the red leaves this repair scope
#                                     with an evidence package in the
#                                     row's evidence field (non-empty);
#   watch-only(guard-correct: R)      the red is not a repair target: the
#     R in cancel-intent | superseded | budget | out-of-scope
#                                     guard was correct, and the row
#                                     records why nothing was done.
# The /1 rows predate the vocabulary: their free-form outcome value is
# normalized by the token before the first parenthesis, so
# "repaired(doc-count-sync)" normalizes to repaired.  A /1 escalated row
# whose evidence field is absent or empty is counted, never reclassified:
# it lands in the escalated-without-evidence-package line of the report.
#
# Determinism.  The aggregate and JSON faces carry no wall clock: the
# window comes from --date (the ISO week containing it), every count comes
# from the ledger content, and identical inputs produce byte-identical
# reruns.  Record rows are the exception: they are runtime accounting
# events and carry the append-time timestamp, the same form as every
# other ledger writer in this repository.

import argparse
import datetime as _dt
import io
import json
import os
import sys
import time

PROG = "repair_weekly"
SCHEMA_REPORT = "rocqwash-repair-weekly/1"
SCHEMA_LEDGER_V1 = "rocqwash-repair-ledger/1"
SCHEMA_LEDGER_V2 = "rocqwash-repair-ledger/2"

DEFAULT_LEDGER_REL = "docs/repair-ledger.jsonl"

OUTCOME_REPAIRED = "repaired"
OUTCOME_ESCALATED = "escalated(evidence-package)"
OUTCOME_WATCH_ONLY = "watch-only"
OUTCOME_BASES = (OUTCOME_REPAIRED, "escalated", OUTCOME_WATCH_ONLY)
GUARD_CORRECT_REASONS = ("cancel-intent", "superseded", "budget",
                         "out-of-scope")
WATCH_PREFIX = "watch-only(guard-correct:"
ESCALATED_TAG = "evidence-package"


class UsageError(Exception):
    """Usage error, malformed input, or vocabulary refusal (exit 2)."""


class MissingInput(Exception):
    """A required input file is absent (exit 9, fail-loud)."""


# ---- ledger reading ----

def ledger_rows(path):
    """The ledger rows, fail-loud on malformed lines (append-only JSONL)."""
    if not os.path.isfile(path):
        return None
    rows = []
    with io.open(path, "r", encoding="utf-8") as fh:
        for no, ln in enumerate(fh, start=1):
            ln = ln.strip()
            if not ln:
                continue
            try:
                row = json.loads(ln)
            except ValueError as exc:
                raise UsageError("repair ledger row %d is not valid JSON"
                                 " (%s): %s" % (no, path, exc))
            if not isinstance(row, dict):
                raise UsageError("repair ledger row %d is not an object:"
                                 " %s" % (no, path))
            rows.append(row)
    return rows


def row_ts(row):
    """The row timestamp as a datetime, or None when absent/unparseable."""
    raw = row.get("ts_utc") or row.get("utc")
    if not isinstance(raw, str):
        return None
    try:
        return _dt.datetime.strptime(raw.strip(), "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def parse_repair_outcome(value, rowno):
    """Validate one /2 repair-outcome value against the E6 vocabulary.

    Returns (base, reason) with base in OUTCOME_BASES and reason None or
    a guard-correct reason; a vocabulary violation is fail-loud."""
    v = (value or "").strip()
    if v == OUTCOME_REPAIRED:
        return (OUTCOME_REPAIRED, None)
    if v == OUTCOME_ESCALATED:
        return ("escalated", None)
    if v.startswith(WATCH_PREFIX) and v.endswith(")"):
        reason = v[len(WATCH_PREFIX):-1].strip()
        if reason not in GUARD_CORRECT_REASONS:
            raise UsageError(
                "repair ledger row %d: watch-only guard-correct reason"
                " %r is outside the vocabulary %s"
                % (rowno, reason, "|".join(GUARD_CORRECT_REASONS)))
        return (OUTCOME_WATCH_ONLY, reason)
    raise UsageError(
        "repair ledger row %d: repair-outcome value %r is outside the"
        " E6 vocabulary (%s | %s | %s)"
        % (rowno, value, OUTCOME_REPAIRED, OUTCOME_ESCALATED,
           WATCH_PREFIX + " |".join(GUARD_CORRECT_REASONS) + ")"))


def has_evidence(row):
    """True when the row carries a non-empty evidence package."""
    ev = row.get("evidence")
    if isinstance(ev, dict):
        return len(ev) > 0
    if isinstance(ev, (list, tuple)):
        return len(ev) > 0
    if isinstance(ev, str):
        return bool(ev.strip())
    return False


def normalize_outcome(row, rowno):
    """(base, reason, recorded) for one row of either schema version.

    A /2 row is validated strictly; a /1 row is normalized by the token
    before the first parenthesis.  Returns base None for a /1 value the
    vocabulary does not cover (unrecognized tokens stay data)."""
    if row.get("schema") == SCHEMA_LEDGER_V2:
        if "repair-outcome" not in row:
            raise UsageError("repair ledger row %d: a %s row without a"
                             " repair-outcome field is a contract"
                             " violation" % (rowno, SCHEMA_LEDGER_V2))
        base, reason = parse_repair_outcome(row["repair-outcome"], rowno)
        if base == "escalated" and not has_evidence(row):
            base = "escalated-no-evidence"
        return (base, reason, row.get("repair-outcome"))
    raw = row.get("outcome")
    if not isinstance(raw, str) or not raw.strip():
        return (None, None, "(missing outcome field)")
    token = raw.strip().split("(", 1)[0].strip()
    if token == OUTCOME_REPAIRED:
        return (OUTCOME_REPAIRED, None, raw)
    if token == "escalated":
        base = "escalated" if has_evidence(row) else "escalated-no-evidence"
        return (base, None, raw)
    if token == OUTCOME_WATCH_ONLY:
        return (OUTCOME_WATCH_ONLY, None, raw)
    return (None, None, raw)


# ---- aggregation ----

def iso_week_window(date_str):
    """(monday, sunday, (iso_year, iso_week)) for a YYYY-MM-DD date."""
    try:
        day = _dt.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise UsageError("--date expects YYYY-MM-DD, got %r" % date_str)
    monday = (day - _dt.timedelta(days=day.weekday())).date()
    sunday = monday + _dt.timedelta(days=6)
    iso = day.isocalendar()
    return (monday, sunday, (iso[0], iso[1]))


def aggregate(rows, window):
    """The distribution report dict (input-derived only, no wall clock)."""
    monday, sunday, iso = window
    rep = {
        "schema": SCHEMA_REPORT,
        "window": {"monday": monday.isoformat(),
                   "sunday": sunday.isoformat(),
                   "iso_week": "%d-W%02d" % (iso[0], iso[1])},
        "rows_total": len(rows),
        "schemas_seen": {},
        "in_window": 0,
        "out_of_window": 0,
        "no_timestamp": 0,
        "outcome_distribution": {OUTCOME_REPAIRED: 0, "escalated": 0,
                                 OUTCOME_WATCH_ONLY: 0},
        "guard_correct_reasons": {},
        "escalated_without_evidence": 0,
        "unrecognized": [],
        "class_distribution": {},
        "ticket_distribution": {},
        "rows": [],
    }
    for i, row in enumerate(rows, start=1):
        schema = row.get("schema") or "(no schema field)"
        rep["schemas_seen"][schema] = rep["schemas_seen"].get(schema, 0) + 1
        base, reason, recorded = normalize_outcome(row, i)
        ts = row_ts(row)
        if ts is None:
            state = "no-timestamp"
            rep["no_timestamp"] += 1
        elif monday <= ts.date() <= sunday:
            state = "in"
            rep["in_window"] += 1
        else:
            state = "out"
            rep["out_of_window"] += 1
        if base is None:
            rep["unrecognized"].append({"row": i, "outcome": recorded})
        elif state == "in":
            key = base if base != "escalated-no-evidence" else "escalated"
            rep["outcome_distribution"][key] += 1
            if base == "escalated-no-evidence":
                rep["escalated_without_evidence"] += 1
            if reason:
                rep["guard_correct_reasons"][reason] = \
                    rep["guard_correct_reasons"].get(reason, 0) + 1
            cls = row.get("class") or "(no class field)"
            rep["class_distribution"][cls] = \
                rep["class_distribution"].get(cls, 0) + 1
            ticket = row.get("ticket") or "(no ticket field)"
            rep["ticket_distribution"][ticket] = \
                rep["ticket_distribution"].get(ticket, 0) + 1
        rep["rows"].append({
            "row": i,
            "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None,
            "window": state,
            "class": row.get("class"),
            "target": row.get("target"),
            "ticket": row.get("ticket"),
            "outcome_recorded": recorded,
            "outcome_e6": base,
            "guard_correct_reason": reason,
            "schema": schema,
        })
    return rep


def pct(n, total):
    return "%.1f%%" % (100.0 * n / total) if total else "0.0%"


def render_markdown(rep, out_name):
    """The weekly markdown face (banner + five-field block + tables)."""
    w = rep["window"]
    total = rep["in_window"]
    dist = rep["outcome_distribution"]
    ls = []
    ls.append("# %s — repair-outcome ledger weekly distribution face." %
              os.path.basename(out_name))
    ls.append("")
    ls.append("> **RepairWeeklyFace**: the weekly distribution of the")
    ls.append("> repair-outcome ledger under the E6 vocabulary, generated")
    ls.append("> by `tools/repair_weekly.py` from the ledger content only.")
    ls.append(">")
    ls.append("> Purpose.  Account every red case recorded in")
    ls.append("> `docs/repair-ledger.jsonl` for the ISO week of the report")
    ls.append("> date: the outcome census (repaired,")
    ls.append("> escalated(evidence-package), watch-only), the")
    ls.append("> guard-correct reason breakdown, the class and ticket")
    ls.append("> distributions, and a digest of every row with its window")
    ls.append("> state.")
    ls.append(">")
    ls.append("> Interface.  `cw.sh repair-weekly --date YYYY-MM-DD --out")
    ls.append("> FILE [--ledger P] [--json P]`; regenerating this face")
    ls.append("> reruns the aggregation from the same ledger content, and")
    ls.append("> identical inputs give byte-identical reruns.")
    ls.append(">")
    ls.append("> Dependencies.  Generated from the ledger rows only; no")
    ls.append("> wall clock and no absolute path enters the face.")
    ls.append(">")
    ls.append("> Evidence.  Row counts here are reproducible with")
    ls.append("> `--json`; the generator selftest and the destructive")
    ls.append("> matrix K rows pin the aggregation and write faces.")
    ls.append(">")
    ls.append("> Exit-codes.  The face is a report; findings are data and")
    ls.append("> the generator exit code never escalates on them.")
    ls.append("")
    ls.append("## 1. Window and input")
    ls.append("")
    ls.append("| field | value |")
    ls.append("|---|---|")
    ls.append("| report date basis | %s |" % w["iso_week"])
    ls.append("| window | %s .. %s (%s) |" % (w["monday"], w["sunday"],
                                              w["iso_week"]))
    ls.append("| ledger rows total | %d |" % rep["rows_total"])
    ls.append("| rows in window | %d |" % rep["in_window"])
    ls.append("| rows out of window | %d |" % rep["out_of_window"])
    ls.append("| rows without a parseable timestamp | %d |" %
              rep["no_timestamp"])
    schemas = sorted(rep["schemas_seen"].items())
    ls.append("| schemas seen | %s |" %
              ("; ".join("%s x%d" % (k, v) for k, v in schemas) or "none"))
    ls.append("")
    ls.append("## 2. Outcome distribution (E6 vocabulary, in-window rows)")
    ls.append("")
    ls.append("| repair-outcome | rows | share |")
    ls.append("|---|---|---|")
    ls.append("| %s | %d | %s |" % (OUTCOME_REPAIRED, dist[OUTCOME_REPAIRED],
                                    pct(dist[OUTCOME_REPAIRED], total)))
    ls.append("| %s | %d | %s |" % (OUTCOME_ESCALATED, dist["escalated"],
                                    pct(dist["escalated"], total)))
    ls.append("| %s | %d | %s |" % (OUTCOME_WATCH_ONLY,
                                    dist[OUTCOME_WATCH_ONLY],
                                    pct(dist[OUTCOME_WATCH_ONLY], total)))
    ls.append("")
    notes = []
    if rep["escalated_without_evidence"]:
        notes.append("escalated rows without an evidence package: %d"
                     % rep["escalated_without_evidence"])
    if rep["unrecognized"]:
        notes.append("unrecognized outcome tokens: %s" %
                     ", ".join("%s (row %d)" % (u["outcome"], u["row"])
                               for u in rep["unrecognized"]))
    ls.append(notes and "; ".join(notes) + "." or
              "No side-state to declare: every in-window row normalized"
              " into the vocabulary, no escalated row lacks an evidence"
              " package.")
    ls.append("")
    ls.append("## 3. Guard-correct reasons (watch-only)")
    ls.append("")
    reasons = sorted(rep["guard_correct_reasons"].items())
    if reasons:
        for k, v in reasons:
            ls.append("- %s: %d" % (k, v))
    else:
        ls.append("none recorded.")
    ls.append("")
    ls.append("## 4. Class distribution (in-window rows)")
    ls.append("")
    ls.append("| class | rows |")
    ls.append("|---|---|")
    for k, v in sorted(rep["class_distribution"].items()):
        ls.append("| %s | %d |" % (k, v))
    if not rep["class_distribution"]:
        ls.append("| (none in window) | 0 |")
    ls.append("")
    ls.append("## 5. Ticket distribution (in-window rows)")
    ls.append("")
    ls.append("| ticket | rows |")
    ls.append("|---|---|")
    for k, v in sorted(rep["ticket_distribution"].items()):
        ls.append("| %s | %d |" % (k, v))
    if not rep["ticket_distribution"]:
        ls.append("| (none in window) | 0 |")
    ls.append("")
    ls.append("## 6. Row digest (all rows)")
    ls.append("")
    ls.append("| # | timestamp | window | class | target | ticket |"
              " outcome as recorded | E6 outcome |")
    ls.append("|---|---|---|---|---|---|---|---|")
    for r in rep["rows"]:
        ls.append("| %d | %s | %s | %s | %s | %s | %s | %s |" % (
            r["row"], r["ts"] or "(no timestamp)", r["window"],
            r["class"] or "(none)", r["target"] or "(none)",
            r["ticket"] or "(none)", r["outcome_recorded"],
            r["outcome_e6"] or "unrecognized"))
    ls.append("")
    ls.append("## 7. Schema extension register (rocqwash-repair-ledger/2)")
    ls.append("")
    ls.append("The E6 extension adds the `repair-outcome` field with the")
    ls.append("values `repaired`, `escalated(evidence-package)` (the row")
    ls.append("carries a non-empty `evidence` package), and")
    ls.append("`watch-only(guard-correct: cancel-intent | superseded |")
    ls.append("budget | out-of-scope)`.  `/1` rows stay valid and are")
    ls.append("normalized by the token before the first parenthesis; new")
    ls.append("per-red rows are appended by `cw.sh repair-weekly --record`.")
    ls.append("")
    return "\n".join(ls)


def render_json(rep):
    return json.dumps(rep, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


# ---- record face ----

def record_row(args):
    """One validated /2 ledger row (no write here)."""
    value = args.repair_outcome
    row = {"schema": SCHEMA_LEDGER_V2,
           "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "kind": "repair-outcome",
           "class": args.record_class,
           "target": args.target,
           "repair-outcome": value}
    if args.ticket:
        row["ticket"] = args.ticket
    if args.reason:
        row["reason"] = args.reason
    base, reason = parse_repair_outcome(value, 0)
    if base == "escalated":
        if not args.evidence_file:
            raise UsageError(
                "--record escalated(evidence-package) needs --evidence-file"
                " (the evidence package is part of the outcome)")
        if not os.path.isfile(args.evidence_file):
            raise MissingInput("evidence file absent: %s" % args.evidence_file)
        with io.open(args.evidence_file, "r", encoding="utf-8") as fh:
            try:
                row["evidence"] = json.load(fh)
            except ValueError as exc:
                raise UsageError("evidence file is not valid JSON: %s"
                                 " (%s)" % (args.evidence_file, exc))
        if not has_evidence(row):
            raise UsageError("evidence file carries an empty package: %s"
                             % args.evidence_file)
    if reason:
        row["guard-correct"] = reason
    return row


def ledger_append(path, row):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


# ---- selftest ----

def selftest():
    """Deterministic vectors on tmp fixtures; returns (ok, detail)."""
    import tempfile
    import shutil
    import hashlib
    tmp = tempfile.mkdtemp(prefix="repair_weekly_selftest_")
    ok, detail = True, []

    def vec(name, cond, extra=""):
        nonlocal ok
        hit = bool(cond)
        ok = ok and hit
        detail.append("%s %s%s" % ("PASS" if hit else "FAIL", name,
                                   (" :: " + extra) if extra and not hit else
                                   ""))
        return hit

    try:
        # v1 normalization and window slicing (fixture mirrors the real
        # three-row ledger plus one out-of-window row).
        led = os.path.join(tmp, "led.jsonl")
        rows = [
            {"class": "doc-count", "outcome": "repaired(doc-count-sync)",
             "schema": SCHEMA_LEDGER_V1, "target": "README-cw.md",
             "utc": "2026-11-16T13:30:43Z"},
            {"branch": "main", "class": "flaky-quarantine",
             "evidence": {"alone_rc": 1, "verdict": "content-red"},
             "head_sha": "eb01729", "kind": "repair", "outcome": "escalated",
             "reason": "content-red case stays visible",
             "schema": SCHEMA_LEDGER_V1, "target": "t_verify_fresh",
             "ticket": "E2-3", "ts_utc": "2026-11-16T14:31:34Z"},
            {"class": "flaky-quarantine", "outcome": "repaired",
             "schema": SCHEMA_LEDGER_V1, "target": "tests/t.py",
             "ticket": "E2-3", "ts_utc": "2026-11-16T14:32:08Z"},
            {"class": "doc-count", "outcome": "repaired",
             "schema": SCHEMA_LEDGER_V1, "target": "old.md",
             "utc": "2026-11-10T00:00:00Z"},
        ]
        with io.open(led, "w", encoding="utf-8", newline="\n") as fh:
            for r in rows:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
        monday, sunday, iso = iso_week_window("2026-11-17")
        vec("iso-week", (str(monday) == "2026-11-16" and
                         str(sunday) == "2026-11-22" and
                         iso == (2026, 47)), "%s %s %s" % (monday, sunday, iso))
        rep = aggregate(ledger_rows(led), (monday, sunday, iso))
        vec("v1-in-window", rep["in_window"] == 3 and
            rep["out_of_window"] == 1, json.dumps(
                {k: rep[k] for k in ("in_window", "out_of_window")}))
        vec("v1-normalize", rep["outcome_distribution"] ==
            {OUTCOME_REPAIRED: 2, "escalated": 1, OUTCOME_WATCH_ONLY: 0} and
            rep["escalated_without_evidence"] == 0,
            json.dumps(rep["outcome_distribution"]))
        vec("v1-class", rep["class_distribution"] ==
            {"doc-count": 1, "flaky-quarantine": 2} and
            rep["ticket_distribution"] ==
            {"(no ticket field)": 1, "E2-3": 2},
            json.dumps([rep["class_distribution"],
                        rep["ticket_distribution"]]))
        # v2 vocabulary: valid values, malformed values, evidence gate.
        led2 = os.path.join(tmp, "led2.jsonl")
        good = [
            {"schema": SCHEMA_LEDGER_V2, "class": "c", "target": "t",
             "repair-outcome": "repaired",
             "ts_utc": "2026-11-17T00:00:00Z"},
            {"schema": SCHEMA_LEDGER_V2, "class": "c", "target": "t2",
             "repair-outcome": "escalated(evidence-package)",
             "evidence": {"pack": "full"},
             "ts_utc": "2026-11-17T00:00:01Z"},
            {"schema": SCHEMA_LEDGER_V2, "class": "c", "target": "t3",
             "repair-outcome": "watch-only(guard-correct: budget)",
             "ts_utc": "2026-11-17T00:00:02Z"},
        ]
        with io.open(led2, "w", encoding="utf-8", newline="\n") as fh:
            for r in good:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
        rep2 = aggregate(ledger_rows(led2), (monday, sunday, iso))
        vec("v2-vocab", rep2["outcome_distribution"] ==
            {OUTCOME_REPAIRED: 1, "escalated": 1, OUTCOME_WATCH_ONLY: 1}
            and rep2["guard_correct_reasons"] == {"budget": 1},
            json.dumps([rep2["outcome_distribution"],
                        rep2["guard_correct_reasons"]]))
        for bad, why in (
                ("watch-only(guard-correct: vibes)", "bad reason"),
                ("escalated", "escalated without evidence"),
                ("possibly-fine", "outside vocabulary")):
            try:
                parse_repair_outcome(bad, 0)
                vec("v2-refuse %s" % why, False, "accepted %r" % bad)
            except UsageError:
                vec("v2-refuse %s" % why, True)
        v2_no_field = {"schema": SCHEMA_LEDGER_V2, "class": "c",
                       "target": "t"}
        try:
            normalize_outcome(v2_no_field, 1)
            vec("v2-missing-field", False, "accepted a /2 row without"
                " repair-outcome")
        except UsageError:
            vec("v2-missing-field", True)
        # byte-identical reruns on both output faces.
        out_md = os.path.join(tmp, "w.md")
        out_js = os.path.join(tmp, "w.json")
        md5s = []
        for _ in range(2):
            rc = run_aggregate(led, "2026-11-17", out_md, out_js)
            if rc != 0:
                vec("rerun rc", False, "rc=%d" % rc)
                break
            md5s.append((hashlib.md5(io.open(out_md, "rb").read())
                         .hexdigest(),
                         hashlib.md5(io.open(out_js, "rb").read())
                         .hexdigest()))
        else:
            vec("byte-identical-reruns", md5s[0] == md5s[1],
                str(md5s))
        # fail-loud: malformed row rc 2; absent explicit ledger rc 9;
        # absent default-path ledger is a zero-row report rc 0.
        bad_led = os.path.join(tmp, "bad.jsonl")
        io.open(bad_led, "w", encoding="utf-8", newline="\n").write(
            "{not json\n")
        try:
            ledger_rows(bad_led)
            vec("malformed-row", False, "accepted malformed JSON")
        except UsageError:
            vec("malformed-row", True)
        absent = os.path.join(tmp, "absent.jsonl")
        try:
            run_aggregate(absent, "2026-11-17", None, None, explicit=True)
            vec("absent-explicit-fail-loud", False,
                "an explicitly named absent ledger did not raise")
        except MissingInput:
            vec("absent-explicit-fail-loud", True)
        rc = run_aggregate(absent, "2026-11-17", None, None,
                           explicit=False)
        vec("absent-default-data", rc == 0, "rc=%d" % rc)
        # CLI exit-code mapping (subprocess, the same face the suite sees).
        import subprocess
        cli = [sys.executable, "-B", os.path.abspath(__file__)]
        pr = subprocess.run(cli + ["--ledger", absent, "--date",
                                   "2026-11-17", "--json",
                                   os.path.join(tmp, "never.json")],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        vec("cli-absent-rc9", pr.returncode == 9, "rc=%d" % pr.returncode)
        pr = subprocess.run(cli + ["--ledger", bad_led, "--date",
                                   "2026-11-17"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        vec("cli-malformed-rc2", pr.returncode == 2, "rc=%d" % pr.returncode)
        # record face: plan zero-write, apply appends exactly one row,
        # escalated refusal without evidence.
        ev = os.path.join(tmp, "ev.json")
        io.open(ev, "w", encoding="utf-8", newline="\n").write(
            '{"pack": "full"}\n')
        args = argparse.Namespace(
            record=True, apply=False, record_class="c", target="t",
            repair_outcome="escalated(evidence-package)", ticket="E6",
            evidence_file=ev, reason=None, ledger=led, repo=None,
            date=None, out=None, json_out=None, selftest=False)
        r0 = record_row(args)
        vec("record-plan-row", r0["schema"] == SCHEMA_LEDGER_V2 and
            r0["repair-outcome"] == "escalated(evidence-package)",
            json.dumps(r0))
        before = ledger_rows(led)
        args = argparse.Namespace(
            record=True, apply=True, record_class="c", target="t",
            repair_outcome="watch-only(guard-correct: out-of-scope)",
            ticket=None, evidence_file=None,
            reason="guard refusal is data", ledger=led, repo=None,
            date=None, out=None, json_out=None, selftest=False)
        r1 = record_row(args)
        ledger_append(led, r1)
        after = ledger_rows(led)
        vec("record-apply-one-row", len(after) == len(before) + 1 and
            after[-1]["repair-outcome"] ==
            "watch-only(guard-correct: out-of-scope)",
            "before=%d after=%d" % (len(before), len(after)))
        args = argparse.Namespace(
            record=True, apply=True, record_class="c", target="t",
            repair_outcome="escalated(evidence-package)", ticket=None,
            evidence_file=None, reason=None, ledger=led, repo=None,
            date=None, out=None, json_out=None, selftest=False)
        try:
            record_row(args)
            vec("record-escalated-refusal", False, "accepted without"
                " evidence file")
        except UsageError:
            vec("record-escalated-refusal", True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return ok, detail


def run_aggregate(ledger, date, out, json_out, explicit=True):
    """One aggregate run against a given ledger path (selftest driver)."""
    rows = ledger_rows(ledger)
    if rows is None:
        if explicit:
            raise MissingInput("ledger absent: %s" % ledger)
        rows = []
    rep = aggregate(rows, iso_week_window(date))
    if out:
        with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_markdown(rep, out))
    if json_out:
        with io.open(json_out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_json(rep))
    return 0


# ---- cli ----

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog=PROG, description="repair-outcome ledger weekly distribution"
        " face (repair class E6)")
    ap.add_argument("--ledger", default=None,
                    help="ledger path (default %s)" % DEFAULT_LEDGER_REL)
    ap.add_argument("--date", default=None,
                    help="report date YYYY-MM-DD; the window is the ISO"
                    " week containing it")
    ap.add_argument("--out", default=None,
                    help="weekly markdown face output path (stdout when"
                    " absent)")
    ap.add_argument("--json", dest="json_out", default=None,
                    help="machine report output path (%s)" % SCHEMA_REPORT)
    ap.add_argument("--record", action="store_true",
                    help="record one per-red outcome row instead of"
                    " aggregating")
    ap.add_argument("--apply", action="store_true",
                    help="with --record: append the row (plan without it)")
    ap.add_argument("--class", dest="record_class", default=None,
                    help="with --record: the repair class of the red case")
    ap.add_argument("--target", default=None,
                    help="with --record: the red case target")
    ap.add_argument("--repair-outcome", default=None,
                    help="with --record: %s | %s | %s" %
                    (OUTCOME_REPAIRED, OUTCOME_ESCALATED,
                     WATCH_PREFIX + "REASON)"))
    ap.add_argument("--ticket", default=None,
                    help="with --record: the ticket identifier")
    ap.add_argument("--evidence-file", default=None,
                    help="with --record: JSON file carrying the evidence"
                    " package (mandatory for escalated)")
    ap.add_argument("--reason", default=None,
                    help="with --record: one-line reason note")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    try:
        if args.selftest:
            if args.record:
                raise UsageError("--selftest and --record are mutually"
                                 " exclusive")
            ok, detail = selftest()
            for ln in detail:
                print(ln)
            if ok:
                print("REPAIR-WEEKLY-SELFTEST PASS")
                return 0
            print("REPAIR-WEEKLY-SELFTEST RED", file=sys.stderr)
            return 1

        repo_root = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))
        ledger = args.ledger or os.path.join(repo_root, DEFAULT_LEDGER_REL)
        if not os.path.isfile(ledger) and args.ledger:
            raise MissingInput("ledger absent: %s" % ledger)

        if args.record:
            if not (args.record_class and args.target and
                    args.repair_outcome):
                raise UsageError("--record needs --class, --target, and"
                                 " --repair-outcome")
            row = record_row(args)
            if args.apply:
                ledger_append(ledger, row)
                print("APPLIED record-row-appended=1 ledger=%s" % ledger)
            else:
                print("PLAN record-row=%s" %
                      json.dumps(row, ensure_ascii=False, sort_keys=True))
            return 0

        if not args.date:
            raise UsageError("--date YYYY-MM-DD is required for the"
                             " aggregate face")
        rows = ledger_rows(ledger)
        if rows is None:
            rows = []
        rep = aggregate(rows, iso_week_window(args.date))
        if args.out or args.json_out:
            if args.out:
                with io.open(args.out, "w", encoding="utf-8",
                             newline="\n") as fh:
                    fh.write(render_markdown(rep, args.out))
            if args.json_out:
                with io.open(args.json_out, "w", encoding="utf-8",
                             newline="\n") as fh:
                    fh.write(render_json(rep))
            print("WROTE weekly=%s json=%s rows_total=%d in_window=%d" %
                  (args.out or "(none)", args.json_out or "(none)",
                   rep["rows_total"], rep["in_window"]))
            return 0
        sys.stdout.write(render_markdown(rep, "repair-weekly.md"))
        return 0
    except UsageError as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        return 2
    except MissingInput as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        return 9


if __name__ == "__main__":
    sys.exit(main())
