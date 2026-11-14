#!/usr/bin/env python3
"""i18n_translate.py - model-site translation stage (P2) of the E4 pipeline.

Purpose. Enforce per-segment model-site annotation (SPEC section 5): every
machine-translated segment carries a nine-key record (segment_id, direction,
model_id, prompt_template_ref, timestamp_utc, linkages_run, annotation_site,
policy_precheck_ref, tenpoint_verdict); a backfill with no model_id, or a
segment delivered with no annotation at all, is rejected loud. The default
handoff form is fully zero-network: emit a segment packet, an external
model-side agent backfills translations, ingest validates and produces the
ledger rows. The optional http form is an OpenAI-compatible chat/completions
provider behind a default-deny environment gate, with one NETRED ledger line
per call, failures included.
Interface. Pure functions: build_handoff(segments, direction) -> rows;
ingest_translations(segments, rows, prompt_refs=None)
-> (translated, ledger_rows); check_net_env(environ) -> refusal-or-None;
parse_chat_response(payload_text) -> (content, error); protected_token_findings(
segments, translated) -> findings. CLI: --segments <json> --direction
zh2en|en2zh plus exactly one action: --emit <out.jsonl> (zero network),
--ingest <in.jsonl> (zero network), or --provider http --netred-ledger <p>.
Shared flags: --prompts <dir>, --policy-ref <s>, --translated-out <json>,
--ledger-out <jsonl>, --json <report>, --timeout <s>, --selftest.
Dependencies. Stdlib only: argparse, datetime, io, json, os, sys,
urllib.error, urllib.request. Zero third-party imports.
Evidence. Contract translate-provider row; i18n SPEC sections 5 and 9.
Exit-codes. 0 success; 1 data verdict red (ingest rejections, incomplete
backfill coverage, failed segment calls, malformed input data); 2 usage or
environment refusal (missing flag or direction, closed net gate, missing
provider configuration, prompt template shape, each named on stderr); 9
input or output file unreadable.
"""
# Extended contract (moved from the docstring to hold the 30-line header
# budget): Dependencies, environment gate.  The http form fires only when
# ROCQWASH_MCP_ALLOW_NET equals "1" and all three of ROCQWASH_LLM_ENDPOINT /
# ROCQWASH_LLM_MODEL / ROCQWASH_LLM_KEY are set; a missing item is named on
# stderr and the run refuses. Credentials never enter packet files, ledger
# rows, reports, or log lines.
# Evidence detail. Interface contract, translate-provider row and its CLI section
# (emit row keys, backfill row keys, built-in prompt naming form); seeds/i18n
# SPEC sections 5 and 9 (nine-key annotation, ledger row form: no additions,
# deletions, or renames); loader discipline per tools/norm_lint.py (fail
# loud, unreadable input exits 9).

import argparse
import datetime
import io
import json
import os
import sys
import urllib.error
import urllib.request

TOOL = "i18n_translate.py"
SCHEMA_REPORT = "rocqwash.i18n.translate/1"

DIRECTIONS = ("zh2en", "en2zh")
PROVIDERS = ("handoff", "http")

# Nine annotation keys of SPEC section 5, canonical order; the ledger row
# produced by ingest_translations carries exactly these keys, no additions
# and no renames.
ANNOTATION_KEYS = (
    "segment_id",
    "direction",
    "model_id",
    "annotation_site",
    "prompt_template_ref",
    "linkages_run",
    "policy_precheck_ref",
    "tenpoint_verdict",
    "timestamp_utc",
)

# Emit row keys per the contract (six keys, exactly).
EMIT_KEYS = (
    "segment_id",
    "direction",
    "source_text",
    "protected_tokens",
    "prompt_template_ref",
    "instruction",
)

# Backfill row keys per the contract (five keys, exactly).
BACKFILL_KEYS = (
    "segment_id",
    "translated_text",
    "model_id",
    "prompt_template_ref",
    "timestamp_utc",
)

NET_GATE_ENV = "ROCQWASH_MCP_ALLOW_NET"
NET_CONFIG_ENVS = (
    "ROCQWASH_LLM_ENDPOINT",
    "ROCQWASH_LLM_MODEL",
    "ROCQWASH_LLM_KEY",
)

HUMAN_MODEL_ID = "human"
SITE_MODEL = "model"
SITE_HUMAN = "human"
VERDICT_PENDING = "PENDING"
LINKAGES_AT_P2 = []

