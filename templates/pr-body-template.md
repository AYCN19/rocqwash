# pr-body-template.md — pull-request description template for rocqwash contributions.

Purpose.  Fixed skeleton for rocqwash pull-request descriptions: the identity
  header, summary, deliverables, baseline declaration, verification list, known
  deltas, the AI-assistance disclosure, and the ICLA statement. Fill the
  bracketed slots per change; the disclosure wording is quoted verbatim from
  `docs/license-protocol-v1.0-20261114.md` section 7 and is not paraphrased.
Interface.  Documentation/template face; it defines no interface of its own and
  prescribes the verification commands each pull request reports
  (`tests/run_tests.sh`, `tools/doc_lint.py`, `tools/axiom_guard.py`).
Dependencies.  References the license-protocol document cited under Purpose (the
  section 7 disclosure), `CONTRIBUTING.md` (section 0.5), `CLA/ICLA.md`,
  `NOTICE`, and `tests/run_tests.sh` for the suite command.
Evidence.  The disclosure block below reproduces the standard form of
  license-protocol section 7 verbatim; the verification
  commands cite the tools' documented invocation lines.
Exit-codes.  None of its own; the commands it prescribes carry their own exit
  codes, described exactly as implemented by those tools.

Technical director: 王宝军 (pen name: 王小哥) (recursive-evolution line · Steward)

Executive director: <contributor name — the machine owner of the submitting agent; bare real name per the role table>

## Summary

<one paragraph: what this work stream lands, which tickets/orders it fulfills, the branch and commit grouping.>

## Deliverables

| # | Item | Path |
|---|------|------|
| 1 | ... | `path` |

## Baseline declaration

Branch cut from main at `<anchor sha>` (pre-PR alignment law: re-based onto the newest
origin/main immediately before assembly — fetch 4× retry, cherry-pick increments,
conflicts fail loud). Zero direct pushes to main; the only integration is this PR.

## Verification

1. Full suite: `ROCWASH_PY=py bash tests/run_tests.sh` → `<anchor ledger line>`; reds ⊆
   anchor red roster, zero new reds, zero lost greens (newly rostered cases listed
   honestly if any).
2. doc-lint: `py -B tools/doc_lint.py --repo <tree>` → verdict `<…>`; zero new findings.
3. Fitness gate: `py -B tools/axiom_guard.py --repo <tree> --rocq <rocq> --coqchk <coqchk>`
   → rc 0, all Closed.

## Known deltas / 已知差集（如实·候上游裁）

1. <delta with evidence — registered, not silently waived>

## AI-assistance disclosure (standard form, quoted verbatim from license-protocol §7) · AI 辅助披露（标准形·逐字引用 license-protocol §7）

> AI-assistance disclosure (standard form): this change was produced
> through the project's own self-evolution pipeline — AI agents executed
> construction, verification, and assembly under the direction of the
> human engineer [name] ([steward / contributor]), who reviewed and
> accepted the results and takes full responsibility for the content.
> Substantive design decisions follow the workorder specification and
> the repository's canonical forms; boundaries and open items are
> registered in [section]. This statement is made under the NOTICE
> Authorship Statement and ICLA §5.2 (AI as instrument — human
> authorship).

Fill the bracketed slots (the directing human + steward acceptance note, and
the registering section). The Chinese mirror of the standard form lives in
license-protocol section 7, the single wording source.

AI-assistance disclosure (standard form): <the English form verbatim, same three slots>.

## ICLA

<per CONTRIBUTING.md §0.5 / CLA-README: signed statement reference, or pending
registration — never proxy-signed; provenance disclosed if agent-executed under a
standing delegation.>
