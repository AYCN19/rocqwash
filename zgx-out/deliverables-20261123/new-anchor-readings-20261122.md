# New-anchor readings - upstream 5-commit window + trend w10 + MCP b_gate_audit (R2-91, 20261122)

- Ticket: R2-91
- seat: new-anchor reading seat (pure read-only readings; the only
  write faces are this card, the receipt, and /tmp/rqw-mcp/r2-91
  staging), identity live-lumen (subagent, dynamic workflow)
- Date: 2026-11-22
- Card artifact: this file (English ASCII; CJK author names and
  filenames appear as \uXXXX escapes). Ask-named generic path
  (new-anchor-readings-20261122.md); the anchor is carried in this
  header: 35c9ecf7, window w10 (first window after w9).
- Target repo: /Users/zuguangzhao/rocqwash (the ask-named MAIN clone,
  also ROCQWASH_HOME of the MCP face). Clone-face honesty: the w9
  trend card measured the sibling workclone
  /Users/zuguangzhao/ComplexAnalysis/rocqwash-loop; this window's
  scans ran in the main clone per the ask. The dirty-face pin is
  byte-identical across both clones (md5 c3b88ece51b8f7e9378faf5
  a5aac418f measured in BOTH clones, this session and the w9/R2-89
  cards), so the scan-face delta between clones is the 3 untracked
  zgx-out files present only in the main clone (impact measured and
  confined to the norm lane, section 4).