# Built-in prompt templates. The named refs follow the contract naming form
# "prompts/zh2en-repo-v1". Templates carry {source_text} and
# {protected_tokens} placeholders and instruct byte-identical preservation of
# protected tokens (SPEC section 2 preservation list).
BUILTIN_TEMPLATE_ZH2EN = (
    "Translate the Chinese prose below into repository-face English.\n"
    "Rules:\n"
    "1. Keep every protected token byte-identical: {protected_tokens}\n"
    "2. Translate prose only; never add commentary, headings, or notes.\n"
    "3. Use plain declarative English with concrete verbs; avoid inflated\n"
    "   marketing wording and avoid the AI-flavor register words registered\n"
    "   in the project glossary.\n"
    "4. Keep the sentence structure of the source; do not merge or split\n"
    "   sentences.\n"
    "5. Output only the translation.\n"
    "\n"
    "Source text:\n"
    "{source_text}\n"
)
BUILTIN_TEMPLATE_EN2ZH = (
    "Translate the English prose below into Chinese following the project\n"
    "terminology register.\n"
    "Rules:\n"
    "1. Keep every protected token byte-identical: {protected_tokens}\n"
    "2. For any domain term use the standard Chinese term registered in the\n"
    "   project termbase; do not coin new renderings.\n"
    "3. Translate prose only; never add commentary, headings, or notes.\n"
    "4. Output only the translation.\n"
    "\n"
    "Source text:\n"
    "{source_text}\n"
)
BUILTIN_PROMPTS = {
    "zh2en": ("prompts/zh2en-repo-v1", BUILTIN_TEMPLATE_ZH2EN),
    "en2zh": ("prompts/en2zh-repo-v1", BUILTIN_TEMPLATE_EN2ZH),
}

# Per-row instruction carried in the emit packet.
INSTRUCTIONS = {
    "zh2en": (
        "Translate this prose segment into repository-face English. Keep the"
        " protected tokens byte-identical, translate prose only, and return"
        " only the translation."
    ),
    "en2zh": (
        "Translate this prose segment into Chinese using the project"
        " termbase standard terms. Keep the protected tokens byte-identical,"
        " translate prose only, and return only the translation."
    ),
}


def die(message, code):
    sys.stderr.write("%s: %s\n" % (TOOL, message))
    raise SystemExit(code)


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def parse_utc(value):
    """Return True when value is a parseable ISO-8601 UTC instant string."""
    if not isinstance(value, str) or not value:
        return False
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        datetime.datetime.fromisoformat(text)
    except ValueError:
        return False
    return True


# ---------------------------------------------------------------------------
# input and output helpers
# ---------------------------------------------------------------------------


def load_segments(path):
    """Read a segments JSON file (array, or object with a segments key)."""
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as exc:
        die("segments file unreadable: %s (%s)" % (path, exc), 9)
    try:
        data = json.loads(raw)
    except ValueError as exc:
        die("segments file is not valid JSON: %s (%s)" % (path, exc), 1)
    if isinstance(data, dict) and isinstance(data.get("segments"), list):
        data = data["segments"]
    return data


def load_backfill_rows(path):
    """Read a backfill JSONL file (one JSON object per non-empty line)."""
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as exc:
        die("backfill file unreadable: %s (%s)" % (path, exc), 9)
    rows = []
    for lineno, line in enumerate(raw.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except ValueError as exc:
            die(
                "backfill line %d is not valid JSON: %s (%s)"
                % (lineno, path, exc),
                1,
            )
    return rows


def write_jsonl(path, rows):
    try:
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as exc:
        die("output not writable: %s (%s)" % (path, exc), 9)


def write_json(path, payload):
    try:
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2))
            handle.write("\n")
    except OSError as exc:
        die("output not writable: %s (%s)" % (path, exc), 9)


def resolve_prompt(prompt_dir, direction):
    """Return (prompt_template_ref, template_text) for one direction.

    Built-in constants when prompt_dir is None; otherwise the template
    file whose name starts with the direction and ends .txt or .md inside
    prompt_dir; the emitted ref is prompts/<file-stem>, matching the
    contract naming form. Ambiguous or absent templates fail loud.
    """
    if prompt_dir is None:
        return BUILTIN_PROMPTS[direction]
    candidates = []
    for name in sorted(os.listdir(prompt_dir)):
        if name.startswith(direction) and name.endswith((".txt", ".md")):
            candidates.append(name)
    if not candidates:
        die(
            "prompt dir %s carries no %s*.txt or %s*.md template"
            % (prompt_dir, direction, direction),
            2,
        )
    if len(candidates) > 1:
        die(
            "prompt dir %s carries ambiguous %s templates: %s"
            % (prompt_dir, direction, ", ".join(candidates)),
            2,
        )
    chosen = os.path.join(prompt_dir, candidates[0])
    try:
        with io.open(chosen, "r", encoding="utf-8") as handle:
            template = handle.read()
    except OSError as exc:
        die("prompt template unreadable: %s (%s)" % (chosen, exc), 9)
    if "{source_text}" not in template:
        die(
            "prompt template %s lacks the {source_text} placeholder" % chosen,
            2,
        )
    ref = "prompts/" + os.path.splitext(os.path.basename(chosen))[0]
    return ref, template


def render_prompt(template, source_text, protected_tokens):
    """Fill the template placeholders; unknown placeholders fail loud."""
    token_text = ", ".join(protected_tokens) if protected_tokens else "(none)"
    try:
        return template.format(
            source_text=source_text, protected_tokens=token_text
        )
    except (KeyError, IndexError, ValueError) as exc:
        die("prompt template has an unusable placeholder (%s)" % exc, 2)


