#!/bin/bash
# sentinel_supervisor.sh - supervisor shell: auto-restart wrapper keeping a long-running sentinel loop alive (canonical deployment form).
#
# Purpose.  Keep `tools/cw_sentinel.py --loop` alive across crashes: run it as
#   a child, restart it with capped exponential backoff after any nonzero
#   exit, and rely on the on-disk state file for lossless continuation. It
#   covers the crash shapes no in-process retry layer reaches (emit/rename
#   faults, OOM kills, machine restarts). State is never rebuilt silently: the
#   seen ledger is idempotent and duplication is preferred over loss.
#
# Interface.  No flags of its own; configuration is environment-only. Deploy:
#     SENTINEL_WORK=/path/to/_log/sentinel \
#     SENTINEL_WATCH_REPOS="ORG/REPO-A ORG/REPO-B" \
#     [SENTINEL_GUARD=/path/to/cpu_guard.sh SENTINEL_GUARD_ARGS="-MaxWaitSec 120"] \
#     nohup bash examples/sentinel_supervisor.sh >/dev/null 2>&1 &
#   Run a `--once` preflight of the sentinel first; the withdrawal hook `supervisor_withdraw_hook` is empty by default.
#
# Dependencies.  bash 3.2 (a full-width byte right after a bare $VAR is
#   swallowed into the variable name; variables are always braced ${VAR});
#   python3; `tools/cw_sentinel.py`; writable SENTINEL_WORK; optional guard
#   script run as `bash $SENTINEL_GUARD $SENTINEL_GUARD_ARGS -- <command>`.
#
# Evidence.  Selftest vector 15 of `tools/cw_sentinel.py` statically asserts
#   this script: bash -n parse, structural tokens (restart cap, backoff, state
#   continuation, hook `return 0`, three state-file names, rc triage), no
#   hard-coded user-home paths, and the ${} bracing law above.
#
# Exit-codes.  0 = normal withdrawal (child rc=0 after its round budget, or
#   the withdrawal hook fired); 1 = restart budget exhausted; 2 = usage error
#   (missing required configuration; child rc=2, restart cannot help); 9 = environment unreachable (repo root, sentinel, or work dir missing).

set -u

# ---- configuration (environment variables only; required items fail-loud; no hard-coded absolute paths) ----
SENTINEL_REPO_ROOT="${SENTINEL_REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SENTINEL_WORK="${SENTINEL_WORK:-}"                  # directory holding the three state files (required)
SENTINEL_WATCH_REPOS="${SENTINEL_WATCH_REPOS:-}"    # space-separated repos (required; at least one signal source)
SENTINEL_BRANCH="${SENTINEL_BRANCH:-}"              # optional; applied to every watched repo (repo first, then branch)
SENTINEL_INTERVAL="${SENTINEL_INTERVAL:-600}"       # round interval seconds (600)
SENTINEL_MAX_ROUNDS="${SENTINEL_MAX_ROUNDS:-60}"    # round cap (60; 0 = unlimited)
SENTINEL_GUARD="${SENTINEL_GUARD:-}"                # empty = run the child directly (pure logic, zero compile); set to a wrapper such as cpu_guard.sh for thermal-guard wrapping
SENTINEL_GUARD_ARGS="${SENTINEL_GUARD_ARGS:--MaxWaitSec 120}"   # example form
SUPERVISOR_MAX_RESTARTS="${SUPERVISOR_MAX_RESTARTS:-40}"        # restart cap (40)
SUPERVISOR_BACKOFF_BASE="${SUPERVISOR_BACKOFF_BASE:-60}"        # backoff base seconds (60)
SUPERVISOR_BACKOFF_MAX="${SUPERVISOR_BACKOFF_MAX:-600}"         # backoff cap seconds
SENTINEL_EXTRA_ARGS="${SENTINEL_EXTRA_ARGS:-}"                  # extra flags passed through (e.g. --emit-max-bytes 104857600)

# ---- usage fail-loud (supervisor itself: 2 = usage error, 9 = environment unreachable) ----
[ -n "$SENTINEL_WORK" ] || { echo "[supervisor] FAIL-LOUD 2: SENTINEL_WORK is required (directory for the three state files)" >&2; exit 2; }
[ -n "$SENTINEL_WATCH_REPOS" ] || { echo "[supervisor] FAIL-LOUD 2: SENTINEL_WATCH_REPOS is required (at least one signal source)" >&2; exit 2; }
[ -d "$SENTINEL_REPO_ROOT" ] || { echo "[supervisor] FAIL-LOUD 9: SENTINEL_REPO_ROOT directory missing: $SENTINEL_REPO_ROOT" >&2; exit 9; }
[ -f "$SENTINEL_REPO_ROOT/tools/cw_sentinel.py" ] || { echo "[supervisor] FAIL-LOUD 9: sentinel binary missing: $SENTINEL_REPO_ROOT/tools/cw_sentinel.py" >&2; exit 9; }
[ -d "$SENTINEL_WORK" ] || { echo "[supervisor] FAIL-LOUD 9: SENTINEL_WORK directory missing (create it before mounting): $SENTINEL_WORK" >&2; exit 9; }
cd "$SENTINEL_REPO_ROOT" || { echo "[supervisor] FAIL-LOUD 9: cd failed: $SENTINEL_REPO_ROOT" >&2; exit 9; }

