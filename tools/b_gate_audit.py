#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""b_gate_audit.py - measure the B-level generalization gate from round records.
Purpose.  The B threshold needs at least three instances, each backed by one
  applied round; a single-instance generalization is a false generalization.
  An instance is one admission of a class in one round (same-round duplicates
  collapse); rounds count distinct admitting rounds.  Each round-state
  admitted_classes entry is one instance record, deduplicated by class: a
  class counted from ledger rounds keeps those counts; a class with no
  admitting ledger round counts one instance and one round; zero-admission
  classes report instances=0.  A class is ready when instances >= 3 and
  rounds >= 1; the verdict is ready when at least 3 classes are ready.

Interface.  python3 tools/b_gate_audit.py [--selftest].  The default run
  reads the round ledger, round state and taxonomy files read-only, writes
  docs/b-gate-audit.json (schema rocqwash.b-gate-audit/1, sorted keys,
  deterministic) and prints a summary with a per-class near-ready gap
  report; --selftest is offline on tempfiles.

Exit-codes.  0 audit completed (an honest not-ready verdict is data, not a
  failure); 1 read errors only (missing file, corrupt line or malformed
  entry, each in the "errors" field, fail-loud, audit continues); 2 usage.

Dependencies.  Python 3 standard library only; zero network; no I/O on import.

Evidence.  Vectors on temporary files: gate reached (three classes x three
  rounds, duplicate entry collapses), single instance (exact gap text; the
  state mirror does not inflate the count), empty records (remaining_to_b
  3), a state-only class (one instance and one round), corrupt lines (valid
  row counted, 4 ledger errors + 2 missing files), near-ready gap rows (one
  per not-ready class), the exit-code mapping, and the writer round-trip.
"""

import argparse
import contextlib
import io
import json
import os
import sys
import tempfile

SCHEMA = "rocqwash.b-gate-audit/1"
THRESHOLD_INSTANCES = 3
THRESHOLD_ROUNDS = 1
READY_CLASSES_NEEDED = 3
DEFAULT_LEDGER = os.path.join("docs", "round-ledger.jsonl")
DEFAULT_STATE = os.path.join("docs", "round-state.json")
DEFAULT_TAXONOMY = os.path.join("tools", "taxonomy.json")
DEFAULT_OUT = os.path.join("docs", "b-gate-audit.json")


def _read_json_object(path, label, errors):
    """Read one JSON object file; on failure record an error and return None."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        errors.append("%s: cannot read %s: %s" % (label, path, exc))
        return None
    except ValueError as exc:
        errors.append("%s: invalid JSON in %s: %s" % (label, path, exc))
        return None
    if not isinstance(data, dict):
        errors.append("%s: %s is not a JSON object" % (label, path))
        return None
    return data


