# rocqwash — Coq/Rocq Constructive Proof Unblocking Engine

**rocqwash** is a mechanical diagnosis, washing, verification, and certification toolchain for Coq/Rocq constructive mathematics projects. It is designed to **naturally surpass LLM/probabilistic approaches** in proof-unblocking: every diagnostic is a type-theoretic structural property, every fix is idempotent and replayable, every verification is independently reproducible.

> **Core Principle**: 凡可用类型论结构性判据机检的，一律不交给概率模型猜。
> (What can be mechanically verified via type-theoretic structural criteria shall never be delegated to probabilistic models.)

## Architecture: Three Chains in One

```
Toolchain (scripts + templates + canonical recipes)
    ↓
Logic Chain (criteria + gates + calibration standards)
    ↓
Derivation Chain (input → wash → verify → land → certify → push)
```

## Components

| Module | Purpose | LLM Surpass |
|--------|---------|-------------|
| `scan/` | Prop leakage scanner (5 frozen lanes + 3 negative-capture lanes) | Exact to line; LLM cannot guarantee exhaustive |
| `names/` | Statement-name ordinal list extractor + N=N assertion | LLM cannot guarantee ordinal counting |
| `wash/` | Canonical 7-step wash engine (exact-string + count==1 + idempotent) | LLM-generated tactics not idempotently replayable |
| `verify/` | R4 three-source (bare magic=0 + probe dual-face + five-pattern grep) | LLM cannot enumerate full closure |
| `seam/` | Generation-gap seam probe (W13 four-mechanism auto-classification) | Mechanical supply-signature Check vs LLM guess |
| `certify/` | Two-tier freeze system + push-window four-criteria + UNION v2 | LLM cannot replace deterministic process |
| `watch/` | CI monitoring + pin-IP push + thermal guard | Deterministic workflow vs LLM instability |
| `tools/` | cpu_guard.sh thermal wrapper + shared utilities | Hardware-aware process control |
| `wrapper/` | Adapter layers for frozen / out-of-repo pieces: `coqc_shim.sh` + `gate7_probe.sh` (gate7 probe chain → local `rocq c`, guard-wrapped launcher) + `guard.sh` + `scan_station.py` | Canonical argv/env adaptation; criteria stay solely with the original tools |
| `scan/scan_v4_token.py` | Token-level qualified-identifier census (bare vs dotted constructor references, binder-aware) — closes the mixed-line masking blind spot of line-level filters | Token census is exhaustive at token granularity; line-level `grep -v` drops lines that carry both forms |
| `wash/cure_pack.json` + `wash/cure_applier.py` | Consumer-cure canonical pack: twenty-four deterministic idempotent rewrite patterns — the legacy five (bridge-wrapped rewrite, goal-opening downshift, opaque-reflexivity cure, qualified successor form, NatLe supply bridge), nine v1.1 statement-face patterns from the 20261103 wash-campaign field report (Qle/Qlt carrier-face downshifts in token and %-scoped notation forms, refl bridge opener, Import-shadow direct-face qualification as two exclusive variants with fail-loud conflict detection, NatLe premise lift + intros-tail-guarded drop wrap), five v1.2 S07-lineage adaptation patterns from the W66 field report (parameterized-shell drop with a :=-binding-right guard, notation rebind line-insertion, @field projection-bridge bare form, predicate-face convergence token map whose targets must be the consuming supply lemma's conclusion constant names, and a report-only binder-shell station for the manual binder surgery), and five v1.3 patterns for the CI #178 extraction-defect families (E3 generic-interface instantiation: abstract-carrier application stations rewritten to a concrete-carrier specialization shim generated after the last import; E2 record polymorphic field: the un-annotated field-consumption Definition restated as an explicit-type-annotated middleware with downstream arity adaptation and a report-only sweep-completion station), applied by a face/proof-scoped regex engine with per-face token guards plus a line-insert and a station-report engine | Exact trigger + template + second-run-zero-change assertion; LLM-generated rewrites are not idempotently replayable |
| `scan/dual_scan.py` | Dual-scanner cross-check driver: runs scan_v4_token + mac_stmt_scan over the same candidate files and reports per-file station counts plus a diff (only_v4 / only_stmt / common) — turns shared scanner blindness (application/type-face red causes) into a mechanical fact per file instead of a silent assumption | Both scanners' exit codes and station line-sets are mechanical; scanner consensus is reported, never blessed as completeness |
| `verify/erasure_classifier.py` | Extraction-erasure station classifier: six clusters with disposition suggestions, CAPTURE cross-check, markdown adjudication ledger | Deterministic pattern rules over extraction artifacts; advisory output for human adjudication, never a verdict |
| `wash/probe_engine.py` | Batch closure-compatibility probe engine: candidates TSV × world dir → per-file `rocq c` under cpu_guard → rc triage (WASHABLE / BORN-CLEAN / red-cause classes incl. MISSING_LIB) → idempotent ledger JSON | Real exit codes + red-cause regex classification are mechanical; LLM guesses at closure compatibility |
| `tools/chain_graph.py` | Multi-ledger merger → missing-lib chain-root graph (dependents count + root self-washability) → TOP ranking markdown + JSON | Union/override merge and dependents counting are deterministic; LLM loses track across ledgers |
| `wash/comment_pack.json` + `wash/comment_sweep.py` | Comment-domain sweep sidecar (does not impersonate a statement-face pattern): nested-comment-and-string-aware state machine, comment-domain flag-word exchange (review-bias word → neutral English term), data-driven leading-header replacement with a five-field shape spec; every application mechanically asserts the code-line-equality projection (comment-strip per the w7 criterion) and second-run zero-change | Comment-domain-only edits are provable by the code-strip projection; LLM edits leak into code silently |
| `tools/ledger_sync.py` | Probe-ledger × status-ledger TSV sync: E1 dedup / E3 ghost / MD5-drift / NO-MD5 / generation-divergence findings (v2.1: recognizes the freeze-ledger `items` subkey shell and filters bare-dict metadata keys loudly; divergence-carrying records are surfaced per-entry with an idempotent row note, never silently dropped) / loud column validation → new TSV, idempotent | Fail-loud bookkeeping with deterministic row upgrades; LLM silently drops or duplicates rows |
| `tools/pushci.py` | Push-CI one-shot pipeline orchestrator: five stages — preflight emission gate (dyld doctor verdict + net-probe stable window + optional gate4 comment pre-scan; the no-emission-on-single-probe discipline is codified here), push (retry ×3 + ghproxy re-route for https://github.com/ remotes; pushed_sha = ls-remote remote tip), CI watch (status-only polling — a frozen updated_at is not a zombie verdict), heal (ci_triage family dispatch: NETRED/coqchk-skipped → stable-window → rerun, capped; content-red is never auto-fixed; off-table families are never auto-rerun), verdict ± PR merge — seven-state verdict (`success|fix-content|toolchain|unstable|heal-exhausted|gate4-block|dry-run`), exit codes 0/1/2/9; orchestrates the v35 four tools via subprocess, zero new engines; fully offline-injectable (`--injector`/`--git-caller`/`--sleep-scale`) | Deterministic state machine over mechanical gates; LLM cannot be trusted to decide emission windows or auto-heal policies |

## Repository Layout / 目录结构

```
rocqwash/
├── cli/rocqwash          # 统一 CLI 入口 — unified CLI entry (scan/names/wash/verify/seam/certify/watch)
├── docs/
│   ├── zh/architecture.md  # 架构文档（中文）— architecture doc (Chinese)
│   └── en/architecture.md  # 架构文档（英文镜像）— architecture doc (English mirror)
├── CONTRIBUTING.md       # 贡献指南（流程/代码规范/测试要求/cpu_guard 使用说明）
├── examples/             # 全链演示样例 + Makefile — single-file full-chain demo (scan→names→N=N→wash→verify)
├── scan/  names/         # 已实现通用逐件工具（mac_stmt_scan.py / scan_v4_token.py / dual_scan.py）— implemented generic tools
├── tools/                # cpu_guard.sh 温控包裹 + 战役工装 — thermal guard + campaign tools
├── wrapper/              # 适配层族（gate7 探针链 shim/启动器＋cpu_guard 直通＋scan 指认包装）— adapter layers (gate7 shim/probe, guard pass-through, scan station)
├── wash/                 # wash_engine.py 通用逐件洗引擎 + probe_engine.py 批量闭包探针 + 治愈包/战役批洗 — generic wash engine + batch probe engine + cure pack + campaign tools
├── verify/               # verify_vo.py 绿判四件套 + 战役验证工装 — four-pack green verdict + campaign verify tools
├── seam/                 # seam_probe.py W13 四机制指纹探针 — W13 four-mechanism fingerprint probe
├── certify/              # freeze_manifest.py 两层冻结 + push_gate.py 推窗四判据/UNION v2 + frozen8.py 八件冻结名单 — two-tier freeze + push-window gate + UNION v2 + frozen-eight registry
├── watch/                # watch.py CI 监控/钉 IP 推送/ls-remote 确证 — CI monitoring / pin-IP push / ls-remote confirm
├── tests/  workflows/    # 自测套件（56 例）/ CI 工作流占位 — test suite (56 cases) / CI placeholder
└── README.md  LICENSE  .gitignore
```

> 状态快照 2026-11-01（巡检打磨席 rqsup4）：`scan/`、`names/`、`tools/cpu_guard.sh`、
> `cli/`、`examples/`、`docs/`、`tests/`（34 例自测套件）已实现并实测；`wash/`
> （`wash_engine.py` 台账洗引擎＋`_abl1_wash.py` 战役件＋`world_hook.py` 世界基校验钩子·
> 五课①）、`verify/`（`verify_vo.py` 绿判四件套＋战役工装＋`verify_gate6.py` gate6 薄包装·
> 五课③）、`seam/`（`seam_probe.py` W13 四机制指纹探针）、`certify/`（`freeze_manifest.py`
> 两层冻结清单＋`push_gate.py` 推窗四判据/UNION v2 深件·席 rqwash2＋`frozen8.py`
> 八件冻结名单机检）、`watch/`
> （`watch.py` CI 监控/钉 IP 推送/ls-remote 确证·零 dispatch 结构保证）、`tools/`
> （`select_audit.py` 选件审计器·五课②）、`recipes/`（`S07_projection_reanchor_E5.md`
> 五课④＋`ENBIG7_same_domain_collision_PW1.md` 五课③·判例处方件双件）、`wrapper/`
> （适配层族：gate7 探针链 `coqc_shim.sh`＋`gate7_probe.sh`·cpu_guard 直通
> `guard.sh`·scan 指认包装 `scan_station.py`·席 rqadapt·三判例验收站
> `precedent_station.py`·五课⑤ rqsup4）已落地；
> `verify/` 统一入口已收口（显式子动词分派 `cli/rocqwash verify gate4|verify_vo|verify_gate6|retrofit`·
> rqadapt 落三子动词 2026-10-31·rqsup4 四巡补 verify_gate6 20261101）；`certify/`
> 同款显式分派 `cli/rocqwash certify freeze|push_gate|frozen8`（rqsup4 五巡补
> frozen8 20261101）——冻结件零改动；R4 提取侧三源为待办。
> v30 增补（20261103·探测战役工具化轮）：`wash/probe_engine.py` 批量闭包相容
> 探针引擎＋`tools/chain_graph.py` 多账合并链根图＋`tools/ledger_sync.py`
> probe×状态台账同步器（E1 去重/E3 幽灵/列校验 fail-loud）——承 W13/W25/台账
> v2 三原型 1:1 泛化，全路径参数化零硬编码；自测套件扩至 40 例全绿。
> v31 增补（20261103·洗形战役实战判例工具化轮）：`wash/cure_pack.json` v1.1
> 五式→十四式（Qle/Qlt 载体面降移两形·refl 桥开门·Import 遮蔽直通面双变体
> exclusive-group fail-loud·NatLe 前提提升＋intros-tail 守卫 drop 包裹）＋
> `wash/cure_applier.py` face-regex 域引擎（face/proof 域触发·逐面 token 守卫·
> 文件级前置条件）＋`wash/comment_pack.json`＋`comment_sweep.py` 注释域 sweep
> 旁车（嵌套注释+字符串感知状态机·旗词换形·数据驱动头注换代·w7 code 行全等
> 投影幂等断言）＋`tools/ledger_sync.py` v2.1（items 子键壳识别＋裸 dict 元数据
> 键响亮滤除＋GEN-DIVERGENCE 双代分歧出账——分歧优先序成文：kept 代＝下游账
> basis 榜系消费代，dropped 代只注记不弃账）；自测套件扩至 41 例全绿。
> v32 增补（20261103·S07 世系适配式工具化轮·W66 支撑席提案实装）：
> `wash/cure_pack.json` v1.1→v1.2 十四式→十九式（cure32_A 参数化壳去除·
> :=-binding-right 守卫／cure32_B 记号重绑 line-insert 引擎／cure32_C 投影桥
> 裸名形 face+proof 域／谓词面收敛 token_map——换名目标须取消费供给引理结论面
> 同一常量名·delta 等价异名编译绿而提取插 Obj.magic／binder 壳 report-only
> 站型——手刀辖区报站·术后站数归零）＋`scan/dual_scan.py` 双器对拍驱动
> （scan_v4＋mac_stmt_scan 双扫×逐件差异报告 only_v4/only_stmt）＋cure_applier
> 器修（exclusive-group 冲突＋--json 路径 report 落盘·rc=4 文档值）；
> 自测套件扩至 42 例全绿（门控 S07 编译弧：红→机械 cure→binder 手术→绿→
> 提取 Obj.magic 0/0）。
> v34 增补（20261104·CI #178 提取面缺陷族逆向修订轮）：`wash/cure_pack.json`
> v1.2→v1.3 十九式→二十四式——工单定谳两类缺陷族入 cure：E3 泛型接口实例化
> （cure34_E3_use_station_spec 抽象载体应用站改写特化 shim 调用＋cure34_E3_spec_shim
> line-insert 末个 Import 后生成具体载体中间 Definition；shim 体保留被特化的抽象
> 应用、face_exclude 护体防二遍自缠）＋E2 记录多态字段（cure34_E2_field_annot
> 无标注消费面重述为显式类型标注中间 Definition＋cure34_E2_use_arity 下游元数
> 站随行＋cure34_E2_station_unannot report-only 清账站）——五式全复用 v32 引擎
> 零新引擎；门控 E2/E3 编译弧第一手：pre-fix 编译绿（提取时缺陷族）、修后绿、
> E2 消费面 `'a1 -> 'a1`→`nat -> nat`、消费单元 magic 0/0、world 访问器债=1
> 机械钉（实体修复工作流域·canonical_note 记界）。自测套件 43 例。
> v36 增补（20261111·推送 CI 一键流水线轮）：`tools/pushci.py` 修复后推送 CI
> 一键流水线编排器——五段管线：preflight 发射闸（dyld doctor verdict＋net-probe
> 稳窗双闸·可选 gate4 头注预扫·禁发射律代码化）→push（重试 3 发×45s＋
> https://github.com/ 形 ghproxy 换路·pushed_sha=ls-remote 远端 tip）→watch
> （status-only 口径轮询·updated_at 冻结非僵尸判据）→heal（ci_triage family
> 分派：B/E 族→稳窗过→rerun·帽 --max-heal 3·A 内容红禁代修·C toolchain 停·
> 表外族禁自动 rerun 人工指认）→verdict±merge（七态 success/fix-content/
> toolchain/unstable/heal-exhausted/gate4-block/dry-run·退出码 0/1/2/9）——
> v35 四器（doctor/net-probe/triage/union）subprocess 编排零新引擎；离线可测
> 注入内建（--injector/--git-caller/--sleep-scale·零真网络零真 push）；自测
> 套件扩至 48 例。
> v37 增补（20261111·实时动态三器轮·用户令：配合工作流实时动态提供清洗、洗形、
> 排障、疏通堵塞）：`tools/cw_sentinel.py` 实时动态哨（三路信号源 CI runs/台账
> 链根/buildlog 词面→JSONL 事件流·once/loop 双模·判类全权在 ci_triage·链根
> 全权在 chain_graph·零动作是缺省）＋`tools/wash_shape.py` 洗形器·正典形五洗
> 流水（词面/token/头注/行尾/锚五洗全 subprocess 编排既有引擎·plan 缺省零写盘·
> --apply 落刀后复跑五洗复核）＋`tools/unclog.py` 疏通堵塞闭环引擎（probe 归集
> →chain_graph 挑根→cure_applier 落刀→rescan/resprobe 复核→verdict
> unclogged/wall/rounds-exhausted·缺省干跑·frozen 在册红拒·诚实墙禁硬凑）——
> 三器共同接口纪律五条：JSON-in/JSON-out（--json report·schema 钦名
> rocqwash-sentinel/1·rocqwash-shape/1·rocqwash-unclog/1·sort_keys 字节恒同）·
> 退出码 0/1/2/9（红是数据非器红·响亮 stdout）·--once/--loop 双模（--interval
> 可调·JSONL 事件流 --events）·离线可测（--injector 子进程调用层罐装＋
> --sleep-scale·零真网络零真编译于 selftest）·编排而非重造（零新引擎）；
> `cw.sh` 入口扩至十五工具（sentinel/wash-shape/unclog 三路由·四处同步）·
> 工作流配合接口速查见 [README-cw.md](README-cw.md)「工作流配合接口」节；
> 自测套件扩至 51 例（47 过/4 例正本缺卷让席·真本机全跑）。
> v38 增补（20261111·工作流集成与综合体检轮·四席并铸＋集成席收口）：
> `tools/cw_doctor.py` 综合体检器·四域聚合（①环境＝toolchain_dyld_doctor 编排
> ②网络＝net_probe --rounds 1 ③注册册锚正典形审计 ④堵账＝probe_engine 真探
> ＋chain_graph 链根——逐域 subprocess 编排既有一器零新引擎→综合健康分 0-100
> ＋per-domain verdict＋advice 处置清单·schema rocqwash-cwdoctor/1·--injector
> 离线可测·只诊断禁代执行·红是数据非器红 healthy=0/degraded=1）；工作流集成
> 面：`examples/workflows/` 三嵌段正典样例（backend-sentinel 后台哨／step-pushci
> 单步推 CI／loop-unclog 堵账疏通·全部离线可注入形）＋
> `docs/workflow-integration-whitepaper-v1.0-20261111.md` 集成白皮书（主会话
> 让路模式／后台任务拓扑／推窗四判据×发射闸双门并立）；韧性层：共享退避纯函数
> `tools/_http_backoff.py`（CI GET 403/429/5xx 指数退避·Retry-After 尊重·
> ci_triage/cw_sentinel/pushci 三器接入）＋net_probe `--jitter/--seed` 抖散
> ＋pushci `--timeout`／sentinel `--subproc-timeout` 子进程防挂（injector
> canned 路径一律零重试零真网络）；接口扩面：sentinel `--on-red-preset`
> （unclog 干跑/pushci dry-run 预设动作·与 --on-red 互斥）＋unclog `--audit`
> 只读堵账基线（--src 全文件 md5 跑前跑后自证零写盘·verdict=audit exit 0）；
> `cw.sh` 入口扩至十六工具（cw-doctor 路由·四处同步）；自测套件扩至 52 例
> （t_cw_doctor 最小自测壳两判·缺壳集成席自补）。
> v39 增补（20261111·文档核与接驳实战轮·工装席四铸＋集成席收口）：
> `tools/doc_lint.py` 文档←→实现一致性三查器（①工具表查＝cw.sh 头注/usage/
> hint/case 四处互检＋tools/ 通用入口对账 ②计数查＝tests/run_tests.sh CASES
> vs tests/README.md vs README.md 三处对账 ③旗标查＝docs 引用旗标 vs 各器
> --help 实出逐枚对照（--help 真跑·帽 20 器）——schema rocqwash-doclint/1·
> verdict consistent|drift·红是数据非器红·--selftest tmp 迷你仓六矢量·
> 零网络零写盘）；接驳实战核：`tests/test_relay_e2e.py` cw_sentinel
> --on-red-preset unclog 全链三判 e2e（事件触发→--audit 干跑 rc=0 零写盘
> md5 自证→JSONL 同盘 unclog report 路径逐字节对拍·全 canned 罐装·实跑原文
> 落 docs/ops-realtime-service-v1.0-20261111.md 实时动态服务运行手册）；
> 洗形器扩容：wash_shape `--header-map-preset NAME` 钦名头注模板库
> `tests/fixtures/header_map_v1.json`（战役正典蒸馏·金标引据在册·schema
> rocqwash-header-map/1·与 --header-map 同槽互斥）＋cure_pack v1.4 语料普查
> 轮单式扩容：`cure39_ifq_connective_qualify` 接口量化连接词限定（20261111
> 证据门控普查·b48-52 wash-wave 引据 commit 9a51c74·RI0 语境件语句面裸
> lt/le/plus 钉 @S01_BaseRing 投影形·树正典形；普查纪律 held——引据较薄之形
> 全数留 pending 不铸·夹具 cure39_t13/cure39_plain）。`cw.sh` 入口扩至十七工具
> （doc-lint 路由·四处同步）；自测套件扩至 54 例（t_relay_e2e 三判 e2e＋
> t_doclint 最小自测壳三判·缺壳集成席自补）。
> v40 增补（20261111·正典化巩固波·四席并铸＋集成席收口）：`tools/baseline_diff.py`
> 堵账基线对比器（两份 unclog --audit 堵账基线 argv 序=旧→新→new_blocks/
> resolved_blocks/persistent 三清单＋score_delta·verdict improved/degraded/
> stable/incomparable·账面自洽预检拒手编基线·候选面四元组两账比对跨集如实拒判·
> timing 段不入对比＝基线唯一非确定段——schema rocqwash-baseline-diff/1·红是
> 数据非器红）＋`examples/baselines/` 堵账基线入仓规程（命名律
> audit-<域>-<yyyymmdd>.json·真树干跑产·timing 注记·工装席铸）；破坏面复核矩阵
> `tests/test_destructive_matrix.py` 17 行拒写判据一行一拒写（会写盘器×写面×护栏
> 锚 file:line：unclog×4/wash_shape×4/pushci×3/cw_sentinel×2/registry_union×2/
> cure_applier×2·全 tmp fixture＋injector 罐装零真网络零真仓零真编译·矩阵红＝
> 护栏破响亮列破口·破坏面席铸）；稳态三器扩容：cw_sentinel `--emit-max-bytes`
> JSONL 轮转（.1/.2 保留 2 代·seq 跨代续号）＋`--rebuild-state` 崩溃恢复
> （损坏 state 红拒 9 禁静默重建·显式重建唯一合法路）、unclog `--state-file`
> 同形哨态 seen 差分（red-new 事件 only-new·与 cw_sentinel state 同形互读写·
> --rounds/--loop 与 --audit/--state-file 两组互斥 rc=2·损坏红拒 9）、
> wash_shape --loop 事件流同形对齐（rocqwash-sentinel-event/1·seq 跨进程续号
> ＋ts=off 注记）＋plan 跨轮缓存（源件 md5 变→重算·恒同→hit 复用·plan_cache
> 响亮出账）（稳态席铸·selftest 十二/十三/十八矢量扩容）；`cw.sh` 入口扩至
> 二十工具（baseline-diff 路由·六处同步含 legal 两清单与计数行）；服务层总览
> [docs/service-layer-overview-v1.0-20261111.md](docs/service-layer-overview-v1.0-20261111.md)
> （三链一图全景＋器面索引·docs 席铸）；自测套件扩至 56 例
> （t_destructive_matrix 17 行判据＋t_baseline_diff 最小自测壳三判·缺壳集成席
> 自补）。
> 组件级细节见 [docs/zh/architecture.md](docs/zh/architecture.md) /
> [docs/en/architecture.md](docs/en/architecture.md)；贡献流程见
> [CONTRIBUTING.md](CONTRIBUTING.md)。

## Getting Started (5 minutes)

Prerequisites (three lines):

- `python3` ≥ 3.9 — no third-party packages required
- a Rocq/Coq 9.x toolchain on `PATH` — needed only for the compile-verification pieces; everything else runs without it
- Windows: use Git Bash as your shell (the toolchain is bash + python3)

```bash
git clone https://github.com/hy7pc8gfmf-dotcom/rocqwash.git
cd rocqwash
bash tests/run_tests.sh          # self-test suite; exit 0 = all green
```

First run — scan a demo source for statement-face Prop leakage:

```bash
python3 scan/mac_stmt_scan.py --file examples/demo_prop_leak.v
# RED stations: ['demo_eq_self', 'demo_eq_sym', 'demo_le_eq', 'demo_le_self', 'demo_mixed']
```

First verification — comment-hygiene gate on a clean sample:

```bash
python3 verify/gate4_comment_guard.py --file tests/fixtures/gate4_clean_sample.v
# [gate4ext] ... 件数=1  PASS=1  FAIL=0  REVIEW(人工复核)=0  UNREADABLE=0 ...
```

Token-level successor-qualification census (finds bare constructor references
that line-level filters miss):

```bash
python3 scan/scan_v4_token.py --file path/to/file.v --json census.json
```

## Platform Support

| Platform | Support | Notes |
|---|---|---|
| macOS | full | `tools/cpu_guard.sh` thermal gate uses `pmset` (macOS-only); queue/nice lanes are POSIX |
| Windows | Git Bash + python3 | light-load direct runs; bring your own thermal policy if needed (`cpu_guard.sh` thermal reading degrades gracefully without `pmset`) |
| Linux | same path as Windows | unverified by this project's CI — reported as-is, no claims |

## Quick Start

```bash
# Scan a .v file for Prop leakage — via the unified CLI entry
cli/rocqwash scan --file my_proof.v

# Extract statement names and assert N=N against baseline
cli/rocqwash names my_proof.v --names-out names.txt
cli/rocqwash names my_proof.v --compare my_proof_washed.v --expect 487

# Wash with an explicit exact-string ledger (idempotent, fail-loud, no guessing)
cli/rocqwash wash my_proof.v --patch wash_ledger.json --out my_proof_washed.v

# Green-verdict four-pack on a compiled pair (magic / freshness / exit / log)
cli/rocqwash verify verify_vo --v my_proof.v --vo my_proof.vo --rc 0 --log build.log

# W13 four-mechanism seam fingerprints (candidate list + prescriptions)
cli/rocqwash seam --file my_proof.v

# Two-tier freeze manifest (tier1 per-file md5 + tier2 manifest md5)
cli/rocqwash certify freeze freeze . --out manifest.json
cli/rocqwash certify freeze check . --manifest manifest.json

# Push-window four-criteria gate (judges the window, never pushes)
cli/rocqwash certify push_gate window --repo . --runs-json runs.json --suite tests/run_tests.sh

# UNION v2 multi-world manifest (per-world tier1/tier2 + union tier)
cli/rocqwash certify push_gate union-freeze --world wa=./world_a --world wb=./world_b --out union.json
cli/rocqwash certify push_gate union-check --manifest union.json

# CI in-flight monitoring (offline evidence mode; online read-only query also available)
python3 watch/watch.py ci --runs-json runs.json

# Pin-IP push wrapper (dry-run by default; masked output; --yes actually pushes)
python3 watch/watch.py push --repo . --remote origin --pin-ip 140.82.113.3 --url-host github.com

# Post-push ls-remote double-read confirmation
python3 watch/watch.py confirm --repo . --remote origin --branch main --sha <sha>

# Equivalent direct invocation
python3 scan/mac_stmt_scan.py --file my_proof.v
python3 names/mac_stmt_names.py my_proof.v --names-out names.txt

# Full-chain demo (scan → names → N=N → wash → verify)
make -C examples demo

# Compile with thermal guard
bash tools/cpu_guard.sh -Reg /tmp/my_reg -Front 0 -Mid 1 -- rocq c -native-compiler no -Q . "" my_proof.v
```

## Seven Canonical Steps (不可跳)

1. **cp source into sandbox** (write-isolation)
2. **Three-state triage** (true-wash / bridge-retain=exception-registry / UNCERTAIN=probe-first)
3. **Canonical face-mapping wash** (Qlt→QltT / Qle→QleT' / ==→QeqT / bare=→Id+id_cong / nat≤→NatLe)
4. **Compile verification** (RC=0 / magic 436f712100015ff4 / vo newer than v / PA Closed / coqchk Axioms:none)
5. **R4 three-source conjunction** (bare full-extraction magic=0 + probe dual-face magic=0 + five-pattern grep=0)
6. **gate7 English化 retrofit** (CJK→0 + five-field header 30-line cap)
7. **N=N name-table assertion** (mac_stmt_names.py ordinal full-equality) + freeze md5

Each step must pass before the next. Any failure = honest WIP, no green-washing.

## Four W13 Seam Mechanisms (Generation-Gap Auto-Classification)

1. **== statement rewrite/ring/reflexivity structurally unusable on QeqT(Id) goals** → flip back via qeq_imp_qeqT first
2. **Keyed-matching instantiation**: supply-side parameter must take the actual shape in the goal
3. **Premiss-carrying lemma consumption**: assert-化 + dual-shore bridge
4. **Cross-line Require topology leak**: statement-level multi-line awareness + driver idempotent resume

## LLM Integration

rocqwash is designed to **complement** LLM agents, not compete with them:

- **LLM excels at**: understanding "what does this math mean" (semantic layer)
- **rocqwash excels at**: ensuring "this proof is real" (mechanical layer)

**Collaboration pattern**: LLM understands → rocqwash diagnoses → LLM fixes → rocqwash verifies → LLM commits → rocqwash certifies.

## Why rocqwash Surpasses LLM/Probabilistic Approaches

| Capability | LLM | rocqwash |
|-----------|-----|----------|
| Prop leakage localization | LLM needs to read entire file and may miss lines | `mac_stmt_scan.py` pins to exact line in milliseconds |
| Missing dependency detection | LLM guesses Require chains | Require line-by-line scan + Set tree diff = mechanical exhaustive, zero omissions |
| Seam type classification | LLM reads error messages and guesses direction | W13 four-mechanism grep fingerprint → prescription mapping = mechanical, not experiential |
| Wash mapping | LLM generates tactics that may hallucinate | Canonical 7-form exact-string replacement + count==1 assertion = idempotent replayable |
| Compile verification | LLM trusts self-report | `world.run("rocq",...)` exit code = deterministic |
| R4 three-source | LLM may miss spots | bare full-closure extraction + probe dual-face + five-pattern grep = triple-source conjunction |
| N=N name-table | LLM may miscount | `mac_stmt_names.py` ordinal full-equality assertion = mechanical |
| UNION world integrity | LLM may skip dependency copies | Per-piece md5 manifest = mechanical leak-proof |

**Core barrier**: These capabilities are not "better prompts" — they are structural properties of Coq/Rocq type theory. QeqT-goal Qeq-rewrite impossibility is a corollary of Set/Prop type-theoretic mutual exclusion. No prompt engineering can override type theory.

## License

Apache 2.0
