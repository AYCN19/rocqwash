# -*- coding: utf-8 -*-
"""test_clean_mode.py: clean-mode switch selftest (rocqwash tests/).

Purpose.  Verify the ROCWASH_CLEAN=1 contract end to end: canonical-dependency
         faces report "requires canonical environment: ..." and refuse
         (exit 9; exit 1 for `tools/_abl1_4b_compile.py`, which keeps its own
         standing toolchain contract); default mode (env unset) stays
         unchanged; clean-available faces (--selftest, --registry) still
         pass under the switch.
Interface.  python3 -B tests/test_clean_mode.py   (suite case t_clean_mode).
         No CLI flags; drives seven repo tools as subprocesses and prints one
         ok/FAIL line per vector plus the final CLEAN-MODE-SELFTEST PASS line.
Dependencies.  Python 3 stdlib only (os, subprocess, sys, tempfile); drives
         seven repo tools as subprocesses; zero compile, zero network, zero
         writes outside mkdtemp.
Evidence.  The clean-mode census and semantics are documented in
         `docs/clean-mode-manual-20261114.md`; tests/run_tests.sh carries the
         clean-mode detection gate (canonical auto-detection off). One
         deterministic vector per face, machine-independent: no vector
         requires a canonical path to be present or absent, and default-mode
         vectors assert message absence or standing usage contracts rather
         than environment-dependent exit codes.
Exit-codes.  0 = every vector ok (CLEAN-MODE-SELFTEST PASS printed); 1 = any
         vector failed (named FAIL line, fail-loud).
"""
import os
import shutil
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(_HERE)

MARK = "requires canonical environment"

BASE_ENV = os.environ.copy()
BASE_ENV.pop("ROCWASH_CLEAN", None)
BASE_ENV.pop("ROCWASH_ROCQWORKER", None)
CLEAN_ENV = dict(BASE_ENV)
CLEAN_ENV["ROCWASH_CLEAN"] = "1"

PY = sys.executable or "python3"


def run_py(rel, args, env, timeout=120):
    """Run a repo tool as a subprocess; merged stdout+stderr, text mode."""
    p = subprocess.run([PY, "-B", os.path.join(REPO, rel)] + args,
                       env=env, cwd=REPO, timeout=timeout,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, errors="replace")
    return p.returncode, p.stdout


