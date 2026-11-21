# `rocqwash-service-campaign-total` · 服务战役总报告 · service work-stream total report v1.0 (November 11, 2026)

> Purpose.  The cumulative total report of the v35-v41 work streams: diagnosis layer → orchestration layer → service layer → integration health-check layer → corpus expansion → canonicalization consolidation → parallelism and guardrails; seven work streams landed as seven commits on the single day of November 11, 2026, distilled into one document. This document is the deliverable of the v41 ledger schedule's "close-out total-archive work stream (v42)" (the source line `更新账.md:3760` labels it 五波累账总报告 (a cumulative total report of five work streams); this document carries all seven work streams of v35-v41 per its task instruction).
> Interface.  Document face only, a read-only distillation of in-tree materials: ① the ledger sections v35-v41 in `更新账.md` (`更新账.md:3552-3760`, the original untouched); ② the four existing `docs/` documents: workflow-integration-whitepaper / perf-profile / push-gate-dual-door-assessment / ops-realtime-service (the in-tree service-layer-overview of the same v40 close-out work stream is referenced alongside, for the §2 two-dimension classification); ③ `git log v35..HEAD` and `git show --stat` over the seven commits, run at writing time (hashes recorded per work stream in §1); ④ the cw.sh twenty-tool roster, read at cw.sh:99 and cw.sh:104-153. Every number and commit hash is transcribed from the in-tree materials above; zero from memory. The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  None at runtime (document face). Grounded in the rocqwash v41 tree (`c5df4d4`); `更新账.md` is read read-only; the frozen-eight set, quad8 and `更新账.md` were not touched (the ledger read-only); `cw.sh`, the full test suite and the README series belong to the integration agent and were not touched by this document's authoring lane. The three-gate close-out baseline (`doc_lint --repo` drift=0 / `tests/test_destructive_matrix.py` 17 verdicts all passing / `tests/run_tests.sh` full suite zero failing) belongs to the integration agent's final run; this lane does not run it on the integration agent's behalf; it only re-runs doc_lint after submitting this document, to verify zero drift for this document (end of §5).
> Evidence.  The commit chain in §1 is the `git log --oneline v35..HEAD` output run at writing time (seven commits, oldest → newest); the tool-roster facts in §2 come from the cw.sh route segments cited per row; the closing self-check re-ran `python3 tools/doc_lint.py --repo .` wrapped in `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120`; verdict consistent, drift=0, including zero flag drift for this document's flag citations (tail of §5).
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged.

## §1 The seven work streams in sequence (v35→v41 · key points and commit hash per stream) · 七波演进脉络（v35→v41·每波要点＋commit 号）

`git log v35..HEAD` run at writing time shows exactly seven commits (`git log --oneline` run in person, oldest → newest):
acf9fe6 (v35) → 4026051 (v36) → 41e74b0 (v37) → c205ea0 (v38) → caa3a28 (v39)
→ 496ebdf (v40) → c5df4d4 (v41, HEAD).

### Work stream 1 · v35 diagnosis layer (acf9fe6) · 波一·v35 诊断层（acf9fe6）

