#!/usr/bin/env python3
"""lean_sweep.py - Lean vacuity probe batch sweep orchestrator (seed completion).
Purpose.  Bins vacuity probe files (witness, boundary, the canonical five
  refutation forms) into per-lane compile shots, dedups every probe against
  the union of all prior lane ledgers (skip-existing), casts merged shots
  with a row-offset map plus a zero-compile syntax precheck, and fires only
  when --fire is given and the toolchain probe passes; the compile leg is a
  designed SKIP in the default face (loud declaration, no spawn).
Interface.  python -I tools/lean_sweep.py --batches B.json --out DIR
  [--json F] [--fire] [--worktree WT] [--lake PATH] [--guard PATH]
  [--core N] [--lanes N] [--skip-ledgers F ...] [--taxonomy FILE]
  [--max-shot-items N] [--big-item-bytes N] [--liveness-interval S]
  [--bisect-max N] [--timeout-s S] | --selftest.  Status JSON schema
  rocqwash-lean-sweep.status/1; lane ledgers carry the canonical
  batchId|idx|probe|status|rc five-column rows; --taxonomy pins the
  consumer contract for row_render candidate rows (the C3.4 row contract
  mirrored from vacgen.py validate_row plus the canonical five-form
  caliber on refutationForms).
Dependencies.  Python 3 standard library only; zero network; no compiler
  spawn in the default face; the fire leg shells out to lake (optionally
  wrapped in the thermal guard) and only when the toolchain probe passes.
Evidence.  The eight compile-orchestration discipline rules of the OAI v3
  lessons are coded here (per-lane ledgers; syntax precheck with single
  refire fallback; canonical caliber; skip-existing; ALERT freeze lane
  side; two-sample liveness with a declared no-CPU boundary; big-item slow
  lane plus bisect fallback; stop-race terminal recheck); seed divergences
  sit in the extended contract below; suite pin tests/refinery_segments/sweep.py.
Exit-codes.  0 ok (designed skips declared loud); 1 failing sweep data; 2
  ALERT freeze (stop-work) or usage or malformed form (the banner names
  which); 3 syntax precheck refusal, nothing fires; 9 missing input path.
"""
# Extended contract (moved out of the docstring to respect the 30-line
# header budget).  Registered divergences from the packaged seed
# (lean_sweep_seed.py, OAI v3 lessons):
# 1. Key caliber: the seed keyed ledger dedup by "idx|probe" pairs and
#    compared them against "batchId|idx|probe" triples, so skip-existing
#    never matched across batches.  The canonical key everywhere here is the
#    triple batchId|idx|probe, carried in five-column ledger rows
#    "batchId|idx|probe|status|rc" (the seed read three columns).
# 2. GREEN batches merge only witness/boundary probes (all expected rc=0);
#    falsify probes fire one per shot, because the first expected-fail in a
#    merged file would stop compilation and leave the rest unjudged.  The
#    seed merged green[:30] and left the red leg implicit.
# 3. On a merged-shot failure the offset map resolves the failing probe by
#    its error line first; bisect (rule 7) is the fallback when the output
#    carries no parseable "file:line: error" face.
# 4. The precheck runs before any file is written (the seed wrote the
#    merged file first, then prechecked); import lifting is line-based
#    (the seed split the source at the first "import" substring anywhere).
# 5. A lane that trips the ALERT gate writes ALERT.marker.lane<k> and stops
#    before its next shot (rule 5 lane side; the seed had no marker face).

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

TOOL = "lean_sweep"
STATUS_SCHEMA = "rocqwash-lean-sweep.status/1"
BATCHES_SCHEMA = "rocqwash-lean-sweep.batches/1"
TAXONOMY_SCHEMA = "rocqwash.taxonomy-candidates/1"
CANONICAL_FORMS = ("full", "point", "tactics", "noclassic", "band")
POSITIVE_PROBES = ("witness", "boundary")
# canonical probe order: determinism of bins, lanes and merged files
PROBE_ORDER = POSITIVE_PROBES + tuple("falsify_" + f for f in CANONICAL_FORMS)
TIER_STATUS = "SKIP-TIERT"
OK_STATUS = "OK"
TIER_MAX_BYTES = 1024
TIER_MAX_SORRY = 2
DEFAULT_LANES = 12
MAX_LANES = 16
MAX_SHOT_ITEMS_DEFAULT = 30
BIG_ITEM_BYTES_DEFAULT = 51200
LIVENESS_INTERVAL_DEFAULT = 70.0
BISECT_MAX_DEFAULT = 8
TIMEOUT_DEFAULT_S = 600
DEFAULT_CORE = 4
# taxonomy row contract mirrored from vacgen.py (C3.4 row admission plus the
# consumer-side canonical-forms pin; see validate_taxonomy_row below)
REQUIRED_ROW_FIELDS = ("schemaVersion", "familyId", "cluster", "match",
                       "priority", "confidence", "witnessStrategy",
                       "mathlibAnchors", "refutationForms",
                       "boundaryApplicability", "gapKeywords")
MATCH_TARGETS = ("assumption.type", "assumption.name", "instance.type",
                 "conclusion", "file.text")
ROW_FLAG_MAP = {"": 0, "I": re.IGNORECASE, "IGNORECASE": re.IGNORECASE,
                "M": re.MULTILINE, "MULTILINE": re.MULTILINE,
                "S": re.DOTALL, "DOTALL": re.DOTALL}


class FormError(Exception):
    """Malformed input form (rc=2; fail-loud, nothing fired or written)."""


class MissingPath(Exception):
    """Missing input path (rc=9; fail-loud, no simulation)."""


# ---- inputs: batches plan, skip ledgers, taxonomy candidate rows ------------

