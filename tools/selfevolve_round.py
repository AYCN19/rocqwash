#!/usr/bin/env python3
"""selfevolve_round.py - one deterministic mechanical round (cron face,
20261117 desk order: the standing self-evolution cadence).

Pipeline: census (jargon_apply --plan) -> apply -> verify (py_compile /
bash -n hard gates, norm_lint/doc_lint advisory) -> auto_round commit
(ledger + anchor, jargon class admitted at confidence 1.0 >= 0.80) ->
push -> route the CI judge (the push carries GITHUB_TOKEN, so GitHub
suppresses its push event - R13 sub-face 4; workflow_dispatch is the
documented exception).

Safety:
  * frozen faces (certify/scan/verify/wrapper + the repair roster) are
    excluded by jargon_apply itself (the round-1 standing rule)
  * zero qualifying fixes = clean no-op pass (no commit, no push)
  * apply residue != zero = fail-loud, no commit
  * --dry-run: census + report only (local testing)
"""
import json
import os
import subprocess
import sys

REPO = os.environ.get("GITHUB_REPOSITORY", "hy7pc8gfmf-dotcom/rocqwash")
PY = sys.executable or "python3"


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


def main():
    dry = "--dry-run" in sys.argv
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
