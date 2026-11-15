#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jargon_apply.py - apply the jargon-to-standard map to prose faces.

Purpose.  Reads seeds/jargon/jargon-map.json (62 entries) read-only and
  drives the E2 application face: plan every machine-applicable occurrence
  of a banned face on .py/.sh/.md prose faces; behind --apply only, splice
  the mapped standard in and rescan via tools/norm_lint.py with the
  projected table; residue zero is the exit-zero gate and a second apply
  plans zero would-fix items.  rewrite_or_delete rows are never applied by
  machine (human findings); rows whose note records a sense split or
  context guard, and rows with context-keyed slash alternatives, are
  guarded (default reject-and-report; --guarded-interactive emits the
  query file); carve-outs ride the exempt mechanism; backticks are masked.
  The map's own source table (--a2-table) is never a wash target.

Interface.  Pure functions load_map, project_table, plan_rewrites,
  apply_rewrites; CLI --file | --tree with --plan (default zero writes) |
  --apply, --json, --guarded-interactive, --selftest.

Dependencies.  Python 3 standard library only; tools/norm_lint.py is the
  same-source matcher, prose-face extraction, and rescan detector (absent
  module exits 9); the in-repo md table feeds the A2 vector (loud SKIP
  when absent).  Zero network face.

Evidence.  --selftest: seed contract; classification; derive_after
  vectors; projector byte equality; loader round-trip; A2 row-equality
  diff of the 13 md-provenance rows; apply idempotence; guarded
  rejection; carve-out silence; backtick masking; scan parity.

