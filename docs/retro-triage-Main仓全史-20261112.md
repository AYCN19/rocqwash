# `retro-triage-Main仓全史-20261112.md` — the Main repository's CI full-history retro-triage measured ledger (retro-triage · zero-code pure measurement), measured November 12, 2026.

> Purpose.  The delivery record of roadmap ⑦'s five-step path, step 1 ("zero code first: the Main historical-run retro-triage" · `docs/勘形-multi-repo-Main仓适配-20261112.md:204-207`). Zero-code, pure measurement: this agent changed no code; the rocqwash working tree gained exactly this one file; the frozen eight, quad8 and the ledger `更新账.md` were never touched (the ledger read-only, cited only). Classification authority rests entirely with the existing tool face `tools/ci_triage.py` (the online `--repo/--run` mode · the same method as the v44 Set precedent · `更新账.md:3821`).
> Interface.  Document face only; no runtime interface. All live measurement went through the GitHub Actions REST API in the report-only form, every execution wrapped in `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120`; credentials come from the `~/.netrc` `machine github.com` line and are never echoed. The v48 watcher state was read directly from `/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48/`. The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  The tool faces `tools/ci_triage.py` (classification), `tools/cw_sentinel.py` (the watcher window), `tools/doc_lint.py` (reference consistency) and `tools/cpu_guard.sh`; `~/.netrc` for the API token; no runtime dependency of this document on any code face.
> Evidence.  Every number is transcribed from the named run-time outputs: the /tmp fetch and triage records named in §1 and §2, the watcher state/events reads (§4), and the self-attestation table in §7; the watcher reconciliation (agree=30, disagree=0) was computed by this agent; the doc_lint full-repository rerun returned VERDICT consistent, exit 0 (§7 row 6). The §8 supplement was added by the tooling agent and carries its own recorded runs. Primary registration: the task instruction's stated form disagrees with the measurement — the instruction states "full history to now ≈ 25 runs · full coverage", while the measured `GET /actions/runs?per_page=100` = **total_count=369** (two workflows: the retired 9.1 build's 338 + the active Main CI 9.3's 31); the measurement governs and the discrepancy is registered as-is (§1).
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged (the inventory GET and all 32 `ci_triage` runs returned rc=0, §7).

