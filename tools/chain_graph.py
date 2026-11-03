#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chain_graph.py — 多份 probe 台账合并→链根图→TOP 榜（rocqwash tools/·v30 实战
判例工具化·承 seat_wash25/w25_merge_ledgers.py 1:1 泛化·20261103 入账）

输入 N 份 probe 台账 JSON（argv 序＝合并序；probe_engine 的
rocqwash-probe-ledger/1「records」壳与 W13 式裸 {件名: 记录} 双形通吃）：
  1 合并：并集；重复键保留后批记录（后批覆盖前批·战役口径），batches 字段
    累积全历史标签（标签＝文件名去 .json·重名自动缀序号）。
  2 缺库提取：记录已有 missing 字段（probe_engine 产出）直用；否则对 red 原文
    跑缺库 regex `(?:Unable to locate library|Cannot find library)`。
  3 链根图：rc1 件按所缺库分组 → lib → dependents/n/batches；每根附**自身
    可洗性字段** self——根件自身在合并账中的 rc/verdict：
      washable=true（rc=0）＝洗此根即解锁全部 dependents（链根正典）；
      washable=false（rc!=0）＝根件自身亦被阻（链中环·先治根的因）；
      probed=false＝根件未在候选集（UNPROBED·候补探）。
  4 TOP 榜：dependents 数降序（同数按库名典序）出 markdown＋json。

输出全部确定性（sorted 迭代＋sort_keys 落盘）：同输入重跑字节级恒同。

用法（全部路径参数化·零硬编码·零网络）：
  python3 tools/chain_graph.py LEDGER1.json LEDGER2.json [...] \
      [--json chain_graph.json] [--md chain_top.md] [--top 25]
  python3 tools/chain_graph.py --selftest

