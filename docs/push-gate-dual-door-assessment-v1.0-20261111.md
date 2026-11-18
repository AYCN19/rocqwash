# push-gate-dual-door-assessment — the push_gate push-window four criteria × the pushci preflight check: dual-door normalization assessment report (v1.0, November 11, 2026)

> Purpose.  Assessment-only evaluation of whether the two push gates — the `certify/push_gate.py` `window` subcommand (the four push-window criteria) and the `tools/pushci.py` stage-1 preflight check — overlap, differ, and can be normalized into one; three options are examined and one is recommended. Commissioned by the v39/v40 ledger scheduling item "normalize-assess the `push_gate.py` push-window four criteria against the pushci preflight (the standing two-gate arrangement recorded as-is)" (`更新账.md:3609`, `更新账.md:3700`). Zero code change: both tools, the wrapper, `cw.sh`, the tests, and the README series were untouched under this task instruction (a separately commissioned `cw_sentinel` guard fix landed by this agent in the same round belongs to a different task instruction and is unrelated to this assessment). All conclusions anchor only on code and run evidence present in the tree; line anchors reflect the tree state after 496ebdf (rocqwash v40). Written separately by the assessment agent.
> Interface.  Document face only; no runtime interface. Assessment domain: `certify/push_gate.py` (the `window` subcommand, the four push-window criteria) and `tools/pushci.py` (the five-stage pipeline preflight→push→watch→heal→verdict±merge, stage 1 = the preflight check, the launch-time gate). The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  Read-only citations of the on-tree faces `certify/push_gate.py`, `tools/pushci.py`, `wrapper/push_gate_rq.sh`, `cw.sh`, `README-cw.md`, `docs/workflow-integration-whitepaper-v1.0-20261111.md`, `examples/workflows/step-pushci.md`, and `更新账.md`; no runtime dependency on any code face.
> Evidence.  §6: the `--selftest` runs of both assessed tools (both rc=0), the `certify/frozen8.py --ledger` roster check (`certify/push_gate` count = 0), and the suite baseline `bash tests/run_tests.sh` (52 passed / 0 failing / 4 skipped, rc=0); items not run live are declared as such in §6.
> Exit-codes.  Not applicable to a document face; the assessed tools keep their implemented exit-code semantics unchanged (0/1/2/9, documented in §1).

---

## 1 What each gate judges

### 1.1 Gate B: push_gate window — the four push-window criteria (timing and evidence)

Canonical statement: `certify/push_gate.py:8-30` (docstring); implementation at `:109-212`. It carries the effort-level push-window hard requirement (`push_gate.py:9` cites the ConstructiveWorld effort workflow wf_land.dwf.ts:40): "① runs in_progress=0 ② local ≥ remote ③ fetch clean ④ certification passing confirmed". Mechanical form:

| criterion | what it judges | evidence source | anchor |
|---|---|---|---|
| c1 ci-idle | CI runs in flight = 0. Any status ≠ `completed` is conservatively counted as in flight (fail-closed). | `--runs-json` (pre-fetched Actions runs JSON — **this tool itself does zero networking**, it only interprets) or `--ci-capped-min N` (the most recent reflog `update by push` entry is ≥ N minutes old plus a CI-duration cap ⇒ an in-flight run is impossible) | `push_gate.py:109-151` |
| c2 local≥remote | after fetch, `rev-list --count HEAD..<remote>/<branch>` (behind) == 0; ahead is uncapped (a locally leading tree is exactly the to-be-pushed state) | git mechanical counting | `push_gate.py:154-165` |
| c3 fetch-clean | ls-remote read twice, before and after, with the same sha; fetch rc=0; the remote sha is an ancestor of local HEAD (`merge-base --is-ancestor`) — nobody moved the remote inside the window | genuine remote read-only operations (fetch/ls-remote) | `push_gate.py:168-187` |
| c4 cert-green | mechanical re-check of this repository's certification passing: `bash tests/run_tests.sh` rc==0 (`--suite` can name another suite); optionally `--freeze-manifest` frozen-artifact zero-drift must also return rc==0 | exit codes | `push_gate.py:190-212` |

