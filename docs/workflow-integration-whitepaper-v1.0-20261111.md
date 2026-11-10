# 工作流配合白皮书 v1.0（workflow-integration whitepaper·2026-11-11）

> rocqwash v37（41e74b0）·配合外部工作流引擎（dynamic workflow 等）实时动态提供
> 清洗、洗形、排障、疏通堵塞的**接口正本**。内容全部取自各器 docstring 与
> `--help` 实况（2026-11-11 逐器实取·先读后写·零凭空 API）；与
> `README-cw.md`「工作流配合接口」节（README-cw.md:71-140）同源互补——速查在彼，
> 机理在此。三正典嵌段的逐命令展开在 `examples/workflows/` 三件：
> `backend-sentinel.md`／`step-pushci.md`／`loop-unclog.md`（§2 引用）。
>
> 范围声明：本白皮书只覆盖**工作流配合面**（v37 三器 sentinel/wash-shape/unclog
> ＋v36 pushci＋v37 接口纪律）；`cw.sh`/`tests/run_tests.sh`/README 系列本体归
> 集成席所有，本文不改其一字。

**读者**：写工作流脚本（子代理编排/后台 bash 任务）的席与人。读完应能：
①按 §1 五纪律把器嵌进任意编排引擎；②按 §2 取现成嵌段；③按 §3 摆后台哨与
主会话的让路关系；④按 §4 分清 pushci 发射闸与 push_gate 推窗四判据两扇门。

---

## §1 接口五纪律（v37 三器共同·工作流按此嵌入·不必懂各器内部）

纪律正本：`README-cw.md:71-140`（速查）＋各器 docstring（机理）。逐条机理如下。

### 纪律①　JSON-in/JSON-out·schema 钦名·确定性

- 出账一律 `--json OUT`，schema 钦名：`rocqwash-sentinel/1`（每轮覆盖写）、
  `rocqwash-shape/1`、`rocqwash-unclog/1`、`rocqwash-pushci/1`；
  loop 态事件流 `--events FILE` 逐行 JSONL（sentinel 行 schema
  `rocqwash-sentinel-event/1`·键含 `seq` 事件流内单调，消费方按 seq 排序即恢复
  全局序）。
- 确定性：`--json` 落盘 `sort_keys`（README-cw.md:82-86）·同输入重跑**字节级
  恒同**；报告零墙钟零绝对路径（路径只出基名·unclog docstring「输出」节；
  `--sleep-scale 0` 时事件行 `ts` 关闭并以 `note:"ts=off…"` 注记，
  cw_sentinel.py:301-306）。
- 事件流写法：sentinel `--emit`＝JSONL **append＋逐行 flush+fsync**＋stdout 镜像
  （cw_sentinel.py:31、310-321）；unclog `--events` 进程开跑即开写
  （io.open(…, "w")·unclog.py:733，一次闭环一份流）；wash-shape `--events` 为
  loop 追加账（`--help`：「stdout 恒流·此参另落盘」）。

### 纪律②　退出码 0/1/2/9 口径（红是数据非器红·响亮 stdout）

| 码 | sentinel | wash-shape | unclog | pushci（v36 同型） |
|----|----------|------------|--------|--------------------|
| 0 | 巡检完成（CI 红/堵塞是事件数据） | clean/shaped | unclogged | success/dry-run |
| 1 | —（红走事件流） | partial/plan-miss（洗未尽·响亮出账） | wall/rounds-exhausted（诚实墙·禁硬凑） | heal-exhausted/unstable/toolchain |
| 2 | 用法错（缺模式/三源全缺/repo 形坏） | 用法错/冻结件红拒/引擎形外退出 | 用法错/注入场景形错 | fix-content/gate4-block/用法错 |
| 9 | 信号源不可达（HTTP 4xx·injector 未覆盖·子进程 rc≠0） | 路径缺失 | fail-loud（路径缺失/器红/frozen 不可得） | 目标缺失（repo/remote/分支/PR/netrc/API 不可达·watch 轮帽达） |

