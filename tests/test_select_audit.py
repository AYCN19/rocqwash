#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_select_audit.py - self-test for tools/select_audit.py (tests/).

Purpose.  Exercises tools/select_audit.py end to end and its audit functions
  directly: the negative forms (in-batch duplicate, cross-batch collision,
  name outside the roster), the positive full-roster form, and the
  Require-face audit (full-form parsing, Stdlib allowlist exemption, world
  existence closure, fail-loud missing paths, the CLI code surface, and
  string-literal Require stripping with the bare-form allowlist).

Interface.  python3 tests/test_select_audit.py (no flags); prints one PASS/
  FAIL line per check plus the final TEST-SELECT-AUDIT verdict; registered
  as the t_select_audit lane of tests/run_tests.sh.

Dependencies.  Python 3 standard library only (io, os, shutil, subprocess,
  sys, tempfile); temp directories only, zero repository writes, zero
  network; the sibling tools/select_audit.py must exist.

Evidence.  Eleven sections, twenty checks: tool --selftest; DUP-BATCH;
  DUP-CROSS; NOT-IN-ORDER; clean roster form; parse_requires forms (names,
  verbs, From prefixes, comment stripping); allowlist exemption against an
  empty world; closure with exactly two gaps and the 8/3/5 stats counters;
  MissingPath on missing file/world; CLI codes 0/1/2/9; the string-literal
  and bare-form vector ending with exactly one gap (LW0QPoly).

