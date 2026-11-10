# 服务层总览 v1.0（service-layer overview·2026-11-11）

> 一张图讲清 rocqwash 现役能力全貌：**四职能**（清洗／洗形／排障／疏通）×
> **三层**（诊断 v35／编排 v36／服务 v37-v39）×**统一入口**（cw.sh 十九工具）×
> **工作流配合接口**（引 whitepaper）。内容全部取自器实况（各器 `--help` 与
> docstring·`cw.sh` 工具表·更新账 v35-v39 段·2026-11-11 先读后写·零凭空
> API）；文中旗标引用已经 `tools/doc_lint.py` ③旗标查逐枚对照 `--help` 实出
> 机检。分工：速查在 [`README-cw.md`](../README-cw.md)·接口正本在
> [`workflow-integration-whitepaper-v1.0-20261111.md`](workflow-integration-whitepaper-v1.0-20261111.md)
> ·运行规程在
> [`ops-realtime-service-v1.0-20261111.md`](ops-realtime-service-v1.0-20261111.md)
> ——本文是三者的合图景，不替代其一；与器不一致视为 bug（CONTRIBUTING §1.5 同律）。

## 一、一张图（现役能力全貌）

```text
┌───────────────────── 工作流配合面（外部编排引擎）─────────────────────┐
│  dynamic workflow 子代理／后台 bash 任务                              │
│  嵌段正典：examples/workflows/ 三件（后台哨·单步推CI·疏通闭环）        │
│  接口五纪律（whitepaper §1）：schema 钦名·退出码 0/1/2/9（红是数据    │
│  非器红）·once/loop 双模·injector 离线可测·编排零新引擎——调器读       │
│  JSON·不重造判据                                                     │
└──────────────────────────▲ JSONL 事件流／JSON 报告────────────────────┘
┌───────────────── 服务层 v37-v39（实时动态·四职能落点）────────────────┐
│  清洗＝wash_shape＋cure（消费位治愈正典包 v1.4·25 式）                │
│  洗形＝五洗流水（词面/token/头注/行尾/锚·plan/apply 两段）            │
│  排障＝sentinel 三路实时哨＋cw-doctor 四域体检（聚合 v35 诊断三器）    │
│  疏通＝unclog 闭环（probe 归集→chain_graph 挑根→cure 落刀→复核）      │
│  收口＝doc-lint 文档←→实现一致性三查                                  │
└──────────────────────────▲ subprocess 编排（零新引擎）────────────────┘
┌───────────────── 编排层 v36（一键流水线）─────────────────────────────┐
│  pushci 五段：发射闸（doctor＋net-probe 双闸）→push→watch→heal→       │
│  verdict±merge（七态封册对退出码 0/1/2/9）                            │
└──────────────────────────▲ 编排 v35 四器 ─────────────────────────────┘
┌───────────────── 诊断层 v35 ＋ v29-v32 底座 ──────────────────────────┐
│  排障三器：doctor（dyld 断链）·net-probe（双探稳窗）·triage（五族判类）│
│  手术器：union（注册册 union·缺省干跑）                               │
│  底座：scan4 普查·probe 探针·chain 链根·cure 治愈·sync-ledger·        │
│        erasure·dual-scan·netname-normalize·select-audit               │
└───────────────────────────────────────────────────────────────────────┘
        统一入口：bash cw.sh <tool>（十九工具＋help·1:1 透传·bash 3.2）
```

读法：外部工作流只站在图顶——调器、读 JSON、按五纪律分流；四职能全部由
既有引擎 subprocess 编排承做（零新引擎，向下复用 v35 诊断层与 v29-v32 底座）。

## 二、四职能矩阵