- Criterion order: **c3 first** (fetch settles the remote-tracking ref; only then do the c1 timeline and the c2 count have a basis) → c1 → c2 → c4 (`cmd_window`, `push_gate.py:235-239`).
- Conclusion: all four criteria PASS ⇒ `push-window: OPEN`, exit 0; otherwise CLOSED, exit 1 — **NOT-RUN = window closed; absent corroboration is never counted as passing** (the honesty law, `push_gate.py:29`; the c1 zero-evidence NOT-RUN at `:151`). Exit-code roster 0/1/2/9 (`push_gate.py:65-67`).
- **It judges the window and never pushes**: the push action belongs to the caller (`push_gate.py:30`); window is read-only throughout (write-domain declaration `push_gate.py:49-50`; fetch/ls-remote are remote read-only operations).
- In-service form: the manual legacy chain (`README-cw.md:60`) plus the adapter `wrapper/push_gate_rq.sh` (window injects `--repo <repo-root> --suite <repo-root>/tests/run_tests.sh`, removing cwd sensitivity; a no-argument call exits 2 and forbids surprise networking — `push_gate_rq.sh:60-63,71-72`).

### 1.2 Gate A: pushci preflight — the launch-time gate (can the environment initiate)

Canonical statement: `tools/pushci.py:7-16` (docstring); implementation `stage_preflight` at `:703-748`. Stage 1 of the five-stage pipeline (preflight→push→watch→heal→verdict±merge); the no-initiation rule in code form:

| check | what it judges | stop condition | anchor |
|---|---|---|---|
| ① toolchain | `tools/toolchain_dyld_doctor.py` subprocess → verdict ≠ healthy (toolchain linkage failure surface) | `StopVerdict("toolchain", 1)` | `pushci.py:710-737` |
| ② net | `tools/net_probe.py --rounds 2 --interval S --stable-window` subprocess → UNSTABLE (dual-probe stability window; the single-probe no-initiation rule belongs to the four tools themselves — this tool only honors their rulings) | `StopVerdict("unstable", 1)` | `pushci.py:739-744,787-795` |
| ③ (optional) gate4 pre-scan | `--pre-scan-gate4`: `git diff <base>...<branch>` collects the changed .v files → `verify/gate4_comment_guard.py` per file → passes only at FAIL=0 (REVIEW is recorded loudly and does not block) | `StopVerdict("gate4-block", 2)` | `pushci.py:746-748,802-843` |

- After the gate, stages 2-5: push (the git four-call order get-url→rev-parse→push×3, 45 s each → ghproxy reroute ×2 → ls-remote remote-tip recheck, `pushci.py:17-24,847-898`) → resolve+watch (head_branch+head_sha interlock, `pushci.py:25-30,912+`) → heal (classification via `ci_triage`, bounded rerun cap of 3, family-A content failures are never machine-fixed, `pushci.py:31-42`) → verdict±merge.
- Exit-code roster: 0 = success/dry-run; 1 = heal-exhausted/unstable/toolchain; 2 = fix-content/gate4-block/usage error; 9 = target missing (`pushci.py:101-104`). The verdict closed roster carries seven states (`pushci.py:118-119`).
- `--dry-run` = print the plan only, zero side effects (zero git, zero API, zero tool subprocesses, `pushci.py:89`; the destructive-surface matrix row P1 attests both flows empty through the api_calls/git-caller dual record).
- Mainline in-service form: the `cw.sh pushci` route (`cw.sh:218`; the twenty-tool roster `cw.sh:232`), plus workflow embedded section ② (`examples/workflows/step-pushci.md`).

---

## 2 The overlap surface (very little is truly judged by both gates)

1. **The same physical object**: both gates ultimately serve the same `git push` — gate B judges "does the window open right now", gate A executes the push itself after passing its checks. The judged object is the same; the ownership of the action differs (B only judges and never pushes; A judges and pushes).
2. **The same fail-closed posture**: gate B — no evidence = NOT-RUN = window closed (`push_gate.py:29,151`); gate A — either gate tool's verdict ≠ healthy/UNSTABLE = no initiation (`pushci.py:737,742`). Both gates forbid "absence of evidence counted as passing".
3. **The same read-only posture**: gate B's write-domain declaration is read-only throughout (`push_gate.py:49-50`); gate A's preflight stage runs only local probe subprocesses plus net_probe read-only GETs, zero writes to the tree or the remote (report/--json write only to a caller-named path). The two gates' write-domain discipline shares one origin (write only to explicitly named outputs; zero surprise writes).
4. **The post-hoc fallback of c2/c3 lives in the push itself**: at real push time git's own non-fast-forward rejection is the final mechanical fallback for behind>0 / a remote moved inside the window — but that is learned only after a failed initiation; gate B's value is exactly to spare the futile initiation beforehand. This is the only substantive "overlap" of criteria between the two gates, and it is a fallback relation, not a duplicated-criteria relation.
5. **The criterion sets do not intersect**: c1-c4 and doctor/net-probe/gate4 — not one criterion of one set coincides with the other (§3.2). The alleged dual-door overlap is an overlap of discipline (fail-closed / mechanical evidence / read-only), not duplicated work at the criterion level.

