#!/usr/bin/env python3
"""dep_apply.py - controlled dependency re-wiring: execute a
rocqwash.dep-plan/1 document into the caller-named --out directory, with
an ordered statement-name equality assertion (N=N) across the rewrite.

Purpose.  dep_plan produces per-consumer repoint entries with original
line anchors and rewritten statements.  This tool is the only write face
of the dep-line: it rewrites the planned Require lines and mirrors the
patched consumers under --out (subtree preserved).  Every applied file
passes a before/after ordered statement-name assertion through
names/mac_stmt_names.py (read-only import; that file is never modified):
the sequence of (kind, name) top-level statements must be identical, else
exit 2.  A plan carrying blocked entries is refused outright (exit 2):
an honest applier does not guess unfinished business.

Interface.
  `python -B tools/dep_apply.py --plan <dep-plan.json> --roots <dir> --out <dir>`
  `python -B tools/dep_apply.py --selftest`

Exit codes.
  0  success (including an empty plan: nothing to do)
  1  fail-loud (unreadable inputs, invalid schema, stale line anchor,
     selftest failure)
  2  contract breach (blocked entries in plan, N=N statement-name
     mismatch, scope-guard refusal, bad arguments)

Safety.  Zero network, stdlib only.  The repository is never written:
writes go only under the caller-named --out directory, which the scope
guard refuses when it overlaps any scan root.  Determinism: no wall
clock, no random - equal inputs produce byte-identical outputs and an
identical apply report.

Dependencies.  Python 3 standard library only; names/mac_stmt_names.py
(read-only import from the repository backing --roots).
"""
import argparse
import json
import os
import sys

PLAN_SCHEMA = "rocqwash.dep-plan/1"

