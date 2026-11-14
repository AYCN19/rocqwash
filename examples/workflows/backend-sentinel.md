# backend-sentinel.md — 工作流嵌段①：后台哨（nohup 长驻＋JSONL 消费端）

> rocqwash v37 嵌段正典样例三件之一。对应 `README-cw.md`「工作流配合接口」⑤
> （README-cw.md:103-119）典型后台哨命令行的可整段复制版＋消费端样例＋退出码
> 分支表＋dynamic-workflow 嵌段伪码。器实况以 `tools/cw_sentinel.py` docstring
> 与 `--help` 为正本（schema `rocqwash-sentinel/1`·事件 `rocqwash-sentinel-event/1`）。
>
> **纪律红线（先读后用）**：
> - **零动作是缺省**——哨缺省 report-only，只出事件流与报告，不动任何东西；
>   `--on-red 'CMD'` 是显式旁路动作（超时帽 60s·rc≠0 不改哨退出码）
>   （tools/cw_sentinel.py:31-32 docstring「缺省无＝report-only·**零动作是缺省**」）。
> - **红是数据非器红**——CI 红/堵塞是事件数据，哨巡检照常 exit 0；
>   退出码只表器面（0 完成／2 用法错／9 信号源不可达）。
> - **loop 须给 `--state-file`**——seen 幂等持久层（rocqwash-sentinel-state/1）；
>   缺省 None＝内存态，once 单轮可用、loop 跨轮会重复出事件。
> - `--emit` 是 **JSONL append＋逐行 flush+fsync**（tools/cw_sentinel.py:31、318-321），
>   stdout 恒有镜像（响亮）；`seq` 事件流内单调，emit 在位时以文件现有行数为基
>   **跨进程续号**——消费方按 seq 排序即恢复全局序（tools/cw_sentinel.py:294-298）。

## 1. 后台哨正典命令块（整段复制执行）

```bash
# ── backend-sentinel 嵌段：三路信号源后台哨 ─────────────────────────
# 变量按你的工作区改这四行（其余原样照抄）
LEDGERS_DIR=ledgers/            # 路②：probe 台账 JSON 目录（可省略此路）
BUILDLOG=build.log              # 路③：编译日志文件（可省略此路）
WORK=.                          # 哨产物落点（events/report/state 全在此）
SENTINEL_INTERVAL=60            # 轮间隔秒

# （本段在 rocqwash 仓根执行；cw.sh 按 cx 透传 1:1，参数与退出码不改写）
# 路①CI 轮询 org/repo 的 main；②台账链根；③buildlog 词面。
# 三路可任意组合·至少一路；此处三路全开作正典示范。
mkdir -p "$LEDGERS_DIR"
nohup bash cw.sh sentinel --loop --interval "$SENTINEL_INTERVAL" \
  --watch-repo ORG/REPO --branch main \
  --watch-ledgers "$LEDGERS_DIR" --watch-buildlog "$BUILDLOG" \
  --state-file "$WORK/.sentinel-state.json" --emit "$WORK/events.jsonl" \
  --json "$WORK/sentinel-report.json" \
  >/dev/null 2>&1 &
echo "SENTINEL_PID=$!"
```

要点逐行：

| 片段 | 为什么 |
|---|---|
| `nohup … &` | 工作流后台 bash 任务形（README-cw.md:78「`--loop --interval S` 长驻哨态（后台 bash 任务用）」） |
| `--watch-repo ORG/REPO --branch main` | 路①CI 信号（`--branch` 归最近一个 `--watch-repo` 组·可重复多组） |
| `--watch-ledgers DIR` | 路②新 probe 台账→chain_graph 子进程出 TOP 链根→`blocking` 事件 |
| `--watch-buildlog FILE` | 路③tail 增量 grep 词面 `BUILD-FAIL／EXIT=134／Error:`（41e74b0 tools/cw_sentinel.py:113 `BUILDLOG_SIGNAL_RE` 同源）→`build-signal` 事件 |
| `--state-file …` | loop 必配：seen 幂等（新 run／新台账 mtime+名字／buildlog 字节 offset 全记） |
| `--emit events.jsonl` | JSONL 事件流（消费端见 §2）；stdout 镜像被 `>/dev/null` 丢弃，证据面全在 --emit/--json |
| `--json sentinel-report.json` | 每轮覆盖写 report（rocqwash-sentinel/1） |
| `>/dev/null 2>&1 &` | 哨 stdout 与 --emit 逐字节同源（emit_event 先 stdout 镜像再 append，tools/cw_sentinel.py:310-321），丢弃 stdout 不丢证据 |

**收哨**（轮帽自停或手动）：

```bash
# 正途：给 --max-rounds N（0=无限·缺省）让哨自停；
# 手动收哨才用 kill（对 PID 发 TERM，哨无 trap 特殊化，POSIX 语义直收）
kill "$SENTINEL_PID"
```

