# ops-realtime-service — 实时动态服务运行手册 v1.0（2026-11-11）

> 正本声明：本手册全部命令与字段取自器实况（`tools/cw_sentinel.py`/`tools/unclog.py`/
> `tools/pushci.py`/`tools/cw_doctor.py` 的 `--help` 与 docstring·rocqwash v38 c205ea0），
> 标注行号一律锚 c205ea0 提交态（并席并发开发中·工作树行号会漂）；全部「实测样例」为
> 2026-11-11 工装席 tmp 注入演练**实跑原文**（fixture 数据·零真网络零真编译），三判级
> 证据在 `tests/test_relay_e2e.py`（事件触发／unclog 干跑 rc=0 零写盘／JSONL 同盘
> unclog report 路径——三判全过·幂等两跑 rc=0）。器实况与本文冲突时以器 `--help` 为准。
>
> 纪律红线（全节通用）：
> - **红是数据非器红**——CI 红/堵塞/墙都是事件与报告数据；退出码只表器面。
> - **零动作是缺省**——哨缺省 report-only；落刀只经人审后显式 `--apply`（自动接驳
>   缺省干跑是铁律，tools/cw_sentinel.py:48-49、tools/unclog.py:41-44）。
> - **离线演练钉**——`--injector`＋`--sleep-scale 0` 是演练形；生产形不带（样例中
>   `"note": "ts=off…"` 即演练注记·生产事件行带真 `ts`，tools/cw_sentinel.py:34-35）。
> - **真编译必经 cpu_guard**——凡 `--world` 真探/真落刀活跑，`--guard` 必给
>   （probe_engine.py:10 判例·温控铁律）；纯逻辑编排（判类/链根/cure 干跑）零编译
>   不需 guard。

## §1 后台哨标准命令与 JSONL 消费

### 1.1 标准命令（后台长驻·整段复制执行）

```bash
# ── §1.1 后台哨标准块（在 rocqwash 仓根执行·cw.sh 按 cx 1:1 透传）──────
LEDGERS_DIR=ledgers/            # 路②：probe 台账 JSON 目录（可省此路）
BUILDLOG=build.log              # 路③：编译日志文件（可省此路）
WORK=.                          # 哨产物落点（events/report/state 全在此）
SENTINEL_INTERVAL=60            # 轮间隔秒

# 目录先立（台账目录缺＝哨 rc 9 fail-loud·buildlog 缺档反可＝零事件非红）
mkdir -p "$LEDGERS_DIR"
# 前置用法预检：--once 单轮跑通（exit 0）才放行后台长驻——把 2 档用法错挡在 spawn 前
bash cw.sh sentinel --once --watch-ledgers "$LEDGERS_DIR" \
  --state-file "$WORK/.sentinel-probe-state.json" \
  --json "$WORK/sentinel-probe-report.json"

# 长驻哨：三路信号源（CI runs／本地台账链根／buildlog 词面）可任意组合
nohup bash cw.sh sentinel --loop --interval "$SENTINEL_INTERVAL" \
  --watch-repo ORG/REPO --branch main \
  --watch-ledgers "$LEDGERS_DIR" --watch-buildlog "$BUILDLOG" \
  --state-file "$WORK/.sentinel-state.json" --emit "$WORK/events.jsonl" \
  --json "$WORK/sentinel-report.json" \
  >/dev/null 2>&1 &
echo "SENTINEL_PID=$!"
```

要点（器实况锚）：`--loop` 须配 `--state-file`（seen 幂等持久层
rocqwash-sentinel-state/1·tools/cw_sentinel.py:98-101）；`--emit` 是 JSONL append
＋逐行 flush+fsync（tools/cw_sentinel.py:31）；`--json` 每轮覆盖写 report
（rocqwash-sentinel/1·sort_keys·tools/cw_sentinel.py:81-86）；stdout 与事件流逐字
节同源，`>/dev/null` 不丢证据；给 `--max-rounds N` 哨自停，手动收哨才
`kill "$SENTINEL_PID"`（POSIX TERM·哨无 trap 特殊化）。

