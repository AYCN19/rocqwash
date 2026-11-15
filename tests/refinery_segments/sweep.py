#!/usr/bin/env python3
"""tests/refinery_segments/sweep.py -- t_refinery segment for the orchestration
pair (lean_sweep.py + verdict_diff.py), P2-6 lane.

Purpose.  Pin the contract of the two orchestration tools item by item:
  both --selftest vector groups, the verdict-table schema
  (rocqwash-verdict-diff/1 with the six buckets and a consistent total), the
  lean_sweep --taxonomy consumer pin against row_render candidate rows (C3.4
  mirror acceptance plus canonical five-form refusal faces), the designed
  SKIP faces of the compile leg, and the judge side of the ALERT double
  freeze gate at suite level.
Interface.  run_segment_sweep() -> (passed, failed, skipped, results) with
  results a list of (status, check, detail) tuples, status in
  PASS/FAIL/SKIP; importing this module spawns nothing (import-safe);
  `python -I tests/refinery_segments/sweep.py` runs the segment standalone
  and prints SEGMENT / SUMMARY / TOTAL lines.
Dependencies.  Python 3 standard library only; the two tools load from
  tools/ by absolute path and each degrades to one loud SKIP line naming
  its path while it has not landed; fixtures are synthesized in a temp dir
  per run; zero network, zero compile, zero real-tree touch.
Evidence.  The refinery work order, section 6 increment A (selftest
  vectors, verdict-table schema pin, taxonomy interface pin); compile-
  orchestration discipline rules 2/3/5 of the OAI v3 lessons; the E5 merge
  contract exercised by the integration assembler.
Exit-codes.  0 all checks green (zero FAIL); 1 at least one FAIL (each
  listed, fail loud); SKIP never counts as a pass.
"""

import json
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LEAN_SWEEP = os.path.join(ROOT, "tools", "lean_sweep.py")
VERDICT_DIFF = os.path.join(ROOT, "tools", "verdict_diff.py")

CANONICAL_FORMS = ("full", "point", "tactics", "noclassic", "band")
VERDICT_SCHEMA = "rocqwash-verdict-diff/1"
STATUS_SCHEMA = "rocqwash-lean-sweep.status/1"
TAXONOMY_SCHEMA = "rocqwash.taxonomy-candidates/1"


def _run(argv, timeout=180):
    """Run one tool subprocess (isolated interpreter, no bytecode writes)
    and normalize stdout to text (utf-8, errors replaced)."""
    proc = subprocess.run([sys.executable, "-I", "-B"] + argv,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout)
    proc.stdout = proc.stdout.decode("utf-8", errors="replace") \
        if isinstance(proc.stdout, bytes) else (proc.stdout or "")
    return proc


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _green_rows(bid, idx, boundary="OK|0"):
    rows = ["%s|%s|witness|OK|0" % (bid, idx)]
    rows += ["%s|%s|falsify_%s|OK|1" % (bid, idx, f) for f in CANONICAL_FORMS]
    rows.append("%s|%s|boundary|%s" % (bid, idx, boundary))
    return rows


def _taxonomy_row(family, forms):
    """One valid row_render candidate row (full C3.4 field set)."""
    return {"schemaVersion": 2, "familyId": family, "cluster": "c1",
            "match": {"target": "assumption.type", "regex": "Nat", "flags": ""},
            "priority": 50, "confidence": "HIGH",
            "witnessStrategy": "point bite", "witnessTemplate": {},
            "mathlibAnchors": [{"symbol": "s", "relPath": "Mathlib/X.lean",
                                "line": 1}],
            "refutationForms": list(forms), "boundaryApplicability": "none",
            "gapKeywords": ["k"], "sourceLane": "row_render",
            "sourceRowId": family + "-r1"}


def _batches_doc(family=None):
    """Batches plan for two items; familyId attached in taxonomy mode."""
    files = [{"idx": 10, "bytes": 90000, "sorryCount": 7},
             {"idx": 11, "bytes": 100, "sorryCount": 1}]
    if family:
        for item in files:
            item["familyId"] = family
    return {"schema": "rocqwash-lean-sweep.batches/1",
            "batches": [{"batchId": "bA", "files": files}]}


