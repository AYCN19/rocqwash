# rocqwash 服务战役总报告 v2.0（service campaign total·2026-11-12）

> **版本**：v2.0＝**v1.0 基座全保留**（docs/rocqwash-service-campaign-total-
> v1.0-20261111.md·v35-v42 累账·2026-11-11）＋**「六波增补（20261112）」章**
> ——v43 机动实测→v44 哨长驻首演→v45 台账渲染→v46 红事件路由与注册册审计→
> v47 门控弧关闭与哨真仓首战→v48 多仓勘形与 DS4 三账收口。本件属 v1.0 §5
> 「v42 收口总档波剩余」的 v2.0 续档·任务书钦名。
>
> **素材与事实纪律（v2.0 增补面·一切数字自在盘材料转录·零凭记忆）**：①更新账.md
> v43-v48 段（更新账.md:3794-3944·只读蒸馏未触原文）；②docs/勘形-multi-repo-
> Main仓适配-20261112.md（v48 ⑦勘形档·分级与小改面）；③docs/perf-profile-
> v1.0-20261111.md §五回填两段＋examples/baselines/perf-README.md §3 判读三律；
> ④docs/ops-sentinel-长驻手册-v1.0-20261112.md（v48 哨手册）；⑤examples/
> baselines/ 三账实读（K1=audit-ConstructiveWorld_Live-20261111.json·K2=perf-
> ConstructiveWorld_Live-k2-20261111.json·K3=audit-k3-20261112.json——本席本
> ask 实读 K3 账 args.probe_parallel=3/timing.probe_chain_s=165.202/
> n_records=27/n_red=0 逐项相符）；⑥git log c5df4d4..HEAD 与 git show --stat
> 六 commit 实测（本席本 ask 实跑·哈希逐波录入 §6）；⑦v48 哨长驻产物三件套
> 实读（CW 侧 _log/sentinel_v48/·本席本 ask 实测）。
>
> **任务书给形与实取不符登记**：任务书「23→24→25 器演进」末位与实取不符——
> 实取 23（v46）→24（v47）→**24（v48 零新器）**（git show --stat 325b4dc 六
> 文件无 cw.sh·cw.sh:247-270 case 分派实数二十四路由·本席实跑）——按实取为准
> 如实登记（docs/勘形-multi-repo-Main仓适配-20261112.md §1.3「任务书给形与
> 实取不符·实取为准·如实登记」同律·v35-① 口径勘误判例同款·详见 §7.1）。
>
> **本席纪律**：只读与写作·零码改；冻结八件／quad8／更新账.md 禁触未犯
> （更新账仅只读）；rocqwash 工作树零 git commit（v48 325b4dc·工作树净口径
> 保持）；cw.sh／tests 总套／README 系列归集成席零触碰。三闸收口基准
> （doc_lint --repo drift=0／tests/test_destructive_matrix.py 17 判全过／
> tests/run_tests.sh 全套零红）归集成席终跑——本席不代跑总套，仅对本文交稿
> 后复跑 doc_lint 验本文零漂（卷末交稿自证）。

---

## §0 v1.0 基座全文（2026-11-11 原样保留·零改一字）

> **基座声明**：以下为 docs/rocqwash-service-campaign-total-v1.0-20261111.md
> 全文原样保留（v42 收口时点口径）——时点性陈述（「现役」「二十工具」「56 例」
> 「入列」等）均系 20261111 基座口径·现势以 §7 计数总表与 §6 各波为准；其
> §5 候令九条的六波收口对账见 §6.x；v1.0 卷末交稿自证行系其当时实测记录·
> 本件不代跑不代改。

**rocqwash 服务战役总报告 v1.0（service campaign total·2026-11-11）**

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

### §1 七波演进脉络（v35→v41·每波要点＋commit 号）

git log v35..HEAD 实测恰七 commit（本席实跑 `git log --oneline`，老→新）：
acf9fe6（v35）→4026051（v36）→41e74b0（v37）→c205ea0（v38）→caa3a28（v39）
→496ebdf（v40）→c5df4d4（v41·HEAD）。

#### 波一·v35 诊断层（acf9fe6）

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

#### 波二·v36 编排层（4026051）

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

#### 波三·v37 服务层（41e74b0）

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

