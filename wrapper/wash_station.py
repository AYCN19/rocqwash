#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""wash_station.py — wash-station three-step composer, steps 5/6/7 (rocqwash wrapper/).

Purpose.  Composes the three ad-hoc manual loops of the nine-step shape
  normalization form into one station command with zero frozen-file edits:
  step 5 cross-check (`names/mac_stmt_names.py work/X.v --compare src/X.v`,
  the N=N ordered-equality assertion), step 6 gate4
  (`verify/gate4_comment_guard.py --file work/X.v`, the five-field header
  mechanical check v2.1 EXT), step 7 probe (`seam/seam_probe.py --file
  work/X.v`, the W13 four-mechanism fingerprint candidates).  Every step
  runs the frozen canonical file directly (subprocess `python3 -B
  <canonical absolute path>`); the station only composes, emits the
  station account and aggregates exit codes — the sole verdict source for
  each step stays that canonical file's own exit code (zero criterion
  copying; the scan_station.py "recognize only + pass through" and
  gate7_probe.sh "zero criterion copying" adaptation discipline).  The
  station itself writes nothing except the user-specified --station-json
  (and the frozen files' own user-specified --gate4-json/--probe-json/
  --probe-csv).  Dry run by default in the sense that no step writes
  unless the underlying frozen tool is given its write flags.

Interface.  python3 wrapper/wash_station.py --washed WORK.v --baseline
  SRC.v [--root DIR] [--steps names,gate4,probe] [--include-let]
  [--kinds LIST] [--expect-names N] [--gate4-json PATH]
  [--gate4-no-principle] [--gate4-length-fail] [--gate4-length-cap N]
  [--probe-json PATH] [--probe-csv PATH] [--check-pin]
  [--expect-names-md5 HEX | --expect-gate4-md5 HEX |
  --expect-probe-md5 HEX] [--station-json PATH] | --station-selftest.
  Step subset may shrink but never reorders (composer contract).  The
  step 7 probe is a fingerprint-candidate check only (the E364 blind-spot
  rule: a hit is a candidate, not a verdict; zero hits means no
  candidates were emitted, not "no seam" — the report lists, it does not
  clear); it does not replace the gate7 extraction gate (the
  ConstructiveWorld-Set scripts/gates/gate7_extract_run.py out-of-repo
  read-only canonical), whose verdicts still run through the
  wrapper/gate7_probe.sh chain.

Dependencies.  Python 3 standard library only; every path parameterized,
  zero network.  Subprocesses always run `python3 -B` (no __pycache__ on
  read-only faces).  The station never wraps itself in cpu_guard (the
  `seat_nw8` nested-deadlock precedent — the wrapping duty belongs to the
  caller, per the nw8 zero-bare-call convention).

Evidence.  --station-selftest: nine frozen vectors, zero writes, no
  frozen file executed — canonical presence, pin hex shape, --steps
  subset ordering plus unknown-step rejection, hard-worst aggregation,
  the three rc->verdict tables, the three command assemblies, input
  precheck (baseline dependency + same-file rejection), station-account
  extraction (positive and negative), and the md5 assertion shape check.

Exit-codes.  Aggregation law, hard-worst wins: 0 = all steps green
  (step5 rc=0 and step6 rc=0 and step7 rc=0 — a probe hit is a candidate,
  not a failure, per the E364 rule); 1 = hard failing (step5 rc!=0 name
  face N!=N / step6 rc=1 hard violation / step7 rc!=0 account-write
  failure); 2 = review-grade or station-level (step6 rc=2 REVIEW items /
  station usage error / md5 assertion failure — a failed assertion never
  opens the run); 9 = file or canonical missing (washed/baseline/any
  canonical; the precheck gates the run at zero steps).
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys

PROG = "wash_station"
WRAP_NAME = "wrapper/wash_station.py"

# frozen canonical files (repo-root-relative paths + pinned md5 taken from the
# live tree when this wrapper was built).  If a canonical is revised by the
# freeze authority, the wrapper agent re-pins against the live tree; this
# station never edits canonicals.
CANONICALS = {
    "names": {"rel": "names/mac_stmt_names.py",
              "pin": "01dc635ce445b05628bdd6e728990ce3"},
    "gate4": {"rel": "verify/gate4_comment_guard.py",
              "pin": "d7ab397c5f0243d0c7320f91d0f14481"},
    "probe": {"rel": "seam/seam_probe.py",
              "pin": "7a01359a22b8960b352191f1a4490b37"},
}
PIN_NOTE = "20261031 rqadapt 适配时嵌记"
STEP_ORDER = ("names", "gate4", "probe")          # steps 5/6/7 fixed order (may shrink, never reorder)
STEP_LABEL = {"names": "s5-xcheck", "gate4": "s6-gate4", "probe": "s7-probe"}