### 1.2 JSONL 消费端

事件行 `json.dumps(..., sort_keys=True)`（tools/cw_sentinel.py:386）——键恒字典序，
`"kind": "ci-red"` 是字节级稳定 grep 靶形；`seq` 以文件现有行数为基**跨进程续号**
（tools/cw_sentinel.py:32-33），消费方按 seq 排序即恢复全局序。

```bash
# grep 形（零依赖·粗筛）
grep -c '"kind": "ci-red"' "$WORK/events.jsonl"      # CI 红事件计数
grep '"kind": "blocking"'    "$WORK/events.jsonl"    # 台账堵塞链根事件
grep '"kind": "build-signal"' "$WORK/events.jsonl"   # 编译日志词面命中事件
```

```bash
# python3 纯 stdlib 形（结构化取字段＋读当轮 report 的 on-red 执行账）
python3 - "$WORK/events.jsonl" "$WORK/sentinel-report.json" <<'PY'
import json, sys
for ln in sorted(open(sys.argv[1]), key=lambda l: json.loads(l).get("seq", 0)):
    ev = json.loads(ln)
    if ev["kind"] == "ci-red":
        print("CI-RED run=%s family=%s action=%s" % (ev["run"], ev["family"], ev["action"]))
    elif ev["kind"] == "blocking":
        print("BLOCKING top_root=%s dependents=%s" % (ev["top_root"], ev["dependents"]))
    elif ev["kind"] == "build-signal":
        print("BUILD-SIGNAL hits=%d" % ev["hits_total"])
rep = json.load(open(sys.argv[2]))   # on-red 执行账在 report 不在事件流（§2.3 口径）
for act in rep.get("actions", []):
    print("ON-RED rc=%s cmd=%s" % (act.get("rc"), act.get("cmd")))
PY
```

### 1.3 真实输出样例（2026-11-11 工装席实跑原文·tmp 注入演练）

ci-red 事件行（`--once --watch-repo org/repo --branch main --injector … --emit …
--sleep-scale 0` 实测 rc 0）：

```json
{"action": "fix-content", "branch": "main", "conclusion": "failure", "evidence": ["红件 1/1：ids=[501]", "在册族：A-content-red（判类序取先）"], "family": "A-content-red", "kind": "ci-red", "note": "ts=off（--sleep-scale 0·确定性输出）｜判类=rocqwash-ci-triage/1（ci_triage 子进程 --offline）", "repo": "org/repo", "run": 178, "run_number": 9, "schema": "rocqwash-sentinel-event/1", "seq": 1, "sha": "abc123def"}
```

**生产形（不带 `--sleep-scale 0`）事件行带真 `ts`**——§1.1 块形状活跑实测
（2026-11-11 工装席·ledger+buildlog 双路·`--loop --max-rounds 2` 自停 rc 0）：

```json
{"dependents": ["B1"], "kind": "blocking", "ledger": "ledgerA.json", "n": 1, "note": "TOP 链根=chain_graph rocqwash-chain-graph/1 top_order 首名（self 字段判链根可洗性·chain_graph.py:88 判例）", "schema": "rocqwash-sentinel-event/1", "self": {"probed": true, "rc": 0, "verdict": null, "washable": true}, "seq": 1, "top_root": "LibX", "ts": "2026-11-10T21:43:53Z"}
{"hits": ["BUILD-FAIL at step 2"], "hits_total": 1, "kind": "build-signal", "log": "…/build.log", "note": "词面 BUILD-FAIL/EXIT=134/Error:（判类谱 A/C token·ci_triage.py:95-118 同源）", "offset_after": 29, "offset_before": 0, "schema": "rocqwash-sentinel-event/1", "seq": 2, "truncated": false, "ts": "2026-11-10T21:43:53Z"}
```

同跑 report/state 落账实证：`report: mode=loop round=2`·state 记
`ledgers=1 buildlogs=1`（seen 幂等在位·§1.1 块逐行可整段复制执行）。

### 1.4 退出码分支表（哨面）

