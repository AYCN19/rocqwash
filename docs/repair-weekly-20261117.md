# repair-weekly-20261117.md — repair-outcome ledger weekly distribution face.

> **RepairWeeklyFace**: the weekly distribution of the
> repair-outcome ledger under the E6 vocabulary, generated
> by `tools/repair_weekly.py` from the ledger content only.
>
> Purpose.  Account every red case recorded in
> `docs/repair-ledger.jsonl` for the ISO week of the report
> date: the outcome census (repaired,
> escalated(evidence-package), watch-only), the
> guard-correct reason breakdown, the class and ticket
> distributions, and a digest of every row with its window
> state.
>
> Interface.  `cw.sh repair-weekly --date YYYY-MM-DD --out
> FILE [--ledger P] [--json P]`; regenerating this face
> reruns the aggregation from the same ledger content, and
> identical inputs give byte-identical reruns.
>
> Dependencies.  Generated from the ledger rows only; no
> wall clock and no absolute path enters the face.
>
> Evidence.  Row counts here are reproducible with
> `--json`; the generator selftest and the destructive
> matrix K rows pin the aggregation and write faces.
>
> Exit-codes.  The face is a report; findings are data and
> the generator exit code never escalates on them.

## 1. Window and input

| field | value |
|---|---|
| report date basis | 2026-W47 |
| window | 2026-11-16 .. 2026-11-22 (2026-W47) |
| ledger rows total | 3 |
| rows in window | 3 |
| rows out of window | 0 |
| rows without a parseable timestamp | 0 |
| schemas seen | rocqwash-repair-ledger/1 x3 |

## 2. Outcome distribution (E6 vocabulary, in-window rows)

| repair-outcome | rows | share |
|---|---|---|
| repaired | 2 | 66.7% |
| escalated(evidence-package) | 1 | 33.3% |
| watch-only | 0 | 0.0% |

No side-state to declare: every in-window row normalized into the vocabulary, no escalated row lacks an evidence package.

## 3. Guard-correct reasons (watch-only)

none recorded.

## 4. Class distribution (in-window rows)

| class | rows |
|---|---|
| doc-count | 1 |
| flaky-quarantine | 2 |

## 5. Ticket distribution (in-window rows)

| ticket | rows |
|---|---|
| (no ticket field) | 1 |
| E2-3 | 2 |

## 6. Row digest (all rows)

| # | timestamp | window | class | target | ticket | outcome as recorded | E6 outcome |
|---|---|---|---|---|---|---|---|
| 1 | 2026-11-16T13:30:43Z | in | doc-count | README-cw.md | (none) | repaired(doc-count-sync) | repaired |
| 2 | 2026-11-16T14:31:34Z | in | flaky-quarantine | t_verify_fresh | E2-3 | escalated | escalated |
| 3 | 2026-11-16T14:32:08Z | in | flaky-quarantine | tests/test_verify_fresh.py | E2-3 | repaired | repaired |

## 7. Schema extension register (rocqwash-repair-ledger/2)

The E6 extension adds the `repair-outcome` field with the
values `repaired`, `escalated(evidence-package)` (the row
carries a non-empty `evidence` package), and
`watch-only(guard-correct: cancel-intent | superseded |
budget | out-of-scope)`.  `/1` rows stay valid and are
normalized by the token before the first parenthesis; new
per-red rows are appended by `cw.sh repair-weekly --record`.
