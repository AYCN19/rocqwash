# Contributing to rocqos (rocqwash) / 贡献指南

> Purpose.  Contributor guide for the rocqos (Rocq operations suite)
>   repository: the honesty laws, licensing and contributor agreement, the
>   contribution workflow, code style, the module contract, test
>   requirements, cpu_guard usage, commit and review discipline, and the
>   five interface disciplines for workflow-facing tools.
> Interface.  Prose face for contributors and reviewers, no CLI of its own;
>   it points readers to [`docs/zh/architecture.md`](docs/zh/architecture.md) /
>   [`docs/en/architecture.md`](docs/en/architecture.md) (architecture and
>   component state), [`docs/CAPABILITY-INDEX.md`](docs/CAPABILITY-INDEX.md)
>   (full contract surface) and [`docs/mcp.md`](docs/mcp.md) (MCP surface).
> Dependencies.  `LICENSE` (AGPL-3.0-or-later), `CLA/ICLA.md`, `CLA/CCLA.md`,
>   `NOTICE`, `cw.sh`, `cli/rocqwash`, `tests/run_tests.sh`,
>   `tools/cpu_guard.sh`, `tools/doc_lint.py`, `tools/norm_lint.py`,
>   `seeds/jargon/jargon-map.json`; rocq/coqc for the compile demos; macOS
>   `pmset` for the cpu_guard thermal gate.
> Evidence.  The §4 command list: `bash tests/run_tests.sh`, the component
>   `--selftest` vectors, `make -C examples demo`, and the N=N ordered
>   equality assertion; review accepts mechanical evidence only.
> Exit-codes.  Codes referenced in this guide: 0 pass; 1 data-incomplete;
>   2 usage or assertion; 3 no generic entry; 4 ambiguous entries;
>   9 missing target.

> Status.  Formal name **rocqos** (Rocq operations suite); the link name
>   stays `rocqwash` (one repository, two names; decided on November 15,
>   2026).  Current-state anchor: tag `rw-v0.1.0-20261114` (public
>   repository, CI passing).

## 0. Core Principles / 核心原则

The rocqwash repository accepts only contributions that type-theoretic
structural criteria can check mechanically. Three honesty laws are
veto-level:

1. **Report the hit list, never a cleanliness verdict (E364)**: a tool
   reports the hit list and classification notes only; a "no leak /
   passed" conclusion may come only from the kernel criteria (census /
   magic numbers / exit codes). A 0-hit result must additionally pass a
   negative-vector control.
2. **fail-loud**: every assertion failure exits non-zero with loud output;
   no silent error swallowing, no spurious passes, and NOT-RUN must never
   be marked as passed (SKIPs must be labeled explicitly).
3. **Idempotent replay**: every rewrite operation is exact-string + count
   assertion + skip-if-already-applied.

## 0.5 License & Contributor Agreement / 许可与贡献者协议

The repository is licensed **AGPL-3.0-or-later** (full text in the
repo-root `LICENSE`). Contribution terms:

