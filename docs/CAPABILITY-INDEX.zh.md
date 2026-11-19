# rocqwash CAPABILITY-INDEX（工具能力契约面 · Tool Capability Contract Surface）

版本锚 Version anchor：`d6d0ec75747edee957e334d1ff9391707cb39f21`（引擎本体批落岸提交·施工基座注记；2026-11-15 本地 `git rev-parse HEAD` 于工作树实测。词面普查未重跑：§1/§2 逐行照录面仍以普查铸时锚 `5829f6d18a9ee2bc63c19ef46caad115e34a0c85` 的词面事实为准；census 重扫候下波）。
Version anchor: `d6d0ec75747edee957e334d1ff9391707cb39f21`, the engine-body batch integration commit, recorded here as the construction-base annotation; measured locally on 2026-11-15 (`git rev-parse HEAD` on the working tree). The census was not re-run: the §1/§2 transcribed lines remain the census-time word-face facts cast at `5829f6d18a9ee2bc63c19ef46caad115e34a0c85`; the census re-scan awaits the next work stream.

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
| ai_flavor.py | 20,687 | 481 | Y | Y | 0/5 | zero | none | arg |
| ai_flavor_apply.py | 54,124 | 1,299 | Y | Y | 0/7 | urllib.request | env | arg |
| auto_round.py | 84,108 | 1,898 | Y | Y | 2/22 | zero | none | arg |
| axiom_guard.py | 22,281 | 504 | Y | Y | 0/7 | zero | env (ROCWASH_ROCQ, ROCWASH_COQCHK) | arg |
| b_gate_audit.py | pending | pending | Y | Y | 0/1 | zero | none | arg |
| i18n_pipeline.py | 80,939 | 1,939 | Y | Y | 0/4 | zero | env | arg |
| i18n_translate.py | 45,371 | 1,301 | Y | Y | 0/13 | urllib.request | env | arg |
| i18n_verify.py | 47,407 | 1,030 | Y | Y | 0/13 | zero | none | arg |
| jargon_apply.py | 41,610 | 967 | Y | Y | 0/10 | zero | none | arg |
| learning_feedback.py | pending | pending | Y | Y | 0/1 | zero | none | arg |
| termbase.py | 22,477 | 520 | Y | Y | 0/5 | zero | none | arg |
| baseline_diff.py | 41,200 | 800 | Y | Y | 2/2 | zero | none | arg |
| bus_feeder.py | 33,027 | 749 | Y | Y | 1/4 | zero | none | arg |
| chain_graph.py | 14,854 | 335 | Y | Y | 1/3 | zero | none | arg |
| ci_triage.py | 121,218 | 2,194 | Y | Y | 0/11 | urllib.request | coq(109), win(4), runner(2) | arg |
| contrib_intake.py | 62,133 | 1,365 | Y | Y | 0/11 | git: clone | coq(23) | arg |
| cw_doctor.py | 58,988 | 1,176 | Y | Y | 0/15 | zero | env, coq(5), dyld(31), thermal(5) | arg |
| cw_sentinel.py | 119,753 | 2,168 | Y | Y | 0/23 | http.client, socket, urllib.request | coq(1), thermal(3) | arg |
| doc_lint.py | 61,486 | 1,291 | Y | Y | 0/3 | zero | none | arg |
| evolution_dashboard.py | 38,249 | 811 | Y | Y | 0/8 | zero | none | arg |
| evolve.py | 90,890 | 1,819 | Y | Y | 0/19 | zero | coq(7) | arg |
| ledger_sync.py | 26,938 | 549 | Y | Y | 0/5 | zero | none | arg |
| net_probe.py | 19,076 | 412 | Y | Y | 0/7 | socket, urllib.request | none (network is its subject) | arg |
| netname_normalize.py | 15,059 | 332 | Y | Y | 0/4 | zero | none | arg |
| norm_lint.py | 32,256 | 823 | Y | Y | 0/8 | zero | none | arg |
| pin_repair.py | pending | pending | Y | Y | 0/4 | zero | none | arg |
| pushci.py | 108,070 | 2,134 | Y | Y | 0/21 | urllib.request, git: push+ls-remote | env, coq(11) | arg |
| red_dispatch.py | 48,353 | 935 | Y | Y | 0/10 | zero | coq(5), thermal(1) | arg |
| registry_audit.py | 51,476 | 1,054 | Y | Y | 0/11 | zero | coq(12) | arg |
| registry_fix.py | 60,064 | 1,161 | Y | Y | 0/8 | zero | env, coq(5) | arg |
| registry_regen.py | 61,590 | 1,346 | Y | Y | 0/15 | zero | coq(37) | arg |
| registry_union.py | 42,872 | 931 | Y | Y | 0/14 | zero | coq(4) | arg |
| render_events.py | 26,635 | 547 | Y | Y | 0/5 | zero | none | arg |
| select_audit.py | 32,930 | 654 | Y | Y | 0/6 | zero | ocaml/opam token(2) | arg |
| selfevolve_round.py | pending | pending | Y | N | 0/2 | urllib.request | env | usage |
| symbiosis_bus.py | 39,500 | 878 | Y | Y | 1/9 | zero | none | arg |
| toolchain_dyld_doctor.py | 23,777 | 492 | Y | Y | 0/6 | zero | env, coq(32), dyld(39), thermal(5) | arg |
| unclog.py | 103,325 | 1,943 | Y | Y | 0/30 | zero | coq(5), thermal(2) | arg |
| uplink.py | 59,383 | 1,392 | Y | Y | 1/15 | zero | none | arg |
| vacgen.py | 122,111 | 2,625 | Y | Y | 0/20 | zero | lean(64), thermal(3) | arg |
| wash_shape.py | 110,172 | 2,285 | Y | Y | 0/16 | zero | env, coq(6) | arg |

表例（Legend）：Doc = 文件头 docstring 在场；Arg = argparse import 在场；Pos/Opt = 位置参数/可选旗标数；Network face = 词面三通道判读（zero = 三通道皆零命中）；Env markers = 标记族（词面命中次数）：ocaml = ocamlc/ocamldep/opam，coq = coqc/coqtop/coqchk/coqdep/rocq 系，thermal = cpu_guard/_THERMAL 系，runner = self-hosted/actions-runner，win = Windows 守卫词面，env = ROCWASH_* 环境变量，dyld = macOS dyld 工具面，lean = lake/mathlib/Lean/elan 系；Basis = 调用形还原依据（arg = argparse 还原，usage = usage 字符串）。Env markers 是词面命中，非运行时需求实证（边界见 §3.1）。

Legend: Doc = module docstring present; Arg = argparse import present; Pos/Opt = positional/optional flag counts; Network face = three-channel word-face reading (zero = no hit in any channel); Env markers = marker families with word-face hit counts (ocaml = ocamlc/ocamldep/opam; coq = coqc/coqtop/coqchk/coqdep/rocq family; thermal = cpu_guard/_THERMAL family; runner = self-hosted/actions-runner; win = Windows guard wording; env = ROCWASH_* environment variables; dyld = macOS dyld tooling face; lean = lake/mathlib/Lean/elan family). Env markers are word-face hits, not proof of runtime requirements (boundary in §3.1). Basis = invocation reconstruction source (arg = argparse; usage = usage string).

## 2. 逐件契约 · Per-Item Contract Lines

依文件名字典序 44 件；每条目逐行照录 census，新增仅「示例 Example」一行。
44 items in filename order; each entry transcribes the census verbatim; the only added line is 示例 Example.

落岸注记 Integration note（引擎本体票·落岸日）：引擎本体批七件按字典序插入本节（ai_flavor／ai_flavor_apply／i18n_pipeline／i18n_translate／i18n_verify／jargon_apply／termbase），条目转录自 `docs/engine-body-capabilities.md`（道8 稿）并经合流环节逐件 `--selftest` 活跑复验；「状态 Status」行为本批增行（增行单列声明律）；§1 总表七行的 Bytes/Lines/Pos-Opt 为合流树活测；下方汇总观察保留 census 时点词面事实不改写。
Integration note (the engine-body ticket, at integration): the seven engine-body entries are inserted in filename order, transcribed from docs/engine-body-capabilities.md (the lane-8 draft) and re-verified live by the integration agent per file (--selftest); the 状态 Status line is this batch's added line (declared single-line addition); the section 1 rows carry live measurements on the integration tree; the aggregates below stay the census-time word-face facts.

