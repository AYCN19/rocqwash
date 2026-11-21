#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""numeric_probe.py - exact-arithmetic re-verification gate for claimed
numerical verifications (the CP1989-style stdlib exact gate face).

Purpose.  Reads a claim file (JSON array; rows carry id, kind, statement,
  the discriminating field left|interval|target, source_anchor) and
  mechanically re-verifies each claim with Fraction exact arithmetic:
  rational-bound executes A < B / A <= B / A = B; interval-containment
  executes x in [lo, hi]; transcendental-plan (zeta/theta/psi/ln) emits a
  bound-discipline verification plan and returns PLANNED (the honest
  plan-only face, never a fabricated numeric verdict).  Entries parse to
  closed rational intervals: "p/q" an exact point; a decimal with d
  written fraction digits carries value +/- 10^-d/2 (explicit precision
  k overrides d; a bare integer is exact).  Numbers that fail to parse
  land honest UNPARSED rows.  Verdicts PASS / FAIL / PLANNED / UNPARSED;
  one JSON report line, every top-level key but schema and scan_face
  wrapped {"value", "basis"}, scan_face stating coverage and blind spots
  (the tree_audit shape).
Interface.  python -I tools/numeric_probe.py --claim CLAIMS.json [--out
  OUT.json] | --selftest.  rc 0 iff no FAIL and no UNPARSED row; rc 1
  names every red row id on stderr (fail loud); rc 2 usage (missing
  --claim, flag conflicts, unreadable path).
Dependencies.  Python 3 stdlib only (argparse, fractions, json, os, re,
  shutil, sys, tempfile); zero floats, zero subprocess, zero network; zero
  writes beyond the caller-named --out.
Evidence.  --selftest runs the frozen 42-vector group in-process on synthetic
  claim files (parse, executed comparison, interval, plan, UNPARSED, shape
  and rc faces) and prints "[SELFTEST] numeric_probe green: 42 vector(s), 0 fail".
Exit-codes.  0 green; 1 red (selftest red, FAIL/UNPARSED rows, --out write failure); 2 usage.
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from fractions import Fraction

TOOL = "numeric_probe"
REPORT_SCHEMA = "rocqwash-numeric-probe/1"
V_PASS = "PASS"
V_FAIL = "FAIL"
V_PLAN = "PLANNED"
V_UNPARSED = "UNPARSED"
K_RB = "rational-bound"
K_IC = "interval-containment"
K_TP = "transcendental-plan"
# The frozen selftest vector (the CP1989 exact-gate precedent: the vector
# count itself is frozen; a 43rd vector turns the selftest red).
SELFTEST_VECTOR_COUNT = 42

# Accepted operator spellings, mapped onto the three executed comparison
# faces.  Anything outside this table is an UNPARSED row, never a guess.
OPS = {"<": "lt", "lt": "lt", "<=": "le", "le": "le",
       "=": "eq", "==": "eq", "eq": "eq"}

# Entry grammar (declared face): a fraction "p/q" (denominator nonzero) is
# an exact point; a decimal with an integer part and d written fraction
# digits is the written value carried as a band value +/- 10^-d/2; an
# integer with no fraction digits is an exact point (an explicit
# "precision": k entry-object field overrides d for either form).  The
# exponent form ("1e-3") is not in the grammar and parses as UNPARSED.
FRAC_RE = re.compile(r"\A([+-]?\d+)/(\d+)\Z")
DEC_RE = re.compile(r"\A([+-]?)(\d+)(?:\.(\d*))?\Z")

# Transcendental symbol tokens recognized in a transcendental-plan target.
# Each match adds the plan's bound-discipline step for that symbol family;
# the scan is a token scan over the verbatim target string, nothing more.
PLAN_SYMBOLS = [
    ("zeta", re.compile(r"zeta|\u03b6", re.I)),
    ("theta", re.compile(r"theta|\u03b8", re.I)),
    ("psi", re.compile(r"psi|\u03c8", re.I)),
    ("ln", re.compile(r"\bln\b|\blog\b", re.I)),
    ("exp", re.compile(r"\bexp\b", re.I)),
    ("trig", re.compile(r"\b(?:sin|cos|tan)\b", re.I)),
    ("pi", re.compile(r"\bpi\b|\u03c0", re.I)),
    ("euler_gamma", re.compile(r"\bgamma\b|euler.?gamma|\u03b3", re.I)),
]

