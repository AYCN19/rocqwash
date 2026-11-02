(* cure_examples.v — minimal compilable examples for the five canonical
   consumer-cure patterns of wash/cure_pack.json.
   Self-contained: dependencies are the standard library only, so external
   users can replay every pattern without any private-world dependencies.

   Patterns exercised (see wash/cure_pack.json for triggers and templates):
     cure1  rewrite (qeqT_imp_qeq _ _ (lemma args))  — bridge-wrapped rewrite
     cure2  apply qeq_imp_qeqT                       — goal-opening downshift
     cure3  apply Qeq_refl                           — opaque-reflexivity cure
     cure4  Datatypes.S                              — qualified successor form
     cure5  exact (NatLe_drop _ _ H)                 — NatLe supply bridge

   Build: rocq c -native-compiler no -q -Q . "" cure_examples.v
   (wrap the compiler invocation in your platform thermal guard for long runs) *)

From Stdlib Require Import QArith.QArith Arith.Arith Lia.

(* ---- Set-layer Q equality carrier and the two direction bridges ---- *)

Definition QeqT (a b : Q) : Set :=
  (match (Qnum a * QDen b ?= Qnum b * QDen a)%Z with
   | Eq => true
   | _ => false
   end) = true.

Lemma qeq_imp_qeqT : forall a b : Q, a == b -> QeqT a b.
Proof.
  intros a b Hab. unfold Qeq in Hab. unfold QeqT.
  destruct (Qnum a * QDen b ?= Qnum b * QDen a)%Z eqn:E; cbn.
  - reflexivity.
  - exfalso.
    assert (Hc : (Qnum b * QDen a ?= Qnum b * QDen a)%Z = Eq)
      by (apply Z.compare_refl).
    rewrite Hab in E. rewrite E in Hc. discriminate Hc.
  - exfalso.
    assert (Hc : (Qnum a * QDen b ?= Qnum a * QDen b)%Z = Eq)
      by (apply Z.compare_refl).
    rewrite <- Hab in E. rewrite E in Hc. discriminate Hc.
Qed.

Lemma qeqT_imp_qeq : forall a b : Q, QeqT a b -> a == b.
Proof.
  intros a b H. unfold QeqT in H.
  destruct (Qnum a * QDen b ?= Qnum b * QDen a)%Z eqn:E.
  - unfold Qeq. apply Z.compare_eq in E. exact E.
  - discriminate H.
  - discriminate H.
Qed.

(* ---- cure2 + cure1: a step lemma and its bridge-wrapped consumer ---- *)

Fixpoint g (n : nat) : Q :=
  match n with
  | O => 1%Q
  | Datatypes.S j => (2 * g j)%Q
  end.

(* cure2 canonical: QeqT goal opened with the downshift bridge, then the
   ==-face proof (here definitional, so reflexivity closes it). *)
Lemma g_step : forall k : nat, QeqT (g (Datatypes.S k)) (2 * g k)%Q.
Proof.
  intro k. apply qeq_imp_qeqT. reflexivity.
Qed.

(* cure1 canonical: rewriting through a QeqT-face step lemma requires the
   qeqT_imp_qeq wrap with two explicit _ arguments. *)
Lemma g_dbl : forall k : nat,
  QeqT (g (Datatypes.S (Datatypes.S k))) (2 * (2 * g k))%Q.
Proof.
  intro k. apply qeq_imp_qeqT.
  rewrite (qeqT_imp_qeq _ _ (g_step (Datatypes.S k))).
  rewrite (qeqT_imp_qeq _ _ (g_step k)).
  reflexivity.
Qed.

(* ---- cure3: opaque reflexivity on the carrier face, canonical cure ---- *)

Lemma qeqT_refl : forall a : Q, QeqT a a.
Proof.
  intro a. apply qeq_imp_qeqT. apply Qeq_refl.
Qed.

(* ---- cure4: qualified successor form in a field-shadowing context ---- *)

Record Space := MkSpace { S : Set; sz : nat }.

Definition bump (p : Space) (n : nat) : nat := sz p + Datatypes.S n.

(* ---- cure5: NatLe carrier, its drop bridge, and a bridge-consuming proof ---- *)

Definition NatLe (n m : nat) : Set := (Nat.leb n m) = true.

Lemma NatLe_drop : forall n m : nat, NatLe n m -> (n <= m)%nat.
Proof.
  intros n m H. unfold NatLe in H. destruct (Nat.leb n m) eqn:E.
  - apply (proj1 (Nat.leb_le n m)). exact E.
  - discriminate H.
Qed.

Lemma drop_consumer : forall n m : nat, NatLe n m -> (n <= Datatypes.S m)%nat.
Proof.
  intros n m H. apply Nat.le_le_succ_r. exact (NatLe_drop _ _ H).
Qed.