## 2. JSONL 消费端（工作流主流程这样读哨）

事件行 `json.dumps(..., sort_keys=True)`（tools/cw_sentinel.py:312）——键恒字典序，
`"kind": "ci-red"` 是**字节级稳定**的 grep 靶形：

```bash
# grep 形（零依赖·粗筛）
grep '"kind": "ci-red"'      "$WORK/events.jsonl"   # CI 红事件
grep '"kind": "blocking"'    "$WORK/events.jsonl"   # 台账堵塞链根事件
grep '"kind": "build-signal"' "$WORK/events.jsonl"  # 编译日志词面命中事件
```

```bash
# python3 纯 stdlib 形（结构化取字段·按 seq 恢复全局序）
python3 - "$WORK/events.jsonl" <<'PY'
import json, sys
for ln in sorted(open(sys.argv[1]), key=lambda l: json.loads(l).get("seq", 0)):
    ev = json.loads(ln)
    if ev["kind"] == "ci-red":
        print("CI-RED run=%s family=%s action=%s" % (ev["run"], ev["family"], ev["action"]))
    elif ev["kind"] == "blocking":
        print("BLOCKING top_root=%s dependents=%s" % (ev["top_root"], ev["dependents"]))
    elif ev["kind"] == "build-signal":
        print("BUILD-SIGNAL hits=%d" % ev["hits_total"])
PY
```

## 3. 真实输出样例（2026-11-11 铸席实跑·非手写）

**ci-red 事件行**（`--once --watch-repo org/repo --branch main --injector … --emit …
--json … --sleep-scale 0` 实测 rc 0，tmp 注入演练）：

```json
{"action": "fix-content", "branch": "main", "conclusion": "failure", "evidence": ["红件 1/1：ids=[501]", "在册族：A-content-red（判类序取先）"], "family": "A-content-red", "kind": "ci-red", "note": "ts=off (--sleep-scale 0; deterministic output)|classification=rocqwash-ci-triage/1 (ci_triage subprocess --offline)", "repo": "org/repo", "run": 178, "run_number": 9, "schema": "rocqwash-sentinel-event/1", "seq": 1, "sha": "abc123def"}
```

**blocking ＋ build-signal 事件行**（`--once --watch-ledgers … --watch-buildlog …
--sleep-scale 0` 实测 rc 0；台账 B 缺库 A→链根 A）：

```json
{"dependents": ["B"], "kind": "blocking", "ledger": "base.json", "n": 1, "note": "ts=off (--sleep-scale 0; deterministic output)|TOP chain root = first name in chain_graph rocqwash-chain-graph/1 top_order (self field judges chain-root washability; chain_graph.py:88 precedent)", "schema": "rocqwash-sentinel-event/1", "self": {"probed": true, "rc": 0, "verdict": "RC0", "washable": true}, "seq": 1, "top_root": "A"}
{"hits": ["BUILD-FAIL: round 1", "Error: Unable to locate library | A"], "hits_total": 2, "kind": "build-signal", "log": "build.log", "note": "ts=off (--sleep-scale 0; deterministic output)|tokens BUILD-FAIL/EXIT=134/Error: (classification-spectrum A/C tokens; ci_triage.py:95-118 same source)", "offset_after": 56, "offset_before": 0, "schema": "rocqwash-sentinel-event/1", "seq": 2, "truncated": false}
```

**每轮 report**（rocqwash-sentinel/1·覆盖写·节选自同次实跑）：

```json
{
 "actions": [],
 "events": [ { "action": "fix-content", "family": "A-content-red",
               "kind": "ci-red", "run": 178, "seq": 1,
               "schema": "rocqwash-sentinel-event/1" } ],
 "mode": "once",
 "round": 1,
 "schema": "rocqwash-sentinel/1",
 "sleep_scale": 0.0,
 "sources": { "ci": [ { "branches": ["main"], "new_runs": 1,
                        "red_runs": 1, "repo": "org/repo", "runs_seen": 1 } ] },
 "state_file": ".sentinel-state.json",
 "ts_enabled": false
}
```

**后台哨整块实测**（2026-11-11·tmp 演练形：`--loop --interval 1 --max-rounds 2
--sleep-scale 0 --injector …`）：哨 2 轮自停·events.jsonl 落 2 行（seq 1,2）·
`grep -c '"kind": "ci-red"'` → `1`（rc 0）·进程归零。**生产形不带 `--injector`/
`--sleep-scale`**（那两枚是离线演练钉：见 README-cw.md:88-92 纪律③）。

## 4. 退出码分支表（哨面·红是数据非器红）

