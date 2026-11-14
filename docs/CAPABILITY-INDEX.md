# rocqwash CAPABILITY-INDEX（工具能力契约面 · Tool Capability Contract Surface）

版本锚 Version anchor：`5829f6d18a9ee2bc63c19ef46caad115e34a0c85`（钉住克隆 `D:/ComplexAnalysis/rocqwash` main，2026-11-14 本地 `git rev-parse HEAD` 实测；对账回执 N2 实测与远端 main 一致）。
Version anchor: pinned clone `D:/ComplexAnalysis/rocqwash` main at `5829f6d18a9ee2bc63c19ef46caad115e34a0c85`, measured locally on 2026-11-14 (`git rev-parse HEAD`); the reconciliation receipt (channel N2) matched this head to the remote main.

## 0. 定位与读法 · Positioning and How to Read

**定位（中文）**：本文件是 rocqwash 工具能力的唯一契约面。每件工具一个条目，逐行照录同批词面普查产出；调用者（工作流工单、自动化任务、未来 MCP 层）按行直调，不再手搓路径与参数。每条目七字段：路径、一句话用途、调用形（argparse 词面还原）、可复制示例、依赖、网络面、SKIP 面。

**Positioning (English)**: this file is the single contract surface for rocqwash tool capability. One entry per tool, transcribed line-by-line from the same-batch word-face census; callers (workflow tickets, automation tasks, a future MCP layer) invoke straight from the entry line instead of hand-writing paths and arguments. Each entry carries seven fields: path, one-line purpose, invocation form (restored from the argparse word face), a copyable example, imports, network face, and the SKIP face.

**调用者义务 Caller duty**：按行直调时记录所用 HEAD sha 作版本锚；HEAD 推进后以同步义务为准重核条目面。
When invoking from an entry, record the HEAD sha used as the version anchor; after HEAD advances, re-check the entry face following the sync duty.

**证据与边界 Evidence and boundary**：
- 逐件行照录自同批普查产出 `census.md` 与机读 `census-tools.json`（`tools/` 下 27 件 `.py`，AST 词面级；普查时点 2026-11-14；`python -I` 零网络运行；普查未执行、未导入、未派生任何工具本体）。
- Per-item lines are transcribed verbatim from the same-batch census outputs `census.md` and machine-readable `census-tools.json` (27 `.py` files under `tools/`, AST word-face level; census time 2026-11-14; run under `python -I` with zero network; the census executed, imported, and spawned no tool).
- 示例行从 argparse/usage 词面还原（AST 级旗标形态表 `flag-shape.json`，判读规则：`action=store_true/store_false/count` 为布尔形，其余为取值形），禁虚构：位置参数以 `<name>` 占位；取值旗标写 `--flag <value>`；布尔旗标可直接照抄。示例仅示调用形，非必选项声明；全旗标面以调用形行为准。
- Example lines are restored from the argparse/usage word faces (AST-level flag-shape table `flag-shape.json`; classification rule: `action=store_true/store_false/count` is boolean, everything else is value-taking) with no invention: positional arguments appear as `<name>` placeholders, value-taking flags as `--flag <value>`, boolean flags copyable as written. An example shows the call form, not a statement of which options are required; the invocation line carries the full flag face.
- 调用前缀沿用各件 usage/docstring 面的记载形（`python` 或 `python3`）；实际以调用环境解释器为准。
- Invocation prefixes follow each tool's documented form (`python` or `python3`); use the interpreter available in the calling environment.
- 退出码语义属运行时证据，铸面时点未测（census 边界 §1）；本文件第 4 节轻探账对实测的 8 件记录 rc 与输出面，其余件候后续核验步骤。
- Exit-code semantics are runtime evidence not measured at cast time (census boundary §1); the light-probe ledger in §4 records rc and output face for the 8 measured items; the remaining items await the later verification step.
- `cpu_guard.sh`（4,053 B）系目录内唯一非 `.py` 件，在本次普查范围之外，仅记为元数据；其契约面未入本表。
- `cpu_guard.sh` (4,053 B) is the only non-`.py` file in the directory, outside the census scope, recorded as metadata; its contract face is not in this index.

## 1. 总表 · Summary Table

| File | Bytes | Lines | Doc | Arg | Pos/Opt | Network face (word) | Env markers | Basis |
|---|---|---|---|---|---|---|---|---|
| _abl1_4b_compile.py | 3,451 | 80 | Y | N | 0/0 | zero | ocaml(15) | usage |
| _gen_fin_mac.py | 9,001 | 166 | Y | Y | 0/6 | zero | ocaml(7), coq(12), thermal(3), runner(1) | arg |
| _http_backoff.py | 5,082 | 110 | Y | N | 0/0 | zero | none | usage |
| baseline_diff.py | 41,200 | 800 | Y | Y | 2/2 | zero | none | arg |
| chain_graph.py | 14,854 | 335 | Y | Y | 1/3 | zero | none | arg |
| ci_triage.py | 121,218 | 2,194 | Y | Y | 0/11 | urllib.request | coq(109), win(4), runner(2) | arg |
| contrib_intake.py | 62,133 | 1,365 | Y | Y | 0/11 | git: clone | coq(23) | arg |
| cw_doctor.py | 58,988 | 1,176 | Y | Y | 0/15 | zero | env, coq(5), dyld(31), thermal(5) | arg |
| cw_sentinel.py | 119,753 | 2,168 | Y | Y | 0/23 | http.client, socket, urllib.request | coq(1), thermal(3) | arg |
| doc_lint.py | 61,486 | 1,291 | Y | Y | 0/3 | zero | none | arg |
| evolve.py | 90,890 | 1,819 | Y | Y | 0/19 | zero | coq(7) | arg |
| ledger_sync.py | 26,938 | 549 | Y | Y | 0/5 | zero | none | arg |
| net_probe.py | 19,076 | 412 | Y | Y | 0/7 | socket, urllib.request | none (network is its subject) | arg |
| netname_normalize.py | 15,059 | 332 | Y | Y | 0/4 | zero | none | arg |
| norm_lint.py | 32,256 | 823 | Y | Y | 0/8 | zero | none | arg |
| pushci.py | 108,070 | 2,134 | Y | Y | 0/21 | urllib.request, git: push+ls-remote | env, coq(11) | arg |
| red_dispatch.py | 48,353 | 935 | Y | Y | 0/10 | zero | coq(5), thermal(1) | arg |
| registry_audit.py | 51,476 | 1,054 | Y | Y | 0/11 | zero | coq(12) | arg |
| registry_fix.py | 60,064 | 1,161 | Y | Y | 0/8 | zero | env, coq(5) | arg |
| registry_regen.py | 61,590 | 1,346 | Y | Y | 0/15 | zero | coq(37) | arg |
| registry_union.py | 42,872 | 931 | Y | Y | 0/14 | zero | coq(4) | arg |
| render_events.py | 26,635 | 547 | Y | Y | 0/5 | zero | none | arg |
| select_audit.py | 32,930 | 654 | Y | Y | 0/6 | zero | ocaml/opam token(2) | arg |
| toolchain_dyld_doctor.py | 23,777 | 492 | Y | Y | 0/6 | zero | env, coq(32), dyld(39), thermal(5) | arg |
| unclog.py | 103,325 | 1,943 | Y | Y | 0/30 | zero | coq(5), thermal(2) | arg |
| vacgen.py | 122,111 | 2,625 | Y | Y | 0/20 | zero | lean(64), thermal(3) | arg |
| wash_shape.py | 110,172 | 2,285 | Y | Y | 0/16 | zero | env, coq(6) | arg |