#### 波四·v38 接驳体检层（c205ea0）

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

#### 波五·v39 语料滚扩（caa3a28）

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

#### 波六·v40 正典化巩固（496ebdf）

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

#### 波七·v41 并行与护栏（c5df4d4）

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

### §2 现役能力全表（cw.sh 二十工具·四职能×三层双维归类）

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

### §3 判例总表（v35-v41 各账「判例/口径登记」节蒸馏·编号沿用）

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

### §4 真实树战报（audit 基线 27/27 RC0·三发史·诚实墙拒判实录）

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

### §5 待办与 v43+ 路线图（各账「边界与待办」节汇总·去重）

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

---

## §6 六波增补（20261112·v43→v48）

**commit 面（本席本 ask 实跑 `git log --oneline c5df4d4..HEAD`·老→新恰六
commit）**：ffb8c82（v42 收口总档波＝v1.0 基座波·本件 §0 即其交付件）→
459a77d（v43）→8e124b3（v45）→a9720ab（v46）→6217808（v47）→325b4dc
（v48·HEAD）。**v44 零码改·无独立 commit**——纯运行波·其账由 v45 commit
8e124b3 携带的更新账 v44 段在库（更新账.md:3814-3834）。六波素材全部引更新账
v43-v48 段（更新账.md:3794-3944·只读蒸馏未触原文）＋上列在库件；各波 git
show 统计均本席实跑。

### 波八·v43 机动实测（459a77d·零码改纯验证·路线图④+①双收口）

主会话机械执行两件（更新账.md:3794-3810·git show 统计 459a77d＝3 files
+103/-0）：

- **④门控编译弧总开关收口**：`ROCWASH_ROCQ` 指 9.3 多路器
  （mac93_install_work/opam93/rocq93/bin/rocq 实测在卷）→tests/test_cure_pack.py
  门控弧 **TEST-CURE-PACK: PASS rc=0**（E2 consumer-unit magic 0/0·world
  accessor debt pinned=1·E2/E3 夹具 9.3 编译全链通）——9.1 工具链 MISSING
  不再阻门控弧·9.3 直替可行实证（更新账.md:3800）。诚实记界：翻绿是「现役
  世界代际」passing·**非 9.1 复绿**（§9 边界 3 同源）。
- **①probe --jobs 真树 DS4 回填收口**：27 件同候选面（/tmp/audit27.tsv·
  ≤30 件采样规模判例）K=2 audit——`tools/unclog.py --audit
  --probe-parallel 2` probe_chain **101.916s vs K=1 190.728s＝1.87×**·
  n_records=27 n_red=0（与 K=1 互证）·timing.jobs=2 维度字段实测在账
  （更新账.md:3801）。同候选面·同世界（/tmp/probe_world_v38 APFS clone
  537 vo）·同 rocq-cmd 模板（9.3 coqc）·cpu_guard 包裹——除 K 外全维恒同
  ＝baseline_diff 口径可比（更新账.md:3805）。K=2 基线入仓 examples/baselines/
  perf-ConstructiveWorld_Live-k2-20261111.json（更新账.md:3806·perf-profile
  §五回填段 :157-165 同数·本席实读该账 args.probe_parallel=2 逐项相符）。
- 集成面不变：cw.sh 二十工具·测试 56 例 52 过 0 failing·三闸收口全绿
  （更新账.md:3810）。

### 波九·v44 哨长驻首演（无独立 commit·零码改纯运行·路线图②close out）

「实时动态配合工作流」目标的**首场实战验证**（更新账.md:3814-3834）——
哨在真仓真历史上完整跑通「发现→classification→事件流」三段·v37-v39 三波服务层设计
被真实数据回灌确认（更新账.md:3829）：

- **命令**：`python3 tools/cw_sentinel.py --loop --interval 45 --max-rounds 15
  --watch-repo hy7pc8gfmf-dotcom/ConstructiveWorld-Set --state-file
  /tmp/sentinel_v44_state.json --emit /tmp/sentinel_v44_events.jsonl`
  （report-only 缺省零动作·更新账.md:3820）。
- **行为**：15 轮×45s 全程跑毕（12 分钟窗）——**首轮 retro-triage 全战役史**：
  fresh state 下把 Set repository 30 条历史 run 拉出经 ci_triage 判类逐条归族
  （更新账.md:3821）。
