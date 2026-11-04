(* cure34_e2_fixture.v — E2 record-polymorphic-field red-face miniature
   (consumer side).

   BASE state (this file, uncured) compiles green against the miniature
   world (fixture cure34_e23_world.v): the consumer Definition unann
   consumes the record's inside-polymorphic field wf without an explicit
   type annotation, so the extracted face stays polymorphic
   ("val unann : 'a1 -> 'a1" — the E2 shape of the CI #178 census; the
   UpAblMetaWindow born-clean landing recorded magic=0 while CI counted
   13).  The cured canonical form restates the consumption as the
   explicit-type-annotated middleware Definition
   (Definition unann (n : nat) : nat := wf theW nat n.) and the downstream
   application station follows the one-binder face
   (":= unann n.").  After the cure the extracted signature is
   "val unann : nat -> nat" (asserted in the test arc on the .mli).

   The tests copy this file to Cure34E2Fixture.v and the world to
   Cure34E23World.v so the Require below resolves; dry-run tests never
   compile anything. *)

Require Import Cure34E23World.

(* un-annotated consumption of the polymorphic record field *)
Definition unann := wf theW.

Definition use_unann (n : nat) : nat := unann nat n.
