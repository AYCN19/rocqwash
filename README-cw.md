# cw.sh — v29-v32 工具波统一入口速查 / Unified entry quick reference

`cw.sh` 是 rocqwash v29-v32 七工具＋20261111 五工具＋v37 三器＋v38 一器＋v39 三器（doc-lint/netname-normalize/select-audit）＋v40 一器＋v45 一器＋v46 两器（dispatch/audit·共二十三个）的**一键调用入口**（repo 根）：

```
bash cw.sh <tool> [args...]
```

- **零配置**：路径全部相对仓根（ROOT 取自脚本所在目录），仓随迁随用；
- **透传**：参数与退出码 1:1 直转（`exec`），不改写、不模拟；
- **bash 3.2 兼容**：macOS 自带 `/bin/bash` 可直接跑；只读路由层，自身零写盘；
- **与 `cli/rocqwash` 互补**：后者路由 v29 前七模块（scan/names/wash/verify/
  seam/certify/watch）；v29-v32 工具所在目录已含多个通用入口，模块级自动路由
  的歧义保护（exit 4）不覆盖它们——本入口按工具名显式补位。20261111 五工具
  （doctor/net-probe/triage/union/pushci）同落 `tools/` 多入口目录，同此显式名
  补位路由。

## 中文速查表

| 工具 | 目标脚本 | 用途 | 一行示例 |
|------|----------|------|----------|
| `scan4` | `scan/scan_v4_token.py` | token 级限定名普查（限定名/遮蔽源/追踪 id） | `bash cw.sh scan4 --file demo.v --json report.json --text` |
| `cure` | `wash/cure_applier.py` | 消费位治愈正典包（**缺省干跑**，`--apply` 才写盘） | `bash cw.sh cure --file demo.v --apply` |
| `probe` | `wash/probe_engine.py` | 批量闭包相容探针（候选清单×世界目录→rc 分流台账） | `bash cw.sh probe --candidates list.tsv --src src/ --world world/ --out ledger.json` |
| `chain` | `tools/chain_graph.py` | 多份 probe 台账合并→链根图＋TOP 榜 | `bash cw.sh chain l1.json l2.json --md top.md --top 25` |
| `sync-ledger` | `tools/ledger_sync.py` | probe 台账×状态台账 TSV 合并同步 | `bash cw.sh sync-ledger --probe ledger.json --ledger status.tsv --out new.tsv --report sync.json` |
| `erasure` | `verify/erasure_classifier.py` | 提取擦除位分类顾问（.mli 逐位归类） | `bash cw.sh erasure --mli out.mli --md-out ledger.md` |
| `dual-scan` | `scan/dual_scan.py` | 双器对拍（scan_v4_token×mac_stmt_scan 逐件差异） | `bash cw.sh dual-scan --dir src/ --out report.json` |
| `doctor` | `tools/toolchain_dyld_doctor.py` | dyld 工具链断链诊断（批量 EXIT=134 面·只诊断＋restore 建议·**禁代执行**） | `bash cw.sh doctor --worker PATH --donor DIR --json dyld.json` |
| `net-probe` | `tools/net_probe.py` | 网络窗探针（双探稳窗·单探禁发射·HTTPError 即可达） | `bash cw.sh net-probe --rounds 2 --interval 60 --stable-window` |
| `triage` | `tools/ci_triage.py` | CI 红炉分诊（五族+绿炉判类谱·红是数据非器红） | `bash cw.sh triage --repo ORG/REPO --run ID --logs` |
| `union` | `tools/registry_union.py` | 注册册 union 手术（main 为底＋对 merge-base 真独有尾插·**缺省干跑**） | `bash cw.sh union --base b --main m --branch x --kind order --json r.json` |
| `pushci` | `tools/pushci.py` | 修复后推送 CI 一键流水线（五段管线 preflight 发射闸→push→watch→heal→verdict±merge·v35 四器 subprocess 编排零新引擎·verdict 七态 `success\|fix-content\|toolchain\|unstable\|heal-exhausted\|gate4-block\|dry-run` 对应退出码 0/1/2/9） | `bash cw.sh pushci --repo-path . --branch feature/x --json report.json` |
| `sentinel` | `tools/cw_sentinel.py` | 实时动态哨（三路信号源 CI runs/台账链根/buildlog 词面→JSONL 事件流·once/loop 双模·判类全权在 ci_triage·**零动作是缺省**·`--on-red-preset` 五预设可重复链式按序一败续行——unclog/pushci/wash-shape/triage/cw-doctor·各承缺省干跑铁律·与 `--on-red` 互斥·旁路动作必伴 `--emit` 双路同守卫 rc=2） | `bash cw.sh sentinel --once --watch-ledgers ledgers/ --on-red-preset unclog --on-red-arg src=src/ --emit events.jsonl --json r.json` |
| `wash-shape` | `tools/wash_shape.py` | 洗形器·正典形五洗流水（词面/token/头注/行尾/锚·plan 缺省零写盘·`--apply` 落刀后复跑五洗复核·③头注模板源三路探测：`--header-map` 逐件数据 > `--header-map-preset` 钦名模板库 `tests/fixtures/header_map_v1.json`（战役正典蒸馏·金标引据在册·schema `rocqwash-header-map/1`）> env·同槽显传互斥 rc=2） | `bash cw.sh wash-shape --file demo.v --header-map-preset campaign_set_diamond --json plan.json` |
| `unclog` | `tools/unclog.py` | 疏通堵塞闭环引擎（probe 归集→chain_graph 挑根→cure_applier 落刀→复核→verdict `unclogged\|wall\|rounds-exhausted\|audit`·缺省干跑·frozen 在册红拒·`--audit` 只读堵账基线零写盘自证·与 `--apply`/`--loop` 互斥·`--probe-parallel K` 探针并行度透传 probe_engine `--jobs`·timing 段 jobs 维度入账同候选面异 K 前后跑可比） | `bash cw.sh unclog --src src/ --world world/ --audit --probe-parallel 2 --json r.json` |
| `cw-doctor` | `tools/cw_doctor.py` | 综合体检器·四域聚合（环境 dyld／网络 net_probe／注册册锚正典形审计／堵账 probe_engine＋chain_graph 逐域 subprocess 编排既有一器→综合健康分 0-100＋verdict `healthy\|degraded`＋advice 处置清单·**只诊断禁代执行**·红是数据非器红·schema `rocqwash-cwdoctor/1`·`--injector` 离线可测） | `bash cw.sh cw-doctor --json r.json --registry order.txt` |
| `doc-lint` | `tools/doc_lint.py` | 文档←→实现一致性三查器（①cw.sh 头注/usage/hint/case 四处工具表互检＋tools/ 通用入口对账 ②CASES vs tests/README.md vs README.md 计数三处对账 ③doc 引用旗标 vs 各器 `--help` 实出逐枚对照·verdict `consistent\|drift`·红是数据非器红·schema `rocqwash-doclint/1`·`--repo` 被审仓根缺省本仓） | `bash cw.sh doc-lint --repo . --json doclint.json` |
| `baseline-diff` | `tools/baseline_diff.py` | 堵账基线对比器（两份 unclog `--audit` 基线 argv 序=旧→新→`new_blocks`/`resolved_blocks`/`persistent` 三清单＋`score_delta`·verdict 四态 `improved\|degraded\|stable\|incomparable`·账面自洽预检拒手编·timing 不入对比·红是数据非器红·schema `rocqwash-baseline-diff/1`·入仓规程见 [examples/baselines/README.md](examples/baselines/README.md)） | `bash cw.sh baseline-diff audit-wash-20261101.json audit-wash-20261111.json --md diff.md` |
| `dispatch` | `tools/red_dispatch.py` | 红事件路由器（哨红事件→动作预设·三档 preset `report-only\|suggest\|auto`·**缺省 report-only 零执行**·suggest 出可复制命令块·auto 显式才代跑 60s 帽 rc≠0 入账不改退出码·防重 state＋cooldown·路由全挂既有 cw.sh 路由零新引擎·A 族内容红禁代修出 fix 清单·schema `rocqwash-red-dispatch/1`） | `bash cw.sh dispatch --event-file events.jsonl --preset suggest --json route.json` |
| `audit` | `tools/registry_audit.py` | 注册册卫生审计器（order.txt/_CoqProject 双册**只读**四账出账：重复行/锚撞文本/顺序号形/形怪/缺锚/孤儿/live 拓扑引用＋`--fix-plan` 确定性处方零写盘·**`--apply` 不存在**·键式/锚正典直用 registry_union 零重造·病灶是数据恒 exit 0·schema `rocqwash-registry-audit/1`·真仓活跑前置注记（v40 基线规程同律 [examples/baselines/README.md](examples/baselines/README.md)：真树活跑归主会话·席面只证器 selftest/夹具级）） | `bash cw.sh audit --order order.txt --project _CoqProject --live-src src/ --fix-plan --json audit.json` |
| `help` | — | 总帮助；`help <tool>` 看该工具一行提示 | `bash cw.sh help probe` |

