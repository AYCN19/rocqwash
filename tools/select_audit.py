#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""select_audit.py - batch-selection auditor with a Require-face audit (rocqwash tools/).

Purpose.  Audits candidate selection lists against a full read of the tree's
  `order.txt` roster (line-by-line, never from memory), so in-batch duplicates,
  cross-batch name collisions, roster ghosts and duplicate roster rows surface
  before a batch enters a born world.  A second face audits the Require
  statements of a `.v` file: statement-level parsing, allowlist, closure.

Interface.  python3 tools/select_audit.py --order <order.txt> --select <batch.txt>
  [--select <batch2.txt> ...] [--json out.json] | --order <order.txt> --grep <name>
  | --requires <file.v> --world <world-dir> | --selftest.  Checks (any failing ->
  exit 1): DUP-BATCH duplicate name in one batch; DUP-CROSS one name claimed by
  >= 2 batches; NOT-IN-ORDER name absent from the roster; DUP-ORDER duplicate
  roster row; REQ-GAP non-exempt Require with no `.v`/`.vo` counterpart.  Names
  normalize alike on both sides (whitespace/`#` comments/`.v` suffix stripped,
  `/`-paths kept, whole-word match: `UpReqBanach` never matches `UpReqBanachExp.v`).
Dependencies.  Python 3 standard library only (argparse, io, json, os, re, sys);
  read-only inputs, the sole write surface is the explicit --json report path.
Evidence.  --selftest drives temp-file vectors (clean, duplicate, collision,
  ghost, roster self-duplicate, grep two-way, usage/missing codes, Require-face
  RED and CLOSED, string-literal stripping); suite tests/test_select_audit.py
  (lane t_select_audit); precedents `sandbox/seat_nw6/账/候批账-nw6批.md`, `sandbox/seat_dver2/账/collision_enbig7_20261031.md`.
Exit-codes.  0 = AUDIT-CLEAN / REQUIRES-CLOSED / grep hit; 1 = AUDIT-RED /
  REQ-GAP / grep miss; 2 = usage error; 9 = missing input path (fail loud,
  no simulation).
