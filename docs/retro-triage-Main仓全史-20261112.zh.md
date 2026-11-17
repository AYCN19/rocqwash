# 实测台账：Main 仓 CI 全史回扫（retro-triage·零码纯实测）20261112

> **性质**：实测席执行档·路线图⑦五步路径步 1（「零码先行：Main 历史 run retro-triage」·
> `docs/勘形-multi-repo-Main仓适配-20261112.md:204-207`）的交付件。**零码·纯实测**——
> 本席零代码改动，rocqwash 工作树只增本档一文件；禁触冻结八件/quad8/更新账.md
> （更新账只读引据）。判类全权在既有器面 `tools/ci_triage.py`（线上模式
> `--repo/--run`·v44 Set 先例同法·`更新账.md:3821`）；一切执行经
> `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120` 包裹；
> netrc token 零回显。
>
> **任务书给形与实取不符（首要登记）**：任务书给形「全史截至现约 25 条·全量」——
> 实取 `GET /actions/runs?per_page=100` ＝ **total_count=369**（两条 workflow：退役
> 9.1 炉 338＋现役 Main CI 9.3 的 31）。按实取为准：现役 coq93 系列 31 条**逐条全判**（本档
> §二主表）；退役 coq.yml 338 条**全量清点不逐判**（§一·3——量级超出任务书命名规模·
> 系退役 workflow 非本战役服务史·如实登记不充当实测）。哨覆盖对账与已知史锚
> （#16-20/#22/#23/#24/#25+）全部落在 coq93 系列上，与本档主表同号可对。

---

## 一、全史 runs 清单（实取 20261112·/tmp/retro_main/runs_full.json）

### 1.1 实取通道

- 命令：`bash cpu_guard.sh -MaxWaitSec 120 python3 -B /tmp/retro_main_runs.py`
  （只读 GET·token 取 `~/.netrc` machine github.com 行·ci_triage 同款 netrc 口径
  `tools/ci_triage.py:240-272`·脚本永不回显）——rc=0·cpu_guard MID pos=2 响亮。
- 端点：`GET /repos/hy7pc8gfmf-dotcom/ConstructiveWorld-Main/actions/runs?per_page=100`
  分页到齐（369 条＝100/100/100/69 四页·续拉三跳·DUP-IDS=0·PAGE-END=4）；
  全量落 /tmp（仓外·零仓内写盘）。

### 1.2 两 workflow 构成（实取）

| workflow | path | state | runs | run_number | 结论分布 | 事件分布 | created 区间 |
|---|---|---|---|---|---|---|---|
| Main CI 9.3（**现役唯一**） | .github/workflows/coq93.yml | active | **31** | **#1-#31 无缺号** | success 12／failure 12／cancelled 6／skipped 1 | push 24／pull_request 5／workflow_dispatch 2 | 2026-11-04T18:57Z .. 2026-11-11T17:35Z |
| Coq CI（**9.1 退役炉**） | .github/workflows/coq.yml | disabled_manually（勘形 §1.1 同款实取） | **338** | #1-#340 缺 #85/#221（API 无记录·未触发或已删不可分辨·如实） | success 160／failure 79／cancelled 99 | push 326／workflow_dispatch 12 | 2026-09-07T20:23Z .. 2026-11-04T19:35Z |

- coq.yml 月度结论分布（清点）：2026-09＝95 成/38 败/25 撤·2026-10＝63 成/71 败/
  25 撤·2026-11＝16 败/3 撤/2 成（含末代 run#340）。**本轮清点未逐判**（量级 338＝
  任务书命名规模 15 倍·且系 9.1 退役炉非现役服务史——逐判候选另排程·不冒充本轮实测）。
- coq93 系列 31 条 = 任务书已知史锚（§三）与 v47/v48 哨覆盖（§四）的公共坐标系。

## 二、逐 run 判类台账（coq93 全 31＋coq#340 桥件·32 发全 rc=0）

### 2.1 通道与命令形

- 每 run 一发：`bash cpu_guard.sh -MaxWaitSec 120 python3 -B tools/ci_triage.py
  --repo hy7pc8gfmf-dotcom/ConstructiveWorld-Main --run <id> [--logs] --json
  /tmp/retro_main/tri/coq93_<N>_<id>.json`（本席 31 连发＋coq#340 单发·
  **32 发 rc=0**·编排器 /tmp/retro_main_triage.py 整体经 cpu_guard 包裹）。
