# vacgen: Vacuity Probe Skeleton Generator

`tools/vacgen.py` casts a four-account vacuity probe package for the headline
theorem of a Lean artifact. It recognizes the shape of the statement's premise
face, transcribes it verbatim into a set of probe skeletons, and grades what
can be graded without compiling. The generator is Python standard library
only, zero network, zero compile, and runs under `python -I`. It casts
skeletons and never asserts mathematics: every artifact-facing proof
obligation is a declared `TODO-SEAT` marker in the skeleton, filled by a
later audit pass.

## The four accounts

| Account | File(s) | Expected verdict | Content |
|---|---|---|---|
| 1. witness | `witness.lean` | expected-green-after-fill | premise-nonempty envelope theorem: a concrete witness for the artifact's premise conjunction |
| 2. refutation spectrum | `falsify_full.lean`, `falsify_point.lean`, `falsify_tactics.lean`, `falsify_noclassic.lean`, `falsify_band.lean` | expected-fail | five refutation probes attempting to derive `False` from the transcribed premise interface |
| 3. boundary | `boundary.lean` | expected-green-after-fill | closed-form separation machine checks over the relevant regions |
| 4. gap anchors | `gap_anchors.txt` | census record | name-family census chain, a negative-finding block with its four boundary elements, and the per-file ledger |

Each cast prints the per-file ledger (byte/line/sorry/agent counts), a
word-face coverage lower bound with its date, a fixed set of bound-form
checks, and a final verdict line (`ok=true` / `ok=false`). Verdicts over
coverage are lower bounds at the cast window, never exact-equality
invariants.

## The expected-red contract

The refutation spectrum is compile-must-fail by design, and this inversion is
the core of the tool's verdict semantics:

- A probe red (`rc != 0`) on a `falsify_*` face is the expected verdict: the
  premise interface resisted that refutation form (nonempty evidence).
- A probe green (`rc = 0`) on the same face means the transcribed premise
  interface is jointly unsatisfiable, so the artifact's statement is vacuously
  true. That is the vacuity alert, the highest alert level: freeze, escalate,
  verdict `ok = false`.
- A red on an expected-green face (witness, boundary, or the pre-probe smoke
  file) is a probe-side defect, never evidence about the artifact.

Every refutation face carries the `EXPECTED-FAIL` marker and a header stating
this rc contract, so a runner reading the skeleton knows that compile reds on
that face are the designed outcome and must not be reported as failures. The
test `tests/t_vacgen_expectedred.py` pins the contract at the word-face level
in three checks (registration per face, the inverted rc contract, and the
red/green boundary); its Lean compile leg is a design-SKIP and never
compiles. Grading of probe results beyond the word face follows the five
grades defined in `docs/vacgen_sop.md` (strong red / weak red / refutation
green / boundary green / absence).

## Running it

Cast mode (v1 CLI face preserved):

```
python -I tools/vacgen.py --in <statement-face.lean> --out <output-dir>
```

Coverage preflight over a census-qualified file set:

```
python -I tools/vacgen.py --preflight-all --census <census.json> --root <clone>
        [--report <difficulty-map.json>]
```

The taxonomy table is located by a fail-safe chain: vacgen first tries the `--taxonomy` flag, then
the `VACGEN_TAXONOMY` environment variable, then a `taxonomy.json` next to the
tool, then a builtin starter row. With no taxonomy file the generator keeps
its builtin recognition face; unrecognized premise shapes are counted as
declared seats, never silently dropped.

## Deployment environment constants

Three environment constants are defined for wiring the compile environment at
deployment time; they feed the `--worktree`, `--lake` and `--toolchain`
flags, which are recorded verbatim in the `Build` and `Toolchain pin` header
fields of every cast skeleton:

| Constant | Feeds | Expected form |
|---|---|---|
| `ROCWASH_LEAN_WORKTREE` | `--worktree` | directory path of the Lean worktree holding the mathlib cache |
| `LAKE` | `--lake` | path of the `lake` executable |
| `MATHLIB_PIN` | `--toolchain` | toolchain version string (the `lean-toolchain` value, for example `v4.35.0-rc3`) |

Reading contract: CLI flag, then the environment constant, then the built-in
default (the same precedence shape as the taxonomy chain). At this revision
the generator itself reads none of the three from the environment; a consumer
wrapper or a future engine-side admission implements the contract, and
setting the constants alone changes nothing. Expected forms, the
toolchain-equality gate, and the variant spellings registered in earlier
design drafts are documented in `tools/vacgen_env_note.md`.

## Boundaries

- The generator compiles nothing. Probe compilation is the consumer's face:
  a pinned Lean toolchain and mathlib snapshot, always wrapped in a thermal
  guard, never a bare `lake` run.
- Coverage scores are word-face lower bounds (regex plus bracket-balanced
  surgery); elaboration-time semantics are invisible to the generator, and
  every verdict states that boundary.
- Absence verdicts and splice anchors are relative to the pinned snapshot
  window; when the upstream library advances, they must be re-run.
- A refutation red records that the interface resisted the attempted
  strength; it is not a satisfiability proof. The tool judges no open
  mathematical clause and registers no priority claims.

## Test surface

- `tests/t_vacgen_shape.py`: casts the fixture and asserts the four-account
  skeleton layout (zero-network, zero-compile).
- `tests/t_vacgen_expectedred.py`: pins the expected-red contract in three
  checks and reports the Lean compile leg as a design-SKIP (zero-network,
  zero-compile, tmp-directory writes only).

Both run standalone with `python -I` and report pass, skip, or a loud red
listing; they never count a by-design red as a failure.

## Related documents

- `docs/vacgen_sop.md`: the operating procedure and the five-grade verdict
  law for probe results.
- `tools/vacgen_env_note.md`: the deployment environment constants note.
- `docs/en/architecture.md`: repository architecture overview.
