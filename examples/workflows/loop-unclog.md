# loop-unclog.md — 工作流嵌段③：堵账疏通闭环（干跑→人审→--apply→复核·诚实墙分支）

> rocqwash v37 嵌段正典样例三件之三。把 `README-cw.md:128-130`「unclog 嵌段」
> 展开为可整段复制执行的命令块＋真实输出样例＋退出码分支表（诚实墙分支）＋
> dynamic-workflow 嵌段伪码。器实况正本：`tools/unclog.py` docstring（v37 旗舰·
> 手工五步闭成自旋：probe 归集→chain_graph 链根→cure_applier 落刀→rescan/resprobe
> 复核→判定；schema `rocqwash-unclog/1`·verdict 三态
> `unclogged|wall|rounds-exhausted`，unclog.py:76）与 `--help`。
>
> **纪律红线**：
> - **--apply 缺省关＝全干跑零写盘**（单开关·`--yes` 不需要，unclog.py docstring
>   「安全律」节）：落刀只对**链根件**（`<src>/<根>.v`——pick 之外无 cure 调用
>   路径·对非链根件禁落刀系结构性保证）·只经正典包 cure_pack v1.3（禁 freeform
>   编辑）。
> - **诚实墙禁硬凑**——TOP 榜全 `self.washable=false` 或可洗根全部碰壁→
>   `verdict=wall exit 1`，墙账逐根列不可洗因，零落刀零硬凑（unclog.py:35-38）。
> - **红是数据非器红**——probe rc1 候选是产出数据；退出码只表器面与终局
>   （0=unclogged·1=wall/rounds-exhausted·2=用法/场景形错·9=fail-loud）。
> - **世界换代口径**——本器零写 `--world`；洗后复探红是否清账取决于世界 .vo
>   基座换代（调用方按 wash/world_hook.py 认证代纪律播种），器只如实出账
>   （unclog.py docstring「世界纪律」）。

## 1. 第一步：干跑（缺省零写盘·出方案账）

```bash
# ── loop-unclog 嵌段·第 1 步：干跑（在 rocqwash 仓根执行）────────────
SRC=src/                          # 源树根（根件 <根>.v 取自此）
WORLD=world/                      # 世界目录（probe 检验 cwd·.vo 基座调用方播种）
CANDS=cands.tsv                   # 候选清单 TSV（表头「件名\tmd5」·probe_engine 同款）

bash cw.sh unclog --src "$SRC" --world "$WORLD" --candidates "$CANDS" \
  --json unclog-dry.json --events unclog-dry-events.jsonl
echo "UNCLOG_DRY_RC=$?"           # 0=红已清（无需落刀）·1=wall/轮尽·读账定夺
```

> 干跑块无 `--apply`——这是**结构性缺省**，不是漏写（见上红线第一条）。

**实测样例**（2026-11-11 铸席 tmp 注入演练：`--src … --world … --candidates …
--injector inj/ --json … --events …`，rc=0；stdout 进度原文）：

```text
workdir -> /tmp/.../wd
候选面: --candidates …/cands.tsv
injector: …/inj（probe canned 2 发·resprobe canned 1）
frozen 在册: 8 件（certify/frozen8.py --ledger 实取·预检红拒）
[round 1/5] 归集: probe 红账 1: B
chain_top: A(n=1,washable=True)
RECHECK A rescan_station=0 resprobe_rc=0
[round 1/5] root=A cures=1
[round 2/5] 归集: probe 红账 0: -
[round 2/5] root=- cures=0 (red empty)
report -> /tmp/.../wd/report.json
VERDICT: unclogged (exit 0)
```

对应 report 的轮账（实测节选·rocqwash-unclog/1·cure.stage=dry-run＝未落刀）：