- `--logs` 规约（任务书「红炉才细看·绿炉跳」）：failure/cancelled 19 发加
  `--logs`；success/skipped 13 发零 `--logs`（判类走步级表·绿炉零网络追加）。
- 出账：rocqwash-ci-triage/1 report 逐 run 落 /tmp；判类谱五族＋绿炉＋
  UNRECOGNIZED 兜底全在器面（`tools/ci_triage.py:3-29` 判类谱·`:165-166` run 级
  判类序谱外置顶）。

### 2.2 主表（coq93 #1-#31＋coq#340）

判类＝run 级 verdict（`tools/ci_triage.py:513-530`）；「哨对账」列＝v48 哨 state
seen 族同异（§四）；墙钟＝job duration_sec。

| run# | id | 事件 | 结论 | branch | 判类 | action | 主要证据行（红步/机理） | 墙钟 | 哨对账 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 41892161661 | push | failure | main | **A-content-red** | fix-content | Build full tree 红（步名内容族）＋gate5/gate2 连红 | 127s | **窗外缺（本轮补判）** |
| 2 | 41898362546 | push | failure | main | A-content-red | fix-content | Build full tree 红＋gate5/gate2 | 129s | ✓同 A |
| 3 | 41914865932 | push | failure | main | **UNRECOGNIZED** | watch-only | failure·零红步·Build 悬 in_progress（runner 失联形）·谱外不充谱 | 57007s | ✓同 UNREC |
| 4 | 42050566114 | push | failure | main | **E-coqchk-skipped** | rerun-after-stable-window | gate4 红（artifact 词面）＋coqchk skipped＝E 签名两件齐 | 138s | ✓同 E |
| 5 | 42065570836 | push | failure | main | A-content-red | fix-content | Build full tree 红＋gate2 | 33465s | ✓同 A |
| 6 | 42151784648 | push | failure | main | A-content-red | fix-content | coqchk full-tree certification 红（步名 COQCHK 族）＋gate2 | 29980s | ✓同 A |
| 7 | 42221225472 | push | cancelled | main | **UNRECOGNIZED** | watch-only | cancelled＋唯 gate2 红步（fail-loud 哨步连红·谱外） | 1722s | ✓同 UNREC |
| 8 | 42225371642 | push | cancelled | main | UNRECOGNIZED | watch-only | cancelled＋唯 gate2 红步 | 1957s | ✓同 UNREC |
| 9 | 42230638246 | push | success | main | none | watch-only | 全绿 0 红件 | 39022s | ✓绿 |
| 10 | 42345007340 | push | failure | main | UNRECOGNIZED | watch-only | failure＋唯 gate2 红步 | 40785s | ✓同 UNREC |
| 11 | 42397887296 | push | failure | main | A-content-red | fix-content | coqchk full-tree certification 红＋gate2 | 1017s | ✓同 A |
| 12 | 42402305184 | push | success | main | none | watch-only | 全绿 | 1253s | ✓绿 |
| 13 | 42444700994 | push | success | main | none | watch-only | 全绿 | 1201s | ✓绿 |
| 14 | 42447585809 | push | failure | main | A-content-red | fix-content | gate7 extraction execution（post-build 词面）红＋gate2 | 328s | ✓同 A |
| 15 | 42448415112 | push | success | main | none | watch-only | 全绿 | 1198s | ✓绿 |
| 16 | 42456863184 | pull_request | cancelled | gamma/w3-wave1 | A-content-red | fix-content | cancelled＋gate5 红（pre-coqchk 词面→内容族·有红步非连坐） | 61s | ✓同 A |
| 17 | 42457455971 | pull_request | cancelled | gamma/w3-wave1 | A-content-red | fix-content | cancelled＋gate5 红（同上） | 95s | ✓同 A |
| 18 | 42457899042 | workflow_dispatch | skipped | gamma/w3-wave1 | none | watch-only | job skipped 零步（条件跳过非红·`ci_triage.py:422-425`） | 0s | ✓绿 |
| 19 | 42458352264 | push | success | main | none | watch-only | 全绿 | 1113s | ✓绿 |
| 20 | 42461341685 | pull_request | cancelled | gamma/gate7-port | UNRECOGNIZED | watch-only | cancelled＋唯 gate2 红步 | 738s | ✓同 UNREC |
| 21 | 42471831874 | push | success | main | none | watch-only | 全绿 | 1204s | ✓绿 |
| 22 | 42600735076 | pull_request | failure | fix/unif-l0-deposit | **B-netred** | rerun-after-stable-window | Run actions/checkout@v5 红（步名网络族）·已知 NETRED 锚咬合 | 87s | ✓同 B |
| 23 | 42610674504 | push | success | main | none | watch-only | **全绿**（1521s 完走·步级零红零跳）·任务书「僵尸·预期 E/OTHER」不符（§三·3） | 1521s | ✓绿 |
| 24 | 42663742407 | push | failure | main | E-coqchk-skipped | rerun-after-stable-window | gate4 红＋coqchk skipped＝E 签名 | 119s | ✓同 E |
| 25 | 42667436985 | push | success | main | none | watch-only | 全绿 | 1096s | ✓绿 |
| 26 | 42676028568 | workflow_dispatch | cancelled | main | UNRECOGNIZED | watch-only | cancelled＋唯 gate2 红步 | 156s | ✓同 UNREC |
| 27 | 42859373023 | push | success | main | none | watch-only | 全绿 | 1169s | ✓绿 |
| 28 | 42876807576 | pull_request | success | fix/unif-l1-g1-witness | none | watch-only | 全绿 | 1214s | ✓绿 |
| 29 | 42887706384 | push | success | main | none | watch-only | 全绿 | 1260s | ✓绿 |
| 30 | 43061870614 | push | failure | main | E-coqchk-skipped | rerun-after-stable-window | gate4 红 42s＋Build skip＋coqchk skipped＝E 签名 | 129s | ✓同 E |
| 31 | 43069611064 | push | success | main | none | watch-only | 全绿 | 1215s | ✓绿 |
| 340* | 41898362460 | push | failure | main | A-content-red | fix-content | Build full tree 红＋gate2（9.1 炉末代·coq.yml 系） | 251s | ✓同 A |

