#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/refinery_segments/calib.py -- P2-5 calibration-lane segment.

Purpose.  Contract-test the W4 calibration face end to end: the calibration
  ledger tool's own fixture vectors, rerun idempotence (zero new rows on the
  same report and rc face), the carried correlationId, append-only ledger
  growth, the row-rot signal face (signals are data; --strict exits 4),
  declared red-leg semantics, the CLI usage face, and the correlationId
  wiring added to the experience-bus port (append, skip, zero regression).

Interface.  `run_segment_calibration()` returns (passed, failed, skipped,
  results) with results rows shaped (status, check_name, detail), statuses
  in {PASS, FAIL, SKIP}; importing this module spawns nothing (import-safe).
  Running the file directly executes the segment and prints SEGMENT,
  SUMMARY and TOTAL lines in the refinery merge contract shape.

Dependencies.  Python 3 standard library only; every vector runs the tools
  in a subprocess with temporary fixtures (no repository write, no network);
  the two inspected tools are stdlib-only.

Evidence.  Each check runs a command on this machine and asserts its exit
  code and output face; the ledger bytes are compared read-back, never
  inferred from stdout alone.

Exit-codes.  0 all checks green (zero FAIL); 1 at least one FAIL (each
  printed, fail loud); SKIP lines name their missing surface and never
  count as passes.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CALIB_TOOL = os.path.join(REPO, "tools", "calibration_ledger.py")
PORT_TOOL = os.path.join(REPO, "tools", "exp_port.py")
MARK = "CALIBRATION-LEDGER-SELFTEST PASS"
PORT_MARK = "EXP-PORT-SELFTEST PASS"


