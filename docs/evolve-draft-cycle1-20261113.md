# evolve-draft-cycle1-20261113.md — autonomous-evolution engine, cycle-1 candidate task-book drafts (harvest → derive → draft only).
>
> **EvolveDraftCycle1**: the five graded candidates the engine derived from three real signal sources in its first demonstration cycle, each carrying its producing-signal evidence, its verbatim prescription commands, and its execution lane. This file is a draft face: every execution step in it stays with the human reviewer — the autonomous-execution gate is not closed by this document.
>
> Purpose.  Turn the cycle-1 signal harvest (annotation-lint tree account, dual-repository CI sentinel round, registry audit at the Set mainline tip) into exactly five candidates with mechanical grading (P0/P1/P2), expected fitness deltas counted from the recorded account, and acceptance checks — so the next cycle can execute against named, evidence-anchored work items instead of narrated intentions.
>
> Interface.  Companion record: `docs/演示-evolve首轮-20261113.md` (the three-section signal/candidate/draft account and the engine verdict). Commands cited verbatim from the owning tools `tools/norm_lint.py`, `tools/cw_sentinel.py`, `tools/registry_audit.py`, `tools/registry_fix.py`, `tools/ci_triage.py`, routed through `cw.sh`; every run wrapped by `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120 --`. Working artifacts of this cycle live under `/tmp/evolve_c1/`.
>
> Dependencies.  rocqwash tree `23943e8` (v54, clean at capture time); baseline account `docs/norm-lint-baseline-20261113.json`; Set remote tip `0d58903b2110f259fd6cc3b4f77c3ca06342a49e`; the isolation protocol `docs/contrib-isolation-protocol-v1.0-20261113.md` (lane discipline, fetch-first, dry-run defaults); Python 3 stdlib-only tools.
>
> Evidence.  Each candidate's producing-signal line (command, rc, key output) is recorded in the companion document §1; every expected delta is counted mechanically from `/tmp/evolve_c1/normlint_now.json` against `docs/norm-lint-baseline-20261113.json`, not estimated.
>
> Exit-codes.  No new exit codes — this is a prose draft face. The cited tools keep their implemented semantics (`norm_lint` 0/1/2/9 report-only, `registry_audit` 0 with findings as data / 2 usage / 9 missing input, `registry_fix` 0/1/2/9 dry-run by default, `ci_triage` 0 with outcomes as data).

## 0. Grading criteria (mechanical, applied to this cycle's signals)

- **P0** — the audited core-lane tip itself is red on CI (`fix-content` action at the same sha the registry audit read): every downstream derive/integrate step inherits a red base; diagnose first.
- **P1** — a deterministic prescription already exists and its executor is in-repo (registry hygiene), or the block is a curable-error face count ≥ 50 with an established cure lane (translation replacement under the annotation card).
- **P2** — a tooling or metric improvement whose design needs a reviewer decision before implementation.
- Every candidate records: producing signal (S1 = lint account, S2 = sentinel round, S3 = registry audit), evidence (verbatim numbers), lane (engine drafts / human executes), frozen-surface touch (none in all five), expected fitness delta.

## 1. C1 (P0) — diagnose the Set mainline tip content-red

- **Source**: S2, sentinel round 1, event seq 6.
- **Evidence**: event `{"kind":"ci-red","repo":"hy7pc8gfmf-dotcom/ConstructiveWorld-Set","run_number":310,"run":43275862117,"sha":"0d58903b2110f259fd6cc3b4f77c3ca06342a49e","family":"A-content-red","action":"fix-content","evidence":["红件 1/2：ids=[131383951644]"` — the sha equals the tip the S3 audit read (`origin/main` = `0d58903b`), so the mainline head commit is red while the books on it are being prescribed against. A second A-content-red sits at Set run_number 294 and one at Main run_number 53; family counts this round: A×3, D×3, E×2, C×1, UNRECOGNIZED×1.
- **Routing**: `tools/red_dispatch.py` maps ci-red+A to the manual-fix-note route — content repair is human-only, zero commands executed on the engine's behalf.
- **Drafted diagnosis step (human runs)**:
  ```
  python3 -B tools/ci_triage.py --repo hy7pc8gfmf-dotcom/ConstructiveWorld-Set --run 43275862117 --logs --json /tmp/evolve_c1/triage_310.json
  ```
- **Acceptance**: the triage report names the failing step and the concrete content token (`Error:` / `FAIL` / `ORDER-MISSING` / nonzero `COQCHK_EXIT`); a fix owner can be assigned from it; a follow-up sentinel round shows the Set red-run count dropping.
- **Risk**: none — read-only diagnosis; the fix itself is outside engine scope by the manual-fix-note route.

