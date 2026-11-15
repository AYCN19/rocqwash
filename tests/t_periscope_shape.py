#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_periscope_shape.py — tests/ suite shell for tools/periscope.py.

Purpose.  Hook the periscope sweep tool into the tests/ suite and smoke its
  shape offline: the tool's own frozen vector group (CLI face, config
  schema matrix, the three burned-in behaviors, cap/stop/retry machine,
  read-only pledge, draft-template invariants, dry-run zero-write, NETRED
  per-shot ledger) runs under --selftest and is attested by its frozen
  marker line; this shell re-checks the subprocess faces a suite reader
  cares about.

Interface.  `python3 tests/t_periscope_shape.py` (rostered in
  tests/run_tests.sh as case t_periscope_shape on 20261115, audit finding
  P0-6; the roster count is derived one-way from the CASES block in
  tests/run_tests.sh via doc_lint's second check).  Six checks: --selftest rc=0
  with the `PERISCOPE-SELFTEST PASS` marker; --help rc=0 naming the six
  flags of the CLI face; exit-code convention spot checks (--bogus=2, a
  bare run refused with rc=2 naming --out, --config on an absent file
  rc=9, a schema-drifted config rc=2); a config-schema pass (a valid
  six-source config dry-runs rc=0); the dry-run draft skeleton carries all
  five judgment-template sections plus the four negative-finding element
  labels; the dry-run writes zero bytes (its --out path never materializes).

Dependencies.  Python 3 stdlib only; the inspected tool is stdlib-only;
  every check runs on temporary fixtures or nonexistent scratch paths;
  nothing in the repository is written; zero network — the --selftest and
  --dry-run faces cannot reach the transport layer by construction, and
  both faces complete on this machine without any curl invocation.

Evidence.  Every check here runs the tool in a subprocess and asserts the
  exit code and the output face on this machine; the fixture vectors are
  attested by the tool's own --selftest marker, never inferred.

Exit-codes.  0 = all six checks pass; 1 = any check red (fail-loud, the
  red check is printed; no silent downgrade).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "periscope.py")
MARK = "PERISCOPE-SELFTEST PASS"
FLAGS = ("--config", "--out", "--rounds", "--netrc", "--dry-run",
         "--selftest")
SECTIONS = ("逐源 digest", "撞车初筛三态", "C1 触发判定", "负发现四要素",
            "排窗建议五条")
ELEMENTS = ("scanned (what was scanned)",
            "not scanned (surfaces outside this sweep)",
            "not an absolute claim",
            "aliased equivalents not exhaustively ruled out")


def run(args):
    """Run the tool in a subprocess (stdout+stderr merged).  `-X utf8`
    pins the stdio encoding: under `-I` the interpreter ignores
    PYTHONIOENCODING, so on a cp936 console the draft skeleton's CJK
    sections would otherwise reach this pipe mojibake'd."""
    p = subprocess.run([sys.executable, "-B", "-I", "-X", "utf8", TOOL]
                       + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       cwd=REPO)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def write_config(tmp, name, mutate=None):
    """Materialize a config file derived from the tool's own default by
    running a --dry-run plan parse... simpler: a minimal valid six-source
    object written here (schema mirror, independent of the tool)."""
    cfg = {
        "schema": "rocqwash-periscope-config/1",
        "sentinel": {"endpoint": "https://api.github.com/rate_limit",
                     "rounds": 10},
        "defaults": {"cap_per_source": 8},
        "deposit_anchors": {"mathlib_pr45912_closed_at":
                            "2026-11-11T22:19:13Z"},
        "sources": [
            {"key": "mathlibpr", "kind": "github_search",
             "url": "https://api.github.com/search/issues?q=zeta",
             "auth": "netrc"},
            {"key": "pr45912", "kind": "github_api",
             "url": "https://api.github.com/repos/o/r/pulls/1",
             "auth": "netrc"},
            {"key": "arxiv-dzeta", "kind": "arxiv",
             "url": "https://export.arxiv.org/api/query?q={WINDOW}",
             "auth": "none", "days_window": 30},
            {"key": "arxiv-quasir", "kind": "arxiv",
             "url": "https://export.arxiv.org/api/query?q={WINDOW}",
             "auth": "none", "days_window": 30},
            {"key": "issues", "kind": "github_issue",
             "url": "https://api.github.com/repos/o/Main/issues/3",
             "auth": "netrc", "comments": {"enabled": True,
                                           "per_page": 30}},
            {"key": "dzzftip", "kind": "github_commits",
             "url": "https://api.github.com/repos/o/DZ/commits?per_page=3",
             "auth": "netrc", "c1_frozen_prefix": "09afbb4"},
        ],
    }
    if mutate is not None:
        mutate(cfg)
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(cfg, handle)
    return path


