From Stdlib.Logic Require Import FunctionalExtensionality.
Theorem lp_mirror_funext : forall (A B : Type) (f g : A -> B), (forall x, f x = g x) -> f = g.
Proof. intros. apply functional_extensionality_dep. intros. apply H. Qed.
