# 评估：push_gate 推窗四判据 × pushci preflight 归一可行性（v36 双门并立现状）

- **版本**：v1.0 · 2026-11-11（评估席·push-gate 单独成文·只读评估零改码）
- **任务书**：评估 `certify/push_gate.py` 推窗四判据 vs `tools/pushci.py` preflight
  的归一可行性（v36 登记的双门并立现状）；本轮一律只出文档·改造候令。
- **盘面实况**：rocqwash HEAD **8e124b3**（v45 render_events.py 路由入册）·工作树
  净（`git status --porcelain` 实跑 0 行）。任务书头注「v37 41e74b0」已过时——
  仓库当日在途推进 v37→v45；本文全部行号锚现势工作树（=HEAD 现势），与评估
  结论无涉（评估对象代码即现盘正本）。
- **先例旁证**：docs/ 同日已有 `push-gate-dual-door-assessment-v1.0-20261111.md`
  （先席独立成文·其案 A/B/C 对应本文乙/甲/丙·裁决同为「保持并立」）。两席
  独立同判＝旁证强化；本文判据清单/冲突面/成本锚全部为本席独立实取，不承袭。

---

## 0 处置上限：冻结名单核对（先查名单定权限）

`certify/frozen8.py:74-83` `LEDGER8` 账载八件：freeze_manifest.py /
mac_stmt_names.py / mac_stmt_scan.py / seam_probe.py / cpu_guard.sh /
gate4_comment_guard.py / verify_vo.py / wash_engine.py。

本席实跑 `python3 -B certify/frozen8.py --ledger`（经 cpu_guard 包裹）rc=0，
出账恰八行——**certify/push_gate.py 不在冻结八件在册**（机械证据：ledger 全册
无此名）。故处置上限＝nonfrozen-mutable（可建议小改造）；但任务书明令
**本轮一律只出文档**，甲/丙等改造形态一律以「候令」登记，本席零改码。

---

## 1 四判据实取清单（certify/push_gate.py·全文 633 行本席精读）

| 判据 | 判什么 | 证据源 | 代码锚 |
|---|---|---|---|
| c1 ci-idle | CI 在飞 run=0。status≠`completed` 一律保守计在飞（fail-closed） | `--runs-json`（预取 Actions runs JSON·本器自身零网络只判读）或 `--ci-capped-min N`（reflog 最近 `update by push` 距今 ≥N 分钟＋CI 时长封顶⇒在飞不可能）；**无证据=NOT-RUN=关窗** | `push_gate.py:109-151`（双源互斥校验 :219-222·零证据 NOT-RUN :151） |
| c2 local≥remote | fetch 后 `rev-list --count HEAD..<remote>/<branch>`（behind）==0；ahead 不设上限（本地领先正是待推态） | git 机械计数 | `push_gate.py:154-165` |
| c3 fetch-clean | ls-remote **前后双读同 sha**＋fetch rc=0＋远端 sha 是本地 HEAD 祖先（merge-base --is-ancestor）——窗内无人动云端 | 真远端只读操作（fetch/ls-remote）；fetch 失败（含网络死窗）=FAIL 窗如实关 | `push_gate.py:168-187` |
| c4 cert-green | 本仓认证绿机械复核：`bash tests/run_tests.sh` rc==0（`--suite` 可指认）；可另加 `--freeze-manifest` → freeze_manifest.py check 零漂移亦须 rc==0 | 退出码 | `push_gate.py:190-212` |

- 判序 **c3 先行**（fetch 落定 remote-tracking ref，c1 时间线/c2 计数方有据）
  → c1 → c2 → c4：`push_gate.py:235-239`。
- 结论面：四判据全 PASS ⇒ `push-window: OPEN` exit 0；否则 CLOSED exit 1
  （NOT-RUN=关窗·缺席旁证不计绿）：`push_gate.py:245-258`；退出码册 0/1/2/9
  （`:65-67`）。
- **只判窗不开推**：push 动作在调用方（`:30`）；window 全程只读（写域声明
  `:49-50`）。CLI 形参册实取（`:584-596`）：`--repo/--branch/--remote/
  --runs-json/--ci-capped-min/--freeze-manifest/--suite/--json`——**无
  `--check` 旗标**；只读态＝`window` 子命令本身（本席自证矢量 rc=0 实证其
  本地 bare 远端零网络全程可跑）。
- 同件另有 union-freeze/union-check（UNION v2 多世界清单 :263-396）与本评估
  无涉，不展开。

## 2 preflight 三闸实取清单（tools/pushci.py·全文 2086 行本席精读）

