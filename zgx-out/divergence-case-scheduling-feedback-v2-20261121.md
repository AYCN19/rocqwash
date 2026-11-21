# Divergence case file v2: `docs/scheduling-feedback.json` -- committed face vs recomputed face (three values, scheduling feedback) -- root-cause-confirmed edition
Ticket: R2-48 (case file v2 casting agent, written form; identity live-lumen, host Darwin arm64)
Purpose.  Case record for the `docs/scheduling-feedback.json` divergence: the committed
  canonical face (blob a952af0, 3/46/0.0588 over "51 rows") vs the deterministic recompute
  (blob 06998c8, 1/38/0.0244 over 41 rows). Registers the face-value table, the confirmed
  root cause (H1, HIGH, survived two falsification runs R2-44), the H2-H6 dispositions, the
  three desk options with their measured consequences, the residual unknowns, and the
  reproduction base. Disposition remains open; the ruling power rests with the desk: this
  file registers the measured consequences of the options and does not choose for it.
Interface.  Prose record face (not executable). Supersedes v1 (R2-39, same directory,
  `divergence-case-scheduling-feedback-20261121.md`) with v1's section 2 timeline and
  section 5 command base preserved (sections 2 and 7 here); companion execution record
  `../R2-48-receipt.md`; conclusions tagged [R2-39 records] / [R2-44 records] throughout.
Dependencies.  `return-package/divergence-case-scheduling-feedback-20261121.md` (v1 case
  file), `return-package/divergence-rootcause-recon-20261121.md` (R2-44 recon card),
  `../R2-44-receipt.md` (R2-44 execution record),
  `/Users/zuguangzhao/rocqwash/zgx-out/zgx-ledger-proposals.jsonl` (lines 22/23, verified
  by this agent this session, section 8), `tools/learning_feedback.py`,
  `docs/exp-ledger.jsonl`, `docs/b-gate-audit.json`.
Evidence.  The checks executed by this agent this session are listed verbatim in section 8;
  every other conclusion is cited to its agent of record; the whole file is written on the
  baseline of the root-cause finding: the face was integrated ahead of its input, and the
  10 ghost rows never reached the repository. Supersession note: v1's carried-over sections
  are a faithful transcription of v1; where wording or numbers differ, the v1 English
  original governs.
Exit-codes.  Not applicable (prose record face; no exit codes are defined or altered).
Discipline: this agent ran zero git queries, zero network, zero repository-tree writes this session; writes are exactly two files -- this case file v2 and `../R2-48-receipt.md`. Everything marked [R2-39 records] / [R2-44 records] was executed by the original agent and is transcribed here verbatim by citation; the only checks this agent executed personally, with output shown, are those in section 8.

---

## 1. The case in one paragraph (post-verdict form)

v1's one-sentence statement stands verbatim: at every sampled anchor since 2026-11-19, the committed canonical face of `docs/scheduling-feedback.json` and the deterministic recompute of `tools/learning_feedback.py` over the same commit's own inputs disagree in exactly the three repair_outcomes values; every other byte of the file is identical, and the companion face `docs/b-gate-audit.json` recomputes byte-identical everywhere -- the divergence class is specific to scheduling-feedback.json.

Face-value table (values cited from proposal lines 1/15/19/21 and the R2-36 execution record; blob identities re-pinned in the R2-39 session):

| side | blob | sha256 | repair_outcomes (repaired / unrecorded / rate / wogc / escalated) | total rows |
|---|---|---|---|---|
| canonical (committed) | a952af079aa8e6baf68b38f60a5d68248963d86e | 1ed190e168041c74488086f3aa5f55711a2a140fc436e043b0c183f58db19b14 | 3 / 46 / 0.0588 / 2 / 0 | 51 |
| recompute (produced) | 06998c8fbbcf3d88087d370fc1556bcb3fce8b08 | e66ca0a1d1b862b6b0554b96d7852ed4b39e239a32f114ba09199fbadb9c423b (full value) | 1 / 38 / 0.0244 / 2 / 0 | 41 |

v1 recorded only a 16-hex prefix of the produced-side sha256 (v1 honesty note 6); the full 64-hex value was supplied by the r24 batch (proposal line 23, verified by this agent in section 8), and the gap is closed.

One sentence that became sayable only after the verdict (v1 could not say it): the canonical side's "51" was never a committed fact -- it is the input row count at the face's generation time. compute_repair adds 1 to total for every valid JSONL row and sets rate = repaired/total (tool lines 256-276), so the committed total=51 implies exactly 51 valid input rows at generation time; the committed ledger, however, has only 41 rows, and no blob in the entire history has 51 rows (evidence 3 in section 4.2). [R2-44 records]

Delta arithmetic (fail-loud correction, on record in R2-44): the ticket's wording "8 lines" was only the unrecorded delta (46-38); the measured total delta is 10 rows -- unrecorded +8, repaired +2; wogc=2 and escalated=0 are identical on both sides (re-pinned from the committed face). The three-value difference is one quantity in two notations: 3/51=0.0588, 1/41=0.0244.

F1-F6 (v1 section 1, all still true, one line each): F1 the canonical blob is a952af0 at all 10 anchors; F2 recompute determinism (all four archived recomputed faces are 06998c8; the r20 rerun cmp rc=0); F3 the divergence diff is always the same 471-byte three-value hunk (r12=r17=r20, cmp this session); F4 the sole repair input blob cf81fa36 is unchanged since 95460fd, 41 rows, and the tool says 1/38 over the committed input; F5 the face's last touch is fa879e4, before the case opened -- the face was stale on arrival; F6 the desk resolve 0a0a9c43 integrated the case's evidence faces and did not touch the face. The verdict upgrades F4's "no committed state can produce 3/46" from a tension to a proven survey result (evidence 3, section 4.2).

