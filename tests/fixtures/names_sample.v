(* names_sample.v — mac_stmt_names.py --expect 自测最小样例（rocqwash tests/）。
   构形账本（census 口径·不含 Let）：7 条顶层语句；
   --include-let 口径：8 条。注释内诱饵名不得计入（注释被状态机掩蔽）。 *)

(* 注释诱饵：Lemma fake_in_comment 与 Proof. 均在注释内，不应计入。 *)
Require Import QArith.

Section ns_sec.

Definition ns_succ (x : nat) : nat := S x.

Lemma ns_succ_ge : forall x : nat, ns_succ x >= x.
Proof.
  intros x. apply Nat.le_succ_diag_r.
Qed.

Theorem ns_compose : forall x : nat, ns_succ (ns_succ x) >= x.
Proof.
  intros x. apply ns_succ_ge.
Qed.

Fixpoint ns_add (a b : nat) : nat :=
  match a with
  | O => b
  | S a' => S (ns_add a' b)
  end.

Instance ns_natle_proper : Proper (eq ==> eq) ns_succ.

Let ns_helper (x : nat) : nat := x.

(* Unicode 名道判例形（CONTRIBUTING §2：Unicode 仅允许在名道内）。 *)
Lemma ns_δ运输 : forall x : nat, x = x.
Proof.
  intros x. reflexivity.
Qed.

Example ns_ex : ns_succ 0 = 1.
Proof.
  reflexivity.
Qed.

End ns_sec.
