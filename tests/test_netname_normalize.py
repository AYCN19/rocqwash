#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_netname_normalize.py — tools/netname_normalize.py 自测（tests/·本轮实战
判例工具化①·20261101）

.v.v 双后缀名净名归一器（<净名>.v.v→<净名>.v）：
  1 自证        工具 --selftest 八判全过（rc 0）
  2 干跑默认    映射表出账（MAP 行逐条）·零字节落盘（件仍在·目标不新建）→ rc 1 PENDING
  3 apply 正判  归一落盘 → rc 0·目标在·源不在·内容逐字节恒等（改名不改字节）
  4 md5 验讫    apply 出账 RENAME 行带 md5=＋VERIFY-OK（冻结律机械化在账）
  5 COLLIDE     X.v 与 X.v.v 并存 → rc 1·拒改名不覆写（对侧件内容保全原样）
  6 净世界      无 .v.v → rc 0 NORMALIZE-CLEAN
  7 CLI 四码    --help 0／未知形参 2／缺 --dir 2／--dir 缺失 9
  8 出账面      --map TSV 行形 <src>\t<dst>／--json verdict·entries 咬合
  9 子目录      sub/B.v.v → sub/B.v（os.walk 全索引·/ 归一相对路径）

幂等：临时目录即写即清·零仓库写盘·零网络·零触真仓。
退出码：0=九节全过；1=任一红。
"""
import io
import os
import subprocess
import sys
import tempfile
import shutil
import json

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "netname_normalize.py")

BODY_A = "Lemma a : True.\nProof. exact I. Qed.\n"
BODY_B = "Definition b := 1.\n"


def run(args):
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else ""
    return p


def wf(dirpath, name, text):
    fp = os.path.join(dirpath, name)
    with io.open(fp, "w", encoding="utf-8") as fh:
        fh.write(text)
    return fp


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_tnetname_")
    try:
        # 1 工具自证（八判）
        p = run(["--selftest"])
        check("selftest", p.returncode == 0 and "PASS" in p.stdout, p.stdout[-400:])

        # 2+3+4+9 干跑默认零落盘 → apply 归一 md5 验讫 → 字节恒等（根＋子目录两件）
        w = os.path.join(tmp, "world")
        os.makedirs(os.path.join(w, "sub"))
        wf(w, "A.v.v", BODY_A)
        wf(os.path.join(w, "sub"), "B.v.v", BODY_B)
        wf(w, "Clean.v", "Lemma c : True.\nProof. exact I. Qed.\n")  # 净名对照件
        p = run(["--dir", w])
        check("干跑_PENDING", p.returncode == 1 and "NORMALIZE-PENDING" in p.stdout
              and "MAP A.v.v -> A.v" in p.stdout and "MAP sub/B.v.v -> sub/B.v" in p.stdout,
              "rc=%d" % p.returncode)
        check("干跑_零落盘", os.path.isfile(os.path.join(w, "A.v.v"))
              and not os.path.exists(os.path.join(w, "A.v"))
              and os.path.isfile(os.path.join(w, "sub", "B.v.v")),
              "干跑不得改名/新建")
        src_bytes = io.open(os.path.join(w, "A.v.v"), "rb").read()
        p = run(["--dir", w, "--apply"])
        check("apply_rc0", p.returncode == 0 and "APPLY-DONE" in p.stdout,
              "rc=%d %s" % (p.returncode, p.stdout[-200:]))
        check("md5_验讫在账", "RENAME A.v.v" in p.stdout and "VERIFY-OK" in p.stdout
              and "md5=" in p.stdout, p.stdout)
        a_path = os.path.join(w, "A.v")
        b_path = os.path.join(w, "sub", "B.v")
        check("apply_落盘", os.path.isfile(a_path) and os.path.isfile(b_path)
              and not os.path.exists(os.path.join(w, "A.v.v"))
              and not os.path.exists(os.path.join(w, "sub", "B.v.v")),
              "改名后源亡标在")
        check("改名不改字节", io.open(a_path, "rb").read() == src_bytes
              and io.open(b_path, encoding="utf-8").read() == BODY_B,
              "内容逐字节恒等")
        check("净名对照件不误伤", os.path.isfile(os.path.join(w, "Clean.v"))
              and "Clean.v ->" not in p.stdout, "纯 .v 件不得入账")

        # 5 COLLIDE 拒覆写：X.v 与 X.v.v 并存 → rc 1·对侧件内容保全
        w2 = os.path.join(tmp, "world2")
        os.makedirs(w2)
        wf(w2, "X.v", "ORIGINAL-TARGET\n")
        wf(w2, "X.v.v", "DOUBLE-SUFFIX\n")
        p = run(["--dir", w2, "--apply"])
        check("COLLIDE_拒覆写", p.returncode == 1 and "COLLIDE" in p.stdout
              and io.open(os.path.join(w2, "X.v"), encoding="utf-8").read() == "ORIGINAL-TARGET\n"
              and os.path.isfile(os.path.join(w2, "X.v.v")),
              "rc=%d" % p.returncode)

        # 6 净世界 → rc 0 CLEAN
        w3 = os.path.join(tmp, "world3")
        os.makedirs(w3)
        wf(w3, "Ok.v", BODY_A)
        p = run(["--dir", w3])
        check("净世界_CLEAN", p.returncode == 0 and "NORMALIZE-CLEAN" in p.stdout,
              "rc=%d" % p.returncode)

        # 7 CLI 四码：--help 0／未知形参 2／缺 --dir 2／--dir 缺失 9
        p = run(["--help"])
        check("cli_help0", p.returncode == 0 and "usage" in p.stdout,
              "rc=%d" % p.returncode)
        p = run(["--bogus"])
        check("cli_未知形参2", p.returncode == 2, "rc=%d" % p.returncode)
        p = run([])
        check("cli_缺dir2", p.returncode == 2, "rc=%d" % p.returncode)
        p = run(["--dir", os.path.join(tmp, "nowhere")])
        check("cli_缺dir9", p.returncode == 9, "rc=%d" % p.returncode)

        # 8 出账面：--map TSV／--json 咬合
        w4 = os.path.join(tmp, "world4")
        os.makedirs(w4)
        wf(w4, "M.v.v", BODY_A)
        mapf = os.path.join(tmp, "map.tsv")
        jsonf = os.path.join(tmp, "acc.json")
        p = run(["--dir", w4, "--map", mapf, "--json", jsonf])
        rows = [ln.rstrip("\n").split("\t") for ln in io.open(mapf, encoding="utf-8")
                if ln.strip()]
        acc = json.load(io.open(jsonf, encoding="utf-8"))
        check("map_json_出账", rows == [["M.v.v", "M.v"]]
              and acc["verdict"] == "PENDING"
              and acc["entries"][0]["netname"] == "M",
              repr(rows) + repr(acc.get("verdict")))

        # 9 .v.v.v 形：一层一归一（N.v.v.v → N.v.v·重跑再剥·如实出账）
        w5 = os.path.join(tmp, "world5")
        os.makedirs(w5)
        wf(w5, "N.v.v.v", BODY_A)
        p = run(["--dir", w5])
        check("vvv_一层一归一", p.returncode == 1 and "N.v.v.v -> N.v.v" in p.stdout,
              "rc=%d" % p.returncode)

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-20s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-NETNAME-NORMALIZE FAIL: %d/%d 红" % (len(fails), len(checks)))
            return 1
        print("TEST-NETNAME-NORMALIZE PASS: selftest/干跑零落盘/apply归一/改名不改字节/"
              "COLLIDE拒覆写/净世界CLEAN/CLI四码/map+json出账/vvv一层一归一 九节全过"
              "（本轮实战判例工具化①）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
