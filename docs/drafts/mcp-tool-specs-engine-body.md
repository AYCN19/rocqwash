# docs/drafts/mcp-tool-specs-engine-body.md — MCP TOOL_SPECS registration draft, engine body batch (lane 8 draft, wiring belongs to the integration agent)

> Purpose.  Registration draft (the lane 8 deliverable of work order the engine-body ticket, draft only, zero wiring): pre-casts three candidate registration entries — `ai_flavor_detect`, `jargon_plan`, `i18n_pipeline_dryrun` — in the exact `TOOL_SPECS` shape of `tools/mcp_server.py`. Wiring (writing them into `tools/mcp_server.py`) and the counting-face sync belong to the integration agent.
> Interface.  Document face (a draft, not executable). Carries the `docs/mcp.md` section 3 table rows, the Python `TOOL_SPECS` literals, the per-candidate `net_gated` reading, the per-key `arg_map` semantics, the 21-to-24 counting face, and the unexposed-face register; cited as the engine-body registration source by `docs/mcp.md` and `docs/engine-body-capabilities.md`.
> Dependencies.  `tools/mcp_server.py` (the `TOOL_SPECS` shape, read at snapshot HEAD `523e7d4`), `docs/mcp.md`, `docs/engine-body-capabilities.md`, `seeds/engines/ENGINES.md`, and the three registered engine files `tools/ai_flavor.py`, `tools/jargon_apply.py`, `tools/i18n_pipeline.py`; no runtime dependency of its own.
> Evidence.  The version anchor below pins the transcribed shapes to snapshot HEAD `523e7d4`; section 9 records the first-hand self-checks (the live 21-entry `TOOL_SPECS` count and the wording-instrument CLEAN verdict over this file). The original Chinese text is preserved in the sibling `mcp-tool-specs-engine-body.md.zh.md` archive.
> Exit-codes.  Not applicable to a document face; the rc values discussed in section 8 are the documented tools' observed exit codes, described as implemented.

Integration note: the lane 8 draft deliverable of work order the engine-body ticket (draft only, zero wiring). This file pre-casts three candidate registration entries in the exact `TOOL_SPECS` shape of `tools/mcp_server.py` (`name`/`kind`/`cli`/`net_gated`/`fixed_args`/`arg_map`/`schema`/`description`, schema = closed property set with `additionalProperties:false`). Wiring (writing them into `tools/mcp_server.py`) and the counting-face sync belong to the integration agent (contract volume section 5: this draft graduates into TOOL_SPECS, tools/list 21 to 24, README count lines synced).

Version anchor: snapshot HEAD `523e7d4` (unpack copy taken on the arrival day); the `TOOL_SPECS` shape is read from that snapshot's `tools/mcp_server.py:83` (table head), `:825` (argv mapping), and `:891` (argument validation); the 21-capability count is read from `docs/mcp.md` sections 1 and 3 (original 8 plus the 13 of RQW13 batch 1).

## 1. Positioning

Three candidates per contract volume section 2 lane 8: the ai_flavor detection face, the jargon plan face, and the i18n pipeline dry-run face. Names follow the `vacgen_generate` / `pushci_status` / `sentinel_status` precedent (tool plus face encoded, snake_case); the dry-run candidate takes a dedicated name (see section 8 note 7), so a future full-face `i18n_pipeline` registration stays additive (existing specs untouched, per the expansion-note discipline of `docs/mcp.md` section 1).

## 2. Table rows for the capability table (`docs/mcp.md` section 3)

| Capability | Underlying entry (INDEX true form) | Arguments (schema properties; * = required) | Security face |
|---|---|---|---|
| ai_flavor_detect | `tools/ai_flavor.py` | file, tree, json_out, selftest | allow (zero network, report form zero writes) |
| jargon_plan | `tools/jargon_apply.py --plan` | file, tree, json_out | allow (plan is zero-write by default, the apply face is not exposed) |
| i18n_pipeline_dryrun | `tools/i18n_pipeline.py --stage p0\|p1` | manifest*, stage, json_out | allow (stage limited to the p0/p1 dry-run face, the p3/p6 write stages are not exposed) |

All three candidates carry `net_gated:false` (section 4 reading); the ticket's only network face (the i18n http provider leg) is outside this registration batch.

## 3. TOOL_SPECS literals (exact server shape)

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

Literals note: the `json_out → --json` key naming follows the in-repo convention (the `doc_lint`, `netname_normalize`, and `norm_lint` specs share it); boolean `selftest` rides the bare-flag leg (True appends the flag, False omits it, the `_build_argv` boolean leg, `tools/mcp_server.py:825`); `required=("manifest", "stage")` uses the `required=` parameter (precedent `baselinediff` at `tools/mcp_server.py:163`).

