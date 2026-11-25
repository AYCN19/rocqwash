#!/usr/bin/env python3
"""dep_crosscheck.py - the dep-line rotation report: chain the four dep
tools (census, plan, apply, verify) over one real module and render the
honest cross-check report document.

Purpose.  D1 dep_census scans, D2 dep_plan plans the retirement of a
target, D3 dep_apply executes the plan into an out mirror with the N=N
statement-name assertion, D4 dep_retire_verify probes the outcome.  This
tool orchestrates those four as one chain (subprocess per sibling tool,
sys.executable, zero imports of the wash chain) and renders
docs/dep-retire-report-<date>.md content: per-leg verdicts, artifact
schemas, and the failure leg if the chain aborts.  It is the only
dep-line place that mentions registration needs; the note lives in the
report text only (registration into cw.sh routes / capability docs
belongs to the main-line rotation close-out, by line split).

Interface.
  `python -B tools/dep_crosscheck.py --roots <dir> --target Mod
           --replacement Mod --out <dir>`
  `python -B tools/dep_crosscheck.py --selftest`

Exit codes.
  0  chain completed (verdicts inside the report are independent facts)
  1  fail-loud (missing sibling tools, unreadable artifacts, selftest)
  2  usage error

Safety.  Zero network.  Writes: chain artifacts and the report under the
caller-named --out directory only; the repository tree is never written
(apply mirrors under --out by construction).  Determinism: the report is
assembled from tool documents with sorted keys and no wall clock; equal
inputs give byte-identical reports.

Dependencies.  Python 3 standard library; sibling dep tools in tools/;
a Rocq toolchain for the verify leg (its absence is reported honestly in
the report, not faked).
"""
import argparse
import json
import os
import subprocess
import sys

SCHEMA = "rocqwash.dep-crosscheck/1"

STEPS = ("census", "plan", "apply", "verify")


def sibling_path(tools_dir, name):
    path = os.path.join(tools_dir, name)
    if not os.path.isfile(path):
        raise FailLoud(1, "sibling tool missing: %s" % path)
    return path


def run_step(tools_dir, name, argv):
    """Run one sibling tool; return (rc, artifact_doc_or_none, stdout)."""
    tool = sibling_path(tools_dir, name)
    proc = subprocess.run(
        [sys.executable, "-B", tool] + argv,
        capture_output=True, text=True, errors="replace", timeout=600)
    return proc.returncode, proc.stdout + proc.stderr