```json
{
 "mode": { "apply": false, "injector": true, "loop": false, "source": "tsv" },
 "rounds": [ {
   "chain_top": [ { "dependents": ["B"], "lib": "A", "n": 1,
                    "self": { "probed": true, "rc": 0,
                              "verdict": "RC0", "washable": true } } ],
   "cure": { "md5_after": "69cccc393d849a7c96a87565b6dc72c2",
             "md5_before": "d47bbca3db58dbfeb55c4ad0cb47e950",
             "on_disk_md5_match": true,
             "patterns": { "cure13_natle_premise_lift": 1 },
             "rc": 0, "stage": "dry-run", "total_matches": 1 },
   "cures_applied": 0, "cures_planned": 1, "root": "A", "root_file": "A.v",
   "rescan": { "ids": "S", "rc": 0, "residual_zero": true, "station_count": 0 },
   "resprobe": { "md5_match": null, "n_records": 1, "rc": 0, "rc_ok": true },
   "round": 1 } ],
 "final": { "cures_applied_total": 0, "cures_planned_total": 1,
            "red_files": [], "rounds_run": 2, "verdict": "unclogged",
            "wall_count": 0 },
 "schema": "rocqwash-unclog/1",
 "verdict": "unclogged",
 "wall": {}
}
```

**零写盘实证**（同次实跑）：干跑后根件 md5 与 cure.md5_before 恒同
（`d47bbca3db58dbfeb55c4ad0cb47e950`）——文件未动。

## 2. 第二步：人审方案（读干跑账·不跑器）

人审三问（全部出自 report，零新引擎）：

| 读哪里 | 判什么 |
|---|---|
| `rounds[].chain_top[].self.washable` | 链根可洗性三分（chain_graph 口径）；全 false→预期 wall |
| `rounds[].cure.patterns` | 正典包将落的 pattern 名与计数（如 `cure13_natle_premise_lift: 1`）——方案不对→不开 --apply |
| `rounds[].cure.stage` | `dry-run`=未落刀；此值在 --apply 后才变 `applied` |

## 3. 第三步：--apply 落刀＋第四步复核（同一命令出齐账）

```bash
# ── loop-unclog 嵌段·第 3-4 步：落刀＋复核（人审过才走这步）──────────
bash cw.sh unclog --src "$SRC" --world "$WORLD" --candidates "$CANDS" \
  --apply --json unclog-apply.json --events unclog-apply-events.jsonl
echo "UNCLOG_APPLY_RC=$?"
```

**实测样例**（同日 tmp 演练·rc=0；stdout 落刀与复核原文）：

```text
[round 1/5] 归集: probe 红账 1: B
chain_top: A(n=1,washable=True)
APPLIED A cures=1 md5_after=69cccc393d849a7c96a87565b6dc72c2 on_disk_match=True
RECHECK A rescan_station=0 resprobe_rc=0
[round 1/5] root=A cures=1
[round 2/5] 归集: probe 红账 0: -
[round 2/5] root=- cures=0 (red empty)
VERDICT: unclogged (exit 0)
```

复核三判据（report 内·复跑五洗同源引擎）：

- `rounds[].rescan.residual_zero == true`（scan_v4_token 复扫受治件·cured token
  残差应零——样例实测 `station_count: 0`）；
- `rounds[].resprobe.rc_ok == true`（probe_engine 复探受治件·rc 应 0——样例实测
  `rc: 0`）；
- `final.red_files == []` 且 `final.cures_applied_total == 1`（红账空＝疏通）。

**复核不过的诚实形**：`resprobe.rc_ok=false` 时 stdout 响亮缀
`resprobe-rc=…（应 0 未达·如实入账）`（unclog.py:620-621）——器不把「落刀了」
混充「疏通了」，红是否清账最终看世界换代（红线第四条）。

## 4. 退出码分支表（verdict 三态·诚实墙分支）

| 退出码 | verdict | 含义（unclog --help/docstring 口径） | 工作流动作 |
|---|---|---|---|
| 0 | `unclogged` | 红账空（疏通·或本就无红） | 收尾；读 final.cures_*_total 入账 |
| 1 | `wall` | **诚实墙**：TOP 榜全不可洗或可洗根全部碰壁→零落刀零硬凑·墙账逐根列因（wall 字段） | 人审 wall 账分派：见下行墙因表 |
| 1 | `rounds-exhausted` | `--rounds`（默认 5）轮尽红未清·各轮账＋终判探在册 | 读 rounds[] 逐轮账·人定加轮/换世界/人工修 |
| 2 | （无 verdict） | 用法错／注入场景形错（如 canned 序列耗尽/缺列/形坏——按序严格消费 fail-loud） | 修命令行或补 canned 场景 |
| 9 | （无 verdict） | fail-loud（路径缺失／引擎子进程非数据性非零退／frozen 在册不可得／全树枚举零候选） | 人工补路径/修器面 |

**诚实墙因分派表**（wall 字段 `reason` 值·正本 unclog.py:35-47）：

