#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_evolve.py — tests/ suite adapter for tools/evolve.py.

Purpose.  Brings the autonomous evolution engine (harvest→derive→draft,
  draft-only, human-review-gated) into the suite entry and adds usage-face
  smoke checks.  The tool's own correctness is attested by its --selftest
  vectors (canned signal injection through real subprocesses, candidate-rule
  unit judgments, draft formation, frozen exclusion, sentinel
  seen-idempotence, deterministic double run); this shell wires those
  vectors into the suite and probes the exit-code contract.

Interface.  Invoked by tests/run_tests.sh (t_evolve) or standalone:
  python3 -B tests/test_evolve.py.  Three checks:
  1 --selftest exits 0 with ten PASS vector-group lines and no FAIL line;
  2 --help exits 0 (argparse usage face present);
  3 exit-code contract spot checks: --bogus 2; missing --draft-out 2;
    no signal source 2; watch-repo without state 2; two suite sources 2;
    missing baseline 9; missing output parent 9.

Dependencies.  Python 3 standard library only (os, subprocess, sys); runs
  the tool as a subprocess with -B; no network, no compile, no writes to
  the repository (the engine selftest writes only its own mkdtemp).

Evidence.  Every check is a deterministic subprocess invocation against the
  in-repository tool; the exit-code probes were each verified by direct
  runs before being encoded here.

Exit-codes.  0 = all three checks pass; 1 = any check fails (fail-loud:
  each failure is listed on stdout, never silent).
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "evolve.py")


def run(args):
    """Run the tool as a subprocess; merged stdout+stderr, no writes."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []
    rc, out = run(["--selftest"])
    n_pass = sum(1 for line in out.splitlines() if line.startswith("PASS "))
    if rc != 0 or n_pass != 10 or "FAIL" in out:
        fails.append("check1 --selftest should exit 0 with ten PASS vector "
                     "group lines and no FAIL line (got rc=%d, PASS=%d)"
                     % (rc, n_pass))
        print(out)
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("check2 --help should exit 0 (got rc=%d)" % rc)
        print(out)
    probes = [
        (["--bogus"], 2),
        (["--json", os.path.join(REPO, "no-such-x-evolve.json")], 2),
        (["--draft-out",
          os.path.join(REPO, "no-such-draft-evolve-selftest.md")], 2),
        (["--draft-out",
          os.path.join(REPO, "no-such-draft-evolve-selftest.md"),
          "--watch-repo", "org/repo"], 2),
        (["--draft-out",
          os.path.join(REPO, "no-such-draft-evolve-selftest.md"),
          "--suite-now", "--suite-ledger",
          os.path.join(REPO, "tests", "run_tests.sh")], 2),
        (["--draft-out",
          os.path.join(REPO, "no-such-dir-evolve-selftest", "d.md"),
          "--baseline",
          os.path.join(REPO, "no-such-baseline-evolve-selftest.json")], 9),
    ]
    want = [w for _a, w in probes]
    got = []
    for args, _want in probes:
        rc_p, _out = run(args)
        got.append(rc_p)
    if got != want:
        fails.append("check3 exit-code contract should be %s (got %s)"
                     % (want, got))
    print("== test_evolve: %d pass / %d fail =="
          % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
