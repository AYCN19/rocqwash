#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""select_audit.py — 选件审计器：批选清单对树 order.txt 全表 grep 剔重（rocqwash tools/·
20261101 席 rqsupport）

五课反馈轮打磨件②（nw6 课＋dver2-enbig7 课工具化）：
  - **nw6 课**：选件勘定员必须**实读树 order.txt 全表 grep 剔重·禁凭记忆**。
    判例源：`sandbox/seat_nw6/账/候批账-nw6批.md`（HansonLcm 混入实录在卷——同 seat 域
    他席在飞件 `work/HansonLcm.v`（15:33:04）与本席批作业同域并行，靠冻结时点全表
    实扫才勘明零互覆；凭记忆报批即有混入他席件之险）。本器把「全表实读」机械化：
    每个候选名都对 order.txt **逐行**归一化比对，不做任何记忆/缓存捷径。
  - **dver2-enbig7 课**：同件双席并行各带 born 闸必撞世界。判例源：
    `sandbox/seat_dver2/账/collision_enbig7_20261031.md`（enbig7 席越界写 seat_dver2
    域·两次 born 失败＝世界规格残缺仍 born 之工序缺陷·主会话仲裁 36c35816）。
    本器把「同件双认领」前兆机械化：同一模块名出现在 ≥2 份批选清单＝DUP-CROSS 撞名红。

审计四判（全部 RED 才 exit 1·任一即红）：
  DUP-BATCH    同一批选清单内同名重复（凭记忆选件之典型误）
  DUP-CROSS   同一模块名出现在 ≥2 份批选清单（同域双席撞名前兆·enbig7 判例）
  NOT-IN-ORDER 候选名不在树 order.txt 全表（选了树里没有的件）
  DUP-ORDER    树 order.txt 自身同名多行（注册表重复·全表 grep 方能现形）

用法：
  python3 tools/select_audit.py --order <order.txt> --select <batch.txt>
                                [--select <batch2.txt> …] [--json out.json]
  python3 tools/select_audit.py --order <order.txt> --grep <名>   # 单名全表 grep
  python3 tools/select_audit.py --selftest

名归一（order 行与批选行同律）：剥首尾空白→剥 #注释→剥 #代签（`名.v#R0-d66910`
与裸名与 `名.v` 三形同归一）→剥 .v 后缀。全词比对防前缀误咬（UpReqBanach ≠
UpReqBanachExp——born_world assert_md5 同律）。

退出码：0=AUDIT-CLEAN（四判零发现）；1=AUDIT-RED（任一发现）；2=用法错；
        9=路径缺失（fail-loud 不模拟）。--grep 形：0=命中／1=未命中。
