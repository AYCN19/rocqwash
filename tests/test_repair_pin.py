#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_repair_pin.py: suite hookup shell for tools/pin_repair.py (tests/).

Purpose.  Wires the provenance v2 pin repair executor (the R15 class of
  the recursive-era CI whitepaper, section 2: re-sign a drifted
  provenance pin only after the sync tool's zero-write plan verdicts
  IN-SYNC) into the suite entry; the apply-path seed carries verbatim
  standing seed entries (IN-SYNC by construction) plus fixture sources
  in the provenance v2 form; the exit-3 path rides a synthetic single
  entry the standing md table cannot cover.

Interface.  python3 tests/test_repair_pin.py (no arguments; suite entry).

Dependencies.  Standard library only; zero network; every fixture byte
  lives in the system temp dir (a fixture git repository holds the
  repo-pin faces); preflights read the standing sync verdict and the
  standing seed suite result read-only; no bytecode cache files are
  written, in this process or any subprocess tree.

Evidence.  The five vector faces are detailed in the contract block
  below the imports.

Exit-codes.  0 all executed vectors green (loud SKIP lines allowed); 1
  any vector red (fail-loud, listed); 2 usage.
"""

import argparse
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "pin_repair.py")
SYNC = os.path.join(REPO, "tools", "jargon_map_sync.py")
SEEDS = os.path.join(REPO, "tests", "t_engines_seeds.py")
LIVE_SEED = os.path.join(REPO, "seeds", "jargon", "jargon-map.json")
MAP_SCHEMA = "rocqwash-jargon-map/1"
SELFTEST_MARK = "PIN-REPAIR-SELFTEST PASS"
TIMEOUT = 300
# the whole subprocess tree writes no bytecode cache files
NO_PYC_ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

# Contract block (moved from the docstring to hold the 30-line header
# budget).  Fixture architecture: the CLI of the executor pins the
# judgment root to the tool's own repository, while these fixtures must
# judge a temporary git repository, so the plan/apply vectors call the
# executor's shared flow() in process with root set to the fixture repo
# (the same shape the executor's own selftest uses); subprocesses drive
# the tool's --selftest, the standing sync plan, the standing seed
# suite and the fixture gate.  Vector faces: (1) --selftest rc=0 with
# the frozen marker PIN-REPAIR-SELFTEST PASS; (2) plan over a drift
# fixture rc=0, action=plan, the drifted repo pin named in the v2
# fields (locator, pin kind, pinned blob sha vs HEAD blob sha, state),
# seed bytes untouched; (3) apply rc=0 with the repo pin re-signed to
# the working bytes' blob sha and every other seed byte unchanged,
# verify=seeds-suite-green; (4) plan over a not-in-sync fixture rc=3,
# ok=false, stage=plan, verdict recorded, zero write; (5) plan over an
# upstream-absent fixture rc=0 with the absent row carrying the pinned
# md5, the matched consistency and the declared skip notice;
# preflights degrade affected vectors to loud SKIP lines.


def run_tool(args):
    """One subprocess of the repair tool; stdout and stderr stay apart."""
    p = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       cwd=REPO, timeout=TIMEOUT, env=NO_PYC_ENV)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def run_readonly(cmd):
    """One read-only subprocess over a standing face; streams merged."""
    p = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8"] + cmd,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       cwd=REPO, timeout=TIMEOUT, env=NO_PYC_ENV)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def result_json(out):
    """The one-line result face: the last non-empty stdout line."""
    lines = [l for l in out.splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else None


def md5_bytes(data):
    return hashlib.md5(data).hexdigest()


def file_md5(path):
    with io.open(path, "rb") as fh:
        return md5_bytes(fh.read())


def read_bytes(path):
    with io.open(path, "rb") as fh:
        return fh.read()


def write_bytes(path, data):
    with io.open(path, "wb") as fh:
        fh.write(data)


def dump_seed(path, m):
    """Serialize a fixture seed the way the standing map is serialized:
    the file's own key order, indent 2, ensure_ascii off, trailing
    newline (the byte-stable form tools/pin_repair.py rewrites under)."""
    write_bytes(path, (json.dumps(m, ensure_ascii=False, indent=2)
                       + "\n").encode("utf-8"))


def load_tool():
    """The repair executor module, loaded by explicit path for the
    in-process plan/apply vectors.  Bytecode cache writes are disabled
    around the import so the repository gains no cache files."""
    saved = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(
            "pin_repair_under_test", TOOL)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = saved


def load_standing_entries():
    """The standing seed map, read once read-only (fixture premise only)."""
    with io.open(LIVE_SEED, encoding="utf-8") as fh:
        return json.load(fh)


def fixture_repo(tmp, prefix):
    """A throwaway git repository inside the temp directory: the sandbox
    the fixture repo pins are judged against.  git init/add/commit are
    local object-database operations; the whole fixture stays offline
    and no fixture byte lands in the real tree."""
    repo = os.path.join(tmp, prefix + "pinrepo")
    os.makedirs(repo)

    def git(*args):
        p = subprocess.run(["git"] + list(args), cwd=repo,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=TIMEOUT, env=NO_PYC_ENV)
        if p.returncode != 0:
            raise ValueError("fixture git %s failed: %s"
                             % (args[0],
                                p.stderr.decode("utf-8", "replace").strip()))
        return p.stdout.decode("utf-8", "replace").strip()

    git("init", "-q")
    git("config", "core.autocrlf", "false")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "fixture")
    return repo, git


class DriftFixture(object):
    """The fixture face shared by vectors 2, 3 and 5 (names only; the
    judgment reads the seed bytes)."""

    def __init__(self, seed_path, seed_bytes, repo, head_sha, stale_sha,
                 absent_rel, absent_pin):
        self.seed_path = seed_path
        self.seed_bytes = seed_bytes
        self.repo = repo
        self.head_sha = head_sha
        self.stale_sha = stale_sha
        self.absent_rel = absent_rel
        self.absent_pin = absent_pin


def drift_fixture(tmp, real, prefix, absent_upstream=False):
    """A seed fixture built per the contract adjudication, in the
    provenance v2 form: the standing seed's entries verbatim (the gate
    judges such a map IN-SYNC by construction) plus fixture sources
    judged in a fixture git repository.  Source one is a repo pin left
    at a stale blob sha (the drift under repair); source two is an
    external pin whose in-repo snapshot bytes, upstream original and
    pinned md5 agree; with absent_upstream the third source's upstream
    original does not exist on this machine (recorded absent with the
    declared notice, never fatal)."""
    repo, git = fixture_repo(tmp, prefix)
    repo_rel = "fixture-src.md"
    repo_abs = os.path.join(repo, repo_rel)
    committed = b"fixture repo source bytes\n"
    write_bytes(repo_abs, committed)
    git("add", repo_rel)
    git("commit", "-q", "-m", "fixture content")
    head_sha = git("rev-parse", "HEAD:" + repo_rel)
    stale_sha = hashlib.sha1(b"stale-pin-marker").hexdigest()
    if stale_sha == head_sha:
        raise ValueError("fixture construction: the stale blob sha equals"
                         " the fixture HEAD blob sha")
    snap_rel = "fixture-snapshot.md"
    upstream_v1 = b"fixture upstream bytes\n"
    write_bytes(os.path.join(tmp, prefix + "upstream.md"), upstream_v1)
    snap_v1 = b"fixture upstream bytes\n"
    write_bytes(os.path.join(repo, snap_rel), snap_v1)
    sources = [
        {"locator": "repo", "path": repo_rel,
         "role": "fixture source, pin stale",
         "pin": {"kind": "git-blob-sha", "value": stale_sha}},
        {"locator": "external", "path": snap_rel,
         "role": "fixture source, pin true",
         "upstream_path": os.path.join(tmp, prefix + "upstream.md"),
         "pin": {"kind": "md5", "value": md5_bytes(snap_v1)}},
    ]
    absent_rel = None
    absent_pin = None
    if absent_upstream:
        absent_rel = "fixture-snapshot-absent.md"
        absent_pin = md5_bytes(b"absent fixture snapshot bytes\n")
        write_bytes(os.path.join(repo, absent_rel),
                    b"absent fixture snapshot bytes\n")
        sources.append({"locator": "external", "path": absent_rel,
                        "role": "fixture source, upstream absent",
                        "upstream_path": os.path.join(
                            tmp, prefix + "upstream-absent.md"),
                        "pin": {"kind": "md5", "value": absent_pin}})
    fx = dict(real)
    fx["provenance"] = dict(real["provenance"])
    fx["provenance"]["sources"] = sources
    path = os.path.join(tmp, prefix + "seed.json")
    dump_seed(path, fx)
    data = read_bytes(path)
    # the stale 40-hex pin names exactly the drifted repo source, and it
    # must occur once so the byte-level re-sign check below can replace
    # it; the head sha must not occur yet
    if data.count(stale_sha.encode("ascii")) != 1:
        raise ValueError("fixture construction: the stale blob sha occurs"
                         " %d times, expected 1"
                         % data.count(stale_sha.encode("ascii")))
    if data.count(head_sha.encode("ascii")) != 0:
        raise ValueError("fixture construction: the fixture HEAD blob sha"
                         " already occurs in the seed bytes")
    return DriftFixture(path, data, repo, head_sha, stale_sha,
                        absent_rel, absent_pin)


def pending_fixture(tmp):
    """A one-entry synthetic seed whose single face the standing md table
    does not cover: every admitted md face is missing from this map, so
    the sync plan appends and verdicts PENDING regardless of which way
    the standing content moves (the exit-3 fixture shape).  Its provenance
    is in the v2 form, judged in a fixture git repository."""
    repo, git = fixture_repo(tmp, "pend-")
    repo_rel = "fixture-src.md"
    write_bytes(os.path.join(repo, repo_rel), b"fixture repo source bytes\n")
    git("add", repo_rel)
    git("commit", "-q", "-m", "fixture content")
    head_sha = git("rev-parse", "HEAD:" + repo_rel)
    m = {
        "schema": MAP_SCHEMA, "engine": "jargon",
        "seed_role": "fixture map for the repair-pin shell",
        "face_language": "en", "count": 1,
        "selection_rule": "fixture", "boundary_note": "fixture",
        "provenance": {"sources": [
            {"locator": "repo", "path": repo_rel,
             "role": "fixture source",
             "pin": {"kind": "git-blob-sha", "value": head_sha}}]},
        "entries": [{
            "id": "J001", "face": "zz fixture face",
            "standard": "zz fixture standard",
            "standard_language": "en",
            "standard_source": "fixture track", "source_line": 3,
            "disposition": "replace", "exempts": [],
            "cross_track_note": None, "note": None,
        }],
    }
    path = os.path.join(tmp, "pend-seed.json")
    dump_seed(path, m)
    return path


def gate_cmd(seed_path):
    """The contract gate: the sync tool's zero-write plan with the seed
    under test forwarded on --map (the same command shape the executor
    wires for its own --seed input)."""
    return [sys.executable, "-I", "-B", SYNC, "--map", seed_path]


def standing_sync_in_sync():
    """The standing zero-write plan verdict over the real faces."""
    rc, out = run_readonly([SYNC])
    return rc == 0 and "VERDICT IN-SYNC" in out


def standing_seeds_green():
    """The standing seed suite result (read-only premise for vector 3)."""
    rc, out = run_readonly([SEEDS])
    return rc == 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="test_repair_pin")
    ap.parse_args(argv)
    fails = []
    passed = 0
    if not os.path.isfile(TOOL):
        print("FAIL: repair executor missing: %s" % TOOL)
        print("== test_repair_pin: 0 pass / 1 red ==")
        return 1
    tool = load_tool()
    tmp = tempfile.mkdtemp(prefix="rqw_repair_pin_")
    try:
        # vector 1: the tool's own frozen selftest vector group
        try:
            rc, out, err = run_tool(["--selftest"])
            if rc == 0 and SELFTEST_MARK in out:
                passed += 1
                print("PASS vector 1 --selftest rc=0 with frozen marker")
            else:
                fails.append("vector 1 --selftest should be rc=0 with %r"
                             " (got rc=%d, marker=%s)"
                             % (SELFTEST_MARK, rc, SELFTEST_MARK in out))
                print((out + err)[-2000:])
        except subprocess.TimeoutExpired:
            fails.append("vector 1 --selftest timed out (%ds)" % TIMEOUT)

        # preflights: standing premises behind vectors 2, 3 and 5
        premise_sync = standing_sync_in_sync()
        if not premise_sync:
            print("SKIP vectors 2 and 5: the standing sync plan verdict is"
                  " no longer IN-SYNC, so an in-sync fixture cannot be"
                  " derived from the standing entries")
        premise_seeds = standing_seeds_green()
        if not premise_seeds:
            print("SKIP vector 3: the standing seed suite is red, so the"
                  " apply-verify premise does not hold")

        real = load_standing_entries() if premise_sync else None

        # vector 2: plan over a drift fixture is zero-write, action=plan,
        # the drifted repo pin named in the v2 fields
        if premise_sync:
            try:
                fx = drift_fixture(tmp, real, "v2-")
                rep, code = tool.flow("plan", fx.seed_path, gate_cmd(
                    fx.seed_path), root=fx.repo)
                untouched = read_bytes(fx.seed_path) == fx.seed_bytes
                drifted = rep.get("drifted") if isinstance(rep, dict) else []
                rows = [r for r in (drifted or [])
                        if isinstance(r, dict) and r.get("path")
                        == "fixture-src.md"]
                row = rows[0] if rows else None
                ok = (code == 0 and untouched and isinstance(rep, dict)
                      and rep.get("ok") is True
                      and rep.get("action") == "plan"
                      and len(drifted or []) == 1
                      and isinstance(rep.get("blocked"), list)
                      and rep.get("blocked") == []
                      and isinstance(rep.get("absent"), list)
                      and rep.get("absent") == []
                      and row is not None
                      and row.get("locator") == "repo"
                      and row.get("kind") == "git-blob-sha"
                      and row.get("state") == "drifted"
                      and row.get("pinned_blob_sha") == fx.stale_sha
                      and row.get("head_blob_sha") == fx.head_sha
                      and (rep.get("verdict") or "").startswith(
                          "VERDICT IN-SYNC"))
                if ok:
                    passed += 1
                    print("PASS vector 2 plan drift fixture: rc=0,"
                          " action=plan, the drifted repo pin named by"
                          " locator, kind, pinned vs HEAD blob sha and"
                          " state, seed bytes untouched")
                else:
                    fails.append("vector 2 plan drift fixture: rc=%d"
                                 " untouched=%s rep=%r"
                                 % (code, untouched, rep))
                    print(repr(rep)[:2000])
            except subprocess.TimeoutExpired:
                fails.append("vector 2 plan timed out (%ds)" % TIMEOUT)
            except ValueError as exc:
                fails.append("vector 2 fixture construction: %s" % exc)

        # vector 3: apply re-signs only the pin value, byte-exactly
        if premise_sync and premise_seeds:
            try:
                fx = drift_fixture(tmp, real, "v3-")
                rep, code = tool.flow("apply", fx.seed_path, gate_cmd(
                    fx.seed_path), root=fx.repo)
                after = read_bytes(fx.seed_path)
                # the working bytes equal the committed bytes, so the
                # re-signed value is the fixture HEAD blob sha
                expected = fx.seed_bytes.replace(
                    fx.stale_sha.encode("ascii"), fx.head_sha.encode("ascii"))
                byte_ok = after == expected
                try:
                    bj = json.loads(fx.seed_bytes.decode("utf-8"))
                    aj = json.loads(after.decode("utf-8"))
                except ValueError:
                    bj = aj = None
                dict_ok = (bj is not None and isinstance(aj, dict)
                           and isinstance(bj, dict)
                           and len(bj["provenance"]["sources"])
                           == len(aj["provenance"]["sources"]))
                if dict_ok:
                    # expected face: the fixture doc with the repo pin
                    # moved to the working bytes' blob sha
                    bj["provenance"]["sources"][0]["pin"]["value"] = \
                        fx.head_sha
                    dict_ok = aj == bj
                resigned = (rep.get("resigned") or []) \
                    if isinstance(rep, dict) else []
                rrow = [r for r in resigned
                        if isinstance(r, dict) and r.get("path")
                        == "fixture-src.md"]
                face_ok = (isinstance(rep, dict)
                           and rep.get("ok") is True
                           and rep.get("action") == "apply"
                           and len(rrow) == 1
                           and rrow[0].get("locator") == "repo"
                           and rrow[0].get("kind") == "git-blob-sha"
                           and rrow[0].get("pinned_blob_sha") == fx.stale_sha
                           and rrow[0].get("resigned_blob_sha")
                           == fx.head_sha
                           and rep.get("verify") == "seeds-suite-green")
                if code == 0 and byte_ok and dict_ok and face_ok:
                    passed += 1
                    print("PASS vector 3 apply drift fixture: rc=0,"
                          " the repo pin re-signed to the working bytes'"
                          " blob sha, every other byte unchanged, verify"
                          " green")
                else:
                    fails.append("vector 3 apply: rc=%d byte_ok=%s"
                                 " dict_ok=%s face_ok=%s rep=%r"
                                 % (code, byte_ok, dict_ok, face_ok, rep))
                    print(repr(rep)[:2000])
            except subprocess.TimeoutExpired:
                fails.append("vector 3 apply timed out (%ds)" % TIMEOUT)
            except ValueError as exc:
                fails.append("vector 3 fixture construction: %s" % exc)

        # vector 4: plan over a not-in-sync fixture exits 3, fail-loud,
        # and writes nothing
        try:
            ppath = pending_fixture(tmp)
            pbefore = read_bytes(ppath)
            # the gate verdict short-circuits the flow before any source
            # judgment, so the default judgment root is never reached
            rep, code = tool.flow("plan", ppath, gate_cmd(ppath))
            untouched = read_bytes(ppath) == pbefore
            ok = (code == 3 and untouched and isinstance(rep, dict)
                  and rep.get("ok") is False
                  and rep.get("stage") == "plan"
                  and isinstance(rep.get("verdict"), str)
                  and rep.get("verdict")
                  and "IN-SYNC" not in rep.get("verdict"))
            if ok:
                passed += 1
                print("PASS vector 4 plan not-in-sync fixture: rc=3,"
                      " ok=false, stage=plan, verdict recorded, seed"
                      " bytes untouched")
            else:
                fails.append("vector 4 plan not-in-sync fixture: rc=%d"
                             " untouched=%s rep=%r" % (code, untouched, rep))
                print(repr(rep)[:2000])
        except subprocess.TimeoutExpired:
            fails.append("vector 4 plan timed out (%ds)" % TIMEOUT)

        # vector 5: plan over an upstream-absent fixture records it, no
        # crash
        if premise_sync:
            try:
                fx = drift_fixture(tmp, real, "v5-", absent_upstream=True)
                rep, code = tool.flow("plan", fx.seed_path, gate_cmd(
                    fx.seed_path), root=fx.repo)
                untouched = read_bytes(fx.seed_path) == fx.seed_bytes
                absent = rep.get("absent") if isinstance(rep, dict) else []
                arows = [r for r in (absent or [])
                         if isinstance(r, dict) and r.get("path")
                         == fx.absent_rel]
                arow = arows[0] if arows else None
                ok = (code == 0 and untouched and isinstance(rep, dict)
                      and rep.get("ok") is True
                      and rep.get("action") == "plan"
                      and arow is not None
                      and arow.get("locator") == "external"
                      and arow.get("pinned_md5") == fx.absent_pin
                      and arow.get("consistency") == "matched"
                      and arow.get("declared") == tool.UPSTREAM_ABSENT_NOTICE)
                if ok:
                    passed += 1
                    print("PASS vector 5 plan upstream-absent source:"
                          " rc=0, the absent row carries the pinned md5,"
                          " the matched consistency and the declared"
                          " skip notice, no crash, seed bytes untouched")
                else:
                    fails.append("vector 5 plan upstream-absent source:"
                                 " rc=%d untouched=%s rep=%r arow=%r"
                                 % (code, untouched, rep, arow))
                    print(repr(rep)[:2000])
            except subprocess.TimeoutExpired:
                fails.append("vector 5 plan timed out (%ds)" % TIMEOUT)
            except ValueError as exc:
                fails.append("vector 5 fixture construction: %s" % exc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("== test_repair_pin: %d pass / %d red ==" % (passed, len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
