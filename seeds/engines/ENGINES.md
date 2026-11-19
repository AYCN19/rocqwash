# rocqwash ENGINES: five-engine registry candidates and growth roadmap

Purpose.  Registry candidates for the five-engine seed batch RQW12, issued
  November 14, 2026 (E1 ai-flavor, E2 jargon, E3 termbase, E4 i18n, E5
  engine-registry), plus a growth roadmap with acceptance criteria per step.
  This file registers candidates; it is not the in-library contract surface.
  When an engine is integrated, its entry is transcribed into
  `docs/CAPABILITY-INDEX.md` section 2 in the same seven-field form and the
  candidate marker in section 2 here moves to `landed`.
Interface.  Documentation face (not executable).  Each engine entry carries
  the seven CAPABILITY-INDEX fields (field list identical to
  `docs/CAPABILITY-INDEX.md` section 0).  Sections: 0 source originals,
  1 entry reader guide, 2 registry candidates, 3 growth roadmap, 4
  boundaries.  Consumers: `tests/t_engines_seeds.py` (structure vectors);
  after integration the MCP `capability_index` tool (`tools/mcp_server.py`).
Dependencies.  `docs/CAPABILITY-INDEX.md` (entry form and version anchor),
  the source originals quoted in section 0, `tests/t_engines_seeds.py`, and
  `docs/jargon-to-standard-mapping-v1.md` (term standards).
Evidence.  Version anchor (measured November 14, 2026, local
  `git rev-parse HEAD` on the pinned clone): rocqwash main
  `5829f6d18a9ee2bc63c19ef46caad115e34a0c85`, the same anchor recorded at
  `docs/CAPABILITY-INDEX.md` line 3.  Evidence for every gap claim in this
  file was re-verified live in the current-state audit cited in section 0;
  commands and outputs are listed there and were re-run by the E5 agent
  where this file states a number.
Exit-codes.  Not applicable (documentation face); the asserting suite keeps
  its own contract (`tests/t_engines_seeds.py`: 0 no FAIL, 1 at least one
  FAIL).

## 0. Source originals and transcription discipline

The seed face transcribes data and wording from the originals below. The
originals stay the sole maintenance points. Every seed copy is a read-only
snapshot: re-transcribe on upstream change, record byte count and date in the
touched seed, never edit the snapshot in place, and keep upstream wording
verbatim (transcription without tampering).

```
term register (sole maintenance point; E1 and E3 transcription source)
  `D:/ComplexAnalysis/规范术语/术语表-通用-项目级-20260921.md`
  (94,989 bytes, mtime November 9, 2026 at audit time; section 1 rule 0 and
  the section 4.0 adjudication table are the transcription sources)

annotation whitepaper (E2 mapping provenance)
  `D:/ComplexAnalysis/规范术语/注释规范白皮书-v1.0-20260921.md`
  (in-file header self-attests v1.8, October 7, 2026; section 4 mapping table;
  the design volume's "v1.10" reference has no matching file on disk and is
  treated as a design-volume typo pending design-side review, per audit
  section 2 note 5)

redline whitepaper (discipline source for all five engines)
  `D:/ComplexAnalysis/规范术语/纯构造性纲领与红线律白皮书-v2.0-20261008.md`
  (in-file header self-attests v2.5, October 26, 2026)

design volume (the upstream order for this seed batch)
  `D:/ComplexAnalysis/attn/跨线资产/分析与工单/rocqwash五引擎生长设计卷-20261114.md`

current-state audit (evidence base for the gap claims below)
  `D:/ComplexAnalysis/attn/_rqw12_seeds_20261114/gap-五引擎-20261114.md`

in-library jargon table (E2 loader-consumable form today)
  docs/jargon-to-standard-mapping-v1.md (rocqwash repo; 19,263 bytes,
  145 table rows at audit time; norm_lint default at norm_lint.py:84)

ai-flavor detection instrument (E1 detection face today; outside the
rocqwash tree, transcribed as data, binary not moved)
  `D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/ai_flavor_selfcheck.sh`
  (58 lines; battery of 36 faces in 4 groups plus a separate em-dash count;
  exit 0 clean / 1 red / 2 usage, selfcheck lines 19 and 53-58)
```

Register rule for this file: the document face is English; CJK characters
appear only inside the verbatim path block above (paths are quoted exactly as
they exist on disk; transcription without tampering covers path spelling too).

## 1. How to read an entry

