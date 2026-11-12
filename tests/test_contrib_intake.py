#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_contrib_intake.py — tests/ suite shell for tools/contrib_intake.py.

Purpose.  Hook the contribution intake inspector into the tests/ suite and
  smoke its usage face; the inspector's own dual-clone four-gate vector
  group runs under its --selftest and is attested by its frozen marker
  line, so this shell re-runs it rather than re-implementing any gate.

Interface.  `python3 tests/test_contrib_intake.py` (suite entry:
  tests/run_tests.sh case t_contrib_intake).  Three checks: --selftest
  rc=0 with the `CONTRIB-INTAKE-SELFTEST PASS` marker; --help rc=0 with a
  usage face; exit-code convention spot checks (--bogus=2, no input=2,
  missing contrib face=9, unresolvable contrib ref=9 — the same four-code
  shape the tool's own selftest asserts).

Dependencies.  Python 3 stdlib only; the inspected tool is stdlib-only and
  builds its own temporary git-clone fixtures under --selftest; the base
  face of the spot checks points at this repository (a valid local git
  repository, read-only); zero network.

Evidence.  Every check here runs the tool in a subprocess and asserts the
  exit code on this machine; the four-gate vector group is attested by the
  tool's own --selftest marker, never inferred.

Exit-codes.  0 = all three checks pass; 1 = any check red (fail-loud,
  the red check is printed; no silent downgrade).
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "contrib_intake.py")
MARK = "CONTRIB-INTAKE-SELFTEST PASS"


def run(args):
    """Run the inspector in a subprocess (stdout+stderr merged)."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("check1 --selftest should be rc=0 with %r (rc=%d)"
                     % (MARK, rc))
        print(out)
    rc, out = run(["--help"])
    if rc != 0 or "usage" not in out:
        fails.append("check2 --help should be rc=0 with a usage face "
                     "(rc=%d)" % rc)
        print(out)
    # exit-code convention spot checks; the base face is this repository
    # (a valid local git repository, read-only for the inspector)
    rc_b, _ = run(["--bogus"])
    rc_n, _ = run([])
    rc_m, _ = run(["--contrib-repo", os.path.join(REPO, "no-such-face"),
                   "--contrib-ref", "x", "--base-repo", REPO,
                   "--base-ref", "main"])
    rc_r, _ = run(["--contrib-repo", REPO, "--contrib-ref", "no-such-ref",
                   "--base-repo", REPO, "--base-ref", "main"])
    if not (rc_b == 2 and rc_n == 2 and rc_m == 9 and rc_r == 9):
        fails.append("check3 exit codes should be bogus=2/no-input=2/"
                     "missing-face=9/bad-ref=9 (got %d/%d/%d/%d)"
                     % (rc_b, rc_n, rc_m, rc_r))
    print("== test_contrib_intake: %d pass / %d red =="
          % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