def chain(tools_dir, roots, target, replacement, out_dir, coqc=None):
    """Execute census -> plan -> apply -> verify; return the chain doc.

    apply mirrors patched consumers under out_dir; verify runs against
    the FIRST mirrored consumer copy (the rewired artifact).  Any leg
    failing hard (rc not in the tool's success set) aborts the chain and
    the doc records the abort leg honestly.
    """
    legs = []
    census_out = os.path.join(out_dir, "census.json")
    rc, out = run_step(tools_dir, "dep_census.py",
                       ["--roots", roots, "--out", census_out])
    legs.append({"leg": "census", "rc": rc,
                 "schema": "rocqwash.dep-map/1",
                 "note": out.strip().splitlines()[-1] if out.strip() else ""})
    if rc != 0:
        return {"schema": SCHEMA, "legs": legs, "aborted": "census"}
    with open(census_out, "r", encoding="utf-8") as fh:
        census = json.load(fh)

    plan_out = os.path.join(out_dir, "plan")
    os.makedirs(plan_out, exist_ok=True)
    rc, out = run_step(tools_dir, "dep_plan.py",
                       ["--census", census_out, "--target", target,
                        "--replacement", replacement, "--roots", roots,
                        "--out", plan_out, "--apply"])
    legs.append({"leg": "plan+apply", "rc": rc,
                 "schema": "rocqwash.dep-plan/1",
                 "note": out.strip().splitlines()[-1] if out.strip() else ""})
    if rc != 0:
        return {"schema": SCHEMA, "legs": legs, "aborted": "plan"}
    with open(os.path.join(plan_out, "dep-plan.json"), "r",
              encoding="utf-8") as fh:
        plan = json.load(fh)

    consumers = sorted({e["consumer"] for e in plan["entries"]
                        if e.get("action") == "repoint"})
    if not consumers:
        return {"schema": SCHEMA, "legs": legs, "aborted": None,
                "note": "empty plan: target unreferenced, nothing to "
                        "apply or verify"}

    apply_out = os.path.join(out_dir, "apply")
    os.makedirs(apply_out, exist_ok=True)
    names_dir = os.path.join(os.path.abspath(roots[0]), "names")
    rc, out = run_step(tools_dir, "dep_apply.py",
                       ["--plan", os.path.join(plan_out, "dep-plan.json"),
                        "--roots", roots, "--out", apply_out,
                        "--names-dir", names_dir])
    legs.append({"leg": "apply", "rc": rc,
                 "schema": "rocqwash.dep-apply-report/1",
                 "note": out.strip().splitlines()[-1] if out.strip() else ""})
    if rc != 0:
        return {"schema": SCHEMA, "legs": legs, "aborted": "apply"}

    first_consumer = consumers[0]
    mirrored = os.path.join(apply_out, os.path.relpath(
        os.path.abspath(first_consumer), os.path.abspath(roots[0])))
    verify_argv = ["--file", mirrored, "--module", target]
    if coqc:
        verify_argv += ["--coqc", coqc]
    rc, out = run_step(tools_dir, "dep_retire_verify.py", verify_argv)
    legs.append({"leg": "verify", "rc": rc,
                 "schema": "rocqwash.retire-verify/1",
                 "note": out.strip().splitlines()[-1] if out.strip() else ""})
    return {
        "schema": SCHEMA,
        "target": target,
        "replacement": replacement,
        "roots": roots,
        "legs": legs,
        "aborted": None,
        "consumers": consumers,
    }


def render_report(doc, registration_note=True):
    """Render the deterministic markdown report from the chain doc."""
    lines = []
    lines.append("# dep-line cross-check report")
    lines.append("")
    lines.append("- schema: %s" % doc.get("schema"))
    lines.append("- target: %s" % doc.get("target"))
    lines.append("- replacement: %s" % doc.get("replacement"))
    lines.append("- roots: %s" % doc.get("roots"))
    if doc.get("aborted"):
        lines.append("- chain state: ABORTED at leg %s" % doc["aborted"])
    else:
        lines.append("- chain state: completed")
    lines.append("")
    lines.append("## Legs")
    lines.append("")
    lines.append("| leg | rc | schema | note |")
    lines.append("| --- | --- | --- | --- |")
    for leg in doc.get("legs", []):
        note = (leg.get("note") or "").replace("|", "\\|")
        lines.append("| %s | %s | %s | %s |"
                     % (leg["leg"], leg["rc"], leg.get("schema", ""),
                        note))
    lines.append("")
    lines.append("## Honest reading")
    lines.append("")
    lines.append("The verify verdict is a fact about the probed artifact, "
                 "not a quality label for the line: a fixture whose "
                 "provider is not compiled in-tree verifies UNSAFE, and "
                 "that is the correct outcome for an out-of-context "
                 "artifact. The chain itself reports completion, never "
                 "quality.")
    lines.append("")
    if registration_note:
        lines.append("## Registration note")
        lines.append("")
        lines.append("The dep-line tools (dep_census, dep_plan, dep_apply, "
                     "dep_retire_verify, dep_crosscheck) are not yet "
                     "registered: no cw.sh case routes, no capability-doc "
                     "rows, no run_tests.sh CASES entries. Registration is "
                     "the main-line rotation close-out's action, outside "
                     "the dep-line file domain; until then the tool-table "
                     "doc_lint delta of each landing PR is the expected "
                     "and recorded residue.")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Selftest (in-process vectors; no siblings, no disk, no network)
