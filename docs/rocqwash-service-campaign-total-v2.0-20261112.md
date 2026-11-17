# `rocqwash-service-campaign-total-v2.0-20261112.md` — the rocqwash service effort total report, v2.0 (compiled November 12, 2026).

> Purpose.  The consolidated total report of the rocqwash service effort: v2.0 keeps the complete v1.0 base (`docs/rocqwash-service-campaign-total-v1.0-20261111.md` · the accumulated ledger of work streams v35-v42, November 11, 2026) and adds the "six-work-stream addendum (November 12, 2026)" chapter — v43 the ad-hoc real-run measurement → v44 the resident watcher's first rehearsal → v45 the ledger renderer → v46 red-event routing and the registry audit → v47 the gated-compile arc closed and the watcher's first real-repository field run → v48 the multi-repository assessment and the DS4 three-account close-out. This face is the v2.0 continuation archive of the v1.0 §5 "v42 close-out total-archive work stream remainder", designated by the task instruction. Documentation-only face: read-only and writing, zero code changes; the frozen eight families, quad8 and the ledger `更新账.md` were never touched (the ledger read-only); the rocqwash working tree carried zero git commits at authoring time (v48 `325b4dc` · the clean-tree wording preserved); `cw.sh`, the full test suite and the README family belonged to the integration agent and were not touched.
> Interface.  Document face only; no runtime interface. Every fact is cited from a named source: the ledger `更新账.md` v43-v48 sections (`更新账.md:3794-3944` · read-only distillation, the original untouched); `docs/勘形-multi-repo-Main仓适配-20261112.md` (the v48 ⑦ assessment document); `docs/perf-profile-v1.0-20261111.md` §5's two backfill sections + `examples/baselines/perf-README.md` §3's three judgment rules; `docs/ops-sentinel-长驻手册-v1.0-20261112.md` (the v48 watcher manual); the three baseline accounts in `examples/baselines/` (K1=`audit-ConstructiveWorld_Live-20261111.json` · K2=`perf-ConstructiveWorld_Live-k2-20261111.json` · K3=`audit-k3-20261112.json`); the `git log c5df4d4..HEAD` and `git show --stat` measurement of the six commits; the three v48 resident-watcher artifacts under the CW-side `_log/sentinel_v48/`. The original Chinese text of this face is preserved in the sibling `.zh.md` archive.
> Dependencies.  Read-only distillation of the frozen ledger `更新账.md` and of the in-tree documents listed under Interface; no runtime dependency; no code face is modified by this document.
> Evidence.  Every number is transcribed from the named on-disk materials · zero values from memory. This agent read the K3 account in this ask and it matches item by item (`args.probe_parallel=3` / `timing.probe_chain_s=165.202` / `n_records=27` / `n_red=0`); the `git log c5df4d4..HEAD` and `git show --stat` runs of the six commits were executed by this agent in this ask, hashes recorded work stream by work stream in §6; the v48 watcher artifacts (`ls` / `wc -l` / python3) were measured by this agent in this ask. The task instruction's "23→24→25 tool-count evolution" disagrees with the measurement — measured 23 (v46) → 24 (v47) → **24 (v48, zero new tools)**; recorded as measured, per the same rule as the assessment document §1.3 and the v35-① criterion-correction precedent (§7.1). The three-gate close-out baseline (`doc_lint --repo` drift=0 / `tests/test_destructive_matrix.py` 17 verdicts all passing / `tests/run_tests.sh` the full suite zero failing) belongs to the integration agent's final run — this agent did not rerun the full suite; after this document's submission only the doc_lint check is rerun to verify this document's zero drift (the end-of-document submission self-attestation).
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged.

---

## §0 The v1.0 base full text (November 11, 2026, preserved verbatim · zero changes)

> **Base statement**: the following is the full text of `docs/rocqwash-service-campaign-total-v1.0-20261111.md` preserved verbatim (the v42 close-out point-in-time wording) — point-in-time statements ("active", "twenty tools", "56 cases", "onboarded" and similar) all carry the November 11, 2026 base wording · for the current state consult the §7 count master table and the §6 per-work-stream accounts; the six-work-stream close-out reconciliation of its §5 nine pending-execution items is at §6.x; the v1.0 end-of-document submission self-attestation line is that round's own measured record · this face neither reran nor altered it.

**rocqwash service effort total report v1.0 (service effort total · November 11, 2026)**

