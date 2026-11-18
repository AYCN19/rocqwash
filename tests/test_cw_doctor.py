#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cw_doctor.py — minimal selftest shell for tools/cw_doctor.py (rocqwash tests/).

Purpose.  Wire the aggregate health doctor `tools/cw_doctor.py` into the
  suite entry point (tests/run_tests.sh, lane `t_cw_doctor`) and smoke its
  two side-effect-free faces; the doctor attests its own --selftest frozen
  vector group, and this shell adds no vectors (marker + usage face).

Interface.  python3 tests/test_cw_doctor.py      # suite lane (run_tests.sh)
  python3 -B tests/test_cw_doctor.py             # manual; -B keeps
  __pycache__ off.  Check 1: --selftest exits 0 and stdout carries the
  frozen marker "CW-DOCTOR-SELFTEST PASS"; check 2: --help exits 0 (the
  argparse usage face is present).

Dependencies.  Python 3 standard library only (os, subprocess, sys); runs
  tools/cw_doctor.py as a subprocess; zero network, zero disk writes, no
  real-repository touch (the real dyld and real probe faces stay out of
  the suite; the canned-injection face is attested by the doctor itself).

Evidence.  The doctor's --selftest frozen vectors attest the canned faces
  (V1 four domains all green 100; V2 env failing 60.0; V3 registry skip
  renormalize 86.67 + the CW_SET honest skip; V4 clog TOP injection 88.75;
  V5 advice generation; V6 JSON idempotence byte-identical; V7 CLI four
  codes; V8 the registry-audit unit — all --injector canned tmp fixtures,
  zero real otool/network/compiles); this shell re-asserts the marker and
  the usage face on every suite run.

Exit-codes.  0 = both checks pass; 1 = at least one check failing (the
  failing checks are listed loudly, never silent); a doctor failure
  surfaces through check 1.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "cw_doctor.py")
MARK = "CW-DOCTOR-SELFTEST PASS"


def run(args):
    """Run the doctor tool as a subprocess (merged stdout+stderr; zero disk
    writes, zero network)."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("check 1: --selftest expected rc=0 with %r in stdout (observed rc=%d)" % (MARK, rc))
        print(out)
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("check 2: --help expected rc=0 (observed rc=%d)" % rc)
        print(out)
    print("== test_cw_doctor: %d passing / %d failing ==" % (2 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
