# rocqwash CI Technical Whitepaper — The Recursive-Iteration Era (v1.0)

- **Date**: 2026-11-16
- **Scope**: failure-class taxonomy, triage interface and repair playbook for the rocqwash CI **after** recursive self-improvement (auto_round rounds, seat waves, self-heal watch) became a normal producer of repository changes.
- **Supersedes**: the host-mismatch era playbook (eleven root causes, 2026-11-16 assessment — code page / autocrlf / HOME override / isolated mode / shell escaping). Those classes still occur; this whitepaper covers what the old playbook **cannot**: failures caused by the iteration machinery itself and by its interaction with hosts, services and concurrent sessions.
- **Companion machine interface**: `docs/ci-triage-table.json` (schema `rocqwash.ci-triage-table/1`) — the symptom→cause→prescription table this whitepaper documents, in machine-readable form. Consumers: the self-heal watch (`selfheal_rocqwash.py`), any session or seat triaging a red run, and future auto-repair agents. **Contract**: match the failing step's log against `markers`; apply `prescription`; respect `auto_repairable` and `escalation`; record the outcome class in the repair ledger (repaired / escalated / watch-only-guard-correct).

---

## 1. Why this CI reddens easily, is hard to fix, and recurs

Four amplifiers, all structural:

1. **Landing cadence** — seats, rounds and waves push many small commits per day; red probability scales with landing count.
2. **One-sided verification** — a fix validated only on the machine that made it is unverified by construction elsewhere (host branches, env vars, platform temp dirs). Case: the TMP fallback landed with `tempfile.gettempdir()` but **without `import tempfile`** — green on Windows (TMP always set, fallback branch never taken), `NameError` on Linux (run 43860918397).
3. **Repair capacity at L1** — the repair agent executes approved actions only; content reds outside its rewrite table are recorded, not fixed. Until the fitness gate is rewired (axiom_guard) and the action space grows class by class, most content reds escalate to sessions by design.
4. **Multi-session concurrency** — several sessions push to the same branch from different working trees; the self-hosted runner's checkout resolves through a path-rewritten dependency on one of those trees staying current (see R8).

"Hard to fix" is therefore not one bug: it is the gap between **red production rate** (amplifier 1) and **classified, verified repair rate** (amplifiers 2-4). The remedy is this whitepaper + the triage table + the E-series guards, not ad-hoc heroics.

## 2. Failure-class taxonomy (recursive era)

Each class: **Symptom** (stable log/observable markers) → **Mechanism** → **Guard** (prevention) → **Prescription** (repair) → **Auto-repairable** (today).

### R1 — Recursive-artifact drift (lane registered, artifact absent)
- Symptom: suite line `FAIL (rc=2)` with `can't open file '.../<name>.py'`; roster count includes a lane whose file is not in the checkout.
- Mechanism: a round/seat registered a test lane but the target file is untracked or landed in another lane; the roster grew before the artifact did.
- Guard: roster derivation must assert file existence per lane (registration without file = red at roster-build time).
- Prescription: drop the lane registration (commit 2748b52 precedent), keep the file lane pending; re-register when the file lands **with an rc=111 skip protocol**.
- Auto-repairable: **yes** (guard class ① of the repair scope).

### R2 — Mechanical-wash overreach (frozen / self-referential faces)
- Symptom: three stations fail-loud together; mapping-source table entries replaced by standard words (norm_lint then flags ordinary English phrases — an active false-positive machine).
- Mechanism: the wash engine's target set did not exclude the frozen set or the mapping source table itself (e04f2f6 precedent; 29ef3ba rollback).
- Guard: exclusion table as a single source (`tools/repair_scope.py`, F1); self-reference guard (`--a2-table` precedent).
- Prescription: revert the touched frozen faces to pre-round content (surgical `checkout HEAD^ -- <faces>`), keep the clean improvements, record the class in the round ledger.
- Auto-repairable: partial (revert leg yes; re-landing the intended improvement needs a seat).

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
- Auto-repairable: the rewiring is a one-time landing (done via autonomy.json), after which this class is structurally closed.

