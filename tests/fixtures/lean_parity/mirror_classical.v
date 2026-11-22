From Stdlib.Logic Require Import Classical_Prop.
Theorem lp_mirror_classical : forall P : Prop, P \/ ~ P.
Proof. intros. apply classic. Qed.
