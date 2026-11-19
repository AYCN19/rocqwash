# Component map / 组件地图（对接侧可调用面·CLI 一直一行）

> Every row is an in-repo, zero-network (unless marked), stdlib-only component with an
> explicit CLI contract and selftest. Run all with the real interpreter (`python -B` in-repo
> harness form; beware store-stub `python` on Windows — use `py`). Full contracts live in
> each file's docstring; this map is the docking-side index.

## Φ pipeline faces / 演进主链

| Component | Face | One-liner |
|---|---|---|
| `tools/vacgen.py` | assumption census + taxonomy lookup | `py -B tools/vacgen.py --in <file.v> --out <dir> --report <r.json>` |
| `tools/gap_cluster.py` | W1 gap clustering | `py -I tools/gap_cluster.py --reports <cast.json> --out <ledger.json>` |
| `tools/row_render.py` | W2 emit/ingest/check/tenpoint | `py -I tools/row_render.py --gaps <w2.json> --ingest <backfill.jsonl> --draft-out <draft.json>` |
| `tools/auto_round.py` | approve / commit / anchor / rollback | `ROCWASH_PY=py bash tests/run_tests.sh` first; then `py -B tools/auto_round.py approve --class <name> --note <basis>`; `py -B tools/auto_round.py commit --classes <c> --files <f,...> --message <m>` |
| `tools/bus_feeder.py` | symbiosis swap → gap ledger | `py -I tools/bus_feeder.py feed --swap docs/symbiosis-swap-round1.jsonl` (idempotent; re-run shows zero-feed) |
| `tools/scheduler_lite.py` | round trigger — **X work stream in flight, not yet on main; consult after its PR lands** | (face documented in-repo after integration) |

## Verification / verification faces / 验证面

| Component | Face | One-liner |
|---|---|---|
| `tools/axiom_guard.py` | fitness gate (axioms) | `py -B tools/axiom_guard.py --repo . --rocq <rocq.exe> --coqchk <coqchk.exe> --timeout 600` |
| `certify/frozen8.py` | frozen trust anchors | `py -I certify/frozen8.py check --repo . --list certify/frozen8_manifest.json --tier2 certify/frozen8_tier2.md5` |
| `certify/frozen8.py` | re-sign (post-squash SOP) | `py -I certify/frozen8.py freeze --repo . --out certify/frozen8_manifest.json --tier2 certify/frozen8_tier2.md5` |
| `tools/norm_lint.py` | wording gate | `py -B tools/norm_lint.py --tree` (selftest: `--selftest`) |
| `tools/doc_lint.py` | docs-vs-impl gate | `py -B tools/doc_lint.py --repo <root> --json <out.json>` |
| `tests/run_tests.sh` | full suite (roster ledger) | `ROCWASH_PY=py bash tests/run_tests.sh` |

## Landing / watch faces / 落岸与看护

| Component | Face | One-liner |
|---|---|---|
| `tools/auto_merge.py` | merge door judge (six verdicts + rails) — **X work stream in flight, not yet on main** | (face documented in-repo after integration; calibration selftest carries the six-verdict vectors) |
| `tools/uplink.py` | external return-package intake | `py -B tools/uplink.py verify <pkg>` → `intake` |
| `tools/cw_sentinel.py` | watch daemon | `py -B tools/cw_sentinel.py --loop --interval 60` |
| `tools/evolution_dashboard.py` | KPI/self-observation | `py -B tools/evolution_dashboard.py --json <out.json>` |
| `tools/repair_scope.py` | shared repair-exclusion source | imported by repair waves; frozen faces永远 excluded |

## Workflow templates / 工作流模板

- `templates/wf-recursion-wave-template.dwf.ts` — one construction work stream: P0 cloud
  alignment → parallel seats → mechanical gates → branch → fork push → PR → CI judge.
  Fill the parameter block; keep the discipline strings byte-stable.
- `templates/ci-green-watch.sh` — CI-green sentinel for the alignment law (green →
  align → anchor-verify; red → report and wait for self-heal).
- `templates/pr-body-template.md` — PR preamble: dual-role header, disclosure standard
  form (verbatim, three slots), ICLA section.

## Interpreter note / 解释器注记

On Windows machines with a store-stub `python`/`python3` (rc 49 or silent zero-output),
use the real launcher (`py`, Python 3.12+) or `ROCWASH_PY=py` for the suite; inside this
repo's tools the harness form is `python -B` via `run_tests.sh`'s escape hatch
(`PY=${ROCWASH_PY:-python3}`).