### R6 — Watchdog reflexivity (the watch itself is the failure surface)
- Symptom variants: (a) run-level conclusion `skipped` misread as red; (b) the watch dies with the runner it guards; (c) the runner's checkout depends on an out-of-repo tree staying current (path-rewritten dependency), so a lagging tree fails `not our ref` at checkout — **the local self-hosted face class**.
- Mechanism: guards and watchers are code too; their own lifecycle and dependencies are part of the failure surface.
- Guard: skip≠red judgment (three-way conclusion reading); runner heartbeat + schedule-failure alarm (watch-the-watch); the dependency tree must be kept current (sync before landing) and the dependency documented in the service map (`techdocs/本机服务面与勿扰清单`).
- Prescription: correct the judgment (skip = guard-correct); sync the dependency tree; escalate watch-death to the desk with the heartbeat evidence.
- Auto-repairable: judgment fixes yes; runner lifecycle needs the desk.

### R7 — Environment-branch fixes (a fix with an unexercised branch)
- Symptom: a host-specific fallback added in a fix crashes **only on the host that takes that branch** (`NameError: name 'tempfile' is not defined` on Linux; green on Windows where TMP always exists — run 43860918397).
- Mechanism: the fix added a fallback referencing `tempfile.gettempdir()` without `import tempfile`; the dev machine never executes the fallback branch, so local green proves nothing for the branch.
- Guard: **every new host-branch in a fix must be executed at least once before landing** (unset the env vars locally and run; the suite's host-matrix exists for exactly this). The eleven-cause playbook's rule "pin irrelevant host variables inside the fixture boundary" extends to: "exercise every fallback branch you add".
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
- Mechanism: concurrent sessions share one working tree; landing waves overlap pending lanes.
- Guard: meal/face selection must read `git status --porcelain` first and exclude dirty faces (collision-free matrix before concurrency); landing waves use 3-way apply onto the current head and preserve pending lanes.
- Prescription: stash→rebase(resign)→push→pop dance; record both sides in the ledger.
- Auto-repairable: partial (the union merge is mechanical; adjudication of conflicting intents is not).

## 3. Judgment matrix

| Surface | Role |
|---|---|
| macOS hosted | primary judge (canonical suite) |
| Linux / Windows hosted | blocking faces (stable roster) |
| Windows self-hosted (LIVE-ROCQWASH) | blocking face + canonical-path evidence (depends on R6 tree-currency) |
| Platform-sensitive watch seats | advisory (`continue-on-error`), never block; host-noise tracked here |
| self-heal watch | triage + transient heal + content-red recording; **its own skips are guard-correct, not red** |

## 4. Repair playbook (procedure per red)

1. Pull the **whole-run** log (single-job endpoint 403s; run endpoint works).
2. Match the failing step against `docs/ci-triage-table.json` markers → class.
3. Read the class section above; apply the prescription; respect `auto_repairable`.
4. Land the fix through the same gates as any change (fitness gate, language gates, certification-face exclusion).
5. Record the outcome class in the repair ledger (`repaired / escalated / watch-only-guard-correct`) — this is how "watched" stays distinguishable from "failed to fix".

## 5. Case files

- **Run 43860918397** (two reds): R7 (Linux, tempfile import missing in the TMP-fallback branch — fix c9f23d3) + R6(c) (Windows self-hosted, `not our ref` at checkout — the runner's path-rewritten dependency tree lagged the shore; resolved by syncing that tree, and registered as a standing dependency in the service map).

## 6. Lineage

- Host-mismatch era: eleven root causes (code page, autocrlf, HOME override, isolated mode, shell escaping, execv argv, taskpolicy, `.git` in write-sweep, MSYS path folding, grandchild process reaping) — see the 2026-11-16 deployment/RSI assessment, §二.
- Recursive era: this whitepaper. Update rule: every new class lands here AND as a row in `docs/ci-triage-table.json` AND as an experience card in the cross-line area (`exp/INDEX.md`) in the same round (the replication obligation).
