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
     carrier face) fails — the opacity the cure3 pattern addresses.  The
     v1.4.1 compile-leg arc runs here too: the old-class disease form is
     intercepted by the --apply compile leg (rc 1, file untouched), the
     shipped class cures canonically, the cured face compiles after the
     documented proof re-fit, and the leg records a real compile-ok pass.
     Skipped (rc 111) when ROCWASH_ROCQ is unset, so external clones pass
     without a toolchain.
  6. v1.2 S07-lineage flows: the cure32 adaptation arc — pre-cure station
     count (report-only, file untouched), full-pack dry-run counts on the
     base fixture, apply + documented binder surgery + all-zero re-run,
     and the exclusive-group conflict regression (rc 4 with --json, report
     written, no traceback).  The env-gated compile section also runs the
     S07 arc end to end: the miniature world compiles, the base consumer
     fails with "Illegal application", the cured consumer (after the
     documented binder surgery) compiles rc=0, and Separate Extraction
     reports Obj.magic 0 on every .ml/.mli with the bare fields resolved
     through the global instance.
  7. v1.3 E2/E3 flows (CI #178 extraction-defect families): pack
     integrity for the five cure34 patterns, fixture flows for both
     families (dry-run counts on the pre-fix miniatures, apply, all-zero
     re-run, report-only station residual), and the env-gated compile arc:
     the miniature world compiles, both pre-fix consumers compile green
     (these families are extraction-time defects, not compile-time ones —
     the red face of record is the extraction census), the cured consumers
     compile rc=0, and the extraction census shows magic 0/0 with the
     monomorphic station faces (E3 shim call; E2 "val unann : nat -> nat"
     on the .mli).  Compile sections are skipped (rc 111) when ROCWASH_ROCQ
     is unset, so external clones pass without a toolchain.
  8. v1.4 corpus-survey flow (cure39, b48-52 wash-work stream citation): the
     interface-quantified connective qualification — dry-run station
     count on the T13 miniature (10 = two compat statements x five
     connective stations), apply rc=0 with the qualified faces and the
     guarded negatives (Definition face, binder declaration, already-
     qualified face, proof witness call) verbatim, re-run zero, and the
     differently-named-context negative fixture at zero matches (the
     file_include gate pins the exact RI0 context face).
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


def _bash_argv():
    """bash invocation argv for the cpu_guard wrapper.  On Windows, bare
    "bash" in a subprocess resolves to the System32 WSL Store stub
    (CreateProcess searches System32 before PATH; the stub answers with a
    UTF-16 'wsl --update' banner and a nonzero rc), so resolve explicitly:
    ROCWASH_BASH overrides, then a PATH scan that skips the known stub;
    other platforms keep the plain name."""
    if os.name != "nt":
        return ["bash"]
    override = os.environ.get("ROCWASH_BASH", "")
    if override and os.path.isfile(override):
        return [override]
    for d in os.environ.get("PATH", "").split(os.pathsep):
        p = os.path.join(d, "bash.exe")
        if os.path.isfile(p) and "system32" not in p.lower():
            return [p]
    return ["bash"]


BASH_ARGV = _bash_argv()


# 1. applier mechanics
r = run([sys.executable, "-B", APPLIER, "--selftest"])
check("applier --selftest rc=0", r.returncode == 0,
      "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])

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
want_v32 = {"cure32_A_param_shell_drop", "cure32_B_notation_rebind",
            "cure32_C_atfield_bridge_bare",
            "cure32_C_predicate_face_converge",
            "cure32_station_binder_shell"}
want_v34 = {"cure34_E3_use_station_spec", "cure34_E3_spec_shim",
            "cure34_E2_field_annot", "cure34_E2_use_arity",
            "cure34_E2_station_unannot"}
want_v39 = {"cure39_ifq_connective_qualify"}
check("legacy five present", want_legacy <= set(ids))
check("v1.1 nine present", want_v31 <= set(ids))
check("v1.2 five present", want_v32 <= set(ids))
check("v1.3 five present", want_v34 <= set(ids))
check("v1.4 one present", want_v39 <= set(ids))
check("pattern count 5+9+5+5+1", len(pack["patterns"]) == 25)
check("pack version 1.4.1", pack["version"] == "1.4.1")
check("every pattern has trigger+template+idempotence",
      all(("trigger_regex" in p or "trigger" in p or "token_map" in p
           or "station_regex" in p or "insert_line" in p)
          and ("template" in p or "template_fn" in p or "token_map" in p
               or "insert_line" in p or "station_regex" in p)
          and "idempotence_note" in p for p in pack["patterns"]))
check("v1.1 patterns carry lineage",
      all("v31_lineage" in p for p in pack["patterns"]
          if p["id"] in want_v31))
check("v1.2 patterns carry lineage",
      all("v32_lineage" in p for p in pack["patterns"]
          if p["id"] in want_v32))
check("v1.3 patterns carry lineage",
      all("v34_lineage" in p for p in pack["patterns"]
          if p["id"] in want_v34))
check("v1.4 patterns carry lineage",
      all("v39_lineage" in p for p in pack["patterns"]
          if p["id"] in want_v39))
check("v1.4 targets are the three interface connectives",
      dict((p["id"], p) for p in pack["patterns"]
           if p["id"] == "cure39_ifq_connective_qualify"
           )["cure39_ifq_connective_qualify"]["token_targets"]
      == {"lt": "@S01_BaseRing.lt RI0", "le": "@S01_BaseRing.le RI0",
          "plus": "@S01_BaseRing.plus RI0"})
check("exclusive group declared on both shadow variants",
      [p.get("exclusive_group") for p in pack["patterns"]
       if p["id"].startswith(("cure11", "cure12"))] == ["import-shadow"] * 2)
check("station pattern is report-only",
      [p.get("mode") for p in pack["patterns"]
       if p["id"] == "cure32_station_binder_shell"] == ["report"])
check("v1.3 station pattern is report-only",
      [p.get("mode") for p in pack["patterns"]
       if p["id"] == "cure34_E2_station_unannot"] == ["report"])
check("v1.3 E3 pair ordered station-rewrite before shim-insert",
      [p["id"] for p in pack["patterns"]
       if p["id"].startswith("cure34_E3")][0] == "cure34_E3_use_station_spec")
check("convergence targets the supply lemma's own constant",
      dict((p["id"], p) for p in pack["patterns"]
           if p["id"] == "cure32_C_predicate_face_converge"
           )["cure32_C_predicate_face_converge"]["token_map"]["req"]
      == "real_eq"
      and "real_eq x x" in io.open(
          os.path.join(HERE, "fixtures", "cure32_s07_world.v"),
          encoding="utf-8").read())

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
          "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
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
          "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-400:])
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
          "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-400:])
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
          r.stdout.decode("utf-8", "replace")[-200:])
    check("conflict left the file untouched",
          io.open(tgt, encoding="utf-8").read() == before_txt)
    # variant (a) alone: delete the shadowing Import line
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--apply",
             "--only", "cure11_import_shadow_delete"])
    check("variant (a) apply rc=0", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
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
          "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
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
          "total matches: 0" in r.stdout.decode("utf-8", "replace"))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# 5. v1.2 fixture flows: the S07-lineage adaptation arc (cure32)
