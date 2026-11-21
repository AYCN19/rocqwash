# `勘形-multi-repo-Main仓适配-20261112.md`: the Main repository CI adaptation shape-survey for the rocqwash tooling (roadmap ⑦ multi-repository extension · read-only · zero code changes), surveyed November 12, 2026.

> Purpose.  The shape-survey face ahead of roadmap ⑦ "multi-repository extension" (the candidate at `docs/roadmap-v43-plus-20261111.md:84-92`): the "Main repository CI shape survey" that gates that candidate. **Read-only, zero code changes**: this agent changed no code, and the rocqwash working tree gained exactly this one file; the frozen eight, quad8 and the ledger `更新账.md` were never touched (the ledger is cited read-only). **Criterion**: the Main repository CI structure is taken as measured (api.github.com read-only GET over netrc · the token is never echoed · every execution wrapped in cpu_guard); every point where the task instruction's stated shape disagrees with the measurement is registered item by item (§1.3). **Grading**: ready as-is (usable with zero changes) / minor fix (fixture, procedure or wording level) / medium change (structural blind spot or data-surface engineering).
> Interface.  Document face only; no runtime interface. All live measurement went through read-only GET calls against api.github.com with the token sourced from the `~/.netrc` `machine github.com` line (the same netrc sourcing as `tools/ci_triacy.py`; the scripts never echo the token), every execution wrapped in `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh`. The grading verdict is §4, the recommended path is §5, the boundaries and as-is records are §6. The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  The /tmp fetch scripts `/tmp/fetch_main_ci.py` and `/tmp/fetch_main_tree.py` (read-only GET; named in §1.1), `tools/ci_triage.py` (--selftest), the Set repository workflow file /Users/apple/Desktop/ConstructiveWorld-Set/.github/workflows/coq.yml (read in full), `~/.netrc` for the API token, and `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh` around every execution; no runtime dependency of this document on any code face.
> Evidence.  Every value labeled "measured" is transcribed from the named run outputs: the two rc=0 fetch runs (§7 rows 1-2), the ci_triage --selftest PASS rc=0 (§7 row 3), the full read of the Set coq.yml (§7 row 4) and the doc_lint rerun (§7 row 5). Line-number citations for the Main repository's two workflows refer to the fetched /tmp copies (remote ref=main HEAD at fetch time; `/tmp/mainwf_coq93.yml` named in §1.1); citations for this repository's tool faces refer to the working-tree files under the v47 `6217808` criterion (§6.5). pushci/unclog --selftest were **not** rerun by this agent (on record rc=0 from v36/v41 · `更新账.md:3591`/`:3740` · §6.1).
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged. Every run recorded in §7 and §9 returned rc=0.

---

## 1. The Main repository CI shape as measured (November 12, 2026 · api.github.com netrc GET)

### 1.1 The fetch channel and the repository meta