| 码 | 含义（cw_sentinel --help／docstring 口径·tools/cw_sentinel.py:72-78） | 运维动作 |
|---|---|---|
| 0 | 巡检完成（红已作为事件出账·非器红） | 让路继续；红事件交人审分诊（§4） |
| 1 | —（哨无 1 档：红走事件流不走退出码） | 不应出现；出现按 9 处置复查 |
| 2 | 用法错（缺模式/双模同给/三源全缺/--branch 先于 --watch-repo/repo 形坏/once 带 loop 专属参/on-red 预设用法错） | spawn 前被 §1.1 预检挡住；修参重启 |
| 9 | 信号源不可达（CI HTTP 4xx/5xx·netrc 缺·token 空·runs/jobs 形坏·预设器件缺·injector 缺失/形坏/canned 未覆盖·ledgers 目录缺·state 形坏·子进程 rc≠0/超时） | fail-loud 即停（不带病运行）·人工修源后重启哨 |

## §2 on-red 预设三式对照表（report-only／unclog 干跑／pushci dry-run）

### 2.1 对照表

| 项 | report-only（缺省） | `--on-red-preset unclog` | `--on-red-preset pushci` |
|---|---|---|---|
| 性质 | 零动作是缺省（tools/cw_sentinel.py:39-40） | 预设即模板 sugar·与 `--on-red` 同一执行器（py:42-44） | 同左 |
| 展开命令（实文·py:150-155） | 无 | `python3 -B tools/unclog.py --src {src} --json {emit_dir}/unclog_{run}.json` | `python3 -B tools/pushci.py --repo-path {repo_path} --branch {branch} --json {emit_dir}/pushci_{run}.json --dry-run` |
| 必传 `--on-red-arg` | —（给了即孤儿→2） | `src=<源树根>` | `repo_path=<仓目录>`＋`branch=<分支>` |
| 缺省安全态 | — | **`--apply` 缺省不加＝疏通只干跑**（py:48-49 铁律） | **`--dry-run` 缺省＝只打计划零副作用 exit 0**（tools/pushci.py:89） |
| 触发事件 | —（report-only 也出事件） | ci-red/blocking/build-signal 三类红事件逐件代跑（py:713-716） | 同左 |
| 占位替换 | — | 静态 `{src}`/`{emit_dir}` 展开期实替（emit_dir=`--emit` 所在目录·py:53-55）；动态 `{run}`/`{family}`/`{repo}` 事件直替（py:666-674） | 同左 |
| 执行帽 | — | 60s（`ON_RED_TIMEOUT`·py:168）超时记 `rc=None` | 同左 |
| 退出码影响 | — | **旁路动作非器面：rc≠0/超时只入 actions 账＋stdout 注记，哨退出码不变**（py:37-39、682-688） | 同左 |
| v38 实测（tmp 演练） | 哨 exit 0·`actions: []` | 代跑 unclog rc=9 入账（§2.3）·哨 exit 0 | 干跑 rc=0 零副作用（实测·§2.3 末）·哨 exit 0 |

### 2.2 用法负例（全 rc=2 fail-loud·selftest 实证 py:1266-1281）

| 负例 | 码 |
|---|---|
| `--on-red` 与 `--on-red-preset` 同给（preset 即占动作槽·禁静默择一 py:44-46） | 2 |
| preset 名不识别 | 2 |
| 必传参数缺（unclog 缺 `src=`／pushci 缺任一） | 2 |
| 参数重键／无 `=`／空 K·V／未知键（unclog 给 `world=` 不属其参面） | 2 |
| preset 在场而 `--emit` 缺（`{emit_dir}` 取事件流所在目录·py:53-55） | 2 |
| `--on-red-arg` 孤儿（无 preset 在场·py:808-809） | 2 |
| 预设器件缺失（unclog.py/pushci.py 文件缺） | 9（py:656-657） |

### 2.3 实况要点：代跑 unclog 的 rc=9（v38 如实口径）

**实测原文**（tmp 演练·同 `tests/test_relay_e2e.py` 判1／哨 selftest ⑨ 判例
tools/cw_sentinel.py:1240-1265「代跑 unclog（fixture 无 --world）应 rc=9 入账」）：

