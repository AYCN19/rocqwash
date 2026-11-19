#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_baseline_diff.py — tools/baseline_diff.py 自测壳（tests/·20261111 v40
集成席挂接·缺壳自补——器由工装席铸·总套挂接归集成席）

堵账基线对比器（schema rocqwash-baseline-diff/1·两份 unclog --audit 基线
argv 序=旧→新→new_blocks/resolved_blocks/persistent 三清单＋score_delta·
verdict improved/degraded/stable/incomparable·账面自洽预检拒手编·候选面四元组
比对·timing 段不入对比·a failing result is data, not a tool failure）挂接件：器自带 --selftest tmp 合成基线
冻结矢量组（①improved 红减/②degraded 红增＋墙因变/③stable＋timing 不入对比
＋json/md 幂等字节恒同＋零写输入/④incomparable 候选集异＋非 audit 形/⑤md 输出/
⑥CLI 四码＋形坏拒判零出账——baseline_diff.py --selftest 矢量表自述）已由铸席
自证，本壳接进套件总入口并加用法面冒烟：
  1 --selftest rc=0 且 stdout 含 "BASELINE-DIFF-SELFTEST PASS" 冻结标记
  2 --help rc=0（argparse 用法面在位）
  3 --bogus rc=2／缺两账 rc=2／缺账文件 rc=9（退出码口径抽验——器口径
    0=improved/stable·1=degraded/incomparable（a failing result is data, not a tool failure）·2=用法错/
    输入形坏（schema 不对/账面自洽破）·9=路径缺失）

用法：
  python3 tests/test_baseline_diff.py    # 套件内经 run_tests.sh 调
  python3 -B tests/test_baseline_diff.py # 手动（-B 禁 __pycache__）

零触律：--selftest 全 tmp 合成基线自写自清；本壳三判零写盘零网络零编译零触
真仓；python3 -B 禁 __pycache__。退出码：0=三判全过；1=任一红（fail-loud
响亮列红·禁静默）。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "baseline_diff.py")
MARK = "BASELINE-DIFF-SELFTEST PASS"


def run(args):
    """子进程跑对比器（stdout+stderr 合流·零写盘零网络）。"""
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
    rc_c, _o = run([])
    rc_m, _o = run([os.path.join(REPO, "no-such-audit.json"),
                    os.path.join(REPO, "no-such-audit-2.json")])
    if not (rc_b == 2 and rc_c == 2 and rc_m == 9):
        fails.append("判3 退出码口径应 bogus=2/缺两账=2/缺账文件=9"
                     "（实测 %d/%d/%d）" % (rc_b, rc_c, rc_m))
    print("== test_baseline_diff: %d 过 / %d 红 ==" % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