典型流水线（发现→治愈→复核）：

```
bash cw.sh scan4 --file demo.v --json census.json      # 1 普查
bash cw.sh cure   --file demo.v                        # 2 干跑看方案
bash cw.sh cure   --file demo.v --apply               # 3 落刀（写盘）
bash cw.sh scan4  --file demo.v --json after.json      # 4 复扫应为零
```

CI 红炉修复链（doctor→net-probe→pushci(含 watch+heal)→triage）：

```
bash cw.sh doctor --json dyld.json                              # 1 dyld 断链诊断（批量 EXIT=134 面·restore 建议只打印禁代执行）
bash cw.sh net-probe --rounds 2 --interval 60 --stable-window   # 2 双探稳窗（连续两轮全端点可达才准发射·单探禁发射）
bash cw.sh pushci --repo-path . --branch feature/x --json report.json   # 3 一键流水线（preflight 内复跑 doctor＋net-probe 双闸→push→watch CI→heal 自愈 rerun→verdict±--merge·verdict 七态见上表）
bash cw.sh triage --repo ORG/REPO --run ID --logs               # 4 verdict≠success 时红炉分诊（红是数据非器红·按族给 action）
```

> 手动老链仍在册可单独用：`python3 certify/push_gate.py window ...` 推窗四判据
> ＋裸 `git push`。pushci 的 preflight 发射闸只复跑 doctor＋net-probe 两闸（可选
> `--pre-scan-gate4` 头注预扫）——套件绿/behind=0 等推窗四判据不在此册，过闸
> 纪律仍归 `certify/push_gate.py`。

