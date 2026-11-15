#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_watch_repo_form.py - SEED S2 negative-vector tests for the
cw_sentinel --watch-repo ORG/REPO form contract.

Purpose.  Pin the existing cw_sentinel contract (the argv scan rejects a
  non ORG/REPO value with rc=2) as executable assertions so the negative
  vector is guarded by the suite: (1) a local-directory form (drive letter
  / path separators) is rejected with rc=2 and the ORG/REPO message;
  (2) a bare token without "/" is rejected with rc=2; (3) the source
  record stays anchored (tools/cw_sentinel.py carries the REPO_RE match
  gate at the recorded site).
Interface.  python3 tests/test_watch_repo_form.py (via run_tests.sh) or
  python -B tests/test_watch_repo_form.py (manual).
Dependencies.  Python 3 standard library only; the sibling
  tools/cw_sentinel.py.
Evidence.  Vectors 1-2 run the tool as a subprocess under `python -I`
  (no network is reached: the form check fires before any fetch). The
  child emits UTF-8, so the parent decodes with encoding="utf-8",
  errors="replace" (the locale codec mangles the message face on this
  lane). Fixtures are synthetic paths only; zero writes outside the temp
  face of the subprocess.
Exit-codes.  0 = all checks pass; 1 = any check red (fail loud).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SENTINEL = os.path.join(ROOT, "tools", "cw_sentinel.py")
PY = sys.executable or "python"


def run(args):
    p = subprocess.run(
        [PY, "-I", "-X", "utf8", SENTINEL] + args,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        cwd=ROOT,
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    fails = []

    # vector 1: local-directory form -> rc=2, ORG/REPO message
    rc, out = run(["--watch-repo", "D:/ComplexAnalysis/rocqwash", "--once"])
    if rc != 2:
        fails.append("v1 local-path form: want rc=2 got rc=%s" % rc)
    if "ORG/REPO" not in out:
        fails.append("v1 local-path form: message missing ORG/REPO face")

    # vector 2: bare token without "/" -> rc=2
    rc, out = run(["--watch-repo", "justrepo", "--once"])
    if rc != 2:
        fails.append("v2 bare token: want rc=2 got rc=%s" % rc)
    if "ORG/REPO" not in out:
        fails.append("v2 bare token: message missing ORG/REPO face")

    # vector 3: source anchor stays in place (REPO_RE gate)
    src = open(SENTINEL, encoding="utf-8").read()
    if "REPO_RE.match(val)" not in src:
        fails.append("v3 source anchor: REPO_RE.match gate missing")

    if fails:
        for f in fails:
            print("FAIL: %s" % f)
        print("test_watch_repo_form: %d red" % len(fails))
        return 1
    print("test_watch_repo_form: 3 checks pass (local-path rc=2, "
          "bare-token rc=2, source anchor present)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
