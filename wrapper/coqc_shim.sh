#!/bin/bash
# wrapper/coqc_shim.sh — argv adapter from the gate7 probe's --coqc parameter to the local rocq compiler.
# Purpose.  Canonical adapter face for the compiler invocation of the gate7
#   extraction-run gate (upstream script
#   `ConstructiveWorld-Set/scripts/gates/gate7_extract_run.py`, read-only in
#   its own repository, never modified).  gate7 invokes the compiler as
#   `--coqc <coqc args>` (default
#   `DEFAULT_COQC = C:/Rocq-Platform~9.1~2026.01/bin/coqc.exe`, a Windows
#   path absent on this machine) while Rocq 9.1 expects `rocq c <args>`;
#   this file replaces the hand-built one-line shims: it injects the `c`
#   subcommand, passes every argument through verbatim, and carries zero
#   verdicts and zero logic.
# Interface.  Usage: wrapper/coqc_shim.sh <coqc args...>; wired by
#   `wrapper/gate7_probe.sh` as `... gate7_extract_run.py --coqc
#   wrapper/coqc_shim.sh --tree <world> ...`; env knob
#   `GATE7_PROBE_ROCQ` overrides the rocq path (default = the Live
#   toolchain path; probe and shim share the knob).
# Dependencies.  bash 3.2-compatible; the rocq binary named by
#   `GATE7_PROBE_ROCQ` or the default path; gate7 calls this shim per
#   module as a subprocess, so no guard may be nested here: a nested
#   guard would contend with the outer probe's guard for the same registry
#   and deadlock; the outer `wrapper/gate7_probe.sh` guard wraps the
#   python process tree and owns thermal control.
# Evidence.  tests/test_gate7_wrapper.py judges 1/3/4: `bash -n` syntax; the
#   argv contract byte-exact (with `GATE7_PROBE_ROCQ=/bin/echo`, stdout is
#   `c A B --x` plus a newline); fail-loud rc 9 on a missing rocq target.
# Exit-codes.  9 = rocq binary missing or not executable (fail-loud, nothing
#   simulated; rocqwash CLI convention "missing file = 9"; CONTRIBUTING §0
#   honesty rules); otherwise the rocq exit code itself (exec pass-through).
set -u

ROCQ_BIN="${GATE7_PROBE_ROCQ:-/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live/bin/rocq}"

if [ ! -x "$ROCQ_BIN" ]; then
  echo "wrapper/coqc_shim.sh: rocq 缺失 missing: $ROCQ_BIN" >&2
  echo "  (fail-loud：不模拟编译任何行为 — shim simulates nothing; 可用 GATE7_PROBE_ROCQ=<bin> 覆写)" >&2
  exit 9
fi

exec "$ROCQ_BIN" c "$@"