退出码：0=出账完成（rc1 计数是数据非器红·响亮入 stdout）；2=用法错；9=任一
输入台账缺失。图 schema=rocqwash-chain-graph/1。
"""
import argparse
import io
import json
import os
import re
import sys

PROG = "chain_graph"
SCHEMA = "rocqwash-chain-graph/1"

MISSING_LIB_RE = re.compile(r"(?:unable to locate library|cannot find library)"
                            r"\s+\|?\s*([A-Za-z0-9_']+)", re.IGNORECASE)


def load_ledger(path):
    """probe 台账 → {件名: 记录}（probe_engine 壳与 W13 裸 dict 双形通吃）。"""
    with io.open(path, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    if isinstance(d, dict) and isinstance(d.get("records"), dict):
        return d["records"]
    if isinstance(d, dict):
        return d
    raise ValueError("台账形态不识别（既非 records 壳亦非裸 dict）: %s" % path)


def merge_ledgers(paths):
    """并集合并（后批覆盖）→ (merged, labels)。batches 累积全历史。"""
    merged = {}
    used_labels = {}
    labels = []
    for idx, path in enumerate(paths, start=1):
        stem = os.path.basename(path)
        if stem.endswith(".json"):
            stem = stem[:-len(".json")]
        label = stem
        if label in used_labels:
            used_labels[label] += 1
            label = "%s%d" % (label, used_labels[label])
        else:
            used_labels[label] = 1
        labels.append(label)
        recs = load_ledger(path)
        for k, v in recs.items():
            rec = dict(v)
            rec["batches"] = (merged[k].get("batches") if k in merged else []) + [label]
            merged[k] = rec
    return merged, labels


def missing_of(rec):
    """记录所缺库：missing 字段直用；否则 red 原文 regex。非缺库返回 None。"""
    m = rec.get("missing")
    if m:
        return m
    red = rec.get("red") or ""
    mm = MISSING_LIB_RE.search(red)
    return mm.group(1) if mm else None


def build_graph(merged):
    """链根图：rc1 缺库分组＋根件自身可洗性。→ (libs, stats, rc1_missing)。"""
    libs = {}
    rc1_missing_set = set()
    for name in sorted(merged):
        rec = merged[name]
        if rec.get("rc") != 1:
            continue
        lib = missing_of(rec)
        if not lib:
            continue
        rc1_missing_set.add(name)
        e = libs.setdefault(lib, {"dependents": [], "batches": set()})
        e["dependents"].append(name)
        e["batches"].update(rec.get("batches") or [])
    libs_out = {}
    for lib, e in libs.items():
        self_rec = merged.get(lib)
        s = {"probed": self_rec is not None,
             "rc": self_rec.get("rc") if self_rec else None,
             "verdict": self_rec.get("verdict") if self_rec else None,
             "washable": bool(self_rec) and self_rec.get("rc") == 0}
        libs_out[lib] = {"dependents": sorted(e["dependents"]),
                         "n": len(e["dependents"]),
                         "batches": sorted(e["batches"]),
                         "self": s}
    libs_out = dict(sorted(libs_out.items(),
                           key=lambda kv: (-kv[1]["n"], kv[0])))
    stats = {"merged_total": len(merged),
             "rc0": sorted(k for k, v in merged.items() if v.get("rc") == 0),
             "rc1": sorted(k for k, v in merged.items() if v.get("rc") == 1),
             "other": sorted(k for k, v in merged.items()
                             if v.get("rc") not in (0, 1))}
    return libs_out, stats, sorted(rc1_missing_set)


def top_md(libs, stats, rc1_missing, top_n, paths):
    """TOP 榜 markdown（确定性·dependents 降序）。"""
    lines = ["# Chain Graph TOP（链根图·%d 份台账并集）" % len(paths), ""]
    lines.append("- merged_total=%d rc0=%d rc1=%d other=%d"
                 % (stats["merged_total"], len(stats["rc0"]),
                    len(stats["rc1"]), len(stats["other"])))
    lines.append("- rc1 缺库型=%d 非缺库（代差型等）=%d"
                 % (len(rc1_missing), len(stats["rc1"]) - len(rc1_missing)))
    lines.append("- 缺库根（distinct libs）=%d" % len(libs))
    lines.append("")
    lines.append("| # | n | lib | self | batches | dependents |")
    lines.append("|---|---|-----|------|---------|------------|")
    for i, (lib, e) in enumerate(list(libs.items())[:top_n], start=1):
        s = e["self"]
        self_txt = ("probed rc=%s verdict=%s washable=%s"
                    % (s["rc"], s["verdict"], str(s["washable"]).lower())
                    if s["probed"] else "UNPROBED")
        deps = ",".join(e["dependents"])
        if len(deps) > 120:
            deps = deps[:117] + "..."
        lines.append("| %d | %d | %s | %s | %s | %s |"
                     % (i, e["n"], lib, self_txt,
                        ",".join(e["batches"]), deps))
    lines.append("")
    return "\n".join(lines)


def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def selftest():
    """内嵌冻结向量组（临时合成双账·零触真仓零网络）：并集覆盖＋batches 累积＋
    缺库分组＋自身可洗性三分＋TOP 榜确定性＋CLI 四码。"""
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

    tmp = tempfile.mkdtemp(prefix="rocqwash_chain_self_")
    try:
        # 账 A：LibX rc0（链根可洗）＋两缺库消费者；LibY 自身 rc1（链中环）
        la = {"LibX": {"file": "LibX", "rc": 0, "red": ""},
              "B1": {"file": "B1", "rc": 1,
                     "red": "Error: Unable to locate library | LibX"},
              "B2": {"file": "B2", "rc": 1,
                     "red": "Error: Cannot find library | LibX"},
              "C1": {"file": "C1", "rc": 1,
                     "red": "Error: Unable to locate library | LibY"},
              "LibY": {"file": "LibY", "rc": 1, "red": "Error: Illegal application"}}
        fa = os.path.join(tmp, "ledgerA.json")
        json.dump(la, io.open(fa, "w", encoding="utf-8"))
        # 账 B：B2 后批洗绿（覆盖）；D1 新增 LibX 消费者
        lb = {"B2": {"file": "B2", "rc": 0, "red": ""},
              "D1": {"file": "D1", "rc": 1,
                     "red": "Error: Unable to locate library | LibX"}}
        fb = os.path.join(tmp, "ledgerB.json")
        json.dump(lb, io.open(fb, "w", encoding="utf-8"))
        jf = os.path.join(tmp, "graph.json")
        mf = os.path.join(tmp, "top.md")
        p = run([fa, fb, "--json", jf, "--md", mf])
        assert p.returncode == 0, p.stdout
        g = json.load(io.open(jf, encoding="utf-8"))
        assert g["schema"] == SCHEMA and g["stats"]["merged_total"] == 6, g["stats"]
        # 后批覆盖：B2 以账 B rc0 记录为准且 batches 累积 [ledgerA, ledgerB]
        b2 = g["records"]["B2"]
        assert b2["rc"] == 0 and b2["batches"] == ["ledgerA", "ledgerB"], b2
        # 链根：LibX dependents=B1,D1（B2 后批已绿出局）·self washable
        lx = g["libs"]["LibX"]
        assert lx["n"] == 2 and lx["dependents"] == ["B1", "D1"], lx
        assert lx["self"]["probed"] and lx["self"]["washable"] is True, lx
        # 链中环：LibY 自身 rc1 → washable=false
        ly = g["libs"]["LibY"]
        assert ly["n"] == 1 and ly["self"]["washable"] is False, ly
        # TOP 榜确定性：重跑字节恒同
        before_j = io.open(jf, "rb").read()
        before_m = io.open(mf, "rb").read()
        p = run([fa, fb, "--json", jf, "--md", mf])
        assert p.returncode == 0, p.stdout
        assert io.open(jf, "rb").read() == before_j, "json 字节漂移＝违例"
        assert io.open(mf, "rb").read() == before_m, "md 字节漂移＝违例"
        assert "LibX" in before_m.decode("utf-8"), "TOP 榜缺链根"
        # CLI 四码
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "缺台账应 rc=2 实测 %d" % p.returncode
        p = run([os.path.join(tmp, "nope.json")])
        assert p.returncode == 9, "缺台账应 rc=9 实测 %d" % p.returncode
        print("CHAIN-GRAPH-SELFTEST PASS: 并集覆盖/batches 累积/链根分组/"
              "自身可洗性三分/确定性字节恒同/CLI 四码 六判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="多份 probe 台账合并→链根图（missing-lib→"
                               "dependents→自身可洗性）→TOP 榜 markdown+json")
    ap.add_argument("ledgers", nargs="*", metavar="LEDGER.json",
                    help="probe 台账（argv 序＝合并序·后批覆盖前批）")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="链根图原始数据出账")
    ap.add_argument("--md", default=None, metavar="out.md",
                    help="TOP 榜 markdown 出账")
    ap.add_argument("--top", type=int, default=25, metavar="N",
                    help="TOP 榜行数（默认 25）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not args.ledgers:
        print("FAIL-LOUD: 至少一份 probe 台账必给（--selftest 除外）",
              file=sys.stderr)
        sys.exit(2)
    for pth in args.ledgers:
        if not os.path.exists(pth):
            print("FAIL-LOUD: 台账缺失: %s" % pth, file=sys.stderr)
            sys.exit(9)

    merged, labels = merge_ledgers(args.ledgers)
    libs, stats, rc1_missing = build_graph(merged)

    print("=== CHAIN-GRAPH MERGE ===")
    print("ledgers: %s" % ", ".join("%s=%s" % (l, p) for l, p
                                    in zip(labels, args.ledgers)))
    print("union total: %d rc0: %d rc1: %d other: %d"
          % (stats["merged_total"], len(stats["rc0"]), len(stats["rc1"]),
             len(stats["other"])))
    print("rc1 missing-lib: %d  rc1 non-missing(代差型等): %d"
          % (len(rc1_missing), len(stats["rc1"]) - len(rc1_missing)))
    print("distinct missing libs: %d" % len(libs))
    print("--- TOP libs by dependents ---")
    for lib, e in list(libs.items())[:args.top]:
        s = e["self"]
        self_txt = ("rc=%s washable=%s" % (s["rc"], s["washable"])
                    if s["probed"] else "UNPROBED")
        print("%3d  %-38s [%s] %s"
              % (e["n"], lib, self_txt, ",".join(e["dependents"])[:150]))

    acc = {"schema": SCHEMA, "ledgers": args.ledgers, "labels": labels,
           "stats": {"merged_total": stats["merged_total"],
                     "rc0": stats["rc0"], "rc1": stats["rc1"],
                     "other": stats["other"]},
           "rc1_missing_files": rc1_missing,
           "rc1_nonmissing_files": [k for k in stats["rc1"]
                                    if k not in set(rc1_missing)],
           # libs 在 json 落盘按典序（sort_keys）；rank 序＝top_order 显式保存
           "top_order": list(libs.keys()),
           "libs": libs, "records": merged}
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, indent=1, ensure_ascii=False, sort_keys=True)
        print("json ->", args.json)
    if args.md:
        with io.open(args.md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(top_md(libs, stats, rc1_missing, args.top, args.ledgers))
        print("md ->", args.md)
    sys.exit(0)


if __name__ == "__main__":
    main()
