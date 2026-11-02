# -*- coding: utf-8 -*-
"""test_cure_pack.py — regression coverage for the consumer-cure canonical pack
(wash/cure_pack.json + wash/cure_applier.py).

Vectors:
  1. applier selftest (in-memory mechanics: five patterns, trigger gates,
     idempotence) — rc 0.
  2. pack integrity: JSON parses, five pattern ids present, every pattern
     carries trigger/template and an idempotence note.
  3. dry-run then --apply on a temp copy of the shadow fixture restricted to
     cure4: exactly three stations cured, binder-bound lines untouched,
     written file idempotent (applier's own second-pass assertion).
  4. compile check (env-gated): with ROCWASH_ROCQ set to the rocq binary
     (Rocq/Coq 9.x), tests/fixtures/cure_examples.v compiles rc=0 in a temp
     dir, and a negative-control variant (bare reflexivity directly on the
     carrier face) fails — the opacity the cure3 pattern addresses.  Skipped
     (rc 111) when ROCWASH_ROCQ is unset, so external clones pass without a
     toolchain.
"""
import io, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
APPLIER = os.path.join(REPO, "wash", "cure_applier.py")
PACK = os.path.join(REPO, "wash", "cure_pack.json")
EXAMPLES = os.path.join(HERE, "fixtures", "cure_examples.v")
FIXTURE = os.path.join(HERE, "fixtures", "scan_v4_shadow_fixture.v")

fails = []


def check(name, cond, extra=""):
    print("  %-34s %s %s" % (name, "ok" if cond else "FAIL", extra))
    if not cond:
        fails.append(name)


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          **kw)


# 1. applier mechanics
r = run([sys.executable, "-B", APPLIER, "--selftest"])
check("applier --selftest rc=0", r.returncode == 0,
      "" if r.returncode == 0 else r.stdout.decode()[-300:])

# 2. pack integrity
import json
pack = json.load(io.open(PACK, encoding="utf-8"))
ids = [p["id"] for p in pack["patterns"]]
check("five patterns", len(pack["patterns"]) == 5)
want = {"cure1_qeqT_imp_qeq_rewrite_wrap", "cure2_qeq_imp_qeqT_goal_open",
        "cure3_qeq_refl_replace_reflexivity", "cure4_datatypes_s_qualify",
        "cure5_natle_drop_bridge"}
check("pattern ids complete", set(ids) == want)
check("every pattern has trigger+template+idempotence",
      all(("trigger_regex" in p or "trigger" in p) and "template" in p
          and "idempotence_note" in p for p in pack["patterns"]))

# 3. dry-run + apply on a temp copy (cure4 only)
tmp = tempfile.mkdtemp(prefix="rw_cure_")
try:
    tgt = os.path.join(tmp, "fixture.v")
    shutil.copy(FIXTURE, tgt)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt,
             "--only", "cure4_datatypes_s_qualify", "--json",
             os.path.join(tmp, "dry.json")])
    dry = json.load(io.open(os.path.join(tmp, "dry.json"), encoding="utf-8"))
    check("dry-run cure4 matches=3",
          dry["report"]["cure4_datatypes_s_qualify"]["matches"] == 3)
    after_dry = io.open(tgt, encoding="utf-8").read()
    check("dry-run wrote nothing",
          after_dry == io.open(FIXTURE, encoding="utf-8").read())
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--apply",
             "--only", "cure4_datatypes_s_qualify"])
    check("apply rc=0 (idempotence verified)", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode()[-300:])
    cured = io.open(tgt, encoding="utf-8").read()
    check("bare stations qualified",
          cured.count("+ Datatypes.S n + Datatypes.S n.") == 1
          and cured.count("Datatypes.S (Datatypes.S n) + Datatypes.S (Datatypes.S n)") == 1
          and cured.count("+ Datatypes.S (size sp).") == 1)
    check("binder-local untouched",
          "Definition local_sum (S : Set) (f : S -> nat) (x : S) : nat := f x + 0."
          in cured)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# 4. compile check (env-gated, thermal-guard wrapped like every compile)
rocq = os.environ.get("ROCWASH_ROCQ", "")
if rocq and os.path.exists(rocq):
    guard = os.path.join(REPO, "tools", "cpu_guard.sh")
    tmp = tempfile.mkdtemp(prefix="rw_curec_")
    reg = os.path.join(tmp, "guard_reg")
    os.makedirs(reg, exist_ok=True)

    def guarded(args):
        return run([guard, "-Reg", reg, "-Front", "0", "-Mid", "1",
                    "-MaxWaitSec", "600", "--"] + args)
    try:
        ex = os.path.join(tmp, "cure_examples.v")
        shutil.copy(EXAMPLES, ex)
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", tmp, "", ex])
        check("cure_examples compiles rc=0 (guard-wrapped)", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode()[-300:])
        # negative control: bare reflexivity on the carrier face is opaque
        neg = io.open(EXAMPLES, encoding="utf-8").read() + """

Lemma neg_opaque_reflexivity : forall a : Q, QeqT a a.
Proof.
  intro a. reflexivity.
Qed.
"""
        negf = os.path.join(tmp, "neg_control.v")
        io.open(negf, "w", encoding="utf-8").write(neg)
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", tmp, "", negf])
        check("opaque-reflexivity negative fails (rc!=0)", r.returncode != 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
else:
    print("  compile check: SKIP (ROCWASH_ROCQ unset)")

print("TEST-CURE-PACK:", "PASS" if not fails else "FAIL %s" % fails)
sys.exit(0 if not fails else 1)