- **14 事件**：family 分布 A-content-red×9／B-netred×1／C-toolchain-break×1／
  E-coqchk-skipped×1／UNRECOGNIZED×2；action fix-content×9／
  rerun-after-stable-window×2／restore-toolchain×1／watch-only×2
  （更新账.md:3822）。
- **判类吻合度（核心验证）**：#280→A（陈旧基座 uab_ssUnit 时代）✓·#283→C
  （dyld 断链日）✓·#289→E（上传 DNS 窗）✓·#286 cancelled→B-netred 连坐＋
  UNRECOGNIZED 并列不充谱 ✓——判类与 20261110 六幕实战实况逐条吻合
  （更新账.md:3823）。
- **幂等**：第 2-15 轮零重复事件（state seen 生效）＝长驻稳态实证
  （更新账.md:3824）。

### 波十·v45 render_events 台账渲染器（8e124b3）

- **`tools/render_events.py`**（547 行·git show 统计 8e124b3 本席实跑＝3
  files +601/-3）：哨事件 JSONL→markdown 台账渲染器——`--events`/`--dir`
  合并（seq+ts 排序）→kind/family/action 三维分布＋逐事件 9 列表（坏行容错
  rc1·未知 kind 归 other·竖线转义）＋`--json` summary
  （rocqwash-render-events/1）＋`--top` 截断（更新账.md:3844）。自证：
  selftest 七矢量 rc=0＋**真实哨产出渲染断言**（v44 14 事件·family
  A=9/B=1/C=1/E=1/UNREC=2 独立重算全对·两跑字节恒同——更新账.md:3844）。
- **集成**：cw.sh 二十一路由（render-events 挂接六处同步·锚两败教训＝v40
  baseline-diff 插位改序·按实文重锚三发收口）；doc_lint VERDICT consistent
  drift=0（refs=87）（更新账.md:3845）。
- 八波总收兵（v35-v45）：九 commit 全 ls-remote reconcile·路线图②③④①⑧已
  close out·⑤⑥⑦pending execution（更新账.md:3853）。

### 波十一·v46 red_dispatch＋registry_audit＋push_gate 归一评估（a9720ab·路线图③实质关闭）

三席并铸＋集成席收口（更新账.md:3857-3884·git show 统计 a9720ab 本席实跑
＝12 files +2522/-15）。代际注：本波任务书铸于 v37 基线·落刀时实况已 v45
8e124b3——集成席实勘后**按现势落 v46 口径**（23 工具/58 例·更新账.md:3859）；
两新器恰为 v45 路线图候令面实质推进：red_dispatch＝pending execution③接驳守门的产品化·
registry_audit＝真仓活跑安全前置（更新账.md:3859/:3877）。

- **`tools/red_dispatch.py`（约 760 行）红事件路由器**（更新账.md:3865）：
  sentinel 事件 JSONL→五族路由（B/E→pushci 重派／A→manual-fix-note 禁代修
  出 fix 清单／C→doctor／blocking→unclog 落刀仅显式人审／build-signal→
  wash-shape）＋D/UNRECOGNIZED→watch-only；三档 `--preset`（report-only
  缺省／suggest／auto 显式）·validate-all-then-execute 全批零半派·
  `--state-file` 防重＋`--cooldown` 600·参数三级解算·shell 元字符守卫防注入。
  自证：`--selftest` rc=0 36 判 12 矢量＋live smoke（auto 标记文件实证·二跑
  cooldown skipped=1）。
- **`tools/registry_audit.py` 注册册卫生审计器**（只读铁律·零写盘·落刀面
  另由 registry-fix 承担·更新账.md:3866）：四账＝重复行/锚（撞文本·顺序号形
  ·形怪·缺锚·canonical #R<序>-<md5-8>）/孤儿双向/拓扑引用（`--live-src` 实件
  reconcile）；`--fix-plan` 只出确定性处方（DEDUP 保首/锚刷直用 registry_union
  引擎/ORPHAN-ADD 模板/撞锚列 unresolvable）。自证：`--selftest` rc=0 五判
  （v35 真账形态样张 19 病灶精确盘点·md5 冻结向量 77c2b9a8 实嵌·只读 md5
  恒同）＋**真仓只读 demo**：Set Live 权威对 duplicates=12（_CoqProject 尾区
  L492-515 逐字重复块·#40 直并族实证）anchors=523（撞锚 6 恰 v35 判例原文）。
