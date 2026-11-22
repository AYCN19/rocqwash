From Stdlib.Logic Require Import PropExtensionality.
From Stdlib.Logic Require Import IndefiniteDescription.
From Stdlib.Logic Require Import ProofIrrelevance.
Theorem t_axaudit_pi : forall (P : Prop) (p1 p2 : P), p1 = p2.
Proof. intros. apply proof_irrelevance. Qed.
Theorem t_axaudit_pe : forall P Q : Prop, P <-> Q -> P = Q.
Proof. intros. apply propositional_extensionality. assumption. Qed.
Theorem t_axaudit_cid : forall (A : Type) (P : A -> Prop), (exists x, P x) -> {x : A | P x}.
Proof. intros. apply constructive_indefinite_description. assumption. Qed.
