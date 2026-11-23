# MANIFEST - zgx deliverables batch 3 2026/11/23 (4 readings cards)

Purpose. Session card for ticket R2-112; states the ticket's measured facts (archive copy of the deliverables batch 3).
Interface. Data face (markdown); not executable; read by the trend reader and the norm scanner.
Dependencies. Documents and staging paths cited in the body; no runtime dependencies.
Evidence. Anchor and md5 values first-hand measured this session (source census in agent R2-112 receipt-plan section 2, re-verified at assembly); supply receipt R2-112-receipt-pr.md; per-item post-copy md5 equals the return-package source md5 (4/4).
Exit-codes. Not applicable (data face).

## Card body

Ticket: R2-112
Seat: assembly supply agent (green-path PR face, R2-112)
Anchor: origin/main = 6af8067ebf21ebe33a923500fea9cd6934c2e148 (full sha re-verified by fresh fetch at assembly, 2026/11/23; fetch attempt 1 failed rc=128 empty reply, attempt 2 after 120s backoff confirmed the anchor unchanged - no drift, matches `seat A` receipt-plan anchor exactly)
Mode: original-name copy, zero content modification; post-copy md5 must equal source md5 (verified 4/4); ASCII gate (bytes above 0x7F) = 0 for all 4 items, re-run post-copy
Excluded: MANIFEST itself self-excluded from this list (its md5 is recorded in the supply receipt, batch-1/2 precedent)

name	bytes	md5
ai-flavor-trend-w16-20261123.md	20773	4bc3342e08e449b65ca24c7b5335a727
rsi-reshoot-3-20261123.md	8597	0bb49397c2d3a01cd587379840b503c4
ai-flavor-trend-w17-20261123.md	10559	344416f4bdc0594a3505564e4d0d0712
mech-health-2-20261123.md	15628	a7497da0eefbcb10b21c6cd1bbc9524f
