TICKET: R2-106 reshoot agent - RSI 21:11Z-22:0xZ window re-shoot (the 21:11Z
  ring slot did NOT run honest; re-shoot following the 16th/17th-ring
  re-shoot form R2-85/R2-93/R2-99); rsi-loop.log batch block landed
  (declared exception write face); zero repo-tree write by this agent;
  identity live-lumen
Purpose. RSI window re-shoot after the ring slot did not run honest: ground zero-write-form rerun of the six pkg steps in mktemp-mirror isolation, MCP jsonl face re-read, judgment vs the pre-arrival block. Ticket R2-106, agent live-lumen.
Interface. This card plus the receipt R2-106-receipt-beat.md; the declared exception write face is the rsi-loop.log batch block; canonical tree zero-touch; consumed by the dispatching workflow.
Dependencies. /Users/zuguangzhao/rocqwash MAIN clone; the loop clone at last-known tip c0b2811; the zgx-plan-run.sh pkg master (read first-hand); the b-gate-audit and learning_feedback tools; the mcp_call.sh helper; python3 -I only.
Evidence. All six steps rc 0 with mirror-isolation reads quoted inline and every reading taken this session; the pre-arrival writer identity is NOT established and is recorded NOT adjudicated.
Exit-codes. Six pkg steps rc 0; MCP server rc 0; zero network operations; the predecessor ring's not-honest face stands recorded as-is.

## Card body

STATEMENTS: ground face = this agent's own first-hand zero-write-form rerun
  of the six pkg steps (zgx-plan-run.sh section order, pkg master read
  first-hand this session) at loop HEAD c0b2811: steps 1-2 (b_gate_audit,
  learning_feedback) mktemp-mirror isolated per the R2-85/R2-99 form
  (mirror /tmp/rqw-mcp/r2-106/mirror.bBid7gOK, tools/ 89 files + docs/
  three ledgers copied byte-equal, copies cmp-verified pre-run, run cwd =
  mirror, mirror three inputs sha-unchanged post-run); steps 3-6
  (jargon_map_sync, pin_repair --plan, t_engines_seeds, t_engines_body)
  in-loop by-design zero-write; all six rc=0, all readings first-hand this
  session 2026/11/22 22:05-22:09Z. MCP face = /tmp/rqw-mcp/r2-106/
  mcp-bgate.jsonl(.text/.err) + mcp-lf.jsonl(.text/.err) (mcp_call.sh,
  ROCQWASH_HOME=/Users/zuguangzhao/rocqwash; raw jsonl read first-hand:
  row-ids [1,3], error None, isError false both faces). KEY NEW FACE: the
  exp-ledger growth R2-101 foresaw on MAIN has SYNCED into the loop tree
  (77 -> 82 rows, 022caa2e -> 057e9cad) and the learning_feedback triple
  MOVED 7/68/0.0909 -> 7/73/0.0854 at this beat (first post-growth
  first-hand reading; growth-attributed, not tool drift)
SOURCE ROUTING: ask (R2-106) names the six-step ground order, the MCP
  helper path and the two staging paths, the rsi-loop.log batch-block
  shape with the note-line template, this card path, and the receipt
  path; beat shape read from rsi-loop.log tail 15 (L168-192: 173436Z
  reshoot full form + `pre-seat` 211911Z five-element block); pkg master
  zgx-plan-run.sh (37 lines, workspace pkg-rsi-20261120/
  zgx-rsi-plan-package-20261120/05-scripts/, six-step order L23-34);
  w13 baseline card ai-flavor-trend-w13-20261123.md (anchor fb799bfe
  lineage) + R2-103-receipt-pr.md (post-cure baseline error=757
  warn=1195) read first-hand per the ask's preload; pin/fetch legs NOT
  run, anchor stays; re-shoot form precedents rsi-reshoot-20261123.md
  (R2-99, same-type master), R2-93 receipt stage-2, R2-85 receipt mirror
  law; H1 face precedent h1-shadelta-20261123.md (R2-101, baselines
  7877d61d/d279a8cd/022caa2e + MAIN +5-row observation)
COMPILE: none (zero-compile markdown card; no code produced or modified
  by this agent; all tool runs were existing tools invoked read-only or
  mirror-isolated)
