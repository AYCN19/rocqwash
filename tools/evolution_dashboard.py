#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Sign-off: \u738b\u5c0f\u54e5 (rocqwash \u81ea\u6f14\u8fdb\u7ebf\u00b7\u4eea\u8868\u76d8\u5e2d)
"""evolution_dashboard.py - self-evolution dashboard over the three standing accounts.
Purpose.  Aggregate the experience ledger (docs/exp-ledger.jsonl, schema
  rocqwash-exp/1), the round ledger (docs/round-ledger.jsonl, schema
  rocqwash-round/1), and vacgen v2 report JSON files (the TODO-SEAT faces)
  into one dashboard: the coverageLowerPct curve over report runs with a
  per-point TODO-SEAT delta and rise flag, the rounds conversion face,
  and the per-run gap thermometer reading.  Absent standing ledgers and
  zero rows are data, loudly marked, never errors; every reading is a
  dated snapshot taken from input content only.
Interface.  `python -I tools/evolution_dashboard.py [--repo ROOT]
  [--exp-ledger P] [--rounds P] [--reports P]... [--json-out P]
  [--md-out P] [--stdout markdown|json] [--selftest]`.  Defaults resolve
  against the repository root (the parent of tools/): docs/exp-ledger.jsonl,
  docs/round-ledger.jsonl, docs/vacgen-reports (a directory expands to its
  *.json files, sorted).  A default-path input that is absent is a data
  state (present=false); an explicitly flagged absent path exits 9.  Only
  the caller-named --json-out / --md-out files are written; stdout carries
  the summary line plus the selected face.
Dependencies.  Python 3 stdlib only (argparse/json/os/shutil/sys/tempfile);
  zero network (no socket face; NETRED: no network by design); zero
  eval/exec; deterministic: the runtime clock never enters the logic.
Evidence.  --selftest on tmp fixtures: happy-path math and curve order,
  byte-identical reruns, absent-defaults-as-data, corrupt-input exit 9
  zero writes, the rise flag, both faces byte-equal to --stdout.
Exit-codes.  0 = dashboard produced (absent inputs / zero rows are data);
  1 = selftest red; 2 = usage error (bad --stdout choice); 9 = missing or
  corrupt input (an explicitly named path absent, invalid JSON, no vacgen
  face, or a write failure; nothing written).
"""

import argparse
import json
import os
import shutil
import sys
import tempfile

PROG = "evolution_dashboard"
SCHEMA = "rocqwash-evolution-dashboard/1"
TOOL_VERSION = "1.0.0"
EXP_DEFAULT = ("docs", "exp-ledger.jsonl")
ROUNDS_DEFAULT = ("docs", "round-ledger.jsonl")
REPORTS_DEFAULT = ("docs", "vacgen-reports")

# Field notes (the reading rules this dashboard implements; consumers of the
# JSON face rely on these exact definitions):
# - rounds conversion: classConversionPct = sum(len(admissions)) * 100 // 
#   sum(len(classes_applied)) over all rounds (round rows with an empty
#   classes_applied, e.g. rollback/salvage modes, contribute zero to both
#   sums); None when no round carries any applied class.  greenRounds counts
#   rows with verify_rc == 0; greenPct = greenRounds * 100 // roundsTotal.
# - coverage curve: one point per vacgen report file, ordered by the
#   content-borne time point then runId; todoSeatsDelta is the difference
#   against the previous point in that order; a positive delta sets the
#   rise flag (vacgen's fill-round discipline expects the TODO-SEAT count
#   to be monotone non-increasing, so a rise is a signal, reported as data).
# - thermometer: the latest curve point (largest time point, then runId) is
#   the current reading: its TODO-SEAT gap count and coverageLowerPct.

MD_TITLE = ("# \u81ea\u6f14\u8fdb\u4eea\u8868\u76d8 / Evolution Dashboard "
            "(schema %s)" % SCHEMA)


class DashboardInputError(Exception):
    """Missing or corrupt input (exit code 9); the message names the file."""


