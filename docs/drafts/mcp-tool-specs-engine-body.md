# MCP TOOL_SPECS Registration Draft: Engine Body Batch · 引擎本体批 MCP 注册稿（道8 稿 · wiring belongs to the integration agent）

落岸注记 Integration note：引擎本体票（ENGMAX） 第 8 道交付的**稿件**（draft only, zero wiring）。本文件按 `tools/mcp_server.py` 的 `TOOL_SPECS` 实形（`name`/`kind`/`cli`/`net_gated`/`fixed_args`/`arg_map`/`schema`/`description`，schema＝闭属性集 `additionalProperties:false`），预先铸三候选注册条目；接线（写进 `tools/mcp_server.py`）与计数面同步归合流席（契约卷 §5：道8 稿转正·tools/list 21→24 计数面同步 README 计数）。
Integration note: the lane 8 draft deliverable of work order the engine-body ticket (draft only, zero wiring). This file pre-casts three candidate registration entries in the exact `TOOL_SPECS` shape of `tools/mcp_server.py` (`name`/`kind`/`cli`/`net_gated`/`fixed_args`/`arg_map`/`schema`/`description`, schema = closed property set with `additionalProperties:false`). Wiring (writing them into `tools/mcp_server.py`) and the counting-face sync belong to the integration agent (contract volume section 5: this draft graduates into TOOL_SPECS, tools/list 21 to 24, README count lines synced).

版本锚 Version anchor：快照 HEAD `523e7d4`（落岸日解包副本）；`TOOL_SPECS` 实形读自该快照 `tools/mcp_server.py:83`（表头）与 `:825`（argv 映射）、`:799`（参数校验）；21 能力计数读自 `docs/mcp.md` §1/§3（原 8 ＋ RQW13 扩容批 13）并以本席 grep 实点数（21）复核。
Version anchor: snapshot HEAD `523e7d4` (unpack copy, 落岸日); the `TOOL_SPECS` shape is read from that snapshot's `tools/mcp_server.py:83` (table head), `:825` (argv mapping), and `:891` (argument validation); the 21-capability count is read from `docs/mcp.md` sections 1 and 3 (original 8 plus the 13 of RQW13 batch 1).

## 1. 定位 · Positioning

三候选照契约卷 §2 道8 点名：**ai_flavor 检测／jargon plan／i18n pipeline dry-run**。命名循 `vacgen_generate`／`pushci_status`／`sentinel_status` 先例（工具名＋面名编码，snake_case）；dry-run 候选用专名（见 §8 注 7），使未来整面 `i18n_pipeline` 注册仍走追加式（既有 spec 零改动，照 `docs/mcp.md` §1 扩容注记纪律）。
Three candidates per contract volume section 2 lane 8: the ai_flavor detection face, the jargon plan face, and the i18n pipeline dry-run face. Names follow the `vacgen_generate` / `pushci_status` / `sentinel_status` precedent (tool plus face encoded, snake_case); the dry-run candidate takes a dedicated name (see section 8 note 7), so a future full-face `i18n_pipeline` registration stays additive (existing specs untouched, per the expansion-note discipline of `docs/mcp.md` section 1).

## 2. docs/mcp.md §3 表行（Table rows for the capability table）

| Capability | Underlying entry (INDEX true form) | Arguments (schema properties; * = required) | Security face |
|---|---|---|---|
| ai_flavor_detect | `tools/ai_flavor.py` | file, tree, json_out, selftest | allow（零网络·报告态零写） |
| jargon_plan | `tools/jargon_apply.py --plan` | file, tree, json_out | allow（plan 缺省零写·apply 面不暴露） |
| i18n_pipeline_dryrun | `tools/i18n_pipeline.py --stage p0\|p1` | manifest*, stage, json_out | allow（stage 限 p0/p1 干跑面·p3/p6 写面不暴露） |