表例（Legend）：Doc = 文件头 docstring 在场；Arg = argparse import 在场；Pos/Opt = 位置参数/可选旗标数；Network face = 词面三通道判读（zero = 三通道皆零命中）；Env markers = 标记族（词面命中次数）：ocaml = ocamlc/ocamldep/opam，coq = coqc/coqtop/coqchk/coqdep/rocq 系，thermal = cpu_guard/_THERMAL 系，runner = self-hosted/actions-runner，win = Windows 守卫词面，env = ROCWASH_* 环境变量，dyld = macOS dyld 工具面，lean = lake/mathlib/Lean/elan 系；Basis = 调用形还原依据（arg = argparse 还原，usage = usage 字符串）。Env markers 是词面命中，非运行时需求实证（边界见 §3.1）。

Legend: Doc = module docstring present; Arg = argparse import present; Pos/Opt = positional/optional flag counts; Network face = three-channel word-face reading (zero = no hit in any channel); Env markers = marker families with word-face hit counts (ocaml = ocamlc/ocamldep/opam; coq = coqc/coqtop/coqchk/coqdep/rocq family; thermal = cpu_guard/_THERMAL family; runner = self-hosted/actions-runner; win = Windows guard wording; env = ROCWASH_* environment variables; dyld = macOS dyld tooling face; lean = lake/mathlib/Lean/elan family). Env markers are word-face hits, not proof of runtime requirements (boundary in §3.1). Basis = invocation reconstruction source (arg = argparse; usage = usage string).

## 2. 逐件契约 · Per-Item Contract Lines

依文件名字典序 27 件；每条目逐行照录 census，新增仅「示例 Example」一行。
27 items in filename order; each entry transcribes the census verbatim; the only added line is 示例 Example.

### tools/_abl1_4b_compile.py
- 用途 Purpose：内部辅助件：对提取目录中的 OCaml 模块做 mli 先行、依赖不动点轮的增量编译，可选链接并运行 driver；`ocamlc`/`ocamldep` 不在 PATH 即 fail-loud 退出（`_abl1_4b_compile.py:12-20`）。Internal helper: incremental OCaml compilation of an extracted module directory in dependency fixpoint order (interface files first), optionally linking and running a driver; exits loudly if `ocamlc`/`ocamldep` are absent from PATH (`_abl1_4b_compile.py:12-20`).
- 调用形 Invocation：`python3 _abl1_4b_compile.py <extract_dir> [driver.ml]`（usage 字符串还原，本件无 argparse）
- 示例 Example：`python3 _abl1_4b_compile.py <extract_dir>`
- 依赖 Imports：os, re, shutil, subprocess, sys（全标准库）
- 网络 Network face：zero（三通道零命中）
- SKIP 面：需 OCaml 工具链（ocaml/ocamldep 词面 15 处）；调用方需自备 opam 环境

### tools/_gen_fin_mac.py
- 用途 Purpose：内部辅助件：把探针模板适配生成为目标环境形（源模块、模块名、世界名、输出目录、requires 表均参数化）。Internal helper: renders a probe template into a target-environment form (source module, module name, world name, output directory, and requires list all parameterized).
- 调用形 Invocation：`python tools/_gen_fin_mac.py [--source] [--module] [--world] [--world-name] [--outdir] [--requires]`
- 示例 Example：`python tools/_gen_fin_mac.py --source <value>`
- 依赖 Imports：argparse, io, json, os, sys ＋ 仓内 `names/mac_stmt_names.py`（sys.path 注入跨目录引用）
- 网络 Network face：zero
- SKIP 面：ocaml/opam 词面（7）、coq 系词面（12）、cpu_guard 词面（3）、actions-runner 词面（1）；生成对象面向特定编译环境

### tools/_http_backoff.py
- 用途 Purpose：内部共享件：HTTP 限流退避纯函数，冻结向量自检，零网络零 IO；被 ci_triage、cw_sentinel、pushci 三件 import（词面）。Internal shared helper: pure-function HTTP rate-limit backoff with a frozen-vector selftest, no transport and no IO; imported by ci_triage, cw_sentinel, and pushci (word face).
- 调用形 Invocation：`python3 tools/_http_backoff.py --selftest`（usage 字符串还原，本件无 argparse）
- 示例 Example：`python3 tools/_http_backoff.py --selftest`
- 依赖 Imports：sys（单件）
- 网络 Network face：zero
- SKIP 面：无特殊环境词面标记

### tools/baseline_diff.py
- 用途 Purpose：对比两份基线文件，产出增减报告（JSON/markdown 双出形）。Compares two baseline files and reports additions and removals (JSON and markdown output).
- 调用形 Invocation：`python tools/baseline_diff.py <old> <new> [--json] [--md]`
- 示例 Example：`python tools/baseline_diff.py <old> <new> --json <value>`
- 依赖 Imports：argparse, io, json, os, shutil, subprocess, sys, tempfile
- 网络 Network face：zero
- SKIP 面：无特殊环境词面标记

### tools/chain_graph.py
- 用途 Purpose：把多份探针台账合并为链根图与排序清单。Merges multiple probe ledgers into a chain-root graph and a ranked list.
- 调用形 Invocation：`python tools/chain_graph.py <ledgers> [--json] [--md] [--top]`
- 示例 Example：`python tools/chain_graph.py <ledgers> --json <value>`
- 依赖 Imports：argparse, io, json, os, re, shutil, subprocess, sys, tempfile
- 网络 Network face：zero
- SKIP 面：无特殊环境词面标记

