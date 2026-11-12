#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_registry_regen.py — tests/ suite shell for tools/registry_regen.py.

Purpose.  Hook the contribution registration-row regenerator into the
  tests/ suite and smoke its usage face; the regenerator's own fixture
  vector group (topological regeneration, missing-dependency BLOCK, the
  frozen md5 vector, blast and divergence cases) runs under --selftest
  and is attested by its frozen marker line.

Interface.  `python3 tests/test_registry_regen.py` (suite entry:
  tests/run_tests.sh case t_registry_regen).  Three checks: --selftest
  rc=0 with the `REGISTRY-REGEN-SELFTEST PASS` marker; --help rc=0 with a
  usage face; exit-code convention spot checks (--bogus=2, no input=2,
  --apply without --out=2, negative --seq=2, missing base repository=9).

Dependencies.  Python 3 stdlib only; the inspected tool is stdlib-only
  and builds its own temporary git-clone fixtures under --selftest; the
  spot checks use only nonexistent scratch paths, so nothing on this
  repository is written or read as input; zero network.

Evidence.  Every check here runs the tool in a subprocess and asserts the
  exit code on this machine; the fixture vector group is attested by the
  tool's own --selftest marker, never inferred.

Exit-codes.  0 = all three checks pass; 1 = any check red (fail-loud,
  the red check is printed; no silent downgrade).
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "registry_regen.py")
MARK = "REGISTRY-REGEN-SELFTEST PASS"
NO_SUCH = os.path.join(REPO, "no-such-regen-scratch")


def run(args):
    """Run the regenerator in a subprocess (stdout+stderr merged)."""
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
    # exit-code convention spot checks (all vectors are usage/missing-input
    # faces the tool detects before any read or write)
    rc_b, _ = run(["--bogus"])
    rc_n, _ = run([])
    rc_a, _ = run(["--base-repo", NO_SUCH, "--base-ref", "main",
                   "--contrib-repo", NO_SUCH, "--contrib-ref", "x",
                   "--pieces", "A", "--anchor-src", NO_SUCH, "--apply"])
    rc_s, _ = run(["--base-repo", NO_SUCH, "--base-ref", "main",
                   "--contrib-repo", NO_SUCH, "--contrib-ref", "x",
                   "--pieces", "A", "--anchor-src", NO_SUCH, "--seq", "-1"])
    rc_m, _ = run(["--base-repo", NO_SUCH, "--base-ref", "main",
                   "--contrib-repo", NO_SUCH, "--contrib-ref", "x",
                   "--pieces", "A", "--anchor-src", NO_SUCH])
    if not (rc_b == 2 and rc_n == 2 and rc_a == 2 and rc_s == 2
            and rc_m == 9):
        fails.append("check3 exit codes should be bogus=2/no-input=2/"
                     "apply-without-out=2/negative-seq=2/missing-base=9 "
                     "(got %d/%d/%d/%d/%d)"
                     % (rc_b, rc_n, rc_a, rc_s, rc_m))
    print("== test_registry_regen: %d pass / %d red =="
          % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