# ---------------------------------------------------------------------------
# pure faces (importable by the pipeline assembly lane)
# ---------------------------------------------------------------------------


def check_segments(segments, need_direction=False, need_policy=False):
    """Validate the segment list shape; raise ValueError naming the defect.

    Required per segment: non-empty string segment_id (unique across the
    list) and string source_text. Optional: protected_tokens (list of
    strings), source_span, direction, policy_precheck_ref. Ingest and the
    http provider additionally require direction and a non-empty
    policy_precheck_ref (P0 annotation precedes translation), with one
    direction shared by the whole list.
    """
    if not isinstance(segments, list) or not segments:
        raise ValueError("segments must be a non-empty JSON array of objects")
    seen = set()
    directions = set()
    for pos, seg in enumerate(segments, 1):
        where = "segment #%d" % pos
        if not isinstance(seg, dict):
            raise ValueError("%s is not a JSON object" % where)
        seg_id = seg.get("segment_id")
        if not isinstance(seg_id, str) or not seg_id.strip():
            raise ValueError("%s lacks a non-empty string segment_id" % where)
        if seg_id in seen:
            raise ValueError("duplicate segment_id in input: %s" % seg_id)
        seen.add(seg_id)
        source = seg.get("source_text")
        if not isinstance(source, str) or not source:
            raise ValueError(
                "segment %s lacks a string source_text" % seg_id
            )
        tokens = seg.get("protected_tokens")
        if tokens is not None:
            if not isinstance(tokens, list) or not all(
                isinstance(item, str) for item in tokens
            ):
                raise ValueError(
                    "segment %s protected_tokens must be a list of strings"
                    % seg_id
                )
        if need_direction:
            direction = seg.get("direction")
            if direction not in DIRECTIONS:
                raise ValueError(
                    "segment %s lacks direction (%s required here)"
                    % (seg_id, "|".join(DIRECTIONS))
                )
            directions.add(direction)
        if need_policy:
            policy = seg.get("policy_precheck_ref")
            if not isinstance(policy, str) or not policy.strip():
                raise ValueError(
                    "segment %s lacks a non-empty policy_precheck_ref"
                    " (P0 annotation must precede translation)" % seg_id
                )
    if need_direction and len(directions) > 1:
        raise ValueError(
            "mixed directions in one run: %s" % "|".join(sorted(directions))
        )


def build_handoff(segments, direction, prompt_refs=None):
    """Build the emit packet rows (six contract keys, input order).

    Zero side effects; the rows carry no timestamps, so repeated calls on
    the same inputs are byte-identical. prompt_refs maps direction to a
    (ref, template) pair; built-in constants apply when omitted.
    """
    if direction not in DIRECTIONS:
        raise ValueError(
            "unknown direction %r (%s)" % (direction, "|".join(DIRECTIONS))
        )
    check_segments(segments)
    refs = prompt_refs or BUILTIN_PROMPTS
    ref = refs[direction][0]
    rows = []
    for seg in segments:
        rows.append(
            {
                "segment_id": seg["segment_id"],
                "direction": direction,
                "source_text": seg["source_text"],
                "protected_tokens": list(seg.get("protected_tokens") or []),
                "prompt_template_ref": ref,
                "instruction": INSTRUCTIONS[direction],
            }
        )
    return rows


class IngestRejected(Exception):
    """Backfill rejected loud: carries rejections and uncovered segments."""

    def __init__(self, rejections, missing):
        super().__init__(
            "ingest rejected: %d row(s), %d segment(s) without coverage"
            % (len(rejections), len(missing))
        )
        self.rejections = rejections
        self.missing = missing