\* coq#340 系 coq.yml（退役 9.1 炉）末代 run·非 coq93 系列——单发补判只为哨 33 事件
并集对账完备（§四·3）；coq.yml 余 337 条清点未逐判（§一·2）。

### 2.3 族分布与判据面观察（本轮 32 发蒸馏）

**族分布**（coq93 31 条）：none×13（success 12＋skipped 1）／A-content-red×8
（#1,#2,#5,#6,#11,#14,#16,#17）／UNRECOGNIZED×6（#3,#7,#8,#10,#20,#26）／
E-coqchk-skipped×3（#4,#24,#30）／B-netred×1（#22）。action 分布：watch-only×19
（绿 13＋谱外 6）／fix-content×8／rerun-after-stable-window×4（E3＋B1）。
判类谱外零 UNRECOGNIZED 误断、零充谱——兜底按设计响亮（`tools/ci_triage.py:22-23`）。

判据面四观察（全部步级证据直读·日志词面因 §2.4-② 缺席·如实）：

1. **步名族 regex 全兼容实证**（勘形 §3.1 预言逐条命中）：Build full tree→A
   （:136 CONTENT 词 build）；coqchk full-tree certification→A（COQCHK_STEP :139）；
   checkout@v5→B（NET 词 checkout :137）；gate5 quarantine(pre-coqchk)→A（词面
   搭便 coqchk 子串）；gate7 extraction execution(post-build)→A（词面搭便 build
   子串）——与勘形 §3.1 表五行一一咬合。
2. **E 签名机理实证**（三例同构 #4/#24/#30）：gate4 comment guard 步名含
   「artifact-only」→UPLOAD_STEP_RE 命中（:452）＋coqchk 步 skipped→E 签名两件齐
   （:456-465）；E 判类序先于步名 B（:473-478）——勘形 §3.1 担心的 gate4 红误归 B
   **未现**（三例 coqchk 均 skipped→E 路）；E 第三件 GATE-BANNER-ABSENT 日志确证
   因 415 缺席（如实注·勿读作已确证）。
