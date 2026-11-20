# rocqwash Contributor License Agreement (CLA)

> **CLAOverview**: the contributor license agreement overview of the rocqwash
> project: file structure, signing process, and the dual-licensing rationale.
>
> Purpose.  Explain why rocqwash requires a Contributor License Agreement and
> route each contributor class to the right agreement face (`CLA/ICLA.md`,
> `CLA/CCLA.md`, or `CLA/commercial_license_template.md`).
>
> Interface.  Read-and-route document face: contributors read the file table,
> follow the per-class signing steps, and send the signed agreement to
> `168888@live.cn`; no executable interface.
>
> Dependencies.  None at runtime — a standalone document face paired with
> `CLA/ICLA.md`, `CLA/CCLA.md`, and `CLA/commercial_license_template.md` under
> the AGPL-3.0-or-later protocol.
>
> Evidence.  The file table matches the faces under `CLA/`; the pre-header
> original is preserved in the sibling archive `CLA/README.md.zh.md`.
>
> Exit-codes.  Not applicable (document face; no executable interface).

All contributors to rocqwash must sign a Contributor License Agreement
before their contributions can be merged. This protects both the
contributor and the project.

## File Structure

| File | Applies to |
|------|---------|
| `ICLA.md` | Individual contributors (independent developers, students, freelancers) |
| `CCLA.md` | Legal entities (companies, institutions, teams) and their employees |
| `commercial_license_template.md` | Counterparties in commercial license negotiations (starting point for negotiating an alternative to AGPL-3.0 obligations) |

## Signing Process

### Individual Contributors (ICLA)
1. Open `ICLA.md`
2. Fill in the signature block (name, email, GitHub ID, date, signature)
3. Send it to `168888@live.cn`, or attach a scanned copy or screenshot to
   your first pull request

### Legal Entities (CCLA)
1. An authorized representative of the entity opens `CCLA.md`
2. Fill in the entity information and signature
3. Send it to `168888@live.cn`
4. Each employee who actually contributes must still sign the ICLA, but may
   cite the entity's CCLA number in the remarks field

## Why a CLA — and why the dual-licensing clause matters

rocqwash is distributed under **AGPL-3.0-or-later**. The AGPL keeps the
public edition free in the free-software sense and keeps commercial
pressure on hosted/closed integrations; it also means the project can
only grant an alternative (commercial) license for a contribution if the
contributor has authorized that. The CLA is exactly that authorization:
copyright and patent grants to the Project Steward plus a
dual-licensing authorization, so the project can offer a free public
edition and separately licensed enterprise terms at the same time.

Without a signed CLA, a contribution cannot be merged: the project would
lose the ability to license the combined work under any terms other than
AGPL-3.0.

## Authorship statement (human authorship; AI as instrument)

Contributors state, as part of the ICLA/CCLA representations, that their
contribution contains their own substantive creative authorship and that
artificial-intelligence systems, where used, acted only as instruments
under their direction. The human is the author; the tool is a tool. This
mirrors the project-wide statement in NOTICE and keeps the copyright and
patent chain on human footing.

## Contact

Project steward: 王宝军 — `168888@live.cn`
