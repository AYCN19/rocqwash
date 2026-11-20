# rocqwash Commercial License — Negotiation Template (v1.0, 20261114)

> **CommercialLicense**: the commercial license negotiation template of the
> rocqwash project: module scope, grant, restrictions, audit ledger, and
> signature block for negotiating an alternative to AGPL-3.0-or-later obligations.
>
> Purpose.  State the negotiation starting point under which the Licensor may
> grant a licensee alternative rights to the AGPL obligations, module by
> module (M1-M5), with every bracketed item left as a negotiation variable.
>
> Interface.  Read-and-negotiate document face: pick modules in the section-2
> matrix, fill the bracketed variables of sections 3-8, and return the
> section-9 signature block to `168888@live.cn`.
>
> Dependencies.  None at runtime — a standalone document face paired with
> `CLA/CCLA.md`, `CLA/ICLA.md`, and `CLA/README.md`; the AGPL boundary rule
> is registered in `NOTICE`.
>
> Evidence.  Its module matrix matches the license protocol registered in
> `NOTICE`; the pre-header original is preserved in the sibling archive
> `CLA/commercial_license_template.md.zh.md`.
>
> Exit-codes.  Not applicable (document face; no executable interface).

> Starting point for negotiating an alternative license to the
> AGPL-3.0-or-later obligations of the rocqwash repository. All bracketed
> items are negotiation variables. The final instrument supersedes this
> template; nothing in this template binds the Steward until signed.
>
> Licensor (Steward): 王宝军 — 168888@live.cn

## 1. Parties and definitions

| | |
|---|---|
| **Licensor** | 王宝军 (Project Steward), 168888@live.cn |
| **Licensee** | [legal entity name, registration number] |
| **Software** | rocqwash, the repository-hygiene and CI triage toolset at https://github.com/hy7pc8gfmf-dotcom/rocqwash, including tools/, wrapper/, certify/, verify/, seeds/ data, .github/ workflow faces, and documentation |
| **AGPL License** | GNU Affero General Public License v3.0 or later (the public edition) |

Background. The Software is distributed publicly under the AGPL License.
The Licensee wishes to obtain rights that the AGPL License conditions on
open-sourcing, without those conditions.

## 2. Scope — pick and price per module

| # | Licensed module (one or more) | Typical licensee need |
|---|---|---|
| M1 | AGPL exemption for internal closed-source use and modification (no copyleft trigger for Licensee's own code combining with the Software) | Enterprises embedding rocqwash into proprietary toolchains |
| M2 | AGPL exemption for hosted/managed offering (offering the Software, modified or unmodified, as part of a network service without source-disclosure obligations to service users) | Platforms productizing the CI triage / hygiene faces |
| M3 | Hosted managed triage service operated by the Licensor (five-family triage, budget-capped self-heal, auto-repair rounds, round ledger with rollback/salvage) — SLA-backed | Licensees buying the outcome, not the software |
| M4 | Enterprise rule and data packs (extended edit-class tables, enterprise jargon/termbase packs, enhanced taxonomy rules) — non-public increments | Licensees wanting capability beyond the public seeds |
| M5 | Priority maintenance, support, and direct engineer access (response-time SLA) | Regulated or production-critical adopters |

Reservation. The Licensor reserves all rights not expressly granted.
The public source face remains AGPL-licensed; this template never imposes
retroactive restrictions on it (boundary principle registered in NOTICE
and docs/license-protocol-v1.0-20261114.md).

## 3. Grant

Subject to payment of [fees] and the terms herein, the Licensor grants
the Licensee a [non-exclusive / exclusive within Field], [worldwide /
Territory], [perpetual / Term] license to [module set M_]: to install,
execute, modify internally, and internally deploy the Software and the
Licensed Modules [without the obligations of sections 4–13 and 13 of
AGPL-3.0, to the extent of the licensed modules / as a hosted service
operated by the Licensor per Annex SLA].

## 4. Restrictions (standard)

No sublicense; no transfer without written consent; no removal of
NOTICE/attribution faces; no use of the rocqwash name or marks beyond
nominative reference (trademark rights reserved); no benchmark
publication of enterprise rule packs without consent.

## 5. Audit and ledger

Licensee shall keep reasonable records sufficient to verify scope
compliance for [12/24] months after expiry. The Software's own
experience ledger (append-only, fingerprinted) is admissible between the
parties as a factual record of tool actions, subject to its masking.

## 6. Warranties and liability

AS IS, per AGPL §15-16 defaults unless Licensee purchases the support
module (M5), in which case the SLA annex defines the sole and exclusive
remedies. Liability cap: [fees paid in prior 12 months].

## 7. Term, termination, effects

[Perpetual / annual]. Material breach → cure period [30] days →
termination of the grant; AGPL-3.0 remains available to the Licensee for
versions obtained under it (irrevocable per §4.2 for prior versions
received under AGPL).

## 8. Governing law

The People's Republic of China. Venue: [court/arbitration institution].

## 9. Signature

```
Licensor:  王宝军   Date: ____________  Signature: ____________
Licensee:  [name]   Date: ____________  Signature: ____________
```

Annexes: A. Fee schedule · B. Module matrix (M1–M5 selection) ·
C. SLA terms (M3/M5) · D. Enterprise rule-pack inventory (M4)
