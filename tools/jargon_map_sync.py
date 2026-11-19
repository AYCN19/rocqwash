#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jargon_map_sync.py - sync the md jargon mapping table into the seed map.

Purpose.  One-way sync of docs/jargon-to-standard-mapping-v1.md (detector
  map) into seeds/jargon/jargon-map.json (apply map), plus
  contract-prov-v2 S1 provenance: --apply re-signs v2 pins (repo to the
  blob sha of current bytes, external to the md5 of LF-normalized
  snapshot bytes) and refuses a v1-shaped seed; --migrate flips v1
  path+md5 sources to locator/pin in one pass, writes snapshots as
  LF-normalized bytes into seeds/jargon/_snapshots/, then runs the
  consumer suite as the exit gate (rollback when red).  Admission,
  upsert, zh authority and count-exact rules: see the comment block.
Interface.  --md P | --map P | --json P | --apply | --migrate |
  --selftest; plan is the default and zero-write; the VERDICT
  IN-SYNC/PENDING/SYNCED tail lines are the gate surface of
  tools/pin_repair.py.
Dependencies.  Python 3 standard library only; tools/norm_lint.py loaded
  by path (same-source RE_FW_PAREN, absent exits 9);
  seeds/jargon/SPEC.md is the schema contract; the migrate gate runs
  tests/t_engines_seeds.py with rc 0 required.  Zero network face; the
  md table is never written.
Evidence.  --selftest on temporary fixtures: filter admits and rejects,
  upsert/retag/authority with count exact, byte-identical rerun,
  duplicate-face exit 1, CLI plan zero-write, apply idempotence,
  missing input exit 9, v2 plan/apply/migrate (re-sign all-PASS,
  off-canonical keep, v1 refusal, red-smoke rollback), blob sha
  agrees with git, consistency FAIL forms, declared freshness-SKIP,
  EOL vectors (CRLF upstream pinned normalized, CRLF snapshot to LF).
Exit-codes.  0 green; 1 findings or refusal; 2 usage; 9 missing input;
  5 migrate rolled back after a red consumer smoke.
