# 处方件 — S07 投影重锚（E5·magic 六件判例文档化）

> rocqwash recipes/·20261101 agent rqsupport·五课反馈轮打磨件④。
> 判例源（只读已核在盘）：`sandbox/seat_reanchor/账/迁移账-六件重锚.md`（UpReqSampling
> 件·重锚员 20261031·凭据=该席全部实跑命令与 json/log 在卷）＋`sandbox/seat_magic6/`
> 台账（CI 探针基线 magic=293·P1 行）＋`seat_reanchor/账/重锚diff-96行.patch`（96 行
> 脉冲逐 hunk 机械复核纯三映射）。

## 〇、一符总纲

| 项 | 值 |
|---|---|
| 处方号 | **E5**（语句面投影重锚·magic 归零处方） |
| 病名 | Class 字段投影承载语句面 → 提取面 `Obj.magic` 泛滥（假载体病） |
| 判例件 | UpReqSampling.v（六件批之一·基线 magic=**293** → 重锚后 **0**） |
| 六件批 | UpAblMetaWorld3 / UpDebtSqrtAbsReq / UpEntropyGainReq / UpFirewallReq / UpReqTempEntropy / UpReqSampling（M34 新落叶子件·共享 work 世界同址实录） |
| 铁律位 | 语句面（签名+assert 类型面）重锚具体面；证明体战术/项式**零字符**；注释**零触碰** |

## 一、病灶（根因链·判例转录）

1. **Class 三大关系字段是 Set 值域**：`Class RealInterfaceEnhancedSetoid`
   （`S07_RealSetoidExpLog.v:8075`）字段 `req / lt / le : Real -> Real -> Set`。
   提取后字段坍缩为 `type req = __`（不可 condemn 的空类型）。
2. **实例绑定具体面**：`RealEnhancedReal`（`S07_RealSetoidExpLog.v:8740`）绑
   `req:=real_eq ／ lt:=real_lt ／ le:=real_le`。
3. **语句面写裸投影名**：件语句面全写在字段投影上（`Import RealInterfaceEnhancedMod`
   裸名＋`Notation R := Real`，无 Let 锚位），而证明体与依赖链
   （UpReqAlgebra/UpReqDist/S02）全走具体面——**两表示系交叉即 Obj.magic**。
   实测：重锚前 CI 检验 magic=293（seat_magic6 台账 §一 P1 行在卷）。
4. **树内健康判例**（同病灶已愈件）：树内 `UpReqAlgebra.v`（`req_plus_zero_r :
   forall a : R, real_eq (plus a zero) a`，源 :48 邻域）同款保留 Import＋
   `Notation R := Real`＋裸 plus/mult 字段名、**仅关系面用具体名**，树内 magic=0。

## 二、处方（E5 三映射·语句面重锚具体面）

具体面实体（均在 `S02_CauchyComplete.v`，均 `Real -> Real -> Set`）：

| 投影（病面） | 具体面（愈面） | 定义位 | UpReqSampling 判例刀量 |
|---|---|---|---|
| `req` | `real_eq` | S02:411 | 58 处 |
| `lt` | `real_lt` | S02:480 | 22 处 |
| `le` | `real_le` | S02:484 | 38 处 |

合计 118 关系名 token。**改动脉冲 96 行**（86 diff hunk，逐 hunk 机械复核纯三映射、
0 意外——`seat_reanchor/账/重锚diff-96行.patch` 在卷）。

### 刀面三分（何者改·何者禁改）

