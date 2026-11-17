# rocqwash v43+ 路线图（候选态·候令未排程）— 20261111

> **性质**：总档席产·候选池为裁决素材**非排程令**——逐条候主会话钦定后入波。
> **素材源**：更新账.md v34–v41 八节「边界与待办」（`更新账.md:3543`/`:3576`/`:3605`/`:3635`/`:3666`/`:3696`/`:3725`/`:3756`）＋在库规程四件（perf-README／ops-realtime 手册／push-gate 双门评估／workflow 白皮书）。
> **口径**：rocqwash v41 `c5df4d4`·工作树净·禁 git commit（主会话统一提交）·本席只写本档一文件零撞车（cw.sh／tests 总套／README 系列归集成席）。

---

## 一、真实约束（四条·逐条锚）

1. **8GB Air 温控**：一切执行经 `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh` 包裹铁律；probe 侧温控警示已入器（`wash/probe_engine.py:49`「K>1 时机内多 rocqworker 并发＝热负载↑」·`:507` ADVISE 行·`:478` 同给建议 K≤2）；采样帽 ≤30 件温控窗规程已立（`examples/baselines/perf-README.md:60-68`·`:113` keep K≤2 unless 用户自裁）。
2. **单 runner**：套件口径「CI runner 无本机正本」已入注（`tests/run_tests.sh:146`）；双门评估档确认「现状双门并立＋正典串行序已是单 runner 约束下的最优解」（`docs/push-gate-dual-door-assessment-v1.0-20261111.md:209`）。
3. **积分静默窗**：任务书给定约束。库内在册锚点**零命中**（本席 20261111 全库 grep「积分／静默窗／quota」实跑无果·如实记）——排程面含义：CI 活跑类候选（②⑦的真发段）须避窗错峰，观测类候选（②哨长驻）静默期零事件亦属合法观测非器红。
4. **金标纪律**：evidence-gated 先例＝11 候选收 1 拒 10 逐条因（`更新账.md:3680`/`:3689`「宁缺毋滥代码化」）；never-synthesized 由代码执行（wash_shape header-map 缺 evidence 拒载·`tools/wash_shape.py:151-152` 探测次序与 plan-miss 如实）；金标修前形态不可全考面已立诚实记界先例（`更新账.md:3546`）。

---

## 二、候选池（8 条·编号承任务书·每条四列＋验证方式）

### ① probe --jobs>1 真树实测（温控窗规程已立）

**溯源**：`更新账.md:3758`（v41 待办 1「温控窗候令·canned 机制实证已毕」）。

| 价值 | 依赖 | 成本 | 风险 |
|---|---|---|---|
| 填实 `docs/perf-profile-v1.0-20261111.md:19/:125` DS4 唯一「待补」占位——并行墙钟剖面从方法占位转实测；v41 并行波收口最后一缺 | 规程全备：`--probe-parallel`（tools/unclog.py:373 透传 probe_engine `--jobs`）＋真编译经 `--rocq-cmd` 模板已实证可跑（v41 第三发 27/27·`更新账.md:3753`）→**不硬依赖④**；温控窗规程（perf-README §4） | 低-中：同候选面 K=1/2/3 各一跑（K=1 已有 190.7s 量级参照·`perf-profile:47`）＋账面补表 | 温控（K>1 热负载——器内警示注记不强制·用户自裁）；单 runner 挤压嫌疑注记；**加速不显著或负加速→如实录**（DS4 纪律：禁编数字） |

**验证方式（怎么算做完）**：同候选面（`examples/baselines/audit-ConstructiveWorld_Live-20261111.json` 27 件）K=1/2/3 三账齐、timing 段 jobs 维度在账、全程 cpu_guard 包裹留痕；DS4 表三行「待补」→实数（含负结论如实）；三账经 baseline_diff 口径确认 candidates 集恒同＝可比。

### ② sentinel --loop 长驻首战（真实战役消费）

