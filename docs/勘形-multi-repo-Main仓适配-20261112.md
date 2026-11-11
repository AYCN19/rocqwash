# 勘形档：路线图⑦ 多仓扩展——rocqwash 服务 Main 仓 CI 的适配面（只读·零动码）20261112

> **性质**：勘形评估档·路线图⑦候选（`docs/roadmap-v43-plus-20261111.md:84-92`）的
> 「Main 仓 CI 形制勘察」前置面。**只读·零动码**——本席零代码改动、rocqwash 工作树
> 只增本档一文件；禁触冻结八件/quad8/更新账.md（本席对更新账只读引据）。
> **口径**：Main 仓 CI 结构**实取为准**（api.github.com netrc 只读 GET·token 零回显·
> 全程 cpu_guard 包裹）；任务书给形与实取不符处逐条如实登记（§一·2）。
> **分级**：即用（零改可用）／小改（fixtures/规程/词面级）／中改（结构性盲面/数据面工程）。

---

## 一、Main 仓 CI 形制实取（20261112·api.github.com netrc GET）

### 1.1 实取通道与 meta

- 通道：`/tmp/fetch_main_ci.py`（只读 GET·token 取 `~/.netrc` machine github.com 行
  password——`tools/ci_triacy.py` 同款 netrc 口径·脚本永不回显 token）。
  实跑两脚本：`python3 -B /tmp/fetch_main_ci.py` 与 `python3 -B /tmp/fetch_main_tree.py`（均 rc=0·cpu_guard 包裹）。
- **REPO-META（实取）**：`hy7pc8gfmf-dotcom/ConstructiveWorld-Main` default_branch=**main**
  private=False size_kb=34468 **push_perm=True**（netrc token 对 Main 仓有 push 权——
  v36「真发段需真远端凭据·用户面」（`更新账.md:3608`）的凭据面现势已具备）。
- **workflows（实取 GET /actions/workflows）**：total_count=2——
  | workflow | id | path | state |
  |---|---|---|---|
  | Coq CI（9.1 炉） | 352580515 | .github/workflows/coq.yml | **disabled_manually**（休眠） |
  | **Main CI 9.3** | 407286573 | .github/workflows/coq93.yml | **active（现役唯一）** |

  两文件全文已实取落 /tmp（coq93.yml=606 行·coq.yml=457 行）；本节引据行号以
  实取件 `/tmp/mainwf_coq93.yml` 为准（远端 ref=main HEAD 时点）。

### 1.2 coq93.yml（Main CI 9.3）现役形要点（实读全文）

| 面 | 实取 | 行号 |
|---|---|---|
| 触发面 | push branches **[main]**＋pull_request＋workflow_dispatch（macos_only 输入·文件头注自注「模板残留·无害」） | `coq93.yml:40-49` |
| 并发组 | **单组固定名 `cw-main-ci-93`＋cancel-in-progress: true**（与 Set per-ref 池不同·见 §3.2） | `coq93.yml:51-54` |
| job 数 | **单 job `coq-build`（Windows self-hosted）——mac observation job 无**（头注明文「mac 观察席 omit（Main 底本无 mac job 块·如实登记）」） | `coq93.yml:58-66`·`:32-33` |
| timeout | 2880min（48h 重尾冷编墙·run 41914865932 判例） | `coq93.yml:70-74` |
| checkout | **actions/checkout@v5 fetch-depth:1——非 API tarball** | `coq93.yml:89-91` |
| 工具链 | job env 形 A 9.3 注入（COQC/COQCHK/COQLIB/ROCQLIB→opam-root default 9.3） | `coq93.yml:75-87` |
| 认证树 | **ConstructiveWorld_vo 树**（build/chk/gate5/gate2 全 on vo）；Live 树仅 gate1/gate4 词面扫描 | `coq93.yml:105-107`·`:131-133`·`:417`·`:564` |
| build 形 | parallel_build.sh **14 道并行**（BLDJ_JOBS=14·指纹 skip·非 cold build）·pwsh cpu_guard_v3.ps1 温控 | `coq93.yml:247-368` |
| coqchk 形 | parallel_chk.sh **14 路**共享闭包（CHK_JOBS=14·CHK_TREE_COPY=1）·ATT-RECON 跳验清单＋W3 每 20 轮全量 backstop | `coq93.yml:479-529` |
| gate 步谱 | gate1→gate4→gate3→Seed→RAM guard→Build→tree-stats→gate5→attest reconcile→coqchk→Upload cache→gate2→Upload logs（14 步全列实取） | `coq93.yml:102-605` |
| 日志词面 | GATE-BANNER-ABSENT/GATE-BANNER-FAIL/GATE2-AXIOMS-RED/GATE5-RED/GATE5-NOSCANNABLE/GATE4-RED/ATT-RECON-FAIL/DEP-CASCADE/W3-BACKSTOP | `coq93.yml:565`·`:569`·`:586`·`:424-428`·`:137`·`:467-470`·`:335`·`:507` |

