#!/bin/bash
# ci-green-watch.sh — CI-green watcher (the alignment-law trigger).
#
# Purpose.  Poll the repository's main-branch CI runs until the newest run settles, then report the
#   settle state: exit 0 + GREEN -> align now (fetch + ff-only) and run anchor verification;
#   exit 2 + RED -> the `rocqwash self-heal` workflow owns it, do not rush, re-poll later;
#   exit 3 + CAP -> the window is unsettled; escalate or re-arm.
# Interface.  `NETRC=<path> REPO=<org/repo> bash ci-green-watch.sh`; both parameters are
#   environment-supplied (defaults: netrc `$HOME/.netrc`, repo `hy7pc8gfmf-dotcom/rocqwash`);
#   polls the GitHub Actions runs API (`?branch=main&per_page=10`) every 120s for up to 20 rounds;
#   each round prints one of `GREEN <sha7>` / `RED <sha7>` / `RUNNING <sha7>` / `EMPTY` / `ERR <detail>`.
# Dependencies.  `curl` with a netrc credential file (`--netrc-file`), `python` (stdlib `json`),
#   `seq`, `date`, `sleep`; bash 3.2-compatible.
# Evidence.  The settle judgment considers only runs of the newest `head_sha` and requires every one
#   of them `completed` (GREEN additionally requires `conclusion == success`); the `rocqwash self-heal`
#   workflow is excluded by name before the judgment.
# Exit-codes.  0 = newest run settled passing (align now); 2 = newest run settled failing (the
#   self-heal line owns it, re-poll later); 3 = round cap reached without a settle.
N="${NETRC:-$HOME/.netrc}"
REPO="${REPO:-hy7pc8gfmf-dotcom/rocqwash}"
for i in $(seq 1 20); do
  curl -s --netrc-file "$N" "https://api.github.com/repos/$REPO/actions/runs?branch=main&per_page=10" | python -c "
import sys, json
try:
    d = json.load(sys.stdin)
    runs = [r for r in d.get('workflow_runs', []) if r['name'] != 'rocqwash self-heal']
    if not runs:
        print('EMPTY'); raise SystemExit
    newest = runs[0]['head_sha']
    states = [(r['status'], r['conclusion']) for r in runs if r['head_sha'] == newest]
    if all(s == 'completed' and c == 'success' for s, c in states):
        print('GREEN', newest[:7])
    elif all(s == 'completed' for s, c in states):
        print('RED', newest[:7])
    else:
        print('RUNNING', newest[:7])
except Exception as e:
    print('ERR', e)
" > .ci-state.$$
  OUT=$(cat .ci-state.$$); rm -f .ci-state.$$
  echo "[$(date '+%H:%M:%S')] $OUT"
  case "$OUT" in
    GREEN*) exit 0 ;;
    RED*)   exit 2 ;;
  esac
  sleep 120
done
echo "CAP-reached (unsettled)"; exit 3