REGISTRY: rsi-loop.log lines 186-192 (batch 20261122T220845Z
  anchor=c0b2811, appended by this agent, L185 was the `pre-seat` block's
  fifth element); R2-99 card (equal-form precedent, `pre-seat` block
  registered-not-adjudicated law); R2-85 receipt (mirror law + the three
  ledger sha256 baselines); R2-93 receipt (watch_only caliber law +
  step-2 equivalence law); R2-101 H1 card (022caa2e baseline + the MAIN
  +5-row out-of-scope observation this beat confirms synced); R2-103
  receipt-pr (PR #34 merge c0b2811 + post-cure norm baseline); pilot
  card rsi-mcp-pilot-20261122.md (write-face law: the write is the
  integration point, not the computation); receipt R2-106-receipt-beat.md

# RSI re-shoot beat 21:11Z-22:0xZ window (R2-106, 2026/11/22 UTC / 2026/11/23 local)

## 1. Ring-slot miss (honest face)

- The scheduled 21:11Z ring slot did NOT run (and no 22:0xZ slot ran
  either before this agent): the 21:1xZ face in rsi-loop.log is the
  `pre-seat` 211911Z block (L180-185, anchor=c0b2811), carrying the five
  elements and NO note and NO H1/sha face; no block exists between it
  and this agent's block. Writer identity of the `pre-seat` 211911Z block
  not established from session logs available to this agent: REGISTERED,
  NOT ADJUDICATED (R2-93 law).
- This agent's first-hand values match the `pre-seat` block value-for-value
  (verdict not-ready / VERDICT IN-SYNC (plan is zero-write) / action
  none / seeds-skips 3 / TOTAL-ENGINES-BODY GREEN 60 passed 0 skipped).
  The re-shoot block is L186-192 (batch 20261122T220845Z anchor=c0b2811),
  appended by this agent as the declared exception write face.
- What the `pre-seat` beat DID do (read from tree faces, not adjudicated
  as process): the loop tree moved 69dd18e -> c0b2811 (HEAD now
  c0b28115, commit "automerge: PR #34 (supply lane, head CI green)",
  committer date 2026-11-22T20:40:59Z), which synced docs/exp-ledger.jsonl
  to the 82-row face (file mtime 2026-11-22T21:19:12Z = the `pre-seat`
  beat's clock) and rewrote docs/b-gate-audit.json deterministically
  (mtime 21:19:12Z, md5 c3b88ece = the standing pinned dirty face).

## 2. Six-step ground readings (all rc=0, first-hand)

| # | step (pkg order) | where | rc | key face |
|---|---|---|---|---|
| 1 | b_gate_audit.py | mktemp mirror | 0 | verdict not-ready; 7 classes all not-ready (concl.real.const-lt-field-re-exists 1/1, jargon 1/1, other five 0/0); ready 0 of 3; remaining_to_b=3; errors=0; report md5 c3b88ece51b8f7e9378faf5a5aac418f == canonical pin |
| 2 | learning_feedback.py | mktemp mirror | 0 | rounds total=2 auto=1 human_approved=1 approval_rate_auto=0.5; repair repaired=7 escalated=0 watch_only_guard_correct=2 unrecorded=73 repair_action_rate=0.0854 (MOVED, see 4); calibration ledger_present=true entries=0 agreement_rate=None; feedback_edge open; errors=0; report md5 4deabad9668752a2950ac7fa9293b6f1 = fresh 82-row face |
| 3 | jargon_map_sync.py | in-loop | 0 | mode=plan; wrote=false; appended=0 updated=0 unchanged=122 retagged=0 authority_kept=4 rejected=17 entries=159 count=159; md_faces=143; stderr 0 B |
| 4 | pin_repair.py --plan | in-loop | 0 | ok=true action=none drifted=[] blocked=[]; upstream-absent=2 (annotation-whitepaper + terminology-general snapshots, md5 8876e13f/0eb8bf56 matched) both declared SKIP; verdict VERDICT IN-SYNC (plan is zero-write); stderr 209 B narrative (expected face) |
| 5 | tests/t_engines_seeds.py | in-loop | 0 | TOTAL-SELFTEST GREEN (43 passed); exactly 3 line-head SKIP rows (detector-anchor D:/ path + glossary source x2); stderr 206 B (expected fixture face) |
| 6 | tests/t_engines_body.py | in-loop | 0 | TOTAL-ENGINES-BODY GREEN (60 passed, 0 skipped); 60 PASS rows across 9 segments; stderr 0 B |

Zero-write assertions (measured pre and post all six steps): loop HEAD
c0b28115ea06de0ba791d9898fd573708984717a unchanged; loop porcelain
exactly 1 line (` M docs/b-gate-audit.json`, the standing pinned dirty
face) unchanged; loop report pins md5 c3b88ece (b-gate-audit.json) +
eac316848919d54490e4d2a1206585d9 (clean-tree scheduling-feedback.json
face) equal pre/post. Mirror isolation: step-1/2 reports landed INSIDE
the mirror only (mirror docs/b-gate-audit.json c3b88ece == canonical
pin; mirror docs/scheduling-feedback.json 4deabad9 = the fresh face);
the mirror's three inputs sha-unchanged post-run (7877d61d / d279a8cd /
057e9cad). Copy verification pre-run: 8 probed faces (3 ledgers +
taxonomy + 4 tools) cmp BYTE-EQUAL loop vs mirror.

## 3. MCP snapshot rows (same beat, stage-1/2) - sixth-consecutive EQUAL

| face | capture | protocol | fields | spot-check vs ground |
|---|---|---|---|---|
| b_gate_audit | /tmp/rqw-mcp/r2-106/mcp-bgate.jsonl(.text) | row-ids [1,3], error None, isError false, server rc=0 | 15 lines (exit-code header + 14 report lines) | EQUAL: after the exit-code-header strip, 14/14 lines value-identical vs mirror stdout, 0 diff fields |
| learning_feedback | /tmp/rqw-mcp/r2-106/mcp-lf.jsonl(.text) | row-ids [1,3], error None, isError false, server rc=0 | 8 lines (exit-code header + 7 report lines) | EQUAL: rows 1-6 value-identical; row 7 wrote-line `landing-spot` normalized per pilot law (canonical path vs mirror path) |

- Sixth-consecutive judgment: the five prior EQUAL faces on this lane
  are 115443Z PILOT (b_gate equal), 134617Z stage-2 (learning_feedback
  equal, P-1 closed), 141907Z PILOT-2 (two-face swap equal), 173436Z
  re-shoot (stage-1/2 value-identical spot-check EQUAL) counted
  per-face = five consecutive (PILOT-2 carried both faces); this beat is
  the SIXTH consecutive EQUAL. Series stands VERIFIED x6, same-beat
  same-anchor discipline held (loop c0b2811 vs MAIN HEAD 5abd0c0: the
  delta commit 5abd0c0 touches ONLY zgx-out/zgx-ledger-proposals.jsonl
  +3 rows - zero computation inputs; all probed computation inputs cmp
  BYTE-EQUAL loop vs MAIN working trees this session, so the MCP/ground
  comparison is computation-invariant).
- Computation values carried by both faces (fresh 82-row state): verdict
  not-ready / remaining_to_b=3 / errors=0; triple 7/73/0.0854; rounds
  2/1/1/0.5; calibration present/0/None; feedback_edge open.
- Canonical-tree write-face handling (R-1 face, measured): the MCP
  learning_feedback call rewrote MAIN docs/scheduling-feedback.json and
  the canonical md5 MOVED 28c85e049f96790aea2470188abec6f0 ->
  4deabad9668752a2950ac7fa9293b6f1 - this is the deterministic
  fresh-face rewrite (the first movement of this pin since R2-85; the
  old 28c85e04 face was the 77-row computation, the new 4deabad9 face is
  the 82-row computation, and it is BYTE-IDENTICAL to the mirror's own
  fresh output - same inputs, same bytes, integration point is the only
  difference). docs/b-gate-audit.json md5 c3b88ece EQUAL pre/post (its
  computation inputs did not move). MAIN porcelain shape unchanged (2 M
  + 3 untracked); MAIN HEAD 5abd0c0 read-as-found, untouched; loop tree
  untouched by the MCP calls (they bind ROCQWASH_HOME=MAIN only).

## 4. learning_feedback triple current state + H1 sha-delta judgment

- Triple MOVED this beat: 7/68/0.0909 -> 7/73/0.0854. repaired flat 7
  (fourth consecutive beat at 7); unrecorded 68 -> 73 = EXACTLY the +5
  new exp-ledger rows (mechanical attribution, first-hand: numstat
  69dd18e..eb996ab on docs/exp-ledger.jsonl = +5/-0; every new row is an
  unrecorded exp face, zero rewrites of old rows); rate 0.0909 ->
  0.0854 (7/82 = 0.08536..., tool face; watch_only-inclusive caliber per
  R2-93 law: 7/(73+7+2) = 7/82; the unrecorded-only fraction is
  7/73 = 0.0959 - both stated, no new verdict added).
- H1 sha-delta face (the ask's named judgment), all first-hand this
  session, loop tree:
  - docs/round-ledger.jsonl sha256 7877d61d5c9f267575e2590e4bc174a
    2f13362062d4e33ae0dec650ab6331995 - BYTE-EQUAL to baseline, flat.
  - docs/round-state.json sha256 d279a8cdda582067bdc55b420858a5aabceb
    07413fc3a88ead9493afcc5892c4 - BYTE-EQUAL to baseline, flat.
  - docs/exp-ledger.jsonl sha256 057e9cadaa403ea7c274934afd29bab22d109
    f79d9d580a3e54c274ee515ecc6 - MOVED vs baseline 022caa2ecf51b528523
    0efc3bf19965d985036a92386081ec815094e51e22546; delta = +5 rows
    (77 -> 82), PURE APPEND zero rewrite (first-hand prefix test:
    head -77 | shasum -a 256 = 022caa2e... EXACT).
- Judgment: the 24-ring-baseline three-ledger byte-equal continuation is
  BROKEN on the exp-ledger leg (2 of 3 legs hold: round + state). The
  growth event is eb996ab ("docs(ci): whitepaper section 13 ... triage
  class R24", +5 rows: ci-watch / ci-realreds / mcp-probe exp faces) -
  the very face R2-101 measured on the MAIN tree as an out-of-scope
  observation and predicted would meet the next beat's digest test "when
  the loop tree syncs it". It synced at the `pre-seat` 21:19Z beat
  (checkout to c0b2811) and THIS beat is the first first-hand post-growth
  reading: the H1 digest test is MET, the flat chapter closes with a
  real growth event, and the triple move 68 -> 73 / 0.0909 -> 0.0854 is
  the mechanical consequence (growth-attributed, not tool drift: tools/
  all cmp BYTE-EQUAL loop vs MAIN and the mirror re-run reproduces both
  faces). Loop and MAIN exp-ledger are byte-equal again as of this beat
  (cmp pass), so the next growth window starts from a synced 82-row base.
- observation line (triple): 3/46 -> 5/53 -> 7/59 -> 7/68 (R2-85 series)
  -> 7/68 -> 7/68 (R2-93, R2-99, R2-101 flats) -> 7/73 (this beat, +5 =
  eb996ab rows). Numerator 7 flat across all seven readings; the
  denominator is row-driven, not beat-driven.

## 5. NETRED and write faces

- Zero network operations by this agent: no fetch attempted (anchor
  stays c0b2811 per D-3/R2-93 form), no curl, MCP helper is stdio-local
  (ROCWASH_HOME pinned inside the helper; ROCQWASH_MCP_ALLOW_NET never
  set, never forced; deny faces untouched).
- Write faces exactly: rsi-loop.log L186-192 (declared exception write
  face, appended once from a staging file, verified landed 185 -> 192
  lines) + this card + receipt R2-106-receipt-beat.md + /tmp/rqw-mcp/
  r2-106/ staging (mirror.bBid7gOK, g-step1..6.out/.err, mcp-bgate
  .jsonl/.text/.err, mcp-lf.jsonl/.text/.err, mirror-path.txt,
  batch-block.txt). Zero hand-written writes inside either repo tree;
  the only repo-side byte movement is the MCP-derived-report rewrite on
  MAIN (section 3 R-1 face, deterministic, 28c85e04 -> 4deabad9) and the
  loop tree is byte-identical pre/post all six steps.
- Anchor faces read-as-found (no action taken): loop HEAD c0b2811 ==
  the `pre-seat` block's anchor; MAIN local HEAD 5abd0c0 ("docs(proposals):
  zgx ledger rows 30-32", committed 2026-11-22T21:39:33Z, one commit
  past c0b2811, touching only zgx-out proposals); origin/main refs not
  read network-side by this agent.

## 6. Not run (not named by this ask)

- pin_repair --apply (apply never in scope); any fetch/pin leg; steps
  3-6 via MCP (roster-absent faces, R2-92/R2-93 law unchanged); the
  ai_flavor/norm_lint scan battery (w13 lane - not named by this ask;
  the ask's three-value face is the learning_feedback triple, section
  4); per-row exp-ledger forensics beyond the prefix/digest test;
  adjudication of the `pre-seat` 211911Z block's writer identity or the
  MAIN 5abd0c0 commit (both read-as-found, registered not adjudicated);
  any write into either repo tree by hand.
