#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jargon_map_sync.py - sync the md jargon mapping table into the seed map.

Purpose.  Deterministic one-way sync from docs/jargon-to-standard-mapping-v1.md
  (the detector map, curated superset) into seeds/jargon/jargon-map.json (the
  apply map, schema rocqwash-jargon-map/1), closing the two-source drift: the
  detector table knows every mapped face, the apply map must know the same
  set.  A md row is admitted only when its standard cell derives to a single
  form - parenthetical annotations stripped (the fullwidth RE_FW_PAREN rule,
  then the md tool track's ASCII-paren English-cell convention), an em-dash
  head integration as rewrite_or_delete, and a derived form containing " / "
  or "U+FF0F" rejected as an alternation guard - and its context note carries
  none of the six guard markers ("guarded row", "per-row handling",
  "sense split", "splits the sense", "rules the face out",
  "narrative sense only").  The md
  tool track's em-dash standard cells ("- (delete ...)") are its
  rewrite-or-delete convention: they land as disposition rewrite_or_delete
  with no fixed standard (never machine-applied), the same bucket the seed
  uses for such rows.  Every row the sync writes is tagged with the in-repo
  derivation source (in-repo-md-v1) - the transcription contract's second
  containment source: those entries are checked against this very table by
  the same derivation rule, a check that runs on every machine because the
  table is a repository face.  An admitted face that is new appends one entry
  after the seed prefix in md document order; an admitted face that already
  exists with an equal standard is retagged from the legacy tool-track style
  to the in-repo source (action retagged - the re-admission mark of the
  in-repo-md-v1 contract); an admitted face that already exists with a
  differing standard updates standard, standard_language, standard_source,
  source_line and note in place - the curated superset supersedes - while
  the entry's id, face, exempts, disposition and cross_track_note are
  preserved verbatim.  One authority rule bounds the supersede: an existing
  entry whose standard_language is zh is a whitepaper-track transcription
  (the register authority) and is never machine-superseded - the row is
  reported authority-kept and left byte-identical; the four diverged
  originals J012/J046/J061/J098 carry their whitepaper-verbatim standards on
  the original tool-track tag under this rule, machine-apply stays guarded
  for them (note guards and the alternation guard), and the md keeps the
  single-form suggestions, so detector and applier may differ on those
  guarded faces until the register owner updates the whitepaper.  Every
  existing entry survives the sync and the count label stays exact
  (count == len(entries)).  Plan is the default and writes nothing; only
  --apply writes the map.

Interface.  python3 tools/jargon_map_sync.py [--md P] [--map P] [--apply]
  [--json P] [--selftest].  Report schema rocqwash-jargon-map-sync/1; the
  report carries one row per parsed md face (appended / updated / unchanged /
  retagged / authority-kept / rejected with the reason), the admit counts,
  and the resulting entry total.

Dependencies.  Python 3 standard library only; tools/norm_lint.py is loaded
  by path as the same-source RE_FW_PAREN and loader-grammar provider (absent
  module exits 9); seeds/jargon/SPEC.md is the schema contract text.  The
  row grammar mirrors tools/norm_lint.py:load_jargon_map (face cell: fullwidth
  parentheticals stripped, then split on "/" and "U+FF0F"; header/dash rows
  skipped; malformed rows fail loud).  Zero network face.

Evidence.  --selftest: filter vectors on fixture tables (single-form admit
  with annotation stripping, slash and fullwidth-slash alternation rejects,
  each of the six note-guard rejects, the em-dash rewrite-or-delete admit,
  upsert preserving id/exempts/cross_track_note, the in-repo source tag on
  every written row, the equal-row retag to the in-repo source, the zh
  authority-kept refusal, append with the next id and the tool-track source
  style, exact count label, byte-identical rerun, duplicate admitted face
  refusal, unreadable/absent input exit 9).

Exit-codes.  0 clean plan or a written sync; 1 admit findings listed in plan
  mode or a failed selftest vector or a duplicate admitted face; 2 usage;
  9 missing input (map or md table absent/unreadable).
"""

import argparse
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile

SCHEMA = "rocqwash-jargon-map-sync/1"
MAP_SCHEMA = "rocqwash-jargon-map/1"
TOOL = "jargon_map_sync"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MD_PATH = os.path.join(REPO_ROOT, "docs",
                               "jargon-to-standard-mapping-v1.md")
DEFAULT_MAP_PATH = os.path.join(REPO_ROOT, "seeds", "jargon", "jargon-map.json")
NL_PATH = os.path.join(REPO_ROOT, "tools", "norm_lint.py")

# standard_source style of the tool-repository track (the in-repo md table),
# verbatim from the seed's existing tool-track entries
TOOL_TRACK_SOURCE = ("rocqwash docs/jargon-to-standard-mapping-v1.md"
                     " (tool-repository track)")

# the in-repo derivation source (the in-repo-md-v1 contract): every row the sync
# writes or owns carries this tag; it deliberately extends the tool-track
# prefix above so tools/jargon_apply.py's A2 md-row gate keeps scoping every
# admitted row, while the transcription check can tell the sync's product
# (in-repo-md-v1, containment = the paren-stripped md cell by the derivation
# rule below) from the original tool-track transcriptions (containment = the
# pinned whitepaper)
IN_REPO_SOURCE = ("rocqwash docs/jargon-to-standard-mapping-v1.md"
                  " (in-repo-md-v1)")

# note markers that keep a row out of the apply map (seed SPEC section 3
# guard families, same list tools/jargon_apply.py enforces on the loaded map)
NOTE_GUARD_MARKERS = ("guarded row", "per-row handling", "sense split",
                      "splits the sense", "rules the face out",
                      "narrative sense only")

# the md tool track's rewrite-or-delete marker: a standard cell whose
# derived form opens with the em-dash carries no fixed standard
EM_DASH = "\u2014"

_NL = None


def fail(msg, code):
    sys.stderr.write(TOOL + ": " + msg + "\n")
    raise SystemExit(code)


def norm_lint_module():
    """Load tools/norm_lint.py by path (same-source RE_FW_PAREN provider)."""
    global _NL
    if _NL is None:
        if not os.path.isfile(NL_PATH):
            fail("detector module missing (same-source dependency): " + NL_PATH,
                 9)
        spec = importlib.util.spec_from_file_location("rqw_norm_lint_sync",
                                                      NL_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _NL = mod
    return _NL


def note_guard_reason(note):
    """The guard marker a note carries, or None when the note is clean."""
    low = (note or "").lower()
    for marker in NOTE_GUARD_MARKERS:
        if marker in low:
            return marker
    return None


# ASCII-parenthetical annotation form: the md tool track's English cells use
# halfwidth parens for the same annotation device the whitepaper track spells
# with fullwidth parens (sense qualifiers and process instructions such as
# "batch (process sense)" or "handoff (process narration - delete, state
# facts)") - annotations, never literal replacement text
RE_ASCII_PAREN = re.compile(r"\([^)]*\)")


def derive_standard(cell):
    """Derive the standard cell of one md row.

    Returns (disposition, standard, reject_reason):
      disposition "replace" with the derived single form, or
      "rewrite_or_delete" with standard None for the em-dash cells, or
      (None, None, reason) when the row is not admissible.
    The derivation strips parenthetical annotations first - the fullwidth
    form (norm_lint RE_FW_PAREN, the whitepaper-track convention) and then
    the ASCII form (the md tool track's English-cell convention; both carry
    guards, sense qualifiers and process instructions, never literal
    replacement text).  On the stripped form: an em-dash head is the md's
    rewrite-or-delete convention and lands in the never-applied bucket; a
    surviving " / " or fullwidth "U+FF0F" is an alternation guard and the row
    is rejected (the alternation guard of tools/jargon_apply.py:derive_after).
    """
    fw = norm_lint_module().RE_FW_PAREN
    bare = fw.sub("", cell or "")
    bare = RE_ASCII_PAREN.sub("", bare).strip()
    if not bare:
        return None, None, "empty-standard"
    if bare.startswith(EM_DASH):
        return "rewrite_or_delete", None, None
    if " / " in bare or "\uFF0F" in bare:
        return None, None, "alternation-guard"
    return "replace", bare, None


def parse_md_rows(path):
    """Loader-grammar rows of the md table: one record per derived face.

    Row shape mirrors tools/norm_lint.py:load_jargon_map: the face cell is
    fullwidth-parenthetical-stripped then split on "/" and "U+FF0F"; rows whose
    first cell is empty, carries the CJK header marker, or is a dash run are
    skipped; a data row needs three cells (face, standard, note).  Each
    record: {face, standard_cell, note, line}.  Duplicate derived faces fail
    loud (the loader rejects duplicates, exit 1)."""
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            rows = fh.read().splitlines()
    except OSError as exc:
        fail("md table unreadable: " + path + " (" + str(exc) + ")", 9)
    out = []
    seen = {}
    for lineno, raw in enumerate(rows, 1):
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        first = cells[0] if cells else ""
        if not first or "\u9ED1\u8BDD" in first or set(first) <= set("- "):
            continue
        if len(cells) < 3:
            fail("malformed md table row at %s:%d (need face|standard|note)"
                 % (path, lineno), 1)
        fw = norm_lint_module().RE_FW_PAREN
        face = fw.sub("", first).strip()
        note = cells[2]
        for part in re.split(r"\uFF0F|/", face):
            name = part.strip()
            if not name:
                continue
            if name in seen:
                fail("duplicate derived face %r at %s:%d (first at line %d);"
                     " the loader rejects duplicate faces"
                     % (name, path, lineno, seen[name]), 1)
            seen[name] = lineno
            out.append({"face": name, "standard_cell": cells[1],
                        "note": note, "line": lineno})
    return out


def load_map(path):
    """Read and validate the seed map JSON; fail loud, never silently."""
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        fail("jargon map unreadable: " + path + " (" + str(exc) + ")", 9)
    try:
        m = json.loads(raw)
    except ValueError as exc:
        fail("jargon map is not valid JSON: " + path + " (" + str(exc) + ")",
             9)
    if not isinstance(m, dict) or m.get("schema") != MAP_SCHEMA:
        fail("jargon map schema mismatch in " + path, 1)
    ents = m.get("entries")
    if not isinstance(ents, list) or not ents:
        fail("jargon map carries no entries: " + path, 1)
    seen = set()
    for e in ents:
        if not isinstance(e.get("id"), str) or not e["id"]:
            fail("entry without id in " + path, 1)
        if e["face"] in seen:
            fail("duplicate jargon face %r in " % e["face"] + path, 1)
        seen.add(e["face"])
    if isinstance(m.get("count"), int) and m["count"] != len(ents):
        fail("jargon map count label %r != %d entries"
             % (m.get("count"), len(ents)), 1)
    return m


def _next_id(entries):
    """The next J-number after the highest numeric suffix in the map."""
    top = 0
    for e in entries:
        m = re.match(r"^J(\d+)$", e.get("id") or "")
        if m:
            top = max(top, int(m.group(1)))
    return "J%03d" % (top + 1)


def sync_plan(md_rows):
    """Admission plan over the parsed md rows.

    One plan row per md face: action appended / updated / unchanged, or
    rejected with the filter reason (alternation-guard / empty-standard /
    note-guard:<marker>).  Entries are mutated only by sync_apply; this
    function is read-only."""
    rows = []
    for r in md_rows:
        disp, derived, reason = derive_standard(r["standard_cell"])
        if reason is None:
            reason = note_guard_reason(r["note"])
            if reason is not None:
                reason = "note-guard:" + reason
        rows.append(dict(r, disposition=disp, derived=derived,
                         reject=reason))
    return rows


def sync_apply(m, plan):
    """Apply the admission plan to the loaded map dict (in place).

    Rejected rows touch nothing.  An admitted face that already exists with
    an equal standard is retagged to the in-repo derivation source when its
    tag is the legacy tool-track style (action retagged, no other field
    touched); an equal row already carrying the in-repo source is unchanged.
    An admitted face whose existing entry carries a zh standard is a
    whitepaper-track transcription (the register authority): reported
    authority-kept and never machine-superseded.  Otherwise an admitted
    existing face updates standard / standard_language / standard_source /
    source_line / note in place (id, face, exempts, disposition,
    cross_track_note preserved) with the in-repo source tag; an admitted new
    face appends one entry in md document order with the next J-number and
    the in-repo source tag.  Returns the plan with per-row actions."""
    by_face = dict((e["face"], e) for e in m["entries"])
    for row in plan:
        if row["reject"] is not None:
            row["action"] = "rejected"
            continue
        face = row["face"]
        disp = row["disposition"]
        entry = by_face.get(face)
        if entry is not None:
            if entry.get("disposition") != disp:
                fail("admitted %s row for face %r conflicts with the existing"
                     " %s entry %s; refusing"
                     % (disp, face, entry.get("disposition"),
                        entry.get("id")), 1)
            # a matching entry is untouched (the curated superset only
            # supersedes a DIFFERING standard): replace rows compare the
            # standard cell, rewrite_or_delete rows carry no standard at all
            already = (entry.get("standard") == row["derived"]
                       if disp == "replace"
                       else entry.get("standard") is None)
            if already:
                if entry.get("standard_source") == TOOL_TRACK_SOURCE:
                    # the re-admission mark: the row is the sync's product,
                    # so its provenance moves to the in-repo derivation tag
                    entry["standard_source"] = IN_REPO_SOURCE
                    row["action"] = "retagged"
                else:
                    row["action"] = "unchanged"
                row["entry_id"] = entry["id"]
                continue
            if entry.get("standard_language") == "zh":
                # whitepaper-track authority row: the register decision lives
                # in the whitepaper, not in this mechanical derivation; the
                # md keeps its single-form suggestion and the two faces may
                # differ on such guarded rows until the register owner
                # updates the whitepaper
                row["action"] = "authority-kept"
                row["entry_id"] = entry["id"]
                continue
            entry["standard"] = row["derived"]
            entry["standard_language"] = "en" if disp == "replace" else None
            entry["standard_source"] = IN_REPO_SOURCE
            entry["source_line"] = row["line"]
            entry["note"] = row["note"]
            row["action"] = "updated"
            row["entry_id"] = entry["id"]
            continue
        entry = {
            "id": _next_id(m["entries"]),
            "face": face,
            "standard": row["derived"],
            "standard_language": "en" if disp == "replace" else None,
            "standard_source": IN_REPO_SOURCE,
            "source_line": row["line"],
            "disposition": disp,
            "exempts": [],
            "cross_track_note": None,
            "note": row["note"],
        }
        m["entries"].append(entry)
        by_face[face] = entry
        row["action"] = "appended"
        row["entry_id"] = entry["id"]
    m["count"] = len(m["entries"])
    return plan


def write_map(path, m):
    """Serialize the map byte-stably: the file's own key order, indent 2,
    ensure_ascii off, trailing newline."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(m, ensure_ascii=False, indent=2) + "\n")


def run_sync(args):
    mode = "apply" if args.apply else "plan"
    if not os.path.isfile(args.md):
        fail("md table not found: " + args.md, 9)
    if not os.path.isfile(args.map):
        fail("jargon map not found: " + args.map, 9)
    m = load_map(args.map)
    entries_before = len(m["entries"])
    before = json.dumps(m, ensure_ascii=False, indent=2) + "\n"
    md_rows = parse_md_rows(args.md)
    plan = sync_plan(md_rows)
    sync_apply(m, plan)
    counts = {}
    for row in plan:
        counts[row["action"]] = counts.get(row["action"], 0) + 1
    wrote = False
    if mode == "apply":
        after = json.dumps(m, ensure_ascii=False, indent=2) + "\n"
        if after != before:
            write_map(args.map, m)
            wrote = True
    report = {
        "schema": SCHEMA, "tool": TOOL, "mode": mode,
        "md": os.path.abspath(args.md),
        "map": os.path.abspath(args.map),
        "md_rows_parsed": len(md_rows),
        "entries_before": entries_before,
        "entries_after": len(m["entries"]),
        "count_label": m["count"],
        "actions": counts,
        "rows": [{k: row.get(k) for k in
                  ("face", "line", "disposition", "derived", "reject",
                   "action", "entry_id", "standard_cell")}
                 for row in plan],
    }
    if args.json:
        parent = os.path.dirname(os.path.abspath(args.json))
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(report, ensure_ascii=False, indent=1,
                                sort_keys=True) + "\n")
    print("%s %s: mode=%s md_faces=%d appended=%d updated=%d unchanged=%d"
          " retagged=%d authority_kept=%d rejected=%d entries=%d count=%d"
          " wrote=%s"
          % (TOOL, SCHEMA, mode, len(md_rows),
             counts.get("appended", 0), counts.get("updated", 0),
             counts.get("unchanged", 0), counts.get("retagged", 0),
             counts.get("authority-kept", 0), counts.get("rejected", 0),
             len(m["entries"]), m["count"], str(wrote).lower()))
    for row in plan:
        if row["action"] == "rejected":
            print("  rejected %s (md line %d): %s"
                  % (row["face"], row["line"], row["reject"]))
        elif row["action"] == "authority-kept":
            print("  authority-kept %s (md line %d, entry %s): the existing"
                  " zh standard is a whitepaper-track transcription and is"
                  " never machine-superseded"
                  % (row["face"], row["line"], row["entry_id"]))
        elif row["action"] == "retagged":
            print("  retagged %s -> in-repo source (md line %d, entry %s)"
                  % (row["face"], row["line"], row["entry_id"]))
        elif row["action"] == "updated":
            print("  updated %s -> %s %s (md line %d, entry %s)"
                  % (row["face"], row["disposition"], row["derived"],
                     row["line"], row["entry_id"]))
        elif row["action"] == "appended":
            print("  appended %s -> %s %s (md line %d, entry %s)"
                  % (row["face"], row["disposition"], row["derived"],
                     row["line"], row["entry_id"]))
    if mode == "plan":
        changed = (counts.get("appended", 0) + counts.get("updated", 0)
                   + counts.get("retagged", 0))
        print("VERDICT " + ("PENDING" if changed else "IN-SYNC")
              + " (plan is zero-write)")
        return 1 if changed else 0
    print("VERDICT SYNCED (count label exact: %d == %d entries)"
          % (m["count"], len(m["entries"])))
    return 0


