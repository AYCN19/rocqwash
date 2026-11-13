# 干净模式手册 · Clean Mode Manual（ROCWASH_CLEAN=1）

版本锚 Version anchor：rocqwash main `090be654192aa0ac599b71a945ed7595fc7bc522`（本地 `git rev-parse HEAD` 实测·2026-11-14）。语义变更只经 env 形；本手册不载 cw.sh 面。

## 一 · 语义 · Semantics

**缺省（env 未设或非 `1`）**：行为与历史版本逐字节相同——正本环境自动检测全量保持（探测 9.3 多路器、Set 仓 gate6/gate7 正本脚本、CW Live 工具链、判例机缺省路径），探测到什么用什么，探测不到按既有让席契约让席。

**干净模式（`ROCWASH_CLEAN=1`）**：声明本机不存在正本环境（ConstructiveWorld 判例机面）——
- 正本环境自动检测一律不执行；显式正本指针（`ROCWASH_ROCQ`／`GATE6_SCRIPT`／`GATE7_PROBE_SCRIPT`／`BORN_WORLD_ROCQ`／`ROCWASH_CANON_*`）不应用。
- 正本依赖面不探测、不静默失败：打印英文 `requires canonical environment: <缺什么>` 并按各件既有退出码族退出（六件工具 exit 9＝缺输入族；`tools/_abl1_4b_compile.py` 维持自身 exit 1 工具链契约）。
- 无正本依赖的面（自检/夹具/干跑/纯字面）全部照常可用，第三节四档清单逐面在列。

Default (env unset or not `1`): byte-identical historical behavior, with canonical-environment auto-detection fully active. Clean mode (`ROCWASH_CLEAN=1`): the canonical ConstructiveWorld environment is declared absent, auto-detection and explicit canonical pointers are not applied, and canonical-dependency faces print `requires canonical environment: <what>` and exit non-zero instead of probing; canonical-free faces (selftests, fixtures, dry runs, word-face tools) stay fully available.

## 二 · 正本环境指什么 · What the canonical environment is

判例机（sanctioned machine）上的 ConstructiveWorld 生产面，rocqwash 部分工具以硬编码缺省或自动探测消费它：

| 面 | 判例机路径（缺省值） | 消费者 |
|---|---|---|
| CW 主树＋cpu_guard＋Live 工具链 | `/Users/apple/Desktop/ConstructiveWorld` | run_tests.sh 探测、cw_doctor、toolchain_dyld_doctor、contrib_intake |
| Set 仓 gate6/gate7 正本脚本 | `/Users/apple/Desktop/ConstructiveWorld-Set/scripts/gates/` | run_tests.sh 探测、contrib_intake |
| Main 树 gate4 | `/Users/apple/Desktop/ConstructiveWorld-Main` | quad8_reconcile audit 域 |
| 战役工作区（W1 树/逐调账） | `/Users/apple/Desktop/S系Prop清除战役工单` | mac_stmt_scan 基准靶、frozen_call 逐调账缺省 |
| 四仓副本群 rq 副本 | `/Users/apple/Desktop/rocqwash` | quad8_reconcile 在册 ROOTS |
| 9.3 多路器（rocq/rocqworker） | `/Users/apple/Desktop/mac93_install_work/opam93/rocq93/` | run_tests.sh 缺省探测、toolchain_dyld_doctor 缺省 worker |
| PATH 工具链二进制 | `rocq`/`coqc`/`coqdep`/`ocamlc`/`otool` | probe_engine、registry_regen、_abl1_4b_compile、toolchain_dyld_doctor |

## 三 · 正本依赖四档清单 · Canonical-dependency census (four tiers)

### 3.1 可用 Available（干净模式全功能，Python 3 标准库即可；registry 系另需 `git`）

| 面 | 锚 |
|---|---|
| tools/：doc_lint、norm_lint、baseline_diff、chain_graph、ledger_sync、netname_normalize、render_events、red_dispatch、registry_audit、registry_fix、registry_union、select_audit、vacgen（零编译面） | 各件 `--selftest` 冻结矢量 |
| tools/：ci_triage `--selftest` 与 `--offline`、net_probe `--selftest`、cw_sentinel `--selftest`、pushci `--selftest`、evolve `--selftest`、registry_regen `--selftest`、wash_shape `--selftest`、unclog `--selftest`、contrib_intake `--selftest`、cw_doctor `--selftest`、toolchain_dyld_doctor `--selftest` | 罐装注入/临时夹具 |
| wash/：wash_engine、comment_sweep、cure_applier（干跑面）、probe_engine `--selftest`、world_hook；scan/：mac_stmt_scan `--selftest`／`--file`、scan_v4_token、dual_scan；names/mac_stmt_names `--expect` | 套件逐例 |
| verify/：verify_vo `--selftest`、gate4_comment_guard `--file`、erasure_classifier、extract_magic_check（桩链）、retrofit_gate7_irr 干跑；seam/、certify/（freeze_manifest、frozen8、push_gate）、watch/、wrapper/（scan_station、verify_born、quad8 `--selftest`／`--registry`、frozen_call `--selftest`、precedent_station） | 套件逐例 |

