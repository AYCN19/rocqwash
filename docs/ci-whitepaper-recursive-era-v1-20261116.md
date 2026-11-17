# rocqwash CI Technical Whitepaper — The Recursive-Iteration Era (v1.0)

- **Date**: 2026-11-16
- **Scope**: failure-class taxonomy, triage interface and repair playbook for the rocqwash CI **after** recursive self-improvement (auto_round rounds, agent waves, self-heal watch) became a normal producer of repository changes.
- **Supersedes**: the host-mismatch era playbook (eleven root causes, 2026-11-16 assessment — code page / autocrlf / HOME override / isolated mode / shell escaping). Those classes still occur; this whitepaper covers what the old playbook **cannot**: failures caused by the iteration machinery itself and by its interaction with hosts, services and concurrent sessions.
- **Companion machine interface**: `docs/ci-triage-table.json` (schema `rocqwash.ci-triage-table/1`) — the symptom→cause→prescription table this whitepaper documents, in machine-readable form. Consumers: the self-heal watch (`selfheal_rocqwash.py`), any session or agent triaging a red run, and future auto-repair agents. **Contract**: match the failing step's log against `markers`; apply `prescription`; respect `auto_repairable` and `escalation`; record the outcome class in the repair ledger (repaired / escalated / watch-only-guard-correct).

---

## 1. Why this CI reddens easily, is hard to fix, and recurs

Four amplifiers, all structural:

1. **Landing cadence** — seats, rounds and waves push many small commits per day; red probability scales with integration count.
2. **One-sided verification** — a fix validated only on the machine that made it is unverified by construction elsewhere (host branches, env vars, platform temp dirs). Case: the TMP fallback landed with `tempfile.gettempdir()` but **without `import tempfile`** — green on Windows (TMP always set, fallback branch never taken), `NameError` on Linux (run 43860918397).
3. **Repair capacity at L1** — the repair agent executes approved actions only; content reds outside its rewrite table are recorded, not fixed. Until the fitness gate is rewired (axiom_guard) and the action space grows class by class, most content reds escalate to sessions by design.
4. **Multi-session concurrency** — several sessions push to the same branch from different working trees; the self-hosted runner's checkout resolves through a path-rewritten dependency on one of those trees staying current (see R8).

"Hard to fix" is therefore not one bug: it is the gap between **red production rate** (amplifier 1) and **classified, verified repair rate** (amplifiers 2-4). The remedy is this whitepaper + the triage table + the E-series guards, not ad-hoc heroics.

## 2. Failure-class taxonomy (recursive era)

Each class: **Symptom** (stable log/observable markers) → **Mechanism** → **Guard** (prevention) → **Prescription** (repair) → **Auto-repairable** (today).

### R1 — Recursive-artifact drift (lane registered, artifact absent)
- Symptom: suite line `FAIL (rc=2)` with `can't open file '.../<name>.py'`; roster count includes a lane whose file is not in the checkout.
- Mechanism: a round/agent registered a test lane but the target file is untracked or landed in another lane; the roster grew before the artifact did.
- Guard: roster derivation must assert file existence per lane (registration without file = red at roster-build time).
- Prescription: drop the lane registration (commit 2748b52 precedent), keep the file lane pending; re-register when the file lands **with an rc=111 skip protocol**.
- Auto-repairable: **yes** (guard class ① of the repair scope).

### R2 — Mechanical-wash overreach (frozen / self-referential faces)
- Symptom: three stations fail-loud together; mapping-source table entries replaced by standard words (norm_lint then flags ordinary English phrases — an active false-positive machine).
- Mechanism: the wash engine's target set did not exclude the frozen set or the mapping source table itself (e04f2f6 precedent; 29ef3ba rollback).
- Guard: exclusion table as a single source (`tools/repair_scope.py`, F1); self-reference guard (`--a2-table` precedent).
- Prescription: revert the touched frozen faces to pre-round content (surgical `checkout HEAD^ -- <faces>`), keep the clean improvements, record the class in the round ledger.
- Auto-repairable: partial (revert leg yes; re-integration the intended improvement needs a agent).

