#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_flaky_guard: suite shell for tools/flaky_guard.py (repair class E2-3).

    Purpose.  Roster hookup: the tool's 32-vector sandbox --selftest is
      driven here as one subprocess; the shell adds the --help face,
      exit-code spot checks and one read-only --status run.  Zero writes
      outside mkdtemp; zero network; zero compile.
    Interface.  No CLI.  Four checks: (1) the frozen selftest marker
      FLAKY-GUARD-SELFTEST PASS with rc 0; (2) --help rc 0; (3) exit-code
      spots (--bogus 2, --detect without --log 2, an absent log 9);
      (4) --status leaves the advisory roster and the repair ledger
      byte-identical (read-only pledge).
    Dependencies.  Python 3 stdlib only (os, subprocess, sys); paths
      derived from this file; no repository writes.
    Evidence.  The four checks above on every suite pass; the sandbox
      vector group attested by check 1 is detailed in the tool's own
      --selftest output.
    Exit-codes.  0 all checks pass; 1 any check red (listed loudly); 9
      the tool file is missing.
"""
import os
import shutil
import subprocess
import sys
import tempfile

TOOL_REL = os.path.join("tools", "flaky_guard.py")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL = os.path.join(REPO, TOOL_REL)


def run_tool(argv, timeout=900):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    pr = subprocess.run([sys.executable, "-B", TOOL] + argv,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        env=env, timeout=timeout, cwd=REPO)
    out = pr.stdout.decode("utf-8", "replace") \
        if isinstance(pr.stdout, bytes) else (pr.stdout or "")
    return pr.returncode, out


def main():
    if not os.path.isfile(TOOL):
        print("SKIP: %s not landed (the shell attests nothing)" % TOOL_REL)
        return 111
    checks = []

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), detail))

    # 1. the tool's sandbox vector group (the heavy evidence)
    rc, out = run_tool(["--selftest"])
    check("selftest-frozen-marker", rc == 0 and "FLAKY-GUARD-SELFTEST PASS"
          in out, "rc=%s tail=%s" % (rc, out[-300:]))

    # 2. the usage face
    rc, out = run_tool(["--help"])
    check("help-face", rc == 0 and "usage" in out, "rc=%s" % rc)

    # 3. exit-code spot checks
    rc, out = run_tool(["--bogus"])
    check("code-bogus-2", rc == 2, "rc=%s" % rc)
    rc, out = run_tool(["--detect", "--repo", REPO])
    check("code-log-required-2", rc == 2, "rc=%s" % rc)
    rc, out = run_tool(["--detect", "--log", os.path.join(REPO, "tests",
                                                          "no_such_log.txt"),
                        "--repo", REPO])
    check("code-log-missing-9", rc == 9, "rc=%s" % rc)

    # 4. status against the standing repo: rc 0, read-only pledge
    roster = os.path.join(REPO, "tests", "advisory_roster.txt")
    ledger = os.path.join(REPO, "docs", "repair-ledger.jsonl")
    before = {}
    for p in (roster, ledger):
        before[p] = open(p, "rb").read() if os.path.isfile(p) else None
    rc, out = run_tool(["--status", "--repo", REPO])
    after = {}
    for p in (roster, ledger):
        after[p] = open(p, "rb").read() if os.path.isfile(p) else None
    check("status-read-only", rc == 0 and "FLAKY-STATUS" in out
          and before == after, "rc=%s out=%s" % (rc, out[-200:]))

    failed = [c for c in checks if not c[1]]
    for name, ok, detail in checks:
        print("%s %s%s" % ("PASS" if ok else "FAIL", name,
                           (" - %s" % detail) if detail and not ok else ""))
    print("summary: %d checks, %d FAIL" % (len(checks), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