S07_WORLD_F = os.path.join(HERE, "fixtures", "cure32_s07_world.v")
S07_F = os.path.join(HERE, "fixtures", "cure32_s07_fixture.v")

tmp = tempfile.mkdtemp(prefix="rw_cure32_")
try:
    # 5a. pre-cure station count: the report-only station sees the alien
    #     binder pair and never touches the file (md5 identical)
    tgt = os.path.join(tmp, "fixture_base.v")
    shutil.copy(S07_F, tgt)
    base_txt = io.open(tgt, encoding="utf-8").read()
    r = run([sys.executable, "-B", APPLIER, "--file", tgt,
             "--only", "cure32_station_binder_shell", "--json",
             os.path.join(tmp, "station.json")])
    dry = json.load(io.open(os.path.join(tmp, "station.json"),
                            encoding="utf-8"))
    check("station pre-cure count=1 (report-only)",
          dry["report"]["cure32_station_binder_shell"]["matches"] == 1)
    check("station run wrote nothing",
          io.open(tgt, encoding="utf-8").read() == base_txt)

    # 5b. full-pack dry-run counts on the base fixture
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--json",
             os.path.join(tmp, "dry32.json")])
    dry = json.load(io.open(os.path.join(tmp, "dry32.json"),
                            encoding="utf-8"))
    rep = dry["report"]
    check("dry-run A=2 B=1 C(a)=5 C(b)=2 residual-station=0",
          rep["cure32_A_param_shell_drop"]["matches"] == 2
          and rep["cure32_B_notation_rebind"]["matches"] == 1
          and rep["cure32_C_atfield_bridge_bare"]["matches"] == 5
          and rep["cure32_C_predicate_face_converge"]["matches"] == 2
          and rep["cure32_station_binder_shell"]["matches"] == 0)

    # 5c. apply the mechanical cures, then the documented manual binder
    #     surgery (the pair (R : Set) {RIS : ...} goes away together with
    #     the intros names — the station's reported positions), then the
    #     re-run is all-zero
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--apply"])
    check("S07 fixture apply rc=0", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-400:])
    cured = io.open(tgt, encoding="utf-8").read()
    check("shell dropped at annotation and binder",
          ": RealInterfaceEnhancedSetoid :=" in cured
          and "{RIS : RealInterfaceEnhancedSetoid}" in cured)
    check("notation rebind inserted after the import",
          "Require Import Cure32S07World.\nNotation R := Real." in cured)
    check("bridges bare + predicate faces converged",
          "real_lt zero (Z_align_req beta) ->" in cured
          and "real_eq (Z_align_req beta) (Z_align_req beta)." in cured
          and "mult (one_pos) (Z_align_req beta)." in cured
          and "@Z_align_req Real ufx_ren" not in cured)
    cured = re.sub(r"forall \(R : Set\) \{RIS : RealInterfaceEnhancedSetoid\}"
                   r"\s*\(beta : R\),", "forall beta : Real,", cured)
    cured = cured.replace("intros R RIS beta Hz.", "intros beta Hz.")
    io.open(tgt, "w", encoding="utf-8").write(cured)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--json",
             os.path.join(tmp, "dry32b.json")])
    dry = json.load(io.open(os.path.join(tmp, "dry32b.json"),
                            encoding="utf-8"))
    check("post-surgery re-run all-zero (station residual included)",
          all(v["matches"] == 0 for v in dry["report"].values()))

    # 5d. exclusive-group conflict regression (v32 fix): with --json the
    #     conflict path writes the report and exits 4 (no traceback)
    cfile = os.path.join(tmp, "conflict.v")
    io.open(cfile, "w", encoding="utf-8").write(
        "Require Import S02_CauchyComplete.\n"
        "Import RealInterfaceEnhancedMod.\n"
        "Theorem r1 : forall u : Real, req u (opp u).\n"
        "Proof. intros. apply r0. Qed.\n")
    cj = os.path.join(tmp, "conflict.json")
    r = run([sys.executable, "-B", APPLIER, "--file", cfile, "--json", cj])
    check("conflict rc=4 with --json (report written, no traceback)",
          r.returncode == 4 and os.path.exists(cj)
          and b"UnboundLocalError" not in r.stdout
          and json.load(io.open(cj, encoding="utf-8"))
          .get("exclusive_group_conflict") is not None)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# 6. v1.3 fixture flows: the E2/E3 extraction-defect families (cure34)