# ---------------------------------------------------------------------------

def _doc(aborted=None, legs=None):
    return {"schema": SCHEMA,
            "target": "Old.Mod", "replacement": "New.Mod",
            "roots": "r", "legs": legs or [], "aborted": aborted,
            "consumers": ["r/a.v"]}


def _selftest():
    ok = True
    def check(label, cond):
        nonlocal ok
        if not cond:
            print("SELFTEST FAIL %s" % label, file=sys.stderr)
            ok = False

    legs = [{"leg": s, "rc": 0, "schema": "s/%s" % s, "note": "n-%s" % s}
            for s in STEPS]

    # 1 four legs render in canonical order
    rep = render_report(_doc(legs=legs))
    check("leg-order",
          [rep.index("| %s |" % s) for s in STEPS] ==
          sorted(rep.index("| %s |" % s) for s in STEPS))

    # 2 abort marking
    rep_ab = render_report(_doc(aborted="plan", legs=legs[:2]))
    check("abort-marked", "ABORTED at leg plan" in rep_ab
          and "chain state: completed" not in rep_ab)

    # 3 determinism: byte-identical reports from equal docs
    check("report-determinism",
          render_report(_doc(legs=legs)) == render_report(_doc(legs=legs)))

    # 4 registration note present exactly once (and omissible)
    check("reg-note-once",
          render_report(_doc(legs=legs)).count("## Registration note") == 1)
    check("reg-note-off",
          "Registration" not in render_report(_doc(legs=legs),
                                              registration_note=False))

    # 5 honest reading section always present
    check("honest-reading",
          "## Honest reading" in render_report(_doc(aborted="census")))

    # 6 step table integrity
    check("steps-canonical", STEPS == ("census", "plan", "apply", "verify"))

    if ok:
        print("DEP-CROSSCHECK-SELFTEST PASS (%d vector groups)" % 6)
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
        description="chain census/plan/apply/verify over one target and "
                    "render the dep-line cross-check report")
    ap.add_argument("--tools-dir", default=None,
                    help="directory holding the four sibling tools "
                         "(default: this file's tools/)")
    ap.add_argument("--roots", default=None,
                    help="scan roots backing the chain")
    ap.add_argument("--target", default=None,
                    help="module to retire in the chain")
    ap.add_argument("--replacement", default=None,
                    help="module the consumers re-point to")
    ap.add_argument("--out", default=None,
                    help="existing directory for chain artifacts and the "
                         "report markdown")
    ap.add_argument("--coqc", default=None, help="explicit coqc path")
    ap.add_argument("--selftest", action="store_true",
                    help="run the in-process vector groups")
    args = ap.parse_args(argv)

    if args.selftest:
        sys.exit(_selftest())
    if not args.out or not args.roots or not args.target \
            or not args.replacement:
        raise FailLoud(2, "--roots, --target, --replacement and --out are "
                          "required")
    if not os.path.isdir(args.out):
        raise FailLoud(2, "--out must be an existing directory (the "
                          "caller creates it)")
    tools_dir = args.tools_dir or os.path.dirname(os.path.abspath(__file__))

    doc = chain(tools_dir, args.roots, args.target, args.replacement,
                args.out, coqc=args.coqc)
    report = render_report(doc)
    report_path = os.path.join(args.out, "dep-retire-report.md")
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(report)
    with open(os.path.join(args.out, "crosscheck.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, indent=2, sort_keys=True,
                            ensure_ascii=False) + "\n")
    state = doc.get("aborted") or "completed"
    print("chain %s; report: %s" % (state, report_path))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except FailLoud as exc:
        print("FAIL-LOUD: %s" % exc.msg, file=sys.stderr)
        sys.exit(exc.rc)
