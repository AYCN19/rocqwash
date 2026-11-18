#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_netname_normalize.py - selftest for tools/netname_normalize.py (tests/).

Purpose.  Drives the `.v.v` double-suffix clean-name normalizer (map
  `<clean>.v.v -> <clean>.v`) through nine sections on temp-directory
  fixtures: 1 selftest (tool --selftest passes all eight vectors, rc 0);
  2 dry run default (MAP rows emitted, zero bytes written) -> rc 1 PENDING;
  3 apply (rc 0, target present, source gone, contents byte-identical);
  4 md5 verified (RENAME rows carry md5= and VERIFY-OK); 5 COLLIDE refuses
  overwrite (X.v and X.v.v coexist, rc 1, the other side preserved);
  6 clean world (no `.v.v`, rc 0 NORMALIZE-CLEAN); 7 CLI four codes (help 0,
  unknown flag 2, missing --dir flag 2, --dir absent 9); 8 report surfaces
  (--map TSV `<src>\t<dst>`, --json verdict and entries interlock);
  9 subdirectory (sub/B.v.v -> sub/B.v, os.walk full index).

Interface.  python3 tests/test_netname_normalize.py; no flags or arguments;
  each section asserts on the tool's exit code, stdout tokens and on-disk
  effects.

Dependencies.  Python 3 standard library only (io, json, os, shutil,
  subprocess, sys, tempfile); spawns the local tool via sys.executable -B;
  zero network, zero compiles, zero repository writes.

Evidence.  One PASS/FAIL row per named check, then TEST-NETNAME-NORMALIZE
  PASS|FAIL with the section roll-up; the exit code carries the verdict.
  Registered as t_netname_normalize in tests/run_tests.sh and tests/README.md.

