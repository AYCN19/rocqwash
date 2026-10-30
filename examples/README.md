# examples — 单文件全链演示样例 / Single-file full-chain demo

（中文）本目录演示 rocqwash 全链：**scan → names → (N=N 断言) → wash → verify**。
样例为单文件 `demo_prop_leak.v`（原件·结论位含 Prop 裸形）＋洗后对照件
`washed/demo_prop_leak_washed.v`（按 README「七步规范」第 3 步规范面映射改写：
结论位裸 `=`→`Id`＋`id_refl`、结论位 nat 裸 `<=`→`NatLe`＋`natle_ok`；前提位 Prop
 lawful keep 保留）。运行：

```bash
make demo    # 全链；或分步 make scan names nn wash verify clean
```

**实测结果（2026-10-31·撰写机实跑）**：

| 步骤 | 结果 |
|---|---|
| scan 原件 | 5 个 RED 站（全部 5 条语句·结论位）；by_cat `P4_bareeq:4, P5_le:4`；前提位 3 处 EXEMPT（lawful keep）；md5 `ddeb97fe…` |
| names 原件 | `total: 5`，`--expect 5` OK，anomalies 0，duplicates ∅ |
| N=N 断言 | `断言 5=5 有序全等 : PASS`（原件 vs 洗后件·`mac_stmt_names.py --compare`） |
| scan 洗后件 | `RED stations: []`（结论位全迁 Set 载体）；仅 1 处前提位 EXEMPT；md5 `5bf31d2f…` |
| wash | **RUN**——`washed/demo_ledger.json`（16 patch exact-string 台账）驱动 `wash_engine.py`：16 patch 全 APPLY、幂等重放 `applied=0 skipped=16`、引擎输出与参照件 `washed/demo_prop_leak_washed.v` **逐字节恒同**（`cmp` 断言·漂移即 FAIL） |
| verify 编译段 | SKIP——撰写机无 rocq/coqc；有 rocq 的机器上 `make demo` 会自动经 `tools/cpu_guard.sh` 编译洗后件 |
| verify R4 段 | SKIP——`verify/` 三件未带 `_` 前缀件（两历史战役工装＋`verify_vo.py`）通用入口不唯一（cli exit 4 口径·统一收口待办）；可直跑 `python3 verify/verify_vo.py --v … --vo …` |

**诚实注记（honest notes）**：
- SKIP ＝ NOT-RUN，非通过、非绿——本 demo 绝不把未执行步骤标成通过。
- 两个 .v 的**可编译性未经验证**（撰写机无 rocq/coqc，编译从未运行）；证明体仅用
  Coq prelude（`le_n`/`reflexivity`/`eq_sym`/构造子），一旦接入 rocq 由 `make verify`
  首跑即验。
- 扫描器的 RED 是「真命中候选」——定谳唯内核 census（报清单不报清白·E364）。

---

(English) This directory demonstrates the full rocqwash chain: **scan → names → (N=N
assertion) → wash → verify** on a single file, `demo_prop_leak.v` (original, with
conclusion-position Prop bare forms) plus the wash-target specimen
`washed/demo_prop_leak_washed.v` (canonical mapping per README "Seven Canonical
Steps" step 3: conclusion bare `=`→`Id` via `id_refl`, conclusion nat `<=`→`NatLe`
via `natle_ok`; premise-position Prop kept as lawful). Run `make demo`.

Measured on the authoring machine (2026-10-31): scan finds 5 RED stations
(`P4_bareeq:4, P5_le:4` by category, 3 EXEMPT premise hits); names asserts N=5 with
0 anomalies; the N=N ordered-equality assertion between original and washed specimen
PASSES; the washed file scans with `RED stations: []`. The wash step now **runs for
real**: `washed/demo_ledger.json` (16 exact-string patches) drives
`wash_engine.py` — all 16 patches APPLY, the idempotent replay reports
`applied=0 skipped=16`, and the engine output is **byte-identical** to the reference
`washed/demo_prop_leak_washed.v` (cmp-asserted; drift fails the demo). The compile
segment of verify SKIPs (no rocq/coqc here — on a rocq-equipped machine `make demo`
compiles the specimen under `tools/cpu_guard.sh` automatically); the R4 segment
SKIPs (three non-underscore files in `verify/` — two historical campaign tools plus
`verify_vo.py` — leave the generic entry ambiguous, cli exit 4; unification is
TODO; call `python3 verify/verify_vo.py --v … --vo …` directly). SKIP = NOT-RUN,
never a pass. Compile-ability of both .v files is **unverified** (no rocq on the
authoring machine); proofs use prelude-only tactics.
