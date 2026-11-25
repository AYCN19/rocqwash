#!/usr/bin/env python3
"""xtr_extract_census.py - read-only census of Rocq extraction vernacular.

Purpose.  The extraction face (Recursive Extraction, Separate Extraction,
Extract Constant/Inductive/Table, Extraction Inline/Language/Blacklist)
is the boundary where proven statements become program text.  This tool
inventories every extraction point (file, line, command, targets, payload)
as deterministic JSON with schema rocqwash.xtr-census/1, for downstream
audit tools (xtr_magic_audit, xtr_erasure_link).  Comments are masked by
a nested-aware local scanner (hidden statements are never counted); an
unknown extraction-face statement lands in an explicit unparsed bucket.

Interface.
  python -B tools/xtr_extract_census.py --roots DIR[,DIR...] [--out FILE]
      [--format json|text] [--selftest]

Exit-codes.  0 success; 1 fail-loud (unreadable input, selftest failure);
2 usage error.

Safety.  Zero network, stdlib only, read-only over input trees; the only
write is the caller-named --out file.  Determinism: no wall clock, no
random, sorted keys, byte-identical output for equal inputs.  Honesty:
is_safe_primitive is a curated textual allowlist match, not a semantic
claim; report-only.  --selftest prints XTR-EXTRACT-CENSUS-SELFTEST PASS.

Evidence.  Ten selftest vectors plus tests/t_xtr_meta.py (five vector
groups) and double-run live fixture determinism, green at integration.

Dependencies.  Python 3 standard library only.
"""
import argparse
import json
import os
import re
import sys

SCHEMA = "rocqwash.xtr-census/1"
GENERATED_BY = "tools/xtr_extract_census.py"
SELFTEST_MARKER = "XTR-EXTRACT-CENSUS-SELFTEST PASS"
DEFAULT_LANGUAGE = "ocaml"

_QUALID = r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*"
_IDENT = r"[A-Za-z_][A-Za-z0-9_']*"
_QUALIDS = _QUALID + r"(?:\s+" + _QUALID + r")*"
_IDENTS = _IDENT + r"(?:\s+" + _IDENT + r")*"
_STRING = r'"(?:[^"\\]|\\.)*"'

_LANG_RE = re.compile(
    r"^\s*Extraction\s+Language\s+(Ocaml|Haskell|JSON|Json)\s*\.\s*$")
_BLACKLIST_RE = re.compile(
    r"^\s*Extraction\s+Blacklist\s+(" + _IDENTS + r")\s*\.\s*$")
_EXTR_LIB_RE = re.compile(
    r"^\s*Extraction\s+Library\s+(" + _IDENT + r")\s*\.\s*$")
_EXTR_INLINE_RE = re.compile(
    r"^\s*Extraction\s+(NoInline|Inline)\s+(" + _QUALIDS + r")\s*\.\s*$")
_EXTR_FILE_RE = re.compile(
    r"^\s*Extraction\s+(" + _STRING + r")\s+(" + _QUALIDS + r")\s*\.\s*$")
_REC_FILE_RE = re.compile(
    r"^\s*Recursive\s+Extraction\s+(" + _STRING + r")\s+(" + _QUALIDS +
    r")\s*\.\s*$")
_SEP_FILE_RE = re.compile(
    r"^\s*Separate\s+Extraction\s+(" + _STRING + r")\s+(" + _QUALIDS +
    r")\s*\.\s*$")
_EXTR_PLAIN_RE = re.compile(
    r"^\s*Extraction\s+(" + _QUALIDS + r")\s*\.\s*$")
_REC_LIB_RE = re.compile(
    r"^\s*Recursive\s+Extraction\s+Library\s+(" + _IDENT + r")\s*\.\s*$")
_REC_RE = re.compile(
    r"^\s*Recursive\s+Extraction\s+(" + _QUALIDS + r")\s*\.\s*$")
_SEP_RE = re.compile(
    r"^\s*Separate\s+Extraction\s+(" + _QUALIDS + r")\s*\.\s*$")