Exit-codes.  0 = all twenty checks pass; 1 = any check fails (fail loud).
"""
import io
import os
import subprocess
import sys
import tempfile
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(REPO, "tools", "select_audit.py")

ORDER = ("S01_BaseRing.v#R0-d66910\n"
         "S02_CauchyComplete.v#R0-d66910\n"
         "S03_QExp.v#R0-d66910\n"
         "HansonLcm.v#R0-d66910\n"
         "zzm1_gauss.v\n"
         "Local/LW0LeibSeparation.v#R160-eb42d3\n")

# Require-face fixture: the six case-named Stdlib modules + every statement
# form (multi-name/multi-line/From/Export) + a comment-face Require that must
# stay unrecorded
REQ_TEXT = (
    "(* Require Import Ghost. a Require inside a comment must not be recorded *)\n"
    "From Stdlib Require Import\n"
    "     QArith.QArith\n"
    "     List.List.\n"
    "Require Export Lia.\n"
    "From Foo Require Import A.\n"
    "Require Export sub.B.\n"
    "Require sub.C.\n"
    "Require Import UpReqBanach.\n"
    "From Local Require Import Missing_Mod.\n")

# live-scan fixture: the string-literal prose Require (the
# `ConstructiveWorld_Live/UpReqIndex.v:2821` form; on/mother and friends must
# never be recorded) + the bare/short-path Stdlib names (each verified present
# under the toolchain Stdlib/** tree) + one true in-tree gap name
REQ_TEXT2 = (
    '"FA-D1S12 pack: zero Require on mother, slot reconciliation."\n'
    "Require Import Lists.List PeanoNat Permutation.\n"
    "Require Import QArith_base Qring Qfield Qabs ZArithRing.\n"
    "Require Import String Ascii Wf_nat micromega.Lqa.\n"
    "Require Import LW0QPoly.\n")


def run(args):
    p = subprocess.run([sys.executable, "-B", AUDIT] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else ""
    return p


def wf(tmp, name, text):
    fp = os.path.join(tmp, name)
    with io.open(fp, "w", encoding="utf-8") as fh:
        fh.write(text)
    return fp


def load_mod():
    """Load tools/select_audit.py directly by path (no package import; exec
    with zero side effects; main sits behind a __main__ guard)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("select_audit_mod", AUDIT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build_world(tmp):
    """The closure-test world: A.v, UpReqBanachExp.v, sub/B.v, sub/C.vo (the
    prefix over-match negative is in the set)."""
    w = os.path.join(tmp, "reqworld")
    os.makedirs(os.path.join(w, "sub"), exist_ok=True)
    wf(w, "A.v", "Module A. End A.\n")
    wf(w, "UpReqBanachExp.v", "Module E. End E.\n")
    wf(os.path.join(w, "sub"), "B.v", "Module B. End B.\n")
    wf(os.path.join(w, "sub"), "C.vo", "fakevo\n")
    return w


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_tselectaudit_")
    try:
        order = wf(tmp, "order.txt", ORDER)
        # 1 tool self-attestation
        p = run(["--selftest"])
        check("selftest", p.returncode == 0 and "PASS" in p.stdout, p.stdout[-400:])

        # 2 negative: in-batch duplicate (HansonLcm written twice, the from-memory form)
        b_dup = wf(tmp, "dup.txt", "HansonLcm.v\nHansonLcm\n")
        p = run(["--order", order, "--select", b_dup])
        check("dup_batch_negative", p.returncode == 1 and "DUP-BATCH" in p.stdout,
              "rc=%d" % p.returncode)

        # 3 negative: the same name claimed by two batches (two agents each
        #    reporting HansonLcm)
        b_a = wf(tmp, "batch_a.txt", "S03_QExp.v#R2-abc\n")
        b_b = wf(tmp, "batch_b.txt", "HansonLcm.v\n")
        b_c = wf(tmp, "batch_c.txt", "HansonLcm\nS01_BaseRing.v\n")
        p = run(["--order", order, "--select", b_a, "--select", b_b, "--select", b_c])
        check("dup_cross_negative", p.returncode == 1 and "DUP-CROSS" in p.stdout
              and "HansonLcm" in p.stdout, "rc=%d" % p.returncode)

        # 4 negative: a from-memory name outside the roster
        b_ghost = wf(tmp, "ghost.txt", "From_Memory_Only.v\n")
        p = run(["--order", order, "--select", b_ghost])
        check("not_in_order_negative", p.returncode == 1 and "NOT-IN-ORDER" in p.stdout,
              "rc=%d" % p.returncode)

        # 5 positive: every selection on the roster (with #-tag and /-path forms)
        b_ok = wf(tmp, "ok.txt", "# candidate batch\nS03_QExp.v#R2-abc\nzzm1_gauss.v\n"
                                 "Local/LW0LeibSeparation.v\n")
        p = run(["--order", order, "--select", b_ok])
        check("pos_clean", p.returncode == 0 and "AUDIT-CLEAN" in p.stdout,
              "rc=%d" % p.returncode)

        # ---- Require-face audit direct tests ----
        mod = load_mod()

        # 6 parse_requires: every form parsed (multi-name/multi-line/From/
        #    Export/bare Require/comment stripped)
        parsed = mod.parse_requires(REQ_TEXT)
        names = [n for n, _f, _v in parsed]
        check("require_parse_forms",
              names == ["QArith.QArith", "List.List", "Lia", "A", "sub.B",
                        "sub.C", "UpReqBanach", "Missing_Mod"], repr(names))
        verbs = {n: v for n, _f, v in parsed}
        check("require_parse_verbs", verbs.get("Lia") == "Export"
              and verbs.get("sub.B") == "Export" and verbs.get("A") == "Import"
              and verbs.get("sub.C") == "", repr(verbs))
        frms = {n: f for n, f, _v in parsed}
        check("require_parse_from", frms.get("A") == "Foo"
              and frms.get("Missing_Mod") == "Local"
              and frms.get("Lia") is None, repr(frms))
        check("require_parse_comment_strip", "Ghost" not in names, repr(names))

        # 7 Stdlib allowlist exemption: the all-Stdlib batch against an empty
        #    world -> zero gaps
        wempty = os.path.join(tmp, "wempty")
        os.makedirs(wempty)
        f_std = wf(tmp, "r_std.v",
                   "Require Import QArith.\nRequire Export Lia.\n"
                   "Require Import Lqa Morphisms Extraction.\n"
                   "From Stdlib Require Import List.\n")
        check("require_stdlib_exempt", mod.audit_requires(f_std, wempty) == [],
              repr(mod.audit_requires(f_std, wempty)))

        # 8 closure existence: .v/.vo/subdirectories all close; exactly two
        #    gaps (no prefix over-match on UpReqBanachExp.v)
        world = build_world(tmp)
        f_req = wf(tmp, "r_req.v", REQ_TEXT)
        gaps = mod.audit_requires(f_req, world)
        gnames = sorted(g["name"] for g in gaps)
        check("require_closure_two_gaps",
              gnames == ["Missing_Mod", "UpReqBanach"]
              and all(g["code"] == "REQ-GAP" for g in gaps), repr(gaps))
        stats = {}
        mod.audit_requires(f_req, world, stats)
        check("require_stats", stats == {"require_names": 8, "stdlib_exempt": 3,
                                         "tree_checked": 5}, repr(stats))

        # 9 fail loud: missing file/world -> MissingPath
        raised = None
        try:
            mod.audit_requires(os.path.join(tmp, "nope.v"), world)
        except mod.MissingPath:
            raised = "file"
        check("require_missing_file", raised == "file", repr(raised))
        raised = None
        try:
            mod.audit_requires(f_req, os.path.join(tmp, "noworld"))
        except mod.MissingPath:
            raised = "world"
        check("require_missing_world", raised == "world", repr(raised))

        # 10 CLI codes: 0 closed / 1 gaps (Ghost never leaks) / 2 missing
        #    --world / 9 missing world
        p = run(["--requires", f_std, "--world", wempty])
        check("require_cli_rc0", p.returncode == 0 and "REQUIRES-CLOSED" in p.stdout,
              "rc=%d %s" % (p.returncode, p.stdout[-200:]))
        p = run(["--requires", f_req, "--world", world])
        check("require_cli_rc1", p.returncode == 1 and "REQ-GAP" in p.stdout
              and "Ghost" not in p.stdout, "rc=%d" % p.returncode)
        p = run(["--requires", f_req])
        check("require_cli_rc2", p.returncode == 2, "rc=%d" % p.returncode)
        p = run(["--requires", f_req, "--world", os.path.join(tmp, "noworld")])
        check("require_cli_rc9", p.returncode == 9, "rc=%d" % p.returncode)

        # 11 live-scan face: string-literal stripping (the
        #    `ConstructiveWorld_Live/UpReqIndex.v:2821` form) + the bare-form
        #    Stdlib allowlist (verified under the toolchain tree) + exactly
        #    one true gap, LW0QPoly
        parsed2 = mod.parse_requires(REQ_TEXT2)
        names2 = [n for n, _f, _v in parsed2]
        check("require_string_literal_strip",
              names2 == ["Lists.List", "PeanoNat", "Permutation", "QArith_base",
                         "Qring", "Qfield", "Qabs", "ZArithRing", "String",
                         "Ascii", "Wf_nat", "micromega.Lqa", "LW0QPoly"],
              repr(names2))
        gaps2 = mod.audit_requires(wf(tmp, "r_req2.v", REQ_TEXT2), world)
        check("require_bare_form_allowlist_one_gap",
              [g["name"] for g in gaps2] == ["LW0QPoly"], repr(gaps2))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-20s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-SELECT-AUDIT FAIL: %d/%d failing" % (len(fails), len(checks)))
            return 1
        print("TEST-SELECT-AUDIT PASS: selftest/in-batch duplicate/cross-batch"
              " collision/not-in-order/pos + Require face (parsing/exemption/"
              "closure/missing paths/CLI codes/live-scan vectors) all pass"
              " (twenty checks, eleven sections)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