1. **Sign the ICLA first**: sign [`CLA/ICLA.md`](CLA/ICLA.md) before your
   first merged contribution (copyright and patent grant, dual-license
   authorization, and the human-as-author representation); signed copies
   go to the Steward, Wang Baojun (168888@live.cn; governing law: the
   People's Republic of China). Corporate contributors use
   [`CLA/CCLA.md`](CLA/CCLA.md).
2. **Human authorship**: a contribution must contain substantial human
   creative authorship; AI tools may assist, but the submitter is the
   author and is responsible for the content (same source as the `NOTICE`
   AUTHORSHIP STATEMENT). Disclose AI assistance in the PR description.
3. **License invariant**: once merged, a contribution is licensed
   AGPL-3.0-or-later; private-only add-on terms are not accepted (the
   commercial-license track in
   [`CLA/commercial_license_template.md`](CLA/commercial_license_template.md)
   is unrelated to contributions).

## 1. Contribution Workflow / 贡献流程

0. **ICLA and intake precheck**: sign the ICLA (see §0.5) and run the
   read-only four-gate intake check
   `bash cw.sh contrib-intake --contrib-repo <your-repo>` (contribution
   repo / baseline repo / ref / paths / jargon mapping are parameterized;
   on BLOCK, correct per the prompt). Disclose AI assistance in the PR
   description.
1. **Claim a module slot**: the `workflows/` placeholder and the module
   deep pieces (the R4 extraction-side three-source piece, the `verify/`
   unified-entry close-out (needs a historical-file rename once the freeze
   lifts), and the `certify/` close-out (see docs/zh/architecture.md §4
   notes ①③)) are open slots (an empty directory = not landed; `tests/`
   already hosts the self-test suite, and new cases go directly into
   `tests/run_tests.sh`, see §4). Claim the slot in an issue or task
   instruction first to avoid colliding with concurrent work (this
   repository is developed by multiple concurrent agents; check
   `git log --oneline -5` for the latest state before submitting).
2. **Branch and commit**: open a work branch from the default branch;
   commit messages follow the `type: summary` form (`feat:` / `docs:` /
   `fix:` / `test:`, per the existing log).
3. **Implement**: follow the §2 code style and the §3 module contract.
4. **Self-verify**: run every command in §4 and paste the exit codes and
   output summaries into the PR / delivery notes. New scanner channels,
   allowlist entries, or extractor behavior must also add frozen
   `--selftest` vectors.
5. **Doc sync**: every user-visible behavior change updates the
   `docs/zh/` and `docs/en/` bilingual mirrors and `README.md`; a
   mismatch between these documents and the code counts as a bug.
6. **Review criteria**: review accepts mechanical evidence only (exit
   codes, md5s, count assertions, selftest PASS), never a verbal "I tested
   it" claim.

## 2. Code Style / 代码规范

**Python** (`scan/`, `names/`, and every generic entry):

- Standard library only (the two existing scanners use only
  `os/re/sys/json/io/hashlib/argparse`), zero third-party dependencies;
  Python ≥ 3.9 compatible (`sys.stdout.reconfigure` is already in use).
- UTF-8 file header (`# -*- coding: utf-8 -*-`) plus a module docstring
  that states purpose, inheritance lineage, and usage item by item.
- CLI via argparse; flag naming aligned with the existing tools
  (`--file/--json/--names-out/--expect/--compare` style).
- **Exit-code contract**: `0` = pass; `2` = assertion failure
  (`--expect`/`--compare`/selftest vectors); `9` = target file missing.
  Everything else fails loud (`SystemExit("FAIL-LOUD: ...")` with location
  information).
- Full listing output: lists, counts, anomalies and duplicates all go to
  stdout or `--json`; conclusion-only output is not accepted.
- Comment language is free; identifiers are ASCII (Unicode is allowed only
  inside scanned identifier-name channels; see the Unicode name-channel
  handling in `mac_stmt_names.py`).
- md5 fingerprints: every write-to-disk comparison or freeze outputs the
  source file's md5 (see the scanners' `md5_of`).
- **Language and standardization five-gate set (hard for new files)**:
  comments, docstrings, help and runtime output text in English only; the
  five-field English header (`Purpose. / Interface. / Dependencies. /
  Evidence. / Exit-codes.`, ≤30 lines, see
  [`docs/annotation-standard-v1.0-20261113.md`](docs/annotation-standard-v1.0-20261113.md));
  CJK = 0 on new code faces; a clean ai-flavor battery
  (`python -I tools/ai_flavor.py --file <file>`; the 36-face and em-dash
  batteries; target 0); jargon avoided per
  [`seeds/jargon/jargon-map.json`](seeds/jargon/jargon-map.json)
  (`norm_lint` machine-checked); runtime output-string changes synced to
  test assertions. Exempt faces (verbatim seed transcriptions / test data
  / `docs/zh/` mirrors / internal ledgers) are registration-based: every
  exemption is registered (file:line · class · basis); an unregistered
  hit is a violation.

**Bash** (`tools/`, `cli/`): `set -u`; temporary resources cleaned via
`trap ... EXIT INT TERM`; exit codes passed through unmodified; compatible
with macOS stock bash 3.2 (no bash 4+ features).

**Coq/Rocq (`.v` samples and templates)**: ASCII statement names; comments
in library-facing files follow gate7 (CJK → 0, five-field header, 30-line
cap); the sample file header states dependencies and compile-verification
status.

## 3. Module Contract / 模块契约 (integration with `cli/rocqwash`)