# --- selftest vectors (in-process, temporary fixtures, standalone) ---

FX_MD = "\n".join([
    "# fixture mapping table (tmp only)",
    "",
    "| \u9ED1\u8BDD (jargon face) | \u6807\u51C6 (standard expression)"
    " | \u8BED\u5883\u6CE8\u8BB0 (context note) |",
    "|---|---|---|",
    "| \u6253\u5305 | \u5c01\u88c5\uff08\u5408\u53d6\u8bed\u5883\u53ef\u5199"
    "\u5408\u53d6\u5c01\u88c5\uff09 | plain row with a fullwidth annotation."
    " 1 file. |",
    "| \u76d8\u70b9 | keep / drop | alternation-guard standard. 1 file. |",
    "| \u5bf9\u62cd | \u5168\u5bbd\uff0f\u5f62 | fullwidth-slash"
    " alternation. 1 file. |",
    "| \u7ea2\u7ebf | non-negotiable constraint | guarded row note. 1 file. |",
    "| \u94c1\u5f8b | invariant | per-row handling note. 1 file. |",
    "| \u56de\u6f6e | regression | sense split note. 1 file. |",
    "| \u65b0\u4f24 | newly introduced issue | splits the sense note."
    " 1 file. |",
    "| \u60ac\u7a7a | dangling reference | rules the face out note."
    " 1 file. |",
    "| \u76f4\u6392 | reorganize | narrative sense only note. 1 file. |",
    "| \u953b\u9020 | construct | clean note, admitted. 1 file. |",
    "| \u4ea4\u68d2 | \u2014 (delete the narration) | em-dash convention row."
    " 1 file. |",
    "| seat | agent | clean English row. 1 file. |",
    "| \u94fe\u6761 | evidence chain | seed twin, standard differs."
    " 1 file. |",
    "| \u80fd\u91cf | unchanged form | seed twin, standard equal. 1 file. |",
    "| \u6e05\u76d8 | liquidated | zh authority twin, admitted md row."
    " 1 file. |",
]) + "\n"

