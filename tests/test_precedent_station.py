#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_precedent_station.py — three-precedent acceptance station self-test (tests/).

    Purpose.  Drives `wrapper/precedent_station.py`, the acceptance station for
      the E7 carrier relay / R23 notation overload / E5 projection re-anchor
      precedents: step 1 names cross-check against the reference, step 2
      `gate4`, step 3 optional `gate7`. Runs the light chain (steps 1-2) plus
      station shape checks; the heavy `gate7` step stays in the
      `t_gate7_wrapper` lane. Seven checks: selftest / positive smoke /
      negative / REVIEW escalation / gate7 shape / unknown apply face refused;
      frozen md5 side evidence.

    Interface.  python3 tests/test_precedent_station.py (no arguments); drives
      the station via subprocess with `--station-selftest`, `--cured`,
      `--baseline`, `--knife`, `--station-json`, `--steps`,
      `--gate4-length-cap`, `--gate7-tree`, `--gate7-module`; prints one
      PASS/FAIL line per check plus the `TEST-PRECEDENT-STATION` token.

    Dependencies.  Python 3 standard library only; `wrapper/precedent_station.py`,
      `names/mac_stmt_names.py`, `verify/gate4_comment_guard.py` resolved
      relative to this file's parent directory; zero compile, zero network,
      zero repository writes.

    Evidence.  Registered as lane `t_precedent_station` in tests/run_tests.sh;
      the frozen md5 side evidence re-asserts the update ledger section three
      values for both canonical files.

    Exit-codes.  0 = all seven checks pass; 1 = any check failing (each
      check prints PASS/FAIL with failure detail, fail-loud).
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATION = os.path.join(REPO, "wrapper", "precedent_station.py")
NAMES = os.path.join(REPO, "names", "mac_stmt_names.py")
GATE4 = os.path.join(REPO, "verify", "gate4_comment_guard.py")
NAMES_FROZEN_MD5 = "9e26c0db2c60ced3629a13a821bdf615"   # frozen value registered in the update ledger section three
GATE4_FROZEN_MD5 = "3615027b14b63ce38d247da44957f145"   # frozen value registered in the update ledger section three

HEADER = """(* precedent_station_fixture.v — 三判例验收站夹具（rocqwash tests/自造·零外部素材）。

   Mission.  Exercise the three-precedent acceptance chain lightly (names+gate4).
   Dependencies.  Rocq standard library only.
   References.  recipes/S07_projection_reanchor_E5.md; update ledger five-lessons.
   Constructivity.  Set-carried statements; proofs close with Qed; no classics.
   Build.  rocq c -native-compiler no -q -Q . "" precedent_station_fixture.v
*)

"""


