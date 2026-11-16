#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_roster_resync.py: suite hookup shell for tools/roster_resync.py (tests/; E2 repair class 2 roster hookup, 20261116).

Purpose.  Wires the roster count drift guard into the suite entry: the
  guard's own tmp-fixture selftest vectors (the real doc_lint consistent
  verdict as the green criterion, the one-way roster discipline, the
  budget cap, the shared repair_scope gate) are attested by the guard's
  --selftest; this shell only drives the argparse faces and the exit-code
  convention, plus the shared-exclusion module's selftest through the
  guard's own first vector.

Interface.  python3 tests/test_roster_resync.py  (suite entry via
  run_tests.sh t_roster_resync; zero arguments).

Dependencies.  Python 3 standard library only; subprocess drives the
  real tools/roster_resync.py CLI; zero network; zero writes outside the
  system temp dir; zero real-repo contact.

Evidence.  Four checks: (1) --selftest rc=0 with the
  ROSTER-RESYNC-SELFTEST PASS frozen marker; (2) --help rc=0 (the usage
  face); (3) --bogus=2; (4) a missing --repo directory=9.

Exit-codes.  0 all checks pass; 1 any check red (fail-loud, listed).
"""

import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "roster_resync.py")
MARK = "ROSTER-RESYNC-SELFTEST PASS"


def run(args):
    """One subprocess of the guard (stdout+stderr merged; zero writes
    outside the tmp fixture the guard itself manages)."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def main():
    fails = []
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("check 1 --selftest should be rc=0 with %r"
                     " (got rc=%d)" % (MARK, rc))
        print(out)
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("check 2 --help should be rc=0 (got rc=%d)" % rc)
        print(out)
    rc, _out = run(["--bogus"])
    if rc != 2:
        fails.append("check 3a --bogus should be rc=2 (got rc=%d)" % rc)
    absent = tempfile.mkdtemp(prefix="rqw_roster_resync_shell_")
    try:
        rc, _out = run(["--repo", absent])
        if rc != 9:
            fails.append("check 3b a missing --repo should be rc=9"
                         " (got rc=%d)" % rc)
    finally:
        import shutil
        shutil.rmtree(absent, ignore_errors=True)
    print("== test_roster_resync: %d pass / %d red =="
          % (4 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
