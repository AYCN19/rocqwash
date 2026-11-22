# MCP roster 50 -> 51 wire-face verification (R2-92, 20261122)

- Ticket: R2-92 (expansion-verification seat; read-only ring: zero
  repo-tree writes; write faces = this card, the receipt
  R2-92-receipt-roster.md, and /tmp/rqw-mcp/r2-92 staging only)
- Statement faces verified: (a) wire tools/list roster count 51 ==
  the fourteen-ring source-face discovery 51 (R2-91 card section 2.1);
  (b) vacgen_coq_generate inputSchema read per-parameter off the wire
  capture; (c) tests/t_mcp_face.py re-run at the ask-named command,
  51-capability assertion PASS rc 0; (d) vacgen_coq_generate empty-args
  wire call, usage-error fail-loud form, no compile leg spent; (e) zgx
  ledger rows 28/29 five-face cross-check against the 51 roster.
- Source routing: working clone /Users/zuguangzhao/rocqwash detached
  HEAD == origin/main == 35c9ecf7dda1fbc8c9c4f5c2f2669507537a2207
  (rev-parse measured at seat start and again at close, identical);
  dirty faces exactly 2 M (docs/b-gate-audit.json md5
  c3b88ece51b8f7e9378faf5a5aac418f, docs/scheduling-feedback.json md5
  28c85e049f96790aea2470188abec6f0) + 3 untracked zgx-out files,
  byte-identical pre/post all seat actions; branch-side supply commit
  3ccc947 one parent-hop behind the detached tip.
- Compile command lines: (1) `bash -c 'cd /Users/zuguangzhao/rocqwash
  && /usr/bin/python3 -I tests/t_mcp_face.py 2>&1 | tail -6; echo RC=$?'`
  (ask-verbatim form; RC measured 0) plus a capture-form re-run
  (`/usr/bin/python3 -I tests/t_mcp_face.py > out 2> err; echo PYRC=$?`,
  PYRC=0, stderr empty); (2) `bash <workspace>/_scripts/mcp_call.sh
  vacgen_coq_generate '{}' /tmp/rqw-mcp/r2-92/call-vacgen_coq_generate
  .jsonl` (helper pins ROCQWASH_HOME=/Users/zuguangzhao/rocqwash; stdio
  face; allow-net=False per stderr); (3) tools/list emission driver
  /tmp/rqw-mcp/r2-92/emit_tools_list.py (mirrors the helper handshake
  lines 15-19 byte-form, request method switched to tools/list; same
  ROCQWASH_HOME pin, same interpreter -I, same server --stdio entry).
- Related registration: R2-91 card new-anchor-readings-20261122.md
  (source-face 51 discovery + carried wire-re-emission obligation);
  zgx-out/zgx-ledger-proposals.jsonl rows 28/29 (proposal faces);
  docs/mcp.md section 3 (51-row table, vacgen_coq_generate last row,
  line 119); mcp-surface-census-v2 card section 5 registration law
  (cited by ledger row 28).

## 1. Wire tools/list emission and roster count (ask item 1)

