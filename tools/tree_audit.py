#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tree_audit.py - read-only tree health audit over .lean/.v source trees.

Purpose.  One JSON-line census of a source tree: file/byte/line totals (lines
  and non-empty lines), declaration counts split into thm (theorem|lemma) and
  defFam (def|abbrev|structure|class|instance|inductive) with decls as their
  combined total, an unsound-feature sweep (sorry, sorryAx, axiom, opaque,
  native_decide, unsafe, implemented_by, extern, ofReduceBool), comment faces,
  per-directory and largest-file tables, and the import-root histogram.  Every
  top-level key but scan_face is {"value": N, "basis": "..."} so each number
  travels with its counting rule, and scan_face states what the scan covers
  and what it cannot see.  Counting is byte-literal and lowercase, calibrated
  one-to-one to the sandbox census_rh.py face (raw bytes, so comments and
  strings count too), so a same-tree cross-check is field-for-field equal; the
  root is scanned literally (no src/ descent) and .v counts sit beside .lean.
Interface.  python3 tools/tree_audit.py --root DIR [--json OUT] | --selftest;
  stdout carries one JSON line and --json writes the same payload to OUT.
  Fields: files, bytes, lines, nonEmptyLines, thm, defFam, decls, sorry,
  sorryAx, axiom, opaque, native_decide, unsafe, implemented_by, extern,
  ofReduceBool, commentLines, blockCommentFiles, perDir, largest10,
  zeroDeclFiles, importRoots, root, errors, errorCount, scan_face.  Shape:
  every field but scan_face is {"value": ..., "basis": ...}; perDir.value maps
  the first path segment to {files, decls, bytes}, largest10.value is
  [{"path","bytes"}], importRoots.value is a top-ten [[root,count]] list,
  errors.value is a capped string list; scan_face has exactly the four fields
  scanned, not_scanned, negative_finding, equivalents.
Dependencies.  Python 3 standard library only (argparse, json, os, re, shutil,
  sys, tempfile); the fast path reads each file once in binary and scans bytes
  with precompiled regexes: zero subprocess, zero network, zero imports of the
  scanned tree, zero tree writes.
Evidence.  --selftest builds a temporary fixture tree (.v and .lean files with
  hand-derived known counts covering the thm/defFam split and blank /
  whitespace-only lines), asserts every report field against those vectors,
  asserts the value/basis shape of every top-level key but scan_face and the
  four verbatim scan_face strings, the exit-code faces (green scan, empty
  tree, missing root rc=2) and the --json round trip; the Deicyde mirror
  cross-check against census_rh.py runs out of tree.
Exit-codes.  0 green (complete scan or green selftest); 1 red (any selftest
  vector fails, any file read fails, or the --json write fails); 2 usage
  (missing or non-directory --root, --selftest combined with scan flags,
  unknown flags).
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile

TOOL = "tree_audit"

# Detail carried below the five-field header budget (the norm_lint
# header-budget rule keeps the docstring to the five fields):
#
# Calibration.  Every pattern below is byte-identical to the census_rh.py
# oracle in attn/_alpoge_rh_audit_20261121/ (the Deicyde cross-check face):
# thm/deffam/axiom/opaque/unsafe/commentLine are line-anchored (re.M), sorry
# and sorryAx are word-bounded tokens, native_decide is a bare token,
# implemented_by and extern are attribute prefixes, ofReduceBool is the
# Lean.ofReduceBool path, block comments are the "/-" opener, the import
# pattern captures the first dotted segment of the module name, and
# nonEmptyLines is the oracle's splitlines-then-strip face.  One deliberate
# deviation from the oracle: decls is reported here as the combined total
# thm + defFam (8 line-start keywords), not the oracle's narrower 5-keyword
# decl face, per the v2 audit contract; the two agree exactly on trees with
# no structure/class/inductive at line start.  The oracle compiles the
# sorryAx pattern but never sums it; this tool closes that gap per the audit
# contract (sorryAx is a token total).  A file enters the scan by a .lean or
# .v suffix (the oracle scans .lean only), and any .git directory is skipped
# wholesale.
#
# Output shape.  Every top-level key except scan_face is {"value": ...,
# "basis": ...}; the basis is one ASCII line naming the counting rule, so a
# consumer quoting a number quotes its rule with it and two tools cannot
# hide different rules behind one field name.  scan_face carries the four
# fixed English fields scanned / not_scanned / negative_finding /
# equivalents, so a citation of any count carries the scan's coverage limits
# with it; all four strings are module constants pinned verbatim by the
# selftest.
#
# Determinism.  Counts, perDir totals, zeroDeclFiles, bytes, lines and
# nonEmptyLines are walk-order independent.  largest10 sorts (bytes, rel)
# tuples descending and importRoots sorts by descending count with ties kept
# in first-encounter order, both exactly as the oracle does, so a same-tree
# cross-check is equal; importRoots tie order is filesystem-walk dependent
# by construction.
#
# Fast path.  Each counted pass is gated on its pattern's required literal
# (see _pattern_count): a match necessarily contains the literal, so an
# absent literal skips the regex with the count provably unchanged, and
# clean files pay for only the few passes whose literals they carry.  The
# nonEmptyLines pass opens only when the file holds at least one
# non-whitespace byte (NONEMPTY_GATE); that byte must land on some
# splitlines segment stripped non-empty, so a closed gate proves the count
# is 0 and an open gate never changes it.