三候选全部 `net_gated:false`（§4 判读）；全票唯一网络面（i18n http 提供者腿）不在本批注册面内。
All three candidates carry `net_gated:false` (section 4 reading); the ticket's only network face (the i18n http provider leg) is outside this registration batch.

## 3. TOOL_SPECS 字面（Python literals, exact server shape）

```python
# ---- the engine-body ticket lane 8 draft: engine body batch (3 candidates,
# appended after the RQW13 batch 1 block; names and schemas per
# docs/drafts/mcp-tool-specs-engine-body.md; zero-network faces only).
{
    "name": "ai_flavor_detect",
    "kind": "cli",
    "cli": os.path.join("tools", "ai_flavor.py"),
    "net_gated": False,
    "fixed_args": [],
    "arg_map": (
        ("file", "--file"),
        ("tree", "--tree"),
        ("json_out", "--json"),
        ("selftest", "--selftest"),
    ),
    "schema": _object_schema(
        {
            "file": {"type": "string", "description": "target file to scan; CLI flag --file"},
            "tree": {"type": "string", "description": "target directory to scan (*.py *.sh *.md *.json *.ts); CLI flag --tree"},
            "json_out": {"type": "string", "description": "write the rocqwash.ai-flavor.report/1 report to this path; CLI flag --json"},
            "selftest": {"type": "boolean", "description": "run the clean and polluted probe pair; bare CLI flag --selftest"},
        }
    ),
    "description": (
        "Run the 36-face AI-flavor wording battery plus the em-dash battery over a file "
        "or a directory tree (tools/ai_flavor.py, schema rocqwash.ai-flavor.report/1). "
        "Zero network face, zero writes, report-first. Exit codes: 0 clean, 1 hits "
        "(findings are data, not errors), 2 usage."
    ),
},
{
    "name": "jargon_plan",
    "kind": "cli",
    "cli": os.path.join("tools", "jargon_apply.py"),
    "net_gated": False,
    "fixed_args": ["--plan"],
    "arg_map": (
        ("file", "--file"),
        ("tree", "--tree"),
        ("json_out", "--json"),
    ),
    "schema": _object_schema(
        {
            "file": {"type": "string", "description": "target file to plan; CLI flag --file"},
            "tree": {"type": "string", "description": "target directory to plan; CLI flag --tree"},
            "json_out": {"type": "string", "description": "write the zero-write plan report (before/after pairs) to this path; CLI flag --json"},
        }
    ),
    "description": (
        "Plan jargon-to-standard rewrites over a file or a tree with zero writes "
        "(tools/jargon_apply.py --plan; before/after pairs from the 62-entry map "
        "seeds/jargon/jargon-map.json). Zero network face. The apply face is not "
        "exposed over MCP; callers carrying write duty use the CLI directly, where "
        "plan also stays the default."
    ),
},
{
    "name": "i18n_pipeline_dryrun",
    "kind": "cli",
    "cli": os.path.join("tools", "i18n_pipeline.py"),
    "net_gated": False,
    "fixed_args": [],
    "arg_map": (
        ("manifest", "--manifest"),
        ("stage", "--stage"),
        ("json_out", "--json"),
    ),
    "schema": _object_schema(
        {
            "manifest": {"type": "string", "description": "run manifest path (i18n SPEC section 9 run manifest shape); CLI flag --manifest"},
            "stage": {"type": "string", "enum": ["p0", "p1"], "description": "dry-run stage: p0 policy pre-check (a refusal is a legal exit-0 outcome with its ledger row) or p1 segmentation with the protection list; p3/p6 are write-bearing and withheld from this face; CLI flag --stage"},
            "json_out": {"type": "string", "description": "write the stage report to this path; CLI flag --json"},
        },
        required=("manifest", "stage"),
    ),
    "description": (
        "Dry-run the analysis stages of the i18n pipeline over a run manifest "
        "(tools/i18n_pipeline.py --stage p0|p1): p0 policy pre-check and p1 "
        "segmentation with the protection list (segment ledger rows, i18n SPEC "
        "section 9 nine-key shape). Zero network face (the P2 model stage lives in "
        "tools/i18n_translate.py and is not part of this face). Write face: stage "
        "account rows go to the ledger path named by the manifest; the target face "
        "is never written at the exposed stages."
    ),
},
```