def load_batches(path, taxonomy_mode):
    """Load and validate the batches plan (rc=2 malformed, rc=9 missing).

    Accepted containers: {"schema": ..., "batches": [...]} or a bare list of
    batches.  Each batch carries batchId and files; each file carries idx,
    bytes, sorryCount and (required in taxonomy mode) familyId.  Duplicate
    (batchId, idx) items are a form error: they would double-count bins and
    collide in the ledger key space."""
    if not os.path.isfile(path):
        raise MissingPath("batches file missing: %s" % path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (ValueError, UnicodeDecodeError) as exc:
        raise FormError("batches JSON parse failure: %s (%s)" % (path, exc))
    batches = doc.get("batches") if isinstance(doc, dict) else doc
    if isinstance(doc, dict):
        schema = doc.get("schema")
        if schema is not None and schema != BATCHES_SCHEMA:
            raise FormError("batches schema %r is not %s" % (schema, BATCHES_SCHEMA))
    if not isinstance(batches, list):
        raise FormError("batches malformed: expected a list of batches")
    records, seen = [], set()
    for b_pos, batch in enumerate(batches):
        if not isinstance(batch, dict):
            raise FormError("batch %d is not an object" % b_pos)
        bid = batch.get("batchId")
        if not isinstance(bid, str) or not bid.strip():
            raise FormError("batch %d: batchId missing or empty" % b_pos)
        files = batch.get("files")
        if not isinstance(files, list):
            raise FormError("batch %r: files missing or not a list" % bid)
        for f_pos, item in enumerate(files):
            if not isinstance(item, dict):
                raise FormError("batch %r file %d is not an object" % (bid, f_pos))
            idx, nbytes, sorry = item.get("idx"), item.get("bytes"), item.get("sorryCount")
            for name, val in (("idx", idx), ("bytes", nbytes), ("sorryCount", sorry)):
                if not isinstance(val, int) or isinstance(val, bool):
                    raise FormError("batch %r file %r: %s must be an integer"
                                    % (bid, idx, name))
            if nbytes < 0 or sorry < 0:
                raise FormError("batch %r file %r: bytes/sorryCount must be >= 0"
                                % (bid, idx))
            family = item.get("familyId")
            if taxonomy_mode and (not isinstance(family, str) or not family.strip()):
                raise FormError("batch %r file %r: familyId is required in"
                                " taxonomy mode (--taxonomy)" % (bid, idx))
            key = (bid, idx)
            if key in seen:
                raise FormError("duplicate item batchId=%r idx=%r (keys must be"
                                " unique)" % (bid, idx))
            seen.add(key)
            records.append({"batchId": bid, "idx": idx, "bytes": nbytes,
                            "sorryCount": sorry, "familyId": family})
    return records


def load_skip_ledgers(paths):
    """Union the skip key set across ALL given ledgers (rule 4: one ledger
    per lane, dedup across every ledger, so a re-slice never re-fires a
    done probe).  Row form: batchId|idx|probe|status|rc (>= 4 columns read).
    Malformed rows are counted and declared, never silently dropped."""
    skip, malformed = set(), 0
    for path in paths:
        if not os.path.isfile(path):
            raise MissingPath("skip ledger missing: %s" % path)
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                parts = line.strip().split("|")
                if len(parts) < 4:
                    if line.strip():
                        malformed += 1
                    continue
                skip.add((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return skip, malformed


def validate_taxonomy_row(row):
    """Row admission contract, mirrored from vacgen.py validate_row (C3.4):
    required fields, match.target enum, regex compiles with a supported
    flag, priority integer, confidence enum, non-empty mathlibAnchors.
    Consumer-side pin on top (canonical caliber, rule 3): refutationForms
    must be a non-empty list drawn only from the canonical five forms."""
    errs = []
    if not isinstance(row, dict):
        return ["row is not an object"]
    for field in REQUIRED_ROW_FIELDS:
        if field not in row:
            errs.append("missing required field %s" % field)
    if errs:
        return errs
    match = row["match"]
    if not isinstance(match, dict) or match.get("target") not in MATCH_TARGETS:
        errs.append("match.target must be one of %s" % ", ".join(MATCH_TARGETS))
    regex = match.get("regex") if isinstance(match, dict) else None
    if not isinstance(regex, str) or not regex.strip():
        errs.append("match.regex missing")
    else:
        flags = match.get("flags", "")
        if not isinstance(flags, str) or flags.strip() not in ROW_FLAG_MAP:
            errs.append("match.flags unsupported (use '', I/M/S or long names)")
        else:
            try:
                re.compile(regex, ROW_FLAG_MAP[flags.strip()])
            except re.error as exc:
                errs.append("match.regex compile failed: %s" % exc)
    if not isinstance(row["priority"], int) or isinstance(row["priority"], bool):
        errs.append("priority must be an integer")
    if row["confidence"] not in ("HIGH", "MID"):
        errs.append("confidence must be HIGH or MID")
    anchors = row["mathlibAnchors"]
    if not isinstance(anchors, list) or len(anchors) < 1:
        errs.append("mathlibAnchors must be a non-empty list (C3.2)")
    forms = row["refutationForms"]
    if not isinstance(forms, list) or not forms:
        errs.append("refutationForms must be a non-empty list")
    elif not all(f in CANONICAL_FORMS for f in forms):
        errs.append("refutationForms must stay inside the canonical five-form"
                    " caliber %s (rule 3: no legacy face mixes into the plan)"
                    % ", ".join(CANONICAL_FORMS))
    return errs


def load_taxonomy(path):
    """Load row_render candidate rows for the --taxonomy consumer pin.

    Accepted containers: a bare list of rows, or {"schema":
    "rocqwash-taxonomy-candidates/1", "rows": [...]}.  Any invalid row is a
    form error naming the row position and familyId (fail-loud; nothing
    sweeps on a refused plan).  Returns (rows, summary)."""
    if not os.path.isfile(path):
        raise MissingPath("taxonomy candidates file missing: %s" % path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (ValueError, UnicodeDecodeError) as exc:
        raise FormError("taxonomy JSON parse failure: %s (%s)" % (path, exc))
    if isinstance(doc, list):
        rows = doc
        schema = None
    elif isinstance(doc, dict) and isinstance(doc.get("rows"), list):
        rows = doc["rows"]
        schema = doc.get("schema")
    else:
        raise FormError("taxonomy malformed: expected a list of rows or an"
                        " object with a rows list")
    if schema is not None and schema != TAXONOMY_SCHEMA:
        raise FormError("taxonomy schema %r is not %s" % (schema, TAXONOMY_SCHEMA))
    for pos, row in enumerate(rows):
        errs = validate_taxonomy_row(row)
        if errs:
            family = row.get("familyId") if isinstance(row, dict) else None
            raise FormError("taxonomy row %d (familyId=%r) refused: %s"
                            % (pos, family, "; ".join(errs)))
    families = {}
    for row in rows:
        # canonical order win: a family seen across rows plans the union of
        # its forms in canonical form order (rule 3)
        slot = families.setdefault(row["familyId"], set())
        slot.update(row["refutationForms"])
    forms_by_family = {
        family: [f for f in CANONICAL_FORMS if f in slot]
        for family, slot in families.items()}
    summary = {"rows": len(rows), "families": len(forms_by_family),
               "forms_union": sorted({f for forms in forms_by_family.values()
                                      for f in forms})}
    return rows, forms_by_family, summary


# ---- binning and lane assignment --------------------------------------------

def bin_items(records, out_root, skip_keys, forms_by_family):
    """Bin fresh probe faces into GREEN (witness/boundary), RED (falsify,
    one canonical form per entry) and SKIP-TIERT (tiny boundary faces,
    seed caliber: bytes <= 1024 and sorryCount <= 2).  Keys present in any
    prior ledger (skip_keys) are never re-binned (rule 4).  Items with no
    probe file on disk land in the loud zero_probe list, never in a silent
    void."""
    green, red, tier, zero_probe = [], [], [], []
    for rec in records:
        bid, idx = rec["batchId"], rec["idx"]
        item_dir = os.path.join(out_root, "items", bid, str(idx))
        forms = (forms_by_family or {}).get(rec["familyId"], list(CANONICAL_FORMS))
        found = False
        for probe in POSITIVE_PROBES:
            path = os.path.join(item_dir, probe + ".lean")
            key = (bid, str(idx), probe)
            if (probe == "boundary" and rec["bytes"] <= TIER_MAX_BYTES
                    and rec["sorryCount"] <= TIER_MAX_SORRY):
                if key not in skip_keys:
                    tier.append(dict(rec, probe=probe, path=path))
                found = found or os.path.exists(path)
            elif os.path.exists(path) and key not in skip_keys:
                green.append(dict(rec, probe=probe, path=path))
                found = True
        for form in forms:
            probe = "falsify_" + form
            path = os.path.join(item_dir, probe + ".lean")
            if os.path.exists(path) and (bid, str(idx), probe) not in skip_keys:
                red.append(dict(rec, probe=probe, path=path))
                found = True
        if not found:
            zero_probe.append("%s|%s" % (bid, idx))
    return green, red, tier, zero_probe


def assign_lanes(green, red, tier, lanes, big_item_bytes, max_shot_items):
    """Round-robin lane assignment with a dedicated slow lane (rule 7):
    entries whose item bytes exceed big_item_bytes go to lane 0 as
    single-entry shots; merged GREEN shots (witness/boundary only) and
    single RED shots share lanes 1..N-1.  Returns per-lane shot plans plus
    the tier rows written to each lane ledger up front."""
    plans = [{"lane": k, "shots": [], "tier_rows": []} for k in range(lanes)]
    def probe_rank(entry):
        return (entry["batchId"], entry["idx"], PROBE_ORDER.index(entry["probe"]))
    big, rest = [], []
    for entry in sorted(green, key=probe_rank) + sorted(red, key=probe_rank):
        (big if entry["bytes"] > big_item_bytes else rest).append(entry)
    # tier rows spread evenly; they are ledger bookkeeping, not shots
    for pos, entry in enumerate(sorted(tier, key=probe_rank)):
        plans[pos % lanes]["tier_rows"].append(entry)
    reds = [e for e in rest if e["probe"].startswith("falsify_")]
    greens = [e for e in rest if not e["probe"].startswith("falsify_")]
    # big items: one single-entry shot each on lane 0 (slow lane)
    for entry in big:
        plans[0]["shots"].append([entry])
    # remaining green entries: merged shots of at most max_shot_items,
    # round-robin over lanes 1..N-1 (lane 0 stays the slow lane)
    pool = lanes - 1 if lanes > 1 else 1
    for pos in range(0, len(greens), max_shot_items):
        target = plans[1 + (pos // max_shot_items) % pool] if lanes > 1 else plans[0]
        target["shots"].append(greens[pos:pos + max_shot_items])
    # red entries always fire one per shot (expected-fail faces never merge)
    for pos, entry in enumerate(sorted(reds, key=probe_rank)):
        target = plans[1 + pos % pool] if lanes > 1 else plans[0]
        target["shots"].append([entry])
    return plans


# ---- merged casting with offset map and syntax precheck (rule 2) ------------

def _ns_for(entry):
    """Stable Lean namespace for one probe entry (batchId is hashed: batch
    ids are free-form strings, namespaces must be identifier-safe)."""
    digest = hashlib.md5(entry["batchId"].encode("utf-8")).hexdigest()[:8]
    return "P%s_%s_%s" % (digest, entry["idx"], entry["probe"])


def cast_shot(entries, shot_tag, lane_no, out_root):
    """Cast one merged shot file plus its row-offset map, then run the
    zero-compile syntax precheck (rule 2) BEFORE any file is written.
    Returns (merged_path, map_path, offset_map, None) or (None, None, None,
    error_message).  Import lines are lifted into a shared header (line
    based, so an 'import' substring inside a body never truncates it)."""
    segments, offset_map, imports = [], [], set()
    for entry in sorted(entries, key=lambda e: (e["batchId"], e["idx"],
                                                PROBE_ORDER.index(e["probe"]))):
        try:
            with open(entry["path"], "r", encoding="utf-8", errors="replace") as fh:
                src = fh.read()
        except OSError as exc:
            return None, None, None, "probe read failure: %s (%s)" % (entry["path"], exc)
        body_lines = []
        for line in src.splitlines():
            if line.strip().startswith("import "):
                imports.add(line.strip())
            else:
                body_lines.append(line)
        ns = _ns_for(entry)
        body = "\n".join(body_lines).strip("\n")
        segment = "namespace %s\n%s\nend %s\n" % (ns, body, ns)
        segments.append(segment)
        offset_map.append({"batchId": entry["batchId"], "idx": entry["idx"],
                           "probe": entry["probe"], "namespace": ns,
                           "expected": "GREEN" if entry["probe"] in POSITIVE_PROBES else "RED",
                           "segment": segment})
    # exact line numbering: the import header occupies its own lines plus one
    # blank separator; offset ranges must land on real merged-file lines
    header_lines = (len(imports) + 1) if imports else 0
    line_no = 1 + header_lines
    for item in offset_map:
        segment = item.pop("segment")
        item["startLine"] = line_no
        line_no += segment.count("\n")
        item["endLine"] = line_no - 1
        segments.append(segment)
        line_no += 1  # blank separator line between segments
    # rule 2: word-face precheck on the in-memory segments (namespace/end
    # balance, seed caliber).  This is a word-face gate, not a Lean parser;
    # a body mentioning the faces inside string literals trips it fail-loud,
    # which is the safe direction (refuse, never fire a broken box).
    for pos, segment in enumerate(segments):
        if segment.count("namespace") != segment.count("end "):
            first = offset_map[pos]
            return None, None, None, (
                "SYNTAX-PRECHECK-FAIL shot=%s seg=%d (item %s|%s %s):"
                " namespace=%d vs end=%d word-face mismatch"
                % (shot_tag, pos, first["batchId"], first["idx"], first["probe"],
                   segment.count("namespace"), segment.count("end ")))
    shots_dir = os.path.join(out_root, "shots")
    os.makedirs(shots_dir, exist_ok=True)
    merged_path = os.path.join(shots_dir, "merged_%s_L%d.lean" % (shot_tag, lane_no))
    map_path = os.path.join(shots_dir, "offset_map_%s_L%d.json" % (shot_tag, lane_no))
    header = ("\n".join(sorted(imports)) + "\n\n") if imports else ""
    with open(merged_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(header + "\n".join(segments))
    with open(map_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"shot": shot_tag, "lane": lane_no, "items": offset_map}, fh,
                  ensure_ascii=False, indent=1, sort_keys=True)
    return merged_path, map_path, offset_map, None


# ---- toolchain probe, firing, error-line mapping, bisect (rules 5-7) --------

def resolve_tool(path_or_name):
    """Toolchain probe: an existing file path wins, then PATH lookup via
    shutil.which, then absence (the designed SKIP face, loud)."""
    if os.path.isfile(path_or_name):
        return path_or_name
    return shutil.which(path_or_name)


def fire_shot(merged_path, worktree, lake, guard, core, timeout_s):
    """Fire one cast shot.  guard form (seed shape, thermal wrapper):
    powershell cpu_guard -TempLimit 98 -CoreN N -AllowG3 -GearForce 0.
    Direct form (guard omitted): lake env lean <file> with cwd=worktree.
    Returns (rc, output); output decoded utf-8 with errors=replace."""
    if guard:
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
               "-File", guard, "-TempLimit", "98", "-CoreN", str(core),
               "-AllowG3", "-GearForce", "0", "-Command",
               "cd /d %s && %s env lean %s" % (worktree, lake, merged_path)]
        cwd = None
    else:
        cmd = [lake, "env", "lean", merged_path]
        cwd = worktree
    try:
        proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=timeout_s)
        output = proc.stdout.decode("utf-8", errors="replace") \
            if isinstance(proc.stdout, bytes) else (proc.stdout or "")
        return proc.returncode, output
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or b""
        if isinstance(partial, str):
            partial = partial.encode("utf-8", errors="replace")
        return None, ("TIMEOUT after %ss\n" % timeout_s
                      + partial.decode("utf-8", errors="replace"))


def parse_failing_line(output, merged_path, offset_map):
    """Error-line mapping (rule 7 primary): the first 'merged_<tag>_L<k>
    .lean:<line>:' error face locates the failing probe through the offset
    map.  Returns (failing_entry, passed_entries, unjudged_entries) or None
    when the output carries no parseable error face (caller bisects)."""
    name = os.path.basename(merged_path)
    hit = re.search(r"%s:(\d+):\d+:\s*error" % re.escape(name), output)
    if not hit:
        return None
    line_no = int(hit.group(1))
    for pos, item in enumerate(offset_map):
        if item["startLine"] <= line_no <= item["endLine"]:
            return (item, offset_map[:pos], offset_map[pos + 1:])
    return None


def ledger_row(entry, status, rc):
    """Canonical five-column ledger row (see header, divergence note 1)."""
    return "%s|%s|%s|%s|%s" % (entry["batchId"], entry["idx"], entry["probe"],
                               status, "-" if rc is None else rc)


def append_rows(lane_path, rows):
    """Per-lane ledger append (rule 1: one file per lane, never a shared
    single ledger; rows flushed immediately so a stop race loses at most
    the shot in flight)."""
    with open(lane_path, "a", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(row + "\n")
        fh.flush()


def ledger_line_count(path):
    """Data-row count of a lane ledger (liveness sampling face, rule 6)."""
    if not os.path.isfile(path):
        return 0
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for line in fh if line.strip())


def liveness_two_sample(lane_path, interval_s):
    """Two-sample liveness (rule 6: 70-90s spacing in the field, never a
    single-point verdict).  Declared stdlib boundary: no CPU column, so
    delta=0 cannot separate dead from glacier here; the report says
    'review before acting' and never asserts death."""
    first = ledger_line_count(lane_path)
    time.sleep(interval_s)
    second = ledger_line_count(lane_path)
    return {"first": first, "second": second, "delta": second - first,
            "verdict": "progressing" if second > first
            else "no-progress-in-window (review before acting; two samples,"
                 " no single-point death claim)"}


def bisect_shot(entries, shot_tag, lane_no, out_root, ctx, budget, mark="b"):
    """Bisect fallback (rule 7): a merged shot whose output carries no
    parseable error line splits in halves; a leaf entry fires alone and
    its rc decides.  Rows for clean entries still land rc=0 (taken from the
    offset map, so row keys can never drift from the cast box).  Budget
    caps the extra shots; exhausted residue is reported unjudged, loud."""
    rows, extra, unjudged = [], 0, []
    if not entries:
        return rows, extra, unjudged
    if len(entries) == 1:
        entry = entries[0]
        cast = cast_shot([entry], shot_tag + mark + "L", lane_no, out_root)
        if cast[3]:
            return [], 0, ["%s|%s|%s (precheck: %s)" % (entry["batchId"],
                          entry["idx"], entry["probe"], cast[3])]
        rc, _ = fire_shot(cast[0], ctx["worktree"], ctx["lake_resolved"],
                          ctx["guard_resolved"], ctx["core"], ctx["timeout_s"])
        return [ledger_row(entry, OK_STATUS, rc)], 1, []
    if budget <= 0:
        return [], 0, ["%s|%s (bisect budget exhausted; shot not isolated)"
                       % (e["batchId"], e["idx"]) for e in entries]
    mid = len(entries) // 2
    for side, half in enumerate((entries[:mid], entries[mid:])):
        if budget - extra <= 0:
            unjudged += ["%s|%s (bisect budget exhausted; shot not isolated)"
                         % (e["batchId"], e["idx"]) for e in half]
            continue
        cast = cast_shot(half, shot_tag + mark + str(side), lane_no, out_root)
        if cast[3]:
            sub_rows, sub_extra, sub_unjudged = bisect_shot(
                half, shot_tag, lane_no, out_root, ctx, budget - extra,
                mark + str(side))
        else:
            rc, _ = fire_shot(cast[0], ctx["worktree"], ctx["lake_resolved"],
                              ctx["guard_resolved"], ctx["core"], ctx["timeout_s"])
            extra += 1
            if rc == 0:
                rows += [ledger_row(item, OK_STATUS, 0) for item in cast[2]]
                continue
            sub_rows, sub_extra, sub_unjudged = bisect_shot(
                half, shot_tag, lane_no, out_root, ctx, budget - extra,
                mark + str(side))
        rows += sub_rows
        extra += sub_extra
        unjudged += sub_unjudged
    return rows, extra, unjudged


def run_lane(plan, lane_no, lane_path, out_root, ctx, report):
    """Fire one lane's shots (rule 5 lane side): a falsify probe with rc=0
    writes ALERT.marker.lane<k>, its row lands first, and the lane stops
    before its next shot.  Merged-shot failures resolve by error line
    first, then bisect.  Returns the ALERT key or None."""
    alert_key = None
    tag = time.strftime("%Y%m%dT%H%M%S")
    if plan["tier_rows"]:
        append_rows(lane_path, [ledger_row(e, TIER_STATUS, None)
                                for e in plan["tier_rows"]])
        report["tier_rows_written"] += len(plan["tier_rows"])
    for pos, entries in enumerate(plan["shots"]):
        if alert_key:
            report["shots_skipped_after_alert"] += 1
            continue
        cast = cast_shot(entries, "%s_%d" % (tag, pos), lane_no, out_root)
        if cast[3] and len(entries) > 1:
            # rule 2 prescription: a refused box falls back to single fire
            for entry in entries:
                single = cast_shot([entry], "%s_%d_s" % (tag, pos), lane_no, out_root)
                if single[3]:
                    report["precheck_failures"].append(
                        "%s|%s|%s: %s" % (entry["batchId"], entry["idx"],
                                          entry["probe"], single[3]))
                    continue
                rc, _ = fire_shot(single[0], ctx["worktree"], ctx["lake_resolved"],
                                  ctx["guard_resolved"], ctx["core"], ctx["timeout_s"])
                append_rows(lane_path, [ledger_row(entry, OK_STATUS, rc)])
                report["rows_written"] += 1
            continue
        if cast[3]:
            report["precheck_failures"].append(
                "%s: %s" % (entries[0]["batchId"], cast[3]))
            continue
        rc, output = fire_shot(cast[0], ctx["worktree"], ctx["lake_resolved"],
                               ctx["guard_resolved"], ctx["core"], ctx["timeout_s"])
        report["shots_fired"] += 1
        merged = len(entries) > 1
        if rc == 0:
            # rows come straight from the offset map: box and bookkeeping
            # share one source (no zip alignment to drift)
            append_rows(lane_path, [ledger_row(item, OK_STATUS, 0)
                                    for item in cast[2]])
            report["rows_written"] += len(entries)
            continue
        if rc is None:  # timeout: two-sample liveness, no single-point claim
            sample = liveness_two_sample(lane_path, ctx["liveness_interval"])
            report["liveness_samples"].append({"lane": lane_no, **sample})
            report["unjudged"] += len(entries)
            continue
        if merged:
            located = parse_failing_line(output, cast[0], cast[2])
            if located:
                failing, passed, unjudged = located
                rows = [ledger_row(item, OK_STATUS, 0) for item in passed]
                rows.append(ledger_row(failing, OK_STATUS, rc))
                append_rows(lane_path, rows)
                report["rows_written"] += len(rows)
                report["unjudged"] += len(unjudged)
            else:
                rows, extra, unjudged = bisect_shot(
                    entries, "%s_%d" % (tag, pos), lane_no, out_root, ctx,
                    ctx["bisect_max"])
                append_rows(lane_path, rows)
                report["rows_written"] += len(rows)
                report["bisect_shots"] += extra
                report["unjudged"] += len(unjudged)
                for key in unjudged:
                    report["unjudged_keys"].append(key)
                report["failing_data"] = True
            continue
        # single-entry shot (falsify leg): rc=0 is the ALERT gate (rule 5)
        entry = entries[0]
        append_rows(lane_path, [ledger_row(entry, OK_STATUS, rc)])
        report["rows_written"] += 1
        if rc == 0:
            alert_key = "%s|%s|%s" % (entry["batchId"], entry["idx"], entry["probe"])
            marker = os.path.join(out_root, "ALERT.marker.lane%d" % lane_no)
            with open(marker, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(alert_key + "\n")
            report["alert_keys"].append(alert_key)
        elif rc != 1:
            report["out_of_band_rc"].append(
                "%s|%s|%s rc=%s" % (entry["batchId"], entry["idx"],
                                    entry["probe"], rc))
            report["failing_data"] = True
    return alert_key


def recheck_terminal(lane_paths, expected_rows, out_root, alert_expected):
    """Stop-race recheck (rule 8): a completion claim is only accepted when
    a fresh disk read reproduces it (row counts per lane ledger, ALERT
    markers on disk).  Notification-shaped signals raced the runtime in the
    OAI runs; the disk is the only accepted witness here."""
    mismatches = []
    for path, expected in zip(lane_paths, expected_rows):
        actual = ledger_line_count(path)
        if actual != expected:
            mismatches.append("lane ledger %s: %d rows on disk vs %d written"
                              % (os.path.basename(path), actual, expected))
    markers = sorted(f for f in os.listdir(out_root)
                     if f.startswith("ALERT.marker.lane")) if os.path.isdir(out_root) else []
    if len(markers) != len(alert_expected):
        mismatches.append("ALERT markers on disk %d vs %d tripped in-run"
                          % (len(markers), len(alert_expected)))
    return mismatches


# ---- selftest (embedded vectors; tmp-synthesized fixtures; zero compile,
# ---- zero network, zero real-tree touch) ------------------------------------

def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def selftest():
    """Six vectors on tmp fixtures: binning plus tier plus skip-existing /
    casting plus precheck plus determinism / taxonomy pin acceptance plus
    refusal faces / designed SKIP faces (default and fire-without-toolchain)
    / skip-ledger union / CLI exit codes.  Zero compile, zero network."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_lean_sweep_self_")
    try:
        out = os.path.join(tmp, "out")
        items = os.path.join(out, "items")
        # item 10: witness + boundary, big; item 11: tier-sized boundary; item 12: falsify_full
        _write(os.path.join(items, "bA", "10", "witness.lean"), "theorem w10 : True := trivial\n")
        _write(os.path.join(items, "bA", "10", "boundary.lean"), "theorem b10 : True := trivial\n")
        _write(os.path.join(items, "bA", "11", "witness.lean"), "theorem w11 : True := trivial\n")
        _write(os.path.join(items, "bA", "11", "boundary.lean"), "theorem b11 : True := trivial\n")
        _write(os.path.join(items, "bA", "12", "falsify_full.lean"), "theorem f12 : False := trivial\n")
        batches = os.path.join(tmp, "batches.json")
        _write(batches, json.dumps({
            "schema": BATCHES_SCHEMA,
            "batches": [{"batchId": "bA", "files": [
                {"idx": 10, "bytes": 90000, "sorryCount": 7},
                {"idx": 11, "bytes": 100, "sorryCount": 1},
                {"idx": 12, "bytes": 500, "sorryCount": 1}]}]},
            ensure_ascii=False, indent=1))
        # vector 1: binning, tier caliber, slow-lane assignment
        recs = load_batches(batches, taxonomy_mode=False)
        assert len(recs) == 3, recs
        green, red, tier, zero = bin_items(recs, out, set(), None)
        assert [g["probe"] for g in green].count("witness") == 2, green
        assert any(t["probe"] == "boundary" and t["idx"] == 11 for t in tier), tier
        assert len(red) == 1 and red[0]["probe"] == "falsify_full", red
        plans = assign_lanes(green, red, tier, lanes=3,
                             big_item_bytes=BIG_ITEM_BYTES_DEFAULT,
                             max_shot_items=MAX_SHOT_ITEMS_DEFAULT)
        assert plans[0]["shots"] and len(plans[0]["shots"][0]) == 1, "big item must ride the slow lane"
        assert all(len(s) == 1 for s in plans[0]["shots"]), plans[0]
        # skip-existing: a prior ledger row removes its key from the bins
        ledger = os.path.join(tmp, "results-lane0.tsv")
        _write(ledger, "bA|10|witness|OK|0\n")
        skip, malformed = load_skip_ledgers([ledger])
        assert malformed == 0 and skip == {("bA", "10", "witness")}, skip
        green2, _, tier2, _ = bin_items(recs, out, skip, None)
        assert not any(g["probe"] == "witness" and g["idx"] == 10 for g in green2), green2
        assert any(t["idx"] == 11 for t in tier2), "an unledgered tier row must still list"
        _write(ledger, "bA|10|witness|OK|0\nbA|11|boundary|SKIP-TIERT|-\n")
        skip2, _ = load_skip_ledgers([ledger])
        _, _, tier3, _ = bin_items(recs, out, skip2, None)
        assert not any(t["idx"] == 11 for t in tier3), "a ledgered tier row must not re-list"
        print("vector 1 binning + tier caliber + slow lane + skip-existing union: PASS")

        # vector 2: casting, offset map, precheck, byte determinism
        entries = [dict(r, probe="witness", path=os.path.join(items, "bA", "10", "witness.lean"))
                   for r in recs if r["idx"] == 10]
        entries += [dict(r, probe="falsify_point", path=os.path.join(items, "bA", "12", "falsify_full.lean"))
                    for r in recs if r["idx"] == 12]
        cast1 = cast_shot(entries, "t1", 1, out)
        assert cast1[3] is None, cast1[3]
        merged, map_path, offset = cast1[0], cast1[1], cast1[2]
        with open(merged, "r", encoding="utf-8") as fh:
            text1 = fh.read()
        assert text1.splitlines()[0].startswith("import") or "namespace P" in text1, text1[:80]
        assert offset[0]["expected"] == "GREEN" and offset[1]["expected"] == "RED", offset
        assert offset[1]["startLine"] > offset[0]["endLine"], "offset ranges must be monotonic"
        cast2 = cast_shot(entries, "t1", 1, out)
        with open(cast2[0], "r", encoding="utf-8") as fh:
            assert fh.read() == text1, "casting must be byte-deterministic"
        # precheck refusal: a probe body with an extra 'end ' face trips the gate
        bad = os.path.join(items, "bA", "13", "witness.lean")
        _write(bad, "theorem w13 : True := trivial\nend dangling\n")
        rec13 = dict(recs[0], idx=13)
        cast3 = cast_shot([dict(rec13, probe="witness", path=bad)], "t2", 2, out)
        assert cast3[3] and "SYNTAX-PRECHECK-FAIL" in cast3[3], cast3[3]
        assert not os.path.exists(os.path.join(out, "shots", "merged_t2_L2.lean")), \
            "a refused box must write nothing (precheck before write)"
        print("vector 2 casting + offset map monotonic + precheck refusal writes nothing"
              " + byte determinism: PASS")

        # vector 3: taxonomy consumer pin (accept, refuse faces, join hole)
        rows_path = os.path.join(tmp, "taxonomy-candidates.json")
        row = {"schemaVersion": 2, "familyId": "fam.alpha", "cluster": "c1",
               "match": {"target": "assumption.type", "regex": "Nat", "flags": ""},
               "priority": 50, "confidence": "HIGH",
               "witnessStrategy": "point bite", "witnessTemplate": {},
               "mathlibAnchors": [{"symbol": "s", "relPath": "Mathlib/X.lean", "line": 1}],
               "refutationForms": ["full", "point"], "boundaryApplicability": "numeric-constant",
               "gapKeywords": ["k"], "sourceLane": "row_render", "sourceRowId": "r1"}
        _write(rows_path, json.dumps({"schema": TAXONOMY_SCHEMA, "rows": [row]},
                                     ensure_ascii=False, indent=1))
        _, forms_by_family, summary = load_taxonomy(rows_path)
        assert forms_by_family == {"fam.alpha": ["full", "point"]}, forms_by_family
        assert summary["rows"] == 1 and summary["forms_union"] == ["full", "point"], summary
        # batches without familyId are refused in taxonomy mode
        try:
            load_batches(batches, taxonomy_mode=True)
            raise AssertionError("taxonomy mode must require familyId")
        except FormError as exc:
            assert "familyId is required" in str(exc), exc
        # a non-canonical refutation form is refused (canonical caliber, rule 3)
        bad_row = dict(row, familyId="fam.beta", refutationForms=["full", "legacy_op"])
        bad_rows_path = os.path.join(tmp, "taxonomy-bad.json")
        _write(bad_rows_path, json.dumps({"rows": [bad_row]}, ensure_ascii=False, indent=1))
        try:
            load_taxonomy(bad_rows_path)
            raise AssertionError("non-canonical refutationForms must be refused")
        except FormError as exc:
            assert "canonical five-form" in str(exc), exc
        # a row missing a required field is refused, naming the field
        nofield = {k: v for k, v in row.items() if k != "priority"}
        nofield_path = os.path.join(tmp, "taxonomy-nofield.json")
        _write(nofield_path, json.dumps({"rows": [nofield]}, ensure_ascii=False, indent=1))
        try:
            load_taxonomy(nofield_path)
            raise AssertionError("row missing a required field must be refused")
        except FormError as exc:
            assert "priority" in str(exc), exc
        print("vector 3 taxonomy pin (C3.4 mirror accept; familyId join required;"
              " non-canonical forms refused; missing field refused by name): PASS")

        # vector 4: designed SKIP faces (default face and fire without toolchain)
        def run_cli(argv):
            proc = subprocess.run(
                [sys.executable, "-B", os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), TOOL + ".py")] + argv,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
            proc.stdout = proc.stdout.decode("utf-8", errors="replace") \
                if isinstance(proc.stdout, bytes) else (proc.stdout or "")
            return proc
        out2 = os.path.join(tmp, "out2")
        import shutil as _cp
        _cp.copytree(items, os.path.join(out2, "items"))
        proc = run_cli(["--batches", batches, "--out", out2, "--lanes", "3",
                        "--json", os.path.join(out2, "status.json")])
        assert proc.returncode == 0, (proc.returncode, proc.stdout)
        assert "compile leg: design SKIP" in proc.stdout, proc.stdout
        with open(os.path.join(out2, "status.json"), "r", encoding="utf-8") as fh:
            status = json.load(fh)
        assert status["schema"] == STATUS_SCHEMA and status["compile_leg"] == "design-skip", status
        out3 = os.path.join(tmp, "out3")
        proc = run_cli(["--batches", batches, "--out", out3, "--fire",
                        "--lake", os.path.join(tmp, "no-such-lake.exe"),
                        "--json", os.path.join(out3, "status.json")])
        assert proc.returncode == 0, (proc.returncode, proc.stdout)
        assert "SKIP-TOOLCHAIN-ABSENT" in proc.stdout, proc.stdout
        with open(os.path.join(out3, "status.json"), "r", encoding="utf-8") as fh:
            assert json.load(fh)["compile_leg"] == "skip-toolchain-absent"
        print("vector 4 designed SKIP faces (default face declares design-skip;"
              " fire without toolchain declares skip-toolchain-absent, rc0): PASS")

        # vector 5: liveness two-sample (rule 6 face; tiny interval in test)
        sample_path = os.path.join(tmp, "results-lane1.tsv")
        _write(sample_path, "bA|10|witness|OK|0\n")
        sample = liveness_two_sample(sample_path, 0.05)
        assert sample["delta"] == 0 and "review before acting" in sample["verdict"], sample
        print("vector 5 two-sample liveness (delta face, no single-point death"
              " claim): PASS")

        # vector 6: CLI refusals (missing path 9, malformed form 2, lanes bound 2)
        proc = run_cli(["--batches", os.path.join(tmp, "nope.json"), "--out", out2])
        assert proc.returncode == 9, proc.returncode
        bad_batches = os.path.join(tmp, "batches-bad.json")
        _write(bad_batches, "{not json")
        proc = run_cli(["--batches", bad_batches, "--out", out2])
        assert proc.returncode == 2, proc.returncode
        proc = run_cli(["--batches", batches, "--out", out2, "--lanes", "0"])
        assert proc.returncode == 2, proc.returncode
        proc = run_cli(["--batches", batches, "--out", out2, "--lanes", "17"])
        assert proc.returncode == 2, proc.returncode
        print("vector 6 CLI refusals (missing 9, malformed 2, lanes outside"
              " 1..16 refused): PASS")

        print("LEAN-SWEEP-SELFTEST PASS: six vectors all pass (binning/tier/"
              "skip-existing, casting/precheck/determinism, taxonomy pin,"
              " designed SKIP faces, two-sample liveness, CLI refusals)")
        return 0
    except AssertionError as exc:
        print("LEAN-SWEEP-SELFTEST FAIL: %s" % exc)
        return 2
    finally:
        import shutil as _shutil
        _shutil.rmtree(tmp, ignore_errors=True)


# ---- CLI ---------------------------------------------------------------------

def build_parser():
    ap = argparse.ArgumentParser(
        prog=TOOL, description="Lean vacuity probe batch sweep orchestrator"
        " (per-lane ledgers, skip-existing dedup, merged casting with syntax"
        " precheck, designed-SKIP compile leg, ALERT freeze gate, bisect"
        " fallback, stop-race recheck)")
    ap.add_argument("--batches", required=True, metavar="B.json",
                    help="batches plan (schema %s)" % BATCHES_SCHEMA)
    ap.add_argument("--out", required=True, metavar="DIR",
                    help="sweep output root (items tree, lane ledgers, shots)")
    ap.add_argument("--json", default=None, metavar="F",
                    help="status JSON path (default <out>/sweep-status.json)")
    ap.add_argument("--fire", action="store_true",
                    help="arm the compile leg (default: designed SKIP, loud)")
    ap.add_argument("--worktree", default=None, metavar="WT",
                    help="working directory for the compile leg")
    ap.add_argument("--lake", default=None, metavar="PATH",
                    help="lake binary (probe passes on file or PATH hit)")
    ap.add_argument("--guard", default=None, metavar="PATH",
                    help="optional thermal guard wrapper (seed command shape)")
    ap.add_argument("--core", type=int, default=DEFAULT_CORE, metavar="N",
                    help="cores passed to the guard wrapper (default %d)" % DEFAULT_CORE)
    ap.add_argument("--lanes", type=int, default=DEFAULT_LANES, metavar="N",
                    help="lane count, 1..%d (default %d)" % (MAX_LANES, DEFAULT_LANES))
    ap.add_argument("--skip-ledgers", nargs="*", default=[], metavar="F",
                    help="prior lane ledgers; their key union is skipped (rule 4)")
    ap.add_argument("--taxonomy", default=None, metavar="FILE",
                    help="row_render candidate rows (consumer pin: C3.4 mirror"
                    " plus canonical five-form caliber)")
    ap.add_argument("--max-shot-items", type=int, default=MAX_SHOT_ITEMS_DEFAULT,
                    metavar="N", help="merged GREEN shot cap (default %d)"
                    % MAX_SHOT_ITEMS_DEFAULT)
    ap.add_argument("--big-item-bytes", type=int, default=BIG_ITEM_BYTES_DEFAULT,
                    metavar="N", help="slow-lane threshold in bytes (default %d)"
                    % BIG_ITEM_BYTES_DEFAULT)
    ap.add_argument("--liveness-interval", type=float, default=LIVENESS_INTERVAL_DEFAULT,
                    metavar="S", help="two-sample spacing seconds (default %g; the"
                    " field value is 70-90)" % LIVENESS_INTERVAL_DEFAULT)
    ap.add_argument("--bisect-max", type=int, default=BISECT_MAX_DEFAULT, metavar="N",
                    help="extra-shot budget for bisect fallback (default %d)"
                    % BISECT_MAX_DEFAULT)
    ap.add_argument("--timeout-s", type=int, default=TIMEOUT_DEFAULT_S, metavar="S",
                    help="per-shot timeout seconds (default %d)" % TIMEOUT_DEFAULT_S)
    return ap


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        sys.exit(selftest())
    args = build_parser().parse_args(argv)
    status_path = args.json or os.path.join(args.out, "sweep-status.json")
    report = {"schema": STATUS_SCHEMA, "tool": TOOL,
              "compile_leg": "design-skip", "rows_written": 0,
              "tier_rows_written": 0, "shots_fired": 0,
              "shots_skipped_after_alert": 0, "bisect_shots": 0,
              "unjudged": 0, "failing_data": False,
              "alert_keys": [], "unjudged_keys": [],
              "precheck_failures": [], "out_of_band_rc": [],
              "liveness_samples": [], "zero_probe": [],
              "recheck": {"status": "not-run", "mismatches": []}}

    def finish(code):
        report["counts"] = {"green": report.pop("green_bin", 0),
                            "red": report.pop("red_bin", 0),
                            "tier": report.pop("tier_bin", 0)}
        status_dir = os.path.dirname(os.path.abspath(status_path))
        if status_dir and not os.path.isdir(status_dir):
            os.makedirs(status_dir, exist_ok=True)
        with open(status_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1, sort_keys=True)
        print("[sweep] status -> %s" % status_path)
        sys.exit(code)

    try:
        records = load_batches(args.batches, taxonomy_mode=bool(args.taxonomy))
        forms_by_family, tax_summary = None, None
        if args.taxonomy:
            _, forms_by_family, tax_summary = load_taxonomy(args.taxonomy)
            known = {r["familyId"] for r in records}
            holes = sorted({r["familyId"] for r in records
                            if r["familyId"] not in forms_by_family})
            if holes:
                raise FormError("taxonomy join hole: families %s have no candidate"
                                " row (the join must be total; nothing sweeps)"
                                % ", ".join(holes))
            unused = sorted(set(forms_by_family) - known)
            tax_summary["families_without_items"] = unused
            print("[sweep] taxonomy: %d rows, %d families, forms union %s%s"
                  % (tax_summary["rows"], tax_summary["families"],
                     tax_summary["forms_union"],
                     ("; %d families without items: %s" % (len(unused), unused))
                     if unused else ""))
        skip_keys, malformed = load_skip_ledgers(args.skip_ledgers)
        if malformed:
            print("[sweep] skip ledgers: %d malformed rows skipped (declared,"
                  " not silent)" % malformed)
    except MissingPath as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        sys.exit(9)
    except FormError as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        sys.exit(2)

    if not 1 <= args.lanes <= MAX_LANES:
        print("FAIL-LOUD: --lanes must be within 1..%d" % MAX_LANES, file=sys.stderr)
        sys.exit(2)
    if args.max_shot_items < 1 or args.big_item_bytes < 0 or args.bisect_max < 0:
        print("FAIL-LOUD: --max-shot-items/--big-item-bytes/--bisect-max out of"
              " range", file=sys.stderr)
        sys.exit(2)

    green, red, tier, zero_probe = bin_items(records, args.out, skip_keys,
                                             forms_by_family)
    report.update({"green_bin": len(green), "red_bin": len(red),
                   "tier_bin": len(tier), "skip_existing": len(skip_keys),
                   "zero_probe": zero_probe, "lanes": args.lanes})
    print("[sweep] GREEN=%d RED=%d SKIP-TIERT=%d (skip-existing %d keys across"
          " %d ledgers)" % (len(green), len(red), len(tier), len(skip_keys),
                            len(args.skip_ledgers)))
    if zero_probe:
        print("[sweep] %d items carry no probe file on disk: %s"
              % (len(zero_probe), ", ".join(zero_probe[:8])))
    plans = assign_lanes(green, red, tier, args.lanes, args.big_item_bytes,
                         args.max_shot_items)
    report["shots_planned"] = sum(len(p["shots"]) for p in plans)
    print("[sweep] %d lanes, %d shots planned (merged GREEN boxes capped at %d;"
          " falsify legs fire one per shot; items over %d bytes ride the slow"
          " lane)" % (args.lanes, report["shots_planned"], args.max_shot_items,
                      args.big_item_bytes))

    if not args.fire:
        # zero-compile face: every planned shot is cast and prechecked (rule
        # 2 proof without a compiler); any refusal is rc=3, nothing fires
        tag = time.strftime("%Y%m%dT%H%M%S")
        for plan in plans:
            for pos, entries in enumerate(plan["shots"]):
                cast = cast_shot(entries, "%s_p%d" % (tag, pos), plan["lane"],
                                 args.out)
                if cast[3]:
                    report["precheck_failures"].append(cast[3])
        if report["precheck_failures"]:
            for line in report["precheck_failures"]:
                print("SYNTAX-PRECHECK-FAIL: %s" % line)
            print("FAIL-LOUD: %d shot(s) refused by the syntax precheck;"
                  " nothing fires on a broken box (rule 2)" % len(report["precheck_failures"]),
                  file=sys.stderr)
            finish(3)
        print("[sweep] compile leg: design SKIP (--fire not given; nothing"
              " spawns; %d planned shot(s) cast and prechecked as plan"
              " artifacts)" % report["shots_planned"])
        report["taxonomy"] = tax_summary
        finish(0)

    # fire mode: toolchain probe first (loud skip when absent, rc stays 0)
    lake_resolved = resolve_tool(args.lake) if args.lake else None
    if not lake_resolved:
        print("[sweep] SKIP-TOOLCHAIN-ABSENT: --fire given but lake %r is not a"
              " file and not on PATH; compile leg stays a declared skip"
              % (args.lake,))
        report["compile_leg"] = "skip-toolchain-absent"
        report["taxonomy"] = tax_summary
        finish(0)
    guard_resolved = None
    if args.guard:
        guard_resolved = resolve_tool(args.guard)
        if not guard_resolved:
            print("FAIL-LOUD: guard %r is not a file and not on PATH" % args.guard,
                  file=sys.stderr)
            sys.exit(9)
    if not args.worktree:
        print("FAIL-LOUD: --fire requires --worktree (the compile leg runs with"
              " the worktree as cwd)", file=sys.stderr)
        sys.exit(2)
    ctx = {"worktree": args.worktree, "lake_resolved": lake_resolved,
           "guard_resolved": guard_resolved, "core": args.core,
           "timeout_s": args.timeout_s, "liveness_interval": args.liveness_interval,
           "bisect_max": args.bisect_max}
    report["compile_leg"] = "fired"
    report["taxonomy"] = tax_summary

    os.makedirs(args.out, exist_ok=True)
    expected_rows, lane_paths = [], []
    for plan in plans:
        lane_no = plan["lane"]
        lane_path = os.path.join(args.out, "results-lane%d.tsv" % lane_no)
        lane_paths.append(lane_path)
        run_lane(plan, lane_no, lane_path, args.out, ctx, report)
        # settle-time tally (rule 8 baseline): the claim this run makes about
        # the lane; the terminal recheck re-reads from disk afterwards, and
        # any drift names a stop race (a lane that kept moving after the
        # run believed it settled, or rows lost to an append race)
        expected_rows.append(ledger_line_count(lane_path))
    # rule 8: accept the completion claim only after a fresh disk recheck
    mismatches = recheck_terminal(lane_paths, expected_rows, args.out,
                                  report["alert_keys"])
    report["recheck"] = {"status": "mismatch" if mismatches else "passed",
                         "mismatches": mismatches}
    if report["alert_keys"]:
        print("ALERT FREEZE GATE: %d vacuity alert(s), stop-work; markers and"
              " judge-side counting (verdict_diff.py) form the double gate"
              % len(report["alert_keys"]))
        for key in report["alert_keys"]:
            print("  ALERT %s" % key)
        finish(2)
    if mismatches:
        for line in mismatches:
            print("STOP-RACE-MISMATCH: %s" % line)
        report["failing_data"] = True
    if report["precheck_failures"]:
        print("[sweep] %d precheck refusal(s) recorded (nothing fired for those"
              " probes)" % len(report["precheck_failures"]))
        report["failing_data"] = True
    if report["unjudged"] or report["unjudged_keys"]:
        print("[sweep] %d unjudged probes after fallback (declared; a re-slice"
              " picks them up via skip-existing)" % report["unjudged"])
        report["failing_data"] = True
    print("[sweep] recheck: %s; rows %d (tier %d), shots %d, bisect extras %d"
          % (report["recheck"]["status"], report["rows_written"],
             report["tier_rows_written"], report["shots_fired"],
             report["bisect_shots"]))
    finish(1 if report["failing_data"] else 0)


if __name__ == "__main__":
    main()