**溯源**：`更新账.md:3638`（v37 待办 2「--loop 真后台候首个真实消费场景」）。

| 价值 | 依赖 | 成本 | 风险 |
|---|---|---|---|
| 哨从夹具级全验转真实战场——三路信号源（CI 红炉/本地堵账/构建日志）首次真消费；v41 新三预设（wash-shape/triage/cw-doctor·链式 `--on-red-preset`）得实战检验 | 真实战役窗口（下波战役即验证·`更新账.md:3638`）；工作流嵌段与 ops 手册标准命令已备（`examples/workflows/backend-sentinel.md`＋ops 手册 §2） | **低（零新码）**——纯运行面：后台 bash 任务挂 `--loop`＋`--emit` JSONL 流 | 长驻进程与主会话让路（白皮书五机制已备）；静默窗内信号稀疏＝零事件合法观测；旁路动作只干跑（unclog 干跑缺省铁律·`更新账.md:3650`）不会真落刀 |

**验证方式**：真实战役期间 `tools/cw_sentinel.py --loop` 挂哨→`--emit` JSONL ≥1 真实事件（kind/family/action 字段齐全）→`--state-file` 二跑幂等零重复事件→战报引用事件计数＋消费端 grep/python3 样例实跑对账。

### ③ on-red→unclog 全自动接驳评估（干跑自动→人审 apply 守门设计）

**溯源**：`更新账.md:3639`（v37 待办 3 前半）；v38 已落预设＋干跑铁律、v39 relay e2e 已测（`tests/test_relay_e2e.py`）——本候选是接驳链最后一环的**自动化边界评估**。

| 价值 | 依赖 | 成本 | 风险 |
|---|---|---|---|
| 「哨红→unclog dry run→人审 `--apply`」现有人工缝隙的守门设计成档——服务化安全自动化的裁决素材；双门评估档方法论（案 A 并立四理由·`docs/push-gate-dual-door-assessment-v1.0:128/:192`）的产品化复用 | ②首战真实事件语料（评估需真实触发样本）；既约口径不可单方面放宽：`--apply` 缺省关＋白名单人审（ops 手册 §3 规程 `:174`/`:228`「零动作是缺省」`:12`） | 低（评估档·**零动码为缺省**——若结论要动码另排波） | 全自动 apply 诱惑＝本候选最大风险（gold-standard/冻结面）——守门设计必须保持干跑自动、落刀人审；评估若建议放宽即违既约裁决（v38 互斥裁决＋v40 真缺口修复后的护栏面） |

**验证方式**：评估档落 docs/（现状→案选项→建议案＋理由＋残余风险如实·案 A 体例）；纯评估案＝doc_lint drift=0 保持＋档内命令块 bash -n 全过；若含动码建议＝destructive matrix 增判＋relay e2e 扩矢量＋三闸不动红。

### ④ 9.1 工具链依赖面决（ROCWASH_ROCQ 指 9.3 或复原捐体——门控编译弧 SKIP 四例翻绿）

**溯源**：`更新账.md:3579`（v35 待办 2）＋`:3537`（通路勘误：`ROCWASH_ROCQ` 须指 rocq 多路器非 shim）。

**现势实考（本席 20261111）**：惯指路径 `/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live/bin/rocq` 实测 **No such file or directory**（v35 所记 MISSING 现势仍在）；9.3 多路器在卷实证 `/Users/apple/Desktop/mac93_install_work/opam93/rocq93/bin/rocq`（find 命中）。