"""
import argparse
import io
import json
import os
import re
import sys

PROG = "select_audit"


def normalize_line(line):
    """Line -> module name: strip `#` comments and `#`-tag annotations, strip
    the `.v` suffix, strip whitespace.  Empty or comment-only lines return None.

    A name may carry an embedded `/` path form (the certified roster
    `scripts/order.txt` carries one row `Local/LW0LeibSeparation.v#R160-eb42d3`
    among its 671 lines, read first-hand from the live table): the auditor must
    read the whole table and never reject it over one row's shape.
    """
    s = line.strip()
    s = s.split("#", 1)[0].strip()  # strip the # comment / # tag annotation (Name.v#R0-d66910 -> Name.v)
    if not s:
        return None
    if s.endswith(".v"):
        s = s[:-2]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*/?[A-Za-z0-9_'/]*", s):
        raise AuditError("not a valid module name %r (after normalization the"
                         " name must be an identifier or an identifier/path"
                         " form)" % line.strip())
    return s


def read_names(path, what):
    """Read a selection file -> the ordered bare-name list."""
    if not os.path.isfile(path):
        raise MissingPath("%s file missing: %s" % (what, path))
    names = []
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            n = normalize_line(line)
            if n is not None:
                names.append(n)
    return names


class AuditError(Exception):
    pass


class MissingPath(Exception):
    pass


def audit(order_names, batches):
    """The four-check audit.  order_names = the roster's ordered bare names;
    batches = [(path, ordered bare names), ...].  Returns the findings list
    (each item a dict(code/name/detail))."""
    findings = []
    # check 4: duplicate rows of one name inside the roster itself (only a
    # full-table grep can surface them)
    seen_order = {}
    for n in order_names:
        seen_order[n] = seen_order.get(n, 0) + 1
    for n in sorted(seen_order):
        if seen_order[n] > 1:
            findings.append({"code": "DUP-ORDER", "name": n,
                             "detail": "order.txt carries %d rows of this name"
                                       " (duplicate registry row)" % seen_order[n]})
    order_set = set(order_names)
    # check 1: in-batch duplicates (the form a from-memory selection produces)
    # + check 2: cross-batch name collision (two agents claiming one file)
    global_seen = {}  # name -> [batch_idx...]
    for bi, (bpath, names) in enumerate(batches, 1):
        seen = {}
        for n in names:
            seen[n] = seen.get(n, 0) + 1
        for n in sorted(seen):
            if seen[n] > 1:
                findings.append({"code": "DUP-BATCH", "name": n,
                                 "detail": "batch %d (%s) repeats the name %d"
                                           " times" % (bi, os.path.basename(bpath), seen[n])})
            global_seen.setdefault(n, []).append(bi)
    for n in sorted(global_seen):
        if len(global_seen[n]) > 1:
            findings.append({"code": "DUP-CROSS", "name": n,
                             "detail": "dual claim on one file: batches %s"
                                       " (two agents in one domain - a name"
                                       "-collision precursor)"
                                       % ", ".join(str(b) for b in global_seen[n])})
    # check 3: a name selected that the roster does not hold (full-table read,
    # never from memory)
    for n in sorted(set(k for _, names in batches for k in names)):
        if n not in order_set:
            findings.append({"code": "NOT-IN-ORDER", "name": n,
                             "detail": "absent from the order.txt roster"
                                       " (full-table grep miss on a read of"
                                       " the whole table)"})
    return findings


def grep_rows(order_lines, name):
    """Single-name full-table grep (the mechanical stand-in for a full read) ->
    the raw hit rows.  Whole-word comparison."""
    hits = []
    pat = re.compile(r"(^|[^A-Za-z0-9_])" + re.escape(name) + r"\.v(\s|$|#)")
    for line in order_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if pat.search(stripped):
            hits.append(stripped.rstrip("\n"))
    return hits


# ---------------------------------------------------------------------------
# Require-face audit: statement-level Require parsing, Stdlib allowlist
# exemption, world existence closure.
#
# Defect forms this face closes (side evidence, a read-only survey of the
# ConstructiveWorld workflow drafts `.zcode/workflow-drafts/nw10九件勘定审计席.dwf.ts:9`
# and `.zcode/workflow-drafts/abl6六件审计验证席.dwf.ts:10`, whose instructions
# mandated a per-file Require/From grep over a no-allowlist closure): a
# single-line grep misses Require Export and multi-name statements, and a
# closure without an allowlist judges the standard-library modules
# (QArith/Lia/List/Extraction/Lqa/Morphisms and the bare/short-path forms)
# as in-tree gaps.  The three-part method:
#   1. parse_requires: statement-level regex from `Require` to its terminator;
#     collects multi-name / multi-line / From-prefix / Import-Export verb
#     forms; Coq block comments and string literals are stripped in one pass
#     first (a Require inside a comment or a string literal never enters the
#     findings).
#   2. STDLIB_ROOTS: a Require name whose first segment hits the allowlist is
#     exempt (QArith.QArith exempts by the QArith root; Lia is single-segment;
#     no collision with the in-tree naming S01_*/UpReq*/*Lcm).
#   3. audit_requires: every non-exempt name is checked against the full world
#     index (os.walk collecting .v/.vo relative paths) by exact or
#     `/`-anchored suffix match; compatible with `-R` world-root prefixes and
#     From-directory forms; the `/` anchor guards prefix over-matching (a
#     world holding sub/UpReqBanachExp.v does not close UpReqBanach).
# ---------------------------------------------------------------------------

# Six case-named Stdlib roots lead, followed by the common bare/short-path
# Stdlib logic roots (first-segment exemptions; an extensible constant).
# The bare/short-path roots (Lists, Strings, Sorting, String, Ascii, PeanoNat,
# Permutation, QArith_base, Qring, Qfield, Qabs, ZArith_dec, ZArithRing,
# Wf_nat, micromega, setoid_ring) were each verified present under the local
# toolchain tree `Live/toolchain/opam/live/lib/coq/user-contrib/Stdlib/**`
# before entering this set.
STDLIB_ROOTS = frozenset((
    "QArith", "Lia", "List", "Extraction", "Lqa", "Morphisms",
    "Stdlib", "Coq", "Init", "Logic", "Program",
    "Arith", "ZArith", "NArith", "Nat", "Peano", "BinNums", "BinInt",
    "BinNat", "BinPos", "Decimal", "Hexadecimal", "Number", "Numbers",
    "Bool", "Setoid", "Setoids", "Decidable", "Orders", "Rings", "Fields",
    "Algebra", "Structures", "Relations", "Reals", "Rbase", "Rtrigo",
    "Nia", "Psatz", "Micromega",
    # bare/short-path additions (verified present under Stdlib/**, first
    # segments of the bare and short-path forms)
    "Lists", "Strings", "Sorting", "String", "Ascii", "PeanoNat",
    "Permutation", "QArith_base", "Qring", "Qfield", "Qabs",
    "ZArith_dec", "ZArithRing", "Wf_nat", "micromega", "setoid_ring",
))

# statement head: [From X] Require [Import|Export] (captures the From prefix
# and the verb; the name region is scanned separately)
_REQ_HEAD_RE = re.compile(
    r"(?:From\s+(?P<frm>[A-Za-z_][\w']*(?:\.[\w']*)*)\s+)?"
    r"Require(?P<verb>\s+(?:Import|Export))?(?![\w'])",
    re.S)
# name token: dotted-path identifier
_REQ_NAME_RE = re.compile(r"[A-Za-z_][\w']*(?:\.[A-Za-z_][\w']*)*")
# name-region stop words (a bare token hit stops the scan; dotted tokens are
# unaffected, so the Local.LW0 form still collects a name)
_VERNAC_STOP = frozenset((
    "Require", "From", "Import", "Export", "Definition", "Theorem",
    "Lemma", "Proof", "Qed", "Inductive", "CoInductive", "Fixpoint",
    "CoFixpoint", "Example", "Corollary", "Proposition", "Remark", "Fact",
    "Record", "Class", "Instance", "Module", "Section", "End", "Variable",
    "Variables", "Context", "Hypothesis", "Parameter", "Parameters",
    "Axiom", "Conjecture", "Notation", "Infix", "Reserved", "Ltac",
    "Hint", "Declare", "Load", "Canonical", "Coercion", "Include",
))


def _strip_coq_comments(text):
    """Strip Coq block comments ((* ... *), nested) and string literals ("..."
    with \\ escapes) in one pass.

    A Require inside a comment must never be recorded, and neither must a
    prose Require inside a string literal: the live file
    `ConstructiveWorld_Live/UpReqIndex.v:2821` carries three
    `"FA-D1S12 … zero Require on mother …"` literals that once pushed the six
    prose words on/mother/of/six/face/delta into the findings as false names;
    one-pass stripping removes the defect.
    """
    out = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "(" and text[i:i + 2] == "(*":
            depth = 1
            i += 2
            while i < n and depth:
                if text[i:i + 2] == "(*":
                    depth += 1
                    i += 2
                elif text[i:i + 2] == "*)":
                    depth -= 1
                    i += 2
                else:
                    i += 1
            out.append(" ")
        elif ch == '"':
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            out.append(" ")
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def parse_requires(text):
    """Parse every Require statement form -> an ordered
    [(module, from_prefix, verb)] list.

    Collects `Require A B.`, `Require Import A B.`, `Require Export A B.`,
    `From X Require Import A B.` and their multi-name/multi-line forms
    (statement-level scan to the terminator, re.S); block comments are
    stripped first; the name region is scanned token by token and stops safely
    at a terminator, an unparseable token, or a bare stop word.
    """
    text = _strip_coq_comments(text)
    out = []
    for head in _REQ_HEAD_RE.finditer(text):
        frm = head.group("frm")
        verb = (head.group("verb") or "").strip()
        pos = head.end()
        while pos < len(text):
            while pos < len(text) and text[pos].isspace():
                pos += 1
            if pos >= len(text):
                break  # statement open at EOF with no terminator: keep the names collected so far, emit no garbage
            ch = text[pos]
            if ch == ".":
                break  # statement terminator
            tok_m = _REQ_NAME_RE.match(text, pos)
            if not tok_m:
                break  # unparseable name region such as an export list (x y): stop safely, the collected names stand
            tok = tok_m.group(0)
            if "." not in tok and tok in _VERNAC_STOP:
                break  # name region overrun by a malformed statement: a bare vernacular word stops the scan
            out.append((tok, frm, verb))
            pos = tok_m.end()
    return out


_WORLD_INDEX_MEMO = {}


def world_index(world_dir):
    """world_dir -> the set of relative .v/.vo paths (full os.walk index,
    cached per abspath within the process)."""
    root = os.path.abspath(world_dir)
    hit = _WORLD_INDEX_MEMO.get(root)
    if hit is not None:
        return hit
    files = set()
    for dirpath, _dirs, fnames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        for fn in fnames:
            if fn.endswith(".v") or fn.endswith(".vo"):
                rel = fn if rel_dir == "." else os.path.join(rel_dir, fn)
                files.add(rel.replace(os.sep, "/"))
    _WORLD_INDEX_MEMO[root] = files
    return files


def _in_world(name, files):
    """Existence closure: a dotted path expands to `/` form and closes when it
    equals an indexed file or ends one as `/path` for either suffix.

    The suffix comparison carries the `/` anchor (whole-word discipline again,
    guarding prefix over-matching): a world holding sub/UpReqBanachExp.v does
    not close UpReqBanach.
    """
    rel = "/".join(name.split("."))
    for suf in (".v", ".vo"):
        if rel + suf in files:
            return True
    for suf in (".v", ".vo"):
        tail = "/" + rel + suf
        for f in files:
            if f.endswith(tail):
                return True
    return False


def audit_requires(file, world_dir, stats=None):
    """Require-face audit of one .v file.

    The three-part method: parse_requires parses every statement form,
    STDLIB_ROOTS exempts by first name segment, world_index supplies the
    existence closure.  Returns the findings list (dict code/name/detail,
    same shape as audit()); REQ-GAP = a non-exempt Require with no .v/.vo
    counterpart inside the world (an in-tree gap).  A missing file or
    world_dir raises MissingPath (fail loud, no simulation).  Passing a dict
    as stats fills the three counters require_names/stdlib_exempt/
    tree_checked (optional, None by default).
    """
    if not os.path.isfile(file):
        raise MissingPath("--requires file missing: %s" % file)
    if not os.path.isdir(world_dir):
        raise MissingPath("--world directory missing: %s" % world_dir)
    with io.open(file, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    parsed = parse_requires(text)
    files = world_index(world_dir)
    findings = []
    seen = set()
    n_exempt = 0
    for name, _frm, verb in parsed:
        if name.split(".")[0] in STDLIB_ROOTS:
            n_exempt += 1
            continue  # Stdlib allowlist exemption: never judged as an in-tree gap
        if name in seen:
            continue
        seen.add(name)
        if not _in_world(name, files):
            findings.append({
                "code": "REQ-GAP", "name": name,
                "detail": "Require%s gap: the world %s holds no %s.v/.vo"
                          " (negative on the full-index existence check; the"
                          " Stdlib allowlist already exempted the rest)"
                          % ((" Export" if verb == "Export" else ""),
                             os.path.basename(os.path.normpath(world_dir)), name)})
    if stats is not None:
        stats["require_names"] = len(parsed)
        stats["stdlib_exempt"] = n_exempt
        stats["tree_checked"] = len(seen)
    return findings


def selftest():
    """Embedded vector set (temp-file driven): clean, in-batch duplicate,
    cross-batch collision, not-in-order, duplicate roster rows, grep two-way
    verdict, three-name-form normalization, usage and missing-path codes."""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_selectaudit_self_")
    try:
        order = os.path.join(tmp, "order.txt")
        with io.open(order, "w", encoding="utf-8") as fh:
            fh.write("S01_BaseRing.v#R0-d66910\n"
                     "S02_CauchyComplete.v#R0-d66910\n"
                     "S03_QExp.v#R0-d66910\n"
                     "HansonLcm.v#R0-d66910\n"
                     "zzm1_gauss.v\n"
                     "Local/LW0LeibSeparation.v#R160-eb42d3\n")

        def run(args):
            return subprocess_run([sys.executable, "-B",
                                   os.path.join(os.path.dirname(os.path.abspath(__file__)), PROG + ".py")] + args)

        b1 = os.path.join(tmp, "b1.txt")
        with io.open(b1, "w", encoding="utf-8") as fh:
            fh.write("# candidate batch\nS03_QExp.v#R2-abc\nzzm1_gauss.v\nLocal/LW0LeibSeparation.v\n")
        # 1. clean: the three name forms converge (#-tag, bare name, .v suffix,
        #    /-path form) -> rc 0 CLEAN
        p = run(["--order", order, "--select", b1])
        assert p.returncode == 0, "clean must return rc=0, measured %d\n%s" % (p.returncode, p.stdout)
        assert "AUDIT-CLEAN" in p.stdout, p.stdout

        # 2. in-batch duplicate negative -> rc 1, DUP-BATCH
        dupb = os.path.join(tmp, "dupb.txt")
        with io.open(dupb, "w", encoding="utf-8") as fh:
            fh.write("HansonLcm.v\nHansonLcm\n")
        p = run(["--order", order, "--select", dupb])
        assert p.returncode == 1 and "DUP-BATCH" in p.stdout, p.stdout

        # 3. cross-batch collision negative -> rc 1, DUP-CROSS
        b2 = os.path.join(tmp, "b2.txt")
        with io.open(b2, "w", encoding="utf-8") as fh:
            fh.write("zzm1_gauss\nHansonLcm.v\n")
        p = run(["--order", order, "--select", b1, "--select", b2])
        assert p.returncode == 1 and "DUP-CROSS" in p.stdout, p.stdout
        assert "zzm1_gauss" in p.stdout, p.stdout

        # 4. not-in-order negative -> rc 1, NOT-IN-ORDER
        ghost = os.path.join(tmp, "ghost.txt")
        with io.open(ghost, "w", encoding="utf-8") as fh:
            fh.write("From_Memory_Only.v\n")
        p = run(["--order", order, "--select", ghost])
        assert p.returncode == 1 and "NOT-IN-ORDER" in p.stdout, p.stdout

        # 5. duplicate roster row negative -> rc 1, DUP-ORDER
        order_dup = os.path.join(tmp, "order_dup.txt")
        with io.open(order_dup, "w", encoding="utf-8") as fh:
            fh.write("A_Mod.v\nB_Mod.v\nA_Mod.v#R1-ffff\n")
        bd = os.path.join(tmp, "bd.txt")
        with io.open(bd, "w", encoding="utf-8") as fh:
            fh.write("B_Mod\n")
        p = run(["--order", order_dup, "--select", bd])
        assert p.returncode == 1 and "DUP-ORDER" in p.stdout and "A_Mod" in p.stdout, p.stdout

        # 6. --grep two-way: hit rc 0 with per-row output; miss rc 1; whole-word,
        #    no prefix over-match
        p = run(["--order", order, "--grep", "HansonLcm"])
        assert p.returncode == 0 and "HansonLcm.v#R0-d66910" in p.stdout, p.stdout
        p = run(["--order", order, "--grep", "No_Such_Mod"])
        assert p.returncode == 1, "grep miss must return rc=1, measured %d" % p.returncode
        # prefix guard: grep S01_BaseRing hits exactly 1 row and never pulls the S03 row
        p = run(["--order", order, "--grep", "S01_BaseRing"])
        hit_lines = [l for l in p.stdout.splitlines() if l.startswith("ORDER-HIT")]
        assert p.returncode == 0 and len(hit_lines) == 1 \
            and "S03" not in p.stdout, p.stdout

        # 7. usage/missing paths: no --select and no --grep -> rc 2; order
        #    missing -> rc 9
        p = run(["--order", order])
        assert p.returncode == 2, "missing --select must return rc=2, measured %d" % p.returncode
        p = run(["--select", b1])
        assert p.returncode == 2, "--select without --order must return rc=2, measured %d" % p.returncode
        p = run(["--order", os.path.join(tmp, "nope.txt"), "--select", b1])
        assert p.returncode == 9, "missing --order file must return rc=9, measured %d" % p.returncode

        # 8. prefix guard in the audit body: selecting UpReqBanach must not
        #    accept UpReqBanachExp as in-tree
        order_pfx = os.path.join(tmp, "order_pfx.txt")
        with io.open(order_pfx, "w", encoding="utf-8") as fh:
            fh.write("UpReqBanachExp.v\n")
        bp = os.path.join(tmp, "bp.txt")
        with io.open(bp, "w", encoding="utf-8") as fh:
            fh.write("UpReqBanach\n")
        p = run(["--order", order_pfx, "--select", bp])
        assert p.returncode == 1 and "NOT-IN-ORDER" in p.stdout \
            and "UpReqBanachExp" not in p.stdout, p.stdout

        # 9. Require-face RED: the allowlist exempts
        #    QArith/Lia/List/Extraction/Lqa/Morphisms, the multi-name/multi-line/
        #    From/Export forms all parse, the comment-face Require is stripped,
        #    and the closure finds exactly two gaps (UpReqBanach must not
        #    over-match UpReqBanachExp.v)
        rw = os.path.join(tmp, "reqworld")
        os.makedirs(os.path.join(rw, "sub"))
        for fn, content in (("A.v", "Module A. End A.\n"),
                            ("UpReqBanachExp.v", "Module E. End E.\n"),
                            (os.path.join("sub", "B.v"), "Module B. End B.\n"),
                            (os.path.join("sub", "C.vo"), "fakevo\n")):
            with io.open(os.path.join(rw, fn), "w", encoding="utf-8") as fh:
                fh.write(content)
        reqf = os.path.join(tmp, "req.v")
        with io.open(reqf, "w", encoding="utf-8") as fh:
            fh.write("(* Require Import Ghost. a Require inside a comment must not be recorded *)\n"
                     "From Stdlib Require Import\n"
                     "     QArith.QArith\n"
                     "     List.List.\n"
                     "Require Export Lia.\n"
                     "Require Import Lqa Morphisms Extraction.\n"
                     "From Foo Require Import A.\n"
                     "Require Export sub.B.\n"
                     "Require sub.C.\n"
                     "Require Import UpReqBanach.\n"
                     "From Local Require Import Missing_Mod.\n")
        p = run(["--requires", reqf, "--world", rw])
        gap_lines = [l for l in p.stdout.splitlines() if l.startswith("FINDING REQ-GAP")]
        assert p.returncode == 1 and "REQ-GAP" in p.stdout, p.stdout
        assert "UpReqBanach" in p.stdout and "Missing_Mod" in p.stdout, p.stdout
        assert "Ghost" not in p.stdout, "the comment-face Require leaked into the findings\n" + p.stdout
        assert len(gap_lines) == 2, "exactly two gaps expected (UpReqBanach/Missing_Mod)\n" + p.stdout
        assert "stdlib_exempt=6" in p.stdout, p.stdout

        # 10. Require-face CLEAN and usage/missing paths: all-exempt batch ->
        #     REQUIRES-CLOSED rc 0; --requires without --world -> rc 2; missing
        #     file/world -> rc 9
        req_std = os.path.join(tmp, "req_std.v")
        with io.open(req_std, "w", encoding="utf-8") as fh:
            fh.write("Require Import QArith.\nRequire Export Lia.\n")
        p = run(["--requires", req_std, "--world", rw])
        assert p.returncode == 0 and "REQUIRES-CLOSED" in p.stdout, p.stdout
        # string-literal vector: the prose Require inside a string literal (the
        # `ConstructiveWorld_Live/UpReqIndex.v:2821` form) stays unrecorded;
        # the bare/short-path Stdlib names (Lists.List/PeanoNat/Permutation/
        # QArith_base/Qring/ZArithRing/micromega.Lqa, each verified present
        # under the toolchain Stdlib/** tree) are exempt -> CLOSED against the
        # small world too
        req_str = os.path.join(tmp, "req_str.v")
        with io.open(req_str, "w", encoding="utf-8") as fh:
            fh.write('"FA-D1S12 pack: zero Require on mother, slot reconciliation."\n'
                     "Require Import Lists.List PeanoNat Permutation.\n"
                     "Require Import QArith_base Qring Qfield Qabs ZArithRing.\n"
                     "Require Import String Ascii Wf_nat.\n"
                     "Require Import micromega.Lqa.\n")
        p = run(["--requires", req_str, "--world", rw])
        assert p.returncode == 0 and "REQUIRES-CLOSED" in p.stdout, p.stdout
        assert "mother" not in p.stdout and "reconciliation" not in p.stdout, p.stdout
        p = run(["--requires", req_std])
        assert p.returncode == 2, "--requires without --world must return rc=2, measured %d" % p.returncode
        p = run(["--requires", os.path.join(tmp, "nope.v"), "--world", rw])
        assert p.returncode == 9, "missing --requires file must return rc=9, measured %d" % p.returncode
        p = run(["--requires", req_std, "--world", os.path.join(tmp, "noworld")])
        assert p.returncode == 9, "missing --world directory must return rc=9, measured %d" % p.returncode

        print("SELECT-AUDIT-SELFTEST PASS: clean/in-batch duplicate/cross-batch "
              "collision/not-in-order/duplicate roster rows/grep two-way/no "
              "prefix over-match/usage 2/missing 9/Require-face RED/Require-face "
              "CLEAN+usage+string-literal stripping+bare-form allowlist - "
              "all eleven checks pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def subprocess_run(argv):
    import subprocess
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="batch-selection auditor: candidate selection"
                               " lists checked against a full-table grep of the"
                               " tree's order.txt, plus the Require-face audit")
    ap.add_argument("--order", default=None, help="the certified tree's order.txt"
                   " table (read-only; required for the select/grep forms)")
    ap.add_argument("--select", action="append", default=[], metavar="BATCH_FILE",
                    help="candidate selection file (repeatable = multiple"
                    " batches; feeds the cross-batch collision check)")
    ap.add_argument("--grep", default=None, help="single-name full-table grep"
                    " (the mechanical stand-in for a full read)")
    ap.add_argument("--requires", default=None, metavar="FILE.v",
                    help="the Require-face audit target file (statement-level"
                    " parsing with allowlist exemption and world closure)")
    ap.add_argument("--world", default=None, metavar="WORLD_DIR",
                    help="world directory paired with --requires (the .v/.vo"
                    " existence-closure surface)")
    ap.add_argument("--json", default=None, help="audit JSON report path")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # the --requires + --world audit form (independent of the order/select/grep forms)
    if args.requires:
        if not args.world:
            print("FAIL-LOUD: --requires requires --world <world-dir>"
                  " (the .v/.vo existence-closure surface)", file=sys.stderr)
            sys.exit(2)
        stats = {}
        try:
            findings = audit_requires(args.requires, args.world, stats)
        except MissingPath as e:
            print("FAIL-LOUD: %s" % e, file=sys.stderr)
            sys.exit(9)
        print("REQUIRES-AUDIT file=%s world=%s require_names=%d "
              "stdlib_exempt=%d tree_checked=%d"
              % (args.requires, args.world, stats.get("require_names", 0),
                 stats.get("stdlib_exempt", 0), stats.get("tree_checked", 0)))
        for f in findings:
            print("FINDING %-12s %s — %s" % (f["code"], f["name"], f["detail"]))
        if findings:
            print("REQUIRES-RED: %d in-tree gaps (exit 1; add the missing"
                  " module or extend the STDLIB_ROOTS allowlist)"
                  % len(findings))
        else:
            print("REQUIRES-CLOSED: the Require face is fully closed (every"
                  " statement form parsed; Stdlib allowlist exemption; world"
                  " .v/.vo existence closure)")
        sys.exit(1 if findings else 0)

    if not args.order:
        print("FAIL-LOUD: the select/grep forms require --order <order.txt>", file=sys.stderr)
        sys.exit(2)

    try:
        if args.grep:
            if not os.path.isfile(args.order):
                print("FAIL-LOUD: --order file missing: %s" % args.order, file=sys.stderr)
                sys.exit(9)
            with io.open(args.order, encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
            try:
                name = normalize_line(args.grep)
            except AuditError as e:
                print("FAIL-LOUD: %s" % e, file=sys.stderr)
                sys.exit(2)
            hits = grep_rows(lines, name)
            print("GREP %s full-table hits on %d row(s):" % (name, len(hits)))
            for h in hits:
                print("ORDER-HIT %s" % h)
            sys.exit(0 if hits else 1)

        if not args.select:
            print("FAIL-LOUD: give --select or --grep (nothing to audit)", file=sys.stderr)
            sys.exit(2)
        order_names = read_names(args.order, "--order")
        batches = [(p, read_names(p, "--select")) for p in args.select]
    except MissingPath as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    except AuditError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    print("SELECT-AUDIT order=%s order_rows=%d order_names=%d batches=%d selected=%d"
          % (args.order, len(order_names), len(set(order_names)), len(batches),
             sum(len(n) for _, n in batches)))
    findings = audit(order_names, batches)
    for f in findings:
        print("FINDING %-12s %s — %s" % (f["code"], f["name"], f["detail"]))
    if findings:
        print("AUDIT-RED: %d findings (exit 1; deduplicate and resubmit)" % len(findings))
        verdict = "RED"
    else:
        print("AUDIT-CLEAN: zero findings across the four checks (full-table"
              " read; no in-batch duplicates; no cross-batch collisions; every"
              " selection in the roster)")
        verdict = "CLEAN"

    if args.json:
        acc = {"order": args.order,
               "order_rows": len(order_names), "order_names": len(set(order_names)),
               "batches": [{"path": p, "count": len(n), "names": n} for p, n in batches],
               "findings": findings, "verdict": verdict}
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)

    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