| 闸 | 判什么 | 不过即停 | 代码锚 |
|---|---|---|---|
| ① toolchain | subprocess `tools/toolchain_dyld_doctor.py --json`（--worker 缺省探测）→ verdict≠healthy（dyld 断链面） | `StopVerdict("toolchain", 1)` | `pushci.py:710-737` |
| ② net | subprocess `tools/net_probe.py --rounds 2 --interval S --stable-window`（双探稳窗）→ UNSTABLE | `StopVerdict("unstable", 1)` | `pushci.py:739-744, 750-800`（真模式 :787-795） |
| ③ gate4 预扫（可选 `--pre-scan-gate4`） | `git diff --name-only <base>...<branch>` 取 .v 变更件 → `verify/gate4_comment_guard.py --file` 逐件（rc 0=PASS/1=FAIL/2=复核）→ FAIL=0 才放行（REVIEW 响亮入账不拦） | `StopVerdict("gate4-block", 2)` | `pushci.py:746-748, 802-843` |

- 过闸后段 2-5：push（git 恒 4 调 get-url→rev-parse→push×3 发×45s→ghproxy
  换路×2 发→ls-remote 远端 tip 复核：`:17-24, 847-908`）→ watch（head_branch+
  head_sha 咬合·status-only：`:912-971`）→ heal（ci_triage 判类·B/E 有界
  rerun·A 禁代修·`:973-1023`）→ verdict±merge。
- 关键性质：`--timeout` 缺省 120s 全部真子进程防挂（超时杀＋fail-loud 9）：
  `pushci.py:197-207, 2026-2028`；「纯 preflight 模式零 git 调」`:1166-1167`；
  verdict 封册七态 `:157-165`；preflight 零 API（runs 查询在 watch 段 :930）。
- 本席实跑 `--dry-run` rc=0：计划恰三闸（toolchain/net/gate4-未启）·无窗闸·
  零 git 零 API 零工具子进程——三闸结构的机器实证。

## 3 对照矩阵：谁覆盖谁 / 谁独有 / 冲突面

### 3.1 判据覆盖矩阵（7 个判据面·**无一重合**）

| 判据面 | push_gate window | pushci preflight | 覆盖关系 |
|---|---|---|---|
| CI 在飞=0（c1） | ✅ `:109-151` | ❌ 推前不查在飞（watch 段只看推后新 run `:930-956`） | **push_gate 独有** |
| behind=0（c2） | ✅ `:154-165` 事前判 | ❌ 无预扫；等价后果由 push 时 git 非快进拒绝**事后**兜底（rc≠0→5 发徒劳→unstable `:863-880`） | **push_gate 独有**（pushci 仅事后兜底） |
| 窗内无人动云端（c3） | ✅ `:168-187` | ❌（push 后 ls-remote `:885-899` 是远端 tip 取证，非判窗） | **push_gate 独有** |
| 本地认证绿（c4） | ✅ `:190-212` | ❌ 本地不跑套件；绿由远端 CI watch+heal 判 `:912-1023` | **push_gate 独有**（哲学异：本地先绿 vs 远端后判） |
| 工具链健康（doctor） | ❌ | ✅ `:710-737` | **pushci 独有** |
| 网络稳窗（net_probe 双探 --stable-window） | ❌（c3 只证连通＋干净·无时序稳窗） | ✅ `:739-744, 787-795` | **pushci 独有** |
| .v 头注守卫预扫（gate4） | ❌ | ✅ `:746-748, 802-843`（可选） | **pushci 独有** |

任务书提示双侧代码证实：**pushci 无 behind=0 检查**（stage_push 仅 rev-parse
在位性 `:852-859`）；**push_gate 无网络稳窗**（c1-c4 无 net_probe 调用）。
互连现状：`grep push_gate tools/pushci.py` **零命中**（本席实跑）——双门零
互连，纯并立。

### 3.2 冲突面（同一物理条件·两门处置异）

1. **behind>0**：push_gate=事前 CLOSED exit 1（c2 计数＋c3 祖先链双证）；
   pushci=事中 push rc≠0→重试 5 发（3×45s＋ghproxy 2 发≈3 分钟徒劳）→
   verdict=**unstable**（语义归「网络不稳」而非「时机未到」）exit 1
   （自证矢量〔十二〕实锚 `:1746-1769`）。同一条件：时点/verdict 名/成本
   三重不同。
2. **网络死窗**：push_gate c3 fetch 失败=FAIL 关窗（`:174-176`）；pushci
   net UNSTABLE=禁发射 unstable。都禁动·但账面册不同（OPEN/CLOSED vs 七态
   verdict）·且 push_gate 无稳窗概念、pushci 无窗内干净概念——互补非重复。
3. **子进程时限**：pushci `--timeout` 缺省 120s 超时杀 fail-loud 9
   （`:197-207`）；push_gate c4 直跑全套件无时限（`run_out :94-100` 无
   timeout 形参）。方案甲下套件>120s 必被杀报 9——两器时限语义硬冲突。
