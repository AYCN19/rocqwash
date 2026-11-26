(* xtr e2e fixture: declaration face claiming magic-free extraction. *)
Extract Constant Z.add => "(+)".
Theorem clean_proof : 1 = 1.
Proof. reflexivity. Qed.