- **docs/评估-push_gate推窗四判据与pushcinormalize-20261111.md**（更新账.md:3867）：
  推窗四判据（c1 ci-idle/c2 behind=0/c3 fetch-clean/c4 cert-green·判序
  c3→c1→c2→c4·只判窗不开推）vs pushci preflight 三闸逐项对照——**7 判据面
  零交·双门零互连**（grep 实证）；三案：甲 preflight 增第 4 闸（c1 证据死锁
  ＋c4>120s 两座山→不推荐）·**乙保持双门＋文档分工（推荐）**·丙判据下沉库
  函数（改 certify 深件→否决）；push_gate 非冻结（frozen8.py:74-83 实取八件
  无它·nonfrozen-mutable）。与 v41 先席档（push-gate-dual-door-assessment
  v1.0 案 A/B/C）同判旁证·两档并存不合并留档（更新账.md:3884）。
- **集成面＋帽值换代**（更新账.md:3868）：cw.sh 二十三工具（route/audit
  两路由）·run_tests.sh 58 例·**doc_lint DEFAULT_HELP_CAP 20→24**（集成席
  登记帽溢出 cure_applier/probe_engine→主会话裁决换代·v38 波时点已预注）；
  自证：run_tests.sh 58 例/54 过/0 failing/4 SKIP 两遍实跑 EXIT 0·doc_lint
  --help-cap 24 VERDICT consistent drift=0。

### 波十二·v47 ⑧关闭＋哨真仓首战＋registry_fix 执行器（6217808·路线图⑧正式关闭）

三席并铸＋集成席收口（更新账.md:3888-3915·git show 统计 6217808 本席实跑
＝7 files +1325/-16）：

- **⑧A 案执行完毕＝门控编译弧总开关翻绿**（更新账.md:3894）：tests/
  run_tests.sh 总开关段缺省探测四路径（`ROCWASH_ROCQ` env 已设则尊→9.3 多路
  器存在即 export·另三路径指认 Set repository gate7/gate6 正本与 BORN 世界 rocq）——
  门控弧四位翻绿（t_cure_pack 编译 check 段/t_probe_engine 真 rocq 节/
  run_tests 两套例·**判据语义零改动·经缺省面翻**）＋**CANON 三例超任务书
  翻绿**（t_gate7_wrapper 13/13·t_verify_gate6 五判·t_gate6_born_wrapper
  21/21·绿证在先方落缺省）·cure pack 编译弧全链 PASS（v43 27/27 同源先例
  复现）。**SKIP 4→1**·唯余 t_quad8_check＝CANON_W1 四仓副本群缺卷族·与
  门控无关如实留账（更新账.md:3897/:3914·§8 条 4 同源）。
- **哨真仓首战 33 事件**（更新账.md:3895）：cw_sentinel 双仓 `--once`
  （Set 30 runs/15 failing·Main 30/18）→**33 事件**（A19/UNREC8/E3/B2/C1——
  B-netred×2 恰 Set#269/Main#22 已知 NETRED 红炉族咬合＝判类真值对账）·
  passing 25 runs 静默记 seen＝绿也是真观测·二跑幂等零新事件（哨长盯旗名词面
  勘误一处→真旗标 `--max-rounds` 如实录）；JSONL 33 行逐行合法·schema
  rocqwash-sentinel-event/1·seq 递增·state seen 30/30 咬合。UNREC8 待人工
  复核＝判类谱「不充谱」设计内诚实（§9 边界 2）。
- **`tools/registry_fix.py`（1161 行）审计处方式执行器**（v46 待办 2 兑现·
  卫生环闭合 audit→fix 四步·更新账.md:3896）：DEDUP 保首（audit 原行号系
  验尸）／锚刷（registry_union.apply_reanchor 同款·缺实件 skip·MD5-DRIFT
  炸）／ORPHAN/缺锚/unresolvable→skip 如实（禁机械造锚）；断言三判（被治键
  duplicates=0／锚撞零新增 A3 引擎／孤儿不增）·任一炸=exit2＋**逐字节回滚**
  ·缺省干跑零写盘（work-dir 亦不建）。自证：`--selftest` 8/8 rc=0（
  `--apply` 12 重复块→0＋77c2b9a8 同输同出逐字节＝registry_union CLI 同参
  产物·人工炸点回滚·自然炸点 A3·落刀确定性）。
