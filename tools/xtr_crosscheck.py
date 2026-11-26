#!/usr/bin/env python3
"""xtr_crosscheck.py - chain the four xtr tools over one fixture world
and emit the full-line crosscheck document.

Purpose.  Tickets X1-X4 each stand alone; this tool runs them as one
chain over a shared fixture world: leg A the extraction census, leg B
the magic audit against census claims, leg C the construct probe, leg
D the three-source erasure link.  Each leg gets a status (ok / missing
/ failed) and the combined document carries the leg verdicts plus
mismatch and leak counts.  Schema rocqwash.xtr-crosscheck/1.
Report-only: the only writes are the caller-named --out and per-leg
temporary JSON files under the caller-named --work dir.

Interface.
  python -B tools/xtr_crosscheck.py --decl DIR --products DIR [--assumptions DIR] [--work DIR] [--out FILE] [--format json|text] [--selftest]

Exit-codes.  0 all legs ok (COMPLETE; mismatches and leaks are data,
not failures); 1 any leg missing or failed (INCOMPLETE, fail-loud);
2 usage error.

Safety.  Zero network, stdlib only, read-only over the input trees.
Determinism: no wall clock, sorted keys; byte-identical documents for
equal fixture worlds.

Evidence.  Five selftest vectors (all-legs-ok chain, seeded audit
mismatch, seeded erasure leak, missing-tool honesty over a partial
root, double-run determinism), green at integration.

Dependencies.  Python 3 standard library only; invokes the four xtr
tools of this line as subprocesses; no compiler toolchain; no network.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

SCHEMA = "rocqwash.xtr-crosscheck/1"
GENERATED_BY = "tools/xtr_crosscheck.py"
SELFTEST_MARKER = "XTR-CROSSCHECK-SELFTEST PASS"

_CENSUS_TOOL = os.path.join("tools", "xtr_extract_census.py")
_MAGIC_TOOL = os.path.join("tools", "xtr_magic_audit.py")
_PROBE_TOOL = os.path.join("tools", "xtr_param_probe.py")
_ERASURE_TOOL = os.path.join("verify", "xtr_erasure_link.py")

_DECL_V = """(* xtr crosscheck fixture: declaration face. *)
Extract Constant Z.add => "(+)".
Theorem clean_proof : 1 = 1.
Proof. reflexivity. Qed.
(* goods.v claims magic-free: every payload above is safe. *)
"""

_BAD_DECL_V = """(* xtr crosscheck fixture: risky face. *)
Extract Constant unsafe_gate => "Obj.magic 0".
Program Definition risky := 0.
Inductive box : Type :=
| mk_box : sigT (fun a : Type => a) -> box.
"""

_GOODS_ML = """let z_add = (+)
let clean_proof = Obj.magic 0
"""

_BAD_ML = """let unsafe_gate = Obj.magic 0
let risky = 0
let mk_box = Obj.magic 0
"""

_ASSUMPTION_PA = "Closed under the global context\n"


def _tool_path(repo_root, rel):
    return os.path.join(repo_root, rel)


def _run_leg(repo_root, tool_rel, argv, leg_name, work_dir):
    """Run one leg.  Returns (status, document_or_none, note)."""
    tool = _tool_path(repo_root, tool_rel)
    if not os.path.isfile(tool):
        return "missing", None, "tool not found: %s" % tool_rel
    out_path = os.path.join(work_dir, "leg_%s.json" % leg_name)
    proc = subprocess.run(
        [sys.executable, "-B", tool] + argv + ["--out", out_path,
                                               "--format", "json"],
        capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or not os.path.isfile(out_path):
        return "failed", None, (proc.stderr or proc.stdout)[:200]
    try:
        with open(out_path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        return "failed", None, str(exc)[:200]
    return "ok", doc, ""


def _fixture_summary(doc):
    """Small deterministic summary block of a leg document."""
    if doc is None:
        return None
    out = {"schema": doc.get("schema")}
    if "summary" in doc:
        out["summary"] = doc["summary"]
    if "counts_by_command" in doc:
        out["counts_by_command"] = doc["counts_by_command"]
    if "counts_by_category" in doc:
        out["counts_by_category"] = doc["counts_by_category"]
    if "verdict_by_file" in doc:
        out["verdict_by_file"] = doc["verdict_by_file"]
    return out


def run_chain(repo_root, decl_dir, products_dir, assumptions_dir, work_dir):
    """Run the four legs; return the combined document."""
    legs = {}
    docs = {}
    status, doc, note = _run_leg(
        repo_root, _CENSUS_TOOL, ["--roots", decl_dir], "census", work_dir)
    legs["census"] = {"status": status, "note": note}
    if status == "ok":
        docs["census"] = doc
    census_arg = (["--census", os.path.join(work_dir, "leg_census.json")]
                  if status == "ok" else [])
    status, doc, note = _run_leg(
        repo_root, _MAGIC_TOOL,
        ["--sources", products_dir] + census_arg, "audit", work_dir)
    legs["audit"] = {"status": status, "note": note}
    if status == "ok":
        docs["audit"] = doc
    status, doc, note = _run_leg(
        repo_root, _PROBE_TOOL, ["--roots", decl_dir], "probe", work_dir)
    legs["probe"] = {"status": status, "note": note}
    if status == "ok":
        docs["probe"] = doc
    erasure_argv = ["--decl-sources", decl_dir, "--sources", products_dir]
    if assumptions_dir:
        erasure_argv += ["--assumptions", assumptions_dir]
    status, doc, note = _run_leg(
        repo_root, _ERASURE_TOOL, erasure_argv, "erasure", work_dir)
    legs["erasure"] = {"status": status, "note": note}
    if status == "ok":
        docs["erasure"] = doc
    all_ok = all(v["status"] == "ok" for v in legs.values())
    mismatch_files = 0
    leak_count = 0
    if "audit" in docs:
        mismatch_files = docs["audit"].get("summary", {}).get(
            "mismatch_files", 0)
    if "erasure" in docs:
        leak_count = docs["erasure"].get("summary", {}).get(
            "verdicts", {}).get("LEAK", 0)
    combined = {
        "schema": SCHEMA,
        "generated_by": GENERATED_BY,
        "legs": {k: dict(legs[k], summary=_fixture_summary(docs.get(k)))
                 for k in sorted(legs)},
        "summary": {
            "verdict": "COMPLETE" if all_ok else "INCOMPLETE",
            "audit_mismatch_files": mismatch_files,
            "erasure_leak_constants": leak_count,
        },
    }
    return combined


# ---------------------------------------------------------------------------
# Selftest (constructs its own fixture world in a temp directory)
# ---------------------------------------------------------------------------

def _selftest():
    failures = []

    def check(cond, label):
        if not cond:
            failures.append(label)

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def build_world(root):
        decl = os.path.join(root, "decls")
        prod = os.path.join(root, "products")
        assum = os.path.join(root, "assumptions")
        os.makedirs(decl)
        os.makedirs(prod)
        os.makedirs(assum)
        with open(os.path.join(decl, "goods.v"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(_DECL_V)
        with open(os.path.join(decl, "bad.v"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(_BAD_DECL_V)
        with open(os.path.join(prod, "goods.ml"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(_GOODS_ML)
        with open(os.path.join(prod, "bad.ml"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(_BAD_ML)
        with open(os.path.join(assum, "clean_proof.pa"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(_ASSUMPTION_PA)
        return decl, prod, assum

    # v1-v3: full chain over the seeded world; the world intentionally
    # carries one audit mismatch (goods.v claims magic-free, goods.ml
    # carries Obj.magic) and one erasure leak (clean_proof in products)
    tmp = tempfile.mkdtemp(prefix="xtr_crosscheck_selftest_")
    try:
        decl, prod, assum = build_world(tmp)
        work = os.path.join(tmp, "work")
        os.makedirs(work)
        rep1 = run_chain(repo_root, decl, prod, assum, work)
        check(rep1["summary"]["verdict"] == "COMPLETE", "v1 chain complete")
        check(all(v["status"] == "ok"
                  for v in rep1["legs"].values()), "v1 all legs ok")
        check(rep1["summary"]["audit_mismatch_files"] == 1,
              "v2 seeded mismatch recorded")
        check(rep1["summary"]["erasure_leak_constants"] == 1,
              "v3 seeded leak recorded")
        check(rep1["legs"]["census"]["summary"]["counts_by_command"].get(
            "Extract Constant") == 2, "v1 census leg counted")
        check(rep1["legs"]["probe"]["summary"]["counts_by_category"].get(
            "program-obligation") == 1, "v1 probe leg counted")

        # v4: missing-tool honesty over a partial root
        partial = os.path.join(tmp, "partial_root")
        os.makedirs(os.path.join(partial, "tools"))
        shutil.copy(_tool_path(repo_root, _CENSUS_TOOL),
                    os.path.join(partial, _CENSUS_TOOL))
        work2 = os.path.join(tmp, "work2")
        os.makedirs(work2)
        rep2 = run_chain(partial, decl, prod, None, work2)
        check(rep2["summary"]["verdict"] == "INCOMPLETE",
              "v4 partial root incomplete")
        check(rep2["legs"]["census"]["status"] == "ok", "v4 census leg ok")
        check(rep2["legs"]["audit"]["status"] == "missing", "v4 audit miss")
        check(rep2["legs"]["erasure"]["status"] == "missing", "v4 erase miss")

        # v5: determinism - same world, byte-identical double chain
        work3 = os.path.join(tmp, "work3")
        os.makedirs(work3)
        work4 = os.path.join(tmp, "work4")
        os.makedirs(work4)
        a = json.dumps(run_chain(repo_root, decl, prod, assum, work3),
                       sort_keys=True)
        b = json.dumps(run_chain(repo_root, decl, prod, assum, work4),
                       sort_keys=True)
        check(a == b, "v5 determinism")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

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
        description="Full-line xtr chain over one fixture world "
                    "(schema %s)." % SCHEMA)
    parser.add_argument("--decl", default=None,
                        help="fixture directory of .v declaration sources")
    parser.add_argument("--products", default=None,
                        help="fixture directory of extraction products")
    parser.add_argument("--assumptions", default=None,
                        help="optional directory of Print Assumptions "
                             "captures")
    parser.add_argument("--work", default=None,
                        help="working directory for per-leg JSON files")
    parser.add_argument("--out", default=None)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.decl or not args.products:
        sys.stderr.write("usage error: --decl and --products are required "
                         "(or run --selftest)\n")
        return 2
    for path, label in ((args.decl, "decl"), (args.products, "products")):
        if not os.path.isdir(path):
            sys.stderr.write("fail-loud: %s dir not found: %s\n"
                             % (label, path))
            return 1
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tmp_work = None
    work = args.work
    if work is None:
        tmp_work = tempfile.mkdtemp(prefix="xtr_crosscheck_work_")
        work = tmp_work
    else:
        os.makedirs(work, exist_ok=True)
    try:
        combined = run_chain(repo_root, args.decl, args.products,
                             args.assumptions, work)
    finally:
        if tmp_work is not None:
            shutil.rmtree(tmp_work, ignore_errors=True)
    all_ok = combined["summary"]["verdict"] == "COMPLETE"
    out = (report_text(combined) if args.format == "text"
           else json.dumps(combined, indent=2, sort_keys=True) + "\n")
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(out)
    else:
        sys.stdout.write(out)
    return 0 if all_ok else 1


def report_text(doc):
    lines = ["xtr-crosscheck %s" % SCHEMA]
    s = doc["summary"]
    lines.append("verdict=%s audit_mismatch_files=%d "
                 "erasure_leak_constants=%d" % (
                     s["verdict"], s["audit_mismatch_files"],
                     s["erasure_leak_constants"]))
    for name in sorted(doc["legs"]):
        leg = doc["legs"][name]
        lines.append("  leg %-8s %-8s %s" % (
            name, leg["status"], leg.get("note", "")))
        if leg.get("summary"):
            lines.append("    %s" % json.dumps(leg["summary"],
                                               sort_keys=True)[:200])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