_EXTRACT_C_RE = re.compile(
    r"^\s*Extract\s+(Inlined\s+)?Constant\s+(" + _QUALID + r")\s*=>\s*(" +
    _STRING + r")\s*\.\s*$")
_EXTRACT_I_RE = re.compile(
    r"^\s*Extract\s+(Inlined\s+)?Inductive\s+(" + _QUALID + r")\s*=>\s*(" +
    _STRING + r")\s*(\[\s*.*?\s*\])?\s*\.\s*$")
_EXTRACT_T_RE = re.compile(
    r"^\s*Extract\s+Table\s+(" + _QUALID + r")\s*=>\s*(" + _STRING +
    r")\s*\.\s*$")

_STATEMENT_START_RE = re.compile(
    r"^\s*(?:Extraction|Extract|Recursive\s+Extraction|Separate\s+Extraction)\b")
_UNPARSE_BUCKET_CAP = 40

# Conservative curated allowlist: payload texts whose OCaml translation is
# a well-known pure primitive.  Membership is a textual judgment, not a
# semantic proof; anything outside the set is reported unsafe-by-default.
SAFE_PRIMITIVES = {
    "id": "identity",
    "not": "logical",
    "negb": "logical",
    "succ": "arithmetic",
    "pred": "arithmetic",
    "(+)": "arithmetic",
    "(-)": "arithmetic",
    "( * )": "arithmetic",
    "(*)": "arithmetic",
    "( / )": "arithmetic",
    "(/)": "arithmetic",
    "(mod)": "arithmetic",
    "( mod )": "arithmetic",
    "(land)": "arithmetic",
    "(lor)": "arithmetic",
    "(lxor)": "arithmetic",
    "(=)": "comparison",
    "(<)": "comparison",
    "(>)": "comparison",
    "(<=)": "comparison",
    "(>=)": "comparison",
    "(<>)": "comparison",
    "string_of_int": "conversion",
    "int_of_string_opt": "conversion",
    "Z.to_int": "conversion",
    "Z.of_int": "conversion",
    "N.to_int": "conversion",
    "N.of_int": "conversion",
}
_UNSAFE_PAYLOAD_TOKENS = (
    "Obj.magic", "unsafeCoerce", "assert false", "failwith",
    "Printf.", "print_", "ignore ", "ref ",
)
_OCAML_PAYLOAD_TOKENS = (
    "Obj.magic", "Stdlib.", "Pervasives.", "Printf.", "List.",
    "Char.", "String.", "Not_found", "invalid_arg",
)
_HASKELL_PAYLOAD_TOKENS = ("unsafeCoerce", "Data.", "Text.Printf")


# ---------------------------------------------------------------------------
# Comment masking (nested-aware, line preserving)
# ---------------------------------------------------------------------------

def mask_comment_spans(text):
    """Replace Rocq (* ... *) comment content with spaces, nested-aware.

    Newlines inside comments are kept so that line numbers of the masked
    text still match the original source byte for byte.
    """
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


def _logical_statements(masked_lines):
    """Yield (start_lineno, joined_text) for extraction-face statements.

    A line whose masked content starts an extraction command opens a
    logical statement; continuation lines are joined until one whose
    stripped content ends with a period.  A statement that never
    terminates within the cap is returned with an unterminated flag via
    the plain joined text (the caller reports it as unparsed).
    """
    statements = []
    i = 0
    n = len(masked_lines)
    while i < n:
        if not _STATEMENT_START_RE.match(masked_lines[i]):
            i += 1
            continue
        start = i + 1
        joined = masked_lines[i].strip()
        j = i
        closed = joined.endswith(".")
        while not closed and j - i + 1 < _UNPARSE_BUCKET_CAP and j + 1 < n:
            j += 1
            joined = joined + " " + masked_lines[j].strip()
            closed = masked_lines[j].strip().endswith(".")
        statements.append((start, joined))
        i = j + 1
    return statements


def _unquote(payload):
    """Strip the surrounding double quotes of a payload string."""
    if payload is None:
        return None
    if len(payload) >= 2 and payload[0] == '"' and payload[-1] == '"':
        return payload[1:-1]
    return payload