# per-canonical rc -> station verdict tables (zero criterion copying: the
# verdict derives solely from the canonical's own rc)
NAMES_GATE = {0: "PASS"}                            # others (2=unequal, 9=missing) -> FAIL
GATE4_GATE = {0: "PASS", 1: "FAIL", 2: "REVIEW"}    # nw8 sense: only REVIEW=0 counts as clean
PROBE_GATE = {0: "PASS"}                            # hits are candidates, not failures (E364 rule); rc!=0 = account failure

VERDICT_RANK = {"PASS": 0, "REVIEW": 1, "FAIL": 2, "MISSING": 3}
VERDICT_EXIT = {"PASS": 0, "REVIEW": 2, "FAIL": 1, "MISSING": 9}

# station-account info extraction (reporting only, never re-judges — the
# verdict derives solely from rc; a failed extraction emits null honestly).
# KEEP (data faces): the regexes parse the frozen canonicals' own output
# formats verbatim and must not be rewritten.
RE_NAMES_ASSERT = re.compile(r"断言 (\d+)=(\d+) 有序全等 : (PASS|FAIL)")
RE_NAMES_TOTAL = re.compile(r"^total: (\d+)", re.M)
RE_GATE4_SUM = re.compile(
    r"件数=(\d+)\s+PASS=(\d+)\s+FAIL=(\d+)\s+REVIEW\(人工复核\)=(\d+)\s+UNREADABLE=(\d+)")
RE_PROBE_TOTAL = re.compile(r"^TOTAL: (\d+) 候选", re.M)

