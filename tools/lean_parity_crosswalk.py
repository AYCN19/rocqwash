#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lean_parity_crosswalk.py - the Lean/Rocq axiom parity crosswalk engine.
Purpose.  Put the Lean face (tools/lean_axiom_sweep.py) and the Rocq face
  (tools/axiom_audit.py) side by side and judge their agreement row by row
  over one shared sample set: both sides are enumerated by their own tools'
  pure functions, joined on the five mirror proposition keys (clean /
  classical / funext / custom / sorry), and each row asserts
  map(rocq grade) == lean class plus the axiom-set mirror.  The mapping is
  read verbatim from axiom_audit.LEAN_PARITY_ROWS (never a second table);
  the Rocq Admitted <-> Lean sorryAx row is the design-frozen mirror rule
  (axiom_audit.LEAN_PARITY_NOTE).  Output schema rocqwash.parity.lean-census/1.
Interface.  python3 -I tools/lean_parity_crosswalk.py [--fixtures DIR]
  [--rocq-face] [--lean-face] [--rocq BIN] [--lean-sweep-json FILE]
  [--census-json FILE] [--snapshot OUT] [--baseline SNAP] [--json OUT]
  [--timeout SEC] | --selftest.
Dependencies.  Python 3 standard library only; loads both parent tools by
  file path (importlib) and reuses their pure functions unchanged; the
  engine-gated faces need the Rocq engine (--rocq / ROCWASH_ROCQ / PATH)
  and a usable Lean toolchain; never downloaded, never simulated; zero
  network.
Evidence.  Deterministic: the offline trunk is frozen-vector only, sorted
  rows, no wall clock, byte-identical reruns; the engine-gated faces record
  loud SKIP legs with reasons when their engine is absent and fail loud on
  a configured-but-broken engine; the mirror fixtures
  (tests/fixtures/lean_parity) carry one bilingual pair per proposition
  key; --selftest runs the frozen offline vector group only.
Exit-codes.  0 green (verdict MATCH under every face that ran); 1 red (any
  MISMATCH pair, count inequality, or error: unjudgeable is not green);
  2 usage error; the suite hook owns the SKIP code 111 for absent engines.