字面注 literals note：`arg_map` 中 `json_out → --json` 的键名循仓内既有惯例（`doc_lint`／`netname_normalize`／`norm_lint` 三 spec 同形）；布尔 `selftest` 走裸旗标（True 附旗标，False 省略，`_build_argv` 布尔腿，`tools/mcp_server.py:825`）；`required=("manifest", "stage")` 用 `required=` 形参（先例 `baselinediff` `required=("old", "new")`，`tools/mcp_server.py:163`）。
Literals note: the `json_out → --json` key naming follows the in-repo convention (the `doc_lint`, `netname_normalize`, and `norm_lint` specs share it); boolean `selftest` rides the bare-flag leg (True appends the flag, False omits it, the `_build_argv` boolean leg, `tools/mcp_server.py:825`); `required=("manifest", "stage")` uses the `required=` parameter (precedent `baselinediff` at `tools/mcp_server.py:163`).

## 4. net_gated 逐条标注 · net_gated per candidate

| name | net_gated | 判读依据 Basis |
|---|---|---|
| ai_flavor_detect | `False` | 检测面零网络（词面与词表均为本地数据，契约卷 §2 道1；ENGINES.md E1 条目 Network face zero） |
| jargon_plan | `False` | plan 面零网络零写（契约卷 §2 道2 默认零写；ENGINES.md E2 条目 Network face zero） |
| i18n_pipeline_dryrun | `False` | 本道自身零网络面（契约卷 §2 道4 明文：P2 网络面全在道5 provider 内） |

判读口径照 `docs/mcp.md` §5 第 5 条（扩容批零新门控面先例）：按 INDEX 面与契约面词面判读零网络者不设 `ROCQWASH_MCP_ALLOW_NET` 门控。本批三候选无一触网；全票唯一网络面＝i18n http 提供者腿（default-deny·环境门三变量＋NETRED ledger），属 `tools/ai_flavor_apply.py` 与 `tools/i18n_translate.py` 的可选腿，不在本批三候选内，**不加门控、不注册**。
Reading convention per `docs/mcp.md` section 5 item 5 (the expansion-batch zero-gate precedent): zero-network faces under the INDEX and contract word-face reading carry no `ROCQWASH_MCP_ALLOW_NET` gate. None of the three candidates touches the network. The ticket's only network face, the i18n http provider leg (default-deny, the three-variable environment gate plus a NETRED ledger line per call), lives in the optional legs of `tools/ai_flavor_apply.py` and `tools/i18n_translate.py`; it is outside the three candidates and is neither gated nor registered here.

## 5. arg_map 逐键 · arg_map key by key

### ai_flavor_detect（契约卷 §2 道1）

| schema key | arg_map flag | JSON type | required | 语义与出处 Semantics and source |
|---|---|---|---|---|
| file | `--file` | string | no | 目标文件（契约卷 §2 道1 CLI 行） |
| tree | `--tree` | string | no | 目标目录，五扩展 *.py *.sh *.md *.json *.ts（契约卷 §2 道1） |
| json_out | `--json` | string | no | 报告落盘路径，schema rocqwash.ai-flavor.report/1（契约卷 §2 道1 输出键面） |
| selftest | `--selftest` | boolean | no | 净/污染双探针（契约卷 §2 道1；数据豁免律不覆盖 em-dash） |

### jargon_plan（契约卷 §2 道2）

| schema key | arg_map flag | JSON type | required | 语义与出处 Semantics and source |
|---|---|---|---|---|
| file | `--file` | string | no | 目标文件（契约卷 §2 道2 CLI 行） |
| tree | `--tree` | string | no | 目标目录（同上） |
| json_out | `--json` | string | no | plan 报告落盘路径（契约卷 §2 道2 `--json <out>`） |

