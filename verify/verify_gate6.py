#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_gate6.py — gate6 census thin wrapper + EntropyUnsatMark verdict mechanization.

    Purpose.  verify/ per-tool green-verdict entry face, two forms: (1)
      thin wrapper of the canonical census script
      `ConstructiveWorld-Set/scripts/gates/gate6_statement_census.py`
      (out-of-repository canonical, read-only; the launch layer is
      `wrapper/gate6_census.sh`; zero criteria duplication) — subprocess
      `python3 -B`, return code passthrough 1:1; (2) judge form — the
      seat_eum EntropyUnsatMark adjudication (statement-face bare Prop
      quantifier ch1 governance) mechanized into four rules over two census
      reports: ch1-must-drop (ch1 after < before, or zero on both sides);
      names-must-hold (statement names ordered-equal before→after);
      side-channels-zero-growth (ch2/ch3 zero growth; newly appeared files
      all-zero, axiom-free born); retirement-unpunished (INFO, never failing).

    Interface.  --tree <dir> [--json o] [--text] [--gate --baseline B]
      [--baseline-out O] [--script <gate6.py>] (flags pass through 1:1);
      --judge-before before.json --judge-after after.json
      [--judge-json out.json]; report shape {"files": {…: {ch1, ch2, ch3, names}}}.

    Dependencies.  Python 3 standard library only; zero network, zero
      compilation (the canonical script is a pure static token scan).

    Evidence.  --selftest ten vectors on fixture report shapes and fixture
      scripts (zero real-repository writes); tests/test_verify_gate6.py.

    Exit-codes.  0 = verdict passing or canonical census/gate passing;
      1 = verdict failing or canonical gate failing; 2 = usage or malformed
      report; 9 = missing path (script/--tree/--judge-*; fail-loud, no simulation).
