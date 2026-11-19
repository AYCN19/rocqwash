#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_red_dispatch.py — tools/red_dispatch.py 自测壳（tests/·20261112 v46
集成席挂接·缺壳自补——器由铸席铸·总套挂接归集成席）

红事件路由器（哨红事件→动作预设路由·三档 preset report-only/suggest/auto·
缺省零执行·auto 显式才代跑 60s 帽 rc≠0 入账不改退出码·防重 state＋cooldown·
路由全挂既有 cw.sh 路由零新引擎·A 族内容红禁代修出 fix 清单·schema
rocqwash-red-route/1）挂接件：器自带 --selftest tmp 假仓根十二矢量组
（①路由表全族覆盖/②占位替换/③auto 执行实证/④state 防重/⑤cooldown/
⑥report-only 缺省零执行/⑦JSONL stdin 多事件/⑧fail-loud 面/⑨rc≠0 不改
退出码/⑩A 族 fix 清单＋C 族定令/⑪确定性/⑫整体单对象兜底——red_dispatch.py
--selftest 矢量表自述·离线零网络零编译）已由铸席自证，本壳接进套件总入口
并加用法面冒烟：
  1 --selftest rc=0 且 stdout 含 "RED-DISPATCH-SELFTEST PASS" 冻结标记
  2 --help rc=0（argparse 用法面在位）
  3 退出码口径抽验：--bogus rc=2／--dry-run 缺 auto 档 rc=2／事件文件缺
    rc=9（器口径 0=处理完成·a failing result is data, not a tool failure·assignment rc≠0/超时/跳过皆入账
    不改退出码；2=用法错；9=输入缺失）

用法：
  python3 tests/test_red_dispatch.py    # 套件内经 run_tests.sh 调
  python3 -B tests/test_red_dispatch.py # 手动（-B 禁 __pycache__）

零触律：--selftest 全 mkdtemp 自写自清（假 cw.sh 标记文件实证）；本壳三判
零写盘零网络零编译零触真仓；python3 -B 禁 __pycache__。退出码：0=三判全过；
1=任一红（fail-loud 响亮列红·禁静默）。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "red_dispatch.py")
MARK = "RED-DISPATCH-SELFTEST PASS"


def run(args):
    """子进程跑路由器（stdout+stderr 合流·零写盘零网络零编译）。"""
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
    rc_d, _o = run(["--dry-run", "--preset", "report-only"])
    rc_m, _o = run(["--event-file", os.path.join(REPO, "no-such-events.jsonl")])
    if not (rc_b == 2 and rc_d == 2 and rc_m == 9):
        fails.append("判3 退出码口径应 bogus=2/dry-run 误档=2/事件文件缺=9"
                     "（实测 %d/%d/%d）" % (rc_b, rc_d, rc_m))
    print("== test_red_dispatch: %d 过 / %d 红 ==" % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
