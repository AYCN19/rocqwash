# perf-profile — performance profile report v1.0 (November 11, 2026)

> Purpose.  The first on-repository record of the `tools/unclog.py --audit` probe profile: the v40 audit real-compile measurement + the v41 parallel-layer tmp-fixture mechanism measurement + the method and placeholder for the K=1 vs K=2 real-compile wall-clock profile (as it is — measurable values are recorded measured; unmeasurable ones record the method and numbers are never invented).
> Interface.  Document face only. Collection-method canon: [`examples/baselines/perf-README.md`](../examples/baselines/perf-README.md) (the three-step probe --jobs K profile collection · the wall-clock non-determinism note · the ≤30-piece sample cap · the record template). Flag citations were machine-checked against the emitted `--help` faces by the `tools/doc_lint.py` flag check (check ③). The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  The data sources of section 1 (the /tmp audit accounts and fixture scripts, plus the landed examples/baselines/ accounts) and the tool faces `tools/unclog.py`, `wash/probe_engine.py`; no runtime dependency.
> Evidence.  Every number in this report is transcribed word for word from the named data source (tmp pieces are volatile · transcription is what puts them in the repository) · zero derived values passed off as measured; derived values are explicitly labeled "derived". Every check in section 7 ran wrapped in cpu_guard. Chinese annotations inside recorded output lines are the recorded runs' original wording, translated at the normalization round; the verbatim originals are in the `.zh.md` archive.
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged.

## 1. The data-source list and the measurability verdicts

