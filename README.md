# rocqwash — Coq/Rocq Constructive Proof Unblocking Engine

**rocqwash** is a mechanical diagnosis, washing, verification, and certification toolchain for Coq/Rocq constructive mathematics projects. It is designed to **naturally surpass LLM/probabilistic approaches** in proof-unblocking: every diagnostic is a type-theoretic structural property, every fix is idempotent and replayable, every verification is independently reproducible.

> **Core Principle**: 凡可用类型论结构性判据机检的，一律不交给概率模型猜。
> (What can be mechanically verified via type-theoretic structural criteria shall never be delegated to probabilistic models.)

## Architecture: Three Chains in One

```
Toolchain (scripts + templates + canonical recipes)
    ↓
Logic Chain (criteria + gates + calibration standards)
    ↓
Derivation Chain (input → wash → verify → land → certify → push)
```

## Components

| Module | Purpose | LLM Surpass |
|--------|---------|-------------|
| `scan/` | Prop leakage scanner (5 frozen lanes + 3 negative-capture lanes) | Exact to line; LLM cannot guarantee exhaustive |
| `names/` | Statement-name ordinal list extractor + N=N assertion | LLM cannot guarantee ordinal counting |
| `wash/` | Canonical 7-step wash engine (exact-string + count==1 + idempotent) | LLM-generated tactics not idempotently replayable |
| `verify/` | R4 three-source (bare magic=0 + probe dual-face + five-pattern grep) | LLM cannot enumerate full closure |
| `seam/` | Generation-gap seam probe (W13 four-mechanism auto-classification) | Mechanical supply-signature Check vs LLM guess |
| `certify/` | Two-tier freeze system + push-window four-criteria + UNION v2 | LLM cannot replace deterministic process |
| `watch/` | CI monitoring + pin-IP push + thermal guard | Deterministic workflow vs LLM instability |
| `tools/` | cpu_guard.sh thermal wrapper + shared utilities | Hardware-aware process control |
| `wrapper/` | Adapter layers for frozen / out-of-repo pieces: `coqc_shim.sh` + `gate7_probe.sh` (gate7 probe chain → local `rocq c`, guard-wrapped launcher) + `guard.sh` + `scan_station.py` | Canonical argv/env adaptation; criteria stay solely with the original tools |
| `scan/scan_v4_token.py` | Token-level qualified-identifier census (bare vs dotted constructor references, binder-aware) — closes the mixed-line masking blind spot of line-level filters | Token census is exhaustive at token granularity; line-level `grep -v` drops lines that carry both forms |
| `wash/cure_pack.json` + `wash/cure_applier.py` | Consumer-cure canonical pack: nineteen deterministic idempotent rewrite patterns — the legacy five (bridge-wrapped rewrite, goal-opening downshift, opaque-reflexivity cure, qualified successor form, NatLe supply bridge), nine v1.1 statement-face patterns from the 20261103 wash-campaign field report (Qle/Qlt carrier-face downshifts in token and %-scoped notation forms, refl bridge opener, Import-shadow direct-face qualification as two exclusive variants with fail-loud conflict detection, NatLe premise lift + intros-tail-guarded drop wrap), and five v1.2 S07-lineage adaptation patterns from the W66 field report (parameterized-shell drop with a :=-binding-right guard, notation rebind line-insertion, @field projection-bridge bare form, predicate-face convergence token map whose targets must be the consuming supply lemma's conclusion constant names, and a report-only binder-shell station for the manual binder surgery), applied by a face/proof-scoped regex engine with per-face token guards plus a line-insert and a station-report engine | Exact trigger + template + second-run-zero-change assertion; LLM-generated rewrites are not idempotently replayable |
| `scan/dual_scan.py` | Dual-scanner cross-check driver: runs scan_v4_token + mac_stmt_scan over the same candidate files and reports per-file station counts plus a diff (only_v4 / only_stmt / common) — turns shared scanner blindness (application/type-face red causes) into a mechanical fact per file instead of a silent assumption | Both scanners' exit codes and station line-sets are mechanical; scanner consensus is reported, never blessed as completeness |
| `verify/erasure_classifier.py` | Extraction-erasure station classifier: six clusters with disposition suggestions, CAPTURE cross-check, markdown adjudication ledger | Deterministic pattern rules over extraction artifacts; advisory output for human adjudication, never a verdict |
| `wash/probe_engine.py` | Batch closure-compatibility probe engine: candidates TSV × world dir → per-file `rocq c` under cpu_guard → rc triage (WASHABLE / BORN-CLEAN / red-cause classes incl. MISSING_LIB) → idempotent ledger JSON | Real exit codes + red-cause regex classification are mechanical; LLM guesses at closure compatibility |
| `tools/chain_graph.py` | Multi-ledger merger → missing-lib chain-root graph (dependents count + root self-washability) → TOP ranking markdown + JSON | Union/override merge and dependents counting are deterministic; LLM loses track across ledgers |
| `wash/comment_pack.json` + `wash/comment_sweep.py` | Comment-domain sweep sidecar (does not impersonate a statement-face pattern): nested-comment-and-string-aware state machine, comment-domain flag-word exchange (review-bias word → neutral English term), data-driven leading-header replacement with a five-field shape spec; every application mechanically asserts the code-line-equality projection (comment-strip per the w7 criterion) and second-run zero-change | Comment-domain-only edits are provable by the code-strip projection; LLM edits leak into code silently |
| `tools/ledger_sync.py` | Probe-ledger × status-ledger TSV sync: E1 dedup / E3 ghost / MD5-drift / NO-MD5 / generation-divergence findings (v2.1: recognizes the freeze-ledger `items` subkey shell and filters bare-dict metadata keys loudly; divergence-carrying records are surfaced per-entry with an idempotent row note, never silently dropped) / loud column validation → new TSV, idempotent | Fail-loud bookkeeping with deterministic row upgrades; LLM silently drops or duplicates rows |

## Repository Layout / 目录结构

```
rocqwash/
├── cli/rocqwash          # 统一 CLI 入口 — unified CLI entry (scan/names/wash/verify/seam/certify/watch)
├── docs/
│   ├── zh/architecture.md  # 架构文档（中文）— architecture doc (Chinese)
│   └── en/architecture.md  # 架构文档（英文镜像）— architecture doc (English mirror)
├── CONTRIBUTING.md       # 贡献指南（流程/代码规范/测试要求/cpu_guard 使用说明）
├── examples/             # 全链演示样例 + Makefile — single-file full-chain demo (scan→names→N=N→wash→verify)
├── scan/  names/         # 已实现通用逐件工具（mac_stmt_scan.py / scan_v4_token.py / dual_scan.py）— implemented generic tools
├── tools/                # cpu_guard.sh 温控包裹 + 战役工装 — thermal guard + campaign tools
├── wrapper/              # 适配层族（gate7 探针链 shim/启动器＋cpu_guard 直通＋scan 指认包装）— adapter layers (gate7 shim/probe, guard pass-through, scan station)
├── wash/                 # wash_engine.py 通用逐件洗引擎 + probe_engine.py 批量闭包探针 + 治愈包/战役批洗 — generic wash engine + batch probe engine + cure pack + campaign tools
├── verify/               # verify_vo.py 绿判四件套 + 战役验证工装 — four-pack green verdict + campaign verify tools
├── seam/                 # seam_probe.py W13 四机制指纹探针 — W13 four-mechanism fingerprint probe
├── certify/              # freeze_manifest.py 两层冻结 + push_gate.py 推窗四判据/UNION v2 + frozen8.py 八件冻结名单 — two-tier freeze + push-window gate + UNION v2 + frozen-eight registry
├── watch/                # watch.py CI 监控/钉 IP 推送/ls-remote 确证 — CI monitoring / pin-IP push / ls-remote confirm
├── tests/  workflows/    # 自测套件（42 例）/ CI 工作流占位 — test suite (42 cases) / CI placeholder
└── README.md  LICENSE  .gitignore
```

> 状态快照 2026-11-01（巡检打磨席 rqsup4）：`scan/`、`names/`、`tools/cpu_guard.sh`、
> `cli/`、`examples/`、`docs/`、`tests/`（34 例自测套件）已实现并实测；`wash/`
> （`wash_engine.py` 台账洗引擎＋`_abl1_wash.py` 战役件＋`world_hook.py` 世界基校验钩子·
> 五课①）、`verify/`（`verify_vo.py` 绿判四件套＋战役工装＋`verify_gate6.py` gate6 薄包装·
> 五课③）、`seam/`（`seam_probe.py` W13 四机制指纹探针）、`certify/`（`freeze_manifest.py`
> 两层冻结清单＋`push_gate.py` 推窗四判据/UNION v2 深件·席 rqwash2＋`frozen8.py`
> 八件冻结名单机检）、`watch/`
> （`watch.py` CI 监控/钉 IP 推送/ls-remote 确证·零 dispatch 结构保证）、`tools/`
> （`select_audit.py` 选件审计器·五课②）、`recipes/`（`S07_projection_reanchor_E5.md`
> 五课④＋`ENBIG7_same_domain_collision_PW1.md` 五课③·判例处方件双件）、`wrapper/`
> （适配层族：gate7 探针链 `coqc_shim.sh`＋`gate7_probe.sh`·cpu_guard 直通
> `guard.sh`·scan 指认包装 `scan_station.py`·席 rqadapt·三判例验收站
> `precedent_station.py`·五课⑤ rqsup4）已落地；
> `verify/` 统一入口已收口（显式子动词分派 `cli/rocqwash verify gate4|verify_vo|verify_gate6|retrofit`·
> rqadapt 落三子动词 2026-10-31·rqsup4 四巡补 verify_gate6 20261101）；`certify/`
> 同款显式分派 `cli/rocqwash certify freeze|push_gate|frozen8`（rqsup4 五巡补
> frozen8 20261101）——冻结件零改动；R4 提取侧三源为待办。
> v30 增补（20261103·探测战役工具化轮）：`wash/probe_engine.py` 批量闭包相容
> 探针引擎＋`tools/chain_graph.py` 多账合并链根图＋`tools/ledger_sync.py`
> probe×状态台账同步器（E1 去重/E3 幽灵/列校验 fail-loud）——承 W13/W25/台账
> v2 三原型 1:1 泛化，全路径参数化零硬编码；自测套件扩至 40 例全绿。
> v31 增补（20261103·洗形战役实战判例工具化轮）：`wash/cure_pack.json` v1.1
> 五式→十四式（Qle/Qlt 载体面降移两形·refl 桥开门·Import 遮蔽直通面双变体
> exclusive-group fail-loud·NatLe 前提提升＋intros-tail 守卫 drop 包裹）＋
> `wash/cure_applier.py` face-regex 域引擎（face/proof 域触发·逐面 token 守卫·
> 文件级前置条件）＋`wash/comment_pack.json`＋`comment_sweep.py` 注释域 sweep
> 旁车（嵌套注释+字符串感知状态机·旗词换形·数据驱动头注换代·w7 code 行全等
> 投影幂等断言）＋`tools/ledger_sync.py` v2.1（items 子键壳识别＋裸 dict 元数据
> 键响亮滤除＋GEN-DIVERGENCE 双代分歧出账——分歧优先序成文：kept 代＝下游账
> basis 榜系消费代，dropped 代只注记不弃账）；自测套件扩至 41 例全绿。
> v32 增补（20261103·S07 世系适配式工具化轮·W66 支撑席提案实装）：
> `wash/cure_pack.json` v1.1→v1.2 十四式→十九式（cure32_A 参数化壳去除·
> :=-binding-right 守卫／cure32_B 记号重绑 line-insert 引擎／cure32_C 投影桥
> 裸名形 face+proof 域／谓词面收敛 token_map——换名目标须取消费供给引理结论面
> 同一常量名·delta 等价异名编译绿而提取插 Obj.magic／binder 壳 report-only
> 站型——手刀辖区报站·术后站数归零）＋`scan/dual_scan.py` 双器对拍驱动
> （scan_v4＋mac_stmt_scan 双扫×逐件差异报告 only_v4/only_stmt）＋cure_applier
> 器修（exclusive-group 冲突＋--json 路径 report 落盘·rc=4 文档值）；
> 自测套件扩至 42 例全绿（门控 S07 编译弧：红→机械 cure→binder 手术→绿→
> 提取 Obj.magic 0/0）。
> 组件级细节见 [docs/zh/architecture.md](docs/zh/architecture.md) /
> [docs/en/architecture.md](docs/en/architecture.md)；贡献流程见
> [CONTRIBUTING.md](CONTRIBUTING.md)。

## Getting Started (5 minutes)

Prerequisites (three lines):

- `python3` ≥ 3.9 — no third-party packages required
- a Rocq/Coq 9.x toolchain on `PATH` — needed only for the compile-verification pieces; everything else runs without it
- Windows: use Git Bash as your shell (the toolchain is bash + python3)

```bash
git clone https://github.com/hy7pc8gfmf-dotcom/rocqwash.git
cd rocqwash
bash tests/run_tests.sh          # self-test suite; exit 0 = all green
```

First run — scan a demo source for statement-face Prop leakage:

```bash
python3 scan/mac_stmt_scan.py --file examples/demo_prop_leak.v
# RED stations: ['demo_eq_self', 'demo_eq_sym', 'demo_le_eq', 'demo_le_self', 'demo_mixed']
```

First verification — comment-hygiene gate on a clean sample:

```bash
python3 verify/gate4_comment_guard.py --file tests/fixtures/gate4_clean_sample.v
# [gate4ext] ... 件数=1  PASS=1  FAIL=0  REVIEW(人工复核)=0  UNREADABLE=0 ...
```

Token-level successor-qualification census (finds bare constructor references
that line-level filters miss):

```bash
python3 scan/scan_v4_token.py --file path/to/file.v --json census.json
```

## Platform Support

| Platform | Support | Notes |
|---|---|---|
| macOS | full | `tools/cpu_guard.sh` thermal gate uses `pmset` (macOS-only); queue/nice lanes are POSIX |
| Windows | Git Bash + python3 | light-load direct runs; bring your own thermal policy if needed (`cpu_guard.sh` thermal reading degrades gracefully without `pmset`) |
| Linux | same path as Windows | unverified by this project's CI — reported as-is, no claims |

## Quick Start

```bash
# Scan a .v file for Prop leakage — via the unified CLI entry
cli/rocqwash scan --file my_proof.v

# Extract statement names and assert N=N against baseline
cli/rocqwash names my_proof.v --names-out names.txt
cli/rocqwash names my_proof.v --compare my_proof_washed.v --expect 487

# Wash with an explicit exact-string ledger (idempotent, fail-loud, no guessing)
cli/rocqwash wash my_proof.v --patch wash_ledger.json --out my_proof_washed.v

# Green-verdict four-pack on a compiled pair (magic / freshness / exit / log)
cli/rocqwash verify verify_vo --v my_proof.v --vo my_proof.vo --rc 0 --log build.log

# W13 four-mechanism seam fingerprints (candidate list + prescriptions)
cli/rocqwash seam --file my_proof.v

# Two-tier freeze manifest (tier1 per-file md5 + tier2 manifest md5)
cli/rocqwash certify freeze freeze . --out manifest.json
cli/rocqwash certify freeze check . --manifest manifest.json

# Push-window four-criteria gate (judges the window, never pushes)
cli/rocqwash certify push_gate window --repo . --runs-json runs.json --suite tests/run_tests.sh

# UNION v2 multi-world manifest (per-world tier1/tier2 + union tier)
cli/rocqwash certify push_gate union-freeze --world wa=./world_a --world wb=./world_b --out union.json
cli/rocqwash certify push_gate union-check --manifest union.json

# CI in-flight monitoring (offline evidence mode; online read-only query also available)
python3 watch/watch.py ci --runs-json runs.json

# Pin-IP push wrapper (dry-run by default; masked output; --yes actually pushes)
python3 watch/watch.py push --repo . --remote origin --pin-ip 140.82.113.3 --url-host github.com

# Post-push ls-remote double-read confirmation
python3 watch/watch.py confirm --repo . --remote origin --branch main --sha <sha>

# Equivalent direct invocation
python3 scan/mac_stmt_scan.py --file my_proof.v
python3 names/mac_stmt_names.py my_proof.v --names-out names.txt

# Full-chain demo (scan → names → N=N → wash → verify)
make -C examples demo

# Compile with thermal guard
bash tools/cpu_guard.sh -Reg /tmp/my_reg -Front 0 -Mid 1 -- rocq c -native-compiler no -Q . "" my_proof.v
```

## Seven Canonical Steps (不可跳)

1. **cp source into sandbox** (write-isolation)
2. **Three-state triage** (true-wash / bridge-retain=exception-registry / UNCERTAIN=probe-first)
3. **Canonical face-mapping wash** (Qlt→QltT / Qle→QleT' / ==→QeqT / bare=→Id+id_cong / nat≤→NatLe)
4. **Compile verification** (RC=0 / magic 436f712100015ff4 / vo newer than v / PA Closed / coqchk Axioms:none)
5. **R4 three-source conjunction** (bare full-extraction magic=0 + probe dual-face magic=0 + five-pattern grep=0)
6. **gate7 English化 retrofit** (CJK→0 + five-field header 30-line cap)
7. **N=N name-table assertion** (mac_stmt_names.py ordinal full-equality) + freeze md5

Each step must pass before the next. Any failure = honest WIP, no green-washing.

## Four W13 Seam Mechanisms (Generation-Gap Auto-Classification)

1. **== statement rewrite/ring/reflexivity structurally unusable on QeqT(Id) goals** → flip back via qeq_imp_qeqT first
2. **Keyed-matching instantiation**: supply-side parameter must take the actual shape in the goal
3. **Premiss-carrying lemma consumption**: assert-化 + dual-shore bridge
4. **Cross-line Require topology leak**: statement-level multi-line awareness + driver idempotent resume

## LLM Integration

rocqwash is designed to **complement** LLM agents, not compete with them:

- **LLM excels at**: understanding "what does this math mean" (semantic layer)
- **rocqwash excels at**: ensuring "this proof is real" (mechanical layer)

**Collaboration pattern**: LLM understands → rocqwash diagnoses → LLM fixes → rocqwash verifies → LLM commits → rocqwash certifies.

## Why rocqwash Surpasses LLM/Probabilistic Approaches

| Capability | LLM | rocqwash |
|-----------|-----|----------|
| Prop leakage localization | LLM needs to read entire file and may miss lines | `mac_stmt_scan.py` pins to exact line in milliseconds |
| Missing dependency detection | LLM guesses Require chains | Require line-by-line scan + Set tree diff = mechanical exhaustive, zero omissions |
| Seam type classification | LLM reads error messages and guesses direction | W13 four-mechanism grep fingerprint → prescription mapping = mechanical, not experiential |
| Wash mapping | LLM generates tactics that may hallucinate | Canonical 7-form exact-string replacement + count==1 assertion = idempotent replayable |
| Compile verification | LLM trusts self-report | `world.run("rocq",...)` exit code = deterministic |
| R4 three-source | LLM may miss spots | bare full-closure extraction + probe dual-face + five-pattern grep = triple-source conjunction |
| N=N name-table | LLM may miscount | `mac_stmt_names.py` ordinal full-equality assertion = mechanical |
| UNION world integrity | LLM may skip dependency copies | Per-piece md5 manifest = mechanical leak-proof |

**Core barrier**: These capabilities are not "better prompts" — they are structural properties of Coq/Rocq type theory. QeqT-goal Qeq-rewrite impossibility is a corollary of Set/Prop type-theoretic mutual exclusion. No prompt engineering can override type theory.

## License

Apache 2.0
