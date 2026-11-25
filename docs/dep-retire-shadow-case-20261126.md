# dep-line shadow case: statement-head `Real` duplicated across providers

Date: 2026-11-26. Source: statement rosters collected by
`names/mac_stmt_names.py` (read-only use) over every fixture consumer in
the dep-map scan set.

## The case

Two fixture world files both define a top-level statement named `Real`:

- `tests/fixtures/cure32_s07_world.v` - `Real` (plus `RealEnhancedReal`,
  `real_eq`, `real_lt`, `zero`)
- `tests/fixtures/cure34_e23_world.v` - `Real` (plus `natIF`, `gstep`,
  `theW`)

A consumer that requires both modules in one file resolves the
statement head `Real` against the LAST Require that exports it; the
other provider's `Real` becomes shadowed. Concretely:

```rocq
Require Import Cure32S07World.
Require Import Cure34E23World.
(* every bare use of Real below resolves against Cure34E23World *)
```

This is exactly the provider-shadowing ambiguity the dep-map's flat
consumer-to-provider projection cannot see (the census records that a
consumer requires both modules, but not which export wins). The honest
consequences for the dep tools:

- `dep_plan` re-pointing either world module can silently flip which
  provider a downstream `Real` resolves to, without any line-level
  anchor changing; the N=N statement-name assertion in `dep_apply` does
  NOT catch this (the name sequence is unchanged - only resolution
  order moved).
- The safe workflow for retiring a provider that exports a duplicated
  head is therefore: retire one require at a time, and after each leg
  run `dep_retire_verify` probe C (Print Assumptions roster) on the
  consumer - resolution changes surface there as changed assumption
  lines, not as name-table drift.

## Machine-checkable residue

`Real` x2 across the scan set is the only exact duplicate statement
head today (all other names are unique). If a future rotation adds a
duplicate head, this document's detection one-liner is: extract
statement rosters over the scan set and group by name; any group with
more than one distinct provider file is a shadow candidate.

No repository file was modified to produce this document.
