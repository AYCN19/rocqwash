# ops-sentinel — 哨长驻运维手册 v1.0（2026-11-12）

> **正本声明**：本手册是 `tools/cw_sentinel.py` **长驻（--loop）运维手册**——部署／消费／
> 轮转与恢复／实证账四节，全部内容引既有实账（更新账 v37-v47 各节＋既有手册与嵌段
> 三档＋器 docstring），**零码改零新器零新旗标**（文档波·逐条命令为既有正典块转抄或
> v44/v47/v48 实跑原文转录，无杜撰形参）。行号一律锚 rocqwash v47 6217808 工作树现势
> （并发开发行号会漂·冲突以器 `--help` 与 docstring 为准）。上游手册
> `docs/ops-realtime-service-v1.0-20261111.md`（v38 态·命令块/退出码/preset 对照）与本
> 手册逐字兼容，本册只补长驻运维面：落位规范／台账化消费／轮转恢复纪律／两轮实证账。
>
> **纪律红线（全节通用·承 ops-realtime-service v1.0 §纪律 :10-18 五条不变）**：
> 1. **红是数据非器红**——CI 红/堵塞/词面命中都走事件流；哨巡检照常 exit 0，退出码只表
>    器面（0/2/9·cw_sentinel.py:101-111）。
> 2. **零动作是缺省**——哨缺省 report-only；落刀只经人审后显式 `--apply`
>    （cw_sentinel.py:47-48·unclog 干跑缺省铁律 更新账.md:3650）。
> 3. **离线演练钉**——`--injector`＋`--sleep-scale 0` 是演练形；生产形不带（生产事件行带
>    真 `ts`·cw_sentinel.py:34-35）。
> 4. **真编译必经 cpu_guard**——哨本体纯逻辑零编译不经 guard（§1.4 口径）；哨下游真编译
>    动作（unclog `--audit`/`--apply` 带 `--world` 真探）`--guard` 必给。
> 5. **loop 须给 `--state-file`**——seen 幂等持久层（rocqwash-sentinel-state/1）；缺省
>    None=内存态（cw_sentinel.py:132-135）·loop 跨轮无 state 即重复出事件。
>
> **候选溯源链**：更新账.md:3638（v37 待办 2「--loop 真后台候首个真实消费场景」）→
> roadmap-v43-plus ②（docs/roadmap-v43-plus-20261111.md:30-38·验证方式 :38）→ v44 实战
> 首演（更新账.md:3814-3834）→ v47 真仓首战（更新账.md:3895）→ v48 长驻过夜候选
> （更新账.md:3912）→ 本册成档。
>
> **v1.0 补节（20261112 工装席·部署件文档化波）**：补 §1.6 监督壳部署形（部署工件
> `examples/sentinel_supervisor.sh` 新落库＋`cw_sentinel --selftest` 增部署形冒烟矢
> ——承 v50 崩溃判例 更新账.md:3999）——哨器面旗标零改（selftest 矢量面为测试件
> 非器面）；§1.6 行号锚 v50 2ab39bc 现势，其余各节行号仍锚 v47 6217808 不变。

---

## §1 部署（长驻挂哨）

### 1.1 三旗语义与落位规范（建议仓外 CW 侧 `_log/`）

| 旗 | 语义（器面锚） | 长驻口径 |
|---|---|---|
| `--loop` | 长驻轮巡·JSONL 事件流追加（工作流后台 bash 任务用·cw_sentinel.py:87-88；argparse :1077-1078） | 与 `--once` 互斥同给 rc=2（:957-959） |
| `--interval S` | 轮间隔秒·**只属 `--loop`**（once 带之 rc=2·:966-967）·缺省 60（:1035·argparse :1079-1080） | 真实账两形：45s（v44·更新账.md:3820）／60s（正典块·README-cw.md:123） |
| `--state-file F` | seen 幂等持久层 rocqwash-sentinel-state/1（cw_sentinel.py:132-135）·**loop 须给**（argparse :1093-1095） | 每轮末落盘（:1046）·崩溃恢复纪律见 §3.1 |
| `--emit F` | 事件流 JSONL append＋逐行 flush+fsync＋stdout 镜像（cw_sentinel.py:31·:480-509） | 配 `--emit-max-bytes N` 轮转帽防无界（§3.2） |
| `--json out` | 每轮覆盖写 report rocqwash-sentinel/1（sort_keys·cw_sentinel.py:114-121） | actions 执行账在 report 不在事件流（ops-realtime-service:80） |

