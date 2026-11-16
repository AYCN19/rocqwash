#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_selfheal_guards: suite shell for the self-heal driver's three
heal-leg guards (.github/scripts/selfheal_rocqwash.py).

    Purpose.  The three guardrail reinforcement points as frozen vectors:
      the attempt cap (heal_leg :140-143, run_attempt==1 is the stateless
      at-most-once budget), the cancel-intent never-revive gate (:144-145;
      the reconcile leg records cancelled as intent at :204-206), and the
      live re-check right before the rerun POST (:149-156; a live state
      that is cancelled or not completed is desk intent, a transport
      error is a loud skip, only a still-completed run reaches the POST).
    Interface.  No CLI.  Five vector groups, 20 checks: attempt-cap skip
      with zero POST and the cap preceding the live GET; cancel-intent
      skip with zero POST plus the cap-outranks-intent order pin; the
      live re-check four-way (in-progress / cancelled / transport error
      all skip; a still-completed run dispatches exactly one
      rerun-failed-jobs POST behind exactly one GET); the transient-only
      family whitelist; the reconcile intent recording with zero POSTs.
    Dependencies.  Python 3 stdlib only (argparse, importlib.util, json,
      os, sys); the driver module loads by path and its gh_api/time
      symbols are replaced with an in-process recording stub; tmp-free,
      zero network, zero real sleep, zero repository writes.
    Evidence.  Every check asserts on the stub's recorded (method, path)
      call log; nothing is inferred from source reading.
    Exit-codes.  0 all checks pass; 1 any check red (listed loudly).
