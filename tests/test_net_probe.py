#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_net_probe.py - minimal selftest shell for tools/net_probe.py (tests/).

Purpose.  Hook the network-window probe into the suite entry point: the
  probe carries its own --selftest zero-network vector group (classification,
  round shape, verdict levels, stable-window decisions, CLI codes) already
  self-attested on the tool face; this shell runs it and adds a --help
  smoke check.

Interface.  python3 tests/test_net_probe.py; no flags or arguments; called
  from tests/run_tests.sh as lane t_net_probe.

Dependencies.  Python 3 standard library only (os, subprocess, sys); spawns
  the local tool via sys.executable -B (no __pycache__ artifacts); zero
  network, zero writes, zero real-probe runs in the suite.

Evidence.  Two checks: 1 --selftest returns rc 0 and stdout carries the
  frozen marker "NET-PROBE-SELFTEST PASS"; 2 --help returns rc 0 (the
  argparse usage face is present).  One pass/fail roll-up line carries the
  counts; failures are listed loudly, never silenced.

Exit-codes.  0 = both checks pass; 1 = any check failing.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "net_probe.py")
MARK = "NET-PROBE-SELFTEST PASS"


def run(args):
    """Run the probe in a subprocess (stdout and stderr merged, zero writes,
    zero network)."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("check 1 --selftest must return rc=0 and contain %r"
                     " (got rc=%d)" % (MARK, rc))
        print(out)
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("check 2 --help must return rc=0 (got rc=%d)" % rc)
        print(out)
    print("== test_net_probe: %d pass / %d fail ==" % (2 - len(fails),
                                                       len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
