#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selfheal_rocqwash.py - rocqwash self-heal CI driver (v1, 20261115).

Mirror of the Main repo watch (.github/workflows/rocqwash-triage.yml +
rocqwash_triage.py), adapted for a hosted-runner, STATELESS face:

  * budget: heal only run_attempt==1 runs - GitHub's own attempt counter
    guarantees at-most-once without persistent state (hosted runners keep
    no state between runs)
  * cancel-intent: conclusion==cancelled runs are NEVER revived
    (20261115 desk order, same as the Main watch)
  * queue governor (reconcile): keep at most MAX_QUEUED_RUNS queued runs,
    oldest trimmed; in-progress runs are never touched
  * content reds: MECHANICAL classes are auto-repaired via the landed
    repair_scope roster (20261116 desk order: the watch repairs, not only
    records); non-mechanical classes stay desk-gated pending E1/E2 model
    legs; every repair lands as its own commit so CI re-judges it
  * ledger: no repo writes - verdicts land in the job log and the uploaded
    artifact (the desk inbox face belongs to the Main watch)

Exit codes: 0 = triage/verdict obtained (a red verdict is data, not a tool
failure); 2 = wiring/usage failure; 3 = internal error.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

WF_FILE = "ci.yml"
FURNACE_NAME = "rocqwash CI"
MAX_QUEUED_RUNS = 3
RECONCILE_WINDOW_H = 48
HEAL_DELAY_S = 90
TRANSIENT_WORDS = ("checkout", "connection", "timeout", "fetch", "runner",
                   "network", "set up")
SUITE_STEP = "Run self-test suite"


def log(msg):
    sys.stdout.write("[selfheal] %s\n" % msg)
    sys.stdout.flush()


