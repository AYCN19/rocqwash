# 真机演练汇编·收口验证实录（ops-live-run-log·20261111）

档位：收口席三闸终跑＋汇编（实跑记录性工作·零码改）。仓库：rocqwash v41·HEAD `c5df4d4`。
口径：一切数值＝本日实跑/实读所得，fail-loud 不修饰；每段注明证据文件路径或所跑命令与退出码。
禁触声明：冻结八件/quad8/更新账.md 未触；cw.sh/tests 总套/README 系列归集成席，本档未改。

---

## 一、三闸终跑实录（逐项 command＋rc＋关键输出行）

三闸命令一律经温控包裹（`bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120 --`，guard 横幅 `[cpu_guard] FRONT launch pos=0 waited=0s tlevel=0` 各跑实录在案）。

### ① doc_lint --repo（文档←→实现一致性三查·验收 drift=0）

```bash
python3 tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash --json /tmp/wash_gate1_predoc.json
```

- **run A（本档落盘前基线）rc=1·drift_total=1 —— 如实记红**：
  - `[flag] drift  docs/roadmap-v43-plus-20261111.md` ＋
    `refs=32；unresolved=7；oos=0；drift=1；L100: 缺旗标（幻引/多余引用）：--injector 前最近器 tools/baseline_diff.py help 实出无此旗标（实出 5 枚）·池 tools/baseline_diff.py,tools/doc_lint.py 亦无`
  - 其余 19 面全 ok（tool_table 20 器四处互检一致；count CASES=56 五行齐；旗标 13 面零漂）。
  - 漂源归判（git 实证）：`git status --porcelain` 示 `?? docs/roadmap-v43-plus-20261111.md`（untracked·mtime 08:00）——系**他席在飞未收件**（同批 `?? docs/rocqwash-service-campaign-total-v1.0-20261111.md` 已 drift=0），非 c5df4d4 已提交面之漂；该件归其钦定席，收口席零码改不越领地。
  - `tools/baseline_diff.py --help` 实出旗标仅 `--json --md` 两枚（实跑取证）。
- 终跑（本档落盘后重跑同令）：rc 与 drift_total 记于本日收口汇报 notes——drift 判据是树内容机械函数，本档新增 20 面入扫。
- 出账：`/tmp/wash_gate1_predoc.json`（schema `rocqwash-doclint/1`·sort_keys 确定性）。

### ② 破坏面复核矩阵（验收 17 判全过）

```bash
python3 -B tests/test_destructive_matrix.py
```

- **rc=0**，逐行实录：`== destructive-matrix: 17 行过 / 0 行破 ==`；
  `DESTRUCTIVE-MATRIX PASS: 17 行拒写判据全过（unclog×4/wash_shape×4/pushci×3/cw_sentinel×2/registry_union×2/cure_applier×2·全 tmp fixture＋injector 罐装零真网络零真仓零真编译）`
- 17 行：U1 缺 --apply 零写盘／U2 --audit 零写盘＋互斥 rc=2／U3 frozen 红拒／U4 非链根件零被动／W1 plan 缺省零写盘／W2 partial 不谎报 shaped／W3 冻结名红拒 rc=2／W4 header-map 同槽互斥 rc=2／P1 --dry-run 零副作用／P2 内容红零 rerun／P3 heal 帽尽停／S1 缺省 report-only／S2 on-red 双路同守卫 rc=2／R1 registry 干跑零写盘／R2 --apply 才落刀＋无 --out rc=2／C1 cure 干跑零写盘／C2 --apply 才落刀＋幂等败拒写——全 PASS。

### ③ 全套自测（验收零红·SKIP 列如实列）

```bash
bash tests/run_tests.sh
```

- **rc=0**，汇总行实录：`== 汇总: 52 过 / 0 红 / 4 略 / 共 56 例 ==`；
  略例行：`略例（正本环境缺·真本机全跑）: t_gate7_wrapper t_quad8_check t_gate6_born_wrapper t_verify_gate6`
  （四件逐行均为 `SKIP (正本环境缺·rc=111)`）。
- PASS 计数实证：`grep -cE ' PASS$'`＝52；首尾行 `[1/56] t_scan_selftest PASS` … `[56/56] t_baseline_diff PASS`（全套实录 `/tmp/wash_gate3_suite.log`）。
- 三闸归判：②③ 绿；① run A 红于他席在飞件（见上，不修饰）。

---

## 二、真机演练史汇（今日已发生的活体证据蒸馏）

### 2.1 audit 三发史（`/tmp/audit_run*.log` ＋ `/tmp/audit_b48_b53_baseline.json` 实读）