| 价值 | 依赖 | 成本 | 风险 |
|---|---|---|---|
| **门控编译弧总开关**：四处闸位翻绿——`tests/test_cure_pack.py:492`（compile check 段·`:718` SKIP 行）＋`tests/test_probe_engine.py:259-261`（真 rocq 节）＋`tests/run_tests.sh:438/:451` 两总套例；cure 新式真树活跑（`更新账.md:3699`）与⑥的验证基建 | 二选一路径已可考：A＝指 9.3（`mac93_install_work/opam93/rocq93/bin/rocq`·v41 第三发同源已实证 9.3 模板可跑绿）或 B＝复原捐体（toolchain_dyld_doctor `--donor` 溯源规程在库·**禁代执行只出建议**）；cw_paths 移根监察表在册（`更新账.md:3580`） | 低（A＝一次决断＋惯例路径落档口径；B＝中·真拷贝复原动作） | 9.3 与 9.1 代差语义——翻绿是「现役世界代际」passing·非 9.1 复绿（`更新账.md:3753` 同口径·诚实记界）；复原捐体若再 MISSING→doctor 诊断规程兜底；勿与正本缺卷 SKIP 族混淆（run_tests.sh:320/:347/:361/:379 系 CANON 门·另族） |

**验证方式**：决断落档后——`ROCWASH_ROCQ=<决断路径>` 下 `python3 -B tests/test_cure_pack.py` 与 `python3 -B tests/test_probe_engine.py` 实跑 rc=0 且输出**无「SKIP（ROCWASH_ROCQ unset）」段**（四处闸位编译弧全跑）＋全套 56/52/0 红基线不动红＋决断路径与勘误口径合（多路器形）。

### ⑤ wash_shape header-map 模板库滚扩（随战役语料）

**溯源**：`更新账.md:3639`（v37 待办 3 后半）；v39 已落 v1（campaign_set_diamond 五字段·缺 evidence 拒载由代码执行）。

| 价值 | 依赖 | 成本 | 风险 |
|---|---|---|---|
| 头注形洗覆盖面随真实战役语料扩张——新正典形新 preset；never-synthesized 纪律的持续兑现面 | **战役语料**（金标纪律禁预造：无 evidence 不铸·`tools/wash_shape.py:151-152` 拒载 rc2）；②战役窗口产出 | 低（语料到手后蒸馏→`tests/fixtures/` 模板库增库→selftest 增矢量） | curated 面误卷（五字段齐件不机械改写防护已在库·v39 账）；模板代际过期（旧 preset 与新战役形漂移——滚扩时逐占位引据复核） |

**验证方式**：新 preset 经 `--header-map-preset` 装载→渲染→`--apply` 端到端 partial→shaped→幂等复跑；「缺 evidence 拒载」负例 rc2 实跑；真仓面只读验证零写盘；「身内容绝不合成」逐占位引据在册。

### ⑥ cure_pack v1.5（记号重绑变体候第二件复现转正）

**溯源**：`更新账.md:3680`（v39 拒 10 条中「记号重绑候二件复现」候勘）＋`:3699`（v39 待办 2 cure39 新式真树活跑候令）。

**现势实考（本席实读）**：`wash/cure_pack.json` version=**1.4.0**·patterns=**25 式**（含 `cure32_B_notation_rebind` 记号重绑在库先例）。

| 价值 | 依赖 | 成本 | 风险 |
|---|---|---|---|
| 25 式→26+ 式 evidence-gated 扩容；记号重绑族第二件复现转正——gold-standard「宁缺毋滥」正面兑现；v39 待办 2（cure39 真树活跑）可同窗补 | 真实战役第二件复现实例（引据＝真实 diff 逐字·禁合成）；**④门控编译弧**（cure 新式的编译验证）；战役窗口 | 中（工单定谳→face-regex 新式→fixtures→门控弧——v34/v39 先例流程齐） | 语料不到则零扩容（**如实·非失败**——v39 单式扩容已立先例）；第二件复现是本候选成立前提，缺件即候勘不硬凑 |

**验证方式**：cure_applier `--selftest` 增矢量＋whole-pack 幂等 rc=0；门控编译弧 pre-fix passing→cure→cured passing→消费单元 magic 计数对账（依赖④）；拒录路径逐条因在册（若第二件终不复现）。

