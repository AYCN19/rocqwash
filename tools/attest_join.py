#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""attest_join.py - side-by-side join of the cw.attest/v1 module archive
and the rocqwash.b-axiom-audit/1 axiom-audit report.
Purpose.  Produce one machine-readable juxtaposition table: archive
  modules (keys "<Stem>.v" / "Local/<Stem>.v", entries {vo_sha256, size}
  over the compiled .vo bytes) join the audit report's files[] entries
  (repo-relative .v paths carrying the source md5, the file
  classification and the statement-level census) on the exact module
  key; the two hash faces are different objects (compiled bytes vs
  source bytes), so rows record both verbatim and no equality verdict
  exists; keys land in matched / matched_local (directory-prefixed) /
  attest_only / audit_only; per-module verdicts stay unaggregated
  statement-level sets pending the upstream contract decision.
Interface.  python3 -I tools/attest_join.py --attest ARCHIVE --report
  AUDIT_JSON --out JOINED_JSON [--basename-fallback] | --selftest.
Dependencies.  Python 3 standard library only; reads only the two
  caller-named inputs; writes only --out; zero network, zero engine
  launch.
Evidence.  Deterministic: sorted keys, no wall clock, byte-identical
  reruns; --selftest runs frozen offline vectors over a synthetic mini
  vo tree cast in the attest_cast.py form plus synthetic audit payloads;
  the loader is the attest_reconcile.load_attest caliber (schema and
  generated_by string equality, exact entry field set, 64-hex hashes,
  non-negative int size, .v key suffix, tree_sha256 recomputation).
Exit-codes.  0 join table written; 3 archive side unusable (unreadable,
  contract mismatch, tree_sha256 self-consistency broken) so the table
  degrades to empty buckets and never weakens; 2 structural fail-loud
  (audit-side contract break, duplicate report keys, ambiguous basename
  fallback, output write failure, usage error).
