#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_extract_magic.py — selftest for verify/extract_magic_check.py, the
per-file Obj.magic check of the gate7 extraction face (tests/; eleven
sections, numbered by execution order).

Purpose.  Machine-checks the Obj.magic extraction gate end to end on
  stubbed toolchains: tool selftest; E2E failing/passing runs with ledger
  agreement; the inline and driver target-collection modes; the extraction
  failure and missing-.ml fail-loud paths; the ocamlc face; the four CLI
  exit codes; the grep -c counting rule; and the blind-spot completions
  (Class-declaration fixtures, the DECL_SKIP_EXT roster, bare `Extraction`
  commands, unknown vernacular).
Interface.  Drives `verify/extract_magic_check.py` as a python3 -B
  subprocess with --selftest and the full E2E flag set (--v, --world,
  --workdir, --json, --max, --rocq, --ocamlc) against fake rocq/ocamlc
  stub scripts and mini worlds written under a temp directory; the
  in-repo fixture tests/fixtures/names_sample.v is used read-only for
  the driver-mode fallback.
Dependencies.  Python 3 standard library only; zero real compilation (the
  real-toolchain E2E stays outside the suite, the `test_precedent_station`
  scope), zero network, zero touches of external repositories; python3 -B
  keeps __pycache__ off and the temp stage is removed in finally.
Evidence.  Each section asserts concrete outcomes: rc plus VERDICT lines
  with per-line magic context; the --json ledger fields
  verdict/magic_ml/mode/targets/md5_v; the driver source text on disk;
  the module-level grep_count_magic pair (2 lines, hits [1, 3]); the
  fifteen-token DECL_SKIP_EXT roster inside mac_stmt_names.SKIP_KINDS;
  fail-loud rc 9 on unknown vernacular (blind-spot narrowing is not
  silent widening).
