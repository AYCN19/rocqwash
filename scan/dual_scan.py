#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dual_scan.py — dual-scanner cross-check driver (scan_v4_token + mac_stmt_scan).

Purpose:
    Runs the two word-face scanners over the same candidate files and
    cross-checks their station reports:

        scan_v4_token.py   token-level qualified-identifier census
                           (stations: {line, col, token, cls, ...});
        mac_stmt_scan.py   statement-face scanner (hits: {line, cat, ...},
                           plus red_names / capture_stations counters).

    Both scanners are word-face instruments: they are structurally blind to
    red causes that live on the application/type face (e.g. the S07-lineage
    "Illegal application" family) — the dual run turns that shared blindness
    into a mechanical fact per file (two scanners at zero stations) instead
    of a silent assumption.  Scanner consensus is NOT a completeness
    certificate: the diff report states per file which stations only one
    scanner saw, so a third source can be pulled in for the gap.

Inputs:
    --dir path/to/candidates   scan every *.v in the directory (sorted);
                               repeatable with --file for single targets.
    --file path/to/file.v      explicit target (repeatable).
    --out report.json          write the report here (JSON).
    --scan-v4 path             scan_v4_token.py path (default: sibling file).
    --mac-stmt path            mac_stmt_scan.py path (default: sibling file).
    --timeout seconds          per-scan subprocess timeout (default 300).

Outputs:
    report JSON — {file: {scanv4: {rc, stations, lines},
                          macstmt: {rc, hits, red_names, capture, lines},
                          diff: {only_v4, only_stmt, common}}}
    plus a per-file DUAL line on stdout.  Exit code = number of failed
    scanner runs (0 = every scan ran clean; station counts never fail).

Minimal usage:
    python3 dual_scan.py --dir path/to/candidates --out report.json
    python3 dual_scan.py --file a.v --file b.v
"""
import argparse, glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd, timeout):
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        return None


def _load(path):
    try:
        with io_open(path) as fh:
            return json.load(fh)
    except Exception:
        return None


def io_open(path):
    import io
    return io.open(path, "r", encoding="utf-8")


def scan_one(path, scan_v4, mac_stmt, timeout, tmpdir):
    """Dual-scan one file; returns the per-file record."""
    rec = {}
    j4 = os.path.join(tmpdir, "dual_v4_%d.json" % abs(hash(path)))
    p1 = run([sys.executable, "-B", scan_v4, "--file", path, "--json", j4],
             timeout)
    if p1 is None:
        rec["scanv4"] = {"rc": 124, "stations": None, "lines": []}
    else:
        rec["scanv4"] = {"rc": p1.returncode, "stations": None, "lines": []}
        d1 = _load(j4) if p1.returncode == 0 and os.path.exists(j4) else None
        if d1 is not None:
            stations = d1.get("stations", [])
            rec["scanv4"]["stations"] = len(stations)
            rec["scanv4"]["lines"] = sorted(set(
                s.get("line") for s in stations if s.get("line")))
        elif p1.returncode != 0:
            rec["scanv4"]["stderr"] = (p1.stderr or p1.stdout or "")[:200]
    j2 = os.path.join(tmpdir, "dual_stmt_%d.json" % abs(hash(path)))
    p2 = run([sys.executable, "-B", mac_stmt, "--file", path, "--json", j2],
             timeout)
    if p2 is None:
        rec["macstmt"] = {"rc": 124, "hits": None, "red_names": None,
                          "capture": None, "lines": []}
    else:
        d2 = (_load(j2)
              if p2.returncode == 0 and os.path.exists(j2) else None)
        hits = (d2 or {}).get("hits", [])
        rec["macstmt"] = {
            "rc": p2.returncode,
            "hits": len(hits) if isinstance(hits, list) else None,
            "red_names": d2.get("red_names") if d2 else None,
            "capture": (len(d2.get("capture_stations", []))
                        if d2 and isinstance(d2.get("capture_stations"),
                                             list) else None),
            "lines": sorted(set(h.get("line") for h in hits
                                if isinstance(h, dict) and h.get("line"))),
        }
        if p2.returncode != 0:
            rec["macstmt"]["stderr"] = (p2.stderr or p2.stdout or "")[:200]
    l4 = set(rec["scanv4"]["lines"])
    l2 = set(rec["macstmt"]["lines"])
    rec["diff"] = {"only_v4": sorted(l4 - l2), "only_stmt": sorted(l2 - l4),
                   "common": sorted(l4 & l2)}
    return rec


def main():
    ap = argparse.ArgumentParser(
        description="Dual-scanner cross-check driver "
                    "(scan_v4_token + mac_stmt_scan).")
    ap.add_argument("--dir", action="append", default=[],
                    help="directory of candidate .v files (repeatable)")
    ap.add_argument("--file", action="append", default=[],
                    help="single candidate .v file (repeatable)")
    ap.add_argument("--out", help="write the report JSON here")
    ap.add_argument("--scan-v4", default=os.path.join(HERE,
                                                      "scan_v4_token.py"))
    ap.add_argument("--mac-stmt", default=os.path.join(HERE,
                                                       "mac_stmt_scan.py"))
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    for tool in (args.scan_v4, args.mac_stmt):
        if not os.path.exists(tool):
            print("TOOL-MISSING:", tool)
            return 9
    targets = []
    for d in args.dir:
        if not os.path.isdir(d):
            print("DIR-MISSING:", d)
            return 2
        targets.extend(sorted(glob.glob(os.path.join(d, "*.v"))))
    for f in args.file:
        if not os.path.exists(f):
            print("FILE-MISSING:", f)
            return 9
        targets.append(f)
    seen = set()
    targets = [t for t in targets
               if not (t in seen or seen.add(t))]
    if not targets:
        print("NO-TARGETS")
        return 2

    import tempfile
    report = {}
    fails = 0
    tmpdir = tempfile.mkdtemp(prefix="rw_dual_")
    try:
        for path in targets:
            rec = scan_one(path, args.scan_v4, args.mac_stmt,
                           args.timeout, tmpdir)
            report[os.path.basename(path)] = rec
            v4, ms, df = rec["scanv4"], rec["macstmt"], rec["diff"]
            if v4["rc"] != 0 or ms["rc"] != 0:
                fails += 1
            print("DUAL %s scanv4(rc=%s,stations=%s) macstmt(rc=%s,hits=%s) "
                  "diff(only_v4=%d,only_stmt=%d)"
                  % (os.path.basename(path), v4["rc"], v4["stations"],
                     ms["rc"], ms["hits"], len(df["only_v4"]),
                     len(df["only_stmt"])))
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
    if args.out:
        import io
        with io.open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1,
                      sort_keys=True)
        print("report -> %s" % args.out)
    print("DUAL-SCAN-DONE files=%d fails=%d" % (len(targets), fails))
    return fails


if __name__ == "__main__":
    sys.exit(main())
