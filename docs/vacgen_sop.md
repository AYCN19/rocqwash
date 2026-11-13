# SOP · vacuity 探针工具化与判读分档规程 / SOP: Vacuity Probe Tooling and Verdict Grading (vacgen)

> **Header note (English)**
> **Job ID**: vacgen-20261112 · work-order phase 1 · spec-seat deliverable · zero-compile (this scroll regulates; it fires no build itself).
> **Statement face**: this scroll turns the five generalization crafts measured effective in the vacmain v2 four-fold-convergence audit (source receipt §四) into executable steps, each with a machine-checkable verdict surface; it fixes the five-grade verdict law for probe results and the limited-form, three-bounds statement template; it drafts the independent-repo candidate README skeleton.
> **Verdict semantics**: strong red = statement-face break, form registration only; weak red = nonempty evidence; refutation green = vacuity alert (highest level); boundary green = positive machine check; absence = pending (a formalization-gap record, not an alert).
> **Command lines**: every verdict surface below cites an exact command shape; the wording self-check of §五 was executed in the casting session with first-hand output recorded in the scroll (36 registered faces = 0; em-dash count = 0).

- **日期 Date**: 2026-11-12（工单日 Job date）· 铸卷收笔时戳 Casting finalized 2026-11-13 00:04 local（跨午夜如实登记 midnight crossing registered）
- **单号 Job ID**: vacgen-20261112 · 道B 规格席（SOP 铸造·零编译）
- **正本输入 Sources**（全部本会话亲读 first-hand read this session）:
  1. `D:/ComplexAnalysis/attn/_vacmain_audit_20261112/回执-vacmain完备审计v2-20261112.md`（§三 限定式三不越·§四 泛化工艺五条·§五 md5 manifest＝形状对表正本）；
  2. 形状正本八件 shape originals：`D:/ComplexAnalysis/attn/_vacmain_audit_20261112/sbx_v2/` 八个探针件与四卷判读卷（§四 manifest 表）；
  3. 机械工具两件 mechanical tools：`_tools/scan_boundary_tokens.py`、`_tools/judge_census_completed.py`；
  4. 词面登记册 wording register：`D:/ComplexAnalysis/规范术语/术语表-通用-项目级-20260921.md` §4.6 与 §5。
- **消费面 Consumers**: 自检席（相2·形状回归对表＋填充件编译判读）与汇编席（相3·独立仓候选登记）按本卷 §一/§二/§三 执行；词面自查仪器随卷存放于同目录 `ai_flavor_selfcheck.sh`。
- **文档体例 Conventions**: 标题双语（中/英）；表头英文化（table headers in English）；新铸探针件头注英文，四字段（审计单号 audit ID / 语句面 statement face / 判定语义 verdict semantics / 编译命令行 build command line）为最低配置。

---

## 〇、适用域、前置闸与总判定语义 Scope, Pre-Flight Gates, and Top-Level Verdict Semantics

### 0.1 适用域与输入输出面 Scope and I/O Surface

**适用域**: 对任意 Lean 工件的头部定理（challenge `main` 形语句）做 vacuity 审计，即判定其前提合取是否空真（vacuously true：前提不可满足，使被 sorry 证明的语句平凡为真）。本规程是 Rocq 侧 gate8 空真哨兵到 Lean/mathlib 语境的同构迁移（源回执 §四条①实测有效形的成文化）。

**输入面 / Input surface**:

| # | Input | Form（形态） | Gate（闸） |
|---|---|---|---|
| 1 | 工件语句面 artifact statement face | 靶件路径＋sha256（双点对表 two-point match） | sha 不符即 UPGRADE，禁带病开炮 |
| 2 | 工具链 pin toolchain pin | `lean-toolchain` 文件值＋`lake env lean --version` 实测 | 三连恰等，任一漂移即 UPGRADE |
| 3 | mathlib 快照 mathlib snapshot | 快照根路径＋`.lean` 文件数＋登记日期 | 窗口四元组（path, count, date, pin）入卷 |

**输出面 / Output surface**（四账 four accounts，由生成器铸骨架、填充后按 §二 分档判读）:

