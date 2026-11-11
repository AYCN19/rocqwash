# 性能剖面报告 v1.0（perf profile·2026-11-11）

> `tools/unclog.py --audit` probe 剖面的首份在库实录：**v40 audit 真编译实测**
> ＋**v41 并行层 tmp 夹具机制实测**＋**K=1 vs K=2 真编译墙钟剖面的方法与占位**
> （如实——可测者录实测·不可测者录方法禁编数字）。采集法正本在
> [`examples/baselines/perf-README.md`](../examples/baselines/perf-README.md)
> （probe --jobs K 剖面采集三步·墙钟非确定注记·采样规模≤30 件·记录模板）。
> 本报告全部数字**逐字照录**自列明数据源（tmp 件易失·照录即在库正本）·零推算
> 充实测；推导值显式标注「推导」。文中旗标引用经 `tools/doc_lint.py` ③旗标查
> 对照 `--help` 实出机检。

## 一、数据源清单与可测性判定

| 源 | 内容 | 性质 | 可测性判定 |
| --- | --- | --- | --- |
| DS1 | `/tmp/audit_b48_b53_baseline.json`（2026-11-11 07:12 产·配对日志 `/tmp/audit_run3.log`） | v40 audit **真编译**实测（timing 段＋args 溯源） | 已测——§二照录 |
| DS2 | `/tmp/perf_profile_fixture/`（本席 tmp 夹具·07:27 三跑） | v41 `--probe-parallel` tmp 夹具 **injector canned 计时** | 机制可测已测（§三）——**并行墙钟剖面不可测**（canned 零真编译·K 旁路） |
| DS3 | `/tmp/probe_jobs_verify.py`·`/tmp/probe_jobs_edge.py`·`/tmp/unclog_pp_verify.py`（并行席夹具·本席逐一实跑） | v41 并行机制实证（stub rocq·overlap 采样） | 已测——§四照录 |
| DS4 | K=1/2/3 真编译墙钟三跑（同候选面·timing 段差分） | 并行剖面主数据 | **未测→方法＋占位**（§五·真树 audit 活跑归主会话——`tools/unclog.py` docstring 同律） |

DS1 溯源注记：该路径当日早先曾为 rc=127 快败跑产物（rocq 不在 PATH·零真
编译）；07:12 由真编译跑重产（`args.rocq_cmd` 已为实 coqc 路径·27 件全
RC0·red=0）——本报告以 07:12 版为准（已逐字读验）；其 `--src` 源树
ConstructiveWorld_Live 系真树快照·跑后已清场（现不在盘·running 时点在盘）。

## 二、v40 audit 基线实测（DS1 照录）

`report["timing"]`（schema `rocqwash-unclog/1`·audit 形·**无 jobs 字段**——
该跑先于 v41 维度字段·缺位语义＝K=1 串行缺省·与 v41 新账 `jobs:1` 同参数
直接可比）：

```json
{"enumerate_s": null, "manifest_s": 1.289, "probe_chain_s": 190.728,
 "total_s": 194.086}
```

args 溯源（照录）：`candidates=audit27.tsv`（**27 件**·≤30 件采样规模判例）
·`src=ConstructiveWorld_Live`·`world=probe_world_v38`·`rocq_cmd` 实 coqc
（opam93）·`injector=null`·`guard=null`。战况面：`n_records=27`·`red=0`·
`wall_count=0`·verdict audit·exit 0（红是基线数据非器红·本跑全绿）。

推导判读（显式推导·非实测新数据）：

- probe 段占比＝190.728/194.086≈**98.3%**——剖面主段即 probe_chain_s；
  manifest/enumerate 是环境噪声段。
- 串行单件均摊＝190.728/27≈**7.06 s/件**（真编译绿径）——DS4 三跑的量级
  参照（K=1 一跑即 ~190s 量级·三跑总墙钟分钟级·温控可行）。

## 三、tmp 夹具机制实测（DS2 照录）

夹具：`/tmp/perf_profile_fixture/`——src 三件链（C←B←A·极简正文）＋
`cands.tsv`（3 件）＋`inj/scenario.json`（probe canned 台账一发：A RC0·
B/C RED-MISSING_LIB·喂真 chain_graph）·**零真编译**（canned 罐装·K 旁路）。
命令形（三跑仅 K 与出账路径异·一切执行经
`bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120`
包裹）：

```bash
python3 tools/unclog.py --src /tmp/perf_profile_fixture/src \
  --candidates /tmp/perf_profile_fixture/cands.tsv \
  --world /tmp/perf_profile_fixture/world \
  --audit --injector /tmp/perf_profile_fixture/inj \
  [--probe-parallel K] --workdir <wd> --json <out.json>
```

三跑 `report["timing"]` 照录（A/B＝同命令 K=1 双跑·C＝`--probe-parallel 2`）：

