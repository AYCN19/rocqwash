# net-interface-SPEC.md - termbase community-norm source interface (stub, ALLOW_NET face)

Purpose. Define the ALLOW_NET face of the E3 termbase: the community-norm source interface stub that a future fetch pass implements, with the three domain slots recorded unfetched and the transcription snapshot protected from network content.
Interface. Contract stub only (schema `rocqwash-termbase-net/1` proposed in section 3); no engine code ships in this delivery. The seed discipline for this directory is data JSON + SPEC md + tests py; the engine itself grows later on rocqwash's own wash_shape / norm_lint / evolve faces.
Dependencies. `termbase.json` in this directory (built-in seed); the project term glossary recorded at `termbase.json` -> `source_of_truth.path` (the sole maintenance point; the built-in seed is a read-only transcription snapshot of its section 4.0).
Evidence. `test_snippet.py` in this directory asserts the slot and snapshot invariants; the register checks cited in the delivery receipt ran `tools/norm_lint.py` and the ai-flavor self-check on these faces.
Exit-codes. Not applicable (specification face; no executable ships here).

## 1. Purpose

The built-in seed carries two kinds of content:

1. **Snapshot face** (shipped, offline): the section 4.0 entry skeleton and its 98 entries, transcribed verbatim from the glossary. This face is final for this delivery and is never rewritten by network activity.
2. **Domain slot face** (declared, unfetched): three slots that name community norm sources the termbase should eventually consume. This SPEC is the contract for how those slots get filled.

## 2. ALLOW_NET face (default deny)

- The termbase performs **zero network activity by default**. Every slot in `termbase.json` carries `"status": "unfetched"` and `"content": null`.
- Fetching real slot content is a **candidate order outside the current delivery**: it happens only in a pass that the user explicitly orders and that authorizes network use.
- Any authorized fetch follows the per-launch registration rule: one NETRED ledger entry per launch, including failed launches. A failed fetch is recorded as a failed fetch; it is never treated as evidence that the source drifted (`fetch failure != drift`).
- Rate limits, backoff, and batch spacing follow the house NETRED rules: check the rate-limit budget first, batch with intervals, back off on failure, and never saturate the shared limit pool.

## 3. Interface stub (proposed contract, schema `rocqwash-termbase-net/1`)

The engine-side face to be grown later (stub here, implemented only in a later delivery):

```
fetch_slot(slot_id, opts) -> FetchResult
```

`FetchResult` fields (all mandatory; determinism discipline: sorted keys, no local wall-clock fields inside the content body, UTC timestamps only at the envelope level):

| Field | Type | Meaning |
|---|---|---|
| `slot_id` | string | one of the three slot ids in `termbase.json` |
| `source_url` | string | the URL actually fetched |
| `source_version` | string or null | upstream version/commit/tag the content was fetched at, when the source exposes one |
| `fetched_at_utc` | string | UTC ISO-8601 instant of the fetch (envelope level only) |
| `content` | string | the fetched text, kept as fetched (transcription discipline applies downstream, not here) |
| `content_sha256` | string | hash of `content` bytes, for idempotent re-runs |
| `status` | enum | `fetched` / `fetch-failed` / `source-unavailable` |
| `failure_note` | string or null | mandatory when `status` is not `fetched` |

Constraints on any implementation:

1. **GET only.** No write verbs against community sources.
2. **One declaration per slot.** The slot's `source` object in `termbase.json` is the only fetch target; implementations do not improvise mirror URLs. Mirror fallback, if ever needed, is a user-adjudicated change to the slot declaration first.
3. **Idempotence.** Re-running with the same upstream content must produce a byte-identical `FetchResult` apart from `fetched_at_utc`.
4. **No content overwrite.** A successful fetch writes into the slot's `content` field only. It never edits the snapshot entries, never edits the glossary path, and never merges fetched text into the transcription face. Slot content and snapshot entries are two disjoint faces (see section 5).

## 4. Slot inventory (all unfetched in this delivery)

| Slot id | Title | Declared source | Refresh trigger (summary) |
|---|---|---|---|
| `mathlib-naming-convention` | mathlib naming convention | declared URL in `termbase.json` (`url_verified: false`; not probed in this delivery) | upstream naming rules change; user-ordered pass |
| `lean-style-guide` | Lean style guide | declared URL in `termbase.json` (`url_verified: false`; not probed in this delivery) | Lean release changes consumed style guidance; user-ordered pass |
| `journal-style` | journal style | no URL yet; venue nomination pending; local-corpus candidates recorded in the slot | user nominates a target venue; user-ordered pass |

Every refresh, regardless of slot, also re-runs the seed schema tests (`test_snippet.py` segment) and updates the slot's recorded version and the NETRED ledger together.

## 5. Provenance and overwrite rules

- Fetched slot content is **reference material**, not adjudication. Adjudications (what a term should be) remain the glossary's authority; the built-in snapshot transcribes that authority and stays verbatim.
- If a future delivery wants a fetched convention reflected in adjudications, the path is: fetch into the slot, register the proposal, and let the human maintenance authority update the glossary; then a sync pass re-transcribes the glossary section into the snapshot (updating `meta` counts and the `snapshot` hash together). There is no path from network content directly into snapshot entries.
- Slot content provenance is recorded in the slot itself (`source_version`, fetch envelope), so any consumer can tell transcribed snapshot data from fetched reference data.

## 6. NETRED ledger requirements

A fetch pass must append, per launch (success or failure): slot id, target URL, launch instant (UTC), outcome, and content hash when fetched. The ledger lives with the delivery receipt, not in this directory.

## 7. Non-goals in this delivery

- No fetch, no probe, no URL verification (the declared URLs are recorded as declared, with `url_verified: false`).
- No engine implementation of `fetch_slot`.
- No change to the snapshot face or to the glossary source.