| 退出码 | 含义（cw_sentinel --help／docstring 口径） | 工作流动作 |
|---|---|---|
| 0 | 巡检完成（CI 红/堵塞已作为**事件**出账·非器红） | 后台哨此码即进程收尾·主流程读 events.jsonl 断后续 |
| 1 | —（哨无 1 档：红走事件流·不走退出码） | 不会出现；出现即cw.sh 路由异常，按 9 处置复查 |
| 2 | 用法错（缺模式/双模同给/三源全缺/`--branch` 先于 `--watch-repo`/repo 形坏/负参/once 带 loop 专属参） | 后台哨启动前应被挡住——嵌段伪码 §5 把它放前置 `--once` 预检 |
| 9 | 信号源不可达（CI HTTP 4xx/5xx·netrc 缺·token 空·runs/jobs 形坏·injector 缺失/形坏/canned 未覆盖·ledgers 目录缺·state 形坏·子进程 rc≠0） | fail-loud 即停（不带病运行·tools/cw_sentinel.py:727 源硬错注记）·人工修源后重启哨 |

## 5. dynamic-workflow 嵌段伪码

```text
// 嵌段①后台哨：后台 bash 任务＋主流程消费事件流（主会话让路模式见白皮书 §3）
// 器：cw.sh sentinel（tools/cw_sentinel.py）·schema rocqwash-sentinel/1
phase "spawn-sentinel" {
  // 前置用法预检：--once 单轮跑通（exit 0）才放行后台长驻——把 2 档用法错
  // 挡在 spawn 之前；--injector + --sleep-scale 0 离线演练（纪律③）
  const probe = await world.run("bash", ["cw.sh", "sentinel", "--once",
      "--watch-ledgers", "ledgers/", "--state-file", ".sentinel-probe-state.json",
      "--json", ".sentinel-probe-report.json"]);        // 退出码即判据
  if (probe.exitCode !== 0) return { verdict: "sentinel-unusable", rc: probe.exitCode };

  // 长驻哨：后台任务（nohup … &）·world.run 只做 spawn+首查，不等它终结
  await world.run("bash", ["-c",
    "nohup bash cw.sh sentinel --loop --interval 60 " +
    "--watch-repo ORG/REPO --branch main " +
    "--watch-ledgers ledgers/ --watch-buildlog build.log " +
    "--state-file .sentinel-state.json --emit events.jsonl " +
    "--json sentinel-report.json >/dev/null 2>&1 & echo $!"]);
  // 主会话让路：后续 phase 干自己的活，只在检查点回头读事件流
}
phase "consume-checkpoint" {
  // 消费端门：grep 计数即判据（0=无红·非 0=有红事件交人审子代理）
  const reds = await world.run("grep", ["-c", '"kind": "ci-red"', "events.jsonl"]);
  if (reds.exitCode === 0 && Number(reds.stdout.trim()) > 0) {
    const triage = await agent({ role: "triage",   // 人审/分诊子代理读事件行与 report
      ask: "读 events.jsonl 的 ci-red 事件与 sentinel-report.json，按 family 给处置"});
    return { verdict: "red-forwarded", triage };
  }
  return { verdict: "no-red-events" };
}
```

> 伪码契约（dynamic-workflows SKILL §5/§10）：`world.run` 第一参是编译期字面量
> 命令名·运行时值进 args 数组；退出码即确认，不许子代理复述世界已裁决的事。

## 6. 诚实注记

- 本文全部输出样例为 2026-11-11 铸席在本仓 `tools/cw_sentinel.py`（v37 41e74b0）
  tmp 注入演练**实跑**所产，非手写；样例事件行含 `"note": "ts=off…"` 是
  `--sleep-scale 0` 演练形的确定性注记（tools/cw_sentinel.py:301-306）——生产形
  事件行带真 `ts`。文中行号一律锚 41e74b0 提交态（并席并发开发中·工作树行号会漂）。
- 样例中 `org/repo`、run 178、md5 等均为 tmp 夹具数据，非任何真仓信号。
- 消费端 grep 靶形依赖事件行 sort_keys 字节序（rocqwash 接口纪律·README-cw.md:82-86）；
  若上游器改键序，grep 形失效而 python3 形不受影响——重结构化解析优先。
- 三器接口共同纪律五条的正本在 `README-cw.md`「工作流配合接口」（README-cw.md:71-140）；
  本嵌段是其中⑤后台哨形的展开，与其逐字兼容。

（English brief) Workflow block ①: run the v37 real-time sentinel as a background
bash task (`nohup bash cw.sh sentinel --loop … --emit events.jsonl &`), consume the
JSONL event stream from the main session (grep or stdlib-python), branch on exit
codes 0/2/9 (red is data, not tool failure — it travels in events, not exit codes).
Default is report-only; `--on-red` is an explicit bypass action. `--state-file` is
required for loop idempotency. See `README-cw.md` §「工作流配合接口」 for the
normative five-discipline contract.
