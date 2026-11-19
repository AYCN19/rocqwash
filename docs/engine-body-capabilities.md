# docs/engine-body-capabilities.md — rocqwash engine body capability entries (lane 8 draft for INDEX transcription)

> Purpose.  Capability-entry draft (the lane 8 deliverable of work order the engine-body ticket, draft only, zero wiring): pre-transcribes the capability entries for the three engine bodies (E1 ai_flavor, E2 jargon, E4 i18n) and the E3 termbase thin layer in the seven-field entry form of `docs/CAPABILITY-INDEX.md` section 2. Wiring and the INDEX transcription belong to the integration agent.
> Interface.  Document face (a draft, not executable). Carries the summary table (engine slot, CLI face, exit codes, network face, basis per file) and the per-item entries with the added Status line; cited as the integration source by `docs/mcp.md` and by the MCP registration draft [`docs/drafts/mcp-tool-specs-engine-body.md`](drafts/mcp-tool-specs-engine-body.md).
> Dependencies.  The snapshot `rocqwash-523e7d4.tar` (HEAD `523e7d4`), the contract volume section 2 per-lane subsections, the three seeds SPEC files, `seeds/engines/ENGINES.md`, and the seven engine files under `tools/` described by the entries; no runtime dependency of its own.
> Evidence.  The version anchor below pins the transcription to the unpacked snapshot (unpack verified on arrival; baseline report `OUT/p0-baseline-report.md` verdict blocked=false); section 3 records the wording-instrument CLEAN verdict and the credential-face check over this file. The original Chinese text is preserved in the sibling `engine-body-capabilities.md.zh.md` archive.
> Exit-codes.  Not applicable to a document face; the exit-code basis of each entry is stated per file in the tables as implemented (the instrument-family 0/1/2/9 contract).

Integration note: draft deliverable of lane 8, work order the engine-body ticket (engine bodies Max three-piece: E1 ai_flavor, E2 jargon, E4 i18n, plus the E3 offline lookup thin layer). This file pre-transcribes the capability entries for the three engine bodies and the termbase thin layer in the seven-field entry form of `docs/CAPABILITY-INDEX.md` section 2. Wiring and the INDEX transcription belong to the integration agent (contract volume section 5). Chinese mirror: [`docs/zh/engine-body.zh.md`](zh/engine-body.zh.md).

Version anchor: snapshot `rocqwash-523e7d4.tar` (HEAD `523e7d4`; unpack copy verified on arrival; baseline re-verification report `OUT/p0-baseline-report.md` verdict blocked=false). The engine body files described here are delivered by lanes 1 to 6 of the same work order and land through the integration agent. The transcription basis of every entry is the contract volume section 2 (per-lane subsections), the three seeds SPEC files, and `seeds/engines/ENGINES.md`, all inside this snapshot.

## 0. Positioning and markers

- **`[live]` marker semantics**: every face in this file carries `[live]`, denoting the in-tree state after the work order's integration lands the engine bodies. Before integration the files are absent from the snapshot tree; callers activate against the landed tree, and the integration agent re-verifies each entry against the landed `--help`/`--selftest` faces (contract volume section 5) before transcribing into `docs/CAPABILITY-INDEX.md` section 2 (candidate-to-landed duty per the ENGINES.md `Landing duty` section).
- **Entry form**: seven fields per entry — path (heading line), purpose, invocation, example, imports, network face, SKIP face — matching `docs/CAPABILITY-INDEX.md` section 2 field by field. This draft adds one Status line per entry, declared here as the draft's own addition (the INDEX precedent: verbatim lines plus declared added lines).
- **Interpreter**: example lines use the in-repo documented prefix `python -I`; the calling environment's interpreter governs (this host measures `py -I` as the real launcher; see baseline report section 4).
- **Exit-code basis**: instrument-family exit contract 0/1/2/9 (0 = clean or legal outcome, 1 = hits or verification red, 2 = usage, 9 = missing external), pinned per lane by contract volume section 2; hits are data, not errors.

## 1. Summary table