### tools/ci_triage.py
- 用途 Purpose：拉取并分诊失败 CI 炉的日志，输出分诊结论（`--offline` 可改走本地日志面）。Fetches and triages logs of failing CI runs; `--offline` switches to local log input.
- 调用形 Invocation：`python tools/ci_triage.py [--offline] [--repo] [--run] [--logs] [--no-dump-filter] [--netrc] [--baseline-seconds] [--baseline-step] [--timeout] [--retry-max] [--json]`
- 示例 Example：`python tools/ci_triage.py --offline <value> --logs`
- 依赖 Imports：argparse, datetime, io, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request ＋ 仓内 `tools/_http_backoff.py`
- 网络 Network face：非零（urllib.request；另 subprocess 桥 token 命中）
- SKIP 面：coq 系词面（109，含日志词汇面）、Windows 守卫词面（4）、self-hosted runner 词面（2）；运行需网络窗，`--offline` 除外

### tools/contrib_intake.py
- 用途 Purpose：外部贡献 intake 检查器：四道只读闸核验后出结论（贡献仓/基线仓/ref/路径/jargon 映射均参数化）。Contribution intake inspector: a read-only four-gate check that issues a verdict (contribution repo, base repo, refs, paths, and jargon map all parameterized).
- 调用形 Invocation：`python tools/contrib_intake.py [--contrib-repo] [--contrib-ref] [--base-repo] [--base-ref] [--paths] [--order-path] [--project-path] [--lane-prefix] [--jargon-map] [--rocq-cmd] [--json]`
- 示例 Example：`python tools/contrib_intake.py --contrib-repo <value>`
- 依赖 Imports：argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile ＋ 仓内 `tools/registry_union.py`
- 网络 Network face：非零（git 子进程 token 面：`clone`；无传输类 import）
- SKIP 面：coq 系词面（23）；运行涉及 git clone（网络）

### tools/cw_doctor.py
- 用途 Purpose：健康汇总检查器：多域 rollup 出报告（registry、source、world、worker、dyld、endpoints、guard 等域词面在旗标表）。Aggregate health checker rolling up several domains (registry, source, world, worker, dyld, endpoints, guard domains all present in the flag face).
- 调用形 Invocation：`python tools/cw_doctor.py [--json] [--workdir] [--registry] [--src] [--sample] [--world] [--worker] [--donor] [--endpoints] [--guard] [--guard-reg] [--guard-maxwait] [--timeout] [--rocq-cmd] [--injector]`
- 示例 Example：`python tools/cw_doctor.py --json <value>`
- 依赖 Imports：argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile
- 网络 Network face：zero（`--endpoints` 旗标为参数面，域探测可能委托外部）
- SKIP 面：`ROCWASH_ROCQWORKER` 环境变量、coq 系词面（5）、dyld 工具面（31）、cpu_guard 词面（5）

### tools/cw_sentinel.py
- 用途 Purpose：常驻实时 watcher：盯仓、台账与构建日志，事件流 JSONL 出证，支持 on-red 动作挂接与多轮 loop。Resident real-time watcher over a repo, ledgers, and the build log, emitting a JSONL event stream, with on-red hooks and a loop mode.
- 调用形 Invocation：`python tools/cw_sentinel.py [--once] [--loop] [--interval] [--max-rounds] [--watch-repo] [--branch] [--watch-ledgers] [--watch-buildlog] [--state-file] [--emit] [--emit-max-bytes] [--rebuild-state] [--on-red] [--on-red-preset] [--on-red-arg] [--netrc] [--timeout] [--retry-max] [--net-retries] [--subproc-timeout] [--injector] [--sleep-scale] [--json]`
- 示例 Example：`python tools/cw_sentinel.py --interval <value> --once`
- 依赖 Imports：argparse, datetime, http.client, io, json, os, re, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.request ＋ 仓内 `tools/_http_backoff.py`
- 网络 Network face：非零（http.client, socket, urllib.request；subprocess 桥 token 命中）
- SKIP 面：coq 系词面（1）、cpu_guard 词面（3）；运行需网络窗

### tools/doc_lint.py
- 用途 Purpose：docs 与实现一致性检查器：路由表、cw.sh 面、`--help` 面三查对账。Docs-versus-implementation consistency checker: routing tables, the face of cw.sh, and the `--help` face.
- 调用形 Invocation：`python tools/doc_lint.py [--repo] [--json] [--help-cap]`
- 示例 Example：`python tools/doc_lint.py --repo <value>`
- 依赖 Imports：argparse, io, json, os, re, shutil, subprocess, sys, tempfile
- 网络 Network face：zero
- SKIP 面：无特殊环境词面标记

### tools/evolve.py
- 用途 Purpose：自演化引擎 v1：从 watcher 事件与台账面生成演化草案并登记（sentinel/suite/registry 系旗标面在卷）。Self-evolution engine v1: drafts evolution proposals from watcher events and ledger faces (sentinel, suite, and registry flag families present).
- 调用形 Invocation：`python tools/evolve.py [--draft-out] [--json] [--repo-root] [--top] [--baseline] [--jargon-map] [--watch-repo] [--sentinel-state] [--sentinel-state-seed] [--sentinel-branch] [--sentinel-events] [--sentinel-injector] [--suite-ledger] [--suite-now] [--registry-git] [--registry-ref] [--git-path-order] [--git-path-project] [--registry-baseline]`
- 示例 Example：`python tools/evolve.py --draft-out <value> --suite-now`
- 依赖 Imports：argparse, io, json, os, re, shutil, subprocess, sys, tempfile ＋ 仓内 `certify/frozen8.py`（sys.path 注入跨目录引用）
- 网络 Network face：zero（git 子命令 token 面仅本地操作：status/commit/add）
- SKIP 面：coq 系词面（7）

### tools/ledger_sync.py
- 用途 Purpose：探针台账与状态台账的 TSV 合并同步器（策略参数化）。TSV merge synchronizer between the probe ledger and the status ledger (policy parameterized).
- 调用形 Invocation：`python tools/ledger_sync.py [--probe] [--ledger] [--out] [--report] [--policy]`
- 示例 Example：`python tools/ledger_sync.py --probe <value>`
- 依赖 Imports：argparse, io, json, os, re, shutil, subprocess, sys, tempfile
- 网络 Network face：zero
- SKIP 面：无特殊环境词面标记