`cli/rocqwash`, the unified entry, routes per the following contract
(`cli/rocqwash help` prints the same text):

1. Every module directory (`wash/ verify/ seam/ certify/ watch/ …`) exposes
   at most one **generic per-file entry**: a `.py` without a leading
   underscore, argparse interface, per-file arguments (e.g. `<file.v>`).
2. When the entry is present (the only non-`_`-prefixed `.py`),
   `cli/rocqwash <sub>` auto-routes to it, passing arguments and exit
   codes through 1:1.
3. **A `_` prefix marks effort- or agent-specific tooling** (hardcoded
   paths, no per-file argv; e.g. `wash/_abl1_wash.py`,
   `verify/_parse_fin_mac.py`). The unified entry never auto-runs these,
   which prevents accidental writes to external sandboxes; call
   `python3 <path>` directly when needed. New effort tooling keeps the `_`
   prefix.
4. No generic entry → CLI exit 3; multiple generic entries → exit 4 (with
   a listing for manual selection). Exception: the three generic
   `certify/` pieces and the four generic `verify/` pieces are routed
   explicitly by the CLI; `rocqwash certify freeze|push_gate|frozen8
   [args...]` and `rocqwash verify gate4|verify_vo|verify_gate6|adaptation
   [args...]` pass through 1:1; no sub-verb still exits 4 with the
   listing; an unknown sub-verb exits 2. Route history:

   | Route | Added | Note |
   |---|---|---|
   | `verify` explicit route (adaptation entry) | October 31, 2026 | initial route |
   | `verify_gate6` | November 1, 2026 | round 4 |
   | `certify` `frozen8` | November 1, 2026 | round 5, zero frozen-file changes |

5. Tooling **must not write outside the repository** unless its docstring
   prominently declares ROOT and states its idempotency; batch tooling
   must be idempotent (already present in the tree = skip) with count
   assertions.
6. New subcommands: one `run_module` case line in `cli/rocqwash`; nothing
   else in the CLI changes.

## 4. Test Requirements / 测试要求

Everything in this section must pass before delivery. **Zero build**: pure
standard-library Python + bash (Python ≥ 3.9, bash ≥ 3.2, macOS stock), no
compile or build step; demos that involve compilation need rocq/coqc, and
when it is absent the corresponding segment SKIPs explicitly (SKIP =
NOT-RUN, never a spurious pass). Run the one-shot test suite first
(historical baseline: five rounds on November 1, 2026, 31 pass / 0 fail;
**the current roster in [`tests/README.md`](tests/README.md) is
authoritative, 67 cases at tag `rw-v0.1.0`**):

```bash
# ⓪ one-shot suite (repo-wide gate)
bash tests/run_tests.sh                              # all green EXIT 0; any red EXIT 1
ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh  # suite self-check: injected always-red → 1 fail / EXIT 1 (count follows the roster)
```

Suite coverage and format (the case count grows with the roster; 67 cases
at tag `rw-v0.1.0`) are documented in [`tests/README.md`](tests/README.md):
scanner selftest; names `--expect` positive, `-Let` and negative verdicts;
gate4 clean/dirty pair; adaptation dry run; wash effort-piece tools (three
verdicts); wash_engine six verdicts; verify_vo thirteen verdicts
(including the four `--require-fresh` fresh-compile defenses); seam_probe
four mechanisms; freeze_manifest four verdicts; push_gate UNION six
verdicts + window four verdicts; watch zero-network vector group;
cpu_guard `-Direct` smoke + rc propagation; netname_normalize nine
sections; verify_fresh eight sections; extract_magic ten sections. Items
①–④ below are component-level checks (① is suite-covered; ② ③ ④ stay
manual; the ②–④ baselines were measured on October 31, 2026):