Exit-codes.  0 clean or residue zero after apply; 1 hits, residue, or a failed vector; 2 usage; 9 missing input."""

import argparse
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SCHEMA = "rocqwash.jargon-apply.report/1"
TOOL = "jargon_apply"
FACES = (".py", ".sh", ".md")
WINDOW = 40

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL_PATH = os.path.join(REPO_ROOT, "tools", "norm_lint.py")
DEFAULT_MAP_PATH = os.path.join(REPO_ROOT, "seeds", "jargon", "jargon-map.json")
DEFAULT_A2_PATH = os.path.join(REPO_ROOT, "docs", "jargon-to-standard-mapping-v1.md")
AUTONOMY_PATH = os.path.join(REPO_ROOT, "autonomy.json")
AUTONOMY_DEFAULT = {"mode": "auto", "admission_threshold": 0.8,
                    "max_unreviewed_rounds": 12, "oscillation_alert": 2}

# fixed suggestion cell for rewrite_or_delete rows in the projected table
# (seed SPEC section 2 projection rule, verbatim)
UNMAPPED_SUGGEST = "rewrite per context or delete (no fixed standard recorded)"

# note markers that turn a replace row into a guarded row (seed SPEC
# section 3: rows whose note records a sense split or a context guard need
# per-row handling before any machine apply)
NOTE_GUARD_MARKERS = ("guarded row", "per-row handling", "sense split",
                      "splits the sense", "rules the face out",
                      "narrative sense only")
# a note routing the carve-out to the exempt mechanism is not a guard: the
# preserve ruling rides the loader exempt regex, line-scoped
NOTE_EXEMPT_ROUTING = "exempt regex carries"

_NL = None


def fail(msg, code):
    sys.stderr.write(TOOL + ": " + msg + "\n")
    raise SystemExit(code)


def norm_lint_module():
    """Load tools/norm_lint.py by path so import works from any caller."""
    global _NL
    if _NL is None:
        if not os.path.isfile(NL_PATH):
            fail("detector module missing (same-source dependency): " + NL_PATH, 9)
        spec = importlib.util.spec_from_file_location("rqw_norm_lint_host", NL_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _NL = mod
    return _NL


def load_map(path):
    """Read and validate the jargon map JSON; fail loud, never silently."""
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        fail("jargon map unreadable: " + path + " (" + str(exc) + ")", 9)
    try:
        m = json.loads(raw)
    except ValueError as exc:
        fail("jargon map is not valid JSON: " + path + " (" + str(exc) + ")", 9)
    if not isinstance(m, dict) or m.get("schema") != "rocqwash-jargon-map/1":
        fail("jargon map schema mismatch in " + path, 1)
    ents = m.get("entries")
    if not isinstance(ents, list) or not ents:
        fail("jargon map carries no entries: " + path, 1)
    if isinstance(m.get("count"), int) and m["count"] != len(ents):
        fail("jargon map count label %r != %d entries"
             % (m.get("count"), len(ents)), 1)
    seen = set()
    for e in ents:
        eid = e.get("id")
        face = e.get("face")
        disp = e.get("disposition")
        if not isinstance(eid, str) or not eid:
            fail("entry without id in " + path, 1)
        if not isinstance(face, str) or not face:
            fail(eid + ": face must be a non-empty string", 1)
        if face in seen:
            fail("duplicate jargon face " + repr(face) + " in " + path, 1)
        seen.add(face)
        if disp not in ("replace", "rewrite_or_delete"):
            fail(eid + ": bad disposition " + repr(disp), 1)
        if disp == "replace" and not isinstance(e.get("standard"), str):
            fail(eid + ": replace entry without a standard cell", 1)
        if disp == "rewrite_or_delete" and e.get("standard") is not None:
            fail(eid + ": rewrite_or_delete entry carries a standard", 1)
        if not isinstance(e.get("exempts"), list) or \
                any(not isinstance(x, str) for x in e.get("exempts") or []):
            fail(eid + ": exempts must be a list of strings", 1)
    return m


def _split_paren_aware(cell, sep):
    """Split on sep outside fullwidth parentheses; inside-paren seps stay."""
    parts, buf, depth = [], [], 0
    for ch in cell:
        if ch == "\uFF08":
            depth += 1
        elif ch == "\uFF09":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return parts


def derive_after(entry):
    """Deterministic replacement text for one map entry, or None when the
    standard cell needs a context choice (guarded).

    Ordered rules, all documented: strip fullwidth-parenthetical annotations
    (they carry guards and context notes, never literal replacement text);
    an arrow-form cell is a directive row, so the pair whose left side equals
    the face wins and its right side is the replacement, else a single
    arrowless part is the primary form; a paren-free cell with slash
    alternatives is context-keyed and returns None (alternation guard).
    """
    nlm = norm_lint_module()
    cell = entry.get("standard") or ""
    bare = nlm.RE_FW_PAREN.sub("", cell).strip()
    if not bare:
        return None
    if "\u2192" in bare:
        parts = _split_paren_aware(cell, "\uFF1B")
        for part in parts:
            if "\u2192" in nlm.RE_FW_PAREN.sub("", part):
                left, right = part.split("\u2192", 1)
                if nlm.RE_FW_PAREN.sub("", left).strip() == entry["face"]:
                    out = nlm.RE_FW_PAREN.sub("", right).strip()
                    return out or None
        plain = [nlm.RE_FW_PAREN.sub("", p).strip() for p in parts
                 if "\u2192" not in nlm.RE_FW_PAREN.sub("", p)]
        if len(plain) == 1 and plain[0]:
            return plain[0]
        return None
    if " / " in bare or "\uFF0F" in bare:
        return None
    return bare


def guard_reason(entry):
    """Classify one entry: None when machine-applicable, else the reason."""
    note = (entry.get("note") or "").lower()
    if NOTE_EXEMPT_ROUTING in note:
        return None
    for marker in NOTE_GUARD_MARKERS:
        if marker in note:
            return "note-guard"
    if derive_after(entry) is None:
        cell = entry.get("standard") or ""
        bare = norm_lint_module().RE_FW_PAREN.sub("", cell).strip()
        if " / " in bare or "\uFF0F" in bare:
            return "alternation-guard"
        return "underivable-standard"
    return None


def build_records(m):
    """Per-entry matcher records, longest face first (loader sort parity).

    Regex objects and compiled exempts come from norm_lint.JargonTerm so the
    matcher is the same source as the detector; claiming every planned span
    (not only the first hit per face) is a deliberate strengthening that
    cannot diverge on this map because all 62 faces are CJK words and the
    whole-word adjacency rule already blocks cross-face overlaps.
    """
    nlm = norm_lint_module()
    recs = []
    for e in m["entries"]:
        disp = e["disposition"]
        if disp == "rewrite_or_delete":
            after, reason = None, "rewrite_or_delete"
        else:
            after = derive_after(e)
            reason = guard_reason(e)
            if reason is not None:
                after = None
            elif after is None:
                reason = "underivable-standard"
            else:
                reason = "replace"
        jt = nlm.JargonTerm(e["face"],
                            e.get("standard") or UNMAPPED_SUGGEST,
                            e.get("exempts") or [])
        recs.append({"face_id": e["id"], "term": e["face"], "note": e.get("note"),
                     "after": after,
                     "disposition": "replace" if reason == "replace" else "human",
                     "reason": reason, "regex": jt.regex, "exempts": jt.exempts})
    recs.sort(key=lambda r: (-len(r["term"]), r["term"]))
    return recs


def _windows(line, start, end, after):
    """Before window on the original line and the matching after preview."""
    radius = max(0, (WINDOW - (end - start)) // 2)
    lo = max(0, start - radius)
    hi = min(len(line), end + radius)
    before = line[lo:hi]
    after_preview = None
    if after is not None:
        after_preview = line[lo:start] + after + line[end:hi]
    return before, after_preview


def _plan_lines(line_items, recs):
    """Occurrence-level plan over (lineno, line) pairs.

    Mirror of norm_lint.jargon_findings per line: backtick masking, longest
    face first, line-scoped exempt skip, overlap rejection; every surviving
    occurrence is planned (the detector records one finding per face per
    line, the applier needs all of them to reach residue zero).
    """
    nlm = norm_lint_module()
    entries = []
    for lineno, txt in line_items:
        work = nlm.mask_backticks(txt)
        claimed = []
        for rec in recs:
            if any(rx.search(work) for rx in rec["exempts"]):
                continue
            for mt in rec["regex"].finditer(work):
                start, end = mt.span()
                if any(start < pe and ps < end for ps, pe in claimed):
                    continue
                claimed.append((start, end))
                before, after_preview = _windows(txt, start, end, rec["after"])
                entries.append({
                    "face_id": rec["face_id"], "term": rec["term"],
                    "line": lineno, "start": start, "end": end,
                    "before": before, "after": after_preview,
                    "replacement": rec["after"],
                    "disposition": rec["disposition"], "reason": rec["reason"],
                })
    return entries


def plan_rewrites(text, m):
    """Zero-write plan over the whole text (every line scanned)."""
    recs = build_records(m)
    items = [(i + 1, line) for i, line in enumerate(text.splitlines())]
    return _plan_lines(items, recs)


def _split_lines_keepings(text):
    """Split into (content, ending) pairs; join reconstructs byte-for-byte."""
    if text == "":
        return []
    out = []
    start = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\r":
            if i + 1 < n and text[i + 1] == "\n":
                out.append((text[start:i], "\r\n"))
                i += 2
            else:
                out.append((text[start:i], "\r"))
                i += 1
            start = i
        elif ch == "\n":
            out.append((text[start:i], "\n"))
            i += 1
            start = i
        else:
            i += 1
    out.append((text[start:], ""))
    if len(out) > 1 and out[-1] == ("", ""):
        out.pop()
    return out


def apply_rewrites(text, entries):
    """Splice machine-disposition entries into the text; returns
    (new_text, applied).  Entries are re-verified at their recorded span
    (line content equals the face there) before splicing with the plain
    replacement text; stale or foreign spans are skipped and simply stay out
    of applied.  Human-disposition entries are never applied.  Line endings
    are preserved byte-for-byte.
    """
    machine = [e for e in entries if e.get("disposition") == "replace"]
    lines = _split_lines_keepings(text)
    by_line = {}
    for e in machine:
        by_line.setdefault(e["line"], []).append(e)
    applied = []
    for lineno, pair in enumerate(lines, 1):
        group = by_line.get(lineno)
        if not group:
            continue
        content, ending = pair
        group.sort(key=lambda e: e["start"], reverse=True)
        for e in group:
            start, end = e["start"], e["end"]
            replacement = e.get("replacement")
            if content[start:end] != e["term"] or not replacement:
                continue
            content = content[:start] + replacement + content[end:]
            applied.append(e)
        lines[lineno - 1] = (content, ending)
    new_text = "".join(c + e for c, e in lines)
    applied.sort(key=lambda e: (e["line"], e["start"]))
    return new_text, applied


def project_table(m):
    """Canonical projection (seed SPEC section 2, one data row per entry).

    Row shape and cell rules equal the seed test projector (tag cell: short
    source tag; exempt cell: semicolon-joined regexes, empty when none); the
    separator-first head row is skipped by the loader dash-run rule, so the
    table loads with exactly one active term per entry.
    """
    rows = ["|---|---|---|---|\n"]
    for e in m["entries"]:
        std = e["standard"] if e["disposition"] == "replace" else UNMAPPED_SUGGEST
        src = e.get("standard_source") or ""
        if "annotation-whitepaper" in src:
            tag = "annotation-track"
        elif src:
            tag = "tool-track"
        else:
            tag = "rewrite-or-delete"
        cells = [e["face"], std, tag, ";".join(e.get("exempts") or [])]
        rows.append("| " + " | ".join(cells) + " |\n")
    return "".join(rows)


def parse_md_rows(path):
    """Loader-grammar rows of an md pipe table: (lineno, face, standard)."""
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            rows = fh.read().splitlines()
    except OSError as exc:
        fail("a2 table unreadable: " + path + " (" + str(exc) + ")", 9)
    out = []
    for lineno, raw in enumerate(rows, 1):
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        first = cells[0] if cells else ""
        if not first or "\u9ED1\u8BDD" in first or set(first) <= set("- "):
            continue
        if len(cells) < 3:
            continue
        for part in re.split(r"\uFF0F|/", first):
            name = part.strip()
            if name:
                out.append((lineno, name, cells[1]))
    return out


def a2_diff(m, md_path):
    """A2 row-equality duty, mechanically scoped by map provenance.

    The map transcribes exactly two source faces: the annotation whitepaper
    (not in this repository) and the in-repo md table.  The equality duty
    binds the md-provenance rows: for each of them the md row must exist
    exactly once and the standard cell must equal the transcribed cell,
    byte for byte.  Returns (diffs, checked, md_rows).
    """
    rows = parse_md_rows(md_path)
    index = {}
    for lineno, face, standard in rows:
        index.setdefault(face, []).append((lineno, standard))
    diffs = []
    checked = 0
    for e in m["entries"]:
        src = e.get("standard_source") or ""
        if not src.startswith("rocqwash docs/jargon-to-standard-mapping-v1.md"):
            continue
        checked += 1
        found = index.get(e["face"]) or []
        if len(found) != 1:
            diffs.append(e["id"] + ": md rows for the face: "
                         + str(len(found)) + " (need exactly 1)")
            continue
        if found[0][1] != e["standard"]:
            diffs.append(e["id"] + ": standard cell differs from md line "
                         + str(found[0][0]))
    return diffs, checked, len(rows)


def read_autonomy():
    """The mode switch of the round ledger section; closed class set here."""
    if not os.path.isfile(AUTONOMY_PATH):
        return dict(AUTONOMY_DEFAULT), "default"
    try:
        with io.open(AUTONOMY_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        fail("autonomy.json unreadable: " + str(exc), 1)
    mode = data.get("mode", AUTONOMY_DEFAULT["mode"])
    if mode not in ("auto", "gated"):
        fail("autonomy.json has an unknown mode " + repr(mode), 1)
    return data, "autonomy.json"


def _read_text(path):
    try:
        with io.open(path, "r", encoding="utf-8", newline="") as fh:
            text = fh.read()
    except OSError as exc:
        fail("unreadable: " + path + " (" + str(exc) + ")", 9)
    had_bom = text.startswith("\ufeff")
    if had_bom:
        text = text.lstrip("\ufeff")
    return text, had_bom


def _prose_segments(kind, text, nlm):
    """Prose-face line items for one file; parse errors return (None, err)."""
    if kind == "py":
        segs, _first_doc, err = nlm.py_docface(text)
        if err:
            return None, err
        return segs, None
    if kind == "sh":
        segs, _ = nlm.sh_docface(text)
        return segs, None
    return [(i + 1, line) for i, line in enumerate(text.splitlines())], None


def _collect_targets(args, skip_abs):
    if args.file:
        if not os.path.isfile(args.file):
            fail("file not found: " + args.file, 9)
        ext = os.path.splitext(args.file)[1].lower()
        if ext not in FACES:
            fail("unsupported face (need .py/.sh/.md): " + args.file, 2)
        ap = os.path.abspath(args.file)
        if ap in skip_abs:
            fail("target file is the wash map's own source table; a tool "
                 "never washes its own map: " + args.file, 1)
        return [("file", os.path.basename(ap), ap, ext[1:])], None
    if not os.path.isdir(args.tree):
        fail("tree root not found: " + args.tree, 9)
    root_abs = os.path.abspath(args.tree)
    files, archives = norm_lint_module().collect_files(root_abs, skip_abs)
    return [("tree", rel, ap, kind) for rel, ap, kind in files], root_abs


def _rescan(args, target_abs, root_abs, table_path, tmpdir):
    """Detector rerun after apply: norm_lint fed with the projected table."""
    nlm = norm_lint_module()
    out_path = os.path.join(tmpdir, "rescan.json")
    cmd = [sys.executable, "-I", NL_PATH,
           "--tree" if root_abs else "--file", target_abs,
           "--jargon-map", table_path, "--json", out_path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=300)
    except OSError as exc:
        fail("rescan detector could not start: " + str(exc), 9)
    if proc.returncode == 9:
        fail("rescan detector reports missing input (rc 9)", 9)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-400:]
        fail("rescan detector failed (rc %d): %s" % (proc.returncode, tail), 1)
    try:
        with io.open(out_path, "r", encoding="utf-8") as fh:
            report = json.load(fh)
    except (OSError, ValueError) as exc:
        fail("rescan report unreadable: " + str(exc), 1)
    residue = 0
    for rec in report.get("files") or []:
        for fd in rec.get("findings") or []:
            if fd.get("kind") == "jargon":
                residue += 1
    per_file = {}
    for rec in report.get("files") or []:
        per_file[rec.get("path")] = sum(
            1 for fd in rec.get("findings") or [] if fd.get("kind") == "jargon")
    return {"ran": True, "tool": "norm_lint", "rc": proc.returncode,
            "jargon_findings": residue, "per_file": per_file}


def _write_json(path, data):
    p = os.path.abspath(path)
    d = os.path.dirname(p)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def _write_guarded_queries(rows, out_path):
    p = os.path.abspath(out_path)
    d = os.path.dirname(p)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(p, "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def run_plan_or_apply(args):
    mode = "apply" if args.apply else "plan"
    map_path = args.jargon_map or DEFAULT_MAP_PATH
    if not os.path.isfile(map_path):
        fail("jargon map not found: " + map_path, 9)
    m = load_map(map_path)
    autonomy, autonomy_source = read_autonomy()
    nlm = norm_lint_module()
    recs = build_records(m)
    skip_abs = set()
    if args.json:
        skip_abs.add(os.path.abspath(args.json))
    if args.guarded_interactive:
        skip_abs.add(os.path.abspath(args.guarded_out))
    # Self-reference guard: the wash map's own source table carries the
    # banned faces by construction.  Rewriting it would strip the faces it
    # must supply (13 contract rows) and break the seed's pinned-source
    # md5 contract.  A tool never washes its own map.
    skip_abs.add(os.path.abspath(args.a2_table or DEFAULT_A2_PATH))
    targets, root_abs = _collect_targets(args, skip_abs)
    tmpdir = tempfile.mkdtemp(prefix="rqw_jargon_apply_")
    applied_total = 0
    failed_total = 0
    machine_total = 0
    human_total = 0
    parse_errors = 0
    query_rows = []
    file_rows = []
    try:
        for scope, rel, ap, kind in targets:
            text, had_bom = _read_text(ap)
            segs, err = _prose_segments(kind, text, nlm)
            row = {"path": rel, "kind": kind, "scanned": True,
                   "would_fix": 0, "human": 0, "rewrites": [], "human_findings": []}
            if err is not None:
                row["scanned"] = False
                row["parse_error"] = err
                parse_errors += 1
                file_rows.append(row)
                continue
            entries = _plan_lines(segs, recs)
            machine = [e for e in entries if e["disposition"] == "replace"]
            human = [e for e in entries if e["disposition"] == "human"]
            row["would_fix"] = len(machine)
            row["human"] = len(human)
            row["rewrites"] = machine
            row["human_findings"] = human
            machine_total += len(machine)
            human_total += len(human)
            if mode == "apply" and machine:
                new_text, applied = apply_rewrites(text, machine)
                failed = len(machine) - len(applied)
                failed_total += failed
                applied_total += len(applied)
                if applied and new_text != text:
                    with io.open(ap, "w", encoding="utf-8", newline="") as fh:
                        if had_bom:
                            fh.write("\ufeff")
                        fh.write(new_text)
                row["applied"] = len(applied)
                row["apply_failed"] = failed
                row["written"] = bool(applied) and new_text != text
            for e in human:
                query_rows.append({
                    "face_id": e["face_id"], "term": e["term"], "file": rel,
                    "line": e["line"], "before": e["before"],
                    "reason": e["reason"],
                    "note": dict((r["face_id"], r["note"]) for r in recs).get(e["face_id"]),
                    "instruction": "human wording needed: state the replacement "
                                   "text for this occurrence or confirm deletion; "
                                   "the engine never machine-applies this row",
                })
            file_rows.append(row)
        rescan = {"ran": False, "detail": "plan mode is zero-write"}
        if mode == "apply":
            # residue-zero gate of the machine pass: the rescan table
            # carries the machine-applicable faces only; guarded and
            # rewrite_or_delete rows are human findings the apply never
            # touches, so counting them as residue would make exit zero
            # unreachable on any mixed face
            machine_ids = set(r["face_id"] for r in recs
                              if r["reason"] == "replace")
            machine_map = dict(m)
            machine_map["entries"] = [e for e in m["entries"]
                                      if e["id"] in machine_ids]
            table_path = os.path.join(tmpdir, "jargon-map.table.md")
            with io.open(table_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(project_table(machine_map))
            target_abs = root_abs if root_abs else os.path.abspath(args.file)
            rescan = _rescan(args, target_abs, root_abs, table_path, tmpdir)
            for row in file_rows:
                if row.get("scanned"):
                    row["residue_jargon"] = rescan["per_file"].get(row["path"], 0)
        if args.guarded_interactive and query_rows:
            _write_guarded_queries(query_rows, args.guarded_out)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    report = {
        "schema": SCHEMA, "tool": TOOL, "mode": mode,
        "target": args.tree if args.tree else args.file,
        "target_kind": "tree" if args.tree else "file",
        "map": {"path": os.path.abspath(map_path), "schema": m.get("schema"),
                "entries": len(m["entries"])},
        "autonomy": {"mode": autonomy.get("mode"), "source": autonomy_source},
        "files": file_rows,
        "summary": {"files": len(file_rows), "parse_errors": parse_errors,
                    "would_fix": machine_total, "human": human_total,
                    "applied": applied_total if mode == "apply" else 0,
                    "apply_failed": failed_total if mode == "apply" else 0,
                    "residue_jargon": rescan.get("jargon_findings", 0)
                    if mode == "apply" else 0},
        "rescan": rescan,
    }
    if args.json:
        _write_json(args.json, report)
    print("%s %s: mode=%s files=%d would_fix=%d human=%d applied=%d residue=%d"
          % (TOOL, SCHEMA, mode, len(file_rows), machine_total, human_total,
             applied_total, report["summary"]["residue_jargon"]))
    if args.guarded_interactive and query_rows:
        print("guarded query file: " + os.path.abspath(args.guarded_out)
              + " (rows=%d)" % len(query_rows))
    if mode == "plan":
        hits = machine_total + human_total
        print("VERDICT " + ("HITS" if hits else "CLEAN")
              + " (plan is zero-write)")
        return 1 if hits else 0
    ok = failed_total == 0 and rescan.get("jargon_findings", 0) == 0
    print("VERDICT " + ("GREEN" if ok else "RESIDUE")
          + " (residue zero is the exit-zero gate)")
    return 0 if ok else 1


# --- selftest vectors (in-process, temporary fixtures, standalone) ---

FIX_MAP = {
    "schema": "rocqwash-jargon-map/1", "engine": "jargon", "count": 5,
    "entries": [
        {"id": "F001", "face": "\u6253\u5305", "standard": "\u5c01\u88c5",
         "standard_language": "zh", "disposition": "replace", "exempts": [],
         "note": None},
        {"id": "F002", "face": "\u8d26\u76ee", "standard": None,
         "standard_language": None, "disposition": "rewrite_or_delete",
         "exempts": [], "note": None},
        {"id": "F003", "face": "\u63a2\u9488", "standard": "\u68c0\u9a8c",
         "standard_language": "zh", "disposition": "replace", "exempts": [],
         "note": None},
        {"id": "F004", "face": "\u6d88\u8d39", "standard": "\u4f7f\u7528",
         "standard_language": "zh", "disposition": "replace",
         "exempts": ["\u96f6\u6d88\u8d39"], "note": "Carve-out transcribed: "
         "the exempt regex carries that preserve ruling."},
        {"id": "F005", "face": "\u65d7\u8230", "standard": "\u4e3b",
         "standard_language": "zh", "disposition": "replace", "exempts": [],
         "note": "Guarded row: the standard cell carries a context guard; "
                 "per-row handling required before any machine apply."},
    ],
}

FIX_TEXT = (
    "intro line with \u6253\u5305 and \u63a2\u9488 words\n"
    "guarded \u65d7\u8230 case stays\n"
    "the \u8d26\u76ee word is human only\n"
    "a bare \u6d88\u8d39 fires on this line\n"
    "the \u96f6\u6d88\u8d39 compound stays silent\n"
    "cite `\u63a2\u9488` only, masked\n"
)

FIX_PY = (
    '"""fixture: parity vector for the planner.\n'
    "\n"
    "Purpose.  Carries known faces on prose lines.\n"
    "Interface.  None (fixture).\n"
    "Dependencies.  None.\n"
    "Evidence.  Selftest vector.\n"
    "Exit-codes.  0.\n"
    '"""\n'
    "# a \u6253\u5305 hit and a \u63a2\u9488 hit on one comment line\n"
    "VALUE = \"\u6253\u5305 in a string literal is not a prose face\"\n"
    "x = 1\n"
)