| 职能 | 器 | 入口（cw.sh 路由→脚本） | 一句话职责 | 缺省安全态 |
|---|---|---|---|---|
| 清洗 | `wash_shape`＋`cure_applier` | `cw.sh wash-shape`→`tools/wash_shape.py`／`cw.sh cure`→`wash/cure_applier.py` | 消费位治愈：cure 正典包（v1.4·25 式·evidence-gated）为刀，wash_shape 编排落刀面 | 两器缺省干跑·`--apply` 显式才写盘 |
| 洗形 | `wash_shape`（五洗引擎：gate4／scan_v4_token／cure_applier／comment_sweep／registry_union 全 subprocess） | `cw.sh wash-shape`→`tools/wash_shape.py` | 正典形五洗流水：词面洗／token 洗／头注形洗／行尾洗／锚形洗·plan/apply 两段 | plan 段零写盘·apply 后复跑五洗复核→shaped/partial 如实·冻结名红拒 |
| 排障 | `toolchain_dyld_doctor`＋`net_probe`＋`ci_triage`（v38 聚合：`cw_doctor`） | `cw.sh doctor`／`cw.sh net-probe`／`cw.sh triage`／`cw.sh cw-doctor` | 环境断链诊断／网络双探稳窗／CI 红炉五族判类→四域聚合健康分＋advice | 全部只诊断＋建议·禁代执行·红是数据非器红 |
| 疏通 | `unclog`＋`chain_graph` | `cw.sh unclog`→`tools/unclog.py`／`cw.sh chain`→`tools/chain_graph.py` | 堵账闭环：probe 归集→链根挑根→cure 落刀→rescan/resprobe 复核→verdict | unclog 缺省干跑（`--audit` 只读基线·frozen 在册红拒）·诚实墙逐根列因禁硬凑 |

## 三、三层演进（v35→v36→v37-v39·全部 2026-11-11）

| 层 | 波次（commit） | 器面 | 层职责 |
|---|---|---|---|
| 诊断层 | v35（acf9fe6） | doctor·net-probe·triage·union 四新器（＋v29-v32 底座 scan4/cure/probe/chain/sync-ledger/erasure/dual-scan） | 把 20261110 战役诊断手法工具化：环境／网络／判类／注册册四面各一器 |
| 编排层 | v36（4026051） | pushci（subprocess 编排 v35 四器·零新引擎） | 一键流水线：发射闸→push→watch→heal→verdict±merge·七态封册 |
| 服务层 | v37（41e74b0）／v38（c205ea0）／v39（caa3a28） | v37＝unclog·wash-shape·sentinel 三器＋接口五纪律；v38＝cw-doctor 四域体检＋`--on-red-preset` 接驳＋`--audit` 审计＋韧性层＋三嵌段＋whitepaper；v39＝doc-lint＋cure_pack v1.4＋header_map_v1 模板库＋relay e2e＋ops 手册＋入口补齐十九 | 批处理工具→实时动态服务：四职能常驻化＋体检＋文档收口 |

## 四、入口：cw.sh 十九工具全表

统一入口 `bash cw.sh <tool> [args...]`（repo 根·参数与退出码 1:1 透传·
`bash cw.sh help <tool>` 看单器一行提示）：

| 路由 | 目标脚本 | 层／职能 | 一句话 |
|---|---|---|---|
| `scan4` | `scan/scan_v4_token.py` | 底座 | token 级限定名普查 |
| `cure` | `wash/cure_applier.py` | 底座·清洗 | 消费位治愈正典包（缺省干跑） |
| `probe` | `wash/probe_engine.py` | 底座 | 批量闭包相容探针 |
| `chain` | `tools/chain_graph.py` | 底座·疏通 | 多账合并链根图 |
| `sync-ledger` | `tools/ledger_sync.py` | 底座 | probe 台账×状态台账合并同步 |
| `erasure` | `verify/erasure_classifier.py` | 底座 | 擦除位分类顾问 |
| `dual-scan` | `scan/dual_scan.py` | 底座 | 双器对拍驱动 |
| `doctor` | `tools/toolchain_dyld_doctor.py` | 诊断·排障 | dyld 工具链断链诊断（禁代执行） |
| `net-probe` | `tools/net_probe.py` | 诊断·排障 | 网络窗探针（双探稳窗） |
| `triage` | `tools/ci_triage.py` | 诊断·排障 | CI 红炉分诊（五族+绿炉） |
| `union` | `tools/registry_union.py` | 诊断 | 注册册 union 手术（缺省干跑） |
| `pushci` | `tools/pushci.py` | 编排 | 推送 CI 一键流水线（七态 verdict） |
| `sentinel` | `tools/cw_sentinel.py` | 服务·排障 | 实时动态哨（JSONL 事件流） |
| `wash-shape` | `tools/wash_shape.py` | 服务·清洗/洗形 | 洗形五洗流水 |
| `unclog` | `tools/unclog.py` | 服务·疏通 | 疏通堵塞闭环引擎 |
| `cw-doctor` | `tools/cw_doctor.py` | 服务·排障 | 综合体检四域聚合 |
| `doc-lint` | `tools/doc_lint.py` | 服务·收口 | 文档←→实现一致性三查 |
| `netname-normalize` | `tools/netname_normalize.py` | 底座（v39 入口补齐） | .v.v 双后缀净名归一 |
| `select-audit` | `tools/select_audit.py` | 底座（v39 入口补齐） | 批选审计器（grep 剔重＋Require 面审计） |
| `help` | — | 伪路由 | 总帮助／单器一行提示 |

