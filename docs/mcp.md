# rocqwash MCP stdio 服务器：协议面与安全面 · Protocol Face and Security Face (docs/mcp.md)

版本锚 Version anchor：`4be42dedcade0cc0fe4b0da83ca1c82b7d4bbc75`（钉住克隆 main，2026-11-14 本地 `git rev-parse HEAD` 实测；8 能力真名与调用形逐条照录该 HEAD 下 `docs/CAPABILITY-INDEX.md` 条目行；INDEX 文件内版本锚行记录的是其普查时点 HEAD，自指落位形见 INDEX §0 调用者义务）。
Version anchor: pinned clone main at `4be42dedcade0cc0fe4b0da83ca1c82b7d4bbc75`, measured locally on 2026-11-14 (`git rev-parse HEAD`); the 8 capability true names and call forms are transcribed line-by-line from `docs/CAPABILITY-INDEX.md` at that HEAD. The anchor line inside the INDEX records its own census-time HEAD (self-referential landing form; see the INDEX §0 caller duty).

落岸注记 Landing note：RQW08（2026-11-14）·本文件随 `work.draft/mcp_server.py` 同批落岸；协议契约源＝工单 RQW08 §〇（MCP stdio·newline-delimited JSON-RPC 2.0·python stdlib 手写三方法·零依赖律·net_probe/ci_triage/pushci_status 默认拒·凭据零接触·ROCQWASH_HOME 定装基面）。

## 1. 定位 · Positioning

本文件是 rocqwash MCP stdio 服务器（`mcp_server.py`）的使用与契约说明：协议面、8 能力 schema 表、启动法、安全面与设计 SKIP 面。任何支持 MCP stdio 的调用者（会话、子代理、自动化任务）零路径知识直调 8 能力；底层 CLI 真名与旗标面以 `docs/CAPABILITY-INDEX.md`（RQW06 契约面）为唯一权威源。

This file is the usage and contract document for the rocqwash MCP stdio server (`mcp_server.py`): the protocol face, the 8-capability schema table, startup, the security face, and the design SKIP face. Any MCP-stdio caller (a session, a subagent, an automation task) calls the 8 capabilities with zero path knowledge; the underlying CLI true names and flag faces take `docs/CAPABILITY-INDEX.md` (the RQW06 contract surface) as the single authority.

## 2. 协议面 · Protocol face

- **传输 Transport**：stdio 逐行 JSON。每行恰一个 JSON-RPC 2.0 对象，UTF-8 编码；响应逐行写 stdout 并即刷。诊断与就绪日志只走 stderr。stdin EOF 即退出（exit 0）。
- **Transport**: line-delimited JSON over stdio. Exactly one JSON-RPC 2.0 object per line, UTF-8; responses are written to stdout line by line and flushed. Diagnostics and the ready log go to stderr only. stdin EOF exits the process with code 0.

**方法表 Methods**：

| Method | Kind | Request params | Response | Notes |
|---|---|---|---|---|
| initialize | request | `protocolVersion`, `capabilities`, `clientInfo` | `protocolVersion`（回显客户端所报，缺省 `2024-11-05`）、`capabilities.tools={listChanged:false}`、`serverInfo={name:"rocqwash-mcp",version}` | 单一能力面＝tools |
| notifications/initialized | notification | none | 无响应（静默消费，stderr 留一行诊断） | JSON-RPC 通知不回包 |
| tools/list | request | none | `tools`：8 件，各带 `name`／`description`／`inputSchema`（object·闭属性集·additionalProperties:false） | 清单静态，无分页游标 |
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

8 能力按工单点名序排列；底层条目真名照录 INDEX §2；布尔参数 `true`＝附加旗标、`false`＝省略；`*`＝必填；取值旗标以 `--flag value` 传递；参数值禁止以 `-` 开头（防子 CLI 旗标注入）。

| Capability | Underlying entry (INDEX true form) | Arguments (schema properties; * = required) | Security face |
|---|---|---|---|
| sentinel_status | `tools/cw_sentinel.py --once` | watch_repo, branch, state_file, timeout, sleep_scale | default deny（网络面） |
| net_probe | `tools/net_probe.py` | endpoints, rounds, interval, stable_window, seed | default deny（网络面） |
| baselinediff | `tools/baseline_diff.py OLD NEW` | old*, new*, json_out, md_out | allow |
| ci_triage | `tools/ci_triage.py` | repo, run, logs, offline, timeout, retry_max | default deny（网络面） |
| vacgen_generate | `tools/vacgen.py` | input, out, toolchain, snapshot, audit_id, name, worktree, lake, core, force, preflight_all | allow（编译腿设计 SKIP） |
| exp_append | `tools/exp_port.py append` | tool*, points*, evidence, batch | allow（CLI 待落岸，existence probe） |
| pushci_status | `tools/pushci.py` | repo_path, branch, base_ref, dry_run, watch_interval, watch_max_rounds, timeout | default deny（网络＋远端写面） |
| capability_index | `docs/CAPABILITY-INDEX.md`（文件直读，非 CLI） | （无） | allow |

表注 Table notes：

1. **未暴露旗标面 Unexposed flags**：凭据形/注入形/测试钩形旗标有意不暴露（`--netrc`、`--injector`、`--git-caller`）；变更类旗标不暴露（`--merge`、`--pr`）；全旗标面以 INDEX 条目行调用形为准，需要全旗标面的调用者直接走 CLI。
   Credential-shaped, injection, and test-hook flags (`--netrc`, `--injector`, `--git-caller`) are deliberately not exposed; mutation flags (`--merge`, `--pr`) are not exposed; the full flag face stays with the INDEX entry lines.