3. **UNRECOGNIZED 两形实证**（Main 特有红形·判类谱外按设计人工指认）：
   ①runner 中途失联形（#3：conclusion=failure 而零 failure 步·Build 步悬
   status=in_progress conclusion=None·墙钟 57007s≈15.8h——注意勘形 §1.2 把该
   run id 引作 2880min timeout 判例锚·实测 15.8h＜48h 帽且 conclusion=failure 非
   timed_out·判例锚指 timeout 配置面非触顶实录·两读并记不互斥）；②gate2-only
   红步形（#7,#8,#10,#20,#26：cancelled/failure 且唯 gate2 axioms sentinel 红——
   gate2 步名零 regex 命中（:136-139 五族词面俱不沾）→谱外）。gate1/gate3 红形
   本轮未现（勘形 §3.1 预言其零命中共面·实取主患为 gate2）。
4. **连坐形判别实证**：cancelled 有步骤零红步→B 连坐（:437-441）在本系列
   **零例**（PR 镜像代 #16/#17/#20 与 dispatch #26 的 cancelled 全带红步→各自
   落 A/UNRECOGNIZED·红不被 cancelled 吞）；D 零步骤形亦零例（#18 是 skipped
   非 cancelled·走 :422-425 条件跳过路）。

### 2.4 新实证面（器面已漂·本席零码如实登记）

1. **logs 端点 415（v35 判例形已漂）**：19 发 `--logs` 全数
   `logs-GET: HTTP 415 {"message":"Unsupported 'Accept' header: 'text/plain'.
   Must accept 'application/json'."}`——`tools/ci_triage.py:348` 现行
   `accept="text/plain"` 被 GitHub 现势拒。本席独立双探（只读·netrc 同款）：
   `Accept: text/plain`→415（上词原样）；`Accept: application/json`→403
   Azure-signed-URL 层 AuthenticationFailed XML（403/415 与退避重试设计内·
   原码入证据 `:341-354` fail-soft 落账）。→**判类本轮全走步名族/E 签名步级
   证据·日志词面零在场**；器面小改候选＝--logs 路改 `application/json` 后跟
   signed-URL 重定向（勘形分级「小改」同档·候另席）。
2. **墙钟两代**：冷编长墙代（#3/#5/#6/#9/#10·29980-57007s≈8.3-15.8h）与指纹
   skip 快炉代（#15 后绿炉 1096-1260s≈18-21min·红炉 61-328s）分界在 2026-11-07
   ~11-08 间——与 coq93.yml 14 道并行指纹 skip 形（勘形 §1.2 实取）对读吻合；
   仅趋势级观察（律 1 噪声带口径·单跑读数·`docs/perf-profile-v1.0-20261111.md:172`）。

## 三、与已知史对账（任务书锚逐条）

| 锚 | 任务书给形 | 实测（本档 §二） | 对账 |
|---|---|---|---|
| #16-20 | PR 镜像盲区代 | #16/#17 pull_request gamma/w3-wave1 cancelled→A（gate5 红）；#18 dispatch 同枝 skipped→绿；#19 push main→绿；#20 pull_request gamma/gate7-port cancelled→UNRECOGNIZED（gate2-only）。事件面 push/PR/dispatch 混杂同窗（2026-11-08 06:58-08:04）——pushci PR 路 mirror-blind 双重失配史迹（勘形 §3.2）与实取窗对读成立 | ✓（判类面：A×2＋谱外×1＋绿×2） |
| #22 | PR NETRED | pull_request fix/unif-l0-deposit failure→**B-netred**（checkout 红步直证）——与哨 B-netred×2 恰 Set#269/Main#22 咬合（`docs/ops-sentinel-长驻手册-v1.0-20261112.md:321`）逐字复核成立 | ✓ 完全咬合 |
| #23 | 僵尸【已实测·判类预期 E/OTHER】 | push main **success→none**（1521s 完走·18 步全 success 零红零跳·job「Rocq 9.3 build + coqchk (self-hosted seed cache, Windows)」）·哨 state 同记绿。**实测与预期不符·如实登记**——「僵尸」面（如 dispatch 僵尸/分支保护僵尸等形态语义）不在本席实测谱内·API 步级全绿为机械事实 | ✗ 预期 E/OTHER vs 实测绿（判类谱 none）——两留不修饰 |
| #24 | failure | push main failure→**E-coqchk-skipped**（gate4 红＋coqchk skipped） | ✓（failure 收束·判类 E） |
| #25+ | push 系 | #25-#31＝push 6／PR 1（#28）／dispatch 1（#26）·绿 5／红 2（#26 谱外·#30 E）——push 为主体系成立（PR/dispatch 散布在册） | ✓（系别面） |

