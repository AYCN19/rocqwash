# ai_flavor trend card - em-dash / wording / norm faces, rocqwash (R2-102, window w13)
Purpose. Trend sampler window w13: anchor face verify, ai_flavor + norm_lint double scan (ground CLI form, read-only), row-level findings ledger, dual-baseline judgment vs w12 and vs the post-fix face. Ticket R2-102, agent live-lumen (subagent, dynamic workflow).
Interface. This card (English ASCII; non-ASCII gate = 0 bytes measured post-write) plus the receipt R2-102-receipt.md; consumed by the dispatching workflow.
Dependencies. /Users/zuguangzhao/rocqwash MAIN clone (read-only this agent), python3 -I, git, tools/ai_flavor.py, tools/norm_lint.py, the w12 trend card + its staging, docs/jargon-to-standard-mapping-v1.md; no MCP helper.
Evidence. Every value below was measured this session with the quoted command forms; staging /tmp/rqw-mcp/r2-102-w13 holds all raw outputs; anchor fb799bfe network-verified via the ask-named fetch.
Exit-codes. Scans and the fetch rc 0; the ask-literal grep pipeline returned zero stdout lines and is registered as-is; the wording battery RED verdict stands recorded (report-only instrument face).


- Ticket: R2-102, agent: trend sampler w13 (read-only sampling; zero
  hand-written repo-tree content; write faces = this card, the
  receipt R2-102-receipt.md, and /tmp/rqw-mcp/r2-102-w13 staging),
  identity live-lumen (subagent, dynamic workflow)
- Date: 2026/11/22 (UTC clock: fetch beat 2026-11-22T19:16Z, scans
  2026-11-22T19:17-19:19Z, card write 2026-11-22T19:20Z; local
  calendar 2026/11/23; the ask-named filename carries 2026/11/23 and
  is written exactly as named)
- Card artifact: this file (English ASCII; CJK paths appear as
  \uXXXX escapes; non-ASCII gate = 0 bytes, measured post-write)
- Target repo: /Users/zuguangzhao/rocqwash (MAIN clone, the
  R2-91/R2-95/R2-97/R2-99 lineage clone; dirty pair + 3 untracked
  preserved byte-identical through every action)
- FINAL anchor: fb799bfe602550305020f4c27852020de7e379ee = origin/
  main at scan time (HEAD == origin/main byte-equality pass
  verified; == the ask's expected fb799bfe EXACT; the scans
  sampled THIS tip)

## 1. Anchor face: fetch rc 0 zero-refmove, rev-list 2 EXACT, window 100% deliverables face

- Pre-fetch face (measured at agent open): HEAD = 8d6c47dd (the
  deliverables commit) attached to branch supply/zgx/deliverables-
  20261123 (branch UNTOUCHED by this agent, verified post-checkout);
  local origin/main was ALREADY fb799bfe... - i.e. the ask's
  expected anchor matched the PRE-FETCH ref face, moved there by an
  earlier beat's fetch (the R2-101 patrol tip-snapshot beat; the
  24-loop card books ANCHOR MOVED 1e4018a -> fb799bfe from that
  beat). Dirty pair pins c3b88ece (docs/b-gate-audit.json) +
  28c85e04 (docs/scheduling-feedback.json) + 3 untracked zgx-out
  files, all present at open.
- The ask-named fetch ran exactly once: `git -C /Users/zuguangzhao/
  rocqwash -c http.version=HTTP/1.1 fetch origin` - rc 0, ONE
  attempt, HTTP/1.1 forced, zero retries, zero backoff, stderr
  EMPTY (fetch.err 0 bytes = NO refmove; the ref was already at the
  tip, unlike w12 where the fetch itself moved origin/main).
