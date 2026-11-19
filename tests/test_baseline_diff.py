#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_baseline_diff.py — minimal selftest shell for tools/baseline_diff.py (rocqwash tests/).

Purpose.  Wire the blockage-record baseline comparator (schema
  rocqwash-baseline-diff/1) into the suite entry point (tests/run_tests.sh,
  lane `t_baseline_diff`) and smoke its usage and exit-code faces; the
  comparator attests its own --selftest frozen vector group, and this
  shell adds no vectors (marker + usage face).

Interface.  python3 tests/test_baseline_diff.py    # suite lane
  (run_tests.sh); python3 -B tests/test_baseline_diff.py  # manual; -B
  keeps __pycache__ off.  Check 1: --selftest exits 0 and stdout carries
  the frozen marker "BASELINE-DIFF-SELFTEST PASS"; check 2: --help exits
  0 (the argparse usage face is present); check 3: exit-code sampling.

Dependencies.  Python 3 standard library only (os, subprocess, sys); runs
  tools/baseline_diff.py as a subprocess; zero network, zero disk writes,
  no real-repository touch (the tool's --selftest synthesizes its
  baselines in tmp directories it writes and cleans itself).

Evidence.  The comparator's --selftest frozen vector group (improved / degraded
  (wall-cause change) / stable (timing excluded, json+md reruns byte-identical) /
  incomparable (candidate-set difference, non-audit form) / md output / CLI four
  codes with malformed-form rejection) is self-documented in tools/baseline_diff.py;
  this shell re-asserts the marker and usage face and samples the exit-code
  convention (0=improved/stable, 1=degraded/incomparable — a failing result is
  data, not a tool failure; 2=usage error or malformed input; 9=path missing).

Exit-codes.  0 = all three checks pass; 1 = at least one check failing
  (the failing checks are listed loudly, never silent).
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "baseline_diff.py")
MARK = "BASELINE-DIFF-SELFTEST PASS"


def run(args):
    """Run the comparator in a subprocess (stdout+stderr merged; zero disk
    writes, zero network)."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("check 1: --selftest expected rc=0 with %r in stdout"
                     " (observed rc=%d)" % (MARK, rc))
        print(out)
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("check 2: --help expected rc=0 (observed rc=%d)" % rc)
        print(out)
    rc_b, _o = run(["--bogus"])
    rc_c, _o = run([])
    rc_m, _o = run([os.path.join(REPO, "no-such-audit.json"),
                    os.path.join(REPO, "no-such-audit-2.json")])
    if not (rc_b == 2 and rc_c == 2 and rc_m == 9):
        fails.append("check 3: exit codes expected bogus=2 / no-arguments=2"
                     " / missing-file=9 (observed %d/%d/%d)"
                     % (rc_b, rc_c, rc_m))
    print("== test_baseline_diff: %d passing / %d failing =="
          % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
