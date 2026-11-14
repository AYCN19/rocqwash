#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""termbase.py - offline terminology lookup thin layer over the E3 seed (zero network).

Purpose.  Load the built-in termbase seed (a read-only transcription
  snapshot), validate its schema fail-loud, and answer exact-face term
  lookups against the current-term column.  The layer adds no entries
  and edits nothing: the snapshot is never rewritten in place, the
  domain slots stay unfetched by design, and the network interface plus
  the DIY entry channel stay candidate faces of their own seed SPECs.

Interface.  --lookup TERM | --schema-check | --selftest, with [--db P]
  and [--json P] where applicable.  A lookup matches TERM against the
  first cell of every entry after stripping emphasis and full-width
  parentheses and splitting on the face separators (slash, full-width
  slash, arrow); a miss is data (empty result, exit 0).  Reports carry
  English keys, schema rocqwash.termbase.lookup/1, sorted keys.

Dependencies.  Python 3 standard library only; default database is
  seeds/termbase/termbase.json under the repository root two levels
  above this file (--db overrides); zero network by contract.

Evidence.  --selftest: real-seed schema validation; five single-aspect
  corruptions each flagged by name; lookup hits on single-face, multi-
  face, arrow-chain, and shared terms; miss empty; byte-identical
  renders; exit-code face 9/2/1 through main(); import face carries no
  network module.

Exit-codes.  0 accounted (lookups, misses, schema-check pass are data;
  selftest green); 1 malformed database or selftest failure (named
  problem list); 2 usage; 9 database missing or unreadable.