```bash
# ① 扫描器 E364 冻结向量组（正/负/名道/CAPTURE/混合面全量）→ SELFTEST PASS，exit 0
python3 scan/mac_stmt_scan.py --selftest

# ② 统一 CLI 冒烟：help / 未知子命令 / certify 显式分派 / watch 已路由
cli/rocqwash help; echo $?               # exit 0
cli/rocqwash bogus; echo $?              # exit 2
cli/rocqwash certify 2>&1; echo $?       # exit 4（无子动词＝freeze_manifest+push_gate+frozen8 三通用入口不唯一·列清单·与 verify/ 同款契约形）
cli/rocqwash certify freeze --selftest; echo $?     # exit 0（显式分派→freeze_manifest.py·1:1 透传）
cli/rocqwash certify push_gate --selftest; echo $?  # exit 0（显式分派→push_gate.py·1:1 透传）
cli/rocqwash certify frozen8 --selftest; echo $?    # exit 0（显式分派→frozen8.py·1:1 透传·五巡补件）
cli/rocqwash certify bogusverb 2>&1; echo $?        # exit 2（未知子动词·列合法子动词 freeze|push_gate|frozen8）
cli/rocqwash verify gate4 --file <clean.v>; echo $?  # exit 0/1/2=gate4 自身口径透传（净件 0·脏件 1·复核项 2）
cli/rocqwash verify verify_vo --selftest; echo $?    # exit 0（显式分派→verify_vo.py·九判绿）
cli/rocqwash verify verify_gate6 --selftest; echo $? # exit 0（显式分派→verify_gate6.py·十判绿·四巡补件）
cli/rocqwash verify bogusverb 2>&1; echo $?          # exit 2（未知子动词·列合法子动词 gate4|verify_vo|verify_gate6|adaptation）
cli/rocqwash watch ci --runs-json <f>; echo $?  # watch.py 已路由（ci 离线证据判读）

# ③ 全链演示（scan→names→N=N→wash→verify；SKIP 显式标注 NOT-RUN）
make -C examples demo                  # exit 0；wash 段台账真跑（引擎输出与参照件逐字节恒同）
make -C examples clean                 # 收尾清 build/

# ④ N=N 名表断言（任何洗/改写类 PR 必附：改前 vs 改后 有序全等）
cli/rocqwash names examples/demo_prop_leak.v \
  --compare examples/washed/demo_prop_leak_washed.v --expect 5   # 断言 5=5 PASS
```

Additional requirements:

- **New scanner channels / allowlist entries / extractor behavior**: add
  the matching frozen vectors to `mac_stmt_scan.py`'s
  `SELFTEST_POS/POS_CONCL/NEG/NAMES/CAPTURE/MIXED` groups (positive and
  negative examples in pairs) and keep `--selftest` fully passing.
- **Sanitize/rewrite PRs**: attach the ②④-style assertions (before/after
  N=N ordered equality, plus the idempotent-replay output
  `applied=0 skipped=N`).
- **Compile-touching changes**: always wrap them in `tools/cpu_guard.sh`
  (§5), and check the `.vo` magic `436f712100015ff4` and mtime freshness
  (four-point pass criterion).
- **Doc changes**: keep the zh/en mirrors in sync and keep `make demo` at
  exit 0.
- **Zero new failing criteria**: the post-change failing set must be a
  subset of the pre-change baseline roster (a failing result is data; the
  Windows host-face spurious-failure family follows the
  [`tests/README.md`](tests/README.md) roster; passes and skips are not
  reduced). Count staleness caused by the change itself must be fixed in
  the same change; existing debt is paid in its own work stream.

## 5. cpu_guard Usage / cpu_guard 使用说明 (v3 thermal wrapping)

**Every compile on this machine goes through the cpu_guard wrap**
(thermal-overload protection; on hardware reality it never ABORTs, it
slows down, queues, or degrades):

```bash
# 标准形（README Quick Start 同款）
bash tools/cpu_guard.sh -Reg /tmp/my_reg -Front 0 -Mid 1 -- \
  rocq c -native-compiler no -Q . "" my_proof.v

# 默认档（Front=2 Mid=2）：前 2 位 FRONT 全速，随后 2 位 MID(nice 10)，其余排队
bash tools/cpu_guard.sh -- <编译命令...>

# 小探针直通（不排队不注册，nice 19 后台防饿死）
bash tools/cpu_guard.sh -Direct -- ./probe.sh
```