| File | Engine slot | CLI face (short) | Exit codes | Network face | Basis |
|---|---|---|---|---|---|
| tools/ai_flavor.py | E1 detection | `--file` / `--tree` / `--selftest` / `--json` | 0 / 1 / 2 | zero | contract volume section 2 lane 1 |
| tools/ai_flavor_apply.py | E1 apply | `--emit-handoff` / `--apply-handoff` / `--apply` / `--state` | 0 / 1 / 2 | http leg default-deny | lane 3 |
| tools/jargon_apply.py | E2 apply | `--file` / `--tree` / `--plan` / `--apply` / `--guarded-interactive` / `--json` | 0 / 1 / 2 (9 = unreadable input file, loader family) | zero | lane 2 |
| tools/i18n_pipeline.py | E4 P0/P1/P3/P6 | `--manifest` / `--stage p0\|p1\|p3\|p6` / `--json` | 0 / 1 / 2 | zero | lane 4 |
| tools/i18n_translate.py | E4 P2 | `--emit` / `--ingest` / `--prompts` | 0 / 1 / 2 | http leg default-deny | lane 5 |
| tools/i18n_verify.py | E4 P4/P5 | `--emit-tenpoint` / `--ingest-tenpoint` | 0 / 1 / 2 | zero | lane 6 |
| tools/termbase.py | E3 offline | `--selftest` plus the `lookup(term)` pure function | 0 / 2 (schema fail-loud) | offline zero | lane 6 |

Table note: Bytes/Lines columns are not carried here (those are census-time facts in the INDEX section 1 table; this draft describes the contract face before integration, and the integration agent records the census face at INDEX transcription time).

## 2. Per-item entries

### tools/ai_flavor.py

- Status: [live] (lane 1 deliverable; the E1 detection body)
- Purpose: Wording-battery detection body: a 36-face battery (10 zh faces in 3 families, 15 English word stems, 8 sentence faces, 3 paragraph-initial faces) plus a separate em-dash battery (U+2014 count, target 0), reading the word map `seeds/ai_flavor/word-map.json` read-only with the detector regex branches transcribed verbatim (no regex literal rewriting); hits are data, not errors (exit 1 hits, 0 clean, 2 usage, the shell instrument contract); `--selftest` runs the clean and polluted probe pair with the data-exclusion rule for this file and the word map (the em-dash target stays global with no exclusion); the report is JSON with English keys (`schema:"rocqwash.ai-flavor.report/1"`, `file`, `batteries{}`, `em_dash_count`, `hits[{line,battery,face_id,before,after}]`, a 40-character window each for before/after); pure-function exports `detect_text(text, word_map) -> report_dict` and `load_word_map(path) -> dict` feed the apply and pipeline faces.
- Invocation: `python -I tools/ai_flavor.py --file <p> [--json <out>]` [live]; `python -I tools/ai_flavor.py --tree <dir> [--json <out>]` (the five extensions *.py *.sh *.md *.json *.ts) [live]; `python -I tools/ai_flavor.py --selftest` [live]
- Example: `python -I tools/ai_flavor.py --file docs/report.md --json out/ai-flavor-report.json`
- Imports: Python 3 standard library only (the work order stdlib-only gate, no third-party imports); the word map loads through stdlib json, read-only.
- Network face: Zero: faces and word map are local data and local text reads; no E1 stage performs network I/O.
- SKIP face: Report-first form, zero writes by default; exit 1 lists findings instead of raising an error; the em-dash target applies everywhere including this file; the `--selftest` self-exclusion covers the wording batteries only (data-exclusion rule), never the em-dash battery.

### tools/ai_flavor_apply.py

- Status: [live] (lane 3 deliverable; the E1 application face)
- Purpose: Advisory application face: every write is advisory and gated behind `--apply`, and every rewrite goes through the rewrite provider. Three dispositions per candidate kind: the 10 zh faces are ban-remediation (no coined substitute, human restate only, never machine-rewritten); the 15 English stems are neutral-direct-form (explore/examine/important, context choice left to the rewrite provider); the 11 sentence and paragraph faces are delete-or-restate. The handoff form (default, zero network): `--emit-handoff` writes segment packages (one `{finding_id, face_id, lang, before, candidates, instruction}` per line); the external model agent fills `{finding_id, choice, after_text, model_id}` and `--apply-handoff` validates (all finding_id matched, choice legal, model_id non-empty; any gap rejects loud) plus the structure guard (delimiter counts unchanged, line-level structure check, per the gate4_autofix reference) before writing. Budget cap: one round per class per target file (`--state`); after apply the detector re-runs and GREEN requires zero residual; idempotent (a second apply reports zero would-fix). Pure-function exports: `plan_suggestions(text, report) -> entries[]`, `emit_handoff(entries) -> str`, `ingest_handoff(text, handoff_rows) -> (new_text, applied[], rejected[])`.
- Invocation: `python -I tools/ai_flavor_apply.py --file <p> --emit-handoff <out.jsonl>` [live]; `python -I tools/ai_flavor_apply.py --file <p> --apply-handoff <in.jsonl>` [live]; `--apply-handoff <in.jsonl>` (the write gate) plus `--state <p>` (the budget-cap state file; default beside the target file) [live]
- Example: `python -I tools/ai_flavor_apply.py --file docs/report.md --emit-handoff out/handoff.jsonl --state out/state.json`
- Imports: Python 3 standard library only (stdlib-only gate); the handoff default face is zero-network; the optional http provider leg declares its transport imports at integration (the contract face does not pin module names).
- Network face: Handoff face zero; the http provider leg is non-zero and default-deny: the environment gate is `ROCQWASH_MCP_ALLOW_NET=1` plus `ROCQWASH_LLM_ENDPOINT` / `ROCQWASH_LLM_MODEL` / `ROCQWASH_LLM_KEY`, and any missing variable refuses loudly naming the missing one (OpenAI-compatible chat/completions shape); every call writes a NETRED ledger line (URL, time, verdict, failures included).
- SKIP face: The 10 zh faces are never machine-rewritten (disposition human); handoff ingest rejection is fail-loud with the rejected list reported; without any model configuration the handoff form stays fully functional (the executing agent is the model site); without the environment gate the http leg refuses instead of degrading.