- Channel: `/tmp/fetch_main_ci.py` (read-only GET · the token is taken from the `~/.netrc` `machine github.com` line's password, the same netrc sourcing as `tools/ci_triacy.py` · the script never echoes the token).
  Both scripts were run for real: `python3 -B /tmp/fetch_main_ci.py` and `python3 -B /tmp/fetch_main_tree.py` (both rc=0 · wrapped in cpu_guard).
- **REPO-META (measured)**: `hy7pc8gfmf-dotcom/ConstructiveWorld-Main` default_branch=**main**
  private=False size_kb=34468 **push_perm=True** (the netrc token carries push permission on the Main repository,
  the credential face of the v36 note "the live-push segment needs real remote credentials · the user face" (`更新账.md:3608`) is in place in the current state).
- **workflows (measured GET /actions/workflows)**: total_count=2:
  | workflow | id | path | state |
  |---|---|---|---|
  | Coq CI (9.1 build) | 352580515 | .github/workflows/coq.yml | **disabled_manually** (dormant) |
  | **Main CI 9.3** | 407286573 | .github/workflows/coq93.yml | **active (the only active one)** |

  The full text of both files was fetched into /tmp (coq93.yml=606 lines · coq.yml=457 lines); the line numbers cited in this section refer to the
  fetched copy `/tmp/mainwf_coq93.yml` (remote ref=main HEAD at fetch time).

### 1.2 coq93.yml (Main CI 9.3), the active shape read in full

| face | measured | lines |
|---|---|---|
| Triggers | push branches **[main]** + pull_request + workflow_dispatch (macos_only input · the file-header comment notes itself "template residue · harmless") | `coq93.yml:40-49` |
| Concurrency group | **single fixed group `cw-main-ci-93` + cancel-in-progress: true** (unlike the Set per-ref pool · see §3.2) | `coq93.yml:51-54` |
| Job count | **single job `coq-build` (Windows self-hosted), no mac observation job** (the header states plainly "mac observation omitted (the Main base has no mac job block · registered as-is)") | `coq93.yml:58-66` · `:32-33` |
| timeout | 2880min (the 48-hour cold-build wall · the run 41914865932 precedent) | `coq93.yml:70-74` |
| checkout | **actions/checkout@v5 fetch-depth:1, not an API tarball** | `coq93.yml:89-91` |
| Toolchain | job-env shape A 9.3 injection (COQC/COQCHK/COQLIB/ROCQLIB → opam-root default 9.3) | `coq93.yml:75-87` |
| Certification tree | **the ConstructiveWorld_vo tree** (build/chk/gate5/gate2 all on vo); the Live tree sees only the gate1/gate4 wording scans | `coq93.yml:105-107` · `:131-133` · `:417` · `:564` |
| Build shape | parallel_build.sh **14 lanes in parallel** (BLDJ_JOBS=14 · fingerprint skip · not a cold build) · pwsh cpu_guard_v3.ps1 thermal guard | `coq93.yml:247-368` |
| coqchk shape | parallel_chk.sh **14-way shared closure** (CHK_JOBS=14 · CHK_TREE_COPY=1) · the ATT-RECON skip list + the W3 full-coverage backstop every 20 rounds | `coq93.yml:479-529` |
| Gate step spectrum | gate1→gate4→gate3→Seed→RAM guard→Build→tree-stats→gate5→attest reconcile→coqchk→Upload cache→gate2→Upload logs (all 14 steps listed as measured) | `coq93.yml:102-605` |
| Log wording faces | GATE-BANNER-ABSENT/GATE-BANNER-FAIL/GATE2-AXIOMS-RED/GATE5-RED/GATE5-NOSCANNABLE/GATE4-RED/ATT-RECON-FAIL/DEP-CASCADE/W3-BACKSTOP | `coq93.yml:565` · `:569` · `:586` · `:424-428` · `:137` · `:467-470` · `:335` · `:507` |

### 1.3 The instruction's stated shape versus the measurement (two disagreements · the measurement governs · registered as-is)

1. The instruction states "Windows single lane / cold build / **two mac observation jobs**"; measured: a **single** Windows
   job (mac observation omitted · stated plainly at `coq93.yml:32-33`); the build is a fingerprint-skip 14-lane parallel
   build, not a cold build (the cold-build shape is the current active shape of the **Set repository** coq.yml:21/:30). The "two jobs" shape is the Set repository's
   active shape (Set coq.yml:19-735, two jobs). Suspected conflation of the two repositories' shapes · the measurement governs.
2. The instruction states "**API tarball checkout**"; measured: the Main coq93.yml uses actions/checkout@v5
   (`coq93.yml:89-91`); the API tarball checkout (the ref quiescence supersede gate + tarball
   fetch · the dual-store lesson of November 9, 2026) is the **Set repository** coq.yml:39-88 shape.

### 1.4 The tree surface as measured (`/tmp/fetch_main_tree.py` · rc=0)

- root: the two trees `ConstructiveWorld_Live/` + `ConstructiveWorld_vo/` + the root `_CoqProject`
  (3743B) + `build.sh` + the root `cpu_guard.ps1` (an old shim · the Set repository carries the same note pointing at the infra canonical copy).
- The dual-ledger PATH-PROBE (HTTP codes as measured): Live/order.txt **200** (35384B) · Live/_CoqProject **200**
  (19862B) · vo/order.txt **200** (33752B) · vo/_CoqProject **200** (18788B) ·
  **root/order.txt 404** · root/_CoqProject 200.
- Live top-level entries=**1000** (truncated by the contents API's single-page cap · registered as-is) · .v within the single page=**995** (a lower bound;
  the note at `coq93.yml:101` gives "Live 679/vo 700", the September 25, 2026 gate1 tree state · a different time point yields a different count · both numbers are recorded and are not mutually exclusive).
- **No local Main repository checkout exists** (measured `ls -d /Users/apple/Desktop/*Main*` empty); the basis of §3.3's source-tree ruling.

---

## 2. The Set repository coq.yml active shape (comparison · read in full from /Users/apple/Desktop/ConstructiveWorld-Set/.github/workflows/coq.yml)

| face | Set active (read) | Main coq93.yml (measured) | difference grade |
|---|---|---|---|
| Triggers | push[main] + pull_request + route (macos_only) | same | same shape |
| Concurrency | **per-ref pool `cw-main-ci-${{ github.ref }}` + cancel-in-progress: false** (:15-17 · PR certification queues separately from main pushes) | single group cw-main-ci-93 + cancel-in-progress:true | **different** |
| Jobs | two jobs: coq-build (Windows certification) + coq-build-macos (macOS observation · :439-735) | single job (mac omitted) | **different** |
| checkout | API tarball + ref quiescence supersede gate (:39-88) | actions/checkout@v5 | **different** |
| Certification tree | **single Live tree** (gate1/4/6/7/5/coqchk/gate2 all on ConstructiveWorld_Live · order.txt on Live at :199/:289) | vo-tree certification + Live wording scan | **different** |
| build | cold build (15 items · minute-scale · :167-168) with the pwsh thermal guard | 14-lane fingerprint-skip parallel | **different** |
| coqchk | shared-closure single pass -o (ci_coqchk_live.sh) · the mac lane's inline loop prints **COQCHK_EXIT/COQCHK_ALL_PASS** (:671-673) | parallel_chk.sh 14-way (the wording output awaits the retro-triage evidence) | partially different |
| Registry ledgers | root _CoqProject + the Live dual ledger (no root order.txt · measured by ls) | root _CoqProject + **the Live dual ledger + the vo dual ledger** | Main carries one extra set |
| Thermal guard | pwsh cpu_guard_v3.ps1 (Windows) + the local cpu_guard.sh (mac :538/:542/:667) | pwsh cpu_guard_v3.ps1 | same shape |

- The classification-spectrum wording face is identical across both repositories: GATE-BANNER-ABSENT carries the same token in both (Set :714 / Main :565 /
  `ci_triage.py:114`): the E-family evidence wording that ci_triage keys on is present across repositories.

---

## 3. The adaptation gaps item by item (rocqwash tool faces × Main CI · four faces)

### 3.1 The ci_triage five-family classification × Main step names (compatibility table · the classification table `tools/ci_triage.py:25-29`)

| Main failing step (measured step name) | step-name regex hit (:136-139) | classification | grade |
|---|---|---|---|
| Build full tree (…) (:247) | build→CONTENT | **A-content-red** | compatible |
| coqchk full-tree certification (…) (:479) | coqchk→CONTENT/COQCHK_STEP | A / E-family counterpart | compatible |
| Upload coqchk logs (:591) / Upload vo trust cache (:538) / Upload tree-stats (:382) | upload→NET/UPLOAD | B / E family (E = the upload step failing + coqchk skipped · with both Main conditions present, E can fire) | compatible |
| gate5 vo-binary quarantine (pre-coqchk…) (:411) | **contains the coqchk substring → CONTENT** | A (classified content-red · semantically a content failure · acceptable) | compatible (rides on the wording) |
| attest reconcile (…miss -> coqchk…) (:455) | **contains the coqchk substring → CONTENT** | A | compatible (rides on the wording) |
| Seed trust cache from local vo tree (:171) | cache→NET | B (when failing · mostly environment/path · the B fallback is acceptable) | compatible |
| **gate1 poison-token guard** (:102) | **zero hits** | **UNRECOGNIZED fallback** (when no log is given) | fallback · no misattribution |
| **gate3 cross-tree require-face diff** (:151) | **zero hits** | **UNRECOGNIZED fallback** | fallback · no misattribution |
| **gate4 comment guard (…artifact-only)** (:127) | **artifact→NET judged first** (the classification order judges step-name B before step-name A · :473-478) | when failing, **misclassified as B-netred** | **wording trap** (the same name and the same trap at Set :120 · not new in Main) |

- Log wording (--logs · KEY_LOG_PATTERNS :109-123): GATE-BANNER-ABSENT/`公理总数`/COQCHK_EXIT
  etc. are present in Main (:565/:571); **the Main-specific failing wordings (GATE2-AXIOMS-RED/GATE5-RED/
  ATT-RECON-FAIL/SINGLE-TREE-POISON/DEP-CASCADE) are not rostered → the evidence is thin but the family assignment is not blocked**
  (the step-name regex already covers the A faces · gate1/gate3 fall to UNRECOGNIZED pending manual identification; the classifier's by-design
  honesty: it never fabricates a family · :22-23/:493-495).
- The C-family wordings (EXIT=134/Abort trap: 6 · :132) are the mac-precedent shape; the Main Windows build link-failure log shape is unproven;
  run-level bulk C assignment (two same-shape content failures escalate to C · :498-510) is unaffected.
- **Verdict: the five-family skeleton is ready as-is** (a genuinely failing run is never missed: the worst case, UNRECOGNIZED, is loud ·
  no misattribution, no fabricated families); extending the canned fixtures to the Main shape (§4 item ②) plus the gate4 step-name
  wording trap and the optional Main failing-wording extension = **minor fix**.
- Tool-face self-proof: `python3 -B tools/ci_triage.py --selftest` run by this agent: **PASS rc=0** (November 12, 2026).

### 3.2 pushci pushing to Main (the mirror-blind face · `tools/pushci.py`)

- **Compliant faces (ready as-is)**: ① the remote URL derives ORG/REPO as the last two segments (`repo_from_url` :264-284 · the host
  is unrestricted) → hy7pc8gfmf-dotcom/ConstructiveWorld-Main ✓; ② the ghproxy rerouting gate requires the remote URL
  to carry the `https://github.com/` prefix (`ghproxy_url` :287-292) → the Main shape complies as-is; ③ the netrc token
  carries **measured push_perm=True** on Main (§1.1).
- **The structural gap (the largest gap · medium change): the PR route's mirror-blind double mismatch**:
  1. The push allowlist is **[main]** (`coq93.yml:41-42`) → a pushci push of a topic branch triggers nothing =
     structurally no run to watch (not a mirror problem · the trigger surface itself has none).
  2. A PR-triggered run's head_sha is the merge commit (generated on refs/pull/N/merge) ≠ the pushed tip →
     the watch's two-key match on head_branch + head_sha (:942-944) **must mismatch**; refs/pull/* never enters the git
     mirror/push surface, and `ls-remote refs/heads/<branch>` (:885-886) cannot see it either;
     **the task instruction's "refs/pull/* does not enter the mirror" precedent holds as measured, and the merge-sha mismatch stacks on top of it**.
  3. pushci has no workflow_dispatch call face (the API surface = the four shapes runs GET / rerun POST / pulls GET / merge PUT
     · :1009-1011/:1071-1112) → the route path is blocked too.
  → **The only pushci route compatible with Main = push directly to refs/heads/main** (a push event · head_sha = tip,
  so the match holds); for the PR route, either change the watch-match semantics (a tool change · medium change) or set a procedure that the PR route must not go
  through pushci (zero code · the latter recommended first).
- **The behavior difference (minor fix)**: Main's single concurrency group + cancel-in-progress:true (:51-54) versus Set's
  per-ref no-cancel: under Main a new push cancels the in-flight run → a collective-cancellation loop in the heal rerun face (a cancelled run has
  steps but zero failing steps = the B cascade → rerun → cancelled again… until --max-heal is exhausted, exit 1). Taming with zero tool changes:
  the `--watch-max-rounds` safety valve (:2024-2025 · over the cap fail-loud 9) + a procedure-table note.
- **The match-window note (not a live defect)**: RUNS_QUERY is a single page of per_page=30 (:152/:698-699 carries no continuation fetch;
  the ci_triage jobs face pages :316-338 while the pushci runs face does not); Main builds rotate at low frequency on the
  2880-minute wall, so 30 windows suffice for the current state; widening the busy-state window = a minor-fix candidate · registered as-is.
- The dry-run-first hard requirement carries over from v36: the first live run goes through `--dry-run` first (:1116-1157 · the plan
  face has zero side effects · the v36 S6 criterion that HEAD/porcelain stay unchanged before and after · `更新账.md:3608`); this agent did
  not probe Main's branch-protection face (the protection API was not probed · registered as unverified).

### 3.3 unclog --src pointing at a Main ConstructiveWorld_Live source (availability)

- **The tool face (ready as-is)**: --src/--world/--rocq-cmd/--candidates/--probe-parallel are fully parameterized
  with zero hard-coding (the `tools/unclog.py:119` usage section · :1089-1131 args · :959 --src missing fail-loud 9);
  the K=1/2 same-parameter dual runs are on record (`docs/perf-profile-v1.0-20261111.md:156-163` 1.87× ·
  `更新账.md:3801` the v43 dual-run mutual confirmation).
- **The source face (unavailable in the current state → the medium-change prerequisite · data-surface engineering)**:
  1. No local Main repository checkout (§1.4 measured ls empty); --src has no source tree to point at.
  2. **The world (--world) has no CI production line**: Main's certification surface is the vo tree (`coq93.yml:247`/:479 · the
     vo-trust-cache-windows-93 artifact is **vo-tree .vo** :538-545); the Live tree's .vo world
     has no CI production line at all (for comparison, the local CW Live world's probe_world_v38 was an ephemeral
     /tmp APFS clone, cleared since · perf-profile:23-24/:3805).
  3. The candidate surface needs fresh sampling: Main Live .v≥995 (§1.4) versus the local baseline's 27 items; a different candidate surface =
     incomparable (`examples/baselines/README.md:64-66` the candidate-surface quadruple criterion).
  4. **The baseline-domain same-name collision (the second face of the same-name tree)**: the audit-<domain> domain = the --src base name (README §2 :22-26):
     the Main Live tree's base name is ConstructiveWorld_Live as well → it collides with the active baseline
     `audit-ConstructiveWorld_Live-20261111.json` **in the same domain under the same name** → file-name collision + cross-tree
     mis-comparison (a same-name tree ≠ the same domain); the domain must be renamed with a generation break (e.g. audit-CW-Main-Live-…) or split
     into directories · this document recommends the former.
  → the medium change = materialize the source (an API tarball or a clone) → build the world → sample the candidate surface (the ≤30-item
  procedure perf-README:60-68) → record the first audit run: **zero tool changes · pure data-surface engineering**.

