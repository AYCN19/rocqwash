# rocqwash 服务战役总报告 v1.0（service campaign total·2026-11-11）

> **v35-v41 七波累账总报告**——诊断层→编排层→服务层→接驳体检层→语料滚扩→
> 正典化巩固→并行与护栏，2026-11-11 单日七波（七 commit）全役蒸馏。本件属
> v41 账排程「收口总档波（v42）」的交付件（更新账.md:3760 原文作「五波累账
> 总报告」·本件按任务书承 v35-v41 全役七波）。
>
> **素材与事实纪律**：①更新账.md v35-v41 各段（更新账.md:3552-3760·只读蒸馏
> 未触原文）；②docs/ 已有四件——workflow-integration-whitepaper／
> perf-profile／push-gate-dual-door-assessment／ops-realtime-service（同属
> v40 收口波的在库件 service-layer-overview 一并参照，用于 §2 双维归类）；③
> git log v35..HEAD 与 git show --stat 七 commit 实测（本席本 ask 实跑·哈希
> 逐波录入 §1）；④cw.sh 二十工具册实测（cw.sh:99、cw.sh:104-153）。一切数字
> 与 commit 号自上述在盘材料转录·零凭记忆。
>
> **本席纪律**：只读与写作·零码改；冻结八件／quad8／更新账.md 禁触未犯
> （更新账仅只读）；cw.sh／tests 总套／README 系列归集成席零触碰。三闸收口
> 基准（doc_lint --repo drift=0／tests/test_destructive_matrix.py 17 判全过／
> tests/run_tests.sh 全套零红）归集成席终跑——本席不代跑，仅对本文交稿后
> 复跑 doc_lint 验本文零漂（§5 末）。

## §1 七波演进脉络（v35→v41·每波要点＋commit 号）

git log v35..HEAD 实测恰七 commit（本席实跑 `git log --oneline`，老→新）：
acf9fe6（v35）→4026051（v36）→41e74b0（v37）→c205ea0（v38）→caa3a28（v39）
→496ebdf（v40）→c5df4d4（v41·HEAD）。

### 波一·v35 诊断层（acf9fe6）

20261110 mac-runner CI 诊断六幕实战的工具化（更新账.md:3554）。四器落刀：
`tools/toolchain_dyld_doctor.py`（dyld 断链诊断·otool -L 解析硬引用→missing
件 donor 根溯源→只出建议禁代执行·`--smoke` 冒烟）、`tools/net_probe.py`
（上传端点网络窗探针·**双探稳窗律**连续两轮全过才 STABLE·a single-probe round must not initiate）、
`tools/ci_triage.py`（CI failing-build triage·五族判类谱 A 内容红/B NETRED/C 工具链断链
/D 排队资源墙/E coqchk-skipped＋绿炉·判类序 UNRECOGNIZED>C>A>E>B>D·
`--baseline-seconds` 倍数对表）、`tools/registry_union.py`（注册册 union operation
·main 为底＋对 base 提取真独有行·A1/A2/A3 断言 fail-loud·`--reanchor`
md5-8 正典形·dry run by default）。本地映射半边同步：CW 侧 cw_paths v1.0→v1.1
（更新账.md:3580）。集成面 cw.sh 十一工具；总套 47 例/43 过/0 failing/4 SKIP
（更新账.md:3562）。git show --stat：26 files·+3610/-16。

### 波二·v36 编排层（4026051）

一键流水线把 v35 四器编排成链（更新账.md:3591）：`tools/pushci.py`（1918 行）
五段管线——preflight（doctor 环境闸＋net_probe 稳窗闸＋可选 `--pre-scan-gate4`
头注预扫）→push（HTTP/1.1 三发×45s→ghproxy 换路两发·github.com 形才换）→
resolve+watch（head_branch+head_sha 咬合·status-only 口径）→heal（ci_triage
判类分派·B/E 双探稳窗后 rerun〔403 幂等〕帽 `--max-heal 3`·A/C 停禁代修·
表外族禁自动 rerun）→verdict±merge（409 重拉 tip 歇 60s 重试 ≤3）·verdict
七态封册。**编排零新引擎**（全 subprocess v35 引擎）；六场景 15 判 canned
（S1-S6·--injector 双形＋--git-caller 成对·离线零真网络）。cw.sh 十二工具；
总套 48/44/0 failing/4 SKIP。跨席协作判例：测试席 escalate「实现缺席」→编排席令
「先铸实现无关件＋有界轮询」→实现落盘逐版对齐——三层各一席零撞车
（更新账.md:3598）。git show --stat：14 files·+3916/-22。