- **集成面**（更新账.md:3897）：cw.sh 二十四工具（registry-fix 六处同步）·
  run_tests.sh +57/-6（总开关段＋t_registry_fix 挂例）·**59 例/58 过/0 failing/
  1 SKIP** 两遍·doc_lint consistent·cw.sh 二十四工具齐。
- registry_fix 真树落刀候令：Set Live 双册 12 重复块＋锚刷处方已在案——真树
  落刀涉多写者仓（曾栢源线/值守席活跃）·候用户令或协调台对表
  （更新账.md:3908·§8 条 1 同源）。

### 波十三·v48 ⑦勘形分级＋DS4 三账收口＋哨手册＋哨长驻真部署（325b4dc·路线图八候选全数关闭）

三席＋集成席＋主会话（更新账.md:3918-3944·git show 统计 325b4dc 本席实跑
＝6 files +749/-5·**无 cw.sh＝零新器**）：

- **⑦多仓适配勘形** docs/勘形-multi-repo-Main仓适配-20261112.md（只读零动码·
  更新账.md:3924）：Main CI 实取三要点（现役唯 coq93.yml 9.3 单 Windows job·
  mac observation omit〔coq93.yml:32-33〕·checkout=v5 非 API tarball·
  concurrency 单组 cancel-in-progress〔heal rerun 连坐取消面〕·push allowlist
  [main]）→**分级 verdict＝即用 4／小改 3／中改 2**（勘形档 §四/:184-198）：
  最大缺口＝pushci PR 路 mirror-blind 双重失配（PR run head_sha=merge commit
  ≠pushed tip·coq93.yml:41-42 vs tools/pushci.py:942-944）＋unclog Main Live
  正本不可用（两中改）；五步建议路径（retro-triage 零码→fixtures 小改→
  `--dry-run`→push-main 真发→unclog 正本独立排程·勘形档 §五/:202-217）。
  api 实取 coq93.yml 606 行全文·selftest 实跑 rc=0（勘形档 §七/:233-241）。
- **①DS4 K=3 真跑收口**（更新账.md:3925）：examples/baselines/audit-k3-
  20261112.json 真树堵账基线落仓——27/27 RC0·probe_chain_s=165.202·三账
  cross-check against the reference **K1=190.728/K2=101.916（1.87×）/K3=165.202＝K3 较 K2 慢 1.62×＝
  负边际加速如实录**（现机 4 CPU·K=2 档位即拐点·DS4 纪律禁编数字禁凑绿）
  ·温控全账（FRONT·tlevel 58→60·无热钳位·挤压注记：跑时另一席 nice-19
  coqchk 17 件在飞）·baseline_diff 双向 verdict=stable 四元组恒同＝
  comparable。本席实读该账 timing.jobs=3/probe_chain_s=165.202/total_s=
  169.684/n_records=27/n_red=0 逐项相符；perf-profile §五回填段三行实数
  （:120-127/:167-174）。**路线图①DS4 三账齐正式收口——roadmap 总序八候选
  全数关闭**（②③④①⑧已收＋⑤⑥金标跳＋⑦勘形落地分级·更新账.md:3936）。
- **哨长驻运维手册** docs/ops-sentinel-长驻手册-v1.0-20261112.md（更新账.md:
  3926）：四节——部署〔仓外 CW 侧 _log 落位·nohup/后台两形〕／使用〔event
  schema＋render_events＋red_dispatch 配对＋--once 嵌段三用形〕／轮转恢复
  〔cw_sentinel.py:136 崩溃恢复判例＋2 代轮转＋seen 宁重复不丢件〕／实证账
  〔v44 14 事件＋v47 首战 33 事件＋v48 落位实况〕。file:line 直引 81 处·
  8 引锚 sed 逐行对表咬合·doc_lint refs=114 drift=0。
