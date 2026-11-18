#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_wash_engine.py — selftest for the generic sanitize engine `wash/wash_engine.py` (rocqwash tests/).

Purpose.  Parallel to `tests/test_wash_fixture.py` (module import plus a ROOT patch on
  the instance file `wash/_abl1_wash.py`); this test drives the generic engine through
  its real argv CLI via subprocess (no hardcoded paths, no patching) on a mkdtemp
  fixture. Six checks: pos (two-tag patch ledger -> all APPLY, exit 0, on-disk
  count(new)==expect and count(old)==0, nested comment `(* nest (* deep *) outer *)`
  preserved verbatim — comment masking does not damage body text); idem (same ledger
  replayed on the sanitized file -> all SKIP, applied=0 skipped=N, exit 0, output
  byte-identical — the idempotent-replay evidence CONTRIBUTING section 4 attaches to
  sanitize PRs); neg (exact `old` string of the first tag corrupted -> that tag FAIL,
  exit 1, output untouched — fail-loud); bracket-neg (`old` with unbalanced parentheses,
  nesting-aware -> exit 2, zero writes); isolation (--out == --file -> exit 2);
  CLI contract (bare or positional call without --patch -> exit 3, SKIP semantics in
  the `examples/Makefile` demo; missing --file -> exit 2; missing --file/--patch paths -> exit 9).

Interface.  python3 tests/test_wash_engine.py; no flags; spawns `wash/wash_engine.py` with
  --file/--patch/--out and asserts on exit codes, stdout tokens (applied=/skipped=/
  fail=NO, FAIL, NOT-WRITTEN, md5 src=/out=), stderr tokens and on-disk effects.

Dependencies.  Python 3 standard library only (io, json, os, shutil, subprocess, sys,
  tempfile); engine spawned as sys.executable -B; writes only under a mkdtemp directory
  removed in a finally block; zero repository writes; runs are deterministic.

Evidence.  One assert per check, check name in the assert message; the WASH-ENGINE PASS
  line is the verdict; roster row: `t_wash_engine` (tests/run_tests.sh, README row 9).

Exit-codes.  0 = all six checks passing; 1 = any check failing (uncaught AssertionError).
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL = os.path.join(REPO, "wash", "wash_engine.py")

BODY = ("(* nest (* deep *) outer *)\n"
        "Lemma vec_a : forall x : nat, x = x.\n"
        "Proof.\n"
        "  intros x. reflexivity.\n"
        "Qed.\n")

LEDGER = {"patches": [
    {"tag": "eq2id", "expect": 1,
     "old": "Lemma vec_a : forall x : nat, x = x.\n",
     "new": "Lemma vec_a : forall x : nat, Id nat x x.\n"},
    {"tag": "refl2id", "expect": 1,
     "old": "  intros x. reflexivity.\n",
     "new": "  intros x. apply id_refl.\n"},
]}


def run(args):
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def main():
    tmp = tempfile.mkdtemp(prefix="rocqwash_washeng_t_")
    try:
        src = os.path.join(tmp, "vec.v")
        with io.open(src, "w", encoding="utf-8", newline="") as fh:
            fh.write(BODY)
        ledger_p = os.path.join(tmp, "ledger.json")
        with io.open(ledger_p, "w", encoding="utf-8") as fh:
            json.dump(LEDGER, fh)
        out = os.path.join(tmp, "vec_washed.v")

        # ---------- pos: apply both tags ----------
        rc, so, se = run(["--file", src, "--patch", ledger_p, "--out", out])
        assert rc == 0, "pos: expected exit 0, got %d\n%s%s" % (rc, so, se)
        assert "applied=2 skipped=0 fail=NO" in so, so
        with io.open(out, encoding="utf-8", newline="") as fh:
            washed = fh.read()
        assert washed.count("Id nat x x") == 1 and washed.count("apply id_refl") == 1, washed
        assert washed.count("x = x.") == 0 and washed.count("reflexivity") == 0, washed
        assert "nest (* deep *) outer" in washed, "nested comment must be preserved verbatim"
        assert "md5 src=" in so and "out=" in so, "source/output md5 must both be reported"

        # ---------- idem: idempotent replay (CONTRIBUTING section 4: applied=0 skipped=N) ----------
        before = open(out, "rb").read()
        out2 = os.path.join(tmp, "vec_washed2.v")
        rc, so, se = run(["--file", out, "--patch", ledger_p, "--out", out2])
        assert rc == 0, "idem: expected exit 0, got %d\n%s%s" % (rc, so, se)
        assert "applied=0 skipped=2 fail=NO" in so, so
        assert open(out2, "rb").read() == before, "idem: output must be byte-identical"

        # ---------- neg: fail-loud, a corrupted file is never written ----------
        with io.open(src, "w", encoding="utf-8", newline="") as fh:
            fh.write(BODY.replace("x = x.", "x = (x)."))
        rc, so, se = run(["--file", src, "--patch", ledger_p, "--out", out])
        assert rc == 1, "neg: expected exit 1, got %d\n%s%s" % (rc, so, se)
        assert "FAIL" in so and "NOT-WRITTEN" in so, so
        assert open(out, "rb").read() == before, "neg: fail-loud lost (output was modified)"

        # ---------- bracket-neg: unbalanced parentheses (nesting-aware) ----------
        bad = os.path.join(tmp, "bad.json")
        with io.open(bad, "w", encoding="utf-8") as fh:
            json.dump({"patches": [{"tag": "b", "old": "f (x.", "new": "g x", "expect": 1}]}, fh)
        rc, so, se = run(["--file", src, "--patch", bad, "--out", out])
        assert rc == 2, "bracket-neg: expected exit 2, got %d\n%s%s" % (rc, so, se)
        assert "嵌套括号感知" in se, se

        # ---------- isolation: --out == --file refused ----------
        with io.open(src, "w", encoding="utf-8", newline="") as fh:
            fh.write(BODY)
        rc, so, se = run(["--file", out, "--patch", ledger_p, "--out", out])
        assert rc == 2, "isolation: expected exit 2, got %d\n%s%s" % (rc, so, se)
        assert "写隔离" in se, se

        # ---------- CLI contract ----------
        rc, _, _ = run(["--file", src])                       # no ledger -> 3
        assert rc == 3, "no-ledger: expected exit 3, got %d" % rc
        rc, _, _ = run([src])                                 # positional bare form -> 3 (examples/Makefile demo form)
        assert rc == 3, "positional-bare: expected exit 3, got %d" % rc
        rc, _, _ = run(["--patch", ledger_p, "--out", out])   # ledger without --file -> 2
        assert rc == 2, "no-file: expected exit 2, got %d" % rc
        rc, _, _ = run(["--file", src, "--patch", os.path.join(tmp, "gone.json"), "--out", out])
        assert rc == 9, "missing-patch: expected exit 9, got %d" % rc
        rc, _, _ = run(["--file", os.path.join(tmp, "gone.v"), "--patch", ledger_p, "--out", out])
        assert rc == 9, "missing-file: expected exit 9, got %d" % rc

        print("WASH-ENGINE PASS: pos(2 APPLY·count assertions·nested comment preserved)"
              "/idem(applied=0 skipped=2·byte-identical)"
              "/neg(FAIL·NOT-WRITTEN)/bracket-neg(2)/isolation(2)/CLI(3·3·2·9·9) all passed")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