# Per-symbol bound-discipline steps of the verification plan (the plan's
# mechanical content: what to compute, with which wall discipline).  These
# are plan steps, not computations: the probe executes no transcendental
# arithmetic of its own (stdlib scope), so nothing here is a verdict.
PLAN_STEPS = {
    "zeta": (
        "zeta(s): evaluate through the Dirichlet eta transform (terms "
        "1/n^s with alternating signs, the eta tail bounded by its "
        "next-term magnitude for Re(s) > 0) or an Euler-Maclaurin "
        "expansion with a stated remainder majorant; the tail bound must "
        "be a hand-derived rational inequality, never a numeric spot check"
    ),
    "theta": (
        "theta: evaluate the defining series under directed rounding at "
        "declared precision >= 50 digits; convert each partial result to "
        "rational walls lo/hi by rounding down/up; the Taylor/Lagrange "
        "remainder that justifies the wall gap is recorded as an explicit "
        "rational inequality"
    ),
    "psi": (
        "psi: evaluate through its defining series or functional equation "
        "under directed rounding at declared precision >= 50 digits; "
        "rational wall pairs lo/hi per value; the remainder bound feeding "
        "the walls is recorded as an explicit rational inequality"
    ),
    "ln": (
        "ln: evaluate via the decimal module at declared precision >= 50 "
        "digits with directed rounding (one wall pass rounding down, one "
        "rounding up); record the argument-reduction identity used and "
        "its rational-inequality remainder bound"
    ),
    "exp": (
        "exp: evaluate via the decimal module at declared precision >= 50 "
        "digits with directed rounding; the alternating-series remainder "
        "majorant that bounds the wall gap is recorded as an explicit "
        "rational inequality"
    ),
    "trig": (
        "trig: evaluate via argument reduction to [-pi/4, pi/4] and the "
        "Taylor series under directed rounding at declared precision "
        ">= 50 digits; pi itself enters as the exact-rational wall pair "
        "produced by the plan's pi step, never as a float literal"
    ),
    "pi": (
        "pi: produce exact rational walls via a Machin-family series "
        "(pi = 16*atan(1/5) - 4*atan(1/239)); the alternating arctan "
        "tail is bounded by its next term, giving walls whose gap is an "
        "explicit rational inequality; consume pi only as this wall pair"
    ),
    "euler_gamma": (
        "euler gamma: evaluate through the digamma limit psi(n+1) - ln(n) "
        "under directed rounding at declared precision >= 50 digits; the "
        "harmonic/ln tail majorant is recorded as an explicit rational "
        "inequality before the walls are accepted"
    ),
}

PLAN_GENERIC = (
    "no approved high-precision transcendental backend exists in stdlib "
    "scope: every numeric face of this target is planned, not judged; the "
    "plan is the deliverable until a backend ticket lands, and no numeric "
    "verdict is fabricated for it"
)

PLAN_NONE_NOTE = (
    "no transcendental symbol token was detected in the target string; "
    "state the symbol set explicitly before this plan can name steps"
)


def parse_entry(entry):
    """Parse one numeric entry into a closed rational interval.

    Returns (lo, hi, basis, None) on success or (None, None, None, reason)
    on a parse failure.  lo/hi are Fractions; basis states the parse face
    precisely enough to re-derive both walls by hand.
    """
    precision = None
    if isinstance(entry, dict):
        extra = set(entry) - {"value", "precision"}
        if extra:
            return None, None, None, (
                "entry object carries unexpected keys: %s" % sorted(extra))
        value = entry.get("value")
        precision = entry.get("precision")
        if precision is not None and (
                isinstance(precision, bool) or not isinstance(precision, int)
                or precision < 0):
            return None, None, None, (
                "declared precision must be a non-negative integer, got %r"
                % (precision,))
    elif isinstance(entry, str):
        value = entry
    else:
        return None, None, None, (
            "entry is neither a string nor a {value, precision} object: %r"
            % (entry,))

    if not isinstance(value, str):
        return None, None, None, "entry value must be a string, got %r" % (value,)
    text = value.strip()

    m = FRAC_RE.match(text)
    if m:
        num = int(m.group(1))
        den = int(m.group(2))
        if den == 0:
            return None, None, None, "fraction denominator is zero: '%s'" % text
        point = Fraction(num, den)  # normalized face of the same rational
        return point, point, (
            "exact rational point %s (entry '%s')" % (point, text)), None

    m = DEC_RE.match(text)
    if m:
        sign = -1 if m.group(1) == "-" else 1
        int_part = m.group(2)
        frac = m.group(3) or ""
        value_frac = Fraction(sign * int(int_part + frac), 10 ** len(frac))
        declared = len(frac) if precision is None else precision
        if declared > 0:
            half = Fraction(1, 2 * 10 ** declared)
            lo = value_frac - half
            hi = value_frac + half
            return lo, hi, (
                "decimal '%s', declared precision %d, band [%s, %s] "
                "(value %s +/- %s)" % (text, declared, lo, hi, value_frac,
                                       half)), None
        return value_frac, value_frac, (
            "exact integer point %s (entry '%s')" % (value_frac, text)), None

    return None, None, None, (
        "entry is neither a p/q fraction nor a plain decimal: '%s'" % text)