### 3.4 The registry dual-ledger path difference (the same-name ConstructiveWorld_Live tree)

- Three surfaces measured (§1.4/§2): Set = root _CoqProject + the Live dual ledger (no root order.txt); Main =
  root _CoqProject + **the Live dual ledger + the vo dual ledger**; Main carries one more vo set than Set.
- The tool face is ready as-is: `registry_union.py` --git direct read + --git-path explicit designation (:785-791/:844) +
  the --main/--branch/--git three-input face (:779-803 · the roadmap ⑦ provenance `tools/registry_union.py:781-790`
  read and confirmed); **GIT_PATH_DEFAULT = the repo-root order.txt/_CoqProject (:84) misses in both repositories**
  (both lack a root order.txt · Set measured by ls / Main measured 404); **--git-path must be explicit**:
  Set → `ConstructiveWorld_Live/order.txt`; Main → `ConstructiveWorld_vo/order.txt`
  (the certification registry · `coq93.yml:305`) or `ConstructiveWorld_Live/order.txt` (the Live face);
  **which ledger to pick = a cross-repository semantic decision** (Set's certification surface = the Live single-tree ledger · Main's certification surface = the vo ledger · under the same-name
  tree the parameter shapes agree but the semantic ledger choice differs · not a tool defect).
- Non-negotiable constraint: the registry write face (--apply persisting to disk) in the Main repository = **a cross-repository out-of-scope write** (roadmap ⑦'s risk column
  "the adapter must not write into another repository on its behalf" · :90); the audit face (the read-only four ledgers · registry_audit.py) is ready as-is;
  the operation face (union --apply) waits for a Main-repository discipline ruling before another discussion · this document does not start it.