STATION_USAGE = """wash_station — wash-station three-step composer, steps 5/6/7 (wrapper/)

Usage:
  python3 wrapper/wash_station.py --washed WORK.v --baseline SRC.v [station flags]

Station flags:
  --washed FILE         washed file (shared target of the three steps; required)
  --baseline FILE       step-5 cross-check baseline (required when names is in step)
  --root DIR            frozen canonical repository root (default = this wrapper's repo root)
  --steps LIST          step subset, comma-separated (names,gate4,probe; default all; may shrink, never reorder)
  --include-let/--kinds LIST/--expect-names N     passed through to names
  --gate4-json PATH / --gate4-no-principle / --gate4-length-fail / --gate4-length-cap N
                        passed through to gate4
  --probe-json PATH / --probe-csv PATH            passed through to seam_probe
  --check-pin           three canonical pinned-md5 assertions
  --expect-names-md5/--expect-gate4-md5/--expect-probe-md5 HEX   extra assertions
  --station-json PATH   station-account JSON (the station's only write surface; zero writes by default)
  --station-selftest    station selftest (nine vectors; zero writes; no frozen file executed)
  -h / --help           this help

Exit codes: 0=all three steps green  1=hard failing (cross-check unequal / gate4 hard violation / probe account failure)
        2=REVIEW or station-level usage / assertion failure
        9=file or canonical missing
"""


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def default_root():
    """Default canonical repo root = the grandparent of this wrapper file (wrapper/'s parent)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def canonical_path(root, step):
    return os.path.join(os.path.abspath(root), *CANONICALS[step]["rel"].split("/"))


def norm_hex(s):
    """Assertion-value shape check: strip whitespace/quotes, lowercase; non-32-hex returns None."""
    t = s.strip().strip("'\"").lower()
    if len(t) == 32 and all(c in "0123456789abcdef" for c in t):
        return t
    return None


def parse_steps(spec_list):
    """--steps parsing: comma split plus repeated-flag merge; an unknown step
    name raises ValueError; reorderings are discarded — always normalized to
    the steps-5/6/7 fixed order (composer contract: may shrink, never
    reorder)."""
    got = set()
    for spec in spec_list or []:
        for tok in spec.split(","):
            tok = tok.strip()
            if not tok:
                continue
            if tok not in STEP_ORDER:
                raise ValueError("unknown step name %r (legal: names,gate4,probe)" % tok)
            got.add(tok)
    if not got:
        raise ValueError("--steps parsed to an empty set")
    return [s for s in STEP_ORDER if s in got]


def check_inputs(washed, baseline, steps):
    """Input shape precheck: returns an error string or None (file existence is main's precheck; this checks the composition shape only)."""
    if not washed:
        return "--washed is required (shared target of the three steps)"
    if "names" in steps and not baseline:
        return "--baseline is required (the step-5 cross-check baseline, when names is in step)"
    if washed and baseline and os.path.abspath(washed) == os.path.abspath(baseline):
        return "washed file and cross-check baseline are the same file (the check would degenerate to always-true; refused): %s" % washed
    return None


def child_argv(canonical, rest):
    """Direct-call child form: [python, -B, frozen canonical absolute path, ...passthrough args].  -B forbids __pycache__."""
    py = sys.executable or "python3"
    return [py, "-B", canonical] + list(rest)


def names_cmd(canonical, washed, baseline, include_let, kinds, expect_names):
    rest = [washed, "--compare", baseline]
    if include_let:
        rest.append("--include-let")
    if kinds:
        rest += ["--kinds", kinds]
    if expect_names is not None:
        rest += ["--expect", str(expect_names)]
    return child_argv(canonical, rest)


def gate4_cmd(canonical, washed, gate4_json, no_principle, length_fail, length_cap):
    rest = ["--file", washed]
    if gate4_json:
        rest += ["--json", gate4_json]
    if no_principle:
        rest.append("--no-principle")
    if length_fail:
        rest.append("--length-fail")
    if length_cap is not None:
        rest += ["--length-cap", str(length_cap)]
    return child_argv(canonical, rest)


def probe_cmd(canonical, washed, probe_json, probe_csv):
    rest = ["--file", washed]
    if probe_json:
        rest += ["--json", probe_json]
    if probe_csv:
        rest += ["--hits-csv", probe_csv]
    return child_argv(canonical, rest)


def gate_step(table, rc):
    """Verdict table lookup; an rc outside the table is always FAIL (fail-loud, nothing waved through)."""
    return table.get(rc, "FAIL")


def aggregate(verdicts):
    """Aggregation law, hard-worst wins: MISSING(9) > FAIL(1) > REVIEW(2) > PASS(0)."""
    if not verdicts:
        return "PASS", 0
    worst = max(verdicts, key=lambda v: VERDICT_RANK[v])
    return worst, VERDICT_EXIT[worst]


def run_child(argv):
    """Run a frozen file directly: capture the child process and echo it verbatim (operator visibility equals the ad-hoc loop); the rc passes through unchanged."""
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, encoding="utf-8", errors="replace")
    if p.stdout:
        sys.stdout.write(p.stdout)
        sys.stdout.flush()
    if p.stderr:
        sys.stderr.write(p.stderr)
        sys.stderr.flush()
    return p.returncode, p.stdout or ""


def extract_info(stdout, probe_json_path):
    """Station-account info extraction (reporting only, never re-judges; nothing extracted means None, emitted honestly)."""
    info = {}
    m = RE_NAMES_ASSERT.search(stdout)
    if m:
        info["names_assert"] = "%s=%s %s" % (m.group(1), m.group(2), m.group(3))
    m = RE_NAMES_TOTAL.search(stdout)
    if m:
        info["names_total"] = int(m.group(1))
    m = RE_GATE4_SUM.search(stdout)
    if m:
        info["gate4_summary"] = {"files": int(m.group(1)), "pass": int(m.group(2)),
                                 "fail": int(m.group(3)), "review": int(m.group(4)),
                                 "unreadable": int(m.group(5))}
    m = RE_PROBE_TOTAL.search(stdout)
    hits_total = int(m.group(1)) if m else None
    per_lane = None
    if probe_json_path and os.path.isfile(probe_json_path):
        try:
            with io.open(probe_json_path, encoding="utf-8") as fh:
                acc = json.load(fh)
            hits = acc.get("hits")
            if isinstance(hits, list):
                hits_total = len(hits)
                per_lane = {}
                for h in hits:
                    lane = h.get("lane")
                    if lane:
                        per_lane[lane] = per_lane.get(lane, 0) + 1
        except Exception as e:
            info["probe_json_read_error"] = str(e)
    if hits_total is not None:
        info["probe_hits_total"] = hits_total
    if per_lane is not None:
        info["probe_hits_per_lane"] = per_lane
    return info