FINAL ANCHOR (locked before and after every scan): `35c9ecf7dda1fb
c8c9c4f5c2f2669507537a2207` = origin/main ("ci: selftest-local face
advisory (continue-on-error)"); tree `308cbb8d9e7650aa23a3b5a2bc4be
d3ad5427c4e`; 5 commits past the w9 end anchor f75ffa0 (rev-list
--count, measured); 113 commits total visible from tip; the clone is
SHALLOW (rev-parse --is-shallow-repository = true, measured - depth
limits the locally visible history face, see section 6).

## 1. New-anchor status and discipline (executed exactly, this session)

- NEW ANCHOR EXISTS - the skip clause does NOT apply: single-flight
  `git fetch origin` rc 0 (zero transfer; origin/main already read
  35c9ecf7 pre-fetch, objects pre-positioned by an earlier session);
  `git rev-list --count f75ffa0..origin/main` = 5 (> 0). Per the w9
  card's skip/scan rule, a >0 count = full window; the full double
  scan was run.
- Dirty-face continuity (seat law: dirty faces preserved, never
  overwritten): pre-status `git status --porcelain` = exactly the
  canonical pair ` M docs/b-gate-audit.json` (md5 c3b88ece... ==
  the w4-w8 pin) + ` M docs/scheduling-feedback.json` (md5 28c85e04
  9f96790aea2470188abec6f0) + 3 old untracked zgx-out files; branch
  `supply/zgx/mcp-expansion-proposals-20261122` at 3ccc947. The
  dirty pair is UNCHANGED between HEAD and origin/main
  (`git diff --stat 3ccc947 35c9ecf -- docs/b-gate-audit.json
  docs/scheduling-feedback.json` EMPTY rc 0), so a plain
  `git checkout -q 35c9ecf7` (NO -f, detached) carried both intact:
  md5 re-measured IDENTICAL after the checkout; the b-gate dirty
  content grep-measured 0 occurrences of U+2014 (no reading
  contamination). Nothing discarded; no clean run.
- Instrument comparability re-proven on THIS clone:
  `git diff --stat 8502146 35c9ecf7 -- tools/ai_flavor.py
  tools/norm_lint.py seeds/ai_flavor/word-map.json` EMPTY rc 0 (the
  ticket anchor IS reachable in the main clone); window form
  f75ffa0..35c9ecf on the same 3 paths EMPTY rc 0. Instruments
  byte-stable across the whole span; readings comparable.
- Post-scan lock: HEAD == origin/main == 35c9ecf7 (rev-parse both,
  after all scans and the MCP call); status = still exactly the
  pinned pair + 3 untracked. Zero writes inside the repo tree by
  this seat (the MCP call's derived-report write is measured in
  section 5: byte-identical output, md5 unchanged - zero state
  drift materialized).

## 2. The 5 new commits, per-commit face (chronological)

Counting basis (recorded honestly, same as the w9 card): em = U+2014
occurrences over the commit's OWN diff added(+)/removed(-) lines
(`git show <c>`, +++/--- headers excluded); cjk = added lines
containing U+4E00-U+9FFF. f38b0bc is a merge (parents=2): plain
`git show` prints a combined diff - under-represents both-parent
content; the row-level closure in section 4 is the authoritative
face. Diff-face totals: +5 em added / -9 em removed = net -3, which
CLOSES EXACTLY against the row-face delta -3 (section 4); cjk 0/0
across all five.

| # | commit | author face | theme face (subject, ASCII-glossed) | files face | em +add/-rem | cjk +lines |
|---|---|---|---|---|---|---|
| 1 | caaf920 | console side (git author CJK name \u738b\u5c0f\u96ea) | feat(registration): close the registration lag - axiom-audit + vacgen-coq routes in all four cw.sh places + dispatch arms, README-cw count faces 74 routes / 72 tools, census re-anchor; rides the repair_scope tolerance fix; self-reports "stacks on 8ad21fb (title 71)" | 9 (+2825/-253): README-cw.md, cw.sh, docs/census-tools.json (+440), docs/mcp.md (+23), tests/t_mcp_face.py (+55), tools/axiom_audit.py (rewrite, -224 net), tools/mcp_server.py (+65), tools/taxonomy-coq.json (+709 NEW), tools/vacgen_coq.py (+1530 NEW) | +4 / -7 | 0 |
| 2 | a3fcf0c | console side (\u738b\u5c0f\u96ea) | fix(axiom-audit): live-report-schema order/line-tolerant (names/files/forms asserted substantively, line numbers positive ints, grade counts as coverage floors); live-run-green allowlist extended; selftest 19/19 rc=0, t_mcp_face 51 capabilities PASS (cited from commit message, not re-run) | 2 (+3/-3): README-cw.md, README-cw.zh.md | +1 / -1 | 0 |
| 3 | 3ccc947 | live-lumen (THIS strand: the supply seat's ledger commit) | feat(proposals): zgx ledger rows 28-29 (mcp roster expansion + allow-remainder closeout proposals) | 1 (+2): zgx-out/zgx-ledger-proposals.jsonl | +0 / -0 | 0 |
| 4 | f38b0bc | github-actions[bot] | automerge: PR #31 (supply lane, head CI green); merge parents a3fcf0c + 3ccc947 - carries EXACTLY the +2 ledger rows of #3, nothing else | 1 (+2): zgx-out/zgx-ledger-proposals.jsonl (combined diff) | +0 / -0 | 0 |
| 5 | 35c9ecf | console side (\u738b\u5c0f\u96ea) | ci: selftest-local face advisory - one line `continue-on-error: true` on the Windows self-hosted local face; advisory form: hosted Linux + Windows faces carry the blocking verdict; escalation context mirror-lag capacity + shared-tree coupling; structural fix (runner workspace isolation) tracked separately | 1 (+1): .github/workflows/ci.yml | +0 / -0 | 0 |

Console-side NEW-face identification (beyond the #31 supply face):

1. MCP roster face 50 -> 51: ONE new capability `vacgen_coq_generate`
   (mcp_server.py diff between f75ffa0 and 35c9ecf carries exactly
   one added roster entry; wire-schema grep count of "name" keys 56
   -> 57; tests/t_mcp_face.py now asserts "the 51-name roster" and
   header says "51-capability face"). Wire tools/list was NOT
   re-emitted by this seat (ask bounds the MCP face to the one
   b_gate_audit call); the 51 face rests on source-face + the
   a3fcf0c commit-message CI citation.
2. Registration face: axiom-audit + vacgen-coq routes registered in
   all four cw.sh places plus dispatch arms; README-cw count faces
   synced to "74 routes over 72 tools" (up from 73 tools after
   2e6d160's attest_join); docs/mcp.md +23 lines; docs/
   census-tools.json re-anchored (+440).
3. New tool faces: tools/vacgen_coq.py (1530 lines, new) and
   tools/taxonomy-coq.json (709 lines, new); tools/axiom_audit.py
   rewritten (-224 net).
4. CI advisory face: the local self-hosted runner face demoted to
   continue-on-error (35c9ecf, one line, comment-dated 20261122).
5. Supply face (#31, the seat strand's own): ledger rows 28-29
   landed to the console side via f38b0bc - the proposal face is
   RECEIVED (see section 6).

## 3. Scan form (ground CLI, per card lineage)

Both named scans ran at full tree scale at the origin/main anchor,
anchor locked before and after (section 1):

```
python3 -I tools/ai_flavor.py --tree /Users/zuguangzhao/rocqwash
                                           # rc 1 RED
python3 -I tools/ai_flavor.py --tree ... --json /tmp/rqw-mcp/r2-91/ai_flavor.json
                                           # rc 1, hits pass
python3 -I tools/norm_lint.py --tree ...   # rc 0 report-only
python3 -I tools/norm_lint.py --tree ... --json .../norm_lint.json --md .../norm_lint.md
                                           # rc 0
```

## 4. Reading 1+2: ai_flavor and norm_lint at 35c9ecf (w10)

ai_flavor (detector): exit 1 RED, stderr empty. `EM_DASH_U2014
count=8033 (target 0)`; `TOTAL_WORDING_LINES=263`; stdout = 343
per-file rows + 2 EXEMPT + 7 summary = 352 lines (wc -l). Battery:
CH_3FAMILIES_10FACES 108 / EN_WORD_STEMS_15FACES 140 / EN_SENTENCE_
8FACES 15 / EN_PARA_INITIAL_3FACES 0 (sum 263 exact; stems +2 vs
w9's 138). Hits (json pass) 410 = zh(CH) 173 + EN_WORD_STEMS 195 +
EN_SENTENCE 42; machine lane (stems+sentence) 237, zh 173 flat; the
+2 hits are EN_WORD_STEMS inside docs/census-tools.json (70 hits in
that file now).

norm_lint (linter): exit 0 report-only. `norm-lint rocqwash-norm-
lint/1: files=303 error=763 warn=1068 cjk_ratio=0.031928`. Per-kind
(aggregated from the json report): jargon 692 / header 71 /
forbidden 996 / cjk 38 / budget 34; error closure 692 + 71 = 763
EXACT; warn closure 996 + 38 + 34 = 1068 EXACT. archives_skipped =
174; policy block identical to every prior reading (active_faces
143, jargon map docs/jargon-to-standard-mapping-v1.md, cjk_threshold
0.0, cjk_whitelist null, whitelisted_files 0, gate=false) -
movement is data, not policy.

Row-level closure vs w9 (script /tmp/rqw-mcp/r2-91/parse_w10.py,
both row maps parsed from stdout, diffed, re-summed):

- ADDED 0 / REMOVED 0 rows; CHANGED 2, closure EXACT:
  - docs/census-tools.json: wd 68 -> 70, em 24 -> 19 (d_em -5,
    d_wd +2) - the caaf920 census re-anchor rewrote the data file;
  - docs/mcp.md: wd 0, em 1 -> 3 (d_em +2) - the mcp.md doc edit
    added em-dash prose to a LIVE scanned row;
  - totals: em 8036 -> 8033 (-3 EXACT), wd 261 -> 263 (+2 EXACT).

W10 TREND VERDICTS:

- em: CONTINUED DECLINE but marginal - 8036 -> 8033 = -3 (-0.04%),
  second consecutive window-over-window drop. The wash lane is IDLE:
  ZERO i18n commits in this window (the six unit-u1..u6 commits of
  w9 have no successor here) - the i18n series did NOT continue
  washing. The -3 decomposes as re-anchor restructuring -5
  (census-tools.json data rewrite) net of the window's only gross
  em INFLOW: +2 into docs/mcp.md, a live scanned row - the first
  scanned-row em inflow since the w9 window (w9's own +12 inflow sat
  in the unscanned jsonl blind spot). Scan-tree inflow has resumed;
  the jsonl blind spot face is joined by a live-row inflow face.
- norm: ERROR ROSE FOR THE FIRST TIME in the observation line -
  733 -> 763 (+30), after falling 1001 -> ... -> 733 across every
  prior window. Movers (per-file, all positive, no negative mover):
  commit-face +24 all from caaf920's registration batch
  (tools/vacgen_coq.py +11 = jargon 10 + budget 1; docs/mcp.md +5;
  tests/t_mcp_face.py +4; tools/mcp_server.py +2; cw.sh +2 - all
  jargon) and clone-face +13 from the UNTRACKED
  zgx-out/pr-description-draft-20261120.md (jargon 2 / header 5 /
  forbidden 5 / cjk 1) which exists only in the main-clone worktree
  (the w9 rocqwash-loop clone has no such file) - NOT attributable
  to any commit; it carries 0 em and 0 wd (not in the detector row
  map), so the EM face is uncontaminated by the clone delta. Warn
  1061 -> 1068 (+7: forbidden +5 and cjk +1 clone-face, budget +1
  commit-face). R4 rebase face: warn 1068 > plan-era 1045 (breach
  GREW), error 763 < 1001 but the fall REVERSED - the inflow rate
  (new registration faces) outpaced the idle wash lane this window.
- Absolute baselines (both faces stated): 7412 -> 8033 = +621
  (+8.4%) ask-cited; 7484 -> 8033 = +549 (+7.3%) in-clone. The
  window's -3 does not dent the net-above-baseline face.
- Observation line (em): 7412 (R2-11) / 7484 (8502146) 8657 8657
  8710 8737 8737 8737 8737 8808 8808 8825 8858 8976 8976 8976 9010
  9010 8436 8436 8436 8436 8036 (w9 @f75ffa0, first drop) -> 8033
  (w10 @35c9ecf, second drop, -3).

Batch table re-derivation (script /tmp/rqw-mcp/r2-91/
batch_calc_w10.py = the w9 batch script re-pointed at this
session's row map; w10 cells vs the w9 card's CUR column):

| family | w9 @f75ffa0 | w10 @35c9ecf |
|---|---|---|
| B1 docs/zh + docs/en | 19/ 17/ 795 | 19/ 17/ 795 |
| B2 docs root em>=50 (post-B3b) | 11/ 11/ 849 | 11/ 11/ 849 |
| B3 docs root <50 + docking + drafts | 57/ 82/ 765 | 57/ 84/ 762 |
| B3b docs root .md.zh.md archives | 13/  5/ 425 | 13/  5/ 425 |
| B4 seeds non-snapshot (+2 test_snippet) | 8/ 28/ 145 | 8/ 28/ 145 |
| B5 seeds/_snapshots (DECISION) | 2/  6/ 386 | 2/  6/ 386 |
| B6 tests root (no fixtures) | 88/ 29/ 521 | 88/ 29/ 521 |
| B7 tests/fixtures (DECISION) | 5/  0/  46 | 5/  0/  46 |
| B8 tools washable | 30/  6/ 342 | 30/  6/ 342 |
| B9 wrapper/watch/scan/cli/templates | 36/  0/ 367 | 36/  0/ 367 |
| B10 examples + recipes | 19/  5/ 241 | 19/  5/ 241 |
| B11 repo root + zgx-out | 16/ 29/ 495 | 16/ 29/ 495 |
| B12 CLA (DECISION, default EXCLUDE) | 8/  0/  26 | 8/  0/  26 |
| B13 instruments (LAST; 1 row + 1 exempt) | 1+1/  0/   6 | 1+1/  0/   6 |
| B14 verify + wash washable | 14/  0/ 134 | 14/  0/ 134 |
| batches subtotal | 327/218/5543 | 327/220/5540 |
| frozen book (16 files) | 16/ 43/2493 | 16/ 43/2493 |
| TOTAL | 343/261/8036 | 343/263/8033 |

- Closure EXACT: 5540 + 2493 = 8033; wd 220 + 43 = 263; uncovered
  non-frozen = 0 files. Only moved cell: B3 (em -3, wd +2 - the two
  changed rows both sit in B3). Frozen book 2493 SEVENTH consecutive
  flat reading. B2 split re-derived flat: LIVE 1 face / 56 em
  (docs/ops-evolve-\u624b\u518c-v1.0-20261113.md) + ARCHIVE 10 faces
  / 793 em. Archive class flat: all .zh.md 151 faces / 4894 em;
  non-frozen 146 / 3631 = 45.2% (flat); R6 ARCHIVE RULING stays
  BLOCKING. zgx-out rows 3, flat.
- Re-rank trigger: w10's -3 is sub-threshold; NO re-order fires. The
  w9 order stands with B3 refreshed: B2 849 > B1 795 > B3 762 > B6
  521 > B11 495 > B9 367 > B8 342 > B10 241 > B4 145 > B14 134 ||
  decision tail B5 386 > B7 46 > B12 26 || B13 6 LAST.

## 5. MCP face: b_gate_audit, one shot (ask item 3)

Call form: `bash <workspace>/_scripts/mcp_call.sh b_gate_audit '{}'
/tmp/rqw-mcp/r2-91/call-b_gate_audit.jsonl` (helper pins
ROCQWASH_HOME=/Users/zuguangzhao/rocqwash; stdio face; allow-net=
False per stderr). Raw protocol capture + parsed .text landed at
the ask-named path (helper writes OUT un-suffixed; renamed to the
ask-named .jsonl form in staging - a /tmp write only, no re-emi-
ssion). server rc 0, isError=false, RPC no error.

Readings (14-line stdout): exit code 0; schema rocqwash.b-gate-
audit/1; threshold line unchanged; 7 class rows - concl.ne.applied-
nonzero 0/0, concl.nezero.predicate 0/0, concl.quantified.
existential 0/0, concl.quantified.universal 0/0, concl.real.const-
lt-field-re-exists 1/1, ineq.real.const-lt-field-re 0/0, jargon
1/1; **verdict: not-ready; ready classes: 0 of 3 needed;
remaining_to_b: 3; errors: 0**; `report written:
docs/b-gate-audit.json`.

Drift face vs the RSI beats and w9: ZERO. All fields equal the
R2-86 and R2-89 readings (both at f75ffa0): same verdict, same
ready-classes 0 of 3, same remaining_to_b 3, errors 0, and the same
7 class rows with the same instance/round counts (1/1 on exactly
const-lt-field-re-exists and jargon). Expected: the tool's three
inputs (docs/round-ledger.jsonl, docs/round-state.json,
tools/taxonomy.json) were untouched by all 5 window commits
(caaf920's file list contains none of them) and tools/
b_gate_audit.py itself is untouched. The RSI beat's 7/59 -> 7/68
growth face belongs to the learning_feedback input ledger (R2-89
card section 4), a different tool; no b_gate_audit-side counterpart
moved. Drift recorded: NONE.

R-1 write-face measurement (first-hand): the derived-report write
DID fire (report-written line present). Pre-call md5 c3b88ece51b8f7
e9378faf5a5aac418f == post-call md5 IDENTICAL; git status still
` M` with the pinned content. The deterministic recompute at this
anchor is byte-identical to the standing dirty face, so the R-1
canonical-write face materialized in FORM but with ZERO byte/state
drift this shot - no pin was disturbed, nothing to restore. The
standing R-1 desk question (authorize canonical derived-report
writes / re-point the helper / selftest-only face) stays open,
unadjudicated here.

## 6. Supply-chain status line (ask-provided face + local face)

- Ask-provided: nine PRs MERGED through #31; #31 = this seat
  strand's proposal face RECEIVED by the console side.
- First-hand: f38b0bc (merge parents a3fcf0c + 3ccc947) carries
  exactly zgx-out/zgx-ledger-proposals.jsonl +2 (rows 28-29: mcp
  roster expansion proposals + allow-remainder closeout) - the
  proposal content crossed the wire and landed on main; the
  R2-90 receipt (read first-hand this session) covers the PR #31
  lifecycle (201 at 12:14:34Z, merged 12:18:38Z by github-actions
  [bot], 5/5 terminal check-runs).
- Local marker face (depth-limited, honest): the clone is SHALLOW
  (true; 113 commits from tip). Visible merged-PR markers from tip:
  4 automerge merge commits (#27 c147190, #29 96519e0, #30 f75ffa0,
  #31 f38b0bc) + 1 automerge-form non-merge commit (#17 3e18590) =
  5 distinct PR numbers; 1 intra-ring supply merge (19dcc75). The
  count of NINE is not locally reconstructible (squash/direct
  landings leave no automerge marker; shallow depth truncates);
  NO network query was spent on it (NETRED: the single sanctioned
  fetch was spent; deny faces untouched). Drift between the
  ask-provided nine and the locally visible five is recorded
  as-is, unadjudicated.
- Roster-guard note: the 50==50==50 guard face is now 51 on the
  source face (section 2.1); the standing three-source agreement
  (wire == mcp.md section 3 == INDEX render) was NOT re-measured
  this window (no tools/list emission) - carried as the next
  supply face's obligation together with ledger rows 28-29's
  five-candidate faces.

## 7. Not run (not named by this ask)

learning_feedback measurement (P-1 gate stays open, unmeasured);
wire tools/list re-emission; doc_lint; tests/run_tests.sh;
ai_flavor_apply selftest; any plan/emit/apply handoff lane; the
http lane; per-commit jargon counts (jargon is tree-level only,
692); any network call beyond the single quiet fetch (rc 0, no
retry, no backoff spent; ROCQWASH_MCP_ALLOW_NET never set). One MCP
emission total (b_gate_audit {} per ask item 3).

## Provenance and limitations

- Scratch/staging (all outside the repo tree): /tmp/rqw-mcp/r2-91/
  (ai_flavor.out/.json/.err, norm_lint.out/.json/.md/.err,
  call-b_gate_audit.jsonl + .text + .err, parse_w10.py,
  batch_calc_w10.py, percommit.py).
- Comparators: w9 card row map /tmp/r2-57b-w9/ai_flavor.out +
  norm_lint.json + batch_calc_w9.py (read first-hand, re-run
  re-pointed); R2-89 pilot card + R2-90 receipt (read first-hand);
  RSI migration card + audit-chain-v2 card (read first-hand).
- Clone-face: w9/w10 em numbers come from different clones (both
  byte-pinned on the dirty pair, both at their window's origin/main,
  instruments byte-stable 8502146..35c9ecf); the only clone-face
  finding isolated is the untracked pr-description draft's +13
  norm findings (0 em 0 wd).
- The shallow-clone face (true) limits local history reconstruction;
  supply-chain counts beyond the visible markers are ask-provided,
  not locally verified.
- Zero writes inside the repo tree this session. Repo-side changes:
  HEAD moved 3ccc947 (branch supply/...) -> detached 35c9ecf7 by
  plain checkout (dirty pair carried intact, md5 identical
  pre/post); origin/main ref bookkeeping pre-dated this seat.
  Card + receipt written outside the repo.

Receipt line:
`R2-91 DONE w10(35c9ecf7 NEW ANCHOR: fetch rc 0 single-flight zero-transfer, rev-list f75ffa0..origin/main = 5; window = w9 end anchor f75ffa0 -> origin/main 35c9ecf7, 5 commits caaf920/a3fcf0c/3ccc947/f38b0bc/35c9ecf; dirty pair md5 c3b88ece + 28c85e04 carried intact through plain checkout no -f, b-gate dirty 0 em; instruments 8502146..35c9ecf 3-path diff EMPTY rc 0; clone shallow=true 113 commits) ai_flavor rc 1 RED em 8033 / wd 263 / rows 343 (352 lines stdout, battery CH 108 / stems 140 +2 / sentence 15 / para 0, hits 410 = zh 173 + stems 195 + sentence 42, machine lane 237); norm rc 0 files=303 error=763 warn=1068 cjk_ratio=0.031928 per-kind jargon 692 / header 71 / forbidden 996 / cjk 38 / budget 34 closures EXACT, policy block identical, archives_skipped 174; row closure EXACT 0 added 0 removed 2 changed (census-tools.json em 24->19 wd 68->70, mcp.md em 1->3) delta -3 em +2 wd; trend VERDICT: second consecutive drop but -3 marginal (-0.04%), i18n wash lane IDLE (zero i18n commits this window, series did NOT continue washing), re-anchor restructuring -5 (caaf920 census-tools) net of FIRST scanned-row em inflow since w9 (+2 docs/mcp.md live row); norm ERROR FIRST RISE 733->763 +30 (commit-face +24 all caaf920 registration batch jargon 23 + budget 1; clone-face +13 untracked pr-description draft 0 em 0 wd - em face uncontaminated), warn 1061->1068, R4 breach GREW (1068 > 1045) while error 763 < 1001 fall REVERSED; absolute baselines still above: 7412->+621 +8.4%, 7484->+549 +7.3%; batch closure EXACT 5540 + frozen 2493 = 8033, only cell moved B3 765->762 em 82->84 wd, frozen seventh consecutive flat, archive non-frozen 146/3631 45.2% flat, R6 BLOCKING carries, no re-rank fires (w9 order stands, B3 refreshed); MCP b_gate_audit {} one shot server rc 0 isError false: verdict not-ready / ready classes 0 of 3 / remaining_to_b 3 / errors 0, 7 class rows ZERO drift vs R2-86/R2-89 @f75ffa0 (inputs untouched by all 5 commits), R-1 write fired but pre/post md5 IDENTICAL c3b88ece = zero byte drift, no pin disturbed; roster 50->51 vacgen_coq_generate (source face + t_mcp_face 51 assertion; wire tools/list not re-emitted); supply-chain: ask-provided nine MERGED through #31, first-hand f38b0bc parents a3fcf0c+3ccc947 carries exactly ledger rows 28-29 +2 (proposal face RECEIVED by console side), local shallow marker face 5 distinct PR numbers (#17 #27 #29 #30 #31), nine-count not locally reconstructible - recorded as-is; NETRED spent once (fetch), MCP emitted once; anchor locked around all scans and at close; zero repo writes 2026-11-22`
