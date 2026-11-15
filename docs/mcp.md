# rocqwash MCP stdio 服务器：协议面与安全面 · Protocol Face and Security Face (docs/mcp.md)

版本锚 Version anchor：`4be42dedcade0cc0fe4b0da83ca1c82b7d4bbc75`（钉住克隆 main，2026-11-14 本地 `git rev-parse HEAD` 实测；原 8 能力真名与调用形逐条照录该 HEAD 下 `docs/CAPABILITY-INDEX.md` 条目行）＋扩容批锚 Expansion anchor：工作树 HEAD `8e04cc6f9b6ee118e8e2729e9ae3edd6a163bf79`（2026-11-14 本地 `git rev-parse HEAD` 实测；扩容 13 能力真名与调用形逐条照录该 HEAD 下 INDEX §2 条目行；该 HEAD 尚未含本扩容批自身的 commit，自指落位形照旧）。INDEX 文件内版本锚行记录的是其普查时点 HEAD，自指落位形见 INDEX §0 调用者义务。
Version anchor: pinned clone main at `4be42dedcade0cc0fe4b0da83ca1c82b7d4bbc75`, measured locally on 2026-11-14 (`git rev-parse HEAD`); the original 8 capability true names and call forms are transcribed line-by-line from `docs/CAPABILITY-INDEX.md` at that HEAD. Expansion anchor: working-tree HEAD `8e04cc6f9b6ee118e8e2729e9ae3edd6a163bf79` (measured locally on 2026-11-14); the 13 expansion capability true names and call forms are transcribed line-by-line from the INDEX section 2 entries at that HEAD, which does not yet contain this expansion batch's own commit (the self-referential landing form applies as before). The anchor line inside the INDEX records its own census-time HEAD (self-referential landing form; see the INDEX §0 caller duty).

落岸注记 Landing note：RQW08（2026-11-14）·本文件随 `work.draft/mcp_server.py` 同批落岸；协议契约源＝工单 RQW08 §〇（MCP stdio·newline-delimited JSON-RPC 2.0·python stdlib 手写三方法·零依赖律·net_probe/ci_triage/pushci_status 默认拒·凭据零接触·ROCQWASH_HOME 定装基面）。

## 1. 定位 · Positioning

本文件是 rocqwash MCP stdio 服务器（`mcp_server.py`）的使用与契约说明：协议面、24 能力 schema 表、启动法、安全面与设计 SKIP 面。任何支持 MCP stdio 的调用者（会话、子代理、自动化任务）零路径知识直调 24 能力；底层 CLI 真名与旗标面以 `docs/CAPABILITY-INDEX.md`（RQW06 契约面）为唯一权威源。

This file is the usage and contract document for the rocqwash MCP stdio server (`mcp_server.py`): the protocol face, the 24-capability schema table, startup, the security face, and the design SKIP face. Any MCP-stdio caller (a session, a subagent, an automation task) calls the 24 capabilities with zero path knowledge; the underlying CLI true names and flag faces take `docs/CAPABILITY-INDEX.md` (the RQW06 contract surface) as the single authority.

**扩容注记 Expansion note（RQW13 batch 1，2026-11-14）**：原 8 能力（RQW08 落岸）之外，本批新增 13 件零网络能力，逐件照 INDEX §2 条目行转写；`baseline_diff` 已以 `baselinediff` 名在册，不重复注册。扩容批走追加式（既有 8 件 spec 与其 schema 零改动；仅服务端新增 array 参数型与逐项 `-` 前缀校验，既有调用形不变）。**引擎本体批注记 Engine-body batch note（引擎本体票·落岸日）**：本批再加 3 件零网络能力（ai_flavor_detect／jargon_plan／i18n_pipeline_dryrun），逐件从 `docs/drafts/mcp-tool-specs-engine-body.md`（道8 稿）在合流环节转正入 `TOOL_SPECS`；追加式同律（既有 21 件 spec 与其 schema 零改动）；全票唯一网络面（i18n http 提供者腿）不在批内，不注册不加闸，保持 default-deny。
The engine-body batch (the engine-body ticket, at integration) adds 3 further zero-network capabilities (ai_flavor_detect / jargon_plan / i18n_pipeline_dryrun), graduated from docs/drafts/mcp-tool-specs-engine-body.md (the lane-8 draft) by the integration agent; additive again (the 21 existing specs and schemas untouched); the ticket's only network face (the i18n http provider leg) is outside the batch and stays default-deny, neither registered nor gated.
Beyond the original 8 capabilities (the RQW08 landing), this batch adds 13 zero-network capabilities, each transcribed from its INDEX section 2 entry line; `baseline_diff` was already on this face under the name `baselinediff` and is not registered twice. The expansion is additive: the 8 existing specs and their schemas are untouched; the server only gains the array argument type and per-item `-` prefix validation, leaving existing call forms unchanged.