def ingest_translations(segments, rows, prompt_refs=None):
    """Validate backfill rows and produce (translated, ledger_rows).

    Rejection rules per row (fail loud, each rejection named): the row must
    be an object; segment_id must resolve to an input segment at most once;
    model_id must be a non-empty string (a backfill without it is an
    undisclosed machine-translation attempt); translated_text must be
    non-empty; prompt_template_ref must match the ref in force for the
    segment direction; timestamp_utc must parse as ISO-8601; a declared
    annotation_site must agree with the site derived from model_id
    (the literal "human" annotates site "human", any other model_id
    annotates site "model"). After per-row validation, every input segment
    must carry exactly one accepted row; uncovered segments are reported
    named. Any rejection or gap raises IngestRejected.

    Ledger rows carry exactly the nine annotation keys of SPEC section 5 in
    canonical order: annotation_site as derived above, linkages_run empty
    at P2 (the linkage stage appends), tenpoint_verdict "PENDING",
    timestamp_utc taken from the backfill row (never synthesized).
    """
    check_segments(segments, need_direction=True, need_policy=True)
    refs = prompt_refs or BUILTIN_PROMPTS
    by_id = {}
    for seg in segments:
        by_id[seg["segment_id"]] = seg
    rejections = []
    accepted = {}
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            rejections.append(
                {"row_index": index, "segment_id": None,
                 "reason": "row-not-object"}
            )
            continue
        seg_id = row.get("segment_id")
        if not isinstance(seg_id, str) or not seg_id.strip():
            rejections.append(
                {"row_index": index, "segment_id": None,
                 "reason": "missing-segment-id"}
            )
            continue
        if seg_id not in by_id:
            rejections.append(
                {"row_index": index, "segment_id": seg_id,
                 "reason": "unknown-segment-id"}
            )
            continue
        if seg_id in accepted:
            rejections.append(
                {"row_index": index, "segment_id": seg_id,
                 "reason": "duplicate-segment-id"}
            )
            continue
        model_id = row.get("model_id")
        if not isinstance(model_id, str) or not model_id.strip():
            rejections.append(
                {"row_index": index, "segment_id": seg_id,
                 "reason": "missing-model-id"}
            )
            continue
        body = row.get("translated_text")
        if not isinstance(body, str) or not body.strip():
            rejections.append(
                {"row_index": index, "segment_id": seg_id,
                 "reason": "missing-translated-text"}
            )
            continue
        expected_ref = refs[by_id[seg_id]["direction"]][0]
        if row.get("prompt_template_ref") != expected_ref:
            rejections.append(
                {"row_index": index, "segment_id": seg_id,
                 "reason": "prompt-template-ref-mismatch",
                 "expected": expected_ref,
                 "got": row.get("prompt_template_ref")}
            )
            continue
        stamp = row.get("timestamp_utc")
        if not parse_utc(stamp):
            rejections.append(
                {"row_index": index, "segment_id": seg_id,
                 "reason": "invalid-timestamp"}
            )
            continue
        derived_site = (
            SITE_HUMAN if model_id == HUMAN_MODEL_ID else SITE_MODEL
        )
        declared_site = row.get("annotation_site")
        if declared_site is not None and declared_site != derived_site:
            rejections.append(
                {"row_index": index, "segment_id": seg_id,
                 "reason": "annotation-site-conflict",
                 "derived": derived_site,
                 "declared": declared_site}
            )
            continue
        accepted[seg_id] = row
    missing = [
        seg["segment_id"] for seg in segments if seg["segment_id"] not in accepted
    ]
    if rejections or missing:
        raise IngestRejected(rejections, missing)
    translated = []
    ledger_rows = []
    for seg in segments:
        seg_id = seg["segment_id"]
        row = accepted[seg_id]
        model_id = row["model_id"]
        translated.append(
            {
                "segment_id": seg_id,
                "translated_text": row["translated_text"],
            }
        )
        ledger_rows.append(
            {
                "segment_id": seg_id,
                "direction": seg["direction"],
                "model_id": model_id,
                "annotation_site": (
                    SITE_HUMAN if model_id == HUMAN_MODEL_ID else SITE_MODEL
                ),
                "prompt_template_ref": row["prompt_template_ref"],
                "linkages_run": list(LINKAGES_AT_P2),
                "policy_precheck_ref": seg["policy_precheck_ref"],
                "tenpoint_verdict": VERDICT_PENDING,
                "timestamp_utc": row["timestamp_utc"],
            }
        )
    return translated, ledger_rows


def protected_token_findings(segments, translated):
    """Report protected tokens absent from a delivered translation.

    Early pointer only; the pipeline linkage stage owns the preservation
    diff gate. Findings never alter the exit code here.
    """
    body_by_id = {}
    for item in translated:
        body_by_id[item["segment_id"]] = item.get("translated_text", "")
    findings = []
    for seg in segments:
        body = body_by_id.get(seg["segment_id"])
        if body is None:
            continue
        for token in seg.get("protected_tokens") or []:
            if token not in body:
                findings.append(
                    {
                        "segment_id": seg["segment_id"],
                        "token": token,
                        "finding": "protected-token-absent",
                    }
                )
    return findings


# ---------------------------------------------------------------------------
# http provider (default-deny; the only network face of this module)
# ---------------------------------------------------------------------------


def check_net_env(environ):
    """Return a refusal message, or None when the gate is fully open.

    Default deny: the gate variable must equal "1" and every provider
    variable must be set non-empty; the refusal names the gate or the
    missing variable(s).
    """
    if environ.get(NET_GATE_ENV) != "1":
        return (
            "network gate %s is not set to 1 (default deny)" % NET_GATE_ENV
        )
    missing = [
        name
        for name in NET_CONFIG_ENVS
        if not str(environ.get(name) or "").strip()
    ]
    if missing:
        return "missing environment variable(s): " + ", ".join(missing)
    return None


def parse_chat_response(payload_text):
    """Parse an OpenAI-compatible chat completion body.

    Returns (content, None) on success or (None, named-error).
    """
    try:
        data = json.loads(payload_text)
    except ValueError as exc:
        return None, "invalid-json-response (%s)" % exc
    if not isinstance(data, dict):
        return None, "response-root-not-object"
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return None, "response-has-no-choices"
    first = choices[0]
    message = first.get("message") if isinstance(first, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        return None, "response-has-empty-content"
    return content, None


def http_translate_segment(endpoint, model_name, api_key, prompt_text, timeout_s):
    """One chat/completions POST; returns (content, error, http_status).

    The api_key travels in the Authorization header only; it never enters
    error strings, ledger lines, or reports.
    """
    url = endpoint.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt_text}],
            "temperature": 0,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            status = getattr(response, "status", None)
            payload = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return None, "http-error-%d" % exc.code, exc.code
    except (urllib.error.URLError, OSError) as exc:
        return None, "network-error (%s)" % exc.__class__.__name__, None
    content, error = parse_chat_response(payload)
    if error is not None:
        return None, error, status
    return content, None, status