"""

# Detail carried below the five-field header budget (the norm_lint
# header-budget rule keeps the docstring to the five fields):
#
# Sync semantics (S0, unchanged).  Deterministic one-way sync from the
# detector table (curated superset) into the apply map, closing the
# two-source drift: the detector table knows every mapped face, the
# apply map must know the same set.  A md row is admitted only when its
# standard cell derives to a single form - parenthetical annotations
# stripped (the fullwidth RE_FW_PAREN rule, then the md tool track's
# ASCII-paren English-cell convention), an em-dash head integrated as
# rewrite_or_delete, and a derived form containing " / " or "U+FF0F"
# rejected as an alternation guard - and its context note carries none
# of the six guard markers ("guarded row", "per-row handling",
# "sense split", "splits the sense", "rules the face out",
# "narrative sense only").  The em-dash standard cells ("- (delete
# ...)") are the md tool track's rewrite-or-delete convention: they
# land as disposition rewrite_or_delete with no fixed standard and are
# never machine-applied.  Every row the sync writes is tagged with the
# in-repo derivation source (in-repo-md-v1), the transcription
# contract's second containment source.  An admitted face that is new
# appends one entry after the seed prefix in md document order; an
# admitted face already present with an equal standard is retagged from
# the legacy tool-track style to the in-repo source (action retagged,
# the re-admission mark); an admitted face already present with a
# differing standard updates standard, standard_language,
# standard_source, source_line and note in place - the curated superset
# supersedes - while id, face, exempts, disposition and cross_track_note
# are preserved verbatim.  One authority rule bounds the supersede: an
# existing entry whose standard_language is zh is a whitepaper-track
# transcription (the register authority) and is never machine-superseded;
# the row is reported authority-kept and left byte-identical.  Every
# existing entry survives the sync and the count label stays exact
# (count == len(entries)).
#
# Provenance v2 (contract-prov-v2).  Fingerprint the evidence itself,
# never a path: a repository source pins the git blob sha of its
# committed content (pure sha1 over the "blob <len>" header plus the
# bytes, equal to git hash-object and, under this repository's LF
# checkout discipline, to git rev-parse HEAD:<path>, the form the
# consumer judges after the commit that carries both sides); an external source
# pins the md5 of a byte-for-byte snapshot copied into the snapshots
# directory at cast time, with upstream_path kept as an informational
# locator no check grounds a verdict on.  v1 fields (absolute path plus
# md5) are not kept: the consumer flips in one commit (R14, no
# transition window), so --apply refuses a v1-shaped seed loudly and
# --migrate is the only v1-to-v2 path.  Apply re-signs in place: repo
# pins to the blob sha of current bytes; external snapshots refresh
# from upstream bytes on a canonical machine, and off-canonical a
# standing snapshot keeps its pin while the freshness layer reports a
# declared SKIP.  Migrate is idempotent, writes snapshot bytes before
# the map, self-checks its product with the v2 judgment, then runs the
# consumer suite as the exit gate and rolls the seed back
# byte-identically when the gate is red.  The md table is never a write
# target of this tool.
#
# EOL normalization (contract-eol).  The external md5 pin is an
# EOL-independent fingerprint: the pin value is the md5 of the
# CRLF-to-LF-normalized bytes (the net normalization of this
# repository's .gitattributes, "* text=auto eol=lf"), the snapshot is
# stored in the repository as LF bytes, the consistency layer hashes
# the normalized snapshot bytes, and the freshness layer hashes the
# normalized upstream bytes.  A snapshot re-saved by git (or any
# checkout/smudge shape) therefore cannot move the md5, and an upstream
# that flips line endings alone cannot either.  Upstream originals are
# never rewritten: normalization is applied to the bytes this tool
# hashes and writes into the repository, not to the authority files
# themselves.  Repository sources keep the git blob sha pin, which is
# already byte-committed and outside this law.

import argparse
import contextlib
import hashlib
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
SEED_SUITE_PATH = os.path.join(REPO_ROOT, "tests", "t_engines_seeds.py")
SUITE_TIMEOUT_S = 300

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

# --- provenance v2 (contract-prov-v2) constants ---

LOCATOR_REPO = "repo"
LOCATOR_EXTERNAL = "external"
PIN_BLOB_SHA = "git-blob-sha"
PIN_MD5 = "md5"
SNAPSHOT_DIRNAME = "_snapshots"

# the declared-SKIP text of the freshness layer, verbatim from the
# contract: an absent upstream is a declared skip, never a silent one
SKIP_FRESHNESS_DECL = ("SKIP (declared, freshness unverifiable"
                       " off-canonical: upstream absent)")

# external upstream basenames registered to their snapshot file names in
# the snapshots directory (the contract names these two); an unregistered
# upstream basename fails loud instead of inventing a name.  The keys are
# the real upstream artifact names (external evidence references, i18n
# exemption registered in the delivery report).
SNAPSHOT_NAMES = {
    "\u6ce8\u91ca\u89c4\u8303\u767d\u76ae\u4e66-v1.0-20260921.md":
        "annotation-whitepaper-v1.0-20260921.md",
    "\u672f\u8bed\u8868-\u901a\u7528-\u9879\u76ee\u7ea7-20260921.md":
        "terminology-general-project-20260921.md",
}

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
    surviving " / " or fullwidth "U+FF0F" is an alternation guard and the
    row is rejected (the alternation guard of tools/jargon_apply.py:derive_after).
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


# --- provenance v2: pins, judgments, re-sign, migration ---


def blob_sha(data):
    """Git blob sha of exact bytes (sha1 over the blob header plus body).

    Equal to git hash-object over the same bytes; under this repository's
    LF checkout discipline (gitattributes eol=lf, core.autocrlf false) it
    is also equal to git rev-parse HEAD:<path> of the committed file, the
    form the consumer check judges after the commit that carries both
    sides."""
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


def md5_hex(data):
    """The md5 hex digest of exact bytes."""
    return hashlib.md5(data).hexdigest()


def normalize_eol(data):
    """CRLF to LF, the net normalization of this repository's
    .gitattributes ("* text=auto eol=lf").

    The external md5 pin is an EOL-independent fingerprint: pins are
    computed over normalized bytes and snapshots are stored as LF
    bytes, so a git re-save or a checkout/smudge shape cannot move the
    fingerprint.  Upstream originals are never rewritten by callers of
    this function; only the hashed and stored bytes are."""
    return data.replace(b"\r\n", b"\n")


def read_bytes(path):
    """File bytes, or None when the file is missing or unreadable."""
    try:
        with io.open(path, "rb") as fh:
            return fh.read()
    except OSError:
        return None


def read_bytes_loud(path, what):
    """File bytes; fail loud exit 9 when missing or unreadable."""
    try:
        with io.open(path, "rb") as fh:
            return fh.read()
    except OSError as exc:
        fail("%s unreadable: %s (%s)" % (what, path, exc), 9)


def repo_join(repo_root, rel):
    """Resolve a repo-relative v2 path (forward slashes) to a local path."""
    return os.path.join(repo_root, *rel.split("/"))


def posix_rel(repo_root, abs_path):
    """Repository-relative forward-slash form of an absolute path."""
    rel = os.path.relpath(os.path.abspath(abs_path), repo_root)
    return rel.replace(os.sep, "/")


def write_snapshot(path, data):
    """Write snapshot bytes verbatim (callers pass LF-normalized bytes
    per contract-eol), creating the snapshots directory."""
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "wb") as fh:
        fh.write(data)


def source_shape(src):
    """v2 (locator and pin), v1 (path plus md5, no locator), or unknown."""
    if not isinstance(src, dict):
        return "unknown"
    if "locator" in src or "pin" in src:
        return "v2" if ("locator" in src and "pin" in src) else "unknown"
    if "md5" in src:
        return "v1"
    return "unknown"


def judge_repo_blob(repo_root, rel, pin):
    """Repo-source judgment: pin against the blob sha of current bytes.

    The HEAD form of this judgment (git rev-parse HEAD:<path>) belongs to
    the consumer after the commit that carries both sides; this
    working-bytes form is the pre-commit self-check of the write path."""
    if pin.get("kind") != PIN_BLOB_SHA:
        return "FAIL", "pin kind %r is not %s" % (pin.get("kind"),
                                                  PIN_BLOB_SHA)
    data = read_bytes(repo_join(repo_root, rel))
    if data is None:
        return "FAIL", "pinned file absent"
    if blob_sha(data) == pin.get("value"):
        return "PASS", "blob sha matches current file bytes"
    return "FAIL", ("content red: file bytes differ from the pinned blob"
                    " sha (edited without re-sign)")


def judge_snapshot_md5(repo_root, rel, pin):
    """External-source consistency layer: normalized snapshot bytes md5
    against the pin (CRLF to LF before hashing, contract-eol)."""
    if pin.get("kind") != PIN_MD5:
        return "FAIL", "pin kind %r is not %s" % (pin.get("kind"), PIN_MD5)
    data = read_bytes(repo_join(repo_root, rel))
    if data is None:
        return "FAIL", "snapshot absent (consistency unverifiable)"
    if md5_hex(normalize_eol(data)) == pin.get("value"):
        return "PASS", "normalized snapshot bytes match the pinned md5"
    return "FAIL", "snapshot bytes differ from the pinned md5"


def judge_freshness(upstream_path, pin):
    """External-source freshness layer: normalized upstream bytes md5
    against the pin (CRLF to LF before hashing, contract-eol).

    Canonical only: an absent upstream is a declared SKIP (the exact
    contract text), never a silent one; a present upstream whose bytes
    drifted from the pin is a real FAIL."""
    if not upstream_path or not os.path.exists(upstream_path):
        return "SKIP", SKIP_FRESHNESS_DECL
    data = read_bytes(upstream_path)
    if data is None:
        return "FAIL", "upstream present but unreadable"
    if md5_hex(normalize_eol(data)) == pin.get("value"):
        return "PASS", "freshness verified against normalized upstream" \
                       " bytes on canonical"
    return "FAIL", "upstream drifted from the pinned md5 (freshness red)"


def check_sources_v2(sources, repo_root):
    """Per-source v2 judgment rows; every result line names its layer.

    Repo sources judge repo-blob; external sources judge
    external-consistency and external-freshness.  This is the offline
    form of the consumer semantics (check_snapshot_md5 v2): the same
    layers, the same declared-SKIP text."""
    rows = []
    for src in sources:
        rel = src.get("path") if isinstance(src, dict) else None
        loc = src.get("locator") if isinstance(src, dict) else None
        pin = src.get("pin") if isinstance(src, dict) else None
        pin = pin if isinstance(pin, dict) else {}
        if loc == LOCATOR_REPO:
            status, detail = judge_repo_blob(repo_root, rel, pin)
            rows.append({"source": rel, "locator": loc,
                         "layer": "repo-blob", "status": status,
                         "detail": detail})
        elif loc == LOCATOR_EXTERNAL:
            status, detail = judge_snapshot_md5(repo_root, rel, pin)
            rows.append({"source": rel, "locator": loc,
                         "layer": "external-consistency", "status": status,
                         "detail": detail})
            status, detail = judge_freshness(src.get("upstream_path"), pin)
            rows.append({"source": rel, "locator": loc,
                         "layer": "external-freshness", "status": status,
                         "detail": detail})
        else:
            rows.append({"source": rel, "locator": loc, "layer": "shape",
                         "status": "FAIL",
                         "detail": "source is not v2-shaped"})
    return rows


def resign_sources(sources, repo_root):
    """Re-sign v2 pins to current bytes, in place; returns report rows.

    Repo sources pin the blob sha of the file's current bytes (the new
    content this sync just read).  External sources refresh the snapshot
    from the LF-normalized upstream bytes when upstream is present (a
    canonical machine stores the snapshot as LF bytes and pins their
    md5, contract-eol); off-canonical, a standing snapshot keeps its pin
    and the freshness layer reports the declared SKIP.  A source with
    neither an upstream nor a snapshot fails loud: a pin nobody can
    ground is not written.  Upstream originals are read, never
    rewritten."""
    rows = []
    for src in sources:
        if source_shape(src) != "v2":
            fail("provenance source is not v2-shaped: %r"
                 % (src.get("path") if isinstance(src, dict) else src,), 1)
        rel = src["path"]
        loc = src["locator"]
        pin = src["pin"]
        if loc == LOCATOR_REPO:
            if pin.get("kind") != PIN_BLOB_SHA:
                fail("repo source %s carries pin kind %r, expected %s"
                     % (rel, pin.get("kind"), PIN_BLOB_SHA), 1)
            data = read_bytes_loud(repo_join(repo_root, rel),
                                   "pinned repo source")
            value = blob_sha(data)
            action = "resigned" if pin.get("value") != value else "current"
            pin["kind"] = PIN_BLOB_SHA
            pin["value"] = value
            rows.append({"source": rel, "locator": loc,
                         "layer": "repo-blob", "action": action,
                         "value": value})
        elif loc == LOCATOR_EXTERNAL:
            if pin.get("kind") != PIN_MD5:
                fail("external source %s carries pin kind %r, expected %s"
                     % (rel, pin.get("kind"), PIN_MD5), 1)
            upstream = src.get("upstream_path")
            snapshot = repo_join(repo_root, rel)
            if upstream and os.path.exists(upstream):
                data = normalize_eol(read_bytes_loud(upstream,
                                                     "external upstream"))
                changed = read_bytes(snapshot) != data
                if changed:
                    write_snapshot(snapshot, data)
                value = md5_hex(data)
                if changed:
                    action = "refreshed"
                elif pin.get("value") != value:
                    action = "resigned"
                else:
                    action = "current"
                pin["kind"] = PIN_MD5
                pin["value"] = value
                detail = "snapshot holds the LF-normalized upstream bytes"
            elif os.path.isfile(snapshot):
                action = "kept"
                value = pin.get("value")
                detail = ("off-canonical: standing snapshot keeps its pin;"
                          " freshness " + SKIP_FRESHNESS_DECL)
            else:
                fail("external source %s has neither an upstream to copy"
                     " nor a snapshot to keep (upstream: %s)"
                     % (rel, upstream), 9)
            rows.append({"source": rel, "locator": loc,
                         "layer": "external-consistency", "action": action,
                         "value": value, "detail": detail})
        else:
            fail("unknown locator %r for source %r" % (loc, rel), 1)
    return rows


def apply_resign(m, repo_root):
    """The --apply provenance tail: refuse v1 loudly, re-sign v2 in place.

    Returns the per-source re-sign rows (None when the seed carries no
    provenance sources list).  A v1-shaped seed refuses the whole apply
    before any write: the consumer flips in the same commit (R14), so the
    only v1-to-v2 path is --migrate."""
    prov = m.get("provenance")
    if not isinstance(prov, dict):
        return None
    sources = prov.get("sources")
    if not isinstance(sources, list):
        return None
    shapes = [source_shape(s) for s in sources]
    if "unknown" in shapes:
        fail("provenance source shape unrecognized; refusing the apply", 1)
    if "v1" in shapes:
        fail("provenance sources are v1-shaped (absolute path plus md5);"
             " refusing a half-migrated apply write; run --migrate first"
             " (the consumer patch lands in the same commit)", 1)
    if not shapes:
        return []
    return resign_sources(sources, repo_root)


def migrate_source(src, repo_root, snapshot_dir):
    """One v1 source flipped to the v2 form; returns (new dict, snapshot
    path or None, bytes).

    A source inside the repository becomes a repo locator pinned to the
    blob sha of its current bytes.  An external source is snapshotted:
    the caller stores the LF-normalized bytes (contract-eol: snapshots
    live in the repository as LF bytes) and the pin is the md5 of those
    normalized bytes, with the v1 absolute path kept as the
    informational upstream_path.  Role text and the whitepaper's
    self-declared version ride along unchanged; the v1 md5 key does
    not.  The upstream original is read, never rewritten."""
    path = src.get("path")
    if not isinstance(path, str) or not path:
        fail("v1 source without a usable path: %r" % (src,), 1)
    abs_path = os.path.abspath(path)
    try:
        rel = posix_rel(repo_root, abs_path)
        is_repo = not rel.startswith("../")
    except ValueError:
        # across drives there is no relative form; treat as external
        is_repo = False
    data = read_bytes_loud(abs_path, "v1 source")
    out = {}
    if is_repo:
        out["locator"] = LOCATOR_REPO
        out["path"] = rel
        for key in ("role", "self_declared_version"):
            if src.get(key) is not None:
                out[key] = src[key]
        out["pin"] = {"kind": PIN_BLOB_SHA, "value": blob_sha(data)}
        return out, None, data
    name = SNAPSHOT_NAMES.get(os.path.basename(abs_path))
    if name is None:
        fail("no snapshot name registered for upstream basename %r;"
             " registered snapshot names: %s"
             % (os.path.basename(abs_path),
                ", ".join(sorted(SNAPSHOT_NAMES.values()))), 1)
    snapshot_abs = os.path.join(snapshot_dir, name)
    data = normalize_eol(data)
    out["locator"] = LOCATOR_EXTERNAL
    out["path"] = posix_rel(repo_root, snapshot_abs)
    out["upstream_path"] = path
    for key in ("role", "self_declared_version"):
        if src.get(key) is not None:
            out[key] = src[key]
    out["pin"] = {"kind": PIN_MD5, "value": md5_hex(data)}
    return out, snapshot_abs, data


def rollback_migrate(map_path, raw, prior_snapshots):
    """Restore the seed bytes and every snapshot this run touched."""
    with io.open(map_path, "wb") as fh:
        fh.write(raw)
    for path, prior in sorted(prior_snapshots.items()):
        if prior is None:
            if os.path.exists(path):
                os.remove(path)
        else:
            with io.open(path, "wb") as fh:
                fh.write(prior)
    restored = read_bytes(map_path) == raw
    print("  rollback seed %s; snapshots restored=%d"
          % ("byte-identical" if restored else "FAILED",
             len(prior_snapshots)))
    return restored


def run_seed_suite(repo_root, suite_path):
    """Run the consumer seed suite; returns (rc, output).

    rc is None when the suite could not be launched or timed out; the
    second value then carries the failure text instead of output."""
    import subprocess
    try:
        proc = subprocess.run([sys.executable, "-I", suite_path],
                              cwd=repo_root, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=SUITE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, "seed suite timed out after %ds" % SUITE_TIMEOUT_S
    except OSError as exc:
        return None, "seed suite failed to launch: %s" % exc
    return proc.returncode, proc.stdout or ""


def _suite_label(repo_root, suite_path):
    """Forward-slash repo-relative label of the suite path for reports."""
    try:
        return os.path.relpath(suite_path, repo_root).replace(os.sep, "/")
    except ValueError:
        return suite_path


def _emit_json(report, json_path):
    """Write the report JSON when a path was given (same style as sync)."""
    if not json_path:
        return
    parent = os.path.dirname(os.path.abspath(json_path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(json_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=1,
                            sort_keys=True) + "\n")


def _print_rows(rows):
    """Print judgment rows: status, layer, source, detail (layer named)."""
    for r in rows:
        print("  %s %s %s - %s"
              % (r["status"], r["layer"], r["source"], r["detail"]))


def migrate_map(map_path, repo_root=REPO_ROOT, suite_path=SEED_SUITE_PATH,
                json_path=None):
    """Flip v1 provenance to v2 in one pass; idempotent; exit gate = the
    consumer suite (rc 0 required, R14 discipline).

    Write order: snapshot bytes first (the referent), then the map.  The
    migrated seed is self-checked with the v2 judgment before the consumer
    suite runs; a red self-check or a red suite rolls the seed (and every
    snapshot this run wrote or overwrote) back byte-identically.  Returns
    the process exit code: 0 green, 1 refusal or red self-check, 5 red
    consumer smoke."""
    m = load_map(map_path)
    raw = read_bytes(map_path)
    prov = m.get("provenance") if isinstance(m.get("provenance"), dict) \
        else None
    sources = prov.get("sources") if isinstance(prov, dict) else None
    if not isinstance(sources, list):
        fail("seed carries no provenance.sources list to migrate: "
             + map_path, 1)
    print("%s %s: mode=migrate map=%s sources=%d"
          % (TOOL, SCHEMA, os.path.abspath(map_path), len(sources)))
    summary = {"schema": SCHEMA, "tool": TOOL, "mode": "migrate",
               "map": os.path.abspath(map_path),
               "sources_in": len(sources)}
    shapes = [source_shape(s) for s in sources]
    if not shapes or all(s == "v2" for s in shapes):
        # idempotent no-op: already v2, nothing to write
        print("  no-op: provenance is already v2 (%d sources)"
              % len(sources))
        rows = check_sources_v2(sources, repo_root)
        _print_rows(rows)
        summary["action"] = "none (provenance already v2)"
        red = [r for r in rows if r["status"] == "FAIL"]
        if red:
            summary["verify"] = rows
            _emit_json(summary, json_path)
            fail("already-v2 seed fails its own v2 judgment (%d red rows);"
                 " migration wrote nothing" % len(red), 1)
        rc_suite, _out = run_seed_suite(repo_root, suite_path)
        summary["verify"] = rows
        if rc_suite == 0:
            print("consumer smoke: %s rc=0" % _suite_label(repo_root,
                                                           suite_path))
            print("MIGRATE VERDICT NO-OP (provenance already v2; smoke rc=0)")
            summary["consumer_smoke"] = {"rc": 0}
            _emit_json(summary, json_path)
            return 0
        print("consumer smoke RED (rc=%s); the no-op wrote nothing"
              % rc_suite)
        summary["consumer_smoke"] = {"rc": rc_suite}
        _emit_json(summary, json_path)
        return 5
    if set(shapes) - {"v1"}:
        fail("provenance mixes source shapes (%s); migration refuses a"
             " partial flip" % sorted(set(shapes)), 1)
    if (json.dumps(m, ensure_ascii=False, indent=2) + "\n") \
            != raw.decode("utf-8"):
        fail("seed is not byte-stable under the map serializer; refusing"
             " a write that could reformat unrelated bytes", 1)
    snapshot_dir = os.path.join(os.path.dirname(os.path.abspath(map_path)),
                                SNAPSHOT_DIRNAME)
    prior = {}
    pending = []
    migrated = []
    for src in sources:
        new_src, snapshot_abs, data = migrate_source(src, repo_root,
                                                     snapshot_dir)
        if snapshot_abs is not None:
            prior[snapshot_abs] = read_bytes(snapshot_abs)
            pending.append((snapshot_abs, data))
            summary.setdefault("snapshots", []).append(
                {"path": posix_rel(repo_root, snapshot_abs),
                 "bytes": len(data)})
        migrated.append(new_src)
    for snapshot_abs, data in pending:
        write_snapshot(snapshot_abs, data)
    prov["sources"] = migrated
    write_map(map_path, m)
    for old, new_src in zip(sources, migrated):
        print("  migrated %s -> %s (%s)"
              % (old.get("path"), new_src["path"], new_src["pin"]["kind"]))
    rows = check_sources_v2(migrated, repo_root)
    _print_rows(rows)
    summary["action"] = "migrated"
    summary["verify"] = rows
    red = [r for r in rows if r["status"] == "FAIL"]
    if red:
        restored = rollback_migrate(map_path, raw, prior)
        summary["rollback"] = "byte-identical" if restored else "FAILED"
        _emit_json(summary, json_path)
        fail("migrated seed failed its own v2 self-check (%d red rows);"
             " seed rolled back" % len(red), 1)
    rc_suite, _out = run_seed_suite(repo_root, suite_path)
    if rc_suite == 0:
        print("consumer smoke: %s rc=0" % _suite_label(repo_root, suite_path))
        print("MIGRATE VERDICT GREEN (sources=%d snapshots=%d smoke rc=0)"
              % (len(migrated), len(pending)))
        summary["consumer_smoke"] = {"rc": 0}
        _emit_json(summary, json_path)
        return 0
    restored = rollback_migrate(map_path, raw, prior)
    print("consumer smoke RED (rc=%s); migration exit 5" % rc_suite)
    summary["consumer_smoke"] = {"rc": rc_suite}
    summary["rollback"] = "byte-identical" if restored else "FAILED"
    _emit_json(summary, json_path)
    return 5


def run_migrate(args):
    """CLI wrapper of migrate_map (the md table is never a migrate input)."""
    if args.md != DEFAULT_MD_PATH:
        fail("--migrate takes no --md; the md table is never written here", 2)
    return migrate_map(args.map, json_path=args.json)


def run_sync(args, repo_root=REPO_ROOT):
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
    prov_rows = None
    if mode == "apply":
        prov_rows = apply_resign(m, repo_root)
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
        "provenance": ({"sources": prov_rows}
                       if prov_rows is not None else None),
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
    if prov_rows:
        for r in prov_rows:
            print("  %s %s [%s] pin=%s"
                  % (r["action"], r["source"], r["layer"], r["value"]))
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


def _skip(results, name, detail):
    """Record a vector that could not run on this machine (never a FAIL)."""
    results.append((name, "skip", detail))


def _write(tmp, rel, text):
    path = os.path.join(tmp, rel)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def _write_bytes(path, data):
    with io.open(path, "wb") as fh:
        fh.write(data)
    return path


def _run_sync_apply(md_path, map_path):
    """In-process apply over fixture files; returns (report dict, rc)."""
    m = load_map(map_path)
    before = json.dumps(m, ensure_ascii=False, indent=2) + "\n"
    plan = sync_apply(m, sync_plan(parse_md_rows(md_path)))
    after = json.dumps(m, ensure_ascii=False, indent=2) + "\n"
    report = {"before": before, "after": after, "plan": plan, "map": m}
    return report, 0


# fixture upstream basename: the registered annotation-whitepaper upstream
# (external evidence reference; the snapshot name comes from SNAPSHOT_NAMES)
UP_BASE = "\u6ce8\u91ca\u89c4\u8303\u767d\u76ae\u4e66-v1.0-20260921.md"
SNAP_REL = "seeds/jargon/_snapshots/" + SNAPSHOT_NAMES[UP_BASE]


def _v2_doc(md_data, up_data, upstream, pin_blob=None, pin_md=None):
    """Fixture v2 map doc over one repo source and one external source."""
    return {
        "schema": MAP_SCHEMA, "engine": "jargon",
        "seed_role": "fixture map for the provenance v2 vectors",
        "face_language": "en", "count": 2,
        "provenance": {"transcription": "fixture provenance v2 map",
                       "sources": [
                           {"locator": LOCATOR_REPO, "path": "docs/table.md",
                            "role": "fixture detector table",
                            "pin": {"kind": PIN_BLOB_SHA,
                                    "value": pin_blob or blob_sha(md_data)}},
                           {"locator": LOCATOR_EXTERNAL, "path": SNAP_REL,
                            "upstream_path": upstream,
                            "role": "fixture authority",
                            "pin": {"kind": PIN_MD5,
                                    "value": pin_md or md5_hex(up_data)}}]},
        "entries": [
            {"id": "J001", "face": "alpha", "standard": "one",
             "standard_language": "en", "standard_source": IN_REPO_SOURCE,
             "source_line": 1, "disposition": "replace", "exempts": [],
             "cross_track_note": None, "note": "clean row."},
            {"id": "J002", "face": "beta", "standard": "two",
             "standard_language": "en", "standard_source": IN_REPO_SOURCE,
             "source_line": 2, "disposition": "replace", "exempts": [],
             "cross_track_note": None, "note": "clean row."},
        ],
    }


def _v1_doc(upstream, md_abs, md_data, up_data):
    """Fixture v1 map doc over the same two sources (absolute path + md5)."""
    return {
        "schema": MAP_SCHEMA, "engine": "jargon",
        "seed_role": "fixture map for the migration vectors",
        "face_language": "en", "count": 2,
        "provenance": {"transcription": "fixture provenance v1 map",
                       "sources": [
                           {"path": md_abs,
                            "role": "fixture detector table",
                            "md5": md5_hex(md_data)},
                           {"path": upstream,
                            "role": "fixture authority",
                            "self_declared_version": "v1.8 (fixture)",
                            "md5": md5_hex(up_data)}]},
        "entries": [
            {"id": "J001", "face": "alpha", "standard": "one",
             "standard_language": "en", "standard_source": IN_REPO_SOURCE,
             "source_line": 1, "disposition": "replace", "exempts": [],
             "cross_track_note": None, "note": "clean row."},
            {"id": "J002", "face": "beta", "standard": "two",
             "standard_language": "en", "standard_source": IN_REPO_SOURCE,
             "source_line": 2, "disposition": "replace", "exempts": [],
             "cross_track_note": None, "note": "clean row."},
        ],
    }


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

        # --- provenance v2 vectors (contract-prov-v2 S1) ---
        v2dir = os.path.join(tmp, "v2world")
        repo_root = os.path.join(v2dir, "repo")
        docs_dir = os.path.join(repo_root, "docs")
        seeds_dir = os.path.join(repo_root, "seeds", "jargon")
        up_dir = os.path.join(v2dir, "upstream")
        for d in (docs_dir, seeds_dir, up_dir):
            os.makedirs(d, exist_ok=True)
        md_v2 = os.path.join(docs_dir, "table.md")
        upstream = os.path.join(up_dir, UP_BASE)
        snap_v2 = repo_join(repo_root, SNAP_REL)
        map_v2 = os.path.join(seeds_dir, "jargon-map.json")
        map_v1 = os.path.join(seeds_dir, "v1-map.json")
        md_bytes_1 = ("| alpha | one | clean row. |\n"
                      "| beta | two | clean row. |\n").encode("utf-8")
        # a byte-level edit that parses to the same rows (comment line):
        # pins must move while the entry sync stays unchanged
        md_bytes_2 = ("# revised table bytes\n"
                      "| alpha | one | clean row. |\n"
                      "| beta | two | clean row. |\n").encode("utf-8")
        up_bytes_1 = b"upstream authority bytes v1\n"
        up_bytes_2 = b"upstream authority bytes v2\n"
        suite_green = _write(tmp, "suite_green.py",
                             "import sys\nsys.exit(0)\n")
        suite_red = _write(tmp, "suite_red.py",
                           "import sys\nsys.exit(1)\n")

        def reset_v2(md_data, up_data, snap_data=None):
            _write_bytes(md_v2, md_data)
            _write_bytes(upstream, up_data)
            if snap_data is not None:
                write_snapshot(snap_v2, snap_data)
            _write_bytes(map_v2,
                         (json.dumps(_v2_doc(md_data, up_data, upstream),
                                     ensure_ascii=False, indent=2)
                          + "\n").encode("utf-8"))

        def reset_v1(md_data, up_data):
            _write_bytes(md_v2, md_data)
            _write_bytes(upstream, up_data)
            doc = _v1_doc(upstream, os.path.abspath(md_v2), md_data, up_data)
            _write_bytes(map_v1,
                         (json.dumps(doc, ensure_ascii=False, indent=2)
                          + "\n").encode("utf-8"))

        # vector 10: plan mode over a v2 seed keeps its verdict and
        # zero-write contract unchanged
        reset_v2(md_bytes_1, up_bytes_1, snap_data=up_bytes_1)
        digest0 = read_bytes(map_v2)
        proc = subprocess_run([sys.executable, "-I", "-X", "utf8",
                               os.path.abspath(__file__), "--map", map_v2,
                               "--md", md_v2])
        ok = (proc.returncode == 0 and read_bytes(map_v2) == digest0
              and "VERDICT IN-SYNC" in proc.stdout)
        _vec(results, "v2-plan-verdict-unchanged", ok,
             "plan mode over locator/pin provenance stays content-only:"
             " IN-SYNC, rc 0, zero bytes written"
             if ok else "rc=%d out=%r" % (proc.returncode, proc.stdout[:200]))

        # vector 11: --apply re-signs v2 pins to current bytes; a second
        # apply is byte-identical
        reset_v2(md_bytes_1, up_bytes_1, snap_data=up_bytes_1)
        _write_bytes(md_v2, md_bytes_2)
        _write_bytes(upstream, up_bytes_2)
        ns = argparse.Namespace(md=md_v2, map=map_v2, apply=True, json=None)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = run_sync(ns, repo_root=repo_root)
        doc = load_map(map_v2)
        s_repo, s_ext = doc["provenance"]["sources"]
        judge_rows = check_sources_v2(doc["provenance"]["sources"], repo_root)
        ok = (rc == 0
              and s_repo["pin"]["kind"] == PIN_BLOB_SHA
              and s_repo["pin"]["value"] == blob_sha(md_bytes_2)
              and read_bytes(snap_v2) == up_bytes_2
              and s_ext["pin"]["kind"] == PIN_MD5
              and s_ext["pin"]["value"] == md5_hex(up_bytes_2)
              and len(judge_rows) == 3
              and all(r["status"] == "PASS" for r in judge_rows))
        digest_re = read_bytes(map_v2)
        with contextlib.redirect_stdout(io.StringIO()):
            rc2 = run_sync(ns, repo_root=repo_root)
        ok = ok and rc2 == 0 and read_bytes(map_v2) == digest_re
        _vec(results, "v2-apply-resigns-pins", ok,
             "apply moved the repo pin to the new blob sha, refreshed the"
             " snapshot from upstream bytes, re-pinned the md5; the v2"
             " judgment is all-PASS and a second apply is byte-identical"
             if ok else "rc=%d/%d rows=%r" % (rc, rc2, judge_rows))

        # vector 12: off-canonical apply keeps the standing snapshot and
        # its pin (the freshness layer will declare the SKIP)
        reset_v2(md_bytes_1, up_bytes_1, snap_data=up_bytes_1)
        digest0 = read_bytes(map_v2)
        os.rename(upstream, upstream + ".away")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = run_sync(ns, repo_root=repo_root)
        doc = load_map(map_v2)
        s_ext = doc["provenance"]["sources"][1]
        rows = check_sources_v2(doc["provenance"]["sources"], repo_root)
        fresh = [r for r in rows if r["layer"] == "external-freshness"]
        cons = [r for r in rows if r["layer"] == "external-consistency"]
        ok = (rc == 0
              and s_ext["pin"]["value"] == md5_hex(up_bytes_1)
              and read_bytes(snap_v2) == up_bytes_1
              and read_bytes(map_v2) == digest0
              and fresh and fresh[0]["status"] == "SKIP"
              and cons and cons[0]["status"] == "PASS")
        os.rename(upstream + ".away", upstream)
        _vec(results, "v2-apply-off-canonical-keeps-snapshot", ok,
             "without upstream, apply keeps the standing snapshot and pin"
             " (map byte-identical); consistency PASS, freshness SKIP"
             if ok else "rc=%d rows=%r" % (rc, rows))

        # vector 13: --apply on a v1-shaped seed refuses loudly, zero write
        reset_v1(md_bytes_1, up_bytes_1)
        digest0 = read_bytes(map_v1)
        proc = subprocess_run([sys.executable, "-I", "-X", "utf8",
                               os.path.abspath(__file__), "--map", map_v1,
                               "--md", md_v2, "--apply"])
        ok = (proc.returncode == 1 and read_bytes(map_v1) == digest0
              and "migrate" in (proc.stderr or ""))
        _vec(results, "v2-apply-refuses-v1-shape", ok,
             "v1 path+md5 provenance refuses the apply (exit 1, zero"
             " write, stderr names --migrate)"
             if ok else "rc=%d err=%r" % (proc.returncode,
                                          (proc.stderr or "")[:200]))

        # vector 14: --migrate flips v1 to v2, writes the snapshot, is
        # idempotent, and self-checks all-PASS
        reset_v1(md_bytes_1, up_bytes_1)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = migrate_map(map_v1, repo_root=repo_root,
                             suite_path=suite_green)
        doc = json.loads(read_bytes(map_v1).decode("utf-8"))
        srcs = doc["provenance"]["sources"]
        snap_data = read_bytes(snap_v2)
        judge_rows = check_sources_v2(srcs, repo_root)
        ok = (rc == 0
              and "md5" not in srcs[0] and "md5" not in srcs[1]
              and srcs[0]["locator"] == LOCATOR_REPO
              and srcs[0]["path"] == "docs/table.md"
              and srcs[0]["pin"]["kind"] == PIN_BLOB_SHA
              and srcs[0]["pin"]["value"] == blob_sha(md_bytes_1)
              and srcs[1]["locator"] == LOCATOR_EXTERNAL
              and srcs[1]["path"] == SNAP_REL
              and srcs[1]["upstream_path"] == upstream
              and srcs[1]["pin"]["kind"] == PIN_MD5
              and srcs[1]["pin"]["value"] == md5_hex(up_bytes_1)
              and srcs[1]["self_declared_version"] == "v1.8 (fixture)"
              and snap_data == up_bytes_1
              and len(judge_rows) == 3
              and all(r["status"] == "PASS" for r in judge_rows)
              and doc["count"] == 2
              and [e["id"] for e in doc["entries"]] == ["J001", "J002"])
        digest_mig = read_bytes(map_v1)
        with contextlib.redirect_stdout(io.StringIO()):
            rc2 = migrate_map(map_v1, repo_root=repo_root,
                              suite_path=suite_green)
        ok = ok and rc2 == 0 and read_bytes(map_v1) == digest_mig
        _vec(results, "v2-migrate-flip-idempotent", ok,
             "migrate flipped both sources to locator/pin (v1 md5 keys"
             " gone), wrote the byte-identical snapshot, kept entries and"
             " count, judged all-PASS, and a second migrate is a no-op"
             if ok else "rc=%d/%d srcs=%r" % (rc, rc2, srcs))

        # vector 15: a red consumer smoke rolls the migration back
        reset_v1(md_bytes_1, up_bytes_1)
        if os.path.exists(snap_v2):
            os.remove(snap_v2)
        digest0 = read_bytes(map_v1)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = migrate_map(map_v1, repo_root=repo_root,
                             suite_path=suite_red)
        ok = (rc == 5 and read_bytes(map_v1) == digest0
              and not os.path.exists(snap_v2))
        _vec(results, "v2-migrate-smoke-red-rolls-back", ok,
             "red consumer smoke (rc 1 fixture suite): seed rolled back"
             " byte-identically, created snapshot removed, exit 5"
             if ok else "rc=%d snap_exists=%s"
             % (rc, os.path.exists(snap_v2)))

        # vector 16: the pure blob sha agrees with git (hash-object and,
        # after a commit, rev-parse HEAD:path)
        git = shutil.which("git")
        if git is None:
            _skip(results, "repo-blob-agrees-with-git",
                  "SKIP: git unavailable on this machine; the agreement"
                  " check did not run")
        else:
            import subprocess
            grepo = os.path.join(tmp, "grepo")
            gdocs = os.path.join(grepo, "docs")
            os.makedirs(gdocs, exist_ok=True)
            gf = os.path.join(gdocs, "pinned.md")
            gdata = b"pinned bytes v1\n"
            _write_bytes(gf, gdata)

            def g(*a):
                return subprocess.run(
                    [git, "-C", grepo, "-c", "core.autocrlf=false"] + list(a),
                    capture_output=True, text=True, timeout=60)

            g("init", "-q")
            h = g("hash-object", "docs/pinned.md").stdout.strip()
            g("add", "docs/pinned.md")
            g("-c", "user.email=f@f.example", "-c", "user.name=fixture",
              "commit", "-q", "-m", "pin fixture")
            r = g("rev-parse", "HEAD:docs/pinned.md").stdout.strip()
            ok = (h == blob_sha(gdata) and r == blob_sha(gdata))
            _vec(results, "repo-blob-agrees-with-git", ok,
                 "blob_sha equals git hash-object and git rev-parse"
                 " HEAD:docs/pinned.md (%s)" % blob_sha(gdata)
                 if ok else "hash-object=%r rev-parse=%r expected=%r"
                 % (h, r, blob_sha(gdata)))

        # vector 17: v2 judgment forms - all-PASS baseline, snapshot
        # absent FAIL, snapshot tampered FAIL
        reset_v2(md_bytes_1, up_bytes_1, snap_data=up_bytes_1)
        doc = load_map(map_v2)
        rows = check_sources_v2(doc["provenance"]["sources"], repo_root)
        all_pass = (len(rows) == 3
                    and all(r["status"] == "PASS" for r in rows))
        os.remove(snap_v2)
        rows = check_sources_v2(doc["provenance"]["sources"], repo_root)
        cons = [r for r in rows if r["layer"] == "external-consistency"]
        absent_fail = (cons and cons[0]["status"] == "FAIL"
                       and "absent" in cons[0]["detail"])
        _write_bytes(snap_v2, b"tampered bytes\n")
        rows = check_sources_v2(doc["provenance"]["sources"], repo_root)
        cons = [r for r in rows if r["layer"] == "external-consistency"]
        tamper_fail = (cons and cons[0]["status"] == "FAIL"
                       and "differ" in cons[0]["detail"])
        ok = all_pass and absent_fail and tamper_fail
        _vec(results, "v2-judgment-consistency-forms", ok,
             "all-PASS baseline; deleted snapshot is a consistency FAIL"
             " (absent); tampered snapshot is a consistency FAIL (differ)"
             if ok else "pass=%s absent=%s tamper=%s"
             % (all_pass, absent_fail, tamper_fail))

        # vector 18: absent upstream is a declared SKIP with the exact
        # contract text, beside a PASS consistency layer
        reset_v2(md_bytes_1, up_bytes_1, snap_data=up_bytes_1)
        os.rename(upstream, upstream + ".away")
        doc = load_map(map_v2)
        rows = check_sources_v2(doc["provenance"]["sources"], repo_root)
        fresh = [r for r in rows if r["layer"] == "external-freshness"]
        cons = [r for r in rows if r["layer"] == "external-consistency"]
        ok = (fresh and fresh[0]["status"] == "SKIP"
              and fresh[0]["detail"] == SKIP_FRESHNESS_DECL
              and cons and cons[0]["status"] == "PASS")
        os.rename(upstream + ".away", upstream)
        _vec(results, "freshness-skip-declared-off-canonical", ok,
             "freshness layer reports exactly %r while consistency stays"
             " PASS" % SKIP_FRESHNESS_DECL
             if ok else "rows=%r" % rows)

        # --- EOL normalization vectors (contract-eol) ---
        up_crlf = b"authority bytes v1\r\nsecond authority line\r\n"
        up_norm = normalize_eol(up_crlf)

        # vector 19: a CRLF upstream is pinned by its normalized md5 and
        # stored as an LF snapshot
        reset_v2(md_bytes_1, up_crlf, snap_data=None)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = run_sync(ns, repo_root=repo_root)
        doc = load_map(map_v2)
        s_ext = doc["provenance"]["sources"][1]
        snap_data = read_bytes(snap_v2)
        rows = check_sources_v2(doc["provenance"]["sources"], repo_root)
        ok = (rc == 0
              and s_ext["pin"]["value"] == md5_hex(up_norm)
              and snap_data == up_norm
              and b"\r\n" not in snap_data
              and len(rows) == 3
              and all(r["status"] == "PASS" for r in rows))
        _vec(results, "eol-crlf-upstream-pinned-normalized", ok,
             "a CRLF upstream re-signs the pin to the normalized md5 and"
             " the snapshot is stored as LF bytes; the v2 judgment is"
             " all-PASS"
             if ok else "rc=%d pin=%s rows=%r"
             % (rc, s_ext["pin"]["value"], rows))

        # vector 20: a standing CRLF snapshot is rewritten to LF bytes on
        # apply, and a git-style re-save back to CRLF cannot move the
        # consistency verdict
        reset_v2(md_bytes_1, up_crlf, snap_data=up_crlf)
        doc = _v2_doc(md_bytes_1, up_crlf, upstream,
                      pin_md=md5_hex(up_norm))
        _write_bytes(map_v2, (json.dumps(doc, ensure_ascii=False,
                                         indent=2) + "\n").encode("utf-8"))
        with contextlib.redirect_stdout(io.StringIO()):
            rc = run_sync(ns, repo_root=repo_root)
        snap_after = read_bytes(snap_v2)
        digest0 = read_bytes(map_v2)
        # simulate a checkout/smudge shape that re-saves the snapshot
        # with CRLF line endings
        _write_bytes(snap_v2, up_crlf)
        doc2 = load_map(map_v2)
        rows = check_sources_v2(doc2["provenance"]["sources"], repo_root)
        cons = [r for r in rows if r["layer"] == "external-consistency"]
        with contextlib.redirect_stdout(io.StringIO()):
            rc2 = run_sync(ns, repo_root=repo_root)
        ok = (rc == 0
              and snap_after == up_norm
              and b"\r\n" not in snap_after
              and cons and cons[0]["status"] == "PASS"
              and rc2 == 0
              and read_bytes(snap_v2) == up_norm
              and read_bytes(map_v2) == digest0)
        _vec(results, "eol-crlf-snapshot-rewritten-to-lf", ok,
             "a CRLF snapshot is rewritten to LF bytes on apply; a re-save"
             " back to CRLF still passes the consistency layer and the"
             " next apply restores LF with the map unchanged"
             if ok else "rc=%d/%d cons=%r" % (rc, rc2, cons))

        # vector 21: the EOL pass is idempotent - a second apply over the
        # normalized tree is byte-identical on both the map and snapshot
        reset_v2(md_bytes_1, up_crlf, snap_data=None)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = run_sync(ns, repo_root=repo_root)
        digest_map = read_bytes(map_v2)
        digest_snap = read_bytes(snap_v2)
        with contextlib.redirect_stdout(io.StringIO()):
            rc2 = run_sync(ns, repo_root=repo_root)
        ok = (rc == 0 and rc2 == 0
              and read_bytes(map_v2) == digest_map
              and read_bytes(snap_v2) == digest_snap)
        _vec(results, "eol-normalized-apply-idempotent", ok,
             "a second apply over the normalized tree writes zero bytes:"
             " map and snapshot stay byte-identical"
             if ok else "rc=%d/%d map_stable=%s snap_stable=%s"
             % (rc, rc2, read_bytes(map_v2) == digest_map,
                read_bytes(snap_v2) == digest_snap))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = 0
    for name, ok, detail in results:
        if ok is True:
            tag = "PASS"
        elif ok == "skip":
            tag = "SKIP"
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
                    help="write the synced map and re-sign v2 provenance"
                         " pins (default is a zero-write plan)")
    ap.add_argument("--migrate", action="store_true",
                    help="flip v1 provenance to v2 once, write snapshots,"
                         " then run the consumer suite as the exit gate")
    ap.add_argument("--json", metavar="P",
                    help="write the report JSON there")
    ap.add_argument("--selftest", action="store_true",
                    help="run the selftest vectors; standalone")
    args = ap.parse_args(argv)
    if args.selftest:
        if args.apply or args.migrate or args.json \
                or args.md != DEFAULT_MD_PATH or args.map != DEFAULT_MAP_PATH:
            fail("--selftest runs standalone; combine it with no scan flags", 2)
        return run_selftest(args)
    if args.migrate:
        if args.apply:
            fail("--migrate and --apply are separate modes", 2)
        return run_migrate(args)
    return run_sync(args)


if __name__ == "__main__":
    sys.exit(main())