### 波三·v37 服务层（41e74b0）

批处理工具→实时动态服务层（更新账.md:3615）。三器落刀：`tools/unclog.py`
（1161 行·疏通闭环 probe 归集→chain_graph 链根→cure_applier 只正典包落刀→
scan_v4+probe 复核→verdict；诚实墙逐根列因禁硬凑；dry run by default）、
`tools/wash_shape.py`（洗形五洗流水：词面/token/头注/行尾/锚·plan/apply 两段
·plan 零写盘·冻结名册红拒）、`tools/cw_sentinel.py`（1079 行·实时哨三路信号
源 CI 红炉/本地堵账/构建日志→JSONL 事件流·**report-only 缺省零动作**）。
接口五件套三器贯通：JSON-in/out schema designated、退出码 0/1/2/9（红是数据非器
failing）、--once/--loop、--injector/--sleep-scale 离线可测、编排零新引擎
（更新账.md:3627）。cw.sh 十五工具；总套 51/47/0 failing/4 SKIP；README-cw 新增
「工作流配合接口」节。git show --stat：11 files·+4011/-13。

### 波四·v38 接驳体检层（c205ea0）

接驳与体检（更新账.md:3645）：`tools/cw_doctor.py`（1082 行·四域聚合体检
环境 40/网络 20/注册 25/堵账 15→健康分 0-100＋advice 逐非绿域指向对应器·
真机全真跑 91.67 healthy rc=0）；cw_sentinel `--on-red-preset` 接驳预设
（unclog/pushci·干跑缺省铁律·与 `--on-red` 互斥 rc=2）；unclog `--audit`
真树只读审计（零写盘硬保证＝全文件 md5 跑前跑后自证恒同·与 --apply/--loop
互斥）；韧性层 `tools/_http_backoff.py`（403/429/5xx 指数退避·injector 路零
重试）＋子进程防挂（`--timeout`/`--subproc-timeout` 缺省 120s）＋net_probe
`--jitter`/`--seed`。examples/workflows 三正典嵌段＋docs/workflow-integration-
whitepaper v1.0（11 bash 围栏块 bash -n 两轮 0 败·134 枚旗标逐枚 grep reconcile
0 缺失）。cw.sh 十六工具；总套 52/48/0 failing/4 SKIP。git show --stat：
18 files·+3364/-171。

### 波五·v39 语料滚扩（caa3a28）

金标纪律执行的语料滚扩（更新账.md:3676）：`wash/cure_pack.json` v1.3→v1.4
（24→25 式）——三源勘察得候选 11 条，**收 1 式** `cure39_ifq_connective_
qualify`（引据＝Set 仓锚 commit 9a51c74 diff 逐字 25 站·face-regex 复用零新
引擎），**拒 10 条逐条因**；`tests/fixtures/header_map_v1.json` 头注模板库
v1（preset=campaign_set_diamond·占位 6 枚全带引据·**缺 evidence 拒载由代码
执行**）；`tools/doc_lint.py` 文档←→实现一致性三查器（工具表/计数/旗标三查
·初跑 drift=3→主会话补 netname-normalize/select-audit/doc-lint 三路由后
consistent drift=0）；tests/test_relay_e2e.py 接驳端到端＋docs/ops-realtime-
service 运行手册。cw.sh 十七→十九工具；总套 54/50/0 failing/4 SKIP；doc_lint
refs=87 drift=0。git show --stat：18 files·+2962/-73。

### 波六·v40 正典化巩固（496ebdf）

稳态巩固（更新账.md:3706）：cw_sentinel state 崩溃恢复（损坏 fail-loud 9 红拒
·`--rebuild-state` 唯一合法重建路）＋JSONL 轮转（`--emit-max-bytes` 保留 2 代
·seq 跨代续号）；unclog --loop seen 差分事件；wash_shape plan-cache 失效；
`tools/baseline_diff.py`（545 行·两份 audit 基线对比→new/resolved/persistent
按链根逐因对齐·**candidates 集不同=incomparable 如实拒判**）；**破坏面复核
矩阵** tests/test_destructive_matrix.py 17 行拒写判据（负例注入自证·逮住 1 处
真护栏缺口——cw_sentinel plain `--on-red` 无 `--emit` 被 rc=0 接受·修复排
v41）；文档收口（CONTRIBUTING 接口五纪律节＋CHANGELOG＋docs/service-layer-
overview 四职能×三层全貌＋examples/baselines/README 规程）。cw.sh 二十工具；
总套 56/52/0 failing/4 SKIP。git show --stat：16 files·+2953/-99。

