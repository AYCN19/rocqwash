# ops-evolve-手册-v1.0-20261113.md — operations manual for the autonomous-evolution engine, v1.0.

> **AutonomousEvolutionEngine**: the harvest → derive → spawn → validate → integrate loop, draft-only, human-review-gated.
>
> Purpose.  Map the natural-growth framing onto implemented machinery: variation = harness
>   signals → candidates; selection = suite + norm_lint + frozen checks; inheritance = ledger and
>   commit (§1); the draft output `--draft-out` and the implemented fitness accounting (§2);
>   safety invariants (§3); two recorded cases plus the cycle-1 live demonstration as the real
>   sample sources (§4).  Status: the engine face landed during this manual's issue window
>   (rocqwash v54 tree, `23943e8` base); every mechanism cited is live and anchored (§4.5).
>
> Interface.  Implemented face `tools/evolve.py --draft-out PATH [--json P] [--top N] [--baseline
>   P] [--jargon-map P] [--watch-repo ORG/REPO] [--sentinel-state F] [--sentinel-events F]
>   [--suite-ledger F] | [--suite-now] [--registry-git REPO --registry-ref REF] | --selftest`;
>   flags verbatim from the implemented `--help` (full table §2.1); report schema rocqwash-evolve/1.
>
> Dependencies.  Python 3 stdlib-only engine over existing stdlib-only tools; paths parameterized;
>   baseline data face `docs/norm-lint-baseline-20261113.json`; evidence accounts
>   `docs/判例-R3复发-route2tierA自愈-20261113.md` and `docs/复核-UNREC-14事件-20261112.md`;
>   frozen ledger `更新账.md` read-only (§3.3).
>
> Evidence.  `tools/evolve.py:3-58` (implemented five-field docstring); `tools/ci_triage.py:6-64`
>   (spectrum); `tools/red_dispatch.py:59-79` (presets); `tools/norm_lint.py:80-85` (schema,
>   budget); baseline error=2441 warn=1036 files=140; issue-time checks (§4.5): lint of this
>   file error=0, doc check consistent, engine selftest rc=0, suite green.
>
> Exit-codes.  Implemented: 0 = harvest/derive/draft completed (adverse signals are data,
>   reported explicitly); 2 = usage error; 9 = missing or unreachable input.  Fail-loud, no
>   silent downgrade; the engine never executes a candidate and never writes the repository.

## 1. Algorithm — natural growth, mapped to machinery

### 1.1 The three stages

A repository that improves itself across rounds is described by the natural-growth framing and
nothing more: new work items appear (variation), the checks keep what passes (selection), and
what passes is recorded so the next round starts from it (inheritance). Each stage is a tool
invocation with a fixed input and output schema; the framing names the loop, the machinery does
the work. The recorded v54 roadmap named the stages harvest → derive → spawn → validate →
integrate (`更新账.md:4101`); the implemented face realizes it as harvest → derive → draft — the
draft IS the spawn-gate deliverable, and validate and integrate stay human-executed (§1.4).
Harvest and derive realize variation and the frozen checks realize selection, all under the
human-review gate of §3.1.

### 1.2 Variation — harness signals → candidates

Variation is signal-driven, never invented. The implemented engine harvests five signal
classes (`tools/evolve.py:3-58`), each from an existing engine by subprocess — zero new engines:

| Signal class | Schema | Producer (implemented form) | Enters the loop as |
|---|---|---|---|
| norm fitness | `rocqwash-norm-lint/1` | a current `norm_lint --tree` scan diffed against the baseline ledger; frozen surfaces excluded from the translatable metric | translation-replacement candidates; the fitness delta |
| sentinel ci-red | `rocqwash-sentinel-event/1` | one `cw_sentinel --once` round over the watched repositories (`ci_triage` subprocess classification: families A/B/C/D/E plus none plus UNRECOGNIZED, run precedence UNRECOGNIZED > C > A > E > B > D, `tools/ci_triage.py:46`) | per-family action candidates |
| suite state | suite exit account | a captured `run_tests.sh` output, or a live run | selection-surface state for graduation (§1.3) |
| registry accounts | registry audit account | a `registry_audit --git` pass over the serviced books, increment against a supplied prior audit | registry prescription candidates |
| maintained UNRECOGNIZED | sentinel state + event stream | the long-lived stream's state and event faces | rule-refinement candidates |

