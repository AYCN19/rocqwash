# `评估-push_gate推窗四判据与pushci归一-20261111.md` — assessment of normalization feasibility between the four push-window criteria of `certify/push_gate.py` and the `tools/pushci.py` preflight checks, under the v36 two-door coexistence status (standalone, read-only assessment, zero code changed), measured November 11, 2026.

> Purpose.  Assess whether the two coexisting doors — the push-window decision in `certify/push_gate.py window` (criteria c1 ci-idle, c2 local>=remote, c3 fetch-clean, c4 cert-green) and the preflight checks in `tools/pushci.py` (toolchain, net, gate4 pre-scan) — can be normalized into one mechanism. Deliverable: this document only; every change form (embedding the window check into the preflight, or sinking the criteria into a shared library) is registered as pending execution, never applied. Scope: the criterion inventories of both doors, the coverage matrix, the conflict surfaces, three normalization options with per-item cost anchors, and a recommendation.
>
> Interface.  Document face only; no runtime interface, and this assessment changed no code face. Every live check listed in §6 was wrapped in `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120` (FRONT tier). The original Chinese text is preserved in the sibling `.zh.md` archive. Line anchors cite the working tree at measurement time and are informational, not a stability contract.
>
> Dependencies.  Read in full at measurement time: `certify/push_gate.py` (633 lines), `tools/pushci.py` (2086 lines), `certify/frozen8.py` (408 lines), and the same-day precedent document `docs/push-gate-dual-door-assessment-v1.0-20261111.md`. The live checks depend on the `cpu_guard.sh` wrapper and the repository's own git history; no network face is involved (the self-tests run against local bare remotes), and this document has no runtime dependency on any code face.
>
> Evidence.  Repository state at measurement: HEAD `8e124b3` (v45, the render_events.py routing registered), working tree clean (`git status --porcelain` ran, 0 lines). The task instruction's header note "v37 41e74b0" was stale — the repository advanced v37 to v45 in flight that day — so every line anchor in this document reflects the current tree state and does not affect the conclusions (the assessed code is the tree's canonical copy). The §6 table records each live check with its command and measured outcome (all rc=0); `grep push_gate tools/pushci.py` returned zero hits. An independent same-day assessment of the same question exists under `docs/`, written by an earlier agent, and reaches the same conclusion (its options A/B/C correspond to this document's B/A/C); the two rulings corroborate each other, while this document's criterion inventory, conflict surfaces and cost anchors were all measured here and inherit nothing.
>
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged: `push_gate.py` window decides OPEN (exit 0) / CLOSED (exit 1) under the register 0/1/2/9 (`push_gate.py:65-67`), and `pushci.py` keeps its fail-loud 9 and its seven-state verdict register (`pushci.py:157-165`).

---

## 0. The disposition ceiling: consult the frozen list first (the list sets the permission)

`certify/frozen8.py:74-83` records the eight-item `LEDGER8`: freeze_manifest.py / mac_stmt_names.py / mac_stmt_scan.py / seam_probe.py / cpu_guard.sh / gate4_comment_guard.py / verify_vo.py / wash_engine.py.

This agent ran `python3 -B certify/frozen8.py --ledger` (wrapped by cpu_guard), rc=0, output exactly eight lines: **`certify/push_gate.py` is not among the frozen eight** (mechanical evidence: the name is absent from the full ledger). The disposition ceiling is therefore nonfrozen-mutable (small changes may be proposed); but the task instruction orders document-only output this round, so the change forms (options A and C below) are registered as pending execution, and this agent changed zero code.

## 1. The four criteria as measured (`certify/push_gate.py`, all 633 lines read in full)

| criterion | what it decides | evidence source | code anchor |
|---|---|---|---|
| c1 ci-idle | CI runs in flight = 0; any status != `completed` is conservatively counted as in flight (fail-closed) | `--runs-json` (a pre-fetched Actions runs JSON; the tool itself makes zero network calls, it only interprets) or `--ci-capped-min N` (the reflog's most recent `update by push` is at least N minutes old, plus a CI duration cap, so in flight is impossible); **no evidence = NOT-RUN = window closed** | `push_gate.py:109-151` (two-source mutual-exclusion check `:219-222`, zero-evidence NOT-RUN `:151`) |
| c2 local>=remote | after fetch, `rev-list --count HEAD..<remote>/<branch>` (behind) == 0; ahead is uncapped (a locally leading tree is exactly the state waiting to push) | git mechanical count | `push_gate.py:154-165` |
| c3 fetch-clean | ls-remote read twice, before and after, with the same sha + fetch rc=0 + the remote sha is an ancestor of local HEAD (`merge-base --is-ancestor`): nobody moved the remote side inside the window | genuine read-only remote operations (fetch/ls-remote); a fetch failure (including a dead-network window) = FAIL, the window honestly closed | `push_gate.py:168-187` |
| c4 cert-green | this repository's certification-passing state re-checked mechanically: `bash tests/run_tests.sh` rc==0 (`--suite` may name the script); optionally `--freeze-manifest` adds a freeze_manifest.py check whose zero-drift result must also return rc==0 | exit codes | `push_gate.py:190-212` |

- Order: **c3 first** (fetch settles the remote-tracking ref; only then do the c1 timeline and the c2 count have a basis), then c1, c2, c4: `push_gate.py:235-239`.
- Conclusion face: all four criteria PASS => `push-window: OPEN`, exit 0; otherwise CLOSED, exit 1 (NOT-RUN closes the window; absent corroboration never counts as passing): `push_gate.py:245-258`; exit-code register 0/1/2/9 (`:65-67`).
- **It decides the window only and never pushes**: the push action belongs to the caller (`:30`); window is read-only throughout (write-domain declaration `:49-50`). The CLI parameter register as measured (`:584-596`): `--repo/--branch/--remote/--runs-json/--ci-capped-min/--freeze-manifest/--suite/--json` — **there is no `--check` flag**; the read-only mode is the `window` subcommand itself (this agent's own self-test vector rc=0 demonstrated that it runs end to end against a local bare remote with zero network).
- The same file also carries union-freeze/union-check (the UNION v2 multi-world register, `:263-396`); unrelated to this assessment and not expanded.

## 2. The preflight checks as measured (`tools/pushci.py`, all 2086 lines read in full)

| check | what it decides | stop on failure | code anchor |
|---|---|---|---|
| (1) toolchain | subprocess `tools/toolchain_dyld_doctor.py --json` (`--worker` auto-detected by default) => verdict != healthy (the dyld linkage-failure surface) | `StopVerdict("toolchain", 1)` | `pushci.py:710-737` |
| (2) net | subprocess `tools/net_probe.py --rounds 2 --interval S --stable-window` (two probes with a stability window) => UNSTABLE | `StopVerdict("unstable", 1)` | `pushci.py:739-744, 750-800` (real mode `:787-795`) |
| (3) gate4 pre-scan (optional `--pre-scan-gate4`) | `git diff --name-only <base>...<branch>` collects the changed .v files, then `verify/gate4_comment_guard.py --file` runs per file (rc 0=PASS / 1=FAIL / 2=review); released only when FAIL=0 (REVIEW is loudly recorded but does not block) | `StopVerdict("gate4-block", 2)` | `pushci.py:746-748, 802-843` |

- After the checks, stages 2-5: push (git always makes exactly 4 calls — get-url, rev-parse, push 3 attempts x 45s, ghproxy reroute 2 attempts, then an ls-remote remote-tip recheck: `:17-24, 847-908`), watch (head_branch + head_sha binding, status-only: `:912-971`), heal (ci_triage classification; bounded rerun for classes B/E; class A is never fixed in place: `:973-1023`), then verdict ± merge.
- Key properties: `--timeout` defaults to 120s on all real subprocesses as a hang guard (kill on timeout + fail-loud 9): `pushci.py:197-207, 2026-2028`; "the pure preflight mode makes zero git calls" `:1166-1167`; the verdict register's seven states `:157-165`; preflight makes zero API calls (the runs query lives in the watch stage, `:930`).
- This agent ran `--dry-run`, rc=0: the plan is exactly the three checks (toolchain/net/gate4 not enabled), no window check, zero git calls, zero API calls, zero tool subprocesses — machine evidence of the three-check structure.

## 3. The comparison matrix: who covers whom, who is unique, where they conflict

### 3.1 Criterion coverage matrix (7 criterion surfaces, none overlapping)

| criterion surface | push_gate window | pushci preflight | coverage relation |
|---|---|---|---|
| CI in flight = 0 (c1) | ✅ `:109-151` | ❌ no in-flight check before the push (the watch stage only sees runs created after the push, `:930-956`) | **push_gate only** |
| behind = 0 (c2) | ✅ `:154-165`, decided in advance | ❌ no pre-scan; the equivalent outcome is git's non-fast-forward rejection at push time, after the fact (rc != 0, 5 wasted attempts, unstable `:863-880`) | **push_gate only** (pushci has only the after-the-fact fallback) |
| nobody moved the remote inside the window (c3) | ✅ `:168-187` | ❌ (the post-push ls-remote `:885-899` collects the remote tip as evidence; it decides no window) | **push_gate only** |
| local certification passing (c4) | ✅ `:190-212` | ❌ the suite does not run locally; passing is judged remotely by watch + heal `:912-1023` | **push_gate only** (different philosophies: passing first locally vs judged remotely afterwards) |
| toolchain health (doctor) | ❌ | ✅ `:710-737` | **pushci only** |
| network stability window (net_probe, two probes, `--stable-window`) | ❌ (c3 proves connectivity + cleanliness only, no timing stability window) | ✅ `:739-744, 787-795` | **pushci only** |
| .v header-comment guard pre-scan (gate4) | ❌ | ✅ `:746-748, 802-843` (optional) | **pushci only** |

Both sides of the task instruction's hints are confirmed in code: **pushci has no behind=0 check** (stage_push runs only a rev-parse existence check, `:852-859`); **push_gate has no network stability window** (c1-c4 make no net_probe call). Interconnection status: `grep push_gate tools/pushci.py` returns **zero hits** (this agent ran it) — the two doors have zero interconnection, pure coexistence.

### 3.2 Conflict surfaces (the same physical condition, treated differently by the two doors)

1. **behind > 0**: push_gate decides in advance: CLOSED, exit 1 (the c2 count plus the c3 ancestry chain, two proofs). pushci discovers it mid-run: push rc != 0, then 5 retry attempts (3 x 45s + 2 ghproxy attempts, about 3 minutes wasted), ending in verdict = **unstable** (semantically filed under "network instability" rather than "wrong timing"), exit 1 (self-test vector 12 anchors this at `:1746-1769`). One condition: timing, verdict name and cost differ threefold.
2. **Dead-network window**: push_gate c3 treats a fetch failure as FAIL and closes the window (`:174-176`); pushci's net UNSTABLE forbids initiation and reports unstable. Both forbid action, but the registers differ (OPEN/CLOSED vs the seven-state verdict); push_gate has no stability-window concept and pushci has no within-window cleanliness concept — complementary, not duplicated.
3. **Subprocess time limits**: pushci's `--timeout` defaults to 120s with kill on timeout and fail-loud 9 (`:197-207`); push_gate c4 runs the full suite directly with no time limit (`run_out`, `:94-100`, no timeout parameter). Under option A a suite longer than 120s is always killed reporting 9 — the two tools' timeout semantics hard-conflict.
4. **The git call-sequence contract**: pushci always makes exactly 4 git calls (docstring `:24`; the self-test asserts exactly 4 calls, `:1497-1502`); push_gate window adds ls-remote x2 + fetch + rev-list x2 + merge-base + reflog, about 7 calls. Option A breaks the 4-call constant sequence = a full refresh of every canned vector.
5. **The preflight's nature**: the current preflight makes zero git calls and zero API calls (`:1166-1167`); option A's fourth check (c3) necessarily touches a genuine remote fetch — the nature changes, and the documentation/vectors/fixtures must all follow in a coordinated update.

## 4. Normalization options proposed (three options, migration cost anchored line by line)

### Option A: the pushci preflight gains a fourth check (a subprocess call to push_gate's read-only mode)

**Read-only premise ruling**: push_gate's CLI has **no `--check` flag** (parameter register as measured, `:584-596`); the read-only mode is the `window` subcommand itself (read-only throughout, `:49-50`; the push action belongs to the caller, `:30`; this agent's selftest rc=0 demonstrated it). The answer to "does its CLI support a read-only invocation" is therefore **yes, but the form is the `window` subcommand, not `--check`** — option A's call form would be `python3 -B certify/push_gate.py window --repo <repo_path> --branch <branch> ...`.

**Technical feasibility**: push_gate.py itself could stay unchanged (the criteria canonical copy untouched; calling it as an orchestration step fits pushci's own "orchestration, zero new engine" wording, `:5-6`); pushci's `_run_py` subprocess form is compatible with window's `--json` output form (`:659-676`). **But four cost items anchor as follows**:

- **a) The c1 evidence deadlock (no solution satisfies both sides)**: without `--runs-json`/`--ci-capped-min`, c1 = NOT-RUN, CLOSED exit 1 (`:151`; the self-test vector "zero evidence NOT-RUN closes the window" demonstrated rc=0), so the fourth check would close the window on every run. Solution one: the pushci preflight pre-fetches the runs JSON = a new genuine API call (the current preflight makes zero API calls; the token credential surface would enter earlier). Solution two: `--ci-capped-min` depends on a reflog `update by push` entry (`:138-142`) — **the first push of a new branch (pushci's main use case) necessarily has no entry, a NOT-RUN deadlock**.
- **b) The c4 time-limit conflict**: c4 runs the full `tests/run_tests.sh` (minutes) against pushci's `--timeout` default of 120s (`:2026-2028`), so it is necessarily killed reporting 9. Relaxing the timeout means the automated pipeline pays the full minutes-long suite on every push; pointing `--suite` at a lighter script hollows out the criterion (certification-passing in name only).
- **c) The contract coordination surface**: the verdict register needs an eighth state (currently seven, `:157-165`; the selftest register assertion `:1811-1813`) + a report-schema `rocqwash-pushci/1` extension + a refresh of the git 4-call constant-sequence assertion (`:1497-1502`) + the dry-run plan lines + `tests/fixtures/pushci_scenarios` + full alignment of the README-cw / whitepaper / embed-block-2 documentation faces.
- **d) The atomicity illusion**: passing the window check does not mean the window is still open at push time (c3's before/after double-read design self-demonstrates that the window is not atomic, `:170-183`) — embedding it in door A creates the illusion "passed the checks = safe"; with the two doors coexisting, each issuing its own record (`window.json` + the pushci report), the evidence stays unmixed.

**Conclusion: technically feasible; enabling the check by default is net-negative (the c1 deadlock and the c4 cost admit no both-sides solution), and the optional-flag form would expand the surface instead of normalizing — not recommended** (matching the precedent document's option B ruling).

### Option B: keep the two doors and state the division of labor in documentation (push_gate = the push-authorization check, pushci = the execution pipeline)

**The status quo is already this form, and the convention is on file** (this agent checked each item):
- README-cw.md:60-63: "the suite-passing / behind=0 push-window criteria are not in this register; check discipline still belongs to `certify/push_gate.py`" (grep confirms the text is in place); `:188` "two doors coexisting — the four push-window criteria x the preflight check".
- `wrapper/push_gate_rq.sh` is in place (ls confirms) — door B's independent invocation face is already adapted.
- cw.sh routes nothing to push_gate (grep confirms zero hits) — door B stays out of the single-command main line; the division boundary is maintained naturally by the consuming side.
- pushci's docstring self-describes "orchestration rather than rebuilding" (`:5-6`) — keeping the criteria canonical copy in certify/ is the substance of that "zero new engine".

**Migration cost: zero code** (this round lands only this document). Residual risk (registered honestly; inherent to option B): no mechanical check forces a workflow to decide door B first — running pushci alone initiates, and window discipline rests on documentation and workflow embed blocks. This is the self-consistent cost of the "push-window discipline is initiated explicitly by the caller" philosophy, not a gap.

**Conclusion: recommended**. The criterion sets have zero intersection (§3.1) and the problems are heterogeneous ("should we push now" vs "can the environment initiate"), so the normalization benefit does not exist while the costs are all real (§4 options A/C) — coexistence is the correct answer.

### Option C: sinking the push-window criteria into a library function imported by both tools

**Frozen-face check**: push_gate.py is not frozen (the §0 run evidence), so there is no frozen obstacle; but its import of the frozen file freeze_manifest reuses `tier1_lines`/`tier2_of` read-only (`:79-88`), so a push_gate refactor must keep the frozen interface as-is (the tier1/tier2 criterion function signatures change in zero ways), and a push_gate md5 change moves its self-test vector group (`:401-567`) and the wrapper injection form.

**Cost list**: extracting c1-c4 into a library reshapes certify's deep structure; after both tools import it, one criterion with two consumers is a drift-prone arrangement; tools/ and certify/ have no package structure (pushci currently imports only the same-directory `_http_backoff`, `:174-176`), so sys.path injection or packaging is required = a structural change; **the c1 evidence model and the c4 cost carry over unchanged** (library-izing does not resolve the semantic conflict: the criterion's ownership changes, and the model conflict between "NOT-RUN closes the window" and "run the probe now and decide now" remains).

**Conclusion: a medium risk of touching frozen-adjacent surfaces, an expanding drift surface, and the core contradiction unresolved — rejected** (the same ruling as the precedent document's option C, "the one clearly inferior option").

## 5. Conclusions and recommendation

**Disposition: option B (keep the two doors, division of labor in documentation)** — this round's deliverable is this document; options A/C are registered as pending execution (if option A is later adopted by decision, §4-A items a/b — the c1 evidence pre-fetch and the c4 time limit — must be resolved first).

Four reasons:
1. **Zero criterion intersection** (§3.1 anchors: 7 surfaces, none overlapping) — the duplication normalization would eliminate does not exist;
2. **The cost asymmetry forbids embedding** (c4's minutes-long suite against the automated per-push pipeline's 120s time-limit cap);
3. **The evidence models conflict** (door B's fail-closed rule "absent corroboration closes the window" against door A's "run the probe now, decide now": putting c1 inside door A either deadlocks new branches or dilutes the honesty rule with a passing default; the flat-mode passing-default precedent `:766-774` cannot be cited for c1);
4. **A single canonical copy of the criteria is the only drift-free form** (the four criteria's canonical copy lives only in `certify/push_gate.py`; pushci references it zero times, grep-confirmed — the current coexistence is already the optimal form under that constraint).

## 6. No-change statement and evidence surface

**No-change statement**: this assessment changed zero code — push_gate.py / pushci.py / frozen8.py / wrapper / cw.sh / tests / README all untouched; the frozen eight (the eight items on frozen8.py's `LEDGER8`), the quad8 domain and `更新账.md` were never read and never touched under the no-touch constraint (the ledger-related conclusions rest on the task instruction, on `pushci.py:3` self-describing the v36 flagship registered on November 11, 2026, and on README-cw.md:188).

**This agent's run evidence** (November 11, 2026; every run wrapped in `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120`, FRONT tier):

| check | command | measured |
|---|---|---|
| frozen list | `python3 -B certify/frozen8.py --ledger` | rc=0; output exactly eight lines; push_gate not listed |
| door B self-test | `python3 -B certify/push_gate.py --selftest` | rc=0; the six UNION criteria plus the window's four criteria — c1 two-source, c2 behind, c4 failing-suite, zero-evidence NOT-RUN — all passed (local bare remote, zero network) |
| door A self-test | `python3 -B tools/pushci.py --selftest` | rc=0; eight vectors + the flat binding + the resilience layer + the CLI's four exit codes, all passed (zero real network, zero real push, zero compilation) |
| door A three-check structure | `python3 -B tools/pushci.py --repo-path <repo> --branch master --dry-run` | rc=0; the plan is exactly three checks, no window check; zero side effects |
| two-door zero interconnection | `grep -n push_gate tools/pushci.py` | zero hits |
| division of labor on file | `grep -n push_gate README-cw.md` / `grep push_gate cw.sh` / `ls wrapper/push_gate_rq.sh` | README:60-63,188 on file; cw.sh zero hits; wrapper in place |
| tree state | `git rev-parse --short HEAD` + `git status --porcelain` | 8e124b3 (v45); working tree clean, 0 lines |

**Code surfaces read**: `certify/push_gate.py` all 633 lines; `tools/pushci.py` all 2086 lines; `certify/frozen8.py` all 408 lines; `docs/push-gate-dual-door-assessment-v1.0-20261111.md` in full (the corroborating precedent).

**Not run (declared honestly)**: (1) push_gate window's online window decision against a real remote (requires real network credentials; this agent's discipline is zero real network; the behavior is covered by the self-test vectors' local bare remote); (2) c4's actual baseline over this repository's suite (not re-run by this agent; the precedent document's same-day measurement of 52 passing / 0 failing / 4 skipped, rc=0, is available for reference, and this agent does not vouch for those numbers); (3) `更新账.md` was never read under the no-touch constraint, so the "v36 registration" rests on the task instruction and the on-disk docstring. None of the three affects the criterion comparison or the option rulings (all anchored in on-disk code and self-test vectors).
