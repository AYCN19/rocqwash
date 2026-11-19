#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cw_sentinel.py - suite hookup shell for tools/cw_sentinel.py (tests/).

Purpose.  The sentinel already attests itself: its own --selftest carries
  the frozen vector set (the thirteen canned-injection vectors, all over
  the --injector canned path with tmp fixtures: zero real network, zero
  compile).  This shell only connects that selftest into the suite entry
  and adds a --help smoke check:
  1 --selftest rc=0 and stdout carries the frozen "CW-SENTINEL-SELFTEST
    PASS" marker;
  2 --help rc=0 (the argparse usage face is in place).

Interface.  python3 tests/test_cw_sentinel.py       # from run_tests.sh in
    the suite;  python3 -B tests/test_cw_sentinel.py  # manual (-B disables
    __pycache__).

Dependencies.  Python 3 standard library only (os, subprocess, sys); the
  tool face tools/cw_sentinel.py on disk.  Zero-touch rule: zero network,
  zero writes, zero touches of the real repository (the real API face is
  never hooked into the suite; the canned injection face is attested by the
  sentinel's own selftest); python3 -B disables __pycache__.

Evidence.  Both checks fail loud: any red prints the captured sentinel
  output and the failing condition, then exits 1 (never silent).  Suite
  hookup: t_cw_sentinel in tests/run_tests.sh.

Exit-codes.  0 = both checks pass; 1 = either check red.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "cw_sentinel.py")
MARK = "CW-SENTINEL-SELFTEST PASS"


def run(args):
    """Run the sentinel in a subprocess (stdout+stderr merged; zero writes,
    zero network)."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("check 1: --selftest must exit 0 and print %r (got rc=%d)"
                     % (MARK, rc))
        print(out)
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("check 2: --help must exit 0 (got rc=%d)" % rc)
        print(out)
    print("== test_cw_sentinel: %d pass / %d red ==" % (2 - len(fails),
                                                        len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
