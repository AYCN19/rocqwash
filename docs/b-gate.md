# b-gate - the B-level generalization threshold as a computable audit.

Ticket: recursive three-gap closing batch (November 19, 2026), b-gate lane.
Statement faces: tools/b_gate_audit.py; docs/b-gate-audit.json (schema
  rocqwash.b-gate-audit/1); tools/taxonomy.json (read-only class vocabulary);
  docs/round-ledger.jsonl and docs/round-state.json (read-only inputs)
Source route: repo docs/ (this file; the threshold definition is the batch
  contract face carried by the CAPABILITY-INDEX b_gate_audit entry)
Command: python -I tools/b_gate_audit.py --selftest
Registry: CAPABILITY-INDEX entry added same round

> Purpose.  Turn the B-level generalization threshold (3 instances, each
>   grounded in at least 1 executed round) into a per-class audit over
>   the round records: instance and round counts, a per-class readiness
>   verdict, and an explicit gap list, written to docs/b-gate-audit.json.
> Interface.  `python -I tools/b_gate_audit.py [--selftest]`; the default
>   run reads docs/round-ledger.jsonl and docs/round-state.json
>   read-only and writes docs/b-gate-audit.json plus a stdout summary.
> Dependencies.  Python 3 standard library only (argparse, JSON and JSONL
>   reading, tempfile fixtures); tools/taxonomy.json as the read-only
>   class vocabulary.
> Evidence.  --selftest runs four vectors on tempfile fixtures (a
>   threshold-meeting class, a single-instance class, an empty ledger,
>   malformed-line tolerance); zero network; the default run writes only
>   docs/b-gate-audit.json and never its read-only inputs.
> Exit-codes.  0 = readings are data: a not-ready verdict on empty or
>   below-threshold classes is a data state, never padded; a bad ledger
>   row lands in an error field and the stdout summary fails loud.

## Problem

The B-level generalization threshold was applied by judgment. A class was
treated as ready for B-construction when reviewers agreed it had enough
grounding, and no artifact recorded instances or rounds per class, so the
threshold was unmeasurable. A class grounded in a single instance could pass
as general with nothing to point at. This tool turns the threshold into an
audit: per-class instance and round counts, a per-class readiness verdict,
and an explicit gap list.

## Threshold

A class is B-gate ready when it has at least 3 instances, each grounded in at
least 1 executed round. One instance is one admission of the class in
`docs/round-ledger.jsonl` (per round and class, deduplicated within a round);
the round count is the number of rounds in which the class was admitted.
A single-instance induction is fake generality; two more grounded instances
are the minimum additional evidence the gate accepts. An empty ledger audits
honestly as `not-ready` with `remaining_to_b` of 3; the tool does not inflate
counts it did not measure.

## Output

`docs/b-gate-audit.json`, schema `rocqwash.b-gate-audit/1`:

```json
{"schema": "rocqwash.b-gate-audit/1",
 "threshold": {"instances": 3, "rounds_per_instance": 1},
 "classes": [{"class": "jargon", "instances": 1, "rounds": 1,
              "ready": false,
              "gap": "needs 2 more instances with a round each"}],
 "ready_classes": [],
 "verdict": "not-ready",
 "remaining_to_b": 3}
```

The class entry above matches the current records: `jargon` was admitted in
one round with one admission, one short of the instance threshold, so the
first entry is illustrative of the shape and the honest verdict for today's
records is `not-ready` with no ready classes.

## Relation

`ready_classes` feeds the B-construction gate: a class enters construction
eligibility only by appearing in that list, and the list is computed from the
round records rather than asserted. The audit is recomputable at any time;
when a claimed readiness and a fresh audit run disagree, the audit wins.

## Selftest

`python -I tools/b_gate_audit.py --selftest` runs four vectors on temporary
fixtures: a class that meets the threshold; a single-instance class; an empty
ledger; malformed-line tolerance. No network; fixture writes stay inside the
temporary tree. The default run writes only `docs/b-gate-audit.json` (this
repository's own audit face) and never its read-only inputs.