| 跑 | K | jobs | enumerate_s | manifest_s | probe_chain_s | total_s | rc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 1（缺省） | 1 | null | 0.001 | 0.078 | 0.079 | 0 |
| B | 1（缺省） | 1 | null | 0.001 | 0.102 | 0.104 | 0 |
| C | 2 | 2 | null | 0.001 | 0.089 | 0.091 | 0 |

机检四判（本席核验脚本 rc=0·照录）：

1. **jobs 维度入账**：timing 段 `jobs` 值 1/1/2 各录其值＝`--probe-parallel`
   实参·stdout 响亮行同步出 `timing: jobs=K`——前后跑可比面就绪。
2. **墙钟非确定**：A/B 同命令双跑 probe_chain_s 0.078→0.102（逐跑必异）·
   而 **jobs 维度恒同**——剖面差分只认段值趋势不认单跑毫秒。
3. **A vs B**：除 timing 段外逐键恒同（「同输入重跑字节恒同」对 timing 段
   之外全成立·本席机检 PASS）。
4. **A vs C**：除 timing 段＋`args.probe_parallel` 实参（1→2·K 记账在
   args）外逐键恒同（本席机检 PASS）。

判读界线：本表 probe_chain_s 差异属 canned 罐装噪声（0.078/0.102/0.089 同
量级散布）·**不是并行加速证据**——canned probe 零真编译·K 旁路照记。机制
（字段在账·值随 K 走）已实证；加速面归 DS4。

## 四、v41 并行机制实证（DS3 照录·本席逐一实跑）

并行席 `wash/probe_engine.py --jobs`（ThreadPool 分片·典序收账）＋
`tools/unclog.py --probe-parallel`（透传）落地后·三份 tmp 夹具脚本本席实跑
全过（rc=0·stdout 尾行照录）：

- `probe_jobs_verify.py` → `PROBE-JOBS-VERIFY PASS`：K=1 串行 overlap=1；
  K=3 **真并发 overlap=3** 且**台账字节恒同**（完成序不侵入输出序·确定性
  铁律）；per-件 log 独立＋世界零残留。
- `probe_jobs_edge.py` → `PROBE-JOBS-EDGE PASS`：K>1 候选重名 fail-loud
  rc=2；K=4×`--guard` 包裹 rc=7 真取透传；resume SKIP 先行台账恒同。
- `unclog_pp_verify.py` → `UNCLOG-PP-VERIFY PASS`：闭环 `--probe-parallel 3`
  透传生效（overlap=3·非仅 argv 静读）；**--audit 同享同参**（K=2 probe 真
  跑 overlap=2）；`--probe-parallel 0` 用法闸 rc=2。

即：**机制层 K=1 vs K>1 已实证**（真并发·确定性·audit 同享）；未实证的
只剩**真编译墙钟剖面**（DS4）。

## 五、K=1 vs K=2 真编译墙钟剖面——方法＋占位（如实）

**可测性判定：不可测（本席职权内）**。真树 audit 活跑归主会话
（`tools/unclog.py` docstring·`examples/baselines/README.md` §3 同律）；
tmp 真编译夹具（stub/极简件）信号噪声比不足·合成重编译件属另造基准非现势
剖面——均不采。零编数字：下表只立占位·待真树三跑回填。

方法（采集法正本 `examples/baselines/perf-README.md` §2·摘要）：同候选面
（≤30 件·DS1 判例 27 件）固定 `--src/--world/--rocq-cmd/--candidates`·
K=1/2/3 各一跑（`--probe-parallel K`·真编译经 `--guard` 包裹·温控 K≤2
建议）·各 `--json` 出账·timing 段差分（`probe_chain_s` 主指标·`jobs` 维度
在账前后可比）。

实测（真树 27 件面·三行已回填实数——K=1/K=2 照录 20261111 账·K=3 为
20261112 实跑回填·回填段详注）：

| 跑 | K | timing.jobs | probe_chain_s | total_s | 备注 |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | （缺位＝1 语义） | 190.728 | 194.086 | 串行基线——DS1 同面参照 190.728（20261111 账照录） |
| 2 | 2 | 2 | 101.916 | 105.436 | 温控 K≤2 建议——v43 双跑回填（20261111 08:1x） |
| 3 | 3 | 3 | 165.202 | 169.684 | 建议与跑 2 错峰——20261112 实跑·负边际（回填段详注） |

判读参照（定性·禁以参照代实测）：DS2/DS3 已证 K>1 真并发且台账确定性零漂
——真编译墙钟收益面取决于逐件编译并行度（probe 段近似逐件独立·理想加速
量级受 guard FRONT 槽位与热钳位约束）·真值以三跑 timing 段差分为准。

## 六、结论与后继

1. `report["timing"]["jobs"]` 维度字段已入账（v41·本席）——v40 旧账缺位
   语义 K=1 可比·新账缺省恒带；回归全绿（§七）。
2. 采集法就绪（perf-README·三步＋模板＋≤30 件温控）。
3. DS4 真树三跑归主会话：回填 §五占位即成完整并行剖面（下一版 v1.1）。

