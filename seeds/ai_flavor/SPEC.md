# SPEC: ai_flavor seed package (engine E1, wording register)

Purpose.  Package: seed work stream RQW12, engine E1 of the five-engine
  growth design volume
  (`D:/ComplexAnalysis/attn/跨线资产/分析与工单/rocqwash五引擎生长设计卷-20261114.md`, section 3, entry 1).
  The package is data plus specification only: it carries **no executable
  engine body**. The engine faces (selfcheck / norm_lint / wash_shape /
  evolve) grow from this data in later work streams per the design
  volume's two-leg growth path.

Interface.  `word-map.json` (schema `rocqwash.seeds.ai-flavor.word-map/1`),
  this SPEC, `test_snippet.py` (merged into `tests/t_engines_seeds.py` by the
  tests-integration agent); consumers `tools/ai_flavor.py`, `tools/ai_flavor_apply.py`.

Dependencies.  Python 3 standard library only; the register canon and
  secondary sources of section 2; detector facts of section 1.

Evidence.  `test_snippet.py` completeness and candidate-set assertions
  (the section 3 invariant) and the section 8 verification log.

Exit-codes.  `test_snippet.py`: 0 no FAIL, 1 any FAIL (fail-loud);
  detector instrument: 0 CLEAN, 1 RED, 2 usage error (section 1).

Files in this directory:

| file | role |
|---|---|
| `word-map.json` | 36 wording faces mapped to register-sourced replacement candidates |
| `SPEC.md` | this document |
| `test_snippet.py` | completeness assertions; segment to be merged into `tests/t_engines_seeds.py` by the tests-integration agent |

## 1. Detection face status (selfcheck instrument)

The working detector is a shell instrument:

- Path: `D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/ai_flavor_selfcheck.sh`
  (58 lines, cast on 12 November 2026).
- Batteries (one `command grep -c -E` pass each; counts are matching **lines**,
  not occurrences):

  | battery | faces | pattern location in instrument |
  |---|---|---|
  | `CH_3FAMILIES_10FACES` | 10 zh | line 29 (case sensitive) |
  | `EN_WORD_STEMS_15FACES` | 15 en stems | line 34 (case insensitive) |
  | `EN_SENTENCE_8FACES` | 8 en sentence faces | line 39 (case insensitive) |
  | `EN_PARA_INITIAL_3FACES` | 3 en paragraph-initial faces | line 44 (case insensitive, line-anchored) |

  Plus one separate em-dash battery (U+2014 occurrence count, target 0), which
  is **not** one of the 36 faces (see `structural_battery_em_dash` in the JSON).
- Exit codes: 0 = all batteries zero (CLEAN); 1 = any hit (RED); 2 = usage error.
- The instrument contains its pattern literals by design and excludes itself
  from its own assertion; the same exclusion applies to `word-map.json` and to
  the constants block of `test_snippet.py` (both are the battery data, so the
  wording batteries fire on them; the em-dash count must stay 0 everywhere).
- Location note: the instrument lives in the attn workspace, not in the
  rocqwash tree. The rocqwash tree carries document references only, verified
  on 14 November 2026 by `command grep -rn "ai_flavor" docs/ tools/`:
  `docs/CAPABILITY-INDEX.md:395,396,413`, `docs/mcp.md:120`,
  `docs/vacgen_sop.md:16,340,348`.
- Live runs this session (14 November 2026): a two-line plain-text probe gave
  `VERDICT CLEAN`, exit 0; a probe containing one zh face and one en stem gave
  `TOTAL_WORDING_LINES=2`, `VERDICT RED`, exit 1.

## 2. Sources and transcription discipline

- Primary canon (sole maintenance point, self-declared in its header):
  `D:/ComplexAnalysis/规范术语/术语表-通用-项目级-20260921.md`
  - section 4.6 (heading line 292 at the 14 November 2026 snapshot): row A (line 294)
    registers the 10 zh faces; row C (line 296) carries the false-positive
    boundary.
  - section 5 (heading line 381): the en face paragraph (line 402) registers
    the 15 stems, the 8 sentence faces, the 3 paragraph-initial faces, and
    their dispositions.
- Secondary source named in the charter:
  `D:/ComplexAnalysis/规范术语/注释规范白皮书-v1.0-20260921.md` section 4. Its
  mapping table contributes **none** of the 36 faces (that table is the E2
  jargon source); see negative finding NF2.
- Operating mirror cited by the instrument header:
  `C:/Users/Live/.zcode/skills/cw-wf-dispatch/references/constraint-blocks.md`
  section 13. Its en avoid list omits one stem relative to glossary section 5
  (see transcription_notes in the JSON). This map follows glossary section 5,
  which matches the instrument.
