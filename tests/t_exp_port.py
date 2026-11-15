#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_exp_port.py — tests/ suite shell for tools/exp_port.py.

Purpose.  Hook the experience-bus port into the tests/ suite and smoke its
  usage face; the port's own fixture vector group (append/idempotent seen
  set/dry-run zero-write/carried id and provenance/corrupt-ledger fail
  loud/query vectors/minted-id sequence) runs under --selftest and is
  attested by its frozen marker line.

Interface.  `python3 tests/t_exp_port.py` (rostered in tests/run_tests.sh
  as case t_exp_port on 20261115, audit finding P0-6; the roster count is
  derived one-way from the CASES block in tests/run_tests.sh by doc_lint's
  second check).
  Four checks: --selftest rc=0 with the `EXP-PORT-SELFTEST PASS` marker;
  --help rc=0 with a usage face; exit-code convention spot checks
  (--bogus=2, append without --points=2, query on an absent ledger=9);
  a copy dry-run: append --dry-run against a copy of the ledger in a
  temporary directory reports a would-be id and writes nothing.

Dependencies.  Python 3 stdlib only; the inspected tool is stdlib-only;
  every check runs on temporary fixtures or nonexistent scratch paths;
  nothing on this repository is written; zero network.

Evidence.  Every check here runs the tool in a subprocess and asserts the
  exit code and output face on this machine; the fixture vector group is
  attested by the tool's own --selftest marker, never inferred.

Exit-codes.  0 = all four checks pass; 1 = any check red (fail-loud, the
  red check is printed; no silent downgrade).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "exp_port.py")
MARK = "EXP-PORT-SELFTEST PASS"


def run(args, cwd=None):
    """Run the port in a subprocess (stdout+stderr merged)."""
    p = subprocess.run([sys.executable, "-B", "-I", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       cwd=cwd)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []

    # Check 1: the port's own fixture vector group attests green.
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("check1 --selftest should be rc=0 with %r (rc=%d)\n%s"
                     % (MARK, rc, out))

    # Check 2: --help is a clean usage face (argparse hyphen-wrap repair,
    # doc_lint precedent: a "--tok\n<ws>cont" break rejoins to the token).
    rc, out = run(["--help"])
    flat = re.sub(r"-\s*\n\s*", "-", out)
    if rc != 0 or "rocqwash-exp/1" not in flat or "append" not in flat:
        fails.append("check2 --help should be rc=0 naming the schema and "
                     "append (rc=%d)\n%s" % (rc, out))

    # Check 3: exit-code convention spot checks on scratch paths only.
    rc, _ = run(["--bogus"])
    if rc != 2:
        fails.append("check3 --bogus should exit 2, got %d" % rc)
    scratch = os.path.join(tempfile.gettempdir(), "exp_port_no_such_ledger")
    rc, _ = run(["append", "--tool", "t"])  # missing required --points
    if rc != 2:
        fails.append("check3 append without --points should exit 2, got %d" % rc)
    rc, _ = run(["query", "--ledger", scratch])
    if rc != 9:
        fails.append("check3 query on an absent ledger should exit 9, got %d" % rc)

    # Check 4: copy dry-run — a temporary copy of the repo ledger face;
    # the port reports a would-be id and the copy stays byte-identical.
    tmp = tempfile.mkdtemp(prefix="t_exp_port_copy_")
    try:
        copy_ledger = os.path.join(tmp, "exp-ledger.jsonl")
        with open(copy_ledger, "w", encoding="utf-8") as handle:
            handle.write('{"batch":"b","evidence":"e","fingerprint":"f1",'
                         '"id":"EXP-19700101-0001","points":"p","schema":'
                         '"rocqwash-exp/1","tool":"t"}\n')
        before = open(copy_ledger, "rb").read()
        rc, out = run(["append", "--tool", "t2", "--points", "p2",
                       "--ledger", copy_ledger, "--dry-run"])
        after = open(copy_ledger, "rb").read()
        if rc != 0 or "dry-run id=" not in out:
            fails.append("check4 copy dry-run should report dry-run id= rc=0 "
                         "(rc=%d)\n%s" % (rc, out))
        if before != after:
            fails.append("check4 copy dry-run must not write any byte")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for line in fails:
            sys.stderr.write("T_EXP_PORT FAIL %s\n" % line)
        return 1
    sys.stdout.write("T-EXP-PORT SUITE SHELL PASS (4 checks)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