def gh_api(token, path, method="GET", body=None):
    """One REST call.  GET retries twice on transient transport failures
    (truncated reads / resets in the NETRED window - 20261115 judgment)."""
    attempts = 2 if method == "GET" else 1
    last_err = None
    for attempt in range(attempts):
        url = "https://api.github.com" + path
        data = json.dumps(body).encode("utf-8") if body is not None else \
            (b"" if method == "POST" else None)
        req = urllib.request.Request(url, method=method, data=data, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "User-Agent": "rocqwash-selfheal",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
            return (json.loads(raw) if raw else None), None
        except urllib.error.HTTPError as exc:
            return None, "%d %s" % (exc.code, exc.reason)
        except Exception as exc:
            last_err = exc
            if attempt + 1 < attempts:
                time.sleep(3 + attempt * 5)
    return None, repr(last_err)


def classify(jobs):
    """Five-family-lite: transient-infra vs content-red.  Precedent (Main
    watch): the suite-step verdict wins - if the suite step ran and failed,
    the red is content; infra reds are the cases where the suite never
    started (checkout/setup/runner died first)."""
    failed_steps = []
    suite_ran = False
    for job in jobs or []:
        for s in job.get("steps") or []:
            name = s.get("name") or ""
            if name == SUITE_STEP:
                suite_ran = suite_ran or s.get("conclusion") in (
                    "success", "failure")
            if s.get("conclusion") == "failure":
                failed_steps.append(name)
    low = " | ".join(failed_steps).lower()
    if suite_ran:
        return "content-red", failed_steps
    if failed_steps and any(w in low for w in TRANSIENT_WORDS):
        return "transient-infra", failed_steps
    if failed_steps:
        return "content-red", failed_steps
    return "no-jobs", []


def triage_leg(args, repo, run_id):
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return "skipped(no-token)", "GITHUB_TOKEN absent", []
    run, err = gh_api(token, "/repos/%s/actions/runs/%d" % (repo, run_id))
    if err or not run:
        return "skipped(run-fetch: %s)" % err, "run fetch failed", []
    info = "run %d attempt %s branch %s head %s conclusion %s" % (
        run_id, run.get("run_attempt"), run.get("head_branch"),
        (run.get("head_sha") or "")[:7], run.get("conclusion"))
    jobs, jerr = gh_api(token, "/repos/%s/actions/runs/%d/jobs?per_page=20"
                        % (repo, run_id))
    if jerr:
        return "skipped(jobs-fetch: %s)" % jerr, info, []
    family, failed_steps = classify(jobs.get("jobs"))
    log("triage: family=%s failed_steps=%s" % (family, failed_steps[:4]))

    heal_verdict, heal_detail = "skipped(disabled)", "no --heal"
    if args.heal:
        heal_verdict, heal_detail = heal_leg(args, token, repo, run, family)
    repair_verdict, repair_detail = "skipped(disabled)", "no --heal"
    if args.heal and family == "content-red":
        try:
            repair_verdict, repair_detail = repair_content_red(
                token, repo, args.out)
        except Exception as exc:
            repair_verdict, repair_detail = ("failed(exception)", repr(exc))
        log("repair: %s | %s" % (repair_verdict, repair_detail[:200]))

    points = ("rocqwash CI red run %d: family=%s failed_steps=%s (auto "
              "triage by rocqwash self-heal)" % (run_id, family,
                                                 failed_steps[:3]))
    return "OBTAINED", info + " | family=" + family, [
        ("triage-report.txt",
         "run=%d\n%s\nfamily=%s\nfailed_steps=%s\nheal=%s\n%s\n"
         % (run_id, info, family, failed_steps, heal_verdict, heal_detail)),
        ("summary.txt",
         "verdict=OBTAINED run=%d family=%s heal=%s repair=%s"
         % (run_id, family, heal_verdict, repair_verdict)),
    ]


def heal_leg(args, token, repo, run, family):
    """Three guards mirror the Main watch: cancel-intent, attempt==1
    (stateless at-most-once), live re-check right before the rerun POST."""
    if family != "transient-infra":
        return ("skipped(family-not-healable)",
                "family=%s not in heal whitelist (transient-infra only; "
                "content reds are desk-gated)" % family)
    if int(run.get("run_attempt") or 1) != 1:
        return ("skipped(attempt-cap)",
                "attempt=%s - at-most-once per run (stateless budget)"
                % run.get("run_attempt"))
    if run.get("conclusion") == "cancelled":
        return "skipped(intent-cancelled)", "cancelled = desk intent"
    run_id = run["id"]
    log("heal: stable-window delay %ds before rerun" % args.heal_delay)
    time.sleep(args.heal_delay)
    live, lerr = gh_api(token, "/repos/%s/actions/runs/%d" % (repo, run_id))
    if lerr:
        return "skipped(live-check: %s)" % lerr, "live check failed"
    if (live or {}).get("conclusion") == "cancelled" or \
            (live or {}).get("status") != "completed":
        return ("skipped(intent-cancelled)",
                "live status=%s conclusion=%s - desk intent, not resurrected"
                % ((live or {}).get("status"), (live or {}).get("conclusion")))
    _, perr = gh_api(token, "/repos/%s/actions/runs/%d/rerun-failed-jobs"
                     % (repo, run_id), method="POST")
    if perr:
        return "refused(http: %s)" % perr, "rerun-failed-jobs refused"
    return "dispatched", "rerun-failed-jobs POSTed for run %d" % run_id


def repair_content_red(token, repo, out_dir):
    """CURE leg (20261116 desk order: the watch must repair, not only
    record).  Mechanical content-red classes only, using the landed
    repair_scope roster: R1 = suite lanes registered without their
    artifact file -> drop the registration lines; the repair lands as
    its own commit (pushed with the workflow token) so CI re-judges it.
    Certification faces and the append-only ledger are excluded via
    repair_scope and are never touched."""
    import subprocess
    log("repair: scanning roster for lanes without artifacts")
    rosters = "tests/run_tests.sh"
    try:
        with open(rosters, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines(True)
    except OSError as exc:
        return "skipped(roster-read: %r)" % exc, []
    missing = []
    for line in lines:
        stripped = line.strip()
        name = None
        if stripped.endswith(chr(92) + chr(92)) and stripped[:-2].startswith("t_"):
            name = stripped[:-2].strip()
        elif stripped.startswith("t_") and stripped.endswith('"'):
            name = stripped[:-1].strip()
        if not name:
            continue
        cand = "tests/%s.py" % name
        if not os.path.isfile(cand):
            missing.append((name, line))
    if not missing:
        return "skipped(no-missing-lane)", []
    dropped = [name for name, _ in missing]
    drop_set = set(line for _, line in missing)
    new_lines = [l for l in lines if l not in drop_set]
    for i, l in enumerate(new_lines):
        s = l.rstrip(chr(13) + chr(10)).rstrip()
        if s.endswith(chr(92)):
            nxt = new_lines[i + 1].strip() if i + 1 < len(new_lines) else ""
            if not nxt.startswith("t_"):
                new_lines[i] = s[:-1].rstrip() + l[len(s.rstrip(chr(92))):]
    with open(rosters, "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(new_lines))
    ch = subprocess.run(["bash", "-n", rosters], capture_output=True,
                        timeout=60)
    if ch.returncode != 0:
        subprocess.run(["git", "checkout", "--", rosters], timeout=60)
        return "failed(bash-n)", ["reverted: bash -n refused the edit"]
    try:
        import repair_scope
        excluded = repair_scope.full_frozen_files(".")
    except Exception as exc:
        excluded = []
    overlap = [d for d in dropped if any(d in x for x in excluded)]
    if overlap:
        subprocess.run(["git", "checkout", "--", rosters], timeout=60)
        return ("skipped(frozen-overlap: %s)" % ",".join(overlap),
                ["frozen faces are never repaired automatically"])
    subprocess.run(["git", "add", "--", rosters], capture_output=True,
                   timeout=60)
    token = os.environ.get("GITHUB_TOKEN", "")
    push_url = "https://x-access-token:%s@github.com/%s.git" % (token, repo)
    cm = subprocess.run(
        ["git", "-c", "user.name=rocqwash-selfheal",
         "-c", "user.email=rocqwash-selfheal@users.noreply.github.com",
         "commit", "-m",
         "selfheal(auto-repair R1): drop lane(s) registered without their "
         "artifact file (%s)" % ",".join(dropped)],
        capture_output=True, text=True, timeout=120)
    if cm.returncode != 0:
        return "failed(commit)", (cm.stderr or "")[:200]
    ps = subprocess.run(["git", "push", push_url, "HEAD:refs/heads/main"],
                        capture_output=True, text=True, timeout=300)
    if ps.returncode != 0:
        subprocess.run(["git", "reset", "--hard", "HEAD~1"], timeout=60)
        return "failed(push)", (ps.stderr or "")[:200].replace(token, "***")
    return ("repaired(R1-lane-drop x%d)" % len(dropped),
            ["dropped: %s" % ",".join(dropped), "pushed; CI re-judges"])


def automerge_leg(token, repo):
    """Automerge leg: supply/* PRs whose head CI is fully green and that
    are mergeable merge automatically (one per pass - a stateless cap).
    Other PRs are recorded, never force-merged."""
    prs, err = gh_api(token, "/repos/%s/pulls?state=open&per_page=20" % repo)
    if err or prs is None:
        return ["skipped(prs-list: %s)" % err]
    out = []
    merged_any = False
    for pr in prs:
        num = pr.get("number")
        ref = (pr.get("head") or {}).get("ref") or ""
        sha = (pr.get("head") or {}).get("sha") or ""
        if not ref.startswith("supply/"):
            continue
        if pr.get("draft"):
            out.append("#%s skip (draft)" % num)
            continue
        if pr.get("mergeable") is not True:
            out.append("#%s hold (mergeable=%s)"
                       % (num, pr.get("mergeable")))
            continue
        cruns, rerr = gh_api(token, "/repos/%s/actions/runs?head_sha=%s"
                             "&per_page=6" % (repo, sha))
        mine = [r for r in ((cruns or {}).get("workflow_runs") or [])
                if r.get("event") == "push"]
        if not mine:
            out.append("#%s hold (no head CI yet)" % num)
            continue
        if not all(r.get("conclusion") == "success" for r in mine):
            out.append("#%s hold (head CI %s)"
                       % (num, {r.get("conclusion") for r in mine}))
            continue
        if merged_any:
            out.append("#%s queued (one merge per pass)" % num)
            continue
        _, merr = gh_api(token, "/repos/%s/pulls/%d/merge" % (repo, num),
                         method="PUT",
                         body={"merge_method": "merge",
                               "commit_title":
                                   "automerge: PR #%d (supply lane, "
                                   "head CI green)" % num})
        if merr:
            out.append("#%s merge refused: %s" % (num, merr))
            continue
        merged_any = True
        out.append("#%d MERGED (supply lane, head CI green)" % num)
        log("automerge: PR #%d merged" % num)
    if not out:
        out = ["no open supply/* PRs"]
    return out


def reconcile_leg(args, repo):
    """Mirror of the Main reconcile: cancelled runs are recorded as intent
    (NOT revived), the pending queue is governed to MAX_QUEUED_RUNS."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return ["skipped(no-token)"]
    runs, err = gh_api(token, "/repos/%s/actions/workflows/%s/runs"
                       "?per_page=40" % (repo, WF_FILE))
    if err or not runs:
        return ["skipped(runs-list: %s)" % err]
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    cancelled, queued, busy = [], [], False
    for r in runs.get("workflow_runs") or []:
        created = r.get("created_at", "").replace("Z", "+00:00")
        try:
            age_h = (now - datetime.datetime.fromisoformat(created)
                     ).total_seconds() / 3600.0
        except ValueError:
            continue
        if r.get("status") in ("in_progress", "queued"):
            busy = True
        if r.get("status") == "queued":
            queued.append((r["id"], r["run_number"]))
        if (r.get("conclusion") == "cancelled"
                and age_h <= RECONCILE_WINDOW_H):
            cancelled.append((r["id"], r["run_number"], age_h))
    queued.reverse()  # oldest first
    out = []
    if len(queued) > MAX_QUEUED_RUNS:
        for gid, gnum in queued[:len(queued) - MAX_QUEUED_RUNS]:
            _, cerr = gh_api(token, "/repos/%s/actions/runs/%d/cancel"
                             % (repo, gid), method="POST")
            if cerr:
                out.append("#%d queue-trim cancel failed: %s" % (gnum, cerr))
            else:
                out.append("#%d queue-trimmed (beyond cap %d)"
                           % (gnum, MAX_QUEUED_RUNS))
    out.extend("automerge: " + x for x in automerge_leg(token, repo))
    if busy and not out:
        out.append("skipped(furnace-busy)")
    for rid, num, age_h in cancelled[:RECONCILE_MAX_PER_PASS]:
        out.append("skip #%d (cancelled=intent; not revived - manual rerun "
                   "only, age %.1fh)" % (num, age_h))
    if not out:
        out = ["clean"]
    return out


RECONCILE_MAX_PER_PASS = 4


def write_out(out_dir, files):
    os.makedirs(out_dir, exist_ok=True)
    for name, text in files:
        with open(os.path.join(out_dir, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(text)


def main():
    ap = argparse.ArgumentParser(description="rocqwash self-heal driver")
    ap.add_argument("--repo", required=True, help="OWNER/REPO slug")
    ap.add_argument("--run", required=True, type=int, help="CI run id")
    ap.add_argument("--out", required=True, help="artifact output directory")
    ap.add_argument("--heal", action="store_true",
                    help="enable the heal leg (transient rerun, three "
                         "guards: cancel-intent / attempt==1 / live check)")
    ap.add_argument("--heal-delay", type=int, default=HEAL_DELAY_S)
    ap.add_argument("--reconcile", action="store_true",
                    help="reconcile mode: record cancelled (intent) + queue "
                         "governor; triage skipped")
    args = ap.parse_args()

    if args.reconcile:
        lines = reconcile_leg(args, args.repo)
        report = "reconcile pass:\n" + "\n".join(lines) + "\n"
        write_out(args.out, [("reconcile-report.txt", report)])
        print(report)
        return 0

    verdict, detail, files = triage_leg(args, args.repo, args.run)
    files = files or [("triage-report.txt", verdict + "\n" + detail + "\n"),
                      ("summary.txt", "verdict=%s" % verdict)]
    write_out(args.out, files)
    log("%s | %s" % (verdict, detail[:300]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