def append_netred(path, entry):
    """Append one NETRED ledger line (JSONL); failures included."""
    try:
        with io.open(path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        die("netred ledger not writable: %s (%s)" % (path, exc), 9)


# ---------------------------------------------------------------------------
# selftest (fully offline)
# ---------------------------------------------------------------------------

PROBE_TS_FORMAT = "%04d-%02d-%02dT%02d:%02d:%02dZ"
PROBE_TS = PROBE_TS_FORMAT % (1970, 1, 1, 0, 0, 0)


def _probe_segments():
    return [
        {
            "segment_id": "s0001",
            "source_text": "first probe segment body",
            "protected_tokens": ["norm_lint"],
            "direction": "zh2en",
            "policy_precheck_ref": "P0-probe",
        },
        {
            "segment_id": "s0002",
            "source_text": "second probe segment body",
            "protected_tokens": [],
            "direction": "zh2en",
            "policy_precheck_ref": "P0-probe",
        },
    ]


def _probe_backfill(translated_map, model_id="probe-model", site=None):
    rows = []
    for seg_id in sorted(translated_map):
        row = {
            "segment_id": seg_id,
            "translated_text": translated_map[seg_id],
            "model_id": model_id,
            "prompt_template_ref": BUILTIN_PROMPTS["zh2en"][0],
            "timestamp_utc": PROBE_TS,
        }
        if site is not None:
            row["annotation_site"] = site
        rows.append(row)
    return rows


def run_selftest(out):
    """Offline probes over the pure faces and the refusal branches."""
    problems = []

    def check(name, condition, detail=""):
        if condition:
            out.write("SELFTEST PASS %s\n" % name)
        else:
            problems.append(name)
            out.write("SELFTEST FAIL %s %s\n" % (name, detail))

    check(
        "constants",
        DIRECTIONS == ("zh2en", "en2zh")
        and len(ANNOTATION_KEYS) == 9
        and len(EMIT_KEYS) == 6
        and len(BACKFILL_KEYS) == 5,
    )
    check(
        "net-gate-names",
        NET_GATE_ENV == "ROCQWASH_MCP_ALLOW_NET"
        and NET_CONFIG_ENVS
        == (
            "ROCQWASH_LLM_ENDPOINT",
            "ROCQWASH_LLM_MODEL",
            "ROCQWASH_LLM_KEY",
        ),
    )

    segments = _probe_segments()
    rows = build_handoff(segments, "zh2en")
    check(
        "emit-row-shape",
        len(rows) == 2
        and all(list(row.keys()) == list(EMIT_KEYS) for row in rows)
        and rows[0]["prompt_template_ref"] == "prompts/zh2en-repo-v1"
        and rows[0]["protected_tokens"] == ["norm_lint"]
        and bool(rows[0]["instruction"]),
    )
    check(
        "emit-idempotent",
        json.dumps(build_handoff(segments, "zh2en"), ensure_ascii=False)
        == json.dumps(rows, ensure_ascii=False),
    )

    backfill = _probe_backfill(
        {"s0001": "first probe rendered body", "s0002": "second body"}
    )
    translated, ledger = ingest_translations(segments, backfill)
    check(
        "ledger-nine-keys",
        len(ledger) == 2
        and all(
            list(row.keys()) == list(ANNOTATION_KEYS) for row in ledger
        )
        and all(row["annotation_site"] == SITE_MODEL for row in ledger)
        and all(row["tenpoint_verdict"] == VERDICT_PENDING for row in ledger)
        and all(row["linkages_run"] == [] for row in ledger)
        and all(row["timestamp_utc"] == PROBE_TS for row in ledger),
    )
    check(
        "translated-passthrough",
        translated[0]["segment_id"] == "s0001"
        and translated[0]["translated_text"] == "first probe rendered body",
    )

    human_rows = _probe_backfill(
        {"s0001": "one", "s0002": "two"}, model_id=HUMAN_MODEL_ID
    )
    _, human_ledger = ingest_translations(segments, human_rows)
    check(
        "human-site",
        all(row["annotation_site"] == SITE_HUMAN for row in human_ledger)
        and all(row["model_id"] == HUMAN_MODEL_ID for row in human_ledger),
    )

    def rejects(mutate, reason):
        rows_for_probe = _probe_backfill(
            {"s0001": "one", "s0002": "two"}
        )
        mutate(rows_for_probe)
        try:
            ingest_translations(segments, rows_for_probe)
        except IngestRejected as exc:
            got = [item["reason"] for item in exc.rejections]
            return reason in got
        return False

    check(
        "reject-missing-model-id",
        rejects(lambda rs: rs[0].pop("model_id"), "missing-model-id"),
    )
    check(
        "reject-empty-translation",
        rejects(lambda rs: rs[0].__setitem__("translated_text", "  "),
                "missing-translated-text"),
    )
    check(
        "reject-ref-mismatch",
        rejects(
            lambda rs: rs[0].__setitem__("prompt_template_ref", "other"),
            "prompt-template-ref-mismatch",
        ),
    )
    check(
        "reject-invalid-timestamp",
        rejects(
            lambda rs: rs[0].__setitem__("timestamp_utc", "not-a-timestamp"),
            "invalid-timestamp",
        ),
    )
    check(
        "reject-unknown-segment",
        rejects(lambda rs: rs[0].__setitem__("segment_id", "s0099"),
                "unknown-segment-id"),
    )

    def duplicate_rows():
        base = _probe_backfill({"s0001": "one", "s0002": "two"})
        return [base[0], base[0], base[1]]

    try:
        ingest_translations(segments, duplicate_rows())
        dup_ok = False
    except IngestRejected as exc:
        dup_ok = any(
            item["reason"] == "duplicate-segment-id"
            for item in exc.rejections
        )
    check("reject-duplicate-segment", dup_ok)

    check(
        "reject-site-conflict",
        rejects(
            lambda rs: rs[0].__setitem__("annotation_site", SITE_MODEL),
            "annotation-site-conflict",
        )
        or rejects(
            lambda rs: rs[0].__setitem__("annotation_site", "other"),
            "annotation-site-conflict",
        ),
    )

    check(
        "reject-non-object-row",
        rejects(lambda rs: rs.__setitem__(0, 42), "row-not-object"),
    )

    partial = _probe_backfill({"s0001": "one"})
    try:
        ingest_translations(segments, partial)
        coverage_ok = False
    except IngestRejected as exc:
        coverage_ok = exc.missing == ["s0002"] and not exc.rejections
    check("reject-incomplete-coverage", coverage_ok)

    no_policy = [
        {"segment_id": "s0001", "source_text": "body", "direction": "zh2en"},
    ]
    try:
        build_handoff(no_policy, "zh2en")
        build_ok = True
    except ValueError:
        build_ok = False
    policy_ok = False
    if build_ok:
        try:
            ingest_translations(no_policy, [])
        except ValueError as exc:
            policy_ok = "policy_precheck_ref" in str(exc)
        except IngestRejected:
            policy_ok = False
    check("reject-missing-policy-ref", build_ok and policy_ok)

    content, error = parse_chat_response(
        '{"choices": [{"message": {"content": "rendered body"}}]}'
    )
    check("parse-response-ok", content == "rendered body" and error is None)
    content_bad, error_bad = parse_chat_response("{}")
    check(
        "parse-response-error",
        content_bad is None and error_bad == "response-has-no-choices",
    )

    check(
        "default-deny-gate",
        check_net_env({}) == (
            "network gate ROCQWASH_MCP_ALLOW_NET is not set to 1"
            " (default deny)"
        ),
    )
    refusal_config = check_net_env({NET_GATE_ENV: "1"})
    check(
        "default-deny-config-named",
        refusal_config is not None
        and "ROCQWASH_LLM_ENDPOINT" in refusal_config
        and "ROCQWASH_LLM_MODEL" in refusal_config
        and "ROCQWASH_LLM_KEY" in refusal_config,
    )
    check("net-env-open", check_net_env(
        {
            NET_GATE_ENV: "1",
            "ROCQWASH_LLM_ENDPOINT": "https://example.test/v1",
            "ROCQWASH_LLM_MODEL": "probe-model",
            "ROCQWASH_LLM_KEY": "probe-key",
        }
    ) is None)

    findings = protected_token_findings(
        segments,
        [
            {"segment_id": "s0001", "translated_text": "body without it"},
            {"segment_id": "s0002", "translated_text": "other"},
        ],
    )
    check(
        "token-findings",
        len(findings) == 1
        and findings[0]["segment_id"] == "s0001"
        and findings[0]["token"] == "norm_lint",
    )

    check("timestamp-parse-ok", parse_utc(PROBE_TS))
    check("timestamp-parse-bad", not parse_utc("13/45/2000"))

    if problems:
        out.write(
            "SELFTEST RESULT RED (%d failed check(s))\n" % len(problems)
        )
        return 1
    out.write("SELFTEST RESULT GREEN (all checks passed, zero network)\n")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _stamp_cli_fields(segments, direction, policy_ref):
    """Return flag-stamped copies; conflicts between flag and file exit 2."""
    working = []
    for seg in segments:
        item = dict(seg)
        seg_id = item.get("segment_id", "?")
        carried = item.get("direction")
        if carried is not None and carried != direction:
            die(
                "segment %s carries direction %s conflicting with"
                " --direction %s" % (seg_id, carried, direction),
                2,
            )
        item["direction"] = direction
        if policy_ref:
            carried_policy = item.get("policy_precheck_ref")
            if (
                carried_policy not in (None, "")
                and carried_policy != policy_ref
            ):
                die(
                    "segment %s carries policy_precheck_ref %r conflicting"
                    " with --policy-ref %r"
                    % (seg_id, carried_policy, policy_ref),
                    2,
                )
            item["policy_precheck_ref"] = policy_ref
        working.append(item)
    return working


def run_emit(args):
    ref, _template = resolve_prompt(args.prompts, args.direction)
    rows = build_handoff(
        args._segments,
        args.direction,
        prompt_refs={args.direction: (ref, _template)},
    )
    write_jsonl(args.emit, rows)
    report = {
        "schema": SCHEMA_REPORT,
        "mode": "emit",
        "direction": args.direction,
        "provider": "handoff",
        "segments": len(rows),
        "prompt_template_ref": ref,
        "emit_out": args.emit,
    }
    sys.stdout.write(
        "EMIT segments=%d direction=%s prompt_template_ref=%s out=%s\n"
        % (len(rows), args.direction, ref, args.emit)
    )
    if args.json:
        report["exit"] = 0
        write_json(args.json, report)
    return 0


# contract key behind each key-missing reason code; the refusal line
# names it so the gap is readable in the ledger key vocabulary
REJECT_REASON_KEYS = {
    "missing-segment-id": "segment_id",
    "missing-model-id": "model_id",
    "missing-translated-text": "translated_text",
    "prompt-template-ref-mismatch": "prompt_template_ref",
    "invalid-timestamp": "timestamp_utc",
    "annotation-site-conflict": "annotation_site",
}


def run_ingest(args):
    rows = load_backfill_rows(args.ingest)
    ref, _template = resolve_prompt(args.prompts, args.direction)
    prompt_refs = {args.direction: (ref, _template)}
    try:
        translated, ledger = ingest_translations(
            args._segments, rows, prompt_refs=prompt_refs
        )
    except ValueError as exc:
        die("segments invalid for ingest: %s" % exc, 1)
    except IngestRejected as exc:
        for item in exc.rejections:
            key_name = REJECT_REASON_KEYS.get(item["reason"])
            sys.stderr.write(
                "%s: REJECT row %s segment %s reason %s%s%s\n"
                % (
                    TOOL,
                    item.get("row_index"),
                    item.get("segment_id"),
                    item["reason"],
                    " (key %s)" % key_name if key_name else "",
                    ""
                    if "expected" not in item
                    else " (expected %r got %r)"
                    % (item["expected"], item["got"]),
                )
            )
        for seg_id in exc.missing:
            sys.stderr.write(
                "%s: NO-COVERAGE segment %s (backfill carries no row for"
                " it)\n" % (TOOL, seg_id)
            )
        if args.json:
            write_json(
                args.json,
                {
                    "schema": SCHEMA_REPORT,
                    "mode": "ingest",
                    "direction": args.direction,
                    "provider": "handoff",
                    "accepted": 0,
                    "rejections": exc.rejections,
                    "missing": exc.missing,
                    "exit": 1,
                },
            )
        return 1
    findings = protected_token_findings(args._segments, translated)
    for item in findings:
        sys.stdout.write(
            "WARN segment %s: protected token %r absent from the delivered"
            " translation\n" % (item["segment_id"], item["token"])
        )
    if args.translated_out:
        write_json(args.translated_out, translated)
    if args.ledger_out:
        write_jsonl(args.ledger_out, ledger)
    report = {
        "schema": SCHEMA_REPORT,
        "mode": "ingest",
        "direction": args.direction,
        "provider": "handoff",
        "accepted": len(translated),
        "rejections": [],
        "missing": [],
        "protected_token_findings": len(findings),
        "prompt_template_ref": ref,
        "translated_out": args.translated_out,
        "ledger_out": args.ledger_out,
    }
    sys.stdout.write(
        "INGEST accepted=%d ledger_rows=%d findings=%d prompt_template_ref=%s\n"
        % (len(translated), len(ledger), len(findings), ref)
    )
    if args.json:
        report["exit"] = 0
        write_json(args.json, report)
    return 0


def run_http(args):
    refusal = check_net_env(os.environ)
    if refusal is not None:
        die("http provider refused: %s" % refusal, 2)
    if not args.netred_ledger:
        die("--netred-ledger <p> is required for the http provider", 2)
    if args.timeout <= 0:
        die("--timeout must be a positive integer", 2)
    endpoint = os.environ["ROCQWASH_LLM_ENDPOINT"]
    model_name = os.environ["ROCQWASH_LLM_MODEL"]
    api_key = os.environ["ROCQWASH_LLM_KEY"]
    try:
        check_segments(
            args._segments, need_direction=True, need_policy=True
        )
    except ValueError as exc:
        die("segments invalid for http translate: %s" % exc, 1)
    ref, template = resolve_prompt(args.prompts, args.direction)
    translated = []
    ledger_rows = []
    failures = []
    netred_lines = 0
    for seg in args._segments:
        prompt_text = render_prompt(
            template, seg["source_text"], seg.get("protected_tokens") or []
        )
        stamp = utc_now()
        content, error, status = http_translate_segment(
            endpoint, model_name, api_key, prompt_text, args.timeout
        )
        verdict = "ok" if error is None else "failed"
        append_netred(
            args.netred_ledger,
            {
                "time_utc": stamp,
                "url": endpoint.rstrip("/") + "/chat/completions",
                "segment_id": seg["segment_id"],
                "verdict": verdict,
                "http_status": status,
                "error": error,
            },
        )
        netred_lines += 1
        if error is not None:
            failures.append(
                {"segment_id": seg["segment_id"], "error": error}
            )
            sys.stdout.write(
                "HTTP segment %s verdict failed (error %s)\n"
                % (seg["segment_id"], error)
            )
            continue
        translated.append(
            {
                "segment_id": seg["segment_id"],
                "translated_text": content,
            }
        )
        ledger_rows.append(
            {
                "segment_id": seg["segment_id"],
                "direction": args.direction,
                "model_id": model_name,
                "annotation_site": SITE_MODEL,
                "prompt_template_ref": ref,
                "linkages_run": list(LINKAGES_AT_P2),
                "policy_precheck_ref": seg["policy_precheck_ref"],
                "tenpoint_verdict": VERDICT_PENDING,
                "timestamp_utc": stamp,
            }
        )
        sys.stdout.write(
            "HTTP segment %s verdict ok (http_status %s)\n"
            % (seg["segment_id"], status)
        )
    if args.translated_out:
        write_json(args.translated_out, translated)
    if args.ledger_out:
        write_jsonl(args.ledger_out, ledger_rows)
    sys.stdout.write(
        "HTTP translated=%d failed=%d netred_lines=%d ledger=%s\n"
        % (len(translated), len(failures), netred_lines, args.netred_ledger)
    )
    report = {
        "schema": SCHEMA_REPORT,
        "mode": "translate-http",
        "direction": args.direction,
        "provider": "http",
        "model_id": model_name,
        "prompt_template_ref": ref,
        "translated": len(translated),
        "failed": len(failures),
        "failures": failures,
        "netred_ledger": args.netred_ledger,
        "netred_lines": netred_lines,
        "translated_out": args.translated_out,
        "ledger_out": args.ledger_out,
        "exit": 1 if failures else 0,
    }
    if args.json:
        write_json(args.json, report)
    return 1 if failures else 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog=TOOL,
        description=(
            "E4 P2 model-site translation stage: handoff loop by default"
            " (zero network), optional gated http provider; per-segment"
            " annotation mandatory."
        ),
    )
    parser.add_argument(
        "--segments",
        help="segments JSON file (array, or object with a segments key)",
    )
    parser.add_argument(
        "--direction", choices=list(DIRECTIONS), help="translation direction"
    )
    parser.add_argument(
        "--emit",
        help="write the handoff packet as JSONL to this path (zero network)",
    )
    parser.add_argument(
        "--ingest",
        help="validate a backfill JSONL file at this path (zero network)",
    )
    parser.add_argument(
        "--provider",
        choices=list(PROVIDERS),
        default="handoff",
        help="handoff (default, zero network) or http (default-deny gate)",
    )
    parser.add_argument(
        "--prompts",
        help="prompt template dir with <direction>*.txt/.md files"
             " (default: built-in constants)",
    )
    parser.add_argument(
        "--policy-ref",
        help="P0 policy pre-check pointer stamped into ingest/http rows",
    )
    parser.add_argument(
        "--translated-out", help="write translated segments JSON here"
    )
    parser.add_argument(
        "--ledger-out", help="write the segment ledger rows JSONL here"
    )
    parser.add_argument(
        "--netred-ledger",
        help="NETRED ledger JSONL path (required for the http provider)",
    )
    parser.add_argument(
        "--json", help="write a run report JSON at this path"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="per-call http timeout in seconds (default 60)",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="run the offline selftest and exit",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        return run_selftest(sys.stdout)

    actions = []
    if args.emit:
        actions.append("emit")
    if args.ingest:
        actions.append("ingest")
    if args.provider == "http":
        actions.append("http")
    if not actions:
        die(
            "no action requested: give --emit, --ingest, --provider http,"
            " or --selftest",
            2,
        )
    if len(actions) > 1 or (args.provider == "http" and (args.emit or args.ingest)):
        die(
            "actions %s conflict: choose one of --emit, --ingest,"
            " --provider http" % "+".join(actions),
            2,
        )
    if not args.segments:
        die("--segments <json> is required", 2)
    if not args.direction:
        die("--direction zh2en|en2zh is required", 2)

    raw_segments = load_segments(args.segments)
    try:
        check_segments(raw_segments)
    except ValueError as exc:
        die("segments invalid: %s" % exc, 1)
    args._segments = _stamp_cli_fields(
        raw_segments, args.direction, args.policy_ref
    )
    if actions[0] == "emit":
        return run_emit(args)
    if actions[0] == "ingest":
        return run_ingest(args)
    return run_http(args)


if __name__ == "__main__":
    sys.exit(main())