| # | Account（账） | Expected verdict（预期判定） | Content（内容） |
|---|---|---|---|
| 1 | witness 面 | 预期绿 expected-green | 存在实例信封定理（构造性 witness·两锚拼合） |
| 2 | 否证谱 refutation spectrum | 预期红 expected-fail | 多形态否证探针（全形/特化/语境/纪律面/战术谱） |
| 3 | 边界机检 boundary machine check | 预期绿 expected-green | 闭式实数序分离定理组 |
| 4 | 缺位定谳 absence verdict | 预期缺位 expected-absent | 名族普查＋四股合取定谳（§1.4） |

### 0.2 前置闸 Pre-Flight Gates（fail-loud·任一失守即停工升格）

| # | Gate | Command shape（命令形） | PASS criterion |
|---|---|---|---|
| G1 | 工具链恰等 toolchain equality | `cat lean-toolchain` ＋ `lake env lean --version` | 输出与 pin 逐字恰等 |
| G2 | 靶件指纹 target fingerprint | `sha256sum <artifact>`（随包副本与正本两点各一发） | 双点同值 |
| G3 | 形状正本在盘 shape originals on disk | `md5sum <八件>` 对表 §四 manifest | 逐件同值 |
| G4 | python 可用 python availability | `python -I -c "print('ok')"` | exit 0·生成器与扫描器均 python -I 纯 stdlib |

### 0.3 总判定语义 Top-Level Verdict Semantics

**否证面绿＝空真实锤＝最高级警报。** 一条否证探针（预期红件）编译 rc=0，即：该前提合取不可满足，被审计的 sorry 证明语句平凡为真（vacuously true），此为空真（vacuity）实锤，立即冻结、升格上报、审计判定置 `ok = false`。预期红哨兵保持安静（rc=1）＝健康态。其余各面判定按 §二 五档律执行。本语义在源审计四重收敛中实测兑现（否证谱 5/5 rc=1·警报零）。

---

## 一、泛化工艺五条·规程化 The Five Generalization Crafts, Codified

> 每条工艺＝可执行步骤（S 系列）＋判定面（V 系列·机检表）。步骤为操作规程，判定面为验收口径；判定面每行的 PASS/RED 判据均可由命令形机械复核。

### 1.1 工艺一：哨兵语义（预期红制）Craft 1: Sentinel Semantics (Expected-Red Discipline)

**工艺一句话**: 每个探针件在开炮前必须已声明预期判定；否证面是 COMPILE-MUST-FAIL 哨兵：编译绿即警报，红保持即健康。

**步骤 Steps**:

- **S1-1 预期判定前置声明**: 每个探针件头注在开炮前写明预期判定。否证面标 `EXPECTED-FAIL`（含预期落点：written-form 收尾读点或残余目标）；witness/边界/骨架面标预期绿。占位 sorry 以 `EXPECTED-FAIL`/`TODO-SEAT` 注释显式声明并计数。
- **S1-2 骨架验证炮先行**: 先发骨架验证件（与五否证面共享 module 头、import 面、探针点引理、bites 与 `#print axioms` 命令·但不含任何必败定理），要求 rc=0 绿。骨架未先证健全前，任何否证红不可读作证据（红可能系骨架缺陷而非判定）。源审计例：`_vacsmoke.lean` rc=0 先行，五形态红方为预期判定（源回执 §一·重2）。
- **S1-3 否证面开炮与落点登记**: 逐否证面发射，逐面记 rc 与判读落点（编译器报错 `file:line`）。落点必须落在声明的收尾读点；落点漂移＝勘形事件，如实登记。
- **S1-4 警报规则**: 任一 `EXPECTED-FAIL` 面 rc=0 ＝空真警报：冻结一切后续炮、升格上报、`ok = false`。警报判定以本面编译日志为唯一凭据。

**判定面 V1（机检表）**:

| Check | Command shape（命令形） | PASS | RED |
|---|---|---|---|
| 预期判定标记在位 | `command grep -c "EXPECTED-FAIL" <probe.lean>` | 否证面 ≥1；预期绿面 =0 | 缺标记开炮 |
| 骨架炮先行绿 | guard 包裹编译 smoke 件·`echo RC=$?` 无管道直取 | 否证判读前已有 rc=0 记录 | smoke rc=1＝骨架缺陷·禁读否证红为证据 |
| 否证面红且落点在读点 | guard 包裹编译·逐面 `echo RC=$?`＋日志归档 | rc=1 且报错落点＝声明读点 | rc=0＝空真警报（S1-4）；落点漂移＝勘形 |
| 占位计数单调 | 填充轮次间 `command grep -c "TODO-SEAT" <file>` 对照 | 计数单调不增（monotone non-increasing） | 对活计数器写精确等式不变式（禁·见 §2.2 注） |

