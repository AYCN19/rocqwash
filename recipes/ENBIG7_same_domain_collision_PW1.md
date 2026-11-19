# ENBIG7_same_domain_collision_PW1.md — recipe face: same-domain twin-agent collision, private-world rebuild (PW1, the dver2-enbig7 case documented) · original title: `处方件 — 同域双席撞·私占世界重建（PW1·dver2-enbig7 判例文档化）`

> Purpose.  Recipe PW1 handles the same-domain twin-agent collision: an out-of-bounds agent wrote through another agent's exclusive write domain, and the world face was displaced or polluted. Lesson 3 of the five-lesson ledger ("the dver2-enbig7 same-domain collision") carries two faces: the precursor machine check already exists as a tool check (`tools/select_audit.py`, DUP-CROSS; polishing piece 2); this face lands the **disposition side**, the world-recovery recipe for after a collision has happened, under the exclusive write-domain invariant.
>
> Interface.  Document face only; no runtime interface. The recovery steps ride the wired tools: `tools/select_audit.py` (DUP-CROSS / DUP-ORDER / NOT-IN-ORDER), `wash/world_hook.py` (`--world <private world> --manifest <certified-generation account>`), `wrapper/quad8_reconcile.py` + `wrapper/frozen_call.py` (copy-group reconciliation), `wash/wash_engine.py` (frozen) with the `wash/world_hook.py --` pass-through form, and `certify/freeze_manifest.py` (two-layer freeze). The original Chinese text is preserved in the sibling `.zh.md` archive.
>
> Dependencies.  Read-only precedent sources, verified present in the tree at documentation time: `sandbox/seat_dver2/账/collision_enbig7_20261031.md` (the same-day verbatim record of the collision; arbitration `36c35816`), `world_md5_assert.txt` / `world_md5_assert_close.txt` (the two-snapshot against-source assertion manifests: pre-born and close-out window), and `world_refresh_race_note.txt` (the Live-refresh race record); the roster tables `ConstructiveWorld_Live/order.txt` and `scripts/order.txt` cited in section 3.
>
> Evidence.  Documented November 1, 2026, in `recipes/`, by agent `rqsup4` (the inspection polishing round; the third piece of the five-lesson feedback round). The case measurements in the tables below come from the case record: arbitration `36c35816`; 25/25 md5 assertions OK; 24 chain pieces born rc=0 (14:00:09-14:34:46) and the product born rc=0 (14:35); three zero-tampering re-assertions during the intrusion window.
>
> Exit-codes.  Not applicable to a document face; the referenced tools keep their implemented exit-code semantics unchanged (measured in the case: `world_hook.py` 3 WDIFF + 1 WMISS → RED rc 9; second-family copy refusal rc 8; `select_audit.py` NOT-IN-ORDER failing).

## 0. At a glance

| item | value |
|---|---|
| recipe number | **PW1** (private-world rebuild) |
| defect name | same-domain twin-agent parallel write: the out-of-bounds agent writes through another agent's exclusive write domain, and the world face is displaced or polluted |
| case | October 31, 2026, the enbig7 English-batch agent wrote out of bounds into `seat_dver2` (from 13:31): the `tree/` world .vo displaced; born debris (.vok/.vos/.aux/.glob); `logs/` born_dv*.rc/.log; `gate4_itg_tree.json`/`gate6_itg_*.json`; `_dvtree/`; the `work/` deployment |
| arbitration | arbitration `36c35816`: `seat_dver2` stays with this agent; the intruder converges back to `seat_enbig7`; disposition = wait for quiet → full re-audit → private world |
| governing invariant | **the exclusive write-domain rule** (each agent owns an exclusive write domain; the domain boundary is binding on all agents); products from the intrusion window are never adopted; another agent's domain is read-only and never cleaned by proxy |

## 1. The defect (root-cause chain, transcribed from the case record)

1. **The domain boundary was breached**: the intruder held the reg lane (`/tmp/cw_reg_enbig7`,
   pids 94466/94468/94481) and wrote out of bounds into another agent's exclusive domain:
   a scheduling-plane defect, not a tooling-plane defect.
2. **The world spec was incomplete yet born anyway**: the intruder's two born attempts failed
   (r1 13:33 missing `S12_B5RecycleSF`; r2 13:42 missing `UpReqQExpTail`): the process defect of
   born with the chain pieces not yet complete. PW1 does not excuse this defect: after the
   intruder converges back to its own domain it must repair its own world spec (born only after
   the chain-piece reconciliation is complete); the recipe does not perform this on its behalf.
3. **The Live-refresh race** (`world_refresh_race_note.txt`): at 13:31:30, while the cp broadcast
   the world, the Live-side runner refresh was in flight: a transient extra
   `abl_dmw2_sharpen_decay.v` (md5 `c5e43ba4…`) appeared, and after the cp the Live side settled
   back at generation 140. Disposition: remove it from `tree/` (inside this agent's write
   position) and archive it; the world is the Live generation-140 invariant, and members outside
   the target dependency closure do not enter the world.