## 四、与哨 33 事件覆盖注记（v47 账＋v48 落位两录不合并不修饰）

### 4.1 哨侧覆盖面（state 直读·`/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48/`）

- events.jsonl **33 行**（全 ci-red）＝Set 15＋Main 18（本席逐行实读·family 分布
  A18/UNREC8/E4/B2/C1——手册 §4.3 `:336-342` 同款）；Main 18 事件 run id：
  coq93 #2,#3,#4,#5,#6,#7,#8,#10,#11,#14,#16,#17,#20,#22,#24,#26,#30＋coq#340。
- state.json Main seen=**31**（coq93 #2-#31＋coq#340）·Set seen=30——与 v47 账
  「Main 30 runs/18 红·state seen 30/30」（`更新账.md:3895`）与手册 §4.3「各
  30/30」差一：现读多 coq93#31（绿·`cw_sentinel.py:589-590/:608/:612` 绿记
  seen 不出事件·events 33 行未变）——两账系各自时点快照·本席现读为 20261112
  02:00 后现势·如实并记不追账。
- **窗外结构性缺额实证**：哨窗 `RUNS_QUERY per_page=30`（`tools/cw_sentinel.py:172`）
  ＋repo 总量 369＞30→窗内恒为最新 30 条。现势窗（created_at 降序 rank 1-30）
  恰＝coq93 #2-#31 三十条；**coq93#1 全仓第 33 新**（rank 31=coq#340·rank 32=
  coq#339·均 created 同秒 2026-11-04T18:57:08Z 竞序）——只要≥30 条更新的 run
  在册（现势 369 且单调增），#1 结构性永在窗外·哨在册面永不回补。这就是任务书
  「补全史缺额」的机械实体：**本轮 #1 补判=A-content-red**（127s 冷编败·Build
  full tree 红）。另 coq#340（rank 31·与 coq93#2 created 同秒 19:35:12Z）现势
  窗外在册却在哨 seen——系先前窗界不同时点轮所记·seen 永不逐出（宁重复不丢件·
  手册 §3.3 口径）·与 v47 账 30/30 快照之差如实并记不追账。

### 4.2 逐 run 对账（本轮判类 vs 哨 state seen 族）

coq93 两边共测 **30 条·30/30 族全同·0 分歧**（绿 12＋红 18 逐条咬合·
本席机检输出在案：agree=30 disagree=0 sentinel_absent=1）；差异面恰互补：
哨独有 coq#340（本轮单发补判→A·与哨事件同族 ✓）·本轮独有 coq93#1（哨窗外）。
**哨 33 事件的 Main-18 判类被本轮独立复算逐条复现**——判类谱跨时间稳定·
B/E/A/UNREC 族零漂。

### 4.3 并集口径（哨 33 事件 × 本轮 32 发）

- Main 侧红炉并集＝**19 个 distinct run**（coq93 18＋coq#340）·本轮**全部亲测**；
  族分布并集：A-content-red×9（#1,#2,#5,#6,#11,#14,#16,#17,#340）／
  UNRECOGNIZED×6／E-coqchk-skipped×3／B-netred×1。哨 Main-18＝并集 19 减本轮
  补判 #1 后同余 17＋#340（恒等）。绿炉并集：coq93 13（哨 state 全记 seen）。
- Set 侧 15 事件本轮**未重判**（v44 Set 先例已 retro 全史 30 条·`更新账.md:3821`；
  本轮 scope=Main 仓——任务书明命）。33 事件总量对读：Set 15＋Main 18＝33 恒等；
  并集新增信息＝Main 红炉 #1（哨结构性盲区）＋coq.yml 338 清点底账。

## 五、结论

1. **判类吻合度**：coq93 全史 31 条逐判·与哨 33 事件共测面 30/30 全同零分歧·
   与已知史五锚四符一不符（#23 僵尸预期 E/OTHER vs 实测绿·如实两留）——
   v44 Set 先例的「判类与实况逐条吻合」在 Main 仓复现。
2. **史缺额补齐**：哨窗外结构性盲区（per_page=30 窗×369 总量）本轮以
   per_page=100 全量清点＋coq93 全判补齐·#1（A-content-red）为唯一哨永不可见
   红炉·已入册。
