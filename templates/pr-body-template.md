技术总监：王宝军（笔名：王小哥）（递归演进线·Steward）

执行总监：<contributor name — the machine owner of the submitting seat; bare real name per the role table>

## Summary

<one paragraph: what this wave lands, which tickets/orders it fulfills, the branch and commit grouping.>

## Deliverables

| # | Item | Path |
|---|------|------|
| 1 | ... | `path` |

## Baseline declaration

Branch cut from main at `<anchor sha>` (pre-PR alignment law: re-based onto the newest
origin/main immediately before assembly — fetch 4× retry, cherry-pick increments,
conflicts fail loud). Zero direct pushes to main; the only landing is this PR.

## Verification

1. Full suite: `ROCWASH_PY=py bash tests/run_tests.sh` → `<anchor ledger line>`; reds ⊆
   anchor red roster, zero new reds, zero lost greens (newly rostered cases listed
   honestly if any).
2. doc-lint: `py -B tools/doc_lint.py --repo <tree>` → verdict `<…>`; zero new findings.
3. Fitness gate: `py -B tools/axiom_guard.py --repo <tree> --rocq <rocq> --coqchk <coqchk>`
   → rc 0, all Closed.

## Known deltas / 已知差集（如实·候上游裁）

1. <delta with evidence — registered, not silently waived>

## AI 辅助披露（标准形·逐字引用 license-protocol §7）

> AI 辅助披露（标准形）：本变更经本项目自带的递归式演进管线产出——AI 智能体在人类工程师（<fill:
> the directing human + steward acceptance note>）的方向指导下执行构筑、复核与组装；该工程师复核验收结果
> 并对内容负全责。实质设计决策沿工单规格与仓既有正典形落位；边界与未决项登记于 Known deltas 节。
> 本声明依 NOTICE Authorship Statement 与 ICLA §5.2（AI as instrument — human authorship）作出。

AI-assistance disclosure (standard form): <the English form verbatim, same three slots>.

## ICLA

<per CONTRIBUTING.md §0.5 / CLA-README: signed statement reference, or pending
registration — never proxy-signed; provenance disclosed if seat-executed under a
standing delegation.>
