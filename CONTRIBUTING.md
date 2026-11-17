# Contributing to rocqos (rocqwash) / 贡献指南

> 双语指南：每节先中文、后 English 摘要。架构与组件现状见
> [`docs/zh/architecture.md`](docs/zh/architecture.md) /
> [`docs/en/architecture.md`](docs/en/architecture.md)。
>
> 正式名 **rocqos**（Rocq operations suite）·链接名仍 `rocqwash`（一仓两名·2026-11-15 定）。current state锚=tag `rw-v0.1.0-20261114`（公开仓·CI 绿）。全量契约面=[`docs/CAPABILITY-INDEX.md`](docs/CAPABILITY-INDEX.md)·MCP 面=[`docs/mcp.md`](docs/mcp.md)。

## 0. 核心原则 / Core Principles

**中文**：rocqwash 只收「类型论结构性判据可机检」的贡献。三条诚实律是一票否决项：

1. **报清单不报清白**（E364）——工具只出命中清单与归类注记；「无泄露/已通过」结论
   唯内核判据（census/魔数/退出码）可出。0 命中必须另过负证对照。
2. **fail-loud**——断言失败一律非零退出＋响亮输出；禁静默吞错、禁spurious pass、禁把
   NOT-RUN 标成通过（SKIP 必须显式标注）。
3. **幂等可重放**——一切改写操作 exact-string ＋ count 断言 ＋ 已present in the tree即 skip。

**English**: rocqwash only accepts contributions checkable by type-theoretic
structural criteria. Three honesty laws are veto-level: (1) report the hit list,
never a cleanliness verdict — verdicts belong to kernel criteria only, and 0-hit
results require negative-vector control; (2) fail-loud — non-zero exit + loud output
on any assertion failure, no green-washing, SKIPs must be explicit; (3) idempotent
replay — exact-string + count assertions + skip-if-already-applied.

## 0.5 许可与贡献者协议 / License & Contributor Agreement

**中文**：本仓以 **AGPL-3.0-or-later** 授权（仓根 `LICENSE` 全文）。贡献条款：

1. **ICLA 先签**：首次贡献被合并前签署 [`CLA/ICLA.md`](CLA/ICLA.md)（版权与专利双授予＋双许可授权＋AI 作为工具之人为作者主体系声明）；签署件交 Steward 王宝军（168888@live.cn·管辖：中华人民共和国法律）。企业贡献者走 [`CLA/CCLA.md`](CLA/CCLA.md)。
2. **人为主体系**：贡献须含人类实质性创作；AI 工具可辅助，但提交者为作者并对内容负责（`NOTICE` AUTHORSHIP STATEMENT 同源）；PR 描述请披露 AI 辅助面。
3. **协议不变量**：贡献一经并入即按 AGPL-3.0-or-later 授权；不接受「仅私有许可」的补充条款（商业许可轨道见 [`CLA/commercial_license_template.md`](CLA/commercial_license_template.md)·与贡献无关）。

**English**: the repo is licensed **AGPL-3.0-or-later** (see `LICENSE`). Terms: (1) sign
[`CLA/ICLA.md`](CLA/ICLA.md) before your first merged contribution (copyright + patent
grant, dual-license authorization, and the human-as-author representation; signed copies
to the Steward, Wang Baojun, 168888@live.cn, PRC law; corporate contributors use the
CCLA). (2) Contributions require substantial human creative authorship; AI tools may
assist but the submitter is the author and discloses AI assistance in the PR. (3) Merged
contributions are licensed AGPL-3.0-or-later; no private-only add-on terms.

## 1. 贡献流程 / Contribution Workflow

**中文**：

0. **ICLA 与 intake 预检**：签署 ICLA（见 §0.5）＋只读四闸自检
   `bash cw.sh contrib-intake --contrib-repo <your-repo>`（贡献仓/基线仓/ref/路径/jargon
   映射参数化·BLOCK 即按提示补正）。AI 辅助面在 PR 描述披露。
