#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_toolchain_dyld_doctor.py — tools/toolchain_dyld_doctor.py 最小自测壳（tests/·
20261111 集成席四工具波挂接）

dyld 工具链断链诊断器挂接件：诊断器自带 --selftest 全链离线向量组（otool 样例
解析/系统剔除外部保留/exists-missing/同名兜底/CLI 四码·零真 otool 零编译零网络）
已由铸席自证，本壳只把它接进套件总入口并加 --help 冒烟：
  1 --selftest rc=0 且 stdout 含 "DYLD-DOCTOR-SELFTEST PASS" 冻结标记
  2 --help rc=0（argparse 用法面在位）

用法：
  python3 tests/test_toolchain_dyld_doctor.py        # 套件内经 run_tests.sh 调
  python3 -B tests/test_toolchain_dyld_doctor.py     # 手动（-B 禁 __pycache__）

零触律：零真 otool 零编译零网络零写盘零触真仓；python3 -B 禁 __pycache__。
退出码：0=两判全过；1=任一红（fail-loud 响亮列红·禁静默）。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "toolchain_dyld_doctor.py")
MARK = "DYLD-DOCTOR-SELFTEST PASS"


def run(args):
    """子进程跑诊断器（stdout+stderr 合流·零写盘零网络）。"""
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
    print("== test_toolchain_dyld_doctor: %d 过 / %d 红 =="
          % (2 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