- Zero tampering: canon excerpts in the JSON are byte-faithful quotes,
  including the duplicated stem token and the "Morever" spelling in the canon's
  paragraph-initial chain. Face keys use the instrument's standard spellings.
  Amendments go to the canon first; this snapshot follows per the sync
  discipline.

## 3. word-map.json schema

Top level:

| field | meaning |
|---|---|
| `schema` | `rocqwash.seeds.ai-flavor.word-map/1.0` |
| `engine` | `ai_flavor` |
| `face_count` | 36 (must equal `len(faces)`) |
| `candidate_kinds` | meaning of each candidate kind |
| `candidate_scope` | family-level scope statement (no per-face table exists in the canon) |
| `source_of_truth` | canon paths, sections, snapshot dates, integrity rule |
| `detection_reference` | instrument path, battery literals, exit codes |
| `structural_battery_em_dash` | em-dash battery facts (excluded from the 36) |
| `faces` | 36 face entries |
| `canon_excerpts` | verbatim canon quotes keyed for citation |
| `transcription_notes` | fidelity notes (duplicated token, spelling, mirror gap) |

Face entry fields: `id`, `face`, `lang`, `battery`, `detector_regex_branch`
(verbatim branch of the instrument alternation), `match_mode`,
`canon_anchor`, optional `register_level` / `detector_note` / `canon_note`,
and `candidates`.

Candidate entry: `kind` (one of `ban-remediation`, `delete-or-restate`,
`neutral-direct-form`), `value`, `basis` (points at a canon excerpt key with
the verbatim fragment). Candidate semantics:

- zh faces (10): the register bans the face with **no compliant substitute**;
  candidates record that remediation, never a coined word.
- en stems (15): candidates are exactly the three neutral direct forms the
  register enumerates (`explore`, `examine`, `important`), applied per context.
- en sentence and paragraph faces (11): disposition is delete or restate.

Invariant enforced by tests: every candidate list is non-empty, every kind is
in the allowed set, and the en-stem candidate values equal the register-
enumerated set exactly (machine guard against coined words).

## 4. Replacement closure gap (wash_shape wiring, to grow)

Current state, verified first-hand on 14 November 2026:

- `tools/norm_lint.py` is report-only for wording faces; its parameterized
  jargon face is the E2 surface.
- `tools/wash_shape.py` is the applier (`--apply` flips plan mode to write
  mode) but has **no** jargon or ai-flavor face:
  `command grep -n "jargon" tools/wash_shape.py` returns nothing (exit 1), and
  `ai_flavor` / `word-map` probes over `tools/wash_shape.py` and
  `tools/norm_lint.py` return zero hits. The rocqwash `seeds/` directory does
  not exist yet (probe exit 2).
- No per-face substitution table for these 36 faces exists in the canon
  (NF1): the register gives one family-level guidance line for the stems and
  outright bans the zh faces without substitutes.

Consequence: mechanical substitution over this map would overstep the
register. The honest closure path, for the engine faces to grow in later
waves:

1. Wire the ai-flavor face into `wash_shape` as **advisory** suggestions:
   detection from this vocabulary, suggestion text taken from the candidate
   kinds (ban / delete-or-restate / neutral-direct-form with per-context
   note), with human or agent review before any write. Plan mode first, write
   mode only behind the existing `--apply` gate.
2. Alternatively (or additionally) amend the canon with a per-face
   substitution table at the sole maintenance point, then re-transcribe into
   this map and drop the family-level caveat.
3. Until one of the above lands, this seed powers detection and structured
   reporting only; it does not authorize automatic rewrites.

Integration note (the engine-body ticket, integrated this round).  Path 1 above
has landed: the detection body is `tools/ai_flavor.py`, the advisory apply
face is `tools/ai_flavor_apply.py` (three dispositions per candidate kind;
handoff default zero-network, http leg default-deny), and the wash_shape
integration is the advisory wash 7 stage whose apply arm only emits the
handoff package.  Mechanical substitution stays banned: every E1 write goes
through the rewrite provider (contract volume section 4, design change 4).
The original section text stands unchanged as the pre-integration record.

## 5. Boundaries carried from the canon

- Row C caution (quote kept in `canon_excerpts`): sentence-shaped faces are
  the weakest detection evidence; technical contrast sentences are legitimate
  after case-by-case review. Consumers of this map should treat sentence-
  battery hits as review items, not verdicts.
- em-dash: the register quota is at most 1 per 1000 characters; the
  instrument target is 0. Both are recorded, neither altered; the instrument
  target governs authored files in this effort.
- Register row A also lists one zh face (C-level sourcing, use with care)
  that is outside the instrument battery; it appears only inside the verbatim
  row A quote, not as a mapped face.

## 6. Negative findings (four-element boundary)