### 波七·v41 并行与护栏（c5df4d4）

并行与护栏缺口修复（更新账.md:3735）：sentinel 护栏缺口修复——plain
`--on-red` 缺 `--emit` → rc=2（cw_sentinel.py:883-886·旁路动作必伴随事件流
落盘），矩阵 S2 扩 plain+preset 双向（v40 登记→v41 转正）；双门归一评估报告
docs/push-gate-dual-door-assessment（**建议案 A 并立各判各的**·零动码）；
probe_engine `--jobs K` 并行池（缺省 1 串行零漂移·**台账序恒按候选典序**·
温控 K≤2 建议·候选重名 fail-loud）＋unclog `--probe-parallel` 透传＋report
timing 增 jobs 维度（矢量十三→十四）；sentinel preset 注册表扩展（wash-shape
/triage 动态键/cw-doctor 三新预设＋PRESET_REQUIRED_ARGS 声明化＋链式
`--on-red-preset` 一败续行）；perf 规程与 docs/perf-profile（四源如实·DS4
K 真编译三跑不可测录方法占位零编数字）。真树 audit 基线 27/27 RC0 red=0 入
examples/baselines/（§4）。总套 56/52/0 failing/4 SKIP＋矩阵 17 判全过＋doc_lint
consistent。git show --stat：14 files·+1239/-154。

## §2 现役能力全表（cw.sh 二十工具·四职能×三层双维归类）

统一入口 `bash cw.sh <tool> [args...]`（repo 根·参数与退出码 1:1 透传·
bash 3.2 兼容·cw.sh:65-82 路由契约）。二十工具册实测自 cw.sh:104-153 与
cw.sh:207-226 路由段；三层归属与职能槽沿用 docs/service-layer-overview
§四表（v39 current state）＋各波账，baseline-diff（v40 新入册）系本席按 cw.sh:60-62
描述定位（该账未给职能槽·如实注）。「役前底座」＝v29-v32 既有件（战役复用
的引擎面）；四职能＝清洗/shape normalization/排障/clear blockages。