### tools/net_probe.py
- 用途 Purpose：网络窗探针：裸 GET 全端点可达性 N 轮探测，双探稳窗判定（连续两轮全端点可达才判稳）。Network-window probe: bare-GET reachability over all endpoints for N rounds; a window counts as stable only after two consecutive all-endpoint passes.
- 调用形 Invocation：`python tools/net_probe.py [--endpoints] [--rounds] [--interval] [--stable-window] [--jitter] [--seed] [--json]`（旗标取值细节：`--endpoints` 为逗号分隔端点表、`--rounds`/`--interval` 为数值，见 JSON `argparse.add_argument` 逐旗标 kwargs 面）
- 示例 Example：`python tools/net_probe.py --endpoints <value> --stable-window`
- 依赖 Imports：argparse, datetime, io, json, os, random, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.request
- 网络 Network face：非零（socket, urllib.request；网络即其探测对象）
- SKIP 面：无工具链标记；运行需网络窗（其本职）
- 备注 Note：docstring usage 行（net_probe.py:20）记载 `--selftest`，分发在 argparse 之前由 `sys.argv` 手工完成（net_probe.py:317-319，`selftest()` 定义于 ：173）；argparse 面旗标表（7 项）不含该旗标。此文档面与 argparse 面的分歧已如实登记，待轻探步骤核验。The docstring usage line (`net_probe.py:20`) documents `--selftest`, dispatched manually via `sys.argv` before argparse (`net_probe.py:317-319`; `selftest()` defined at line 173); the argparse flag face (7 flags) does not list it. Recorded as a doc-versus-argparse divergence for the light-probe step to verify.

### tools/netname_normalize.py
- 用途 Purpose：`.v.v` 双后缀净名归一器（映射表可出可施，`--apply` 落改）。Normalizes doubled `.v.v` suffixes (map can be emitted or applied with `--apply`).
- 调用形 Invocation：`python tools/netname_normalize.py [--dir] [--apply] [--map] [--json]`
- 示例 Example：`python tools/netname_normalize.py --dir <value> --apply`
- 依赖 Imports：argparse, hashlib, io, json, os, shutil, subprocess, sys, tempfile
- 网络 Network face：zero
- SKIP 面：无特殊环境词面标记

### tools/norm_lint.py
- 用途 Purpose：注释面规范化 lint，报告态先行（jargon 映射、CJK 阈值与白名单参数化；内置 `--selftest`）。Annotation-face normalization lint, report-first form (jargon map, CJK threshold, and whitelist parameterized; built-in `--selftest`).
- 调用形 Invocation：`python tools/norm_lint.py [--tree] [--file] [--jargon-map] [--cjk-threshold] [--cjk-whitelist] [--json] [--md] [--selftest]`
- 示例 Example：`python tools/norm_lint.py --tree <value> --selftest`
- 依赖 Imports：argparse, fnmatch, io, json, os, re, shutil, sys, tempfile, tokenize
- 网络 Network face：zero
- SKIP 面：无特殊环境词面标记

### tools/pushci.py
- 用途 Purpose：推岸后 CI 一条龙编排器：push、ls-remote 确证、CI 盯守、判读与愈合轮（步骤/愈合上限/盯守节律均参数化）。One-shot push-then-CI orchestrator: push, ls-remote confirmation, CI watching, verdict reading, and heal rounds (steps, heal cap, and watch cadence parameterized).
- 调用形 Invocation：`python tools/pushci.py [--repo-path] [--branch] [--base-ref] [--remote] [--pre-scan-gate4] [--pr] [--merge] [--merge-method] [--max-heal] [--watch-interval] [--probe-interval] [--watch-max-rounds] [--timeout] [--retry-max] [--steps] [--injector] [--git-caller] [--sleep-scale] [--netrc] [--json] [--dry-run]`
- 示例 Example：`python tools/pushci.py --repo-path <value> --pre-scan-gate4`
- 依赖 Imports：argparse, io, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request ＋ 仓内 `tools/_http_backoff.py`
- 网络 Network face：非零（urllib.request；git 子进程 token 面：`push`, `ls-remote`；subprocess 桥 token 命中）
- SKIP 面：`ROCWASH_MASK` 环境变量、coq 系词面（11）；运行需网络窗与远端仓访问权

### tools/red_dispatch.py
- 用途 Purpose：红事件路由器：事件文件按预设分发动作（冷却、状态文件、dry-run 与 `--selftest` 内置）。Red-event dispatcher: routes an event file to preset actions (cooldown, state file, dry-run, and built-in `--selftest`).
- 调用形 Invocation：`python tools/red_dispatch.py [--event-file] [--preset] [--json] [--state-file] [--cooldown] [--repo-path] [--param] [--on-args] [--dry-run] [--selftest]`
- 示例 Example：`python tools/red_dispatch.py --event-file <value> --dry-run`
- 依赖 Imports：argparse, contextlib, io, json, os, re, shutil, subprocess, sys, tempfile, time
- 网络 Network face：zero
- SKIP 面：coq 系词面（5）、cpu_guard 词面（1）

### tools/registry_audit.py
- 用途 Purpose：注册册双册只读卫生审计，出确定性修复计划（fix-plan）。Read-only hygiene audit over the two registry files, emitting a deterministic fix plan.
- 调用形 Invocation：`python tools/registry_audit.py [--order] [--project] [--git] [--ref] [--git-path-order] [--git-path-project] [--live-src] [--anchor-src] [--fix-plan] [--json] [--md]`
- 示例 Example：`python tools/registry_audit.py --order <value> --fix-plan`
- 依赖 Imports：argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile ＋ 仓内 `tools/registry_union.py`
- 网络 Network face：zero
- SKIP 面：coq 系词面（12）

### tools/registry_fix.py
- 用途 Purpose：registry_audit 修复计划的执行器（`--apply` 落改；`ROCWASH_REGISTRY_FIX_INJECT_BLAST` 为注入测试位）。Applies the fix plan produced by registry_audit (`--apply`; `ROCWASH_REGISTRY_FIX_INJECT_BLAST` is a blast-injection test hook).
- 调用形 Invocation：`python tools/registry_fix.py [--audit-json] [--order] [--project] [--anchor-src] [--apply] [--work-dir] [--audit-tool] [--json]`
- 示例 Example：`python tools/registry_fix.py --audit-json <value> --apply`
- 依赖 Imports：argparse, hashlib, io, json, os, shutil, subprocess, sys, tempfile ＋ 仓内 `tools/registry_union.py`
- 网络 Network face：zero
- SKIP 面：`ROCWASH_REGISTRY_FIX_INJECT_BLAST` 环境变量、coq 系词面（5）

### tools/registry_regen.py
- 用途 Purpose：贡献面注册行到合并目标线的再生成器（基线/贡献两仓双 ref、分片表、路径表均参数化）。Regenerates contribution registration rows onto the merge-target line (base and contribution repos, refs, piece table, and path table parameterized).
- 调用形 Invocation：`python tools/registry_regen.py [--base-repo] [--base-ref] [--contrib-repo] [--contrib-ref] [--pieces] [--anchor-src] [--dep-source] [--seq] [--base-path-order] [--base-path-project] [--contrib-path-order] [--contrib-path-project] [--out] [--apply] [--json]`
- 示例 Example：`python tools/registry_regen.py --base-repo <value> --apply`
- 依赖 Imports：argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile ＋ 仓内 `tools/registry_union.py`
- 网络 Network face：zero
- SKIP 面：coq 系词面（37）

