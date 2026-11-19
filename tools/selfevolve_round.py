#!/usr/bin/env python3
"""selfevolve_round.py - one deterministic mechanical round (cron face).
Purpose.  One mechanical round: census -> apply -> verify (py_compile /
  bash -n gates, norm_lint / doc_lint advisory) -> auto_round commit ->
  push -> route the CI judge (R13 sub-face 4).  Frozen faces stay
  excluded by jargon_apply; zero fixes = no-op pass; residue != 0 =
  fail-loud red.
Interface.  python3 tools/selfevolve_round.py [--dry-run] [--pin-repair
  [--seed P]].  --pin-repair (A-batch leg, before census, never fatal)
  plans the seed pins (tools/pin_repair.py --plan): no drift = clean
  skip; absent pins = hosted structural blind (one ledger row, no
  commit); drift = --apply + an independent auto_round commit (class
  R15-repair, rides the round push); refusal = loud; --dry-run plans
  only.  Every round prints one cadence report JSON line: cadence_hint
  from docs/scheduling-feedback.json via the finite in-code tier table
  (alert: escalated >= 3, or repaired == 0 with >= 5 recorded repair
  actions; slow: rate < 0.2; else normal; absent feedback = normal);
  escalated >= 3 also appends one cadence-alert ledger row (loud).
Dependencies.  Standard library only; no network face added (judge
  routing reuses gh_dispatch); subprocess faces: jargon_apply.py,
  pin_repair.py (-I), auto_round.py, py_compile / bash -n, the lints;
  the ledger path reads env ROCQWASH_REPAIR_PLAN_LEDGER (default
  docs/repair-plan-ledger.jsonl).
Evidence.  Vectors: zero-drift skip; hosted-blind ledger row; drift
  apply + independent commit; refusal fail-loud; cadence tier fixtures.
Exit-codes.  0 green / clean no-op; 2 fail-loud red (apply residue,
  admission refusal, push refusal); 3 census report unreadable; the
  pin-repair leg and the cadence report never change the exit code.
"""
import argparse
import json
import os
import subprocess
import sys
import time

REPO = os.environ.get("GITHUB_REPOSITORY", "hy7pc8gfmf-dotcom/rocqwash")
PY = sys.executable or "python3"

PIN_REPAIR_EXECUTOR = "tools/pin_repair.py"
PIN_REPAIR_SEED_DEFAULT = os.path.join("seeds", "jargon", "jargon-map.json")
PIN_REPAIR_COMMIT_MESSAGE = ("fix(seeds): R15 pin re-sign by the round "
                             "apply leg (IN-SYNC plan verdict; "
                             "verify-rollback armed)")
LEDGER_ENV = "ROCQWASH_REPAIR_PLAN_LEDGER"
LEDGER_DEFAULT = os.path.join("docs", "repair-plan-ledger.jsonl")
LEDGER_SCHEMA = "rocqwash.repair-plan/1"
FEEDBACK_PATH = os.path.join("docs", "scheduling-feedback.json")
# the finite cadence tier table (A-batch contract): the thresholds are
# standing constants and are never derived from the data they judge
CADENCE_ALERT_ESCALATED = 3
CADENCE_ALERT_MIN_ACTIONS = 5
CADENCE_SLOW_RATE = 0.2


def run(cmd, timeout=300):
    return subprocess.run(cmd, capture_output=True, timeout=timeout,
                          encoding="utf-8", errors="replace")


