(* scan_v4_shadow_fixture.v — scanner-fixture: the historic mixed-line masking
   pattern, reproduced for regression coverage of scan_v4_token.py.

   Incident shape this file encodes (three stations, exactly):
   a record field named S coexists with successor references.  Three source
   lines carry BOTH the qualified form (Datatypes.S n) AND a bare S token on
   the same line.  Any line-level filter that drops lines containing
   "Datatypes.S" loses those three stations at once — the blindness this
   fixture pins.  The two binder-local references at the bottom are legal and
   must NOT be reported (binder tracking).

   This file is scanner input only; it is not expected to compile. *)

Record StateSpace := MkSpace {
  S : Set;                          (* shadow source: field named S *)
  size : nat
}.

Definition bump (sp : StateSpace) (n : nat) : nat :=
  size sp + Datatypes.S n + S n.
Definition bump2 (sp : StateSpace) (n : nat) : nat :=
  Datatypes.S (Datatypes.S n) + S (Datatypes.S n).
Definition bump3 (sp : StateSpace) (n : nat) : nat :=
  S (size sp) + Datatypes.S (size sp).

(* binder-local uses: legal — S is re-bound as a local parameter here. *)
Definition local_sum (S : Set) (f : S -> nat) (x : S) : nat := f x + 0.
Lemma local_use : forall (S : Set) (x : S), nat.
Proof. intros S x. exact (0%nat). Qed.