def _check_tool_selftest(results, tool_path, token, name):
    """One loud SKIP while the tool has not landed; the selftest token must
    appear on stdout and rc must be 0."""
    if not os.path.isfile(tool_path):
        results.append(("SKIP", name, "tool not landed yet: %s" % tool_path))
        return (0, 0, 1)
    proc = _run([tool_path, "--selftest"])
    if proc.returncode == 0 and token in proc.stdout:
        brief = [line for line in proc.stdout.splitlines() if token in line]
        results.append(("PASS", name, brief[-1] if brief else token))
        return (1, 0, 0)
    results.append(("FAIL", name, "rc=%d, missing token %r; stdout tail: %s"
                    % (proc.returncode, token, proc.stdout[-300:])))
    return (0, 1, 0)


def _check_verdict_schema(results, tmp):
    """Schema pin: a clean ledger table must report schema
    rocqwash-verdict-diff/1, all six buckets, and counts consistent with
    the total (primary buckets only)."""
    if not os.path.isfile(VERDICT_DIFF):
        results.append(("SKIP", "verdict-schema",
                        "tool not landed yet: %s" % VERDICT_DIFF))
        return (0, 0, 1)
    lane = os.path.join(tmp, "schema-lane.tsv")
    _write(lane, "\n".join(_green_rows("bS", 10)
                           + _green_rows("bS", 11, "SKIP-TIERT|-")) + "\n")
    out = os.path.join(tmp, "schema-report.json")
    proc = _run([VERDICT_DIFF, "--results-lane", lane, "--json", out])
    if proc.returncode != 0:
        results.append(("FAIL", "verdict-schema",
                        "clean table rc=%d: %s" % (proc.returncode, proc.stdout[-200:])))
        return (0, 1, 0)
    rep = json.load(open(out, encoding="utf-8"))
    buckets = ("GREEN", "ALERT", "BLOCKED", "MISSING", "EXCEPTION",
               "SKIPPED-TIERT")
    problems = []
    if rep.get("schema") != VERDICT_SCHEMA:
        problems.append("schema=%r" % rep.get("schema"))
    for bucket in buckets:
        if bucket not in rep.get("counts", {}):
            problems.append("missing bucket %s" % bucket)
    total = rep.get("total")
    primary = sum(rep.get("counts", {}).get(b, 0)
                  for b in ("GREEN", "ALERT", "BLOCKED", "MISSING", "EXCEPTION"))
    if total != primary:
        problems.append("total=%r vs primary sum=%d" % (total, primary))
    if problems:
        results.append(("FAIL", "verdict-schema", "; ".join(problems)))
        return (0, 1, 0)
    results.append(("PASS", "verdict-schema",
                    "%s pinned; six buckets; total %d == primary sum"
                    % (VERDICT_SCHEMA, total)))
    return (1, 0, 0)


def _check_taxonomy_pin(results, tmp):
    """Interface pin: lean_sweep --taxonomy consumes row_render candidate
    rows; a valid plan sweeps (status carries the taxonomy summary), a
    non-canonical refutationForms row is refused rc=2, a row missing a
    required field is refused rc=2 naming the field."""
    if not os.path.isfile(LEAN_SWEEP):
        results.append(("SKIP", "taxonomy-pin",
                        "tool not landed yet: %s" % LEAN_SWEEP))
        return (0, 0, 1)
    out = os.path.join(tmp, "tax-out")
    items = os.path.join(out, "items", "bA")
    _write(os.path.join(items, "10", "witness.lean"), "theorem w : True := trivial\n")
    batches = os.path.join(tmp, "tax-batches.json")
    _write(batches, json.dumps(_batches_doc("fam.alpha"), ensure_ascii=False))
    good = os.path.join(tmp, "tax-good.json")
    _write(good, json.dumps({"schema": TAXONOMY_SCHEMA,
                             "rows": [_taxonomy_row("fam.alpha",
                                                    ["full", "point"])]},
                            ensure_ascii=False))
    proc = _run([LEAN_SWEEP, "--batches", batches, "--out", out,
                 "--taxonomy", good, "--lanes", "2",
                 "--json", os.path.join(out, "status.json")])
    problems = []
    if proc.returncode != 0:
        problems.append("valid plan rc=%d: %s" % (proc.returncode, proc.stdout[-200:]))
    else:
        status = json.load(open(os.path.join(out, "status.json"), encoding="utf-8"))
        if status.get("schema") != STATUS_SCHEMA:
            problems.append("status schema=%r" % status.get("schema"))
        tax = status.get("taxonomy") or {}
        if tax.get("rows") != 1 or tax.get("families") != 1 \
                or tax.get("forms_union") != ["full", "point"]:
            problems.append("taxonomy summary incomplete: %r" % tax)
    bad_forms = os.path.join(tmp, "tax-bad-forms.json")
    _write(bad_forms, json.dumps({"rows": [_taxonomy_row("fam.alpha",
                                                         ["full", "legacy_op"])]},
                                  ensure_ascii=False))
    proc = _run([LEAN_SWEEP, "--batches", batches, "--out", os.path.join(tmp, "t2"),
                 "--taxonomy", bad_forms, "--lanes", "2"])
    if proc.returncode != 2 or "canonical five-form" not in proc.stdout:
        problems.append("non-canonical forms: rc=%d (want 2), stdout tail %s"
                        % (proc.returncode, proc.stdout[-160:]))
    row = _taxonomy_row("fam.alpha", ["full"])
    del row["priority"]
    nofield = os.path.join(tmp, "tax-nofield.json")
    _write(nofield, json.dumps({"rows": [row]}, ensure_ascii=False))
    proc = _run([LEAN_SWEEP, "--batches", batches, "--out", os.path.join(tmp, "t3"),
                 "--taxonomy", nofield, "--lanes", "2"])
    if proc.returncode != 2 or "priority" not in proc.stdout:
        problems.append("missing field: rc=%d (want 2), stdout tail %s"
                        % (proc.returncode, proc.stdout[-160:]))
    if problems:
        results.append(("FAIL", "taxonomy-pin", "; ".join(problems)))
        return (0, 1, 0)
    results.append(("PASS", "taxonomy-pin",
                    "candidate rows consumed (rows/families/forms_union in"
                    " status); non-canonical forms rc2; missing field rc2"
                    " named"))
    return (1, 0, 0)