### 退出码

| 码 | 含义 |
|----|------|
| 0 | 通过 |
| 2 | 未知工具（`cw.sh bogus`）；或工具自身 argparse 用法错/断言失败（透传） |
| 9 | 目标脚本缺失（`cw.sh xxx: missing <path>`）；或工具自身目标文件缺失（透传） |
| 其余 | 各工具自身口径 1:1 透传（如 sync-ledger `1`=同步完成带发现·net-probe `1`=不稳窗·doctor `1`=missing-libs·pushci verdict 封册 success/dry-run=0·heal-exhausted/unstable/toolchain=1·fix-content/gate4-block=2·9=目标缺失·cw-doctor `1`=degraded 综合健康分<90 红是数据非器红·doc-lint `1`=drift 文档漂移红是数据非器红） |

## 工作流配合接口（v37 三器共同·配合工作流实时动态提供清洗、洗形、排障、疏通堵塞）

v37 三器（`sentinel`/`wash-shape`/`unclog`）共同接口纪律五条——工作流（dynamic
workflow 子代理/后台 bash 任务）按此嵌入，不必懂各器内部：

**① --once/--loop 双模**：`--once` 单轮巡检/闭环出账即退（工作流步骤内联用）；
`--loop --interval S` 长驻哨态（后台 bash 任务用·`--max-rounds N` 轮帽 0=无限；
unclog 用 `--loop-max` 命周数·rounds-exhausted 非终局歇 `--interval` 再下一周）。
wash-shape 缺省即 once（plan 段零写盘），`--loop` 显式开哨态且可与 `--apply`
并用逐轮落刀。`--sleep-scale F` 全睡乘 F（selftest 用 0=零真睡）。

**② JSON-in/JSON-out＋JSONL 事件流**：`--json OUT` 出确定性报告（sort_keys·
schema 钦名 `rocqwash-sentinel/1`·`rocqwash-shape/1`·`rocqwash-unclog/1`·同输入
重跑字节恒同）；loop 态事件逐行 append `--events FILE`（JSONL·逐行 flush·行
schema `rocqwash-sentinel-event/1`，sentinel 事件键含 `seq` 事件流内单调——消费
方按 seq 排序即恢复全局序）。