## 2. 协议面 · Protocol face

- **传输 Transport**：stdio 逐行 JSON。每行恰一个 JSON-RPC 2.0 对象，UTF-8 编码；响应逐行写 stdout 并即刷。诊断与就绪日志只走 stderr。stdin EOF 即退出（exit 0）。
- **Transport**: line-delimited JSON over stdio. Exactly one JSON-RPC 2.0 object per line, UTF-8; responses are written to stdout line by line and flushed. Diagnostics and the ready log go to stderr only. stdin EOF exits the process with code 0.

**方法表 Methods**：

| Method | Kind | Request params | Response | Notes |
|---|---|---|---|---|
| initialize | request | `protocolVersion`, `capabilities`, `clientInfo` | `protocolVersion`（回显客户端所报，缺省 `2024-11-05`）、`capabilities.tools={listChanged:false}`、`serverInfo={name:"rocqwash-mcp",version}` | 单一能力面＝tools |
| notifications/initialized | notification | none | 无响应（静默消费，stderr 留一行诊断） | JSON-RPC 通知不回包 |
| tools/list | request | none | `tools`：24 件，各带 `name`／`description`／`inputSchema`（object·闭属性集·additionalProperties:false） | 清单静态，无分页游标 |
| tools/call | request | `name`, `arguments` | `content[0].text` ＋ `isError` | 执行层失败走 `isError:true` 结果，非协议错误 |

**错误码表 Error codes**：

| Code | Meaning | Raised when |
|---|---|---|
| -32700 | Parse error | 行非合法 JSON 或非合法 UTF-8（id=null，循环继续不退） |
| -32600 | Invalid request | 行非对象、缺 `method` 或 `method` 非字符串 |
| -32601 | Method not found | 三方法之外的任何请求方法 |
| -32602 | Invalid params | 未知工具、`params.name` 形坏、schema 校验失（缺必填/类型错/未知键/值以 `-` 开头） |
| -32603 | Internal error | 服务端意外异常（stderr 留痕，循环继续） |

- **stdout 纪律 Stream discipline**：stdout 只写协议响应行；子进程 stdout/stderr 一律捕获（`subprocess.PIPE`），绝不并入协议流。空行静默跳过；坏行答 `-32700` 后继续服务。
- **Stream discipline**: stdout carries protocol response lines only; child stdout/stderr are captured and never merged into the protocol stream. Empty lines are skipped; a malformed line gets `-32700` and the loop keeps serving.

## 3. 工具 schema 表 · Tool schema table

原 8 能力按 RQW08 工单点名序排列；RQW13 扩容批 13 件按扩容工单点名序追加于表尾；引擎本体票 引擎本体批 3 件追加于表尾末（道8 稿转正·合流环节接线）。底层条目真名照录 INDEX §2；布尔参数 `true`＝附加旗标、`false`＝省略；`*`＝必填；取值旗标以 `--flag value` 传递；array 参数逐元素展开（位置型按序接续＝argparse `nargs="*"` 面；旗标型逐元素重复 `--flag value`＝argparse `action="append"` 面）；参数值禁止以 `-` 开头（防子 CLI 旗标注入，array 逐元素同查）。