fixed_args＝`["--plan"]`：MCP 面钉死 plan 形（缺省零写），`--apply` 不入 arg_map（§7 未暴露面）。

### i18n_pipeline_dryrun（契约卷 §2 道4）

| schema key | arg_map flag | JSON type | required | 语义与出处 Semantics and source |
|---|---|---|---|---|
| manifest | `--manifest` | string | **yes** | run manifest 路径（i18n SPEC §9 run manifest 形；契约卷 §2 道4） |
| stage | `--stage` | string（enum 发布 p0/p1） | **yes** | 干跑段：p0 政策预查／p1 分段（契约卷 §2 道4 `--stage p0|p1|p3|p6`，本面限 p0/p1） |
| json_out | `--json` | string | no | 段报告落盘路径（契约卷 §2 道4） |

## 6. 计数面 · Counting face（21 → 24）

- 现势现形 21 件＝原 8（RQW08 落岸：sentinel_status／net_probe／baselinediff／ci_triage／vacgen_generate／exp_append／pushci_status／capability_index）＋扩容 13（RQW13 batch 1：chain_graph／doc_lint／ledger_sync／netname_normalize／norm_lint／render_events／select_audit／registry_audit／registry_fix／registry_regen／registry_union／abl1_4b_compile／http_backoff），读自 `docs/mcp.md` §1/§3 与 `tools/mcp_server.py` `TOOL_SPECS` 实点数（本席实数 21 个 dict 字面，见 §9 自验）。
  The current listing carries 21 tools: the original 8 (the RQW08 integration) plus the 13 of RQW13 batch 1, read from `docs/mcp.md` sections 1 and 3 and counted live in this lane's run over `TOOL_SPECS` (21 dict literals; see section 9).
- 本批转正后 `tools/list` ＝ **24 件**（21＋3，追加式：既有 21 spec 与其 schema 零改动，新三 spec 追加于 RQW13 批注块之后）。
  After this batch graduates, `tools/list` carries **24 tools** (21 plus 3, additive: the existing 21 specs and schemas untouched, the three new specs appended after the RQW13 batch block).
- 同步义务归合流席（契约卷 §5）：`docs/mcp.md` §3 表追加三行＋§9 重连注记计数更新＋README 计数行同步＋`tests/t_mcp_face.py` 的「tools/list 恰 21 件、名单逐字对表」断言面更新（该件属零触碰域，本稿只登记义务不触件）。
  Sync duties belong to the integration agent (contract volume section 5): three new rows in `docs/mcp.md` section 3, the section 9 reconnect note count, the README count lines, and the "tools/list carries exactly 21 tools, names matched verbatim" assertion in `tests/t_mcp_face.py` (a zero-touch file for this lane; this draft registers the duty without touching the file).

## 7. 未暴露面与二批登记 · Unexposed faces and the batch-2 register

- **未暴露旗标面**（照 `docs/mcp.md` §3 表注 1 惯例，有意不暴露）：`jargon_apply.py --apply`（写入门；MCP 面只保留 plan 零写形）／`jargon_apply.py --guarded-interactive`（逐行问询交互面，MCP 单发调用形不适配）／`i18n_pipeline.py --stage p3|p6`（写面段：联动改写落段账＋闭合写回，不入干跑面）／三候选各自的 `--json` 以外全部写形旗标（`--emit-handoff`／`--apply-handoff`／`--state`／`--emit`／`--ingest`／`--emit-tenpoint`／`--ingest-tenpoint` 本就属未注册件）。
  Unexposed flag faces (per the `docs/mcp.md` section 3 table note 1 convention, withheld deliberately): `jargon_apply.py --apply` (the write gate; MCP keeps the zero-write plan form), `jargon_apply.py --guarded-interactive` (a per-row interactive face, a poor fit for single-shot MCP calls), `i18n_pipeline.py --stage p3|p6` (write-bearing stages: linkage rewrites land in the ledger and close writes back, outside the dry-run face), and every write-form flag of the unregistered engine files (`--emit-handoff`, `--apply-handoff`, `--state`, `--emit`, `--ingest`, `--emit-tenpoint`, `--ingest-tenpoint`, which belong to files this batch does not register at all).