Each engine entry carries the seven CAPABILITY-INDEX fields: Path, Purpose,
Invocation, Example, Imports, Network face, SKIP face. Status markers:

- `[live]` the named face exists in the rocqwash tree today and is callable as
  written (evidence: path and line, or a live `--help`/`--selftest` run).
- `[candidate]` the face is registered ahead of its integration (the MCP-layer
  form of `tools/mcp_server.py:498-502`); it is not callable until integration
  and the SKIP face says so.

Integration update (the engine-body ticket, integrated this round): the engine
bodies landed through the integration agent and the markers below flip
per the integration duty in this section: E1 replacement `[candidate]` ->
`[live]`, E2 application `[candidate]` -> `[live]`, E3 offline lookup
`[candidate]` -> `[live]` (the E3 network interface and DIY channel stay
`[candidate]`), E4 pipeline `[candidate]` -> `[live]`. Original sentences
are kept; the flips are appended as integration annotations.

Seed paths are given relative to the rocqwash repository root, where the
`seeds/` tree lands after staging.

## 2. Registry candidates

### E1 ai-flavor (AI-flavor wording detection and replacement)
- Path: `seeds/ai_flavor/word-map.json` (data seed) + `seeds/ai_flavor/SPEC.md`
  (spec). Detection face today: the instrument file named in section 0, which
  stays in its current location; its pattern literals are transcribed into the
  JSON word map, not moved as an executable body.
- Purpose: AI-flavor wording detection (36 faces in 4 groups plus a separate
  em-dash count) with the word-to-candidate-replacement map parameterized as
  data, so detection and replacement consume one shared word map. The
  replacement stage does not exist today (no automated replacement anywhere in
  the rocqwash tree) and is registered ahead of integration as a wash_shape
  stage.
- Invocation: detection `[live]` `sh ai_flavor_selfcheck.sh <target.md>` with
  exit 0 clean / 1 red / 2 usage (selfcheck lines 19, 53-58). Replacement
  `[candidate]` after the ai-flavor wash stage lands (roadmap step 2):
  `python tools/wash_shape.py --file <value> --apply` [integration update: the stage landed as wash 7 `ai-flavor` in wash_shape and the
  detection body `tools/ai_flavor.py`; the write face runs through the
  rewrite provider per design change 4, so the wash_shape apply arm emits
  the handoff package, which lands in the caller's process working
  directory (a bare-basename emit path, not beside the target), and the
  round trip completes it]
- Example: `sh ai_flavor_selfcheck.sh docs/report.md`; candidate form:
  `python tools/wash_shape.py --file docs/report.md --apply`
- Imports: wash_shape.py already imports argparse, datetime, hashlib, io,
  json, os, re, shutil, subprocess, sys, tempfile, time (CAPABILITY-INDEX
  entry for tools/wash_shape.py); word-map.json is data read with stdlib json.
- Network face: zero. Word faces and replacements are local data and local
  text edits; no stage of E1 performs network I/O.
- SKIP face: the replacement stage is `[candidate]`; until integration,
  requests for automated replacement get the registered-ahead-of-integration
  answer and the detection face keeps its report-only exit-code contract. [integration update: the replacement face is `[live]` as the advisory wash 7 stage;
  machine substitution stays banned, writes go through the provider]

### E2 jargon (jargon-to-standard mapping)
- Path: `seeds/jargon/jargon-map.json` (data seed) + `seeds/jargon/SPEC.md`
  (spec). Loader-consumable form today: the in-library md pipe table named in
  section 0 (norm_lint default `docs/jargon-to-standard-mapping-v1.md`,
  norm_lint.py:84).
- Purpose: jargon face to standard-term mapping, transcribed from the
  in-library v1 table (its own provenance chain: JARGON v1.1 and the
  annotation whitepaper section 4), feeding detection `[live]` through
  `norm_lint.py --jargon-map` and the wash_shape jargon wash stage
  `[candidate]`. The application side is absent today: `command grep -n
  "jargon" tools/wash_shape.py` returns zero hits at the audit (November 14,
  2026).
  [integration update: the application face landed as wash 6 `jargon`
  in wash_shape over `tools/jargon_apply.py`; the gap sentence above is the
  audit-time fact and stands as written]
