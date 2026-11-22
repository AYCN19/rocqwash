# ai_flavor trend card - em-dash / wording / norm faces, rocqwash (R2-99, window w12)

Purpose. Session card for ticket R2-99; states the ticket's measured facts (archive copy of the deliverables batch).
Interface. Data face (markdown); not executable; read by the trend reader and the norm scanner.
Dependencies. Documents and staging paths cited in the body; no runtime dependencies.
Evidence. Receipt line at the file end; anchor and scan values as cited in the body.
Exit-codes. Not applicable (data face).

## Card body


- Ticket: R2-99, agent: trend sampler w12 (read-only sampling; zero
  hand-written repo-tree content; write faces = this card, the
  receipt R2-99-receipt-w12.md, the rsi-loop.log batch block, and
  /tmp/rqw-mcp/r2-99-w12 staging), identity live-lumen (subagent,
  dynamic workflow)
- Date: 2026/11/22 (UTC clock: agent fetch beat 2026-11-22T17:38Z,
  card write 2026-11-22T17:44Z; local calendar 2026/11/23; the
  ask-named filename carries 2026/11/22 = the UTC date, written
  exactly as named)
- Card artifact: this file (English ASCII; CJK paths appear as
  \uXXXX escapes; non-ASCII gate = 0, measured post-write)
- Target repo: /Users/zuguangzhao/rocqwash (MAIN clone, the
  R2-91/R2-95/R2-97 lineage clone; dirty pair + 3 untracked
  preserved byte-identical through every action)
- FINAL anchor: 1e4018a2aca9597fbaa1ce5e11a4094d7bec8e68 = origin/
  main at scan time (HEAD == origin/main, verified post-scan;
  DRIFT vs the ask's expected 0ba62da - see section 1; the scans
  sampled THIS tip, not 0ba62da)

## 1. Anchor face: fetch rc 0, MID-WINDOW DRIFT to 1e4018a, rev-list 7 not 5

- Pre-fetch face (measured at agent open, before any action): HEAD =
  69dd18e561ceece8c7b50248e5a8891ac67092e3; local origin/main was
  ALREADY 0ba62da491aeed434cb412f73bd200cc4d46e05c - i.e. the ask's
  "new anchor 0ba62da" matched the PRE-FETCH local ref, moved there
  by an earlier beat's fetch (the rsi-loop.log 01:18:57 FETCH-FAIL
  anchor-stays line predates it; that beat did NOT fetch per its own
  note - the 0ba62da refmove came from a different, unlogged fetch).
  Dirty pair pins c3b88ece51b8f7e9378faf5a5aac418f (docs/
  b-gate-audit.json) + 28c85e049f96790aea2470188abec6f0 (docs/
  scheduling-feedback.json) + 3 untracked zgx-out files, all
  present at open.
- The ask-named fetch ran exactly once: `git -C /Users/zuguangzhao/
  rocqwash -c http.version=HTTP/1.1 fetch origin` - rc 0, ONE
  attempt, HTTP/1.1 forced (the 01:18:57 failure was an HTTP2
  framing error; NETRED single-flight honored, zero retries, no
  backoff lane). stderr captured at /tmp/rqw-mcp/r2-99-w12/fetch.err:
  the fetch itself moved origin/main AGAIN - "0ba62da..1e4018a main
  -> origin/main". UPSTREAM MOVED MID-WINDOW: the live tip at scan
  time is 1e4018a2aca9597fbaa1ce5e11a4094d7bec8e68, two commits
  past the ask's expected 0ba62da. Recorded as drift-as-it-is; the
  window was sampled at the TRUE live tip (sampling 0ba62da would
  have missed the last two commits, both touching scanned .md/.json
  lanes - a mis-sample).
- Window count: `git rev-list --count 69dd18e5..origin/main` = 7
  (ask expected 5). Commit list (git log --oneline, chronological):
  9332c2b5 (fix ci-realreds axiom_audit selftest vector), d354580
  (fix ci-realreds-final engine-tolerant census contract), 5378058
  (i18n loop-r1: mechanical em-dash AND JARGON cure round 1, "norm
  faces 20"), 0af741d (i18n loop-r2: mechanical em-dash cure round
  2, "norm faces 16"), 0ba62da (evolve cycle11 re-harvest), eb996ab
  (docs ci whitepaper section 13 + triage R24), 1e4018a (docs ci
  taxonomy R23/R24 + zh face sync-status header).
