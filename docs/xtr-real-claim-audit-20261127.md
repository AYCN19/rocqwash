# xtr-real-claim-audit (ticket XD2, xtr-line)

Purpose.  Arm the X2 claim model with a real census for the first time
and audit the real extraction products against it.  The X6b judgment
case audited the same 232 products without a census, so every verdict
was NO_CLAIM by construction; this ticket closes that gap and
decomposes what the remaining NO_CLAIM bucket actually contains.

Interface.  Data sources: the X1 census tool (v2, quoted-output forms)
swept over the two live libraries read-only; the X2 magic audit run
with `--census` over the 232 staged products (ledger staging directory
`gates/x2real`, read-only copies of the workspace-root deposits).
Machine documents preserved in the line ledger gates directory
(`set_repo_census_v2.json`, `main_repo_census_v2.json`,
`main_repo_census_v1.json`, `xd2_claim_audit_r1.json`,
`xd2_claim_audit_r2.json`).  This volume quotes counts; no CLI of its
own.

Exit-codes.  Not applicable (documentation volume).

Evidence.  Every count below is quoted from a machine document; the
claim audit is deterministic (double-run byte-identical, r1 vs r2) and
the census sweeps are zero-write with respect to both scanned trees.

Dependencies.  The X1 census v2 and X2 audit tools only; no compiler
toolchain; no network.

## Result one: the claim model resolves real claims

Census-armed audit over the 232 real products:

- 34 files MATCH (a census-declared magic-free source links to the
  product by stem, and the product carries zero magic occurrences).
- 0 files MISMATCH (no census-declared magic-free product carries
  magic; the selftest negative control covers this verdict class).
- 198 files NO_CLAIM, decomposed below.
- Totals consistent with the X6b unarmed run: magic 0, erasure dummies
  549.  The armed run adds claim linkage only; the battery counts do
  not move.

## Result two: the NO_CLAIM bucket decomposes into three faces

Linkage in the current claim model is by source stem only: a product
claims when a census extraction point's owning .v file shares the
product's stem.  Decomposing all 116 product stems:

- 17 stems are census-source-linked (34 files, the MATCH set).
- 61 stems are declared in the census only as output files
  (122 files): Separate Extraction runs whose output path differs from
  the owning .v name.  The current model cannot reach them by source
  stem, so they stay NO_CLAIM even though the census declares them.
- 38 stems (76 files) link to nothing in either audited library.

The third face was probed against a second census: the
ConstructiveWorld-Main tree swept read-only (2663 .v files, 1390
extraction points, unparsed 0 under census v2).  None of the 38 stems
links to a Main source or output either.  The names (Datatypes,
BinNums, BinPos, BinInt, Nat, List, and older product names) are
consistent with stale deposits from superseded extraction runs whose
generating statements no longer exist in the current trees; this audit
does not attribute them further.  Archive trees (151 .v files inside
delivery snapshot packages) were noted and not swept.

## Result three: the linkage gap is machine-evidenced

The 61 output-declared stems are not a scan miss: the census declares
them, the linkage rule cannot express them.  This is the same failure
class the X6a volume recorded for the scan face (the unparsed bucket
making a blind spot visible as data), now on the claim face.
Derived ticket XD3: extend the claim linkage to a second rule, output
stem matching against the census `output_file` field (already emitted
by census v2).  Projection from this decomposition: claimed coverage
34 to 156 of 232 files (67.2 percent), MISMATCH face unchanged at 0
under the same battery counts.  XD3 must re-run this audit and confirm
or correct the projection with machine output.

## Result four: the census v2 fix generalizes across libraries

The Main sweep under census v1 left 636 statements unparsed, every one
of the quoted-output form; under census v2 the bucket drains to 0 and
the point count rises 754 to 1390.  Together with the Set sweep (633
files, 330 points, unparsed 137 to 0), the XD1 quoted-output
refinement holds on a second library with zero silent misses.

## Reading guard

Zero magic in these products is evidence about these 232 deposited
products of these two libraries at this commit state, not a property
of extraction in general.  The 34 MATCH verdicts inherit the census's
own safe-class judgment; a census error would propagate here, which is
why the MISMATCH face and the selftest negative control stay first
class.  The staging copy is a fixed snapshot; products deposited after
the snapshot are out of scope for this volume.
