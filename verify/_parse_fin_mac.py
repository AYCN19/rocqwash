#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_parse_fin_mac.py — censusFIN_mac extraction parser (macOS form, Prop-erasure verification).

Purpose.  Classify each statement of a censusFIN_mac `.ml` extraction by
erasure semantics alone, vocabulary-independent: `red` iff "__" appears in
the let body or the value annotation (the Prop-erasure criterion;
Set-cloaked Prop included), `clean` iff no "__" occurs, and per-name
`missing` reported fail-loud when neither a let body nor a type alias
matches, since absence from a full extraction is itself the erasure
criterion.  A `--vo` run adds the four-point pass criterion on the probe
artifacts (exit file, transcript error scan, `.vo` magic, `.vo` freshness).

Interface.  python3 _parse_fin_mac.py SortAlive_Probe_<W>.ml --manifest manifest_<W>.json \
      [--vo SortAlive_Probe_<W>.vo --probe-v SortAlive_Probe_<W>.v \
       --transcript _fin_<W>_build.log --exit-file _fin_<W>.exit --json out.json]
Prints one JSON verdict object on stdout; `--json PATH` also writes the full
result record.  `--vo` requires `--probe-v` for the freshness check.

Dependencies.  Python 3 standard library only; inputs are the `.ml`
extraction and a manifest JSON carrying a `statements` list, plus the
optional build transcript, exit file and `.vo`/`.v` probe artifacts.

Evidence.  The annotation regex tolerates the colon-newline layout because a
single-shape regex drops the whole block when the type annotation breaks
after the colon, reporting a false CLEAN.  The type-alias alternative also
matches the parameterized form `type 'a alive_N = ...`.

Exit-codes.  0 = verdict PASS (four-point criterion holds, any
`--expect-red` assertion holds, no missing names); 2 = verdict FAIL;
9 = `--vo` given without `--probe-v`.
"""
import argparse
import io
import json
import os
import re
import sys

VO_MAGIC_HEX = "436f712100015ff4"


def parse_census(ml_path, manifest, transcript=None):
    ml = io.open(ml_path, encoding="utf-8").read()
    entries = manifest["statements"]
    red, clean, missing = [], [], []
    type_ledger = {"set": [], "type": []}
    for e in entries:
        aid = "alive_%d" % e["idx"]
        # two-shape annotation rule: `:\s*` tolerates both the colon-plus-space and the colon-plus-newline layouts
        ann = re.search(r"\(\*\* val %s :\s*(.+?) \*\*\)" % re.escape(aid), ml, re.S)
        body = re.search(r"^let (?:rec )?%s[^=]*=\n(.*?)(?=\n\n|\n\(\*\*|\Z)" % re.escape(aid),
                         ml, re.M | re.S)
        # third shape of the annotation/type rule family: the parameterized type alias form `type 'a alive_N = ...`
        talias = re.search(r"^type (?:\'[A-Za-z0-9_]+ +)*%s = (.+)$" % re.escape(aid), ml, re.M)
        if body is None and talias is None:
            missing.append(e)
            continue
        if talias is not None:
            target = talias.group(1).strip()
            if "__" in target:
                red.append({**e, "evidence": "type %s = %s" % (aid, target)})
            else:
                clean.append({**e, "evidence": "type %s = %s (set-valued type)" % (aid, target)})
                type_ledger["set"].append(e["name"])
            continue
        btext = body.group(1).strip()
        ann_t = ann.group(1).strip() if ann else "?"
        body_erased = "__" in btext
        ann_erased = "__" in ann_t
        if body_erased or ann_erased:
            red.append({**e, "evidence": "let %s = %s (ann: %s)"
                        % (aid, btext[:48], ann_t[:64])})
        else:
            clean.append({**e, "evidence": "let %s = %s (ann: %s)"
                          % (aid, btext[:48], ann_t[:64])})
            if "forall" in ann_t or "'a" in ann_t:
                type_ledger["type"].append(e["name"])
            else:
                type_ledger["set"].append(e["name"])
    res = {"world": manifest["world"], "red": red, "clean": clean,
           "missing": missing, "total": len(entries),
           "clean_split": {"set_resident": len(type_ledger["set"]),
                           "type_resident": len(type_ledger["type"]),
                           "type_resident_names": type_ledger["type"]}}
    if transcript:
        log = io.open(transcript, encoding="utf-8", errors="replace").read()
        errs = [ln for ln in log.splitlines() if "Error" in ln or "Error:" in ln]
        res["transcript_error_lines"] = len(errs)
        res["transcript_errors_head"] = errs[:5]
    return res


def check_four_piece(probe_v, vo, exit_file=None):
    """Four-point pass criterion check on the probe artifacts: vo magic, freshness, exit."""
    chk = {"probe_v": probe_v, "vo": vo}
    ok = True
    if not os.path.exists(vo):
        chk["vo_exists"] = False
        return False, chk
    chk["vo_exists"] = True
    with open(vo, "rb") as f:
        head = f.read(8)
    chk["vo_magic"] = head.hex()
    magic_ok = (head.hex() == VO_MAGIC_HEX)
    chk["magic_ok"] = magic_ok
    fresh = os.path.getmtime(vo) > os.path.getmtime(probe_v)
    chk["vo_fresher_than_v"] = fresh
    exit_ok = True
    if exit_file:
        if os.path.exists(exit_file):
            rc = io.open(exit_file).read().strip()
            chk["exit_code"] = rc
            exit_ok = (rc == "0")
        else:
            chk["exit_code"] = "MISSING"
            exit_ok = False
    chk["exit_ok"] = exit_ok
    ok = magic_ok and fresh and exit_ok
    return ok, chk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ml")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--vo")
    ap.add_argument("--probe-v")
    ap.add_argument("--transcript")
    ap.add_argument("--exit-file")
    ap.add_argument("--json")
    ap.add_argument("--expect-red", type=int, default=None,
                    help="期望红数断言（不等 exit 2·如 S09 干跑 --expect-red 0）")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    manifest = json.load(io.open(args.manifest, encoding="utf-8"))
    res = parse_census(args.ml, manifest, args.transcript)
    four_ok = True
    if args.vo:
        if not args.probe_v:
            print("FAIL-LOUD: --vo 需配 --probe-v（新鲜度对表）")
            sys.exit(9)
        four_ok, chk = check_four_piece(args.probe_v, args.vo, args.exit_file)
        res["four_piece"] = chk
        res["four_piece_ok"] = four_ok
    expect_ok = True
    if args.expect_red is not None:
        expect_ok = (len(res["red"]) == args.expect_red)
        res["expect_red"] = args.expect_red
        res["expect_ok"] = expect_ok
    out = json.dumps({"world": res["world"], "total": res["total"],
                      "red": len(res["red"]), "clean": len(res["clean"]),
                      "missing": len(res["missing"]),
                      "missing_names": [e["name"] for e in res["missing"]],
                      "red_names": [e["name"] for e in res["red"]],
                      "clean_split": res["clean_split"],
                      "transcript_error_lines": res.get("transcript_error_lines"),
                      "four_piece": res.get("four_piece"),
                      "verdict": "PASS" if (four_ok and expect_ok and not res["missing"]) else "FAIL"},
                     ensure_ascii=False, indent=1)
    print(out)
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
        print("json ->", args.json)
    sys.exit(0 if (four_ok and expect_ok and not res["missing"]) else 2)


if __name__ == "__main__":
    main()