**落位规范（建议仓外 CW 侧 `_log/`）**：哨产物是**运行产物不入 rocqwash 仓**（工作树净·
禁 git commit 口径）——建议落仓外 ConstructiveWorld 侧 `_log/sentinel_<波>/`，三件套同盘：

```text
_log/sentinel_<波>/events.jsonl    # --emit 事件流（JSONL·§2.1 schema）
_log/sentinel_<波>/report.json     # --json 每轮 report（覆盖写·actions 账）
_log/sentinel_<波>/state.json      # --state-file seen 幂等账（§3.1/§3.3）
```

- 活体判例＝**v48 长驻落位** `/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48/`
  三件套实存（§4.3 本席实读）——落位即此形。
- `--emit`／`--state-file`／`--json` 全参数化零硬编码绝对路径（cw_sentinel.py:150-151
  诚实律）；`{emit_dir}` 取 `--emit` 所在目录（预设出账与事件流同盘·cw_sentinel.py:78）。
- 台账目录缺＝哨 rc 9 fail-loud（`--watch-ledgers`·poll_ledgers :633-634）；buildlog 缺档
  反可＝零事件非红（`present=false` 响亮注记·:704-706）。

### 1.2 标准命令（正典块·整段复制执行）

承 ops-realtime-service §1.1（:22-46）／backend-sentinel.md §1（:20-41）正典块，落位按
§1.1 改 `WORK` 变量即成——器面逐旗不改写：

```bash
# ── 长驻哨标准块（rocqwash 仓根执行·cw.sh:41-43 路由 1:1 透传）──────────
REPO=ORG/REPO                    # 路①：CI 仓（可重复多组·--branch 归最近组）
LEDGERS_DIR=ledgers/             # 路②：probe 台账 JSON 目录（可省此路）
BUILDLOG=build.log               # 路③：编译日志文件（可省此路）
WORK=/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48   # §1.1 落位
SENTINEL_INTERVAL=60             # 轮间隔秒

# 前置用法预检：--once 单轮跑通（exit 0）才放行后台长驻——把 2 档用法错挡在 spawn 前
# （ops-realtime-service:33·backend-sentinel.md:147-152）
bash cw.sh sentinel --once --watch-ledgers "$LEDGERS_DIR" \
  --state-file "$WORK/state-probe.json" --json "$WORK/report-probe.json"

# 长驻哨：三路信号源（CI runs／本地台账链根／buildlog 词面）可任意组合·至少一路
nohup bash cw.sh sentinel --loop --interval "$SENTINEL_INTERVAL" \
  --watch-repo "$REPO" --branch main \
  --watch-ledgers "$LEDGERS_DIR" --watch-buildlog "$BUILDLOG" \
  --state-file "$WORK/state.json" --emit "$WORK/events.jsonl" \
  --emit-max-bytes 104857600 \
  --json "$WORK/report.json" \
  >/dev/null 2>&1 &
echo "SENTINEL_PID=$!"
```

要点：`--branch` 须跟在 `--watch-repo` 组内（先 repo 后 branch·否则 rc=2·
parse_watch_specs :937-939）；`--emit-max-bytes` 缺省可不给（无轮转·长驻盘面自管见
§3.2）；stdout 与事件流逐字节同源（emit_event 先镜像后 append·cw_sentinel.py:485-487），
`>/dev/null` 不丢证据。

### 1.3 后台两形（nohup 形／工作流后台 bash 任务形）

| 形 | 出处 | 适用 |
|---|---|---|
| **A·nohup 形** | README-cw.md:123-129（「工作流配合接口」⑤ 典型后台哨命令行）＋backend-sentinel.md:34-40 | 人工/会话挂哨：`nohup … >/dev/null 2>&1 &`＋`echo "SENTINEL_PID=$!"` |
| **B·工作流后台 bash 任务形** | backend-sentinel.md §5 伪码（:154-160 `world.run("bash", ["-c", "nohup … & echo $!"])`）＋ops-realtime-service:299-304；让路机制白皮书（workflow-integration-whitepaper-v1.0-20261111.md:58/:115/:128「让路＝不与哨争写」） | dynamic-workflow 嵌段：spawn＋首查后**主会话让路**，只在检查点回头消费（§2.5） |

两形器面同令（cw.sh 1:1 透传·参数与退出码不改写·backend-sentinel.md:30）——差异只在
spawn 侧载体，哨自身无感知。

### 1.4 cpu_guard 包裹口径

- **哨本体不经 guard**：哨自身零编译零网络（编排律 cw_sentinel.py:143-145；run_py
  docstring「纯逻辑引擎零编译故不经 cpu_guard（probe_engine.py:10 判例：真编译才须
  guard）」:296-300）——spawn／长驻轮巡／判类（ci_triage --offline 子进程）／链根
  （chain_graph 子进程）全纯逻辑，不占编译弧。
