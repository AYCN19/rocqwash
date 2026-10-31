#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gate6_born_wrapper.py — wrapper/gate6_census.sh ＋ wrapper/born_world.sh 自测
（tests/·Mac 适配席 rqadapt·20261031）

二十一判 subprocess 实跑（每例正/负判优先·零编译零网络零仓库写盘·临时目录即写即清）：
  gate6_census.sh：
  1  语法              bash -n → rc=0
  2  子帮助            -h → rc=0 且含用法头注
  3  未知形参          --bogus → rc=2
  4  缺 --tree         → rc=2
  5  tree 缺失         --tree <不存在> → rc=9
  6  正本缺失          GATE6_CENSUS_SCRIPT=<不存在> --tree <tmp> → rc=9
  7  gate 无 baseline  --gate 无 --baseline → rc=2（前置 fail-loud·正本 GATE6-USAGE 同律）
  8  baseline 缺失     --baseline <不存在> → rc=9
  9  --dry-run         → rc=0；stdout 含 guard 档位正典形＋python3 -B＋--tree 透传
                        （零写盘：tmp 内事后无新增文件）
  born_world.sh：
  10 语法              bash -n → rc=0
  11 子帮助            -h → rc=0 且含用法头注
  12 未知形参          --bogus → rc=2
  13 缺 --world        → rc=2
  14 order/module 同给（二义）→ rc=2
  15 runtree 缺失      --runtree <不存在> --world <tmp> --module A → rc=9
  16 模块名带路径      --module sub/A → rc=2
  17 源缺失            runtree/tmp 无 A.v（dry-run 前置面过·cp 环 fail-loud）→ rc=9
  18 --dry-run         → rc=0；stdout 含 BORN-WORLD-DRYRUN＋guard 档位正典形＋
                        `-Q . ""` 正形（零写盘）
  19 order 注释剥离    order 文件 #注释/空行 → dry-run 只列有效名
  20 代际雷 md5 败     --assert-md5 错值 manifest → rc=9＋stderr「代际断言败」
                        且零编译零产物（world 无 .vo）
  21 manifest 只认 .v 源行：仅 .vo 行账 → rc=9「无 A.v 源断言行」

幂等：临时面全在 tempfile 目录并 finally 清理；不触两仓正本、不触各 seat 域；
     不真正调 rocq/guard（全部 fail-loud 路径先于任何编译行为拦截）。