---

## 4. Verdict = the adaptation work grading (ready as-is 4 / minor fix 3 / medium change 2)

| # | adaptation item | grade | one-line basis |
|---|---|---|---|
| 1 | ci_triage five-family classification skeleton × Main step spectrum | **ready as-is** | the A/B/D/E/C skeleton's step names are all compatible + the UNRECOGNIZED fallback does not misattribute + the GATE-BANNER-ABSENT wording is the same token (§3.1 · selftest run by this agent, rc=0) |
| 2 | pushci direct push to refs/heads/main route | **ready as-is** | remote derivation / ghproxy gate / netrc push permission, all three measured compliant (§3.2) |
| 3 | registry dual-ledger audit face (read-only) | **ready as-is** | --git + --git-path explicit designation, zero changes · same-name tree, same parameter shape (§3.4) |
| 4 | unclog tool-face flags | **ready as-is** | fully parameterized, zero changes · runs as soon as the source is in place (§3.3) |
| 5 | pushci_scenarios canned-scenario extension to the Main repository shape | **minor fix** | roadmap ⑦'s verification method explicitly requires "canned scenarios extended to the repository shape all pass" (:92): six scenarios × Main step-spectrum fixtures |
| 6 | heal × Main concurrency behavior cross-check | **minor fix** | the single-group cancel-in-progress:true collective-cancellation loop → the --watch-max-rounds safety valve + a procedure note · tameable with zero tool changes (§3.2) |
| 7 | optional ci_triage extension for the Main failing wordings | **minor fix** | GATE2-AXIOMS-RED/GATE5-RED/ATT-RECON-FAIL etc. (+ discretionary handling of the gate4 artifact wording trap) into KEY_LOG_PATTERNS or canned coverage (§3.1) |
| 8 | pushci PR-route watch match | **medium change** | **the largest gap**: a PR run's head_sha = merge commit must mismatch + refs/pull/* does not enter the mirror + push allowlist [main] gives topic pushes zero triggers (§3.2 · change the watch semantics or set a two-track procedure) |
| 9 | unclog Main Live source availability | **medium change** | no local checkout + the Live world has no CI production line + fresh candidate sampling + the baseline-domain generation-break rename (§3.3 · pure data-surface engineering) |