1. **认领模块槽位**：`workflows/` 占位与各模块深件（R4 提取侧三源、`verify/`
   统一入口conclude / close——需历史件改名·冻结解禁后、`certify/` conclude / close——见
   docs/zh/architecture.md §4 注①③）为开放槽位（空目录＝未落地；`tests/` 已落
   自测套件，新增用例直接扩 `tests/run_tests.sh`，见 §4）。先在 issue/task instruction认领，
   避免与并发席位撞车（本仓库多席位并发开发，提交前 `git log --oneline -5` 看最新盘面）。
2. **分支与提交**：从默认分支开工作分支；提交信息用 `type: summary` 形制
   （`feat:` / `docs:` / `fix:` / `test:`，参照现有 log）。
3. **实现**：遵守 §2 代码规范与 §3 模块契约。
4. **自证**：跑 §4 测试要求全部命令，退出码与输出摘要贴入 PR/交付说明。新扫描道/
   allowlist/提取器行为必须同时补 `--selftest` 冻结向量。
5. **文档同步**：用户可见行为变化必须同步 `docs/zh/` 与 `docs/en/` 双语镜像＋
   `README.md`；本目录文档与代码不一致视为 bug。
6. **评审判据**：评审只认机械证据（退出码、md5、count 断言、selftest PASS），
   不认「我测过了」口头声明。

**English**: (0) sign the ICLA (see §0.5) and run the read-only four-gate intake check `bash cw.sh contrib-intake --contrib-repo <your-repo>`; disclose AI assistance in the PR. (1) claim an open module slot (`workflows/` placeholder and the module
deep pieces: the R4 extraction-side three-source conjunction, the `verify/` unified
entry unification (needs a historical-file rename, after the freeze lifts) and the
`certify/` entry unification (see docs/zh/architecture.md §4 notes ①③) — empty dir =
not landed; `tests/` already hosts
the suite, extend `tests/run_tests.sh` for new cases, see §4); check recent commits
first — this repo
is developed concurrently by multiple agent / seat-workers. (2) branch from the default branch,
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
  - md5 指纹：凡write / persist to disk对照/冻结，输出源文件 md5（参照两器 `md5_of`）。
  - **语言与标准化五闸**（新件硬性）：注释/docstring/帮助与运行时输出文字一律英文；
    新件五字段英文头（`Purpose. / Interface. / Dependencies. / Evidence. / Exit-codes.`
    ·≤30 行·见 [`docs/annotation-standard-v1.0-20261113.md`](docs/annotation-standard-v1.0-20261113.md)）；
    新代码面 CJK=0；AI 味电池 CLEAN（`python -I tools/ai_flavor.py --file <件>`·36 面+em-dash 双电池·目标 0）；
    黑话按 [`seeds/jargon/jargon-map.json`](seeds/jargon/jargon-map.json) 规避（`norm_lint` 机检）；
    运行时输出串改动必须同步测试断言。豁免面（种子逐字转录/测试数据/`docs/zh/` 镜像/内部ledger (data surface) / record list (generic prose)）
    登记制：凡豁免必登记（件:行·类·依据）·未登记命中=违规。
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
about dependency & compile-verification status. New files additionally pass the
five-gate standardization set: English-only comments/docstrings/help/runtime strings,
five-field English header (annotation standard, 30-line cap), CJK=0 on new code faces,
clean ai-flavor battery (`python -I tools/ai_flavor.py --file <file>`), jargon-map
discipline (`norm_lint` machine-checked), and output-string changes synced to test
assertions. Exemptions (verbatim seed transcriptions, test data, `docs/zh/` mirrors,
internal ledgers) are registration-based: an unregistered hit is a violation.

## 3. 模块契约 / Module Contract（与 `cli/rocqwash` 的对接）

**中文**：`cli/rocqwash` 统一入口按下列契约路由（`cli/rocqwash help` 同文）：

1. 每个模块目录（`wash/ verify/ seam/ certify/ watch/ …`）至多一个**通用逐件入口**：
   不带前导下划线的 `.py`，argparse 接口，接受逐件参数（如 `<file.v>`）。
2. 入口在场（唯一非 `_` 前缀 .py）→ `cli/rocqwash <sub>` 自动路由，参数与退出码
   1:1 透传。
