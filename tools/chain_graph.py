#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chain_graph.py — merge probe ledgers into a chain-root graph and a top list (rocqwash tools/).

Purpose.  Merges N probe ledgers (argv order = merge order; the
  `rocqwash-probe-ledger/1` "records" shell from `probe_engine` and the bare
  {name: record} dict form are both accepted) and emits: (1) the union merge
  — later batches override earlier records on duplicate keys, every record
  accumulating its full `batches` label history (label = file name minus
  .json, duplicates suffixed numerically); (2) missing-library extraction —
  the record's `missing` field when present, else the regex
  unable-to-locate/cannot-find over the `red` text; (3) the chain-root graph
  — rc=1 records grouped by missing library, each root carrying a `self`
  block with its own merged-ledger rc/verdict (the three-way contract sits
  on build_graph); (4) the top list — dependents descending, ties by
  library name, markdown plus json.

Interface.  python3 tools/chain_graph.py LEDGER1.json [...] [--json P]
  [--md P] [--top N] | --selftest.  Graph schema rocqwash-chain-graph/1;
  routed as `chain` in the cw.sh table; zero hardcoded paths, zero network;
  output deterministic (sorted iteration plus sort_keys), reruns
  byte-identical.

Dependencies.  Python 3 standard library only; every ledger path parameterized.

Evidence.  --selftest frozen vectors on temporary synthetic ledgers (zero
  real-repo touches, zero network); suite tests/test_chain_graph.py
  (seven sections).

Exit-codes.  0 = graph emitted (the rc1 count is data, not a tool failure,
  reported on stdout); 2 = usage error; 9 = any input ledger missing.
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
    """Probe ledger -> {name: record} (accepts both the `probe_engine`
    records shell and the bare dict form)."""
    with io.open(path, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    if isinstance(d, dict) and isinstance(d.get("records"), dict):
        return d["records"]
    if isinstance(d, dict):
        return d
    raise ValueError("unrecognized ledger shape (neither a records shell "
                     "nor a bare dict): %s" % path)


def merge_ledgers(paths):
    """Union merge (later batch overrides) -> (merged, labels); `batches`
    accumulates the full label history."""
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
    """Missing library of a record: the `missing` field when present, else
    the regex over the `red` text; None when this is not a missing-library
    case."""
    m = rec.get("missing")
    if m:
        return m
    red = rec.get("red") or ""
    mm = MISSING_LIB_RE.search(red)
    return mm.group(1) if mm else None


def build_graph(merged):
    # chain-root `self` block = the root's own record in the merged ledger:
    # washable=true (rc=0) — treating this root unlocks every dependent;
    # washable=false (rc!=0) — the root itself is blocked, a cycle in the
    # chain, treat the root's cause first; probed=false — the root is absent
    # from the candidate set (UNPROBED, pending probe).
    """Chain-root graph: rc=1 records grouped by missing library plus the
    root's own washability. -> (libs, stats, rc1_missing)."""
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
    """Top-list markdown (deterministic; dependents count descending)."""
    lines = ["# Chain Graph TOP (chain-root graph, union of %d ledgers)"
             % len(paths), ""]
    lines.append("- merged_total=%d rc0=%d rc1=%d other=%d"
                 % (stats["merged_total"], len(stats["rc0"]),
                    len(stats["rc1"]), len(stats["other"])))
    lines.append("- rc1 missing-library=%d non-missing (other failure "
                 "classes)=%d"
                 % (len(rc1_missing), len(stats["rc1"]) - len(rc1_missing)))
    lines.append("- missing-library roots (distinct libs)=%d" % len(libs))
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
    """Frozen vector set (temporary synthetic ledgers; zero real-repo
    touches, zero network): union override, batches accumulation,
    missing-library grouping, three-way self washability, top-list
    determinism, CLI four codes."""
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
        # ledger A: LibX rc=0 (washable chain root) plus two missing-library
        # consumers; LibY itself rc=1 (a cycle in the chain)
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
        # ledger B: B2 turns passing in the later batch (override); D1 is a
        # new LibX consumer
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
        # later batch overrides: B2 takes the ledger-B rc=0 record and its
        # batches accumulate as [ledgerA, ledgerB]
        b2 = g["records"]["B2"]
        assert b2["rc"] == 0 and b2["batches"] == ["ledgerA", "ledgerB"], b2
        # chain root: LibX dependents=B1,D1 (B2 left after turning passing
        # in the later batch); self washable
        lx = g["libs"]["LibX"]
        assert lx["n"] == 2 and lx["dependents"] == ["B1", "D1"], lx
        assert lx["self"]["probed"] and lx["self"]["washable"] is True, lx
        # cycle in the chain: LibY itself rc=1 -> washable=false
        ly = g["libs"]["LibY"]
        assert ly["n"] == 1 and ly["self"]["washable"] is False, ly
        # top-list determinism: rerun is byte-identical
        before_j = io.open(jf, "rb").read()
        before_m = io.open(mf, "rb").read()
        p = run([fa, fb, "--json", jf, "--md", mf])
        assert p.returncode == 0, p.stdout
        assert io.open(jf, "rb").read() == before_j, "json byte drift = violation"
        assert io.open(mf, "rb").read() == before_m, "md byte drift = violation"
        assert "LibX" in before_m.decode("utf-8"), "top list missing a chain root"
        # CLI four codes
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag should exit 2, got %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "missing ledgers should exit 2, got %d" % p.returncode
        p = run([os.path.join(tmp, "nope.json")])
        assert p.returncode == 9, "missing ledger file should exit 9, got %d" % p.returncode
        print("CHAIN-GRAPH-SELFTEST PASS: union-override/batches-accumulation/"
              "chain-root-grouping/self-washability-three-way/deterministic-"
              "byte-stability/cli-four-codes six checks pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="merge probe ledgers -> chain-root graph "
                               "(missing-lib -> dependents -> self "
                               "washability) -> top list as markdown+json")
    ap.add_argument("ledgers", nargs="*", metavar="LEDGER.json",
                    help="probe ledgers (argv order = merge order; later "
                         "batches override earlier ones)")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="chain-root graph raw-data output")
    ap.add_argument("--md", default=None, metavar="out.md",
                    help="top-list markdown output")
    ap.add_argument("--top", type=int, default=25, metavar="N",
                    help="top-list row count (default 25)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not args.ledgers:
        print("FAIL-LOUD: at least one probe ledger is required "
              "(except --selftest)", file=sys.stderr)
        sys.exit(2)
    for pth in args.ledgers:
        if not os.path.exists(pth):
            print("FAIL-LOUD: ledger missing: %s" % pth, file=sys.stderr)
            sys.exit(9)

    merged, labels = merge_ledgers(args.ledgers)
    libs, stats, rc1_missing = build_graph(merged)

    print("=== CHAIN-GRAPH MERGE ===")
    print("ledgers: %s" % ", ".join("%s=%s" % (l, p) for l, p
                                    in zip(labels, args.ledgers)))
    print("union total: %d rc0: %d rc1: %d other: %d"
          % (stats["merged_total"], len(stats["rc0"]), len(stats["rc1"]),
             len(stats["other"])))
    print("rc1 missing-lib: %d  rc1 non-missing (other failure classes): %d"
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
           # libs is written to json in name order (sort_keys); the rank
           # order is kept explicitly in top_order
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
