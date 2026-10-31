#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_select_audit.py — tools/select_audit.py 自测（tests/·五课反馈轮·席 rqsupport·
20261101）

五课负例②【nw6 选件重复】＋负例③【dver2-enbig7 同域撞】：
  - nw6：选件勘定员必须实读树 order.txt 全表 grep 剔重·禁凭记忆（候批账-nw6批.md
    HansonLcm 混入实录）。批内同名重复＝凭记忆之典型误 → DUP-BATCH 红。
  - enbig7：同件双席并行各带 born 闸必撞世界（collision_enbig7_20261031.md·主会话
    仲裁 36c35816）。同名出现在两份批选清单＝撞名前兆 → DUP-CROSS 红。

  1 自证        工具 --selftest 九判全过（rc 0）
  2 nw6 负例    批内同名重复 → rc 1·DUP-BATCH 词面
  3 enbig7 负例 双批同名（HansonLcm 判例名重演）→ rc 1·DUP-CROSS 词面
  4 not-in-order 负例：选树外凭记忆名 → rc 1·NOT-IN-ORDER 词面
  5 pos 正判    全表在册批 → rc 0·AUDIT-CLEAN（实表形 fixture 含 #代签与 / 路径行）

幂等：临时目录即写即清·零仓库写盘·零网络。
退出码：0=五判全过；1=任一红。
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

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-20s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-SELECT-AUDIT FAIL: %d/%d 红" % (len(fails), len(checks)))
            return 1
        print("TEST-SELECT-AUDIT PASS: selftest/nw6批内重/enbig7跨批撞/not-in-order/"
              "pos五判全过（五课负例②nw6选件·③enbig7同域撞）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
