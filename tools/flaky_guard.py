#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flaky_guard: order-dependence detection and advisory-roster quarantine.

    Purpose.  Repair class E2-3.  Classifies each red case in a suite log
      by an isolation probe (suite-red plus alone-green = order-dependent;
      red in both contexts = content red that stays visible) and, on
      --apply, moves an order-dependent case into tests/advisory_roster.txt
      so the default suite drops it (loud ADVISORY-OUT line) while the CI
      flaky-watch lane keeps observing it.  Applies are scope-checked
      against tools/repair_scope.py, budget-capped at 2 per class per
      branch, and ledgered (class/target/outcome).  --restore needs
      green-round evidence.  Dry run is the default; --apply is the only
      write face.
    Interface.  --detect --log LOG [--json OUT] [--no-probe] | --probe
      CASE | --move CASE [--apply] | --restore CASE [--apply]
      [--green-rounds N] | --status | --selftest; --repo --roster --ledger
      --suite --py --probe-timeout.  Report schema rocqwash-flaky-detect/1;
      ledger rows rocqwash-repair-ledger/1 (append-only JSONL).
    Dependencies.  Python 3 stdlib only; the probe runs the suite entry
      through bash; repair_scope.py is loaded by path and is mandatory
      (absence is a fail-loud rc 9, never a silent inline fallback).
    Evidence.  --selftest drives a sandbox mini-suite through the full
      arc: baseline red, both verdicts, dry-run zero-write, apply with
      ledger row, idempotent re-apply, three green rounds with
      ADVISORY-OUT, budget and frozen-target refusals, content-red
      refusal, restore both ways, status, scope invariant, CLI codes.
    Exit-codes.  0 accounted (verdicts, plans, refusals are data); 1
      refused (frozen target, budget cap, content-red, not-yet-green) or
      selftest red; 2 usage or malformed input; 9 missing input.
