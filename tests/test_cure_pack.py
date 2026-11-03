# -*- coding: utf-8 -*-
"""test_cure_pack.py — regression coverage for the consumer-cure canonical pack
(wash/cure_pack.json + wash/cure_applier.py).

Vectors:
  1. applier selftest (in-memory mechanics: legacy five patterns plus the
     v1.1 face-regex patterns cure6..cure14, trigger gates, guards,
     idempotence, exclusive-group conflict) — rc 0.
  2. pack integrity: JSON parses, the legacy five pattern ids present with
     their trigger/template/idempotence fields, the nine v1.1 patterns
     present with idempotence notes and lineage fields.
  3. dry-run then --apply on a temp copy of the shadow fixture restricted to
     cure4: exactly three stations cured, binder-bound lines untouched,
     written file idempotent (applier's own second-pass assertion).
  4. v1.1 fixture flows (dry-run + --apply + re-run zero-change):
     qle fixture (face downshifts + refl opener; binder/named/unmarked
     negatives untouched), natle fixture (premise lift + intros-tail-guarded
     drop wrap; constant-tail station untouched), shadow fixture (both
     exclusive variants individually, plain no-import file at zero matches,
     variant pair conflict rc=4 with file untouched).
  5. compile check (env-gated): with ROCWASH_ROCQ set to the rocq binary
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
want_legacy = {"cure1_qeqT_imp_qeq_rewrite_wrap", "cure2_qeq_imp_qeqT_goal_open",
               "cure3_qeq_refl_replace_reflexivity", "cure4_datatypes_s_qualify",
               "cure5_natle_drop_bridge"}
want_v31 = {"cure6_qle_token_downshift", "cure7_qle_notation_downshift",
            "cure8_qlt_token_downshift", "cure9_qlt_notation_downshift",
            "cure10_qle_refl_bridge_open", "cure11_import_shadow_delete",
            "cure12_shadow_direct_face_qualify", "cure13_natle_premise_lift",
            "cure14_natle_drop_wrap"}
check("legacy five present", want_legacy <= set(ids))
check("v1.1 nine present", want_v31 <= set(ids))
check("pattern count 5+9", len(pack["patterns"]) == 14)
check("every pattern has trigger+template+idempotence",
      all(("trigger_regex" in p or "trigger" in p or "token_map" in p)
          and ("template" in p or "template_fn" in p or "token_map" in p)
          and "idempotence_note" in p for p in pack["patterns"]))
check("v1.1 patterns carry lineage",
      all("v31_lineage" in p for p in pack["patterns"]
          if p["id"] in want_v31))
check("exclusive group declared on both shadow variants",
      [p.get("exclusive_group") for p in pack["patterns"]
       if p["id"].startswith(("cure11", "cure12"))] == ["import-shadow"] * 2)

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

# 4. v1.1 fixture flows (dry-run + apply + re-run zero-change per fixture)
QLE_F = os.path.join(HERE, "fixtures", "cure31_qle_fixture.v")
NATLE_F = os.path.join(HERE, "fixtures", "cure31_natle_fixture.v")
SHADOW_F = os.path.join(HERE, "fixtures", "cure31_shadow_fixture.v")
SHADOW_PLAIN_F = os.path.join(HERE, "fixtures", "cure31_shadow_plain_fixture.v")

tmp = tempfile.mkdtemp(prefix="rw_cure31_")
try:
    # 4a. qle fixture: full pack — downshifts + refl opener + guarded negatives
    tgt = os.path.join(tmp, "qle.v")
    shutil.copy(QLE_F, tgt)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--apply"])
    check("qle fixture apply rc=0", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode()[-400:])
    cured = io.open(tgt, encoding="utf-8").read()
    check("qle notation downshifted",
          "QleT' (Qabs x) 2%Q." in cured, cured[:0])
    check("qle token faces downshifted",
          "QleT' a b -> QleT' (f a) (f b)." in cured
          and "QltT a b -> QltT (g a) (g b)." in cured
          and "QltT (Qabs x) 1%Q." in cured)
    check("refl opener injected in QleT'-face proof",
          "apply Qle_to_QleT'. apply Qle_refl." in cured)
    check("guarded negatives untouched",
          "Definition bnd_holder (Qle : nat) (Qlt : nat) (n : nat) := n + Qle + Qlt."
          in cured
          and "Definition named_qle := 3." in cured
          and "Qabs y <= Qabs a." in cured
          and "must survive every application verbatim" in cured)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--json",
             os.path.join(tmp, "qle2.json")])
    dry = json.load(io.open(os.path.join(tmp, "qle2.json"), encoding="utf-8"))
    check("qle re-run zero matches",
          all(v["matches"] == 0 for v in dry["report"].values()))

    # 4b. natle fixture: premise lift + intros-tail-guarded drop wrap
    tgt = os.path.join(tmp, "natle.v")
    shutil.copy(NATLE_F, tgt)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--apply"])
    check("natle fixture apply rc=0", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode()[-400:])
    cured = io.open(tgt, encoding="utf-8").read()
    check("premise lifted (qualified carrier name)",
          "S01_BaseRing.NatLe (gnPrf f pf) k -> NatOK f pf k." in cured
          and "S01_BaseRing.NatLe n m -> n < m." in cured)
    check("drop wrap only at the introduced-hypothesis station",
          "exact (gnPrf_replay f pf k (S01_BaseRing.NatLe_drop _ _ Hk))."
          in cured
          and "exact (gnPrf_replay_eq abg_fzz abg_axz)." in cured)
    check("legacy cure5 wraps the bare NatLe consumption",
          "exact (NatLe_drop _ _ H)." in cured)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--json",
             os.path.join(tmp, "natle2.json")])
    dry = json.load(io.open(os.path.join(tmp, "natle2.json"), encoding="utf-8"))
    check("natle re-run zero matches",
          all(v["matches"] == 0 for v in dry["report"].values()))

    # 4c. shadow fixture: variant pair conflict first (rc 4, file untouched)
    tgt = os.path.join(tmp, "shadow.v")
    shutil.copy(SHADOW_F, tgt)
    before_txt = io.open(tgt, encoding="utf-8").read()
    r = run([sys.executable, "-B", APPLIER, "--file", tgt])
    check("variant pair conflict rc=4 (no --only)", r.returncode == 4,
          r.stdout.decode()[-200:])
    check("conflict left the file untouched",
          io.open(tgt, encoding="utf-8").read() == before_txt)
    # variant (a) alone: delete the shadowing Import line
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--apply",
             "--only", "cure11_import_shadow_delete"])
    check("variant (a) apply rc=0", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode()[-300:])
    cured = io.open(tgt, encoding="utf-8").read()
    check("variant (a) deleted the Import line only",
          "Import RealInterfaceEnhancedMod." not in cured
          and "req (log (exp_neg u) (exp_neg_pos u)) (opp u)." in cured
          and "Definition shadow_binder (log : nat) (n : nat) := n + log."
          in cured)
    # variant (b) alone on a fresh copy: qualify to the global direct face
    tgt = os.path.join(tmp, "shadow_b.v")
    shutil.copy(SHADOW_F, tgt)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--apply",
             "--only", "cure12_shadow_direct_face_qualify"])
    check("variant (b) apply rc=0", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode()[-300:])
    cured = io.open(tgt, encoding="utf-8").read()
    check("variant (b) qualified all five shadowed tokens",
          "S02_CauchyComplete.real_eq (S07_RealSetoidExpLog.real_log "
          "(S07_RealSetoidExpLog.real_exp_neg u) "
          "(S07_RealSetoidExpLog.real_exp_neg_pos u)) "
          "(S02_CauchyComplete.real_opp u)." in cured
          and "Import RealInterfaceEnhancedMod." in cured
          and "Definition shadow_binder (log : nat) (n : nat) := n + log."
          in cured)
    # negative: same bare shape without the Import — zero matches
    r = run([sys.executable, "-B", APPLIER, "--file", SHADOW_PLAIN_F])
    check("no-import file: both variants at zero matches",
          "total matches: 0" in r.stdout.decode())
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