### ⑦ 多仓扩展（rocqwash 服务 Main repository CI 的适配面）

**溯源**：更新账**无直接待办条**——由 v36 pushci 编排面（`tools/pushci.py:26` remote URL 推导·host 须 github.com）＋registry_union 三面输入（`tools/registry_union.py:781-790` `--main`/`--branch`/`--git`）外推·任务书钦定入池（溯源性质如实记）。

| 价值 | 依赖 | 成本 | 风险 |
|---|---|---|---|
| rocqwash 从「自仓 CI 自服务」扩「服务 Main repository CI」——pushci/triage/doctor 三器适配面；服务层白皮书五纪律的跨仓检验 | 真远端凭据（**用户面**——v36 已记「真发段需真远端凭据·用户面」`更新账.md:3608`）；Main repository CI 形制勘察（runner/签名闸差异）；积分静默窗约束最紧的一条 | 中-高（形制勘察→canned 场景扩→真仓 `--dry-run`→真发；跨仓差异逐项对表） | 跨仓红线（Main 仓纪律与 rocqwash 纪律不一致面——适配器禁代仓越权写盘）；NETRED/凭据面；CI 形制不可预知（canned 覆盖有限→首跑 `--dry-run` 先行铁律·`更新账.md:3608`） |

**验证方式**：Main 仓形制勘察档→pushci_scenarios canned 场景扩仓形全过→真仓 `--dry-run` 计划面零副作用（HEAD/porcelain 前后恒同·v36 S6 判据）→真发首战 head_branch＋head_sha 咬合取得 run→ci_triage 判类对表。

### ⑧ sentinel JSONL→工作流 dashboard 直通（artifact 台账化）

**溯源**：v37 事件流在库（`tools/cw_sentinel.py` `--emit` JSONL append+fsync·`docs/workflow-integration-whitepaper-v1.0-20261111.md:35/:134`）＋v40 JSONL 轮转（`--emit-max-bytes` 保留 2 代·seq 跨代续号）外推·任务书钦定入池（溯源性质如实记）。

| 价值 | 依赖 | 成本 | 风险 |
|---|---|---|---|
| 哨事件流从「grep 使用」升「artifact 台账化」——事件＋轮转代际＋baseline_diff 堵账差分聚合一页；多战役横向对比面；后台任务可见性 | ②首战真实事件语料（消费面落地要真形）；**零新引擎纪律**（聚合器纯 stdlib 读 JSONL/JSON）；集成面（cw.sh 路由四处同步＋总套挂接）归集成席 | 中（新器一枚：schema＋sort_keys 确定性＋幂等字节恒同＋`tools/cw_sentinel.py` 同款 `--injector` canned 事件矢量＋集成面） | 事件 schema 演进（聚合器须 fail-loud 缺键红拒·禁静默容错）；轮转代际边界对账（seq 跨代不重号）；新器入 doc_lint 旗标对账面（十九→二十器的表查负担·集成席面） |

**验证方式**：聚合器 `--selftest` 矢量 rc=0＋canned 事件→台账页 sort_keys 落盘两跑字节恒同（幂等）＋真实 JSONL 样例（②产出）入账＋退出码 0/1/2/9 三码实考＋三闸不动红。

---

## 三、排序建议

**总序：④→①→②→③→⑧→⑦→⑤→⑥**

| 序 | 条 | 一句话理由 |
|---|---|---|
| 1 | ④ | **单点决断解锁最多下游**（⑥编译验证、cure 真树活跑、①口径统一）＋成本最低＋SKIP 四例翻绿是现役套件诚实面的直接补全；两条路径现势均已实考在卷 |
| 2 | ① | v41 待办直接收口·规程全备·不硬依赖④（`--rocq-cmd` 模板已实证）——短平快闭环 |
| 3 | ② | 战役窗口触发·零码——且它是③⑧⑤的**语料源**，窗口一到应最优先挂哨 |
| 4 | ③ | ②语料到手即可评估·零动码缺省·守门设计是服务化前提 |
| 5 | ⑧ | 服务化消费面·中成本·依赖②真实事件流 |
| 6 | ⑦ | 价值最大但依赖用户面凭据＋跨仓勘察·静默窗约束最紧·放后非弃 |
| 7-8 | ⑤⑥ | **语料触发型常备候选**——金标禁强凑：「没语料就不做」是设计而非搁置；窗口随② |

