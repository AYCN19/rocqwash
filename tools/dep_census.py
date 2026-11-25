#!/usr/bin/env python3
"""dep_census.py - read-only dependency census: scan .v files, build a
consumer→provider map, and emit it as schema rocqwash.dep-map/1.

Purpose.  Every `.v` file in the scan set is a *consumer*: its `Require`
statements name the modules it depends on.  The census strips comments
(reusing the proven `strip_comment_spans` discipline from wash_shape.py,
rewritten here as a local pure function so that dep-line does not import
from the frozen wash chain), extracts the `Require` lines, normalises the
module names, and groups them by consumer file.  The output is a
deterministic JSON document (schema rocqwash.dep-map/1) that downstream
tools (dep_plan, dep_apply, dep_retire_verify) consume to reason about
dependency-retirement plans.

Interface.
  `python -B tools/dep_census.py --roots <dir>[,<dir>...] --out <file>`
  `python -B tools/dep_census.py --selftest`
  `python -B tools/dep_census.py --roots <dir> --out <file> --format text`

Exit codes.
  0  success (including empty map — zero Require statements found)
  1  fail-loud (unreadable input, invalid schema, selftest failure)
  2  usage error (bad arguments)
  9  internal error (should never reach the user)

Safety.  Zero network, stdlib only, read-only over input trees, the only
write is the caller-named --out file.  Determinism: no wall clock, no
random, sorted output keys — equal inputs produce byte-identical output
(acceptance R5 analogue).  --selftest runs an in-process fixture vector
group (no disk reads) and prints DEP-CENSUS-SELFTEST PASS on success.

Dependencies.  Python 3 standard library only.
"""
import argparse
import json
import os
import re
import sys

SCHEMA = "rocqwash.dep-map/1"

# Classification sets for the optional --classify leg (derived queue
# ticket DQ-1).  Rule order: in-repo stem match first (a local file
# shadows the library), then dotted stdlib prefixes, then the curated
# bare-name set, and everything else is honestly missing-provider.
STDLIB_PREFIXES = ("Coq.", "Stdlib.", "Rocq.")
STDLIB_BARE = frozenset((
    "List", "Arith", "QArith", "Reals", "Int", "ZArith", "Floats",
    "String", "Ascii", "PeanoNat", "Ring", "Field"))

# ---------------------------------------------------------------------------
# Require-line extraction
# ---------------------------------------------------------------------------

_COMMENT_DEPTH_RE = re.compile(r"\(\*.*?\*\)", re.DOTALL)

_REQUIRE_RE = re.compile(
    r"^\s*Require\s+"
    r"(?:(?:Export|Import)\s+)?"
    "((?:[A-Za-z_][A-Za-z0-9_']*)"
    "(?:\\.(?:[A-Za-z_][A-Za-z0-9_']*))*)"
    r"\s*\.\s*$"
)

_FROM_REQUIRE_RE = re.compile(
    r"^\s*From\s+(.+?)\s+(?:Require\s+)?Import\s+"
    "((?:[A-Za-z_][A-Za-z0-9_']*)"
    "(?:\\.(?:[A-Za-z_][A-Za-z0-9_']*))*)"
    r"\s*\.\s*$"
)


def strip_comment_spans(text):
    """Remove Rocq (* ... *) comment spans, nested-aware.

    Reimplementation of the wash_shape.py discipline as a pure local
    function (dep-line does not import from the frozen wash chain).
    """
    out = []
    i = 0
    depth = 0
    n = len(text)
    while i < n:
        if text.startswith("(*", i):
            depth += 1
            i += 2
        elif depth > 0 and text.startswith("*)", i):
            depth -= 1
            i += 2
        elif depth > 0:
            i += 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def extract_requires(text):
    """Return sorted set of Require targets from comment-stripped text."""
    clean = strip_comment_spans(text)
    mods = set()
    for line in clean.splitlines():
        m = _REQUIRE_RE.match(line)
        if m:
            mods.add(m.group(1))
            continue
        m2 = _FROM_REQUIRE_RE.match(line)
        if m2:
            mods.add(m2.group(1) + "." + m2.group(2))
    return sorted(mods)


# ---------------------------------------------------------------------------
# Census
# ---------------------------------------------------------------------------

def scan_tree(roots):
    """Walk the given roots and return a sorted list of .v file paths."""
    vfiles = []
    for root in roots:
        if os.path.isfile(root) and root.endswith(".v"):
            vfiles.append(os.path.abspath(root))
        elif os.path.isdir(root):
            for dirpath, _, filenames in os.walk(root):
                for fn in sorted(filenames):
                    if fn.endswith(".v"):
                        vfiles.append(os.path.join(dirpath, fn))
    return sorted(set(vfiles))


