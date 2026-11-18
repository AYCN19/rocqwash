# 判例档：R3 复发——route2-tierA 驱动同秒全灭·哨监控→classification→自愈全环零人工（20261113）

> **性质**：判例复发实录档·服务层闭环首例。记录 Set repository route2-tierA 分支
> run#301/302（sha `8f59c8f`）「相对路径 cwd=workdir 错位·驱动同秒全灭」判例
> 复发的活逮、classification、自愈全链字据，并附 Set PR#48（integration/g1-pipeline G1
> witness 8 件）勘形预热注记。**只读入档**——本席零代码改动·rocqwash 工作树
> 只增本档一文件；禁触冻结八件/quad8/更新账.md（对更新账只读引据）。
> **口径**：云上面 API 实取为准（api.github.com netrc 只读 GET·token 零回显·
> ci_triage 真跑实判）；「R3」编号承任务书/主会话判例册口径（在库可核机制面
> 见 §二·编号源不在本席可证面·§七如实记）。

---

## 一、案情总览（时间线·全部实取）

| 时刻（UTC 2026-11-12） | 事件 | 实取锚 |
|---|---|---|
| 04:25:53 | run#301（pull_request·sha `8f59c8f`·branch fix/route2-tierA-supply-20261112）创建→failure | runs API id=43154750085 |
| 04:26:07 | run#302（workflow_dispatch·同 sha 同分支）创建→failure | id=43154774367 |
| 04:27:34–04:29:11 | run#301 failing job（130971963665 mac 观察道）gate7 步红 97s→gate5/gate2 连带 | ci_triage 步表实判 |
| **04:38:12** | **哨活逮 run#301**：事件 seq 58·family=A-content-red·action=fix-content·classification=rocqwash-ci-triage/1（ci_triage 子进程 --offline） | `_log/sentinel_v48/events.jsonl` seq 58 |
| 04:44:10（+0800 12:44） | 同事自诊断落 restore `bd8f38b`「restore the two lane fixes lost in the rebase（gate7 tree absolutization＋seed pre-check fallthrough）」 | git show bd8f38b（Set repository） |
| 04:44:17 / 04:45:43 | run#303（pull_request）/run#304（workflow_dispatch）·sha `bd8f38b`·**双 success** | runs API id=43156738535/43156898674 |
| 16:57:12 | 哨补捞 run#302（seq 59·A-content-red 同族）＋watcher state 记 303/304 **success family=null**（绿零事件·幂等在册） | seq 59＋state.json seen_runs |

**全环零人工**：04:25:53 首红起算至 04:45:43 双绿 ≈ **20 分钟**；哨活逮（04:38）
至 restore apply（04:44）≈ **6 分钟**。监控（watcher）→classification（ci_triage）→automatic recovery（同事
会话依证据自诊断）→复绿（303/304）→哨记绿收环——全程无人工拍板介入＝**服务层
闭环首例**。

---

## 二、判例形与复发机理（R3「相对路径 cwd=workdir 错位·驱动同秒全灭」）

- **机理（自述面）**：restore `bd8f38b` commit message 逐字——coq.yml gate7 树
  参数须 `$GITHUB_WORKSPACE/ConstructiveWorld_Live` 绝对形，「relative path
  resolved under the gate7 workdir cwd → 544/544 instant driver failures, run
  43154774367」；即树参数以相对形 `ConstructiveWorld_Live` 在册，gate7 进入
  workdir（`_gate7_work_mac`）cwd 后相对解析错位落 workdir 下·驱动编译面
  `.vo` 树不可见→驱动件 line 2（Require 面）`Unable to locate library` 起头
  错（U 字面证据行实取·行帽截断）→**全数驱动瞬时全灭**。
- **在库机制判例面（同源机理·rocqwash 更新账只读引据）**：gate4 预扫铁则①
  「预扫必须自 Set 仓根用绝对路径跑（**cwd 错位伪绿判例**）——工具侧只对
  「树不存在」设防·对「错位 cwd 下相对路径解析到别棵在盘树」不设防＝伪绿机制面」
  （`更新账.md:2513-2515`）。同一「相对路径 cwd 错位」机理两个发作向：伪绿向
  （解析到别棵在盘树·判绿）与**本次红向**（解析到无 .vo 的 workdir·全灭）。
- **随件第二修复（同 commit）**：`scripts/ci_seed_mac93.sh` 无源种子面裸
  `exit 0` 短路 build 模式→空缓存 0.1s build 步→全部驱动灭（commit 自述
  run 43142078293·510/510 rc=1 形）——修复＝build 模式落入编译环。两文件
  47+/39-（git show --stat 实取）。

