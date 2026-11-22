# norm cures plan - zgx-out/deliverables-20261123/ card face (R2-103)

- Ticket: R2-103, seat: repair-surface inspection + plan (READ-ONLY; zero
  repo-tree writes; write faces = this plan, the receipt R2-103-receipt-
  plan.md, and /tmp/rqw-r2-103/ staging only)
- identity: live-lumen (subagent, dynamic workflow)
- Date: 2026-11-23 (plan write beat, local calendar; the ask-named file-
  name carries 20261123 and is written exactly as named)
- Plan artifact: this file (English ASCII; non-ASCII gate = 0 bytes,
  measured post-write)
- Target repo: /Users/zuguangzhao/rocqwash (MAIN clone; the tree face
  sampled is the fb799bfe checkout, HEAD == origin/main verified)
- Scan anchor: fb799bfe602550305020f4c27852020de7e379ee (== the ask's
  expected fb799bfe EXACT; see section 0 for the fetch failure face)

## 0. Alignment check 1 - anchor before generation (as run)

- NETRED event 1 (single-flight, HTTP/1.1 forced): `git remote -v`; then
  `git -c http.version=HTTP/1.1 fetch origin`.
  Remotes: fork = https://github.com/live-lumen/rocqwash.git ;
  origin = https://github.com/hy7pc8gfmf-dotcom/rocqwash.git
  RESULT: FAILED - "fatal: unable to access
  https://github.com/hy7pc8gfmf-dotcom/rocqwash.git/: Empty reply from
  server". Zero retries, zero backoff (the deny face is not forced).
  The fetch did NOT refresh the remote face; recorded fail-loud.
- Anchor taken from the local ref face, drift reported as-is:
  git rev-parse origin/main = fb799bfe602550305020f4c27852020de7e379ee
  git rev-parse HEAD        = fb799bfe602550305020f4c27852020de7e379ee
  origin/main tip: 2026-11-22 18:28:42 +0000 "automerge: PR #33 (supply
  lane, head CI green)"
- vs the ask's expected anchor fb799bfe: EXACT match, zero drift.
  Strict form: the local ref value equals the expectation; this is NOT a
  fresh network confirmation (the fetch failed). Checks 2 and 3 re-
  verify the same ref (receipt, three-check log).
- Working-tree face at seat open: `git status --porcelain` = 5 entries
  (M docs/b-gate-audit.json, M docs/scheduling-feedback.json, 3 untracked
  zgx-out files) - the preserved dirty pair + 3 untracked of the w13
  card, byte-untouched by this seat through the whole run.

## 1. Instrument face (as run; flags verified per the ask's flag law)

- Flag check: `python3 -I tools/norm_lint.py --help`. Flags: --tree DIR |
  --file PATH (mutually exclusive), --jargon-map P (default
  docs/jargon-to-standard-mapping-v1.md, norm_lint.py:93),
  --cjk-threshold F (default 0.0), --cjk-whitelist P, --json P, --md P,
  --ai-flavor-map P, --selftest. --gate/--strict are reserved (usage
  error today; norm_lint.py:65-70).