| # | 路由 | 目标脚本 | 三层 | 职能 | 入列 | 一行职责（缺省安全态） |
|---|---|---|---|---|---|---|
| 1 | `scan4` | `scan/scan_v4_token.py` | 役前底座 | 普查面 | v29-v32 | token 级限定名普查 |
| 2 | `cure` | `wash/cure_applier.py` | 役前底座 | 清洗（刀） | v29-v32 | 消费位治愈正典包（dry run by default·v39 扩 v1.4 共 25 式） |
| 3 | `probe` | `wash/probe_engine.py` | 役前底座 | 探针面 | v29-v32 | 批量闭包相容探针（v41 增 `--jobs K` 并行·典序确定性） |
| 4 | `chain` | `tools/chain_graph.py` | 役前底座 | clear blockages（挑根） | v29-v32 | 多账合并链根图 |
| 5 | `sync-ledger` | `tools/ledger_sync.py` | 役前底座 | 台账面 | v29-v32 | probe 台账×状态台账合并同步 |
| 6 | `erasure` | `verify/erasure_classifier.py` | 役前底座 | 分类面 | v29-v32 | 擦除位分类顾问 |
| 7 | `dual-scan` | `scan/dual_scan.py` | 役前底座 | 对拍面 | v29-v32 | 双器对拍驱动 |
| 8 | `doctor` | `tools/toolchain_dyld_doctor.py` | 诊断层（v35） | 排障 | v35 | dyld 工具链断链诊断（只诊断＋restore 建议·禁代执行） |
| 9 | `net-probe` | `tools/net_probe.py` | 诊断层（v35） | 排障 | v35 | 网络窗探针（双探稳窗·a single-probe round must not initiate；v38 增 `--jitter`/`--seed`） |
| 10 | `triage` | `tools/ci_triage.py` | 诊断层（v35） | 排障 | v35 | CI failing-build triage（五族＋绿炉判类谱·`--logs`/`--baseline-seconds`） |
| 11 | `union` | `tools/registry_union.py` | 诊断层（v35） | 手术器 | v35 | 注册册 union operation（dry run by default·`--reanchor` md5-8 正典形） |
| 12 | `pushci` | `tools/pushci.py` | 编排层（v36） | single-command pipeline | v36 | 修复后推送 CI single-command pipeline（发射闸→push→watch→heal→verdict±merge·七态封册·`--dry-run` 零副作用） |
| 13 | `sentinel` | `tools/cw_sentinel.py` | 服务层（v37） | 排障（实时哨） | v37 | 实时动态哨·三路信号源→JSONL 事件流（report-only 缺省·`--on-red-preset` 五预设可链式·v40 稳态化·v41 护栏双守卫） |
| 14 | `wash-shape` | `tools/wash_shape.py` | 服务层（v37） | 清洗/shape normalization | v37 | 正典形五洗流水（词面/token/头注/行尾/锚·plan 缺省零写盘·`--header-map-preset` 模板库） |
| 15 | `unclog` | `tools/unclog.py` | 服务层（v37） | clear blockages | v37 | 疏通堵塞闭环引擎（dry run by default·`--audit` 只读基线·诚实墙禁硬凑·v41 `--probe-parallel`） |
| 16 | `cw-doctor` | `tools/cw_doctor.py` | 服务层（v38） | 排障（聚合） | v38 | 综合体检四域聚合→健康分 0-100＋advice（只诊断禁代执行） |
| 17 | `doc-lint` | `tools/doc_lint.py` | 服务层（v39） | close out（四职能外） | v39 | 文档←→实现一致性三查（工具表/计数/旗标·verdict consistent/drift） |
| 18 | `netname-normalize` | `tools/netname_normalize.py` | 役前底座（v39 入口补齐） | 净名面 | v39 | .v.v 双后缀净名归一（映射表＋`--apply` 改名 md5 验讫） |
| 19 | `select-audit` | `tools/select_audit.py` | 役前底座（v39 入口补齐） | 审计面 | v39 | 批选审计器（对 order.txt 全表 grep 剔重＋Require 面审计 v6） |
| 20 | `baseline-diff` | `tools/baseline_diff.py` | 服务层（v40） | clear blockages（堵账对比收口） | v40 | 堵账基线对比（new/resolved/persistent＋verdict 四态·incomparable 如实拒判·timing 不入对比） |

双维速读：**排障**＝doctor/net-probe/triage/sentinel/cw-doctor 五器（诊断层
三器＋服务层哨与聚合体检）；**清洗/shape normalization**＝cure/wash-shape 两器（cure 为刀·
wash_shape 编排落刀面）；**clear blockages**＝chain/unclog/baseline-diff 三器（挑根/
闭环/对比收口）；收口面 doc-lint 在四职能外；其余为役前底座与编排层
（pushci 横跨诊断编排消费面）。入口演化 11→12→15→16→19→20 与 §1 各波
集成面行逐一吻合。

## §3 判例总表（v35-v41 各账「判例/口径登记」节蒸馏·编号沿用）

各账登记节原文编号照录（登记节无编号者按出现序补序号·来源锚随行）。

