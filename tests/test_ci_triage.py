#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ci_triage.py — minimal selftest shell for tools/ci_triage.py (rocqwash tests/).

Purpose.  Wire the failing-build triage tool into the suite entry point
  (tests/run_tests.sh, lane `t_ci_triage`) and smoke its usage face; the
  triage tool attests its own --selftest offline vector group, and this
  shell adds no vectors (marker + usage face).

Interface.  python3 tests/test_ci_triage.py    # suite lane (run_tests.sh);
  python3 -B tests/test_ci_triage.py  # manual; -B keeps __pycache__ off.
  Check 1: --selftest exits 0 and stdout carries the frozen marker
  "CI-TRIAGE-SELFTEST PASS"; check 2: --help exits 0 (the argparse usage
  face is present).

Dependencies.  Python 3 standard library only (os, subprocess, sys); runs
  tools/ci_triage.py as a subprocess; zero network, zero disk writes, no
  real-repository touch (the real API face stays out of the suite; the
  --offline mode is attested by the tool's own selftest).

Evidence.  The triage tool's --selftest offline vector group (the
  five-family taxonomy plus the all-passing state, six offline samples
  all classified; the baseline 13.3x ratio case; the off-spectrum
  UNRECOGNIZED class) is self-documented in tools/ci_triage.py; this
  shell re-asserts the marker and usage face on every suite run.

Exit-codes.  0 = both checks pass; 1 = at least one check failing (the
  failing checks are listed loudly, never silent).
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "ci_triage.py")
MARK = "CI-TRIAGE-SELFTEST PASS"


def run(args):
    """Run the triage tool in a subprocess (stdout+stderr merged; zero disk
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
    print("== test_ci_triage: %d passing / %d failing =="
          % (2 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
