#!/usr/bin/env python3
"""xtr_magic_audit.py - audit Obj.magic / unsafeCoerce density in
extraction products against the xtr-census declaration face.

Purpose.  Rocq extraction turns proven statements into program text,
and some of that text carries escape hatches (Obj.magic in OCaml
products, unsafeCoerce in Haskell products), erasure dummies
(`__`-prefixed identifiers) and impossible-case markers (assert false,
failwith).  This tool scans extraction products (.ml/.mli/.hs), counts
the battery per file, classifies each occurrence by line context with a
red bias, and cross-checks the counts against a rocqwash.xtr-census/1
document whose payloads carry no unsafe token (a product that
nevertheless contains magic is a MISMATCH).  Schema rocqwash.xtr-magic-audit/1.

Interface.
  python -B tools/xtr_magic_audit.py --sources DIR [--census FILE] [--out FILE] [--format json|text] [--selftest]

Exit-codes.  0 success; 1 fail-loud (unreadable input, wrong census
schema, selftest failure); 2 usage error.

Safety.  Zero network, stdlib only, read-only over input trees; the only
write is the caller-named --out file.  Determinism: sorted keys, no wall
clock; byte-identical output for equal inputs.  Honesty: the occurrence
classes are textual heuristics with a red bias, not semantic judgments;
report-only.

Evidence.  Nine selftest vectors including the declared-safe but
actually-magic negative control, plus double-run determinism, green.

Dependencies.  Python 3 standard library only.
"""
import argparse
import json
import os
import re
import sys

SCHEMA = "rocqwash.xtr-magic-audit/1"
GENERATED_BY = "tools/xtr_magic_audit.py"
SELFTEST_MARKER = "XTR-MAGIC-AUDIT-SELFTEST PASS"
CENSUS_SCHEMA = "rocqwash.xtr-census/1"
PRODUCT_EXTS = (".ml", ".mli", ".hs")

_OCAML_TOKENS = ("Obj.magic", "unsafeCoerce")
_HASKELL_TOKENS = ("unsafeCoerce", "GHC.Magic", "unsafeDupablePerformIO")
_COMMON_TOKENS = ("assert false", "failwith")

_INHERENT_MARKERS = (
    "Obj.magic 0", "Obj.magic ()", "(fun x -> x)", "Obj.repr", "__",
)
_ANOMALOUS_MARKERS = ("assert false", "failwith")

_DUMMY_RE = re.compile(r"\b__[A-Za-z0-9_']*\b")


def mask_comments(text, open_tok, close_tok):
    """Blank out nested comment spans, preserving newlines."""
    out = []
    i = 0
    depth = 0
    n = len(text)
    while i < n:
        if text.startswith(open_tok, i):
            depth += 1
            out.append(" " * len(open_tok))
            i += len(open_tok)
        elif depth > 0 and text.startswith(close_tok, i):
            depth -= 1
            out.append(" " * len(close_tok))
            i += len(close_tok)
        elif depth > 0:
            out.append("\n" if text[i] == "\n" else " ")
            i += 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def classify_line(line):
    """Return the occurrence class for one product line.

    The anomalous markers win on a mixed line: when a line carries both
    an impossible-case marker and an inherent marker, the classification
    is biased to anomalous (red) rather than excused.
    """
    if any(m in line for m in _ANOMALOUS_MARKERS):
        return "anomalous"
    if any(m in line for m in _INHERENT_MARKERS):
        return "inherent"
    return "unclassified"


