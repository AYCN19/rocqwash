#!/usr/bin/env python3
"""t_vacgen_shape.py -- vacgen CLI shape selftest (zero-network, zero-compile).

Purpose.
    Assert the four-account skeleton layout of a vacgen cast: run
    tools/vacgen.py --in <fixture> --out <tmp> on a tiny zeta-face fixture
    and require witness.lean, boundary.lean, gap_anchors.txt and >= 5
    falsify faces in the output directory.
    Ticket-15 (需求书v2-B 20261121) conclusion-face vectors: the taxonomy
    conclusion families must be recognized on cast stdout - nonzero applied
    conclusion (concl.ne.applied-nonzero, the 169B QRH challenge face
    `riemannZeta s ≠ 0`), nonvanishing predicate conclusion
    (concl.nezero.predicate), quantified conclusion
    (concl.quantified.universal) - while the premise family
    (ineq.real.const-lt-field-re) and the pre-existing specific exists
    conclusion family (concl.real.const-lt-field-re-exists) stay unchanged
    (premise-face zero regression).

Interface.
    python -I tests/t_vacgen_shape.py   (no flags; one PASS/SKIP/FAIL line to stdout)

Dependencies.
    Python 3 stdlib only (glob, os, re, subprocess, sys, tempfile); zero network,
    zero compile.  The Lean compile leg is design-SKIP (rocqwash CI carries
    no Lean toolchain; docs/vacgen_sop.md SKIP clause).  Loud SKIP with rc 0
    when tools/vacgen.py is absent; fixtures are self-contained.

Evidence.
    Registered suite case t_vacgen_shape (tests/run_tests.sh); the check
    vectors are the four-account skeleton layout and the per-cast conclusion
    classification lines asserted in main().

Exit-codes.
    0 = PASS or design-SKIP; 1 = cast failure or any missing face (fail-loud).
"""
import glob, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VACGEN = os.path.normpath(os.path.join(HERE, "..", "tools", "vacgen.py"))

FIXTURE = (
    "import Mathlib.NumberTheory.LSeries.RiemannZeta\n\n"
    "namespace VacgenSelftest\n\n"
    "theorem demo_half_plane_nonempty : (EXISTS s : CC, (7 / 8 : RR) < s.re) := by\n"
    "  refine (2, by norm_num)\n\n"
    "theorem demo_zero_face {s : CC} (hs : (7 / 8 : RR) < s.re) : riemannZeta s != 0 := by\n"
    "  sorry\n\n"
    "end VacgenSelftest\n"
).replace("EXISTS", chr(0x2203)).replace("CC", chr(0x2102)).replace("RR", chr(0x211D)).replace("!=", chr(0x2260))

# Ticket-15 conclusion-face vector fixtures (single-theorem heads so the head
# selection lands on the vector face).
FIXTURE_NONZERO = (
    "import Mathlib.NumberTheory.LSeries.RiemannZeta\n\n"
    "namespace VacgenShapeNonzero\n\n"
    "theorem qrh_face {s : CC} (hs : (7 / 8 : RR) < s.re) : riemannZeta s != 0 := by\n"
    "  sorry\n\n"
    "end VacgenShapeNonzero\n"
).replace("CC", chr(0x2102)).replace("RR", chr(0x211D)).replace("!=", chr(0x2260))

FIXTURE_NEZERO = (
    "import Mathlib\n\n"
    "namespace VacgenShapeNezero\n\n"
    "theorem nezero_face {N : NN} (h : N != 0) : NeZero N := by\n"
    "  sorry\n\n"
    "end VacgenShapeNezero\n"
).replace("NN", chr(0x2115)).replace("!=", chr(0x2260))

FIXTURE_QUANT = (
    "import Mathlib.NumberTheory.LSeries.RiemannZeta\n\n"
    "namespace VacgenShapeQuant\n\n"
    "theorem quant_face : FORALL s : CC, riemannZeta s != 0 -> s.re = 1 / 2 := by\n"
    "  sorry\n\n"
    "end VacgenShapeQuant\n"
).replace("FORALL", chr(0x2200)).replace("CC", chr(0x2102)).replace("!=", chr(0x2260)).replace("->", chr(0x2192))

CONCL_LINE_RE = re.compile(r"^\s*conclusion\s+-\s+.*->\s*(recognized@(\S+)|todo_seat)\s*$",
                           re.MULTILINE)
PREMISE_LINE_RE = re.compile(r"^\s*assumption\s+\S+.*->\s*(recognized@(\S+)|todo_seat)\s*$",
                             re.MULTILINE)