def _payload_hint(unquoted):
    if unquoted is None:
        return "none"
    if any(tok in unquoted for tok in _HASKELL_PAYLOAD_TOKENS):
        return "haskell-shape"
    if any(tok in unquoted for tok in _OCAML_PAYLOAD_TOKENS):
        return "ocaml-shape"
    return "none"


def classify_payload(unquoted):
    """Return (is_safe_primitive, safe_class) for an unquoted payload."""
    if unquoted is None:
        return (False, "absent")
    if any(tok in unquoted for tok in _UNSAFE_PAYLOAD_TOKENS):
        return (False, "unsafe-shape")
    cls = SAFE_PRIMITIVES.get(unquoted)
    if cls is not None:
        return (True, cls)
    return (False, "unclassified")


def _split_qualids(text):
    return [tok for tok in text.split() if tok]


def analyze_source(text, filename):
    """Census one .v source.  Returns the per-file report fragment."""
    masked = mask_comment_spans(text)
    lines = masked.split("\n")
    points = []
    lang_decls = []
    blacklist_decls = []
    unparsed = []
    language = DEFAULT_LANGUAGE
    for lineno, stmt in _logical_statements(lines):
        point_base = {
            "file": filename,
            "line": lineno,
        }
        m = _LANG_RE.match(stmt)
        if m:
            language = m.group(1).lower()
            lang_decls.append(dict(point_base, language=language))
            continue
        m = _BLACKLIST_RE.match(stmt)
        if m:
            blacklist_decls.append(
                dict(point_base, names=_split_qualids(m.group(1))))
            continue
        m = _REC_LIB_RE.match(stmt)
        if m:
            points.append(dict(point_base, command="Recursive Extraction Library",
                               targets=[m.group(1)], target_payload=None,
                               language=language, payload_hint="none",
                               **dict(zip(("is_safe_primitive", "safe_class"),
                                          classify_payload(None)))))
            continue
        m = _EXTR_LIB_RE.match(stmt)
        if m:
            points.append(dict(point_base, command="Extraction Library",
                               targets=[m.group(1)], target_payload=None,
                               language=language, payload_hint="none",
                               **dict(zip(("is_safe_primitive", "safe_class"),
                                          classify_payload(None)))))
            continue
        m = _EXTR_INLINE_RE.match(stmt)
        if m:
            points.append(dict(
                point_base,
                command="Extraction " + m.group(1),
                targets=_split_qualids(m.group(2)), target_payload=None,
                language=language, payload_hint="none",
                **dict(zip(("is_safe_primitive", "safe_class"),
                           classify_payload(None)))))
            continue
        m = _REC_RE.match(stmt)
        if m:
            points.append(dict(point_base, command="Recursive Extraction",
                               targets=_split_qualids(m.group(1)),
                               target_payload=None, language=language,
                               payload_hint="none",
                               **dict(zip(("is_safe_primitive", "safe_class"),
                                          classify_payload(None)))))
            continue
        m = _SEP_RE.match(stmt)
        if m:
            points.append(dict(point_base, command="Separate Extraction",
                               targets=_split_qualids(m.group(1)),
                               target_payload=None, language=language,
                               payload_hint="none",
                               **dict(zip(("is_safe_primitive", "safe_class"),
                                          classify_payload(None)))))
            continue
        m = _EXTRACT_C_RE.match(stmt)
        if m:
            unq = _unquote(m.group(3))
            safe, cls = classify_payload(unq)
            points.append(dict(
                point_base,
                command="Extract Inlined Constant" if m.group(1)
                        else "Extract Constant",
                targets=[m.group(2)], target_payload=m.group(3),
                language=language, payload_hint=_payload_hint(unq),
                is_safe_primitive=safe, safe_class=cls))
            continue
        m = _EXTRACT_I_RE.match(stmt)
        if m:
            unq = _unquote(m.group(3))
            safe, cls = classify_payload(unq)
            points.append(dict(
                point_base,
                command="Extract Inlined Inductive" if m.group(1)
                        else "Extract Inductive",
                targets=[m.group(2)], target_payload=m.group(3),
                language=language, payload_hint=_payload_hint(unq),
                is_safe_primitive=safe, safe_class=cls))
            continue
        m = _EXTRACT_T_RE.match(stmt)
        if m:
            unq = _unquote(m.group(2))
            safe, cls = classify_payload(unq)
            points.append(dict(point_base, command="Extract Table",
                               targets=[m.group(1)], target_payload=m.group(2),
                               language=language, payload_hint=_payload_hint(unq),
                               is_safe_primitive=safe, safe_class=cls))
            continue
        m = _EXTR_FILE_RE.match(stmt)
        if m:
            points.append(dict(point_base, command="Extraction",
                               targets=_split_qualids(m.group(2)),
                               output_file=_unquote(m.group(1)),
                               target_payload=None, language=language,
                               payload_hint="none",
                               **dict(zip(("is_safe_primitive", "safe_class"),
                                          classify_payload(None)))))
            continue
        m = _REC_FILE_RE.match(stmt)
        if m:
            points.append(dict(point_base, command="Recursive Extraction",
                               targets=_split_qualids(m.group(2)),
                               output_file=_unquote(m.group(1)),
                               target_payload=None, language=language,
                               payload_hint="none",
                               **dict(zip(("is_safe_primitive", "safe_class"),
                                          classify_payload(None)))))
            continue
        m = _SEP_FILE_RE.match(stmt)
        if m:
            points.append(dict(point_base, command="Separate Extraction",
                               targets=_split_qualids(m.group(2)),
                               output_file=_unquote(m.group(1)),
                               target_payload=None, language=language,
                               payload_hint="none",
                               **dict(zip(("is_safe_primitive", "safe_class"),
                                          classify_payload(None)))))
            continue
        m = _EXTR_PLAIN_RE.match(stmt)
        if m:
            points.append(dict(point_base, command="Extraction",
                               targets=_split_qualids(m.group(1)),
                               output_file=None, target_payload=None,
                               language=language, payload_hint="none",
                               **dict(zip(("is_safe_primitive", "safe_class"),
                                          classify_payload(None)))))
            continue
        unparsed.append(dict(point_base, text=stmt[:200]))
    for p in points:
        p.setdefault("output_file", None)
    return {
        "points": points,
        "language_declarations": lang_decls,
        "blacklist_decls": blacklist_decls,
        "unparsed": unparsed,
    }


