(* cure34_e3_fixture.v — E3 generic-interface-instantiation red-face
   miniature (consumer side).

   BASE state (this file, uncured) compiles green against the miniature
   world (fixture cure34_e23_world.v): the E3 family is an extraction-time
   defect, not a compile-time one — the consumer stations instantiate the
   generic supply lemma through the explicit abstract-carrier application
   form, which rides the polymorphic face at extraction (the CI #178 gate7
   census shape).  The cured canonical form rewrites every station to the
   specialization shim call gstep_spec and inserts the shim Definition
   (Definition gstep_spec (x : Real) : Real := gstep Real natIF x.) right
   after the last import; the cured file compiles green and extracts with
   the monomorphic station face ("let ufx_nat n = gstep_spec n").

   The tests copy this file to Cure34E3Fixture.v and the world to
   Cure34E23World.v so the Require below resolves; dry-run tests never
   compile anything. *)

Require Import Cure34E23World.

(* abstract-carrier instantiation station of the generic supply lemma *)
Definition ufx_nat (n : Real) : Real := gstep Real natIF n.

(* the shim is delta-equal to the original application: the theorem face
   carries the same station shape and reflexivity still closes after the
   rewrite (gstep_spec unfolds to the very application it specializes) *)
Theorem ufx_gstep_mul : forall n : Real,
  gstep Real natIF n = Nat.mul n n.
Proof.
  intro n.
  reflexivity.
Qed.
