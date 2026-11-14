#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""i18n_pipeline.py - E4 translation pipeline body (policy pre-check, prose
segmentation, four-linkage application, ledger closure).

Purpose.  Stages P0, P1, P3 and P6 of the zh<->en four-linkage pipeline
  (i18n SPEC sections 2-5, 7 and 9): P0 policy pre-check over the
  target-face regime table (refusal is a legal ledgered outcome); P1
  prose segmentation under a token protection list; P3 linkage
  application L1-L4, mechanical rewrites limited to the replace
  disposition; P6 append-only segment-ledger closure, gated on nine-key
  rows, machine segments at annotation_site "model", non-PENDING verdicts.
Interface.  Six operations with signatures fixed by
  seeds/i18n/pipeline_stub.py: segment_document(text, direction);
  translate_segments(segments, model_id, prompt_template_ref);
  apply_linkages(segments, linkage_ids); verify_faces(run_manifest);
  tenpoint_review(target_artifact); sync_ledger_append(ledger_path,
  rows).  CLI: --manifest RUN.json --stage p0|p1|p3|p6 [--json OUT]
  plus --selftest; bare invocation is a usage error.  Stage P2 and
  stages P4/P5 are assembled from companion modules (i18n_translate,
  i18n_verify) and fail loud when this tree lacks them.
Dependencies.  Python 3 standard library only; zero network on every
  face (the http provider is a companion-module face).  Data faces are
  the three engine seeds under seeds/ (ai_flavor, jargon, termbase).
Evidence.  --selftest runs in-memory zero-write vectors: regime table,
  refusal resolution, manifest shapes, segmentation spans, protection
  classes, row validation, closure gate, batteries, drift, supersede.
Exit-codes.  0 stage accounted (P0 refusal included); 1 data condition
  (closure gate red, malformed ledger or handoff); 2 usage or protocol
  violation; 9 missing input (manifest, target, ledger, companion).