RX = {
    "thm": re.compile(rb"^\s*(theorem|lemma)\b", re.M),
    "deffam": re.compile(rb"^\s*(def|abbrev|structure|class|instance"
                         rb"|inductive)\b", re.M),
    "sorry": re.compile(rb"\bsorry\b"),
    "sorryAx": re.compile(rb"\bsorryAx\b"),
    "axiom": re.compile(rb"^\s*axiom\s", re.M),
    "opaque": re.compile(rb"^\s*opaque\s", re.M),
    "native_decide": re.compile(rb"native_decide"),
    "unsafe": re.compile(rb"^\s*unsafe\s", re.M),
    "implemented_by": re.compile(rb"@\[implemented_by"),
    "extern": re.compile(rb"@\[extern"),
    "ofReduceBool": re.compile(rb"Lean\.ofReduceBool"),
    "comment_line": re.compile(rb"^\s*--", re.M),
    "block_comment": re.compile(rb"/-"),
    "import": re.compile(rb"^\s*import\s+([A-Za-z_][\w.]*)", re.M),
}

SOURCE_SUFFIXES = (".lean", ".v")
READ_ERROR_CAP = 10

# Decl-keyword literals for the decl gates (any presence opens the pass).
THM_LITERALS = (b"theorem", b"lemma")
DEFFAM_LITERALS = (b"def", b"abbrev", b"structure", b"class",
                   b"instance", b"inductive")

# Gate for the non-empty-line pass: one byte outside the ASCII whitespace
# set proves a non-empty line exists; no such byte proves the count is 0.
NONEMPTY_GATE = re.compile(rb"[^\t\n\x0b\x0c\r ]")

# The four fixed scan-face strings.  They travel with every report so a
# consumer quoting any count also quotes the scan's coverage limits; the
# selftest pins all four verbatim.
SCAN_SCANNED = (
    "All files with a .lean or .v suffix under the root, walked recursively"
    " with .git directories skipped; each file is read once in binary and"
    " counted with fixed lowercase byte regexes, so comment and string"
    " content is counted too."
)
SCAN_NOT_SCANNED = (
    "Files with any other suffix, everything under .git, and anything a"
    " byte regex cannot see: identifier meaning, declaration structure,"
    " encodings, uppercase spellings; unreadable files appear only in"
    " errors."
)
SCAN_NEGATIVE_FINDING = (
    "A zero count is a negative finding of this scan, not an absolute"
    " claim."
)
SCAN_EQUIVALENTS = (
    "The declaration family uses fixed keyword patterns; equivalent"
    " constructs spelled differently are not exhaustively covered."
)


def _pattern_count(rx, literals, txt):
    """Regex match count gated by the pattern's required literal(s).

    A bytes literal opens the pass only when present; a tuple opens it when
    any member is present.  The gate never changes a count: no literal, no
    match, so the regex runs only on files that can match.
    """
    if isinstance(literals, bytes):
        if literals not in txt:
            return 0
    else:
        for lit in literals:
            if lit in txt:
                break
        else:
            return 0
    return len(rx.findall(txt))


