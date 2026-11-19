#!/usr/bin/env python3
"""t_vacgen_shape.py -- vacgen CLI shape selftest (zero-network, zero-compile).

Runs tools/vacgen.py --in <fixture> --out <tmp> on a tiny zeta-face fixture
and asserts the four-account skeleton layout. Lean compile face is design-SKIP
(rocqwash CI carries no Lean toolchain; see docs/vacgen_sop.md SKIP clause).
"""
import glob, os, subprocess, sys, tempfile

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

def main() -> int:
    if not os.path.isfile(VACGEN):
        print("SKIP: tools/vacgen.py not found (design-SKIP face)")
        return 0
    tmp = tempfile.mkdtemp(prefix="vacgen_shape_")
    fx = os.path.join(tmp, "fixture.lean")
    with open(fx, "w", encoding="utf-8") as f:
        f.write(FIXTURE)
    out = os.path.join(tmp, "out")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", VACGEN, "--in", fx, "--out", out],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if r.returncode != 0:
        print("FAIL: vacgen rc=", r.returncode, r.stderr[-300:])
        return 1
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
    print("PASS: four-account skeleton present (", len(glob.glob(os.path.join(out, "*"))), " files )")
    return 0

if __name__ == "__main__":
    sys.exit(main())
