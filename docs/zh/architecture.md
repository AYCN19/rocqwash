# rocqwash 架构（Architecture·中文版）

> 状态快照：2026-10-31（certify 深件 `push_gate.py` 推窗四判据＋UNION v2 清单落地＋
> `watch/` 模块首件 `watch.py` 落地＋套件扩至 16 例·席 rqwash2 施刀）。本文档如实
> 反映仓库当前盘面：已实现组件以源代码逐条核对，未落地组件以空目录/占位如实标注。
> 英文镜像见 [`docs/en/architecture.md`](../en/architecture.md)。快照后仓库仍在活跃
> 开发（并发席位持续落库），以代码为准。

## 1. 定位与核心原则（Positioning & Core Principle）

rocqwash 是 Coq/Rocq 构造性数学项目的机械式诊断／洗／验证／认证工具链：

> **核心原则**：凡可用类型论结构性判据机检的，一律不交给概率模型猜。
> (What can be mechanically verified via type-theoretic structural criteria shall never be delegated to probabilistic models.)

三条诚实律贯穿全部组件：

1. **报清单不报清白**（E364 盲区律）——扫描器只出命中清单＋逐 hit 归类注记；
   「无泄露」判词唯内核 census（SortAlive `__`-census）可出，任何 0 命中须另过
   负证对照（`--selftest` 内嵌 E364 向量）方可采信。
2. **fail-loud**——断言失败／文件缺失／未知命令一律非零退出，禁静默吞错；
   注释/字符串未闭合、孤儿 closer 等逐笔出账。
3. **幂等可重放**——洗/补丁类操作 exact-string ＋ count 断言 ＋ 已在盘即 skip，重放安全。

## 2. 三条链合一（Three Chains in One）

```
Toolchain        工具链（scripts + templates + canonical recipes）
    ↓
Logic Chain      逻辑链（criteria + gates + calibration standards）
    ↓
Derivation Chain 推导链（input → wash → verify → land → certify → push）
```

## 3. 工具链数据流（Toolchain Data Flow）

```
                    ┌──────────────────────────────────────────────────┐
                    │  tools/cpu_guard.sh v3 — 一切编译的温控包裹          │
                    │  （FRONT/MID/BACK 动态梯队列 + pmset 温控门）        │
                    └────────────────────────┬─────────────────────────┘
                                             │ 包裹每一次编译
  .v ──▶ scan ──▶ names ──▶ wash ──▶ compile ──▶ verify(R4) ──▶ seam ──▶ certify ──▶ watch
        已实现   已实现   已实现  (guard)     已实现*      已实现*   已实现    已实现

  已实现*＝通用逐件首件落地（wash＝台账执行器·verify＝绿判四件套·seam＝指纹探针；
          R4 全三源为待办）

  统一入口：cli/rocqwash（scan / names / wash / verify / seam / certify / watch 七子命令）
```

| 站 | 输入 | 输出 | 状态 |
|---|---|---|---|
| scan | 单件 `.v` | 命中清单＋归类注记（stdout / `--json` / `--hits-csv`） | 已实现 |
| names | 单件或两件 `.v` | 有序语句名清单＋ N=N 有序全等断言 | 已实现 |
| wash | 单件 `.v` ＋ 台账 JSON | 洗后 `.v`（exact-string+count·幂等） | 已实现（`wash_engine.py`·台账须显式给）；战役批量工装亦在库 |
| compile | `.v` | `.vo`（魔数 `436f712100015ff4` 咬合） | 经 cpu_guard |
| verify(R4) | `.v`+`.vo` 对（±rc/log 旁证） | 绿判四件套逐件账＋判定 | 已实现（`verify_vo.py`）；R4 全三源统一入口待办（见 §4 注②） |
| seam | 单件 `.v` | W13 四机制指纹候选清单＋处方映射 | 已实现（`seam_probe.py`·候选非定谳） |
| certify | 目录/多世界＋清单 | 两层冻结清单 freeze/check＋推窗四判据＋UNION v2 | 已实现（`freeze_manifest.py`＋`push_gate.py`·见注③） |
| watch | runs 证据/远端 | CI 在飞监控＋钉 IP 推送（干跑默认）＋ls-remote 确证 | 已实现（`watch.py`·零 dispatch 结构保证） |

## 4. 组件表（Components·以源码核对）