def audit_root(root):
    """Scan root once in binary and return (report, rc).

    rc 2 names a non-directory root (a usage error), rc 1 marks a scan with
    read failures (each recorded in errors, loud), rc 0 a complete scan.
    """
    if not os.path.isdir(root):
        return None, 2
    files = 0
    total_bytes = 0
    total_lines = 0
    non_empty_lines = 0
    thm_total = 0
    deffam_total = 0
    decls = 0
    sorry = 0
    sorry_ax = 0
    axiom = 0
    opaque = 0
    native_decide = 0
    unsafe_files = 0
    implemented_by_files = 0
    extern_files = 0
    of_reduce_bool_files = 0
    comment_lines = 0
    block_comment_files = 0
    zero_decl_files = 0
    per_dir = {}
    largest = []
    imports = {}
    errors = []
    for r, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for fn in names:
            if not fn.endswith(SOURCE_SUFFIXES):
                continue
            path = os.path.join(r, fn)
            rel = os.path.relpath(path, root).replace("\\", "/")
            try:
                with open(path, "rb") as fh:
                    txt = fh.read()
            except OSError as exc:
                errors.append("read %s: %s" % (rel, exc))
                continue
            top = rel.split("/")[0]
            bucket = per_dir.setdefault(top, {"files": 0, "decls": 0,
                                              "bytes": 0})
            bucket["files"] += 1
            bucket["bytes"] += len(txt)
            files += 1
            total_bytes += len(txt)
            total_lines += txt.count(b"\n")
            if NONEMPTY_GATE.search(txt):
                non_empty_lines += sum(1 for ln in txt.splitlines()
                                       if ln.strip())
            largest.append((len(txt), rel))
            n_thm = _pattern_count(RX["thm"], THM_LITERALS, txt)
            n_deffam = _pattern_count(RX["deffam"], DEFFAM_LITERALS, txt)
            n_decl = n_thm + n_deffam
            thm_total += n_thm
            deffam_total += n_deffam
            decls += n_decl
            bucket["decls"] += n_decl
            comment_lines += _pattern_count(RX["comment_line"], b"--", txt)
            sorry += _pattern_count(RX["sorry"], b"sorry", txt)
            sorry_ax += _pattern_count(RX["sorryAx"], b"sorryAx", txt)
            axiom += _pattern_count(RX["axiom"], b"axiom", txt)
            opaque += _pattern_count(RX["opaque"], b"opaque", txt)
            native_decide += _pattern_count(RX["native_decide"],
                                            b"native_decide", txt)
            if _pattern_count(RX["unsafe"], b"unsafe", txt):
                unsafe_files += 1
            if _pattern_count(RX["implemented_by"], b"@[implemented_by",
                              txt):
                implemented_by_files += 1
            if _pattern_count(RX["extern"], b"@[extern", txt):
                extern_files += 1
            if _pattern_count(RX["ofReduceBool"], b"ofReduceBool", txt):
                of_reduce_bool_files += 1
            if _pattern_count(RX["block_comment"], b"/-", txt):
                block_comment_files += 1
            if n_decl == 0:
                zero_decl_files += 1
            if _pattern_count(RX["import"], b"import", txt):
                for m in RX["import"].findall(txt):
                    r0 = m.split(b".")[0].decode("ascii", "replace")
                    imports[r0] = imports.get(r0, 0) + 1
    largest.sort(reverse=True)
    report = {
        "files": {"value": files,
                  "basis": ".lean and .v files under the root; .git trees"
                           " are skipped"},
        "bytes": {"value": total_bytes,
                  "basis": "raw byte totals of the scanned files, binary"
                           " read"},
        "lines": {"value": total_lines,
                  "basis": "LF-terminated lines, binary read (LF byte"
                           " count)"},
        "nonEmptyLines": {"value": non_empty_lines,
                          "basis": "lines carrying at least one"
                                   " non-whitespace byte (splitlines, then"
                                   " strip)"},
        "thm": {"value": thm_total,
                "basis": "declarations starting a line with 'theorem' or"
                         " 'lemma'"},
        "defFam": {"value": deffam_total,
                   "basis": "declarations starting a line with def,"
                            " abbrev, structure, class, instance or"
                            " inductive"},
        "decls": {"value": decls,
                  "basis": "combined total thm + defFam (backward anchor)"},
        "sorry": {"value": sorry,
                  "basis": "word-bounded 'sorry' token hits, comments and"
                           " strings included"},
        "sorryAx": {"value": sorry_ax,
                    "basis": "word-bounded 'sorryAx' token hits, comments"
                             " and strings included"},
        "axiom": {"value": axiom,
                  "basis": "'axiom ' declarations at line start"},
        "opaque": {"value": opaque,
                   "basis": "'opaque ' declarations at line start"},
        "native_decide": {"value": native_decide,
                          "basis": "bare 'native_decide' substring hits"},
        "unsafe": {"value": unsafe_files,
                   "basis": "files with at least one line starting with"
                            " 'unsafe '"},
        "implemented_by": {"value": implemented_by_files,
                           "basis": "files containing '@[implemented_by'"},
        "extern": {"value": extern_files,
                   "basis": "files containing '@[extern'"},
        "ofReduceBool": {"value": of_reduce_bool_files,
                         "basis": "files containing 'Lean.ofReduceBool'"},
        "commentLines": {"value": comment_lines,
                         "basis": "lines whose first non-space text starts"
                                  " with '--'"},
        "blockCommentFiles": {"value": block_comment_files,
                              "basis": "files containing the '/-'"
                                       " block-comment opener"},
        "perDir": {"value": per_dir,
                   "basis": "first path segment -> {files, decls, bytes};"
                            " decls is the thm + defFam face"},
        "largest10": {"value": [{"path": rel, "bytes": n}
                                for n, rel in largest[:10]],
                      "basis": "top 10 files by raw bytes, descending;"
                               " ties break by path, descending"},
        "zeroDeclFiles": {"value": zero_decl_files,
                          "basis": "files with zero thm and zero defFam"
                                   " line-start hits"},
        "importRoots": {"value": [[r0, n] for r0, n in
                                  sorted(imports.items(),
                                         key=lambda kv: -kv[1])[:10]],
                        "basis": "top 10 first segments of import targets"
                                 " by count; ties keep first-encounter"
                                 " order"},
        "root": {"value": root,
                 "basis": "the audit root as given; scanned literally, no"
                          " src/ descent"},
        "errors": {"value": errors[:READ_ERROR_CAP],
                   "basis": "first 10 read failures, each 'read <relative"
                            " path>: <reason>'"},
        "errorCount": {"value": len(errors),
                       "basis": "total files that failed to read; errors"
                                " is capped at 10"},
        "scan_face": {
            "scanned": SCAN_SCANNED,
            "not_scanned": SCAN_NOT_SCANNED,
            "negative_finding": SCAN_NEGATIVE_FINDING,
            "equivalents": SCAN_EQUIVALENTS,
        },
    }
    return report, (1 if errors else 0)