| Parameter | Default | Meaning |
|---|---|---|
| `-Front N` | 2 | FRONT-tier slot count (nice 0, full speed) |
| `-Mid N` | 2 | MID-tier slot count (nice 10) |
| `-MaxWaitSec N` | 900 | queue-timeout seconds; at expiry the submission is released by demotion to BACK (`taskpolicy -b nice -n 19`) instead of starving |
| `-Direct` | off | direct pass-through for small probes and checks (no queueing, no registration) |
| `-ThrottleFloor N` | 90 | thermal gate: `pmset -g therm` `CPU_Speed_Limit` < N% → cooling poll |
| `-ThermalMaxWait N` | 3600 | cooling cap in seconds; at expiry warn and release (demoted) |
| `-Reg <dir>` | `/tmp/cpu_guard.reg` | registry directory; the two lanes queue separately and do not block each other |
| `--` | required | the wrapped command follows |

Behavior: entries are registered FIFO on arrival (stale slots are cleared
automatically via `kill -0`); a submission moves up in turn as its
predecessors finish; the exit code is the wrapped command's exit code
(passed through unmodified). Smoke selftest:
`bash tools/cpu_guard.sh -Front 2 -Mid 2 -- echo GUARD-OK` (measured
output `[cpu_guard] FRONT launch …` + `GUARD-OK`, exit 0).

## 6. Commits & Review / 提交信息与评审

Commit as `type: summary` (`feat:` / `docs:` / `fix:` / `test:`); one
verifiable unit per commit. Review asks three questions: (1) where is the
evidence (exit codes / output)? (2) are the assertions fail-loud? (3) are
both doc mirrors synced? A "no" on any question sends it back.

Maintainer side: maintainer commits are GPG-signed (repository
`commit.gpgsign` applies); the ledger [`更新账.md`](更新账.md) is
append-only (exactly one line per integration; the CRLF hard gate =
numstat exactly +1/-0); stage explicit paths only, never `-A`; during
concurrent-agent windows check the tree first and never touch or entangle
other agents' uncommitted work.

## 7. Interface Five Disciplines / 接口五纪律 (workflow-facing tools, shared contract since v37)

The workflow-facing tools (currently `tools/cw_sentinel.py` (sentinel),
`tools/wash_shape.py` (wash-shape), `tools/unclog.py` (unclog),
`tools/pushci.py` (pushci); `tools/cw_doctor.py` joins in the same shape
since v38) must honor all five interface disciplines. This section shares
its source with §1 of the workflow-integration whitepaper
([`docs/workflow-integration-whitepaper-v1.0-20261111.md`](docs/workflow-integration-whitepaper-v1.0-20261111.md);
the per-tool mechanics and authoritative commands live there); the quick
reference is the workflow-facing-interface section of
[`README-cw.md`](README-cw.md).

1. **JSON-in/JSON-out with named schemas and determinism**: output goes
   through `--json OUT` with a named schema: `rocqwash-sentinel/1`,
   `rocqwash-shape/1`, `rocqwash-unclog/1`, `rocqwash-pushci/1`
   (`rocqwash-cwdoctor/1` since v38; `rocqwash-doclint/1` since v39).
   Loop-mode event streams go through `--events FILE`, one JSON object per
   line (sentinel event schema `rocqwash-sentinel-event/1`; the `seq` key
   is monotonic within the stream). `--json` output is written with
   `sort_keys`, so a rerun on the same input is byte-identical; reports
   carry zero wall-clock and zero absolute paths (paths are emitted as
   basenames only; with `--sleep-scale 0` the event-line `ts` field is
   off and a note records that).
2. **Exit codes 0/1/2/9 (a failing result is data, not a tool failure;
   loud stdout)**: 0 = passing / inspection complete / unclogged (pushci
   success and dry-run = 0); 1 = data-incomplete (sanitize pass
   incomplete: partial / plan-miss, honest blocker, rounds exhausted;
   pushci heal-exhausted / unstable / toolchain); 2 = usage error
   (including the frozen-file failing refusal and injected-scenario shape
   errors); 9 = missing or fail-loud (source unreachable, injector
   coverage gap, path missing, subprocess rc ≠ 0). Data-level failures
   (CI failing, blockage, blockers) travel in the event stream and the
   report's failing records and never enter the exit code. Workflows
   branch on two levels: first by exit code on the tool face (2 = fix the
   call, 9 = fix the target), then read the JSON and branch on
   `verdict`/`kind` for the data face.
