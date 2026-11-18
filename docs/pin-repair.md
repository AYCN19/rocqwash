# pin-repair - provenance-pin drift repair for the jargon seed map.

Ticket: recursive three-gap closing batch (November 19, 2026), pin-repair lane.
Statement faces: tools/pin_repair.py; seeds/jargon/jargon-map.json;
  docs/ci-whitepaper-recursive-era-v1-20261116.md (R15); docs/ci-triage-table.json (R15);
  tests/t_engines_seeds.py
Source route: repo docs/ (the class definition lives in the whitepaper and the triage row)
Command: python -I tools/pin_repair.py --selftest
Registry: CAPABILITY-INDEX entry added same round

> Purpose.  Detect and repair silent provenance-pin drift: when a pinned
>   source file changed without the matching md5 re-sign in
>   seeds/jargon/jargon-map.json (`provenance.sources`), re-sign the pins
>   behind the sync tool's zero-write plan verdict.
> Interface.  `python -I tools/pin_repair.py [--selftest]`; `--plan`
>   reports the zero-write plan verdict only; `--apply [--seed <path>]`
>   re-signs drifted pins in place (key order and 2-space indent
>   preserved) and re-runs the seeds suite; the default seed is
>   seeds/jargon/jargon-map.json.
> Dependencies.  Python 3 standard library only; tools/jargon_map_sync.py
>   (the zero-write plan instrument, run with the repo root as cwd);
>   tests/t_engines_seeds.py (the verification gate).
> Evidence.  --selftest runs four offline vectors on tempfile fixtures;
>   --apply verifies through tests/t_engines_seeds.py (jargon segment
>   green, all pinned sources matching their md5 snapshots) and restores
>   the pre-apply byte snapshot on any red.
> Exit-codes.  0 = nothing to repair, a plan-only report, or an apply
>   verified by the seeds suite; 3 = the sync plan is not IN-SYNC
>   (content needs a decision a machine must not make); 4 = apply-time
>   verification failed (pre-apply bytes restored); 2 = usage errors.

## Problem

Provenance pins drift silently when a pinned source file changes without the
matching md5 re-sign in `seeds/jargon/jargon-map.json` (`provenance.sources`).
The pin check (`check_snapshot_md5`, tests/t_engines_seeds.py:514) opens the
pinned sources at absolute paths (two of the three pins sit outside the
repo), so hosted runners hit OSError and report SKIP: a hosted green run is
not evidence about the pins, and the canonical local face is the only layer
that verifies them. The live case recorded in the whitepaper section (source edit
9a5daeb without a re-sign, repaired in b3cbcf0, pin 1b042a18 to f21428f0)
produced that pair, hosted green and canonical red; class definition:
section R15 of `docs/ci-whitepaper-recursive-era-v1-20261116.md`.

## Usage

```
python -I tools/pin_repair.py --selftest
python -I tools/pin_repair.py --plan
python -I tools/pin_repair.py --apply [--seed <path>]
```

The default seed is `seeds/jargon/jargon-map.json`. `--plan` and `--apply`
share the front half: hash every `provenance.sources` entry (a missing file
is recorded absent), run the sync tool zero-write plan
(`python -I tools/jargon_map_sync.py`, cwd = repo root) and parse its
VERDICT line (`--plan` reports only). `--apply` re-signs drifted md5 values
in place (key order and 2-space indent preserved) and re-runs the seeds suite.

Exit codes:

| Code | Meaning |
|---|---|
| 0 | nothing to repair (`action:"none"`), a plan-only report, or an apply verified by the seeds suite |
| 3 | the sync plan is not `VERDICT IN-SYNC`; content needs a decision that a machine must not make; report `{ok:false, stage:"plan"}` with the raw verdict |
| 4 | apply-time verification failed; the seed file is restored from the pre-apply byte snapshot and the failure is reported |
| 2 | usage errors (standard argparse path) |

## Safety

- The re-sign runs only behind the sync tool's zero-write plan verdict
  `VERDICT IN-SYNC (plan is zero-write)` (tools/jargon_map_sync.py): content
  healthy, pin alone stale. Any other verdict exits 3 and changes nothing.
- `--apply` snapshots the seed file bytes before writing; if verification is
  not green it restores those bytes before exiting 4 (verify-rollback).
- Verification is the local gate the class prescription names:
  `python -I tests/t_engines_seeds.py` with the jargon segment green
  (`9 checks, 0 FAIL`) and all 3 pinned sources matching their md5 snapshots.
- In the CI context apply is desk/cron-gated: scheduled automation may run
  `--plan` freely; `--apply` on the canonical machine stays behind per-incident
  on-call approval, and the not-IN-SYNC branch stays with a human.

## Relation to the triage table

`docs/ci-triage-table.json` row `R15` carries `auto_repairable: true` with
the guard "re-sign only behind the IN-SYNC plan verdict". Before this
executor the flag stated policy; now the guarded branch (IN-SYNC plus drift)
is the mechanical path this tool runs and the escalation branch (not
IN-SYNC) exits 3 without touching the seed. Hosted faces stay blind while
the pins use absolute paths; a hosted-verifiable pin form is a separate
design decision kept in the whitepaper prescription.
