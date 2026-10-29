(* gate4_dirty_sample.v — 闸④守卫脏样例（rocqwash tests/）。
   反判专用：五字段缺失＋基座禁词＋扩展族词面＋席次/战役叙述＋日期戳
   ＋承认式英文词面全命中，预期 verdict=FAIL 且退出码 1。本件永不编译。 *)

(* 脏样例：五字段缺失，禁词探针、拍平、缝合、挂账、收口齐发。
   更新日志：2026-10-30 本席收口记录，批次改写完毕。
   承认面：正文含 admit 字面与 FIXME 与 workaround。
*)

Lemma dirty_sample : forall x : Q, Qlt x x.
Proof.
  (* 战役叙述：挂账清算，拍平收口，本席完工。 *)
  Admitted.