def build_dep_map(vfiles):
    """Build {consumer_path: [required_module, ...]} for each .v file."""
    dep_map = {}
    for vf in vfiles:
        try:
            with open(vf, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            raise FailLoud(1, "unreadable consumer %s: %s" % (vf, exc))
        deps = extract_requires(text)
        dep_map[vf] = deps
    return dep_map


def classify_edges(dep_map):
    """Classify every Require edge: in-repo / stdlib / missing-provider.

    Returns {module: {"class": str, "refs": int}} sorted by module.  The
    in-repo test matches the required module's last segment against the
    stems of the scanned files (the same projection the consumer map
    uses); it cannot see module hierarchies, which is why a stem match
    is trusted first and a miss is reported as missing-provider rather
    than guessed away.
    """
    stems = set()
    for consumer in dep_map:
        stem = os.path.splitext(os.path.basename(consumer))[0]
        stems.add(stem)
    edges = {}
    for mods in dep_map.values():
        for mod in mods:
            if mod not in edges:
                edges[mod] = 0
            edges[mod] += 1
    classification = {}
    for mod in sorted(edges):
        if mod.split(".")[-1] in stems:
            cls = "in-repo"
        elif mod.startswith(STDLIB_PREFIXES):
            cls = "stdlib"
        elif "." not in mod and mod in STDLIB_BARE:
            cls = "stdlib"
        else:
            cls = "missing-provider"
        classification[mod] = {"class": cls, "refs": edges[mod]}
    return classification


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------

_SELFTEST_FIXTURES = [
    # (label, source_text, expected_requires_sorted)
    ("plain-require",
     "Require Import List.\nRequire Export Arith.\n",
     ["Arith", "List"]),
    ("from-require",
     "From Coq Require Import ssreflect.\nFrom Stdlib.Requires Import QReals.\n",
     ["Coq.ssreflect", "Stdlib.Requires.QReals"]),
    ("comment-stripped",
     "(* Require Import OldList *)\nRequire Import List.\n",
     ["List"]),
    ("nested-comment",
     "(* outer (* inner Require Import Ghost *) *)\nRequire Import Reals.\n",
     ["Reals"]),
    ("multi-dot-module",
     "From Coq.Numbers.Calc Require Import NatInt.\n",
     ["Coq.Numbers.Calc.NatInt"]),
    ("empty-file",
     "",
     []),
    ("no-require",
     "Theorem trivial : True. Proof. exact I. Qed.\n",
     []),
    ("require-with-export",
     "Require Export Baseline.\n",
     ["Baseline"]),
]


def _selftest():
    ok = True
    for label, text, expected in _SELFTEST_FIXTURES:
        got = extract_requires(text)
        if got != sorted(expected):
            print("SELFTEST FAIL %-24s got=%s expected=%s"
                  % (label, got, expected), file=sys.stderr)
            ok = False
    # determinism: same input → same output
    t1 = extract_requires(_SELFTEST_FIXTURES[0][1])
    t2 = extract_requires(_SELFTEST_FIXTURES[0][1])
    if t1 != t2:
        print("SELFTEST FAIL determinism", file=sys.stderr)
        ok = False

    # classify leg vectors (DQ-1): rule order in-repo > stdlib > missing
    cmap = {"local/Ring.v": ["Ring", "Coq.Lists.List"],
            "local/other.v": ["List", "Ghost"]}
    cls = classify_edges(cmap)
    if cls.get("Ring", {}).get("class") != "in-repo":
        print("SELFTEST FAIL classify in-repo %s" % cls.get("Ring"),
              file=sys.stderr)
        ok = False
    if cls.get("Coq.Lists.List", {}).get("class") != "stdlib":
        print("SELFTEST FAIL classify stdlib-dotted %s"
              % cls.get("Coq.Lists.List"), file=sys.stderr)
        ok = False
    if cls.get("List", {}).get("class") != "stdlib":
        # no List.v stem in the map, so the bare curated stdlib set wins
        print("SELFTEST FAIL classify bare-stdlib %s" % cls.get("List"),
              file=sys.stderr)
        ok = False
    if cls.get("Ghost", {}).get("class") != "missing-provider":
        print("SELFTEST FAIL classify missing %s" % cls.get("Ghost"),
              file=sys.stderr)
        ok = False
    shadow = classify_edges({"local/List.v": ["List"]})
    if shadow.get("List", {}).get("class") != "in-repo":
        print("SELFTEST FAIL classify shadow-precedence %s"
              % shadow.get("List"), file=sys.stderr)
        ok = False
    cls_again = classify_edges(cmap)
    if json.dumps(cls, sort_keys=True) != json.dumps(cls_again,
                                                     sort_keys=True):
        print("SELFTEST FAIL classify determinism", file=sys.stderr)
        ok = False
    if ok:
        print("DEP-CENSUS-SELFTEST PASS (%d vectors + %d classify groups)"
              % (len(_SELFTEST_FIXTURES), 6))
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
        description="dependency census: scan .v files, build consumer→provider "
                    "map, emit rocqwash.dep-map/1")
    ap.add_argument("--roots", default=".",
                    help="comma-separated directories or .v files to scan")
    ap.add_argument("--out", default=None, help="output JSON file")
    ap.add_argument("--format", choices=["json", "text"], default="json")
    ap.add_argument("--classify", action="store_true",
                    help="add the edge_classification table (in-repo / "
                         "stdlib / missing-provider per module; DQ-1)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the in-process fixture vector group")
    args = ap.parse_args(argv)

    if args.selftest:
        sys.exit(_selftest())

    roots = [r.strip() for r in args.roots.split(",") if r.strip()]
    if not roots:
        print("FAIL-LOUD: no roots given (--roots required)", file=sys.stderr)
        sys.exit(2)

    vfiles = scan_tree(roots)
    dep_map = build_dep_map(vfiles)

    doc = {
        "schema": SCHEMA,
        "roots": roots,
        "consumers_scanned": len(vfiles),
        "dependencies": {
            vf: deps for vf, deps in sorted(dep_map.items()) if deps
        },
        "consumers_with_zero_requires": sorted(
            vf for vf, deps in dep_map.items() if not deps
        ),
    }
    if args.classify:
        doc["edge_classification"] = classify_edges(dep_map)

    text = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("dep-map written: %s (%d consumers, %d with deps)"
              % (args.out, len(vfiles), len(doc["dependencies"])))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except FailLoud as exc:
        print("FAIL-LOUD: %s" % exc.msg, file=sys.stderr)
        sys.exit(exc.rc)