NF1. No per-face substitution table for the 36 faces exists in the canon.
  - Scanned: glossary sections 4.6 and 5 read in full this session (lines
    288-404 of the snapshot); the en face paragraph gives one family-level
    guidance line, row A gives no substitutes.
  - Not scanned: the full glossary file line-by-line outside the quoted
    ranges; the archive snapshots under `规范术语/archive_历史快照/`.
  - Scope: a negative finding of that scan, not an absolute claim.
  - Aliases: a per-face table under a different heading (for example a
    "replacement" or "candidate" table elsewhere in the glossary) was not
    exhaustively ruled out.

NF2. The commentary whitepaper section 4 mapping table contains none of the
  36 faces.
  - Scanned: section 4 read in full this session (lines 63-174); a
    `command grep -n` probe over four tokens (the zh register label plus the
    first three en stems of the battery; verbatim token list in
    `canon_excerpts.en_face_paragraph` of the JSON) returned 3 hits, none in
    table rows.
  - Not scanned: the remaining 32 faces were not individually grepped against
    that file; row-level fuzzy variants were not enumerated.
  - Scope: a negative finding of that scan, not an absolute claim.
  - Aliases: equivalent faces with different spellings or translations inside
    that table were not exhaustively ruled out.

NF3. The rocqwash tree has no ai-flavor wiring in the two tools and no
  `seeds/` directory.
  - Scanned: `command grep -n "jargon" tools/wash_shape.py` (exit 1, no
    output); ai-flavor and word-map probes over both tools (zero hits, exit
    1); `ls -d seeds` (exit 2). Document references only, at the lines listed
    in section 1. Dated 14 November 2026.
  - Not scanned: rocqwash git history objects; binary files; files outside
    the four text extensions probed by the earlier survey.
  - Scope: a negative finding of that scan, not an absolute claim.
  - Aliases: wiring under other names (for example a wording face or style
    face parameter) was not exhaustively ruled out.

NF4. No executable replacement closure for ai-flavor faces exists anywhere in
  the rocqwash tree today.
  - Scanned: follows from NF3 plus the document-reference-only finding of
    section 1; the only battery in play is the attn instrument (detection
    only, exit codes 0/1/2).
  - Not scanned: any sibling workspaces outside `D:/ComplexAnalysis` and the
    forbidden backup directory were not probed.
  - Scope: a negative finding of that scan, not an absolute claim.
  - Aliases: closure implemented outside the rocqwash tree (other sandboxes)
    was not exhaustively ruled out.

## 7. Restrictions honored

- No engine body: data JSON, this SPEC, and a test segment only.
- No writes to `README*`, `cw.sh`, `.github`, or any rocqwash tree path; this
  package lands exclusively in the staged seed area.
- JSON keys and SPEC prose in English; canon quotes stay verbatim in the data.
- The test segment is mergeable: standalone entry point plus import-safe
  functions; the integration agent points `WORD_MAP_PATH` at the merged tree
  layout (see the module docstring).

## 8. Verification log (all commands run on 14 November 2026)

| check | command | result |
|---|---|---|
| detector, clean probe | `sh ai_flavor_selfcheck.sh <2-line plain file>` | `VERDICT CLEAN`, exit 0 |
| detector, hit probe | `sh ai_flavor_selfcheck.sh <probe with 1 zh face + 1 en stem>` | `TOTAL_WORDING_LINES=2`, `VERDICT RED`, exit 1 |
| seed tests, positive | `python -I test_snippet.py` (this directory) | 8/8 checks PASS, exit 0 |
| seed tests, negative control | mutated map copy (one stem removed, declared count synced) run through the same tests | 3 assertions fired (count, coverage, battery mix), exit 1 |
| wash_shape wiring probe | `command grep -n "jargon" tools/wash_shape.py` in the rocqwash tree | no output, exit 1 |
| tools ai-flavor probe | `command grep -c "ai_flavor\|ai-flavor\|word-map\|word_map" tools/wash_shape.py tools/norm_lint.py` | 0 and 0, exit 1 |
| seeds dir probe | `ls -d /d/ComplexAnalysis/rocqwash/seeds` | exit 2, absent |
| doc reference probe | `command grep -rn "ai_flavor" docs/ tools/` | 7 lines, all in docs (section 1 list) |
| register check, this file | `sh ai_flavor_selfcheck.sh SPEC.md` | all batteries 0, em-dash 0, `VERDICT CLEAN`, exit 0 (run on the final bytes; one earlier draft line quoting the NF2 probe tokens was reworded to keep this file clean) |
| register check, test file | `sh ai_flavor_selfcheck.sh test_snippet.py` | wording lines fire by design on the embedded expected-face constants (CH 2 lines, en stems 6, en sentence 3); em-dash 0; exit 1, same excluded-data rationale as the instrument itself (section 1) |
