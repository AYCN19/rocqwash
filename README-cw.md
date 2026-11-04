# cw.sh — v29-v32 工具波统一入口速查 / Unified entry quick reference

`cw.sh` 是 rocqwash v29-v32 七个工具的**一键调用入口**（repo 根）：

```
bash cw.sh <tool> [args...]
```

- **零配置**：路径全部相对仓根（ROOT 取自脚本所在目录），仓随迁随用；
- **透传**：参数与退出码 1:1 直转（`exec`），不改写、不模拟；
- **bash 3.2 兼容**：macOS 自带 `/bin/bash` 可直接跑；只读路由层，自身零写盘；
- **与 `cli/rocqwash` 互补**：后者路由 v29 前七模块（scan/names/wash/verify/
  seam/certify/watch）；v29-v32 工具所在目录已含多个通用入口，模块级自动路由
  的歧义保护（exit 4）不覆盖它们——本入口按工具名显式补位。

## 中文速查表

| 工具 | 目标脚本 | 用途 | 一行示例 |
|------|----------|------|----------|
| `scan4` | `scan/scan_v4_token.py` | token 级限定名普查（限定名/遮蔽源/追踪 id） | `bash cw.sh scan4 --file demo.v --json report.json --text` |
| `cure` | `wash/cure_applier.py` | 消费位治愈正典包（**缺省干跑**，`--apply` 才写盘） | `bash cw.sh cure --file demo.v --apply` |
| `probe` | `wash/probe_engine.py` | 批量闭包相容探针（候选清单×世界目录→rc 分流台账） | `bash cw.sh probe --candidates list.tsv --src src/ --world world/ --out ledger.json` |
| `chain` | `tools/chain_graph.py` | 多份 probe 台账合并→链根图＋TOP 榜 | `bash cw.sh chain l1.json l2.json --md top.md --top 25` |
| `sync-ledger` | `tools/ledger_sync.py` | probe 台账×状态台账 TSV 合并同步 | `bash cw.sh sync-ledger --probe ledger.json --ledger status.tsv --out new.tsv --report sync.json` |
| `erasure` | `verify/erasure_classifier.py` | 提取擦除位分类顾问（.mli 逐位归类） | `bash cw.sh erasure --mli out.mli --md-out ledger.md` |
| `dual-scan` | `scan/dual_scan.py` | 双器对拍（scan_v4_token×mac_stmt_scan 逐件差异） | `bash cw.sh dual-scan --dir src/ --out report.json` |
| `help` | — | 总帮助；`help <tool>` 看该工具一行提示 | `bash cw.sh help probe` |

典型流水线（发现→治愈→复核）：

```
bash cw.sh scan4 --file demo.v --json census.json      # 1 普查
bash cw.sh cure   --file demo.v                        # 2 干跑看方案
bash cw.sh cure   --file demo.v --apply               # 3 落刀（写盘）
bash cw.sh scan4  --file demo.v --json after.json      # 4 复扫应为零
```

### 退出码

| 码 | 含义 |
|----|------|
| 0 | 通过 |
| 2 | 未知工具（`cw.sh bogus`）；或工具自身 argparse 用法错/断言失败（透传） |
| 9 | 目标脚本缺失（`cw.sh xxx: missing <path>`）；或工具自身目标文件缺失（透传） |
| 其余 | 各工具自身口径 1:1 透传（如 sync-ledger `1`=同步完成带发现） |

## English brief

`cw.sh` is the one-command entry for the seven tools introduced in the
rocqwash v29-v32 waves. It lives at the repository root:

```
bash cw.sh <tool> [args...]
```

Tool names map 1:1 to the underlying scripts: `scan4`→`scan/scan_v4_token.py`
(token-level qualified-identifier census), `cure`→`wash/cure_applier.py`
(consumer-cure pack, dry-run by default), `probe`→`wash/probe_engine.py`
(batch closure-compatibility probing), `chain`→`tools/chain_graph.py`
(multi-ledger chain-root graph), `sync-ledger`→`tools/ledger_sync.py`
(probe×status-ledger merge), `erasure`→`verify/erasure_classifier.py`
(extraction erasure advisor), `dual-scan`→`scan/dual_scan.py`
(dual-scanner cross-check), plus `help`.

Design contract: all paths are resolved relative to the repository root from
the script's own location (no hardcoded paths; the repo can be cloned anywhere);
arguments and exit codes pass through 1:1 via `exec` (fail-loud, never
rewritten); requires only `bash` 3.2 and `python3` ≥ 3.9, no third-party
dependencies; the entry itself is a read-only dispatcher and writes nothing.
`bash cw.sh help <tool>` prints a one-line usage hint per tool. It complements
the existing `cli/rocqwash` router, which covers the pre-v29 modules — the
v29-v32 tools live in directories with several generic entries each, where the
module auto-router's ambiguity guard declines to guess, so this entry routes
them by explicit tool name. Self-test: `bash tests/test_cw_entry.sh` (also part
of `bash tests/run_tests.sh`).
