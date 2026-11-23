# ai_flavor trend card - skip window w17, rocqwash (R2-111, first skip-branch window)

Purpose. Trend sampler window w17: anchor face (ask-named fetch
  HTTP/1.1, NETRED single-flight), rev-parse origin/main vs the
  expected 6af8067, rev-list 6af8067..origin/main count, skip-branch
  judgment. Ticket R2-111, seat live-lumen (subagent, dynamic
  workflow). First window eligible to take the skip form declared at
  w16 (counter = 4, anchor for w17 = 6af8067).
Interface. This card (English ASCII, five-field header per the norm
  header rule; non-ASCII gate = 0 bytes measured post-write) plus
  the receipt R2-111-receipt-skip.md; consumed by the dispatching
  workflow.
Dependencies. /Users/zuguangzhao/rocqwash MAIN clone (read-only
  this seat), git only; w16 card (FINAL anchor, counter face, skip
  declaration, baseline values), read first-hand; NO scan
  instruments run this window (skip form); no MCP helper.
Evidence. Every value below was measured this session with the
  quoted command forms; staging /tmp/rqw-mcp/r2-111/ holds all raw
  outputs. LIMITATION CARRIED ON THE FACE: BOTH fetch attempts
  FAILED (attempt 1 rc 128 Empty reply; attempt 2 hang, aborted at
  the 90 s cap) - the zero-new-anchor judgment below rests on the
  LOCAL ref; network confirmation FAILED this window.
Exit-codes. fetch attempt 1 rc 128 (Empty reply from server);
  attempt 2 no rc (hang, aborted at the 90 s tool cap, 0 bytes
  stderr); NO third attempt (NETRED: one backoff retry allowed,
  three consecutive flights forbidden); rev-list --count = 0; NO
  scan executed (skip branch), no instrument rc in play.

## Card body

- Ticket: R2-111, seat: trend sampler w17 skip-branch first window
  (read-only; zero repo-tree content; write faces = this card, the
  receipt R2-111-receipt-skip.md, and /tmp/rqw-mcp/r2-111 staging),
  identity live-lumen
- Date: 2026-11-23 (local calendar; the ask-named filename carries
  20261123 and is written exactly as named)
- Target repo: /Users/zuguangzhao/rocqwash (MAIN clone; NO checkout,
  NO scan, zero repo-tree writes this window)