def execute_cmp(lo_a, hi_a, lo_b, hi_b, op_key):
    """Execute one exact comparison of the two entry bands; no floats."""
    if op_key == "lt":
        ok = hi_a < lo_b
        cmp_basis = "executed hi(A)=%s < lo(B)=%s -> %s" % (hi_a, lo_b,
                                                            str(ok).lower())
    elif op_key == "le":
        ok = hi_a <= lo_b
        cmp_basis = "executed hi(A)=%s <= lo(B)=%s -> %s" % (hi_a, lo_b,
                                                             str(ok).lower())
    else:  # eq: exact-point equality only; banded entries cannot certify it
        ok = (lo_a == hi_a == lo_b == hi_b)
        cmp_basis = ("executed exact-point equality A=[%s, %s] B=[%s, %s] "
                     "-> %s" % (lo_a, hi_a, lo_b, hi_b, str(ok).lower()))
    return (V_PASS if ok else V_FAIL), cmp_basis


def execute_contain(lo_x, hi_x, lo_iv, hi_iv):
    """Execute the exact containment of the x band inside [lo_iv, hi_iv]."""
    ok = (lo_iv <= lo_x) and (hi_x <= hi_iv)
    cmp_basis = "executed %s <= %s and %s <= %s -> %s" % (lo_iv, lo_x, hi_x,
                                                          hi_iv,
                                                          str(ok).lower())
    return (V_PASS if ok else V_FAIL), cmp_basis


def build_plan(target):
    """Build the transcendental-plan verification plan for a target string.

    Mechanical content: a token scan over the verbatim target names the
    symbol families, and each named family gets its bound-discipline step.
    The plan computes nothing: the walls it calls for would be produced by
    the recorded discipline and then fed to the rational-bound gate.
    """
    steps = []
    for name, rx in PLAN_SYMBOLS:
        if rx.search(target):
            steps.append({"symbol": name, "step": PLAN_STEPS[name]})
    plan = {
        "compute": [
            "cast every rational literal of the target to Fraction exactly",
            "for each symbol occurrence below, produce exact rational wall "
            "pairs lo/hi by the named bound discipline (directed rounding "
            "at declared precision >= 50 digits, the remainder majorant "
            "recorded as an explicit rational inequality)",
            "feed the resulting wall pairs to the rational-bound gate: the "
            "final comparison is executed by exact Fraction arithmetic "
            "(this tool's rational-bound face), never by floats",
        ],
        "bound_discipline": steps,
        "symbols_detected": [s["symbol"] for s in steps],
        "artifacts": [
            "one rational wall pair per computed side, recorded as exact "
            "p/q strings with the declared precision and the remainder "
            "bound that justifies each gap",
            "one executed comparison row per final inequality, with the "
            "exact comparison recorded in the row basis",
        ],
        "out_of_scope": PLAN_GENERIC,
    }
    if not steps:
        plan["bound_discipline"].append({"symbol": "(none)",
                                         "step": PLAN_NONE_NOTE})
    return plan


def _unparsed(rid, kind, statement, anchor, reason):
    """One honest UNPARSED row: the parse reason rides in the basis."""
    return {
        "id": rid,
        "kind": kind,
        "statement": statement,
        "verdict": V_UNPARSED,
        "basis": reason,
        "source_anchor": anchor,
    }