Derivation rules — a candidate exists only when a stated rule maps a stated signal to it:

1. A jargon finding `{file, line, term, suggest}` becomes a translation-replacement candidate
   naming exactly that face and the standard form from the mapping table
   (`docs/jargon-to-standard-mapping-v1.md`).
2. A family verdict becomes a candidate whose first step is the implemented action
   (`tools/ci_triage.py:246-252`): fix-content, rerun-after-stable-window, restore-toolchain,
   queue-etiquette, or watch-only.
3. A routing-account route becomes a candidate whose body is the suggested command text (the
   route table of `tools/red_dispatch.py:24`).
4. A classification divergence against an independent ground-truth account becomes a
   rule-refinement candidate (worked case: §4.2).

The honest-variation rule: a candidate cites its signal (schema, event seq or run id, file:line)
and nothing else; shapes outside the taxonomy stay UNRECOGNIZED and are never force-fitted —
manual identification first, fail-loud (`tools/ci_triage.py:52-54`). Candidate ordering is
mechanical, not editorial: score = impact × evidence / effort, evidence clamped to [0,10],
deterministic order, plus the standing candidates persisted from the frozen-ledger lineage
(the Derive statement of `tools/evolve.py:3-58`).

### 1.3 Selection — suite + norm_lint + frozen checks

A candidate graduates only when the tree that carries it passes, in this order:

1. The full suite: `bash tests/run_tests.sh` exit 0; SKIP is not counted as red; 1 = any red
   (`tests/run_tests.sh:196-197`).
2. The linter on every touched prose face: zero error-level findings, report-only — findings are
   data and the exit code never escalates on them (`tools/norm_lint.py:13`).
3. The frozen checks, per surface crossed: the doc-vs-implementation check consistent
   (`tools/doc_lint.py`); registry rows only through audit → union / fix
   (`docs/contrib-isolation-protocol-v1.0-20261113.md:113-177`); a change that crosses a lane
   boundary runs the four intake checks — registry, norm, gate expectation, lane isolation, no
   short-circuit, BLOCK is data (`tools/contrib_intake.py:5-19`, `:31`); anything that would
   initiate a push runs the pushci preflight first — the no-initiate rule, unstable → stop,
   exit 1 (`tools/pushci.py:9-21`, `:51`).

Selection pressure is quantitative, not rhetorical: the baseline account
(`docs/norm-lint-baseline-20261113.json`, error=2441 / warn=1036 / files=140) must go down on
the curable basis defined in §2.5, and a round whose fitness account shows any class increased
is a rejected round. This is the
recorded v53 statement — the baseline account is the starting point of the selection pressure,
and the baseline reduction rate is the fitness signal (`更新账.md:4075`).

### 1.4 Inheritance — ledger and commit

A graduated candidate becomes heritable only through two records, both human-executed:

1. The ledger entry: the engine drafts the entry text into its task-book draft; a human appends
   it to `更新账.md` — the engine never writes the frozen ledger (§3.3).
2. The commit: a human commits, after `git fetch` — fetch before claiming, never plan against a
   stale mainline (`docs/contrib-isolation-protocol-v1.0-20261113.md:218-221`).

The ledger is the heritable record: the v46-v54 span (`更新账.md:3857-4107`) is nine releases of
recorded history that every new round reads as its starting point. Nothing else persists across
rounds; uncommitted working-tree state is not heritable.

## 2. Operate

### 2.1 Mode contract — one invocation, one round

The implemented engine is single-round: one invocation = one round of harvest → derive → draft.
Residency stays with the sentinel (`tools/cw_sentinel.py:130-131`); the engine reads maintained
state instead of running resident. Signals are enabled per flag — a run with no signal source
requested is a usage error (exit 2). Every flag below is an implemented harvest flag of
`tools/evolve.py`:

| Enable flag(s) | Signal class harvested | Notes |
|---|---|---|
| `--baseline P` | norm fitness vs the baseline ledger | schema `rocqwash-norm-lint/1`; missing file = 9; without it the norm signal is not harvested and the fitness delta is null (reported, never guessed) |
| `--watch-repo ORG/REPO` (repeatable) + `--sentinel-state F`; `--sentinel-state-seed F` seeds from the long-lived stream's state (read-only); `--sentinel-branch B` filters | new ci-red events — one `--once` round of the sentinel per watched repository | state required (exit 2 without it) |
| `--suite-ledger F` or `--suite-now` | suite last state | captured suite output, or a live run |
| `--registry-git REPO` + `--registry-ref REF`; `--registry-baseline P` prior audit for increment accounting | registry audit accounts over the serviced books | `--git-path-order` / `--git-path-project` overrides |
| `--sentinel-events F` | maintained UNRECOGNIZED events | read-only scan of the stream and state faces |

Common flags: `--draft-out PATH` (required; the parent directory must exist — fail loud 9, no
implicit mkdir), `--json P` (report target, schema rocqwash-evolve/1, sort_keys, overwritten;
the stdout summary line is always printed), `--repo-root DIR` (default: the parent of the
directory holding the engine), `--top N` (draft width, default 5; beyond-top candidates stay in
the report with in_draft=false), `--jargon-map P` (forwarded to the tree scan).

### 2.2 Canonical round forms

```bash
# one round: lint-fitness + suite-ledger signals (wrap in the temperature-control
# wrapper in real use; work artifacts under a work directory)
python3 tools/evolve.py \
  --baseline docs/norm-lint-baseline-20261113.json \
  --suite-ledger <work>/suite_last.txt \
  --draft-out <work>/draft-next.md \
  --json <work>/round.json

# one round with all five sources (sentinel state seeded from the long-lived
# stream; registry audit at the serviced tip)
python3 tools/evolve.py \
  --baseline docs/norm-lint-baseline-20261113.json \
  --watch-repo ORG/REPO-A --watch-repo ORG/REPO-B \
  --sentinel-state <work>/sent_state.json \
  --sentinel-state-seed <stream>/state.json \
  --sentinel-events <stream>/events.jsonl \
  --suite-now \
  --registry-git <repo> --registry-ref origin/main \
  --git-path-order ConstructiveWorld_Live/order.txt \
  --git-path-project ConstructiveWorld_Live/_CoqProject \
  --draft-out <work>/draft-next.md \
  --json <work>/round.json
```

Each invocation harvests the enabled signals, derives candidates by the §1.2 rules, and drafts
the next-round task brief. Idempotence is inherited from the sentinel: a repeated round with
the same state reports zero new events; a fresh state reports the full window (first-battle
semantics).

### 2.3 Residency relationship

The engine never runs resident. The long-lived watch stays with the sentinel, and the engine
consumes its maintained faces: the seed flag copies the stream's state (never written) so a
round reports only what the stream has not yet seen, and the events flag reads the maintained
stream for the UNRECOGNIZED face. Loop-shaped engine use is a shell-level repeat of the
single-round form — a fresh draft per round, the state file carried forward.

### 2.4 --draft-out — the draft file form

`--draft-out PATH` is required and names the draft FILE; together with `--json P` it is the
engine's entire write surface. The draft is the next-round task brief: constitution three-law
preamble auto-carried; per-candidate goal / approach / acceptance / grading; rendered for the
top `--top N` candidates. One draft per round. The cycle-1 live precedent — the human-run
pipeline that immediately preceded the engine face — placed its draft in `docs/` as a canonical
face with the five-field header (`docs/evolve-draft-cycle1-20261113.md`, companion record
`docs/演示-evolve首轮-20261113.md` §3). A draft is inert text: the engine executes nothing from
it and never writes the repository (§3.1).

### 2.5 Fitness accounting

