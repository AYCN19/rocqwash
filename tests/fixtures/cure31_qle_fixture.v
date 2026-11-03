(* cure31 fixture — Qle/Qlt statement-face downshift forms (cure_pack v1.1
   cure6/cure7/cure8/cure9/cure10), mirroring the red-station shapes of the
   20261103 wash-campaign field report.  Statement-face forms only; the
   guarded negatives (binder declarations, Definition bodies, trailing
   comments, unmarked comparisons) must survive every application verbatim. *)

Theorem tbd_wit_bound : forall x : Q, In x [0; 0; 2] -> Qabs x <= 2%Q.
Proof.
  intros x Hx. simpl in Hx.
  destruct Hx as [Hx | [Hx | [Hx | []]]]; subst x.
  - apply xq_Qle_bool_le. vm_compute. reflexivity.
Qed.

Theorem qle_token_face : forall a b : Q, Qle a b -> Qle (f a) (f b).
Proof.
  intros a b H.
  apply Qle_refl.
Qed.

Theorem qlt_token_face : forall a b : Q, Qlt a b -> Qlt (g a) (g b).
Proof.
  intros a b H. apply Qlt_refl.
Qed.

Theorem qlt_marked_face : forall x : Q, P x -> Qabs x < 1%Q.
Proof.
  intros x Hx. apply xq_Qlt_bool_lt. exact Hx.
Qed.

(* guarded negatives: each line below must survive the pack verbatim *)
Definition bnd_holder (Qle : nat) (Qlt : nat) (n : nat) := n + Qle + Qlt.
Definition named_qle := 3.
Theorem unmarked_face : forall a y : Q, In y (P0 [a]) -> Qabs y <= Qabs a.
Proof.
  intros a y Hy. simpl in Hy. destruct Hy as [Hy | []]. subst y.
  apply Qle_refl.
Qed.
