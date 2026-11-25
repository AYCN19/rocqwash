# xtr-line report (extraction trust chain, seed queue X1-X6)

Purpose.  Closing statement of the idle-time extraction trust chain:
six seed tickets that inventory the extraction face, audit its
products against declaration claims, probe its degrading constructs,
link its erasure leaks, and chain the instruments into one verdict.
Every number below is quoted from machine documents in the line
ledger.

Interface.  Five tools under `tools/` and `verify/`, the
`t_xtr_meta.py` shell, two fixture sets, and the design volumes under
`docs/xtr-*.md`.  The crosscheck chains the other four.

Exit-codes.  All tools: 0 success, 1 fail-loud, 2 usage error; the
crosscheck returns 1 when a leg is missing or failed.

Evidence.  Census 13 selftest vectors (post-XD1), magic audit 9,
erasure link 8, param probe 8, crosscheck 5, meta shell 5; every tool
deterministic; norm_lint 0/0 and ai_flavor CLEAN on every new file;
the live e2e chain ends COMPLETE with one seeded MISMATCH and one
seeded LEAK, both recovered as data.

Dependencies.  Python 3 standard library only, line-local; no
compiler toolchain; no network.

## The full-chain verdict (machine output)

`xtr_crosscheck` over the e2e fixture world: `verdict=COMPLETE`,
`audit_mismatch_files=1`, `erasure_leak_constants=1` - the seeded
negative controls (a product carrying Obj.magic against a
magic-free census claim; a proof constant extracted into a product)
are caught by the chain exactly once each, and the declared-unsafe
face is correctly NO_CLAIM rather than a false red.  Leg summaries:
census 2 `Extract Constant` points; audit 3 magic occurrences over 2
products with 1 mismatch; probe 1 program-obligation +
1 constructor-type-quantifier + 1 universe-pin; erasure
1 prop-carried constant, verdicts LEAK 1 / CLEAN 0 /
INCONCLUSIVE 0, assumptions overlay recorded.

## Demand sweep one: the rocqwash face is clean

Census over the whole rocqwash repository: 23 .v files, zero
extraction statements, unparsed bucket empty.  The hosting
repository needs no extraction audit; the demand is external.

## Demand sweep two: the Set library carries 330 extraction statements

Read-only census over the ConstructiveWorld-Set tree (633 .v files),
after the XD1 refinement: 330 extraction points across 148 files
(50 `Recursive Extraction`, 139 `Separate Extraction`, 137
quoted-output `Extraction`, 4 `Extraction Inline`), 137 points with
`output_file` recorded, zero unsafe-shape payloads, unparsed bucket
drained 137 to 0 by the census v2 refinement (derived ticket XD1,
landed in the X6 capacity work stream).  None of these 330 statements
is currently audited by a magic gate; that is the line's measured
follow-on demand.

## The real-products case (X6b headline)

The 232 extraction products (.ml/.mli pairs) of that library audit to
zero `Obj.magic` and 549 `__`-prefixed erasure dummies (DTPT.ml alone
223) - erasure pressure in this domain shows up as dummy-identifier
density, not magic escapes, which is why the audit battery reports
dummies as a first-class counter.

## Registration needs (recorded here only)

The xtr family (5 tools + meta shell + fixtures) is intentionally
unregistered in `tests/run_tests.sh` and un-routed in `cw.sh` - the
zero-collision discipline of an idle-time line forbids touching
shared registration faces; the meta shell asserts the unregistration
invariant continuously.  Main-line close-out can pick the family up
by: adding the tools to the cw.sh routes, registering one suite lane
for `tests/t_xtr_meta.py`, and re-running the doc_lint tool-table
check (the two deferred-registration drift entries then resolve).
Until then the family runs green standalone; this volume is the only
place registration is requested.