The implemented report carries the account (schema rocqwash-evolve/1): signals{norm, sentinel,
suite, registry, unrec}; candidates[] each {rank, kind, title, score, impact, evidence, effort,
in_draft, basis}; fitness{baseline_delta, ...} — the norm delta computed against the baseline
ledger with the frozen surfaces excluded from the translatable metric; without the baseline
flag the delta is null (reported, never guessed). The fitness signal is the reduction rate of
the baseline classes (`更新账.md:4075`); the measurement denominator is the curable surface —
the tree excluding the frozen ledger and the archive faces the scanner already skips. This
denominator rule is registered from the cycle-1 verdict: the ledger appends jargon and
date-stamp faces at every entry on a surface the engine may never touch, so on the gross basis
the metric degrades by construction each cycle (cycle-1: gross −0.33% from ledger growth alone;
curable 0.00% with the tree holding its baseline exactly — `docs/演示-evolve首轮-20261113.md`
§4). The baseline snapshot faces are exempt from tree scans (`tools/norm_lint.py:440`), so
re-measurement never counts the baseline's own reports. Adverse deltas are data: the engine
exits 0 and reports the increase item-by-item; graduation still runs through the §1.3 checks —
findings are data, and a worsening is data too.

### 2.6 Exit-code contract and wrapper discipline

Implemented semantics: 0 = harvest/derive/draft completed (adverse signals are data, reported
explicitly); 2 = usage error (missing draft target, no signal source requested, malformed
flags, selftest assertion); 9 = missing or unreachable input (a requested signal source
unreachable or malformed, missing files, output parent missing, engine tool missing).
Fail-loud, no silent downgrade. Any downstream action that compiles or runs the Coq toolchain
goes through the temperature-control wrapper (`tools/cpu_guard.sh`, one of the frozen eight);
the engine's own stdlib rounds do not need it.

## 3. Safety

### 3.1 The spawn-stage human-review gate

Hard requirement: the engine only harvests, derives and drafts. The spawn stage writes
task-book drafts; a draft is not an action. Nothing runs, applies, merges or pushes because the
engine decided so — every next step becomes real only through a human decision recorded outside
the engine. The engine's write surface is exactly its `--draft-out` draft file plus its
`--json` report — the implemented write-surface declaration of the engine face. This is the
autonomous-execution boundary of the recorded safety track: the spawn stage produces draft
files and does not run or repair the repository on its own behalf.

### 3.2 No auto-apply — the inherited default-action ladder

