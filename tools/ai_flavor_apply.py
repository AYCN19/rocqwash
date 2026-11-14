#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai_flavor_apply.py - advisory rewrite planner and gated applier for ai-flavor faces.

Purpose.  Plans advisory rewrites from detector findings; applies them only
  through a rewrite provider behind gates: plan mode is zero-write; zh
  ban-remediation faces are human-only and never machine-written; stems
  offer the register neutral forms; sentence faces offer delete-or-restate;
  every write passes a structural guard plus a detector rescan whose zero
  residue gates GREEN; a second cycle on a clean file reports zero would-fix.
Interface.  --file PATH [--json OUT] | --emit-handoff OUT.jsonl |
  --apply-handoff IN.jsonl --state P | --provider http --state P |
  --selftest.  handoff (default, zero network) emits {finding_id, face_id,
  lang, before, candidates, instruction} and ingests {finding_id, choice,
  after_text, model_id}; bad rows are rejected loudly with zero writes;
  http is default-deny (ROCQWASH_MCP_ALLOW_NET=1 plus endpoint, model,
  and key variables; refusal names each missing one; one NETRED row per
  call attempt).  Pure exports: plan_suggestions(text, report),
  emit_handoff(entries), ingest_handoff(text, handoff_rows).
Dependencies.  Python 3 standard library only; detector module
  tools/ai_flavor.py beside this file; seed word-map.json read-only.
Evidence.  Contract volume section 2 lane 3; ai-flavor seed SPEC section 4 path 1; gate4 autofix reference module; selftest on seed fixtures.
Exit-codes.  0 GREEN (plan clean, or apply then rescan residue zero); 1 RED
  (findings or human items, or residue after apply); 2 usage or assertion
  (flag misuse, package rejection, budget cap, report shape); 9 missing
  input (target, seed map, state file, detector module).
