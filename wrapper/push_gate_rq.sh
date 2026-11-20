#!/bin/bash
# wrapper/push_gate_rq.sh — repository-anchored adapter layer for certify/push_gate.py.
# Purpose.  certify/push_gate.py (in-service component, never edited by this layer) defaults
#   its window subcommand's `--repo` to "." (`default="."` at certify/push_gate.py:585), so a
#   run from outside the repository fails the git determination. This layer resolves the
#   repository root from its own script location (one directory up) and injects
#   `--repo <REPO>` and `--suite <REPO>/tests/run_tests.sh` for window; no window or manifest
#   logic is copied or reimplemented; parsing authority stays with certify/push_gate.py, and
#   exit codes pass through 1:1.
# Interface.  window [--branch B] [--runs-json f | --ci-capped-min N] [--freeze-manifest m.json]
#   [--json out] | union-freeze --world name=path --out union.json | union-check --manifest
#   union.json | --selftest | --show | -h | --help.  Contract: window receives `--repo` and
#   `--suite` injected before the user arguments, and argparse keeps the last value, so an
#   explicit user `--repo`/`--suite` still overrides (returning to cwd-sensitive semantics);
#   union-freeze, union-check, --selftest, -h and --help pass through with zero injection;
#   with no arguments the wrapper exits 2 and never defaults to window (window performs
#   network access through ls-remote/fetch, so the caller initiates a window check
#   explicitly); `--show` prints the post-injection argv and the repository anchor
#   (zero network, zero execution).
# Dependencies.  python3 (override through the PYTHON3 environment variable);
#   certify/push_gate.py at the repository root's certify/ directory; bash `set -u`.
# Evidence.  Zero-write layer: no writes to the repository tree or the sandbox, diagnostics
#   on stdout only; the component runs with -B (no `__pycache__`, so the certify/ tree
#   reconciliation stays stable); injection correctness is machine-checked by `--show`;
#   fail-loud existence checks (script location, repository root, component file) precede
#   every invocation; this layer itself performs no compilation and no network access.
# Exit-codes.  9 = fail-loud (certify/push_gate.py missing or repository root resolution
#   failed); 2 = usage error (no arguments or unknown subcommand); 0 = `--show` diagnostic
#   completed; all other codes pass through unchanged from certify/push_gate.py
#   (window: 0 = OPEN, 1 = CLOSED including NOT-RUN; see the component's own exit-code table).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)" || { echo "FAIL-LOUD: 脚本位置解析失败" >&2; exit 9; }
REPO="$(cd "$HERE/.." && pwd)" || { echo "FAIL-LOUD: 仓库根解析失败: $HERE/.." >&2; exit 9; }
PY="${PYTHON3:-python3}"
TARGET="$REPO/certify/push_gate.py"
[ -f "$TARGET" ] || { echo "FAIL-LOUD: 正本缺失: $TARGET" >&2; exit 9; }

if [ $# -eq 0 ]; then
  echo "FAIL-LOUD: 无参调用禁绝（防 surprise 网络·见头注注入契约 3）" >&2
  echo "用法: $0 window [选项...] | union-freeze ... | union-check ... | --selftest | --show" >&2
  exit 2
fi
case "$1" in
  --show)
    echo "wrapper/push_gate_rq.sh --show（诊断·零网络零执行）"
    echo "  REPO    = $REPO"
    echo "  suite   = $REPO/tests/run_tests.sh"
    echo "  argv    = $PY -B $TARGET window --repo $REPO --suite $REPO/tests/run_tests.sh <用户参...>"
    echo "  passthru= union-freeze / union-check / --selftest（零注入直通）"
    exit 0 ;;
  window)
    shift
    exec "$PY" -B "$TARGET" window --repo "$REPO" --suite "$REPO/tests/run_tests.sh" "$@" ;;
  union-freeze|union-check|--selftest|-h|--help)
    exec "$PY" -B "$TARGET" "$@" ;;
  *)
    echo "FAIL-LOUD: 未知子命令: $1（合法: window | union-freeze | union-check | --selftest | --show）" >&2
    exit 2 ;;
esac
