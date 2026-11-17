# push_gate 推窗四判据 × pushci preflight 发射闸 — 双门归一评估报告

- **版本**：v1.0 · 2026-11-11（rocqwash v40 496ebdf 后工作树·评估席单独成文）
- **任务书**：v39/v40 更新账排程项「push_gate.py 推窗四判据与 pushci preflight 的
  归一评估（双门并立现况如实注）」（`更新账.md:3609`、`更新账.md:3700`）
- **评估域**：`certify/push_gate.py`（window 子命令·推窗四判据）与
  `tools/pushci.py`（五段管线第 1 段 preflight·发射闸）两扇门的判据面、重叠面、
  差异面、归一可行性三案与建议案。
- **纪律声明（只评估不动码）**：本报告零代码变更——两器、wrapper、cw.sh、
  tests、README 系列在本评估任务下一概未动（本席同轮另有一项钦定的
  cw_sentinel 护栏修复，属任务书另一件，与本评估互不相涉）。全部结论只锚
  在盘代码与实跑证据，行号锚 496ebdf 后工作树现势。

---

## 1 两门各判什么

### 1.1 门 B：push_gate window — 推窗四判据（时机与凭证）

正本 `certify/push_gate.py:8-30`（docstring）＋实作 `:109-212`。承战役推送窗
铁律（`push_gate.py:9` 引 ConstructiveWorld 战役 wf_land.dwf.ts:40）：
「①runs in_progress=0 ②本地≥云端 ③fetch 干净 ④认证绿已坐实」。机械落地：

| 判据 | 判什么 | 证据源 | 锚 |
|---|---|---|---|
| c1 ci-idle | CI 在飞 run=0。status≠`completed` 一律保守计在飞（fail-closed） | `--runs-json`（预取 Actions runs JSON·**本器自身零网络**只做判读）或 `--ci-capped-min N`（reflog 最近 `update by push` 距今 ≥N 分钟＋CI 时长封顶 ⇒ 在飞不可能） | `push_gate.py:109-151` |
| c2 local≥remote | fetch 后 `rev-list --count HEAD..<remote>/<branch>`（behind）==0；ahead 不设上限（本地领先正是待推态） | git 机械计数 | `push_gate.py:154-165` |
| c3 fetch-clean | ls-remote **前后双读同 sha**＋fetch rc=0＋远端 sha 是本地 HEAD 祖先（merge-base --is-ancestor）——窗内无人动云端 | 真远端只读操作（fetch/ls-remote） | `push_gate.py:168-187` |
| c4 cert-green | 本仓认证绿机械复核：`bash tests/run_tests.sh` rc==0（`--suite` 可指认）；可另加 `--freeze-manifest` 冻结件零漂移亦须 rc==0 | 退出码 | `push_gate.py:190-212` |

- 判序：**c3 先行**（fetch 落定 remote-tracking ref，c1 时间线/c2 计数方有据）
  → c1 → c2 → c4（`cmd_window`·`push_gate.py:235-239`）。
- 结论：四判据全 PASS ⇒ `push-window: OPEN` exit 0；否则 CLOSED exit 1——
  **NOT-RUN＝关窗·缺席旁证不计绿**（诚实律·`push_gate.py:29`、c1 零证据
  NOT-RUN `:151`）。退出码册 0/1/2/9（`push_gate.py:65-67`）。
- **只判窗不开推**：push 动作在调用方（`push_gate.py:30`）；window 全程只读
  （写域声明 `push_gate.py:49-50`·fetch/ls-remote 均远端只读操作）。
- 在役形：手动老链（`README-cw.md:60`）＋适配层 `wrapper/push_gate_rq.sh`
  （window 注入 `--repo <仓根> --suite <仓根>/tests/run_tests.sh` 消灭 cwd
  敏感·无参调用 exit 2 禁 surprise 网络·`push_gate_rq.sh:60-63,71-72`）。

### 1.2 门 A：pushci preflight — 发射闸（环境能不能发射）

