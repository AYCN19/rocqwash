#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_recipe_enbig7_pw1.py — recipes/ENBIG7_same_domain_collision_PW1.md 处方件自测
（tests/·巡检打磨轮·agent rqsup4·20261101）

五课件③【dver2-enbig7 同域撞·私占世界重建 PW1】：越界席写穿他席独占写域→世界面
置换/污染；处方＝仲裁收敛→待静（入侵期产物不采）→全量重审计→私占世界按 order.txt
链序 born→三度 md5 复断。判例源：seat_dver2/账/collision_enbig7_20261031.md
（主会话仲裁 36c35816·25/25 对源断言·24 链件链序 born 全 rc=0·三度复断零篡改）。

  1 处方件在册  recipes/ENBIG7_same_domain_collision_PW1.md 在盘且判例锚词面齐
                （PW1／collision_enbig7_20261031／36c35816／待静／全量重审计／
                 私占世界／order.txt 链序／三度／未采／锚必随代换）
  2 前兆负例    【判例 enbig7 形】同一模块名出现在 ≥2 份批选清单 → select_audit
                DUP-CROSS failing rc 1（撞名前兆机检·tools/select_audit.py）
  3 世界偏斜负例【入侵置换形】fixture 世界 .vo 被置换（≠认证代锚）→ world_hook
                WDIFF→rc 9·洗引擎未跑零落盘（wash/world_hook.py·-- 透传形）
  4 愈面正判    【私占重建后形】fixture 世界按现拍认证代锚全等 → WORLD-BASE-OK
                rc 0·透传形引擎真跑落盘（锚=现拍 md5·锚必随代换的机械同构）
  5 冻结旁证    wash/wash_engine.py md5 == 在册冻结值 664446bc…（只读 import 面零触）