E23_WORLD_F = os.path.join(HERE, "fixtures", "cure34_e23_world.v")
E3_F = os.path.join(HERE, "fixtures", "cure34_e3_fixture.v")
E2_F = os.path.join(HERE, "fixtures", "cure34_e2_fixture.v")

tmp = tempfile.mkdtemp(prefix="rw_cure34_")
try:
    # 6a. E3 pre-fix miniature: station rewrite (statement faces) + shim
    #     insert after the import; the shim body keeps the abstract
    #     application verbatim; re-run all-zero
    tgt = os.path.join(tmp, "e3.v")
    shutil.copy(E3_F, tgt)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt,
             "--only", "cure34_E3_use_station_spec,cure34_E3_spec_shim",
             "--json", os.path.join(tmp, "dry34e3.json")])
    dry = json.load(io.open(os.path.join(tmp, "dry34e3.json"),
                            encoding="utf-8"))
    rep = dry["report"]
    check("E3 dry-run stations=2 shim=1",
          rep["cure34_E3_use_station_spec"]["matches"] == 2
          and rep["cure34_E3_spec_shim"]["matches"] == 1)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--apply",
             "--only", "cure34_E3_use_station_spec,cure34_E3_spec_shim"])
    check("E3 apply rc=0 (idempotence verified)", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-400:])
    cured = io.open(tgt, encoding="utf-8").read()
    check("E3 shim inserted after the import",
          "Require Import Cure34E23World.\n"
          "Definition gstep_spec (x : Real) : Real := gstep Real natIF x."
          in cured)
    check("E3 stations reshimmed (faces, shim body intact)",
          ":= gstep_spec n." in cured
          and "gstep_spec n = Nat.mul n n." in cured
          and ":= gstep Real natIF n." not in cured
          and "Definition gstep_spec (x : Real) : Real := gstep Real natIF x."
          in cured)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--json",
             os.path.join(tmp, "dry34e3b.json")])
    dry = json.load(io.open(os.path.join(tmp, "dry34e3b.json"),
                            encoding="utf-8"))
    check("E3 re-run zero matches",
          all(v["matches"] == 0 for v in dry["report"].values()))

    # 6b. E2 pre-fix miniature: annotated middleware + arity stations +
    #     report-only station residual dropping to zero
    tgt = os.path.join(tmp, "e2.v")
    shutil.copy(E2_F, tgt)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt,
             "--only", "cure34_E2_station_unannot", "--json",
             os.path.join(tmp, "dry34e2s.json")])
    dry = json.load(io.open(os.path.join(tmp, "dry34e2s.json"),
                            encoding="utf-8"))
    check("E2 pre-cure station count=1 (report-only)",
          dry["report"]["cure34_E2_station_unannot"]["matches"] == 1)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--apply",
             "--only", "cure34_E2_field_annot,cure34_E2_use_arity"])
    check("E2 apply rc=0 (idempotence verified)", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-400:])
    cured = io.open(tgt, encoding="utf-8").read()
    check("E2 middleware annotated + arity adapted",
          "Definition unann (n : nat) : nat := wf theW nat n." in cured
          and ":= unann n." in cured
          and "unann nat n" not in cured)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--json",
             os.path.join(tmp, "dry34e2b.json")])
    dry = json.load(io.open(os.path.join(tmp, "dry34e2b.json"),
                            encoding="utf-8"))
    check("E2 re-run all-zero (station residual included)",
          all(v["matches"] == 0 for v in dry["report"].values()))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# 8. v1.4 fixture flow: interface-quantified connective qualification
