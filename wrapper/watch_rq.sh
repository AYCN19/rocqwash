#!/bin/bash
# wrapper/watch_rq.sh — repository-anchored adapter layer for watch/watch.py.
#
# Purpose.  watch/watch.py (in-service component, never edited by this layer) defaults its
#   push/confirm `--repo` to "." (`default="."` at watch/watch.py:453 and watch/watch.py:464),
#   so a run from outside the repository fails the git determination. This layer resolves the
#   repository root from its own script location (one directory up) and injects `--repo <REPO>`
#   for push/confirm; no logic is copied or reimplemented; parsing authority stays with
#   watch/watch.py, and exit codes pass through 1:1.
# Interface.  push [--remote origin] [--pin-ip IP --url-host HOST] [--mask STR]... [--yes|--dry-run]
#   [-- refspecs...] | confirm --remote origin --branch main --sha <sha> [--reads 2 --gap 2] | ci
#   --runs-json f | ci --repo owner/name --online | --show | --selftest.  Contract: push/confirm
#   get `--repo <REPO>` injected before the user arguments, and argparse keeps the last value,
#   so an explicit user `--repo` still overrides (returning to cwd-sensitive semantics); ci and
#   --selftest pass through with zero injection (ci's `--repo` is owner/name; a repository
#   directory there would break the meaning; the offline `--runs-json` path is supplied by the
#   caller); push never sets `--yes` (dry-run by default; a real push is caller-initiated, then
#   confirm makes N ls-remote reads that all equal `--sha`); `--show` prints the post-injection
#   argv and the repository anchor (zero network, zero execution).
# Dependencies.  python3 (override through the PYTHON3 environment variable); watch/watch.py one
#   directory above this script; bash `set -u`.
# Evidence.  Zero-write layer: stdout diagnostics only; the component runs with -B (no
#   `__pycache__`). Injection correctness is machine-checked by `--show`; `--selftest` passes
#   through to the frozen vector set (suite cases `t_watch` and `t_watch_repo_form`,
#   tests/run_tests.sh); the no-rerun/no-cancel/no-`workflow_dispatch` property holds
#   structurally in watch/watch.py and is not re-implemented here (no second source to drift).
# Exit-codes.  9 = fail-loud (watch/watch.py missing or repository root resolution failed);
#   2 = usage error (no arguments or unknown subcommand); 0 = `--show` ran; all other codes
#   pass through unchanged (push: 0 = dry run, otherwise the git push code; confirm: 0 =
#   confirmed, 1 = reads disagree; ci: 0 = idle, 1 = in flight or unusable evidence).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)" || { echo "FAIL-LOUD: 脚本位置解析失败" >&2; exit 9; }
REPO="$(cd "$HERE/.." && pwd)" || { echo "FAIL-LOUD: 仓库根解析失败: $HERE/.." >&2; exit 9; }
PY="${PYTHON3:-python3}"
TARGET="$REPO/watch/watch.py"
[ -f "$TARGET" ] || { echo "FAIL-LOUD: 正本缺失: $TARGET" >&2; exit 9; }

if [ $# -eq 0 ]; then
  echo "FAIL-LOUD: 无参调用禁绝（ci 需证据源·push 需子命令·见头注注入契约 5）" >&2
  echo "用法: $0 push [选项...] | confirm --remote R --branch B --sha S | ci ... | --selftest | --show" >&2
  exit 2
fi
case "$1" in
  --show)
    echo "wrapper/watch_rq.sh --show（诊断·零网络零执行）"
    echo "  REPO    = $REPO"
    echo "  argv    = $PY -B $TARGET push --repo $REPO <用户参...>"
    echo "            $PY -B $TARGET confirm --repo $REPO <用户参...>"
    echo "  passthru= ci / --selftest（零注入直通·ci 的 --repo 是 owner/name 非目录）"
    exit 0 ;;
  push)
    shift
    exec "$PY" -B "$TARGET" push --repo "$REPO" "$@" ;;
  confirm)
    shift
    exec "$PY" -B "$TARGET" confirm --repo "$REPO" "$@" ;;
  ci|--selftest|-h|--help)
    exec "$PY" -B "$TARGET" "$@" ;;
  *)
    echo "FAIL-LOUD: 未知子命令: $1（合法: push | confirm | ci | --selftest | --show）" >&2
    exit 2 ;;
esac