## 4. net_gated per candidate

| name | net_gated | Basis |
|---|---|---|
| ai_flavor_detect | `False` | detection face zero network (word faces and word map are local data; contract volume section 2 lane 1; ENGINES.md E1 entry Network face zero) |
| jargon_plan | `False` | plan face zero network zero writes (zero-write default per contract volume section 2 lane 2; ENGINES.md E2 entry Network face zero) |
| i18n_pipeline_dryrun | `False` | this lane itself carries no network face (contract volume section 2 lane 4 states it outright: the P2 network face lives entirely inside the lane 5 provider) |

Reading convention per `docs/mcp.md` section 5 item 5 (the expansion-batch zero-gate precedent): zero-network faces under the INDEX and contract word-face reading carry no `ROCQWASH_MCP_ALLOW_NET` gate. None of the three candidates touches the network. The ticket's only network face, the i18n http provider leg (default-deny, the three-variable environment gate plus a NETRED ledger line per call), lives in the optional legs of `tools/ai_flavor_apply.py` and `tools/i18n_translate.py`; it is outside the three candidates and is neither gated nor registered here.

## 5. arg_map key by key

### ai_flavor_detect (contract volume section 2, lane 1)

| schema key | arg_map flag | JSON type | required | Semantics and source |
|---|---|---|---|---|
| file | `--file` | string | no | target file (contract volume section 2 lane 1 CLI line) |
| tree | `--tree` | string | no | target directory, the five extensions *.py *.sh *.md *.json *.ts (contract volume section 2 lane 1) |
| json_out | `--json` | string | no | report output path, schema rocqwash.ai-flavor.report/1 (contract volume section 2 lane 1 output-key face) |
| selftest | `--selftest` | boolean | no | clean and polluted probe pair (contract volume section 2 lane 1; the data-exemption rule does not cover the em-dash battery) |

### jargon_plan (contract volume section 2, lane 2)

| schema key | arg_map flag | JSON type | required | Semantics and source |
|---|---|---|---|---|
| file | `--file` | string | no | target file (contract volume section 2 lane 2 CLI line) |
| tree | `--tree` | string | no | target directory (as above) |
| json_out | `--json` | string | no | plan report output path (contract volume section 2 lane 2 `--json <out>`) |

fixed_args = `["--plan"]`: the MCP face pins the plan form (zero writes by default); `--apply` stays outside arg_map (the unexposed faces, section 7).

### i18n_pipeline_dryrun (contract volume section 2, lane 4)

| schema key | arg_map flag | JSON type | required | Semantics and source |
|---|---|---|---|---|
| manifest | `--manifest` | string | **yes** | run manifest path (i18n SPEC section 9 run manifest shape; contract volume section 2 lane 4) |
| stage | `--stage` | string (published enum p0/p1) | **yes** | dry-run stages: p0 policy pre-check / p1 segmentation (contract volume section 2 lane 4 `--stage p0|p1|p3|p6`; this face is limited to p0/p1) |
| json_out | `--json` | string | no | stage report output path (contract volume section 2 lane 4) |

## 6. Counting face (21 → 24)

- The current listing carries 21 tools: the original 8 (the RQW08 integration: sentinel_status, net_probe, baselinediff, ci_triage, vacgen_generate, exp_append, pushci_status, capability_index) plus the 13 of RQW13 batch 1 (chain_graph, doc_lint, ledger_sync, netname_normalize, norm_lint, render_events, select_audit, registry_audit, registry_fix, registry_regen, registry_union, abl1_4b_compile, http_backoff), read from `docs/mcp.md` sections 1 and 3 and counted live in this lane's run over `TOOL_SPECS` (21 dict literals; see section 9).
- After this batch graduates, `tools/list` carries **24 tools** (21 plus 3, additive: the existing 21 specs and schemas untouched, the three new specs appended after the RQW13 batch block).
- Sync duties belong to the integration agent (contract volume section 5): three new rows in `docs/mcp.md` section 3, the section 9 reconnect note count, the README count lines, and the "tools/list carries exactly 21 tools, names matched verbatim" assertion in `tests/t_mcp_face.py` (a zero-touch file for this lane; this draft registers the duty without touching the file).

## 7. Unexposed faces and the batch-2 register