- Invocation: detection `[live]` (report-only; loader at norm_lint.py:154-189
  reads md pipe rows and fails loudly on malformed or duplicate rows):
  `python tools/norm_lint.py --tree <value> --jargon-map docs/jargon-to-standard-mapping-v1.md`
  Application `[candidate]` wash_shape jargon stage. [integration update: the application stage is `[live]`:
  `python tools/wash_shape.py --dir <value> --apply --only jargon`]
- Example: `python tools/norm_lint.py --tree tools --jargon-map docs/jargon-to-standard-mapping-v1.md`
  (live); candidate form: `python tools/wash_shape.py --dir <value> --apply --only jargon`
- Imports: norm_lint.py imports argparse, fnmatch, io, json, os, re, shutil,
  sys, tempfile, tokenize (CAPABILITY-INDEX entry). Interface note: the live
  loader consumes md pipe-table rows, so the JSON seed needs the render step
  defined in its SPEC (JSON to pipe-table render with a row-for-row equality
  duty); direct JSON consumption by the loader is a loader change and is part
  of roadmap step 1, not a silent format rename.
- Network face: zero.
- SKIP face: norm_lint is report-only first form; writes happen only through
  the future wash_shape stage, which is `[candidate]` until integration.
  [integration update: that stage is `[live]`]

### E3 termbase (terminology standardization base)
- Path: `seeds/termbase/termbase.json` (offline built-in seed) +
  `seeds/termbase/net-interface-SPEC.md` + `seeds/termbase/diy-channel-SPEC.md`.
- Purpose: terminology standardization and internationalization base, the
  whole set absent today (name-level and text-level scans in the audit found
  no termbase face anywhere in the rocqwash tree, November 14, 2026). The
  seed is an
  offline read-only snapshot of the term register skeleton (section 1 rule 0
  and the section 4.0 adjudication table) plus domain slots, a network
  interface spec for community normative sources, and a DIY entry channel spec
  (intake gates with provenance).
- Invocation: `[candidate]` offline lookup over termbase.json (stdlib json
  read); network interface `[candidate]` fires only under
  `ROCQWASH_MCP_ALLOW_NET=1` (the MCP-layer gate convention,
  tools/mcp_server.py pushci entry description). [integration update:
  the offline lookup is `[live]` as `python -I tools/termbase.py --lookup
  <term>` plus `--selftest` (design change 2, offline subset only); the
  network interface stays `[candidate]`]
- Example: validation example only at seed stage, `python -I tests/t_engines_seeds.py`
  (termbase schema vectors); no lookup CLI exists until integration.
- Imports: stdlib json for the seed; the net interface declares its imports at
  integration (urllib family expected, declared in net-interface-SPEC.md).
- Network face: offline zero; net interface non-zero and default-deny (env
  gate plus a NETRED ledger line per fetch, failures included).
- SKIP face: the built-in snapshot is never edited in place (upstream register
  is the sole maintenance point); DIY entries enter only through the intake
  gates; without the env gate the net interface refuses loudly.

### E4 i18n (bilingual translation pipeline)
- Path: `seeds/i18n/` (spec directory; the spec file is the one issued by the
  design volume section 3, its filename kept as issued).
- Purpose: zh-to-en and en-to-zh translation pipeline spec with four coupled
  stages (terminology standardization, normalization, internationalization,
  AI-flavor removal), a half-finished product by design: spec plus skeleton
  stub. LLM-dependent steps are marked at the model site (the SPEC names the
  required model configuration; nothing silently substitutes for it), and the
  register-checked English output face carries the manual ten-point checklist
  duty.
- Invocation: none executable at seed stage. Skeleton stub after integration
  runs offline smoke only; LLM steps skip loudly naming the missing
  configuration.
  [integration update: the pipeline body is `[live]` as
  `python -I tools/i18n_pipeline.py --manifest <run.json> --stage p0|p1|p3|p6`
  with the companion faces `tools/i18n_translate.py` (P2) and
  `tools/i18n_verify.py` (P4/P5); design change 1 registers the promotion
  beyond the step 4 stub]
- Example: validation example only at seed stage, `python -I tests/t_engines_seeds.py`
  (i18n spec structure vectors).
- Imports: stdlib only in the stub face; the LLM interface is declared in the
  SPEC and is not implemented inside seeds (seeds carry zero engine body).
- Network face: offline zero; any LLM or network face is SPEC-declared and
  default-deny.