### 1.2 工艺二：探针铸形四件套 Craft 2: Probe Casting, Four-Piece Set

**工艺一句话**: 每个探针件由四件构成：英文头注、逐字转录机检、machine bites、PA 逐定理报数；四件齐备，红绿判定才可归属。

**步骤 Steps**:

- **S2-1（a）英文头注**: 探针件头部注释块全英文，最低四字段：审计单号（audit ID）、语句面（statement face：转录自哪个靶件哪段前提界面）、判定语义（verdict semantics：预期判定＋绿/红各自含义）、编译命令行（build command line：含温控包裹全形）；另附纪律行（no sorry / no admit / no native_decide / no new axioms）。参照形：`sbx_v2/` 八件头注。
- **S2-2（b）逐字转录机检**: 被审计前提界面逐字转录进探针假设位；转录文本与靶件原文作机械比对（字符串/token 级等值），比对输出留痕。**靶件本体永不入 import 面**（其 sorry 证明件会污染公理审计）；探针以重声明方式承载界面（源回执 §一·重2「转录逐字机检」行）。
- **S2-3（c）machine bites**: 在具体探针点实例化界面词汇的小定理组，故意编译绿，证明转录界面相对靶件声明的同一 import 面可类型化。bites 全绿是否证红可读作证据的前置条件（界面咬合验证）。
- **S2-4（d）PA 逐定理报数**: 文件尾对每个可编译声明逐一发 `#print axioms`；预期谱＝`[propext, Classical.choice, Quot.sound]` 子集；命中 `sorryAx` 即红；新增 axiom 声明即红。

**判定面 V2（机检表）**:

| Check | Command shape（命令形） | PASS | RED |
|---|---|---|---|
| 头注四字段齐备 | `command grep -c -E "Audit|Statement|Verdict|Build" <probe.lean>` 头注区逐字段 | 四字段各 ≥1 | 缺任一字段 |
| 转录等值机检 | `python -I` 比对脚本（转录文本 × 靶件原文） | 输出 PASS 留痕 | 任一不等值 |
| 靶件零导入 | `command grep -n "<artifact-module>" <probe.lean>` 扫 import 面 | 0 命中 | ≥1（污染源在） |
| bites 全绿 | 编译日志逐 bite 定理查 rc 与 PA 行 | 全部 rc=0＋PA 三标准 | 任一红＝界面咬合失败·禁读否证红为证据 |
| PA 三标准 | `command grep -c "sorryAx" <log>` | 0 | ≥1（红·UPGRADE） |

### 1.3 工艺三：防波堤扫描器 Craft 3: Token Breakwater Scanner

**工艺一句话**: 承认式 token（sorry/admit/native_decide/axiom 族）在语句/证明面必须零命中；扫描器剥嵌套块注释与字符串字面量，代码面与注释面分账：注释面命中如实报告但不构成违规。

**工具 Tool**: `_tools/scan_boundary_tokens.py`（python -I·纯 stdlib·单遍扫描；md5 见 §四 manifest·行 15 token 表：`\b(sorry|admit|native_decide|sorryAx|axiom|axiomX|Admitted|Abort)\b`）。

**步骤 Steps**:

- **S3-1 逐件扫描**: 每个探针件一发：`python -I scan_boundary_tokens.py <probe.lean>`；`echo RC=$?` 直取退出码。
- **S3-2 双面分账读数**: 读 `CODE_FACE_HITS`（剥注释后语句/证明面）与 `RAW_FACE_HITS`（含注释全文）两账。判据只在代码面：注释面命中（如头注纪律行自述 no sorry）如实列示、不作违规。
- **S3-3 机制边界（防误伤两条）**: 扫描器剥 `/- -/`（含 `/-- -/` docstring）与 `--` 行注释及字符串字面量；Rocq 形 `(* *)` 刻意不剥：使用它的 `.lean` 件本身不可解析（源审计边界件 attempt-1 判例：Rocq 形定界符进 Lean 头注＝编译红·fail-loud 勘形登记·语句面零触碰）。

**判定面 V3（机检表）**:

