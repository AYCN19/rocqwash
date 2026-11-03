(* cure32_s07_fixture.v — S07-lineage adaptation red-face miniature
   (consumer side).

   BASE state (this file, uncured) raises
   "Illegal application (Non-functional construction)" against the
   argument-less interface world (fixture cure32_s07_world.v): the source
   face applies the interface Class to a carrier, binds the parameterized
   binder pair, applies the law fields with the explicit carrier/instance
   prefix, and carries the projection-face predicates lt/req.

   One full pack run (cure32_A shell drop + cure32_B notation rebind +
   cure32_C bridge bare + predicate-face convergence) turns the file into
   the cured canonical form, which compiles against the world and
   extracts with zero Obj.magic.  The tests copy this file to
   Cure32S07Fixture.v and the world to Cure32S07World.v so the Require
   below resolves; dry-run tests never compile anything. *)

Require Import Cure32S07World.

(* alien parameterized face of record: shell + binder pair + bridges *)
Definition ufx_ren : RealInterfaceEnhancedSetoid Real :=
  mkRIES 1 Nat.mul (fun x => x).

Theorem ufx_pos : forall (R : Set) {RIS : RealInterfaceEnhancedSetoid R}
                         (beta : R),
  lt zero (@Z_align_req Real ufx_ren beta) ->
  req (@Z_align_req Real ufx_ren beta) (@Z_align_req Real ufx_ren beta).
Proof.
  intros R RIS beta Hz.
  apply supply_refl.
Qed.

(* Set-valued sample so the extraction gate carries real code, not only
   an erased proposition. *)
Definition ufx_sample (beta : Real) : Real :=
  mult (@one_pos Real ufx_ren) (@Z_align_req Real ufx_ren beta).