3. **`_` 前缀＝战役/席位专用工装**（路径硬编码、不接逐件 argv，如
   `wash/_abl1_wash.py`、`verify/_parse_fin_mac.py`）——统一入口**不代跑**，防止
   误触外部沙箱写；需要时直接 `python3 <path>` 调用。新战役工装请沿用 `_` 前缀命名。
4. 无通用入口 → CLI exit 3；多通用入口 → exit 4（列清单人工指认）。例外：`certify/`
   三通用件与 `verify/` 四通用件已由 CLI 显式分派conclude / close——`rocqwash certify
   freeze|push_gate|frozen8 [args...]`、`rocqwash verify
   gate4|verify_vo|verify_gate6|adaptation [args...]`
   1:1 透传；无子动词仍走 exit 4 列清单，未知子动词 exit 2（verify 分派·2026-10-31
   适配席 rqadapt；verify_gate6 补件 20261101 席 rqsup4 四巡；certify frozen8 补件
   20261101 席 rqsup4 五巡·冻结件零改动）。
5. 工装**禁写仓库外路径**除非在其 docstring 显眼声明 ROOT 并说明幂等性；批量工装
   必须幂等（已present in the tree=skip）＋ count 断言。
6. 新子命令接入：在 `cli/rocqwash` `case` 表加一行 `run_module` 分支即可，无需改 CLI
   其它部分。

**English**: each module dir exposes at most one *generic per-file entry* (a
non-underscore-prefixed `.py` with an argparse CLI); the unified entry auto-routes to
it with 1:1 passthrough. Underscore-prefixed tools are effort / work stream/agent / seat-worker-specific
(hardcoded paths, no per-file argv) and are never auto-run by the unified entry —
use the `_` prefix for new effort / work stream tools. No generic entry → exit 3; multiple →
exit 4. Exception: `certify/`'s three generic pieces and `verify/`'s four generic
pieces are unified via explicit CLI dispatch — `rocqwash certify
freeze|push_gate|frozen8 [args...]` and `rocqwash verify
gate4|verify_vo|verify_gate6|adaptation [args...]`
pass through 1:1; no sub-verb still exits 4 with the listing, an unknown sub-verb
exits 2 (verify dispatch: 2026-10-31, adapter agent / seat-worker; `verify_gate6` added 2026-11-01
agent / seat-worker rqsup4 round 4; certify `frozen8` added 2026-11-01 agent / seat-worker rqsup4 round 5 —
zero frozen-file changes).
Tools must not write outside the repo unless their docstring prominently
declares the ROOT and idempotency; batch tools must be idempotent with count
assertions. New subcommands need one `run_module` line in `cli/rocqwash`.

## 4. 测试要求 / Test Requirements

**中文**——交付前必跑全绿。**零构建**：纯 Python 标准库＋bash（Python ≥ 3.9、
bash ≥ 3.2·macOS 自带），无编译构建步骤；涉编译的演示需 rocq/coqc，缺席时对应段
显式 SKIP＝NOT-RUN（绝不spurious pass）。交付前先跑一键自测套件（历史基线 2026-11-01 五巡 31 过 0 红；**current state名册以
[`tests/README.md`](tests/README.md) 为准·tag `rw-v0.1.0` 时点=67 例**）：

```bash
# ⓪ 一键自测套件（全仓总闸）
bash tests/run_tests.sh                              # 全绿 EXIT 0；任一红 EXIT 1
ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh  # 套件自检：注入恒红例 → 1 红/EXIT 1（计数随名册）
```

套件覆盖面与形制（例数随名册推进·tag `rw-v0.1.0`=67：scan selftest／names `--expect` 正·含-Let·负判／gate4
净·脏两判／adaptation dry run／wash 战役件三判／wash_engine 六判／verify_vo 十三判
（含 `--require-fresh` fresh-compile 防线四判）／
seam_probe 四机制／freeze_manifest 四判／push_gate UNION 六判＋window 四判／
watch 零网络向量组／cpu_guard `-Direct` 冒烟＋rc 传播／netname_normalize 九节／
verify_fresh 八节／extract_magic 十节）见
[`tests/README.md`](tests/README.md)。以下 ①–④ 为组件级专项命令（① 已由套件覆盖；
②③④ 未入套件，仍需手跑；②–④ 实测基线 2026-10-31）：

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
cli/rocqwash verify bogusverb 2>&1; echo $?          # exit 2（未知子动词·列合法子动词 gate4|verify_vo|verify_gate6|retrofit）
cli/rocqwash watch ci --runs-json <f>; echo $?  # watch.py 已路由（ci 离线证据判读）