| 面 | 处置 | 判例依据 |
|---|---|---|
| 签名面语句（Theorem/Lemma/Variable/Hypothesis 槽·51 条） | 三映射重锚 | 受影响语句 61 条＝签名面 51＋体内 assert 面 10 |
| 体内 assert 类型面（Proof 内局部语句·10 条） | 同治（类型面随迁） | assert 面提取后不落独立导出名，但类型面与外层同病同治 |
| 证明体战术/项式 | **零字符改动** | E5 处方兑现判据：改后一次编译过（born rc=0） |
| 注释行含裸 token（14 行：源行 2/16/20/65/66/77/88/145/146/641/668/696/720/1011） | **零触碰** | 注释不进提取面；触碰即污染 diff 纯度 |
| `Notation R := Real` 桥 | **保留** | 树内 UpReqAlgebra 判例同款保留 |
| Class 字段定义本体（S07 正本） | **禁触**（Set 仓只读） | 重锚只动件面，不动库面 |
| 前提/binder 位 | **零触碰**（non-negotiable constraint② lawful keep 同源） | nw6 判例同律：前提/binder 位禁硬修 |

### 判例验收四证（UpReqSampling 实测·20261031）

| 关 | 判据 | 实测 |
|---|---|---|
| born 编译 | RC=0＋.vo 魔数 `436f7121 00015ff4`＋.vo 新于 .v | RC=0 一次过（vo md5 `10d393bd3bc3641f1aa7e4fbf91be4e6`·50826B） |
| gate7 提取探针 | **magic=0（硬验收）** | magic_ml=0／magic_mli=0（51 名·missing=0）；基线 293→0；独立复核 grep Obj.magic .ml/.mli 双 0 |
| cross-check against the reference（语句名） | mac_stmt_names 有序全等 | census 51=51、含 Let 67=67·有序全等 PASS（成品 md5 `45ce11a7283926051698a46ebc012a09` vs 源 `4dba5385…`） |
| gate4＋CJK＋承认式 | PASS=1 FAIL=0；CJK=0；承认式=0 | 全达标（头注 30 行五字段齐；Admitted/admit/Abort 词界计数 0） |

签名稳定律附记：六件系 M34 新落叶子件、树内零下游消费（seat_magic6 台账 §二.4 口径）
→ 无下游适配面；落装面 md5 变更（`4dba5385…`→`45ce11a7…`）→ M34 注册锚随落装波换
锚（注册面归编排方，非重锚席职责）。vo 代际：重锚后 vo 与落装病面 vo（`817f2929…`）
不同 digest——重锚席世界内病面 vo 已剔除，born 纯度保持。

## 三、rocqwash 工装接线（本仓三件各就各位）

1. **台账洗**（wash/wash_engine.py·在役冻结件）：三映射天然是 exact-string 台账形——
   `{"tag":"req2real_eq","old":"req ","new":"real_eq ","expect":N}` 逐映射一条
   （expect 取实测刀量；word-boundary 例外面——注释行/前提位/证明体——由台账 old
   串携带足量上下文精确锚定，**禁**裸单词全替换）。
2. **born 前世界基断言**（wash/world_hook.py·本轮新件①）：`--world <目录> --manifest
   <认证代账>` 于 born 前断言世界=认证代（nw5 雷防线）。
3. **收口判读**：gate6 侧 `verify/verify_gate6.py`（本轮新件③·薄调正本/判例器化）；
   gate7 magic 硬验收=0 侧归 `wrapper/gate7_probe.sh`（既有正典启动层）。
4. **选件面**（tools/select_audit.py·本轮新件②）：六件批属多席共享 work 世界实录
   （迁移账 §五.1）——批选前先对树 order.txt 全表审计剔重＋跨批撞名（enbig7 判例）。

## 四、何时不适用（处方边界·不硬凑）

- 语句面已走具体面、magic 仍非零 → 非 E5 病（查 gate7 探针的 missing/exclusions 面）。
- 件有树内下游消费 → 迁移账不再是轻账：签名重锚牵连下游适配，须先勘定消费面
  （`mac_stmt_names` cross-check against the reference＋Require 面全表 grep）再动刀。
- Class 字段本体须改 → 越权：S07 正本在 Set 仓只读；升单走编排方，处方件不代行。
