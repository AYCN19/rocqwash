# evolve cycle-1 verdict (20261113)

## Executed candidate

C1 (P0, engine TOP1): Set tip `0d58903b` self-cert run#310 A-content-red diagnosis.

## Verdict (evidence: job 131383951644 log, run 43275862117)

**Split-lane finding**: on the same commit, the macOS observation lane is fully green
(gate7 544-piece extraction pass, coqchk full-tree success 1064s, gate2 CLEAN, uploads pass)
— the content face is certified by the mac lane. The red is confined to the **Windows
cold-build lane**: `COQCHK_EXIT=1` with the COQCHK export resolving to the 9.1 fallback
path (`D:/ComplexAnalysis/attn/ocaml_work_20261101/.../coqchk.exe`); the yml comment block
itself documents the form-A injection rule ("form-A script absent from tree -> 9.1 coqchk
-> gate2 banner red, fail-loud"). gate2 verdict `NO_AXIOMS_SECTION` is the banner-missing
consequence. Repair ownership: Windows lane owner (toolchain wiring), not content.

## Classification

A-content-red **downgraded to lane-level toolchain issue** (mac lane certifies content;
content fix = none needed). Feeds back to the engine: family C1-style candidates on
split-lane runs should consult the sibling lane verdict before scoring impact.

## Cycle-2 guidance

TOP candidate shifts to: Windows cold-build lane form-A injection repair (owner: lane
owner) + the two cross-repo registry decisions already queued (2 orphans, badge-anchor
form 28 pairs).
