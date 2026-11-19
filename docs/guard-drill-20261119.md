# Guard drill: three trigger faces, temp repository only

Ticket: contract-guard-drill, the guard-drill contract inside the A-batch
  closed-loop cron guard consumption package
Statement faces: soft stop refusal; oscillation alert; rollback archive-then-revert;
  scheduling-feedback reading-face linkage
Source route: clone of the rocqwash repository at commit f88fe9af12248031bb55472a0c265c969779a0b4
  into a system temp directory; the drills ran only inside that clone, with
  tools/auto_round.py and tools/learning_feedback.py as committed at that SHA
Command: py -I -X utf8 tools/auto_round.py --repo-root . --autonomy autonomy-drill.json
  {commit|anchor|rollback|status} ... ; py -I -X utf8 tools/learning_feedback.py
Registry: docs/CAPABILITY-INDEX.md (auto_round, learning_feedback rows);
  the recursive-era CI whitepaper and the feedback-loop SOP under docs/
Purpose. Records the controlled drill of the three guard trigger faces and the
  feedback-face linkage, run entirely in a temp clone.
Interface. Documentation only; no code interface changes.
Dependencies. tools/auto_round.py and tools/learning_feedback.py at f88fe9af; git;
  Python 3 standard library.
Evidence. Command transcripts quoted per section below; feedback faces A, B, B2
  and C computed inside the temp clone.
Exit-codes. Not applicable (documentation face); tool exits are quoted where observed.

## 1. Scope and zero-touch attestation

- The repository under drill is a disposable clone; nothing in this drill ran against the real checkout except the read-only pre and post checks listed here.
- Real checkout before the drill: HEAD f88fe9af12248031bb55472a0c265c969779a0b4; git status carried two pre-existing modified files owned by concurrent work (docs/exp-ledger.jsonl, round-plan.json); refs/rocqwash held 1 ref; .git/hooks held no non-sample hooks; core.hooksPath unset.
- Real checkout after the drill, before this report: HEAD and refs unchanged; the same two pre-existing modified lines; no new refs; no new commits. Three untracked out_docseat_*.json files in the root belong to that same concurrent work; they appeared while the drill was running, and no drill command writes to the real checkout.
- The only real-checkout change attributable to this drill is the new file you are reading, the untracked deliverable the contract names.
- The clone showed the same hook-free shape (0 non-sample hooks, hooksPath unset), so the clone versus init fork risk named by the contract did not materialize.

## 2. Setup

- Drill autonomy file (clone root, autonomy-drill.json): max_unreviewed_rounds=4, oscillation_alert=2; verify_cmd omitted, so the default check ran (tools/norm_lint.py --selftest from the repo root), recorded as verify_kind=norm_lint in every ledger row.
- The clone carried the committed ledger state: 2 round rows, no anchor, 41 experience rows. Drill rounds therefore start at round 3, and the unreviewed counter starts at 2.
- Fixtures: docs/drill-note.md (one appended line per round); a hits file [{"file": "docs/drill-note.md", "line": 2}] kept outside the clone; both removed with the clone.
- Baseline tool vectors, all pass: auto_round --selftest (18 vectors), learning_feedback --selftest (4 of 4), norm_lint --selftest (exit 0).

## 3. Drill 1: soft stop

| step | command face | observed | exit |
|---|---|---|---|
| rounds 3 and 4 land | commit --classes date-strip --files docs/drill-note.md | round=3 head=c380f1a52fbf; round=4 head=37552073f51e | 0 |
| round 5 attempt, unreviewed=4 equals cap | same command, after appending line 4 | stderr: auto_round commit: soft stop: 4 unreviewed rounds reached the cap 4; remedy: 'anchor --promote' after review, or rerun with --continue | 1 |
| remedy | anchor --promote | anchor promoted head=37552073f51e rounds-covered=4 | 0 |
| round 5 retry | commit, same files | round=5 mode=auto head=47082ad8ed84 files=1 classes=date-strip | 0 |

Verdict: the refusal fires exactly at the cap, names the count, the cap and both remedies, and performs no write (HEAD stayed at the round 4 SHA until the promote). The bounded release arc is the review anchor. Counter at tools/auto_round.py:695-701; the cap check at tools/auto_round.py:780-785.

## 4. Drill 2: oscillation alert (alert=2)

| step | stdout | ledger row |
|---|---|---|
| round 6, first touch of docs/drill-note.md:2 | no alert line | oscillation_count=0 |
| round 7, second touch of the same site | oscillation-alert: docs/drill-note.md:2 touched in 2 rounds | oscillation_count=1, verify_kind=norm_lint, verify_rc=0 |