> Scope ruling on the instruction-vs-measurement gap: the active coq93 series' 31 runs are **classified individually, every one** (the §2 main table); the retired coq.yml's 338 runs are **inventoried in full, not classified individually** (§1·3 — the scale exceeds the task instruction's named scale, and it is a retired workflow, not this effort's service history · registered as-is, not passed off as measurement). The watcher-coverage reconciliation and the known-history anchors (#16-20/#22/#23/#24/#25+) all fall on the coq93 series and reconcile number-for-number against the §2 main table.

---

## 1. The full-history run inventory (fetched November 12, 2026 · `/tmp/retro_main/runs_full.json`)

### 1.1 The fetch channel

- Command: `bash cpu_guard.sh -MaxWaitSec 120 python3 -B /tmp/retro_main_runs.py`
  (read-only GET · token taken from the `~/.netrc` `machine github.com` line · the same netrc sourcing as ci_triage,
  `tools/ci_triage.py:240-272` · the script never echoes it) — rc=0 · the cpu_guard launch banner printed (MID pos=2).
- Endpoint: `GET /repos/hy7pc8gfmf-dotcom/ConstructiveWorld-Main/actions/runs?per_page=100`
  paged to completion (369 runs = 100/100/100/69 across four pages · three continuation fetches · DUP-IDS=0 · PAGE-END=4);
  the full payload landed in /tmp (outside the repository · zero writes inside the tree).

### 1.2 The two-workflow composition (measured)

| workflow | path | state | runs | run_number | conclusion distribution | event distribution | created range |
|---|---|---|---|---|---|---|---|
| Main CI 9.3 (**the only active workflow**) | .github/workflows/coq93.yml | active | **31** | **#1-#31 with no number gaps** | success 12 / failure 12 / cancelled 6 / skipped 1 | push 24 / pull_request 5 / workflow_dispatch 2 | 2026-11-04T18:57Z .. 2026-11-11T17:35Z |
| Coq CI (**the retired 9.1 build**) | .github/workflows/coq.yml | disabled_manually (the same measured value as the assessment document §1.1) | **338** | #1-#340 with #85/#221 missing (no API record · never-triggered or deleted cannot be distinguished · as recorded) | success 160 / failure 79 / cancelled 99 | push 326 / workflow_dispatch 12 | 2026-09-07T20:23Z .. 2026-11-04T19:35Z |

- coq.yml monthly conclusion distribution (inventory count): 2026-09 = 95 success / 38 failure / 25 cancelled · 2026-10 = 63 success / 71 failure /
  25 cancelled · 2026-11 = 16 failure / 3 cancelled / 2 success (including the final run #340). **This inventory was not classified run-by-run** (scale 338 =
  15× the task instruction's named scale · and it is the retired 9.1 build, not the active service history — individual classification is a separately scheduled candidate and is not passed off as this pass's measurement).
- The 31 coq93-series runs are the common coordinate system of the task instruction's known-history anchors (§3) and the v47/v48 watcher coverage (§4).

## 2. The per-run classification ledger (all 31 coq93 runs + the coq#340 bridge run · 32 runs, all rc=0)

### 2.1 The channel and the command shape

- One run per invocation: `bash cpu_guard.sh -MaxWaitSec 120 python3 -B tools/ci_triage.py
  --repo hy7pc8gfmf-dotcom/ConstructiveWorld-Main --run <id> [--logs] --json
  /tmp/retro_main/tri/coq93_<N>_<id>.json` (this agent's 31 consecutive runs + the single coq#340 run ·
  **32 runs, all rc=0** · the orchestrator `/tmp/retro_main_triage.py` ran wrapped in cpu_guard as a whole).
- The `--logs` convention (the task instruction's "inspect failing builds only · skip passing builds"): the 19 failure/cancelled runs added
  `--logs`; the 13 success/skipped runs used no `--logs` (classification ran on the step-level table · passing builds incurred zero extra network fetches).
- Output: one `rocqwash-ci-triage/1` report per run written to /tmp; the classification spectrum's five families + the passing-build family +
  the UNRECOGNIZED fallback all live in the tool face (`tools/ci_triage.py:3-29` for the classification spectrum · `:165-166` for the run-level
  classification order with the out-of-taxonomy family on top).

### 2.2 The main table (coq93 #1-#31 + coq#340)

classification = the run-level verdict (`tools/ci_triage.py:513-530`); the "watcher reconcile" column = same/different against the v48 watcher state's
seen family (§4); wall clock = job duration_sec.

| run# | id | event | conclusion | branch | classification | action | main evidence line (failed step / mechanism) | wall clock | watcher reconcile |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 41892161661 | push | failure | main | **A-content-red** | fix-content | Build full tree failing (the step-name content family) + gate5/gate2 chained failures | 127s | **outside the window (supplemented this pass)** |
| 2 | 41898362546 | push | failure | main | A-content-red | fix-content | Build full tree failing + gate5/gate2 | 129s | ✓ same A |
| 3 | 41914865932 | push | failure | main | **UNRECOGNIZED** | watch-only | failure · zero failed steps · the Build step hung in in_progress (the runner-lost shape) · out of taxonomy, not force-fitted | 57007s | ✓ same UNREC |
| 4 | 42050566114 | push | failure | main | **E-coqchk-skipped** | rerun-after-stable-window | gate4 failing (the artifact token) + coqchk skipped = both E-signature elements present | 138s | ✓ same E |
| 5 | 42065570836 | push | failure | main | A-content-red | fix-content | Build full tree failing + gate2 | 33465s | ✓ same A |
| 6 | 42151784648 | push | failure | main | A-content-red | fix-content | coqchk full-tree certification failing (the step-name COQCHK family) + gate2 | 29980s | ✓ same A |
| 7 | 42221225472 | push | cancelled | main | **UNRECOGNIZED** | watch-only | cancelled + only the gate2 step failing (the fail-loud sentinel step failing · out of taxonomy) | 1722s | ✓ same UNREC |
| 8 | 42225371642 | push | cancelled | main | UNRECOGNIZED | watch-only | cancelled + only the gate2 step failing | 1957s | ✓ same UNREC |
| 9 | 42230638246 | push | success | main | none | watch-only | all passing · zero failed jobs | 39022s | ✓ passing |
| 10 | 42345007340 | push | failure | main | UNRECOGNIZED | watch-only | failure + only the gate2 step failing | 40785s | ✓ same UNREC |
| 11 | 42397887296 | push | failure | main | A-content-red | fix-content | coqchk full-tree certification failing + gate2 | 1017s | ✓ same A |
| 12 | 42402305184 | push | success | main | none | watch-only | all passing | 1253s | ✓ passing |
| 13 | 42444700994 | push | success | main | none | watch-only | all passing | 1201s | ✓ passing |
| 14 | 42447585809 | push | failure | main | A-content-red | fix-content | gate7 extraction execution (the post-build token) failing + gate2 | 328s | ✓ same A |
| 15 | 42448415112 | push | success | main | none | watch-only | all passing | 1198s | ✓ passing |
| 16 | 42456863184 | pull_request | cancelled | gamma/w3-wave1 | A-content-red | fix-content | cancelled + gate5 failing (the pre-coqchk token → the content family · a failed step is present, so not the cascade) | 61s | ✓ same A |
| 17 | 42457455971 | pull_request | cancelled | gamma/w3-wave1 | A-content-red | fix-content | cancelled + gate5 failing (same as above) | 95s | ✓ same A |
| 18 | 42457899042 | workflow_dispatch | skipped | gamma/w3-wave1 | none | watch-only | job skipped with zero steps (a conditional skip, not a failure · `ci_triage.py:422-425`) | 0s | ✓ passing |
| 19 | 42458352264 | push | success | main | none | watch-only | all passing | 1113s | ✓ passing |
| 20 | 42461341685 | pull_request | cancelled | gamma/gate7-port | UNRECOGNIZED | watch-only | cancelled + only the gate2 step failing | 738s | ✓ same UNREC |
| 21 | 42471831874 | push | success | main | none | watch-only | all passing | 1204s | ✓ passing |
| 22 | 42600735076 | pull_request | failure | fix/unif-l0-deposit | **B-netred** | rerun-after-stable-window | Run actions/checkout@v5 failing (the step-name network family) · matches the known NETRED anchor | 87s | ✓ same B |
| 23 | 42610674504 | push | success | main | none | watch-only | **all passing** (1521s, completed in full · zero failed and zero skipped steps) · disagrees with the task instruction's "zombie · expected E/OTHER" (§3 row #23) | 1521s | ✓ passing |
| 24 | 42663742407 | push | failure | main | E-coqchk-skipped | rerun-after-stable-window | gate4 failing + coqchk skipped = the E signature | 119s | ✓ same E |
| 25 | 42667436985 | push | success | main | none | watch-only | all passing | 1096s | ✓ passing |
| 26 | 42676028568 | workflow_dispatch | cancelled | main | UNRECOGNIZED | watch-only | cancelled + only the gate2 step failing | 156s | ✓ same UNREC |
| 27 | 42859373023 | push | success | main | none | watch-only | all passing | 1169s | ✓ passing |
| 28 | 42876807576 | pull_request | success | fix/unif-l1-g1-witness | none | watch-only | all passing | 1214s | ✓ passing |
| 29 | 42887706384 | push | success | main | none | watch-only | all passing | 1260s | ✓ passing |
| 30 | 43061870614 | push | failure | main | E-coqchk-skipped | rerun-after-stable-window | gate4 failing at 42s + Build skip + coqchk skipped = the E signature | 129s | ✓ same E |
| 31 | 43069611064 | push | success | main | none | watch-only | all passing | 1215s | ✓ passing |
| 340* | 41898362460 | push | failure | main | A-content-red | fix-content | Build full tree failing + gate2 (the retired 9.1 build's final run · the coq.yml series) | 251s | ✓ same A |

\* coq#340 is a coq.yml (retired 9.1 build) run, not part of the coq93 series — the single supplemental classification exists only to complete the
watcher 33-event union reconciliation (§4.3); the remaining 337 coq.yml runs were inventoried, not classified individually (§1.2).

### 2.3 Family distribution and criteria-surface observations (distilled from this pass's 32 runs)

**Family distribution** (the 31 coq93 runs): none×13 (success 12 + skipped 1) / A-content-red×8
(#1,#2,#5,#6,#11,#14,#16,#17) / UNRECOGNIZED×6 (#3,#7,#8,#10,#20,#26) /
E-coqchk-skipped×3 (#4,#24,#30) / B-netred×1 (#22). action distribution: watch-only×19
(passing 13 + out-of-taxonomy 6) / fix-content×8 / rerun-after-stable-window×4 (E3 + B1).
The out-of-taxonomy surface recorded zero UNRECOGNIZED misjudgments and zero force-fits — the fallback is fail-loud by design (`tools/ci_triage.py:22-23`).

Four criteria-surface observations (all direct step-level evidence reads · log-token evidence absent per §2.4-② · recorded as-is):

1. **Step-name-family regex compatibility proven** (each prediction of the assessment document §3.1 hit): Build full tree→A
   (`:136` the CONTENT word build); coqchk full-tree certification→A (COQCHK_STEP `:139`);
   checkout@v5→B (the NET word checkout `:137`); gate5 quarantine(pre-coqchk)→A (the token
   rides on the coqchk substring); gate7 extraction execution(post-build)→A (the token rides on the build
   substring) — matching the assessment document §3.1's five table rows one for one.
2. **The E-signature mechanism proven** (three same-shape cases #4/#24/#30): a gate4 comment guard step whose name contains
   "artifact-only" hits UPLOAD_STEP_RE (`:452`) + the coqchk step skipped = both E-signature elements present
   (`:456-465`); the E classification order precedes the step-name B order (`:473-478`) — the gate4 failing-misrouted-to-B
   concern of assessment §3.1 **did not occur** (in all three cases coqchk was skipped → the E path); the E third element, the GATE-BANNER-ABSENT log confirmation,
   was absent because of the 415 (recorded as-is · not to be read as confirmed).
3. **Two UNRECOGNIZED shapes proven** (Main-specific failing shapes · out-of-taxonomy by design, identified manually):
   ①the runner-lost-mid-step shape (#3: conclusion=failure with zero failure steps · the Build step hung at
   status=in_progress with conclusion=None · wall clock 57007s ≈ 15.8h — note that the assessment document §1.2 cites this
   run id as the 2880min timeout precedent anchor; the measurement gives 15.8h < the 48h cap and conclusion=failure, not
   timed_out · the precedent anchor points at the timeout configuration surface, not at an observed cap-hitting run · both readings recorded side by side, not mutually exclusive); ②the gate2-only failed-step shape (#7,#8,#10,#20,#26: cancelled/failure with only the gate2 axioms sentinel step failing —
   the gate2 step name matches zero regexes (`:136-139`, none of the five family tokens touch it) → out of taxonomy). The gate1/gate3 failing shapes
   did not occur in this pass (the assessment document §3.1 predicts their zero-hit shared surface; the measured main affliction is gate2).
4. **Cascade discrimination proven**: cancelled with steps present and zero failed steps → the B cascade (`:437-441`) had
   **zero instances** in this series (the PR-mirror counterparts #16/#17/#20 and the route run #26 all carried failed steps in their
   cancelled state → each landed in A/UNRECOGNIZED · failing is not swallowed by cancelled); the D zero-step shape also had zero instances (#18 is skipped,
   not cancelled · it takes the `:422-425` conditional-skip path).

### 2.4 Newly proven surfaces (the tool face has since drifted · registered as-is by this agent, zero code changes)

1. **The logs endpoint 415 (the v35 precedent form has drifted)**: all 19 `--logs` runs returned
   `logs-GET: HTTP 415 {"message":"Unsupported 'Accept' header: 'text/plain'. Must accept 'application/json'."}` — the current
   `accept="text/plain"` at `tools/ci_triage.py:348` is rejected by GitHub's current state. This agent's independent dual probe (read-only · the same netrc sourcing):
   `Accept: text/plain` → 415 (the message above, verbatim); `Accept: application/json` → 403
   with an AuthenticationFailed XML at the Azure-signed-URL layer (403/415 sit inside the backoff-retry design ·
   the original codes enter the evidence at `:341-354`, fail-soft recorded). → **classification in this pass ran entirely on the step-name-family / E-signature step-level
   evidence · log-token evidence absent**; the tool-face minor-fix candidate = switch the `--logs` path to `application/json` and follow the
   signed-URL redirect (the assessment document's "minor fix" grade · a candidate for another agent).
2. **Two wall-clock generations**: the cold-compile long-wall generation (#3/#5/#6/#9/#10 · 29980-57007s ≈ 8.3-15.8h) and the fingerprint-
   skip fast-build generation (after #15, passing builds 1096-1260s ≈ 18-21min · failing builds 61-328s) divide between
   November 7 and November 8, 2026 — the cross-read matches the coq93.yml 14-lane parallel fingerprint-skip shape (measured in the assessment document §1.2);
   a trend-level observation only (judgment rule 1's noise-band wording · single-run readings · `docs/perf-profile-v1.0-20261111.md:172`).

## 3. Reconciliation against the known history (the task instruction's anchors, item by item)

| anchor | the task instruction's stated form | measured (this ledger §2) | reconcile |
|---|---|---|---|
| #16-20 | the PR-mirror blind-spot generation | #16/#17 pull_request gamma/w3-wave1 cancelled→A (gate5 failing); #18 route, same branch, skipped→passing; #19 push main→passing; #20 pull_request gamma/gate7-port cancelled→UNRECOGNIZED (gate2-only). The event surface mixes push/PR/route inside one window (November 8, 2026, 06:58-08:04) — the historical pushci PR-path mirror-blind double-mismatch trace (the assessment document §3.2) and the measured window cross-read consistently | ✓ (the classification surface: A×2 + out-of-taxonomy×1 + passing×2) |
| #22 | PR NETRED | pull_request fix/unif-l0-deposit failure→**B-netred** (the checkout failed step proves it directly) — matches exactly the watcher's B-netred×2 at Set#269/Main#22 (`docs/ops-sentinel-长驻手册-v1.0-20261112.md:321`), the verbatim re-check holds | ✓ exact match |
| #23 | zombie [measured · classification expected E/OTHER] | push main **success→none** (1521s completed in full · all 18 steps success, zero failed and zero skipped · job "Rocq 9.3 build + coqchk (self-hosted seed cache, Windows)") · the watcher state likewise records passing. **The measurement disagrees with the expectation · registered as-is** — the "zombie" surface (the shape semantics of a route zombie / a branch-protection zombie and the like) is outside this agent's measured spectrum; the API step-level all-passing state is a mechanical fact | ✗ expected E/OTHER vs measured passing (classification family none) — both kept, neither embellished |
| #24 | failure | push main failure→**E-coqchk-skipped** (gate4 failing + coqchk skipped) | ✓ (conclusion failure · classification E) |
| #25+ | the push series | #25-#31 = push 6 / PR 1 (#28) / route 1 (#26) · passing 5 / failing 2 (#26 out of taxonomy · #30 E) — the push-dominant composition holds (the PR/route runs are on record scattered among them) | ✓ (the series surface) |

## 4. Coverage notes against the watcher's 33 events (the v47 ledger and the v48 state read — two records, not merged, not embellished)

### 4.1 The watcher-side coverage surface (state read directly · `/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48/`)

- events.jsonl carries **33 lines** (all `ci-red` events) = Set 15 + Main 18 (read line by line by this agent · family distribution
  A18/UNREC8/E4/B2/C1 — the same as the watcher manual §4.3 `:336-342`); the run ids of the Main 18 events:
  coq93 #2,#3,#4,#5,#6,#7,#8,#10,#11,#14,#16,#17,#20,#22,#24,#26,#30 + coq#340.
- state.json reads Main seen=**31** (coq93 #2-#31 + coq#340) · Set seen=30 — one more than the v47 ledger's
  "Main 30 runs / 18 failing · state seen 30/30" (`更新账.md:3895`) and the manual §4.3's "30/30 each": the current read adds coq93#31
  (passing · `cw_sentinel.py:589-590/:608/:612` — passing runs enter seen without emitting events · the 33-line events file is unchanged) — the two records are snapshots taken at their own times · this agent's current read is the post-02:00 state of
  November 12, 2026 · recorded side by side as-is, no retroactive adjustment.
- **The structural outside-the-window shortfall proven**: the watcher window is `RUNS_QUERY per_page=30` (`tools/cw_sentinel.py:172`)
  + the repository total 369 > 30 → inside the window there are always the latest 30 runs. The current-state window (created_at descending, rank 1-30)
  is exactly coq93 #2-#31, thirty runs; **coq93#1 is the 33rd-newest run in the whole repository** (rank 31 = coq#340 · rank 32 =
  coq#339 · both created the same second, 2026-11-04T18:57:08Z — a same-second race in ordering) — as long as ≥30 newer runs
  are on record (the current state is 369 and monotonically growing), #1 remains structurally outside the window · the watcher's recorded surface never backfills it. This is the mechanical substance of the task instruction's
  "fill the full-history shortfall": **this pass's #1 supplemental classification = A-content-red** (a cold-compile failure at 127s · the Build
  full tree step failing). Also coq#340 (rank 31 · created the same second as coq93#2, 19:35:12Z) is outside the current-state
  window yet sits in the watcher's seen — recorded by an earlier pass whose window boundary differed at its time · seen never evicts
  (preferring a duplicate over a drop · the watcher manual §3.3 wording) · the difference from the v47 ledger's 30/30 snapshot is recorded side by side as-is, no retroactive adjustment.

### 4.2 The per-run reconcile (this pass's classification vs the watcher state's seen family)

The two sides overlap on **30 coq93 runs · 30/30 families identical · 0 disagreements** (passing 12 + failing 18, matched run by run ·
this agent's machine-check output is on record: agree=30 disagree=0 sentinel_absent=1); the difference surfaces complement each other exactly:
the watcher alone has coq#340 (supplemented by this pass's single run → A · same family as the watcher event ✓) · this pass alone has coq93#1 (outside the watcher window).
**The watcher's 33 events' Main-18 classifications were reproduced item by item by this pass's independent recomputation** — the classification spectrum is stable across time ·
the B/E/A/UNREC families show zero drift.

### 4.3 The union accounting (the watcher's 33 events × this pass's 32 runs)

- The Main-side failing-build union = **19 distinct runs** (coq93 18 + coq#340) · **all measured directly in this pass**;
  the union family distribution: A-content-red×9 (#1,#2,#5,#6,#11,#14,#16,#17,#340) /
  UNRECOGNIZED×6 / E-coqchk-skipped×3 / B-netred×1. The watcher's Main-18 = the union's 19 minus this pass's
  supplemental #1, leaving 17 + #340 (identical). The passing-build union: coq93 13 (all recorded seen in the watcher state).
- The Set-side 15 events were **not re-classified** in this pass (the v44 Set precedent already retro-triaged the full 30-run history · `更新账.md:3821`;
  this pass's scope = the Main repository — named by the task instruction). Cross-read of the 33-event total: Set 15 + Main 18 = 33 (identical);
  the union's new information = the Main failing run #1 (the watcher's structural blind spot) + the coq.yml 338-run inventory ledger.

## 5. Conclusions

1. **Classification agreement**: all 31 coq93 full-history runs classified individually · 30/30 families identical, zero disagreements on the surface shared with the watcher's 33 events ·
   four of the five known-history anchors match and one does not (the #23 zombie expected E/OTHER vs the measured passing · both kept as recorded) —
   the v44 Set precedent's "classification matches the actual state item by item" reproduces on the Main repository.
2. **The history shortfall filled**: the watcher's structural outside-the-window blind spot (the per_page=30 window × the 369 total) was filled this pass by
   the per_page=100 full inventory + the full coq93 classification · #1 (A-content-red) is the only failing run the watcher can never see ·
   now on record.
3. **Two new tool-face proofs** (registered with zero code changes · minor-fix candidates): the logs Accept 415 (§2.4 item 1) +
   the two Main-specific out-of-taxonomy failing shapes, gate2-only and runner-lost, now on record (§2.3 item 3 · the classification spectrum's "no force-fit"
   is by design · a spectrum-extension candidate requires manual identification before separate discussion · mechanical force-fitting is forbidden).
4. The coq.yml (retired 9.1 build) 338-run individual classification = a separately scheduled candidate (this ledger only inventories · it is not passed off as measurement).

## 6. Boundaries and as-recorded notes

1. This agent actually ran: the full-history inventory GET×1 · 32 ci_triage runs (31 consecutive + the coq#340 single · all rc=0) ·
   the logs dual probe ×1 · direct reads of the watcher state/events · the doc_lint rerun (§7). **Not run**: the coq.yml
   337-run individual classification (outside scope · §1.2) · the pushci/unclog selftests (cited on the ledger, not part of this pass).
2. The classification evidence surface = step-level (the step-name-family regex + the E step-level signature) · log-token evidence absent (the 415 · §2.4 item 1)
   — conclusions of the "GATE-BANNER-ABSENT-style token confirmation" kind were claimed nowhere in this pass.
3. The #23 zombie expectation disagreement is kept as recorded on both sides (§3 row #23); the "zombie" semantics are outside the API-measured spectrum.
4. The difference between the watcher state's seen=31 and the two records' 30/30 is recorded side by side as-is, no retroactive adjustment (§4.1); the reconciliation base =
   the current read of the v48 three-artifact set + the verbatim quotes from the v47 ledger text.
5. The /tmp outputs (runs_full.json / tri/*.json) are volatile; every number in this ledger was transcribed from them; the repository
   gained exactly this one file · zero git operations · the frozen eight / quad8 / `更新账.md` never touched.
6. **Line-number freshness + concurrency note**: this ledger's tool-face line-number anchors = the working tree at this agent's start time (the committed state of v48 `325b4dc`) · at the pre-submission verification the working tree showed a concurrent agent's in-flight minor fixes (`git diff tools/ci_triage.py`, three hunks, all inside the docstring / the `〔九〕` selftest vector area · KEY_LOG_PATTERNS / the step-name regexes / classify / run_verdict / accept= and the other classification paths zero changes — this agent's grep machine-check found 0 hits) ·
   this agent's 32 measured runs behaved identically under both versions · line-number citations follow the start-time state (concurrent development drifts; on tool-face conflicts the
   `--help`/docstring is the authority · the same precedent as the watcher manual's appendix item 3).

## 7. This agent's self-attestation record (November 12, 2026 · all wrapped in cpu_guard)

| # | action | result |
|---|---|---|
| 1 | `python3 -B /tmp/retro_main_runs.py` (the full-history inventory GET) | rc=0 · total_count=369 fetched=369 DUP-IDS=0 PAGE-END=4 (§1) |
| 2 | `python3 -B /tmp/retro_main_triage.py` (the 31 consecutive coq93 `ci_triage --repo --run` runs) | rc=0 · TRIAGE-DONE n=31 family_hist={A8,UNREC6,E3,none13,B1} (§2) |
| 3 | `ci_triage.py --repo … --run 41898362460 --logs` (the coq#340 bridge single run) | rc=0 · A-content-red (§2 main table, last row) |
| 4 | the logs dual probe (text/plain vs application/json · job 126871747925) | 415 (the message recorded verbatim) / 403 Azure XML (§2.4 item 1) |
| 5 | direct read of the v48 watcher three-artifact set (state/events/report) | Main seen=31 · events 33 lines, Main 18 · reconcile agree=30/disagree=0 (§4) |
| 6 | `python3 -B tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash` | **VERDICT consistent (exit 0)** · for this ledger refs=18 unresolved=0 oos=0 drift=0 · all three checks zero drift repository-wide (run by this agent after this ledger's drafting · the same round as the §6 item 6 note) |

---

## 8. Tool-face minor-fix implementation notes (November 12, 2026 · the tooling agent's triage-fix supplement · carries the §2.4 item 1 candidate and the two §2.3 item 3 shapes)

> **Section scope**: a later tooling-agent supplement (not the original measurement agent's §1-§7 handwriting) — the classification spectrum order
> UNRECOGNIZED>C>A>E>B>D is **unchanged**; two tool-face minor fixes + two fixtures + the selftest vector block.
> The 32-run classification table in §2 is the record made under the then-current tool face and is **not rewritten retroactively** · the current tool face's classification changes for the same-shape data are registered item by item (§8.3). All real runs were wrapped in
> `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120`.

### 8.1 The logs-endpoint 415 fix (the §2.4 item 1 candidate implemented · the Accept value settled by measurement)

- The measurement probe (read-only GET · job 127903477736 = this ledger §2 run#3's failing job · the same netrc sourcing ·
  the token never echoed): `Accept: text/plain` → 415, the message verbatim (the same shape as §2.4 item 1);
  `Accept: application/vnd.github+json` → **302 Location** (an Azure-signed URL ·
  `application/vnd.github.v3.text` also 302 · the standard form taken); the second hop to the signed URL with
  **zero Authorization** → **200**, the real log 1,673,483 bytes; the control forwarding the token → 403 Azure AuthenticationFailed XML — the mechanism of the §2.4 item 1 dual-probe 403 shape is proven:
  urllib forwards the Authorization header along with the redirect by default · two hops with zero authentication is the fix.
- Tool-face touchpoints: the LOGS_ACCEPT constant at `tools/ci_triage.py:122` + the `_NoRedirect`
  auto-redirect-disabling handler at `:368` + the two-hop rewrite of `fetch_job_log` at `:387` (the first-hop
  backoff-retry semantics for 403/429/5xx preserved · 404/415 original codes still enter the evidence as before · a second-hop failure enters the evidence without retry).
- A real post-fix run as proof (run by this agent): `python3 -B tools/ci_triage.py --repo
  hy7pc8gfmf-dotcom/ConstructiveWorld-Main --run 42221225472 --logs --json
  /tmp/triagefix_r7.json` → rc=0 · run#7's failing job 127903477736 fetched its log with 200 ·
  the evidence captured 3 GATE-BANNER-ABSENT token lines · zero 415 annotations (the §2.4 item 1 "log tokens
  absent" debt discharged).
- The selftest gained canned vectors (`tools/ci_triage.py:1300`, `〔十〕` item 4): the post-fix shape
  hop1 Accept=LOGS_ACCEPT → 302 → hop2 zero Authorization → 200 as a two-hop assertion + the three negatives 415/403/
  redirect-without-Location with original codes entering the evidence (zero network · `_open` injection).

### 8.2 The gate2-only cascade shape enters the taxonomy (an E variant · the manual identification of §2.3 item 3's observation ② landed)

- **Rule provenance = the six UNRECOGNIZED events of this ledger's §2 main table (#3/#7/#8/#10/#20/#26)**: among them
  the **five gate2-only-shape runs #7/#8/#10/#20/#26** (only the gate2 axioms sentinel failing · the preceding
  build/coqchk not content-failing · no other failed step) were manually identified as the "missing coqchk artifacts · gate2
  cascade" family = the E variant; **the #3 runner-lost shape (failure · zero failed steps) stays out of taxonomy, not force-fitted** —
  the six events are recorded together, five admitted, one held (the §5 item 3 discipline "a spectrum extension requires manual identification", carried out through the task instruction's identification).
- The criteria (`tools/ci_triage.py:164` GATE2_STEP_RE + the classify E-variant branch at `:558`):
  the failed-step set ⊆ {gate2 + the upload family} and **a pure gate2 failed step on record** (a gate2 name that is not an upload name — guarding
  against the "Upload artifact (gate2 ledger)" name's incidental gate2-substring match swallowing an upload failure · the negative-evidence vector
  is on record) → family=E-coqchk-skipped · action=rerun-after-stable-window ·
  the evidence notes the gate2-only cascade; a GATE-BANNER-ABSENT log token on record is the third confirming element.
  The action follows the E-family disposition table's uniform rerun-after-stable-window (the network-involved /
  watch-only split has no evidence surface in these five runs · not stipulated, as recorded); #7/#26 whose build step has
  conclusion=cancelled (not in the failed-step family) classify the same — the criteria surface is "not content-failing", not a strict "success/skipped" surface.
- The log semantics confirmed (the post-§8.1-fix path · the original sentence captured from run#7): the gate2 sentinel's own statement —
  "_chk_all.log not on disk — coqchk produced no log (the upstream gate4/build abort cascades · look to the upstream step for the failing cause) ·
  not a COQLIB generation loss" — matching the E-variant criteria word for word.
- Two fixtures (their true shapes transcribed field by field from this ledger §2 main table's 32-run output records · `_provenance` on record):
  `tests/fixtures/ci_triage_gate2_only_cancelled.json` (run#7 · job
  127903477736 · the true cancelled 18-step shape) / `ci_triage_gate2_only_failure.json`
  (run#10 · job 128320751675 · the true failure 18-step shape). The selftest's positive verdicts hit both
  + five negative verdicts (build failing + gate2 failing → A · coqchk proper failing + gate2 failing → A · a gate2
  substring incidental upload failure → B · a lone tree-stats failure → UNRECOGNIZED · the #3 zero-failed-step shape → UNRECOGNIZED,
  not force-fitted) (`tools/ci_triage.py:1300`, `〔十〕`).

### 8.3 The current-state classification cross-read (the §2 main table not rewritten retroactively · recorded side by side as-is)

The five runs #7/#8/#10/#20/#26 classify under the current tool face as E-coqchk-skipped (rerun-after-stable-window)
· #3 remains UNRECOGNIZED — the §2.3 family distribution's UNRECOGNIZED×6 is the then-current tool-face snapshot · the same data
classifies now as UNREC×1 + the E variant×5 (run#7's current-run proof on record at §8.1). The §4 watcher-reconcile 30/30
exact-match conclusion is unaffected (the classification change is a family-name migration only · the failing-run set is unchanged).

---

## 9. Maintained-UNRECOGNIZED two-shape signature notes

> **Section scope.** §2.3 item 3 recorded two Main-specific out-of-taxonomy shapes
> (the runner mid-step loss; the gate2-only failed step). The token-level ground truth for
> both is the review ledger `docs/复核-UNREC-14事件-20261112.md` (`§二` S3/S6,
> `§三`-4/`§三`-6, `§四`-2/`§四`-3). This section fixes the two maintained-UNRECOGNIZED
> signatures and their engine evidence notes. The taxonomy and the run-level
> precedence (UNRECOGNIZED > C > A > E > B > D) are unchanged: both shapes stay
> `family=UNRECOGNIZED` (action `watch-only`) — the supplement adds evidence
> annotations, one canned fixture, and selftest vectors, nothing else (never
> force-fitted into any family).

### 9.1 Shape ① — runner-lost candidate (Main coq93 run #3, id 41914865932)

- Signature (four legs, all from the review ledger `§二` S3/R1 step-level
  evidence): job `conclusion=failure` with zero failed steps; the build step
  "Build full tree (order topology, fingerprint skip, thermal-guarded)" still
  hung at `status=in_progress` with `conclusion=null` while the remaining
  steps stay pending; wall clock 57007s ≈ 15.8h — below the configured cap
  and not `timed_out`; the job-log GET returns HTTP 404 BlobNotFound (the log
  blob was never uploaded — the companion evidence of a runner lost mid-step;
  `§三`-6 records the same double-404 for the Set#284 Windows job).
- Engine form (`tools/ci_triage.py` classify): when all four legs hold — the
  fourth leg being the logs-GET HTTP 404 evidence note, carried online by
  `fetch_job_log` or offline by the `job_log_notes` canned extension —
  classify emits the evidence-package note `runner-lost-candidate` (hung
  build step names, wall clock, 404) plus the maintained rationale line, and
  returns `UNRECOGNIZED`/`watch-only` unchanged. The D shape (cancelled +
  zero steps) does not cover it; no family is assigned.
- Fixture `tests/fixtures/ci_triage_runner_lost.json`: job-level fields from
  a fresh GET; the step table transcribed from the surviving triage record of
  the ledger (the live API no longer serves the step table for this job —
  `steps=[]` on a fresh read, and the check-runs endpoint carries
  `output.steps: null`); `job_log_notes` carries the real HTTP 404
  BlobNotFound note text captured by a direct log-fetch probe. Selftest
  vectors: the positive fixture plus four negatives (no note / note without
  404 / hung non-build step / failed steps present) and a byte-identical rerun.
- Live-read boundary (recorded as-is): a fresh re-triage of run #3 returns
  `UNRECOGNIZED` without the annotation, because the pruned `steps=[]` also
  removes the hung-step leg from the live step table and the `--logs` fetch
  list selects jobs with steps; the four-leg shape is observable through the
  canned fixture (and the 404 leg is still directly observable — the blob is
  still absent on a fresh probe).

### 9.2 Shape ② — attested-red auth-state maintained (Main coq93 run #10, id 42345007340)

- Signature (review ledger `§二` S6/R4, `§三`-4, `§四`-2 token split): genuinely
  executed (dump-line-filtered) `判定=CLEAN(exit 0)` with axiom total 0
  together with `GATE2-ATTEST-RED` — parser CLEAN yet the attestation
  coverage assertion failing (the R4 partition break, appendix absent), with the
  coqchk step completed (40398s). The E gate2-only cascade variant does not
  hold for attested-red shapes (`§四`-3: forcing it there would be a false
  positive — the manual verdict stays UNRECOGNIZED).
- Engine form: the gate2-only shape keeps its exclusion note, and classify
  now additionally emits `auth-state-red-maintained` when both tokens are
  genuinely present on dump-filtered log text — the note carries the UNREC
  maintained rationale automatically (the E cascade variant does not hold; the manual
  identification takes precedence; no force-fit). A single attestation token
  without the pair keeps the plain exclusion note. Family stays
  `UNRECOGNIZED`/`watch-only`.
- Fixture `tests/fixtures/ci_triage_gate2_only_failure.json` (canned
  genuinely-executed lines plus one dump line) carries both tokens; the
  selftest asserts the pair note on it, plus two single-token negatives.
