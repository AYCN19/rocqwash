#!/usr/bin/env python3
"""verdict_diff.py - mechanical judge for vacuity probe sweep results.
Purpose.  Merges the per-lane sweep ledgers into one judgment table with the
  canonical verdict buckets GREEN / ALERT / BLOCKED / MISSING / SKIPPED-TIERT
  plus a named exception list, records lane conflicts, and (with --baseline)
  diffs two judgment tables under the baseline-diff convergence caliber
  (verdict reads only the failing-key movement: fewer failing is converged).
Interface.  python -I tools/verdict_diff.py --results-lane
  "DIR/results-lane*.tsv" [--expected F | --batches F] [--json F] [--md F]
  [--baseline OLD.json] | --selftest.  Report schema rocqwash-verdict-diff/1.
  Judged per item (batchId|idx): ALERT = any canonical falsify rc=0
  (stop-work freeze, judge side of the double gate); BLOCKED = witness or
  boundary fired with rc!=0; GREEN = witness rc=0 AND all five canonical
  falsify forms at rc=1 AND boundary rc=0 or SKIP-TIERT; MISSING = expected
  item with zero rows (only with an expected universe, otherwise declared
  not-computed); EXCEPTION = every unjudgeable shape, each with a reason.
Dependencies.  Python 3 standard library only; lane ledgers in the canonical
  five-column form batchId|idx|probe|status|rc; zero network, zero compile,
  deterministic report (no wall clock on the report face).
Evidence.  Judge side of the ALERT freeze gate (rule 5: lean_sweep.py
  writes the lane marker, this judge counts and exits 2) and of the
  canonical caliber (rule 3: only full/point/tactics/noclassic/band judge
  GREEN; legacy faces land in the exception list).  Divergences from the
  packaged seed (verdict_diff_seed.py, OAI v3 lessons): key caliber
  batchId|idx|probe; GREEN needs all five forms; the universe feeds MISSING;
  BLOCKED, tier notes, conflicts and baseline are new.
Exit-codes.  0 clean table; 1 failing data (BLOCKED / MISSING / EXCEPTION,
  or baseline degraded; a failing result is data, loud on stdout); 2 ALERT
  freeze gate (stop-work) or usage or malformed form (the banner names
  which); 9 missing input path.
"""
# Extended contract (30-line header budget).  GREEN with a tier-skipped
# boundary is GREEN and also listed in the SKIPPED-TIERT annotation bucket
# (an item appears in exactly one primary bucket; the tier face is an
# annotation, not a primary verdict).  Lane ledger readers tolerate rows
# with extra columns and count malformed rows loud instead of dropping them
# silently.  Conflicts (same key, differing rc or status across lane files)
# resolve max-lane (later glob order wins, the seed caliber) and stay on
# the conflict list for the operator.

import argparse
import glob
import json
import os
import sys

PROG = "verdict_diff"
SCHEMA = "rocqwash-verdict-diff/1"
BATCHES_SCHEMA = "rocqwash-lean-sweep.batches/1"
CANONICAL_FORMS = ("full", "point", "tactics", "noclassic", "band")
FALSIFY_PROBES = tuple("falsify_" + f for f in CANONICAL_FORMS)
POSITIVE_PROBES = ("witness", "boundary")
OK_STATUS = "OK"
TIER_STATUS = "SKIP-TIERT"
BUCKETS = ("GREEN", "ALERT", "BLOCKED", "MISSING", "EXCEPTION", "SKIPPED-TIERT")
FAILING_BUCKETS = ("ALERT", "BLOCKED", "MISSING", "EXCEPTION")
CONFLICT_CAP = 10


class FormError(Exception):
    """Malformed input form (rc=2; fail-loud, no report emitted)."""


class MissingPath(Exception):
    """Missing input path (rc=9; fail-loud, no simulation)."""


# ---- lane ledger merge (per-lane files; union across all lanes) --------------

