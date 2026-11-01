#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_select_audit.py — tools/select_audit.py 自测（tests/·五课反馈轮·席 rqsupport·
20261101·v6 判据轮打磨员扩 20261101）

五课负例②【nw6 选件重复】＋负例③【dver2-enbig7 同域撞】＋ v6 判据【nw10/abl6 空账】：
  - nw6：选件勘定员必须实读树 order.txt 全表 grep 剔重·禁凭记忆（候批账-nw6批.md
    HansonLcm 混入实录）。批内同名重复＝凭记忆之典型误 → DUP-BATCH 红。
  - enbig7：同件双席并行各带 born 闸必撞世界（collision_enbig7_20261031.md·主会话
    仲裁 36c35816）。同名出现在两份批选清单＝撞名前兆 → DUP-CROSS 红。
  - v6 判据（判例日期 20261030）：主会话与 nw10/abl6 两审计席同踩「Require 面审计
    把 Stdlib 件（QArith/Lia/List/Extraction/Lqa/Morphisms 等）误判为树内缺口」坑，
    且 grep 单行解析漏 Require Export/多名行。正确工法三件套直测：
    parse_requires 全形式解析／STDLIB_ROOTS 白名单豁免／audit_requires 世界
    .v/.vo 存在性闭包（tools/select_audit.py）。

  1 自证        工具 --selftest 十一判全过（rc 0）
  2 nw6 负例    批内同名重复 → rc 1·DUP-BATCH 词面
  3 enbig7 负例 双批同名（HansonLcm 判例名重演）→ rc 1·DUP-CROSS 词面
  4 not-in-order 负例：选树外凭记忆名 → rc 1·NOT-IN-ORDER 词面
  5 pos 正判    全表在册批 → rc 0·AUDIT-CLEAN（实表形 fixture 含 #代签与 / 路径行）
  6 v6 解析     parse_requires：From X Require Import/Export 多名多行／裸 Require／
               注释剥（Ghost 不入账）／动词与 From 逐名在账
  7 v6 豁免     STDLIB_ROOTS 首段豁免：全 Stdlib 批对空世界 → 零缺口
  8 v6 闭包     audit_requires：.v/.vo/子目录皆闭；缺口恰二（UpReqBanach 不误咬
               UpReqBanachExp.v·Missing_Mod）；REQ-GAP 码与名逐项对
  9 v6 fail-loud 对象缺失/世界缺失 → MissingPath
 10 v6 CLI 四码 0 全闭／1 缺口（Ghost 不泄账）／2 缺 --world／9 世界缺失
 11 v6 实盘补件 字符串散文 Require 剥（UpReqIndex.v:2821 判例形）＋裸形 Stdlib
               白名单（Lists.List/PeanoNat/…工具链实证在库）→缺口恰一 LW0QPoly

幂等：临时目录即写即清·零仓库写盘·零网络。
退出码：0=十一节二十判全过；1=任一红。
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

# v6 判据 fixture：判例点名六 Stdlib 件＋多名多行/From/Export 全形式＋注释 Require
REQ_TEXT = (
    "(* Require Import Ghost. 注释面不得入账 *)\n"
    "From Stdlib Require Import\n"
    "     QArith.QArith\n"
    "     List.List.\n"
    "Require Export Lia.\n"
    "From Foo Require Import A.\n"
    "Require Export sub.B.\n"
    "Require sub.C.\n"
    "Require Import UpReqBanach.\n"
    "From Local Require Import Missing_Mod.\n")