**verdict = ready as-is 4 / minor fix 3 / medium change 2.**

---

## 5. The recommended path (carrying roadmap ⑦'s four-step verification method · :92)

1. **Zero code first (half-day scale)**: retro-triage of the Main historical runs (the v44 Set method ·
   `更新账.md:3820-3825`: cw_sentinel --loop or ci_triage --offline, classified one by one);
   three gains from one pass: a cross-check of the classification agreement + measured proof of the true Main step-name/log-wording shapes (the unnamed checkout step's API
   step-name shape · the parallel_chk.sh wording-output shape · the Windows link-failure log shape, the three to-be-proven faces noted in §3).
2. **Minor fix**: extend the pushci_scenarios six scenarios with the Main-repository-shape fixtures (+ the optional wording extension);
   selftest / the single suite all passing · the three checks stay passing.
3. **Zero code**: a `--dry-run` against the real repository, the plan face with zero side effects (HEAD/porcelain unchanged · the v36 S6 criterion);
   note that the Main local checkout must be materialized first (--repo-path needs a real repository directory · one of the prerequisites of medium-change #9).
4. **The first live engagement**: the **push-event route (refs/heads/main)** + the `--watch-max-rounds` safety valve +
   the heal assignment cross-checked against the Main reference; **avoids the PR mirror-blind face** (medium-change #8 does not block the first engagement).
5. **unclog the Main source (medium change · separately scheduled)**: materialize through an API tarball → build the world → sample candidates ≤30 →
   record the first audit run (**rename the domain with a generation break** to prevent same-name-domain mis-comparison) → the baseline_diff same-domain axis.
6. **The constraint faces**: the credentials (the netrc push permission) are measured in place; the "credits quiet window": the live-push
   segment waits for an off-peak slot, pending execution (roadmap §1 · 3 · no registered in-repository anchor, carried as-is); Main's branch-protection face to be probed before the first live push.

---

## 6. Boundaries and as-is records

1. Runs executed by this agent: the two Main API scripts (rc=0) · ci_triage --selftest (rc=0) · the Set dual-ledger ls.
   **Not rerun**: pushci/unclog --selftest (on record rc=0 from v36/v41 · `更新账.md:3591`/`:3740`,
   not run by this agent · registered as-is).
2. **Not probed**: Main's branch-protection face / the current API rate-limit value / the scripts/parallel_chk.sh script content
   (called directly inside the yml · its content is outside this agent's fetch surface) / whether the pushci runs-face pagination is a live defect (not one under the low-frequency rotation).
3. The two instruction-vs-measurement disagreements are registered (§1.3); the measurement governs.
4. This document changed no code and made no other writes (the rocqwash working tree gained exactly this one file) · the frozen eight / quad8 / `更新账.md` untouched ✓.
5. Citation line numbers: for the Main repository's two workflows the /tmp fetched copies govern (remote ref=main HEAD at fetch time) ·
   for this repository's tool faces the working-tree files govern (the v47 `6217808` criterion).

## 7. This agent's self-attestation record (November 12, 2026 · all wrapped in cpu_guard)

| # | action | result |
|---|---|---|
| 1 | `python3 -B /tmp/fetch_main_ci.py` (netrc GET meta/workflows/contents, both workflow full texts) | rc=0 · the six loud REPO-META/workflows/FETCHED lines (§1.1) |
| 2 | `python3 -B /tmp/fetch_main_tree.py` (root listing + dual-ledger PATH-PROBE + Live top level) | rc=0 · the full 200/404 list (§1.4) |
| 3 | `python3 -B tools/ci_triage.py --selftest` | rc=0 · CI-TRIAGE-SELFTEST PASS |
| 4 | full read of the Set repository coq.yml (735 lines) + the dual-ledger ls | read in full · root order.txt No such file |
| 5 | after this document was written, `python3 -B tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash` | see the record of that round (drift must = 0 to match the three-check baseline; if a phantom citation appears, fix the document and rerun) |

---

## 8. The three minor-fix items, execution record (November 12, 2026 · the v48 survey minor-fix passes · the tooling agent)

> Carrying §5's recommended path: **step 2** (the Main-shape fixtures + the selftest Main-shape interpretation vector) and
> **step 3** (the pushci Main dry-run vector · zero tool changes, zero new flags, zero semantic changes) are done in this pass; **step 4**'s
> live push waits for the execution order and is registered as a single line, not part of this pass (not executed). Every run was wrapped in
> `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120`.

- **Step 2 done** (§5.2):
  - New file `tests/fixtures/ci_triage_main_coq93.json`, the canned true-shape jobs of the Main coq93.yml:
    the single Windows job "Rocq 9.3 build + coqchk (self-hosted seed
    cache, Windows)" (workflow name **Main CI 9.3** · the job name is the coq93.yml:61
    display-rename true shape; the `_provenance` key on record: coq93.yml:38/:61/:89-91/
    :102-591 line sources + runs-on [self-hosted, Windows] + timeout 2880 + the concurrency group
    cw-main-ci-93); the 16 step names transcribed one by one from the measured copy /tmp/mainwf_coq93.yml
    (v5 checkout→gate1→gate4→gate3→Seed→RAM guard→Build full tree→
    Generate tree-stats→Upload tree-stats→gate5→attest reconcile→coqchk
    full-tree certification→Upload vo trust cache→gate2→Upload coqchk
    logs) · the passing sample carries every step success.
  - `tools/ci_triage.py` --selftest gains the [9] Main-shape interpretation vector: the fixture's 16 step names
    matched one by one + deterministic byte identity + **a machine-checked 15-row compatibility table** (the true-shape single-failing-step shape · no logs ·
    the classification order judging step-name B before step-name A) + the two-condition E-family Main shape (Upload coqchk logs failing +
    the coqchk step skipped → E-coqchk-skipped · the empirical proof of §3.1's E row "both conditions present → E can fire").
  - **The machine-checked interpretation pins (the mechanical proof of the §3.1 compatibility table · the vector is frozen)**: Build full
    tree / coqchk full-tree certification / gate5 vo-binary quarantine / attest
    reconcile → **A** (gate5/attest ride on the coqchk substring · the same ruling as §3.1); checkout@v5 /
    Seed trust cache / Upload tree-stats / Upload vo trust cache / Upload coqchk
    logs → **B**; gate4 comment guard → **B** (the artifact substring → step-name B judged first · §3.1's
    wording-trap row proven · the same shape at Set :120, not new in Main); gate3 / gate2 / RAM guard /
    Generate tree-stats → **UNRECOGNIZED fallback**, no misattribution.
  - **One survey-prose erratum registered as-is (the machine check versus the §3.1 prose)**: the §3.1 gate1 row records
    "zero hits → UNRECOGNIZED fallback"; the mechanical measurement shows the gate1 step name "pre-build fail-fast"
    contains the build substring → it rides into **A-content-red** (fix-content · a poison-token
    failure is semantically a content failure · acceptable, the same ride-along as gate5/attest). The "five-family skeleton ready as-is" verdict is
    unaffected (no failing run is missed · no misattribution · the fallback row carries four entries, not the two §3.1 records).
- **Step 3 done** (§5.3 · zero tool changes; `tools/pushci.py` was untouched in this pass):
  - New file `tests/fixtures/pushci_scenarios/s7_main_dry_run.json` (branch=
    main = the refs/heads/main direct-push route · the same shape as rocqwash-pushci-scenario/1 · expects
    git_calls=0/api_calls=0).
  - `tests/test_pushci.py` six-scenario shell → seven scenarios (the S7 Main-shape dry-run vector: the canned
    git-caller empty table + the injector flat verbatim · the report.plan three-check lines
    [1] preflight.toolchain / [1] preflight.net / [1] preflight.gate4 (the disabled shape
    = the correct default of the degenerate base...branch diff on the direct-push main route) + the [2] push plan line
    (HTTP/1.1 + main) asserted line by line; the zero-API zero-git-call pipeline proven; the tmp repository
    before/after identical, zero side effects; idempotent, two runs byte-identical). The real-repository dry run was not run;
    the prerequisite is missing (§3.3/§5.3: the Main local checkout must be materialized first).
- **Step 4's live-push order (§5.4 · not executed · one line)**:

  ```bash
  python3 -B tools/pushci.py --repo-path /Users/apple/Desktop/ConstructiveWorld-Main --branch main --remote origin --watch-max-rounds 6 --max-heal 2 --json /tmp/pushci_main_first.json
  ```

  Prerequisites: ① the Main local checkout materialized (measured on November 12, 2026 by `ls -d /Users/apple/Desktop/*Main*`:
  **not on the volume**; the task instruction's stated shape "/Users/apple/Desktop/ConstructiveWorld-Main
  is on the volume" disagrees with the measurement · registered as-is by the §1.3 method); ② the same command with `--dry-run` first, the plan face with zero
  side effects (the v36 S6 criterion · HEAD/porcelain unchanged before and after); ③ the `--watch-max-rounds` safety
  valve against §3.2's single-group cancel-in-progress:true collective-cancellation loop; ④ Main's branch-protection face to be probed before the first live
  push (§6.2 not probed · carried as-is).

## 9. The execution attestation record (November 12, 2026 · all wrapped in cpu_guard · run by the tooling agent)

| # | command | rc |
|---|---|---|
| 1 | `python3 -B tools/ci_triage.py --selftest` | 0 (CI-TRIAGE-SELFTEST PASS · including the [9] Main-shape interpretation vector: the coq93 true-shape 16-step match + the 15-row compatibility table + the E two-condition shape) |
| 2 | `python3 -B tests/test_pushci.py` | 0 (17 passing / 0 failing · the S7 scenario + the S7 idempotent two-run byte identity) |
| 3 | `bash tests/run_tests.sh` (the full suite · including every tool selftest case) | 0 (58 passing / 0 failing / 1 skipped [the t_quad8_check four-repository copy group's existing SKIP] / 59 cases total) |
| 4 | `python3 -B tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash` | 0 (VERDICT consistent · drift=0 · this document refs=46 unresolved=6 oos=0 · run in the same round after this section was written) |
| 5 | untouched-face reconciliation | the frozen eight (the certify/frozen8.py LEDGER8 roster) / quad8 / `更新账.md` untouched ✓; `tools/pushci.py` zero changes (step 3 is a pure test face) ✓; zero git write operations (no commit) ✓ |