"""
import argparse
import io
import json
import os
import subprocess
import sys

PROG = "verify_gate6"
GATE6_SCRIPT_DEF = ("/Users/apple/Desktop/ConstructiveWorld-Set/scripts"
                    "/gates/gate6_statement_census.py")


# ---------------------------------------------------------------------------
# judge (EUM-VERDICT)
# ---------------------------------------------------------------------------

def load_report(path):
    """Load a census JSON report and shape-check it (canonical reports form).
    Malformed = JudgeError."""
    if not os.path.isfile(path):
        raise MissingPath("report file missing: %s" % path)
    try:
        with io.open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as e:
        raise JudgeError("report JSON parse failed %s: %s" % (path, e))
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        raise JudgeError("report must be the {\"files\": {…}} shape: %s" % path)
    for fname, c in data["files"].items():
        if not isinstance(c, dict):
            raise JudgeError("report files[%s] must be an object: %s" % (fname, path))
        for k in ("ch1", "ch2", "ch3", "names"):
            if k not in c:
                raise JudgeError("report files[%s] missing the %s key: %s" % (fname, k, path))
    return data


def judge(before, after):
    """EntropyUnsatMark four-rule verdict.  Returns (ok, rows).

    Each row is dict(judge/ok/detail); judge is one of ch1-must-drop /
    names-must-hold / side-channels-zero-growth / retirement-unpunished.
    """
    rows = []
    bf, af = before["files"], after["files"]

    def ch_totals(rep, ch):
        return sum(len(rep["files"][f].get(ch, [])) for f in rep["files"])

    # rule 1 ch1-must-drop
    b1, a1 = ch_totals(before, "ch1"), ch_totals(after, "ch1")
    ok1 = (a1 < b1) or (a1 == 0 and b1 == 0)
    rows.append({"judge": "ch1-must-drop", "ok": ok1,
                 "detail": "ch1 before=%d after=%d (must drop, or zero on both sides)" % (b1, a1)})
    # rule 2 names-must-hold (per-file ordered-equal statement names, judged
    #   on surviving files only — a whole-file retirement carries its names
    #   with it under retirement-unpunished and is not drift; names in newly
    #   appeared files are normal growth)
    drift = []
    common = sorted(set(bf) & set(af))
    for f in common:
        if bf[f]["names"] != af[f]["names"]:
            drift.append(f)
    nb = sum(len(bf[f]["names"]) for f in common)
    na = sum(len(af[f]["names"]) for f in common)
    ok2 = (not drift) and (nb == na)
    rows.append({"judge": "names-must-hold", "ok": ok2,
                 "detail": "statement names over surviving files before=%d after=%d "
                           "drift files=%s (ordered-equal and total-equal required)"
                           % (nb, na, drift or "none")})
    # rule 3 side-channels-zero-growth (ch2/ch3) + newly appeared files
    #   all-zero (axiom-free born)
    grows = []
    for ch in ("ch2", "ch3"):
        b, a = ch_totals(before, ch), ch_totals(after, ch)
        if a > b:
            grows.append("%s %d→%d" % (ch, b, a))
    for f in sorted(set(af) - set(bf)):
        for ch in ("ch1", "ch2", "ch3"):
            if af[f].get(ch):
                grows.append("newly appeared file %s %s=%d (axiom-free born requires all-zero)"
                             % (f, ch, len(af[f][ch])))
    rows.append({"judge": "side-channels-zero-growth", "ok": not grows,
                 "detail": "; ".join(grows) if grows
                           else "ch2/ch3 zero growth; newly appeared files all-zero"})
    # rule 4 retirement-unpunished (INFO)
    gone = sorted(set(bf) - set(af))
    rows.append({"judge": "retirement-unpunished", "ok": True,
                 "detail": ("retired files=%s (INFO, never failing)" % gone) if gone
                           else "no retirement"})
    return all(r["ok"] for r in rows if r["judge"] != "retirement-unpunished"), rows


class JudgeError(Exception):
    pass


class MissingPath(Exception):
    pass


# ---------------------------------------------------------------------------
# thin wrapper of the canonical script
# ---------------------------------------------------------------------------

def run_census(script, passthrough_args):
    """Run the canonical script as `python3 -B` in a subprocess; return code
    passthrough 1:1 (zero criteria duplication)."""
    if not os.path.isfile(script):
        print("FAIL-LOUD: canonical gate6 script missing: %s (override with --script/GATE6_SCRIPT)" % script,
              file=sys.stderr)
        sys.exit(9)
    cmd = [sys.executable, "-B", script] + list(passthrough_args)
    sys.stdout.flush()
    return subprocess.run(cmd).returncode


# ---------------------------------------------------------------------------
# selftest (verdict vectors use the seat_eum measured report shape; wrapper
# vectors use fixture scripts; zero real-repository writes)
# ---------------------------------------------------------------------------

EUM_NAMES = ["fa52_EDP_E_B_pos_unsat", "fa52_EntropyDiffReal_premises_unsat",
             "eum_E_B_pos_slot_unsat_ref", "eum_premises_unsat_ref",
             "eum_EntropyDiffReal_section_vacuous"]
EUM_CH1_HIT = {"line": 135, "cmd": "Theorem", "name": "eum_EntropyDiffReal_section_vacuous",
               "excerpt": "Theorem eum_EntropyDiffReal_section_vacuous : forall (Omega_A : "
                          "forall (E_A : Real), real_lt real_zero E_A -> Real) -> Real"}


def eum_report(ch1_hits):
    """Fixture in the seat_eum report shape (EntropyUnsatMark.v; ch1 given
    per before/after)."""
    return {"summary": {"files": 1,
                        "totals": {"ch1": len(ch1_hits), "ch2": 0, "ch3": 0},
                        "statement_names": len(EUM_NAMES)},
            "files": {"EntropyUnsatMark.v": {"ch1": ch1_hits, "ch2": [], "ch3": [],
                                             "names": list(EUM_NAMES)}}}


def selftest():
    """Built-in vectors: eum before/after verdict passing; ch1 not dropped
    failing; name drift failing; side-channel growth failing; newly appeared
    file failing/passing; retirement INFO; malformed report 2; missing judge
    file 9; missing canonical script 9; passthrough rc both ways (fixture
    scripts, zero real repository)."""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_verifygate6_self_")
    here = os.path.dirname(os.path.abspath(__file__))

    def run(args):
        p = subprocess.run([sys.executable, "-B", os.path.join(here, PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else ""
        return p

    def wf(name, obj):
        fp = os.path.join(tmp, name)
        with io.open(fp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
        return fp

    try:
        before = eum_report([EUM_CH1_HIT])
        after = eum_report([])
        # (1) eum verdict positive: before(ch1=1)→after(ch1=0, names 5=5) → GREEN rc 0
        jb, ja = wf("eum_before.json", before), wf("eum_after.json", after)
        p = run(["--judge-before", jb, "--judge-after", ja])
        assert p.returncode == 0, "eum verdict should pass rc=0, got %d\n%s" % (p.returncode, p.stdout)
        assert "EUM-VERDICT-GREEN" in p.stdout and "ch1-must-drop" in p.stdout, p.stdout

        # (2) ch1 not dropped negative (before=after; a stock that is only
        #     frozen punishes growth, not stagnation) → RED rc 1
        p = run(["--judge-before", jb, "--judge-after", jb])
        assert p.returncode == 1 and "ch1-must-drop" in p.stdout, p.stdout

        # (3) name-drift negative (names reordered) → RED rc 1, names-must-hold
        shaken = eum_report([])
        shaken["files"]["EntropyUnsatMark.v"]["names"] = list(reversed(EUM_NAMES))
        js = wf("eum_shaken.json", shaken)
        p = run(["--judge-before", jb, "--judge-after", js])
        assert p.returncode == 1 and "names-must-hold" in p.stdout, p.stdout

        # (4) side-channel growth negative (ch2 appears) → RED rc 1,
        #     side-channels-zero-growth
        grown = eum_report([])
        grown["files"]["EntropyUnsatMark.v"]["ch2"] = [{"line": 9, "cmd": "Class", "name": "",
                                                        "excerpt": "Class C : Prop := {}."}]
        jg = wf("eum_grown.json", grown)
        p = run(["--judge-before", jb, "--judge-after", jg])
        assert p.returncode == 1 and "side-channels-zero-growth" in p.stdout, p.stdout

        # (5) newly appeared file: with ch1 → failing; all-zero → passing
        #     (axiom-free born rule)
        plus = json.loads(json.dumps(after))
        plus["files"]["NewBorn.v"] = {"ch1": [{"line": 3, "cmd": "Lemma", "name": "bad",
                                               "excerpt": "Lemma bad : Prop."}],
                                      "ch2": [], "ch3": [], "names": ["bad"]}
        jp = wf("eum_plus.json", plus)
        p = run(["--judge-before", jb, "--judge-after", jp])
        assert p.returncode == 1 and "newly appeared file" in p.stdout, p.stdout
        plus2 = json.loads(json.dumps(after))
        plus2["files"]["NewBorn.v"] = {"ch1": [], "ch2": [], "ch3": [], "names": []}
        jp2 = wf("eum_plus2.json", plus2)
        p = run(["--judge-before", jb, "--judge-after", jp2])
        assert p.returncode == 0, "all-zero newly appeared file should pass rc=0, got %d\n%s" % (p.returncode, p.stdout)

        # (6) retirement INFO unpunished: after loses one file → still passing
        #     (rule 4 INFO row on the record)
        minus = eum_report([])
        minus["files"] = {}
        jm = wf("eum_minus.json", minus)
        p = run(["--judge-before", jb, "--judge-after", jm])
        assert p.returncode == 0 and "retirement-unpunished" in p.stdout, p.stdout

        # (7) malformed report → rc 2; missing judge file → rc 9
        bad = os.path.join(tmp, "bad.json")
        with io.open(bad, "w", encoding="utf-8") as fh:
            fh.write('{"nope": 1}')
        p = run(["--judge-before", jb, "--judge-after", bad])
        assert p.returncode == 2, "malformed report should rc=2, got %d" % p.returncode
        p = run(["--judge-before", os.path.join(tmp, "nope.json"), "--judge-after", ja])
        assert p.returncode == 9, "missing judge file should rc=9, got %d" % p.returncode

        # (8) thin wrapper: missing --tree → 2; missing tree → 9; missing
        #     canonical script → 9 (fail-loud before any run)
        p = run([])
        assert p.returncode == 2, "missing --tree should rc=2, got %d" % p.returncode
        p = run(["--tree", os.path.join(tmp, "no_tree_dir")])
        assert p.returncode == 9, "missing tree should rc=9, got %d" % p.returncode
        fake = wf("fake.json", {})
        p = run(["--script", os.path.join(tmp, "no_gate6.py"), "--tree", tmp])
        assert p.returncode == 9 and "script missing" in p.stdout, p.stdout

        # (9) passthrough rc both ways (fixture script stand-ins, zero real
        #     repository, zero real census)
        child_ok = os.path.join(tmp, "child_ok.py")
        with io.open(child_ok, "w", encoding="utf-8") as fh:
            fh.write("import sys\nprint('CHILD-OK')\nsys.exit(0)\n")
        p = run(["--script", child_ok, "--tree", tmp, "--text"])
        assert p.returncode == 0 and "CHILD-OK" in p.stdout, p.stdout
        child_red = os.path.join(tmp, "child_red.py")
        with io.open(child_red, "w", encoding="utf-8") as fh:
            fh.write("import sys\nprint('CHILD-RED')\nsys.exit(1)\n")
        p = run(["--script", child_red, "--tree", tmp])
        assert p.returncode == 1 and "CHILD-RED" in p.stdout, p.stdout

        print("VERIFY-GATE6-SELFTEST PASS: eum verdict green/ch1-not-dropped red/name-drift red/"
              "side-channel-growth red/new-file red-green/retirement INFO/malformed 2/missing 9/"
              "script-missing 9/passthrough rc both — all ten checks pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="gate6 census thin wrapper + EntropyUnsatMark verdict mechanization")
    ap.add_argument("--tree", default=None, help=".v tree directory to survey (thin-wrapper form)")
    ap.add_argument("--json", dest="json_out", default=None, help="1:1 passthrough to the canonical script")
    ap.add_argument("--text", action="store_true", help="1:1 passthrough to the canonical script")
    ap.add_argument("--gate", action="store_true", help="1:1 passthrough to the canonical script")
    ap.add_argument("--baseline", default=None, help="1:1 passthrough to the canonical script")
    ap.add_argument("--baseline-out", dest="baseline_out", default=None, help="1:1 passthrough to the canonical script")
    ap.add_argument("--script", default=os.environ.get("GATE6_SCRIPT", GATE6_SCRIPT_DEF),
                    help="canonical gate6 census script path (default ConstructiveWorld-Set canonical path)")
    ap.add_argument("--judge-before", default=None, help="census report before (judge form)")
    ap.add_argument("--judge-after", default=None, help="census report after (judge form)")
    ap.add_argument("--judge-json", default=None, help="verdict record JSON output path")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # judge form
    if args.judge_before or args.judge_after:
        if not (args.judge_before and args.judge_after):
            print("FAIL-LOUD: --judge-before and --judge-after must come as a pair", file=sys.stderr)
            sys.exit(2)
        try:
            before = load_report(args.judge_before)
            after = load_report(args.judge_after)
        except MissingPath as e:
            print("FAIL-LOUD: %s" % e, file=sys.stderr)
            sys.exit(9)
        except JudgeError as e:
            print("FAIL-LOUD: %s" % e, file=sys.stderr)
            sys.exit(2)
        print("EUM-VERDICT before=%s after=%s" % (args.judge_before, args.judge_after))
        ok, rows = judge(before, after)
        for r in rows:
            print("  %s %s — %s" % ("PASS" if r["ok"] else "RED ", r["judge"], r["detail"]))
        if args.judge_json:
            with io.open(args.judge_json, "w", encoding="utf-8", newline="\n") as fh:
                json.dump({"before": args.judge_before, "after": args.judge_after,
                           "verdict": "GREEN" if ok else "RED", "rows": rows},
                          fh, ensure_ascii=False, indent=1)
            print("json ->", args.judge_json)
        print("EUM-VERDICT-%s (EntropyUnsatMark verdict: ch1-must-drop / names-must-hold / "
              "side-channels-zero-growth / retirement-unpunished)"
              % ("GREEN" if ok else "RED"))
        sys.exit(0 if ok else 1)

    # thin-wrapper form
    if not args.tree:
        print("FAIL-LOUD: missing --tree <.v tree directory> (or use the judge form "
              "--judge-before/--judge-after)", file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(args.tree):
        print("FAIL-LOUD: --tree directory missing: %s" % args.tree, file=sys.stderr)
        sys.exit(9)
    if args.gate and not args.baseline:
        print("FAIL-LOUD: --gate requires --baseline (the canonical GATE6-USAGE rule, "
              "pre-checked here)", file=sys.stderr)
        sys.exit(2)
    passthrough = ["--tree", args.tree]
    if args.json_out:
        passthrough += ["--json", args.json_out]
    if args.text:
        passthrough += ["--text"]
    if args.gate:
        passthrough += ["--gate", "--baseline", args.baseline]
    if args.baseline_out:
        passthrough += ["--baseline-out", args.baseline_out]
    sys.exit(run_census(args.script, passthrough))


if __name__ == "__main__":
    main()