The engine adds no execution path to any downstream tool; each keeps its implemented default
(the router's own principle: orchestration adds zero new engines, `tools/red_dispatch.py:8`):

| Tool | Implemented default | Anchor |
|---|---|---|
| `cw.sh dispatch` | report-only zero execution; the `auto` preset only on explicit request, 60 s per-event cap; `--dry-run` prints the plan only | `tools/red_dispatch.py:59-64` |
| `cw.sh registry-regen` | dry run by default; writes only under `--apply` | `cw.sh:82-84` |
| `tools/registry_fix.py` | dry run by default, staged in memory, automatic rollback on any post-apply assertion failure | `docs/contrib-isolation-protocol-v1.0-20261113.md:199-203` |
| `cw.sh pushci` | `--dry-run` = plan only, zero side effects; preflight unstable → stop, exit 1, zero push | `tools/pushci.py:123`, `:51` |
| `cw.sh norm-lint` | report-only; the gated and strict forms are reserved and a usage error today | `tools/norm_lint.py:56-61` |
| `cw.sh unclog` | dry run by default; the apply flag is appended only when explicitly requested | route table of `tools/red_dispatch.py:24` |

Content-surface repair is never automated: for family A the router emits a manual-fix note with
zero commands — content repair is human work; the router states it and the engine inherits it
(`tools/red_dispatch.py:28`).

### 3.3 Frozen surfaces

Read-only citation surfaces, never written by the engine or by any command a draft names: the
frozen eight — `scan/mac_stmt_scan.py`, `names/mac_stmt_names.py`,
`verify/gate4_comment_guard.py`, `tools/cpu_guard.sh`, `wash/wash_engine.py`,
`verify/verify_vo.py`, `seam/seam_probe.py`, `certify/freeze_manifest.py` (recorded at
`更新账.md:281`) — plus the quad8 four-replica group and the frozen ledger `更新账.md`. The
implemented engine imports the frozen-eight list from `certify/frozen8.py` and excludes those
faces from the translatable fitness metric, so the selection pressure can never be moved by
touching what is frozen. Ledger entries are drafted for human append (§1.4); a draft naming a
command that targets a frozen surface is malformed and must not be produced.

### 3.4 Gold-standard evidence discipline

Evidence required before issuance: every candidate, draft and account claim carries a stated
check — an executed command with its exit code, or a file:line anchor; no claims without a
stated check (the annotation card's Evidence field, `docs/annotation-standard-v1.0-20261113.md:53`).
A failing result is data, not a tool failure (the mapping table's phrase rows,
`docs/jargon-to-standard-mapping-v1.md:156`): rounds exit 0 with loud accounts, and exit codes
report instrument state only. Case evidence is anchored, not narrated: the two cases of §4 are
cited by document and line, and every number in them was produced by the issuing account's own
runs.

### 3.5 Non-negotiable constraints

1. Fetch first: before claiming any number or work item, `git fetch` and read the current tip
   (`docs/contrib-isolation-protocol-v1.0-20261113.md:218-221`).
2. Lane layering: the engine writes only its own faces — the draft directory and its accounts;
   it never edits another stream's output, a code identifier, a CLI flag name, a schema field,
   or an exit-code semantics (`docs/contrib-isolation-protocol-v1.0-20261113.md:225-229`).
3. Report-only until the review gate opens: the engine's report-only posture is structural, not
   a mode; the only gate that changes it is the human review of §3.1, and no flag in the §2
   contract opens it.

## 4. Evidence — the recorded cases as the engine's real sample sources

### 4.1 Case one — sentinel live catch, automatic recovery (v52)

The R3 recurrence case (`docs/判例-R3复发-route2tierA自愈-20261113.md`) is a complete recorded
generation on real data:

| Clock (Z) | Event | Anchor |
|---|---|---|
| 04:25:53 | runs #301 / #302 first failing at sha `8f59c8f` | case record §1 |
| 04:38:12 | sentinel live catch of run #301: event seq 58, family `A-content-red`, action `fix-content`, classified by the `ci_triage --offline` subprocess | case record :21 |
| 04:44:10 | colleague self-diagnosis lands the restore commit `bd8f38b` | case record :22 |
| 04:44:17 / 04:45:43 | runs #303 / #304 double passing at `bd8f38b` | case record :23 |
| ≈20 min | start-to-green, zero human decisions inside the monitor → classify → automatic-recovery loop | case record :26 |

Mechanism surface: 531/544 drivers fell into 5 same-second clusters (108/105/102/104/112);
527 explicit line-2 rows plus 13 exemption rows reconciled (case record §2-§3). The R3
"N drivers same-second" signature detection is registered as a rule-refinement candidate (case
record :85). Engine reading: signal (seq 58) → classification (`A-content-red`) → candidate
(`fix-content`) → human-applied fix (`bd8f38b`) → suite validation (double passing) →
inheritance (ledger and commits). The v52 account registers the case (`更新账.md:4040`);
"automatic recovery" is the standard form — first-use gloss: self-heal (mapping table row,
`docs/jargon-to-standard-mapping-v1.md:94`).

### 4.2 Case two — cross-validation against ground truth (v50)

The UNREC-14 re-check (`docs/复核-UNREC-14事件-20261112.md`) gave 14 UNRECOGNIZED events
(8 sentinel plus 6 from the full-history retro triage) an independent human ground truth:
verdict distribution A×1 / B×1 / E×8 / UNREC×4 (record :116-117); 10/14 rows diverged from the
tool face, each divergence recorded item-by-item without forced convergence (record :126; the
v50 account row, `更新账.md:3988`). Three rule-refinement candidates came out of the divergences
— scan-layer dump-line filtering, five attestation-red-family tokens into `KEY_LOG_PATTERNS`
(`tools/ci_triage.py:189`), and the attestation-state red form stays UNRECOGNIZED
(record :95-100) — and were implemented with selftest and fixture re-verification, the
corrected verdicts matching the re-check; true-UNREC residue 2, classification coverage 12/14
(`更新账.md:3997`). Engine reading: the selection-feedback generation in miniature — mechanical
verdicts are candidates, the independent ground truth is the selection surface, recorded
divergences are the heritable rule change. The case also fixes the honest-default rule
empirically: UNRECOGNIZED stays UNRECOGNIZED, manual identification first
(`tools/ci_triage.py:52-54`).

### 4.3 The cycle-1 live demonstration

The engine's first full cycle ran on this tree with zero new code — the pipeline executed
through the live tools themselves, immediately preceding the engine face and proving §1 end to
end (`docs/演示-evolve首轮-20261113.md`; spawned draft `docs/evolve-draft-cycle1-20261113.md`):

- Harvest: 3/3 named sources live, all rc=0 — the lint tree account against the baseline
  (`files=146 error=2449 warn=1062`, captured pre-write), a dual-repository sentinel `--once`
  round (60 runs observed, 10 events, families A×3 / D×3 / E×2 / C×1 / UNREC×1; a second round
  produced zero events — idempotence reproduced), and a fetch-first registry audit at the Set
  tip `0d58903b` (findings total 564: duplicates 12 + anchors 549 + orphans 3 + live topology
  0; fix_plan {dedup 12, orphan 3, reanchor 541}).
- Derive: five candidates graded mechanically (P0 / P1 / P2) from those signals only. The
  top-ranked candidate is the P0 diagnosis that the audited mainline tip itself is CI-red —
  family `A-content-red` at the same sha the audit prescribed against: the §4.1 shape replayed
  on a new signal. The checker self-citation candidate (−133 error, reviewer decision attached)
  is the §4.2 shape — a coverage gap turned into a rule-refinement candidate.
- Spawn: one draft face written, five candidates, each with verbatim evidence numbers and
  verbatim commands; zero writes outside the two engine-output faces; frozen surfaces
  read-only throughout; the human-review gate stayed closed.
- Fitness honesty: curable-error reduction 0.00% (1960 → 1960; the tree held its baseline
  exactly) — the selection pressure is measurable and no cure pass has run yet; the honest zero
  is recorded, not dressed up.

### 4.4 Sample-source rule

The two cases are the engine's labeled regression corpus: every new derivation rule must replay
at least one recorded case row without inventing candidates — a derivation rule that cannot
reproduce a row of §4.1 or §4.2 from its recorded signal is not admitted. What the engine
harvests today is exactly the §1.2 signal surfaces; the case documents are canonical evidence
accounts, read-only for the engine like every prose face it does not own.

### 4.5 Issue-time verification record

Checks run for this manual at issue time, each wrapped in the temperature-control wrapper
(`-MaxWaitSec 120`):

```text
python3 tools/norm_lint.py --selftest
python3 tools/norm_lint.py --file docs/ops-evolve-手册-v1.0-20261113.md --json <work>/lint.json --md <work>/lint.md
python3 tools/doc_lint.py --repo <repo-root> --json <work>/doclint.json
python3 tools/evolve.py --selftest
bash tests/run_tests.sh
```

Results recorded in the issue account (each command wrapped in the temperature-control
wrapper, as above):

- norm_lint selftest: rc=0 — six vectors PASS (map-load, jargon-hit, fields-missing,
  substring-exemption, whitelist-exemption, english-clean).
- norm_lint of this file: rc=0, error=0, warn=21 — one cjk warn (the H1 filename's transition-era
  token) plus twenty date-stamp warns from canonical path citations; zero jargon, header and
  budget findings.
- doc-vs-implementation check: this file ok — refs=72, unresolved=13, drift=0. The repo-wide
  verdict at the same moment is mid-integration drift owned by the engine face's arrival on
  disk (the cw.sh route registration and the help-cap generation step are the integration
  lane's pending moves); registered here, not repaired by proxy, per the lane-layering rule of
  §3.5. The first issue-time run — this file present, engine face not yet on disk — was
  repo-wide consistent, so this manual introduced no drift at any point.
- engine selftest: rc=0 — ten vector groups green (canned injection through real subprocesses,
  candidate rules, draft formation, frozen exclusion, idempotence, deterministic double run).
- full suite: exit 0 — 62 cases, 61 pass, 0 red, 1 skip (the quad8 four-replica case, absent by
  environment), matching the recorded v54 account (`更新账.md:4096`). The engine's suite case
  registration is the integration lane's pending step; this run measured the tree as of its
  start.
