# examples/baselines/perf-README.md — probe 剖面采集规程 / Perf profile protocol

（中文）本件是 [`README.md`](README.md)（堵账基线入仓/对比规程）的**姊妹件**：
那页管**战况面**（红账/墙账·degraded 是回退信号），本页管**器速面**（probe
剖面·timing 段差分）——**两轴分离律**：性能剖面对象恰是基线文件唯一非确定
段（timing）·故剖面账与堵账基线分轴收账·对比判读互不越界（README §4
「人工判读不得凭耗时断言战况」的镜像律＝战况判读也不凭耗时·器速判读只认
timing 段）。对象器＝`tools/unclog.py --audit`（probe 归集一段占真编译跑的
绝对主段·见 `docs/perf-profile-v1.0-20261111.md` §二实测：98.3%）。

## 1. 剖面对象（timing 段＋jobs 维度）

`--audit` 报告 `report["timing"]`（schema `rocqwash-unclog/1`）：

```json
{"enumerate_s": null, "manifest_s": 1.289, "probe_chain_s": 190.728,
 "total_s": 194.086, "jobs": 1}
```

- `enumerate_s`（--src 全树枚举段·`--candidates` 喂面时 null）／
  `manifest_s`（跑前 md5 清单段）＝环境噪声段；`probe_chain_s`（probe 归集
  ＋chain_graph）＝**剖面主指标**；`total_s`＝核对面。
- `jobs` 维度＝`--probe-parallel K` 实参（`wash/probe_engine.py --jobs`
  透传值·缺省 1）——v41 始入账；**缺位（v40 旧账）语义＝K=1 串行**·与新账
  `jobs:1` 直接可比。同候选面异 K 的前后跑凭此字段对轴。

## 2. 采集法（probe --jobs K 剖面采集三步）

**第一步·固定面**：候选面用 `--candidates TSV` 直接代入（枚举面引入 enumerate
噪声）·同一 TSV 三跑复用；`--src/--world/--rocq-cmd/--timeout` 全固定——
`args` 段逐跑全记·前后可比面以 args 段一致为先决（任一异即伪信号·禁比）。

**第二步·三跑**：K=1/2/3 各一跑（`--probe-parallel K`）·各 `--json` 出账·
命名 `perf-<域>-k<K>-<yyyymmdd>.json`（`<域>`＝候选面域·同 README §2 命名
律**分轴**——perf 前缀不入 `audit-` 基线序列·防对比器误配）：

```bash
python3 tools/unclog.py --src <源树根> --world <世界目录> \
  --candidates <面>.tsv --audit --probe-parallel <K> \
  --guard tools/cpu_guard.sh --guard-reg <登记表> \
  --json /tmp/perf-<域>-k<K>-<yyyymmdd>.json
```

**第三步·差分**：三跑 timing 段并排·`probe_chain_s` 为主指标读 K 效应；
`manifest_s/enumerate_s` 作噪声参照；`total_s` 交叉核对。真编译跑的 K 效应
判读只认**三跑趋势**（同段值跨 K 的量级差）·不认单跑毫秒（§3）。

## 3. 墙钟非确定注记（判读三律）

timing 段＝实测墙钟·**逐跑必异**（报告唯一非确定段）——同命令 K=1 双跑
tmp 夹具实证：probe_chain_s 0.078→0.102（`docs/perf-profile-v1.0-20261111.md`
§三·A/B 跑）。判读三律：

1. **单跑不下结论**：同 K 复跑一发出噪声带（两跑散布量级）再读 K 效应；
2. **恒同面先验**：除 timing 段（及 `args.probe_parallel` 实参自身）外·
   同输入重跑逐键恒同——差分出现越界键即夹具/参数漂移·弃账重采；
3. **canned 不算剖面**：`--injector` 罐装零真编译·K 旁路照记（机制可测·
   加速面不可测）——墙钟剖面必须真编译跑。

## 4. 建议采样规模（≤30 件·温控）

- **候选面 ≤30 件**：27 件判例（audit27.tsv）真编译串行 ≈7.06 s/件·
  190.728s/跑（v40 audit 实测·报告 §二）——K=1/2/3 三跑总墙钟分钟级·
  单面容量与温控窗口均以 ≤30 件为限；超面跑分批分域。
- **温控**：一切执行经 `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh`
  包裹；真编译跑加 `--guard`（probe_engine 逐件经 guard·FRONT 档自带钳位）；
  **K>1＝机内多 rocqworker 并发＝热负载↑——K=2 建议档·K=3 跑与前跑错峰**
  （`wash/probe_engine.py` docstring 温控警示同源·注记不强制·用户自裁）。
- **真树 audit 活跑归主会话**（`tools/unclog.py` docstring·README §3 同律）
  ——perf 席只证 fixture 级·真树三跑由主会话按本规程执行。

## 5. 记录模板

```markdown
## probe 剖面记录（<域>·<yyyymmdd>）

- 面：--candidates <面>.tsv（N 件≤30）·src=<源树基名>·world=<世界基名>
- rocq_cmd：<模板原样>·guard=<档位>·产账人=<agent/主会话>

| 跑 | K | timing.jobs | enumerate_s | manifest_s | probe_chain_s | total_s | rc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 |  |  |  |  |  |  |
| 2 | 2 |  |  |  |  |  |  |
| 3 | 3 |  |  |  |  |  |  |

- 噪声带：同 K 复跑一对（K=1）段值散布＝<...>
- 判读：probe_chain_s 跨 K 趋势＝<...>·恒同面核验＝PASS/FAIL
- 出账：/tmp/perf-<域>-k{1,2,3}-<yyyymmdd>.json（易失·引用入 docs/perf-profile-*.md
  报告照录即在库）
```

## 6. 现势边界（v41）

- `timing.jobs` 维度 v41 始入账（`tools/unclog.py --selftest` 矢量⑬冻结）；
  v40 旧账缺位＝K=1 语义可比。
- 真编译 K=1/2/3 三跑首采**未做**（真树活跑归主会话）——占位与实测进度见
  `docs/perf-profile-v1.0-20261111.md` §五。

---

(English) Companion to [README.md](README.md) (blockage-baseline intake):
this file governs the **speed axis** — probe profiling via `tools/unclog.py
--audit` timing segments — while that page governs the **battle axis** (red
accounts / walls); the two never cross-read. Protocol: fix the candidate face
(`--candidates` TSV, one TSV reused), run K=1/2/3 via `--probe-parallel K`
(passed through to `wash/probe_engine.py --jobs`), diff the `timing` segments
(`probe_chain_s` is the headline metric; the `jobs` field records K per run
for comparability — absent in v40-era reports, meaning serial K=1). Wall-clock
caveats: timing is the single non-deterministic part of a report (rerun the
same command and it changes; everything else stays byte-identical), so never
conclude from a single run; injector-canned runs bypass K (mechanism check
only, not a speed profile). Scale ≤30 candidates per face (~27-file precedent:
7.06 s/file serial); wrap everything in `cpu_guard.sh`, keep K≤2 unless
staggered, and remember real-tree audit runs belong to the main session.
Naming: `perf-<domain>-k<K>-<yyyymmdd>.json` — deliberately **not** in the
`audit-` baseline series.
