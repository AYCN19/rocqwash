(* cure31 fixture — Import-shadow direct-face forms (cure_pack v1.1
   cure11/cure12), mirroring the red-station shape of the 20261103 wash
   campaign: bare req/log/exp_neg/exp_neg_pos/opp resolve to module-field
   projections under the shadowing Import and leak extraction casts. *)

Require Import S02_CauchyComplete.
Require Import S07_RealSetoidExpLog.
Import RealInterfaceEnhancedMod.

Theorem logd_log_exp_neg_real : forall u : Real,
  req (log (exp_neg u) (exp_neg_pos u)) (opp u).
Proof.
  intros u. apply logd_root.
Qed.

Definition shadow_binder (log : nat) (n : nat) := n + log.
