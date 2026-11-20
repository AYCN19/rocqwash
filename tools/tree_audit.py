#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tree_audit.py - read-only tree health audit over .lean/.v source trees.

Purpose.  One JSON-line census of a source tree: file/byte/line totals, declaration
  counts, an unsound-feature sweep (sorry, sorryAx, axiom, opaque, native_decide,
  unsafe, implemented_by, extern, ofReduceBool), comment faces, per-directory and
  largest-file tables, and the import-root histogram.  Counting is byte-literal and
  lowercase, calibrated one-to-one to the sandbox census_rh.py face (raw bytes, so
  comments and strings count too), so a same-tree cross-check is field-for-field
  equal; the root is scanned literally (no src/ descent) and .v counts sit beside .lean.
Interface.  python3 tools/tree_audit.py --root DIR [--json OUT] | --selftest; stdout
  carries one JSON line and --json writes the same payload to OUT.  Fields: files,
  bytes, lines, decls, sorry, sorryAx, axiom, opaque, native_decide, unsafe,
  implemented_by, extern, ofReduceBool, commentLines, blockCommentFiles, perDir,
  largest10, zeroDeclFiles, importRoots, plus root, errors and errorCount; sense:
  sorry/sorryAx/native_decide are token totals, axiom/opaque are line-anchored
  declaration totals, unsafe/implemented_by/extern/ofReduceBool are per-file hit
  counts, largest10 is [{"path","bytes"}], importRoots is a top-ten [[root,count]]
  list, perDir maps the first path segment to {files, decls, bytes}.
Dependencies.  Python 3 standard library only (argparse, json, os, re, shutil,
  sys, tempfile); the fast path reads each file once in binary and scans bytes with
  precompiled regexes: zero subprocess, zero network, zero imports of the scanned
  tree, zero tree writes.
Evidence.  --selftest builds a temporary fixture tree (.v and .lean files with
  hand-derived known counts), asserts every report field against those vectors, the
  exit-code faces (green scan, empty tree, missing root rc=2) and the --json round
  trip; the Deicyde mirror cross-check against census_rh.py runs out of tree.
Exit-codes.  0 green (complete scan or green selftest); 1 red (any selftest vector
  fails, any file read fails, or the --json write fails); 2 usage (missing or
  non-directory --root, --selftest combined with scan flags, unknown flags).
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
# decl/axiom/opaque/unsafe/commentLine are line-anchored (re.M), sorry and
# sorryAx are word-bounded tokens, native_decide is a bare token,
# implemented_by and extern are attribute prefixes, ofReduceBool is the
# Lean.ofReduceBool path, block comments are the "/-" opener, and the import
# pattern captures the first dotted segment of the module name.  The oracle
# compiles the sorryAx pattern but never sums it; this tool closes that gap
# per the audit contract (sorryAx is a token total).  A file enters the scan
# by a .lean or .v suffix, and any .git directory is skipped wholesale.
#
# Determinism.  Counts, perDir totals, zeroDeclFiles, bytes and lines are
# walk-order independent.  largest10 sorts (bytes, rel) tuples descending and
# importRoots sorts by descending count with ties kept in first-encounter
# order, both exactly as the oracle does, so a same-tree cross-check is
# equal; importRoots tie order is filesystem-walk dependent by construction.
#
# Fast path.  Each counted pass is gated on its pattern's required literal
# (see _pattern_count): a match necessarily contains the literal, so an
# absent literal skips the regex with the count provably unchanged, and
# clean files pay for only the few passes whose literals they carry.