### tools/registry_union.py
- 用途 Purpose：注册册三方 union 合并器（base/main/branch 三输入、锚再定与 kind 选择参数化）。Three-way union merger for the registry (base/main/branch inputs; re-anchoring and kind selection parameterized).
- 调用形 Invocation：`python tools/registry_union.py [--base] [--main] [--branch] [--git] [--ref-base] [--ref-main] [--ref-branch] [--git-path] [--kind] [--reanchor] [--anchor-src] [--out] [--apply] [--json]`
- 示例 Example：`python tools/registry_union.py --base <value> --apply`
- 依赖 Imports：argparse, collections, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile
- 网络 Network face：zero
- SKIP 面：coq 系词面（4）

### tools/render_events.py
- 用途 Purpose：事件流 JSONL 到 markdown 台账的渲染器。Renders a JSONL event stream into a markdown ledger.
- 调用形 Invocation：`python tools/render_events.py [--events] [--dir] [--md] [--json] [--top]`
- 示例 Example：`python tools/render_events.py --events <value>`
- 依赖 Imports：argparse, io, json, os, re, shutil, subprocess, sys, tempfile
- 网络 Network face：zero
- SKIP 面：无特殊环境词面标记

### tools/select_audit.py
- 用途 Purpose：批选清单对树 order 文件的全表 grep 剔重审计。Audits a batch selection against the tree's order file by full-table grep.
- 调用形 Invocation：`python tools/select_audit.py [--order] [--select] [--grep] [--requires] [--world] [--json]`
- 示例 Example：`python tools/select_audit.py --order <value>`
- 依赖 Imports：argparse, io, json, os, re, shutil, subprocess, sys, tempfile
- 网络 Network face：zero
- SKIP 面：opam 词面（2，待轻探判语义）

### tools/toolchain_dyld_doctor.py
- 用途 Purpose：macOS dyld 工具链断链诊断器（worker/donor 定位、smoke 探测参数化）。Diagnoses broken macOS dyld toolchain links (worker/donor locating and a smoke probe, parameterized).
- 调用形 Invocation：`python tools/toolchain_dyld_doctor.py [--worker] [--donor] [--smoke] [--coqc] [--guard] [--json]`
- 示例 Example：`python tools/toolchain_dyld_doctor.py --worker <value> --smoke`
- 依赖 Imports：argparse, io, json, os, shutil, subprocess, sys, tempfile
- 网络 Network face：zero
- SKIP 面：`ROCWASH_ROCQWORKER` 环境变量、coq 系词面（32）、dyld 工具面（39）、cpu_guard 词面（5）；诊断对象为 macOS 特有工具面

### tools/unclog.py
- 用途 Purpose：编译堵点清理引擎：候选链探测与多轮清理（`--rounds`/`--apply`/`--audit`、guard 耦合与 loop 面参数化）。Blockage-clearing engine for compilation: candidate-chain probing and multi-round clearing (`--rounds`/`--apply`/`--audit`, guard coupling, and loop face parameterized).
- 调用形 Invocation：`python tools/unclog.py [--src] [--world] [--candidates] [--chain-ledgers] [--repo-path] [--rounds] [--apply] [--audit] [--top] [--scan-ids] [--pack] [--probe-resume] [--probe-parallel] [--rocq-cmd] [--guard] [--guard-reg] [--guard-front] [--guard-mid] [--guard-maxwait] [--timeout] [--workdir] [--json] [--events] [--once] [--loop] [--interval] [--loop-max] [--sleep-scale] [--injector] [--state-file]`
- 示例 Example：`python tools/unclog.py --src <value> --apply`
- 依赖 Imports：argparse, hashlib, io, json, os, shutil, subprocess, sys, tempfile, time
- 网络 Network face：zero
- SKIP 面：coq 系词面（5）、cpu_guard 词面（2）；清理对象面向 Coq/Rocq 编译环境

### tools/vacgen.py
- 用途 Purpose：Lean vacuity 探针骨架生成器：四层形状识别（前提分解、taxonomy 查表、置信评分、分层回归），含零编译覆盖 preflight 与难度地图（`--preflight-all`）；本普查时点在岸，为 tools/ 新增件（newly added item），文件头自述 v2。Lean vacuity probe skeleton generator with a four-layer shape-recognition engine (premise decomposition, taxonomy lookup, confidence scoring, tiered harness), including a zero-compile coverage preflight and a difficulty map (`--preflight-all`); present on disk at census time and newly added to tools/, self-described as v2 in its docstring.
- 调用形 Invocation：`python tools/vacgen.py [--in] [--out] [--toolchain] [--snapshot] [--audit-id] [--name] [--worktree] [--lake] [--guard] [--core] [--force] [--taxonomy] [--preflight-all] [--census] [--root] [--cluster-table] [--report] [--exp-draft] [--verify-anchors] [--mathlib]`
- 示例 Example：`python tools/vacgen.py --in <value> --force`
- 依赖 Imports：argparse, datetime, fractions, hashlib, json, os, re, sys（全标准库；文件头自述零第三方依赖）
- 网络 Network face：zero
- SKIP 面：lean/lake/mathlib/elan 词面（64）、cpu_guard 词面（3）；骨架铸形零编译可跑，编译验证腿需 Lean 工具链（设计 SKIP 面）
- 注记 Note：落岸与路由面见 §3.3。

### tools/wash_shape.py
- 用途 Purpose：注释与形状规范化五段流水线（header 映射与预设、多轮 loop、事件流参数化）。Shape-normalizing five-stage pipeline for annotation faces (header maps and presets, multi-round loop, and event stream parameterized).
- 调用形 Invocation：`python tools/wash_shape.py [--file] [--dir] [--exclude] [--only] [--header-map] [--header-map-preset] [--anchor-src] [--repo-root] [--json] [--apply] [--loop] [--interval] [--sleep-scale] [--max-rounds] [--events] [--injector]`
- 示例 Example：`python tools/wash_shape.py --file <value> --apply`
- 依赖 Imports：argparse, datetime, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile, time
- 网络 Network face：zero
- SKIP 面：`ROCWASH_HEADER_MAP` 环境变量、coq 系词面（6）

### 第 2 节汇总观察 · Aggregates for this section

照录 census §4 汇总（逐条为普查时点词面事实）：
Aggregates transcribed from census §4 (each line is a word-face fact at census time):

