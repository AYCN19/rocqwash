#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_precedent_station.py — wrapper/precedent_station.py 三判例验收站自测
（tests/·巡检打磨轮·席 rqsup4·20261101）

五课件⑤【三判例剧本 toolify】：E7 载体中继／R23 记号重载／E5 投影重锚三判例共用
验收链（①names 对表→②gate4→③gate7 可选）一站化。本测试只打**轻链①②**与站级
形制面（③gate7 为真编译重步·其 launcher 形制归 t_gate7_wrapper 判例——本件不重跑）。

  1 站自检      --station-selftest 十判 rc=0
  2 正判烟      fixture 刀后件/基件（语句面全等·证明体异——E7 判例「语句零动」形）
                → steps names,gate4 → exit 0·站账 verdict=PASS·knife 记名在账
  3 负判        刀后件多一语句（语句面动刀违 E7 铁律）→ names rc=2 → exit 1·FAIL
  4 REVIEW 升格 --gate4-length-cap 压帽（头注超标复核级）→ gate4 rc=2 → exit 2
  5 gate7 形制  gate7 在步缺 --gate7-module → exit 9 零开步（预检拦截）
  6 刀面记名面  未知刀面 → exit 2；合法刀面站账落 knife 字段（记录面·不影响判词）
  7 冻结旁证    names/gate4 两正本 md5 == 在册冻结值（站 pin 断言同源零触）

幂等：临时目录即写即清·零仓库写盘·零编译零网络（gate7 步不实跑）。
退出码：0=七判全过；1=任一红。
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATION = os.path.join(REPO, "wrapper", "precedent_station.py")
NAMES = os.path.join(REPO, "names", "mac_stmt_names.py")
GATE4 = os.path.join(REPO, "verify", "gate4_comment_guard.py")
NAMES_FROZEN_MD5 = "01dc635ce445b05628bdd6e728990ce3"   # 更新账.md §三在册值
GATE4_FROZEN_MD5 = "d7ab397c5f0243d0c7320f91d0f14481"   # 更新账.md §三在册值

HEADER = """(* precedent_station_fixture.v — 三判例验收站夹具（rocqwash tests/自造·零外部素材）。

   Mission.  Exercise the three-precedent acceptance chain lightly (names+gate4).
   Dependencies.  Rocq standard library only.
   References.  recipes/S07_projection_reanchor_E5.md; update ledger five-lessons.
   Constructivity.  Set-carried statements; proofs close with Qed; no classics.
   Build.  rocq c -native-compiler no -q -Q . "" precedent_station_fixture.v
*)

"""


def base_body(fn_name):
    return ("Require Import QArith.\n\n"
            "Lemma %s : forall x y : Q, QltT x y -> QltT (x + y) (y + x).\n"
            "Proof.\n  intros x y H. exact H.\nQed.\n" % fn_name)


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args):
    p = subprocess.run([sys.executable, "-B", STATION] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p


def write(tmp, name, text):
    fp = os.path.join(tmp, name)
    with io.open(fp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return fp


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_tprecstation_")
    try:
        # 1 站自检十判
        p = run(["--station-selftest"])
        check("站自检十判", p.returncode == 0 and "PRECEDENT-STATION-SELFTEST" in p.stdout
              and "PASS" in p.stdout, "rc=%d out=%s" % (p.returncode, p.stdout[-300:]))

        # fixture：刀后件=语句面全等＋证明体异（E7 判例「语句零动·证明体换刀」形）
        baseline = write(tmp, "baseline.v", HEADER + base_body("ps_fix_order"))
        cured = write(tmp, "cured.v", HEADER + base_body("ps_fix_order").replace(
            "intros x y H. exact H.",  # 证明体换刀（对表不过问·gate4 不过问）
            "intros x y H. simpl. exact H."))
        # 负判件：语句面多一句（动语句面·违链① N=N）
        cured_bad = write(tmp, "cured_bad.v", HEADER + base_body("ps_fix_order")
                          + "\nLemma ps_fix_extra : forall x : Q, QleT x x.\n"
                            "Proof. intros x. apply Qle_refl.\nQed.\n")

        # 2 正判烟：轻链①②全绿·站账落 knife 记名
        sj = os.path.join(tmp, "station_pos.json")
        p = run(["--cured", cured, "--baseline", baseline,
                 "--knife", "E7-carrier", "--station-json", sj])
        acc = {}
        if os.path.isfile(sj):
            with io.open(sj, encoding="utf-8") as fh:
                acc = json.load(fh)
        check("正判烟_轻链绿", p.returncode == 0 and acc.get("verdict") == "PASS"
              and acc.get("knife") == "E7-carrier"
              and acc.get("steps", {}).get("names", {}).get("rc") == 0
              and acc.get("steps", {}).get("gate4", {}).get("rc") == 0,
              "rc=%d acc=%s out=%s" % (p.returncode, json.dumps(acc)[:200], p.stdout[-300:]))

        # 3 负判：语句面多一句 → ①rc=2 FAIL → 站 exit 1（硬者胜·不短路仍出②账）
        p = run(["--cured", cured_bad, "--baseline", baseline,
                 "--knife", "E7-carrier"])
        check("负判_语句面动刀_exit1", p.returncode == 1 and "FAIL" in p.stdout
              and "①对表" in p.stdout and "②gate4" in p.stdout,
              "rc=%d out=%s" % (p.returncode, p.stdout[-300:]))

        # 4 REVIEW 升格：--gate4-length-cap 5（夹具头注 9 行超标复核级）→ exit 2
        p = run(["--cured", cured, "--baseline", baseline,
                 "--gate4-length-cap", "5"])
        check("REVIEW升格_exit2", p.returncode == 2 and "REVIEW" in p.stdout,
              "rc=%d out=%s" % (p.returncode, p.stdout[-300:]))

        # 5 gate7 形制：gate7 在步缺 --gate7-module → 站级用法错 exit 2 零开步；
        #   module 给名但 .v 不在世界副本 → 预检 exit 9 零开步
        p = run(["--cured", cured, "--baseline", baseline,
                 "--steps", "names,gate4,gate7", "--gate7-tree", tmp])
        c5a = p.returncode == 2 and "①对表" not in p.stdout
        p = run(["--cured", cured, "--baseline", baseline,
                 "--steps", "names,gate4,gate7", "--gate7-tree", tmp,
                 "--gate7-module", "NoSuchMod"])
        check("gate7形制_2缺module_9缺件零开步",
              c5a and p.returncode == 9 and "①对表" not in p.stdout,
              "rc9=%d out=%s" % (p.returncode, p.stdout[-300:]))

        # 6 刀面记名面：未知刀面拒 exit 2
        p = run(["--cured", cured, "--baseline", baseline, "--knife", "bogus-knife"])
        check("未知刀面拒_exit2", p.returncode == 2 and "未知刀面" in p.stdout,
              "rc=%d out=%s" % (p.returncode, p.stdout[-300:]))

        # 7 冻结旁证：两正本 md5 == 在册冻结值（站 pin 断言同源）
        check("冻结件零触", md5_of(NAMES) == NAMES_FROZEN_MD5
              and md5_of(GATE4) == GATE4_FROZEN_MD5,
              "names=%s gate4=%s" % (md5_of(NAMES), md5_of(GATE4)))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-24s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-PRECEDENT-STATION FAIL: %d/%d 红" % (len(fails), len(checks)))
            return 1
        print("TEST-PRECEDENT-STATION PASS: 站自检/正判烟knife记账/负判exit1/"
              "REVIEW升格exit2/gate7形制9/刀面拒2/冻结旁证 七判全过（五课件⑤三判例验收站）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
