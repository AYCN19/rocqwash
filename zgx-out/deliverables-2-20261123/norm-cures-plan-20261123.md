# norm cures plan - the batch-1 deliverables lane of 2026/11/23, card face (R2-103)
Purpose. Repair-surface inspection and cure plan for the batch-1 card lane: instrument face, per-category findings ledger, word-map / slash-form / header cure plans, conflicts, execution order; READ-ONLY, zero repo-tree writes. Ticket R2-103, agent live-lumen (subagent, dynamic workflow).
Interface. This card plus the receipt R2-103-receipt-plan.md; consumed by the dispatching workflow; every cure form below is an engineering spec, not an applied diff at this card's write time.
Dependencies. /Users/zuguangzhao/rocqwash MAIN clone (read-only this agent); python3 -I and git only; tools/norm_lint.py (report-only form, rule faces read from source); docs/jargon-to-standard-mapping-v1.md; the w13 scan staging; the R2-102 receipt.
Evidence. Every command is quoted with its output in sections 0-2; the scan JSON rerun byte-identical (cmp pass); the fetch failed once (Empty reply) and the anchor equality is a local-ref face one confirmation old, recorded as-is.
Exit-codes. norm_lint rc 0 on two byte-identical passes; the fetch rc 128 recorded fail-loud with zero retries; all other commands rc 0; zero edits performed by this card's own run.


- Ticket: R2-103, agent: repair-surface inspection + plan (READ-ONLY; zero
  repo-tree writes; write faces = this plan, the receipt R2-103-receipt-
  plan.md, and /tmp/rqw-r2-103/ staging only)
- identity: live-lumen (subagent, dynamic workflow)
- Date: 2026/11/23 (plan write beat, local calendar; the ask-named file-
  name carries the Nov 23 2026 compact stamp and is written exactly as named)
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
  origin/main tip: 2026/11/22 18:28:42 +0000 "automerge: PR #33 (supply
  lane, head CI green)"
- vs the ask's expected anchor fb799bfe: EXACT match, zero drift.
  Strict form: the local ref value equals the expectation; this is NOT a
  fresh network confirmation (the fetch failed). Checks 2 and 3 re-
  verify the same ref (receipt, three-check log).
- Working-tree face at agent open: `git status --porcelain` = 5 entries
  (M docs/b-gate-audit.json, M docs/scheduling-feedback.json, 3 untracked
  zgx-out files) - the preserved dirty pair + 3 untracked of the w13
  card, byte-untouched by this agent through the whole run.

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

## 2. Findings ledger - the batch-1 deliverables lane of 2026/11/23 (15 files, measured)

- Lane total: 419 findings. Per kind: jargon 188 / forbidden 151 /
  header 75 / budget 5 / cjk 0. All four ask counts (188 jargon, 151
  date-stamp, 75 header, 5 budget) match EXACT, zero drift, and match
  the w13 card's per-kind attribution line.
- Closure: error kinds jargon + header = 263; warn kinds forbidden +
  budget = 156; 263 + 156 = 419 EXACT. Global face: error 1020 = 757
  (rest of tree) + 263 (this lane); warn 1236 = 1080 + 156.
- Per-file counts:
    the batch-1 MANIFEST card (Nov 23 2026)               24
    the w12 trend card (Nov 22 2026)                      28
    the `handover-verify` v8.3 card (Nov 22 2026)         34
    the mainmove card, 9332c2b5 (Nov 22 2026)             21
    the mcp-pilot2 card (Nov 22 2026)                     25
    the mcp-roster51-verify card (Nov 22 2026)            35
    the mcp-stage2 card (Nov 22 2026)                     36
    the mcp-w4-recheck card (Nov 22 2026)                 25
    the new-anchor-readings card (Nov 22 2026)            23
    the pr32-continue-watch card (Nov 22 2026)            29
    the pr32-desk-i18n card (Nov 22 2026)                 46
    the rsi-reshoot card (Nov 23 2026)                    30
    the w11 feedback trend card (Nov 22 2026)             12
    the w12 feedback trend card (Nov 22 2026)             22
    the window-readings card (Nov 22 2026)                29
