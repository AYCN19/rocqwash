# evolve cycle-1 verdict

> Purpose.  Verdict record of the evolve loop's cycle 1: the executed candidate C1, its split-lane diagnosis, the classification decision, and the cycle-2 guidance it produced.
> Interface.  Document face (a record, not executable). Read alongside the cycle-1 candidate draft `docs/evolve-draft-cycle1-20261113.md`; the classification feeds back into the evolve engine's candidate scoring, and the cycle-2 guidance feeds the next draft round.
> Dependencies.  The cycle-1 candidate draft cited in the Interface field, and the evolve engine `tools/evolve.py` (the harvest→derive→draft pipeline that produces such candidates); the CI evidence named in the Verdict heading.
> Evidence.  The evidence sources are cited inline: the CI job log (job `131383951644`) and the CI run record (run `43275862117`); the split-lane facts are transcribed from that evidence (the macOS observation lane fully green, the Windows cold-build lane red with `COQCHK_EXIT=1`).
> Exit-codes.  Not applicable to a document face.

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