- **on-red 预设干跑不占 guard**：unclog（不带 `--apply`＝只干跑）／wash-shape（只出
  plan）／pushci（`--dry-run`）／triage（--offline 判类）／cw-doctor（全缺省体检）五预设
  全零编译旁路动作（cw_sentinel.py:50-79 预设表·60s 帽 :229）。
- **真编译动作才须 guard**：哨红→人工启动的 unclog `--audit`／`--apply` 真探（带
  `--world`）按 ops-realtime-service §3 规程（:174-256）`--guard
  /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh` 必给（红线 :16-18）。
- **席面铁律**：本册撰写席一切执行经 `bash /Users/apple/Desktop/ConstructiveWorld/
  cpu_guard.sh -MaxWaitSec 120` 包裹（温控 v3 全席包裹律·cw-ci-sop §R2）——与器面口径
  两层不混：席面管**执行载体**，器面管**哨下游真编译**。

### 1.5 收哨

- **正途＝自停**：`--max-rounds N`（0=无限·缺省·argparse :1081-1082）——v44 判例即
  `--max-rounds 15` 跑满自停（更新账.md:3820-3821）；`--max-rounds` 只属 `--loop`（once
  带之 rc=2·:968-969）。
- 手动收哨才 `kill "$SENTINEL_PID"`（POSIX TERM·哨无 trap 特殊化·ops-realtime-service:52-53）。

### 1.6 监督壳部署形（examples/sentinel_supervisor.sh·v50 崩溃判例的运行态补偿层）

> 本节＝v1.0 补节（20261112 工装席·部署件文档化波）——行号锚 v50 2ab39bc 工作树
> 现势（其余各节仍锚 v47 6217808·承正本声明漂移注记）；部署正本＝
> `examples/sentinel_supervisor.sh`（自本机运行态 /tmp 版 1:1 泛化·路径全参数化
> 零硬编码绝对路径·中文注记·监督壳自身退出码 0/1/2/9）。

**判例源（v50 账·更新账.md:3999）**：哨长驻 **round10 IncompleteRead 崩**——真崩栈
`http.client.IncompleteRead(371261 read, 72721 expected)`（读 371261／欠 72721 字节·
传输层断流·任务书转述与 v51 器修席在飞 diff 同数互证）＝器债第二类：`api_get_json`
的 v38 退避重试只罩 `HTTPError` 状态码面（cw_sentinel.py:375-386），传输层半读位
`raw = resp.read()`（cw_sentinel.py:373）抛 `http.client.IncompleteRead`（非
URLError/OSError 子类·逃逸 :387 捕获面）→ 未捕获 traceback → rc=1 崩——**退避不护
传输层**。处置两轨：**监督壳补偿已部署**（本机运行态判例：`bash /tmp/sentinel_supervisor.sh`
nohup 常驻·本席 `ps` 实读 PID 489→guard→哨子进程三级活体）＋**器修入 v51**（韧性层
传输层瞬断有界重试＋loop 逐源 skip 兜底·并发在飞落盘）——**壳是进程级兜底非器内修
复**：v51 器修降传输层崩概率后，壳仍兜一切器内不护崩形（emit/rename 失败、OOM、机器
重启、loop 逐源 guard 面之外的上层崩）与已部署旧形运行态。

**state 零损失（本席 20261112 实读·崩后重启续接实证）**：`_log/sentinel_v48/` 三件套
——`report.json` `round=3`（重启后新进程轮号）且**无 `state_rebuilt` 键**（未走重建
·承 §3.1）；`state.json` seen 双仓咬合 Set 30／Main 31（§4.3 崩前账 30/30·重启续接
期自然新增 1）；`events.jsonl` 仍 33 行·seq 1-33 单调无重——**seen 幂等账跨崩零损失
零重报**（承 §3.3 宁重复不丢件——壳补崩溃进程不补数据·数据面由 state 续接自愈）。

**四泛化点＋rc 分诊（自 /tmp 运行态版泛化对照）**：

