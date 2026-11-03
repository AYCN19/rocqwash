(* 旧头注样例
   超长过程性头注（gate4 审校黄面形：头注超行＋语境双义词）
   载体一词在此出现，头注换代靶区。 *)

Require Import List.
Import ListNotations.

(* 注释域靶一：载体词换形；嵌套 (* 载体 深处 *) 为靶二。 *)
Definition sample_len (l : natlist) := length l.

Definition flag_in_string := "载体 在字符串内（禁换形）".

Theorem sample_len_ge_zero : forall l, 0 <= sample_len l.
Proof. intros. apply Nat.le_0_l. Qed.
