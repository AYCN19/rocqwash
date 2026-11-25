# xtr-unaudited-faces (ticket X6a, xtr-line)

Purpose.  Record the capacity work stream census sweeps that answer "which
extraction faces are still unaudited": the rocqwash repository's own
.v face, and the read-only sweep of the ConstructiveWorld-Set library
where the real extraction points live.

Interface.  Data sources: the X1 census tool over both trees; machine
documents preserved in the line ledger gates directory
(repo_census.json, set_repo_census.json).  This volume quotes counts;
no CLI of its own.

Exit-codes.  Not applicable (documentation volume).

Evidence.  Every count below is quoted from a machine census document;
the sweeps are deterministic (double-run byte-identical discipline of
the census tool) and zero-write with respect to both scanned trees.

Dependencies.  The X1 census tool only; no compiler toolchain; no
network.

## Result one: the rocqwash face is clean

The census over the whole rocqwash repository found 23 .v files and
ZERO extraction statements (all command counts empty, unparsed bucket
empty).  The repository that hosts the audit line carries no
extraction face of its own; nothing inside it needs an extraction
audit.  The audit demand is external - which the next sweep confirms.

## Result two: the Set library carries the real extraction face

Read-only census over the ConstructiveWorld-Set tree (633 .v files):

- 193 parsed extraction points across 148 files:
  50 `Recursive Extraction`, 139 `Separate Extraction`,
  4 `Extraction Inline`.
- zero `unsafe-shape` payload classifications.
- zero `Extraction Language` declarations (the default OCaml target
  applies throughout).
- 137 statements in the `unparsed_extraction_face` bucket.

## Derivation XD1: the quoted-output-path blind spot

Every one of the 137 unparsed statements has the same shape:
`Extraction "file.ml" qualids.` - the quoted-output-path form of the
extraction vernacular, absent from the X1 form set.  The unparsed
bucket worked exactly as designed: zero silent misses, and the miss is
visible as data.  Derived ticket XD1 (queued in the X6 capacity work stream)
refines the census with the quoted-output forms, records an
`output_file` field per point, extends the selftest, and re-sweeps the
Set library to confirm the bucket drains to zero.  Until XD1 lands,
the honest reading of the inventory is: 193 parsed + 137 quoted-form
statements = 330 extraction statements across 148 files, none audited
by a magic gate.

## Consumers

XD1 consumes this volume as its requirement document; the line report
quotes both sweeps as the line's demand signal.