- SKIP face: division of duty with the live evolve slot: KIND_TOPIC maps
  norm-regression and longtail-translation to topic "translation"
  (tools/evolve.py:330-337), and the law-one candidates consume norm_lint
  signals `translatable_error_mass` and apply mapping-table replacement with
  .zh.md archive siblings (tools/evolve.py:231-250 and 810-822). That slot is
  EN-ward one-way replacement scheduling; E4 is the bidirectional pipeline.
  The E4 SPEC states this split to prevent a double track.

### E5 engine-registry (registry and roadmap face)
- Path: `seeds/engines/ENGINES.md` (this file) + `tests/t_engines_seeds.py`
  (test suite, merged from the four engine segments plus this total-selftest
  segment by the tests agent).
- Purpose: the five-engine registry candidate surface (this file) plus the
  test suite asserting the seeds. Registration duties on integration:
  transcribe
  each landed entry into `docs/CAPABILITY-INDEX.md` section 2 in the same
  seven-field form; append the pending-capability record through
  `tools/exp_port.py append` (schema rocqwash-exp/1, idempotent seen set,
  tools/exp_port.py:72); register the evolve feed, either a new KIND_TOPIC
  slot or an explicit mapping to the existing "translation" topic, recorded in
  the ledger (tools/evolve.py:330-337).
- Invocation: after integration, read through the MCP `capability_index` tool
  (tools/mcp_server.py:297-306 returns docs/CAPABILITY-INDEX.md); until
  integration, read this file directly.
- Example: `python -I tests/t_engines_seeds.py` (registry structure vectors,
  seed existence vectors, and the total selftest over all five segments).
- Imports: the test segment uses stdlib os, re, sys only.
- Network face: zero.
- SKIP face: candidate entries reference faces that are not landed; such
  references are marked `[candidate]` and return the
  registered-ahead-of-integration answer until integration.

## 3. Growth roadmap (four steps, acceptance criteria per step)

Order is fixed: detection first, application closed loop second, built-in plus
network third, pipeline last. A step starts only when the previous step's
acceptance items all hold.

### Step 1: E2 detection-ready (in-library, zero new engine code)
Work: land `seeds/jargon/jargon-map.json` (transcribed from the in-library v1
table) and `seeds/jargon/SPEC.md`; define the JSON to pipe-table render duty;
keep norm_lint consumption on the md form.
Acceptance criteria:
  A1. `python -I tools/norm_lint.py --selftest` exits 0 with the six PASS
      vector lines and no FAIL line.
  A2. The table rendered from the JSON seed equals the in-library v1 table
      row for row (row count and per-row cells checked by a mechanical diff;
      zero tampering against the transcription source).
  A3. `python -I tools/norm_lint.py --jargon-map <rendered table>` on a probe
      face returns report-only findings with zero writes and the exit-code
      contract unchanged.
  A4. The jargon segment of tests/t_engines_seeds.py is green.

### Step 2: E1/E2 application closed loop (wash_shape wiring)
Work: add the jargon wash stage and the ai-flavor wash stage to wash_shape
(candidate flags registered in section 2), reusing the two-phase plan-then-
apply contract and the five-stage rescan verification shape (wash_shape.py
help face, live run of November 14, 2026).
Acceptance criteria:
  A1. Plan phase (default) performs zero writes and lists would-fix items with
      before-to-after pairs sourced from the seed maps.
  A2. Apply phase on a fixture executes the would-fix items and the re-run
      detection reports zero residual jargon and ai-flavor hits on that
      fixture.
  A3. A second apply run on the same fixture reports zero would-fix items
      (idempotence).
  A4. norm_lint selftest stays at six PASS; the full test suite is green twice
      in a row; no case was skipped or weakened to reach green.
  A5. Replaced Chinese prose keeps the .zh.md archive sibling duty, matching
      the law-one acceptance form (tools/evolve.py:231-250).
  A6. wash_shape network face stays zero (word-level replacement only).

Integration record (the engine-body ticket, integrated this round).  DESIGN-CHANGE
3: the E1/E2 application faces land as wash_shape stages, not as a forked
engine: wash 6 `jargon` (machine-applies the map's replace disposition through
`tools/jargon_apply.py`) and wash 7 `ai-flavor` (advisory only, machine
substitution stays banned).  DESIGN-CHANGE 4: every E1 write goes through the
rewrite provider (handoff default zero-network; http default-deny); the
wash_shape apply arm emits the handoff package and the provider round trip
completes the write, so the rescan reports residual suggestions loudly until
the round trip lands.  Acceptance run by the integration agent on the
integrated tree: A1 zero-write plan with before/after pairs, A2 apply then
zero residual on the jargon leg, A3 idempotence, A6 zero network (the A4/A5
faces are covered by the suite and the .zh.md archive law respectively).