def scan_tree(roots):
    """Walk the roots and return the sorted list of .v file paths."""
    vfiles = []
    for root in roots:
        if os.path.isfile(root):
            if root.endswith(".v"):
                vfiles.append(root)
            continue
        if not os.path.isdir(root):
            raise FileNotFoundError("root not found: %s" % root)
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                if name.endswith(".v"):
                    vfiles.append(os.path.join(dirpath, name))
    return sorted(vfiles)


def build_report(roots, source_reader):
    """Assemble the census document from (filename, text) pairs."""
    fragments = [analyze_source(text, name)
                 for name, text in source_reader]
    points = []
    lang_decls = []
    blacklist_decls = []
    unparsed = []
    for frag in fragments:
        points.extend(frag["points"])
        lang_decls.extend(frag["language_declarations"])
        blacklist_decls.extend(frag["blacklist_decls"])
        unparsed.extend(frag["unparsed"])
    points.sort(key=lambda p: (p["file"], p["line"], p["command"]))
    lang_decls.sort(key=lambda p: (p["file"], p["line"]))
    blacklist_decls.sort(key=lambda p: (p["file"], p["line"]))
    unparsed.sort(key=lambda p: (p["file"], p["line"]))
    counts_command = {}
    counts_file = {}
    for p in points:
        counts_command[p["command"]] = counts_command.get(p["command"], 0) + 1
        counts_file[p["file"]] = counts_file.get(p["file"], 0) + 1
    return {
        "schema": SCHEMA,
        "generated_by": GENERATED_BY,
        "roots": list(roots),
        "files_scanned": len(fragments),
        "extraction_points": points,
        "language_declarations": lang_decls,
        "blacklist_declarations": blacklist_decls,
        "unparsed_extraction_face": unparsed,
        "counts_by_command": dict(sorted(counts_command.items())),
        "counts_by_file": dict(sorted(counts_file.items())),
    }


