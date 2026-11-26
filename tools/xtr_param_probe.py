#!/usr/bin/env python3
"""xtr_param_probe.py - probe .v sources for extraction-degrading
constructs: Program obligation generators, type quantifiers in
constructor parameters, and Set/Type universe pins.

Purpose.  Certain constructs degrade what Rocq extraction can produce:
Program vernacular generates obligations that extract as auxiliary
opaque constants; constructors carrying existentially packaged types
(ex / sigT / sigma shapes) make the extracted representation lossy;
and declarations pinned to the Set or Type universes sit on the
erasure boundary.  This tool reports risk candidates per file with
line, category and snippet.  Schema rocqwash.xtr-param-probe/1.
Report-only: a hit is a candidate for review, not a defect.

Interface.
  python -B tools/xtr_param_probe.py --roots DIR[,DIR...] [--out FILE] [--format json|text] [--selftest]

Exit-codes.  0 success; 1 fail-loud (unreadable input, selftest
failure); 2 usage error.

Safety.  Zero network, stdlib only, read-only over input trees; the
only write is the caller-named --out file.  Determinism: sorted keys,
no wall clock.  Honesty: category detection is textual block-level
matching, not a parse; hits are advisory.

Evidence.  Eight selftest vectors (Program vernacular, obligations,
constructor type quantifier, universe pins, clean negative, masking,
multi-category counts, determinism), green at integration.

Dependencies.  Python 3 standard library only.
"""
import argparse
import json
import os
import re
import sys

SCHEMA = "rocqwash.xtr-param-probe/1"
GENERATED_BY = "tools/xtr_param_probe.py"
SELFTEST_MARKER = "XTR-PARAM-PROBE-SELFTEST PASS"

_PROGRAM_RE = re.compile(
    r"^\s*Program\s+(?:Definition|Fixpoint|Lemma|Theorem|Coroutine)\b")
_OBLIGATION_RE = re.compile(
    r"^\s*(?:Next\s+Obligation|Obligation\s+Tactic\b|Obligation\s+[0-9]|"
    r"Solve\s+(?:All\s+)?Obligations|Dependent\s+Obligations?\b)")
_INDUCTIVE_OPEN_RE = re.compile(r"^\s*(?:Co)?Inductive\b")
_SIGMA_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_'])(sigT2?|exists\b|\{[^}&]*&[^}]*\})")
_UNIVERSE_PIN_RE = re.compile(
    r"^\s*(?:Definition|Fixpoint|Theorem|Lemma|Inductive|CoInductive)\b"
    r"[^.:]*:\s*(?:Type|Set)\b")
_UNIVERSE_VERNAC_RE = re.compile(
    r"^\s*(?:Universe|Polymorphic|Monomorphic|Global\s+Set|"
    r"Local\s+Set|Set\s+Universe\s+Polymorphism)\b")


def mask_comment_spans(text):
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


def probe_source(text, filename):
    """Return the risk-candidate list for one .v source."""
    masked = mask_comment_spans(text)
    lines = masked.split("\n")
    candidates = []
    in_inductive = False
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if _INDUCTIVE_OPEN_RE.match(line):
            in_inductive = True
        if in_inductive and _SIGMA_TOKEN_RE.search(line):
            candidates.append({
                "file": filename, "line": idx,
                "category": "constructor-type-quantifier",
                "snippet": stripped[:120],
            })
        if _PROGRAM_RE.match(line):
            candidates.append({
                "file": filename, "line": idx,
                "category": "program-obligation",
                "snippet": stripped[:120],
            })
        elif _OBLIGATION_RE.match(line):
            candidates.append({
                "file": filename, "line": idx,
                "category": "program-obligation",
                "snippet": stripped[:120],
            })
        if _UNIVERSE_PIN_RE.match(line):
            candidates.append({
                "file": filename, "line": idx,
                "category": "universe-pin",
                "snippet": stripped[:120],
            })
        elif _UNIVERSE_VERNAC_RE.match(line):
            candidates.append({
                "file": filename, "line": idx,
                "category": "universe-pin",
                "snippet": stripped[:120],
            })
        if in_inductive and stripped.endswith(".") and \
                not stripped.startswith("with"):
            in_inductive = False
    return candidates


def scan_tree(roots):
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
    candidates = []
    for name, text in source_reader:
        candidates.extend(probe_source(text, name))
    candidates.sort(key=lambda c: (c["file"], c["line"], c["category"]))
    counts = {}
    for c in candidates:
        counts[c["category"]] = counts.get(c["category"], 0) + 1
    return {
        "schema": SCHEMA,
        "generated_by": GENERATED_BY,
        "roots": list(roots),
        "files_scanned": len(list(source_reader)),
        "candidates": candidates,
        "counts_by_category": dict(sorted(counts.items())),
    }