Exit-codes.  0 = all nine sections passing; 1 = any section failing.
"""
import io
import os
import subprocess
import sys
import tempfile
import shutil
import json

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "netname_normalize.py")

BODY_A = "Lemma a : True.\nProof. exact I. Qed.\n"
BODY_B = "Definition b := 1.\n"


def run(args):
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else ""
    return p


def wf(dirpath, name, text):
    fp = os.path.join(dirpath, name)
    with io.open(fp, "w", encoding="utf-8") as fh:
        fh.write(text)
    return fp


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_tnetname_")
    try:
        # 1. tool selftest (eight vectors)
        p = run(["--selftest"])
        check("selftest", p.returncode == 0 and "PASS" in p.stdout, p.stdout[-400:])

        # 2+3+4+9. dry run default zero writes -> apply normalize md5 verified -> bytes identical (root + subdirectory)
        w = os.path.join(tmp, "world")
        os.makedirs(os.path.join(w, "sub"))
        wf(w, "A.v.v", BODY_A)
        wf(os.path.join(w, "sub"), "B.v.v", BODY_B)
        wf(w, "Clean.v", "Lemma c : True.\nProof. exact I. Qed.\n")  # clean-name control file
        p = run(["--dir", w])
        check("dryrun_PENDING", p.returncode == 1 and "NORMALIZE-PENDING" in p.stdout
              and "MAP A.v.v -> A.v" in p.stdout and "MAP sub/B.v.v -> sub/B.v" in p.stdout,
              "rc=%d" % p.returncode)
        check("dryrun_no_disk_write", os.path.isfile(os.path.join(w, "A.v.v"))
              and not os.path.exists(os.path.join(w, "A.v"))
              and os.path.isfile(os.path.join(w, "sub", "B.v.v")),
              "dry run must not rename or create")
        src_bytes = io.open(os.path.join(w, "A.v.v"), "rb").read()
        p = run(["--dir", w, "--apply"])
        check("apply_rc0", p.returncode == 0 and "APPLY-DONE" in p.stdout,
              "rc=%d %s" % (p.returncode, p.stdout[-200:]))
        check("md5_verified_recorded", "RENAME A.v.v" in p.stdout and "VERIFY-OK" in p.stdout
              and "md5=" in p.stdout, p.stdout)
        a_path = os.path.join(w, "A.v")
        b_path = os.path.join(w, "sub", "B.v")
        check("apply_renamed_on_disk", os.path.isfile(a_path) and os.path.isfile(b_path)
              and not os.path.exists(os.path.join(w, "A.v.v"))
              and not os.path.exists(os.path.join(w, "sub", "B.v.v")),
              "after the rename the source is gone and the target exists")
        check("rename_keeps_bytes", io.open(a_path, "rb").read() == src_bytes
              and io.open(b_path, encoding="utf-8").read() == BODY_B,
              "contents byte-identical")
        check("clean_v_control_untouched", os.path.isfile(os.path.join(w, "Clean.v"))
              and "Clean.v ->" not in p.stdout, "pure .v files must not enter the ledger")

        # 5. COLLIDE refuses overwrite: X.v and X.v.v coexist -> rc 1, other side preserved
        w2 = os.path.join(tmp, "world2")
        os.makedirs(w2)
        wf(w2, "X.v", "ORIGINAL-TARGET\n")
        wf(w2, "X.v.v", "DOUBLE-SUFFIX\n")
        p = run(["--dir", w2, "--apply"])
        check("COLLIDE_refuses_overwrite", p.returncode == 1 and "COLLIDE" in p.stdout
              and io.open(os.path.join(w2, "X.v"), encoding="utf-8").read() == "ORIGINAL-TARGET\n"
              and os.path.isfile(os.path.join(w2, "X.v.v")),
              "rc=%d" % p.returncode)

        # 6. clean world -> rc 0 CLEAN
        w3 = os.path.join(tmp, "world3")
        os.makedirs(w3)
        wf(w3, "Ok.v", BODY_A)
        p = run(["--dir", w3])
        check("clean_world_CLEAN", p.returncode == 0 and "NORMALIZE-CLEAN" in p.stdout,
              "rc=%d" % p.returncode)

        # 7. CLI four codes: --help 0 / unknown flag 2 / missing --dir flag 2 / --dir absent 9
        p = run(["--help"])
        check("cli_help0", p.returncode == 0 and "usage" in p.stdout,
              "rc=%d" % p.returncode)
        p = run(["--bogus"])
        check("cli_unknown_flag_2", p.returncode == 2, "rc=%d" % p.returncode)
        p = run([])
        check("cli_missing_dir_flag_2", p.returncode == 2, "rc=%d" % p.returncode)
        p = run(["--dir", os.path.join(tmp, "nowhere")])
        check("cli_dir_absent_9", p.returncode == 9, "rc=%d" % p.returncode)

        # 8. report surfaces: --map TSV / --json interlock
        w4 = os.path.join(tmp, "world4")
        os.makedirs(w4)
        wf(w4, "M.v.v", BODY_A)
        mapf = os.path.join(tmp, "map.tsv")
        jsonf = os.path.join(tmp, "acc.json")
        p = run(["--dir", w4, "--map", mapf, "--json", jsonf])
        rows = [ln.rstrip("\n").split("\t") for ln in io.open(mapf, encoding="utf-8")
                if ln.strip()]
        acc = json.load(io.open(jsonf, encoding="utf-8"))
        check("map_json_reports", rows == [["M.v.v", "M.v"]]
              and acc["verdict"] == "PENDING"
              and acc["entries"][0]["netname"] == "M",
              repr(rows) + repr(acc.get("verdict")))

        # 9. the .v.v.v form: one strip per run (N.v.v.v -> N.v.v, rerun strips again, reported as-is)
        w5 = os.path.join(tmp, "world5")
        os.makedirs(w5)
        wf(w5, "N.v.v.v", BODY_A)
        p = run(["--dir", w5])
        check("vvv_one_strip_per_run", p.returncode == 1 and "N.v.v.v -> N.v.v" in p.stdout,
              "rc=%d" % p.returncode)

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-26s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-NETNAME-NORMALIZE FAIL: %d/%d failing" % (len(fails), len(checks)))
            return 1
        print("TEST-NETNAME-NORMALIZE PASS: selftest / dry-run zero writes / apply normalize / "
              "rename keeps bytes / COLLIDE refuses overwrite / clean world CLEAN / CLI four codes / "
              "map+json reports / vvv one strip per run - all nine sections passing")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