COVERAGE_RE = re.compile(r"L3 coverage \(lower bound[^)]*\):\s*(\d+)/(\d+)\s*=\s*(\d+)%")


def _cast(fixture_text, tag, tmp):
    """Cast one fixture, return (rc, stdout)."""
    fx = os.path.join(tmp, "fixture_%s.lean" % tag)
    with open(fx, "w", encoding="utf-8") as f:
        f.write(fixture_text)
    out = os.path.join(tmp, "out_%s" % tag)
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", VACGEN, "--in", fx, "--out", out],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r.returncode, r.stdout or ""


def _concl_verdict(stdout):
    m = CONCL_LINE_RE.search(stdout)
    return (m.group(1), m.group(2)) if m else (None, None)


def _premise_verdicts(stdout):
    return PREMISE_LINE_RE.findall(stdout)


def main() -> int:
    if not os.path.isfile(VACGEN):
        print("SKIP: tools/vacgen.py not found (design-SKIP face)")
        return 0
    tmp = tempfile.mkdtemp(prefix="vacgen_shape_")
    fails = []

    # ---- face 1 (pre-ticket): four-account skeleton layout ----
    rc, stdout = _cast(FIXTURE, "base", tmp)
    if rc != 0:
        print("FAIL: vacgen rc=", rc, stdout[-300:])
        return 1
    out = os.path.join(tmp, "out_base")
    checks = {
        "witness": os.path.isfile(os.path.join(out, "witness.lean")),
        "boundary": os.path.isfile(os.path.join(out, "boundary.lean")),
        "gap_anchors": os.path.isfile(os.path.join(out, "gap_anchors.txt")),
        "falsify>=5": len(glob.glob(os.path.join(out, "falsify*"))) >= 5,
    }
    bad = [k for k, v in checks.items() if not v]
    if bad:
        print("FAIL: missing faces:", bad)
        return 1
    # pre-existing specific exists conclusion unchanged (zero-regression pin;
    # the base head theorem carries no premise binder, so the premise-face
    # zero-regression pin lives on the nonzero vector face below)
    fam, _ = _concl_verdict(stdout)
    if fam != "recognized@concl.real.const-lt-field-re-exists":
        fails.append("base specific exists conclusion family moved: %r" % (fam,))

    # ---- face 2 (ticket-15): nonzero applied conclusion (169B QRH face) ----
    rc, stdout = _cast(FIXTURE_NONZERO, "nonzero", tmp)
    if rc != 0:
        fails.append("nonzero cast rc=%d %s" % (rc, stdout[-200:]))
    else:
        fam, _ = _concl_verdict(stdout)
        if fam != "recognized@concl.ne.applied-nonzero":
            fails.append("nonzero conclusion not recognized@concl.ne.applied-nonzero: %r" % (fam,))
        prem = _premise_verdicts(stdout)
        if not (prem and prem[0][1] == "ineq.real.const-lt-field-re"):
            fails.append("nonzero premise family moved: %r" % (prem[:1],))
        m = COVERAGE_RE.search(stdout)
        if not (m and (m.group(1), m.group(2)) == ("2", "2") and m.group(3) == "100"):
            fails.append("nonzero L3 not 2/2 = 100%%: %r" % (m.groups() if m else None,))

    # ---- face 3 (ticket-15): nonvanishing predicate conclusion ----
    rc, stdout = _cast(FIXTURE_NEZERO, "nezero", tmp)
    if rc != 0:
        fails.append("nezero cast rc=%d %s" % (rc, stdout[-200:]))
    else:
        fam, _ = _concl_verdict(stdout)
        if fam != "recognized@concl.nezero.predicate":
            fails.append("nezero conclusion not recognized@concl.nezero.predicate: %r" % (fam,))

    # ---- face 4 (ticket-15): quantified conclusion ----
    rc, stdout = _cast(FIXTURE_QUANT, "quant", tmp)
    if rc != 0:
        fails.append("quant cast rc=%d %s" % (rc, stdout[-200:]))
    else:
        fam, _ = _concl_verdict(stdout)
        if fam != "recognized@concl.quantified.universal":
            fails.append("quant conclusion not recognized@concl.quantified.universal: %r" % (fam,))

    if fails:
        for msg in fails:
            print("FAIL:", msg)
        return 1
    print("PASS: four-account skeleton present (", len(glob.glob(os.path.join(out, "*"))), " files );",
          " ticket-15 conclusion-face vectors green:",
          "nonzero=concl.ne.applied-nonzero(nezero-predicate leg green, quantified=concl.quantified.universal),",
          "premise ineq.real.const-lt-field-re unchanged,",
          "specific exists family unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