def expect(name, cond, detail):
    if not cond:
        print("FAIL %s: %s" % (name, detail))
        sys.exit(1)
    print("ok %s" % name)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    tmp = tempfile.mkdtemp(prefix="rocqwash_clean_mode_self_")
    n = 0

    # -- scan_station --baseline route (canonical S09 target; the frozen
    #    scanner itself is gated at the station layer) --------------------
    rc, out = run_py(os.path.join("wrapper", "scan_station.py"),
                     ["--baseline"], CLEAN_ENV)
    n += 1
    expect("V%02d scan_station --baseline clean reports and refuses rc9" % n,
           rc == 9 and MARK in out,
           "rc=%r out=%r" % (rc, out[-200:]))

    rc, out = run_py(os.path.join("wrapper", "scan_station.py"),
                     ["--baseline"], BASE_ENV)
    n += 1
    expect("V%02d scan_station --baseline default has no clean report" % n,
           MARK not in out, "out=%r" % out[-200:])

    # -- toolchain_dyld_doctor default worker chain -----------------------
    rc, out = run_py(os.path.join("tools", "toolchain_dyld_doctor.py"),
                     [], CLEAN_ENV)
    n += 1
    expect("V%02d dyld_doctor clean default-chain reports and refuses rc9"
           % n, rc == 9 and MARK in out,
           "rc=%r out=%r" % (rc, out[-200:]))

    rc0, out0 = run_py(os.path.join("tools", "toolchain_dyld_doctor.py"),
                       ["--selftest"], BASE_ENV)
    rc, out = run_py(os.path.join("tools", "toolchain_dyld_doctor.py"),
                     ["--selftest"], CLEAN_ENV)
    n += 1
    # The selftest face is switch-invariant (on hosts where it cannot run,
    # e.g. no otool, it fails identically with and without the switch).
    expect("V%02d dyld_doctor --selftest unchanged under clean" % n,
           rc == rc0 and MARK not in out,
           "rc=%r rc0=%r out=%r" % (rc, rc0, out[-200:]))

    rc, out = run_py(os.path.join("tools", "toolchain_dyld_doctor.py"),
                     [], BASE_ENV)
    n += 1
    expect("V%02d dyld_doctor default has no clean report" % n,
           MARK not in out, "out=%r" % out[-200:])

    # -- cw_doctor real rollup vs --selftest ------------------------------
    rc, out = run_py(os.path.join("tools", "cw_doctor.py"), [], CLEAN_ENV)
    n += 1
    expect("V%02d cw_doctor clean real face reports and refuses rc9" % n,
           rc == 9 and MARK in out,
           "rc=%r out=%r" % (rc, out[-200:]))

    rc, out = run_py(os.path.join("tools", "cw_doctor.py"),
                     ["--selftest"], CLEAN_ENV)
    n += 1
    expect("V%02d cw_doctor --selftest passes under clean" % n,
           rc == 0 and "CW-DOCTOR-SELFTEST PASS" in out,
           "rc=%r out=%r" % (rc, out[-200:]))

    # -- probe_engine real-probe face vs --selftest vs usage --------------
    full = ["--candidates", os.path.join(tmp, "c.tsv"),
            "--src", os.path.join(tmp, "src"),
            "--world", os.path.join(tmp, "world"),
            "--out", os.path.join(tmp, "led.json")]
    rc, out = run_py(os.path.join("wash", "probe_engine.py"), full, CLEAN_ENV)
    n += 1
    expect("V%02d probe_engine clean real face reports and refuses rc9" % n,
           rc == 9 and MARK in out,
           "rc=%r out=%r" % (rc, out[-200:]))

    rc0, out0 = run_py(os.path.join("wash", "probe_engine.py"),
                       ["--selftest"], BASE_ENV)
    rc, out = run_py(os.path.join("wash", "probe_engine.py"),
                     ["--selftest"], CLEAN_ENV)
    n += 1
    # The selftest face is switch-invariant (on hosts where the stub driver
    # cannot run it fails identically with and without the switch).
    expect("V%02d probe_engine --selftest unchanged under clean" % n,
           rc == rc0 and MARK not in out,
           "rc=%r rc0=%r out=%r" % (rc, rc0, out[-200:]))

    rc, out = run_py(os.path.join("wash", "probe_engine.py"), [], BASE_ENV)
    n += 1
    expect("V%02d probe_engine default no-args keeps usage rc2, no report"
           % n, rc == 2 and MARK not in out,
           "rc=%r out=%r" % (rc, out[-200:]))

    # -- quad8_reconcile registered roots vs --roots-file fixtures --------
    rc, out = run_py(os.path.join("wrapper", "quad8_reconcile.py"),
                     ["check", "--list", os.path.join(tmp, "m.json")],
                     CLEAN_ENV)
    n += 1
    expect("V%02d quad8 check clean (no roots-file) reports and refuses rc9"
           % n, rc == 9 and MARK in out,
           "rc=%r out=%r" % (rc, out[-200:]))

    rc0, out0 = run_py(os.path.join("wrapper", "quad8_reconcile.py"),
                       ["--selftest"], BASE_ENV)
    rc, out = run_py(os.path.join("wrapper", "quad8_reconcile.py"),
                     ["--selftest"], CLEAN_ENV)
    n += 1
    expect("V%02d quad8 --selftest unchanged under clean" % n,
           rc == rc0 and MARK not in out,
           "rc=%r rc0=%r out=%r" % (rc, rc0, out[-200:]))

    rc, out = run_py(os.path.join("wrapper", "quad8_reconcile.py"),
                     ["--registry"], CLEAN_ENV)
    n += 1
    expect("V%02d quad8 --registry print face stays available under clean"
           % n, rc == 0 and "scan/mac_stmt_scan.py" in out,
           "rc=%r out=%r" % (rc, out[-200:]))

    # -- frozen_call real call face vs --selftest -------------------------
    rc, out = run_py(os.path.join("wrapper", "frozen_call.py"),
                     ["--", os.path.join(tmp, "component")], CLEAN_ENV)
    n += 1
    expect("V%02d frozen_call clean real face reports and refuses rc9" % n,
           rc == 9 and MARK in out,
           "rc=%r out=%r" % (rc, out[-200:]))

    rc0, out0 = run_py(os.path.join("wrapper", "frozen_call.py"),
                       ["--selftest"], BASE_ENV)
    rc, out = run_py(os.path.join("wrapper", "frozen_call.py"),
                     ["--selftest"], CLEAN_ENV)
    n += 1
    expect("V%02d frozen_call --selftest unchanged under clean" % n,
           rc == rc0 and MARK not in out,
           "rc=%r rc0=%r out=%r" % (rc, rc0, out[-200:]))

    # -- _abl1_4b_compile OCaml toolchain (import-time gate, exit 1) ------
    rc, out = run_py(os.path.join("tools", "_abl1_4b_compile.py"),
                     [tmp], CLEAN_ENV)
    n += 1
    expect("V%02d _abl1_4b_compile clean reports, keeps rc1 contract" % n,
           rc == 1 and MARK in out,
           "rc=%r out=%r" % (rc, out[-200:]))

    rc, out = run_py(os.path.join("tools", "_abl1_4b_compile.py"),
                     [tmp], BASE_ENV)
    n += 1
    # Environment-aware default vector: with the OCaml toolchain on PATH the
    # default mode compiles the (empty) fixture and succeeds rc0; without it
    # the standing FATAL rc1 contract holds. Either way no clean-report
    # marker leaks into default mode and the clean vector (V16) keeps its
    # report-and-refuse contract.
    if shutil.which("ocamlc") is not None and shutil.which("ocamldep") is not None:
        expect("V%02d _abl1_4b_compile default compiles empty fixture rc0, no report" % n,
               rc == 0 and "COMPILED-ALL" in out and MARK not in out,
               "rc=%r out=%r" % (rc, out[-200:]))
    else:
        expect("V%02d _abl1_4b_compile default keeps FATAL rc1, no report" % n,
               rc == 1 and MARK not in out,
               "rc=%r out=%r" % (rc, out[-200:]))

    # -- suite gate word face ---------------------------------------------
    with open(os.path.join(_HERE, "run_tests.sh"), "r",
              encoding="utf-8", errors="replace") as fh:
        suite = fh.read()
    n += 1
    expect("V%02d run_tests.sh carries the clean-mode detection gate" % n,
           suite.count("ROCWASH_CLEAN") >= 3,
           "occurrences=%d" % suite.count("ROCWASH_CLEAN"))

    print("CLEAN-MODE-SELFTEST PASS: %d vectors" % n)
    sys.exit(0)


if __name__ == "__main__":
    main()