```text
on-red 注记: cmd rc=9（旁路动作·不改哨退出码）
```

actions 账（`--json` report·非事件流）所记：

```json
{"cmd": "python3 -B …/tools/unclog.py --src /tmp/…/src --json /tmp/…/unclog_178.json",
 "output": "FAIL-LOUD: --world 必给（probe 真探针；离线请 --injector）\nworkdir -> …\n候选面: --src 全树枚举 2 件 -> …\nfrozen 在册: 8 件（certify/frozen8.py --ledger 实取·预检红拒）",
 "rc": 9, "seq": 1, "kind": "ci-red"}
```

运维含义（照实读）：预设模板只透传 `--src`（py:151），而 unclog 的 probe 真探针
须 `--world`（tools/unclog.py:295-296）、离线须 `--injector`——两参预设均不带。
故 **哨侧代跑＝「见红即触发」**（事件＋执行账＋报告路径钦定），**「即疏通」本体**
按 §3 规程由人启动（--audit 基线→人审→--apply 白名单）。这正是 v38 缺省干跑
铁律的落点：哨代跑永零落刀，疏通权在人。

pushci 预设干跑面**实测一枪**（2026-11-11 工装席·`pushci.py --repo-path <tmp> --branch
main --dry-run`·rc=0·零副作用）：

```text
=== FINAL VERDICT: dry-run (exit 0) ===
json -> …/pushci_probe.json
```

## §3 真实树活跑规程（unclog --audit 基线→人审→--apply 白名单）

> unclog.py:63 明文「**真树 audit 活跑归主会话**（本器只证 fixture 级）」——本节是
> 主会话执行该活跑的标准作业书；下述命令块为规程模板（真树活跑前先在 tmp fixture
> 形演练，样例见 §3.1 实测）。

### 3.0 第 0 步：体检预检（可选·推荐）

```bash
# 四域聚合体检（环境/网络/注册/堵账·只诊断零修切·schema rocqwash-cwdoctor/1）
# --src --sample N 开堵账域抽样；真探世界按 wash/world_hook.py 认证代纪律播种
bash cw.sh cw-doctor --json doctor.json --src src/ --sample 8 \
  --world world/ --guard /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh
```

### 3.1 第 1 步：--audit 堵账基线（零写盘·rc 恒 0）

```bash
# 只读审计：单遍 probe 归集→chain_graph→堵账基线报告（final=audit·cures 恒 0）
# --guard 必给（真编译温控）·--json 出基线账·workdir 收逐轮工件
bash cw.sh unclog --src src/ --world world/ --audit \
  --guard /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh \
  --workdir audit-wd/ --json audit-baseline.json
echo "AUDIT_RC=$?"    # 恒 0：红是基线数据非器红（unclog.py:54·110）
```

零写盘是**器内硬保证**：`--src` 全文件 md5 清单跑前跑后自证恒同，清单违同即
fail-loud 9 拒出账（unclog.py:57-59）；耗时各段入 `report["timing"]`（audit 唯一
非确定段·unclog.py:60-61）。互斥：`--audit` 与 `--apply`/`--loop` 同给 rc=2
（unclog.py:55-56·selftest 矢量⑩d）。

**fixture 级实测样例**（2026-11-11 工装席实跑原文·tmp 树 A/B 两件·canned 红账
B 缺 A）：

```text
=== AUDIT 只读基线（单遍 probe 归集→chain_graph·零落刀零写树）===
[audit] 归集: probe 红账 1: B
chain_top: A(n=1,washable=True)
[audit] root=- cures=0 (audit baseline·red=1)
[audit] timing: enumerate=0.0 manifest=0s probe+chain=0.064s total=0.065s
AUDIT: 红账 1·墙 0——基线报告零落刀零写树（exit 0）
report -> /tmp/…/unclog_178.json
VERDICT: audit (exit 0)
```

### 3.2 第 2 步：人审（读基线账什么）