- **哨长驻真部署**（主会话·更新账.md:3942）：后台 exec_1b6e50d4·双仓
  10 分钟巡检·CW 侧 _log/sentinel_v48/ 三件套落位——本波手册即其运维正本。
  **本席本 ask 实读活体**（`ls`/`wc -l`/python3 实测）：三件套实存——
  events.jsonl 33 行·report.json（mode loop·interval 600.0s·round 5·双仓
  ci 源 runs_seen=30/30·round 5 零新事件＝部署后幂等在账）·state.json。
  事件直方图 A18/B2/C1/E4/UNREC8＝33——与 v47 首战账（A19/UNREC8/E3/B2/C1）
  两时点漂移如实并记（§9 边界 7）。
- **集成面**（更新账.md:3927）：README.md v48 快照＋docs 清单登记＋DS4 三账
  baseline_diff 双向复跑 rc=0（集成席实跑）；run_tests 59/58/0 failing/1 SKIP
  钦令两遍·doc_lint consistent（帽 24 无溢出）。
- 边界如实承：K=3 单跑读数＝趋势级（§9 边界 1）·账名 audit-k3-20261112.json
  偏离 perf 命名律（四元组内嵌恒同·实测席已注记保持·更新账.md:3944·§9
  边界 6）；⑦执行路径现势＝步 1-3（retro-triage 零码/fixtures 小改/
  --dry-run）＝v49 面·步 4 真发候令·步 5 独立排程（更新账.md:3937·§8
  条 2 同源）。

### 6.x v1.0 §5 候令九条→六波收口对账（逐条注来源）

| # | v1.0 §5 pending execution | 六波落点 | 状态 |
|---|---|---|---|
| 1 | probe `--jobs`>1 真树实测 | v43 K=2 1.87×（更新账.md:3801）＋v48 K=3 三账齐（:3925） | **已闭** |
| 2 | pushci 真实 CI 端到端活跑 | ⑦勘形五步路径立·步 1-3＝v49 面·步 4 真发候令（勘形档 §五/:202-217·更新账.md:3937） | pending execution（§8 条 2） |
| 3 | unclog/wash_shape 真树 `--apply` 活跑 | 未跑（fixture 级全验维持）——任务书候令面四条外·如实留 §9 边界 5 | 未竟 |
| 4 | sentinel `--loop` 长驻真实消费 | v44 首演＋v47 首战＋v48 真部署（更新账.md:3820/:3895/:3942） | **已闭** |
| 5 | cure39 新式真树活跑 | 未跑·⑤⑥语料触发族同窗打包（§8 条 3） | pending execution |
| 6 | 9.1 编译器依赖面 | v43 ④close out（9.3 直替·:3800）＋v47 ⑧关闭（缺省探测·:3894） | **已闭** |
| 7 | ci_triage 独立长盯态 | 未做（pushci watch 内嵌版外仍无）·§9 边界 5 | 未竟 |
| 8 | header-map 模板库滚扩 | ⑤语料触发候令（roadmap-v43-plus:62·§8 条 3） | pending execution |
| 9 | 双门案 A 残余风险 | v46 评估档案乙同判旁证（保持双门＋文档分工·更新账.md:3867/:3884）——机械强制仍无·案 B 前置山未动 | 同判旁证·未闭 |

## §7 计数总表与现役能力全表增补

### 7.1 计数总表（三行·v42 基座→v48 current state·全部照录更新账各段与本席复核）

| 计数面 | v42 基座（v1.0 时点） | v43/v44（零码改） | v45 | v46 | v47 | v48 current state |
|---|---|---|---|---|---|---|
| cw.sh 入口工具 | 20 | 20 | 21 | 23 | 24 | **24** |
| run_tests.sh 例 | 56 | 56 | 56 | 58 | 59 | **59** |
| 过／failing／SKIP | 52/0/4 | 52/0/4 | 52/0/4 | 54/0/4 | 58/0/1 | **58/0/1** |

来源锚：v42/v43 基座二十工具与 56 例（更新账.md:3810）·v45 二十一路由
（:3845/:3853）·v46 二十三工具与 58/54/0/4（:3868）·v47 二十四工具与
59/58/0/1（:3897）·v48 current state 59/58/0/1 钦令两遍（:3927）。器数现势本席复核
＝cw.sh:247-270 case 分派实数二十四路由＋git show 统计 325b4dc 六文件无
cw.sh（v48 零新器·本席实跑）。

