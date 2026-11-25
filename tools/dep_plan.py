#!/usr/bin/env python3
"""dep_plan.py - dry-run dependency re-plan: given a census document
(schema rocqwash.dep-map/1) and a retirement target module, produce the
plan of which consumer Require line re-points to which replacement.

Purpose.  The census tool (tools/dep_census.py) lists every consumer and
its Require targets.  This tool turns a retirement target into a concrete,
deterministic plan document (schema rocqwash.dep-plan/1): for each consumer
that requires the target, one entry with the original line number, the
original statement text, the proposed action (repoint / blocked) and the
rewritten statement when a replacement is given.  By default the tool
writes nothing; only --apply produces files, and only under the
caller-named --out directory (a mirrored subtree, never the repository).

Interface.
  `python -B tools/dep_plan.py --census <dep-map.json> --target Mod.Name`
  `python -B tools/dep_plan.py --census <dep-map.json> --target M --replacement N`
  `python -B tools/dep_plan.py ... --roots <dir> --out <dir> --apply`
  `python -B tools/dep_plan.py --selftest`

Exit codes.
  0  success (including an empty plan when the target is unreferenced)
  1  fail-loud (unreadable inputs, invalid schema, selftest failure)
  2  usage error (bad arguments, scope-guard refusal)

Safety.  Zero network, stdlib only, read-only over inputs; the only write
path is --apply into the caller-named --out directory, which the scope
guard refuses when it sits inside any scan root.  Determinism: no wall
clock, no random, sorted output - equal inputs produce byte-identical
plans.  Line numbers refer to the original file (comments are masked with
offset preservation, not deleted), so an applier can act without re-search.

Dependencies.  Python 3 standard library only.
"""
import argparse
import json
import os
import re
import sys

SCHEMA = "rocqwash.dep-plan/1"
CENSUS_SCHEMA = "rocqwash.dep-map/1"

_REQUIRE_RE = re.compile(
    r"^(\s*)Require\s+(Export\s+|Import\s+)?"
    "((?:[A-Za-z_][A-Za-z0-9_']*)"
    "(?:\\.(?:[A-Za-z_][A-Za-z0-9_']*))*)"
    r"(\s*\.\s*)$"
)
_FROM_REQUIRE_RE = re.compile(
    r"^(\s*)From\s+(.+?)\s+Require\s+(?:Export\s+|Import\s+)?"
    "((?:[A-Za-z_][A-Za-z0-9_']*)"
    "(?:\\.(?:[A-Za-z_][A-Za-z0-9_']*))*)"
    r"(\s*\.\s*)$"
)