| 泛化点 | 正典形配置面（env·全参数化） | /tmp 运行态判例形 |
|---|---|---|
| 重启帽 | `SUPERVISOR_MAX_RESTARTS`（缺省 40·耗尽 echo 响亮 exit 1） | `for i in $(seq 1 40)` 定长环 |
| 退避 | `SUPERVISOR_BACKOFF_BASE`×2 指数·帽 `SUPERVISOR_BACKOFF_MAX`（缺省 60/600） | 固定 `sleep 60` |
| state 续接注记 | 挂壳即 echo 响亮注记（seen 幂等·跨重启零损失续接·禁静默重建） | 仅注释 |
| 定时收兵钩位 | `supervisor_withdraw_hook` **留空**（缺省 `return 0`·示例 09:00 形在函数上注释·收兵粒度＝spawn 边界·运行中收兵用人工 kill 承 §1.5） | 无钩位（人工 kill 收兵） |
| rc 分诊（泛化新增） | 子 rc=0＝轮尽自停→壳 exit 0；**子 rc=2＝用法错→不进重启环** fail-loud exit 2（重启无义·承 §1.2 spawn 前预检同律）；子 rc=9（信号源不可达）与其余 rc（含传输层崩 rc=1·IncompleteRead 判例形）→退避重启计帽 | 非 0 一律 sleep 60 重启 |
| guard 位 | `SENTINEL_GUARD`（缺省直跑——哨本体纯逻辑零编译 §1.4 口径）＋`SENTINEL_GUARD_ARGS`（缺省 `-MaxWaitSec 120`） | 硬编码 CW 侧 cpu_guard.sh 包裹 |

**部署命令形**（nohup 形 A 同款·§1.3；先 `--once` 预检再挂壳承 §1.2）——必给项
fail-loud：`SENTINEL_WORK`/`SENTINEL_WATCH_REPOS` 缺 → 壳 rc 2；repo root／哨本体／
工作目录缺 → 壳 rc 9：

```bash
SENTINEL_WORK=/path/to/_log/sentinel_v50 \
SENTINEL_WATCH_REPOS="ORG/REPO-A ORG/REPO-B" \
[SENTINEL_GUARD=/path/to/cpu_guard.sh SENTINEL_GUARD_ARGS="-MaxWaitSec 120"] \
nohup bash examples/sentinel_supervisor.sh >/dev/null 2>&1 &
```

**部署形冒烟（非真跑·cw_sentinel --selftest 增矢）**：`bash -n` 语法检＋关键行 grep
断言（重启帽／退避／state 续接注记／收兵钩位留空 `return 0`／guard 位／rc 分诊／
三件套落位名／`/Users/` 零硬编码绝对路径断言）——静态断言零执行零网络，只验部署
工件在库与结构逐点在位。

---

## §2 消费（事件流→台账→接驳→工作流）

### 2.1 JSONL 逐行 schema（rocqwash-sentinel-event/1）

事件行＝`json.dumps(..., sort_keys=True)`（cw_sentinel.py:485）——**键恒字典序·字节级
稳定 grep 靶形**（backend-sentinel.md:66-67）；行序＝产出序；`seq` 事件流内单调，emit
在位时以本体＋轮转代现有行数为基**跨进程（跨代）续号**（cw_sentinel.py:32-34·
emit_seq_base :465-477）——消费方按 seq 排序即恢复全局序。`ts` 由 time 钟出（生产带真
ts·UTC ISO8601 Z 形 :248-251）；`--sleep-scale 0` 关钟注记 `ts=off`（演练形·:34-35）。

四 kind 逐行字段表（全 cw_sentinel.py 产出形）：

| kind | 行字段 | 产出锚 |
|---|---|---|
| `ci-red` | repo/run/run_number/branch/sha/conclusion/family/action/evidence（帽 8 条 clip 200）＋note | :614-621（evidence 帽 :226-227） |
| `blocking` | ledger/top_root/dependents/n/self（self 判链根可洗性·chain_graph.py:88 判例） | :679-686 |
| `build-signal` | log/hits（帽 50）/hits_total/truncated/offset_before/offset_after | :723-729（帽 :227-228） |
| `sentinel-error` | error/code＋note（源硬错 fail-loud rc 退出前最后事件） | :1053-1056 |

真行样例（**v48 长驻实跑原文**·`/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48/
events.jsonl` 行 1·本席实读——生产形真 ts／真 run id／真 sha）：

```json
{"action": "fix-content", "branch": "chore/mac-lane-gate67-v2", "conclusion": "failure", "evidence": ["红件 1/2：ids=[128842885978]", "在册族：A-content-red（判类序取先）"], "family": "A-content-red", "kind": "ci-red", "note": "判类=rocqwash-ci-triage/1（ci_triage 子进程 --offline）", "repo": "hy7pc8gfmf-dotcom/ConstructiveWorld-Set", "run": 42513889148, "run_number": 267, "schema": "rocqwash-sentinel-event/1", "seq": 1, "sha": "726f11ae6b620474c99382c3bbad08ccac1b9796", "ts": "2026-11-11T17:29:00Z"}
```

