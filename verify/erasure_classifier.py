# -*- coding: utf-8 -*-
"""erasure_classifier.py — classification advisor for extraction erasure stations.

    Purpose.  Inventories erasure stations in a separately-extracted OCaml
      interface (.mli) — statements whose type the extractor rendered as `__`
      — and assigns each a classification cluster with a disposition
      suggestion: 1 permutation-conclusion → stdlib-Prop registration-class
      candidate; 2 sorted-conclusion → already dissolved (the statement now
      carries a real Set-carrier type); 3 neq-conclusion → real debt (rewrite
      the statement face to the carrier-equality negation form);
      4 membership-conclusion → capture-adjudication (await human
      adjudication); 5 premise-position → legal erasure (premises may stay
      logical); 6 other / inner-component → manual review.  A first-pass
      advisor for a human adjudicator, never a final verdict.

    Interface.  --mli path/to/Module.mli (primary input); --json
      path/to/scan.json (optional cross-check: scanner CAPTURE stations keyed
      by channel — annotates agreement for cluster 4); --resolve name1,name2
      (names expected dissolved — the report shows their current val type
      status); --json-out out.json; --md-out out.md (human-readable ledger).
      Per-station records carry {name, line, kind, cluster, suggestion,
      evidence} plus per-cluster totals and the cross-check annotations.
      Minimal usage: python3 erasure_classifier.py --mli Module.mli --json-out r.json --md-out r.md

    Dependencies.  Python 3 standard library only (argparse, hashlib, io, json, os, re, sys).
    Evidence.  --selftest built-in vectors (six clusters, `coq_` prefix
      forms, premise positions, multi-line inner-component stations) and
      suite coverage under tests/test_erasure_classifier.py.

    Exit-codes.  0 = ran; 2 = usage or failing selftest; 9 = input missing.
"""
import argparse, hashlib, io, json, os, re, sys

TYPE_PREMISE_RE = re.compile(r"^[ \t]*type\s+(?P<name>[A-Za-z_][\w']*)\s*=.*__")
HEADER_ERASE_RE = re.compile(r"^[ \t]*type\s+__\s*=\s*Obj\.t\s*$")

# cluster ids and their disposition suggestions
CLUSTERS = {
    "permutation-conclusion":
        "stdlib-Prop registration-class candidate (stdlib Permutation "
        "conclusion erased; suggest class registration — adjudicator decides)",
    "sorted-conclusion":
        "already dissolved: statement carries a real Set-carrier type "
        "(set-carried reshape resolution)",
    "neq-conclusion":
        "real debt: rewrite the statement face to the carrier-equality "
        "negation form (QeqT negation) — adjudicator schedules",
    "membership-conclusion":
        "capture-adjudication (CAPTURE): await human adjudication",
    "premise-position":
        "legal erasure: premise positions may remain logical",
    "other":
        "manual review required (no pattern matched)",
}

INFRA = "infrastructure"


def strip_coq_prefix(name):
    return name[4:] if name.startswith("coq_") else name


def name_cluster(name):
    """Pattern heuristics over the coq_-stripped lowercase name; returns a
    cluster id or None.  Grounded in the reference adjudication set:
    *perm* / *sort* / *neq|_ne* / *in* membership tokens."""
    low = strip_coq_prefix(name).lower()
    if "perm" in low:
        return "permutation-conclusion"
    if "sort" in low:
        return "sorted-conclusion"
    if low.endswith("_ne") or "neq" in low:
        return "neq-conclusion"
    if "_in" in low or low.startswith("in_"):
        return "membership-conclusion"
    return None


def val_entries(lines):
    """Join multi-line val declarations: [(start_line, name, full_type_text)].
    A val whose type continues on the next line (empty remainder or unbalanced
    parentheses) consumes continuation lines until parentheses balance."""
    entries = []
    i = 0
    n = len(lines)
    val_head = re.compile(r"^[ \t]*val\s+([A-Za-z_][\w']*)\s*:\s*(.*)$")
    while i < n:
        m = val_head.match(lines[i])
        if not m:
            i += 1
            continue
        name, ty = m.group(1), m.group(2)
        start = i + 1
        bal = ty.count("(") - ty.count(")")
        while (bal > 0 or ty.strip() == "") and i + 1 < n:
            i += 1
            cont = lines[i]
            ty += " " + cont.strip()
            bal += cont.count("(") - cont.count(")")
        entries.append((start, name, ty))
        i += 1
    return entries