正本 `tools/pushci.py:7-16`（docstring）＋实作 `stage_preflight :703-748`。
五段管线（preflight→push→watch→heal→verdict±merge）第 1 段·禁发射律代码化：

| 闸 | 判什么 | 不过即停 | 锚 |
|---|---|---|---|
| ① toolchain | `tools/toolchain_dyld_doctor.py` subprocess → verdict≠healthy（dyld 断链面） | `StopVerdict("toolchain", 1)` | `pushci.py:710-737` |
| ② net | `tools/net_probe.py --rounds 2 --interval S --stable-window` subprocess → UNSTABLE（双探稳窗·单探禁发射由四器自带·本器只认其裁决） | `StopVerdict("unstable", 1)` | `pushci.py:739-744,787-795` |
| ③（可选）gate4 预扫 | `--pre-scan-gate4`：git diff `<base>...<branch>` 取 .v 变更件 → `verify/gate4_comment_guard.py` 逐件 → FAIL=0 才放行（REVIEW 响亮入账不拦） | `StopVerdict("gate4-block", 2)` | `pushci.py:746-748,802-843` |

- 过闸后段 2-5：push（git 四调序 get-url→rev-parse→push×3 发×45s→ghproxy
  换路×2 发→ls-remote 远端 tip 复核·`pushci.py:17-24,847-898`）→
  resolve+watch（head_branch+head_sha 咬合·`pushci.py:25-30,912+`）→
  heal（ci_triage 判类分派·有界 rerun 帽 3·A 族内容红禁代修·`pushci.py:31-42`）
  → verdict±merge。
- 退出码册：0=success/dry-run；1=heal-exhausted/unstable/toolchain；
  2=fix-content/gate4-block/用法错；9=目标缺失（`pushci.py:101-104`）。
  verdict 封册七态（`pushci.py:118-119`）。
- `--dry-run`＝只打计划零副作用（零 git 零 API 零工具子进程·`pushci.py:89`；
  破坏面矩阵 P1 行以 api_calls/git-caller 双流水皆空实证）。
- 主线在役形：`cw.sh pushci` 路由（`cw.sh:218`·二十工具册 `cw.sh:232`），
  工作流嵌段②（`examples/workflows/step-pushci.md`）。

---

## 2 重叠面（两门真正共判的很少）

1. **同一物理对象**：两门最终都服务同一次 `git push`——门 B 判「此刻开不开窗」，
   门 A 过闸后亲自执行 push。判的对象同、动作的归属不同（B 只判不开推·A 判
   且推）。
2. **同款 fail-closed 姿态**：门 B 无证据=NOT-RUN=关窗（`push_gate.py:29,151`）；
   门 A 双闸器 verdict≠healthy/UNSTABLE=禁发射（`pushci.py:737,742`）。两门
   都禁「证据缺席按绿算」。
3. **同款只读姿态**：门 B 写域声明全程只读（`push_gate.py:49-50`）；门 A
   preflight 段只跑本地探针子进程＋net_probe 只读 GET，对仓树/远端零写
   （report/--json 出调用方显式指认路径）。两门的写域纪律同源（只写显式
   指认出账·零 surprise 写）。
4. **c2/c3 的事后兜底在 push 自身**：push 段真推时 git 自带非快进拒绝＝
   behind>0/窗内云端被动的最终机械兜底——但那是**发射失败后**才知道；门 B
   的价值正在把徒劳发射省在事前。这是两门唯一实质「重叠」的判据邻接面，
   且是兜底关系非重复判据关系。
5. **判据集合零交**：c1-c4 与 doctor/net-probe/gate4 五个判据**无一重合**
   （§3.2）。所谓双门重叠是纪律层（fail-closed/机械证据/只读）的重叠，
   不是判据层的重复劳动。

---

## 3 差异面

