# draft-evolve-v55-20261113.md — next-round task-brief draft produced by tools/evolve.py (human-review gate deliverable).

> **EvolveDraft**: the next-round task brief generated from harvested repository signals; candidates are proposals, the autonomous-execution gate stays with human review.
>
> Purpose.  Carry the evolution round's selected candidates to the reviewer as concrete task briefs: each carries a goal, an approach, an acceptance set and a mechanical grading; the constitution three-law preamble rides on every draft this engine emits.
>
> Interface.  Produced by `python3 tools/evolve.py --draft-out draft-evolve-v55-20261113.md` (with the harvested signal flags recorded below); consumed by the human reviewer, who turns accepted candidates into the next round's task assignments.
>
> Dependencies.  None to read this file; the engine that produced it runs on the Python 3 standard library and subprocesses the sibling engines only.
>
> Evidence.  Every candidate cites the harvested signal that derived it (the round inputs section below carries the full counts); the grading formula is impact x evidence / effort with evidence clamped to 10.
>
> Exit-codes.  Not applicable to a data face; the producing engine exits 0 on completion, 2 on usage error, 9 on missing or unreachable input.

## Preamble — constitution three laws (auto-carried)

1. Law one (annotation / normalization / English-ization): every newly
   written face is English-only, passes the normalization lint with zero
   error-level findings, and carries zero jargon residue against the mapping
   table (`docs/jargon-to-standard-mapping-v1.md`); translation replacement
   archives the replaced Chinese prose in a sibling `.zh.md` file.
2. Law two (contributor isolation): this round does not touch contrib-lane
   semantics; core-lane registry rows cross only through the intake pipeline
   (`docs/contrib-isolation-protocol-v1.0-20261113.md`); fetch before
   claiming, first canonical write wins, file-face layering holds.
3. Law three (autonomous evolution): this brief is produced by the evolution
   engine (`tools/evolve.py`); mutation = live-signal-derived candidates,
   selection = the suite/lint/gate checks, heredity = the frozen-ledger
   lineage.

Safety track: every candidate below is a proposal only. The
autonomous-execution gate stays with human review — the reviewer decides
which candidates become round tasks; nothing in this draft has been
executed, and the engine wrote nothing outside its explicit output paths.

## Round inputs (fitness account)

- Repository root: `/Users/apple/Desktop/rocqwash`
- Draft width (--top): 5; candidates derived: 6; drafted: 5.
- Norm fitness: current error 2453 / warn 1106 vs baseline 2441 / 1036; raw delta +12 / +70; translatable delta +4 / +62; reduction rate error -0.0049 warn -0.0676.
  - Frozen surfaces excluded from the translatable metric: `certify/freeze_manifest.py`, `names/mac_stmt_names.py`, `scan/mac_stmt_scan.py`, `seam/seam_probe.py`, `tools/cpu_guard.sh`, `verify/gate4_comment_guard.py`, `verify/verify_vo.py`, `wash/wash_engine.py`, `更新账.md`.
- Sentinel round: 28 new ci-red event(s) over `hy7pc8gfmf-dotcom/ConstructiveWorld-Set`, `hy7pc8gfmf-dotcom/ConstructiveWorld-Main`; family histogram {"A-content-red": 8, "B-netred": 16, "C-toolchain-break": 1, "D-queue-wall": 2, "E-coqchk-skipped": 1}.
- Suite state (now(rc=0)): 62 pass / 0 red / 1 skip / 63 total.
- Registry audit (`/Users/apple/Desktop/ConstructiveWorld-Set`@`origin/main`): duplicates 12, anchors 549, orphans 3, total 564; increment vs the supplied prior audit.
- Maintained UNRECOGNIZED events: 10.

## Candidate 1 — red-triage (rank 1, score 12.0000)

- **Goal** — Give every new failing-run event of this round an explicit route row (8 new A-family event(s); family histogram in Evidence).
- **Approach** — Re-diagnose each event with the triage engine (real execution lines only), then route per the routing table of `red_dispatch.py`: B/E families to the push re-route suggestion, C family to the toolchain doctor suggestion, D family and UNRECOGNIZED to watch-only, and A family to a manual fix note — a content repair is proposed, never automatically applied.
- **Acceptance** — Every new failing event carries a route row in the round account; A-family fixes stay proposal-only; the affected runs return to passing or carry a documented cause.
- **Grading** — impact 3 x evidence 8 (raw 8, clamped to 10) / effort 2 = score 12.0000; failing runs block the serviced lane and route mechanically.
- **Evidence** — sentinel signal: 28 new ci-red event(s), histogram A-content-red=8, B-netred=16, C-toolchain-break=1, D-queue-wall=2, E-coqchk-skipped=1.

## Candidate 2 — registry-hygiene (rank 2, score 10.0000)