def repo_root():
    """Repository root: the parent of tools/ (this file lives in tools/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_path(parts):
    """Repo-relative default path joined as a string."""
    return "/".join(parts)


def read_jsonl(path, label):
    """Parse a JSONL account into dict rows (a '#' first character marks a
    comment line and is skipped; blank lines are skipped).  A line that is
    not valid JSON or not a JSON object raises DashboardInputError (exit 9,
    fail loud, nothing written)."""
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            try:
                entry = json.loads(text)
            except ValueError as exc:
                raise DashboardInputError(
                    "%s %s line %d is not valid JSON: %s"
                    % (label, path, lineno, exc))
            if not isinstance(entry, dict):
                raise DashboardInputError(
                    "%s %s line %d is not a JSON object" % (label, path, lineno))
            rows.append(entry)
    return rows


def read_rounds(path):
    """Parse the round ledger with structural loudness: a row without an
    int round_id >= 1 is damaged input (exit 9), extra keys are tolerated
    (additive schema convention)."""
    rows = read_jsonl(path, "round ledger")
    for idx, row in enumerate(rows, 1):
        rid = row.get("round_id")
        if isinstance(rid, bool) or not isinstance(rid, int) or rid < 1:
            raise DashboardInputError(
                "round ledger %s row %d carries no int round_id >= 1: %r"
                % (path, idx, rid))
    return rows


def rounds_face(rows):
    """Rounds conversion face (definitions in the field notes above)."""
    total = len(rows)
    modes = {}
    green = 0
    applied = 0
    admitted = 0
    per_round = []
    for row in rows:
        mode = str(row.get("mode", ""))
        modes[mode] = modes.get(mode, 0) + 1
        verify_rc = row.get("verify_rc")
        if verify_rc == 0:
            green += 1
        classes = row.get("classes_applied")
        admissions = row.get("admissions")
        n_classes = len(classes) if isinstance(classes, list) else 0
        n_adm = len(admissions) if isinstance(admissions, list) else 0
        applied += n_classes
        admitted += n_adm
        per_round.append({"roundId": row.get("round_id"), "mode": mode,
                          "classesApplied": n_classes, "admissions": n_adm,
                          "verifyRc": verify_rc})
    green_pct = (green * 100 // total) if total else None
    conv_pct = (admitted * 100 // applied) if applied else None
    per_round.sort(key=lambda r: (r["roundId"] is None, r["roundId"]))
    return {"roundsTotal": total, "modes": modes, "greenRounds": green,
            "greenPct": green_pct, "classesAppliedTotal": applied,
            "admissionsTotal": admitted, "classConversionPct": conv_pct,
            "perRound": per_round}


def exp_face(rows):
    """Experience ledger reading face: entry totals, per-batch counts, and
    the content-borne first/last time points (lexical min/max over ISO ts
    strings; entries without a ts are counted and tallied separately)."""
    batches = {}
    first_ts = None
    last_ts = None
    missing_ts = 0
    for row in rows:
        batch = row.get("batch")
        key = batch if isinstance(batch, str) and batch else "(no batch field)"
        ts = row.get("ts")
        ts = ts if isinstance(ts, str) and ts else None
        slot = batches.setdefault(key, {"entries": 0, "firstTs": None,
                                        "lastTs": None})
        slot["entries"] += 1
        if ts is None:
            missing_ts += 1
        else:
            if slot["firstTs"] is None or ts < slot["firstTs"]:
                slot["firstTs"] = ts
            if slot["lastTs"] is None or ts > slot["lastTs"]:
                slot["lastTs"] = ts
            if first_ts is None or ts < first_ts:
                first_ts = ts
            if last_ts is None or ts > last_ts:
                last_ts = ts
    batch_rows = [{"batch": key, "entries": slot["entries"],
                   "firstTs": slot["firstTs"], "lastTs": slot["lastTs"]}
                  for key, slot in sorted(batches.items())]
    return {"entriesTotal": len(rows), "batchCount": len(batches),
            "batches": batch_rows, "firstTs": first_ts, "lastTs": last_ts,
            "entriesWithoutTs": missing_ts}


def resolve_reports(paths, default_dir, repo):
    """Expand and order report inputs: duplicates collapsed, sorted path
    order; a directory expands to its *.json files in sorted order.  With
    no --reports flag the standing default directory is used and its
    absence is a data state (empty list); an explicitly flagged path that
    does not exist exits 9."""
    if not paths:
        default = os.path.join(repo, *default_dir)
        if not os.path.isdir(default):
            return [], default_dir, False
        resolved = sorted(
            os.path.join(default, name) for name in os.listdir(default)
            if name.endswith(".json"))
        return resolved, default_dir, True
    resolved = set()
    for path in paths:
        if os.path.isdir(path):
            for name in sorted(os.listdir(path)):
                if name.endswith(".json"):
                    resolved.add(os.path.join(path, name))
        elif os.path.isfile(path):
            resolved.add(path)
        else:
            raise DashboardInputError(
                "reports path %s does not exist (an explicitly flagged "
                "input must exist)" % path)
    return sorted(resolved), None, True


def parse_report(doc, name):
    """Discriminate the two vacgen report faces by their data shape and
    extract one curve point.  A document carrying neither face raises
    DashboardInputError (exit 9); a face without its id field likewise
    (a run without an id cannot ride the curve deterministically)."""
    if not isinstance(doc, dict):
        raise DashboardInputError("report %s is not a JSON object" % name)
    coverage = doc.get("coverage")
    aggregate = doc.get("aggregate")
    if isinstance(coverage, dict) and "todoSeats" in coverage:
        run_id = doc.get("reportId")
        if not isinstance(run_id, str) or not run_id:
            raise DashboardInputError(
                "report %s carries the cast coverage face without its "
                "reportId (a run without an id cannot ride the curve)" % name)
        cast = doc.get("cast") if isinstance(doc.get("cast"), dict) else {}
        files = cast.get("files")
        return {"runId": run_id, "shape": "cast",
                "ts": coverage.get("registeredAt"),
                "recognized": coverage.get("recognized"),
                "total": coverage.get("total"),
                "todoSeats": coverage.get("todoSeats"),
                "coverageLowerPct": coverage.get("coverageLowerPct"),
                "files": files if isinstance(files, int) else None}
    if isinstance(aggregate, dict) and "coverageLowerPct" in aggregate:
        run_id = doc.get("mapId")
        if not isinstance(run_id, str) or not run_id:
            raise DashboardInputError(
                "report %s carries the preflight-map face without its "
                "mapId (a run without an id cannot ride the curve)" % name)
        total = aggregate.get("assumptionsTotal")
        recognized = aggregate.get("recognized")
        todo = None
        if isinstance(total, int) and isinstance(recognized, int):
            todo = total - recognized
        return {"runId": run_id, "shape": "preflight-map",
                "ts": doc.get("generatedAt"), "recognized": recognized,
                "total": total, "todoSeats": todo,
                "coverageLowerPct": aggregate.get("coverageLowerPct"),
                "files": aggregate.get("files")}
    raise DashboardInputError(
        "report %s carries neither vacgen report face (no coverage "
        "todoSeats key, no aggregate coverageLowerPct key)" % name)


def read_reports(resolved):
    """Read every resolved report file into a curve point (sorted input
    order); damage fails loud before any output is produced."""
    points = []
    for path in resolved:
        with open(path, "r", encoding="utf-8") as handle:
            try:
                doc = json.load(handle)
            except ValueError as exc:
                raise DashboardInputError(
                    "report %s is not valid JSON: %s"
                    % (os.path.basename(path), exc))
        points.append(parse_report(doc, os.path.basename(path)))
    return points


def coverage_face(points):
    """Curve construction: content-borne ordering (time point, then runId),
    per-point TODO-SEAT delta against the previous point, the rise flag,
    and the latest point as the thermometer reading.  A point without a
    time point sorts first (undeclared-vintage face, marked dated=false)."""
    ordered = sorted(points, key=lambda p: (p.get("ts") or "",
                                            str(p.get("runId") or "")))
    curve = []
    prev = None
    for point in ordered:
        delta = None
        if prev is not None and isinstance(prev.get("todoSeats"), int) \
                and isinstance(point.get("todoSeats"), int):
            delta = point["todoSeats"] - prev["todoSeats"]
        row = dict(point)
        row["dated"] = bool(point.get("ts"))
        row["todoSeatsDelta"] = delta
        row["rising"] = bool(delta is not None and delta > 0)
        curve.append(row)
        prev = point
    rising = [row["runId"] for row in curve if row["rising"]]
    latest = curve[-1] if curve else None
    return {"reportRuns": len(points), "curve": curve, "latest": latest,
            "risingRuns": rising}


def build_dashboard(exp_rows, round_rows, points, inputs):
    """Assemble the dashboard document (pure function of its inputs)."""
    exp = exp_face(exp_rows)
    rounds = rounds_face(round_rows)
    coverage = coverage_face(points)
    return {"schema": SCHEMA,
            "tool": {"name": PROG, "version": TOOL_VERSION},
            "inputs": inputs,
            "experienceLedger": exp,
            "rounds": rounds,
            "coverage": coverage}


def collect(repo, exp_path, rounds_path, reports_args):
    """Read all three sources with the default/explicit absence rule and
    return (exp_rows, round_rows, points, inputs_meta)."""
    inputs = {}
    exp_default = default_path(EXP_DEFAULT)
    exp_given = exp_path is not None
    exp_use = exp_path if exp_given else os.path.join(repo, *EXP_DEFAULT)
    exp_present = os.path.isfile(exp_use)
    if not exp_present and exp_given:
        raise DashboardInputError(
            "experience ledger %s does not exist (an explicitly flagged "
            "input must exist)" % exp_path)
    inputs["experienceLedger"] = {
        "path": exp_path if exp_given else exp_default,
        "present": exp_present}
    exp_rows = read_jsonl(exp_use, "experience ledger") if exp_present else []

    rounds_default = default_path(ROUNDS_DEFAULT)
    rounds_given = rounds_path is not None
    rounds_use = rounds_path if rounds_given else \
        os.path.join(repo, *ROUNDS_DEFAULT)
    rounds_present = os.path.isfile(rounds_use)
    if not rounds_present and rounds_given:
        raise DashboardInputError(
            "round ledger %s does not exist (an explicitly flagged input "
            "must exist)" % rounds_path)
    inputs["roundLedger"] = {
        "path": rounds_path if rounds_given else rounds_default,
        "present": rounds_present}
    round_rows = read_rounds(rounds_use) if rounds_present else []

    resolved, default_dir, reports_present = resolve_reports(
        reports_args, REPORTS_DEFAULT, repo)
    inputs["vacgenReports"] = {
        "path": default_dir[0] + "/" + default_dir[1] if default_dir
        else resolved,
        "present": reports_present}
    points = read_reports(resolved) if reports_present else []
    return exp_rows, round_rows, points, inputs


def fmt(value):
    """Deterministic cell rendering: None renders as the dash cell."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def render_markdown(dash):
    """Render the markdown face: bilingual title, English table headers,
    one section per source, absent faces stated loudly, zero rows stated
    loudly.  Pure function of the dashboard document."""
    lines = [MD_TITLE, ""]
    lines.append("Generated from input content only; a reading covers the "
                 "files actually read, not the repository at large.")
    lines.append("")
    exp = dash["experienceLedger"]
    lines.append("## Experience ledger (schema rocqwash-exp/1)")
    lines.append("")
    if not dash["inputs"]["experienceLedger"]["present"]:
        lines.append("Ledger absent at its standing path %s: zero entries "
                     "recorded (data, not an error)."
                     % dash["inputs"]["experienceLedger"]["path"])
    elif exp["entriesTotal"] == 0:
        lines.append("Ledger present and empty: zero entries recorded "
                     "(data, not an error).")
    else:
        lines.append("| Batch | Entries | First ts | Last ts |")
        lines.append("|---|---|---|---|")
        for row in exp["batches"]:
            lines.append("| %s | %s | %s | %s |" % (row["batch"],
                                                    row["entries"],
                                                    fmt(row["firstTs"]),
                                                    fmt(row["lastTs"])))
        lines.append("")
        lines.append("Entries total: %s across %s batches; first ts %s, "
                     "last ts %s; entries without a ts field: %s."
                     % (exp["entriesTotal"], exp["batchCount"],
                        fmt(exp["firstTs"]), fmt(exp["lastTs"]),
                        exp["entriesWithoutTs"]))
    lines.append("")
    rounds = dash["rounds"]
    lines.append("## Rounds conversion (schema rocqwash-round/1)")
    lines.append("")
    if not dash["inputs"]["roundLedger"]["present"]:
        lines.append("Round ledger absent at its standing path %s: zero "
                     "rounds recorded (data, not an error)."
                     % dash["inputs"]["roundLedger"]["path"])
    elif rounds["roundsTotal"] == 0:
        lines.append("Round ledger present and empty: zero rounds recorded "
                     "(data, not an error).")
    else:
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        lines.append("| roundsTotal | %s |" % rounds["roundsTotal"])
        lines.append("| greenRounds (verify_rc = 0) | %s |"
                     % rounds["greenRounds"])
        lines.append("| greenPct | %s |" % fmt(rounds["greenPct"]))
        lines.append("| classesAppliedTotal | %s |"
                     % rounds["classesAppliedTotal"])
        lines.append("| admissionsTotal | %s |" % rounds["admissionsTotal"])
        lines.append("| classConversionPct | %s |"
                     % fmt(rounds["classConversionPct"]))
        modes = ", ".join("%s=%s" % (mode, count)
                          for mode, count in sorted(rounds["modes"].items()))
        lines.append("| modes | %s |" % (modes or "-"))
        lines.append("")
        lines.append("| Round | Mode | Classes applied | Admissions | "
                     "verify_rc |")
        lines.append("|---|---|---|---|---|")
        for row in rounds["perRound"]:
            lines.append("| %s | %s | %s | %s | %s |"
                         % (fmt(row["roundId"]), fmt(row["mode"]),
                            row["classesApplied"], row["admissions"],
                            fmt(row["verifyRc"])))
    lines.append("")
    coverage = dash["coverage"]
    lines.append("## Coverage lower-bound curve (vacgen v2 report faces)")
    lines.append("")
    if not dash["inputs"]["vacgenReports"]["present"]:
        lines.append("Report directory absent at its standing path %s: "
                     "zero runs recorded (data, not an error)."
                     % dash["inputs"]["vacgenReports"]["path"])
    elif coverage["reportRuns"] == 0:
        lines.append("Report directory present and empty: zero runs "
                     "recorded (data, not an error).")
    else:
        lines.append("| Order | Time point | Run | Shape | Files | "
                     "Recognized | Total | TODO-SEAT | Delta | "
                     "coverageLowerPct |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for idx, row in enumerate(coverage["curve"], 1):
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                         % (idx, fmt(row.get("ts")), fmt(row.get("runId")),
                            row["shape"], fmt(row.get("files")),
                            fmt(row.get("recognized")), fmt(row.get("total")),
                            fmt(row.get("todoSeats")),
                            fmt(row.get("todoSeatsDelta")),
                            fmt(row.get("coverageLowerPct"))))
        lines.append("")
        latest = coverage["latest"]
        lines.append("Thermometer reading (latest run %s): TODO-SEAT gaps "
                     "= %s, coverageLowerPct = %s."
                     % (fmt(latest.get("runId")), fmt(latest.get("todoSeats")),
                        fmt(latest.get("coverageLowerPct"))))
        if coverage["risingRuns"]:
            lines.append("Rise signal (data): TODO-SEAT count grew in run(s) "
                         "%s against the previous point in curve order."
                         % ", ".join(str(rid) for rid in coverage["risingRuns"]))
        else:
            lines.append("Rise signal (data): none; the TODO-SEAT count did "
                         "not grow at any step of the curve.")
    lines.append("")
    return "\n".join(lines)


