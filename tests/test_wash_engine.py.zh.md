#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_wash_engine.py — wash/wash_engine.py 通用逐件洗引擎自测（rocqwash tests/）。

与 tests/test_wash_fixture.py（测战役件 _abl1_wash.py·模块导入＋ROOT 补丁）平行：
本测经 subprocess 走 wash_engine.py 真实 argv CLI（通用件无硬编码路径·无需补丁），
在 mkdtemp 临时目录播种 fixture，六判：

  正判 pos    ：两 tag 台账 → 全 APPLY·exit 0；落盘 count(new)==expect、count(old)==0；
                嵌套注释 `(* nest (* deep *) outer *)` 原样保留（剥掩蔽机不伤正文）。
  幂等 idem   ：对洗后产物同账重放 → 全 SKIP（applied=0 skipped=N）·exit 0·产物逐字节恒等
                （CONTRIBUTING §4 洗类 PR 须附的幂等重放口径）。
  反判 neg    ：破坏首个 tag 的 old 精确串 → 该 tag FAIL·exit 1·产物逐字节未动
                （fail-loud·选择性落盘失守即红）。
  括号反判    ：old 括号失衡（嵌套括号感知）→ exit 2·零写。
  隔离反判    ：--out == --file → exit 2（写隔离）。
  CLI 契约    ：无 --patch 裸调/位置形 → exit 3（SKIP 语义·make demo 判据）；
                缺 --file → exit 2；--file/--patch 路径缺失 → exit 9。

全程只写 mkdtemp 临时目录（测毕即删）；仓库零写入；重复运行结果恒同。
用法：python3 tests/test_wash_engine.py   # 全过 exit 0
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL = os.path.join(REPO, "wash", "wash_engine.py")

BODY = ("(* nest (* deep *) outer *)\n"
        "Lemma vec_a : forall x : nat, x = x.\n"
        "Proof.\n"
        "  intros x. reflexivity.\n"
        "Qed.\n")

LEDGER = {"patches": [
    {"tag": "eq2id", "expect": 1,
     "old": "Lemma vec_a : forall x : nat, x = x.\n",
     "new": "Lemma vec_a : forall x : nat, Id nat x x.\n"},
    {"tag": "refl2id", "expect": 1,
     "old": "  intros x. reflexivity.\n",
     "new": "  intros x. apply id_refl.\n"},
]}


def run(args):
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def main():
    tmp = tempfile.mkdtemp(prefix="rocqwash_washeng_t_")
    try:
        src = os.path.join(tmp, "vec.v")
        with io.open(src, "w", encoding="utf-8", newline="") as fh:
            fh.write(BODY)
        ledger_p = os.path.join(tmp, "ledger.json")
        with io.open(ledger_p, "w", encoding="utf-8") as fh:
            json.dump(LEDGER, fh)
        out = os.path.join(tmp, "vec_washed.v")

        # ---------- 正判 pos ----------
        rc, so, se = run(["--file", src, "--patch", ledger_p, "--out", out])
        assert rc == 0, "pos: exit 应 0 实测 %d\n%s%s" % (rc, so, se)
        assert "applied=2 skipped=0 fail=NO" in so, so
        with io.open(out, encoding="utf-8", newline="") as fh:
            washed = fh.read()
        assert washed.count("Id nat x x") == 1 and washed.count("apply id_refl") == 1, washed
        assert washed.count("x = x.") == 0 and washed.count("reflexivity") == 0, washed
        assert "nest (* deep *) outer" in washed, "嵌套注释应原样保留"
        assert "md5 src=" in so and "out=" in so, "源/产物 md5 应双出账"

        # ---------- 幂等 idem（CONTRIBUTING §4：applied=0 skipped=N）----------
        before = open(out, "rb").read()
        out2 = os.path.join(tmp, "vec_washed2.v")
        rc, so, se = run(["--file", out, "--patch", ledger_p, "--out", out2])
        assert rc == 0, "idem: exit 应 0 实测 %d\n%s%s" % (rc, so, se)
        assert "applied=0 skipped=2 fail=NO" in so, so
        assert open(out2, "rb").read() == before, "idem: 产物应逐字节恒等"

        # ---------- 反判 neg（fail-loud·坏文件不落盘）----------
        with io.open(src, "w", encoding="utf-8", newline="") as fh:
            fh.write(BODY.replace("x = x.", "x = (x)."))
        rc, so, se = run(["--file", src, "--patch", ledger_p, "--out", out])
        assert rc == 1, "neg: exit 应 1 实测 %d\n%s%s" % (rc, so, se)
        assert "FAIL" in so and "NOT-WRITTEN" in so, so
        assert open(out, "rb").read() == before, "neg: fail-loud 失守（产物被改）"

        # ---------- 括号反判（嵌套括号感知）----------
        bad = os.path.join(tmp, "bad.json")
        with io.open(bad, "w", encoding="utf-8") as fh:
            json.dump({"patches": [{"tag": "b", "old": "f (x.", "new": "g x", "expect": 1}]}, fh)
        rc, so, se = run(["--file", src, "--patch", bad, "--out", out])
        assert rc == 2, "bracket-neg: exit 应 2 实测 %d\n%s%s" % (rc, so, se)
        assert "嵌套括号感知" in se, se

        # ---------- 隔离反判（--out == --file）----------
        with io.open(src, "w", encoding="utf-8", newline="") as fh:
            fh.write(BODY)
        rc, so, se = run(["--file", out, "--patch", ledger_p, "--out", out])
        assert rc == 2, "isolation: exit 应 2 实测 %d\n%s%s" % (rc, so, se)
        assert "写隔离" in se, se

        # ---------- CLI 契约 ----------
        rc, _, _ = run(["--file", src])                       # 无台账 → 3
        assert rc == 3, "no-ledger: exit 应 3 实测 %d" % rc
        rc, _, _ = run([src])                                 # 位置形裸调 → 3（make demo 形）
        assert rc == 3, "positional-bare: exit 应 3 实测 %d" % rc
        rc, _, _ = run(["--patch", ledger_p, "--out", out])   # 有账缺 --file → 2
        assert rc == 2, "no-file: exit 应 2 实测 %d" % rc
        rc, _, _ = run(["--file", src, "--patch", os.path.join(tmp, "gone.json"), "--out", out])
        assert rc == 9, "missing-patch: exit 应 9 实测 %d" % rc
        rc, _, _ = run(["--file", os.path.join(tmp, "gone.v"), "--patch", ledger_p, "--out", out])
        assert rc == 9, "missing-file: exit 应 9 实测 %d" % rc

        print("WASH-ENGINE PASS: pos(2 APPLY·count 断言·嵌套注释保留)/idem(applied=0 skipped=2·逐字节恒等)"
              "/neg(FAIL·NOT-WRITTEN)/bracket-neg(2)/isolation(2)/CLI(3·3·2·9·9) 全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