| Check | Command shape（命令形） | PASS | RED |
|---|---|---|---|
| 扫描器指纹 | `md5sum _tools/scan_boundary_tokens.py` | 与 §四 manifest 同值 | 漂移即 UPGRADE（禁带病扫描） |
| 逐件代码面零命中 | `python -I scan_boundary_tokens.py <probe.lean>` | `VERDICT CLEAN`＋RC=0 | `VERDICT RED`（RC=1＝fail-loud）；RC=2＝用法/IO 错·重跑非放行 |
| 双面账齐报 | 读输出 `CODE_FACE_HITS`/`RAW_FACE_HITS` 两行 | 两行俱在 | 只报单面＝分账失守 |

### 1.4 工艺四：全树名族普查器 Craft 4: Full-Tree Name-Family Census

**工艺一句话**: 缺位定谳＝名族普查零命中＋三股旁证合取；单一名族零命中只是名级负发现，不构成缺位定谳。

**工具 Tool**: `_tools/judge_census_completed.py`（python -I·walk 全部 `.lean`·逐变体计数并报文件数；md5 见 §四 manifest）。泛化使用时按靶面改写 `VARIANTS` 名族与普查根，仪器形制不变。

**步骤 Steps**:

- **S4-1 快照窗口钉定**: 先钉普查根（mathlib 快照路径＋本地资产根）并登记窗口四元组（path, file count, date, toolchain pin）。文件数是快照登记值，不是活不变式，每次审计运行重新实测并按日期登记。
- **S4-2 名族定义**: 目标构造的候选名族 ≥3 变体（CamelCase 正名/snake_case 变体/模块限定形）；变体集写入普查脚本并随卷登记。
- **S4-3 普查发射**: `python -I judge_census_completed.py`；读每树 `lean files scanned: N`、逐变体命中数、`JOINT VERDICT` 行。
- **S4-4 四股合取定谳**: 缺位定谳要求四股证据**合取**（源审计四股·源回执 §一·重4 与缺位定谳卷 §六）：(a) 名族三变体 0 命中；(b) 属主模块自身 TODO/路线面在场；(c) 既有定义面为级数/junk 形（域外取值见证在场）；(d) 模块全定理清单无延拓型语句。任一股单独只是名级/局部证据；四股齐＝缺位定谳。
- **S4-5 负发现边界自划**: 缺位语句按 §2.4 四要素自划边界（扫了什么/没扫什么/非绝对主张/别名未穷尽）。

**判定面 V4（机检表）**:

| Check | Command shape（命令形） | PASS | RED |
|---|---|---|---|
| 窗口四元组在卷 | 读审计卷登记行 | (path, count, date, pin) 四项齐 | 缺任一项＝窗口未钉·禁下缺位判 |
| 普查输出完整 | `python -I judge_census_completed.py` 输出 | 每树 scanned N＋逐变体计数＋JOINT 行 | `READ_FAIL` 行＝fail-loud 登记 |
| 四股合取 | 四股逐行登记（a/b/c/d·各附第一手凭据路径） | 四股俱在 | 缺任一股→降级为「名级负发现」·不得写「缺位定谳」 |
| JOINT 判读 | 读 `JOINT VERDICT ... = 0` | =0→ABSENT（挂起档）；>0→PRESENT（缺位档撤销·witness 面重跑） | 混读（0 命中直写「不存在」）＝越权主张 |

### 1.5 工艺五：炮序登记制 Craft 5: Shot-Order Registration

**工艺一句话**: 记录面炮与判读凭据炮分账：工作流脚本层的记录面炮（可零费重放、可能先于探针件存在）不构成判读凭据；判读只引用铸后、guard 包裹、无管道直取 rc 的凭据炮。

**步骤 Steps**:

- **S5-1 两账分立**: 每次编译发射时即归账：**记录面炮**（脚本层记录面发射·Resume/Amend 重放零费·发射时探针件可能尚不存在·其 rc 不可归属判定）与**凭据炮**（探针件在盘后发射·guard 包裹·rc 无管道直取·日志归档 md5 钉定）。每炮恰入一账，禁账外编译。
- **S5-2 凭据炮四要件**: 判读引用的每发凭据炮须四要件齐：(a) guard trace 行在卷（core pin / 授权 / 档位 / done exit）；(b) 日志文件入 manifest；(c) rc 无管道直取（`echo RC=$?`·禁 `cmd | tail` 后取码）；(d) 发射时戳登记。源审计例：记录面五炮铸前发射、其 rc=1 不可归属；判读凭据＝铸后 guard 编译＋Judge 逐发重放（源回执 §一·重2「炮序登记」行）。
- **S5-3 独立重放**: 收口前对全部凭据炮做一轮独立重放（逐发重编译·逐面对表席位账）；零分歧方收口；分歧即 fail-loud 勘形。
- **S5-4 温控包裹正形**: 一切编译必经温控 guard 包裹（本机正形 `cpu_guard_v3.ps1 -TempLimit 98 -CoreN <N> -AllowG3 -GearForce 0`·禁裸 lake）；跨机按派发协议换本机等价包裹，禁裸跑。

