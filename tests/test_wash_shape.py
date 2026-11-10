#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_wash_shape.py — tools/wash_shape.py 自测壳（tests/·20261111 v37 洗形席挂接）

洗形器（正典形五洗流水·schema rocqwash-shape/1）挂接件：器自带 --selftest 十二判
冻结向量组（plan 五洗逐判/正件对照/plan 零写盘/--apply 缺省关/plan-miss 如实/
apply→rescan clean→shaped/幂等二跑全 clean/锚缺实体/冻结名排除（罐装＋真在册
红拒）/gate4 罐装判面/CLI 四码/--loop 哨态事件流/确定性字节恒同·全 tmp 夹具零真
网络零真编译）已由铸席自证，本壳接进套件总入口并加用法面冒烟：
  1 --selftest rc=0 且 stdout 含 "WASH-SHAPE-SELFTEST: PASS" 冻结标记
  2 --help rc=0（argparse 用法面在位）
  3 --bogus rc=2／无输入面 rc=2／--file 缺件 rc=9（退出码口径抽验）

用法：
  python3 tests/test_wash_shape.py        # 套件内经 run_tests.sh 调
  python3 -B tests/test_wash_shape.py     # 手动（-B 禁 __pycache__）

零触律：零编译零网络零写盘（--selftest 自写自清 mkdtemp）；python3 -B 禁
__pycache__。退出码：0=三判全过；1=任一红（fail-loud 响亮列红·禁静默）。
"""
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "wash_shape.py")
MARK = "WASH-SHAPE-SELFTEST: PASS"


def run(args):
    """子进程跑洗形器（stdout+stderr 合流·零写盘零网络）。"""
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
    rc_n, _o = run([])
    tmp = tempfile.mkdtemp(prefix="rocqwash_test_wash_shape_")
    try:
        rc_m, _o = run(["--file", os.path.join(tmp, "nope.v")])
    finally:
        os.rmdir(tmp)
    if not (rc_b == 2 and rc_n == 2 and rc_m == 9):
        fails.append("判3 退出码口径应 bogus=2/无输入面=2/缺件=9"
                     "（实测 %d/%d/%d）" % (rc_b, rc_n, rc_m))
    print("== test_wash_shape: %d 过 / %d 红 ==" % (3 - len(fails),
                                                    len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
