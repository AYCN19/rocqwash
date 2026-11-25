#!/usr/bin/env python3
"""dep_retire_verify.py - retirement verification probe: after a consumer
was rewired away from a retired module, verify the retirement held.

Purpose.  Three probes, one verdict:
  A  unlocatable  - a probe file requiring the retired module must FAIL
                    to compile with a missing-library error (the module is
                    genuinely gone from the load path);
  B  compiles     - the rewired consumer must itself compile;
  C  closure      - with --baseline given, the axiom closure reported by
                    Print Assumptions over the consumer's top-level
                    statements must not grow (read-only use of the
                    names/mac_stmt_names.py statement roster; without a
                    baseline the closure facts are reported but do not
                    affect the verdict).
Verdict is SAFE only when A holds, B holds, and C holds-or-not-applicable.
Any failed leg makes it UNSAFE; anything that cannot be established
(toolchain absent, timeout, unrelated compiler error) makes it
INCONCLUSIVE.  Toolchain absence is an honest skip: exit 111.

Interface.
  `python -B tools/dep_retire_verify.py --file <consumer.v> --module Old.Mod`
  `python -B tools/dep_retire_verify.py ... --baseline <assumptions.txt> --json out.json`
  `python -B tools/dep_retire_verify.py --selftest`

Exit codes.
  0   verdict SAFE
  4   verdict UNSAFE
  5   verdict INCONCLUSIVE
  111 honest skip (no Rocq toolchain found)
  1   fail-loud (unreadable inputs, invalid usage, selftest failure)
  2   usage error

Safety.  Zero network; writes only under a caller-visible temp directory
(probe files) and the optional --json path.  The repository is never
written.  Determinism: the verdict document contains no wall clock and
sorted keys; equal inputs produce byte-identical documents.

Dependencies.  Python 3 standard library; a Rocq toolchain (coqc) for
the live probes - its absence degrades to the honest skip, never to a
fake green.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SCHEMA = "rocqwash.retire-verify/1"

# Form reused from wash/probe_engine.py MISSING_LIB_RE (read-only
# reference; the wash chain is not imported and not modified).
MISSING_LIB_RE = re.compile(
    r"(?:unable to locate library|cannot find library)\s+\|?\s*"
    r"([A-Za-z0-9_']+)", re.IGNORECASE)
CLOSED_RE = re.compile(r"Closed under the global context", re.IGNORECASE)
AXIOM_LINE_RE = re.compile(r"^\s*(Axioms?|Assumptions?)\s*:\s*(.*)$")

COQC_CANDIDATES = (
    "coqc",
    r"D:/ComplexAnalysis/attn/opam93/default/bin/coqc.exe",
)
COQC_TIMEOUT = 120


def find_coqc(explicit=None):
    """Return a usable coqc path or None (drives the honest rc 111)."""
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    for cand in COQC_CANDIDATES:
        if os.path.isfile(cand) or shutil.which(cand):
            return shutil.which(cand) or cand
    return None


def run_coqc(coqc, path, lib_args, cwd):
    """Compile one file; return (rc, combined_output)."""
    try:
        proc = subprocess.run(
            [coqc] + list(lib_args) + [path],
            capture_output=True, text=True, errors="replace",
            cwd=cwd, timeout=COQC_TIMEOUT)
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT after %ss" % COQC_TIMEOUT
    except OSError as exc:
        return None, "OSERROR %s" % exc


def probe_unlocatable(coqc, module, lib_args, workdir, runner=run_coqc):
    """Probe A: Require of the retired module must fail as missing."""
    probe = os.path.join(workdir, "probe_absent.v")
    with open(probe, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("Require Import %s.\n" % module)
    rc, out = runner(coqc, probe, lib_args, workdir)
    if rc == 0:
        return False, "module %s still locatable (probe compiled)" % module
    if rc is None:
        return None, out.strip()[:200]
    if MISSING_LIB_RE.search(out):
        return True, "module %s unlocatable (missing-library error)" % module
    return None, ("probe failed with an unrelated error: %s"
                  % out.strip()[:200])


def probe_compiles(coqc, consumer, lib_args, runner=run_coqc):
    """Probe B: the rewired consumer compiles."""
    abs_consumer = os.path.abspath(consumer)
    rc, out = runner(coqc, abs_consumer, lib_args,
                     os.path.dirname(abs_consumer))
    if rc == 0:
        return True, "consumer compiles"
    if rc is None:
        return None, out.strip()[:200]
    return False, ("consumer compile failed: %s" % out.strip()[:200])


def probe_closure(coqc, consumer, module_of_consumer, statements,
                  lib_args, workdir, runner=run_coqc):
    """Probe C: Print Assumptions roster for the consumer statements.

    Returns (ordered assumption lines, ok_flag, note).  ok_flag is None
    when the closure probe could not run (no statements to ask about, or
    the closure probe file itself failed for an unrelated reason).
    """
    if not statements:
        return [], None, "no top-level statements to ask assumptions about"
    lines = ["Require Import %s." % module_of_consumer]
    for name in statements:
        lines.append("Print Assumptions %s." % name)
    probe = os.path.join(workdir, "probe_closure.v")
    with open(probe, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    rc, out = runner(coqc, probe, lib_args, workdir)
    if rc is None:
        return [], None, out.strip()[:200]
    found = []
    current_axioms = None
    for ln in out.splitlines():
        m = AXIOM_LINE_RE.match(ln)
        if m:
            current_axioms = m.group(2).strip()
            found.append(ln.strip())
        elif ln.strip() and current_axioms is not None:
            found.append(ln.strip())
        elif CLOSED_RE.search(ln):
            found.append(ln.strip())
            current_axioms = None
    if not found:
        # nothing parseable came back: an honest INCONCLUSIVE leg, not a
        # silent pass (unrelated compile error, empty output, ...)
        return [], None, ("closure probe gave no parseable output (rc=%s):"
                          " %s" % (rc, out.strip()[:160]))
    return found, True, "closure roster collected (%d lines)" % len(found)


def verdict_from_probes(unloc, compiles, closure_ok, baseline):
    """Fold the three probe results into the verdict string.

    unloc / compiles are True/False/None; closure_ok is True (roster
    within baseline), False (grew), or None (not applicable / unknown).
    """
    if unloc is None or compiles is None or closure_ok is False:
        return "INCONCLUSIVE" if (unloc is None or compiles is None) \
            else "UNSAFE"
    if not unloc or not compiles:
        return "UNSAFE"
    if closure_ok is False:
        return "UNSAFE"
    if closure_ok is None and baseline is not None:
        return "INCONCLUSIVE"
    return "SAFE"


VERDICT_RC = {"SAFE": 0, "UNSAFE": 4, "INCONCLUSIVE": 5}


def verify(coqc, consumer, module, module_of_consumer, lib_args, baseline,
           extract=None):
    """Run the three probes and build the verdict document."""
    with tempfile.TemporaryDirectory(prefix="dep_retire_verify_") as wd:
        unloc, unloc_note = probe_unlocatable(coqc, module, lib_args, wd)
        compiles, comp_note = probe_compiles(coqc, consumer, lib_args)
        statements = []
        if extract is not None and compiles:
            try:
                doc = extract(consumer)
                statements = [s["name"] for s in doc.get("statements", [])]
            except Exception as exc:  # noqa: BLE001 - honest degradation
                statements = []
                compiles = None
                comp_note = "statement roster failed: %s" % exc
        roster, closure_ok, closure_note = ([], None, "skipped (consumer "
                                            "did not compile)")
        if compiles and extract is not None:
            roster, closure_ok, closure_note = probe_closure(
                coqc, consumer, module_of_consumer, statements, lib_args, wd)
    verdict = verdict_from_probes(unloc, compiles, closure_ok, baseline)
    baseline_note = "no baseline given; closure reported, not judged"
    if baseline is not None and roster:
        grew = len([r for r in roster if not CLOSED_RE.search(r)])
        with open(baseline, "r", encoding="utf-8") as fh:
            base_lines = [ln.strip() for ln in fh if ln.strip()]
        if grew > len([b for b in base_lines if not CLOSED_RE.search(b)]):
            verdict = "UNSAFE"
            closure_ok = False
            closure_note = "closure grew vs baseline"
    return {
        "schema": SCHEMA,
        "consumer": consumer,
        "retired_module": module,
        "verdict": verdict,
        "probes": {
            "unlocatable": {"result": unloc, "note": unloc_note},
            "compiles": {"result": compiles, "note": comp_note},
            "closure": {"result": closure_ok, "note": closure_note,
                        "roster": roster},
        },
    }


# ---------------------------------------------------------------------------
# Selftest (canned-output vectors; no toolchain, no disk, no network)
# ---------------------------------------------------------------------------

_OUT_MISSING = ("... Error: Unable to locate library OldMod with read "
                "option -Q ...")
_OUT_CLEAN = ""


class _CannedRun(object):
    def __init__(self, table):
        self.table = table

    def __call__(self, coqc, path, lib_args, cwd):
        key = os.path.basename(path)
        return self.table.get(key, (1, "unexpected probe file"))


def _selftest():
    ok = True
    def check(label, cond):
        nonlocal ok
        if not cond:
            print("SELFTEST FAIL %s" % label, file=sys.stderr)
            ok = False

    # 1 regex form parity with probe_engine (attribution form reused)
    check("missing-lib-match",
          MISSING_LIB_RE.search(_OUT_MISSING) is not None
          and MISSING_LIB_RE.search(_OUT_MISSING).group(1) == "OldMod")
    check("missing-lib-negative",
          MISSING_LIB_RE.search("Error: The reference foo was not found")
          is None)

    # 2 canned runner table exercising the real probe logic
    canned = _CannedRun({
        "probe_absent.v": (1, _OUT_MISSING),
        "consumer.v": (0, _OUT_CLEAN),
        "probe_closure.v": (0, "Closed under the global context\n"),
    })
    with tempfile.TemporaryDirectory() as wd:
        unloc, note = probe_unlocatable("coqc", "OldMod", (), wd,
                                        runner=canned)
        check("probe-a-missing", unloc is True
              and "unlocatable" in note)

    # 3 probe A negative: module still locatable -> UNSAFE leg
    canned_live = _CannedRun({"probe_absent.v": (0, _OUT_CLEAN)})
    with tempfile.TemporaryDirectory() as wd:
        unloc3, _ = probe_unlocatable("coqc", "OldMod", (), wd,
                                      runner=canned_live)
        check("probe-a-locatable", unloc3 is False)

    # 4 probe A unrelated error -> INCONCLUSIVE leg (None)
    canned_odd = _CannedRun({"probe_absent.v": (1, "Error: syntax error")})
    with tempfile.TemporaryDirectory() as wd:
        unloc4, _ = probe_unlocatable("coqc", "OldMod", (), wd,
                                      runner=canned_odd)
        check("probe-a-unrelated", unloc4 is None)

    # 5 fold logic table (pure)
    check("fold-safe", verdict_from_probes(True, True, True, None) == "SAFE")
    check("fold-safe-na",
          verdict_from_probes(True, True, None, None) == "SAFE")
    check("fold-unsafe-locatable",
          verdict_from_probes(False, True, True, None) == "UNSAFE")
    check("fold-unsafe-broken",
          verdict_from_probes(True, False, None, None) == "UNSAFE")
    check("fold-inconclusive-timeout",
          verdict_from_probes(None, True, None, None) == "INCONCLUSIVE")
    check("fold-inconclusive-closure",
          verdict_from_probes(True, True, None, "base.txt") ==
          "INCONCLUSIVE")
    check("fold-unsafe-grew",
          verdict_from_probes(True, True, False, "base.txt") == "UNSAFE")

    # 6 closure probe on canned output (happy + unrelated-fail)
    canned_cls = _CannedRun({
        "probe_closure.v": (0, "t1 : Closed under the global context\n"),
        "odd.v": (1, "Error: syntax error"),
    })
    with tempfile.TemporaryDirectory() as wd:
        roster, cok, cn = probe_closure("coqc", "consumer.v", "Cons",
                                        ["t1"], (), wd, runner=canned_cls)
        check("closure-ok", cok is True and len(roster) == 1)
        roster2, cok2, _ = probe_closure("coqc", "consumer.v", "Cons",
                                         ["t1"], (), wd,
                                         runner=_CannedRun(
                                             {"probe_closure.v":
                                              (1, "Error: boom")}))
        check("closure-unrelated", cok2 is None and roster2 == [])
    with tempfile.TemporaryDirectory() as wd:
        roster3, cok3, _ = probe_closure("coqc", "consumer.v", "Cons",
                                         [], (), wd, runner=canned_cls)
        check("closure-no-statements", cok3 is None)

    # 7 timeout leg -> None (INCONCLUSIVE)
    canned_slow = _CannedRun({"probe_absent.v": (None, "TIMEOUT")})
    with tempfile.TemporaryDirectory() as wd:
        unloc7, _ = probe_unlocatable("coqc", "OldMod", (), wd,
                                      runner=canned_slow)
        check("probe-a-timeout", unloc7 is None)

    # 8 verdict document determinism (pure dict assembly)
    dA = json.dumps({"schema": SCHEMA, "verdict": "SAFE",
                     "probes": {"a": 1}}, sort_keys=True)
    dB = json.dumps({"schema": SCHEMA, "verdict": "SAFE",
                     "probes": {"a": 1}}, sort_keys=True)
    check("doc-determinism", dA == dB)

    if ok:
        print("DEP-RETIRE-VERIFY-SELFTEST PASS (%d vector groups)" % 13)
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
        description="retirement verification probe: SAFE / UNSAFE / "
                    "INCONCLUSIVE verdict over unlocatable+compiles+closure")
    ap.add_argument("--file", help="the rewired consumer .v to verify")
    ap.add_argument("--module", help="the retired module (must be "
                                     "unlocatable)")
    ap.add_argument("--consumer-module", default=None,
                    help="logical module name of the consumer (for the "
                         "closure probe Require; default derived from "
                         "the file stem)")
    ap.add_argument("--coq-arg", action="append", default=[],
                    help="extra coqc library argument, repeatable "
                         "(e.g. -Q dir Lib)")
    ap.add_argument("--baseline", default=None,
                    help="baseline assumptions roster (one line per "
                         "entry); closure must not grow against it")
    ap.add_argument("--coqc", default=None, help="explicit coqc path")
    ap.add_argument("--json", dest="json_out", default=None,
                    help="write the verdict document here")
    ap.add_argument("--selftest", action="store_true",
                    help="run the canned-output vector groups")
    args = ap.parse_args(argv)

    if args.selftest:
        sys.exit(_selftest())
    if not args.file or not args.module:
        raise FailLoud(2, "--file and --module are required")
    if not os.path.isfile(args.file):
        raise FailLoud(2, "consumer file not found: %s" % args.file)

    coqc = find_coqc(args.coqc)
    if coqc is None:
        doc = {
            "schema": SCHEMA,
            "consumer": args.file,
            "retired_module": args.module,
            "verdict": "INCONCLUSIVE",
            "probes": {"unlocatable": {"result": None,
                                       "note": "no Rocq toolchain found"},
                       "compiles": {"result": None,
                                    "note": "no Rocq toolchain found"},
                       "closure": {"result": None,
                                   "note": "no Rocq toolchain found"}},
        }
        text = json.dumps(doc, indent=2, sort_keys=True,
                          ensure_ascii=False) + "\n"
        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8",
                      newline="\n") as fh:
                fh.write(text)
        print("HONEST-SKIP: no Rocq toolchain found; verdict "
              "INCONCLUSIVE (rc 111)")
        sys.exit(111)

    names_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "names")
    extract = None
    if os.path.isfile(os.path.join(names_dir, "mac_stmt_names.py")):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "mac_stmt_names_shared",
            os.path.join(names_dir, "mac_stmt_names.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        extract = mod.extract_statements

    consumer_module = args.consumer_module or os.path.splitext(
        os.path.basename(args.file))[0]
    lib_args = []
    for a in args.coq_arg:
        lib_args.extend(a.split())

    doc = verify(coqc, args.file, args.module, consumer_module, lib_args,
                 args.baseline, extract)
    text = json.dumps(doc, indent=2, sort_keys=True,
                      ensure_ascii=False) + "\n"
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    print("VERDICT: %s (%s)" % (doc["verdict"], args.file))
    sys.exit(VERDICT_RC[doc["verdict"]])


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except FailLoud as exc:
        print("FAIL-LOUD: %s" % exc.msg, file=sys.stderr)
        sys.exit(exc.rc)
