# seeds/claim-watch/README.md: the RH/NS claim-watch signal seed (ticket 13 config).

> Purpose.  Documents `signals-rh-ns.json`, the config seed for `tools/claim_watch.py`: the eight RH signal families and the three NS/Euler triggers transcribed from the requirements document v2-B (ticket 13, the claim-watch nativization ticket, signal list section), the per-entry form mapping, and the reachability caveats that await the first live calibration round.
> Interface.  Document face; no runtime role. The seed validates against schema `rocqwash-claim-watch-config/1` (`tools/claim_watch.py` rejects unknown keys, so this file is the only place the transcription notes live).
> Dependencies.  `tools/claim_watch.py` (the schema authority and the fetch-face definitions).
> Evidence.  The seed file passes `validate_config` (13 signals, zero errors, measured at this increment's integration); the mapping table below cites the ticket item for every entry.
> Exit-codes.  Not applicable to a document face.

## 1. Entry-to-ticket mapping (8 RH signal families, 3 NS/Euler triggers)

The frozen schema holds one source per entry, so two ticket families land as multiple entries (the `rh-02` family spans three re-run repositories, the `rh-05` family spans the HN thread and the Zulip topic): 13 entries cover the 8 + 3 families.

| Entries | Ticket item | Kind | Face notes |
|---|---|---|---|
| `rh-01-brunoloff-progress` | RH 1: brunoloff/rh-lean-progress (progress.json) | repo-path | github-contents file face; the ticket's conclusion-level keyword family rides verbatim |
| `rh-02a/b/c-rerun-*` | RH 2: the luosiallen / Hertaspace / sunnyspot114514 re-run repositories (commit/REPORT) | repo-path | github-owner listing face: the ticket names the three owners, not exact repository names, so the digest covers each owner's sorted full_name+pushed_at list (a new or pushed re-run repository lands as a digest change); `path` ("REPORT") is unused on this face and rides until calibration pins the repositories |
| `rh-03-deicyde-verification` | RH 3: Deicyde/riemann-hypothesis, new files under verification/ (NOTES + static-scan + comparator output) | repo-path | github-contents directory listing face of `verification`: a new file changes the listing digest (round-change) and file names surface to the keyword face |
| `rh-04-alpoge-remark-pdf` | RH 4: alpo.ge/remark.pdf byte comparison, baseline 245114B | repo-path | bare-host raw-bytes face; `hash_pin` carries the ticket's byte baseline as `bytes:245114` (a pin mismatch is pin-drift) |
| `rh-05a-hn-50574968` | RH 5a: HN item 50574968 | status-endpoint | HN Firebase item API (a JSON object); no phase face on this source (phase_field empty), the keyword family carries the signal |
| `rh-05b-zulip-general-113488` | RH 5b: Lean Zulip #general 113488 | zulip-web-public | the built-in no-auth recipe (llms.txt face then api/v1/messages face); a 401 registers unverifiable honestly, never fabricated |
| `rh-06-github-search` | RH 6: GitHub search for new conclusion repositories | status-endpoint | search/repositories API (a JSON object, total_count as the phase field with no done phases); the trigger is the round-over-round digest change of the result set |
| `rh-07-rhverify-status` | RH 7: RH/VERIFY http://106.14.11.164/api/status (phase flip, audit/complete segments) | status-endpoint | the reference schema source; phase flip fires on "audit"/"complete", heartbeat_at staleness defaults (90 minutes) arm the target-silent-death class |
| `ns-08a-tristanbuckmaster-events` | NS a: tristanbuckmaster/navier-stokes new commit/release | status-endpoint | GitHub events API (one face covering PushEvent and ReleaseEvent); a new commit or release changes the digest; the keyword "certificate" carries the certificate-data appearance |
| `ns-08b-comparator-flags` | NS b: comparator*.json gaining enable_nanoda:true / external_kernels / .github/ CI | repo-path | github-contents root listing face (path empty): the appearance of comparator files or .github/ lands as a listing keyword hit and a digest change |
| `ns-08c-sunnyspot-certificate` | NS c: sunnyspot certificate-check.json `numerical_verification` flipping from not_run | repo-path | owner listing face (the ticket names the owner, not the repository); the flip lands as a push, which changes the pushed_at digest; the first round registers the baseline, so a flip that predates the first round cannot be seen from here (the desktop-side watch held the pre-flip state) |

## 2. Honest transcription caveats (awaiting the first live calibration)

1. Owner-only names: ticket items 2 and c name owners (`luosiallen`, `Hertaspace`, `sunnyspot114514`) without exact repository names. The seed transcribes the owners verbatim and the owner-listing face makes the watch functional without inventing repository names; calibration may replace them with `owner/repo` contents faces once pinned.
2. Trigger b names two repositories (the pair of the NS/Euler work stream); the ticket names only one of them (`tristanbuckmaster/navier-stokes`), so one entry carries the named repository and the second entry awaits its own calibration pin.
3. Reachability, rate limits (the GitHub API's unauthenticated budget) and the live Zulip recipe behavior are untested by construction here: the live face is the network face and no live run belongs to this seed's integration. Every unreachable face registers honestly (unverifiable or fetch-failed) until calibration.
4. The conclusion keyword family is the ticket's conclusion-level family rendered in English; hits are forwarding-to-adjudication registrations (ok=false, verbatim quote), never auto-verdicts.
5. The Zulip recipe's no-auth shape is the earlier audit work stream's finding (the login-wall assumption was falsified there); a 401 on a face registers unverifiable honestly on that face.
