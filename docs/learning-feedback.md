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
>   per-class gear and confidence readings, and the four-state repair
>   outcome tally, written to docs/scheduling-feedback.json.
> Interface.  `python -I tools/learning_feedback.py [--selftest]`; the
>   default run reads the three standing accounts read-only
>   (docs/round-ledger.jsonl, docs/round-state.json,
>   docs/exp-ledger.jsonl) and writes docs/scheduling-feedback.json plus
>   a stdout summary.
> Dependencies.  Python 3 standard library only (argparse, JSON and JSONL
>   reading, tempfile fixtures); the three account files as read-only
>   inputs.
> Evidence.  --selftest runs four vectors on tempfile fixtures (one auto
>   plus one human round, malformed-line tolerance, empty ledgers, all
>   four outcome states unrecorded); zero network; writes stay inside the
>   fixture tree; importing the module has no side effects.
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
| `docs/exp-ledger.jsonl` | repair records; the outcome is not a stored column, so each row is classified from its `action` and `points` wording into `repaired`, `escalated`, or `watch_only_guard_correct`, and a row that fits none stays `unrecorded` |

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
 "feedback_edge": {"status": "open",
                   "note": "approval-rate now readable; scheduling does not yet consume it (declared blank)"}}
```

`approval_rate_auto` divides the auto-admitted round count by the total round
count, with human-approved rounds inside the denominator.
`repair_action_rate` is `repaired` over the four-state total and is `null`
when that total is zero.

## Honest boundary

`feedback_edge.status` is `open`: the approval rate and the repair outcome
mix are now readable, and nothing downstream consumes them yet. Scheduling
does not read this file; the missing consumer is declared here rather than
implied. The dashboard section (tools/evolution_dashboard.py) renders the
numbers, which is display only.

## Selftest

`python -I tools/learning_feedback.py --selftest` runs four vectors on
temporary fixtures: one auto plus one human round; malformed-line tolerance;
empty ledgers; all four outcome states unrecorded. No network; writes stay
inside the fixture tree; importing the module has no side effects.