**③ --injector 离线可测**：子进程调用层罐装（sentinel= canned GitHub API 表
`rocqwash-sentinel-injector/1`·未命中 fail-loud 9 **绝不静默走真网络**；
wash-shape= 引擎 `{rc,stdout,report}` 罐装；unclog= probe/resprobe canned 台账
scenario.json）＋`--sleep-scale 0`——零真网络零真编译于 selftest，工作流演练/CI
全离线。

**④ 退出码 0/1/2/9 口径（红是数据非器红·响亮 stdout）**：

| 码 | sentinel | wash-shape | unclog |
|----|----------|------------|--------|
| 0 | 巡检完成（CI 红/堵塞是事件数据） | clean/shaped | unclogged |
| 1 | —（红走事件流） | partial/plan-miss（洗未尽·响亮出账） | wall/rounds-exhausted（诚实墙·禁硬凑） |
| 2 | 用法错（缺模式/三源全缺/repo 形坏） | 用法错/冻结件红拒/引擎形外退出 | 用法错/注入场景形错 |
| 9 | 信号源不可达（HTTP 4xx·injector 未覆盖·子进程 rc≠0） | 路径缺失 | fail-loud（路径缺失/器红/frozen 不可得） |

**⑤ 典型后台哨命令行**（工作流后台任务逐条照抄·事件流供主流程 tail 消费）：

```
# 哨态：台账链根＋buildlog 双源巡检·JSONL 事件流·seen 幂等（loop 须给 --state-file）
nohup bash cw.sh sentinel --loop --interval 60 \
  --watch-ledgers ledgers/ --watch-buildlog build.log \
  --state-file .sentinel-state.json --emit events.jsonl \
  --json sentinel-report.json >/dev/null 2>&1 &

# 洗形哨态：逐轮 plan→apply 落刀→复跑五洗复核（--max-rounds 界定）
nohup bash cw.sh wash-shape --dir src/ --loop --interval 300 --max-rounds 8 \
  --apply --events shape-events.jsonl --json shape-report.json >/dev/null 2>&1 &

# 疏通哨态：五步闭环周而复始·wall/unclogged 终局即停即退
nohup bash cw.sh unclog --src src/ --world world/ --loop --interval 600 --loop-max 8 \
  --events unclog-events.jsonl --json unclog-report.json >/dev/null 2>&1 &
```

**⑥ 三典型工作流嵌段**（工作流脚本内联步·全部离线可注入形）：

```
# pushci 嵌段（发射闸→push→watch→heal→verdict·七态封册按退出码分流）
bash cw.sh pushci --repo-path . --branch feature/x --json pushci.json
case $? in 0) : ;; 1|2) bash cw.sh triage --repo ORG/REPO --run ID --logs ;; esac

# unclog 嵌段（堵塞疏通闭环·verdict 三态按退出码分流·缺省干跑看墙账）
bash cw.sh unclog --src src/ --world world/ --json unclog.json
case $? in 0) echo unclogged ;; 1) echo "wall/rounds-exhausted：读 unclog.json wall 账人工判定" ;; esac

# wash-shape 嵌段（正典形五洗·plan 零写盘先行·人审后再 --apply 两段全施）
bash cw.sh wash-shape --file demo.v --json plan.json      # plan 段（rc 0/1 均有账）
bash cw.sh wash-shape --file demo.v --apply --json shaped.json   # 落刀＋复跑复核
```

> 三器编排而非重造：sentinel 判类全权在 `ci_triage`（subprocess 直调）、链根全权
> 在 `chain_graph`；wash-shape 五洗引擎全 subprocess（gate4/scan_v4/cure_applier/
> comment_sweep/registry_union）；unclog 五步全 subprocess（probe_engine/chain_graph/
> cure_applier/scan_v4_token/frozen8）。工作流调它们即调全部既有引擎。

**⑦ v38 注记（preset／audit／韧性层·20261111）**——三器接口在上述五条纪律上扩面：

