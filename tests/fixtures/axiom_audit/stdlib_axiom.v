From Stdlib.Logic Require Import Classical_Prop.
From Stdlib.Logic Require Import FunctionalExtensionality.
From Stdlib.Logic Require Import Eqdep.
Theorem t_axaudit_classic : forall P : Prop, P \/ ~ P.
Proof. apply classic. Qed.
Theorem t_axaudit_funext : forall (A B : Type) (f g : A -> B), (forall x, f x = g x) -> f = g.
Proof. intros. apply functional_extensionality_dep. intros. apply H. Qed.
Theorem t_axaudit_k : forall (U : Type) (p : U) (Q : U -> Type) (x : Q p) (h : p = p), x = eq_rect p Q x p h.
Proof. intros. apply eq_rect_eq. Qed.