**判定面 V5（机检表）**:

| Check | Command shape（命令形） | PASS | RED |
|---|---|---|---|
| 两账齐备 | 炮序台账逐行 label | 每炮恰一账·记录面炮显式标 non-evidence | 账外编译或混账 |
| 凭据四要件 | 逐引用日志 `command grep -c -E "pinned to core|done exit" <log>`＋rc 行 | 四要件全在 | 缺任一件＝该炮不得作判读凭据 |
| 独立重放零分歧 | 重放日志逐发对表席位账 | rc 与落点逐发同值 | 任一分歧＝fail-loud 勘形 |
| 重放件钉定 | `md5sum <replay logs>` 入 manifest | 全数在卷 | 缺卷 |

---

## 二、判读分档律 Verdict Grading Law

### 2.1 五档表 The Five Grades

| Grade（档） | Mechanical trigger（机械触发） | Reading（判读） | Mandatory action（必做动作） |
|---|---|---|---|
| **强红 strong red** | 语句面断裂：探针自身语句相对界面不成立（转录位 Unknown identifier / 构造不可用 / Cannot find witness 形） | **只作形态登记（form registration only）·无证据效力**（探针未咬合界面·既不证空也不证非空） | 登记形态；修探针；重发炮 |
| **弱红 weak red** | 机械红非语句面断裂·落点在声明读点（automation exhausted / unsolved goals 形） | **非空证据**：该前提界面在此谱面强度下抗拒了本次否证尝试 | 逐面登记 rc＋落点；入收敛账 |
| **绿（否证面）refutation green** | `EXPECTED-FAIL` 面编译 rc=0 | **空真警报（vacuity alert）＝最高级**：前提合取不可满足·被审语句平凡为真 | 冻结＋升格上报＋`ok = false` |
| **边界绿 boundary green** | 边界机检面（预期绿）编译 rc=0 | **正面机检**：闭式分离计算成立 | 登记·限定式陈述（只对该闭式事实下判） |
| **缺位 absence** | §1.4 四股合取在钉定快照内成立 | **挂起（pending）**：形式化缺口记录·非警报·非判空·非判可证 | 按 §2.4 四要素登记；复审条件＝上游形式化落地 |

**预期绿面转红的补充档位**: witness/边界/骨架面（预期绿）编译红＝探针侧缺陷或拼合面断裂（如 witness 拼合锚失配），按强红同法处理：fail-loud 勘形登记、修探针、重发炮；不得读作对被审计工件的任何判定（源回执升级通道③同形）。

### 2.2 分档适用边界与活计数器注记 Scoping Note and Live-Counter Note

- **适用域**: 本五档律适用于 vacuity 探针族（转录界面＋否证/边界/witness 面）。其它探针族（如对修正形的反转探针）在铸形时按工艺一 S1-1 自行声明预期判定映射，档位语义随映射走；未声明预期判定的炮不进分档判读。
- **活计数器禁精确等式不变式**: 探针计数、骨架填充计数、快照文件数等随时间演进的量，其不变式只取单调边界（如「TODO-SEAT 计数单调不增」「EXPECTED-FAIL 面不得转绿」）；**禁写精确等式不变式**（如「恒为 N 件」「success 恰 K 个」）；快照数值一律带日期登记、不作活检验定界（工件核验器设计律条 1）。

### 2.3 限定式三不越模板 Limited-Form, Three-Bounds Template

审计结论/升格语句一律限定式；三界之外的外推一律无效。模板（槽位以尖括号标注）：