4. **git 调用序契约**：pushci 恒 4 调（docstring `:24`；selftest 断言恰 4 调
   `:1497-1502`）；push_gate window 引入 ls-remote×2＋fetch＋rev-list×2＋
   merge-base＋reflog ≈7 调。方案甲破坏 4 调恒序＝全套 canned 矢量翻新。
5. **preflight 性质**：现 preflight 零 git 零 API（`:1166-1167`）；方案甲第
   4 闸（c3）必触真远端 fetch——性质改变须文档/矢量/夹具全套联动。

## 4 归一方案建议书（三案·迁移成本逐条锚码）

### 案甲 — pushci preflight 增第 4 闸（subprocess 调 push_gate 只读态）

**只读前提裁决**：push_gate CLI **无 `--check` 旗标**（形参册实取 `:584-596`）；
只读态＝`window` 子命令本身（全程只读 `:49-50`·push 在调用方 `:30`·本席
selftest rc=0 实证）。故「若其 CLI 支持只读」答案为**支持·但形为 window 子
命令非 --check**——方案甲的调用形应为 `python3 -B certify/push_gate.py window
--repo <repo_path> --branch <branch> …`。

**技术可行性**：push_gate.py 自身可零改动（判据正本不动·编排调用合
pushci「编排零新引擎」字面 `:5-6`）；pushci 侧 `_run_py` 子进程形与 window
`--json` 出账形兼容（`:659-676`）。**但四座成本山实锚如下**：

- **a) c1 证据死锁（无两全解）**：无 `--runs-json`/`--ci-capped-min` →
  c1=NOT-RUN → CLOSED exit 1（`:151`·自证矢量「零证据 NOT-RUN 关窗」rc=0
  实证）→ 第 4 闸恒关。解法一：pushci preflight 预取 runs JSON=新增真 API
  调（现 preflight 零 API·token 凭据面提前引入）；解法二：`--ci-capped-min`
  依赖 reflog `update by push` 条目（`:138-142`）——**新枝首推（pushci 主
  用例）必无条目 → NOT-RUN 死锁**。
- **b) c4 时限冲突**：c4 直跑全套 `tests/run_tests.sh`（分钟级）vs pushci
  `--timeout` 缺省 120s（`:2026-2028`）→ 必 9 被杀。放宽 timeout=自动管线
  每推付全套分钟级；改 `--suite` 指轻量脚本=判据掏空（认证绿名存实亡）。
- **c) 契约联动面**：verdict 封册需第八态（现七态 `:157-165`·selftest 封册
  断言 `:1811-1813`）＋report schema `rocqwash-pushci/1` 扩展＋git 4 调恒序
  断言翻新（`:1497-1502`）＋dry-run 计划行＋tests/fixtures/pushci_scenarios
  ＋README-cw/白皮书/嵌段②文档面全套对齐。
- **d) 原子性幻觉**：窗判过≠推时窗仍开（c3 前后双读设计自证窗非原子
  `:170-183`）——嵌进门 A 造「过闸即安全」错觉；两门并立各出各账
  （window.json＋pushci report）证据不混叠。

**裁决：技术可行·默认开闸净负（c1 死锁＋c4 成本无两全）·可选旗标形不归一
反扩面——不推荐**（与先例文档案 B 裁决一致）。

### 案乙 — 保持双门＋文档写明分工（push_gate=推送授权闸·pushci=执行流水线）

**现状即此形·规约已在档**（本席逐一实查）：
- README-cw.md:60-63：「套件绿/behind=0 等推窗四判据不在此册·过闸纪律仍归
  `certify/push_gate.py`」（grep 实证在位）；:188「双门并立——推窗四判据×
  发射闸」。
- wrapper/push_gate_rq.sh 在位（ls 实证）——门 B 独立调用面已适配。
- cw.sh 对 push_gate **零路由**（grep 实证零命中）——门 B 不进主线一键，
  分工边界由消费面自然维持。
- pushci docstring 自陈「编排而非重造」（`:5-6`）——判据正本留在 certify/
  正是「零新引擎」的实质。

**迁移成本：零代码**（本轮仅落本文档）。残余风险（如实登记·案乙固有）：
无机械闸强制工作流先判门 B——pushci 单跑即发射，窗纪律靠文档与工作流嵌段
约束；此系「推窗纪律由调用方显式发起」哲学的自洽代价，非缺口。

**裁决：推荐**。判据集零交（§3.1）＋问题异质（「该不该现在推」vs「环境能不能
发射」）⇒ 归一收益不存在、成本全是实打实（§4 甲/丙）——并立即正解。

### 案丙 — 推窗判据下沉为库函数双器 import