def parse_mli(path):
    """Inventory erasure stations from an extraction interface.
    Returns (stations, header_count)."""
    try:
        text = io.open(path, "r", encoding="utf-8", errors="replace").read()
    except OSError as e:
        raise SystemExit("INPUT-MISSING: %s (%s)" % (path, e))
    lines = text.split("\n")
    stations = []
    header_count = 0
    for i, l in enumerate(lines, 1):
        if HEADER_ERASE_RE.match(l):
            header_count += 1
    for start, name, ty in val_entries(lines):
        if ty.strip() == "__":
            cl = name_cluster(name)
            stations.append(dict(name=name, line=start, kind="conclusion",
                                 erased_whole=True,
                                 cluster=cl or "other"))
        elif "__" in ty:
            positions = ty.count("__")
            # conclusion clusters apply to whole-conclusion erasures only;
            # inner-component positions are advisory "other" with the
            # name-pattern hint recorded for the adjudicator.
            stations.append(dict(name=name, line=start, kind="inner-component",
                                 erased_whole=False, positions=positions,
                                 cluster="other",
                                 name_hint=name_cluster(name),
                                 type_hint=ty[:100]))
    for i, l in enumerate(lines, 1):
        m = TYPE_PREMISE_RE.match(l)
        if m and m.group("name") != "__":
            name = m.group("name")
            positions = l.count("__")
            stations.append(dict(name=name, line=i, kind="premise-position",
                                 erased_whole=False, positions=positions,
                                 cluster="premise-position"))
    stations.sort(key=lambda s: (s["line"], s["name"]))
    return stations, header_count


