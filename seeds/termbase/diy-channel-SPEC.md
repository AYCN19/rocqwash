# diy-channel-SPEC.md - agent DIY termbase entry channel (contrib_intake four-gate isomorph)

Purpose. Define the lane where agent workers register DIY termbase entries without touching the read-only snapshot, mapped gate-for-gate onto the repository's existing four-gate intake instrument.
Interface. Channel specification only (entry book schema `rocqwash-termbase-diy/1` in section 4); no engine code ships in this delivery (seed discipline: data JSON + SPEC md + tests py).
Dependencies. rocqwash `tools/contrib_intake.py` (read-only four-gate contribution inspector; gate assembly at contrib_intake.py:819-825, contract docstring at contrib_intake.py:3-32, report schema `rocqwash-contrib-intake/1` at contrib_intake.py:86); `termbase.json` and `net-interface-SPEC.md` in this directory.
Evidence. The isomorphism table in section 3 cites the intake instrument line by line; `test_snippet.py` guards the snapshot and slot invariants that the channel must preserve.
Exit-codes. Not applicable (specification face; no executable ships here).

## 1. Purpose

The built-in seed `termbase.json` is a read-only transcription snapshot of the project term glossary (section 4.0). Agent workers that discover or coin a term adjudication outside that snapshot need a lane to register it without touching the snapshot and without silent promotion. This SPEC defines that lane, mapped gate for gate onto the existing intake instrument so the mechanical behavior is inherited, not reinvented.

## 2. Lane discipline (isolation comes first)

1. **The snapshot is untouchable.** DIY activity never edits `termbase.json` entries, its `entry_skeleton`, its `source_of_truth`, or its `meta`. The snapshot changes only through the sync discipline recorded inside it: the human maintenance authority updates the glossary, then a sync pass re-transcribes the section.
2. **DIY entries land in their own book**: `seeds/termbase/diy_entries.json`, schema `rocqwash-termbase-diy/1` (entry schema in section 4). This book is an append face: admitted entries are appended, never rewritten in place.
3. **Promotion path** (the only path from DIY to snapshot): `proposed -> admitted` (four gates pass) -> `promoted` (the adjudication is adopted by the glossary's maintenance authority in the glossary itself; a later sync pass re-transcribes the section and the entry's content becomes redundant). Zero silent promotion: nothing in this directory ever edits the glossary.

## 3. The four gates (isomorphic mapping)

Each DIY intake runs the four gates without short-circuit, mirroring the intake instrument's gate assembly (contrib_intake.py:819-825). Verdicts are data: `BLOCK` records the block, it does not abort the other gates.

| # | Intake gate (source) | DIY termbase gate | What it checks | Blocking condition |
|---|---|---|---|---|
| 1 | `registry` (registry books reconciled by union dry run; A2 collision on an added key already in main) | **key registry** | entry `id` unique across the DIY book; `current_term` (first cell) not already adjudicated in the snapshot face for the same `sub_table` unless the entry explicitly claims a refinement of that row (`refines` field, mandatory in that case); DIY book stays well-formed | collision or malformed book: BLOCK, with a regeneration prescription in the intake record (new id, or explicit `refines` link), mirroring the intake instrument's prescription face (contrib_intake.py:355-384) |
| 2 | `norm` (new/changed prose faces linted by `norm_lint.py`; error-level blocks) | **replacement norm** | the proposed replacement text is a standard expression: lint the entry's text faces through `norm_lint.py`; the replacement must not itself introduce jargon or AI-flavor faces (no re-translation into fresh jargon) | any error-level finding on the entry's replacement or note text: BLOCK; warn-level findings recorded |
| 3 | `gate_expectation` (gate4 per .v face plus gate7 probe: availability-only unless a real probe command is given) | **adjudication expectation** | every entry carries its adjudication expectation: non-empty `source` and `evidence` fields, and a machine-checkable schema face. Availability-only mode checks field presence and shape. Real-probe mode (run when the claimed local source is reachable): verify the cited glossary row actually carries the cited adjudication (diff the cited cells against the snapshot or the glossary file) | missing/empty provenance fields or schema-shape failure: BLOCK. Real-probe mismatch against the cited source: BLOCK. Probe unavailable: recorded, non-blocking, expectations deferred |
| 4 | `isolation` (changed paths outside the contribution lane tallied as warning-level evidence) | **lane isolation** | the intake touches only `seeds/termbase/` (and, for the receipt, the agent's own log lane). Any changed path outside the lane is tallied as warning-level evidence in the intake record; the snapshot file appearing as modified is an automatic BLOCK regardless of the tally (it is the untouchable face) | snapshot modified: BLOCK. Other outside-lane paths: warning-level, recorded, non-blocking |

Gate ordering and non-short-circuit behavior follow the intake instrument: all four gates always run; the summary carries `verdict` (PASS/BLOCK), `block_gates`, and `warn_total`.

## 4. DIY entry schema (`diy_entries.json`, schema `rocqwash-termbase-diy/1`)

```json
{
  "schema": "rocqwash-termbase-diy/1",
  "entries": [
    {
      "id": "diy-<yyyymmdd>-<nnn>",
      "status": "proposed | admitted | promoted",
      "sub_table": "proposed-new | round2 | intl | round3 | round4",
      "current_term": "the term face the entry adjudicates",
      "adjudication": "the proposed normative replacement",
      "note": "screening note (context, scope, first-occurrence form)",
      "source": "where the adjudication comes from (user order, community source, precedent)",
      "evidence": "pointer to the material backing the adjudication",
      "refines": "snapshot entry id this entry refines, or null",
      "intake": "intake record reference (gates verdicts)"
    }
  ]
}
```

Key names are English (ASCII). Entry text may be any language the adjudication needs; the replacement norm gate still applies.

## 5. Statuses

- `proposed`: entry registered, gates not yet run or not yet green.
- `admitted`: all four gates green (or warnings recorded only); the entry is a valid reference for consumers.
- `promoted`: the adjudication has been adopted into the glossary by its maintenance authority, and a sync pass has folded it into the snapshot. The DIY entry keeps its history row; it is not deleted.

## 6. Non-goals in this delivery

- No `diy_entries.json` ships now (the book is created by the first intake that has an entry to register).
- No engine implementation of the four gates for this lane; until an implementation grows on the intake instrument, intakes are performed by an agent running the checks of section 3 by hand and recording verdicts in the intake record.
- No write access to the glossary source or to the snapshot face.