- **Goal** — Reduce the mechanically prescribable registry findings (12 duplicate + 3 orphan findings; anchor histogram in Evidence) on the audited books.
- **Approach** — registry_audit --fix-plan for the deterministic prescriptions, registry_fix dry run by default, human review, then --apply with per-row md5 accounting and automatic rollback on any post-apply assertion failure; rows are regenerated on the current mainline, never hand-edited.
- **Acceptance** — A rerun audit shows zero duplicate residue on treated keys, no new anchor-text collisions, no orphan growth; the books are byte-identical outside the treated rows; the full suite is green twice.
- **Grading** — impact 2 x evidence 10 (raw 15, clamped to 10) / effort 2 = score 10.0000; prescriptions are deterministic but touch a multi-writer surface.
- **Evidence** — registry signal: duplicates 12, anchors 549, orphans 3, total 564 (increment {"anchors": 0, "duplicates": 0, "live": 0, "orphans": 0, "total": 0}); by kind: anchor-collision=8, anchor-malformed=525, anchor-seq-form=16, dup-coqproject=12, orphan-order-only=3.

## Candidate 3 — taxonomy-supplement (rank 3, score 10.0000)

- **Goal** — Reduce the maintained UNRECOGNIZED event set (10 maintained event(s)) by extending the classification taxonomy with reviewed rules or a written ground-truth note per event.
- **Approach** — For each maintained event: re-diagnose with the triage engine --repo --run --logs (real execution lines only), extract the discriminating token, either add the rule with an UNRECOGNIZED-maintenance acceptance vector (machine verdict = review verdict) or keep the event UNRECOGNIZED with a written ground-truth note; never force-fit a shape outside the taxonomy.
- **Acceptance** — Every maintained event either re-classifies into a documented family or stays UNRECOGNIZED with a written note; the triage engine --selftest rc=0 with the new vectors; the full suite is green twice.
- **Grading** — impact 2 x evidence 10 (raw 10, clamped to 10) / effort 2 = score 10.0000; each maintained event needs review, not code mass.
- **Evidence** — UNRECOGNIZED maintained events: hy7pc8gfmf-dotcom/ConstructiveWorld-Main run 3 (seq 17); hy7pc8gfmf-dotcom/ConstructiveWorld-Main run 7 (seq 21); hy7pc8gfmf-dotcom/ConstructiveWorld-Main run 8 (seq 22); hy7pc8gfmf-dotcom/ConstructiveWorld-Main run 10 (seq 23); hy7pc8gfmf-dotcom/ConstructiveWorld-Main run 20 (seq 28); hy7pc8gfmf-dotcom/ConstructiveWorld-Main run 26 (seq 31); hy7pc8gfmf-dotcom/ConstructiveWorld-Main run 54 (seq 69); hy7pc8gfmf-dotcom/ConstructiveWorld-Set run 284.

## Candidate 4 — norm-regression (rank 4, score 2.0000)

- **Goal** — Bring the translatable error-level finding count back to or below the baseline before any new surface work (4 error findings regressed across 1 file(s) since the baseline).
- **Approach** — Diff the current findings against the baseline per file (the regressing files are listed in Evidence), apply translation replacement or header completion per the mapping table on exactly those faces, and archive each replaced Chinese prose in its .zh.md sibling.
- **Acceptance** — The translatable error count is back to or below the baseline; norm_lint --selftest rc=0; the full suite is green (0 red) twice; doc_lint consistent.
- **Grading** — impact 4 x evidence 1 (raw 1, clamped to 10) / effort 2 = score 2.0000; a fitness regression blocks new surface work and touches few files.
- **Evidence** — norm signal: translatable delta +4; regressing files: `docs/draft-evolve-v55-20261113.md` +4.

## Candidate 5 — standing-candidate (rank 5, score 0.5000)

- **Goal** — Execute the recorded final step of the multi-repo adaptation path (a real push against the protected main repository) once its recorded preconditions hold.
- **Approach** — Confirm the working-clone placement decision and the branch-protection posture recorded in the ledger, run the push planner in dry-run first, then the real push only after the human gate accepts the plan.
- **Acceptance** — The dry-run plan matches the recorded expectations; the real push (if approved) lands with its run evidence captured; no direct push to a protected branch.
- **Grading** — impact 1 x evidence 1 (raw 1, clamped to 10) / effort 2 = score 0.5000; persisted memory with no live signal this round; baseline agenda weight.
- **Evidence** — heredity: ledger v54 entry, boundary list; origin ledger v49 entry, boundary list.

## Not drafted this round (beyond the top-5 cut)

- rank 6 — Restore the four-repo reconciliation suite case when the archive returns (score 0.5000).

## Boundary

This draft is a deliverable of the harvest→derive→draft pipeline only. The engine does not execute candidates, does not modify the repository, and does not touch the frozen surfaces; turning a candidate into a round task is the reviewer's decision.