def classify(path_mli, crosscheck=None, resolve_names=()):
    stations, header_count = parse_mli(path_mli)

    # cluster 2 realization: names expected dissolved but currently erased?
    resolve = []
    mli_text = io.open(path_mli, "r", encoding="utf-8", errors="replace").read()
    by_name = {}
    for _start, nm, ty in val_entries(mli_text.split("\n")):
        by_name[nm] = ty
    for nm in resolve_names:
        erased = any(s["name"] == nm and s["kind"] == "conclusion"
                     for s in stations)
        if erased:
            resolve.append(dict(name=nm, status="still-erased"))
        elif any(strip_coq_prefix(s["name"]) == strip_coq_prefix(nm)
                 for s in stations):
            resolve.append(dict(name=nm, status="still-erased"))
        elif nm in by_name or ("coq_" + nm) in by_name:
            ty = by_name.get(nm, by_name.get("coq_" + nm, "?"))
            resolve.append(dict(name=nm, status="resolved",
                                evidence="val type present: %s" % ty[:60]))
        else:
            resolve.append(dict(name=nm, status="missing"))

    # cluster 4 cross-check against a scanner capture report
    capture_agree = None
    if crosscheck:
        cap = set(crosscheck.get("capture_stations", {}).get("P6_In", []))
        found = set(strip_coq_prefix(s["name"]) for s in stations
                    if s["cluster"] == "membership-conclusion")
        capture_agree = dict(scanner_captured=sorted(cap),
                             classifier_membership=sorted(found),
                             agree=(cap == found))

    totals = {}
    for s in stations:
        totals[s["cluster"]] = totals.get(s["cluster"], 0) + 1
    return dict(mli=path_mli,
                md5=md5_of(path_mli),
                station_count=len(stations),
                infrastructure_lines=header_count,
                stations=stations,
                totals=totals,
                resolve=resolve,
                capture_agree=capture_agree)


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_md(res, out):
    lines = ["# Erasure station classification ledger", ""]
    lines.append("- input mli: `%s` (md5 `%s`)" % (res["mli"], res["md5"]))
    lines.append("- stations: %d (infrastructure header lines: %d)"
                 % (res["station_count"], res["infrastructure_lines"]))
    lines.append("- totals per cluster: %s" % json.dumps(res["totals"], sort_keys=True))
    lines.append("")
    lines.append("| name | line | kind | cluster | suggestion |")
    lines.append("|---|---|---|---|---|")
    for s in res["stations"]:
        sug = CLUSTERS[s["cluster"]]
        lines.append("| `%s` | %d | %s | %s | %s |"
                     % (s["name"], s["line"], s["kind"], s["cluster"], sug))
    if res["resolve"]:
        lines.append("")
        lines.append("## Dissolution check (names expected resolved)")
        lines.append("")
        lines.append("| name | status | evidence |")
        lines.append("|---|---|---|")
        for r in res["resolve"]:
            lines.append("| `%s` | %s | %s |"
                         % (r["name"], r["status"], r.get("evidence", "-")))
    if res["capture_agree"] is not None:
        ca = res["capture_agree"]
        lines.append("")
        lines.append("## CAPTURE cross-check")
        lines.append("")
        lines.append("- scanner captured: %s" % ca["scanner_captured"])
        lines.append("- classifier membership cluster: %s" % ca["classifier_membership"])
        lines.append("- agree: %s" % ca["agree"])
    lines.append("")
    lines.append("This ledger is an advisor report; final adjudication is human.")
    with io.open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def selftest():
    ok = True
    sample = """type __ = Obj.t
val insert_perm_cons : __
val coq_D5_perm : __
val xq_hd_In : __
val xq_last_In : __
val q_lt_neq0 : __
val cons_ne : __
type all_same = Q -> Q -> __ -> __ -> QeqT
val inner_user : (Q, (__ * Q) sigT) And
val clean_thing : Q
val sorted_now : SortedCarrier
val counter_ex :
    (Q list, (Q list, (__, Q Not) And) sigT) sigT
"""
    io_tmp = "/tmp/erasure_selftest_%d.mli" % os.getpid()
    with io.open(io_tmp, "w", encoding="utf-8") as f:
        f.write(sample)
    res = classify(io_tmp)
    clusters = dict((s["name"], s["cluster"]) for s in res["stations"])
    checks = [
        ("header counted", res["infrastructure_lines"] == 1),
        ("perm cluster", clusters.get("insert_perm_cons") == "permutation-conclusion"),
        ("coq_ perm cluster", clusters.get("coq_D5_perm") == "permutation-conclusion"),
        ("membership cluster", clusters.get("xq_hd_In") == "membership-conclusion"),
        ("membership cluster 2", clusters.get("xq_last_In") == "membership-conclusion"),
        ("neq cluster", clusters.get("q_lt_neq0") == "neq-conclusion"),
        ("neq cluster suffix", clusters.get("cons_ne") == "neq-conclusion"),
        ("premise cluster", clusters.get("all_same") == "premise-position"),
        ("inner other", clusters.get("inner_user") == "other"),
        ("multiline val inner", clusters.get("counter_ex") == "other"),
        ("typed val not a station", "clean_thing" not in clusters),
        ("sorted typed val not a station", "sorted_now" not in clusters),
        ("premise positions", next(s["positions"] for s in res["stations"]
                                   if s["kind"] == "premise-position") == 2),
    ]
    os.unlink(io_tmp)
    for name, c in checks:
        print("  %-28s %s" % (name, "ok" if c else "FAIL"))
        ok = ok and c
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return ok


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(
        description="Classification advisor for extraction erasure stations.")
    ap.add_argument("--mli", help="extraction interface .mli (primary input)")
    ap.add_argument("--json", help="scanner report with capture_stations (cross-check)")
    ap.add_argument("--resolve", help="names expected dissolved (comma-separated)")
    ap.add_argument("--json-out", help="classification report JSON path")
    ap.add_argument("--md-out", help="markdown ledger path")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(0 if selftest() else 2)

    if not args.mli:
        ap.print_help()
        sys.exit(2)
    if not os.path.exists(args.mli):
        print("FILE-MISSING:", args.mli)
        sys.exit(9)
    cross = None
    if args.json:
        if not os.path.exists(args.json):
            print("FILE-MISSING:", args.json)
            sys.exit(9)
        with io.open(args.json, "r", encoding="utf-8") as f:
            cross = json.load(f)
    resolve_names = [t.strip() for t in args.resolve.split(",")] if args.resolve else []

    res = classify(args.mli, crosscheck=cross, resolve_names=resolve_names)
    print("mli: %s" % res["mli"])
    print("md5: %s" % res["md5"])
    print("stations: %d  infrastructure: %d" % (res["station_count"], res["infrastructure_lines"]))
    print("totals: %s" % json.dumps(res["totals"], sort_keys=True))
    for s in res["stations"]:
        print("  L%-5d %-30s %-16s -> %s" % (s["line"], s["name"], s["kind"], s["cluster"]))
    if res["resolve"]:
        for r in res["resolve"]:
            print("  resolve: %-28s %s %s" % (r["name"], r["status"], r.get("evidence", "")))
    if res["capture_agree"] is not None:
        print("capture agree: %s" % res["capture_agree"]["agree"])
    print("advisor report only — final adjudication is human.")
    if args.json_out:
        with io.open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
        print("report json -> %s" % args.json_out)
    if args.md_out:
        write_md(res, args.md_out)
        print("ledger md -> %s" % args.md_out)
    sys.exit(0)


if __name__ == "__main__":
    main()