---

## 3 The difference surface

1. **They answer different questions**: gate A = "can the environment initiate" (toolchain / network stability window / head-comment guard); gate B = "should the push happen now" (CI idle / local leading / nobody moved the remote in-window / certification passing). Whitepaper §4 qualifier: "two gates, each judging its own question, neither substituting for the other" (`docs/workflow-integration-whitepaper-v1.0-20261111.md:163-201`).
2. **Different evidence models**: gate A's evidence is always present (doctor/probe/gate4 real-mode runs always produce a verdict; a malformed run fails loud with 2); gate B's c1 evidence is **optional**, and its absence closes the window (the NOT-RUN semantics, `push_gate.py:141-151`) — the push window is a decision of "opens when the corroboration is complete"; the launch-time gate is a decision of "probes run now and are judged now".
3. **Different cost structures**: gate A's three checks are second-scale; gate B's c4 runs the full `tests/run_tests.sh` directly (measured this round by this agent: 52 passed / 0 failing / 4 skipped, rc=0 — minute-scale bulk) plus an optional frozen-artifact reconciliation. The cost asymmetry is structural, not an implementation shortcut.
4. **Different network postures**: gate B's c3 must touch the real remote (fetch/ls-remote, read-only); gate A's preflight stage itself makes zero git and zero remote calls (doctor is local; net_probe calls its probe endpoint). The adapter therefore establishes a "no-argument calls forbidden" contract against surprise networking (`push_gate_rq.sh:60-63`).
5. **Different exit codes and record surfaces**: gate A's check failure folds into the five-stage verdict closed roster of seven states plus the report `stages.preflight{toolchain,net,gate4?}` (`pushci.py:107-111`); gate B keeps its own OPEN/CLOSED 0/1 roster plus per-criterion PASS/FAIL/NOT-RUN lines and an optional window.json (`push_gate.py:241-258`). The two rosters are each on file and never translated into one another.
6. **Different freshness instants**: under the canonical serial order (whitepaper §4 — gate B judges the window first, gate A then runs the pipeline), gate B's c3 dual-read evidence is already seconds stale when gate A performs the real push — c3's own before/after dual-read design shows its author knew the window is not atomic; the only form that could make it atomic is "the window judge performs the push itself", and neither gate is that today (see the illusion risk in §4, Option B).
7. **Different consumers**: gate A = the mainline single command (the `cw.sh` route plus workflow embedded section ②; the verdict can branch, and heal gives bounded automatic recovery); gate B = the manual legacy chain plus the adapter plus a workflow pre-window step. The `cw.sh` twenty-tool roster carries **no** push-gate route (`cw.sh:232`) — gate B stays registered through the wrapper and the docs, outside the mainline single command.
8. **Different module postures**: gate A = `tools/` orchestration glue (the four tool subprocesses, zero new engines, `pushci.py:5-6`); gate B = a `certify/` deep face (mechanical criteria plus a UNION v2 multi-world checklist in the same file, frozen vector groups self-attesting, adapter-wrapped). **push_gate.py is not on the frozen8 frozen-eight roster** (measured by this agent: `frozen8.py --ledger` full-roster count = 0) — it is in service and repairable, but this assessment changes nothing.

---

## 4 Three normalization options

### Option A — keep the two gates side by side, each judging its own question (fix the status quo)

**Form**: zero change to both tools. Whitepaper §4 canonical serial order (gate B judges the window first; only an OPEN window enters gate A) + the honest side note in README-cw (`README-cw.md:60-63`: "the push-window four criteria such as suite passing / behind=0 are not in that roster; check discipline remains with `certify/push_gate.py`") + the embedded section ② note ("two gates … neither substitutes for the other", `step-pushci.md:159-161`) — that is the entire regulation of the status quo.