| 编号 | 来源锚 | 判例/口径 | 蒸馏 | 后续落点 |
|---|---|---|---|---|
| v35-① | 更新账.md:3574（§三） | 口径勘误 | v34 账记 t_quad8_check「failing」——本环境实为 SKIP（rc=111·正本四仓副本群不在卷）；非器红非本轮引入·两环境语境差如实并记 | 套件口径「SKIP 不计红」沿用至今 |
| v36-① | 更新账.md:3607（§四.1 契约偏离登记①） | --injector 双形 | pushci `--injector` 双形（steps 严格按轮＋flat 夹具 verbatim）——语义未放宽 | v36 六场景 15 判离线可测的正本形态 |
| v36-② | 更新账.md:3607（②） | README 计数面 | README.md 无工具计数（改同步例数行 43→48） | 例数行同步律沿用 |
| v36-③ | 更新账.md:3607（③） | README 快照面 | README.md 无 v35 快照行（v35 波未入主 README·本轮只补 v36 行内点名） | — |
| v36-④ | 更新账.md:3607（④） | 不代改史 | tests/README.md「在册 47 例」系当时现势陈述·遵不代前轮改史原样保留 | — |
| v37-① | 更新账.md:3632（§三） | 跨席计数漂移 | 哨席 cw.sh 头注计数十三与 usage 十二不一致→集成席统一十五（跨席计数漂移·集成收口职·判例） | 计数漂移归集成收口职的成文先例 |
| v37-② | 更新账.md:3633（§三） | injector 哲学 | unclog `--injector`＝「canned 检验·真编排」——chain/cure/scan/frozen8 注入下照旧真跑（非傀儡测试）·离线可测与真实编排并存 | 白皮书 §1 纪律④机理节同源 |
| v38-① | 更新账.md:3663（§三裁决登记） | 同槽互斥 | `--on-red-preset` 与 `--on-red` 同给＝互斥 rc=2（任务书「preset 优先」vs selftest「互斥」张力→按库同槽互斥纪律裁决·docstring 记界） | ops 手册 §2.2 负例表在册 |
| v38-② | 更新账.md:3664（§三） | 双钟不并铃 | cw_sentinel `--timeout`（HTTP 单请求）与 `--subproc-timeout`（子进程帽）两物分立（v37 既约口径不动） | v40 §三延续登记 |
| v39-① | 更新账.md:3693（§三） | 扩容诚实 | cure_pack v1.4 单式扩容＝勘察诚实结论（三源无第二件复现的形态按律候勘·非扩容不足） | 「宁缺毋滥」代码化（header_map 缺 evidence 拒载） |
| v39-② | 更新账.md:3694（§三） | 判据打磨 | doc_lint 幻引/悬引判据的实证修正（dup≠多余·README.md:232 union-freeze --world 合法多值） | doc_lint 判据定型 |
| v40-① | 更新账.md:3718（§二矩阵战果） | 真护栏缺口 | 破坏面矩阵逮住 cw_sentinel plain `--on-red` 无 `--emit` 被 rc=0 接受（护栏真身在 preset 路径·探针实跑证实动作执行）——负例注入自证＋真缺口逮住双证 | **v41 修复转正**（cw_sentinel.py:883-886 守卫·矩阵 S2 扩双向） |
| v40-② | 更新账.md:3722（§三） | 旗名分立 | `--loop-max` 与 `--max-rounds` 旗名分属 unclog/sentinel 两器·未造别名（任务书笔误如实纠正·docstring 记界） | — |
| v40-③ | 更新账.md:3723（§三） | 双钟延续 | cw_sentinel 双钟分立延续（on-red 60s 旁路帽 v37 既约不动） | — |
| v41-① | 更新账.md:3747（§二跨席协作） | 同文件串行化 | 并行席与 perf 席同改 unclog.py（并行层＋timing 维度）＝共享基座增量补维（perf 席开工前首读已见并行层·改补不覆）——零冲突实况 | 同文件双席协作法样本 |
| v41-② | 更新账.md:3748（§二） | 代际演替 | 器产账面代际演替如实记录：audit 基线 JSON 被 07:12 真编译跑重产（早先 rc=127 快败账被覆盖） | perf-profile §一 DS1 以 07:12 版为准逐字读验 |

## §4 真实树战报（audit 基线 27/27 RC0·三发史·诚实墙拒判实录）

- **对象与候选面**：Set repository ConstructiveWorld_Live 真树·27 件＝20261110 两批
  新落位（b48-52 十三＋b53-57 十四·md5 实测回填 TSV）·世界＝runner 工作区
  Live APFS clone（537 vo·现役代际·零触碰 runner 正本）（更新账.md:3698、
  3727；examples/baselines/audit-ConstructiveWorld_Live-20261111.note.md）。
- **三发史**（更新账.md:3752-3753·note 侧车「对照史」节）：第一/二发 rc=127
  器因红（编译器缺位——「裸 coqc 不存在」铁则又一证）·**诚实墙正确拒判**
  （「代差型/器因红·禁硬凑」）；第三发带 `--rocq-cmd` 9.3 coqc 模板成产。
- **成产战报**：**27/27 RC0·red=0·墙=0**·cures_planned=0（audit 只读）·
  verdict audit exit 0。timing 段：manifest 1.289s／probe_chain 190.728s／
  total 194.086s（唯一非确定段·不入基线对比）。本席实读在库正本
  examples/baselines/audit-ConstructiveWorld_Live-20261111.json 与上述数字
  逐项相符（args.rocq_cmd＝opam93 coqc `-native-compiler no -q -Q . "" {name}.v`
  ·src=ConstructiveWorld_Live·world=probe_world_v38·injector=null）。
  实证意义：20261110 两批新落位面在现役世界代际**全部闭包相容**实锤
  （更新账.md:3753）。