幂等：临时目录即写即清·零仓库写盘·零编译零网络（世界基断言为纯 md5 differential comparison）。
退出码：0=五判全过；1=任一红。
"""
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECIPE = os.path.join(REPO, "recipes", "ENBIG7_same_domain_collision_PW1.md")
HOOK = os.path.join(REPO, "wash", "world_hook.py")
AUDIT = os.path.join(REPO, "tools", "select_audit.py")
ENGINE = os.path.join(REPO, "wash", "wash_engine.py")
ENGINE_FROZEN_MD5 = "664446bc717395d8496c8c30a5af9ccf"  # 更新账.md §三在册值

RECIPE_ANCHORS = [
    "PW1", "collision_enbig7_20261031", "36c35816",
    "待静", "全量重审计", "私占世界", "order.txt 链序", "三度", "未采",
    "锚必随代换", "world_hook", "select_audit", "DUP-CROSS",
]


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(argv):
    import subprocess
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_trecipepw1_")
    try:
        # 1 处方件在册＋判例锚词面齐
        ok1 = os.path.isfile(RECIPE)
        missing = []
        if ok1:
            with io.open(RECIPE, encoding="utf-8") as fh:
                doc = fh.read()
            missing = [a for a in RECIPE_ANCHORS if a not in doc]
            ok1 = not missing
        else:
            missing = ["<处方件整缺>"]
        check("处方件锚词面", ok1, "缺锚=%s" % missing)

        # 2【前兆负例·enbig7 判例形】同件双认领 → DUP-CROSS failing rc 1
        order = os.path.join(tmp, "order.txt")
        with io.open(order, "w", encoding="utf-8") as fh:
            fh.write("S03_QExp.v#R0-d66910\nDver2_Target.v#R28-f09c39\n")
        b1 = os.path.join(tmp, "b_dver2.txt")
        b2 = os.path.join(tmp, "b_enbig7.txt")
        with io.open(b1, "w", encoding="utf-8") as fh:
            fh.write("Dver2_Target.v\n")  # dver2 席批选
        with io.open(b2, "w", encoding="utf-8") as fh:
            fh.write("Dver2_Target.v\n")  # enbig7 席同件认领（越界前兆）
        p = run([sys.executable, "-B", AUDIT, "--order", order,
                 "--select", b1, "--select", b2])
        check("前兆负例_DUP-CROSS", p.returncode == 1 and "DUP-CROSS" in p.stdout,
              "rc=%d out=%s" % (p.returncode, p.stdout[:200]))

        # 3/4 共用夹具：私占世界（五锚现拍=认证代·world_hook 内置五锚名齐）
        # 与入侵置换世界（同表 S01 被置换旧代体·余四锚同值）
        src_v = os.path.join(tmp, "vec.v")
        with io.open(src_v, "w", encoding="utf-8", newline="") as fh:
            fh.write("Lemma vec_a : forall x : nat, x = x.\nProof.\n  intros x. reflexivity.\nQed.\n")
        ledger = {"patches": [{"tag": "eq2id", "expect": 1,
                               "old": "Lemma vec_a : forall x : nat, x = x.\n",
                               "new": "Lemma vec_a : forall x : nat, Id nat x x.\n"}]}
        ledger_p = os.path.join(tmp, "ledger.json")
        with io.open(ledger_p, "w", encoding="utf-8") as fh:
            json.dump(ledger, fh)

        ANCHOR_NAMES = ["EntropyUnsatMark", "S01_BaseRing", "S02_CauchyComplete",
                        "S03_QExp", "UpReqLpoEquiv"]  # world_hook BUILTIN_ANCHORS 五名
        world = os.path.join(tmp, "world_pw1")      # 私占重建后形：五锚现拍=认证代
        os.makedirs(world)
        anchor_args = []
        for k, name in enumerate(sorted(ANCHOR_NAMES)):
            with io.open(os.path.join(world, name + ".vo"), "wb") as fh:
                fh.write(("CERTIFIED-GEN-VO-%02d-%s\n" % (k, name)).encode())
            anchor_args += ["--anchor", "%s=%s" % (name, md5_of(os.path.join(world, name + ".vo")))]

        world_inv = os.path.join(tmp, "world_invaded")  # 入侵置换形：S01 同件旧代体
        os.makedirs(world_inv)
        for name in sorted(ANCHOR_NAMES):
            body = b"INVADER-STALE-VO\n" if name == "S01_BaseRing" \
                else open(os.path.join(world, name + ".vo"), "rb").read()
            with io.open(os.path.join(world_inv, name + ".vo"), "wb") as fh:
                fh.write(body)

        out_v = os.path.join(tmp, "vec_washed.v")

        # 3【世界偏斜负例·入侵置换形】错代世界 → S01 WDIFF rc 9·引擎未跑零落盘
        p = run([sys.executable, "-B", HOOK, "--world", world_inv]
                + anchor_args + ["--",
                                 "--file", src_v, "--patch", ledger_p, "--out", out_v])
        check("偏斜负例_WDIFF拦截",
              p.returncode == 9 and "WDIFF" in p.stdout and not os.path.exists(out_v),
              "rc=%d out=%s" % (p.returncode, p.stdout[:200]))

        # 4【愈面正判·私占重建后形】认证代世界 → WORLD-BASE-OK·透传引擎真跑
        p = run([sys.executable, "-B", HOOK, "--world", world]
                + anchor_args + ["--",
                                 "--file", src_v, "--patch", ledger_p, "--out", out_v])
        check("愈面正判_WORLD-BASE-OK",
              p.returncode == 0 and "WORLD-BASE-OK" in p.stdout
              and os.path.isfile(out_v),
              "rc=%d out=%s" % (p.returncode, p.stdout[:200]))

        # 5 冻结旁证：引擎 md5 仍=在册冻结值（只读 import 面零触）
        check("冻结件零触", md5_of(ENGINE) == ENGINE_FROZEN_MD5,
              "md5=%s" % md5_of(ENGINE))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-22s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-RECIPE-PW1 FAIL: %d/%d 红" % (len(fails), len(checks)))
            return 1
        print("TEST-RECIPE-PW1 PASS: 处方件锚/前兆DUP-CROSS/偏斜WDIFF拦截/"
              "愈面WORLD-BASE-OK/冻结旁证 五判全过（五课件③同域撞私占世界处方）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
