# xtr-param-probe design (ticket X4, xtr-line)

Purpose.  Specify and record the construction of
`tools/xtr_param_probe.py` (schema `rocqwash.xtr-param-probe/1`), the
probe for extraction-degrading constructs in .v sources.

Interface.  The tool CLI, selftest marker and gates are specified in
the tool header; this volume records the three risk categories, the
block-scoping rule, the acceptance evidence and the consumers.

Exit-codes.  Tool: 0 success (including zero candidates); 1 fail-loud
(unreadable input, selftest failure); 2 usage error.

Evidence.  Eight selftest vectors (Program vernacular, obligation
vernacular, constructor type quantifier with honest double-hit
accounting, universe pins, clean negative, comment masking,
multi-category counts, determinism), double-run live fixture
byte-identical, norm_lint error=0 warn=0, ai_flavor CLEAN.

Dependencies.  Python 3 standard library only; no imports from other
lines; no compiler toolchain; no network.

## The three risk categories

1. `program-obligation`.  `Program Definition/Fixpoint/Lemma/Theorem/
   Coroutine` and the obligation vernacular (`Next Obligation`,
   `Obligation Tactic`, `Obligation N`, `Solve [All] Obligations`,
   `Dependent Obligations`).  Obligations extract as auxiliary
   constants with opacity the development did not write by hand.
2. `constructor-type-quantifier`.  Constructor parameters carrying
   existentially packaged types: `sigT` / `sigT2` tokens, `exists`
   applications, or brace-sigma shapes `{x : A & P x}` on lines inside
   an open Inductive/CoInductive block.  The extracted representation
   of such constructors is lossy and typically magic-ridden.
3. `universe-pin`.  Declarations pinned to `Set` or `Type`
   (`Definition/Fixpoint/Theorem/Lemma/Inductive/CoInductive ... :
   Type|Set`) and the universe vernacular (`Universe`, `Polymorphic`,
   `Monomorphic`, `Set/Local Set Universe Polymorphism`).  The
   universe choice decides whether a computation survives extraction.

## Block scoping

An Inductive/CoInductive block opens at its head line and closes at
the first line whose stripped content ends in a period (a constructor
or the type itself); sigma-token detection runs only inside the open
block, so an unrelated `Definition` that merely mentions `sigT` is not
flagged (selftest v3 records the negative).  The type pin on the
Inductive head itself is separately flagged as `universe-pin` - a
fixture can therefore carry two honest hits for one construct, and
the selftest asserts exactly that accounting.

## Honesty

Hits are textual candidates for human review, not parse-tree facts and
not defect claims.  The report is advisory; the tool is report-only
and performs no writes beyond the caller-named `--out` file.

## Consumers

X5 `xtr_crosscheck` runs this probe as the third leg of the full-chain
report over one fixture world; the line report carries the category
counts.  Registration stays deferred to the main-line close-out (same
class as X1-X3), asserted by the meta shell's unregistration vector.