- **入仓**：基线 JSON＋产账说明侧车 md 落 examples/baselines/·随 v41 commit
  c5df4d4 入库（更新账.md:3754；git show --stat c5df4d4 列 audit-…json 71 行
  ＋note 7 行）。对比器就位：baseline_diff.py 对两份 audit 基线出增减三清单
  ·账面自洽校验拦手编账（v40 §一②）。
- **代际演替如实记**：/tmp/audit_b48_b53_baseline.json 早先曾为 rc=127 快败
  跑产物·07:12 由真编译跑重产覆盖——perf-profile DS1 以 07:12 版为准逐字
  读验（docs/perf-profile §一 DS1 溯源注记·v41-②判例）。
- **诚实墙机制在册**（本战报的拒判实录即其首次实战）：unclog 诚实墙六因
  self-unwashable/cure-miss/frozen-in-service/root-file-missing/exclusive-
  group-conflict/no-chain-root 逐根列因禁硬凑（docs/ops-realtime-service
  §3.2）；审计零写盘＝全文件 md5 跑前跑后自证恒同违则 fail-loud 9
  （docs/ops-realtime-service §3.1）。

## §5 待办与 v43+ 路线图（各账「边界与待办」节汇总·去重）

**役内已闭（待办→落点）**：pushci single-command pipeline（v35 边界.1→v36 落地）；
sentinel `--on-red` 接驳预设（v37 边界.3→v38 落地）；真树 audit 活跑与基线
入仓（v38 边界.1/v39 边界.1/v40 边界.1→v41 三发成产入库）；sentinel plain
`--on-red` 守卫修复＋矩阵判据转正（v40 边界.2→v41 落地）；push_gate 双门
归一评估（v36 边界.3/v40 排程→v41 docs/push-gate-dual-door-assessment 建议案
A 并立·零动码·v41 边界.2 闭合）；本总报告（v41 边界.3 v42 排程→本件）。

**pending execution/未竟（v43+ 候选·逐条注来源）**：

1. probe `--jobs`>1 真树实测（温控窗候令·canned 机制实证已毕）——v41
   边界.1；DS4 真编译 K=1/2/3 三跑占位待回填 docs/perf-profile §五（回填即
   perf-profile v1.1·docs/perf-profile §六.3）。
2. pushci 真实 CI 端到端活跑（真 push→真炉→heal·首跑建议 `--dry-run` 先行
   再真发）——v36 边界.2、v38 边界.2、whitepaper 附录 A 未实跑项同。
3. unclog `--apply`／wash_shape `--apply` 真实树活跑（fixture 级全验·首跑
   建议 `--src` 小子集先行·白名单形规程 docs/ops-realtime-service §3.3）——
   v37 边界.1。
4. sentinel `--loop` 长驻真实消费场景（工作流后台 bash 任务挂 JSONL 流·配合
   下波战役即验证）——v37 边界.2。
5. cure39 新式（cure39_ifq_connective_qualify）真实树活跑（fixture 级全验）
   ——v39 边界.2。
6. 9.1 编译器依赖面候决（`ROCWASH_ROCQ` 惯指路径 MISSING·指 9.3 CW_MAC93
   或复原捐体·CW 侧 cw_paths v1.1 移根监察表在册）——v35 边界.2。
7. ci_triage `--watch` 长盯态（pushci watch 内嵌版外的独立长盯）——v36
   边界.3。
8. wash_shape `--header-map` 模板库随战役语料滚动扩容——v37 边界.3（v39
   header_map_v1 已立首库）。
9. 双门案 A 残余风险在册：无机械闸强制工作流先判门 B（pushci 单跑即发射·
   窗纪律靠文档与嵌段约束）；若日后要机械强制·案 B 是唯一不改判据正本的
   路径·但须先解 c4 全套成本与 c1 新枝首推死锁再议——docs/push-gate-dual-
   door-assessment §5 残余风险。

**v42 收口总档波剩余（v41 边界.3 排程）**：三闸终跑（doc_lint --repo
drift=0／tests/test_destructive_matrix.py 17 判全过／tests/run_tests.sh 全套
零红）＝集成席终跑口径（本席不代跑·见卷首）；真机演练汇编；v43+ 路线图
（本节即其草案底稿）。

——本席交稿自证：本文件写成后经 `bash /Users/apple/Desktop/ConstructiveWorld/
cpu_guard.sh -MaxWaitSec 120` 包裹复跑 `python3 tools/doc_lint.py --repo .`
·verdict consistent drift=0（含本文旗标引用零漂）——实测记录见交割 notes。