3. **器面新实证两条**（零码登记·候小改）：logs Accept 415（§2.4-1）＋
   Main 特有谱外红形 gate2-only/runner 失联两形在册（§2.3-3·判类谱「不充谱」
   设计内·扩谱候选须人工指认后另议·禁机械充谱）。
4. coq.yml（9.1 退役炉）338 条逐判＝另排程候选（本档仅清点·禁冒充实测）。

## 六、边界与如实记

1. 本席实跑：全史清单 GET×1·ci_triage 32 发（31 连发＋coq#340 单发·全 rc=0）·
   logs 双探×1·哨 state/events 直读·doc_lint 复跑（§七）。**未跑**：coq.yml
   337 条逐判（scope 外·§一·2）·pushci/unclog selftest（在账引据非本轮）。
2. 判类证据面＝步级（步名族 regex＋E 步级签名）·日志词面零在场（415·§2.4-1）
   ——「GATE-BANNER-ABSENT 等词面确证」类结论本轮一律不冒认。
3. #23 僵尸预期不符如实两留（§三·3）；「僵尸」语义不在 API 实测谱内。
4. 哨 state seen=31 与两账 30/30 之差如实并记不追账（§四·1）；对账基点＝
   v48 落位三件套现读＋v47 账文直引。
5. /tmp 出账（runs_full.json/tri/*.json）系易失件·本档数字全部自其转录；仓内
   只增本档一文件·零 git 操作·冻结八件/quad8/更新账.md 零触碰。
6. **行号时效＋并发注记**：本档器面行号锚＝本席开工时点工作树（v48 325b4dc 已
   提交态）·交稿前核验时工作树现出并发席在飞小改（`git diff tools/ci_triage.py`
   三 hunks 全落 docstring/〔九〕selftest 矢区·KEY_LOG_PATTERNS/步名 regex/
   classify/run_verdict/accept= 等判类路径零改动——本席 grep 机检 0 命中）·
   本席 32 发实测行为两版一致·行号引用以开工态为准（并发开发会漂·器面冲突以
   `--help`/docstring 为正本·ops-sentinel 手册 §附·3 同款先例）。

## 七、本席自证字据（20261112·全部 cpu_guard 包裹）

| # | 动作 | 结果 |
|---|---|---|
| 1 | `python3 -B /tmp/retro_main_runs.py`（全史清单 GET） | rc=0·total_count=369 fetched=369 DUP-IDS=0 PAGE-END=4（§一） |
| 2 | `python3 -B /tmp/retro_main_triage.py`（coq93 31 连发 ci_triage --repo --run） | rc=0·TRIAGE-DONE n=31 family_hist={A8,UNREC6,E3,none13,B1}（§二） |
| 3 | `ci_triage.py --repo … --run 41898362460 --logs`（coq#340 桥件单发） | rc=0·A-content-red（§二主表末行） |
| 4 | logs 双探（text/plain vs application/json·job 126871747925） | 415（原词入账）/403 Azure XML（§2.4-1） |
| 5 | 哨 v48 三件套直读（state/events/report） | Main seen=31·events 33 行 Main 18·对账 agree=30/disagree=0（§四） |
| 6 | `python3 -B tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash` | **VERDICT consistent（exit 0）**·本档 refs=18 unresolved=0 oos=0 drift=0·全仓三查零漂（本档交稿后本席实跑·§六·6 注记同轮） |

---

## 八、器面小改落地注记（20261112·工装席 triage-fix 席增补·承 §2.4-1 候选与 §2.3-3 两形）

> **本节性质**：后续工装席增补（非 §一-§七原实测席笔迹）——判类谱序
> UNRECOGNIZED>C>A>E>B>D **不动**；器面两小改＋fixture 两件＋selftest 矢量区。
> 本档 §二主表 32 发判类系当时器面记录**不追溯改写**·现势器面对同形数据的
> 判类变化逐条在册（§8.3）。全部实跑经
> `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120` 包裹。

### 8.1 logs 端点 415 修法（§2.4-1 候选落地·Accept 值实测定）

- 实测探针（只读 GET·job 127903477736＝本档 §二 run#3 红件·netrc 同款口径·
  token 永不回显）：`Accept: text/plain`→415 原词（§2.4-1 同形复现）；
  `Accept: application/vnd.github+json`→**302 Location**（Azure 签名 URL·
  `application/vnd.github.v3.text` 同 302·取标准形）；对签名 URL
  **零 Authorization** 第二跳→**200** 实日志 1,673,483 bytes；对照带 token
  转发→403 Azure AuthenticationFailed XML——§2.4-1 双探 403 形机理实证
  ＝urllib 缺省随重定向转发 Authorization 头所致·两跳零认证即修。
- 器面落点：`tools/ci_triage.py:122` LOGS_ACCEPT 常量＋`:368` _NoRedirect
  禁自动重定向 handler＋`:387` fetch_job_log 两跳重写（403/429/5xx 第一跳
  退避重试语义保持·404/415 原码照旧入证据·第二跳失败入证据不重试）。
- 修后真发一发实证（本席实跑）：`python3 -B tools/ci_triage.py --repo
  hy7pc8gfmf-dotcom/ConstructiveWorld-Main --run 42221225472 --logs --json
  /tmp/triagefix_r7.json` → rc=0·run#7 红件 job 127903477736 取日志 200·
  evidence 抓到 GATE-BANNER-ABSENT 词面 3 行·零 415 注记（§2.4-1「日志词面
  零在场」债清偿）。
- selftest 增 canned 矢（`tools/ci_triage.py:1300` 〔十〕·4）：修后形
  hop1 Accept=LOGS_ACCEPT→302→hop2 零 Authorization→200 两跳断言＋415/403/
  重定向无 Location 三负例原码入证据（零网络·_open 注入）。

### 8.2 gate2-only 连坐形入谱（E 变体·§2.3-3 观察二的人工指认落谱）

- **规则出处＝本档 §二主表 UNREC 六事件（#3/#7/#8/#10/#20/#26）**：其中
  **#7/#8/#10/#20/#26 五发 gate2-only 形**（唯 gate2 axioms sentinel 红·前置
  build/coqchk 非 content 红·无其他红步）人工指认为「coqchk 产物缺·gate2
  连坐」族＝E 变体；**#3 runner 失联形（failure·零红步）仍谱外不充谱**——
  六事件并录·五入一留（§五·3「扩谱须人工指认」纪律承本任务书指认）。
- 判据（`tools/ci_triage.py:164` GATE2_STEP_RE＋`:558` classify E 变体分支）：
  红步集 ⊆ {gate2＋上传族} 且**纯 gate2 红步在册**（gate2 名非上传名——防
  「Upload artifact (gate2 ledger)」gate2 子串词面搭便误吞上传红·负证矢量
  在册）→ family=E-coqchk-skipped·action=rerun-after-stable-window·
  evidence 注 gate2-only 连坐；log GATE-BANNER-ABSENT 词面在册即第三件确证。
  action 承 E 族处置表统一 rerun-after-stable-window（涉网络/ watch-only
  分流本五发无证据面·如实不设）；#7/#26 build 步 conclusion=cancelled（非
  红步族）同判——判据面为「非 content 红」非「success/skipped 严格面」。
- 日志语义确证（§8.1 修后通路·run#7 实抓原句）：gate2 哨自陈「_chk_all.log
  不在盘——coqchk 未产出日志（上游 gate4/build 夭折连带·红因看上游步）·
  非 COQLIB 代际失守」——与 E 变体判据逐字咬合。
- fixtures 两件（真形自本档 §二主表 32 发出账逐字段誊录·_provenance 在册）：
  `tests/fixtures/ci_triage_gate2_only_cancelled.json`（run#7·job
  127903477736·cancelled 18 步真形）／`ci_triage_gate2_only_failure.json`
  （run#10·job 128320751675·failure 18 步真形）。selftest 正判两件全命中
  ＋负判五发（build 红＋gate2 红→A·coqchk proper 红＋gate2 红→A·gate2
  子串搭便上传红→B·tree-stats 单红→UNRECOGNIZED·#3 零红步形→UNRECOGNIZED
  不充谱）（`tools/ci_triage.py:1300` 〔十〕）。

### 8.3 现势判类对读（不追溯改写 §二主表·如实并记）

#7/#8/#10/#20/#26 五发现势判类＝E-coqchk-skipped（rerun-after-stable-window）
·#3 仍 UNRECOGNIZED——§2.3 族分布 UNRECOGNIZED×6 为当时器面快照·现势同批
数据判类＝UNREC×1＋E 变体×5（run#7 现发实证 §8.1 在卷）。§四哨对账 30/30
全同结论不受影响（判类面变化仅族名迁移·红件集不变）。

---

## 九、Maintained-UNRECOGNIZED two-shape signature notes（维持 UNREC 两形签名说明）

> **Section scope.** §2.3-3 recorded two Main-specific out-of-taxonomy shapes
> (runner mid-step loss; gate2-only red step). The token-level ground truth for
> both is the review ledger `docs/复核-UNREC-14事件-20261112.md` (§二 S3/S6,
> §三-4/§三-6, §四-2/§四-3). This section fixes the two maintained-UNRECOGNIZED
> signatures and their engine evidence notes. The taxonomy and the run-level
> precedence (UNRECOGNIZED > C > A > E > B > D) are unchanged: both shapes stay
> `family=UNRECOGNIZED` (action `watch-only`) — the supplement adds evidence
> annotations, one canned fixture, and selftest vectors, nothing else (never
> force-fitted into any family).

### 9.1 Shape ① — runner-lost candidate（runner 失联形·Main coq93 run #3, id 41914865932）

- Signature (four legs, all from the review ledger §二 S3/R1 step-level
  evidence): job `conclusion=failure` with zero failed steps; the build step
  "Build full tree (order topology, fingerprint skip, thermal-guarded)" still
  hung at `status=in_progress` with `conclusion=null` while the remaining
  steps stay pending; wall clock 57007s ≈ 15.8h — below the configured cap
  and not `timed_out`; the job-log GET returns HTTP 404 BlobNotFound (the log
  blob was never uploaded — the companion evidence of a runner lost mid-step;
  §三-6 records the same double-404 for the Set#284 Windows job).
- Engine form (`tools/ci_triage.py` classify): when all four legs hold — the
  fourth leg being the logs-GET HTTP 404 evidence note, carried online by
  `fetch_job_log` or offline by the `job_log_notes` canned extension —
  classify emits the evidence-package note `runner-lost-candidate` (hung
  build step names, wall clock, 404) plus the maintained rationale line, and
  returns `UNRECOGNIZED`/`watch-only` unchanged. The D shape (cancelled +
  zero steps) does not cover it; no family is assigned.
- Fixture `tests/fixtures/ci_triage_runner_lost.json`: job-level fields from
  a fresh GET; the step table transcribed from the surviving triage record of
  the ledger (the live API no longer serves the step table for this job —
  `steps=[]` on a fresh read, and the check-runs endpoint carries
  `output.steps: null`); `job_log_notes` carries the real HTTP 404
  BlobNotFound note text captured by a direct log-fetch probe. Selftest
  vectors: the positive fixture plus four negatives (no note / note without
  404 / hung non-build step / red steps present) and a byte-identical rerun.
- Live-read boundary (recorded as-is): a fresh re-triage of run #3 returns
  `UNRECOGNIZED` without the annotation, because the pruned `steps=[]` also
  removes the hung-step leg from the live step table and the `--logs` fetch
  list selects jobs with steps; the four-leg shape is observable through the
  canned fixture (and the 404 leg is still directly observable — the blob is
  still absent on a fresh probe).

### 9.2 Shape ② — attested-red auth-state maintained（认证态红形·Main coq93 run #10, id 42345007340）

- Signature (review ledger §二 S6/R4, §三-4, §四-2 token split): genuinely
  executed (dump-line-filtered) `判定=CLEAN(exit 0)` with axiom total 0
  together with `GATE2-ATTEST-RED` — parser CLEAN yet the attestation
  coverage assertion red (R4 partition break, appendix absent), with the
  coqchk step completed (40398s). The E gate2-only cascade variant does not
  hold for attested-red shapes (§四-3: forcing it there would be a false
  positive — the manual verdict stays UNRECOGNIZED).
- Engine form: the gate2-only shape keeps its exclusion note, and classify
  now additionally emits `auth-state-red-maintained` when both tokens are
  genuinely present on dump-filtered log text — the note carries the UNREC
  maintained rationale automatically (E cascade variant does not hold; manual
  identification takes precedence; no force-fit). A single attestation token
  without the pair keeps the plain exclusion note. Family stays
  `UNRECOGNIZED`/`watch-only`.
- Fixture `tests/fixtures/ci_triage_gate2_only_failure.json` (canned
  genuinely-executed lines plus one dump line) carries both tokens; the
  selftest asserts the pair note on it, plus two single-token negatives.