- FINAL anchor: 6af8067ebf21ebe33a923500fea9cd6934c2e148 =
  origin/main at judgment time (== the ask's expected 6af8067 EXACT
  == w16's FINAL anchor EXACT) - measured on the LOCAL ref, which
  the failed fetch did NOT move

## 1. Anchor face: fetch FAILED x2 (rc 128 Empty reply; retry hang-aborted), single-flight honored (2 flights, cap 3), local ref did NOT move

- Pre-fetch face (measured at seat open): HEAD =
  71803083016e7deaf13881e7f11a271aac6a25a3 attached to branch
  supply/zgx/deliverables-2-norm-cures-20261123 (the R2-109
  leave-behind, untouched by this seat); porcelain = 3 M
  (docs/b-gate-audit.json, docs/scheduling-feedback.json,
  zgx-out/zgx-ledger-proposals.jsonl) + 3 untracked zgx-out files =
  6 entries == the w16 CLOSE face EXACT; local origin/main
  pre-fetch = 6af8067.
- The ask-named fetch, attempt 1: `git -C /Users/zuguangzhao/
  rocqwash -c http.version=HTTP/1.1 fetch origin` - rc 128, stderr
  102 bytes = "fatal: unable to access 'https://github.com/
  hy7pc8gfmf-dotcom/rocqwash.git/': Empty reply from server" - the
  SAME Empty-reply failure mode R2-109 recorded on its two
  post-merge fetches (the failure mode that hid the PR#37 landing
  from the local ref until w16's successful fetch).
- Backoff 20 s, then attempt 2 (the single allowed backoff retry;
  2 < 3 flights): HUNG - no rc, 0 bytes stderr, aborted at the 90 s
  tool cap. WORSE than attempt 1 (no server reply at all, not even
  an error line). NO attempt 3 (NETRED: three consecutive flights
  forbidden).
- Post-fetch measurement: origin/main =
  6af8067ebf21ebe33a923500fea9cd6934c2e148 UNCHANGED (the failed
  fetch moved nothing); `git rev-list --count
  6af8067ebf21ebe33a923500fea9cd6934c2e148..origin/main` = 0.
  Close face == open face: HEAD 7180308 unchanged, porcelain
  6 entries unchanged.
- Anchor-stays face recorded AS-IS (fail-loud): the count-0 is
  measured on the LOCAL ref whose last network-verified sync was
  w16's successful fetch earlier today. Anything landing upstream
  AFTER that sync was INVISIBLE to this window (both attempts
  failed). This is NOT a network-verified zero-new-anchor; it is
  an anchor-stays under fetch failure.

## 2. Skip-branch judgment: count leg = 0 -> SKIP branch TAKEN (first use of the w16-declared form); NO scan run

- The skip branch rule (w16 card counter declaration): a window
  whose rev-list count = 0 MAY take the skip form - anchor-face
  verify + rev-list count, full double scan skippable while the
  chain holds. This window's count leg = 0 (measured above), so
  the SKIP BRANCH IS TAKEN - first use since the w15/w16
  declarations.
- NO ai_flavor run, NO norm_lint run, NO tree diff, NO row diff:
  zero new anchors detected, nothing to compare against the
  baseline (em 7936 / norm error 763 / norm warn 1263 / rows 332 -
  the w16 values, carried unchanged BY DECLARATION of this skip,
  not by measurement).
- Honest-basis line (fail-loud): the skip rests on count = 0 at a
  ref that could NOT be re-verified against upstream this window.
  If upstream landed commits during the failure window, w18's
  first successful fetch will surface them (the R2-109 -> w16
  precedent: two Empty-reply failures hid PR#37; the next
  successful fetch carried the refmove and w16 caught it and went
  PAID). The skip taken here is conditional on the network truth
  w18 will reveal.

## 3. Carry declaration

- em 7936 CARRIED (no new tree sampled, no scan; the four-degree
  flat chain w12=w13=w14=w15=w16=7936 stands, unbroken).
- Three-flat counter: 4, MAINTAINED (this window exercises the
  w16-declared skip branch; it neither increments nor resets the
  counter - only em movement resets to 0).
- w18 anchor = 6af8067 (the current origin/main value, measured
  post-fetch this window).
- Failure-anchor-stay ledger: this window = consecutive
  failure-anchor-stay #1 (fetch failed AND anchor unchanged).
  Forward warning: if w18's fetch ALSO fails, that is #2; a third
  consecutive failure window must NOT take the skip form on a
  failed fetch - it must surface the network blockage (escalate /
  PAID by other means), not keep declaring anchor-stays.

## 4. Not run (not named by this ask, or gated)

No ai_flavor, no norm_lint, no per-commit enumeration (rev-list
count = 0, nothing to enumerate), no tree-diff instruments, no PR
feedback GETs, no MCP helper calls, no tests/run_tests.sh, no
checkout, no rocqwash-loop clone touch, no curl. ROCQWASH_MCP_
ALLOW_NET never set.

## Provenance and limitations

- NETRED ledger this seat, every event: (1) git fetch origin over
  HTTP/1.1, attempt 1 - rc 128, Empty reply from server (102 bytes
  stderr); (2) 20 s backoff; (3) git fetch origin over HTTP/1.1,
  attempt 2 - hang, aborted at the 90 s tool cap, 0 bytes stderr.
  TWO failed flights, then STOP (cap honored). No other git
  network ops; no curl; no MCP network. Zero successful network
  events this window.
- Staging (all outside the repo tree): /tmp/rqw-mcp/r2-111/
  (prefetch-face.txt, fetch.out, fetch.err, fetch2.out, fetch2.err,
  anchor-judgment.txt).
- Comparators: w16 card (FINAL anchor 6af8067, counter = 4,
  skip-branch declaration, baselines 7936 / 763 / 1263 / 332), read
  first-hand this session.
- Limitations: (a) THE carrying limitation - both fetch attempts
  failed, so this window's zero-new-anchor is a LOCAL anchor-stays,
  not network-verified; the skip is conditional on w18's network
  truth; (b) no scan values were measured this window - every
  baseline value in section 2 is carried by declaration from the
  w16 card; (c) the local repo's standing dirty face (3 M + 3
  untracked) is the w15/w16-recorded concurrent face, outside both
  scan lanes, unadjudicated, untouched; (d) STAGING CONCURRENCY
  FACE, recorded as-is, not adjudicated: another writer used
  /tmp/rqw-mcp/r2-111/ concurrently this window (pr34.json,
  pr35.json, pr36.json, call-b_gate_audit.jsonl + .err + .text,
  netred-ledger.txt, timestamps 10:31-10:33, NOT this seat's
  outputs), and this seat's fetch.err went from 102 bytes
  (attempt-1 stderr, read back in-session right after the run) to
  0 bytes by the post-write listing - an overwrite by the
  concurrent writer; ALL measured values survived (rc 128 and the
  verbatim stderr line are quoted in section 1 from the in-session
  capture; prefetch-face.txt 467 bytes and anchor-judgment.txt are
  intact and re-verified post-write), so no finding depends on the
  truncated artifact, but the raw attempt-1 stderr bytes are no
  longer independently re-readable from staging.
- Zero hand-written repo-tree content this session: no checkout,
  no writes, no branch moves; the fetch moved nothing (failed).
  Card + receipt + staging written OUTSIDE the repo. HEAD 7180308,
  origin/main 6af8067 at close.

Receipt line:
`R2-111 DONE w17 SKIP (skip branch TAKEN - first use of the w16-declared form; count leg rev-list 6af8067..origin/main = 0) @6af8067 (origin/main UNCHANGED == ask's expected 6af8067 EXACT == w16 FINAL anchor EXACT; fetch FAILED x2: attempt 1 rc 128 Empty reply from server 102 bytes stderr - the same failure mode R2-109 recorded twice, attempt 2 after 20 s backoff HUNG and was aborted at the 90 s cap 0 bytes stderr, NO third flight per the forbidden-three-consecutive rule; the count-0 is a LOCAL anchor-stays under fetch failure, NOT network-verified - last network-verified sync of this ref was w16's successful fetch earlier today, anything landing upstream since is invisible to this window, w18's first successful fetch will surface it per the R2-109 -> w16 refmove-carry precedent; pre-fetch face == w16 close face EXACT (HEAD 7180308 on supply/zgx/deliverables-2-norm-cures-20261123, porcelain 3 M + 3 untracked), close face == open face, the fetch moved nothing; NO scan run - ai_flavor / norm_lint / tree diff / row diff all skipped by the skip form; em 7936 CARRIED by declaration (four-degree flat chain w12..w16 = 7936 stands unbroken), counter 4 MAINTAINED (skip neither increments nor resets; only em movement resets to 0), baselines 7936/763/1263/332 carried unchanged by declaration not measurement; w18 anchor = 6af8067; failure-anchor-stay ledger: this window = consecutive #1, forward warning - a w18 fetch failure = #2, a third consecutive failure window must NOT take the skip form on a failed fetch; NETRED 2 events (fetch x1 rc 128 Empty reply, fetch x1 hang-abort) 2 failures 0 successes 1 backoff, zero MCP, zero curl, zero hand-written repo-tree content 2026-11-23`
