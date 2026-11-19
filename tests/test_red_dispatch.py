#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_red_dispatch.py — minimal selftest shell for tools/red_dispatch.py
(rocqwash tests/).

Purpose.  Wire the red-event router `tools/red_dispatch.py` into the suite
  entry point (tests/run_tests.sh, lane `t_red_dispatch`) and smoke its
  usage faces; the router itself (three action-preset tiers report-only /
  suggest / auto, schema rocqwash-red-route/1) is attested by its own
  --selftest, so this shell adds no vectors.

Interface.  python3 tests/test_red_dispatch.py    # suite lane
  (tests/run_tests.sh); python3 -B tests/test_red_dispatch.py    # manual
  (-B keeps __pycache__ off).  Check 1: --selftest exits 0 and stdout
  carries the frozen marker "RED-DISPATCH-SELFTEST PASS"; check 2: --help
  exits 0 (the argparse usage face is present); check 3: exit-code
  sampling -- --bogus rc=2, --dry-run without an explicit auto tier rc=2,
  missing event file rc=9.

Dependencies.  Python 3 standard library only (os, subprocess, sys); runs
  tools/red_dispatch.py as a subprocess; zero network, zero compilation,
  zero repository writes (the selftest stages are mkdtemp, self-cleaning).

Evidence.  The router's --selftest frozen twelve-vector group attests the
  routing behavior on a fake temporary repository root (vector roster in
  the extended contract comment below); this shell re-asserts the marker
  and usage faces every suite run (wired in November 12, 2026).

Exit-codes.  0 = all three checks pass; 1 = at least one check failing
  (the failing checks are listed loudly, never silent).
"""

# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard).  The router's
# --selftest vector roster, run by the tool itself on a fake temporary
# repository root, offline, zero network, zero compilation: 1 route-table
# family coverage; 2 placeholder substitution; 3 auto-execution proof;
# 4 de-duplication state; 5 cooldown; 6 report-only default executes
# nothing; 7 JSONL stdin multi-event; 8 fail-loud face; 9 a failing child
# rc is recorded without changing the exit code; 10 family-A fix list +
# family-C scheduled command; 11 determinism; 12 single-object fallback.

import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "red_dispatch.py")
MARK = "RED-DISPATCH-SELFTEST PASS"


def run(args):
    """Run the router as a subprocess (merged stdout+stderr; zero writes,
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
    rc_d, _o = run(["--dry-run", "--preset", "report-only"])
    rc_m, _o = run(["--event-file", os.path.join(REPO, "no-such-events.jsonl")])
    if not (rc_b == 2 and rc_d == 2 and rc_m == 9):
        fails.append("check 3: exit codes expected bogus=2 / dry-run wrong tier=2 / missing event file=9 (observed %d/%d/%d)" % (rc_b, rc_d, rc_m))
    print("== test_red_dispatch: %d passing / %d failing ==" % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