（正本 README-cw.md:94-101＋pushci.py:91-93。）要点：**数据红不进退出码**——
哨的红走事件流、unclog 的红走 report 红账；退出码只表器面与终局。工作流分流
因此是两级：先按退出码分器面（2=改调用·9=补目标），再读 JSON 按 verdict/kind
分数据面（§2 三嵌段各自带分支表）。

### 纪律③　--once/--loop 双模

- `--once`（sentinel/unclog 缺省）单轮出账即退——**工作流步骤内联用**；
  wash-shape 缺省即 once（plan 段零写盘）。
- `--loop --interval S` 长驻哨态——**工作流后台 bash 任务用**（nohup 形见 §3）；
  轮帽：sentinel `--max-rounds N`（0=无限）、wash-shape `--max-rounds N`、
  unclog `--loop-max N`（命周数·rounds-exhausted 非终局歇 `--interval` 再下一周；
  unclogged/wall 终局即停即退）。
- `--sleep-scale F` 全部 sleep 乘 F（0=零真睡＋关事件 ts）——离线演练/确定性
  钉，**生产形不给**。

### 纪律④　--injector 离线可测（零真网络零真编译于演练）

| 器 | injector 形 | 未覆盖语义 |
|----|-------------|-----------|
| sentinel | canned GitHub API 表（rocqwash-sentinel-injector/1·`{"responses":[{url_contains,status,body}…]}`·按序首中即用可循环复用；须与 `--watch-repo` 同给） | fail-loud 9·**绝不静默走真网络** |
| wash-shape | 子进程调用层罐装 `{引擎键:{rc,stdout,report}}`（键集 gate4/scan_v4/cure/sweep/registry_union/frozen8） | fail-loud |
| unclog | `DIR/scenario.json＝{"probe":[ledger…],"resprobe":[ledger…]}`·两类 probe_engine 调用按序严格消费；chain_graph/cure_applier/scan_v4_token/frozen8 注入下照旧真跑（真编排非傀儡） | 耗尽/缺列/形坏 fail-loud 2 |
| pushci | `--injector DIR`＋`--git-caller FILE` **必须成对**（单边给出=用法错 2·防「injector 无 canned git」静默真 push） | 失配 fail-loud |

（正本：各器 docstring「离线可测」节。）工作流自测/CI 演练一律走注入形＋
`--sleep-scale 0`：三器 `--selftest` 与套件挂接件（`tests/test_cw_sentinel.py`/
`test_wash_shape.py`/`test_unclog.py`/`test_pushci.py`·经 `tests/run_tests.sh`
t_* 四节）全部零真网络零真编译，即此纪律的自证。

### 纪律⑤　编排零新引擎

三器＋pushci 内部**全 subprocess 直调既有引擎**（README-cw.md:137-140）：
sentinel 判类全权在 `ci_triage`、链根全权在 `chain_graph`；wash-shape 五洗引擎全
subprocess（gate4/scan_v4/cure_applier/comment_sweep/registry_union）；unclog 五步
全 subprocess（probe_engine/chain_graph/cure_applier/scan_v4_token/frozen8）；
pushci 编排 v35 四器（doctor/net_probe/ci_triage/gate4 守卫·pushci.py:5-7）。
推论（对工作流作者的两条约束）：

- **编排零新引擎是双向的**——工作流侧也不要为「再判一次红/再挑一次根」写新
  逻辑：调器，读它的 JSON。器已把判据代码化（发射闸/四判据/诚实墙）。
- 真编译一律经 cpu_guard 温控包裹（CONTRIBUTING §5）：哨自身零编译零网络
  （cw_sentinel docstring「编排律」）；需要真编译的是 probe_engine 探针——
  unclog 以 `--guard PATH --guard-reg DIR --guard-front N --guard-mid N
  --guard-maxwait N` 透传（`--help` 实有）。

### 补：python3 纯 stdlib＋fail-loud＋零硬编码路径