| Capability | Underlying entry (INDEX true form) | Arguments (schema properties; * = required) | Security face |
|---|---|---|---|
| sentinel_status | `tools/cw_sentinel.py --once` | watch_repo, branch, state_file, timeout, sleep_scale | default deny（网络面） |
| net_probe | `tools/net_probe.py` | endpoints, rounds, interval, stable_window, seed | default deny（网络面） |
| baselinediff | `tools/baseline_diff.py OLD NEW` | old*, new*, json_out, md_out | allow |
| ci_triage | `tools/ci_triage.py` | repo, run, logs, offline, timeout, retry_max | default deny（网络面） |
| vacgen_generate | `tools/vacgen.py` | input, out, toolchain, snapshot, audit_id, name, worktree, lake, core, force, preflight_all | allow（编译腿设计 SKIP） |
| exp_append | `tools/exp_port.py append` | tool*, points*, evidence, batch | allow（CLI 在卷·幂等 seen 集） |
| pushci_status | `tools/pushci.py` | repo_path, branch, base_ref, dry_run, watch_interval, watch_max_rounds, timeout | default deny（网络＋远端写面） |
| capability_index | `docs/CAPABILITY-INDEX.md`（文件直读，非 CLI） | （无） | allow |
| chain_graph | `tools/chain_graph.py LEDGERS...` | ledgers*（array·位置型）, json_out, md_out, top | allow |
| doc_lint | `tools/doc_lint.py` | repo, json_out, help_cap | allow（help 实跑只读） |
| ledger_sync | `tools/ledger_sync.py` | probe, ledger, out, report, policy | allow |
| netname_normalize | `tools/netname_normalize.py` | dir, apply, map, json_out | allow（apply＝本地改名写面·限 --dir 内） |
| norm_lint | `tools/norm_lint.py` | tree, file, jargon_map, cjk_threshold, cjk_whitelist, json_out, md_out, selftest | allow（报告态先行） |
| render_events | `tools/render_events.py` | events, dir, md_out, json_out, top | allow |
| select_audit | `tools/select_audit.py` | order, select*（array·重复旗标面）, grep, requires, world, json_out | allow |
| registry_audit | `tools/registry_audit.py` | order, project, git, ref, git_path_order, git_path_project, live_src, anchor_src, fix_plan, json_out, md_out | allow（本地 git 只读） |
| registry_fix | `tools/registry_fix.py` | audit_json, order, project, anchor_src, apply, work_dir, audit_tool, json_out | allow（缺省干跑·apply 受 staged 断言＋回滚约束） |
| registry_regen | `tools/registry_regen.py` | base_repo, base_ref, contrib_repo, contrib_ref, pieces, anchor_src, dep_source, seq, base_path_order, base_path_project, contrib_path_order, contrib_path_project, out, apply, json_out | allow（缺省干跑·apply 须显式 out） |
| registry_union | `tools/registry_union.py` | base, main, branch, git, ref_base, ref_main, ref_branch, git_path, kind, reanchor, anchor_src, out, apply, json_out | allow（缺省干跑） |
| abl1_4b_compile | `tools/_abl1_4b_compile.py EXTRACT_DIR [DRIVER.ML]` | extract_dir*（位置型）, driver（位置型） | allow（OCaml 工具链设计 SKIP 面） |
| http_backoff | `tools/_http_backoff.py --selftest` | （无） | allow（纯函数自检面） |
| ai_flavor_detect | `tools/ai_flavor.py` | file, tree, json_out, selftest | allow（零网络·报告态零写） |
| jargon_plan | `tools/jargon_apply.py --plan` | file, tree, json_out | allow（plan 缺省零写·apply 面不暴露） |
| i18n_pipeline_dryrun | `tools/i18n_pipeline.py --stage p0\|p1` | manifest*, stage, json_out | allow（stage 限 p0/p1 干跑面·p3/p6 写面不暴露） |

表注 Table notes：