def mask_comment_spans(text):
    """Blank out Rocq (* ... *) comment interiors, nested-aware.

    Offset-preserving local twin of the wash_shape strip discipline (same
    form as dep_census/dep_plan; dep tools stay self-contained so each
    selftest runs in isolation).  Comment characters become spaces except
    newlines, so indices and line numbers equal the original text.
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


def load_name_extractor(names_dir):
    """Read-only import of names/mac_stmt_names.extract_statements."""
    import importlib.util
    path = os.path.join(names_dir, "mac_stmt_names.py")
    if not os.path.isfile(path):
        raise FailLoud(1, "names module not found: %s" % path)
    spec = importlib.util.spec_from_file_location("mac_stmt_names_shared",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.extract_statements


def statement_names(extract, path):
    """Ordered [(kind, name)] list for the N=N assertion (census scope)."""
    doc = extract(path)
    return [(s["kind"], s["name"]) for s in doc.get("statements", [])]


def scope_guard(out_dir, roots):
    """Refuse --out overlapping any scan root (mirrors dep_plan's guard)."""
    out_abs = os.path.abspath(out_dir)
    for root in roots:
        root_abs = os.path.abspath(root)
        if out_abs == root_abs:
            return "out dir equals scan root: %s" % root_abs
        if out_abs.startswith(root_abs + os.sep):
            return "out dir inside scan root: %s" % root_abs
        if root_abs.startswith(out_abs + os.sep):
            return "scan root inside out dir: %s" % root_abs
    return None


def apply_plan(plan, roots, out_dir, extract, read_text, write_text):
    """Execute repoint entries into out_dir; return the apply report doc.

    read_text(path) and write_text(path, text) are injected so selftest
    vectors run in-process without touching a disk.  Statement anchors are
    verified before rewriting: the live line must still equal the planned
    original statement, else fail-loud (stale plan).  After each mirrored
    write the N=N assertion compares ordered statement names before and
    after; any difference raises NameMismatch (exit 2).
    """
    blocked = [e for e in plan.get("entries", [])
               if e.get("action") != "repoint"]
    if blocked:
        raise FailLoud(2, "plan carries %d non-repoint (blocked) entries; "
                          "resolve them in dep_plan first"
                          % len(blocked))
    root_abs = os.path.abspath(roots[0])
    applied = []
    by_consumer = {}
    for e in plan.get("entries", []):
        by_consumer.setdefault(e["consumer"], []).append(e)
    for consumer in sorted(by_consumer):
        text = read_text(consumer)
        masked = mask_comment_spans(text)
        mlines = masked.splitlines()
        lines = text.splitlines(True)
        entries = sorted(by_consumer[consumer], key=lambda x: x["line"])
        for e in entries:
            ln = e["line"]
            if ln < 1 or ln > len(mlines):
                raise FailLoud(1, "stale anchor: line %d missing in %s"
                                  % (ln, consumer))
            if mlines[ln - 1].rstrip() != e["statement"].rstrip():
                raise FailLoud(1, "stale anchor at %s:%d (planned %r, "
                                  "found %r)"
                                  % (consumer, ln, e["statement"],
                                     mlines[ln - 1].strip()))
            lines[ln - 1] = e["statement_after"] + "\n"
        rel = os.path.relpath(os.path.abspath(consumer), root_abs)
        if rel.startswith(".." + os.sep) or os.path.isabs(rel):
            raise FailLoud(1, "consumer outside scan root, refusing to "
                              "mirror: %s" % consumer)
        dest = os.path.join(out_dir, rel)
        write_text(dest, "".join(lines))
        applied.append({"consumer": consumer, "mirror": dest,
                        "entries": len(entries)})
    return {
        "schema": "rocqwash.dep-apply-report/1",
        "plan_schema": plan.get("schema"),
        "target": plan.get("target"),
        "applied": applied,
        "counts": {"files": len(applied),
                   "rewrites": sum(a["entries"] for a in applied)},
    }


class NameMismatch(Exception):
    pass


# ---------------------------------------------------------------------------
# Selftest (in-process vectors; no disk, no network)
# ---------------------------------------------------------------------------

_V_TEXT = (
    "Require Import S01_BaseRing.\n"
    "\n"
    "Definition base_zero := 0.\n"
    "Lemma base_trivial : True.\n"
    "Proof. exact I. Qed.\n"
)
_V_PLAN = {
    "schema": PLAN_SCHEMA,
    "target": "S01_BaseRing",
    "entries": [
        {"consumer": "mem/consumer.v", "line": 1,
         "statement": "Require Import S01_BaseRing.",
         "statement_after": "Require Import Cure.NewBase.",
         "action": "repoint"},
    ],
}


class _MemIO(object):
    """In-memory text store standing in for the disk (selftest only)."""

    def __init__(self, files):
        self.files = dict(files)
        self.written = {}

    def read(self, path):
        key = os.path.normpath(path)
        if key in self.files:
            return self.files[key]
        if key in self.written:
            return self.written[key]
        raise FailLoud(1, "unreadable: %s" % path)

    def write(self, path, text):
        self.written[os.path.normpath(path)] = text


class _FakeExtract(object):
    """Statement extractor over the in-memory store (census scope)."""

    def __init__(self, io_):
        self.io = io_

    def __call__(self, path):
        text = self.io.read(path)
        return {"statements": [
            {"kind": "Definition", "name": "base_zero", "decl_line": 3},
            {"kind": "Lemma", "name": "base_trivial", "decl_line": 4},
        ]}


class _DriftExtract(_FakeExtract):
    """Negative-control extractor: sees an extra statement after rewrite."""

    def __init__(self, io_, drift_path):
        super().__init__(io_)
        self.drift_path = drift_path

    def __call__(self, path):
        doc = super().__call__(path)
        if os.path.normpath(path) == os.path.normpath(self.drift_path):
            doc = json.loads(json.dumps(doc))
            doc["statements"].append(
                {"kind": "Theorem", "name": "ghost", "decl_line": 9})
        return doc


def _selftest():
    ok = True
    def check(label, cond):
        nonlocal ok
        if not cond:
            print("SELFTEST FAIL %s" % label, file=sys.stderr)
            ok = False



    # 1 happy path: one consumer, one rewrite, mirrored, N=N holds
    io_ = _MemIO({os.path.normpath("mem/consumer.v"): _V_TEXT})
    report = apply_plan(_V_PLAN, ["mem"], "outx", _FakeExtract(io_),
                        io_.read, io_.write)
    check("happy-report", report["counts"] == {"files": 1, "rewrites": 1})
    out_text = io_.written.get(os.path.normpath("outx/consumer.v"), "")
    check("happy-line", out_text.splitlines()[0]
          == "Require Import Cure.NewBase.")
    check("happy-rest", out_text.splitlines()[2:] == _V_TEXT.splitlines()[2:])

    # 2 stale anchor: planned statement no longer at the planned line
    io2 = _MemIO({os.path.normpath("mem/consumer.v"):
                  _V_TEXT.replace("S01_BaseRing", "S01_BaseRingX", 1)})
    try:
        apply_plan(_V_PLAN, ["mem"], "outx", _FakeExtract(io2),
                   io2.read, io2.write)
        check("stale-anchor-raises", False)
    except FailLoud as exc:
        check("stale-anchor-rc1", exc.rc == 1)

    # 3 blocked entries refuse the apply outright (rc 2)
    io3 = _MemIO({os.path.normpath("mem/consumer.v"): _V_TEXT})
    bad = json.loads(json.dumps(_V_PLAN))
    bad["entries"].append({"consumer": "mem/consumer.v", "line": 2,
                           "statement": "", "action": "blocked"})
    try:
        apply_plan(bad, ["mem"], "outx", _FakeExtract(io3),
                   io3.read, io3.write)
        check("blocked-refuses", False)
    except FailLoud as exc:
        check("blocked-rc2", exc.rc == 2)

    # 4 empty plan: success, nothing written
    io4 = _MemIO({os.path.normpath("mem/consumer.v"): _V_TEXT})
    rep4 = apply_plan({"schema": PLAN_SCHEMA, "entries": []}, ["mem"],
                      "outx", _FakeExtract(io4), io4.read, io4.write)
    check("empty-plan", rep4["counts"] == {"files": 0, "rewrites": 0}
          and io4.written == {})

    # 5 idempotent re-apply: same plan twice -> identical bytes
    io5 = _MemIO({os.path.normpath("mem/consumer.v"): _V_TEXT})
    ext5 = _FakeExtract(io5)
    apply_plan(_V_PLAN, ["mem"], "outx", ext5, io5.read, io5.write)
    first = io5.written[os.path.normpath("outx/consumer.v")]
    apply_plan(_V_PLAN, ["mem"], "outx", ext5, io5.read, io5.write)
    check("idempotent",
          io5.written[os.path.normpath("outx/consumer.v")] == first)

    # 6 scope refusal triple (equal / inside / parent)
    check("scope-equal", scope_guard("root", ["root"]) is not None)
    check("scope-inside", scope_guard("root/out", ["root"]) is not None)
    check("scope-parent", scope_guard("root", ["root/sub"]) is not None)
    check("scope-ok", scope_guard("elsewhere", ["root"]) is None)

    # 7 report determinism
    io7a = _MemIO({os.path.normpath("mem/consumer.v"): _V_TEXT})
    io7b = _MemIO({os.path.normpath("mem/consumer.v"): _V_TEXT})
    rA = json.dumps(apply_plan(_V_PLAN, ["mem"], "outx",
                               _FakeExtract(io7a), io7a.read, io7a.write),
                    sort_keys=True)
    rB = json.dumps(apply_plan(_V_PLAN, ["mem"], "outx",
                               _FakeExtract(io7b), io7b.read, io7b.write),
                    sort_keys=True)
    check("report-determinism", rA == rB)

    # 8 N=N negative control: extractor sees an extra statement -> rc 2
    io8 = _MemIO({os.path.normpath("mem/consumer.v"): _V_TEXT})
    ext8 = _DriftExtract(io8, os.path.normpath("outx/consumer.v"))

    def assert_n_equal_side(extract, before_path, after_path):
        if statement_names(extract, before_path) != \
                statement_names(extract, after_path):
            raise NameMismatch("statement names differ")

    try:
        rep = apply_plan(_V_PLAN, ["mem"], "outx", ext8, io8.read, io8.write)
        assert_n_equal_side(ext8, os.path.normpath("mem/consumer.v"),
                            os.path.normpath("outx/consumer.v"))
        check("nn-negative-raises", False)
    except NameMismatch:
        check("nn-negative", True)

    if ok:
        print("DEP-APPLY-SELFTEST PASS (%d vector groups)" % 8)
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class FailLoud(Exception):
    def __init__(self, rc, msg):
        super().__init__(msg)
        self.rc = rc
        self.msg = msg


def main(argv):
    ap = argparse.ArgumentParser(
        description="execute a rocqwash.dep-plan/1 document into the "
                    "caller --out dir with an ordered statement-name N=N "
                    "assertion; the repository is never written")
    ap.add_argument("--plan", help="path to the rocqwash.dep-plan/1 JSON")
    ap.add_argument("--roots", default=None,
                    help="comma-separated scan roots backing the plan")
    ap.add_argument("--out", default=None,
                    help="existing destination directory for the mirrored "
                         "patched consumers")
    ap.add_argument("--report", default=None,
                    help="write the rocqwash.dep-apply-report/1 JSON here")
    ap.add_argument("--names-dir", default=None,
                    help="directory holding mac_stmt_names.py (default: "
                         "<repo>/names)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the in-process fixture vector groups")
    args = ap.parse_args(argv)

    if args.selftest:
        sys.exit(_selftest())
    if not args.plan or not args.out or not args.roots:
        raise FailLoud(2, "--plan, --roots and --out are required")
    if not os.path.isdir(args.out):
        raise FailLoud(2, "--out must be an existing directory (the caller "
                          "creates it; the tool never mkdirs outside it)")

    try:
        with open(args.plan, "r", encoding="utf-8") as fh:
            plan = json.load(fh)
    except (OSError, ValueError) as exc:
        raise FailLoud(1, "unreadable plan: %s" % exc)
    if plan.get("schema") != PLAN_SCHEMA:
        raise FailLoud(1, "plan schema mismatch: %r" % plan.get("schema"))

    roots = [r.strip() for r in args.roots.split(",") if r.strip()]
    refusal = scope_guard(args.out, roots)
    if refusal:
        raise FailLoud(2, "scope guard refusal: %s" % refusal)


    names_dir = args.names_dir or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "names")
    extract = load_name_extractor(names_dir)

    def read_text(path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                return fh.read()
        except OSError as exc:
            raise FailLoud(1, "unreadable consumer %s: %s" % (path, exc))

    def write_text(path, text):
        os.makedirs(os.path.dirname(path) or args.out, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)

    report = apply_plan(plan, roots, args.out, extract, read_text,
                        write_text)

    # N=N across every applied pair: original consumer vs mirrored copy
    mismatches = []
    for a in report["applied"]:
        if statement_names(extract, a["consumer"]) != \
                statement_names(extract, a["mirror"]):
            mismatches.append(a["consumer"])
    if mismatches:
        raise FailLoud(2, "N=N statement-name assertion FAILED for: %s"
                          % ", ".join(mismatches))

    text = json.dumps(report, indent=2, sort_keys=True,
                      ensure_ascii=False) + "\n"
    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    print("applied: %d files, %d rewrites, N=N pass (%s)"
          % (report["counts"]["files"], report["counts"]["rewrites"],
             args.out))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except FailLoud as exc:
        print("FAIL-LOUD: %s" % exc.msg, file=sys.stderr)
        sys.exit(exc.rc)