- argparse 面：25/27 件有 argparse import 与旗标面；2 件（`_abl1_4b_compile.py`、`_http_backoff.py`）无 argparse，调用形由 usage 字符串还原（前者 `sys.argv` 位置参数手工解析，后者文档面记载 `--selftest`）。
- 子命令面：27 件 `add_parser` 词面命中全零（逐件 AST 扫描），即全部为平铺旗标形，无子命令路由面。
- 网络面：22/27 词面三通道零命中；5 件非零（ci_triage、cw_sentinel、net_probe、pushci 为传输类 import；contrib_intake 为 git `clone` 子进程 token 面）。
- 特殊环境面：18/27 命中至少一个标记族；9 件无任何标记（baseline_diff、chain_graph、doc_lint、ledger_sync、netname_normalize、norm_lint、render_events、_http_backoff 加 net_probe 仅需网络窗）。
- docstring 面：27/27 全件有文件头 docstring；逐字面已录 JSON。
- 依赖面：27 件 import 全部为标准库或仓内模块，零第三方依赖；仓内跨目录引用两处（`evolve.py` 引 `certify/frozen8.py`、`_gen_fin_mac.py` 引 `names/mac_stmt_names.py`，均经 sys.path 注入），仓内同目录引用一处共享件（`tools/_http_backoff.py` 被三件网络工具 import）。
- `--selftest` token 面：24/27 件源码含 `--selftest` 词面；其中 norm_lint 与 red_dispatch 有 argparse 旗标位，net_probe 为手工 argv 分发（见 §2 备注），其余件的旗标位归属待轻探核验。
- 内部件约定：3 件下划线前缀（`_abl1_4b_compile.py`、`_gen_fin_mac.py`、`_http_backoff.py`）自述与命名一致为内部辅助/共享件。
- 文件规模跨度：3,451 B 至 122,111 B；行数 80 至 2,625。
- `vacgen.py` 为 tools/ 新增件（本普查时点在岸；早前外部账面为 23 件工具快照，本普查按现势 27 件逐件入表，件数基线与对账回执第六节的 28/25 记账相容：28 = 27 py + cpu_guard.sh）。

## 3. 尾 · Tail

### 3.1 负发现边界（四要素） · Negative-Finding Boundaries (four elements)

以下各条均为本次扫描面的负发现，非绝对主张（照录 census §5）。
Each item below is a negative finding of that scan, not an absolute claim (transcribed from census §5).

**5.1 「零第三方依赖」**
1. 扫了什么：27 件全部 import 语句的模块名与 stdlib 模块名集、tools/ 同目录文件名集、全仓 `.py` 文件名集三方比对（AST 词面，2026-11-14）。
2. 没扫什么：运行时动态 import（`importlib`、`__import__` 调用面未逐一深挖）、非 Python 面的依赖（cpu_guard.sh 所需 shell 环境）。
3. 非绝对主张：只主张本词面扫描零第三方模块名命中。
4. 别名未穷尽：以字符串动态拼接模块名的 import 形未穷尽排除。
复审条件：每次 tools/ 增件或本普查复跑时重扫。

**5.2 「22 件零网络面」**
1. 扫了什么：传输类 import 面（socket/ssl/urllib.request/http.client/requests 等清单）、subprocess 桥 token 面（curl/wget/api 主机名）、git 网络子命令 token 面（push/fetch/clone/pull/ls-remote 三通道，2026-11-14）。
2. 没扫什么：运行时实际连接行为；动态构造的主机名与 URL（f-string 拼接形未逐一还原语义）；被这些工具调用的外部程序（coqc/lake/git 本体）自身的网络行为。
3. 非绝对主张：只主张本三通道词面扫描零命中，不主张「这些工具运行时必然零网络」。
4. 别名未穷尽：经环境变量间接注入端点、经 shell 别名/包装脚本的网络调用未穷尽排除。
复审条件：轻探步骤实测 `--help` 与退出码时一并复核；工具版本推进后重扫。

**5.3 「零子命令面」**
1. 扫了什么：27 件 AST 全树 `add_parser` 调用面扫描（命中 0）。
2. 没扫什么：非 argparse 的手工子命令路由（`sys.argv[1]` 分支分发形）未逐件深挖。
3. 非绝对主张：只主张 argparse 子命令机制词面零命中。
4. 别名未穷尽：以旗标组合（如 `--steps`、`--mode` 类）承载的子命令语义未穷尽排除（pushci 旗标面含 `--steps`，语义待轻探）。
复审条件：轻探步骤抽验旗标语义时复核。

**5.4 「18 件特殊环境面」**
1. 扫了什么：9 个标记族（ocaml/opam、coq/rocq 系、lean/lake/mathlib、macOS dyld 工具、Windows 守卫、GPG、cpu_guard 温控、self-hosted runner、ROCWASH_* 环境变量）的词面计数与样本。
2. 没扫什么：运行时真实环境需求；动态拼接的环境变量名（`"ROCWASH_" + suffix` 形）未穷尽排除。
3. 非绝对主张：标记命中是词面事实，不构成「运行时必需」实证；样本中部分命中来自注释与 help 词汇面（如 ci_triage 的 coq 词面多为日志解析词汇）。
4. 别名未穷尽：其他环境依赖形式（容器、特定 shell、PATH 布局）未系统排查。
复审条件：轻探步骤与后续实际调用时逐件核实。

### 3.2 零网络声明 · Zero-Network Declaration

**铸造面（本文件自身）**：本文件铸造全程零网络。铸面动作限于：钉住克隆词面读取（census AST 面、旗标形态 AST 面、`git show --stat`/`grep` 只读命令）与 8 件本地轻探（`--help` ×7、`--selftest` ×1，本地进程，无网络）；铸面过程无任何网络调用。

**Cast face (this file itself)**: this file was cast with zero network. Casting actions were limited to: word-face reads of the pinned clone (the census AST face, the AST flag-shape face, read-only `git show --stat` and `grep` commands) and 8 local light probes (`--help` on 7 tools, `--selftest` on 1, local processes, no network); no network call occurred during casting.

**逐件面（对 27 件工具的网络判读）**：22 件「零网络面」系词面三通道扫描面的负发现，非运行时绝对主张，四要素见 §3.1 之 5.2；网络面非零五件（ci_triage、cw_sentinel、net_probe、pushci、contrib_intake）调用前须按各自 SKIP 面评估网络窗与远端访问权。网络面负发现的复审条件（§3.1 之 5.2）与本文件轻探账（§4）一并适用；工具版本推进后重扫。

