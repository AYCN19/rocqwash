# Contributing to rocqwash / 贡献指南

> 双语指南：每节先中文、后 English 摘要。架构与组件现状见
> [`docs/zh/architecture.md`](docs/zh/architecture.md) /
> [`docs/en/architecture.md`](docs/en/architecture.md)。

## 0. 核心原则 / Core Principles

**中文**：rocqwash 只收「类型论结构性判据可机检」的贡献。三条诚实律是一票否决项：

1. **报清单不报清白**（E364）——工具只出命中清单与归类注记；「无泄露/已通过」判词
   唯内核判据（census/魔数/退出码）可出。0 命中必须另过负证对照。
2. **fail-loud**——断言失败一律非零退出＋响亮输出；禁静默吞错、禁假绿、禁把
   NOT-RUN 标成通过（SKIP 必须显式标注）。
3. **幂等可重放**——一切改写操作 exact-string ＋ count 断言 ＋ 已在盘即 skip。

**English**: rocqwash only accepts contributions checkable by type-theoretic
structural criteria. Three honesty laws are veto-level: (1) report the hit list,
never a cleanliness verdict — verdicts belong to kernel criteria only, and 0-hit
results require negative-vector control; (2) fail-loud — non-zero exit + loud output
on any assertion failure, no green-washing, SKIPs must be explicit; (3) idempotent
replay — exact-string + count assertions + skip-if-already-applied.

## 1. 贡献流程 / Contribution Workflow

**中文**：

1. **认领模块槽位**：`wash/`(通用逐件入口)、`seam/`、`certify/`、`watch/`、
   `workflows/` 为开放槽位（空目录＝未落地；`tests/` 已落自测套件，新增用例直接扩
   `tests/run_tests.sh`，见 §4）。先在 issue/工单认领，避免
   与并发席位撞车（本仓库多席位并发开发，提交前 `git log --oneline -5` 看最新盘面）。
2. **分支与提交**：从默认分支开工作分支；提交信息用 `type: summary` 形制
   （`feat:` / `docs:` / `fix:` / `test:`，参照现有 log）。
3. **实现**：遵守 §2 代码规范与 §3 模块契约。
4. **自证**：跑 §4 测试要求全部命令，退出码与输出摘要贴入 PR/交付说明。新扫描道/
   白名单/提取器行为必须同时补 `--selftest` 冻结向量。
5. **文档同步**：用户可见行为变化必须同步 `docs/zh/` 与 `docs/en/` 双语镜像＋
   `README.md`；本目录文档与代码不一致视为 bug。
6. **评审判据**：评审只认机械证据（退出码、md5、count 断言、selftest PASS），
   不认「我测过了」口头声明。

**English**: (1) claim an open module slot (`wash/` generic per-file entry, `seam/`,
`certify/`, `watch/`, `workflows/` — empty dir = not landed; `tests/` already hosts
the suite, extend `tests/run_tests.sh` for new cases, see §4); check recent commits
first — this repo
is developed concurrently by multiple seats. (2) branch from the default branch,
commit as `type: summary`. (3) implement per §2/§3. (4) run every command in §4 and
attach exit codes + output summaries; new scanner channels / whitelist entries /
extractor behavior must add `--selftest` frozen vectors. (5) sync `docs/zh/` +
`docs/en/` + README for any user-visible change. (6) review accepts mechanical
evidence only (exit codes, md5s, count assertions, selftest PASS).

## 2. 代码规范 / Code Style

**中文**：

- **Python**（`scan/`、`names/` 及一切通用入口）：
  - 仅标准库（现有两器仅用 `os/re/sys/json/io/hashlib/argparse`），零第三方依赖；
    Python ≥ 3.9 兼容（`sys.stdout.reconfigure` 已在用）。
  - UTF-8 文件头（`# -*- coding: utf-8 -*-`）＋模块 docstring：用途/继承血统/用法逐条写清。
  - CLI 一律 argparse；参数命名与现有器对齐（`--file/--json/--names-out/--expect/
    --compare` 风格）。
  - **退出码口径**：`0`=通过；`2`=断言失败（`--expect`/`--compare`/selftest 向量）；
    `9`=目标文件缺失。其余错误 fail-loud（`SystemExit("FAIL-LOUD: ...")` 带定位信息）。
  - 逐账输出：清单/计数/anomalies/duplicates 全部落 stdout 或 `--json`，禁只给结论。
  - 注释语言不拘，标识符一律 ASCII（Unicode 仅允许出现在被扫描的标识符名道内，
    参照 `mac_stmt_names.py` 的 Unicode 名道处理）。
  - md5 指纹：凡落盘对照/冻结，输出源文件 md5（参照两器 `md5_of`）。
- **Bash**（`tools/`、`cli/`）：`set -u`；临时资源 `trap ... EXIT INT TERM` 清理；
  退出码透传不改写；macOS 自带 bash 3.2 兼容（禁 bash 4+ 特性）。
- **Coq/Rocq（`.v` 样例与模板）**：语句名 ASCII；面向库文件的注释遵守 gate7
  （CJK→0、五字段头注、30 行帽）；样例文件头部注明依赖与可编译性验证状态。

