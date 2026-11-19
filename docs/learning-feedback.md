# learning-feedback - the scheduling feedback edge over the round accounts.

Ticket: recursive three-gap closing batch (November 19, 2026), learning-feedback lane.
Statement faces: tools/learning_feedback.py; docs/scheduling-feedback.json
  (schema rocqwash.scheduling-feedback/1); tools/evolution_dashboard.py
  (feedback section)
Source route: repo docs/ (this file; the schema is defined by the tool and
  summarized here)
Command: python -I tools/learning_feedback.py --selftest
Registry: CAPABILITY-INDEX entry added same round

> Purpose.  Compute the unread approval signal in the round records: the
>   auto versus human-approved round split and approval rate, the
>   per-class gear and confidence readings, the four-state repair outcome
>   tally, and the optional calibration reading (docs/scheduling-feedback.json).
> Interface.  `python -I tools/learning_feedback.py [--selftest]`; the
>   default run reads the three standing accounts read-only
>   (docs/round-ledger.jsonl, docs/round-state.json,
>   docs/exp-ledger.jsonl) and writes docs/scheduling-feedback.json plus
>   a stdout summary.
> Dependencies.  Python 3 standard library only (argparse, JSON and JSONL
>   reading, tempfile fixtures); the three account files as read-only
>   inputs.
> Evidence.  --selftest runs seven vectors on tempfile fixtures (round,
>   tolerance, empty-ledger and outcome-state faces plus the three
>   calibration forms: populated account, empty or absent ledger,
>   unreadable row); zero network; fixture-tree writes; import-safe.
> Exit-codes.  0 = readings are data: a missing account or damaged row
>   lands in an errors field and the stdout summary fails loud; a null
>   repair_action_rate on a zero denominator is reported, never padded.

## Problem

Round records carry an approval signal that nothing reads. Each round entry
states whether a class entered by the auto gear or by a human approval, and
the repair records carry outcome information, but neither number was computed
anywhere: the approval rate was unaccounted and the repair outcome mix had no
readable face. This tool computes that signal; the honest boundary is stated
in its own section below.

## Inputs

All three inputs are read-only; the tool never writes them.

| Face | Role |
|---|---|
| `docs/round-ledger.jsonl` | one row per round: `round_id`, mode, `verify_rc`, `admissions[]` with `class`, gear, `confidence` |
| `docs/round-state.json` | `admitted_classes`, the admitted-class roster |
| `docs/exp-ledger.jsonl` | repair records; the outcome is not a stored column, so each row is classified from its `action` and `points` wording into `repaired`, `escalated`, or `watch_only_guard_correct`, and a row that fits none stays `unrecorded`; its `calibration_ledger` rows also feed the optional `calibration` section |

A missing or unparseable ledger is recorded in the `errors` field of the
affected section and the run continues; it is also printed in the stdout
summary (fail-loud, never silent).

## Output

`docs/scheduling-feedback.json`, schema `rocqwash.scheduling-feedback/1`:

```json
{"schema": "rocqwash.scheduling-feedback/1",
 "rounds": {"total": 2, "auto": 1, "human_approved": 1,
            "approval_rate_auto": 0.5,
            "by_class": [{"class": "jargon", "rounds": 1,
                          "gear": "auto", "confidence": 1.0}]},
 "repair_outcomes": {"repaired": 0, "escalated": 0,
                     "watch_only_guard_correct": 0, "unrecorded": 0,
                     "repair_action_rate": null},
 "calibration": {"section": "calibration", "ledger_present": true,
                 "entries": 2, "agreement_rate": 0.5,
                 "by_class": [{"class": "HIGH", "entries": 2,
                               "agreeing": 1, "agreement_rate": 0.5}],
                 "errors": []},
 "feedback_edge": {"status": "open",
                   "note": "approval-rate now readable; scheduling does not yet consume it (declared blank)"}}
```

`approval_rate_auto` divides the auto-admitted round count by the total round
count, with human-approved rounds inside the denominator.
`repair_action_rate` is `repaired` over the four-state total and is `null`
when that total is zero.

Section presence: every section shown above is present on every run, and
each carries its `errors` list, empty when the account is clean and one
entry per missing or unparseable input otherwise (see Inputs).

The calibration section: an always-present section carrying optional
readings.  Rows of the experience ledger whose `tool` is
`calibration_ledger` (the writer is `tools/calibration_ledger.py`,
consumed read-only here) are read into `ledger_present` (true when the
ledger file exists and holds at least one valid row of any tool; an
absent or row-empty file reports false with null readings, stated never
padded), `entries` (the count of calibration rows), `agreement_rate`
(agreeing over readable entries, rounded to 4 decimals, `null` when no
entry is readable), and `by_class` (the breakdown by predicted grade,
sorted by name; per class: `class`, `entries`, `agreeing`,
`agreement_rate`).  An entry agrees when its predicted grade (`HIGH`
reads 1.0, `MID` reads 0.5) pairs with its measured face (`PASS` reads
1.0, `FAIL` reads 0.0) as `HIGH` with `PASS`; a `MID` row cannot agree
at value level by construction, and a `HIGH` row measured `FAIL` is the
rot shape.  A calibration row whose points text carries no readable
predicted/measured pair stays counted in `entries`, is excluded from the
readings, and is named in `errors` (fail loud, never swallowed).  The
stdout summary carries the calibration line, and calibration errors gate
the exit code like every other account.

## Honest boundary

`feedback_edge.status` is `open`: the approval rate and the repair outcome
mix are now readable, and nothing downstream consumes them yet. Scheduling
does not read this file; the missing consumer is declared here rather than
implied. The dashboard section (tools/evolution_dashboard.py) renders the
numbers, which is display only.

The calibration reading is consultative in the same sense: it states how
often the stored calibration entries agree at value level, and nothing
consumes it.  The admission port (tools/auto_round.py) is untouched by
this reading; an empty or absent calibration account reads null, never a
padded zero, and the agreement rule is a value-level reading of the
stored points text, not an independent re-judgment of any row.

## Selftest

`python -I tools/learning_feedback.py --selftest` runs seven vectors on
temporary fixtures: one auto plus one human round; malformed-line tolerance;
empty ledgers; all four outcome states unrecorded; and the three calibration
forms (a populated calibration account, an empty or absent ledger, a
calibration row with no readable pair). No network; writes stay
inside the fixture tree; importing the module has no side effects.
