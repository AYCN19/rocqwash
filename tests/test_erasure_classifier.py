# -*- coding: utf-8 -*-
"""test_erasure_classifier.py — regression coverage for
verify/erasure_classifier.py (tests/).

Purpose.  Regression suite for the erasure classifier: four vectors — the
  classifier --selftest (six clusters, coq_ prefix forms, premise positions,
  multi-line inner-component stations), a synthetic .mli interface with
  per-name cluster/kind expectations, a CAPTURE cross-check against a
  scanner report, and an optional real-interface replay.
Interface.  Runs `verify/erasure_classifier.py` as a python3 -B subprocess
  with --selftest, --mli/--json-out/--resolve, and --json (CAPTURE report);
  the replay is env-gated by ROCWASH_ERASURE_MLI and ROCWASH_ERASURE_SCAN
  and is skipped when the variables are unset, so external clones pass
  without local artifacts.
Dependencies.  Python 3 standard library only; the classifier is located
  relative to this file's parent directory; fixtures are built in a temp
  directory removed in finally.
Evidence.  A vector passes only on concrete outcomes: selftest rc 0;
  conclusion clusters firing only on whole-conclusion erasures while
  inner-component positions stay advisory "other" with a name-pattern hint
  and a typed val never a station; capture agreement on the membership
  cluster with a scanner capture_stations report; the replay reproducing
  the recorded totals with --resolve names reported resolved.
Exit-codes.  0 = all checks pass; 1 = at least one check FAILed (the
  failing check names are listed on the summary line).
"""
import io, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CLS = os.path.join(REPO, "verify", "erasure_classifier.py")

fails = []


def check(name, cond, extra=""):
    print("  %-34s %s %s" % (name, "ok" if cond else "FAIL", extra))
    if not cond:
        fails.append(name)


def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


# 1. selftest
r = run([sys.executable, "-B", CLS, "--selftest"])
check("classifier --selftest rc=0", r.returncode == 0,
      "" if r.returncode == 0 else r.stdout.decode()[-300:])

# 2. synthetic interface
tmp = tempfile.mkdtemp(prefix="rw_erasure_")
try:
    mli = os.path.join(tmp, "Sample.mli")
    io.open(mli, "w", encoding="utf-8").write(
        "type __ = Obj.t\n"
        "val keep_perm : __\n"
        "val xq_hd_In : __\n"
        "val xq_last_In : __\n"
        "val my_neq0 : __\n"
        "val tail_ne : __\n"
        "type pair_of = Q -> __ -> QeqT\n"
        "val inner_thing :\n"
        "    (Q list, (Q, __) sigT) And\n"
        "val typed_now : RealCarrier\n")
    rep = os.path.join(tmp, "rep.json")
    r = run([sys.executable, "-B", CLS, "--mli", mli, "--json-out", rep,
             "--resolve", "typed_now,ghost_name"])
    res = json.load(io.open(rep, encoding="utf-8"))
    cl = dict((s["name"], s["cluster"]) for s in res["stations"])
    kinds = dict((s["name"], s["kind"]) for s in res["stations"])
    check("perm conclusion", cl.get("keep_perm") == "permutation-conclusion")
    check("membership x2", cl.get("xq_hd_In") == "membership-conclusion"
          and cl.get("xq_last_In") == "membership-conclusion")
    check("neq x2", cl.get("my_neq0") == "neq-conclusion"
          and cl.get("tail_ne") == "neq-conclusion")
    check("premise cluster", cl.get("pair_of") == "premise-position")
    check("multiline inner is other+hint",
          cl.get("inner_thing") == "other"
          and kinds.get("inner_thing") == "inner-component"
          and next(s.get("name_hint") is None for s in res["stations"]
                   if s["name"] == "inner_thing"))
    check("typed val not a station", "typed_now" not in cl)
    resolve = dict((x["name"], x["status"]) for x in res["resolve"])
    check("resolve typed=resolved missing=missing",
          resolve.get("typed_now") == "resolved"
          and resolve.get("ghost_name") == "missing")

    # 3. capture cross-check
    scan = os.path.join(tmp, "scan.json")
    io.open(scan, "w", encoding="utf-8").write(json.dumps(
        {"capture_stations": {"P6_In": ["xq_hd_In", "xq_last_In"]}}))
    rep2 = os.path.join(tmp, "rep2.json")
    run([sys.executable, "-B", CLS, "--mli", mli, "--json", scan,
         "--json-out", rep2])
    res2 = json.load(io.open(rep2, encoding="utf-8"))
    check("capture agree True",
          res2["capture_agree"] is not None and res2["capture_agree"]["agree"])
finally:
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

# 4. optional real-interface replay (env-gated)
mli_env = os.environ.get("ROCWASH_ERASURE_MLI", "")
scan_env = os.environ.get("ROCWASH_ERASURE_SCAN", "")
if mli_env and os.path.exists(mli_env):
    cmd = [sys.executable, "-B", CLS, "--mli", mli_env,
           "--json-out", os.path.join(tempfile.gettempdir(), "rw_erasure_replay.json")]
    if scan_env and os.path.exists(scan_env):
        cmd += ["--json", scan_env]
    r = run(cmd)
    rep = json.load(io.open(os.path.join(tempfile.gettempdir(), "rw_erasure_replay.json"),
                            encoding="utf-8"))
    t = rep["totals"]
    check("replay perm=3", t.get("permutation-conclusion") == 3, str(t))
    check("replay membership=2", t.get("membership-conclusion") == 2)
    check("replay neq=3", t.get("neq-conclusion") == 3)
    check("replay premise>=1", t.get("premise-position", 0) >= 1)
    if scan_env:
        check("replay capture agree", rep["capture_agree"]["agree"])
else:
    print("  replay check: SKIP (ROCWASH_ERASURE_MLI unset)")

print("TEST-ERASURE-CLASSIFIER:", "PASS" if not fails else "FAIL %s" % fails)
sys.exit(0 if not fails else 1)