def report_json(report):
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def report_text(report):
    lines = []
    lines.append("xtr-census %s" % SCHEMA)
    lines.append("roots: %s" % ", ".join(report["roots"]))
    lines.append("files_scanned: %d" % report["files_scanned"])
    lines.append("extraction points: %d" % len(report["extraction_points"]))
    for p in report["extraction_points"]:
        payload = p.get("target_payload") or "-"
        lines.append("  %s:%d %s targets=%s payload=%s lang=%s safe=%s" % (
            p["file"], p["line"], p["command"], ",".join(p["targets"]),
            payload, p["language"], str(p["is_safe_primitive"]).lower()))
    if report["unparsed_extraction_face"]:
        lines.append("unparsed extraction-face statements: %d"
                     % len(report["unparsed_extraction_face"]))
        for u in report["unparsed_extraction_face"]:
            lines.append("  %s:%d %s" % (u["file"], u["line"], u["text"]))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Selftest (in-process fixtures, no disk reads)
# ---------------------------------------------------------------------------

def _selftest():
    failures = []

    def check(cond, label):
        if not cond:
            failures.append(label)

    # v1: Extract Constant payload capture and safe-primitive class
    r = analyze_source('Extract Constant Z.add => "(+)".\n', "f1.v")
    check(len(r["points"]) == 1, "v1 point count")
    p = r["points"][0]
    check(p["command"] == "Extract Constant", "v1 command")
    check(p["targets"] == ["Z.add"], "v1 targets")
    check(p["target_payload"] == '"(+)"', "v1 payload")
    check(p["is_safe_primitive"] is True and p["safe_class"] == "arithmetic",
          "v1 safe class")
    check(p["line"] == 1, "v1 line")

    # v2: Recursive and Separate Extraction target lists
    r = analyze_source(
        "Recursive Extraction add mul.\nSeparate Extraction f.\n", "f2.v")
    check(len(r["points"]) == 2, "v2 point count")
    check(r["points"][0]["command"] == "Recursive Extraction", "v2 command a")
    check(r["points"][0]["targets"] == ["add", "mul"], "v2 targets a")
    check(r["points"][1]["command"] == "Separate Extraction", "v2 command b")

    # v3: commented-out extraction is never counted (negative control)
    r = analyze_source("(* Extraction fake. *)\nExtraction real.\n", "f3.v")
    check(len(r["points"]) == 1, "v3 negative control count")
    check(r["points"][0]["targets"] == ["real"], "v3 negative control target")

    # v4: Extraction Language state propagates to later points
    r = analyze_source(
        'Extraction Language Haskell.\nExtract Constant f => "id".\n', "f4.v")
    check(len(r["language_declarations"]) == 1, "v4 lang decl")
    check(r["points"][0]["language"] == "haskell", "v4 language state")

    # v5: nested comments mask fake statements
    r = analyze_source(
        "(* outer (* Extraction fake. *) still comment *)\n"
        "Extraction realone.\n", "f5.v")
    check(len(r["points"]) == 1, "v5 nested comment count")
    check(r["points"][0]["targets"] == ["realone"], "v5 nested target")

    # v6: unsafe payload flagged, ocaml shape hinted
    r = analyze_source('Extract Constant bad => "Obj.magic 0".\n', "f6.v")
    p = r["points"][0]
    check(p["is_safe_primitive"] is False, "v6 unsafe flag")
    check(p["safe_class"] == "unsafe-shape", "v6 unsafe class")
    check(p["payload_hint"] == "ocaml-shape", "v6 hint")

    # v7: unknown Extract-family form lands in the unparsed bucket; a
    # plain Extraction with several names parses as a target list by
    # design (textually indistinguishable from an unknown subcommand)
    r = analyze_source('Extract Foo bar => "x".\n', "f7.v")
    check(len(r["points"]) == 0, "v7 no point")
    check(len(r["unparsed"]) == 1, "v7 unparsed bucket")
    check(r["unparsed"][0]["line"] == 1, "v7 unparsed line")
    r = analyze_source("Extraction Testwise foo.\n", "f7b.v")
    check(len(r["points"]) == 1 and r["points"][0]["targets"] ==
          ["Testwise", "foo"], "v7b plain parse by design")

    # v8: empty source and multi-line Extract Inductive with variants
    r = analyze_source("", "f8a.v")
    check(len(r["points"]) == 0, "v8 empty source")
    r = analyze_source(
        'Extract Inductive sumbool => "bool"\n'
        '  [ left -> "true" | right -> "false" ].\n', "f8b.v")
    check(len(r["points"]) == 1, "v8 multiline point")
    p = r["points"][0]
    check(p["command"] == "Extract Inductive", "v8 multiline command")
    check(p["targets"] == ["sumbool"], "v8 multiline target")
    check(p["line"] == 1, "v8 multiline start line")

    # v9: determinism - same input, byte-identical report
    srcs = [("a.v", 'Extract Constant Z.of_int => "Z.of_int".\n'),
            ("b.v", "Separate Extraction g h.\n")]
    rep1 = report_json(build_report(["r"], srcs))
    rep2 = report_json(build_report(["r"], srcs))
    check(rep1 == rep2, "v9 determinism")

    # v10: Extraction Inline vs plain Extraction ordering
    r = analyze_source("Extraction Inline helper.\nExtraction user.\n", "f10.v")
    check(len(r["points"]) == 2, "v10 two points")
    check(r["points"][0]["command"] == "Extraction Inline", "v10 inline first")
    check(r["points"][1]["command"] == "Extraction", "v10 plain second")

    # v11 (XD1): quoted-output-path forms capture output_file
    r = analyze_source('Extraction "out/mod.ml" add mul.\n', "f11.v")
    check(len(r["points"]) == 1, "v11 one point")
    p = r["points"][0]
    check(p["command"] == "Extraction", "v11 command")
    check(p["output_file"] == "out/mod.ml", "v11 output file")
    check(p["targets"] == ["add", "mul"], "v11 targets")
    r = analyze_source('Recursive Extraction "rec_out.ml" f g.\n', "f11b.v")
    p = r["points"][0]
    check(p["command"] == "Recursive Extraction" and
          p["output_file"] == "rec_out.ml" and
          p["targets"] == ["f", "g"], "v11 recursive file form")
    r = analyze_source('Separate Extraction "sep_dir" h.\n', "f11c.v")
    p = r["points"][0]
    check(p["command"] == "Separate Extraction" and
          p["output_file"] == "sep_dir", "v11 separate dir form")

    # v12 (XD1): plain forms still carry output_file None (uniform shape)
    r = analyze_source("Extraction plain.\n", "f12.v")
    check(r["points"][0]["output_file"] is None, "v12 uniform shape")

    # v13 (XD1): commented quoted form is never counted
    r = analyze_source('(* Extraction "fake.ml" nope. *)\n', "f13.v")
    check(len(r["points"]) == 0, "v13 comment masked")

    if failures:
        sys.stdout.write("%s FAIL: %s\n" % (SELFTEST_MARKER, failures[0]))
        return 1
    sys.stdout.write(SELFTEST_MARKER + "\n")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv):
    parser = argparse.ArgumentParser(
        description="Read-only census of Rocq extraction vernacular "
                    "(schema %s)." % SCHEMA)
    parser.add_argument("--roots", default=None,
                        help="comma-separated directories or .v files")
    parser.add_argument("--out", default=None,
                        help="write the JSON report to this file")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.roots:
        sys.stderr.write("usage error: --roots is required "
                         "(or run --selftest)\n")
        return 2
    roots = [r for r in args.roots.split(",") if r]
    try:
        vfiles = scan_tree(roots)
    except FileNotFoundError as exc:
        sys.stderr.write("fail-loud: %s\n" % exc)
        return 1
    pairs = []
    for path in vfiles:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            sys.stderr.write("fail-loud: unreadable %s: %s\n" % (path, exc))
            return 1
        pairs.append((path.replace(os.sep, "/"), text))
    report = build_report(roots, pairs)
    if args.format == "text":
        out = report_text(report)
    else:
        out = report_json(report)
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