## 2. The recipe (PW1 five steps: fixed order, memorized, never skipped)

| step | action | measured in the case (`seat_dver2`, October 31, 2026) |
|---|---|---|
| 1 | **Arbitration and domain convergence**: orchestration exercises the ruling authority (the ownership ruling plus the intruder converging back to its own domain); the recipe does not perform arbitration | arbitration `36c35816`: `seat_dver2` stays with this agent; enbig7 converges to `seat_enbig7` |
| 2 | **Wait for quiet**: no cuts before the intrusion stops; products from the intrusion window are never adopted (the `logs/` candidates and the `work/` deployment all discarded) | "no intrusion-window product was adopted" is on record |
| 3 | **Full re-audit**: against-source md5 assertion: each world `.v` piece asserted against its source (the Live current text / the ledger-pinned generation), plus the chain pieces asserted against the frozen-ledger md5, one assertion line per piece; non-target closure members removed and archived | `world_md5_assert.txt`: 25/25 OK (20 Live .v pieces against sources + 4 chain pieces against the digcure frozen ledger, the BL/PI/PEI/truncfam four-source equal-value record) |
| 4 | **Full replay of the private world**: build the private world directory (`work/<private>/`), born each piece in `order.txt` chain order (all rc=0), and close out with the product born | 24 chain pieces born in `order.txt` chain order, all rc=0 (14:00:09-14:34:46); the product born rc=0 (14:35) |
| 5 | **Three-round full md5 re-assertion**: per-piece md5 assertions at the three snapshots (pre-born / after gates / before freeze); close out only at zero tampering | during the intrusion window all three re-assertions read world_dig at 0 tampering (the manifest's three snapshots are on record) |

## 3. Wiring into the rocqwash tooling (the six pieces in this repository, each in place)

1. **Precursor face** (before the collision): `tools/select_audit.py`: DUP-CROSS (one piece
   double-claimed: the precursor of a same-domain twin-agent name collision) + DUP-ORDER
   (same-name duplicate roster rows). Measured table case (November 1, 2026, inspection run):
   the `ConstructiveWorld_Live/order.txt` 199-row table carries DUP-ORDER×2
   (`UpReqBanachExpAdd`/`abl_normconv_real`, each with two rows R28+R29, equal generation
   signatures); only a full-table grep reveals it; record-only, no ruling (external repository:
   recorded faithfully, not repaired on its behalf).
2. **Piece-selection face**: the same tool's NOT-IN-ORDER: piece selection must read the
   **tree-side** `order.txt` table in full (case: EntropyUnsatMark is on the Live table, absent
   from the `scripts/order.txt` 671-row table; the wrong table fails the check, the mechanical
   demonstration of the read-the-right-table discipline).
3. **Pre-born world assertion**: `wash/world_hook.py`: `--world <private world> --manifest
   <certified-generation account>` asserts world = certified generation; **the anchor must move
   with the generation** (never pass an old-generation anchor off as the certified generation).
   Measured case (November 1, 2026, inspection run): the built-in nw5ver five anchors against
   `seat_nw5ver/tree` read 5/5 MATCH; the same anchors against `seat_dver2/tree` (the new
   generation rebuilt at 14:35) read 3 WDIFF + 1 WMISS → RED rc 9.
4. **Tool-copy-group face**: `wrapper/quad8_reconcile.py` + `wrapper/frozen_call.py`:
   four-repository same-md5 copy-group reconciliation plus per-call assertion, guarding against
   tool-layer cross-writes (second-family copies refuse execution, rc 8).
5. **Sanitize-born face**: `wash/wash_engine.py` (frozen) plus the `wash/world_hook.py --`
   pass-through form: with the private world's passing verdict, the sanitized products are
   released to disk.
6. **Close-out face**: `certify/freeze_manifest.py` (two-layer freeze) plus the close-out-window
   re-assertion manifest (step 5's third snapshot is its on-record form).

## 4. Boundaries (the recipe does not force-fit)

- **Arbitration authority rests with orchestration**: this recipe is the **execution face** after
  arbitration; inter-agent disputes are not handled unilaterally, and domains are not cleaned for
  one another.
- **Another agent's domain is read-only**: even under intrusion, the disposition actions (debris
  removal / rebuild) happen only **inside this agent's write position**; defects inside the
  intruder's domain are repaired by the intruder itself.
- **PW1 does not replace the acceptance checks**: the pre-born assertion (`world_hook`) and the
  close-out freeze (`freeze_manifest`) stand on duty independently; a private-world rebuild
  exempts none of the checks.
- **Anchor-generation discipline**: if the private world is rebuilt on a new generation, the
  certified-generation anchor must be re-snapped at the generation change; never reuse an
  old-generation manifest as the certified generation (the nw5 lookalike-source trap).