- `git rev-parse origin/main` = fb799bfe602550305020f4c27852020de7
  e379ee == the ask's expected fb799bfe EXACT. `git rev-list
  --count 1e4018a..origin/main` = 2 EXACT (ask expected 2).
- Window commits (git log --oneline, chronological): 8d6c47d
  docs(deliverables): zgx readings batch 20261123 - 14 cards, mcp
  surface ring 9-21 + trend w10-w12 + desk-pr watch; fb799bf
  automerge: PR #33 (supply lane, head CI green). Merge mechanics:
  fb799bf parents = 1e4018a + 8d6c47d; TREE HASHES EQUAL
  (8d6c47dd^{tree} == fb799bfe^{tree} = ed358557eefccff8accb068f9
  37df853da189a55, rev-parse measured both) - the automerge is
  tree-identical to the branch tip, a pure mechanical merge commit.
- Window 100% `this-seat` face: `git diff --name-only 1e4018a..
  origin/main` = 15 paths, ALL under zgx-out/deliverables-20261123/
  (MANIFEST-deliverables-20261123.md + 14 cards; ls count 15
  byte-exact); zero non-deliverables paths. Deliverables batch =
  the reading-card archive lane (this agent line's cards, incl. the
  w12 trend card copy); automerge = merge machinery. Every window
  path is .md = inside the scanned lane (paid-window shape met).
- Insertions: `git diff --shortstat 1e4018a..fb799bfe` = 15 files
  changed, 2960 insertions(+), 0 deletions - == the ask's +2960
  EXACT; numstat per-file +N/0 for all 15, per-file sum 2960
  EXACT.
- Instruments byte-stable across the window: `git diff --stat
  1e4018a origin/main -- tools/ai_flavor.py tools/norm_lint.py
  seeds/ai_flavor/word-map.json` EMPTY rc 0 (comparability holds).
- Checkout safety (w12 precedent): dirty pair unchanged across
  HEAD..origin/main (`git diff --stat 8d6c47dd fb799bfe -- docs/
  b-gate-audit.json docs/scheduling-feedback.json` EMPTY rc 0);
  plain `git checkout fb799bfe` rc 0, NO -f (from branch
  supply/zgx/deliverables-20261123 to detached fb799bfe, reflog
  read back); pins md5 c3b88ece/28c85e04 IDENTICAL pre/post;
  `git status --porcelain` = exactly the pinned pair + 3 untracked
  at open and at close. Tree equality (see above) means the scan
  face is byte-identical either way.

## 2. Double scan vs the w12 baseline (every value judged)

Baseline (w12 @1e4018a, MEASURED by R2-99, receipt + w12 card read
first-hand; archived row map + norm json RE-READ and re-parsed
first-hand this session, sums 330 rows / 263 wd / 7936 em and
per-kind 686+71=757, 1008+38+34=1080 all EXACT): ai_flavor rc 1
RED em 7936 / wd 263 / rows 330 (339 stdout lines; battery
108/140/15/0; hits 410 = zh 173 + stems 195 + sentence 42);
norm_lint rc 0 files=304 error=757 warn=1080 cjk_ratio=0.031732,
per-kind jargon 686 in 17 files / header 71 in 15 / forbidden 1008
in 102 / cjk 38 in 38 / budget 34 in 34.

Form note (recorded fail-loud): the ask-literal bare norm_lint
form `python3 -I tools/norm_lint.py` ERRORS at this instrument
version - rc 2 usage, "one of the arguments --tree --file is
required" (stderr captured to staging; same face as w12). The scan
ran in the ground CLI form: cwd = clone root, `python3 -I tools/
norm_lint.py --tree .` (same form the w12 measurement used,
comparability holds). ai_flavor ran as the ask names it: `python3
-I tools/ai_flavor.py --tree .` (the bare form would likewise rc 2
- w12 already registered that face; not re-spent). Second passes:
ai_flavor --json (stdout byte-IDENTICAL both passes, md5
5d56e4c06507f35dbc3a5886484d7ce3 both) and norm_lint --json
(stdout differs from pass 1 by exactly the one json-path echo
line; summary line identical).

| face | w12 @1e4018a | w13 @fb799bfe | delta | judgment |
|---|---|---|---|---|
| ai_flavor rc | 1 RED | 1 RED | 0 | RED both (em > 0) |
| em (EM_DASH_U2014) | 7936 | 7936 | 0 | FIRST FLAT after two consecutive drops |
| wd (TOTAL_WORDING_LINES) | 263 | 264 | +1 | +1 = the one added row |
| rows | 330 | 331 | +1 | 0 removed / 0 changed / 1 added |
| battery legs | 108/140/15/0 | 108/141/15/0 | stems +1 | sum 264 = wd exact |
| hits | 410 (173/195/42) | 411 (173/196/42) | +1 stems | the added card line, zh/sentence flat |
| stdout lines | 339 | 340 | +1 | rows +1, exempt 2 + summary 7 both |
| norm rc | 0 report-only | 0 report-only | 0 | both report-only |
| norm files | 304 | 319 | +15 | all 15 new faces carry findings |
| norm error | 757 | 1020 | +263 | ROSE - card-face inflow (jargon +188, header +75) |
| norm warn | 1080 | 1236 | +156 | ROSE - forbidden +151, budget +5 |
| cjk_ratio | 0.031732 | 0.030024 | -0.001708 | denominator grew (ASCII bytes in), cjk count flat |
| policy | 143 faces, gate F | 143 faces, gate F | flat | movement is data, not policy |

Per-kind closure (w13 json, aggregated this session): jargon 874
in 32 files (686/17: +188, +15 files) / header 146 in 30 (71/15:
+75, +15) / forbidden 1159 in 117 (1008/102: +151, +15) / cjk 38
in 38 (flat) / budget 39 in 39 (34/34: +5). Error closure 874 +
146 = 1020 EXACT; warn closure 1159 + 38 + 39 = 1236 EXACT (total
2256 findings, w12 1837).

## 3. `This-seat` attribution (supply self-check core; no self-defense)

- The +2960 insertions = 14 cards + MANIFEST, 15 files, 2960
  content lines byte-measured (split-lines 2975 - 15 file-end
  empty tails = 2960 == numstat EXACT), total 227,792 bytes, all
  in zgx-out/deliverables-20261123/.
- SCAN-LANE face: SCAN_EXTENSIONS (tools/ai_flavor.py:50,
  read first-hand this session) = (".py", ".sh", ".md", ".json",
  ".ts") - .md IS in the scan lane. Unlike the R2-99 precedent
  (docs/exp-ledger.jsonl +2 em OUTSIDE the row map - the .jsonl
  blind spot), the deliverables faces are fully INSIDE both
  instruments' view. NO scanner-vs-diff gap this window: window
  diff-face added-line U+2014 count = 0 == scanner em delta 0
  (the jsonl blind-spot lane itself untouched in this window -
  window name-only contains no .jsonl).
- EM face: ZERO increment, verified not assumed. Direct byte
  measures over the 15 files (grep + python, this session):
  U+2014 occurrences = 0; lines with ANY non-ASCII byte = 0 (pure
  ASCII). Row closure 7936 - 7936 = 0 EXACT with the single added
  row carrying em_dash=0. THE UPSTREAM ASCII GATE IS CLOSED on the
  em lane: the 2960-line card face introduced zero em-dash and
  zero non-ASCII bytes (the zero-increment closure judgment line
  the ask names, for the em face).
- NORM face: the increment is FULLY attributed to the deliverables
  card face (registered as-is, no self-defense). Per-kind deltas ==
  the deliverables-face findings 1:1 EXACT: jargon +188 == 188;
  header +75 == 75; forbidden +151 == 151; budget +5 == 5; cjk +0
  == 0 (sum 419 findings across all 15 files, per-file 12-46,
  worst pr32-desk-i18n-20261122.md 46). The w12 archived json has
  ZERO findings on this lane (the face did not exist at 1e4018a) -
  the entire norm move is this window's card inflow.
- REPAIR-CANDIDATE lines (registered per the ask's no-self-defense
  clause): (1) 's-...-t' jargon family = 160 occurrences across the
  cards (next: l-...-g 13, h-...-r 8, d-...-h 3, c-...-n 3,
  w-...-e 1) - rewrite per docs/jargon-to-standard-mapping-v1.md
  substitutions, or book the deliverables lane into the whitelist
  by console ruling; (2) forbidden date-stamp faces = 151
  (bare '20261122' 70 + dotted '2026-11-22' 34 + 9 more stamp
  tokens 47) - the forbidden list bans date-stamp tokens and the
  cards are dated logs; strip/relocate stamps or whitelist booking;
  (3) header findings = 75 in 15 files, plus header-budget at line
  1 on 5 cards (mcp-roster51-verify, pr32-continue-watch,
  pr32-desk-i18n, rsi-reshoot, window-readings) - header format
  conformance per the norm header rule. Repairing ONLY the
  deliverables face would return norm to error 757 / warn 1080
  (the w12 face) - the increment is 100% reversible by this lane.
- R4 norm-gate rebase face: error leg BREACHED back above plan-era
  (1020 > 1001; the w12 state was 757 < 1001 STILL TRUE - no
  longer true). Warn leg worse: 1236 > 1045 (+191 vs plan, was
  +35). R4 rebase STAYS PENDING, now breaching on BOTH legs; both
  breaches are deliverables-face-attributed (see above).
- Metadata-lane note: the 8d6c47d commit SUBJECT carries one
  em-dash ("batch 20261123 - 14 cards" in the raw subject line)
  inside git metadata; commit messages are outside both
  instruments' scan face (tree diff added lines U+2014 = 0,
  measured). Recorded as observation; no gate effect.

## 4. Row-level diff vs the w12 face (structure 0/0/1, closure EXACT)

Row maps: w12 = /tmp/rqw-mcp/r2-99-w12/ai_flavor.out (330 rows,
re-parsed this session: sums 263 wd / 7936 em exact); w13 = this
session's stdout (331 rows, sums 264 / 7936 exact). Parse+diff
form: python3 -I OrderedDict row parse (this session, staging
inline).

- STRUCTURE: added 1 / removed 0 / changed 0.
- THE 1 ADDED ROW: zgx-out/deliverables-20261123/mainmove-9332c2b5
  -20261122.md (wording_lines=1 em_dash=0) - the window's only
  wording-line inflow, em-free; it is the +1 on stems battery and
  hits (195 -> 196).
- The other 14 faces (13 cards + MANIFEST) are 0/0 and are omitted
  by the detector - omission rule re-proven (zero
  `wording_lines=0 em_dash=0` rows in the stdout).
- Closure: em 0 EXACT; wd +1 EXACT (added row wd 1); rows +1
  EXACT.
- zgx-out row face 3 -> 4: divergence-case-scheduling-feedback-v2
  -20261121.md.zh.md (1, 118) + wash-plan-v2-20261122.md (7, 0) +
  its .zh.md sibling (7, 0) + the new mainmove row (1, 0).

## 5. Counter judgment: em 1-degree FLAT (counter 0 -> 1), window PAID

- Window payment: rev-list 1e4018a..origin/main = 2 > 0 - the
  count-leg rule (single fetch, then `rev-list --count <last-
  anchor>..origin/main`; 0 = skip) says FULL WINDOW. Paid and run.
- em stock: w13 == w12 (7936 == 7936, delta 0) = a TRUE 1-degree
  flat on the em lane (w12 had reset the counter by moving; w13
  adds the first flat degree): three-flat skip counter 0 -> 1. Two
  more consecutive em-flats would be needed before any skip
  branch. ANCHOR FOR W14 = fb799bfe.
- The flat is EM-LANE-ONLY: the norm lane saw the LARGEST single-
  window inflow of the whole observation line (+263 error / +156
  warn), 100% self-supplied by the deliverables card face - the
  window was anything but inert; only the em gate did not move.
- Observation line (em): 7412 (R2-11 other-clone census) / 7484
  (8502146 in-clone) ... 9010 9010 (w7, w8) 8436 (runs 14-17) 8036
  (w9, first drop) 8033 (w10) 8033 (w11) -> 7936 (w12, second
  drop) -> 7936 (w13, FIRST FLAT after two consecutive drops;
  cumulative wash from the 9010 peak = -1074, unchanged). Absolute
  baselines unchanged: 7412 -> 7936 = +524 (+7.1%); 7484 -> 7936 =
  +452 (+6.0%). The em stock remains NET ABOVE both absolute
  baselines, now flat-held.

## 6. Not run (not named by this ask, or gated)

No batch-table re-derivation (the 16-family cut is not named by
this ask; the w13 movement is deliverables-only and is printed in
sections 2-4); no PR feedback GETs (not in the ask's item list); no
MCP helper calls; no per-commit jargon counts (jargon is tree-level
only); no ai_flavor_apply selftest; no tests/run_tests.sh; no
b_gate_audit emission (R-1 write-face gate, not adjudicated); no
rocqwash-loop clone touch; no retry lanes (zero failures to
retry). ROCQWASH_MCP_ALLOW_NET never set.

## Provenance and limitations

- NETRED ledger this agent, every event: (1) git fetch origin over
  HTTP/1.1 - rc 0, ONE attempt, zero retries, zero backoff spend,
  zero refmove. One network event total, zero failures. No other
  git network ops; no curl; no MCP network.
- Staging (all outside the repo tree): /tmp/rqw-mcp/r2-102-w13/
  (fetch.err, checkout.err, ai_flavor.out/.err, ai_flavor2.out/
  .err, ai_flavor_tree.json, norm_lint_bare.out/.err, norm_lint
  .out/.err, norm_lint2.out/.err, norm_lint.json, deliv-files.txt
  [exact ls-tree of zgx-out at tip + anchor hashes]).
- Comparators: w12 card (baseline face + row-map path + R4 face),
  read first-hand; w9 card (card-library form + the .jsonl blind-
  spot precedent + the 0/0-omission proof form), read first-hand;
  /tmp/rqw-mcp/r2-99-w12/ai_flavor.out + norm_lint.json (w12 row
  map + per-kind json, RE-parsed first-hand this session - sums and
  closures EXACT vs the w12 card); 24-loop card segment in b1-
  recursion-final.md (PR#33 MERGED face, merge_commit fb799bfe,
  merged_at 2026-11-22T18:28:43Z, window rev-list=2, 15-paths-all-
  deliverables face, read first-hand this session).
- Limitations: (a) the ask's expected anchor matched the PRE-FETCH
  local ref (moved there by the earlier patrol beat's fetch; this
  agent's fetch was a zero-refmove rc 0) - recorded as-is; (b) the
  bare norm_lint form does not run at this instrument version (rc
  2 usage) - the --tree . ground form was used, the same form w12
  used, comparability holds; (c) norm files= is not disambiguated
  by the tool output between all-scanned-faces and faces-with-
  findings - in this window both interpretations give the same
  +15 (all 15 new faces carry findings); (d) terminal echo of long
  hex/paths showed display-layer noise repeatedly this session -
  every recorded value was re-taken from staged files (grep /
  python parse of /tmp artifacts) or byte-equality shells tests,
  not from the noisy echo; (e) `seat-open` HEAD was on branch
  supply/zgx/deliverables-20261123 (reflog read back) - the plain
  checkout detached HEAD to fb799bfe and left the branch untouched
  (branch --contains still lists it); no branch was created,
  moved, or deleted by this agent; (f) shallow-clone history walks
  still not attempted (per R2-95 registration).
- Zero hand-written repo-tree content this session: the only
  repo-side changes are the fetch's zero refmove (no-op) and the
  plain checkout HEAD move 8d6c47dd -> fb799bfe (tree-identical,
  no -f; the dirty pair carried byte-identical, pins c3b88ece/
  28c85e04 equal pre/post every action; status face = pair + 3
  untracked at open and at close; HEAD == origin/main == fb799bfe
  at close). Card + receipt + staging written OUTSIDE the repo.

Receipt line:
`R2-102 DONE w13 PAID FLAT-ON-EM @fb799bfe (fetch HTTP/1.1 rc 0 single-flight ZERO-refmove - ask's expected fb799bfe == pre-fetch ref face moved there by the earlier patrol beat, reflog + 24-loop card cross-read; rev-list 1e4018a..origin/main = 2 EXACT: 8d6c47d deliverables batch + fb799bf automerge PR#33, merge parents 1e4018a+8d6c47d, automerge tree == branch tree ed358557 measured - pure mechanical merge; window 100% deliverables face: 15 paths ALL zgx-out/deliverables-20261123/ (14 cards + MANIFEST), zero non-deliverables; +2960 insertions EXACT (shortstat + numstat per-file sum), 0 deletions; instruments byte-stable, dirty pair carried via plain checkout no -f, pins c3b88ece/28c85e04 equal pre/post, HEAD==origin/main==fb799bfe at close, branch supply/zgx/deliverables-20261123 untouched) ai_flavor rc 1 RED em 7936 -> 7936 = 0 FIRST FLAT after two consecutive drops / wd 263 -> 264 = +1 / rows 330 -> 331 = +1 (0 removed 0 changed 1 added, battery 108/141/15/0 = 264 exact, hits 410 -> 411 = 173/196/42 stems +1, bare norm form rc 2 usage recorded - ran --tree . ground form, pass2 --json stdout byte-identical md5 5d56e4c0); norm rc 0 files 304 -> 319 = +15 (all 15 new faces carry findings) / error 757 -> 1020 = +263 (jargon 686 -> 874 = +188, header 71 -> 146 = +75) / warn 1080 -> 1236 = +156 (forbidden 1008 -> 1159 = +151, budget 34 -> 39 = +5, cjk 38 flat) / cjk_ratio 0.031732 -> 0.030024 / policy flat 143 gate F, per-kind closures EXACT both sides; SCAN-LANE: .md INSIDE SCAN_EXTENSIONS ai_flavor.py:50 - deliverables face fully inside both instruments, NO scanner-vs-diff gap this window (diff-face U+2014 added = 0 == scanner delta 0; jsonl blind-spot lane untouched); EM face ZERO increment VERIFIED at byte level (U+2014 = 0 and non-ASCII lines = 0 over all 15 files, 2960 lines / 227792 bytes, row closure 0 exact) = ASCII gate CLOSED on the em lane; NORM increment 100% deliverables-attributed 1:1 per kind (188/75/151/5/0 = deltas; w12 json had 0 findings on this lane) - REPAIR CANDIDATES registered no-self-defense: seat jargon family 160 (landing 13 handover 8 dispatch 3 campaign 3 wave 1), date-stamp forbidden faces 151 (20261122 x70, 2026-11-22 x34, +47), header 75 + header-budget L1 x5 cards - repairing this lane alone returns norm to error 757 / warn 1080; R4 REBASE: error leg BREACHED back above plan-era (1020 > 1001, was 757 < 1001), warn +191 vs 1045 - PENDING wider, both legs card-face-attributed; metadata note: 8d6c47d SUBJECT carries one em-dash in git metadata - outside both gates, tree diff 0; row diff structure 0/0/1 - added mainmove-9332c2b5-20261122.md (1, 0) only, other 14 faces 0/0 omitted, zgx-out rows 3 -> 4; counter: em 1-degree flat = chain starts, counter 0 -> 1, anchor for w14 = fb799bfe; observation ...9010 w8 -> 8436 -> 8036 w9 -> 8033 w10 -> 8033 w11 -> 7936 w12 -> 7936 w13 FIRST FLAT, cumulative -1074 from peak unchanged, absolute baselines NET ABOVE (+524/+452) unchanged; NETRED 1 event (fetch rc 0, no refmove) 0 failures 0 retries, zero MCP, zero feedback GETs (not named), zero hand-written repo-tree content 2026-11-22`