def station_selftest():
    """Station selftest, nine vectors (zero writes; no frozen file executed).  Returns the pass boolean."""
    ok = True
    root = default_root()

    # v1 the three canonicals present (default root)
    found = {s: canonical_path(root, s) for s in STEP_ORDER}
    j = all(os.path.isfile(p) for p in found.values())
    print("  judge1 canonicals present (default root):", "PASS" if j else "FAIL", found)
    ok = ok and j

    # v2 the three pins are 32-hex shaped
    j = all(norm_hex(CANONICALS[s]["pin"]) == CANONICALS[s]["pin"] for s in STEP_ORDER)
    print("  judge2 pins are 32-hex shaped:", "PASS" if j else "FAIL")
    ok = ok and j

    # v3 --steps parsing: subset keeps fixed order (may shrink, never reorder) + unknown step name rejected
    try:
        got = parse_steps(["probe,names"])
        j = got == ["names", "probe"]
    except ValueError:
        got, j = None, False
    print("  judge3 steps subset fixed order:", "PASS" if j else "FAIL", got)
    try:
        parse_steps(["bogus"])
        j = False
    except ValueError:
        j = True
    print("  judge3b unknown step name rejected:", "PASS" if j else "FAIL")
    ok = ok and j

    # v4 aggregation law, hard-worst wins
    v1, e1 = aggregate(["PASS", "PASS", "PASS"])
    v2, e2 = aggregate(["PASS", "REVIEW"])
    v3, e3 = aggregate(["FAIL", "REVIEW"])
    v4, e4 = aggregate(["PASS", "MISSING"])
    j = (v1, e1) == ("PASS", 0) and (v2, e2) == ("REVIEW", 2) \
        and (v3, e3) == ("FAIL", 1) and (v4, e4) == ("MISSING", 9)
    print("  judge4 aggregation hard-worst wins:", "PASS" if j else "FAIL",
          (v1, e1), (v2, e2), (v3, e3), (v4, e4))
    ok = ok and j

    # v5 the three verdict tables
    j = (gate_step(NAMES_GATE, 0) == "PASS" and gate_step(NAMES_GATE, 2) == "FAIL"
         and gate_step(GATE4_GATE, 0) == "PASS" and gate_step(GATE4_GATE, 1) == "FAIL"
         and gate_step(GATE4_GATE, 2) == "REVIEW" and gate_step(GATE4_GATE, 7) == "FAIL"
         and gate_step(PROBE_GATE, 0) == "PASS" and gate_step(PROBE_GATE, 9) == "FAIL")
    print("  judge5 verdict tables names/gate4/probe:", "PASS" if j else "FAIL")
    ok = ok and j

    # v6 the three command assemblies (direct-call child form: [python, -B, canonical, ...passthrough])
    c1 = names_cmd("/R/names.py", "w.v", "b.v", True, "Definition,Lemma", 5)
    c2 = gate4_cmd("/R/gate4.py", "w.v", "g.json", False, False, None)
    c3 = probe_cmd("/R/probe.py", "w.v", "p.json", "p.csv")
    head = [sys.executable or "python3", "-B"]
    j = (c1 == head + ["/R/names.py", "w.v", "--compare", "b.v", "--include-let",
                       "--kinds", "Definition,Lemma", "--expect", "5"]
         and c2 == head + ["/R/gate4.py", "--file", "w.v", "--json", "g.json"]
         and c3 == head + ["/R/probe.py", "--file", "w.v", "--json", "p.json",
                           "--hits-csv", "p.csv"])
    print("  judge6 command assemblies:", "PASS" if j else "FAIL")
    ok = ok and j

    # v7 input shape precheck: baseline dependency + same-file rejection
    j = (check_inputs(None, None, ["names"]) is not None
         and check_inputs("w.v", None, ["probe"]) is None
         and check_inputs("w.v", None, ["names"]) is not None
         and check_inputs("w.v", "b.v", ["names"]) is None
         and check_inputs("w.v", "w.v", ["names"]) is not None)
    print("  judge7 input shape precheck:", "PASS" if j else "FAIL")
    ok = ok and j

    # v8 station-account extraction: sample lines from the three frozen files extracted + non-matching input honestly None
    s1 = "file: x\nmd5: ab\ntotal: 7  let_skipped: 0\n断言 7=7 有序全等 : PASS"
    s2 = "[gate4ext] v2.1 扫描时点=T  件数=1  PASS=1  FAIL=0  REVIEW(人工复核)=0  " \
         "UNREADABLE=0  length_cap=30(review)  principle=on  deep_files=0"
    s3 = "TOTAL: 3 候选"
    i1 = extract_info(s1, None)
    i2 = extract_info(s2, None)
    i3 = extract_info(s3, None)
    i0 = extract_info('no extractable lines', None)
    j = (i1.get("names_total") == 7 and i1.get("names_assert") == "7=7 PASS"
         and i2.get("gate4_summary") == {"files": 1, "pass": 1, "fail": 0,
                                         "review": 0, "unreadable": 0}
         and i3.get("probe_hits_total") == 3
         and "probe_hits_total" not in i0 and "names_total" not in i0)
    print("  judge8 station-account extraction positive/negative:", "PASS" if j else "FAIL")
    ok = ok and j

    # v9 assertion shape check: valid 32-hex passes, bogus values rejected
    j = (norm_hex(" 01dc635ce445b05628bdd6e728990ce3 ") == "01dc635ce445b05628bdd6e728990ce3"
         and norm_hex("zz") is None and norm_hex("01dc") is None)
    print("  judge9 assertion shape check pass/reject:", "PASS" if j else "FAIL")
    ok = ok and j

    return ok


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(prog=PROG, description="wash-station three-step composer (calls frozen canonicals directly; zero frozen edits)",
                                 usage=STATION_USAGE)
    ap.add_argument("--washed", default=None, help="washed file (shared target of the three steps)")
    ap.add_argument("--baseline", default=None, help="step-5 cross-check baseline (pre-wash source)")
    ap.add_argument("--root", default=None, help="frozen canonical repository root (default = this wrapper's repo root)")
    ap.add_argument("--steps", action="append", default=None,
                    help="step subset, comma-separated (names,gate4,probe;"
                         " default all; may shrink, never reorder)")
    ap.add_argument("--include-let", action="store_true", help="convergence sense for step 5 (Let counted in)")
    ap.add_argument("--kinds", default=None, help="step-5 kind filter (passed through to names --kinds)")
    ap.add_argument("--expect-names", type=int, default=None, help="step-5 count assertion (passed through to --expect)")
    ap.add_argument("--gate4-json", default=None, help="step-6 gate4 --json write path")
    ap.add_argument("--gate4-no-principle", action="store_true", help="step-6: turn off the judgment-principle heuristic")
    ap.add_argument("--gate4-length-fail", action="store_true", help="step-6: promote over-budget headers to hard violation")
    ap.add_argument("--gate4-length-cap", type=int, default=None, help="step-6 header line cap (default 30)")
    ap.add_argument("--probe-json", default=None, help="step-7 probe --json write path")
    ap.add_argument("--probe-csv", default=None, help="step-7 probe --hits-csv write path")
    ap.add_argument("--check-pin", action="store_true", help="three canonical pinned-md5 assertions")
    ap.add_argument("--expect-names-md5", action="append", default=[], metavar="HEX")
    ap.add_argument("--expect-gate4-md5", action="append", default=[], metavar="HEX")
    ap.add_argument("--expect-probe-md5", action="append", default=[], metavar="HEX")
    ap.add_argument("--station-json", default=None, help="station-account JSON (the station's only write surface)")
    ap.add_argument("--station-selftest", action="store_true", help="station selftest, nine vectors")
    args = ap.parse_args(argv)

    if args.station_selftest:
        p = station_selftest()
        print("WASH-STATION-SELFTEST (wrapper's own nine vectors; zero writes;"
              " no frozen file executed):",
              "PASS" if p else "FAIL")
        sys.exit(0 if p else 2)

    try:
        steps = parse_steps(args.steps) if args.steps else list(STEP_ORDER)
    except ValueError as e:
        print("wash_station: station-level usage error: %s" % e, file=sys.stderr)
        sys.exit(2)
    err = check_inputs(args.washed, args.baseline, steps)
    if err:
        print("wash_station: station-level usage error: %s" % err, file=sys.stderr)
        sys.exit(2)

    # precheck: canonical/target existence (a failed precheck opens zero steps; exit 9)
    root = args.root if args.root else default_root()
    canon = {}
    for s in STEP_ORDER:
        p = canonical_path(root, s)
        if not os.path.isfile(p):
            print("wash_station: canonical missing: %s (%s; repo root %s)"
                  % (CANONICALS[s]["rel"], s, root), file=sys.stderr)
            sys.exit(9)
        canon[s] = p
    for label, path in (("washed", args.washed), ("baseline", args.baseline)):
        if path and not os.path.isfile(path):
            print("wash_station: file missing: %s=%s" % (label, path), file=sys.stderr)
            sys.exit(9)

    # pinned / extra md5 assertions (a failure reports on stderr, exit 2, and never opens the run in a broken state)
    actual = {s: md5_of(canon[s]) for s in STEP_ORDER}
    expects = {"names": args.expect_names_md5, "gate4": args.expect_gate4_md5,
               "probe": args.expect_probe_md5}
    bad = []
    for s in STEP_ORDER:
        for e in expects[s]:
            v = norm_hex(e)
            if v is None or v != actual[s]:
                bad.append((s, e, actual[s]))
        if args.check_pin and CANONICALS[s]["pin"] != actual[s]:
            bad.append((s, "pin:%s" % CANONICALS[s]["pin"], actual[s]))
    if bad:
        for s, want, act in bad:
            print("wash_station: md5 assertion mismatch [%s] want=%s actual=%s"
                  % (s, want, act), file=sys.stderr)
        print("wash_station: assertion failure; the run does not open in a"
              " broken state (if a canonical was revised by the freeze"
              " authority, the wrapper agent must re-pin it)", file=sys.stderr)
        sys.exit(2)

    # open the run: steps 5->6->7 fixed order; every step reports (the composer aggregates the full account; no short-circuit)
    print("== wash_station steps 5/6/7 three-step composition (%s) ==" % WRAP_NAME)
    print("washed:   %s" % args.washed)
    print("baseline: %s" % (args.baseline or "- (names not in step)"))
    for s in STEP_ORDER:
        print("canonical[%s]: %s  md5=%s  pin_match=%s"
              % (s, canon[s], actual[s], CANONICALS[s]["pin"] == actual[s]))

    step_rows = {}
    child_stdout = {}
    for s in steps:
        if s == "names":
            full = names_cmd(canon[s], args.washed, args.baseline,
                             args.include_let, args.kinds, args.expect_names)
        elif s == "gate4":
            full = gate4_cmd(canon[s], args.washed, args.gate4_json,
                             args.gate4_no_principle, args.gate4_length_fail,
                             args.gate4_length_cap)
        else:
            full = probe_cmd(canon[s], args.washed, args.probe_json, args.probe_csv)
        print("-- %s direct call %s" % (STEP_LABEL[s], CANONICALS[s]["rel"]), file=sys.stderr)
        rc, out = run_child(full)
        verdict = gate_step({"names": NAMES_GATE, "gate4": GATE4_GATE,
                             "probe": PROBE_GATE}[s], rc)
        step_rows[s] = {"rc": rc, "verdict": verdict}
        child_stdout[s] = out

    # station-account info extraction (reporting only; never re-judges)
    info = {}
    if "names" in child_stdout:
        info.update(extract_info(child_stdout["names"], None))
    if "gate4" in child_stdout:
        info.update(extract_info(child_stdout["gate4"], None))
    if "probe" in child_stdout:
        info.update(extract_info(child_stdout["probe"], args.probe_json))

    verdicts = [step_rows[s]["verdict"] for s in steps]
    verdict, exit_code = aggregate(verdicts)

    print("--- station account: steps=%s" % "+".join(steps))
    for s in steps:
        r = step_rows[s]
        note = ""
        if s == "names" and info.get("names_assert"):
            note = "(assertion %s; total=%s)" % (info["names_assert"], info.get("names_total", "?"))
        elif s == "gate4" and info.get("gate4_summary"):
            g = info["gate4_summary"]
            note = "(files=%d PASS=%d FAIL=%d REVIEW=%d)" % (g["files"], g["pass"],
                                                             g["fail"], g["review"])
        elif s == "probe" and info.get("probe_hits_total") is not None:
            note = "(TOTAL %d candidates; E364: candidates are not verdicts)" % info["probe_hits_total"]
        print("  %s %-6s rc=%-3d %-6s %s" % (STEP_LABEL[s], s, r["rc"], r["verdict"], note))
    print("verdict: %s" % verdict)

    if args.station_json:
        acc = {
            "station": WRAP_NAME, "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "root": root, "washed": {"path": args.washed, "md5": md5_of(args.washed)},
            "baseline": ({"path": args.baseline, "md5": md5_of(args.baseline)}
                         if args.baseline and "names" in steps else None),
            "canonicals": {s: {"rel": CANONICALS[s]["rel"], "md5": actual[s],
                               "pin": CANONICALS[s]["pin"],
                               "pin_match": CANONICALS[s]["pin"] == actual[s]}
                           for s in STEP_ORDER},
            "steps": step_rows, "info": info, "verdict": verdict, "exit_code": exit_code,
        }
        with io.open(args.station_json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, ensure_ascii=False, indent=1)
        print("station-json ->", args.station_json)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