2. **子进程执行形 Child execution form**：`[sys.executable, <cli>, ...]`，`cwd=ROCQWASH_HOME`，父环境原样透传；调用形与 INDEX 条目行一致（`python tools/<name>.py ...`）。
   Children spawn as `[sys.executable, <cli>, ...]` with `cwd=ROCQWASH_HOME` and the parent environment passed through; call forms match the INDEX entry lines.
3. **结果形 Result shape**：文本结果以 `exit code: <rc>` 头行回传，子进程 stderr 以 `[stderr]` 前缀并入；`rc != 0` 即 `isError:true`（fail-loud）。
   Text results carry an `exit code: <rc>` header line; child stderr is prefixed `[stderr]`; any non-zero rc yields `isError:true` (fail-loud).

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

## 6. 设计 SKIP 面 · Design SKIP face

- **exp_append**：底层 CLI `tools/exp_port.py` 随经验总线包落岸（RQW03 面）；落岸前调用返回显式 not-found 失败结果（existence probe，无 dangling route）；schema 参数面（tool/points/evidence/batch）系该包设计面，落岸后须对 CLI 实形复核。
  `tools/exp_port.py` lands with the experience-bus package; until then calls return an explicit not-found failed result (existence probe, no dangling route); the schema argument face (tool/points/evidence/batch) is that package's design face and gets re-verified against the landed CLI.
- **vacgen_generate 编译腿 vacgen compile leg**：零编译铸形面随处可跑；编译验证腿需 Lean 工具链（INDEX §3.3 设计 SKIP 面），lake 缺席时该腿保持 SKIP。
  The zero-compile casting face runs anywhere; the compile verification leg needs a Lean toolchain (design SKIP face per INDEX §3.3) and stays SKIP when lake is absent.
- **未实现 MCP 面 Unimplemented MCP faces**：resources／prompts／completions／logging／ping／batching／SSE 传输面未实现（未知方法答 `-32601`）；`tools/listChanged` 恒 false（无动态变更通知）。capabilities 只宣告 tools 一面，客户端不应假定其余面在场。
  resources/prompts/completions/logging/ping/batching and the SSE transport are not implemented (unknown methods get `-32601`); `tools/listChanged` stays false; capabilities advertise the tools face only.
- **capability_index 版本锚 capability_index anchor**：INDEX 文本现势直读，其内部版本锚行随仓推进（调用者义务照 INDEX §0）；server 不缓存不加工。
  The INDEX text is returned live from disk; its internal anchor line advances with the repo (caller duty per INDEX §0); the server neither caches nor rewrites it.

## 7. 自检 · Self-check

**握手 Handshake**：`python -I handshake.py`（RQW08 工作目录；`ROCQWASH_MCP_SERVER`／`ROCQWASH_HOME` 可覆写）。探针八发：三核心断言（initialize→capabilities.tools／tools/list→8 能力带 inputSchema／tools/call→capability_index 白名单件）＋通知静默＋default deny 负样本＋`-32601`／`-32602`／`-32700` 三错误面。全程零网络（唯一实弹调用=capability_index 本地文件读）。

实测 Measured（2026-11-14，本铸席实跑）：**21/21 PASS，exit 0**，尾行 `HANDSHAKE GREEN: all assertions passed`。负样本证据：`probe 4 net_probe default-deny: isError true` ＋ 拒答文本点名 `ROCQWASH_MCP_ALLOW_NET`。

**边探针 Edge probes**（握手之外的四面，零网络）：E1 `ROCQWASH_HOME` 未设→fail-loud 失败结果点名该 env；E2 `exp_append` 缺件→显式 not-found 失败结果；E3 `baselinediff` 真实 CLI 分发→`exit code: 9` ＋ `[stderr]` 捕获（CLI 自身 fail-loud 缺输入文件形，分发通路实证）；E4 schema 强制（缺必填/未知键→`-32602`）。实测 **7/7 PASS，exit 0**。

## 8. 语域自查 · Register self-check

器械＝`ai_flavor_selfcheck.sh`（36 词面电池＋em-dash U+2014 电池；器械副本 `D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/ai_flavor_selfcheck.sh`，与 census 同仪）。实测输出（收工时点）：

```text
mcp_server.py : CH_3FAMILIES_10FACES lines=0 / EN_WORD_STEMS_15FACES lines=0 / EN_SENTENCE_8FACES lines=0 / EN_PARA_INITIAL_3FACES lines=0 / EM_DASH_U2014 count=0 (target 0) / TOTAL_WORDING_LINES=0 / VERDICT CLEAN (36 faces = 0; em-dash = 0)  rc=0
handshake.py  : VERDICT CLEAN (36 faces = 0; em-dash = 0)  rc=0
mcp.md        : VERDICT CLEAN (36 faces = 0; em-dash = 0)  rc=0
```

凭据词面自查（值形正则两口径，grep 于三件交付物）：0 命中；`mcp_server.py:30-32` 三处词面均系本文件第 5 节第 2 条否定句 prose，非凭据值。
Credential-face check (value-shape regex passes over the three deliverables): 0 hits; the three wording hits in `mcp_server.py:30-32` are the negation prose of section 5 item 2, not credential values.