def probe_row(index, item):
    """Probe one claim object; returns one report row."""
    if not isinstance(item, dict):
        return _unparsed("(row %d)" % (index + 1), None, None, None,
                         "claim row is not a JSON object: %r" % (item,))
    rid = item["id"] if isinstance(item.get("id"), str) \
        else "(row %d)" % (index + 1)
    kind = item.get("kind") if isinstance(item.get("kind"), str) else None
    statement = item.get("statement") \
        if isinstance(item.get("statement"), str) else None
    anchor = item.get("source_anchor") \
        if isinstance(item.get("source_anchor"), str) else None

    if kind == K_RB:
        for field in ("left", "right", "op"):
            if field not in item:
                return _unparsed(rid, kind, statement, anchor,
                                 "missing field '%s'" % field)
        op_raw = item["op"]
        if not isinstance(op_raw, str) or op_raw not in OPS:
            return _unparsed(rid, kind, statement, anchor,
                             "operator not in the declared table "
                             "(<, <=, =, lt, le, eq, ==): %r" % (op_raw,))
        lo_a, hi_a, basis_a, err = parse_entry(item["left"])
        if err:
            return _unparsed(rid, kind, statement, anchor, "left: %s" % err)
        lo_b, hi_b, basis_b, err = parse_entry(item["right"])
        if err:
            return _unparsed(rid, kind, statement, anchor, "right: %s" % err)
        verdict, cmp_basis = execute_cmp(lo_a, hi_a, lo_b, hi_b, OPS[op_raw])
        return {
            "id": rid, "kind": kind, "statement": statement,
            "verdict": verdict,
            "basis": "%s; A: %s; B: %s" % (cmp_basis, basis_a, basis_b),
            "source_anchor": anchor,
        }

    if kind == K_IC:
        if "interval" not in item:
            return _unparsed(rid, kind, statement, anchor,
                             "missing field 'interval'")
        iv = item["interval"]
        if not isinstance(iv, dict) or set(iv) != {"x", "lo", "hi"}:
            return _unparsed(rid, kind, statement, anchor,
                             "interval must be an object with exactly the "
                             "keys x, lo, hi: %r" % (iv,))
        lo_x, hi_x, x_basis, err = parse_entry(iv["x"])
        if err:
            return _unparsed(rid, kind, statement, anchor, "x: %s" % err)
        lo_iv, _, lo_basis, err = parse_entry(iv["lo"])
        if err:
            return _unparsed(rid, kind, statement, anchor, "lo: %s" % err)
        _, hi_iv, hi_basis, err = parse_entry(iv["hi"])
        if err:
            return _unparsed(rid, kind, statement, anchor, "hi: %s" % err)
        if lo_iv > hi_iv:
            return _unparsed(rid, kind, statement, anchor,
                             "inverted interval: lo=%s > hi=%s"
                             % (lo_iv, hi_iv))
        verdict, cmp_basis = execute_contain(lo_x, hi_x, lo_iv, hi_iv)
        return {
            "id": rid, "kind": kind, "statement": statement,
            "verdict": verdict,
            "basis": "%s; x: %s; lo: %s; hi: %s"
                     % (cmp_basis, x_basis, lo_basis, hi_basis),
            "source_anchor": anchor,
        }

    if kind == K_TP:
        target = item.get("target")
        if not isinstance(target, str) or not target.strip():
            return _unparsed(rid, kind, statement, anchor,
                             "target must be a non-empty string: %r"
                             % (target,))
        return {
            "id": rid, "kind": kind, "statement": statement,
            "verdict": V_PLAN,
            "basis": ("plan-only: no approved high-precision transcendental "
                      "backend in stdlib scope; the plan is the deliverable, "
                      "no numeric verdict fabricated"),
            "plan": build_plan(target),
            "source_anchor": anchor,
        }

    return _unparsed(rid, kind, statement, anchor,
                     "unknown kind %r (expected %s | %s | %s)"
                     % (kind, K_RB, K_IC, K_TP))


def probe_body(claims):
    """Probe a parsed claim-file body (any JSON value) into report rows."""
    if not isinstance(claims, list):
        return [_unparsed("(file)", None, None, None,
                          "claim file top level is not a JSON array: %s"
                          % type(claims).__name__)]
    return [probe_row(i, item) for i, item in enumerate(claims)]


SCAN_FACE = {
    "scanned": (
        "the caller-named --claim JSON file: every claim object listed in "
        "file order; entries parsed to exact Fractions (p/q points or "
        "declared-precision decimal bands); rational-bound and "
        "interval-containment verdicts executed by exact rational "
        "comparison (zero floats); transcendental-plan targets token-"
        "scanned into a bound-discipline verification plan"),
    "not_scanned": (
        "numeric truth beyond the parsed entries: no approved "
        "high-precision transcendental backend exists in stdlib scope, so "
        "kind transcendental-plan is planned (PLANNED) and never judged; "
        "claim provenance and the adequacy of each declared precision are "
        "not audited; a FAIL says the recorded comparison is false as "
        "executed, not that the underlying mathematics is false"),
    "negative_finding": (
        "a FAIL or UNPARSED row is a finding: each red row id is named on "
        "stderr and the exit code is 1; UNPARSED means the claim's numbers "
        "did not parse (an honest row), never a silent skip; PLANNED rows "
        "carry plans and no numeric verdict by design"),
    "equivalents": (
        "a re-run over the same claim file is field-for-field equal "
        "(deterministic exact arithmetic); a same-claims cross-check by "
        "any independent exact-rational comparator must agree row for row; "
        "the --selftest 42-vector group is the offline behavioral witness"),
}