def scan_product(text, ext):
    """Count the magic battery in one product file's masked text."""
    if ext == ".hs":
        language = "haskell"
        masked = mask_comments(text, "{-", "-}")
        tokens = _HASKELL_TOKENS + _COMMON_TOKENS
    else:
        language = "ocaml"
        masked = mask_comments(text, "(*", "*)")
        tokens = _OCAML_TOKENS + _COMMON_TOKENS
    lines = masked.split("\n")
    occurrences = []
    dummy_lines = []
    for idx, line in enumerate(lines, start=1):
        for tok in tokens:
            start = 0
            while True:
                pos = line.find(tok, start)
                if pos < 0:
                    break
                occurrences.append({
                    "line": idx,
                    "kind": tok,
                    "class": classify_line(line),
                    "text": line.strip()[:120],
                })
                start = pos + len(tok)
        for _m in _DUMMY_RE.finditer(line):
            dummy_lines.append(idx)
    counts = {}
    for occ in occurrences:
        counts[occ["kind"]] = counts.get(occ["kind"], 0) + 1
    return {
        "language": language,
        "occurrences": occurrences,
        "dummy_ident_count": len(dummy_lines),
        "dummy_lines": sorted(set(dummy_lines)),
        "counts_by_kind": dict(sorted(counts.items())),
    }


def stem(name):
    """File stem without extension, case-folded for linking."""
    return os.path.splitext(os.path.basename(name))[0].lower()


def census_claims(census_doc):
    """Map .v file paths to their declared claim from a census doc.

    claim is 'magic-free' when no extraction payload of the file carries
    an unsafe shape, 'declared-unsafe' when at least one payload does.
    """
    claims = {}
    if census_doc is None:
        return claims
    for point in census_doc.get("extraction_points", []):
        path = point.get("file")
        if path is None:
            continue
        unsafe = point.get("safe_class") == "unsafe-shape"
        prev = claims.get(path)
        if prev is None:
            claims[path] = "declared-unsafe" if unsafe else "magic-free"
        elif unsafe and prev != "declared-unsafe":
            claims[path] = "declared-unsafe"
    return claims


def build_report(sources_root, pairs, census_doc):
    """Assemble the audit document from (relpath, text, ext) triples."""
    claims = census_claims(census_doc)
    claims_by_stem = {}
    for path, claim in claims.items():
        claims_by_stem[stem(path)] = {"claim": claim, "census_file": path}
    files = []
    for relpath, text, ext in pairs:
        face = scan_product(text, ext)
        total_magic = sum(face["counts_by_kind"].get(k, 0)
                          for k in ("Obj.magic", "unsafeCoerce", "GHC.Magic",
                                    "unsafeDupablePerformIO"))
        link = claims_by_stem.get(stem(relpath))
        if link is None:
            claim, verdict = "none", "NO_CLAIM"
        else:
            claim = link["claim"]
            if claim == "magic-free":
                verdict = "MISMATCH" if total_magic > 0 else "MATCH"
            else:
                verdict = "NO_CLAIM"
        size = len(text.encode("utf-8"))
        density = round(total_magic / (size / 1024.0), 3) if size else 0.0
        files.append({
            "file": relpath,
            "language": face["language"],
            "bytes": size,
            "counts_by_kind": face["counts_by_kind"],
            "total_magic": total_magic,
            "dummy_ident_count": face["dummy_ident_count"],
            "dummy_lines": face["dummy_lines"],
            "density_per_kb": density,
            "occurrences": face["occurrences"],
            "claim": claim,
            "verdict": verdict,
        })
    files.sort(key=lambda f: f["file"])
    verdict_by_file = {f["file"]: f["verdict"] for f in files}
    counts_by_kind = {}
    for f in files:
        for k, v in f["counts_by_kind"].items():
            counts_by_kind[k] = counts_by_kind.get(k, 0) + v
    return {
        "schema": SCHEMA,
        "generated_by": GENERATED_BY,
        "sources_root": sources_root,
        "census": None if census_doc is None
                  else census_doc.get("schema"),
        "files": files,
        "verdict_by_file": dict(sorted(verdict_by_file.items())),
        "counts_by_kind": dict(sorted(counts_by_kind.items())),
        "summary": {
            "files": len(files),
            "total_magic": sum(f["total_magic"] for f in files),
            "total_dummy": sum(f["dummy_ident_count"] for f in files),
            "mismatch_files": sum(1 for f in files
                                  if f["verdict"] == "MISMATCH"),
            "match_files": sum(1 for f in files if f["verdict"] == "MATCH"),
            "no_claim_files": sum(1 for f in files
                                  if f["verdict"] == "NO_CLAIM"),
        },
    }