def render_json(dash):
    """Render the JSON face: canonical deterministic form (sorted keys,
    indent 1, trailing newline)."""
    return json.dumps(dash, ensure_ascii=False, sort_keys=True,
                      indent=1) + "\n"


def summary_line(dash):
    """One-line stdout summary (always printed, both faces)."""
    exp = dash["experienceLedger"]
    rounds = dash["rounds"]
    coverage = dash["coverage"]
    exp_state = ("%d entries / %d batches" % (exp["entriesTotal"],
                                              exp["batchCount"])
                 if dash["inputs"]["experienceLedger"]["present"]
                 else "absent")
    rounds_state = ("%d rounds, green %s, class conversion %s"
                    % (rounds["roundsTotal"], fmt(rounds["greenPct"]),
                       fmt(rounds["classConversionPct"]))
                    if dash["inputs"]["roundLedger"]["present"]
                    else "absent")
    latest = coverage["latest"]
    runs_state = ("%d runs, latest TODO-SEAT %s, latest coverageLowerPct %s"
                  % (coverage["reportRuns"], fmt(latest.get("todoSeats")),
                     fmt(latest.get("coverageLowerPct")))
                  if coverage["reportRuns"] else "absent")
    return ("%s %s: experienceLedger=%s rounds=%s coverage=%s"
            % (PROG, SCHEMA, exp_state, rounds_state, runs_state))