def run_tool(tool, args):
    """Run one inspected tool in a subprocess (stdout+stderr merged)."""
    proc = subprocess.run(
        [sys.executable, "-B", "-I", "-X", "utf8", tool] + list(args),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", errors="replace")


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def read_ledger_rows(path):
    with open(path, "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def check(results, name, thunk):
    """One check: the thunk returns a detail line or raises on red."""
    try:
        detail = thunk()
    except AssertionError as exc:
        results.append(("FAIL", name, str(exc)))
    except Exception as exc:  # loud: a non-assert crash is a FAIL, not a SKIP
        results.append(("FAIL", name, "%s: %s" % (type(exc).__name__, exc)))
    else:
        results.append(("PASS", name, detail))


def _fixture(tmp, rc_value, expected):
    """Write the shared two-prediction report and a one-leg rc face."""
    report = os.path.join(tmp, "report.json")
    rcs = os.path.join(tmp, "rcs.json")
    write_json(report, {"reportId": "vacgenv2-segcast-0000",
                        "assumptions": [
                            {"kind": "assumption", "name": "h1",
                             "status": "recognized",
                             "familyId": "fam.one", "confidence": "HIGH"},
                            {"kind": "assumption", "name": "h2",
                             "status": "todo_seat", "familyId": None,
                             "confidence": None},
                        ]})
    write_json(rcs, {"witness.lean": {"rc": rc_value, "expected": expected}})
    return report, rcs


def _seg_selftest(results):
    def thunk():
        rc, out = run_tool(CALIB_TOOL, ["--selftest"])
        assert_true(rc == 0 and MARK in out,
                    "--selftest should be rc=0 with the marker (rc=%d)\n%s"
                    % (rc, out))
        return "tool fixture vector group green (12 vectors)"
    check(results, "tool-selftest", thunk)


def _seg_r7_idempotence(results):
    def thunk():
        tmp = tempfile.mkdtemp(prefix="calib_seg_r7_")
        try:
            report, rcs = _fixture(tmp, 0, "green")
            ledger = os.path.join(tmp, "exp-ledger.jsonl")
            args = ["--report", report, "--rc-file", rcs, "--ledger", ledger]
            rc1, out1 = run_tool(CALIB_TOOL, args)
            assert_true(rc1 == 0 and out1.count("appended id=") == 1,
                        "first run should append 1 row rc=0 (rc=%d)\n%s"
                        % (rc1, out1))
            before = open(ledger, "rb").read()
            rc2, out2 = run_tool(CALIB_TOOL, args)
            assert_true(rc2 == 0 and out2.count("duplicate-skip id=") == 1,
                        "rerun should skip rc=0 (rc=%d)\n%s" % (rc2, out2))
            assert_true("appended id=" not in out2,
                        "rerun must not append a new row\n%s" % out2)
            assert_true(open(ledger, "rb").read() == before,
                        "rerun must leave the ledger bytes unchanged (R7)")
            return "rerun zero new rows, ledger bytes hold (R7 face)"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    check(results, "r7-idempotence", thunk)


def _seg_correlation_and_append_only(results):
    def thunk():
        tmp = tempfile.mkdtemp(prefix="calib_seg_corr_")
        try:
            report, rcs = _fixture(tmp, 0, "green")
            ledger = os.path.join(tmp, "exp-ledger.jsonl")
            with open(ledger, "w", encoding="utf-8") as handle:
                handle.write('{"batch":"pre","fingerprint":"pf","id":"PRE-1",'
                             '"points":"pp","schema":"rocqwash-exp/1",'
                             '"tool":"pt"}\n')
            pre_head = open(ledger, "rb").read()
            rc, out = run_tool(CALIB_TOOL, ["--report", report, "--rc-file",
                                            rcs, "--ledger", ledger])
            assert_true(rc == 0, "append should be rc=0 (rc=%d)\n%s"
                        % (rc, out))
            assert_true(open(ledger, "rb").read().startswith(pre_head),
                        "append must keep the pre-existing line intact "
                        "(append-only)")
            rows = read_ledger_rows(ledger)
            assert_true(len(rows) == 2, "ledger should hold 2 rows, has %d"
                        % len(rows))
            entry = rows[1]
            assert_true(entry.get("correlationId") == "vacgenv2-segcast-0000",
                        "calibration row must carry correlationId=reportId: "
                        "%r" % entry)
            assert_true(entry.get("schema") == "rocqwash-exp/1",
                        "calibration row must carry the ledger schema: %r"
                        % entry)
            assert_true(str(entry.get("id", "")).startswith("CAL-"),
                        "calibration row id should be CAL-prefixed: %r"
                        % entry.get("id"))
            return ("correlationId carried, append-only growth holds, "
                    "id CAL-prefixed")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    check(results, "correlation-append-only", thunk)


def _seg_signal_face(results):
    def thunk():
        tmp = tempfile.mkdtemp(prefix="calib_seg_signal_")
        try:
            report, rcs = _fixture(tmp, 1, "green")
            ledger = os.path.join(tmp, "exp-ledger.jsonl")
            signals = os.path.join(tmp, "signals.json")
            args = ["--report", report, "--rc-file", rcs, "--ledger", ledger,
                    "--signals-out", signals]
            rc, out = run_tool(CALIB_TOOL, args)
            assert_true(rc == 0 and "[SIGNAL]" in out,
                        "a HIGH row over a failing green leg is a signal "
                        "(rc=%d)\n%s" % (rc, out))
            with open(signals, "r", encoding="utf-8") as handle:
                face = json.load(handle)
            assert_true(face.get("schema") == "rocqwash-calibration/1",
                        "signal face schema wrong: %r" % face.get("schema"))
            assert_true(face.get("signalCount") == 1,
                        "signal face should hold 1 row: %r" % face)
            rc2, out2 = run_tool(CALIB_TOOL, args + ["--strict"])
            assert_true(rc2 == 4, "--strict with a signal should exit 4 "
                        "(rc=%d)\n%s" % (rc2, out2))
            return ("signal row flagged, face JSON written, strict exit 4 "
                    "(signals stay data by default)")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    check(results, "signal-face", thunk)


def _seg_red_leg_semantics(results):
    def thunk():
        tmp = tempfile.mkdtemp(prefix="calib_seg_red_")
        try:
            report = os.path.join(tmp, "report.json")
            rcs = os.path.join(tmp, "rcs.json")
            write_json(report, {"reportId": "vacgenv2-redleg-0000",
                                "assumptions": [
                                    {"kind": "assumption", "name": "h",
                                     "status": "recognized",
                                     "familyId": "fam.r", "confidence": "MID"},
                                ]})
            write_json(rcs, {"refutation-full.lean": {"rc": 1,
                                                      "expected": "red"}})
            ledger = os.path.join(tmp, "exp-ledger.jsonl")
            rc, out = run_tool(CALIB_TOOL, ["--report", report, "--rc-file",
                                            rcs, "--ledger", ledger,
                                            "--default-leg",
                                            "refutation-full.lean"])
            assert_true(rc == 0 and "[SIGNAL]" not in out,
                        "declared red with rc=1 is a PASS: no signal "
                        "(rc=%d)\n%s" % (rc, out))
            rows = read_ledger_rows(ledger)
            assert_true(len(rows) == 1 and "measured PASS" in rows[0]["points"],
                        "red-leg pass should read measured PASS in points: "
                        "%r" % rows[0])
            return "declared red-leg semantics: rc=1 judged PASS, no signal"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    check(results, "red-leg-semantics", thunk)


def _seg_cli_face(results):
    def thunk():
        rc, out = run_tool(CALIB_TOOL, ["--help"])
        assert_true(rc == 0 and "rocqwash-exp/1" in out,
                    "--help should be rc=0 naming the ledger schema "
                    "(rc=%d)\n%s" % (rc, out))
        rc, _ = run_tool(CALIB_TOOL, [])
        assert_true(rc == 2, "missing input should exit 2, got %d" % rc)
        tmp = tempfile.mkdtemp(prefix="calib_seg_cli_")
        try:
            bad = os.path.join(tmp, "bad.json")
            with open(bad, "w", encoding="utf-8") as handle:
                handle.write("not-json{")
            ledger = os.path.join(tmp, "exp-ledger.jsonl")
            rc, _ = run_tool(CALIB_TOOL, ["--report", bad, "--rc-file", bad,
                                          "--ledger", ledger])
            assert_true(rc == 9, "corrupt report should exit 9, got %d" % rc)
            assert_true(not os.path.exists(ledger),
                        "corrupt input must not create the ledger")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return "usage face: help rc=0, missing input 2, corrupt input 9"
    check(results, "cli-face", thunk)


def _seg_port_wiring(results):
    """The correlationId wiring on the experience-bus port stays green."""
    def thunk():
        rc, out = run_tool(PORT_TOOL, ["--selftest"])
        assert_true(rc == 0 and PORT_MARK in out,
                    "exp_port --selftest should stay rc=0 after the "
                    "correlationId wiring (rc=%d)\n%s" % (rc, out))
        tmp = tempfile.mkdtemp(prefix="calib_seg_port_")
        try:
            ledger = os.path.join(tmp, "exp-ledger.jsonl")
            args = ["append", "--tool", "segTool", "--points", "pp",
                    "--evidence", "ee", "--batch", "bb",
                    "--correlation-id", "vacgenv2-segcast-0000",
                    "--ledger", ledger]
            rc, out = run_tool(PORT_TOOL, args)
            assert_true(rc == 0 and out.startswith("appended id="),
                        "port append with --correlation-id should be rc=0 "
                        "(rc=%d)\n%s" % (rc, out))
            entry = read_ledger_rows(ledger)[0]
            assert_true(entry.get("correlationId") == "vacgenv2-segcast-0000",
                        "port row should carry correlationId: %r" % entry)
            before = open(ledger, "rb").read()
            rc, out = run_tool(PORT_TOOL, args)
            assert_true(rc == 0 and out.startswith("duplicate-skip id="),
                        "port re-append should skip rc=0 (rc=%d)\n%s"
                        % (rc, out))
            assert_true(open(ledger, "rb").read() == before,
                        "port duplicate append must not write bytes")
            rc, out = run_tool(PORT_TOOL, ["append", "--tool", "t2",
                                           "--points", "p2",
                                           "--ledger", ledger])
            assert_true(rc == 0 and out.startswith("appended id="),
                        "append without the flag must stay keyless rc=0 "
                        "(rc=%d)\n%s" % (rc, out))
            last = read_ledger_rows(ledger)[-1]
            assert_true("correlationId" not in last,
                        "rows appended without the flag must not carry the "
                        "key: %r" % last)
            return ("port wiring: carried flag persists correlationId, "
                    "re-append skips, keyless appends stay keyless")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    check(results, "port-wiring", thunk)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


SEGMENTS = (
    ("tool-selftest", _seg_selftest),
    ("r7-idempotence", _seg_r7_idempotence),
    ("correlation-append-only", _seg_correlation_and_append_only),
    ("signal-face", _seg_signal_face),
    ("red-leg-semantics", _seg_red_leg_semantics),
    ("cli-face", _seg_cli_face),
    ("port-wiring", _seg_port_wiring),
)


def run_segment_calibration():
    """Refinery merge contract: (passed, failed, skipped, results rows)."""
    results = []
    if not os.path.isfile(CALIB_TOOL):
        results.append(("SKIP", "tools-landed",
                        "tools/calibration_ledger.py not landed yet, "
                        "not gated (%s)" % CALIB_TOOL))
        return _tally(results)
    if not os.path.isfile(PORT_TOOL):
        results.append(("SKIP", "port-landed",
                        "tools/exp_port.py not found, not gated (%s)"
                        % PORT_TOOL))
        return _tally(results)
    for _name, fn in SEGMENTS:
        fn(results)
    return _tally(results)


def _tally(results):
    passed = sum(1 for status, _n, _d in results if status == "PASS")
    failed = sum(1 for status, _n, _d in results if status == "FAIL")
    skipped = sum(1 for status, _n, _d in results if status == "SKIP")
    return passed, failed, skipped, results


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        if argv[0] in ("-h", "--help"):
            print(__doc__.strip())
            return 0
        sys.stderr.write("usage error: unknown argument %r\n" % argv[0])
        return 2
    passed, failed, skipped, results = run_segment_calibration()
    for status, name, detail in results:
        print("%s calib/%s -- %s" % (status, name, detail))
    print("SEGMENT calib passed=%d failed=%d skipped=%d"
          % (passed, failed, skipped))
    print("SUMMARY segments=1 passed=%d failed=%d skipped=%d"
          % (passed, failed, skipped))
    if failed:
        print("TOTAL-CALIBRATION RED (%d failed check(s))" % failed)
        return 1
    print("TOTAL-CALIBRATION GREEN (%d passed, %d skipped)"
          % (passed, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
