#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_toolchain_dyld_doctor.py — minimal selftest shell for tools/toolchain_dyld_doctor.py (tests/).
Purpose.  Hooks the dyld toolchain linkage-failure diagnostician into the suite
  entry: the tool carries its own full offline --selftest vector group (otool
  sample parsing / system-prefix drop with external keep / exists-missing /
  same-basename fallback / CLI codes; zero real otool, zero compiles, zero
  network), self-attested there; this shell wires it into the suite and adds a
  --help smoke: (1) --selftest exits 0 and stdout contains the frozen
  "DYLD-DOCTOR-SELFTEST PASS" marker; (2) --help exits 0 (the argparse usage
  face is present).
Interface.  python3 tests/test_toolchain_dyld_doctor.py (called from the suite
  via run_tests.sh) or python3 -B tests/test_toolchain_dyld_doctor.py (manual;
  -B keeps __pycache__ off); no flags; two subprocess checks of the tool.
Dependencies.  Python 3 standard library only (os, subprocess, sys); spawns the
  local tool via sys.executable -B; zero real otool, zero compiles, zero
  network, zero writes, zero touches of the real repository.
Evidence.  Registered as t_toolchain_dyld_doctor in tests/run_tests.sh and
  tests/README.md; the underlying vector group is attested by the tool's
  --selftest (frozen marker "DYLD-DOCTOR-SELFTEST PASS").
Exit-codes.  0 = both checks passing; 1 = any check failing (loud per-check
  listing, no silent downgrade); 111 = honest skip on a non-POSIX host (the
  canned otool stub is a shell script), reported as SKIP, never a silent pass.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "toolchain_dyld_doctor.py")
MARK = "DYLD-DOCTOR-SELFTEST PASS"


def run(args):
    """Run the diagnostician in a subprocess (stdout+stderr merged; zero
    writes, zero network)."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []
    skipped = False
    rc, out = run(["--selftest"])
    if rc == 111 and "SKIP" in out:
        # Honest skip: the canned otool stub is a POSIX shell script, so the
        # CLI vector cannot run on a non-POSIX host. A skip is not a failure;
        # report it with the repo's honest-skip code so the suite records it
        # as SKIP rather than red.
        skipped = True
        print(out)
    elif rc != 0 or MARK not in out:
        fails.append("check1 --selftest must exit 0 and contain %r (got rc=%d)"
                     % (MARK, rc))
        print(out)
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("check2 --help must exit 0 (got rc=%d)" % rc)
        print(out)
    if fails:
        print("== test_toolchain_dyld_doctor: %d passing / %d failing =="
              % (2 - len(fails), len(fails)))
        for f in fails:
            print("FAIL:", f)
        return 1
    if skipped:
        print("== test_toolchain_dyld_doctor: SKIP (POSIX host required; "
              "honest skip rc=111) ==")
        return 111
    print("== test_toolchain_dyld_doctor: 2 passing / 0 failing ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