**任务书给形勘误登记**：任务书「23→24→25 器演进」末位与实取不符——实取
23（v46）→24（v47）→**24（v48 零新器）**；按实取为准如实登记（勘形档
§1.3 同律·v35-① 口径勘误判例同款）；「25」无在库锚点·不造账。

### 7.2 现役能力全表增补（第 21-24 器·接 §2 表 20 行后·三层/职能双维沿用 §2）

| # | 路由 | 目标脚本 | 三层 | 职能 | 入列 | 一行职责（缺省安全态） |
|---|---|---|---|---|---|---|
| 21 | `render-events` | `tools/render_events.py` | 服务层（v45） | close out（台账渲染） | v45 | 哨事件 JSONL→markdown 台账（`--events`/`--dir` 合并三维分布＋9 列表·坏行容错·`--json` summary·`--top` 截断） |
| 22 | `dispatch` | `tools/red_dispatch.py` | 服务层（v46） | 排障（红事件路由） | v46 | 红事件→动作预设路由（`--preset` 三档 report-only 缺省·`--state-file` 防重＋`--cooldown`·元字符守卫·全批零半派） |
| 23 | `audit` | `tools/registry_audit.py` | 服务层（v46） | 手术器（只读审计） | v46 | 注册册卫生审计四账（只读零写盘·`--fix-plan` 确定性处方·`--live-src` 拓扑对账） |
| 24 | `registry-fix` | `tools/registry_fix.py` | 服务层（v47） | 手术器（处方执行） | v47 | audit fix-plan 逐条落刀（dry run by default·`--apply` 后断言三判·任一炸逐字节回滚） |

双维速读增补（接 §2）：**close out**面添 render-events（台账渲染·接 doc-lint
收口槽）；**排障**面添 route（哨红→动作路由·接 sentinel 消费面）；
**手术器**链成三段＝union（v35 写手术·dry run by default）→audit（v46 只读诊断）→
registry-fix（v47 处方执行）——「诊断→处方→apply」闭环·落刀面缺省干跑＋
人审显式放行铁律三器同守。入口演化 20→21→23→24 与 §6 各波集成面行逐一
吻合（v48 零新器·现势即 24）。

## §8 候令面清单（v49+·四条·逐条注来源）

1. **registry_fix 真树 `--apply`**——`tools/registry_fix.py` 对 Set Live 双册
   12 重复块＋锚刷处方落刀（v46 真仓只读 demo 定病灶·更新账.md:3866；v47
   执行器 selftest 8/8 含逐字节回滚·:3896）；真树落刀涉多写者仓（曾栢源线/
   值守席活跃）·候用户令或协调台对表（更新账.md:3908/:3941）。首跑建议承
   §5 律：小面先行·断言三判＋回滚护栏在器。
2. **⑦步 4 真发（pushci push 事件路线）**——`tools/pushci.py` push 事件路线
   （refs/heads/main）＋`--watch-max-rounds` 安全阀＋heal 分派 Main cross-check against the reference·
   避 PR mirror-blind 面（勘形档 §五.4/:212-213·更新账.md:3937「步 4 真发
   pending execution」）；前置＝步 1-3（Main retro-triage 零码／pushci_scenarios 六场景
   Main 仓形 fixtures 小改／真仓 `--dry-run` 计划面零副作用）＝v49 面·且须
   先物化 Main 本地 checkout（勘形档 §五.3/:210-211）；凭据面已实证（netrc
   push_perm=True·勘形档 §1.1/:20）·Main 分支保护面真发前补探
   （勘形档 §五.6/:217）。
3. **⑤⑥语料触发**——⑤ wash_shape header-map 模板库滚扩＋⑥ cure_pack v1.5
   （记号重绑第二件复现转正）＋v1.0 §5 条 5 cure39 真树活跑同窗：金标禁强凑·
   「没语料就不做」是设计而非搁置（docs/roadmap-v43-plus-20261111.md:62/:72/
   :117/:131·更新账.md:3878/:3907/:3936）——窗口随②哨长驻真部署现役态
   （§6 波十三）。