def load_lane_results(pattern):
    """Union all lane ledgers matching the glob (compile rule 1: one ledger
    per lane, the judge merges; a shared single ledger is the 696-line
    interleave lesson).  Returns (rows, conflicts, malformed_count,
    matched_files).  Row form: batchId|idx|probe|status|rc (extra columns
    tolerated).  A key seen again with a differing rc or status is a
    conflict; max-lane resolution: the later file in glob order wins."""
    files = sorted(glob.glob(pattern))
    if not files:
        raise MissingPath("no lane ledger matches: %s" % pattern)
    rows, conflicts, malformed = {}, [], 0
    for path in files:
        source = os.path.basename(path)
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) < 4:
                    malformed += 1
                    continue
                key = "%s|%s|%s" % (parts[0].strip(), parts[1].strip(),
                                    parts[2].strip())
                status = parts[3].strip()
                rc_text = parts[4].strip() if len(parts) >= 5 else "-"
                if status == TIER_STATUS:
                    rc = None
                elif status == OK_STATUS and rc_text.lstrip("-").isdigit():
                    rc = int(rc_text)
                else:
                    malformed += 1
                    continue
                val = {"status": status, "rc": rc, "source": source}
                old = rows.get(key)
                if old is not None and (old["rc"] != val["rc"]
                                        or old["status"] != val["status"]):
                    conflicts.append({"key": key, "old": old, "new": val})
                rows[key] = val
    return rows, conflicts, malformed, files