**冻结面核对**：push_gate.py 非冻结（§0 实跑证据）→ 无冻结障碍；但其
import 冻结件 freeze_manifest 只读复用 tier1_lines/tier2_of（`:79-88`）——
重构 push_gate 须保冻结接口原样（tier1/tier2 口径函数签名零改动），且
push_gate md5 变更牵动其自证矢量组（`:401-567`）与 wrapper 注入形。

**成本清单**：c1-c4 抽库改 certify 深件结构→双器 import 后同一判据两个
消费面=漂移温床；tools/ 与 certify/ 无包结构（pushci 现只 import 同目录
`_http_backoff` `:174-176`）→ 须 sys.path 注入或包化=结构改造；**c1 证据
模型与 c4 成本两座山原样照搬**（库化不解决语义相克——判据归属变了，
「NOT-RUN=关窗」vs「探针现跑现判」的模型冲突还在）。

**裁决：改冻结邻接面风险中＋漂移面扩张＋核心矛盾不消——否决**（与先例
文档案 C「唯一明确劣解」同判）。

---

## 5 结论与建议

**倾向：案乙（保持双门＋文档分工）**——本轮落地即本文档；甲/丙登记为候令
（若主会话日后钦定甲·须先解 §4 甲 a/b 两座山：c1 证据预取与 c4 时限）。

四条理由：
1. **判据零交**（§3.1 实锚 7 面无一重合）——归一要消的「重复」不存在；
2. **成本不对称禁嵌**（c4 分钟级套件 vs 每推自动管线的 120s 时限帽）；
3. **证据模型相克**（门 B「旁证缺席即关窗」的 fail-closed 诚实律 vs 门 A
   「探针现跑现判」——c1 塞进门 A 要么新枝死锁要么缺省绿稀释诚实律·flat
   形缺省绿先例 `:766-774` 不可援引到 c1）；
4. **判据单一正本=唯一无漂移形态**（四判据正本只在 certify/push_gate.py
   一处·pushci 零引用 grep 实证——现状并立已是该约束下最优）。

## 6 禁改说明与证据面

**禁改声明**：本评估零代码变更——push_gate.py / pushci.py / frozen8.py /
wrapper / cw.sh / tests / README 全部未动；冻结八件（frozen8.py LEDGER8 在册
八件）与 quad8 域/更新账.md 遵禁触令**未读未动**（更新账相关结论以任务书
＋pushci.py:3「v36 旗舰·20261111 入账」＋README-cw.md:188 为证）。

**本席实跑证据**（2026-11-11·全部经 `bash /Users/apple/Desktop/ConstructiveWorld/
cpu_guard.sh -MaxWaitSec 120` 包裹·FRONT 档实跑）：

| 检查 | 命令 | 实测 |
|---|---|---|
| 冻结名单 | `python3 -B certify/frozen8.py --ledger` | rc=0·出账恰八行·push_gate 不在册 |
| 门 B 自证 | `python3 -B certify/push_gate.py --selftest` | rc=0·UNION 六判＋window c1 双源/c2 behind/c4 红套件/零证据 NOT-RUN 四判全过（本地 bare 远端零网络） |
| 门 A 自证 | `python3 -B tools/pushci.py --selftest` | rc=0·八矢量＋flat 咬合＋韧性层＋CLI 四码全过（零真网络零真 push 零编译） |
| 门 A 三闸结构 | `python3 -B tools/pushci.py --repo-path <仓> --branch master --dry-run` | rc=0·计划恰三闸无窗闸·零副作用 |
| 双门零互连 | `grep -n push_gate tools/pushci.py` | 零命中 |
| 分工在档 | `grep -n push_gate README-cw.md`／`grep push_gate cw.sh`／`ls wrapper/push_gate_rq.sh` | README:60-63,188 在档·cw.sh 零命中·wrapper 在位 |
| 盘面状态 | `git rev-parse --short HEAD`＋`git status --porcelain` | 8e124b3（v45）·工作树净 0 行 |

**码面精读**：certify/push_gate.py 全文 633 行；tools/pushci.py 全文 2086 行；
certify/frozen8.py 全文 408 行；docs/push-gate-dual-door-assessment-v1.0-
20261111.md 全文（先例旁证）。

**未实跑项（如实声明）**：①push_gate window 对真远端的线上判窗（需真网络
凭据·本席纪律零真网络；行为已由自证矢量本地 bare 远端覆盖）；②c4 对本仓
套件的实跑基线（本席未复跑；先例文档同日实测 52 过/0 红/4 略 rc=0 可资参考，
本席不背书其数）；③更新账.md 依禁触令未读——「v36 登记」以任务书与在盘
docstring 为证。以上三项均不影响判据对照与方案裁决（全部锚在盘代码与
自证矢量）。