Tooling of the November 10, 2026 mac-runner CI diagnosis six-act live run (更新账.md:3554). Four tools were applied to the tree:
`tools/toolchain_dyld_doctor.py` (dyld broken-linkage diagnosis · otool -L parses the hard references → traces missing pieces back to their donor root → issues suggestions only, never executes on the user's behalf · the `--smoke` smoke run), `tools/net_probe.py`
(the network-window probe for the upload endpoint · the **double-probe stability-window rule**: STABLE only after two consecutive fully passing rounds · a single-probe round must not initiate),
`tools/ci_triage.py` (CI failing-build triage · the five-family classification spectrum: A content failing / B NETRED / C toolchain linkage failure / D queued-resource wall / E coqchk-skipped, plus the passing build · classification order UNRECOGNIZED>C>A>E>B>D ·
cross-checked against the reference as a multiple of `--baseline-seconds`), `tools/registry_union.py` (the registry union operation
· main as the base + extraction of the rows truly unique to base · A1/A2/A3 assertions fail loud · `--reanchor`
md5-8 canonical form · dry run by default). The local mapping's other half synced in step: the ConstructiveWorld-side cw_paths v1.0→v1.1
(更新账.md:3580). Integration surface: cw.sh carries eleven tools; full suite 47 cases / 43 passing / 0 failing / 4 SKIP
(更新账.md:3562). `git show --stat`: 26 files · +3610/-16.

### Work stream 2 · v36 orchestration layer (4026051) · 波二·v36 编排层（4026051）

The single-command pipeline chains the four v35 tools into a pipeline (更新账.md:3591): `tools/pushci.py` (1918 lines)
in five stages: preflight (the doctor environment check + the net_probe stability-window check + the optional `--pre-scan-gate4`
header pre-scan) → push (HTTP/1.1, three sends × 45 s → two sends rerouted through ghproxy · reroute only for github.com-shaped remotes) →
resolve + watch (head_branch + head_sha engagement · status-only basis) → heal (the family comes from ci_triage
classification · rerun after the double-probe stability window for B/E [403 idempotent], capped by `--max-heal 3` · A/C stop and are never auto-repaired ·
families outside the table never rerun automatically) → verdict ± merge (on 409, re-pull the tip, rest 60 s, retry ≤ 3) · the verdict
register holds seven states. **The orchestration adds zero new engines** (everything is subprocess over the v35 engines); six scenarios, 15 canned verdicts
(S1-S6 · the two `--injector` forms paired with `--git-caller` · offline, zero real network). cw.sh carries twelve tools;
full suite 48 / 44 / 0 failing / 4 SKIP. Cross-agent collaboration case: the test agent escalated "implementation absent" → the orchestration agent directed
"construct the implementation-independent pieces first + bounded polling" → the implementation was written to disk and aligned version by version: three layers, one agent each, zero collisions
(更新账.md:3598). `git show --stat`: 14 files · +3916/-22.

### Work stream 3 · v37 service layer (41e74b0) · 波三·v37 服务层（41e74b0）

From batch tools to a real-time dynamic service layer (更新账.md:3615). Three tools were applied: `tools/unclog.py`
(1161 lines · the clear-blockages closed loop: probe collection → chain_graph chain roots → cure_applier applies only from the canonical pack →
scan_v4 + probe re-check → verdict; the honest wall lists the cause per chain root and refuses to fabricate; dry run by default),
`tools/wash_shape.py` (the shape-normalization five-wash pipeline: word face / token / header / line ending / anchor · plan/apply two stages
· plan writes nothing to disk · frozen-roster entries are rejected loudly), `tools/cw_sentinel.py` (1079 lines · the real-time watcher takes three signal
sources: CI failing builds / local blockage records / build logs → JSONL event stream · **report-only by default, zero actions**).
The five interface disciplines run through all three tools: JSON-in/out with the schema designated · exit codes 0/1/2/9 (a failing
result is data, not a tool failure) · `--once`/`--loop` · `--injector`/`--sleep-scale` offline-testable · orchestration adds no new engine
(更新账.md:3627). cw.sh carries fifteen tools; full suite 51 / 47 / 0 failing / 4 SKIP; README-cw gained the
"workflow integration interface" section. `git show --stat`: 11 files · +4011/-13.

### Work stream 4 · v38 integration health-check layer (c205ea0) · 波四·v38 接驳体检层（c205ea0）

Integration and health checks (更新账.md:3645): `tools/cw_doctor.py` (1082 lines · the four-domain aggregated health check:
environment 40 / network 20 / registry 25 / blockage record 15 → health score 0-100, plus per-domain advice pointing each non-passing domain at its tool ·
a full real-machine run scored 91.67, healthy, rc=0); cw_sentinel `--on-red-preset` integration presets
(unclog/pushci · dry run by default as an invariant · mutually exclusive with `--on-red` at rc=2); unclog `--audit`
read-only audit of the real tree (the zero-write guarantee is hard: every file's md5 is proven identical before and after the run · mutually exclusive with --apply/--loop);
the resilience layer `tools/_http_backoff.py` (exponential backoff on 403/429/5xx · zero retries on the injector path) + subprocess hang protection
(`--timeout`/`--subproc-timeout`, default 120 s) + net_probe
`--jitter`/`--seed`. Three canonical embedded blocks under examples/workflows + docs/workflow-integration-
whitepaper v1.0 (11 bash fenced blocks, two `bash -n` rounds, 0 failures · 134 flags reconciled one by one by grep,
0 missing). cw.sh carries sixteen tools; full suite 52 / 48 / 0 failing / 4 SKIP.
`git show --stat`: 18 files · +3364/-171.

### Work stream 5 · v39 corpus expansion (caa3a28) · 波五·v39 语料滚扩（caa3a28）

Corpus expansion executed under the gold-standard discipline (更新账.md:3676): `wash/cure_pack.json` v1.3→v1.4
(24→25 patterns): a three-source survey yielded 11 candidates, **1 pattern accepted**: `cure39_ifq_connective_qualify`
(the citation anchor is the Set repository anchor commit 9a51c74, its diff walked verbatim across 25 sites · the face-regex is reused, zero new
engines), **10 candidates rejected, each with its reason recorded**; `tests/fixtures/header_map_v1.json`, the header template library
v1 (preset=`campaign_set_diamond` · all 6 placeholders carry citations · **a missing evidence cell refuses the load, enforced by code**);
`tools/doc_lint.py`, the doc↔implementation consistency three-checker (tool table / counts / flags ·
the first run had drift=3 → after the coordinating agent added the three routes netname-normalize / select-audit / doc-lint, verdict consistent with drift=0);
tests/test_relay_e2e.py, the integration end-to-end test + the docs/ops-realtime-
service operations manual. cw.sh carries seventeen → nineteen tools; full suite 54 / 50 / 0 failing / 4 SKIP; doc_lint
refs=87 drift=0. `git show --stat`: 18 files · +2962/-73.

### Work stream 6 · v40 canonicalization consolidation (496ebdf) · 波六·v40 正典化巩固（496ebdf）

Steady-state consolidation (更新账.md:3706): cw_sentinel state crash recovery (a corrupted state fails loud at exit 9 and is rejected
· `--rebuild-state` is the only legitimate rebuild path) + JSONL rotation (`--emit-max-bytes`, two generations retained
· seq numbering continues across generations); unclog `--loop` differential seen events; wash_shape plan-cache invalidation;
`tools/baseline_diff.py` (545 lines · compares two audit baselines → new/resolved/persistent
aligned cause by cause along the chain roots · **a different candidates set = incomparable, reported as it is and the ruling refused**); the **destructive-face review
matrix** tests/test_destructive_matrix.py, 17 rows of refuse-to-write verdicts (self-proven by negative-case injection · it caught one
real guardrail gap: cw_sentinel plain `--on-red` without `--emit` was accepted at rc=0 · the fix was scheduled to
v41); documentation close-out (the CONTRIBUTING five-interface-disciplines section + CHANGELOG + the docs/service-layer-
overview four-function × three-layer full picture + the examples/baselines/README procedure). cw.sh carries twenty tools;
full suite 56 / 52 / 0 failing / 4 SKIP. `git show --stat`: 16 files · +2953/-99.

### Work stream 7 · v41 parallelism and guardrails (c5df4d4) · 波七·v41 并行与护栏（c5df4d4）

Parallelism and guardrail-gap repair (更新账.md:3735): the sentinel guardrail-gap repair: plain
`--on-red` without `--emit` → rc=2 (cw_sentinel.py:883-886 · a bypass action must be accompanied by the event stream
written to disk), matrix S2 extended to both plain and preset directions (registered in v40 → made standing in v41); the dual-door unification assessment report
docs/push-gate-dual-door-assessment (**recommendation: option A (the two doors stand side by side and each rules on its own)** · zero code changes);
the probe_engine `--jobs K` parallel pool (default 1, serial, zero drift · **the ledger order always follows the canonical candidate order** ·
the thermal cap recommends K ≤ 2 · duplicate candidate names fail loud) + the unclog `--probe-parallel` pass-through + the report
timing section gains a jobs dimension (the vector goes thirteen → fourteen); the sentinel preset registry expands (the three new presets wash-shape
/ triage dynamic keys / cw-doctor + `PRESET_REQUIRED_ARGS` made declarative + chained
`--on-red-preset` continuing after one failure); the perf procedure and docs/perf-profile (four sources reported as they are · for DS4,
the K true-compile triple run is unmeasurable, so a method placeholder is recorded with zero invented numbers). The real-tree audit baseline 27/27 RC0, red=0, entered
examples/baselines/ (§4). Full suite 56 / 52 / 0 failing / 4 SKIP + the matrix 17 verdicts all passing + doc_lint
consistent. `git show --stat`: 14 files · +1239/-154.

## §2 The active capability table (cw.sh twenty tools · four functions × three layers, two-dimension classification) · 现役能力全表（cw.sh 二十工具·四职能×三层双维归类）

The unified entry `bash cw.sh <tool> [args...]` (repository root · arguments and exit codes pass through 1:1 ·
bash 3.2 compatible · the route contract at cw.sh:65-82). The twenty-tool roster was measured from the route segments
cw.sh:104-153 and cw.sh:207-226; the layer assignment and the function slots follow the docs/service-layer-overview §4 table (the v39 current state) plus each stream's account; baseline-diff (newly enrolled in v40) was slotted by this lane from the cw.sh:60-62
description (that account gives no function slot · noted as it is). "Pre-effort foundation" = the v29-v32 existing pieces (the engine faces the effort reuses);
the four functions = sanitize / shape normalization / failure diagnosis / clear blockages.

| # | Route | Target script | Layer | Function slot | Enrolled | One-line responsibility (default safe state) |
|---|---|---|---|---|---|---|
| 1 | `scan4` | `scan/scan_v4_token.py` | pre-effort foundation | survey face | v29-v32 | token-level qualified-name survey |
| 2 | `cure` | `wash/cure_applier.py` | pre-effort foundation | sanitize (the applier) | v29-v32 | the consumer-site cure canonical pack (dry run by default · v39 extends to v1.4, 25 patterns total) |
| 3 | `probe` | `wash/probe_engine.py` | pre-effort foundation | probe face | v29-v32 | batch closure-compatibility probe (v41 adds the `--jobs K` parallel pool · canonical-order determinism) |
| 4 | `chain` | `tools/chain_graph.py` | pre-effort foundation | clear blockages (root selection) | v29-v32 | the chain-root graph over merged accounts |
| 5 | `sync-ledger` | `tools/ledger_sync.py` | pre-effort foundation | ledger face | v29-v32 | merges and syncs the probe ledger with the status ledger |
| 6 | `erasure` | `verify/erasure_classifier.py` | pre-effort foundation | classification face | v29-v32 | the erasure-site classification advisor |
| 7 | `dual-scan` | `scan/dual_scan.py` | pre-effort foundation | differential-comparison face | v29-v32 | drives the two-scanner differential run |
| 8 | `doctor` | `tools/toolchain_dyld_doctor.py` | diagnosis layer (v35) | failure diagnosis | v35 | dyld toolchain broken-linkage diagnosis (diagnoses and suggests restore only · never executes on the user's behalf) |
| 9 | `net-probe` | `tools/net_probe.py` | diagnosis layer (v35) | failure diagnosis | v35 | the network-window probe (double-probe stability window · a single-probe round must not initiate; v38 adds `--jitter`/`--seed`) |
| 10 | `triage` | `tools/ci_triage.py` | diagnosis layer (v35) | failure diagnosis | v35 | CI failing-build triage (the five-family + passing-build classification spectrum · `--logs`/`--baseline-seconds`) |
| 11 | `union` | `tools/registry_union.py` | diagnosis layer (v35) | operation tool | v35 | the registry union operation (dry run by default · `--reanchor` md5-8 canonical form) |
| 12 | `pushci` | `tools/pushci.py` | orchestration layer (v36) | single-command pipeline | v36 | the post-repair CI-push single-command pipeline (preflight check → push → watch → heal → verdict ± merge · the seven-state verdict register · `--dry-run` has zero side effects) |
| 13 | `sentinel` | `tools/cw_sentinel.py` | service layer (v37) | failure diagnosis (real-time watcher) | v37 | the real-time dynamic watcher · three signal sources → JSONL event stream (report-only by default · five `--on-red-preset` presets, chainable · stabilized in v40 · v41 adds the double guardrail) |
| 14 | `wash-shape` | `tools/wash_shape.py` | service layer (v37) | sanitize / shape normalization | v37 | the canonical-form five-wash pipeline (word face / token / header / line ending / anchor · plan writes nothing by default · the `--header-map-preset` template library) |
| 15 | `unclog` | `tools/unclog.py` | service layer (v37) | clear blockages | v37 | the clear-blockages closed-loop engine (dry run by default · `--audit` read-only baseline · the honest wall refuses to fabricate · v41 adds `--probe-parallel`) |
| 16 | `cw-doctor` | `tools/cw_doctor.py` | service layer (v38) | failure diagnosis (aggregated) | v38 | the combined health check aggregates four domains → health score 0-100 + advice (diagnoses only, never executes on the user's behalf) |
| 17 | `doc-lint` | `tools/doc_lint.py` | service layer (v39) | close out (outside the four functions) | v39 | the doc↔implementation consistency three-check (tool table / counts / flags · verdict consistent/drift) |
| 18 | `netname-normalize` | `tools/netname_normalize.py` | pre-effort foundation (v39 entry completion) | name-normalization face | v39 | .v.v double-suffix name normalization (the mapping table + `--apply` renames verified by md5) |
| 19 | `select-audit` | `tools/select_audit.py` | pre-effort foundation (v39 entry completion) | audit face | v39 | the batch-selection auditor (greps the whole `order.txt` table with dedup + the Require-face audit v6) |
| 20 | `baseline-diff` | `tools/baseline_diff.py` | service layer (v40) | clear blockages (blockage-record comparison close-out) | v40 | the blockage-record baseline comparison (new/resolved/persistent + the four-state verdict · incomparable reported as it is and the ruling refused · timing excluded from comparison) |

Two-dimension quick read: **failure diagnosis** = doctor / net-probe / triage / sentinel / cw-doctor, five tools (the three diagnosis-layer
tools + the service-layer watcher and aggregated health check); **sanitize / shape normalization** = cure / wash-shape, two tools (cure is the applying tool ·
wash_shape is the orchestration apply face); **clear blockages** = chain / unclog / baseline-diff, three tools (root selection /
closed loop / comparison close-out); the close-out face doc-lint sits outside the four functions; the rest are the pre-effort foundation and the orchestration layer
(pushci spans the diagnosis, orchestration and consumption faces). The entry-count evolution 11→12→15→16→19→20 matches the per-stream
integration-surface lines in §1 item by item.

## §3 The case register (distilled from the v35-v41 accounts' case/criterion register sections · numbering carried over) · 判例总表（v35-v41 各账「判例/口径登记」节蒸馏·编号沿用）

The original numbering of each account's register section is carried over verbatim (register sections without numbers get a sequence number by order of appearance · the source anchor rides each row).

| # | Source anchor | Case / criterion | Distillation | Follow-up |
|---|---|---|---|---|
| v35-① | 更新账.md:3574（§三） | criterion correction | the v34 ledger recorded t_quad8_check as "failing": in this environment it is actually SKIP (rc=111 · the canonical repository's four-copy group is not present in the volume); the failure is not a tool failure and was not introduced in that round · the two environments' context difference is recorded side by side, as it is | the suite criterion "SKIP does not count as failing" holds to this day |
| v36-① | 更新账.md:3607（§四.1 契约偏离登记①） | the `--injector` dual form | the pushci `--injector` dual form (steps strictly per round + the flat fixture verbatim); the semantics were not loosened | the canonical form that makes the v36 six-scenario 15-verdict set offline-testable |
| v36-② | 更新账.md:3607（②） | the README count face | README.md carries no tool count (the change syncs the case-count row 43→48) | the case-count-row sync rule holds |
| v36-③ | 更新账.md:3607（③） | the README snapshot face | README.md has no v35 snapshot row (the v35 stream never entered the main README · that round only added the in-row v36 mention) | none |
| v36-④ | 更新账.md:3607（④） | no rewriting history on another's behalf | the tests/README.md "47 cases on record" was a current-state statement at the time · kept verbatim under the no-retrospective-history-edit rule | none |
| v37-① | 更新账.md:3632（§三） | cross-agent count drift | the watcher agent's cw.sh header count said thirteen while usage said twelve → the integration agent unified them at fifteen (cross-agent count drift · a close-out duty of integration · case on record) | the written precedent that count drift belongs to the integration close-out duty |
| v37-② | 更新账.md:3633（§三） | the injector philosophy | unclog `--injector` = "canned verification · real orchestration": under chain/cure/scan/frozen8 injection the tools still run for real (not puppet tests) · offline testability and real orchestration coexist | same source as the whitepaper §1 discipline-④ mechanism section |
| v38-① | 更新账.md:3663（§三裁决登记） | same-slot exclusivity | giving both `--on-red-preset` and `--on-red` = mutually exclusive at rc=2 (the task instruction's "preset wins" vs the selftest's "mutually exclusive" tension → ruled by the repository's same-slot-exclusivity discipline · boundary recorded in the docstring) | the negative-case table in the ops manual §2.2 is on record |
| v38-② | 更新账.md:3664（§三） | two clocks, not one bell | cw_sentinel `--timeout` (single HTTP request) and `--subproc-timeout` (the subprocess cap) remain two separate things (the v37 agreed criterion unchanged) | continued in the v40 §3 register |
| v39-① | 更新账.md:3693（§三） | expansion honesty | the cure_pack v1.4 single-pattern expansion is the honest survey conclusion (a pattern with no second-source reproduction waits for further survey per the rule · not an expansion shortfall) | the prefer-fewer-but-sound principle made into code (header_map refuses to load without evidence) |
| v39-② | 更新账.md:3694（§三） | criterion refinement | the evidence-based correction of the doc_lint phantom-reference/dangling-reference criteria (dup ≠ surplus · README.md:232 union-freeze `--world` legally carries multiple values) | the doc_lint criteria settled |
| v40-① | 更新账.md:3718（§二矩阵战果） | a real guardrail gap | the destructive-face matrix caught that cw_sentinel plain `--on-red` without `--emit` was accepted at rc=0 (the real guardrail lives in the preset path · a live probe run proved the action executes); double proof: negative-case injection self-verification + a real gap caught | **fixed in v41 and made standing** (the cw_sentinel.py:883-886 guard · matrix S2 extended to both directions) |
| v40-② | 更新账.md:3722（§三） | flag names kept separate | `--loop-max` and `--max-rounds` belong to unclog and sentinel respectively · no alias was created (the task instruction's slip corrected as it is · boundary recorded in the docstring) | none |
| v40-③ | 更新账.md:3723（§三） | the two-clock split continues | cw_sentinel keeps its two clocks separate (the on-red 60 s bypass cap stays as agreed in v37) | none |
| v41-① | 更新账.md:3747（§二跨席协作） | same-file serialization | the parallelism agent and the perf agent both edited unclog.py (the parallel layer + the timing dimension) = incremental dimension-adding on a shared base (the perf agent's first read before starting already saw the parallel layer · edits extended, never overwrote): the zero-collision actual record | a worked sample of two-agent same-file collaboration |
| v41-② | 更新账.md:3748（§二） | generation succession | the tool-produced account's generation succession recorded as it is: the audit baseline JSON was re-produced by the 07:12 true-compile run (the earlier rc=127 fast-fail record was overwritten) | perf-profile §1 DS1 reads the 07:12 version verbatim as authoritative |

## §4 The real-tree report (audit baseline 27/27 RC0 · the three-attempt history · the honest wall's refusal record) · 真实树战报（audit 基线 27/27 RC0·三发史·诚实墙拒判实录）

- **Target and candidate face**: the Set repository ConstructiveWorld_Live real tree · 27 pieces = the two placement batches of November 10, 2026
  (b48-52, thirteen + b53-57, fourteen · md5 measured and backfilled into the TSV) · the world = the runner workspace's Live APFS clone (537 vo · the active generation · zero touches to the runner's canonical copy) (更新账.md:3698,
  3727; `examples/baselines/audit-ConstructiveWorld_Live-20261111.note.md`).
- **The three-attempt history** (更新账.md:3752-3753 · the note sidecar's "comparison history" section): attempts one and two failed at rc=127 for a tool reason (the compiler was absent; one more proof of the "bare coqc does not exist" invariant) · **the honest wall refused the ruling, correctly**
  ("generation-gap type / tool-caused failure · no forced patching"); attempt three, carrying the `--rocq-cmd` 9.3 coqc template, went productive.
- **The productive-run report**: **27/27 RC0 · red=0 · wall=0** · cures_planned=0 (audit is read-only) ·
  verdict audit exit 0. Timing section: manifest 1.289 s / probe_chain 190.728 s /
  total 194.086 s (the only non-deterministic section · excluded from baseline comparison). This lane read the in-tree canonical
  `examples/baselines/audit-ConstructiveWorld_Live-20261111.json` directly and every item matches the numbers above (args.rocq_cmd = opam93 coqc `-native-compiler no -q -Q . "" {name}.v`
  · src=ConstructiveWorld_Live · world=probe_world_v38 · injector=null).
  Evidential meaning: the faces placed in the two batches of November 10, 2026 are **all closure-compatible** in the active world generation, hard-confirmed
  (更新账.md:3753).
- **Written into the repository**: the baseline JSON plus the run-account explanation sidecar md landed in examples/baselines/ · entered the repository with the v41 commit
  c5df4d4 (更新账.md:3754; `git show --stat c5df4d4` lists audit-…json at 71 lines
  + the note at 7 lines). The comparator is in place: baseline_diff.py produces the three add/remove lists from two audit baselines
  · the account self-consistency check blocks hand-written accounts (v40 §1②).
- **Generation succession, recorded as it is**: /tmp/audit_b48_b53_baseline.json was earlier the product of an rc=127 fast-fail
  run · overwritten at 07:12 by the true-compile run's re-production; perf-profile DS1 reads the 07:12 version verbatim as
  authoritative (the docs/perf-profile §1 DS1 provenance note · the v41-② case).
- **The honest-wall mechanism is on record** (the refusal record in this report is its first live use): the unclog honest wall's six causes
  self-unwashable/cure-miss/frozen-in-service/root-file-missing/exclusive-
  group-conflict/no-chain-root list the cause per chain root and refuse to fabricate (docs/ops-realtime-service
  §3.2); audit zero-write = every file's md5 proven identical before and after the run, a violation fails loud at 9
  (docs/ops-realtime-service §3.1).

## §5 Pending items and the v43+ roadmap (merged and deduplicated from each account's boundaries-and-pending section) · 待办与 v43+ 路线图（各账「边界与待办」节汇总·去重）

**Closed within the effort (pending item → where it landed)**: the pushci single-command pipeline (v35 boundary.1 → landed in v36);
the sentinel `--on-red` integration presets (v37 boundary.3 → landed in v38); the real-tree audit live run and the baseline
written into the repository (v38 boundary.1 / v39 boundary.1 / v40 boundary.1 → the v41 three-attempt productive run, written into the repository); the sentinel plain
`--on-red` guard fix and the matrix criterion made standing (v40 boundary.2 → landed in v41); the push_gate dual-door
unification assessment (v36 boundary.3 / v40 schedule → the v41 docs/push-gate-dual-door-assessment recommendation, option A side by side
· zero code changes · v41 boundary.2 closed); this total report (v41 boundary.3, scheduled to v42 → this document).

**Pending execution / unfinished (v43+ candidates · each with its source noted)**:

1. A real-tree measurement of probe `--jobs` > 1 (pending execution in the thermal window · the canned-mechanism evidence is complete): v41
   boundary.1; the DS4 true-compile K=1/2/3 triple-run placeholder awaits backfill into docs/perf-profile §5 (the backfill makes it
   perf-profile v1.1 · docs/perf-profile §6.3).
2. A real end-to-end CI live run of pushci (a real push → a real build → heal · for the first run, `--dry-run` first, then a real send): v36 boundary.2 and v38 boundary.2, same as the whitepaper Appendix A not-yet-run items.
3. Real-tree live runs of unclog `--apply` / wash_shape `--apply` (full verification at fixture level · for the first run a small `--src` subset first · the allowlist-form procedure is docs/ops-realtime-service §3.3):
   v37 boundary.1.
4. A real long-resident consumption scenario for sentinel `--loop` (a workflow background bash task attached to the JSONL stream · verified together with the next work stream): v37 boundary.2.
5. A real-tree live run of the new cure39 pattern (`cure39_ifq_connective_qualify`) (full verification at fixture level):
   v39 boundary.2.
6. The 9.1 compiler dependency face awaits its ruling (the `ROCWASH_ROCQ` conventional path is MISSING · point it at 9.3 CW_MAC93
   or the restored donated copy · the CW-side cw_paths v1.1 moved-root watch table is on record): v35 boundary.2.
7. A ci_triage `--watch` long-running monitor mode (a standalone long monitor beyond the watch embedded in pushci): v36
   boundary.3.
8. The wash_shape `--header-map` template library expands rolling with each effort's corpus: v37 boundary.3 (the v39
   header_map_v1 established the first library).
9. The residual risks of dual-door option A are on record: no mechanical check forces a workflow to rule on door B first (a single pushci run initiates on its own ·
   the window discipline rests on documentation and embedded-block constraints); if mechanical enforcement is wanted later, option B is the only path that leaves the canonical criteria unchanged,
   but the c4 full-suite cost and the c1 first-push deadlock on new branches must be solved first; docs/push-gate-dual-
   door-assessment §5 residual risks.

**Remaining in the v42 close-out total-archive work stream (scheduled at v41 boundary.3)**: the three-gate final run (doc_lint --repo
drift=0 / tests/test_destructive_matrix.py 17 verdicts all passing / tests/run_tests.sh full suite
zero failing) = the integration agent's final-run criterion (this lane does not run it on the integration agent's behalf · see the header); the real-machine drill compilation; the v43+ roadmap
(this section is its draft base).

Self-check at submission: after this document was written, `python3 tools/doc_lint.py --repo .`
was re-run wrapped in `bash /Users/apple/Desktop/ConstructiveWorld/
cpu_guard.sh -MaxWaitSec 120`
· verdict consistent, drift=0 (zero drift for this document's flag citations); the measured record is in the handoff notes.