| 读什么 | 字段（rocqwash-unclog/1） | 判读 |
|---|---|---|
| 红账 | `rounds[0].probe_summary.red_files`／`final.red_files` | 本轮堵面全名单 |
| 可洗链根榜 | `rounds[0].chain_top[].lib`＋`.self.washable` | `washable=true` 者入白名单候选 |
| 墙账 | `wall.<root>.reason` | `self-unwashable`/`cure-miss`/`frozen-in-service`/`root-file-missing`/`exclusive-group-conflict`/`no-chain-root`（unclog.py:35-39·696-703）——禁硬凑·人审定夺 |
| 链根件 | `rounds[0].root_file`（`<src>/<根>.v`） | 落刀对象只此形（pick 之外无 cure 调用路径·unclog.py:43-44） |

### 3.3 第 3 步：--apply 白名单活跑（人审放行后）

白名单机制＝`--candidates TSV`（源①·probe_engine 同款表头「件名\tmd5」）：候选面
收窄到人审放行件，链根只从白名单账出、落刀只对白名单链根件。

```bash
# 白名单 TSV：只列人审放行的链根件（md5 与基线时点一致·probe_engine 同款表头）
printf '件名\tmd5\nA\t<audit 时点 md5>\n' > cands-whitelist.tsv
# 活跑：--apply 单开关（缺省关）·--rounds 帽防自旋·洗后复核自动在环内
bash cw.sh unclog --src src/ --world world/ \
  --candidates cands-whitelist.tsv --apply --rounds 5 \
  --guard /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh \
  --workdir apply-wd/ --json apply-report.json --events apply-events.jsonl
echo "APPLY_RC=$?"    # 0=unclogged·1=wall/rounds-exhausted（读账定夺·红是数据）
```

器内结构保证（无需人盯）：落刀只对链根件（unclog.py:43-44）；只正典包
cure_pack v1.3 禁 freeform（unclog.py:42-43）；frozen 在册（certify/frozen8.py
--ledger 实取）预检红拒 fail-closed（unclog.py:45-47）；落刀幂等断言败即拒写
（`idempotence-fail`·unclog.py:614-617）。

### 3.4 第 4 步：复核与终判

环内自动复核：受治件 rescan（cured token 残差应零）＋resprobe（rc 应 0·世界换代
后）——`rounds[k].rescan.residual_zero`／`resprobe.rc_ok` 如实出账不粉饰
（unclog.py:16-17、632-649）。终判三态：`unclogged` exit 0／`wall` exit 1（诚实
墙·逐根列不可洗因）／`rounds-exhausted` exit 1（`--rounds` 帽尽·附各轮账）。
世界换代口径：本器零写 `--world`，洗后复探红是否清账取决于世界 .vo 基座换代
（unclog.py:115-116）——复探未达即如实入账，禁硬凑。

## §4 与主会话让路配合（后台 bash 任务＋通知驱动）

### 4.1 让路模型

哨不推通知——**事件流即通知面**（`--emit` append＋逐行 fsync·seq 跨进程续号·
tools/cw_sentinel.py:31-33）。配合形＝主会话把哨 spawn 成后台 bash 任务后**让路
继续干自己的活**，只在检查点回头消费事件流与当轮 report；红是数据非器红，哨
exit 0 即让路合法（README-cw.md「工作流配合接口」⑤·backend-sentinel.md §5 同形）。

产物三件套（全在 `--emit` 同盘）：

| 产物 | 写形 | 消费口径 |
|---|---|---|
| `events.jsonl` | append＋fsync·事件面 | 检查点 grep/按 seq 排序读（§1.2） |
| `sentinel-report.json` | 每轮覆盖写·**actions 执行账在此**（§2.3 口径） | 检查点读当轮 `actions[]` |
| `unclog_{run}.json`／`pushci_{run}.json` | 预设代跑出账·路径由预设钦定（{emit_dir} 同盘·py:53-55） | 存在性＋verdict 读 |

### 4.2 通知驱动检查点协议

