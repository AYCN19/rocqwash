#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_extract_magic.py — verify/extract_magic_check.py 自测（tests/·本轮实战判例
工具化③·gate7 涨账工具化轮·20261101；v15 增第十一节·首战判例盲区补全·20261102）

gate7 提取面 Obj.magic 逐件机检闸（坑账第十笔工具化·run97/98 三件涨账 28/4/1 承
工单给料）十一节判：
  1 工具自证    --selftest 十二判全过（rc 0）
  2 E2E 红判    假 rocq/ocamlc 桩全链：魔数 2 > max 0 → rc 1·上下文逐行·VERDICT: FAIL
  3 E2E 绿判    --max 2 → rc 0·VERDICT: PASS·--json 台账咬合（verdict/magic_ml/
                mode/targets/md5_v）
  4 inline 形   .v 自带 Separate Extraction 命令 → mode=inline·目标逐名咬合
  5 driver 形   无命令 → 本仓自带极简样例件 fixtures/names_sample.v 兜底收全部
                主定义（census 口径 7 名·含 Unicode 名道）→ driver 稿词面在盘
  6 提取红      假 rocq rc=1 → rc 1 fail-loud·rocq_tail 随账
  7 ml 未产出   假 rocq rc=0 而无 .ml → rc 1（不可计数≠绿）
  8 ocamlc 面   在卷实跑红 → rc 1·status=fail 随账；缺卷 → NOT-RUN 让席不计红
                （魔数面独立判）
  9 CLI 四码    --help 0／未知形参 2／缺 --world 2／缺件 9×2（--v 缺／world .vo
                未编译缺）
  10 计数口径   grep -c 语义（行计数·一行多魔数计一）模块级咬合
  11 盲区补全   v15 首战判例（gate7 四件 2 PASS/2 Class 盲区 fail-loud）：
                Class 声明夹具 census 不再误判异常（声明/命令不入目标·唯真主
                定义入账）／DECL_SKIP_EXT 十五 token 在册／G13 `Extraction` 命令
                形同治／未知 vernacular 仍 fail-loud rc=9（盲区收窄≠静默扩容）

零触律：全部夹具在临时目录自造（假桩脚本＋迷你世界）＋本仓自带 fixtures 只读；
零真编译（真链 E2E 归席位沙箱不入套件·承 precedent_station 判例口径）·零网络·
零触外部仓。幂等：python3 -B 禁 __pycache__·临时目录即写即清。
退出码：0=十一节全过；1=任一红。
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
    """迷你世界（Probe.v＋占位 .vo）＋假 rocq/ocamlc 桩（零真编译全链驱动）。"""
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
        # 1 工具自证（十一判）
        rc, out = run(["--selftest"])
        check("selftest", rc == 0 and "PASS" in out, "rc=%d %s" % (rc, out[-300:]))

        # 2+3+4 E2E 三态：红／绿＋json 咬合／inline 形（假桩全链·零真编译）
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
        # 4 inline 形：.v 自带 Separate Extraction（带 Extraction Require 行）
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

        # 5 driver 形兜底：本仓自带极简样例件 names_sample.v（census 7 名·含 Unicode）
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

        # 6 提取红：假 rocq rc=1 → fail-loud rc 1·rocq_tail 随账
        acc5 = os.path.join(tmp, "acc_rocqred.json")
        rc, out = run(["--v", v_path, "--world", world, "--json", acc5,
                       "--rocq", frocq, "--ocamlc", foc],
                      env={"EMC_FAKE_ML": canned, "EMC_FAKE_RC": "1"})
        r_j = json.load(io.open(acc5, encoding="utf-8"))
        check("提取红", rc == 1 and "提取面红" in out
              and r_j["rocq_rc"] == 1 and r_j["rocq_tail"], "rc=%d" % rc)

        # 7 ml 未产出：假 rocq rc=0 而无 .ml → rc 1（不可计数≠绿）
        rc, out = run(["--v", v_path, "--world", world, "--rocq", frocq,
                       "--ocamlc", foc], env={"EMC_FAKE_ML": ""})
        check("ml未产出红", rc == 1 and "未产出" in out, "rc=%d" % rc)

        # 8 ocamlc 面：实跑红 → rc 1；缺卷 → NOT-RUN 让席（魔数面独立判）
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

        # 9 CLI 四码：--help 0／未知形参 2／缺 --world 2／缺件 9×2
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

        # 10 计数口径：grep -c 语义（行计数·一行多魔数计一）模块级咬合
        mlf = os.path.join(tmp, "M.ml")
        wf(tmp, "M.ml", "let a = Obj.magic x\nlet b = 1\n"
                        "let c = f (Obj.magic y) (Obj.magic z)\n")
        n, hits = emc.grep_count_magic(mlf)
        check("grep_c口径", (n, hits) == (2, [1, 3]), "%s %s" % (n, hits))

        # 11 v15 盲区补全（首战判例·gate7 四件 2 PASS/2 Class 盲区 fail-loud）：
        #    Class 声明夹具 census 不再误判异常——声明/命令 vernacular 不入目标·
        #    唯真主定义入账；DECL_SKIP_EXT 在册；未知 vernacular 仍 fail-loud rc=9
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
        # G13 形（首战第二红 token）：裸 Extraction 命令 census 不再异常
        g13 = wf(tmp, "g13.v", "Definition g_a := 1.\nExtraction g_a.\n")
        m5, t5, _ = emc.collect_targets(g13)
        check("G13形_Extraction命令", m5 == "driver" and t5 == ["g_a"],
              "%s %s" % (m5, t5))
        # 盲区收窄≠静默扩容：未知 vernacular 仍 fail-loud rc=9
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