1. **未暴露旗标面 Unexposed flags**：凭据形/注入形/测试钩形旗标有意不暴露（`--netrc`、`--injector`、`--git-caller`）；远端变更类旗标不暴露（`--merge`、`--pr`）；全旗标面以 INDEX 条目行调用形为准，需要全旗标面的调用者直接走 CLI。扩容批同律：`registry_fix` 的 opt-in `--orphan-add` 面不暴露（该旗标不在本批转写时点的 INDEX 条目行上，registry_fix 条目 Pos/Opt=0/8 与此一致）；`chain_graph` 的 argparse 前手工分发 `--selftest` 面不暴露（同理不在条目行上；此分歧与 INDEX 已登记的 `net_probe` `--selftest` 分歧同形，属 doc-vs-argparse 分歧账）。
   Credential-shaped, injection, and test-hook flags (`--netrc`, `--injector`, `--git-caller`) are deliberately not exposed; remote mutation flags (`--merge`, `--pr`) are not exposed; the full flag face stays with the INDEX entry lines. Same law for the expansion batch: the opt-in `--orphan-add` face of `registry_fix` is not exposed (absent from the INDEX entry line transcribed at expansion time; the entry's Pos/Opt of 0/8 agrees), and the pre-argparse `--selftest` dispatch of `chain_graph` is not exposed for the same reason (a doc-versus-argparse divergence of the same shape as the registered `net_probe` `--selftest` divergence).
2. **本地写面 Local write faces**：扩容批三件带本地写旗标（`netname_normalize --apply`、`registry_fix --apply`、`registry_regen --apply`、`registry_union --apply`），全部缺省干跑、写面限 CLI 自身断言约束内（registry_fix 带 staged 内存断言＋回滚；registry_regen 写面限显式 `--out`）；均不设闸（零网络面，INDEX §1 判读），调用者义务随 CLI 本体。
   Four expansion capabilities carry local write flags (`netname_normalize --apply`, `registry_fix --apply`, `registry_regen --apply`, `registry_union --apply`); all dry run by default and their write faces stay inside the CLI's own assertion machinery (registry_fix applies staged in-memory assertions with rollback; registry_regen writes only under an explicit out). None is gated: zero network face per the INDEX section 1 reading, caller duty rides with the underlying CLI.
3. **子进程执行形 Child execution form**：`[sys.executable, <cli>, ...]`，`cwd=ROCQWASH_HOME`，父环境原样透传；调用形与 INDEX 条目行一致（`python tools/<name>.py ...`）。
   Children spawn as `[sys.executable, <cli>, ...]` with `cwd=ROCQWASH_HOME` and the parent environment passed through; call forms match the INDEX entry lines.
4. **结果形 Result shape**：文本结果以 `exit code: <rc>` 头行回传，子进程 stderr 以 `[stderr]` 前缀并入；`rc != 0` 即 `isError:true`（fail-loud）。
   Text results carry an `exit code: <rc>` header line; child stderr is prefixed `[stderr]`; any non-zero rc yields `isError:true` (fail-loud).
5. **二批候登记 Batch-2 register（候令·未注册）**：27 件 INDEX 条目中，原 8 能力覆盖 6 件真名（`cw_sentinel`/`net_probe`/`baseline_diff`/`ci_triage`/`vacgen`/`pushci`），本批 13 件再覆盖 13 件真名；未注册余 8 件真名＝`_gen_fin_mac`／`contrib_intake`／`cw_doctor`／`evolve`／`red_dispatch`／`toolchain_dyld_doctor`／`unclog`／`wash_shape`。勘形卷「网络重活五件候二批」按 INDEX 面判读为五件候二批＝`contrib_intake`（词面 git clone）／`unclog`（Coq 编译清理循环重活）／`wash_shape`（多轮改形流水线）／`evolve`（仓内 git 提交面）／`cw_doctor`（多域 rollup 检验）；余三件（`red_dispatch`／`toolchain_dyld_doctor`／`_gen_fin_mac`）不在工单点名五件内，候各自车道裁定。五件组成为本席按 INDEX 网络面/重活面判读，工单原文未点名，二批注册时以届时工单为准。
   Of the 27 INDEX entries, the original 8 plus this batch's 13 are registered and `baseline_diff` is covered by `baselinediff`; 8 true names remain unregistered. The ticket's "five network-or-heavy candidates await batch 2" reads, from the INDEX faces, as `contrib_intake` (git clone word face) / `unclog` (Coq compile clearing loops, heavy) / `wash_shape` (multi-round reshaping pipeline) / `evolve` (in-repo git commit face) / `cw_doctor` (multi-domain rollup probes); the other three (`red_dispatch`, `toolchain_dyld_doctor`, `_gen_fin_mac`) are outside the ticket's five and await their own lane decision. The five-name composition is this seat's INDEX-face reading; the ticket does not name them, and the batch-2 ticket governs at registration time.

## 4. 启动法 · Startup

**命令 Command**：`python -I mcp_server.py`（stdio 传输；隔离模式）。

**环境变量表 Env table**：

| Variable | Meaning | Default |
|---|---|---|
| ROCQWASH_HOME | rocqwash 仓库根；tools/call 必需，未设时 fail-loud 报缺（禁静默猜测） | 无（不猜路径） |
| ROCQWASH_MCP_ALLOW_NET | 设为 `1` 才放行 default deny 四能力 | 未设＝拒 |
| ROCQWASH_MCP_TIMEOUT | 单次工具调用硬超时（秒），超时杀子进程并报失败结果 | 300 |

实测环境 Measured environment：Python 3.13.2（Windows 10·Git Bash）；更低版本未测。

**最小会话例 Minimal session example**（三行请求、两行响应；通知不回包）：

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"demo"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"capability_index","arguments":{}}}
```

## 5. 安全面 · Security face

1. **默认拒 Default deny**：`net_probe`／`ci_triage`／`pushci_status`（工单点名三件）＋ `sentinel_status`（本铸加严件）默认拒；调用返回 `isError:true` 失败结果并点名 `ROCQWASH_MCP_ALLOW_NET=1`，是执行层结果非协议错误；唯显式设 `ROCQWASH_MCP_ALLOW_NET=1` 才放行。
   Default deny: `net_probe` / `ci_triage` / `pushci_status` (the three the landing ticket names) plus `sentinel_status` (a strengthening cast by this landing) return a failed tool result (`isError:true`) naming `ROCQWASH_MCP_ALLOW_NET=1`; a denial is an execution-level result, not a protocol error; only the explicit environment opt-in enables them.
   **登记注 Registration note（超出工单最小清单的加严，additive）**：工单点名三件；本铸将 `sentinel_status` 一并纳入闸面，证据＝INDEX §1 总表 `cw_sentinel.py` 词面 Network face＝非零（http.client, socket, urllib.request）＋§2 SKIP 面「运行需网络窗」。加严不弱化：若判读裁「恰按工单三件」，去闸面一行即回（`TOOL_SPECS` 中 `sentinel_status` 的 `net_gated` 置 `False`）。The ticket names three; this landing also gates `sentinel_status` because INDEX §1 records a non-zero network word face for `tools/cw_sentinel.py` (http.client, socket, urllib.request) and its SKIP face requires a network window. Strengthening, not weakening; reverting to the verbatim three-name face is a one-line change.
2. **凭据零接触 Credential zero contact**：server 不读 credential store、不读 token 文件、不读 netrc 路径、不暴露凭据形参数；子进程环境原样透传，凭据处理权留在底层 CLI 自身（如其 `--netrc` 旗标）。server 源内凭据词面仅安全面否定句（`mcp_server.py:30-32`），凭据值形 grep＝0。
   The server reads no credential store, no token file, no netrc path, and exposes no credential-shaped argument; the child environment passes through unchanged and credential handling stays with the underlying CLIs. The only credential wording in the server source is the negation statement of this very face (`mcp_server.py:30-32`); the credential value-shape grep is 0 hits.
3. **子进程隔离 Subprocess isolation**：子进程 stdout/stderr 捕获，协议流零污染；`cwd=ROCQWASH_HOME`；硬超时杀 runaway 子进程；参数以 argv 列表传递（无 shell，无拼接注入面），字符串值禁 `-` 开头。
   Child streams are captured; the protocol stream stays clean; the child runs with `cwd=ROCQWASH_HOME`; a hard timeout kills runaway children; arguments pass as an argv list (no shell, no string-concatenation injection face) and string values must not start with `-`.
4. **零传输 import 面 Zero transport import face**：server 自身仅 import `json`／`os`／`subprocess`／`sys`；无 socket／urllib／http 面，server 本体零网络。
   The server itself imports `json`, `os`, `subprocess`, `sys` only; no socket/urllib/http face; the server body is zero-network.
5. **扩容批零新闸面 Expansion batch adds no gated face**：13 件扩容能力按 INDEX §1 词面判读全零网络（三通道零命中，或仅本地 git 只读面），不设 `ROCQWASH_MCP_ALLOW_NET` 闸；其本地写面由 CLI 自身缺省干跑与断言/回滚机制约束（§3 表注 2）。服务端硬超时与「参数值禁 `-` 前缀」校验（array 逐元素同查）对全部 24 能力一视同仁（引擎本体批三件同律：零网络不设闸）。
   The 13 expansion capabilities all read zero-network under the INDEX section 1 word-face reading (three-channel zero hits, or local git reads only) and carry no `ROCQWASH_MCP_ALLOW_NET` gate; their local write faces stay inside the underlying CLIs' dry-run defaults and assertion/rollback machinery (section 3 table note 2). The server hard timeout and the no-leading-dash argument validation (array items checked the same way) apply to all 24 capabilities equally (the engine-body three follow the same law: zero network, no gate).

## 6. 设计 SKIP 面 · Design SKIP face

- **exp_append**：底层 CLI `tools/exp_port.py` 已落岸（经验总线 A1 面，schema rocqwash-exp/1：tool/points/evidence/batch 四字段，JSONL append 到 `docs/exp-ledger.jsonl`，幂等 seen 集：重复条目返回既有 id 且零写入）；落岸前的 not-found existence-probe 形态退役。注册参数面与 CLI 实形已复核一致。
  `tools/exp_port.py` is in place (the experience-bus A1 face, schema rocqwash-exp/1: the tool/points/evidence/batch four-field face, JSONL append into `docs/exp-ledger.jsonl`, idempotent seen set: a duplicate returns the existing id and writes nothing); the pre-integration not-found existence-probe form is retired. The registered argument face was re-verified against the integrated CLI.
- **vacgen_generate 编译腿 vacgen compile leg**：零编译铸形面随处可跑；编译验证腿需 Lean 工具链（INDEX §3.3 设计 SKIP 面），lake 缺席时该腿保持 SKIP。
  The zero-compile casting face runs anywhere; the compile verification leg needs a Lean toolchain (design SKIP face per INDEX §3.3) and stays SKIP when lake is absent.
- **未实现 MCP 面 Unimplemented MCP faces**：resources／prompts／completions／logging／ping／batching／SSE 传输面未实现（未知方法答 `-32601`）；`tools/listChanged` 恒 false（无动态变更通知）。capabilities 只宣告 tools 一面，客户端不应假定其余面在场。
  resources/prompts/completions/logging/ping/batching and the SSE transport are not implemented (unknown methods get `-32601`); `tools/listChanged` stays false; capabilities advertise the tools face only.
- **capability_index 版本锚 capability_index anchor**：INDEX 文本现势直读，其内部版本锚行随仓推进（调用者义务照 INDEX §0）；server 不缓存不加工。
  The INDEX text is returned live from disk; its internal anchor line advances with the repo (caller duty per INDEX §0); the server neither caches nor rewrites it.
- **abl1_4b_compile 工具链腿 abl1_4b_compile toolchain leg**：注册面零网络可清单化，编译本体需 OCaml 工具链；`ocamlc`/`ocamldep` 缺席时 CLI fail-loud 退出（INDEX 条目 SKIP 面），MCP 调用表现为 `exit code` 非零＋`isError:true` 执行层失败结果，非协议错误。
  The registration face lists with zero network, but the compile body needs an OCaml toolchain; with `ocamlc`/`ocamldep` absent the CLI exits loudly (INDEX entry SKIP face), surfacing over MCP as a non-zero `exit code` with `isError:true`, an execution-level result, not a protocol error.
- **registry 族面向 serviced books The registry family targets serviced books**：`registry_audit`／`registry_fix`／`registry_regen`／`registry_union` 面向带 `order.txt`/`_CoqProject` 的注册册书仓；在无注册册的仓（如本仓）上 `registry_audit` 实测 rc=9 REGISTERED fail-loud（INDEX §4.1 轻探账在卷），属执行层失败结果，非工具病。
  The registry family targets book repositories carrying `order.txt`/`_CoqProject`; on a repository without a registry (this repo), `registry_audit` measured rc=9 REGISTERED fail-loud (INDEX section 4.1 light-probe ledger), an execution-level result, not a tool fault.
- **http_backoff 单面暴露 Single-face exposure**：该件无 argparse（usage 字符串还原面）；MCP 仅暴露 `--selftest` 一发，其余面为模块 import（ci_triage/cw_sentinel/pushci 三件消费），不经 MCP。
  The tool has no argparse (usage-string face); MCP exposes the single `--selftest` call; its other face is module import (consumed by ci_triage, cw_sentinel and pushci) and does not go through MCP.

## 7. 自检 · Self-check

**现役自检器 Active self-check**：`python -I -B tests/t_mcp_face.py`（仓内 tests/ 面；RQW13 扩容批落岸）。子进程拉起 `tools/mcp_server.py`（stdio），单会话逐行断言：①initialize→protocolVersion 回显＋serverInfo；②notifications/initialized 静默无回包；③tools/list 恰 24 件、名单逐字对表（原 8＋扩容 13＋引擎本体批 3）、各带 description＋闭属性 inputSchema；④真调抽验 ≥3 件（http_backoff `--selftest` rc=0／norm_lint `--selftest` rc=0／chain_graph `--selftest` rc=0＋chain_graph 临时夹具双账 array 位置型通路 rc=0）；⑤default deny 负样本（net_probe 拒答，isError:true 点名 `ROCQWASH_MCP_ALLOW_NET`）；⑥`-32601`／`-32602`（未知工具＋新件未知参数＋array 负项拒绝）／`-32700` 三错误面。全程零网络（真调仅 selftest 面与临时夹具）。

roster 注记 Roster note：本例**不挂 `tests/run_tests.sh` roster**（照 A1 席 `tests/t_exp_port.py` 先例：roster 计数与 README.md 计数线机械耦合，README* 为本席零触碰面；roster 插入权属持 README 授权的车道）。独立直跑即完整自检。

**RQW08 期握手器（存照）Legacy handshake of record**：`python -I handshake.py`（RQW08 工作目录 `_rqw08_mcp_20261114/`；探针三发断言 tools/list 恰 8 件）：扩容批后其 probe 3 按预期转红（8 件面已被 21 件面取代），余探针保持绿；该器留存为 RQW08 落岸时点存照，现役自检以上段 t_mcp_face 为准。实测见下。

实测 Measured（2026-11-14，本席实跑）：

```text
python -I -B tests/t_mcp_face.py   -> T-MCP-FACE SUITE SHELL PASS (6 probe groups, 24 capabilities, 3 live-call spot checks)  exit 0
python -I handshake.py (RQW08 ws)  -> HANDSHAKE RED: 2 failed assertions（probe 2「exactly 8 tools :: got 21」＋「names match the 8-capability contract :: missing=[] extra=<恰 13 新件名>」）；其余探针（inputSchema 面/capability_index/default deny/-32601/-32602/-32700）全 PASS；exit 1
```

（实测时点 2026-11-14，本席实跑；旧器两红＝扩容后预期失配形，非病。）

## 8. 语域自查 · Register self-check

器械＝`ai_flavor_selfcheck.sh`（36 词面电池＋em-dash U+2014 电池；器械副本 `D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/ai_flavor_selfcheck.sh`，与 census 同仪）。实测输出（收工时点）：

```text
mcp_server.py   : CH_3FAMILIES_10FACES lines=0 / EN_WORD_STEMS_15FACES lines=0 / EN_SENTENCE_8FACES lines=0 / EN_PARA_INITIAL_3FACES lines=0 / EM_DASH_U2014 count=0 (target 0) / TOTAL_WORDING_LINES=0 / VERDICT CLEAN (36 faces = 0; em-dash = 0)  rc=0
docs/mcp.md     : VERDICT CLEAN (36 faces = 0; em-dash = 0)  rc=0
t_mcp_face.py   : VERDICT CLEAN (36 faces = 0; em-dash = 0)  rc=0
```

凭据词面自查（值形正则 grep 于三件交付物）：0 命中；`mcp_server.py:34-36` 三处词面均系 §5 第 2 条否定句 prose，非凭据值。
Credential-face check (value-shape regex pass over the three deliverables): 0 hits; the wording in `mcp_server.py:34-36` is the negation prose of section 5 item 2, not credential values.

**em-dash 清偿注记 Em-dash settlement note**：扩容前工作树 mcp.md §6 exp_append 行携两处 U+2014（A1 未落件所留）；本批连同本席新增段共五处一并清偿（「——」改冒号/逗号，语义零变），复测三件 em-dash=0。
Before the expansion, the working-tree mcp.md section 6 exp_append lines carried two U+2014 hits left by the uncommitted A1 landing; this batch settled those together with the seats' own additions (five in total, replaced by colon or comma, zero semantic change) and the re-measured count is zero on all three deliverables.

## 9. 现形注记 · Reconnect note（RQW13 扩容批·用户重连面）

**现状 Current**：用户级 MCP config（`~/.zcode/cli/config.json` → `mcp/servers/rocqwash`）拉起形＝`python.exe -I D:/ComplexAnalysis/rocqwash/tools/mcp_server.py`，env＝`ROCQWASH_HOME=D:/ComplexAnalysis/rocqwash`＋`ROCQWASH_MCP_ALLOW_NET=1`；服务器直指本仓活树。重连前客户端现形 **8 件**（sentinel_status/net_probe/baselinediff/ci_triage/vacgen_generate/exp_append/pushci_status/capability_index）。

**重连后 After reconnect**：客户端重启该 stdio 服务器并重连后，`tools/list` 现形 **24 件**（RQW13 批 13 件名单照 §3 表；引擎本体票再加 3 件：ai_flavor_detect／jargon_plan／i18n_pipeline_dryrun，合流落岸）。未重启的既有连接保持 8 件旧面（清单静态，`listChanged:false`，无动态变更通知）。验收锚＝勘形卷 §五「重启重连后 MCP 工具数 ≥ 新增批件数」＋「握手＋一次真调 per 新件抽验」。

Current: the user-level MCP config (`mcp/servers/rocqwash`) spawns `python.exe -I D:/ComplexAnalysis/rocqwash/tools/mcp_server.py` with `ROCQWASH_HOME` and `ROCQWASH_MCP_ALLOW_NET=1`; the server runs against this live tree, and a connected client currently sees 8 tools. After the client restarts this stdio server and reconnects, `tools/list` shows 24 tools (the RQW13 batch's 13 names per the section 3 table plus the engine-body ticket's ai_flavor_detect / jargon_plan / i18n_pipeline_dryrun, landed at integration). An existing connection that is not restarted keeps the 8-tool face (the listing is static, `listChanged:false`, no change notifications). Acceptance anchors: the expansion ticket's "after restart and reconnect the MCP tool count covers the new batch" plus "handshake and one live call per new tool, spot checked".