## 三、哨活逮与判类实录（本席复跑实证）

1. **哨事件（活体账）**：`/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48/
   events.jsonl` seq 58（ts 04:38:12Z）全字段实读——repo=ConstructiveWorld-Set·
   branch=fix/route2-tierA-supply-20261112·run_number=301·sha=`8f59c8f7…`·
   family=A-content-red·action=fix-content·evidence「红件 1/2：ids=[130971963665]·
   在册族：A-content-red（判类序取先）」·note「classification=rocqwash-ci-triage/1（ci_triage
   子进程 --offline）」。任务书称 round58＝该账事件序 58（seq 字段实取 58）。
2. **ci_triage 实判（本席真跑复现）**：`python3 -B tools/ci_triage.py --repo
   hy7pc8gfmf-dotcom/ConstructiveWorld-Set --run 43154750085 --logs --json
   /tmp/ci_triage_r301.json`（cpu_guard 包裹·rc=0）→ **RUN VERDICT
   family=A-content-red action=fix-content**·failing job 1/2（130971963665·mac 观察
   道）·failure-step=gate7 extraction execution→gate5→gate2·passing job 2/2
   skipped（中立）。与哨判逐字同族。
3. **dump 滤除 163 行→真错行浮出**：同跑 evidence 逐字「**dump 行滤除 163 行**
   （青色脚本回显/组指令·非真执行行·复核台账 §三-2 证据陷阱·--no-dump-filter
   可关）」——本席独立复算（日志全文 1698 行经 filter 滤后 1535·恰 163 行·
   `tools/ci_triage.py:196` DUMP_LINE_RE·`:526` filter_dump_lines·`:583`
   dump_dropped 计数）；滤后真执行行浮出＝GATE7 驱动失败真错行（line 2 形·
   §四）。
4. **驱动同秒全灭形（日志全文实算）**：failing job 日志两跳实取（1.69 万字节级·
   ci_triage 自带 fetch_job_log 通道）→**driver failed 行恰 531 条**（驱动
   号 [1/544]–[544/544] 中 531·失败指数 min=1 max=544）·**5 秒簇**分布
   108/105/102/104/112（04:28:07/24/42、04:29:01/11 五个墙钟秒·每秒 ≥102 条）
   ·**527 条显式「line 2」**＋4 条日志行帽截断于行号前（同形无反例）·错误位
   全为驱动件自身 line 2 characters 15-2x。run#302（job 130972045586）同形
   复算：531 条·**逐秒簇分布与 run#301 完全相同（108/105/102/104/112）**·
   同秒确定性批量错位签名。13 条未入失败册＝9 件 LW3 家族工作流豁免跳过＋
   4 件 names=0 自动跳过（[226 ForwardKLAdjudication/289 DTPT/290 DTPT_Truth/
   314 b1_extract4] 日志实取「no top-level informative statements」）——
   531＋13＝544 对账闭合。commit message 自述「544/544」为机理 shorthand
   （544 驱动全数同因）·实测 531 失败＋13 豁免——**两数并录**（§七）。

## 四、R3 签名「N 驱动同秒」检测注记候选（判例价值一）

- **签名定义（本例实测形）**：单 job 日志内 ≥100 条 `driver failed` 行共享同一
  墙钟秒（531 条聚 5 秒·每秒 102–112 条）＋错误位全数同位（line 2）＋两 run
  逐秒簇分布逐条相同＝**批量错位全灭**（环境/路径类·单因扇出）；对照真内容红
  逐件编译秒级发散不成簇。
- **注记候选（非裁决）**：ci_triage evidence 增「同秒簇计数」注记行（既有
  dump 行滤除计数行同位形·`tools/ci_triage.py:601-603` 先例）——判类仍由
  步名/词面定（A-content-red 不变）·注记仅供自诊断/自愈路由提速。阈值候选
  N=50/100·入档待器席另议·本席不动器。
- **判类输出＝自愈输入（监守自愈形态·判例价值二）**：哨判类证据三件套
  （failure-step=gate7＋dump 滤 163 行＋line 2 真错行字面）直接锁定「树参数
  相对形→cwd 错位」单因——同事会话据此 6 分钟落 restore。**哨不止记红·classification
  证据即自愈处方输入**＝本例闭环机理。

## 五、自愈环实录（restore→双绿→哨收环）

- **restore `bd8f38b`（Set 仓实读）**：commit message 逐字录 §二；diff 实取
  两处——coq.yml gate7 树参数相对形 `ConstructiveWorld_Live` 改
  `$GITHUB_WORKSPACE/ConstructiveWorld_Live` 绝对形；ci_seed_mac93.sh 无源面
  `exit 0` 改 build 模式落入编译环（含 run 43142078293 510/510 自述注）。
