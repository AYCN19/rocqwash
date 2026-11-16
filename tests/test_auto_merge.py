#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_auto_merge: suite shell for tools/auto_merge.py (X5 gate judge).

    Purpose.  Roster hookup: the tool's 24-vector --selftest is driven
      here as one subprocess; the shell adds the --help face, the
      exit-code spots, the five calibration fixtures judged through the
      real CLI face to their pinned verdicts, and the dry-run zero-write
      pledge.  Zero writes inside the repository; zero network.
    Interface.  No CLI.  Five checks: (1) the frozen selftest marker
      AUTO-MERGE-SELFTEST PASS with rc 0; (2) --help rc 0 naming the
      judge and rail flags; (3) exit-code spots (--bogus 2, --selftest
      with --facts 2, --facts omitted 2, absent facts file 9, malformed
      JSON 9); (4) the five fixtures S-1..S-5 through --facts each rc 0
      with AUTO-MERGE-VERDICT pinned (already-landed /
      superseded-landed-elsewhere / merge-ok / superseded-landed-elsewhere
      / hold-red); (5) a merge-ok fact with a supply/* head on a tmp
      ledger runs dry (rc 0, ledger never created) while a foreign head
      is refused with rc 1.
    Dependencies.  Python 3 stdlib only (json, os, subprocess, sys,
      tempfile, shutil); paths derived from this file; tmpdir fixtures.
    Evidence.  The five checks above on every suite pass; the frozen
      vector group attested by check 1 is detailed in the tool's own
      --selftest output.
    Exit-codes.  0 all checks pass; 1 any check red (listed loudly); 9
      the tool file is missing.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

TOOL_REL = os.path.join("tools", "auto_merge.py")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL = os.path.join(REPO, TOOL_REL)

FIXTURES = (
    ("s1", "already-landed"),
    ("s2", "superseded-landed-elsewhere"),
    ("s3", "merge-ok"),
    ("s4", "superseded-landed-elsewhere"),
    ("s5", "hold-red"),
)


def run_tool(argv, timeout=300):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    pr = subprocess.run([sys.executable, "-B", TOOL] + argv,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        env=env, timeout=timeout, cwd=REPO)
    out = pr.stdout.decode("utf-8", "replace") \
        if isinstance(pr.stdout, bytes) else (pr.stdout or "")
    return pr.returncode, out


def verdict_line(out):
    for line in out.splitlines():
        if line.startswith("AUTO-MERGE-VERDICT:"):
            return line.split(":", 1)[1].strip()
    return ""


def main():
    if not os.path.isfile(TOOL):
        print("SKIP: %s not landed (the shell attests nothing)" % TOOL_REL)
        return 111
    checks = []

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), detail))

    tmp = tempfile.mkdtemp(prefix="auto_merge_shell_")
    try:
        # 1. the tool's frozen vector group (the heavy evidence)
        rc, out = run_tool(["--selftest"])
        check("selftest-frozen-marker",
              rc == 0 and "AUTO-MERGE-SELFTEST PASS" in out,
              "rc=%s tail=%s" % (rc, out[-300:]))

        # 2. the usage face names the judge and rail flags
        rc, out = run_tool(["--help"])
        want_flags = ("--facts", "--head-branch", "--allow-prefix",
                      "--daily-cap", "--ledger", "--post-merge", "--apply")
        check("help-face", rc == 0
              and all(f in out for f in want_flags),
              "rc=%s missing=%s" % (rc,
                                    [f for f in want_flags if f not in out]))

        # 3. exit-code spot checks
        rc, _ = run_tool(["--bogus"])
        check("exit-bogus-2", rc == 2, "rc=%s" % rc)
        rc, _ = run_tool(["--selftest", "--facts", "x.json"])
        check("exit-selftest-with-facts-2", rc == 2, "rc=%s" % rc)
        rc, _ = run_tool([])
        check("exit-missing-facts-2", rc == 2, "rc=%s" % rc)
        rc, _ = run_tool(["--facts",
                          os.path.join(tmp, "absent.json")])
        check("exit-absent-facts-9", rc == 9, "rc=%s" % rc)
        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        rc, _ = run_tool(["--facts", bad])
        check("exit-malformed-facts-9", rc == 9, "rc=%s" % rc)

        # 4. the five calibration fixtures through the real CLI face
        for name, want in FIXTURES:
            path = os.path.join(HERE, "fixtures",
                                "auto_merge_%s.json" % name)
            rc, out = run_tool(["--facts", path])
            got = verdict_line(out)
            check("fixture-%s" % name,
                  rc == 0 and got == want, "rc=%s want=%s got=%s"
                  % (rc, want, got))

        # 5. dry-run zero-write plus the rail refusal exit contract
        s3 = os.path.join(HERE, "fixtures", "auto_merge_s3.json")
        ledger = os.path.join(tmp, "ledger.jsonl")
        rc, out = run_tool(["--facts", s3, "--head-branch",
                            "supply/seat-pack", "--ledger", ledger])
        check("rail-dry-run-zero-write",
              rc == 0 and "AUTO-MERGE-RAIL: allowed" in out
              and not os.path.exists(ledger), "rc=%s" % rc)
        rc, out = run_tool(["--facts", s3, "--head-branch",
                            "feature/quick-fix", "--ledger", ledger])
        check("rail-refusal-exit-1",
              rc == 1
              and "refused:branch-whitelist" in out, "rc=%s" % rc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    reds = [c for c in checks if not c[1]]
    for name, ok, detail in checks:
        print("  %s  %-36s %s" % ("ok " if ok else "RED", name, detail))
    if reds:
        print("TEST-AUTO-MERGE RED (%d/%d red)" % (len(reds), len(checks)))
        return 1
    print("TEST-AUTO-MERGE PASS (%d checks)" % len(checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
