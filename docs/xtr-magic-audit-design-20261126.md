# xtr-magic-audit design (ticket X2, xtr-line)

Purpose.  Specify and record the construction of
`tools/xtr_magic_audit.py` (schema `rocqwash.xtr-magic-audit/1`), the
Obj.magic / unsafeCoerce audit of extraction products against the
declaration claims of the X1 census.

Interface.  The tool CLI, selftest marker and gates are specified in
the tool header; this volume records the claim model, the occurrence
classification, the acceptance evidence and the consumers.

Exit-codes.  Tool: 0 success; 1 fail-loud (unreadable input, wrong
census schema, selftest failure); 2 usage error.

Evidence.  Nine in-process selftest vectors (battery counts,
impossible-case markers, comment masking, red-biased occurrence
classification, the declared-safe-but-actually-magic negative control,
MATCH case, declared-unsafe NO_CLAIM, path-independent case-folded stem
linking, Haskell battery plus report determinism), double-run live
product scan byte-identical, norm_lint error=0 warn=0, ai_flavor CLEAN.

Dependencies.  Python 3 standard library only; consumes the X1 census
document as data (no import from the census tool); no compiler
toolchain; no network.

## The claim model

The census (X1, schema `rocqwash.xtr-census/1`) records every
extraction point of a .v file with its payload classification.  X2
derives a per-file claim:

- `magic-free`: no extraction payload of the .v file carries an unsafe
  token shape (`Obj.magic`, `unsafeCoerce`, `assert false`, `failwith`,
  printing or ref tokens).  The development declares this face escapes
  without magic.
- `declared-unsafe`: at least one payload is `unsafe-shape`.  The
  development itself declared magic; there is no claim to contradict,
  so products of this stem get verdict `NO_CLAIM` with the claim tag
  recorded (visibility without a false red).

A product links to its census file by case-folded stem
(`src/Safe.v` claims for `out/safe.ml`, `deep/dir/SAFE.ml`, `.mli`
sibling files and so on).  A product with no census entry of its stem
is `NO_CLAIM`.

Verdicts per product file: `MATCH` (magic-free claimed, zero battery),
`MISMATCH` (magic-free claimed, battery non-zero), `NO_CLAIM`.

## The battery and occurrence classification

Counted per product file: `Obj.magic` and `unsafeCoerce` (OCaml
products), `unsafeCoerce`, `GHC.Magic`, `unsafeDupablePerformIO`
(Haskell products), `assert false` and `failwith` (both), plus
`__`-prefixed erasure dummies.  Comments are masked nested-aware before
counting (`(* *)` for OCaml, `{- -}` for Haskell); a token inside a
comment is never counted (selftest v3).

Each occurrence is classified by its line context:

- `anomalous`: the line carries an impossible-case marker
  (`assert false`, `failwith`).  On a mixed line the anomalous markers
  win - the classification is biased red, never excused.
- `inherent`: the line matches known extraction idioms (`Obj.magic 0`,
  `Obj.magic ()`, `(fun x -> x)`, `Obj.repr`, or an erasure dummy on
  the line).
- `unclassified`: everything else.

These are textual heuristics with a stated red bias, not semantic
judgments; the report is advisory and report-only.  Density is
occurrences per KB of product text.

## Consumers

- X3 `xtr_erasure_link` consumes verdicts to link the declaration face,
  the extraction products and the assumption reports.
- X5 `xtr_crosscheck` chains the audit into the full-line report over
  one fixture.

## Registration status

Same deferred-registration class as X1: the xtr family stays
unregistered in the shared suite and un-routed in `cw.sh` until the
main-line close-out; `tests/t_xtr_meta.py` (landed with X1) asserts the
unregistration invariant and reruns this tool's selftest.