"""

# Extended contract (kept outside the docstring so the header stays inside
# the 30-line budget of the annotation standard):
#
# Dispositions.  The seed map splits 36 faces into three rewrite classes:
#   ban-remediation (the ten zh faces; human rewording only, never emitted
#   to a provider, never applied), neutral-direct-form (the fifteen en
#   stems; the provider picks one register-enumerated value per context),
#   delete-or-restate (the eight sentence faces plus the three paragraph
#   initial faces; the provider deletes the span or states the point
#   directly).  Entry fields span_start/span_end are 0-based column
#   offsets inside the hit line; delete_span is the mechanical deletion
#   extent for delete-or-restate entries (the match plus a following
#   whitespace run, plus one directly adjacent comma; when nothing
#   follows, the preceding whitespace run instead).
#
# Subsumption.  When two face matches share text (a stem inside a sentence
#   face, or the three paragraph faces that share one detector branch),
#   the widest or literal-matching entry survives and the covered face ids
#   are recorded under subsumed_face_ids, so one provider row resolves
#   the whole line region.
#
# Provider rows.  --emit-handoff writes one JSON object per provider entry
#   with exactly the six keys named in Interface; candidates carry the
#   seed values verbatim.  --apply-handoff reads filled rows: required
#   keys finding_id, choice, after_text, model_id; the six emit keys may
#   be echoed and must match the fresh plan; any other key, unknown
#   finding_id, duplicate id, illegal choice, empty model_id, or no-op
#   replacement rejects the row.  Ingest is atomic: any rejection leaves
#   the target untouched (exit 2, reasons named per row).
#
# Structural guard.  A line edit survives only when the per-line counts
#   of backtick, quote, parenthesis, bracket, brace, and pipe characters
#   are unchanged; after_text must be single-line, em-dash-free, and free
#   of every seed face.  The apply tail re-runs the detector on the
#   written text; only a zero-residue scan (all 36 faces zero, em-dash
#   zero) yields GREEN, else RED with the residue listed.
#
# Budget cap.  --state records one consumed round per target file per
#   rewrite class; a further apply round on the same pair is refused
#   loudly (exit 2) before any write.  Rounds with zero applied rows
#   record nothing, so the second full cycle on a clean file reports
#   zero would-fix items and leaves state and target untouched.
#
# http provider.  Direct apply path; fires only when the environment gate
#   and the three endpoint variables are all present, refuses loudly
#   naming each missing variable otherwise, and writes one NETRED row
#   per call attempt (URL, time, verdict; failures included) to stderr
#   and to the --json report.  Credential values are never written
#   anywhere.

import argparse
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import time
import urllib.request

TOOL = "ai_flavor_apply"
SEED_SCHEMA = "rocqwash.seeds.ai-flavor.word-map/1.0"
DETECT_SCHEMA = "rocqwash.ai-flavor.report/1"
REPORT_SCHEMA = "rocqwash.ai-flavor.apply.report/1"
STATE_SCHEMA = "rocqwash.ai-flavor.apply-state/1"
KIND_BAN = "ban-remediation"
KIND_NEUTRAL = "neutral-direct-form"
KIND_DELETE = "delete-or-restate"
KINDS = (KIND_BAN, KIND_NEUTRAL, KIND_DELETE)
DELETE_CHOICES = ("delete", "restate")
EM_DASH = "\u2014"
GUARD_TOKENS = ("`", "\"", "'", "(", ")", "[", "]", "{", "}", "|")
ENV_GATE = "ROCQWASH_MCP_ALLOW_NET"
ENV_ENDPOINT = "ROCQWASH_LLM_ENDPOINT"
ENV_MODEL = "ROCQWASH_LLM_MODEL"
ENV_KEY = "ROCQWASH_LLM_KEY"
HTTP_TIMEOUT_S = 60
EMIT_ROW_KEYS = frozenset(("finding_id", "face_id", "lang", "before",
                           "candidates", "instruction"))
FILL_ROW_KEYS = frozenset(("finding_id", "choice", "after_text", "model_id"))
ALLOWED_ROW_KEYS = EMIT_ROW_KEYS | FILL_ROW_KEYS


def fail(msg, code):
    sys.stderr.write(TOOL + ": " + msg + "\n")
    return code


class ApplyError(Exception):
    """Carries a message plus the exit code the CLI must surface."""

    def __init__(self, msg, code):
        Exception.__init__(self, msg)
        self.msg = msg
        self.code = code


def _now_utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------- seed data

def default_word_map_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "seeds", "ai_flavor",
                        "word-map.json")


def load_seed_map(path=None):
    """Read the seed word map; return (map dict, faces indexed by id)."""
    path = path or default_word_map_path()
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ApplyError("seed word map unreadable: %s (%s)" % (path, exc), 9)
    if not isinstance(data, dict) or data.get("schema") != SEED_SCHEMA:
        raise ApplyError("seed word map schema mismatch: %s" % path, 9)
    return data, _faces_by_id(data)


def _faces_by_id(word_map):
    faces = word_map.get("faces") if isinstance(word_map, dict) else None
    if not isinstance(faces, list) or not faces:
        raise ApplyError("word map carries no faces list", 9)
    out = {}
    for face in faces:
        fid = face.get("id") if isinstance(face, dict) else None
        if not isinstance(fid, str) or not fid or fid in out:
            raise ApplyError("face id missing or duplicated: %r" % (fid,), 9)
        branch = face.get("detector_regex_branch")
        if not isinstance(branch, str) or not branch:
            raise ApplyError("face %s carries no detector branch" % fid, 9)
        out[fid] = face
    return out


def _face_kind(face):
    candidates = face.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ApplyError("face %s carries no candidates" % face.get("id"), 9)
    kinds = set()
    for cand in candidates:
        kind = cand.get("kind") if isinstance(cand, dict) else None
        if kind not in KINDS:
            raise ApplyError("face %s carries an unknown candidate kind: %r"
                             % (face.get("id"), kind), 9)
        kinds.add(kind)
    if len(kinds) != 1:
        raise ApplyError("face %s mixes candidate kinds: %r"
                         % (face.get("id"), sorted(kinds)), 9)
    return kinds.pop()


def _face_regex(face):
    flags = re.IGNORECASE if face.get("lang") == "en" else 0
    try:
        return re.compile(face["detector_regex_branch"], flags)
    except re.error as exc:
        raise ApplyError("face %s branch does not compile: %s"
                         % (face.get("id"), exc), 9)


def _face_regexes(word_map):
    return dict((fid, _face_regex(face))
                for fid, face in _faces_by_id(word_map).items())


# ------------------------------------------------------------- pure planning

def _check_report(report):
    if not isinstance(report, dict):
        raise ApplyError("detector report is not an object", 2)
    if report.get("schema") != DETECT_SCHEMA:
        raise ApplyError("detector report schema mismatch (need %s)"
                         % DETECT_SCHEMA, 2)
    if not isinstance(report.get("hits"), list):
        raise ApplyError("detector report carries no hits list", 2)
    em = report.get("em_dash_count")
    if not isinstance(em, int) or isinstance(em, bool) or em < 0:
        raise ApplyError("detector report em_dash_count is not a "
                         "non-negative integer", 2)


def plan_suggestions(text, report, word_map=None):
    """Contract export: detector report in, advisory rewrite entries out.

    One entry per face occurrence; overlapping matches are subsumed into
    the widest entry; finding ids are assigned in deterministic
    (line, column) order.  Zero-write by construction.
    """
    if word_map is None:
        word_map, _ = load_seed_map()
    faces = _faces_by_id(word_map)
    _check_report(report)
    lines = text.split("\n")
    raw = []
    seen_pairs = set()
    for hit in report.get("hits") or []:
        fid = hit.get("face_id")
        line_no = hit.get("line")
        if not isinstance(line_no, int) or isinstance(line_no, bool) \
                or line_no < 1 or line_no > len(lines):
            raise ApplyError("detector hit line out of range: %r"
                             % (line_no,), 2)
        face = faces.get(fid)
        if face is None:
            raise ApplyError("detector hit names unknown face id: %r"
                             % (fid,), 2)
        if hit.get("battery") != face.get("battery"):
            raise ApplyError("detector hit battery mismatch for %s" % fid, 2)
        pair = (line_no, fid)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        line_text = lines[line_no - 1]
        found = list(_face_regex(face).finditer(line_text))
        if not found:
            raise ApplyError("hit not reproducible on line %d for %s"
                             % (line_no, fid), 2)
        for match in found:
            literal = face.get("face")
            exact = isinstance(literal, str) \
                and line_text[match.start():match.end()].lower() \
                == literal.lower()
            raw.append((line_no, match.start(), match.end(), fid, face,
                        0 if exact else 1))
    raw.sort(key=lambda item: (item[0], item[1], -(item[2] - item[1]),
                               item[5], item[3]))
    kept = []
    for item in raw:
        line_no, s, e, fid, face, _flag = item
        host = None
        for cand in kept:
            if cand[0] == line_no and cand[1] <= s and e <= cand[2]:
                host = cand
                break
        if host is None:
            kept.append([line_no, s, e, fid, face, []])
        else:
            host[5].append(fid)
    entries = []
    for n, (line_no, s, e, fid, face, subsumed) in enumerate(kept, 1):
        line_text = lines[line_no - 1]
        kind = _face_kind(face)
        disposition = "human" if kind == KIND_BAN else "provider"
        entry = {
            "finding_id": "af-%04d" % n,
            "line": line_no,
            "face_id": fid,
            "lang": face.get("lang", ""),
            "battery": face.get("battery", ""),
            "kind": kind,
            "disposition": disposition,
            "span_start": s,
            "span_end": e,
            "before": line_text[s:e],
            "candidates": face.get("candidates", []),
            "instruction": _instruction(kind, face),
        }
        if subsumed:
            entry["subsumed_face_ids"] = sorted(subsumed)
        if kind == KIND_DELETE and disposition == "provider":
            ds, de = _delete_extent(line_text, s, e)
            entry["delete_span"] = [ds, de]
        entries.append(entry)
    return entries


def _instruction(kind, face):
    if kind == KIND_NEUTRAL:
        values = [c.get("value") for c in face.get("candidates", [])
                  if isinstance(c, dict) and c.get("value")]
        return ("replace the matched span with the chosen neutral direct "
                "form, inflected to fit the sentence; reply choice one of: "
                "%s; after_text is the full replacement text for the span "
                "and must keep the line's parenthesis, bracket, brace, "
                "quote, backtick, and pipe counts unchanged"
                % ", ".join(values))
    if kind == KIND_DELETE:
        return ("either delete the matched span (choice=delete, after_text "
                "empty; fits discourse connectors and filler phrases) or "
                "state the point directly (choice=restate, after_text is "
                "the replacement text; prefer restate when the span "
                "carries sentence grammar); after_text must not add "
                "newlines or new parenthesis, bracket, brace, quote, "
                "backtick, or pipe characters")
    return ("human rewording only; the register bans this face with no "
            "substitute word; this tool never machine-rewrites it")


def _delete_extent(line_text, s, e):
    """Deletion extent for delete-or-restate entries: swallow the following
    whitespace run, then one directly adjacent comma (and its whitespace);
    when nothing follows, swallow the preceding whitespace run instead."""
    n = len(line_text)
    j = e
    while j < n and line_text[j] in " \t":
        j += 1
    if j < n and line_text[j] == ",":
        j += 1
        while j < n and line_text[j] in " \t":
            j += 1
    if j == e:
        i = s
        while i > 0 and line_text[i - 1] in " \t":
            i -= 1
        return (i, e)
    return (s, j)


# ------------------------------------------------------------ provider faces

def legal_choices(entry):
    kind = entry["kind"]
    if kind == KIND_NEUTRAL:
        return tuple(c.get("value") for c in entry.get("candidates", [])
                     if isinstance(c, dict) and c.get("value"))
    if kind == KIND_DELETE:
        return DELETE_CHOICES
    return ()


def emit_handoff(entries):
    """Contract export: provider entries in, handoff package JSONL out.

    One JSON object per provider entry with exactly the six contract
    keys; human-only entries are never emitted; byte-identical reruns.
    """
    rows = []
    for entry in entries:
        if entry.get("disposition") != "provider":
            continue
        rows.append(json.dumps({
            "finding_id": entry["finding_id"],
            "face_id": entry["face_id"],
            "lang": entry["lang"],
            "before": entry["before"],
            "candidates": entry["candidates"],
            "instruction": entry["instruction"],
        }, sort_keys=True, ensure_ascii=True))
    return "".join(row + "\n" for row in rows)


def _line_struct_ok(old_line, new_line):
    return all(old_line.count(t) == new_line.count(t)
               for t in GUARD_TOKENS)


def _fill_reason(row, entry, seen_ids, lines, face_regexes):
    for key in sorted(FILL_ROW_KEYS):
        if key not in row:
            return "missing_key:" + key
    for key in sorted(row):
        if key not in ALLOWED_ROW_KEYS:
            return "unknown_key:" + key
    if entry is None:
        return "unknown_finding_id"
    fid = entry["finding_id"]
    if fid in seen_ids:
        return "duplicate_finding_id"
    if entry["disposition"] != "provider":
        return "ban_remediation_is_human_only"
    model_id = row["model_id"]
    if not isinstance(model_id, str) or not model_id.strip():
        return "empty_model_id"
    choice = row["choice"]
    if not isinstance(choice, str) or choice not in legal_choices(entry):
        return "illegal_choice"
    after = row["after_text"]
    if not isinstance(after, str):
        return "after_text_not_string"
    if choice == "delete" and after != "":
        return "delete_requires_empty_after_text"
    if choice != "delete":
        if after == "":
            return "empty_after_text"
        if after == entry["before"]:
            return "no_op_replacement"
    if "\n" in after or "\r" in after:
        return "after_text_multiline"
    if EM_DASH in after:
        return "after_text_em_dash"
    for key in ("face_id", "lang", "before"):
        if key in row and row[key] != entry[key]:
            return "mismatch:" + key
    line_text = lines[entry["line"] - 1]
    for other_id in sorted(face_regexes):
        if face_regexes[other_id].search(after):
            return "after_text_fires_face:" + other_id
    if choice == "delete":
        ds, de = entry["delete_span"]
        new_line = line_text[:ds] + line_text[de:]
    else:
        new_line = (line_text[:entry["span_start"]] + after
                    + line_text[entry["span_end"]:])
    if not _line_struct_ok(line_text, new_line):
        return "structural_guard_failed"
    return None


def ingest_handoff(text, handoff_rows, word_map=None, entries=None,
                   detector=None):
    """Contract export: text plus filled handoff rows in; the rewritten
    text, the applied rows, and the rejected rows out.

    Atomic: any rejected row leaves the text untouched and applied empty.
    When entries is omitted the text is re-planned through the detector
    module (pass detector to inject it; lazy-loaded otherwise); the seed
    word map is the default detector vocabulary.
    """
    if word_map is None:
        word_map, _ = load_seed_map()
    if entries is None:
        report = _detect(text, word_map, detector)
        entries = plan_suggestions(text, report, word_map)
    by_id = dict((entry["finding_id"], entry) for entry in entries)
    lines = text.split("\n")
    offsets = [0]
    for line_text in lines:
        offsets.append(offsets[-1] + len(line_text) + 1)
    face_regexes = _face_regexes(word_map)
    applied = []
    rejected = []
    edits = []
    seen_ids = set()
    for idx, row in enumerate(handoff_rows, 1):
        fid = row.get("finding_id") if isinstance(row, dict) else None
        fid = fid if isinstance(fid, str) else ""
        entry = by_id.get(fid) if isinstance(row, dict) else None
        reason = _fill_reason(row, entry, seen_ids, lines, face_regexes) \
            if isinstance(row, dict) else "row_not_object"
        if reason is not None:
            rejected.append({"row": idx, "finding_id": fid,
                             "reason": reason})
            continue
        seen_ids.add(fid)
        line_no = entry["line"]
        line_text = lines[line_no - 1]
        if line_text[entry["span_start"]:entry["span_end"]] \
                != entry["before"]:
            rejected.append({"row": idx, "finding_id": fid,
                             "reason": "stale_plan_entry"})
            continue
        choice = row["choice"]
        after = row["after_text"]
        if choice == "delete":
            ds, de = entry["delete_span"]
            abs_s = offsets[line_no - 1] + ds
            abs_e = offsets[line_no - 1] + de
            expected = line_text[ds:de]
        else:
            abs_s = offsets[line_no - 1] + entry["span_start"]
            abs_e = offsets[line_no - 1] + entry["span_end"]
            expected = entry["before"]
        edits.append((abs_s, abs_e, after if choice != "delete" else "",
                      expected, entry, choice, row["model_id"]))
    for i, edit in enumerate(edits):
        for j, other in enumerate(edits):
            if i != j and edit[0] < other[1] and other[0] < edit[1]:
                rejected.append({"row": i + 1,
                                 "finding_id": edit[4]["finding_id"],
                                 "reason": "overlap_conflict"})
                break
    if rejected:
        return (text, [], rejected)
    edits.sort(key=lambda item: item[0])
    pieces = []
    pos = 0
    for abs_s, abs_e, after, expected, entry, choice, model_id in edits:
        if text[abs_s:abs_e] != expected:
            rejected.append({"row": 0,
                             "finding_id": entry["finding_id"],
                             "reason": "stale_plan_entry"})
            break
        pieces.append(text[pos:abs_s])
        pieces.append(after)
        pos = abs_e
        applied.append({
            "finding_id": entry["finding_id"],
            "line": entry["line"],
            "face_id": entry["face_id"],
            "kind": entry["kind"],
            "choice": choice,
            "before": entry["before"],
            "after": after,
            "model_id": model_id,
        })
    if rejected:
        return (text, [], rejected)
    pieces.append(text[pos:])
    return ("".join(pieces), applied, rejected)


# ------------------------------------------------------------------- budget

def load_state(path):
    if not os.path.exists(path):
        return {"schema": STATE_SCHEMA, "files": {}}
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ApplyError("state file unreadable: %s (%s)" % (path, exc), 9)
    if not isinstance(state, dict) \
            or not isinstance(state.get("files"), dict):
        raise ApplyError("state file out of shape: %s" % path, 9)
    return state


def save_state(path, state):
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(parent):
        raise ApplyError("state directory absent: %s" % parent, 9)
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(state, sort_keys=True, ensure_ascii=True,
                            indent=2) + "\n")


def _path_key(target):
    return os.path.abspath(target).replace(os.sep, "/")


def check_budget(state, path_key, kinds):
    """Refusals for classes that already consumed their one round."""
    files = state.get("files") or {}
    classes = (files.get(path_key) or {}).get("classes") or {}
    refusals = []
    for kind in sorted(set(kinds)):
        record = classes.get(kind)
        if isinstance(record, dict) and record.get("rounds", 0) >= 1:
            refusals.append({"file": path_key, "class": kind,
                             "rounds": record.get("rounds", 0)})
    return refusals


def record_round(state, path_key, kinds_by_count, verdict, now_utc):
    files = state.setdefault("files", {})
    entry = files.setdefault(path_key, {"classes": {}})
    for kind in sorted(kinds_by_count):
        record = entry["classes"].setdefault(
            kind, {"rounds": 0, "applied": 0})
        record["rounds"] += 1
        record["applied"] += int(kinds_by_count[kind])
        record["last_verdict"] = verdict
        record["last_utc"] = now_utc


# ----------------------------------------------------------------- detector

def load_detector():
    """Load the engine E1 detector module: the sibling ai_flavor.py first,
    then an already-imported module, then sys.path (test injection)."""
    here = os.path.dirname(os.path.abspath(__file__))
    sibling = os.path.join(here, "ai_flavor.py")
    if os.path.isfile(sibling):
        try:
            spec = importlib.util.spec_from_file_location("ai_flavor",
                                                          sibling)
            module = importlib.util.module_from_spec(spec)
            sys.modules["ai_flavor"] = module
            spec.loader.exec_module(module)
            return module
        except Exception as exc:
            raise ApplyError("detector module failed to load: %s (%s)"
                             % (sibling, exc), 9)
    module = sys.modules.get("ai_flavor")
    if module is not None:
        return module
    try:
        return importlib.import_module("ai_flavor")
    except ImportError as exc:
        raise ApplyError("detector module ai_flavor.py not found beside %s "
                         "or on sys.path (%s)" % (here, exc), 9)


def _detect(text, word_map, detector=None):
    if detector is None:
        detector = load_detector()
    try:
        return detector.detect_text(text, word_map)
    except ApplyError:
        raise
    except Exception as exc:
        raise ApplyError("detector module unusable: %s" % exc, 2)


# ----------------------------------------------------------- http provider

def net_gate_missing():
    missing = []
    if os.environ.get(ENV_GATE) != "1":
        missing.append(ENV_GATE + " (must be 1)")
    for name in (ENV_ENDPOINT, ENV_MODEL, ENV_KEY):
        if not os.environ.get(name):
            missing.append(name)
    return missing


def _netred(seq, url, model, verdict, detail):
    row = {"seq": seq, "ts_utc": _now_utc(), "url": url, "model": model,
           "verdict": verdict, "detail": detail}
    sys.stderr.write("NETRED " + json.dumps(row, sort_keys=True) + "\n")
    return row


def _loose_json_slice(content):
    text = content.strip()
    a = text.find("{")
    b = text.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("no JSON object in reply")
    return text[a:b + 1]


def _http_prompt(entry, line_text):
    return ("You rewrite one span inside one line of a text file to remove "
            "a banned wording face.\n"
            "face: %s (%s)\n"
            "matched span to replace: %s\n"
            "full line: %s\n"
            "task: %s\n"
            "Reply with STRICT JSON only, no prose around it: "
            "{\"choice\": \"...\", \"after_text\": \"...\"}"
            % (entry["face_id"], entry["kind"], entry["before"],
               line_text, entry["instruction"]))


def http_fill_rows(entries, line_texts, cfg):
    """Direct apply path: one chat/completions call per provider entry.

    Returns (fill rows, NETRED rows); the first failed or unusable call
    aborts with exit 2 after its NETRED row is written.
    """
    rows = []
    netred = []
    url = cfg["endpoint"].rstrip("/") + "/chat/completions"
    provider_entries = [e for e in entries if e["disposition"] == "provider"]
    for seq, entry in enumerate(provider_entries, 1):
        payload = json.dumps({
            "model": cfg["model"],
            "temperature": 0,
            "messages": [{"role": "user",
                          "content": _http_prompt(
                              entry, line_texts[entry["line"] - 1])}],
        }).encode("utf-8")
        request = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + cfg["key"],
        })
        try:
            with urllib.request.urlopen(request,
                                        timeout=HTTP_TIMEOUT_S) as resp:
                body = resp.read().decode("utf-8", "replace")
        except Exception as exc:
            netred.append(_netred(seq, url, cfg["model"], "http_error",
                                  str(exc)[:200]))
            raise ApplyError("http provider call failed for %s (see the "
                             "NETRED row above)" % entry["finding_id"], 2)
        try:
            data = json.loads(body)
            content = data["choices"][0]["message"]["content"]
            fill = json.loads(_loose_json_slice(content))
            row = {
                "finding_id": entry["finding_id"],
                "face_id": entry["face_id"],
                "lang": entry["lang"],
                "before": entry["before"],
                "choice": fill["choice"],
                "after_text": fill["after_text"],
                "model_id": cfg["model"],
            }
        except Exception as exc:
            netred.append(_netred(seq, url, cfg["model"], "invalid_response",
                                  str(exc)[:200]))
            raise ApplyError("http provider returned an unusable reply for "
                             "%s (see the NETRED row above)"
                             % entry["finding_id"], 2)
        netred.append(_netred(seq, url, cfg["model"], "ok", ""))
        rows.append(row)
    return rows, netred


# ----------------------------------------------------------------- CLI face

def build_parser():
    ap = argparse.ArgumentParser(
        prog=TOOL,
        description="advisory rewrite planner and gated applier for the "
                    "ai-flavor wording faces")
    ap.add_argument("--file", metavar="PATH",
                    help="target text file (read-only in plan and emit "
                         "modes)")
    ap.add_argument("--json", metavar="OUT",
                    help="write the run report JSON to OUT")
    ap.add_argument("--emit-handoff", dest="emit_handoff",
                    metavar="OUT.jsonl",
                    help="emit the provider handoff package (zero writes "
                         "to the target)")
    ap.add_argument("--apply-handoff", dest="apply_handoff",
                    metavar="IN.jsonl",
                    help="ingest a filled package and apply it behind the "
                         "structural guard and rescan loop (requires "
                         "--state)")
    ap.add_argument("--state", metavar="PATH",
                    help="budget-cap state file (required for both apply "
                         "forms; one round per target file per class)")
    ap.add_argument("--provider", choices=("handoff", "http"),
                    default="handoff",
                    help="rewrite provider: handoff (default, zero "
                         "network) or http (default-deny direct apply)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the built-in vector suite on temporary "
                         "fixtures")
    return ap


def _read_target(path):
    try:
        with io.open(path, "r", encoding="utf-8", newline="") as fh:
            return fh.read()
    except (OSError, UnicodeError) as exc:
        raise ApplyError("target unreadable: %s (%s)" % (path, exc), 9)


def _write_target(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _write_json(path, payload):
    if not path:
        return
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(payload, sort_keys=True, ensure_ascii=True,
                            indent=2) + "\n")


def _plan_counts(entries, em_dash):
    provider_n = sum(1 for e in entries if e["disposition"] == "provider")
    return len(entries), provider_n, len(entries) - provider_n, em_dash


def _print_plan(target, entries, em_dash):
    total, provider_n, human_n, em_dash = _plan_counts(entries, em_dash)
    print("plan: file=%s findings=%d provider=%d human=%d em_dash=%d"
          % (target, total, provider_n, human_n, em_dash))
    for entry in entries:
        note = ""
        if entry["disposition"] == "human":
            note = " (human rewording only; never machine-rewritten)"
        print("  %s line=%d span=[%d,%d) face=%s kind=%s disposition=%s "
              "before=%s%s"
              % (entry["finding_id"], entry["line"], entry["span_start"],
                 entry["span_end"], entry["face_id"], entry["kind"],
                 entry["disposition"], ascii(entry["before"]), note))
    if em_dash:
        print("  human item: em-dash occurrences=%d (target 0; not "
              "machine-fixable)" % em_dash)


def _print_budget_status(state_path):
    state = load_state(state_path)
    files = state.get("files") or {}
    lines = []
    for path_key in sorted(files):
        classes = files[path_key].get("classes") or {}
        for kind in sorted(classes):
            lines.append("%s class=%s rounds=%s"
                         % (path_key, kind, classes[kind].get("rounds", 0)))
    if lines:
        for line_text in lines:
            print("budget: %s" % line_text)
    else:
        print("budget: %s carries no consumed rounds" % state_path)


def _report_payload(mode, target, entries, em_dash, verdict, **extra):
    total, provider_n, human_n, em_dash = _plan_counts(entries, em_dash)
    payload = {
        "schema": REPORT_SCHEMA,
        "mode": mode,
        "file": target,
        "verdict": verdict,
        "findings_total": total,
        "findings_provider": provider_n,
        "findings_human": human_n,
        "em_dash_count": em_dash,
        "entries": entries,
    }
    payload.update(extra)
    return payload


def _run_plan(target, args, entries, em_dash):
    verdict = "GREEN" if not entries and em_dash == 0 else "RED"
    _print_plan(target, entries, em_dash)
    if args.state:
        _print_budget_status(args.state)
    print("verdict: %s" % verdict)
    _write_json(args.json, _report_payload("plan", target, entries,
                                           em_dash, verdict))
    return 0 if verdict == "GREEN" else 1


def _run_emit(target, args, entries, em_dash):
    verdict = "GREEN" if not entries and em_dash == 0 else "RED"
    package = emit_handoff(entries)
    rows_n = 0 if package == "" else package.count("\n")
    with io.open(args.emit_handoff, "w", encoding="utf-8", newline="") as fh:
        fh.write(package)
    _print_plan(target, entries, em_dash)
    print("package: %s rows=%d" % (args.emit_handoff, rows_n))
    print("verdict: %s" % verdict)
    _write_json(args.json, _report_payload(
        "emit-handoff", target, entries, em_dash, verdict,
        handoff_package=args.emit_handoff, handoff_rows=rows_n))
    return 0 if verdict == "GREEN" else 1


def _run_apply(target, args, text, word_map, detector, entries, em_dash,
               rows, netred, mode):
    new_text, applied, rejected = ingest_handoff(
        text, rows, word_map=word_map, entries=entries)
    if rejected:
        for item in rejected:
            sys.stderr.write("rejected row=%s finding_id=%s reason=%s\n"
                             % (item["row"], item["finding_id"],
                                item["reason"]))
        _write_json(args.json, _report_payload(
            mode, target, entries, em_dash, "REFUSED",
            rejected=rejected, applied=[], netred=netred))
        sys.stderr.write("verdict: REFUSED (rejections above; zero writes)\n")
        return 2
    if not applied:
        # zero would-fix: nothing to write, state untouched; the verdict
        # follows the current scan of the unchanged target
        verdict = "GREEN" if not entries and em_dash == 0 else "RED"
        total, provider_n, human_n, em_dash = _plan_counts(entries, em_dash)
        print("apply: file=%s rows=%d applied=0 rejected=0"
              % (target, len(rows)))
        print("would-fix=0 (nothing to apply; target untouched)")
        print("findings=%d provider=%d human=%d em_dash=%d"
              % (total, provider_n, human_n, em_dash))
        _print_budget_tail(args.state)
        print("verdict: %s" % verdict)
        _write_json(args.json, _report_payload(
            mode, target, entries, em_dash, verdict,
            rejected=[], applied=[], netred=netred))
        return 0 if verdict == "GREEN" else 1
    state = load_state(args.state)
    path_key = _path_key(target)
    kinds_by_count = {}
    for item in applied:
        kinds_by_count[item["kind"]] = kinds_by_count.get(item["kind"], 0) + 1
    refusals = check_budget(state, path_key, sorted(kinds_by_count))
    if refusals:
        for item in refusals:
            sys.stderr.write(
                "budget cap: %s class %s already used its round "
                "(rounds=%s); refusing a further round\n"
                % (item["file"], item["class"], item["rounds"]))
        _write_json(args.json, _report_payload(
            mode, target, entries, em_dash, "REFUSED",
            rejected=[], applied=[], netred=netred,
            budget_refusals=refusals))
        return 2
    _write_target(target, new_text)
    report2 = _detect(new_text, word_map, detector)
    entries2 = plan_suggestions(new_text, report2, word_map)
    em2 = report2.get("em_dash_count", 0)
    verdict = "GREEN" if not entries2 and em2 == 0 else "RED"
    record_round(state, path_key, kinds_by_count, verdict, _now_utc())
    save_state(args.state, state)
    print("apply: file=%s rows=%d applied=%d rejected=0"
          % (target, len(rows), len(applied)))
    for item in applied:
        print("  applied %s line=%d choice=%s before=%s after=%s"
              % (item["finding_id"], item["line"], item["choice"],
                 ascii(item["before"]), ascii(item["after"])))
    residue_total, residue_provider, residue_human, em2 = \
        _plan_counts(entries2, em2)
    print("rescan: findings=%d provider=%d human=%d em_dash=%d"
          % (residue_total, residue_provider, residue_human, em2))
    if residue_total or em2:
        for entry in entries2:
            note = " (human item)" if entry["disposition"] == "human" else ""
            print("  residue %s line=%d face=%s%s"
                  % (entry["finding_id"], entry["line"], entry["face_id"],
                     note))
        if em2:
            print("  residue em-dash occurrences=%d (human item)" % em2)
    _print_budget_tail(args.state)
    print("verdict: %s" % verdict)
    _write_json(args.json, _report_payload(
        mode, target, entries2, em2, verdict,
        rejected=[], applied=applied, netred=netred))
    return 0 if verdict == "GREEN" else 1


def _print_budget_tail(state_path):
    state = load_state(state_path)
    files = state.get("files") or {}
    for path_key in sorted(files):
        for kind in sorted(files[path_key].get("classes") or {}):
            print("budget: %s class=%s rounds=%s"
                  % (path_key, kind,
                     files[path_key]["classes"][kind].get("rounds", 0)))


def run(args):
    if args.selftest:
        if args.file or args.json or args.emit_handoff \
                or args.apply_handoff or args.state:
            raise ApplyError("--selftest takes no other flags", 2)
        return _selftest()
    if args.emit_handoff and args.apply_handoff:
        raise ApplyError("--emit-handoff and --apply-handoff are mutually "
                         "exclusive", 2)
    http_mode = args.provider == "http"
    if http_mode and (args.emit_handoff or args.apply_handoff):
        raise ApplyError("provider http is the direct apply path; drop "
                         "--emit-handoff/--apply-handoff", 2)
    apply_mode = http_mode or bool(args.apply_handoff)
    if apply_mode and not args.state:
        # budget-cap default: a deterministic state file beside the target,
        # so the handoff loop works on the bare contract face while the
        # one-round-per-class cap stays enforced (never bypassed by
        # omitting --state)
        if not args.file:
            raise ApplyError("%s requires --file PATH (and its budget-cap "
                             "state)" % ("--provider http" if http_mode
                                         else "--apply-handoff"), 2)
        args.state = args.file + ".aiflavor-state.json"
    if http_mode:
        missing = net_gate_missing()
        if missing:
            raise ApplyError("http provider is default-deny; missing "
                             "environment: " + ", ".join(missing), 2)
    if not args.file:
        raise ApplyError("give --file PATH (or --selftest)", 2)
    text = _read_target(args.file)
    word_map, _faces = load_seed_map()
    detector = load_detector() if apply_mode else None
    report = _detect(text, word_map, detector)
    entries = plan_suggestions(text, report, word_map)
    em_dash = report.get("em_dash_count", 0)
    if http_mode:
        cfg = {"endpoint": os.environ.get(ENV_ENDPOINT, ""),
               "model": os.environ.get(ENV_MODEL, ""),
               "key": os.environ.get(ENV_KEY, "")}
        line_texts = text.split("\n")
        rows, netred = http_fill_rows(entries, line_texts, cfg)
        return _run_apply(args.file, args, text, word_map, detector,
                          entries, em_dash, rows, netred, "apply-http")
    if args.apply_handoff:
        rows = _read_handoff_rows(args.apply_handoff)
        return _run_apply(args.file, args, text, word_map, detector,
                          entries, em_dash, rows, [], "apply-handoff")
    if args.emit_handoff:
        return _run_emit(args.file, args, entries, em_dash)
    return _run_plan(args.file, args, entries, em_dash)


def _read_handoff_rows(path):
    try:
        with io.open(path, "r", encoding="utf-8", newline="") as fh:
            content = fh.read()
    except (OSError, UnicodeError) as exc:
        raise ApplyError("handoff package unreadable: %s (%s)"
                         % (path, exc), 9)
    rows = []
    for n, line_text in enumerate(content.split("\n"), 1):
        if not line_text.strip():
            continue
        try:
            rows.append(json.loads(line_text))
        except ValueError as exc:
            raise ApplyError("handoff package malformed at %s line %d (%s)"
                             % (path, n, exc), 2)
    return rows


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ApplyError as exc:
        return fail(exc.msg, exc.code)


# ----------------------------------------------------------------- selftest

def _selftest():
    word_map, _faces = load_seed_map()
    by_id = dict((f["id"], f) for f in word_map["faces"])
    stem_text = by_id["en-word-01"]["face"]
    other_stem_text = by_id["en-word-04"]["face"]
    zh_text = by_id["zh-01"]["face"]
    sent_text = by_id["en-sent-01"]["face"]
    pivot_text = by_id["en-word-12"]["face"]
    sent04_text = by_id["en-sent-04"]["face"].replace("crucial", pivot_text)
    para_text = by_id["en-para-01"]["face"]

    def synthetic_report(hits):
        return {"schema": DETECT_SCHEMA, "file": "fixture", "batteries": {},
                "em_dash_count": 0, "hits": hits}

    failures = []
    count = [0]

    def vector(name, fn):
        count[0] += 1
        try:
            fn()
        except Exception as exc:
            failures.append(name)
            print("FAIL %s (%s)" % (name, exc))
        else:
            print("PASS %s" % name)

    line1 = "We %s the corpus and %s the result holds." % (stem_text,
                                                           sent_text)
    line2 = "%s drives the plan." % zh_text
    fixture_text = line1 + "\n" + line2 + "\n"
    fixture_hits = [
        {"line": 1, "battery": by_id["en-word-01"]["battery"],
         "face_id": "en-word-01", "before": line1[:8], "after":
         line1[-8:]},
        {"line": 1, "battery": by_id["en-sent-01"]["battery"],
         "face_id": "en-sent-01", "before": line1[:8], "after":
         line1[-8:]},
        {"line": 2, "battery": by_id["zh-01"]["battery"],
         "face_id": "zh-01", "before": line2[:4], "after": line2[-4:]},
    ]

    def v_seed_shape():
        faces = word_map["faces"]
        assert len(faces) == 36
        kinds = {}
        for face in faces:
            kind = _face_kind(face)
            kinds[kind] = kinds.get(kind, 0) + 1
        assert kinds == {KIND_BAN: 10, KIND_NEUTRAL: 15, KIND_DELETE: 11}

    def v_plan_dispositions():
        entries = plan_suggestions(fixture_text,
                                   synthetic_report(fixture_hits), word_map)
        assert [(e["face_id"], e["disposition"]) for e in entries] == [
            ("en-word-01", "provider"), ("en-sent-01", "provider"),
            ("zh-01", "human")]
        assert [e["finding_id"] for e in entries] == \
            ["af-0001", "af-0002", "af-0003"]
        stem_entry = entries[0]
        assert stem_entry["before"] == stem_text
        assert stem_entry["span_start"] == 3

    def v_subsumption():
        text = "This %s the whole review." % sent04_text
        hits = [
            {"line": 1, "battery": by_id["en-sent-04"]["battery"],
             "face_id": "en-sent-04", "before": "x", "after": "y"},
            {"line": 1, "battery": by_id["en-word-12"]["battery"],
             "face_id": "en-word-12", "before": "x", "after": "y"},
        ]
        entries = plan_suggestions(text, synthetic_report(hits), word_map)
        assert len(entries) == 1
        assert entries[0]["face_id"] == "en-sent-04"
        assert entries[0]["subsumed_face_ids"] == ["en-word-12"]
        assert entries[0]["kind"] == KIND_DELETE

    def v_emit_rows():
        entries = plan_suggestions(fixture_text,
                                   synthetic_report(fixture_hits), word_map)
        package = emit_handoff(entries)
        rows = [json.loads(line_text) for line_text in
                package.splitlines()]
        assert len(rows) == 2
        for row in rows:
            assert set(row.keys()) == set(EMIT_ROW_KEYS)
        assert all(row["face_id"] != "zh-01" for row in rows)
        assert emit_handoff(entries) == package

    def v_ingest_accept():
        entries = plan_suggestions(fixture_text,
                                   synthetic_report(fixture_hits), word_map)
        stem_entry = entries[0]
        value = stem_entry["candidates"][0]["value"]
        rows = [{"finding_id": stem_entry["finding_id"], "choice": value,
                 "after_text": value, "model_id": "tester"}]
        new_text, applied, rejected = ingest_handoff(
            fixture_text, rows, word_map=word_map, entries=entries)
        assert rejected == []
        assert len(applied) == 1
        assert applied[0]["finding_id"] == stem_entry["finding_id"]
        assert value in new_text
        assert stem_text not in new_text

    def v_ingest_delete():
        text = para_text + ", the plan holds.\n"
        hits = [{"line": 1, "battery": by_id["en-para-01"]["battery"],
                 "face_id": "en-para-01", "before": "x", "after": "y"}]
        entries = plan_suggestions(text, synthetic_report(hits), word_map)
        entry = entries[0]
        assert entry["kind"] == KIND_DELETE
        assert entry["delete_span"] == [0, len(para_text) + 2]
        rows = [{"finding_id": entry["finding_id"], "choice": "delete",
                 "after_text": "", "model_id": "tester"}]
        new_text, applied, rejected = ingest_handoff(
            text, rows, word_map=word_map, entries=entries)
        assert rejected == [] and len(applied) == 1
        assert new_text == "the plan holds.\n"

    def v_reject_matrix():
        entries = plan_suggestions(fixture_text,
                                   synthetic_report(fixture_hits), word_map)
        stem_entry = entries[0]
        sent_entry = entries[1]
        zh_entry = entries[2]
        value = stem_entry["candidates"][0]["value"]

        def ingest_one(row):
            return ingest_handoff(fixture_text, [row], word_map=word_map,
                                  entries=entries)

        def reason_of(row):
            new_text, applied, rejected = ingest_one(row)
            assert applied == [] and new_text == fixture_text
            assert len(rejected) == 1
            return rejected[0]["reason"]

        base = {"finding_id": stem_entry["finding_id"], "choice": value,
                "after_text": value, "model_id": "tester"}
        bad = dict(base, finding_id="af-9999")
        assert reason_of(bad) == "unknown_finding_id"
        bad = dict(base, model_id="")
        assert reason_of(bad) == "empty_model_id"
        bad = dict(base, choice="delete")
        assert reason_of(bad) == "illegal_choice"
        bad = dict(base, finding_id=zh_entry["finding_id"])
        assert reason_of(bad) == "ban_remediation_is_human_only"
        bad = dict(base, after_text=other_stem_text)
        assert reason_of(bad) == \
            "after_text_fires_face:" + by_id["en-word-04"]["id"]
        bad = dict(base, after_text="a" + chr(0x2014) + "b")
        assert reason_of(bad) == "after_text_em_dash"
        bad = dict(base, after_text="a\nb")
        assert reason_of(bad) == "after_text_multiline"
        bad = {k: v for k, v in base.items() if k != "model_id"}
        assert reason_of(bad) == "missing_key:model_id"
        bad = dict(base, zzz=1)
        assert reason_of(bad) == "unknown_key:zzz"
        bad = dict(base, after_text=stem_entry["before"])
        assert reason_of(bad) == "no_op_replacement"
        bad = dict(base, before="stale")
        assert reason_of(bad) == "mismatch:before"
        bad = dict(base, after_text="`" + value)
        assert reason_of(bad) == "structural_guard_failed"
        bad = {"finding_id": sent_entry["finding_id"], "choice": "delete",
               "after_text": "x", "model_id": "tester"}
        assert reason_of(bad) == "delete_requires_empty_after_text"

    def v_atomic_multi():
        entries = plan_suggestions(fixture_text,
                                   synthetic_report(fixture_hits), word_map)
        stem_entry = entries[0]
        value = stem_entry["candidates"][0]["value"]
        good = {"finding_id": stem_entry["finding_id"], "choice": value,
                "after_text": value, "model_id": "tester"}
        bad = {"finding_id": "af-9999", "choice": value,
               "after_text": value, "model_id": "tester"}
        new_text, applied, rejected = ingest_handoff(
            fixture_text, [good, bad], word_map=word_map, entries=entries)
        assert new_text == fixture_text and applied == []
        assert [r["reason"] for r in rejected] == ["unknown_finding_id"]

    def v_duplicate_and_echo():
        entries = plan_suggestions(fixture_text,
                                   synthetic_report(fixture_hits), word_map)
        stem_entry = entries[0]
        value = stem_entry["candidates"][0]["value"]
        row = {"finding_id": stem_entry["finding_id"],
               "face_id": stem_entry["face_id"],
               "lang": stem_entry["lang"],
               "before": stem_entry["before"],
               "candidates": stem_entry["candidates"],
               "instruction": stem_entry["instruction"],
               "choice": value, "after_text": value, "model_id": "tester"}
        _new_text, applied, rejected = ingest_handoff(
            fixture_text, [row, row], word_map=word_map, entries=entries)
        assert applied == []
        assert [r["reason"] for r in rejected] == ["duplicate_finding_id"]

    def v_budget():
        state = {"schema": STATE_SCHEMA, "files": {}}
        key = "D:/x/f.md"
        assert check_budget(state, key, [KIND_NEUTRAL]) == []
        record_round(state, key, {KIND_NEUTRAL: 2}, "GREEN", "T")
        refusals = check_budget(state, key, [KIND_NEUTRAL, KIND_DELETE])
        assert len(refusals) == 1
        assert refusals[0]["class"] == KIND_NEUTRAL
        assert state["files"][key]["classes"][KIND_NEUTRAL]["applied"] == 2
        tmp = tempfile.mkdtemp(prefix="ai_flavor_apply_selftest_")
        state_path = os.path.join(tmp, "state.json")
        fresh = load_state(state_path)
        assert fresh["schema"] == STATE_SCHEMA
        save_state(state_path, fresh)
        again = load_state(state_path)
        assert again["schema"] == STATE_SCHEMA

    def v_legal_choices():
        entries = plan_suggestions(fixture_text,
                                   synthetic_report(fixture_hits), word_map)
        values = tuple(c["value"] for c in entries[0]["candidates"])
        assert legal_choices(entries[0]) == values
        assert legal_choices(entries[1]) == DELETE_CHOICES
        assert legal_choices(entries[2]) == ()

    def v_bogus_detector():
        class Bogus(object):
            pass

        try:
            ingest_handoff(fixture_text, [], word_map=word_map,
                           entries=None, detector=Bogus())
        except ApplyError as exc:
            assert exc.code == 2
        else:
            raise AssertionError("bogus detector did not fail loudly")

    def v_determinism_and_clean():
        entries_a = plan_suggestions(fixture_text,
                                     synthetic_report(fixture_hits),
                                     word_map)
        entries_b = plan_suggestions(fixture_text,
                                     synthetic_report(fixture_hits),
                                     word_map)
        assert entries_a == entries_b
        empty = plan_suggestions("plain clean text\n",
                                 synthetic_report([]), word_map)
        assert empty == []
        assert _line_struct_ok("a (b) c", "a (b) d")
        assert not _line_struct_ok("a `b` c", "a b c")

    for name, fn in [
        ("seed-shape", v_seed_shape),
        ("plan-dispositions", v_plan_dispositions),
        ("subsumption", v_subsumption),
        ("emit-rows", v_emit_rows),
        ("ingest-accept", v_ingest_accept),
        ("ingest-delete", v_ingest_delete),
        ("reject-matrix", v_reject_matrix),
        ("atomic-multi", v_atomic_multi),
        ("duplicate-and-echo", v_duplicate_and_echo),
        ("budget", v_budget),
        ("legal-choices", v_legal_choices),
        ("bogus-detector", v_bogus_detector),
        ("determinism-and-clean", v_determinism_and_clean),
    ]:
        vector(name, fn)
    if failures:
        return fail("selftest failed %d of %d vector(s)"
                    % (len(failures), count[0]), 1)
    print("SELFTEST PASS (%d vectors)" % count[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