def write_json(path, payload):
    """Write the stdout payload (plus one newline) to path as UTF-8 text."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
        fh.write("\n")


def run_selftest():
    """Fixture vectors over temporary directories; 0 green, 1 red."""
    fails = []

    def check(name, ok, detail=""):
        if ok:
            print("[PASS] %s" % name)
        else:
            fails.append(name)
            print("[FAIL] %s %s" % (name, detail))

    tmp = tempfile.mkdtemp(prefix="tree_audit_selftest_")
    try:
        a_enc = FIXTURE_ALPHA.encode("utf-8")
        b_enc = FIXTURE_BETA.encode("utf-8")
        g_enc = FIXTURE_GAMMA.encode("utf-8")
        os.mkdir(os.path.join(tmp, "sub"))
        with open(os.path.join(tmp, "alpha.v"), "wb") as fh:
            fh.write(a_enc)
        with open(os.path.join(tmp, "beta.v"), "wb") as fh:
            fh.write(b_enc)
        with open(os.path.join(tmp, "sub", "gamma.lean"), "wb") as fh:
            fh.write(g_enc)
        os.mkdir(os.path.join(tmp, ".git"))
        with open(os.path.join(tmp, ".git", "decoy.v"), "wb") as fh:
            fh.write(b"theorem decoy : Nat := 0\nsorry\n")
        with open(os.path.join(tmp, "notes.txt"), "wb") as fh:
            fh.write(b"sorry\ntheorem decoy : Nat := 0\n")
        report, rc = audit_root(tmp)
        check("scan-rc", rc == 0, "rc=%s" % rc)
        check("files", report["files"]["value"] == 3,
              "got %s" % report["files"]["value"])
        check("bytes", report["bytes"]["value"] ==
              len(a_enc) + len(b_enc) + len(g_enc),
              "got %s" % report["bytes"]["value"])
        check("lines", report["lines"]["value"] == 35,
              "got %s" % report["lines"]["value"])
        check("nonEmptyLines", report["nonEmptyLines"]["value"] == 33,
              "got %s" % report["nonEmptyLines"]["value"])
        check("thm", report["thm"]["value"] == 3,
              "got %s" % report["thm"]["value"])
        check("defFam", report["defFam"]["value"] == 7,
              "got %s" % report["defFam"]["value"])
        check("decls", report["decls"]["value"] == 10,
              "got %s" % report["decls"]["value"])
        check("decls-combined", report["decls"]["value"] ==
              report["thm"]["value"] + report["defFam"]["value"],
              "thm=%s defFam=%s decls=%s" % (report["thm"]["value"],
                                             report["defFam"]["value"],
                                             report["decls"]["value"]))
        check("sorry", report["sorry"]["value"] == 3,
              "got %s" % report["sorry"]["value"])
        check("sorryAx", report["sorryAx"]["value"] == 2,
              "got %s" % report["sorryAx"]["value"])
        check("axiom", report["axiom"]["value"] == 1,
              "got %s" % report["axiom"]["value"])
        check("opaque", report["opaque"]["value"] == 1,
              "got %s" % report["opaque"]["value"])
        check("native_decide", report["native_decide"]["value"] == 2,
              "got %s" % report["native_decide"]["value"])
        check("unsafe", report["unsafe"]["value"] == 1,
              "got %s" % report["unsafe"]["value"])
        check("implemented_by", report["implemented_by"]["value"] == 1,
              "got %s" % report["implemented_by"]["value"])
        check("extern", report["extern"]["value"] == 1,
              "got %s" % report["extern"]["value"])
        check("ofReduceBool", report["ofReduceBool"]["value"] == 1,
              "got %s" % report["ofReduceBool"]["value"])
        check("commentLines", report["commentLines"]["value"] == 5,
              "got %s" % report["commentLines"]["value"])
        check("blockCommentFiles", report["blockCommentFiles"]["value"] == 1,
              "got %s" % report["blockCommentFiles"]["value"])
        check("zeroDeclFiles", report["zeroDeclFiles"]["value"] == 1,
              "got %s" % report["zeroDeclFiles"]["value"])
        # The .git skip and the suffix filter are proven by the totals
        # above: the .git decoy would add one thm hit and one sorry token,
        # notes.txt one sorry token and one thm hit; both stay out of
        # every count.
        # Shape: every top-level key but scan_face carries value + basis;
        # scan_face carries exactly the four fixed fields, verbatim.
        bare = [k for k in report
                if k != "scan_face"
                and not (isinstance(report[k], dict)
                         and "value" in report[k]
                         and "basis" in report[k])]
        check("value-basis-shape", bare == [], "bare keys: %s" % bare)
        face = report["scan_face"]
        check("scan-face-fields",
              sorted(face) == ["equivalents", "negative_finding",
                               "not_scanned", "scanned"],
              "got %s" % sorted(face))
        check("scan-face-verbatim",
              face.get("scanned") == SCAN_SCANNED
              and face.get("not_scanned") == SCAN_NOT_SCANNED
              and face.get("negative_finding") == SCAN_NEGATIVE_FINDING
              and face.get("equivalents") == SCAN_EQUIVALENTS,
              "scan_face strings drifted from the constants")
        per_dir = report["perDir"]["value"]
        check("perDir-keys", set(per_dir) == {"alpha.v", "beta.v", "sub"},
              "got %s" % sorted(per_dir))
        check("perDir-alpha", per_dir.get("alpha.v") == {
            "files": 1, "decls": 7, "bytes": len(a_enc)},
            "got %s" % per_dir.get("alpha.v"))
        check("perDir-beta", per_dir.get("beta.v") == {
            "files": 1, "decls": 0, "bytes": len(b_enc)},
            "got %s" % per_dir.get("beta.v"))
        check("perDir-sub", per_dir.get("sub") == {
            "files": 1, "decls": 3, "bytes": len(g_enc)},
            "got %s" % per_dir.get("sub"))
        largest = report["largest10"]["value"]
        check("largest10-count", len(largest) == 3, "got %s" % len(largest))
        check("largest10-top", largest[0] == {"path": "alpha.v",
                                              "bytes": len(a_enc)},
              "got %s" % largest[0])
        imports = dict(report["importRoots"]["value"])
        check("importRoots", imports == {"Mathlib": 2, "Batteries": 1,
                                         "Init": 1} and len(imports) == 3,
              "got %s" % report["importRoots"]["value"])
        check("errors", report["errors"]["value"] == []
              and report["errorCount"]["value"] == 0,
              "got %s / %s" % (report["errors"]["value"],
                               report["errorCount"]["value"]))
        check("root-field", report["root"]["value"] == tmp,
              "got %s" % report["root"]["value"])
        # --json round trip: the file payload parses back to the report.
        json_path = os.path.join(tmp, "out.json")
        payload = json.dumps(report, ensure_ascii=False)
        write_json(json_path, payload)
        with open(json_path, "r", encoding="utf-8") as fh:
            round_trip = json.load(fh)
        check("json-round-trip", round_trip == report, "payload mismatch")
        # Empty tree face: zero files, still green.
        empty = tempfile.mkdtemp(prefix="tree_audit_selftest_empty_")
        try:
            report2, rc2 = audit_root(empty)
            check("empty-rc", rc2 == 0
                  and report2["files"]["value"] == 0,
                  "rc=%s files=%s" % (rc2, report2["files"]["value"]))
        finally:
            shutil.rmtree(empty, ignore_errors=True)
        # Missing root face: rc 2, loud.
        missing = os.path.join(tmp, "no-such-dir")
        report3, rc3 = audit_root(missing)
        check("missing-root-rc", rc3 == 2 and report3 is None,
              "rc=%s report=%s" % (rc3, report3))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        print("[SELFTEST] tree_audit red: %d vector(s) failed: %s"
              % (len(fails), ", ".join(fails)))
        return 1
    print("[SELFTEST] tree_audit green: all vectors pass")
    return 0


FIXTURE_ALPHA = (
    "-- alpha fixture header comment\n"
    "theorem alpha_one : Nat := 1\n"
    "def alpha_two : Nat := 2\n"
    "-- mentions sorry inside a comment (raw-scan sense)\n"
    "axiom alpha_ax : Prop\n"
    "opaque alpha_op : Nat := 3\n"
    "instance alpha_inst : Inhabited Nat where default := 0\n"
    "abbrev alpha_ab : Nat := 7\n"
    "@[implemented_by alpha_two] def alpha_attr : Nat := 8\n"
    '@[extern "alpha_e"] def alpha_ext : Nat := 9\n'
    "unsafe def alpha_u : Nat := 10\n"
    "sorry\n"
    "sorry\n"
    "sorryAx\n"
    "native_decide\n"
    "Lean.ofReduceBool\n"
    "import Mathlib.Data.Set\n"
    "import Batteries.Tactic\n"
    "/- block comment\n"
    "-- inside a block comment still lands on the line count\n"
    "-/\n"
    "native_decide\n"
    "structure alpha_st where\n"
    "class alpha_cl where\n"
    "inductive alpha_in | tag\n"
    "\n"
    "   \n"
)

FIXTURE_BETA = (
    "-- beta fixture: a declaration-free face\n"
    "import Mathlib.Data.Set\n"
    "prose mentions sorryAx without a declaration\n"
)

FIXTURE_GAMMA = (
    "-- gamma fixture: the .lean face\n"
    "theorem gamma_one : Nat := 1\n"
    "lemma gamma_two : Nat := 2\n"
    "def gamma_three : Nat := 3\n"
    "import Init\n"
)


def main(argv=None):
    """CLI entry; returns the process exit code (0/1/2)."""
    ap = argparse.ArgumentParser(
        prog=TOOL,
        description="read-only tree health audit over .lean/.v source trees"
                    " (one JSON line)")
    ap.add_argument("--root", metavar="DIR",
                    help="the audit root (scanned literally; .git skipped)")
    ap.add_argument("--json", metavar="OUT",
                    help="write the stdout JSON payload to OUT as well")
    ap.add_argument("--selftest", action="store_true",
                    help="run the fixture vectors on temporary directories")
    args = ap.parse_args(argv)
    if args.selftest:
        if args.root or args.json:
            ap.error("--selftest runs standalone; combine it with no scan"
                     " flags")
        return run_selftest()
    if not args.root:
        ap.error("--root is required unless --selftest is given")
    report, rc = audit_root(args.root)
    if rc == 2:
        sys.stderr.write("tree_audit: --root is not a directory: %s\n"
                         % args.root)
        return 2
    payload = json.dumps(report, ensure_ascii=False)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(payload)
    if args.json:
        try:
            write_json(args.json, payload)
        except OSError as exc:
            sys.stderr.write("tree_audit: --json write failed: %s\n" % exc)
            return 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