```text
升格/结论语句（限定式）:
  "<工件>（<路径>，sha256 <64位十六进制>）通过 vacuity 审计（<UTC 日期>）：
   <逐面一行结论：witness 面/否证谱/边界机检/缺位定谳>。"
三不越限定 / Three bounds:
  ① 对象界 Object bound: 只适用该工件本件（sha 锁定）；
    不外推至同工件的其它件、其它版本。
  ② 谱面界 Spectrum bound: 只适用本探针谱面（manifest 锁定）；
    不外推至其它探针形态、未来新增形态。
  ③ 时点界 Window bound: 只适用该工具链 pin 与该 mathlib 快照窗口；
    上游推进后判定须复审，不作永久主张。
  越界外推（「全库已审」「永久有效」「零点自由命题真假」类全称表述）一律无效。
```

**worked example（源审计实测形·节录）**: 「Axiom 挑战面 `main`（`DedekindZetaChallenge.lean`·sha256 `dd2562c8…62be`）通过公理闭包＋vacuity 双审计（2026-11-12）：ℚ 特化面构造性 witness 编译绿；否证谱五形态全红（非空证据·零空真警报）；边界机检绿；泛型延拓面形式化缺位如实挂起。」三界逐字绑定见源回执 §三。

### 2.4 负发现边界四要素（缺位档配套）Negative-Finding Boundary, Four Elements

凡「未检出/零命中/扫描面无先例」类语句（负发现），必须同句自带四要素；缺任一要素即降格为「本次工具面未检出」：

| # | Element（要素） | Content（内容） |
|---|---|---|
| 1 | 扫了什么 what was scanned | 面/方法/时点逐项（哪些树·何种口径·文件级或名级·UTC 时点） |
| 2 | 没扫什么 what was not scanned | 显式声明未覆盖面（如「按名检索而非逐件通读」） |
| 3 | 非绝对主张 non-absolute | 表述为「该扫描面的负发现」，禁写「不存在/从未有人做过」 |
| 4 | 别名未穷尽 aliases not exhausted | 同名异形、翻译变体、语义等价实现可能在本扫描面之外 |

每条缺位判词还须附**复审条件**（扫描面何时重扫：上游快照推进即重跑普查）；无复审条件的挂起不予收口。

---

## 三、独立仓候选 README 骨架 Independent-Repo Candidate README Skeleton

### 3.1 零先斩声明 Zero-Preemption Declaration

**独立仓候选＝登记不建仓（零先斩）**: 本节只登记候选骨架文本，未创建任何仓库、未注册任何名称、未对外发布、未向上游提交任何件；骨架文本系草案，后续候令另单处理。本节文本为目标对外面（发布体），已按对外语域书写：只写做了什么与测得什么、零内部编号、零优先权主张。

### 3.2 README 骨架正文 README Skeleton Draft

```markdown
# vacgen · Vacuity Probe Generator for Lean Artifacts（候选工具 / candidate tool）

**Status / 状态**: candidate registration only: no repository has been created,
no name registered, nothing published, nothing submitted upstream. This page is
a draft skeleton for a possible future standalone repository.

## What it does / 工具做什么

Given a Lean artifact's headline theorem, vacgen generates a four-account
vacuity probe package and grades the results:

1. **Witness face**: an existence-instance envelope theorem showing a concrete
   witness function satisfies the artifact's premise conjunction (constructive
   non-vacuity evidence for the specialized face);
2. **Refutation spectrum**: expected-fail probes attempting to derive `False`
   from the transcribed premise interface; a probe that compiles means the
   interface is unsatisfiable, i.e. the artifact's `sorry`-proven statement is
   vacuously true (the alert);
3. **Boundary machine check**: closed-form separation computations over the
   relevant regions (positive machine checks);
4. **Absence verdict**: a name-family census over the pinned library snapshot,
   deciding whether the formalization face of the needed background theory is
   present or absent (absence is recorded as pending, never as an alert).

## Input surface / 输入面

- the artifact statement face (target file + sha256, verified at two points);
- the toolchain pin (`lean-toolchain` value, verified against the running
  toolchain);
- the pinned mathlib snapshot (path + `.lean` file count + registration date).

## Output surface / 输出面

Four accounts (witness / refutation spectrum / boundary / absence), each with
per-probe exit codes, verdict loci, `#print axioms` profiles
(`propext`/`Classical.choice`/`Quot.sound` tolerated; `sorryAx` is a red
finding), and an md5 manifest of every probe and log.

## Dependency boundary / 上游依赖划界

- The generator itself: Python 3 standard library only; zero network; zero
  compilation.