写隔离：本件只读两形参文件；唯一写盘面＝显式 --json 出账路径。
"""
import argparse
import io
import json
import os
import re
import sys

PROG = "select_audit"


def normalize_line(line):
    """行→模块名：#注释/#代签剥离＋.v 后缀剥离＋空白剥离。空/注释行→None。

    名允许内嵌 `/` 路径形（实盘认证表 scripts/order.txt 671 行中有
    `Local/LW0LeibSeparation.v#R160-eb42d3` 一行·20261101 实测）——审计器必须能
    实读整表，禁因个别行形拒表。
    """
    s = line.strip()
    s = s.split("#", 1)[0].strip()  # 剥 #注释与 #代签（名.v#R0-d66910 → 名.v）
    if not s:
        return None
    if s.endswith(".v"):
        s = s[:-2]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*/?[A-Za-z0-9_'/]*", s):
        raise AuditError("非法模块名 %r（归一后须标识符或标识符/路径形）" % line.strip())
    return s


def read_names(path, what):
    """读清单文件 → (有序裸名列表, 行计数)。"""
    if not os.path.isfile(path):
        raise MissingPath("%s 文件缺失: %s" % (what, path))
    names = []
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            n = normalize_line(line)
            if n is not None:
                names.append(n)
    return names


class AuditError(Exception):
    pass


class MissingPath(Exception):
    pass


def audit(order_names, batches):
    """四判审计。order_names=全表有序裸名；batches=[(路径, 有序裸名列表)…]。
    返回 findings 列表（每项 dict(code/name/detail)）。"""
    findings = []
    # 判④ 树表自身同名多行（全表 grep 方能现形）
    seen_order = {}
    for n in order_names:
        seen_order[n] = seen_order.get(n, 0) + 1
    for n in sorted(seen_order):
        if seen_order[n] > 1:
            findings.append({"code": "DUP-ORDER", "name": n,
                             "detail": "order.txt 全表 %d 行同名（注册表重复）" % seen_order[n]})
    order_set = set(order_names)
    # 判① 批内重复（nw6 凭记忆负例）＋ 判② 跨批撞名（enbig7 判例）
    global_seen = {}  # name -> [batch_idx...]
    for bi, (bpath, names) in enumerate(batches, 1):
        seen = {}
        for n in names:
            seen[n] = seen.get(n, 0) + 1
        for n in sorted(seen):
            if seen[n] > 1:
                findings.append({"code": "DUP-BATCH", "name": n,
                                 "detail": "批 %d（%s）内 %d 次重复" % (bi, os.path.basename(bpath), seen[n])})
            global_seen.setdefault(n, []).append(bi)
    for n in sorted(global_seen):
        if len(global_seen[n]) > 1:
            findings.append({"code": "DUP-CROSS", "name": n,
                             "detail": "同件双认领：批 %s（同域双席撞名前兆·enbig7 判例）"
                                       % "、".join(str(b) for b in global_seen[n])})
    # 判③ 选了树里没有的件（全表实读·禁凭记忆）
    for n in sorted(set(k for _, names in batches for k in names)):
        if n not in order_set:
            findings.append({"code": "NOT-IN-ORDER", "name": n,
                             "detail": "不在树 order.txt 全表（实读全表 grep 未命中）"})
    return findings


def grep_rows(order_lines, name):
    """单名全表 grep（勘定员实读替身）——返回命中的原始行列表。全词比对。"""
    hits = []
    pat = re.compile(r"(^|[^A-Za-z0-9_])" + re.escape(name) + r"\.v(\s|$|#)")
    for line in order_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if pat.search(stripped):
            hits.append(stripped.rstrip("\n"))
    return hits


def selftest():
    """内嵌向量组（临时文件驱动）：clean／批内重（nw6）／跨批撞（enbig7）／
    不在树／树表自重／grep 双判／名归一三形／用法与缺件。"""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_selectaudit_self_")
    try:
        order = os.path.join(tmp, "order.txt")
        with io.open(order, "w", encoding="utf-8") as fh:
            fh.write("S01_BaseRing.v#R0-d66910\n"
                     "S02_CauchyComplete.v#R0-d66910\n"
                     "S03_QExp.v#R0-d66910\n"
                     "HansonLcm.v#R0-d66910\n"
                     "zzm1_gauss.v\n"
                     "Local/LW0LeibSeparation.v#R160-eb42d3\n")

        # ① clean：名归一三形会师（#代签/裸名/.v 后缀·含 / 路径形）→ rc 0 CLEAN

        def run(args):
            return subprocess_run([sys.executable, "-B",
                                   os.path.join(os.path.dirname(os.path.abspath(__file__)), PROG + ".py")] + args)

        b1 = os.path.join(tmp, "b1.txt")
        with io.open(b1, "w", encoding="utf-8") as fh:
            fh.write("# 候批\nS03_QExp.v#R2-abc\nzzm1_gauss.v\nLocal/LW0LeibSeparation.v\n")
        # ① clean：名归一三形会师（#代签/裸名/.v 后缀·含 / 路径形）→ rc 0 CLEAN
        p = run(["--order", order, "--select", b1])
        assert p.returncode == 0, "clean 应 rc=0 实测 %d\n%s" % (p.returncode, p.stdout)
        assert "AUDIT-CLEAN" in p.stdout, p.stdout

        # ② 批内重复负判（nw6）→ rc 1·DUP-BATCH
        dupb = os.path.join(tmp, "dupb.txt")
        with io.open(dupb, "w", encoding="utf-8") as fh:
            fh.write("HansonLcm.v\nHansonLcm\n")
        p = run(["--order", order, "--select", dupb])
        assert p.returncode == 1 and "DUP-BATCH" in p.stdout, p.stdout

        # ③ 跨批撞名负判（enbig7）→ rc 1·DUP-CROSS
        b2 = os.path.join(tmp, "b2.txt")
        with io.open(b2, "w", encoding="utf-8") as fh:
            fh.write("zzm1_gauss\nHansonLcm.v\n")
        p = run(["--order", order, "--select", b1, "--select", b2])
        assert p.returncode == 1 and "DUP-CROSS" in p.stdout, p.stdout
        assert "zzm1_gauss" in p.stdout, p.stdout

        # ④ 不在树负判 → rc 1·NOT-IN-ORDER
        ghost = os.path.join(tmp, "ghost.txt")
        with io.open(ghost, "w", encoding="utf-8") as fh:
            fh.write("From_Memory_Only.v\n")
        p = run(["--order", order, "--select", ghost])
        assert p.returncode == 1 and "NOT-IN-ORDER" in p.stdout, p.stdout

        # ⑤ 树表自重负判 → rc 1·DUP-ORDER
        order_dup = os.path.join(tmp, "order_dup.txt")
        with io.open(order_dup, "w", encoding="utf-8") as fh:
            fh.write("A_Mod.v\nB_Mod.v\nA_Mod.v#R1-ffff\n")
        bd = os.path.join(tmp, "bd.txt")
        with io.open(bd, "w", encoding="utf-8") as fh:
            fh.write("B_Mod\n")
        p = run(["--order", order_dup, "--select", bd])
        assert p.returncode == 1 and "DUP-ORDER" in p.stdout and "A_Mod" in p.stdout, p.stdout

        # ⑥ --grep 双判：命中 rc 0 逐行出；未命中 rc 1；全词不误咬
        p = run(["--order", order, "--grep", "HansonLcm"])
        assert p.returncode == 0 and "HansonLcm.v#R0-d66910" in p.stdout, p.stdout
        p = run(["--order", order, "--grep", "No_Such_Mod"])
        assert p.returncode == 1, "grep 未命中应 rc=1 实测 %d" % p.returncode
        # 前缀不误咬：grep S01_BaseRing 恰 1 行命中·不得咬出 S03 行
        p = run(["--order", order, "--grep", "S01_BaseRing"])
        hit_lines = [l for l in p.stdout.splitlines() if l.startswith("ORDER-HIT")]
        assert p.returncode == 0 and len(hit_lines) == 1 \
            and "S03" not in p.stdout, p.stdout

        # ⑦ 用法/缺件：缺 --select 且无 --grep → rc 2；order 缺失 → rc 9
        p = run(["--order", order])
        assert p.returncode == 2, "缺 select 应 rc=2 实测 %d" % p.returncode
        p = run(["--order", os.path.join(tmp, "nope.txt"), "--select", b1])
        assert p.returncode == 9, "order 缺失应 rc=9 实测 %d" % p.returncode

        # ⑧ 前缀不误咬（审计本体）：选 UpReqBanach 不误认 UpReqBanachExp 在树
        order_pfx = os.path.join(tmp, "order_pfx.txt")
        with io.open(order_pfx, "w", encoding="utf-8") as fh:
            fh.write("UpReqBanachExp.v\n")
        bp = os.path.join(tmp, "bp.txt")
        with io.open(bp, "w", encoding="utf-8") as fh:
            fh.write("UpReqBanach\n")
        p = run(["--order", order_pfx, "--select", bp])
        assert p.returncode == 1 and "NOT-IN-ORDER" in p.stdout \
            and "UpReqBanachExp" not in p.stdout, p.stdout

        print("SELECT-AUDIT-SELFTEST PASS: clean/批内重nw6/跨批撞enbig7/不在树/"
              "树表自重/grep双判/全词不误咬/用法2/缺件9 九判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def subprocess_run(argv):
    import subprocess
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="选件审计器：批选清单对树 order.txt 全表 grep 剔重")
    ap.add_argument("--order", required=True, help="认证树 order.txt 全表（只读）")
    ap.add_argument("--select", action="append", default=[], metavar="批选清单",
                    help="候选批选文件（可重复＝多批·跨批撞名判据面）")
    ap.add_argument("--grep", default=None, help="单名全表 grep（勘定员实读替身）")
    ap.add_argument("--json", default=None, help="审计账 JSON 出账路径")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        if args.grep:
            if not os.path.isfile(args.order):
                print("FAIL-LOUD: --order 文件缺失: %s" % args.order, file=sys.stderr)
                sys.exit(9)
            with io.open(args.order, encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
            try:
                name = normalize_line(args.grep)
            except AuditError as e:
                print("FAIL-LOUD: %s" % e, file=sys.stderr)
                sys.exit(2)
            hits = grep_rows(lines, name)
            print("GREP %s 全表命中 %d 行:" % (name, len(hits)))
            for h in hits:
                print("ORDER-HIT %s" % h)
            sys.exit(0 if hits else 1)

        if not args.select:
            print("FAIL-LOUD: --select 与 --grep 必给其一（无单不审）", file=sys.stderr)
            sys.exit(2)
        order_names = read_names(args.order, "--order")
        batches = [(p, read_names(p, "--select")) for p in args.select]
    except MissingPath as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    except AuditError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    print("SELECT-AUDIT order=%s order_rows=%d order_names=%d batches=%d selected=%d"
          % (args.order, len(order_names), len(set(order_names)), len(batches),
             sum(len(n) for _, n in batches)))
    findings = audit(order_names, batches)
    for f in findings:
        print("FINDING %-12s %s — %s" % (f["code"], f["name"], f["detail"]))
    if findings:
        print("AUDIT-RED: %d 发现（exit 1·剔重后重报）" % len(findings))
        verdict = "RED"
    else:
        print("AUDIT-CLEAN: 四判零发现（全表实读·批内无重·跨批无撞·选件皆在树）")
        verdict = "CLEAN"

    if args.json:
        acc = {"order": args.order,
               "order_rows": len(order_names), "order_names": len(set(order_names)),
               "batches": [{"path": p, "count": len(n), "names": n} for p, n in batches],
               "findings": findings, "verdict": verdict}
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)

    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