Exit-codes.  0 = all eleven sections pass; 1 = any section failed (checks listed).
"""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "verify", "extract_magic_check.py")
NAMES_SAMPLE = os.path.join(REPO, "tests", "fixtures", "names_sample.v")

_spec = importlib.util.spec_from_file_location("emc_tool", TOOL)
emc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(emc)

CANNED_ML = ("let p_one = Obj.magic (Obj.magic 1)\n"
             "let p_two = Obj.magic 2\n")
SAMPLE_NAMES = ["ns_succ", "ns_succ_ge", "ns_compose", "ns_add",
                "ns_natle_proper", "ns_δ运输", "ns_ex"]


def run(args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=e)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def wf(dirpath, name, text):
    fp = os.path.join(dirpath, name)
    with io.open(fp, "w", encoding="utf-8") as fh:
        fh.write(text)
    return fp


def make_stage(tmp, tag, v_text):
    """Mini world (Probe.v plus a placeholder .vo) plus fake rocq/ocamlc
    stubs (drives the full chain with zero real compilation)."""
    stage = os.path.join(tmp, tag)
    world = os.path.join(stage, "world")
    os.makedirs(world)
    v_path = wf(world, "Probe.v", v_text)
    with open(os.path.join(world, "Probe.vo"), "wb") as fh:
        fh.write(b"FAKE-VO-PLACEHOLDER")
    canned = wf(stage, "canned.ml", CANNED_ML)
    frocq = wf(stage, "fake_rocq.sh",
               "#!/bin/bash\n"
               "for last; do :; done\n"
               "# 真 rocq 形仿：.ml 以被提取模块命名（driver 稿取 Require Import 名）\n"
               "if [ -f \"$last\" ]; then\n"
               "  mod=\"$(grep -m1 '^Require Import' \"$last\" | sed 's/^Require Import //; s/\\.$//')\"\n"
               "fi\n"
               "[ -n \"${mod:-}\" ] || mod=\"$(basename \"$last\" .v)\"\n"
               "[ -n \"${EMC_FAKE_ML:-}\" ] && cp \"$EMC_FAKE_ML\" \"$mod.ml\"\n"
               "if [ \"${EMC_FAKE_RC:-0}\" != \"0\" ]; then echo \"Error: fake rocq blew up\" >&2; fi\n"
               "exit \"${EMC_FAKE_RC:-0}\"\n")
    foc = wf(stage, "fake_oc.sh", "#!/bin/bash\nexit \"${EMC_OC_RC:-0}\"\n")
    os.chmod(frocq, 0o755)
    os.chmod(foc, 0o755)
    return stage, world, v_path, canned, frocq, foc


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_textractmagic_")
    try:
        # 1. tool selftest (the tool's own check battery)
        rc, out = run(["--selftest"])
        check("selftest", rc == 0 and "PASS" in out, "rc=%d %s" % (rc, out[-300:]))

        # 2+3+4. E2E three states: failing / passing with ledger agreement /
        # inline mode (stubbed full chain, zero real compilation)
        stage, world, v_path, canned, frocq, foc = make_stage(
            tmp, "s1", "Definition p_one := 1.\nDefinition p_two := 2.\n")
        wd = os.path.join(stage, "wd")
        acc = os.path.join(tmp, "acc_red.json")
        rc, out = run(["--v", v_path, "--world", world, "--workdir", wd,
                       "--json", acc, "--rocq", frocq, "--ocamlc", foc],
                      env={"EMC_FAKE_ML": canned})
        check("e2e红_默认max0", rc == 1 and "VERDICT: FAIL" in out
              and "魔数行上下文" in out and "L1:" in out and "L2:" in out,
              "rc=%d" % rc)
        acc_j = json.load(io.open(acc, encoding="utf-8"))
        check("e2e红_账咬合", acc_j["verdict"] == "FAIL" and acc_j["magic_ml"] == 2
              and acc_j["max"] == 0 and len(acc_j["magic_lines"]) == 2
              and acc_j["ocamlc"]["status"] == "pass", repr(acc_j["verdict"]))
        acc2 = os.path.join(tmp, "acc_green.json")
        rc, out = run(["--v", v_path, "--world", world, "--max", "2", "--workdir", wd,
                       "--json", acc2, "--rocq", frocq, "--ocamlc", foc],
                      env={"EMC_FAKE_ML": canned})
        g_j = json.load(io.open(acc2, encoding="utf-8"))
        check("e2e绿_max2", rc == 0 and "VERDICT: PASS" in out
              and g_j["verdict"] == "PASS" and g_j["magic_ml"] == 2
              and g_j["mode"] == "driver"
              and g_j["targets"] == ["p_one", "p_two"],
              "rc=%d" % rc)
        check("md5_v_在账", os.path.isfile(v_path)
              and g_j["md5_v"] == emc.md5_of(v_path), g_j["md5_v"])
        # 4. inline mode: the .v carries its own Separate Extraction
        # (with the Extraction Require line)
        stage2, world2, v_inline, canned2, frocq2, foc2 = make_stage(
            tmp, "s2",
            "From Stdlib Require Import Extraction.\n"
            "Definition i_a := 1.\nDefinition i_b := 2.\n"
            "Separate Extraction i_a i_b.\n")
        acc3 = os.path.join(tmp, "acc_inline.json")
        rc, out = run(["--v", v_inline, "--world", world2, "--max", "2",
                       "--json", acc3, "--rocq", frocq2, "--ocamlc", foc2],
                      env={"EMC_FAKE_ML": canned2})
        i_j = json.load(io.open(acc3, encoding="utf-8"))
        check("inline形", rc == 0 and i_j["mode"] == "inline"
              and i_j["targets"] == ["i_a", "i_b"]
              and i_j["commands"] == [["i_a", "i_b"]], "rc=%d" % rc)

        # 5. driver-mode fallback: the in-repo minimal sample names_sample.v
        # (7 names in the census, Unicode names included)
        stage3 = os.path.join(tmp, "s3")
        world3 = os.path.join(stage3, "world")
        os.makedirs(world3)
        shutil.copyfile(NAMES_SAMPLE, os.path.join(world3, "names_sample.v"))
        with open(os.path.join(world3, "names_sample.vo"), "wb") as fh:
            fh.write(b"FAKE-VO-PLACEHOLDER")
        wd3 = os.path.join(stage3, "wd")
        acc4 = os.path.join(tmp, "acc_names.json")
        rc, out = run(["--v", os.path.join(world3, "names_sample.v"),
                       "--world", world3, "--max", "0", "--workdir", wd3,
                       "--json", acc4, "--rocq", frocq, "--ocamlc", foc],
                      env={"EMC_FAKE_ML": canned})
        n_j = json.load(io.open(acc4, encoding="utf-8"))
        drv_txt = io.open(os.path.join(wd3, "_names_sample_emc_driver.v"),
                          encoding="utf-8").read()
        check("driver形_样例件7名", rc == 1 and n_j["mode"] == "driver"
              and n_j["targets"] == SAMPLE_NAMES, "rc=%d %s" % (rc, n_j["targets"]))
        check("driver稿词面", "From Stdlib Require Import Extraction." in drv_txt
              and "Require Import names_sample." in drv_txt
              and "Separate Extraction " + " ".join(SAMPLE_NAMES) + "." in drv_txt,
              drv_txt)

        # 6. extraction failure: fake rocq rc=1 -> fail-loud rc 1,
        # rocq_tail recorded in the ledger
        acc5 = os.path.join(tmp, "acc_rocqred.json")
        rc, out = run(["--v", v_path, "--world", world, "--json", acc5,
                       "--rocq", frocq, "--ocamlc", foc],
                      env={"EMC_FAKE_ML": canned, "EMC_FAKE_RC": "1"})
        r_j = json.load(io.open(acc5, encoding="utf-8"))
        check("提取红", rc == 1 and "提取面红" in out
              and r_j["rocq_rc"] == 1 and r_j["rocq_tail"], "rc=%d" % rc)

        # 7. no .ml produced: fake rocq rc=0 without an .ml -> rc 1
        # (uncountable is not passing)
        rc, out = run(["--v", v_path, "--world", world, "--rocq", frocq,
                       "--ocamlc", foc], env={"EMC_FAKE_ML": ""})
        check("ml未产出红", rc == 1 and "未产出" in out, "rc=%d" % rc)

        # 8. ocamlc face: a real failing run -> rc 1; missing binary ->
        # NOT-RUN, the judge abstains (the magic face is judged independently)
        acc6 = os.path.join(tmp, "acc_ocred.json")
        rc, out = run(["--v", v_path, "--world", world, "--max", "9",
                       "--json", acc6, "--rocq", frocq, "--ocamlc", foc],
                      env={"EMC_FAKE_ML": canned, "EMC_OC_RC": "1"})
        o_j = json.load(io.open(acc6, encoding="utf-8"))
        check("ocamlc红", rc == 1 and o_j["ocamlc"]["status"] == "fail"
              and o_j["magic_ml"] == 2, "rc=%d" % rc)
        rc, out = run(["--v", v_path, "--world", world, "--max", "9",
                       "--rocq", frocq,
                       "--ocamlc", os.path.join(tmp, "no_such_ocamlc")],
                      env={"EMC_FAKE_ML": canned})
        check("ocamlc缺卷让席", rc == 0 and "NOT-RUN" in out, "rc=%d" % rc)

        # 9. the four CLI codes: --help 0 / unknown arg 2 / missing --world 2
        # / missing input 9 x2
        rc, out = run(["--help"])
        check("cli_help0", rc == 0 and "usage" in out, "rc=%d" % rc)
        rc, out = run(["--bogus"])
        check("cli_未知形参2", rc == 2, "rc=%d" % rc)
        rc, out = run(["--v", v_path])
        check("cli_缺world2", rc == 2, "rc=%d" % rc)
        rc, out = run(["--v", os.path.join(tmp, "gone.v"), "--world", world])
        check("cli_缺v9", rc == 9, "rc=%d" % rc)
        empty_world = os.path.join(tmp, "empty_world")
        os.makedirs(empty_world)
        rc, out = run(["--v", v_path, "--world", empty_world])
        check("cli_vo未编译9", rc == 9 and "先编后检" in out, "rc=%d" % rc)

        # 10. counting rule: grep -c semantics (line count; one line with
        # several magics counts once), checked at module level
        mlf = os.path.join(tmp, "M.ml")
        wf(tmp, "M.ml", "let a = Obj.magic x\nlet b = 1\n"
                        "let c = f (Obj.magic y) (Obj.magic z)\n")
        n, hits = emc.grep_count_magic(mlf)
        check("grep_c口径", (n, hits) == (2, [1, 3]), "%s %s" % (n, hits))

        # 11. blind-spot completion (the Class-declaration blind spot): the
        #    census no longer misjudges the Class fixture as an anomaly --
        #    declaration/command vernacular stays out of the targets, only
        #    real main definitions enter; DECL_SKIP_EXT is registered;
        #    unknown vernacular still fails loud with rc=9
        cls_fixture = (
            "Declare Scope req_scope.\n"
            "Class reqord (R : Set) : Set := mk {\n"
            "  rord_le_dec : forall a b : R, Or (le a b) (Not (le a b));\n"
            "  rlt_dec : forall a b : R, Or (lt a b) (Not (lt a b))\n"
            "}.\n"
            "Record rstore : Set := mkstore { rs_carrier : Set }.\n"
            "Scheme reqord_ind := Induction for reqord Sort Prop.\n"
            "Canonical req_can : reqord := reqord_rect.\n"
            "Section s1.\n"
            "Context {R : Set} {DO : reqord R}.\n"
            "Variable tok : R.\n"
            "Definition cls_pick (x y : R) : R := x.\n"
            "Instance req_inst : reqord nat.\n"
            "Extraction cls_pick.\n"
            "About cls_pick.\n"
            "Close Scope req_scope.\n"
            "End s1.\n")
        stage4, world4, v_cls, _, frocq4, foc4 = make_stage(tmp, "s4", cls_fixture)
        acc7 = os.path.join(tmp, "acc_cls.json")
        rc, out = run(["--v", v_cls, "--world", world4, "--max", "2", "--json", acc7,
                       "--rocq", frocq4, "--ocamlc", foc4],
                      env={"EMC_FAKE_ML": canned})
        c_j = json.load(io.open(acc7, encoding="utf-8"))
        check("class夹具_e2e绿", rc == 0 and "VERDICT: PASS" in out
              and "语句清单异常" not in out and c_j["verdict"] == "PASS",
              "rc=%d %s" % (rc, out[-200:]))
        check("class夹具_账咬合", c_j["mode"] == "driver"
              and c_j["targets"] == ["cls_pick", "req_inst"]
              and c_j["statements"] == ["cls_pick", "req_inst"]
              and "reqord" not in c_j["targets"] and "rstore" not in c_j["targets"],
              repr(c_j["targets"]))
        check("盲区在册_十五token", len(emc.DECL_SKIP_EXT) == 15
              and all(t in emc.mac_stmt_names.SKIP_KINDS for t in emc.DECL_SKIP_EXT),
              sorted(emc.DECL_SKIP_EXT))
        # G13 shape (the second blind-spot token): a bare Extraction command
        # no longer trips the census
        g13 = wf(tmp, "g13.v", "Definition g_a := 1.\nExtraction g_a.\n")
        m5, t5, _ = emc.collect_targets(g13)
        check("G13形_Extraction命令", m5 == "driver" and t5 == ["g_a"],
              "%s %s" % (m5, t5))
        # blind-spot narrowing is not silent widening: unknown vernacular
        # still fails loud with rc=9
        unk = wf(tmp, "unk.v", "Bogonize widget.\nDefinition unk_ok := 1.\n")
        try:
            emc.collect_targets(unk)
            check("未知仍红9", False, "未触发 SystemExit")
        except SystemExit as e:
            check("未知仍红9", e.code == 9, "code=%r" % (e.code,))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-20s %s %s" % (name, "PASS" if ok else "FAIL",
                                     detail if not ok else ""))
        if fails:
            print("TEST-EXTRACT-MAGIC FAIL: %d/%d 红" % (len(fails), len(checks)))
            return 1
        print("TEST-EXTRACT-MAGIC PASS: selftest/E2E红绿+账咬合/inline形/driver形样例件"
              "7名+稿词面/提取红/ml未产出/ocamlc红+缺卷让席/CLI四码/grep-c口径/"
              "盲区补全class夹具 "
              "十一节全过（gate7 涨账工具化轮·坑账第十笔工具化·v15 首战判例盲区补全）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