- The ask's literal pipeline: `cd /Users/zuguangzhao/rocqwash && python3 -I
  tools/norm_lint.py --tree . 2>&1 | grep "zgx-out/deliverables"`
  RESULT: 0 lines (grep rc 1). FAIL-LOUD: at this instrument version
  stdout carries ONLY the summary line; findings are not printed. The
  file:line ledger was taken from the report face instead:
  `python3 -I tools/norm_lint.py --tree . --json /tmp/rqw-r2-103/norm.json`
  (rc 0; schema rocqwash-norm-lint/1; parsed with python3 -I).
- Summary line (both runs): "norm-lint rocqwash-norm-lint/1: files=319
  error=1020 warn=1236 cjk_ratio=0.030024 (report-only: findings are
  data)" - equals the w13 card's @fb799bfe face, zero drift.
- Determinism: rerun to /tmp/rqw-r2-103/norm2.json; `cmp norm.json
  norm2.json` = byte-identical (contract norm_lint.py:75-76).
- Rule sources read first-hand this session (tools/norm_lint.py, 944
  lines): FIELDS five-field tuple (norm_lint.py:92); DEFAULT_JARGON_MAP
  (norm_lint.py:93); HEADER_BUDGET = 30 (norm_lint.py:94); FORBIDDEN
  word-faces: internal role names + date stamps (norm_lint.py:124-129);
  md header region = file start to first "## " heading (norm_lint.py:132,
  325-333, 504-509); field-presence md regex "^[ \t]*>?[ \t]*FIELD(?:\s|$)"
  (norm_lint.py:111-117); banner rule (norm_lint.py:105-110, 347-350);
  budget warn at line 1 (norm_lint.py:511-513); backtick masking applies
  to the jargon and CJK faces ONLY (norm_lint.py:241-244, 358-361,
  397-409) and NOT to forbidden (norm_lint.py:383-393, raw-line match);
  the cjk whitelist gates the cjk kind only (norm_lint.py:520-524); the
  mapping loader strips full-width paren qualifiers and splits the face
  cell on slashes (norm_lint.py:208-219).

## 2. Findings ledger - zgx-out/deliverables-20261123/ (15 files, measured)

- Lane total: 419 findings. Per kind: jargon 188 / forbidden 151 /
  header 75 / budget 5 / cjk 0. All four ask counts (188 jargon, 151
  date-stamp, 75 header, 5 budget) match EXACT, zero drift, and match
  the w13 card's per-kind attribution line.
- Closure: error kinds jargon + header = 263; warn kinds forbidden +
  budget = 156; 263 + 156 = 419 EXACT. Global face: error 1020 = 757
  (rest of tree) + 263 (this lane); warn 1236 = 1080 + 156.
- Per-file counts:
    MANIFEST-deliverables-20261123.md                     24
    ai-flavor-trend-w12-20261122.md                       28
    handover-verify-20261122-v83.md                       34
    mainmove-9332c2b5-20261122.md                         21
    mcp-pilot2-20261122.md                                25
    mcp-roster51-verify-20261122.md                       35
    mcp-stage2-20261122.md                                36
    mcp-w4-recheck-20261122.md                            25
    new-anchor-readings-20261122.md                       23
    pr32-continue-watch-20261122.md                       29
    pr32-desk-i18n-20261122.md                            46
    rsi-reshoot-20261123.md                               30
    trend-w11-feedback-20261122.md                        12
    trend-w12-feedback-20261122.md                        22
    window-readings-20261122.md                           29
- The lane draws zero cjk findings (cards are pure ASCII; the w13 card
  measured 0 non-ASCII lines over all 15 files) and every forbidden hit
  in the lane is a date-stamp token: 11 distinct tokens, zero internal-
  role-name hits (token counts in Appendix A2).

## 3. Cure plans per category

Global cure laws (bind every category; from the dispatch discipline):
- Zero semantic change: only the sanctioned target forms below; no fact,
  number, sha, path, or quote is altered beyond the mapped word/stamp
  form; quoted external artifact names (PR titles, branch refs, file
  names, commit subjects) are NEVER rewritten (identifier/quotation
  positions, mapping table section 1.1 and section 6).
- Zero line deletion: no existing content line is removed; every change
  is a within-line word/stamp replacement or an addition (the header
  block and one section heading per card). Per-file line counts are
  non-decreasing after the cures.
- ASCII gate: every added or rewritten byte sequence is ASCII; the lane
  must stay at 0 non-ASCII lines and the em face must stay flat at 7936
  (zero U+2014 added; the em gate is the ai_flavor instrument gate,
  R2-102 card).
- Backtick discipline: backticking an identifier citation clears the
  jargon face (mask_backticks, norm_lint.py:358-361) but does NOT clear
  the forbidden face (norm_lint.py:383-393); use backticks only where
  the citation is genuinely an identifier.

## 3.1 jargon family (188 findings) -> word-map standard forms

- Authority: docs/jargon-to-standard-mapping-v1.md, Table 5b (the
  English colloquial family); the table is the default --jargon-map
  (norm_lint.py:93, loader norm_lint.py:163-223; 143 active faces).
- Target forms (face -> standard cell, verbatim from the table):
    seat     -> agent
    landing  -> integration
    handover -> (delete the narration; state the facts; cite the
                handover document identifier verbatim in backticks
                where the reference is to the document itself)
    dispatch -> route (narrative sense; the red_dispatch.py identifier
                stays; row exempt regex "^#?\s*dispatch\s+red-event router")
    campaign -> effort / work stream
    wave     -> work stream (organizational sense)
- Lane counts: seat 160, landing 13, handover 8, dispatch 3, campaign 3,
  wave 1 (sum 188; equals the w13 card's repair-candidate split).
- Cure forms per instance class:
  a) seat x160: plain noun swap "seat" -> "agent" on the mapped
     occurrence, grammar preserved ("verify seat C" -> "verify agent C";
     "at seat open" -> "at agent open"; "by this seat" -> "by this
     agent"). The mapping note reserves the one-worker-per-seat topology
     wording for ledger and identifier surfaces; none of the 160 lane
     hits is a backticked citation, so all 160 swap.
  b) landing x13: swap to "integration" on the mapped occurrence
     ("landing status" -> "integration status"; "Proposal landing
     judgment" heading -> "Proposal integration judgment"; "landing
     spot" -> "integration point"; "landing with its docs/mcp.md row" ->
     "integrated with its docs/mcp.md row" where the verb reading
     requires the participle; fact content unchanged).
  c) handover x8: two sub-classes.
     - Narration references to the handover DOCUMENT (v8.3 master or the
       handover ledger series): backtick-cite the identifier verbatim
       ("handover v8.3 section 5" -> "`handover v8.3` section 5";
       "handover ledger series" -> "`handover` ledger series"; the
       citation is exempt as an identifier per mapping section 1.1).
       Affected: MANIFEST:6, MANIFEST:14 (bare filename row - backtick
       the file name), pr32-desk-i18n:40, :75, :168, trend-w12-feedback:183.
     - Filename-internal tokens: pr32-desk-i18n:15 cites
       session-handover-20261120-live-lumen.md and MANIFEST:14 cites
       handover-verify-20261122-v83.md; backtick the file-name citation
       (clears the jargon face; the date stamp inside stays - see 3.2b).
  d) dispatch x3: handover-verify:2 names the skill discipline
     cw-wf-dispatch - backtick-cite it (`cw-wf-dispatch`, identifier
     citation); new-anchor-readings:79 quotes a commit subject - the
     quoted subject is an external artifact, backtick the quote (the
     token inside the quote is not rewritten); new-anchor-readings:96
     is narrative ("dispatch arms") -> "route arms".
  e) campaign x3 (mcp-w4-recheck:5, :24, :45): narrative organizational
     sense -> "effort" or "work stream" per local grammar.
  f) wave x1 (mcp-roster51-verify:218, "ticket 14 wave"): organizational
     sense -> "work stream".
- The full 188-row file:line listing with target form is Appendix A1.

## 3.2 date-stamp family (151 findings) -> forbidden-face canonical form

- The banned word-face (norm_lint.py:127): word-bounded YYYYMMDD
  (compact) and word-bounded YYYY-MM-DD (dotted). The suggest cell:
  "drop the date stamp from the prose face; dates belong in the ledger
  surface".
- Canonical compliant form: YYYY/MM/DD (slash form). It preserves the
  date value byte-for-byte in meaning, is pure ASCII, and matches
  neither banned alternative; both lane forms collapse into it:
  "2026-11-22" -> "2026/11/22"; "20261122" -> "2026/11/22".
- ISO-8601 timestamps with a T suffix ("2026-11-22T17:38Z") do NOT fire
  the dotted alternative (no word boundary before T) and are left
  untouched; the rewrite touches only occurrences that actually fired.
- Classification method (this seat's analysis tooling, not an
  instrument): regex-faithful to norm_lint.py:127 (only boundary-
  matching spans counted) + a lexical token-run rule (an occurrence is
  identifier-position when its maximal [A-Za-z0-9._/-] run carries a
  letter or a slash) + one manual quotation judgment (handover-verify:
  62, below). Two earlier classifier rounds were discarded when they
  mis-classified T-suffixed timestamps and dot-adjacent filename runs;
  the registered numbers are the regex-faithful round.

  Subset 3.2a - prose date stamps: 51 findings on 50 distinct rows
  (measured split: dotted 2026-11-22 x34 + 2026-11-23 x7 = 41; compact
  20261122 x10; 41 + 10 = 51; no other token fires at a prose position).
  CURABLE: rewrite the firing occurrence
  to the slash form. Rows listed in Appendix A2 marked prose.

  Subset 3.2b - identifier and quotation positions: 100 findings on 100
  rows (token histogram: 20261122 x60, 20261114 x9, 20261116 x7,
  20261111 x6, 20261120 x6, 20261121 x5, 20261113 x4, 20261115 x2,
  20261123 x1; no dotted token fires at an identifier position).
  NOT word-curable without corrupting the referenced artifact:
  MANIFEST rows 9-22 (14 rows) embed the stamp in the listed file NAME;
  the card bodies cite card file names, paths (zgx-out/deliverables-
  20261123/), branch refs (i18n/normfast-loop-20261122), driver script
  names (wf-zgx-b1-r94-mcp-beat-20261122.md), and one quoted upstream
  PR title ("mechanical norm cures 20261122 (...)", handover-verify:62 -
  both firing occurrences on that row sit in the quotation and the
  branch ref; the lexical rule classed one span prose, overruled by
  manual reading: a quoted title is a quotation face, never rewritten).
  FAIL-LOUD, instrument fact: the forbidden face has NO exemption
  channel - backticks do not mask it (norm_lint.py:383-393) and the
  only whitelist in the instrument gates the cjk kind (norm_lint.py:
  520-524). Clearing these 100 requires a console ruling (lane booking
  or an instrument extension), not a word edit. Rows listed in
  Appendix A2 marked ident-or-quote.

## 3.3 header family (75 findings) -> five-field canonical block

- Rule face: an md header is the file start to the first "## " heading;
  it must not OPEN with a field line (banner rule) and must carry all
  five fields Purpose. / Interface. / Dependencies. / Evidence. /
  Exit-codes. line-anchored (norm_lint.py:92, 105-117, 336-355).
- Measured: all 15 cards fail exactly the five field-presence checks
  (banner_ok true on all 15; 5 findings x 15 = 75 EXACT; no docstring-
  class findings - every card has a non-empty header region).
- Cure (pure insertion, zero deletion): after line 1 of each card insert
  one blank line, the five field lines, one blank line, the section
  heading "## Card body", one blank line (9 added lines; the original
  line 1 stays the first line so the banner rule stays satisfied; every
  original line survives below the new heading).
- Field-line template (each line starts with the field name verbatim +
  period + whitespace, per norm_lint.py:111-117; ASCII; no banned face,
  no stamp, no em-dash; the ticket id is filled from the card's own
  face):
    Purpose. Session card for ticket R2-XX; states the ticket's measured
    facts (archive copy of the deliverables batch).
    Interface. Data face (markdown); not executable; read by the trend
    reader and the norm scanner.
    Dependencies. Documents and staging paths cited in the body; no
    runtime dependencies.
    Evidence. Receipt line at the file end; anchor and scan values as
    cited in the body.
    Exit-codes. Not applicable (data face).
  Multi-line field lines are fine (the presence regex is line-anchored
  on the field name; continuation lines carry no constraint).
- Observed ticket ids for the XX fill (from each card's own line 1-3,
  read this session): MANIFEST R2-100; ai-flavor-trend-w12 R2-99;
  handover-verify R2-96; mainmove R2-98; mcp-pilot2 R2-94; mcp-roster51-
  verify R2-92; mcp-stage2 R2-93; mcp-w4-recheck R2-93; new-anchor-
  readings R2-91; pr32-continue-watch R2-98; pr32-desk-i18n R2-97;
  rsi-reshoot R2-99; trend-w11-feedback R2-92; trend-w12-feedback
  R2-97; window-readings R2-95.
- Placement caution: the block MUST NOT go above line 1 (nine cards
  open with a "TICKET:" line; a field line at the very top would trip
  the banner rule, norm_lint.py:347-350).
- The full 75-row listing is Appendix A3.

## 3.4 budget family (5 findings) -> header region compression by
   boundary insertion

- Rule face: warn when the md header region exceeds HEADER_BUDGET = 30
  lines (norm_lint.py:94, 511-513); the region ends at the first
  "## " heading (norm_lint.py:325-333).
- Measured region sizes: mcp-roster51-verify 37, pr32-continue-watch
  32, pr32-desk-i18n 31, rsi-reshoot 34, window-readings 50. The five
  budget cards match the w13 card's named five EXACT.
- Interaction fail-loud: the section 3.3 insertion alone (9 lines)
  would push three NON-budget cards over the limit - mainmove 28 -> 37,
  mcp-stage2 28 -> 37, new-anchor-readings 29 -> 38 - creating three
  NEW budget findings. The paired design avoids this on all 15 cards:
  the "## Card body" heading inserted with the block makes the region
  = line 1 + blank + five fields + blank = 8 lines (region ends AT the
  heading line, norm_lint.py:328-330), which is <= 30 everywhere.
  MANIFEST has no "## " heading today (region = 22 = whole file); the
  same insertion gives it region = 8 and adds the missing structure.
- Compression is relocation, not deletion: every displaced preamble
  line survives below the new heading in order. Zero lines removed.
- The full 5-row listing is Appendix A4.

## 3.5 conflicts requiring console adjudication (fail-loud, pre-registered)

  C1. MANIFEST copy contract: MANIFEST line 5 binds the batch to
  "original-name copy, zero content modification; post-copy md5 must
  equal source md5 (verified 14/14)", and rows 9-22 record per-file
  bytes + md5. ANY byte edit to any card breaks the copy-md5 equality
  and stales the MANIFEST columns. The cures therefore require one of:
  (i) the same cures applied to the source originals first, then a
  fresh copy pass restoring equality (new bytes/md5 columns), or
  (ii) a console ruling that the batch is amended in place with the
  MANIFEST value columns re-derived post-cure (names never change), or
  (iii) lane booking without edits. This is a batch-discipline
  decision above the seat; the word-level plan is identical under
  (i) and (ii).
  C2. The 100 identifier/quotation stamp residuals (3.2b): no
  instrument channel cures them by word edit; console booking or an
  instrument extension (identifier exemption or forbidden whitelist)
  is required for the lane to reach zero.
  C3. Post-cure predicted face: with 3.1 + 3.2a + 3.3 + 3.4 fully
  applied: lane error contribution 0 -> global error 757 (the w12 face,
  EXACT); lane warn contribution 100 (the 3.2b residuals) -> global
  warn 1180 = 1080 (w12) + 100. With an additional C2 booking the lane
  reaches zero and global warn returns to 1080 EXACT.

## 3.6 execution order and verification protocol (for the fixing seat)

  Order: (1) re-run the baseline scan and confirm 419; (2) slash-
  rewrite the 51 prose stamps (Appendix A2 prose rows); (3) apply the
  188 jargon swaps / backtick citations (Appendix A1); (4) insert the
  9-line header blocks on all 15 cards (3.3 + 3.4 paired design);
  (5) re-scan; (6) re-derive MANIFEST value columns per the C1 ruling.
  Verification gates after the cures:
  - norm_lint rerun: lane jargon 0, lane header 0, lane budget 0,
    lane forbidden = 100 (or 0 after C2), lane cjk 0; global error 757,
    global warn 1180 (or 1080 after C2); report face rc 0.
  - ai_flavor rerun: em face FLAT at 7936 (zero U+2014 in every added
    or rewritten byte); wd/rows movement is data, registered not gated.
  - ASCII gate: 0 non-ASCII bytes over the 15 files, before and after.
  - Zero-deletion audit: per-file line counts non-decreasing (each card
    +9 lines); git diff shows no removed content line; the modified-
    line set is a subset of the Appendix rows plus the insertion blocks.
  - Determinism: two consecutive post-cure scans byte-identical.

## 4. Not run / limitations (fail-loud)

  - No cures were applied by this seat: R2-103 is a read-only planning
    seat; every number above is a measurement, not an edit result.
  - The network fetch failed (Empty reply from server); the anchor is
    the local ref value equal to the expectation, not a fresh remote
    confirmation. No retry was spent (deny face).
  - The ask-literal grep pipeline is empty at this instrument version
    (findings not on stdout); the --json report face was used instead,
    after a --help flag verification (section 1).
  - The prose/identifier classification (3.2) is this seat's tooling,
    regex-faithful to the instrument word-face plus a lexical token-run
    rule plus one manual quotation judgment; it is not an instrument
    and its per-row labels are advisory to the fixing seat.
  - Instruments byte-stability across the seat window: the scans ran at
    the fb799bfe checkout with the dirty pair + 3 untracked untouched;
    no tools/ file was read-modified; norm_lint.py and the mapping
    table were read only.

## 5. Provenance

  - Commands (all rc 0 unless marked FAILED): git remote -v; git -c
    http.version=HTTP/1.1 fetch origin (FAILED); git rev-parse
    origin/main / HEAD (x3 across the three checks); git status
    --porcelain; python3 -I tools/norm_lint.py --help; python3 -I
    tools/norm_lint.py --tree . (stdout captured); same | grep
    zgx-out/deliverables (0 lines, expected face registered); python3 -I
    tools/norm_lint.py --tree . --json (x2, byte-identical); python3 -I
    parse passes over the JSON and the 15 card files (read-only).
  - Staging (outside the repo tree): /tmp/rqw-r2-103/ (norm_lint.out,
    norm.json, norm2.json, deliv-grep.out, deliv-findings.txt,
    prose-rows.txt, ident-rows.txt).
  - Comparators read first-hand: the w13 trend card (return-package/
    ai-flavor-trend-w13-20261123.md) for the 188/151/75/5 attribution,
    the five budget card names, and the repair-candidate split; docs/
    jargon-to-standard-mapping-v1.md in full; tools/norm_lint.py in
    full; MANIFEST-deliverables-20261123.md in full.
  - NETRED ledger this seat: 1 network event (the failed fetch), zero
    retries, zero backoff, no curl, no MCP network calls.

## Appendix A1 - jargon findings, file:line term -> target form (188 rows)

zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:3 seat -> agent
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:6 handover -> delete the narration; state the facts (or backtick-cite the handover document identifier)
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:14 handover -> delete the narration; state the facts (or backtick-cite the handover document identifier)
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:3 seat -> agent
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:8 seat -> agent
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:24 seat -> agent
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:276 seat -> agent
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:277 seat -> agent
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:282 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:1 handover -> delete the narration; state the facts (or backtick-cite the handover document identifier)
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:1 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:2 dispatch -> route (narrative sense; the red_dispatch.py identifier stays)
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:2 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:4 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:9 landing -> integration
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:9 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:13 landing -> integration
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:15 landing -> integration
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:43 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:60 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:65 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:83 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:87 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:89 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:97 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:98 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:102 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:107 seat -> agent
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:108 seat -> agent
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:1 seat -> agent
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:76 landing -> integration
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:94 seat -> agent
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:123 landing -> integration
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:165 seat -> agent
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:192 seat -> agent
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:195 seat -> agent
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:207 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:1 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:2 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:4 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:5 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:11 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:13 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:19 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:45 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:62 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:68 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:77 landing -> integration
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:82 landing -> integration
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:82 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:86 seat -> agent
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:87 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:3 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:15 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:19 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:42 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:45 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:46 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:49 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:52 landing -> integration
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:58 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:63 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:70 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:71 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:178 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:182 landing -> integration
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:186 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:218 wave -> work stream (organizational sense; release sense stays on ledger surfaces)
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:237 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:239 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:243 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:245 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:252 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:254 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:260 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:264 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:268 seat -> agent
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:278 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:1 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:4 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:7 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:8 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:22 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:24 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:33 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:36 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:40 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:73 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:86 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:97 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:104 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:110 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:111 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:113 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:128 landing -> integration
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:145 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:146 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:149 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:153 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:155 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:156 seat -> agent
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:160 seat -> agent
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:2 seat -> agent
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:5 campaign -> effort / work stream
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:5 seat -> agent
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:9 seat -> agent
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:24 campaign -> effort / work stream
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:39 seat -> agent
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:45 campaign -> effort / work stream
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:54 seat -> agent
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:56 seat -> agent
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:114 seat -> agent
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:124 seat -> agent
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:126 seat -> agent
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:127 seat -> agent
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:4 seat -> agent
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:39 seat -> agent
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:61 seat -> agent
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:79 dispatch -> route (narrative sense; the red_dispatch.py identifier stays)
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:81 seat -> agent
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:92 seat -> agent
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:96 dispatch -> route (narrative sense; the red_dispatch.py identifier stays)
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:105 seat -> agent
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:275 seat -> agent
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:333 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:1 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:4 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:25 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:46 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:49 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:64 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:129 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:130 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:213 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:232 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:248 seat -> agent
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:250 seat -> agent
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:1 seat -> agent
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:3 seat -> agent
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:15 handover -> delete the narration; state the facts (or backtick-cite the handover document identifier)
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:23 seat -> agent
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:40 handover -> delete the narration; state the facts (or backtick-cite the handover document identifier)
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:63 seat -> agent
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:75 handover -> delete the narration; state the facts (or backtick-cite the handover document identifier)
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:139 seat -> agent
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:168 handover -> delete the narration; state the facts (or backtick-cite the handover document identifier)
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:170 seat -> agent
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:175 seat -> agent
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:181 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:1 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:4 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:5 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:18 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:25 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:28 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:31 landing -> integration
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:39 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:43 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:44 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:45 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:74 landing -> integration
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:75 landing -> integration
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:111 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:112 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:121 seat -> agent
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:130 seat -> agent
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:3 seat -> agent
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:40 seat -> agent
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:3 seat -> agent
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:7 seat -> agent
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:110 seat -> agent
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:131 seat -> agent
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:150 seat -> agent
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:173 seat -> agent
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:183 handover -> delete the narration; state the facts (or backtick-cite the handover document identifier)
zgx-out/deliverables-20261123/window-readings-20261122.md:1 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:3 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:6 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:8 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:42 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:46 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:48 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:60 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:111 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:126 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:185 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:226 seat -> agent
zgx-out/deliverables-20261123/window-readings-20261122.md:231 seat -> agent

## Appendix A2 - forbidden (date-stamp) findings, file:line token class (151 rows)

(class prose = slash-form curable per 3.2a; class ident-or-quote =
 identifier/quotation position, console channel per 3.2b)

zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:1 2026-11-23 prose
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:4 2026-11-23 prose
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:9 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:10 20261123 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:11 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:12 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:13 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:14 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:15 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:16 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:17 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:18 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:19 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:20 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:21 20261122 ident-or-quote
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:22 20261122 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:8 2026-11-22 prose
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:9 2026-11-23 prose
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:10 20261122 prose
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:65 20261122 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:140 20261116 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:141 20261114 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:144 20261114 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:145 20261121 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:146 20261113 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:148 20261111 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:150 20261114 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:151 20261122 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:155 20261116 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:157 20261111 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:290 20261122 ident-or-quote
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:325 2026-11-22 prose
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:325 20261122 ident-or-quote
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:3 2026-11-22 prose
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:9 2026-11-22 prose
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:33 2026-11-22 prose
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:33 20261122 ident-or-quote
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:56 20261120 ident-or-quote
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:59 20261122 ident-or-quote
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:62 20261122 ident-or-quote
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:65 20261122 ident-or-quote
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:81 2026-11-22 prose
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:11 20261122 ident-or-quote
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:14 20261122 ident-or-quote
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:16 20261122 ident-or-quote
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:28 2026-11-22 prose
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:49 20261116 ident-or-quote
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:67 20261122 prose
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:71 20261116 ident-or-quote
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:221 2026-11-22 prose
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:2 20261122 ident-or-quote
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:3 20261120 ident-or-quote
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:3 20261122 ident-or-quote
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:7 2026-11-22 prose
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:94 2026-11-22 prose
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:1 20261122 prose
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:32 20261122 ident-or-quote
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:292 2026-11-22 prose
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:12 20261122 ident-or-quote
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:17 20261122 ident-or-quote
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:18 20261122 ident-or-quote
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:28 2026-11-22 prose
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:62 20261121 ident-or-quote
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:62 20261122 ident-or-quote
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:168 2026-11-22 prose
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:2 2026-11-22 prose
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:3 2026-11-22 prose
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:4 20261120 ident-or-quote
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:4 20261122 ident-or-quote
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:24 20261115 ident-or-quote
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:45 20261115 ident-or-quote
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:126 2026-11-22 prose
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:1 20261122 prose
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:7 2026-11-22 prose
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:10 20261122 ident-or-quote
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:44 20261122 ident-or-quote
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:104 20261122 prose
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:175 20261120 ident-or-quote
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:221 20261113 ident-or-quote
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:337 2026-11-22 prose
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:16 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:18 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:32 2026-11-22 prose
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:89 2026-11-23 prose
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:138 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:236 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:238 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:239 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:240 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:241 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:256 2026-11-22 prose
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:15 20261120 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:21 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:31 2026-11-22 prose
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:41 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:44 20261122 prose
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:54 20261122 prose
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:89 20261114 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:90 20261111 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:91 20261113 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:94 20261116 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:95 20261114 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:97 20261121 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:98 20261111 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:99 20261114 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:100 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:112 20261116 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:113 20261114 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:117 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:119 20261114 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:120 20261121 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:121 20261111 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:123 20261113 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:126 20261111 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:129 20261114 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:199 20261122 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:207 2026-11-22 prose
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:208 20261116 ident-or-quote
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:248 2026-11-22 prose
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:11 2026-11-22 prose
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:20 20261120 ident-or-quote
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:23 20261122 ident-or-quote
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:30 20261122 ident-or-quote
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:34 2026-11-22 prose
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:34 2026-11-23 prose
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:41 2026-11-23 prose
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:7 2026-11-22 prose
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:10 20261122 ident-or-quote
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:146 20261122 ident-or-quote
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:152 20261122 ident-or-quote
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:165 2026-11-22 prose
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:7 2026-11-22 prose
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:8 2026-11-23 prose
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:9 20261122 prose
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:12 20261122 ident-or-quote
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:33 20261121 ident-or-quote
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:42 20261122 prose
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:107 20261122 ident-or-quote
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:178 20261122 ident-or-quote
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:180 20261122 ident-or-quote
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:196 2026-11-22 prose
zgx-out/deliverables-20261123/window-readings-20261122.md:27 20261122 ident-or-quote
zgx-out/deliverables-20261123/window-readings-20261122.md:30 20261122 ident-or-quote
zgx-out/deliverables-20261123/window-readings-20261122.md:32 20261122 ident-or-quote
zgx-out/deliverables-20261123/window-readings-20261122.md:34 20261122 ident-or-quote
zgx-out/deliverables-20261123/window-readings-20261122.md:50 2026-11-22 prose
zgx-out/deliverables-20261123/window-readings-20261122.md:116 2026-11-22 prose
zgx-out/deliverables-20261123/window-readings-20261122.md:120 2026-11-22 prose
zgx-out/deliverables-20261123/window-readings-20261122.md:123 20261122 prose
zgx-out/deliverables-20261123/window-readings-20261122.md:177 2026-11-22 prose
zgx-out/deliverables-20261123/window-readings-20261122.md:257 2026-11-22 prose

## Appendix A3 - header findings, file:line missing-field (75 rows)

zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:1 Dependencies.
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:1 Evidence.
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:1 Exit-codes.
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:1 Interface.
zgx-out/deliverables-20261123/MANIFEST-deliverables-20261123.md:1 Purpose.
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:1 Interface.
zgx-out/deliverables-20261123/ai-flavor-trend-w12-20261122.md:1 Purpose.
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:1 Dependencies.
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:1 Evidence.
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:1 Exit-codes.
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:1 Interface.
zgx-out/deliverables-20261123/handover-verify-20261122-v83.md:1 Purpose.
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:1 Interface.
zgx-out/deliverables-20261123/mainmove-9332c2b5-20261122.md:1 Purpose.
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:1 Interface.
zgx-out/deliverables-20261123/mcp-pilot2-20261122.md:1 Purpose.
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:1 Interface.
zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:1 Purpose.
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:1 Interface.
zgx-out/deliverables-20261123/mcp-stage2-20261122.md:1 Purpose.
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:1 Interface.
zgx-out/deliverables-20261123/mcp-w4-recheck-20261122.md:1 Purpose.
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:1 Interface.
zgx-out/deliverables-20261123/new-anchor-readings-20261122.md:1 Purpose.
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:1 Interface.
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:1 Purpose.
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:1 Interface.
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:1 Purpose.
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:1 Dependencies.
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:1 Evidence.
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:1 Exit-codes.
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:1 Interface.
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:1 Purpose.
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:1 Interface.
zgx-out/deliverables-20261123/trend-w11-feedback-20261122.md:1 Purpose.
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:1 Interface.
zgx-out/deliverables-20261123/trend-w12-feedback-20261122.md:1 Purpose.
zgx-out/deliverables-20261123/window-readings-20261122.md:1 Dependencies.
zgx-out/deliverables-20261123/window-readings-20261122.md:1 Evidence.
zgx-out/deliverables-20261123/window-readings-20261122.md:1 Exit-codes.
zgx-out/deliverables-20261123/window-readings-20261122.md:1 Interface.
zgx-out/deliverables-20261123/window-readings-20261122.md:1 Purpose.

## Appendix A4 - budget findings, file:line term (5 rows)

zgx-out/deliverables-20261123/mcp-roster51-verify-20261122.md:1 header-budget
zgx-out/deliverables-20261123/pr32-continue-watch-20261122.md:1 header-budget
zgx-out/deliverables-20261123/pr32-desk-i18n-20261122.md:1 header-budget
zgx-out/deliverables-20261123/rsi-reshoot-20261123.md:1 header-budget
zgx-out/deliverables-20261123/window-readings-20261122.md:1 header-budget

