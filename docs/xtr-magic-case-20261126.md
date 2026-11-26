# xtr-magic-case (ticket X6b, xtr-line)

Purpose.  Record a real Obj.magic judgment case from this line's
domain, per the seed queue's capacity ticket: what the extraction
products of an actual certified library look like under the X2 audit
battery.

Interface.  Data source: the X2 magic audit over the 232 real
extraction products (.ml/.mli pairs) deposited at the ComplexAnalysis
workspace root by prior extraction runs of the Set library; machine
document preserved in the line ledger gates directory
(real_products_audit.json).  The audit ran without a census (all
verdicts NO_CLAIM by construction); this volume reads the battery
counts, not claims.

Exit-codes.  Not applicable (documentation volume).

Evidence.  232 products scanned: total_magic = 0, total_dummy = 549,
mismatch = 0.  Deterministic double-run discipline applies to the
audit tool; the counts are machine output, not prose claims.

Dependencies.  The X2 audit tool only; no compiler toolchain; no
network.

## The case: erasure shows up as dummies, not magic

Across all 232 real extraction products the magic battery is ZERO:
no `Obj.magic`, no `unsafeCoerce`, no `assert false`, no `failwith`.
The erasure burden of the library instead appears entirely as
`__`-prefixed dummy identifiers - 549 of them, concentrated in one
module family:

- DTPT.ml: 223 dummies; DTPT.mli: 221
- S02_CauchyComplete.mli: 14
- S07_RealSetoidExpLog.ml: 7
- Lw4cPiLicGate.ml: 6

The shape judgment this case supports: for extraction products of
proof-heavy constructive libraries, a ZERO magic count is achievable
and was achieved, and the honest audit signal for erasure pressure is
the dummy-identifier density, not magic.  A gate that only counted
`Obj.magic` would pass this library silently while 549 erasure points
accumulate; the X2 battery therefore reports dummies as a first-class
counter (per-file counts and line lists) instead of a footnote.

## Reading guard

The absence of magic in these products is evidence about THIS
extraction run of THIS library, not a property of extraction in
general; products from a development with Prop-leaking definitions or
`Extract Constant ... => "Obj.magic ..."` payload declarations would
flag, and the X2 claim model (census cross-check) is the instrument
for exactly that comparison inside a repository that carries a census.
