(* cure39_plain_fixture.v — negative fixture for
   cure39_ifq_connective_qualify: the same bare-connective statement
   shape but under a DIFFERENTLY-named section context variable
   (RI, not RI0).  The file_include gate (the exact RI0 section-context
   face — note this header deliberately does NOT spell that face out,
   because the gate regex is matched against the whole file and a
   comment mention would open it) must keep the pattern at zero
   matches — the qualified target hardcodes the RI0 context name, and
   a differently-named context is manual-surgery territory (dry-run
   visible, never silently rewritten).  Mirrors the campaign arc: the
   b48-52 re-anchor (commit 9a51c74) names its context variables
   RI0/DO0 explicitly; same-shape files that do not carry that exact
   context face are outside the pattern's scope.

   Red-face miniature input; not expected to compile (lineage anchors,
   not Requires). *)

Require Import S01_BaseRing.

Section Plain.

Context {RI : RealInterfaceEnhanced}.
Context {DO : DecidableOrder RI}.

Theorem plain_compat :
  forall a b c d : @S01_BaseRing.R RI,
    lt a b -> le c d -> lt (plus a c) (plus b d).
Proof.
  intros a b c d Hab Hcd.
  exact (@fa53_lt_plus_compat_lt_le_dec RI DO a b c d Hab Hcd).
Qed.

End Plain.
