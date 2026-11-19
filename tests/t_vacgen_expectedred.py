#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_vacgen_expectedred.py -- expected-red contract selftest for the vacgen cast (zero-network, zero-compile).

Purpose.
    The refutation spectrum of a vacgen cast is compile-must-fail BY DESIGN: a probe red (rc != 0) on a falsify
    face is the expected verdict (weak red = nonempty evidence: the premise interface resisted the refutation
    attempt), while a probe green (rc = 0) would be the vacuity alert (verdict ok = false, highest alert level).
    This test pins that contract at the word-face level, so the by-design rc != 0 can never be misread as a suite
    failure (reading rule from tools/baseline_diff.py: a red is data, not a tool failure; only unregistered reds
    are defects).  Three checks pin the per-face EXPECTED-FAIL registration (marker, falsify theorem line,
    grade=EXPECTED-FAIL ledger row), the inverted rc verdict contract in each face header (rc = 0 = vacuity
    alert, rc != 0 = expected evidence; RC_CONTRACT below), and the red/green boundary (expected-green faces
    carry zero EXPECTED-FAIL and >= 1 EXPECTED-GREEN-AFTER-FILL marker, verdict ok=true; a red there is a
    probe-side defect, never evidence).

Interface.
    python -I tests/t_vacgen_expectedred.py   (no flags; PASS/SKIP/FAIL to stdout; manual: python3 -B ...)

Dependencies.
    Python 3 stdlib only (os, re, subprocess, sys, tempfile); zero network, zero compile, zero writes outside
    a mktemp directory; Lean compile leg design-SKIP unconditionally (suite never compiles; no Lean toolchain
    on CI, mathlib caches never pulled); ROCWASH_LEAN_WORKTREE observed and reported, not acted on
    (tools/vacgen_env_note.md); fixture casts through the builtin starter taxonomy row, independent of any taxonomy.json.

Evidence.
    Suite case t_vacgen_expectedred (tests/run_tests.sh); the frozen RC_CONTRACT vector below is the wording the
    engine does not mechanically check - any rewording of the contract must re-register it.

Exit-codes.
    0 = all checks pass (design-SKIP legs reported, never counted red); 1 = any red (fail-loud listing).
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VACGEN = os.path.normpath(os.path.join(HERE, "..", "tools", "vacgen.py"))

# The five-face refutation spectrum as cast by this revision
# (tools/vacgen.py REFUTATION_FACES, frozen here as the test vector).
FACES = ("full", "point", "tactics", "noclassic", "band")
GREEN_TARGETS = ("witness.lean", "boundary.lean")

# Frozen contract vector: the full EXPECTED-FAIL rc-semantics block every
# refutation face header must carry (whitespace-normalized match).  This is
# the wording the engine does NOT mechanically check, so the test freezes it
# verbatim; a rewording of the contract must re-register this vector.
RC_CONTRACT = (
    "EXPECTED-FAIL (probe must fail). rc = 0 (green) would mean the "
    "transcribed premise interface is jointly unsatisfiable at this probe "
    "strength = vacuity alert (immediate escalation, ok = false). rc = 1 "
    "(red) = nonempty evidence: the interface resisted this refutation form."
)

FIXTURE = (
    "import Mathlib.NumberTheory.LSeries.RiemannZeta\n\n"
    "namespace VacgenExpectedredSelftest\n\n"
    "theorem demo_half_plane_nonempty : (EXISTS s : CC, (7 / 8 : RR) < s.re) := by\n"
    "  refine (2, by norm_num)\n\n"
    "theorem demo_zero_face {s : CC} (hs : (7 / 8 : RR) < s.re) : riemannZeta s != 0 := by\n"
    "  sorry\n\n"
    "end VacgenExpectedredSelftest\n"
).replace("EXISTS", chr(0x2203)).replace("CC", chr(0x2102)).replace("RR", chr(0x211D)).replace("!=", chr(0x2260))


def main() -> int:
    if not os.path.isfile(VACGEN):
        print("SKIP: tools/vacgen.py not found (design-SKIP face)")
        return 0

    tmp = tempfile.mkdtemp(prefix="vacgen_expectedred_")
    fx = os.path.join(tmp, "expectedred_fixture.lean")
    with open(fx, "w", encoding="utf-8") as f:
        f.write(FIXTURE)
    out = os.path.join(tmp, "out")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", VACGEN, "--in", fx, "--out", out],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if r.returncode != 0:
        print("FAIL: cast rc=", r.returncode)
        print((r.stdout or "")[-400:])
        print((r.stderr or "")[-400:])
        return 1
    stdout = r.stdout or ""

    fails = {"check1": [], "check2": [], "check3": []}

    # ---- check 1: expected-red registration per refutation face ----
    for face in FACES:
        path = os.path.join(out, "falsify_%s.lean" % face)
        if not os.path.isfile(path):
            fails["check1"].append("falsify_%s.lean missing from the cast" % face)
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if text.count("EXPECTED-FAIL") < 1:
            fails["check1"].append(
                "falsify_%s.lean carries no EXPECTED-FAIL marker" % face)
        if "_falsify_%s : False := by" % face not in text:
            fails["check1"].append(
                "falsify_%s.lean missing the falsify theorem line" % face)
        if not re.search(r"^\s+falsify_%s\.lean\s+grade=EXPECTED-FAIL" % face,
                         stdout, re.MULTILINE):
            fails["check1"].append(
                "ledger row grade=EXPECTED-FAIL missing for falsify_%s.lean" % face)
    if "[PASS] expected_fail_marker_present_per_refutation" not in stdout:
        fails["check1"].append(
            "cast check expected_fail_marker_present_per_refutation not PASS")

    # ---- check 2: inverted verdict contract in the face header ----
    for face in FACES:
        path = os.path.join(out, "falsify_%s.lean" % face)
        if not os.path.isfile(path):
            continue  # already reported by check 1
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if " ".join(text.split()).find(RC_CONTRACT) < 0:
            fails["check2"].append(
                "falsify_%s.lean header lacks the frozen rc-contract vector "
                "(rc = 0 vacuity alert / rc = 1 expected evidence)" % face)

    # ---- check 3: the red/green boundary ----
    for name in GREEN_TARGETS:
        path = os.path.join(out, name)
        if not os.path.isfile(path):
            fails["check3"].append("%s missing from the cast" % name)
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if text.count("EXPECTED-FAIL") != 0:
            fails["check3"].append(
                "%s carries an EXPECTED-FAIL marker (expected-green face)" % name)
        if text.count("EXPECTED-GREEN-AFTER-FILL") < 1:
            fails["check3"].append(
                "%s carries no EXPECTED-GREEN-AFTER-FILL marker" % name)
    if "[PASS] expected_fail_marker_absent_per_green" not in stdout:
        fails["check3"].append(
            "cast check expected_fail_marker_absent_per_green not PASS")
    if "ok=true" not in stdout:
        fails["check3"].append("cast verdict is not ok=true")

    # ---- Lean compile leg: design-SKIP (observed, never acted on) ----
    worktree = os.environ.get("ROCWASH_LEAN_WORKTREE")
    print("SKIP: Lean compile leg design-SKIP (zero-compile suite; "
          "ROCWASH_LEAN_WORKTREE=%s observed, not acted on)"
          % (worktree if worktree else "<unset>"))

    red = sum(1 for msgs in fails.values() if msgs)
    print("== t_vacgen_expectedred: %d pass / %d red =="
          % (3 - red, red))
    for name in ("check1", "check2", "check3"):
        for msg in fails[name]:
            print("FAIL: %s: %s" % (name, msg))
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