**English**: Python tools are stdlib-only, Python ≥3.9, argparse-based, UTF-8
headers with thorough module docstrings, aligned flag naming, exit codes
0=pass / 2=assertion-fail / 9=file-missing, fail-loud otherwise, full ledger output
(no conclusion-only). Bash is `set -u`, traps cleanup, exit-code passthrough, macOS
bash-3.2 compatible. In `.v` files: ASCII statement names, gate7 comment hygiene for
library files (CJK→0, five-field header, 30-line cap), and an honest header note
about dependency & compile-verification status.

## 3. 模块契约 / Module Contract（与 `cli/rocqwash` 的对接）

**中文**：`cli/rocqwash` 统一入口按下列契约路由（`cli/rocqwash help` 同文）：

1. 每个模块目录（`wash/ verify/ seam/ certify/ watch/ …`）至多一个**通用逐件入口**：
   不带前导下划线的 `.py`，argparse 接口，接受逐件参数（如 `<file.v>`）。
2. 入口在场（唯一非 `_` 前缀 .py）→ `cli/rocqwash <sub>` 自动路由，参数与退出码
   1:1 透传。
3. **`_` 前缀＝战役/席位专用工装**（路径硬编码、不接逐件 argv，如
   `wash/_abl1_wash.py`、`verify/_parse_fin_mac.py`）——统一入口**不代跑**，防止
   误触外部沙箱写；需要时直接 `python3 <path>` 调用。新战役工装请沿用 `_` 前缀命名。
4. 无通用入口 → CLI exit 3；多通用入口 → exit 4（列清单人工指认）。
5. 工装**禁写仓库外路径**除非在其 docstring 显眼声明 ROOT 并说明幂等性；批量工装
   必须幂等（已在盘=skip）＋ count 断言。
6. 新子命令接入：在 `cli/rocqwash` `case` 表加一行 `run_module` 分支即可，无需改 CLI
   其它部分。

**English**: each module dir exposes at most one *generic per-file entry* (a
non-underscore-prefixed `.py` with an argparse CLI); the unified entry auto-routes to
it with 1:1 passthrough. Underscore-prefixed tools are campaign/seat-specific
(hardcoded paths, no per-file argv) and are never auto-run by the unified entry —
use the `_` prefix for new campaign tools. No generic entry → exit 3; multiple →
exit 4. Tools must not write outside the repo unless their docstring prominently
declares the ROOT and idempotency; batch tools must be idempotent with count
assertions. New subcommands need one `run_module` line in `cli/rocqwash`.

## 4. 测试要求 / Test Requirements

**中文**——交付前必跑全绿。**零构建**：纯 Python 标准库＋bash（Python ≥ 3.9、
bash ≥ 3.2·macOS 自带），无编译构建步骤；涉编译的演示需 rocq/coqc，缺席时对应段
显式 SKIP＝NOT-RUN（绝不假绿）。交付前先跑一键自测套件（2026-10-30 实测
10 过 / 0 红 / EXIT 0）：

```bash
# ⓪ 一键自测套件（全仓总闸）
bash tests/run_tests.sh                              # 全绿 EXIT 0；任一红 EXIT 1
ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh  # 套件自检：注入恒红例 → 10过/1红/EXIT 1
```

套件覆盖面与形制（10 例：scan selftest／names `--expect` 正·含-Let·负判／gate4
净·脏两判／retrofit 干跑／wash 三判／cpu_guard `-Direct` 冒烟＋rc 传播）见
[`tests/README.md`](tests/README.md)。以下 ①–④ 为组件级专项命令（① 已由套件覆盖；
②③④ 未入套件，仍需手跑；②–④ 实测基线 2026-10-29，套件与 ① 于 2026-10-30 复测全绿）：

```bash
# ① 扫描器 E364 冻结向量组（正/负/名道/CAPTURE/混合面全量）→ SELFTEST PASS，exit 0
python3 scan/mac_stmt_scan.py --selftest

# ② 统一 CLI 冒烟：help / 未知子命令 / pending 模块口径
cli/rocqwash help                      # exit 0
cli/rocqwash bogus; echo $?            # exit 2
cli/rocqwash seam;   echo $?           # exit 3（seam/ 空）

# ③ 全链演示（scan→names→N=N→wash→verify；SKIP 显式标注 NOT-RUN）
make -C examples demo                  # exit 0；wash/verify 段按盘面 SKIP 或 RUN
make -C examples clean                 # 收尾清 build/

# ④ N=N 名表断言（任何洗/改写类 PR 必附：改前 vs 改后 有序全等）
cli/rocqwash names examples/demo_prop_leak.v \
  --compare examples/washed/demo_prop_leak_washed.v --expect 5   # 断言 5=5 PASS
```

附加要求：

- **新扫描道/白名单/提取器行为**：必须同步补 `mac_stmt_scan.py` 的
  `SELFTEST_POS/POS_CONCL/NEG/NAMES/CAPTURE/MIXED` 冻结向量（正例＋负例成对），
  且 `--selftest` 全绿。