## 五、服务面接口旗标速览（`cw.sh sentinel --help` 等六器实出·v39 现势）

| 器（入口） | 关键旗标 | 备注 |
|---|---|---|
| `cw.sh sentinel`（`tools/cw_sentinel.py`） | `--once`／`--loop --interval S --max-rounds N`／`--watch-repo ORG/REPO --branch B`／`--watch-ledgers DIR`／`--watch-buildlog FILE`／`--state-file F`／`--emit F`／`--json OUT`／`--on-red 'CMD'`／`--on-red-preset NAME --on-red-arg K=V`／`--injector F`／`--sleep-scale F` | 三路信号源可任意组合；`--on-red` 与 `--on-red-preset` 互斥 rc=2；缺省 report-only |
| `cw.sh wash-shape`（`tools/wash_shape.py`） | `--file A.v`（可多件）／`--dir TREE`／`--only KINDS`／`--header-map M`／`--header-map-preset NAME`／`--anchor-src DIR`／`--apply`／`--json OUT`／`--events F`／`--loop --interval S --max-rounds N`／`--injector SCEN.json`／`--sleep-scale F` | `--header-map` 与 `--header-map-preset` 同槽互斥 rc=2；plan 缺省零写盘 |
| `cw.sh unclog`（`tools/unclog.py`） | `--src DIR --world DIR`／`--candidates TSV`／`--chain-ledgers JSON...`／`--rounds N --top N`／`--apply`／`--audit`／`--workdir DIR`／`--guard PATH --guard-reg DIR --guard-front N --guard-mid N --guard-maxwait N`／`--events F`／`--loop --interval S --loop-max N`／`--injector DIR`／`--json OUT` | 缺省干跑；`--audit` 只读基线与 `--apply`/`--loop` 互斥 rc=2；`--guard*` 真编译 cpu_guard 透传 |
| `cw.sh pushci`（`tools/pushci.py`） | `--repo-path DIR --branch B`／`--pre-scan-gate4`／`--merge`／`--max-heal N`／`--timeout S`／`--dry-run`／`--json OUT`／`--injector DIR --git-caller FILE` | verdict 七态封册 0/1/2/9；离线演练两旗标必须成对 |
| `cw.sh cw-doctor`（`tools/cw_doctor.py`） | `--json OUT`／`--registry PATH`／`--src DIR --sample N --world DIR`／`--worker PATH --donor DIR`／`--endpoints URL,..`／`--guard PATH`／`--timeout S`／`--workdir DIR`／`--injector DIR` | 四域聚合健康分 0-100·verdict healthy/degraded；只诊断禁代执行 |
| `cw.sh doc-lint`（`tools/doc_lint.py`） | `--repo DIR`／`--json OUT`／`--help-cap N` | 三查 verdict consistent/drift（红是数据非器红） |

## 六、工作流配合接口（正本：whitepaper §1）