"""
# Extended contract (kept outside the five-field block for the header
# budget; the comment face carries the same register rules as the docstring):
#
# Stage semantics (staged execution with resume, driven by a run directory):
#   p0  resolve the target face against P0_REGIMES (transcribed from i18n
#       SPEC section 7, grading rows D and E); append the policy annotation
#       row to the ledger before any translation; a refusal face ends the
#       run legally with exit 0 and later stages refuse to start.
#   p1  segment the target (file, or a tree scanned over .md/.py/.sh with
#       dot directories, docs/zh/ and *.zh.md archives skipped) and write
#       segments.json; the ledger is not touched at this stage (rows are
#       written at P2/P3 per the SPEC data contract).
#   p3  two phases.  Phase A: no translation-filled.jsonl in the run
#       directory -> assemble the handoff through the companion translation
#       module, write translation-handoff.jsonl, exit 0, and stop; the
#       model site fills translated_text, model_id, prompt_template_ref and
#       timestamp_utc per row.  Phase B: the filled file exists -> ingest
#       through the companion module, apply the declared linkages L1-L4 in
#       canonical order, write the translated artifacts under
#       translated/, and append one ledger row per segment.
#   p6  read the ledger, gate closure, and append a close record.  Ledger
#       rows may arrive from companion-module CLI faces as well as from p3;
#       the read rule is append-only supersede: the last row per
#       segment_id wins.  A ten-point verdict write-back is an updated row
#       appended by the verification companion, never an in-place edit.
#
# Run-directory file protocol (all keys English, deterministic bytes where
# no wall-clock field is required):
#   run-state.json            stage progress and the manifest fingerprint
#   segments.json             P1 output (segment_id, direction, target_file,
#                             source_span, source_text, protected_tokens)
#   translation-handoff.jsonl phase A output for the model site
#   translation-filled.jsonl  phase B input from the model site
#   translated-segments.json  phase B state: translated text plus findings
#   translated/<relative>     reconstructed target-face artifacts
#   ledger (manifest key)     segment-ledger.jsonl, append-only JSONL
#
# Linkage discipline: L1 resolves termbase entries through the companion
# lookup module and reports unresolved or inconsistent terms (report-only);
# L2 plans and applies jargon rewrites through the companion apply module
# and touches only replace-disposition entries; L3 is local and mechanical
# (zero CJK residue and em-dash density at most 1 per 1000 characters on
# the zh2en target register, protection-list zero-drift diff in both
# directions); L4 runs companion detection and records each hit as an
# advisory finding, never an automatic rewrite.  Linkage rewrites are
# accounted by the linkages_run key of the segment row; annotation_site
# keeps the translation site (model or human) and is not changed by
# linkage surgery.
#
# Protection list (byte-identical preservation, both directions): fenced
# code blocks (line level), inline backtick spans, URLs, file paths,
# CLI flags, math spans, dotted and case-shaped identifiers, numeric
# bracket citations, and parenthetical citations carrying a year.  The
# drift check compares per-token occurrence counts between source and
# translated text.
#
# Determinism: stage outputs other than ledger timestamps are byte-stable
# for identical inputs; file walks are sorted; reports carry no wall-clock
# fields.  Zero network: this module imports no socket-facing facility.

import argparse
import datetime
import hashlib
import importlib.util
import io
import json
import os
import re
import sys

PIPELINE_ID = "rocqwash-i18n-pipeline/1"

DIRECTIONS = ("zh2en", "en2zh")

# The four linkages of i18n SPEC section 3; values are data-face pointers
# (kept identical to the seed stub so the interface shape stays comparable).
LINKAGES = {
    "normalization": "seeds/termbase/termbase.json (E3 seed)",
    "standardization": "seeds/jargon/jargon-map.json (E2 seed); "
                       "docs/jargon-to-standard-mapping-v1.md (in-repo md form)",
    "internationalization": "SPEC section 2 preservation list; norm_lint "
                            "--cjk-threshold; em-dash density rule",
    "de_ai_flavor": "seeds/ai_flavor/word-map.json (E1 seed); "
                    "ai_flavor_selfcheck.sh battery precedent",
}

OPERATIONS = (
    "segment_document",
    "translate_segments",
    "apply_linkages",
    "verify_faces",
    "tenpoint_review",
    "sync_ledger_append",
)

SCHEMA_REPORT = "rocqwash.i18n.pipeline.report/1"
SCHEMA_SEGMENTS = "rocqwash.i18n.pipeline.segments/1"
SCHEMA_STATE = "rocqwash.i18n.pipeline.state/1"
SCHEMA_POLICY = "rocqwash.i18n.pipeline.policy/1"
SCHEMA_CLOSE = "rocqwash.i18n.pipeline.close/1"
SCHEMA_TRANSLATED = "rocqwash.i18n.pipeline.translated/1"

# Nine annotation keys of i18n SPEC section 5, in canonical order; a full
# segment row adds source_span (section 9).  No key may be added, dropped
# or renamed.
ANNOTATION_KEYS = (
    "segment_id",
    "direction",
    "model_id",
    "prompt_template_ref",
    "timestamp_utc",
    "linkages_run",
    "annotation_site",
    "policy_precheck_ref",
    "tenpoint_verdict",
)
ROW_KEYS = ANNOTATION_KEYS + ("source_span",)
SEGMENT_ID_RE = re.compile(r"\As\d{4,}\Z")
TENPOINT_VERDICTS = ("PENDING", "ALL-PASS", "N-FAIL", "BLOCKED")
ANNOTATION_SITES = ("model", "human")
POLICY_VERDICTS = ("accepted", "refused")

TARGET_FACES = ("repo", "paper", "supplement")

# P0 regime table, transcribed from the i18n SPEC section 7 grading rows D
# and E: review-sensitive faces default to disclosure_required true; the
# review-visible supplement face sits in the publication-line forbidden
# class (unpublished manuscripts under peer review must not carry
# AI-generated uploads), so refusal is true there and refusal is a legal,
# ledgered outcome.  This table is a module constant: a run manifest may
# not relax it.
P0_REGIMES = {
    "repo": {
        "regime_ref": "SPEC-7-E-repo-face",
        "disclosure_required": True,
        "refusal": False,
        "disclosure_form": [
            "usage statement",
            "in-text marking per segment",
            "prompt comparison record (segment ledger)",
        ],
        "red_lines": [
            "concealed machine text: every machine segment carries its "
            "model-site annotation",
            "no internal workflow identifiers on review-visible faces",
        ],
    },
    "paper": {
        "regime_ref": "SPEC-7-E-journal-line",
        "disclosure_required": True,
        "refusal": False,
        "disclosure_form": [
            "usage statement",
            "in-text marking per segment",
            "prompt comparison record (segment ledger)",
        ],
        "red_lines": [
            "no fabricated references",
            "no overclaiming beyond the source text",
            "machine use limited to readability and language polish",
        ],
    },
    "supplement": {
        "regime_ref": "SPEC-7-E-publication-line",
        "disclosure_required": True,
        "refusal": True,
        "disclosure_form": [],
        "red_lines": [
            "unpublished manuscripts under peer review must not carry "
            "AI-generated uploads (publication-line forbidden class)",
            "review-visible faces must not expose internal workflow "
            "identifiers or process narrative",
        ],
    },
}

STAGES = ("p0", "p1", "p3", "p6")

HANDOFF_OUT_NAME = "translation-handoff.jsonl"
HANDOFF_IN_NAME = "translation-filled.jsonl"
SEGMENTS_NAME = "segments.json"
STATE_NAME = "run-state.json"
TRANSLATED_NAME = "translated-segments.json"
TRANSLATED_DIR_NAME = "translated"

RE_FENCE = re.compile(r"\A\s*(?:```|~~~)")
RE_INLINE_CODE = re.compile(r"`[^`\n]+`")
RE_URL = re.compile(r"\b(?:https?|ftp)://[^\s<>\"')\]]+")
RE_MATH = re.compile(
    r"\$\$[^$]+\$\$|\$[^$\n]+\$\$?"
    r"|\\\((?:[^)\\]|\\.)*?\\\)"
    r"|\\\[(?:[^\]\\]|\\.)*?\\\]")
RE_PATH = re.compile(r"(?:[A-Za-z]:)?(?:[\\/][\w.\-]+)+[\\/]?")
RE_FLAG = re.compile(r"(?<![\w./\\-])(?:--[A-Za-z][\w-]*|-[A-Za-z]\b)")
RE_IDENT = re.compile(
    r"\b(?:[A-Za-z_][A-Za-z0-9_]*_[A-Za-z0-9_]+"
    r"|[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+"
    r"|[A-Z]{2,}(?:_[A-Z0-9]+)+"
    r"|\w+(?:\.\w+)+)\b")
RE_CITE_NUM = re.compile(r"\[\d+(?:\s*[,;\-]\s*\d+)*\]")
RE_CITE_YEAR = re.compile(r"\([^()\n]*(?:19|20)\d{2}[^()\n]*\)")

# Composite scanner: alternatives are ordered by priority, leftmost-longest
# behavior comes from the alternation order at each position.
RE_PROTECTED = re.compile(
    RE_INLINE_CODE.pattern
    + "|" + RE_URL.pattern
    + "|" + RE_MATH.pattern
    + "|" + RE_PATH.pattern
    + "|" + RE_FLAG.pattern
    + "|" + RE_CITE_NUM.pattern
    + "|" + RE_CITE_YEAR.pattern
    + "|" + RE_IDENT.pattern)

# Zero-residue battery ranges (zh2en target register): CJK blocks plus
# fullwidth forms and CJK punctuation, mirroring the norm_lint CJK face.
RE_CJK_RESIDUE = re.compile(
    "[\u2e80-\u2eff\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf"
    "\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")
EM_DASH = "\u2014"
EM_DASH_QUOTA_PER_1000 = 1.0  # i18n SPEC section 3 L3, glossary section 5

RE_FW_PAREN = re.compile("\uff08[^\uff09]*\uff09")
RE_BOLD = re.compile(r"\*\*(.+?)\*\*")

TREE_EXTENSIONS = (".md", ".py", ".sh")


class PipelineError(Exception):
    """Fail-loud carrier; exit_code selects the CLI exit (0/1/2/9 only)."""

    def __init__(self, message, exit_code=1):
        super(PipelineError, self).__init__(message)
        self.exit_code = int(exit_code)


def utc_now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def norm_slashes(path):
    return str(path).replace("\\", "/")


# ---------------------------------------------------------------- manifest


def validate_manifest_shape(manifest):
    """Shape-validate a parsed manifest (i18n SPEC section 9 form); a
    malformed shape is a usage error naming the key."""
    if not isinstance(manifest, dict):
        raise PipelineError("manifest must be a JSON object", 2)
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        raise PipelineError("manifest key run_id must be a non-empty string", 2)
    target = manifest.get("target")
    if not isinstance(target, dict):
        raise PipelineError("manifest key target must be an object", 2)
    tpath = target.get("path")
    if not isinstance(tpath, str) or not tpath.strip():
        raise PipelineError("manifest key target.path must be a non-empty "
                            "string", 2)
    face = target.get("face")
    if face not in TARGET_FACES:
        raise PipelineError("manifest key target.face must be one of %s"
                            % (TARGET_FACES,), 2)
    direction = manifest.get("direction")
    if direction not in DIRECTIONS:
        raise PipelineError("manifest key direction must be one of %s"
                            % (DIRECTIONS,), 2)
    ledger_path = manifest.get("ledger_path")
    if not isinstance(ledger_path, str) or not ledger_path.strip():
        raise PipelineError("manifest key ledger_path must be a non-empty "
                            "string", 2)
    linkages = manifest.get("linkages", list(LINKAGES))
    if (not isinstance(linkages, list) or not linkages
            or any(k not in LINKAGES for k in linkages)):
        raise PipelineError("manifest key linkages must be a non-empty list "
                            "drawn from %s" % (sorted(LINKAGES),), 2)
    pre = manifest.get("policy_precheck", {})
    if not isinstance(pre, dict):
        raise PipelineError("manifest key policy_precheck must be an object",
                            2)
    for key in ("disclosure_required", "refusal"):
        if key in pre and not isinstance(pre[key], bool):
            raise PipelineError("manifest key policy_precheck.%s must be a "
                                "boolean" % key, 2)
    if "regime_ref" in pre and not isinstance(pre["regime_ref"], str):
        raise PipelineError("manifest key policy_precheck.regime_ref must be "
                            "a string", 2)
    return manifest


def load_manifest(path):
    """Read and shape-validate a run manifest.

    Missing file exits 9; a malformed shape exits 2 naming the key."""
    if not os.path.isfile(path):
        raise PipelineError("manifest not found: %s" % path, 9)
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, UnicodeError) as exc:
        raise PipelineError("manifest unreadable: %s (%s)" % (path, exc), 9)
    except ValueError as exc:
        raise PipelineError("manifest not valid JSON: %s (%s)" % (path, exc), 2)
    return validate_manifest_shape(manifest)


def manifest_fingerprint(manifest):
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=True)
    return hashlib.md5(canonical.encode("utf-8")).hexdigest()


def run_dir_of(manifest):
    run_dir = os.path.dirname(manifest["ledger_path"])
    return run_dir if run_dir else "."


# ------------------------------------------------------------------- P0


def resolve_regime(face, policy_precheck):
    """Resolve the P0 verdict for a target face against the module table.

    The table governs: a manifest that disagrees with it on the booleans is
    a stage-protocol violation, never a way to relax the regime."""
    regime = P0_REGIMES[face]
    if "disclosure_required" in policy_precheck and (
            policy_precheck["disclosure_required"]
            != regime["disclosure_required"]):
        raise PipelineError(
            "policy_precheck.disclosure_required=%s contradicts the regime "
            "table for face %s (table value %s); the regime table governs"
            % (policy_precheck["disclosure_required"], face,
               regime["disclosure_required"]), 2)
    if "refusal" in policy_precheck and (
            policy_precheck["refusal"] != regime["refusal"]):
        raise PipelineError(
            "policy_precheck.refusal=%s contradicts the regime table for "
            "face %s (table value %s); the regime table governs"
            % (policy_precheck["refusal"], face, regime["refusal"]), 2)
    verdict = {
        "face": face,
        "regime_ref": policy_precheck.get("regime_ref",
                                          regime["regime_ref"]),
        "disclosure_required": regime["disclosure_required"],
        "refusal": regime["refusal"],
        "disclosure_form": list(regime["disclosure_form"]),
        "red_lines": list(regime["red_lines"]),
    }
    return verdict


def policy_precheck_ref(manifest, face):
    return "P0-%s-%s" % (face, manifest["run_id"])


def policy_row(run_id, ref, verdict, direction, target_path):
    return {
        "schema": SCHEMA_POLICY,
        "record_type": "policy",
        "run_id": run_id,
        "policy_precheck_ref": ref,
        "target": norm_slashes(target_path),
        "face": verdict["face"],
        "direction": direction,
        "regime_ref": verdict["regime_ref"],
        "disclosure_required": verdict["disclosure_required"],
        "refusal": verdict["refusal"],
        "disclosure_form": verdict["disclosure_form"],
        "red_lines": verdict["red_lines"],
        "verdict": "refused" if verdict["refusal"] else "accepted",
        "timestamp_utc": utc_now_iso(),
    }


# --------------------------------------------------------------- P1 segment


def extract_protected_tokens(text):
    """Protected-token scan, first-appearance order, deduplicated."""
    tokens = []
    seen = set()
    for match in RE_PROTECTED.finditer(text):
        token = match.group(0)
        if token and token not in seen:
            seen.add(token)
            tokens.append(token)
    return tokens


def segment_document(text, direction):
    """Split a document into prose segments (i18n SPEC section 4 P1).

    A segment is a maximal run of consecutive prose lines: blank lines and
    fenced code blocks break runs, fenced interiors are excluded whole.
    Each segment carries its source_span (1-based, end inclusive) and the
    protected tokens extracted from its text.  Segment ids are assigned
    s0001.. within this call; the CLI renumbers across files deterministically.
    """
    if not isinstance(text, str):
        raise PipelineError("segment_document: text must be a string", 2)
    if direction not in DIRECTIONS:
        raise PipelineError("segment_document: direction must be one of %s"
                            % (DIRECTIONS,), 2)
    lines = text.splitlines()
    segments = []
    run_start = None
    in_fence = False
    for idx, line in enumerate(lines, 1):
        if RE_FENCE.match(line):
            if run_start is not None:
                segments.append((run_start, idx - 1))
                run_start = None
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.strip():
            if run_start is not None:
                segments.append((run_start, idx - 1))
                run_start = None
            continue
        if run_start is None:
            run_start = idx
    if run_start is not None:
        segments.append((run_start, len(lines)))
    out = []
    for number, (start, end) in enumerate(segments, 1):
        seg_text = "\n".join(lines[start - 1:end])
        out.append({
            "segment_id": "s%04d" % number,
            "direction": direction,
            "source_span": {"start_line": start, "end_line": end},
            "source_text": seg_text,
            "protected_tokens": extract_protected_tokens(seg_text),
        })
    return out


# ----------------------------------------------------------------- ledger


def validate_segment_row(row):
    """Full segment-row shape: exactly ROW_KEYS, verbatim values checked."""
    if not isinstance(row, dict):
        raise PipelineError("segment row must be a JSON object", 1)
    keys = set(row.keys())
    missing = [k for k in ROW_KEYS if k not in keys]
    extra = [k for k in sorted(keys - set(ROW_KEYS))]
    if missing or extra:
        raise PipelineError(
            "segment row %s key set drifted from the nine-key contract: "
            "missing=%s extra=%s" % (row.get("segment_id"), missing, extra), 1)
    if not SEGMENT_ID_RE.match(row["segment_id"]):
        raise PipelineError("segment row has malformed segment_id %r"
                            % (row["segment_id"],), 1)
    if row["direction"] not in DIRECTIONS:
        raise PipelineError("segment row %s direction not in %s"
                            % (row["segment_id"], (DIRECTIONS,)), 1)
    for key in ("model_id", "prompt_template_ref", "timestamp_utc",
                "policy_precheck_ref"):
        value = row[key]
        if not isinstance(value, str) or not value.strip():
            raise PipelineError("segment row %s key %s must be a non-empty "
                                "string" % (row["segment_id"], key), 1)
    span = row["source_span"]
    if not isinstance(span, dict) or set(span.keys()) != {
            "start_line", "end_line"}:
        raise PipelineError("segment row %s source_span must carry exactly "
                            "start_line and end_line" % row["segment_id"], 1)
    for key in ("start_line", "end_line"):
        if not isinstance(span[key], int) or isinstance(span[key], bool) \
                or span[key] < 1:
            raise PipelineError("segment row %s source_span.%s must be a "
                                "positive integer" % (row["segment_id"], key),
                                1)
    if span["start_line"] > span["end_line"]:
        raise PipelineError("segment row %s source_span start exceeds end"
                            % row["segment_id"], 1)
    if row["annotation_site"] not in ANNOTATION_SITES:
        raise PipelineError("segment row %s annotation_site not in %s"
                            % (row["segment_id"], (ANNOTATION_SITES,)), 1)
    if row["tenpoint_verdict"] not in TENPOINT_VERDICTS:
        raise PipelineError("segment row %s tenpoint_verdict not in %s"
                            % (row["segment_id"], (TENPOINT_VERDICTS,)), 1)
    run = row["linkages_run"]
    if (not isinstance(run, list) or not run
            or any(k not in LINKAGES for k in run)):
        raise PipelineError("segment row %s linkages_run must be a non-empty "
                            "list drawn from %s"
                            % (row["segment_id"], (sorted(LINKAGES),)), 1)
    return row


def validate_policy_row(row):
    required = {
        "schema", "record_type", "run_id", "policy_precheck_ref", "target",
        "face", "direction", "regime_ref", "disclosure_required", "refusal",
        "disclosure_form", "red_lines", "verdict", "timestamp_utc",
    }
    keys = set(row.keys()) if isinstance(row, dict) else set()
    if keys != required:
        raise PipelineError(
            "policy row key set drifted: missing=%s extra=%s"
            % (sorted(required - keys), sorted(keys - required)), 1)
    if row["record_type"] != "policy":
        raise PipelineError("policy row record_type must be 'policy'", 1)
    if row["face"] not in TARGET_FACES:
        raise PipelineError("policy row face not in %s" % (TARGET_FACES,), 1)
    if row["direction"] not in DIRECTIONS:
        raise PipelineError("policy row direction not in %s" % (DIRECTIONS,),
                            1)
    if row["verdict"] not in POLICY_VERDICTS:
        raise PipelineError("policy row verdict not in %s" % (POLICY_VERDICTS,),
                            1)
    if not isinstance(row["disclosure_required"], bool) \
            or not isinstance(row["refusal"], bool):
        raise PipelineError("policy row booleans must be JSON booleans", 1)
    for key in ("disclosure_form", "red_lines"):
        if not isinstance(row[key], list):
            raise PipelineError("policy row key %s must be a list" % key, 1)
    return row


def validate_close_row(row):
    required = {
        "schema", "record_type", "run_id", "segments_total",
        "machine_segments", "human_segments", "verdict", "timestamp_utc",
    }
    keys = set(row.keys()) if isinstance(row, dict) else set()
    if keys != required:
        raise PipelineError(
            "close row key set drifted: missing=%s extra=%s"
            % (sorted(required - keys), sorted(keys - required)), 1)
    if row["record_type"] != "close":
        raise PipelineError("close row record_type must be 'close'", 1)
    if row["verdict"] != "closed":
        raise PipelineError("close row verdict must be 'closed'", 1)
    for key in ("segments_total", "machine_segments", "human_segments"):
        if not isinstance(row[key], int) or isinstance(row[key], bool) \
                or row[key] < 0:
            raise PipelineError("close row key %s must be a non-negative "
                                "integer" % key, 1)
    return row


def validate_ledger_rows(rows):
    for position, row in enumerate(rows, 1):
        kind = row.get("record_type") if isinstance(row, dict) else None
        if kind == "policy":
            validate_policy_row(row)
        elif kind == "close":
            validate_close_row(row)
        elif kind is None:
            validate_segment_row(row)
        else:
            raise PipelineError("ledger line %d has unknown record_type %r"
                                % (position, kind), 1)
    return rows


def sync_ledger_append(ledger_path, rows):
    """Append rows to the segment ledger (i18n SPEC section 4 P6).

    Append-only JSONL, one object per line, English keys, shape-validated
    before the first byte is written.  Returns the number of rows appended.
    """
    if not isinstance(rows, (list, tuple)):
        raise PipelineError("sync_ledger_append: rows must be a list", 2)
    rows = list(rows)
    validate_ledger_rows(rows)
    parent = os.path.dirname(ledger_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    payload = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")) + "\n"
        for row in rows)
    with io.open(ledger_path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
    return len(rows)


def read_ledger(ledger_path):
    """Parse the ledger; malformed JSONL is a data condition (exit 1)."""
    if not os.path.isfile(ledger_path):
        raise PipelineError("segment ledger not found: %s" % ledger_path, 9)
    try:
        with io.open(ledger_path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except (OSError, UnicodeError) as exc:
        raise PipelineError("segment ledger unreadable: %s (%s)"
                            % (ledger_path, exc), 9)
    rows = []
    for number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except ValueError as exc:
            raise PipelineError(
                "segment ledger %s line %d is not valid JSON (%s)"
                % (ledger_path, number, exc), 1)
    return rows


def latest_segment_rows(rows):
    """Append-only supersede: the last row per segment_id wins."""
    latest = {}
    for row in rows:
        if isinstance(row, dict) and "segment_id" in row \
                and "record_type" not in row:
            latest[row["segment_id"]] = row
    return latest


def closure_gate(rows, expected_ids=()):
    """P6 closure gate over the ledger.

    Machine rows (model_id not the literal human) must sit at annotation
    site model; every segment row must be nine-key complete with a
    source_span and a non-PENDING verdict; every expected segment from P1
    must have a row.  Returns (violations, counts)."""
    violations = []
    latest = latest_segment_rows(rows)
    for segment_id in sorted(expected_ids):
        if segment_id not in latest:
            violations.append({
                "segment_id": segment_id,
                "problems": ["no ledger row for a P1 segment"],
            })
    machine = 0
    human = 0
    for segment_id in sorted(latest):
        row = latest[segment_id]
        problems = []
        try:
            validate_segment_row(row)
        except PipelineError as exc:
            problems.append(str(exc))
        if row.get("tenpoint_verdict") == "PENDING":
            problems.append("tenpoint_verdict is PENDING; closure needs a "
                            "written-back verdict")
        if row.get("model_id") != "human" \
                and row.get("annotation_site") != "model":
            problems.append("machine segment at annotation_site %r; the "
                            "contract requires \"model\""
                            % (row.get("annotation_site"),))
        if problems:
            violations.append({"segment_id": segment_id,
                               "problems": problems})
        if row.get("model_id") == "human":
            human += 1
        else:
            machine += 1
    return violations, {
        "segments_total": len(latest),
        "machine_segments": machine,
        "human_segments": human,
    }


def close_row(run_id, counts):
    return {
        "schema": SCHEMA_CLOSE,
        "record_type": "close",
        "run_id": run_id,
        "segments_total": counts["segments_total"],
        "machine_segments": counts["machine_segments"],
        "human_segments": counts["human_segments"],
        "verdict": "closed",
        "timestamp_utc": utc_now_iso(),
    }


# ------------------------------------------------- companion module loader


_COMPANIONS = {}

VERIFY_VERIFY_CANDIDATES = (
    "verify_faces", "run_verify_faces", "run_verify", "verify", "run_p4")
VERIFY_TENPOINT_CANDIDATES = (
    "emit_tenpoint", "emit_tenpoint_form", "tenpoint_form", "run_p5")


def load_companion(module_name, required=()):
    """Load a sibling engine module by path from this file's directory.

    Deterministic under python -I (no sys.path dependence).  Missing file
    or missing contract callable fails loud with exit 9."""
    cached = _COMPANIONS.get(module_name)
    if cached is not None:
        return cached
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, module_name + ".py")
    if not os.path.isfile(path):
        raise PipelineError(
            "companion module tools/%s.py is not present in this tree; this "
            "face needs it (contract callables: %s). Land the companion "
            "module first, then re-run."
            % (module_name, ", ".join(required) or "per contract"), 9)
    spec = importlib.util.spec_from_file_location(
        "i18n_pipeline_companion_" + module_name, path)
    if spec is None or spec.loader is None:
        raise PipelineError("companion module %s cannot be loaded" % path, 9)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    missing = [name for name in required
               if not callable(getattr(module, name, None))]
    if missing:
        raise PipelineError(
            "companion module tools/%s.py lacks contract callables: %s"
            % (module_name, ", ".join(missing)), 9)
    _COMPANIONS[module_name] = module
    return module


def resolve_callable(module, names, module_name):
    for name in names:
        candidate = getattr(module, name, None)
        if callable(candidate):
            return name, candidate
    raise PipelineError(
        "companion module tools/%s.py exposes none of the expected P4/P5 "
        "entry points (%s); the contract names its CLI face but not its "
        "in-module function names, so the integration pass must reconcile "
        "this interface gap" % (module_name, ", ".join(names)), 9)


# ------------------------------------------------------------ linkages


def canonical_linkages(linkage_ids):
    if not isinstance(linkage_ids, (list, tuple)) or not linkage_ids:
        raise PipelineError("linkage ids must be a non-empty list", 2)
    unknown = [k for k in linkage_ids if k not in LINKAGES]
    if unknown:
        raise PipelineError("unknown linkage ids: %s" % (unknown,), 2)
    return [k for k in LINKAGES if k in set(linkage_ids)]


def termbase_inventory():
    """Enumerate termbase entry faces from the data seed (report-only L1).

    Irregular rows are counted and skipped, mirroring the seed's own
    irregular-row register; this returns {face: standard_display}."""
    path = os.path.join(repo_root(), "seeds", "termbase", "termbase.json")
    if not os.path.isfile(path):
        raise PipelineError("termbase seed not found: %s" % path, 9)
    with io.open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise PipelineError("termbase seed %s carries no entries list" % path,
                            9)
    inventory = {}
    irregular = 0
    for entry in entries:
        cells = entry.get("cells") if isinstance(entry, dict) else None
        if not isinstance(cells, list) or not cells:
            irregular += 1
            continue
        face = clean_cell(cells[0])
        if not face or len(face) > 30 or "|" in face:
            irregular += 1
            continue
        standard = ""
        if len(cells) > 1:
            bold = RE_BOLD.search(cells[1])
            standard = clean_cell(bold.group(1)) if bold \
                else clean_cell(cells[1])[:60]
        inventory.setdefault(face, standard)
    return inventory, irregular, path


def clean_cell(text):
    if not isinstance(text, str):
        return ""
    stripped = RE_FW_PAREN.sub("", text)
    stripped = stripped.replace("**", " ").strip()
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped


def l1_normalization(segment, inventory, irregular):
    """Termbase lookup through the companion module (report-only): faces
    observed in the source text resolve against the termbase; a face with
    no entries is an advisory finding.  The companion module must exist
    whenever the linkage is declared, matched faces or not."""
    module = load_companion("termbase", ("lookup",))
    findings = []
    source_text = segment["source_text"]
    for face in sorted(inventory):
        if face not in source_text:
            continue
        try:
            resolved = module.lookup(face)
        except PipelineError:
            raise
        except Exception as exc:
            raise PipelineError("termbase lookup failed for %r (%s)"
                                % (face, exc), 1)
        if not isinstance(resolved, list) or not resolved:
            findings.append({
                "segment_id": segment["segment_id"],
                "linkage": "normalization",
                "kind": "term-unresolved",
                "detail": "termbase lookup returned no entries for %r" % face,
            })
    findings.append({
        "segment_id": segment["segment_id"],
        "linkage": "normalization",
        "kind": "inventory-note",
        "detail": "inventory faces=%d irregular_rows=%d (report-only)"
                  % (len(inventory), irregular),
    })
    return findings


def l2_standardization(segment):
    """Plan and apply jargon rewrites through the companion apply module.

    Mechanical rewrites are limited to what the companion plan returns
    (replace disposition per its contract); each plan entry must carry a
    before/after pair or the interface is declared broken."""
    module = load_companion("jargon_apply",
                            ("load_map", "plan_rewrites", "apply_rewrites"))
    map_path = os.path.join(repo_root(), "seeds", "jargon", "jargon-map.json")
    jargon_map = module.load_map(map_path)
    text = segment["translated_text"]
    entries = module.plan_rewrites(text, jargon_map)
    if not isinstance(entries, list):
        raise PipelineError(
            "jargon_apply.plan_rewrites returned %s instead of an entry list"
            % (type(entries).__name__,), 9)
    for entry in entries:
        if not isinstance(entry, dict) \
                or not isinstance(entry.get("before"), str) \
                or not isinstance(entry.get("after"), str):
            raise PipelineError(
                "jargon_apply.plan_rewrites entry lacks a before/after pair "
                "(observed keys: %s); contract expects before/after pairs"
                % (sorted(entry.keys()) if isinstance(entry, dict)
                   else type(entry).__name__,), 9)
    new_text, applied = module.apply_rewrites(text, entries)
    if not isinstance(new_text, str):
        raise PipelineError("jargon_apply.apply_rewrites returned a "
                            "non-string text", 9)
    segment["translated_text"] = new_text
    findings = [{
        "segment_id": segment["segment_id"],
        "linkage": "standardization",
        "kind": "rewrite-applied",
        "detail": "planned=%d applied=%d" % (len(entries), len(applied)),
    }]
    return findings


def l3_internationalization(segment):
    """Mechanical locale face: CJK residue, em-dash density, drift diff.

    The residue and density batteries bind the zh2en target register only
    (Chinese em-dash and fullwidth punctuation are legal on en2zh targets);
    the protection-list drift check binds both directions."""
    findings = []
    text = segment["translated_text"]
    direction = segment["direction"]
    if direction == "zh2en":
        residue_lines = []
        for offset, line in enumerate(text.splitlines(), 1):
            count = len(RE_CJK_RESIDUE.findall(line))
            if count:
                residue_lines.append(
                    {"line": offset, "count": count})
        if residue_lines:
            findings.append({
                "segment_id": segment["segment_id"],
                "linkage": "internationalization",
                "kind": "cjk-residue",
                "detail": residue_lines,
            })
        em_count = text.count(EM_DASH)
        density = em_count * 1000.0 / max(len(text), 1)
        if density > EM_DASH_QUOTA_PER_1000:
            findings.append({
                "segment_id": segment["segment_id"],
                "linkage": "internationalization",
                "kind": "em-dash-density",
                "detail": "count=%d chars=%d density=%.3f per 1000 (quota "
                          "%.1f)" % (em_count, len(text), density,
                                     EM_DASH_QUOTA_PER_1000),
            })
    source_text = segment.get("source_text", "")
    for token in segment.get("protected_tokens", []):
        expected = source_text.count(token)
        actual = text.count(token)
        if actual < expected:
            findings.append({
                "segment_id": segment["segment_id"],
                "linkage": "internationalization",
                "kind": "protection-drift",
                "detail": "token %r expected %d occurrence(s), found %d"
                          % (token, expected, actual),
            })
    return findings


def l4_de_ai_flavor(segment):
    """Detection-only sweep; every hit is an advisory finding (never an
    automatic rewrite; remediation belongs to the apply-companion flow)."""
    module = load_companion("ai_flavor", ("load_word_map", "detect_text"))
    map_path = os.path.join(repo_root(), "seeds", "ai_flavor",
                            "word-map.json")
    word_map = module.load_word_map(map_path)
    report = module.detect_text(segment["translated_text"], word_map)
    if not isinstance(report, dict) or not isinstance(report.get("hits"),
                                                      list):
        raise PipelineError(
            "ai_flavor.detect_text returned %s instead of a report with a "
            "hits list" % (type(report).__name__,), 9)
    findings = []
    for hit in report["hits"]:
        if not isinstance(hit, dict):
            raise PipelineError("ai_flavor hit entry is not an object", 9)
        findings.append({
            "segment_id": segment["segment_id"],
            "linkage": "de_ai_flavor",
            "kind": "detection-hit",
            "detail": {
                "face_id": hit.get("face_id"),
                "battery": hit.get("battery"),
                "line": hit.get("line"),
                "before": hit.get("before"),
                "after": hit.get("after"),
            },
        })
    return findings


def apply_linkages(segments, linkage_ids):
    """Apply the linkage chain over translated segments (SPEC section 4 P3).

    Expects translated segment dicts (segment_id, direction, translated_text,
    source_text, protected_tokens).  Order is canonical L1-L4 regardless of
    the caller's list order; only L2 rewrites text.  Returns (segments,
    findings)."""
    order = canonical_linkages(linkage_ids)
    if not isinstance(segments, (list, tuple)):
        raise PipelineError("apply_linkages: segments must be a list", 2)
    inventory = None
    irregular = 0
    findings = []
    for segment in segments:
        if not isinstance(segment, dict) or not segment.get("segment_id") \
                or not isinstance(segment.get("translated_text"), str):
            raise PipelineError(
                "apply_linkages expects translated segment dicts with "
                "segment_id and translated_text", 2)
        for linkage in order:
            if linkage == "normalization":
                if inventory is None:
                    inventory, irregular, _ = termbase_inventory()
                findings.extend(l1_normalization(segment, inventory,
                                                 irregular))
            elif linkage == "standardization":
                findings.extend(l2_standardization(segment))
            elif linkage == "internationalization":
                findings.extend(l3_internationalization(segment))
            elif linkage == "de_ai_flavor":
                findings.extend(l4_de_ai_flavor(segment))
    return list(segments), findings


# --------------------------------------------------- assembled operations


def translate_segments(segments, model_id, prompt_template_ref):
    """Assemble stage P2 in handoff form (zero network; the http provider
    is a companion-module CLI face and is never reached from here)."""
    if not isinstance(segments, (list, tuple)) or not segments:
        raise PipelineError("translate_segments: segments must be a "
                            "non-empty list", 2)
    if model_id is not None and (not isinstance(model_id, str)
                                 or not model_id.strip()):
        raise PipelineError("translate_segments: model_id must be a "
                            "non-empty string when given", 2)
    if prompt_template_ref is not None and (
            not isinstance(prompt_template_ref, str)
            or not prompt_template_ref.strip()):
        raise PipelineError("translate_segments: prompt_template_ref must "
                            "be a non-empty string when given", 2)
    directions = set()
    for segment in segments:
        if not isinstance(segment, dict) \
                or segment.get("direction") not in DIRECTIONS:
            raise PipelineError("translate_segments: every segment needs a "
                                "valid direction", 2)
        directions.add(segment["direction"])
    if len(directions) != 1:
        raise PipelineError("translate_segments: mixed directions in one "
                            "run (%s)" % (sorted(directions),), 2)
    module = load_companion("i18n_translate",
                            ("build_handoff", "ingest_translations"))
    rows = module.build_handoff(list(segments), directions.pop())
    if not isinstance(rows, list) or not rows:
        raise PipelineError(
            "i18n_translate.build_handoff returned no rows; expected one "
            "handoff row per segment", 9)
    for row in rows:
        if not isinstance(row, dict) or not row.get("segment_id"):
            raise PipelineError(
                "i18n_translate.build_handoff row lacks segment_id", 9)
    return {
        "mode": "handoff",
        "rows": rows,
        "expected_model_id": model_id,
        "prompt_template_ref": prompt_template_ref,
        "next": "fill translated_text, model_id, prompt_template_ref and "
                "timestamp_utc per row, save as " + HANDOFF_IN_NAME
                + ", then re-run stage p3",
    }


def verify_faces(run_manifest):
    """Assemble stage P4 through the verification companion module."""
    if not isinstance(run_manifest, dict):
        raise PipelineError("verify_faces: run_manifest must be a dict", 2)
    module = load_companion("i18n_verify")
    name, fn = resolve_callable(module, VERIFY_VERIFY_CANDIDATES,
                                "i18n_verify")
    return fn(run_manifest)


def tenpoint_review(target_artifact):
    """Assemble stage P5 (emit face) through the verification companion.

    The verdict itself stays human-performed; the companion CLI face ingests
    the filled verdict file and writes verdict rows back to the ledger."""
    if not isinstance(target_artifact, str) or not target_artifact.strip():
        raise PipelineError("tenpoint_review: target_artifact must be a "
                            "non-empty path string", 2)
    module = load_companion("i18n_verify")
    name, fn = resolve_callable(module, VERIFY_TENPOINT_CANDIDATES,
                                "i18n_verify")
    return fn(target_artifact)


# ------------------------------------------------------------ run support


def repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


def state_path(run_dir):
    return os.path.join(run_dir, STATE_NAME)


def load_state(run_dir):
    path = state_path(run_dir)
    if not os.path.isfile(path):
        return None
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, UnicodeError, ValueError) as exc:
        raise PipelineError("run state unreadable: %s (%s)" % (path, exc), 1)


def write_state(run_dir, state):
    path = state_path(run_dir)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    payload = json.dumps(state, ensure_ascii=False, indent=1,
                         sort_keys=True) + "\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)


def write_json(path, obj):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    payload = json.dumps(obj, ensure_ascii=False, indent=1,
                         sort_keys=True) + "\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)


def read_json_file(path, exit_code=9):
    if not os.path.isfile(path):
        raise PipelineError("file not found: %s" % path, exit_code)
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, UnicodeError) as exc:
        raise PipelineError("file unreadable: %s (%s)" % (path, exc),
                            exit_code)
    except ValueError as exc:
        raise PipelineError("file not valid JSON: %s (%s)" % (path, exc), 1)


def read_text_file(path):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeError) as exc:
        raise PipelineError("target unreadable: %s (%s)" % (path, exc), 9)


def walk_target_files(target_path):
    if os.path.isfile(target_path):
        return [target_path]
    if not os.path.isdir(target_path):
        raise PipelineError("target not found: %s" % target_path, 9)
    collected = []
    for root, dirnames, filenames in os.walk(target_path):
        dirnames[:] = sorted(d for d in dirnames
                             if not d.startswith(".") and d != "zh")
        for filename in sorted(filenames):
            if filename.endswith(".zh.md"):
                continue
            if os.path.splitext(filename)[1] in TREE_EXTENSIONS:
                collected.append(os.path.join(root, filename))
    return collected


def check_state(manifest, state, need_stages):
    """Stage-protocol gate: fingerprint drift and required prior stages."""
    fingerprint = manifest_fingerprint(manifest)
    run_dir = run_dir_of(manifest)
    if state is None:
        raise PipelineError(
            "no run state in %s; run stage p0 first" % run_dir, 2)
    if state.get("manifest_md5") != fingerprint:
        raise PipelineError(
            "manifest drift: the run directory %s was started with a "
            "different manifest; use a fresh run directory" % run_dir, 2)
    stages = state.get("stages", {})
    for stage in need_stages:
        if stages.get(stage, {}).get("status") != "done":
            raise PipelineError(
                "stage order violation: stage %s must run before this "
                "stage (run it first)" % stage, 2)
    return stages


def ledger_has_policy_row(rows, ref):
    for row in rows:
        if isinstance(row, dict) and row.get("record_type") == "policy" \
                and row.get("policy_precheck_ref") == ref:
            return row
    return None


# ---------------------------------------------------------- stage runners


def run_stage_p0(manifest, args):
    run_dir = run_dir_of(manifest)
    os.makedirs(run_dir, exist_ok=True)
    fingerprint = manifest_fingerprint(manifest)
    state = load_state(run_dir)
    face = manifest["target"]["face"]
    verdict = resolve_regime(face, manifest.get("policy_precheck", {}))
    ref = policy_precheck_ref(manifest, face)
    if state is not None \
            and state.get("manifest_md5") != fingerprint \
            and state.get("stages", {}).get("p0", {}).get("status") == "done":
        raise PipelineError(
            "manifest drift: run directory %s was started with a different "
            "manifest; use a fresh run directory" % run_dir, 2)
    if state is not None \
            and state.get("manifest_md5") == fingerprint \
            and state.get("stages", {}).get("p0", {}).get("status") == "done":
        return ({
            "stage": "p0",
            "verdict": state["stages"]["p0"]["verdict"],
            "policy_precheck_ref": ref,
            "noop": "already recorded for this manifest",
        }, 0)
    ledger_path = manifest["ledger_path"]
    existing = None
    if os.path.isfile(ledger_path):
        existing = ledger_has_policy_row(read_ledger(ledger_path), ref)
    if existing is None:
        row = policy_row(manifest["run_id"], ref, verdict,
                         manifest["direction"], manifest["target"]["path"])
        sync_ledger_append(ledger_path, [row])
    recorded = "refused" if verdict["refusal"] else "accepted"
    if state is None:
        state = {"schema": SCHEMA_STATE, "run_id": manifest["run_id"],
                 "manifest_md5": fingerprint, "stages": {}}
    state.setdefault("stages", {})["p0"] = {
        "status": "done",
        "verdict": recorded,
        "policy_precheck_ref": ref,
    }
    write_state(run_dir, state)
    return ({
        "stage": "p0",
        "verdict": recorded,
        "policy_precheck_ref": ref,
        "regime_ref": verdict["regime_ref"],
        "disclosure_required": verdict["disclosure_required"],
        "refusal": verdict["refusal"],
        "red_lines": verdict["red_lines"],
    }, 0)


def run_stage_p1(manifest, args):
    run_dir = run_dir_of(manifest)
    state = load_state(run_dir)
    stages = check_state(manifest, state, need_stages=("p0",))
    if stages.get("p0", {}).get("verdict") == "refused":
        raise PipelineError(
            "this run was refused at the policy pre-check (face %s); "
            "translation is forbidden on this face and later stages will "
            "not start" % manifest["target"]["face"], 2)
    if stages.get("p1", {}).get("status") == "done":
        segments_path = os.path.join(run_dir, SEGMENTS_NAME)
        if not os.path.isfile(segments_path):
            raise PipelineError(
                "run state records stage p1 as done but %s is missing"
                % segments_path, 9)
        data = read_json_file(segments_path)
        return ({"stage": "p1", "segments": len(data.get("segments", [])),
                 "noop": "already segmented for this manifest"}, 0)
    target_path = manifest["target"]["path"]
    files = walk_target_files(target_path)
    segments = []
    counter = 0
    base = target_path if os.path.isdir(target_path) else \
        os.path.dirname(target_path) or "."
    for path in files:
        text = read_text_file(path)
        for segment in segment_document(text, manifest["direction"]):
            counter += 1
            segment["segment_id"] = "s%04d" % counter
            rel = os.path.relpath(path, base)
            segment["target_file"] = norm_slashes(rel)
            # the P0 annotation precedes translation: every P1 segment
            # row carries the policy pre-check reference of this run
            segment["policy_precheck_ref"] = policy_precheck_ref(
                manifest, manifest["target"]["face"])
            segments.append(segment)
    write_json(os.path.join(run_dir, SEGMENTS_NAME), {
        "schema": SCHEMA_SEGMENTS,
        "run_id": manifest["run_id"],
        "direction": manifest["direction"],
        "target": norm_slashes(target_path),
        "segments": segments,
    })
    state.setdefault("stages", {})["p1"] = {
        "status": "done",
        "segments": len(segments),
        "files": len(files),
    }
    write_state(run_dir, state)
    return ({
        "stage": "p1",
        "segments": len(segments),
        "files": len(files),
        "protected_tokens_total": sum(len(s["protected_tokens"])
                                      for s in segments),
    }, 0)


def run_stage_p3(manifest, args):
    run_dir = run_dir_of(manifest)
    state = load_state(run_dir)
    stages = check_state(manifest, state, need_stages=("p0", "p1"))
    if stages.get("p0", {}).get("verdict") == "refused":
        raise PipelineError(
            "this run was refused at the policy pre-check; stage p3 will "
            "not start", 2)
    segments_path = os.path.join(run_dir, SEGMENTS_NAME)
    data = read_json_file(segments_path)
    segments = data.get("segments")
    if not isinstance(segments, list):
        raise PipelineError("%s carries no segments list" % segments_path, 1)
    ref = stages["p0"]["policy_precheck_ref"]
    linkages_run = canonical_linkages(manifest.get("linkages",
                                                   list(LINKAGES)))
    if not segments:
        state["stages"]["p3"] = {"status": "done", "phase": "applied",
                                 "segments": 0}
        write_state(run_dir, state)
        return ({"stage": "p3", "phase": "applied", "segments": 0,
                 "findings": {}, "ledger_rows": 0}, 0)
    handout = os.path.join(run_dir, HANDOFF_OUT_NAME)
    handin = os.path.join(run_dir, HANDOFF_IN_NAME)
    if not os.path.isfile(handin):
        assembled = translate_segments(segments, None, None)
        payload = "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n"
            for row in assembled["rows"])
        parent = os.path.dirname(handout)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with io.open(handout, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload)
        state["stages"]["p3"] = {"status": "emit",
                                 "phase": "handoff-emitted",
                                 "rows": len(assembled["rows"])}
        write_state(run_dir, state)
        return ({
            "stage": "p3",
            "phase": "handoff-emitted",
            "rows": len(assembled["rows"]),
            "handoff": norm_slashes(handout),
            "next": assembled["next"],
        }, 0)
    raw_rows = read_handoff_rows(handin)
    translated, annotation_rows = ingest_translated(segments, raw_rows)
    translated, findings = apply_linkages(translated, linkages_run)
    artifacts = write_translated_artifacts(manifest, segments, translated)
    write_json(os.path.join(run_dir, TRANSLATED_NAME), {
        "schema": SCHEMA_TRANSLATED,
        "run_id": manifest["run_id"],
        "direction": manifest["direction"],
        "linkages_run": linkages_run,
        "segments": translated,
        "findings": findings,
    })
    ledger_path = manifest["ledger_path"]
    existing_rows = read_ledger(ledger_path) \
        if os.path.isfile(ledger_path) else []
    present = set()
    for row in existing_rows:
        if isinstance(row, dict) and "segment_id" in row \
                and "record_type" not in row \
                and row.get("policy_precheck_ref") == ref:
            present.add(row["segment_id"])
    wanted = [s["segment_id"] for s in translated]
    extras = present - set(wanted)
    if extras:
        raise PipelineError(
            "ledger holds rows for this run that no segment produced "
            "(%s); resolve the run directory before re-running stage p3"
            % (sorted(extras),), 1)
    if set(wanted) <= present:
        rows_written = 0
    else:
        _require_policy_row(existing_rows, ref)
        rows = []
        for segment in translated:
            annotation = annotation_for(annotation_rows, segment["segment_id"])
            rows.append(build_segment_row(segment, annotation, linkages_run,
                                          ref))
        rows_written = sync_ledger_append(ledger_path, rows)
    state["stages"]["p3"] = {"status": "done", "phase": "applied",
                             "segments": len(translated)}
    write_state(run_dir, state)
    tally = {}
    for finding in findings:
        key = "%s/%s" % (finding["linkage"], finding["kind"])
        tally[key] = tally.get(key, 0) + 1
    return ({
        "stage": "p3",
        "phase": "applied",
        "segments": len(translated),
        "linkages_run": linkages_run,
        "findings_tally": tally,
        "artifacts": artifacts,
        "ledger_rows_written": rows_written,
    }, 0)


def read_handoff_rows(path):
    rows = []
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except (OSError, UnicodeError) as exc:
        raise PipelineError("filled handoff unreadable: %s (%s)"
                            % (path, exc), 9)
    for number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except ValueError as exc:
            raise PipelineError(
                "filled handoff %s line %d is not valid JSON (%s)"
                % (path, number, exc), 1)
    return rows


def ingest_translated(segments, raw_rows):
    """Ingest through the companion module and merge the translated text
    into the P1 segment dicts (the returned working set keeps source_text,
    protected_tokens, source_span and target_file, so linkage L3 can run
    its drift diff).  Loud companion rejections map to the data-condition
    exit (1) with the named message kept."""
    module = load_companion("i18n_translate",
                            ("build_handoff", "ingest_translations"))
    try:
        translated, annotation_rows = module.ingest_translations(
            list(segments), raw_rows)
    except PipelineError:
        raise
    except Exception as exc:
        raise PipelineError("handoff ingestion rejected the filled rows (%s)"
                            % exc, 1)
    if not isinstance(translated, list) \
            or not isinstance(annotation_rows, list):
        raise PipelineError(
            "i18n_translate.ingest_translations returned %s / %s; expected "
            "(translated list, ledger rows list)"
            % (type(translated).__name__, type(annotation_rows).__name__), 9)
    by_id = {}
    for item in translated:
        if not isinstance(item, dict) or not item.get("segment_id"):
            raise PipelineError(
                "ingested translation item lacks segment_id", 1)
        text = item.get("translated_text")
        if not isinstance(text, str) or not text.strip():
            raise PipelineError(
                "ingested translation for %s carries no translated_text"
                % item["segment_id"], 1)
        by_id[item["segment_id"]] = text
    working = []
    for segment in segments:
        segment_id = segment["segment_id"]
        if segment_id not in by_id:
            raise PipelineError(
                "no ingested translation for segment %s" % segment_id, 1)
        merged = dict(segment)
        merged["translated_text"] = by_id[segment_id]
        working.append(merged)
    return working, annotation_rows


def annotation_for(annotation_rows, segment_id):
    for row in annotation_rows:
        if isinstance(row, dict) and row.get("segment_id") == segment_id:
            annotation = {}
            for key in ("model_id", "prompt_template_ref", "timestamp_utc"):
                value = row.get(key)
                if not isinstance(value, str) or not value.strip():
                    raise PipelineError(
                        "annotation row for %s lacks %s; the model-site "
                        "annotation is the disclosure obligation itself"
                        % (segment_id, key), 1)
                annotation[key] = value
            return annotation
    raise PipelineError("no annotation row for segment %s" % segment_id, 1)


def build_segment_row(segment, annotation, linkages_run, ref):
    row = {
        "segment_id": segment["segment_id"],
        "direction": segment["direction"],
        "source_span": segment["source_span"],
        "model_id": annotation["model_id"],
        "annotation_site": "human" if annotation["model_id"] == "human"
        else "model",
        "prompt_template_ref": annotation["prompt_template_ref"],
        "linkages_run": list(linkages_run),
        "policy_precheck_ref": ref,
        "tenpoint_verdict": "PENDING",
        "timestamp_utc": annotation["timestamp_utc"],
    }
    return validate_segment_row(row)


def _require_policy_row(rows, ref):
    """The P0 annotation row must precede any translation row, and a
    refusal row forbids translation rows outright."""
    row = ledger_has_policy_row(rows, ref)
    if row is None:
        raise PipelineError(
            "no policy annotation row with reference %s in the ledger; the "
            "P0 note must land before any translation row (run stage p0)"
            % ref, 2)
    if row.get("verdict") == "refused":
        raise PipelineError(
            "the policy row for this run records a refusal; translation "
            "rows are forbidden", 2)
    return row


def write_translated_artifacts(manifest, segments, translated):
    """Reconstruct target-face artifacts under translated/ (never in place
    on the source; the archive-sibling law belongs to the replacement
    routing slot, not to this pipeline)."""
    target_path = manifest["target"]["path"]
    base = target_path if os.path.isdir(target_path) else \
        os.path.dirname(target_path) or "."
    by_file = {}
    for segment in translated:
        by_file.setdefault(segment["target_file"], []).append(segment)
    artifacts = []
    run_dir = run_dir_of(manifest)
    for rel in sorted(by_file):
        source_path = os.path.join(base, rel.replace("/", os.sep))
        original = read_text_file(source_path)
        lines = original.splitlines()
        pieces = []
        cursor = 0
        file_segments = sorted(by_file[rel],
                               key=lambda s: s["source_span"]["start_line"])
        for segment in file_segments:
            start = segment["source_span"]["start_line"] - 1
            end = segment["source_span"]["end_line"]
            pieces.extend(lines[cursor:start])
            pieces.extend(segment["translated_text"].splitlines())
            cursor = end
        pieces.extend(lines[cursor:])
        text = "\n".join(pieces)
        if original.endswith("\n") and not text.endswith("\n"):
            text += "\n"
        out_path = os.path.join(run_dir, TRANSLATED_DIR_NAME,
                                rel.replace("/", os.sep))
        parent = os.path.dirname(out_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        artifacts.append(norm_slashes(out_path))
    return artifacts


def run_stage_p6(manifest, args):
    """Close the ledger; returns (report, exit_code) - an unclosed gate is
    a data condition and exits 1 with the named violations."""
    run_dir = run_dir_of(manifest)
    state = load_state(run_dir)
    if state is not None \
            and state.get("manifest_md5") == manifest_fingerprint(manifest) \
            and state.get("stages", {}).get("p0", {}).get("verdict") \
            == "refused":
        return ({
            "stage": "p6",
            "verdict": "refused-run",
            "note": "the run was refused at the policy pre-check; there is "
                    "nothing to close and no close record is written",
        }, 0)
    stages = check_state(manifest, state, need_stages=("p0", "p1"))
    ledger_path = manifest["ledger_path"]
    rows = read_ledger(ledger_path)
    close_positions = [i for i, row in enumerate(rows)
                       if isinstance(row, dict)
                       and row.get("record_type") == "close"]
    segment_positions = [i for i, row in enumerate(rows)
                         if isinstance(row, dict) and "segment_id" in row
                         and "record_type" not in row]
    if close_positions and segment_positions \
            and max(segment_positions) > max(close_positions):
        raise PipelineError(
            "ledger carries segment rows after the close record; the "
            "append-only ledger was re-opened", 1)
    if close_positions:
        return ({"stage": "p6", "verdict": "closed",
                 "noop": "close record already present"}, 0)
    segments_path = os.path.join(run_dir, SEGMENTS_NAME)
    data = read_json_file(segments_path)
    expected_ids = [s["segment_id"] for s in data.get("segments", [])]
    violations, counts = closure_gate(rows, expected_ids)
    if violations:
        return ({
            "stage": "p6",
            "verdict": "unclosed",
            "violations": violations,
            "counts": counts,
        }, 1)
    sync_ledger_append(ledger_path, [close_row(manifest["run_id"], counts)])
    return ({"stage": "p6", "verdict": "closed", "counts": counts}, 0)


# ------------------------------------------------------------- selftest


def selftest(out):
    """In-memory vectors, zero writes; returns the process exit code."""
    out.write("I18N PIPELINE SELFTEST (%s)\n" % PIPELINE_ID)
    failures = []
    checks = [0]

    def check(name, fn):
        checks[0] += 1
        try:
            fn()
        except AssertionError as exc:
            failures.append("%s: %s" % (name, exc))
        except PipelineError as exc:
            failures.append("%s: unexpected PipelineError %s" % (name, exc))
        except Exception as exc:
            failures.append("%s: %r" % (name, exc))

    def expect_error(name_fn, fragment):
        try:
            name_fn()
        except PipelineError as exc:
            assert fragment in str(exc), (
                "message %r lacks %r" % (str(exc), fragment))
            return
        raise AssertionError("expected a PipelineError")

    def v_constants():
        assert OPERATIONS == (
            "segment_document", "translate_segments", "apply_linkages",
            "verify_faces", "tenpoint_review", "sync_ledger_append")
        assert DIRECTIONS == ("zh2en", "en2zh")
        assert set(LINKAGES) == {
            "normalization", "standardization", "internationalization",
            "de_ai_flavor"}
        assert set(P0_REGIMES) == set(TARGET_FACES)
        for face, regime in P0_REGIMES.items():
            assert regime["disclosure_required"] is True, face
            assert isinstance(regime["red_lines"], list) and regime["red_lines"]
        assert P0_REGIMES["supplement"]["refusal"] is True
        assert P0_REGIMES["paper"]["refusal"] is False
        assert P0_REGIMES["repo"]["refusal"] is False

    def v_regime():
        verdict = resolve_regime("paper", {})
        assert verdict["refusal"] is False
        assert verdict["disclosure_required"] is True
        verdict = resolve_regime("supplement", {})
        assert verdict["refusal"] is True
        expect_error(lambda: resolve_regime("paper", {"refusal": True}),
                     "regime table governs")
        expect_error(lambda: resolve_regime(
            "repo", {"disclosure_required": False}), "regime table governs")

    def v_manifest():
        base = {
            "run_id": "i18n-selftest",
            "target": {"path": "unused.md", "face": "paper"},
            "direction": "zh2en",
            "ledger_path": "unused/segment-ledger.jsonl",
        }
        assert manifest_fingerprint(base) != manifest_fingerprint(dict(
            base, direction="en2zh"))
        validate_manifest_shape(base)
        expect_error(lambda: load_manifest(os.path.join(
            os.sep, "definitely", "absent.json")), "not found")
        no_ledger = dict(base, ledger_path="")
        expect_error(lambda: validate_manifest_shape(no_ledger), "ledger_path")
        bad_face = dict(base, target={"path": "a", "face": "novel"})
        expect_error(lambda: validate_manifest_shape(bad_face), "target.face")
        bad_dir = dict(base, direction="fr2de")
        expect_error(lambda: validate_manifest_shape(bad_dir), "direction")

    def v_segmentation():
        text = "\n".join([
            "# Title",
            "",
            "Prose line one.",
            "Prose line two with `code` and --flag.",
            "",
            "```",
            "x = 1",
            "```",
            "More prose after the fence.",
        ])
        segments = segment_document(text, "zh2en")
        spans = [(s["source_span"]["start_line"], s["source_span"]["end_line"])
                 for s in segments]
        assert spans == [(1, 1), (3, 4), (9, 9)], spans
        tokens = segments[1]["protected_tokens"]
        assert tokens == ["`code`", "--flag"], tokens
        expect_error(lambda: segment_document(text, "fr2de"),
                     "direction must be one of")

    def v_protection_classes():
        text = ("See https://example.com/x and C:\\data\\file.md, run "
                "run_stage --json out.json with my_var and CamelCase, math "
                "$a+b$ plus [1] and (Smith, 1999).")
        tokens = extract_protected_tokens(text)
        joined = "\n".join(tokens)
        assert "https://example.com/x" in joined
        assert "C:\\data\\file.md" in joined
        assert "--json" in joined
        assert "my_var" in joined
        assert "CamelCase" in joined
        assert "$a+b$" in joined
        assert "[1]" in joined
        assert "(Smith, 1999)" in joined

    def v_row_validation():
        row = {
            "segment_id": "s0001",
            "direction": "zh2en",
            "source_span": {"start_line": 1, "end_line": 2},
            "model_id": "model-x",
            "annotation_site": "model",
            "prompt_template_ref": "prompts/zh2en-repo-v1",
            "linkages_run": ["internationalization"],
            "policy_precheck_ref": "P0-paper-run",
            "tenpoint_verdict": "ALL-PASS",
            "timestamp_utc": "1970-01-01T00:00:00Z",
        }
        validate_segment_row(row)
        broken = dict(row)
        del broken["annotation_site"]
        expect_error(lambda: validate_segment_row(broken),
                     "annotation_site")
        broken = dict(row)
        broken["surprise"] = 1
        expect_error(lambda: validate_segment_row(broken), "extra=")
        broken = dict(row)
        broken["tenpoint_verdict"] = "MAYBE"
        expect_error(lambda: validate_segment_row(broken), "tenpoint_verdict")
        broken = dict(row)
        broken["source_span"] = {"start_line": 2, "end_line": 1}
        expect_error(lambda: validate_segment_row(broken), "exceeds end")

    def v_closure_gate():
        def good_row(segment_id, verdict, site="model", model="model-x"):
            return {
                "segment_id": segment_id,
                "direction": "zh2en",
                "source_span": {"start_line": 1, "end_line": 1},
                "model_id": model,
                "annotation_site": site,
                "prompt_template_ref": "prompts/zh2en-repo-v1",
                "linkages_run": ["internationalization"],
                "policy_precheck_ref": "P0-paper-run",
                "tenpoint_verdict": verdict,
                "timestamp_utc": "1970-01-01T00:00:00Z",
            }
        policy = {
            "schema": SCHEMA_POLICY, "record_type": "policy", "run_id": "r",
            "policy_precheck_ref": "P0-paper-run", "target": "a.md",
            "face": "paper", "direction": "zh2en",
            "regime_ref": "SPEC-7-E-journal-line",
            "disclosure_required": True, "refusal": False,
            "disclosure_form": [], "red_lines": [], "verdict": "accepted",
            "timestamp_utc": "1970-01-01T00:00:00Z",
        }
        rows = [policy, good_row("s0001", "ALL-PASS"),
                good_row("s0002", "N-FAIL")]
        validate_ledger_rows(rows)
        violations, counts = closure_gate(rows, ["s0001", "s0002"])
        assert violations == [], violations
        assert counts == {"segments_total": 2, "machine_segments": 2,
                          "human_segments": 0}, counts
        rows.append(good_row("s0003", "PENDING"))
        violations, _ = closure_gate(rows)
        assert any(v["segment_id"] == "s0003" for v in violations)
        rows[-1] = good_row("s0003", "ALL-PASS", site="human")
        violations, _ = closure_gate(rows)
        assert any("annotation_site" in p
                   for v in violations for p in v["problems"])
        rows[-1] = good_row("s0003", "ALL-PASS", model="human",
                            site="human")
        violations, counts = closure_gate(rows)
        assert violations == []
        assert counts["human_segments"] == 1

    def v_supersede():
        row_a = {"segment_id": "s0001", "tenpoint_verdict": "PENDING"}
        row_b = {"segment_id": "s0001", "tenpoint_verdict": "ALL-PASS"}
        latest = latest_segment_rows([row_a, row_b])
        assert latest["s0001"]["tenpoint_verdict"] == "ALL-PASS"

    def v_density_and_residue():
        cjk = "\u6b8a\u7559"
        findings_gate = l3_internationalization({
            "segment_id": "s0001", "direction": "zh2en",
            "translated_text": "clean text " + cjk,
            "source_text": "clean text", "protected_tokens": []})
        assert any(f["kind"] == "cjk-residue" for f in findings_gate)
        findings_gate = l3_internationalization({
            "segment_id": "s0001", "direction": "en2zh",
            "translated_text": cjk,
            "source_text": "text", "protected_tokens": []})
        assert not any(f["kind"] == "cjk-residue" for f in findings_gate)
        long_text = "x" * 2000 + EM_DASH
        findings_gate = l3_internationalization({
            "segment_id": "s0001", "direction": "zh2en",
            "translated_text": long_text, "source_text": "",
            "protected_tokens": []})
        assert not any(f["kind"] == "em-dash-density" for f in findings_gate)
        short_text = "x" * 600 + EM_DASH
        findings_gate = l3_internationalization({
            "segment_id": "s0001", "direction": "zh2en",
            "translated_text": short_text, "source_text": "",
            "protected_tokens": []})
        assert any(f["kind"] == "em-dash-density" for f in findings_gate)

    def v_drift():
        findings_gate = l3_internationalization({
            "segment_id": "s0001", "direction": "zh2en",
            "translated_text": "kept --flag only",
            "source_text": "use --flag and `keep`",
            "protected_tokens": ["--flag", "`keep`"]})
        assert any(f["kind"] == "protection-drift"
                   and "`keep`" in str(f["detail"]) for f in findings_gate)
        findings_gate = l3_internationalization({
            "segment_id": "s0001", "direction": "zh2en",
            "translated_text": "use --flag and `keep`",
            "source_text": "use --flag and `keep`",
            "protected_tokens": ["--flag", "`keep`"]})
        assert not any(f["kind"] == "protection-drift"
                       for f in findings_gate)

    def v_linkage_order():
        assert canonical_linkages(
            ["de_ai_flavor", "normalization"]) == [
            "normalization", "de_ai_flavor"]
        expect_error(lambda: canonical_linkages(["nope"]), "unknown linkage")
        expect_error(lambda: apply_linkages([{"segment_id": "s0001"}],
                                            ["internationalization"]),
                     "translated segment dicts")

    def v_id_and_ref():
        manifest = {"run_id": "run-7", "target": {"path": "a", "face": "repo"},
                    "direction": "zh2en", "ledger_path": "x"}
        assert policy_precheck_ref(manifest, "repo") == "P0-repo-run-7"

    check("constants", v_constants)
    check("regime", v_regime)
    check("manifest", v_manifest)
    check("segmentation", v_segmentation)
    check("protection-classes", v_protection_classes)
    check("row-validation", v_row_validation)
    check("closure-gate", v_closure_gate)
    check("ledger-supersede", v_supersede)
    check("density-and-residue", v_density_and_residue)
    check("protection-drift", v_drift)
    check("linkage-order", v_linkage_order)
    check("id-and-ref", v_id_and_ref)
    if failures:
        for item in failures:
            out.write("SELFTEST FAIL %s\n" % item)
        out.write("SELFTEST FAIL (%d of %d vectors)\n"
                  % (len(failures), checks[0]))
        return 1
    out.write("SELFTEST PASS (%d vectors, zero writes, zero network)\n"
              % checks[0])
    return 0


# ------------------------------------------------------------------ CLI


def build_parser():
    parser = argparse.ArgumentParser(
        prog="i18n_pipeline.py",
        description="E4 translation pipeline body: stages p0/p1/p3/p6 over "
                    "a run manifest (see the i18n SPEC in seeds/i18n; "
                    "companion modules carry stages P2/P4/P5).",
    )
    parser.add_argument("--manifest", default=None, metavar="RUN.json",
                        help="run manifest (i18n SPEC section 9 form)")
    parser.add_argument("--stage", default=None, choices=list(STAGES),
                        help="stage to execute; stages are resumable")
    parser.add_argument("--json", default=None, metavar="OUT",
                        help="write the stage report JSON to OUT")
    parser.add_argument("--selftest", action="store_true",
                        help="in-memory vectors, zero writes, exit 0")
    return parser


def emit_report(args, report):
    payload = json.dumps(
        dict(report, schema=SCHEMA_REPORT), ensure_ascii=False, indent=1,
        sort_keys=True) + "\n"
    if args.json:
        write_json(args.json, dict(report, schema=SCHEMA_REPORT))
    else:
        sys.stdout.write(payload)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        if args.manifest or args.stage or args.json:
            sys.stderr.write(
                "i18n_pipeline: --selftest takes no other flags\n")
            return 2
        return selftest(sys.stdout)
    if not args.manifest or not args.stage:
        sys.stderr.write(
            "i18n_pipeline: give --manifest RUN.json and --stage "
            "p0|p1|p3|p6 (or --selftest)\n")
        parser.print_usage(sys.stderr)
        return 2
    runners = {
        "p0": run_stage_p0,
        "p1": run_stage_p1,
        "p3": run_stage_p3,
        "p6": run_stage_p6,
    }
    try:
        manifest = load_manifest(args.manifest)
        report, code = runners[args.stage](manifest, args)
    except PipelineError as exc:
        sys.stderr.write("i18n_pipeline: %s\n" % exc)
        return exc.exit_code
    emit_report(args, report)
    return code


if __name__ == "__main__":
    sys.exit(main())
