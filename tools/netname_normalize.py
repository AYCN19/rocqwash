#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""netname_normalize.py — .v.v 双后缀名净名归一器（rocqwash tools/·本轮实战判例
工具化①·20261101 入账）

世界内 .v 文件误存成双后缀 `.v.v`（编辑器追加/脚本拼接之典型病）即令 Require 面
按净名找不到件——依赖网假性缺口。本器把「净名归一」机械化：

  输入目录 → os.walk 全索引收 `*.v.v` → 产出净名映射表
      <净名>.v.v  →  <净名>.v
  （剥一个 `.v.v` 后缀即净名·目标名＝净名＋`.v`。`X.v.v.v` 形剥一层得
  `X.v.v`——一层一归一，重跑再剥·如实出账不静默迭代。）

两态制（--dry-run 默认）：
  - **dry run（默认）**：只出映射表与发现，零字节落盘（唯一写面＝显式 --map/--json
    出账路径）；
  - **--apply**：逐件 os.rename 落盘改名，**改名前后 md5 一致性校验**（改名不改
    字节·冻结律机械化）——前后 md5 不等即 MD5-MISMATCH failing。

判据（发现即红·exit 1）：
  PENDING      干跑面发现待归一 `.v.v` 件（世界净名面未闭）
  COLLIDE      目标名 `<净名>.v` 已在盘——拒改名不覆写（对侧件内容保全·人工裁断）
  DEGENERATE   剥后净名为空（文件名恰为 `.v.v`）——畸形不出名·跳过
  MD5-MISMATCH 改名前后 md5 不等（正常经 os.rename 不可达·达即环境异常 fail-loud）

用法（CLI 形制参照 tools/select_audit.py）：
  python3 tools/netname_normalize.py --dir <世界目录> [--map out.tsv] [--json out.json]
  python3 tools/netname_normalize.py --dir <世界目录> --apply   # 落盘改名
  python3 tools/netname_normalize.py --selftest

退出码：0=CLEAN（无 `.v.v`）或 APPLY 后全量归一且 md5 验讫；1=RED（PENDING/
COLLIDE/MD5-MISMATCH 任一）；2=用法错（--help rc=0／未知形参 rc=2 承 argparse）；
9=--dir 路径缺失（fail-loud 不模拟）。

