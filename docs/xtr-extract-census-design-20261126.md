# xtr-extract-census design (ticket X1, xtr-line)

Purpose.  Specify and record the construction of
`tools/xtr_extract_census.py` (schema `rocqwash.xtr-census/1`), the
read-only census of Rocq extraction vernacular that feeds xtr_magic_audit
(X2), xtr_erasure_link (X3) and xtr_crosscheck (X5).

Interface.  The tool CLI, selftest markers and the line-local meta shell
are specified in the tool headers; this volume records the recognized
vernacular forms, the design decisions, the acceptance evidence and the
registration status.

Exit-codes.  Tool: 0 success; 1 fail-loud (unreadable input, selftest
failure); 2 usage error.  Meta shell: 0 all vectors green; 1 any red.

Evidence.  Ten in-process selftest vectors, five meta-shell vector
groups, and double-run byte-identical live fixture determinism, all
green at integration.

Dependencies.  Python 3 standard library only; no imports from other
lines; no compiler toolchain; no network.

## Purpose in the line

The extraction face of a Rocq development is the boundary where proven
statements leave the kernel and become program text (`Recursive
Extraction`, `Separate Extraction`, `Extract Constant`, `Extract
Inductive`, `Extraction Inline`, `Extraction Language`, `Extraction
Blacklist`, `Extract Table`).  Ticket X1 inventories every extraction
point as a deterministic JSON document so the downstream tickets of this
line have a machine-readable base:

- X2 `xtr_magic_audit` consumes the census and audits extraction
  products for `Obj.magic` / `unsafeCoerce` density against declared
  expectations.
- X3 `xtr_erasure_link` links the census declaration face with
  extraction products and assumption reports.
- X5 `xtr_crosscheck` chains X1-X4 over one fixture into a full-line
  report.

The existing wash-line gate `verify/extract_magic_check.py` (gate7
extraction-face Obj.magic per-file gate) is a different instrument: it
drives a real extraction and counts magic in compiled products.  This
tool is a zero-toolchain text census of the vernacular face and does not
duplicate, import, or modify that gate.

## Recognized vernacular forms

| command | capture |
| --- | --- |
| `Extract Constant qualid => "payload".` | target, payload |
| `Extract Inlined Constant qualid => "payload".` | target, payload |
| `Extract Inductive qualid => "payload" [variants].` | target, payload |
| `Extract Inlined Inductive qualid => "payload" [variants].` | target, payload |
| `Extract Table qualid => "payload".` | target, payload |
| `Recursive Extraction qualids.` | target list |
| `Recursive Extraction Library ident.` | module |
| `Separate Extraction qualids.` | target list |
| `Extraction qualids.` | target list |
| `Extraction Library ident.` | module |
| `Extraction Inline qualids.` / `Extraction NoInline qualids.` | target list |
| `Extraction Language Ocaml\|Haskell\|JSON.` | language state |
| `Extraction Blacklist idents.` | blacklist names |

Anything else on the extraction face (a line starting with `Extraction`,
`Extract`, `Recursive Extraction`, `Separate Extraction` that matches no
form above) is recorded in `unparsed_extraction_face` with its text and
line - never silently dropped.

## Design decisions

1. Comment masking.  Rocq comments are masked by a nested-aware scanner
   that preserves newlines, so line numbers stay true and a statement
   hidden in a comment is never counted (selftest vector v3 is the
   negative control for exactly this).
2. Logical statement joining.  An extraction statement may span several
   lines (`Extract Inductive` variant tables).  The scanner joins from
   the statement-opening line until a line ending in a period, capped at
   40 lines; an unterminated statement falls into the unparsed bucket.
3. Plain `Extraction a b.` ambiguity.  Text-level scanning cannot
   distinguish a plain target list from an unknown subcommand name; the
   plain form parses as a target list by design and this design accepts
   that (vector v7b documents the stance).
4. Language state.  `Extraction Language` is file-scoped state: every
   point after it carries that language.  The default is `ocaml`, the
   documented default target of the extraction vernacular.
5. Safe-primitive classification.  `is_safe_primitive` is a conservative
   curated allowlist on the payload text (pure arithmetic, comparison,
   conversion, identity, logical forms).  Anything containing
   `Obj.magic`, `unsafeCoerce`, `assert false`, `failwith`, printing or
   ref tokens is flagged `unsafe-shape`; everything else outside the
   allowlist is `unclassified` and reported not-safe.  This is a textual
   judgment, not a semantic claim - the report is advisory.
6. Payload hint.  `payload_hint` records the observed shape
   (`ocaml-shape` / `haskell-shape` / `none`) independently of the
   declared language state, so a declared-Haskell file with OCaml-shaped
   payloads is visible.

## Determinism and safety

No wall clock, no random, sorted keys (`json.dumps(..., sort_keys=True)`),
points sorted by (file, line, command); equal inputs produce
byte-identical output.  Zero network, stdlib only, read-only over input
trees; the only write is the caller-named `--out` file.

## Acceptance

- `--selftest`: 10 in-process vectors (v1 payload capture and safe
  class, v2 target lists, v3 comment negative control, v4 language
  state, v5 nested comments, v6 unsafe payload flag, v7 unparsed bucket
  and plain-parse stance, v8 empty and multi-line forms, v9 report
  determinism, v10 inline-vs-plain ordering) - prints
  `XTR-EXTRACT-CENSUS-SELFTEST PASS`, exit 0.
- `tests/t_xtr_meta.py`: line-local meta shell, 5 vector groups
  (discovery, per-tool selftest, unregistration invariant, fixture face,
  double-run determinism) - prints `T-XTR-META PASS`, exit 0.
- Live scan over `tests/fixtures/xtr_census/` byte-identical across two
  runs.

## Registration status

The xtr family is intentionally NOT registered in `tests/run_tests.sh`
(or any shared registration face): the zero-collision discipline of the
idle-time line forbids touching shared registration files.  `tests/
t_xtr_meta.py` asserts this unregistration invariant as vector v3.
Registration into the shared faces is deferred to the main-line
close-out and recorded here as a pending obligation of that close-out.