def _vec(results, name, ok, detail):
    results.append((name, ok, detail))


def run_selftest(args):
    results = []
    nlm = norm_lint_module()
    seed_path = DEFAULT_MAP_PATH
    have_seed = os.path.isfile(seed_path)
    a2_path = args.a2_table or DEFAULT_A2_PATH
    m_real = load_map(seed_path) if have_seed else None

    # vector 1: seed data contract and the mandated 62-entry count
    if m_real is None:
        _vec(results, "seed-contract", None, "SKIP: seed map not found")
    else:
        ents = m_real["entries"]
        ok = (m_real.get("schema") == "rocqwash-jargon-map/1"
              and len(ents) == 62 and m_real.get("count") == 62
              and len(set(e["face"] for e in ents)) == 62)
        _vec(results, "seed-contract", ok,
             "62 entries, unique faces, schema pinned" if ok
             else "seed shape drifted: entries=%d count=%r"
                  % (len(ents), m_real.get("count")))

    # vector 2: entry classification with reasons (snapshot drift sentinel)
    if m_real is None:
        _vec(results, "classification", None, "SKIP: seed map not found")
    else:
        recs = build_records(m_real)
        machine = sorted(r["face_id"] for r in recs if r["reason"] == "replace")
        note_guard = sorted(r["face_id"] for r in recs if r["reason"] == "note-guard")
        alternation = sorted(r["face_id"] for r in recs
                             if r["reason"] == "alternation-guard")
        rod = sorted(r["face_id"] for r in recs if r["reason"] == "rewrite_or_delete")
        want_note = ["J012", "J013", "J018", "J046", "J047"]
        want_alt = ["J001", "J003", "J004", "J016", "J023", "J024", "J048",
                    "J049", "J050", "J056", "J057", "J061"]
        want_rod = ["J032", "J033", "J034"]
        ok = (len(machine) == 42 and note_guard == want_note
              and alternation == want_alt and rod == want_rod)
        _vec(results, "classification", ok,
             "machine=42 note-guard=5 alternation-guard=12 rewrite_or_delete=3"
             if ok else
             "machine=%d note=%s alt=%s rod=%s" % (len(machine), note_guard,
                                                   alternation, rod))

    # vector 3: derive_after vectors on the real map, by face id
    if m_real is None:
        _vec(results, "derive-after", None, "SKIP: seed map not found")
    else:
        by_id = dict((e["id"], e) for e in m_real["entries"])
        want = {"J005": "\u88c5\u914d", "J006": "\u5c01\u88c5",
                "J042": "\u6ce8\u518c", "J054": "\u63d0\u4f9b",
                "J058": "\u4f59\u91cf\u6d88\u9664\u8bba\u8bc1",
                "J062": "\u63a5\u53e3\u53c2\u6570",
                "J009": "\u4f7f\u7528", "J022": "machine ruling"}
        bad = [k for k, v in want.items() if derive_after(by_id[k]) != v]
        bad += [k for k in ("J001", "J003", "J004", "J016", "J018", "J023",
                            "J024", "J048", "J049", "J050", "J056", "J057",
                            "J061")
                if derive_after(by_id[k]) is not None]
        bad += [k for k in ("J012", "J013", "J046", "J047")
                if derive_after(by_id[k]) is None]
        _vec(results, "derive-after", not bad,
             "8 arrow/plain cells derive; 13 alternation cells derive none; "
             "4 note-guard cells derive a plain form (note guards them)"
             if not bad else "wrong derivation for: " + ", ".join(bad))

    # vector 4: projector form equals the seed test projector byte for byte
    snippet_path = os.path.join(REPO_ROOT, "seeds", "jargon", "test_snippet.py")
    if m_real is None or not os.path.isfile(snippet_path):
        _vec(results, "projector-canonical-form", None,
             "SKIP: seed map or seed test projector not found")
    else:
        spec = importlib.util.spec_from_file_location("rqw_jargon_seed_proj",
                                                      snippet_path)
        seed_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(seed_mod)
        tmp = tempfile.mkdtemp(prefix="rqw_jargon_selftest_")
        try:
            theirs = os.path.join(tmp, "theirs.md")
            seed_mod.project_table(m_real, theirs)
            with io.open(theirs, "r", encoding="utf-8") as fh:
                theirs_text = fh.read()
            mine = project_table(m_real)
            ok = mine == theirs_text
            _vec(results, "projector-canonical-form", ok,
                 "byte-identical to the seed projector" if ok
                 else "row shape differs from the seed projector")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # vector 5: loader round-trip of the projection
    if m_real is None:
        _vec(results, "loader-roundtrip", None, "SKIP: seed map not found")
    else:
        table = project_table(m_real)
        tmp = tempfile.mkdtemp(prefix="rqw_jargon_selftest_")
        try:
            tp = os.path.join(tmp, "projected.md")
            with io.open(tp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(table)
            terms = nlm.load_jargon_map(tp)
            got = sorted(t.term for t in terms)
            want = sorted(e["face"] for e in m_real["entries"])
            by_face = dict((e["face"], e) for e in m_real["entries"])
            bad = []
            if got != want or len(terms) != 62:
                bad.append("active face set mismatch")
            for t in terms:
                e = by_face[t.term]
                want_suggest = (e["standard"] if e["disposition"] == "replace"
                                else UNMAPPED_SUGGEST)
                if t.suggest != want_suggest:
                    bad.append(t.term + ": suggest mismatch")
            _vec(results, "loader-roundtrip", not bad,
                 "62 active faces with transcribed suggestions" if not bad
                 else "; ".join(bad[:5]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # vector 6: A2 row-equality diff against the in-repo md table
    if m_real is None:
        _vec(results, "a2-row-equality", None, "SKIP: seed map not found")
    elif not os.path.isfile(a2_path):
        _vec(results, "a2-row-equality", None,
             "SKIP: in-repo md table not found at " + a2_path)
    else:
        diffs, checked, md_rows = a2_diff(m_real, a2_path)
        ok = not diffs and checked == 13
        _vec(results, "a2-row-equality", ok,
             "13/13 md-provenance rows equal; md table parsed faces=%d; "
             "scope note: 46 annotation-track and 3 rewrite_or_delete rows "
             "come from the whitepaper, outside this repository" % md_rows
             if ok else "diffs: " + "; ".join(diffs[:5]))

    # vectors 7 to 9: functional vectors on the embedded fixture map
    fxdir = tempfile.mkdtemp(prefix="rqw_jargon_selftest_")
    try:
        fxmap_path = os.path.join(fxdir, "fixture-map.json")
        with io.open(fxmap_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(FIX_MAP, ensure_ascii=False, indent=1) + "\n")
        fm = load_map(fxmap_path)

        # vector 7: plan, apply, replan idempotence on the fixture text
        plan1 = plan_rewrites(FIX_TEXT, fm)
        machine1 = [e for e in plan1 if e["disposition"] == "replace"]
        human1 = [e for e in plan1 if e["disposition"] == "human"]
        new_text, applied = apply_rewrites(FIX_TEXT, plan1)
        plan2 = plan_rewrites(new_text, fm)
        machine2 = [e for e in plan2 if e["disposition"] == "replace"]
        _, applied2 = apply_rewrites(new_text, plan2)
        ok = (len(machine1) == 3 and len(applied) == 3
              and len(human1) == 2 and machine2 == [] and applied2 == []
              and "\u6253\u5305" not in new_text
              and "\u65d7\u8230" in new_text and "\u8d26\u76ee" in new_text
              and "\u96f6\u6d88\u8d39" in new_text and "\u63a2\u9488" in new_text)
        _vec(results, "plan-apply-idempotence", ok,
             "3 machine fixes applied; 2 human rows untouched; replan clean; "
             "second apply applies nothing"
             if ok else
             "machine1=%d applied=%d human1=%d machine2=%d applied2=%d"
             % (len(machine1), len(applied), len(human1), len(machine2),
                len(applied2)))

        # vector 8: carve-out exemption, backtick masking, human rows
        terms_line = [(i + 1, l) for i, l in enumerate(FIX_TEXT.splitlines())]
        plan = _plan_lines(terms_line, build_records(fm))
        got = sorted((e["term"], e["line"]) for e in plan)
        bad = []
        if any(t == "\u6d88\u8d39" and ln == 5 for t, ln in got):
            bad.append("carve-out compound fired")
        if any(t == "\u63a2\u9488" and ln == 6 for t, ln in got):
            bad.append("backtick citation fired")
        if not any(t == "\u8d26\u76ee" and ln == 3 for t, ln in got):
            bad.append("rewrite_or_delete face missing from findings")
        _vec(results, "exemptions-and-masking", not bad,
             "exempt line silent, backtick masked, human row listed"
             if not bad else "; ".join(bad))

        # vector 9: scan parity with norm_lint jargon findings on a py fixture
        table = project_table(fm)
        tp = os.path.join(fxdir, "projected.md")
        with io.open(tp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(table)
        terms = nlm.load_jargon_map(tp)
        segs, _first_doc, err = nlm.py_docface(FIX_PY)
        mine = _plan_lines(segs, build_records(fm))
        mine_set = sorted((e["line"], e["term"]) for e in mine)
        theirs = sorted((f["line"], f["term"])
                        for f in nlm.jargon_findings(segs, terms))
        ok = err is None and mine_set == theirs
        _vec(results, "scan-parity", ok,
             "planner finding set equals norm_lint jargon findings" if ok
             else "mine=%s theirs=%s" % (mine_set, theirs))
    finally:
        shutil.rmtree(fxdir, ignore_errors=True)

    failed = 0
    for name, ok, detail in results:
        if ok is True:
            tag = "PASS"
        elif ok is False:
            tag = "FAIL"
            failed += 1
        else:
            tag = "SKIP"
        print("%s %s - %s" % (tag, name, detail))
    print("summary: %d vectors, %d FAIL" % (len(results), failed))
    return 1 if failed else 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog=TOOL)
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--tree", metavar="DIR",
                       help="plan or apply over DIR for .py/.sh/.md faces")
    group.add_argument("--file", metavar="PATH", help="one face file")
    ap.add_argument("--jargon-map", metavar="P",
                    default=DEFAULT_MAP_PATH, help="jargon map JSON (read-only)")
    ap.add_argument("--plan", action="store_true",
                    help="plan mode, zero writes (default)")
    ap.add_argument("--apply", action="store_true",
                    help="execute would-fix items, then rescan; residue zero "
                         "is the exit-zero gate")
    ap.add_argument("--json", metavar="P", help="write the report JSON there")
    ap.add_argument("--guarded-interactive", action="store_true",
                    help="emit the per-line query file for guarded rows")
    ap.add_argument("--guarded-out", metavar="P",
                    default="jargon-guarded-queries.jsonl",
                    help="guarded query file path")
    ap.add_argument("--selftest", action="store_true",
                    help="run the selftest vectors; standalone")
    ap.add_argument("--a2-table", metavar="P", default=DEFAULT_A2_PATH,
                    help="in-repo md table for the A2 vector")
    args = ap.parse_args(argv)
    if args.selftest:
        if args.tree or args.file or args.json or args.apply or args.plan \
                or args.guarded_interactive:
            fail("--selftest runs standalone; combine it with no scan flags", 2)
        return run_selftest(args)
    if args.apply and args.plan:
        fail("--plan and --apply are mutually exclusive", 2)
    if not args.tree and not args.file:
        ap.error("one of the arguments --tree --file is required")
    return run_plan_or_apply(args)


if __name__ == "__main__":
    sys.exit(main())
