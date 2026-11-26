# xtr-crosscheck design (ticket X5, xtr-line)

Purpose.  Specify and record the construction of
`tools/xtr_crosscheck.py` (schema `rocqwash.xtr-crosscheck/1`), the
four-leg chain that turns the standalone X1-X4 instruments into one
full-line verdict over a shared fixture world, and the line report
that quotes its machine output.

Interface.  The tool CLI, selftest marker and gates are specified in
the tool header; this volume records the leg topology, the verdict
rules, the fixture world, and the acceptance evidence.

Exit-codes.  Tool: 0 all legs ok (verdict COMPLETE; mismatches and
leaks are data, not failures); 1 any leg missing or failed (verdict
INCOMPLETE, fail-loud); 2 usage error.

Evidence.  Five selftest vectors (all-legs-ok chain, seeded audit
mismatch, seeded erasure leak, missing-tool honesty over a partial
root, double-run determinism) plus the live e2e fixture world under
`tests/fixtures/xtr_e2e/` with double-run byte-identical chain output,
norm_lint error=0 warn=0, ai_flavor CLEAN.

Dependencies.  Python 3 standard library only; invokes the four xtr
tools of this line as subprocesses; no compiler toolchain; no network.

## Leg topology

| leg | tool | input | verdict quoted |
| --- | --- | --- | --- |
| A census | xtr_extract_census | decl fixture dir | counts_by_command |
| B audit | xtr_magic_audit | products + leg A census | mismatch_files |
| C probe | xtr_param_probe | decl fixture dir | counts_by_category |
| D erasure | xtr_erasure_link | decl + products (+ assumptions) | LEAK count |

Leg B consumes leg A's census file, so the claim model of X2 exercises
end-to-end inside the chain.  A leg that cannot run reports status
`missing` (tool absent) or `failed` (nonzero exit, note carries the
first 200 bytes of stderr) - never a silent skip; the combined verdict
is COMPLETE only when all four legs are ok.

## The fixture world (tests/fixtures/xtr_e2e)

Two declaration files and their products, seeded so every instrument
has honest work:

- `goods.v` claims magic-free (safe payload) and declares `Theorem
  clean_proof`; its product `goods.ml` deliberately carries
  `Obj.magic` - the audit leg must record exactly one MISMATCH, and
  the erasure leg must record exactly one LEAK (`clean_proof` present
  in a product).
- `bad.v` declares the unsafe payload (`Obj.magic 0`), a `Program
  Definition`, and a `sigT` constructor inside a Type-pinned
  inductive; its product links as declared-unsafe (NO_CLAIM, not a
  false red) and the probe leg records the program-obligation,
  constructor-type-quantifier and universe-pin hits.
- `assumptions/clean_proof.pa` carries the closed marker so the
  erasure overlay records `closed` for the leaking constant.

## The line report

the line report volume `docs/xtr-report-<date>.md` (landed in the same PR) quotes the
chain output over this fixture world plus the two capacity sweeps
(rocqwash face zero-point; Set library 330 extraction points after the
XD1 refinement) as the line's machine-verified closing statement.
Registration needs are recorded there only - the xtr family stays
unregistered in the shared faces until the main-line close-out.
