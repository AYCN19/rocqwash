#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_registry_audit.py — minimal selftest shell for tools/registry_audit.py
(rocqwash tests/).

Purpose.  Wire the registry hygiene auditor `tools/registry_audit.py` into
  the suite entry point (tests/run_tests.sh, lane `t_registry_audit`) and
  smoke its usage faces; the auditor itself (four read-only audits over
  the order.txt/_CoqProject book pair, findings are data) is attested by
  its own --selftest, so this shell adds no vectors.

Interface.  python3 tests/test_registry_audit.py    # suite lane
  (tests/run_tests.sh); python3 -B tests/test_registry_audit.py    # manual
  (-B keeps __pycache__ off).  Check 1: --selftest exits 0 and stdout
  carries the frozen marker "REGISTRY-AUDIT-SELFTEST PASS"; check 2:
  --help exits 0 (the argparse usage face is present); check 3: exit-code
  sampling -- --bogus rc=2, no input form rc=2, one book of the pair
  missing rc=2, both book files missing rc=9.

Dependencies.  Python 3 standard library only (os, subprocess, sys); runs
  tools/registry_audit.py as a subprocess; zero network, zero compilation,
  zero repository writes (the selftest fixtures are synthetic tmp files
  plus a tmp clone, self-cleaning).

Evidence.  The auditor's --selftest vector group attests the audit behavior
  (vector roster in the extended contract comment below); this shell
  re-asserts the marker and usage faces every suite run (wired in
  November 12, 2026).

Exit-codes.  0 = all three checks pass; 1 = at least one check failing
  (the failing checks are listed loudly, never silent).
"""

# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard).  The auditor's
# --selftest vector roster, run by the tool itself, offline, zero network,
# zero compilation: the full finding-class spectrum (duplicate rows,
# anchor-text collisions, seq-form and malformed anchors, missing anchors,
# cross-book orphans, live topology) on tmp synthetic v35-ledger-shape
# fixtures; the deterministic --fix-plan with keep-first rows; the frozen
# registry_union md5 vector 77c2b9a8; placeholder and read-only proofs
# (book pair and live tree md5 unchanged before/after); byte-identical
# reruns; the --git form on a tmp clone (bad ref exits 9); CLI exit codes.
# Report schema rocqwash-registry-audit/1.

import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "registry_audit.py")
MARK = "REGISTRY-AUDIT-SELFTEST PASS"


def run(args):
    """Run the auditor as a subprocess (merged stdout+stderr; zero writes,
    zero network, zero compilation)."""
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
    rc_b, _o = run(["--bogus"])
    rc_e, _o = run([])
    rc_h, _o = run(["--order", os.path.join(REPO, "tests", "fixtures",
                                             "names_sample.v")])
    rc_m, _o = run(["--order", os.path.join(REPO, "no-such-order.txt"),
                    "--project", os.path.join(REPO, "no-such-project.txt")])
    if not (rc_b == 2 and rc_e == 2 and rc_h == 2 and rc_m == 9):
        fails.append("check 3: exit codes expected bogus=2 / no input form=2 / one book of the pair=2 / both books missing=9 (observed %d/%d/%d/%d)" % (rc_b, rc_e, rc_h, rc_m))
    print("== test_registry_audit: %d passing / %d failing ==" % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