**分波建议**：
- **v43（近波·零战役依赖）**：④＋①（④先行半小时级决断，①温控窗内分批三跑）。
- **v44（战役波）**：②挂哨长驻→③接驳评估→（语料触发窗口：⑤⑥候勘转正与否如实定）。
- **服务化波（随需）**：⑧台账化→⑦多仓适配（凭据到位后）。

**依赖要点**：④是⑥与 cure 活跑的验证基建；②是③⑧⑤⑥的语料基建；③⑧⑦零战役依赖面可并行评估档先行。

---

## 四、本档边界（如实）

1. 本档为**候选态**非排程令——逐条候主会话钦定；⑤⑥为语料触发型，禁无据开工。
2. 三闸收口归集成席终跑：破坏面矩阵 17 判与全套 run_tests.sh **本席未跑**（如实记·非本席领地）；本席只就本档新件自证 doc_lint 一闸（§五·1）。
3. 「积分静默窗」库内无在册锚点（§一·3·实跑零命中）——按任务书给定承引，入波前如需精确窗口定义候主会话补充。
4. ⑦⑧溯源性质为「任务书钦定入池·账内无直接待办条」——与①②③④⑤⑥的账内待办直引不同源，已逐条标注。
5. push/commit 归主会话统一执行（本席零 git 写操作）。

---

## 五、本席自证字据（20261111 实跑·全部 cpu_guard 包裹）

1. **doc_lint 一闸**：本档写入后 `python3 -B tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash` 实跑→VERDICT 与退出码见当轮账（本席写作后即跑·drift 须=0 方合三闸基准——若本档旗标引用引入幻引即修档重跑）。
2. 六器 `--help` 旗标全集实跑（cw_sentinel/unclog/wash_shape/pushci/registry_union/probe_engine）——本档旗标引用逐枚对表非凭记忆。
3. `wash/cure_pack.json` 实读：version=1.4.0·patterns=25 式。
4. 工具链现势：9.1 惯指路径 MISSING（ls 实证）＋9.3 多路器 `mac93_install_work/opam93/rocq93/bin/rocq` 在卷（find 实证）。
5. 仓库现势：`git status --short` 空＋`git log -1` = `c5df4d4`（v41）——与任务书口径合。

---

## 六、Growth wiring annotation (RQW12 · 20261114)

Annotation only: no candidate rows added, removed, or reordered; the pool above is unchanged.

The five-engine seeds (E1 ai-flavor word map, E2 jargon map, E3 termbase, E4 i18n pipeline spec, E5 engines index; per the five-engine growth design volume 20261114) are landed on main at commit `9fa2bff` (RQW12, 2026-11-14): data + SPEC faces under `seeds/` (ai_flavor, jargon, termbase, i18n, engines) plus the seed selftest `tests/t_engines_seeds.py`; zero executable engine body, since the engines themselves grow on their own wash_shape / norm_lint / evolve faces in later waves. The seeds directory is the evolve candidate input face: the next growth cycle (RQW10 form) consumes `seeds/` as its feed. Selftest face: `python -I tests/t_engines_seeds.py` reports 5 segments / 42 checks, green, re-run first-hand in the repo layout on 2026-11-14. Honest boundary: `tests/run_tests.sh` does not wire the seeds selftest yet, so CI run 43555890998 (green at `9fa2bff`) did not execute it; suite wiring remains a follow-up candidate for the integration agent.