def main():
    fails = []

    # Check 1: the tool's own frozen vector group attests green.
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("check1 --selftest should be rc=0 with %r (rc=%d)\n%s"
                     % (MARK, rc, out))

    # Check 2: --help is a clean usage face naming the six flags
    # (argparse hyphen-wrap repair, doc_lint precedent).
    rc, out = run(["--help"])
    flat = re.sub(r"-\s*\n\s*", "-", out)
    if rc != 0:
        fails.append("check2 --help should be rc=0 (rc=%d)\n%s" % (rc, out))
    for flag in FLAGS:
        if flag not in flat:
            fails.append("check2 --help should name %s\n%s" % (flag, flat))

    # Check 3: exit-code convention spot checks on scratch paths only.
    rc, _ = run(["--bogus"])
    if rc != 2:
        fails.append("check3 --bogus should exit 2, got %d" % rc)
    rc, out = run([])
    if rc != 2 or "--out" not in out:
        fails.append("check3 a bare run should be refused rc=2 naming "
                     "--out (rc=%d)\n%s" % (rc, out))
    tmp = tempfile.mkdtemp(prefix="t_periscope_shape_")
    try:
        rc, out = run(["--config", os.path.join(tmp, "absent.json"),
                       "--dry-run"])
        if rc != 9:
            fails.append("check3 --config on an absent file should exit 9, "
                         "got %d" % rc)

        def break_schema(cfg):
            cfg["schema"] = "some-other-schema/9"
        bad = write_config(tmp, "bad_schema.json", break_schema)
        rc, out = run(["--config", bad, "--dry-run"])
        if rc != 2:
            fails.append("check3 a schema-drifted config should exit 2, "
                         "got %d\n%s" % (rc, out))

        # Check 4: a valid six-source config dry-runs green.
        good = write_config(tmp, "good.json")
        rc, out = run(["--config", good, "--dry-run"])
        if rc != 0 or "rocqwash-periscope-config/1" not in out:
            fails.append("check4 valid config dry-run should be rc=0 and "
                         "name the schema (rc=%d)\n%s" % (rc, out))

        # Check 5: the dry-run draft skeleton carries the five sections and
        # the four mandatory negative-finding element labels.
        for head in SECTIONS:
            if head not in out:
                fails.append("check5 dry-run skeleton misses section %r"
                             % head)
        for label in ELEMENTS:
            if label not in out:
                fails.append("check5 dry-run skeleton misses the mandatory "
                             "element %r" % label)

        # Check 6: the dry-run writes zero bytes — its --out path never
        # materializes and the scratch root stays empty.
        out_dir = os.path.join(tmp, "out_never")
        rc, out = run(["--config", good, "--out", out_dir, "--dry-run"])
        if rc != 0:
            fails.append("check6 dry-run with --out should be rc=0 "
                         "(rc=%d)\n%s" % (rc, out))
        if os.path.exists(out_dir):
            fails.append("check6 dry-run must not create its --out path")
        residue = [n for n in os.listdir(tmp) if n != "out_never"]
        # only the config files written by this shell itself are expected;
        # the tool must have added nothing beyond them.
        allowed = {"absent.json", "bad_schema.json", "good.json"}
        extra = [n for n in residue
                 if not (n.endswith(".json") and n in allowed)]
        if extra:
            fails.append("check6 dry-run left unexpected files: %r" % extra)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for line in fails:
            sys.stderr.write("T_PERISCOPE_SHAPE FAIL %s\n" % line)
        return 1
    sys.stdout.write("T-PERISCOPE-SHAPE SUITE SHELL PASS (6 checks)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