def base_body(fn_name):
    return ("Require Import QArith.\n\n"
            "Lemma %s : forall x y : Q, QltT x y -> QltT (x + y) (y + x).\n"
            "Proof.\n  intros x y H. exact H.\nQed.\n" % fn_name)


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args):
    p = subprocess.run([sys.executable, "-B", STATION] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p


def write(tmp, name, text):
    fp = os.path.join(tmp, name)
    with io.open(fp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return fp


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_tprecstation_")
    try:
        # check 1: station selftest, ten internal checks
        p = run(["--station-selftest"])
        check("station selftest ten checks", p.returncode == 0 and "PRECEDENT-STATION-SELFTEST" in p.stdout
              and "PASS" in p.stdout, "rc=%d out=%s" % (p.returncode, p.stdout[-300:]))

        # fixture: the cured file has statement faces equal to the baseline
        # and a different proof body (the E7 precedent shape: statement faces
        # untouched, proof body replaced)
        baseline = write(tmp, "baseline.v", HEADER + base_body("ps_fix_order"))
        cured = write(tmp, "cured.v", HEADER + base_body("ps_fix_order").replace(
            "intros x y H. exact H.",  # proof body replaced; neither the names step nor gate4 objects
            "intros x y H. simpl. exact H."))
        # negative fixture: one extra statement sentence (statement face
        # touched, violating the step-1 statement-count N=N equality)
        cured_bad = write(tmp, "cured_bad.v", HEADER + base_body("ps_fix_order")
                          + "\nLemma ps_fix_extra : forall x : Q, QleT x x.\n"
                            "Proof. intros x. apply Qle_refl.\nQed.\n")

        # check 2: positive smoke — light chain steps 1-2 pass, station
        # account records the --knife name
        sj = os.path.join(tmp, "station_pos.json")
        p = run(["--cured", cured, "--baseline", baseline,
                 "--knife", "E7-carrier", "--station-json", sj])
        acc = {}
        if os.path.isfile(sj):
            with io.open(sj, encoding="utf-8") as fh:
                acc = json.load(fh)
        check("positive smoke light chain green", p.returncode == 0 and acc.get("verdict") == "PASS"
              and acc.get("knife") == "E7-carrier"
              and acc.get("steps", {}).get("names", {}).get("rc") == 0
              and acc.get("steps", {}).get("gate4", {}).get("rc") == 0,
              "rc=%d acc=%s out=%s" % (p.returncode, json.dumps(acc)[:200], p.stdout[-300:]))

        # check 3: negative — one extra statement sentence -> step 1 rc=2
        # FAIL -> station exit 1 (the hard step wins; no short-circuit, the
        # step-2 account is still emitted)
        p = run(["--cured", cured_bad, "--baseline", baseline,
                 "--knife", "E7-carrier"])
        check("negative statement-face touch exit1", p.returncode == 1 and "FAIL" in p.stdout
              and "①对表" in p.stdout and "②gate4" in p.stdout,
              "rc=%d out=%s" % (p.returncode, p.stdout[-300:]))

        # check 4: REVIEW escalation — --gate4-length-cap 5 (the fixture
        # header is 9 lines, over the review-grade cap) -> exit 2
        p = run(["--cured", cured, "--baseline", baseline,
                 "--gate4-length-cap", "5"])
        check("REVIEW escalation exit2", p.returncode == 2 and "REVIEW" in p.stdout,
              "rc=%d out=%s" % (p.returncode, p.stdout[-300:]))

        # check 5: gate7 shape — gate7 in the steps but --gate7-module
        # missing -> station-level usage error exit 2, zero steps opened;
        # module named but its .v file absent from the world tree ->
        # preflight exit 9, zero steps opened
        p = run(["--cured", cured, "--baseline", baseline,
                 "--steps", "names,gate4,gate7", "--gate7-tree", tmp])
        c5a = p.returncode == 2 and "①对表" not in p.stdout
        p = run(["--cured", cured, "--baseline", baseline,
                 "--steps", "names,gate4,gate7", "--gate7-tree", tmp,
                 "--gate7-module", "NoSuchMod"])
        check("gate7 shape exit2 missing module exit9 missing file",
              c5a and p.returncode == 9 and "①对表" not in p.stdout,
              "rc9=%d out=%s" % (p.returncode, p.stdout[-300:]))

        # check 6: apply-face naming — unknown apply face refused, exit 2
        p = run(["--cured", cured, "--baseline", baseline, "--knife", "bogus-knife"])
        check("unknown apply face refused exit2", p.returncode == 2 and "未知刀面" in p.stdout,
              "rc=%d out=%s" % (p.returncode, p.stdout[-300:]))

        # check 7: frozen side evidence — both canonical files' md5 equal the
        # registered frozen values (the station pin asserts the same source)
        check("frozen files zero-touch", md5_of(NAMES) == NAMES_FROZEN_MD5
              and md5_of(GATE4) == GATE4_FROZEN_MD5,
              "names=%s gate4=%s" % (md5_of(NAMES), md5_of(GATE4)))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-24s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-PRECEDENT-STATION FAIL: %d/%d checks failing" % (len(fails), len(checks)))
            return 1
        print("TEST-PRECEDENT-STATION PASS: station selftest / positive smoke "
              "knife naming / negative exit1 / REVIEW escalation exit2 / "
              "gate7 shape exit9 / unknown apply face exit2 / frozen side "
              "evidence — all seven checks pass (three-precedent acceptance station)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