- The lane draws zero cjk findings (cards are pure ASCII; the w13 card
  measured 0 non-ASCII lines over all 15 files) and every forbidden hit
  in the lane is a date-stamp token: 11 distinct tokens, zero internal-
  role-name hits (token counts in Appendix A2).

## 3. Cure plans per category

Global cure laws (bind every category; from the `dispatch discipline`):
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
    role-holder word (stem-root s-...-t; jargon map table 5b)
         -> agent
    integration-arrival word (stem-root l-...-g; jargon map table 5b)
         -> integration
    narration-passing word (stem-root h-...-r; jargon map table 5b)
         -> (delete the narration; state the facts; cite the
                h-...-r document identifier verbatim in backticks
                where the reference is to the document itself)
    routing word (stem-root d-...-h; jargon map table 5b)
         -> route (narrative sense; the red_dispatch.py identifier
                stays; row exempt regex
                `^#?\s*dispatch\s+red-event router`)
    organized-effort word (stem-root c-...-n; jargon map table 5b)
         -> effort / work stream
    work-stream word (stem-root w-...-e; jargon map table 5b)
         -> work stream (organizational sense)
- Lane counts: role-holder (s-...-t) 160, integration-arrival (l-...-g) 13,
  narration-passing (h-...-r) 8, routing (d-...-h) 3, organized-effort (c-...-n) 3,
  work-stream (w-...-e) 1 (sum 188; equals the w13 card's repair-candidate split).
- Cure forms per instance class:
  a) role-holder word (stem-root s-...-t) x160: plain noun swap of that
     face -> "agent" on the mapped
     occurrence, grammar preserved ("verify s-...-t C" -> "verify agent C";
     "at s-...-t open" -> "at agent open"; "by this s-...-t" -> "by this
     agent"). The mapping note reserves the `one-worker-per-seat` topology
     wording for ledger and identifier surfaces; none of the 160 lane
     hits is a backticked citation, so all 160 swap.
  b) integration-arrival word (stem-root l-...-g) x13: swap to
     "integration" on the mapped occurrence
     ("l-...-g status" -> "integration status"; "Proposal l-...-g
     judgment" heading -> "Proposal integration judgment"; "l-...-g
     spot" -> "integration point"; "l-...-g with its docs/mcp.md row" ->
     "integrated with its docs/mcp.md row" where the verb reading
     requires the participle; fact content unchanged).
  c) narration-passing word (stem-root h-...-r) x8: two sub-classes.
     - Narration references to the `handover` DOCUMENT (v8.3 master or the
       `handover` ledger series): backtick-cite the identifier verbatim
       ("h-...-r v8.3 section 5" -> "`handover v8.3` section 5";
       "h-...-r ledger series" -> "`handover` ledger series"; the
       citation is exempt as an identifier per mapping section 1.1).
       Affected: MANIFEST:6, MANIFEST:14 (bare filename row - backtick
       the file name), pr32-desk-i18n:40, :75, :168, trend-w12-feedback:183.
     - Filename-internal tokens: pr32-desk-i18n:15 cites
       the `session-handover` live-lumen card of Nov 20 2026 and
       MANIFEST:14 cites
       the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1
       lane; backtick the file-name citation
       (clears the jargon face; the date stamp inside stays - see 3.2b).
  d) routing word (stem-root d-...-h) x3: `handover-verify`:2 names the
     skill discipline
     `cw-wf-dispatch` - backtick-cite it (`cw-wf-dispatch`, identifier
     citation); new-anchor-readings:79 quotes a commit subject - the
     quoted subject is an external artifact, backtick the quote (the
     token inside the quote is not rewritten); new-anchor-readings:96
     is narrative ("d-...-h arms") -> "route arms".
  e) organized-effort word (stem-root c-...-n) x3 (mcp-w4-recheck:5,
     :24, :45): narrative organizational
     sense -> "effort" or "work stream" per local grammar.
  f) work-stream word (stem-root w-...-e) x1 (mcp-roster51-verify:218,
     "ticket 14 w-...-e"): organizational
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
- Classification method (this agent's analysis tooling, not an
  instrument): regex-faithful to norm_lint.py:127 (only boundary-
  matching spans counted) + a lexical token-run rule (an occurrence is
  identifier-position when its maximal [A-Za-z0-9._/-] run carries a
  letter or a slash) + one manual quotation judgment (`handover-verify`:
  62, below). Two earlier classifier rounds were discarded when they
  mis-classified T-suffixed timestamps and dot-adjacent filename runs;
  the registered numbers are the regex-faithful round.

  Subset 3.2a - prose date stamps: 51 findings on 50 distinct rows
  (measured split: dotted Nov 22 2026 x34 + Nov 23 2026 x7 = 41; compact
  Nov 22 2026 compact x10; 41 + 10 = 51; no other token fires at a prose
  position).
  CURABLE: rewrite the firing occurrence
  to the slash form. Rows listed in Appendix A2 marked prose.

  Subset 3.2b - identifier and quotation positions: 100 findings on 100
  rows (token histogram: Nov 22 2026 compact x60, Nov 14 2026 compact
  x9, Nov 16 2026 compact x7,
  Nov 11 2026 compact x6, Nov 20 2026 compact x6, Nov 21 2026 compact
  x5, Nov 13 2026 compact x4, Nov 15 2026 compact x2,
  Nov 23 2026 compact x1; no dotted token fires at an identifier
  position).
  NOT word-curable without corrupting the referenced artifact:
  MANIFEST rows 9-22 (14 rows) embed the stamp in the listed file NAME;
  the card bodies cite card file names, paths (the batch-1 deliverables
  lane of 2026/11/23), branch refs (the normfast loop branch of Nov 22
  2026), driver script
  names (the wf-zgx driver script of Nov 22 2026), and one quoted upstream
  PR title ("mechanical norm cures 20261122 (...)", `handover-verify`:62 -
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
  `handover-verify` R2-96; mainmove R2-98; mcp-pilot2 R2-94; mcp-roster51-
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
  decision above the agent; the word-level plan is identical under
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

## 3.6 execution order and verification protocol (for the fixing agent)

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

  - No cures were applied by this agent: R2-103 is a read-only planning
    agent; every number above is a measurement, not an edit result.
  - The network fetch failed (Empty reply from server); the anchor is
    the local ref value equal to the expectation, not a fresh remote
    confirmation. No retry was spent (deny face).
  - The ask-literal grep pipeline is empty at this instrument version
    (findings not on stdout); the --json report face was used instead,
    after a --help flag verification (section 1).
  - The prose/identifier classification (3.2) is this agent's tooling,
    regex-faithful to the instrument word-face plus a lexical token-run
    rule plus one manual quotation judgment; it is not an instrument
    and its per-row labels are advisory to the fixing agent.
  - Instruments byte-stability across the agent window: the scans ran at
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
    the w13 trend card (this lane, Nov 23 2026)) for the 188/151/75/5
    attribution,
    the five budget card names, and the repair-candidate split; docs/
    jargon-to-standard-mapping-v1.md in full; tools/norm_lint.py in
    full; the batch-1 MANIFEST card (Nov 23 2026) in full.
  - NETRED ledger this agent: 1 network event (the failed fetch), zero
    retries, zero backoff, no curl, no MCP network calls.