合流注记 Integration note（共生总线票·集成合流）：本节 symbiosis_bus 条目按文件名字典序插入，用途/调用形/示例行转录自本树 `python tools/symbiosis_bus.py --help` 实词面与模块 docstring（非 census 出品·本条目按实词面转录），§1 总表行为合流树活测；「状态 Status」行为本批增行（增行单列声明律）；`tests/t_mcp_face.py` 的 `symbiosis_status` MCP face（25 capability 名册）即挂本条目契约面。`tools/uplink.py` 在盘未追踪（uplink 票交付件），其 census 级条目候其自身合流增量，本注记不代写。
Integration note (the symbiosis ticket, at integration): the symbiosis_bus entry below is inserted in filename order; the purpose, invocation, and example lines are transcribed from this tree's live `python tools/symbiosis_bus.py --help` word face and the module docstring (not a census product; this entry is transcribed from the live word face); the section 1 row carries live measurements on the integration tree; the 状态 Status line is this batch's added line (declared single-line addition). The `symbiosis_status` MCP face in `tests/t_mcp_face.py` (the 25-capability roster) hangs its contract on this entry. `tools/uplink.py` sits on disk untracked (the uplink ticket's deliverable); its census-grade entry awaits that lane's own integration increment and is deliberately not hand-written here.

合流注记 Integration note（uplink 票·集成合流）：本节 uplink 条目按文件名字典序插入，用途/调用形/示例行转录自本树 `python tools/uplink.py --help` 实词面与模块 docstring（非 census 出品·本条目按实词面转录），§1 总表行为合流树活测；「状态 Status」行为本批增行（增行单列声明律）；`cw.sh uplink` 路由（头表/usage/hint_for/case 四处）随本批增量落位，`grep -c uplink cw.sh` 实测见合流注记附随证据；登记面 `docs/uplink-intake.jsonl`（schema `rocqwash-uplink/1`·首行注释形·零真实条目）与 `tests/t_uplink_shape.py`（直跑形·不入 run_tests 名册；名册计数与 README 计数行耦合，改动权在持授权的工单流）挂本条目契约面。`docs/uplink_sop.md` 为其操作规程。
Integration note (the uplink ticket, at integration): the uplink entry below is inserted in filename order; the purpose, invocation, and example lines are transcribed from this tree's live `python tools/uplink.py --help` word face and the module docstring (not a census product; this entry is transcribed from the live word face); the section 1 row carries live measurements on the integration tree; the 状态 Status line is this batch's added line (declared single-line addition). The `cw.sh uplink` route (header table / usage / hint_for / case, all four places) lands with this increment; the measured `grep -c uplink cw.sh` count rides with this note as its evidence. The register file `docs/uplink-intake.jsonl` (schema `rocqwash-uplink/1`, comment-header form, zero real rows) and `tests/t_uplink_shape.py` (run directly, deliberately not rostered in tests/run_tests.sh: the roster count is coupled to the README count lines, whose rewrite belongs to the work stream holding that authorization) hang their contracts on this entry. `docs/uplink_sop.md` is the operation manual.

合流注记 Integration note（自演进仪表盘票·集成落位）：本节 evolution_dashboard 条目按文件名字典序插入，用途/调用形/示例行转录自本树 `python -I tools/evolution_dashboard.py --help` 实词面与模块 docstring（非 census 出品·本条目按实词面转录），§1 总表行为本树活测；「状态 Status」行为本批增行（增行单列声明律）；`cw.sh evolution-dashboard` 路由（头表/usage/hint_for/case 四处）随本批增量落位，`DEFAULT_HELP_CAP` 47→48 同 registered-tool precedent；`tests/t_evolution_dashboard_shape.py`（直跑形·不入 run_tests 名册；名册计数与 README 计数行耦合，改动权在持授权的工单流）挂本条目契约面。本树现势：`docs/round-ledger.jsonl` 与 `docs/vacgen-reports/` 缺席＝工具契约内的数据态（present=false 如实出账），首份轮次账行与首份 vacgen report 落岸后曲线即活。
Integration note (the evolution-dashboard ticket, at integration): the evolution_dashboard entry below is inserted in filename order; the purpose, invocation, and example lines are transcribed from this tree's live `python -I tools/evolution_dashboard.py --help` word face and the module docstring (not a census product; this entry is transcribed from the live word face); the section 1 row carries live measurements on this tree; the 状态 Status line is this batch's added line (declared single-line addition). The `cw.sh evolution-dashboard` route (header table / usage / hint_for / case, all four places) lands with this increment, together with the `DEFAULT_HELP_CAP` bump 47 to 48 under the same registered-tool precedent. `tests/t_evolution_dashboard_shape.py` (run directly, deliberately not rostered in tests/run_tests.sh: the roster count is coupled to the README count lines, whose rewrite belongs to the work stream holding that authorization) hangs its contract on this entry. Current-tree state: `docs/round-ledger.jsonl` and `docs/vacgen-reports/` are absent, which is a data state inside the tool's contract (reported as present=false); the curve goes live once the first round row and the first vacgen report land.

合流注记 Integration note（缺口账喂送工单·集成落位）：本节 bus_feeder 条目按文件名字典序插入（baseline_diff 与 chain_graph 之间），用途/调用形/示例行转录自本树 `py -I -B tools/bus_feeder.py --help` 实词面与模块 docstring（非 census 出品·本条目按实词面转录），§1 总表行为本树活测；「状态 Status」行为本批增行（增行单列声明律）；`cw.sh bus-feeder` 路由（头表/usage/hint_for/case 四处）随本批增量落位，`DEFAULT_HELP_CAP` 48→49 同 registered-tool precedent（并发写手下 47→48 系 evolution-dashboard 流先行落位）；`tests/t_bus_feeder_shape.py`（直跑形·不入 run_tests 名册；名册计数与 README 计数行耦合，改动权在持授权的工单流）与 `docs/symbiosis_sop.md` §六（喂送面契约增量）挂本条目契约面。识别集 divergence 在册：`tools/gap_cluster.py` 类别 token 逃逸 `\u5748`（U+5748）与其出品方实发 token（U+5751，`tools/vacgen.py` 2470 行）不同码位且只读 `category` 键拼法，故喂送器自钉 U+5751 并读双键拼法（divergence 详见该器扩展契约注释与 SOP §六边界行）；gap_cluster 本体不在本工单改动面。
Integration note (the bus-feeder ticket, at integration): the bus_feeder entry below is inserted in filename order (between baseline_diff and chain_graph); the purpose, invocation, and example lines are transcribed from this tree's live `py -I -B tools/bus_feeder.py --help` word face and the module docstring (not a census product; this entry is transcribed from the live word face); the section 1 row carries live measurements on this tree; the 状态 Status line is this batch's added line (declared single-line addition). The `cw.sh bus-feeder` route (header table / usage / hint_for / case, all four places) lands with this increment, together with the `DEFAULT_HELP_CAP` bump 48 to 49 under the same registered-tool precedent (under concurrent writers, the 47 to 48 bump was landed first by the evolution-dashboard lane). `tests/t_bus_feeder_shape.py` (run directly, deliberately not rostered in tests/run_tests.sh: the roster count is coupled to the README count lines, whose rewrite belongs to the work stream holding that authorization) and `docs/symbiosis_sop.md` section 六 (the feed-face contract increment) hang their contracts on this entry. The recognition-set divergence is on record: the `tools/gap_cluster.py` category token escape `\u5748` (U+5748) differs in code point from the token its own producer emits (U+5751, `tools/vacgen.py` line 2470) and reads only the `category` key spelling, so the feeder pins U+5751 itself and reads both key spellings (the divergence is documented in that tool's extended contract comment and in the SOP section boundary line); the gap_cluster body is outside this ticket's write face.

合流注记 Integration note（基座诚信洗链编译与公理守卫工单·集成落位）：本节 axiom_guard 条目按文件名字典序插入（auto_round 与 i18n_pipeline 之间），用途/调用形/示例行转录自本树 `py -B tools/axiom_guard.py --help` 实词面与模块 docstring（非 census 出品·本条目按实词面转录），§1 总表行为本树活测；「状态 Status」行为本批增行（增行单列声明律）；`cw.sh axiom-guard` 路由（头表/usage/hint_for/case 四处）随本批增量落位，`DEFAULT_HELP_CAP` 49→50 同 registered-tool precedent。该件为本包公理守卫（审计报告 §3.2 所指最严重缺位的正主）：编译三分类（compile-ok／compile-broken 登记债／skip-无工具链）＋ compile-ok 件两级检测（轻面=逐定理 Print Assumptions survey·重面=coqchk -o 内核复检权威判定·token 检疫面不采〔gate5 判例：只可检疫不可判定〕）；`ROCWASH_ROCQ`/`ROCWASH_COQCHK` env 门控（未配置=rc 111 诚实 skip）；写面=调用方点名的 `--out` 报告卷＋私有临时工作目录（.vo 输出面 temp-only·仓树零字节）；双跑字节恒同实测在案。破坏面矩阵两行（本件编译腿写面一行＋cure_applier 编译腿写面一行）挂 `tests/test_destructive_matrix.py` 本批增行。
Integration note (the substrate compile-loop and axiom-guard ticket, at integration): the axiom_guard entry below is inserted in filename order (between auto_round and i18n_pipeline); the purpose, invocation, and example lines are transcribed from this tree's live `py -B tools/axiom_guard.py --help` word face and the module docstring (not a census product; this entry is transcribed from the live word face); the section 1 row carries live measurements on this tree; the 状态 Status line is this batch's added line (declared single-line addition). The `cw.sh axiom-guard` route (header table / usage / hint_for / case, all four places) lands with this increment, together with the `DEFAULT_HELP_CAP` bump 49 to 50 under the same registered-tool precedent. This tool is the package's axiom guard (the owner of the repo's most serious misalignment named in audit report section 3.2): compile tri-classification (compile-ok / compile-broken debt register / skip-no-toolchain) plus two-level detection on compile-ok files (light face = per-theorem Print Assumptions census; heavy face = coqchk -o kernel recheck as the authority; the token-quarantine face is not adopted per the gate5 precedent: quarantine only, never a verdict). `ROCWASH_ROCQ` / `ROCWASH_COQCHK` environment gating (unconfigured = rc 111 honest skip). Write faces: the caller-named `--out` report volume plus a private temp workdir (the .vo output face is temp-only; the repository tree gains zero bytes); the byte-identical double run is measured and on record. Two destructive-matrix rows (this tool's compile-leg write face and the cure_applier compile-leg write face) hang on this entry as `tests/test_destructive_matrix.py` additions of the same batch.

合流注记 Integration note（递归三缺口批·铸面时点）：本节 b_gate_audit／learning_feedback／pin_repair 三条目按文件名字典序插入各自字母位（b_gate_audit 落 ai_flavor_apply 与 baseline_diff 之间；learning_feedback 落 jargon_apply 与 ledger_sync 之间；pin_repair 落 norm_lint 与 pushci 之间）；三工具系本批并行交付件，条目按契约先行并行法自本批三契约面铸形（条目文以契约为准·不等工具道自身完工），每条目携「状态 Status」行为本批增行（增行单列声明律）；§1 总表三行携同一契约面声明（Doc/Arg/Pos-Opt/Network face/Env markers/Basis 取契约必带面），Bytes/Lines 两格保持 `pending`，待各工具道自身合流增量的在盘实测补齐。本节头部条目计数行按活计数器律改为实际值（43）；普查范围计数（普查时点 27 件 `.py`）、本节末汇总观察与第 5 节保真度记录行保持各自时点记录不改写。
Integration note (the recursive three-gap batch, at cast): the b_gate_audit, learning_feedback, and pin_repair entries below are inserted in filename order at their alphabetical slots (b_gate_audit between ai_flavor_apply and baseline_diff; learning_feedback between jargon_apply and ledger_sync; pin_repair between norm_lint and pushci); the three tools are this batch's parallel deliverables and the entries are cast from the batch contract faces under the contract-first rule (the entry text rides the contract, not a live tool face, and does not wait for the tool lanes); each entry carries a Status line as this batch's added line (declared single-line addition). The section 1 rows carry the same contract-face declarations (Doc/Arg/Pos-Opt/Network face/Env markers/Basis from the contract-mandated faces); the Bytes and Lines cells stay `pending` until the tool lanes' own integration increments carry the on-disk measurements. The section header count line above is advanced to the live entry count per the live-count rule; the census-scope count (27 `.py` files at census time), the aggregates at the end of this section, and the section 5 fidelity line stay the records of their own cast times and are not rewritten.

合流注记 Integration note（A 批同票增量·铸面时点）：本节 selfevolve_round 条目按文件名字典序插入（select_audit 与 symbiosis_bus 之间）；该工具先于本增量存在（常驻 cron 轮·cw.sh 路由 selfevolve-round）但铸面基线上无索引条目，故条目按契约先行并行法自 A 批契约面铸形（条目文以契约为准·非 --help 实词面：该器旗面自 sys.argv 读·无 argparse·实词面随工具道自身增量增长）；§1 总表行携契约面声明（Doc Y；Arg N·树词面无 argparse 导入；Pos/Opt 0/2＝布尔旗 `--dry-run` 与 `--pin-repair`；Network face 取词面：urllib.request 加 git push token；Env markers：env；Basis：usage），Bytes/Lines 两格保持 `pending`，待工具道自身合流增量补齐实测。本节头部条目计数行按活计数器律改为实际值（43→44）；普查范围计数、本节末汇总观察与第 5 节保真度记录行保持各自时点记录不改写。
Integration note (the A-batch closed loop, at cast): the selfevolve_round entry below is inserted in filename order (between select_audit and symbiosis_bus); the tool predates this increment on disk (the standing cron round, the cw.sh route selfevolve-round) but carried no index entry at the cast base, so the entry is cast here from the A-batch contract faces under the contract-first rule (the entry text rides the contract, not a live --help face: the tool reads its flags from sys.argv, carries no argparse, and its live flag face grows by the tool lane's own increment); the section 1 row carries the contract-face declarations (Doc Y; Arg N, no argparse import on the tree word face; Pos/Opt 0/2, the boolean flags --dry-run and --pin-repair; Network face from the word face, urllib.request plus the git push token; Env markers: env; Basis: usage), and the Bytes and Lines cells stay `pending` until the tool lane's own integration increment carries the on-disk measurements. The section header count line is advanced to the live entry count per the live-count rule (43 to 44); the census-scope count, the aggregates at the end of this section, and the section 5 fidelity line stay the records of their own cast times and are not rewritten.

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

### tools/ai_flavor.py
- 状态 Status：[live]（引擎本体票 道1 交付·合流落岸·E1 检测本体）
- 用途 Purpose：AI 味词面检测本体：36 词面电池（中文 3 族 10 面、英文词干 15、句式 8、段首 3）加独立 em-dash 电池（U+2014 计数，目标 0），词表只读 `seeds/ai_flavor/word-map.json`（正则字面逐字转录）；命中是数据非错误。Wording detection body: a 36-face battery (10 zh, 15 en stems, 8 sentence, 3 paragraph-initial) plus a separate em-dash battery (target 0); hits are data, not errors; pure exports `detect_text(text, word_map)` and `load_word_map(path)`.
- 调用形 Invocation：`python -I tools/ai_flavor.py --file <p> [--json <out>]` ／ `--tree <dir>`（*.py *.sh *.md *.json *.ts）／ `--selftest`
- 示例 Example：`python -I tools/ai_flavor.py --file docs/report.md --json out/ai-flavor-report.json`
- 依赖 Imports：argparse, json, os, re, sys（全标准库）
- 网络 Network face：zero
- SKIP 面：报告态先行零写；exit 1=有命中（数据）；em-dash 目标全域含本件自身；`--selftest` 自排除仅覆盖词面电池（数据豁免律），不覆盖 em-dash

### tools/ai_flavor_apply.py
- 状态 Status：[live]（引擎本体票 道3 交付·合流落岸·E1 施加面）
- 用途 Purpose：AI 味施加面：全部写入建议性（advisory）且在写入门（`--apply-handoff`／`--provider http`）后，改写一律经改写提供者（handoff 默认零网络：`--emit-handoff` 出段包、回填后 `--apply-handoff` 校验写入；http 腿 default-deny）；中文 10 面永不机改，词干面取 register 中性直陈形，句式面删或改述；预算帽每目标文件每类一轮（`--state`，缺省落目标件旁 `<file>.aiflavor-state.json`）；改写后重跑检测残留=0 方 GREEN。Advisory apply face: writes only through the rewrite provider (handoff default zero-network; http leg default-deny under the env gate), zh ban faces never machine-written, budget cap per file per class via `--state`, rescan residue zero gates GREEN.
- 调用形 Invocation：`python -I tools/ai_flavor_apply.py --file <p> [--json <out>] [--emit-handoff <out.jsonl> | --apply-handoff <in.jsonl> --state <p>] [--provider handoff|http]`
- 示例 Example：`python -I tools/ai_flavor_apply.py --file docs/report.md --emit-handoff out/handoff.jsonl --state out/state.json`
- 依赖 Imports：argparse, importlib.util, io, json, os, re, sys, tempfile, time, urllib.request ＋ 仓内 `tools/ai_flavor.py`（同目录）
- 网络 Network face：handoff 面 zero；http 腿 non-zero（default-deny：`ROCQWASH_MCP_ALLOW_NET=1` ＋ `ROCQWASH_LLM_ENDPOINT`／`ROCQWASH_LLM_MODEL`／`ROCQWASH_LLM_KEY` 三缺一响亮拒绝并命名缺项；逐次调用写 NETRED 行含失败；凭据值零落盘零日志）
- SKIP 面：中文 10 面处置=human 永不上机改；handoff ingest 拒收 fail-loud（`rejected[]` 如实回报）；无模型配置时 handoff 形全功能（执行智能体=模型处）

### tools/b_gate_audit.py
- 状态 Status：[contracted]（B 门槛审计交付件·契约先行并行法自契约面铸形·[live] 标记待工具道自身合流增量补挂）
- 用途 Purpose：B 级通用化门槛审计：逐类盘点实例数（round 账内 admissions 出现次数·同轮去重）与已准入轮数，按「≥3 实例 × 各 ≥1 轮已准入」门槛出 readiness verdict；instances≥3 且 rounds≥1 该类 ready；写 `docs/b-gate-audit.json`（schema `rocqwash.b-gate-audit/1`），携门槛、逐类读数（`class`/`instances`/`rounds`/`ready`/`gap`）、达标类清单、`verdict` 与 `remaining_to_b`；全空账出 verdict `not-ready` 且 remaining=3，读数是数据禁凑值。B-level generalization threshold audit: per class, counts the instances (admissions occurrences in the round ledger, deduplicated within one round) and the distinct admitting rounds, and issues a readiness verdict against the threshold of 3 instances with at least 1 admitted round each; writes `docs/b-gate-audit.json` (schema `rocqwash.b-gate-audit/1`); an empty record reads verdict `not-ready` with remaining 3, reported as data and never padded.
- 调用形 Invocation：`python -I tools/b_gate_audit.py [--selftest]`（默认跑读轮次记录出审计件与 stdout 摘要）
- 示例 Example：`python -I tools/b_gate_audit.py --selftest`
- 依赖 Imports：契约面声明仅标准库（argparse CLI·JSON 读取·tempfile 夹具）；逐项 import 清单待工具道自身合流增量补齐。Standard library only per the contract face (argparse CLI, JSON reading, tempfile fixtures); the itemized import list rides the tool lane's own integration increment.
- 网络 Network face：zero（契约面声明 no network by design）
- SKIP 面：exit 0=读数是数据（空账或未达标类出 `not-ready` 属数据态·禁凑值）；坏账行或缺件记入 `error` 字段且 stdout 摘要 fail-loud·续跑不静默跳过；唯一写面=`docs/b-gate-audit.json`；`--selftest` 四矢量离线跑 tempfile 夹具（达标类／单实例类／空账／坏行容错），零网络，零触真实记录

### tools/baseline_diff.py
- 用途 Purpose：对比两份基线文件，产出增减报告（JSON/markdown 双出形）。Compares two baseline files and reports additions and removals (JSON and markdown output).
- 调用形 Invocation：`python tools/baseline_diff.py <old> <new> [--json] [--md]`
- 示例 Example：`python tools/baseline_diff.py <old> <new> --json <value>`
- 依赖 Imports：argparse, io, json, os, shutil, subprocess, sys, tempfile
- 网络 Network face：zero
- SKIP 面：无特殊环境词面标记

### tools/bus_feeder.py
- 状态 Status：[live]（缺口账喂送工单交付·集成落位·本批增行）
- 用途 Purpose：共生交换包到 TODO-SEAT 缺口账的喂送器：`feed` 读一只离线交换包（schema `rocqwash-symbio/1`，`tools/symbiosis_bus.py` export 面出品），按三规则识别集（出品方实发坑类别 token U+5751 于顶层 `category` 或 source 字典 `category`/中文键两拼法；points/evidence 内 `TODO-SEAT` 字面；evidence 内 `status=todo_seat` 字面）选出 gap 类条目，每条落恰一行缺口行到缺口喂送账（缺省 `docs/gap-feed-ledger.jsonl`，`--ledger` 可改指）：行内条目逐字保真（schema `rocqwash-exp/1`·指纹域不动）加三枚指纹域外 schema 增量（`correlationId`=`feed:<sourceRepo>@<anchor>`·`shapeKey` 沿 `tools/gap_cluster.py` 族形状键链·`recognition`=命中规则名）；重复 id／指纹响亮跳过零写入（幂等，同包重放字节恒同）；`status` 出行数、路由、shape→rows 映射与逐包 present/new 读数。时间点与 id 一律取自条目内容禁运行时注入；写面仅缺口喂送账一件；零网络设计。Gap-ledger feeder for symbiosis swap packages: `feed` reads one offline swap package (schema `rocqwash-symbio/1`, the export face of `tools/symbiosis_bus.py`), selects gap-class entries by the three-rule recognition set (the producer's real pitfall category token U+5751 under the top-level `category` key or the source dict's `category` / zh key spellings; the literal `TODO-SEAT` token in points or evidence; the literal `status=todo_seat` token in evidence), and lands exactly one gap row per selected entry in the gap feed ledger (default `docs/gap-feed-ledger.jsonl`, `--ledger` overrides): the row keeps the entry verbatim (schema `rocqwash-exp/1`, the fingerprint domain untouched) plus three schema increments outside the fingerprint domain (`correlationId` = `feed:<sourceRepo>@<anchor>`, `shapeKey` from the `tools/gap_cluster.py` family-shape key chain, `recognition` = the rule name); repeated ids and fingerprints skip loudly with zero writes (idempotent, byte-identical replay); `status` reports row counts, routes, the shape-to-rows mapping, and per-package present/new readings. Ids and time points ride entry content, never a clock; the gap feed ledger is the only write face; zero network by design.
- 调用形 Invocation：`python tools/bus_feeder.py [--selftest] {feed,status} --swap SWAP.jsonl [--ledger P] [--dry-run]`（`--swap` feed 面恰一·status 面可重复）
- 示例 Example：`python tools/bus_feeder.py feed --swap docs/symbiosis-swap-round1.jsonl --ledger docs/gap-feed-ledger.jsonl --dry-run`
- 依赖 Imports：argparse, json, os, sys ＋ 仓内 `tools/symbiosis_bus.py`（同目录；交换包读取·envelope 校验·共享退出码异常·canonical 行形）＋ 仓内 `tools/gap_cluster.py`（族形状键链与形状抽象）
- 网络 Network face：zero（三通道零命中；no network by design）
- SKIP 面：exit 0=读数是数据（skip 行／零命中／零缺口行均如实出账）；1=selftest 矢量组红；2=用法或 IO；9=缺件或损坏输入（交换包/账行坏 JSON·envelope 漂移·指纹失真）零写入；识别集 divergence（gap_cluster 类别 token 码位 U+5748 vs 出品方 U+5751）在该器扩展契约注释与 `docs/symbiosis_sop.md` §六边界行在册；真实样本干跑读数 `would-feed=1 nonGap=26 total=27`

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

### tools/evolution_dashboard.py
- 状态 Status：[live]（自演进仪表盘工单交付·集成落位·本批增行）
- 定位 Positioning：the dashboard is the standing **a KPI aggregation read-out** face over the three ledgers; the rocqos rename candidate awaiting adjudication（更名候选在册未应用·rename is a candidate, not an applied change）
- 用途 Purpose：自演进仪表盘：聚合三本在库账面（经验账 `docs/exp-ledger.jsonl` schema `rocqwash-exp/1`＋轮次账 `docs/round-ledger.jsonl` schema `rocqwash-round/1`＋vacgen v2 report JSON 文件族）出一份仪表盘：coverageLowerPct 曲线（逐 report run 一点·按内容时点排序·携逐点 TODO-SEAT 增量与上升旗标）、轮次转化面（greenPct＝verify_rc 0 轮占比·classConversionPct＝admissions 对 classes_applied）、逐 run 缺口数体温计读数（最新曲线点）。缺席的缺省路径账面＝数据态（present=false 如实出账）；显式指认路径缺席 exit 9。写面仅调用方点名的 `--json-out`/`--md-out` 两件；零网络设计。Self-evolution dashboard: aggregates the three standing accounts (the experience ledger schema `rocqwash-exp/1`, the round ledger schema `rocqwash-round/1`, and vacgen v2 report JSON files) into one dashboard: the coverageLowerPct curve (one point per report run, ordered by content-borne time point, with a per-point TODO-SEAT delta and rise flag), the rounds conversion face (greenPct and classConversionPct), and the thermometer reading (the latest curve point). An absent default-path account is a data state (present=false); an explicitly flagged absent path exits 9. The only writes are the caller-named `--json-out` / `--md-out` files; zero network by design.
- 调用形 Invocation：`python -I tools/evolution_dashboard.py [--repo <root>] [--exp-ledger <p>] [--rounds <p>] [--reports <p>]... [--json-out <p>] [--md-out <p>] [--stdout markdown|json] [--selftest]`
- 示例 Example：`python -I tools/evolution_dashboard.py --json-out docs/dashboard.json --md-out docs/dashboard.md`
- 依赖 Imports：argparse, json, os, shutil, sys, tempfile（全标准库）
- 网络 Network face：zero（无 socket 面；no network by design）
- SKIP 面：exit 0=读数是数据（缺席账面／零条目／零轮次／零 report run 均如实标记）；1=selftest failing；2=用法错（含坏 `--stdout` 取值）；9=显式指认路径缺席／账行或 report 非 JSON／无 vacgen 面／输出写失败（零写入）；时间点一律取自输入内容禁运行时注入；`--reports` 目录展开为 *.json 排序序

### tools/evolve.py
- 用途 Purpose：自演化引擎 v1：从 watcher 事件与台账面生成演化草案并登记（sentinel/suite/registry 系旗标面在卷）。Self-evolution engine v1: drafts evolution proposals from watcher events and ledger faces (sentinel, suite, and registry flag families present).
- 调用形 Invocation：`python tools/evolve.py [--draft-out] [--json] [--repo-root] [--top] [--baseline] [--jargon-map] [--watch-repo] [--sentinel-state] [--sentinel-state-seed] [--sentinel-branch] [--sentinel-events] [--sentinel-injector] [--suite-ledger] [--suite-now] [--registry-git] [--registry-ref] [--git-path-order] [--git-path-project] [--registry-baseline]`
- 示例 Example：`python tools/evolve.py --draft-out <value> --suite-now`
- 依赖 Imports：argparse, io, json, os, re, shutil, subprocess, sys, tempfile ＋ 仓内 `certify/frozen8.py`（sys.path 注入跨目录引用）
- 网络 Network face：zero（git 子命令 token 面仅本地操作：status/commit/add）
- SKIP 面：coq 系词面（7）

### tools/auto_round.py
- 状态 Status：[live]（引擎本体票 道9 交付·合流落岸·轮次账/回档/salvage 本体）
- 用途 Purpose：轮次账回档本体：autonomy.json 双档准入（auto 自批/gated 等人批·同一代码路径 admission_decision）加 §7.2 十键轮次账 JSONL（append-only）加 commit trailer（Rocqwash-Round/-Mode/Salvage-Of）加轻量 ref refs/rocqwash/rounds/\<n\> 加回档=先归档 refs/rocqwash/drift/ 后单 revert 回锚（零 reset 零 force 零 push）加 salvage 精修包往返加振荡告警加 max_unreviewed_rounds 软停（--continue 显式放行）加 status/list/log 三查询面。Auto round ledger body: admission per the autonomy gear, one verified commit per round, append-only ledger JSONL, round trailers plus lightweight refs, anchor rollback via drift archive then a single revert (no reset, no force, no push), salvage round-trip, oscillation alarm and a soft stop on unreviewed rounds.
- 调用形 Invocation：`python -I tools/auto_round.py <command> [--repo-root <p>] [--autonomy <p>] [--state <p>] [--ledger <p>] [--continue]`；commands：commit / approve / anchor / rollback / salvage / merge-salvage / status / list / log；加 `--selftest`
- 示例 Example：`python -I tools/auto_round.py status --repo-root .`
- 依赖 Imports：argparse, datetime, json, os, shutil, subprocess, sys, tempfile（全标准库）
- 网络 Network face：zero（V18 反网络自检自扫描·socket/urllib/ftplib/smtplib/http.client 词面系负扫描 token，非调用面）
- SKIP 面：git 提交面经 subprocess（git 在场才活）；一切变更面先验证后写；轮次账 append-only（禁回写历史行）

### tools/axiom_guard.py
- 状态 Status：[live]（基座诚信洗链编译与公理守卫工单交付·集成落位·本批增行）
- 用途 Purpose：仓级公理守卫：对仓内全部 .v 件（23 件全量·除 .git）编译三分类（compile-ok／compile-broken 登记债·错误尾随账／skip-无工具链），compile-ok 件走两级检测：轻面=逐定理 Print Assumptions survey（注释/字符串掩蔽状态机提名·批编译按序归属·标记数不齐逐定理回退）；重面=coqchk -o 内核复检（CONTEXT SUMMARY 的 Axioms 节为唯一判据·stdlib 索引松弛节不判）＝权威判定；本仓标准=Closed 零公理·白名单缺省空（`--allow-axiom` 可重复指认）；轻面报公理即红（预筛面）·heavy 报公理或不可判即红（不可判≠passing）；compile-broken 件登记为债非红。编译走私有临时目录（.vo 输出面 temp-only·仓树零字节·源目录 -Q 映射只读解析同籍世界）；报告卷=调用方 `--out` 下 `axiom-guard-report.json`（排序输入·零墙钟·双跑字节恒同）。Repo-wide axiom guard: compiles and tri-classifies every .v file under the repo (23 files at the reference HEAD, .git excluded): compile-ok / compile-broken into the debt register with error tails / skip-no-toolchain, and judges every compile-ok file at two levels: the light face, a per-theorem Print Assumptions census (statement names extracted through a comment/string masking scanner, one batched census compile attributed in order, per-statement fallback when the marker count mismatches), and the heavy face, a coqchk -o kernel recheck whose CONTEXT SUMMARY Axioms section is the only judged section (stdlib index-relaxation sections are never judged) as the authoritative verdict. The repo standard is Closed zero axioms with an empty default whitelist (`--allow-axiom` repeats); a light-face axiom fails the file (pre-screen), a heavy-face axiom or an unjudgeable heavy face fails the file (unjudgeable is not green); compile-broken files are debt, not red. Compiles run in a private temp workdir (the .vo output face is temp-only; the repository tree gains zero bytes; the source directory is mapped -Q read-only so built sibling worlds resolve); the report volume is `axiom-guard-report.json` under the caller-named `--out` (sorted inputs, no wall clock, byte-identical double run).
- 调用形 Invocation：`python3 tools/axiom_guard.py --repo <dir> [--out <dir>] [--rocq <bin>] [--coqchk <bin>] [--allow-axiom <name>]... [--timeout <sec>] [--keep]`
- 示例 Example：`ROCWASH_ROCQ=/path/rocq ROCWASH_COQCHK=/path/coqchk python3 tools/axiom_guard.py --repo . --out evid/t0-2`
- 依赖 Imports：argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile（全标准库）＋ 外部二进制 rocq／coqchk（flag 或 env 提供·缺一即 skip·绝不模拟）
- 网络 Network face：zero（子进程仅本地 rocq/coqchk 编译与内核复检；no network by design）
- SKIP 面：exit 0=PASS（compile-broken 件在债册·非红）；1=failing（白名单外公理或 heavy 面不可判）；2=用法错；9=fail-loud（已配置的二进制路径不存在／`--repo` 缺失）；111=rocq 或 coqchk 未配置（flag 与 env 皆无）诚实 skip·判空不模拟（承 verify/ rc 111 口径）；`ROCWASH_ROCQ`/`ROCWASH_COQCHK` env 门控；token 检疫面不采（gate5 判例：只可检疫不可判定）；真跑须 `tools/cpu_guard.sh` 包裹（承 extract_magic_check 契约形）

### tools/i18n_pipeline.py
- 状态 Status：[live]（引擎本体票 道4 交付·合流落岸·E4 编排本体 P0/P1/P3/P6）
- 用途 Purpose：zh<->en 双向四联动管线编排本体：六操作签名不可变（承 `seeds/i18n/pipeline_stub.py`），本道实现 P0 政策预查（`repo`/`paper`/`supplement` regime 表，refusal 即合法结果 exit 0 记台账）、P1 分段器（保护名单、段=连续散文行区间、段账十键（含 policy_precheck_ref））、P3 四联动编排（L1 termbase 查词、L2 jargon 投影、L3 CJK 零残留加 em-dash 密度、L4 ai_flavor 检测）、P6 段账闭合校验。Pipeline orchestration body: six immutable operation signatures, P0 policy pre-check (refusal is a legal exit-0 ledgered outcome), P1 segmentation under the protection list, P3 four-linkage application, P6 append-only ledger closure gate.
- 调用形 Invocation：`python -I tools/i18n_pipeline.py --manifest <run.json> --stage p0|p1|p3|p6 [--json <out>]` ／ `--selftest`
- 示例 Example：`python -I tools/i18n_pipeline.py --manifest out/run.json --stage p1 --json out/segments.json`
- 依赖 Imports：argparse, io, json, os, re, subprocess, sys, tempfile ＋ 仓内 `tools/jargon_apply.py`／`tools/i18n_translate.py`／`tools/i18n_verify.py`／`tools/termbase.py`（组装面）
- 网络 Network face：zero（P2 网络面全在 `tools/i18n_translate.py` provider 内）
- SKIP 面：P0 refusal 是合法结果非故障（台账有行）；闭合校验不满足即 fail-loud 拒闭合；缺道5/道6 模块时组装腿 fail-loud

### tools/i18n_translate.py
- 状态 Status：[live]（引擎本体票 道5 交付·合流落岸·E4 模型处层 P2）
- 用途 Purpose：模型处层（P2）：handoff 形默认零网络（`--emit` 出段包、回填后 `--ingest` 十键校验（含 policy_precheck_ref），缺 model_id 或缺标注即违规拒收 fail-loud）；http 形可选 default-deny（OpenAI 兼容端点逐段调用逐段标注 `annotation_site="model"`，NETRED 台账逐次含失败）；prompt 模板 `--prompts <dir>`（缺省内置常数）。Model-site layer P2: handoff form default zero-network with ten-key (including policy_precheck_ref) ingest validation; http form optional default-deny with per-segment annotation and a NETRED ledger line per call.
- 调用形 Invocation：`python -I tools/i18n_translate.py --segments <p> --emit <out.jsonl> [--prompts <dir>]` ／ `--ingest <in.jsonl>` ／ `--provider handoff|http`
- 示例 Example：`python -I tools/i18n_translate.py --segments out/segments.json --emit out/handoff.jsonl`
- 依赖 Imports：argparse, io, json, os, re, sys, tempfile, time, urllib.request
- 网络 Network face：handoff 面 zero；http 腿 non-zero（default-deny：环境门三变量缺一响亮拒绝并命名缺项；NETRED 行逐次含失败；凭据值零落盘零日志）
- SKIP 面：全票唯一网络面=http 提供者腿；无环境门拒绝而非降级；零标注机器段=管线违规十键拒收（含 policy_precheck_ref）

### tools/i18n_verify.py
- 状态 Status：[live]（引擎本体票 道6 交付·合流落岸·E4 P4/P5）
- 用途 Purpose：P4 机械验证编排（子进程调 `tools/ai_flavor.py`／`tools/norm_lint.py --jargon-map`／`tools/doc_lint.py`，汇成验证矩阵 JSON `rocqwash.i18n.verify/1`）；P5 人工十点单面（`--emit-tenpoint` 出审读表单按目标面形态取变体；`--ingest-tenpoint` 校验结论写回段账 `tenpoint_verdict`；引擎不替人判）。P4 runs the mechanical verify instruments as subprocesses into one matrix; P5 emits the human ten-point form and ingests verdicts fail-loud; the engine never judges.
- 调用形 Invocation：`python -I tools/i18n_verify.py --verify-target <p> [--json <out>]` ／ `--emit-tenpoint <target>` ／ `--ingest-tenpoint <verdicts.json>` ／ `--selftest`
- 示例 Example：`python -I tools/i18n_verify.py --emit-tenpoint docs/report.en.md --json out/tenpoint-form.json`
- 依赖 Imports：argparse, io, json, os, subprocess, sys, tempfile ＋ 本地仪器子进程（`tools/ai_flavor.py`／`tools/norm_lint.py`／`tools/doc_lint.py`）
- 网络 Network face：zero（子进程均为本地工具只读探跑）
- SKIP 面：P5 十点单为人工门（引擎出表单与写回，不产 verdict）；子进程目标件缺席 fail-loud；结论文件 schema=`rocqwash.tenpoint.verdicts/1`

### tools/jargon_apply.py
- 状态 Status：[live]（引擎本体票 道2 交付·合流落岸·E2 施加面加纯函数库）
- 用途 Purpose：黑话到标准术施加面：数据只读 `seeds/jargon/jargon-map.json`（62 条）；只机改 `disposition:"replace"` 条目；`rewrite_or_delete` 永不机改（findings 列出处置=human）；guarded 行默认拒改上报（`--guarded-interactive` 出逐行问询文件）；preserve 豁免走 exempt 机制；标识符位永不改写（反引号跨段遮蔽）；默认 plan 零写列 before/after 对，`--apply` 后自动重扫残留=0 方 exit 0，幂等。Jargon-to-standard apply face over the 62-entry map: replace entries only, human rows listed never applied, guarded rows refuse by default, plan default zero-write, apply rescans to residue zero, idempotent.
- 调用形 Invocation：`python -I tools/jargon_apply.py --file <p> | --tree <dir> [--plan | --apply] [--json <out>] [--guarded-interactive]` ／ `--selftest`
- 示例 Example：`python -I tools/jargon_apply.py --tree docs --plan --json out/jargon-plan.json`
- 依赖 Imports：argparse, importlib.util, io, json, os, re, shutil, subprocess, sys, tempfile ＋ 仓内 `tools/norm_lint.py`（同源匹配器）
- 网络 Network face：zero
- SKIP 面：默认零写；`rewrite_or_delete` 行处置=human；重扫残留非零即 exit 非 0（验证红）；幂等（二次 apply 零 would-fix）

### tools/learning_feedback.py
- 状态 Status：[contracted]（学习环反馈交付件·契约先行并行法自契约面铸形·[live] 标记待工具道自身合流增量补挂）
- 用途 Purpose：调度反馈边：读三本在库账面（`docs/round-ledger.jsonl`／`docs/round-state.json`／`docs/exp-ledger.jsonl`），算出调度可读反馈件 `docs/scheduling-feedback.json`（schema `rocqwash.scheduling-feedback/1`）：轮次总数含 auto 与人批拆分、批准率分母含人批轮、逐类 gear 与 confidence 读数、修复结果四态计数（repaired／escalated／watch-only-guard-correct·归不进者如实记 `unrecorded`）；反馈边声明为 open：批准率自此有读数，调度侧尚未消费（declared blank）。Scheduling feedback edge: reads the three standing accounts and computes the scheduling-readable feedback file `docs/scheduling-feedback.json` (schema `rocqwash.scheduling-feedback/1`): round totals with the auto and human-approved split, the approval rate over all rounds, per-class gear and confidence readings, and the four-state repair outcome tally with unclassifiable rows honestly counted as `unrecorded`; the feedback edge is declared open (the approval rate becomes readable while scheduling does not yet consume it).
- 调用形 Invocation：`python -I tools/learning_feedback.py [--selftest]`（默认跑读三账出反馈件与 stdout 摘要）
- 示例 Example：`python -I tools/learning_feedback.py --selftest`
- 依赖 Imports：契约面声明仅标准库（argparse CLI·JSONL 读取·tempfile 夹具）；逐项 import 清单待工具道自身合流增量补齐。Standard library only per the contract face (argparse CLI, JSONL reading, tempfile fixtures); the itemized import list rides the tool lane's own integration increment.
- 网络 Network face：zero（契约面声明 no network by design）
- SKIP 面：exit 0=读数是数据（缺账或坏行记 `error` 字段·stdout 摘要 fail-loud·续跑不静默跳过；分母为零时 `repair_action_rate` 出 null·如实声明禁凑值）；唯一写面=`docs/scheduling-feedback.json`；`--selftest` 四矢量跑 tempfile 夹具（一 auto 一人批两轮／坏行容错／空账／四态全 unrecorded），零网络，零触真实账

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
- 调用形 Invocation：`python tools/norm_lint.py [--tree] [--file] [--jargon-map] [--cjk-threshold] [--cjk-whitelist] [--json] [--md] [--selftest]`；落岸增旗 integration addition（引擎本体票·落岸日）：`[--ai-flavor-map]`（可选 ai-flavor 报告面，缺省关闭时报告逐字节不变；optional ai-flavor report face, byte-identical report when absent）
- 示例 Example：`python tools/norm_lint.py --tree <value> --selftest`
- 依赖 Imports：argparse, fnmatch, io, json, os, re, shutil, sys, tempfile, tokenize
- 网络 Network face：zero
- SKIP 面：无特殊环境词面标记

### tools/pin_repair.py
- 状态 Status：[contracted]（R15 钉修执行器交付件·契约先行并行法自契约面铸形·[live] 标记待工具道自身合流增量补挂）
- 用途 Purpose：R15 类钉漂移修复执行器：读 seed JSON `provenance.sources` 数组逐源 md5 核对，跑 sync 工具零写 plan（`python -I tools/jargon_map_sync.py`），仅 `VERDICT IN-SYNC` 读数放行（其余 verdict 即内容 retag·需人工裁定·exit 3 携原始 verdict 上报）；`--plan` 报告漂移源（path／pinned md5／current md5）零写入；`--apply` 以源文件现字节重签 seed 的 md5 字段（保 JSON 键序与 2 空格缩进·只改 md5 字段值），复跑 `python -I tests/t_engines_seeds.py` 作本地验证门，验证不绿即以 apply 前字节快照还原 seed（exit 4·fail-loud）。Pin-drift repair executor for the R15 class: md5-checks each pinned source of the seed JSON's `provenance.sources`, runs the sync tool's zero-write plan, and proceeds only on `VERDICT IN-SYNC` (any other verdict means content retagging, which belongs to human adjudication: exit 3 with the raw verdict reported); `--plan` reports the drifted sources with zero writes; `--apply` re-signs the seed's md5 fields from the source files' current bytes (JSON key order and 2-space indent preserved) and re-runs the local seeds suite as the verification gate, restoring the seed from the pre-apply byte snapshot (exit 4, fail-loud) when verification is not green.
- 调用形 Invocation：`python -I tools/pin_repair.py --selftest | --plan | --apply [--seed <path>]`（`--seed` 缺省 `seeds/jargon/jargon-map.json`）
- 示例 Example：`python -I tools/pin_repair.py --plan`
- 依赖 Imports：契约面点名 hashlib、io、json、subprocess（仅标准库）；逐项 import 清单待工具道自身合流增量补齐。The contract face names hashlib, io, json, subprocess (standard library only); the itemized import list rides the tool lane's own integration increment.
- 网络 Network face：zero（子进程仅本地 sync 工具与本地 seeds 套件；no network by design）
- SKIP 面：exit 0=plan 报告或 apply 验证绿（无漂移 `action:"none"`·报告面 `action:"plan"`·apply 绿后 `verify:"seeds-suite-green"`）；3=非 IN-SYNC verdict（内容 retag 需人工裁定·携原始 verdict 上报·禁机改）；4=apply 后验证不绿·seed 以 apply 前字节快照还原·fail-loud；stdout 一行 JSON 结果面·过程可读面走 stderr·禁打印任何密钥；`--selftest` 四矢量跑 tempfile 夹具（IN-SYNC／漂移／absent／非 IN-SYNC），零网络，零触真实 seed

### tools/pushci.py
- 用途 Purpose：推岸后 CI 一条龙编排器：push、ls-remote 确证、CI monitor、判读与愈合轮（步骤/愈合上限/盯守节律均参数化）。One-shot push-then-CI orchestrator: push, ls-remote confirmation, CI watching, verdict reading, and heal rounds (steps, heal cap, and watch cadence parameterized).
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

### tools/selfevolve_round.py
- 状态 Status：[contracted]（A 批同票增量交付件·按契约先行并行法自本批契约面铸形·[live] 标记随工具道自身合流增量）[contracted](A-batch closed-loop deliverable, cast from the batch contract face under the contract-first parallel rule; the [live] marker rides the tool lane's own integration increment)
- 用途 Purpose：cron 面单次确定性机械轮：census（jargon_apply --plan）→apply→verify（py_compile／bash -n 硬性检查＋norm_lint/doc_lint advisory）→auto_round commit→push→路由 CI 判读。A 批同票增量新增两面：（1）环境感知钉修腿·仅在显式 `--pin-repair` 旗后激活（hosted cron 形不传旗·计划行为零变化）：对 seed 跑 pin_repair --plan；钉源在本机缺席（hosted 结构性盲·仓外绝对路径）＝追加一行记录（action=plan·note=hosted-blind）后干净跳过零 commit；有漂移且 plan rc=0＝--apply 并落一枚独立 commit（class R15-repair·message 指名 IN-SYNC plan verdict 与 armed verify-rollback）·由 round 既有 push 顺带推岸；apply rc 非 0＝fail-loud 零 commit（执行器自恢复 pre-apply 字节）；零漂移＝一行 no-op；全腿围栏：任何意外失败追加一行 ok:false 记录后 round 主链继续·round 永不被钉修腿阻塞。（2）round 报告增 `cadence_hint` 字段·读 `docs/scheduling-feedback.json`（schema rocqwash.scheduling-feedback/1·缺文件→hint=normal·note=absent）·代码内有限常量档位表：escalated ≥3 或 repaired==0 且修复动作总数 ≥5→alert；repair_action_rate <0.2→slow；否则 normal；alert 读数另向 `docs/repair-plan-ledger.jsonl`（schema rocqwash.repair-plan/1）追加一行 cadence-alert 并响亮打印。yml cron 表达式零改动：报告只携 hint·节奏调制=桌面令。One deterministic mechanical round on the cron face: census -> apply -> verify -> auto_round commit -> push -> route the CI judge. The A-batch increment adds two faces: (1) the environment-aware pin-repair leg behind the explicit `--pin-repair` flag (the hosted cron form passes no flag, zero scheduled behavior change): plan the seed behind the IN-SYNC verdict; pinned sources absent on the host = one ledger row (action=plan, note=hosted-blind), then a clean zero-commit skip; drift with plan rc=0 = apply and one independent commit (class R15-repair) carried by the round's existing push; apply rc nonzero = fail-loud, zero commit; zero drift = a one-line no-op; the leg is fenced so the round main chain never blocks on it. (2) consumption v2: the round report carries `cadence_hint` read from `docs/scheduling-feedback.json` (a missing file reads hint normal, note absent) mapped by a finite constant tier table (alert / slow / normal as above); an alert reading also appends one cadence-alert row (schema rocqwash.repair-plan/1) and prints loud. The workflow cron expression is untouched: cadence modulation is a desk order, the report carries the hint only.
- 调用形 Invocation：`python -I tools/selfevolve_round.py [--dry-run] [--pin-repair]`（无 argparse·旗面自 sys.argv 读；`--dry-run` 本地测试形；`--pin-repair` 桌面/本地站点的钉修腿显式开关）(no argparse; the flag face is read from sys.argv; `--dry-run` is the local testing form; `--pin-repair` is the desk/local opt-in for the repair leg)
- 示例 Example：`python -I tools/selfevolve_round.py --dry-run --pin-repair`
- 依赖 Imports：json, os, subprocess, sys, urllib.request（全标准库；urllib.request 为 CI 判读路由腿的函数内导入·逐项清单随工具道自身合流增量）(all standard library; urllib.request is the function-local import of the CI judge routing leg; the itemized list rides the tool lane's own integration increment)
- 网络 Network face：non-zero（urllib.request；git push 子进程词面）(non-zero; urllib.request; the git push subprocess token face)
- SKIP 面：exit 0=正常终态（零合格修复的干净 no-op 轮·dry-run 报告·完成的轮次；钉修腿的 hosted-blind 跳过与零漂移 no-op 为账面数据态非失败）；非零退出=fail-loud 检查（census 报告不可读·apply residue 非零·准入拒绝·push 拒绝）；repair-plan 账路径受 `ROCQWASH_REPAIR_PLAN_LEDGER` env 重定向（缺省 `docs/repair-plan-ledger.jsonl`）；cadence 档位=代码内有限常量表（normal/slow/alert）禁运行时生成；`round-plan.json` 与 `round-apply.json` 为轮次运行时产物。Exit 0 = green terminal states (a clean no-op pass, the dry-run report, or a completed round; a hosted-blind or zero-drift repair leg is a ledger data state, never a failure); nonzero exits are the fail-loud gates (unreadable census report, apply residue nonzero, admission refusal, push refusal); the repair-plan ledger path honors the `ROCQWASH_REPAIR_PLAN_LEDGER` environment override; cadence tiers are a finite constant table, never generated at run time; `round-plan.json` and `round-apply.json` are round runtime products

### tools/symbiosis_bus.py
- 状态 Status：[live]（共生总线票 道1-3 交付·集成合流·规格 §1.1 四 face 本体）
- 用途 Purpose：跨仓共生经验总线：export 把本仓 `docs/exp-ledger.jsonl`（schema `rocqwash-exp/1`）导出为离线交换包（schema `rocqwash-symbio/1`·首行 envelope 携 `sourceRepo`/`anchor`/`entryCount`·随后每行一条原样条目）；import 逐条经 `tools/exp_port.py` append 单口落账（重复 id/fingerprint 幂等跳过·correlationId 携 `symbio:<sourceRepo>@<anchor>` 路由标记）；status 双向计数（入向 bus 行计数＋对给定交换包的 present/new 计数·时点取自条目内容）；diff 出两本账的条目 id 差集清单。零网络设计（交换走离线文件·NETRED 登记面写明 no network by design）。Cross-repository experience bus: export renders the local ledger as an offline swap package (schema `rocqwash-symbio/1`, one envelope line carrying `sourceRepo`/`anchor`/`entryCount`, then one verbatim entry line per entry); import lands each entry through the `tools/exp_port.py` append face (duplicate ids and fingerprints skip idempotently; a `symbio:<sourceRepo>@<anchor>` correlationId marks the route); status counts both directions from entry content; diff lists the entry-id difference of two ledgers. No network face by design (exchange walks offline files; the NETRED register row states no network by design).
- 调用形 Invocation：`python tools/symbiosis_bus.py [--selftest] {export,import,status,diff} [--out SWAP.jsonl] [--swap SWAP.jsonl] [--ledger P] [--source-repo NAME] [--anchor HEX] [--a LEDGER_A] [--b LEDGER_B] [--dry-run]`（`--swap` import 面恰一·status 面可重复；export 真跑需 `--out`）
- 示例 Example：`python tools/symbiosis_bus.py export --ledger docs/exp-ledger.jsonl --out swap-round1.jsonl --source-repo rocqwash`
- 依赖 Imports：argparse, json, os, sys ＋ 仓内 `tools/exp_port.py`（同目录；import 腿经其 append 契约与 ledger 解析）
- 网络 Network face：zero（三通道零命中；no network by design）
- SKIP 面：exit 0=读数是数据（duplicate-skip／零差集／零计数）；1=selftest 矢量组报错退出；2=用法或 IO；9=缺件或损坏输入零写入；时间戳取自条目内容禁运行时注入；写面=export 的 `--out` 一件＋import 经 append 口的账本

### tools/termbase.py
- 状态 Status：[live]（引擎本体票 道6 交付·合流落岸·E3 离线查词薄层）
- 用途 Purpose：术语库只读薄层：`seeds/termbase/termbase.json` 只读（stdlib json，schema 校验 fail-loud）加 `lookup(term) -> entries` 精确面查词（剥强调与全角括号、按分隔符拆面）加 `--selftest`。Read-only terminology thin layer over the E3 seed: schema validation fails loud, exact-face lookup, zero network; the E3 net interface and DIY channel stay candidates of their own seed SPECs.
- 调用形 Invocation：`python -I tools/termbase.py --lookup <term> [--db <p>] [--json <out>]` ／ `--schema-check` ／ `--selftest`
- 示例 Example：`python -I tools/termbase.py --selftest`
- 依赖 Imports：argparse, json, os, sys（全标准库）
- 网络 Network face：offline zero（联网接口为 E3 candidate，default-deny，不在本票）
- SKIP 面：内置快照永不原位编辑（上游术语表唯一维护点）；miss 是数据（空结果 exit 0）

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

### tools/uplink.py
- 状态 Status：[live]（uplink 票 交付三件·集成合流·规格 §1.2 三 face 本体）
- 用途 Purpose：外产回传包标准上行门：`verify` 把包 zip 与 md5 旁证（32 位十六进制串或旁证文件）及 md5sum 行格式逐文件 manifest 做机器比对，stdout 出逐件证据清单（ok／mismatch／missing／unlisted／declared-surface／dir／info＋汇总行），任一失配或缺件即 fail-loud 终态 rc=1；`intake` 先内置复验同一比对面（红即拒绝、零落笔），green 才向登记面 append 恰一行（schema `rocqwash-uplink/1`·六字段 `package`/`source-seat`/`md5`/`verified`/`landed-ref`/`exit`·同参重跑 duplicate-skip 幂等·`--dry-run` 只报 would-append 行）；`pr-prep` 从登记行渲染 PR 描述草稿文件（只收 verified=true 行·零 git 调用·绝不开 PR）。zip 读取自足（中央目录解析＋RFC 1951 inflate·stored 与 deflate·CRC-32 校验；零第三方依赖）；ZIP64、加密件、未知压缩法、多盘、超预算（2 GiB）为结构化拒跑 rc=9。确定性：同输入同字节输出，时间戳不进逻辑（登记 schema 无时间字段）。零网络设计（全部交换走离线文件·NETRED 登记面写明 no network by design）。Standard intake gate for external return packages: `verify` compares the package zip against its md5 sidecar and md5sum-style manifest member by member with a per-file evidence list (any mismatch or missing declared member is fail-loud rc=1); `intake` re-runs the same comparison and, only on green, appends exactly one register row (schema `rocqwash-uplink/1`, six fields, duplicate-skip idempotent, `--dry-run` reports the would-append line and writes nothing); `pr-prep` renders the pull-request description draft of one register row (verified rows only, zero git calls, never opens a pull request). The zip reader is self-contained (central directory plus RFC 1951 inflate, stored and deflate members, CRC-32 checked); ZIP64, encrypted, unknown-method, multi-disk, and over-budget (2 GiB) archives are structured refusals rc=9. Deterministic byte-identical output; no clock in the logic (the register schema carries no timestamp). No network face by design (all exchange rides offline files; the NETRED register row states no network by design).
- 调用形 Invocation：`python tools/uplink.py [--selftest] {verify,intake,pr-prep} --package P.zip [--digest HEX|SIDECAR] [--manifest M.md5] --source-seat SEAT --landed-ref REF [--register PATH] [--dry-run] --out DRAFT.md [--signature LINE]`（`--register` 与 `--registry` 同槽双拼；verify 面需 `--digest` 或 `--manifest` 至少其一；intake 面另需 `--source-seat` 与 `--landed-ref`；pr-prep 面需 `--out`）
- 示例 Example：`python tools/uplink.py verify --package return.zip --manifest MANIFEST.md5`
- 依赖 Imports：argparse, hashlib, json, os, re, sys（全标准库）
- 网络 Network face：zero（三通道零命中；no network by design）
- SKIP 面：exit 0=green 终态（appended／duplicate-skip／dry-run／draft written）；1=fail-loud（失配/缺件/未验证行/selftest 矢量报错，零静默跳过）；2=用法、IO 或输入内容非法（非 zip 包、manifest 行格式坏、寄存行损坏前的拒读不属此列）；9=缺件或结构化拒跑（包/旁证/manifest 缺席、寄存行坏 JSON、ZIP64、加密、未知压缩法、多盘、超预算）；写面=intake 的登记面一件（缺省 `docs/uplink-intake.jsonl`）＋pr-prep 的 `--out` 一件，仓树其余零字节（shape 测试以全树 checksum 断言）；`--selftest` 19 矢量冻结组跑临时夹具（夹具外零写入）

### tools/vacgen.py
- 用途 Purpose：Lean vacuity 探针骨架生成器：四层形状识别（前提分解、taxonomy 查表、置信评分、分层回归），含零编译覆盖 preflight 与难度地图（`--preflight-all`）；本普查时点在岸，为 tools/ 新增件（newly added item），文件头自述 v2。Lean vacuity probe skeleton generator with a four-layer shape-recognition engine (premise decomposition, taxonomy lookup, confidence scoring, tiered harness), including a zero-compile coverage preflight and a difficulty map (`--preflight-all`); present on disk at census time and newly added to tools/, self-described as v2 in its docstring.
- 调用形 Invocation：`python tools/vacgen.py [--in] [--out] [--toolchain] [--snapshot] [--audit-id] [--name] [--worktree] [--lake] [--guard] [--core] [--force] [--taxonomy] [--preflight-all] [--census] [--root] [--cluster-table] [--report] [--exp-draft] [--verify-anchors] [--mathlib]`
- 示例 Example：`python tools/vacgen.py --in <value> --force`
- 依赖 Imports：argparse, datetime, fractions, hashlib, json, os, re, sys（全标准库；文件头自述零第三方依赖）
- 网络 Network face：zero
- SKIP 面：lean/lake/mathlib/elan 词面（64）、cpu_guard 词面（3）；骨架铸形零编译可跑，编译验证腿需 Lean 工具链（设计 SKIP 面）
- 注记 Note：落岸与路由面见 §3.3。

### tools/wash_shape.py
- 用途 Purpose：注释与形状规范化五段流水线（header 映射与预设、多轮 loop、事件流参数化）。Shape-normalizing five-stage pipeline for annotation faces (header maps and presets, multi-round loop, and event stream parameterized). 落岸注记 Integration note（引擎本体票·落岸日）：新增 wash 6 (`jargon`)（`tools/jargon_apply.py` 机改 replace 条目）与 wash 7 (`ai-flavor`)（advisory：plan 列建议、`--apply` 仅出 handoff 段包，写入经改写提供者往返），`--only` 接受 `jargon`／`ai-flavor`／`6`／`7`；`--dir` 在选中 6/7 洗时加收 .py/.sh/.md(.json/.ts) 散文面。Washes 6 (`jargon`) and 7 (`ai-flavor`, advisory) joined the pipeline; `--only` accepts the two names and `6`/`7`; `--dir` also collects the prose faces when either is selected.
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

### 3.3 vacgen 段（落岸注记） · vacgen Section (integration note)

- **落岸事实（第一手实测）**：`tools/vacgen.py` 系 2026-11-13 经 graft commit `5829f6d` 入岸（本文件版本锚即该 commit）。`git show --stat` 实测四文件：`tools/vacgen.py` 2,625 行、`docs/vacgen_sop.md` 384 行、`tests/t_vacgen_shape.py` 51 行、`更新账.md` +1 行。落岸单注记：RQW02。
- **Landing facts (first-hand measured)**: `tools/vacgen.py` landed on 2026-11-13 via graft commit `5829f6d` (the version anchor of this file). `git show --stat` measured four files: `tools/vacgen.py` 2,625 lines, `docs/vacgen_sop.md` 384 lines, `tests/t_vacgen_shape.py` 51 lines, `更新账.md` +1 line. Landing-package note: RQW02.
- **双面形态**：零编译面（骨架铸形无 Lean 环境可跑）＋编译验证腿（需 Lean 工具链，设计 SKIP 面）；三通道词面（lean/lake/mathlib/elan 64 处）与 SKIP 面照录于第 2 节 vacgen 条目。详规程 = `docs/vacgen_sop.md`；形状回归自检 = `tests/t_vacgen_shape.py`。
- **Two faces**: a zero-compile face (skeleton casting runs without a Lean environment) plus a compile-verification leg (needs a Lean toolchain, a design SKIP face); the three-channel word faces (lean/lake/mathlib/elan, 64 hits) and the SKIP face are transcribed in the §2 vacgen entry. Detailed procedure = `docs/vacgen_sop.md`; shape regression selftest = `tests/t_vacgen_shape.py`.
- **路由面（2026-11-14 复测·current state）**：cw.sh vacgen 分支已落（commit `8e04cc6` 四处齐备：头表/usage/hint_for/case；`grep -c vacgen cw.sh` = 6 实测）；CLI 调用形 `bash cw.sh vacgen ...` 与直调 `python tools/vacgen.py ...` 两形并行有效。
- **Route face (re-measured 2026-11-14, current)**: the cw.sh vacgen branch has landed (commit `8e04cc6`, all four places present: header table / usage / hint_for / case; `grep -c vacgen cw.sh` = 6 measured); both `bash cw.sh vacgen ...` and the direct `python tools/vacgen.py ...` invocation forms are valid.
- **CI 锚**：本 head 之炉 #43421710372 conclusion=success（对账回执 N3 实测，2026-11-13；同 head 前三炉连续 success）。
- **CI anchor**: the run at this head, #43421710372, concluded success (reconciliation receipt channel N3, measured 2026-11-13; the three prior runs at earlier heads were all success).

### 3.4 记录 · Provenance

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

SKIP (not probed by this agent, awaiting the later verification pass): the five network-face tools ci_triage / cw_sentinel / net_probe / pushci / contrib_intake (their runs need a network window or remote access); special-environment/heavy tools _abl1_4b_compile (usage face; a bare call triggers the compile face), _gen_fin_mac, cw_doctor, evolve, red_dispatch, registry_audit, registry_fix, registry_regen, registry_union, select_audit, toolchain_dyld_doctor, unclog, vacgen, wash_shape. The `net_probe` `--selftest` divergence (§2 note) also awaits that step.

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

Register note (2026-11-15, work stream-2 annotation closeout): the version anchor at the top advanced to `d6d0ec7` (the engine-body batch integration commit) as a construction-base annotation. The census cast stays pinned at `5829f6d`; no census re-scan ran (the census re-scan awaits the next work stream). The cycle-3 entry below is kept as written for its own time.

Cycle-3 entry, kept as written: the version anchor then at the top (5829f6d) lagged the working-tree HEAD (8e04cc6) by seven commits. Facts measured on the lagged state, per the caller duty in section 0:

- Committed tool count at HEAD is 28 `.py` files under `tools/` (`git ls-tree HEAD tools/`), one above the census count 27 recorded in section 1: `tools/mcp_server.py` was added after the census snapshot. Its contract face is reachable directly (`python -I tools/mcp_server.py --help`; the capability mapping is documented in `docs/mcp.md`). A census-grade entry awaits the census lane's own re-run; this register deliberately does not hand-write one.
- Two further tools sit on disk untracked: `tools/exp_port.py` (experience-bus port, schema rocqwash-exp/1, `append`/`query` faces plus `--selftest`) and `tools/periscope.py` (collection legs; operation manual at `docs/periscope_sop.md`). They join the index only once their own commits exist on the tracked face.
- Consequence for callers: entries in section 2 stay valid for the 27 censused tools at their recorded faces; for the three faces above, invoke from each tool's own `--help` word face and record the HEAD used, exactly as the caller duty requires.
