(* probe_pass_sample.v — probe engine pass-side fixture.
   Dependencies: none (stdlib-only True).
   Compile status: verified green via `rocq c -Q . ""` on Rocq 9.1 (born-clean). *)
Lemma probe_pass_ok : True.
Proof. exact I. Qed.
