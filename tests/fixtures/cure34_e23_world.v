(* Cure34E23World — miniature generic-interface world for the cure34
   E2/E3 extraction-defect-family fixtures (self-contained: the stdlib
   prelude only).

   E3 surface (generic-interface instantiation): the carrier-parameterized
   interface Class MetaIF supplies the generic one-step lemma gstep whose
   parameters carry the abstract carrier — consumer stations instantiate it
   through the explicit abstract-carrier application form
   "gstep Real natIF x" (compiles green everywhere; the CI #178 gate7
   whole-tree census shape, LW3 four-module family).  The E3 cure
   specializes the generic at the concrete carrier through an intermediate
   Definition shim (cure34_E3_spec_shim) and rewrites the stations
   (cure34_E3_use_station_spec).

   E2 surface (record polymorphic field): the record Wr carries the
   inside-polymorphic field wf; a consumer Definition consuming it without
   an explicit type annotation extracts with the polymorphic face
   ("val unann : 'a1 -> 'a1").  The E2 cure restates the consumption as an
   explicit-type-annotated middleware Definition (cure34_E2_field_annot)
   and adapts the downstream arity stations (cure34_E2_use_arity).

   Honesty boundary (fixture-world generation): this world is written in
   the extraction-clean generation — no Obj.magic appears in any world-side
   extraction unit.  A defect-generation world whose field accessors
   themselves cast ("Obj.magic w.wf __ x") is world-generation debt owned
   by the entity-repair workflow; a consumer-side text cure cannot reach
   it, and the pack's canonical notes document that boundary.

   Exercised by: tests/test_cure_pack.py (compile-gated E2/E3 arc; the
   world is compiled first, the consumer fixtures Require it by the module
   name Cure34E23World).  Dry-run tests never compile anything. *)

Definition Real : Set := nat.

(* E3 surface: generic interface + generic supply lemma *)
Class MetaIF (R : Set) : Type := mkMIF { mhalf : R; mfn : R -> R -> R }.

Global Instance natIF : MetaIF nat := @mkMIF nat 5 Nat.mul.

Definition gstep (R : Set) (i : MetaIF R) (x : R) : R := @mfn R i x x.

(* E2 surface: record with an inside-polymorphic field *)
Record Wr : Type := mkW { wf : forall (A : Set), A -> A; wv : nat }.

Definition theW : Wr := mkW (fun A x => x) 5.
