#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_abl1_wash.py - batch exact-string patch applier for the abl1 ablation proof tree.

Purpose.  Applies the fixed per-file patch ledger in `PATCHES` to the hardcoded
  absolute `ROOT` tree: each entry is a (tag, old, new, expect) tuple, applied
  only when the file holds exactly `expect` occurrences of `old`; after the
  replace the count of `new` must reach `expect` (assertion on, fail loud).
  Idempotent: an entry whose `new` is already present at least `expect` times
  while `old` occurs zero times is skipped; per file, one failed entry leaves
  the whole file unwritten.

Interface.  `python3 wash/_abl1_wash.py` - no flags, no arguments; `ROOT` is
  hardcoded by design and `main()` runs only under `__main__`.  Output: one
  line per entry (`APPLY` / `SKIP` / `FAIL` with file, tag and counts) plus
  one summary line `--- applied=N skipped=N fail=YES|NO`.  Per-entry old/new
  strings are recorded in `station_ledger.md` beside the target tree;
  `tests/test_wash_fixture.py` imports this module, points `ROOT` at a temp
  fixture and asserts on this exact output.

Dependencies.  Python 3 standard library only (`sys`, `os`, `re`); run as a script
  it rewrites the target files in place under `ROOT`; no network, no compiler.

Evidence.  `tests/run_tests.sh:336` runs `tests/test_wash_fixture.py`, which seeds
  a temp fixture from `PATCHES` and asserts the positive / idempotent-replay /
  negative triple: all-apply with on-disk count checks, replay skips,
  corrupted `old` failing loud, file left byte-identical.

Exit-codes.  0 = every entry applied or skipped; 1 = at least one entry failed
  its count assertion (fail loud; the failing file is not written).