def expected_universe(expected_path, batches_path):
    """Expected item keys from --expected ({"items": ["batchId|idx"]} or a
    bare list) or from a sweep --batches plan (all batchId|idx pairs).  At
    most one source; neither given means the MISSING face is declared
    not-computed (a negative MISSING claim is never made without a
    universe)."""
    if expected_path and batches_path:
        raise FormError("--expected and --batches are alternative universe"
                        " sources; give at most one")
    if expected_path:
        if not os.path.isfile(expected_path):
            raise MissingPath("expected universe file missing: %s" % expected_path)
        try:
            with open(expected_path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (ValueError, UnicodeDecodeError) as exc:
            raise FormError("expected universe JSON parse failure: %s (%s)"
                            % (expected_path, exc))
        items = doc.get("items") if isinstance(doc, dict) else doc
        if not isinstance(items, list) or \
                not all(isinstance(x, str) for x in items):
            raise FormError("expected universe malformed: items must be a list"
                            " of batchId|idx strings")
        return {"source": "expected", "count": len(items),
                "keys": sorted(set(items))}
    if batches_path:
        if not os.path.isfile(batches_path):
            raise MissingPath("batches file missing: %s" % batches_path)
        try:
            with open(batches_path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (ValueError, UnicodeDecodeError) as exc:
            raise FormError("batches JSON parse failure: %s (%s)"
                            % (batches_path, exc))
        batches = doc.get("batches") if isinstance(doc, dict) else doc
        if not isinstance(batches, list):
            raise FormError("batches malformed: expected a list of batches")
        keys = set()
        for batch in batches:
            bid = batch.get("batchId") if isinstance(batch, dict) else None
            for item in (batch.get("files") or []) if isinstance(batch, dict) else []:
                idx = item.get("idx") if isinstance(item, dict) else None
                if isinstance(bid, str) and isinstance(idx, int):
                    keys.add("%s|%s" % (bid, idx))
        return {"source": "batches", "count": len(keys), "keys": sorted(keys)}
    return {"source": "none", "count": 0, "keys": []}


# ---- judgment core (pure; deterministic) -------------------------------------

def judge(rows, universe):
    """Judge every item with at least one ledger row, plus every expected
    item with none (MISSING, only when a universe is given).  One primary
    bucket per item in the order ALERT > BLOCKED > EXCEPTION > MISSING >
    GREEN; SKIPPED-TIERT is an annotation set.  Deterministic: sorted keys
    throughout."""
    by_item = {}
    for key, val in rows.items():
        probe = key.rsplit("|", 1)[1]
        bid_idx = key[: -(len(probe) + 1)]
        by_item.setdefault(bid_idx, {})[probe] = val
    verdict = {bucket: [] for bucket in BUCKETS}
    exceptions = []
    for bid_idx in sorted(by_item):
        probes = by_item[bid_idx]
        bucket, reason = _judge_item(probes)
        if bucket == "EXCEPTION":
            exceptions.append({"key": bid_idx, "reason": reason})
            verdict["EXCEPTION"].append(bid_idx)
        else:
            verdict[bucket].append(bid_idx)
        if any(p["status"] == TIER_STATUS for p in probes.values()):
            verdict["SKIPPED-TIERT"].append(bid_idx)
    missing = []
    if universe["source"] != "none":
        for key in universe["keys"]:
            if key not in by_item and key not in verdict["MISSING"]:
                missing.append(key)
        verdict["MISSING"] = sorted(set(verdict["MISSING"]) | set(missing))
    return verdict, exceptions


def _judge_item(probes):
    """One item's probe rows -> (primary bucket, exception reason or None).
    ALERT first (vacuity evidence outranks everything), then BLOCKED
    (expected-green faces red), then EXCEPTION shapes, then GREEN."""
    legacy = [p for p in probes
              if p.startswith("falsify_") and p not in FALSIFY_PROBES]
    if legacy:
        return ("EXCEPTION",
                "legacy falsify face %s present (canonical caliber: only %s"
                " judge GREEN; the legacy face must be re-cast before it"
                " mixes into any count)" % (", ".join(sorted(legacy)),
                                            ", ".join(FALSIFY_PROBES)))
    for name in sorted(probes):
        row = probes[name]
        if row["status"] == TIER_STATUS and name != "boundary":
            return ("EXCEPTION",
                    "%s carries %s status (the tier caliber applies to the"
                    " boundary face only)" % (name, TIER_STATUS))
    falsifies = [probes[name] for name in FALSIFY_PROBES if name in probes]
    for row in falsifies:
        if row["status"] == OK_STATUS and row["rc"] == 0:
            return ("ALERT", None)
    for name in ("witness", "boundary"):
        row = probes.get(name)
        if row is not None and row["status"] == OK_STATUS and row["rc"] != 0:
            return ("BLOCKED",
                    "%s expected green, fired rc=%s (probe defect or"
                    " toolchain face, not vacuity evidence)" % (name, row["rc"]))
    for row in falsifies:
        if row["status"] == OK_STATUS and row["rc"] not in (0, 1):
            return ("EXCEPTION",
                    "falsify rc out of band (%s: rc=%s; expected 0 alert or"
                    " 1 expected-fail)" % (
                        next(n for n in FALSIFY_PROBES
                             if probes[n] is row), row["rc"]))
    witness = probes.get("witness")
    if witness is None:
        return ("EXCEPTION",
                "no witness row among %d row(s) (partial coverage: the item"
                " cannot be judged without its witness face)"
                % len(probes))
    boundary = probes.get("boundary")
    forms_present = [n for n in FALSIFY_PROBES if n in probes]
    if witness["status"] == OK_STATUS and witness["rc"] == 0:
        if len(forms_present) == len(FALSIFY_PROBES) \
                and boundary is not None \
                and (boundary["status"] == TIER_STATUS
                     or (boundary["status"] == OK_STATUS and boundary["rc"] == 0)):
            return ("GREEN", None)
        return ("EXCEPTION",
                "partial coverage: %d/%d canonical falsify forms present,"
                " boundary %s (GREEN needs all five forms at rc=1 and a"
                " boundary face at rc=0 or %s)"
                % (len(forms_present), len(FALSIFY_PROBES),
                   "absent" if boundary is None else
                   "rc=%s" % boundary.get("rc"), TIER_STATUS))
    return ("EXCEPTION",
            "witness face unjudgeable (status=%s rc=%s)"
            % (witness["status"], witness["rc"]))


def failing_keys_of(verdict):
    """Failing key set for the baseline convergence caliber (the union of
    the four failing buckets; GREEN and tier annotations never drive it)."""
    keys = []
    for bucket in FAILING_BUCKETS:
        for entry in verdict.get(bucket, []):
            keys.append(entry["key"] if isinstance(entry, dict) else entry)
    return sorted(set(keys))


# ---- baseline differential convergence (the baseline-diff caliber) ------------

def baseline_diff(old, current_keys):
    """Old judgment-table report vs current failing keys -> convergence
    report.  Verdict reads only the failing-key count movement (fewer
    failing is converged), the same law as tools/baseline_diff.py: wall
    faces and GREEN movement never drive the verdict.  A report whose
    schema is not rocqwash-verdict-diff/1 is a form error (rc=2)."""
    if not isinstance(old, dict) or old.get("schema") != SCHEMA:
        raise FormError("baseline report schema %r is not %s (this tool diffs"
                        " only its own judgment tables)"
                        % (old.get("schema") if isinstance(old, dict) else None,
                           SCHEMA))
    old_keys = old.get("failing_keys")
    if not isinstance(old_keys, list):
        old_keys = failing_keys_of(old.get("verdict", {}))
    old_keys = sorted(set(old_keys))
    new_set, old_set = set(current_keys), set(old_keys)
    resolved = sorted(old_set - new_set)
    new_failing = sorted(new_set - old_set)
    persistent = sorted(old_set & new_set)
    delta = len(new_set) - len(old_set)
    verdict = ("converged" if delta < 0 else "degraded" if delta > 0
               else "stable")
    return {"verdict": verdict, "old_failing": len(old_set),
            "new_failing": len(new_set), "delta": delta,
            "resolved": resolved, "new_blocks": new_failing,
            "persistent": persistent}


# ---- report faces --------------------------------------------------------------

def build_report(verdict, exceptions, conflicts, malformed, files,
                 universe, baseline):
    """Assemble the report dict (deterministic: sorted lists, no wall
    clock; conflicts capped on the embedded face, full count kept)."""
    total = sum(len(verdict[b]) for b in ("GREEN", "ALERT", "BLOCKED",
                                          "MISSING", "EXCEPTION"))
    report = {
        "schema": SCHEMA,
        "total": total,
        "counts": {b: len(verdict[b]) for b in BUCKETS},
        "verdict": verdict,
        "exceptions": exceptions,
        "conflicts": conflicts[:CONFLICT_CAP],
        "conflict_count": len(conflicts),
        "malformed_rows": malformed,
        "lane_files": [os.path.basename(f) for f in files],
        "expected_universe": {"source": universe["source"],
                              "count": universe["count"]},
        "missing_face": ("computed" if universe["source"] != "none" else
                         "not-computed (no expected universe given; no"
                         " MISSING claim is made)"),
        "failing_keys": failing_keys_of(verdict),
        "ok": not any(verdict[b] for b in ("ALERT", "MISSING")),
        "baseline": baseline,
    }
    return report


def report_md(report):
    """Human reading face (deterministic; same input byte-identical)."""
    counts = report["counts"]
    lines = ["# Verdict Table (%s)" % report["schema"], ""]
    lines.append("- lanes merged: %s" % (", ".join(report["lane_files"]) or "-"))
    lines.append("- expected universe: %s (%s)" % (report["expected_universe"]["source"],
                                                   report["missing_face"]))
    lines.append("")
    lines.append("| verdict | items |")
    lines.append("|---|---|")
    for bucket in BUCKETS:
        lines.append("| %s | %d |" % (bucket, counts[bucket]))
    lines.append("")
    lines.append("**ok: %s** (ALERT=%d, MISSING=%d)"
                 % (str(report["ok"]).lower(), counts["ALERT"], counts["MISSING"]))
    if report["exceptions"]:
        lines.append("")
        lines.append("## exceptions (%d)" % counts["EXCEPTION"])
        lines.append("")
        lines.append("| item | reason |")
        lines.append("|---|---|")
        for exc in report["exceptions"]:
            lines.append("| %s | %s |" % (exc["key"], exc["reason"].replace("|", "\\|")))
    if report["conflict_count"]:
        lines.append("")
        lines.append("## lane conflicts (%d, first %d embedded)"
                     % (report["conflict_count"], len(report["conflicts"])))
        for conflict in report["conflicts"]:
            lines.append("- %s: %s@%s vs %s@%s"
                         % (conflict["key"], conflict["old"]["source"],
                            conflict["old"]["rc"], conflict["new"]["source"],
                            conflict["new"]["rc"]))
    if report["baseline"] is not None:
        base = report["baseline"]
        lines.append("")
        lines.append("## baseline convergence (%s)" % base["verdict"])
        lines.append("")
        lines.append("- failing: %d -> %d (delta %+d)"
                     % (base["old_failing"], base["new_failing"], base["delta"]))
        lines.append("- resolved: %s" % (", ".join(base["resolved"]) or "-"))
        lines.append("- new: %s" % (", ".join(base["new_blocks"]) or "-"))
        lines.append("- persistent: %s" % (", ".join(base["persistent"]) or "-"))
    lines.append("")
    return "\n".join(lines)


def print_report(report):
    """Loud stdout face; the ALERT banner is the judge side of the freeze
    gate (rule 5)."""
    counts = report["counts"]
    print("=== VERDICT-DIFF judgment table (%s) ===" % report["schema"])
    print("lanes merged: %d file(s); malformed rows %d; conflicts %d"
          % (len(report["lane_files"]), report["malformed_rows"],
             report["conflict_count"]))
    print("expected universe: %s (%s)" % (report["expected_universe"]["source"],
                                          report["missing_face"]))
    print(" | ".join("%s=%d" % (b, counts[b]) for b in BUCKETS))
    if report["conflict_count"]:
        print("conflicts (max-lane resolution, first %d):" % len(report["conflicts"]))
        for conflict in report["conflicts"]:
            print("  %s: %s@%s vs %s@%s" % (conflict["key"],
                  conflict["old"]["source"], conflict["old"]["rc"],
                  conflict["new"]["source"], conflict["new"]["rc"]))
    if report["baseline"] is not None:
        base = report["baseline"]
        print("BASELINE: %s (failing %d -> %d, delta %+d; resolved %d, new %d,"
              " persistent %d)" % (base["verdict"], base["old_failing"],
                                   base["new_failing"], base["delta"],
                                   len(base["resolved"]),
                                   len(base["new_blocks"]),
                                   len(base["persistent"])))
    if counts["ALERT"]:
        print("ALERT FREEZE GATE: %d item(s) with a canonical falsify probe at"
              " rc=0; stop-work (lane markers and this count form the double"
              " gate)" % counts["ALERT"])
        for key in report["verdict"]["ALERT"]:
            print("  ALERT %s" % key)


# ---- selftest (embedded vectors; tmp-synthesized ledgers; zero network) -------

def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _green_rows(bid, idx, boundary="OK|0"):
    """Ledger rows of a fully GREEN item (witness 0, five forms 1)."""
    rows = ["%s|%s|witness|OK|0" % (bid, idx)]
    rows += ["%s|%s|falsify_%s|OK|1" % (bid, idx, f) for f in CANONICAL_FORMS]
    rows.append("%s|%s|boundary|%s" % (bid, idx, boundary))
    return rows


def selftest():
    """Seven vectors on tmp fixtures: GREEN plus tier annotation / ALERT
    freeze rc=2 / BLOCKED plus out-of-band EXCEPTION rc=1 / MISSING with and
    without a universe / lane conflicts plus malformed rows / partial
    coverage and legacy-form exceptions / baseline convergence plus CLI
    refusals.  Zero compile, zero network, zero real-tree touch."""
    import shutil
    import subprocess
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_verdict_diff_self_")
    try:
        tool = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            PROG + ".py")

        def run(argv):
            proc = subprocess.run([sys.executable, "-B", tool] + argv,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, timeout=120)
            proc.stdout = proc.stdout.decode("utf-8", errors="replace") \
                if isinstance(proc.stdout, bytes) else (proc.stdout or "")
            return proc

        # vector 1: GREEN (full five forms) plus a tier-skipped boundary
        #   annotation; clean table rc=0; counts and total consistent
        lane1 = os.path.join(tmp, "results-lane1.tsv")
        _write(lane1, "\n".join(_green_rows("bA", 10)
                                + _green_rows("bA", 11, "SKIP-TIERT|-")) + "\n")
        out1 = os.path.join(tmp, "v1.json")
        proc = run(["--results-lane", lane1, "--json", out1])
        assert proc.returncode == 0, (proc.returncode, proc.stdout)
        rep = json.load(open(out1, encoding="utf-8"))
        assert rep["schema"] == SCHEMA, rep["schema"]
        assert rep["counts"]["GREEN"] == 2 and rep["counts"]["SKIPPED-TIERT"] == 1, rep["counts"]
        assert rep["verdict"]["SKIPPED-TIERT"] == ["bA|11"], rep["verdict"]
        assert rep["ok"] is True and rep["failing_keys"] == [], rep
        assert rep["total"] == rep["counts"]["GREEN"] + rep["counts"]["ALERT"] \
            + rep["counts"]["BLOCKED"] + rep["counts"]["MISSING"] \
            + rep["counts"]["EXCEPTION"], "total must span the primary buckets"
        print("vector 1 GREEN table (five-form caliber; tier annotation;"
              " counts/total consistent; rc0): PASS")

        # vector 2: ALERT freeze gate (falsify_band rc=0): rc=2, banner names
        #   the item, judge side of the double gate
        lane2 = os.path.join(tmp, "results-lane2.tsv")
        rows2 = _green_rows("bB", 20)
        rows2[-2] = "bB|20|falsify_band|OK|0"
        _write(lane2, "\n".join(rows2) + "\n")
        proc = run(["--results-lane", lane2, "--json", os.path.join(tmp, "v2.json")])
        assert proc.returncode == 2, (proc.returncode, proc.stdout)
        assert "ALERT FREEZE GATE" in proc.stdout and "bB|20" in proc.stdout, proc.stdout
        rep2 = json.load(open(os.path.join(tmp, "v2.json"), encoding="utf-8"))
        assert rep2["verdict"]["ALERT"] == ["bB|20"] and rep2["ok"] is False, rep2
        print("vector 2 ALERT freeze gate (falsify rc=0 -> rc2, banner, judge"
              " side of the double gate): PASS")

        # vector 3: BLOCKED (witness red) plus out-of-band falsify rc (124):
        #   failing data rc=1, exception list carries the reasons
        lane3 = os.path.join(tmp, "results-lane3.tsv")
        rows3 = ["bC|30|witness|OK|2"]
        rows3 += ["bC|30|falsify_%s|OK|1" % f for f in CANONICAL_FORMS[:2]]
        rows3 += ["bC|31|witness|OK|0", "bC|31|falsify_full|OK|124"]
        _write(lane3, "\n".join(rows3) + "\n")
        proc = run(["--results-lane", lane3, "--json", os.path.join(tmp, "v3.json")])
        assert proc.returncode == 1, (proc.returncode, proc.stdout)
        rep3 = json.load(open(os.path.join(tmp, "v3.json"), encoding="utf-8"))
        assert rep3["verdict"]["BLOCKED"] == ["bC|30"], rep3["verdict"]
        reasons = {e["key"]: e["reason"] for e in rep3["exceptions"]}
        assert "bC|31" in reasons and "out of band" in reasons["bC|31"], reasons
        print("vector 3 BLOCKED + out-of-band EXCEPTION (rc1 failing data;"
              " reasons name the shape): PASS")

        # vector 4: MISSING face - computed with a universe, declared
        #   not-computed without one (a negative MISSING claim needs a
        #   universe; negative-finding boundary law)
        expected = os.path.join(tmp, "expected.json")
        _write(expected, json.dumps({"items": ["bA|10", "bZ|99"]}))
        proc = run(["--results-lane", lane1, "--expected", expected,
                    "--json", os.path.join(tmp, "v4.json")])
        assert proc.returncode == 1, (proc.returncode, proc.stdout)
        rep4 = json.load(open(os.path.join(tmp, "v4.json"), encoding="utf-8"))
        assert rep4["verdict"]["MISSING"] == ["bZ|99"], rep4["verdict"]
        assert rep4["missing_face"] == "computed", rep4
        proc = run(["--results-lane", lane1, "--json", os.path.join(tmp, "v4b.json")])
        assert proc.returncode == 0, proc.returncode
        rep4b = json.load(open(os.path.join(tmp, "v4b.json"), encoding="utf-8"))
        assert rep4b["missing_face"].startswith("not-computed"), rep4b
        assert rep4b["counts"]["MISSING"] == 0, "no universe, no MISSING claim"
        print("vector 4 MISSING face (computed from a universe; declared"
              " not-computed without one): PASS")

        # vector 5: lane merge - union across two lane files, conflict
        #   recorded (same key, differing rc), malformed rows counted loud
        laneA = os.path.join(tmp, "results-laneA.tsv")
        laneB = os.path.join(tmp, "results-laneB.tsv")
        _write(laneA, "\n".join(_green_rows("bD", 40)) + "\nbD|41|witness|OK|1\n")
        _write(laneB, "bD|41|witness|OK|0\ngarbage line\nshort|row\n")
        proc = run(["--results-lane", os.path.join(tmp, "results-lane[AB].tsv"),
                    "--json", os.path.join(tmp, "v5.json")])
        rep5 = json.load(open(os.path.join(tmp, "v5.json"), encoding="utf-8"))
        assert rep5["conflict_count"] == 1, rep5
        assert rep5["conflicts"][0]["key"] == "bD|41|witness", rep5["conflicts"]
        assert rep5["malformed_rows"] == 2, rep5["malformed_rows"]
        assert rep5["verdict"]["GREEN"] == ["bD|40"], rep5["verdict"]
        assert rep5["verdict"]["EXCEPTION"] == ["bD|41"], "single witness row = partial"
        print("vector 5 lane merge (union dedup, conflict recorded with both"
              " sources, malformed rows counted): PASS")

        # vector 6: exception shapes - partial coverage (3/5 forms),
        #   legacy falsify face refused from GREEN, SKIP-TIERT on witness
        lane6 = os.path.join(tmp, "results-lane6.tsv")
        rows6 = ["bE|50|witness|OK|0"]
        rows6 += ["bE|50|falsify_%s|OK|1" % f for f in CANONICAL_FORMS[:3]]
        rows6 += ["bE|50|boundary|OK|0",
                  "bE|51|witness|OK|0",
                  "bE|51|falsify_op_legacy|OK|1",
                  "bE|52|witness|SKIP-TIERT|-"]
        _write(lane6, "\n".join(rows6) + "\n")
        proc = run(["--results-lane", lane6, "--json", os.path.join(tmp, "v6.json")])
        assert proc.returncode == 1, (proc.returncode, proc.stdout)
        rep6 = json.load(open(os.path.join(tmp, "v6.json"), encoding="utf-8"))
        reasons = {e["key"]: e["reason"] for e in rep6["exceptions"]}
        assert rep6["counts"]["GREEN"] == 0, "no partial item may count GREEN"
        assert "partial coverage" in reasons.get("bE|50", ""), reasons
        assert "legacy falsify face" in reasons.get("bE|51", ""), reasons
        assert "applies to the boundary face only" in reasons.get("bE|52", ""), reasons
        print("vector 6 exception shapes (partial coverage, legacy form"
              " refused from GREEN, tier status on a non-boundary probe): PASS")

        # vector 7: baseline convergence (converged / stable / degraded) and
        #   CLI refusals (no ledger match 9, malformed baseline 2, md face)
        baseline_old = os.path.join(tmp, "old.json")
        _write(baseline_old, json.dumps({
            "schema": SCHEMA, "failing_keys": ["bC|30", "bC|31", "bD|99"],
            "counts": {}}, ensure_ascii=False, indent=1))
        out7 = os.path.join(tmp, "v7.json")
        proc = run(["--results-lane", lane3, "--baseline", baseline_old,
                    "--json", out7])
        assert proc.returncode == 1, (proc.returncode, proc.stdout)
        rep7 = json.load(open(out7, encoding="utf-8"))
        assert rep7["baseline"]["verdict"] == "converged", rep7["baseline"]
        assert rep7["baseline"]["resolved"] == ["bD|99"], rep7["baseline"]
        assert rep7["baseline"]["persistent"] == ["bC|30", "bC|31"], rep7["baseline"]
        md7 = os.path.join(tmp, "v7.md")
        proc = run(["--results-lane", lane3, "--baseline", baseline_old,
                    "--md", md7])
        md_text = open(md7, encoding="utf-8").read()
        assert "baseline convergence (converged)" in md_text, md_text[:300]
        proc = run(["--results-lane", os.path.join(tmp, "no-match*.tsv")])
        assert proc.returncode == 9, proc.returncode
        bad_base = os.path.join(tmp, "old-bad.json")
        _write(bad_base, json.dumps({"schema": "rocqwash-other/1"}))
        proc = run(["--results-lane", lane1, "--baseline", bad_base])
        assert proc.returncode == 2 and "schema" in proc.stdout, proc.stdout
        print("vector 7 baseline convergence (converged/stable caliber on"
              " failing-key movement; malformed baseline rc2; no-match rc9;"
              " md face): PASS")

        print("VERDICT-DIFF-SELFTEST PASS: seven vectors all pass (GREEN"
              " table, ALERT gate, BLOCKED + exceptions, MISSING face,"
              " lane merge, exception shapes, baseline convergence)")
        return 0
    except AssertionError as exc:
        print("VERDICT-DIFF-SELFTEST FAIL: %s" % exc)
        return 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---- CLI ----------------------------------------------------------------------

def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="mechanical judge for vacuity probe sweep"
        " results: merges per-lane ledgers into the GREEN / ALERT / BLOCKED /"
        " MISSING / SKIPPED-TIERT table plus a named exception list, with an"
        " optional baseline convergence diff")
    ap.add_argument("--results-lane", required=True, metavar="GLOB",
                    help="glob of per-lane ledgers, e.g. DIR/results-lane*.tsv")
    ap.add_argument("--expected", default=None, metavar="F",
                    help="expected universe JSON ({\"items\": [\"batchId|idx\"...]})"
                         " for the MISSING face (alternative to --batches)")
    ap.add_argument("--batches", default=None, metavar="B.json",
                    help="sweep batches plan as the expected universe"
                         " (alternative to --expected)")
    ap.add_argument("--baseline", default=None, metavar="OLD.json",
                    help="prior judgment-table report for the convergence diff")
    ap.add_argument("--json", default=None, metavar="F",
                    help="write the report JSON (schema %s)" % SCHEMA)
    ap.add_argument("--md", default=None, metavar="F",
                    help="write the human-readable markdown table")
    args = ap.parse_args(argv)

    def write(path, text, tag):
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            print("%s -> %s" % (tag, path))
        except OSError as exc:
            print("FAIL-LOUD: report write failure: %s (%s)" % (path, exc),
                  file=sys.stderr)
            sys.exit(9)

    try:
        rows, conflicts, malformed, files = load_lane_results(args.results_lane)
        universe = expected_universe(args.expected, args.batches)
        verdict, exceptions = judge(rows, universe)
        baseline = None
        if args.baseline:
            if not os.path.isfile(args.baseline):
                raise MissingPath("baseline report missing: %s" % args.baseline)
            try:
                with open(args.baseline, "r", encoding="utf-8") as fh:
                    old = json.load(fh)
            except (ValueError, UnicodeDecodeError) as exc:
                raise FormError("baseline JSON parse failure: %s (%s)"
                                % (args.baseline, exc))
            baseline = baseline_diff(old, failing_keys_of(verdict))
    except MissingPath as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        sys.exit(9)
    except FormError as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        sys.exit(2)

    report = build_report(verdict, exceptions, conflicts, malformed, files,
                          universe, baseline)
    print_report(report)
    if args.json:
        write(args.json, json.dumps(report, ensure_ascii=False, indent=1,
                                    sort_keys=True) + "\n", "json")
    if args.md:
        write(args.md, report_md(report), "md")

    counts = report["counts"]
    if counts["ALERT"]:
        sys.exit(2)  # freeze gate: stop-work overrides every other face
    sys.exit(1 if report["failing_keys"] else 0)


if __name__ == "__main__":
    main()