| reason | 语义 | 交谁 |
|---|---|---|
| `self-unwashable` | 链中环·根件自身被阻（先治根的因） | 人工（器不硬凑） |
| `no-chain-root` | 红账无一缺库链根（代差型/器因红·墙账不得哑） | 人工分诊（对照 ci_triage 判类谱） |
| `root-file-missing` | 链根件缺失（红因所缺库无对应源件） | 人工补件 |
| `cure-miss` | 正典包干跑零方案（total_matches=0·不硬造） | 人工扩包或改写 |
| `frozen-in-service` | 根名/根件撞 frozen8 在册八件·预检红拒 | **禁触冻结件**——改侧道 |
| `exclusive-group-conflict` | 变体须 `--only` 人择（禁自动代选） | 人工择一后重跑 |
| `idempotence-fail` | 落刀幂等断言拒写（cure_applier 拒·文件未动） | 人工查重复式 |

**墙账实测样例**（2026-11-11 tmp 实跑：台账 Y rc1 RED-OTHER＋C1 缺 Y→链根 Y
self-unwashable；rc=1）：

```text
候选面: --chain-ledgers …/base.json（merge 模式·无逐轮全量重探）
frozen 在册: 8 件（certify/frozen8.py --ledger 实取·预检红拒）
[round 1/5] 归集: merge 红账 2: C1,Y
WALL: Y — self-unwashable（根件自身被阻 rc=1 verdict=RED-OTHER（链中环·先治根的因））
[round 1/5] root=- cures=0 (wall)
VERDICT: wall (exit 1)
```

```json
{ "final": { "cures_applied_total": 0, "cures_planned_total": 0,
             "red_files": ["C1", "Y"], "rounds_run": 1,
             "verdict": "wall", "wall_count": 1 },
  "rounds": [ { "chain_top": [ { "lib": "Y", "n": 1,
                                 "self": { "probed": true, "rc": 1,
                                           "verdict": "RED-OTHER",
                                           "washable": false } } ],
                "cure": null, "cures_applied": 0, "cures_planned": 0,
                "root": null, "round": 1 } ],
  "schema": "rocqwash-unclog/1", "verdict": "wall",
  "wall": { "Y": { "detail": "根件自身被阻 rc=1 verdict=RED-OTHER（链中环·先治根的因）",
                   "reason": "self-unwashable", "root": "Y" } } }
```

## 5. 候选面三源与离线注入形

候选面三源任选（互斥·docstring「候选面三源任选」节）：

```bash
# 源①候选 TSV 直接代入（表头「件名<TAB>md5」）
bash cw.sh unclog --src "$SRC" --world "$WORLD" --candidates cands.tsv --json r.json
# 源②既有 probe 台账并入（argv 序=合并序·后批覆盖前批·merge 模式无逐轮全量重探）
bash cw.sh unclog --src "$SRC" --chain-ledgers l1.json l2.json --json r.json
# （两者缺省）源③--src 全树枚举 *.v 逐件 md5
bash cw.sh unclog --src "$SRC" --world "$WORLD" --json r.json
```

离线注入（工作流演练/CI 用·纪律③）：`--injector DIR/`，`DIR/scenario.json＝
{"probe":[ledger...],"resprobe":[ledger...]}`——probe/resprobe 两类 probe_engine
调用**按序严格消费** canned 台账（原样落 workdir 后仍喂真 chain_graph·耗尽/缺列/
形坏 fail-loud 2）；chain_graph/cure_applier/scan_v4_token/frozen8 注入模式下
照旧真跑（真编排非傀儡，unclog.py docstring「离线可测」节）。台账记录实形
（rocqwash-probe-ledger/1·本席演练所用）：

```json
{ "schema": "rocqwash-probe-ledger/1", "n_records": 2, "records": {
    "A": { "file": "A", "md5": null, "rc": 0, "red": "", "missing": null,
           "red_class": null, "verdict": "RC0", "red_count": null, "md5_match": null },
    "B": { "file": "B", "md5": null, "rc": 1,
           "red": "Error: Unable to locate library | A (while searching for a .vos file).",
           "missing": "A", "red_class": "MISSING_LIB",
           "verdict": "RED-MISSING_LIB", "red_count": null, "md5_match": null } } }
```

