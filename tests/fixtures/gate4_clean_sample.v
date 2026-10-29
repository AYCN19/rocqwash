(* gate4_clean_sample.v — 闸④守卫净样例（rocqwash tests/）。
   五字段齐备、规范序、无禁词、无承认式词面、无日期戳、无内部上下文语汇，
   预期 verdict=PASS 且退出码 0。字段用英文标签形（FIELD_SPECS 双语登记）。 *)

(* Mission.  Provide a minimal fixture that passes the gate4 comment guard.
   Dependencies.  Rocq standard library only.
   References.  rocqwash README and docs/architecture.
   Constructivity.  All statements are Set-carried; proofs close with Qed;
      no excluded middle and no classical principle appears in this sample.
   Build.  rocq c -native-compiler no -q -Q . "" gate4_clean_sample.v
*)

Require Import QArith.

Lemma clean_order : forall x y : Q, QltT x y -> QltT (x + y) (y + x).
Proof.
  intros x y H. exact H.
Qed.