#    (cure39, b48-52 wash-work stream citation commit 9a51c74, UpAblT13
#    re-anchor form).  --only run: the miniature also carries the
#    shadowing Import line the campaign added, which cure11 (full pack)
#    would delete — the interplay is documented in the fixture header.
T13_F = os.path.join(HERE, "fixtures", "cure39_t13_fixture.v")
T13_PLAIN_F = os.path.join(HERE, "fixtures", "cure39_plain_fixture.v")

tmp = tempfile.mkdtemp(prefix="rw_cure39_")
try:
    tgt = os.path.join(tmp, "t13.v")
    shutil.copy(T13_F, tgt)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt,
             "--only", "cure39_ifq_connective_qualify", "--json",
             os.path.join(tmp, "dry39.json")])
    dry = json.load(io.open(os.path.join(tmp, "dry39.json"),
                            encoding="utf-8"))
    check("cure39 dry-run stations=10",
          dry["report"]["cure39_ifq_connective_qualify"]["matches"] == 10)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--apply",
             "--only", "cure39_ifq_connective_qualify"])
    check("cure39 apply rc=0 (idempotence verified)", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-400:])
    cured = io.open(tgt, encoding="utf-8").read()
    check("cure39 compat faces qualified",
          "@S01_BaseRing.lt RI0 a b -> @S01_BaseRing.le RI0 c d ->"
          in cured
          and "@S01_BaseRing.lt RI0 (@S01_BaseRing.plus RI0 a c) "
              "(@S01_BaseRing.plus RI0 b d)." in cured)
    check("cure39 guarded negatives untouched",
          "Definition keeper (le : nat) (n : nat) := n + le." in cured
          and "Lemma bnd_guard (lt : nat) : True." in cured
          and "Theorem already_qualified :\n  @S01_BaseRing.lt RI0 1 2 -> "
              "@S01_BaseRing.le RI0 2 3." in cured
          and "exact (@fa53_lt_plus_compat_lt_le_dec RI0 DO0 a b c d "
              "Hab Hcd)." in cured)
    r = run([sys.executable, "-B", APPLIER, "--file", tgt, "--json",
             os.path.join(tmp, "dry39b.json")])
    dry = json.load(io.open(os.path.join(tmp, "dry39b.json"),
                            encoding="utf-8"))
    check("cure39 re-run zero matches",
          dry["report"]["cure39_ifq_connective_qualify"]["matches"] == 0)
    # negative: same bare shape under a differently-named context
    # variable (RI, not RI0) — the file_include gate keeps it at zero
    r = run([sys.executable, "-B", APPLIER, "--file", T13_PLAIN_F,
             "--only", "cure39_ifq_connective_qualify"])
    check("differently-named context: zero matches (gate)",
          "total matches: 0" in r.stdout.decode("utf-8", "replace"),
          r.stdout.decode("utf-8", "replace")[-200:])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# compile check (env-gated, thermal-guard wrapped like every compile)
