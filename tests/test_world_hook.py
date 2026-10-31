#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_world_hook.py — wash/world_hook.py 自测（tests/·五课反馈轮·席 rqsupport·20261101）

五课负例①【nw5 世界偏斜】：born 世界必须=RUNTREE 认证代 cp·禁自带旧代。
判例源：seat_nw5ver/账/world_md5_assert_npw.txt ASSERT4（自带 world 副本 WDIFF×14/
WMISS×2 实录）。本件在套件层独立复现该雷的机检负例（与工具 --selftest 互为旁证）：

  1 自证       工具 --selftest 十二判全过（rc 0）
  2 nw5 负例   偏斜世界（旧代 .vo）＋透传洗刀 → rc 9·WDIFF 词面·--out 零落盘
               （born 前断言拦下·引擎一步未跑）
  3 WMISS 负例 认证代基座缺件 → rc 9·WMISS 词面
  4 pos 正判   认证代世界（夹具锚现拍）→ rc 0·引擎真跑·产物落盘
  5 冻结旁证   wash/wash_engine.py md5 == 在册冻结值 664446bc…（钩子只读复用·
               零字节触伴——在役八组件冻结禁改的机检旁证）

幂等：临时目录即写即清·不触两仓正本/各 seat 域·零编译零网络。
退出码：0=五判全过；1=任一红。
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(REPO, "wash", "world_hook.py")
ENGINE = os.path.join(REPO, "wash", "wash_engine.py")
ENGINE_FROZEN_MD5 = "664446bc717395d8496c8c30a5af9ccf"  # 更新账.md §三在册值

ANCHOR_NAMES = ["S01_BaseRing", "S02_CauchyComplete", "S03_QExp",
                "UpReqLpoEquiv", "EntropyUnsatMark"]


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args):
    p = subprocess.run([sys.executable, "-B", HOOK] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else ""
    return p


def make_world(root, stale_first=False):
    """夹具世界：五锚名各一 .vo；stale_first=True 时首件写旧代内容。"""
    world = os.path.join(root, "world")
    os.makedirs(world)
    mds = {}
    for k, name in enumerate(sorted(ANCHOR_NAMES)):
        content = b"OLD-GEN-VO\n" if (stale_first and k == 0) else ("VO-%02d-%s\n" % (k, name)).encode()
        with io.open(os.path.join(world, name + ".vo"), "wb") as fh:
            fh.write(content)
        mds[name] = md5_of(os.path.join(world, name + ".vo"))
    return world, mds


def make_ledger(root):
    src_v = os.path.join(root, "vec.v")
    with io.open(src_v, "w", encoding="utf-8", newline="") as fh:
        fh.write("Lemma vec_a : forall x : nat, x = x.\nProof.\n  intros x. reflexivity.\nQed.\n")
    ledger = {"patches": [{"tag": "eq2id", "expect": 1,
                           "old": "Lemma vec_a : forall x : nat, x = x.\n",
                           "new": "Lemma vec_a : forall x : nat, Id nat x x.\n"}]}
    lp = os.path.join(root, "ledger.json")
    with io.open(lp, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh)
    return src_v, lp


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_tworldhook_")
    try:
        # 1 工具自证
        p = run(["--selftest"])
        check("selftest", p.returncode == 0 and "PASS" in p.stdout, p.stdout[-400:])

        # 2【nw5 负例】世界偏斜：born 前断言拦下·引擎零落盘
        stale_root = os.path.join(tmp, "stale")
        os.makedirs(stale_root)
        world_s, _ = make_world(stale_root, stale_first=True)
        src_v, lp = make_ledger(stale_root)
        out_v = os.path.join(stale_root, "vec_washed.v")
        fresh_root = os.path.join(tmp, "fresh")
        os.makedirs(fresh_root)
        world_f, mds = make_world(fresh_root)
        # 认证代锚 manifest（套件夹具·形承 world_md5_assert.txt 表列形·对 fresh 现拍）
        man = os.path.join(stale_root, "man.txt")
        with io.open(man, "w", encoding="utf-8") as fh:
            for n in sorted(mds):
                fh.write("%s  %s.vo  OK\n" % (mds[n], n))
        p = run(["--world", world_s, "--manifest", man, "--",
                 "--file", src_v, "--patch", lp, "--out", out_v])
        check("nw5_WDIFF_负例", p.returncode == 9 and "WDIFF" in p.stdout
              and not os.path.exists(out_v),
              "rc=%d out_exists=%s" % (p.returncode, os.path.exists(out_v)))

        # 3 WMISS 负例
        p = run(["--world", world_f, "--anchor", "Absent_Mod=%s" % ("0" * 32)])
        check("WMISS_负例", p.returncode == 9 and "WMISS" in p.stdout,
              "rc=%d" % p.returncode)

        # 4 pos：认证代世界＋透传洗刀 → rc 0·产物落盘
        out_v2 = os.path.join(fresh_root, "vec_washed.v")
        p = run(["--world", world_f, "--manifest", man, "--",
                 "--file", src_v, "--patch", lp, "--out", out_v2])
        check("pos_透传", p.returncode == 0 and os.path.isfile(out_v2)
              and "WORLD-BASE-OK" in p.stdout, "rc=%d" % p.returncode)

        # 5 冻结旁证：引擎 md5 仍=在册冻结值
        check("冻结件零触", md5_of(ENGINE) == ENGINE_FROZEN_MD5,
              "md5=%s" % md5_of(ENGINE))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-14s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-WORLD-HOOK FAIL: %d/%d 红" % (len(fails), len(checks)))
            return 1
        print("TEST-WORLD-HOOK PASS: selftest/nw5偏斜负例/WMISS负例/pos透传/冻结旁证 五判全过"
              "（五课负例①nw5·世界基）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