Honesty note first: the ask-named staging artifact
/tmp/rqw-mcp/r2-92/tools-list.jsonl was ABSENT at seat start (the
directory /tmp/rqw-mcp/r2-92/ itself did not exist; the ask's
pre-check transcript slot also arrived empty). No pre-check face was
passed to this seat. Per the discipline the staging write is inside
this seat's declared write face, and the re-emission is exactly the
obligation R2-91 section 6 carried ("wire tools/list was NOT
re-emitted ... carried as the next supply face's obligation"), so this
seat emitted it fresh: driver /tmp/rqw-mcp/r2-92/emit_tools_list.py,
one initialize/initialized/tools-list sequence into
`/usr/bin/python3 -I /Users/zuguangzhao/rocqwash/tools/mcp_server.py
--stdio` with ROCQWASH_HOME pinned, raw protocol lines landing at the
ask-named path. server rc 0, id==3 response carries no error object.

Readings:

- WIRE_ROSTER_COUNT = 51 (parsed from the id==3 result.tools array of
  /tmp/rqw-mcp/r2-92/tools-list.jsonl, first-hand this seat).
- Agreement against the fourteen-ring source face: 51 == 51 EXACT.
  The R2-91 card section 2.1 measured the source face (mcp_server.py
  diff f75ffa0..35c9ecf7 carries exactly one added roster entry;
  wire-schema "name"-key grep count 56 -> 57; t_mcp_face 51-name
  assertion), and this seat's wire emission now lands on the same
  number from the wire side.
- Agreement against docs/mcp.md section 3: the capability column of
  the section 3 table parses to exactly 51 rows and the ordered
  name-list comparison is EQUAL (wire list == mcp.md list, mechanical
  diff run, zero names either side); last row both sides =
  vacgen_coq_generate. Two of the three standing roster-guard sources
  (wire == mcp.md section 3) re-measured equal this seat; the third
  (INDEX render) was NOT re-emitted this seat (not named by the ask;
  carried, see section 6).
- Roster tail (names 43-51 in wire order): tree_audit, axiom_sweep,
  claim_watch, source_fetch, sweep_verdict, release_chain,
  numeric_probe, statement_probes, vacgen_coq_generate - the
  vacgen_coq_generate entry is the single new face versus the R2-87
  wire capture of the 50-face (whose parsed count 50 is cited
  first-hand inside ledger row 28).

vacgen_coq_generate schema face (read off the wire capture,
inputSchema per-parameter):

- additionalProperties = false; required = [] (empty - every
  parameter optional at the guard, so a bare `{}` call passes the
  -32602 enum/value guard and reaches the child; see section 4).
- from_v: type string - "batch input: a .v file, or a directory whose
  *.v files are walked recursively (.git skipped); tool-required for
  the batch face; --selftest runs without it; CLI flag --from-v".
- taxonomy: type string - taxonomy table path (chain: this flag, then
  the VACGEN_COQ_TAXONOMY env, then the tool-adjacent
  taxonomy-coq.json, then the builtin starter row); CLI flag
  --taxonomy.
- out: type string - batch output root (default vacgen_coq_batch_out
  under the repository root); the only disk face the batch face
  writes, one JSON per statement plus summary.json under it; CLI flag
  --out.
- limit: type integer - cap the number of statements processed after
  enumeration (must be a positive integer, usage error rc 2
  otherwise; counted in summary.input.limitApplied); CLI flag
  --limit.
- selftest: type boolean - run the in-process offline vector face and
  exit (takes no other flag): taxonomy-load vector, recognition
  vectors over the fixture known families, unknown-shape todo_seat
  vector, hole-face degradation (description truncated at 200 chars
  in this card; full text in the wire capture).

## 2. t_mcp_face re-run (ask item 2)

Ask-named command, run verbatim (single-quoted so RC=$? evaluates
inside the named shell):

```
bash -c 'cd /Users/zuguangzhao/rocqwash && /usr/bin/python3 -I tests/t_mcp_face.py 2>&1 | tail -6; echo RC=$?'
```

Output (complete - the suite's stdout is a single line, so tail -6 is
that line):

```
T-MCP-FACE SUITE SHELL PASS (9 probe groups, 51 capabilities, 9 live-call spot checks)
RC=0
```

Supplementary capture-form re-run for the true interpreter rc (the
named form's `$?` measures the pipeline tail): PYRC=0, stderr 0
bytes, stdout 1 line, same PASS line, archived at
/tmp/rqw-mcp/r2-92/t_mcp_face.out/.err. The suite internally asserts
`names != EXPECTED_TOOLS -> fail` (tests/t_mcp_face.py:477) with
EXPECTED_TOOLS frozen at tests/t_mcp_face.py:154; its PASS at rc 0 is
the 51-name assertion holding at HEAD.

EXPECTED_TOOLS drift face (ask-named "42 old word-face vs 51 new
face"), measured honestly:

- At HEAD (35c9ecf7): EXPECTED_TOOLS holds 51 names.
- At the prior window anchor f75ffa0 (blob locally readable): 50
  names. Delta f75ffa0 -> HEAD: +vacgen_coq_generate exactly, zero
  removed - the assertion moved one-for-one with the roster.
- The 42 word-face is NOT locally reconstructible from this clone:
  `git rev-list HEAD -- tests/t_mcp_face.py` returns exactly one
  visible commit (caaf920, the registration-lag commit that landed
  the 51 face); earlier commits touching the file sit beyond the
  shallow depth and their trees are unreadable (`git log --follow`
  and per-commit blob reads both fail with "unable to read tree",
  measured). Whether an earlier era of the assertion held 42 is
  recorded as unverifiable-here, not adjudicated; the two locally
  measurable points are 50 (f75ffa0) and 51 (HEAD), and the ask's
  "42" is not among them.

## 3. vacgen_coq_generate empty-args wire call (ask item 3)

Call form (helper, ask-named):

```
bash /Users/zuguangzhao/.zcode/workspace/f440121c-6adb-4a16-8c3b-ed64a23b0458/_scripts/mcp_call.sh vacgen_coq_generate '{}' /tmp/rqw-mcp/r2-92/call-vacgen_coq_generate.jsonl
```

Readings (raw capture + parsed .text + .err at the ask-named paths):

- server rc 0; RPC layer clean (no -32602/-32601/-32700 - the empty
  args DO pass the wire guard, matching required=[] in section 1);
  isError = true, carried fail-loud per the result-shape law
  (docs/mcp.md section 3 note 4: any non-zero rc yields isError:true).
- content text (complete): `exit code: 2` header, the argparse usage
  block `usage: vacgen-coq [-h] [--from-v FROM_V] [--taxonomy
  TAXONOMY] [--out OUT_DIR] [--limit LIMIT] [--selftest]`, and the
  line `FAIL-LOUD: --from-v <file|dir> is required in batch mode
  (usage error, rc=2)`.
- Form judgment (recorded as-is): with required=[] and neither from_v
  nor selftest supplied, the guard lets the call through and the
  child answers the bare invocation with its designed usage-error rc
  2 - the empty-args form is the usage face, not a batch face. No
  coq compile leg was spent and none exists in this tool's design
  (docs/mcp.md:119: "zero network, zero compile, no Rocq process is
  ever started"); no batch enumeration ran, and the default out root
  never materialized (`vacgen_coq_batch_out` absent from the clone
  root, checked post-call). The selftest vector face was NOT spent
  this seat (the ask names the empty-args form only).
- Deny face: stderr carries `allow-net=False`; ROCQWASH_MCP_ALLOW_NET
  never set this session; zero network spent by the call.

## 4. Proposal landing judgment: zgx rows 28/29 vs the 51 roster (ask item 4)

Material read first-hand: zgx-out/zgx-ledger-proposals.jsonl rows 28
and 29 (the two rows f38b0bc landed to the console side, per the
R2-91 card section 2 commit face and this seat's ledger read).

- Row 28 (kind proposal, MCP roster expansion): the expansion set it
  lands is FOUR candidate faces - jargon_map_sync, pin_repair,
  engines_seeds, engines_body (dependency-safe order, each under the
  census-v2 section 5 registration law, each "expose plan/selftest
  only, write-bearing legs stay CLI-side"). The row itself registers
  the five-vs-four deviation: the ask wording had named FIVE faces
  including learning_feedback, but learning_feedback was already
  rostered (wire #28 + docs/mcp.md section 3 row + INDEX entry),
  so the row's expansion set is the four roster-absent faces and
  learning_feedback's residual item (default-run {} value-equivalence
  measurement) is a stage-2 candidate, not a roster expansion.
  Row 28's proposal target line reads "moves the roster guard
  50==50==50 to 54==54==54" (four additions).
- Row 29 (kind proposal, census closeout): not a registration row -
  it asks that whichever workflow first produces the production input
  artifacts re-runs the four W faces (ledger_sync, i18n_pipeline_
  dryrun, verdict_diff, sweep_verdict) once each; the W registrations
  themselves stand.

Judgment face (ask item 4, both halves):

1. Is vacgen_coq_generate one of the proposal faces? NO - measured,
   not assumed. The proposal faces of rows 28/29 are
   {learning_feedback (stage-2 residual), jargon_map_sync, pin_repair,
   engines_seeds, engines_body} + the four W faces of row 29;
   vacgen_coq_generate appears in neither row (string-absent from
   both row bodies, and it is not one of the four candidate names).
   Family diagnosis, recorded as-is: the proposal candidates are
   plan/selftest faces of existing CLI/test files (a different family
   from the Rocq-domain batch face); vacgen_coq_generate arrived by
   the console side's own registration line (caaf920, ticket 14 wave
   1, self-described as riding the repair_scope tolerance fix) - the
   console-side self-expansion and the zgx candidate lane are TWO
   PARALLEL LINES that did not meet in this window: the candidate
   lane's four faces did not ride caaf920, and the console's new face
   was not one of the candidates.
2. Are the five proposal faces in the 51 roster? Checked face by face
   against the first-hand wire list: learning_feedback PRESENT
   (wire #28, the M1 registration the deviation note cites);
   jargon_map_sync ABSENT; pin_repair ABSENT; engines_seeds ABSENT;
   engines_body ABSENT. The four candidate faces' absence from the
   roster is the mechanical precondition for the candidate lane to
   keep waiting: per the rows' own law (a capability joins only with
   its own implementation ticket moving roster count line, wire
   tools/list, and section 3 table together), all four stay
   pending-their-tickets (the candidate seats remain unlanded), and
   the row 28 target face is now 51==51==51 pending -> 54==54==54
   when they land, not yet.

## 5. Pin and dirty-face continuity (seat discipline)

Measured pre-seat and re-measured after every repo-adjacent action
(tools/list emission, both t_mcp_face runs, the vacgen call):

- docs/b-gate-audit.json md5 c3b88ece51b8f7e9378faf5a5aac418f -
  IDENTICAL at seat start and at close (the c3b88ece pin holds).
- docs/scheduling-feedback.json md5 28c85e049f96790aea2470188abec6f0
  - IDENTICAL at seat start and at close (never touched; the two
  suite runs and the MCP calls did not regenerate it - the empty-args
  call usage-errored before any write, and t_mcp_face's live-call
  spot checks are out-of-tree per the suite's own design, corroborated
  by the unchanged status face).
- `git status --porcelain` at close: exactly
  ` M docs/b-gate-audit.json` + ` M docs/scheduling-feedback.json` +
  the 3 untracked zgx-out files - byte-identical to seat start.
- HEAD still detached at 35c9ecf7 == origin/main at close. Zero
  checkout, zero -f, zero tree writes by this seat.

## 6. Not run (not named by this ask)

- The INDEX render re-emission (the third roster-guard source): not
  named; the two-source agreement wire == mcp.md section 3 is
  first-hand this seat, the three-source agreement stays carried.
- learning_feedback default-run {} value-equivalence measurement
  (row 28's stage-2 candidate; the P-1 gate face stays open).
- The vacgen_coq_generate `--selftest` vector face and any real batch
  face (the ask bounds this seat to the empty-args form; no compile
  leg exists in the tool's design and none was sought).
- The row 29 W-face re-measurements (awaiting the production input
  artifacts, per the row's own proposal).
- Any network call: NETRED ledger empty this seat - zero fetches,
  zero API faces; all emissions were local stdio (2 tool/list-class
  drives: the roster emission + the helper call; the t_mcp_face suite
  internally makes its own 9 live-call spot checks in-process).

## Provenance and limitations

- Staging (all outside the repo tree): /tmp/rqw-mcp/r2-92/
  (tools-list.jsonl + .err, emit_tools_list.py, call-vacgen_coq_
  generate.jsonl + .text + .err, t_mcp_face.out/.err, commits.txt,
  fetch.err [0-byte pre-seat remnant, never written by this seat]).
- Comparators read first-hand: R2-91 card (source-face 51, carried
  obligations), zgx ledger rows 28/29, docs/mcp.md section 3,
  tests/t_mcp_face.py (assertion line 477, EXPECTED_TOOLS line 154),
  the helper script _scripts/mcp_call.sh (handshake mirrored).
- Limitations: shallow clone (only caaf920 visible for
  tests/t_mcp_face.py history) bounds the EXPECTED_TOOLS drift
  reconstruction to the two measured points 50/51; the ask's 42
  word-face stays unadjudicated; the INDEX render source not
  re-measured.
- Receipt: R2-92-receipt-roster.md (sibling directory, written after
  this card).

Receipt line:
`R2-92 DONE roster 50->51 WIRE-FACE VERIFIED @35c9ecf7 (HEAD==origin/main detached, dirty pair md5 c3b88ece+28c85e04 + 3 untracked byte-identical pre/post all actions, zero repo writes): staging artifact tools-list.jsonl ABSENT at seat start + pre-check transcript slot EMPTY -> this seat emitted fresh (emit_tools_list.py mirrors helper handshake, tools/list form, server rc 0) - WIRE_ROSTER=51 == source-face 51 (R2-91 sec 2.1) == docs/mcp.md sec-3 parsed 51 rows EXACT ordered-equal both sides (three-source agreement: two sources re-measured, INDEX render not re-emitted, carried); vacgen_coq_generate #51 closes roster, inputSchema: required=[] additionalProperties=false 5 params from_v:str/taxonomy:str/out:str/limit:int/selftest:bool; t_mcp_face ask-verbatim PASS rc 0 'T-MCP-FACE SUITE SHELL PASS (9 probe groups, 51 capabilities, 9 live-call spot checks)' + capture-form PYRC=0 stderr 0B (asserts names==EXPECTED_TOOLS at line 477, frozen line 154); EXPECTED_TOOLS drift MEASURED 50@f75ffa0 -> 51@HEAD delta +vacgen_coq_generate only, ask's 42 word-face NOT locally reconstructible (shallow: only caaf920 touches the file, older trees unreadable 'unable to read tree') - recorded unverifiable-here; vacgen_coq_generate {} via helper: guard passed (required=[]), child usage-error rc 2 isError=true fail-loud 'FAIL-LOUD: --from-v <file|dir> is required in batch mode', NO compile leg (tool design zero-compile, none sought), vacgen_coq_batch_out never materialized, selftest vector face not spent, allow-net=False; proposal judgment: vacgen_coq_generate NOT a row-28/29 proposal face (string-absent both rows; candidates are plan/selftest faces, different family) - console-side self-expansion (caaf920 ticket 14 wave 1) and zgx candidate lane = TWO PARALLEL LINES unmet this window; five proposal faces vs 51 roster: learning_feedback PRESENT (#28, its residual default-run equivalence = stage-2), jargon_map_sync/pin_repair/engines_seeds/engines_body ALL ABSENT -> candidate seats stay pending their implementation tickets (row-28 target 54==54==54 untriggered), row-29 W faces all PRESENT registered; NETRED zero spent, MCP stdio emissions 2 + suite-internal spot checks; anchor locked around all actions 2026-11-22`