| source | content | nature | measurability verdict |
| --- | --- | --- | --- |
| DS1 | `/tmp/audit_b48_b53_baseline.json` (produced November 11, 2026 07:12 · paired log `/tmp/audit_run3.log`) | the v40 audit **real-compile** measurement (the timing section + args provenance) | measured — §2 transcribes |
| DS2 | `/tmp/perf_profile_fixture/` (this agent's tmp fixture · three runs 07:27) | the v41 `--probe-parallel` tmp-fixture **injector-canned timing** | the mechanism is measurable and measured (§3) — **the parallel wall-clock profile is not measurable** (canned, zero real compile · K bypassed) |
| DS3 | `/tmp/probe_jobs_verify.py` · `/tmp/probe_jobs_edge.py` · `/tmp/unclog_pp_verify.py` (the parallel-layer agent's fixtures · each executed by this agent) | the v41 parallel-mechanism proof (stub rocq · overlap sampling) | measured — §4 transcribes |
| DS4 | the K=1/2/3 real-compile wall-clock three runs (the same candidate face · timing-section differences) | the parallel profile's primary data | **not measured → method + placeholder** (§5 · real-tree audit live runs belong to the main session — `tools/unclog.py` docstring, same law) |

DS1 provenance note: earlier the same day this path held the product of an rc=127 fast-fail run (rocq not on PATH · zero real
compilation); at 07:12 it was re-produced by a real-compile run (`args.rocq_cmd` already the real coqc path · all 27 pieces
RC0 · red=0) — this report uses the 07:12 version (read and verified word by word); its `--src` source tree
ConstructiveWorld_Live was a real-tree snapshot · cleaned up after the run (not on disk now · on disk at run time).

## 2. The v40 audit baseline measurement (DS1 transcription)

`report["timing"]` (schema `rocqwash-unclog/1` · audit form · **no jobs field** —
this run predates the v41 dimension field · the missing-slot semantics = the K=1 serial default · directly
comparable with the v41 account's `jobs:1` at equal parameters):

```json
{"enumerate_s": null, "manifest_s": 1.289, "probe_chain_s": 190.728,
 "total_s": 194.086}
```

args provenance (transcribed): `candidates=audit27.tsv` (**27 pieces** · the ≤30-piece sample-size precedent)
· `src=ConstructiveWorld_Live` · `world=probe_world_v38` · `rocq_cmd` real coqc
(opam93) · `injector=null` · `guard=null`. Run-state face: `n_records=27` · `red=0` ·
`wall_count=0` · verdict audit · exit 0 (failings are baseline data, not a tool failure · this run all passing).

Derived reading (explicitly derived · not newly measured data):

- the probe section's share = 190.728/194.086 ≈ **98.3%** — the profile's main section is probe_chain_s;
  manifest/enumerate are environmental-noise sections.
- the serial per-piece average = 190.728/27 ≈ **7.06 s/piece** (the real-compile passing path) — the order-of-magnitude
  reference for the DS4 three runs (one K=1 run is already ~190s scale · three runs total wall-clock on the order of minutes · thermally feasible).

## 3. The tmp-fixture mechanism measurement (DS2 transcription)

The fixture: `/tmp/perf_profile_fixture/` — a src three-piece chain (C←B←A · minimal bodies) +
`cands.tsv` (3 pieces) + `inj/scenario.json` (one canned probe ledger shot: A RC0 ·
B/C RED-MISSING_LIB · feeds the real chain_graph) · **zero real compilation** (canned · K bypassed).
Command shape (the three runs differ only in K and the output path · every execution wrapped in
`bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120`):

```bash
python3 tools/unclog.py --src /tmp/perf_profile_fixture/src \
  --candidates /tmp/perf_profile_fixture/cands.tsv \
  --world /tmp/perf_profile_fixture/world \
  --audit --injector /tmp/perf_profile_fixture/inj \
  [--probe-parallel K] --workdir <wd> --json <out.json>
```

The three runs' `report["timing"]` transcribed (A/B = the same command run twice at K=1 · C = `--probe-parallel 2`):

| run | K | jobs | enumerate_s | manifest_s | probe_chain_s | total_s | rc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 1 (default) | 1 | null | 0.001 | 0.078 | 0.079 | 0 |
| B | 1 (default) | 1 | null | 0.001 | 0.102 | 0.104 | 0 |
| C | 2 | 2 | null | 0.001 | 0.089 | 0.091 | 0 |

The four machine-check verdicts (this agent's verification script rc=0 · transcribed):

1. **the jobs dimension is in the account**: the timing section's `jobs` values 1/1/2 each record their value = the
   `--probe-parallel` argument · the loud stdout line emits `timing: jobs=K` in sync — the before/after comparability face is ready.
2. **the wall clock is non-deterministic**: A/B, the same command run twice, probe_chain_s 0.078→0.102 (every run differs) ·
   while **the jobs dimension stays identical** — profile differences read section-value trends, never single-run milliseconds.
3. **A vs B**: identical key by key except the timing section ("identical inputs rerun byte-identical" holds everywhere
   outside the timing section · this agent's machine check PASS).
4. **A vs C**: identical key by key except the timing section + the `args.probe_parallel` argument (1→2 · K is
   accounted in args) (this agent's machine check PASS).

Reading boundary: this table's probe_chain_s spread is canned noise (0.078/0.102/0.089 same-order scatter) ·
**not parallel-speedup evidence** — the canned probe compiles nothing and K is bypassed, recorded as such. The mechanism
(the field is in the account · the value follows K) is proven; the speedup face belongs to DS4.

## 4. The v41 parallel-mechanism proof (DS3 transcription · each run executed by this agent)

The parallel-layer agent's `wash/probe_engine.py --jobs` (ThreadPool sharding · canonical-order accounting) +
`tools/unclog.py --probe-parallel` (pass-through) landed, and this agent executed all three tmp fixture scripts, all passing
(rc=0 · stdout tail lines transcribed):

- `probe_jobs_verify.py` → `PROBE-JOBS-VERIFY PASS`: K=1 serial overlap=1;
  K=3 **real concurrency overlap=3** and the **ledger stays byte-identical** (completion order never invades output order · the determinism
  invariant); per-piece logs independent + zero world residue.
- `probe_jobs_edge.py` → `PROBE-JOBS-EDGE PASS`: K>1 duplicate candidate names fail loud
  rc=2; K=4 wrapped in `--guard` rc=7 really taken from the pass-through; resume SKIP leaves the ledger identical.
- `unclog_pp_verify.py` → `UNCLOG-PP-VERIFY PASS`: the loop's `--probe-parallel 3`
  pass-through takes effect (overlap=3 · not merely a static argv read); **`--audit` shares the same parameter** (a K=2 probe real
  run overlap=2); `--probe-parallel 0` usage check rc=2.

That is: **at the mechanism layer, K=1 vs K>1 is proven** (real concurrency · determinism · audit sharing); the only thing left
unproven is the **real-compile wall-clock profile** (DS4).

## 5. The K=1 vs K=2 real-compile wall-clock profile — method + placeholder (as it is)

**Measurability verdict: not measurable (within this agent's authority)**. Real-tree audit live runs belong to the main session
(`tools/unclog.py` docstring · `examples/baselines/README.md` §3 same law);
tmp real-compile fixtures (stub / minimal pieces) have too low a signal-to-noise ratio · synthetic recompile-heavy pieces would be a fabricated benchmark, not the current-state
profile — neither is adopted. Zero invented numbers: the table below holds only placeholders, to be backfilled by the real-tree three runs.

The method (collection-method canon `examples/baselines/perf-README.md` §2 · abridged): fix `--src/--world/--rocq-cmd/--candidates` over the same candidate face
(≤30 pieces · DS1's precedent of 27) ·
one run each at K=1/2/3 (`--probe-parallel K` · real compilation wrapped in `--guard` · thermally, K≤2
advised) · each emits its `--json` account · read the timing-section differences (`probe_chain_s` the primary metric · the `jobs` dimension
in the account makes before/after comparable).

Measured (the real-tree 27-piece face · three rows backfilled with real numbers — K=1/K=2 transcribed from the November 11, 2026 account · K=3 backfilled from the
November 12, 2026 real run · details in the backfill sections):

| run | K | timing.jobs | probe_chain_s | total_s | note |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | (missing = 1 semantics) | 190.728 | 194.086 | the serial baseline — DS1's same-face reference 190.728 (transcribed from the November 11, 2026 account) |
| 2 | 2 | 2 | 101.916 | 105.436 | the thermal K≤2 advice — backfilled by the v43 two-run (November 11, 2026 08:1x) |
| 3 | 3 | 3 | 165.202 | 169.684 | advised to run off-peak with run 2 — a real run of November 12, 2026 · negative margin (details in the backfill section) |

Reading reference (qualitative · a reference never substitutes for measurement): DS2/DS3 proved K>1 real concurrency with zero ledger determinism drift
— the real-compile wall-clock gain depends on per-piece compile parallelism (the probe section is approximately per-piece independent · the ideal speedup
magnitude is bounded by the guard FRONT slots and thermal clamping) · the true values are the three runs' timing-section differences.

## 6. Conclusions and follow-ups

1. The `report["timing"]["jobs"]` dimension field is in the account (v41 · this agent) — the v40 old account's missing-slot
   semantics stay K=1-comparable · the new account always carries it by default; the regression is all passing (§7).
2. The collection method is ready (perf-README · three steps + template + the ≤30-piece thermal cap).
3. The DS4 real-tree three runs belong to the main session: backfilling §5's placeholders completes the parallel profile (next version v1.1).

## 7. This report's machine-check list (all executed by this agent · wrapped in cpu_guard)

| # | command | rc |
| --- | --- | --- |
| 1 | `python3 -B tools/unclog.py --selftest` | 0 (fourteen vectors passing · including ⑬ the jobs dimension) |
| 2 | `python3 -B tests/test_unclog.py` | 0 (3 passing / 0 failing) |
| 3 | the tmp fixture three runs (the §3 command shapes A/B/C) | 0/0/0 |
| 4 | `python3 -B /tmp/perf_profile_fixture/compare_runs.py` | 0 (four verdicts PASS) |
| 5 | `python3 -B /tmp/probe_jobs_verify.py` | 0 |
| 6 | `python3 -B /tmp/probe_jobs_edge.py` | 0 |
| 7 | `python3 -B /tmp/unclog_pp_verify.py` | 0 |
| 8 | the full-suite regression: `tests/run_tests.sh` = **52 passing / 0 failing / 4 skipped / 56 cases rc=0** (t_unclog/t_doclint/t_destructive_matrix/t_baseline_diff/t_probe_engine all passing); `tests/test_destructive_matrix.py` alone = **17 rows passing / 0 broken rc=0**; `tools/doc_lint.py --repo .` = **verdict consistent rc=0** (this report refs=29 · drift=0 · oos=0) | 0/0/0 |

— item 8's result stands on the final regression run (the account was backfilled when this report was delivered); the numbers of §2-§5 all
come from the §1 files, transcribed word for word.


## DS4 real-tree measurement backfill, November 11, 2026 08:1x (main session · roadmap item ① close out)

| run | K | probe_chain_s | total_s | n_records | n_red | evidence |
|---|---|---|---|---|---|---|
| DS1 (the v41 baseline) | 1 | 190.728 | 194.086 | 27 | 0 | examples/baselines/audit-ConstructiveWorld_Live-20261111.json |
| DS4 (this round's backfill) | 2 | 101.916 | 105.436 | 27 | 0 | examples/baselines/perf-ConstructiveWorld_Live-k2-20261111.json |
| DS4-k3 (the November 12, 2026 measurement agent) | 3 | 165.202 | 169.684 | 27 | 0 | examples/baselines/audit-k3-20261112.json |

**Measured speedup = 1.87×** (probe_chain accounting · the same 27-piece candidate face · the same world /tmp/probe_world_v38 · the same rocq-cmd 9.3 coqc template · wrapped in cpu_guard). The jobs dimension field (added in v41) is in the account for both runs (K=1 missing-slot semantics / K=2 explicit 2). Two runs with n_red=0 cross-prove = the 27 newly placed pieces reproduce RC0 stably in the active world generation (not a one-run fluke).

## The K=3 backfill, November 12, 2026: three accounts complete · the negative-margin speedup recorded as it is (DS4 close out)

The K=3 real run (rc=0 · cpu_guard FRONT pos=1 waited=0s · `--probe-parallel 3` · the same candidate face /tmp/audit27.tsv · the same world /tmp/probe_world_v38 · the same verbatim rocq-cmd coqc template as K=1/K=2):
`timing = {enumerate_s: null, jobs: 3, manifest_s: 2.574, probe_chain_s: 165.202, total_s: 169.684}` · 27/27 RC0 · red=0 · walls=0 · the probe ledger's md5_match 27/27 all true.

**The speedup, three accounts side by side (probe_chain accounting): K1/K2/K3 = 190.728/101.916/165.202 → K1/K2 = 1.87× · K1/K3 = 1.15× · K3 is 1.62× slower than K2 (K2/K3 = 0.62) = negative-margin speedup · recorded as it is per the DS4 discipline · no invented numbers, no forced passes**. The total accounting points the same way (194.086/105.436/169.684). Reading (single-run readings · rule 1's noise band not yet resampled = trend-level): **the parallel gain turns at the K=2 step — on this machine (4 CPU) with the current duty face, K=3 has no gain**. Contention-suspect note (as it is · no excuse-making): during the run another agent's nice-19 coqchk over 17 pieces was in flight in the background · the guard's warm-state precheck read tlevel=58 → launch 60 (the K=2 run read 0) · pmset CPU_Speed_Limit=100%, no thermal clamping; K=3 ran off-peak from K=2 (the previous day 08:14), compliant.

The comparability machine check (executed by this agent): the identical-face K=3 vs K=2 comparison is key-by-key identical except the timing section + `args.probe_parallel` (0 key differences); `baseline_diff` in both directions (K1↔K3 · K2↔K3) verdict=stable · the candidate-face quadruple `source=tsv · src=ConstructiveWorld_Live · candidates=audit27.tsv · chain_ledgers=-` identical · rc=0. The account name `audit-k3-20261112.json` landed as the task instruction specified (the perf-README §2 naming law's native form would be `perf-ConstructiveWorld_Live-k3-*.json` · the quadruple is embedded and identical · the diff measured no mispairing · noted as it is); rocq-cmd takes the same verbatim coqc template as K=1/K=2 rather than bin/rocq (args-section identity is the precondition · perf-README §2 — the template word "rocq" is the rocq93 suite's generic name).

## The K=3 resampling, November 12, 2026: rule 1's noise band, first sample (the two-shot interval · the measurement agent's k3-noise)

A K=3 resampling shot for perf-README §3 rule 1 ("a single run draws no conclusion") (off-peak from the first shot · the thermal discipline matches the v48 measurement agent) — the backfill section above's "rule 1's noise band not yet resampled = trend-level" has a readable band from this section on.

The procedure (the same verbatim as the first shot · the args section machine-checked key-by-key identical, 0 key differences): `--probe-parallel 3` · the same candidate face /tmp/audit27.tsv · the same world /tmp/probe_world_v38 · the same verbatim coqc template as K=1/K=2/K3 · src=ConstructiveWorld_Live (the Set repository canon · all 27 pieces' md5 verified live before the run) · wrapped in cpu_guard (FRONT pos=1 waited=0s · launch tlevel=57 · no thermal clamping).

| run | K | timing.jobs | manifest_s | probe_chain_s | total_s | rc |
| --- | --- | --- | --- | --- | --- | --- |
| the first shot (the backfill section above) | 3 | 3 | 2.574 | 165.202 | 169.684 | 0 |
| the resampling (this agent · 02:12-02:15) | 3 | 3 | 2.16 | 190.719 | 195.221 | 0 |

**The noise band (probe_chain accounting · the two-shot interval) = [165.202, 190.719] · band width 25.517s = 15.4% of the first reading (14.3% by the midpoint accounting)**; the total accounting points the same way (169.684→195.221 · +15.1%). The run-state face is identical across the two shots: 27/27 RC0 · red=0 · walls=0 · the ledger's md5_match 27/27 · the args section and every non-timing section key-by-key identical (the difference sits exactly in the only non-deterministic section, timing · rule 2's identical-face prior PASS).

The negative result as it is (no invented numbers): the resampling reading 190.719 is **15.4% slower** than the first shot · and differs from the K=1 serial baseline 190.728 by only -0.009s (it lands on the serial line) · the two-shot interval as a whole covers the serial value. The qualitative conclusion above ("K3 is 1.62× slower than K2 = negative margin") is supported by both shots together (both are far slower than K2=101.916 · holds outside the band); but the precise negative-margin magnitude of K3 relative to K1 is single-run-level noise (one shot 25.5s faster than serial · one shot level with serial) — **K=3 has no gain = the robust conclusion readable from the two shots · the precise negative-margin multiple cannot be read from a single run (rule 1's worked example)**.

The thermal and contention note (as it is · no excuse-making): the first shot and the resampling both ran in the same window as another agent's nice-19 background coqchk loop (a 17-piece base rebuild · the -Direct step) — the band values include the contention effect; the two shots ran off-peak, compliant (the first shot produced its account at 01:40 · the resampling started 02:12 · no time overlap); launch warm-state 58→60 for the first shot · 57 for the resampling · pmset CPU_Speed_Limit=100%, no thermal clamping in either shot.

The comparable machine check (executed by this agent · all wrapped in cpu_guard): `baseline_diff` in both directions (K3→K3b · K3b→K3) verdict=stable rc=0 · the candidate-face quadruple `source=tsv · src=ConstructiveWorld_Live · candidates=audit27.tsv · chain_ledgers=-` identical; K1↔K3b · K2↔K3b cross-checked, also stable rc=0. The output account name `audit-k3b-20261112.json` per the task instruction (a departure from the perf naming law · the same note as the first shot's precedent is kept · the quadruple is embedded and identical, the diff measured no mispairing).