def report_json(report):
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def report_text(report):
    lines = []
    lines.append("xtr-magic-audit %s" % SCHEMA)
    lines.append("sources_root: %s" % report["sources_root"])
    s = report["summary"]
    lines.append("files=%d total_magic=%d total_dummy=%d mismatch=%d "
                 "match=%d no_claim=%d" % (
                     s["files"], s["total_magic"], s["total_dummy"],
                     s["mismatch_files"], s["match_files"],
                     s["no_claim_files"]))
    for f in report["files"]:
        lines.append("  %s [%s] magic=%d dummy=%d claim=%s verdict=%s" % (
            f["file"], f["language"], f["total_magic"],
            f["dummy_ident_count"], f["claim"], f["verdict"]))
        for occ in f["occurrences"][:10]:
            lines.append("    L%d %s (%s): %s" % (
                occ["line"], occ["kind"], occ["class"], occ["text"]))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Selftest (in-process fixtures, no disk reads)
# ---------------------------------------------------------------------------

def _selftest():
    failures = []

    def check(cond, label):
        if not cond:
            failures.append(label)

    def census_doc(points):
        return {"schema": CENSUS_SCHEMA, "extraction_points": points}

    # v1: battery counts on an OCaml product
    src = ("let f x =\n"
           "  match x with\n"
           "  | Some y -> y + 1\n"
           "  | None -> Obj.magic 0\n\n"
           "let g = Obj.magic (fun x -> x) + Obj.magic 0\n")
    face = scan_product(src, ".ml")
    check(face["counts_by_kind"].get("Obj.magic") == 3, "v1 magic count")
    check(face["counts_by_kind"].get("assert false", 0) == 0, "v1 no assert")
    check(face["language"] == "ocaml", "v1 language")

    # v2: impossible-case markers counted
    src2 = "let h = failwith \"abs\"\nlet k = assert false\n"
    face2 = scan_product(src2, ".ml")
    check(face2["counts_by_kind"].get("failwith") == 1, "v2 failwith")
    check(face2["counts_by_kind"].get("assert false") == 1, "v2 assert")

    # v3: comment masking - magic inside a comment is not counted
    src3 = "(* Obj.magic fake *)\nlet ok = 1\n"
    face3 = scan_product(src3, ".ml")
    check(face3["counts_by_kind"] == {}, "v3 comment masked")

    # v4: occurrence classification with red bias
    src4 = ("let a = Obj.magic 0\n"
            "let b = Obj.magic (assert false)\n"
            "let c = Obj.magic q\n")
    face4 = scan_product(src4, ".ml")
    cls = {o["line"]: o["class"] for o in face4["occurrences"]}
    check(cls[1] == "inherent", "v4 inherent class")
    check(cls[2] == "anomalous", "v4 red bias on mixed line")
    check(cls[3] == "unclassified", "v4 unclassified")

    # v5: negative control - census claims magic-free, product has magic
    cen = census_doc([
        {"file": "src/Safe.v", "line": 1, "command": "Extract Constant",
         "targets": ["add"], "safe_class": "arithmetic",
         "is_safe_primitive": True, "target_payload": '"(+)"'},
    ])
    report = build_report("out", [("out/safe.ml", "let add = Obj.magic 0\n",
                                   ".ml")], cen)
    check(report["files"][0]["verdict"] == "MISMATCH", "v5 mismatch verdict")
    check(report["summary"]["mismatch_files"] == 1, "v5 mismatch summary")

    # v6: MATCH case - census magic-free, product clean
    report = build_report("out", [("out/safe.ml", "let add = fun x -> x\n",
                                   ".ml")], cen)
    check(report["files"][0]["verdict"] == "MATCH", "v6 match verdict")

    # v7: declared-unsafe payload yields NO_CLAIM (nothing to contradict)
    cen2 = census_doc([
        {"file": "src/Bad.v", "line": 1, "command": "Extract Constant",
         "targets": ["bad"], "safe_class": "unsafe-shape",
         "is_safe_primitive": False, "target_payload": '"Obj.magic 0"'},
    ])
    report = build_report("out", [("out/bad.ml", "let bad = Obj.magic 0\n",
                                   ".ml")], cen2)
    check(report["files"][0]["verdict"] == "NO_CLAIM", "v7 no claim")
    check(report["files"][0]["claim"] == "declared-unsafe", "v7 claim tag")

    # v8: stem linking is path-independent and case-folded, and a
    # non-matching stem stays NO_CLAIM
    report = build_report("out", [
        ("deep/nested/dir/SAFE.ml", "let add = Obj.magic 0\n", ".ml"),
        ("out/other.ml", "let x = Obj.magic 0\n", ".ml"),
    ], cen)
    by_file = {f["file"]: f for f in report["files"]}
    check(by_file["deep/nested/dir/SAFE.ml"]["verdict"] == "MISMATCH",
          "v8 stem link")
    check(by_file["out/other.ml"]["verdict"] == "NO_CLAIM", "v8 no link")

    # v9: haskell products use the haskell battery; determinism of the
    # full report; dummy identifiers counted
    hs = "f x = unsafeCoerce x\n__dummy x = x\n"
    face9 = scan_product(hs, ".hs")
    check(face9["counts_by_kind"].get("unsafeCoerce") == 1, "v9 haskell")
    check(face9["language"] == "haskell", "v9 language")
    check(face9["dummy_ident_count"] == 1, "v9 dummy counted")
    pairs = [("out/a.ml", "let u = Obj.magic 0\n", ".ml"),
             ("out/b.hs", "g = unsafeCoerce\n", ".hs")]
    rep1 = report_json(build_report("out", pairs, cen))
    rep2 = report_json(build_report("out", pairs, cen))
    check(rep1 == rep2, "v9 determinism")

    if failures:
        sys.stdout.write("%s FAIL: %s\n" % (SELFTEST_MARKER, failures[0]))
        return 1
    sys.stdout.write(SELFTEST_MARKER + "\n")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _read_census(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        sys.stderr.write("fail-loud: cannot read census %s: %s\n"
                         % (path, exc))
        return None
    if doc.get("schema") != CENSUS_SCHEMA:
        sys.stderr.write("fail-loud: census schema %r is not %s\n"
                         % (doc.get("schema"), CENSUS_SCHEMA))
        return None
    return doc


def main(argv):
    parser = argparse.ArgumentParser(
        description="Obj.magic / unsafeCoerce audit of extraction products "
                    "against the xtr census (schema %s)." % SCHEMA)
    parser.add_argument("--sources", default=None,
                        help="directory of extraction products")
    parser.add_argument("--census", default=None,
                        help="rocqwash.xtr-census/1 JSON document")
    parser.add_argument("--out", default=None,
                        help="write the JSON report to this file")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.sources:
        sys.stderr.write("usage error: --sources is required "
                         "(or run --selftest)\n")
        return 2
    if not os.path.isdir(args.sources):
        sys.stderr.write("fail-loud: sources dir not found: %s\n"
                         % args.sources)
        return 1
    census_doc = None
    if args.census:
        census_doc = _read_census(args.census)
        if census_doc is None:
            return 1
    pairs = []
    for dirpath, _dirnames, filenames in os.walk(args.sources):
        for name in sorted(filenames):
            ext = os.path.splitext(name)[1]
            if ext not in PRODUCT_EXTS:
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, "r", encoding="utf-8",
                          errors="replace") as fh:
                    text = fh.read()
            except OSError as exc:
                sys.stderr.write("fail-loud: unreadable %s: %s\n"
                                 % (path, exc))
                return 1
            relpath = os.path.relpath(path, args.sources).replace(os.sep, "/")
            pairs.append((relpath, text, ext))
    pairs.sort(key=lambda p: p[0])
    report = build_report(args.sources, pairs, census_doc)
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