生产形 blocking／build-signal 真行样例见 ops-realtime-service §1.3（:98-100·
2026-11-11 工装席活跑实测·真 ts）。

### 2.2 消费双形（grep 粗筛／python3 结构化）

承 backend-sentinel.md §2（:69-89）与 ops-realtime-service §1.2（:61-83）原样：

```bash
# grep 形（零依赖·粗筛——靶形靠 sort_keys 字节序）
grep -c '"kind": "ci-red"'      "$WORK/events.jsonl"   # CI 红事件计数
grep    '"kind": "blocking"'    "$WORK/events.jsonl"   # 台账堵塞链根事件
grep    '"kind": "build-signal"' "$WORK/events.jsonl"  # 编译日志词面命中事件
```

```bash
# python3 纯 stdlib 形（按 seq 恢复全局序＋读当轮 report 的 actions 执行账）
python3 - "$WORK/events.jsonl" "$WORK/report.json" <<'PY'
import json, sys
for ln in sorted(open(sys.argv[1]), key=lambda l: json.loads(l).get("seq", 0)):
    ev = json.loads(ln)
    print(ev["kind"], ev.get("family"), ev.get("top_root"), ev.get("hits_total"))
rep = json.load(open(sys.argv[2]))   # on-red 执行账在 report 不在事件流
for act in rep.get("actions", []):
    print("ON-RED rc=%s cmd=%s" % (act.get("rc"), act.get("cmd")))
PY
```

grep 形依赖键序——若上游器改键序则 python3 形不受影响，重结构化解析优先
（backend-sentinel.md:185-186 诚实注记）。

### 2.3 render-events 台账化（哨 JSONL→markdown 台账·v45 器）

`tools/render_events.py`（v45 入账·更新账.md:3844）＝纯消费端渲染器，零网络零重造：

```bash
# 单流渲染（--events 与 --dir 互斥·双给双缺均 rc=2）
python3 -B tools/render_events.py --events "$WORK/events.jsonl" \
  --md "$WORK/ledger.md" --json "$WORK/summary.json"
# 目录合并形（多文件/轮转代分片·按 (seq, ts, 来源序, 行序) 恢复全局序）
python3 -B tools/render_events.py --dir "$WORK" --md "$WORK/ledger.md"
```

- 输出：kind/family/action 三维分布表＋逐事件 9 列表（seq/kind/family/action/repo/run/
  branch/sha 前 8/evidence 首 2）；`--json` summary schema `rocqwash-render-events/1`
  （render_events.py:71·kind 全谱 :74 谱外归 other）；`--top N` family 表截断。
- **不去重**：流里有什么渲染什么（重复是流的真相非器的错·如实——render_events.py
  docstring「不去重」节）；坏行容错＝跳过＋计 bad_lines＋rc 1 出账照常（数据残缺响亮）。
- 退出码 0/1/2/9：0=渲染完成零坏行（verdict ok 或 empty 皆 0——红是数据非器红）；1=
  bad_lines>0；2=用法错；9=输入不可达（render_events.py docstring 退出码节）。
- 确定性：同输入重跑字节级恒同（selftest 幂等矢量）；溯源＝roadmap ⑧ artifact 台账化
  （roadmap-v43-plus-20261111.md:94-100）·v45 真实哨产出渲染断言（v44 14 事件 family
  分布独立重算全对·两跑字节恒同·更新账.md:3844）。

### 2.4 red_dispatch 接驳配对（哨红事件→动作预设路由·v46 器）

`tools/red_dispatch.py`（v46 入账·更新账.md:3865）读哨事件 JSONL 按 kind/family 出**动作
预设**——**配对例**承 README-cw.md:215-221（⑨ 红事件路由嵌段）原样：

```bash
# 哨态配对：--on-red 模板喂事件流整盘→路由器（suggest 档零执行出复制块）
bash cw.sh sentinel --once --watch-ledgers ledgers/ --emit events.jsonl \
  --on-red 'python3 tools/red_dispatch.py --event-file <json> --preset suggest'

# 单步直调（不经哨·对既有事件流补一轮路由账·report-only 缺省零执行）
bash cw.sh dispatch --event-file events.jsonl --preset suggest --json route.json
```

- **五路由**（路由只挂既有 cw.sh 路由零新引擎·red_dispatch.py docstring 路由表节）：B/E
  族→pushci 重派建议／A 族→manual-fix-note **禁代修**出 fix 清单／C 族→doctor 建议／
  blocking→unclog 建议（`--apply` 仅显式）／build-signal→wash-shape 建议。