## 七、本报告机检清单（全部本席实跑·经 cpu_guard 包裹）

| # | 命令 | rc |
| --- | --- | --- |
| 1 | `python3 -B tools/unclog.py --selftest` | 0（十四矢量全过·含⑬jobs 维度） |
| 2 | `python3 -B tests/test_unclog.py` | 0（3 过/0 红） |
| 3 | tmp 夹具三跑（§三命令形 A/B/C） | 0/0/0 |
| 4 | `python3 -B /tmp/perf_profile_fixture/compare_runs.py` | 0（四判 PASS） |
| 5 | `python3 -B /tmp/probe_jobs_verify.py` | 0 |
| 6 | `python3 -B /tmp/probe_jobs_edge.py` | 0 |
| 7 | `python3 -B /tmp/unclog_pp_verify.py` | 0 |
| 8 | 全套回归：`tests/run_tests.sh`＝**52 过/0 红/4 略/56 例 rc=0**（t_unclog/t_doclint/t_destructive_matrix/t_baseline_diff/t_probe_engine 全过）；`tests/test_destructive_matrix.py` 单跑＝**17 行过/0 破 rc=0**；`tools/doc_lint.py --repo .`＝**verdict consistent rc=0**（本报告 refs=29·drift=0·oos=0） | 0/0/0 |

——第 8 项结果以最终回归实跑为准（本席交割时回填账面）；§二~§五数字全部
来自 §一所列文件逐字照录。


## 20261111 08:1x 回填：DS4 真树实测（主会话·路线图①收口）

| 跑 | K | probe_chain_s | total_s | n_records | n_red | 证据 |
|---|---|---|---|---|---|---|
| DS1（v41 基线） | 1 | 190.728 | 194.086 | 27 | 0 | examples/baselines/audit-ConstructiveWorld_Live-20261111.json |
| DS4（本轮回填） | 2 | 101.916 | 105.436 | 27 | 0 | examples/baselines/perf-ConstructiveWorld_Live-k2-20261111.json |
| DS4-k3（20261112 实测席） | 3 | 165.202 | 169.684 | 27 | 0 | examples/baselines/audit-k3-20261112.json |

**实测加速比＝1.87×**（probe_chain 口径·27 件同候选面·同世界 /tmp/probe_world_v38·同 rocq-cmd 9.3 coqc 模板·cpu_guard 包裹）。jobs 维度字段（v41 增）双跑实测在账（K=1 缺位语义/K=2 显式 2）。两次 n_red=0 互证＝27 件新落位面在现役世界代际 RC0 稳定复现（非偶然单跑）。

## 20261112 K=3 回填：三账齐·负边际加速如实录（DS4 收口）

K=3 真跑（rc=0·cpu_guard FRONT pos=1 waited=0s·`--probe-parallel 3`·同候选面 /tmp/audit27.tsv·同世界 /tmp/probe_world_v38·同 K=1/K=2 字面 rocq-cmd coqc 模板）：
`timing = {enumerate_s: null, jobs: 3, manifest_s: 2.574, probe_chain_s: 165.202, total_s: 169.684}`·27/27 RC0·red=0·墙=0·probe 台账 md5_match 27/27 全真。

**加速比三账对表（probe_chain 口径）：K1/K2/K3＝190.728/101.916/165.202 → K1/K2＝1.87×·K1/K3＝1.15×·K3 较 K2 慢 1.62×（K2/K3＝0.62）＝负边际加速·DS4 纪律如实录·禁编数字禁凑绿**。total 口径同向（194.086/105.436/169.684）。判读（单跑读数·律 1 噪声带未复跑采样＝趋势级）：**并行收益在 K=2 档位现拐点——现机（4 CPU）现职守面 K=3 无收益**。挤压嫌疑注记（如实·不作开脱）：跑时另一席 nice-19 coqchk 17 件后台在飞·guard 热态预检 tlevel=58→launch 60（K=2 跑为 0）·pmset CPU_Speed_Limit=100% 无热钳位；K=3 与 K=2（前日 08:14）错峰合规。

口径可比性机检（本席实跑）：恒同面 K=3 vs K=2 除 timing 段＋`args.probe_parallel` 外逐键恒同（0 键差）；`baseline_diff` 双向（K1↔K3·K2↔K3）verdict=stable·候选面四元组 `source=tsv·src=ConstructiveWorld_Live·candidates=audit27.tsv·chain_ledgers=-` 恒同·rc=0。账名按任务书指定 `audit-k3-20261112.json` 落仓（perf-README §2 命名律本名形 `perf-ConstructiveWorld_Live-k3-*.json`·四元组内嵌恒同·diff 实测无误配·如实注记）；rocq-cmd 取 K=1/K=2 同字面 coqc 模板而非 bin/rocq（args 段一致为先决·perf-README §2——模板词「rocq」系 rocq93 套件泛指）。