# ---- scheduled withdrawal hook (empty; deployers fill it as needed) ----
# Hook contract: evaluated once before each spawn. Withdrawing = exit 0 inside
# the function (the whole shell exits; the three state files stay consumable);
# not withdrawing = return 0. Withdrawal granularity = spawn boundary (a
# running child is never interrupted; to stop a running child, kill it
# manually). Example form (withdraw at 09:00: no new rounds inside the
# 09:00-12:00 window):
#   supervisor_withdraw_hook() { h=$(date +%H); [ "$h" -ge 9 ] && [ "$h" -lt 12 ] && exit 0; return 0; }
supervisor_withdraw_hook() {
  return 0   # empty (default: never withdraw; withdrawal happens only via --max-rounds self-stop or a manual kill)
}

# ---- state continuation note (loud declaration of lossless continuation across crash restarts; once per shell) ----
echo "[supervisor] state continuation: --state-file in place (seen ledger idempotent across restarts, zero-loss continuation; prefer duplicate events over loss; never rebuild state silently)"
echo "[supervisor] work=$SENTINEL_WORK repos=[$SENTINEL_WATCH_REPOS] interval=${SENTINEL_INTERVAL}s max_rounds=$SENTINEL_MAX_ROUNDS restarts<=$SUPERVISOR_MAX_RESTARTS backoff=${SUPERVISOR_BACKOFF_BASE}s*2 cap=${SUPERVISOR_BACKOFF_MAX}s"

backoff=$SUPERVISOR_BACKOFF_BASE
attempt=0
while :; do
  supervisor_withdraw_hook
  attempt=$((attempt + 1))
  if [ "$attempt" -gt "$SUPERVISOR_MAX_RESTARTS" ]; then
    echo "[supervisor] restart budget exhausted (cap ${SUPERVISOR_MAX_RESTARTS})" >&2
    exit 1
  fi
  echo "[supervisor restart $attempt] $(date -u +%H:%M:%SZ)"
  cmd=(python3 -B tools/cw_sentinel.py --loop \
    --interval "$SENTINEL_INTERVAL" --max-rounds "$SENTINEL_MAX_ROUNDS")
  for r in $SENTINEL_WATCH_REPOS; do
    cmd+=(--watch-repo "$r")
    [ -n "$SENTINEL_BRANCH" ] && cmd+=(--branch "$SENTINEL_BRANCH")
  done
  cmd+=(--state-file "$SENTINEL_WORK/state.json" \
    --emit "$SENTINEL_WORK/events.jsonl" --json "$SENTINEL_WORK/report.json")
  [ -n "$SENTINEL_EXTRA_ARGS" ] && cmd+=($SENTINEL_EXTRA_ARGS)
  if [ -n "$SENTINEL_GUARD" ]; then
    bash "$SENTINEL_GUARD" $SENTINEL_GUARD_ARGS -- "${cmd[@]}"
  else
    "${cmd[@]}"
  fi
  RC=$?
  echo "[supervisor] exit=$RC at $(date -u +%H:%M:%SZ)"
  if [ "$RC" -eq 0 ]; then
    echo "[supervisor] child finished its round budget (--max-rounds exhausted, self-stopped) = normal withdrawal"
    exit 0
  fi
  if [ "$RC" -eq 2 ]; then
    echo "[supervisor] rc=2 usage error: restart cannot help, fail-loud exit (restart budget not consumed)" >&2
    exit 2
  fi
  # rc=9 (signal source unreachable) and every other rc (including
  # transport-layer crashes, rc=1, the IncompleteRead shape) go to the
  # backoff-restart path and count against the restart cap
  # (note: with bash 3.2, a full-width byte right after a bare $VAR is
  # swallowed into the variable name; always brace variables ${VAR})
  echo "[supervisor] backoff ${backoff}s before restart (rc=${RC})"
  sleep "$backoff"
  backoff=$((backoff * 2))
  if [ "$backoff" -gt "$SUPERVISOR_BACKOFF_MAX" ]; then
    backoff=$SUPERVISOR_BACKOFF_MAX
  fi
done