- **preset**：sentinel 增 `--on-red-preset NAME`（红事件预设动作·预设即模板
  sugar·v41 预设表数据化扩至五预设：`unclog`＝干跑疏通（**不带 --apply**·
  人审后再落刀）、`pushci`＝`--dry-run` 只打计划、`wash-shape`＝只出 plan
  （**不带 --apply**·plan 零写盘）、`triage`＝对红 run 复诊重判类（repo/run
  事件直替族）、`cw-doctor`＝全缺省体检——各预设自动接驳各器缺省干跑铁律；
  **可重复＝链式**按给定序逐件执行·一败续行不改哨退出码·actions 账每条
  一笔）；展开走与 `--on-red` **同一执行器**（60s 帽·rc≠0 不改哨退出码·
  零新执行路径）；必传参数经 `--on-red-arg K=V` 透传（链式参数面＝全链
  并集）·`{emit_dir}` 取 `--emit` 所在目录；与 `--on-red` **互斥**（同给
  rc=2 fail-loud 禁静默择一）；**旁路动作必伴事件流**——plain `--on-red`
  与 preset 缺 `--emit` 双路同守卫 rc=2（v41 破坏面矩阵 S2 判据转正）。
  wash-shape 同形扩面（v39 轮）：
  ③头注形洗模板源增 `--header-map-preset NAME` 钦名模板（`tests/fixtures/
  header_map_v1.json` 战役正典蒸馏库·schema `rocqwash-header-map/1`·占位全承
  目标件自身 Require 面与既有头注逐字·任一绑不上 plan-miss 不硬造；与
  `--header-map` 同槽互斥 rc=2·模板源探测次序 `--header-map` > preset > env）。
- **audit**：unclog 增 `--audit` 只读堵账基线（单遍 probe 干跑归集→chain_graph
  →出基线报告·`final.verdict=audit` exit 0 红是基线数据非器红·cures 恒 0＝
  零落刀零复核）；**零写盘硬保证**＝`--src` 全文件 md5 清单跑前跑后自证恒同
  （违同 fail-loud 9·染污基线不出账）；与 `--apply`/`--loop` 互斥 rc=2；
  timing 段实测墙钟为报告唯一非确定段——v41 增 `--probe-parallel K` 探针
  并行度透传 probe_engine `--jobs`（timing 段 jobs 维度入账·同候选面异 K
  前后跑可比·--guard 同给建议 K≤2 温控自裁）。
- **韧性层**：CI GET 403/429/5xx 指数退避重试抽公共件 `tools/_http_backoff.py`
  纯函数（`ci_triage`/`cw_sentinel`/`pushci` 三器共享·`--retry-max` 缺省 3·
  Retry-After 秒数头尊重·4xx 语义面不重试）；net-probe 增 `--jitter/--seed`
  （每端点探测前随机微抖·抖散对齐性重试风暴·加法式键缺省零行为变化）；
  pushci 增 `--timeout`（真子进程防挂帽）·sentinel 增 `--subproc-timeout`
  （编排子进程防挂）——**injector canned 路径一律零重试零真网络**（离线可测
  铁律）。各器形详锚其 docstring 与 `--help`。

**⑧ 三嵌段正典样例（examples/workflows/·可整段复制）＋集成白皮书**：

- 嵌段①后台哨：[examples/workflows/backend-sentinel.md](examples/workflows/backend-sentinel.md)
  （⑤ 后台哨命令块整段复制版＋JSONL 消费端 grep/python3 双形＋退出码分支表＋
  dynamic-workflow 嵌段伪码）
- 嵌段②单步推 CI：[examples/workflows/step-pushci.md](examples/workflows/step-pushci.md)
  （⑥ pushci 嵌段展开·`--dry-run` 先行→真发→verdict 七态分流表＋离线演练形）
- 嵌段③堵账疏通：[examples/workflows/loop-unclog.md](examples/workflows/loop-unclog.md)
  （⑥ unclog 嵌段展开·干跑→人审→`--apply`→复核四判＋诚实墙因分派表）
- 集成白皮书：[docs/workflow-integration-whitepaper-v1.0-20261111.md](docs/workflow-integration-whitepaper-v1.0-20261111.md)
  （主会话让路模式／后台任务拓扑／双门并立——推窗四判据×发射闸）
- 实时动态服务运行手册：[docs/ops-realtime-service-v1.0-20261111.md](docs/ops-realtime-service-v1.0-20261111.md)
  （后台哨标准命令与 JSONL 消费／preset 接驳 unclog 全链三判 e2e＝
  `tests/test_relay_e2e.py`·tmp 注入演练实跑原文在册·与器 `--help` 冲突时以器为准）
- 服务层总览（v40）：[docs/service-layer-overview-v1.0-20261111.md](docs/service-layer-overview-v1.0-20261111.md)
  （三链一图全景＋器面索引·docs 席铸）
