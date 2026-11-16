# SOP: Feedback Edge v1, Human Calibration Ledger to Manual Render-Schedule Adjustment (rocqwash)

> **FeedbackLoopSop**: the five-field card for the manual feedback edge of the
> rocqwash self-evolution loop (ticket X7, batch 3, honest form).
>
> Purpose. Regulate the manual half of the loop: a human reads the calibration
>   ledger (docs/round-ledger.jsonl plus the evolution_dashboard output), then
>   adjusts the render schedule (the knobs that pace when the next round may
>   render into the tree), under explicit approval, in a fixed record form.
>   It also carries the standing declaration of the automatic edge after the
>   evolve demotion: candidates only, every execution step human-run.
> Interface. This scroll regulates and cites; it executes nothing itself. The
>   faces it names: `cw.sh evolution-dashboard` (tools/evolution_dashboard.py),
>   `cw.sh scheduler-lite plan` (tools/scheduler_lite.py), `cw.sh evolve`
>   (tools/evolve.py), `cw.sh auto-round` (tools/auto_round.py), the apply face
>   tools/jargon_apply.py, and the experience write port tools/exp_port.py.
>   Section 1 = what to read, section 2 = what to adjust, section 3 = who
>   approves, section 4 = the record form, section 5 = one worked pass.
> Dependencies. Python 3 stdlib tools only; zero network on every cited face;
>   schemas rocqwash-round/1, rocqwash.round-state/1,
>   rocqwash-evolution-dashboard/1, rocqwash.scheduler-lite.plan/1 and
>   rocqwash-exp/1 as fixed by their owning tools; no schema is redefined here.
> Evidence. First-hand readings taken in the casting session and quoted
>   verbatim in section 5: the live dashboard summary line, the live scheduler
>   plan line, both tool selftests (rc=0), the two live round rows, and the
>   ruling provenance cited per section (work order, release scripts, ledgers).
> Exit-codes. This card is a document and exits nothing itself; the exit codes
>   of the cited tools are described, never redesigned (0 = the face answered,
>   1 = a gate refused or selftest red, 2 = usage, 9 = missing or corrupt
>   input; each tool's card is the authority for its own numbers).

## 0. Scope and the standing declaration of the automatic edge

### 0.1 The loop this scroll regulates

The self-evolution loop has two edges. The automatic edge produces material:
candidates (`tools/evolve.py`), plans (`tools/scheduler_lite.py`), and gated
round commits (`tools/auto_round.py`). The manual edge judges and paces: a
human reads the rendered calibration ledger, decides whether and when the next
round may render into the tree, changes the pacing knobs, and records the
decision. This scroll fixes the manual edge: what to read (section 1), what to
adjust (section 2), who approves (section 3), what to write down (section 4).

### 0.2 Declaration: the automatic edge after the evolve demotion

Standing declaration (ticket clause, ruling of record): after the evolve
demotion adopted as default in the batch-3 work order (candidate ruling point
5: "T2-3 annotation form, T2-1/2 demotion"; the work order is the v2 merged
draft titled "effective repair strengthening and recursive batch 3",
20261116, line 3), the automatic edge of this loop is a candidate-declaration
edge:

1. `tools/evolve.py` declares candidates and nothing else: "evolve never
   executes a candidate or writes the repository" (tools/evolve.py:13-14);
   the draft is a human-gated task brief (tools/evolve.py:5-14).
2. `tools/scheduler_lite.py` plans only: "the face plans only and never fires
   (dry-run by design)" (tools/scheduler_lite.py:10-11); the plan document
   carries `"dryRun": true` (tools/scheduler_lite.py:309) and the two ignite
   pipeline lines are informational, "This face executes neither step"
   (tools/scheduler_lite.py:63-67).
3. The machine writer of the forward loop is the round commit face, and it is
   gated: admission per the gear, soft-stop check, verify gate, one commit,
   one ledger row (tools/auto_round.py:37-44), with certification-face scope
   refusal built in (tools/auto_round.py:118-120); the rollback and salvage
   faces are recovery writers with their own gates (tools/auto_round.py:51-75).
4. Therefore: no candidate, plan, or dashboard reading ever executes itself.
   Execution is the manual edge acting through sections 2 and 3.

Honesty note on the tree wording: the demoted wording ("signal-to-task-brief
generator") is not yet in the tree surface; README and cw.sh still carry the
older engine wording (README.md:19, cw.sh:91), and the wording demotion rides
the release's F4 ticket (wf-ef-lanes-20261116.dwf.ts:169). The declaration above
is the ruling this SOP records; the wording faces are the F4 ticket's write,
not this scroll's.

### 0.3 Verdict semantics

- Every reading below is data: quiet, blocked, absent, and zero rows are
  readings, not errors; the cited tools exit 0 for them by design.
- A knob change without its record row is a violation of this scroll, not a
  style issue: the record is what makes the pacing auditable.
- Refusals are loud: a gate refusal (exit 1) or a corrupt input (exit 9) stops
  the loop pass; it is never worked around silently.

## 1. What to read (the human calibration ledger)

Read in this order, all faces read-only:

### 1.1 The round ledger (docs/round-ledger.jsonl, schema rocqwash-round/1)

Append-only JSONL, machine-written by the round commit face; the row carries
ten contract keys plus the additive verify_kind key: round_id, mode, base_sha,
head_sha, classes_applied, admissions, files, verify_rc, oscillation_count,
timestamp_utc (tools/auto_round.py:100-105). Read the tail rows for: verify_rc
(the gate truth of each round), admissions (what the gear admitted and on what
basis), oscillation_count (a file:line site touched too often; the alert
threshold is autonomy.json `oscillation_alert`), and mode (auto, gated,
salvage, rollback). The ledger and the state file are working-tree records the
port never stages, so a rollback revert cannot rewrite round history
(tools/auto_round.py:108-110).

### 1.2 The evolution dashboard (schema rocqwash-evolution-dashboard/1)

One command renders the three standing accounts into one reading:
`cw.sh evolution-dashboard` or `py -I -X utf8 tools/evolution_dashboard.py
[--stdout markdown|json] [--json-out P] [--md-out P]` (tools/evolution_dashboard.py:16-21;
cw.sh:136-137). It aggregates docs/exp-ledger.jsonl, docs/round-ledger.jsonl
and the vacgen v2 report directory (tools/evolution_dashboard.py:44-46). The
reading rules are fixed by the tool's field notes (tools/evolution_dashboard.py:50-61):

- rounds conversion: greenRounds counts rows with verify_rc = 0; greenPct and
  classConversionPct are the conversion face of rounds into admitted classes;
- coverage curve: one point per vacgen report, ordered by content time then
  runId; todoSeatsDelta against the previous point; a positive delta sets the
  rise flag, and a rise is a signal (the fill-round discipline expects the
  TODO-SEAT count to be monotone non-increasing);
- thermometer: the latest curve point is the current gap reading.

Absent inputs and zero rows are data states, loudly marked, never errors
(tools/evolution_dashboard.py:8-13). Outputs written with --json-out/--md-out
are dated snapshots of the input content, not records; do not treat them as
the ledger (section 4).

### 1.3 The scheduler plan (schema rocqwash.scheduler-lite.plan/1)

One command answers "is a jargon-class round due":
`cw.sh scheduler-lite plan [--ef-marker P] [--threshold N] [--interval-seconds N]
[--json]` (cw.sh:148-149). The verdict is quiet | due | blocked; blocked rows
carry reason tokens: ef-gate-closed, autonomy-gated, class-not-admitted,
cadence-not-due (tools/scheduler_lite.py:289-296). The plan shows the gap
signal (todoSeat total vs threshold), the cadence (measured tail-pair interval
or the backfill constant, and whether the spacing has elapsed), the tier-B
gear face (autonomy mode plus the admitted roster in docs/round-state.json),
and the EF all-green marker gate (tools/scheduler_lite.py:265-279).

### 1.4 The four standing alarms

A loop pass is mandatory (not optional) when any of these appears in the
reading: (a) a round row with verify_rc != 0; (b) a dashboard rise flag or a
rising TODO-SEAT thermometer; (c) a scheduler verdict=blocked with any reason
token; (d) oscillation_count above zero in the round tail or the state file.
Otherwise a pass may be paced by the cadence the scheduler reports.

## 2. What to adjust (the render-schedule knobs)

"Render schedule" means the knob set that paces when the next round renders
into the tree: the trigger threshold, the round interval, and the gear config.
The complete adjust list, and nothing outside it:

| Knob | Where it stands | Runtime override | First authority |
|---|---|---|---|
| gap trigger threshold | DEFAULT_THRESHOLD = 1 (tools/scheduler_lite.py:50) | `--threshold N` | the reader per pass; a standing change is a PR edit |
| round interval seconds | DEFAULT_INTERVAL_SECONDS = 40566, a measured backfill of the round-ledger tail pair (tools/scheduler_lite.py:53-56) | `--interval-seconds N` | candidate ruling point 3: the measured axiom_guard first-run timing backfills this one knob (work order line 88); the same ruling is written at tools/scheduler_lite.py:53-55 |
| gear mode | autonomy.json `mode` (auto | gated) | none (config file) | tools/auto_round.py:81-85 |
| admission threshold | autonomy.json `admission_threshold` (now 0.8) | none | tools/auto_round.py:86-87 |
| soft-stop cap | autonomy.json `max_unreviewed_rounds` (now 12) | `--continue` on one commit, explicitly | tools/auto_round.py:88-90 |
| oscillation alert | autonomy.json `oscillation_alert` (now 2) | none | tools/auto_round.py:91-93 |
| verify gate | autonomy.json `verify_cmd` (now the axiom_guard compile leg, the E4/X1 swap) | none | tools/auto_round.py:94-98; autonomy.json:1-7 |

Not knobs, never adjusted from this loop: the EF all-green marker gate is a
release gate, open or closed by the marker file only (tools/scheduler_lite.py:265-279);
the certification-face family (certify/, verify/, wrapper/, scan/), the frozen
eight roster, and the repo-root update ledger are outside every write this
loop can propose (work order constraint block, section 4); the jargon map's
own source table and the frozen roster are never wash targets
(tools/jargon_apply.py:15-16).

### 2.1 The ignite pipeline (manual execution only)

When the scheduler verdict is due and section 3 has approved, the round is
rendered by two human-run steps, exactly the pipeline the plan declares
(tools/scheduler_lite.py:65-67):

1. `py -I -X utf8 tools/jargon_apply.py --tree --apply` (the plan face is the
   default zero-write form; --apply splices and rescans; residue zero is the
   exit-zero gate, tools/jargon_apply.py:6-11);
2. `py -I -X utf8 tools/auto_round.py commit --classes jargon --files <step1
   plan files> --hits <hits.json>` (one verified round: admission, soft stop,
   verify gate, one commit, one ledger row, tools/auto_round.py:37-44).

A re-run of a landed round is a loud nothing-to-do (exit 0, no write), so
idempotence is built in (tools/auto_round.py:42-44). A knob change lands as a
PR review of the config or constant edit; nothing in this loop pushes to main
directly (the release integration form; fork push only).

## 3. Who approves

| Decision | Approver of record | Recorded by |
|---|---|---|
| class admission (out-of-band) | the receiver-side project user | `auto-round approve --class NAME [--confidence X] [--note TEXT]` writes the state entry (tools/auto_round.py:45-47, 851-871) |
| soft-stop release / re-baseline | the receiver-side project user | `auto-round anchor --promote` (tools/auto_round.py:48-50, 874-895) |
| knob standing change (interval, threshold, gear keys) | the receiver-side project user, by PR review | the PR plus the ruling row (section 4.3) |
| ignite run of a due round | the receiver-side project user | the round row the commit face writes |

The approver-of-record precedent is verbatim in the state file: "human
point-order approved (unconditional); ruling by the receiver-side project user
2026-11-15, transcribed verbatim by receiver main session; evidence pack ...
md5 OK" (docs/round-state.json admitted_classes row 2). Seats and sessions
read, render evidence, and propose; they never self-approve an admission, a
knob change, or an ignite run. A ruling is transcribed verbatim into the
record that carries it; a paraphrase is not a ruling.

## 4. The record form

Four forms, each owned by its port; nothing else is written:

1. **Round row** (docs/round-ledger.jsonl, rocqwash-round/1): machine-written
   by the commit face only (tools/auto_round.py:100-105). This is the record
   of an executed round; humans do not hand-edit it.
2. **Approval entry** (docs/round-state.json, rocqwash.round-state/1): written
   by `auto-round approve`; fields class, confidence, basis, coq_comment_safe,
   timestamp_utc (tools/auto_round.py:112-116, 159-160). The basis string is
   the ruling-of-record slot: who approved, when, on what evidence pack.
3. **Ruling row** (docs/exp-ledger.jsonl, rocqwash-exp/1): one append per
   pacing or knob ruling, through the experience-bus port
   `exp_port.py append --tool T --points P --evidence E --batch B [--id ID]`;
   repeats of the same content are loud no-ops, so retries stay idempotent
   (tools/exp_port.py:6-14). This is where a knob change (interval backfill,
   threshold amendment) is recorded with its measured basis.
4. **Repair-outcome row** (docs/repair-ledger.jsonl, rocqwash-repair-ledger/1):
   when the loop's change repairs a red, the outcome lands here with its
   evidence; the live rows carry outcome repaired and escalated
   (docs/repair-ledger.jsonl:1-4), the writer face is the flaky-guard port
   (tools/flaky_guard.py:73-77), and a quarantined case is watched by the CI
   flaky-watch lane, never hidden (tools/flaky_guard.py:46-51); "watch-only"
   names that observation posture, not a ledger outcome.

Minimum record discipline: every knob change carries (a) the ruling row of
form 3 with the measured basis and the approver, (b) the PR that carries the
edit, (c) the next round row that shows the new pacing in force. A knob change
with fewer than three traces is not landed.

## 5. One worked pass (this session, zero writes)

The casting session ran the read faces against the live tree and changed
nothing. Commands and verbatim outputs:

- `py -I -X utf8 tools/evolution_dashboard.py --stdout markdown` (rc=0):
  `evolution_dashboard rocqwash-evolution-dashboard/1: experienceLedger=30
  entries / 10 batches rounds=2 rounds, green 100, class conversion 50
  coverage=absent`; the rounds table shows both rows mode=auto verify_rc=0
  (docs/round-ledger.jsonl rows 1-2; round 1 admitted jargon on the gear-auto
  basis "confidence 1.00 >= threshold 0.80", round 2 registered the
  point-order class out-of-band, admissions empty).
- `py -I -X utf8 tools/scheduler_lite.py plan --ef-marker
  D:/ComplexAnalysis/attn/_eflanes_out_20261116/ef-done.marker` (rc=0):
  `scheduler-lite plan: verdict=quiet todoSeat=0/1 cadence=measured 40566s
  due=true gear=auto class=jargon admitted=true gate=open (dry-run only; no
  ignition face)`.
- `py -I -X utf8 tools/scheduler_lite.py --selftest` (rc=0, all vectors PASS,
  including source-cjk-free-em-dash-free) and
  `py -I -X utf8 tools/evolution_dashboard.py --selftest` (rc=0,
  EVOLUTION-DASHBOARD SELFTEST PASS, 8 vectors).

Verdict of the worked pass: no alarm fires (no red verify_rc, no rise flag,
verdict=quiet, oscillation zero), so the loop pass records nothing and adjusts
nothing. The interval knob stays at the measured ledger backfill 40566 s until
the axiom_guard first-run timing is measured and approved (candidate ruling
point 3 remains open; work order line 88). The coverage face reads absent
because docs/vacgen-reports/ holds no report yet; that is a data state inside
the tool contract, not a fault (tools/evolution_dashboard.py:8-13).

## 6. Boundaries (honest limits of this v1)

- The loop stays manual by design in v1: the KPI-driven level-3 scheduler full
  form is a later ticket (batch-4 ticket T4-1; the extensible ticket list in
  the batch-2 package techdocs, section 5); nothing in this scroll automates a
  decision.
- The wording demotion named in section 0.2 is a ruling of record; the README
  and cw.sh wording faces ride the release's F4 ticket and are not this scroll's
  write.
- This scroll adds no schema, no tool, and no route; doc_lint must stay at
  zero new findings from this file (work order language gate, section 4).
- The zh rendition, if one is wanted, archives as a .zh.md sibling or under
  docs/zh/ per the language law; this face itself stays zero CJK.
- Registered exemptions (date-stamp findings of norm_lint, class forbidden,
  unfixable without falsifying a record): this face's :50 carries the
  work-order date because it pins the ruling of record to its exact document
  and line; :72 carries the stamp because it is part of the cited release
  script's real name; :197 carries the date because it sits inside the
  verbatim ruling quote that section 3 requires to be transcribed verbatim.
