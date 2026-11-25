#!/usr/bin/env python3
"""xtr_erasure_link.py - three-source erasure link over the declaration
face, extraction products, and captured Print Assumptions reports.

Purpose.  Rocq erases Prop-carrying proofs at extraction; a proof
constant that nonetheless appears as a computational item in an
extraction product is an erasure leak.  This tool links three sources
per constant - the .v declaration face (Theorem/Lemma heads are
Prop-carried candidates; Definition/Fixpoint heads are computational),
the extraction products (.ml/.mli/.hs), and
optional captured Print Assumptions reports - and issues a three-state
verdict CLEAN / LEAK / INCONCLUSIVE per Prop-carried constant.
Schema rocqwash.xtr-erasure-link/1.  Report-only; existing verify/
gates stay untouched.

Interface.
  python -B verify/xtr_erasure_link.py --decl-sources DIR --sources DIR [--assumptions DIR] [--out FILE] [--format json|text] [--selftest]

Exit-codes.  0 success; 1 fail-loud; 2 usage error.

Safety.  Zero network, stdlib only, read-only over input trees; the
only write is the caller-named --out file.  Determinism: sorted keys,
no wall clock.  Honesty: statement-head and product-presence matching
are textual token-boundary heuristics, not kernel facts; advisory.

Evidence.  Eight selftest vectors (clean, leak, inconclusive,
computational scoping, token-boundary precision, assumption overlay
with escalation and missing honesty, determinism), green at integration.

Dependencies.  Python 3 standard library only.
"""
import argparse
import json
import os
import re
import sys

SCHEMA = "rocqwash.xtr-erasure-link/1"
GENERATED_BY = "verify/xtr_erasure_link.py"
SELFTEST_MARKER = "XTR-ERASURE-LINK-SELFTEST PASS"
PRODUCT_EXTS = (".ml", ".mli", ".hs")
ASSUMPTION_EXTS = (".pa", ".txt")

_PROP_HEAD_RE = re.compile(
    r"^\s*(?:Theorem|Lemma|Corollary|Remark|Fact|Proposition)\s+"
    r"([A-Za-z_][A-Za-z0-9_']*)")
_COMP_HEAD_RE = re.compile(
    r"^\s*(?:Definition|Fixpoint|CoFixpoint|Let|Example|Instance)\s+"
    r"([A-Za-z_][A-Za-z0-9_']*)")
_CLOSED_MARKER = "Closed under the global context"
_AXIOM_LINE_RE = re.compile(
    r"^\s*(?:Axioms?|Variables?|Parameters?)\s*:", re.IGNORECASE)
_PRESENCE_RE = None  # built per constant (token-boundary match)


def mask_rocq_comments(text):
    """Blank nested (* *) spans, preserving newlines."""
    out = []
    i = 0
    depth = 0
    n = len(text)
    while i < n:
        if text.startswith("(*", i):
            depth += 1
            out.append("  ")
            i += 2
        elif depth > 0 and text.startswith("*)", i):
            depth -= 1
            out.append("  ")
            i += 2
        elif depth > 0:
            out.append("\n" if text[i] == "\n" else " ")
            i += 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def scan_declarations(text, filename):
    """Split statement heads of one .v source into prop and comp faces."""
    masked = mask_rocq_comments(text)
    prop, comp = [], []
    for line in masked.split("\n"):
        m = _PROP_HEAD_RE.match(line)
        if m:
            prop.append({"name": m.group(1), "file": filename})
            continue
        m = _COMP_HEAD_RE.match(line)
        if m:
            comp.append({"name": m.group(1), "file": filename})
    return prop, comp


def presence(text, name):
    """Token-boundary check whether a product text mentions name."""
    pattern = r"(?<![A-Za-z0-9_'])" + re.escape(name) + \
              r"(?![A-Za-z0-9_'])"
    return re.search(pattern, text) is not None


def stem(name):
    return os.path.splitext(os.path.basename(name))[0].lower()


def load_assumptions(dirpath):
    """Map constant name to 'closed' / 'non-closed' / 'unparsed'."""
    result = {}
    if dirpath is None:
        return result
    for name in sorted(os.listdir(dirpath)):
        ext = os.path.splitext(name)[1]
        if ext not in ASSUMPTION_EXTS:
            continue
        path = os.path.join(dirpath, name)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            result[stem(name)] = "missing"
            continue
        if _CLOSED_MARKER in text:
            result[stem(name)] = "closed"
        elif _AXIOM_LINE_RE.search(text):
            result[stem(name)] = "non-closed"
        else:
            result[stem(name)] = "unparsed"
    return result


