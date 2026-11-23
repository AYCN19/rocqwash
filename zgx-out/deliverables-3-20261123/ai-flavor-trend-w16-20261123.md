# ai_flavor trend card - em-dash / wording / norm faces, rocqwash (R2-110, window w16)

Purpose. Trend sampler window w16: anchor face verify (new anchor
  6af8067 = the PR#37 norm-cures integration composition), PAID re-scan
  (skip branch open but NOT taken - the new anchor landed, rev-list
  2 > 0), double scan (ai_flavor + norm_lint, ground CLI form,
  read-only), tree-level recheck of the fix face, row-level diff,
  counter judgment. Ticket R2-110, agent live-lumen (subagent,
  dynamic workflow).
Interface. This card (English ASCII, five-field header per the norm
  header rule; non-ASCII gate = 0 bytes measured post-write) plus
  the receipt R2-110-receipt-w16.md; consumed by the dispatching
  workflow.
Dependencies. /Users/zuguangzhao/rocqwash MAIN clone (read-only
  this agent), python3 -I, git, tools/ai_flavor.py,
  tools/norm_lint.py, w15 card + w15 staging, R2-109-receipt-pr.md
  (the fix integration face), rsi-loop.log tail 15; no MCP helper.
Evidence. Every value below was measured this session with the
  quoted command forms; staging /tmp/rqw-mcp/r2-110-w16/ holds all
  raw outputs; anchor 6af8067 network-verified via the ask-named
  fetch (the refmove is carried by THIS fetch - see section 1).
Exit-codes. fetch rc 0 single-flight (refmove 7b183ed..6af8067
  carried, zero retries); ai_flavor rc 1 RED (standing data face)
  x2 passes byte-identical (md5 pair == w15's pair EXACT);
  norm_lint rc 0 report-only x2, summary line byte-equal, json
  pass2 cmp BYTE-IDENTICAL.

## Card body

- Ticket: R2-110, agent: trend sampler w16 (read-only sampling; zero
  repo-tree content; write faces = this card, the receipt
  R2-110-receipt-w16.md, and /tmp/rqw-mcp/r2-110-w16 staging),
  identity live-lumen
- Date: 2026/11/23 (local calendar; the ask-named filename carries
  2026/11/23 and is written exactly as named)
- Target repo: /Users/zuguangzhao/rocqwash (MAIN clone; scanned
  read-only at the working tree, which is tree-identical to the
  anchor - see section 1; NO checkout performed at all this window)
- FINAL anchor: 6af8067ebf21ebe33a923500fea9cd6934c2e148 =
  origin/main at scan time (== the ask's expected 6af8067 EXACT ==
  R2-109's recorded merge_commit_sha EXACT, network-confirmed; the
  scans sampled THIS tip's tree)

## 1. Anchor face: fetch rc 0 single-flight, the refmove CARRIED by this fetch, rev-list 2 == the ask's expected 2 EXACT, window = the PR#37 norm-cures integration

- Pre-fetch face (measured at agent open): HEAD =
  71803083016e7deaf13881e7f11a271aac6a25a3 (the R2-109 fix head)
  attached to branch supply/zgx/deliverables-2-norm-cures-20261123
  (the R2-109 leave-behind, untouched by this agent); porcelain =
  exactly 3 M (docs/b-gate-audit.json, docs/scheduling-feedback.json,
  zgx-out/zgx-ledger-proposals.jsonl) + 3 untracked zgx-out files -
  ONE M MORE than the w15 face (2 M + 3 untracked): the third M is
  the zgx-ledger-proposals.jsonl concurrent-append face R2-109
  recorded `mid-seat`, still standing dirty at this window's open;
  as-recorded, not adjudicated. Local origin/main was 7b183ed
  (pre-fetch) - R2-109's check-3 and post-merge fetches both FAILED
  (Empty reply, rc 128, recorded in its receipt), so the local ref
  never saw the merge; THIS agent's ask-named fetch carries the
  move.
- The ask-named fetch ran exactly once: `git -C /Users/zuguangzhao/
  rocqwash -c http.version=HTTP/1.1 fetch origin` - rc 0, ONE
  attempt, HTTP/1.1 forced, zero retries, zero backoff; stderr 98
  bytes = "7b183ed..6af8067 main -> origin/main" - UNLIKE w13/w14/
  w15 (all zero-refmove), this fetch carries the refmove, as
  expected from the R2-109 fetch-failure leave-behind.
- `git rev-parse origin/main` = 6af8067ebf21ebe33a923500fea9cd6934
  c2e148 == the ask's expected 6af8067 EXACT == R2-109-receipt-pr.md
  merge_commit_sha EXACT. `git rev-list --count
  7b183ed869efba0a07b027a7bffd643b8ec569fc..origin/main` = 2 == the
  ask's expected window EXACT (the ask named the window correctly,
  w15-form).
- Per-commit enumeration, each classified: 7180308 (parent 7b183ed)
  = the R2-109 fix head "docs(deliverables): norm cures over
  readings batch 2 [ONE U+2014 em-dash in the raw subject here]
  stem-free transcription over cure-plan wordform listings" - the
  em-dash is commit METADATA, outside both instruments' scan face
  (w15/89acc8a precedent); 6af8067 (parents 7b183ed + 7180308) =
  "automerge: PR #37 (supply lane, head CI green)" == R2-109's
  recorded merge_commit_sha EXACT = the new anchor.
- Window diff face: `git diff --name-only 7b183ed..origin/main` =
  9 paths, ALL under zgx-out/deliverables-2-20261123/ (MANIFEST
  untouched by design, R2-109 G6). `git diff --shortstat
  7b183ed..origin/main` = 9 files changed, 685 insertions(+), 612
  deletions(-) == R2-109 receipt EXACT (the 612 numstat deletions
  are substituted lines, not net deletions - see the wc -l closure
  in section 3).
- Instruments byte-stable across the window: `git diff --stat
  7b183ed..origin/main -- tools/ai_flavor.py tools/norm_lint.py
  seeds/ai_flavor/word-map.json` EMPTY rc 0 (comparability holds).
- Scan-equivalence face: `git rev-parse 7180308^{tree}
  6af8067^{tree} HEAD^{tree}` all =
  d8fceeec6b5490e204077e888b409188cea27047 - the PR#37 automerge is
  TREE-IDENTICAL to its branch head (PR#33/PR#35/PR#36 precedent)
  and HEAD carries that tree, so the scans sampled the anchor face
  with ZERO checkout and ZERO repo-tree writes (w15-strength form).
  For contrast 7b183ed^{tree} = cb9ad746... (the w15 tree).
- Close face: HEAD 7180308 and origin/main 6af8067 unchanged at
  close; porcelain same 3 M + 3 untracked at close; dirty pins md5
  c3b88ece (b-gate-audit, == the w15 canonical pin EXACT),
  4deabad9 (scheduling-feedback, == the w15/w14 CLOSE pin EXACT),
  b61b7d26 (ledger-proposals, the R2-109 leave-behind) - no
  `mid-seat` movement this window.

## 2. Double scan vs the w15 baseline AND vs the R2-109 post-fix face (every value judged)

Baseline 1: w15 @7b183ed (em 7936 / wd 265 / rows 332 / error 1177
  / warn 2211 / files 329 / cjk_ratio 0.028760 / findings 3388 /
  hits 412 = 173/197/42 - w15 card read first-hand).
Baseline 2: R2-109 post-fix face (error 763 / warn 1263 / files 329
  / cjk_ratio 0.028635 / lane findings 74 = 68 warn + 6 error /
  cured 1362 - R2-109-receipt-pr.md read first-hand).

Form note: ground CLI form, cwd = clone root: `python3 -I tools/
  ai_flavor.py --tree .` and `python3 -I tools/norm_lint.py --tree .
  --json <path>`. The --tree flag was verified in source this
  session (tools/ai_flavor.py:437, tools/norm_lint.py:911,
  mutually exclusive with --file at :935-937). Second passes:
  ai_flavor stdout md5 b47d75f1d5e3d9329e48f0668b20764e BOTH passes
  == the w15 pair value EXACT (the whole stdout is byte-identical
  to w15's); norm_lint pass2 json cmp BYTE-IDENTICAL to pass1, the
  summary line byte-equal (the only stdout difference is the json
  path echo on line 2 - pass 2 wrote a different path, expected).

| face | w15 @7b183ed | w16 @6af8067 | delta | judgment |
|---|---|---|---|---|
| ai_flavor rc | 1 RED | 1 RED | 0 | standing data face |
| em (EM_DASH_U2014) | 7936 | 7936 | 0 | fix zero-semantic expectation CONFIRMED; FOURTH consecutive flat |
| wd (TOTAL_WORDING_LINES) | 265 | 265 | 0 | flat |
| rows | 332 | 332 | 0 | ask's "rows 332->?" answered: 332 |
| battery legs | 108/142/15/0 | 108/142/15/0 | 0 | all flat (fix inserts touch no battery face) |
| hits | 412 (173/197/42) | 412 (173/197/42) | 0 | measured from ai_flavor_tree.json |
| stdout lines | 341 | 341 | 0 | stdout byte-identical w15 = w16 |
| norm files | 329 | 329 | 0 | flat |
| norm error | 1177 | 763 | -414 | == R2-109 post-fix 763 EXACT |
| norm warn | 2211 | 1263 | -948 | == R2-109 post-fix 1263 EXACT |
| findings total | 3388 | 2026 | -1362 | == R2-109 cured 1362 EXACT; lane 74 + non-lane 1952 |
| cjk | 38 in 38 | 38 in 38 | 0 | flat, ZERO inflow w12-w16 |
| cjk_ratio | 0.028760 | 0.028635 | -0.000125 | == R2-109 post-fix value EXACT |
| policy | 143 gate F | 143 gate F | 0 | flat (active_faces 143, gate false) |

- TREE-LEVEL RECHECK CLOSURE (the ask's bolded line): the merged
  tree's norm summary `files=329 error=763 warn=1263
  cjk_ratio=0.028635` == R2-109's after face on the fix branch
  EXACT on ALL FOUR values - the PR#37 integration face is confirmed
  present in the merged main tree, first-hand, this window. THE
  FIX-FACE RECHECK LOOP IS CLOSED.
- Per-kind closure (w16 json, aggregated this session): jargon 692
  / header 71 / forbidden 1191 / cjk 38 in 38 / budget 34. Error
  692 + 71 = 763 EXACT; warn 1191 + 38 + 34 = 1263 EXACT (total
  2026; w15 3388).
- w15 -> w16 per-kind: jargon 1066 -> 692 (-374), header 111 -> 71
  (-40), forbidden 2137 -> 1191 (-946), cjk 38 -> 38 (0), budget
  36 -> 34 (-2). Sum -1362 EXACT against the findings diff == R2-109
  cured 1362 EXACT.

## 3. Landing-face attribution: the PR#37 norm cures, 100% lane-attributed, +/-72 pure-insert face

- Window content: exactly ONE face - the PR#37 norm-cures integration,
  9 files +685/-612 numstat, all under zgx-out/deliverables-2-20261123/.
  No other tree delta (no instrument change; the .jsonl concurrent
  face is outside the scan lanes and uncommitted anyway).
- wc -l closure (measured this session, 10 lane files): 2178
  (7b183ed) -> 2250 (HEAD tree) = +72 net lines, == R2-109 G5
  EXACT. Per-file: MANIFEST 26->26 (0, untouched control), w13
  282->288 (+6), w14 348->348 (0, in-line edits only), gap-convert
  68->74 (+6), gap-proposal 83->89 (+6), h1 144->152 (+8),
  longitudinal 95->101 (+6), mech 124->132 (+8), plan 806->830
  (+24), rsi 202->210 (+8) - == R2-109's G5 per-file table EXACT,
  every row.
- NORM face: -1362, 100% lane-attributed, verified two ways: (a)
  lane findings w15 1436 -> w16 74 (forbidden 68 + jargon 6) == R2-109
  EXACT, per-file lane face == R2-109 receipt EXACT (MANIFEST 11
  forbidden / w13 18 forbidden / w14 6 forbidden + 1 jargon /
  gap-convert 3 forbidden / gap-proposal 9 forbidden + 4 jargon /
  h1 2 forbidden / longitudinal 2 forbidden + 1 jargon / mech 8
  forbidden / plan 3 forbidden / rsi 6 forbidden); (b) the non-lane
  (path,kind) count maps are SET-EQUAL between the w15 json and the
  w16 json (221 entries = 221 entries) - ZERO norm movement outside
  the lane.
- Tuple-level accounting note (registered as-is): a naive
  (file,line,kind) tuple diff w15->w16 reads REMOVED 868 / ADDED
  42; the 42 pseudo-adds all sit in the 8 files that took insert
  lines (+6/+8/+24) and are line-shift ghosts (findings below an
  insert slide down); MANIFEST and w14 (the two 0-insert files)
  contribute ZERO pseudo-adds, confirming the artifact reading.
  The robust accounting is the per-kind counter diff (section 2)
  plus the non-lane set-equality above.
- EM face: ZERO increment, verified at three levels: (a) ai_flavor
  em 7936 == 7936 and stdout byte-identical to w15; (b) byte-level
  direct measurement on ALL 10 lane files at the HEAD tree this
  session: high-bit (>0x7F) bytes = 0 and U+2014 byte-triples = 0
  per file, TOTAL hi 0 / em 0 (10/10 == R2-109's G4, re-measured
  live at the merged tree); (c) the 7180308 subject em-dash is
  commit METADATA, outside the scan face (w15/89acc8a precedent).
  THE ASCII GATE STAYS CLOSED through the fix integration.

## 4. Row-level diff vs the w15 face: EMPTY (added 0 / removed 0 / changed 0)

- `diff /tmp/rqw-mcp/r2-108-w15/ai_flavor.out /tmp/rqw-mcp/
  r2-110-w16/ai_flavor.out` -> EMPTY (the two stdouts are
  md5-identical: b47d75f1 both). rows 332 -> 332; wd 265 both;
  em 7936 both; battery 108/142/15/0 both; hits 412 = 173/197/42
  both (re-parsed from the w16 json this session).
- The +/-72 face is INVISIBLE to ai_flavor: zero new rows, zero new
  wording lines, zero em - the five-field headers and stem-free
  reflows touch no battery face and no em-dash face (R2-109's G3
  collision analysis, now tree-confirmed). The w15 comparator pair
  value b47d75f1 carries over UNCHANGED for the w17 comparator.

## 5. Counter judgment: skip branch OPEN but NOT taken - window PAID re-scan (rev-list 2 > 0); em 4-degree flat, counter 3 -> 4

- Window payment: the w15 card declared the SKIP BRANCH OPEN for
  the em lane from w16 (counter = 3). The skip form's precondition
  is a window whose count leg says skip (rev-list --count 0); THIS
  window's count leg = 2 > 0 (the PR#37 integration arrived), so the
  FULL WINDOW rule fires and the full double scan RUN - as the ask
  itself directs (new anchor present = PAID re-scan, not a skip).
  The skip branch stays OPEN, unused.
- em stock: w16 == w15 == w14 == w13 == w12 (7936 x5, delta 0) = a
  TRUE 4-degree flat on the em lane: three-flat counter 3 -> 4.
  THE CHAIN HOLDS THROUGH A CURE PASS: the +72-line fix integration,
  1362 norm findings cured, em stock moved ZERO - the strongest
  flat evidence yet that the em lane is fully decoupled from the
  norm lane's cure cycle.
- Counter declaration (as-is): counter = 4, skip branch remains
  OPEN for the em lane; a future window whose rev-list count = 0
  MAY take the skip form (anchor-face verify + rev-list count,
  full double scan skippable while the chain holds); ANY em
  movement resets to 0. ANCHOR FOR W17 = 6af8067. Scope unchanged
  from w15: the counter is scoped to the em-flat chain; the NORM
  lane's own movement discipline stays a console decision (the
  norm lane DID move this window, -1362 - a cure, the desired
  direction, but movement nonetheless).
- Observation line (em): 7412 (R2-11 other-clone census) / 7484
  (8502146 in-clone) ... 9010 9010 (w7, w8) 8436 (runs 14-17) 8036
  (w9, first drop) 8033 (w10) 8033 (w11) -> 7936 (w12, second
  drop) -> 7936 (w13, first flat) -> 7936 (w14, second flat) ->
  7936 (w15, third flat) -> 7936 (w16, FOURTH consecutive flat;
  the ask's "...7936->7936->?" answered: 7936; cumulative wash
  from the 9010 peak = -1074, unchanged). Absolute baselines
  unchanged: 7412 -> 7936 = +524 (+7.1%); 7484 -> 7936 = +452
  (+6.0%). NET ABOVE both, flat-held FOUR degrees.
- Norm-gate line (R4 face, for the re-decision): error 763 < 1001 -
  the RE-BREACH is cured, error back UNDER the plan-era line (w15
  face was 1177 > 1001 by +176); warn 1263 > 1045 by +218 - the
  warn leg REMAINS BREACHED, now composed of the standing pre-fix
  breach (1195 vs 1045 = +150, the w14 recovered face) plus the 68
  in-lane citation residuals R2-109 registered (the C-1 whitelist
  question, still open). R4 rebase STAYS PENDING, bound by the
  residual-floor decision, no longer by uncured supply debt.

## 6. Not run (not named by this ask, or gated)

No PR feedback GETs; no MCP helper calls; no per-commit jargon
counts; no ai_flavor_apply selftest; no tests/run_tests.sh; no
b_gate_audit emission (R-1 write-face gate); no cure pass (the
window's cure was R2-109's, already landed); no rocqwash-loop
clone touch; no retry lanes (zero failures to retry); no checkout
(unnecessary - tree equality measured); no shallow-clone history
walks (per R2-95 registration). ROCQWASH_MCP_ALLOW_NET never set.

## Provenance and limitations

- NETRED ledger this agent, every event: (1) git fetch origin over
  HTTP/1.1 - rc 0, ONE attempt, zero retries, zero backoff spend;
  the fetch CARRIED the refmove 7b183ed..6af8067 (expected: R2-109's
  two post-integration fetches failed Empty reply, so the move was
  pending). One network event total, zero failures. No other git
  network ops; no curl; no MCP network.
- Staging (all outside the repo tree): /tmp/rqw-mcp/r2-110-w16/
  (fetch.out/.err, ai_flavor.out/.err, ai_flavor2.out/.err,
  ai_flavor_tree.json, norm_lint.out/.err, norm_lint.json,
  norm_lint2.out/.err, norm_lint2.json).
- Comparators: w15 card (baseline faces + counter face + skip
  declaration), read first-hand; w15 staging re-parsed first-hand
  (row diff EMPTY, findings diff accounting, non-lane set-equality);
  R2-109-receipt-pr.md (PR#37 face: merge_commit 6af8067, head
  7180308, 9 files +685/-612, after face 763/1263/329/0.028635,
  G5 per-file wc -l table, G4 ASCII gate), read first-hand;
  rsi-loop.log tail 15 (latest batch block anchor=7b183ed), read
  first-hand.
- Limitations: (a) the w16 em-flat judgment covers the em lane
  ONLY; the norm lane moved -1362 this window (a cure) and the
  counter scoping is unchanged from w15; (b) the tuple-level
  findings diff carries line-shift ghosts (section 3) - the
  authoritative accounting is the per-kind counters + the non-lane
  set-equality, both exact; (c) the 68 warn residuals keep the
  warn leg above the 1045 line (+218) - a policy question (C-1
  whitelist channel), not this agent's to adjudicate; (d) the
  third M (zgx-ledger-proposals.jsonl) is the R2-109-recorded
  concurrent face, outside both scan lanes, unadjudicated; (e)
  pass-2 comparators are same-session artifacts, re-verified by
  byte-identity (ai_flavor md5 pair, norm json cmp).
- Zero hand-written repo-tree content this session: no checkout,
  no writes, no branch moves; the only repo-side change is the
  fetch's carried refmove. Card + receipt + staging written
  OUTSIDE the repo. The branch
  supply/zgx/deliverables-2-norm-cures-20261123 remains checked
  out, untouched; HEAD 7180308, origin/main 6af8067 at close.

Receipt line:
`R2-110 DONE w16 PAID (skip branch open but NOT taken - rev-list 2 > 0, the PR#37 landing arrived) @6af8067 (fetch HTTP/1.1 rc 0 single-flight - UNLIKE w13/w14/w15 this fetch CARRIES the refmove 7b183ed..6af8067, expected from R2-109's two Empty-reply fetch failures leaving the move pending; ask's expected 6af8067 == measured EXACT == R2-109 merge_commit_sha EXACT; rev-list 7b183ed..origin/main = 2 == expected 2 EXACT, per-commit: 7180308 fix head (parent 7b183ed, subject ONE U+2014 = metadata face outside the scan lane, w15 89acc8a precedent) + 6af8067 automerge PR#37 == R2-109 sha EXACT; window 9 paths all lane +685/-612 numstat (substituted lines; MANIFEST untouched by design) == R2-109 EXACT; instruments byte-stable; 7180308^{tree} == 6af8067^{tree} == HEAD^{tree} = d8fceeec - scans read the anchor tree at HEAD with ZERO checkout ZERO repo-tree writes; close face == open face (pins c3b88ece + 4deabad9 == w15 values EXACT + third M b61b7d26 the R2-109 concurrent leave-behind, no mid-seat beat); ai_flavor rc 1 RED x2 byte-identical md5 b47d75f1 == the w15 pair value EXACT - stdout WHOLLY byte-identical w15=w16: em 7936 -> 7936 = 0 FOURTH consecutive FLAT / wd 265 flat / rows 332 -> 332 (ask's 332->? answered 332) / battery 108/142/15/0 flat / hits 412 = 173/197/42 flat (json-verified) / stdout lines 341 both - the +/-72 fix face is INVISIBLE to ai_flavor, tree-confirmed; norm rc 0 x2, summary files=329 error=763 warn=1263 cjk_ratio=0.028635 == R2-109 post-fix face EXACT ON ALL FOUR - TREE-LEVEL RECHECK LOOP CLOSED (the merged main tree carries the fix face first-hand), pass2 json cmp byte-identical, per-kind jargon 692 / header 71 / forbidden 1191 / cjk 38 in 38 flat w12-w16 / budget 34, error 692+71=763 EXACT warn 1191+38+34=1263 EXACT, total 2026 = lane 74 + non-lane 1952, w15->w16 per-kind deltas -374/-40/-946/0/-2 = -1362 == R2-109 cured 1362 EXACT; lane 74 = forbidden 68 + jargon 6 == R2-109 EXACT, per-file lane face == R2-109 receipt EXACT (MANIFEST 11 / w13 18 / w14 6+1 / gap-convert 3 / gap-proposal 9+4 / h1 2 / longitudinal 2+1 / mech 8 / plan 3 / rsi 6); non-lane (path,kind) maps SET-EQUAL w15=w16 (221=221) - zero norm movement outside the lane; tuple-diff 42 pseudo-adds all in the 8 inserted-in files = line-shift ghosts (MANIFEST/w14 zero - artifact reading confirmed), registered; wc -l closure 2178 -> 2250 = +72 EXACT, per-file == R2-109 G5 table row-for-row (MANIFEST 0 / w13 +6 / w14 0 / gap-convert +6 / gap-proposal +6 / h1 +8 / longitudinal +6 / mech +8 / plan +24 / rsi +8); ASCII gate 10/10 hi=0 em=0 re-measured at the merged tree - GATE STAYS CLOSED; row diff added 0 / removed 0 / changed 0 (stdout md5-identical); counter: skip branch OPEN at window open (counter=3) but window PAID (count leg 2>0), full double scan RUN, em 4-degree flat (w12=w13=w14=w15=w16=7936), counter 3 -> 4, chain HOLDS THROUGH A CURE PASS, skip form remains available for a future rev-list-0 window, any em movement resets to 0, anchor for w17 = 6af8067; observation ...8033 w11 -> 7936 w12 -> 7936 w13 -> 7936 w14 -> 7936 w15 -> 7936 w16, cumulative -1074 from peak unchanged, baselines NET ABOVE (+524/+452) unchanged; R4: error 763 < 1001 RECOVERED (w15 re-breach cured), warn 1263 > 1045 by +218 BREACH REMAINS (= standing 150 + the 68 registered citation residuals, C-1 whitelist question open), R4 rebase PENDING bound by the residual decision not supply debt; NETRED 1 event (fetch rc 0 single-flight, refmove carried, zero retries zero backoff) 0 failures, zero MCP, zero hand-written repo-tree content 2026-11-23`