- Probe compilation: consumer-provided Lean toolchain + mathlib snapshot
  (pinned; every absence verdict and every witness splice anchor is relative
  to that snapshot window).
- Verdicts carry their snapshot window: when the upstream library advances,
  absence verdicts must be re-run (re-run condition registered with each
  verdict); splice anchors are re-verified against the new snapshot before
  any reuse.

## Non-goals / 不做什么

- It does not judge the mathematical truth of open clauses inside the
  artifact (a refutation red records that the interface resisted the attempted
  strength; it is not a satisfiability proof).
- It does not replace kernel checking; it composes with it.
- It registers no priority claims of any kind.
```

**骨架四要件对表**（本席自检·行级核对）:

| Required element（要件） | Location in skeleton（落位） |
|---|---|
| tool 名 tool name | 标题行 `vacgen · Vacuity Probe Generator for Lean Artifacts` |
| 输入输出面 I/O surface | `Input surface` / `Output surface` 两节 |
| 零先斩声明 zero-preemption | `Status / 状态` 首段 |
| 上游 mathlib 快照依赖划界 snapshot boundary | `Dependency boundary` 全节（窗口绑定＋复审条件） |

---

## 四、形状正本 manifest 与对表 Shape-Original Manifest and Cross-Check

**口径**: 下表 md5 系本席本会话 `md5sum` 第一手实测（2026-11-13 00:0x local）；对表正本＝源回执 §五 manifest；十件加四卷全数同值＝同一实体（对表律：判定正本一律 md5/sha 对表，不凭文件名或尺寸直觉）。

**探针件与工具 Probes and tools（10 件）**:

| File | md5 (measured) | vs 源回执 §五 manifest |
|---|---|---|
| `sbx_v2/_vacmain_q_witness.lean` | `451a796ecdb700305cc35bdc0e5e6f5e` | MATCH |
| `sbx_v2/_vacmain_boundary.lean` | `91b2c094295261ce4d25be94df80316b` | MATCH |
| `sbx_v2/_vacsmoke.lean` | `d05e87ec243f323bf0716c08b8ac0b3f` | MATCH |
| `sbx_v2/_vacfalsify_full.lean` | `428a8134f7344e45bbb8a4767789d6d1` | MATCH |
| `sbx_v2/_vacfalsify_rat.lean` | `01c29f5daab1988caa8a51e5be1438d3` | MATCH |
| `sbx_v2/_vacfalsify_gamma.lean` | `aa6ec7aaeb54dfb04636e7bb8a0d6cc7` | MATCH |
| `sbx_v2/_vacfalsify_noclassic.lean` | `b68a0a46bbf92d3749aea46c1bb21f65` | MATCH |
| `sbx_v2/_vacfalsify_tactics.lean` | `73536866405e175eff90b92575a7703d` | MATCH |
| `_tools/scan_boundary_tokens.py` | `5e8b308f8c3c8201c27afabf73ec1d77` | MATCH |
| `_tools/judge_census_completed.py` | `8d8ca9feaf3fe83c6c7df4d2c389755c` | MATCH |

**判读卷 Adjudication scrolls（4 卷）**:

| File | md5 (measured) | vs 源回执 §五 manifest |
|---|---|---|
| `sbx_v2/witness判读-20261112.md` | `c49f89f52193692e55fc88cb6917fdef` | MATCH |
| `sbx_v2/否证谱判读-20261112.md` | `6ae392743bc2cac2ddca31faeed84c51` | MATCH |
| `sbx_v2/边界机检判读-20261112.md` | `2807832ac2d721807078e5e32aaa227a` | MATCH |
| `sbx_v2/延拓缺位定谳-20261112.md` | `31851ad7d1210bc1945c76f0651ec6e7` | MATCH |

**对表结论**: 14/14 逐字节 MATCH，形状正本在盘未漂移，相2 形状回归对表可以此表为基准。

---

## 五、AI 味词面自查（断言随卷）AI-Flavor Wording Self-Check (Assertion on Record)

### 5.1 登记册与仪器 Register and Instrument

- **登记册 Register**: `D:/ComplexAnalysis/规范术语/术语表-通用-项目级-20260921.md` §4.6（AI 味词面登记册·中文词语 A 行与表述模式 C 行）＋§5（英文词面/句式/结构三族）；操作形镜像＝`C:/Users/Live/.zcode/skills/cw-wf-dispatch/references/constraint-blocks.md` §十三。
- **自查面 Battery**: 中文三族 10 词面（公文黑话动词族/伪抽象名词族/口号压缩族·族名与词面全表以登记册 §4.6 A 行与仪器内嵌正则为准·词面字面量不入本卷，防自证命中）＋英文 26 模（15 词干＋8 句式＋3 段首过渡）＋em-dash（U+2014）计数。
- **仪器 Instrument**: 本卷同目录 `ai_flavor_selfcheck.sh`（词面字面量内嵌于仪器·仪器不在自身断言域内·`command grep` 实测·禁 ugrep shim 单发）。
- **仪器两向验效（本席第一手）**: 阳性对照件（内嵌四电池各一枚已知命中面＋一枚 em-dash）实测 `VERDICT RED`·exit 1·四电池计数逐面精确为 1、em-dash 计数精确为 1；阴性对照（本卷）`VERDICT CLEAN`·exit 0。两向过方用于 §5.2 断言（审计工具先以已知真值验效再出数）。

### 5.2 实测输出 Measured Output（本席第一手·2026-11-13 00:0x local）

命令（逐字）:

```bash
sh "D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/ai_flavor_selfcheck.sh" \
   "D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/SOP-vacuity探针工具化-20261112.md"