def run_probe(claim_path):
    """Probe one claim file; returns (report, rc, red_ids).

    rc is 0 iff no FAIL and no UNPARSED row; 1 otherwise, with red_ids
    listing every red row id for the stderr red list; 2 for an unreadable
    claim path (a usage error).
    """
    try:
        with open(claim_path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        return None, 2, ["claim file unreadable: %s" % exc]
    try:
        claims = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        claims = "unparseable: %s" % exc
    rows = probe_body(claims)
    counts = {
        "total": len(rows),
        "pass": sum(1 for r in rows if r["verdict"] == V_PASS),
        "fail": sum(1 for r in rows if r["verdict"] == V_FAIL),
        "planned": sum(1 for r in rows if r["verdict"] == V_PLAN),
        "unparsed": sum(1 for r in rows if r["verdict"] == V_UNPARSED),
    }
    red_ids = [r["id"] for r in rows if r["verdict"] in (V_FAIL, V_UNPARSED)]
    report = {
        "schema": REPORT_SCHEMA,
        "claim_file": {
            "value": claim_path,
            "basis": "the --claim path as given on the command line",
        },
        "claims": {
            "value": rows,
            "basis": "one row per claim object in file order; id, kind, "
                     "statement and source_anchor carried verbatim; the "
                     "row basis records the exact executed comparison",
        },
        "counts": {
            "value": counts,
            "basis": "counting rule: total = claim rows in file order; "
                     "pass/fail/planned/unparsed counted by verdict; "
                     "fail + unparsed > 0 makes rc 1 (fail loud)",
        },
        "scan_face": dict(SCAN_FACE),
    }
    rc = 0 if (counts["fail"] == 0 and counts["unparsed"] == 0) else 1
    return report, rc, red_ids


def _emit_json(payload):
    """One UTF-8 JSON line on stdout, console-encoder independent."""
    sys.stdout.buffer.write(
        (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


# --------------------------------------------------------------- selftest

def _selftest():
    """Run the frozen 42-vector group in-process; return 0 green or 1 red.

    Zero network, zero subprocess, zero repository writes: the vectors run
    against synthetic claim files in a system temporary directory and
    against the parse/plan/execute functions directly.  The vector count
    is itself a frozen vector: a count other than 42 is a red.
    """
    failures = []
    passed = []

    def check(name, cond, detail=""):
        if cond:
            passed.append(name)
            print("[PASS] %s" % name)
        else:
            failures.append("%s: %s" % (name, detail or "vector red"))

    tmp = tempfile.mkdtemp(prefix="numeric_probe_selftest_")
    try:
        def write_claims(name, doc):
            path = os.path.join(tmp, name)
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                if isinstance(doc, str):
                    handle.write(doc)
                else:
                    json.dump(doc, handle)
            return path

        # ---- group P: entry parse faces (9 vectors) --------------------
        lo, hi, basis, err = parse_entry("3/4")
        check("P1 fraction-point",
              err is None and lo == Fraction(3, 4) and hi == Fraction(3, 4)
              and basis == "exact rational point 3/4 (entry '3/4')")
        lo, hi, _, err = parse_entry("-2/5")
        check("P2 fraction-negative",
              err is None and lo == Fraction(-2, 5) and hi == lo)
        _, _, _, err = parse_entry("3/0")
        check("P3 fraction-zero-denominator",
              err is not None and "denominator is zero" in err)
        lo, hi, _, err = parse_entry("3.14")
        check("P4 decimal-band",
              err is None and lo == Fraction(627, 200)
              and hi == Fraction(629, 200))
        lo, hi, _, err = parse_entry("42")
        check("P5 bare-integer-point",
              err is None and lo == Fraction(42) and hi == lo)
        lo, hi, _, err = parse_entry({"value": "3.14", "precision": 4})
        check("P6 declared-precision-band",
              err is None and lo == Fraction(62799, 20000)
              and hi == Fraction(62801, 20000))
        _, _, _, err = parse_entry("1e-3")
        check("P7 exponent-form-rejected", err is not None)
        _, _, _, err = parse_entry("abc")
        check("P8 garbage-rejected", err is not None)
        _, _, _, err = parse_entry(42)
        check("P9 non-string-entry-rejected", err is not None)

        # ---- group R: executed rational-bound faces (8 vectors) --------
        path = write_claims("rb1.json", [
            {"id": "rb1", "kind": K_RB, "statement": "1/3 < 1/2",
             "left": "1/3", "op": "<", "right": "1/2", "source_anchor": "s1"}])
        report, rc, red = run_probe(path)
        row = report["claims"]["value"][0]
        check("R1 lt-pass", rc == 0 and red == []
              and row["verdict"] == V_PASS)
        check("R2 comparison-recorded",
              row["basis"] == "executed hi(A)=1/3 < lo(B)=1/2 -> true; "
              "A: exact rational point 1/3 (entry '1/3'); "
              "B: exact rational point 1/2 (entry '1/2')")
        path = write_claims("rb2.json", [
            {"id": "rb2", "kind": K_RB, "left": "0.7", "op": "<",
             "right": "2/3"}])
        report, rc, red = run_probe(path)
        row = report["claims"]["value"][0]
        check("R3 lt-fail-decimal-band",
              rc == 1 and red == ["rb2"] and row["verdict"] == V_FAIL
              and "executed hi(A)=3/4 < lo(B)=2/3 -> false" in row["basis"])
        path = write_claims("rb3.json", [
            {"id": "rb3", "kind": K_RB, "left": "3.14", "op": "<",
             "right": "22/7"}])
        report, rc, red = run_probe(path)
        row = report["claims"]["value"][0]
        check("R4 lt-band-touch-fail",
              row["verdict"] == V_FAIL
              and "executed hi(A)=629/200 < lo(B)=22/7 -> false"
              in row["basis"])
        path = write_claims("rb45.json", [
            {"id": "rb4", "kind": K_RB, "left": "6/8", "op": "<=",
             "right": "3/4"},
            {"id": "rb5", "kind": K_RB, "left": "1/2", "op": "le",
             "right": "1/3"}])
        report, rc, red = run_probe(path)
        rows = report["claims"]["value"]
        check("R5 le-pass-and-fail",
              rows[0]["verdict"] == V_PASS and rows[1]["verdict"] == V_FAIL
              and red == ["rb5"])
        path = write_claims("rb67.json", [
            {"id": "rb6", "kind": K_RB, "left": "3/4", "op": "=",
             "right": "6/8"},
            {"id": "rb7", "kind": K_RB, "left": "3.14", "op": "=",
             "right": "3.14"}])
        report, rc, red = run_probe(path)
        rows = report["claims"]["value"]
        check("R6 eq-pass-points",
              rows[0]["verdict"] == V_PASS
              and "executed exact-point equality A=[3/4, 3/4] "
                  "B=[3/4, 3/4] -> true" in rows[0]["basis"])
        check("R7 eq-fail-bands",
              rows[1]["verdict"] == V_FAIL
              and "executed exact-point equality A=[627/200, 629/200] "
                  "B=[627/200, 629/200] -> false" in rows[1]["basis"])
        path = write_claims("rb8.json", [
            {"id": "rb8", "kind": K_RB, "left": "1", "op": ">",
             "right": "0"}])
        report, rc, red = run_probe(path)
        row = report["claims"]["value"][0]
        check("R8 unknown-op-unparsed",
              row["verdict"] == V_UNPARSED
              and "operator not in the declared table" in row["basis"])

        # ---- group I: interval-containment faces (6 vectors) ------------
        path = write_claims("iv.json", [
            {"id": "iv1", "kind": K_IC, "interval": {"x": "1/2",
                                                     "lo": "0", "hi": "1"}},
            {"id": "iv2", "kind": K_IC,
             "interval": {"x": {"value": "0.5", "precision": 2},
                          "lo": "0.49", "hi": "0.51"}},
            {"id": "iv3", "kind": K_IC,
             "interval": {"x": {"value": "0.5", "precision": 2},
                          "lo": "1/2", "hi": "1"}},
            {"id": "iv4", "kind": K_IC, "interval": {"x": "1", "lo": "0",
                                                     "hi": "1"}},
            {"id": "iv5", "kind": K_IC, "interval": {"x": "-1/2", "lo": "0",
                                                     "hi": "1"}}])
        report, rc, red = run_probe(path)
        rows = report["claims"]["value"]
        check("I1 point-inside-pass",
              rows[0]["verdict"] == V_PASS
              and "executed 0 <= 1/2 and 1/2 <= 1 -> true" in rows[0]["basis"]
              and rc == 1 and red == ["iv3", "iv5"])
        check("I2 banded-x-inside-pass",
              rows[1]["verdict"] == V_PASS
              and "executed 97/200 <= 99/200 and 101/200 <= 103/200 -> true"
              in rows[1]["basis"])
        check("I3 banded-x-pokes-below-fail",
              rows[2]["verdict"] == V_FAIL
              and "executed 1/2 <= 99/200" in rows[2]["basis"])
        check("I4 closed-endpoint-touch-pass",
              rows[3]["verdict"] == V_PASS
              and "executed 0 <= 1 and 1 <= 1 -> true" in rows[3]["basis"])
        check("I5 below-fail", rows[4]["verdict"] == V_FAIL)
        path = write_claims("iv6.json", [
            {"id": "iv6", "kind": K_IC, "interval": {"x": "1/2", "lo": "1",
                                                     "hi": "0"}}])
        report, rc, red = run_probe(path)
        row = report["claims"]["value"][0]
        check("I6 inverted-interval-unparsed",
              row["verdict"] == V_UNPARSED
              and "inverted interval: lo=1 > hi=0" in row["basis"])

        # ---- group T: transcendental-plan faces (5 vectors) -------------
        path = write_claims("tp1.json", [
            {"id": "tp1", "kind": K_TP, "statement": "ln(65)/4 - 27/26 > 0",
             "target": "ln(65)/4 vs 27/26, with zeta(s) and psi(182) walls",
             "source_anchor": "prop3.1"}])
        report, rc, red = run_probe(path)
        row = report["claims"]["value"][0]
        check("T1 planned-verdict",
              row["verdict"] == V_PLAN and rc == 0 and red == [])
        check("T2 plan-shape",
              set(row["plan"]) == {"compute", "bound_discipline",
                                   "symbols_detected", "artifacts",
                                   "out_of_scope"})
        check("T3 symbol-detection-zeta-psi-ln",
              row["plan"]["symbols_detected"] == ["zeta", "psi", "ln"]
              and all(s["step"] for s in row["plan"]["bound_discipline"]))
        path = write_claims("tp2.json", [
            {"id": "tp2", "kind": K_TP,
             "target": "theta(17) < pi - 3.14 and gamma < 1/2"}])
        report, rc, red = run_probe(path)
        row = report["claims"]["value"][0]
        check("T4 symbol-detection-theta-pi-gamma",
              row["plan"]["symbols_detected"] == ["theta", "pi", "euler_gamma"])
        check("T5 no-numeric-verdict",
              row["verdict"] not in (V_PASS, V_FAIL)
              and "no numeric verdict fabricated" in row["basis"])

        # ---- group U: UNPARSED honest-row faces (6 vectors) -------------
        path = write_claims("un.json", [
            {"id": "u1", "kind": K_RB, "left": "1/2", "op": "<"},
            {"id": "u2", "kind": K_RB, "left": "1/2", "right": "1/3"},
            {"id": "u3", "kind": K_IC, "interval": {"lo": "0", "hi": "1"}},
            {"id": "u4", "kind": "float-compare", "left": "1/2", "op": "<",
             "right": "1/3"},
            {"id": "u5", "kind": K_RB, "left": "2/-", "op": "<",
             "right": "1"},
            "not an object"])
        report, rc, red = run_probe(path)
        rows = report["claims"]["value"]
        check("U1 missing-right-unparsed",
              rows[0]["verdict"] == V_UNPARSED
              and "missing field 'right'" in rows[0]["basis"])
        check("U2 missing-op-unparsed",
              rows[1]["verdict"] == V_UNPARSED
              and "missing field 'op'" in rows[1]["basis"])
        check("U3 interval-missing-key-unparsed",
              rows[2]["verdict"] == V_UNPARSED
              and "exactly the keys x, lo, hi" in rows[2]["basis"])
        check("U4 unknown-kind-unparsed",
              rows[3]["verdict"] == V_UNPARSED
              and "unknown kind 'float-compare'" in rows[3]["basis"])
        check("U5 bad-entry-unparsed",
              rows[4]["verdict"] == V_UNPARSED
              and "left: entry is neither" in rows[4]["basis"])
        check("U6 non-object-row-unparsed",
              rows[5]["verdict"] == V_UNPARSED
              and rows[5]["id"] == "(row 6)"
              and "not a JSON object" in rows[5]["basis"])

        # ---- group S: report shape faces (5 vectors) --------------------
        path = write_claims("shape.json", [
            {"id": "g1", "kind": K_RB, "left": "1/3", "op": "<=",
             "right": "1/2"},
            {"id": "g2", "kind": K_TP, "target": "zeta(-1) wall"}])
        report, rc, red = run_probe(path)
        check("S1 counts-wrap",
              set(report["counts"]) == {"value", "basis"}
              and set(report["counts"]["value"])
              == {"total", "pass", "fail", "planned", "unparsed"}
              and report["counts"]["value"] == {"total": 2, "pass": 1,
                                                "fail": 0, "planned": 1,
                                                "unparsed": 0})
        check("S2 claim-file-and-claims-wrap",
              set(report["claim_file"]) == {"value", "basis"}
              and set(report["claims"]) == {"value", "basis"}
              and all(set(r) >= {"id", "kind", "verdict", "basis"}
                      for r in report["claims"]["value"]))
        check("S3 scan-face-four-fields",
              set(report["scan_face"]) == {"scanned", "not_scanned",
                                           "negative_finding", "equivalents"})
        check("S4 verdict-domain",
              all(r["verdict"] in (V_PASS, V_FAIL, V_PLAN, V_UNPARSED)
                  for r in report["claims"]["value"]))
        path = write_claims("notarray.json", {"id": "x", "kind": "n/a"})
        report, rc, red = run_probe(path)
        check("S5 non-array-file-one-unparsed-row",
              rc == 1 and report["counts"]["value"]["total"] == 1
              and report["claims"]["value"][0]["id"] == "(file)"
              and "not a JSON array" in report["claims"]["value"][0]["basis"])

        # ---- group E: rc faces (3 vectors) ------------------------------
        path = write_claims("green.json", [
            {"id": "e1", "kind": K_RB, "left": "1/3", "op": "<",
             "right": "1/2"},
            {"id": "e2", "kind": K_TP, "target": "psi(182) wall"}])
        report, rc, red = run_probe(path)
        check("E1 rc-green", rc == 0 and red == [])
        path = write_claims("mixed.json", [
            {"id": "e3", "kind": K_RB, "left": "1/2", "op": "<",
             "right": "1/3"},
            {"id": "e4", "kind": K_RB, "left": "3/0", "op": "<",
             "right": "1"}])
        report, rc, red = run_probe(path)
        check("E2 rc-red-lists-ids", rc == 1 and red == ["e3", "e4"])
        check("E3 usage-faces",
              main(["--claim", os.path.join(tmp, "missing.json")]) == 2
              and main(["--selftest", "--claim", path]) == 2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # Frozen vector-count envelope: the group above must hold exactly 42.
    if len(passed) + len(failures) != SELFTEST_VECTOR_COUNT:
        failures.append("vector-count-freeze: %d vectors ran, the frozen "
                        "vector is %d"
                        % (len(passed) + len(failures),
                           SELFTEST_VECTOR_COUNT))
    if failures:
        for line in failures:
            sys.stderr.write("NUMERIC-PROBE-SELFTEST FAIL %s\n" % line)
        return 1
    print("[SELFTEST] %s green: %d vector(s), 0 fail"
          % (TOOL, SELFTEST_VECTOR_COUNT))
    return 0


def main(argv=None):
    """Flag gate, then the selected face: --selftest, or the --claim probe."""
    parser = argparse.ArgumentParser(
        prog="numeric_probe.py",
        description="exact-arithmetic re-verification gate for claimed "
                    "numerical verifications (Fraction only, zero floats, "
                    "zero subprocess, zero network).")
    parser.add_argument("--claim", default=None,
                        help="claim file: a JSON array of claim objects "
                             "(id, kind, statement, left|interval|target, "
                             "source_anchor)")
    parser.add_argument("--out", default=None,
                        help="additionally write the JSON report to this "
                             "caller-named path")
    parser.add_argument("--selftest", action="store_true",
                        help="run the frozen 42-vector group in-process and "
                             "exit; takes no other flag")
    args = parser.parse_args(argv)

    if args.selftest:
        if args.claim or args.out:
            sys.stderr.write(
                "%s: usage error: --selftest takes no other flag\n" % TOOL)
            return 2
        return _selftest()

    if not args.claim:
        parser.print_usage(sys.stderr)
        sys.stderr.write(
            "%s: usage error: --claim CLAIMS.json is required "
            "(or --selftest)\n" % TOOL)
        return 2

    report, rc, red_ids = run_probe(args.claim)
    if rc == 2:
        sys.stderr.write("%s: %s\n" % (TOOL, red_ids[0]))
        return 2
    _emit_json(report)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(report, handle, ensure_ascii=False, indent=1)
                handle.write("\n")
        except OSError as exc:
            sys.stderr.write("%s: --out write failed: %s\n" % (TOOL, exc))
            return 1
    if rc == 1:
        for rid in red_ids:
            sys.stderr.write("%s: red row: %s\n" % (TOOL, rid))
    return rc


if __name__ == "__main__":
    sys.exit(main())