canned 消费序实测注记（2026-11-11 tmp 实跑教训·如实记）：candidates 模式**逐轮
全量重探**——每轮 probe 各耗 1 发 canned（含干跑）；resprobe 每次复核耗 1 发；
序列耗尽＝fail-loud 2。故演练场景的 probe 序列长度须 ≥ 轮数。

**loop 哨态**（README-cw.md:116-118 同款）：`--loop --interval 600 --loop-max 8
--events unclog-events.jsonl`——闭环周而复始，`unclogged/wall` 终局即停即退，
`rounds-exhausted` 非终局歇 `--interval` 再下一周（`--loop-max` 命周数帽·0=不限）。

## 6. dynamic-workflow 嵌段伪码

```text
// 嵌段③堵账疏通：干跑门→人审→--apply→复核四判·诚实墙分流（器：cw.sh unclog）
phase "unclog-loop" {
  // 1) 干跑（缺省零写盘·结构保证）——退出码即终局预演
  const dry = await world.run("bash", ["cw.sh", "unclog", "--src", "src/",
      "--world", "world/", "--candidates", "cands.tsv",
      "--json", "unclog-dry.json"]);
  if (dry.exitCode === 0) return { verdict: "already-unclogged" };

  // 2) 人审方案：子代理只读 dry 账（washable/patterns/stage），答 落刀|不落刀
  const review = await agent({ role: "cure-reviewer",
    ask: "读 unclog-dry.json rounds[].cure.patterns 与 wall 账，答 落刀|不落刀+理由" });
  if (review.answer !== "落刀") return { verdict: "held", why: review.reason };

  // 3) 落刀＋复核（同一命令出齐账·--apply 是唯一写开关）
  const apply = await world.run("bash", ["cw.sh", "unclog", "--src", "src/",
      "--world", "world/", "--candidates", "cands.tsv", "--apply",
      "--json", "unclog-apply.json"]);
  switch (apply.exitCode) {
    case 0: return { verdict: "unclogged" };              // rescan/resprobe 三判据读账确认
    case 1: {                                             // wall 或 rounds-exhausted
      const wall = await agent({ role: "wall-triage",
        ask: "读 unclog-apply.json wall 账按 reason 分派（frozen-in-service 一律禁触）" });
      return { verdict: "wall", wall: wall.answer };
    }
    case 2: return { verdict: "usage-or-scenario" };
    case 9: return { verdict: "fail-loud" };
  }
}
```

## 7. 诚实注记

- 本文全部输出样例为 2026-11-11 铸席在本仓 `tools/unclog.py`（v37 41e74b0）tmp
  注入演练**实跑**所产（干跑 rc 0／--apply rc 0／墙 rc 1·夹具 A.v/B.v 与 canned
  台账均 tmp 造），非手写；样例路径仅出基名（report 确定性纪律·unclog.py
  docstring「输出」节）。
- `cure13_natle_premise_lift` 是正典包真实 pattern 名（wash/cure_pack.json v1.3·
  实跑报告 patterns 字段原值）。
- 本席未实跑真编译探针（probe_engine 真探需 rocq 世界基座·真编译必经 cpu_guard
  包裹：`--guard PATH --guard-reg DIR …` 透传，unclog --help「--guard」条）——
  真探形属用户面，离线注入形已实测。
- 退出码分支表逐格锚 unclog docstring「退出码」节与 `--help` 尾注；墙因表锚
  unclog.py:35-47 诚实墙节与 wall_add 调用点（unclog.py:429 unprobed·431
  self-unwashable·470 frozen-in-service·514 no-chain-root·542 root-file-missing·
  548/574 exclusive-group-conflict·565 cure-miss·578 idempotence-fail）。文中行号
  一律锚 41e74b0 提交态（并席并发开发中·工作树行号会漂）。

（English brief) Workflow block ③: the unclogging closed loop. Canonical order:
dry-run first (default — `--apply` is the only write switch; dry run touches
nothing, proven by md5 equality), human review of the planned cure patterns, then
`--apply` (canonical cure-pack only, chain-root files only, structurally), then
re-verify (`rescan.residual_zero` + `resprobe.rc_ok` + empty red ledger). Honest
wall (`verdict=wall`, exit 1) reports per-root reasons instead of forcing cures.
Verdicts `unclogged|wall|rounds-exhausted` map to exit 0|1|1; usage/scenario
errors 2; fail-loud 9.