"""
# Extended contract (kept outside the five-field block; budget discipline):
#
# Order-dependence contract.  A case is an order-dependent flake when the
# full-suite context reddens it while an isolated run of the same case is
# green (a predecessor's side effect breaks its assumption).  The reverse
# (green in suite, red alone) and the red-in-both form are content facts:
# the first never reddens the main suite, the second is debt that stays
# visible on every platform (ci.yml doctrine: content-level reds are never
# hidden).  Only the suite-red/alone-green signature is quarantined; every
# other outcome is recorded and left in place.
#
# Advisory roster contract.  tests/advisory_roster.txt carries one case
# name per line plus '#' comments.  tests/run_tests.sh drops rostered
# cases from the default selection (ADVISORY-OUT lines) unless
# ROCWASH_TESTS_ONLY names them explicitly (a watch lane can run a
# quarantined case on purpose).  The CI flaky-watch job runs the roster in
# its own observation step, so a quarantined case is watched, never
# silently hidden.  Restoration requires N consecutive green isolation
# rounds (default 3, the fixture criterion); the CI-level cross-platform
# evidence rule stays with the watch lane's own process.
#
# Isolation probe semantics.  The probe runs the suite entry with
# ROCWASH_TESTS_ONLY=<case>.  rc 0 alone-green; rc 1 content-red; rc 2
# selection error (unknown case); rc 111 canonical skip (no evidence
# either way - the case did not really run); timeout = no evidence.  The
# sandbox runner additionally honors SUITE_STATE, a fresh state directory
# per invocation, so each probe models a clean checkout.

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

PROG = "flaky_guard"
SCHEMA_REPORT = "rocqwash-flaky-detect/1"
SCHEMA_LEDGER = "rocqwash-repair-ledger/1"

DEFAULT_SUITE_REL = "tests/run_tests.sh"
DEFAULT_ROSTER_REL = "tests/advisory_roster.txt"
DEFAULT_LEDGER_REL = "docs/repair-ledger.jsonl"

ROSTER_HEADER = (
    "# advisory roster - flaky quarantine (repair class E2-3).",
    "# One rostered case per line; lines starting with '#' are comments.",
    "# Written only by tools/flaky_guard.py --move --apply (scope-checked",
    "# against tools/repair_scope.py, budget-capped, ledgered).  The default",
    "# suite drops these cases with a loud ADVISORY-OUT line and the CI",
    "# flaky-watch lane keeps observing them; --restore returns a case",
    "# after green-round evidence.",
)

# data faces: the CJK literals below match the standing suite's own output
# shapes (run_tests.sh summary line), the doc_lint COUNT_PATTERNS precedent
SUMMARY_RES = (
    re.compile(r"^== 汇总: (\d+) 过 / (\d+) 红 / (\d+) 略 / 共 (\d+) 例 =="),
    re.compile(r"^== mini-summary: (\d+) pass / (\d+) red / (\d+) total ==\s*$"),
)
CASE_LINE_RE = re.compile(
    r"^\[\d+/\d+\]\s+(\S+)\s+(PASS|FAIL|SKIP)(?:\s+\(rc=(\d+)\))?\s*$")
CASES_BLOCK_RE = re.compile(r'(?ms)^CASES="(.*?)"\s*$')

VERDICT_ORDER = "order-dependent"
VERDICT_CONTENT = "content-red"
VERDICT_NOEVID = "no-evidence"
VERDICT_UNKNOWN = "unknown-case"


class UsageError(Exception):
    """Usage / malformed input (exit 2)."""


class MissingInput(Exception):
    """Missing file, runner or module (exit 9)."""


class Refused(Exception):
    """Repair refused - the reason is data (exit 1)."""


def log(msg):
    sys.stdout.write("[flaky-guard] %s\n" % msg)
    sys.stdout.flush()


def slashes(p):
    return (p or "").replace("\\", "/")


def repo_rel(path, repo_root):
    rel = os.path.relpath(path, repo_root)
    return slashes(rel)


def load_repair_scope():
    """Load tools/repair_scope.py by path (mandatory single source)."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "repair_scope.py")
    if not os.path.isfile(path):
        raise MissingInput("repair_scope.py not found next to flaky_guard.py"
                           " (the shared exclusion single source): %s" % path)
    try:
        spec = importlib.util.spec_from_file_location(
            "rqw_flaky_guard_repair_scope", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception as exc:
        raise MissingInput("repair_scope.py failed to load: %r" % (exc,))


RS = load_repair_scope()
SCOPE = RS.FlakyQuarantineScope
CLASS_ID = SCOPE.CLASS_ID
TICKET = SCOPE.TICKET
DEFAULT_BUDGET = SCOPE.BUDGET_PER_BRANCH


# ---- suite faces ----

def parse_cases(repo_root, suite_rel=DEFAULT_SUITE_REL):
    """Statically rostered case names from the suite entry (the CASES
    block; the FAIL_PROBE injection case is not part of the block)."""
    path = os.path.join(repo_root, suite_rel)
    if not os.path.isfile(path):
        raise MissingInput("suite runner missing: %s" % path)
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    m = CASES_BLOCK_RE.search(text)
    if m is None:
        raise UsageError("suite runner shape unrecognized (no CASES block):"
                         " %s" % path)
    names = m.group(1).replace("\\\n", " ").split()
    if not names:
        raise UsageError("suite runner CASES block is empty: %s" % path)
    return names


def parse_suite_log(text):
    """Suite output -> (per-case map, summary tuple or None)."""
    cases = {}
    summary = None
    for raw in text.splitlines():
        line = raw.rstrip()
        m = CASE_LINE_RE.match(line)
        if m is not None:
            name, status = m.group(1), m.group(2)
            rc = int(m.group(3)) if m.group(3) is not None else \
                (1 if status == "FAIL" else 0)
            cases[name] = {"status": status, "rc": rc}
            continue
        for rx in SUMMARY_RES:
            m = rx.match(line)
            if m is not None:
                summary = tuple(int(g) for g in m.groups())
                break
    return cases, summary


def run_suite(repo_root, suite_rel, only=None, exclude=None, py=None,
              timeout=None, sandbox_state=None):
    """One suite invocation through bash; returns (rc, output text).
    A sandbox state directory is honored by the sandbox runner only."""
    suite_path = os.path.join(repo_root, suite_rel)
    if not os.path.isfile(suite_path):
        raise MissingInput("suite runner missing: %s" % suite_path)
    bash = shutil.which("bash")
    if bash is None:
        raise MissingInput("bash not on PATH - the isolation probe runs the"
                           " suite entry, which is a bash script")
    env = dict(os.environ)
    env["ROCWASH_PY"] = py or slashes(sys.executable)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("ROCWASH_TESTS_ONLY", None)
    env.pop("ROCWASH_TESTS_EXCLUDE", None)
    env.pop("ROCWASH_ADVISORY_ROSTER", None)
    if only is not None:
        env["ROCWASH_TESTS_ONLY"] = only
    if exclude is not None:
        env["ROCWASH_TESTS_EXCLUDE"] = exclude
    if sandbox_state is not None:
        env["SUITE_STATE"] = sandbox_state
    else:
        env.pop("SUITE_STATE", None)
    try:
        pr = subprocess.run([bash, slashes(suite_path)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            env=env, timeout=timeout, cwd=repo_root)
        out = pr.stdout.decode("utf-8", "replace") \
            if isinstance(pr.stdout, bytes) else (pr.stdout or "")
        return pr.returncode, out
    except subprocess.TimeoutExpired:
        return None, "probe-timeout after %ss" % timeout


def probe_case(repo_root, case, suite_rel, py=None, timeout=None,
               sandbox_state=None):
    """Isolation probe verdict for one case (see the contract block)."""
    rc, out = run_suite(repo_root, suite_rel, only=case, py=py,
                        timeout=timeout, sandbox_state=sandbox_state)
    if rc is None:
        return {"alone_rc": None, "verdict": VERDICT_NOEVID, "tail": out}
    if rc == 0:
        verdict = VERDICT_ORDER      # suite-red plus alone-green
    elif rc == 1:
        verdict = VERDICT_CONTENT
    elif rc == 2:
        verdict = VERDICT_UNKNOWN
    elif rc == 111:
        verdict = VERDICT_NOEVID     # canonical skip: the case did not run
    else:
        verdict = VERDICT_CONTENT
    return {"alone_rc": rc, "verdict": verdict, "tail": out[-800:]}


# ---- advisory roster ----

def roster_active(path):
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        return [ln.strip() for ln in fh
                if ln.strip() and not ln.strip().startswith("#")]


def roster_write_merged(path, add=None, remove=None):
    """Read-merge-write with a same-directory temp file + os.replace."""
    lines = []
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    active = [ln.strip() for ln in lines
              if ln.strip() and not ln.strip().startswith("#")]
    changed = False
    if add is not None and add not in active:
        lines.append(add)
        changed = True
    if remove is not None and remove in active:
        lines = [ln for ln in lines if ln.strip() != remove]
        changed = True
    if not changed:
        return False
    if not lines:
        lines = list(ROSTER_HEADER)
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    os.replace(tmp, path)
    return True


# ---- repair ledger ----

def ledger_rows(path):
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for no, ln in enumerate(fh, start=1):
            ln = ln.strip()
            if not ln:
                continue
            try:
                row = json.loads(ln)
            except ValueError as exc:
                raise UsageError("repair ledger row %d is not valid JSON"
                                 " (%s): %s" % (no, path, exc))
            if not isinstance(row, dict):
                raise UsageError("repair ledger row %d is not an object:"
                                 " %s" % (no, path))
            rows.append(row)
    return rows


def ledger_append(path, row):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def git_face(repo_root):
    """(branch, short head sha); nogit when the tree is not a work tree."""
    try:
        pr = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=5, cwd=repo_root)
        branch = pr.stdout.decode("utf-8", "replace").strip() or "nogit"
        pr = subprocess.run(["git", "rev-parse", "HEAD"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=5, cwd=repo_root)
        sha = pr.stdout.decode("utf-8", "replace").strip()[:7] or "nogit"
        return (branch if pr.returncode == 0 else "nogit"), sha
    except Exception:
        return "nogit", "nogit"


def budget_used(rows, branch):
    return sum(1 for r in rows
               if r.get("kind") == "repair" and r.get("class") == CLASS_ID
               and r.get("outcome") == "repaired"
               and r.get("branch", "nogit") == branch)


def ledger_row(kind, target, outcome, repo_root, roster_rel, evidence=None,
               reason=None):
    branch, sha = git_face(repo_root)
    row = {
        "schema": SCHEMA_LEDGER,
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": kind,
        "class": CLASS_ID,
        "ticket": TICKET,
        "target": target,
        "outcome": outcome,
        "branch": branch,
        "head_sha": sha,
        "roster": roster_rel,
    }
    if evidence is not None:
        row["evidence"] = evidence
    if reason is not None:
        row["reason"] = reason
    return row


# ---- actions ----

def _resolve(args):
    repo_root = os.path.abspath(args.repo or
                                os.path.dirname(os.path.dirname(
                                    os.path.abspath(__file__))))
    if not os.path.isdir(repo_root):
        raise MissingInput("repo root missing: %s" % repo_root)
    suite_rel = repo_rel(os.path.abspath(args.suite), repo_root) \
        if args.suite else DEFAULT_SUITE_REL
    roster_abs = os.path.abspath(args.roster) if args.roster else \
        os.path.join(repo_root, DEFAULT_ROSTER_REL)
    ledger_abs = os.path.abspath(args.ledger) if args.ledger else \
        os.path.join(repo_root, DEFAULT_LEDGER_REL)
    return repo_root, suite_rel, roster_abs, ledger_abs


def _scope_check(roster_abs, ledger_abs, repo_root):
    """The single-source consumption face: both write targets must sit
    inside the class repair scope before any byte is planned."""
    ok, refusals = [], []
    for abs_path in (roster_abs, ledger_abs):
        rel = repo_rel(abs_path, repo_root)
        reason = SCOPE.refusal_reason(rel, repo_root)
        if reason is not None:
            refusals.append((rel, reason))
    return (not refusals), refusals


def cmd_detect(args):
    repo_root, suite_rel, roster_abs, ledger_abs = _resolve(args)
    if not args.log:
        raise UsageError("--detect needs --log LOG (a suite output file)")
    if not os.path.isfile(args.log):
        raise MissingInput("log file missing: %s" % args.log)
    try:
        with open(args.log, "r", encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise MissingInput("log file unreadable: %s (%s)" % (args.log, exc))
    cases, summary = parse_suite_log(text)
    fail_cases = [n for n, c in cases.items() if c["status"] == "FAIL"]
    verdicts = []
    probed = 0
    for name in fail_cases:
        if args.no_probe:
            entry = {"case": name, "suite_rc": cases[name]["rc"],
                     "alone_rc": None, "verdict": VERDICT_NOEVID,
                     "action": "unprobed"}
        else:
            probe = probe_case(repo_root, name, suite_rel, py=args.py,
                               timeout=args.probe_timeout)
            probed += 1
            action = {VERDICT_ORDER: "move-candidate",
                      VERDICT_CONTENT: "keep-visible"}.get(
                          probe["verdict"], "record-only")
            entry = {"case": name, "suite_rc": cases[name]["rc"],
                     "alone_rc": probe["alone_rc"],
                     "verdict": probe["verdict"], "action": action}
        verdicts.append(entry)
    report = {
        "schema": SCHEMA_REPORT,
        "log": slashes(args.log),
        "suite_summary": list(summary) if summary else None,
        "fail_cases": len(fail_cases),
        "probed": probed,
        "verdicts": verdicts,
    }
    log("detect log=%s fail_cases=%d probed=%d"
        % (slashes(args.log), len(fail_cases), probed))
    for v in verdicts:
        log("CANDIDATE %-24s suite_rc=%s alone_rc=%s verdict=%-16s action=%s"
            % (v["case"], v["suite_rc"], v["alone_rc"], v["verdict"],
               v["action"]))
    if not fail_cases:
        log("no red cases in the log - nothing to classify")
    if args.json:
        parent = os.path.dirname(os.path.abspath(args.json))
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1,
                      sort_keys=True)
        log("json -> %s" % args.json)
    return 0


def cmd_probe(args):
    repo_root, suite_rel, _roster_abs, _ledger_abs = _resolve(args)
    cases = parse_cases(repo_root, suite_rel)
    if args.probe not in cases:
        raise UsageError("case is not in the suite roster: %s" % args.probe)
    probe = probe_case(repo_root, args.probe, suite_rel, py=args.py,
                       timeout=args.probe_timeout)
    log("probe case=%s alone_rc=%s verdict=%s"
        % (args.probe, probe["alone_rc"], probe["verdict"]))
    return 0


def cmd_move(args):
    repo_root, suite_rel, roster_abs, ledger_abs = _resolve(args)
    cases = parse_cases(repo_root, suite_rel)
    if args.move not in cases:
        raise UsageError("case is not in the suite roster: %s" % args.move)
    roster_rel = repo_rel(roster_abs, repo_root)
    ledger_rel = repo_rel(ledger_abs, repo_root)
    mode = "apply" if args.apply else "plan"
    log("FLAKY-MOVE case=%s mode=%s repo=%s" % (args.move, mode,
                                                os.path.basename(repo_root)))
    ok, refusals = _scope_check(roster_abs, ledger_abs, repo_root)
    if not ok:
        for rel, reason in refusals:
            log("REFUSED reason=frozen-target target=%s detail=%s"
                % (rel, reason))
        raise Refused("write face outside the repair scope (%s)"
                      % "; ".join("%s: %s" % r for r in refusals))
    log("SCOPE-OK roster=%s ledger=%s (both faces inside the %s scope)"
        % (roster_rel, ledger_rel, CLASS_ID))
    if args.move in roster_active(roster_abs):
        log("ALREADY-QUARANTINED %s - no-op, no ledger row" % args.move)
        return 0
    rows = ledger_rows(ledger_abs)
    branch, _sha = git_face(repo_root)
    used = budget_used(rows, branch)
    budget = args.budget if args.budget is not None else DEFAULT_BUDGET
    log("BUDGET class=%s used=%d/%d branch=%s" % (CLASS_ID, used, budget,
                                                  branch))
    probe = probe_case(repo_root, args.move, suite_rel, py=args.py,
                       timeout=args.probe_timeout)
    log("PROBE alone_rc=%s verdict=%s" % (probe["alone_rc"],
                                          probe["verdict"]))
    evidence = {"alone_rc": probe["alone_rc"], "verdict": probe["verdict"]}
    if probe["verdict"] == VERDICT_CONTENT:
        if args.apply:
            ledger_append(ledger_abs, ledger_row(
                "repair", args.move, "escalated", repo_root, roster_rel,
                evidence=evidence,
                reason="content-red case stays visible; quarantine refused"))
        raise Refused("content-red case (%s alone_rc=%s) is not quarantine"
                      " material - it stays visible in the blocking suite"
                      % (args.move, probe["alone_rc"]))
    if probe["verdict"] != VERDICT_ORDER:
        raise Refused("isolation probe gives no order-dependence evidence"
                      " (verdict=%s alone_rc=%s) - quarantine needs"
                      " suite-red plus alone-green"
                      % (probe["verdict"], probe["alone_rc"]))
    if used >= budget:
        if args.apply:
            ledger_append(ledger_abs, ledger_row(
                "repair", args.move, "escalated", repo_root, roster_rel,
                evidence=evidence,
                reason="budget exhausted (%d/%d on branch %s); desk gate"
                       % (used, budget, branch)))
        raise Refused("repair budget exhausted for class %s on branch %s"
                      " (%d/%d) - escalation to the desk"
                      % (CLASS_ID, branch, used, budget))
    log("PLAN roster-append=%s ledger-row={kind:repair,class:%s,target:%s,"
        "outcome:repaired}" % (args.move, CLASS_ID, args.move))
    if not args.apply:
        log("PLAN dry run - zero bytes written (pass --apply to land)")
        return 0
    roster_write_merged(roster_abs, add=args.move)
    ledger_append(ledger_abs, ledger_row(
        "repair", args.move, "repaired", repo_root, roster_rel,
        evidence=evidence))
    log("APPLIED roster-append=%s ledger-row-appended=1" % args.move)
    return 0


def cmd_restore(args):
    repo_root, suite_rel, roster_abs, ledger_abs = _resolve(args)
    cases = parse_cases(repo_root, suite_rel)
    if args.restore not in cases:
        raise UsageError("case is not in the suite roster: %s" % args.restore)
    if args.green_rounds < 1:
        raise UsageError("--green-rounds must be >= 1 (empty evidence is"
                         " not evidence), got %d" % args.green_rounds)
    roster_rel = repo_rel(roster_abs, repo_root)
    ledger_rel = repo_rel(ledger_abs, repo_root)
    mode = "apply" if args.apply else "plan"
    log("FLAKY-RESTORE case=%s rounds=%d mode=%s"
        % (args.restore, args.green_rounds, mode))
    ok, refusals = _scope_check(roster_abs, ledger_abs, repo_root)
    if not ok:
        for rel, reason in refusals:
            log("REFUSED reason=frozen-target target=%s detail=%s"
                % (rel, reason))
        raise Refused("write face outside the repair scope (%s)"
                      % "; ".join("%s: %s" % r for r in refusals))
    if args.restore not in roster_active(roster_abs):
        log("NOT-QUARANTINED %s - no-op, no ledger row" % args.restore)
        return 0
    greens = 0
    for i in range(args.green_rounds):
        probe = probe_case(repo_root, args.restore, suite_rel, py=args.py,
                           timeout=args.probe_timeout)
        log("ROUND r%d alone_rc=%s verdict=%s"
            % (i + 1, probe["alone_rc"], probe["verdict"]))
        if probe["alone_rc"] == 0:
            greens += 1
    log("GREEN-EVIDENCE %d/%d rounds green" % (greens, args.green_rounds))
    if greens < args.green_rounds:
        if args.apply:
            ledger_append(ledger_abs, ledger_row(
                "repair", args.restore, "escalated", repo_root, roster_rel,
                evidence={"green_rounds": greens,
                          "required": args.green_rounds},
                reason="restore refused: green-round evidence missing; the"
                       " case stays quarantined"))
        raise Refused("restore refused: %d/%d green rounds (needs %d) -"
                      " the case stays quarantined"
                      % (greens, args.green_rounds, args.green_rounds))
    log("PLAN roster-remove=%s ledger-row={outcome:restored}"
        % args.restore)
    if not args.apply:
        log("PLAN dry run - zero bytes written (pass --apply to land)")
        return 0
    roster_write_merged(roster_abs, remove=args.restore)
    ledger_append(ledger_abs, ledger_row(
        "repair", args.restore, "restored", repo_root, roster_rel,
        evidence={"green_rounds": greens, "required": args.green_rounds}))
    log("APPLIED roster-remove=%s ledger-row-appended=1" % args.restore)
    log("NOTE the CI-level rule adds cross-platform green evidence before"
        " removal from the ci.yml roster provenance - the watch lane owns"
        " that face")
    return 0


def cmd_status(args):
    repo_root, _suite_rel, roster_abs, ledger_abs = _resolve(args)
    roster_rel = repo_rel(roster_abs, repo_root)
    ledger_rel = repo_rel(ledger_abs, repo_root)
    active = roster_active(roster_abs)
    log("FLAKY-STATUS repo=%s roster=%s entries=%d"
        % (os.path.basename(repo_root), roster_rel, len(active)))
    for name in active:
        log("QUARANTINED %s" % name)
    branch, _sha = git_face(repo_root)
    rows = ledger_rows(ledger_abs)
    used = budget_used(rows, branch)
    budget = args.budget if args.budget is not None else DEFAULT_BUDGET
    log("BUDGET class=%s used=%d/%d branch=%s" % (CLASS_ID, used, budget,
                                                  branch))
    if rows:
        log("LEDGER %s rows=%d last-outcome=%s"
            % (ledger_rel, len(rows), rows[-1].get("outcome")))
    else:
        log("LEDGER %s rows=0 (no repairs recorded)" % ledger_rel)
    return 0


# ---- selftest (sandbox mini-suite; zero real-repo writes) ----

RUNNER_SH = r"""#!/usr/bin/env bash
# mini suite - sandbox fixture for tools/flaky_guard.py --selftest
# mirrors the tests/run_tests.sh selection contract: per-case PASS/FAIL
# lines, ONLY/EXCLUDE/advisory selection, a summary line, exit 0/1.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${ROCWASH_PY:-python3}
STATE=${SUITE_STATE:-"$HERE/state"}
export SUITE_STATE="$STATE"
ADVISORY=${ROCWASH_ADVISORY_ROSTER:-"$HERE/advisory_roster.txt"}
# literal roster block: the guard parses this shape statically (the
# run_tests.sh CASES form with backslash continuations)
ALL_CASES="t_alpha t_polluter t_orderdep t_broken"
CASES="\
t_alpha \
t_polluter \
t_orderdep \
t_broken"

t_alpha()    { "$PY" -B "$HERE/cases/t_alpha.py"; }
t_polluter() { "$PY" -B "$HERE/cases/t_polluter.py"; }
t_orderdep() { "$PY" -B "$HERE/cases/t_orderdep.py"; }
t_broken()   { "$PY" -B "$HERE/cases/t_broken.py"; }

_advisory=""
if [ -f "$ADVISORY" ]; then
  for _n in $(grep -v '^[[:space:]]*#' "$ADVISORY" | tr '\n\r' '  '); do
    [ -z "$_n" ] && continue
    _hit=0
    for _c in $ALL_CASES; do [ "$_c" = "$_n" ] && _hit=1 && break; done
    if [ "$_hit" = "1" ]; then
      _advisory="$_advisory $_n"
    else
      echo "ADVISORY-NOTE: unknown advisory name ignored: $_n"
    fi
  done
fi

for _w in ${ROCWASH_TESTS_ONLY:-}; do
  _ok=0
  for _c in $ALL_CASES; do [ "$_c" = "$_w" ] && _ok=1 && break; done
  if [ "$_ok" != "1" ]; then
    echo "SELECTION-ERROR: unknown ONLY name: $_w"
    exit 2
  fi
done

CASES="$ALL_CASES"
if [ -n "${ROCWASH_TESTS_ONLY:-}" ] || [ -n "${ROCWASH_TESTS_EXCLUDE:-}" ] || [ -n "$_advisory" ]; then
  _sel=""
  for _c in $CASES; do
    _drop=0
    if [ -n "${ROCWASH_TESTS_ONLY:-}" ]; then
      _drop=1
      for _w in $ROCWASH_TESTS_ONLY; do
        [ "$_c" = "$_w" ] && _drop=0 && break
      done
    else
      for _x in ${ROCWASH_TESTS_EXCLUDE:-}; do
        if [ "$_c" = "$_x" ]; then
          _drop=1
          printf 'SELECTED-OUT %-12s\n' "$_c"
        fi
      done
      for _ax in $_advisory; do
        if [ "$_c" = "$_ax" ]; then
          _drop=1
          printf 'ADVISORY-OUT %-12s (flaky quarantine; the watch lane covers it)\n' "$_c"
        fi
      done
    fi
    [ "$_drop" != "1" ] && _sel="$_sel $_c"
  done
  CASES="$_sel"
  if [ -z "$(echo $CASES | tr -d ' ')" ]; then
    echo "SELECTION-ERROR: selection is empty"
    exit 2
  fi
fi

PASS=0; FAIL=0; TOTAL=0
NC=$(echo $CASES | wc -w | tr -d ' ')
for c in $CASES; do
  TOTAL=$((TOTAL + 1))
  if "$c" >"$HERE/.last_$c.log" 2>&1; then
    PASS=$((PASS + 1))
    printf '[%d/%d] %-12s PASS\n' "$TOTAL" "$NC" "$c"
  else
    rc=$?
    FAIL=$((FAIL + 1))
    printf '[%d/%d] %-12s FAIL (rc=%d)\n' "$TOTAL" "$NC" "$c" "$rc"
  fi
done
echo "== mini-summary: $PASS pass / $FAIL red / $TOTAL total =="
if [ "$FAIL" -ne 0 ]; then
  exit 1
fi
exit 0
"""

CASE_ALPHA = (
    "import sys\n"
    "sys.exit(0)\n"
)

CASE_POLLUTER = (
    "import os, sys\n"
    "state = os.environ['SUITE_STATE']\n"
    "os.makedirs(state, exist_ok=True)\n"
    "marker = os.path.join(state, 'marker')\n"
    "with open(marker, 'w', encoding='utf-8') as fh:\n"
    "    fh.write('polluted')\n"
    "sys.exit(0)\n"
)

CASE_ORDERDEP = (
    "import os, sys\n"
    "state = os.environ.get('SUITE_STATE')\n"
    "if not state:\n"
    "    sys.exit(3)  # harness contract missing - fail loud, never guess\n"
    "os.makedirs(state, exist_ok=True)\n"
    "marker = os.path.join(state, 'marker')\n"
    "if not os.path.exists(marker):\n"
    "    with open(marker, 'w', encoding='utf-8') as fh:\n"
    "        fh.write('clean')\n"
    "with open(marker, 'r', encoding='utf-8') as fh:\n"
    "    content = fh.read()\n"
    "sys.exit(0 if content == 'clean' else 1)\n"
)

CASE_BROKEN = (
    "import sys\n"
    "print('broken by construction (content-red vector)')\n"
    "sys.exit(1)\n"
)


def build_sandbox(root):
    """Sandbox mini-suite tree: runner + four cases + an empty roster."""
    os.makedirs(os.path.join(root, "cases"))
    files = {
        "run_suite.sh": RUNNER_SH,
        os.path.join("cases", "t_alpha.py"): CASE_ALPHA,
        os.path.join("cases", "t_polluter.py"): CASE_POLLUTER,
        os.path.join("cases", "t_orderdep.py"): CASE_ORDERDEP,
        os.path.join("cases", "t_broken.py"): CASE_BROKEN,
    }
    for rel, body in files.items():
        with open(os.path.join(root, rel), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(body)
    with open(os.path.join(root, "advisory_roster.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(ROSTER_HEADER) + "\n")
    return {"root": root,
            "suite": os.path.join(root, "run_suite.sh"),
            "roster": os.path.join(root, "advisory_roster.txt"),
            "ledger": os.path.join(root, "repair-ledger.jsonl")}


class Sandbox(object):
    """A selftest sandbox run: fresh state dir per suite invocation."""

    def __init__(self, sbx):
        self.sbx = sbx
        self._tmp = None

    def run(self, only=None, exclude=None):
        self._cleanup()
        self._tmp = tempfile.mkdtemp(prefix="rqw_flaky_state_")
        return run_suite(self.sbx["root"], self.sbx["suite"], only=only,
                         exclude=exclude, timeout=120,
                         sandbox_state=self._tmp)

    def _cleanup(self):
        if self._tmp is not None:
            shutil.rmtree(self._tmp, ignore_errors=True)
            self._tmp = None

    def close(self):
        self._cleanup()


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def selftest():
    tmp = tempfile.mkdtemp(prefix="rqw_flaky_selftest_")
    vecs = []

    def vec(name, ok, detail=""):
        vecs.append((name, bool(ok), detail))

    try:
        guard = os.path.abspath(__file__)
        real_repo = os.path.dirname(os.path.dirname(guard))
        py = slashes(sys.executable)

        # ---- V1 baseline red: the orderdep case fails in suite context,
        #      the content-red vector fails too; detection sees both.
        sbx = build_sandbox(os.path.join(tmp, "sbx"))
        box = Sandbox(sbx)
        rc, out = box.run()
        vec("v1-baseline-red", rc == 1 and "t_orderdep" in out
            and "FAIL" in out, "rc=%s" % rc)
        cases, _summary = parse_suite_log(out)
        vec("v1-parse", cases.get("t_orderdep", {}).get("status") == "FAIL"
            and cases.get("t_broken", {}).get("status") == "FAIL",
            sorted(cases).__str__())
        log_path = os.path.join(tmp, "baseline.log")
        with open(log_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(out)
        roster_before = read_bytes(sbx["roster"])
        p = run_guard(["--detect", "--log", log_path, "--repo", sbx["root"],
                       "--suite", sbx["suite"], "--roster", sbx["roster"],
                       "--ledger", sbx["ledger"], "--py", py])
        vec("v2-detect-rc", p["rc"] == 0, p["out"][-300:])
        vec("v2-detect-verdicts",
            "verdict=order-dependent" in p["out"]
            and "verdict=content-red" in p["out"], p["out"][-400:])
        vec("v2-detect-zero-write",
            read_bytes(sbx["roster"]) == roster_before
            and not os.path.isfile(sbx["ledger"]), "")
        p = run_guard(["--detect", "--log", log_path, "--json",
                       os.path.join(tmp, "detect.json"), "--repo",
                       sbx["root"], "--suite", sbx["suite"], "--roster",
                       sbx["roster"], "--ledger", sbx["ledger"], "--py", py])
        rep = json.loads(open(os.path.join(tmp, "detect.json"),
                              encoding="utf-8").read())
        vec("v2-json-schema", rep["schema"] == SCHEMA_REPORT
            and rep["fail_cases"] == 2 and rep["probed"] == 2, "")

        # ---- V3/V4 single probes: orderdep alone-green, broken alone-red.
        rc, out = box.run(only="t_orderdep")
        vec("v3-orderdep-alone-green", rc == 0, "rc=%s" % rc)
        rc, out = box.run(only="t_broken")
        vec("v4-broken-alone-red", rc == 1, "rc=%s" % rc)

        # ---- V5 move dry-run: plan lines, zero bytes.
        p = run_guard(["--move", "t_orderdep", "--repo", sbx["root"],
                       "--suite", sbx["suite"], "--roster", sbx["roster"],
                       "--ledger", sbx["ledger"], "--py", py])
        vec("v5-plan-rc", p["rc"] == 0 and "PLAN roster-append=t_orderdep"
            in p["out"], p["out"][-400:])
        vec("v5-plan-zero-write",
            read_bytes(sbx["roster"]) == roster_before
            and not os.path.isfile(sbx["ledger"]), "")

        # ---- V6 apply: roster row + ledger row; re-apply is a no-op.
        p = run_guard(["--move", "t_orderdep", "--apply", "--repo",
                       sbx["root"], "--suite", sbx["suite"], "--roster",
                       sbx["roster"], "--ledger", sbx["ledger"], "--py", py])
        active = roster_active(sbx["roster"])
        rows = ledger_rows(sbx["ledger"])
        vec("v6-apply", p["rc"] == 0 and active == ["t_orderdep"]
            and len(rows) == 1
            and rows[0]["outcome"] == "repaired"
            and rows[0]["class"] == CLASS_ID
            and rows[0]["target"] == "t_orderdep", p["out"][-400:])
        ledger_before = read_bytes(sbx["ledger"])
        p = run_guard(["--move", "t_orderdep", "--apply", "--repo",
                       sbx["root"], "--suite", sbx["suite"], "--roster",
                       sbx["roster"], "--ledger", sbx["ledger"], "--py", py])
        vec("v6-idempotent", p["rc"] == 0
            and "ALREADY-QUARANTINED" in p["out"]
            and read_bytes(sbx["ledger"]) == ledger_before
            and roster_active(sbx["roster"]) == ["t_orderdep"],
            p["out"][-200:])

        # ---- V7 the fixture green criterion: the main suite runs green
        #      three consecutive rounds, each with a loud ADVISORY-OUT.
        greens = 0
        for i in range(3):
            rc, out = box.run(exclude="t_broken")
            if rc == 0 and "ADVISORY-OUT" in out and "t_orderdep" in out:
                greens += 1
        vec("v7-three-green-rounds", greens == 3, "greens=%d" % greens)

        # ---- V8 budget cap: a full ledger refuses the next repair.
        sbx2 = build_sandbox(os.path.join(tmp, "sbx2"))
        forge = [{"schema": SCHEMA_LEDGER, "kind": "repair",
                  "class": CLASS_ID, "ticket": TICKET, "target": "t_x",
                  "outcome": "repaired", "branch": "nogit",
                  "head_sha": "nogit", "roster": "tests/advisory_roster.txt"}
                 for _ in range(2)]
        with open(sbx2["ledger"], "w", encoding="utf-8", newline="\n") as fh:
            for row in forge:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        p = run_guard(["--move", "t_orderdep", "--apply", "--repo",
                       sbx2["root"], "--suite", sbx2["suite"], "--roster",
                       sbx2["roster"], "--ledger", sbx2["ledger"],
                       "--py", py])
        rows2 = ledger_rows(sbx2["ledger"])
        vec("v8-budget-refused", p["rc"] == 1
            and "budget exhausted" in p["out"]
            and roster_active(sbx2["roster"]) == []
            and len(rows2) == 3
            and rows2[-1]["outcome"] == "escalated", p["out"][-400:])

        # ---- V9 frozen-target refusals against the real repo scope
        #      (single-source consumption; dry run, zero bytes anywhere).
        p = run_guard(["--move", "t_watch_repo_form", "--repo", real_repo,
                       "--roster", os.path.join(real_repo, "certify",
                                                "adv.txt")])
        vec("v9-frozen-roster", p["rc"] == 1
            and "frozen-target" in p["out"]
            and "directory family exclusion" in p["out"], p["out"][-300:])
        p = run_guard(["--move", "t_watch_repo_form", "--repo", real_repo,
                       "--ledger", os.path.join(real_repo, "更新账.md")])
        vec("v9-frozen-ledger", p["rc"] == 1 and "frozen-target" in p["out"]
            and "append-only" in p["out"], p["out"][-300:])
        vec("v9-no-roster-created",
            not os.path.isfile(os.path.join(real_repo, "certify", "adv.txt")),
            "")

        # ---- V10 content-red refusal: broken is never quarantined.
        p = run_guard(["--move", "t_broken", "--apply", "--repo", sbx["root"],
                       "--suite", sbx["suite"], "--roster", sbx["roster"],
                       "--ledger", sbx["ledger"], "--py", py])
        vec("v10-content-red-refused", p["rc"] == 1
            and "content-red" in p["out"]
            and roster_active(sbx["roster"]) == ["t_orderdep"],
            p["out"][-300:])

        # ---- V11 restore without green evidence is refused; the case
        #      stays quarantined.  The guard's own probes run against the
        #      sandbox runner's persistent state dir (sbx/state), so a
        #      polluted marker there models a leftover side effect that
        #      reddens the case even alone.
        state_dir = os.path.join(sbx["root"], "state")
        os.makedirs(state_dir, exist_ok=True)
        with open(os.path.join(state_dir, "marker"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write("polluted")
        p = run_guard(["--restore", "t_orderdep", "--green-rounds", "1",
                       "--apply", "--repo", sbx["root"], "--suite",
                       sbx["suite"], "--roster", sbx["roster"], "--ledger",
                       sbx["ledger"], "--py", py])
        vec("v11-restore-refused", p["rc"] == 1
            and "restore refused" in p["out"]
            and roster_active(sbx["roster"]) == ["t_orderdep"],
            p["out"][-300:])
        p = run_guard(["--restore", "t_orderdep", "--green-rounds", "0",
                       "--apply", "--repo", sbx["root"], "--suite",
                       sbx["suite"], "--roster", sbx["roster"], "--ledger",
                       sbx["ledger"], "--py", py])
        vec("v11-zero-rounds-usage", p["rc"] == 2, "rc=%s" % p["rc"])

        # ---- V12 restore with green rounds: roster shrinks back, ledger
        #      records the restore; the suite reddens again (expected).
        with open(os.path.join(state_dir, "marker"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write("clean")
        p = run_guard(["--restore", "t_orderdep", "--green-rounds", "2",
                       "--apply", "--repo", sbx["root"], "--suite",
                       sbx["suite"], "--roster", sbx["roster"], "--ledger",
                       sbx["ledger"], "--py", py])
        rows = ledger_rows(sbx["ledger"])
        vec("v12-restore-applied", p["rc"] == 0
            and roster_active(sbx["roster"]) == []
            and rows[-1]["outcome"] == "restored"
            and any(r["outcome"] == "escalated" for r in rows),
            p["out"][-400:])
        rc, out = box.run(exclude="t_broken")
        vec("v12-back-to-red", rc == 1, "rc=%s" % rc)

        # ---- V13 status: loud account, zero writes.
        ledger_before = read_bytes(sbx["ledger"])
        p = run_guard(["--status", "--repo", sbx["root"], "--roster",
                       sbx["roster"], "--ledger", sbx["ledger"]])
        vec("v13-status", p["rc"] == 0 and "FLAKY-STATUS" in p["out"]
            and "BUDGET" in p["out"]
            and read_bytes(sbx["ledger"]) == ledger_before,
            p["out"][-300:])

        # ---- V14 scope invariant on the real repo (repair_scope import).
        ok, refusals = SCOPE.check_writable(real_repo)
        vec("v14-scope-invariant", ok and not refusals, repr(refusals))
        vec("v14-scope-refusals",
            SCOPE.refusal_reason("更新账.md", real_repo) is not None
            and SCOPE.refusal_reason("seeds/x.json", real_repo) is not None
            and SCOPE.refusal_reason("docs/zh/a.md", real_repo) is not None
            and SCOPE.refusal_reason("../x", real_repo) is not None
            and SCOPE.refusal_reason("tests/advisory_roster.txt",
                                     real_repo) is None, "")

        # ---- V15 CLI codes.
        p = run_guard(["--help"])
        vec("v15-help", p["rc"] == 0 and "usage" in p["out"], "")
        p = run_guard(["--bogus"])
        vec("v15-bogus", p["rc"] == 2, "rc=%s" % p["rc"])
        p = run_guard(["--detect", "--log",
                       os.path.join(tmp, "absent.log"), "--repo",
                       sbx["root"]])
        vec("v15-log-missing", p["rc"] == 9, "rc=%s" % p["rc"])
        p = run_guard(["--detect", "--repo", sbx["root"]])
        vec("v15-log-required", p["rc"] == 2, "rc=%s" % p["rc"])
        p = run_guard(["--move", "t_nosuch", "--repo", sbx["root"],
                       "--suite", sbx["suite"]])
        vec("v15-unknown-case", p["rc"] == 2, "rc=%s" % p["rc"])
        p = run_guard(["--detect", "--probe", "t_x", "--repo", sbx["root"]])
        vec("v15-two-actions", p["rc"] == 2, "rc=%s" % p["rc"])
        corrupt = os.path.join(sbx2["root"], "corrupt.jsonl")
        with open(corrupt, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{not json}\n")
        p = run_guard(["--move", "t_orderdep", "--repo", sbx2["root"],
                       "--suite", sbx2["suite"], "--roster", sbx2["roster"],
                       "--ledger", corrupt, "--py", py])
        vec("v15-corrupt-ledger", p["rc"] == 2 and "not valid JSON"
            in p["out"], p["out"][-200:])

        box.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [v for v in vecs if not v[1]]
    for name, ok, detail in vecs:
        print("%s %s%s" % ("PASS" if ok else "FAIL", name,
                           (" - %s" % detail) if detail and not ok else ""))
    print("summary: %d vectors, %d FAIL" % (len(vecs), len(failed)))
    if failed:
        return 1
    print("FLAKY-GUARD-SELFTEST PASS: baseline red / detect verdicts"
          " order-dependent vs content-red / dry-run zero-write / apply"
          " with ledger row and idempotent re-apply / three consecutive"
          " green rounds with ADVISORY-OUT / budget refusal / frozen-target"
          " refusals against the real scope / content-red refusal / restore"
          " refusal and restore with green rounds / status / scope"
          " invariant / CLI codes - all vectors pass")
    return 0


def run_guard(argv):
    """One subprocess run of this tool (selftest helper)."""
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        pr = subprocess.run([sys.executable, "-B",
                             os.path.abspath(__file__)] + argv,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            env=env, timeout=600)
        out = pr.stdout.decode("utf-8", "replace") \
            if isinstance(pr.stdout, bytes) else (pr.stdout or "")
        return {"rc": pr.returncode, "out": out}
    except subprocess.TimeoutExpired:
        return {"rc": None, "out": "guard invocation timed out"}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        return selftest()
    actions = [f for f, flag in (("detect", "--detect"), ("probe", "--probe"),
                                 ("move", "--move"), ("restore", "--restore"),
                                 ("status", "--status")) if flag in argv]
    if len(actions) > 1:
        sys.stderr.write("%s: one action per run, got %s\n"
                         % (PROG, ",".join(actions)))
        return 2
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="order-dependence detection and advisory-roster"
                    " quarantine (repair class E2-3; report schema %s,"
                    " ledger schema %s)" % (SCHEMA_REPORT, SCHEMA_LEDGER))
    ap.add_argument("--detect", action="store_true",
                    help="classify every red case in --log (with isolation"
                         " probes unless --no-probe)")
    ap.add_argument("--probe", metavar="CASE",
                    help="run one isolation probe for CASE")
    ap.add_argument("--move", metavar="CASE",
                    help="quarantine CASE into the advisory roster"
                         " (dry-run plan by default)")
    ap.add_argument("--restore", metavar="CASE",
                    help="return CASE from the advisory roster after"
                         " green-round evidence")
    ap.add_argument("--status", action="store_true",
                    help="print the roster, the budget and the ledger"
                         " summary (read-only)")
    ap.add_argument("--selftest", action="store_true",
                    help="sandbox vector group (zero real-repo writes)")
    ap.add_argument("--log", metavar="LOG", default=None,
                    help="suite output file for --detect")
    ap.add_argument("--json", metavar="OUT", default=None,
                    help="detect report output path (%s)" % SCHEMA_REPORT)
    ap.add_argument("--no-probe", action="store_true",
                    help="detect without isolation probes (unprobed rows)")
    ap.add_argument("--apply", action="store_true",
                    help="land the planned write (roster and ledger); the"
                         " default is a dry-run plan")
    ap.add_argument("--green-rounds", dest="green_rounds", type=int,
                    default=3, metavar="N",
                    help="consecutive green rounds --restore needs"
                         " (default 3)")
    ap.add_argument("--budget", type=int, default=None, metavar="N",
                    help="override the per-branch repair budget (default"
                         " from repair_scope)")
    ap.add_argument("--probe-timeout", dest="probe_timeout", type=int,
                    default=300, metavar="S",
                    help="per-probe second cap (default 300)")
    ap.add_argument("--repo", default=None, metavar="DIR",
                    help="repo root (default: the parent of tools/)")
    ap.add_argument("--roster", default=None, metavar="PATH",
                    help="advisory roster file (default %s)"
                         % DEFAULT_ROSTER_REL)
    ap.add_argument("--ledger", default=None, metavar="PATH",
                    help="repair ledger file (default %s)"
                         % DEFAULT_LEDGER_REL)
    ap.add_argument("--suite", default=None, metavar="PATH",
                    help="suite runner (default %s)" % DEFAULT_SUITE_REL)
    ap.add_argument("--py", default=None, metavar="EXE",
                    help="interpreter for the suite's child processes"
                         " (default: this interpreter)")
    args = ap.parse_args(argv)
    if not actions:
        ap.print_help()
        return 2
    try:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        if args.detect:
            return cmd_detect(args)
        if args.probe:
            return cmd_probe(args)
        if args.move:
            return cmd_move(args)
        if args.restore:
            return cmd_restore(args)
        if args.status:
            return cmd_status(args)
        ap.print_help()
        return 2
    except Refused as exc:
        log("REFUSED %s" % exc)
        return 1
    except UsageError as exc:
        sys.stderr.write("FAIL-LOUD: %s\n" % exc)
        return 2
    except MissingInput as exc:
        sys.stderr.write("FAIL-LOUD: %s\n" % exc)
        return 9


if __name__ == "__main__":
    sys.exit(main())