### 3.2 让席 SKIP（套件既有让席契约，干净模式下照常让席不充红）

| 面 | 让席判据锚 |
|---|---|
| t_gate7_wrapper | tests/run_tests.sh:409（`CANON`／`GATE7_PROBE_SCRIPT`） |
| t_quad8_check | tests/run_tests.sh:436（四仓副本目录在卷判定） |
| t_gate6_born_wrapper | tests/run_tests.sh:450 |
| t_verify_gate6 | tests/run_tests.sh:468 |
| t_cure_pack 编译段、t_probe_engine 真 rocq 节 | tests/test_cure_pack.py:492、tests/test_probe_engine.py:259（`ROCWASH_ROCQ` 门控） |

### 3.3 降级 Degraded（功能收窄但可用）

| 面 | 降级形 | 锚 |
|---|---|---|
| tools/registry_regen.py | 无 `coqdep` 时退 require 边序 | tools/registry_regen.py:341,612 |
| ci_triage `--offline` | 本地日志面替代拉取 | docs/CAPABILITY-INDEX.md ci_triage 条目 |
| toolchain_dyld_doctor 显传 `--worker`（及 `--smoke` 显传 `--coqc`／`--guard`） | 分析指定二进制而非判例机缺省 | tools/toolchain_dyld_doctor.py:395-402 |
| quad8_reconcile `--roots-file` | 夹具根替代在册 ROOTS | wrapper/quad8_reconcile.py:583,588 |
| cw_doctor `--injector` | 罐装四域聚合 | tools/cw_doctor.py:1152 |
| contrib_intake gate7 可用性面 | 只记可用性布尔不执行 | tools/contrib_intake.py:703-716 |

### 3.4 不可用 Unavailable（干净模式显式申报 `requires canonical environment`，exit 9；末行注记者 exit 1）

| 面 | 申报内容 | 实装锚 |
|---|---|---|
| mac_stmt_scan `--baseline` | 战役工作区 S09 worldT_mac 基准靶（通用扫描走 `--file`；正本经 wrapper/scan_station.py 闸——正本本体冻结禁改，直调正本不受闸、按既有缺靶契约报错） | wrapper/scan_station.py（透传前闸） |
| toolchain_dyld_doctor 缺省 worker 链 | 判例机 rocqworker 缺省（`--worker`／env 可绕） | tools/toolchain_dyld_doctor.py（worker 解析处） |
| cw_doctor 四域真聚合（无 `--injector`） | CW Live 树（guard 缺省/注册册账/探针世界） | tools/cw_doctor.py（run() 值校验后闸·usage 面退出码不受扰） |
| probe_engine 真编译探针 | rocq 工具链（缺省 `--rocq-cmd` 模板即真面；显式 `--rocq-cmd` 桩与 `--selftest` 仍可用） | wash/probe_engine.py（必填参校验后闸） |
| quad8_reconcile `freeze`/`check`（无 `--roots-file`） | 在册四仓正本副本群 | wrapper/quad8_reconcile.py（分发前闸） |
| frozen_call 真调用面 | 缺省仓内冻结名单或战役逐调账（显传 `--manifest`＋`--log` 的调用方自有面仍可用） | wrapper/frozen_call.py（自检分发后闸） |
| _abl1_4b_compile | OCaml 工具链（ocamlc/ocamldep 经 opam env） | tools/_abl1_4b_compile.py（导入期工具链闸） |

套件级：干净模式下 tests/run_tests.sh 的正本探测块（`CANON` 判定＋`ROCWASH_ROCQ`/`GATE7_PROBE_SCRIPT`/`GATE6_SCRIPT`/`BORN_WORLD_ROCQ` 缺省指认）整体跳过，3.2 各例按既有契约让席。

## 四 · 用法 · Usage

```sh
# 全套件·干净模式（正本依赖例让席）
ROCWASH_CLEAN=1 bash tests/run_tests.sh

# 单件·干净模式探活
ROCWASH_CLEAN=1 python3 -B tests/test_clean_mode.py

# 单器示例：干净模式下真编译面显式申报（实测 2026-11-14·rc=1·申报词面转录于下）
ROCWASH_CLEAN=1 python3 tools/_abl1_4b_compile.py
  requires canonical environment: the OCaml toolchain (ocamlc/ocamldep on PATH via opam env)
```

## 五 · 边界 · Boundaries

- 干净模式只治理正本环境面；网络面（ci_triage/cw_sentinel/pushci/net_probe 的拉取与推送）由 NETRED 纪律另行治理，`ROCWASH_CLEAN` 不关网络。
- 干净模式不改变任何退出码族语义：申报退出沿用各件既有缺输入码；不新增码位。
- `git` 是 registry 系工具的基础依赖（非正本面）；干净模式不豁免它。
- The switch governs the canonical-environment face only; the network face stays under the standing NETRED discipline, and no exit-code family is redefined.
