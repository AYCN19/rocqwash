# dep-line unregistered dependency edges (capacity ticket D6-a)

Date: 2026-11-26. Source: full-repo run of `tools/dep_census.py`
(rocqwash.dep-map/1) over the origin/main tree (893fc9b lineage), then
classification of every Require edge against the scanned consumer stems.

## Edge table

| module | refs | classification |
| --- | --- | --- |
| S01_BaseRing | 3 | MISSING-provider (no in-tree stem match) |
| S02_CauchyComplete | 2 | MISSING-provider |
| S07_RealSetoidExpLog | 2 | MISSING-provider |
| Cure34E23World | 2 | MISSING-provider |
| Cure32S07World | 1 | MISSING-provider |
| RocqwashDeliberatelyAbsentLib | 1 | MISSING-provider (deliberate negative fixture, probe_red_sample.v) |
| QArith | 2 | stdlib |
| List | 1 | stdlib |

Reading: 8 distinct edges over 23 consumers. Six edges name modules that
do not exist anywhere in this tree; five of them are fixture references
into the wider Set-repo context (they resolve only when the fixtures are
compiled inside that context), and one is an intentional
missing-library probe fixture. None of these edges is removable from
this repository alone - retiring them is out of dep-line scope; the
registered debt is that dep_retire_verify will honestly report UNSAFE /
INCONCLUSIVE for every consumer of a MISSING-provider module compiled
out of context, which the cross-check report already documents as the
expected out-of-context reading.

## Derived tickets (queue)

- DQ-1: extend `dep_census` with an optional `--classify` leg that emits
  this edge table (in-repo / stdlib / missing) alongside the dep-map, so
  the classification is machine-generated per rotation instead of
  hand-written. Owner: dep-line, next rotation.
- DQ-2: `probe_red_sample.v` and `gate4_clean_sample.v` fail probe B
  (compile) under Rocq 9.3 out of context; if the main-line wants
  per-fixture SAFE baselines, a fixtures-with-providers compile context
  (a -Q mapping over the Set-repo build products) is the prerequisite.
  Owner: main-line decision, not dep-line.

No repository file was modified to produce this document; the census ran
read-only and the artifacts live outside the tree.