> **The v35-v41 seven-work-stream accumulated-ledger total report** — diagnosis layer → orchestration layer → service layer → hookup health-check layer → corpus expansion → canonical consolidation → parallelism and guardrails; seven work streams (seven commits) within the single day of November 11, 2026, distilled across the whole effort. This face is the deliverable of the v41 ledger-scheduled "close-out total-archive work stream (v42)" (the `更新账.md:3760` original reads "five-work-stream accumulated-ledger total report" · this face carries the whole effort's seven work streams v35-v41 per the task instruction).
>
> **The materials and fact discipline** (every number transcribed from the on-disk materials below · zero from memory): ① the `更新账.md` v35-v41 sections (`更新账.md:3552-3760` · read-only distillation, the original untouched); ② the four existing docs/ faces — workflow-integration-whitepaper / perf-profile / push-gate-dual-door-assessment / ops-realtime-service (plus the in-tree service-layer-overview of the same v40 close-out work stream, consulted for the §2 two-dimension classification); ③ the `git log v35..HEAD` and `git show --stat` measurement of the seven commits (run by this agent in its ask · the hashes recorded work stream by work stream in §1); ④ the cw.sh twenty-tool roster measured (`cw.sh:99`, `cw.sh:104-153`).
>
> **This agent's discipline**: read-only and writing · zero code changes; the frozen eight / quad8 / `更新账.md` untouched, verified (the ledger read-only); `cw.sh` / the full test suite / the README family belonged to the integration agent, untouched. The three-gate close-out baseline (`doc_lint --repo` drift=0 / `tests/test_destructive_matrix.py` 17 verdicts all passing / `tests/run_tests.sh` the full suite zero failing) belongs to the integration agent's final run — this agent did not rerun it, and only reran the doc_lint check for this document after drafting (§5, end).

### §1 The seven-work-stream evolution line (v35→v41 · per-work-stream key points + commit ids)

The `git log v35..HEAD` measurement shows exactly seven commits (run by this agent: `git log --oneline`, oldest → newest):
acf9fe6 (v35) → 4026051 (v36) → 41e74b0 (v37) → c205ea0 (v38) → caa3a28 (v39)
→ 496ebdf (v40) → c5df4d4 (v41 · HEAD).

#### Work stream 1 · v35 diagnosis layer (acf9fe6)

The tooling of the six-act November 10, 2026 mac-runner CI diagnosis drill (`更新账.md:3554`). Four tools applied:
`tools/toolchain_dyld_doctor.py` (dyld linkage-failure diagnosis · `otool -L` parsing of hard references → missing pieces traced to their donor roots → recommendations only, never executed on the user's behalf · `--smoke` smoke check), `tools/net_probe.py`
(the upload-endpoint network-window probe · the **two-probe stability-window rule** — two consecutive fully passing rounds before STABLE · a single-probe round must not initiate),
`tools/ci_triage.py` (CI failing-build triage · the five-family classification spectrum A content-failing / B NETRED / C toolchain linkage failure / D queueing resource saturation / E coqchk-skipped, plus passing builds ·
the classification order UNRECOGNIZED > C > A > E > B > D ·
the `--baseline-seconds` multiple lookup table), `tools/registry_union.py` (the registry union operation
· main as the base + extraction of the rows truly unique to base · the A1/A2/A3 assertions fail loud · `--reanchor`
the md5-8 canonical form · dry run by default). The local mapping half synchronized: the CW-side cw_paths v1.0→v1.1
(`更新账.md:3580`). Integration face: eleven `cw.sh` tools; the full suite 47 cases / 43 passing / 0 failing / 4 SKIP
(`更新账.md:3562`). `git show --stat`: 26 files · +3610/-16.

#### Work stream 2 · v36 orchestration layer (4026051)

The single-command pipeline chains the four v35 tools (`更新账.md:3591`): `tools/pushci.py` (1918 lines)
the five-stage pipeline — preflight (the doctor environment check + the net_probe stability-window check + the optional `--pre-scan-gate4` header pre-scan) → push (HTTP/1.1, three shots × 45 s → the ghproxy reroute, two shots · reroute only for the github.com form) →
resolve+watch (the head_branch + head_sha interlock · the status-only reading) → heal (the ci_triage
classification routing · B/E rerun only after the two-probe stability window [403 idempotent] capped at `--max-heal 3` · A/C stops and never repairs on the user's behalf ·
out-of-spectrum families never auto-rerun) → verdict±merge (409 re-pulls the tip, rests 60 s, retries ≤ 3) · the verdict's
seven-state register. **The orchestration added zero new engines** (all subprocess over the v35 engines); six scenarios, 15 verdicts, canned
(S1-S6 · the `--injector` two forms + `--git-caller` paired · offline, zero real network). Twelve `cw.sh` tools;
the full suite 48/44/0 failing/4 SKIP. The cross-agent collaboration precedent: the test agent escalated "implementation absent" → the orchestration agent instructed
"cast the implementation-independent pieces first + bounded polling" → the implementation landed, aligned version by version — three layers, one agent each, zero collisions
(`更新账.md:3598`). `git show --stat`: 14 files · +3916/-22.

#### Work stream 3 · v37 service layer (41e74b0)

Batch tools → a real-time dynamic service layer (`更新账.md:3615`). Three tools applied: `tools/unclog.py`
(1161 lines · the clear-blockages closed loop: probe collection → chain_graph chain roots → cure_applier applies only canonical packages →
scan_v4 + probe re-check → verdict; the honesty wall lists the reason for every root and never force-fits; dry run by default),
`tools/wash_shape.py` (the shape-normalization five-wash pipeline: word faces / tokens / headers / line endings / anchors · the plan/apply two stages
· plan writes zero to disk · frozen-roster entries refused), `tools/cw_sentinel.py` (1079 lines · the real-time watcher with three signal sources —
CI failing builds / local blockage records / build logs → the JSONL event stream · **report-only by default, zero actions**).
The five-discipline interface set runs through all three tools: JSON-in/out schema designated, exit codes 0/1/2/9 (a failing result is data, not a tool
failure), `--once`/`--loop`, `--injector`/`--sleep-scale` offline-testable, orchestration with zero new engines
(`更新账.md:3627`). Fifteen `cw.sh` tools; the full suite 51/47/0 failing/4 SKIP; README-cw gains the
"workflow cooperation interface" section. `git show --stat`: 11 files · +4011/-13.

#### Work stream 4 · v38 hookup health-check layer (c205ea0)

Hookup and health checking (`更新账.md:3645`): `tools/cw_doctor.py` (1082 lines · the four-domain aggregated health check —
environment 40 / network 20 / registry 25 / blockages 15 → health score 0-100 + advice pointing each non-passing domain at its tool ·
the real-machine full run 91.67 healthy rc=0); the cw_sentinel `--on-red-preset` hookup presets
(unclog/pushci · the dry-run-by-default invariant · mutually exclusive with `--on-red` at rc=2); the unclog `--audit`
real-tree read-only audit (the zero-write hard guarantee = all-file md5 self-verified identical before and after the run · mutually exclusive with `--apply`/`--loop`);
the resilience layer `tools/_http_backoff.py` (403/429/5xx exponential backoff · the injector path retries zero)
+ subprocess hang protection (`--timeout`/`--subproc-timeout` default 120 s) + net_probe
`--jitter`/`--seed`. Three canonical embedded blocks in examples/workflows + `docs/workflow-integration-whitepaper` v1.0 (11 bash fenced blocks, `bash -n` two rounds, 0 failures · 134 flags reconciled one by one by grep,
0 missing). Sixteen `cw.sh` tools; the full suite 52/48/0 failing/4 SKIP. `git show --stat`:
18 files · +3364/-171.

#### Work stream 5 · v39 corpus expansion (caa3a28)

The corpus expansion under gold-standard discipline (`更新账.md:3676`): `wash/cure_pack.json` v1.3→v1.4
(24→25 forms) — the three-source survey produced 11 candidates, **1 form accepted**
`cure39_ifq_connective_qualify` (the citation = the Set repository anchor commit `9a51c74`, the diff word-for-word across 25 stations · face-regex reuse, zero new
engines), **10 rejected with per-item reasons**; `tests/fixtures/header_map_v1.json` the header template library
v1 (preset=`campaign_set_diamond` · all 6 placeholders carry citations · **refusing to load without evidence, enforced in code**); `tools/doc_lint.py` the document ↔ implementation consistency three-check tool (tool table / counts / flags, three checks
· the first run drift=3 → after the main session added the netname-normalize / select-audit / doc-lint three routes,
consistent drift=0); `tests/test_relay_e2e.py` the hookup end-to-end + the docs/ops-realtime-
service runbook. Seventeen → nineteen `cw.sh` tools; the full suite 54/50/0 failing/4 SKIP; doc_lint
refs=87 drift=0. `git show --stat`: 18 files · +2962/-73.

#### Work stream 6 · v40 canonical consolidation (496ebdf)

Steady-state consolidation (`更新账.md:3706`): the cw_sentinel state crash recovery (corrupt state fails loud at 9 and refuses
· `--rebuild-state` the only legitimate rebuild path) + JSONL rotation (`--emit-max-bytes` keeps 2 generations
· seq numbering continues across generations); the unclog `--loop` seen-difference events; the wash_shape plan-cache invalidation;
`tools/baseline_diff.py` (545 lines · two audit baselines compared → new/resolved/persistent
aligned by chain root, reason by reason · **a different candidates set = incomparable, refused as recorded**); the **destructive-face review
matrix** `tests/test_destructive_matrix.py`, 17 rows of refuse-to-write criteria (negative-example injection self-attestation · caught 1
real guardrail gap — cw_sentinel plain `--on-red` without `--emit` accepted at rc=0 · the fix scheduled for
v41); the documentation close-out (the CONTRIBUTING five interface disciplines section + CHANGELOG + the docs/service-layer-
overview four-function × three-layer full map + the examples/baselines/README procedure). Twenty `cw.sh` tools;
the full suite 56/52/0 failing/4 SKIP. `git show --stat`: 16 files · +2953/-99.

#### Work stream 7 · v41 parallelism and guardrails (c5df4d4)

The parallelism and guardrail gap fixes (`更新账.md:3735`): the sentinel guardrail gap fixed — plain
`--on-red` without `--emit` → rc=2 (`cw_sentinel.py:883-886` · bypass actions must always be accompanied by the event stream persisting to disk), the matrix S2 extended to the plain+preset pair, both ways (registered in v40 → made standing in v41); the dual-door unified assessment report
docs/push-gate-dual-door-assessment (**proposal A: the two doors stand side by side, each judging its own** ·
zero code touched);
the probe_engine `--jobs K` parallel pool (default 1, serial, zero drift · **the ledger order always by candidate canonical order** ·
the thermal guard advises K≤2 · duplicate candidate names fail loud) + the unclog `--probe-parallel` pass-through + the report
timing section gains the jobs dimension (vector thirteen → fourteen); the sentinel preset registry extended (wash-shape
/triage dynamic keys / cw-doctor — three new presets + PRESET_REQUIRED_ARGS declared + the chained
`--on-red-preset` continues after one failure); the perf procedure and docs/perf-profile (four sources as measured · the DS4
K real-compile three-run profile unmeasurable → the method and a placeholder recorded, zero invented numbers). The real-tree audit baseline 27/27 RC0 red=0 entered
`examples/baselines/` (§4). The full suite 56/52/0 failing/4 SKIP + the matrix 17 verdicts all passing + doc_lint
consistent. `git show --stat`: 14 files · +1239/-154.

### §2 The active capability master table (the twenty `cw.sh` tools · the four functions × three layers, two-dimension classification)

The unified entry `bash cw.sh <tool> [args...]` (repository root · arguments and exit codes passed 1:1 ·
bash 3.2 compatible · the `cw.sh:65-82` route contract). The twenty-tool roster was measured from `cw.sh:104-153` and the
`cw.sh:207-226` route section; the three-layer assignment and the function slots follow the docs/service-layer-overview
§4 table (the v39 current state) + the per-work-stream accounts; baseline-diff (newly onboarded in v40) was positioned by this agent from the `cw.sh:60-62`
description (that account gave no function slot · noted as such). The "pre-effort foundation" = the existing v29-v32 faces (the engine surface
the effort reuses); the four functions = sanitize / shape normalization / failure diagnosis / clear blockages.

| # | route | target script | layer | function | onboarded | one-line duty (default safe state) |
|---|---|---|---|---|---|---|
| 1 | `scan4` | `scan/scan_v4_token.py` | pre-effort foundation | survey face | v29-v32 | token-level qualified-name survey |
| 2 | `cure` | `wash/cure_applier.py` | pre-effort foundation | sanitize (applier) | v29-v32 | consumer-position cure canonical package (dry run by default · v39 extends to v1.4, 25 forms total) |
| 3 | `probe` | `wash/probe_engine.py` | pre-effort foundation | probe face | v29-v32 | the batch closure-compatibility probe (v41 adds `--jobs K` parallelism · canonical-order determinism) |
| 4 | `chain` | `tools/chain_graph.py` | pre-effort foundation | clear blockages (root picking) | v29-v32 | the merged chain-root graph across accounts |
| 5 | `sync-ledger` | `tools/ledger_sync.py` | pre-effort foundation | ledger face | v29-v32 | probe ledger × state ledger merged synchronization |
| 6 | `erasure` | `verify/erasure_classifier.py` | pre-effort foundation | classification face | v29-v32 | the erasure-position classification advisor |
| 7 | `dual-scan` | `scan/dual_scan.py` | pre-effort foundation | differential-comparison face | v29-v32 | the two-scanner differential-run driver |
| 8 | `doctor` | `tools/toolchain_dyld_doctor.py` | diagnosis layer (v35) | failure diagnosis | v35 | dyld toolchain linkage-failure diagnosis (diagnosis + restore advice only · never executes) |
| 9 | `net-probe` | `tools/net_probe.py` | diagnosis layer (v35) | failure diagnosis | v35 | the network-window probe (the two-probe stability window · a single-probe round must not initiate; v38 adds `--jitter`/`--seed`) |
| 10 | `triage` | `tools/ci_triage.py` | diagnosis layer (v35) | failure diagnosis | v35 | CI failing-build triage (the five-family + passing-build classification spectrum · `--logs`/`--baseline-seconds`) |
| 11 | `union` | `tools/registry_union.py` | diagnosis layer (v35) | operation tool | v35 | the registry union operation (dry run by default · `--reanchor` the md5-8 canonical form) |
| 12 | `pushci` | `tools/pushci.py` | orchestration layer (v36) | single-command pipeline | v36 | the post-repair push-CI single-command pipeline (preflight check → push → watch → heal → verdict±merge · the seven-state register · `--dry-run` zero side effects) |
| 13 | `sentinel` | `tools/cw_sentinel.py` | service layer (v37) | failure diagnosis (real-time watcher) | v37 | the real-time dynamic watcher · three signal sources → JSONL event stream (report-only default · `--on-red-preset` five presets, chainable · v40 steady-state hardening · v41 dual guardrails) |
| 14 | `wash-shape` | `tools/wash_shape.py` | service layer (v37) | sanitize / shape normalization | v37 | the canonical-form five-wash pipeline (word faces / tokens / headers / line endings / anchors · plan defaults to zero writes · the `--header-map-preset` template library) |
| 15 | `unclog` | `tools/unclog.py` | service layer (v37) | clear blockages | v37 | the clear-blockages closed-loop engine (dry run by default · `--audit` the read-only baseline · the honesty wall never force-fits · v41 `--probe-parallel`) |
| 16 | `cw-doctor` | `tools/cw_doctor.py` | service layer (v38) | failure diagnosis (aggregated) | v38 | the comprehensive health check · four domains aggregated → health score 0-100 + advice (diagnosis only, never executes) |
| 17 | `doc-lint` | `tools/doc_lint.py` | service layer (v39) | close out (outside the four functions) | v39 | the document ↔ implementation consistency three-check (tool table / counts / flags · verdict consistent/drift) |
| 18 | `netname-normalize` | `tools/netname_normalize.py` | pre-effort foundation (the v39 entry completion) | name-normalization face | v39 | the .v.v dual-suffix name normalization (the mapping table + `--apply` rename with md5 verification) |
| 19 | `select-audit` | `tools/select_audit.py` | pre-effort foundation (the v39 entry completion) | audit face | v39 | the batch-selection auditor (the order.txt full-table grep dedup + the Require-face audit v6) |
| 20 | `baseline-diff` | `tools/baseline_diff.py` | service layer (v40) | clear blockages (blockage-record comparison close-out) | v40 | the blockage-baseline comparison (new/resolved/persistent + the four-state verdict · incomparable refused as recorded · timing excluded from the comparison) |

The two-dimension quick reading: **failure diagnosis** = doctor/net-probe/triage/sentinel/cw-doctor, five tools (the three diagnosis-layer
tools + the service-layer watcher and the aggregated health check); **sanitize / shape normalization** = cure/wash-shape, two tools (cure is the applier ·
wash_shape orchestrates the application face); **clear blockages** = chain/unclog/baseline-diff, three tools (root picking /
closed loop / comparison close-out); the close-out face doc-lint sits outside the four functions; the rest are the pre-effort foundation and the orchestration layer
(pushci spans the diagnosis, orchestration and consumer faces). The entry evolution 11→12→15→16→19→20 matches the §1 integration rows
work stream by work stream.

### §3 The precedent master table (distilled from the "precedent / wording registration" sections of the v35-v41 accounts · numbering carried over)

Each account's registration-section original numbering is carried verbatim (unnumbered registrations receive sequence numbers by order of appearance · the source anchor rides the row).

| # | source anchor | precedent / wording | distillation | later placement |
|---|---|---|---|---|
| v35-① | `更新账.md:3574` (§3) | criterion correction | the v34 account recorded t_quad8_check as "failing" — in this environment it is actually SKIP (rc=111 · the canonical four-repository copy group is not on this volume); a data failing, not introduced by this round · the two-environment difference recorded as such | the suite wording "SKIP does not count as failing", carried to this day |
| v36-① | `更新账.md:3607` (§4.1 contract-deviation registration ①) | the `--injector` two forms | the pushci `--injector` two forms (steps strict per round + the flat fixture verbatim) — the semantics not relaxed | the canonical form of the v36 six-scenario 15-verdict offline testability |
| v36-② | `更新账.md:3607` (②) | the README count face | README.md carried no tool count (the sync example-count line 43→48) | the example-count line sync rule, carried forward |
| v36-③ | `更新账.md:3607` (③) | the README snapshot face | README.md had no v35 snapshot line (the v35 work stream did not enter the main README · this round only added the in-line v36 mention) | — |
| v36-④ | `更新账.md:3607` (④) | never rewrite history | tests/README.md "47 cases registered" was the then-current statement · kept verbatim under the no-history-rewrite rule | — |
| v37-① | `更新账.md:3632` (§3) | cross-agent count drift | the watcher agent's cw.sh header count said thirteen while its usage said twelve → the integration agent unified to fifteen (cross-agent count drift · the integration close-out duty · precedent) | the written precedent that count drift belongs to the integration close-out duty |
| v37-② | `更新账.md:3633` (§3) | the injector philosophy | unclog `--injector` = "canned verification · real orchestration" — chain/cure/scan/frozen8 still really run under injection (not puppet tests) · offline testability and real orchestration coexist | the whitepaper §1 discipline ④ mechanism section, same source |
| v38-① | `更新账.md:3663` (§3 ruling registration) | same-slot mutual exclusion | `--on-red-preset` and `--on-red` together = mutually exclusive at rc=2 (the task instruction's "preset wins" vs the selftest's "mutually exclusive" tension → ruled by the repository's same-slot mutual-exclusion invariant · the boundary recorded in the docstring) | the ops manual §2.2 negative-example table, registered |
| v38-② | `更新账.md:3664` (§3) | the two clocks stay separate | the cw_sentinel `--timeout` (per-HTTP-request) and `--subproc-timeout` (the subprocess cap) are two separate things (the v37 agreed wording unchanged) | the v40 §3 continued registration |
| v39-① | `更新账.md:3693` (§3) | expansion honesty | the cure_pack v1.4 single-form expansion is the honest survey conclusion (forms without a second independent reproduction are held for survey · not an expansion shortfall) | "prefer scarcity over dilution" made code (header_map refuses to load without evidence) |
| v39-② | `更新账.md:3694` (§3) | criterion polish | the empirical correction of the doc_lint phantom / dangling citation criteria (dup ≠ superfluous · README.md:232 union-freeze --world is a legitimate multi-value) | the doc_lint criteria finalized |
| v40-① | `更新账.md:3718` (§2 matrix results) | a real guardrail gap | the destructive matrix caught cw_sentinel plain `--on-red` without `--emit` accepted at rc=0 (the real guardrail lives on the preset path · the probe run confirmed the action executes) — the negative-example injection self-attestation + a real gap caught, two proofs | **the v41 fix made standing** (the cw_sentinel.py:883-886 guard · the matrix S2 extended both ways) |
| v40-② | `更新账.md:3722` (§3) | flag-name separation | `--loop-max` and `--max-rounds` belong to unclog / sentinel respectively · no alias created (the task instruction's typo corrected as recorded · the boundary in the docstring) | — |
| v40-③ | `更新账.md:3723` (§3) | the two clocks continue | the cw_sentinel two-clock separation continues (the on-red 60 s bypass cap, the v37 agreement unchanged) | — |
| v41-① | `更新账.md:3747` (§2 cross-agent collaboration) | same-file serialization | the parallelism agent and the perf agent both edited unclog.py (the parallel layer + the timing dimension) = an incremental dimension addition on a shared base (the perf agent read the parallel layer before starting · appended without overwriting) — the zero-conflict record | a sample of the same-file two-agent collaboration method |
| v41-② | `更新账.md:3748` (§2) | generational succession | the tool-produced account's generational succession recorded as it happened: the audit baseline JSON was re-produced by the 07:12 real-compile run (the earlier rc=127 fast-fail record was overwritten) | perf-profile §1 DS1 reads the 07:12 version word for word |

### §4 The real-tree results report (the audit baseline 27/27 RC0 · the three-run history · the honesty wall's recorded refusals)

- **Subject and candidate face**: the Set repository ConstructiveWorld_Live real tree · 27 pieces = the two placement batches of November 10, 2026
  (b48-52, thirteen + b53-57, fourteen · md5 measured and backfilled into the TSV) · world = the runner workspace's
  Live APFS clone (537 vo · the active generation · the runner canonical copy untouched) (`更新账.md:3698`,
  `3727`; `examples/baselines/audit-ConstructiveWorld_Live-20261111.note.md`).
- **The three-run history** (`更新账.md:3752-3753` · the note sidecar's "comparison history" section): the first/second runs rc=127,
  tool-cause failing (the compiler absent — one more proof of the "bare coqc does not exist" invariant) · **the honesty wall refused to judge, correctly**
  ("generation-mismatch / tool-cause failing · never force-fit"); the third run, with the `--rocq-cmd` 9.3 coqc template, produced.
- **The production results**: **27/27 RC0 · red=0 · wall=0** · cures_planned=0 (the audit is read-only) ·
  verdict audit, exit 0. The timing section: manifest 1.289 s / probe_chain 190.728 s /
  total 194.086 s (the only non-deterministic section · excluded from baseline comparison). This agent read the in-tree canonical copy
  `examples/baselines/audit-ConstructiveWorld_Live-20261111.json` and it matches the numbers above item by item (args.rocq_cmd = opam93 coqc `-native-compiler no -q -Q . "" {name}.v`
  · src=ConstructiveWorld_Live · world=probe_world_v38 · injector=null).
  Evidential meaning: the two placement batches of November 10, 2026 are confirmed **all closure-compatible** in the active world generation
  (`更新账.md:3753`).
- **Archived**: the baseline JSON + the run-account note sidecar md placed in `examples/baselines/` · entered the repository with the v41 commit
  c5df4d4 (`更新账.md:3754`; the `git show --stat` of c5df4d4 lists audit-…json at 71 lines
  + the note at 7 lines). The comparator in place: baseline_diff.py produces the three delta lists from two audit baselines
  · the account self-consistency check blocks hand-written accounts (the v40 §1 ②).
- **The generational succession, recorded as it happened**: /tmp/audit_b48_b53_baseline.json had earlier been the product of an rc=127 fast-fail
  run · re-produced and overwritten by the real-compile run at 07:12 — perf-profile DS1 reads the 07:12 version, word for word
  (the `docs/perf-profile` §1 DS1 provenance note · the v41-② precedent).
- **The honesty-wall mechanism registered** (this report's recorded refusals are its first field use): the unclog honesty wall's six reasons
  self-unwashable / cure-miss / frozen-in-service / root-file-missing / exclusive-
  group-conflict / no-chain-root list the reason for every root and never force-fit (docs/ops-realtime-service
  §3.2); the audit's zero writes = all-file md5 self-verified identical before and after the run, violations fail loud at 9
  (docs/ops-realtime-service §3.1).

### §5 To-dos and the v43+ route map (summarized from each account's "boundaries and to-dos" section · deduplicated)

**Closed within the effort (to-do → placement)**: the pushci single-command pipeline (the v35 boundary.1 → landed in v36);
the sentinel `--on-red` hookup presets (the v37 boundary.3 → landed in v38); the real-tree audit live run and the baseline
archived (the v38 boundary.1 / v39 boundary.1 / v40 boundary.1 → the v41 three-run production and archive); the sentinel plain
`--on-red` guard fix + the matrix criterion made standing (the v40 boundary.2 → landed in v41); the push_gate dual-door
unified assessment (the v36 boundary.3 / v40 scheduling → v41 docs/push-gate-dual-door-assessment, proposal
A side by side · zero code touched · the v41 boundary.2 closed); this total report (the v41 boundary.3, the v42 scheduling → this face).

**Pending execution (the v43+ candidates · each with its source)**:

1. the probe `--jobs`>1 real-tree measurement (a thermal-window pending-execution item · the canned mechanism is empirically settled) — the v41
   boundary.1; the DS4 real-compile K=1/2/3 three-run placeholders await backfill into docs/perf-profile §5 (the backfill =
   perf-profile v1.1 · docs/perf-profile §6.3).
2. the pushci real CI end-to-end live run (a real push → a real build → heal · for the first run, `--dry-run` first,
   then the real shot) — the v36 boundary.2, the v38 boundary.2, the whitepaper appendix A unrun items likewise.
3. the unclog `--apply` / wash_shape `--apply` real-tree live run (fixture-level full verification · for the first run, a small `--src` subset first · the allowlist-form
   procedure docs/ops-realtime-service §3.3) —
   the v37 boundary.1.
4. the sentinel `--loop` long-resident real consumption (a workflow background bash task hanging on the JSONL stream ·
   verified with the next effort's work stream) — the v37 boundary.2.
5. the cure39 new form (cure39_ifq_connective_qualify) real-tree live run (fixture-level full verification)
   — the v39 boundary.2.
6. the 9.1 compiler dependency face, pending decision (`ROCWASH_ROCQ` habitual path MISSING · points to 9.3 CW_MAC93
   or a restored donor · the CW-side cw_paths v1.1 root-move watch table registered) — the v35 boundary.2.
7. the ci_triage `--watch` long-watch state (independent of the pushci watch embedded version) — the v36
   boundary.3.
8. the wash_shape `--header-map` template library expanding with the effort corpus — the v37 boundary.3 (the v39
   header_map_v1 founded the first library).
9. the dual-door proposal A residual risk, registered: no mechanical check forces the workflow to judge door B first (a pushci single run launches ·
   the window discipline rests on documentation and embedded-block constraints); if mechanical enforcement is ever wanted · proposal B is the only path that leaves the canonical criteria unchanged
   · but the c4 full-suite cost and the c1 new-branch first-push deadlock must be solved first — docs/push-gate-dual-
   door-assessment §5 residual risk.

**The v42 close-out total-archive work stream remainder (the v41 boundary.3 schedule)**: the three-gate final runs (`doc_lint --repo`
drift=0 / `tests/test_destructive_matrix.py` 17 verdicts all passing / `tests/run_tests.sh` the full suite
zero failing) = the integration agent's final-run wording (not rerun by this agent · see the header); the real-machine drill compilation; the v43+ route map
(this section is its draft base).

—— Submission self-attestation of that round: after the v1.0 file was written, `python3 tools/doc_lint.py --repo .` was rerun wrapped in `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120`
· verdict consistent drift=0 (including zero drift in that document's flag citations) — the measurement record is in the delivery notes.

---

## §6 The six-work-stream addendum (November 12, 2026 · v43→v48)

**The commit face** (run by this agent in this ask: `git log --oneline c5df4d4..HEAD` · oldest → newest, exactly six
commits): ffb8c82 (the v42 close-out total-archive work stream = the v1.0 base work stream · this face's §0 is its deliverable) →
459a77d (v43) → 8e124b3 (v45) → a9720ab (v46) → 6217808 (v47) → 325b4dc
(v48 · HEAD). **v44 changed zero code · no separate commit** — a pure run work stream · its account is in the repository via the `更新账.md` v44 section carried by the v45 commit
8e124b3 (`更新账.md:3814-3834`). All six work streams' material is cited from the `更新账.md`
v43-v48 sections (`更新账.md:3794-3944` · read-only distillation, the original untouched) + the in-tree faces listed above; every work stream's `git show` statistics were run by this agent.

### Work stream 8 · v43 the ad-hoc real-run measurement (459a77d · zero code changes, pure verification · route-map ④+① double close-out)

The main session mechanically executed two items (`更新账.md:3794-3810` · the `git show --stat` of 459a77d = 3 files
+103/-0):

- **④ the gated-compile arc master switch closed out**: `ROCWASH_ROCQ` points at the 9.3 multiplexer
  (`mac93_install_work/opam93/rocq93/bin/rocq` measured present) → the `tests/test_cure_pack.py`
  gated arc **TEST-CURE-PACK: PASS rc=0** (the E2 consumer-unit magic 0/0 · the world accessor debt pinned=1 · the E2/E3 fixtures compile through the whole chain on 9.3) — the missing 9.1 toolchain
  no longer blocks the gated arc · the 9.3 direct substitution is empirically viable (`更新账.md:3800`). The honest boundary: the turned-passing state is the "active
  world generation" passing · **not a 9.1 restoration** (§9 boundary 3, same source).
- **① the probe --jobs real-tree DS4 backfill closed out**: the same 27-piece candidate face (`/tmp/audit27.tsv` ·
  the ≤30-piece sample-size precedent) K=2 audit — `tools/unclog.py --audit --probe-parallel 2` probe_chain **101.916 s vs K=1 190.728 s = 1.87×** ·
  n_records=27 n_red=0 (mutually corroborating with K=1) · the timing.jobs=2 dimension field measured in the account
  (`更新账.md:3801`). Same candidate face · same world (the /tmp/probe_world_v38 APFS clone
  537 vo) · same rocq-cmd template (9.3 coqc) · wrapped in cpu_guard — every dimension identical except K =
  comparable under the baseline_diff wording (`更新账.md:3805`). The K=2 baseline archived at `examples/baselines/perf-ConstructiveWorld_Live-k2-20261111.json` (`更新账.md:3806` · the perf-profile
  §5 backfill section :157-165, same numbers · read by this agent, args.probe_parallel=2 matches item by item).
- The integration face unchanged: twenty `cw.sh` tools · the tests 56 cases, 52 passing, 0 failing · the three close-out gates all passing
  (`更新账.md:3810`).

### Work stream 9 · v44 the resident watcher's first rehearsal (no separate commit · zero code changes, pure run · route-map ② close out)

The **first field verification** of the "real-time dynamic cooperation with workflows" goal (`更新账.md:3814-3834`) —
the watcher ran the full "discovery → classification → event stream" three stages over the real repository's real history · the v37-v39 three-work-stream service-layer design
confirmed by real data feeding back (`更新账.md:3829`):

- **The command**: `python3 tools/cw_sentinel.py --loop --interval 45 --max-rounds 15 --watch-repo hy7pc8gfmf-dotcom/ConstructiveWorld-Set --state-file /tmp/sentinel_v44_state.json --emit /tmp/sentinel_v44_events.jsonl`
  (report-only default, zero actions · `更新账.md:3820`).
- **The behavior**: 15 rounds × 45 s run to completion (a 12-minute window) — **the first round triaged the whole effort history retroactively**:
  from fresh state, the Set repository's 30 historical runs were pulled and classified family by family by ci_triage
  (`更新账.md:3821`).
- **14 events**: the family distribution A-content-red ×9 / B-netred ×1 / C-toolchain-break ×1 /
  E-coqchk-skipped ×1 / UNRECOGNIZED ×2; the actions fix-content ×9 /
  rerun-after-stable-window ×2 / restore-toolchain ×1 / watch-only ×2
  (`更新账.md:3822`).
- **The classification agreement (the core verification)**: #280 → A (the stale foundation of the uab_ssUnit era) ✓ · #283 → C
  (the dyld linkage-failure day) ✓ · #289 → E (the upload DNS window) ✓ · #286 cancelled → B-netred by the group-cancel coupling +
  UNRECOGNIZED side by side, no forced spectrum fit ✓ — the classifications match the six-act drill of November 10, 2026 item by item
  (`更新账.md:3823`).
- **Idempotence**: rounds 2-15 produced zero duplicate events (the state seen in effect) = the long-resident steady-state proof
  (`更新账.md:3824`).

### Work stream 10 · v45 the render_events ledger renderer (8e124b3)

- **`tools/render_events.py`** (547 lines · the `git show --stat` of 8e124b3, run by this agent = 3
  files +601/-3): the watcher-event JSONL → markdown ledger renderer — the `--events`/`--dir`
  merge (sorted by seq+ts) → the kind/family/action three-dimension distribution + the 9-column per-event table (bad-line tolerance
  rc1 · unknown kinds filed as other · pipe escaping) + the `--json` summary
  (rocqwash-render-events/1) + the `--top` truncation (`更新账.md:3844`). Self-attestation:
  the selftest seven vectors rc=0 + **a real watcher-output render assertion** (the v44 14 events · the family
  A=9/B=1/C=1/E=1/UNREC=2 recomputed independently, all correct · the two runs byte-identical — `更新账.md:3844`).
- **The integration**: twenty-one `cw.sh` routes (the render-events hookup synced in six places · anchored on the two earlier failures = the v40
  baseline-diff insertion reorder · re-anchored on the actual text, closed out in three shots); the doc_lint VERDICT consistent
  drift=0 (refs=87) (`更新账.md:3845`).
- The eight-work-stream overall wrap-up (v35-v45): nine commits all reconciled by ls-remote · route-map ②③④①⑧
  closed out · ⑤⑥⑦ pending execution (`更新账.md:3853`).

### Work stream 11 · v46 red_dispatch + registry_audit + the push_gate unified evaluation (a9720ab · route-map ③ substantively closed)

Three agents cast together + the integration agent closed out (`更新账.md:3857-3884` · the `git show --stat` of a9720ab, run by this agent
= 12 files +2522/-15). The generation note: this work stream's task instruction was cast on the v37 baseline · at application time the actual state was already v45
8e124b3 — the integration agent surveyed and **applied the v46 current-state wording** (23 tools / 58 cases · `更新账.md:3859`);
the two new tools are exactly the substantive advance of the v45 route-map pending-execution face: red_dispatch = the productization of the pending-execution ③ hookup gatekeeping ·
registry_audit = the safety precondition for real-repository live runs (`更新账.md:3859`/`:3877`).

- **`tools/red_dispatch.py` (~760 lines), the red-event router** (`更新账.md:3865`):
  the sentinel event JSONL → five-family routing (B/E → pushci re-route / A → manual-fix-note, never repaired on the user's behalf, produces the fix list / C → doctor / blocking → unclog application only with explicit human review / build-signal →
  wash-shape) + D/UNRECOGNIZED → watch-only; the three `--preset` tiers (report-only
  default / suggest / auto, explicit) · validate-all-then-execute, zero half-executed batches ·
  `--state-file` dedup + `--cooldown` 600 · three-tier parameter resolution · a shell metacharacter guard against injection.
  Self-attestation: `--selftest` rc=0, 36 verdicts over 12 vectors + a live smoke (the auto-marked file verified · the second run
  cooldown skipped=1).
- **`tools/registry_audit.py`, the registry hygiene auditor** (the read-only invariant · zero writes · the application face
  is carried by registry-fix — `更新账.md:3866`): the four audit checks = duplicate rows/anchors (text collisions · sequence-number shapes
  · odd shapes · missing anchors · the canonical #R<seq>-<md5-8>) / two-way orphans / topology references (the `--live-src` real-piece
  reconcile); `--fix-plan` emits only deterministic prescriptions (DEDUP keeps the first / the anchor refresh goes straight through the registry_union
  engine / ORPHAN-ADD templates / colliding anchors listed unresolvable). Self-attestation: `--selftest` rc=0, five verdicts
  (a v35 real-account specimen, 19 defects inventoried exactly · the md5 frozen vector 77c2b9a8 embedded · the read-only md5
  identical) + **a real-repository read-only demo**: the Set Live authority pair duplicates=12 (the `_CoqProject` tail region
  L492-515 word-for-word duplicate block · the #40 direct-merge family verified) anchors=523 (6 anchor collisions, exactly the v35 precedent's originals).
- **`docs/评估-push_gate推窗四判据与pushcinormalize-20261111.md`** (`更新账.md:3867`):
  the push-window four criteria (c1 ci-idle / c2 behind=0 / c3 fetch-clean / c4 cert-green · the judgment order
  c3→c1→c2→c4 · judges the window only, never opens the push) versus the pushci preflight three checks, item by item — **zero overlap across the 7 criterion faces
  · the two doors zero interconnection** (grep-verified); three proposals: the first adds a fourth preflight check (the c1 evidence deadlock
  + the c4>120 s two mountains → not recommended) · **the second keeps the two doors + divides the documentation (recommended)** · the third sinks the criteria into library
  functions (touches deep certify pieces → rejected); push_gate is not frozen (frozen8.py:74-83 measured eight pieces
  without it · nonfrozen-mutable). Side by side with the v41 earlier-agent document (the push-gate-dual-door-assessment
  v1.0 proposals A/B/C), same-verdict corroboration · the two documents coexist unmerged, both on file (`更新账.md:3884`).
- **The integration face + the cap-value generation change** (`更新账.md:3868`): twenty-three `cw.sh` tools (the route/audit
  two routes) · run_tests.sh 58 cases · **doc_lint DEFAULT_HELP_CAP 20→24** (the integration agent
  registered the cap overflow for cure_applier/probe_engine → the main session ruled the generation change · pre-registered at the v38 work stream's point in time);
  self-attestation: run_tests.sh 58 cases / 54 passing / 0 failing / 4 SKIP, two runs EXIT 0 · doc_lint
  --help-cap 24 VERDICT consistent drift=0.

### Work stream 12 · v47 ⑧ closed + the watcher's first real-repository field run + the registry_fix executor (6217808 · route-map ⑧ formally closed)

Three agents cast together + the integration agent closed out (`更新账.md:3888-3915` · the `git show --stat` of 6217808, run by this agent
= 7 files +1325/-16):

- **⑧ proposal A executed to completion = the gated-compile arc master switch turned passing** (`更新账.md:3894`): the tests/
  run_tests.sh master-switch section probes four paths by default (if the `ROCWASH_ROCQ` env is set it is honored → the 9.3 multiplex-
  er existing is exported · the other three paths point at the Set repository gate7/gate6 canonical copies and the BORN world rocq) —
  the gated arc's four positions turned passing (the t_cure_pack compile check section / the t_probe_engine real rocq node /
  the two run_tests case sets · **criterion semantics changed zero · flipped through the default face**) + **the three CANON cases turned passing beyond the task instruction**
  (t_gate7_wrapper 13/13 · t_verify_gate6 five verdicts · t_gate6_born_wrapper
  21/21 · the passing proof landed before the default) · the cure-pack compile arc PASS through the whole chain (the v43 27/27 same-source precedent
  reproduced). **SKIP 4→1** · only t_quad8_check remains = the CANON_W1 four-repository copy group's missing-volume family · unrelated to
  the gate, recorded as such (`更新账.md:3897`/`:3914` · §8 item 4, same source).
- **The watcher's first real-repository field run, 33 events** (`更新账.md:3895`): the cw_sentinel dual-repository `--once`
  (Set 30 runs / 15 failing · Main 30/18) → **33 events** (A19/UNREC8/E3/B2/C1 —
  the two B-netred ×2 exactly interlock with the known NETRED failing builds Set#269/Main#22 = the classification ground-truth reconciliation) ·
  the 25 passing runs silently recorded as seen = passing is also a real observation · the second run idempotent, zero new events (one
  watcher long-watch flag-name face corrected → the real flag `--max-rounds` recorded as it is); the JSONL 33 lines, all legal line by line · the schema
  rocqwash-sentinel-event/1 · seq increasing · the state seen 30/30 interlocked. The UNREC8 await human
  review = the classification spectrum's "no forced fit" honesty by design (§9 boundary 2).
- **`tools/registry_fix.py` (1161 lines), the audit-prescription executor** (the v46 to-do item 2 fulfilled ·
  the hygiene loop closes audit→fix in four steps · `更新账.md:3896`): DEDUP keeps the first (the audit's original line numbers are for the
  post-mortem) / the anchor refresh (the registry_union.apply_reanchor same form · missing real pieces skip · MD5-DRIFT
  fails loud) / ORPHAN / missing-anchor / unresolvable → skip as recorded (anchors never fabricated mechanically); the three assertions (the treated keys'
  duplicates=0 / anchor collisions zero new, the A3 engine / orphans not increased) · any failure = exit 2 + **a byte-for-byte rollback**
  · dry run by default, zero writes (not even the work dir is created). Self-attestation: `--selftest` 8/8 rc=0 (
  the `--apply` 12 duplicate blocks → 0 + 77c2b9a8 same input, same output byte-for-byte = the registry_union CLI same-argument
  product · the artificial failure point rollback · the natural failure point A3 · application determinism).
- **The integration face** (`更新账.md:3897`): twenty-four `cw.sh` tools (registry-fix synced in six places) ·
  run_tests.sh +57/-6 (the master-switch section + the t_registry_fix case) · **59 cases / 58 passing / 0 failing/
  1 SKIP**, twice · doc_lint consistent · all twenty-four `cw.sh` tools present.
- The registry_fix real-tree application pending-execution item: the Set Live dual-ledger 12 duplicate blocks + the anchor-refresh prescription are already on file — the real-tree
  application touches a multi-writer repository (the `曾栢源` work line / on-duty agents active) · awaiting a user instruction or a coordinator cross-check
  (`更新账.md:3908` · §8 item 1, same source).

### Work stream 13 · v48 the ⑦ assessment grading + the DS4 three-account close-out + the watcher manual + the watcher's resident real deployment (325b4dc · all eight route-map candidates closed)

Three agents + the integration agent + the main session (`更新账.md:3918-3944` · the `git show --stat` of 325b4dc, run by this agent
= 6 files +749/-5 · **no cw.sh = zero new tools**):

- **⑦ the multi-repository adaptation assessment** `docs/勘形-multi-repo-Main仓适配-20261112.md` (read-only, zero code changes ·
  `更新账.md:3924`): the Main CI measured three key points (the active workflow is only coq93.yml, a 9.3 single Windows job ·
  the mac observation job omitted [`coq93.yml:32-33`] · checkout=v5, not the API tarball ·
  concurrency single group cancel-in-progress [the heal-rerun group-cancel face] · the push allowlist
  [main]) → **the graded verdict = use as-is 4 / minor changes 3 / medium changes 2** (the assessment document §4/:184-198):
  the largest gap = the pushci PR-path mirror-blind double mismatch (the PR run head_sha=merge commit
  ≠ the pushed tip · `coq93.yml:41-42` vs `tools/pushci.py:942-944`) + the unclog Main Live
  canonical copy unusable (the two medium changes); the five-step recommended path (retro-triage zero code → fixtures minor changes →
  `--dry-run` → the push-main real shot → the unclog canonical copy independently scheduled · the assessment document §5/:202-217).
  The API-measured coq93.yml 606-line full text · the selftest run rc=0 (the assessment document §7/:233-241).
- **① the DS4 K=3 real-run close-out** (`更新账.md:3925`): `examples/baselines/audit-k3-20261112.json` the real-tree blockage baseline archived — 27/27 RC0 · probe_chain_s=165.202 · the three accounts
  cross-checked against the reference **K1=190.728/K2=101.916 (1.87×)/K3=165.202 = K3 slower than K2 by 1.62× = the
  negative marginal speedup recorded as measured** (the current machine has 4 CPUs · the K=2 tier is the inflection point · the DS4 discipline forbids inventing numbers and forbids force-fitting passing)
  · the full thermal account (FRONT · tlevel 58→60 · no thermal clamping · the contention note: during the run another agent's
  nice-19 coqchk over 17 pieces was in flight) · the baseline_diff two-way verdict=stable, the quadruple identical =
  comparable. This agent read the account: timing.jobs=3/probe_chain_s=165.202/total_s=
  169.684/n_records=27/n_red=0 match item by item; the perf-profile §5 backfill section's three real-number
  rows (:120-127/:167-174). **Route-map ① the DS4 three accounts complete, formally closed out — the roadmap's eight candidates
  all closed** (②③④①⑧ closed + ⑤⑥ the gold-standard skip + ⑦ the assessment landed with grading · `更新账.md:3936`).
- **The resident-watcher operations manual** `docs/ops-sentinel-长驻手册-v1.0-20261112.md` (`更新账.md:3926`): four sections — deployment [placed outside the repository on the CW side `_log` · the nohup/background two forms] / usage [the event
  schema + render_events + the red_dispatch pairing + the `--once` embedded-block three use forms] / rotation and recovery
  [the `cw_sentinel.py:136` crash-recovery precedent + the 2-generation rotation + seen prefers duplication over loss] / the measurement account
  [the v44 14 events + the v47 first field run's 33 events + the v48 placement state]. 81 direct file:line citations ·
  8 citation anchors reconciled line by line by sed · doc_lint refs=114 drift=0.
- **The resident watcher really deployed** (the main session · `更新账.md:3942`): the background exec_1b6e50d4 · dual repositories ·
  a 10-minute inspection interval · the CW-side `_log/sentinel_v48/` three-file set placed — this work stream's manual is its operations canonical copy.
  **This agent read the live state in this ask** (`ls`/`wc -l`/python3 measured): the three-file set exists —
  events.jsonl 33 lines · report.json (mode loop · interval 600.0 s · round 5 · the dual-repository
  ci source runs_seen=30/30 · round 5 zero new events = the post-deployment idempotence on record) · state.json.
  The event histogram A18/B2/C1/E4/UNREC8 = 33 — a two-point drift against the v47 first-run account (A19/UNREC8/E3/B2/C1), recorded as such
  (§9 boundary 7).
- **The integration face** (`更新账.md:3927`): the README.md v48 snapshot + the docs list registration + the DS4 three-account
  baseline_diff two-way rerun rc=0 (run by the integration agent); run_tests 59/58/0 failing/1 SKIP
  run twice as instructed · doc_lint consistent (cap 24, no overflow).
- The boundaries carried honestly: the K=3 single-run reading is trend-level (§9 boundary 1) · the account name `audit-k3-20261112.json`
  departs from the perf naming rule (the quadruple embedded identical · the measuring agent's note kept · `更新账.md:3944` · §9
  boundary 6); the ⑦ execution path's current state = steps 1-3 (retro-triage zero code / fixtures minor changes /
  `--dry-run`) = the v49 face · step 4, the real shot, awaits instruction · step 5 independently scheduled (`更新账.md:3937` · §8
  item 2, same source).

### 6.x The v1.0 §5 nine pending-execution items → the six-work-stream close-out reconciliation (each with its source)

| # | v1.0 §5 pending execution | the six-work-stream placement | state |
|---|---|---|---|
| 1 | the probe `--jobs`>1 real-tree measurement | the v43 K=2 1.87× (`更新账.md:3801`) + the v48 K=3 three accounts complete (`:3925`) | **closed** |
| 2 | the pushci real CI end-to-end live run | the ⑦ assessment's five-step path stands · steps 1-3 = the v49 face · step 4, the real shot, awaits instruction (the assessment document §5/:202-217 · `更新账.md:3937`) | pending execution (§8 item 2) |
| 3 | the unclog/wash_shape real-tree `--apply` live run | not run (fixture-level full verification maintained) — outside the task instruction's four pending-execution items · recorded honestly in §9 boundary 5 | unmet |
| 4 | the sentinel `--loop` long-resident real consumption | the v44 first rehearsal + the v47 first field run + the v48 real deployment (`更新账.md:3820`/`:3895`/`:3942`) | **closed** |
| 5 | the cure39 new form real-tree live run | not run · the ⑤⑥ corpus-trigger family bundled in the same window (§8 item 3) | pending execution |
| 6 | the 9.1 compiler dependency face | the v43 ④ close-out (the 9.3 direct substitution · `:3800`) + the v47 ⑧ closure (default probing · `:3894`) | **closed** |
| 7 | the ci_triage independent long-watch state | not done (still absent beyond the pushci watch embedded version) · §9 boundary 5 | unmet |
| 8 | the header-map template library expansion | the ⑤ corpus trigger awaits instruction (roadmap-v43-plus:62 · §8 item 3) | pending execution |
| 9 | the dual-door proposal A residual risk | the v46 evaluation document's second-proposal same-verdict corroboration (keep the two doors + divide the documentation · `更新账.md:3867`/`:3884`) — mechanical enforcement still absent · proposal B's precondition mountains unmoved | same-verdict corroboration · not closed |

## §7 The count master table and the active-capability master table addendum

### 7.1 The count master table (three rows · the v42 base → the v48 current state · all transcribed from the ledger sections and re-checked by this agent)

| count face | v42 base (the v1.0 point in time) | v43/v44 (zero code changes) | v45 | v46 | v47 | v48 current state |
|---|---|---|---|---|---|---|
| cw.sh entry tools | 20 | 20 | 21 | 23 | 24 | **24** |
| run_tests.sh cases | 56 | 56 | 56 | 58 | 59 | **59** |
| passing / failing / SKIP | 52/0/4 | 52/0/4 | 52/0/4 | 54/0/4 | 58/0/1 | **58/0/1** |

The source anchors: the v42/v43 base twenty tools and 56 cases (`更新账.md:3810`) · the v45 twenty-one routes
(`:3845`/`:3853`) · the v46 twenty-three tools and 58/54/0/4 (`:3868`) · the v47 twenty-four tools and
59/58/0/1 (`:3897`) · the v48 current state 59/58/0/1 run twice as instructed (`:3927`). The tool-count current state, re-checked by this agent
= the `cw.sh:247-270` case routing counts exactly twenty-four routes + the `git show --stat` of 325b4dc, six files without
cw.sh (v48 zero new tools · run by this agent).

**The task-instruction given-shape correction registration**: the task instruction's "23→24→25 tool-count evolution" end disagrees with the measurement — measured
23 (v46) → 24 (v47) → **24 (v48, zero new tools)**; recorded as measured (the assessment document
§1.3, same rule · the v35-① criterion-correction precedent, same kind); "25" has no in-tree anchor · no account invented.

### 7.2 The active-capability master table addendum (tools 21-24 · continuing the §2 table after row 20 · the layer/function two dimensions carried over from §2)

| # | route | target script | layer | function | onboarded | one-line duty (default safe state) |
|---|---|---|---|---|---|---|
| 21 | `render-events` | `tools/render_events.py` | service layer (v45) | close out (ledger rendering) | v45 | the watcher-event JSONL → markdown ledger (the `--events`/`--dir` merge, the three-dimension distribution + the 9-column table · bad-line tolerance · the `--json` summary · the `--top` truncation) |
| 22 | `dispatch` | `tools/red_dispatch.py` | service layer (v46) | failure diagnosis (red-event routing) | v46 | the red-event → action-preset routing (the `--preset` three tiers, report-only default · `--state-file` dedup + `--cooldown` · the metacharacter guard · zero half-executed batches) |
| 23 | `audit` | `tools/registry_audit.py` | service layer (v46) | operation tool (read-only audit) | v46 | the registry hygiene audit, four checks (read-only, zero writes · the `--fix-plan` deterministic prescriptions · the `--live-src` topology reconciliation) |
| 24 | `registry-fix` | `tools/registry_fix.py` | service layer (v47) | operation tool (prescription execution) | v47 | applies the audit fix-plan item by item (dry run by default · the three assertions after `--apply` · any failure rolls back byte-for-byte) |

The two-dimension quick reading addendum (continuing §2): the **close out** face gains render-events (ledger rendering · joining the doc-lint
close-out slot); the **failure diagnosis** face gains route (watcher red → action routing · joining the sentinel consumer face);
the **operation tool** chain becomes three stages = union (the v35 write operation · dry run by default) → audit (the v46 read-only diagnosis) →
registry-fix (the v47 prescription execution) — the "diagnosis → prescription → apply" closed loop · the application face dry run by default +
explicit human-review release, one invariant guarded by all three tools. The entry evolution 20→21→23→24 matches the §6 integration rows work stream by work stream
(v48 zero new tools · the current state is 24).

## §8 The pending-execution face list (v49+ · four items · each with its source)

1. **the registry_fix real-tree `--apply`** — `tools/registry_fix.py` applies the Set Live dual-ledger
   12 duplicate blocks + the anchor-refresh prescription (the v46 real-repository read-only demo located the defects · `更新账.md:3866`; the v47
   executor selftest 8/8 including the byte-for-byte rollback · `:3896`); the real-tree application touches a multi-writer repository (the `曾栢源` work line /
   on-duty agents active) · awaiting a user instruction or a coordinator cross-check (`更新账.md:3908`/`:3941`). The first run carries the
   §5 rule: a small face first · the three assertions + the rollback guardrail are in the tool.
2. **⑦ step 4, the real shot (the pushci push-event route)** — `tools/pushci.py` the push-event route
   (refs/heads/main) + the `--watch-max-rounds` safety valve + the heal routed Main cross-check against the reference ·
   avoiding the PR mirror-blind face (the assessment document §5.4/:212-213 · `更新账.md:3937` "step 4, the real shot,
   pending execution"); the precondition = steps 1-3 (the Main retro-triage zero code / the pushci_scenarios six-scenario
   Main-repository-form fixture minor changes / the real-repository `--dry-run` plan face with zero side effects) = the v49 face · and the
   Main local checkout must be materialized first (the assessment document §5.3/:210-211); the credential face is verified (netrc
   push_perm=True · the assessment document §1.1/:20) · the Main branch-protection face to be probed before the real shot
   (the assessment document §5.6/:217).
3. **the ⑤⑥ corpus triggers** — the ⑤ wash_shape header-map template library expansion + the ⑥ cure_pack v1.5
   (the notation-rebinding second independent reproduction promoted) + the v1.0 §5 item 5 cure39 real-tree live run in the same window: the gold standard forbids force-fitting ·
   "no corpus, no work" is a design decision, not a deferral (`docs/roadmap-v43-plus-20261111.md:62`/`:72`/
   `:117`/`:131` · `更新账.md:3878`/`:3907`/`:3936`) — the window rides the ② resident-watcher real-deployment active state
   (§6 work stream 13).
4. **the t_quad8 four-repository re-scan** — the t_quad8_check recovery condition = the four-repository copy group (the CANON_W1
   S-line Prop-clearance effort instruction directory) re-scanned · awaiting a desktop-tidying review-and-delete ruling (`更新账.md:3914`);
   the 1 SKIP case is a missing-volume family, not a tool failing · unrelated to the gate, recorded as such (`更新账.md:3897`).

## §9 The honest boundaries (each with its source · new in v2.0)

1. **The K3 single-run reading is trend-level** — the K=3 real run was not resampled · the noise band not yet produced (`examples/baselines/perf-README.md` §3 judgment rule 1 "a single run draws no conclusion" :54) · the negative-margin reading
   (K3 slower than K2 by 1.62× · the K=2 tier is the inflection point) is a single-run trend-level conclusion, not a final ruling
   (`更新账.md:3943` · `docs/perf-profile-v1.0-20261111.md:172` "a single-run reading · rule 1 ·
   the noise band without resampling = trend level").
2. **The watcher's 8 UNRECOGNIZED events await human review** — of the v47 real-repository first field run's 33 events,
   UNREC8 (`更新账.md:3895`) · the classification spectrum's "no forced fit" honesty by design: the Main step names' zero-hit faces
   (the gate1/gate3 forms) fall to the UNRECOGNIZED fallback · loud but never misjudging · human designation takes precedence
   (the `tools/ci_triage.py:22-23` classification-spectrum note · the assessment document §3.1/:101-102/:108-109);
   the v44 first rehearsal's UNREC ×2, same rule (`更新账.md:3822`).
3. **The turned-passing state is the "active world generation" passing · not a 9.1 restoration** — the v43 ④ close-out / the v47 ⑧ closure, same wording,
   honestly bounded (`更新账.md:3800`/`:3894` · roadmap-v43-plus:58); the 9.1 restoration awaits a donor
   restoration (`tools/toolchain_dyld_doctor.py` the `--donor` tracing procedure in tree · never executes,
   recommendations only).
4. **The pushci PR-path mirror-blind = the largest medium-change gap** — the PR run head_sha=merge
   commit must mismatch + refs/pull/* not mirrored + the push allowlist [main] zero topic triggers
   (the assessment document §3.2/:122-133 · §4 table #8/:195); changing the tool's watch semantics or standing a procedure, two tracks ·
   neither done (as recorded). The unclog Main Live canonical copy unusable = the other medium change (no local checkout +
   the Live world has no CI production line + the candidate face needs new sampling + the baseline domain same-name conflict breaks the generation · the assessment document
   §3.3/:151-164).
5. **The v1.0 §5 pending-execution items 3/7 unmet** — the unclog/wash_shape real-tree application live runs and the ci_triage
   independent long-watch state untouched through the six work streams (the §6.x reconciliation table) · outside the task instruction's four pending-execution items · recorded honestly, never claimed closed.
6. **The account-name departure note** — `examples/baselines/audit-k3-20261112.json` departs from
   the perf-README §2 naming rule's native form (perf-<domain>-k3-*.json) · the quadruple embedded identical ·
   the baseline_diff two-way measurement mispaired nothing · the measuring agent's note kept (`更新账.md:3944` ·
   perf-profile:174).
7. **The classification histogram drifts between the two observation points** — the v47 first-run account (`更新账.md:3895`) A19/UNREC8/E3/
   B2/C1 vs the v48 deployment live state (read by this agent in this ask: `_log/sentinel_v48/events.jsonl`)
   A18/B2/C1/E4/UNREC8: the total red 33 constant · A and E each drifted 1 event = the CI history window's natural rolling drift
   (the E-family signature of upload failings + coqchk skipped forms as the window moves) · both observations are true values · recorded side by side as such,
   no account rewritten.
8. **The assessment's unexplored faces** — the Main branch-protection face / the API rate-limit current value / scripts/
   parallel_chk.sh contents / the pushci runs pagination condition (not a condition under low-frequency rotation) all unexplored
   (the assessment document §6.2/:226-227); the "score quiet window" zero in-tree anchor hits, carried honestly
   (roadmap-v43-plus:13).
9. **The v46 evaluation documents coexist as two copies** — the earlier agent's proposals ABC (push-gate-dual-door-assessment-
   v1.0) + the v46 comparison table (`评估-push_gate推窗四判据与pushcinormalize`) same-verdict corroboration ·
   unmerged, both on file (`更新账.md:3884`).

---

—— Submission self-attestation of this face: after this file was rewritten, `python3 tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash` was rerun wrapped in `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120`
· FAIL-LOUD rc=9 — `tools/selfevolve_round.py --help` timed out (> 60 s), an in-flight edit by concurrent work in the shared tree (git status: modified; a direct probe of that face's `--help` hangs independent of doc_lint), not caused by this documentation-only edit; the checks that completed before the fail-loud (tool_table 4 checks, unrouted none; count CASES=86, 5 checks) reported no drift; the flag check did not complete, so this document's zero-drift verification is carried as not completed this round, never as passing.