形态列：**通用逐件**＝带 argparse 接口、可被 `cli/rocqwash` 自动路由；
**战役专用**＝`_` 前缀、路径硬编码、不接逐件 argv，统一入口不代跑（直接 `python3` 调用）。

| 模块 | 文件 | 形态 | 状态 | 要点 |
|---|---|---|---|---|
| `scan/` | `mac_stmt_scan.py` | 通用逐件 | **已实现** | 语句面 Prop 裸形扫描器：冻结道五族 P1–P5（13 子通道：Qlt/Qle/`==`/exists·and·or·not·false/裸`=`/`<=`·`<`·`>=`·`>`）＋负捕获道三族（P6_In/P8_True/P9_proper·结论位 CAPTURE/前提位 EXEMPT）；分类四分 RED/WHITELIST/EXEMPT/CAPTURE；白名单与 BRIDGE_FAMILY 在册；混合面（载体并现裸形）检测；`--manifest` 四账对账（swallowed/blind/kind_drift/line_drift·blind=∅ 断言）；`--selftest` E364 冻结向量组；`--baseline` S09 基准试射 |
| `names/` | `mac_stmt_names.py` | 通用逐件 | **已实现** | 顶层语句名有序清单提取器：census 口径（9 kind·不含 Let）／`--include-let` 会师口径；`--compare` 两件有序 1:1 全等断言（N=N 形·不等 exit 2）；`--expect` 计数断言；`--kinds` 过滤；ARM2 证明体独立成臂消费；Unicode 名道；fail-loud 全程 |
| `wash/` | `wash_engine.py` | 通用逐件 | **已实现**（2026-10-31） | 通用逐件规范洗引擎：`_abl1_wash.py` 应用循环 1:1 泛化为 argv 台账驱动——exact-string＋count 断言＋幂等（new 在盘且 old 绝迹=skip）＋嵌套括号感知（注释/字符串掩蔽后括号自平衡机检）＋写隔离（永不回写 `--file`）＋fail-loud（任一 FAIL 该文件整笔不落盘）。台账 JSON＝PATCHES 账本逐字段直译（tag/old/new/expect）。无台账 exit 3（不猜·SKIP 语义）。`--selftest` 七判冻结向量 |
| `wash/` | `_abl1_wash.py` | 战役专用 | 已落库 | 席 abl1 批洗工装：exact-string ＋ count 断言 ＋ 幂等（new 已在盘=skip）；嵌套括号感知；`ROOT` 硬编码外部战役沙箱、不接 argv |
| `verify/` | `verify_vo.py` | 通用逐件 | **已实现**（2026-10-31） | 通用逐件绿判四件套机检：(.v,.vo) 对＋可选 rc/log 旁证——①exit==0（`--rc`/`--exit-file`）②log 零 Error 行 ③.vo 魔数 `436f712100015ff4` ④.vo 严格新于 .v；判据承 `_parse_fin_mac.py:82-108` 冻结口径；缺席旁证＝NOT-RUN 显式出账不计绿（③④必检）；`--selftest` 九判冻结向量 |
| `verify/` | `_parse_fin_mac.py` | 战役专用 | 已落库 | censusFIN_mac 解析道：提取擦除语义（RED iff `__` 现于 let 体/型注·含 Set-cloaked Prop）＋绿判四件套并查（exit 码/log 零 Error/`.vo` 魔数/`.vo` mtime 新鲜度）＋ann 正则双形律 |
| `verify/` | `gate4_comment_guard.py` | 战役专用 | 已落库 | 闸④头注五字段机检守卫 v2.1：词面族谱五族＋三域覆盖＋判定原则；零编译零网络零树写 |
| `verify/` | `retrofit_gate7_irr.py` | 战役专用 | 已落库 | gate7 英化 retrofit：只动注释不动物义 token；md5 冻结断言＋token 流恒等断言，fail-loud 不落盘 |
| `seam/` | `seam_probe.py` | 通用逐件 | **已实现**（2026-10-31） | W13 四机制代际缝指纹探针：①==语句×rewrite/ring/reflexivity→qeq_imp_qeqT 回向 ②apply(/rewrite( 全应用形→键配实例化 ③rewrite 本文件载前件引理（类型位 depth-0 `->`）→assert-化＋双岸桥 ④Require 跨行/语句面限定名不在 Require 集（前奏豁免册除外）→拓扑补列。分段/词面承 scan 冻结正典本地重实现；E364 盲区律（候选非定谳·0 命中非无缝判词）；`--selftest` 四正例＋掩蔽负例 |
| `certify/` | `freeze_manifest.py` | 通用逐件 | **已实现**（2026-10-31） | 两层冻结清单：tier1 逐文件 md5（确定性遍历·`relpath  md5` 行账）＋tier2＝tier1 账文 md5（动清单即现形）；freeze 幂等（无时间戳·同盘面重产逐字节恒同）＋check 三分对账（changed/added/removed·零漂移 exit 0）；`.git/` 与清单自身不入账 |
| `certify/` | `push_gate.py` | 通用逐件 | **已实现**（2026-10-31·席 rqwash2） | certify 深件（与冻结 v1 并存·只读 import 其 tier1_lines/tier2_of 承冻结口径）：`window` 推送窗四判据机检——c1 CI 在飞=0（`--runs-json` 预取证据 / `--ci-capped-min` reflog 推送时间线证据·本器零网络·无证据=NOT-RUN=关窗 fail-closed）＋c2 本地≥云端（fetch 后 behind=0）＋c3 fetch 干净（ls-remote 双读同 sha＋远端为 HEAD 祖先）＋c4 认证绿（套件 rc=0 必检＋`--freeze-manifest` 零漂移可选）；只判窗不开推，OPEN exit 0／CLOSED（含 NOT-RUN）exit 1。`union-freeze`/`union-check` UNION v2 多世界清单（schema rocqwash-union-manifest/2）：逐世界 tier1/tier2 承 v1＋第三层 union_tier2（逐世界 tier2 行账文 md5）＋`--tier2` 侧册；freeze 幂等逐字节恒同＋check 逐世界三分对账＋三层咬合；`--selftest` UNION 六判＋window 四判冻结向量（本地 path 远端·零网络） |
| `watch/` | `watch.py` | 通用逐件 | **已实现**（2026-10-31·席 rqwash2） | watch 首件：`ci` CI 在飞监控（`--runs-json` 离线证据 / `--repo owner/name --online` urllib 只读查询·`--interval/--timeout` 轮询；status≠completed 一律计在飞 fail-closed；NETWORK-UNREACHABLE 如实出账）＋`push` 钉 IP 推送包装器（默认 DRY-RUN 只出账零网络·`--yes` 才真推；远端 URL 主机→`--pin-ip` 改写保留 userinfo/port＋`http.<改写URL>.extraheader=Host:` 承战役口径；输出遮蔽＝`--mask` 串∪URL userinfo 密码部∪env ROCQWASH_MASK→`***MASKED***`·`--ssl-verify-off` 须显式且账面警告）＋`confirm` ls-remote N 读确证（N≥2 双读纪律下限·全等才 PUSH-CONFIRMED）。**结构性零 dispatch**：无 rerun/cancel/workflow_dispatch 任何代码路径——停手律由结构保证；本器零编译，一切编译仍必经冻结件 cpu_guard 包裹。`--selftest` 零网络向量组（ci 四判＋rewrite/mask 单元＋push 干跑＋env 遮蔽＋confirm 三判·本地 path 远端） |
| `tools/` | `cpu_guard.sh` | 通用 | **已实现** | cpu_guard v3 温控包裹（见 §6） |
| `tools/` | `_gen_fin_mac.py` / `_abl1_4b_compile.py` | 战役专用 | 已落库 | censusFIN 探针模板生成器（参数化模块/世界/依赖链）；R4 4b ocamlc 编译驱动（硬编码 opam 路径） |
| `cli/` | `rocqwash` | 统一入口 | **已实现** | 七子命令路由（契约见 §5；2026-10-31 修 run_module 分支缺 `shift`——子命令名漏传被路由件的病灶，与 §5「1:1 透传」契约对齐） |
| `examples/` | `demo_prop_leak.v` 等 | 演示 | **已实现** | 单文件全链演示（见 `examples/README.md`·实跑数据在案）。2026-10-31 起 wash 段真跑：`washed/demo_ledger.json`（16 patch exact-string 台账）驱动 `wash_engine.py`，引擎输出与参照件 `washed/demo_prop_leak_washed.v` **逐字节恒同**（cmp 断言·幂等重放 applied=0 skipped=16） |
| `docs/` | 本目录 | 文档 | **已实现** | zh/en 双语架构文档 |
| `tests/` | `run_tests.sh` ＋ 5 测试件 ＋ `fixtures/` | 通用 | **已实现** | 自测套件总入口：`bash tests/run_tests.sh`（16 例正/负两判·全绿 exit 0／任一红 exit 1·幂等零仓库写入·`ROCQWASH_TESTS_FAIL_PROBE=1` 注入恒红例自检）；覆盖 scan selftest／names `--expect` 正·含-Let·负判／gate4 净·脏两判／retrofit 干跑／wash 战役件三判／wash_engine 六判／verify_vo 九判／seam_probe 四机制／freeze_manifest 四判／push_gate UNION 六判＋window 四判／watch 零网络向量组／cpu_guard `-Direct` 冒烟＋退出码传播（见 [`tests/README.md`](../../tests/README.md)） |
| `workflows/` | —（空） | — | pending | CI 工作流占位（`.github/workflows/ci.yml` 在库：macOS 套件闸） |

> 注①：`verify/` 现有三件未带 `_` 前缀件——历史战役工装 `gate4_comment_guard.py`、
> `retrofit_gate7_irr.py`＋通用件 `verify_vo.py`。按 §5 路由契约「通用入口不唯一」
> → `cli/rocqwash verify` exit 4 列清单人工指认（2026-10-31 实测）。**统一收口的
> 前提是把两件历史工装改名为 `_` 前缀——本轮该两件为在役/冻结件禁改，故收口入
> 待办**；在收口前请直接 `python3 verify/verify_vo.py --v ... --vo ...` 调用。
>
> 注②：R4 全三源（bare 全提取 magic=0＋probe 双面 magic=0＋五式 grep=0）中的提取
> 侧依赖 `_abl1_4b_compile.py` 的 ocamlc 链接器重活（硬编码 opam 路径），其通用化
> 为超标项，**如实转待办**——`verify_vo.py` 现承接四件套机检段（编译产物侧），
> 提取侧三源合取待后续席位。
>
> 注③：`certify/` 现有两通用件——`freeze_manifest.py`（冻结中）＋`push_gate.py`
> （2026-10-31 席 rqwash2 落）。按 §5 路由契约「通用入口不唯一」→
> `cli/rocqwash certify` exit 4 列清单人工指认（2026-10-31 实测，与 verify/ 同款
> 契约形）。深件请直接 `python3 certify/push_gate.py window ...` 等方式调用；
> 收口（其一改名 `_` 前缀或 CLI 显式分派）待冻结解禁后一并入。
>
> 注④：`watch/watch.py` 的 `push` 子命令默认 DRY-RUN（零网络零执行只出账），
> `--yes` 才真推；本席自身 push 纪律＝先 `push_gate.py window` 判窗（CLOSED 不推）
> →`watch.py push` 真推取真 rc→`watch.py confirm` ls-remote 双读确证。

## 5. `cli/rocqwash` 统一入口路由契约

```
rocqwash <subcommand> [args...]
  scan     → scan/mac_stmt_scan.py（参数/退出码 1:1 透传）
  names    → names/mac_stmt_names.py（同上）
  wash|verify|seam|certify|watch → 按模块目录动态路由：
      · 目录下唯一「非 _ 前缀」.py＝通用逐件入口 → 自动路由
      · 「_ 前缀」.py＝战役专用工装 → 统一入口不代跑（防误触外部沙箱写）
      · 无通用入口 → exit 3；多通用入口 → exit 4（列清单人工指认）
```

退出码表：

| 工具 | 0 | 2 | 3 | 4 | 9 |
|---|---|---|---|---|---|
| `scan --file` | 输出清单（有命中也是 0——命中是发现不是失败） | `--selftest` 向量失败 | — | — | 文件缺失 |
| `names` | 清单/断言通过 | `--expect`/`--compare` 断言失败 | — | — | 文件缺失 |
| `wash/wash_engine.py` | 全账 APPLY/SKIP（fail=NO） | 任一 FAIL＝1；台账畸形/用法错＝2 | 无台账（不猜·SKIP 语义） | — | `--file`/`--patch` 缺失 |
| `verify/verify_vo.py` | 四件套 PASS | 用法错（--rc/--exit-file 互斥等） | — | — | 路径缺失（任一红 FAIL＝1） |
| `seam/seam_probe.py` | 出账（候选是发现不是失败） | `--selftest` 向量失败 | — | — | `--file` 缺失 |
| `certify/freeze_manifest.py` | freeze 成功／check 零漂移 | 用法错／清单畸形 | — | — | 目录/清单缺失（check 有漂移＝1） |
| `certify/push_gate.py` | window=OPEN／union-check 零漂移／union-freeze 成 | 用法错／清单畸形（union-check 漂移＝1·window CLOSED 含 NOT-RUN＝1） | — | — | 仓库/清单/世界根缺失 |
| `watch/watch.py` | ci=CI-IDLE／push DRY-RUN／confirm PUSH-CONFIRMED（真推＝git rc 透传） | 用法错（ci 在飞>0/证据不可用＝1·confirm 不一致＝1） | — | — | 仓库/远端/文件缺失 |
| `cli/rocqwash` | — | 未知子命令 | 无通用逐件入口 | 通用入口不唯一 | 入口脚本缺失 |
| `tools/cpu_guard.sh` | — | — | — | — | —（退出码＝被包裹命令退出码） |

## 6. `tools/cpu_guard.sh` v3（动态梯队列温控协议）

一切编译必经 cpu_guard 包裹（防热过载宕机·判据优先）：

```
bash tools/cpu_guard.sh [-Front 2] [-Mid 2] [-MaxWaitSec 900] [-Direct]
                        [-ThrottleFloor 90] [-ThermalMaxWait 3600] [-Reg <dir>] -- <命令...>
```

- **梯队列**：进场 FIFO 登记；位次 <Front(默认 2)＝FRONT 档 nice 0 全速；
  <Front+Mid(默认 +2)＝MID 档 nice 10；更靠后＝队列轮询，`MaxWaitSec`(900s) 到点降级
  BACK（`taskpolicy -b nice -n 19`）放行不饿死。
- **温控门**（全档适用·硬件现实永不 ABORT）：`pmset -g therm` 的 `CPU_Speed_Limit`
  < `ThrottleFloor`(90%) → 冷却轮询；`ThermalMaxWait`(3600s) 到点警告放行（降级）。
- **`-Direct`**：探针直通——不排队不注册，nice 19＋后台立即执行（小探针防饿死）。
- **双车道 `-Reg <dir>`**：分道登记表，两线队列独立互不排队；缺省行为与单道一致。
- **陈旧槽清理**：注册槽 PID `kill -0` 存活校验自动清陈旧；退出码＝被包裹命令退出码。

## 7. 规划组件设计目标（正本：README「Seven Canonical Steps」与「W13 四机制」）

- **wash 七步规范（不可跳）**：①cp 源入沙箱（写隔离）→ ②三态分诊（true-wash／
  bridge-retain=例外登记／UNCERTAIN=probe-first）→ ③规范面映射洗（Qlt→QltT／
  Qle→QleT'／`==`→QeqT／裸`=`→Id+id_cong／nat≤→NatLe）→ ④编译验证（RC=0／魔数
  `436f712100015ff4`／vo 新于 v／PA Closed／coqchk Axioms:none）→ ⑤R4 三源合取
  （bare 全提取 magic=0＋probe 双面 magic=0＋五式 grep=0）→ ⑥gate7 英化 retrofit
  （CJK→0＋五字段头注 30 行帽）→ ⑦N=N 名表断言（`mac_stmt_names.py` 有序全等）＋freeze md5。任何失败＝诚实 WIP，
  禁假绿。
- **W13 四机制**：①`==`语句 rewrite/ring/reflexivity 结构性不可用于 QeqT(Id) 目标
  →先 `qeq_imp_qeqT` 回向；②键配实例化（供给侧参数须取目标实形）；③载前件引理
  消费（assert-化＋双岸桥）；④跨行 Require 拓扑漏（语句级多行感知＋驱动幂等续跑）。

## 8. 相关文档

- 英文镜像：[`docs/en/architecture.md`](../en/architecture.md)
- 贡献流程／代码规范／测试要求／cpu_guard 使用说明：[`../CONTRIBUTING.md`](../../CONTRIBUTING.md)
- 全链演示：[`../../examples/README.md`](../../examples/README.md)
- 自测套件：[`../../tests/README.md`](../../tests/README.md)（`bash tests/run_tests.sh`）
- 项目总览：[`../../README.md`](../../README.md)
