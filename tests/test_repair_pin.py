#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_repair_pin.py: suite hookup shell for tools/pin_repair.py (tests/).

Purpose.  Wires the provenance-pin repair executor (the R15 class of the
  recursive-era CI whitepaper, section 2: re-sign a drifted provenance
  md5 pin only after the sync tool's zero-write plan verdicts IN-SYNC)
  into the suite entry, per the contract face A3 and its adjudication:
  the apply-path fixture carries verbatim copies of the standing seed
  entries (IN-SYNC by construction); the exit-3 path rides a synthetic
  single entry the standing md table cannot cover.

Interface.  python3 tests/test_repair_pin.py (no arguments; suite entry).

Dependencies.  Python 3 standard library only; subprocess drives the real
  tools/pin_repair.py CLI; preflights read the standing sync verdict and
  the standing seed suite result read-only; zero network; every fixture
  lives in the system temp dir; subprocess trees disable bytecode cache
  writes, so the repository gains no cache files.

Evidence.  (1) --selftest rc=0 with the frozen marker PIN-REPAIR-SELFTEST
  PASS; (2) --plan over a drift fixture rc=0, action=plan, per-source
  pinned/current md5 rows, seed bytes untouched; (3) --apply rc=0 with
  every md5 field re-signed to the current source md5, every other byte
  unchanged; (4) --plan over a not-in-sync fixture rc=3, ok=false,
  stage=plan, verdict recorded, zero write; (5) --plan over an
  absent-source fixture rc=0 with the absent row carrying a null current
  md5; preflights degrade affected vectors to loud SKIP lines.

Exit-codes.  0 all executed vectors green (loud SKIP lines allowed); 1
  any vector red (fail-loud, listed); 2 usage.
"""

import argparse
import hashlib
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


def dump_seed(path, m):
    """Serialize a fixture seed the way the standing map is serialized:
    the file's own key order, indent 2, ensure_ascii off, trailing
    newline (the byte-stable form tools/pin_repair.py rewrites under)."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(m, ensure_ascii=False, indent=2) + "\n")


def make_source(tmp, name, text):
    path = os.path.join(tmp, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def load_standing_entries():
    """The standing seed map, read once read-only (fixture premise only)."""
    with io.open(LIVE_SEED, encoding="utf-8") as fh:
        return json.load(fh)


def drift_fixture(tmp, real, prefix, absent_path=None):
    """A seed fixture built per the contract adjudication: the standing
    seed's entries verbatim (the gate judges such a map IN-SYNC by
    construction) plus fixture sources in the temp dir; source one pins a
    stale md5 (the drift under repair), source two pins the true md5 of
    its file, and the optional third source is absent on disk.  Returns
    (seed_path, seed_bytes, drifted_path, stale_md5)."""
    src_a = make_source(tmp, prefix + "src-a.md", "fixture source one\n")
    src_b = make_source(tmp, prefix + "src-b.md", "fixture source two\n")
    stale = md5_bytes(b"stale-pin-marker")
    sources = [
        {"path": src_a, "role": "fixture source, pin stale", "md5": stale},
        {"path": src_b, "role": "fixture source, pin true",
         "md5": file_md5(src_b)},
    ]
    if absent_path is not None:
        sources.append({"path": absent_path,
                        "role": "fixture source, absent on disk",
                        "md5": stale})
    fx = dict(real)
    fx["provenance"] = dict(real["provenance"])
    fx["provenance"]["sources"] = sources
    path = os.path.join(tmp, prefix + "seed.json")
    dump_seed(path, fx)
    data = read_bytes(path)
    # the stale hex pins exactly the sources that do not carry a true md5:
    # one (the drifted source) in the two-source form, two (drifted plus
    # absent) when an absent source is requested
    expected = 2 if absent_path is not None else 1
    if data.count(stale.encode("ascii")) != expected:
        raise ValueError("fixture construction: the stale md5 hex occurs"
                         " %d times, expected %d"
                         % (data.count(stale.encode("ascii")), expected))
    return path, data, src_a, stale


def pending_fixture(tmp):
    """A one-entry synthetic seed whose single face the standing md table
    does not cover: every admitted md face is missing from this map, so
    the sync plan appends and verdicts PENDING regardless of which way
    the standing content moves (the exit-3 fixture shape)."""
    src = make_source(tmp, "pend-src.md", "fixture source pending\n")
    m = {
        "schema": MAP_SCHEMA, "engine": "jargon",
        "seed_role": "fixture map for the repair-pin shell",
        "face_language": "en", "count": 1,
        "selection_rule": "fixture", "boundary_note": "fixture",
        "provenance": {"sources": [
            {"path": src, "role": "fixture source",
             "md5": md5_bytes(b"stale-pin-marker")}]},
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

        # vector 2: plan over a drift fixture is zero-write, action=plan
        if premise_sync:
            try:
                path, before, src_a, stale = drift_fixture(tmp, real, "v2-")
                rc, out, err = run_tool(["--plan", "--seed", path])
                untouched = read_bytes(path) == before
                try:
                    rep = result_json(out)
                except ValueError:
                    rep = None
                rows = {}
                if isinstance(rep, dict):
                    for row in rep.get("drifted") or []:
                        if isinstance(row, dict) and "path" in row:
                            rows[row["path"]] = row
                row = rows.get(src_a)
                if row is None:
                    for key in sorted(rows):
                        if os.path.basename(key) == os.path.basename(src_a):
                            row = rows[key]
                ok = (rc == 0 and untouched and isinstance(rep, dict)
                      and rep.get("ok") is True
                      and rep.get("action") == "plan"
                      and row is not None
                      and row.get("pinned_md5") == stale
                      and row.get("current_md5") == file_md5(src_a))
                if ok:
                    passed += 1
                    print("PASS vector 2 --plan drift fixture: rc=0,"
                          " action=plan, per-source md5 rows, seed bytes"
                          " untouched")
                else:
                    fails.append("vector 2 --plan drift fixture: rc=%d"
                                 " untouched=%s rep=%r"
                                 % (rc, untouched, rep))
                    print((out + err)[-2000:])
            except subprocess.TimeoutExpired:
                fails.append("vector 2 --plan timed out (%ds)" % TIMEOUT)
            except ValueError as exc:
                fails.append("vector 2 fixture construction: %s" % exc)

        # vector 3: apply re-signs only the md5 values, byte-exactly
        if premise_sync and premise_seeds:
            try:
                path, before, src_a, stale = drift_fixture(tmp, real, "v3-")
                rc, out, err = run_tool(["--apply", "--seed", path])
                after = read_bytes(path)
                new_md5 = file_md5(src_a)
                expected = before.replace(stale.encode("ascii"),
                                          new_md5.encode("ascii"))
                byte_ok = after == expected
                try:
                    bj = json.loads(before.decode("utf-8"))
                    aj = json.loads(after.decode("utf-8"))
                except ValueError:
                    bj = aj = None
                dict_ok = (bj is not None and isinstance(aj, dict)
                           and isinstance(bj, dict)
                           and len(bj["provenance"]["sources"])
                           == len(aj["provenance"]["sources"]))
                if dict_ok:
                    # expected face: the fixture doc with every source pin
                    # moved to the current md5 of its file
                    for src in bj["provenance"]["sources"]:
                        src["md5"] = file_md5(src["path"])
                    dict_ok = aj == bj
                try:
                    rep = result_json(out)
                except ValueError:
                    rep = None
                resigned = json.dumps((rep or {}).get("resigned") or [],
                                      default=str)
                face_ok = (isinstance(rep, dict)
                           and rep.get("ok") is True
                           and rep.get("action") == "apply"
                           and os.path.basename(src_a) in resigned
                           and rep.get("verify") == "seeds-suite-green")
                if rc == 0 and byte_ok and dict_ok and face_ok:
                    passed += 1
                    print("PASS vector 3 --apply drift fixture: rc=0,"
                          " md5 values re-signed to the current source"
                          " md5, every other byte unchanged, verify green")
                else:
                    fails.append("vector 3 --apply: rc=%d byte_ok=%s"
                                 " dict_ok=%s face_ok=%s rep=%r"
                                 % (rc, byte_ok, dict_ok, face_ok, rep))
                    print((out + err)[-2000:])
            except subprocess.TimeoutExpired:
                fails.append("vector 3 --apply timed out (%ds)" % TIMEOUT)
            except ValueError as exc:
                fails.append("vector 3 fixture construction: %s" % exc)

        # vector 4: plan over a not-in-sync fixture exits 3, fail-loud,
        # and writes nothing
        try:
            ppath = pending_fixture(tmp)
            pbefore = read_bytes(ppath)
            rc, out, err = run_tool(["--plan", "--seed", ppath])
            untouched = read_bytes(ppath) == pbefore
            try:
                rep = result_json(out)
            except ValueError:
                rep = None
            ok = (rc == 3 and untouched and isinstance(rep, dict)
                  and rep.get("ok") is False
                  and rep.get("stage") == "plan"
                  and isinstance(rep.get("verdict"), str)
                  and "IN-SYNC" not in rep.get("verdict"))
            if ok:
                passed += 1
                print("PASS vector 4 --plan not-in-sync fixture: rc=3,"
                      " ok=false, stage=plan, verdict recorded, seed"
                      " bytes untouched")
            else:
                fails.append("vector 4 --plan not-in-sync fixture: rc=%d"
                             " untouched=%s rep=%r" % (rc, untouched, rep))
                print((out + err)[-2000:])
        except subprocess.TimeoutExpired:
            fails.append("vector 4 --plan timed out (%ds)" % TIMEOUT)

        # vector 5: plan over an absent-source fixture records it, no crash
        if premise_sync:
            try:
                absent = os.path.join(tmp, "v5-src-absent.md")
                path, before, src_a, stale = drift_fixture(tmp, real, "v5-",
                                                           absent_path=absent)
                rc, out, err = run_tool(["--plan", "--seed", path])
                untouched = read_bytes(path) == before
                try:
                    rep = result_json(out)
                except ValueError:
                    rep = None
                absent_rows = {}
                if isinstance(rep, dict):
                    for row in rep.get("absent") or []:
                        if isinstance(row, dict) and "path" in row:
                            absent_rows[row["path"]] = row
                arow = absent_rows.get(absent)
                if arow is None:
                    for key in sorted(absent_rows):
                        if os.path.basename(key) == os.path.basename(absent):
                            arow = absent_rows[key]
                ok = (rc == 0 and untouched and isinstance(rep, dict)
                      and rep.get("action") == "plan"
                      and arow is not None
                      and arow.get("current_md5") is None
                      and arow.get("pinned_md5") == stale)
                if ok:
                    passed += 1
                    print("PASS vector 5 --plan absent source: rc=0, the"
                          " absent row carries path, pinned md5 and a null"
                          " current md5, no crash, seed bytes untouched")
                else:
                    fails.append("vector 5 --plan absent source: rc=%d"
                                 " untouched=%s rep=%r arow=%r"
                                 % (rc, untouched, rep, arow))
                    print((out + err)[-2000:])
            except subprocess.TimeoutExpired:
                fails.append("vector 5 --plan timed out (%ds)" % TIMEOUT)
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