def _check_designed_skip(results, tmp):
    """The compile leg is a designed SKIP: the default face declares it and
    exits 0; --fire without a toolchain declares SKIP-TOOLCHAIN-ABSENT and
    exits 0 without ledgers."""
    if not os.path.isfile(LEAN_SWEEP):
        results.append(("SKIP", "designed-skip",
                        "tool not landed yet: %s" % LEAN_SWEEP))
        return (0, 0, 1)
    batches = os.path.join(tmp, "skip-batches.json")
    _write(batches, json.dumps(_batches_doc(), ensure_ascii=False))
    problems = []
    out1 = os.path.join(tmp, "skip-default")
    proc = _run([LEAN_SWEEP, "--batches", batches, "--out", out1, "--lanes", "2",
                 "--json", os.path.join(out1, "status.json")])
    if proc.returncode != 0 or "compile leg: design SKIP" not in proc.stdout:
        problems.append("default face rc=%d stdout tail %s"
                        % (proc.returncode, proc.stdout[-200:]))
    else:
        status = json.load(open(os.path.join(out1, "status.json"), encoding="utf-8"))
        if status.get("compile_leg") != "design-skip":
            problems.append("compile_leg=%r" % status.get("compile_leg"))
    out2 = os.path.join(tmp, "skip-fire")
    absent_lake = os.path.join(tmp, "no-such-lake.exe")
    proc = _run([LEAN_SWEEP, "--batches", batches, "--out", out2, "--fire",
                 "--lake", absent_lake, "--lanes", "2",
                 "--json", os.path.join(out2, "status.json")])
    if proc.returncode != 0 or "SKIP-TOOLCHAIN-ABSENT" not in proc.stdout:
        problems.append("fire face rc=%d stdout tail %s"
                        % (proc.returncode, proc.stdout[-200:]))
    else:
        status = json.load(open(os.path.join(out2, "status.json"), encoding="utf-8"))
        if status.get("compile_leg") != "skip-toolchain-absent":
            problems.append("fire compile_leg=%r" % status.get("compile_leg"))
        leftovers = [f for f in os.listdir(out2) if f.startswith("results-lane")]
        if leftovers:
            problems.append("no-toolchain fire wrote ledgers: %s" % leftovers)
    if problems:
        results.append(("FAIL", "designed-skip", "; ".join(problems)))
        return (0, 1, 0)
    results.append(("PASS", "designed-skip",
                    "default face declares design-skip; fire without"
                    " toolchain declares skip-toolchain-absent, zero ledgers"))
    return (1, 0, 0)


