#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_registry_audit.py — tools/registry_audit.py 自测壳（tests/·20261112
v46 集成席挂接·缺壳自补——器由铸席铸·总套挂接归集成席）

注册册卫生审计器（order.txt/_CoqProject 双册只读四账出账：重复行/锚撞文本/
顺序号形/形怪/缺锚/孤儿/live 拓扑引用＋--fix-plan 确定性处方零写盘·--apply
不存在·键式/锚正典直用 tools/registry_union.py 零重造·病灶是数据恒 exit 0·
schema rocqwash-registry-audit/1）挂接件：器自带 --selftest tmp 合成 v35
真账形态矢量组（四账判类全谱/处方保首＋77c2b9a8 md5 冻结向量＋占位/只读
实证双册与 live 树前后 md5 恒同/确定性重跑字节恒同/--git 直读 tmp clone＋
坏 ref 9/CLI 四码——registry_audit.py --selftest 矢量表自述·零触真仓零网络
零编译）已由铸席自证，本壳接进套件总入口并加用法面冒烟：
  1 --selftest rc=0 且 stdout 含 "REGISTRY-AUDIT-SELFTEST PASS" 冻结标记
  2 --help rc=0（argparse 用法面在位）
  3 退出码口径抽验：--bogus rc=2／无输入面 rc=2／半册 rc=2／缺册文件
    rc=9（器口径 0=出账·病灶是数据 count>0 仍 0；2=用法错；9=输入缺）

用法：
  python3 tests/test_registry_audit.py    # 套件内经 run_tests.sh 调
  python3 -B tests/test_registry_audit.py # 手动（-B 禁 __pycache__）

零触律：--selftest 全 mkdtemp 自写自清（tmp 合成双册＋tmp clone）；本壳三判
零写盘零网络零编译零触真仓；python3 -B 禁 __pycache__。退出码：0=三判全过；
1=任一红（fail-loud 响亮列红·禁静默）。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "registry_audit.py")
MARK = "REGISTRY-AUDIT-SELFTEST PASS"


def run(args):
    """子进程跑审计器（stdout+stderr 合流·零写盘零网络零编译）。"""
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
    rc_e, _o = run([])
    rc_h, _o = run(["--order", os.path.join(REPO, "tests", "fixtures",
                                             "names_sample.v")])
    rc_m, _o = run(["--order", os.path.join(REPO, "no-such-order.txt"),
                    "--project", os.path.join(REPO, "no-such-project.txt")])
    if not (rc_b == 2 and rc_e == 2 and rc_h == 2 and rc_m == 9):
        fails.append("判3 退出码口径应 bogus=2/无输入面=2/半册=2/缺册=9"
                     "（实测 %d/%d/%d/%d）" % (rc_b, rc_e, rc_h, rc_m))
    print("== test_registry_audit: %d 过 / %d 红 ==" % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
