"""Seed schema assertions for the termbase engine (E3, RQW12 seeds delivery).

Purpose.  Assert the schema and integrity invariants of the built-in
  termbase seed: JSON parse face, entry skeleton consistency, verbatim
  transcription checks against the source glossary when that file is
  reachable locally, three unfetched domain slots carrying no content
  payload, ASCII (English) key register, recorded source-of-truth
  snapshot identity, and the zero-engine-body purity of the seed
  directory.
Interface.  Pytest-compatible test functions (no side effects at
  import).  Also runnable standalone: `python test_snippet.py` prints
  one PASS/FAIL line per check and exits 0 on success, 1 on failure.
  This file is the merge segment for tests/t_engines_seeds.py; the
  tests agent assembles the combined file.
Dependencies.  Python 3 standard library only.  Seed files are located
  by walking up from this file (a sibling termbase.json or an ancestor
  seeds/termbase/ directory), overridable with ROCQWASH_SEEDS_DIR.
Evidence.  Run standalone in the staging tree, all checks PASS; with
  the source glossary present, the transcription checks execute for
  real (full cell-by-cell comparison against the recorded snapshot
  hash identity).
Exit-codes.  0 accounted; 1 failure (standalone mode).
"""
import hashlib
import io
import json
import os
import re
import sys

SCHEMA = "rocqwash-termbase-seed/1"
TOOL = "termbase"
EXPECTED_SLOT_IDS = ["mathlib-naming-convention", "lean-style-guide",
                     "journal-style"]
SLOT_ALLOWED_KEYS = {"id", "title", "status", "source", "refresh_conditions",
                     "content"}
ENTRY_ALLOWED_KEYS = {"id", "sub_table", "row_index", "cells"}
SUB_TABLE_ORDER = ["round2", "intl", "round3", "round4"]
SEED_DIR_FILES = {"termbase.json", "net-interface-SPEC.md",
                  "diy-channel-SPEC.md", "test_snippet.py"}
KEY_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
ID_PATTERN = re.compile(r"^[a-z0-9]+-r[0-9]{2,}$")


def _seed_dir():
    env = os.environ.get("ROCQWASH_SEEDS_DIR")
    if env:
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    for _ in range(8):
        # three layouts: snippet inside seeds/termbase/, merged file in a
        # tests/ dir whose ancestor carries seeds/, repo root layouts
        for cand in (os.path.join(d, "termbase", "termbase.json"),
                     os.path.join(d, "seeds", "termbase", "termbase.json"),
                     os.path.join(d, "termbase.json")):
            if os.path.isfile(cand):
                return os.path.dirname(cand)
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    raise AssertionError("termbase seed directory not found from %s "
                         "(set ROCQWASH_SEEDS_DIR to override)" % here)


def _seed_path(name):
    return os.path.join(_seed_dir(), name)