三器纯标准库零第三方依赖（CONTRIBUTING §2 同律）；fail-loud 禁静默降级（源
不可达 9·injector 未覆盖 9·子进程 rc≠0 9——哨「不带病运行」，
cw_sentinel.py:727 源硬错注记）；全路径参数化零硬编码绝对路径（器件路径由本件
所在仓派生·pushci TOOLS_DIR 判例）。`cw.sh` 是 1:1 透传入口（exec·不改写参数与
退出码·README-cw.md:9-11）——工作流里 `bash cw.sh <tool>` 与直调
`python3 tools/<tool>.py` 语义全同，本文嵌段一律走 cw.sh 形（少一处路径耦合）。

---

## §2 三嵌段引用（examples/workflows/）

三正典嵌段＝README-cw.md「工作流配合接口」⑥（README-cw.md:121-135）的逐命令
展开，每件含：可整段复制执行的命令块＋JSONL/JSON 真实输出样例＋退出码分支表
＋与 dynamic-workflow 嵌段对应的伪码注释。**样例全部为 2026-11-11 tmp 注入演练
实跑所产，非手写**（各件「诚实注记」节自报实测形）。

| 嵌段 | 文件 | 器 | 场景 | 纪律落点 |
|---|---|---|---|---|
| ①后台哨 | `examples/workflows/backend-sentinel.md` | `cw.sh sentinel`（tools/cw_sentinel.py） | nohup 长驻三路信号源→JSONL 事件流＋消费端 grep/python3 样例 | ③loop 后台形·①事件流·②0/2/9 表 |
| ②单步推 CI | `examples/workflows/step-pushci.md` | `cw.sh pushci`（tools/pushci.py） | `--dry-run` 先行人审→真发→verdict 七态分流 | ②0/1/2/9 封册·④injector+git-caller 成对 |
| ③堵账疏通闭环 | `examples/workflows/loop-unclog.md` | `cw.sh unclog`（tools/unclog.py） | 干跑（零写盘）→人审方案→`--apply`→复核三判据·诚实墙七因分派 | ②三态封册·③/④注入形·⑤编排 |

wash-shape（`cw.sh wash_shape`→tools/wash_shape.py·正典形五洗流水）未设专嵌段：
其两段制（plan 缺省零写盘→人审→`--apply` 落刀复跑复核）与嵌段③同构——读
`README-cw.md:132-134` 三行嵌段与该器 docstring「两段制」节即可照③的人审-落刀
骨架自拼；其 loop 哨态命令行正本在 README-cw.md:112-114。

---

## §3 后台任务与主会话让路模式

「让路」= 工作流主会话（或主代理）把长驻哨交给后台 bash 任务后，**不与哨争写
同一工作集、不轮询哨进程，只在检查点读哨的自报产物**。此模式由五条机制保证
（全部锚器实况）：

1. **产物自持**：哨的全部产出走显式参数路径——`--emit`（事件流）、`--json`
   （每轮 report）、`--state-file`（seen 幂等）、unclog 另有 `--workdir`
   （逐轮台账/报告工件·缺省 mkdtemp 时 stdout 响亮报路径）。stdout 被后台任务
   重定向丢弃**不丢证据**：事件行先 stdout 镜像再 append 落盘
   （cw_sentinel.py:311-321），--emit 与 report 自足。
2. **写域互斥**：器只写自己被显式指认的出路径与 workdir；unclog 零写 `--world`
   （docstring「世界纪律」）；wash-shape 冻结件与更新账.md 自动排除、显式指认
   冻结件＝红拒 exit 2（docstring「范围与禁触面」）。主会话让路期间照常动自己的
   文件，不会踩哨的写集；哨也不会越界。
3. **有界让路**：哨不是无限挂起——`--max-rounds`／`--loop-max` 轮帽可自停；
   unclog 终局 verdict（unclogged/wall）即停即退（docstring「--once/--loop 双模」
   节）；fail-loud 9 时哨即停不带病运行（cw_sentinel.py:727）。主会话让路是
   「等到检查点/终局」，不是「永挂」。
4. **检查点回读**：主会话在 phase 检查点读事件流——grep 靶形
   `'"kind": "ci-red"'` 依赖事件行 sort_keys 字节序（纪律①），结构化消费按
   `seq` 排序恢复全局序（emit 在位时 seq 以文件现有行数为基跨进程续号，
   cw_sentinel.py:294-298）。样例与消费端正典形：`backend-sentinel.md` §2-3。