def write_output(path, text, label):
    """Write one caller-named output file; a write failure is exit 9
    (fail loud, no partial face claimed)."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        raise DashboardInputError(
            "%s output directory does not exist: %s" % (label, parent))
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main(argv=None):
    """CLI entry; returns the process exit code (0/1/2/9 contract)."""
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="self-evolution dashboard over the experience ledger, "
                    "the round ledger, and vacgen v2 TODO-SEAT report faces")
    parser.add_argument("--repo", default=None, metavar="ROOT",
                        help="repository root (default: the parent of tools/)")
    parser.add_argument("--exp-ledger", default=None, metavar="P",
                        help="experience ledger path (default: "
                             "docs/exp-ledger.jsonl under the repo root; an "
                             "explicit path must exist)")
    parser.add_argument("--rounds", default=None, metavar="P",
                        help="round ledger path (default: "
                             "docs/round-ledger.jsonl under the repo root; "
                             "an explicit path must exist)")
    parser.add_argument("--reports", action="append", default=None,
                        metavar="P",
                        help="vacgen report file or directory (repeatable; "
                             "default: docs/vacgen-reports under the repo "
                             "root; an explicit path must exist)")
    parser.add_argument("--json-out", default=None, metavar="P",
                        help="write the JSON face to this file")
    parser.add_argument("--md-out", default=None, metavar="P",
                        help="write the markdown face to this file")
    parser.add_argument("--stdout", default="markdown",
                        choices=("markdown", "json"),
                        help="full face printed to stdout (default markdown)")
    parser.add_argument("--selftest", action="store_true",
                        help="frozen fixture vectors; zero writes outside "
                             "one temporary directory")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    repo = args.repo if args.repo else repo_root()
    try:
        exp_rows, round_rows, points, inputs = collect(
            repo, args.exp_ledger, args.rounds, args.reports)
        dash = build_dashboard(exp_rows, round_rows, points, inputs)
        json_face = render_json(dash)
        md_face = render_markdown(dash)
        if args.json_out:
            write_output(args.json_out, json_face, "json-out")
        if args.md_out:
            write_output(args.md_out, md_face, "md-out")
    except DashboardInputError as exc:
        sys.stderr.write("%s fail-loud: %s\n" % (PROG, exc))
        return 9
    # stdout carries bytes, not text: the newline translation of the
    # platform text layer would break the byte-identity between the
    # --stdout face and the --json-out / --md-out files.
    sys.stdout.buffer.write((summary_line(dash) + "\n"
                             + (json_face if args.stdout == "json"
                                else md_face)).encode("utf-8"))
    sys.stdout.buffer.flush()
    return 0


# ---------------------------------------------------------------- selftest --

def assert_true(condition, message):
    """Selftest assertion: a red vector raises immediately (exit 1)."""
    if not condition:
        raise AssertionError(message)


def seed(path, text):
    """Write one fixture file (parent dirs included)."""
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def exp_row(eid, ts, batch):
    """One rocqwash-exp/1 fixture entry (idempotent-shape keys only)."""
    return json.dumps({"schema": "rocqwash-exp/1", "id": eid, "ts": ts,
                       "tool": "fixture", "points": "p", "evidence": "e",
                       "batch": batch, "fingerprint": "f" * 64},
                      sort_keys=True)


def round_row(rid, mode, classes, admissions, verify_rc):
    """One rocqwash-round/1 fixture row (the ten contract keys)."""
    return json.dumps({"round_id": rid, "mode": mode,
                       "base_sha": "b" * 40, "head_sha": "h" * 40,
                       "classes_applied": classes, "admissions": admissions,
                       "files": ["x.py"], "verify_rc": verify_rc,
                       "oscillation_count": 0,
                       "timestamp_utc": "2026-11-15T00:00:0%dZ" % rid},
                      sort_keys=True)


def cast_report(run_id, ts, recognized, total, todo):
    """One vacgen cast-face report fixture."""
    return json.dumps({
        "reportId": run_id,
        "coverage": {"recognized": recognized, "todoSeats": todo,
                     "total": total, "coverageLowerPct": recognized * 100 // total,
                     "registeredAt": ts},
        "cast": {"files": 8, "todoSeatsByFile": {"witness.lean": todo}}},
        sort_keys=True)


def map_report(map_id, ts, files, recognized, total):
    """One vacgen preflight-map report fixture."""
    return json.dumps({
        "mapId": map_id, "generatedAt": ts,
        "aggregate": {"files": files, "recognized": recognized,
                      "assumptionsTotal": total,
                      "coverageLowerPct": recognized * 100 // total,
                      "tierCounts": {"A": 0, "B": 0, "C": 0, "D": files},
                      "unparsedCount": 0}},
        sort_keys=True)


def seed_repo(root, with_data=True):
    """Seed one fixture repository (the three standing accounts)."""
    docs = os.path.join(root, "docs")
    reports = os.path.join(docs, "vacgen-reports")
    if not with_data:
        return docs, reports
    seed(os.path.join(docs, "exp-ledger.jsonl"), "\n".join([
        exp_row("E-1", "2026-11-13T10:00:00Z", "batch-a"),
        exp_row("E-2", "2026-11-14T10:00:00Z", "batch-a"),
        exp_row("E-3", "2026-11-15T10:00:00Z", "batch-b"),
    ]) + "\n")
    seed(os.path.join(docs, "round-ledger.jsonl"), "\n".join([
        round_row(1, "auto", ["c1", "c2", "c3"],
                  [{"class": "c1"}, {"class": "c2"}], 0),
        round_row(2, "auto", ["c4"], [{"class": "c4"}], 1),
        round_row(3, "rollback", [], [], 0),
    ]) + "\n")
    seed(os.path.join(reports, "r1-cast.json"),
         cast_report("vacgenv2-fix-001", "2026-11-14T01:00:00Z", 3, 5, 2)
         + "\n")
    seed(os.path.join(reports, "r2-map.json"),
         map_report("vacgenv2-preflight-002", "2026-11-15T01:00:00Z",
                    9, 6, 12) + "\n")
    return docs, reports


def selftest():
    """Frozen fixture vectors; returns 0 green / 1 red (fail loud)."""
    tmp = tempfile.mkdtemp(prefix="evolution_dashboard_selftest_")
    fails = []
    try:
        # V1 happy path: three sources with conversion math, curve order,
        # delta, and the rise flag all asserted on the dashboard document.
        repo1 = os.path.join(tmp, "repo1")
        seed_repo(repo1)
        exp_rows, round_rows, points, inputs = collect(repo1, None, None, None)
        dash = build_dashboard(exp_rows, round_rows, points, inputs)
        assert_true(dash["experienceLedger"]["entriesTotal"] == 3, "V1 exp total")
        assert_true(dash["experienceLedger"]["batchCount"] == 2, "V1 batches")
        assert_true(dash["experienceLedger"]["lastTs"]
                    == "2026-11-15T10:00:00Z", "V1 last ts")
        rounds = dash["rounds"]
        assert_true(rounds["roundsTotal"] == 3, "V1 rounds total")
        assert_true(rounds["greenRounds"] == 2 and rounds["greenPct"] == 66,
                    "V1 green face: %r" % rounds)
        assert_true(rounds["classesAppliedTotal"] == 4, "V1 applied total")
        assert_true(rounds["admissionsTotal"] == 3, "V1 admissions total")
        assert_true(rounds["classConversionPct"] == 75, "V1 conversion: %r"
                    % rounds)
        coverage = dash["coverage"]
        assert_true(coverage["reportRuns"] == 2, "V1 runs")
        curve = coverage["curve"]
        assert_true([row["runId"] for row in curve]
                    == ["vacgenv2-fix-001", "vacgenv2-preflight-002"],
                    "V1 curve order: %r" % [row["runId"] for row in curve])
        assert_true(curve[0]["todoSeats"] == 2 and curve[1]["todoSeats"] == 6,
                    "V1 todo seats")
        assert_true(curve[1]["todoSeatsDelta"] == 4 and curve[1]["rising"],
                    "V1 delta/rise: %r" % curve[1])
        assert_true(coverage["risingRuns"] == ["vacgenv2-preflight-002"],
                    "V1 rising runs")
        assert_true(coverage["latest"]["runId"] == "vacgenv2-preflight-002",
                    "V1 latest")

        # V2 determinism: both faces byte-identical across two runs.
        md1 = render_markdown(dash)
        js1 = render_json(dash)
        exp_rows, round_rows, points, inputs = collect(repo1, None, None, None)
        dash2 = build_dashboard(exp_rows, round_rows, points, inputs)
        assert_true(render_markdown(dash2) == md1, "V2 md bytes drift")
        assert_true(render_json(dash2) == js1, "V2 json bytes drift")

        # V3 CLI faces: --stdout json equals --json-out bytes; md-out
        # written; summary line printed; exit 0.
        out_json = os.path.join(tmp, "o1", "dash.json")
        out_md = os.path.join(tmp, "o1", "dash.md")
        os.makedirs(os.path.dirname(out_json), exist_ok=True)
        code = main(["--repo", repo1, "--json-out", out_json,
                     "--md-out", out_md, "--stdout", "json"])
        assert_true(code == 0, "V3 exit code")
        with open(out_json, "r", encoding="utf-8") as handle:
            assert_true(handle.read() == js1, "V3 json-out == stdout json")
        with open(out_md, "r", encoding="utf-8") as handle:
            md_text = handle.read()
        assert_true(md_text == md1, "V3 md-out == stdout markdown")
        assert_true(md_text.startswith(MD_TITLE), "V3 md title face")

        # V4 absent defaults are data: a bare repo runs exit 0 with every
        # source marked absent and zero counts.
        repo2 = os.path.join(tmp, "repo2")
        os.makedirs(repo2, exist_ok=True)
        code = main(["--repo", repo2])
        assert_true(code == 0, "V4 absent-defaults exit 0")

        # V5 explicit absent paths exit 9 with zero writes; corrupt lines
        # and faceless reports likewise; nothing lands in the output dir.
        out_guard = os.path.join(tmp, "o2", "never.json")
        absent = os.path.join(tmp, "absent.json")
        code = main(["--repo", repo1, "--rounds", absent,
                     "--json-out", out_guard])
        assert_true(code == 9, "V5 explicit absent exit 9")
        assert_true(not os.path.exists(out_guard), "V5 zero writes on 9")
        code = main(["--repo", repo1, "--reports", absent])
        assert_true(code == 9, "V5 explicit absent reports exit 9")
        docs_bad = os.path.join(tmp, "repo3", "docs")
        seed(os.path.join(docs_bad, "exp-ledger.jsonl"),
             exp_row("E-1", "2026-11-13T10:00:00Z", "b") + "\nnot-json{\n")
        code = main(["--repo", os.path.join(tmp, "repo3")])
        assert_true(code == 9, "V5 corrupt ledger line exit 9")
        bad_dir = os.path.join(tmp, "repo4", "docs", "vacgen-reports")
        seed(os.path.join(bad_dir, "faceless.json"),
             json.dumps({"nothing": True}) + "\n")
        code = main(["--repo", os.path.join(tmp, "repo4")])
        assert_true(code == 9, "V5 faceless report exit 9")
        code = main(["--repo", repo1, "--json-out",
                     os.path.join(tmp, "missing-dir", "dash.json")])
        assert_true(code == 9, "V5 missing output dir exit 9")

        # V6 usage face: a bad --stdout choice exits 2 (argparse face).
        try:
            main(["--repo", repo1, "--stdout", "bogus"])
            code2 = 0
        except SystemExit as exc:
            code2 = exc.code
        assert_true(code2 == 2, "V6 bad --stdout exits 2, got %r" % code2)

        # V7 rise-then-fall thermometer: a third report dropping the gap
        # count flips the rise flag off and moves the reading.
        docs1 = os.path.join(repo1, "docs", "vacgen-reports")
        seed(os.path.join(docs1, "r3-cast.json"),
             cast_report("vacgenv2-fix-003", "2026-11-16T01:00:00Z", 5, 5, 0)
             + "\n")
        exp_rows, round_rows, points, inputs = collect(repo1, None, None, None)
        dash3 = build_dashboard(exp_rows, round_rows, points, inputs)
        cov3 = dash3["coverage"]
        assert_true(cov3["reportRuns"] == 3, "V7 runs")
        assert_true(cov3["latest"]["todoSeats"] == 0, "V7 latest reading")
        assert_true(cov3["latest"]["todoSeatsDelta"] == -6, "V7 fall delta")
        assert_true(not cov3["latest"]["rising"], "V7 latest point not rising")
        assert_true(cov3["risingRuns"] == ["vacgenv2-preflight-002"],
                    "V7 historical rise kept as data: %r" % cov3["risingRuns"])
        assert_true(cov3["curve"][1]["rising"], "V7 earlier rise kept as data")

        # V8 markdown absent faces are stated loudly (no silent zero).
        md_absent = render_markdown(build_dashboard([], [], [], {
            "experienceLedger": {"path": default_path(EXP_DEFAULT),
                                 "present": False},
            "roundLedger": {"path": default_path(ROUNDS_DEFAULT),
                            "present": False},
            "vacgenReports": {"path": default_path(REPORTS_DEFAULT),
                              "present": False}}))
        assert_true("absent" in md_absent, "V8 absent stated")
        assert_true("data, not an error" in md_absent, "V8 data statement")
    except AssertionError as exc:
        fails.append(str(exc))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        for line in fails:
            sys.stderr.write("EVOLUTION-DASHBOARD SELFTEST FAIL %s\n" % line)
        return 1
    sys.stdout.write("EVOLUTION-DASHBOARD SELFTEST PASS (8 vectors)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
