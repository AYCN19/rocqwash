# xtr-erasure-link design (ticket X3, xtr-line)

Purpose.  Specify and record the construction of
`verify/xtr_erasure_link.py` (schema `rocqwash.xtr-erasure-link/1`),
the three-source erasure link over the .v declaration face, extraction
products, and captured Print Assumptions reports.

Interface.  The tool CLI, selftest marker and gates are specified in
the tool header; this volume records the link model, the verdict
logic, the acceptance evidence and the consumers.

Exit-codes.  Tool: 0 success; 1 fail-loud (unreadable input, selftest
failure); 2 usage error.

Evidence.  Eight selftest vectors (clean, leak, inconclusive,
computational-declaration scoping, token-boundary precision,
assumption overlay with escalation and missing-report honesty,
closed-marker parse, report determinism), double-run live fixture
byte-identical, norm_lint error=0 warn=0, ai_flavor CLEAN.

Dependencies.  Python 3 standard library only; no imports from other
lines; no compiler toolchain; no network.

## The link model

Rocq erases Prop-carrying proofs at extraction; a proof constant that
appears as a computational item in an extraction product is an erasure
leak.  The tool links three sources per constant:

1. Declaration face.  Statement heads of the .v sources:
   Theorem / Lemma / Corollary / Remark / Fact / Proposition heads name
   Prop-carried candidates; Definition / Fixpoint / CoFixpoint / Let /
   Example / Instance heads name computational declarations.  Comments
   are masked nested-aware before head scanning.
2. Extraction products (.ml/.mli/.hs).  A Prop-carried constant is
   linked to the products of its case-folded file stem; presence uses
   a token-boundary match, so an identifier that merely contains the
   name (`good_theorem_suffix`) is not a hit (selftest v5).
3. Assumption reports (optional `--assumptions` directory, one
   captured Print Assumptions output per constant file).  A report
   with the closed marker records `closed`; a report with axiom lines
   records `non-closed`; anything else records `unparsed` - never
   guessed.  A constant without a report records `missing`.

## Verdict logic

- `LEAK`: Prop-carried and present in a linked product.  If the
  assumption overlay also shows `non-closed`, the entry is escalated
  (field `escalated: true`) - a leak riding on axioms.
- `CLEAN`: Prop-carried and absent from every linked product.
- `INCONCLUSIVE`: no product shares the declaration stem, so the
  erasure question cannot be asked honestly.

Computational declarations are recorded (`computational_declarations`)
but are out of leak scope by design: they are supposed to extract.

## Position in the line

This is the README-acknowledged triple-source conjunction face
(realized as a new `verify/xtr_*.py` file so the existing
`erasure_classifier.py` and other verify/ gates stay untouched).
X5 `xtr_crosscheck` chains this verdict into the full-line report over
one fixture.

## Registration status

Same deferred-registration class as X1/X2: unregistered in the shared
suite and un-routed in `cw.sh` until the main-line close-out;
`tests/t_xtr_meta.py` reruns this tool's selftest once landed.