**Per-item face (network reading of the 27 tools)**: the 22 zero-network readings are negative findings of the three-channel word-face scan, not absolute runtime claims; the four elements are in §3.1 item 5.2. For the five tools with a non-zero network face (ci_triage, cw_sentinel, net_probe, pushci, contrib_intake), callers must assess the network window and remote access rights against each SKIP face before invoking. The re-check conditions of §3.1 item 5.2 and the light-probe ledger (§4) apply together; re-scan after tool versions advance.

### 3.3 vacgen 段（落岸注记） · vacgen Section (landing note)

- **落岸事实（第一手实测）**：`tools/vacgen.py` 系 2026-11-13 经 graft commit `5829f6d` 入岸（本文件版本锚即该 commit）。`git show --stat` 实测四文件：`tools/vacgen.py` 2,625 行、`docs/vacgen_sop.md` 384 行、`tests/t_vacgen_shape.py` 51 行、`更新账.md` +1 行。落岸单注记：RQW02。
- **Landing facts (first-hand measured)**: `tools/vacgen.py` landed on 2026-11-13 via graft commit `5829f6d` (the version anchor of this file). `git show --stat` measured four files: `tools/vacgen.py` 2,625 lines, `docs/vacgen_sop.md` 384 lines, `tests/t_vacgen_shape.py` 51 lines, `更新账.md` +1 line. Landing-package note: RQW02.
- **双面形态**：零编译面（骨架铸形无 Lean 环境可跑）＋编译验证腿（需 Lean 工具链，设计 SKIP 面）；三通道词面（lean/lake/mathlib/elan 64 处）与 SKIP 面照录于第 2 节 vacgen 条目。详规程 = `docs/vacgen_sop.md`；形状回归自检 = `tests/t_vacgen_shape.py`。
- **Two faces**: a zero-compile face (skeleton casting runs without a Lean environment) plus a compile-verification leg (needs a Lean toolchain, a design SKIP face); the three-channel word faces (lean/lake/mathlib/elan, 64 hits) and the SKIP face are transcribed in the §2 vacgen entry. Detailed procedure = `docs/vacgen_sop.md`; shape regression selftest = `tests/t_vacgen_shape.py`.
- **路由面（2026-11-14 复测·现势）**：cw.sh vacgen 分支已落（commit `8e04cc6` 四处齐备：头表/usage/hint_for/case；`grep -c vacgen cw.sh` = 6 实测）；CLI 调用形 `bash cw.sh vacgen ...` 与直调 `python tools/vacgen.py ...` 两形并行有效。
- **Route face (re-measured 2026-11-14, current)**: the cw.sh vacgen branch has landed (commit `8e04cc6`, all four places present: header table / usage / hint_for / case; `grep -c vacgen cw.sh` = 6 measured); both `bash cw.sh vacgen ...` and the direct `python tools/vacgen.py ...` invocation forms are valid.
- **CI 锚**：本 head 之炉 #43421710372 conclusion=success（对账回执 N3 实测，2026-11-13；同 head 前三炉连续 success）。
- **CI anchor**: the run at this head, #43421710372, concluded success (reconciliation receipt channel N3, measured 2026-11-13; the three prior runs at earlier heads were all success).

### 3.4 记账 · Provenance

- 扫描树：钉住克隆 `D:/ComplexAnalysis/rocqwash` @ `5829f6d18a9ee2bc63c19ef46caad115e34a0c85`（本地 `git rev-parse HEAD` 实测，2026-11-14；工作树 porcelain 0 行）。
- Scan tree: pinned clone `D:/ComplexAnalysis/rocqwash` at `5829f6d18a9ee2bc63c19ef46caad115e34a0c85` (measured locally via `git rev-parse HEAD`, 2026-11-14; working tree porcelain 0 lines).
- 逐件行母本：`census.md` ＋ `census-tools.json`（含 sha256 逐件锚；同目录 `census_tools_build.py`，stdlib-only，`python -I`）。
- Per-item source: `census.md` plus `census-tools.json` (with per-file sha256 anchors; builder `census_tools_build.py` in the same directory, stdlib-only, `python -I`).
- 示例旗标形态依据：`flag_shape_probe.py`（AST 级只读器，不执行不导入工具本体）产出 `flag-shape.json`；对五处反直觉旗标（`--offline`、`--stable-window`、`--suite-now`、`--fix-plan`、`--once`）另做源行 spot 复核，与 AST 判读一致。
- Example flag-shape basis: `flag_shape_probe.py` (AST-level read-only pass; no tool executed or imported) produced `flag-shape.json`; five counter-intuitive flags (`--offline`, `--stable-window`, `--suite-now`, `--fix-plan`, `--once`) were additionally spot-checked at source-line level, agreeing with the AST reading.
- 铸面时点：2026-11-14。
- Cast time: 2026-11-14.

## 4. 轻探账（≤8 件） · Light-Probe Ledger

实测时点 2026-11-14；命令形 `python -I tools/<name>.py --help`（钉住克隆仓库根执行）；rc 与输出面逐件记账。轻面件只探；网络面五件与特殊环境/重活件标 SKIP 不探，候后续核验步骤全谱。
Measured 2026-11-14; command form `python -I tools/<name>.py --help` (run from the pinned clone root); rc and output face recorded per item. Light tools only; the five network-face tools and special-environment/heavy tools are marked SKIP and not probed, awaiting the later verification pass.

| # | Tool | Command | rc | Output face (head) | Verdict |
|---|---|---|---|---|---|
| 1 | baseline_diff.py | `--help` | 0 | `usage: baseline_diff [-h] [--json out.json] [--md out.md] OLD.json NEW.json` | PASS，与调用形相符；两位置参数以 metavar `OLD.json`/`NEW.json` 渲染 |
| 2 | chain_graph.py | `--help` | 0 | `usage: chain_graph [-h] [--json out.json] [--md out.md] [--top N] [LEDGER.json ...]` | PASS，相符 |
| 3 | doc_lint.py | `--help` | 0 | `usage: doc_lint [-h] [--repo DIR] [--json out.json] [--help-cap N]` | PASS，相符 |
| 4 | ledger_sync.py | `--help` | 0 | `usage: ledger_sync [-h] [--probe FILE] [--ledger FILE] [--out FILE] [--report FILE] [--policy {unprobed-only,annotate-only}]` | PASS，相符；`--policy` 带 choices 面 |
| 5 | render_events.py | `--help` | 0 | `usage: render_events [-h] [--events FILE.jsonl] [--dir DIR] [--md out.md] [--json out.json] [--top N]` | PASS，相符 |
| 6 | norm_lint.py | `--help` | 0 | `usage: norm_lint [-h] [--tree DIR \| --file PATH] [--jargon-map JARGON_MAP] ...` | PASS，相符；`--tree`/`--file` 为互斥组 |
| 7 | netname_normalize.py | `--help` | 0 | `usage: netname_normalize [-h] [--dir DIR] [--apply] [--map out.tsv] [--json JSON]` | PASS，相符 |
| 8 | _http_backoff.py | `--selftest` | 0 | 自检 PASS 单行（退避序列/帽/重试面/Retry-After 分项全过） | PASS，usage 面记载形成立 |

