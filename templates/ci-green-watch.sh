#!/bin/bash
# ci-green-watch.sh — CI-green sentinel (alignment law trigger).
# Polls the repo's main-branch CI until the newest run settles:
#   exit 0 + GREEN  -> align now (fetch + ff-only) and run anchor verification
#   exit 2 + RED    -> self-heal line is on it; do not rush, re-poll later
#   exit 3 + CAP    -> window unsettled; escalate or re-arm
# Usage: NETRC=<path> REPO=<org/repo> bash ci-green-watch.sh
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