1. **回答的问题不同**：门 A＝「环境能不能发射」（工具链/网络稳窗/头注守卫）；
   门 B＝「此刻该不该推」（CI 空闲/本地领先/窗内无人动/认证绿）。白皮书 §4
   定语：「两扇门，各判各的，互不替代」
   （`docs/workflow-integration-whitepaper-v1.0-20261111.md:163-201`）。
2. **证据模型不同**：门 A 的证据恒在场（doctor/probe/gate4 真模式必跑必出
   verdict·形坏 fail-loud 2）；门 B 的 c1 证据**可选**且缺席即关窗
   （NOT-RUN 语义·`push_gate.py:141-151`）——推窗是「旁证齐了才开」的
   判定，发射闸是「探针现跑现判」的判定。
3. **成本结构不同**：门 A 三闸秒级；门 B 的 c4 直跑全套 `tests/run_tests.sh`
   （本席本轮实测 52 过/0 红/4 略·rc=0——分钟级体量）＋可选冻结件对账。
   成本不对称是结构性的，不是实现偷懒。
4. **网络姿态不同**：门 B 的 c3 必须触真远端（fetch/ls-remote·只读）；门 A
   的 preflight 本段零 git 零远端调（doctor 本地·net_probe 打探针端点）。
   适配层因此立「无参调用禁绝」契约防 surprise 网络（`push_gate_rq.sh:60-63`）。
5. **退出码与账面不同**：门 A 闸败折进五段 verdict 封册七态＋report
   `stages.preflight{toolchain,net,gate4?}`（`pushci.py:107-111`）；门 B 自有
   OPEN/CLOSED 0/1 册＋逐判据 PASS/FAIL/NOT-RUN 行＋可选 window.json
   （`push_gate.py:241-258`）。两册各自在档·互不翻译。
6. **新鲜度时刻不同**：正典串行序（白皮书 §4·门 B 先判窗→门 A 再跑管线）
   下，门 B 的 c3 双读证据在门 A 真推时已是数秒旧账——c3 自己的前后双读
   设计说明作者明知窗非原子；唯一能原子化的形态是「判窗者亲自 push」，
   而两门现在都不是（见 §4 案 B 的幻觉风险）。
7. **消费面不同**：门 A＝主线一键（cw.sh 路由＋工作流嵌段②·verdict 可分流
   ＋heal 有界自愈）；门 B＝手动老链＋适配层＋工作流前置判窗步骤。cw.sh
   二十工具册**无** push-gate 路由（`cw.sh:232`）——门 B 靠 wrapper 与文档
   在册，不进主线一键。
8. **模块姿态不同**：门 A＝tools/ 编排胶水（四器 subprocess·零新引擎·
   `pushci.py:5-6`）；门 B＝certify/ 深件（机械判据＋UNION v2 多世界清单
   同件·冻结向量组自证·适配层包锚）。**push_gate.py 不在 frozen8 冻结八件
   在册**（本席实测 `frozen8.py --ledger` 全册 grep 计数=0）——在役可修但
   本评估不动。

---

## 4 归一可行性三案

### 案 A — 保持并立·各判各的（现状固化）

**形态**：两器零改动。白皮书 §4 正典串行序（先门 B 判窗·OPEN 才进门 A）
＋README-cw 诚实旁注（`README-cw.md:60-63`「套件绿/behind=0 等推窗四判据
不在此册·过闸纪律仍归 certify/push_gate.py」）＋嵌段②注记（「两扇门…
互不替代」`step-pushci.md:159-161`）即现状的全部规约。

- 收益：零代码零回归面；判据归属单一（四判据唯一正本在 certify·判据无
  第二份实现＝无漂移面）；c1 证据「调用方显式发起」的契约（适配层契的 3）
  保持——推窗纪律由人/工作流按仓况选择证据源，器不越权猜。
- 代价：要双门全查的调用方需串行两条命令（工作流嵌段已给正典序·人手
  老链用户需自读文档）；pushci 单跑仍可不判窗（见 §5 残余风险）。
- 裁决：**可行·现状即稳态**。

### 案 B — pushci preflight 调 push_gate window 作闸（编排放大一格）

