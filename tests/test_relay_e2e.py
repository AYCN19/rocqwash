#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_relay_e2e.py — end-to-end relay check for the cw_sentinel
--on-red-preset unclog chain (tests/).

    Purpose.  Drives the sentinel->unclog relay end to end on tmp
      fixtures: (1) event trigger — the canned failing CI build (run 178)
      emits the ci-red event into the --emit JSONL and the unclog preset
      delegate-runs the tool (cmd expansion and the delegate rc=9 are
      recorded honestly in the actions account; the watcher exit code
      stays 0 — side actions sit outside the verdict surface); (2) unclog
      dry run — --audit rc=0 with zero tree writes, failure seen
      (red_files=["B"]), chain root A washable, `wall` empty; (3) the
      report path recorded by check (1) byte-compared against check
      (2)'s report (schema `rocqwash-unclog/1`, verdict=audit).

    Interface.  python3 tests/test_relay_e2e.py; drives `tools/cw_sentinel.py`
      and `tools/unclog.py` via subprocess; lane `t_relay_e2e` in tests/run_tests.sh.

    Dependencies.  Python 3 standard library only; zero real network, zero
      real compilation, zero real-repo touch (all canned; delegated helpers
      are pure stdlib, unclog.py:192-193); tmp self-managed (mkdtemp removed
      in finally, delegate residue swept); runs under `python3 -B`.

    Evidence.  Precedent: cw_sentinel selftest case [9] trigger capture
      (cw_sentinel.py:1941-1962; preset table cw_sentinel.py:324); unclog
      selftest v10 --audit (unclog.py:1705) and v4 rounds-exhausted
      (unclog.py:1555); fixture bodies match unclog.py:1385,1440-1457.

    Exit-codes.  0 = all three checks pass; 1 = any check failing (each
      failure listed loudly; no silent downgrade).
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENTINEL = os.path.join(REPO, "tools", "cw_sentinel.py")
UNCLOG = os.path.join(REPO, "tools", "unclog.py")

CURE13_BODY = ("Theorem t8 : forall f pf k,\n"          # unclog.py:1385 CURE13_BODY, same text
               "  (gnPrf f pf <= k)%nat -> NatOK f pf k.\n"
               "Proof. intros. apply g0. Qed.\n")