- **双绿（runs API 实取）**：run#303（pull_request·04:44:17Z）conclusion=
  success；run#304（workflow_dispatch·04:45:43Z）conclusion=success——双道
  （PR 触发＋route）同 sha 双绿＝自愈完整实证。
- **哨收环（state 实读）**：`_log/sentinel_v48/state.json` seen_runs 记
  43156738535/43156898674＝success·family=null（绿不生事件·设计内幂等）——
  **哨亲见红→failing→passing→绿全环**。
- **main 现势对账**：Set main HEAD `074eaa4` 同题 restore 在册（compare API：
  429ed53→main 两笔＝`9b9631b` route2 供应 7 件＋`074eaa4` mac-lane restore·
  实取）——自愈面已入主线。

## 六、Set PR#48 勘形（integration/g1-pipeline·G1 witness 8 件·预热注记）

> 任务书给名 AYCN19（PR 标题/正文无此字面·如实记）。全节 API 实取·零动 PR。

### 6.1 meta 与 CI current state

- **PR#48**：open·draft=False·head=`landing/g1-pipeline`（`adb295b`·4 commits：
  `1ee7b24` 8 件落装→`d389dc2` registry 按主线重生成→`2c52ee9` 三孤件恢复
  （w1-b5-v2 谱系）→`adb295b` FepIdentClass 降期（born-dirty 提取面））·
  base=main·created 03:24:32Z·updated 16:50:59Z·**mergeable=False·
  mergeable_state=dirty**。
- **分支 CI current state（4 runs 实取）**：#300 failure（`1ee7b24`）·#306 cancelled
  （`d389dc2`·watcher seq 60 捞获·两红件 A-content-red+E-coqchk-skipped）·#307
  failure（`2c52ee9`）·**#308 在飞**（`adb295b`＝现 head·16:51:00Z 起·
  conclusion=None 实取）——预热注记：**head 结论候令补记·现势不可预断**。

### 6.2 files API 清点（21 件·+5171/-576）

| 类 | 件 |
|---|---|
| **G1 witness 8 件**（PR body 依赖序） | laur_extract→calib＋calib_cert→witness→phiwin→rs_channel→rs_assembly→ab_def（`planb3_g1_calib/`_cert`/planb4_g1_ab_def/laur_extract/phiwin/rs_assembly/rs_channel/witness`.v·全 added） |
| 其余新增 .v 9 件（Set 本地谱系） | Arch_GibbsA_01/EntropyMonoSplitInst（w1-b5 孤件恢复·对 Main 树 blob 异）/N_total_assembly/WC_budget_family/atan_expl_rate/mach_fold_chain/tier_A_explicit_rate/vertex_window/window_cos_assembly |
| registry/infra 4 件（modified） | order.txt +554/-537·_CoqProject +15·coq.yml +38/-38·ci_seed_mac93.sh +9/-1 |

PR body 验证自述（如实转录）：逐件编译 8/8 rc=0（Rocq 9.3.0）·全树冷编裁决
516/518 EXIT=0（8 件落装件全绿）；另列 origin/main 既有缺陷 4 项（S05 排序
未净·R97 三行册有件缺等·「not from this integration」自述）。

### 6.3 mergeable=dirty 撞面定形（重叠件 blob 逐件对表·11 件）

- **blob 恒同 9 件**：coq.yml/ci_seed_mac93.sh（PR 侧已含 mac-lane 两修复同文
  面·与 `bd8f38b` 侧 blob 同）＋7 件 .v（N_total_assembly 等＝main 已落
  route2 供应波同件 `9b9631b`）——git 同内容 add/add 自动可解。
- **blob 异 2 件＝撞面集中 registry 两册**：order.txt（PR `32d3fc44` vs main
  `513cb3d0`）＋_CoqProject（PR `19aac77e` vs main `3eb19523`）——双侧按各自
  主线重生成相撞。行级撞点以 GitHub mergeable=False 现判为权威·机检为候选
  定位。**预热注记：PR#48 须在 main current state（`074eaa4`）上重生成 registry 两册
  后重评（与 PR#48 commit `d389dc2`「regenerate on main lineage」同法·基线
  换现主线）——本席不动 PR·候 PR 席令**。

### 6.4 与 Main 已并 unif limbs 波的关系（回灌判据·机检证实）

