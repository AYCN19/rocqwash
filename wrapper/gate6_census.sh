#!/bin/bash
# wrapper/gate6_census.sh — canonical gate6 statement-face Prop survey launcher
# Purpose.  Canonical in-repo launcher for the gate6 statement-face Prop survey gate (whitepaper
#   redline II, v2.4+; ch1 statement face, ch2 field-section face, ch3 global hypothesis face;
#   semantic final judgment stays with the gate7 extraction run).  Pure static lexical scan:
#   zero network, zero compilation, read-only tree scan.  No criteria and no logic here:
#   verdicts and baselines stay with the upstream script alone, of which this file is the only
#   in-repo entry point (no dual-source drift).
# Interface.  用法 Usage: bash wrapper/gate6_census.sh --tree <.v tree dir>
#   [--json <out>] [--text] [--gate --baseline <B>] [--baseline-out <O>]
#   [--gate-script <gate6.py>] [--dry-run] [-- <gate6 native args, verbatim>]
#   Env knobs: GATE6_CENSUS_SCRIPT (upstream gate6 path), GATE6_CENSUS_REG (guard registry
#   dir; default /tmp/cw_reg_gate6_census; an agent may set its own, e.g. /tmp/cw_reg_<name>,
#   so two lanes never queue on it), GATE6_CENSUS_FRONT/-MID/-MAXWAIT (guard tiers; default
#   0/1/600).  The gate6 process runs as python3 -B (no __pycache__ into the read-only
#   upstream repository) under built-in guard wiring; callers must not add an outer guard
#   (same-registry deadlock).  Args map 1:1 to the upstream argparse (--tree/--json/--text/
#   --gate/--baseline/--baseline-out; gate6_statement_census.py:158-163); no business
#   defaults here — report-only vs --gate is the caller's explicit choice.  Writes go only
#   to user-given --json/--baseline-out paths (CONTRIBUTING §3.5); otherwise stdout only.
# Dependencies.  bash; python3 on PATH; wrapper/guard.sh (pass-through layer of the frozen
#   tools/cpu_guard.sh; md5-equal 9c5392d6… to the local ConstructiveWorld/cpu_guard.sh);
#   the upstream gate6 script, read-only.
# Evidence.  tests/test_gate6_born_wrapper.py judges 1-9 subprocess-cover this face: bash -n
#   syntax; -h usage face; rc 2 usage errors; rc 9 missing inputs; zero-write --dry-run form.
# Exit-codes.  0 = census report / gate passing (or after --dry-run output); 2 = this layer's
#   usage error (unknown argument, missing --tree); 9 = missing file (upstream gate6 script,
#   --tree dir, python3 — fail-loud, nothing simulated); otherwise the guard pass-through =
#   the gate6 exit code (1 = gate failing: growth/new-file regression, per R15 the stock is
#   frozen and only growth is penalized; 2 = upstream usage-IO error incl. missing tree).
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GUARD="$ROOT/wrapper/guard.sh"

GATE6_SCRIPT="${GATE6_CENSUS_SCRIPT:-/Users/apple/Desktop/ConstructiveWorld-Set/scripts/gates/gate6_statement_census.py}"
REG="${GATE6_CENSUS_REG:-/tmp/cw_reg_gate6_census}"
FRONT="${GATE6_CENSUS_FRONT:-0}"
MID="${GATE6_CENSUS_MID:-1}"
MAXWAIT="${GATE6_CENSUS_MAXWAIT:-600}"

usage() {
  sed -n '2,44p' "$0" | grep -E '^#' | sed 's/^# \{0,1\}//'
}

TREE=""; JSONOUT=""; TEXT=0; GATE=0; BASELINE=""; BASEOUT=""; GATE6OVR=""; DRYRUN=0
EXTRA=()
AFTER="--args"
while [ $# -gt 0 ]; do
  case "$1" in
    --tree) TREE="${2-}"; shift 2 ;;
    --json) JSONOUT="${2-}"; shift 2 ;;
    --text) TEXT=1; shift ;;
    --gate) GATE=1; shift ;;
    --baseline) BASELINE="${2-}"; shift 2 ;;
    --baseline-out) BASEOUT="${2-}"; shift 2 ;;
    --gate-script) GATE6OVR="${2-}"; shift 2 ;;
    --dry-run) DRYRUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) AFTER="--extra"; shift; EXTRA=("$@"); break ;;
    *) echo "wrapper/gate6_census.sh: 未知形参 unknown arg: $1" >&2
       echo "  (-h|--help 看用法; gate6 原生形参请置于 -- 之后逐字透传)" >&2; exit 2 ;;
  esac
done
[ -n "$GATE6OVR" ] && GATE6_SCRIPT="$GATE6OVR"

fail9() { echo "wrapper/gate6_census.sh: $1" >&2; echo "  (fail-loud exit 9：文件缺失不模拟任何行为)" >&2; exit 9; }

# --- usage/file-face fail-loud checks (before any guard behavior) -----------
[ -n "$TREE" ] || { echo "wrapper/gate6_census.sh: 缺 --tree <.v 树目录>" >&2; exit 2; }
[ -d "$TREE" ] || fail9 "--tree 目录缺失: $TREE"
[ -f "$GATE6_SCRIPT" ] || fail9 "gate6 正本缺失: $GATE6_SCRIPT (可用 GATE6_CENSUS_SCRIPT/--gate-script 覆写)"
[ -x "$GUARD" ] || fail9 "guard 直通层缺失: $GUARD"
command -v python3 >/dev/null 2>&1 || fail9 "python3 不在 PATH"
if [ "$GATE" = "1" ] && [ -z "$BASELINE" ]; then
  echo "wrapper/gate6_census.sh: --gate 需配 --baseline（正本 GATE6-USAGE 同律·此处前置 fail-loud）" >&2
  exit 2
fi
[ -z "$BASELINE" ] || [ -f "$BASELINE" ] || fail9 "--baseline 文件缺失: $BASELINE"

# -- gate6 argument assembly (zero criterion copying; args 1:1 with the upstream argparse:158-163) ---
CMD=(python3 -B "$GATE6_SCRIPT"
     --tree "$TREE")
[ "$TEXT" = "1" ] && CMD+=(--text)
[ "$GATE" = "1" ] && CMD+=(--gate)
[ -n "$BASELINE" ] && CMD+=(--baseline "$BASELINE")
[ -n "$JSONOUT" ] && CMD+=(--json "$JSONOUT")
[ -n "$BASEOUT" ] && CMD+=(--baseline-out "$BASEOUT")
[ ${#EXTRA[@]} -gt 0 ] && CMD+=("${EXTRA[@]}")

if [ "$DRYRUN" = "1" ]; then
  printf 'GATE6-CENSUS-DRYRUN guard: bash %q -Reg %q -Front %q -Mid %q -MaxWaitSec %q --\n' \
    "$GUARD" "$REG" "$FRONT" "$MID" "$MAXWAIT"
  printf 'GATE6-CENSUS-DRYRUN cmd:'
  printf ' %q' "${CMD[@]}"
  printf '\n'
  exit 0
fi

# -- guard wiring (exit code passes through exec unchanged) ------------------
exec bash "$GUARD" -Reg "$REG" -Front "$FRONT" -Mid "$MID" -MaxWaitSec "$MAXWAIT" -- "${CMD[@]}"
