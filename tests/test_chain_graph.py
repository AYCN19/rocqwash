#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_chain_graph.py — self-test for tools/chain_graph.py (tests/).

    Purpose.  Checks the multi-ledger merge chain-root graph tool in seven
      sections: selftest; dual-shape merge (`records` shell × bare dict);
      merge semantics (union, later-batch override, `batches` history, label
      = file name minus .json); chain-root three-way `washable` verdict
      (true/false/UNPROBED); missing-source duality (`missing` field direct,
      regex fallback over `red`); top-list ordering, `--top` truncation and
      byte-identical reruns; CLI exit codes.

    Interface.  python3 tests/test_chain_graph.py (no arguments); drives
      `tools/chain_graph.py` via subprocess with `--selftest`, `--json`,
      `--md`, `--top`, and positional ledger paths; prints `[n/7] <name>
      OK — <note>` per section and the `TEST-CHAIN-GRAPH PASS` token.

    Dependencies.  Python 3 standard library only (importlib.util, io, json,
      os, shutil, subprocess, sys, tempfile); `tools/chain_graph.py` resolved
      relative to this file's parent directory; runs under `python3 -B` (no
      __pycache__); fixtures synthesized under tempfile.mkdtemp, removed in
      finally; zero real compilation, zero network, zero repository writes.

    Evidence.  Registered as lane `t_chain_graph` in tests/run_tests.sh;
      asserts the `rocqwash-chain-graph/1` fields (`merged_total`,
      `top_order`, `libs`, `records`) and byte-identical rerun output.

    Exit-codes.  0 = all seven sections pass; 1 = any section failing
      (AssertionError caught, message printed, fail-loud).
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
    assert rc == 0, "selftest should exit rc=0, got %d\n%s" % (rc, out)
    assert "CHAIN-GRAPH-SELFTEST PASS" in out, out
    return "selftest six checks pass"


def sec2_dual_shape_merge(tmp):
    """`records` shell (`probe_engine` shape) × bare dict, merged."""
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
    return "dual-shape merge (records shell × bare dict) merged 3 records"


def sec3_merge_semantics(tmp):
    a = dump(os.path.join(tmp, "m1.json"),
             {"Same": rec("Same", 1, "Error: Unable to locate library | Lz"),
              "Keep": rec("Keep", 0)})
    b = dump(os.path.join(tmp, "m1b.json"),
             {"Same": rec("Same", 0)})  # the later batch overrides with a clean record
    rc, out = run([a, b, "--json", os.path.join(tmp, "g3.json")])
    assert rc == 0, out
    g = json.load(io.open(os.path.join(tmp, "g3.json"), encoding="utf-8"))
    s = g["records"]["Same"]
    assert s["rc"] == 0, "the later batch should override, got rc=%r" % s["rc"]
    assert s["batches"] == ["m1", "m1b"], "labels should accumulate, got %r" % s["batches"]
    assert "Lz" not in g["libs"], "a record cleaned back to passing must leave the chain roots (its only consumer is passing)"
    return "later batch overrides + batches accumulate + label is file name minus .json"


def sec4_self_washability(tmp):
    """chain-root three-way split: `washable` true/false/UNPROBED."""
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
    return "chain-root washable true/false/UNPROBED checked field by field"


def sec5_missing_dual_source(tmp):
    """the `missing` field used directly vs regex fallback over the raw `red`
    text (the ' | ' joined form and the tight '|' form)."""
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
        "the `missing` field should take precedence over the `red` text"
    assert g["libs"]["PipeLib"]["dependents"] == ["PipeCand"], g["libs"]
    assert g["libs"]["TightLib"]["dependents"] == ["TightCand"], g["libs"]
    return "missing field used directly + regex fallback (raw space form and ' | ' joined form both covered)"


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
    order = g["top_order"]  # explicit rank-order field (the libs dict serializes in dict order)
    ns = [g["libs"][k]["n"] for k in order]
    assert ns == sorted(ns, reverse=True), "descending order violated %r" % ns
    assert len(order) == 6 and order[0] == "Lib5", order
    md = io.open(mf, encoding="utf-8").read()
    assert "| 1 | 6 | Lib5 |" in md, md[:400]
    assert "Lib2" not in md, "--top 3 should truncate to the first three"
    before_j = io.open(jf, "rb").read()
    before_m = io.open(mf, "rb").read()
    rc2, _ = run([a, "--json", jf, "--md", mf, "--top", "3"])
    assert rc2 == 0, out
    assert io.open(jf, "rb").read() == before_j, "json output drifted across reruns"
    assert io.open(mf, "rb").read() == before_m, "md output drifted across reruns"
    return "top-list ordering/truncation/header + byte-identical json/md reruns"


def sec7_cli_codes(tmp):
    rc, out = run(["--help"])
    assert rc == 0 and "usage" in out, out[-200:]
    rc, out = run(["--bogus"])
    assert rc == 2, "unknown flag should exit rc=2, got %d" % rc
    rc, out = run([])
    assert rc == 2, "missing ledger argument should exit rc=2, got %d" % rc
    rc, out = run([os.path.join(tmp, "nope.json")])
    assert rc == 9, "nonexistent ledger file should exit rc=9, got %d" % rc
    return "CLI four codes (help 0/bogus 2/no-ledger 2/missing-file 9)"


def main():
    tmp = tempfile.mkdtemp(prefix="rocqwash_chain_test_")
    try:
        secs = [
            ("1 selftest", sec1_selftest),
            ("2 dual-shape", lambda: sec2_dual_shape_merge(tmp)),
            ("3 merge semantics", lambda: sec3_merge_semantics(tmp)),
            ("4 chain-root", lambda: sec4_self_washability(tmp)),
            ("5 missing dual", lambda: sec5_missing_dual_source(tmp)),
            ("6 top+determinism", lambda: sec6_top_and_determinism(tmp)),
            ("7 CLI four codes", lambda: sec7_cli_codes(tmp)),
        ]
        n = 0
        for name, fn in secs:
            note = fn()
            n += 1
            print("  [%d/7] %-14s OK — %s" % (n, name, note))
        print("TEST-CHAIN-GRAPH PASS: 7/7 sections pass")
        return 0
    except AssertionError as e:
        print("TEST-CHAIN-GRAPH FAIL: %s" % e)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