## Appendix A1 - jargon findings, file:line term -> target form (188 rows)

the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 3: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 6: narration-passing word (stem-root h-...-r; jargon map table 5b) -> delete the narration; state the facts (or backtick-cite the h-...-r document identifier)
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 14: narration-passing word (stem-root h-...-r; jargon map table 5b) -> delete the narration; state the facts (or backtick-cite the h-...-r document identifier)
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 3: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 8: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 24: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 276: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 277: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 282: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 1: narration-passing word (stem-root h-...-r; jargon map table 5b) -> delete the narration; state the facts (or backtick-cite the h-...-r document identifier)
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 1: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 2: routing word (stem-root d-...-h; jargon map table 5b) -> route (narrative sense; the red_dispatch.py identifier stays)
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 2: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 4: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 9: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 9: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 13: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 15: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 43: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 60: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 65: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 83: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 87: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 89: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 97: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 98: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 102: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 107: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 108: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 1: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 76: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 94: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 123: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 165: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 192: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 195: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 207: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 1: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 2: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 4: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 5: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 11: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 13: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 19: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 45: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 62: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 68: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 77: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 82: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 82: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 86: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 87: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 3: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 15: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 19: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 42: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 45: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 46: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 49: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 52: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 58: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 63: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 70: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 71: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 178: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 182: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 186: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 218: work-stream word (stem-root w-...-e; jargon map table 5b) -> work stream (organizational sense; release sense stays on ledger surfaces)
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 237: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 239: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 243: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 245: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 252: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 254: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 260: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 264: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 268: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 278: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 1: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 4: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 7: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 8: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 22: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 24: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 33: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 36: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 40: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 73: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 86: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 97: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 104: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 110: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 111: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 113: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 128: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 145: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 146: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 149: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 153: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 155: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 156: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 160: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 2: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 5: organized-effort word (stem-root c-...-n; jargon map table 5b) -> effort / work stream
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 5: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 9: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 24: organized-effort word (stem-root c-...-n; jargon map table 5b) -> effort / work stream
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 39: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 45: organized-effort word (stem-root c-...-n; jargon map table 5b) -> effort / work stream
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 54: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 56: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 114: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 124: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 126: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 127: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 4: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 39: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 61: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 79: routing word (stem-root d-...-h; jargon map table 5b) -> route (narrative sense; the red_dispatch.py identifier stays)
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 81: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 92: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 96: routing word (stem-root d-...-h; jargon map table 5b) -> route (narrative sense; the red_dispatch.py identifier stays)
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 105: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 275: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 333: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 1: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 4: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 25: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 46: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 49: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 64: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 129: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 130: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 213: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 232: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 248: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 250: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 1: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 3: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 15: narration-passing word (stem-root h-...-r; jargon map table 5b) -> delete the narration; state the facts (or backtick-cite the h-...-r document identifier)
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 23: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 40: narration-passing word (stem-root h-...-r; jargon map table 5b) -> delete the narration; state the facts (or backtick-cite the h-...-r document identifier)
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 63: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 75: narration-passing word (stem-root h-...-r; jargon map table 5b) -> delete the narration; state the facts (or backtick-cite the h-...-r document identifier)
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 139: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 168: narration-passing word (stem-root h-...-r; jargon map table 5b) -> delete the narration; state the facts (or backtick-cite the h-...-r document identifier)
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 170: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 175: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 181: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 1: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 4: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 5: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 18: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 25: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 28: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 31: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 39: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 43: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 44: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 45: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 74: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 75: integration-arrival word (stem-root l-...-g; jargon map table 5b) -> integration
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 111: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 112: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 121: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 130: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 3: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 40: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 3: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 7: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 110: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 131: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 150: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 173: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 183: narration-passing word (stem-root h-...-r; jargon map table 5b) -> delete the narration; state the facts (or backtick-cite the h-...-r document identifier)
the window-readings card (Nov 22 2026) of the batch-1 lane, line 1: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 3: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 6: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 8: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 42: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 46: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 48: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 60: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 111: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 126: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 185: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 226: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent
the window-readings card (Nov 22 2026) of the batch-1 lane, line 231: role-holder word (stem-root s-...-t; jargon map table 5b) -> agent