```

实测输出（逐字）:

```text
CH_3FAMILIES_10FACES lines=0
EN_WORD_STEMS_15FACES lines=0
EN_SENTENCE_8FACES lines=0
EN_PARA_INITIAL_3FACES lines=0
EM_DASH_U2014 count=0 (target 0)
TOTAL_WORDING_LINES=0
VERDICT CLEAN (36 faces = 0; em-dash = 0)
```

（仪器 exit 0·终测时戳 2026-11-13 00:11 local。铸卷过程如实注记：首轮实测 `EM_DASH_U2014 count=45`（RED·草稿含中文破折号与 README 英文破折号），逐处清改后终测如上；词面电池首轮即全零。终测绑定收卷态，时效见 §5.3。）

### 5.3 断言与时效 Assertion and Validity

**断言**: 本卷（`SOP-vacuity探针工具化-20261112.md`）在铸卷收笔时点对 36 词面电池 grep=0、em-dash=0，系**该文件该时点静态内容的闭窗扫描断言**（快照断言·带日期登记），非活不变式；文件任何后续改动即时失效本断言，改动方须重跑仪器并重新登记。此系「文意与实现同闸」的文档版：本卷 §五声称的自查与仪器实际执行的检查逐字对应（仪器正则即登记册词面全表·无省略无扩权）。

---

## 六、验收清单（本 SOP 五项交付）Acceptance Checklist (Five Deliverables of This Scroll)

| # | Deliverable（交付项） | Verdict surface（判定面） | Status |
|---|---|---|---|
| ① | 泛化工艺五条规程化（每条＝可执行步骤＋判定面） | §一：五工艺各有 S 系列步骤＋V 系列机检表（步骤 20 条·判定面行 20 行·实数点验） | DONE |
| ② | 判读分档律（五档）＋限定式三不越模板 | §二：五档表（§2.1）＋适用边界与活计数器注记（§2.2）＋三不越模板（§2.3）＋负发现四要素（§2.4） | DONE |
| ③ | 独立仓候选 README 骨架（四要件） | §三：零先斩声明（§3.1）＋骨架正文（§3.2）＋四要件对表（tool 名/输入输出面/零先斩/快照划界全落位） | DONE |
| ④ | AI 味词面自查 grep=0 断言随卷 | §五：登记册＋仪器＋第一手实测输出（36 faces=0·em-dash=0·exit 0）＋时效条款 | DONE |
| ⑤ | 双语标题＋表头英文化 | 全卷 `#`/`##`/`###` 标题双语；全部表格表头列名均英文（铸卷时逐表枚举复核） | DONE |

**边界如实（本卷未做之事 What this scroll does not cover）**: vacgen 生成器实体、双工件端到端自检、OAI 边界件填充编译、全役 md5 manifest 收口，分别属铸造席/自检席/汇编席职权面，本卷只供其规程与判读律；本卷零编译零发炮（SOP 系文书件·零编译纪律适用）。

*本卷不写自身 md5（自引悖论防波·同源回执例），收卷方 md5sum 对表即可。*