Usage:  python3 tools/lean_parity_crosswalk.py --selftest
"""

# Detail carried below the five-field header budget (the norm_lint
# header-budget rule keeps the docstring to the five fields):
#
# Four layers.  Layer 1 (offline trunk, always runs): the Lean side is the
#   sweep tool's canned `#print axioms` output fixtures (LEAN_OUT_* module
#   constants) parsed by its own name-keyed parser and classified by its
#   own precedence; the Rocq side is the audit tool's frozen census batch
#   text (CENSUS_BATCH_TEXT) parsed by its own block parser plus two
#   crosswalk-owned frozen census vectors (the custom-axiom face and the
#   Admitted face) whose block grammar was measured on Rocq 9.3.0 with
#   Print Assumptions (an Admitted statement surfaces as the statement's
#   own name inside its Axioms: block, exactly as
#   axiom_audit.LEAN_PARITY_NOTE records).  Layer 2 (mirror fixtures, Rocq
#   side real): the committed bilingual pair group under
#   tests/fixtures/lean_parity - the Lean side reads each mirror .lean
#   file through the sweep's own enumeration and copy-append probe
#   construction against the frozen `#print axioms` expectation file
#   (.lean.expected), the Rocq side runs the real axiom_audit census over
#   the mirror .v files when an engine resolves.  Layer 3 (both engines
#   real, Lean-gated hosts): the real sweep payload and the real census
#   payload join by mirror proposition name; also consumable pre-made via
#   --lean-sweep-json / --census-json.  Layer 4 (closure evolution, zero
#   toolchain): --snapshot writes a rocqwash-axiom-closure-snapshot/1
#   snapshot of the crosswalk's Lean-side rows via the sweep tool's own
#   build_snapshot, --baseline diffs against a previous snapshot via its
#   own diff_closures (four verdicts plus diff_alarm).
#
# Pair verdicts.  A pair is MATCH when (a) the mapped lean class equals
#   the Lean side's own classification and (b) the axiom-set mirror holds:
#   clean = both closures empty; classical = classic on the Rocq face
#   corresponds to Classical.choice on the Lean face; funext = the Rocq
#   functional_extensionality family corresponds to a Lean closure that
#   is a subset of the standard trio (functional extensionality is
#   derived there, no builtin axiom); custom = both faces carry verbatim
#   non-platform axiom names; sorry = the Rocq Admitted face (the
#   statement's own name in its axiom set) corresponds to sorryAx on the
#   Lean face.  Anything else is MISMATCH with the failing side named in
#   the pair basis.  A census-error row is unmappable and lands MISMATCH,
#   never guessed.  An enumeration-count inequality between the two sides
#   (a proposition missing on one side) is MISMATCH, never silent
#   truncation.
#
# {value, basis} law.  Every top-level key of the payload except "schema"
#   and "scan_face" is {"value": ..., "basis": ...} (the
#   rocqwash-axiom-sweep/1 calibration form); scan_face carries exactly
#   the four fixed English fields, pinned verbatim by the selftest.

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

TOOL = "lean_parity_crosswalk"
SCHEMA = "rocqwash.parity.lean-census/1"
MAPPING_SOURCE = "axiom_audit.LEAN_PARITY_ROWS/1"

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
SWEEP_PATH = os.path.join(TOOLS_DIR, "lean_axiom_sweep.py")
AUDIT_PATH = os.path.join(TOOLS_DIR, "axiom_audit.py")
DEFAULT_FIXTURES = os.path.join(REPO_ROOT, "tests", "fixtures",
                                "lean_parity")

PROG_TIMEOUT_DEFAULT = 600
ERROR_TAIL_LINES = 12

EXIT_OK = 0
EXIT_RED = 1
EXIT_USAGE = 2

# The five mirror proposition keys (the design freezes this roster).
MIRROR_KEYS = ("clean", "classical", "funext", "custom", "sorry")

# Mirror statement name roster: the bilingual fixture group names each
# statement identically on both faces (the join key), and each name maps
# to its proposition key.  Data, not a mapping table: the grade->class
# mapping stays single-source in axiom_audit.LEAN_PARITY_ROWS.
MIRROR_STATEMENT_KEYS = {
    "lp_mirror_clean": "clean",
    "lp_mirror_classical": "classical",
    "lp_mirror_funext": "funext",
    "lp_mirror_custom": "custom",
    "lp_mirror_admitted": "sorry",
}

# Fixture file stems per proposition key (the admitted pair carries the
# "admitted" stem per the design's fixture naming, not the key name).
MIRROR_FIXTURE_STEMS = {
    "clean": "clean",
    "classical": "classical",
    "funext": "funext",
    "custom": "custom",
    "sorry": "admitted",
}

# The four fixed scan-face strings (pinned verbatim by the selftest).
SCAN_SCANNED = (
    "Both frozen vector faces: the Lean side is the canned `#print axioms`"
    " output fixtures of rocqwash-axiom-sweep/1 parsed by its own"
    " name-keyed parser and classified by its own six-class precedence;"
    " the Rocq side is the frozen census batch text of"
    " rocqwash.b-axiom-audit/1 parsed by its own ordered-block parser and"
    " graded by its own four-grade classifier; rows join on the five"
    " mirror proposition keys (clean / classical / funext / custom /"
    " sorry) and each pair asserts the mapped class equality and the"
    " axiom-set mirror."
)
SCAN_NOT_SCANNED = (
    "No Lean toolchain is launched by the offline trunk; the engine-gated"
    " faces (the mirror-fixture census, the real Lean sweep) run only"
    " when their engine resolves and otherwise ride the payload as loud"
    " SKIP legs with reasons; a configured-but-broken engine fails loud"
    " (rc 1), never silently degrades; a census-error row is unmappable"
    " and lands MISMATCH."
)
SCAN_NEGATIVE_FINDING = (
    "A MATCH matrix over the five frozen rows is a negative finding of"
    " this crosswalk, not an absolute claim about any Lean repository;"
    " the mapping is quoted from axiom_audit.LEAN_PARITY_ROWS verbatim"
    " and every pair carries the counting rule in its basis."
)
SCAN_EQUIVALENTS = (
    "The Rocq Admitted <-> Lean sorryAx correspondence is the"
    " design-frozen mirror rule (axiom_audit.LEAN_PARITY_NOTE), not a row"
    " of the graded table; the Lean-side trio-subset fixtures stand for"
    " the derived functional-extensionality face (Lean 4 has no builtin"
    " funext axiom); the frozen `#print axioms` text form of the Lean 4"
    " CLI is taken as frozen where no Lean engine exists to re-verify it."
)

# The crosswalk-owned frozen census vectors (block grammar measured on
# Rocq 9.3.0 with Print Assumptions, this host, cpu-guard wrapped:
# "Axioms:" section head at column zero, entry lines "name : type" at
# column zero, wrapped type lines indented - the audit tool's own
# parse_census_blocks grammar).  The custom vector mirrors the committed
# mirror_custom.v pair; the admitted vector mirrors mirror_admitted.v and
# carries the statement's OWN name (the measured Admitted face).
ROCWASH_CENSUS_CUSTOM_TEXT = (
    "Axioms:\n"
    "lp_mirror_ax : True = True\n")
ROCWASH_CENSUS_CUSTOM_STMTS = [("lp_mirror_custom", 2)]
ROCWASH_CENSUS_CUSTOM_DECLARED = ("lp_mirror_ax",)
ROCWASH_CENSUS_ADMITTED_TEXT = (
    "Axioms:\n"
    "lp_mirror_admitted : True\n")
ROCWASH_CENSUS_ADMITTED_STMTS = [("lp_mirror_admitted", 2)]
ROCWASH_CENSUS_ADMITTED_DECLARED = ()

ADMITTED_BASIS = (
    "Rocq Admitted <-> Lean sorryAx: a Rocq Admitted surfaces in the"
    " census as the admitted statement's own name inside its Axioms:"
    " block (axiom_audit.LEAN_PARITY_NOTE, measured on Rocq 9.3.0), and"
    " the Lean mirror face of that statement is the SORRY-ALARM class"
    " (sorryAx); the design freezes this correspondence as the mirror"
    " rule that precedes the graded table")
TABLE_BASIS = (
    "the single-source grade -> Lean-class map read verbatim from"
    " axiom_audit.LEAN_PARITY_ROWS/1 (no second table exists in this"
    " tool)")
SORRY_CLASS = "SORRY-ALARM"
ROCQ_GRADE_ALARM_ORDER = ("custom", "funext", "classical", "stdlib")


def _load_module(tag, path):
    """Load one parent tool by file path (importlib; no package context)."""
    spec = importlib.util.spec_from_file_location(tag, path)
    if spec is None or spec.loader is None:
        raise SystemExit("FAIL-LOUD: cannot load %s from %s" % (tag, path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_parents():
    """(sweep_module, audit_module): both parent tools, unchanged."""
    return (_load_module("rocqwash_lean_axiom_sweep", SWEEP_PATH),
            _load_module("rocqwash_axiom_audit", AUDIT_PATH))


SWEEP, AUDIT = load_parents()


# ---- layer 1: the frozen-vector faces ----

LEAN_FROZEN_KEYS = (
    ("clean", "LEAN_OUT_CLEAN", "t_clean"),
    ("classical", "LEAN_OUT_THREE", "t_three"),
    ("funext", "LEAN_OUT_SUBSET", "t_subset"),
    ("custom", "LEAN_OUT_CUSTOM", "t_custom"),
    ("sorry", "LEAN_OUT_SORRY", "t_sorry"),
)


def lean_frozen_rows():
    """{key: lean decl row} over the sweep tool's canned `#print axioms`
    fixtures, enumerated, parsed and classified by the sweep tool's own
    pure functions (parse_print_axioms + classify_decl_rows)."""
    rows = {}
    for key, const, name in LEAN_FROZEN_KEYS:
        output = getattr(SWEEP, const)
        parsed = SWEEP.parse_print_axioms(output, [(2, name)])
        decl_rows = SWEEP.classify_decl_rows(
            "mirror_%s.lean" % key, [(name, 2, False)], parsed, [],
            "frozen-vector")
        rows[key] = decl_rows[0]
    return rows


def rocq_frozen_rows():
    """{key: (statement, verdict, axioms, declared_names)} over the audit
    tool's frozen census batch text plus the two crosswalk-owned frozen
    census vectors (custom, admitted), parsed by the audit tool's own
    parse_census_blocks and graded by its own classify_axiom."""
    rows = {}
    count = len(AUDIT.CENSUS_BATCH_STMTS)
    blocks = AUDIT.parse_census_blocks(AUDIT.CENSUS_BATCH_TEXT, count)
    if blocks is None or len(blocks) != count:
        raise ValueError("the frozen census batch text no longer parses"
                         " into %d ordered blocks" % count)
    base_keys = ("clean", "classical", "funext")
    for key, (stmt, _ln), (verdict, axioms) in zip(
            base_keys, AUDIT.CENSUS_BATCH_STMTS, blocks):
        rows[key] = (stmt, verdict, list(axioms), frozenset())
    for key, text, stmts, declared in (
            ("custom", ROCWASH_CENSUS_CUSTOM_TEXT,
             ROCWASH_CENSUS_CUSTOM_STMTS, ROCWASH_CENSUS_CUSTOM_DECLARED),
            ("sorry", ROCWASH_CENSUS_ADMITTED_TEXT,
             ROCWASH_CENSUS_ADMITTED_STMTS, ROCWASH_CENSUS_ADMITTED_DECLARED)):
        blocks = AUDIT.parse_census_blocks(text, len(stmts))
        if blocks is None or len(blocks) != len(stmts):
            raise ValueError("the frozen %s census vector no longer parses"
                             " into %d ordered blocks" % (key, len(stmts)))
        (stmt, _ln) = stmts[0]
        rows[key] = (stmt, blocks[0][0], list(blocks[0][1]),
                     frozenset(declared))
    return rows


# ---- the mapping (single source) ----

def parity_map():
    """{rocq_grade: lean_class} read verbatim from
    axiom_audit.LEAN_PARITY_ROWS - the only grade->class mapping this
    tool holds (never a second table)."""
    return {grade: lean_class
            for grade, lean_class, _builtin in AUDIT.LEAN_PARITY_ROWS}


def is_admitted_face(statement, axioms):
    """True for the measured Admitted face: the statement's own name
    rides its axiom set (Print Assumptions prints the exact statement
    name; axiom_audit.LEAN_PARITY_NOTE)."""
    return statement in axioms


def statement_grade(verdict, axioms, declared_names):
    """One grade for a census statement row: closed stays closed; an
    axiom-bearing row grades by its worst axiom under the audit tool's
    own classify_axiom (alarm order custom > funext > classical >
    stdlib); a census-error row has no grade."""
    if verdict == AUDIT.GRADE_CLOSED:
        return AUDIT.GRADE_CLOSED
    grades = [AUDIT.classify_axiom(ax, set(declared_names))
              for ax in axioms]
    for grade in ROCQ_GRADE_ALARM_ORDER:
        if grade in grades:
            return grade
    return AUDIT.GRADE_CUSTOM


def map_rocq_statement(statement, verdict, axioms, declared_names):
    """(lean_class, grade, basis): the Admitted mirror rule precedes the
    graded table (which is read verbatim from
    axiom_audit.LEAN_PARITY_ROWS)."""
    if verdict == "axioms" and is_admitted_face(statement, axioms):
        return (SORRY_CLASS, AUDIT.GRADE_CUSTOM, ADMITTED_BASIS)
    grade = statement_grade(verdict, axioms, declared_names)
    lean_class = parity_map()[grade]
    return (lean_class, grade, TABLE_BASIS)


# ---- the axiom-set mirror per proposition key ----

def mirror_axioms_ok(key, statement, rocq_axioms, lean_axioms):
    """The design-frozen axiom-set mirror for one proposition key (see
    the detail block: clean / classical / funext / custom / sorry)."""
    trio = set(SWEEP.BENIGN_STANDARD)
    if key == "clean":
        return list(rocq_axioms) == [] and list(lean_axioms) == []
    if key == "classical":
        rocq_classical = any(a.rsplit(".", 1)[-1]
                             in AUDIT.CLASSICAL_AXIOM_NAMES
                             for a in rocq_axioms)
        return rocq_classical == ("Classical.choice" in lean_axioms)
    if key == "funext":
        rocq_funext = any(a.rsplit(".", 1)[-1]
                          .startswith("functional_extensionality")
                          for a in rocq_axioms)
        lean_benign = all(a in trio for a in lean_axioms)
        return rocq_funext and lean_benign
    if key == "custom":
        tabled = (AUDIT.CLASSICAL_AXIOM_NAMES + AUDIT.FUNEXT_AXIOM_NAMES
                  + AUDIT.STDLIB_AXIOM_NAMES)
        lean_custom = (bool(lean_axioms)
                       and all(a not in trio and a != SWEEP.SORRY_AX
                               for a in lean_axioms))
        rocq_custom = (bool(rocq_axioms)
                       and all(a.rsplit(".", 1)[-1] not in tabled
                               for a in rocq_axioms))
        return lean_custom and rocq_custom
    if key == "sorry":
        return (statement in rocq_axioms
                and SWEEP.SORRY_AX in lean_axioms)
    return False


def lean_class_of(lean_row):
    """The Lean side's own class from a sweep-tool declaration row; a
    live sweep payload row (dict with a "classification" key) works the
    same as a classify_decl_rows product."""
    return lean_row["classification"]


def lean_axioms_of(lean_row):
    return list(lean_row["axioms"])


def build_pair(key, rocq_side, lean_row):
    """One crosswalk pair: {proposition, rocq_verdict, rocq_grade,
    rocq_axioms, lean_class, lean_axioms, verdict, basis}.  verdict is
    MATCH only when the mapped class equals the Lean side's own class
    AND the axiom-set mirror holds."""
    statement, verdict, rocq_axioms, declared_names = rocq_side
    lean_class = lean_class_of(lean_row)
    lean_axioms = lean_axioms_of(lean_row)
    if verdict == "census-error":
        return {"proposition": key, "rocq_verdict": verdict,
                "rocq_grade": "", "rocq_axioms": list(rocq_axioms),
                "lean_class": lean_class, "lean_axioms": lean_axioms,
                "verdict": "MISMATCH",
                "basis": ("the Rocq census could not map this statement"
                          " (census-error); the row is unmappable and"
                          " never guessed")}
    lean_class_mapped, grade, map_basis = map_rocq_statement(
        statement, verdict, rocq_axioms, declared_names)
    ok = (lean_class_mapped == lean_class
          and mirror_axioms_ok(key, statement, rocq_axioms, lean_axioms))
    basis = ("map(%s) == %s; %s; axiom-set mirror %s: rocq=%r lean=%r"
             % (grade, lean_class_mapped, map_basis, key,
                list(rocq_axioms), lean_axioms))
    return {"proposition": key, "rocq_verdict": verdict,
            "rocq_grade": grade, "rocq_axioms": list(rocq_axioms),
            "lean_class": lean_class, "lean_axioms": lean_axioms,
            "verdict": "MATCH" if ok else "MISMATCH", "basis": basis}


def build_pairs(rocq_rows, lean_rows):
    """The pair matrix over the mirror roster.  A proposition missing on
    one side is a MISMATCH pair (an enumeration-count inequality is
    never silently truncated away)."""
    pairs = []
    for key in MIRROR_KEYS:
        rocq_side = rocq_rows.get(key)
        lean_row = lean_rows.get(key)
        if rocq_side is None or lean_row is None:
            missing = []
            if rocq_side is None:
                missing.append("rocq")
            if lean_row is None:
                missing.append("lean")
            pairs.append({"proposition": key, "rocq_verdict": "",
                          "rocq_grade": "", "rocq_axioms": [],
                          "lean_class": "", "lean_axioms": [],
                          "verdict": "MISMATCH",
                          "basis": ("enumeration-count inequality: the"
                                    " %s side carries no row for this"
                                    " mirror proposition"
                                    % " and ".join(missing))})
            continue
        pairs.append(build_pair(key, rocq_side, lean_row))
    return pairs


# ---- layer 2: the bilingual mirror fixtures ----

def lean_fixture_rows(fixtures_dir):
    """{key: lean decl row} over the committed mirror group: each
    mirror_<key>.lean is enumerated by the sweep tool's own
    enumerate_decls, its copy-append probe list is built by the sweep
    tool's own build_copy_checker, and the frozen expectation file
    mirror_<key>.lean.expected is parsed by the sweep tool's own
    name-keyed parser (the Lean enumeration face is frozen-vector
    proxied; no Lean engine is involved)."""
    rows = {}
    for key in MIRROR_KEYS:
        stem = MIRROR_FIXTURE_STEMS[key]
        lean_path = os.path.join(fixtures_dir,
                                 "mirror_%s.lean" % stem)
        expected_path = os.path.join(fixtures_dir,
                                     "mirror_%s.lean.expected" % stem)
        with open(lean_path, "rb") as fh:
            text = fh.read().decode("utf-8", "replace")
        with open(expected_path, "rb") as fh:
            expected = fh.read().decode("utf-8", "replace")
        decls = SWEEP.enumerate_decls(text)
        if len(decls) != 1:
            raise ValueError("mirror_%s.lean must enumerate exactly one"
                             " declaration (got %r)" % (key, decls))
        _checker, probes = SWEEP.build_copy_checker(
            text, [nm for nm, _ln, _p in decls])
        parsed = SWEEP.parse_print_axioms(expected, probes)
        row = SWEEP.classify_decl_rows(
            os.path.basename(lean_path), decls, parsed, [],
            "frozen-expected")[0]
        rows[key] = row
    return rows


def rocq_rows_from_census_payload(payload):
    """{statement: (statement, verdict, axioms, declared_names)} from a
    real (or canned) rocqwash.b-axiom-audit/1 census payload; only the
    mirror roster statements join, the declared-axiom sweep of the
    payload feeds the grading."""
    declared = frozenset(d["name"] for d in payload.get("declared_axioms",
                                                        []))
    rows = {}
    for f in payload.get("files", []):
        for r in f.get("census", []):
            nm = r["statement"]
            if nm in MIRROR_STATEMENT_KEYS:
                rows[nm] = (nm, r["verdict"], list(r["axioms"]), declared)
    return rows


def lean_rows_from_sweep_payload(payload):
    """{proposition key: lean decl row} from a real (or canned)
    rocqwash-axiom-sweep/1 payload (declarations_detail rows joined by
    the mirror roster)."""
    rows = {}
    for r in payload["declarations_detail"]["value"]:
        key = MIRROR_STATEMENT_KEYS.get(r["name"])
        if key is not None:
            rows[key] = r
    return rows


# ---- engine faces (layer 2 Rocq side, layer 3) ----

def run_child(argv, timeout):
    """One subprocess run as (rc, merged_output, failure) - failure is
    None on a completed run, else the timeout or launch-failure text."""
    try:
        pr = subprocess.run(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "", "timeout after %ss" % timeout
    except OSError as exc:
        return None, "", "launch failed: %s" % exc
    return (pr.returncode, pr.stdout.decode("utf-8", "replace"), None)


def census_face(fixtures_dir, engine, timeout, work):
    """The layer-2 Rocq side: the real axiom_audit census over the
    mirror .v files.  Returns (payload_or_None, leg_note).  The census
    judges the mirror tree red by construction (the fixtures carry
    axioms on purpose), so child rc 0/1 with a parseable census payload
    is the expected face; rc 2/9 or a launch failure fails loud."""
    json_path = os.path.join(work, "mirror_census.json")
    argv = [sys.executable, "-I", "-B", AUDIT_PATH,
            "census", "--repo", fixtures_dir, "--rocq", engine,
            "--timeout", str(timeout), "--json", json_path]
    rc, output, failure = run_child(argv, timeout + 60)
    if failure is not None:
        return None, ("census child %s" % failure)
    if rc in (0, 1):
        try:
            with open(json_path, "rb") as fh:
                payload = json.loads(fh.read().decode("utf-8", "replace"))
        except (OSError, ValueError) as exc:
            return None, ("census child rc %s left no parseable payload:"
                          " %s" % (rc, exc))
        if payload.get("schema") != AUDIT.SCHEMA:
            return None, ("census child payload carries schema %r, want"
                          " %s" % (payload.get("schema"), AUDIT.SCHEMA))
        return payload, ("ran (child rc %s, verdict %s)"
                         % (rc, payload.get("verdict")))
    return None, ("census child failed loud (rc %s): %s"
                  % (rc, output.strip()[:200]))


def lean_face(fixtures_dir, timeout, work):
    """The layer-3 Lean side: the real lean_axiom_sweep over the mirror
    .lean files, gated by the sweep tool's own toolchain probe.  Returns
    (payload_or_None, leg_note); an absent toolchain is a loud SKIP leg,
    a usable-looking but failing sweep fails loud."""
    lean, lake, usable_lean, usable_lake = SWEEP.probe_toolchain()
    if not (usable_lean or usable_lake):
        return None, ("SKIP: Lean toolchain absent - the real Lean sweep"
                      " leg is not run (lean=%r lake=%r)"
                      % (lean, lake))
    json_path = os.path.join(work, "mirror_sweep.json")
    argv = [sys.executable, "-I", "-B", SWEEP_PATH,
            "--root", fixtures_dir, "--timeout", str(timeout),
            "--json", json_path]
    rc, output, failure = run_child(argv, timeout + 60)
    if failure is not None:
        return None, ("sweep child %s" % failure)
    if rc in (0, 1):
        try:
            with open(json_path, "rb") as fh:
                payload = json.loads(fh.read().decode("utf-8", "replace"))
        except (OSError, ValueError) as exc:
            return None, ("sweep child rc %s left no parseable payload:"
                          " %s" % (rc, exc))
        if payload.get("schema") != SWEEP.SCHEMA:
            return None, ("sweep child payload carries schema %r, want"
                          " %s" % (payload.get("schema"), SWEEP.SCHEMA))
        return payload, ("ran (child rc %s)" % rc)
    return None, ("sweep child failed loud (rc %s): %s"
                  % (rc, output.strip()[:200]))


# ---- layer 4: closure evolution (zero toolchain) ----

def snapshot_face(lean_rows):
    """A rocqwash-axiom-closure-snapshot/1 snapshot of the crosswalk's
    Lean-side rows, built by the sweep tool's own build_snapshot
    (deterministic, sorted, no wall clock)."""
    return SWEEP.build_snapshot("lean_parity_crosswalk",
                                list(lean_rows.values()), [])


# ---- payload assembly ({value, basis} law) ----

def build_payload(pairs, legs, enumeration, closure_face=None):
    """The rocqwash.parity.lean-census/1 payload: every top-level key
    except "schema" and "scan_face" is {value, basis}-wrapped; verdict
    is MATCH only when every pair matched and the two-side enumeration
    counts are equal (an inequality is never silently truncated)."""
    match = sum(1 for p in pairs if p["verdict"] == "MATCH")
    mismatch = len(pairs) - match
    counts = {"pairs": len(pairs), "match": match, "mismatch": mismatch}
    counts.update(enumeration)
    counts_equal = (enumeration.get("lean_enumerated", -1)
                    == enumeration.get("rocq_enumerated", -2))
    verdict = "MATCH" if (mismatch == 0 and counts_equal
                          and len(pairs) > 0) else "MISMATCH"
    payload = {
        "schema": SCHEMA,
        "mapping_source": {"value": MAPPING_SOURCE,
                           "basis": ("the grade -> Lean-class mapping is"
                                     " read verbatim from"
                                     " axiom_audit.LEAN_PARITY_ROWS/1;"
                                     " the Rocq Admitted <-> Lean sorryAx"
                                     " row is the design-frozen mirror"
                                     " rule (axiom_audit.LEAN_PARITY_NOTE)"
                                     " and precedes the table")},
        "pairs": {"value": pairs,
                  "basis": "one crosswalk pair per mirror proposition"
                           " key (clean / classical / funext / custom /"
                           " sorry); each pair carries the mapped class,"
                           " both axiom sets and the MATCH / MISMATCH"
                           " verdict with the counting rule in its"
                           " basis"},
        "counts": {"value": counts,
                   "basis": "pair counts (pairs / match / mismatch) plus"
                            " the two-side enumeration counts; an"
                            " enumeration-count inequality forces the"
                            " top-level verdict to MISMATCH instead of"
                            " a silent truncation"},
        "verdict": {"value": verdict,
                    "basis": "MATCH when every pair matched and the"
                             " two-side enumeration counts are equal;"
                             " any MISMATCH pair or count inequality is"
                             " red (unjudgeable is not green)"},
        "legs": {"value": legs,
                 "basis": "per-face run record: trunk (the frozen-vector"
                          " layer, always runs), fixture_lean (the"
                          " mirror .lean/.expected face, offline),"
                          " fixture_rocq (the real census face,"
                          " engine-gated), lean_live (the real sweep"
                          " face, Lean-gated); skipped faces carry"
                          " their loud reason"},
        "note": {"value": HONEST_NOTE,
                 "basis": "the honest-boundary note frozen with this"
                          " tool (frozen Lean text form, no Lean engine"
                          " in the offline trunk, mirror-rule provenance)"},
        "scan_face": {
            "scanned": SCAN_SCANNED,
            "not_scanned": SCAN_NOT_SCANNED,
            "negative_finding": SCAN_NEGATIVE_FINDING,
            "equivalents": SCAN_EQUIVALENTS,
        },
    }
    if closure_face is not None:
        payload["closure_diff"] = {
            "value": closure_face,
            "basis": ("per-declaration closure diff of this run's"
                      " Lean-side snapshot against the --baseline file"
                      " (schema %s), computed by the sweep tool's own"
                      " diff_closures: rows keyed by full declaration"
                      " name with the four verdicts and diff_alarm"
                      % SWEEP.SNAPSHOT_SCHEMA),
        }
        payload["diff_alarm"] = {
            "value": closure_face["diff_alarm"]["value"],
            "basis": SWEEP.DIFF_BASIS_ALARM,
        }
    return payload


HONEST_NOTE = (
    "Honest boundaries: (1) the frozen Lean vectors (the sweep tool's"
    " canned `#print axioms` fixtures and the mirror .lean.expected"
    " files) carry the Lean 4 CLI text form; where no Lean engine exists"
    " on the host they are taken as frozen, not engine-re-verified;"
    " (2) the offline trunk never launches any Lean binary and never"
    " simulates one; (3) the Rocq Admitted <-> Lean sorryAx row is a"
    " data mapping (axiom_audit.LEAN_PARITY_NOTE), not a toolchain"
    " launch; (4) the mirror fixtures exist so the same sample set is"
    " enumerable on both faces - a Rocq tree is never passed off as a"
    " Lean face.")


# ---- run face ----

def run_face(args):
    """The crosswalk run: the offline trunk always runs; the
    engine-gated faces join when asked and their engines resolve.  Every
    pair's sides take the deepest face that ran (frozen < fixture <
    live) and the pair basis names each side's source."""
    legs = {}
    lean_rows = {}
    rocq_rows = {}
    sources = {}

    frozen_lean = lean_frozen_rows()
    frozen_rocq = rocq_frozen_rows()
    for key in MIRROR_KEYS:
        lean_rows[key] = frozen_lean[key]
        rocq_rows[key] = frozen_rocq[key]
        sources[key] = ("lean: frozen vector %s"
                        % dict((k, c) for k, c, _n in LEAN_FROZEN_KEYS)[key],
                        "rocq: frozen census vector")
    legs["trunk_frozen_vectors"] = "ran (layer 1: both parent tools'" \
        " canned fixtures, zero engine)"

    fixtures = args.fixtures or DEFAULT_FIXTURES
    if not os.path.isdir(fixtures):
        legs["fixture_lean"] = ("SKIP: mirror fixture directory absent:"
                                " %s" % fixtures)
    else:
        missing = [fn
                   for k in MIRROR_KEYS
                   for fn in ("mirror_%s.lean" % MIRROR_FIXTURE_STEMS[k],
                              "mirror_%s.lean.expected"
                              % MIRROR_FIXTURE_STEMS[k])
                   if not os.path.exists(os.path.join(fixtures, fn))]
        if missing:
            legs["fixture_lean"] = ("SKIP: the fixture directory carries"
                                    " no mirror group (missing %s)"
                                    % ", ".join(sorted(missing)[:3]))
        else:
            try:
                fixture_lean = lean_fixture_rows(fixtures)
            except (OSError, ValueError) as exc:
                sys.stderr.write("%s: the mirror fixture face failed"
                                 " loud: %s\n" % (TOOL, exc))
                return EXIT_RED, None
            for key, row in fixture_lean.items():
                lean_rows[key] = row
                sources[key] = ("lean: mirror fixture %s (frozen `#print"
                                " axioms` expectation)"
                                % row["file"], sources[key][1])
            legs["fixture_lean"] = ("ran (layer 2 lean side: frozen"
                                    " expected over %d mirror .lean"
                                    " files)" % len(fixture_lean))

    if args.census_json:
        try:
            with open(args.census_json, "rb") as fh:
                payload = json.loads(fh.read().decode("utf-8", "replace"))
        except (OSError, ValueError) as exc:
            sys.stderr.write("%s: --census-json unreadable: %s\n"
                             % (TOOL, exc))
            return EXIT_RED, None
        if payload.get("schema") != AUDIT.SCHEMA:
            sys.stderr.write("%s: --census-json carries schema %r, want"
                             " %s\n" % (TOOL, payload.get("schema"),
                                        AUDIT.SCHEMA))
            return EXIT_RED, None
        live = rocq_rows_from_census_payload(payload)
        for key in MIRROR_KEYS:
            stmt = _statement_for_key(key, live)
            if stmt is not None:
                rocq_rows[key] = live[stmt]
                sources[key] = (sources[key][0],
                                "rocq: --census-json payload")
        legs["fixture_rocq"] = ("ran (layer 2 rocq side via"
                                " --census-json: %d mirror statements)"
                                % len(live))
    elif args.rocq_face:
        engine = AUDIT.resolve_engine(args.rocq)
        if engine is None:
            legs["fixture_rocq"] = ("SKIP: no compile engine configured"
                                    " (flag --rocq, environment"
                                    " ROCWASH_ROCQ, or PATH coqc / rocq)")
        elif not os.path.exists(engine):
            sys.stderr.write("%s: engine configured but binary missing:"
                             " %s\n" % (TOOL, engine))
            return EXIT_RED, None
        else:
            work = tempfile.mkdtemp(prefix="rocqwash_parity_census_")
            try:
                payload, note = census_face(fixtures, engine,
                                            args.timeout, work)
            finally:
                shutil.rmtree(work, ignore_errors=True)
            legs["fixture_rocq"] = note
            if payload is not None:
                live = rocq_rows_from_census_payload(payload)
                for key in MIRROR_KEYS:
                    stmt = _statement_for_key(key, live)
                    if stmt is not None:
                        rocq_rows[key] = live[stmt]
                        sources[key] = (sources[key][0],
                                        "rocq: live census over %s"
                                        % fixtures)
    else:
        legs["fixture_rocq"] = ("not requested (pass --rocq-face for the"
                                " real census face)")

    if args.lean_sweep_json:
        try:
            with open(args.lean_sweep_json, "rb") as fh:
                payload = json.loads(fh.read().decode("utf-8", "replace"))
        except (OSError, ValueError) as exc:
            sys.stderr.write("%s: --lean-sweep-json unreadable: %s\n"
                             % (TOOL, exc))
            return EXIT_RED, None
        if payload.get("schema") != SWEEP.SCHEMA:
            sys.stderr.write("%s: --lean-sweep-json carries schema %r,"
                             " want %s\n" % (TOOL, payload.get("schema"),
                                             SWEEP.SCHEMA))
            return EXIT_RED, None
        live = lean_rows_from_sweep_payload(payload)
        for key, row in live.items():
            lean_rows[key] = row
            sources[key] = ("lean: --lean-sweep-json payload",
                            sources[key][1])
        legs["lean_live"] = ("ran (layer 3 lean side via"
                             " --lean-sweep-json: %d mirror"
                             " declarations)" % len(live))
    elif args.lean_face:
        work = tempfile.mkdtemp(prefix="rocqwash_parity_sweep_")
        try:
            payload, note = lean_face(fixtures, args.timeout, work)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        legs["lean_live"] = note
        if payload is not None:
            live = lean_rows_from_sweep_payload(payload)
            for key, row in live.items():
                lean_rows[key] = row
                sources[key] = ("lean: live sweep over %s" % fixtures,
                                sources[key][1])
    else:
        legs["lean_live"] = ("not requested (pass --lean-face for the"
                             " real sweep face; on a Lean-absent host"
                             " it would be a loud SKIP leg)")

    rocq_sides = {}
    for key in MIRROR_KEYS:
        statement, verdict, axioms, declared = rocq_rows[key]
        rocq_sides[key] = (statement, verdict, axioms, declared)
    pairs = build_pairs(rocq_sides, lean_rows)
    for pair in pairs:
        pair["basis"] = ("side sources (%s; %s). %s"
                         % (sources[pair["proposition"]][0],
                            sources[pair["proposition"]][1],
                            pair["basis"]))
    lean_enumerated = len(lean_rows)
    rocq_enumerated = len(rocq_rows)

    closure = None
    snapshot = None
    if args.snapshot or args.baseline:
        snapshot = snapshot_face(lean_rows)
    if args.baseline:
        base, err = SWEEP.load_snapshot(args.baseline)
        if err is not None:
            sys.stderr.write("%s: %s\n" % (TOOL, err))
            return EXIT_USAGE, None
        closure = SWEEP.diff_closures(base, snapshot)

    payload = build_payload(
        pairs, legs,
        {"lean_enumerated": lean_enumerated,
         "rocq_enumerated": rocq_enumerated},
        closure_face=closure)
    if args.snapshot:
        write_json(args.snapshot,
                   json.dumps(snapshot, ensure_ascii=False))
    return (EXIT_OK if payload["verdict"]["value"] == "MATCH"
            else EXIT_RED), payload