RX = {
    "decl": re.compile(rb"^\s*(theorem|lemma|def|instance|abbrev)\b", re.M),
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

# Decl-keyword literals for the decl gate (any presence opens the pass).
KW_DECLS = (b"theorem", b"lemma", b"def", b"instance", b"abbrev")


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
            bucket = per_dir.setdefault(top, {"files": 0, "decls": 0, "bytes": 0})
            bucket["files"] += 1
            bucket["bytes"] += len(txt)
            files += 1
            total_bytes += len(txt)
            total_lines += txt.count(b"\n")
            largest.append((len(txt), rel))
            n_decl = _pattern_count(RX["decl"], KW_DECLS, txt)
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
            if _pattern_count(RX["implemented_by"], b"@[implemented_by", txt):
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
        "files": files,
        "bytes": total_bytes,
        "lines": total_lines,
        "decls": decls,
        "sorry": sorry,
        "sorryAx": sorry_ax,
        "axiom": axiom,
        "opaque": opaque,
        "native_decide": native_decide,
        "unsafe": unsafe_files,
        "implemented_by": implemented_by_files,
        "extern": extern_files,
        "ofReduceBool": of_reduce_bool_files,
        "commentLines": comment_lines,
        "blockCommentFiles": block_comment_files,
        "perDir": per_dir,
        "largest10": [{"path": rel, "bytes": n} for n, rel in largest[:10]],
        "zeroDeclFiles": zero_decl_files,
        "importRoots": [[r0, n] for r0, n in
                        sorted(imports.items(), key=lambda kv: -kv[1])[:10]],
        "root": root,
        "errors": errors[:READ_ERROR_CAP],
        "errorCount": len(errors),
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
        check("files", report["files"] == 3, "got %s" % report["files"])
        check("bytes", report["bytes"] == len(a_enc) + len(b_enc) + len(g_enc),
              "got %s" % report["bytes"])
        check("lines", report["lines"] == 30, "got %s" % report["lines"])
        check("decls", report["decls"] == 7, "got %s" % report["decls"])
        check("sorry", report["sorry"] == 3, "got %s" % report["sorry"])
        check("sorryAx", report["sorryAx"] == 2, "got %s" % report["sorryAx"])
        check("axiom", report["axiom"] == 1, "got %s" % report["axiom"])
        check("opaque", report["opaque"] == 1, "got %s" % report["opaque"])
        check("native_decide", report["native_decide"] == 2,
              "got %s" % report["native_decide"])
        check("unsafe", report["unsafe"] == 1, "got %s" % report["unsafe"])
        check("implemented_by", report["implemented_by"] == 1,
              "got %s" % report["implemented_by"])
        check("extern", report["extern"] == 1, "got %s" % report["extern"])
        check("ofReduceBool", report["ofReduceBool"] == 1,
              "got %s" % report["ofReduceBool"])
        check("commentLines", report["commentLines"] == 5,
              "got %s" % report["commentLines"])
        check("blockCommentFiles", report["blockCommentFiles"] == 1,
              "got %s" % report["blockCommentFiles"])
        check("zeroDeclFiles", report["zeroDeclFiles"] == 1,
              "got %s" % report["zeroDeclFiles"])
        # The .git skip and the suffix filter are proven by the totals above:
        # the decoy file would add one decl and two sorry tokens, notes.txt
        # one more sorry token; both stay out of every count.
        per_dir = report["perDir"]
        check("perDir-keys", set(per_dir) == {"alpha.v", "beta.v", "sub"},
              "got %s" % sorted(per_dir))
        check("perDir-alpha", per_dir.get("alpha.v") == {
            "files": 1, "decls": 4, "bytes": len(a_enc)},
            "got %s" % per_dir.get("alpha.v"))
        check("perDir-beta", per_dir.get("beta.v") == {
            "files": 1, "decls": 0, "bytes": len(b_enc)},
            "got %s" % per_dir.get("beta.v"))
        check("perDir-sub", per_dir.get("sub") == {
            "files": 1, "decls": 3, "bytes": len(g_enc)},
            "got %s" % per_dir.get("sub"))
        largest = report["largest10"]
        check("largest10-count", len(largest) == 3, "got %s" % len(largest))
        check("largest10-top", largest[0] == {"path": "alpha.v",
                                              "bytes": len(a_enc)},
              "got %s" % largest[0])
        imports = dict(report["importRoots"])
        check("importRoots", imports == {"Mathlib": 2, "Batteries": 1,
                                         "Init": 1} and len(imports) == 3,
              "got %s" % report["importRoots"])
        check("errors", report["errors"] == [] and report["errorCount"] == 0,
              "got %s / %s" % (report["errors"], report["errorCount"]))
        check("root-field", report["root"] == tmp, "got %s" % report["root"])
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
            check("empty-rc", rc2 == 0 and report2["files"] == 0,
                  "rc=%s files=%s" % (rc2, report2["files"]))
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
