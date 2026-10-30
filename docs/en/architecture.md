# rocqwash Architecture (English)

> Status snapshot: 2026-10-31 (generic per-file entries landed for wash/verify/seam/
> certify + suite extended to 14 cases, seat rqwash). This document faithfully reflects
> the current state of the repository: implemented components are checked against the
> source code, pending components are labeled as such (empty dirs / placeholders).
> Chinese mirror: [`docs/zh/architecture.md`](../zh/architecture.md). The repo is under
> active development (modules land continuously); the code is the source of truth.

## 1. Positioning & Core Principle

rocqwash is a mechanical diagnosis / washing / verification / certification toolchain
for Coq/Rocq constructive mathematics projects:

> **Core principle**: What can be mechanically verified via type-theoretic structural
> criteria shall never be delegated to probabilistic models.
> （凡可用类型论结构性判据机检的，一律不交给概率模型猜。）

Three honesty laws run through all components:

1. **Report the list, not a verdict of cleanliness** (E364 blind-zone law) — the
   scanner only emits a hit list with per-hit classification notes; a "no leakage"
   verdict may only come from the kernel census (SortAlive `__`-census); any 0-hit
   result must additionally pass the negative-vector control (E364 vectors embedded
   in `--selftest`).
2. **fail-loud** — assertion failures / missing files / unknown commands exit
   non-zero; silent error swallowing is forbidden; unterminated comments/strings and
   orphan closers are all ledgered.
3. **Idempotent & replayable** — wash/patch operations are exact-string + count
   asserted + skip-if-already-applied; safe to replay.

## 2. Three Chains in One

```
Toolchain        (scripts + templates + canonical recipes)
    ↓
Logic Chain      (criteria + gates + calibration standards)
    ↓
Derivation Chain (input → wash → verify → land → certify → push)
```

## 3. Toolchain Data Flow

```
                  ┌────────────────────────────────────────────────────┐
                  │ tools/cpu_guard.sh v3 — thermal wrapper for ALL compiles │
                  │ (FRONT/MID/BACK dynamic ladder queue + pmset gate)      │
                  └────────────────────────┬───────────────────────────┘
                                           │ wraps every compile
  .v ──▶ scan ──▶ names ──▶ wash ──▶ compile ──▶ verify(R4) ──▶ seam ──▶ certify ──▶ watch
        done     done     done    (guard)     done*        done*     piece 1    planned

  done* = first generic per-file piece landed (wash: ledger executor · verify: four-pack ·
          seam: fingerprint probe; full R4 three-source & deeper certify pieces are TODO)

  Unified entry: cli/rocqwash (subcommands scan / names / wash / verify / seam / certify / watch)
```

| Stage | Input | Output | Status |
|---|---|---|---|
| scan | single `.v` | hit list + classification notes (stdout / `--json` / `--hits-csv`) | implemented |
| names | one or two `.v` | ordered statement-name list + N=N ordered-equality assertion | implemented |
| wash | single `.v` + ledger JSON | washed `.v` (exact-string + count, idempotent) | implemented (`wash_engine.py`, ledger must be explicit); campaign batch tool also landed |
| compile | `.v` | `.vo` (magic `436f712100015ff4` check) | via cpu_guard |
| verify(R4) | `.v`+`.vo` pair (± rc/log evidence) | green-verdict four-pack per-piece ledger + verdict | implemented (`verify_vo.py`); full R4 three-source unified entry is TODO (see §4 note) |
| seam | single `.v` | W13 four-mechanism fingerprint candidate list + prescription mapping | implemented (`seam_probe.py`, candidates not verdicts) |
| certify | dir + manifest | two-tier freeze manifest freeze/check | first piece implemented (`freeze_manifest.py`); push-window four-criteria + UNION v2 TODO |
| watch | — | CI monitoring + pin-IP push + thermal guard | placeholder, pending |

## 4. Component Table (verified against source)

Shape column: **generic per-file** = argparse interface, auto-routed by
`cli/rocqwash`; **campaign tool** = `_`-prefixed, hardcoded paths, no per-file argv,
NOT auto-run by the unified entry (invoke directly with `python3`).