外部工作流（dynamic workflow 子代理／后台 bash 任务）按**接口五纪律**嵌入，
不必懂各器内部（逐器机理与命令正本见
[`workflow-integration-whitepaper-v1.0-20261111.md`](workflow-integration-whitepaper-v1.0-20261111.md) §1；
速查在 README-cw.md「工作流配合接口」节；CONTRIBUTING §7 与其同源）：

1. **JSON-in/JSON-out·schema 钦名·确定性**——出账一律 `--json`（schema
   rocqwash-sentinel/1·rocqwash-shape/1·rocqwash-unclog/1·rocqwash-pushci/1）；
   loop 态事件流 `--events` 逐行 JSONL；`--json` 落盘 sort_keys·同输入重跑
   字节级恒同。
2. **退出码 0/1/2/9（红是数据非器红）**——先按退出码分器面（2=改调用·
   9=补目标），再读 JSON 按 verdict/kind 分数据面。
3. **--once/--loop 双模**——`--once` 步骤内联；`--loop` 后台哨＋轮帽自停；
   `--sleep-scale 0` 为离线确定性钉。
4. **--injector 离线可测**——演练/CI 全注入形＋`--sleep-scale 0`：零真网络
   零真编译；未覆盖 fail-loud 9 绝不静默走真。
5. **编排零新引擎**——器内全 subprocess 直调既有引擎；工作流侧同律：调器读
   JSON·不重造判据。

三正典嵌段（可整段复制·样例为实跑所产）：

| 嵌段 | 文件 | 器 | 场景 |
|---|---|---|---|
| ①后台哨 | `examples/workflows/backend-sentinel.md` | sentinel | nohup 长驻三路信号源→JSONL 事件流＋消费端 |
| ②单步推 CI | `examples/workflows/step-pushci.md` | pushci | `--dry-run` 先行人审→真发→verdict 七态分流 |
| ③疏通闭环 | `examples/workflows/loop-unclog.md` | unclog | 干跑→人审→`--apply`→复核·诚实墙分派 |

## 七、典型链路三条（器实况命令·旗标均 cw_sentinel 等器 `--help` 实出）

```bash
# 链一：CI 红炉修复链（诊断层→编排层·README-cw 同款）
bash cw.sh doctor --json dyld.json
bash cw.sh net-probe --rounds 2 --interval 60 --stable-window
bash cw.sh pushci --repo-path . --branch feature/x --json pushci-report.json
bash cw.sh triage --repo ORG/REPO --run ID --logs
```

```bash
# 链二：实时服务闭环（服务层·四职能各一拍·先看账后落刀）
bash cw.sh sentinel --once --watch-ledgers ledgers/ --json sentinel-report.json
bash cw.sh cw-doctor --json doctor.json --registry order.txt
bash cw.sh unclog --src src/ --world world/ --audit --json audit-baseline.json
bash cw.sh wash-shape --file demo.v --json plan.json
# （人审放行后落刀·白名单形与真编译 guard 规程见 ops 手册 §3）
bash cw.sh wash-shape --file demo.v --apply --json shaped.json
```

```bash
# 链三：文档收口链（v39·文档改动交付前自证）
bash cw.sh doc-lint --repo . --json doclint-report.json
```

## 八、证据与归属

- 本文撰写时点：rocqwash v39（caa3a28·工作树净）。全部旗标引用取自本席当日
  逐器 `--help` 实跑（cpu_guard 包裹·13 器 rc=0：cw_sentinel／wash_shape／
  unclog／pushci／cw_doctor／net_probe／ci_triage／toolchain_dyld_doctor／
  registry_union／chain_graph／doc_lint／cure_applier／scan_v4_token），
  并经 `bash cw.sh doc-lint` 三查机检（本文件旗标查零漂）。
- 本文由文档收口席（工装席·docs）撰写；领地＝本文件＋CONTRIBUTING §7 增补＋
  CHANGELOG.md 新建。`cw.sh`／`tests/run_tests.sh`／README 系列归集成席零触碰；
  冻结八件／quad8／更新账.md 禁触未犯（更新账仅只读蒸馏）。
- 行号会随多席并发漂移：旗标与命令以 cw_sentinel 等各器 `--help`＋docstring
  为正本，漂移时按节名重锚（whitepaper 附录 B 同律）。
