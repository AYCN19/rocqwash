# -*- coding: utf-8 -*-
"""test_dual_scan.py — regression coverage for scan/dual_scan.py (v32).

Vectors (all on temp-dir fixtures — zero real-repo touches):
  1. clean fixture: both scanners run rc=0 at zero stations, the diff is
     empty on both sides, exit code 0, and the report JSON is written.
  2. statement-face fixture: mac_stmt_scan reports a station scan_v4_token
     cannot see -> diff.only_stmt nonempty (the one-sided case, reported
     not resolved — scanner consensus is not a completeness certificate).
  3. token-face fixture: scan_v4_token reports an unqualified-global
     station mac_stmt_scan does not -> diff.only_v4 nonempty.
  4. determinism: two runs over the same targets produce byte-identical
     report JSONs (no timestamps, no environment noise).
  5. CLI contract: help rc=0; unknown flag rc=2; missing --dir rc=2;
     missing --file rc=9; missing scanner tool rc=9.
"""
import io, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DUAL = os.path.join(REPO, "scan", "dual_scan.py")

fails = []


def check(name, cond, extra=""):
    print("  %-46s %s %s" % (name, "ok" if cond else "FAIL", extra))
    if not cond:
        fails.append(name)


def run(cmd, **kw):
    return subprocess.run([sys.executable, "-B", DUAL] + cmd,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          **kw)


CLEAN = "Definition k (n : nat) : nat := n + 0.\n"
STMT_FACE = ("Theorem g : forall n : nat, n <= n.\n"
             "Proof. intros. apply Nat.le_refl. Qed.\n")
TOKEN_FACE = "Definition k (n : nat) := S n + 0.\n"

tmp = tempfile.mkdtemp(prefix="rw_dual_")
try:
    # 1. clean fixture: zero/zero, empty diff, rc 0, report written
    d1 = os.path.join(tmp, "clean")
    os.makedirs(d1)
    io.open(os.path.join(d1, "clean.v"), "w", encoding="utf-8").write(CLEAN)
    out1 = os.path.join(tmp, "r1.json")
    r = run(["--dir", d1, "--out", out1])
    check("clean dir: rc=0", r.returncode == 0, r.stdout.decode()[-200:])
    rep = json.load(io.open(out1, encoding="utf-8"))
    rec = rep["clean.v"]
    check("clean: both scanners at zero stations",
          rec["scanv4"]["rc"] == 0 and rec["scanv4"]["stations"] == 0
          and rec["macstmt"]["rc"] == 0 and rec["macstmt"]["hits"] == 0)
    check("clean: empty diff both sides",
          rec["diff"]["only_v4"] == [] and rec["diff"]["only_stmt"] == [])

    # 2. statement-face station -> only_stmt
    d2 = os.path.join(tmp, "stmt")
    os.makedirs(d2)
    io.open(os.path.join(d2, "stmt.v"), "w", encoding="utf-8").write(STMT_FACE)
    out2 = os.path.join(tmp, "r2.json")
    r = run(["--dir", d2, "--out", out2])
    rep = json.load(io.open(out2, encoding="utf-8"))
    rec = rep["stmt.v"]
    check("statement-face station: only_stmt nonempty, only_v4 empty",
          r.returncode == 0 and rec["macstmt"]["hits"] >= 1
          and len(rec["diff"]["only_stmt"]) >= 1
          and rec["diff"]["only_v4"] == [],
          str(rec["diff"]))

    # 3. token-face station -> only_v4
    d3 = os.path.join(tmp, "tok")
    os.makedirs(d3)
    io.open(os.path.join(d3, "tok.v"), "w", encoding="utf-8").write(TOKEN_FACE)
    out3 = os.path.join(tmp, "r3.json")
    r = run(["--dir", d3, "--out", out3])
    rep = json.load(io.open(out3, encoding="utf-8"))
    rec = rep["tok.v"]
    check("token station: only_v4 nonempty, only_stmt empty",
          r.returncode == 0 and rec["scanv4"]["stations"] >= 1
          and len(rec["diff"]["only_v4"]) >= 1
          and rec["diff"]["only_stmt"] == [],
          str(rec["diff"]))

    # 4. determinism: same targets twice -> byte-identical reports
    o1 = os.path.join(tmp, "d1.json")
    o2 = os.path.join(tmp, "d2.json")
    run(["--dir", d2, "--dir", d3, "--out", o1])
    run(["--dir", d2, "--dir", d3, "--out", o2])
    b1 = io.open(o1, "rb").read()
    b2 = io.open(o2, "rb").read()
    check("determinism: byte-identical reports", b1 == b2)

    # 5. CLI contract
    r = run([])
    check("no targets rc=2", r.returncode == 2, str(r.returncode))
    r = run(["--dir", os.path.join(tmp, "nope")])
    check("missing dir rc=2", r.returncode == 2, str(r.returncode))
    r = run(["--file", os.path.join(tmp, "nope.v")])
    check("missing file rc=9", r.returncode == 9, str(r.returncode))
    r = run(["--file", os.path.join(d1, "clean.v"),
             "--scan-v4", os.path.join(tmp, "no_tool.py")])
    check("missing scanner tool rc=9", r.returncode == 9, str(r.returncode))
    r = subprocess.run([sys.executable, "-B", DUAL, "--help"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    check("--help rc=0", r.returncode == 0, str(r.returncode))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("TEST-DUAL-SCAN:", "PASS" if not fails else "FAIL %s" % fails)
sys.exit(0 if not fails else 1)