### Step 3: E3 built-in plus network
Work: land `seeds/termbase/termbase.json`, `net-interface-SPEC.md`, and
`diy-channel-SPEC.md`; implement the offline lookup and the gated network
interface per the specs.
Acceptance criteria:
  A1. termbase.json passes schema validation offline under `python -I` with
      zero network.
  A2. The network interface fires only with `ROCQWASH_MCP_ALLOW_NET=1`;
      without it, the refusal is loud and names the environment variable.
  A3. Every fetch writes a NETRED ledger line (URL, time, verdict), failures
      included.
  A4. DIY entries enter only through the intake gates with provenance fields;
      rejected entries are reported, never dropped silently.
  A5. Snapshot discipline holds: the built-in copy is never edited in place;
      the sync duty against the upstream register is documented in the SPEC.

Integration record (the engine-body ticket, integrated this round).  DESIGN-CHANGE
2: this ticket takes the Step 3 offline subset only (`tools/termbase.py` over
`seeds/termbase/termbase.json`, the read-only lookup plus `--selftest`); the
E3 network interface and the DIY entry channel are outside the ticket and
stay `[candidate]` per their own seed SPECs.  The order clause above ("a step
starts only when the previous step's acceptance items all hold") is read with
the user order commissioning this round as the sequence authority: the offline subset
lands inside this ticket while the network faces keep their candidate state.

### Step 4: E4 pipeline
Work: review the translation SPEC against the manual ten-point checklist,
then land the skeleton stub per the SPEC.
Acceptance criteria:
  A1. The SPEC records the ten-point checklist review, the AI-policy precheck
      note, and a model-site marker on every LLM-dependent step.
  A2. The stub passes offline smoke under `python -I` with zero network;
      LLM-dependent steps skip loudly and name the missing configuration.
  A3. The SPEC documents the division of duty against the live evolve
      translation slot (one-way EN-ward replacement scheduling versus the
      bidirectional pipeline; no double track).
  A4. The English output face passes the ai-flavor battery and the em-dash
      target of 0 before any integration.

Integration record (the engine-body ticket, integrated this round).  DESIGN-CHANGE
1: E4 lands as the full pipeline body, not the skeleton stub this step
describes: `tools/i18n_pipeline.py` implements P0/P1/P3/P6, assembles P2
from `tools/i18n_translate.py` and P4/P5 from `tools/i18n_verify.py`, with
the handoff and http provider forms and the human ten-point gate.  The
original step 4 wording (stub face, skip-loud LLM steps) stands above as the
roadmap text it replaced in fact; the spec file under `seeds/i18n/` carries
the same record in its section 14.  Basis: the user order commissioning this round ("Max engines, the three
pieces fully covered").

### Landing duty (applies to every step)
Each landed engine transcribes into `docs/CAPABILITY-INDEX.md` section 2 in
the seven-field form, appends the pending-capability record through
`tools/exp_port.py append`, and registers its evolve feed slot. The seed copy
[integration note: the INDEX transcription for the seven
engine-body files is done by the integration agent; the exp_port append and
the evolve feed slot registration were not in the contract volume section 5
checklist for this ticket and are left registered here as an open duty for
the receiving session, not silently assumed]
stays a read-only snapshot; the source originals in section 0 remain the sole
maintenance points. README files, `cw.sh`, and `.github` are outside the seed
batch and stay untouched.

## 4. Boundaries

- Seeds carry data (JSON), spec (md), and tests (py) only; zero executable
  engine body. The engines grow through their own wash_shape, norm_lint, and
  evolve faces in later waves.
- English-face register is checked: seed JSON keys are English, spec and test
  comments are English, and the ENGINES.md document face passes the ai-flavor
  battery and the em-dash target of 0 (CJK appears only in the verbatim path
  block of section 0).
- Network faces are default-deny; the only network-bearing candidate (E3 net
  interface) is gated by `ROCQWASH_MCP_ALLOW_NET=1` with a NETRED ledger duty.
- Negative findings in this file (for example "no termbase face in the tree")
  are findings of the audit scan named in section 0, not absolute claims; the
  audit records the scan surface and its boundaries in its own sections.