- **三档 preset**：report-only（缺省零执行·零副作用）／suggest（出可复制命令块）／auto
  （**显式才代跑**·60s 帽·rc≠0 响亮入账不改退出码·red_dispatch.py docstring 头 :9-11）。
- **防重**：`--state-file` 键式 kind+repo+run+family＋cooldown 缺省 600（red_dispatch.py
  :70-76）·state 形坏 → 9 红拒不重建（**cw_sentinel.py:136 崩溃恢复纪律同款**·
  red_dispatch.py:73-74）。
- 干跑自动/落刀人审铁律保持（守门设计·roadmap ③ :40-46 既约口径不可单方面放宽）。

### 2.5 工作流嵌段（`--once` 步骤版）

`--once`＝单轮巡检出账退出，**工作流步骤用**（cw_sentinel.py:87）——三用形全既有：

1. **spawn 前用法预检**（把 2 档用法错挡在 spawn 前）：backend-sentinel.md:147-152／
   ops-realtime-service:33——`--once` 跑通 exit 0 才放行 §1.3 形 B 后台长驻。
2. **检查点单轮消费**：backend-sentinel.md:163-172 consume-checkpoint——grep 计数即判据
   （0=无红继续让路·非 0=有红交人审/分诊子代理）。
3. **真仓批量巡检首战形态**：v47 首战即 `--once` 双仓形态（更新账.md:3895·§4.2）。

嵌段伪码整段承 backend-sentinel.md §5（:143-176）——spawn-sentinel／consume-checkpoint
两 phase＋伪码契约（world.run 第一参编译期字面量·退出码即确认 :175-176）；工作流全嵌段
索引见 workflow-integration-whitepaper-v1.0-20261111.md:115（①后台哨行）与
service-layer-overview-v1.0-20261111.md:127。

---

## §3 轮转与恢复

### 3.1 state 崩溃恢复纪律（cw_sentinel.py:136 判例）

**判例原文**（cw_sentinel.py:136-141 docstring）：state 损坏（JSON 解析失败/键形坏）→
**fail-loud 9 红拒——器不吞不重建**（seen 是幂等账·静默重建＝红事件重报面失守·损坏
原件原样不动）。**恢复唯二路**：

1. **人工删件**——下轮零态起步（首次挂哨等价形：state 缺省 None／文件缺失＝零态起步，
   load_state :401-420 实现同段）。
2. **`--rebuild-state` 显式重建**——唯一合法重建路：弃既有 seen 从零起·stdout 响亮
   `STATE-REBUILD` 注记（run_sentry :1028-1033）＋report `state_rebuilt=true`（:881-882）；
   **须与 `--state-file` 同给否则 rc=2**（无 state 即无物可重建·:991-993·argparse
   :1102-1106）。

selftest ⑪ 矢量实证（cw_sentinel.py:1677-1711）：损坏红拒 9＋原件逐字节不动＋无
STATE-REBUILD 注记／同损坏件 `--rebuild-state` → rc0·红事件复现（seen 弃）·state 重生为
合法新账／rebuild 缺 `--state-file` rc=2。

**同律推广（既有器面）**：red_dispatch 防重 state 形坏 → 9 红拒不重建
（cw_sentinel.py:136 崩溃恢复纪律同款·red_dispatch.py:73-74）——seen/防重两类幂等账
同一条纪律。

### 3.2 JSONL 2 代轮转（v40 机制）

**机制**（v40 入账·更新账.md:3704/:3710「JSONL 轮转（--emit-max-bytes·保留 2 代·seq 跨
代续号不重号）」）：`--emit-max-bytes N` 追加前查超限（本体现有字节＋新行字节＞N）→
**先轮转再追加**（cw_sentinel.py:36-41·emit_event :490-501）：

```text
FILE.1 → FILE.2（旧 FILE.2 覆盖弃·保留 2 代）→ FILE → FILE.1 → 新 FILE 空
```

- 单行本身超 N＝行不可分割·空档直写（轮转后仍可能单行超帽·下轮追加前即再轮转）；
- rename 失败 → 9（rotate_emit :451-462）；轮转走 stdout 响亮注记＋report
  `emit_rotations` 计数（:883-885）；
- **seq 跨代续号**：续号基＝本体＋.1/.2 行数和（emit_seq_base :465-477）——轮转代同属
  一条事件流·消费方按 seq 排序**跨代恢复全局序**（cw_sentinel.py:40-41·ops-live-run-log:99）；
- 用法闸：须与 `--emit` 同给／N<1 → rc=2（:984-990）；
- selftest ⑫ 矢量实证（cw_sentinel.py:1713-1751）：三跑超帽→.1/.2 两代实存·
  sorted(seqs)==[1,2,3] 跨代不重号·缺 `--emit`/N=0 rc=2。