"""

# Extended contract (kept below the five-field header budget):
# Join key canon: exact string equality between an archive module key and
#   a report files[].file when the audit run root equals the archive cast
#   vo-tree root; the ".v" suffix, any directory prefix (the Local/ face)
#   and letter case are preserved with zero normalization.  When the
#   roots do not align, --basename-fallback joins on basename + ".v" and
#   only after an ambiguity sweep: any basename carried by more than one
#   archive key or more than one report file is enumerated and exits 2
#   (duplicate keys are never merged in silence).
# Buckets: matched (bare keys), matched_local (keys carrying a directory
#   prefix, e.g. the single Local/ module of the Main archive),
#   attest_only, audit_only; the union is exhaustive over both key sets.
#   matched_local exists because attest_reconcile narrows its skip
#   surface to top-level keys; the join table keeps the Local face
#   visible instead of dropping it.
# Hash faces stay distinct: vo_sha256 hashes the compiled .vo byte
#   stream while files[].md5 hashes the .v source bytes; matched rows
#   juxtapose both verbatim and the tool emits no equivalence verdict at
#   row or table level.
# Module verdicts: the audit payload judges at statement level (census[]
#   rows: closed / axioms / census-error) plus a file classification
#   (compile-ok / compile-broken); the join consolidates verdict_set
#   (sorted set of statement verdicts present) and axiom_set (sorted
#   union of census axioms) per module, both lossless set faces, and
#   deliberately performs NO semantic aggregation (no worst-of rule, no
#   census-error contagion); that rule is an open contract decision
#   (ticket R2-80 blocker B2) and rides disclosed_limitations.
# Freshness: the audit report carries no commit or tree hash field, and
#   the archive tree_sha256 hashes the vo byte face, so the two sides
#   cannot cross-confirm freshness in data; the table records the
#   archive tree_sha256, each side's schema and tool, and lists this as
#   a disclosed limitation; same-commit provenance stays a run-flow duty
#   (ticket R2-80 blocker B3).  allow_axioms rides the output verbatim
#   (a verdict without its allowlist is not reproducible).
# Output modes: JOINED (exit 0), NO_ARCHIVE (exit 3, empty buckets, zero
#   counts), AUDIT-INVALID (exit 2), AMBIGUOUS (exit 2, ambiguities
#   listed); counts keys: matched / matched_local / attest_only /
#   audit_only / ambiguous.

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

PROG = "attest_join"
SCHEMA = "cw.attest-join/v1"
ARCHIVE_SCHEMA = "cw.attest/v1"
ARCHIVE_GENERATED_BY = "coqchk green run"
AUDIT_SCHEMA = "rocqwash.b-axiom-audit/1"
CLASSIFICATIONS = ("compile-ok", "compile-broken")

EXIT_JOINED = 0
EXIT_STRUCTURAL = 2
EXIT_NO_ARCHIVE = 3

RULE_EXACT = "exact-string"
RULE_BASENAME = "basename"

MODE_JOINED = "JOINED"
MODE_NO_ARCHIVE = "NO_ARCHIVE"
MODE_AUDIT_INVALID = "AUDIT-INVALID"
MODE_AMBIGUOUS = "AMBIGUOUS"

DISCLOSED_LIMITATIONS = (
    "no equivalence verdict exists: vo_sha256 hashes the compiled .vo "
    "byte stream while files[].md5 hashes the .v source bytes; the two "
    "hash faces are different objects and this join is a juxtaposition, "
    "never an equality check",
    "module verdicts stay unaggregated: the audit payload judges at "
    "statement level; verdict_set and axiom_set are lossless set "
    "consolidations and any semantic per-module rule (worst-of grades, "
    "census-error contagion) is an open contract decision (ticket R2-80 "
    "blocker B2)",
    "freshness cannot cross-confirm in data: the audit report carries no "
    "commit or tree hash field and the archive tree_sha256 hashes the "
    "vo byte face; same-commit provenance stays a run-flow duty "
    "(ticket R2-80 blocker B3)",
    "the exact-string join assumes the audit run root equals the "
    "archive cast vo-tree root; misaligned roots need --basename-fallback, "
    "which refuses ambiguous basenames instead of merging them",
)

ZERO_COUNTS = {"matched": 0, "matched_local": 0, "attest_only": 0,
               "audit_only": 0, "ambiguous": 0}


class ArchiveError(Exception):
    """Archive side unusable (the EXIT_NO_ARCHIVE path)."""


class AuditContractError(Exception):
    """Report side contract break (structural, EXIT_STRUCTURAL)."""


class AmbiguityError(Exception):
    """Ambiguous basename fallback (structural, EXIT_STRUCTURAL)."""

    def __init__(self, ambiguities):
        super().__init__("ambiguous basename join refused: %d basename(s)"
                         % len(ambiguities))
        self.ambiguities = ambiguities


# ---------------------------------------------------------------- hashing --
def sha256_file(path):
    """(hex digest, byte count) of a file's byte stream."""
    digest = hashlib.sha256()
    size = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def canonical_tree_sha256(modules):
    """The archive casting formula: sha256 over the canonical modules
    serialization (json.dumps sort_keys=True, separators=(",", ":"),
    ensure_ascii=False) - byte-identical to attest_cast.py."""
    canonical = json.dumps(modules, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ---------------------------------------------------------------- archive --
def load_attest(path):
    """Contract-shape check + tree_sha256 self-consistency, the
    attest_reconcile.load_attest caliber.  Any mismatch raises
    ArchiveError (the caller takes EXIT_NO_ARCHIVE: empty table)."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
        archive = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise ArchiveError("archive unreadable or not JSON: %s: %s"
                           % (path, exc))
    if not isinstance(archive, dict):
        raise ArchiveError("archive top level is not a JSON object")
    if archive.get("schema") != ARCHIVE_SCHEMA:
        raise ArchiveError("archive schema off contract: %r != %r"
                           % (archive.get("schema"), ARCHIVE_SCHEMA))
    if archive.get("generated_by") != ARCHIVE_GENERATED_BY:
        raise ArchiveError("archive generated_by off contract (not a "
                           "coqchk green run cast): %r"
                           % (archive.get("generated_by"),))
    modules = archive.get("modules")
    if not isinstance(modules, dict) or not modules:
        raise ArchiveError("archive modules missing or not a non-empty "
                           "object")
    for key, entry in modules.items():
        if not isinstance(entry, dict) or set(entry) != {"vo_sha256",
                                                         "size"}:
            raise ArchiveError("module entry fields off contract: %r"
                               % (key,))
        sha = entry["vo_sha256"]
        size = entry["size"]
        if not isinstance(sha, str) or len(sha) != 64:
            raise ArchiveError("vo_sha256 not a 64-char hex string: %r"
                               % (key,))
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise ArchiveError("size not a non-negative int: %r" % (key,))
        if not key.endswith(".v"):
            raise ArchiveError("module key lacks the .v suffix: %r"
                               % (key,))
    tree_sha = archive.get("tree_sha256")
    if not isinstance(tree_sha, str) or len(tree_sha) != 64:
        raise ArchiveError("tree_sha256 not a 64-char hex string")
    recomputed = canonical_tree_sha256(modules)
    if recomputed != tree_sha:
        raise ArchiveError("archive tree_sha256 self-consistency broken: "
                           "archive %s != recomputed %s"
                           % (tree_sha, recomputed))
    return archive


# ------------------------------------------------------------------ report --
def _audit_rows(rows, key):
    """Shape checks for the statements / census lists of one entry."""
    for row in rows:
        if not isinstance(row, dict):
            raise AuditContractError("list row not an object in %s"
                                     % (key,))
        if not isinstance(row.get("name"), str):
            raise AuditContractError("statement name missing in %s"
                                     % (key,))
        if not isinstance(row.get("line"), int) \
                or isinstance(row.get("line"), bool):
            raise AuditContractError("statement line not an int in %s"
                                     % (key,))


def load_audit(path):
    """Report-side contract check (schema rocqwash.b-axiom-audit/1).

    Returns {"entries": {file: entry}, "allow_axioms": [...], "tool",
    "repo", "files_scanned"}.  Any mismatch raises AuditContractError
    (structural fail-loud, EXIT_STRUCTURAL)."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
        report = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise AuditContractError("audit report unreadable or not JSON: "
                                 "%s: %s" % (path, exc))
    if not isinstance(report, dict):
        raise AuditContractError("audit report top level is not a JSON "
                                 "object")
    if report.get("schema") != AUDIT_SCHEMA:
        raise AuditContractError("audit report schema off contract: %r "
                                 "!= %r" % (report.get("schema"),
                                            AUDIT_SCHEMA))
    allow = report.get("allow_axioms")
    if not isinstance(allow, list) \
            or not all(isinstance(a, str) for a in allow):
        raise AuditContractError("allow_axioms missing or not a list of "
                                 "strings (a verdict without its "
                                 "allowlist is not reproducible)")
    files = report.get("files")
    if not isinstance(files, list):
        raise AuditContractError("files missing or not a list")
    entries = {}
    for entry in files:
        if not isinstance(entry, dict):
            raise AuditContractError("files[] row not an object")
        key = entry.get("file")
        if not isinstance(key, str) or not key.endswith(".v"):
            raise AuditContractError("files[] row lacks a .v file path: "
                                     "%r" % (key,))
        md5 = entry.get("md5")
        if not isinstance(md5, str) or len(md5) != 32:
            raise AuditContractError("src md5 not a 32-char hex string "
                                     "(md5, not the archive's 64-char "
                                     "sha256 face) in %s" % (key,))
        if not isinstance(entry.get("statements"), list):
            raise AuditContractError("statements missing or not a list "
                                     "in %s" % (key,))
        _audit_rows(entry["statements"], key)
        census = entry.get("census")
        if not isinstance(census, list):
            raise AuditContractError("census missing or not a list in %s"
                                     % (key,))
        for row in census:
            if not isinstance(row, dict):
                raise AuditContractError("census row not an object in %s"
                                         % (key,))
            if not isinstance(row.get("statement"), str) \
                    or not isinstance(row.get("verdict"), str):
                raise AuditContractError("census row statement/verdict "
                                         "not strings in %s" % (key,))
            if not isinstance(row.get("line"), int) \
                    or isinstance(row.get("line"), bool):
                raise AuditContractError("census row line not an int in "
                                         "%s" % (key,))
            axioms = row.get("axioms")
            if not isinstance(axioms, list) \
                    or not all(isinstance(a, str) for a in axioms):
                raise AuditContractError("census axioms not a list of "
                                         "strings in %s" % (key,))
        if entry.get("classification") not in CLASSIFICATIONS:
            raise AuditContractError("classification off the enum in %s: "
                                     "%r" % (key,
                                             entry.get("classification")))
        rc = entry.get("compile_rc")
        if rc is not None and not isinstance(rc, int):
            raise AuditContractError("compile_rc neither an int nor "
                                     "null in %s" % (key,))
        if key in entries:
            raise AuditContractError("duplicate report file key (keys "
                                     "are never merged in silence): %s"
                                     % (key,))
        entries[key] = entry
    return {
        "entries": entries,
        "allow_axioms": sorted(allow),
        "tool": report.get("tool"),
        "repo": report.get("repo"),
        "files_scanned": len(files),
    }


# ------------------------------------------------------------------- join --
def audit_module_face(entry):
    """Lossless set consolidation of one report entry: verdict_set and
    axiom_set (no semantic aggregation is performed)."""
    return {
        "verdict_set": sorted({r["verdict"] for r in entry["census"]}),
        "axiom_set": sorted({ax for r in entry["census"]
                             for ax in r["axioms"]}),
    }


def matched_row(key, audit_key, att_entry, aud_entry):
    """One joined row: archive face and report face side by side."""
    row = {
        "key": key,
        "audit_file": audit_key,
        "vo_sha256": att_entry["vo_sha256"],
        "size": att_entry["size"],
        "src_md5": aud_entry["md5"],
        "classification": aud_entry["classification"],
        "compile_rc": aud_entry.get("compile_rc"),
        "statements": len(aud_entry["statements"]),
        "census": len(aud_entry["census"]),
    }
    row.update(audit_module_face(aud_entry))
    return row


def attest_only_row(key, att_entry):
    return {"key": key, "vo_sha256": att_entry["vo_sha256"],
            "size": att_entry["size"]}


def audit_only_row(key, aud_entry):
    return {"key": key, "src_md5": aud_entry["md5"],
            "classification": aud_entry["classification"]}


def empty_buckets():
    return {"matched": [], "matched_local": [], "attest_only": [],
            "audit_only": []}


def exact_join(modules, entries):
    """Exact-string key join (zero normalization, case-sensitive)."""
    buckets = empty_buckets()
    for key in sorted(modules):
        if key not in entries:
            buckets["attest_only"].append(attest_only_row(key,
                                                          modules[key]))
            continue
        row = matched_row(key, key, modules[key], entries[key])
        if "/" in key:
            buckets["matched_local"].append(row)
        else:
            buckets["matched"].append(row)
    for key in sorted(entries):
        if key not in modules:
            buckets["audit_only"].append(audit_only_row(key,
                                                        entries[key]))
    return buckets


def basename_join(modules, entries):
    """Basename fallback for misaligned roots; every ambiguous basename
    (either side) is enumerated and refuses the join."""
    by_base_arch = {}
    for key in modules:
        by_base_arch.setdefault(os.path.basename(key), []).append(key)
    by_base_aud = {}
    for key in entries:
        by_base_aud.setdefault(os.path.basename(key), []).append(key)
    ambiguities = []
    for base in sorted(set(by_base_arch) | set(by_base_aud)):
        arch_keys = sorted(by_base_arch.get(base, []))
        aud_keys = sorted(by_base_aud.get(base, []))
        if len(arch_keys) > 1:
            ambiguities.append({"side": "archive", "basename": base,
                                "keys": arch_keys})
        if len(aud_keys) > 1:
            ambiguities.append({"side": "report", "basename": base,
                                "keys": aud_keys})
    if ambiguities:
        raise AmbiguityError(ambiguities)
    buckets = empty_buckets()
    aud_by_base = {os.path.basename(k): k for k in entries}
    for key in sorted(modules):
        aud_key = aud_by_base.get(os.path.basename(key))
        if aud_key is None:
            buckets["attest_only"].append(attest_only_row(key,
                                                          modules[key]))
            continue
        row = matched_row(key, aud_key, modules[key], entries[aud_key])
        if "/" in key:
            buckets["matched_local"].append(row)
        else:
            buckets["matched"].append(row)
    joined_aud = set(aud_by_base[k] for k in modules
                     if os.path.basename(k) in aud_by_base)
    for key in sorted(entries):
        if key not in joined_aud:
            buckets["audit_only"].append(audit_only_row(key,
                                                        entries[key]))
    return buckets


def archive_info(path, archive):
    return {
        "path": str(path),
        "schema": ARCHIVE_SCHEMA,
        "generated_by": archive["generated_by"],
        "tree_sha256": archive["tree_sha256"],
        "module_count": len(archive["modules"]),
    }


def audit_info(path, audit):
    return {
        "path": str(path),
        "schema": AUDIT_SCHEMA,
        "tool": audit["tool"],
        "repo": audit["repo"],
        "allow_axioms": audit["allow_axioms"],
        "files_scanned": audit["files_scanned"],
    }


def build_doc(mode, rule, archive_block, audit_block, buckets, counts,
              ambiguities, reason):
    """One mode-shaped document (all modes share the key set)."""
    return {
        "schema": SCHEMA,
        "tool": PROG,
        "mode": mode,
        "join_rule": rule,
        "archive": archive_block,
        "archive_valid": archive_block is not None
                        and mode != MODE_NO_ARCHIVE,
        "audit": audit_block,
        "audit_valid": audit_block is not None
                       and mode not in (MODE_NO_ARCHIVE,
                                        MODE_AUDIT_INVALID),
        "reason": reason,
        "counts": counts,
        "matched": buckets["matched"],
        "matched_local": buckets["matched_local"],
        "attest_only": buckets["attest_only"],
        "audit_only": buckets["audit_only"],
        "ambiguities": ambiguities,
        "disclosed_limitations": list(DISCLOSED_LIMITATIONS),
    }


def build_joined_doc(rule, att_path, rep_path, archive, audit, buckets):
    counts = {
        "matched": len(buckets["matched"]),
        "matched_local": len(buckets["matched_local"]),
        "attest_only": len(buckets["attest_only"]),
        "audit_only": len(buckets["audit_only"]),
        "ambiguous": 0,
    }
    return build_doc(MODE_JOINED, rule, archive_info(att_path, archive),
                     audit_info(rep_path, audit), buckets, counts, [],
                     None)


def write_doc(path, doc):
    """Atomic write (tmp + replace), sorted keys, one trailing newline;
    byte-identical reruns over identical inputs."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    text = json.dumps(doc, ensure_ascii=False, indent=1,
                      sort_keys=True) + "\n"
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


# ------------------------------------------------------------------- main --
def summarize(doc):
    """One stdout line per mode (loud, deterministic forms)."""
    if doc["mode"] == MODE_JOINED:
        c = doc["counts"]
        print("[attest-join] mode=JOINED rule=%s matched=%d "
              "matched_local=%d attest_only=%d audit_only=%d "
              "archive_tree_sha256=%s"
              % (doc["join_rule"], c["matched"], c["matched_local"],
                 c["attest_only"], c["audit_only"],
                 doc["archive"]["tree_sha256"]))
    elif doc["mode"] == MODE_NO_ARCHIVE:
        print("[no-archive] %s" % doc["reason"])
    elif doc["mode"] == MODE_AUDIT_INVALID:
        print("[error] %s" % doc["reason"])
    else:
        print("[ambiguous] %s" % doc["reason"])


def run_face(args):
    """The run face: archive first (exit 3 direction), report second and
    the join third (structural, exit 2 direction)."""
    rule = RULE_BASENAME if args.basename_fallback else RULE_EXACT
    try:
        archive = load_attest(args.attest)
    except ArchiveError as exc:
        doc = build_doc(MODE_NO_ARCHIVE, rule, None, None,
                        empty_buckets(), dict(ZERO_COUNTS), [],
                        str(exc))
        write_doc(args.out, doc)
        summarize(doc)
        return EXIT_NO_ARCHIVE
    try:
        audit = load_audit(args.report)
    except AuditContractError as exc:
        doc = build_doc(MODE_AUDIT_INVALID, rule,
                        archive_info(args.attest, archive),
                        {"path": str(args.report), "valid": False,
                         "reason": str(exc)},
                        empty_buckets(), dict(ZERO_COUNTS), [],
                        str(exc))
        write_doc(args.out, doc)
        summarize(doc)
        return EXIT_STRUCTURAL
    try:
        if rule == RULE_BASENAME:
            buckets = basename_join(archive["modules"], audit["entries"])
        else:
            buckets = exact_join(archive["modules"], audit["entries"])
        doc = build_joined_doc(rule, args.attest, args.report, archive,
                               audit, buckets)
    except AmbiguityError as exc:
        counts = dict(ZERO_COUNTS)
        counts["ambiguous"] = len(exc.ambiguities)
        doc = build_doc(MODE_AMBIGUOUS, rule,
                        archive_info(args.attest, archive),
                        audit_info(args.report, audit),
                        empty_buckets(), counts, exc.ambiguities,
                        str(exc))
        write_doc(args.out, doc)
        summarize(doc)
        for amb in exc.ambiguities:
            print("  ambiguous %s basename %r: %s"
                  % (amb["side"], amb["basename"], ", ".join(amb["keys"])))
        return EXIT_STRUCTURAL
    write_doc(args.out, doc)
    summarize(doc)
    return EXIT_JOINED


def build_parser():
    """The flag face (extracted so --selftest runs standalone)."""
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="Side-by-side join of the cw.attest/v1 module "
                    "archive and the rocqwash.b-axiom-audit/1 audit "
                    "report (juxtaposition, never an equality check).")
    ap.add_argument("--attest", default=None,
                    help="cw.attest/v1 archive JSON (read-only)")
    ap.add_argument("--report", default=None,
                    help="rocqwash.b-axiom-audit/1 report JSON "
                         "(read-only)")
    ap.add_argument("--out", default=None,
                    help="join table JSON output path")
    ap.add_argument("--basename-fallback", action="store_true",
                    help="join on basename + .v for misaligned roots; "
                         "ambiguous basenames fail loud (exit 2)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the frozen offline vector group and exit")
    return ap


# --------------------------------------------------------------- selftest --
def cast_archive(tree):
    """The attest_cast.py casting face, replicated for the synthetic
    vectors: root *.vo (non-recursive) + Local/*.vo (non-recursive);
    names starting with '_' stay off the face; keys <stem>.v and
    Local/<stem>.v; tree_sha256 over the canonical modules form."""
    modules = {}
    for name in sorted(os.listdir(tree)):
        path = os.path.join(tree, name)
        if not name.endswith(".vo") or not os.path.isfile(path):
            continue
        if name.startswith("_"):
            continue
        sha, size = sha256_file(path)
        modules[name[:-3] + ".v"] = {"vo_sha256": sha, "size": size}
    local = os.path.join(tree, "Local")
    if os.path.isdir(local):
        for name in sorted(os.listdir(local)):
            path = os.path.join(local, name)
            if not name.endswith(".vo") or not os.path.isfile(path):
                continue
            if name.startswith("_"):
                continue
            sha, size = sha256_file(path)
            modules["Local/" + name[:-3] + ".v"] = {"vo_sha256": sha,
                                                    "size": size}
    return {
        "modules": modules,
        "tree_sha256": canonical_tree_sha256(modules),
        "generated_by": ARCHIVE_GENERATED_BY,
        "schema": ARCHIVE_SCHEMA,
    }


def synth_file(rel, md5hex, classification="compile-ok", census=(),
               statements=(), compile_rc=0):
    """One synthetic report files[] entry (base_report entry shape)."""
    return {
        "file": rel,
        "md5": md5hex,
        "statements": list(statements),
        "census": list(census),
        "classification": classification,
        "compile_rc": compile_rc,
    }


def synth_census(name, verdict, axioms=(), line=1):
    """One synthetic census row (census_file row shape)."""
    return {"statement": name, "line": line, "verdict": verdict,
            "axioms": sorted(set(axioms))}


def synth_report(files, allow=()):
    """A synthetic rocqwash.b-axiom-audit/1 payload (base_report shape)."""
    return {
        "schema": AUDIT_SCHEMA,
        "tool": "axiom_audit",
        "repo": "/synthetic/repo-root",
        "engine": {"binary": "/bin/coqc", "form": "coqc"},
        "standard": "zero non-allowlisted axioms in any judged statement "
                    "(default allowlist empty)",
        "allow_axioms": sorted(set(allow)),
        "files_scanned": len(files),
        "files": files,
        "declared_axioms": [],
        "axiom_inventory": [],
        "classification_counts": {"stdlib": 0, "classical": 0,
                                  "funext": 0, "custom": 0},
        "debt_register": [],
        "red_files": [],
        "verdict": "PASS",
    }


def dump_json(obj, path):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


def read_json(path):
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def selftest():
    """Frozen offline vectors: zero network, zero engine launch, zero
    real-repo touch.  Returns 1 on any FAIL, else 0."""
    fails = []
    total = [0]

    def vec(name, ok, detail=""):
        total[0] += 1
        print(("[PASS] " if ok else "[FAIL] ") + name
              + ((" - " + detail) if detail else ""))
        if not ok:
            fails.append(name)

    script = os.path.abspath(__file__)
    tmp = tempfile.mkdtemp(prefix="rocqwash_attest_join_selftest_")
    try:
        # ---- synthetic vo tree, cast in the attest_cast.py form ----
        tree = os.path.join(tmp, "vo_tree")
        os.makedirs(os.path.join(tree, "Local"))
        voices = {
            "a.vo": b"vo-bytes-a\n",
            "b.vo": b"vo-bytes-b\n",
            "_hidden.vo": b"vo-bytes-hidden\n",
            os.path.join("Local", "c.vo"): b"vo-bytes-c\n",
        }
        for rel, blob in voices.items():
            with open(os.path.join(tree, rel), "wb") as fh:
                fh.write(blob)
        deeper = os.path.join(tree, "sub")
        os.makedirs(deeper)
        with open(os.path.join(deeper, "z.vo"), "wb") as fh:
            fh.write(b"vo-bytes-z\n")
        archive = cast_archive(tree)
        att_path = os.path.join(tmp, "cw_attest.json")
        dump_json(archive, att_path)
        vec("cast-face-keys",
            sorted(archive["modules"]) == ["Local/c.v", "a.v", "b.v"],
            "'_'-prefixed and deeper files stay off the cast face: %s"
            % sorted(archive["modules"]))
        sha_a, size_a = sha256_file(os.path.join(tree, "a.vo"))
        ent = archive["modules"]["a.v"]
        vec("cast-entry-shape",
            set(ent) == {"vo_sha256", "size"}
            and ent["vo_sha256"] == sha_a and ent["size"] == size_a,
            "entries carry {vo_sha256, size} over the .vo bytes")
        vec("loader-accepts-cast",
            load_attest(att_path)["tree_sha256"] == archive["tree_sha256"],
            "the cast archive passes the reconcile-caliber loader")

        # ---- loader rejection vectors (each contract check one vector)
        def archive_error_with(mutate):
            bad = json.loads(json.dumps(archive))
            mutate(bad)
            bad_path = os.path.join(tmp, "bad_attest.json")
            dump_json(bad, bad_path)
            try:
                load_attest(bad_path)
            except ArchiveError:
                return True
            return False

        vec("loader-schema-reject",
            archive_error_with(lambda d: d.__setitem__("schema",
                                                       "cw.attest/v2")),
            "schema string equality enforced")
        vec("loader-generated-by-reject",
            archive_error_with(
                lambda d: d.__setitem__("generated_by", "hand cast")),
            "generated_by string equality enforced")
        vec("loader-entry-extra-field-reject",
            archive_error_with(
                lambda d: d["modules"]["a.v"].__setitem__("axioms", [])),
            "entry field set stays exactly {vo_sha256, size}")
        vec("loader-size-bool-reject",
            archive_error_with(
                lambda d: d["modules"]["a.v"].__setitem__("size", True)),
            "bool size refuses (not a non-negative int)")
        vec("loader-key-suffix-reject",
            archive_error_with(
                lambda d: d["modules"].__setitem__("a", {"vo_sha256":
                                                         "0" * 64,
                                                         "size": 1})),
            ".v key suffix enforced")
        vec("loader-empty-modules-reject",
            archive_error_with(lambda d: d.__setitem__("modules", {})),
            "empty modules refuse")
        vec("loader-tree-consistency-reject",
            archive_error_with(
                lambda d: d.__setitem__("tree_sha256", "f" * 64)),
            "canonical recomputation catches a tampered tree_sha256")

        # ---- synthetic audit payloads ----
        md5_a = hashlib.md5(b"src-a").hexdigest()
        md5_c = hashlib.md5(b"src-c").hexdigest()
        md5_d = hashlib.md5(b"src-d").hexdigest()
        md5_br = hashlib.md5(b"src-broken").hexdigest()
        report = synth_report([
            synth_file("a.v", md5_a,
                       census=[synth_census("t_a", "closed")],
                       statements=[{"name": "t_a", "line": 1}]),
            synth_file("d.v", md5_d,
                       census=[synth_census("t_d", "axioms",
                                            ["classic"])],
                       statements=[{"name": "t_d", "line": 1}]),
            synth_file("Local/c.v", md5_c,
                       census=[synth_census("t_c", "axioms",
                                            ["proof_irrelevance",
                                             "classic"])],
                       statements=[{"name": "t_c", "line": 1}]),
            synth_file("broken.v", md5_br,
                       classification="compile-broken", census=[],
                       statements=[], compile_rc=2),
        ])
        rep_path = os.path.join(tmp, "audit_report.json")
        dump_json(report, rep_path)
        loaded = load_audit(rep_path)
        vec("audit-loader-accepts",
            len(loaded["entries"]) == 4
            and loaded["allow_axioms"] == []
            and loaded["tool"] == "axiom_audit",
            "the report loads; allow_axioms and tool ride through")

        def audit_error_with(mutate):
            bad = json.loads(json.dumps(report))
            mutate(bad)
            bad_path = os.path.join(tmp, "bad_report.json")
            dump_json(bad, bad_path)
            try:
                load_audit(bad_path)
            except AuditContractError:
                return True
            return False

        vec("audit-loader-schema-reject",
            audit_error_with(
                lambda d: d.__setitem__("schema", "rocqwash.other/1")),
            "audit schema string equality enforced")
        vec("audit-loader-dup-keys-reject",
            audit_error_with(
                lambda d: d["files"].append(d["files"][0])),
            "duplicate report keys fail loud, never merge")
        vec("audit-loader-classification-reject",
            audit_error_with(
                lambda d: d["files"][0].__setitem__(
                    "classification", "weird")),
            "classification stays on the two-value enum")
        vec("audit-loader-allowlist-reject",
            audit_error_with(lambda d: d.__setitem__("allow_axioms",
                                                     "classic")),
            "allow_axioms must be a list (reproducibility face)")

        # ---- exact join faces ----
        aud_loaded = load_audit(rep_path)
        arch_loaded = load_attest(att_path)
        doc = build_joined_doc(RULE_EXACT, att_path, rep_path,
                               arch_loaded, aud_loaded,
                               exact_join(arch_loaded["modules"],
                                          aud_loaded["entries"]))
        c = doc["counts"]
        vec("exact-join-counts",
            c["matched"] == 1 and c["matched_local"] == 1
            and c["attest_only"] == 1 and c["audit_only"] == 2
            and c["ambiguous"] == 0,
            "counts %s" % c)
        rows = {r["key"]: r for r in doc["matched"]
                + doc["matched_local"]}
        row_a = rows.get("a.v")
        row_c = rows.get("Local/c.v")
        vec("matched-row-payload",
            row_a is not None
            and row_a["verdict_set"] == ["closed"]
            and row_a["axiom_set"] == []
            and row_a["src_md5"] == md5_a
            and row_c is not None
            and row_c["verdict_set"] == ["axioms"]
            and row_c["axiom_set"] == ["classic", "proof_irrelevance"]
            and row_c["src_md5"] == md5_c,
            "rows juxtapose vo_sha256/size with src_md5 and the "
            "statement-level sets verbatim")
        vec("local-bucket-explicit",
            any(r["key"] == "Local/c.v" for r in doc["matched_local"])
            and not any(r["key"] == "Local/c.v" for r in doc["matched"]),
            "the Local/ face joins into matched_local, never dropped "
            "into silence")
        only_b = doc["attest_only"]
        only_aud = {r["key"]: r for r in doc["audit_only"]}
        vec("only-buckets-face",
            [r["key"] for r in only_b] == ["b.v"]
            and only_b[0]["vo_sha256"]
            == archive["modules"]["b.v"]["vo_sha256"]
            and sorted(only_aud) == ["broken.v", "d.v"]
            and only_aud["broken.v"]["classification"]
            == "compile-broken"
            and only_aud["d.v"]["src_md5"] == md5_d,
            "attest_only carries the archive face, audit_only the "
            "report face")
        vec("determinism-double-build",
            json.dumps(build_joined_doc(
                RULE_EXACT, att_path, rep_path, arch_loaded, aud_loaded,
                exact_join(arch_loaded["modules"],
                           aud_loaded["entries"])),
                sort_keys=True)
            == json.dumps(doc, sort_keys=True),
            "double build is byte-identical")

        # ---- basename fallback faces ----
        mis_report = synth_report([
            synth_file("src/a.v", md5_a,
                       census=[synth_census("t_a", "closed")]),
            synth_file("src/b.v", hashlib.md5(b"src-b2").hexdigest(),
                       census=[synth_census("t_b", "closed")]),
            synth_file("src/d.v", md5_d,
                       census=[synth_census("t_d", "axioms",
                                            ["classic"])]),
        ])
        mis_path = dump_synth(mis_report, tmp, "misroot")
        mis = load_audit(mis_path)
        doc2 = build_joined_doc(
            RULE_BASENAME, att_path, "mis", archive, mis,
            basename_join(archive["modules"], mis["entries"]))
        c2 = doc2["counts"]
        vec("basename-fallback-joins",
            c2["matched"] == 2 and c2["matched_local"] == 0
            and c2["attest_only"] == 1 and c2["audit_only"] == 1
            and doc2["matched"][0]["audit_file"] == "src/a.v",
            "misaligned roots join by unique basenames; counts %s" % c2)

        dup_arch = {
            "modules": {
                "x.v": {"vo_sha256": "0" * 64, "size": 1},
                "Local/x.v": {"vo_sha256": "1" * 64, "size": 2},
            },
        }
        dup_arch["tree_sha256"] = canonical_tree_sha256(
            dup_arch["modules"])
        dup_arch["generated_by"] = ARCHIVE_GENERATED_BY
        dup_arch["schema"] = ARCHIVE_SCHEMA
        one_aud = load_audit(dump_synth(
            synth_report([synth_file("x.v", md5_a, census=[])]),
            tmp, "one_x"))
        try:
            basename_join(dup_arch["modules"], one_aud["entries"])
            amb_arch = False
            amb_msg = ""
        except AmbiguityError as exc:
            amb_arch = True
            amb_msg = str(exc) + repr(exc.ambiguities)
        dup_aud = load_audit(dump_synth(
            synth_report([
                synth_file("p/m.v", md5_a, census=[]),
                synth_file("q/m.v", md5_c, census=[]),
            ]),
            tmp, "dup_m"))
        base_arch = {
            "modules": {"m.v": {"vo_sha256": "2" * 64, "size": 3}},
        }
        base_arch["tree_sha256"] = canonical_tree_sha256(
            base_arch["modules"])
        base_arch["generated_by"] = ARCHIVE_GENERATED_BY
        base_arch["schema"] = ARCHIVE_SCHEMA
        try:
            basename_join(base_arch["modules"], dup_aud["entries"])
            amb_aud = False
            amb_msg2 = ""
        except AmbiguityError as exc:
            amb_aud = True
            amb_msg2 = str(exc) + repr(exc.ambiguities)
        vec("basename-ambiguity-fails-loud",
            amb_arch and amb_aud
            and "Local/x.v" in amb_msg and "x.v" in amb_msg
            and "p/m.v" in amb_msg2 and "q/m.v" in amb_msg2
            and "archive" in amb_msg and "report" in amb_msg2,
            "ambiguous basenames are enumerated on both sides, never "
            "merged")

        # ---- exit-code contract (self-spawn) ----
        def spawn(argv):
            try:
                pr = subprocess.run(
                    [sys.executable, "-I", "-B", script] + argv,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=120)
            except subprocess.TimeoutExpired:
                return None, "", "timeout"
            return (pr.returncode,
                    pr.stdout.decode("utf-8", "replace"),
                    pr.stderr.decode("utf-8", "replace"))

        out1 = os.path.join(tmp, "joined.json")
        rc, _o, _e = spawn(["--attest", att_path, "--report", rep_path,
                            "--out", out1])
        ok = rc == 0
        if ok:
            got = read_json(out1)
            ok = (got["mode"] == MODE_JOINED
                  and got["schema"] == SCHEMA
                  and got["archive"]["tree_sha256"]
                  == archive["tree_sha256"])
        vec("exit-joined-rc0", ok,
            "run face writes the JOINED table (rc %s)" % rc)

        bad_att = os.path.join(tmp, "tampered.json")
        tam = json.loads(json.dumps(archive))
        tam["tree_sha256"] = "f" * 64
        dump_json(tam, bad_att)
        out2 = os.path.join(tmp, "no_archive.json")
        rc, _o, _e = spawn(["--attest", bad_att, "--report", rep_path,
                            "--out", out2])
        ok = rc == 3
        if ok:
            got = read_json(out2)
            ok = (got["mode"] == MODE_NO_ARCHIVE
                  and got["archive_valid"] is False
                  and got["counts"] == ZERO_COUNTS
                  and got["matched"] == []
                  and got["disclosed_limitations"]
                  == list(DISCLOSED_LIMITATIONS))
        vec("exit-no-archive-rc3", ok,
            "archive trouble degrades to the empty table and never "
            "weakens (rc %s)" % rc)

        bad_rep = os.path.join(tmp, "broken_schema_report.json")
        brep = json.loads(json.dumps(report))
        brep["schema"] = "rocqwash.b-axiom-audit/0"
        dump_json(brep, bad_rep)
        out3 = os.path.join(tmp, "audit_invalid.json")
        rc, _o, _e = spawn(["--attest", att_path, "--report", bad_rep,
                            "--out", out3])
        ok = rc == 2
        if ok:
            got = read_json(out3)
            ok = (got["mode"] == MODE_AUDIT_INVALID
                  and got["archive_valid"] is True
                  and got["audit"]["valid"] is False)
        vec("exit-audit-invalid-rc2", ok,
            "report contract break is structural fail-loud (rc %s)" % rc)

        amb_att = os.path.join(tmp, "dup_arch.json")
        dump_json(dup_arch, amb_att)
        amb_rep = os.path.join(tmp, "one_x_report.json")
        dump_json(synth_report([synth_file("x.v", md5_a, census=[])]),
                  amb_rep)
        out4 = os.path.join(tmp, "ambiguous.json")
        rc, _o, _e = spawn(["--attest", amb_att, "--report", amb_rep,
                            "--out", out4, "--basename-fallback"])
        ok = rc == 2
        if ok:
            got = read_json(out4)
            ok = (got["mode"] == MODE_AMBIGUOUS
                  and got["counts"]["ambiguous"] == 1
                  and got["ambiguities"][0]["side"] == "archive"
                  and got["ambiguities"][0]["keys"]
                  == ["Local/x.v", "x.v"])
        vec("exit-ambiguous-rc2", ok,
            "ambiguous basename fallback fails loud with the "
            "enumeration (rc %s)" % rc)

        rc, _o, _e = spawn(["--selftest", "--attest", att_path])
        vec("selftest-standalone-only-rc2", rc == 2,
            "--selftest combined with a run flag is a usage error "
            "(rc %s)" % rc)
        rc, _o, _e = spawn(["--report", rep_path])
        vec("usage-missing-attest-rc2", rc == 2,
            "missing --attest is a usage error (rc %s)" % rc)

        # ---- source language gate (self face: zero CJK, zero em-dash)
        with open(script, "rb") as fh:
            src = fh.read().decode("utf-8")
        cjk = any("\u2e80" <= ch <= "\u9fff" or "\uf900" <= ch <= "\ufaff"
                  or "\uff00" <= ch <= "\uffef" for ch in src)
        vec("source-language-gate",
            not cjk and "\u2014" not in src,
            "the source carries zero CJK and zero em-dash characters")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("selftest: %d vector(s), %d FAIL" % (total[0], len(fails)))
    if fails:
        print("selftest RED: %s" % ", ".join(fails))
        return 1
    return 0


def dump_synth(payload, tmp, tag):
    """Write a synthetic payload to a temp file and return the path
    (selftest helper; keeps the vector faces compact)."""
    path = os.path.join(tmp, "synth_%s.json" % tag)
    dump_json(payload, path)
    return path


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.selftest:
        if args.attest is not None or args.report is not None \
                or args.out is not None or args.basename_fallback:
            build_parser().error("--selftest runs standalone; combine it "
                                 "with no run flags")
        return selftest()
    if args.attest is None or args.report is None or args.out is None:
        build_parser().error("--attest, --report and --out are required "
                             "for the run face")
    return run_face(args)


if __name__ == "__main__":
    sys.exit(main())