"""

import argparse
import copy
import io
import json
import os
import re
import shutil
import sys
import tempfile

SCHEMA = "rocqwash-termbase-seed/1"
TOOL = "termbase"
LOOKUP_SCHEMA = "rocqwash.termbase.lookup/1"
DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "seeds", "termbase", "termbase.json")

TOP_KEYS = {"description", "domain_slots", "entries", "entry_skeleton",
            "meta", "prose_notes", "schema", "slots_policy",
            "source_of_truth", "tool"}
ENTRY_KEYS = {"id", "sub_table", "row_index", "cells"}
PROSE_NOTE_KEYS = {"label", "text_verbatim"}
SUB_TABLES = ("round2", "intl", "round3", "round4")
SLOT_IDS = ["mathlib-naming-convention", "lean-style-guide", "journal-style"]
SLOT_KEYS = {"id", "title", "status", "source", "refresh_conditions",
             "content"}
KEY_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
ID_PATTERN = re.compile(r"^[a-z0-9]+-r[0-9]{2,}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

# current-term cell normalization: emphasis and full-width parentheses are
# presentation markup, faces inside one cell are separated by the slash,
# full-width slash, and arrow chains of adjudication history
FW_PAREN = re.compile("（[^）]*）")
EMPHASIS = re.compile(r"\*\*")
FACE_SPLIT = re.compile(r"／|→|/")


class TermbaseError(Exception):
    """Fail-loud carrier: kind is "missing" (exit 9) or "malformed" (exit 1)."""

    def __init__(self, kind, detail):
        super().__init__(detail)
        self.kind = kind


def fail(kind, detail):
    raise TermbaseError(kind, detail)


# ---------- schema validation (pure; returns named problems) ----------

def _walk_keys(obj, problems, where):
    if isinstance(obj, dict):
        for key, val in obj.items():
            if not KEY_PATTERN.match(key):
                problems.append("%s: non-English key %r" % (where, key))
            _walk_keys(val, problems, where)
    elif isinstance(obj, list):
        for val in obj:
            _walk_keys(val, problems, where)


def _validate_skeleton(seed, problems):
    sk = seed.get("entry_skeleton")
    if not isinstance(sk, dict):
        problems.append("entry_skeleton: missing or not an object")
        return {}
    if not (isinstance(sk.get("origin_verbatim"), str)
            and sk["origin_verbatim"].startswith("**")):
        problems.append("entry_skeleton.origin_verbatim: missing or not verbatim prose")
    subs = sk.get("sub_tables")
    if not isinstance(subs, dict) or sorted(subs.keys()) != sorted(SUB_TABLES):
        problems.append("entry_skeleton.sub_tables: keys drifted from %s"
                        % (", ".join(SUB_TABLES)))
        return {}
    for name in SUB_TABLES:
        st = subs[name]
        cols = st.get("columns")
        if not isinstance(cols, list) or cols != st.get("header_verbatim"):
            problems.append("%s: columns drifted from header_verbatim" % name)
            cols = cols if isinstance(cols, list) else []
        if not (isinstance(st.get("column_count"), int)
                and st["column_count"] == len(cols) and len(cols) >= 3):
            problems.append("%s: column_count disagrees with columns" % name)
        eng = st.get("english_column_names")
        if not (isinstance(eng, list) and len(eng) == len(cols)):
            problems.append("%s: english_column_names length mismatch" % name)
        if not (isinstance(st.get("row_count"), int) and st["row_count"] >= 1):
            problems.append("%s: row_count missing or below one" % name)
        if not (st.get("preamble_verbatim") is None
                or isinstance(st.get("preamble_verbatim"), str)):
            problems.append("%s: preamble_verbatim not a string or null" % name)
    return subs


def _validate_entries(seed, subs, problems):
    entries = seed.get("entries")
    if not (isinstance(entries, list) and entries):
        problems.append("entries: missing or empty")
        return []
    seen_ids = set()
    per_table = {}
    irregular = {r.get("id") for r in seed.get("meta", {}).get(
        "source_irregular_rows", []) if isinstance(r, dict)}
    for pos, entry in enumerate(entries):
        where = "entries[%d]" % pos
        if not isinstance(entry, dict) or set(entry.keys()) != ENTRY_KEYS:
            problems.append("%s: key set drifted from the entry skeleton" % where)
            continue
        eid = entry["id"]
        if not (isinstance(eid, str) and ID_PATTERN.match(eid)):
            problems.append("%s: id %r off the id pattern" % (where, eid))
        if eid in seen_ids:
            problems.append("%s: duplicate id %s" % (where, eid))
        seen_ids.add(eid)
        table = entry["sub_table"]
        if table not in subs:
            problems.append("%s: unknown sub_table %r" % (where, table))
            continue
        if not (isinstance(entry["row_index"], int) and entry["row_index"] >= 1):
            problems.append("%s: row_index not a positive integer" % where)
        cells = entry["cells"]
        if not (isinstance(cells, list) and cells
                and all(isinstance(c, str) and c.strip() for c in cells)):
            problems.append("%s: cells not a list of non-empty strings" % where)
            continue
        declared = subs[table].get("column_count")
        if isinstance(declared, int) and len(cells) > declared:
            problems.append("%s: %d cells exceed the declared %d columns"
                            % (where, len(cells), declared))
        if isinstance(declared, int) and len(cells) < declared and eid not in irregular:
            problems.append("%s: short row %s not registered as irregular"
                            % (where, eid))
        if eid in irregular and not (isinstance(declared, int)
                                     and len(cells) == declared - 1):
            problems.append("%s: irregular row %s registration inconsistent"
                            % (where, eid))
        per_table.setdefault(table, []).append(entry["row_index"])
    for table, indexes in sorted(per_table.items()):
        if indexes != list(range(1, len(indexes) + 1)):
            problems.append("%s: row_index sequence broken" % table)
        declared_count = subs[table].get("row_count")
        if isinstance(declared_count, int) and len(indexes) != declared_count:
            problems.append("%s: %d rows against declared row_count %d"
                            % (table, len(indexes), declared_count))
    return entries


def _validate_meta(seed, entries, problems):
    meta = seed.get("meta")
    if not isinstance(meta, dict):
        problems.append("meta: missing or not an object")
        return
    if meta.get("entry_count") != len(entries):
        problems.append("meta.entry_count disagrees with the entry list")
    counts = {}
    for entry in entries:
        table = entry.get("sub_table")
        counts[table] = counts.get(table, 0) + 1
    if meta.get("sub_table_counts") != counts:
        problems.append("meta.sub_table_counts disagrees with the entries")
    notes = seed.get("prose_notes")
    if not isinstance(notes, list):
        problems.append("prose_notes: missing or not a list")
        notes = []
    if meta.get("prose_note_count") != len(notes):
        problems.append("meta.prose_note_count disagrees with prose_notes")
    for pos, note in enumerate(notes):
        if not isinstance(note, dict) or set(note.keys()) != PROSE_NOTE_KEYS:
            problems.append("prose_notes[%d]: key set drifted" % pos)
        elif not (note["label"] and note["text_verbatim"].startswith("**")):
            problems.append("prose_notes[%d]: label or verbatim text empty" % pos)
    for row in meta.get("source_irregular_rows", []):
        if not isinstance(row, dict) or not row.get("note"):
            problems.append("meta.source_irregular_rows: row without a note")
        elif row.get("declared_columns") != row.get("actual_cells") + 1:
            problems.append("meta.source_irregular_rows: column arithmetic off")


def _validate_slots(seed, problems):
    slots = seed.get("domain_slots")
    if not (isinstance(slots, list) and len(slots) == 3):
        problems.append("domain_slots: expected exactly three slots")
        return
    if [s.get("id") if isinstance(s, dict) else None for s in slots] != SLOT_IDS:
        problems.append("domain_slots: slot id order drifted")
    for pos, slot in enumerate(slots):
        if not isinstance(slot, dict) or not set(slot.keys()) <= SLOT_KEYS:
            problems.append("domain_slots[%d]: key set drifted" % pos)
            continue
        if slot.get("status") != "unfetched":
            problems.append("domain_slots[%d]: status not unfetched" % pos)
        if slot.get("content") is not None:
            problems.append("domain_slots[%d]: unfetched slot carries content" % pos)
        conds = slot.get("refresh_conditions")
        if not (isinstance(conds, list) and conds
                and all(isinstance(c, str) and c for c in conds)):
            problems.append("domain_slots[%d]: refresh_conditions malformed" % pos)
        if not (isinstance(slot.get("source"), dict) and slot["source"]):
            problems.append("domain_slots[%d]: source not a populated object" % pos)


def _validate_source_of_truth(seed, problems):
    sot = seed.get("source_of_truth")
    if not isinstance(sot, dict):
        problems.append("source_of_truth: missing or not an object")
        return
    path = sot.get("path")
    if not (isinstance(path, str) and path.endswith(".md")):
        problems.append("source_of_truth.path: not a markdown path")
    snap = sot.get("snapshot")
    if not isinstance(snap, dict):
        problems.append("source_of_truth.snapshot: missing")
        return
    if not (isinstance(snap.get("bytes"), int) and snap["bytes"] > 0):
        problems.append("source_of_truth.snapshot.bytes: not a positive integer")
    if not (isinstance(snap.get("sha256"), str)
            and SHA256_PATTERN.match(snap["sha256"])):
        problems.append("source_of_truth.snapshot.sha256: not a hex digest")
    if not (isinstance(snap.get("mtime_utc"), str)
            and re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T", snap["mtime_utc"])):
        problems.append("source_of_truth.snapshot.mtime_utc: not an ISO instant")
    if not (isinstance(sot.get("snapshot_discipline"), str)
            and "read-only" in sot["snapshot_discipline"]):
        problems.append("source_of_truth.snapshot_discipline: not read-only")
    if not (isinstance(sot.get("section"), str)
            and sot["section"].startswith("### 4.0")):
        problems.append("source_of_truth.section: not the transcribed section")


def validate_schema(seed):
    """Return the list of named schema problems; empty means the seed holds."""
    problems = []
    if not isinstance(seed, dict):
        return ["top level: not a JSON object"]
    if seed.get("schema") != SCHEMA:
        problems.append("schema: %r instead of %s" % (seed.get("schema"), SCHEMA))
    if seed.get("tool") != TOOL:
        problems.append("tool: %r instead of %s" % (seed.get("tool"), TOOL))
    if not (isinstance(seed.get("description"), str) and seed["description"]):
        problems.append("description: missing or empty")
    if not (isinstance(seed.get("slots_policy"), str)
            and "candidate order" in seed["slots_policy"]):
        problems.append("slots_policy: missing or without the candidate-order rule")
    if set(seed.keys()) != TOP_KEYS:
        problems.append("top-level key set drifted: %s"
                        % sorted(set(seed.keys()) ^ TOP_KEYS))
    subs = _validate_skeleton(seed, problems)
    entries = _validate_entries(seed, subs, problems)
    _validate_meta(seed, entries, problems)
    _validate_slots(seed, problems)
    _validate_source_of_truth(seed, problems)
    _walk_keys(seed, problems, "keys")
    return problems


def load_termbase(path):
    """Read and validate the database; missing is exit 9, malformed exit 1."""
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as exc:
        fail("missing", "termbase database unreadable: %s (%s)" % (path, exc))
    try:
        seed = json.loads(raw)
    except ValueError as exc:
        fail("malformed", "termbase database is not valid JSON: %s (%s)"
             % (path, exc))
    problems = validate_schema(seed)
    if problems:
        fail("malformed", "termbase database fails schema validation (%d "
                          "problem(s)):\n  " % len(problems)
             + "\n  ".join(problems))
    return seed


# ---------- lookup (pure) ----------

def faces_of_text(head):
    """Faces of one cell text: markup stripped, separators split."""
    head = FW_PAREN.sub("", EMPHASIS.sub("", head))
    return [face.strip() for face in FACE_SPLIT.split(head) if face.strip()]


def faces_of_entry(entry):
    """Current-term faces of one entry: markup stripped, separators split."""
    return faces_of_text(entry["cells"][0])


def lookup(term, seed=None):
    """Exact-face matches for term; a miss is an empty list, not an error.

    The query takes the same markup stripping and separator splitting as
    the entry cells, so a raw cell string finds its own entry; seed
    defaults to the built-in database (the contract face lookup(term))."""
    if seed is None:
        seed = load_termbase(DEFAULT_DB)
    needles = set(faces_of_text(term))
    if not needles:
        return []
    return [entry for entry in seed["entries"]
            if needles & set(faces_of_entry(entry))]


# ---------- reporting ----------

def render(report):
    return json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_output(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def lookup_report(term, db_display, hits):
    return {"schema": LOOKUP_SCHEMA, "tool": TOOL, "term": term,
            "db": db_display, "hit_count": len(hits),
            "entries": hits}


# ---------- selftest ----------

def selftest(out):
    """Vectors on the real seed plus temporary fixtures; 0 green, 1 red."""
    problems = []
    work = tempfile.mkdtemp(prefix="termbase-selftest-")
    try:
        _run_vectors(out, work, problems)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if problems:
        out.write("TERMBASE-SELFTEST: FAIL (%d vector(s))\n" % len(problems))
        return 1
    out.write("TERMBASE-SELFTEST: PASS (lookup thin layer, schema fail-loud, "
              "zero network)\n")
    return 0


def _run_vectors(out, work, problems):
    seed = load_termbase(DEFAULT_DB)

    def check(name, condition, detail=""):
        if condition:
            out.write("PASS %s\n" % name)
        else:
            problems.append(name)
            out.write("FAIL %s%s\n" % (name, (": " + detail) if detail else ""))

    check("real-seed-schema", validate_schema(seed) == [],
          "the shipped database must validate")

    # corruption battery: one mutation per vector, each must be flagged
    mutations = []
    mutated = copy.deepcopy(seed)
    mutated["schema"] = "rocqwash-termbase-seed/0"
    mutations.append(("schema-string-drift", mutated))
    mutated = copy.deepcopy(seed)
    mutated["entries"][0]["extra_key"] = 1
    mutations.append(("entry-key-drift", mutated))
    mutated = copy.deepcopy(seed)
    mutated["entries"][1]["id"] = mutated["entries"][0]["id"]
    mutations.append(("duplicate-id", mutated))
    mutated = copy.deepcopy(seed)
    first_table = seed["entries"][0]["sub_table"]
    for entry in mutated["entries"]:
        if entry["sub_table"] == first_table:
            entry["row_index"] = 5
            break
    mutations.append(("row-index-break", mutated))
    mutated = copy.deepcopy(seed)
    mutated["meta"]["entry_count"] = mutated["meta"]["entry_count"] + 1
    mutations.append(("meta-count-drift", mutated))
    for name, mutated_seed in mutations:
        check("corruption-" + name, validate_schema(mutated_seed) != [],
              "the mutation must draw a named problem")

    check("lookup-single-face", [e["id"] for e in lookup("机检", seed)] == ["round2-r01"])
    check("lookup-multi-face",
          "round2-r04" in [e["id"] for e in lookup("钉定", seed)])
    check("lookup-arrow-chain",
          "round4-r02" in [e["id"] for e in lookup("分离窗口级", seed)])
    check("lookup-shared-term",
          {e["id"] for e in lookup("无前提闭式定理", seed)} == {"intl-r01"})
    check("lookup-second-table-face",
          {e["id"] for e in lookup("零前提闭式", seed)} == {"round2-r07"})
    check("lookup-miss-is-data", lookup("词语不在册", seed) == [])

    one = render(lookup_report("机检", "db", lookup("机检", seed)))
    two = render(lookup_report("机检", "db", lookup("机检", seed)))
    check("determinism", one == two, "identical inputs must render identically")

    check("exit-missing-db",
          main(["--lookup", "机检", "--db", os.path.join(work, "absent.json")]) == 9)
    check("exit-usage-no-mode", main([]) == 2)
    check("exit-usage-two-modes",
          main(["--lookup", "机检", "--schema-check"]) == 2)
    broken = os.path.join(work, "broken.json")
    write_output(broken, "{ not json")
    check("exit-malformed-db",
          main(["--lookup", "机检", "--db", broken]) == 1)

    source = io.open(__file__, "r", encoding="utf-8").read()
    import ast
    net_modules = {"socket", "urllib", "urllib2", "http", "requests",
                   "ftplib", "telnetlib", "smtplib", "asyncio"}
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    net_imports = sorted(imported & net_modules)
    check("zero-network-import-face", not net_imports,
          "network imports found: %s" % net_imports)


# ---------- CLI ----------

def usage(parser, message):
    sys.stderr.write("termbase: %s\n" % message)
    parser.print_usage(sys.stderr)
    return 2


def main(argv=None):
    # stream faces are UTF-8 by contract; the console codepage on Windows
    # hosts must not gate what a report may carry
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    parser = argparse.ArgumentParser(
        prog="termbase.py",
        description="offline terminology lookup thin layer over the E3 seed "
                    "(read-only, schema fail-loud, zero network)")
    parser.add_argument("--lookup", metavar="TERM",
                        help="look TERM up against the current-term faces")
    parser.add_argument("--schema-check", action="store_true",
                        help="validate the database schema only")
    parser.add_argument("--selftest", action="store_true",
                        help="run the selftest vectors")
    parser.add_argument("--db", default=DEFAULT_DB, metavar="P",
                        help="database path (default: the built-in seed)")
    parser.add_argument("--json", default=None, metavar="P",
                        help="write the report to P instead of stdout")
    args = parser.parse_args(argv)

    modes = [flag for flag, given in
             ((("--lookup", args.lookup is not None)),
              (("--schema-check", args.schema_check)),
              (("--selftest", args.selftest))) if given]
    if len(modes) != 1:
        return usage(parser, "exactly one of --lookup, --schema-check, "
                             "--selftest is required (got %s)"
                     % (", ".join(modes) or "none"))
    try:
        if args.selftest:
            return selftest(sys.stdout)
        seed = load_termbase(args.db)
        if args.schema_check:
            report = {"schema": LOOKUP_SCHEMA, "tool": TOOL,
                      "mode": "schema-check", "db": args.db,
                      "entry_count": len(seed["entries"]),
                      "problems": []}
            text = render(report)
            if args.json:
                write_output(args.json, text)
            else:
                sys.stdout.write(text)
            return 0
        hits = lookup(args.lookup, seed)
        text = render(lookup_report(args.lookup, args.db, hits))
        if args.json:
            write_output(args.json, text)
        else:
            sys.stdout.write(text)
        return 0
    except TermbaseError as exc:
        sys.stderr.write("termbase: %s\n" % exc)
        return 9 if exc.kind == "missing" else 1


if __name__ == "__main__":
    sys.exit(main())
