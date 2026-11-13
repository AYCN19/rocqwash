# vacgen environment constants note (deployment wiring, annotation only)

**Status**: annotation file. It documents three deployment-time environment
constants, their expected form, and their reading contract. It changes no
executable code: `tools/vacgen.py` is untouched by this note, and no line of
this file is read by any program in this repository. The note exists so that
integrators wire the constants against one stated contract instead of
reverse-reading the generator source.

## The three constants

| Constant | Feeds (CLI flag) | Expected form | Built-in default (this revision) |
|---|---|---|---|
| `ROCWASH_LEAN_WORKTREE` | `--worktree` | directory path: the Lean worktree that holds the mathlib cache used for probe compilation | `tools/vacgen.py:68` (a session-specific machine path) |
| `LAKE` | `--lake` | executable path: the `lake` binary that compiles the probe skeletons | `tools/vacgen.py:67` (`.elan` install path) |
| `MATHLIB_PIN` | `--toolchain` | toolchain version string: the `lean-toolchain` value the mathlib snapshot is pinned to (for example `v4.35.0-rc3`) | `tools/vacgen.py:70` |

The three values are header-recorded only (`--worktree`, `--lake` and
`--toolchain` are recorded verbatim into the `Build` / `Toolchain pin` header
fields of every cast skeleton; see `emit_refutation` / `emit_witness` in
`tools/vacgen.py`). They select and describe the compile environment; the
generator itself still compiles nothing (zero-compile design).

## Reading contract

Precedence, mirroring the taxonomy location chain
(`tools/vacgen.py:784-795`, the same shape as `--taxonomy` >
`VACGEN_TAXONOMY` > tool-adjacent file > builtin):

```
CLI flag  >  environment constant  >  built-in default
```

- A value passed on the command line always wins.
- When the flag is absent, the consumer wrapper reads the environment
  constant and passes it as the flag (thin-wrapper mapping; the engine keeps
  zero changes, so machine default paths are never load-bearing).
- When both are absent, the built-in default applies and is recorded in the
  skeleton header as-is, so every cast carries its full provenance on its
  face.

Expected-form details:

- Paths are host-native; forward slashes are accepted on all hosts. The
  worktree path must be the root that `lake` recognizes (it holds
  `lean-toolchain` and the mathlib cache); the lake path must point at a
  `lake` executable, not a wrapper script that changes the toolchain.
- `MATHLIB_PIN` must equal the worktree's `lean-toolchain` value and the
  running toolchain (`lake env lean --version`), per the toolchain-equality
  pre-flight gate in `docs/vacgen_sop.md` (section 0.2, gate G1). A mismatch
  is an upgrade-and-stop condition, never a silent re-pin.
- Probe compilation, where a consumer performs it, goes through a thermal
  guard wrapper and never runs `lake` bare (`docs/vacgen_sop.md` section 1.5,
  step S5-4).

## Current-state honesty (as of this revision)

Inside the engine, `tools/vacgen.py` reads exactly one environment variable
at this revision: `VACGEN_TAXONOMY` (`tools/vacgen.py:789`). None of the
three constants above is read by engine code yet; setting them alone changes
nothing until a reader implements the contract above (a consumer wrapper
translating constants to flags, or a future engine-side admission using the
same precedence chain). `tests/t_vacgen_expectedred.py` observes and reports
`ROCWASH_LEAN_WORKTREE` without acting on it, which keeps that honesty
machine-visible.

## Name variants of record

Earlier design drafts spelled the constants `ROCWASH_LEAN_WORKTREE` /
`ROCWASH_LAKE` / `ROCWASH_MATHLIB_PIN`, `ROCWASH_LEAN_WORKTREE` /
`ROCWASH_LEAN_LAKE` / `ROCWASH_MATHLIB_PIN`, and sketched a `VACGEN_LEAN_WORKTREE`
/ `VACGEN_LAKE` / `VACGEN_GUARD` overlay. This note fixes the canonical names
as `ROCWASH_LEAN_WORKTREE`, `LAKE`, `MATHLIB_PIN`. The variant spellings are
registration history only: nothing in this revision reads them, and a wrapper
must not accept them silently (an unknown constant should be reported, not
ignored, so a misnamed variable surfaces at the integration face instead of
degrading into the built-in defaults).

## Out of scope

`--guard`, `--core` and `--snapshot` keep their built-in defaults
(`tools/vacgen.py:66-72`); no environment constants are defined for them by
this note. If a deployment needs to vary them, extend this note first and
keep the same precedence contract.