- 堵账基线入仓规程（v40）：[examples/baselines/README.md](examples/baselines/README.md)
  （`unclog --audit` 基线命名律 `audit-<域>-<yyyymmdd>.json`／timing 非确定段
  注记／baseline-diff 对比判读与红线纪律·工装席铸）

**⑨ 红事件路由嵌段（v46·red_dispatch 配对例·哨红事件→动作预设路由）**：

```
# 哨态红事件→路由器接驳（--on-red 模板配对例·<json> 取 --emit 事件流同盘
# 路径——哨每遇红事件即以事件流整盘喂路由器·suggest 档零执行出复制块）
bash cw.sh sentinel --once --watch-ledgers ledgers/ --emit events.jsonl \
  --on-red 'python3 tools/red_dispatch.py --event-file <json> --preset suggest'

# 单步直调（不经哨·对既有事件流补一轮路由账·report-only 缺省零执行）
bash cw.sh dispatch --event-file events.jsonl --preset suggest --json route.json
```

> dispatch 是路由而非引擎：五路由（B/E 族→pushci 重派·A 族→manual-fix-note
> 禁代修出 fix 清单·C 族→doctor·blocking→unclog·build-signal→wash-shape）
> 全挂既有 cw.sh 路由零新引擎；三档 preset 缺省 report-only 零执行（红是
> 数据），auto 显式才代跑（60s 帽·rc≠0 响亮入账不改退出码·防重 state＋
> cooldown）；与哨 `--on-red` 配对时占位替换 `{family}/{run}/{repo}` 既有
> 语义不动——路由器自行从事件流读全事件。

## English brief

`cw.sh` is the one-command entry for the seven tools introduced in the
rocqwash v29-v32 waves plus the five tools added on 20261111 plus the three
v37 tools plus the v38 aggregate doctor plus the v39 trio (doc-lint plus
netname-normalize/select-audit) plus the v40 baseline-diff plus the v45
render-events plus the v46 dispatch/audit pair (twenty-three in total). It
lives at the repository root:

```
bash cw.sh <tool> [args...]
```

