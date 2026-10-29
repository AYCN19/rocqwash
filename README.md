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

## Repository Layout / 目录结构

```
rocqwash/
├── cli/rocqwash          # 统一 CLI 入口 — unified CLI entry (scan/names/wash/verify/seam/certify/watch)
├── docs/
│   ├── zh/architecture.md  # 架构文档（中文）— architecture doc (Chinese)
│   └── en/architecture.md  # 架构文档（英文镜像）— architecture doc (English mirror)
├── CONTRIBUTING.md       # 贡献指南（流程/代码规范/测试要求/cpu_guard 使用说明）
├── examples/             # 全链演示样例 + Makefile — single-file full-chain demo (scan→names→wash→verify)
├── scan/  names/         # 已实现通用逐件工具 — implemented generic tools (mac_stmt_scan.py / mac_stmt_names.py)
├── tools/                # cpu_guard.sh 温控包裹 + 战役工装 — thermal guard + campaign tools
├── wash/  verify/        # 模块目录 — module slots（战役工装已落库；通用逐件入口 pending）
├── seam/  certify/  watch/   # 模块占位 — module placeholders (pending)
├── tests/  workflows/    # 占位 — placeholders (pending)
└── README.md  LICENSE  .gitignore
```

> 状态快照 2026-10-29：`scan/`、`names/`、`tools/cpu_guard.sh`、`cli/`、`examples/`、
> `docs/` 已实现并实测；`wash/`、`verify/` 已落库战役级工装（`_` 前缀·通用逐件入口
> pending）；`seam/`、`certify/`、`watch/`、`tests/`、`workflows/` 为空占位。
> 组件级细节见 [docs/zh/architecture.md](docs/zh/architecture.md) /
> [docs/en/architecture.md](docs/en/architecture.md)；贡献流程见
> [CONTRIBUTING.md](CONTRIBUTING.md)。

## Quick Start

```bash
# Scan a .v file for Prop leakage — via the unified CLI entry
cli/rocqwash scan --file my_proof.v

# Extract statement names and assert N=N against baseline
cli/rocqwash names my_proof.v --names-out names.txt
cli/rocqwash names my_proof.v --compare my_proof_washed.v --expect 487

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