## Appendix A2 - forbidden (date-stamp) findings, file:line token class (151 rows)

(class prose = slash-form curable per 3.2a; class ident-or-quote =
 identifier/quotation position, console channel per 3.2b)

the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 1: Nov 23 26 2026 dashed prose
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 4: Nov 23 26 2026 dashed prose
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 9: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 10: Nov 23 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 11: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 12: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 13: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 14: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 15: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 16: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 17: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 18: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 19: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 20: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 21: Nov 22 26 2026 compact ident-or-quote
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 22: Nov 22 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 8: Nov 22 26 2026 dashed prose
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 9: Nov 23 26 2026 dashed prose
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 10: Nov 22 26 2026 compact prose
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 65: Nov 22 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 140: Nov 16 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 141: Nov 14 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 144: Nov 14 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 145: Nov 21 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 146: Nov 13 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 148: Nov 11 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 150: Nov 14 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 151: Nov 22 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 155: Nov 16 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 157: Nov 11 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 290: Nov 22 26 2026 compact ident-or-quote
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 325: Nov 22 26 2026 dashed prose
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 325: Nov 22 26 2026 compact ident-or-quote
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 3: Nov 22 26 2026 dashed prose
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 9: Nov 22 26 2026 dashed prose
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 33: Nov 22 26 2026 dashed prose
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 33: Nov 22 26 2026 compact ident-or-quote
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 56: Nov 20 26 2026 compact ident-or-quote
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 59: Nov 22 26 2026 compact ident-or-quote
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 62: Nov 22 26 2026 compact ident-or-quote
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 65: Nov 22 26 2026 compact ident-or-quote
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 81: Nov 22 26 2026 dashed prose
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 11: Nov 22 26 2026 compact ident-or-quote
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 14: Nov 22 26 2026 compact ident-or-quote
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 16: Nov 22 26 2026 compact ident-or-quote
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 28: Nov 22 26 2026 dashed prose
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 49: Nov 16 26 2026 compact ident-or-quote
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 67: Nov 22 26 2026 compact prose
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 71: Nov 16 26 2026 compact ident-or-quote
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 221: Nov 22 26 2026 dashed prose
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 2: Nov 22 26 2026 compact ident-or-quote
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 3: Nov 20 26 2026 compact ident-or-quote
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 3: Nov 22 26 2026 compact ident-or-quote
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 7: Nov 22 26 2026 dashed prose
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 94: Nov 22 26 2026 dashed prose
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 1: Nov 22 26 2026 compact prose
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 32: Nov 22 26 2026 compact ident-or-quote
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 292: Nov 22 26 2026 dashed prose
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 12: Nov 22 26 2026 compact ident-or-quote
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 17: Nov 22 26 2026 compact ident-or-quote
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 18: Nov 22 26 2026 compact ident-or-quote
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 28: Nov 22 26 2026 dashed prose
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 62: Nov 21 26 2026 compact ident-or-quote
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 62: Nov 22 26 2026 compact ident-or-quote
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 168: Nov 22 26 2026 dashed prose
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 2: Nov 22 26 2026 dashed prose
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 3: Nov 22 26 2026 dashed prose
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 4: Nov 20 26 2026 compact ident-or-quote
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 4: Nov 22 26 2026 compact ident-or-quote
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 24: Nov 15 26 2026 compact ident-or-quote
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 45: Nov 15 26 2026 compact ident-or-quote
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 126: Nov 22 26 2026 dashed prose
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 1: Nov 22 26 2026 compact prose
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 7: Nov 22 26 2026 dashed prose
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 10: Nov 22 26 2026 compact ident-or-quote
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 44: Nov 22 26 2026 compact ident-or-quote
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 104: Nov 22 26 2026 compact prose
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 175: Nov 20 26 2026 compact ident-or-quote
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 221: Nov 13 26 2026 compact ident-or-quote
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 337: Nov 22 26 2026 dashed prose
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 16: Nov 22 26 2026 compact ident-or-quote
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 18: Nov 22 26 2026 compact ident-or-quote
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 32: Nov 22 26 2026 dashed prose
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 89: Nov 23 26 2026 dashed prose
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 138: Nov 22 26 2026 compact ident-or-quote
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 236: Nov 22 26 2026 compact ident-or-quote
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 238: Nov 22 26 2026 compact ident-or-quote
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 239: Nov 22 26 2026 compact ident-or-quote
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 240: Nov 22 26 2026 compact ident-or-quote
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 241: Nov 22 26 2026 compact ident-or-quote
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 256: Nov 22 26 2026 dashed prose
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 15: Nov 20 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 21: Nov 22 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 31: Nov 22 26 2026 dashed prose
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 41: Nov 22 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 44: Nov 22 26 2026 compact prose
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 54: Nov 22 26 2026 compact prose
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 89: Nov 14 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 90: Nov 11 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 91: Nov 13 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 94: Nov 16 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 95: Nov 14 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 97: Nov 21 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 98: Nov 11 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 99: Nov 14 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 100: Nov 22 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 112: Nov 16 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 113: Nov 14 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 117: Nov 22 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 119: Nov 14 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 120: Nov 21 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 121: Nov 11 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 123: Nov 13 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 126: Nov 11 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 129: Nov 14 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 199: Nov 22 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 207: Nov 22 26 2026 dashed prose
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 208: Nov 16 26 2026 compact ident-or-quote
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 248: Nov 22 26 2026 dashed prose
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 11: Nov 22 26 2026 dashed prose
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 20: Nov 20 26 2026 compact ident-or-quote
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 23: Nov 22 26 2026 compact ident-or-quote
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 30: Nov 22 26 2026 compact ident-or-quote
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 34: Nov 22 26 2026 dashed prose
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 34: Nov 23 26 2026 dashed prose
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 41: Nov 23 26 2026 dashed prose
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 7: Nov 22 26 2026 dashed prose
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 10: Nov 22 26 2026 compact ident-or-quote
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 146: Nov 22 26 2026 compact ident-or-quote
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 152: Nov 22 26 2026 compact ident-or-quote
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 165: Nov 22 26 2026 dashed prose
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 7: Nov 22 26 2026 dashed prose
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 8: Nov 23 26 2026 dashed prose
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 9: Nov 22 26 2026 compact prose
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 12: Nov 22 26 2026 compact ident-or-quote
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 33: Nov 21 26 2026 compact ident-or-quote
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 42: Nov 22 26 2026 compact prose
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 107: Nov 22 26 2026 compact ident-or-quote
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 178: Nov 22 26 2026 compact ident-or-quote
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 180: Nov 22 26 2026 compact ident-or-quote
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 196: Nov 22 26 2026 dashed prose
the window-readings card (Nov 22 2026) of the batch-1 lane, line 27: Nov 22 26 2026 compact ident-or-quote
the window-readings card (Nov 22 2026) of the batch-1 lane, line 30: Nov 22 26 2026 compact ident-or-quote
the window-readings card (Nov 22 2026) of the batch-1 lane, line 32: Nov 22 26 2026 compact ident-or-quote
the window-readings card (Nov 22 2026) of the batch-1 lane, line 34: Nov 22 26 2026 compact ident-or-quote
the window-readings card (Nov 22 2026) of the batch-1 lane, line 50: Nov 22 26 2026 dashed prose
the window-readings card (Nov 22 2026) of the batch-1 lane, line 116: Nov 22 26 2026 dashed prose
the window-readings card (Nov 22 2026) of the batch-1 lane, line 120: Nov 22 26 2026 dashed prose
the window-readings card (Nov 22 2026) of the batch-1 lane, line 123: Nov 22 26 2026 compact prose
the window-readings card (Nov 22 2026) of the batch-1 lane, line 177: Nov 22 26 2026 dashed prose
the window-readings card (Nov 22 2026) of the batch-1 lane, line 257: Nov 22 26 2026 dashed prose

