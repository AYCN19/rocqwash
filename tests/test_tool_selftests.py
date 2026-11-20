#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tool_selftests.py: tools/ selftest meta enumerator hookup (tests/).

Purpose.  The meta-verification layer for the tools/ selftest face: enumerate
  every tool under tools/*.py (helper modules whose file name starts with `_`
  are excluded) and require each to hold a declared --selftest face (the
  quoted flag literal in source) exiting rc=0, or a registered in-file
  exemption marker "# selftest-exempt: <basis>" (basis non-empty).  A red,
  missing, or undeclared selftest fails the meta test and lists the names,
  so any self-proof absence stays visible in every suite run on both CI faces.

Interface.  python3 tests/test_tool_selftests.py [--repo DIR] [--timeout N]
  [--selftest]; suite entry via run_tests.sh t_tool_selftests.  --repo
  defaults to the repository root (the parent of tests/); --timeout is the
  per-attempt cap in seconds (default 120); one cap overrun grants one
  retry; an exempted tool never runs; --selftest runs the vector face.

Dependencies.  Python 3 standard library only; one subprocess per declared
  face with python -B (an overrunning run is started once more); zero
  network; zero writes (temp fixtures only; vector stubs under tempfile).

Evidence.  One line per tool: PASS, SKIP (rc=111, the suite's standing
  environment-absent code, with the tool's own reason), EXEMPT with the
  registered basis, or FAIL with class and detail; plus a bounded excerpt,
  a FAIL list, and a SUMMARY line; the universe derives from the tools/
  directory at run time; two consecutive overruns print the standing
  timeout FAIL line; --selftest prints [SELFTEST] check lines.

Exit-codes.  0 all green/skipped/exempted (registered basis); 1 any FAIL
  (names listed); 2 usage error; --selftest: 0 green, 1 any check red.
"""

import argparse
import contextlib
import io
import os
import re
import subprocess
import sys
import tempfile

# The registered exemption marker: one line, "# selftest-exempt: <basis>",
# basis non-empty (leading indentation tolerated, the shape after "#" is
# literal).
EXEMPT_RE = re.compile(r"^\s*# selftest-exempt: (\S.*)$")

# A quoted "--selftest" literal in the source (an argparse flag name or a
# pre-argparse argv membership form) declares the face.  The declaration is
# judged statically from the file text: a tool without the literal has no
# face to run, and per the contract it must then hold a registered
# exemption.
QUOTED_SELFTEST_RE = re.compile(r"""["']--selftest["']""")

# The suite's standing environment-absent yield code (run_tests.sh exit
# contract: a case exiting 111 = SKIP, not red).  A tool selftest that
# declares 111 reports its own loud reason; the meta layer carries it as a
# SKIP line, visible and excluded from the FAIL list.
SKIP_RC = 111

# One granted retry on a cap overrun: a timed-out run is started once more,
# and only a second consecutive overrun is judged a timeout, so a single
# overrun under machine load does not decide the outcome.
MAX_TIMEOUT_ATTEMPTS = 2

DEFAULT_TIMEOUT = 120
EXCERPT_LINES = 3
EXCERPT_WIDTH = 160

# The vector face (--selftest): its own small cap and stub sleep, so a real
# cap overrun is exercised without inflating the runtime; the stub sleep
# must stay above the cap for the overrun to be reproducible.
VECTOR_CAP = 2
VECTOR_SLEEP = 30


def tool_universe(tools_dir):
    """The enumerated universe: tools/*.py sorted, leading-`_` names excluded."""
    names = sorted(fn for fn in os.listdir(tools_dir)
                   if fn.endswith(".py") and not fn.startswith("_")
                   and os.path.isfile(os.path.join(tools_dir, fn)))
    return names


def read_text(path):
    """Read one tool file as utf-8 text (strict); errors propagate."""
    with io.open(path, "r", encoding="utf-8", errors="strict") as fh:
        return fh.read()


def exempt_basis(text):
    """The registered exemption basis (first marker line wins), or None.

    A marker registers only when the basis after the colon is non-empty;
    an exemption without a basis is not a registration.
    """
    for line in text.splitlines():
        m = EXEMPT_RE.match(line)
        if m:
            return m.group(1)
    return None


def run_selftest(path, timeout):
    """One declared --selftest face, with one retry on a cap overrun.

    Runs the face with python -B (the suite convention) up to
    MAX_TIMEOUT_ATTEMPTS times: a run that overruns the cap is started
    once more, and only a second consecutive overrun yields rc None.  Any
    completed run decides the outcome on its own (a red or skipped rc is
    never retried).  Returns (rc, excerpt): rc is the child exit code, or
    None when every attempt overran the cap; the excerpt is the first
    EXCERPT_LINES merged stdout/stderr lines of the deciding run, each
    clipped, decode errors replaced.
    """
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "-B", path, "--selftest"]
    for _attempt in range(MAX_TIMEOUT_ATTEMPTS):
        try:
            pr = subprocess.run(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            continue
        out = pr.stdout.decode("utf-8", errors="replace")
        lines = [ln[:EXCERPT_WIDTH] for ln in out.splitlines()[:EXCERPT_LINES]]
        return pr.returncode, " | ".join(lines)
    return None, ""


def _stub_body(marker, sleep_always):
    """A generated stub fixture script: counts its starts, sleeps on demand.

    Each start appends to the marker file (the direct evidence that exactly
    one retry was granted) and then sleeps past the vector cap; with
    sleep_always cleared it sleeps on its first start only, so the second
    start (the granted retry) returns immediately.
    """
    lines = [
        "import os",
        "import sys",
        "import time",
        "",
        "marker = %r" % (marker,),
        'if "--selftest" in sys.argv:',
        "    seen = 0",
        "    if os.path.exists(marker):",
        "        with open(marker) as fh:",
        '            seen = int(fh.read().strip() or "0")',
        '    with open(marker, "w") as fh:',
        "        fh.write(str(seen + 1))",
    ]
    if sleep_always:
        lines.append("    time.sleep(%d)" % (VECTOR_SLEEP,))
    else:
        lines.append("    if seen == 0:")
        lines.append("        time.sleep(%d)" % (VECTOR_SLEEP,))
    return "\n".join(lines) + "\n"


FAST_STUB_BODY = (
    "import sys\n"
    "\n"
    'if "--selftest" in sys.argv:\n'
    '    print("fast stub green")\n'
)


def _write_stub(directory, name, body):
    """Write one stub fixture into the vector directory and return its path."""
    path = os.path.join(directory, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return path


def _marker_count(marker):
    """The number of starts a stub recorded (0 when the marker is absent)."""
    if not os.path.exists(marker):
        return 0
    with io.open(marker, "r", encoding="utf-8") as fh:
        text = fh.read().strip()
    return int(text) if text else 0


def selftest_vectors():
    """The meta layer's own vector face: retry semantics over slow stubs.

    Three vector groups, each in its own tempfile directory (offline, zero
    repository writes):

    1. retry-once: a stub over the cap on its first start only comes back
       rc=0 through the single granted retry, and its marker shows exactly
       two starts (no further retry was spent).
    2. two consecutive overruns: a stub over the cap on both starts comes
       back rc=None after exactly two starts, so a genuinely hung face
       keeps failing.
    3. output contract: the enumeration over a synthetic repository exits
       1 and prints the standing timeout FAIL line for the double-overrun
       stub, and prints the standing PASS line for a fast stub.

    Prints one [SELFTEST] line per check plus a [SELFTEST-SUMMARY] line;
    returns 0 all green, 1 any check red.
    """
    checks = []

    with tempfile.TemporaryDirectory(prefix="t_tool_selftests_retry_") as tmp:
        marker = os.path.join(tmp, "attempts.txt")
        stub = _write_stub(tmp, "slow_once_stub.py",
                           _stub_body(marker, sleep_always=False))
        rc, _ = run_selftest(stub, VECTOR_CAP)
        checks.append(("retry-once lands rc=0", rc == 0))
        checks.append(("retry-once spends exactly two starts",
                       _marker_count(marker) == 2))

    with tempfile.TemporaryDirectory(prefix="t_tool_selftests_hang_") as tmp:
        marker = os.path.join(tmp, "attempts.txt")
        stub = _write_stub(tmp, "slow_always_stub.py",
                           _stub_body(marker, sleep_always=True))
        rc, _ = run_selftest(stub, VECTOR_CAP)
        checks.append(("two consecutive overruns land rc=None", rc is None))
        checks.append(("two overruns spend exactly two starts",
                       _marker_count(marker) == 2))

    with tempfile.TemporaryDirectory(prefix="t_tool_selftests_words_") as tmp:
        tools = os.path.join(tmp, "tools")
        os.mkdir(tools)
        _write_stub(tools, "slow_stub.py",
                    _stub_body(os.path.join(tmp, "attempts.txt"), True))
        _write_stub(tools, "fast_stub.py", FAST_STUB_BODY)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(["--repo", tmp, "--timeout", str(VECTOR_CAP)])
        out = buf.getvalue()
        checks.append(("enumeration exits 1 on the double-overrun tool",
                       code == 1))
        checks.append(("timeout FAIL wording stays",
                       ("[FAIL] tools/slow_stub.py timeout: exceeded %ds"
                        % VECTOR_CAP) in out))
        checks.append(("fast tool keeps the standing PASS line",
                       "[PASS] tools/fast_stub.py" in out))

    bad = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print("[SELFTEST] %s: %s" % (name, "PASS" if ok else "FAIL"))
    print("[SELFTEST-SUMMARY] pass=%d fail=%d"
          % (len(checks) - len(bad), len(bad)))
    return 1 if bad else 0


def main(argv=None):
    """Run the enumeration, or the --selftest vector face; return 0/1/2."""
    ap = argparse.ArgumentParser(
        description="tools/ selftest meta enumerator: every tool green on"
                    " --selftest or exempted with a registered basis")
    ap.add_argument("--repo", default=None,
                    help="repository root (default: the parent of tests/)")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help="per-attempt subprocess cap in seconds (default %d)"
                         % DEFAULT_TIMEOUT)
    ap.add_argument("--selftest", action="store_true",
                    help="run this meta layer's own vector face (retry"
                         " semantics over tempfile slow stubs) instead of"
                         " the enumeration")
    args = ap.parse_args(argv)
    if args.timeout <= 0:
        ap.error("--timeout must be a positive number of seconds")
    if args.selftest:
        return selftest_vectors()
    repo = args.repo or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tools_dir = os.path.join(repo, "tools")
    if not os.path.isdir(tools_dir):
        print("META-ENUMERATOR-ERROR: no tools/ directory under %s" % repo)
        return 2
    names = tool_universe(tools_dir)
    if not names:
        print("META-ENUMERATOR-ERROR: no tools/*.py found under %s" % tools_dir)
        return 2
    fails = []
    passed = skipped = exempted = failed = 0
    print("[META] universe=%d tools, per-tool cap %ds (failures are re-listed"
          " at the end; the per-tool log below is alphabetical)" % (len(names), args.timeout))
    for name in names:
        rel = "tools/" + name
        path = os.path.join(tools_dir, name)
        try:
            text = read_text(path)
        except (OSError, UnicodeDecodeError) as e:
            failed += 1
            fails.append(rel)
            print("[FAIL] %s unreadable: %s" % (rel, e))
            continue
        if not QUOTED_SELFTEST_RE.search(text):
            # No declared face: the contract requires a registered exemption.
            # Judged statically from the file text; the tool is not invoked.
            basis = exempt_basis(text)
            if basis is not None:
                exempted += 1
                print("[EXEMPT] %s basis=%s" % (rel, basis))
            else:
                failed += 1
                fails.append(rel)
                print("[FAIL] %s missing: no --selftest face declared in"
                      " source and no registered exemption marker" % rel)
            continue
        rc, excerpt = run_selftest(path, args.timeout)
        if rc == 0:
            passed += 1
            print("[PASS] %s" % rel)
            continue
        if rc == SKIP_RC:
            skipped += 1
            print("[SKIP] %s rc=111 (the suite's environment-absent code)%s"
                  % (rel, (" reason: %s" % excerpt) if excerpt else ""))
            continue
        failed += 1
        fails.append(rel)
        if rc is None:
            print("[FAIL] %s timeout: exceeded %ss" % (rel, args.timeout))
        else:
            detail = "red: --selftest exited rc=%s" % rc
            if excerpt:
                detail += " excerpt: %s" % excerpt
            print("[FAIL] %s %s" % (rel, detail))
    print("[SUMMARY] pass=%d skip=%d exempt=%d fail=%d total=%d"
          " universe=tools/*.py (leading-'_' names excluded) timeout=%ss"
          % (passed, skipped, exempted, failed, len(names), args.timeout))
    if fails:
        print("[FAILURES] %d: %s" % (len(fails), ", ".join(fails)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
