#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_doc_lint.py — tools/doc_lint.py 自测壳（tests/·20261111 v39 集成席挂接·
缺壳自补——器由工装席铸·总套挂接归集成席）

文档←→实现一致性三查器（schema rocqwash-doclint/1）挂接件：器自带 --selftest
tmp 迷你仓冻结向量组（V1 一致仓 0 漂/V2 工具表缺一 hint/V3 计数漂/V4 旗标幻引/
V5 CLI 三码＋--help-cap 0→2/V6 JSON 幂等字节恒同·doc_lint.py --selftest 矢量表
自述）已由铸席自证，本壳接进套件总入口并加用法面冒烟：
  1 --selftest rc=0 且 stdout 含 "DOC-LINT-SELFTEST PASS" 冻结标记
  2 --help rc=0（argparse 用法面在位）
  3 --bogus rc=2／--help-cap 0 rc=2／--repo 缺目录 rc=9（退出码口径抽验——
    器口径 0=consistent·1=drift·2=用法错·9=缺·被审仓必需输入缺失走 9）

用法：
  python3 tests/test_doc_lint.py        # 套件内经 run_tests.sh 调
  python3 -B tests/test_doc_lint.py     # 手动（-B 禁 __pycache__）

零触律：--selftest 全 tmp 迷你仓夹具自写自清；本壳三判零写盘零网络零编译
零触真仓；python3 -B 禁 __pycache__。退出码：0=三判全过；1=任一红
（fail-loud 响亮列红·禁静默）。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "doc_lint.py")
MARK = "DOC-LINT-SELFTEST PASS"


def run(args):
    """子进程跑三查器（stdout+stderr 合流·零写盘零网络）。"""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("判1 --selftest 应 rc=0 且含 %r（实测 rc=%d）" % (MARK, rc))
        print(out)
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("判2 --help 应 rc=0（实测 rc=%d）" % rc)
        print(out)
    rc_b, _o = run(["--bogus"])
    rc_c, _o = run(["--repo", REPO, "--help-cap", "0"])
    rc_m, _o = run(["--repo", os.path.join(REPO, "no-such-dir")])
    if not (rc_b == 2 and rc_c == 2 and rc_m == 9):
        fails.append("判3 退出码口径应 bogus=2/--help-cap 0=2/缺仓=9"
                     "（实测 %d/%d/%d）" % (rc_b, rc_c, rc_m))
    print("== test_doc_lint: %d 过 / %d 红 ==" % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