- **Unexposed flag faces** (per the `docs/mcp.md` section 3 table note 1 convention, withheld deliberately): `jargon_apply.py --apply` (the write gate; MCP keeps the zero-write plan form), `jargon_apply.py --guarded-interactive` (a per-row interactive face, a poor fit for single-shot MCP calls), `i18n_pipeline.py --stage p3|p6` (write-bearing stages: linkage rewrites land in the ledger and close writes back, outside the dry-run face), and every write-form flag of the unregistered engine files (`--emit-handoff`, `--apply-handoff`, `--state`, `--emit`, `--ingest`, `--emit-tenpoint`, `--ingest-tenpoint`, which belong to files this batch does not register at all).
- **Batch-2 register** (awaiting orders, not registered): the four remaining engine files are outside this batch's three candidates and await their own lane decisions. `ai_flavor_apply` (the handoff emit/ingest round trip; a write face needing the full handoff loop, MCP shape open), `i18n_translate` (the handoff emit/ingest faces; the http leg never enters the MCP face under the default-deny discipline), `i18n_verify` (the P4 verification matrix plus the ten-point emit/ingest faces), and `termbase` (the `--selftest` face as the natural candidate). This composition is this lane's reading of the contract volume section 2 lane 8 scope; the ticket does not name the four, and the batch-2 ticket governs at registration time (the same declaration shape as `docs/mcp.md` section 3 table note 5).

## 8. Design notes

1. **Interaction of rc=1 with the isError mapping**: the detection candidate's exit 1 means hits found (data, not errors), while the server maps any nonzero rc to `isError:true` (`docs/mcp.md` section 3 table note 4). Under this interaction a hits-found result presents as `isError:true` with the report body in the text content (the `exit code: 1` header still returned). This draft recommends keeping the exit-code contract verbatim (the ticket hard gate 0/1/2/9) and letting callers read "isError:true plus a report body" as findings present; whether to add a result-level special case for the detection family is the integration agent's call, not pre-decided here.
2. **enum is a publication face, not a validator face**: the server validator checks type, the closed property set, the dash-prefix ban, and required (read at `tools/mcp_server.py:799`); it does not check `enum`. The `enum:["p0","p1"]` on `stage` publishes intent to callers; the enforcing gate is the CLI usage face (an out-of-set value exits 2, surfacing over MCP as an execution-level failure result).
3. **Single target**: pass exactly one of the two keys; passing both or neither (without selftest) is a usage error on the rc=2 face (the instrument-family usage contract).
4. **Dash-prefix ban**: all string values (including `json_out` and `manifest` paths) must not start with `-` (the live server check at `tools/mcp_server.py:799`).
5. **Pre-integration behavior**: until the integration agent lands the engine bodies, `tools/call` on the three candidates returns the existing `Registered ahead of its landing` isError result shape (the missing-CLI branch at `tools/mcp_server.py:944`), an execution-level failure, not a protocol error.
6. **Global faces unchanged**: `ROCQWASH_HOME` duty, the hard timeout (`ROCQWASH_MCP_TIMEOUT`, default 300), argv-list passing (no shell), child stream capture, and the stdout discipline apply to the three candidates unchanged (`docs/mcp.md` sections 2, 4, 5).
7. **Naming and additivity**: the dry-run candidate takes the dedicated name `i18n_pipeline_dryrun`, so a future full-face `i18n_pipeline` registration (stages p3/p6 included) stays an additive spec; the existing 21 specs are untouched (the same discipline as the `docs/mcp.md` section 1 expansion note). The final name is the integration agent's call (a rename is a one-line change).

## 9. Self-check

- **Live `TOOL_SPECS` count**: `command grep -c '"name":' tools/mcp_server.py` over the snapshot tree (the current count is 21, run live by this lane; recorded in the execution record `standards.selfTests`).
- **Register self-check**: the whole file was checked with the instrument `ai_flavor_selfcheck.sh` (36 wording faces plus the em-dash U+2014 battery; register source: glossary sections 4.6/5); the measured output is recorded below at closing time.

```
CH_3FAMILIES_10FACES lines=0
EN_WORD_STEMS_15FACES lines=0
EN_SENTENCE_8FACES lines=0
EN_PARA_INITIAL_3FACES lines=0
EM_DASH_U2014 count=0 (target 0)
TOTAL_WORDING_LINES=0
VERDICT CLEAN (36 faces = 0; em-dash = 0)
```

Execution: `sh ai_flavor_selfcheck.sh docs/drafts/mcp-tool-specs-engine-body.md`, exit 0 (live run by this lane on the arrival day; the instrument copy is the work-order package `techdocs/ai_flavor_selfcheck.sh`). One RED during casting (one zh word face plus two em-dash characters on the batch-2 register line) was remediated on the spot (the double-character dash became a colon, the zh face became a direct statement) and the re-check came back CLEAN; this note itself carries none of the remediated literals; the same discipline as the remediation note in `docs/mcp.md` section 8.

- Credential-face check (value-shape pass over this file): 0 hits; the three gate variables appear as variable names only (configuration key names, not credential values).
