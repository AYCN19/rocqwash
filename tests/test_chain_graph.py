#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_chain_graph.py — tools/chain_graph.py 自测（tests/·v30 实战判例工具化·
承 W25 w25_merge_ledgers.py 工具化轮·20261103）

多账合并链根图七节判：
  1 工具自证    --selftest 六判全过（rc 0）
  2 双形通吃    probe_engine「records」壳台账＋W13 式裸 {件名:记录} 台账混并
  3 合并语义    并集/后批覆盖/batches 累积全历史/标签重名缀序号
  4 链根三分    根件 washable=true（rc0）／false（rc1 链中环）／UNPROBED（不在
                候选集）三形态逐字段咬合
  5 missing 双源 probe_engine missing 字段直用／red 原文 regex fallback（双 regex 形：
                Unable to locate＋Cannot find library·含「 | 」续行拼接形）
  6 TOP 榜      md 表头/排序（n 降序·同数典序）/--top 截断/json stats 咬合＋
                重跑字节级恒同（确定性）
  7 CLI 四码    --help 0／未知形参 2／缺台账 2／台账缺失 9

零触律：全部夹具临时合成（双账即写即清）·零真编译零网络零触真仓。
幂等：python3 -B 禁 __pycache__。退出码：0=七节全过；1=任一红。
"""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "chain_graph.py")

_spec = importlib.util.spec_from_file_location("chain_graph_mod", TOOL)
cg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cg)


def run(args):
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def dump(path, obj):
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)
    return path


def rec(name, rc, red="", missing=None):
    r = {"file": name, "rc": rc, "red": red}
    if missing is not None:
        r["missing"] = missing
    return r


def sec1_selftest():
    rc, out = run(["--selftest"])
    assert rc == 0, "selftest 应 rc=0 实测 %d\n%s" % (rc, out)
    assert "CHAIN-GRAPH-SELFTEST PASS" in out, out
    return "selftest 六判绿"


def sec2_dual_shape_merge(tmp):
    """records 壳（probe_engine 形）×裸 dict（W13 形）混并。"""
    a = dump(os.path.join(tmp, "shapeA.json"),
             {"schema": cg.SCHEMA,
              "records": {"RootLib": rec("RootLib", 0),
                          "Dep1": rec("Dep1", 1,
                                      "Error: Unable to locate library | "
                                      "RootLib (while searching for a .vos "
                                      "file).")}})
    b = dump(os.path.join(tmp, "shapeB.json"),
             {"Dep2": rec("Dep2", 1, "Error: Cannot find library | RootLib")})
    rc, out = run([a, b, "--json", os.path.join(tmp, "g.json")])
    assert rc == 0, out
    g = json.load(io.open(os.path.join(tmp, "g.json"), encoding="utf-8"))
    assert g["stats"]["merged_total"] == 3, g["stats"]
    assert g["libs"]["RootLib"]["n"] == 2, g["libs"]["RootLib"]
    return "双形通吃（records 壳×裸 dict）混并 3 件"


def sec3_merge_semantics(tmp):
    a = dump(os.path.join(tmp, "m1.json"),
             {"Same": rec("Same", 1, "Error: Unable to locate library | Lz"),
              "Keep": rec("Keep", 0)})
    b = dump(os.path.join(tmp, "m1b.json"),
             {"Same": rec("Same", 0)})  # 后批洗绿覆盖
    rc, out = run([a, b, "--json", os.path.join(tmp, "g3.json")])
    assert rc == 0, out
    g = json.load(io.open(os.path.join(tmp, "g3.json"), encoding="utf-8"))
    s = g["records"]["Same"]
    assert s["rc"] == 0, "后批应覆盖·实测 rc=%r" % s["rc"]
    assert s["batches"] == ["m1", "m1b"], "标签累积·实测 %r" % s["batches"]
    assert "Lz" not in g["libs"], "后批洗绿应出局链根（唯一消费者已绿）"
    return "后批覆盖＋batches 累积＋标签取文件名去 .json"


def sec4_self_washability(tmp):
    """链根三分：washable true/false/UNPROBED。"""
    a = dump(os.path.join(tmp, "w1.json"),
             {"WashRoot": rec("WashRoot", 0),
              "d1": rec("d1", 1, "Error: Unable to locate library | WashRoot"),
              "ChainedRoot": rec("ChainedRoot", 1,
                                 "Error: Illegal application "
                                 "(Non-functional construction)"),
              "d2": rec("d2", 1, "Error: Unable to locate library | ChainedRoot"),
              "d3": rec("d3", 1, "Error: Unable to locate library | NeverProbedLib")})
    rc, out = run([a, "--json", os.path.join(tmp, "g4.json")])
    assert rc == 0, out
    g = json.load(io.open(os.path.join(tmp, "g4.json"), encoding="utf-8"))
    wr = g["libs"]["WashRoot"]["self"]
    assert wr["probed"] and wr["rc"] == 0 and wr["washable"] is True, wr
    cr = g["libs"]["ChainedRoot"]["self"]
    assert cr["probed"] and cr["rc"] == 1 and cr["washable"] is False, cr
    up = g["libs"]["NeverProbedLib"]["self"]
    assert up["probed"] is False and up["washable"] is False, up
    return "链根三分 washable true/false/UNPROBED 逐字段咬合"


def sec5_missing_dual_source(tmp):
    """missing 字段直用 vs red regex fallback（含「 | 」拼接形与「|」无空格形）。"""
    a = dump(os.path.join(tmp, "d1.json"),
             {"FieldCand": rec("FieldCand", 1, "Error: AnyLib boom",
                               missing="FieldLib"),
              "PipeCand": rec("PipeCand", 1,
                              "Error: Unable to locate library | PipeLib "
                              "(while searching for a .vos file)."),
              "TightCand": rec("TightCand", 1,
                               "Error: Cannot find library TightLib")})
    rc, out = run([a, "--json", os.path.join(tmp, "g5.json")])
    assert rc == 0, out
    g = json.load(io.open(os.path.join(tmp, "g5.json"), encoding="utf-8"))
    assert "FieldLib" in g["libs"] and "AnyLib" not in g["libs"], \
        "missing 字段应优先于 red 词面"
    assert g["libs"]["PipeLib"]["dependents"] == ["PipeCand"], g["libs"]
    assert g["libs"]["TightLib"]["dependents"] == ["TightCand"], g["libs"]
    return "missing 字段直用＋regex 兜底（raw 空格形/「 | 」拼接形双咬合）"


def sec6_top_and_determinism(tmp):
    libs_src = {}
    for i in range(6):
        lib = "Lib%d" % i
        libs_src[lib] = rec(lib, 0)
        for j in range(i + 1):
            libs_src["dep_%d_%d" % (i, j)] = rec(
                "dep_%d_%d" % (i, j), 1,
                "Error: Unable to locate library | %s" % lib)
    a = dump(os.path.join(tmp, "t1.json"), libs_src)
    jf = os.path.join(tmp, "g6.json")
    mf = os.path.join(tmp, "top.md")
    rc, out = run([a, "--json", jf, "--md", mf, "--top", "3"])
    assert rc == 0, out
    g = json.load(io.open(jf, encoding="utf-8"))
    order = g["top_order"]  # rank 序显式字段（libs 字典在 json 按典序）
    ns = [g["libs"][k]["n"] for k in order]
    assert ns == sorted(ns, reverse=True), "降序违例 %r" % ns
    assert len(order) == 6 and order[0] == "Lib5", order
    md = io.open(mf, encoding="utf-8").read()
    assert "| 1 | 6 | Lib5 |" in md, md[:400]
    assert "Lib2" not in md, "--top 3 应截断至前三"
    before_j = io.open(jf, "rb").read()
    before_m = io.open(mf, "rb").read()
    rc2, _ = run([a, "--json", jf, "--md", mf, "--top", "3"])
    assert rc2 == 0, out
    assert io.open(jf, "rb").read() == before_j, "json 重跑字节漂移＝违例"
    assert io.open(mf, "rb").read() == before_m, "md 重跑字节漂移＝违例"
    return "TOP 榜排序/截断/表头＋json/md 重跑字节恒同"


def sec7_cli_codes(tmp):
    rc, out = run(["--help"])
    assert rc == 0 and "usage" in out, out[-200:]
    rc, out = run(["--bogus"])
    assert rc == 2, "未知形参应 rc=2 实测 %d" % rc
    rc, out = run([])
    assert rc == 2, "缺台账应 rc=2 实测 %d" % rc
    rc, out = run([os.path.join(tmp, "nope.json")])
    assert rc == 9, "台账缺失应 rc=9 实测 %d" % rc
    return "CLI 四码（help0/bogus2/缺账2/缺件9）"


def main():
    tmp = tempfile.mkdtemp(prefix="rocqwash_chain_test_")
    try:
        secs = [
            ("1 selftest", sec1_selftest),
            ("2 双形通吃", lambda: sec2_dual_shape_merge(tmp)),
            ("3 合并语义", lambda: sec3_merge_semantics(tmp)),
            ("4 链根三分", lambda: sec4_self_washability(tmp)),
            ("5 missing 双源", lambda: sec5_missing_dual_source(tmp)),
            ("6 TOP＋确定性", lambda: sec6_top_and_determinism(tmp)),
            ("7 CLI 四码", lambda: sec7_cli_codes(tmp)),
        ]
        n = 0
        for name, fn in secs:
            note = fn()
            n += 1
            print("  [%d/7] %-14s OK — %s" % (n, name, note))
        print("TEST-CHAIN-GRAPH PASS: 7/7 节全过")
        return 0
    except AssertionError as e:
        print("TEST-CHAIN-GRAPH FAIL: %s" % e)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