"""
import sys, os, re

ROOT = "/Users/apple/Desktop/S系Prop清除战役工单/work_Main_full/sandbox/seat_abl1/src"
POW = [("abl_archpa04_step_calc", "ap4"), ("abl_attniter_step_calc", "aic"),
       ("abl_cw220_step_calc", "cw2"), ("abl_mixchain_step_calc", "mtc2"),
       ("abl_p2a_step_calc", "p2c"), ("abl_s06_step_calc", "sdc")]

def patches_for_pow(fname, P):
    com = f"{P}_pow_iter_comm"
    base = [
        # statement rewrite: bare = -> Id (conclusion position)
        (f"stmt",
         f"  {P}_pow_iter p q ({P}_iter p q x) k = {P}_iter p q ({P}_pow_iter p q x k).\n",
         f"  Id ({P}_pow_iter p q ({P}_iter p q x) k)\n     ({P}_iter p q ({P}_pow_iter p q x k)).\n",
         1),
        # proof body: reflexivity -> apply `id_refl`; rewrite IH -> `id_cong`
        # congruence (Id is not a setoid)
        (f"proof",
         "  intros p q x k. induction k as [| k IH].\n"
         "  - simpl. reflexivity.\n"
         "  - simpl. rewrite IH. simpl. reflexivity.\n",
         "  intros p q x k. induction k as [| k IH].\n"
         "  - simpl. apply id_refl.\n"
         f"  - simpl. exact (id_cong ({P}_iter p q) IH).\n",
         1),
        # consumer sites x2 (in-hypothesis): `rewrite <- ... in Hbound` ->
        # revert + destruct (`Id` indexed abstraction)
        (f"inhyp",
         f"rewrite <- ({com} p q x k') in Hbound.",
         f"revert Hbound. destruct ({com} p q x k'). intros Hbound.",
         2),
        # consumer site (goal, two-line form): rewrite <- -> destruct
        (f"goal2l",
         f"        rewrite <- ({com} p q x\n                      ({P}_k_enum f p q ({P}_iter p q x) e)).\n",
         f"        destruct ({com} p q x\n                    ({P}_k_enum f p q ({P}_iter p q x) e)).\n",
         1),
        # consumer site (goal, j')
        (f"goalj",
         f"simpl. rewrite <- ({com} p q x j'). exact IH.",
         f"simpl. destruct ({com} p q x j'). exact IH.",
         1),
        # consumer site (goal, k0)
        (f"goalk0",
         f"* simpl. rewrite <- ({com} p q x k0). exact Hb0.",
         f"* simpl. destruct ({com} p q x k0). exact Hb0.",
         1),
    ]
    if P == "mtc2":
        # mixchain shape differs: one in-hypothesis site only; goal site in
        # single-line form; no goal-j site (verified at L167/L175/L320)
        base[3] = ("goal1l",
                   f"        rewrite <- ({com} p q x ({P}_k_enum f p q ({P}_iter p q x) e)).\n",
                   f"        destruct ({com} p q x ({P}_k_enum f p q ({P}_iter p q x) e)).\n",
                   1)
        base = [b for b in base if b[0] != "goalj"]
        base[2] = (base[2][0], base[2][1], base[2][2], 1)
    return base

PATCHES = {f"{f}.v": patches_for_pow(f, p) for f, p in POW}
PATCHES["abl_audit_base_v5.v"] = [
    ("stmt",
     "    sf_consensus_iter agents (k1 + k2)\n    = sf_consensus_iter (sf_consensus_iter agents k1) k2.\n",
     "    Id (sf_consensus_iter agents (k1 + k2))\n       (sf_consensus_iter (sf_consensus_iter agents k1) k2).\n", 1),
    ("proof",
     "  intros k1. induction k1 as [| k1' IH]; intros agents k2.\n  - reflexivity.\n",
     "  intros k1. induction k1 as [| k1' IH]; intros agents k2.\n  - apply id_refl.\n", 1),
    ("consumer",
     "  rewrite (abe_consensus_iter_add k1 agents k2).\n",
     "  destruct (id_sym (abe_consensus_iter_add k1 agents k2)).\n", 1),
]
PATCHES["abl_audit_base_v7.v"] = [
    ("require",
     "Require Import G10_LoebFam.\n",
     "Require Import G10_LoebFam.\nRequire Import S01_BaseRing (NatLe, NatLe_drop).\n", 1),
    ("stmt",
     "     (gnPrf f pf <= k)%nat ->\n",
     "     NatLe (gnPrf f pf) k ->\n", 1),
    ("proof",
     "    intros f pf k Hk. exact (gnPrf_replay f pf k Hk).\n",
     "    intros f pf k Hk. exact (gnPrf_replay f pf k (NatLe_drop _ _ Hk)).\n", 1),
]
PATCHES["abl_arctan_diff_40.v"] = [
    ("stmt",
     "  d * Qinv (1 + a * a)\n"
     "  - ((a + d - b) * Qinv (1 + (a + d) * b) - (a - b) * Qinv (1 + a * b))\n"
     "    * ((1 + a * b) * (1 + a * b) * Qinv ((1 + a * a) * (1 + b * b))) ==\n"
     "  d * d * b * Qinv ((1 + (a + d) * b) * (1 + a * a)).\n",
     "  QeqT (d * Qinv (1 + a * a)\n"
     "  - ((a + d - b) * Qinv (1 + (a + d) * b) - (a - b) * Qinv (1 + a * b))\n"
     "    * ((1 + a * b) * (1 + a * b) * Qinv ((1 + a * a) * (1 + b * b))))\n"
     "  (d * d * b * Qinv ((1 + (a + d) * b) * (1 + a * a))).\n", 1),
    ("proof",
     "  unfold Qdiv in Hcore.\n  exact Hcore.\n",
     "  unfold Qdiv in Hcore.\n  apply qeq_imp_qeqT. exact Hcore.\n", 1),
    ("consumer",
     "  apply (abl9_slope_id_pt (projT1 u n) (projT1 v n) (projT1 h n) Hnz1 Hnz2).\n",
     "  exact (qeqT_imp_qeq _ _\n          (abl9_slope_id_pt (projT1 u n) (projT1 v n) (projT1 h n) Hnz1 Hnz2)).\n", 1),
]
PATCHES["ablt9_rhscc_scinst.v"] = [
    ("stmt",
     "  abl9b_ext_km (Datatypes.S m) == abl9b_ksc m.\n",
     "  QeqT (abl9b_ext_km (Datatypes.S m)) (abl9b_ksc m).\n", 1),
    ("proof",
     "  intros m. unfold abl9b_ext_km, abl9b_ksc, Qdiv, Qeq.\n"
     "  cbn [Z.of_nat Pos.mul Qnum Qden Qmult Qplus Qopp Qminus Qinv].\n"
     "  rewrite ?abl9b_zpos_succ. ring.\n",
     "  intros m.\n"
     "  assert (Hcore : abl9b_ext_km (Datatypes.S m) == abl9b_ksc m).\n"
     "  { unfold abl9b_ext_km, abl9b_ksc, Qdiv, Qeq.\n"
     "    cbn [Z.of_nat Pos.mul Qnum Qden Qmult Qplus Qopp Qminus Qinv].\n"
     "    rewrite ?abl9b_zpos_succ. ring. }\n"
     "  apply qeq_imp_qeqT. exact Hcore.\n", 1),
    ("consumer",
     "  rewrite ablt9_rhscc_km_ksc.\n",
     "  rewrite (qeqT_imp_qeq _ _ (ablt9_rhscc_km_ksc m)).\n", 1),
]

def main():
    total_applied = total_skipped = 0
    any_fail = False
    for fname, plist in PATCHES.items():
        path = os.path.join(ROOT, fname)
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
        file_fail = False
        for tag, old, new, expect in plist:
            c_old = content.count(old)
            c_new = content.count(new)
            if c_new >= expect and c_old == 0:
                print(f"SKIP  {fname}:{tag}  (already applied)")
                total_skipped += 1
                continue
            if c_old != expect:
                print(f"FAIL  {fname}:{tag}  count(old)={c_old} expect={expect}  -- no edit")
                file_fail = True
                any_fail = True
                continue
            content = content.replace(old, new)
            assert content.count(new) >= expect, f"post-assert {fname}:{tag}"
            print(f"APPLY {fname}:{tag}  old={c_old} -> new inserted")
            total_applied += 1
        if not file_fail:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
        else:
            print(f"!!!   {fname}  NOT WRITTEN (fail-loud; correct the ledger entry, then rerun)")
    print(f"--- applied={total_applied} skipped={total_skipped} fail={'YES' if any_fail else 'NO'}")
    sys.exit(1 if any_fail else 0)

if __name__ == "__main__":
    main()
