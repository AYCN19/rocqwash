# dep-line cross-check report

- schema: rocqwash.dep-crosscheck/1
- target: S01_BaseRing
- replacement: Cure.NewBase
- roots: .
- chain state: completed

## Legs

| leg | rc | schema | note |
| --- | --- | --- | --- |
| census | 0 | rocqwash.dep-map/1 | dep-map written: C:\Users\拯救者\AppData\Local\Temp\tmp.c6reP4DWNA\chain\census.json (23 consumers, 12 with deps) |
| plan+apply | 0 | rocqwash.dep-plan/1 | plan + patched tree written under C:\Users\拯救者\AppData\Local\Temp\tmp.c6reP4DWNA\chain\plan (3 repoint, 0 blocked, 3 files written) |
| apply | 0 | rocqwash.dep-apply-report/1 | applied: 3 files, 3 rewrites, N=N pass (C:\Users\拯救者\AppData\Local\Temp\tmp.c6reP4DWNA\chain\apply) |
| verify | 4 | rocqwash.retire-verify/1 | VERDICT: UNSAFE (C:\Users\拯救者\AppData\Local\Temp\tmp.c6reP4DWNA\chain\apply\tests\fixtures\cure39_plain_fixture.v) |

## Honest reading

The verify verdict is a fact about the probed artifact, not a quality label for the line: a fixture whose provider is not compiled in-tree verifies UNSAFE, and that is the correct outcome for an out-of-context artifact. The chain itself reports completion, never quality.

## Registration note

The dep-line tools (dep_census, dep_plan, dep_apply, dep_retire_verify, dep_crosscheck) are not yet registered: no cw.sh case routes, no capability-doc rows, no run_tests.sh CASES entries. Registration is the main-line rotation close-out's action, outside the dep-line file domain; until then the tool-table doc_lint delta of each landing PR is the expected and recorded residue.
