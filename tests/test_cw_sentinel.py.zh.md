#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cw_sentinel.py — tools/cw_sentinel.py 最小自测壳（tests/·20261111 v37
实时动态哨挂接）

实时动态哨挂接件：哨自带 --selftest 冻结矢量组（①once ci-red＋二跑 seen 幂等
零事件／②ledger 新件 blocking＋幂等／③buildlog 增量 grep＋半行不误报／④
--on-red 占位替换执行实证＋缺省零动作／⑤loop 三轮 JSONL 序贯／⑥--emit JSONL
逐行合法 sort_keys＋seq 事件流内序贯＋确定性字节恒同＋CLI 四码＋CI 401→9＋
injector canned 未覆盖→9＋ledgers 目录缺→9——全 --injector canned＋tmp
fixture·零真网络零编译）已由铸席自证，本壳只把它接进套件总入口并加 --help
冒烟：
  1 --selftest rc=0 且 stdout 含 "CW-SENTINEL-SELFTEST PASS" 冻结标记
  2 --help rc=0（argparse 用法面在位）

用法：
  python3 tests/test_cw_sentinel.py       # 套件内经 run_tests.sh 调
  python3 -B tests/test_cw_sentinel.py    # 手动（-B 禁 __pycache__）

零触律：零网络零写盘零触真仓（真 API 面不挂套件·canned 注入面由铸席
selftest 自证）；python3 -B 禁 __pycache__。
退出码：0=两判全过；1=任一红（fail-loud 响亮列红·禁静默）。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "cw_sentinel.py")
MARK = "CW-SENTINEL-SELFTEST PASS"


def run(args):
    """子进程跑哨（stdout+stderr 合流·零写盘零网络）。"""
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
    print("== test_cw_sentinel: %d 过 / %d 红 ==" % (2 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