**形态**：preflight 增第④步 subprocess `python3 -B certify/push_gate.py
window --repo <repo_path> --branch <branch> [--runs-json …]`，exit 0 才过闸；
push_gate 仍系判据唯一正本（编排调用非重实现·合「编排零新引擎」字面）。

逐条过堂：

- **c4 成本并入每次发射**：c4 直跑全套套件（§3.3）——嵌进 pushci＝每次
  真推前付全套分钟级时长；改 `--suite` 指轻量脚本＝判据掏空（认证绿名存
  实亡）。**无两全**。
- **c1 证据在 pushci 侧结构性缺席**：c1 双源（runs-json/ci-capped-min）
  pushci 一概无旗标可透传；且 ci-capped-min 时间线证据要求 reflog 有
  `update by push` 条目（`push_gate.py:138-142`）——**新枝首推（pushci 的
  主用例）必无此条目 → NOT-RUN → CLOSED**：默认开闸＝pushci 对新枝永闭。
  要解须给 pushci 加 runs-json 预取旗标＋文档面全套同步——改动已出
  「一格编排」量级。
- **verdict 封册要第八态**：CLOSED 折进七态无位可归——映射 unstable=1 是
  语义扭曲（unstable 系网络/推路不稳非时机未到）；新态=report schema
  `rocqwash-pushci/1` 扩展＋README-cw/白皮书/嵌段②/CHANGELOG/doc_lint
  所查面全套对齐＋tests/fixtures/pushci_scenarios 与 t_pushci 15 矢量、
  矩阵 P1（dry-run `stages == {}` 断言）逐面复核。
- **原子性幻觉**：窗判过≠推时窗仍开（§3.6）——把门 B 嵌进门 A 会造出
  「过闸即安全」的错觉，而 c3 双读设计恰恰自证窗非原子。两门并立时各出
  各账（window.json＋pushci report），嵌套后证据反而混叠。
- **门 B 并不因此退役**：手动老链（README-cw:60）合法在册——push_gate
  window 仍须独立可调；同一判据集出现两条调用面（pushci 内嵌＋独立 CLI）
  ＝doc_lint 日日对抗的漂移温床。
- 裁决：**技术可行·默认开闸净负·可选旗标形不归一反扩面**。归一目标
  （一个入口判全）达不到，只把两扇门变成一扇半。

### 案 C — 判据合并（一扇大门·单一器面）

**形态**：或把 c1-c4 重实现进 pushci preflight，或把 doctor/net-probe/gate4
并进 push_gate window——判据单器全判。

- 向 pushci 合并＝四判据第二份实现：违背「编排零新引擎」的实质（判据
  重实现即新引擎）；certify 正本仍在（老链在册）→ 双正本漂移面；
  c4 成本与 c1 缺席两座山原样照搬（同案 B 前两条）。
- 向 push_gate 合并＝certify 深件姿态改变：只读 window 变成跑 doctor/
  probe/gate4 子进程的编排面（certify 件从未有工具编排职能·UNION 清单
  同件的冻结向量组语义被搅动）；pushci 老调用面仍须在册 → 同样双正本。
- 两向共同：两器的既有 CLI、文档、测试矢量、消费面一个都删不掉——合并
  只增不减。**归一评估三案中唯一明确劣解。**
- 裁决：**否决**。

---

## 5 建议案与理由

**建议案：A — 保持并立·各判各的。** 理由四条：

1. **判据零交·问题异质**（§2.5/§3.1）：两门没有一条重复判据，回答的是
   「能不能发射」与「该不该现在推」两个不同问题——归一的收益（消重复）
   在此不存在，归一的成本（c4 并入每推·c1 新枝死锁·封册第八态·schema/
   文档/夹具全套联动）全是实打实的。无利有损，不归一。
2. **成本结构禁嵌**（§3.3/§4-B）：c4 全套套件的分钟级体量只适合「人要开窗
   时付一次」，不适合嵌进每次发射的自动管线。案 B/C 的所有形态都绕不开
   这座山。