## 2. Timeline T0-T6 (carried verbatim from v1 section 2; a faithful transcription, v1's wording governs)

Anchor chain (each hop merge-base --is-ancestor YES; rev-list counts as follows; R2-39 records):
f1b6e27 ->(+2)-> 3e18590 ->(+2)-> 6998c40 ->(+1)-> 3a56b85 ->(+10)-> c48a548 ->(+8)-> 0a0a9c43 ->(+3)-> 8502146; f1b6e27..8502146 = 26 commits; c48a548..8502146 = 11; fa879e4 is an ancestor of f1b6e27 (6 commits).

| # | time (UTC) | anchor | what happened | batch stamp / proposal line | diff shape |
|---|---|---|---|---|---|
| T0 | 2026-11-19 22:13:39Z (batch); line 1 ts 22:17:23Z | f1b6e27 (1 of 3 samples) | Discovery. First sampling of f1b6e27 inside the /Users/zuguangzhao/rocqwash clone; the b-gate recompute is byte-identical to the committed face while scheduling-feedback diverges; recorded fail-loud, no cause asserted at the time | R1 batch 20261119T221339Z; proposal line 1 | git diff is exactly the three-value change (line 1 evidence; blob pair same as F1+F2) |
| T1 | 2026-11-19 23:00:26Z; line 2 ts 23:02:10Z | f1b6e27 (2 of 3 samples) | Second independent reproduction, second batch; same three values; b-gate still byte-identical | R2 batch 20261119T230026Z; proposal line 2 | same three-value change (line 2 evidence) |
| T2 | 2026-11-19 23:29:08Z; line 3 ts 23:30:00Z | f1b6e27 (3 of 3 samples) | Third independent reproduction; committed vs recompute checked with blob-level cmp (git show HEAD:docs/b-gate-audit.json output piped to cmp) | R3 batch 20261119T232908Z; proposal line 3 | same three-value change (line 3 evidence) |
| T3 | 2026-11-19 23:46:22Z; line 4 ts 23:46:58Z | 3e18590 | First cross-anchor sampling, first test at a new anchor after the PR#17 automerge; the divergence survived the anchor move; exp-ledger has 41 rows at both HEAD and fa879e4 -> the "uncommitted ledger state" hypothesis entered the record (no cause asserted at the time) | R4 batch 20261119T234622Z; proposal line 4 | the same three-value hunk quoted verbatim in r4-plan-run.log step 7; archived recompute face hash 06998c8 (R2-39 session) |
| T4 | 2026-11-20 14:16:31Z; line 15 ts 14:18:05Z | 6998c40 (as labeled; see caveat) | Fourth sampling under the "6998c40" label. Caveat (correlation ledger 9.7 note 3, confirmed by F1): no tool ever ran on 6998c40; the tip had moved +1 and the read anchor was in fact 3a56b85 (= 6998c40+1); 6998c40 itself was only checked for the committed face (canonical blob and values re-pinned at 6998c40 in the R2-39 session). The divergence switched to the rocqwash-loop clone here; the proposal upgraded to "recompute and integrate the new face" | R2-20 batch 20261120T141631Z; proposal line 15; archive r12-anchor-3a56b85-20261120T141631Z/ | r12-divergence.diff, 471 bytes, index a952af0..06998c8 (cmp this session) |
| T5 | 2026-11-20 16:51:50Z; line 20 ts 16:56:15Z | c48a548 | Fifth sampling, third independent anchor witnessing the same blob pair (after 0765d671 and 3a56b85); fetch went through the full NETRED path (30s low-speed abort rc=128, 120s backoff, HTTP/1.1 retry rc=0); the proposal added a process demand: a sync guard keyed to the face's input blob shas | R2-26 batch 20261120T165150Z; proposal line 20; archive r17-anchor-c48a548-20261120T165150Z/ | r17-divergence.diff == r12-divergence.diff, 471 bytes, index a952af0..06998c8 (cmp this session) |
| T6 | 2026-11-20 19:19:30Z; line 21 ts 19:24:17Z | 8502146 | Sixth sampling, first after the desk resolve 0a0a9c43; the divergence survived the desk action; line 21's wording: this face survived three reading agents and one desk resolve and is still stale; proposal unchanged (standing recompute + sync guard; line 21 calls it overdue) | R2-36 batch 20261120T191930Z; proposal line 21; archive r20-20261120T191930Z/ | r20-divergence.diff == r17 == r12, 471 bytes, index a952af0..06998c8 (cmp this session) |

Context rows (unnumbered sampling slots):