def collect_ledger_admissions(path, errors):
    """Parse the round ledger into (admitted, sources).

    admitted maps class_name to the set of distinct admitting round ids;
    sources maps class_name to one pointer per admitting ledger row, in
    file order ("round-ledger line N (round_id R)").  Every unreadable
    line or malformed entry records one error and the parse continues
    with the remaining lines; nothing is dropped silently.
    """
    admitted = {}
    sources = {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError as exc:
        errors.append("round-ledger: cannot read %s: %s" % (path, exc))
        return admitted
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            errors.append("round-ledger line %d: invalid JSON: %s" % (lineno, exc))
            continue
        if not isinstance(row, dict):
            errors.append("round-ledger line %d: not a JSON object" % lineno)
            continue
        round_id = row.get("round_id")
        if isinstance(round_id, bool) or not isinstance(round_id, (str, int)):
            errors.append(
                "round-ledger line %d: missing or invalid round_id" % lineno)
            continue
        admissions = row.get("admissions")
        if not isinstance(admissions, list):
            errors.append(
                "round-ledger line %d: missing or invalid admissions list" % lineno)
            continue
        for idx, entry in enumerate(admissions):
            if not isinstance(entry, dict):
                errors.append(
                    "round-ledger line %d: admission %d is not an object"
                    % (lineno, idx))
                continue
            class_name = entry.get("class")
            if not isinstance(class_name, str) or not class_name:
                errors.append(
                    "round-ledger line %d: admission %d has no class"
                    % (lineno, idx))
                continue
            decision = entry.get("decision")
            if not isinstance(decision, str) or not decision:
                errors.append(
                    "round-ledger line %d: admission %d has no decision"
                    % (lineno, idx))
                continue
            if decision != "admitted":
                continue
            rounds = admitted.setdefault(class_name, set())
            if round_id in rounds:
                continue
            rounds.add(round_id)
            sources.setdefault(class_name, []).append(
                "round-ledger line %d (round_id %s)" % (lineno, round_id))
    return admitted, sources


def collect_state_classes(data, errors):
    """Collect class names from the round state admitted_classes list.

    Returns (classes, sources); sources maps each class to its first
    admitting entry pointer ("round-state admitted_classes[i]").
    """
    classes = set()
    sources = {}
    if data is None:
        return classes, sources
    admitted = data.get("admitted_classes")
    if not isinstance(admitted, list):
        errors.append("round-state: missing or invalid admitted_classes list")
        return classes
    for idx, entry in enumerate(admitted):
        if not isinstance(entry, dict):
            errors.append(
                "round-state: admitted_classes entry %d is not an object" % idx)
            continue
        name = entry.get("class")
        if not isinstance(name, str) or not name:
            errors.append(
                "round-state: admitted_classes entry %d has no class" % idx)
            continue
        if name in classes:
            continue
        classes.add(name)
        sources[name] = "round-state admitted_classes[%d]" % idx
    return classes, sources


def collect_taxonomy_classes(data, errors):
    """Collect family ids from the taxonomy table rows.

    Returns (classes, sources); sources maps each family to its first
    row pointer ("taxonomy rows[i]").
    """
    classes = set()
    sources = {}
    if data is None:
        return classes, sources
    rows = data.get("rows")
    if not isinstance(rows, list):
        errors.append("taxonomy: missing or invalid rows list")
        return classes
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append("taxonomy: row %d is not an object" % idx)
            continue
        family = row.get("familyId")
        if not isinstance(family, str) or not family:
            errors.append("taxonomy: row %d has no familyId" % idx)
            continue
        if family in classes:
            continue
        classes.add(family)
        sources[family] = "taxonomy rows[%d]" % idx
    return classes, sources


def gap_message(instances):
    """Gap text for a class below the instance threshold."""
    missing = THRESHOLD_INSTANCES - instances
    if missing == 1:
        return "needs 1 more instance with a round each"
    return "needs %d more instances with a round each" % missing


def near_ready_delta(instances):
    """Actionable delta sentence for a class below the instance threshold."""
    missing = THRESHOLD_INSTANCES - instances
    if missing == 1:
        return ("admit this class in 1 more round, one admission each, to"
                " reach %d instances" % THRESHOLD_INSTANCES)
    return ("admit this class in %d more rounds, one admission each, to"
            " reach %d instances" % (missing, THRESHOLD_INSTANCES))


def build_report(ledger_path, state_path, taxonomy_path):
    """Build the audit report (with per-class near-ready rows).

    Returns (report, errors)."""
    errors = []
    admitted, ledger_sources = collect_ledger_admissions(
        ledger_path, errors)
    state = _read_json_object(state_path, "round-state", errors)
    taxonomy = _read_json_object(taxonomy_path, "taxonomy", errors)
    state_classes, state_sources = collect_state_classes(state, errors)
    taxonomy_classes, taxonomy_sources = collect_taxonomy_classes(
        taxonomy, errors)
    universe = set(admitted)
    universe |= state_classes
    universe |= taxonomy_classes
    classes = []
    ready_classes = []
    for name in sorted(universe):
        ledger_rounds = admitted.get(name, set())
        if ledger_rounds:
            instances = len(ledger_rounds)
            n_rounds = len(ledger_rounds)
        elif name in state_classes:
            # A state-only admission (no admitting ledger round) is one
            # grounded instance and one round; a class already counted from
            # ledger rounds keeps those counts (deduplicated by class).
            instances = 1
            n_rounds = 1
        else:
            instances = 0
            n_rounds = 0
        ready = instances >= THRESHOLD_INSTANCES and n_rounds >= THRESHOLD_ROUNDS
        classes.append({
            "class": name,
            "instances": instances,
            "rounds": n_rounds,
            "ready": ready,
            "gap": None if ready else gap_message(instances),
        })
        if ready:
            ready_classes.append(name)
    remaining = max(0, READY_CLASSES_NEEDED - len(ready_classes))
    near_ready = []
    for row in classes:
        if row["ready"]:
            continue
        name = row["class"]
        if ledger_sources.get(name):
            pointers = list(ledger_sources[name])
        elif name in state_sources:
            pointers = [state_sources[name]]
        elif name in taxonomy_sources:
            pointers = [taxonomy_sources[name]]
        else:
            pointers = ["no grounding record"]
        near_ready.append({
            "class": name,
            "instances": row["instances"],
            "rounds": row["rounds"],
            "instances_delta": THRESHOLD_INSTANCES - row["instances"],
            "sources": pointers,
            "delta": near_ready_delta(row["instances"]),
        })
    report = {
        "schema": SCHEMA,
        "threshold": {
            "instances": THRESHOLD_INSTANCES,
            "rounds_per_instance": THRESHOLD_ROUNDS,
        },
        "classes": classes,
        "ready_classes": ready_classes,
        "verdict": "ready" if remaining == 0 else "not-ready",
        "remaining_to_b": remaining,
        "near_ready": near_ready,
        "errors": errors,
    }
    return report, errors


def exit_code(report):
    """Map a report to the process exit code: 1 on read errors, else 0."""
    return 1 if report["errors"] else 0


def write_report(report, out_path):
    """Write the report as deterministic JSON with a trailing newline."""
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def print_summary(report, out_path):
    """Print the human-readable audit summary."""
    print("b-gate audit: schema %s" % SCHEMA)
    print(
        "threshold: %d instances and %d round(s) per class;"
        " verdict ready needs %d ready classes"
        % (THRESHOLD_INSTANCES, THRESHOLD_ROUNDS, READY_CLASSES_NEEDED))
    for row in report["classes"]:
        mark = "ready" if row["ready"] else "not-ready"
        line = "class %s: instances=%d rounds=%d %s" % (
            row["class"], row["instances"], row["rounds"], mark)
        if row["gap"]:
            line += " (%s)" % row["gap"]
        print(line)
    print("near-ready gap report:")
    if report["near_ready"]:
        for row in report["near_ready"]:
            print(
                "near-ready %s: instances=%d rounds=%d instances_delta=%d"
                " sources=%s delta=%s"
                % (row["class"], row["instances"], row["rounds"],
                   row["instances_delta"], "; ".join(row["sources"]),
                   row["delta"]))
    else:
        print("near-ready gap: none (no not-ready class)")
    print("verdict: %s" % report["verdict"])
    print("ready classes: %d of %d needed"
          % (len(report["ready_classes"]), READY_CLASSES_NEEDED))
    print("remaining_to_b: %d" % report["remaining_to_b"])
    print("errors: %d" % len(report["errors"]))
    for err in report["errors"]:
        print("error: %s" % err)
    print("report written: %s" % out_path.replace(os.sep, "/"))


def _write_temp(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _run_vector(base, name, ledger_text, state_obj, taxonomy_obj):
    """Write one vector's inputs under base and build the report."""
    vec_dir = os.path.join(base, name)
    os.makedirs(vec_dir)
    ledger = os.path.join(vec_dir, "ledger.jsonl")
    state = os.path.join(vec_dir, "state.json")
    taxonomy = os.path.join(vec_dir, "taxonomy.json")
    _write_temp(ledger, ledger_text)
    _write_temp(state, json.dumps(state_obj, sort_keys=True))
    _write_temp(taxonomy, json.dumps(taxonomy_obj, sort_keys=True))
    report, errors = build_report(ledger, state, taxonomy)
    return report, errors


def selftest():
    """Run the offline vectors; return 0 when all pass, else 1."""
    failures = []
    with tempfile.TemporaryDirectory(prefix="b_gate_audit_selftest_") as tmp:
        # Vector 1: gate reached - three classes, three rounds each, one
        # duplicate admission entry inside round 1 that must collapse.
        rows = []
        for rid in (1, 2, 3):
            entries = [{"class": "alpha", "decision": "admitted"}]
            if rid == 1:
                entries.append({"class": "alpha", "decision": "admitted"})
            entries.append({"class": "beta", "decision": "admitted"})
            entries.append({"class": "gamma", "decision": "admitted"})
            rows.append(json.dumps(
                {"round_id": rid, "admissions": entries}, sort_keys=True))
        report, errors = _run_vector(
            tmp, "v1_gate_reached", "\n".join(rows) + "\n",
            {"schema": "rocqwash.round-state/1", "admitted_classes": [
                {"class": "alpha"}, {"class": "beta"}, {"class": "gamma"}]},
            {"rows": [{"familyId": "alpha"}, {"familyId": "beta"},
                      {"familyId": "gamma"}]})
        if errors:
            failures.append("v1: unexpected errors: %r" % (errors,))
        by_name = {row["class"]: row for row in report["classes"]}
        for cls in ("alpha", "beta", "gamma"):
            row = by_name.get(cls)
            if row is None:
                failures.append("v1: class %s missing" % cls)
                continue
            if row["instances"] != 3 or row["rounds"] != 3 or not row["ready"]:
                failures.append("v1: class %s wrong row %r" % (cls, row))
        if report["verdict"] != "ready":
            failures.append("v1: verdict %r != ready" % report["verdict"])
        if report["remaining_to_b"] != 0:
            failures.append(
                "v1: remaining_to_b %r != 0" % report["remaining_to_b"])
        if report["ready_classes"] != ["alpha", "beta", "gamma"]:
            failures.append(
                "v1: ready_classes %r wrong" % (report["ready_classes"],))

        # Vector 2: single-instance class - one round, one admission; the
        # class also sits in round-state, and the mirror entry must not
        # inflate the ledger count (dedupe by class).
        line = json.dumps(
            {"round_id": 1,
             "admissions": [{"class": "solo", "decision": "admitted"}]},
            sort_keys=True)
        report, errors = _run_vector(
            tmp, "v2_single_instance", line + "\n",
            {"schema": "rocqwash.round-state/1",
             "admitted_classes": [{"class": "solo"}]},
            {"rows": []})
        if errors:
            failures.append("v2: unexpected errors: %r" % (errors,))
        if len(report["classes"]) != 1:
            failures.append("v2: expected one class row")
        else:
            row = report["classes"][0]
            expected = {"class": "solo", "instances": 1, "rounds": 1,
                        "ready": False,
                        "gap": "needs 2 more instances with a round each"}
            if row != expected:
                failures.append("v2: row %r != %r" % (row, expected))
        if report["verdict"] != "not-ready":
            failures.append("v2: verdict %r != not-ready" % report["verdict"])
        if report["remaining_to_b"] != 3:
            failures.append(
                "v2: remaining_to_b %r != 3" % report["remaining_to_b"])

        # Vector 3: empty records - verdict not-ready, remaining 3, no padding.
        report, errors = _run_vector(
            tmp, "v3_empty", "",
            {"schema": "rocqwash.round-state/1", "admitted_classes": []},
            {"rows": []})
        if errors:
            failures.append("v3: unexpected errors: %r" % (errors,))
        if report["classes"] != []:
            failures.append("v3: classes %r != []" % (report["classes"],))
        if report["verdict"] != "not-ready":
            failures.append("v3: verdict %r != not-ready" % report["verdict"])
        if report["remaining_to_b"] != 3:
            failures.append(
                "v3: remaining_to_b %r != 3" % report["remaining_to_b"])

        # Vector 4: corrupt lines - the valid row still counts, every
        # malformed face surfaces as one error, nothing drops silently.
        v4_dir = os.path.join(tmp, "v4_corrupt")
        os.makedirs(v4_dir)
        good = json.dumps(
            {"round_id": 1,
             "admissions": [{"class": "keep", "decision": "admitted"}]},
            sort_keys=True)
        _write_temp(
            os.path.join(v4_dir, "ledger.jsonl"),
            good + "\n"
            + "{not json\n"
            + json.dumps({"round_id": 3}, sort_keys=True) + "\n"
            + json.dumps({"round_id": 4,
                          "admissions": [{"decision": "admitted"}]},
                         sort_keys=True) + "\n"
            + json.dumps({"round_id": 5,
                          "admissions": [{"class": "x"}]},
                         sort_keys=True) + "\n")
        v4_report, v4_errors = build_report(
            os.path.join(v4_dir, "ledger.jsonl"),
            os.path.join(v4_dir, "missing_state.json"),
            os.path.join(v4_dir, "missing_taxonomy.json"))
        by_name = {row["class"]: row for row in v4_report["classes"]}
        keep = by_name.get("keep")
        if keep is None or keep["instances"] != 1:
            failures.append("v4: valid row not counted: %r" % (keep,))
        if len(v4_errors) != 6:
            failures.append(
                "v4: expected 6 errors (4 ledger + 2 missing files), got %d: %r"
                % (len(v4_errors), v4_errors))
        if v4_report["verdict"] != "not-ready":
            failures.append("v4: verdict %r != not-ready" % v4_report["verdict"])

        # Vector 5: state-only class - admitted through round-state only
        # (no admitting ledger round); one instance and one round.  This is
        # the recorded false negative of ledger-only counting.
        report, errors = _run_vector(
            tmp, "v5_state_only", "",
            {"schema": "rocqwash.round-state/1",
             "admitted_classes": [{"class": "state-only"}]},
            {"rows": []})
        if errors:
            failures.append("v5: unexpected errors: %r" % (errors,))
        if len(report["classes"]) != 1:
            failures.append("v5: expected one class row")
        else:
            row = report["classes"][0]
            expected = {"class": "state-only", "instances": 1, "rounds": 1,
                        "ready": False,
                        "gap": "needs 2 more instances with a round each"}
            if row != expected:
                failures.append("v5: row %r != %r" % (row, expected))
        if report["verdict"] != "not-ready":
            failures.append("v5: verdict %r != not-ready" % report["verdict"])

        # Vector 6: near-ready gap face - two not-ready classes (one
        # taxonomy-only at zero instances, one ledger-grounded at two
        # instances) and one ready class; each not-ready class reports one
        # near-ready row (counts, instance delta, source rows, actionable
        # delta), and the ready class is absent from the report.  The
        # printed summary face carries one line per not-ready class.
        rows6 = []
        for rid in (1, 2, 3):
            entries = [{"class": "gamma", "decision": "admitted"}]
            if rid < 3:
                entries.append({"class": "beta", "decision": "admitted"})
            rows6.append(json.dumps(
                {"round_id": rid, "admissions": entries}, sort_keys=True))
        report, errors = _run_vector(
            tmp, "v6_near_ready", "\n".join(rows6) + "\n",
            {"schema": "rocqwash.round-state/1", "admitted_classes": []},
            {"rows": [{"familyId": "alpha"}, {"familyId": "beta"},
                      {"familyId": "gamma"}]})
        if errors:
            failures.append("v6: unexpected errors: %r" % (errors,))
        expected_near = [
            {"class": "alpha", "instances": 0, "rounds": 0,
             "instances_delta": 3,
             "sources": ["taxonomy rows[0]"],
             "delta": "admit this class in 3 more rounds, one admission"
                      " each, to reach 3 instances"},
            {"class": "beta", "instances": 2, "rounds": 2,
             "instances_delta": 1,
             "sources": ["round-ledger line 1 (round_id 1)",
                         "round-ledger line 2 (round_id 2)"],
             "delta": "admit this class in 1 more round, one admission"
                      " each, to reach 3 instances"},
        ]
        if report["near_ready"] != expected_near:
            failures.append(
                "v6: near_ready %r != %r"
                % (report["near_ready"], expected_near))
        if report["verdict"] != "not-ready":
            failures.append("v6: verdict %r != not-ready" % report["verdict"])
        if report["remaining_to_b"] != 2:
            failures.append(
                "v6: remaining_to_b %r != 2" % report["remaining_to_b"])
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            print_summary(report, "unused.json")
        near_lines = [
            line for line in captured.getvalue().splitlines()
            if line.startswith("near-ready")]
        expected_lines = [
            "near-ready gap report:",
            "near-ready alpha: instances=0 rounds=0 instances_delta=3"
            " sources=taxonomy rows[0] delta=admit this class in 3 more"
            " rounds, one admission each, to reach 3 instances",
            "near-ready beta: instances=2 rounds=2 instances_delta=1"
            " sources=round-ledger line 1 (round_id 1); round-ledger"
            " line 2 (round_id 2) delta=admit this class in 1 more"
            " round, one admission each, to reach 3 instances",
        ]
        if near_lines != expected_lines:
            failures.append(
                "v6: summary lines %r != %r" % (near_lines, expected_lines))

        # Exit-code mapping: a clean audit exits 0 even when the verdict is
        # not-ready (the verdict is data, not a failure); any read error
        # exits 1; an unknown flag exits 2 through the usage parser.
        clean_report, clean_errors = build_report(
            os.path.join(tmp, "v3_empty", "ledger.jsonl"),
            os.path.join(tmp, "v3_empty", "state.json"),
            os.path.join(tmp, "v3_empty", "taxonomy.json"))
        if clean_errors or exit_code(clean_report) != 0:
            failures.append(
                "exit map: clean run must exit 0, got %r (errors %r)"
                % (exit_code(clean_report), clean_errors))
        if exit_code(v4_report) != 1:
            failures.append(
                "exit map: read-error run must exit 1, got %r"
                % (exit_code(v4_report),))
        captured = io.StringIO()
        usage_code = None
        try:
            with contextlib.redirect_stderr(captured):
                main(["--no-such-flag"])
        except SystemExit as exc:
            usage_code = exc.code
        if usage_code != 2:
            failures.append(
                "exit map: unknown flag exit %r != 2" % (usage_code,))

        # The writer round-trips through the report file.
        out_path = os.path.join(tmp, "report.json")
        probe, _ = build_report(
            os.path.join(tmp, "v3_empty", "ledger.jsonl"),
            os.path.join(tmp, "v3_empty", "state.json"),
            os.path.join(tmp, "v3_empty", "taxonomy.json"))
        write_report(probe, out_path)
        with open(out_path, "r", encoding="utf-8") as handle:
            reloaded = json.load(handle)
        if reloaded != probe:
            failures.append("writer: reloaded report differs from built report")
        if reloaded.get("schema") != SCHEMA:
            failures.append("writer: schema %r != %r" % (
                reloaded.get("schema"), SCHEMA))

    if failures:
        for item in failures:
            print("selftest FAIL: %s" % item)
        print("selftest: %d failure(s)" % len(failures))
        return 1
    print("selftest: vectors passed (gate reached, single instance,"
          " empty records, state-only class, corrupt lines, near-ready"
          " gap report, exit-code mapping, writer round-trip)")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="b_gate_audit.py",
        description=(
            "Measure the B-level generalization gate from round records"
            " and write docs/b-gate-audit.json."))
    parser.add_argument(
        "--selftest", action="store_true",
        help="run the offline vectors on temporary files and exit")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    report, _ = build_report(DEFAULT_LEDGER, DEFAULT_STATE, DEFAULT_TAXONOMY)
    print_summary(report, DEFAULT_OUT)
    write_report(report, DEFAULT_OUT)
    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main())