3. **c1 证据模型与 pushci 语义相克**（§4-B）：推窗判据的核心是「旁证缺席
   即关窗」的 fail-closed 诚实律；发射闸的核心是「探针现跑现判」。把前者
   塞进后者，要么造新枝首推死锁，要么用缺省绿注记把 NOT-RUN 稀释掉
   （pushci flat 形 preflight 缺省绿已有先例 `pushci.py:766-774`——同款
   手法用在 c1 上＝诚实律失守）。
4. **判据单一正本＝唯一无漂移形态**（§4-B/C）：四判据正本只在 certify/
   push_gate.py 一处，门 A 不复判、门 B 不复跑探针——「重复判一次是浪费，
   漏判一扇是洞」的既定口诀（白皮书 §4 要点 1）正是案 A 的规约现成文。
   现状双门并立＋正典串行序已是该约束下的最优解。

**规约现状确认（均已在档·本评估零新增义务）**：白皮书 §4 正典串行序与
三要点（`workflow-integration-whitepaper-v1.0-20261111.md:163-201`）；
README-cw 诚实旁注（`README-cw.md:60-63`）；嵌段②两门互不替代注记
（`step-pushci.md:159-161`）；适配层注入/禁 surprise 网络契约
（`wrapper/push_gate_rq.sh:60-63,71-72`）。v39 排程本评估时注「双门并立
现况如实注」（`更新账.md:3609`）——本评估结论：**并立即正解·如实注已足·
无须改码**。

**残余风险（如实登记·案 A 固有）**：无任何机械闸强制工作流先判门 B——
pushci 单跑即发射，窗纪律靠文档与嵌段约束。此系「环候窗纪律由调用方显式
发起」哲学（适配层契的 3 同源）的自洽代价，非缺口；若主会话日后要机械
强制，案 B 是唯一不改判据正本的路径，但须先解 §4-B 四条（尤其 c4 成本
与 c1 新枝死锁）再议。

---

## 6 证据面（本席实跑·2026-11-11）

| 检查 | 命令（经 `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120` 包裹） | 实测 |
|---|---|---|
| 门 B 自证 | `python3 -B certify/push_gate.py --selftest` | rc=0·UNION 六判＋window c1 双源/c2 behind/c4 红套件/零证据 NOT-RUN 四判全过 |
| 门 A 自证 | `python3 -B tools/pushci.py --selftest` | rc=0·八矢量＋flat 咬合＋韧性层＋CLI 四码全过（零真网络零真 push 零编译） |
| 冻结册核对 | `python3 -B certify/frozen8.py --ledger` 输出 grep `certify/push_gate` | 计数=0（push_gate 不在冻结八件） |
| 套件现状基线 | `bash tests/run_tests.sh`（本席同轮护栏修复回归一并实证） | 52 过/0 红/4 略·rc=0（56 例·四略系正本环境缺·真本机全跑） |

**码面精读**：`certify/push_gate.py` 全文 632 行（window 四判据实作 :109-258
＋UNION v2 ＋自证）；`tools/pushci.py` docstring 与管线关键段（:1-120 头注
退出码册·:703-843 preflight 三闸·:847-908 push 段·:1116-1180 run 入口）；
`wrapper/push_gate_rq.sh` 全文；`cw.sh` 路由与工具册；`README-cw.md:40-80`；
`docs/workflow-integration-whitepaper-v1.0-20261111.md` §4；`examples/
workflows/step-pushci.md:156-167`；`更新账.md` 排程锚。

**未实跑项（如实声明）**：pushci 真发段与 push_gate window 对真远端的
线上判窗（需真远端凭据与真网络·用户面——本席纪律零真网络）；c4 对本仓
套件的 window 内递归实跑（判据行为已由 push_gate 自证矢量「c4 红套件→
CLOSED」与本席直跑套件基线双侧覆盖）。两者命令形均以在盘代码为正本给出，
运行时行为未经本席线上验证。