FX_MAP = {
    "schema": MAP_SCHEMA, "engine": "jargon",
    "seed_role": "fixture map for the sync selftest",
    "face_language": "zh",
    "count": 3,
    "selection_rule": "fixture",
    "boundary_note": "fixture",
    "provenance": {"sources": []},
    "entries": [
        {"id": "J001", "face": "\u94fe\u6761",
         "standard": "old chain form",
         "standard_language": "en",
         "standard_source": TOOL_TRACK_SOURCE,
         "source_line": 12, "disposition": "replace", "exempts": ["\u4e3b\u94fe"],
         "cross_track_note": "glossary quote preserved",
         "note": "older tool-track transcription, standard differs"},
        {"id": "J002", "face": "\u80fd\u91cf",
         "standard": "unchanged form", "standard_language": "en",
         "standard_source": TOOL_TRACK_SOURCE, "source_line": 99,
         "disposition": "replace", "exempts": [], "cross_track_note": None,
         "note": "already in sync"},
        {"id": "J003", "face": "\u6e05\u76d8",
         "standard": "\u6e05\u7b97", "standard_language": "zh",
         "standard_source": TOOL_TRACK_SOURCE, "source_line": 101,
         "disposition": "replace", "exempts": [], "cross_track_note": None,
         "note": "whitepaper-track authority row on the tool-track tag"},
    ],
}