## 2. C2 (P1) — apply the mechanically safe registry prescriptions at the Set tip

- **Source**: S3, `tools/registry_audit.py --git` at `origin/main` (rc=0, findings as data).
- **Evidence**: findings total 564 = duplicates 12 (all `dup-coqproject`) + anchors 549 (`anchor-collision` 8, `anchor-malformed` 525, `anchor-seq-form` 16) + orphans 3 (`orphan-order-only`: `Arch_GibbsA_01` order L553, `EntropyMonoSplitInst` L554, `UpAblT13c_G13` L495) + live topology 0 (every book key resolves on the tip tree; no `.v` on disk lacks a book row). `fix_plan` = {dedup 12, orphan 3, reanchor 541, unresolvable 0}. Cross-reference: the v54 PR48 field check measured the identical 12/549/3/0 at the PR-head ref `34ce83d` — the residue is pre-existing registered debt (cross-repo decision demands), not merge-introduced.
- **Scope decision (this draft's prescription)**: apply only the mechanically safe set — dedup 12 (keep-first on the duplicated `_CoqProject` lines) + orphan 3 (ORPHAN-ADD module lines into `_CoqProject`; direction is order-only, so no registered sequence number is needed). The reanchor 541 set stays deferred to the registered cross-repo decision: re-stamping rewrites sequence-registered rows and the v54 account registered that residue as a decision demand, not mechanical work.
- **Stale-lane guard (real state observed this cycle)**: the local Set working lane sits at `bd8f38b`, behind the audited tip `0d58903b`. Tip-derived prescriptions must never be applied to stale books — the precondition is a lane update to the tip (the ghproxy-route fetch of `main` is already done; the working-lane fast-forward is the human's move) or a fresh work tree at the tip.
- **Drafted commands (human runs; dry run first, zero writes)**:
  ```
  python3 -B tools/registry_audit.py --git /Users/apple/Desktop/ConstructiveWorld-Set --ref origin/main --git-path-order ConstructiveWorld_Live/order.txt --git-path-project ConstructiveWorld_Live/_CoqProject --live-src <tip-tree> --anchor-src <tip-tree> --fix-plan --json regen-audit.json --md regen-audit.md
  python3 -B tools/registry_fix.py --audit-json regen-audit.json --order ConstructiveWorld_Live/order.txt --project ConstructiveWorld_Live/_CoqProject --anchor-src <tip-tree> --json regen-fix-report.json
  ```
  (step 1 already executed this cycle — its output is `/tmp/evolve_c1/set_audit.json`; step 2 as shown is a dry run; the human adds `--apply --work-dir <dir>` only after review. The tool's three post-apply assertions and per-byte rollback are its implemented semantics.)
- **Acceptance**: re-running step 1 after the apply shows duplicates 12→0 and orphans 3→0 with live topology still 0; all three assertions pass; the 12 dedup keys are exactly the audit's list (`Arch_UpAbl_01`, `DenPosGeneral`, `RMaxSwap`, `abl_redischarge_sumd_inst`, `tlw1729_negform`, `u5c_dm_escape_discharge`, `u5c_inst_e`, `u5c_inst_sqrt2`, `u5c_inst_sqrt3`, `uabd_supply_S05_Z_align_pos_unit`, `uabd_supply_S08_kl_term_equiv`, `uabda_g13_evict_discharge`); C1's diagnosis is not blocked by registry work.
- **Risk**: registry books of the serviced repository — writes happen only under `--apply`, guarded by assertions and rollback; no frozen surface is touched.

## 3. C3 (P1) — core-four tools: header form + long-tail translation replacement

- **Source**: S1 (per-file error ranking) + the v53 boundary item that named exactly these four tools as the recursive queue.
- **Evidence**: `tools/ci_triage.py` 19 error faces (header 5, budget 1, jargon 14, forbidden 9, cjk 1), `tools/unclog.py` 16, `tools/cw_sentinel.py` 14, `tools/pushci.py` 7 — 56 error faces total, of which 24 are the header-form face (all five field names missing at the period-spelled form `Purpose.` `Interface.` `Dependencies.` `Evidence.` `Exit-codes.`, plus the 30-line header budget). Top jargon terms per tool: ci_triage `探针`×5 `红`×5 `兜底`, unclog `落刀`×5 `落盘`×2, cw_sentinel `分诊`×3, pushci `判类`×2.
- **Cure**: the annotation-card translation-replacement lane — English replacement on docstring/help faces with `.zh.md` archive siblings, the zero-change boundary (identifiers, CLI flags, schema field names, exit-code semantics byte-identical), and the period-spelled five-field header on each tool, each header compressed into the 30-line budget.
- **Expected delta**: −56 error faces (−2.86% of the curable surface 1960).
- **Acceptance**: per-tool `norm_lint --file` error=0; each tool's `--selftest` rc=0 before and after (docstring-only diff); `doc_lint` verdict consistent.
- **Risk**: low — the lane rule forbids code-semantic edits; the suite guards the behavior face.

## 4. C4 (P1) — entry and test-suite prose: translation replacement on the three largest curable doc faces

- **Source**: S1 (per-file error ranking).
- **Evidence**: `README.md` 62 error / 53 warn (jargon: `campaign`×6 `红`×6 `dispatch`×5 `台账`×4 `仓`×3 `席`×3 `红是数据非器红`×3 `干跑`×3 `retrofit`×2 `wave`×2 `哨`×2 `绿判四件套`×2; date stamps 20261111×14, 20261112×11, 20261103×4, 2026-11-13×3, 20261113×3; role name `工装席`×4), `tests/run_tests.sh` 41 error / 37 warn, `tests/README.md` 38 error / 26 warn — 141 error + 116 warn on three faces.
- **Cure**: the same translation-replacement lane (English canonical faces, `.zh.md` archives, zero-change boundary; date stamps move out of prose into the ledger surface, per the card's grading table).
- **Expected delta**: −141 error (−7.20% of curable), −116 warn.
- **Acceptance**: the three faces error=0; the `run_tests.sh` flag-token set unchanged (flags are outside the rewrite scope); suite exit code unchanged.
- **Risk**: low.

## 5. C5 (P2) — checker self-citation exemption: the annotation card's own ban-enumeration faces

- **Source**: S1 cross-analysis (self-referential coverage gap).
- **Evidence**: `docs/annotation-standard-v1.0-20261113.md` carries 133 jargon error + 5 forbidden + 1 cjk findings. Most sit on the card's §4.1–4.3 ban lists (L80/L81/L85/L89) — the card must enumerate the banned faces verbatim to define them, and the linter flags them because only the mapping table (not the card) is exempt from the jargon check, and the report-face skip covers `docs/norm-lint-baseline-*.md` only. Nine further hits are genuine prose-position faces in the card body (L4/L8/L10/L18/L62/L71/L72/L93/L101 — lineage naming and role-topology wording).
- **Significance**: 6.79% of the curable error surface is structurally uncurable by translation — a fitness-signal distortion: no amount of the prescribed cure drives this block to zero.
- **Cure (two-part; the (a) variant needs the reviewer's decision)**:
  - (a) checker-side: extend the exemption to face-enumeration surfaces — either a data-driven whitelist class registered like the existing CJK whitelist (`--cjk-whitelist` precedent), or a bounded positional skip for card §4 enumeration lines. Template: the mapping-table exemption (exempt from the jargon check only, everything else still scanned).
  - (b) card-side: reword the nine genuine prose faces (lineage naming loses the banned tokens; enumeration lines keep the faces as identifier citations — the backtick citation form already exempts them mechanically).
- **Expected delta**: −133 error (−6.79%).
- **Acceptance**: card file error=0 at prose positions; the ban lists remain complete (every §4.1–4.3 face still greps in the card — completeness is machine-checked, so the exemption cannot silently weaken the ban); `norm_lint --selftest` rc=0.
- **Risk**: medium — a checker change that touches the fitness metric itself; requires the reviewer's variant decision and a loud changelog entry.

## 6. Cycle-2 projection and the measurement rule

- C3 + C4 + C5 sum to −330 error faces on the curable surface: 1960 → 1630, a projected cycle-2 reduction rate of **+16.84%** (curable-error basis). On the gross basis (including the frozen ledger) the same work reads +13.5% — and the gross basis degrades every cycle by construction, because each new ledger entry appends date-stamp and jargon faces (+8 error this cycle) on a surface the engine is forbidden to touch.
- **Measurement rule derived this cycle (register for the engine spec)**: the fitness signal is the curable-error reduction rate = (baseline error − current error) / baseline error, computed on the tree **excluding the frozen ledger** (`更新账.md`) and the archive faces the scanner already skips. The v53/v54 account lines register the baseline reduction rate as the fitness signal; this rule fixes its denominator so the metric measures what the engine can actually move.
- Safety restatement: this file drafts; it executes nothing. C1's diagnosis, C2's apply, C3–C5's replacements are all human-gated steps whose commands are cited verbatim so the reviewer runs exactly what is written.