写隔离：干跑零写盘；--apply 写面恰为逐件改名（不新建不覆写）；唯一另两写面＝
显式 --map/--json 出账路径。临时目录夹具自证·零触真仓。
"""
import argparse
import hashlib
import io
import json
import os
import sys

PROG = "netname_normalize"
DOUBLE_SUFFIX = ".v.v"


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_entry(rel):
    """相对路径（/ normalize）→ (netname, src_rel, dst_rel) 或 None（非 .v.v 件）。

    `X.v.v` → netname=X·dst=X.v；`sub/X.v.v` → netname=sub/X·dst=sub/X.v。
    """
    rel = rel.replace(os.sep, "/")
    if not rel.endswith(DOUBLE_SUFFIX):
        return None
    netname = rel[: -len(DOUBLE_SUFFIX)]
    return (netname, rel, netname + ".v")


def scan_world(world_dir):
    """world_dir 全索引 → 有序 [(netname, src_rel, dst_rel)]（os.walk·/ normalize·排序稳定）。"""
    out = []
    for dirpath, _dirs, fnames in os.walk(world_dir):
        for fn in fnames:
            rel = os.path.relpath(os.path.join(dirpath, fn), world_dir)
            e = normalize_entry(rel)
            if e is not None:
                out.append(e)
    out.sort(key=lambda t: t[1])
    return out


def audit(world_dir):
    """净名面审计：扫 `.v.v` → 逐件出 (entry, collide) 台账。

    COLLIDE＝目标名 `<净名>.v` 已在盘（拒改名不覆写）；DEGENERATE＝净名剥空。
    返回 (entries, findings)；entries 为合法可归一件，findings 为 dict 列表。
    """
    entries = []
    findings = []
    for netname, src, dst in scan_world(world_dir):
        if netname == "":
            findings.append({"code": "DEGENERATE", "name": src,
                             "detail": "净名剥空（文件名恰为 .v.v）——跳过不出名"})
            continue
        if os.path.exists(os.path.join(world_dir, dst)):
            findings.append({"code": "COLLIDE", "name": netname,
                             "detail": "目标 %s 已在盘——拒改名不覆写（人工裁断）" % dst})
            continue
        entries.append((netname, src, dst))
    return entries, findings


def apply_renames(world_dir, entries):
    """--apply 落盘：逐件改名＋md5 前后一致性校验。返回 (applied, findings)。"""
    applied = []
    findings = []
    for netname, src, dst in entries:
        sp = os.path.join(world_dir, src)
        dp = os.path.join(world_dir, dst)
        if os.path.exists(dp):  # 改名瞬间对侧件出现（并发写）——仍拒覆写
            findings.append({"code": "COLLIDE", "name": netname,
                             "detail": "改名时目标 %s 已在盘——拒覆写" % dst})
            continue
        before = md5_of(sp)
        os.rename(sp, dp)
        after = md5_of(dp)
        if before != after:
            findings.append({"code": "MD5-MISMATCH", "name": netname,
                             "detail": "%s 改名前后 md5 不等（before=%s after=%s）"
                                       % (dst, before, after)})
            continue
        applied.append((netname, src, dst, before))
    return applied, findings


def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def selftest():
    """内嵌冻结向量组（临时目录驱动）：干跑零落盘双判／apply normalize＋md5 验讫／
    COLLIDE 拒覆写／DEGENERATE／净世界 CLEAN／CLI 四码（--help 0·未知形参 2·
    缺 dir 9）／--map --json 出账。零触真仓。"""
    import shutil
    import tempfile

    def run(args):
        import subprocess
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    tmp = tempfile.mkdtemp(prefix="rocqwash_netname_self_")
    try:
        # ① 干跑默认：映射表出账·零字节落盘（件仍在）→ rc 1 PENDING
        w = os.path.join(tmp, "world")
        os.makedirs(os.path.join(w, "sub"))
        body_a = "Lemma a : True.\nProof. exact I. Qed.\n"
        body_b = "Definition b := 1.\n"
        with io.open(os.path.join(w, "A.v.v"), "w", encoding="utf-8") as fh:
            fh.write(body_a)
        with io.open(os.path.join(w, "sub", "B.v.v"), "w", encoding="utf-8") as fh:
            fh.write(body_b)
        p = run(["--dir", w])
        assert p.returncode == 1 and "PENDING" in p.stdout and "2" in p.stdout, p.stdout
        assert "A.v.v -> A.v" in p.stdout and "sub/B.v.v -> sub/B.v" in p.stdout, p.stdout
        assert os.path.isfile(os.path.join(w, "A.v.v")), "干跑落盘改名＝违例"
        assert not os.path.exists(os.path.join(w, "A.v")), "干跑新建目标＝违例"

        # ② --apply：归一落盘＋md5 验讫 → rc 0·字节前后恒等
        p = run(["--dir", w, "--apply"])
        assert p.returncode == 0 and "APPLY" in p.stdout, p.stdout
        assert "VERIFY-OK" in p.stdout and "md5" in p.stdout, p.stdout
        assert not os.path.exists(os.path.join(w, "A.v.v")), p.stdout
        assert not os.path.exists(os.path.join(w, "sub", "B.v.v")), p.stdout
        with io.open(os.path.join(w, "A.v"), encoding="utf-8") as fh:
            assert fh.read() == body_a, "改名改字节＝违例"
        with io.open(os.path.join(w, "sub", "B.v"), encoding="utf-8") as fh:
            assert fh.read() == body_b, "改名改字节＝违例"

        # ③ COLLIDE 拒覆写：X.v 与 X.v.v 并存 → rc 1·对侧件保全
        w2 = os.path.join(tmp, "world2")
        os.makedirs(w2)
        with io.open(os.path.join(w2, "X.v"), "w", encoding="utf-8") as fh:
            fh.write("ORIGINAL-TARGET\n")
        with io.open(os.path.join(w2, "X.v.v"), "w", encoding="utf-8") as fh:
            fh.write("DOUBLE-SUFFIX\n")
        p = run(["--dir", w2, "--apply"])
        assert p.returncode == 1 and "COLLIDE" in p.stdout, p.stdout
        assert os.path.isfile(os.path.join(w2, "X.v.v")), "撞名件被静默弃置＝违例"
        with io.open(os.path.join(w2, "X.v"), encoding="utf-8") as fh:
            assert fh.read() == "ORIGINAL-TARGET\n", "目标名被覆写＝违例"

        # ④ DEGENERATE：文件名恰为 .v.v → 跳过不出名
        w3 = os.path.join(tmp, "world3")
        os.makedirs(w3)
        with io.open(os.path.join(w3, ".v.v"), "w", encoding="utf-8") as fh:
            fh.write("x\n")
        p = run(["--dir", w3])
        assert p.returncode == 1 and "DEGENERATE" in p.stdout, p.stdout

        # ⑤ 净世界 → rc 0 CLEAN
        p = run(["--dir", tmp])  # tmp 根含 world*/残留·唯 world1 已归一……改用专造净域
        w4 = os.path.join(tmp, "world4")
        os.makedirs(w4)
        with io.open(os.path.join(w4, "Clean.v"), "w", encoding="utf-8") as fh:
            fh.write("Lemma c : True.\nProof. exact I. Qed.\n")
        p = run(["--dir", w4])
        assert p.returncode == 0 and "NORMALIZE-CLEAN" in p.stdout, p.stdout

        # ⑥ CLI 四码：--help 0／未知形参 2／缺 --dir 2／--dir 缺失 9
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "缺 --dir 应 rc=2 实测 %d" % p.returncode
        p = run(["--dir", os.path.join(tmp, "nowhere")])
        assert p.returncode == 9, "缺 dir 应 rc=9 实测 %d" % p.returncode

        # ⑦ --map/--json 出账：映射表 TSV 与审计账 JSON 逐件咬合
        w5 = os.path.join(tmp, "world5")
        os.makedirs(w5)
        with io.open(os.path.join(w5, "M.v.v"), "w", encoding="utf-8") as fh:
            fh.write("Lemma m : True.\nProof. exact I. Qed.\n")
        mapf = os.path.join(tmp, "map.tsv")
        jsonf = os.path.join(tmp, "acc.json")
        p = run(["--dir", w5, "--map", mapf, "--json", jsonf])
        assert p.returncode == 1, p.stdout
        with io.open(mapf, encoding="utf-8") as fh:
            rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
        assert rows == [["M.v.v", "M.v"]], repr(rows)
        with io.open(jsonf, encoding="utf-8") as fh:
            acc = json.load(fh)
        assert acc["dir"] == w5 and acc["verdict"] == "PENDING", repr(acc)
        assert [e["src"] for e in acc["entries"]] == ["M.v.v"], repr(acc)

        # ⑧ X.v.v.v 形：一层一归一（剥一层得 X.v.v·重跑再剥·如实出账）
        w6 = os.path.join(tmp, "world6")
        os.makedirs(w6)
        with io.open(os.path.join(w6, "N.v.v.v"), "w", encoding="utf-8") as fh:
            fh.write("Lemma n : True.\nProof. exact I. Qed.\n")
        p = run(["--dir", w6])
        assert p.returncode == 1 and "N.v.v.v -> N.v.v" in p.stdout, p.stdout

        print("NETNAME-NORMALIZE-SELFTEST PASS: 干跑零落盘/apply归一md5验讫/COLLIDE拒覆写/"
              "DEGENERATE/净世界CLEAN/CLI四码/help0/map+json出账/vvv一层一归一 八判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description=".v.v 双后缀名净名归一器：产出净名映射表"
                               "（<净名>.v.v→<净名>.v）＋--apply 落盘改名（md5 验讫）")
    ap.add_argument("--dir", default=None, help="世界目录（os.walk 全索引·必给）")
    ap.add_argument("--apply", action="store_true",
                    help="落盘改名（缺省干跑只出表零写盘）")
    ap.add_argument("--map", default=None, metavar="out.tsv",
                    help="净名映射表 TSV 出账路径（<src>\\t<dst>）")
    ap.add_argument("--json", default=None, help="审计账 JSON 出账路径")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not args.dir:
        print("FAIL-LOUD: --dir <世界目录> 必给（--selftest 除外）", file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(args.dir):
        print("FAIL-LOUD: --dir 路径缺失: %s" % args.dir, file=sys.stderr)
        sys.exit(9)

    entries, findings = audit(args.dir)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print("NETNAME-NORMALIZE dir=%s mode=%s double_suffix=%d pending=%d findings=%d"
          % (args.dir, mode, len(entries) + sum(1 for f in findings
                                                if f["code"] in ("COLLIDE", "DEGENERATE")),
             len(entries), len(findings)))
    for f in findings:
        print("FINDING %-12s %s — %s" % (f["code"], f["name"], f["detail"]))
    applied = []
    if args.apply:
        applied, af = apply_renames(args.dir, entries)
        findings.extend(af)
        for netname, src, dst, md5 in applied:
            print("RENAME %-40s -> %-40s md5=%s VERIFY-OK" % (src, dst, md5))
    else:
        for netname, src, dst in entries:
            print("MAP %s -> %s" % (src, dst))

    if findings:
        print("NORMALIZE-RED: %d 发现（PENDING 待 --apply／COLLIDE 人工裁断／"
              "MD5-MISMATCH fail-loud）" % len(findings))
        verdict = "RED" if not args.apply else "APPLY-RED"
    elif args.apply:
        print("APPLY-DONE: %d 件归一且 md5 前后验讫（改名不改字节）" % len(applied))
        verdict = "APPLIED"
    elif entries:
        print("NORMALIZE-PENDING: %d 件待归一（干跑零落盘·--apply 落盘）" % len(entries))
        verdict = "PENDING"
    else:
        print("NORMALIZE-CLEAN: 净名面全闭（世界无 .v.v 双后缀件）")
        verdict = "CLEAN"

    if args.map:
        with io.open(args.map, "w", encoding="utf-8", newline="\n") as fh:
            for netname, src, dst in entries:
                fh.write("%s\t%s\n" % (src, dst))
        print("map ->", args.map)
    if args.json:
        acc = {"dir": args.dir, "mode": mode, "verdict": verdict,
               "entries": [{"netname": n, "src": s, "dst": d}
                           for n, s, d in entries],
               "applied": [{"src": s, "dst": d, "md5": m}
                           for n, s, d, m in applied],
               "findings": findings}
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)

    ok = (not findings) and (not (entries and not args.apply))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