def _load_seed():
    with io.open(_seed_path("termbase.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _source_bytes_if_present():
    """Raw bytes of the glossary source, or None when this host does not
    carry it (repo/CI faces may not mount the authoring machine paths)."""
    seed = _load_seed()
    path = seed["source_of_truth"]["path"]
    if os.path.isfile(path):
        with io.open(path, "rb") as fh:
            return fh.read()
    return None


# ---------- parse face ----------

def test_parse_face():
    seed = _load_seed()
    assert seed["schema"] == SCHEMA, seed.get("schema")
    assert seed["tool"] == TOOL, seed.get("tool")
    assert isinstance(seed["description"], str) and seed["description"]
    assert isinstance(seed["slots_policy"], str) and seed["slots_policy"]
    assert "candidate order" in seed["slots_policy"]


def test_source_of_truth_recorded():
    seed = _load_seed()
    sot = seed["source_of_truth"]
    assert sot["path"].endswith(".md")
    assert "glossary" in sot["role"] or "maintenance" in sot["role"]
    snap = sot["snapshot"]
    assert isinstance(snap["bytes"], int) and snap["bytes"] > 0
    assert re.match(r"^[0-9a-f]{64}$", snap["sha256"])
    assert re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T", snap["mtime_utc"])
    assert "read-only" in sot["snapshot_discipline"]
    assert sot["section"].startswith("### 4.0")


# ---------- skeleton and entries ----------

def test_entry_skeleton_declared():
    seed = _load_seed()
    sk = seed["entry_skeleton"]
    assert isinstance(sk["origin_verbatim"], str) and sk["origin_verbatim"]
    assert sk["origin_verbatim"].startswith("**")
    subs = sk["sub_tables"]
    assert sorted(subs.keys()) == sorted(SUB_TABLE_ORDER)
    for key, st in subs.items():
        cols = st["columns"]
        assert cols == st["header_verbatim"]
        assert st["column_count"] == len(cols) >= 3
        assert len(st["english_column_names"]) == len(cols)
        assert st["row_count"] >= 1
        assert isinstance(st["preamble_verbatim"], (str, type(None)))


def test_entries_shape():
    seed = _load_seed()
    subs = seed["entry_skeleton"]["sub_tables"]
    entries = seed["entries"]
    assert isinstance(entries, list) and entries
    ids = set()
    per_table = {}
    for e in entries:
        assert set(e.keys()) == ENTRY_ALLOWED_KEYS, sorted(e.keys())
        assert ID_PATTERN.match(e["id"]), e["id"]
        assert e["id"] not in ids, "duplicate id %s" % e["id"]
        ids.add(e["id"])
        st = e["sub_table"]
        assert st in subs, st
        assert isinstance(e["row_index"], int) and e["row_index"] >= 1
        cells = e["cells"]
        assert isinstance(cells, list) and cells
        assert all(isinstance(c, str) and c.strip() for c in cells)
        assert len(cells) <= subs[st]["column_count"], (e["id"], len(cells))
        per_table.setdefault(st, []).append(e["row_index"])
    for st, idxs in per_table.items():
        assert idxs == list(range(1, len(idxs) + 1)), \
            "%s row_index sequence broken" % st
        assert len(idxs) == subs[st]["row_count"], st


def test_irregular_rows_registered():
    """Rows whose source line carries fewer cells than its table header
    declares are transcribed verbatim and must be registered in meta."""
    seed = _load_seed()
    subs = seed["entry_skeleton"]["sub_tables"]
    irregular = {r["id"] for r in seed["meta"]["source_irregular_rows"]}
    for e in seed["entries"]:
        declared = subs[e["sub_table"]]["column_count"]
        if len(e["cells"]) < declared:
            assert e["id"] in irregular, \
                "short row %s not registered" % e["id"]
        else:
            assert e["id"] not in irregular, \
                "regular row %s wrongly registered" % e["id"]
    for r in seed["meta"]["source_irregular_rows"]:
        assert r["declared_columns"] == r["actual_cells"] + 1, r
        assert r["note"], r


def test_meta_counts_consistent():
    seed = _load_seed()
    meta = seed["meta"]
    assert meta["entry_count"] == len(seed["entries"])
    counts = {}
    for e in seed["entries"]:
        counts[e["sub_table"]] = counts.get(e["sub_table"], 0) + 1
    assert meta["sub_table_counts"] == counts, meta["sub_table_counts"]
    assert meta["prose_note_count"] == len(seed["prose_notes"])
    for n in seed["prose_notes"]:
        assert set(n.keys()) == {"label", "text_verbatim"}
        assert n["label"] and n["text_verbatim"].startswith("**")


# ---------- domain slots ----------

def test_domain_slots_three_unfetched():
    seed = _load_seed()
    slots = seed["domain_slots"]
    assert isinstance(slots, list) and len(slots) == 3
    assert [s["id"] for s in slots] == EXPECTED_SLOT_IDS
    for s in slots:
        assert set(s.keys()) <= SLOT_ALLOWED_KEYS, sorted(s.keys())
        assert s["status"] == "unfetched", (s["id"], s["status"])
        assert s["content"] is None, s["id"]
        assert "payload" not in s and "entries" not in s, s["id"]
        rc = s["refresh_conditions"]
        assert isinstance(rc, list) and rc
        assert all(isinstance(c, str) and c for c in rc)
        assert any("NETRED" in c or "user-ordered" in c for c in rc), s["id"]
        src = s["source"]
        assert isinstance(src, dict) and src


def test_slot_sources_declared_not_verified():
    """Unfetched means unfetched: declared sources carry no verified flag
    of true and the journal-style slot has no URL yet (venue pending)."""
    seed = _load_seed()
    by_id = {s["id"]: s for s in seed["domain_slots"]}
    for sid in ("mathlib-naming-convention", "lean-style-guide"):
        src = by_id[sid]["source"]
        assert src["url_verified"] is False, sid
        assert src["declared_url"].startswith("https://"), sid
    src = by_id["journal-style"]["source"]
    assert src["declared_url"] is None
    assert "pending" in src["venue_nomination"]


# ---------- register (English face) ----------

def test_json_keys_english():
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert KEY_PATTERN.match(k), "non-English key: %r" % k
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(_load_seed())


def test_spec_faces_english_ascii():
    for name in ("net-interface-SPEC.md", "diy-channel-SPEC.md"):
        data = io.open(_seed_path(name), "rb").read()
        data.decode("ascii")  # raises on any non-ASCII byte
        assert len(data) > 1000, name


# ---------- sync discipline (executed only when the source is present) ----------

def test_snapshot_identity_matches_source():
    data = _source_bytes_if_present()
    if data is None:
        print("SKIP test_snapshot_identity_matches_source: glossary source "
              "not present on this host")
        return
    snap = _load_seed()["source_of_truth"]["snapshot"]
    assert len(data) == snap["bytes"], "source byte count drifted"
    assert hashlib.sha256(data).hexdigest() == snap["sha256"], \
        "source sha256 drifted: regenerate the seed via the sync pass"


def _split_cells(line):
    s = line.strip()
    assert s.startswith("|") and s.endswith("|"), repr(line)
    return [c.strip() for c in s[1:-1].split("|")]


def _parse_source_section(data):
    """Minimal parser for glossary section 4.0: returns per-table
    (header_cells, row_cells lists) in document order."""
    lines = data.decode("utf-8").split("\n")
    i0 = next(i for i, l in enumerate(lines) if l.startswith("### 4.0 "))
    i1 = next(i for i, l in enumerate(lines) if l.startswith("### 4.6 "))
    tables = []
    cur = None
    for l in lines[i0 + 1:i1]:
        if l.strip().startswith("|"):
            if cur is None:
                cur = []
            cur.append(l)
        else:
            if cur is not None:
                tables.append(cur)
                cur = None
    if cur is not None:
        tables.append(cur)
    out = []
    for tl in tables:
        header = _split_cells(tl[0])
        assert set(tl[1].strip()) <= set("|-: "), tl[1]
        out.append((header, [_split_cells(x) for x in tl[2:]]))
    return out


def test_transcription_verbatim_against_source():
    """Full cell-by-cell comparison of every entry against the source
    section (executed only when the glossary file is reachable)."""
    data = _source_bytes_if_present()
    if data is None:
        print("SKIP test_transcription_verbatim_against_source: glossary "
              "source not present on this host")
        return
    seed = _load_seed()
    src_tables = _parse_source_section(data)
    assert len(src_tables) == len(SUB_TABLE_ORDER), len(src_tables)
    by_table = {}
    for e in seed["entries"]:
        by_table.setdefault(e["sub_table"], []).append(e)
    for key, (header, rows) in zip(SUB_TABLE_ORDER, src_tables):
        st = seed["entry_skeleton"]["sub_tables"][key]
        assert st["header_verbatim"] == header, key
        got = by_table[key]
        assert len(got) == len(rows), \
            "%s row count drifted: seed %d vs source %d" \
            % (key, len(got), len(rows))
        for e, src_row in zip(got, rows):
            assert e["cells"] == src_row, \
                "%s cell drift at source row %d" % (e["id"], e["row_index"])


# ---------- seed directory purity ----------

def test_seed_dir_zero_engine_body():
    d = _seed_dir()
    names = set(os.listdir(d)) - {"__pycache__"}
    assert names == SEED_DIR_FILES, \
        "seed directory surface drifted: %s" % sorted(names)
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            assert not f.endswith((".sh", ".exe", ".bat", ".cmd", ".pyd")), \
                "executable artifact in seed dir: %s" % f
            if f.endswith(".py"):
                assert f == "test_snippet.py", f


# ---------- standalone runner ----------

def _main():
    checks = [
        test_parse_face,
        test_source_of_truth_recorded,
        test_entry_skeleton_declared,
        test_entries_shape,
        test_irregular_rows_registered,
        test_meta_counts_consistent,
        test_domain_slots_three_unfetched,
        test_slot_sources_declared_not_verified,
        test_json_keys_english,
        test_spec_faces_english_ascii,
        test_snapshot_identity_matches_source,
        test_transcription_verbatim_against_source,
        test_seed_dir_zero_engine_body,
    ]
    failed = 0
    for fn in checks:
        try:
            fn()
            print("PASS %s" % fn.__name__)
        except AssertionError as e:
            failed += 1
            print("FAIL %s: %s" % (fn.__name__, e))
        except Exception as e:  # fail loud, keep counting
            failed += 1
            print("FAIL %s: %r" % (fn.__name__, e))
    print("TERMBASE-SEED-SCHEMA: %d checks, %d failed"
          % (len(checks), failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_main())