- **二批候登记 Batch-2 register（待批·未注册）**：引擎本体余四面不属本批三候选，候各自车道裁定：`ai_flavor_apply`（handoff emit/ingest 往返面，写面需 handoff 往返闭合，MCP 形态候裁）／`i18n_translate`（handoff emit/ingest 面；http 腿永不入 MCP 面，default-deny 纪律）／`i18n_verify`（P4 验证矩阵＋十点单 emit/ingest 面）／`termbase`（`--selftest` 面为自然候选）。本组成系本席按契约卷 §2 道8 点名范围判读，票原文未点名四面，二批注册以届时票为准（照 `docs/mcp.md` §3 表注 5 同款声明）。
  Batch-2 register (awaiting orders, not registered): the four remaining engine files are outside this batch's three candidates and await their own lane decisions. `ai_flavor_apply` (the handoff emit/ingest round trip; a write face needing the full handoff loop, MCP shape open), `i18n_translate` (the handoff emit/ingest faces; the http leg never enters the MCP face under the default-deny discipline), `i18n_verify` (the P4 verification matrix plus the ten-point emit/ingest faces), and `termbase` (the `--selftest` face as the natural candidate). This composition is this lane's reading of the contract volume section 2 lane 8 scope; the ticket does not name the four, and the batch-2 ticket governs at registration time (the same declaration shape as `docs/mcp.md` section 3 table note 5).

## 8. 设计注记 · Design notes

1. **rc=1 与 isError 映射的交互 Interaction of rc=1 with the isError mapping**：检测候选的 exit 1＝有命中（数据非错误），而服务端现律 rc≠0 即 `isError:true`（`docs/mcp.md` §3 表注 4）。此交互下，命中结果以 `isError:true` ＋ 文本体报告面呈现（`exit code: 1` 头行照返）。本稿建议**保持 rc 契约逐字不漂移**（票硬约束 0/1/2/9），调用方按「isError:true ＋ 报告体在场＝有命中」读；是否为检测族引入结果级特判，属合流席裁量，本稿不预设。The detection candidate's exit 1 means hits found (data, not errors), while the server maps any nonzero rc to `isError:true` (`docs/mcp.md` section 3 table note 4). Under this interaction a hits-found result presents as `isError:true` with the report body in the text content (the `exit code: 1` header still returned). This draft recommends keeping the exit-code contract verbatim (the ticket hard gate 0/1/2/9) and letting callers read "isError:true plus a report body" as findings present; whether to add a result-level special case for the detection family is the integration agent's call, not pre-decided here.
2. **enum 为发布面非校验面 enum is a publication face, not a validator face**：服务端校验器实查 type／闭属性集／`-` 前缀／required 四面（`tools/mcp_server.py:799` 实读），不查 `enum`；`stage` 的 `enum:["p0","p1"]` 随 `inputSchema` 发布给调用方，强制面＝CLI usage 面（越集值 rc=2，经 MCP 表现为执行层失败结果）。The server validator checks type, the closed property set, the dash-prefix ban, and required (read at `tools/mcp_server.py:799`); it does not check `enum`. The `enum:["p0","p1"]` on `stage` publishes intent to callers; the enforcing gate is the CLI usage face (an out-of-set value exits 2, surfacing over MCP as an execution-level failure result).
3. **file/tree 单选 Single target**：两键恰传其一；同传/双缺（无 selftest）属用法错，rc=2 面（器械族用法错契约）。Pass exactly one of the two keys; passing both or neither (without selftest) is a usage error on the rc=2 face (the instrument-family usage contract).
4. **`-` 前缀禁律 Dash-prefix ban**：全部 string 值（含 `json_out` 路径与 `manifest` 路径）禁 `-` 开头（服务端现役校验，`tools/mcp_server.py:799`）。All string values (including `json_out` and `manifest` paths) must not start with `-` (the live server check at `tools/mcp_server.py:799`).
5. **落岸前行为 Pre-integration behavior**：合流席落岸引擎本体前，`tools/call` 对三候选返回既有 `Registered ahead of its landing` isError 结果形（`tools/mcp_server.py:944` CLI 缺席分支），属执行层失败非协议错误。Until the integration agent lands the engine bodies, `tools/call` on the three candidates returns the existing `Registered ahead of its landing` isError result shape (the missing-CLI branch at `tools/mcp_server.py:944`), an execution-level failure, not a protocol error.
6. **全局面不变 Global faces unchanged**：`ROCQWASH_HOME` 必需、硬超时（`ROCQWASH_MCP_TIMEOUT` 默认 300）、argv 列表传参（无 shell）、子进程流捕获、stdout 纪律，对三候选一视同仁（`docs/mcp.md` §2/§4/§5 现律）。`ROCQWASH_HOME` duty, the hard timeout (`ROCQWASH_MCP_TIMEOUT`, default 300), argv-list passing (no shell), child stream capture, and the stdout discipline apply to the three candidates unchanged (`docs/mcp.md` sections 2, 4, 5).
7. **命名与追加式 Naming and additivity**：dry-run 候选取专名 `i18n_pipeline_dryrun`，使未来整面 `i18n_pipeline`（p3/p6 全段）注册仍为追加 spec；既有 21 spec 零改动（`docs/mcp.md` §1 扩容注记纪律同形）。终名裁量归合流席（改名＝一行变更）。The dry-run candidate takes the dedicated name `i18n_pipeline_dryrun`, so a future full-face `i18n_pipeline` registration (stages p3/p6 included) stays an additive spec; the existing 21 specs are untouched (the same discipline as the `docs/mcp.md` section 1 expansion note). The final name is the integration agent's call (a rename is a one-line change).