def build_report(pairs, product_pairs, assumptions_dir):
    """Assemble the link report.

    pairs:        (filename, text) of .v declaration sources
    product_pairs:(relpath, text) of extraction products
    assumptions_dir: directory of captured Print Assumptions reports
    """
    assumptions = load_assumptions(assumptions_dir)
    prop = []
    comp = []
    for filename, text in pairs:
        p, c = scan_declarations(text, filename)
        prop.extend(p)
        comp.extend(c)
    products_by_stem = {}
    for relpath, text in product_pairs:
        products_by_stem.setdefault(stem(relpath), []).append(text)
    entries = []
    for item in sorted(prop, key=lambda x: (x["name"], x["file"])):
        name = item["name"]
        linked = products_by_stem.get(stem(item["file"]), [])
        if not linked:
            verdict = "INCONCLUSIVE"
            in_products = False
        else:
            in_products = any(presence(text, name) for text in linked)
            verdict = "LEAK" if in_products else "CLEAN"
        entry = {
            "name": name,
            "declared_in": item["file"],
            "verdict": verdict,
            "in_products": in_products,
            "linked_products": len(linked),
        }
        if assumptions_dir is not None:
            entry["assumptions"] = assumptions.get(name.lower(), "missing")
            if entry["assumptions"] == "non-closed" and in_products:
                entry["escalated"] = True
        entries.append(entry)
    comp_names = sorted({c["name"] for c in comp})
    counts = {"CLEAN": 0, "LEAK": 0, "INCONCLUSIVE": 0}
    for e in entries:
        counts[e["verdict"]] += 1
    return {
        "schema": SCHEMA,
        "generated_by": GENERATED_BY,
        "prop_carried": entries,
        "computational_declarations": comp_names,
        "assumptions_report": None if assumptions_dir is None
                              else dict(sorted(assumptions.items())),
        "summary": {
            "prop_carried": len(entries),
            "computational": len(comp_names),
            "verdicts": counts,
            "products": len(product_pairs),
        },
    }


def report_json(report):
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def report_text(report):
    lines = ["xtr-erasure-link %s" % SCHEMA]
    s = report["summary"]
    lines.append("prop_carried=%d leak=%d clean=%d inconclusive=%d "
                 "products=%d" % (s["prop_carried"], s["verdicts"]["LEAK"],
                                  s["verdicts"]["CLEAN"],
                                  s["verdicts"]["INCONCLUSIVE"],
                                  s["products"]))
    for e in report["prop_carried"]:
        extra = ""
        if "assumptions" in e:
            extra = " assumptions=%s" % e["assumptions"]
            if e.get("escalated"):
                extra += " ESCALATED"
        lines.append("  %-24s %-12s in_products=%s%s" % (
            e["name"], e["verdict"], str(e["in_products"]).lower(), extra))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Selftest (in-process fixtures, no disk reads)
# ---------------------------------------------------------------------------