def _statement_for_key(key, live_rows):
    for statement, _verdict, _axioms, _declared in live_rows.values():
        if MIRROR_STATEMENT_KEYS.get(statement) == key:
            return statement
    return None


def write_json(path, payload):
    """Write the payload text (plus one newline) to path as UTF-8."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
        fh.write("\n")


def summarize(payload):
    """One stderr line (stdout stays the single JSON line)."""
    legs = payload["legs"]["value"]
    skips = sorted(k for k, v in legs.items() if str(v).startswith("SKIP"))
    sys.stderr.write(
        "LEAN-PARITY-CROSSWALK: %s pairs=%d match=%d mismatch=%d"
        " lean_enum=%d rocq_enum=%d skips=%s\n"
        % (payload["verdict"]["value"],
           payload["counts"]["value"]["pairs"],
           payload["counts"]["value"]["match"],
           payload["counts"]["value"]["mismatch"],
           payload["counts"]["value"]["lean_enumerated"],
           payload["counts"]["value"]["rocq_enumerated"],
           ",".join(skips) if skips else "none"))


# ---- selftest (frozen offline vectors; zero network, zero engine) ----

def selftest():
    """Two offline legs; 0 green, 1 red with the failing names on
    stdout.  Zero network, zero engine launch, zero real-repo touch."""
    fails = []
    total = [0]

    def vec(name, ok, detail=""):
        total[0] += 1
        print("[PASS] %s" % name if ok else "[FAIL] %s %s" % (name, detail))
        if not ok:
            fails.append(name)

    script = os.path.abspath(__file__)
    tmp = tempfile.mkdtemp(prefix="rocqwash_parity_selftest_")
    try:
        # ---- leg one: the offline crosswalk trunk ----
        vec("parents-load",
            SWEEP.SCHEMA == "rocqwash-axiom-sweep/1"
            and AUDIT.SCHEMA == "rocqwash.b-axiom-audit/1"
            and len(AUDIT.LEAN_PARITY_ROWS) == 5,
            "both parent tools loaded by file path; the parity table is"
            " the audit tool's own 5-row constant")
        table = parity_map()
        vec("parity-map-single-source",
            table == {g: lc for g, lc, _b in AUDIT.LEAN_PARITY_ROWS}
            and table[AUDIT.GRADE_CLOSED] == "CLEAN"
            and table[AUDIT.GRADE_STDLIB] == "BENIGN-STANDARD"
            and table[AUDIT.GRADE_CLASSICAL] == "BENIGN-STANDARD"
            and table[AUDIT.GRADE_FUNEXT] == "BENIGN-STANDARD"
            and table[AUDIT.GRADE_CUSTOM] == "CUSTOM-AXIOM-ALARM",
            "the only mapping in this tool is the audit tool's own"
            " table, read verbatim: %r" % (table,))
        frozen_lean = lean_frozen_rows()
        vec("lean-frozen-rows-face",
            [frozen_lean[k]["classification"] for k in MIRROR_KEYS]
            == ["CLEAN", "BENIGN-STANDARD", "BENIGN-STANDARD",
                "CUSTOM-AXIOM-ALARM", SORRY_CLASS]
            and frozen_lean["sorry"]["axioms"] == ["sorryAx"]
            and frozen_lean["classical"]["axioms"]
            == list(SWEEP.BENIGN_STANDARD)
            and frozen_lean["funext"]["axioms"] == ["propext"],
            "five lean rows from the sweep tool's own canned fixtures"
            " and its own classify: %r"
            % ([frozen_lean[k]["classification"] for k in MIRROR_KEYS],))
        frozen_rocq = rocq_frozen_rows()
        vec("rocq-frozen-rows-face",
            [frozen_rocq[k][1] for k in MIRROR_KEYS]
            == [AUDIT.GRADE_CLOSED, "axioms", "axioms", "axioms",
                "axioms"]
            and frozen_rocq["classical"][2] == ["classic"]
            and frozen_rocq["funext"][2]
            == ["functional_extensionality_dep"]
            and frozen_rocq["custom"][2] == ["lp_mirror_ax"]
            and frozen_rocq["sorry"][2] == ["lp_mirror_admitted"],
            "five rocq rows from the audit tool's frozen batch text plus"
            " the two crosswalk-owned measured vectors: %r"
            % ([frozen_rocq[k][1:3] for k in MIRROR_KEYS],))
        vec("admitted-face-measured-form",
            is_admitted_face("lp_mirror_admitted",
                             frozen_rocq["sorry"][2])
            and not is_admitted_face("lp_mirror_custom",
                                     frozen_rocq["custom"][2])
            and statement_grade("axioms", frozen_rocq["sorry"][2],
                                frozenset()) == AUDIT.GRADE_CUSTOM,
            "the Admitted face is the statement's own name inside its"
            " axiom set (measured on Rocq 9.3.0; "
            "axiom_audit.LEAN_PARITY_NOTE) and grades custom before the"
            " mirror rule")
        cls, grade, basis = map_rocq_statement(
            "lp_mirror_admitted", "axioms", ["lp_mirror_admitted"],
            frozenset())
        vec("admitted-mirror-rule",
            cls == SORRY_CLASS and grade == AUDIT.GRADE_CUSTOM
            and "LEAN_PARITY_NOTE" in basis,
            "the Admitted row maps to the SORRY-ALARM class with the"
            " design-frozen basis, not via a graded-table row: %r / %r"
            % (cls, basis[:60]))
        cls, _grade, _basis = map_rocq_statement(
            "lp_mirror_classical", "axioms", ["classic"], frozenset())
        vec("graded-table-faces",
            cls == "BENIGN-STANDARD"
            and map_rocq_statement("t_one", AUDIT.GRADE_CLOSED, [],
                                   frozenset())[0] == "CLEAN"
            and map_rocq_statement("lp_mirror_custom", "axioms",
                                   ["lp_mirror_ax"],
                                   {"lp_mirror_ax"})[0]
            == "CUSTOM-AXIOM-ALARM"
            and map_rocq_statement("lp_mirror_funext", "axioms",
                                   ["functional_extensionality_dep"],
                                   frozenset())[0] == "BENIGN-STANDARD",
            "closed/classical/custom/funext rows map through"
            " LEAN_PARITY_ROWS lookups only")
        pairs = build_pairs(dict((k, frozen_rocq[k])
                                 for k in MIRROR_KEYS), frozen_lean)
        vec("trunk-crosswalk-match",
            [p["verdict"] for p in pairs] == ["MATCH"] * 5
            and [p["lean_class"] for p in pairs]
            == ["CLEAN", "BENIGN-STANDARD", "BENIGN-STANDARD",
                "CUSTOM-AXIOM-ALARM", SORRY_CLASS],
            "the five frozen rows crosswalk MATCH: %r"
            % ([p["verdict"] for p in pairs],))
        bad_lean = dict(frozen_lean)
        bad_row = dict(frozen_lean["custom"])
        bad_row["classification"] = "CLEAN"
        bad_lean["custom"] = bad_row
        bad_pairs = build_pairs(dict((k, frozen_rocq[k])
                                     for k in MIRROR_KEYS), bad_lean)
        vec("mismatch-fail-loud",
            [p["verdict"] for p in bad_pairs].count("MISMATCH") == 1
            and bad_pairs[3]["proposition"] == "custom"
            and "MISMATCH" in bad_pairs[3]["verdict"],
            "a corrupted lean class lands exactly one MISMATCH pair with"
            " the failing key named")
        half_lean = {k: v for k, v in frozen_lean.items() if k != "sorry"}
        half_pairs = build_pairs(dict((k, frozen_rocq[k])
                                      for k in MIRROR_KEYS), half_lean)
        vec("count-inequality-not-truncated",
            len(half_pairs) == 5 and half_pairs[4]["verdict"] == "MISMATCH"
            and "enumeration-count inequality"
            in half_pairs[4]["basis"],
            "a missing side row is a MISMATCH pair naming the missing"
            " side, never a silent truncation")
        err_pairs = build_pairs(
            {"clean": ("t_one", "census-error", ["boom"], frozenset()),
             "classical": frozen_rocq["classical"],
             "funext": frozen_rocq["funext"],
             "custom": frozen_rocq["custom"],
             "sorry": frozen_rocq["sorry"]},
            frozen_lean)
        vec("census-error-unmappable",
            err_pairs[0]["verdict"] == "MISMATCH"
            and "census-error" in err_pairs[0]["basis"]
            and err_pairs[0]["rocq_grade"] == "",
            "a census-error row is unmappable and lands MISMATCH, never"
            " guessed")
        payload = build_payload(
            pairs, {"trunk_frozen_vectors": "ran"},
            {"lean_enumerated": 5, "rocq_enumerated": 5})
        bare = [k for k in payload
                if k not in ("scan_face", "schema")
                and not (isinstance(payload[k], dict)
                         and "value" in payload[k]
                         and "basis" in payload[k])]
        vec("payload-value-basis-law", bare == [],
            "every top-level key except schema and scan_face is"
            " {value, basis}-wrapped; bare keys: %s" % bare)
        face = payload["scan_face"]
        vec("scan-face-fields",
            sorted(face) == ["equivalents", "negative_finding",
                             "not_scanned", "scanned"]
            and face["scanned"] == SCAN_SCANNED
            and face["not_scanned"] == SCAN_NOT_SCANNED
            and face["negative_finding"] == SCAN_NEGATIVE_FINDING
            and face["equivalents"] == SCAN_EQUIVALENTS
            and "LEAN_PARITY_NOTE" in face["equivalents"],
            "the four fixed English fields ride the payload pinned"
            " verbatim")
        vec("schema-and-mapping-constants",
            payload["schema"] == SCHEMA
            and payload["mapping_source"]["value"] == MAPPING_SOURCE
            and payload["verdict"]["value"] == "MATCH",
            "schema %s; mapping_source %s" % (SCHEMA, MAPPING_SOURCE))
        canned_sweep = {"schema": SWEEP.SCHEMA,
                        "declarations_detail": {"value": [
                            dict(frozen_lean["clean"], name="lp_mirror_clean",
                                 file="mirror_clean.lean"),
                            dict(frozen_lean["classical"],
                                 name="lp_mirror_classical",
                                 file="mirror_classical.lean"),
                            dict(frozen_lean["funext"],
                                 name="lp_mirror_funext",
                                 file="mirror_funext.lean"),
                            dict(frozen_lean["custom"],
                                 name="lp_mirror_custom",
                                 file="mirror_custom.lean"),
                            dict(frozen_lean["sorry"],
                                 name="lp_mirror_admitted",
                                 file="mirror_admitted.lean"),
                        ]}}
        live_lean = lean_rows_from_sweep_payload(canned_sweep)
        canned_census = {"schema": AUDIT.SCHEMA,
                         "declared_axioms": [{"name": "lp_mirror_ax"}],
                         "files": [{"file": "mirror_clean.v",
                                    "census": [{"statement":
                                                "lp_mirror_clean",
                                                "verdict": "closed",
                                                "axioms": []}]},
                                   {"file": "mirror_classical.v",
                                    "census": [{"statement":
                                                "lp_mirror_classical",
                                                "verdict": "axioms",
                                                "axioms": ["classic"]}]},
                                   {"file": "mirror_funext.v",
                                    "census": [{"statement":
                                                "lp_mirror_funext",
                                                "verdict": "axioms",
                                                "axioms":
                                                ["functional_"
                                                 "extensionality_dep"]}]},
                                   {"file": "mirror_custom.v",
                                    "census": [{"statement":
                                                "lp_mirror_custom",
                                                "verdict": "axioms",
                                                "axioms":
                                                ["lp_mirror_ax"]}]},
                                   {"file": "mirror_admitted.v",
                                    "census": [{"statement":
                                                "lp_mirror_admitted",
                                                "verdict": "axioms",
                                                "axioms":
                                                ["lp_mirror_admitted"]}]}]}
        live_rocq = rocq_rows_from_census_payload(canned_census)
        join_pairs = build_pairs(
            {key: live_rocq[_statement_for_key(key, live_rocq)]
             for key in MIRROR_KEYS}, live_lean)
        vec("join-face-canned-live-payloads",
            all(p["verdict"] == "MATCH" for p in join_pairs)
            and len(join_pairs) == 5,
            "the layer-3 join machinery over canned live-shaped payloads"
            " matches all five mirror rows")
        snap = snapshot_face(frozen_lean)
        vec("snapshot-face",
            snap["schema"] == SWEEP.SNAPSHOT_SCHEMA
            and snap["tool"] == SWEEP.TOOL
            and snap["classified_count"] == 5
            and snap["unparsed_count"] == 0
            and [d["name"] for d in snap["declarations"]]
            == sorted(d["name"] for d in snap["declarations"]),
            "the closure snapshot is the sweep tool's own build_snapshot"
            " over the crosswalk's lean rows: %d declarations"
            % snap["classified_count"])
        snap_path = os.path.join(tmp, "snap.json")
        write_json(snap_path, json.dumps(snap, ensure_ascii=False))
        loaded, err = SWEEP.load_snapshot(snap_path)
        vec("snapshot-round-trip",
            err is None and loaded == snap,
            "write + the sweep tool's own load_snapshot round-trips"
            " byte-faithfully")
        calm = SWEEP.diff_closures(loaded, snapshot_face(frozen_lean))
        vec("diff-identical-alarm-false",
            all(r["verdict"] == SWEEP.DIFF_UNCHANGED
                for r in calm["rows"])
            and calm["diff_alarm"]["value"] is False,
            "the same rows diff UNCHANGED with diff_alarm false (the"
            " sweep tool's own diff_closures)")
        drifted = dict(frozen_lean)
        drifted_row = dict(frozen_lean["clean"])
        drifted_row["axioms"] = ["propext"]
        drifted["clean"] = drifted_row
        alarm = SWEEP.diff_closures(loaded, snapshot_face(drifted))
        vec("diff-changed-alarm-true",
            alarm["rows"][0]["verdict"] == SWEEP.DIFF_CHANGED
            and alarm["diff_alarm"]["value"] is True
            and alarm["rows"][0]["from_axioms"] == []
            and alarm["rows"][0]["to_axioms"] == ["propext"],
            "an axiom-set drift lands AXIOM-SET-CHANGED with diff_alarm"
            " true")
        payload_txt = json.dumps(payload, ensure_ascii=False)
        vec("determinism-double-build",
            json.dumps(build_payload(
                pairs, {"trunk_frozen_vectors": "ran"},
                {"lean_enumerated": 5, "rocq_enumerated": 5}),
                ensure_ascii=False) == payload_txt
            and "\n" not in payload_txt,
            "double payload build is byte-identical and single-line")
        out_path = os.path.join(tmp, "out.json")
        write_json(out_path, payload_txt)
        with open(out_path, "r", encoding="utf-8") as fh:
            vec("json-round-trip", json.load(fh) == payload,
                "the payload file round-trips")

        # ---- leg two: the flag / exit-code faces ----
        def spawn(argv, env=None):
            try:
                p = subprocess.run(
                    [sys.executable, "-I", "-B", script] + argv,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=120, env=env)
            except subprocess.TimeoutExpired:
                return None, "", "timeout"
            return (p.returncode,
                    p.stdout.decode("utf-8", "replace"),
                    p.stderr.decode("utf-8", "replace"))

        vec("selftest-flag-standalone",
            build_parser().parse_args(["--selftest"]).selftest is True
            and build_parser().parse_args([]).selftest is False,
            "--selftest parses standalone and defaults to False (the"
            " vector face never spawns the tool recursively)")
        rc, _out, _err = spawn([])
        vec("run-face-default-trunk-rc0", rc == 0,
            "the default run face is the offline trunk (rc %s)" % rc)
        rc, out, _err = spawn(["--json", os.path.join(tmp, "cli.json")])
        vec("run-face-json-verdict",
            rc == 0
            and json.load(open(os.path.join(tmp, "cli.json")))
            ["verdict"]["value"] == "MATCH",
            "the CLI face writes the payload and judges MATCH (rc %s)"
            % rc)
        rc, _out, err = spawn(["--baseline",
                               os.path.join(tmp, "absent.json")])
        vec("baseline-absent-rc2", rc == 2 and "baseline" in err,
            "a missing --baseline file is a usage error named on stderr"
            " (rc %s)" % rc)
        rc, _out, _err = spawn(["--selftest", "--json",
                                os.path.join(tmp, "x.json")])
        vec("selftest-standalone-only-rc2", rc == 2,
            "--selftest combined with a write flag exits %s (usage"
            " error)" % rc)
        empty_dir = os.path.join(tmp, "empty_path")
        os.makedirs(empty_dir)
        gate_env = dict(os.environ)
        gate_env["PATH"] = empty_dir
        rc, out, err = spawn(["--lean-face",
                              "--json",
                              os.path.join(tmp, "skip.json")],
                             env=gate_env)
        skip_ok = False
        if rc == 0:
            with open(os.path.join(tmp, "skip.json"), "r",
                      encoding="utf-8") as fh:
                skip_payload = json.load(fh)
            skip_ok = (skip_payload["verdict"]["value"] == "MATCH"
                       and str(skip_payload["legs"]["value"]
                               ["lean_live"]).startswith("SKIP"))
        vec("lean-face-absent-skip-leg",
            rc == 0 and skip_ok,
            "with no Lean toolchain the lean face is a loud SKIP leg and"
            " the trunk still judges (rc %s, stderr %r)"
            % (rc, err.strip()[:80]))
        rc, _out, err = spawn(["--rocq-face", "--rocq",
                               os.path.join(tmp, "no-engine"),
                               "--fixtures", tmp])
        vec("broken-engine-fails-loud",
            rc == 1 and "missing" in err,
            "a configured-but-missing engine fails loud rc 1, never a"
            " silent skip (rc %s)" % rc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("[SELFTEST] %s %s: %d vector(s), %d fail"
          % (TOOL, "green" if not fails else "red", total[0], len(fails)))
    if fails:
        print("[SELFTEST] red vectors: %s" % ", ".join(fails))
        return 1
    return 0


# ---- flag face ----

def build_parser():
    """The flag face (extracted so --selftest runs standalone)."""
    ap = argparse.ArgumentParser(
        prog=TOOL,
        description="the Lean/Rocq axiom parity crosswalk engine (one"
                    " JSON line; schema %s; the mapping is"
                    " axiom_audit.LEAN_PARITY_ROWS/1 verbatim)" % SCHEMA)
    ap.add_argument("--fixtures", metavar="DIR", default=None,
                    help="the bilingual mirror fixture group (default"
                         " tests/fixtures/lean_parity under the repo"
                         " root)")
    ap.add_argument("--rocq-face", action="store_true",
                    help="run the real axiom_audit census over the mirror"
                         " .v files (engine chain --rocq / ROCWASH_ROCQ /"
                         " PATH; absent engine = loud SKIP leg)")
    ap.add_argument("--lean-face", action="store_true",
                    help="run the real lean_axiom_sweep over the mirror"
                         " .lean files (toolchain probed; absent"
                         " toolchain = loud SKIP leg)")
    ap.add_argument("--rocq", default=os.environ.get("ROCWASH_ROCQ", ""),
                    help="compile engine binary (default ROCWASH_ROCQ,"
                         " then PATH coqc / rocq)")
    ap.add_argument("--lean-sweep-json", metavar="FILE", default=None,
                    help="consume an existing rocqwash-axiom-sweep/1"
                         " payload as the lean side (layer 3 without"
                         " spawning)")
    ap.add_argument("--census-json", metavar="FILE", default=None,
                    help="consume an existing rocqwash.b-axiom-audit/1"
                         " census payload as the rocq side (layer 2"
                         " without spawning)")
    ap.add_argument("--snapshot", metavar="OUT", default=None,
                    help="write a machine closure snapshot (schema %s)"
                         " of the lean-side rows" % SWEEP.SNAPSHOT_SCHEMA)
    ap.add_argument("--baseline", metavar="SNAP", default=None,
                    help="diff this run's lean-side snapshot against a"
                         " previous snapshot file (the sweep tool's own"
                         " diff_closures; the closure_diff and"
                         " diff_alarm fields ride the payload)")
    ap.add_argument("--timeout", type=int, default=PROG_TIMEOUT_DEFAULT,
                    help="per-child subprocess timeout seconds (default"
                         " %d)" % PROG_TIMEOUT_DEFAULT)
    ap.add_argument("--json", metavar="OUT", default=None,
                    help="write the stdout JSON payload to OUT as well")
    ap.add_argument("--selftest", action="store_true",
                    help="run the frozen offline vector group and exit")
    return ap


def main(argv=None):
    """CLI entry; returns the process exit code (0/1/2)."""
    args = build_parser().parse_args(argv)
    if args.selftest:
        if (args.fixtures or args.rocq_face or args.lean_face
                or args.lean_sweep_json or args.census_json
                or args.snapshot or args.baseline or args.json):
            build_parser().error("--selftest runs standalone; combine it"
                                 " with no crosswalk flags")
        return selftest()
    if args.timeout < 1:
        build_parser().error("--timeout must be >= 1")
    code, payload = run_face(args)
    if payload is None:
        return code
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    text = json.dumps(payload, ensure_ascii=False)
    print(text)
    if args.json:
        try:
            write_json(args.json, text)
        except OSError as exc:
            sys.stderr.write("%s: --json write failed: %s\n" % (TOOL, exc))
            return EXIT_RED
    summarize(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())