def gh_dispatch(token, repo, workflow, ref):
    import urllib.request
    req = urllib.request.Request(
        "https://api.github.com/repos/%s/actions/workflows/%s/dispatches"
        % (repo, workflow),
        data=json.dumps({"ref": ref}).encode(),
        headers={"Accept": "application/vnd.github+json",
                 "Authorization": "Bearer " + token,
                 "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status


def utc_ts():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ledger_path():
    """Repair-plan ledger path; the env seam lets tests redirect rows
    to a temporary file (the standing ledger never takes test rows)."""
    return os.environ.get(LEDGER_ENV) or LEDGER_DEFAULT


def ledger_append(row):
    """Append one JSON row to the repair-plan ledger; returns True on
    write, and an OSError is printed loud and reported (never a silent
    swallow)."""
    try:
        with open(ledger_path(), "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")
        return True
    except OSError as err:
        print("FAIL-LOUD: repair-plan ledger append failed (%s): %r"
              % (ledger_path(), err))
        return False


def build_parser():
    """The flag face; --help prints usage and exits without running the
    round (a bare main() would execute it, which once made a doc_lint
    --help probe rewrite the census artifact as a side effect)."""
    ap = argparse.ArgumentParser(
        prog="selfevolve_round",
        description="One deterministic mechanical round (cron face); "
                    "--pin-repair arms the R15 pin-repair leg.")
    ap.add_argument("--dry-run", dest="dry_run", action="store_true",
                    help="census + report only, no writes (local testing)")
    ap.add_argument("--pin-repair", dest="pin_repair", action="store_true",
                    help="arm the R15 pin-repair leg (desk/local opt-in; "
                         "the hosted cron passes no flag)")
    ap.add_argument("--seed", default=PIN_REPAIR_SEED_DEFAULT,
                    help="seed path forwarded to pin_repair (default: "
                         + PIN_REPAIR_SEED_DEFAULT + ")")
    return ap


def executor_report(proc):
    """The executor's one JSON stdout line as a dict, else None."""
    lines = (proc.stdout or "").strip().splitlines()
    if not lines:
        return None
    try:
        report = json.loads(lines[-1])
    except ValueError:
        return None
    return report if isinstance(report, dict) else None


def plan_failed_row(proc, row):
    """Fill the ledger row for a failed or unparseable plan run."""
    tail = ((proc.stderr or proc.stdout or "").strip()[-300:])
    row["note"] = ("pin-repair --plan exit %s; tail=%s"
                   % (proc.returncode, tail))
    print("FAIL-LOUD: pin-repair leg plan failed (exit %s) - ledger row "
          "written, round continues" % proc.returncode)
    ledger_append(row)


def apply_leg(seed, row, drifted):
    """Apply the pin re-sign and land it as one independent commit.

    An apply refusal stays loud with zero commit (the executor already
    rolled the seed back byte-identically on a red verification); a
    green apply is committed through the round admission gate with the
    standing class and message, then rides the round's own push (a
    zero-fix round leaves the commit for the next round's push)."""
    row["action"] = "apply"
    try:
        proc = run([PY, "-I", PIN_REPAIR_EXECUTOR, "--apply",
                    "--seed", seed], timeout=600)
    except Exception as err:
        row["ok"] = False
        row["note"] = "pin-repair --apply spawn failed: %r" % (err,)
        print("FAIL-LOUD: %s - zero commit, round continues" % row["note"])
        ledger_append(row)
        return
    report = executor_report(proc)
    if proc.returncode != 0 or not report \
            or report.get("action") != "apply":
        row["ok"] = False
        tail = ((proc.stderr or proc.stdout or "").strip()[-300:])
        row["note"] = ("pin-repair --apply refused (exit %s); zero "
                       "commit; tail=%s" % (proc.returncode, tail))
        print("FAIL-LOUD: %s - round continues" % row["note"])
        ledger_append(row)
        return
    row["ok"] = True
    row["drifted"] = drifted
    res = run([PY, "tools/auto_round.py", "commit", "--repo-root", ".",
               "--classes", "R15-repair", "--class-confidence",
               "R15-repair=1.0", "--message", PIN_REPAIR_COMMIT_MESSAGE,
               "--files", seed], timeout=600)
    tail = (((res.stdout or "") + (res.stderr or "")).strip()[-300:])
    if res.returncode != 0:
        row["ok"] = False
        row["note"] = ("pin re-sign commit refused (exit %s): %s"
                       % (res.returncode, tail))
        print("FAIL-LOUD: %s - round continues" % row["note"])
        ledger_append(row)
        return
    row["note"] = ("pin re-sign applied and committed (%d pin(s), class "
                   "R15-repair): %s" % (len(drifted), tail))
    print("pin-repair leg: %s" % row["note"])
    ledger_append(row)


def pin_repair_leg(dry, seed):
    """R15 pin-repair leg (A-batch contract deliverable one).

    Environment-aware dual site: on the hosted runner the two pins
    outside the repository are unreadable, the executor's plan then
    reports the absent form, and the leg degrades to one ledger row
    plus a clean skip (zero commit); on the local site a drifted plan
    is applied and committed independently.  This leg never raises and
    never changes the round exit code."""
    row = {"schema": LEDGER_SCHEMA, "ts": utc_ts(), "run": "round",
           "class": "R15", "action": "plan", "ok": False, "drifted": [],
           "verdict": "", "note": ""}
    try:
        proc = run([PY, "-I", PIN_REPAIR_EXECUTOR, "--plan",
                    "--seed", seed], timeout=420)
    except Exception as err:
        row["note"] = "pin-repair --plan spawn failed: %r" % (err,)
        print("FAIL-LOUD: %s - round continues" % row["note"])
        ledger_append(row)
        return
    report = executor_report(proc)
    if proc.returncode == 0 and report:
        verdict = report.get("verdict", "")
        row["verdict"] = verdict if isinstance(verdict, str) else ""
        row["ok"] = bool(report.get("ok"))
    if proc.returncode == 0 and report and report.get("action") == "none":
        print("pin-repair leg: no pin drift (action=none) - clean skip")
        return
    absent = report.get("absent") if report else None
    if (proc.returncode == 0 and report
            and report.get("action") == "plan" and absent):
        row["note"] = ("hosted-blind: %d pinned source(s) unreadable "
                       "here (absent form); drifted=%d; zero commit"
                       % (len(absent), len(report.get("drifted") or [])))
        print("pin-repair leg: %s - round continues" % row["note"])
        ledger_append(row)
        return
    drifted = report.get("drifted") if report else None
    if (proc.returncode == 0 and report
            and report.get("action") == "plan" and drifted):
        if dry:
            print("dry-run: pin re-sign would apply (%d drifted pin(s), "
                  "no writes)" % len(drifted))
            return
        apply_leg(seed, row, drifted)
        return
    plan_failed_row(proc, row)


def outcome_count(value):
    """Non-negative count from a feedback value (number or list); a
    malformed value reads as zero and never invents an alert."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(int(value), 0)
    if isinstance(value, list):
        return len(value)
    return 0


def read_cadence_hint():
    """Map docs/scheduling-feedback.json onto the finite cadence tier
    table (A-batch contract deliverable two).  Absent feedback reads
    normal with the absent note; an unreadable or malformed face prints
    loud and reads normal (a broken input never invents an alert).
    Repair actions are the recorded outcome counts (repaired, escalated,
    errors, watch_only_guard_correct); unrecorded rows are not actions.
    Returns the stdout summary dict."""
    summary = {"cadence_hint": "normal", "note": "absent",
               "escalated": None, "repaired": None,
               "repair_action_rate": None, "repair_actions_total": None}
    try:
        with open(FEEDBACK_PATH, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except OSError:
        return summary
    except ValueError as err:
        summary["note"] = "invalid-json"
        print("FAIL-LOUD: scheduling-feedback unreadable (%r) - hint "
              "stays normal" % (err,))
        return summary
    outcomes = doc.get("repair_outcomes") if isinstance(doc, dict) else None
    if not isinstance(outcomes, dict):
        summary["note"] = "malformed"
        print("FAIL-LOUD: scheduling-feedback carries no repair_outcomes "
              "object - hint stays normal")
        return summary
    escalated = outcome_count(outcomes.get("escalated"))
    repaired = outcome_count(outcomes.get("repaired"))
    actions = (repaired + escalated
               + outcome_count(outcomes.get("errors"))
               + outcome_count(outcomes.get("watch_only_guard_correct")))
    rate = outcomes.get("repair_action_rate")
    if isinstance(rate, bool) or not isinstance(rate, (int, float)):
        rate = None
    if escalated >= CADENCE_ALERT_ESCALATED or (
            repaired == 0 and actions >= CADENCE_ALERT_MIN_ACTIONS):
        hint = "alert"
    elif rate is not None and rate < CADENCE_SLOW_RATE:
        hint = "slow"
    else:
        hint = "normal"
    return {"cadence_hint": hint,
            "note": ("escalated=%d repaired=%d actions=%d rate=%s"
                     % (escalated, repaired, actions,
                        "n/a" if rate is None else "%.4f" % rate)),
            "escalated": escalated, "repaired": repaired,
            "repair_action_rate": rate, "repair_actions_total": actions}


def emit_cadence_report():
    """Print the round cadence report line; on escalated >= 3 append one
    cadence-alert row to the repair-plan ledger (loud print; the round
    itself continues either way)."""
    summary = read_cadence_hint()
    print("cadence-hint: " + json.dumps(summary, sort_keys=True))
    escalated = summary["escalated"]
    if escalated is not None and escalated >= CADENCE_ALERT_ESCALATED:
        row = {"schema": LEDGER_SCHEMA, "ts": utc_ts(), "run": "round",
               "class": "cadence", "action": "cadence-alert", "ok": False,
               "drifted": [], "verdict": "alert", "note": summary["note"]}
        if ledger_append(row):
            print("CADENCE-ALERT: escalated=%d >= %d - alert row appended "
                  "to %s" % (escalated, CADENCE_ALERT_ESCALATED,
                             ledger_path()))


def main(argv=None):
    args = build_parser().parse_args(argv)
    dry = args.dry_run
    if args.pin_repair:
        try:
            pin_repair_leg(dry, args.seed)
        except Exception as err:
            print("FAIL-LOUD: pin-repair leg raised (%r) - round "
                  "continues" % (err,))
            try:
                ledger_append({"schema": LEDGER_SCHEMA, "ts": utc_ts(),
                               "run": "round", "class": "R15",
                               "action": "plan", "ok": False,
                               "drifted": [], "verdict": "",
                               "note": "pin-repair leg internal error: "
                                       "%r" % (err,)})
            except Exception as row_err:
                print("FAIL-LOUD: pin-repair ledger row also failed: %r"
                      % (row_err,))
    try:
        emit_cadence_report()
    except Exception as err:
        print("FAIL-LOUD: cadence report raised (%r) - round continues"
              % (err,))
    plan = run([PY, "tools/jargon_apply.py", "--tree", ".", "--plan",
                "--json", "round-plan.json"])
    try:
        report = json.load(open("round-plan.json", encoding="utf-8"))
    except Exception as err:
        print("census report unreadable: %r" % err)
        return 3
    fixes = (report.get("would_fix")
             or report.get("fixes")
             or report.get("would_fix_count")
             or [])
    n = len(fixes) if isinstance(fixes, list) else int(fixes or 0)
    print("census: would_fix=%s" % n)
    if n == 0:
        print("no qualifying mechanical fixes this round - clean no-op pass")
        return 0
    if dry:
        print("dry-run: %d fixes would apply (no writes)" % n)
        return 0

    res = run([PY, "tools/jargon_apply.py", "--tree", ".", "--apply",
               "--json", "round-apply.json"], timeout=600)
    print("apply rc=%s %s" % (res.returncode,
                              (res.stderr or res.stdout).strip()[-300:]))
    if res.returncode != 0:
        print("FAIL-LOUD: apply residue gate refused the round")
        return 2

    changed = run(["git", "diff", "--name-only"]).stdout.split()
    if not changed:
        print("apply produced no diff - no-op pass")
        return 0
    print("changed faces (%d): %s" % (len(changed), ", ".join(changed[:20])))

    for f in changed:
        if f.endswith(".py"):
            rc = run([PY, "-m", "py_compile", f])
            if rc.returncode != 0:
                print("FAIL-LOUD: py_compile %s red" % f)
                return 2
        elif f.endswith(".sh"):
            rc = run(["bash", "-n", f])
            if rc.returncode != 0:
                print("FAIL-LOUD: bash -n %s red" % f)
                return 2
    for face, args in (("norm_lint", ["--tree", "."]),
                       ("doc_lint", [])):
        rc = run([PY, "tools/%s.py" % face] + args, timeout=600)
        print("advisory %s rc=%s" % (face, rc.returncode))

    files_arg = ",".join(changed)
    res = run([PY, "tools/auto_round.py", "commit", "--repo-root", ".",
               "--classes", "jargon", "--class-confidence", "jargon=1.0",
               "--message", "selfevolve cron round: mechanical jargon sweep",
               "--files", files_arg], timeout=600)
    print("auto_round commit rc=%s %s" % (
        res.returncode,
        ((res.stdout or "") + (res.stderr or "")).strip()[-300:]))
    if res.returncode != 0:
        print("FAIL-LOUD: auto_round admission refused the round")
        return 2

    res = run(["git", "push", "origin", "HEAD:main"], timeout=300)
    print("push rc=%s %s" % (res.returncode,
                             (res.stderr or "").strip()[-200:]))
    if res.returncode != 0:
        print("FAIL-LOUD: push refused")
        return 2

    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        try:
            gh_dispatch(token, REPO, "ci.yml", "main")
            print("post-commit CI dispatched@main (push-event suppression "
                  "bypass - R13 sub-face 4)")
        except Exception as err:
            print("post-commit CI dispatch failed (desk watch covers): %r"
                  % err)
    else:
        print("no GITHUB_TOKEN: post-commit CI dispatch skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
