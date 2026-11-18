#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_net_probe.py — tools/net_probe.py 最小自测壳（tests/·20261111 集成席四工具波挂接）

网络窗探针挂接件：探针自带 --selftest 零网络向量组（classify_error 分类
HTTPError 可达/URLError·超时不可达/canned 注入探针/稳窗判定/CLI 四码）已由
铸席自证，本壳只把它接进套件总入口并加 --help 冒烟：
  1 --selftest rc=0 且 stdout 含 "NET-PROBE-SELFTEST PASS" 冻结标记
  2 --help rc=0（argparse 用法面在位）

用法：
  python3 tests/test_net_probe.py        # 套件内经 run_tests.sh 调
  python3 -B tests/test_net_probe.py     # 手动（-B 禁 __pycache__）

零触律：零网络零写盘零触真仓（真探测面不挂套件·canned 注入由铸席 selftest
自证）；python3 -B 禁 __pycache__。
退出码：0=两判全过；1=任一红（fail-loud 响亮列红·禁静默）。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "net_probe.py")
MARK = "NET-PROBE-SELFTEST PASS"


def run(args):
    """子进程跑探针（stdout+stderr 合流·零写盘零网络）。"""
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
    print("== test_net_probe: %d 过 / %d 红 ==" % (2 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