| # | time | event | evidence |
|---|---|---|---|
| C0 (added in v2, before T0) | 2026-11-19T17:40:19Z (fa879e4 adate 2026-11-20T01:40:19+08:00) | Birth commit fa879e4. The face a952af0 was born in a development commit: the same commit rewrote the tool v1.0 -> v1.1.0 (calibration wiring, snapshot EOL normalization) and touched no ledger among its 14 paths; the values of pre-image 432094a6 were exactly 1/38/0.0244 (the recompute-side values) -- this commit flipped the face from right to wrong, and the input-side 51-row dev-tree ledger did not come with it | R2-44 records (recon card sections 1-2); in-face diff 432094a6..a952af0 |
| C1 (before T0) | 2026-11-19 20:45:25Z | The supply-track PR#17 batch artifact zgx-out/scheduling-feedback.20261119T204525Z.json already carried the recompute-side values 1/38/0.0244; the automerge 3e18590 (2026-11-19T21:14:45Z, commit 97c809f carrying the batch) merged into main -- the case's recompute side was upstream before the case was discovered | values re-analyzed in the R2-39 session: git show 97c809f:zgx-out/scheduling-feedback.20261119T204525Z.json -> repaired=1 unrecorded=38 rate=0.0244; PR#17 touched exactly 3 files, all zgx-out/ (correlation ledger section 3) |
| C2 (between T4 and T5) | 2026-11-20 15:42:14Z (proposal ts); r5 batch 20261120T153929Z | The r5 agent read anchor 0765d671 (between 3a56b85 and c48a548, +9 to c48a548): manual recount under added classification rules (independent classification of the committed 41 rows by the tool's action vocabulary: 1 fix-content, 2 watch-only, 38 rows with no vocabulary token -- exact agreement with the tool) and the stale-on-arrival finding (input blob cf81fa36 unchanged since 95460fd, which precedes fa879e4); target renamed stale-scheduling-feedback-face | proposal line 19; blob identity and ancestry re-checked in the R2-39 session (F4) |
| C3 (between T5 and T6) | 0a0a9c43 committed 2026-11-21T03:03:06+08:00 (= 2026-11-20T19:03:06Z), 16 minutes before the T6 batch stamp | DESK RESOLVE: integrated the evidence track (38 zgx-out paths: reading-agent batches, r12 divergence evidence, governance proposals, dual-stamp environment snapshots 204525Z + 232908Z). docs/ untouched (section 3) | git show --name-only 0a0a9c43: 38 paths, 0 outside zgx-out/ (R2-39 session) |
| C4 (after T6) | tip then a4d8d50 (2026-11-21T03:30:24+08:00, 4 commits after 0a0a9c43) | The case was still open at tip: canonical face still a952af0; committed proposal ledger 20 lines (measured at 0a0a9c43, 8502146, a4d8d50) vs working tree 21 lines -- line 21 uncommitted, the same posture as every earlier batch line (correlation ledger 8 note 4) | git rev-parse a4d8d50:docs/scheduling-feedback.json -> a952af0; line counts at the three commits via git show (R2-39 session) |
| C5 (added in v2, after T6) | line 22 ts 2026-11-20T20:55:47Z; line 23 ts 21:22:43Z; recon card / execution record 2026-11-21 | The verdict landed on the record and post-verdict re-testing: the R2-44 recon card + execution record were delivered, proposal line 22 appended (root cause + precise guard target, json.loads self-check 21 -> 22); then the r24 batch (line 23) re-tested at the new upstream tip d27af2d -- divergence unchanged (exactly 3 diff lines, index a952af0..06998c8), input blob cf81fa36 unchanged, face last touch still fa879e4; in between, one unlogged fetch+checkout at 21:07:49Z (disclosed in netred_p6.md, see residual 3 in section 6). R2-48 cast this case file v2 | R2-44 execution record; lines 22/23 verified by this agent in section 8 |

Numbering note: in the correlation ledger's trajectory numbering T0-T7, ledger-T0 = C1 of this file and ledger-T1..T7 = T0..T6 of this file. This file follows the ticket's sampling-anchor scheme and is self-consistent.

Closed-form assertion (carried verbatim from v1): at every sampling slot the diff index names the same blob pair a952af0..06998c8 -- the committed side because the canonical blob is the same at all anchors (F1), the produced side because every archived recomputed face hashes 06998c8 (F2), and the literal index line appears in the three archived diff files, byte-identical to one another (F3). The line 23 (r24, d27af2d) re-test extends the assertion to the post-verdict new upstream tip.

## 3. The desk resolve 0a0a9c43: what was integrated and what was not (carried from v1 section 3; the openness rationale updated to the post-verdict form)

What the resolve is (R2-39 records): the single-parent commit 0a0a9c43d4fc7aa11ba806d4ce2cc4da9375c955 (parent a07403e), message "chore(zgx-out): land PR#18 content via desk resolve - her planface reading batches at anchors f1b6e27/3e18590/3a56b85/c48a548, r12 divergence evidence, governance proposals, and the dual-stamp environment snapshots (204525Z + 232908Z both preserved); zgx actor namespace (PR#18 resolve)", committer date 2026-11-21T03:03:06+08:00; ancestor of 8502146 (c48a548 -> 0a0a9c43 = 8; 0a0a9c43 -> 8502146 = 3) and also of a4d8d50 (+4).

What was integrated (38 paths, measured, R2-39 records): all zgx-out/ (grep -c . = 38, grep -vc '^zgx-out/' = 0). The R20 task instruction said "40 items"; the commit actually carried 38 (correlation ledger 10.3 on record; the 40-vs-38 wording belongs to the integration-verification agent R2-35's jurisdiction, not to this case). The proposal evidence track has 20 committed lines at each of 0a0a9c43/8502146/a4d8d50 -- lines 1-20 all upstream. Dual-stamp environment closure: environment.20261119T204525Z.txt and 232908Z.txt both present, blobs differing only in the line 3 stamp.

What was not done: docs/ untouched -- none of the 38 paths leaves zgx-out/; the face's last touch remains fa879e4; the canonical blob is still a952af0 at both 0a0a9c43 and 8502146, values 3/46/0.0588 (F1). The stale face survived its own integration: the same resolve that took the divergence evidence into zgx-out/ left the face the evidence describes stale in place under docs/ -- one and the same commit.

Openness rationale (post-verdict form). The case stays open not for lack of evidence and not for unstable readings -- by T6 the divergence was deterministic, input-anchored, and byte-stable, on record across 7 batches / 10 anchors / 26 commits / 2 clones. v1 attributed the openness to the evidence/action asymmetry plus an authority question ("which face is authoritative"); after the verdict the former stands as before and the latter is half closed: R2-44 does not answer "which face is authoritative" for the desk, but it answers everything the evidence faces can answer -- the birth-commit-faithful product of the committed inputs is the recompute face (falsification run a in section 4.3; a mechanical fact on record). The case is therefore open at exactly one point:

1. The evidence faces are all upstream (0a0a9c43 integrated lines 1-20; lines 21/22/23 are on disk and on record; commit posture in section 9 note 3).
2. The object face (blob a952af0) has had no owner action on record since fa879e4.
3. The disposition (choosing one of A/B/C, deciding whether to pursue the intent layer) is a ruling, not evidence -- reading agents have no authority over it; proposals can only recommend (lines 15/19/20/21/22 recommend, none act).
4. Nothing in the pipeline recomputes this face and no guard keys it to its input, so every future reading agent will re-discover the divergence -- T4/T5/T6 and r24 (line 23) did exactly that. What 0a0a9c43 resolved was the case's record, not the case.

Case state OPEN, pending one desk ruling (among the options in section 5).

## 4. Root cause confirmed (new chapter)

### 4.1 The H1 statement (HIGH)

H1: the canonical face blob a952af0 was written by exactly one commit -- fa879e4 ("feat(evolution): two closing tickets ...", author 168888@live.cn, adate 2026-11-20T01:40:19+08:00 = 2026-11-19T17:40:19Z, single parent 5074eac). The same commit rewrote `tools/learning_feedback.py` (v1.0 -> v1.1.0, adding the calibration section) and replaced the face's pre-image blob 432094a6 -- whose values 1/38/0.0244 are byte-for-byte the recompute-side values -- with a952af0 (3/46/0.0588); meanwhile the face's sole repair input `docs/exp-ledger.jsonl` stayed at blob cf81fa36 throughout (41 rows, unchanged since 95460fd, which precedes fa879e4). Running fa879e4's own tool over its own committed input produces blob 06998c8 (1/38/0.0244, rc=0, errors=0) -- the birth commit cannot reproduce its own committed face. The all-refs ledger survey finds exactly 4 blobs in a strictly append-only prefix chain (27 -> 30 -> 38 -> 41 rows): no 51-row state and no 3x fix-content anywhere; the unreachable objects of both clones, the working trees, and the bounded host scan all lack the missing state. Therefore: the face was computed by a real tool run (output shape complete, calibration section included) over a then-local 51-row dev-tree ledger that preceded the shore ledger by 10 rows -- +2 action=fix-content, +8 rows with no action-vocabulary token -- and only the face was committed. The 10 input rows never reached any ref and are unrecoverable on this machine. The face was stale on arrival; every recompute since (including the zgx supply batch 3h05m after the face's commit, through r24/d27af2d) yields 06998c8. [R2-44 records, evidence in sections 4.2-4.3]

In plain words: one development commit handed in the finished report card while the original answer sheet stayed behind in a work tree that never entered the repository, and the answer sheet was later lost. From then on the whole pipeline repeatedly reconciled the report card against a mismatched answer sheet, and every round found the mismatch -- what was missing was never the accounting; it was those 10 rows.

### 4.2 The three decisive pieces of evidence (all executed in the R2-44 session, commands verbatim)

Evidence 1, birth-point archaeology. `git log --follow --format='%H|%aI|%cI|%an|%cn|%s' -- docs/scheduling-feedback.json` (run in both clones). The full-history clone yields exactly two commits: f88fe9af (2026-11-19T06:14:24+08:00, creation; face blob 432094a6, values analyzed by that agent as 1/38/0.0244 -- the recompute-side values; the same commit created the tool and the repair-plan-ledger history) and fa879e4 (2026-11-20T01:40:19+08:00, the birth of a952af0; git rev-parse fa879e4:docs/scheduling-feedback.json = a952af0..., fa879e4^: = 432094a6). No later commit ever touched the face (consistent with F1/F5). The same fa879e4 commit carried 14 paths (ci-whitepaper, learning-feedback.md, pin-provenance-v2, scheduling-feedback.json, the jargon SPEC + two snapshots + jargon-map + test_snippet, t_engines_seeds, and the four tools evolution_dashboard/jargon_map_sync/learning_feedback/pin_repair), none of them a ledger -- the face rewrite was carried inside a tool-feature commit, not a ledger-integration commit. The rocqwash shallow clone's --follow sees only 3e18590 -- a shallow-graft artifact (is-shallow-repository=true, .git/shallow holds 2 commits), not a second birth; the full-history clone is the authority on history.

Evidence 2, birth-state sandbox recompute. `git archive fa879e4 | tar -x -C /tmp/r244-sbx && python3 -I tools/learning_feedback.py` -> stdout "repair: repaired=1 escalated=0 watch_only_guard_correct=2 unrecorded=38 repair_action_rate=0.0244", rc=0, errors: 0; the written face git hash-object = 06998c8fbbcf3d88087d370fc1556bcb3fce8b08 -- exactly the recompute blob. The birth commit's own tool over its own committed input cannot reproduce its own committed face; if H1 were false (the committed state already sufficient), this run would have produced a952af0/3/46. The /tmp sandbox is a registered exception; the scratch files were deleted after the check (residual 5, section 6).

Evidence 3, the all-refs ledger survey. `for c in $(git log --all --format=%H -- docs/exp-ledger.jsonl); do git rev-parse $c:docs/exp-ledger.jsonl; done | sort -u` -> exactly 4 blobs:

| blob | first integrated in commit | date (+08:00) | rows | fix-content | watch-only | escalated | no token |
|---|---|---|---|---|---|---|---|
| ffd36594 | 523e7d4 | 2026-11-14T14:05:03 | 27 | 1 | 0 | 0 | 26 |
| 343fa11d | 70bb8c0 | 2026-11-15T17:00:39 | 30 | 1 | 0 | 0 | 29 |
| 3760669b | a69f370 | 2026-11-17T06:01:12 | 38 | 1 | 2 | 0 | 35 |
| cf81fa36 | 95460fd | 2026-11-19T02:16:45 | 41 | 1 | 2 | 0 | 38 |

A strictly append-only chain (each older blob is a byte prefix of the newer one; 3/3 links True, python prefix check by that agent). No 51-row state anywhere in committed history: absent from all refs, all tags, all fetched remote branches, and the 3 locally present PR heads (8b528beb/PR10, 918d5f00/PR12, ad4e5d26/PR15, all carrying 343fa11d); `git fsck --unreachable --no-reflogs` finds 0 ledger-shaped unreachable blobs in either clone (the 41 unreachable blobs of rocqwash are all merge-conflict/document residue); the three working-tree ledgers are all cf81fa36/41 rows (f233b26 is the seventh anchor); a bounded host JSONL scan (files of 45-60 lines x action=fix-content) yields zero candidates.

### 4.3 Two falsification runs (H1 survived both)

- Falsification run (a), "can the birth-era tool over the committed inputs produce the face?" -- DISPROVEN: this is evidence 2. It produced 06998c8, not a952af0. [RUN]
- Falsification run (b), "does some committed ledger state produce 3/46?" -- DISPROVEN: this is evidence 3. No blob has 51 rows; the sole blob set is the strict prefix chain ending at cf81fa36. [RUN]
- The inverse form, recorded honestly: the inverse of the ticket's example test -- "recomputing over the row set predicted by H1 should give 3/46" -- is not executable: the H1 row set cannot be materialized (absent from refs, unreachable objects, working trees, and host files alike). Recorded NOT RUN (impossible); the survey result stands in its place. [R2-44 on record]

### 4.4 Dispositions for H2-H6

| hypothesis | content | disposition | basis (all R2-44 records) |
|---|---|---|---|
| H2 | birth-era tool-rule defect (= option B1's form) | REFUTED, HIGH | fa879e4's own tool over its own committed input yields the recompute face (falsification run a); REPAIR_TOKENS and EXP_DEFAULT at birth = current (tool lines 91 / 100-105; the diff to 8502146 touches none of the classification core); C2's manual recount independently re-checked (proposal line 19) |
| H3 | a foreign input file (another 51-row JSONL) | LOW, residual | EXP_DEFAULT fixed at birth as ("docs","exp-ledger.jsonl") [RUN]; bounded host scan zero candidates [RUN]. Cannot be fully falsified -- a deleted file leaves no trace; recorded as a residual, not asserted |
| H4 | a hand-edited face (not a tool run) | LOW, residual | the fa879e4 face diff adds a fully schema-coherent calibration section (entries 0 / ledger_present true / agreement null) while the calibration_ledger row count in cf81fa36 = 0 [RUN] -- exactly the output shape of a real run over the committed input (or a 51-row superset containing no calibration rows); the rounds face byte-untouched. A hand edit would have to invent the section out of thin air while leaving rounds untouched. Cannot be strictly falsified; recorded as a residual |
| H5 | the delta rows were desktop-side entries, integrated upstream later | desktop-side origin HIGH; late integration REFUTED, HIGH | dual-side desktop appends are established ledger practice: the 95460fd message ("rows appended in the dev-tree ledger and landed via API git-data") and a69f370 ("union-sync the exp/repair ledgers after the rebase dance (both-side appends)"). But the 10 rows in question never reached anywhere: survey + fsck + working tree + host scan all negative [RUN]. The 10 rows are ghost rows: recorded on the desktop (or parked somewhere), never shipped |
| H6 | history rewrite / unfetched remote refs hiding a 51-row commit | LOW, partially open | no supporting evidence -- the strict prefix-chain survey plus fa879e4's tool-commit character already explain the state. The residual gap, stated honestly: 12 remote refs unfetched (single-flight ls-remote enumeration rc=0; a fetch would modify the odb, forbidden by the read-only discipline); the 3 locally present PR heads are all clean. Chronology (PR numbers, batch35-20261117, tag dates) places the unfetched refs at or after the case window. Post-verdict developments in residual 3, section 6 |

### 4.5 Chronological corroboration and the ghost-row window

The 10-row delta decomposes as: +2 rows action=fix-content (repaired 3 vs 1), +8 rows carrying no REPAIR_TOKENS vocabulary token (unrecorded 46 vs 38); watch-only (2) and escalated (0) unchanged. The time window is bounded by committed data: later than the shore ledger's last row ts 2026-11-18T17:05:56Z (EXP-20261118-0002), earlier than the face's commit instant 2026-11-19T17:40:19Z. The exact content is unrecoverable (residual 1, section 6).

Corroboration: the zgx supply batch artifact at 2026-11-19T20:45:25Z (3h05m after the face's commit) already carried 1/38/0.0244 -- the 51-row state was no longer in (or was never in) the supply track's tree when it ran; the instant the 51-row dev-tree state is positively pinned is exactly the face's commit instant. The "desktop-side late integration" question (the ticket's original words, romanized "houtao ru zhang", as transliterated by R2-44) is answered: desktop-side origin YES, late integration NO (H5 in section 4.4). [R2-44 records]

## 5. The three desk-side options: measured consequences after the verdict (decision surface with the desk; adjudication forbidden)

The non-adjudication clause (carried verbatim from v1 section 4, not loosened by a word): this file establishes no correctness ranking, expresses no preference, and closes nothing. The case remains OPEN until the desk rules. What the verdict changed is the measured cost and feasibility of each option -- not who makes the choice.

### Option A -- recompute and integrate the new face: mechanical support

Post-verdict support: the recompute face is the birth-commit-faithful product of the committed inputs (falsification run a in section 4.3: birth tool x committed input = 06998c8, rc=0 errors=0), and it has been the supply track's face since 2026-11-19T20:45:25Z; the family precedent stands (docs/b-gate-audit.json recomputes byte-identical to the committed face at every anchor, blob 6c823880..., re-pinned in the R2-39 session). The acceptance gates v1 section 4 set for column A remain valid verbatim: rerun rc=0 errors=0 at the new anchor; the diff limited to the 3 repair_outcomes fields with all other bytes identical; rerun determinism cmp rc=0; the integration commit touches docs/ (the first commit to do so since fa879e4) and carries the divergence-evidence references (lines 15/19/20/21/22); the guard demonstrably fires on the "ledger appended without face rerun" fixture. The verdict adds one natural acceptance gate of its own: the integration blob should be 06998c8 or a descendant -- if it is not, the inputs at the integration anchor have changed and the case must be re-established per the new inputs, not the old values copied.
On-record recommended wording: lines 15/19/20/21 (regenerate-and-land), line 22 strengthened with the verdict mechanism.

### Option B -- keep the canonical face, fix the recompute side: both forms defeated

B1 (tool-rule defect) -- counter-evidenced on record: H2 REFUTED, HIGH (section 4.4). The birth tool over the birth input = the recompute face; the classification core is unchanged since birth; C2's manual recount independently re-checked. B1's discharge burden (demonstrating the rule defect from a committed state) currently has no supporting evidence on record and two independent pieces of counter-evidence. If the desk still wants to pursue B1, it must first overturn falsification run (a) or the C2 recount -- both are RUN on record; overturning them is new evidence work, not re-assertion.

B2 (supply the missing 51-row input state) -- infeasible as the case record stands: R2-44's measured conclusion, verbatim, is measured impossible-on-record. The survey proves no committed state can produce 3/46 (evidence 3, section 4.2); the ghost rows are unrecoverable on this machine (the survey's hunt, all negative, section 4.2). B2's discharge burden (supplying the state or a reconstruction of it, and demonstrating the tool yielding 3/46/0.0588) cannot be met with anything on the case record. The only theoretical exit lies outside the record: the author's other machine may still hold the then-current work tree -- the machine-local archive can neither prove nor disprove its existence, and the desk must seek that evidence from the author directly. This file registers, honestly, that this exit exists and is not on record.

The acceptance gates v1 section 4 set for column B (a corrected tool or a repaired input reproducing 3/46/0.0588 over the committed state, all other faces unchanged, and no disturbance to b-gate-audit or the six-tool battery) are carried over verbatim, for the desk to use if it opens a new path.

### Option C -- other paths (carried verbatim from v1, updated item by item)

- C1, integrate the guard only (leave the face): the verdict gives the guard a precise target -- a guard keyed to the input blob shas would have fired at fa879e4 itself: the face was rerun without the ledger being integrated, the exact mirror image of "ledger appended while the face was not rerun" (line 22's wording). But C1 does not resolve the divergence on record: the existing divergence would trip the guard immediately, in effect pushing the desk back to A or B.
- C2, close the case with a "known-state" annotation: the post-verdict cost is clearer -- the case file would then carry both "root cause proven" and "the face keeps its wrong values", and every future reading agent would still re-discover the divergence (7 batches and 10 anchors so far, with d27af2d added by line 23) unless the reading protocol itself changes -- a suppressive change whose cost belongs to the desk; the F2/F4 determinism evidence would remain on record with no reconciling account.
- C3, a dedicated integration/verification packaging agent: applicable to A or B; changes the executor, not the assertion; this file's zero-reuse rule for its own numbers stands.
- C4, any other construction the desk defines.

Decision surface with the desk; adjudication forbidden: the above is measurement, not a ruling. Option A's mechanical support does not make A correct -- "authoritative" could still belong to B: if the desk holds that the ghost rows are the ledger that should have been, that is an intent ruling requiring evidence from the author, and this file has no such authority. The case is OPEN, pending one desk ruling.

## 6. Five residual unknowns (stated honestly)

1. The exact content of the ghost ten rows (+2 fix-content, +8 without token; window (2026-11-18T17:05:56Z, 2026-11-19T17:40:19Z]): unrecoverable by any of the four routes -- refs, unreachable objects, working trees, host files; the arithmetic pins only the token-class counts. The inverse recompute over the real rows is NOT RUN (impossible); the survey stands in its place.
2. The holding machine / work tree: which specific work tree or machine held the 51-row state at the commit instant is undecidable -- every environment snapshot on record has host=Darwin/arm64, leaving nothing to distinguish.
3. The contents of the 12 unfetched remote refs (the H6 residual): the R2-44 session only enumerated them with ls-remote (rc=0); a fetch was forbidden by the read-only discipline, so the contents are unverified. Post-verdict developments (line 23, verified by this agent in section 8): d27af2d was pulled into the loop clone by one unlogged fetch+checkout at 21:07:49Z and became upstream main's tip (disclosed in netred_p6.md); the r24 batch (line 23) re-tested on it -- divergence unchanged, input blob cf81fa36 unchanged, face last touch still fa879e4; that is, at least main's tip among the 12 refs has been verified and hides nothing. The remaining refs' contents are still unverified -- low risk (chronology places them at or after the case window) but not falsified; kept on the record honestly.
4. Author intent (whether the ghost rows were ever meant to ship): unknowable from artifacts. Late integration is normal ledger history (the 95460fd/a69f370 messages), and "forgot to integrate" is the most parsimonious reading -- but parsimony is not evidence; if the desk needs an intent finding, the only evidence source is the author.
5. The sandbox exception and the bounded scan's boundary: the verdict's decisive recompute (falsification run a) ran under the /tmp sandbox exception (/tmp/r244-sbx and r244-* scratch files, deleted after the check); the evidence on record is only the captured stdout and the produced-face blob 06998c8, and verification means re-running the two commands verbatim. Recorded in the same frame, honestly: the first full-_home JSONL scan was killed past 120s and replaced by the bounded scan -- "zero candidates on this machine" is a bounded negative, not an exhaustive one.

## 7. Reproduction base

Divergence-face base: every command of v1 section 5 (5.1 proposal-ledger integrity, 5.2 anchor chain, 5.3 canonical-face survey, 5.4 diff-archive byte identity, 5.5 recompute determinism and blob re-pinning, 5.6 the T0 merge batch artifact, 5.7 resolve contents, 5.8 repair-input identity, 5.9 the reading-agent evidence sequence) remains valid verbatim; v1 section 5 governs word for word and is not repeated here. [R2-39 records]

Post-verdict commands (R2-44 records, verbatim in section 4.2; summary):
- Birth-point archaeology: git log --follow --format='%H|%aI|%cI|%an|%cn|%s' -- docs/scheduling-feedback.json (both clones)
- Birth-state sandbox recompute: git archive fa879e4, extracted with tar to /tmp/r244-sbx, then python3 -I tools/learning_feedback.py (the /tmp exception)
- All-refs survey: git log --all --format=%H -- docs/exp-ledger.jsonl, rev-parse of the blob per commit, then sort -u
- Prefix-chain check: pairwise byte-prefix check (python, 3/3 True)
- Unreachable-object search: git fsck --unreachable --no-reflogs (both clones)
- Tool-core read points: tools/learning_feedback.py line 91 (EXP_DEFAULT), lines 100-105 (REPAIR_TOKENS), lines 256-276 (compute_repair)
- Remote-ref enumeration: git ls-remote origin (single flight, enumeration only)

## 8. Checks executed by this agent this session (R2-48, verbatim)

1. Proposal-ledger on-disk verification (read-only, /Users/zuguangzhao/rocqwash/zgx-out/zgx-ledger-proposals.jsonl):
   - `wc -l` -> 23 (the R2-44 execution record notes its session went 21 -> 22; a later line followed, see item 3 below).
   - `sed -n '22p'` piped to `python3 -I` (json.loads + field output + ASCII assertion) -> json OK; ts=2026-11-20T20:55:47Z, actor=zgx, target=docs/scheduling-feedback.json, schema=zgx-proposal/1, ascii_only=True -- matching the R2-44 execution record's line 22 field for field; R2-44's append is confirmed on disk.
   - `tail -n 1` (= line 23) piped to `python3 -I` -> json OK; ts=2026-11-20T21:22:43Z, actor=zgx, target=docs/scheduling-feedback.json, kind=proposal, ascii_only=True; the evidence field records the r24 batch 20261120T212043Z: the d27af2d re-test (six tools rc=0; face cmp first difference at line 17 char 400; committed sha256 1ed190e1... / produced e66ca0a1...b9c423b full values; diff exactly 3 lines; index a952af0..06998c8; 8eff64e..d27af2d = 3 commits with the three docs paths untouched; input blob cf81fa36 unchanged; face last touch fa879e4); it also discloses one unlogged fetch+checkout at 21:07:49Z (netred_p6.md). Line 23 falls under the r24 agent's jurisdiction; this file registers only its existence and its main points (C5, residual 3 in section 6).
2. Execution-record ASCII self-check (run after writing): `python3 -I` asserted ../R2-48-receipt.md all-ASCII -> ascii_only=True.
3. Both written files on disk: ls -l of this file and ../R2-48-receipt.md.

Beyond these, this agent ran zero checks; every conclusion on record is a citation (discipline line at the top).

## 9. Honesty notes

1. This agent ran zero git queries, zero network, zero repository-tree writes (writes are this file + the execution record only); no original agent's check was re-run -- that is this agent's task boundary (written casting), not an omission. Every conclusion on record is tagged with its original agent ([R2-39 records] / [R2-44 records]); the verification path = v1 section 5 + the recon card sections 2-4 commands.
2. The timeline is a faithful transcription of v1 section 2; where wording or numbers differ, the v1 English original governs, and any discrepancy is reported per the experience-face discipline, never silently rewritten.
3. The commit posture of lines 21/22/23: the R2-39 records show 20 committed lines (measured at 0a0a9c43/8502146/a4d8d50); line 21 was uncommitted; line 22 was appended by R2-44 (verified on disk by this agent); line 23 was appended by r24 (verified on disk by this agent). Whether the three have since reached upstream, this agent could not verify with zero git -- recorded honestly as "unverified".
4. 8eff64e and d27af2d: R2-44 observed the former as upstream main's tip at that time; line 23 records that the latter became the tip through the 21:07:49Z fetch+checkout and was re-tested on it. The facts at both SHAs come from other agents' records; this agent did not independently verify the git side -- cited honestly.
5. The produced-face sha256 full value (e66ca0a1d1b862b6b0554b96d7852ed4b39e239a32f114ba09199fbadb9c423b) was not recomputed by this agent; cited from line 23; the "16-hex prefix only" gap of v1 honesty note 6 is closed by it, with credit to the r24 agent.
6. This file adjudicates nothing (the section 5 clause) and appends no proposal line -- case-file agents do not propose (v1 honesty note 9 posture unchanged).
7. Every number in this file traces to the four sources at the top (sections 1-7 are citations); this agent's new measurements are only the three items in section 8.

## 10. Summary (condensed restatement; the section text above governs)

**Case.** At every anchor since 2026-11-19 the committed face of docs/scheduling-feedback.json (blob a952af0: repair_outcomes 3/46/0.0588 over "51 rows") disagrees with the deterministic recompute of tools/learning_feedback.py over the same commit's own inputs (blob 06998c8: 1/38/0.0244 over 41 rows) in exactly three values; everything else is byte-identical, and companion docs/b-gate-audit.json recomputes byte-identical everywhere. Total measured delta: 10 rows (+2 repaired, +8 unrecorded; wogc/escalated unchanged) - the "8 lines" framing was the unrecorded delta only (fail-loud correction on record by R2-44).

**Root cause - CONFIRMED, H1, HIGH (R2-44).** The stale face was born in one commit, fa879e4 (2026-11-19T17:40:19Z), which rewrote the tool (v1.0 -> v1.1.0), replaced the face's pre-image 432094a6 (whose values already were the recompute values) with a952af0, and touched no ledger path among its 14 paths: the face was computed by a real tool run against a then-local dev-tree exp-ledger of 51 valid rows (+2 action=fix-content, +8 token-less vs shore cf81fa36/41); only the face was committed. The face was stale on arrival; every recompute since - including the zgx supply batch 3h05m later and the r24 batch at d27af2d - yields 06998c8.

**Three decisive evidences.** (1) Birth archaeology: exactly two commits ever touched the face; the birth commit carried tool+face but no ledger. (2) Birth-state sandbox rerun: the birth commit's own tool over its own committed inputs yields 06998c8 (rc=0, errors 0), not the committed face. (3) All-refs survey: exactly 4 ledger blobs in a strict append-only prefix chain (27/30/38/41 rows); no 51-row state exists in any ref, tag, remote branch, local PR head, unreachable object, working tree, or bounded host scan.

**Two falsification runs (H1 survived both).** (a) "committed inputs + birth-era tool can produce the face" - DISPROVEN (rerun yields 06998c8); (b) "some committed ledger state yields 3/46" - DISPROVEN (survey). The inverse test over the real ghost rows is NOT RUN - impossible, the rows are unrecoverable; the survey stands in its place.

**H2-H6.** H2 birth-era tool-rule defect REFUTED HIGH (this is option B1's form); H3 foreign-input-file LOW residual; H4 hand-edited face LOW residual (coherent new calibration section, zero calibration_ledger rows in the committed ledger); H5 desktop-side origin HIGH / late integration REFUTED HIGH (the 10 rows are ghost rows, never shipped); H6 history-rewrite/unfetched-refs LOW, partially open (12 remote refs enumerated, not fetched at recon time; post-recon, d27af2d has since been fetched and re-read with the divergence intact - proposal line 23; the rest remain unverified).

**Desk options after the verdict - consequences mapped, no adjudication.** Option A (regenerate and land, the recorded proposal label) is mechanically supported: the recompute face is the birth-commit-faithful product of the committed inputs, plus the family precedent (b-gate-audit byte-identical at every anchor); a natural added gate: the integration blob should be 06998c8 or a descendant. Option B1 is counter-evidenced (H2 REFUTED; its discharge burden has no supporting evidence on record - overturning it would take new evidence work, not re-assertion). Option B2 is measured impossible-on-record (no committed state yields 3/46; the ghost rows are unrecoverable) - the only theoretical exit, the author's other machine, lies outside the record and is a matter for the desk to pursue with the author. The sync guard gains a precise target: keyed to input blob shas, it would have fired at fa879e4 itself (face rerun without ledger integration - the mirror shape). Selection remains the desk's; this file ranks nothing and closes nothing.

**Five residual unknowns.** (1) exact ghost-row content; (2) which tree/machine held the 51-row state at the commit instant; (3) contents of the 12 remote refs (d27af2d since fetched and re-read clean per line 23; the rest unverified); (4) author intent - unknowable from artifacts; (5) the evidence's own boundaries: the decisive rerun ran under the /tmp sandbox exception (scratch deleted; verification = re-running the recorded commands), and the "no candidate on this host" result is a bounded-scan negative, not an exhaustive one.

**Status.** Root cause CONFIRMED; case OPEN pending one desk ruling. This file supersedes v1 (R2-39) with the timeline and command base preserved; the casting agent (R2-48) ran zero git queries - every claim is attributed to its agent of record (R2-39 / R2-44 / r24 line 23 / R2-48 fresh checks in section 8).