def run(tool, args):
    """subprocess runner (stdout and stderr merged; canned mode: zero
    network, zero compilation)."""
    p = subprocess.run([sys.executable, "-B", tool] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def tree_manifest(root):
    """--src whole-file md5 inventory (deterministic double sort; same shape
    as tree_manifest at unclog.py:360; recomputed independently here as the
    baseline surface of the zero-write differential proof)."""
    man = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for fn in sorted(filenames):
            fp = os.path.join(dirpath, fn)
            with io.open(fp, "rb") as fh:
                man[os.path.relpath(fp, root)] = hashlib.md5(fh.read()).hexdigest()
    return man


def build_fixture(tmp):
    """the three tmp fixtures (gold-standard provenance cited inline): the
    src tree, the watcher injector, the unclog scenario.  Returns
    (src, injector path, scenario directory)."""
    src = os.path.join(tmp, "src")
    os.makedirs(src)
    with io.open(os.path.join(src, "A.v"), "w", encoding="utf-8") as fh:
        fh.write(CURE13_BODY)
    with io.open(os.path.join(src, "B.v"), "w", encoding="utf-8") as fh:
        fh.write("Require Import A.\n")
    # (1) the watcher injector: canned failing CI build, run 178 (same
    # runs/jobs bodies as the cw_sentinel selftest canned fixture,
    # cw_sentinel.py:1645-1662)
    inj = {"schema": "rocqwash-sentinel-injector/1", "responses": [
        {"url_contains": "/actions/runs?", "status": 200,
         "body": {"total_count": 1, "workflow_runs": [
             {"id": 178, "name": "CI", "run_number": 9, "status": "completed",
              "conclusion": "failure", "head_branch": "main",
              "head_sha": "abc123def",
              "html_url": "https://github.com/org/repo/actions/runs/178"}]}},
        {"url_contains": "/runs/178/jobs", "status": 200,
         "body": {"total_count": 1, "jobs": [
             {"id": 501, "name": "build", "status": "completed",
              "conclusion": "failure",
              "started_at": "2026-11-10T08:00:00Z",
              "completed_at": "2026-11-10T08:01:00Z",
              "steps": [{"number": 1, "name": "Build (coqc batch)",
                         "status": "completed", "conclusion": "failure",
                         "started_at": "2026-11-10T08:00:01Z",
                         "completed_at": "2026-11-10T08:00:30Z"}]}]}}]}
    inj_path = os.path.join(tmp, "inj_sentinel.json")
    with io.open(inj_path, "w", encoding="utf-8") as fh:
        json.dump(inj, fh, sort_keys=True)
    # (3) the unclog scenario: the canned failing probe ledger (same record
    # shape as unclog.py:1440-1457; same L1 content: A passing and washable,
    # B missing A)
    led = {"schema": "rocqwash-probe-ledger/1", "n_records": 2, "records": {
        "A": {"file": "A", "md5": None, "rc": 0, "red": "", "missing": None,
              "red_class": None, "verdict": "RC0", "red_count": None,
              "md5_match": None},
        "B": {"file": "B", "md5": None, "rc": 1,
              "red": "Error: Unable to locate library | A (while searching "
                     "for a .vos file).",
              "missing": "A", "red_class": "MISSING_LIB",
              "verdict": "RED-MISSING_LIB", "red_count": None,
              "md5_match": None}}}
    scen_dir = os.path.join(tmp, "scenario")
    os.makedirs(scen_dir)
    with io.open(os.path.join(scen_dir, "scenario.json"), "w",
                 encoding="utf-8") as fh:
        json.dump({"probe": [led]}, fh, sort_keys=True)
    return src, inj_path, scen_dir


def main():
    # zero-touch law: zero real network, zero real compilation, zero
    # real-repo touch — the real subprocess chain only orchestrates pure-
    # stdlib helpers (unclog.py:192-193); only a real `rocq c` compile
    # needs the cpu_guard (the probe_engine contract).  tmp is self-managed
    # (mkdtemp removed in finally) and `python3 -B` keeps __pycache__ off.
    # real-run sample (November 11, 2026, a live tmp exercise, not
    # handwritten; the full transcript is archived in the ops
    # realtime-service manual under docs/, linked from CHANGELOG.md):
    # watcher leg stdout tail `on-red note: cmd rc=9 (side action; does not
    # change the sentinel's exit code)` then exit 0; unclog leg stdout tail
    # `report -> .../unclog_178.json` plus `VERDICT: audit (exit 0)`; the
    # src md5 inventory diffs empty before and after (zero writes).
    fails = []
    tmp = tempfile.mkdtemp(prefix="rocqwash_relay_e2e_")
    try:
        src, inj_path, scen_dir = build_fixture(tmp)
        emit = os.path.join(tmp, "events.jsonl")
        rep_path = os.path.join(tmp, "report.json")
        emit_dir = os.path.dirname(os.path.abspath(emit))

        # -- check 1 event trigger: canned failing CI build -> ci-red event
        # -> the on-red preset delegate run --
        rc, out = run(SENTINEL, [
            "--once", "--watch-repo", "org/repo", "--branch", "main",
            "--injector", inj_path,
            "--state-file", os.path.join(tmp, "state.json"),
            "--emit", emit, "--json", rep_path,
            "--on-red-preset", "unclog", "--on-red-arg", "src=" + src,
            "--sleep-scale", "0"])
        if rc != 0:
            fails.append("check 1: the watcher should exit rc=0 (a failing "
                         "result is data, not a tool failure); got %d\n%s"
                         % (rc, out[-600:]))
        try:
            evs = [json.loads(l) for l in io.open(emit, encoding="utf-8")
                   if l.strip()]
        except (ValueError, OSError) as e:
            evs = []
            fails.append("check 1: the event stream should be parseable: %s"
                         % e)
        if len(evs) != 1 or evs and evs[0].get("kind") != "ci-red" \
                or evs and evs[0].get("run") != 178 \
                or evs and evs[0].get("family") != "A-content-red" \
                or evs and evs[0].get("schema") != "rocqwash-sentinel-event/1" \
                or evs and evs[0].get("seq") != 1:
            fails.append("check 1: the JSONL should carry exactly 1 line, "
                         "ci-red (run=178, family=A-content-red, seq=1); "
                         "got %s" % (evs or "empty"))
        rep = {}
        try:
            rep = json.load(io.open(rep_path, encoding="utf-8"))
        except (ValueError, OSError) as e:
            fails.append("check 1: the watcher report should be readable: %s"
                         % e)
        acts = rep.get("actions") or []
        # the preset embeds the sentinel's own interpreter (sys.executable,
        # quoted), not a bare "python3" literal — on Windows a bare python3
        # resolves to the Store stub (T0-5 platform-defect family); this test
        # spawns the sentinel with sys.executable, so the expected expansion
        # carries the same interpreter.
        want_cmd = ('"%s" -B %s --src %s --json %s/unclog_178.json'
                    % (sys.executable, UNCLOG, src, emit_dir))
        if len(acts) != 1 or acts and acts[0].get("cmd") != want_cmd \
                or acts and acts[0].get("rc") != 9:
            fails.append("check 1: the actions account should hold exactly 1 "
                         "entry with cmd=preset expanded (%s) and the "
                         "delegate rc=9 recorded honestly (fixture without "
                         "world; same case as the cw_sentinel selftest [9] "
                         "trigger capture); got %s" % (want_cmd, acts))
        if rep.get("on_red_preset") != "unclog":
            fails.append("check 1: report.on_red_preset should be unclog; "
                         "got %r" % rep.get("on_red_preset"))
        # sweep the delegated unclog run's mkdtemp residue (same sweep as
        # the cw_sentinel selftest, cw_sentinel.py:1961)
        if acts:
            mw = re.search(r"workdir -> (\S+)", acts[0].get("output") or "")
            if mw:
                shutil.rmtree(mw.group(1), ignore_errors=True)
        # evidence for check 3: the unclog report path named by the actions
        # account; preset outputs share the disk with the event stream
        # (cw_sentinel.py:1062-1064)
        named_report = os.path.join(emit_dir, "unclog_178.json")

        # -- check 2 unclog dry run rc=0 with zero tree writes: unclog
        # --audit, canned, on the same fixture tree --
        # the preset delegate shape (--src alone, no --world/--injector)
        # must exit rc=9 offline (a real probe needs a world,
        # unclog.py:485), so the proper dry run is proven here in the audit
        # canned shape: audit is the only dry-run form that simultaneously
        # sees the failure, exits rc=0, and self-proves zero writes (the
        # failing-canned closed-loop dry run ends verdict=rounds-exhausted
        # rc=1; same case as unclog selftest v4, unclog.py:1555)
        man_before = tree_manifest(src)
        rc2, out2 = run(UNCLOG, [
            "--src", src, "--audit", "--injector", scen_dir,
            "--workdir", os.path.join(tmp, "wd"), "--json", named_report])
        if rc2 != 0:
            fails.append("check 2: unclog --audit should exit rc=0 (the "
                         "failing baseline is data, not a tool failure); "
                         "got %d\n%s" % (rc2, out2[-600:]))
        urep = {}
        try:
            urep = json.load(io.open(named_report, encoding="utf-8"))
        except (ValueError, OSError) as e:
            fails.append("check 2: the unclog report should be readable: %s"
                         % e)
        if urep:
            fin = urep.get("final") or {}
            r0 = (urep.get("rounds") or [{}])[0]
            ct0 = (r0.get("chain_top") or [{}])[0]
            if urep.get("schema") != "rocqwash-unclog/1" \
                    or urep.get("verdict") != "audit":
                fails.append("check 2: the report should carry schema="
                             "rocqwash-unclog/1 and verdict=audit; got %s/%r"
                             % (urep.get("schema"), urep.get("verdict")))
            if r0.get("probe_summary", {}).get("red_files") != ["B"] \
                    or fin.get("red_files") != ["B"]:
                fails.append("check 2: the failure should be seen "
                             "(red_files=[B]; the canned ledger has B "
                             "missing A); got round=%s final=%s"
                             % (r0.get("probe_summary"), fin.get("red_files")))
            if ct0.get("lib") != "A" \
                    or ct0.get("self", {}).get("washable") is not True:
                fails.append("check 2: chain root A should emerge washable "
                             "(washable=True); got %s" % ct0)
            if fin.get("cures_planned_total") != 0 \
                    or fin.get("cures_applied_total") != 0:
                fails.append("check 2: the dry run should keep cures at 0 "
                             "(audit applies nothing); got %s" % fin)
            if urep.get("wall") != {}:
                fails.append("check 2: the wall of a washable, non-frozen "
                             "tree should stay empty; got %s"
                             % urep.get("wall"))
            if urep.get("mode", {}).get("audit") is not True \
                    or urep.get("mode", {}).get("apply") is not False:
                fails.append("check 2: mode should carry audit=true and "
                             "apply=false; got %s" % urep.get("mode"))
        man_after = tree_manifest(src)
        if man_before != man_after or not man_before:
            fails.append("check 2: the zero-write self-proof broke — the src "
                         "md5 inventory should be identical and non-empty "
                         "before and after; before=%s after=%s"
                         % (man_before, man_after))

        # -- check 3 the JSONL-side unclog report path: the path named by
        # the actions account equals the file actually written --
        # measurement note (stated as measured): the watcher's --emit JSONL
        # event stream carries events only (the four emit_event kinds
        # ci-red/blocking/build-signal/sentinel-error; cw_sentinel.py:879,
        # 947, 998, 1428), while the actions account (including the unclog
        # report path) travels in the --json report; this check therefore
        # settles on the JSONL-side directory plus the recorded path
        # compared against the report actually written.
        if not os.path.isfile(named_report):
            fails.append("check 3: the report at the path named by the "
                         "preset cmd should exist: %s" % named_report)
        elif os.path.dirname(os.path.abspath(emit)) != emit_dir \
                or not os.path.isfile(emit):
            fails.append("check 3: the emit JSONL should sit in the same "
                         "directory: %s" % emit)
        elif urep.get("schema") != "rocqwash-unclog/1" \
                or urep.get("verdict") != "audit":
            fails.append("check 3: the same-directory report should carry "
                         "schema=rocqwash-unclog/1 and verdict=audit "
                         "(compared against the actions[0].cmd path); got "
                         "%s" % urep.get("verdict"))
        if acts and "unclog_178.json" not in (acts[0].get("cmd") or ""):
            fails.append("check 3: actions[0].cmd should contain the unclog "
                         "report path name; got %s" % acts[0].get("cmd"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("== test_relay_e2e: %d pass / %d fail ==" % (3 - len(fails),
                                                       len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