def _check_alert_gate(results, tmp):
    """Judge side of the ALERT double freeze gate at suite level: one
    canonical falsify row at rc=0 must turn the table rc=2 with the freeze
    banner (the lane marker side is pinned inside the lean_sweep selftest)."""
    if not os.path.isfile(VERDICT_DIFF):
        results.append(("SKIP", "alert-gate",
                        "tool not landed yet: %s" % VERDICT_DIFF))
        return (0, 0, 1)
    lane = os.path.join(tmp, "alert-lane.tsv")
    rows = _green_rows("bG", 70)
    rows[-2] = "bG|70|falsify_band|OK|0"
    _write(lane, "\n".join(rows) + "\n")
    proc = _run([VERDICT_DIFF, "--results-lane", lane])
    if proc.returncode == 2 and "ALERT FREEZE GATE" in proc.stdout \
            and "bG|70" in proc.stdout:
        results.append(("PASS", "alert-gate",
                        "falsify rc=0 -> rc2 freeze banner naming the item"))
        return (1, 0, 0)
    results.append(("FAIL", "alert-gate",
                    "rc=%d (want 2); banner/item named: %s"
                    % (proc.returncode,
                       "ALERT FREEZE GATE" in proc.stdout and "bG|70" in proc.stdout)))
    return (0, 1, 0)


def _check_taxonomy_live_draft(results):
    """Live interface pin (work order increment D chain): when the row_render
    draft exists, the real candidate rows must pass the consumer pin
    (load_taxonomy acceptance with the rows/families/forms_union summary);
    one loud SKIP names the draft while it has not landed."""
    if not os.path.isfile(LEAN_SWEEP):
        results.append(("SKIP", "taxonomy-live-draft",
                        "tool not landed yet: %s" % LEAN_SWEEP))
        return (0, 0, 1)
    draft = os.path.join(ROOT, "docs", "drafts", "taxonomy-candidates.json")
    if not os.path.isfile(draft):
        results.append(("SKIP", "taxonomy-live-draft",
                        "row_render draft not landed yet: %s" % draft))
        return (0, 0, 1)
    import importlib.util
    spec = importlib.util.spec_from_file_location("t_ref_sweep_lean_sweep",
                                                  LEAN_SWEEP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        rows, forms, summary = mod.load_taxonomy(draft)
    except mod.FormError as exc:
        results.append(("FAIL", "taxonomy-live-draft",
                        "real draft refused by the consumer pin: %s" % exc))
        return (0, 1, 0)
    results.append(("PASS", "taxonomy-live-draft",
                    "real row_render draft consumed: %d rows, %d families,"
                    " forms union %s"
                    % (summary["rows"], summary["families"],
                       ",".join(summary["forms_union"]))))
    return (1, 0, 0)


def run_segment_sweep():
    """Run every check; returns (passed, failed, skipped, results)."""
    results = []
    tmp = tempfile.mkdtemp(prefix="rocqwash_t_refinery_sweep_")
    try:
        tally = [0, 0, 0]
        tally = [a + b for a, b in zip(tally, _check_tool_selftest(
            results, LEAN_SWEEP, "LEAN-SWEEP-SELFTEST PASS", "lean-sweep-selftest"))]
        tally = [a + b for a, b in zip(tally, _check_tool_selftest(
            results, VERDICT_DIFF, "VERDICT-DIFF-SELFTEST PASS",
            "verdict-diff-selftest"))]
        tally = [a + b for a, b in zip(tally, _check_verdict_schema(results, tmp))]
        tally = [a + b for a, b in zip(tally, _check_taxonomy_pin(results, tmp))]
        tally = [a + b for a, b in zip(tally, _check_taxonomy_live_draft(results))]
        tally = [a + b for a, b in zip(tally, _check_designed_skip(results, tmp))]
        tally = [a + b for a, b in zip(tally, _check_alert_gate(results, tmp))]
        return tally[0], tally[1], tally[2], results
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    passed, failed, skipped, results = run_segment_sweep()
    for status, name, detail in results:
        print("%s sweep/%s -- %s" % (status, name, detail))
    print("SEGMENT sweep passed=%d failed=%d skipped=%d"
          % (passed, failed, skipped))
    print("SUMMARY segments=1 passed=%d failed=%d skipped=%d"
          % (passed, failed, skipped))
    if failed:
        print("TOTAL-SWEEP-SEGMENT RED (%d failed check(s))" % failed)
        return 1
    print("TOTAL-SWEEP-SEGMENT GREEN (%d passed, %d skipped)"
          % (passed, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