- Benefit: zero code, zero regression surface; single ownership of criteria (the four criteria have their sole canonical home in certify; no second implementation = no drift surface); the contract that c1 evidence is "initiated explicitly by the caller" (adapter contract clause 3) is preserved — the push-window discipline lets the human/workflow choose the evidence source per repository state, and the tool never overreaches by guessing.
- Cost: a caller wanting both gates must run two commands serially (the workflow embedded section already gives the canonical order; manual-chain users must read the docs); pushci alone can still skip the window judgment (see the residual risk in §5).
- Ruling: **feasible; the status quo is the steady state**.

### Option B — pushci preflight calls push_gate window as a check (orchestration enlarged by one notch)

**Form**: preflight gains a step ④, the subprocess `python3 -B certify/push_gate.py window --repo <repo_path> --branch <branch> [--runs-json …]`; only exit 0 passes the check; push_gate remains the sole canonical home of the criteria (an orchestration call, not a reimplementation — fits "orchestration adds no new engine" literally).

Examined item by item:

- **The c4 cost folds into every initiation**: c4 runs the full suite directly (§3.3) — embedded in pushci, every real push pays the full minute-scale duration; switching `--suite` to a lightweight script hollows out the criterion (certification passing in name only). **There is no way to have both.**
- **The c1 evidence is structurally absent on the pushci side**: of c1's two sources (runs-json/ci-capped-min), pushci has no flag to pass either through; and the ci-capped-min timeline evidence requires a reflog `update by push` entry (`push_gate.py:138-142`) — **a new branch's first push (pushci's primary use case) necessarily lacks that entry → NOT-RUN → CLOSED**: the default-open gate makes pushci permanently closed for new branches. Fixing it requires adding a runs-json pre-fetch flag to pushci plus a full documentation sweep — the change has already outgrown "one notch of orchestration".
- **The verdict closed roster would need an eighth state**: CLOSED has no slot among the seven states; mapping it to unstable=1 is a semantic distortion (unstable is network/push-path instability, not "the time has not come"); a new state = a `rocqwash-pushci/1` report schema extension plus a full alignment sweep of README-cw / the whitepaper / embedded section ② / CHANGELOG / every doc_lint-checked face, plus per-face re-checks of `tests/fixtures/pushci_scenarios` and the 15 t_pushci vectors and matrix row P1 (the dry-run `stages == {}` assertion).
- **The atomicity illusion**: the window having passed its judgment ≠ the window still being open at push time (§3.6) — nesting gate B inside gate A would create the illusion of "check passed, therefore safe", while c3's dual-read design is itself proof that the window is not atomic. Side by side, the two gates keep separate records (window.json plus the pushci report); nested, the evidence instead blurs together.
- **Gate B does not retire because of this**: the manual legacy chain (README-cw:60) stays legitimately registered — push_gate window must remain independently callable; one criterion set gaining two call surfaces (embedded in pushci + standalone CLI) = the standing drift breeding ground that doc_lint fights daily.
- Ruling: **technically feasible; a default-open gate is a net negative; the optional-flag form does not normalize, it enlarges the surface**. The normalization goal (one entry judging everything) is not reached; the two gates become one and a half.

### Option C — merge the criteria (one large gate, a single tool face)

**Form**: either reimplement c1-c4 inside pushci preflight, or fold doctor/net-probe/gate4 into push_gate window — one tool judges all criteria.

- Merging into pushci = a second implementation of the four criteria: it violates the substance of "orchestration adds no new engine" (a criterion reimplementation is a new engine); the certify canonical home remains (the legacy chain stays registered) → a dual-canonical-home drift surface; the c4 cost and c1 absence mountains are carried over unchanged (Option B's first two bullets).
- Merging into push_gate = a change of the certify deep-face posture: a read-only window becomes an orchestration face running doctor/probe/gate4 subprocesses (a certify file has never carried tool-orchestration duties; the UNION checklist's same-file frozen vector groups get their semantics disturbed); pushci's legacy call surface must stay registered → again a dual canonical home.
- Common to both directions: neither tool's existing CLI, documentation, test vectors, or consumers can be deleted — merging only adds. **The only clearly inferior option among the three.**
- Ruling: **rejected**.

---

## 5 The recommended option and the reasons

**Recommendation: A — keep the two gates side by side, each judging its own question.** Four reasons:

1. **The criterion sets do not intersect; the questions are heterogeneous** (§2.5/§3.1): the two gates share not one duplicated criterion and answer two different questions — "can the environment initiate" and "should the push happen now". The benefit of normalization (eliminating duplication) does not exist here, while the costs (c4 folded into every push, the c1 new-branch deadlock, the eighth roster state, the full schema/documentation/fixture alignment sweep) are all real. No gain, real loss: do not normalize.
2. **The cost structure forbids nesting** (§3.3/§4-B): the minute-scale bulk of c4's full suite fits "paid once when a human wants the window open", not "folded into every automated initiation". Every form of Options B/C must climb this mountain.
3. **The c1 evidence model clashes with pushci semantics** (§4-B): the core of the push-window criteria is the fail-closed honesty law of "corroboration absent = window closed"; the core of the launch-time gate is "probes run now and are judged now". Forcing the former into the latter either creates the new-branch first-push deadlock, or dilutes NOT-RUN with default-passing annotations (pushci's flat-form preflight default-passing precedent already exists, `pushci.py:766-774` — the same technique applied to c1 = the honesty law lost).
4. **A single canonical home for criteria is the only drift-free form** (§4-B/C): the four criteria's canonical home is only in `certify/push_gate.py`; gate A never re-judges them, gate B never reruns the probes — the standing maxim "judging twice is waste, missing one gate is a hole" (whitepaper §4 point 1) is precisely Option A's regulation, already written. The standing arrangement of two gates side by side plus the canonical serial order is already the optimum under this constraint.

**Confirmation of the regulatory status quo (all already on file; this assessment adds zero obligations)**: whitepaper §4 canonical serial order and the three points (`workflow-integration-whitepaper-v1.0-20261111.md:163-201`); the README-cw honest side note (`README-cw.md:60-63`); the embedded section ② two-gates-not-substitutable note (`step-pushci.md:159-161`); the adapter injection / no-surprise-networking contract (`wrapper/push_gate_rq.sh:60-63,71-72`). When v39 scheduled this assessment it noted "the standing two-gate arrangement recorded as-is" (`更新账.md:3609`) — this assessment's conclusion: **side by side is the correct answer; recording it as-is suffices; no code change needed**.

**Residual risk (recorded as-is; inherent to Option A)**: no mechanical check forces a workflow to judge gate B first — pushci alone runs and initiates, and window discipline rests on documentation and the embedded section. This is the self-consistent cost of the "window discipline is initiated explicitly by the caller" philosophy (same origin as adapter contract clause 3), not a gap. If mechanical enforcement is wanted later, Option B is the only path that leaves the criteria canonical home unchanged, but §4-B's four items (especially the c4 cost and the c1 new-branch deadlock) must be solved before revisiting.

---

## 6 The evidence surface (run by this agent, November 11, 2026)

| check | command (wrapped in `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120`) | measured |
|---|---|---|
| gate B self-attestation | `python3 -B certify/push_gate.py --selftest` | rc=0; the UNION six verdicts plus the window c1 dual-source / c2 behind / c4 failing-suite / zero-evidence NOT-RUN four verdicts all passed |
| gate A self-attestation | `python3 -B tools/pushci.py --selftest` | rc=0; the eight vectors + flat interlock + resilience layer + CLI four exit codes all passed (zero real network, zero real push, zero compilation) |
| frozen-roster check | `python3 -B certify/frozen8.py --ledger` output searched for `certify/push_gate` | count = 0 (push_gate is not among the frozen eight) |
| suite status baseline | `bash tests/run_tests.sh` (also attesting the same-round guard-fix regression) | 52 passed / 0 failing / 4 skipped, rc=0 (56 cases; the four skips are source-environment absences; the real machine runs all) |

**Close reading of the code faces**: `certify/push_gate.py` in full, 632 lines (the window four-criteria implementation at `:109-258` + UNION v2 + self-attestation); `tools/pushci.py` docstring and pipeline key sections (`:1-120` header comments and exit-code roster, `:703-843` preflight three checks, `:847-908` push stage, `:1116-1180` run entry); `wrapper/push_gate_rq.sh` in full; the `cw.sh` routes and tool roster; `README-cw.md:40-80`; `docs/workflow-integration-whitepaper-v1.0-20261111.md` §4; `examples/workflows/step-pushci.md:156-167`; the `更新账.md` scheduling anchors.

**Items not run (declared as such)**: pushci's real push stage and push_gate window's live window judgment against a real remote (requires real remote credentials and a real network — user-side; this agent's discipline is zero real network); c4's in-window recursive run against this repository's suite (the criterion behavior is covered on both sides by the push_gate self-attestation vector "c4 failing suite → CLOSED" and this agent's direct suite baseline). Both command shapes are given with the on-tree code as the canonical source; their runtime behavior was not verified live by this agent.