GUARD_NOTES = ("guarded row", "per-row handling", "sense split",
               "splits the sense", "rules the face out",
               "narrative sense only")


def _vec(results, name, ok, detail):
    results.append((name, bool(ok), detail))


def _write(tmp, rel, text):
    path = os.path.join(tmp, rel)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def _run_sync_apply(md_path, map_path):
    """In-process apply over fixture files; returns (report dict, rc)."""
    m = load_map(map_path)
    before = json.dumps(m, ensure_ascii=False, indent=2) + "\n"
    plan = sync_apply(m, sync_plan(parse_md_rows(md_path)))
    after = json.dumps(m, ensure_ascii=False, indent=2) + "\n"
    report = {"before": before, "after": after, "plan": plan, "map": m}
    return report, 0


def run_selftest(args):
    results = []
    tmp = tempfile.mkdtemp(prefix="rqw_jargon_sync_")
    try:
        # vector 1: single-form admit strips the fullwidth annotation
        md1 = _write(tmp, "md1.md", "\n".join([
            "| \u9ED1\u8BDD (jargon face) | s | n |",
            "|---|---|---|",
            "| \u6253\u5305 | \u5c01\u88c5\uff08\u8bed\u5883\u6ce8\u8bb0"
            "\uff09 | clean note. 1 file. |",
            "| \u6d17 | \u6d88\u6bd2 / \u6e05\u6d01 | slash reject."
            " 1 file. |",
            "| \u6279\u6b21 | batch (process sense) | ascii-paren"
            " annotation stripped. 1 file. |",
            "| \u5bf9\u62cd | \u5168\u5bbd\uff0f\u5f62"
            " | fullwidth-slash reject. 1 file. |",
        ]) + "\n")
        rows = parse_md_rows(md1)
        plan = sync_plan(rows)
        by = dict((r["face"], r) for r in plan)
        ok = (by["\u6253\u5305"]["reject"] is None
              and by["\u6253\u5305"]["derived"] == "\u5c01\u88c5"
              and by["\u6253\u5305"]["disposition"] == "replace"
              and by["\u6d17"]["reject"] == "alternation-guard"
              and by["\u5bf9\u62cd"]["reject"] == "alternation-guard"
              and by["\u6279\u6b21"]["derived"] == "batch")
        _vec(results, "filter-single-form-and-alternation", ok,
             "fullwidth and ascii paren annotations stripped to the single"
             " form; both slash forms rejected" if ok else "plan=%r" % plan)

        # vector 2: each of the six note-guard markers rejects its row
        bad = []
        for i, marker in enumerate(GUARD_NOTES):
            md2 = _write(tmp, "guard%d.md" % i, "\n".join([
                "| \u9ED1\u8BDD (jargon face) | s | n |",
                "|---|---|---|",
                "| face%d | some standard | note carries %s. 1 file. |"
                % (i, marker),
            ]) + "\n")
            plan = sync_plan(parse_md_rows(md2))
            row = plan[0]
            if not (row["reject"] or "").startswith("note-guard:") \
                    or marker not in (row["reject"] or ""):
                bad.append(marker)
        _vec(results, "filter-note-guards", not bad,
             "all six guard markers reject their rows"
             if not bad else "unrejected markers: %s" % ", ".join(bad))

        # vector 3: em-dash cells land as rewrite_or_delete, standard None
        md3 = _write(tmp, "md3.md", "\n".join([
            "| \u9ED1\u8BDD (jargon face) | s | n |",
            "|---|---|---|",
            "| \u4ea4\u68d2 | \u2014 (delete the narration) | process"
            " narration; state facts instead. |",
        ]) + "\n")
        plan = sync_plan(parse_md_rows(md3))
        row = plan[0]
        ok = (row["reject"] is None
              and row["disposition"] == "rewrite_or_delete"
              and row["derived"] is None)
        _vec(results, "em-dash-rewrite-or-delete", ok,
             "the md delete convention lands in the never-applied bucket"
             if ok else "plan=%r" % plan)

        # vector 4: full sync over the fixture map - append, upsert, retag,
        # authority-kept, count label exact, preserve id/exempts/cross_track
        md_path = _write(tmp, "fx.md", FX_MD)
        map_path = _write(tmp, "fx-map.json",
                          json.dumps(FX_MAP, ensure_ascii=False,
                                     indent=2) + "\n")
        report, _rc = _run_sync_apply(md_path, map_path)
        m = report["map"]
        ents = dict((e["face"], e) for e in m["entries"])
        acts = dict((r["face"], r["action"]) for r in report["plan"])
        link = ents["\u94fe\u6761"]
        power = ents["\u80fd\u91cf"]
        qing = ents["\u6e05\u76d8"]
        ok = (m["count"] == len(m["entries"]) == 7
              and link["id"] == "J001" and link["standard"] == "evidence chain"
              and link["standard_language"] == "en"
              and link["standard_source"] == IN_REPO_SOURCE
              and link["exempts"] == ["\u4e3b\u94fe"]
              and link["cross_track_note"] == "glossary quote preserved"
              and power["standard_source"] == IN_REPO_SOURCE
              and power["note"] == "already in sync"
              and power["source_line"] == 99
              and acts["\u80fd\u91cf"] == "retagged"
              and qing["standard"] == "\u6e05\u7b97"
              and qing["standard_language"] == "zh"
              and qing["standard_source"] == TOOL_TRACK_SOURCE
              and qing["source_line"] == 101
              and qing["note"] == "whitepaper-track authority row on the"
                                  " tool-track tag"
              and acts["\u6e05\u76d8"] == "authority-kept"
              and ents["\u6253\u5305"]["id"] == "J004"
              and ents["\u6253\u5305"]["standard"] == "\u5c01\u88c5"
              and ents["\u6253\u5305"]["standard_source"] == IN_REPO_SOURCE
              and ents["seat"]["id"] == "J007"
              and ents["seat"]["standard"] == "agent"
              and ents["\u4ea4\u68d2"]["disposition"] == "rewrite_or_delete"
              and ents["\u4ea4\u68d2"]["standard"] is None
              and ents["\u94fe\u6761"]["note"] == "seed twin, standard"
                                            " differs. 1 file.")
        _vec(results, "sync-append-upsert-retag-authority", ok,
             "append J004..J007, upsert J001 and retag the equal J002 to the"
             " in-repo source with id, exempts and cross_track_note"
             " preserved, zh authority twin J003 never superseded, count"
             " label exact (7)"
             if ok else "entries=%r plan=%r" % (m["entries"], report["plan"]))

        # vector 5: the sync is deterministic and byte-identical on rerun
        first = json.dumps(m, ensure_ascii=False, indent=2) + "\n"
        m2 = json.loads(first)
        plan2 = sync_plan(parse_md_rows(md_path))
        sync_apply(m2, plan2)
        second = json.dumps(m2, ensure_ascii=False, indent=2) + "\n"
        acts = dict((r["face"], r["action"]) for r in plan2)
        ok = first == second and acts["\u94fe\u6761"] == "unchanged" \
            and acts["\u80fd\u91cf"] == "unchanged" \
            and acts["\u6e05\u76d8"] == "authority-kept"
        _vec(results, "rerun-byte-identical", ok,
             "second sync is a byte-identical no-op with unchanged and"
             " authority-kept actions"
             if ok else "rerun drifted")

        # vector 6: duplicate derived face fails loud (exit 1)
        dup_md = "\n".join([
            "| \u9ED1\u8BDD (jargon face) | s | n |",
            "|---|---|---|",
            "| twin / \u540c\u8bcd | one standard | first. |",
            "| \u540c\u8bcd | other standard | second. |",
        ]) + "\n"
        dup_path = _write(tmp, "dup.md", dup_md)
        code = 0
        try:
            parse_md_rows(dup_path)
        except SystemExit as exc:
            code = getattr(exc, "code", None)
        _vec(results, "duplicate-face-refused", code == 1,
             "duplicate derived face exits 1 (loader contract)"
             if code == 1 else "rc=%r" % code)

        # vector 7: CLI plan mode is zero-write and exits 1 when pending
        live_map = os.path.join(tmp, "live-map.json")
        shutil.copyfile(map_path, live_map)
        digest0 = io.open(live_map, "rb").read()
        proc = subprocess_run([sys.executable, "-I", "-X", "utf8",
                               os.path.abspath(__file__), "--map", live_map,
                               "--md", md_path])
        digest1 = io.open(live_map, "rb").read()
        ok = proc.returncode == 1 and digest1 == digest0
        _vec(results, "cli-plan-zero-write", ok,
             "plan mode exits 1 pending and writes zero bytes"
             if ok else "rc=%d wrote=%s" % (proc.returncode,
                                            digest1 != digest0))

        # vector 8: CLI --apply writes; a second --apply is a no-op rc 0
        proc = subprocess_run([sys.executable, "-I", "-X", "utf8",
                               os.path.abspath(__file__), "--map", live_map,
                               "--md", md_path, "--apply"])
        digest2 = io.open(live_map, "rb").read()
        ok1 = proc.returncode == 0 and digest2 != digest0
        proc = subprocess_run([sys.executable, "-I", "-X", "utf8",
                               os.path.abspath(__file__), "--map", live_map,
                               "--md", md_path, "--apply"])
        digest3 = io.open(live_map, "rb").read()
        ok = ok1 and proc.returncode == 0 and digest3 == digest2
        _vec(results, "cli-apply-idempotent", ok,
             "apply writes once, second apply is a byte-identical no-op"
             if ok else "rc=%d stable=%s" % (proc.returncode,
                                             digest3 == digest2))

        # vector 9: missing inputs exit 9
        code = 0
        try:
            load_map(os.path.join(tmp, "absent.json"))
        except SystemExit as exc:
            code = getattr(exc, "code", None)
        _vec(results, "missing-input-exit-9", code == 9,
             "absent map file exits 9" if code == 9 else "rc=%r" % code)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = 0
    for name, ok, detail in results:
        if ok:
            tag = "PASS"
        else:
            tag = "FAIL"
            failed += 1
        print("%s %s - %s" % (tag, name, detail))
    print("summary: %d vectors, %d FAIL" % (len(results), failed))
    if failed:
        print("SYNC-SELFTEST RED (%d)" % failed)
        return 1
    print("SYNC-SELFTEST PASS")
    return 0


def subprocess_run(cmd):
    """Subprocess helper for the CLI vectors (offline, tmp fixtures)."""
    import subprocess
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)


def main(argv=None):
    ap = argparse.ArgumentParser(prog=TOOL)
    ap.add_argument("--md", metavar="P", default=DEFAULT_MD_PATH,
                    help="source md mapping table (detector map)")
    ap.add_argument("--map", metavar="P", default=DEFAULT_MAP_PATH,
                    help="target seed map JSON (written only by --apply)")
    ap.add_argument("--apply", action="store_true",
                    help="write the synced map (default is a zero-write plan)")
    ap.add_argument("--json", metavar="P",
                    help="write the report JSON there")
    ap.add_argument("--selftest", action="store_true",
                    help="run the selftest vectors; standalone")
    args = ap.parse_args(argv)
    if args.selftest:
        if args.apply or args.json \
                or args.md != DEFAULT_MD_PATH or args.map != DEFAULT_MAP_PATH:
            fail("--selftest runs standalone; combine it with no scan flags", 2)
        return run_selftest(args)
    return run_sync(args)


if __name__ == "__main__":
    sys.exit(main())