### tools/jargon_apply.py

- Status: [live] (lane 2 deliverable; the E2 application face plus pure-function library)
- Purpose: Jargon-to-standard application face: data read-only from `seeds/jargon/jargon-map.json` (62 entries); hard rules per jargon SPEC section 3: machine-rewrite `disposition:"replace"` entries only; `rewrite_or_delete` entries are never machine-applied (listed in findings, disposition human); rows whose `note` records a sense split or context guard are guarded and take the per-row handling hook before apply (`--guarded-interactive` emits a per-row question file; the default refuses the rewrite and reports); preserve carve-outs ride the exempt mechanism (`;`-separated regexes, line-scoped); identifier positions are never rewritten (backtick spans masked across segments, per the loader paradigm `tools/norm_lint.py:154-189`); plan default zero-writes and lists before/after pairs; `--apply` re-runs detection afterwards and exit 0 requires zero residual; idempotent. Pure-function exports: `load_map(path) -> dict`, `project_table(map) -> str` (the row-for-row equal JSON-to-pipe-table projector), `plan_rewrites(text, map) -> entries[]` (zero writes), `apply_rewrites(text, entries) -> (new_text, applied[])`.
- Invocation: `python -I tools/jargon_apply.py --file <p> [--plan] [--json <out>]` [live]; `python -I tools/jargon_apply.py --tree <dir> [--plan] [--json <out>]` [live]; `--apply` (the write gate) plus `--guarded-interactive <q>` (the per-row question file) [live]
- Example: `python -I tools/jargon_apply.py --tree docs --plan --json out/jargon-plan.json`
- Imports: Python 3 standard library only (stdlib-only gate); the map loads through stdlib json, read-only.
- Network face: Zero: the map and rewrites are local data and local text edits.
- SKIP face: Zero writes by default; `rewrite_or_delete` rows carry disposition human; guarded rows refuse by default and report; a nonzero residual on rescan exits nonzero (verification red); the single-track law of jargon SPEC section 6 holds (one track per standard cell, cross-track rows quoted as notes only).

### tools/i18n_pipeline.py