### R3 — Stale repair target (superseded head)
- Symptom: a prepared repair no longer applies; the branch moved while the fix was being verified.
- Mechanism: fix prepared on head A; branch advanced to B; A's patch conflicts or is moot.
- Guard: compare-API discrimination (ahead/identical = covered → skip; behind/diverged = not proven → proceed), then re-apply the fix **onto the current head** with a 3-way apply; conflicts escalate.
- Prescription: repair-on-current-head procedure (E3).
- Auto-repairable: partial (re-apply yes; conflicts escalate).

### R4 — Intent & queue violations
- Symptom: cancelled runs re-enter the queue; queued runs pile beyond capacity; "everything is queued and old runs fail again".
- Mechanism: pre-governor behavior — revival of cancelled runs treated as backlog; unbounded queue growth under push bursts.
- Guard: cancelled = intent, never auto-revived; queue governor keeps MAX_QUEUED_RUNS (3), oldest trimmed, in-progress never touched.
- Prescription: none needed (guard-correct); manual rerun remains available.
- Auto-repairable: the guard IS the repair (watch-only-guard-correct).

### R5 — Fitness absence (repair without a real gate)
- Symptom: rounds land with `verify_rc` reflecting only the linter's selftest; a repair that "passed" breaks the suite or the proof surface.
- Mechanism: `DEFAULT_VERIFY_CMD` pointed at `norm_lint.py --selftest` — the gate validated the validator, not the change.
- Guard: rewire `verify_cmd` to the axiom_guard compile leg (autonomy.json; see `techdocs/接口契约-axiom-guard-verify-换轴`); repairs and rounds share the same gate.
- Prescription: rewire + measure the gate cost once, then set the round cadence from measurement.
- Auto-repairable: the rewiring is a one-time integration (done via autonomy.json), after which this class is structurally closed.

### R6 — Watchdog reflexivity (the watch itself is the failure surface)
- Symptom variants: (a) run-level conclusion `skipped` misread as red; (b) the watch dies with the runner it guards; (c) the runner's checkout depends on an out-of-repo tree staying current (path-rewritten dependency), so a lagging tree fails `not our ref` at checkout — **the local self-hosted face class**. Variant (c) refinement (2026-11-17): for rocqwash the bridge resolves to the DESK DEV TREE ITSELF (`.gitconfig` insteadOf → `file:///D:/ComplexAnalysis/rocqwash`), so the desk tree lagging remote by one commit reproduces the red; and `not our ref` must be adjudicated compare-API-first — verify ancestry (behind=0 = NOT an orphan) before concluding a force-push casualty (the 2026-11-17 case was a rebase integration, not an orphaning).
- Mechanism: guards and watchers are code too; their own lifecycle and dependencies are part of the failure surface.
- Guard: skip≠red judgment (three-way conclusion reading); runner heartbeat + schedule-failure alarm (watch-the-watch); the dependency tree must be kept current (sync before integration) and the dependency documented in the service map (`techdocs/本机服务面与勿扰清单`).
- Prescription: correct the judgment (skip = guard-correct); sync the dependency tree; escalate watch-death to the desk with the heartbeat evidence.
- Auto-repairable: judgment fixes yes; runner lifecycle needs the desk.