5. **真编译归 guard**：让路期间哨只发信号不做重活；真正的重活（probe 真编译）
   发生在嵌段③闭环里且必经 cpu_guard 包裹（unclog `--guard*` 透传·纪律⑤）。
   温控铁律见 CONTRIBUTING §5。

后台哨正典命令行三形（sentinel/wash-shape/unclog 各一）已在 README-cw.md:105-118
钦定；嵌段①给出其可复制版＋收哨形＋演练形注记。

**反模式（禁）**：主会话 `tail -f` 阻塞等事件（应检查点回读）；给哨挂
`--on-red` 做重活（on-red 是旁路动作·超时帽 60s·不改哨退出码——重活归工作流
读事件后的子代理步）；多哨写同一 `--state-file`/`--emit`（seq 续号与 seen 幂等
都按「单写者」假设）。

---

## §4 与 push_gate 推窗四判据的双门并立说明

**两扇门，各判各的，互不替代**（README-cw.md:57-60 同口径）：

| | 门 A：pushci 发射闸（preflight 段内） | 门 B：push_gate 推窗四判据（window 子命令） |
|---|---|---|
| 器 | `cw.sh pushci`（tools/pushci.py 五段管线第 1 段） | `python3 certify/push_gate.py window`（certify/push_gate.py·rocqwash-union-manifest 同件） |
| 判什么 | **环境能不能发射**：①toolchain doctor verdict=healthy；②net-probe 双探稳窗 STABLE；（可选 ③`--pre-scan-gate4` 头注预扫 FAIL=0） | **时机与凭证**（承战役推送窗铁律·push_gate.py:8-10「推送窗四判据」）：c1 ci-idle（CI 在飞 run=0·证据 --runs-json 或 --ci-capped-min 时间线）；c2 local≥remote（behind==0）；c3 fetch-clean（ls-remote 双读同 sha＋远端 sha 是本地祖先）；c4 cert-green（tests/run_tests.sh rc==0·可选冻结件零漂移） |
| 退出码 | 随五段 verdict 封册（pushci.py:91-93·闸不过即段停） | window：0=OPEN／1=CLOSED（含 NOT-RUN）／2=用法错／9=路径缺失（push_gate.py:65） |
| 缺证据语义 | 双闸器自带裁决（doctor/probe 出 verdict） | **NOT-RUN＝关窗·缺席旁证不计绿**（诚实律·push_gate.py:29）——fail-closed |
| 覆盖面 | 不含套件绿/behind=0/CI 在飞判（README-cw.md:58-60 明文「不在此册」） | 不含网络稳窗/工具链健康判（c1 只判 CI 在飞·证据源缺即 NOT-RUN） |

**正典并立序**（工作流嵌段②前置门）：

```bash
# 门 B 先判窗（窗不开不动门 A——省一次发射尝试）
python3 certify/push_gate.py window --repo . --branch feature/x \
  --runs-json runs.json --json window.json          # 0=OPEN 才继续
# 门 A 再跑管线（§2 嵌段②：--dry-run 先行→真发→verdict 分流）
bash cw.sh pushci --repo-path . --branch feature/x \
  --pre-scan-gate4 --json pushci-report.json
```

要点三条：

1. **不互检**：pushci 不复跑四判据，push_gate 不复跑 doctor/net-probe——重复
   判一次是浪费，漏判一扇是洞。工作流若两门都要（推窗纪律在册的仓），按上序
   串行各判各的。
2. **本器只判窗不开推**：push_gate window 全程只读（fetch/ls-remote 均远端只读
   操作·push_gate.py docstring「写域声明」），push 动作在调用方——所以两门
   天然可串：门 B 出 OPEN、门 A 出 success，各自的账各自留档。
3. **老链仍在册**：手动老链（四判据＋裸 `git push`·README-cw.md:57）合法但
   不在工作流嵌段册——工作流一律走 pushci 形（verdict 封册可分流·heal 自愈
   有界）。

