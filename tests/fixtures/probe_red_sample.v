(* probe_red_sample.v — probe engine red-side fixture (missing-library family).
   Dependencies: RocqwashDeliberatelyAbsentLib — deliberately absent, expected
   probe verdict RED-MISSING_LIB (rc != 0). Not compilable by design. *)
Require Import RocqwashDeliberatelyAbsentLib.
Lemma probe_red_unreachable : True.
Proof. exact I. Qed.