退出码：0=二十一判全过；1=任一红。
"""
import os
import subprocess
import sys
import tempfile
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(REPO, "wrapper", "gate6_census.sh")
BORN = os.path.join(REPO, "wrapper", "born_world.sh")
MISSING = os.path.join(os.sep, "tmp", "rqadapt_nonexistent_gate6_born_target")


def sh(args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def snapshot(d):
    out = []
    for root, _dirs, files in os.walk(d):
        out.extend(os.path.join(root, f) for f in files)
    return sorted(out)


def main():
    ok = True
    tmp = tempfile.mkdtemp(prefix="rqadapt_g6born_")
    try:
        def judge(n, desc, cond, detail=""):
            nonlocal ok
            print("  judge%d %s: %s%s" % (n, desc, "PASS" if cond else "FAIL",
                                         ("" if cond else "  " + detail)))
            ok = ok and cond

        tree_tmp = os.path.join(tmp, "tree"); os.makedirs(tree_tmp)

        # ---------- gate6_census.sh ----------
        rc, out, err = sh(["bash", "-n", CENSUS])
        judge(1, "census 语法 bash -n", rc == 0, "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", CENSUS, "-h"])
        judge(2, "census -h 用法面", rc == 0 and "gate6" in out and "用法 Usage" in out,
              "rc=%s out[:80]=%r" % (rc, out[:80]))

        rc, out, err = sh(["bash", CENSUS, "--tree", tree_tmp, "--bogus"])
        judge(3, "census 未知形参 rc=2", rc == 2 and "未知形参" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", CENSUS])
        judge(4, "census 缺 --tree rc=2", rc == 2 and "--tree" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", CENSUS, "--tree", MISSING])
        judge(5, "census tree 缺失 rc=9", rc == 9 and "目录缺失" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", CENSUS, "--tree", tree_tmp],
                          env={"GATE6_CENSUS_SCRIPT": MISSING})
        judge(6, "census gate6 正本缺失 rc=9", rc == 9 and "gate6 正本缺失" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", CENSUS, "--tree", tree_tmp, "--gate"])
        judge(7, "census --gate 无 --baseline rc=2", rc == 2 and "--baseline" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", CENSUS, "--tree", tree_tmp, "--baseline", MISSING])
        judge(8, "census baseline 缺失 rc=9", rc == 9 and "baseline 文件缺失" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        before = snapshot(tmp)
        rc, out, err = sh(["bash", CENSUS, "--tree", tree_tmp, "--dry-run"])
        judge(9, "census --dry-run 正典形出账·零写盘",
              rc == 0 and "GATE6-CENSUS-DRYRUN" in out and "python3 -B" in out
              and "-Front 0 -Mid 1 -MaxWaitSec 600" in out and snapshot(tmp) == before,
              "rc=%s out[:200]=%r" % (rc, out[:200]))

        # ---------- born_world.sh ----------
        rc, out, err = sh(["bash", "-n", BORN])
        judge(10, "born 语法 bash -n", rc == 0, "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", BORN, "-h"])
        judge(11, "born -h 用法面", rc == 0 and "born_world" in out and "用法 Usage" in out,
              "rc=%s out[:80]=%r" % (rc, out[:80]))

        rc, out, err = sh(["bash", BORN, "--bogus"])
        judge(12, "born 未知形参 rc=2", rc == 2 and "未知形参" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", BORN, "--module", "A"])
        judge(13, "born 缺 --world rc=2", rc == 2 and "--world" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", BORN, "--world", os.path.join(tmp, "w"),
                           "--module", "A", "--order", MISSING])
        judge(14, "born order/module 同给 rc=2", rc == 2 and "不得同给" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", BORN, "--runtree", MISSING,
                           "--world", os.path.join(tmp, "w"), "--module", "A"])
        judge(15, "born runtree 缺失 rc=9", rc == 9 and "源树缺失" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", BORN, "--runtree", tree_tmp,
                           "--world", os.path.join(tmp, "w"), "--module", "sub/A"])
        judge(16, "born 模块名带路径 rc=2", rc == 2 and "不合法" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", BORN, "--runtree", tree_tmp,
                           "--world", os.path.join(tmp, "w"), "--module", "A"])
        judge(17, "born 源缺失 rc=9（fail-loud 先于编译）",
              rc == 9 and "认证代源缺失" in err
              and not [f for f in snapshot(tmp) if f.endswith(".vo")],
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        world18 = os.path.join(tmp, "w18")
        before = snapshot(tmp)
        rc, out, err = sh(["bash", BORN, "--runtree", tree_tmp, "--world", world18,
                           "--module", "A", "--dry-run"])
        judge(18, "born --dry-run 正形出账·零写盘",
              rc == 0 and "BORN-WORLD-DRYRUN" in out and "-Q . \"\"" in out
              and "-Front 0 -Mid 1 -MaxWaitSec 600" in out and snapshot(tmp) == before,
              "rc=%s out[:200]=%r" % (rc, out[:200]))

        orderf = os.path.join(tmp, "order.txt")
        with open(orderf, "w", encoding="utf-8") as fh:
            fh.write("# 依赖序注释行\n\nA\n  B  \n# 尾注释\n")
        rc, out, err = sh(["bash", BORN, "--runtree", tree_tmp, "--world", world18,
                           "--order", orderf, "--dry-run"])
        listed = [ln for ln in out.splitlines() if "cp:" in ln]
        names = [ln.rsplit("/", 1)[-1].split(" ")[0] for ln in listed]
        judge(19, "born order 注释/空白剥离",
              rc == 0 and names == ["A.v", "B.v"],
              "rc=%s names=%r out[:300]=%r" % (rc, names, out[:300]))

        runtree20 = os.path.join(tmp, "rt20"); os.makedirs(runtree20)
        with open(os.path.join(runtree20, "A.v"), "w", encoding="utf-8") as fh:
            fh.write("Definition a := 1.\n")
        badman = os.path.join(tmp, "bad.md5")
        with open(badman, "w", encoding="utf-8") as fh:
            fh.write("00000000000000000000000000000000  A.v\n")
        world20 = os.path.join(tmp, "w20")
        rc, out, err = sh(["bash", BORN, "--runtree", runtree20, "--world", world20,
                           "--module", "A", "--assert-md5", badman])
        judge(20, "born 代际雷 md5 败 rc=9·零产物",
              rc == 9 and "代际断言败" in err
              and not [f for f in snapshot(tmp) if f.endswith(".vo")],
              "rc=%s err[:160]=%r" % (rc, err[:160]))

        voman = os.path.join(tmp, "vo_only.md5")
        with open(voman, "w", encoding="utf-8") as fh:
            fh.write("00000000000000000000000000000000  A.vo  OK\n")
        world21 = os.path.join(tmp, "w21")
        rc, out, err = sh(["bash", BORN, "--runtree", runtree20, "--world", world21,
                           "--module", "A", "--assert-md5", voman])
        judge(21, "born manifest 只认 .v 源行（.vo 账不哑比）",
              rc == 9 and "源断言行" in err,
              "rc=%s err[:160]=%r" % (rc, err[:160]))

        print("== test_gate6_born_wrapper: %s ==" % ("ALL PASS" if ok else "RED"))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