探活补出细节（`--help` 实测面，census 词面未含）：`--json` 系全仓取值形（示例行按 `--json <value>` 展示）；`ledger_sync --policy` 的 choices 为 `{unprobed-only, annotate-only}`；`norm_lint` 的 `--tree`/`--file` 构成互斥组。三项均为 `--help` 输出面第一手事实，与 census 调用形无矛盾。

Probe-side details (measured `--help` face, absent from the census word face): `--json` is value-taking repo-wide (examples show `--json <value>`); `ledger_sync --policy` choices are `{unprobed-only, annotate-only}`; `norm_lint --tree`/`--file` form a mutually exclusive group. All three are first-hand facts of the `--help` output face, with no contradiction against the census invocation face.

SKIP（本席不探，候后续核验步骤）：网络面五件 ci_triage / cw_sentinel / net_probe / pushci / contrib_intake（运行需网络窗或远端访问）；特殊环境/重活件 _abl1_4b_compile（usage 面，裸调触发编译行为面）、_gen_fin_mac、cw_doctor、evolve、red_dispatch、registry_audit、registry_fix、registry_regen、registry_union、select_audit、toolchain_dyld_doctor、unclog、vacgen、wash_shape。`net_probe` 的 `--selftest` 分歧（§2 备注）亦候该步骤一并核验。

SKIP (not probed by this seat, awaiting the later verification pass): the five network-face tools ci_triage / cw_sentinel / net_probe / pushci / contrib_intake (their runs need a network window or remote access); special-environment/heavy tools _abl1_4b_compile (usage face; a bare call triggers the compile face), _gen_fin_mac, cw_doctor, evolve, red_dispatch, registry_audit, registry_fix, registry_regen, registry_union, select_audit, toolchain_dyld_doctor, unclog, vacgen, wash_shape. The `net_probe` `--selftest` divergence (§2 note) also awaits that step.

### 4.1 Follow-up probes · 补充探活（后续核验步骤产出）

Measured 2026-11-14 against HEAD `8e04cc6f9b6ee118e8e2729e9ae3edd6a163bf79`. The census anchor above stays the cast-time anchor; this block extends the light-probe ledger without re-casting the census, and the caller duty at §0 governs re-checks after HEAD advances. Uncommitted worktree lanes were held by a concurrent integration during measurement (recorded, not attributed).

- `evolve.py` help probe rc=0: the §2 entry line matches the live help face (all 19 flags present, no incompatible names).
- One full evolve round via the §2 example line: rc=0, stdout `evolve rocqwash-evolve/1: signals=3 candidates=5 drafted=5` (baseline + suite-now + maintained sentinel events/state inputs; draft and report written to the caller's work directory).
- The §2 registry pair aimed at this tool repo: rc=9 fail-loud REGISTERED (git show main:order.txt fatal: path does not exist): `git ls-tree main` carries no order.txt and no _CoqProject anywhere in the tree; the registry signal stays pointed at the serviced books only.
- Suite face, bash form: 51 pass / 12 failing / 4 skip / 67 total, rc=1; the 12 failing cases are lane-level and tool faces registered in the cycle accounts (Windows-lane environment faces for dyld/taskpolicy, the wash_shape report fd face, the unclog cure md5 text-mode face, the red_dispatch selftest vector face, the registry_audit reanchor-order face, and the probe/verify faces owned by their own lanes). The ask's literal interpreter form against a `.sh` file is a category error (Python parses the script); the bash form is the executable face.

## 5. 语域自查断言 · Register Self-Check Assertion

本文件正文经仪器 `ai_flavor_selfcheck.sh`（36 词面电池 + em-dash U+2014 电池；词表源 = 术语表 §4.6/§5）自查，靶 = 本文件全件。实测输出见收工时点附录行。
The authored text of this file was checked with the instrument `ai_flavor_selfcheck.sh` (36 wording faces plus the em-dash U+2014 battery; register source: glossary §4.6/§5), target = this whole file. Measured output is appended below at closing time.

凭据词面自查（值形正则与裸字面两口径，grep 于本文件）：0 命中，全件无任何凭据值或凭据词面。
Credential-face check (value-shape regex and bare-literal passes, grep over this file): 0 hits; no credential value or credential wording anywhere.

实测输出 Measured output（收工时点 closing time）：

```
CH_3FAMILIES_10FACES lines=0
EN_WORD_STEMS_15FACES lines=0
EN_SENTENCE_8FACES lines=0
EN_PARA_INITIAL_3FACES lines=0
EM_DASH_U2014 count=0 (target 0)
TOTAL_WORDING_LINES=0
VERDICT CLEAN (36 faces = 0; em-dash = 0)
```

执行形 Execution：`sh ai_flavor_selfcheck.sh CAPABILITY-INDEX.md`，exit 0。器械副本 Instrument copy：`D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/ai_flavor_selfcheck.sh`（2026-11-12 铸件，与 census 同仪）。

照录保真度机检 Transcription-fidelity checks（收工时点 closing time）：census §3 五字段逐行 135 = 135，diffs=0；负发现四要素行 16 = 16，diffs=0；条目数/示例行/SKIP 面 27 = 27 = 27；7 件轻探 `--help` 全旗标在场（baseline_diff 位置参数以 metavar 渲染）。

## 6. 锚滞后登记 · Anchor-lag register (growth cycle 3)

The version anchor at the top (5829f6d) lags the working-tree HEAD (8e04cc6) by seven commits. Facts measured on the lagged state, per the caller duty in section 0:

- Committed tool count at HEAD is 28 `.py` files under `tools/` (`git ls-tree HEAD tools/`), one above the census count 27 recorded in section 1: `tools/mcp_server.py` was added after the census snapshot. Its contract face is reachable directly (`python -I tools/mcp_server.py --help`; the capability mapping is documented in `docs/mcp.md`). A census-grade entry awaits the census lane's own re-run; this register deliberately does not hand-write one.
- Two further tools sit on disk untracked: `tools/exp_port.py` (experience-bus port, schema rocqwash-exp/1, `append`/`query` faces plus `--selftest`) and `tools/periscope.py` (collection legs; operation manual at `docs/periscope_sop.md`). They join the index only once their own commits exist on the tracked face.
- Consequence for callers: entries in section 2 stay valid for the 27 censused tools at their recorded faces; for the three faces above, invoke from each tool's own `--help` word face and record the HEAD used, exactly as the caller duty requires.