def mask_comment_spans(text):
    """Blank out Rocq (* ... *) comment interiors, nested-aware.

    Offset-preserving twin of the wash_shape strip discipline: comment
    characters become spaces except newlines, so indices and line numbers
    in the masked text equal the original text.  A commented-out Require
    therefore cannot match, and a live Require keeps its true line number.
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


def find_target_lines(masked, target):
    """Return [(line_no, whole_line, kind, module_token)] for the target.

    kind is plain or from_qualified; module_token is the exact module text
    the statement names (for from_qualified it is the tail after From).
    line_no is 1-based and refers to the original file.
    """
    hits = []
    for idx, line in enumerate(masked.splitlines(), start=1):
        m = _REQUIRE_RE.match(line)
        if m and m.group(3) == target:
            hits.append((idx, line.rstrip("\n"), "plain", m.group(3)))
            continue
        m2 = _FROM_REQUIRE_RE.match(line)
        if m2 and (m2.group(2) + "." + m2.group(3)) == target:
            hits.append((idx, line.rstrip("\n"), "from_qualified",
                         m2.group(3)))
    return hits


def scope_guard(out_dir, roots):
    """Refuse an --out directory inside any scan root (fail-loud rc 2).

    Equivalent local rewrite of the read-only scope determination
    (repair_scope does not exist on this lineage, so the guard is a pure
    local function: refuse when the resolved out path equals or is inside
    any resolved root, or when any root equals or is inside the out path,
    which would make apply read and write the same tree).
    """
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


def build_plan(census, target, replacement, roots, masked_reader):
    """Build the plan document for retiring target.

    census is a parsed rocqwash.dep-map/1 document; roots is the list of
    scan roots to reread consumers from (the census carries absolute
    paths); masked_reader maps a consumer path to its masked text (shared
    across plan and selftest so vectors need no disk).
    """
    entries = []
    consumers = sorted(census.get("dependencies", {}).keys())
    for consumer in consumers:
        deps = census["dependencies"][consumer]
        if target not in deps:
            continue
        masked = masked_reader(consumer)
        for line_no, whole, kind, token in find_target_lines(masked, target):
            if kind == "from_qualified":
                # rewriting the tail under a foreign From prefix changes
                # resolution semantics; without a matching prefix the only
                # honest action is blocked (kept for the applier to report)
                entry = {
                    "consumer": consumer,
                    "line": line_no,
                    "statement": whole,
                    "action": "blocked",
                    "reason": "from_qualified require; give a replacement "
                              "under the same From prefix or retire the "
                              "From clause explicitly",
                }
            elif replacement:
                new_line = _REQUIRE_RE.sub(
                    lambda m: m.group(1) + "Require "
                    + (m.group(2) or "Import ") + replacement + m.group(4),
                    whole)
                entry = {
                    "consumer": consumer,
                    "line": line_no,
                    "statement": whole,
                    "action": "repoint",
                    "statement_after": new_line,
                    "replacement": replacement,
                }
            else:
                entry = {
                    "consumer": consumer,
                    "line": line_no,
                    "statement": whole,
                    "action": "blocked",
                    "reason": "no replacement given",
                }
            entries.append(entry)
    entries.sort(key=lambda e: (e["consumer"], e["line"]))
    doc = {
        "schema": SCHEMA,
        "census_schema": census.get("schema"),
        "target": target,
        "replacement": replacement or None,
        "entries": entries,
        "counts": {
            "repoint": sum(1 for e in entries if e["action"] == "repoint"),
            "blocked": sum(1 for e in entries if e["action"] == "blocked"),
        },
    }
    return doc


def write_apply(doc, out_dir, roots, read_text):
    """Materialise repoint entries as a mirrored subtree under out_dir.

    Only files with at least one repoint entry are written; consumers with
    blocked entries only are NOT written (an honest applier must not guess
    the fix).  Returns the list of written relative paths.
    """
    by_consumer = {}
    for e in doc["entries"]:
        if e["action"] == "repoint":
            by_consumer.setdefault(e["consumer"], []).append(e)
    written = []
    root_abs = os.path.abspath(roots[0])
    for consumer in sorted(by_consumer):
        text = read_text(consumer)
        masked = mask_comment_spans(text)
        lines = text.splitlines(True)
        for e in sorted(by_consumer[consumer], key=lambda x: -x["line"]):
            lines[e["line"] - 1] = e["statement_after"] + "\n"
        rel = os.path.relpath(os.path.abspath(consumer), root_abs)
        if rel.startswith(".." + os.sep) or os.path.isabs(rel):
            raise FailLoud(1, "consumer outside scan root, refusing to "
                              "mirror: %s" % consumer)
        dest = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dest) or out_dir, exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="") as fh:
            fh.write("".join(lines))
        written.append(rel)
    return sorted(written)


# ---------------------------------------------------------------------------
# Selftest (in-process vectors; no disk, no network)
# ---------------------------------------------------------------------------

_V_PLAIN = "Require Import OldList.\nRequire Export Arith.\n"
_V_TARGET_ABSENT = "Require Import List.\n"
_V_COMMENTED = "(* Require Import OldList *)\nRequire Import Reals.\n"
_V_FROM = "From Coq.Numbers.Calc Require Import NatInt.\n"
_V_MIXED = _V_PLAIN + "From Coq Require Import OldList.\n"


def _census_for(text):
    return {"schema": CENSUS_SCHEMA,
            "dependencies": {"fake/consumer.v": ["OldList", "Arith"]
                             if "OldList" in text or "Arith" in text
                             else []}}


def _selftest():
    ok = True
    def check(label, cond):
        nonlocal ok
        if not cond:
            print("SELFTEST FAIL %s" % label, file=sys.stderr)
            ok = False

    # 1 plain repoint: line number and rewritten statement
    doc = build_plan(_census_for(_V_PLAIN), "OldList", "NewList",
                     ["fake"], lambda p: mask_comment_spans(_V_PLAIN))
    check("plain-entry", len(doc["entries"]) == 1
          and doc["entries"][0]["action"] == "repoint")
    check("plain-line", doc["entries"][0]["line"] == 1)
    check("plain-after",
          doc["entries"][0]["statement_after"] == "Require Import NewList.")

    # 2 target unreferenced -> empty plan, rc path stays success
    doc2 = build_plan({"schema": CENSUS_SCHEMA,
                       "dependencies": {"a.v": ["List"]}},
                      "OldList", None, [], lambda p: "")
    check("empty-plan", doc2["entries"] == []
          and doc2["counts"] == {"repoint": 0, "blocked": 0})

    # 3 commented-out require is ignored (offset-preserving mask)
    masked = mask_comment_spans(_V_COMMENTED)
    check("comment-ignored",
          find_target_lines(masked, "OldList") == []
          and masked.count("\n") == _V_COMMENTED.count("\n"))
    check("comment-offsets", len(masked) == len(_V_COMMENTED))

    # 4 from-qualified require -> blocked (conservative, honest)
    doc4 = build_plan(
        {"schema": CENSUS_SCHEMA,
         "dependencies": {"c.v": ["Coq.Numbers.Calc.NatInt"]}},
        "Coq.Numbers.Calc.NatInt", "Other.NatInt", [],
        lambda p: mask_comment_spans(_V_FROM))
    check("from-blocked", len(doc4["entries"]) == 1
          and doc4["entries"][0]["action"] == "blocked"
          and doc4["entries"][0]["line"] == 1)

    # 5 scope refusal: out dir inside scan root
    check("scope-inside",
          scope_guard(os.path.join("root", "out"), ["root"]) is not None)
    check("scope-equal", scope_guard("root", ["root"]) is not None)
    check("scope-outside-ok",
          scope_guard("elsewhere", ["root"]) is None)

    # 6 idempotent recompute: plan over an already-replanned census is empty
    after = {"schema": CENSUS_SCHEMA,
             "dependencies": {"fake/consumer.v": ["NewList", "Arith"]}}
    doc6 = build_plan(after, "OldList", "NewList", [],
                      lambda p: mask_comment_spans(_V_PLAIN.replace(
                          "OldList", "NewList")))
    check("idempotent", doc6["entries"] == [])

    # 7 no replacement -> blocked with reason
    doc7 = build_plan(_census_for(_V_PLAIN), "OldList", None, [],
                      lambda p: mask_comment_spans(_V_PLAIN))
    check("no-replacement-blocked", doc7["entries"][0]["action"] == "blocked"
          and "reason" in doc7["entries"][0])

    # 8 mixed plain + from: the from-qualified line names Coq.OldList, a
    # different module; only the plain line matches target OldList
    doc8 = build_plan(_census_for(_V_MIXED), "OldList", "NewList", [],
                      lambda p: mask_comment_spans(_V_MIXED))
    check("mixed-no-cross-match",
          [e["action"] for e in doc8["entries"]] == ["repoint"]
          and [e["line"] for e in doc8["entries"]] == [1])

    # 9 determinism: same inputs -> byte-identical documents
    dA = json.dumps(build_plan(_census_for(_V_PLAIN), "OldList", "NewList",
                               [], lambda p: mask_comment_spans(_V_PLAIN)),
                    sort_keys=True)
    dB = json.dumps(build_plan(_census_for(_V_PLAIN), "OldList", "NewList",
                               [], lambda p: mask_comment_spans(_V_PLAIN)),
                    sort_keys=True)
    check("determinism", dA == dB)

    if ok:
        print("DEP-PLAN-SELFTEST PASS (%d vector groups)" % 9)
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class FailLoud(Exception):
    def __init__(self, rc, msg):
        super().__init__(msg)
        self.rc = rc
        self.msg = msg


def _read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def main(argv):
    ap = argparse.ArgumentParser(
        description="dry-run dependency re-plan over a rocqwash.dep-map/1 "
                    "census; writes nothing unless --apply with --out")
    ap.add_argument("--census", help="path to the rocqwash.dep-map/1 JSON")
    ap.add_argument("--target", help="module name to retire (dotted ok)")
    ap.add_argument("--replacement", default=None,
                    help="module the consumers re-point to")
    ap.add_argument("--roots", default=None,
                    help="comma-separated scan roots backing the census "
                         "(required for --apply; used by the scope guard)")
    ap.add_argument("--out", default=None,
                    help="output directory for the plan (and the mirrored "
                         "patched tree under --apply)")
    ap.add_argument("--apply", action="store_true",
                    help="materialise repoint entries under --out")
    ap.add_argument("--selftest", action="store_true",
                    help="run the in-process fixture vector groups")
    args = ap.parse_args(argv)

    if args.selftest:
        sys.exit(_selftest())
    if not args.census or not args.target:
        raise FailLoud(2, "--census and --target are required")
    if args.apply and (not args.out or not args.roots):
        raise FailLoud(2, "--apply requires both --out and --roots")
    if args.apply and not os.path.isdir(args.out):
        raise FailLoud(2, "--out must be an existing directory (the caller "
                          "creates it; the tool never mkdirs outside it)")

    try:
        with open(args.census, "r", encoding="utf-8") as fh:
            census = json.load(fh)
    except (OSError, ValueError) as exc:
        raise FailLoud(1, "unreadable census: %s" % exc)
    if census.get("schema") != CENSUS_SCHEMA:
        raise FailLoud(1, "census schema mismatch: %r" % census.get("schema"))

    roots = [r.strip() for r in (args.roots or "").split(",") if r.strip()]
    if args.apply:
        refusal = scope_guard(args.out, roots)
        if refusal:
            raise FailLoud(2, "scope guard refusal: %s" % refusal)

    def masked_reader(consumer):
        try:
            return mask_comment_spans(_read_text(consumer))
        except OSError as exc:
            raise FailLoud(1, "unreadable consumer %s: %s" % (consumer, exc))

    doc = build_plan(census, args.target, args.replacement, roots,
                     masked_reader)
    text = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out and not args.apply:
        dest = os.path.join(args.out, "dep-plan.json")
        with open(dest, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("plan written: %s (%d repoint, %d blocked)"
              % (dest, doc["counts"]["repoint"], doc["counts"]["blocked"]))
    elif args.out and args.apply:
        plan_dest = os.path.join(args.out, "dep-plan.json")
        with open(plan_dest, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        written = write_apply(doc, args.out, roots, _read_text)
        print("plan + patched tree written under %s (%d repoint, "
              "%d blocked, %d files written)"
              % (args.out, doc["counts"]["repoint"],
                 doc["counts"]["blocked"], len(written)))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except FailLoud as exc:
        print("FAIL-LOUD: %s" % exc.msg, file=sys.stderr)
        sys.exit(exc.rc)