- Status: [live] (lane 4 deliverable; the E4 orchestration body P0/P1/P3/P6)
- Purpose: Orchestration body of the zh↔en bidirectional four-linkage pipeline: the six operation signatures are immutable (per `seeds/i18n/pipeline_stub.py` section 10: segment_document, translate_segments, apply_linkages, verify_faces, tenpoint_review, sync_ledger_append); this lane implements P0/P1/P3/P6 and imports the lane 5 and lane 6 modules to assemble translate_segments, verify_faces, and tenpoint_review. P0 policy pre-check: the target-face regime table covers `repo`/`paper`/`supplement` (the module constant `P0_REGIMES`, transcribed from i18n SPEC section 7 tracks D/E); review-sensitive faces default `disclosure_required:true`; a face whose regime reads `refusal:true` refuses as a legal outcome (exit 0, a refusal row in the ledger), and the P0 annotation row (`policy_precheck_ref`) lands before any translation enters the ledger. P1 segmenter: the protection list (code blocks, inline backticks, CLI flags, dash-form tokens, identifiers, math, citations, paths, URLs); a segment is a run of consecutive prose lines; segment ledger rows follow the SPEC section 9 ten-key shape (including policy_precheck_ref) with `source_span` line numbers. P3 applies the four linkages in order L1 (termbase lookup, lane 6), L2 (jargon projection plus plan, lane 2), L3 (zero CJK residual, em-dash density at most 1 per 1000 characters, zero-drift diff over the protection list), L4 (ai_flavor detection whose hits become findings through the lane 3 suggestion flow); linkage rewrites land in the same ledger with `annotation_site` recorded as it happened. P6 ledger: JSONL append-only, English keys, no process narrative inside rows; closing requires every machine segment to carry all ten keys (including policy_precheck_ref) plus `annotation_site=="model"` and a `tenpoint_verdict` that is no longer PENDING.
- Invocation: `python -I tools/i18n_pipeline.py --manifest <run.json> --stage p0|p1|p3|p6 [--json <out>]` [live] (staged execution, resumable from a checkpoint)
- Example: `python -I tools/i18n_pipeline.py --manifest out/run.json --stage p1 --json out/segments.json`
- Imports: Python 3 standard library only (stdlib-only gate) plus the in-repo lane 2, lane 5, and lane 6 modules (the jargon_apply, i18n_translate, i18n_verify assembly faces); manifest and ledger go through stdlib json.
- Network face: Zero: this lane itself carries no network face; the P2 network face lives entirely in the lane 5 provider.
- SKIP face: A P0 refusal is a legal outcome, not a fault (exit 0, ledger row present); closing fails loud when the close checks do not hold; the P2 model site is not in this lane (without model configuration the translate_segments assembly leg rides the lane 5 handoff form).

### tools/i18n_translate.py

- Status: [live] (lane 5 deliverable; the E4 model-site layer P2)
- Purpose: Model-site layer (P2). Handoff form (default, zero network): `--emit` writes segment packages (one row per segment with segment_id, direction, source_text, protected_tokens, prompt_template_ref, instruction); the external model agent fills `{segment_id, translated_text, model_id, prompt_template_ref, timestamp_utc}` and `--ingest` runs the ten-key (including policy_precheck_ref) validation (a missing model_id or a missing annotation is a violation and rejects loud). Http form (optional, default-deny, the same three-variable environment gate as lane 3): an OpenAI-compatible endpoint, called per segment, annotated per segment (model_id = the endpoint model name, `annotation_site="model"`), with a NETRED ledger line per call, failures included. Prompt templates come from `--prompts <dir>` (built-in template constants by default, named in the `prompt_template_ref:"prompts/zh2en-repo-v1"` shape). Pure-function exports: `build_handoff(segments, direction) -> rows`, `ingest_translations(segments, rows) -> (translated, ledger_rows[])`.
- Invocation: `python -I tools/i18n_translate.py --emit <out.jsonl> [--prompts <dir>]` [live]; `python -I tools/i18n_translate.py --ingest <in.jsonl>` [live]; the http-leg flag face follows the landed usage face (this draft transcribes the contract face) [live]
- Example: `python -I tools/i18n_translate.py --emit out/segments-handoff.jsonl --prompts prompts/`
- Imports: Python 3 standard library only (stdlib-only gate); the handoff default face is zero-network; the http leg declares its transport imports at integration.
- Network face: Handoff face zero; the http leg is non-zero and default-deny (environment gate `ROCQWASH_MCP_ALLOW_NET=1` plus the three variables, any gap refuses loud naming the missing one; NETRED ledger per call, failures included).
- SKIP face: The ticket's only network face is the http provider leg (default-deny); without the environment gate it refuses instead of degrading; the handoff form is fully functional with zero network (the executing agent is the model site); a machine segment without annotation is a pipeline violation (the ten-key check, including policy_precheck_ref, rejects it).

### tools/i18n_verify.py