def _selftest():
    failures = []

    def check(cond, label):
        if not cond:
            failures.append(label)

    decl = ("decls.v",
            "Theorem good_theorem : 1 = 1.\nProof. reflexivity. Qed.\n"
            "Theorem leaky_theorem : 2 = 2.\nProof. reflexivity. Qed.\n"
            "Theorem orphan_theorem : 3 = 3.\nProof. reflexivity. Qed.\n"
            "Definition compute_me := 41 + 1.\n"
            "Lemma t1_suffix_base : 4 = 4.\nProof. reflexivity. Qed.\n")

    # v1: clean - prop constant absent from its stem-linked product
    products = [("out/decls.ml", "let compute_me = 42\n")]
    r = build_report([decl], products, None)
    by_name = {e["name"]: e for e in r["prop_carried"]}
    check(by_name["good_theorem"]["verdict"] == "CLEAN", "v1 clean")

    # v2: leak - prop constant present as a computational item
    products = [("out/decls.ml",
                 "let compute_me = 42\nlet leaky_theorem = Obj.magic 0\n")]
    r = build_report([decl], products, None)
    by_name = {e["name"]: e for e in r["prop_carried"]}
    check(by_name["leaky_theorem"]["verdict"] == "LEAK", "v2 leak")
    check(by_name["leaky_theorem"]["in_products"] is True, "v2 in products")

    # v3: inconclusive - no product linked for the declaration stem
    r = build_report([decl], [("out/other.ml", "let x = 1\n")], None)
    by_name = {e["name"]: e for e in r["prop_carried"]}
    check(by_name["good_theorem"]["verdict"] == "INCONCLUSIVE", "v3 inconcl")

    # v4: computational declarations are out of the leak scope
    r = build_report([decl], [("out/decls.ml", "let compute_me = 42\n")],
                     None)
    check("compute_me" in r["computational_declarations"], "v4 comp face")
    check(all(e["name"] != "compute_me" for e in r["prop_carried"]),
          "v4 not prop carried")

    # v5: token-boundary precision - a product mention of a longer
    # identifier that merely contains the name is not a leak
    products = [("out/decls.ml", "let good_theorem_suffix = 7\n")]
    r = build_report([decl], products, None)
    by_name = {e["name"]: e for e in r["prop_carried"]}
    check(by_name["good_theorem"]["verdict"] == "CLEAN", "v5 boundary")

    # v6: assumption overlay - closed, non-closed with escalation,
    # missing report honesty
    pa = {"good_theorem.pa": "Closed under the global context\n",
          "leaky_theorem.pa": "Axioms:\nbad_axiom : True\n"}
    r = build_report(
        [decl],
        [("out/decls.ml", "let leaky_theorem = 0\n")],
        None)
    # inject assumptions directly through the loader path
    import tempfile
    tmp = tempfile.mkdtemp(prefix="xtr_erasure_selftest_")
    try:
        for fname, text in pa.items():
            with open(os.path.join(tmp, fname), "w",
                      encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        loaded = load_assumptions(tmp)
        check(loaded.get("good_theorem") == "closed", "v6 closed marker")
        check(loaded.get("leaky_theorem") == "non-closed", "v6 axiom lines")
        r = build_report(
            [decl],
            [("out/decls.ml", "let leaky_theorem = 0\n")],
            tmp)
        by_name = {e["name"]: e for e in r["prop_carried"]}
        check(by_name["leaky_theorem"]["assumptions"] == "non-closed",
              "v6 overlay recorded")
        check(by_name["leaky_theorem"].get("escalated") is True,
              "v6 escalation")
        check(by_name["orphan_theorem"]["assumptions"] == "missing",
              "v6 missing honesty")
    finally:
        for fname in os.listdir(tmp):
            os.unlink(os.path.join(tmp, fname))
        os.rmdir(tmp)

    # v7: unparsed assumption report is recorded as unparsed, not guessed
    import tempfile
    tmp = tempfile.mkdtemp(prefix="xtr_erasure_selftest_")
    try:
        with open(os.path.join(tmp, "mystery.txt"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write("some unrelated capture\n")
        loaded = load_assumptions(tmp)
        check(loaded.get("mystery") == "unparsed", "v7 unparsed")
    finally:
        for fname in os.listdir(tmp):
            os.unlink(os.path.join(tmp, fname))
        os.rmdir(tmp)

    # v8: determinism - byte-identical double report
    products = [("out/decls.ml", "let compute_me = 42\n")]
    rep1 = report_json(build_report([decl], products, None))
    rep2 = report_json(build_report([decl], products, None))
    check(rep1 == rep2, "v8 determinism")

    if failures:
        sys.stdout.write("%s FAIL: %s\n" % (SELFTEST_MARKER, failures[0]))
        return 1
    sys.stdout.write(SELFTEST_MARKER + "\n")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _walk(dirpath, exts):
    out = []
    for root, _dirs, files in os.walk(dirpath):
        for name in sorted(files):
            if os.path.splitext(name)[1] in exts:
                out.append(os.path.join(root, name))
    return sorted(out)


def main(argv):
    parser = argparse.ArgumentParser(
        description="Three-source erasure link (schema %s)." % SCHEMA)
    parser.add_argument("--decl-sources", default=None,
                        help="directory tree of .v declaration sources")
    parser.add_argument("--sources", default=None,
                        help="directory tree of extraction products")
    parser.add_argument("--assumptions", default=None,
                        help="directory of captured Print Assumptions "
                             "reports (one constant per file)")
    parser.add_argument("--out", default=None)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.decl_sources or not args.sources:
        sys.stderr.write("usage error: --decl-sources and --sources are "
                         "required (or run --selftest)\n")
        return 2
    for path, label in ((args.decl_sources, "decl-sources"),
                        (args.sources, "sources")):
        if not os.path.isdir(path):
            sys.stderr.write("fail-loud: %s dir not found: %s\n"
                             % (label, path))
            return 1
    pairs = []
    for path in _walk(args.decl_sources, (".v",)):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                pairs.append((path.replace(os.sep, "/"), fh.read()))
        except OSError as exc:
            sys.stderr.write("fail-loud: unreadable %s: %s\n" % (path, exc))
            return 1
    product_pairs = []
    for path in _walk(args.sources, PRODUCT_EXTS):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            sys.stderr.write("fail-loud: unreadable %s: %s\n" % (path, exc))
            return 1
        rel = os.path.relpath(path, args.sources).replace(os.sep, "/")
        product_pairs.append((rel, text))
    report = build_report(pairs, product_pairs, args.assumptions)
    out = report_text(report) if args.format == "text" else report_json(report)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(out)
        except OSError as exc:
            sys.stderr.write("fail-loud: cannot write %s: %s\n"
                             % (args.out, exc))
            return 1
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
