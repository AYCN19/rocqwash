#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registry_regen: contribution-surface registration-row regeneration onto the merge-target lineage.

Purpose.  Rebuild the contribution-side registry pair (order.txt and
  _CoqProject) as the merge-target books verbatim plus canonical rows for the
  named pieces, tail-appended in dependency order, each order row carrying the
  canonical anchor `#R<seq>-<md5-8>` recomputed from the piece entity.
  Dry run by default; the draft is written only under `--apply` into `--out`.

Interface.  `--base-repo REPO --base-ref REF --contrib-repo REPO
  --contrib-ref REF --pieces M1,M2,... --anchor-src DIR [--dep-source
  require|coqdep|registry|auto] [--seq N] [--out DIR] [--apply] [--json P]`;
  schema rocqwash-registry-regen/1.  Dependency order: stdlib Require-surface
  topology by default (dependencies first, ties by the contribution
  registry's existing row order), coqdep when selected, or the registry's
  existing order verbatim.

Dependencies.  Python 3 standard library only; same-source engine import of
  `tools/registry_union.py` (key/anchor forms, assertions, entity md5, git
  show, EOL render); git on PATH for ref reads.

Evidence.  --selftest vectors on temporary fixtures: three-piece topological
  regeneration, missing-dependency BLOCK, the frozen md5 vector ("module A
  content alpha" -> 77c2b9a8), dry-run zero-write, blast and divergence
  cases, CLI exit codes, byte-identical reruns.

Exit-codes.  0 draft produced (BLOCK pieces are data, reported loudly); 1 selftest red;
  2 usage error or assertion failure (key collision, anchor-text collision,
  dependency cycle, entity ambiguity, entity-blob divergence, write integrity);
  9 missing input (repo, ref, book, anchor-src, coqdep absent when selected).
"""
# Extended contract (help face; kept outside the five-field block so the
# header stays within the 30-line budget of the annotation standard):
#
# Inputs
#   --base-repo/--base-ref        merge-target repository and ref; its
#                                 registry pair is the verbatim bottom of the
#                                 regenerated draft (never written by this
#                                 tool).
#   --contrib-repo/--contrib-ref  contribution-surface repository and ref; its
#                                 registry pair supplies each piece's existing
#                                 registration form (row keys and paths) and
#                                 the blob used to cross-check the entity.
#   --pieces M1,M2,...            contribution piece names (bare module
#                                 names; a .v suffix is tolerated and
#                                 stripped); duplicates collapsed keep-first.
#   --anchor-src DIR              materialized contribution tree; each
#                                 piece's entity is the unique <name>.v found
#                                 under it (recursive walk; ambiguity fails
#                                 loud).  It should be the tree root so
#                                 entity relative paths match registry path
#                                 forms.
#   --dep-source                  dependency-ORDER source: require (default,
#                                 stdlib Require-surface parse), coqdep (the
#                                 coqdep binary; exit 9 when absent),
#                                 registry (the contribution registry's
#                                 existing row order verbatim), auto (coqdep
#                                 when on PATH, else require).  Dependency
#                                 SATISFACTION (external dependency
#                                 registered, cascade through blocked pieces,
#                                 cycle detection) always uses the stdlib
#                                 Require parse so the BLOCK semantics are
#                                 uniform across modes; the registry's
#                                 existing order is the tiebreak in every
#                                 mode, so it is never discarded.
#   --seq N                       pin the batch sequence number; default auto
#                                 = max sequence found in the base order
#                                 book plus one (one shared batch number for
#                                 the whole insertion, the batch-anchor form
#                                 the registries already use).
#   --out DIR                     draft destination; under --apply the two
#                                 regenerated books are written as
#                                 DIR/order.txt and DIR/_CoqProject (the
#                                 contribution-side registry pair).  --apply
#                                 requires --out (no in-place default, no
#                                 implicit overwrite).  The draft contains
#                                 the base books plus exactly the --pieces
#                                 rows: pass the full contribution piece
#                                 list.  The previous books stay recoverable
#                                 from the contribution ref via git show.
#   --json P                      report target, schema
#                                 rocqwash-registry-regen/1; on any failure
#                                 nothing is written, including P.
#
# Per-piece status resolution (first match wins)
#   already-in-base  the piece's bare name is registered in either base
#                    book; no row is generated (the base row stands); the
#                    base blob is compared against the entity when both are
#                    reachable and the comparison is recorded as evidence.
#   blocked          the entity is missing under --anchor-src, or an
#                    external dependency is unregistered in base books and
#                    contribution surface (dep-unregistered), or registered
#                    on the contribution surface but outside --pieces
#                    (dep-registered-on-contribution-outside-pieces), or a
#                    set dependency is itself blocked (dep-blocked
#                    cascade).  Blocked pieces are listed with reasons and
#                    generate no rows; the exit code stays 0 (findings are
#                    data).
#   inserted         entity present, dependencies satisfied; rows generated
#                    in dependency order.
#
# Same-source assertions (engine imported from tools/registry_union.py; the
# books' key and anchor forms are that tool's, not re-implementations)
#   order book     internal key uniqueness of the new rows; new keys absent
#                  from the base order keys; anchor-text duplicate-pair
#                  count of the draft not above the base baseline.
#   project book   internal key uniqueness; new keys absent from the base
#                  project keys (project rows carry no anchors, so the
#                  anchor-text assertion is order-book only).
#   entity-blob    for each inserted piece registered on the contribution
#                  surface, the entity md5 must equal the md5 of the blob at
#                  contrib-ref (a stale materialization fails loud before
#                  any row exists); divergence for an already-in-base piece
#                  is recorded, not fatal, since no row is generated for it.
#
# Determinism and write isolation: no timestamps; the only environment reads
# are git and the selected dependency source (recorded in the report); same
# input reruns byte-identical; the write surface under --apply is exactly the
# two --out book paths plus the explicit --json path; a dry run and every
# failure path write nothing.  Line endings and the final newline of each
# draft book follow its base book.

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
try:
    import registry_union as _ru  # noqa: E402  (engine import; never modified)
except Exception as _e:  # pragma: no cover
    print("FAIL-LOUD: sibling tools/registry_union.py not importable "
          "(key/anchor/assertion engine dependency): %s" % _e,
          file=sys.stderr)
    sys.exit(9)

PROG = "registry_regen"
SCHEMA = "rocqwash-registry-regen/1"

KIND_ORDER = _ru.KIND_ORDER
KIND_COQPROJECT = _ru.KIND_COQPROJECT

GIT_PATH_ORDER_DEFAULT = "order.txt"
GIT_PATH_PROJECT_DEFAULT = "_CoqProject"

DEP_SOURCES = ("require", "coqdep", "registry", "auto")
DEP_SOURCE_DEFAULT = "require"

# Require-surface parse: one sentence per line, trailing comments stripped;
# From-forms consumed; the last component of each qualified identifier is the
# dependency token matched against piece bare names.  Lenient by design: an
# unparsed line yields no edge, the registry tiebreak governs, and the parsed
# set is recorded per piece in the report.
RE_LINE_COMMENT = re.compile(r"\(\*.*?\*\)")
RE_REQUIRE = re.compile(
    r"^\s*(?:From\s+[A-Za-z_][\w']*\s+)?"
    r"Require\b"
    r"(?:\s+(?:Import|Export)\b)*"
    r"\s+(?P<qualids>[A-Za-z_][\w']*(?:\.[A-Za-z_][\w']*)*"
    r"(?:\s+[A-Za-z_][\w']*(?:\.[A-Za-z_][\w']*)*)*)"
    r"\s*\.\s*$")
RE_SEQ_NUM = re.compile(r"^#R(\d+)")

STATUS_INSERTED = "inserted"
STATUS_ALREADY = "already-in-base"
STATUS_BLOCKED = "blocked"

BLOCK_ENTITY_MISSING = "entity-missing"
BLOCK_DEP_UNREGISTERED = "dep-unregistered"
BLOCK_DEP_OUTSIDE_PIECES = "dep-registered-on-contribution-outside-pieces"
BLOCK_DEP_BLOCKED = "dep-blocked"

NO_INDEX = 1 << 30  # tiebreak sentinel for pieces absent from a book


class UsageError(Exception):
    """Usage error (exit 2)."""


# ---------- small helpers ----------

def dump_json(path, obj):
    """Deterministic JSON write (sort_keys, indent=1; registry_audit form)."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def md5_of_bytes(data):
    """Full md5 hex of bytes (entity-blob cross-check basis)."""
    return hashlib.md5(data).hexdigest()


def md5_of_file(path):
    """Full md5 hex of a file (the value the blob side must reproduce)."""
    h = hashlib.md5()
    with io.open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def base_component(key):
    """Order-book key -> module name (strip .v, last path component)."""
    return _ru.bare_name(key).rsplit("/", 1)[-1]


def parse_pieces(raw):
    """--pieces value -> (deduplicated bare-name list keep-first, dropped)."""
    names, seen, dropped = [], set(), []
    for part in (raw or "").split(","):
        n = _ru.bare_name(part)
        if not n:
            continue
        if n in seen:
            dropped.append(n)
            continue
        seen.add(n)
        names.append(n)
    return names, sorted(set(dropped))


def parse_requires(text):
    """Source text -> sorted list of required last components."""
    deps = set()
    for line in text.splitlines():
        work = RE_LINE_COMMENT.sub(" ", line)
        m = RE_REQUIRE.match(work)
        if m is None:
            continue
        for qualid in m.group("qualids").split():
            last = qualid.rsplit(".", 1)[-1]
            if last:
                deps.add(last)
    return sorted(deps)


def base_max_seq(order_lines):
    """Max sequence number across base order-book anchors (0 when none)."""
    best = 0
    for ln in order_lines:
        tok = _ru.anchor_of(ln)
        if tok is None:
            continue
        m = RE_SEQ_NUM.match(tok)
        if m:
            best = max(best, int(m.group(1)))
    return best


def first_row_by_name(lines, kind, name):
    """First row whose key matches the piece name -> (key, row or None)."""
    for ln in lines:
        k = _ru.key_of(ln, kind)
        if k is None:
            continue
        probe = k if kind == KIND_COQPROJECT else base_component(k)
        if probe == name:
            return k, ln
    return None, None


def book_module_set(order_lines, project_lines):
    """Module names a book registers (order base components + project keys)."""
    mods = set()
    for ln in order_lines:
        k = _ru.key_of(ln, KIND_ORDER)
        if k is not None:
            mods.add(base_component(k))
    for ln in project_lines:
        k = _ru.key_of(ln, KIND_COQPROJECT)
        if k is not None:
            mods.add(k)
    return mods


def git_read_text(repo, ref, path, what):
    """git show repo@ref:path as text; missing/failing is exit 9."""
    cmd = ["git", "-C", repo, "show", "%s:%s" % (ref, path)]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    except OSError as e:
        raise _ru.MissingInput("%s: git unavailable: %s" % (what, e))
    if p.returncode != 0:
        raise _ru.MissingInput(
            "%s: git show failed rc=%d for %s@%s:%s\n%s"
            % (what, p.returncode, repo, ref, path,
               p.stderr.decode("utf-8", errors="replace").strip()))
    return p.stdout.decode("utf-8")


def git_show_bytes(repo, ref, path):
    """git show as bytes, or None when unreadable (evidence probes only;
    book reads use git_read_text which fails loud)."""
    cmd = ["git", "-C", repo, "show", "%s:%s" % (ref, path)]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    except OSError:
        return None
    if p.returncode != 0:
        return None
    return p.stdout


def read_book(repo, ref, path, what):
    """Book at repo@ref -> (lines, text); lines via the engine's reader."""
    text = git_read_text(repo, ref, path, what)
    return _ru.read_side_text(text, what), text


# ---------- dependency order ----------

def dep_satisfaction(pieces, entities, piece_set):
    """Require-parse edges and external components for every piece (the
    uniform satisfaction basis: BLOCK reasons, cascade, cycle detection)."""
    edges, ext = {}, {}
    for p in pieces:
        comps = parse_requires(entities[p]["text"])
        in_set = sorted({c for c in comps if c in piece_set and c != p})
        out_set = sorted({c for c in comps if c not in piece_set and c != p})
        edges[p] = in_set
        ext[p] = out_set
    return edges, ext


def dep_edges_coqdep(pieces, entities, anchor_src):
    """coqdep order edges (best effort, provenance recorded): run the
    coqdep binary on the piece entities and map .vo targets back to their
    .v sources; only intra-set edges by base name are used; output that
    names no piece yields no edge and the registry tiebreak governs."""
    binary = shutil.which("coqdep")
    if binary is None:
        raise _ru.MissingInput("coqdep not on PATH (--dep-source coqdep)")
    rels = [entities[p]["rel"] for p in pieces]
    try:
        p = subprocess.run([binary] + rels, cwd=anchor_src,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as e:
        raise UsageError("coqdep run failed: %s" % e)
    if p.returncode != 0:
        raise UsageError("coqdep run failed rc=%d: %s"
                         % (p.returncode,
                            p.stderr.decode("utf-8",
                                            errors="replace")[-400:]))
    by_source = {}
    for piece in pieces:
        by_source[os.path.basename(entities[piece]["rel"])] = piece
    edges = {piece: set() for piece in pieces}
    out = p.stdout.decode("utf-8", errors="replace")
    for line in out.splitlines():
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        src = None
        for tok in left.split():
            if tok.endswith(".vo"):
                cand = by_source.get(os.path.basename(tok[:-3] + ".v"))
                if cand is not None:
                    src = cand
                    break
        if src is None:
            continue
        for tok in right.split():
            dep = by_source.get(os.path.basename(tok))
            if dep is not None and dep != src:
                edges[src].add(dep)
    return {piece: sorted(v) for piece, v in edges.items()}


def topo_order(pieces, edges, tiebreak):
    """Kahn topological sort; ready nodes emitted in tiebreak order (the
    contribution registry's row index, then the --pieces order, then the
    name); a cycle fails loud with the member list."""
    remaining = {p: deps for p, deps in edges.items() if p in set(pieces)}
    placed, order = set(), []
    while remaining:
        ready = [p for p, deps in remaining.items()
                 if all(d in placed for d in deps)]
        if not ready:
            cyc = sorted(remaining)
            raise _ru.AssertBlast(
                "DEP-CYCLE",
                ["dependency cycle among pieces: %s" % ",".join(cyc),
                 "residual edges: %s" % "; ".join(
                     "%s->%s" % (p, ",".join(remaining[p]))
                     for p in cyc if remaining[p])])
        ready.sort(key=lambda p: tiebreak.get(p, (NO_INDEX, NO_INDEX, p)))
        for p in ready:
            order.append(p)
            placed.add(p)
            remaining.pop(p)
    return order


# ---------- per-piece classification ----------

def classify_pieces(pieces, base_mods, contrib_mods, base_order_lines,
                    base_project_lines, entities, sat_edges, ext):
    """Resolve each piece to already-in-base / blocked / insertable with the
    deterministic reason precedence: entity-missing, dep-unregistered /
    dep-outside-pieces, dep-blocked (cascade fixpoint); already-in-base is
    resolved from the base books independently of dependencies."""
    blocked = {}
    for p in pieces:
        if entities[p]["path"] is None:
            blocked[p] = (BLOCK_ENTITY_MISSING, [],
                          "no %s.v entity under --anchor-src" % p)
    changed = True
    while changed:
        changed = False
        for p in pieces:
            if p in blocked:
                continue
            missing, outside = [], []
            for c in ext.get(p, []):
                if c in base_mods:
                    continue
                if c in contrib_mods:
                    outside.append(c)
                else:
                    missing.append(c)
            if missing:
                blocked[p] = (BLOCK_DEP_UNREGISTERED, sorted(set(missing)),
                              "Require %s unregistered in base books and "
                              "contribution surface"
                              % ",".join(sorted(set(missing))))
                changed = True
                continue
            if outside:
                blocked[p] = (BLOCK_DEP_OUTSIDE_PIECES, sorted(set(outside)),
                              "Require %s registered on the contribution "
                              "surface but not among --pieces (the draft "
                              "would not carry it)"
                              % ",".join(sorted(set(outside))))
                changed = True
                continue
            for q in sat_edges.get(p, []):
                if q in blocked:
                    blocked[p] = (BLOCK_DEP_BLOCKED, [q],
                                  "set dependency %s is blocked (%s)"
                                  % (q, blocked[q][0]))
                    changed = True
                    break
    records = {}
    for p in pieces:
        ent = entities[p]
        rec = {
            "piece": p,
            "status": STATUS_INSERTED,
            "entity": ent["path"],
            "entity_rel": ent["rel"],
            "deps_in_set": sat_edges.get(p, []),
            "ext_deps": ext.get(p, []),
            "order_row": None,
            "project_row": None,
            "key": None,
            "md5_8": None,
            "seq": None,
            "blocked_code": None,
            "blocked_reason": None,
            "missing_deps": [],
            "base_blob": None,
            "contrib_blob": None,
        }
        if p in blocked:
            code, missing, reason = blocked[p]
            rec["status"] = STATUS_BLOCKED
            rec["blocked_code"] = code
            rec["blocked_reason"] = reason
            rec["missing_deps"] = missing
        else:
            bkey, _ = first_row_by_name(base_order_lines, KIND_ORDER, p)
            _k, bproj = first_row_by_name(base_project_lines,
                                          KIND_COQPROJECT, p)
            if bkey is not None or bproj is not None:
                rec["status"] = STATUS_ALREADY
        records[p] = rec
    return records


def compare_blob(repo, ref, candidates, entity_path):
    """Compare an entity file against repo@ref blobs at the candidate paths;
    first readable candidate wins; status in same | diverged | unreadable |
    skipped (entity absent)."""
    if entity_path is None:
        return {"status": "skipped", "path": None,
                "note": "entity missing under --anchor-src"}
    entity_md5 = md5_of_file(entity_path)
    for cand in candidates:
        if not cand:
            continue
        blob = git_show_bytes(repo, ref, cand)
        if blob is None:
            continue
        blob_md5 = md5_of_bytes(blob)
        return {"status": "same" if blob_md5 == entity_md5 else "diverged",
                "path": cand, "entity_md5": entity_md5,
                "blob_md5": blob_md5}
    return {"status": "unreadable", "path": None,
            "note": "no candidate path readable at the ref",
            "entity_md5": entity_md5}


# ---------- row build ----------

def build_rows(insert_order, records, contrib_order_lines,
               contrib_project_lines, entities, batch_seq):
    """Canonical rows for the inserted pieces: order key from the
    contribution order book's existing key for the piece (first occurrence,
    its own path form preserved) or the entity relative path; project row
    from the contribution project book's existing row or the same relative
    path; the batch sequence is shared by the whole insertion."""
    new_order, new_project = [], []
    for p in insert_order:
        ent_rel = entities[p]["rel"]
        key, _ = first_row_by_name(contrib_order_lines, KIND_ORDER, p)
        if key is None:
            key = ent_rel
        _pk, prow = first_row_by_name(contrib_project_lines,
                                      KIND_COQPROJECT, p)
        proj_row = prow if prow is not None else ent_rel
        md5_8 = _ru.md5_8_of(entities[p]["path"])
        order_row = "%s#R%d-%s" % (key, batch_seq, md5_8)
        rec = records[p]
        rec["key"] = key
        rec["order_row"] = order_row
        rec["project_row"] = proj_row
        rec["md5_8"] = md5_8
        rec["seq"] = batch_seq
        new_order.append(order_row)
        new_project.append(proj_row)
    return new_order, new_project


# ---------- main flow ----------

def run_regen(args):
    """Regen main flow -> report dict (raises MissingInput/UsageError/
    AssertBlast; zero writes on any failure)."""
    pieces, dropped = parse_pieces(args.pieces)
    if not pieces:
        raise UsageError("--pieces parses to no piece names")
    if not os.path.isdir(args.base_repo):
        raise _ru.MissingInput("--base-repo directory missing: %s"
                               % args.base_repo)
    if not os.path.isdir(args.contrib_repo):
        raise _ru.MissingInput("--contrib-repo directory missing: %s"
                               % args.contrib_repo)
    if not os.path.isdir(args.anchor_src):
        raise _ru.MissingInput("--anchor-src directory missing: %s"
                               % args.anchor_src)

    base_order_path = args.base_path_order or GIT_PATH_ORDER_DEFAULT
    base_project_path = args.base_path_project or GIT_PATH_PROJECT_DEFAULT
    contrib_order_path = args.contrib_path_order or GIT_PATH_ORDER_DEFAULT
    contrib_project_path = (args.contrib_path_project
                            or GIT_PATH_PROJECT_DEFAULT)

    base_order_lines, base_order_text = read_book(
        args.base_repo, args.base_ref, base_order_path, "base order book")
    base_project_lines, base_project_text = read_book(
        args.base_repo, args.base_ref, base_project_path,
        "base project book")
    contrib_order_lines, _t = read_book(
        args.contrib_repo, args.contrib_ref, contrib_order_path,
        "contribution order book")
    contrib_project_lines, _t2 = read_book(
        args.contrib_repo, args.contrib_ref, contrib_project_path,
        "contribution project book")
    order_eol, order_final_nl = _ru.detect_eol(
        base_order_text.encode("utf-8"))
    project_eol, project_final_nl = _ru.detect_eol(
        base_project_text.encode("utf-8"))

    # entity resolution: unique <name>.v under --anchor-src (engine
    # semantics: ambiguity fails loud, absence yields None -> BLOCK)
    entities = {}
    for p in pieces:
        try:
            ent = _ru.resolve_entity(p, args.anchor_src)
        except _ru.UsageError as e:
            raise UsageError("entity ambiguity for piece %s: %s" % (p, e))
        rel = None
        text = ""
        if ent is not None:
            rel = os.path.relpath(ent, args.anchor_src).replace(os.sep, "/")
            with io.open(ent, "r", encoding="utf-8",
                         errors="replace") as fh:
                text = fh.read()
        entities[p] = {"path": ent, "rel": rel, "text": text}

    base_mods = book_module_set(base_order_lines, base_project_lines)
    contrib_mods = book_module_set(contrib_order_lines, contrib_project_lines)
    piece_set = set(pieces)

    # satisfaction basis is always the Require parse; the order source is
    # selected (--dep-source) and recorded
    sat_edges, ext = dep_satisfaction(pieces, entities, piece_set)
    requested = args.dep_source
    effective = requested
    if requested == "auto":
        effective = "coqdep" if shutil.which("coqdep") else "require"

    records = classify_pieces(pieces, base_mods, contrib_mods,
                              base_order_lines, base_project_lines,
                              entities, sat_edges, ext)
    insertable = [p for p in pieces if records[p]["status"] == STATUS_INSERTED]

    contrib_row_index = {}
    for idx, ln in enumerate(contrib_order_lines):
        k = _ru.key_of(ln, KIND_ORDER)
        if k is not None and k not in contrib_row_index:
            contrib_row_index[k] = idx
    tiebreak = {}
    for p in pieces:
        k, _ = first_row_by_name(contrib_order_lines, KIND_ORDER, p)
        cidx = contrib_row_index.get(k, NO_INDEX) if k else NO_INDEX
        tiebreak[p] = (cidx, pieces.index(p), p)

    # cycle detection on the satisfaction edges in every mode (a cyclic
    # Require surface admits no valid registration regardless of the order
    # source); require mode then uses the same edges as the order
    ins_set = set(insertable)
    sat_edges_ins = {p: [d for d in sat_edges.get(p, []) if d in ins_set]
                     for p in insertable}
    if effective == "require":
        insert_order = topo_order(insertable, sat_edges_ins, tiebreak)
    elif effective == "coqdep":
        topo_order(insertable, sat_edges_ins, tiebreak)  # cycle check
        coq_edges = dep_edges_coqdep(pieces, entities, args.anchor_src)
        coq_ins = {p: [d for d in coq_edges.get(p, []) if d in ins_set]
                   for p in insertable}
        insert_order = topo_order(insertable, coq_ins, tiebreak)
    else:  # registry: the contribution registry's existing row order
        topo_order(insertable, sat_edges_ins, tiebreak)  # cycle check
        insert_order = sorted(insertable, key=lambda p: tiebreak[p])

    # entity-blob cross-check for inserted pieces (stale materialization
    # fails loud before any row exists)
    for p in insert_order:
        ckey, _ = first_row_by_name(contrib_order_lines, KIND_ORDER, p)
        _k2, cproj = first_row_by_name(contrib_project_lines,
                                       KIND_COQPROJECT, p)
        records[p]["contrib_blob"] = compare_blob(
            args.contrib_repo, args.contrib_ref, [cproj, ckey],
            entities[p]["path"])
        cb = records[p]["contrib_blob"]
        if cb["status"] == "diverged":
            raise _ru.AssertBlast(
                "ENTITY-BLOB-DIVERGED",
                ["piece %s: entity md5 %s under --anchor-src diverges from "
                 "the blob at %s:%s (md5 %s) - stale materialization, "
                 "re-materialize byte-faithfully"
                 % (p, cb["entity_md5"], args.contrib_ref, cb["path"],
                    cb["blob_md5"])])

    # already-in-base evidence: base blob vs entity (data, never fatal)
    for p in pieces:
        if records[p]["status"] != STATUS_ALREADY:
            continue
        _k, bproj = first_row_by_name(base_project_lines,
                                      KIND_COQPROJECT, p)
        bkey, _r = first_row_by_name(base_order_lines, KIND_ORDER, p)
        records[p]["base_blob"] = compare_blob(
            args.base_repo, args.base_ref, [bproj, bkey],
            entities[p]["path"])

    if args.seq is not None:
        batch_seq, seq_mode, base_seq_seen = args.seq, "pinned", None
    else:
        base_seq_seen = base_max_seq(base_order_lines)
        batch_seq, seq_mode = base_seq_seen + 1, "auto"
    new_order, new_project = build_rows(
        insert_order, records, contrib_order_lines, contrib_project_lines,
        entities, batch_seq)

    draft_order = list(base_order_lines) + new_order
    draft_project = list(base_project_lines) + new_project

    # same-source assertions (registry_union engine, unmodified)
    _ru.assert_internal_key_unique(new_order, KIND_ORDER)
    _ru.assert_added_keys_not_in_main(new_order, base_order_lines, KIND_ORDER)
    _ru.assert_anchor_no_new_dups(draft_order, base_order_lines)
    _ru.assert_internal_key_unique(new_project, KIND_COQPROJECT)
    _ru.assert_added_keys_not_in_main(new_project, base_project_lines,
                                      KIND_COQPROJECT)

    report = {
        "schema": SCHEMA,
        "mode": "APPLY" if args.apply else "DRY-RUN",
        "inputs": {
            "base_repo": args.base_repo, "base_ref": args.base_ref,
            "contrib_repo": args.contrib_repo,
            "contrib_ref": args.contrib_ref,
            "anchor_src": args.anchor_src,
            "pieces": pieces,
            "pieces_duplicates_dropped": dropped,
            "dep_source_requested": requested,
            "dep_source": effective,
            "seq_request": args.seq,
            "base_path_order": base_order_path,
            "base_path_project": base_project_path,
            "contrib_path_order": contrib_order_path,
            "contrib_path_project": contrib_project_path,
            "out": args.out,
        },
        "seq": {"mode": seq_mode, "base_max_seq": base_seq_seen,
                "batch_seq": batch_seq},
        "books": {
            "base_order_rows": len(base_order_lines),
            "base_project_rows": len(base_project_lines),
            "contrib_order_rows": len(contrib_order_lines),
            "contrib_project_rows": len(contrib_project_lines),
            "draft_order_rows": len(draft_order),
            "draft_project_rows": len(draft_project),
            "new_order_rows": len(new_order),
            "new_project_rows": len(new_project),
            "eol": {"order": order_eol, "project": project_eol},
        },
        "pieces": [records[p] for p in pieces],
        "insert_order": insert_order,
        "new_rows": {"order": new_order, "project": new_project},
        "assertions": {
            "order_internal_key_unique": "PASS",
            "order_new_keys_not_in_base": "PASS",
            "order_anchor_text_no_new_dups": "PASS",
            "project_internal_key_unique": "PASS",
            "project_new_keys_not_in_base": "PASS",
        },
        "writes": None,
    }

    if not args.apply:
        return report

    os.makedirs(args.out, exist_ok=True)
    order_path = os.path.join(args.out, GIT_PATH_ORDER_DEFAULT)
    project_path = os.path.join(args.out, GIT_PATH_PROJECT_DEFAULT)
    payload_order = _ru.render_output(draft_order, order_eol, order_final_nl)
    payload_project = _ru.render_output(draft_project, project_eol,
                                        project_final_nl)
    try:
        with io.open(order_path, "wb") as fh:
            fh.write(payload_order)
        with io.open(project_path, "wb") as fh:
            fh.write(payload_project)
    except OSError as e:
        raise _ru.AssertBlast("WRITE-FAILED",
                              ["--out write failed: %s" % e])
    if md5_of_file(order_path) != md5_of_bytes(payload_order) \
            or md5_of_file(project_path) != md5_of_bytes(payload_project):
        raise _ru.AssertBlast("WRITE-INTEGRITY",
                              ["draft book on disk differs from the staged "
                               "render (write integrity failure)"])
    report["writes"] = [
        {"book": "order", "path": order_path,
         "md5": md5_of_bytes(payload_order), "rows": len(draft_order)},
        {"book": "project", "path": project_path,
         "md5": md5_of_bytes(payload_project), "rows": len(draft_project)},
    ]
    return report


def print_stdout(rep):
    """Loud stdout report (deterministic; no timestamps)."""
    inp = rep["inputs"]
    print("=== REGISTRY-REGEN (%s, %s) ===" % (rep["mode"], SCHEMA))
    print("  base: %s @ %s (order=%s project=%s)"
          % (inp["base_repo"], inp["base_ref"], inp["base_path_order"],
             inp["base_path_project"]))
    print("  contrib: %s @ %s (order=%s project=%s)"
          % (inp["contrib_repo"], inp["contrib_ref"],
             inp["contrib_path_order"], inp["contrib_path_project"]))
    print("  anchor_src=%s" % inp["anchor_src"])
    print("  dep_source=%s (requested %s) | seq=%s (mode %s)"
          % (inp["dep_source"], inp["dep_source_requested"],
             rep["seq"]["batch_seq"], rep["seq"]["mode"]))
    if inp["pieces_duplicates_dropped"]:
        print("  pieces duplicates collapsed: %s"
              % ",".join(inp["pieces_duplicates_dropped"]))
    bk = rep["books"]
    print("books: base order=%d project=%d | contrib order=%d project=%d"
          % (bk["base_order_rows"], bk["base_project_rows"],
             bk["contrib_order_rows"], bk["contrib_project_rows"]))
    statuses = {}
    for rec in rep["pieces"]:
        statuses[rec["status"]] = statuses.get(rec["status"], 0) + 1
    print("pieces (%d): %s" % (
        len(rep["pieces"]),
        " ".join("%s=%d" % (k, statuses[k]) for k in sorted(statuses))))
    for rec in rep["pieces"]:
        if rec["status"] == STATUS_INSERTED:
            print("  + %s | project row %s | md5_8=%s | deps_in_set=[%s]"
                  % (rec["order_row"], rec["project_row"], rec["md5_8"],
                     ",".join(rec["deps_in_set"])))
        elif rec["status"] == STATUS_ALREADY:
            bb = rec["base_blob"] or {}
            print("  = %s already-in-base (base blob %s)"
                  % (rec["piece"], bb.get("status", "unknown")))
        else:
            print("  ! %s BLOCK %s: %s"
                  % (rec["piece"], rec["blocked_code"],
                     rec["blocked_reason"]))
    print("draft: order %d+%d=%d rows | project %d+%d=%d rows"
          % (bk["base_order_rows"], bk["new_order_rows"],
             bk["draft_order_rows"], bk["base_project_rows"],
             bk["new_project_rows"], bk["draft_project_rows"]))
    print("assertions: " + " ".join(
        "%s=%s" % (k, v) for k, v in sorted(rep["assertions"].items())))
    if rep["writes"] is not None:
        for w in rep["writes"]:
            print("write: %s rows=%d md5=%s"
                  % (w["path"], w["rows"], w["md5"]))
    elif inp["out"] is not None:
        print("out -> %s (dry run: nothing written)" % inp["out"])


# ---------- selftest ----------

def selftest():
    """Embedded vectors (temporary fixtures, no real repository, no network,
    no compilation):

    0  pure functions without git: Require parse forms, topological order
       with registry tiebreak, batch-sequence extraction, frozen md5 vector,
       pieces parsing
    1  three-piece topological regeneration end to end (two temporary git
       repositories plus a materialized tree), schema and byte-identical
       rerun
    2  BLOCK family: dependency unregistered in base and contribution,
       dependency registered on the contribution but outside --pieces,
       cascade through a blocked dependency
    3  frozen md5 vector end to end ("module A content alpha" -> 77c2b9a8)
    4  dry-run zero-write, then --apply writes both books byte-faithfully
       (CRLF base book preserved), already-in-base skip with blob-same
       evidence, idempotent rerun
    5  blast family: identical-content pair (anchor-text new duplicate),
       entity-blob divergence, dependency cycle - all exit 2 with zero
       writes
    6  dep-source=registry order, dep-source=coqdep exit 9 when the binary
       is absent (honestly skipped when present)
    7  CLI exit codes (help 0, bogus 2, no input 2, apply without out 2,
       empty pieces 2, missing repo 9, bad ref 9, missing anchor-src 9,
       missing contribution book 9, negative seq 2) and pinned sequence
    """
    import tempfile

    here = os.path.dirname(os.path.abspath(__file__))
    regen_py = os.path.join(here, PROG + ".py")

    def run(argv):
        p = subprocess.run([sys.executable, "-B", regen_py] + argv,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def wf(path, text, eol="\n"):
        data = text.replace("\n", eol).encode("utf-8")
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        with io.open(path, "wb") as fh:
            fh.write(data)
        return path

    def rd(path):
        with io.open(path, "rb") as fh:
            return fh.read()

    def tree_md5(root):
        rows = []
        for dirpath, _dirs, fnames in os.walk(root):
            for fn in sorted(fnames):
                p = os.path.join(dirpath, fn)
                rows.append((os.path.relpath(p, root), md5_of_file(p)))
        return sorted(rows)

    tmp = tempfile.mkdtemp(prefix="rocqwash_rr_self_")
    try:
        # ---- vector 0: pure functions (no git needed) ----
        deps = parse_requires(
            "Require Import A.B.\n"
            "From Util Require Import P3.\n"
            "Require P3 C.D.\n"
            "(* Require Import NotARequire. *)\n"
            "Definition x := 1.\n")
        assert deps == ["B", "D", "P3"], deps
        assert parse_requires("Require Import MissingPeriod\n") == []
        tieb = {"P1": (5, 0, "P1"), "P2": (9, 1, "P2"), "P3": (2, 2, "P3")}
        assert topo_order(["P1", "P2", "P3"],
                          {"P1": ["P2"], "P2": ["P3"], "P3": []},
                          tieb) == ["P3", "P2", "P1"]
        tieb2 = {"P1": (NO_INDEX, 0, "P1"), "P2": (NO_INDEX, 1, "P2")}
        assert topo_order(["P1", "P2"], {"P1": [], "P2": []},
                          tieb2) == ["P1", "P2"]
        assert base_max_seq(["A.v#R0-11111111", "B.v#R0-22222222",
                             "C.v#R3-abcabcab"]) == 3
        assert base_max_seq(["A.v", "# comment"]) == 0
        assert base_max_seq(["A.v#R152-TBR880", "B.v#R43a003"]) == 152
        d0 = os.path.join(tmp, "vec0")
        os.makedirs(d0)
        wf(os.path.join(d0, "ToyA.v"), "module A content alpha\n")
        assert _ru.md5_8_of(os.path.join(d0, "ToyA.v")) == "77c2b9a8"
        names, dropped = parse_pieces("P1, P2.v ,,P1,P3")
        assert names == ["P1", "P2", "P3"] and dropped == ["P1"], \
            (names, dropped)
        print("  [0/8] pure functions OK (require forms, topo tiebreak, "
              "seq extraction, 77c2b9a8, pieces parse)")

        if shutil.which("git") is None:
            print("  [1/8..7/8] SKIP (git not on PATH; vectors 1-7 need "
                  "temporary git repositories - honest skip, not a pass)")
            print("REGISTRY-REGEN-SELFTEST PASS: pure-function vector only; "
                  "git-gated vectors skipped")
            return 0

        # ---- fixture: two temporary git repositories + materialized tree ----
        env = dict(os.environ)
        env.update({"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
                    "GIT_AUTHOR_DATE": "2026-11-11T00:00:00 +0000",
                    "GIT_COMMITTER_DATE": "2026-11-11T00:00:00 +0000"})
        # Pin the scratch repositories to autocrlf=false for every git call:
        # the CRLF-preservation vector below is about the tool's own byte
        # discipline, not about the host's core.autocrlf. On a Windows host
        # with autocrlf=true the CRLF base books get normalized to LF on
        # commit, so the vector fails for a reason that has nothing to do
        # with the tool (injected config, not the repo's own settings).
        env.update({"GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "core.autocrlf",
                    "GIT_CONFIG_VALUE_0": "false"})

        def git(repo, *a):
            p = subprocess.run(["git", "-C", repo] + list(a), env=env,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            assert p.returncode == 0, (a, p.stdout)
            return p.stdout.decode("utf-8", errors="replace").strip()

        base_repo = os.path.join(tmp, "base_repo")
        contrib_repo = os.path.join(tmp, "contrib_repo")
        anchor = os.path.join(tmp, "contrib_tree")
        os.makedirs(base_repo)
        os.makedirs(contrib_repo)

        base_body = {"BaseA.v": "BaseA module body\n",
                     "BaseB.v": "BaseB module body\n",
                     "Cmain.v": "Cmain module body\n"}
        contrib_body = {
            "P1.v": "Require Import BaseA.\nRequire Import P2.\n"
                    "Require P3.\n(* P1 body *)\n",
            "P2.v": "From Util Require Import P3.\n(* P2 body *)\n",
            "P3.v": "(* P3 leaf, no requires *)\n",
            "Bdep.v": "(* registered on the contribution, not selected *)\n",
            "FrozenA.v": "module A content alpha\n",
            "Blocker.v": "Require Import GhostMod.\n",
            "Blockee.v": "Require Import Blocker.\n",
            "TwA.v": "identical content pair member A\n",
            "TwB.v": "identical content pair member A\n",
            "CycA.v": "Require Import CycB.\n",
            "CycB.v": "Require Import CycA.\n",
            "BaseA.v": "BaseA module body\n",
        }
        contrib_order_rows = [
            "P1.v#R7-aaaaaaaa", "P2.v#R7-bbbbbbbb", "P3.v#R7-cccccccc",
            "Bdep.v#R6-dddddddd", "FrozenA.v#R6-eeeeeeee",
            "Blocker.v#R5-ffffffff", "Blockee.v#R5-ffffffff",
            "TwA.v#R5-ffffffff", "TwB.v#R5-ffffffff",
            "CycA.v#R4-ffffffff", "CycB.v#R4-ffffffff",
            "BaseA.v#R3-99999999",
        ]
        contrib_project_rows = ["-Q . \"\""] + [r.split("#", 1)[0]
                                                for r in contrib_order_rows]

        git(base_repo, "init")
        base_branch = git(base_repo, "symbolic-ref", "--short", "HEAD")
        for name, body in sorted(base_body.items()):
            wf(os.path.join(base_repo, name), body)
        base_order_rows = ["BaseA.v#R0-11111111", "BaseB.v#R0-22222222",
                           "Cmain.v#R0-33333333"]
        wf(os.path.join(base_repo, "order.txt"),
           "\n".join(base_order_rows) + "\n")
        wf(os.path.join(base_repo, "_CoqProject"),
           '-Q . ""\n' + "\n".join(r.split("#", 1)[0]
                                   for r in base_order_rows) + "\n")
        git(base_repo, "add", ".")
        git(base_repo, "commit", "-m", "base books")

        git(contrib_repo, "init")
        contrib_branch = git(contrib_repo, "symbolic-ref", "--short", "HEAD")
        for name, body in sorted(contrib_body.items()):
            wf(os.path.join(contrib_repo, name), body)
        wf(os.path.join(contrib_repo, "order.txt"),
           "\n".join(contrib_order_rows) + "\n")
        wf(os.path.join(contrib_repo, "_CoqProject"),
           "\n".join(contrib_project_rows) + "\n")
        git(contrib_repo, "add", ".")
        git(contrib_repo, "commit", "-m", "contribution surface")

        for name in sorted(contrib_body):
            wf(os.path.join(anchor, name), contrib_body[name])

        md5p = {n: _ru.md5_8_of(os.path.join(anchor, n + ".v"))
                for n in ("P1", "P2", "P3")}
        J = ["--base-repo", base_repo, "--base-ref", base_branch,
             "--contrib-repo", contrib_repo, "--contrib-ref", contrib_branch,
             "--anchor-src", anchor]

        # ---- vector 1: three-piece topological regeneration ----
        d1 = os.path.join(tmp, "vec1")
        os.makedirs(d1)
        j1 = os.path.join(d1, "r.json")
        p = run(J + ["--pieces", "P1,P2,P3", "--json", j1])
        assert p.returncode == 0, p.stdout
        rep = json.load(io.open(j1, encoding="utf-8"))
        assert rep["schema"] == SCHEMA, rep["schema"]
        assert rep["insert_order"] == ["P3", "P2", "P1"], rep["insert_order"]
        assert rep["seq"] == {"mode": "auto", "base_max_seq": 0,
                              "batch_seq": 1}, rep["seq"]
        assert rep["new_rows"]["order"] == [
            "P3.v#R1-%s" % md5p["P3"], "P2.v#R1-%s" % md5p["P2"],
            "P1.v#R1-%s" % md5p["P1"]], rep["new_rows"]["order"]
        assert rep["new_rows"]["project"] == ["P3.v", "P2.v", "P1.v"], \
            rep["new_rows"]["project"]
        assert rep["books"]["draft_order_rows"] == 6, rep["books"]
        assert rep["books"]["draft_project_rows"] == 7, rep["books"]
        assert rep["inputs"]["dep_source"] == "require", rep["inputs"]
        assert all(v == "PASS" for v in rep["assertions"].values()), \
            rep["assertions"]
        assert all(r["contrib_blob"]["status"] == "same"
                   for r in rep["pieces"]
                   if r["status"] == STATUS_INSERTED), rep["pieces"]
        before = rd(j1)
        p = run(J + ["--pieces", "P1,P2,P3", "--json", j1])
        assert p.returncode == 0 and rd(j1) == before, "json drift"
        print("  [1/8] three-piece topological regen OK (P3,P2,P1 despite "
              "registry order P1,P2,P3; batch seq 1; blob cross-check same; "
              "schema; rerun byte-identical)")

        # ---- vector 2: BLOCK family ----
        j2 = os.path.join(d1, "r2.json")
        p = run(J + ["--pieces", "Blocker,Blockee", "--json", j2])
        assert p.returncode == 0, p.stdout
        rep2 = json.load(io.open(j2, encoding="utf-8"))
        by = {r["piece"]: r for r in rep2["pieces"]}
        assert by["Blocker"]["blocked_code"] == BLOCK_DEP_UNREGISTERED, \
            by["Blocker"]
        assert by["Blocker"]["missing_deps"] == ["GhostMod"], by["Blocker"]
        assert by["Blockee"]["blocked_code"] == BLOCK_DEP_BLOCKED, \
            by["Blockee"]
        assert rep2["insert_order"] == [] \
            and rep2["books"]["draft_order_rows"] == 3, rep2["books"]
        p = run(J + ["--pieces", "P1", "--json", j2])
        assert p.returncode == 0, p.stdout
        rep2b = json.load(io.open(j2, encoding="utf-8"))
        assert rep2b["pieces"][0]["blocked_code"] \
            == BLOCK_DEP_OUTSIDE_PIECES, rep2b["pieces"][0]
        assert "P2" in rep2b["pieces"][0]["missing_deps"], \
            rep2b["pieces"][0]
        print("  [2/8] BLOCK family OK (dep-unregistered GhostMod, cascade "
              "Blockee, dep registered on contribution but outside --pieces; "
              "exit 0, draft stays at the base books)")

        # ---- vector 3: frozen md5 vector end to end ----
        j3 = os.path.join(d1, "r3.json")
        p = run(J + ["--pieces", "FrozenA", "--json", j3])
        assert p.returncode == 0, p.stdout
        rep3 = json.load(io.open(j3, encoding="utf-8"))
        assert rep3["new_rows"]["order"] == ["FrozenA.v#R1-77c2b9a8"], \
            rep3["new_rows"]
        print("  [3/8] frozen md5 vector OK (FrozenA -> #R1-77c2b9a8)")

        # ---- vector 4: dry-run zero write, apply, CRLF, already-in-base ----
        d4 = os.path.join(tmp, "vec4")
        os.makedirs(d4)
        out4 = os.path.join(d4, "draft")
        pre_tree = tree_md5(d1)
        p = run(J + ["--pieces", "BaseA,P1,P2,P3", "--out", out4])
        assert p.returncode == 0, p.stdout
        assert not os.path.exists(out4), "dry run wrote to disk"
        assert "(dry run: nothing written)" in p.stdout, p.stdout
        assert tree_md5(d1) == pre_tree, "dry run touched the tree"
        p = run(J + ["--pieces", "BaseA,P1,P2,P3", "--out", out4,
                     "--apply", "--json", os.path.join(d4, "r4.json")])
        assert p.returncode == 0, p.stdout
        rep4 = json.load(io.open(os.path.join(d4, "r4.json"),
                                 encoding="utf-8"))
        assert rep4["mode"] == "APPLY" and rep4["writes"], rep4["mode"]
        st = {r["piece"]: r["status"] for r in rep4["pieces"]}
        assert st == {"BaseA": STATUS_ALREADY, "P1": STATUS_INSERTED,
                      "P2": STATUS_INSERTED, "P3": STATUS_INSERTED}, st
        assert rep4["pieces"][0]["base_blob"]["status"] == "same", \
            rep4["pieces"][0]["base_blob"]
        got_order = rd(os.path.join(out4, "order.txt")).decode("utf-8")
        got_project = rd(os.path.join(out4, "_CoqProject")).decode("utf-8")
        assert got_order.splitlines() == base_order_rows + [
            "P3.v#R1-%s" % md5p["P3"], "P2.v#R1-%s" % md5p["P2"],
            "P1.v#R1-%s" % md5p["P1"]], got_order
        assert got_project.splitlines() == [
            '-Q . ""', "BaseA.v", "BaseB.v", "Cmain.v",
            "P3.v", "P2.v", "P1.v"], got_project
        first = (rd(os.path.join(out4, "order.txt")),
                 rd(os.path.join(out4, "_CoqProject")))
        p = run(J + ["--pieces", "BaseA,P1,P2,P3", "--out", out4,
                     "--apply", "--json", os.path.join(d4, "r4.json")])
        assert p.returncode == 0, p.stdout
        assert (rd(os.path.join(out4, "order.txt")),
                rd(os.path.join(out4, "_CoqProject"))) == first, \
            "rerun drift on the applied draft"
        # CRLF base book: the draft order book follows it
        d4b = os.path.join(tmp, "vec4b")
        os.makedirs(d4b)
        b4 = os.path.join(tmp, "base_repo_crlf")
        os.makedirs(b4)
        git(b4, "init")
        b4_branch = git(b4, "symbolic-ref", "--short", "HEAD")
        for name, body in sorted(base_body.items()):
            wf(os.path.join(b4, name), body)
        wf(os.path.join(b4, "order.txt"),
           "\n".join(base_order_rows) + "\n", eol="\r\n")
        wf(os.path.join(b4, "_CoqProject"),
           '-Q . ""\n' + "\n".join(r.split("#", 1)[0]
                                   for r in base_order_rows) + "\n")
        git(b4, "add", ".")
        git(b4, "commit", "-m", "base books crlf")
        out4b = os.path.join(d4b, "draft")
        p = run(["--base-repo", b4, "--base-ref", b4_branch,
                 "--contrib-repo", contrib_repo,
                 "--contrib-ref", contrib_branch, "--anchor-src", anchor,
                 "--pieces", "P3", "--out", out4b, "--apply"])
        assert p.returncode == 0, p.stdout
        raw = rd(os.path.join(out4b, "order.txt"))
        assert raw == ("BaseA.v#R0-11111111\r\nBaseB.v#R0-22222222\r\n"
                       "Cmain.v#R0-33333333\r\nP3.v#R1-%s\r\n"
                       % md5p["P3"]).encode("utf-8"), raw
        print("  [4/8] dry-run zero-write OK; apply writes both books; "
              "already-in-base skip with blob-same evidence; CRLF preserved; "
              "applied rerun byte-identical")

        # ---- vector 5: blast family (exit 2, zero writes) ----
        d5 = os.path.join(tmp, "vec5")
        os.makedirs(d5)
        out5 = os.path.join(d5, "draft")
        p = run(J + ["--pieces", "TwA,TwB", "--out", out5, "--apply"])
        assert p.returncode == 2, \
            "anchor-text blast should exit 2: %s" % p.stdout
        assert "A3-ANCHOR-TEXT-NEW-DUP" in p.stdout, p.stdout[-400:]
        assert not os.path.exists(out5), "blast wrote to disk"
        # entity-blob divergence: stale materialized tree
        d5b = os.path.join(tmp, "vec5b")
        os.makedirs(d5b)
        anchor_stale = os.path.join(d5b, "tree")
        for name in sorted(contrib_body):
            wf(os.path.join(anchor_stale, name), contrib_body[name])
        wf(os.path.join(anchor_stale, "P2.v"),
           contrib_body["P2.v"] + "(* stale mutation *)\n")
        p = run(["--base-repo", base_repo, "--base-ref", base_branch,
                 "--contrib-repo", contrib_repo,
                 "--contrib-ref", contrib_branch,
                 "--anchor-src", anchor_stale,
                 "--pieces", "P1,P2,P3", "--out", os.path.join(d5b, "draft"),
                 "--apply"])
        assert p.returncode == 2, "divergence should exit 2: %s" % p.stdout
        assert "ENTITY-BLOB-DIVERGED" in p.stdout, p.stdout[-400:]
        assert not os.path.exists(os.path.join(d5b, "draft")), \
            "divergence blast wrote to disk"
        p = run(J + ["--pieces", "CycA,CycB", "--out", out5])
        assert p.returncode == 2, "cycle should exit 2: %s" % p.stdout
        assert "DEP-CYCLE" in p.stdout, p.stdout[-400:]
        print("  [5/8] blast family OK (identical-content pair -> "
              "A3-ANCHOR-TEXT-NEW-DUP; stale entity -> ENTITY-BLOB-DIVERGED; "
              "Require cycle -> DEP-CYCLE; all exit 2 zero writes)")

        # ---- vector 6: dep-source registry / coqdep ----
        j6 = os.path.join(d1, "r6.json")
        p = run(J + ["--pieces", "P1,P2,P3", "--dep-source", "registry",
                     "--json", j6])
        assert p.returncode == 0, p.stdout
        rep6 = json.load(io.open(j6, encoding="utf-8"))
        assert rep6["inputs"]["dep_source"] == "registry", rep6["inputs"]
        assert rep6["insert_order"] == ["P1", "P2", "P3"], \
            rep6["insert_order"]
        if shutil.which("coqdep") is None:
            p = run(J + ["--pieces", "P1,P2,P3", "--dep-source", "coqdep"])
            assert p.returncode == 9, \
                "coqdep absent should exit 9: %s" % p.stdout
            note = "coqdep absent -> 9 (verified)"
        else:
            note = "coqdep present on PATH -> the exit-9 vector is skipped"
        print("  [6/8] dep-source OK (registry order verbatim P1,P2,P3; "
              "%s)" % note)

        # ---- vector 7: CLI exit codes + pinned sequence ----
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, p.returncode
        p = run([])
        assert p.returncode == 2, p.returncode
        p = run(J + ["--pieces", "P1", "--apply"])
        assert p.returncode == 2, "apply without out should be usage 2"
        p = run(J + ["--pieces", ",", " "])
        assert p.returncode == 2, "empty pieces should be usage 2"
        p = run(["--base-repo", os.path.join(tmp, "no_repo"),
                 "--base-ref", "x", "--contrib-repo", contrib_repo,
                 "--contrib-ref", contrib_branch, "--anchor-src", anchor,
                 "--pieces", "P1"])
        assert p.returncode == 9, p.returncode
        p = run(J + ["--pieces", "P1", "--base-ref", "no-such-ref"])
        assert p.returncode == 9, p.returncode
        p = run(J + ["--pieces", "P1", "--anchor-src",
                     os.path.join(tmp, "no_tree")])
        assert p.returncode == 9, p.returncode
        p = run(J + ["--pieces", "P1", "--contrib-path-order", "nope.txt"])
        assert p.returncode == 9, p.returncode
        p = run(J + ["--pieces", "P1", "--seq", "-1"])
        assert p.returncode == 2, "negative seq should be usage 2"
        j7 = os.path.join(d1, "r7.json")
        p = run(J + ["--pieces", "P1,P2,P3", "--json", j7, "--seq", "9"])
        assert p.returncode == 0, p.stdout
        rep7 = json.load(io.open(j7, encoding="utf-8"))
        assert rep7["seq"] == {"mode": "pinned", "base_max_seq": None,
                               "batch_seq": 9}, rep7["seq"]
        assert rep7["new_rows"]["order"][0].endswith("#R9-%s" % md5p["P3"]), \
            rep7["new_rows"]
        print("  [7/8] CLI exit codes OK (help 0, bogus 2, no input 2, "
              "apply-without-out 2, empty pieces 2, missing repo 9, bad ref "
              "9, missing anchor-src 9, missing book 9, negative seq 2) + "
              "pinned seq")

        print("REGISTRY-REGEN-SELFTEST PASS: pure functions/three-piece "
              "topo/BLOCK family/frozen md5/dry-run zero-write + apply + "
              "CRLF/blast family/dep-source/CLI codes - eight vectors all "
              "pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------- entry ----------

def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="contribution-surface registration-row regeneration: "
                    "merge-target books verbatim plus canonical "
                    "#R<seq>-<md5-8> rows for the named pieces, "
                    "tail-appended in dependency order (dry run by default; "
                    "--apply writes the draft pair into --out)")
    ap.add_argument("--base-repo", default=None, metavar="REPO",
                    help="merge-target repository (its books are the draft "
                         "bottom; never written)")
    ap.add_argument("--base-ref", default=None, metavar="REF",
                    help="merge-target ref")
    ap.add_argument("--contrib-repo", default=None, metavar="REPO",
                    help="contribution-surface repository")
    ap.add_argument("--contrib-ref", default=None, metavar="REF",
                    help="contribution-surface ref")
    ap.add_argument("--pieces", default=None, metavar="M1,M2,...",
                    help="contribution piece names (comma separated; .v "
                         "suffix tolerated)")
    ap.add_argument("--anchor-src", default=None, metavar="DIR",
                    help="materialized contribution tree (unique <name>.v "
                         "per piece; entity md5 and Require surfaces come "
                         "from here)")
    ap.add_argument("--dep-source", default=DEP_SOURCE_DEFAULT,
                    choices=DEP_SOURCES, metavar="SRC",
                    help="dependency order: require (default) | coqdep | "
                         "registry | auto")
    ap.add_argument("--seq", default=None, type=int, metavar="N",
                    help="pin the batch sequence number (default: base max "
                         "sequence + 1)")
    ap.add_argument("--base-path-order", default=None, metavar="PATH",
                    help="base order-book path in the repository (default "
                         "order.txt)")
    ap.add_argument("--base-path-project", default=None, metavar="PATH",
                    help="base project-book path (default _CoqProject)")
    ap.add_argument("--contrib-path-order", default=None, metavar="PATH",
                    help="contribution order-book path (default order.txt)")
    ap.add_argument("--contrib-path-project", default=None, metavar="PATH",
                    help="contribution project-book path (default "
                         "_CoqProject)")
    ap.add_argument("--out", default=None, metavar="DIR",
                    help="draft destination; --apply writes DIR/order.txt "
                         "and DIR/_CoqProject (the contribution-side "
                         "registry pair)")
    ap.add_argument("--apply", action="store_true",
                    help="allow the --out write (dry run by default, zero "
                         "writes)")
    ap.add_argument("--json", default=None, metavar="FILE",
                    help="report target (schema rocqwash-registry-regen/1)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    def die(msg, code):
        print("FAIL-LOUD: %s" % msg, file=sys.stderr)
        sys.exit(code)

    if args.base_repo is None or args.base_ref is None:
        die("--base-repo and --base-ref are required (merge target)", 2)
    if args.contrib_repo is None or args.contrib_ref is None:
        die("--contrib-repo and --contrib-ref are required (contribution "
            "surface)", 2)
    if not args.pieces:
        die("--pieces is required (contribution piece names)", 2)
    if args.anchor_src is None:
        die("--anchor-src is required (materialized contribution tree)", 2)
    if args.apply and not args.out:
        die("--apply requires --out (no in-place default, no implicit "
            "overwrite)", 2)
    if args.seq is not None and args.seq < 0:
        die("--seq must be non-negative", 2)

    try:
        report = run_regen(args)
    except _ru.MissingInput as e:
        die(str(e), 9)
    except UsageError as e:
        die(str(e), 2)
    except _ru.UsageError as e:
        die("engine usage failure: %s" % e, 2)
    except _ru.AssertBlast as e:
        print("ASSERT-BLAST %s (exit 2, zero writes):" % e.code,
              file=sys.stderr)
        for item in e.items:
            print("  - %s" % item, file=sys.stderr)
        sys.exit(2)

    print_stdout(report)
    if args.json:
        dump_json(args.json, report)
        print("json -> %s" % args.json)
    sys.exit(0)


if __name__ == "__main__":
    main()