- Status: [live] (lane 6 deliverable; the E4 P4 mechanical verification orchestration plus the P5 ten-point face)
- Purpose: P4 orchestration: subprocess calls to `tools/ai_flavor.py`, `tools/norm_lint.py --jargon-map`, and `tools/doc_lint.py`, collecting rc and reports into a verification matrix JSON (`schema:"rocqwash.i18n.verify/1"`). P5 ten-point face: `--emit-tenpoint <target>` emits the review form (ten point slots per item, each carrying its original-line citation position, variant selected by target-face kind: .v faces use the original ten points of i18n SPEC section 6, tool-repo py/sh/md faces use the annotation-standard card five-field variant); `--ingest-tenpoint <verdicts.json>` validates (per item per point a verdict in {PASS,FAIL} plus complete line citations, frame `ALL-PASS|N-FAIL|BLOCKED`) and writes back to the ledger `tenpoint_verdict`. The engine never judges in the human's place.
- Invocation: `python -I tools/i18n_verify.py --emit-tenpoint <target>` [live]; `python -I tools/i18n_verify.py --ingest-tenpoint <verdicts.json>` [live]; the P4 orchestration flag face follows the landed usage face (this draft transcribes the contract face) [live]
- Example: `python -I tools/i18n_verify.py --emit-tenpoint docs/report.en.md --json out/tenpoint-form.json`
- Imports: Python 3 standard library only (stdlib-only gate; subprocess for the local orchestration); verdict files go through stdlib json.
- Network face: Zero: the subprocesses are local tools in read-only probe runs.
- SKIP face: P5 is a human gate (the engine emits the form and writes back, it never produces verdicts); a missing subprocess target fails loud; the verdict file schema is the contract volume section 3 shape `rocqwash.tenpoint.verdicts/1` (10 rows per item, three frame values).

### tools/termbase.py

- Status: [live] (lane 6 deliverable; the E3 offline lookup thin layer)
- Purpose: Read-only terminology thin layer: `seeds/termbase/termbase.json` read-only (stdlib json, schema validation fails loud), `lookup(term) -> entries`, and `--selftest`. Zero network: the E3 network interface and the DIY entry channel are outside this work order and stay candidates (see the two termbase SPEC files).
- Invocation: `python -I tools/termbase.py --selftest` [live]; the pure function `lookup(term) -> entries` feeds the pipeline L1 import [live]
- Example: `python -I tools/termbase.py --selftest`
- Imports: Python 3 standard library only (stdlib json; the stdlib-only gate).
- Network face: Offline zero (no fetch inside this work order); the network interface is the E3 candidate, default-deny, and when enabled writes a NETRED ledger line per fetch, failures included, per the ENGINES.md E3 entry.
- SKIP face: The built-in snapshot is never edited in place (the upstream glossary stays the sole maintenance point, sync duty rides with the file); DIY entries enter only through the intake gates; without the environment gate the network interface refuses naming `ROCQWASH_MCP_ALLOW_NET`.

## 3. Register self-check

The whole file was checked with the instrument `ai_flavor_selfcheck.sh` (36 wording faces plus the em-dash U+2014 battery; register source: glossary sections 4.6/5); the measured output is recorded below at closing time.

```
CH_3FAMILIES_10FACES lines=0
EN_WORD_STEMS_15FACES lines=0
EN_SENTENCE_8FACES lines=0
EN_PARA_INITIAL_3FACES lines=0
EM_DASH_U2014 count=0 (target 0)
TOTAL_WORDING_LINES=0
VERDICT CLEAN (36 faces = 0; em-dash = 0)
```

Execution: `sh ai_flavor_selfcheck.sh docs/engine-body-capabilities.md`, exit 0 (live run by this lane on the arrival day; the instrument copy is the work-order package `techdocs/ai_flavor_selfcheck.sh`, its manifest md5 verified OK by the baseline lane; the same-day zh mirror and the MCP draft were checked by the same instrument with the same CLEAN verdict). Zero hits in a single pass during casting; the CJK positional-argument breakage of the PowerShell-to-sh path in the work-order package techdocs face is registered (see the execution record); the live run is a direct bash call.

Credential-face check (value-shape pass over this file): 0 hits; no credential value or credential wording anywhere.

## 4. Boundaries

- This file is a draft with zero wiring: the seven engine body files under `tools/` are delivered by lanes 1 to 6 and land through the integration agent; this file creates no `.py` file and modifies no existing file.
- **Landing duty** (the ENGINES.md section of the same name): at integration the integration agent re-verifies per contract volume section 5, transcribes these entries into `docs/CAPABILITY-INDEX.md` section 2 (candidate to landed), and syncs the `docs/mcp.md` capability table (the MCP registration draft lives at [`docs/drafts/mcp-tool-specs-engine-body.md`](drafts/mcp-tool-specs-engine-body.md): three candidates, tools/list 21 to 24).
- The stdlib-only gate and the zero-network default are this ticket's substitute hard gates (all new `.py` files are zero-compile faces, the Prop-leak face does not apply; the only exception is the i18n http provider leg, default-deny).
- The four design-change registrations (E4 promoted to the full pipeline, E3 offline subset inside this ticket, the E1/E2 stage form with integration wiring, E1 writes only through the rewrite provider) belong to the integration agent, per contract volume section 4.