# ③ 全链演示（scan→names→N=N→wash→verify；SKIP 显式标注 NOT-RUN）
make -C examples demo                  # exit 0；wash 段台账真跑（引擎输出与参照件逐字节恒同）
make -C examples clean                 # 收尾清 build/

# ④ N=N 名表断言（任何洗/改写类 PR 必附：改前 vs 改后 有序全等）
cli/rocqwash names examples/demo_prop_leak.v \
  --compare examples/washed/demo_prop_leak_washed.v --expect 5   # 断言 5=5 PASS
```

附加要求：

- **新扫描道/allowlist/提取器行为**：必须同步补 `mac_stmt_scan.py` 的
  `SELFTEST_POS/POS_CONCL/NEG/NAMES/CAPTURE/MIXED` 冻结向量（正例＋负例成对），
  且 `--selftest` 全绿。
- **洗/改写类 PR**：附 ②④ 式断言（改前改后 N=N ＋ 幂等重放输出 `applied=0 skipped=N`）。
- **涉编译的改动**：一律经 `tools/cpu_guard.sh` 包裹（见 §5），并核
  `.vo` 魔数 `436f712100015ff4` 与 mtime 新鲜度（four-point pass criterion口径）。
- **文档改动**：zh/en 双镜像同步，`make demo` 仍 exit 0。
- **零新增红判据**：改动后套件红集 ⊆ 改前基线红集（红=数据·Windows 宿主面spurious failure族照
  `tests/README.md` 名册cross-check against the reference·过/略不减）；自致计数失配（自己改动造成的账面过时）必须当场同步，
  存量债另波清偿。

**English**: everything here must pass before delivery. **Zero build**: pure stdlib
Python + bash (Python ≥ 3.9, bash ≥ 3.2 — macOS stock), no build step; compile demos
need rocq/coqc, absent → the segment SKIPs explicitly (SKIP = NOT-RUN, never
green-washed). Run the one-shot suite first (historical baseline 2026-11-01 five
rounds 31 pass / 0 fail; **current roster in [`tests/README.md`](tests/README.md),
67 cases at tag `rw-v0.1.0`**):

```bash
# ⓪ one-shot suite (repo-wide gate)
bash tests/run_tests.sh                              # all green EXIT 0; any red EXIT 1
ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh  # suite self-check: injected always-red → 1 fail / EXIT 1 (count follows the roster)
```

Coverage & format (roster-grown; 67 cases at tag `rw-v0.1.0`) in [`tests/README.md`](tests/README.md). Items ①–④
below are component-level checks (① is suite-covered; ② ③ ④ stay manual; ②–④
baseline measured 2026-10-31): scanner selftest (exit 0), CLI smoke (help=0,
unknown=2, bare `certify`=4 ambiguous-entry listing, `certify freeze|push_gate|frozen8`
explicit dispatch with 1:1 passthrough, unknown certify sub-verb=2, watch routed), `make -C examples demo`
(exit 0 — the wash step now
runs for real via the ledger, byte-identical to the reference specimen), and the
N=N ordered equality assertion for any wash/rewrite PR. New scanner
channels/whitelist entries must add paired positive+negative frozen selftest
vectors; wash PRs must show idempotent replay (`applied=0 skipped=N`); anything
compiling goes through cpu_guard with the `.vo` magic + freshness checks; doc changes keep zh/en mirrors in sync. Zero-new-red criterion: the post-change red
set must be a subset of the pre-change baseline roster (red is data; Windows host-face
false-red family per the roster); self-inflicted count staleness must be fixed in the
same change, existing debt is paid in its own wave.

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
| `-Direct` | off | probe (tool citation) / check (generic sense)直通（不排队不注册） |
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

**中文（维护侧）**：maintainer 提交一律 GPG 签名（仓 `commit.gpgsign` 沿用）；
[`更新账.md`](更新账.md) append-only（每次落岸恰一行·CRLF 硬闸=numstat 恰 1 加 0 删）；
stage 恰清单禁 `-A`；多席位并发期树检先行（他席未提交件零触碰零卷入）。

**English (maintainer side)**: maintainer commits are GPG-signed; the ledger
`更新账.md` is append-only (exactly one line per integration, CRLF gate = numstat exactly
+1/-0); stage explicit paths only; during concurrent-agent / seat-worker windows check the tree first
and never touch other agent / seat-workers' uncommitted work.

## 7. 接口五纪律 / Interface Five Disciplines（工作流配合面·v37 起共同契约）

**中文**——凡「工作流配合面」器（现役：`tools/cw_sentinel.py`（sentinel）／
`tools/wash_shape.py`（wash-shape）／`tools/unclog.py`（unclog）／
`tools/pushci.py`（pushci）·v38 起 `tools/cw_doctor.py` 同形扩面）接口必须五纪律
全承。本节与
[`docs/workflow-integration-whitepaper-v1.0-20261111.md`](docs/workflow-integration-whitepaper-v1.0-20261111.md)
§1 同源（逐器机理与命令正本在彼）；速查在 [`README-cw.md`](README-cw.md)
「工作流配合接口」节。

1. **JSON-in/JSON-out·schema designated·确定性**：出账一律 `--json OUT`，schema designated——
   `rocqwash-sentinel/1`／`rocqwash-shape/1`／`rocqwash-unclog/1`／
   `rocqwash-pushci/1`（v38 起 `rocqwash-cwdoctor/1`·v39 起
   `rocqwash-doclint/1`）；loop 态事件流 `--events FILE` 逐行 JSONL（sentinel 行
   schema `rocqwash-sentinel-event/1`·键含 `seq` 事件流内单调）。`--json` write / persist to disk
   `sort_keys`，同输入重跑字节级恒同；报告零墙钟零绝对路径（路径只出基名；
   `--sleep-scale 0` 时事件行 `ts` 关闭并以 note 注记）。
2. **退出码 0/1/2/9 口径（a failing result is data, not a tool failure·响亮 stdout）**：0=绿／巡检完成／
   unclogged（pushci success/dry-run=0）；1=数据性未竟（洗未尽 partial/plan-miss·
   诚实墙 wall／轮尽 rounds-exhausted·pushci
   heal-exhausted/unstable/toolchain）；2=用法错（含冻结件红拒·注入场景形错）；
   9=缺/fail-loud（源不可达·injector 未覆盖·路径缺失·子进程 rc≠0）。数据红
   （CI 红/堵塞/墙）走事件流与 report 红账，**不进退出码**；工作流分流两级：
   先按退出码分器面（2=改调用·9=补目标），再读 JSON 按 verdict/kind 分数据面。
3. **--once/--loop 双模**：`--once` 单轮出账即退（工作流步骤内联用·wash-shape
   缺省即 once，plan 段零写盘）；`--loop --interval S` 长驻哨态（后台 bash 任务
   用）＋轮帽可自停（sentinel/wash-shape `--max-rounds N`·unclog `--loop-max N`
   命周数）；`--sleep-scale F` 全部 sleep 乘 F（0=零真睡＋关事件 ts）——离线
   演练/确定性钉，生产形不给。
4. **--injector 离线可测**：工作流自测/CI 演练一律注入形＋`--sleep-scale 0`——
   零真网络零真编译。injector 未覆盖＝fail-loud 9，**绝不静默走真网络**
   （pushci 须 `--injector DIR`＋`--git-caller FILE` 成对·单边给出=用法错 2）；
   unclog 注入下 chain_graph/cure_applier/scan_v4_token/frozen8 照旧真跑
   （真编排非傀儡）。三器 `--selftest` 与套件挂接件（`tests/test_cw_sentinel.py`／
   `test_wash_shape.py`／`test_unclog.py`／`test_pushci.py`）全部零真网络零真
   编译，即此纪律的自证。
5. **编排零新引擎**：器内部全 subprocess 直调既有引擎——sentinel classification全权在
   `ci_triage`、链根全权在 `chain_graph`；wash-shape 五洗引擎（gate4/scan_v4/
   cure_applier/comment_sweep/registry_union）；unclog 五步（probe_engine/
   chain_graph/cure_applier/scan_v4_token/frozen8）；pushci 编排 v35 四器。
   此律双向：**工作流侧也不为「再判一次红/再挑一次根」写新逻辑**——调器，
   读它的 JSON。真编译一律经 cpu_guard（§5）；unclog 以 `--guard PATH
   --guard-reg DIR --guard-front N --guard-mid N --guard-maxwait N` 透传。

补：python3 纯 stdlib＋fail-loud＋零硬编码路径（§2 同律）。`cw.sh` 是 1:1 透传
入口（exec·不改写参数与退出码）——工作流里 `bash cw.sh <tool>` 与直调
`python3 tools/<tool>.py` 语义全同（嵌段一律走 cw.sh 形，少一处路径耦合）。

**新增器入既有流程图景**（v35-v39 五波在既有流程中的落点）：

- **贡献自证链（§1.4／§4）**：新器一律补 `--selftest` 冻结矢量＋挂接
  `tests/run_tests.sh`（v39 current state 54 例）＋过 `tools/doc_lint.py` 三查
  （文档←→实现一致性：工具表/计数/旗标——旗标逐枚对照各器 `--help` 实出）。
- **CI 红炉修复链（README-cw 同款）**：doctor→net-probe→pushci（内嵌
  watch+heal）→triage——v35 四诊断器与 v36 编排器即此链的构件化与一键化。
- **实时服务面（v37-v39 新增）**：sentinel 三路信号源→JSONL 事件流→人审→
  unclog（`--audit` 只读基线→`--apply` allowlistapply）／wash-shape（plan 人审→
  `--apply`）；体检预检 cw-doctor；接驳预设 `--on-red-preset`（unclog=dry run·
  pushci=--dry-run·缺省安全态invariant / hard requirement）。运行规程见
  [`docs/ops-realtime-service-v1.0-20261111.md`](docs/ops-realtime-service-v1.0-20261111.md)。
- **文档conclude / close链（v39）**：文档改动交付前跑 `bash cw.sh doc-lint --repo .`
  三查零漂（verdict consistent·exit 0）。

**English**: tools on the workflow-facing surface (sentinel / wash-shape /
unclog / pushci; cw-doctor in the same shape since v38) must honor the five
interface disciplines of the workflow-integration whitepaper §1: (1) JSON-in/out
with named schemas (rocqwash-sentinel/1, rocqwash-shape/1, rocqwash-unclog/1,
rocqwash-pushci/1; rocqwash-cwdoctor/1, rocqwash-doclint/1 since v38/v39),
sort_keys byte-identical reports and JSONL event streams; (2) exit codes 0/1/2/9
where red is data, not tool failure — workflows branch on exit codes first
(2=fix the call, 9=fix the target), then on JSON verdicts; (3) --once/--loop
dual mode with round caps and `--sleep-scale` as an offline determinism pin;
(4) --injector offline canned testing — uncovered responses fail loudly, the real
network is never touched silently, and pushci requires the injector/git-caller
pair; (5) zero new engines — orchestration of existing engines via subprocess
only, and the same holds on the workflow side: call the tool, read its JSON,
never re-implement a verdict. New tools enter the existing flows as: --selftest
frozen vectors + suite hookup + doc_lint three checks; the CI repair chain
doctor→net-probe→pushci→triage; the realtime service surface (sentinel events →
human review → unclog audit/apply, wash-shape plan/apply, cw-doctor checkup,
--on-red-preset relays); and the doc-closing chain (`bash cw.sh doc-lint --repo .`). The authoritative
per-tool contract face is [`docs/CAPABILITY-INDEX.md`](docs/CAPABILITY-INDEX.md);
the MCP surface (24 capabilities) is [`docs/mcp.md`](docs/mcp.md); the language-engine
stack (ai-flavor / jargon / termbase / i18n pipeline / auto-round) is registered in
[`seeds/engines/ENGINES.md`](seeds/engines/ENGINES.md).