```bash
# 检查点消费（主会话每次让路归来执行·零依赖两查）
WORK=.
grep -c '"kind": "ci-red"' "$WORK/events.jsonl"          # ①事件面：红事件计数
python3 -c "import json,sys; r=json.load(open('$WORK/sentinel-report.json')); print('round=%s actions=%d' % (r['round'], len(r['actions'])))"
                                                          # ②执行面：代跑账笔数
# 分流：0 红 0 账→继续让路；有红有账→红件交人审分诊（§3 规程启动）
```

收哨：`--max-rounds N` 自停为正途；手动才 `kill "$SENTINEL_PID"`（§1.1）。

### 4.3 dynamic-workflow 嵌段伪码（spawn＋检查点·on-red 预设形）

```text
// 嵌段：后台哨＋on-red 预设 unclog＋让路检查点（形承 backend-sentinel.md §5）
phase "spawn-sentinel" {
  // 前置 --once 用法预检（把 2 档用法错挡在 spawn 前）
  const probe = await world.run("bash", ["cw.sh", "sentinel", "--once",
      "--watch-ledgers", "ledgers/", "--state-file", ".sentinel-probe-state.json",
      "--json", ".sentinel-probe-report.json"]);
  if (probe.exitCode !== 0) return { verdict: "sentinel-unusable", rc: probe.exitCode };
  // 长驻哨：旁路动作用预设 unclog（缺省干跑铁律·代跑账入 report.actions）
  await world.run("bash", ["-c",
    "nohup bash cw.sh sentinel --loop --interval 60 " +
    "--watch-repo ORG/REPO --branch main --watch-ledgers ledgers/ " +
    "--state-file .sentinel-state.json --emit events.jsonl " +
    "--json sentinel-report.json --on-red-preset unclog " +
    "--on-red-arg src=src/ >/dev/null 2>&1 & echo $!"]);
  // 主会话让路：后续 phase 干自己的活
}
phase "consume-checkpoint" {
  const reds = await world.run("grep", ["-c", '"kind": "ci-red"', "events.jsonl"]);
  if (reds.exitCode === 0 && Number(reds.stdout.trim()) > 0) {
    // 红件交人审：疏通本体按 §3 规程（--audit 基线→人审→--apply 白名单）
    const triage = await agent({ role: "triage",
      ask: "读 events.jsonl 与 sentinel-report.json 的 actions 账，按 §3 启动疏通" });
    return { verdict: "red-forwarded", triage };
  }
  return { verdict: "no-red-events" };
}
```

### 4.4 接驳全链实测（tmp 演练·三站·`tests/test_relay_e2e.py` 三判所证）

```text
站①哨腿（canned CI 红炉 run 178→on-red preset 代跑）：哨 exit 0·events.jsonl 落
   ci-red 1 行（seq 1）·actions 账 cmd=preset 展开（含 unclog_178.json 路径）·
   代跑 rc=9 如实入账（§2.3）
站②unclog 干跑腿（同一 tmp 树 --audit --injector canned 红账）：rc=0·verdict=
   audit·见红 red_files=[B]·出可洗链根 A(washable=true)·cures 恒 0·src md5
   清单前后恒同（零写盘）
站③同盘对拍：actions[0].cmd 钦定路径 {emit_dir}/unclog_178.json ≡ 实落 report
   （schema rocqwash-unclog/1·verdict audit）
```

三判回归：`python3 -B tests/test_relay_e2e.py`（0=三判全过·1=任一红响亮列红）。

## 附：样例与证据索引

| 证据 | 处 |
|---|---|
| §1.3/§2.3/§3.1/§4.4 实测样例 | 2026-11-11 工装席 tmp 注入演练实跑原文（fixture 数据·org/repo、run 178、md5 均非真仓信号） |
| 三判级回归 | `tests/test_relay_e2e.py`（判1 事件触发／判2 unclog 干跑 rc=0 零写盘／判3 JSONL 同盘 unclog report 路径） |
| 嵌段正典三件 | `examples/workflows/backend-sentinel.md`／`step-pushci.md`／`loop-unclog.md` |
| 接口纪律正本 | `README-cw.md`「工作流配合接口」①-⑥ |
| 器实况正本 | 各器 `--help`＋docstring（行号锚 c205ea0·冲突以器为准） |
