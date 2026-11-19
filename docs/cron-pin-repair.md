# cron-pin-repair - the scheduler-site pin repair leg and the bounded cadence hint.

Ticket: A-batch closed loop (November 19, 2026), documentation lane.
Statement faces: tools/selfevolve_round.py (--pin-repair leg;
  cadence_hint); tools/pin_repair.py; .github/scripts/selfheal_rocqwash.py;
  docs/repair-plan-ledger.jsonl; docs/scheduling-feedback.json
Source route: repo docs/ (docs/pin-repair.md; docs/ci-triage-table.json
  row R15); the N-series scroll (N2/N3/N7) and the A-batch contract faces
  live outside this repository
Command: python -I tools/selfevolve_round.py --dry-run --pin-repair
Registry: CAPABILITY-INDEX selfevolve_round entry, added the same round

> Purpose.  Document the two-site R15 repair form: which site applies,
>   which records only, how the report carries a bounded cadence hint.
> Interface.  Desk site: `python -I tools/selfevolve_round.py --pin-repair`
>   (plan, apply, one independent commit, the round's push carries it).
>   Hosted site: no flag, unchanged; the CI selfheal leg records only.
> Dependencies.  tools/pin_repair.py (the executor: IN-SYNC plan gate, md5
>   re-sign, verify-rollback); docs/scheduling-feedback.json (read-only
>   hint input); docs/repair-plan-ledger.jsonl (the recording write face).
> Evidence.  The site split and the tier table follow the A-batch contract
>   faces; the executor safety face (exit 3 on a non-IN-SYNC verdict; exit
>   4 restores the pre-apply bytes) is documented in docs/pin-repair.md.
> Exit-codes.  Documentation face; the round keeps its exit face (0 = a
>   green round; nonzero = the fail-loud gates of the CAPABILITY-INDEX
>   entry).

## Two-site form

The pins sit at absolute paths outside the repository (hosted runners read
SKIP, so a hosted green run carries no pin evidence; docs/pin-repair.md).
The sites split by what each can see:

| Site | Invocation | Pin behavior |
|---|---|---|
| hosted cron | no `--pin-repair` flag | the leg never activates; the round word face is unchanged; `.github/scripts/selfheal_rocqwash.py` keeps appending one plan-verdict row per R15 match to the ledger (action=plan, or action=executor-absent) |
| desk / local | `--pin-repair` given | plan the seed behind the IN-SYNC verdict; pinned sources absent on this host = one ledger row (action=plan, note=hosted-blind), then a clean zero-commit skip; drift with plan rc=0 = apply; zero drift = a one-line no-op |

## Apply-leg safety face

- Apply runs only behind the sync tool zero-write plan verdict
  `VERDICT IN-SYNC`; any other verdict exits 3 and changes nothing.
- The applied seed is one independent commit, class R15-repair, outside
  the jargon round account. Apply rc nonzero = fail-loud, zero commit;
  the executor self-restores the pre-apply bytes on a red check (exit 4).
- The leg is fenced: any unexpected failure appends one ok:false ledger
  row and the round main chain continues; the round never blocks on it.

## The cadence_hint tier table

The report carries `cadence_hint` from `docs/scheduling-feedback.json` (a
missing file reads hint normal, note absent). The mapping is a finite
constant table in code; thresholds are never generated at run time:

| Hint | Condition | Desk reading |
|---|---|---|
| alert | escalated >= 3, or repaired == 0 with total repair actions >= 5 | one cadence-alert row (schema rocqwash.repair-plan/1, action=cadence-alert) is appended to the ledger and printed loud |
| slow | repair_action_rate < 0.2 | the desk may lower the census cadence by order |
| normal | otherwise | cadence unchanged |

The cron expression stays untouched: the report carries the hint, the desk
decides. Current reading (escalated 0, repaired 1, rate 0.0244): slow.

## Relation to the N-series scroll

- N2 (the last automation segment of the data loop lives at the scheduler
  site): the desk leg realizes census -> drift -> plan -> apply -> commit
  -> push -> CI judge; the hosted site keeps the recording half, blind.
- N3 (feedback consumption must arrive bounded, same ticket): the tier
  table is that bound; apply leg and bound arrive in one increment.
