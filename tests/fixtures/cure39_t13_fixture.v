(* cure39_t13_fixture.v — interface-quantified connective qualification
   red-face miniature (cure_pack v1.4 cure39_ifq_connective_qualify).

   Lineage (gold-standard citation, b48-52 wash wave, ConstructiveWorld-Set
   commit 9a51c74 20261110): UpAblT13_UpEntropyGainReq.v was re-anchored
   from bare order connectives to the interface-quantified Set-carried
   form — before: "lt a b -> le c d -> lt (plus a c) (plus b d)."
   after (landed :55-58/:96-99/:137-140/:188-191/:207-210):
   "@S01_BaseRing.lt RI0 a b -> @S01_BaseRing.le RI0 c d ->
   @S01_BaseRing.lt RI0 (@S01_BaseRing.plus RI0 a c)
   (@S01_BaseRing.plus RI0 b d)." — five compat-slot statements, five
   connective stations each (25 stations).  The same file's
   absolute-value slots (:178-186/:198-204) additionally re-cast
   real_eq -> Id setoid equality and re-point the supply witness
   (@ali_abs_ge_zero_id RI0 DO0) — semantic re-casts outside this
   pattern's mechanical scope (recorded in the survey's pending list).
   Canonical anchors already in the qualified form on the same Context
   face: Arch_PA_01.v (5 qualified stations), UpAblD2_AbsLeId_RI_DO.v
   and twin PA_UpAblD2_AbsLeId_RI_DO.v (1 each).

   Honesty note: this is the statement-face conservation family (the
   batch declaration "no bare connectives on any statement face"), not
   an extraction-defect cure — the batch landed gate7 13/13 magic 0/0 in
   both states.  Interplay note: the campaign file also carries
   "Import RealInterfaceEnhancedMod." (added in the same commit); a FULL
   pack run would let cure11 delete that Import line (its documented
   shadow-cure) — run this fixture's cure with --only, as the tests do.
   This fixture is red-face miniature input; it is not expected to
   compile (the mirrored world names are lineage anchors, not Requires;
   the guarded negatives must survive every application verbatim).

   Exercised by: tests/test_cure_pack.py (mechanical dry-run / apply /
   idempotence flow; dry-run tests never compile anything). *)

Require Import S01_BaseRing.
Import RealInterfaceEnhancedMod.

Section UabT13FwLpc.

Context {RI0 : RealInterfaceEnhanced}.
Context {DO0 : DecidableOrder RI0}.

(* compat slot: bare order connectives — the re-anchor source face *)
Theorem uabT13_egreq_lpc :
  forall a b c d : @S01_BaseRing.R RI0,
    lt a b -> le c d -> lt (plus a c) (plus b d).
Proof.
  intros a b c d Hab Hcd.
  exact (@fa53_lt_plus_compat_lt_le_dec RI0 DO0 a b c d Hab Hcd).
Qed.

(* corollary twin slot: same bare shape, second station family *)
Corollary uabT13_usamp_bs_lpc :
  forall a b c d : @S01_BaseRing.R RI0,
    lt a b -> le c d -> lt (plus a c) (plus b d).
Proof.
  exact uabT13_usamp_lpc_h.
Qed.

(* guarded negatives: each line below must survive the pattern verbatim *)
Definition keeper (le : nat) (n : nat) := n + le.
Lemma bnd_guard (lt : nat) : True.
Proof. exact I. Qed.
Theorem already_qualified :
  @S01_BaseRing.lt RI0 1 2 -> @S01_BaseRing.le RI0 2 3.
Proof. intros. apply r. Qed.

End UabT13FwLpc.