def report_json(report):
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def report_text(report):
    lines = ["xtr-param-probe %s" % SCHEMA]
    lines.append("files_scanned=%d candidates=%d categories=%s" % (
        report["files_scanned"], len(report["candidates"]),
        json.dumps(report["counts_by_category"], sort_keys=True)))
    for c in report["candidates"]:
        lines.append("  %s:%d [%s] %s" % (
            c["file"], c["line"], c["category"], c["snippet"]))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Selftest (in-process fixtures, no disk reads)
# ---------------------------------------------------------------------------

def _selftest():
    failures = []

    def check(cond, label):
        if not cond:
            failures.append(label)

    def cats(src):
        return probe_source(src, "f.v")

    # v1: Program vernacular
    cs = cats("Program Definition foo := bar.\n")
    check(len(cs) == 1 and cs[0]["category"] == "program-obligation",
          "v1 program definition")
    check(cs[0]["line"] == 1, "v1 line")

    # v2: obligation vernacular
    cs = cats("Next Obligation.\nProof. reflexivity. Qed.\n")
    check(len(cs) == 1 and cs[0]["category"] == "program-obligation",
          "v2 next obligation")

    # v3: constructor type quantifier inside an Inductive block
    src = ("Inductive box : Type :=\n"
           "| mk_box : sigT (fun a : Type => a) -> box.\n"
           "Definition after_box := 1.\n")
    cs = cats(src)
    # two honest hits: the sigT constructor parameter plus the Inductive
    # itself being pinned to Type (both live on the erasure boundary)
    check(len(cs) == 2, "v3 two hits (sigma + type pin)")
    sigma = [c for c in cs if c["category"] == "constructor-type-quantifier"]
    pins = [c for c in cs if c["category"] == "universe-pin"]
    check(len(sigma) == 1 and sigma[0]["line"] == 2, "v3 sigma hit line")
    check(len(pins) == 1 and pins[0]["line"] == 1, "v3 pin hit line")
    # the block ends at the period; the later Definition is not scanned
    cs2 = cats("Definition plain := sigT (fun a => a).\n")
    check(len(cs2) == 0, "v3 sigma outside inductive block")

    # v4: Set / Type universe pins
    cs = cats("Definition pinned : Type := 0.\n"
              "Fixpoint loop : Set := 0.\n")
    check(len(cs) == 2, "v4 two pins")
    check(all(c["category"] == "universe-pin" for c in cs), "v4 category")
    cs2 = cats("Definition unpinned := 0.\n")
    check(len(cs2) == 0, "v4 unpinned clean")

    # v5: clean negative - ordinary file has zero candidates
    cs = cats("Definition add := fun x y => x + y.\n"
              "Lemma trivial : True.\nProof. exact I. Qed.\n")
    check(len(cs) == 0, "v5 clean negative")

    # v6: comment masking
    cs = cats("(* Program Definition fake := x. *)\nDefinition ok := 1.\n")
    check(len(cs) == 0, "v6 comment masked")

    # v7: multi-category counts in one file
    src = ("Program Fixpoint p (n : nat) := match n with 0 => 0 "
           "| S k => p k end.\n"
           "Next Obligation.\nQed.\n"
           "Inductive wrapped : Type :=\n"
           "| wrap : {x : nat & x = x} -> wrapped.\n")
    cs = cats(src)
    kinds = [c["category"] for c in cs]
    check(kinds.count("program-obligation") == 2, "v7 program hits")
    check(kinds.count("constructor-type-quantifier") == 1, "v7 sigma hit")

    # v8: determinism - byte-identical double report
    srcs = [("a.v", "Program Definition q := 0.\n"),
            ("b.v", "Definition pinned : Type := 0.\n")]
    rep1 = report_json(build_report(["r"], srcs))
    rep2 = report_json(build_report(["r"], srcs))
    check(rep1 == rep2, "v8 determinism")

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
        description="Extraction-degrading construct probe (schema %s)."
                    % SCHEMA)
    parser.add_argument("--roots", default=None,
                        help="comma-separated directories or .v files")
    parser.add_argument("--out", default=None)
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
                pairs.append((path.replace(os.sep, "/"), fh.read()))
        except OSError as exc:
            sys.stderr.write("fail-loud: unreadable %s: %s\n" % (path, exc))
            return 1
    report = build_report(roots, pairs)
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
