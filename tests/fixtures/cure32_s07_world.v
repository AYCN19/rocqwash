(* Cure32S07World — miniature argument-less interface world for the
   cure32 S07-lineage adaptation fixtures (self-contained: the stdlib
   prelude only).

   This file stands in for the upstream world of the S07 lineage: the
   interface Class RealInterfaceEnhancedSetoid carries ZERO parameters
   (the carrier is the world's own Real), the class fields resolve bare
   through the global instance, and the direct predicate faces real_lt /
   real_eq live at module level.  A source file written against the older
   parameterized face of the interface raises
   "Illegal application (Non-functional construction)" when compiled
   against this world — the red face the cure32 pack patterns cure.

   Exercised by: tests/test_cure_pack.py (compile-gated section; the
   consumer fixture is cure32_s07_fixture.v).  The world is compiled
   first; the consumer Requires it by the module name Cure32S07World. *)

Definition Real : Set := nat.

Class RealInterfaceEnhancedSetoid : Type :=
  mkRIES { one_pos : Real; mult : Real -> Real -> Real;
           Z_align_req : Real -> Real }.

Global Instance RealEnhancedReal : RealInterfaceEnhancedSetoid :=
  mkRIES 1 Nat.mul (fun x => x).

Definition real_eq (a b : Real) : Prop := Nat.eqb a b = true.
Definition real_lt (a b : Real) : Prop := Nat.ltb a b = true.
Definition zero : Real := 0.

(* Supply lemma of record: the conclusion face carries real_eq — the
   constant name the predicate-face convergence (cure32_C(b)) must target,
   not any delta-equivalent synonym. *)
Lemma supply_refl (x : Real) : real_eq x x.
Proof. induction x; simpl; try reflexivity. apply IHx. Qed.