## Appendix A3 - header findings, file:line missing-field (75 rows)

the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 1: Dependencies.
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 1: Evidence.
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 1: Exit-codes.
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 1: Interface.
the batch-1 MANIFEST card (Nov 23 2026) of the batch-1 lane, line 1: Purpose.
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the w12 trend card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the `handover-verify` v8.3 card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the mainmove card, 9332c2b5 (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the mcp-pilot2 card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the mcp-stage2 card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the mcp-w4-recheck card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the new-anchor-readings card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 1: Dependencies.
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 1: Evidence.
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 1: Exit-codes.
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 1: Interface.
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 1: Purpose.
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the w11 feedback trend card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the w12 feedback trend card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
the window-readings card (Nov 22 2026) of the batch-1 lane, line 1: Dependencies.
the window-readings card (Nov 22 2026) of the batch-1 lane, line 1: Evidence.
the window-readings card (Nov 22 2026) of the batch-1 lane, line 1: Exit-codes.
the window-readings card (Nov 22 2026) of the batch-1 lane, line 1: Interface.
the window-readings card (Nov 22 2026) of the batch-1 lane, line 1: Purpose.
## Appendix A4 - budget findings, file:line term (5 rows)

the mcp-roster51-verify card (Nov 22 2026) of the batch-1 lane, line 1: header-budget
the pr32-continue-watch card (Nov 22 2026) of the batch-1 lane, line 1: header-budget
the pr32-desk-i18n card (Nov 22 2026) of the batch-1 lane, line 1: header-budget
the rsi-reshoot card (Nov 23 2026) of the batch-1 lane, line 1: header-budget
the window-readings card (Nov 22 2026) of the batch-1 lane, line 1: header-budget