- Transcription cross-check (the ask's "5 commits: 10da5cb/9332c2b5/
  d354580/0af741d/0ba62da or containing 5378058"): 10da5cb is NOT in
  the window - it is an ANCESTOR of 69dd18e5 (R2-95 receipt segment
  2 already booked 10da5cb + 69dd18e as the w11 window content past
  76cdbbf); 5378058 IS in the window (the "or containing" leg);
  9332c2b5/d354580/0af741d/0ba62da all in; PLUS eb996ab + 1e4018a
  discovered only by the live fetch. The transcription is therefore
  4-of-5 right with the 10da5cb slot wrong and two commits short -
  consistent with a transcription frozen at the 0ba62da ref face.
- Paid-window rule (window-readings-20261122.md segment 5 item 2):
  `git diff --name-only 69dd18e5..1e4018a` = 28 paths, ZERO of them
  under .github/ - the window is 100% non-yml (the INVERSE of w11's
  ci.yml-only window), with heavy scanned-lane content (docs/*.md,
  docs/docking/*.md, README_EN.md, examples/*, recipes/*, seeds/
  i18n/*, tests/t_axiom_audit.py, tools/*.py, docs/
  ci-triage-table.json). PAID, exercised.
- Checkout safety (R2-95 precedent, plain checkout no -f): BOTH
  pre-checks EMPTY rc 0 - `git diff --stat 69dd18e5 1e4018a --
  docs/b-gate-audit.json docs/scheduling-feedback.json` (dirty pair
  unchanged across the window -> clean carry) and the same on
  tools/ai_flavor.py tools/norm_lint.py seeds/ai_flavor/word-map.json
  (INSTRUMENTS BYTE-STABLE across the window - comparability holds).
  `git checkout 1e4018a` rc 0; pins re-measured IDENTICAL after;
  `git status --porcelain` = exactly the pinned pair + 3 untracked.

## 2. Double scan vs the w11 baseline (every value judged)

Baseline (w11 @69dd18e5, MEASURED by R2-95, receipt + archive /tmp/
rqw-mcp/r2-95/ read first-hand this session): ai_flavor rc 1 RED em
8033 / wd 263 / rows 343 (352 stdout lines; battery 108/140/15/0;
hits 410 = zh 173 + stems 195 + sentence 42); norm_lint rc 0
files=303 error=763 warn=1068 cjk_ratio=0.031928, per-kind jargon
692 / header 71 / forbidden 996 / cjk 38 / budget 34,
archives_skipped 174.

Form note (recorded as a deviation, fail-loud): the ask-literal
bare form `python3 -I tools/ai_flavor.py` ERRORS at this instrument
version - rc 2 usage, "one of the arguments --file --tree
--selftest is required" (stderr captured). The scan ran in the
ground CLI form the R2-95 w11 measurement itself used: cwd = clone
root, `python3 -I tools/ai_flavor.py --tree .` (same scale, same
instrument, same clone face incl. the 3 untracked zgx-out rows both
sides). norm_lint likewise (`--tree .`; its --tree/--file group is
likewise required). Second passes: ai_flavor --json (stdout md5
7fc48f99cefccfd787a6cb5aa73cce3d == first pass, byte-identical) and
norm_lint --json for the per-kind closure.

| face | w11 @69dd18e5 | w12 @1e4018a | delta | judgment |
|---|---|---|---|---|
| ai_flavor rc | 1 RED | 1 RED | 0 | RED both (em > 0) |
| em (EM_DASH_U2014) | 8033 | 7936 | -97 (-1.21%) | REAL DROP, 2nd consecutive |
| wd (TOTAL_WORDING_LINES) | 263 | 263 | 0 | FLAT |
| rows | 343 | 330 | -13 | 14 cured to 0/0, 1 added |
| battery legs | 108/140/15/0 | 108/140/15/0 | 0/0/0/0 | FLAT, sum 263 exact |
| hits | 410 (173/195/42) | 410 (173/195/42) | 0 | FLAT under em move (w9 phenomenon class) |
| stdout lines | 352 | 339 | -13 | rows -13, exempt 2 + summary 7 both |
| norm rc | 0 report-only | 0 report-only | 0 | both report-only |
| norm files | 303 | 304 | +1 | one face gained findings |
| norm error | 763 | 757 | -6 | REAL DROP - see R4 row |
| norm warn | 1068 | 1080 | +12 | ROSE (forbidden inflow) |
| cjk_ratio | 0.031928 | 0.031732 | -0.000196 | moved with the cure |
| archives_skipped | 174 | 174 | 0 | FLAT |
| policy | 143 faces, gate F | 143 faces, gate F | flat | movement is data, not policy |

Per-kind closure (w12 json, aggregated this session): jargon 686 in
17 files (w11 count 692: -6) / header 71 in 15 files (71: 0) /
forbidden 1008 in 102 files (996: +12) / cjk 38 in 38 files (38: 0)
/ budget 34 in 34 files (34: 0). Error closure 686 + 71 = 757 EXACT;
warn closure 1008 + 38 + 34 = 1080 EXACT (total 1837, w11 1794).

## 3. Row-level diff vs the w11 face (structure 1/14/5, closure EXACT)

Row maps: w11 = /tmp/rqw-mcp/r2-95/ai_flavor.out (343 rows, re-parsed
this session: sums 263 wd / 8033 em exact); w12 = this session's
stdout (330 rows, sums 263 / 7936 exact). Parse+diff script /tmp/
rqw-mcp/r2-99-w12/batch_calc_w12.py (python3 -I).

- STRUCTURE: added 1 / removed 14 / changed 5 (the ask's "0/0/N"
  face was the w11-vs-w10 face; w11-vs-w12 is 1/14/5).
- em closure: -104 (removed rows) + 33 (added row) - 26 (changed
  net) = -97 EXACT == the summary delta 8033 -> 7936. wd closure: 0
  EXACT (263 flat both). rows: -13 EXACT.
- 14 rows REMOVED = files cured to em 0 AND wd 0 (detector omits
  0/0 rows - PROVEN: grep count of `wording_lines=0 em_dash=0` = 0
  in BOTH stdouts): docs/audit-vacgen-20261116.md 6, docs/
  clean-mode-manual-20261114.md 3, docs/docking/README.md 7, docs/
  docking/alignment-and-pr-protocol.md 5, docs/docking/
  component-map.md 6, docs/exp-bus-backlog.md 3, docs/
  license-protocol-v1.0-20261114.md 10, docs/
  recursive-evolution-whitepaper-v1.0-20261121.md 7, docs/
  vacgen_sop.md 7, docs/\u6f14\u7ec3-\u54e8\u4e8b\u4ef6\u6d88\u8d39-20261113.md 21,
  examples/baselines/README.md 9, examples/baselines/
  audit-ConstructiveWorld_Live-20261111.note.md 3, examples/
  baselines/perf-README.md 11, seeds/i18n/SPEC-\u7ffb\u8bd1\u5f15\u64ce
  -20261114.md 6 -> subtotal -104.
- 1 row ADDED: docs/evolve-draft-cycle11-20261122.md (0, 33) - the
  0ba62da re-harvest landed a NEW live draft carrying +33 em inflow
  on a scanned face (the window's only new em row).
- 5 rows CHANGED: README_EN.md 4 -> 3 (-1); docs/
  ci-whitepaper-recursive-era-v1-20261116.zh.md 67 -> 69 (+2, the
  1e4018a zh sync-status header inflow); docs/
  service-layer-overview-v1.0-20261111.md 10 -> 1 (-9); examples/
  README.md 10 -> 1 (-9); recipes/S07_projection_reanchor_E5.md
  10 -> 1 (-9) -> changed net -26.
- Two-face decomposition of the -97: gross cure -132 (the -104 fully
  cured rows + -28 downward changed legs) vs gross scanned inflow
  +35 (+33 draft + +2 zh header). The cure out-ran the inflow by 97.

## 4. B3 face: 765 -> 762 -> 711, attribution exact

Batch cells re-derived from own row maps by the canonical cut script
form (/tmp/rqw-mcp/r2-91/batch_calc_w10.py read first-hand, adapted
verbatim cut order; same frozen-book rules; script at /tmp/rqw-mcp/
r2-99-w12/batch_calc_w12.py):

| cell | w9 (cited, w9 card) | w11 (measured) | w12 (measured) |
|---|---|---|---|
| B3 COMBINED (docs root <50 + docking + drafts) | 57 f / 82 wd / 765 em | 57 f / 84 wd / 762 em | 48 f / 84 wd / 711 em |

- w11 B3 = 762 measured (NOT 765): the w10 window's -3 landed inside
  B3a (the R2-92-booked +2 docs/mcp.md inflow + a -5 cure elsewhere
  in B3a); w11 flat carried 762. The ask's "765 -> ?" chain resolves
  as 765 (w9) -> 762 (w11) -> 711 (w12).
- w12 B3 delta -51, attribution EXACT from the row diff: B3d -18
  (docking trio 7+5+6 cured to 0/0) + B3a -33 (docs-root cures -57,
  service-layer-overview changed -9, evolve-draft inflow +33).
  Files 57 -> 48 (10 cured away, 1 added).
- Other moved cells w11 -> w12 (closure table): B10 241 -> 200 (-41
  = 9+3+11 baselines removed + 9+9 examples/README + S07 changed),
  B11 495 -> 494 (-1 README_EN), B2 849 -> 851 (+2 zh whitepaper;
  membership stable at 11 faces - no B2/B3 boundary crossing), B6
  521 flat, B1/B4/B5/B7/B8/B9/B12/B13/B14 flat, frozen book 16 f /
  43 wd / 2493 em flat (seventh consecutive flat reading).
- Batch subtotal closure: w11 5540 + 2493 = 8033 EXACT; w12 5443 +
  2493 = 7936 EXACT; uncovered non-frozen 0 files both sides.

## 5. Scanner-scope vs git diff face (the "-99" transcription resolved)

Diff-face counting (git diff U+2014 occurrences per added/removed
line, headers excluded; python3 -I counter at /tmp/rqw-mcp/r2-99-w12/
window.diff parse):

- FULL window 69dd18e5..1e4018a: +39 added / -134 removed = net -95
  (all files, including unscanned).
- 5-commit subwindow 69dd18e5..0ba62da (the ask's expected anchor):
  net -97.
- Tail 0ba62da..1e4018a: +2 (the zh header).
- Per-commit (git show, occurrence face): 9332c2b5 +2/-0; d354580
  0/0; 5378058 +2/-94; 0af741d +0/-40; 0ba62da +33/-0; eb996ab 0/0;
  1e4018a +2/-0. Sum -95 == full-window diff face.
- Scanner-scope (-97) vs full-window diff face (-95): the +2 gap is
  docs/exp-ledger.jsonl +2 em from 9332c2b5 - mapped first-hand to
  the file carrier - and .jsonl is OUTSIDE the detector's row map
  (SCAN_EXTENSIONS, ai_flavor.py:50 - the same blind spot the w9
  card registered). The diff face sees it, the scanner does not.
- THE ASK'S "-99" MATCHES NO MEASURED FACE: scanner -97, full diff
  -95, subwindow diff -97. Closest reconstructable bases, recorded
  as candidates NOT as findings: cure-net + draft (-92 -40 +33 =
  -99, i.e. the two cure commits minus the new draft row, excluding
  both +2 legs) or a transcription frozen mid-window. The measured
  faces stand; the -99 is a transcription deviation, registered
  fail-loud, no invented reconciliation.
- Desk-side 4th-wash real decrease (the ask's headline): PR #32
  (i18n normfast-loop, 2 commits) landed as 5378058 + 0af741d, self-
  reporting "norm faces 20" + "norm faces 16". MEASURED decrease:
  em -97 net scanner-scope (-132 gross cure vs +35 inflow); norm
  error -6 (jargon 692 -> 686 - the jargon half of loop-r1's
  "em-dash AND jargon cure"); warn +12 (forbidden inflow from the
  new docs(ci) faces - NOT a cure effect).

## 6. R4 norm-gate rebase recheck (the ask's re-test row)

- Error leg: 763 -> 757 (-6) - the ask's "jargon cures landed, error
  should drop" is VERIFIED REAL, jargon-attributed (692 -> 686;
  header 71 flat). error 757 < plan-era 1001 STILL TRUE.
- Warn leg: 1068 -> 1080 (+12, forbidden 996 -> 1008, carried by the
  new docs(ci) whitepaper/taxonomy faces). 1080 > plan-era 1045 -
  the rebase condition is the warn leg and it WORSENED. R4 rebase
  STAYS PENDING, now by a wider margin (+35 vs plan, was +23).

## 7. Three-flat counter judgment: chain BROKEN at 1 degree, counter RESET

- Premises measured: w11 was the 1-degree flat (em 8033 == 8033,
  w10 == w11, row diff 0/0/0); w12 is PAID and MOVED - em -97, rows
  -13, norm error -6, warn +12, files +1 (flat faces: wd, battery,
  hits, archives_skipped, policy - the flat faces are the
  structure, not the stock).
- Judgment: w12 = REAL DROP (not flat, not a rebound - the only
  rising faces are inflow lanes: +33 draft row, +2 zh header, +12
  forbidden warnings). The flat chain is BROKEN at 1 degree; it
  never reached 2. The three-flat skip counter is RESET to 0 - by
  R2-97's construction rule (a non-yml norm surface made this
  window paid and it moved) and now by measurement. The skip
  suggestion stands reset: three NEW consecutive flats would be
  needed before any skip branch; the count-leg rule
  (`rev-list --count <last-anchor>..origin/main` after a single
  fetch; 0 = skip) stays the standing gate with ANCHOR FOR W13 =
  1e4018a.
- Observation line (em): 7412 (R2-11 other-clone census) / 7484
  (8502146 in-clone) ... 9010 9010 (w7, w8) 8436 (runs 14-17) 8036
  (w9, first drop) 8033 (w10) 8033 (w11) -> 7936 (w12, second
  consecutive drop; -97; cumulative wash from the 9010 peak = -1074).
  Absolute-baseline face: 7412 -> 7936 = +524 (+7.1%); 7484 -> 7936
  = +452 (+6.0%). Both stated; the em stock remains NET ABOVE both
  absolute baselines - the wash lane has now out-run inflow for two
  consecutive windows but not the full observation history.

## 8. Not run (not named by this ask, or gated)

No PR feedback GETs (the R2-95/R2-97 8-call cadence is not named in
this ask's item list - R2-97 ran it hours ago, 8/8 empty); no MCP
helper calls (not named; capability_index render re-read is gated by
the window-readings rule "only when tools/ or census-tools.json
moves" - neither moved in this window per the diff name-only list);
no b_gate_audit emission (R-1 write-face gate, not adjudicated); no
per-commit jargon counts (jargon is tree-level only); no full
16-family batch table re-print (the moved cells + closure are
printed; the frozen cells are stated flat); no rocqwash-loop clone
touch (the loop's own reshoot beat at 17:34:36Z ran its six steps in
its own mktemp mirror - /tmp/rqw-mcp/r2-99/ mirror.P7oC4F + g-*
outputs are THAT beat's artifacts, read-not-modified by this agent;
this agent's staging is /tmp/rqw-mcp/r2-99-w12/); no retry lanes
(zero failures to retry). ROCQWASH_MCP_ALLOW_NET never set.

## Provenance and limitations

- NETRED ledger this agent, every event: (1) git fetch origin over
  HTTP/1.1 - rc 0, ONE attempt, zero retries, zero backoff spend.
  One network event total, zero failures. No other git network ops;
  no curl; no MCP network.
- Staging (all outside the repo tree): /tmp/rqw-mcp/r2-99-w12/
  (fetch.err, ai_flavor.out/.err, ai_flavor2.out/.err,
  ai_flavor_tree.json, norm_lint.out/.err, norm_lint2.out/.err,
  norm_lint.json, window.diff, batch_calc_w12.py).
- Comparators: R2-95 receipt + window-readings-20261122.md (w11
  measured face + the w12 paid-window rule, read first-hand);
  /tmp/rqw-mcp/r2-95/ai_flavor.out + norm_lint.json (w11 row map +
  per-kind json, read first-hand this session); R2-97
  trend-w12-feedback card (the paid-window-on-#32-merge judgment +
  flat-counter construction rule, read first-hand); w9 card (card
  library form + B3 765 citation + the jsonl blind-spot
  registration); /tmp/rqw-mcp/r2-91/batch_calc_w10.py (canonical
  cut-script form, read first-hand).
- Limitations: (a) the anchor DRIFTED mid-window (0ba62da ->
  1e4018a at the fetch); the card samples the true tip and records
  the ask's 0ba62da as the pre-fetch ref face - any downstream
  consumer keying w12 on 0ba62da must re-key to 1e4018a; (b) the
  ask-literal bare ai_flavor form does not run at this instrument
  version (rc 2 usage) - the --tree . ground form was used, which
  is the same form the w11 measurement used, so comparability
  holds; (c) the em-carrier mapping of the two +2 diff legs used a
  per-line file tracker that mis-groups CJK-quoted diff headers -
  file-level per-commit attribution in section 5 therefore comes
  from the ROW map (closure-exact) and the one targeted carrier
  check (exp-ledger.jsonl), not from the buggy tracker; (d) the
  w11 B3 762 / w12 B3 711 cells are fresh derivations from own rows
  per the batch-list law (lists are console-side at batch time);
  (e) shallow clone (per R2-95 registration) - no per-file history
  walks were attempted.
- Zero hand-written repo-tree content this session: the only
  repo-side changes are the fetch's origin/main refmove (network
  bookkeeping) and the plain checkout HEAD move 69dd18e5 ->
  1e4018a (no -f; the dirty pair carried byte-identical, pins
  c3b88ece/28c85e04 equal pre/post every action; status face =
  pair + 3 untracked at open and at close; HEAD == origin/main ==
  1e4018a at close). Card + receipt + log block written OUTSIDE
  the repo.

Receipt line:
`R2-99 DONE w12 PAID MOVED REAL DROP @1e4018a (fetch HTTP/1.1 rc 0 single-flight, MID-WINDOW DRIFT 0ba62da -> 1e4018a recorded - ask expected 0ba62da = the pre-fetch ref face; rev-list 69dd18e5..origin/main = 7 not 5, transcription 10da5cb NOT in window = w11 ancestor, 5378058 IS in, + eb996ab/1e4018a docs(ci) discovered live; window 100% non-yml = paid rule met; instruments byte-stable, dirty pair carried via plain checkout no -f, pins c3b88ece/28c85e04 equal pre/post) ai_flavor rc 1 RED em 8033 -> 7936 = -97 / wd 263 FLAT / rows 343 -> 330 = -13 (battery 108/140/15/0 flat = 263 exact, hits 410 flat 173/195/42, exempt 2 + summary 7 both, bare no-flag form rc 2 usage recorded - ran --tree . ground form); norm rc 0 files 303 -> 304 / error 763 -> 757 = -6 (jargon 692 -> 686) / warn 1068 -> 1080 = +12 (forbidden 996 -> 1008, docs(ci) inflow) / cjk_ratio 0.031928 -> 0.031732 / archives 174 flat / policy flat, per-kind closures EXACT; row diff 1 added / 14 removed / 5 changed, closure -104 +33 -26 = -97 EXACT (14 files cured to 0/0 -104 incl docking trio -18, new draft docs/evolve-draft-cycle11-20261122.md +33, zh whitepaper header +2, service-layer/examples-README/S07 -9 each, README_EN -1; gross cure -132 vs scanned inflow +35); B3 765 (w9) -> 762 (w11 measured) -> 711 (w12 measured) = -51 attribution exact (B3d -18, B3a -33), batch closure EXACT 5443 + 2493 = 7936, uncovered 0; diff face full window -95 (+39/-134) vs scanner -97: gap = docs/exp-ledger.jsonl +2 unscanned (ai_flavor.py:50 blind spot, carrier mapped); ask's -99 matches NO measured face (candidates: -92 -40 +33 = -99 cure+draft basis, or mid-window freeze) - registered fail-loud; R4 RECHECK: error leg VERIFIED -6 jargon-attributed (757 < 1001 true), warn leg WORSENED +12 (1080 > 1045) - rebase STAYS PENDING; three-flat counter: chain BROKEN at 1 degree, w12 MOVED so counter RESET to 0 by construction AND measurement, anchor for w13 = 1e4018a; observation ...9010 w8 -> 8436 -> 8036 w9 -> 8033 w10 -> 8033 w11 -> 7936 w12 second consecutive drop, absolute baselines still NET ABOVE (+524/+452); NETRED 1 event (fetch rc 0) 0 failures 0 retries, zero MCP, zero feedback GETs (not named), zero hand-written repo-tree content, HEAD==origin/main==1e4018a at close, pair + 3 untracked byte-identical 2026-11-22`