- **洗/改写类 PR**：附 ②④ 式断言（改前改后 N=N ＋ 幂等重放输出 `applied=0 skipped=N`）。
- **涉编译的改动**：一律经 `tools/cpu_guard.sh` 包裹（见 §5），并核
  `.vo` 魔数 `436f712100015ff4` 与 mtime 新鲜度（绿判四件套口径）。
- **文档改动**：zh/en 双镜像同步，`make demo` 仍 exit 0。

**English**: everything here must pass before delivery. **Zero build**: pure stdlib
Python + bash (Python ≥ 3.9, bash ≥ 3.2 — macOS stock), no build step; compile demos
need rocq/coqc, absent → the segment SKIPs explicitly (SKIP = NOT-RUN, never
green-washed). Run the one-shot suite first (measured 2026-10-30: 10 pass / 0 fail /
EXIT 0):

```bash
# ⓪ one-shot suite (repo-wide gate)
bash tests/run_tests.sh                              # all green EXIT 0; any red EXIT 1
ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh  # suite self-check: injected always-red → 10 pass / 1 fail / EXIT 1
```

Coverage & format (10 cases) in [`tests/README.md`](tests/README.md). Items ①–④
below are component-level checks (① is suite-covered; ② ③ ④ are not in the suite and
stay manual; ②–④ baseline measured 2026-10-29, suite & ① re-measured green
2026-10-30): scanner selftest (exit 0), CLI smoke (help=0, unknown=2, pending=3),
`make -C examples demo` (exit 0, SKIPs explicitly labeled), and the N=N ordered
equality assertion for any wash/rewrite PR. New scanner channels/whitelist entries
must add paired positive+negative frozen selftest vectors; wash PRs must show
idempotent replay (`applied=0 skipped=N`); anything compiling goes through
cpu_guard with the `.vo` magic + freshness checks; doc changes keep zh/en mirrors
in sync.

## 5. cpu_guard 使用说明 / cpu_guard Usage（v3 温控包裹）

**中文**——**本机一切编译必经 cpu_guard 包裹**（防热过载宕机；硬件现实永不 ABORT，
只降速/降级）：

```bash
# 标准形（README Quick Start 同款）
bash tools/cpu_guard.sh -Reg /tmp/my_reg -Front 0 -Mid 1 -- \
  rocq c -native-compiler no -Q . "" my_proof.v

# 默认档（Front=2 Mid=2）：前 2 位 FRONT 全速，随后 2 位 MID(nice 10)，其余排队
bash tools/cpu_guard.sh -- <编译命令...>

# 小探针直通（不排队不注册，nice 19 后台防饿死）
bash tools/cpu_guard.sh -Direct -- ./probe.sh
```

| 参数 | 默认 | 含义 |
|---|---|---|
| `-Front N` | 2 | FRONT 档位数（nice 0 全速） |
| `-Mid N` | 2 | MID 档位数（nice 10） |
| `-MaxWaitSec N` | 900 | 排队超时秒数，到点降级 BACK（`taskpolicy -b nice -n 19`）放行不饿死 |
| `-Direct` | off | 探针直通（不排队不注册） |
| `-ThrottleFloor N` | 90 | 温控门：`pmset -g therm` 的 `CPU_Speed_Limit` < N% → 冷却轮询 |
| `-ThermalMaxWait N` | 3600 | 冷却上限秒数，到点警告放行（降级） |
| `-Reg <dir>` | `/tmp/cpu_guard.reg` | 登记表目录；双车道分道排队互不阻塞 |
| `--` | 必有 | 其后为被包裹命令 |

行为要点：进场 FIFO 登记（陈旧槽 `kill -0` 自动清）；前位完成即按当前位次上位；
退出码＝被包裹命令退出码（透传不改写）；冒烟自检
`bash tools/cpu_guard.sh -Front 2 -Mid 2 -- echo GUARD-OK`（实测输出
`[cpu_guard] FRONT launch …` ＋ `GUARD-OK`，exit 0）。

**English**: every compile on this machine goes through cpu_guard (thermal-overload
protection; it never ABORTs on hardware reality — it slows, queues, or degrades).
Default slots Front=2 (nice 0) + Mid=2 (nice 10), further submissions queue and are
demoted to BACK (`taskpolicy -b nice -n 19`) after 900 s. The thermal gate polls
`pmset -g therm`: below `ThrottleFloor` (90%) it cools, capped at `ThermalMaxWait`
(3600 s). `-Direct` bypasses queueing for small probes. `-Reg` splits lanes. Exit
code = wrapped command's. Smoke check:
`bash tools/cpu_guard.sh -Front 2 -Mid 2 -- echo GUARD-OK`.

## 6. 提交信息与评审 / Commits & Review

**中文**：`type: summary`（`feat:`/`docs:`/`fix:`/`test:`）；一次提交一个可验证单元。
评审三问：①证据在哪（退出码/输出）？②断言是否 fail-loud？③文档双镜像同步了吗？
答不出任何一问即退回。

**English**: commit as `type: summary`, one verifiable unit per commit. Review asks
three questions: where is the evidence (exit codes/output)? are assertions
fail-loud? are both doc mirrors synced? Any "no" sends it back.