Verdict: the first touch is silent, the second fires a loud per-site warning, and the count lands in both the state file (line_hits {"docs/drill-note.md:2": 2}) and the ledger row. Accumulation at tools/auto_round.py:682-692; persistence on the commit path at tools/auto_round.py:821-846.

## 5. Drill 3: rollback archive-then-revert

- anchor --set 47082ad8ed848510c96d9e5368187ff5a204a98e (the round 5 tree) reported rounds-covered=7.
- rollback --to anchor printed: rollback round=8 drift-ref=refs/rocqwash/drift/20261118231014-7 head=ac4dbeda8535 files=1, exit 0 (the ref name is UTC stamped; the local zone was +08:00).
- Archive: the drift ref resolves to f6733149997ce3442d861652cc4600a79821b242, exactly the pre-rollback HEAD, and the tool refuses to overwrite an existing archive (tools/auto_round.py:951-955).
- Revert: docs/drill-note.md is back to the 4-line round 5 content. The row 8 ledger entry reads mode=rollback, base_sha=f6733149997c..., head_sha=ac4dbeda8535..., files=["docs/drill-note.md"], admissions=[], classes_applied=[], oscillation_count=0, verify_rc=0, verify_kind=norm_lint.
- History: linear, no rewrite; the round 6 and round 7 commits stay reachable; the revert commit carries the trailers Rocqwash-Round: 8 and Rocqwash-Mode: rollback. The mechanical check ran on the reverted tree before the commit (tools/auto_round.py:960-977).
- status face after the drill: rounds=8, unreviewed=1/4, anchor=47082ad8ed84 round=7, oscillation_sites=1.

Verdict: both mandatory steps observed in order (archive ref first, one revert commit second), content back at the anchor, archive pinned on the ref, ledger row in the rollback shape.

## 6. Feedback-face linkage

| face | when | rounds face | repair four-state face | exit |
|---|---|---|---|---|
| A, baseline | committed ledgers only | total=2, auto=1, human_approved=1, approval_rate_auto=0.5 | repaired=1, escalated=0, watch_only_guard_correct=2, unrecorded=38, rate=0.0244; errors 0 | 0 |
| B, after drills 1 to 3 | plus 6 round rows (3 to 8), no experience rows | total=8, auto=1, human_approved=1, rate=0.125 | identical numbers to A | 1 |
| B2, after round 9 | round 9 used --class-confidence drill-tone-guard=0.9 | total=9, auto=2, rate=0.2222 | unchanged | 1 |
| C, direction fixture | plus 2 experience rows in the clone (action=fix-content, action=escalated) | unchanged from B2 | repaired=2, escalated=1, watch_only_guard_correct=2, unrecorded=38, rate=0.0465 | 1 |

Findings:

1. Guard triggers alone do not move the repair four-state counts. The soft stop refusal and the rollback write no experience rows, and faces A and B carry identical repair numbers. Movement in escalated and repaired requires experience rows carrying action tokens (tools/learning_feedback.py:80-85 and 236-258), confirmed by face C.
2. The rounds face moves on every landed round and treats a rollback row as data only: row 8 lands in total, in neither auto nor human_approved, matching the documented reading rule at tools/learning_feedback.py:36-41.
3. Attribution finding: a factory-registry class (date-strip) rides every round as existing (CLASS_REGISTRY at tools/auto_round.py:162-168; the existing decision at tools/auto_round.py:262-263), so those rows carry empty admissions and the reading face reports one loud error per row, of the form class date-strip has neither an admitted admission nor a human-approved round-state entry (tools/learning_feedback.py:190-196), and exits 1. A confidence-graded non-registry class restores auto attribution (face B2). The committed real-ledger row 1 already uses the graded form (jargon at confidence 1.0), so scheduled consumers should keep the graded convention.

## 7. Wiring conclusion against the bounded-response requirement

The N3 section of the N-series derivation volume in the cross-line asset area (base f88fe9af) requires the guard trio to stand in front of any scheduled consumption of scheduling feedback, on the argument that unbounded feedback is the oscillation source. This drill confirms the trio from the action face: refusal is loud, names its remedies and performs no write; release from refusal runs through one explicit review-anchor act; a repeated touch is counted and warned per site; rollback archives before it reverts and checks the reverted tree before committing; and the feedback face reads outcomes without inventing them (rows outside the action vocabulary stay unrecorded, unattributable rows are named in errors, and exit 1 carries the account). The guard side is ready to sit in front of a bounded consumption tier; consuming the readings inside a scheduler stays out of scope here, as the contract names this drill only.

## 8. Cleanup attestation

- The temp clone and its fixtures were removed after the runs recorded above, and the removal was verified (the temp path no longer exists); nothing from the drill remains outside this report.
- No push, no remote contact, no runner, scheduled-task or MCP signature change; certification faces untouched.