- 消费面衔接：render_events `--dir` 形可合并本体＋轮转代（§2.3·seq 跨代归位）。

### 3.3 seen 幂等语义（宁重复不丢件）

- **state 三 dict**（rocqwash-sentinel-state/1·cw_sentinel.py:132-135）：`repos.<repo>.
  seen_runs`（CI run id→conclusion/run_number/branch/family）／`ledgers`（mtime_ns+size
  同件变亦视新）／`buildlogs`（字节 offset·只认完整行防半行误报）。
- **绿 run 亦记 seen**（poll_ci_repo docstring「绿 run 亦记 seen（幂等·二跑零事件零重判）」
  :556-558·绿不出事件 :589-590）——绿也是真观测（v47 25 绿 runs 静默记 seen·更新账.md:3895）。
- **落盘时序**：每轮末 `save_state`（:1046）·**事件先 emit 后存 state·宁重复不丢件**
  （run_sentry docstring cw_sentinel.py:1024-1026）——emit 与 save 间崩溃的极端窗口可能
  重报·由消费端按 seq/state 对账消化（去重责任在消费侧·哨侧禁静默吞件）。
- **实战判例**：v44 长驻第 2-15 轮零重复事件（--state-file seen 生效·更新账.md:3824）；
  v47 二跑幂等零新事件·state seen 30/30 咬合（更新账.md:3895）。

---

## §4 实证账引用（两轮实战账·file:line 直引）

### 4.1 v44 长驻 14 事件零重复（更新账.md:3814-3834·20261111）

| 项 | 账文（行号） |
|---|---|
| 命令原文 | `cw_sentinel.py --loop --interval 45 --max-rounds 15 --watch-repo hy7pc8gfmf-dotcom/ConstructiveWorld-Set --state-file /tmp/sentinel_v44_state.json --emit /tmp/sentinel_v44_events.jsonl`（report-only 缺省·零动作）——**更新账.md:3820** |
| 行为 | 15 轮×45s 全程跑毕（12 分钟窗）·首轮 retro-triage 全战役史 30 条历史 run 经 ci_triage --offline 逐条判类——**:3821** |
| 事件 | **14 事件**（family：A-content-red×9／B-netred×1／C-toolchain-break×1／E-coqchk-skipped×1／UNRECOGNIZED×2；action：fix-content×9／rerun-after-stable-window×2／restore-toolchain×1／watch-only×2）——**:3822** |
| 判类吻合度（核心验证） | #280→A（陈旧基座时代）／#283→C（dyld 断链日）／#289→E（上传 DNS 窗）／#286 cancelled→B 连坐+UNRECOGNIZED 并列——判类与六幕实战实况逐条吻合——**:3823** |
| **幂等（本册 §3.3 判例）** | 第 2-15 轮**零重复事件**（--state-file seen 生效）＝长驻稳态实证——**:3824** |
| 证据件 | /tmp/sentinel_v44_events.jsonl（14 行 JSONL）／report／日志——**:3825** |

### 4.2 v47 首战 33 事件真仓（更新账.md:3895·20261112 凌晨）

- **真 CI 信号源实证**：`--once` 双仓（Set 30 runs/15 红·Main 30/18）→ **33 事件**
  （A19/UNREC8/E3/B2/C1）——B-netred×2 恰 Set#269/Main#22 已知 NETRED 红炉族咬合＝判类
  真值对账（更新账.md:3895）。
- 绿 25 runs 静默记 seen＝绿也是真观测；**二跑幂等零新事件**；`--loop` 真网络两轮零新
  事件（更新账.md:3895）。
- 自证面：JSONL 33 行逐行合法·schema rocqwash-sentinel-event/1·seq 递增·state seen
  30/30 咬合（更新账.md:3895 自证栏）。
- **词面勘误如实录**：`--loop-max` 旗标词面勘误→真旗标 `--max-rounds`（更新账.md:3895）
  ——本册 §1.5 旗标面即以此勘误为准。
- 账头：v47 账 20261112 凌晨（更新账.md:3888）·v48 候选「sentinel 长驻过夜＝挂真后台
  JSONL 流常驻形态首战」（更新账.md:3912）。

### 4.3 v48 长驻落位实况（§1.1 落位规范活体判例·本席 20261112 实读）

`/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48/` 三件套实存实读：

- `events.jsonl` **33 行**（全 ci-red·family 分布 A-content-red×18／UNRECOGNIZED×8／
  E-coqchk-skipped×4／B-netred×2／C-toolchain-break×1·真 run id/sha/branch·生产形真 ts）；