### R7 — Environment-branch fixes (a fix with an unexercised branch)
- Symptom: a host-specific fallback added in a fix crashes **only on the host that takes that branch** (`NameError: name 'tempfile' is not defined` on Linux; green on Windows where TMP always exists — run 43860918397).
- Mechanism: the fix added a fallback referencing `tempfile.gettempdir()` without `import tempfile`; the dev machine never executes the fallback branch, so local green proves nothing for the branch.
- Guard: **every new host-branch in a fix must be executed at least once before integration** (unset the env vars locally and run; the suite's host-matrix exists for exactly this). The eleven-cause playbook's rule "pin irrelevant host variables inside the fixture boundary" extends to: "exercise every fallback branch you add".
- Prescription: add the missing import/requirement on the branch, land, and add the branch to the roster's platform-sensitive watch until three consecutive greens.
- Auto-repairable: yes (one-line class; the diagnosis needs this table).

### R8 — Service-face coupling (repository updates break local services)
- Symptom: the self-hosted face disconnects; the MCP tools/list count changes or the server drops; the sentinel daemon stops matching its CLI contract.
- Mechanism: local services consume repository faces (`tools/mcp_server.py`, `ci.yml` matrix labels, sentinel CLI); a refactor that renames/moves/rescopes them breaks the wiring.
- Guard: the service map and do-not-touch rules (`techdocs/本机服务面与勿扰清单-20261116.md`): tool signatures additive-only; matrix labels checked against the runner's actual labels; stop-the-line declaration on any service anomaly.
- Prescription: follow the map's recovery pointers; re-register only per the map.
- Auto-repairable: no (service face is out-of-repo; desk-gated).

### R9 — Platform evolution (runtime deprecations)
- Symptom: deprecation warnings escalating to failures on hosted runners ("Node 20 deprecated… forced to Node 24").
- Mechanism: action versions pin runtime majors; GitHub deprecates majors on a published schedule.
- Guard: quarterly `uses:` audit against each action's latest release (fetch-before-use precedent: upload-artifact v4 → v7.0.2).
- Prescription: bump the action, keep the flag face, watch one run.
- Auto-repairable: yes (one-line class).

### R10 — Multi-session collision (same tree, same machine)
- Symptom: a repair or round touches faces another session holds dirty (uncommitted pending lanes); stash/rebase dances; "my fix disappeared".
- Mechanism: concurrent sessions share one working tree; integration waves overlap pending lanes.
- Guard: meal/face selection must read `git status --porcelain` first and exclude dirty faces (collision-free matrix before concurrency); integration waves use 3-way apply onto the current head and preserve pending lanes.
- Prescription: stash→rebase(resign)→push→pop dance; record both sides in the ledger.
- Auto-repairable: partial (the union merge is mechanical; adjudication of conflicting intents is not). **Churn variant (2026-11-17, run 138)**: with `cancel-in-progress: true`, the cancel fires when ANY run enters the group — an older QUEUED run, the moment it started, cancelled the NEWER in-flight tip run (the guard murdered the fresh verdict it was meant to protect). Root cure: cancel-in-progress OFF (in-flight protected) + the self-heal `ci_queue_governor` retires stale QUEUED runs per head branch (keep newest, cancel older queued, in_progress never touched) in the reconcile and automerge-only passes.


### R11 — shallow runner checkout × frozen git-anchor (DRIFT false-flag; 2026-11-16 live case)

- **Symptom**: `DRIFT git锚 HEAD <sha> 非 freeze_commit <sha> 后代` on the local self-hosted face while hosted faces pass; the workspace `.git/shallow` file present; the ancestry verdict fires even though the main lineage is linear and desk-approved.
- **Mechanism**: the runner workspace was a depth-1 shallow clone; `git merge-base --is-ancestor freeze_commit HEAD` evaluates over the visible (single-commit) history and reports not-ancestor (rc=1) - the check's DOWNGRADE branch (rc>=128, objects missing) never fires because rc=1 is a *verdict*, not an error. `ci.yml fetch-depth: 0` alone did not unshallow the cached workspace (the unshallow fetch must actually complete - a NETRED-window abort leaves the shallow file in place).
- **Guard**: the self-hosted checkout carries `fetch-depth: 0`; after one desk unshallow (git fetch --unshallow from the local dev tree via file:// transport, zero-network) the workspace keeps full history.
- **Prescription**: desk one-time unshallow of the runner workspace; durable fix = frozen8 check detects the shallow state and downgrades the git-anchor ring (desk-gated, frozen face).
- **Auto-repairable**: no (frozen face; desk-gated).


### R12 — environment-conditional contract branch × runner PATH drift (2026-11-17 live case)

- **Symptom**: one test red on the local self-hosted face only, all hosted faces green, every other face passing (t_clean_mode V16: `rc=0 out='COMPILED-ALL 0 modules ...'` against a report-and-refuse rc1 contract); the same job was green the day before with zero content change.
- **Mechanism**: a report/refuse branch keyed on environment presence (the clean-mode report lived INSIDE the import-time toolchain gate) silently changes meaning when the machine's PATH gains the dependency — ROCWASH_CLEAN=1 stopped being honored and the tool executed under clean mode. Content fingerprints cannot see environment drift: the suite went green→red with no code change (the runner PATH gained the Rocq/OCaml toolchain).
- **Guard**: every report/refuse branch keyed on environment presence must be executed on BOTH faces before integration (a PATH stub simulates presence); report-not-execute contracts must be checked ABOVE the presence gate, never inside it; test vectors asserting rc must be environment-aware (assert the invariant — marker absence, contract rc per branch — not one environment's rc); the test docstring's own "machine-independent" claim must hold per vector (it was false for V16/V17).
- **Prescription**: move the clean-mode check above the toolchain gate (report always, exit 1, never execute; keep the standing FATAL byte-identical for the absent path); make the default-mode vector environment-aware. Diagnosis recipe: `_runner_loop.log` timeline (green before / red after the environment change) + PATH-stub byte-level reproduction on the old blob.
- **Auto-repairable**: no (contract repair touches tool + test; desk-gated). Sibling class: R7 (a fix carrying an unexercised branch) — R12 is the environment-drift flip of an exercised branch.


### R13 — silent gate stall (a gate reads a signal no trigger produces; 2026-11-17 live case)

- **Symptom**: no red anywhere — a standing automation just never acts. PR #10 sat open with `hold (no head CI yet)` in every reconcile pass while its head commit had ZERO check runs; the desk noticed only because the user asked why the merge never happened.
- **Mechanism**: the automerge green gate matched push-event runs by head SHA, but ci.yml triggers only on `push: [main]` and `workflow_dispatch` — a supply/* PR head can NEVER produce the signal the gate waits for. The gate was implemented correctly against a pipeline that did not exist: the trigger was never extended when the gate landed.
- **Guard**: every gate's required signal must be wired end to end (trigger → run → verdict). Landing a gate demands the same audit as integration a lane: enumerate the producing trigger, the matching key, and the verdict source — a gate with no producer is a stall, not a hold. A reconcile log line repeating identically for hours is the stall's fingerprint.
- **Prescription**: extend the trigger (`pull_request` types opened/synchronize/reopened), broaden the match (push / workflow_dispatch / pull_request runs — a PR-event run's head_sha is the MERGE-ref commit, so match via the `pull_requests` link too), and let the gate self-start the missing signal (route ci.yml at the PR head branch when no run exists). Gate on the hosted faces via the jobs API, never the run-level conclusion: the local self-hosted face is main-only evidence (main_only gate) and a branch route from a ref whose ci.yml predates that gate still runs it.
- **Auto-repairable**: partial (match widening + route-on-demand is mechanical; trigger changes touch the blocking workflow — desk-gated). A blindness sub-face (2026-11-17, run 118): GitHub emits NO workflow_run event for a validation-failed workflow file, so the self-heal watch is structurally blind to parse death — the scheduled reconcile carries a read-only parse-death probe (newest main run jobs=0 = the signature; last-known-good reported alongside) as the in-system sensor; the blocking-file fix stays desk-gated.

## 3. Judgment matrix

| Surface | Role |
|---|---|
| Linux / Windows hosted | blocking faces (stable roster) |
| Windows self-hosted (LIVE-ROCQWASH) | blocking face + canonical-path evidence (depends on R6 tree-currency; the bridge resolves to the dev tree itself — see R6(c) variant) |
| macOS hosted (mac-verify.yml) | advisory face (`continue-on-error`): a capacity-starved macos-15 queue must never block the pipeline (2026-11-17 routing redundancy — the mac face moved out of the blocking matrix) |
| Platform-sensitive watch seats | advisory (`continue-on-error`), never block; host-noise tracked here |
| self-heal watch | triage + transient heal + content-red recording + weekly branch census (merged-stale stubs reported as deletion CANDIDATES, never deleted in-run); **its own skips are guard-correct, not red** |

## 4. Repair playbook (procedure per red)

1. Pull the **whole-run** log (single-job endpoint 403s; run endpoint works).
2. Match the failing step against `docs/ci-triage-table.json` markers → class.
3. Read the class section above; apply the prescription; respect `auto_repairable`.
4. Land the fix through the same gates as any change (fitness gate, language gates, certification-face exclusion).
5. Record the outcome class in the repair ledger (`repaired / escalated / watch-only-guard-correct`) — this is how "watched" stays distinguishable from "failed to fix".

## 5. Case files

- **Run 43860918397** (two reds): R7 (Linux, tempfile import missing in the TMP-fallback branch — fix c9f23d3) + R6(c) (Windows self-hosted, `not our ref` at checkout — the runner's path-rewritten dependency tree lagged the shore; resolved by syncing that tree, and registered as a standing dependency in the service map).
- **Run 43922602217** (attempt 3, 2026-11-17, three chained events): R6(c) variant (checkout `not our ref d8ba0a86` — the bridge resolves to the dev tree itself; the desk tree lagged the fresh rebase integration by one commit; hosted faces green; fix = desk fetch+ff then rerun-failed-jobs) → R12 (t_clean_mode V16 — the runner PATH gaining the Rocq/OCaml toolchain flipped the clean-mode contract branch; fix 35d7f63 = report-not-execute above the gate + environment-aware V17; verified 18/18 on BOTH faces; the desk-side triage agent independently reproduced the red with a PATH stub on the old blob and dug the green→red timeline from `_runner_loop.log`) → **CI #116 all green** with the routing redundancy live (mac-verify advisory green twice; the macos-15 capacity jam structurally cured by moving the mac face out of the blocking matrix + concurrency supersede on the CI group).

## 6. Lineage

- Host-mismatch era: eleven root causes (code page, autocrlf, HOME override, isolated mode, shell escaping, execv argv, taskpolicy, `.git` in write-sweep, MSYS path folding, grandchild process reaping) — see the 2026-11-16 deployment/RSI assessment, §二.
- Recursive era: this whitepaper. Update rule: every new class lands here AND as a row in `docs/ci-triage-table.json` AND as an experience card in the cross-line area (`exp/INDEX.md`) in the same round (the replication obligation).
- **PR #10 chain (2026-11-17)**: R13 sub-face 2 (the PR LIST endpoint never computes `mergeable` — the leg re-reads the single PR before holding) + sub-face 3 (the PR head BRANCH was deleted while the PR stayed open — route 422; the leg restores the head ref from the head commit before dispatching) → **PR #10 MERGED autonomously (merge commit e73a34a9, hosted-jobs gate)** with the local-face checkout red tolerated by design (the bridge lacked the PR head objects) → the durable cure: the JOB_STARTED mirror-sync hook installed on the rocqwash runner (dev-tree = bridge target; explicit capital-GitHub upstream; dirty-tree-guarded main ff; pull-refs backfill; sparse neutralization; printf-style .env writers eat backslash escapes).
- **Fingerprint-skip gate + standing cron (2026-11-17, desk order)**: hosted suite faces + mac advisory carry a fingerprint-keyed verdict cache (whole tree minus the pure-prose allowlist; actions/cache@v6; exact key per face label) - modes FULL / ANCHORS (anchor tier: frozen8 + station + registry faces, the doc-input faces); reruns and dispatches always run FULL; the canonical local face never skips (R12). The standing self-evolution cron (17 */4 * * *) runs one deterministic mechanical round per tick with zero model cost, no-ops cleanly at census zero, and dispatches its own CI judge (R13 sub-face 4 generalization). The stale merged branch (fix/pr3-followups-20261115) was deleted after squash-content equivalence; an uncancellable zombie route (cancel 409 on queued zero-job runs) was retired by deleting its already-merged branch ref.