### 1.3 任务书给形与实取不符（两项·实取为准·如实登记）

1. 任务书给形「Windows 单道/cold build/**mac observation 两 job**」——实取＝Windows
   **单 job**（mac observation omit·`coq93.yml:32-33` 明文）；build＝指纹 skip 14 道并行
   非 cold build（cold build 形现役在 **Set 仓** coq.yml:21/:30）。「两 job」形系 Set 仓
   现役形（Set coq.yml:19-735 双 job）。疑为两仓形混写·按实取为准。
2. 任务书给形「**API tarball checkout**」——实取 Main coq93.yml＝actions/checkout@v5
   （`coq93.yml:89-91`）；API tarball checkout（Ref quiescence supersede gate＋tarball
   fetch·20261109 dual-store lesson）系 **Set 仓** coq.yml:39-88 形。

### 1.4 树面实取（/tmp/fetch_main_tree.py·rc=0）

- root：`ConstructiveWorld_Live/`＋`ConstructiveWorld_vo/` 双树＋root `_CoqProject`
  （3743B）＋`build.sh`＋root `cpu_guard.ps1`（旧 shim·Set 仓同款注记指 infra 正典）。
- 双册 PATH-PROBE（HTTP 码实取）：Live/order.txt **200**（35384B）·Live/_CoqProject **200**
  （19862B）·vo/order.txt **200**（33752B）·vo/_CoqProject **200**（18788B）·
  **root/order.txt 404**·root/_CoqProject 200。
- Live 顶层 entries=**1000**（contents API 单页帽截断·如实）·单页内 .v=**995**（下界；
  coq93.yml:101 注「Live 679/vo 700」系 20260925 gate1 落树时点·不同时点不同口径·两数并录不互斥）。
- **本地无 Main 仓 checkout**（实取 `ls -d /Users/apple/Desktop/*Main*` 空）——§3.3 正本面依据。

---

## 二、Set 仓 coq.yml 现役形（对照·实读 /Users/apple/Desktop/ConstructiveWorld-Set/.github/workflows/coq.yml）

| 面 | Set 现役（实读） | Main coq93.yml（实取） | 差异级 |
|---|---|---|---|
| 触发 | push[main]＋pull_request＋dispatch（macos_only） | 同 | 同形 |
| 并发 | **per-ref 池 `cw-main-ci-${{ github.ref }}`＋cancel-in-progress: false**（:15-17·PR 认证与 main push 分池排队） | 单组 cw-main-ci-93＋cancel-in-progress:true | **异** |
| job | 双 job：coq-build（Windows 认证）＋coq-build-macos（macOS observation·:439-735） | 单 job（mac omit） | **异** |
| checkout | API tarball＋ref quiescence supersede gate（:39-88） | actions/checkout@v5 | **异** |
| 认证树 | **单 Live 树**（gate1/4/6/7/5/coqchk/gate2 全 on ConstructiveWorld_Live·order.txt 在 Live :199/:289） | vo 树认证＋Live 词扫 | **异** |
| build | 冷编（15 件·分钟级·:167-168）温控 pwsh guard | 14 道指纹 skip 并行 | **异** |
| coqchk | 共享闭包单趟 -o（ci_coqchk_live.sh）·mac 道内联循环 **echo COQCHK_EXIT/COQCHK_ALL_PASS**（:671-673） | parallel_chk.sh 14 路（词面产出待 retro 实证） | 部分异 |
| 双册 | root _CoqProject＋Live 双册（root order.txt 无·ls 实测） | root _CoqProject＋**Live 双册＋vo 双册** | Main 多一套 |
| 温控 | pwsh cpu_guard_v3.ps1（Win）＋本机 cpu_guard.sh（mac :538/:542/:667） | pwsh cpu_guard_v3.ps1 | 同形 |

判类谱词面同款面：GATE-BANNER-ABSENT 两仓同 token（Set :714／Main :565／
ci_triage.py:114）——ci_triage 的 E 族确证词面跨仓在位。

---

## 三、适配缺口逐项（rocqwash 器面 × Main CI·四面）

### 3.1 ci_triage 五族判类 × Main 步名（兼容表·判类谱 `tools/ci_triage.py:25-29`）

| Main 红步（实取步名） | 步名 regex 命中（:136-139） | 判类 | 级 |
|---|---|---|---|
| Build full tree (…)（:247） | build→CONTENT | **A-content-red** | 兼容 |
| coqchk full-tree certification (…)（:479） | coqchk→CONTENT/COQCHK_STEP | A／E 族对件 | 兼容 |
| Upload coqchk logs（:591）／Upload vo trust cache（:538）／Upload tree-stats（:382） | upload→NET/UPLOAD | B／E 族（E=上传红＋coqchk skipped·Main 步名两件齐→E 可发） | 兼容 |
| gate5 vo-binary quarantine (pre-coqchk…)（:411） | **含 coqchk 子串→CONTENT** | A（归内容红·语义上属内容红·可接受） | 兼容（词面搭便） |
| attest reconcile (…miss -> coqchk…)（:455） | **含 coqchk 子串→CONTENT** | A | 兼容（词面搭便） |
| Seed trust cache from local vo tree（:171） | cache→NET | B（若红·多为环境/路径面·B 兜底可接受） | 兼容 |
| **gate1 poison-token guard**（:102） | **零命中** | **UNRECOGNIZED 兜底**（无 log 时） | 兜底·不误断 |
| **gate3 cross-tree require-face diff**（:151） | **零命中** | **UNRECOGNIZED 兜底** | 兜底·不误断 |
| **gate4 comment guard (…artifact-only)**（:127） | **artifact→NET 先判**（判类序 步名 B 先于 步名 A·:473-478） | 红时**误归 B-netred** | **词面暗礁**（Set :120 同名同礁·非 Main 新增） |

- 日志词面（--logs·KEY_LOG_PATTERNS :109-123）：GATE-BANNER-ABSENT/公理总数/COQCHK_EXIT
  等在 Main 在位（:565/:571）；**Main 特有红词面（GATE2-AXIOMS-RED/GATE5-RED/
  ATT-RECON-FAIL/SINGLE-TREE-POISON/DEP-CASCADE）不入册→证据稀薄但归族不受阻**
  （步名 regex 兜住 A 面·gate1/gate3 萰 UNRECOGNIZED 人工指认——判类谱「不充谱」
  设计内诚实·:22-23/:493-495）。
- C 族词面（EXIT=134/Abort trap: 6 :132）系 Mac 判例形；Main Windows 炉断链日志形未
  实证——run 级批量判 C（同形内容红≥2 升 C·:498-510）不受影响。
- **结论：五族骨架即用**（真红不漏红——最坏 UNRECOGNIZED 响亮·不误断不充谱）；
  Main 形 canned fixtures 扩（§四·②）＋gate4 步名词面暗礁与 Main 红词面可选扩＝**小改**。
- 器面自证：`python3 -B tools/ci_triage.py --selftest` 本席实跑 **PASS rc=0**（20261112）。

### 3.2 pushci 推 Main（mirror-blind 面·`tools/pushci.py`）

- **合规面（即用）**：①remote URL 推导 ORG/REPO＝末两段（`repo_from_url` :264-284·host
  不限）→ hy7pc8gfmf-dotcom/ConstructiveWorld-Main ✓；②ghproxy 换路形门＝remote URL
  `https://github.com/` 前缀（`ghproxy_url` :287-292）→ Main 形合规即用；③netrc token
  对 Main **push_perm=True 实取**（§1.1）。
- **结构性缺口（最大缺口·中改）——PR 路线 mirror-blind 双重失配**：
  1. push 白名单 **[main]**（`coq93.yml:41-42`）→ pushci push topic-branch **零触发＝
     结构性无 run 可 watch**（非镜像问题·触发面就无）。
  2. PR 触发 run 的 head_sha＝merge commit（refs/pull/N/merge 生成面）≠pushed tip→
     watch 双咬合 head_branch＋head_sha（:942-944）**必失配**；refs/pull/* 不入 git
     镜像/推送面，`ls-remote refs/heads/<branch>`（:885-886）亦不可见——
     **任务书「refs/pull/* 不入镜像判例」实取面成立且叠加 merge-sha 失配**。
  3. pushci 无 workflow_dispatch 调用面（API 面＝runs GET/rerun POST/pulls GET/merge PUT
     四形 :1009-1011/:1071-1112）→ dispatch 路线也不通。
  → **pushci 兼容 Main 的唯一路线＝直推 refs/heads/main**（push 事件·head_sha=tip
  咬合成立）；PR 路线要么动 watch 匹配语义（器改·中改）要么立规程「PR 路线禁走
  pushci」（零码·建议后者先行）。
- **行为差异（小改）**：Main 单组 concurrency＋cancel-in-progress:true（:51-54）vs Set
  per-ref 不取消——Main 下新 push 会取消在飞 run→heal rerun 连坐循环面（cancelled 有
  步骤零红步=B 连坐→rerun→再被取消…至 --max-heal 耗尽 exit 1）。驯服面零器改：
  `--watch-max-rounds` 安全阀（:2024-2025·超帽 fail-loud 9）＋规程对表注记。
- **咬合窗注记（非现患）**：RUNS_QUERY per_page=30 单页（:152/:698-699 无分页续拉；
  ci_triage jobs 面有分页 :316-338 而 pushci runs 面无）——Main 炉 2880min 墙低频轮换
  现势 30 窗量级够用；busy 面扩窗＝小改候选·如实注记。
- 干跑先行铁律承 v36：真发首跑 `--dry-run` 先行（:1116-1157 计划面零副作用·v36 S6
  判据 HEAD/porcelain 前后恒同·`更新账.md:3608`）；Main 分支保护面本席未探（API 未
  探 protection·如实记未验）。

### 3.3 unclog --src 指 Main ConstructiveWorld_Live 的正本可用性

- **器面（即用）**：--src/--world/--rocq-cmd/--candidates/--probe-parallel 全参数化
  零硬编码（`tools/unclog.py:119` 用法节·:1089-1131 args·:959 --src 缺失 fail-loud 9）；
  K=1/2 同参双跑实证在账（`docs/perf-profile-v1.0-20261111.md:156-163` 1.87×·
  `更新账.md:3801` v43 双跑互证）。
- **正本面（现势不可用→中改前置·数据面工程）**：
  1. 本地无 Main 仓 checkout（§1.4 实取 ls 空）——--src 无正本可指。
  2. **世界（--world）无 CI 产线**：Main 认证面=vo 树（coq93.yml:247/:479·产出
     vo-trust-cache-windows-93 artifact 是 **vo 树 .vo** :538-545）——Live 树 .vo 世界
     无任何 CI 产线（对照本地 CW Live 世界 probe_world_v38 系 /tmp APFS clone 易失
     已清场·perf-profile:23-24/:3805）。
  3. 候选面须新采样：Main Live .v≥995（§1.4）vs 本地基线 27 件——不同候选面＝
     incomparable（`examples/baselines/README.md:64-66` 候选面四元组口径）。
  4. **基线域同名冲突（同名树的第二面）**：audit-<域> 域＝--src 基名（README §2 :22-26）
     ——Main Live 树基名同为 ConstructiveWorld_Live→与现役基线
     audit-ConstructiveWorld_Live-20261111.json **同域同名**→文件名碰撞＋跨树误比
     （同名树≠同域）——须断代换域名（如 audit-CW-Main-Live-…）或分目录·本档建议前者。
  → 中改＝物化正本（API tarball 或 clone）→世界构建→候选面采样（≤30 件规程
  perf-README:60-68）→首跑 audit 入账——**器零改·纯数据面工程**。

### 3.4 registry 双册路径差异（ConstructiveWorld_Live 同名树）

- 实取三面（§1.4/§二）：Set＝root _CoqProject＋Live 双册（root order.txt 无）；Main＝
  root _CoqProject＋**Live 双册＋vo 双册**——Main 比 Set 多 vo 套。
- 器面即用：`registry_union.py` --git 直读＋--git-path 显式指认（:785-791/:844）＋
  --main/--branch/--git 三面输入（:779-803·roadmap⑦ 溯源 `tools/registry_union.py:781-790`
  实读核符）；**GIT_PATH_DEFAULT＝repo-root order.txt/_CoqProject（:84）两仓皆失配**
  （root order.txt 两仓均缺·Set ls 实测/Main 404 实取）——**--git-path 必显式**：
  Set→`ConstructiveWorld_Live/order.txt`；Main→`ConstructiveWorld_vo/order.txt`
  （认证注册面·coq93.yml:305）或 `ConstructiveWorld_Live/order.txt`（Live 面）——
  **选哪一册＝跨仓语义对表项**（Set 认证面=Live 单树册·Main 认证面=vo 册·同名树
  下参数形一致但语义选册不同·非器缺）。
- 红线：registry 写面（--apply 落盘）在 Main 仓＝**跨仓越权面**（roadmap⑦ 风险列
  「适配器禁代仓越权写盘」·:90）——审计面（只读四账·registry_audit.py）即用；
  手术面（union --apply）候 Main 仓纪律对表后另议·本档不启。

---

## 四、结论＝适配工作量分级（即用 4／小改 3／中改 2）

| # | 适配项 | 分级 | 一句话依据 |
|---|---|---|---|
| 1 | ci_triage 五族判类骨架 × Main 步谱 | **即用** | A/B/D/E/C 骨架步名全兼容＋UNRECOGNIZED 兜底不误断＋GATE-BANNER-ABSENT 词面同款（§3.1·selftest 本席实跑 rc=0） |
| 2 | pushci 直推 refs/heads/main 路线 | **即用** | remote 推导/ghproxy 形门/netrc push 权三项实取合规（§3.2） |
| 3 | registry 双册审计面（只读） | **即用** | --git＋--git-path 显式指认零改·同名树参数形一致（§3.4） |
| 4 | unclog 器面旗标 | **即用** | 全参数化零改·正本一到位即可跑（§3.3） |
| 5 | pushci_scenarios canned 场景扩 Main 仓形 | **小改** | 路线图⑦验证方式明令「canned 场景扩仓形全过」（:92）——六场景×Main 步谱 fixtures |
| 6 | heal × Main concurrency 行为对表 | **小改** | 单组 cancel-in-progress:true 连坐循环面→--watch-max-rounds 安全阀＋规程注记·零器改可驯（§3.2） |
| 7 | ci_triage Main 红词面可选扩 | **小改** | GATE2-AXIOMS-RED/GATE5-RED/ATT-RECON-FAIL 等（＋gate4 artifact 暗礁词面裁量）入 KEY_LOG_PATTERNS 或 canned 覆盖（§3.1） |
| 8 | pushci PR 路线 watch 咬合 | **中改** | **最大缺口**——PR run head_sha=merge commit 必失配＋refs/pull/* 不入镜像＋push 白名单 [main] topic 零触发（§3.2·器改 watch 语义或立规程双轨） |
| 9 | unclog Main Live 正本可用性 | **中改** | 无本地 checkout＋Live 世界无 CI 产线＋候选面新采样＋基线域同名冲突断代（§3.3·纯数据面工程） |

**verdict＝即用 4／小改 3／中改 2。**

---

## 五、建议路径（承路线图⑦验证方式四步·:92）

1. **零码先行（半天级）**：Main 历史 run **retro-triage**（v44 Set 同法·
   `更新账.md:3820-3825`——cw_sentinel --loop 或 ci_triage --offline 逐条判类）——
   一石三鸟：判类吻合度对表＋Main 步名/日志词面真形实证（checkout 无名步的 API
   步名形·parallel_chk.sh 词面产出形·Windows 断链日志形——三项 §三注记的待实证面）。
2. **小改**：pushci_scenarios 六场景 Main 仓形 fixtures 扩（＋词面可选扩）——selftest/
   单套全过·三闸不动红。
3. **零码**：真仓 `--dry-run` 计划面零副作用（HEAD/porcelain 恒同·v36 S6 判据）——
   注意先物化 Main 本地 checkout（--repo-path 需真仓目录·即中改#9 的前置件之一）。
4. **真发首战**：**push 事件路线（refs/heads/main）**＋`--watch-max-rounds` 安全阀＋
   heal 分派 Main 对表——**避 PR mirror-blind 面**（中改#8 不阻首战）。
5. **unclog Main 正本（中改·独立排程）**：API tarball 物化→世界构建→候选面采样≤30→
   audit 首跑入账（**域断代换名**防同名域误比）→baseline_diff 同域轴。
6. **约束面**：凭据（netrc push 权）已实证在位；「积分静默窗」真发段错峰候令
   （roadmap §一·3·库内无在册锚点如实承）；Main 分支保护面真发前补探。

---

## 六、边界与如实记

1. 本席实跑：Main API 两脚本（rc=0）·ci_triage --selftest（rc=0）·Set 双册 ls。
   **未重跑**：pushci/unclog --selftest（在账 v36/v41 rc=0 引据·`更新账.md:3591`/:3740
   ——非本席实跑·如实记）。
2. **未探**：Main 分支保护面／API rate-limit 现值／scripts/parallel_chk.sh 脚本内容
   （yml 内直调·内容不在本席实取面）／pushci runs 面分页现患与否（低频轮换下非现患）。
3. 任务书给形两处不符已登记（§1.3）——以实取为准。
4. 本档零动码零写盘（rocqwash 工作树只增本档一文件）·禁触冻结八件/quad8/更新账.md ✓。
5. 引据行号：Main 仓两 workflow 以 /tmp 实取件为准（远端 ref=main HEAD 时点）·
   本仓器面以工作树现文件为准（v47 6217808 口径）。

## 七、本席自证字据（20261112·全部 cpu_guard 包裹）

| # | 动作 | 结果 |
|---|---|---|
| 1 | `python3 -B /tmp/fetch_main_ci.py`（netrc GET meta/workflows/contents 两 workflow 全文） | rc=0·REPO-META/workflows/FETCHED 六行响亮（§1.1） |
| 2 | `python3 -B /tmp/fetch_main_tree.py`（root 清单＋双册 PATH-PROBE＋Live 顶层） | rc=0·200/404 全列（§1.4） |
| 3 | `python3 -B tools/ci_triage.py --selftest` | rc=0·CI-TRIAGE-SELFTEST PASS |
| 4 | Set 仓 coq.yml 全文实读（735 行）＋双册 ls | 实读毕·root order.txt No such file |
| 5 | 本档写入后 `python3 -B tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash` | 见当轮账（drift 须=0 方合三闸基准·若幻引即修档重跑） |

---

## 八、小改三件执行记录（20261112·v48 勘形小改 3 波·工装席）

> 承 §五建议路径：**步 2**（Main 形 fixtures＋selftest Main 形判读矢）与
> **步 3**（pushci Main 干跑矢·零器改零旗标增零语义改）本波 done；**步 4**
> 真发候令只立一行不入本波（未执行）。全部实跑经
> `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120`
> 包裹。

- **步 2 done**（§五.2）：
  - 新件 `tests/fixtures/ci_triage_main_coq93.json`——canned Main coq93.yml
    真形 jobs：单 Windows job「Rocq 9.3 build + coqchk (self-hosted seed
    cache, Windows)」（workflow 名 **Main CI 9.3**·job 名系 coq93.yml:61
    display rename 真形；`_provenance` 键在册：coq93.yml:38/:61/:89-91/
    :102-591 行源＋runs-on [self-hosted, Windows]＋timeout 2880＋并发组
    cw-main-ci-93）；步名 16 枚按实取件 /tmp/mainwf_coq93.yml 逐枚誊录
    （v5 checkout→gate1→gate4→gate3→Seed→RAM guard→Build full tree→
    Generate tree-stats→Upload tree-stats→gate5→attest reconcile→coqchk
    full-tree certification→Upload vo trust cache→gate2→Upload coqchk
    logs）·绿样张全步 success。
  - `tools/ci_triage.py` --selftest 增〔九〕Main 形判读矢：fixture 16 步名
    逐枚咬合＋确定性字节恒同＋**兼容表 15 行机检**（真形单红步形·无日志·
    判类序步名 B 先于步名 A）＋E 族 Main 形两件齐形（Upload coqchk logs 红＋
    coqchk 步 skipped→E-coqchk-skipped·§3.1 E 行「两件齐→E 可发」实证）。
  - **机检钉判读（勘形 §3.1 兼容表的机械实证·向量已冻结）**：Build full
    tree／coqchk full-tree certification／gate5 vo-binary quarantine／attest
    reconcile→**A**（gate5/attest 系 coqchk 子串词面搭便·§3.1 同判）；checkout@v5／
    Seed trust cache／Upload tree-stats／Upload vo trust cache／Upload coqchk
    logs→**B**；gate4 comment guard→**B**（artifact 子串→步名 B 先判·§3.1
    词面暗礁行实证·Set :120 同款非 Main 新增）；gate3／gate2／RAM guard／
    Generate tree-stats→**UNRECOGNIZED 兜底**不误断。
  - **一处勘形散文勘误如实登记（机检 vs §3.1 散文）**：§3.1 gate1 行记
    「零命中→UNRECOGNIZED 兜底」——机械实测 gate1 步名「pre-build fail-fast」
    含 build 子串→CONTENT 搭便归 **A-content-red**（fix-content·poison-token
    红语义上属内容红·可接受同 gate5/attest 搭便）。「五族骨架即用」判据不受
    影响（不漏红·不误断·兜底行四枚非 §3.1 所记两枚）。
- **步 3 done**（§五.3·零器改——`tools/pushci.py` 本波零触碰）：
  - 新件 `tests/fixtures/pushci_scenarios/s7_main_dry_run.json`（branch=
    main＝refs/heads/main 直推路线·rocqwash-pushci-scenario/1 同形·expect
    git_calls=0/api_calls=0）。
  - `tests/test_pushci.py` 六场景壳→七场景（S7 Main 形 dry-run 矢：canned
    git-caller 空表＋injector flat verbatim·report.plan 三闸行
    [1] preflight.toolchain／[1] preflight.net／[1] preflight.gate4（未启形
    ＝直推 main 路线 base...branch 差集退化的正确缺省）＋[2] push 计划行
    （HTTP/1.1＋main）逐行断言；零 API 零 git 调用流水实证；tmp 仓
    before/after 恒同零副作用；幂等两跑字节恒同）。真仓 dry-run 未跑——
    前置件缺（§3.3/§五.3：Main 本地 checkout 须先物化）。
- **步 4 真发候令（§五.4·未执行·一行）**：

  ```bash
  python3 -B tools/pushci.py --repo-path /Users/apple/Desktop/ConstructiveWorld-Main --branch main --remote origin --watch-max-rounds 6 --max-heal 2 --json /tmp/pushci_main_first.json
  ```

  前置＝①Main 本地 checkout 物化（20261112 `ls -d /Users/apple/Desktop/*Main*`
  实测**不在卷**——本波任务书给形「/Users/apple/Desktop/ConstructiveWorld-Main
  在卷」与实取不符·按 §1.3 法如实登记）；②先行同令加 `--dry-run` 计划面零
  副作用（v36 S6 判据·HEAD/porcelain 前后恒同）；③`--watch-max-rounds` 安全
  阀压 §3.2 单组 cancel-in-progress:true 连坐循环面；④Main 分支保护面真发
  前补探（§六.2 未探如实承）。

## 九、执行字据（20261112·全部 cpu_guard 包裹·工装席实跑）

| # | 命令 | rc |
|---|---|---|
| 1 | `python3 -B tools/ci_triage.py --selftest` | 0（CI-TRIAGE-SELFTEST PASS·含〔九〕Main 形判读矢：coq93 真形 16 步咬合＋兼容表 15 行＋E 两件齐） |
| 2 | `python3 -B tests/test_pushci.py` | 0（17 过/0 红·S7 场景＋S7 幂等两跑字节恒同） |
| 3 | `bash tests/run_tests.sh`（全套·含全部器 selftest 例） | 0（58 过/0 红/1 略〔t_quad8_check 四仓副本群既有 SKIP〕/共 59 例） |
| 4 | `python3 -B tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash` | 0（VERDICT consistent·drift=0·本档 refs=46 unresolved=6 oos=0·本段写入后当轮实跑） |
| 5 | 禁触对账 | 冻结八件（certify/frozen8.py LEDGER8 在册八件）/quad8/更新账.md 零触碰 ✓；`tools/pushci.py` 零改动（步 3 纯测试面）✓；git 零写操作（未 commit）✓ |