# v6 实盘补件 fixture（v6 轮 Live 世界 569 文件实扫当场现形·同族坑二连）：
#   字符串字面量散文 Require（UpReqIndex.v:2821 判例形·on/mother 等不得入账）
#   ＋裸形/短路径 Stdlib 件（工具链 Stdlib/** 逐一实证在库）＋真树内缺口判例名
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
    """按路径直载 tools/select_audit.py（无包形·exec 零副作用·main 有 __main__ 闸）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("select_audit_mod", AUDIT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build_world(tmp):
    """v6 闭包面世界：A.v／UpReqBanachExp.v／sub/B.v／sub/C.vo（前缀误咬负例在卷）。"""
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
        # 1 工具自证
        p = run(["--selftest"])
        check("selftest", p.returncode == 0 and "PASS" in p.stdout, p.stdout[-400:])

        # 2【nw6 负例】批内重复（HansonLcm 双写·凭记忆形）
        b_dup = wf(tmp, "dup.txt", "HansonLcm.v\nHansonLcm\n")
        p = run(["--order", order, "--select", b_dup])
        check("nw6_DUP-BATCH_负例", p.returncode == 1 and "DUP-BATCH" in p.stdout,
              "rc=%d" % p.returncode)

        # 3【enbig7 负例】双批同名撞（两"席"各报 HansonLcm）
        b_a = wf(tmp, "batch_a.txt", "S03_QExp.v#R2-abc\n")
        b_b = wf(tmp, "batch_b.txt", "HansonLcm.v\n")
        b_c = wf(tmp, "batch_c.txt", "HansonLcm\nS01_BaseRing.v\n")
        p = run(["--order", order, "--select", b_a, "--select", b_b, "--select", b_c])
        check("enbig7_DUP-CROSS_负例", p.returncode == 1 and "DUP-CROSS" in p.stdout
              and "HansonLcm" in p.stdout, "rc=%d" % p.returncode)

        # 4 not-in-order 负例（树外凭记忆名）
        b_ghost = wf(tmp, "ghost.txt", "From_Memory_Only.v\n")
        p = run(["--order", order, "--select", b_ghost])
        check("NOT-IN-ORDER_负例", p.returncode == 1 and "NOT-IN-ORDER" in p.stdout,
              "rc=%d" % p.returncode)

        # 5 pos：全表在册（含 #代签与 / 路径形）
        b_ok = wf(tmp, "ok.txt", "# 候批\nS03_QExp.v#R2-abc\nzzm1_gauss.v\n"
                                 "Local/LW0LeibSeparation.v\n")
        p = run(["--order", order, "--select", b_ok])
        check("pos_CLEAN", p.returncode == 0 and "AUDIT-CLEAN" in p.stdout,
              "rc=%d" % p.returncode)

        # ---- v6 判据·Require 面审计直测（nw10/abl6 空账判例工法）----
        mod = load_mod()

        # 6 parse_requires 全形式解析（多名多行/From/Export/裸 Require/注释剥）
        parsed = mod.parse_requires(REQ_TEXT)
        names = [n for n, _f, _v in parsed]
        check("v6_parse_全形式",
              names == ["QArith.QArith", "List.List", "Lia", "A", "sub.B",
                        "sub.C", "UpReqBanach", "Missing_Mod"], repr(names))
        verbs = {n: v for n, _f, v in parsed}
        check("v6_parse_动词", verbs.get("Lia") == "Export"
              and verbs.get("sub.B") == "Export" and verbs.get("A") == "Import"
              and verbs.get("sub.C") == "", repr(verbs))
        frms = {n: f for n, f, _v in parsed}
        check("v6_parse_From", frms.get("A") == "Foo"
              and frms.get("Missing_Mod") == "Local"
              and frms.get("Lia") is None, repr(frms))
        check("v6_parse_注释剥", "Ghost" not in names, repr(names))

        # 7 Stdlib 白名单豁免：判例点名六件全 Stdlib 批对空世界 → 零缺口
        wempty = os.path.join(tmp, "wempty")
        os.makedirs(wempty)
        f_std = wf(tmp, "r_std.v",
                   "Require Import QArith.\nRequire Export Lia.\n"
                   "Require Import Lqa Morphisms Extraction.\n"
                   "From Stdlib Require Import List.\n")
        check("v6_stdlib_豁免", mod.audit_requires(f_std, wempty) == [],
              repr(mod.audit_requires(f_std, wempty)))

        # 8 闭包存在性：.v/.vo/子目录皆闭；缺口恰二（前缀不误咬 UpReqBanachExp.v）
        world = build_world(tmp)
        f_req = wf(tmp, "r_req.v", REQ_TEXT)
        gaps = mod.audit_requires(f_req, world)
        gnames = sorted(g["name"] for g in gaps)
        check("v6_闭包_缺口恰二",
              gnames == ["Missing_Mod", "UpReqBanach"]
              and all(g["code"] == "REQ-GAP" for g in gaps), repr(gaps))
        stats = {}
        mod.audit_requires(f_req, world, stats)
        check("v6_计数面", stats == {"require_names": 8, "stdlib_exempt": 3,
                                     "tree_checked": 5}, repr(stats))

        # 9 fail-loud：对象缺失/世界缺失 → MissingPath
        raised = None
        try:
            mod.audit_requires(os.path.join(tmp, "nope.v"), world)
        except mod.MissingPath:
            raised = "file"
        check("v6_缺件_file", raised == "file", repr(raised))
        raised = None
        try:
            mod.audit_requires(f_req, os.path.join(tmp, "noworld"))
        except mod.MissingPath:
            raised = "world"
        check("v6_缺件_world", raised == "world", repr(raised))

        # 10 CLI 四码：0 全闭／1 缺口（Ghost 不泄账）／2 缺 --world／9 世界缺失
        p = run(["--requires", f_std, "--world", wempty])
        check("v6_cli_rc0", p.returncode == 0 and "REQUIRES-CLOSED" in p.stdout,
              "rc=%d %s" % (p.returncode, p.stdout[-200:]))
        p = run(["--requires", f_req, "--world", world])
        check("v6_cli_rc1", p.returncode == 1 and "REQ-GAP" in p.stdout
              and "Ghost" not in p.stdout, "rc=%d" % p.returncode)
        p = run(["--requires", f_req])
        check("v6_cli_rc2", p.returncode == 2, "rc=%d" % p.returncode)
        p = run(["--requires", f_req, "--world", os.path.join(tmp, "noworld")])
        check("v6_cli_rc9", p.returncode == 9, "rc=%d" % p.returncode)

        # 11 v6 实盘补件面：字符串散文剥（UpReqIndex.v:2821 判例形）＋裸形 Stdlib
        #    白名单（工具链实证在库）＋真缺口 LW0QPoly 恰一
        parsed2 = mod.parse_requires(REQ_TEXT2)
        names2 = [n for n, _f, _v in parsed2]
        check("v6_实盘_字符串散文剥",
              names2 == ["Lists.List", "PeanoNat", "Permutation", "QArith_base",
                         "Qring", "Qfield", "Qabs", "ZArithRing", "String",
                         "Ascii", "Wf_nat", "micromega.Lqa", "LW0QPoly"],
              repr(names2))
        gaps2 = mod.audit_requires(wf(tmp, "r_req2.v", REQ_TEXT2), world)
        check("v6_实盘_白名单豁免缺口恰一",
              [g["name"] for g in gaps2] == ["LW0QPoly"], repr(gaps2))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-20s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-SELECT-AUDIT FAIL: %d/%d 红" % (len(fails), len(checks)))
            return 1
        print("TEST-SELECT-AUDIT PASS: selftest/nw6批内重/enbig7跨批撞/not-in-order/"
              "pos＋v6判据(解析/豁免/闭包/缺件/CLI四码/实盘补件) 全过"
              "（五课负例②nw6选件·③enbig7同域撞·v6 nw10/abl6空账Require面判据）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
