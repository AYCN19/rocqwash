(* xtr_census fixture: extraction-face sample for the xtr line.
   Text-only fixture, not compiled.  Consumed by tests/t_xtr_meta.py
   and the xtr_crosscheck chain.  Covers: safe payload classification,
   target lists, comment masking (negative control), language state,
   unsafe payload flagging, multi-line Extract Inductive, unparsed
   extraction-face bucket. *)

Extract Constant Z.add => "(+)".
Recursive Extraction add mul.
(* Extraction fake.  Masked by the comment scanner, never counted. *)
Extraction Language Haskell.
Extract Constant unsafe_gate => "unsafeCoerce".
Extract Inductive sumbool => "bool"
  [ left -> "True" | right -> "False" ].
Extract Foo bad => "x".
