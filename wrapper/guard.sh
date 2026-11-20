#!/bin/bash
# wrapper/guard.sh — pass-through adapter for the frozen component `tools/cpu_guard.sh`.
# Purpose.  `tools/cpu_guard.sh` is frozen and in service (running agents reference
#   it live) and is never modified.  This layer is a new adapter face: it copies and
#   re-implements no thermal-control or tiered-queue logic; it forwards argv 1:1 to
#   the repository's original `tools/cpu_guard.sh` and passes the exit code through
#   unchanged (contract: `docs/zh/architecture.md` §6 — exit code = the wrapped
#   command's exit code).  Compiles and tests still go through thermal-control
#   wrapping; this layer is only their new entry point, not a second implementation
#   (the original stays unique, this layer carries zero logic — no dual-source drift).
# Interface.  Usage (byte-identical to the original):
#   wrapper/guard.sh [-Front 2] [-Mid 2] [-MaxWaitSec 900] [-Direct]
#                    [-ThrottleFloor 90] [-ThermalMaxWait 3600] [-Reg <dir>] [--] <command...>
#   1. No argument is intercepted or parsed: everything, including `--`, reaches the
#      original verbatim; parsing authority rests entirely with the original.
#   2. No defaults are injected and no `-Reg` is set on the caller's behalf: default
#      behavior is byte-identical to calling `tools/cpu_guard.sh` directly.
#   3. Exit code = the original's exit code = the wrapped command's exit code (`exec`
#      pass-through, no rewriting).
#   4. Fail-loud: exit 9 when the original is missing (the `cli/rocqwash` exit-code
#      table, file missing = 9); no thermal-control or queue behavior is simulated
#      (no spurious pass; CONTRIBUTING §0 honesty laws).
# Dependencies.  bash; the sibling frozen component `tools/cpu_guard.sh` (resolved
#   from the repository root; the sole wrapped target).  Guard layer wired by
#   `wrapper/gate6_census.sh`, `wrapper/gate7_probe.sh`, and `wrapper/born_world.sh`.
# Evidence.  `bash -n wrapper/guard.sh` passes; delegation smoke `wrapper/guard.sh
#   -Direct -- true` reaches the original and exits 0 (the one-shot probe shape
#   `tests/run_tests.sh` runs against the original).
# Exit-codes.  9 = the repository's original `tools/cpu_guard.sh` missing (fail-loud);
#   otherwise pass-through from the original: the wrapped command's own exit code.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GUARD="$ROOT/tools/cpu_guard.sh"

if [ ! -f "$GUARD" ]; then
  echo "wrapper/guard.sh: 本仓正本缺失 frozen original missing: $GUARD" >&2
  echo "  (fail-loud：直通层不模拟温控/队列任何行为 — pass-through layer simulates nothing)" >&2
  exit 9
fi

exec bash "$GUARD" "$@"
