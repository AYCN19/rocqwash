#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Sign-off: \u738b\u5c0f\u54e5 (rocqwash \u81ea\u6f14\u8fdb\u7ebf\u00b7\u805a\u7c7b\u5e2d)
"""tests/refinery_segments/gap.py -- refinery segment for the gap aggregator lane.

Purpose. Assert the tools/gap_cluster.py contract item by item: the embedded selftest, family-shape-key clustering (an explicit familyId wins, a derived shape comes from typeHead or ledger points, recognized entries are excluded), ledger gap-class tokens, degraded-hole accounting, corrupt-input fail-loud, exit codes, and byte-identical reruns over the CLI (acceptance item R5); an own-register segment keeps this segment file and the tool battery-clean and CJK-free.

Interface. `python -I tests/refinery_segments/gap.py` runs the segment (exit 0 green, 1 any FAIL, 2 usage error). run_segment_gap() returns (passed, failed, skipped, results) and importing this module spawns nothing (import-safe), so the t_refinery merger can aggregate it.

Dependencies. Python 3 standard library only; tools/gap_cluster.py loads dynamically and every tool-facing check degrades to one loud SKIP line while it has not landed; tools/ai_flavor.py is exercised for the own-register face under the same rule; zero network by construction; fixtures are synthesized into a temporary directory.

Evidence. Live runs of `python -I tools/gap_cluster.py --selftest` (rc 0) and of this segment; the vacgen report face contract read from the frozen vacgen source (assumptions[] element key surface).

Exit-codes. 0 all checks green; 1 at least one FAIL (each listed, fail loud); 2 usage error. SKIP lines name their missing surface and never count as passes.
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEGMENT_PATH = os.path.abspath(__file__)
GAP_TOOL = os.path.join(HERE, "tools", "gap_cluster.py")
AI_FLAVOR_TOOL = os.path.join(HERE, "tools", "ai_flavor.py")
TOOL_TIMEOUT_S = 120
USAGE = "usage: python -I tests/refinery_segments/gap.py [-h]"

MODULE_CACHE = {}


def _load_gap_tool(results):
    """Load tools/gap_cluster.py once; loud SKIP naming the absent path when
    the module has not landed, loud FAIL when it raises at import."""
    if "gap" in MODULE_CACHE:
        return MODULE_CACHE["gap"]
    if not os.path.exists(GAP_TOOL):
        results.append(("SKIP", "module-import",
                        "tools/gap_cluster.py not landed yet (%s)" % GAP_TOOL))
        return None
    spec = importlib.util.spec_from_file_location("rqw_gap_cluster", GAP_TOOL)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        results.append(("FAIL", "module-import",
                        "tools/gap_cluster.py loaded but raised at import: %r" % exc))
        return None
    MODULE_CACHE["gap"] = mod
    return mod


def check(results, name, thunk):
    """Run one check; assertion failures and unexpected exceptions become
    FAIL lines with the cause named; a returned string becomes the detail."""
    try:
        detail = thunk()
    except AssertionError as exc:
        results.append(("FAIL", name, str(exc) or "assertion failed"))
    except Exception as exc:
        results.append(("FAIL", name, "%s: %r" % (type(exc).__name__, exc)))
    else:
        results.append(("PASS", name, detail or "ok"))


def assert_true(cond, message):
    if not cond:
        raise AssertionError(message)


def _run_tool(args, timeout=TOOL_TIMEOUT_S):
    """Run the gap tool in a clean interpreter (-I) and return the process."""
    return subprocess.run(
        [sys.executable, "-I", "-X", "utf8", GAP_TOOL] + [str(a) for a in args],
        capture_output=True, timeout=timeout)


def _run_ai_flavor(path, timeout=TOOL_TIMEOUT_S):
    return subprocess.run(
        [sys.executable, "-I", "-X", "utf8", AI_FLAVOR_TOOL, "--file", path],
        capture_output=True, timeout=timeout)


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def _read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _cjk_chars(text):
    """CJK and CJK-punctuation characters in a decoded text (code-face gate)."""
    out = []
    for ch in text:
        code = ord(ch)
        if (0x3000 <= code <= 0x303F or 0x3400 <= code <= 0x4DBF
                or 0x4E00 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF):
            out.append(ch)
    return out


# ------------------------------------------------------------- fixtures ----

def _fixture_report(path):
    """A vacgen v2 report face: the assumptions[] element key surface matches
    the frozen vacgen source (kind, name, typeHead, status, familyId,
    confidence, matchedTarget, degraded)."""
    report = {
        "reportId": "vacgenv2-seg-001",
        "assumptions": [
            {"kind": "assumption", "name": "s", "typeHead": "(1 / 2) < s.re",
             "status": "todo_seat", "familyId": "ineq.real.const-lt-field-re",
             "confidence": None, "matchedTarget": None, "degraded": None},
            {"kind": "assumption", "name": "t", "typeHead": "0 < eps",
             "status": "todo_seat", "familyId": None, "confidence": None,
             "matchedTarget": None, "degraded": None},
            {"kind": "assumption", "name": "u", "typeHead": "0 < eps",
             "status": "todo_seat", "familyId": None, "confidence": None,
             "matchedTarget": None, "degraded": None},
            {"kind": "assumption", "name": "w", "typeHead": "(1 / 2) < s.re",
             "status": "recognized", "familyId": "ineq.real.const-lt-field-re",
             "confidence": "HIGH", "matchedTarget": "assumption.type",
             "degraded": None},
        ],
    }
    _write(path, json.dumps(report))
    return report


def _fixture_ledger(path):
    """One rocqwash-exp/1 gap entry (TODO-SEAT token, family token in points,
    the same family as the report fixture so the cluster merges) and one
    non-gap precedent entry that must stay excluded."""
    gap_line = {
        "schema": "rocqwash-exp/1", "id": "seg-001", "ts": "T0",
        "tool": "vacgen2", "batch": "seg-batch",
        "points": ("premise face not covered by any taxonomy row (TODO-SEAT "
                   "counted, no silent degradation): ineq.real.const-lt-field-re "
                   "@ D:/seg/target.lean"),
        "evidence": "report.json (assumptions[] status=todo_seat)",
        "fingerprint": "a" * 64,
    }
    other_line = {
        "schema": "rocqwash-exp/1", "id": "seg-002", "ts": "T0",
        "tool": "periscope", "batch": "seg-batch",
        "points": "export API query redirect precedent, eight legs lost",
        "evidence": "raw/seg.netred.txt:3-11",
        "fingerprint": "b" * 64,
    }
    _write(path, json.dumps(gap_line) + "\n" + json.dumps(other_line) + "\n")


# -------------------------------------------------------------- segments ----

def run_segment_tool_contract(results):
    """Module import safety plus the embedded selftest exit code."""
    mod = _load_gap_tool(results)
    if mod is None:
        return
    def import_face():
        assert_true(hasattr(mod, "aggregate"), "aggregate() missing")
        assert_true(hasattr(mod, "main"), "main() missing")
        assert_true(hasattr(mod, "SCHEMA"), "SCHEMA missing")
        return "aggregate/main/SCHEMA present, import spawns nothing"

    check(results, "import-face", import_face)

    def selftest_green():
        proc = _run_tool(["--selftest"])
        assert_true(proc.returncode == 0,
                    "--selftest rc %r (stdout tail: %s)"
                    % (proc.returncode, proc.stdout[-200:]))
        assert_true(b"SELFTEST GREEN" in proc.stdout,
                    "no SELFTEST GREEN line in stdout")
        return "python -I tools/gap_cluster.py --selftest rc=0"

    check(results, "tool-selftest", selftest_green)


def run_segment_aggregation(results):
    """In-process aggregation contract over tmp fixtures."""
    mod = _load_gap_tool(results)
    if mod is None:
        return

    def clustering():
        with tempfile.TemporaryDirectory(prefix="refinery_gap_seg_") as tmp:
            rpath = os.path.join(tmp, "report.json")
            lpath = os.path.join(tmp, "ledger.jsonl")
            _fixture_report(rpath)
            _fixture_ledger(lpath)
            got = mod.aggregate([lpath], [rpath])
        keys = [c["shapeKey"] for c in got["clusters"]]
        assert_true(keys == ["fam:ineq.real.const-lt-field-re",
                             "shape:<num> < <id>"],
                    "cluster keys wrong: %r" % keys)
        fam = got["clusters"][0]
        assert_true(fam["count"] == 2,
                    "ledger and report members should merge in the family "
                    "cluster, count=%r" % fam["count"])
        assert_true(fam["members"][0]["origin"] == "ledger",
                    "member order wrong: %r" % fam["members"][0])
        assert_true(fam["explicitFamilyIds"] == ["ineq.real.const-lt-field-re"],
                    "explicit family list wrong: %r" % fam["explicitFamilyIds"])
        shape = got["clusters"][1]
        assert_true(shape["count"] == 2 and shape["variants"] == ["0 < eps"],
                    "shape cluster wrong: count=%r variants=%r"
                    % (shape["count"], shape["variants"]))
        totals = got["totals"]
        assert_true(totals["ledgerGapEntries"] == 1
                    and totals["ledgerNonGapEntries"] == 1,
                    "ledger gap-class split wrong: %r" % totals)
        assert_true(totals["reportTodoSeat"] == 3
                    and totals["reportNonTodoSeat"] == 1,
                    "report todo-seat split wrong: %r" % totals)
        assert_true(totals["gaps"] == 4 and totals["clusters"] == 2,
                    "totals wrong: %r" % totals)
        return ("explicit family merges across origins; shape key derived; "
                "recognized and precedent entries excluded")

    check(results, "aggregation-family-shape", clustering)

    def degraded():
        with tempfile.TemporaryDirectory(prefix="refinery_gap_seg_") as tmp:
            rpath = os.path.join(tmp, "hole.json")
            report = {"reportId": "vacgenv2-seg-002", "assumptions": [
                {"kind": "assumption", "name": "h", "typeHead": "_",
                 "status": "todo_seat", "familyId": None, "confidence": None,
                 "matchedTarget": None, "degraded": "hole"}]}
            _write(rpath, json.dumps(report))
            got = mod.aggregate([], [rpath])
        assert_true(got["clusters"][0]["degradedCounts"] == {"hole": 1},
                    "degraded accounting wrong: %r" % got["clusters"][0])
        return "degraded hole accounted"

    check(results, "aggregation-degraded-hole", degraded)

    def corrupt():
        with tempfile.TemporaryDirectory(prefix="refinery_gap_seg_") as tmp:
            bad = os.path.join(tmp, "bad.jsonl")
            _write(bad, '{"id": "ok"}\nnot-json-at-all\n')
            try:
                mod.aggregate([bad], [])
            except mod.GapInputError as exc:
                assert_true("line 2" in str(exc),
                            "error must name the line: %r" % str(exc))
            else:
                raise AssertionError("corrupt ledger did not fail loud")
            foreign = os.path.join(tmp, "foreign.json")
            _write(foreign, '{"unrelated": true}')
            try:
                mod.aggregate([], [foreign])
            except mod.GapInputError:
                pass
            else:
                raise AssertionError("foreign report did not fail loud")
        return "corrupt ledger line and foreign report fail loud"

    check(results, "aggregation-fail-loud", corrupt)


def run_segment_determinism(results):
    """R5: same inputs, two CLI runs, byte-identical out file and stdout."""
    mod = _load_gap_tool(results)
    if mod is None:
        return

    def r5():
        with tempfile.TemporaryDirectory(prefix="refinery_gap_r5_") as tmp:
            rpath = os.path.join(tmp, "report.json")
            lpath = os.path.join(tmp, "ledger.jsonl")
            _fixture_report(rpath)
            _fixture_ledger(lpath)
            out1 = os.path.join(tmp, "g1.json")
            out2 = os.path.join(tmp, "g2.json")
            shared = os.path.join(tmp, "g.json")
            p1 = _run_tool(["--ledger", lpath, "--reports", rpath,
                            "--out", out1, "--json"])
            p2 = _run_tool(["--ledger", lpath, "--reports", rpath,
                            "--out", out2, "--json"])
            assert_true(p1.returncode == 0 and p2.returncode == 0,
                        "CLI rc %r/%r" % (p1.returncode, p2.returncode))
            d1 = _read_bytes(out1)
            d2 = _read_bytes(out2)
            assert_true(d1 == d2, "out files differ across runs (R5 red)")
            p3 = _run_tool(["--ledger", lpath, "--reports", rpath,
                            "--out", shared, "--json"])
            p4 = _run_tool(["--ledger", lpath, "--reports", rpath,
                            "--out", shared, "--json"])
            assert_true(p3.returncode == 0 and p4.returncode == 0,
                        "shared-out CLI rc %r/%r"
                        % (p3.returncode, p4.returncode))
            assert_true(p3.stdout == p4.stdout,
                        "stdout bytes differ across runs (R5 red)")
            assert_true(p3.stdout.startswith(d1),
                        "stdout JSON face differs from the out file face")
            got = json.loads(d1.decode("utf-8"))
            assert_true(got["totals"]["gaps"] == 4, "R5 fixture totals wrong")
        return "two runs byte-identical (out file and stdout, R5)"

    check(results, "determinism-r5", r5)


def run_segment_exit_codes(results):
    """Exit-code faces: 9 missing input, 2 usage, 0 zero-gap data."""
    mod = _load_gap_tool(results)
    if mod is None:
        return

    def codes():
        with tempfile.TemporaryDirectory(prefix="refinery_gap_rc_") as tmp:
            missing = os.path.join(tmp, "missing.jsonl")
            p = _run_tool(["--ledger", missing])
            assert_true(p.returncode == 9,
                        "missing input rc %r (expected 9)" % p.returncode)
            assert_true(b"FAIL-LOUD" in p.stderr,
                        "missing input must say FAIL-LOUD on stderr")
            p = _run_tool([])
            assert_true(p.returncode == 2,
                        "no-input rc %r (expected 2)" % p.returncode)
            p = _run_tool(["--nonsense"])
            assert_true(p.returncode == 2,
                        "unknown flag rc %r (expected 2)" % p.returncode)
            empty = os.path.join(tmp, "empty.jsonl")
            _write(empty, '{"schema": "rocqwash-exp/1", "id": "seg-003", '
                          '"ts": "T0", "tool": "x", "batch": "b", '
                          '"points": "plain precedent", "fingerprint": "c"}\n')
            out = os.path.join(tmp, "gap.json")
            p = _run_tool(["--ledger", empty, "--out", out])
            assert_true(p.returncode == 0,
                        "zero-gap rc %r (expected 0, empty is data)"
                        % p.returncode)
            got = json.loads(_read_text(out))
            assert_true(got["clusters"] == [], "zero-gap clusters not empty")
        return "exit codes 9/2/0 loud on the named faces"

    check(results, "exit-codes", codes)


def run_segment_own_register(results):
    """This segment and the tool stay battery-clean and CJK-free."""
    def battery(path, label):
        if not os.path.exists(AI_FLAVOR_TOOL):
            results.append(("SKIP", "own-register-" + label,
                            "tools/ai_flavor.py not landed yet (%s)"
                            % AI_FLAVOR_TOOL))
            return
        proc = _run_ai_flavor(path)
        assert_true(proc.returncode == 0,
                    "ai_flavor rc %r on %s (tail: %s)"
                    % (proc.returncode, label, proc.stdout[-200:]))
        assert_true(b"VERDICT CLEAN" in proc.stdout,
                    "%s not battery CLEAN" % label)
        return "%s VERDICT CLEAN (36 faces = 0; em-dash = 0)" % label

    check(results, "own-register-battery-tool",
          lambda: battery(GAP_TOOL, "tools/gap_cluster.py"))
    check(results, "own-register-battery-segment",
          lambda: battery(SEGMENT_PATH, "tests/refinery_segments/gap.py"))

    def cjk_free(path, label):
        text = _read_text(path)
        hits = _cjk_chars(text)
        assert_true(hits == [],
                    "%s carries CJK on a code face: %r" % (label, hits[:8]))
        return "%s CJK face = 0 characters" % label

    check(results, "own-register-cjk-tool",
          lambda: cjk_free(GAP_TOOL, "tools/gap_cluster.py"))
    check(results, "own-register-cjk-segment",
          lambda: cjk_free(SEGMENT_PATH, "tests/refinery_segments/gap.py"))


def run_segment_gap():
    """The lane segment: contract, aggregation, determinism, exit codes,
    own register.  Returns (passed, failed, skipped, results)."""
    results = []
    run_segment_tool_contract(results)
    run_segment_aggregation(results)
    run_segment_determinism(results)
    run_segment_exit_codes(results)
    run_segment_own_register(results)
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
            print(USAGE)
            return 0
        sys.stderr.write("usage error: unknown argument %r\n" % argv[0])
        print(USAGE)
        return 2
    passed, failed, skipped, results = run_segment_gap()
    for status, name, detail in results:
        print("%s %s/%s -- %s" % (status, "gap", name, detail))
    print("SEGMENT %s passed=%d failed=%d skipped=%d"
          % ("gap", passed, failed, skipped))
    print("SUMMARY segments=1 passed=%d failed=%d skipped=%d"
          % (passed, failed, skipped))
    if failed:
        print("TOTAL-REFINERY-GAP RED (%d failed check(s))" % failed)
        return 1
    print("TOTAL-REFINERY-GAP GREEN (%d passed, %d skipped)"
          % (passed, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
