#!/usr/bin/env python3
"""Test segment for the E4 i18n pipeline stub (RQW12 seed, 2026-11-14).

Named assertion (seed ask): `pipeline_stub.py --selftest` exits 0 and
prints a STUB marker.

Merge target: tests/t_engines_seeds.py (seat 5 merges this segment; keep
the function name `test_i18n_pipeline_stub_selftest` stable and keep the
`stub_path` parameter so the merged suite can repoint it at the landed
seeds/i18n/pipeline_stub.py). Standalone run:

    python -I test_snippet.py

Environment face: pure stdlib, zero network, zero writes; the only child
process it spawns is the stub itself under -I (isolated mode).
"""

import subprocess
import sys
from pathlib import Path

SELFTEST_TIMEOUT_S = 60


def _default_stub_path():
    """Sibling stub next to this snippet in seeds/i18n/ (staged or landed)."""
    return Path(__file__).resolve().parent / "pipeline_stub.py"


def test_i18n_pipeline_stub_selftest(stub_path=None):
    """Assert: stub --selftest exits rc=0 and prints a STUB marker.

    Returns a small evidence dict (rc + first stdout lines) so the merged
    suite can ledger the run; raises AssertionError on any failure.
    """
    path = Path(stub_path) if stub_path is not None else _default_stub_path()
    assert path.is_file(), "stub missing: %s" % path
    proc = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", str(path), "--selftest"],
        capture_output=True,
        text=True,
        timeout=SELFTEST_TIMEOUT_S,
    )
    assert proc.returncode == 0, (
        "stub --selftest rc=%d (expected 0); stderr head: %r"
        % (proc.returncode, proc.stderr[:200])
    )
    assert "STUB" in proc.stdout, (
        "no STUB marker in --selftest stdout; head: %r" % proc.stdout[:200]
    )
    return {
        "rc": proc.returncode,
        "stdout_head": proc.stdout.splitlines()[:4],
        "stub_path": str(path),
    }


def main():
    """Standalone runner: run the segment, print PASS evidence, exit code."""
    evidence = test_i18n_pipeline_stub_selftest()
    sys.stdout.write(
        "PASS test_i18n_pipeline_stub_selftest rc=%s stub=%s\n"
        % (evidence["rc"], evidence["stub_path"])
    )
    for line in evidence["stdout_head"]:
        sys.stdout.write("  | %s\n" % line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
