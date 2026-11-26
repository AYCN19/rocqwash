(* xtr e2e fixture: risky face, declared unsafe and degrading. *)
Extract Constant unsafe_gate => "Obj.magic 0".
Program Definition risky := 0.
Inductive box : Type :=
| mk_box : sigT (fun a : Type => a) -> box.
