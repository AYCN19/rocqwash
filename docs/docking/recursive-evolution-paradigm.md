# Recursive-evolution paradigm / 递归式演进范式（推导版·公理链）

> **Status / 状态**: canonical paradigm document (derived form · axioms → theorems →
> components). Quote this file; do not restate it ad hoc. Canonical per the
> single-source discipline (see `docs/license-protocol-v1.0-20261114.md` §7 for the
> disclosure analogue).

## Axioms (constitutional · not amendable by any seat) / 公理（宪法层）

| # | Axiom | Meaning |
|---|---|---|
| S1 | Self-accounting / 自施律 | every state change is ledgered; "done but unrecorded" does not exist |
| S2 | Layer law / 层律 | data-layer proposals auto-admit after one human first-admission per class (乙档); code-layer changes go through the gated round face (human point-order); certification faces are never auto-touched; the constitutional layer is human-only |
| S3 | Gap law / 缺口律 | the throttle is the measured gap count; no measured gaps → no round opens (no padding, no invented work) |
| S4 | Judge-executor separation / 判执分立 | the measurer never approves its own fix |
| S5 | Inheritance law / 遗传律 | every landed face carries its provenance and constraints forward |

## Structure / 结构

Φ (one pass) = cluster gaps → render candidate rows → [human point-order] → admit →
verify (fitness gate) → land as a ledgered round. **Φ\* (recursion) = Φ re-entering
itself**, driven by: a trigger that opens rounds on measured gaps; fuel (internal census +
bus feeding + external sweep); and a learning edge (calibration → render scheduling) so
round N+1 makes better predictions than round N.

## Theorems (the derivation that chose the components) / 定理

- **A (re-enterability)**: Φ having run once is a one-shot event; recursion requires a
  trigger that re-opens rounds without a human re-ignition. The trigger (scheduler lite)
  is the highest-leverage, lowest-cost missing piece once Φ is closed.
- **B (throttle before pump)**: render/admit capacity exists; the bottleneck is the gap
  ledger's refill rate (three sources: internal census, bus feeding, external sweep).
- **C (learning edge)**: without wiring calibration results back into render scheduling,
  Φ\* repeats rather than improves.
- **D (induction sample size)**: generalizing a repair face (B-construction) requires
  ≥3 instances each with ≥1 live round; sample rounds unlock it.
- **E (domain boundary)**: recursion currently spans the Lean/Python world; the Coq-side
  survey defines the D-stage expansion quote.

## Laws this repo enforces on every wave / 全波强制法

1. **Alignment law**: align with origin/main before construction, again immediately
   before PR assembly, and after CI goes green on your landing (squash landings move main
   constantly; stale anchors produce noise). See `alignment-and-pr-protocol.md`.
2. **Fitness law**: every repair/landing passes the real fitness gate —
   `tools/axiom_guard.py` (compile leg + kernel re-check, zero axioms, `Admitted`/`Axiom`/
   `Hypothesis` forbidden, no Prop leakage) plus the suite with zero new reds against the
   anchor roster. A linter self-test is not a fitness gate.
3. **Whoever writes, enters the matrix (S1 hard form)**: every new write face lands with
   a file:line-anchored assertion row in `tests/test_destructive_matrix.py`.
4. **Honest visibility (RC-F lesson)**: guard-correct non-participation is ledgered
   (`watch-only(guard-correct: …)`), so "correctly stood by" is distinguishable from
   "failed to repair".
5. **Single-source wording**: disclosure and signature language quote
   `docs/license-protocol-v1.0-20261114.md` §7 verbatim (three sanctioned slots only).

## Known structural gaps (registered · under ruling) / 已登记结构间隙

- **Squash × freeze-commit**: every squash landing moves HEAD past `freeze_commit` and
  re-triggers the git-anchor check until a re-sign lands (re-sign = canonical
  `frozen8.py freeze` face; criterion upgrade under ruling).
- **No pull_request CI trigger**: `ci.yml` runs on main pushes only, so fork PRs have no
  pre-merge CI face; the automerge door's head-CI criterion needs either a
  pull_request trigger (additive) or a post-merge-only semantics.
- **Trigger ignition**: the scheduler lite is cast and dry-run only; real ignition waits
  for the EF wave all-green signal and the first-week human review of every round.