Tool names map 1:1 to the underlying scripts: `scan4`→`scan/scan_v4_token.py`
(token-level qualified-identifier census), `cure`→`wash/cure_applier.py`
(consumer-cure pack, dry-run by default), `probe`→`wash/probe_engine.py`
(batch closure-compatibility probing), `chain`→`tools/chain_graph.py`
(multi-ledger chain-root graph), `sync-ledger`→`tools/ledger_sync.py`
(probe×status-ledger merge), `erasure`→`verify/erasure_classifier.py`
(extraction erasure advisor), `dual-scan`→`scan/dual_scan.py`
(dual-scanner cross-check), and the 20261111 additions `doctor`→
`tools/toolchain_dyld_doctor.py` (dyld toolchain-breakage diagnostics; prints
restore advice, never executes it), `net-probe`→`tools/net_probe.py`
(network-window probe, double-probe stable window), `triage`→`tools/ci_triage.py`
(CI red-run triage), `union`→`tools/registry_union.py` (registry union surgery,
dry-run by default), `pushci`→`tools/pushci.py` (push-CI one-shot pipeline:
preflight emission gate → push → CI watch → heal rerun → verdict ± merge;
seven-state verdict `success|fix-content|toolchain|unstable|heal-exhausted|
gate4-block|dry-run`), the v37 additions `sentinel`→`tools/cw_sentinel.py`
(real-time watch sentinel: CI runs / local ledger chain-roots / buildlog
tokens → JSONL event stream, once/loop dual mode, report-only by default),
`wash-shape`→`tools/wash_shape.py` (canonical five-pass shaping pipeline:
lexical/token/header/EOL/anchor; plan is zero-write by default, `--apply`
re-runs all five passes for verification; the ③ header-pass template source is
probed in order `--header-map` per-file data > `--header-map-preset` named
template library `tests/fixtures/header_map_v1.json` > env, with the two
explicit flags mutually exclusive rc=2), `unclog`→`tools/unclog.py`
(blockage-unclogging closed loop: probe collection → chain-root pick →
cure-applier → re-scan/re-probe → verdict `unclogged|wall|rounds-exhausted`;
dry-run by default, frozen8 red-refusal), the v38 addition `cw-doctor`→
`tools/cw_doctor.py` (aggregate health check orchestrating the existing tools
per domain — dyld environment / net_probe network / registry anchor audit /
probe_engine+chain_graph clog sampling — into a 0-100 score with verdict
`healthy|degraded` and per-domain advice; diagnosis only, never executes
fixes; `--injector`-offline-testable), plus the v39 addition
`doc-lint`→`tools/doc_lint.py` (docs↔implementation consistency linter, three
checks: cw.sh four-place tool-table cross-check + tools/ generic-entry
reconciliation, CASES count three-way check against tests/README.md and
README.md, and doc flag references verified against each tool's real `--help`
output; verdict `consistent|drift`, red is data not tool failure), plus the
v40 addition `baseline-diff`→`tools/baseline_diff.py` (clog-baseline differ:
two `unclog --audit` baselines in argv order old→new → `new_blocks` /
`resolved_blocks` / `persistent` block lists plus `score_delta`, verdict
`improved|degraded|stable|incomparable` with honest refusal on candidate-set
mismatch; red is data, not tool failure; intake protocol at
`examples/baselines/README.md`), plus the v45 addition
`render-events`→`tools/render_events.py` (sentinel-event JSONL → markdown
ledger renderer), plus the v46 additions
`dispatch`→`tools/red_dispatch.py` (red-event router: sentinel red events →
action presets in three presets `report-only|suggest|auto` — report-only
zero-execution by default, suggest prints a copy-paste command block, auto
executes only when explicit under a 60s cap with rc≠0 recorded loudly without
touching the exit code; dedup state + cooldown; all five routes wired onto
existing cw.sh routes, zero new engines; family-A content-red is never
auto-fixed — it emits a fix list), and
`audit`→`tools/registry_audit.py` (registry hygiene auditor: order.txt/
_CoqProject dual-book read-only four-account output — duplicate rows / anchor
collisions / seq-form / malformed / missing anchors / orphans / live topology —
plus a `--fix-plan` deterministic prescription with zero writes; `--apply`
does not exist; keys and the anchor canon are reused from registry_union,
zero re-invention; findings are data, always exit 0), plus
`help`. The v37 tools share a
common workflow-interface discipline (once/loop dual mode, deterministic
JSON reports + JSONL event streams, `--injector` offline canned testing,
exit codes 0/1/2/9 where red is data not tool failure) — see the Chinese
section 「工作流配合接口」 above. v38 extensions to that interface (preset
table expanded in v41): sentinel
`--on-red-preset` (five canned red-event actions — unclog dry-run / pushci
dry-run / wash-shape plan-only / triage re-triage / cw-doctor checkup —
each honoring its tool's dry-run-by-default discipline, repeatable for
chained sequential fire where one failure continues the chain without
touching the sentinel exit code; mutually exclusive with `--on-red`;
both plain and preset forms require `--emit`, rc=2 otherwise), unclog
`--audit` (read-only clog baseline with an md5 no-write proof;
`--probe-parallel K` threads the probe fan-out through probe_engine
`--jobs` with a jobs dimension recorded in the timing section for
cross-K comparisons), and a shared resilience layer
(`tools/_http_backoff.py` exponential
backoff, net-probe `--jitter/--seed`, pushci `--timeout`, sentinel
`--subproc-timeout`). Three copy-paste canonical workflow blocks live in
`examples/workflows/` (`backend-sentinel.md`, `step-pushci.md`,
`loop-unclog.md`), with the integration whitepaper at
`docs/workflow-integration-whitepaper-v1.0-20261111.md`; the ops runbook for
the realtime service (backend sentinel standard commands, JSONL consumption,
and the `--on-red-preset unclog` relay e2e in `tests/test_relay_e2e.py`) is at
`docs/ops-realtime-service-v1.0-20261111.md`.

Design contract: all paths are resolved relative to the repository root from
the script's own location (no hardcoded paths; the repo can be cloned anywhere);
arguments and exit codes pass through 1:1 via `exec` (fail-loud, never
rewritten); requires only `bash` 3.2 and `python3` ≥ 3.9, no third-party
dependencies; the entry itself is a read-only dispatcher and writes nothing.
`bash cw.sh help <tool>` prints a one-line usage hint per tool. It complements
the existing `cli/rocqwash` router, which covers the pre-v29 modules — the
v29-v32 tools live in directories with several generic entries each, where the
module auto-router's ambiguity guard declines to guess, so this entry routes
them by explicit tool name. Self-test: `bash tests/test_cw_entry.sh` (also part
of `bash tests/run_tests.sh`).
