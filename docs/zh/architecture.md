# rocqwash 架构（Architecture·中文版）

> 状态快照：2026-10-29（`tests/` 行与 §8 链接于 2026-10-30 复核更新）。本文档如实
> 反映仓库当前盘面：已实现组件以源代码逐条核对，未落地组件以空目录/占位如实标注。
> 英文镜像见 [`docs/en/architecture.md`](../en/architecture.md)。
> 快照后仓库仍在活跃开发（并发席位持续落库），以代码为准。

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
        已实现   已实现   见 §4    (guard)      见 §4        规划中    规划中     规划中

  统一入口：cli/rocqwash（scan / names / wash / verify / seam / certify / watch 七子命令）
```

| 站 | 输入 | 输出 | 状态 |
|---|---|---|---|
| scan | 单件 `.v` | 命中清单＋归类注记（stdout / `--json` / `--hits-csv`） | 已实现 |
| names | 单件或两件 `.v` | 有序语句名清单＋ N=N 有序全等断言 | 已实现 |
| wash | 单件 `.v` | 洗后 `.v`（规范面映射·幂等） | 战役批量工装已落库；通用逐件入口 pending |
| compile | `.v` | `.vo`（魔数 `436f712100015ff4` 咬合） | 经 cpu_guard |
| verify(R4) | 提取物／编译产物 | 三源合取判定 | 战役验证工装已落库；统一逐件入口 pending |
| seam | — | W13 四机制自动归类 | 目录占位，pending |
| certify | — | 两层冻结＋推窗四判据＋UNION v2 | 目录占位，pending |
| watch | — | CI 监控＋pin-IP 推送＋温控 | 目录占位，pending |

## 4. 组件表（Components·以源码核对）

形态列：**通用逐件**＝带 argparse 接口、可被 `cli/rocqwash` 自动路由；
**战役专用**＝`_` 前缀、路径硬编码、不接逐件 argv，统一入口不代跑（直接 `python3` 调用）。

| 模块 | 文件 | 形态 | 状态 | 要点 |
|---|---|---|---|---|
| `scan/` | `mac_stmt_scan.py` | 通用逐件 | **已实现** | 语句面 Prop 裸形扫描器：冻结道五族 P1–P5（13 子通道：Qlt/Qle/`==`/exists·and·or·not·false/裸`=`/`<=`·`<`·`>=`·`>`）＋负捕获道三族（P6_In/P8_True/P9_proper·结论位 CAPTURE/前提位 EXEMPT）；分类四分 RED/WHITELIST/EXEMPT/CAPTURE；白名单与 BRIDGE_FAMILY 在册；混合面（载体并现裸形）检测；`--manifest` 四账对账（swallowed/blind/kind_drift/line_drift·blind=∅ 断言）；`--selftest` E364 冻结向量组；`--baseline` S09 基准试射 |
| `names/` | `mac_stmt_names.py` | 通用逐件 | **已实现** | 顶层语句名有序清单提取器：census 口径（9 kind·不含 Let）／`--include-let` 会师口径；`--compare` 两件有序 1:1 全等断言（N=N 形·不等 exit 2）；`--expect` 计数断言；`--kinds` 过滤；ARM2 证明体独立成臂消费；Unicode 名道；fail-loud 全程 |
| `wash/` | `_abl1_wash.py` | 战役专用 | 已落库 | 席 abl1 批洗工装：exact-string ＋ count 断言 ＋ 幂等（new 已在盘=skip）；嵌套括号感知；`ROOT` 硬编码外部战役沙箱、不接 argv。**通用逐件规范洗入口（七步·规范面映射）pending** |
| `verify/` | `_parse_fin_mac.py` | 战役专用 | 已落库 | censusFIN_mac 解析道：提取擦除语义（RED iff `__` 现于 let 体/型注·含 Set-cloaked Prop）＋绿判四件套并查（exit 码/log 零 Error/`.vo` 魔数/`.vo` mtime 新鲜度）＋ann 正则双形律 |
| `verify/` | `gate4_comment_guard.py` | 战役专用 | 已落库 | 闸④头注五字段机检守卫 v2.1：词面族谱五族＋三域覆盖＋判定原则；零编译零网络零树写 |
| `verify/` | `retrofit_gate7_irr.py` | 战役专用 | 已落库 | gate7 英化 retrofit：只动注释不动物义 token；md5 冻结断言＋token 流恒等断言，fail-loud 不落盘 |
| `seam/` | —（空） | — | pending | 规划：代际缝探针（W13 四机制自动归类·机械供给签名 Check） |
| `certify/` | —（空） | — | pending | 规划：两层冻结＋推窗四判据＋UNION v2 |
| `watch/` | —（空） | — | pending | 规划：CI 监控＋pin-IP 推送＋温控 |
| `tools/` | `cpu_guard.sh` | 通用 | **已实现** | cpu_guard v3 温控包裹（见 §6） |
| `tools/` | `_gen_fin_mac.py` / `_abl1_4b_compile.py` | 战役专用 | 已落库 | censusFIN 探针模板生成器（参数化模块/世界/依赖链）；R4 4b ocamlc 编译驱动（硬编码 opam 路径） |
| `cli/` | `rocqwash` | 统一入口 | **已实现** | 七子命令路由（契约见 §5） |
| `examples/` | `demo_prop_leak.v` 等 | 演示 | **已实现** | 单文件全链演示（见 `examples/README.md`·实跑数据在案） |
| `docs/` | 本目录 | 文档 | **已实现** | zh/en 双语架构文档 |
| `tests/` | `run_tests.sh` ＋ `test_retrofit_dryrun.py` / `test_wash_fixture.py` ＋ `fixtures/` | 通用 | **已实现** | 自测套件总入口：`bash tests/run_tests.sh`（10 例正/负两判·全绿 exit 0／任一红 exit 1·幂等零仓库写入·`ROCQWASH_TESTS_FAIL_PROBE=1` 注入恒红例自检）；覆盖 scan selftest／names `--expect` 正·含-Let·负判／gate4 净·脏两判／retrofit 干跑／wash 三判／cpu_guard `-Direct` 冒烟＋退出码传播（见 [`tests/README.md`](../../tests/README.md)） |
| `workflows/` | —（空） | — | pending | CI 工作流占位 |

> 注：`verify/gate4_comment_guard.py` 与 `verify/retrofit_gate7_irr.py` 为无 CLI、
> 路径硬编码的战役工装，但**未带 `_` 前缀**（历史命名），故按 §5 路由契约为
> 「通用入口不唯一」→ `cli/rocqwash verify` exit 4（2026-10-30 实测）；请直接
> `python3` 调用。

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