- **发 1**（`/tmp/audit_run.log`·06:15）：`[audit] 归集: probe 红账 27: CurriculumOptTemp,…,tlw1728R2_r2_res1_moment`（27 件全列）；`WALL: - — no-chain-root（红账 27 件无一缺库链根（代差型/器因红·禁硬凑）…）`；`[audit] timing: enumerate=None manifest=2.955s probe+chain=0.477s total=3.786s`；`AUDIT: 红账 27·墙 1——基线报告零落刀零写树（exit 0）`；`VERDICT: audit (exit 0)`。
- **发末**（`/tmp/audit_run3.log`·07:12）：`[audit] 归集: probe 红账 0: -`；`[audit] root=- cures=0 (audit baseline·red=0)`；`[audit] timing: enumerate=None manifest=1.289s probe+chain=190.728s total=194.086s`；`AUDIT: 红账 0·墙 0——基线报告零落刀零写树（exit 0）`。
- **出账**（`/tmp/audit_b48_b53_baseline.json`）：schema `rocqwash-unclog/1`；`final`: `cures_applied_total=0·cures_planned_total=0·red_files=[]·rounds_run=1·verdict="audit"·wall_count=0`；`rounds[1].probe_summary`: `n_records=27·n_red=0·red_files=[]·source="probe"`；`timing.total_s=194.086`。
- 归判：同一 `--candidates /tmp/audit27.tsv`（27 面）真机两态弧线 **红 27→红 0**，audit 全程零落刀零写树（exit 0）；墙判从「1（no-chain-root·禁硬凑）」归零。如实注记：/tmp 在档 audit 件共四（audit27.tsv·两 log·一出账），发间过程件不在档；两 log 时戳即发 1 与发末。

### 2.2 doc_lint 真仓两态（drift=3→0）

- **drift=3 态**（`/tmp/doclint_real2.json`·05:56；同日 `/tmp/dl_run_a.json`·05:59 互证同值）：三行 drift 均 `tools/ 通用入口（cli/rocqwash:9 非 _ 前缀 .py 定义）无 cw.sh case 路由（路由缺）`，target＝`tools/doc_lint.py`／`tools/netname_normalize.py`／`tools/select_audit.py`。
- **drift=0 态**（`/tmp/doclint_v41.json`·07:47；及本日 run A 出账 `/tmp/wash_gate1_predoc.json` 的 tool_table 行）：`cw.sh 四处＋tools/ 互检一致（20 器四处齐·路径咬合）＋对账零缺口（tools/ 通用入口 15 全路由）`。
- 修因：cw.sh 路由补齐落地（HEAD 提交词 `netname-normalize/select-audit routes landed`·git log c5df4d4 实读）。run A 残红唯一源＝他席在飞 untracked 件（见 §一①），已提交面 20 器表查零漂。

### 2.3 cw_doctor 真机体检（91.67 healthy）

- 证据：`/tmp/cwdoc_real.json`（04:54）。`score=91.67·verdict="healthy"·healthy_min=90.0·active_weight=60`；域账：`env`=100.0/healthy（toolchain_dyld_doctor·missing_refs=[]）；`net`=75.0/partial（up 3/4·`down_endpoints:["https://github.com"]`）；`clog`/`registry`=skip（缺省跳过·advice 如实列重跑法）。
- 归判：真机默认端点源体检过 healthy 线（90）；net 域 partial 拖分而不藏（75＝3/4·与 §2.4 同源）。

### 2.4 net_probe 真机双探（UNSTABLE 红响亮）

- 证据：`/tmp/rocqwash_livecheck_net.json`（02:22–02:23 两轮·schema `rocqwash-net-probe/1`）。两轮同形：`api.github.com`=200 ok／`productionresultssa1.blob.core.windows.net`=400 ok（可达即 ok·非 2xx 亦判）／`results-receiver-actions.githubusercontent.com`=500 ok／`github.com`=`http_code:null·ok:false` 两轮皆倒；**`verdict:"UNSTABLE"`**。
- 归判：4 端点 3 up 1 down 不入稳窗——红响亮如实判 UNSTABLE 非绿；与 §2.3 net 域 75 分互为同源实证。

---

## 三、后台哨可运行态声明（sentinel --loop·从器实况转录）

### 3.1 依赖面（tools/cw_sentinel.py 实读）

- 纯 stdlib：imports＝argparse/datetime/io/json/os/re/subprocess/sys/tempfile/time/urllib.error/urllib.request（`tools/cw_sentinel.py:153-164`）＋同目录共享件 `tools/_http_backoff.py`（`:186` sys.path 注入·退避纯函数三器共享）。**零三方包**。
- 子进程引擎全既有（编排零新引擎）：判类＝ci_triage --offline（真子进程真判类·零网络）；链根＝chain_graph.py；预设动作 unclog（**--apply 缺省不加＝疏通只干跑**）与 pushci --dry-run（缺省只打计划）。
- 外部依赖唯一面：GitHub token 取 `~/.netrc` machine github.com 行第 6 列（--netrc 参数化）；CI 路不用时零网络。

### 3.2 启动命令（cw.sh:41 实形转录）

```bash
cw.sh sentinel --once | --loop [--interval S] [--watch-repo ORG/REPO [--branch B]...] [--watch-ledgers DIR] [--watch-buildlog FILE] [--state-file F] [--emit F] [--on-red 'CMD'] [--on-red-preset NAME]... [--on-red-arg K=V] [--injector F] [--json out]
```

