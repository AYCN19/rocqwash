# examples/baselines/ — 堵账基线入仓规程 / Baseline intake protocol

（中文）本目录收 rocqwash **真树堵账基线**（`tools/unclog.py --audit` 产）及其
对比规程。基线是**数据**不是器红：红账/墙账在册即战况实录，degraded 是回退
信号不是工具故障。产账纪律、命名律、对比判读全在本页。

## 1. 基线是什么

`tools/unclog.py --audit`＝只读审计（单遍 probe 归集→chain_graph→堵账基线报告）：

- schema `rocqwash-unclog/1` **audit 形**：`final.verdict="audit"`＋
  `mode.audit=true`·rounds 单轮（probe_summary/chain_top 全在）·
  cures_planned/cures_applied 恒 0＝零落刀零复核·exit 0（红是基线数据非器红）。
- 零写盘硬保证：`--src` 全文件 md5 清单跑前跑后自证恒同（违即 fail-loud 9·
  染污基线不出账）。
- 墙账 graph 判例全记：unprobed／self-unwashable／frozen-in-service 逐根；
  零链根红账补 no-chain-root 目（禁哑墙）。

## 2. 命名律（入仓唯一名形）

```
audit-<域>-<yyyymmdd>.json
```

- `<域>`＝`--src` 源树基名（如 `wash`）→ `audit-wash-20261101.json`；
- `<yyyymmdd>`＝产账日；同域多基线按文件名排序即时间轴；
- 对比只在**同域**内进行（跨域/跨候选面即 incomparable·见 §5）；
- 文件名不带状态词（禁 `audit-wash-fixed.json` 形）——战况在账内
  `final.red_files`/`wall`，不在文件名上。

## 3. 产账（真树干跑·归主会话）

```bash
python3 tools/unclog.py --src <源树根> [--world <世界目录>] --audit \
  --json examples/baselines/audit-<域>-<yyyymmdd>.json
```

- 真树 audit 活跑归**主会话**（工装席只证器面 fixture 级——unclog docstring
  同律）；本目录只收账与规程，不收产账脚本。
- 离线演练用 `--injector DIR`（canned probe 罐装·零真编译零真网络），
  产物仅作器面验证**不入仓**。

## 4. timing 段注记（唯一非确定段）

`report["timing"]`（enumerate/manifest/probe+chain/total 耗时各段）＝**实测
墙钟·逐跑必异**＝基线文件唯一非确定段。对比器 `tools/baseline_diff.py` 恒
不入对比（报告 `excluded_fields=["timing"]` 在册）——「同输入重跑字节恒同」
对 timing 段之外全成立。人工判读亦不得凭耗时断言战况。

## 5. 对比（堵账增减报告）

```bash
python3 tools/baseline_diff.py \
  examples/baselines/audit-<域>-<旧日>.json \
  examples/baselines/audit-<域>-<新日>.json \
  --md /tmp/diff-<域>-<旧日>-<新日>.md     # diff 报告随手出·不入本目录
```

- schema `rocqwash-baseline-diff/1`：`new_blocks`／`resolved_blocks`／
  `persistent`（按链根键·墙账逐因对齐——old/new 的 reason·detail 逐项＋
  变化旗；红文件条目附 chain_top 链根归因，查无如实 null）／`score_delta`
  ／`verdict`。
- verdict 四态：`improved`（红减）｜`degraded`（红增）｜`stable`（同）｜
  `incomparable`（候选集不同即如实拒判——delta 恒空·score_delta=null）。
  候选面四元组＝`mode.source`＋`args.src`＋`args.candidates`＋
  `args.chain_ledgers`（basename 面）；非 audit 形报告混入同判 incomparable。
- verdict 只认红账 n_red 增减；墙账增减入三清单不驱动 verdict。
- 退出码：0=improved/stable·1=degraded/incomparable（a failing result is data, not a tool failure·响亮
  stdout）·2=输入形坏·9=路径缺失。

## 6. 纪律（红线路）

- **禁手编基线**：对比器账面自洽校验（n_red=|red_files|·wall_count=|wall|·
  probe_summary↔final 红账一致）违即 rc=2 拒判——染污对比不出账。
- **同域同候选面对比**：候选面四元组两账不同 → incomparable 如实
  （跨候选集的增减是伪信号·禁硬凑）。改了候选清单就换 `<域>` 名或明记
  断代，不混轴对比。
- **基线是数据**：degraded/incomparable exit 1 是判读面要接的响亮信号，
  不是器故障——读 --md 定夺处置。
- **timing 不入账判**：见 §4。

---

(English) This directory holds **real-tree unclog baselines** (produced by
`tools/unclog.py --audit`, schema `rocqwash-unclog/1` audit form:
`final.verdict="audit"`, `mode.audit=true`, single round, zero cures, exit 0 —
red is data, not tool failure) plus the intake protocol. Naming:
`audit-<domain>-<yyyymmdd>.json` where `<domain>` is the `--src` tree basename
and `<yyyymmdd>` the production date; compare only within one domain. Real-tree
audit runs belong to the main session; this directory stores baselines and this
protocol only. The `timing` block (wall-clock seconds per phase) is the single
non-deterministic part of a baseline file and is **excluded from comparison**
(`excluded_fields=["timing"]` in `tools/baseline_diff.py`). Comparison:
`python3 tools/baseline_diff.py OLD.json NEW.json [--json out.json] [--md
out.md]` → schema `rocqwash-baseline-diff/1` with `new_blocks` /
`resolved_blocks` / `persistent` (keyed by chain root, wall reasons aligned
factor-by-factor) / `score_delta` / `verdict` ∈ improved|degraded|stable|
incomparable (candidate-set mismatch → incomparable, honest, empty deltas).
Exit codes: 0=improved/stable, 1=degraded/incomparable (data, loud stdout),
2=form error, 9=missing path. Hand-edited baselines are rejected by the
account-consistency checks (rc=2).
