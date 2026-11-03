(* cure31 negative fixture — same bare statement shape as
   cure31_shadow_fixture.v but WITHOUT the shadowing Import line: the
   file_include precondition must keep every shadow variant at zero matches. *)

Require Import S02_CauchyComplete.
Require Import S07_RealSetoidExpLog.

Theorem logd_log_exp_neg_plain : forall u : Real,
  req (log (exp_neg u) (exp_neg_pos u)) (opp u).
Proof.
  intros u. apply logd_root.
Qed.
