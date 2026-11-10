# cw.sh — v29-v32 工具波统一入口速查 / Unified entry quick reference

`cw.sh` 是 rocqwash v29-v32 七工具＋20261111 五工具（共十二个）的**一键调用入口**（repo 根）：

```
bash cw.sh <tool> [args...]
```

- **零配置**：路径全部相对仓根（ROOT 取自脚本所在目录），仓随迁随用；
- **透传**：参数与退出码 1:1 直转（`exec`），不改写、不模拟；
- **bash 3.2 兼容**：macOS 自带 `/bin/bash` 可直接跑；只读路由层，自身零写盘；
- **与 `cli/rocqwash` 互补**：后者路由 v29 前七模块（scan/names/wash/verify/
  seam/certify/watch）；v29-v32 工具所在目录已含多个通用入口，模块级自动路由
  的歧义保护（exit 4）不覆盖它们——本入口按工具名显式补位。20261111 五工具
  （doctor/net-probe/triage/union/pushci）同落 `tools/` 多入口目录，同此显式名
  补位路由。

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
| `doctor` | `tools/toolchain_dyld_doctor.py` | dyld 工具链断链诊断（批量 EXIT=134 面·只诊断＋restore 建议·**禁代执行**） | `bash cw.sh doctor --worker PATH --donor DIR --json dyld.json` |
| `net-probe` | `tools/net_probe.py` | 网络窗探针（双探稳窗·单探禁发射·HTTPError 即可达） | `bash cw.sh net-probe --rounds 2 --interval 60 --stable-window` |
| `triage` | `tools/ci_triage.py` | CI 红炉分诊（五族+绿炉判类谱·红是数据非器红） | `bash cw.sh triage --repo ORG/REPO --run ID --logs` |
| `union` | `tools/registry_union.py` | 注册册 union 手术（main 为底＋对 merge-base 真独有尾插·**缺省干跑**） | `bash cw.sh union --base b --main m --branch x --kind order --json r.json` |
| `pushci` | `tools/pushci.py` | 修复后推送 CI 一键流水线（五段管线 preflight 发射闸→push→watch→heal→verdict±merge·v35 四器 subprocess 编排零新引擎·verdict 七态 `success\|fix-content\|toolchain\|unstable\|heal-exhausted\|gate4-block\|dry-run` 对应退出码 0/1/2/9） | `bash cw.sh pushci --repo-path . --branch feature/x --json report.json` |
| `help` | — | 总帮助；`help <tool>` 看该工具一行提示 | `bash cw.sh help probe` |

典型流水线（发现→治愈→复核）：

```
bash cw.sh scan4 --file demo.v --json census.json      # 1 普查
bash cw.sh cure   --file demo.v                        # 2 干跑看方案
bash cw.sh cure   --file demo.v --apply               # 3 落刀（写盘）
bash cw.sh scan4  --file demo.v --json after.json      # 4 复扫应为零
```

CI 红炉修复链（doctor→net-probe→pushci(含 watch+heal)→triage）：

```
bash cw.sh doctor --json dyld.json                              # 1 dyld 断链诊断（批量 EXIT=134 面·restore 建议只打印禁代执行）
bash cw.sh net-probe --rounds 2 --interval 60 --stable-window   # 2 双探稳窗（连续两轮全端点可达才准发射·单探禁发射）
bash cw.sh pushci --repo-path . --branch feature/x --json report.json   # 3 一键流水线（preflight 内复跑 doctor＋net-probe 双闸→push→watch CI→heal 自愈 rerun→verdict±--merge·verdict 七态见上表）
bash cw.sh triage --repo ORG/REPO --run ID --logs               # 4 verdict≠success 时红炉分诊（红是数据非器红·按族给 action）
```

> 手动老链仍在册可单独用：`python3 certify/push_gate.py window ...` 推窗四判据
> ＋裸 `git push`。pushci 的 preflight 发射闸只复跑 doctor＋net-probe 两闸（可选
> `--pre-scan-gate4` 头注预扫）——套件绿/behind=0 等推窗四判据不在此册，过闸
> 纪律仍归 `certify/push_gate.py`。

### 退出码

| 码 | 含义 |
|----|------|
| 0 | 通过 |
| 2 | 未知工具（`cw.sh bogus`）；或工具自身 argparse 用法错/断言失败（透传） |
| 9 | 目标脚本缺失（`cw.sh xxx: missing <path>`）；或工具自身目标文件缺失（透传） |
| 其余 | 各工具自身口径 1:1 透传（如 sync-ledger `1`=同步完成带发现·net-probe `1`=不稳窗·doctor `1`=missing-libs·pushci verdict 封册 success/dry-run=0·heal-exhausted/unstable/toolchain=1·fix-content/gate4-block=2·9=目标缺失） |

## English brief

`cw.sh` is the one-command entry for the seven tools introduced in the
rocqwash v29-v32 waves plus the five tools added on 20261111 (twelve in
total). It lives at the repository root:

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
(dual-scanner cross-check), and the 20261111 additions `doctor`→
`tools/toolchain_dyld_doctor.py` (dyld toolchain-breakage diagnostics; prints
restore advice, never executes it), `net-probe`→`tools/net_probe.py`
(network-window probe, double-probe stable window), `triage`→`tools/ci_triage.py`
(CI red-run triage), `union`→`tools/registry_union.py` (registry union surgery,
dry-run by default), `pushci`→`tools/pushci.py` (push-CI one-shot pipeline:
preflight emission gate → push → CI watch → heal rerun → verdict ± merge;
seven-state verdict `success|fix-content|toolchain|unstable|heal-exhausted|
gate4-block|dry-run`), plus `help`.

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
