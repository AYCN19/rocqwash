#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cw_doctor.py — tools/cw_doctor.py 最小自测壳（tests/·20261111 v38
综合体检器挂接·集成席）

综合体检器挂接件：体检器自带 --selftest 冻结向量组（①四域全绿 100 分／②环境
红降 60.0／③注册缺册 skip 归一 86.67＋CW_SET 缺册如实 skip／④堵账 TOP 注入
88.75／⑤advice 生成／⑥JSON 幂等字节恒同／⑦CLI 四码＋罐装全覆盖／⑧注册审计
单元——全 --injector canned 罐装 tmp fixture·零真 otool 零真网络零真编译·
chain_graph/注册审计真跑纯 stdlib）已由铸席自证，本壳只把它接进套件总入口并
加 --help 冒烟：
  1 --selftest rc=0 且 stdout 含 "CW-DOCTOR-SELFTEST PASS" 冻结标记
  2 --help rc=0（argparse 用法面在位）

用法：
  python3 tests/test_cw_doctor.py       # 套件内经 run_tests.sh 调
  python3 -B tests/test_cw_doctor.py    # 手动（-B 禁 __pycache__）

零触律：零网络零写盘零触真仓（真 dyld/真探针面不挂套件·canned 注入面由铸席
selftest 自证）；python3 -B 禁 __pycache__。
退出码：0=两判全过；1=任一红（fail-loud 响亮列红·禁静默）。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "cw_doctor.py")
MARK = "CW-DOCTOR-SELFTEST PASS"


def run(args):
    """子进程跑体检器（stdout+stderr 合流·零写盘零网络）。"""
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
    print("== test_cw_doctor: %d 过 / %d 红 ==" % (2 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