"""
import importlib.util
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, ".github", "scripts", "selfheal_rocqwash.py")


def load_module():
    if not os.path.isfile(SCRIPT):
        sys.stderr.write("T-SELFHEAL-GUARDS FAIL selfheal_rocqwash.py "
                         "missing: %s\n" % SCRIPT)
        raise SystemExit(1)
    spec = importlib.util.spec_from_file_location(
        "rqw_test_selfheal_rocqwash", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ApiStub(object):
    """Recording gh_api stand-in: canned run/runs responses, a settable
    live-run state, zero network."""

    def __init__(self, live_run):
        self.live_run = live_run      # None = transport error on live GET
        self.calls = []               # (method, path) log

    def __call__(self, token, path, method="GET", body=None):
        self.calls.append((method, path))
        if path.endswith("/rerun-failed-jobs"):
            return {}, None
        if "/runs/" in path and path.rstrip("/").split("/")[-1].isdigit() \
                and "/jobs" not in path:
            if self.live_run is None:
                return None, "transport-error-canned"
            return self.live_run, None
        if "/runs" in path and "workflows" in path:
            return self.runs_list, None
        if "/jobs" in path:
            return {"jobs": []}, None
        return {}, None

    def posts(self):
        return [p for m, p in self.calls if m == "POST"]


def make_args(heal=True, delay=0):
    import argparse
    return argparse.Namespace(repo="org/repo", run=178, out=".",
                              heal=heal, heal_delay=delay, reconcile=False)


TRANSIENT = "transient-infra"


def run_guard(mod, api, run, family, heal=True, delay=0):
    """heal_leg with the stubbed transport; the real time.sleep face is
    bypassed by stubbing the module symbol (delay 0 even when not
    stubbed)."""
    mod.gh_api = api
    return mod.heal_leg(make_args(heal=heal, delay=delay), "token",
                        "org/repo", run, family)


def main():
    mod = load_module()
    fails = []

    def check(name, cond, detail=""):
        if cond:
            print("PASS %s" % name)
        else:
            fails.append("%s -- %s" % (name, detail))
            print("FAIL %s -- %s" % (name, detail))

    # ---- vector 1: the attempt cap (the at-most-once budget, :140-143) --
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 2,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("attempt-cap-skips", verdict == "skipped(attempt-cap)",
          "verdict=%r detail=%r" % (verdict, detail))
    check("attempt-cap-attempt-echo", "attempt=2" in detail,
          "detail=%r" % detail)
    check("attempt-cap-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    check("attempt-cap-precedes-live-check", api.calls == [],
          "cap must precede the live re-check GET: %r" % api.calls)
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": None,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("attempt-missing-defaults-to-1", verdict != "skipped(attempt-cap)",
          "verdict=%r" % verdict)

    # ---- vector 2: cancel-intent (desk intent, never revived, :144-145) -
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "cancelled"},
                                TRANSIENT)
    check("cancel-intent-skips", verdict == "skipped(intent-cancelled)",
          "verdict=%r detail=%r" % (verdict, detail))
    check("cancel-intent-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    check("cancel-intent-precedes-live-check", api.calls == [],
          "intent gate precedes the live re-check GET: %r" % api.calls)
    # the cap outranks the intent gate (guard order is pinned)
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, _ = run_guard(mod, api,
                           {"id": 178, "run_attempt": 3,
                            "status": "completed",
                            "conclusion": "cancelled"},
                           TRANSIENT)
    check("cap-outranks-intent", verdict == "skipped(attempt-cap)",
          "verdict=%r" % verdict)

    # ---- vector 3: the live re-check (before the rerun POST, :149-156) --
    # 3a: live in_progress = desk moved the run -> intent skip, zero POST
    api = ApiStub(live_run={"id": 178, "status": "in_progress",
                            "conclusion": None})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("live-in-progress-skips", verdict == "skipped(intent-cancelled)",
          "verdict=%r detail=%r" % (verdict, detail))
    check("live-in-progress-live-get", ("GET", "/repos/org/repo/actions/"
                                        "runs/178") in api.calls,
          "calls=%r" % api.calls)
    check("live-in-progress-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    # 3b: live cancelled = desk intent -> skip, zero POST
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "cancelled"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("live-cancelled-skips", verdict == "skipped(intent-cancelled)",
          "verdict=%r detail=%r" % (verdict, detail))
    check("live-cancelled-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    # 3c: live-check transport failure = loud skip, zero POST
    api = ApiStub(live_run=None)
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("live-error-skips", verdict == "skipped(live-check: "
          "transport-error-canned)", "verdict=%r detail=%r"
          % (verdict, detail))
    check("live-error-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    # 3d: live still completed -> exactly one rerun POST
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("live-still-completed-dispatches", verdict == "dispatched",
          "verdict=%r detail=%r" % (verdict, detail))
    check("live-still-completed-one-post",
          api.posts() == ["/repos/org/repo/actions/runs/178/"
                          "rerun-failed-jobs"],
          "posts=%r" % api.posts())
    check("live-still-completed-single-get",
          api.calls == [("GET", "/repos/org/repo/actions/runs/178"),
                        ("POST", "/repos/org/repo/actions/runs/178/"
                         "rerun-failed-jobs")],
          "exactly one live GET then one rerun POST, in order: %r"
          % api.calls)

    # ---- vector 4: the family whitelist feeding the three guards -------
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                "content-red")
    check("content-red-not-healable",
          verdict == "skipped(family-not-healable)",
          "verdict=%r" % verdict)
    check("content-red-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    check("content-red-zero-live-check", api.calls == [],
          "family gate precedes every fetch: %r" % api.calls)

    # ---- vector 5: reconcile records cancelled as intent (:204-206) ----
    api = ApiStub(live_run=None)
    api.runs_list = {"total_count": 3, "workflow_runs": [
        {"id": 201, "run_number": 10, "status": "queued",
         "conclusion": None, "created_at": "2026-11-16T00:00:00Z"},
        {"id": 178, "run_number": 9, "status": "completed",
         "conclusion": "cancelled", "created_at": "2026-11-16T01:00:00Z"},
        {"id": 155, "run_number": 8, "status": "completed",
         "conclusion": "cancelled", "created_at": "2026-11-16T02:00:00Z"},
    ]}
    mod.gh_api = api
    token_saved = os.environ.pop("GITHUB_TOKEN", None)
    try:
        os.environ["GITHUB_TOKEN"] = "stub-token"   # the stub ignores it
        lines = mod.reconcile_leg(make_args(), "org/repo")
    finally:
        os.environ.pop("GITHUB_TOKEN", None)
        if token_saved is not None:
            os.environ["GITHUB_TOKEN"] = token_saved
    text = "\n".join(lines)
    check("reconcile-records-intent-not-revive",
          "cancelled=intent" in text and "not revived" in text, text)
    check("reconcile-cancels-counted",
          sum(1 for ln in lines if "cancelled=intent" in ln) == 2,
          "both cancelled runs recorded: %r" % lines)
    check("reconcile-never-revives", api.posts() == [],
          "reconcile never POSTs a revive: %r" % api.posts())

    if fails:
        sys.stderr.write("T-SELFHEAL-GUARDS RED (%d): %s\n"
                         % (len(fails), "; ".join(fails)))
        return 1
    sys.stdout.write("T-SELFHEAL-GUARDS PASS (5 vector groups, 20 checks: "
                     "attempt-cap / cancel-intent / live re-check / family "
                     "whitelist / reconcile intent recording)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