| Module | File | Shape | Status | Notes |
|---|---|---|---|---|
| `scan/` | `mac_stmt_scan.py` | generic per-file | **implemented** | Statement-face Prop bare-form scanner: five frozen lane families P1–P5 (13 sub-channels: Qlt/Qle/`==`/exists·and·or·not·false/bare `=`/`<=`·`<`·`>=`·`>`) + three negative-capture families (P6_In/P8_True/P9_proper — conclusion-position CAPTURE / premise-position EXEMPT); 4-way classification RED/WHITELIST/EXEMPT/CAPTURE; whitelist & BRIDGE_FAMILY registry; mixed-face (carrier co-present with bare form) detection; `--manifest` four-ledger reconciliation (swallowed/blind/kind_drift/line_drift, blind=∅ asserted); `--selftest` E364 frozen vectors; `--baseline` S09 reference run |
| `names/` | `mac_stmt_names.py` | generic per-file | **implemented** | Top-level statement-name ordinal extractor: census scope (9 kinds, no Let) / `--include-let` rendezvous scope; `--compare` ordered 1:1 equality assertion between two files (N=N form, exit 2 on mismatch); `--expect` count assertion; `--kinds` filter; ARM2 proof-body consumption; Unicode identifiers; fail-loud throughout |
| `wash/` | `wash_engine.py` | generic per-file | **implemented** (2026-10-31) | Generic per-file canonical wash engine: the `_abl1_wash.py` apply loop generalized 1:1 into an argv-driven ledger executor — exact-string + count assertions + idempotent (skip when new form present and old gone) + nested-bracket awareness (bracket-balance checked after comment/string masking) + write isolation (never rewrites `--file`) + fail-loud (any FAIL → that file not written). Ledger JSON = field-for-field translation of the PATCHES ledger (tag/old/new/expect). No ledger → exit 3 (nothing guessed; SKIP semantics). `--selftest` seven frozen vectors |
| `wash/` | `_abl1_wash.py` | campaign tool | landed | Seat-abl1 batch wash tool: exact-string + count assertions + idempotent (skip when new form already on disk); nested-bracket aware; `ROOT` hardcoded to an external campaign sandbox, no argv |
| `verify/` | `verify_vo.py` | generic per-file | **implemented** (2026-10-31) | Generic per-file green-verdict four-pack checker: a (.v, .vo) pair plus optional rc/log evidence — ① exit==0 (`--rc`/`--exit-file`) ② log with zero Error lines ③ .vo magic `436f712100015ff4` ④ .vo strictly newer than .v; criteria inherited frozen from `_parse_fin_mac.py:82-108`; missing evidence = NOT-RUN, explicitly ledgered, never counted green (③④ always checked); `--selftest` nine frozen vectors |
| `verify/` | `_parse_fin_mac.py` | campaign tool | landed | censusFIN_mac parse lane: extraction-erasure semantics (RED iff `__` appears in let body / type annotation, incl. Set-cloaked Prop) + green-verdict four-pack (exit code / log zero Error / `.vo` magic / `.vo` mtime freshness) + ann-regex dual-form law |
| `verify/` | `gate4_comment_guard.py` | campaign tool | landed | Gate-4 header-comment five-field mechanical guard v2.1: five lexeme families + three domains + judging principle; zero compile / zero network / zero tree writes |
| `verify/` | `retrofit_gate7_irr.py` | campaign tool | landed | Gate-7 English retrofit: touches comments only, never code tokens; frozen-md5 + token-stream identity assertions, fail-loud no-write |
| `seam/` | `seam_probe.py` | generic per-file | **implemented** (2026-10-31) | W13 four-mechanism generation-gap fingerprint probe: ① `==`-statement × rewrite/ring/reflexivity → `qeq_imp_qeqT` flip-back ② `apply (`/`rewrite (` full-application forms → keyed-matching instantiation ③ `rewrite` of a this-file premiss-carrying lemma (depth-0 `->` after colon) → assert-ification + dual-shore bridge ④ multi-line Require / statement-face qualified names absent from the Require set (prelude exemption registry excluded) → topology completion. Segmentation/lexeme canon reimplemented locally from the frozen scan canon; E364 blind-zone law (candidates, not verdicts; 0 hits ≠ "seamless"); `--selftest` four positive vectors + masking negatives |
| `certify/` | `freeze_manifest.py` | generic per-file | **implemented** (2026-10-31) | Two-tier freeze manifest: tier1 per-file md5 (deterministic walk, `relpath  md5` line ledger) + tier2 = md5 of the tier1 ledger text (tampering with the manifest is detected); freeze idempotent (no timestamps; same tree reproduces a byte-identical manifest) + check three-way reconciliation (changed/added/removed; zero drift exit 0); `.git/` and the manifest itself excluded. **Push-window four-criteria + UNION v2 TODO** |
| `watch/` | — (empty) | — | pending | Planned: CI monitoring + pin-IP push + thermal guard |
| `tools/` | `cpu_guard.sh` | generic | **implemented** | cpu_guard v3 thermal wrapper (see §6) |
| `tools/` | `_gen_fin_mac.py` / `_abl1_4b_compile.py` | campaign tools | landed | censusFIN SortAlive probe template generator (parameterized module/world/dep-chain); R4 4b ocamlc compile driver (hardcoded opam paths) |
| `cli/` | `rocqwash` | unified entry | **implemented** | Seven-subcommand routing (contract in §5; 2026-10-31 fixed the run_module branches missing `shift` — the subcommand name leaked into routed tools, now aligned with the §5 "1:1 passthrough" contract) |
| `examples/` | `demo_prop_leak.v` et al. | demo | **implemented** | Single-file full-chain demo (see `examples/README.md`, with measured results). Since 2026-10-31 the wash step runs for real: `washed/demo_ledger.json` (16 exact-string patches) drives `wash_engine.py`, and the engine output is **byte-identical** to the reference `washed/demo_prop_leak_washed.v` (cmp assertion; idempotent replay applied=0 skipped=16) |
| `docs/` | this tree | docs | **implemented** | zh/en bilingual architecture docs |
| `tests/` | `run_tests.sh` + 5 test files + `fixtures/` | generic | **implemented** | Test-suite master entry: `bash tests/run_tests.sh` (14 cases, positive/negative pairs; all-green exit 0 / any-red exit 1; idempotent, zero repo writes; `ROCQWASH_TESTS_FAIL_PROBE=1` injects an always-red case as suite self-check); covers scan selftest / names `--expect` pos·with-Let·neg / gate4 clean·dirty / retrofit dry-run / wash campaign-tool three-judgment / wash_engine six-judgment / verify_vo nine-judgment / seam_probe four-mechanism / freeze_manifest four-judgment / cpu_guard `-Direct` smoke + exit-code propagation (see [`tests/README.md`](../../tests/README.md)) |
| `workflows/` | — (empty) | — | pending | CI workflow placeholder (`.github/workflows/ci.yml` on file: macOS suite gate) |