- **G1 witness 8 件＝Main 一致型 L1 面回灌·成立**：8 件 blob sha 对 Main
  main 树 `ConstructiveWorld_Live` 根逐件 SAME **8/8**（planb4_g1_witness
  Main blob `977ba49dda61` 实取同）——PR body「byte-identical to Main-tree
  green versions」自述获 blob 级机检证实。回灌方向＝Main→Set（Set 侧 L1 面
  回灌）·源＝Main unif-closure 谱系（PR body 自述）。
- **与 Main PR#9/#10 的谱系关系**：Main PR#9「y-E1 gamma-line node deposit
  waves 1-4: 49 nodes」已并（merged 12:19:19Z）·PR#10「unif limbs work stream: L3
  limbs（Hp/Htri closed＋Hexit wall registered）＋C3 certs」已并（12:22:29Z）
  ——两波落点 `ConstructiveWorld_Live/y_e1_gamma_nodes/` 子目录（dir 实取
  92 entries）·**G1 witness 8 件同出 Main 树而落点在 Live 根**（不落
  gamma_nodes 子目录）——同谱系不同落位·回灌件互不重叠（blob 表 8 件全在
  Main 根·零 gamma_nodes 件）。

---

## 七、边界与如实记

1. **R3 编号源**：承任务书/主会话判例册口径。库内可核机制判例面＝`更新账.md:
   2513-2515`（cwd 错位伪绿判例·gate4 预扫铁则①）＋`bd8f38b` commit message
   自述；**未寻得库内「R3」字面判例册行**（`复核-UNREC-14事件-20261112.md:48`
   R3 行系 Main run#8 retro 行·与本判例同名异指）——编号源不在本席可证面·
   如实记。
2. **544/544 vs 531/544**：commit 自述 544/544（机理 shorthand）·本席日志实算
   531 失败＋13 豁免/跳过——两数并录不互斥（§三·4）。
3. **round58 口径**：任务书称 round58·哨账字段实取 seq=58（rocqwash-sentinel-
   event/1）——两口径同指该事件·轮次号与事件序同源处本席未另证·如实记。
4. **AYCN19**：任务书给名·PR 标题/正文无此字面（§六如实记）。
5. **本席实跑**：ci_triage 真跑 run#301（--logs·rc=0·§三·2）·run#302 日志
   实算（fetch_job_log 两跳）·两 run 全日志落地 `/tmp/r301_job665.log`/
   `/tmp/r302_job586.log`。**未跑**：ci_triage --selftest（在账 rc=0 引据·
   `docs/勘形-multi-repo-Main仓适配-20261112.md:308`）；PR#48 重评/重基
   （预热注记·pending execution）；run#308 结论（在飞）。
6. **零写盘纪律**：rocqwash 工作树只增本档一文件；Set 仓零改动零 fetch（只读
   git show/log＋API）；冻结八件/quad8/更新账.md 零触碰（更新账只读引据）✓；
   git 零写操作（未 commit）✓。

## 八、本席自证字据（20261113·全部 cpu_guard -MaxWaitSec 120 包裹）

| # | 动作 | 结果 |
|---|---|---|
| 1 | `python3 -B tools/ci_triage.py --repo hy7pc8gfmf-dotcom/ConstructiveWorld-Set --run 43154750085 --logs --json /tmp/ci_triage_r301.json` | rc=0·RUN VERDICT A-content-red/fix-content·dump 行滤除 163 行·GATE7 [N/544] line 2 证据行（§三） |
| 2 | ci_triage.fetch_job_log 两跳拉 run#301/302 failing job 日志全文＋驱动行实算（python3 -B·stdlib） | run#301：1698 行·driver failed 531·5 秒簇 108/105/102/104/112·line 2 显式 527；run#302：同形 531·逐秒簇同分布（§三·4） |
| 3 | Set repository `git show bd8f38b`（stat＋diff＋message 全文） | 两修复逐字实取（§二/§五）·47+/39- |
| 4 | runs API（branch=fix/route2-tierA-supply-20261112·8 runs 全列） | 301/302 failure@`8f59c8f`·303/304 success@`bd8f38b`（§一/§五） |
| 5 | 哨账实读（`_log/sentinel_v48/events.jsonl` seq 58/59＋state.json seen_runs） | 活逮/补捞/记绿三面实取（§三·1/§五） |
| 6 | PR#48 API（pulls/48＋files 分页＋commits＋compare＋重叠 blob cross-check against the reference）＋分支 runs＋Main PR#9/#10＋Main 树 blob/y_e1_gamma_nodes | §六全节实取·8/8 SAME·mergeable=False·#308 在飞 |
| 7 | `python3 -B tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash` | 见当轮账（drift 须=0 方合三闸基准·若幻引即修档重跑） |
