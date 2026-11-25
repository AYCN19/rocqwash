#!/usr/bin/env python3
"""t_xtr_meta.py - line-local meta test over the xtr tool family.

Purpose.  One runner that keeps the whole xtr tool family honest: it
reruns every xtr-prefixed tool's selftest, checks the zero-collision
unregistration invariant, exercises the fixture face, pins determinism.

Vectors.
  1. discovery: tools/xtr_*.py and verify/xtr_*.py are enumerated from
     the repo tree (repo root = parent of tests/); the census tool is
     present.
  2. selftest: every discovered tool passes --selftest with exit 0 and
     a PASS marker containing SELFTEST on stdout.
  3. unregistration invariant: tests/run_tests.sh carries no xtr
     reference - the family stays unregistered in the shared suite by
     design; registration is deferred to the main-line close-out.
  4. fixture: census_sample.v reports the expected face, including the
     commented-out fake statement being masked.
  5. determinism: two census runs over the fixture directory produce
     byte-identical reports.

Interface.
  python -B tests/t_xtr_meta.py

Exit-codes.  0 all vectors green; 1 any red.  Prints T-XTR-META PASS.

Evidence.  The shell runs at integration over the census tool and the
fixture with double-run byte-identical determinism in the ledger.

Dependencies.  Python 3 standard library only.
"""
import glob
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF_FAIL = []


def check(cond, label):
    if not cond:
        SELF_FAIL.append(label)


def main():
    # v1: discovery
    tools = sorted(glob.glob(os.path.join(ROOT, "tools", "xtr_*.py")) +
                   glob.glob(os.path.join(ROOT, "verify", "xtr_*.py")))
    census = os.path.join(ROOT, "tools", "xtr_extract_census.py")
    check(len(tools) >= 1, "v1 no xtr tools discovered")
    check(census in tools, "v1 census tool present")

    # v2: every discovered tool passes --selftest
    for tool in tools:
        proc = subprocess.run(
            [sys.executable, "-B", tool, "--selftest"],
            capture_output=True, text=True, timeout=120)
        check(proc.returncode == 0, "v2 selftest rc %s: %s"
              % (proc.returncode, os.path.basename(tool)))
        check("SELFTEST" in proc.stdout and "PASS" in proc.stdout,
              "v2 selftest marker: " + os.path.basename(tool))

    # v3: unregistration invariant over the shared suite
    run_tests = os.path.join(ROOT, "tests", "run_tests.sh")
    check(os.path.isfile(run_tests), "v3 run_tests.sh present")
    with open(run_tests, "r", encoding="utf-8", errors="replace") as fh:
        suite = fh.read()
    lowered = suite.lower()
    check(not any(tok in lowered for tok in ("xtr_", "xtr-", "/xtr", "xtr ")),
          "v3 run_tests.sh must not reference the xtr family")

    # v4: fixture face via the census module (comment masking included)
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    try:
        import xtr_extract_census as census_mod
        fixture = os.path.join(ROOT, "tests", "fixtures", "xtr_census",
                               "census_sample.v")
        check(os.path.isfile(fixture), "v4 fixture present")
        with open(fixture, "r", encoding="utf-8") as fh:
            frag = census_mod.analyze_source(fh.read(), "census_sample.v")
        commands = [p["command"] for p in frag["points"]]
        check(commands.count("Extract Constant") == 2, "v4 two constants")
        check(commands.count("Recursive Extraction") == 1, "v4 recursive")
        check(commands.count("Extract Inductive") == 1, "v4 inductive")
        check(all(p["targets"] != ["fake"] for p in frag["points"]),
              "v4 commented fake masked")
        check(len(frag["unparsed"]) == 1, "v4 unparsed bucket")
        check(len(frag["language_declarations"]) == 1
              and frag["language_declarations"][0]["language"] == "haskell",
              "v4 language declaration")
        safe = [p for p in frag["points"]
                if p.get("target_payload") == '"(+)"']
        check(len(safe) == 1 and safe[0]["is_safe_primitive"] is True,
              "v4 safe primitive classified")
    finally:
        sys.path.pop(0)

    # v5: determinism across two subprocess runs
    fixture_dir = os.path.join(ROOT, "tests", "fixtures", "xtr_census")
    tmpdir = tempfile.mkdtemp(prefix="t_xtr_meta_")
    try:
        outs = []
        for i in (1, 2):
            path = os.path.join(tmpdir, "run%d.json" % i)
            proc = subprocess.run(
                [sys.executable, "-B", census, "--roots", fixture_dir,
                 "--out", path],
                capture_output=True, text=True, timeout=120)
            check(proc.returncode == 0, "v5 census run rc")
            with open(path, "rb") as fh:
                outs.append(fh.read())
        check(len(outs) == 2 and outs[0] == outs[1], "v5 byte-identical")
    finally:
        for name in os.listdir(tmpdir):
            os.unlink(os.path.join(tmpdir, name))
        os.rmdir(tmpdir)

    if SELF_FAIL:
        sys.stdout.write("T-XTR-META FAIL: %s\n" % SELF_FAIL[0])
        return 1
    sys.stdout.write("T-XTR-META PASS\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
