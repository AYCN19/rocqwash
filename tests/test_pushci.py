#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_pushci.py — scenario shell for tools/pushci.py, the push-CI single-command pipeline (rocqwash tests/).

Purpose.  Drive the pipeline (preflight check, push, watch, NETRED
  automatic recovery rerun, verdict, optional merge) end to end offline:
  seven scenario fixtures (tests/fixtures/pushci_scenarios/*.json) are
  injected through the implementation's native flat shape (fixture
  originals verbatim, canned keys accepted as-is), each judged on exit
  code, report.final, heal rounds, stage fields, and the call ledgers.

Interface.  bash tools/cpu_guard.sh -MaxWaitSec 120 --
  python3 -B tests/test_pushci.py      # suite lane `t_pushci`
  python3 -B tests/test_pushci.py      # manual (-B keeps __pycache__ off)

Dependencies.  Python 3 standard library only; the real git binary only
  builds the tmp-repository fixture (init/add/commit/remote add; push
  never really runs); scenario-layer git goes through --git-caller canned
  injection exclusively; the remote URL is the unreachable fake domain
  pushci.invalid; --sleep-scale 0 always passed; --netrc always a
  nonexistent path (credential lazy-read proof).

Evidence.  Zero side effects asserted per run: HEAD sha and status
  --porcelain unchanged byte-for-byte before/after; api_calls.json
  compared bit-for-bit with the canned-derived sequence (missing, extra,
  misordered all fail); scenarios rerun twice, reports byte-identical
  (drift confined to wall-clock-class keys); wired in November 11, 2026.

Exit-codes.  0 = all eleven sections pass; 1 = any section failing
  (fail-loud: every failing section listed with its file:line).
"""

# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard).  Report schema
# rocqwash-pushci/1; the contract verdict set is the seven states success /
# fix-content / toolchain / unstable / heal-exhausted / gate4-block /
# dry-run; zero writes, zero real network, zero compilation.  Section
# roster, numbered by execution order:
#   1 tool selftest       pushci --selftest frozen vector (rc 0,
#                         PUSHCI-SELFTEST PASS)
#   2 helper selftest     tmp-git repository fixture: real git only the
#                         init/add/commit/remote-add layer (the repo is
#                         built by the fixture; push never really runs —
#                         scenario-layer git all goes through the
#                         --git-caller canned form)
#   3 S1 green path       preflight two checks (flat shape default
#                         passing, loud annotation registered) -> push
#                         injected (get-url/rev-parse/push/ls-remote four
#                         calls, remote-authoritative) -> watch 2 rounds
#                         run success -> verdict success exit 0; zero
#                         heal (rounds empty, last_triage None), zero merge
#   4 S2 NETRED heal      attempt1 failure NETRED (family B,
#                         canned.jobs[0] real classification) -> probe
#                         STABLE (canned.probe[0]) -> rerun 201 (run_id
#                         locked) -> attempt2 success -> verdict success
#                         exit 0; heal_rounds == 1
#   5 S3 content red      failure A-content-red -> verdict fix-content
#                         exit 2; zero-rerun proof = report.heal.rounds
#                         empty (the contract's original wording) +
#                         fired_total == 0 + api_calls zero POST; the
#                         classification registered in heal.last_triage
#   6 S4 heal exhausted   NETRED x 3 (--max-heal 2; canned.jobs three
#                         entries consumed per classification; two rounds
#                         probe STABLE -> rerun 201 still NETRED) ->
#                         verdict heal-exhausted exit 1
#   7 S5 merge flow       run success -> PUT merge 200 (--pr 42; the flat
#                         shape passes pulls GET explicitly) ->
#                         report.merge.merge_sha non-empty exit 0
#   8 S6 dry run          --dry-run plan output; zero API calls
#                         (api_calls.json == []) and zero git calls
#                         (calls.json == []) -> verdict dry-run exit 0
#   9 S7 main form        --branch main (the refs/heads/main direct-push
#                         route; the multi-repo Main-adaptation survey
#                         record of November 12, 2026, section 3.2)
#                         --dry-run: plan output carries the
#                         preflight three-check plan lines
#                         (toolchain/net/gate4) and the [2] push plan line
#                         (HTTP/1.1 + branch main); zero API calls, zero
#                         git calls, zero side effects -> verdict dry-run
#                         exit 0
#  10 idempotence         seven scenarios each run twice (same repository,
#                         same canned): report bytes identical; any drift
#                         leaf must fall in wall-clock-class narrow key
#                         names (otherwise failing; silent widening banned)
#  11 CLI five codes      --help 0; unknown flag 2; missing required 2;
#                         repo missing 9; injector git-caller one-sided 2
# Mapping layer (fixture -> injector, thin): fixture originals copied
# verbatim to DIR/scenario.json (the implementation's flat shape accepts
# canned keys as-is; schema/summary/argv/expect unknown keys are ignored by
# the implementation); the git-caller canned is derived from the fixture
# head_sha and branch (four-call order = the implementation's actual call
# order); expected_api_sequence is derived purely from canned (one GET per
# round, same-round rerun, final-round merge) and compared bit-for-bit with
# api_calls.json.
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUSHCI = os.path.join(REPO, "tools", "pushci.py")
FIXDIR = os.path.join(REPO, "tests", "fixtures", "pushci_scenarios")
SCHEMA = "rocqwash-pushci/1"

# canned test domain (shared by implementation and fixtures: fake-domain
# remote; ORG/REPO derived from the last two URL segments; structurally
# zero network)
TEST_REPO = "octo-org/rocqwash-verify"
REMOTE_URL = "https://pushci.invalid/%s.git" % TEST_REPO
RUNS_PATH = "/repos/%s/actions/runs?per_page=30" % TEST_REPO

# the contract verdict set, seven states (designated by the tool contract;
# never widened)
VERDICTS = ("success", "fix-content", "toolchain", "unstable",
            "heal-exhausted", "gate4-block", "dry-run")

SCENARIOS = ["s1_green_path", "s2_netred_heal", "s3_content_red",
             "s4_heal_exhausted", "s5_merge_flow", "s6_dry_run",
             "s7_main_dry_run"]

# wall-clock-class key names (the exempted face of the idempotence
# judgment; the narrow class is never widened: only these keys may drift
# across runs)
WALLCLOCK_KEY_RX = re.compile(
    r"(^|_)(at|time|timestamp|generated|wallclock|now|iso|date)(_t)?$|_at$", re.I)

INJ_TIMEOUT_SEC = 60   # per-scenario subprocess wall-clock cap (timeout = failing; guards against a canned-mismatch spin)


# ---- small shared helpers ---------------------------------------------------

def real_git():
    """The real git binary (resolved from PATH; no hardcoded absolute
    paths).  Fails loudly when absent."""
    g = shutil.which("git")
    if not g:
        raise RuntimeError("git not on PATH (the tmp-git helper real-git layer is init/commit only)")
    return g


def run(argv, env=None, timeout=INJ_TIMEOUT_SEC):
    """Run a subprocess (stdout+stderr merged; timeout = failing)."""
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=env, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def load_json(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path, obj):
    """Deterministic write (sort_keys; used for the git-caller scenario
    file; follows the house write convention)."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)


def load_scenario(name):
    return load_json(os.path.join(FIXDIR, name + ".json"))


def base_env():
    """Credential clean room: the test subprocess never carries a real
    token (the network face is separately proven through the lazy read of
    a missing --netrc path)."""
    env = dict(os.environ)
    for k in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN"):
        env.pop(k, None)
    return env


# ---- tmp-git repository fixture (real git for the init/add/commit/remote layer only) -

def make_tmp_repo(root, name, branch, remote_url):
    """git init -b <branch> + add + commit + remote add origin.  The
    push/ls-remote/fetch real calls never launch — scenario-layer git all
    goes through the --git-caller canned form (implementation injection
    point 1) and the remote URL is always the fake domain (structurally
    unreachable)."""
    repo = os.path.join(root, name)
    git = real_git()
    cfg = ["-c", "user.name=pushci-test", "-c", "user.email=pushci@test.invalid"]
    rc, out = run([git, "init", "-q", "-b", branch, repo])
    assert rc == 0, "git init expected rc 0: %s" % out
    with io.open(os.path.join(repo, "pushci_probe.txt"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write("branch=%s\n" % branch)
    rc, out = run([git, "-C", repo] + cfg + ["add", "pushci_probe.txt"])
    assert rc == 0, "git add expected rc 0: %s" % out
    rc, out = run([git, "-C", repo] + cfg + ["commit", "-q", "-m", "pushci fixture"])
    assert rc == 0, "git commit expected rc 0: %s" % out
    rc, out = run([git, "-C", repo, "remote", "add", "origin", remote_url])
    assert rc == 0, "git remote add expected rc 0: %s" % out
    return repo


def head_and_status(repo):
    """Repository snapshot (HEAD sha + porcelain) for the zero-side-effect
    criterion (real git, read-only)."""
    git = real_git()
    rc, out = run([git, "-C", repo, "rev-parse", "HEAD"])
    assert rc == 0, "rev-parse HEAD expected rc 0: %s" % out
    rc2, out2 = run([git, "-C", repo, "status", "--porcelain"])
    assert rc2 == 0, "status expected rc 0: %s" % out2
    return out.strip(), out2


# ---- mapping layer: fixture -> injector (flat verbatim) + git-caller scenario -

def rerun_round_map(scen):
    """rerun[j] -> round j+1 (the j+1-th watch round observed NETRED;
    same-round triage -> probe -> rerun)."""
    return {j + 1: rr for j, rr in enumerate(scen["canned"]["rerun"])}


def build_injector(scen, inj_dir, git_json_path):
    """Thin mapping layer: fixture original verbatim -> DIR/scenario.json
    (the implementation's flat shape accepts canned keys as-is;
    schema/scenario/summary/argv/expect unknown keys are ignored by the
    implementation); the git-caller scenario is derived from the fixture
    head_sha/branch.  Returns the git-caller scenario path."""
    os.makedirs(inj_dir)
    shutil.copyfile(os.path.join(FIXDIR, scen["scenario"] + ".json"),
                    os.path.join(inj_dir, "scenario.json"))
    dump_json(git_json_path, {"responses": build_git_responses(scen)})
    return git_json_path


def build_git_responses(scen):
    """git-caller canned (four-call order = the implementation's actual
    call order): get-url -> rev-parse (local tip) -> push -> ls-remote
    (remote-tip confirmation, remote-authoritative).  Dry run makes zero
    calls (empty list)."""
    if scen["argv"]["dry_run"]:
        return []
    return [
        {"args_contains": ["get-url"], "rc": 0, "stdout": REMOTE_URL + "\n"},
        {"args_contains": ["rev-parse"], "rc": 0,
         "stdout": scen["head_sha"] + "\n"},
        {"args_contains": ["push"], "rc": 0, "stdout": "To %s\n" % REMOTE_URL},
        {"args_contains": ["ls-remote"], "rc": 0,
         "stdout": "%s\trefs/heads/%s\n" % (scen["head_sha"], scen["branch"])},
    ]


def expected_api_sequence(scen):
    """The expected API ledger derived purely from canned (one GET per
    round, same-round rerun, final-round merge) -> compared bit-for-bit
    with api_calls.json (the round-scripted proof criterion)."""
    canned = scen["canned"]
    rmap = rerun_round_map(scen)
    n = len(canned["runs"])
    seq = []
    for r in range(1, n + 1):
        seq.append({"round": r, "method": "GET", "path": RUNS_PATH, "status": 200})
        rr = rmap.get(r)
        if rr:
            run_id = canned["runs"][r - 1]["workflow_runs"][0]["id"]
            seq.append({"round": r, "method": "POST",
                        "path": "/repos/%s/actions/runs/%s/rerun"
                                % (TEST_REPO, run_id),
                        "status": rr["status"]})
    if canned["merge"] is not None:
        seq.append({"round": n, "method": "PUT",
                    "path": "/repos/%s/pulls/%s/merge"
                            % (TEST_REPO, scen["argv"]["pr"]),
                    "status": canned["merge"]["status"]})
    return seq


# ---- CLI assembly (contract flags) ------------------------------------------

def pushci_argv(scen, inj_dir, git_json, repo, report_path, netrc_missing):
    """--repo-path/--branch/--injector DIR/--git-caller/--sleep-scale
    0/--json plus the scenario extras (--merge/--pr/--max-heal/--dry-run).
    --steps defaults to all steps (the contract shape is registered;
    scenarios always run the full pipeline).  --netrc always points at a
    nonexistent path = the credential lazy-read proof."""
    argv = [sys.executable, "-B", PUSHCI,
            "--repo-path", repo,
            "--branch", scen["branch"],
            "--remote", "origin",
            "--injector", inj_dir,
            "--git-caller", git_json,
            "--netrc", netrc_missing,
            "--sleep-scale", "0",
            "--json", report_path]
    a = scen["argv"]
    if a.get("max_heal") is not None:
        argv += ["--max-heal", str(a["max_heal"])]
    if a.get("merge"):
        argv += ["--merge", "--pr", str(a["pr"])]
    if a.get("dry_run"):
        argv += ["--dry-run"]
    return argv


# ---- report field access (contract semantics fixed; paths follow the implementation's actual shape) -

def report_fields(rep):
    """verdict (seven states) / final{conclusion,verdict} /
    heal{rounds = the fired ledger, fired_total, last_triage} /
    merge{pr,merged,merge_sha} / watch{rounds,run_id,conclusion} /
    preflight/push/plan/mode."""
    st = rep.get("stages") or {}
    return {
        "verdict": rep.get("verdict"),
        "final": rep.get("final") or {},
        "heal": st.get("heal"),
        "merge": st.get("merge"),
        "watch": st.get("watch") or {},
        "preflight": st.get("preflight") or {},
        "push": st.get("push") or {},
        "plan": rep.get("plan"),
        "mode": rep.get("mode"),
    }


# ---- scenario execution ------------------------------------------------------

def run_scenario(scen, root, tag, repo=None, netrc_missing=None):
    """One scenario, one run: the injector (flat verbatim) + git-caller
    scenario built, then the pushci subprocess, then the result ledger.
    The repo can be reused (the two idempotence runs share one repository
    and one canned)."""
    if repo is None:
        repo = make_tmp_repo(root, "repo_%s_%s" % (tag, scen["scenario"]),
                             scen["branch"], REMOTE_URL)
    inj_dir = os.path.join(root, "inj_%s_%s" % (tag, scen["scenario"]))
    git_json = os.path.join(root, "git_%s_%s.json" % (tag, scen["scenario"]))
    build_injector(scen, inj_dir, git_json)
    before = head_and_status(repo)
    report_path = os.path.join(root, "report_%s_%s.json" % (tag, scen["scenario"]))
    argv = pushci_argv(scen, inj_dir, git_json, repo, report_path,
                       netrc_missing or os.path.join(root, "absent.netrc"))
    rc, out = run(argv, env=base_env())
    after = head_and_status(repo)
    calls_path = git_json[:-len(".json")] + ".calls.json"
    git_calls = load_json(calls_path) if os.path.isfile(calls_path) else None
    api_path = os.path.join(inj_dir, "api_calls.json")
    api_calls = load_json(api_path) if os.path.isfile(api_path) else None
    report = load_json(report_path) if os.path.isfile(report_path) else None
    return {"rc": rc, "stdout": out, "report": report, "report_path": report_path,
            "git_calls": git_calls, "api_calls": api_calls,
            "before": before, "after": after, "repo": repo, "argv": argv,
            "inj_dir": inj_dir}


def assert_common(scen, res):
    """Per-scenario common assertions: exit code / schema / mode / verdict
    / final / repository zero side effects."""
    exp = scen["expect"]
    assert res["rc"] == exp["exit"], "exit expected %d, observed %d\nstdout=%s" % (
        exp["exit"], res["rc"], res["stdout"][-900:])
    assert res["report"] is not None, "report not written (--json should produce the ledger)\n%s" % \
        res["stdout"][-900:]
    rep = res["report"]
    assert rep.get("schema") == SCHEMA, \
        "report schema expected %s, observed %r" % (SCHEMA, rep.get("schema"))
    f = report_fields(rep)
    assert f["verdict"] in VERDICTS, "verdict must be one of the contract's seven states, observed %r" % f["verdict"]
    assert f["verdict"] == exp["verdict"], \
        "verdict expected %s, observed %s\nstdout=%s" % (exp["verdict"], f["verdict"],
                                                         res["stdout"][-600:])
    assert f["final"].get("verdict") == exp["verdict"], \
        "report.final.verdict expected %s, observed %r" % (exp["verdict"], f["final"])
    assert f["final"].get("conclusion") == exp["final_conclusion"], \
        "report.final.conclusion expected %r, observed %r" % (exp["final_conclusion"],
                                                              f["final"].get("conclusion"))
    assert res["before"] == res["after"], \
        "repository drift = side-effect violation: before=%r after=%r" % (res["before"], res["after"])
    return f


def assert_call_ledgers(scen, res):
    """Call-ledger comparison: api_calls must equal the canned-derived
    expectation bit-for-bit; the git_calls count must match the four-call
    injected shape (get-url -> rev-parse -> push -> ls-remote, all rc 0;
    dry run zero calls)."""
    exp = scen["expect"]
    assert res["api_calls"] is not None, "api_calls.json not written (the injector proof face is missing)"
    assert res["api_calls"] == expected_api_sequence(scen), \
        "API ledger mismatch against the canned-derived expected sequence:\n expected=%r\n observed=%r" % (
            expected_api_sequence(scen), res["api_calls"])
    assert len(res["api_calls"]) == exp["api_calls"], \
        "API call count expected %d, observed %d" % (exp["api_calls"], len(res["api_calls"]))
    assert res["git_calls"] is not None, "calls.json not written (the git-injection proof face is missing)"
    assert len(res["git_calls"]) == exp["git_calls"], \
        "git call count expected %d, observed %d: %r" % (exp["git_calls"], len(res["git_calls"]),
                                                         res["git_calls"])
    for g in res["git_calls"]:
        assert g.get("rc") == 0, "canned git calls must carry rc=0: %r" % g
    if not scen["argv"]["dry_run"]:
        push_call, confirm_call = res["git_calls"][2], res["git_calls"][3]
        assert "push" in push_call["args"] \
            and "http.version=HTTP/1.1" in push_call["args"], \
            "the push layer must be registered with http.version=HTTP/1.1 (the implementation's push shape): %r" % push_call
        assert "ls-remote" in confirm_call["args"] \
            and ("refs/heads/%s" % scen["branch"]) in confirm_call["args"], \
            "the post-push ls-remote confirmation must be registered (remote-authoritative): %r" % confirm_call


def check_s1(scen, res):
    f = assert_common(scen, res)
    exp = scen["expect"]
    assert_call_ledgers(scen, res)
    # the two preflight checks (flat shape default passing; loud annotation registered)
    assert f["preflight"].get("toolchain") == {"verdict": "healthy", "rc": 0}, \
        "preflight.toolchain expected healthy/0, observed %r" % f["preflight"].get("toolchain")
    assert f["preflight"].get("net") == {"verdict": "STABLE", "rc": 0}, \
        "preflight.net expected STABLE/0, observed %r" % f["preflight"].get("net")
    assert any("flat injection shape" in e for e in
               (res["report"].get("evidence") or [])), \
        "the flat-shape preflight default pass must carry its loud annotation: %r" % res["report"].get("evidence")
    # push stage: sha = remote tip (ls-remote confirmation, remote-authoritative);
    # single attempt rc 0; no ghproxy
    assert f["push"].get("sha") == scen["head_sha"], \
        "push.sha expected the remote-tip sha, observed %r" % f["push"].get("sha")
    assert f["push"].get("attempts") == [{"target": "origin", "rc": 0}], \
        "push.attempts expected a single attempt rc 0, observed %r" % f["push"].get("attempts")
    assert f["push"].get("ghproxy_used") is False, "the green path must not route through ghproxy"
    # watch stage: 2 rounds run success
    assert f["watch"].get("rounds") == exp["watch_rounds"], \
        "watch.rounds expected %d, observed %r" % (exp["watch_rounds"],
                                                   f["watch"].get("rounds"))
    assert f["watch"].get("run_id") == exp["run_id"], \
        "watch.run_id expected %r, observed %r" % (exp["run_id"], f["watch"].get("run_id"))
    assert f["watch"].get("conclusion") == "success", \
        "watch.conclusion expected success, observed %r" % f["watch"].get("conclusion")
    # zero heal (rounds empty, last_triage None) + zero merge
    assert f["heal"] == {"rounds": [], "fired_total": 0, "last_triage": None}, \
        "S1 zero-heal proof: the heal stage must be an empty ledger, observed %r" % (f["heal"],)
    assert f["merge"] is None, "merge not enabled: no merge stage expected, observed %r" % (f["merge"],)
    return ("S1 green path (exit 0, verdict success, the preflight two-check "
            "annotation, the push four-call injection, remote-authoritative, "
            "zero heal zero merge)")


def check_s2(scen, res):
    f = assert_common(scen, res)
    exp = scen["expect"]
    assert_call_ledgers(scen, res)
    h = f["heal"] or {}
    assert len(h.get("rounds") or []) == exp["heal_rounds"], \
        "heal_rounds expected ==%d, observed %r" % (exp["heal_rounds"], h.get("rounds"))
    r0 = (h.get("rounds") or [{}])[0]
    assert r0.get("round") == 1 and r0.get("family") == "B-netred", \
        "the heal round must be B-netred, observed %r" % r0
    assert r0.get("action") == "rerun-after-stable-window", \
        "the heal action expected rerun-after-stable-window, observed %r" % r0.get("action")
    assert r0.get("probe") == "STABLE", \
        "the heal probe expected STABLE (canned.probe[0]; the rerun is allowed only after the two-probe stable window), observed %r" % \
        r0.get("probe")
    assert r0.get("fired") is True and r0.get("http") == 201, \
        "the rerun must have fired (fired/http=201), observed %r" % r0
    assert h.get("fired_total") == 1, "fired_total expected 1, observed %r" % h.get("fired_total")
    assert (h.get("last_triage") or {}).get("family") == "B-netred", \
        "last_triage expected B-netred, observed %r" % h.get("last_triage")
    assert f["watch"].get("rounds") == exp["watch_rounds"], \
        "watch.rounds expected %d, observed %r" % (exp["watch_rounds"],
                                                   f["watch"].get("rounds"))
    assert f["watch"].get("run_id") == exp["run_id"], \
        "attempt2 reuses the same run id (the rerun path), expected %r, observed %r" % (
            exp["run_id"], f["watch"].get("run_id"))
    posts = [c for c in res["api_calls"] if c["method"] == "POST"]
    assert len(posts) == 1 and "/rerun" in posts[0]["path"], \
        "exactly one rerun POST, observed %r" % posts
    return "S2 NETRED heal (heal_rounds == 1, probe STABLE -> rerun 201 -> attempt2 success)"


def check_s3(scen, res):
    f = assert_common(scen, res)
    assert_call_ledgers(scen, res)
    h = f["heal"] or {}
    # the contract's original wording: the zero-rerun proof is report.heal.rounds empty
    assert h.get("rounds") == [], \
        "zero-rerun proof 1: report.heal.rounds must be empty, observed %r" % (h.get("rounds"),)
    assert h.get("fired_total") == 0, \
        "zero-rerun proof 2: fired_total must be 0, observed %r" % h.get("fired_total")
    posts = [c for c in res["api_calls"] if c["method"] == "POST"]
    assert posts == [], \
        "zero-rerun proof 3: api_calls must carry zero POSTs, observed %r" % posts
    lt = h.get("last_triage") or {}
    assert lt.get("family") == "A-content-red" \
        and lt.get("action") == "fix-content", \
        "the content-red classification must be A-content-red/fix-content (last_triage), observed %r" % lt
    assert any("zero rerun" in e for e in
               ((res["report"].get("evidence") or [])
                + list(lt.get("evidence") or []))), \
        "the zero-rerun evidence must be registered loudly: %r" % res["report"].get("evidence")
    return ("S3 content red (verdict fix-content, exit 2, the zero-rerun triple "
            "proof heal.rounds empty / fired_total=0 / zero API POSTs, the "
            "classification registered in last_triage)")


def check_s4(scen, res):
    f = assert_common(scen, res)
    exp = scen["expect"]
    assert_call_ledgers(scen, res)
    h = f["heal"] or {}
    assert len(h.get("rounds") or []) == exp["heal_rounds"], \
        "heal.rounds expected %d (the --max-heal 2 cap), observed %r" % (exp["heal_rounds"],
                                                                         h.get("rounds"))
    assert h.get("fired_total") == exp["heal_rounds"], \
        "fired_total expected %d, observed %r" % (exp["heal_rounds"], h.get("fired_total"))
    assert all(r.get("fired") is True and r.get("http") == 201
               and r.get("family") == "B-netred"
               for r in (h.get("rounds") or [])), \
        "both heal rounds B-netred -> probe STABLE -> rerun 201, observed %r" % (h.get("rounds"),)
    assert (h.get("last_triage") or {}).get("family") == "B-netred", \
        "last_triage expected B-netred, observed %r" % h.get("last_triage")
    assert f["watch"].get("rounds") == exp["watch_rounds"], \
        "watch.rounds expected %d (three NETRED rounds), observed %r" % (
            exp["watch_rounds"], f["watch"].get("rounds"))
    assert any("cap reached" in e for e in (res["report"].get("evidence") or [])), \
        "the cap-reached evidence must be registered loudly: %r" % res["report"].get("evidence")
    return "S4 heal exhausted (NETRED x 3, --max-heal 2, verdict heal-exhausted, exit 1)"


def check_s5(scen, res):
    f = assert_common(scen, res)
    exp = scen["expect"]
    assert_call_ledgers(scen, res)
    m = f["merge"] or {}
    assert m.get("pr") == exp["pr_number"], \
        "merge.pr expected %r, observed %r" % (exp["pr_number"], m.get("pr"))
    assert m.get("merged") is True, "merge.merged expected true, observed %r" % m.get("merged")
    assert m.get("attempts") == [200], \
        "the PUT merge expected a single 200 attempt, observed %r" % m.get("attempts")
    assert m.get("merge_sha"), \
        "report.merge.merge_sha must be non-empty, observed %r" % (m.get("merge_sha"),)
    assert m.get("merge_sha") == exp["merge_sha"], \
        "merge_sha expected the canned %s, observed %s" % (exp["merge_sha"], m.get("merge_sha"))
    puts = [c for c in res["api_calls"] if c["method"] == "PUT"]
    assert len(puts) == 1 \
        and "/pulls/%d/merge" % exp["pr_number"] in puts[0]["path"], \
        "exactly one PUT merge, observed %r" % puts
    return "S5 merge flow (PUT 200, merge_sha pinned, exit 0)"


def check_s6(scen, res):
    f = assert_common(scen, res)
    assert f["mode"] == "dry-run", "mode expected dry-run, observed %r" % f["mode"]
    assert f["plan"], "a dry run must produce plan output (report.plan non-empty)"
    assert res["git_calls"] == [], \
        "S6 zero-git-call proof: calls.json empty, observed %r" % res["git_calls"]
    assert res["api_calls"] == [], \
        "S6 zero-API-call proof: api_calls.json empty, observed %r" % res["api_calls"]
    assert res["stdout"].strip(), "a dry run must produce plan stdout"
    assert "PLAN [2] push" in res["stdout"], \
        "the plan must carry the push stage line: %s" % res["stdout"][-500:]
    assert scen["branch"] in res["stdout"], \
        "the plan output must carry the branch name (the plan proof): %s" % res["stdout"][-500:]
    return "S6 dry run (zero API and zero git calls proven by the ledgers, the plan registered, verdict dry-run, exit 0)"


def check_s7(scen, res):
    f = assert_common(scen, res)
    assert f["mode"] == "dry-run", "mode expected dry-run, observed %r" % f["mode"]
    assert f["plan"], "a dry run must produce plan output (report.plan non-empty)"
    # the preflight three-check plan lines registered (toolchain/net/gate4; in
    # the main form the gate family is attested line by line in the plan face —
    # gate4 default-off is the correct default for the refs/heads/main
    # direct-push route, where the base...branch diff degenerates; the
    # multi-repo Main-adaptation survey record of November 12, 2026, section
    # 3.2 and section 5 item 4. Note report.plan stores bare lines; the
    # "PLAN " prefix is added only when stdout is rendered)
    assert any("[1] preflight.toolchain" in ln for ln in f["plan"]), f["plan"]
    assert any("[1] preflight.net" in ln for ln in f["plan"]), f["plan"]
    assert any("[1] preflight.gate4" in ln and "not enabled" in ln
               for ln in f["plan"]), f["plan"]
    # the push plan line: the HTTP/1.1 push shape + branch main (the
    # refs/heads/main direct-push route)
    assert any("[2] push" in ln and "HTTP/1.1" in ln and " main" in ln
               for ln in f["plan"]), f["plan"]
    # the main form lock: report.args.branch == "main"
    assert res["report"]["args"]["branch"] == "main", res["report"]["args"]
    # zero-side-effect ledger proof: zero git calls and zero API calls
    # (calls.json and api_calls.json both empty)
    assert res["git_calls"] == [], \
        "S7 zero-git-call proof: calls.json empty, observed %r" % res["git_calls"]
    assert res["api_calls"] == [], \
        "S7 zero-API-call proof: api_calls.json empty, observed %r" % res["api_calls"]
    assert res["stdout"].strip(), "a dry run must produce plan stdout"
    assert "PLAN [2] push" in res["stdout"], \
        "the plan must carry the push stage line: %s" % res["stdout"][-500:]
    assert scen["branch"] in res["stdout"], \
        "the plan output must carry the branch name main (the plan proof): %s" % res["stdout"][-500:]
    return ("S7 main form dry run (branch=main, the preflight three-check plan "
            "lines registered, the push plan line HTTP/1.1 + main, zero API and "
            "zero git calls proven by the ledgers, zero side effects)")


CHECKS = {
    "s1_green_path": check_s1,
    "s2_netred_heal": check_s2,
    "s3_content_red": check_s3,
    "s4_heal_exhausted": check_s4,
    "s5_merge_flow": check_s5,
    "s6_dry_run": check_s6,
    "s7_main_dry_run": check_s7,
}


# ---- idempotence (byte-identity first, the wall-clock narrow-class exception) -

def diff_paths(a, b, prefix=""):
    """Leaf-by-leaf structural diff of two JSON values -> the list of
    differing leaf paths."""
    out = []
    if type(a) is not type(b):
        return [prefix or "<root>"]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(prefix + "/" + k)
            else:
                out.extend(diff_paths(a[k], b[k], prefix + "/" + k))
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append("%s[len %d vs %d]" % (prefix, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(diff_paths(x, y, "%s[%d]" % (prefix, i)))
    elif a != b:
        out.append(prefix or "<root>")
    return out


def idempotence_verdict(path_a, path_b):
    """The two-run report idempotence judgment -> (ok, note).  Byte-identity
    ranks first; otherwise every differing leaf must fall in wall-clock-class
    narrow key names (the contract's exempted face; any other drift
    fails)."""
    ba = io.open(path_a, "rb").read()
    bb = io.open(path_b, "rb").read()
    if ba == bb:
        return True, "byte-identical"
    diffs = diff_paths(load_json(path_a), load_json(path_b))
    bad = [d for d in diffs
           if not WALLCLOCK_KEY_RX.search(d.rsplit("/", 1)[-1].split("[")[0])]
    if bad:
        return False, "non-wall-clock differing leaves: %r" % bad
    return True, "only wall-clock-class leaves drifted (%d leaves) -> per the contract, verdict and the structural key set are compared" % len(diffs)


def _keyset(obj, prefix=""):
    """The structural key set (recursive; the idempotence comparison face)."""
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(prefix + "/" + k)
            keys |= _keyset(v, prefix + "/" + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            keys |= _keyset(v, "%s[%d]" % (prefix, i))
    return keys


# ---- sections ----------------------------------------------------------------

def guard(section, fails, fn):
    """Section execution shell: exceptions caught -> the failing ledger
    (file:line located, fail-loud, never swallowed)."""
    try:
        return fn(), None
    except Exception as exc:  # noqa: BLE001 — every exception is recorded and reported loudly (never silent)
        msg = exc.args[0] if exc.args else str(exc)
        if not isinstance(exc, AssertionError):
            msg = "non-assertion exception %s: %s" % (type(exc).__name__, msg)
        fails.append((section, sys.exc_info(), msg))
        return None, exc


def sec_selftest(fails):
    def _go():
        rc, out = run([sys.executable, "-B", PUSHCI, "--selftest"])
        assert rc == 0, "pushci --selftest expected rc=0, observed %d\n%s" % (rc, out[-900:])
        assert "PUSHCI-SELFTEST PASS" in out, \
            "stdout missing the frozen marker\n%s" % out[-900:]
        return "selftest frozen vector passing (PUSHCI-SELFTEST PASS)"
    return guard("sec1_selftest", fails, _go)[0]


def sec_helper(fails):
    def _go():
        tmp = tempfile.mkdtemp(prefix="pushci_helper_")
        try:
            repo = make_tmp_repo(tmp, "r1", "topic-helper",
                                 "https://pushci.invalid/octo-org/"
                                 "rocqwash-verify.git")
            head, porc = head_and_status(repo)
            assert len(head) == 40 and porc == "", \
                "the tmp repository must be a single-commit clean tree: head=%r porc=%r" % (head, porc)
            git = real_git()
            rc, out = run([git, "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"])
            assert rc == 0 and out.strip() == "topic-helper", \
                "the branch must be the fixture branch: %s" % out
            rc, out = run([git, "-C", repo, "remote", "get-url", "--push",
                           "origin"])
            assert rc == 0 and out.strip() == \
                "https://pushci.invalid/octo-org/rocqwash-verify.git", \
                "the remote must be the canned fake-domain form (structurally zero real network): %s" % out
            return ("tmp-git helper passing (real git for the init/add/commit/"
                    "remote layer only; the push layer is injected by the "
                    "scenario --git-caller; the remote fake domain is "
                    "structurally unreachable)")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return guard("sec2_helper", fails, _go)[0]


def sec_scenarios(fails, root):
    notes = []
    for name in SCENARIOS:
        scen = load_scenario(name)

        def _go():
            return CHECKS[name](scen, run_scenario(scen, root, "run1"))

        note, _ = guard(name, fails, _go)
        notes.append(note)
    return notes


def sec_idempotence(fails, root):
    notes = []
    for name in SCENARIOS:
        scen = load_scenario(name)

        def _go():
            repo = make_tmp_repo(root, "repo_idem_%s" % name, scen["branch"],
                                 REMOTE_URL)
            r1 = run_scenario(scen, root, "idem1", repo=repo)
            r2 = run_scenario(scen, root, "idem2", repo=repo)
            exp = scen["expect"]
            assert r1["rc"] == r2["rc"] == exp["exit"], \
                "both runs must exit %d (observed %d/%d)" % (exp["exit"], r1["rc"], r2["rc"])
            assert r1["report"] is not None and r2["report"] is not None, \
                "both runs must write the report"
            ok, note = idempotence_verdict(r1["report_path"], r2["report_path"])
            assert ok, "idempotence failing: %s" % note
            f1 = report_fields(r1["report"])
            f2 = report_fields(r2["report"])
            assert f1["verdict"] == f2["verdict"] == exp["verdict"], \
                "both runs' verdict identical and in contract: %r vs %r" % (f1["verdict"], f2["verdict"])
            assert _keyset(r1["report"]) == _keyset(r2["report"]), \
                "both runs' report structural key sets identical"
            return "%s two-run idempotence (%s)" % (name, note)

        note, _ = guard("idem_" + name, fails, _go)
        notes.append(note)
    return notes


def sec_cli_codes(fails):
    def _go():
        tmp = tempfile.mkdtemp(prefix="pushcli_codes_")
        try:
            rc, out = run([sys.executable, "-B", PUSHCI, "--help"])
            assert rc == 0 and "usage" in out, \
                "--help expected rc=0 with usage, observed %d\n%s" % (rc, out[-400:])
            rc, out = run([sys.executable, "-B", PUSHCI, "--bogus-flag"])
            assert rc == 2, "unknown flag expected rc=2, observed %d\n%s" % (rc, out[-400:])
            rc, out = run([sys.executable, "-B", PUSHCI])
            assert rc == 2, "missing required arguments expected rc=2, observed %d\n%s" % (rc, out[-400:])
            rc, out = run([sys.executable, "-B", PUSHCI, "--repo-path",
                           os.path.join(tmp, "no_repo"), "--branch", "x"])
            assert rc == 9, "missing repository expected rc=9, observed %d\n%s" % (rc, out[-400:])
            rc, out = run([sys.executable, "-B", PUSHCI, "--repo-path", tmp,
                           "--branch", "x", "--injector", os.path.join(tmp, "inj")])
            assert rc == 2, "one-sided injector expected rc=2, observed %d\n%s" % (rc, out[-400:])
            return "CLI five codes (help 0, unknown flag 2, missing required 2, repository missing 9, one-sided injector 2)"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return guard("sec_cli_codes", fails, _go)[0]


# ---- main flow ----------------------------------------------------------------

def frame_loc(exc_info):
    """Failing-example location: the deepest frame in this file ->
    file:line."""
    for fr in reversed(traceback.extract_tb(exc_info[2])):
        if os.path.abspath(fr.filename) == os.path.abspath(__file__):
            return "%s:%d" % (fr.filename, fr.lineno)
    return "%s:?" % os.path.basename(__file__)


def main():
    print("== test_pushci: pushci scenario shell (repo=%s) ==" % REPO)
    if not os.path.isfile(PUSHCI):
        print("FAIL-LOUD: tools/pushci.py missing — the scenario sections cannot run (fail-loud)")
        return 1
    fails = []
    notes = []
    tmp = tempfile.mkdtemp(prefix="rocqwash_pushci_test_")
    try:
        notes.append(sec_selftest(fails))
        notes.append(sec_helper(fails))
        notes.extend(sec_scenarios(fails, tmp))
        notes.extend(sec_idempotence(fails, tmp))
        notes.append(sec_cli_codes(fails))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for n in notes if n)
    print("== test_pushci: %d passing / %d failing ==" % (passed, len(fails)))
    for n in notes:
        if n:
            print("PASS:", n)
    for label, exc, msg in fails:
        print("FAIL %s at %s: %s" % (label, frame_loc(exc), msg))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