- `report.json`：mode=loop·round=1；
- `state.json`：rocqwash-sentinel-state/1·双仓 seen 各 30/30
  （hy7pc8gfmf-dotcom/ConstructiveWorld-Set＋…-Main）。
- 如实注记：与 v47 账 33 事件**同量级而 family 分布微异**（A19→A18·E3→E4）——两轮独立
  实跑，判类谱与 seen 面以各自 state/report 为准，本册两录不合并不修饰。

### 4.4 关联账与文档索引（全既有）

| 锚 | 内容 |
|---|---|
| 更新账.md:3638 | v37 待办 2「sentinel 长驻实跑 --loop 真后台」＝本册候选源 |
| 更新账.md:3650 | unclog 干跑缺省铁律（红线 2 器面锚） |
| 更新账.md:3704/:3710 | v40 账·JSONL 2 代轮转＋state 崩溃恢复语义入账（§3.1/§3.2 机制锚） |
| 更新账.md:3753 | v41 第三发 27/27 RC0·probe_chain 190.7s（真编译量级参照） |
| 更新账.md:3801＋perf-profile-v1.0-20261111.md:158-163 | v43 K=2 实测 101.916s＝**1.87×**（27 件同候选面两跑互证·DS4 回填）——哨下游真编译温控窗排程参照 |
| 更新账.md:3814-3834 | v44 长驻 14 事件账（§4.1） |
| 更新账.md:3844 | v45 render_events 入账（§2.3） |
| 更新账.md:3865 | v46 red_dispatch 入账（§2.4） |
| 更新账.md:3888-3914 | v47 账·33 事件真仓首战（§4.2）＋v48 候选 :3912 |
| 更新账.md:3999 | v50 崩溃判例：哨长驻 round10 IncompleteRead 崩＝传输层器债第二类·监督壳补偿已部署·器修入 v51（§1.6 判例源） |
| roadmap-v43-plus-20261111.md:30-38 | 候选② sentinel --loop 长驻首战（价值/依赖/成本/风险＋验证方式 :38） |
| roadmap-v43-plus-20261111.md:13/:35 | 积分静默窗：**观测类候选静默期零事件亦属合法观测非器红**（排程面口径） |
| ops-live-run-log-20261111.md:79-111 | 后台哨可运行态声明（依赖面 :83-85·启动命令 :87-94·JSONL 消费 :96-100·活体烟测 :102-111） |
| ops-realtime-service-v1.0-20261111.md 全册 | v38 态上游手册（命令块/preset 对照/真树活跑规程 §3/让路配合 §4）——与本册逐字兼容 |
| backend-sentinel.md 全册 | 嵌段①正典（命令块 §1/消费端 §2/退出码 §4/伪码 §5） |

---

## 附：本册边界（如实）

1. **零新造**：本册零码改零新器零新旗标——全部命令为既有正典块转抄（README-cw ⑤⑨／
   backend-sentinel §1 §5／ops-realtime-service §1 §3）或实跑原文转录（v44/v48）；唯一
   「新面」是 §1.1 落位变量取值（仓外 CW 侧 `_log/sentinel_<波>/`），系 v48 活体落位的
   规范化转述，非新机制（`--emit`/`--state-file`/`--json` 本就全参数化·cw_sentinel.py:150-151）。
2. **禁触对账**：冻结八件／quad8／更新账.md 零触碰（更新账只读引据）；零 git 写操作。
3. **行号时效**：行号锚 v47 6217808 工作树现势（并发开发会漂）——器面冲突以
   `--help`／docstring 为正本（先例：ops-realtime-service 正本声明 :3-8）。
4. **证据分级**：§2.1 v48 真行／§4.3 落位实况＝本席本波实读；§4.1/§4.2＝更新账账文直引
   （原席实跑·本席未复跑）；§2.3/§2.4 器语义＝docstring 实读。哨 `--selftest` 12 节矢量
   面与三闸回归史见 ops-live-run-log §3.4（:110）——本册未复跑自测，如实注记。
5. **v1.0 补节对账（20261112 工装席）**：§1.6 为补节——新落库部署工件
   `examples/sentinel_supervisor.sh`（上件 1「零新造」指哨器面零改·本补节不动该结论；
   部署壳是仓内 examples 新工件非器）＋`cw_sentinel --selftest` 增部署形冒烟矢（测试
   件非器面·器旗标零改）；§1.6 崩栈真形与 state 零损失证据＝本席本波实读（report/
   state/events 三件实读＋ps 活体三级实读），v51 器修面＝并发席在飞 diff 实读转述
   （其成形以 v51 账为准·本册不代账）。