- 双模：--once 单轮巡检出账退出（工作流步骤用）／--loop --interval S 长驻。旗标实在性自 argparse 逐条取证（`tools/cw_sentinel.py:1075-1147`）：--once/--loop/--interval/--max-rounds/--watch-repo/--branch/--watch-ledgers/--watch-buildlog/--state-file/--emit/--emit-max-bytes/--rebuild-state/--on-red/--on-red-preset/--on-red-arg/--netrc/--timeout/--retry-max/--subproc-timeout/--injector/--sleep-scale/--json 全实出。
- 用法闸：--interval 只属 --loop，与 --once 同给 rc=2（`:966-967`）；--on-red/--on-red-preset 须伴 --emit（旁路动作必伴随事件流落盘·缺者 rc=2·同给互斥 rc=2）。

### 3.3 JSONL 消费方式（docstring＋实况）

- 事件流：--emit FILE 逐行 append＋flush＋fsync，stdout 镜像响亮。行 schema=`rocqwash-sentinel-event/1`，键 sort_keys，行序＝产出序。
- seq 流内单调：--emit 在位时以本体＋轮转代现有行数为基跨进程续号；**消费方按 seq 排序即恢复全局序**（跨代亦然——--emit-max-bytes 超限先轮转 FILE.1→FILE.2 保留 2 代·seq 跨代续号不重号）。
- 三路信号源（可组合·至少一路）：①CI 路 --watch-repo（新 completed run→jobs→ci_triage 判类·state-file seen 幂等）②本地账路 --watch-ledgers（新 probe/ledger JSON→chain_graph→TOP 链根 blocking 事件）③本地堵路 --watch-buildlog（tail 增量 grep·词面 BUILD-FAIL／EXIT=134／Error:·只认完整行防半行误报）。

### 3.4 活体烟测（本档收口时实跑·rc=0）

```bash
python3 tools/cw_sentinel.py --once --watch-buildlog /tmp/wash_sentinel_smoke_buildlog.log --emit /tmp/wash_sentinel_smoke_events.jsonl --state-file /tmp/wash_sentinel_smoke_state.json --sleep-scale 0 --json /tmp/wash_sentinel_smoke_report.json
```

- 实出事件行（/tmp/wash_sentinel_smoke_events.jsonl·节选键）：
  `{"hits": ["Error:FooBar required"], "hits_total": 1, "kind": "build-signal", …, "schema": "rocqwash-sentinel-event/1", "seq": 1, "truncated": false}` ——注意「红是数据非器红」：--once 带红事件仍 rc=0 退出（事件入账·退出码语义分离）。
- 器自测史（同日实跑实录）：`/tmp/sentinel_final.log`（06:45 前身版 11 节 PASS）→ `/tmp/final_cw_sentinel.out`（12 节全过：①once 幂等②ledger③buildlog 增量④on-red⑤loop 三轮 JSONL 序贯⑥emit sort_keys/seq⑦确定性⑧CLI 四码⑨preset 展开⑩韧性退避 403×3→[2,4,8]·Retry-After·503 耗尽 9⑪state 崩溃恢复⑫emit 轮转 2 代）——即 v41 全断言面 PASS。
- **就绪度结论**：本机 --once 烟测 rc=0 事件实出＝哨可运行；依赖面零缺＋state/emit 落盘面齐＋韧性层自测过＝--loop 长驻就绪（启动命令如 §3.2·CI 路需 netrc 在位，本地账/堵路两路零外依赖即可单跑）。

---

## 四、证据文件路径总表

| 类 | 路径 | 时戳（11-11） |
|---|---|---|
| audit 发 1 | /tmp/audit_run.log | 06:15 |
| audit 发末 | /tmp/audit_run3.log | 07:12 |
| audit 出账 | /tmp/audit_b48_b53_baseline.json | 07:12 |
| audit 候选面 | /tmp/audit27.tsv | 05:16 |
| doclint drift=3 态 | /tmp/doclint_real2.json（/tmp/dl_run_a.json 同值互证） | 05:56（05:59） |
| doclint drift=0 态 | /tmp/doclint_v41.json | 07:47 |
| doclint run A 出账 | /tmp/wash_gate1_predoc.json | 本日收口时 |
| cw_doctor 91.67 | /tmp/cwdoc_real.json | 04:54 |
| net_probe UNSTABLE | /tmp/rocqwash_livecheck_net.json | 02:22–02:23 |
| 哨自测 12 节 | /tmp/final_cw_sentinel.out（/tmp/sentinel_final.log 11 节前身） | 06:45（04:55） |
| 哨活体烟测 | /tmp/wash_sentinel_smoke_{buildlog.log,events.jsonl,state.json,report.json} | 本日收口时 |
| 闸② 全行实录 | 本档 §一②（逐行誊录） | 本日收口时 |
| 闸③ 全套实录 | /tmp/wash_gate3_suite.log | 本日收口时 |

（凡「本日收口时」＝本档撰写会话内实跑；各 /tmp 件时戳为 ls -la 实取。）