## 9. 自验 · Self-check

- **TOOL_SPECS 实点数**：`command grep -c '"name":' tools/mcp_server.py` 于快照树实跑（21 件现势计数，本席活跑，见回执 standards.selfTests）。
  The live count of `TOOL_SPECS` entries is measured with the grep above over the snapshot tree (21, run by this lane; recorded in the receipt standards).
- **语域自查 Register self-check**：本文件全件经器械 `ai_flavor_selfcheck.sh`（36 词面电池＋em-dash U+2014 电池；词表源＝术语表 §4.6/§5）自查，实测输出见下（收工时点）。The whole file was checked with the instrument `ai_flavor_selfcheck.sh` (36 wording faces plus the em-dash U+2014 battery); measured output below at closing time.

```
CH_3FAMILIES_10FACES lines=0
EN_WORD_STEMS_15FACES lines=0
EN_SENTENCE_8FACES lines=0
EN_PARA_INITIAL_3FACES lines=0
EM_DASH_U2014 count=0 (target 0)
TOTAL_WORDING_LINES=0
VERDICT CLEAN (36 faces = 0; em-dash = 0)
```

执行形 Execution：`sh ai_flavor_selfcheck.sh docs/drafts/mcp-tool-specs-engine-body.md`，exit 0（落岸日 本席活跑；器械副本＝票包 `techdocs/ai_flavor_selfcheck.sh`）。铸行途中一次 RED（二批登记行一处 zh 词面＋两处 em-dash 字符），已当场清偿（双字符破折号改冒号、zh 词面改直述），复测 CLEAN；本注记自身不携被清偿字面；mcp.md §8 清偿注记同款纪律。

- 凭据词面自查（值形 grep 于本文件）：0 命中，全件无任何凭据值或凭据词面；环境门三变量名只以变量名形出现（配置键名，非凭据值）。
  Credential-face check (value-shape pass over this file): 0 hits; the three gate variables appear as variable names only (configuration key names, not credential values).