rocq = os.environ.get("ROCWASH_ROCQ", "")
if rocq and os.path.exists(rocq):
    guard = os.path.join(REPO, "tools", "cpu_guard.sh")
    tmp = tempfile.mkdtemp(prefix="rw_curec_")
    reg = os.path.join(tmp, "guard_reg")
    os.makedirs(reg, exist_ok=True)

    def guarded(args):
        return run(BASH_ARGV + [guard, "-Reg", reg, "-Front", "0", "-Mid", "1",
                    "-MaxWaitSec", "600", "--"] + args)
    try:
        ex = os.path.join(tmp, "cure_examples.v")
        shutil.copy(EXAMPLES, ex)
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", tmp, "", ex])
        check("cure_examples compiles rc=0 (guard-wrapped)", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
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

        # v32 S07 arc: world compiles -> base is the red face of record ->
        # mechanical cures + documented binder surgery -> green -> the
        # extraction gate reports Obj.magic 0 on every .ml/.mli.
        wdir = os.path.join(tmp, "world")
        os.makedirs(wdir)
        shutil.copy(S07_WORLD_F, os.path.join(wdir, "Cure32S07World.v"))
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", wdir, "", os.path.join(wdir, "Cure32S07World.v")])
        check("S07 world compiles rc=0", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
        basef = os.path.join(wdir, "Cure32S07Fixture.v")
        shutil.copy(S07_F, basef)
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", wdir, "", basef])
        sout = r.stdout.decode("utf-8", "replace")
        check("S07 base fails with Illegal application (red face of record)",
              r.returncode != 0 and "Illegal application" in sout,
              sout[-200:])
        r = run([sys.executable, "-B", APPLIER, "--file", basef, "--apply"])
        check("S07 mechanical cures apply rc=0", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-400:])
        t = io.open(basef, encoding="utf-8").read()
        t = re.sub(r"forall \(R : Set\) \{RIS : RealInterfaceEnhancedSetoid\}"
                   r"\s*\(beta : R\),", "forall beta : Real,", t)
        t = t.replace("intros R RIS beta Hz.", "intros beta Hz.")
        io.open(basef, "w", encoding="utf-8").write(t)
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", wdir, "", basef])
        check("S07 cured+surgery compiles rc=0", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
        extdir = os.path.join(tmp, "ext")
        os.makedirs(extdir)
        drv = os.path.join(extdir, "ext_driver.v")
        io.open(drv, "w", encoding="utf-8").write(
            "From Stdlib Require Import Extraction.\n"
            "Require Import Cure32S07Fixture.\n"
            "Separate Extraction Cure32S07Fixture.ufx_sample.\n")
        # extraction output lands in the driver's cwd — pin it to extdir so
        # nothing leaks into the repo
        r = run(BASH_ARGV + [guard, "-Reg", reg, "-Front", "0", "-Mid", "1",
                 "-MaxWaitSec", "600", "--", rocq, "c",
                 "-native-compiler", "no", "-q", "-Q", wdir, "", drv],
                cwd=extdir)
        check("extraction run rc=0", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
        magics, mfiles = 0, 0
        for name in os.listdir(extdir):
            if name.endswith(".ml") or name.endswith(".mli"):
                mfiles += 1
                with io.open(os.path.join(extdir, name), encoding="utf-8",
                             errors="replace") as fh:
                    magics += fh.read().count("Obj.magic")
        check("extraction gate Obj.magic=0 on every .ml/.mli",
              r.returncode == 0 and magics == 0 and mfiles >= 2,
              "files=%d magics=%d" % (mfiles, magics))
        mlp = os.path.join(extdir, "Cure32S07Fixture.ml")
        check("extracted code resolves bare fields via the instance",
              os.path.exists(mlp)
              and "coq_RealEnhancedReal" in io.open(
                  mlp, encoding="utf-8", errors="replace").read())

        # v34 E2/E3 arc: the miniature world compiles, both pre-fix
        # consumers compile green (these families are extraction-time
        # defects — the red face of record is the extraction census, the
        # CI #178 shape), the cured consumers compile rc=0, and the
        # extraction census shows magic 0/0 with the monomorphic station
        # faces (E3 shim call; E2 "val unann : nat -> nat" on the .mli).
        w34dir = os.path.join(tmp, "world34")
        os.makedirs(w34dir)
        shutil.copy(E23_WORLD_F, os.path.join(w34dir, "Cure34E23World.v"))
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", w34dir, "",
                     os.path.join(w34dir, "Cure34E23World.v")])
        check("E23 world compiles rc=0", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])

        e3f = os.path.join(w34dir, "Cure34E3Fixture.v")
        shutil.copy(E3_F, e3f)
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", w34dir, "", e3f])
        check("E3 pre-fix compiles green (extraction-time family)",
              r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
        r = run([sys.executable, "-B", APPLIER, "--file", e3f, "--apply"])
        check("E3 cures apply rc=0", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-400:])
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", w34dir, "", e3f])
        check("E3 cured compiles rc=0", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
        e3ext = os.path.join(tmp, "ext34e3")
        os.makedirs(e3ext)
        drv = os.path.join(e3ext, "ext_driver.v")
        io.open(drv, "w", encoding="utf-8").write(
            "From Stdlib Require Import Extraction.\n"
            "Require Import Cure34E3Fixture.\n"
            "Separate Extraction Cure34E3Fixture.ufx_nat.\n")
        r = run(BASH_ARGV + [guard, "-Reg", reg, "-Front", "0", "-Mid", "1",
                 "-MaxWaitSec", "600", "--", rocq, "c",
                 "-native-compiler", "no", "-q", "-Q", w34dir, "", drv],
                cwd=e3ext)
        magics = 0
        for name in ("Cure34E3Fixture.ml", "Cure34E3Fixture.mli"):
            p = os.path.join(e3ext, name)
            if os.path.exists(p):
                with io.open(p, encoding="utf-8", errors="replace") as fh:
                    magics += fh.read().count("Obj.magic")
        check("E3 extraction rc=0 magic 0/0 (consumer units)",
              r.returncode == 0 and magics == 0,
              "rc=%d magics=%d" % (r.returncode, magics))
        e3ml = os.path.join(e3ext, "Cure34E3Fixture.ml")
        e3ml_text = ""
        if os.path.exists(e3ml):
            e3ml_text = io.open(e3ml, encoding="utf-8",
                                errors="replace").read()
        check("E3 extracted station monomorphic (shim call)",
              "let ufx_nat =\n  gstep_spec" in e3ml_text
              and "val ufx_nat : coq_Real -> coq_Real" in e3ml_text,
              e3ml_text[-160:] if e3ml_text else "ml missing")

        e2f = os.path.join(w34dir, "Cure34E2Fixture.v")
        shutil.copy(E2_F, e2f)
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", w34dir, "", e2f])
        check("E2 pre-fix compiles green (extraction-time family)",
              r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
        e2pre_ext = os.path.join(tmp, "ext34e2pre")
        os.makedirs(e2pre_ext)
        drv = os.path.join(e2pre_ext, "ext_driver.v")
        io.open(drv, "w", encoding="utf-8").write(
            "From Stdlib Require Import Extraction.\n"
            "Require Import Cure34E2Fixture.\n"
            "Separate Extraction Cure34E2Fixture.use_unann.\n")
        r = run(BASH_ARGV + [guard, "-Reg", reg, "-Front", "0", "-Mid", "1",
                 "-MaxWaitSec", "600", "--", rocq, "c",
                 "-native-compiler", "no", "-q", "-Q", w34dir, "", drv],
                cwd=e2pre_ext)
        e2mli_pre = os.path.join(e2pre_ext, "Cure34E2Fixture.mli")
        pre_sig = ""
        if os.path.exists(e2mli_pre):
            pre_sig = io.open(e2mli_pre, encoding="utf-8",
                              errors="replace").read()
        check("E2 pre-cure face polymorphic ('a -> 'a)",
              "'a1 -> 'a1" in pre_sig,
              pre_sig[-120:] if pre_sig else "mli missing")
        r = run([sys.executable, "-B", APPLIER, "--file", e2f, "--apply"])
        check("E2 cures apply rc=0", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-400:])
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", w34dir, "", e2f])
        check("E2 cured compiles rc=0", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
        e2ext = os.path.join(tmp, "ext34e2")
        os.makedirs(e2ext)
        drv = os.path.join(e2ext, "ext_driver.v")
        io.open(drv, "w", encoding="utf-8").write(
            "From Stdlib Require Import Extraction.\n"
            "Require Import Cure34E2Fixture.\n"
            "Separate Extraction Cure34E2Fixture.use_unann.\n")
        r = run(BASH_ARGV + [guard, "-Reg", reg, "-Front", "0", "-Mid", "1",
                 "-MaxWaitSec", "600", "--", rocq, "c",
                 "-native-compiler", "no", "-q", "-Q", w34dir, "", drv],
                cwd=e2ext)
        magics_cons = 0
        for name in ("Cure34E2Fixture.ml", "Cure34E2Fixture.mli"):
            p = os.path.join(e2ext, name)
            if os.path.exists(p):
                with io.open(p, encoding="utf-8", errors="replace") as fh:
                    magics_cons += fh.read().count("Obj.magic")
        e2mli = os.path.join(e2ext, "Cure34E2Fixture.mli")
        post_sig = ""
        if os.path.exists(e2mli):
            post_sig = io.open(e2mli, encoding="utf-8",
                               errors="replace").read()
        check("E2 cured face monomorphic (nat -> nat)",
              r.returncode == 0 and "nat -> nat" in post_sig,
              post_sig[-120:] if post_sig else "mli missing")
        # honesty boundary, mechanically pinned: the consumer unit extracts
        # clean, while the world-generation accessor cast (the wf projection
        # of the inside-polymorphic field) stays exactly where the fixture
        # world header and the pack canonical note document it - world-side
        # debt owned by the entity-repair workflow, out of reach of
        # consumer-side text cures
        e2wml = os.path.join(e2ext, "Cure34E23World.ml")
        wmagic = 0
        if os.path.exists(e2wml):
            wmagic = io.open(e2wml, encoding="utf-8",
                             errors="replace").read().count("Obj.magic")
        check("E2 consumer-unit magic 0/0; world accessor debt pinned=1",
              magics_cons == 0 and wmagic == 1,
              "consumer magics=%d world magics=%d" % (magics_cons, wmagic))

        # v1.4.1 compile-leg arc (T0-2/T0-3, audit P0-2/P0-3): the disease
        # form of the old lhs class is intercepted by the --apply compile
        # leg, the shipped (tightened) class cures canonically, the cured
        # statement face compiles after the documented proof re-fit, and
        # the leg records a real compile-ok pass.  The proof re-fit mirrors
        # the documented binder surgery of the S07 arc above: statement-
        # face downshifts obligate a downstream proof re-fit (cure10 exists
        # for exactly this), so the arc pins the obligation instead of
        # hiding it.
        legdir = os.path.join(tmp, "leg")
        os.makedirs(legdir)
        disease = os.path.join(legdir, "disease.v")
        io.open(disease, "w", encoding="utf-8", newline="\n").write(
            "From Stdlib Require Import QArith.QArith QArith.Qabs List.\n"
            "Import ListNotations.\n"
            "Definition QleT' (x y : Q) : Set := (Qle_bool x y) = true.\n"
            "\n"
            "Lemma lem1 : forall x : Q, In x [0; 0; 2] -> Qabs x <= 2%Q.\n"
            "Proof.\n"
            "  intros x Hx. simpl in Hx.\n"
            "  destruct Hx as [Hx|[Hx|[Hx|[]]]]; subst x;\n"
            "    apply (proj1 (Qle_bool_iff _ _)); vm_compute; reflexivity.\n"
            "Qed.\n")
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", legdir, "", disease])
        check("disease base file compiles rc=0", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
        old_pack_path = os.path.join(legdir, "old_class_pack.json")
        old_pack = json.load(io.open(PACK, encoding="utf-8"))
        tightened = old_pack["patterns"][0]  # marker: replacement verified below
        replaced = 0
        for p in old_pack["patterns"]:
            if p["id"] in ("cure7_qle_notation_downshift",
                           "cure9_qlt_notation_downshift"):
                if "(?<![A-Za-z0-9_'])(?P<lhs>[^\\n()<>=:,-]+?)" \
                        in p["trigger_regex"]:
                    p["trigger_regex"] = p["trigger_regex"].replace(
                        "(?<![A-Za-z0-9_'])(?P<lhs>[^\\n()<>=:,-]+?)",
                        "(?P<lhs>[^\\n()<>=-]+?)", 1)
                    p["idempotence_note"] = \
                        "old-class probe pack (pre-v1.4.1 trigger)"
                    replaced += 1
        check("old-class probe pack built (two triggers reverted)",
              replaced == 2 and tightened is not None)
        json.dump(old_pack, io.open(old_pack_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        d_old = os.path.join(legdir, "disease_old.v")
        shutil.copy(disease, d_old)
        before_bytes = io.open(d_old, "rb").read()
        r = run([sys.executable, "-B", APPLIER, "--file", d_old,
                 "--pack", old_pack_path,
                 "--only", "cure7_qle_notation_downshift", "--apply"])
        sout = r.stdout.decode("utf-8", "replace")
        check("old-class disease intercepted by the compile leg (rc=1)",
              r.returncode == 1 and "compile-regression intercepted" in sout,
              sout[-200:])
        check("intercepted file NOT written (byte-constant)",
              io.open(d_old, "rb").read() == before_bytes)
        d_new = os.path.join(legdir, "canon_new.v")
        io.open(d_new, "w", encoding="utf-8", newline="\n").write(
            "From Stdlib Require Import QArith.QArith QArith.Qabs List.\n"
            "Import ListNotations.\n"
            "Definition QleT' (x y : Q) : Set := (Qle_bool x y) = true.\n"
            "\n"
            "Lemma lem1 : forall x : Q, (Qle_bool x (2#1)) = true -> "
            "x <= 2%Q.\n"
            "Proof.\n"
            "  intros x H. apply (proj1 (Qle_bool_iff _ _)). exact H.\n"
            "Qed.\n")
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", legdir, "", d_new])
        check("canonical base file compiles rc=0", r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
        r = run([sys.executable, "-B", APPLIER, "--file", d_new,
                 "--only", "cure7_qle_notation_downshift", "--apply",
                 "--rocq", ""])
        check("shipped class cures canonically (leg not configured -> rc=0)",
              r.returncode == 0, r.stdout.decode("utf-8", "replace")[-200:])
        cured_text = io.open(d_new, encoding="utf-8").read()
        check("cured face canonical; head-eating form absent",
              "= true -> QleT' x 2%Q." in cured_text
              and "QleT' (Lemma" not in cured_text)
        # documented proof re-fit: the premise already carries the carrier
        # face's bool equation, so the cured Set goal closes by exact H
        # (the re-fit obligation of a statement-face downshift; the old
        # goal-Prop form would break here by or-elimination into Set)
        refit = cured_text.replace(
            "intros x H. apply (proj1 (Qle_bool_iff _ _)). exact H.",
            "intros x H. exact H.")
        io.open(d_new, "w", encoding="utf-8", newline="\n").write(refit)
        r = guarded([rocq, "c", "-native-compiler", "no", "-q",
                     "-Q", legdir, "", d_new])
        check("cured face + documented proof re-fit compiles rc=0",
              r.returncode == 0,
              "" if r.returncode == 0 else r.stdout.decode("utf-8", "replace")[-300:])
        # a real before/after compile-ok pass through the leg: a proof- and
        # semantics-agnostic probe pattern (inserts one valid Definition)
        probe_pack_path = os.path.join(legdir, "leg_probe_pack.json")
        json.dump({"pack": "leg_probe", "version": "0", "patterns": [
            {"id": "leg_probe_insert", "title": "compile-leg pass probe",
             "engine": "line-insert",
             "insert_line": "Definition leg_probe := 1.",
             "insert_after": "last-import",
             "idempotence_note": "present line skips (count 0)"}]},
            io.open(probe_pack_path, "w", encoding="utf-8"),
            ensure_ascii=False, indent=1)
        d_pass = os.path.join(legdir, "leg_pass.v")
        shutil.copy(disease, d_pass)
        r = run([sys.executable, "-B", APPLIER, "--file", d_pass,
                 "--pack", probe_pack_path, "--apply"])
        sout = r.stdout.decode("utf-8", "replace")
        check("compile leg records a real compile-ok pass (rc pair 0/0)",
              r.returncode == 0 and "COMPILE-LEG: compile-ok" in sout
              and "(rc before=0 after=0)" in sout, sout[-200:])
        check("probe insert landed on disk",
              "Definition leg_probe := 1." in io.open(
                  d_pass, encoding="utf-8").read())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
else:
    print("  compile check: SKIP (ROCWASH_ROCQ unset)")

print("TEST-CURE-PACK:", "PASS" if not fails else "FAIL %s" % fails)
sys.exit(0 if not fails else 1)
