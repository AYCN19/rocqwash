# pin-provenance-v2 - the provenance pin schema, v2 form (evidence body, not paths).

Ticket: pin-source provenance v2 closing package (November 19, 2026), schema/doc face.
Statement faces: seeds/jargon/jargon-map.json (provenance.sources); seeds/jargon/_snapshots/;
  tools/jargon_map_sync.py, tools/pin_repair.py, tests/t_engines_seeds.py,
  seeds/jargon/test_snippet.py, the CI whitepaper (R15, R17), docs/ci-triage-table.json (R15, R17)
Source route: repo docs/ (this face); the frozen schema and design ruling live in the provenance-v2 closing contract (desk side)
Command: python -I tests/t_engines_seeds.py (the consumer verification gate, jargon segment 9/0)
Registry: docs/CAPABILITY-INDEX.md (the pin_repair entry, updated to the v2 form same round)

> Purpose.  One frozen interface for how the jargon seed proves its pinned
>   sources: a pin records the evidence body of a source, not a path. Repo
>   sources pin the committed git blob sha; external sources pin the md5 of
>   an in-repo byte snapshot taken at sign time; hosted faces verify the
>   consistency layer, freshness stays canonical-only (R15, R17).
> Interface.  Schema definition only; consumers: tools/jargon_map_sync.py (write side), tools/pin_repair.py (repair side), tests/t_engines_seeds.py and seeds/jargon/test_snippet.py (check side).
> Dependencies.  Python 3 standard library and git only; no network face.
> Evidence.  Canonical full green; hosted green with the declared skip (evidence slot in the whitepaper case files).
> Exit-codes.  Not applicable to a document face.

## Problem

The v1 pin form recorded an md5 plus an absolute path per source: two of the
three pins sat outside the repository, so hosted runners hit OSError and
reported SKIP, and the absolute path crossed two trees, producing the
cross-tree race R17. One design change retires both failure modes.

## Schema (frozen; v1 fields are not kept)

Per source, inside `provenance.sources` of seeds/jargon/jargon-map.json:

    {"locator": "repo", "path": "<repo-relative path>",
     "pin": {"kind": "git-blob-sha", "value": "<40 hex>"}}
    {"locator": "external", "path": "<repo-relative snapshot path>",
     "upstream_path": "<absolute path of the external original>",
     "pin": {"kind": "md5", "value": "<32 hex>"}}

- locator "repo": path is repository-relative; pin.value is the blob sha of the
  file's committed content (`git rev-parse HEAD:<path>`); absolute paths forbidden.
- locator "external": path is the in-repo snapshot; upstream_path is informational
  only, never a consistency input; pin.value is the snapshot md5 (the original's md5 at sign time).
- A snapshot is a byte-level copy of the external original at sign time (no rewriting,
  original CJK and line endings preserved) under seeds/jargon/_snapshots/; the seed and its consumers flip in one commit (R14's discipline).

## Layers

Per-source judgment is fail-loud and names its layer in the result line.
1. Repo source: `git rev-parse HEAD:<path>` versus pin.value (one answer on
   every machine); mismatch or missing file = FAIL; hosted faces truly verify.
2. External source, consistency layer: the in-repo snapshot's md5 must equal
   pin.value, otherwise FAIL.
3. External source, freshness layer: if upstream_path exists (the canonical
   machine) its md5 must equal pin.value, otherwise FAIL (true drift); if not,
   a declared skip carrying the exact text
   `SKIP (declared, freshness unverifiable off-canonical: upstream absent)`.

## EOL-agnostic fingerprinting

The pin anchors content identity, not line endings. The fingerprint rule is
normalize-then-hash: bytes are normalized CRLF to LF before the md5 is taken,
the same law the repository's `.gitattributes` applies to the checkout
(`* text=auto eol=lf`: every platform checks out LF, so a checkout shape can
never flip a judgment). Both comparison layers judge the same fingerprint:
the consistency layer takes the md5 of the normalized snapshot bytes against
pin.value, and the freshness layer takes the md5 of the normalized upstream
bytes the same way. A pin value is the md5 of normalized bytes, taken at sign
time, so signing and verifying share one rule and no layer depends on the
line endings of the tree it runs in.

## Verification

The seed suite keeps its snapshot-md5 segment name and FAIL/SKIP/PASS count shape, so
consumers read v2 results unchanged; transcription checks verify external entries against
the in-repo snapshots (hosted-verifiable); the IN-SYNC zero-write plan verdict stays the
only gate before a re-sign; the one-shot migration form converts the v1 seed to v2
(`python -I tools/jargon_map_sync.py --migrate`; seed suite as exit gate, mapping md
body untouched).

## Dual-machine evidence

Canonical: the seed suite green with all three layers exercised. Hosted: green with the freshness
layer reporting the declared skip; the first hosted run carrying that literal line is the
blindness-retired proof (run number recorded post-run in the whitepaper's v2 integration line).