3. **`--once`/`--loop` dual mode**: `--once` runs one round, emits the
   record and exits (inline workflow steps; wash-shape defaults to once,
   and the plan phase writes nothing to disk); `--loop --interval S` is
   the long-running watcher mode (for background bash tasks), with round
   caps that stop the tool itself (sentinel/wash-shape `--max-rounds N`,
   unclog `--loop-max N`); `--sleep-scale F` multiplies every sleep by F
   (0 = no real sleep, plus event `ts` off), for offline drills and
   determinism pinning; not for production.
4. **`--injector` offline testability**: workflow selftests and CI drills
   always run in injected mode with `--sleep-scale 0`, zero real network
   and zero real compile. An injector coverage gap fails loudly with exit
   9, and the real network is never touched silently (pushci requires
   `--injector DIR` and `--git-caller FILE` as a pair; one without the
   other is usage error 2). Under injection, unclog still really runs
   chain_graph/cure_applier/scan_v4_token/frozen8 (real orchestration,
   not a puppet). The tools' `--selftest` suite-hookup files
   (`tests/test_cw_sentinel.py` / `test_wash_shape.py` / `test_unclog.py`
   / `test_pushci.py`) all run with zero real network and zero real
   compile, which is the self-proof of this discipline.
5. **Zero new engines**: inside the tools, everything orchestrates the
   existing engines through direct subprocess calls; sentinel
   classification lives entirely in `ci_triage` and chain-root analysis
   entirely in `chain_graph`; wash-shape uses the five wash engines
   (gate4/scan_v4/cure_applier/comment_sweep/registry_union); unclog uses
   the five steps (probe_engine/chain_graph/cure_applier/scan_v4_token/
   frozen8); pushci orchestrates the four v35 tools. The discipline is
   two-way: the workflow side writes no new logic for re-judging a
   failure or re-picking a root cause either; call the tool and read its
   JSON. Real compiles always go through cpu_guard (§5); unclog passes
   `--guard PATH --guard-reg DIR --guard-front N --guard-mid N
   --guard-maxwait N` through.

Addendum: python3, pure standard library, fail-loud, zero hardcoded paths
(same rule as §2). `cw.sh` is the 1:1 passthrough entry (exec; arguments
and exit codes are not rewritten); inside a workflow, `bash cw.sh <tool>`
and a direct `python3 tools/<tool>.py` call are semantically identical
(nested blocks use the `cw.sh` form, one less path coupling).

**Where new tools enter the existing flows** (the entry points of the
five releases v35–v39):

- **Contribution self-verification chain (§1.4/§4)**: every new tool adds
  `--selftest` frozen vectors, hooks into `tests/run_tests.sh` (v39
  current state: 54 cases), and passes the three `tools/doc_lint.py`
  checks (documentation-vs-implementation consistency: tool table,
  counts, flags; flags are checked one by one against each tool's actual
  `--help` output).
- **CI failing-build repair chain (same as README-cw)**: `doctor` →
  `net-probe` → `pushci` (embeds watch + heal) → `triage`; the four v35
  diagnostic tools and the v36 orchestrator are the componentized,
  one-command form of this chain.
- **Realtime service surface (added v37–v39)**: the sentinel's three
  signal sources → JSONL event stream → human review → unclog (`--audit`
  read-only baseline → `--apply` allowlist application) / wash-shape
  (plan under human review → `--apply`); the cw-doctor checkup as the
  preflight; `--on-red-preset` relays (unclog = dry run, pushci =
  `--dry-run`; the default is the safe invariant state). The runbook is
  [`docs/ops-realtime-service-v1.0-20261111.md`](docs/ops-realtime-service-v1.0-20261111.md).
- **Documentation close-out chain (v39)**: run
  `bash cw.sh doc-lint --repo .` before delivering doc changes; three
  checks, zero drift (verdict consistent, exit 0).

The authoritative per-tool contract face is
[`docs/CAPABILITY-INDEX.md`](docs/CAPABILITY-INDEX.md); the MCP surface
(24 capabilities) is [`docs/mcp.md`](docs/mcp.md); the language-engine
stack (ai-flavor / jargon / termbase / i18n pipeline / auto-round) is
registered in [`seeds/engines/ENGINES.md`](seeds/engines/ENGINES.md).