> Note ①: `verify/` now holds three non-underscore-prefixed files — the historical
> campaign tools `gate4_comment_guard.py`, `retrofit_gate7_irr.py` plus the generic
> `verify_vo.py`. Under the §5 routing contract they count as ambiguous generic
> entries → `cli/rocqwash verify` exits 4 with a listing for manual disambiguation
> (measured 2026-10-31). **Unifying the entry requires renaming the two historical
> tools to the `_` prefix — both are in-service/frozen files this round, so the
> rename is logged as TODO**; until then call `python3 verify/verify_vo.py --v ...
> --vo ...` directly.
>
> Note ②: the extraction side of the full R4 three-source conjunction (bare
> full-extraction magic=0 + probe dual-face magic=0 + five-pattern grep=0) depends on
> the `_abl1_4b_compile.py` ocamlc linker path (hardcoded opam paths); generalizing it
> is over the scope of this round and is **honestly logged as TODO** — `verify_vo.py`
> currently covers the four-pack segment (compiled-artifact side); the extraction-side
> three-source conjunction awaits a later seat.

## 5. `cli/rocqwash` Unified-Entry Routing Contract

```
rocqwash <subcommand> [args...]
  scan     → scan/mac_stmt_scan.py (args & exit codes passed through 1:1)
  names    → names/mac_stmt_names.py (same)
  wash|verify|seam|certify|watch → dynamic per-module routing:
      · exactly one NON-underscore-prefixed .py in the module dir = generic
        per-file entry → auto-routed
      · underscore-prefixed .py = campaign tool → NOT auto-run (prevents
        accidental writes to external sandboxes)
      · no generic entry → exit 3; multiple generic entries → exit 4 (listed
        for manual disambiguation)
```

Exit-code table:

| Tool | 0 | 2 | 3 | 4 | 9 |
|---|---|---|---|---|---|
| `scan --file` | list printed (hits are findings, not failures) | `--selftest` vector failure | — | — | file missing |
| `names` | list / assertions pass | `--expect`/`--compare` assertion failure | — | — | file missing |
| `wash/wash_engine.py` | full ledger APPLY/SKIP (fail=NO) | any FAIL = 1; malformed ledger / usage = 2 | no ledger (nothing guessed; SKIP semantics) | — | `--file`/`--patch` missing |
| `verify/verify_vo.py` | four-pack PASS | usage error (--rc/--exit-file mutual exclusion etc.) | — | — | path missing (any red FAIL = 1) |
| `seam/seam_probe.py` | ledger printed (candidates are findings, not failures) | `--selftest` vector failure | — | — | `--file` missing |
| `certify/freeze_manifest.py` | freeze done / check zero drift | usage error / malformed manifest | — | — | dir/manifest missing (check drift = 1) |
| `cli/rocqwash` | — | unknown subcommand | no generic per-file entry | ambiguous generic entry | entry script missing |
| `tools/cpu_guard.sh` | — | — | — | — | — (exit code = wrapped command's) |

## 6. `tools/cpu_guard.sh` v3 (Dynamic Ladder-Queue Thermal Protocol)

Every compile goes through cpu_guard (thermal-overload protection, criteria first):

```
bash tools/cpu_guard.sh [-Front 2] [-Mid 2] [-MaxWaitSec 900] [-Direct]
                        [-ThrottleFloor 90] [-ThermalMaxWait 3600] [-Reg <dir>] -- <command...>
```

- **Ladder queue**: FIFO registration on entry; position <Front (default 2) = FRONT
  tier, nice 0 full speed; <Front+Mid (default +2) = MID tier, nice 10; further back
  = queued polling, demoted to BACK (`taskpolicy -b nice -n 19`) after
  `MaxWaitSec` (900 s) so nothing starves.
- **Thermal gate** (all tiers, never ABORTs on hardware reality): when
  `pmset -g therm` reports `CPU_Speed_Limit` < `ThrottleFloor` (90%), cool down in a
  polling loop; at `ThermalMaxWait` (3600 s) warn and proceed degraded.
- **`-Direct`**: probe bypass — no queue, no registration, immediate background nice 19
  execution (protects small probes from starvation).
- **Dual-lane `-Reg <dir>`**: separate registration tables; two lanes queue
  independently; default behavior unchanged when `-Reg` is omitted.
- **Stale-slot cleanup**: registration slots are validated with `kill -0` and reaped;
  exit code = wrapped command's exit code.

## 7. Planned Component Design Targets (canonical: README "Seven Canonical Steps" & "W13")

- **7 canonical wash steps (unskippable)**: ①cp source into sandbox (write isolation)
  → ②three-state triage (true-wash / bridge-retain = exception registry / UNCERTAIN =
  probe-first) → ③canonical face-mapping wash (Qlt→QltT / Qle→QleT' / `==`→QeqT /
  bare `=`→Id+id_cong / nat≤→NatLe) → ④compile verification (RC=0 / magic
  `436f712100015ff4` / vo newer than v / PA Closed / coqchk Axioms:none) → ⑤R4
  three-source conjunction (bare full-extraction magic=0 + probe dual-face magic=0 +
  five-pattern grep=0) → ⑥gate7 English retrofit (CJK→0 + five-field header 30-line
  cap) → ⑦N=N name-table assertion (`mac_stmt_names.py` ordinal full-equality) + freeze md5. Any
  failure = honest WIP, no
  green-washing.
- **W13 four mechanisms**: ① `==`-statement rewrite/ring/reflexivity structurally
  unusable on QeqT(Id) goals → flip back via `qeq_imp_qeqT` first; ② keyed-matching
  instantiation (supply-side parameter must take the actual goal shape); ③
  premiss-carrying lemma consumption (assert-ification + dual-shore bridge); ④
  cross-line Require topology leak (statement-level multi-line awareness + driver
  idempotent resume).

## 8. Related Documents

- Chinese mirror: [`docs/zh/architecture.md`](../zh/architecture.md)
- Contributing workflow / code style / test requirements / cpu_guard usage:
  [`../CONTRIBUTING.md`](../../CONTRIBUTING.md)
- Full-chain demo: [`../../examples/README.md`](../../examples/README.md)
- Test suite: [`../../tests/README.md`](../../tests/README.md) (`bash tests/run_tests.sh`)
- Project overview: [`../../README.md`](../../README.md)