---

## 附录 A　本白皮书真跑证据（2026-11-11 铸席实跑·全 tmp 零仓库写盘）

| 检查 | 命令（经 cpu_guard 包裹） | 实测 |
|---|---|---|
| 三器 --help 权威旗标 | `python3 tools/cw_sentinel.py --help`／`tools/unclog.py --help`／`tools/wash_shape.py --help`／`tools/pushci.py --help` | 全 rc 0·旗标逐条入账 |
| 哨三路实跑 | `cw_sentinel.py --once --watch-repo org/repo --branch main --injector … --emit … --json … --sleep-scale 0`（ci-red）＋`--once --watch-ledgers … --watch-buildlog … --sleep-scale 0`（blocking＋build-signal） | rc 0·事件行/report 三样例入嵌段① |
| 后台哨整块 | `nohup bash cw.sh sentinel --loop … --max-rounds 2 --sleep-scale 0 --injector … &`（tmp 演练形） | 2 轮自停·events 2 行·`grep -c '"kind": "ci-red"'`→1（rc 0） |
| pushci 干跑 | `pushci.py --repo-path . --branch main --dry-run --json …` | rc 0·计划文本＋report 样例入嵌段② |
| unclog 干跑 | `unclog.py --src … --world … --candidates … --injector … --json …`（tmp 夹具） | rc 0·cure.stage=dry-run·根件 md5 恒同（零写盘实证） |
| unclog 落刀 | 同上＋`--apply` | rc 0·stage=applied·rescan.residual_zero=true·resprobe.rc_ok=true·verdict unclogged |
| unclog 诚实墙 | `unclog.py --src … --chain-ledgers base.json --json …`（Y self-unwashable） | rc 1·wall 账样例入嵌段③ |
| 旗标对账 | 每嵌段引用旗标 grep 对照各器 `--help` 输出 | 见交付说明（全部存在·零凭空） |

未实跑项（如实声明）：pushci 真发段（需真远端凭据·用户面）；probe_engine 真编译
探针（需 rocq 世界基座·用户面·真编译必经 cpu_guard）。两者的命令形均以
`--help`/docstring 为正本给出，未经本席实跑验证运行时行为。

## 附录 B　变更与归属

- v1.0·2026-11-11：初版（§1-§4＋附录）。撰写：examples 嵌段铸造席（工作流嵌段
  三件＋本白皮书）。`cw.sh`/`tests/run_tests.sh`/README 系列归集成席；冻结八件/
  quad8/更新账.md 禁触未犯（本席会话零写上述面·全写集见文件清单）。
- 本文行号引用一律锚 v37 **41e74b0 提交态**（多席并发开发中·工作树行号会漂；
  漂移时按节名＋器 docstring 重锚）。
- 上游漂移时以各器 docstring＋`--help` 为正本修订本文；本文与器不一致视为 bug
  （CONTRIBUTING §1.5 同律）。

（English abstract) This whitepaper is the normative interface contract for
embedding rocqwash v37 tools into external workflow engines. §1 five interface
disciplines (named JSON schemas + JSONL event streams with sort_keys determinism;
exit codes 0/1/2/9 where red is data not tool failure; --once/--loop dual mode;
--injector offline canned testing with fail-loud coverage; orchestration of
existing engines via subprocess — zero new engines). §2 references the three
canonical workflow blocks under `examples/workflows/` (background sentinel /
single-step push-CI / unclogging closed loop), each with copy-paste command
blocks, real captured outputs, exit-code branch tables and dynamic-workflow
pseudocode. §3 defines the background-task yield mode: sentinels own their
declared output paths, terminate on round caps or terminal verdicts, and the main
session reads the event stream at checkpoints only. §4 states the two-gate
doctrine: pushci's preflight emission gate (toolchain + net stable-window ± gate4
pre-scan) and push_gate's four push-window criteria (ci-idle / local≥remote /
fetch-clean / cert-green, NOT-RUN = closed) are independent gates to be run in
series, never substitutes for each other.