4. **t_quad8 四仓回卷**——t_quad8_check 恢复条件＝四仓副本群（CANON_W1
   S系Prop清除战役工单目录）回卷·候桌面整理审删裁决（更新账.md:3914）；
   SKIP 1 例系缺卷族非器红·与门控无关如实留账（更新账.md:3897）。

## §9 诚实边界（逐条注来源·v2.0 新增）

1. **K3 单跑读数＝趋势级**——K=3 真跑未复跑采样·噪声带未发（examples/
   baselines/perf-README.md §3 判读律 1「单跑不下结论」:54）·负边际判读
   （K3 较 K2 慢 1.62×·K=2 档位即拐点）系单跑趋势级结论非定谳
   （更新账.md:3943·docs/perf-profile-v1.0-20261111.md:172「单跑读数·律 1
   噪声带未复跑采样＝趋势级」）。
2. **哨事件判类 UNRECOGNIZED 8 事件待人工复核**——v47 真仓首战 33 事件中
   UNREC8（更新账.md:3895）·判类谱「不充谱」设计内诚实：Main 步名零命中面
   （gate1/gate3 形）归 UNRECOGNIZED fallback·响亮不误断·人工指认优先
   （tools/ci_triage.py:22-23 判类谱注记·勘形档 §3.1/:101-102/:108-109）；
   v44 首演 UNREC×2 同律（更新账.md:3822）。
3. **翻绿是「现役世界代际」passing·非 9.1 复绿**——v43 ④close out/v47 ⑧关闭同口径
   诚实记界（更新账.md:3800/:3894·roadmap-v43-plus:58）；9.1 复绿候捐体
   复原（`tools/toolchain_dyld_doctor.py` `--donor` 溯源规程在库·禁代执行
   只出建议）。
4. **pushci PR 路线 mirror-blind＝中改最大缺口**——PR run head_sha=merge
   commit 必失配＋refs/pull/* 不入镜像＋push allowlist [main] topic 零触发
   （勘形档 §3.2/:122-133·§四表#8/:195）；器改 watch 语义或立规程双轨·
   均未做（如实）。unclog Main Live 正本不可用＝另一中改（无本地 checkout＋
   Live 世界无 CI 产线＋候选面须新采样＋基线域同名冲突断代·勘形档
   §3.3/:151-164）。
5. **v1.0 §5 pending execution 3/7 未竟**——unclog/wash_shape 真树落刀活跑与 ci_triage
   独立长盯态六波未触（§6.x 对账表）·任务书候令面四条外·如实留账不冒闭。
6. **账名偏离注记**——examples/baselines/audit-k3-20261112.json 偏离
   perf-README §2 命名律本名形（perf-<域>-k3-*.json）·四元组内嵌恒同·
   baseline_diff 双向实测无误配·实测席注记保持（更新账.md:3944·
   perf-profile:174）。
7. **判类直方图两时点漂移**——v47 首战账（更新账.md:3895）A19/UNREC8/E3/
   B2/C1 vs v48 部署活体（本席本 ask 实读 _log/sentinel_v48/events.jsonl）
   A18/B2/C1/E4/UNREC8：总红 33 恒定·A/E 各漂 1 件＝CI 历史窗滚动自然漂移
   （上传红＋coqchk skipped 的 E 族签名随窗形成）·两观测均真值·如实并记
   不作修账。
8. **勘形未探面**——Main 分支保护面／API rate-limit 现值／scripts/
   parallel_chk.sh 内容／pushci runs 面分页现患（低频轮换下非现患）均未探
   （勘形档 §六.2/:226-227）；「积分静默窗」库内在册锚点零命中如实承
   （roadmap-v43-plus:13）。
9. **v46 评估文档双份并存**——先席案 ABC（push-gate-dual-door-assessment-
   v1.0）＋v46 对照表（评估-push_gate推窗四判据与pushcinormalize）同判旁证·
   不合并留档（更新账.md:3884）。

---

——本席交稿自证：本文件写成后经 `bash /Users/apple/Desktop/ConstructiveWorld/
cpu_guard.sh -MaxWaitSec 120` 包裹复跑 `python3 tools/doc_lint.py --repo
/Users/apple/Desktop/rocqwash`·verdict consistent rc=0（含本文旗标引用零漂）
——实测记录见交割 notes。
