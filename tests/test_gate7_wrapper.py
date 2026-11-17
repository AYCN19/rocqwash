#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gate7_wrapper.py — wrapper/gate7_probe.sh ＋ wrapper/coqc_shim.sh 自测
（tests/·Mac 适配席 rqadapt·20261031）

十三判 subprocess 实跑（每例正/负判优先·零编译零网络零仓库写盘）：
  1  shim 语法            bash -n wrapper/coqc_shim.sh → rc=0
  2  probe 语法           bash -n wrapper/gate7_probe.sh → rc=0
  3  shim argv 契约       GATE7_PROBE_ROCQ=/bin/echo shim A B → stdout≡"c A B\\n"
                          （证 coqc <args> → `c` 子命令注入＋其余逐字透传）
  4  shim fail-loud       GATE7_PROBE_ROCQ=<不存在> → rc=9＋stderr 响亮
  5  probe 子帮助         -h → rc=0 且含 Usage 面头注
  6  probe 未知形参       --bogus → rc=2
  7  probe 缺 --tree      （无 --tree）→ rc=2
  8  probe tree 缺失      --tree <不存在> --module M → rc=9
  9  probe order/module 缺一 → rc=2
 10  probe order/module 同给（二义）→ rc=2
 11  probe module .v 不在世界副本 → rc=9
 12  probe gate7 正本缺失 GATE7_PROBE_SCRIPT=<不存在> → rc=9
 13  probe --dry-run      → rc=0；stdout 含 guard 档位正典形与 python3 -B/
                          --tree/--coqc 透传面；order 文件装配在 workdir 内
                          （临时目录·即写即清）

幂等：临时面全在 tempfile 目录并 finally 清理；不触两仓正本、不触各 agent 域。
退出码：0=十三判全过；1=任一红。
"""
import os
import subprocess
import sys
import tempfile
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIM = os.path.join(REPO, "wrapper", "coqc_shim.sh")
PROBE = os.path.join(REPO, "wrapper", "gate7_probe.sh")
MISSING = os.path.join(os.sep, "tmp", "rqadapt_nonexistent_gate7_probe_target")


def sh(args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def main():
    ok = True
    tmp = tempfile.mkdtemp(prefix="rqadapt_g7wrap_")
    try:
        def judge(n, desc, cond, detail=""):
            nonlocal ok
            print("  judge%d %s: %s%s" % (n, desc, "PASS" if cond else "FAIL",
                                         ("" if cond else "  " + detail)))
            ok = ok and cond

        rc, out, err = sh(["bash", "-n", SHIM])
        judge(1, "shim 语法 bash -n", rc == 0, "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", "-n", PROBE])
        judge(2, "probe 语法 bash -n", rc == 0, "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", SHIM, "A B", "--x"], env={"GATE7_PROBE_ROCQ": "/bin/echo"})
        judge(3, "shim argv 契约 c 注入＋逐字透传", rc == 0 and out == "c A B --x\n",
              "rc=%s out=%r" % (rc, out))

        rc, out, err = sh(["bash", SHIM, "--version"],
                          env={"GATE7_PROBE_ROCQ": os.path.join(tmp, "no_rocq")})
        judge(4, "shim fail-loud rc=9", rc == 9 and "missing" in err and "rocq" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "-h"])
        judge(5, "probe 子帮助 -h rc=0", rc == 0 and "Usage" in out,
              "rc=%s out=%r" % (rc, out[:120]))

        rc, out, err = sh(["bash", PROBE, "--bogus"])
        judge(6, "probe 未知形参 rc=2", rc == 2 and "unknown arg" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE])
        judge(7, "probe 缺 --tree rc=2", rc == 2 and "--tree" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "--tree", MISSING, "--module", "M"])
        judge(8, "probe tree 缺失 rc=9", rc == 9 and MISSING in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "--tree", tmp])
        judge(9, "probe order/module 缺一 rc=2", rc == 2 and "--order" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "--tree", tmp, "--order", MISSING, "--module", "M"])
        judge(10, "probe order/module 同给 rc=2", rc == 2,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "--tree", tmp, "--module", "NoSuchMod"])
        judge(11, "probe module .v 不在副本 rc=9", rc == 9 and "NoSuchMod" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "--tree", tmp, "--module", "M",
                           "--workdir", os.path.join(tmp, "w12"),
                           "--gate-script", MISSING])
        judge(12, "probe gate7 正本缺失 rc=9", rc == 9 and MISSING in err,
              "rc=%s err=%r" % (rc, err[:200]))

        world = os.path.join(tmp, "world")
        work = os.path.join(tmp, "w13")
        os.makedirs(world)
        with open(os.path.join(world, "DemoMod.v"), "w") as f:
            f.write("Definition demo_id (x:nat) := x.\n")
        jout = os.path.join(tmp, "j13.json")
        rc, out, err = sh(["bash", PROBE, "--tree", world, "--module", "DemoMod",
                           "--workdir", work, "--json", jout, "--dry-run"])
        order_path = os.path.join(work, "order_gate7_probe.txt")
        order_txt = ""
        if os.path.isfile(order_path):
            with open(order_path) as f:
                order_txt = f.read()
        judge(13, "probe --dry-run 出账＋order 装配",
              rc == 0
              and "GATE7-PROBE-DRYRUN guard:" in out
              and "-Front 0 -Mid 1 -MaxWaitSec 600" in out
              and "python3 -B" in out
              and "--tree" in out and world in out
              and "--coqc" in out and SHIM in out
              and jout in out
              and os.path.isfile(order_path) and order_txt == "DemoMod\n",
              "rc=%s out=%r order=%r" % (rc, out[:300], order_txt[:60]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("TEST-GATE7-WRAPPER:", "PASS (13/13)" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
