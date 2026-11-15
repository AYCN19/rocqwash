"""row_render.py - refinery W2 row renderer: gap-cluster ledger to candidate
taxonomy rows through the E4 P2 handoff form.

Purpose. Render a gap-cluster ledger (the W1 face) into candidate taxonomy
rows for docs/drafts/taxonomy-candidates.json: emit a render packet, an
external model-side agent backfills one candidate row per gap, and ingest
admits every row only when the vacgen admission gate (validate_row, C3.4)
passes; the form is the verified i18n_translate shape (zero-network
emit/ingest, an optional http provider behind the default-deny gate with
one NETRED line per call, nine-key ledger rows, the i18n_verify ten-point
human gate).
Interface. Pure functions: load_gaps(path) -> gaps; check_gaps(gaps) -> None;
build_handoff(gaps, prompt_refs=None) -> packet rows; ingest_rows(gaps,
rows, vacgen=None, prompt_refs=None) -> (candidate_rows, ledger_rows);
check_net_env(environ) -> refusal-or-None; emit_tenpoint(draft) -> form;
tenpoint_problems(verdicts, draft) -> (problems, frame).  CLI: --gaps plus
one of --emit, --ingest, --check-draft, --emit-tenpoint, --ingest-tenpoint
(with --draft-out), or --provider http (with --netred-ledger); shared:
--vacgen, --prompts, --policy-ref, --ledger-out, --json, --timeout.
Dependencies. Python 3 standard library only (argparse, datetime,
importlib.util, io, json, os, re, sys, tempfile, urllib); the admission
gate and the provider/tenpoint faces load dynamically from the sibling
tools/vacgen.py, tools/i18n_translate.py and tools/i18n_verify.py.
Evidence. Contract segment tests/refinery_segments/render.py; the C3.4
admission table in tools/vacgen.py; the E4 P2 emit/ingest contract rows.
Exit-codes. 0 success; 1 data verdict red (rejections, incomplete gap
coverage, admission failures, invalid draft rows); 2 usage or environment
refusal (each named on stderr); 9 input or output file unreadable.
"""
# Extended contract (kept outside the five-field block per the annotation
# standard 30-line header budget).
# Host loading.  The renderer never re-implements row judgment: admission is
# delegated to the loaded vacgen host's validate_row (C3.4), flag decoding to
# its ROW_FLAG_MAP/flags_int, and the target enum to its MATCH_TARGETS.  The
# http provider reuses the i18n host's check_net_env (default deny:
# ROCQWASH_MCP_ALLOW_NET=1 plus ROCQWASH_LLM_ENDPOINT / ROCQWASH_LLM_MODEL /
# ROCQWASH_LLM_KEY all set), its chat/completions POST face, its response
# parser and its NETRED ledger append; credentials never enter packets,
# ledger rows, reports or log lines.  The ten-point face reuses the verify
# host's schemas, verdict vocabulary and validate_verdicts; the renderer
# only supplies the ten row-review point texts and writes the verdict frame
# back into the draft rows.  The engine never judges.
# Renderer-side row contract (distinct from admission).  A backfill row
# payload must carry schemaVersion (2) and the thirteen rendered fields
# (familyId, cluster, match, priority, confidence, witnessStrategy,
# witnessTemplate, mathlibAnchors, refutationForms, boundaryApplicability,
# gapKeywords, notes), keep refutationForms inside the W6 vocabulary, and
# match at least one sample face of its source gap when the gap declares
# sample faces (the trace check).  Rejections are named row by row; any
# rejection or uncovered gap aborts the draft write (fail loud, no partial
# draft).
# Draft shape.  {"schema": "rocqwash.taxonomy-candidates/1", "rows": [...],
# "provenance": {...}, "admission": {...}}.  Each admitted row carries its
# provenance (sourceGapId, sourceLane "row-render-handoff") and a flat
# tenpointVerdict field that starts "PENDING" and is rewritten by the
# ten-point ingest to the verdict frame.  The draft carries no synthesized
# timestamps; ledger rows take timestampUtc from their backfill rows.
# Negative finding.  The draft's provenance block carries the four-element
# negative-finding boundary (scannedWhat / notScanned / nonAbsoluteClaim /
# aliasesNotExhausted plus a rescanCondition), so the candidate set is
# always scoped to its source-ledger scan face.
# Determinism.  build_handoff is side-effect free and byte-stable on equal
# inputs (no timestamps in packet rows); ingest output depends only on the
# inputs and the loaded host faces.  Re-render with the same ledger and the
# same backfill reproduces the draft bytes.

import argparse
import datetime
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request

TOOL = "row_render.py"
SCHEMA_REPORT = "rocqwash.rowrender.report/1"
DRAFT_SCHEMA = "rocqwash.taxonomy-candidates/1"
GAP_LEDGER_SCHEMA = "rocqwash.gap-ledger/1"

# Nine render-ledger annotation keys, canonical order; role-for-role reuse of
# the E4 P2 nine-key segment annotation (SPEC section 5 form).
ANNOTATION_KEYS = (
    "gapId",
    "renderAction",
    "modelId",
    "annotationSite",
    "promptTemplateRef",
    "linkagesRun",
    "policyPrecheckRef",
    "tenpointVerdict",
    "timestampUtc",
)

# Emit packet row keys per the render contract (seven keys, exactly).
EMIT_KEYS = (
    "gapId",
    "cluster",
    "sampleFaces",
    "keywords",
    "occurrences",
    "promptTemplateRef",
    "instruction",
)

# Backfill row keys per the render contract (five keys, exactly).
BACKFILL_KEYS = (
    "gapId",
    "row",
    "modelId",
    "promptTemplateRef",
    "timestampUtc",
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
LINKAGES_AT_RENDER = []

# W6 vocabulary (order refinement 3): the strength word pair this renderer
# activates on every rendered row; admission stays owned by the vacgen gate.
W6_REFUTATION_FORMS = ("full", "point", "tactics", "noclassic", "band")

ROW_SCHEMA_VERSION = 2

# The thirteen rendered fields (the full row face of lane W2), plus
# schemaVersion; semantic admission checks stay with the vacgen host (C3.4).
RENDER_ROW_FIELDS = (
    "schemaVersion",
    "familyId",
    "cluster",
    "match",
    "priority",
    "confidence",
    "witnessStrategy",
    "witnessTemplate",
    "mathlibAnchors",
    "refutationForms",
    "boundaryApplicability",
    "gapKeywords",
    "notes",
)

GAP_STATUSES = ("open", "clustered", "rendered", "void")

PROVIDERS = ("handoff", "http")

# Built-in render prompt. The named ref follows the contract naming form
# "prompts/render-row-v1". The template carries the gap-field placeholders
# and instructs the model-side agent to return one JSON row object.
BUILTIN_TEMPLATE_RENDER = (
    "Cast one candidate taxonomy row for the vacuity-refinery engine, as a\n"
    "single JSON object.\n"
    "Rules:\n"
    "1. Output only the JSON object; no commentary, headings, or fences.\n"
    "2. The object carries exactly these fields: schemaVersion (the integer\n"
    "   2), familyId, cluster, match (object with target, regex, flags),\n"
    "   priority (integer), confidence (HIGH or MID), witnessStrategy,\n"
    "   witnessTemplate, mathlibAnchors (non-empty list of objects with\n"
    "   symbol, relPath, line), refutationForms, boundaryApplicability,\n"
    "   gapKeywords, notes.\n"
    "3. match.target is one of: assumption.type, assumption.name,\n"
    "   instance.type, conclusion, file.text. The regex must compile under\n"
    "   Python re with flags '' or one of I/M/S (or their long names).\n"
    "4. refutationForms is a non-empty list drawn from the vocabulary:\n"
    "   full, point, tactics, noclassic, band.\n"
    "5. gapKeywords come from the gap entry below, verbatim when present.\n"
    "6. mathlibAnchors name declarations in a pinned mathlib snapshot; the\n"
    "   line numbers are candidate pins that the C3.3 anchor gate verifies\n"
    "   later; never state a pin you cannot name.\n"
    "7. Write in plain declarative English at the register a mathlib review\n"
    "   would accept; no marketing wording.\n"
    "\n"
    "Gap entry:\n"
    "cluster: {cluster}\n"
    "occurrences: {occurrences}\n"
    "sample faces:\n{sample_faces}\n"
    "keywords: {keywords}\n"
)
BUILTIN_PROMPT_RENDER = ("prompts/render-row-v1", BUILTIN_TEMPLATE_RENDER)

INSTRUCTION_RENDER = (
    "Cast one candidate taxonomy row for this gap entry. Return only the"
    " JSON row object with the full field set; the regex must compile and"
    " keep the mathlib review register."
)

# Ten-point review face for a candidate-row draft (the manual first-admission
# gate of the layer law: the engine emits the form and ingests verdicts,
# never judges).
TENPOINT_INTRO_RENDER = (
    "Ten-point first-admission review on the candidate-row face: one verdict"
    " and one source-line citation per point."
)
TENPOINT_ROW_POINTS = (
    "1. familyId names the premise family it renders and does not collide"
    " with a landed familyId in the active taxonomy.",
    "2. match.target is the correct lookup face (assumption.type,"
    " assumption.name, instance.type, conclusion, file.text) for the gap's"
    " evidence.",
    "3. match.regex compiles and matches at least one sample face of the"
    " source gap.",
    "4. priority and confidence are honest: priority orders the family"
    " against landed rows, and confidence states HIGH only for"
    " v1-transcription-grade evidence.",
    "5. witnessStrategy states the mathematical attack in one or two"
    " sentences a mathlib reviewer would accept.",
    "6. witnessTemplate bites are well-formed statement templates using only"
    " declared placeholders.",
    "7. mathlibAnchors carry symbol, relPath and line; pins declare their"
    " status and face the C3.3 anchor gate.",
    "8. refutationForms stay inside the W6 vocabulary (full, point, tactics,"
    " noclassic, band).",
    "9. boundaryApplicability names the boundary class the row applies to,"
    " or declares none.",
    "10. gapKeywords trace verbatim to the source gap ledger entry, and"
    " notes carry provenance without process narrative.",
)


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
# host loading (the renderer delegates, never re-implements)
# ---------------------------------------------------------------------------


class HostBroken(Exception):
    """A host module is absent or unusable; the caller turns this into a
    loud failure naming the path and the missing face."""


def resolve_host_path(explicit, env_name, sibling_name):
    """Resolution chain: explicit argument, then the named environment
    variable, then the sibling file next to this tool."""
    if explicit:
        return explicit, "--vacgen flag"
    env = os.environ.get(env_name) if env_name else None
    if env:
        return env, "%s env" % env_name
    sibling = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), sibling_name
    )
    return sibling, "sibling default"


def load_module_from_path(tag, path, required_faces):
    """Load one host module from a file path; absent file or a missing face
    raises HostBroken with the path and the face named."""
    if not os.path.isfile(path):
        raise HostBroken("host module not found: %s (%s)" % (path, tag))
    spec = importlib.util.spec_from_file_location(tag, path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise HostBroken(
            "host module %s failed at import: %r" % (path, exc)
        )
    for face in required_faces:
        if not hasattr(module, face):
            raise HostBroken(
                "host module %s lacks the %s face" % (path, face)
            )
    return module


def load_vacgen_host(explicit=None):
    """Load the admission host (tools/vacgen.py) and require the C3.4
    admission faces; returns the module."""
    path, origin = resolve_host_path(
        explicit, "ROW_RENDER_VACGEN", "vacgen.py"
    )
    module = load_module_from_path(
        "rqw_rowrender_vacgen",
        path,
        ("validate_row", "MATCH_TARGETS", "ROW_FLAG_MAP", "flags_int"),
    )
    module._rowrender_origin = origin
    return module


def load_i18n_host():
    """Load the provider host (tools/i18n_translate.py) for the verified
    network-gate, POST, response-parse and NETRED-append faces."""
    path, _origin = resolve_host_path(None, None, "i18n_translate.py")
    return load_module_from_path(
        "rqw_rowrender_i18n",
        path,
        (
            "check_net_env",
            "parse_chat_response",
            "http_translate_segment",
            "append_netred",
        ),
    )


def load_verify_host():
    """Load the ten-point host (tools/i18n_verify.py) for the verdict
    schemas, the verdict vocabulary and validate_verdicts."""
    path, _origin = resolve_host_path(
        None, "ROW_RENDER_VERIFY", "i18n_verify.py"
    )
    return load_module_from_path(
        "rqw_rowrender_verify",
        path,
        (
            "FORM_SCHEMA",
            "VERDICT_SCHEMA",
            "VERDICT_VALUES",
            "FRAME_VALUES",
            "POINT_COUNT",
            "validate_verdicts",
        ),
    )


def check_net_env(environ):
    """Default-deny network gate, re-exported through the i18n host."""
    return load_i18n_host().check_net_env(environ)


def host_path_of(module):
    """Best-effort absolute path of a loaded host module."""
    path = getattr(module, "__file__", None)
    return os.path.abspath(path) if path else "loaded"


# ---------------------------------------------------------------------------
# input and output helpers
# ---------------------------------------------------------------------------


def read_text(path, what):
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        die("%s file unreadable: %s (%s)" % (what, path, exc), 9)


def load_json_file(path, what):
    raw = read_text(path, what)
    try:
        return json.loads(raw)
    except ValueError as exc:
        die("%s file is not valid JSON: %s (%s)" % (what, path, exc), 1)


def load_jsonl(path, what):
    raw = read_text(path, what)
    rows = []
    for lineno, line in enumerate(raw.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except ValueError as exc:
            die(
                "%s line %d is not valid JSON: %s (%s)"
                % (what, lineno, path, exc),
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


# ---------------------------------------------------------------------------
# gap ledger (the W1 face this renderer consumes)
# ---------------------------------------------------------------------------


def check_gaps(gaps, need_policy=False):
    """Validate the gap list shape; raise ValueError naming the defect.

    Required per gap: non-empty string gapId (unique across the list) and
    non-empty string cluster. Optional: occurrences (positive integer),
    files / sampleFaces / keywords (lists of strings), status (one of
    open/clustered/rendered/void), notes, policyPrecheckRef. Ingest
    additionally requires a non-empty policyPrecheckRef per gap (the
    layer-law first-admission reference precedes rendering).
    """
    if not isinstance(gaps, list) or not gaps:
        raise ValueError("gaps must be a non-empty JSON array of objects")
    seen = set()
    for pos, gap in enumerate(gaps, 1):
        where = "gap #%d" % pos
        if not isinstance(gap, dict):
            raise ValueError("%s is not a JSON object" % where)
        gap_id = gap.get("gapId")
        if not isinstance(gap_id, str) or not gap_id.strip():
            raise ValueError("%s lacks a non-empty string gapId" % where)
        if gap_id in seen:
            raise ValueError("duplicate gapId in input: %s" % gap_id)
        seen.add(gap_id)
        cluster = gap.get("cluster")
        if not isinstance(cluster, str) or not cluster.strip():
            raise ValueError(
                "gap %s lacks a non-empty string cluster" % gap_id
            )
        occurrences = gap.get("occurrences")
        if occurrences is not None and (
            not isinstance(occurrences, int)
            or isinstance(occurrences, bool)
            or occurrences < 1
        ):
            raise ValueError(
                "gap %s occurrences must be a positive integer" % gap_id
            )
        for field in ("files", "sampleFaces", "keywords"):
            value = gap.get(field)
            if value is not None and (
                not isinstance(value, list)
                or not all(isinstance(item, str) for item in value)
            ):
                raise ValueError(
                    "gap %s %s must be a list of strings" % (gap_id, field)
                )
        status = gap.get("status")
        if status is not None and status not in GAP_STATUSES:
            raise ValueError(
                "gap %s status %r outside %s"
                % (gap_id, status, "/".join(GAP_STATUSES))
            )
        notes = gap.get("notes")
        if notes is not None and not isinstance(notes, str):
            raise ValueError("gap %s notes must be a string" % gap_id)
        if need_policy:
            policy = gap.get("policyPrecheckRef")
            if not isinstance(policy, str) or not policy.strip():
                raise ValueError(
                    "gap %s lacks a non-empty policyPrecheckRef (the"
                    " layer-law first-admission reference must precede"
                    " rendering)" % gap_id
                )


def load_gaps(path):
    """Read a gap ledger JSON file (array, or object with a gaps key; a
    schema field must name rocqwash.gap-ledger/1 when present)."""
    data = load_json_file(path, "gap ledger")
    if isinstance(data, dict):
        schema = data.get("schema")
        if schema is not None and schema != GAP_LEDGER_SCHEMA:
            die(
                "gap ledger schema %r instead of %s"
                % (schema, GAP_LEDGER_SCHEMA),
                1,
            )
        data = data.get("gaps")
    return data


def render_prompt(template, gap):
    """Fill the template placeholders from one gap; unknown placeholders
    fail loud."""
    faces = gap.get("sampleFaces") or []
    face_text = "\n".join(faces) if faces else "(none)"
    keywords = gap.get("keywords") or []
    keyword_text = ", ".join(keywords) if keywords else "(none)"
    occurrences = gap.get("occurrences")
    fields = {
        "cluster": gap["cluster"],
        "occurrences": occurrences if occurrences is not None else "n/a",
        "sample_faces": face_text,
        "keywords": keyword_text,
    }
    try:
        return template.format(**fields)
    except (KeyError, IndexError, ValueError) as exc:
        die("render prompt template has an unusable placeholder (%s)" % exc, 2)


def resolve_prompt(prompt_dir):
    """Return (prompt_template_ref, template_text) for the render action.

    Built-in constant when prompt_dir is None; otherwise the template file
    whose name starts with render and ends .txt or .md inside prompt_dir;
    the emitted ref is prompts/<file-stem>. Ambiguous, absent or unusable
    templates fail loud.
    """
    if prompt_dir is None:
        return BUILTIN_PROMPT_RENDER
    candidates = []
    for name in sorted(os.listdir(prompt_dir)):
        if name.startswith("render") and name.endswith((".txt", ".md")):
            candidates.append(name)
    if not candidates:
        die(
            "prompt dir %s carries no render*.txt or render*.md template"
            % prompt_dir,
            2,
        )
    if len(candidates) > 1:
        die(
            "prompt dir %s carries ambiguous render templates: %s"
            % (prompt_dir, ", ".join(candidates)),
            2,
        )
    chosen = os.path.join(prompt_dir, candidates[0])
    try:
        with io.open(chosen, "r", encoding="utf-8") as handle:
            template = handle.read()
    except OSError as exc:
        die("render prompt template unreadable: %s (%s)" % (chosen, exc), 9)
    if "{sample_faces}" not in template:
        die(
            "render prompt template %s lacks the {sample_faces} placeholder"
            % chosen,
            2,
        )
    ref = "prompts/" + os.path.splitext(os.path.basename(chosen))[0]
    return ref, template


# ---------------------------------------------------------------------------
# pure faces (importable by the contract segment and the assembly lane)
# ---------------------------------------------------------------------------


def build_handoff(gaps, prompt_refs=None):
    """Build the emit packet rows (seven contract keys, input order).

    Zero side effects; the rows carry no timestamps, so repeated calls on
    the same inputs are byte-identical. prompt_refs supplies a
    (ref, template) pair; the built-in constant applies when omitted.
    """
    check_gaps(gaps)
    ref, _template = prompt_refs or BUILTIN_PROMPT_RENDER
    rows = []
    for gap in gaps:
        rows.append(
            {
                "gapId": gap["gapId"],
                "cluster": gap["cluster"],
                "sampleFaces": list(gap.get("sampleFaces") or []),
                "keywords": list(gap.get("keywords") or []),
                "occurrences": gap.get("occurrences"),
                "promptTemplateRef": ref,
                "instruction": INSTRUCTION_RENDER,
            }
        )
    return rows


class IngestRejected(Exception):
    """Backfill rejected loud: carries rejections and uncovered gaps."""

    def __init__(self, rejections, missing):
        super().__init__(
            "ingest rejected: %d row(s), %d gap(s) without coverage"
            % (len(rejections), len(missing))
        )
        self.rejections = rejections
        self.missing = missing


def row_shape_errors(row):
    """Renderer-side row contract: presence of the thirteen rendered fields
    plus schemaVersion (integer 2), the W6 vocabulary on refutationForms,
    and a dict-shaped witnessTemplate. Semantic admission (target enum,
    regex compile, priority integer, confidence vocabulary, non-empty
    anchors) stays with the vacgen host validate_row."""
    errors = []
    if not isinstance(row, dict):
        return ["row payload is not an object"]
    for field in RENDER_ROW_FIELDS:
        if field not in row:
            errors.append("missing rendered field %s" % field)
    if errors:
        return errors
    if row["schemaVersion"] != ROW_SCHEMA_VERSION:
        errors.append(
            "schemaVersion %r instead of %d"
            % (row["schemaVersion"], ROW_SCHEMA_VERSION)
        )
    forms = row["refutationForms"]
    if not isinstance(forms, list) or not forms:
        errors.append("refutationForms must be a non-empty list")
    else:
        for form in forms:
            if form not in W6_REFUTATION_FORMS:
                errors.append(
                    "refutationForms entry %r outside the W6 vocabulary (%s)"
                    % (form, ", ".join(W6_REFUTATION_FORMS))
                )
    template = row["witnessTemplate"]
    if not isinstance(template, dict):
        errors.append("witnessTemplate must be an object")
    else:
        bites = template.get("bites")
        if bites is not None and (
            not isinstance(bites, list)
            or not all(isinstance(item, str) for item in bites)
        ):
            errors.append("witnessTemplate.bites must be a list of strings")
    return errors


def trace_sample_faces(gap, row, vacgen):
    """Return True when the row regex matches at least one sample face of
    the source gap. Gaps without sample faces pass vacuously (declared,
    not silent: the ledger records the trace state per gap)."""
    faces = gap.get("sampleFaces") or []
    if not faces:
        return True
    match = row["match"]
    flags = vacgen.flags_int(match.get("flags", ""))
    try:
        pattern = re.compile(match["regex"], flags)
    except re.error:
        return False
    return any(pattern.search(face) is not None for face in faces)


def ingest_rows(gaps, rows, prompt_refs=None, vacgen=None):
    """Validate backfill rows and produce (candidate_rows, ledger_rows).

    Rejection rules per row (fail loud, each rejection named): the row must
    be an object; gapId must resolve to an input gap at most once; modelId
    must be a non-empty string (an undisclosed machine-render attempt is
    refused); the row payload must carry the thirteen rendered fields with
    the renderer-side shape; the payload must pass the vacgen admission
    gate validate_row (C3.4) with every error named; the regex must match
    at least one sample face of the source gap when the gap declares
    faces; promptTemplateRef must match the ref in force; timestampUtc
    must parse as ISO-8601; a declared annotationSite must agree with the
    site derived from modelId. After per-row validation, every input gap
    must carry exactly one accepted row; uncovered gaps are reported
    named. Any rejection or gap raises IngestRejected.

    Ledger rows carry exactly the nine annotation keys in canonical order:
    annotationSite derives from modelId (the literal "human" annotates site
    human, any other modelId annotates site model), linkagesRun is empty at
    render time (the round linkage appends), tenpointVerdict is PENDING,
    timestampUtc comes from the backfill row (never synthesized).
    """
    check_gaps(gaps, need_policy=True)
    if vacgen is None:
        vacgen = load_vacgen_host()
    ref = (prompt_refs or BUILTIN_PROMPT_RENDER)[0]
    by_id = {}
    for gap in gaps:
        by_id[gap["gapId"]] = gap
    rejections = []
    accepted = {}
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            rejections.append(
                {"row_index": index, "gap_id": None, "reason": "row-not-object"}
            )
            continue
        gap_id = row.get("gapId")
        if not isinstance(gap_id, str) or not gap_id.strip():
            rejections.append(
                {"row_index": index, "gap_id": None,
                 "reason": "missing-gap-id"}
            )
            continue
        if gap_id not in by_id:
            rejections.append(
                {"row_index": index, "gap_id": gap_id,
                 "reason": "unknown-gap-id"}
            )
            continue
        if gap_id in accepted:
            rejections.append(
                {"row_index": index, "gap_id": gap_id,
                 "reason": "duplicate-gap-id"}
            )
            continue
        model_id = row.get("modelId")
        if not isinstance(model_id, str) or not model_id.strip():
            rejections.append(
                {"row_index": index, "gap_id": gap_id,
                 "reason": "missing-model-id"}
            )
            continue
        payload = row.get("row")
        if not isinstance(payload, dict):
            rejections.append(
                {"row_index": index, "gap_id": gap_id,
                 "reason": "missing-row-payload"}
            )
            continue
        if row.get("promptTemplateRef") != ref:
            rejections.append(
                {"row_index": index, "gap_id": gap_id,
                 "reason": "prompt-template-ref-mismatch",
                 "expected": ref, "got": row.get("promptTemplateRef")}
            )
            continue
        if not parse_utc(row.get("timestampUtc")):
            rejections.append(
                {"row_index": index, "gap_id": gap_id,
                 "reason": "invalid-timestamp"}
            )
            continue
        shape_errors = row_shape_errors(payload)
        if shape_errors:
            rejections.append(
                {"row_index": index, "gap_id": gap_id,
                 "reason": "row-shape", "errors": shape_errors}
            )
            continue
        admission_errors = vacgen.validate_row(payload)
        if admission_errors:
            rejections.append(
                {"row_index": index, "gap_id": gap_id,
                 "reason": "admission-validate-row",
                 "errors": [str(e) for e in admission_errors]}
            )
            continue
        if not trace_sample_faces(by_id[gap_id], payload, vacgen):
            rejections.append(
                {"row_index": index, "gap_id": gap_id,
                 "reason": "trace-sample-faces",
                 "detail": ("the row regex matches none of the source"
                            " gap's sample faces")}
            )
            continue
        derived_site = (
            SITE_HUMAN if model_id == HUMAN_MODEL_ID else SITE_MODEL
        )
        declared_site = row.get("annotationSite")
        if declared_site is not None and declared_site != derived_site:
            rejections.append(
                {"row_index": index, "gap_id": gap_id,
                 "reason": "annotation-site-conflict",
                 "derived": derived_site, "declared": declared_site}
            )
            continue
        accepted[gap_id] = (payload, model_id, row["timestampUtc"])
    missing = [gap["gapId"] for gap in gaps if gap["gapId"] not in accepted]
    if rejections or missing:
        raise IngestRejected(rejections, missing)
    candidates = []
    ledger_rows = []
    for gap in gaps:
        gap_id = gap["gapId"]
        payload, model_id, stamp = accepted[gap_id]
        candidate = dict(payload)
        candidate["sourceGapId"] = gap_id
        candidate["sourceLane"] = "row-render-handoff"
        candidate["tenpointVerdict"] = VERDICT_PENDING
        candidates.append(candidate)
        ledger_rows.append(
            {
                "gapId": gap_id,
                "renderAction": "render",
                "modelId": model_id,
                "annotationSite": (
                    SITE_HUMAN if model_id == HUMAN_MODEL_ID else SITE_MODEL
                ),
                "promptTemplateRef": ref,
                "linkagesRun": list(LINKAGES_AT_RENDER),
                "policyPrecheckRef": gap["policyPrecheckRef"],
                "tenpointVerdict": VERDICT_PENDING,
                "timestampUtc": stamp,
            }
        )
    return candidates, ledger_rows


# ---------------------------------------------------------------------------
# draft assembly and the R6 re-acceptance face
# ---------------------------------------------------------------------------


def negative_finding_block(source_ledger):
    """The four-element negative-finding boundary for a rendered draft: the
    candidate set is a finding of the source-ledger scan face, not an
    absolute claim."""
    return {
        "scannedWhat": (
            "candidate rows rendered from the gap-cluster ledger at %s"
            " (the families that ledger declares; no other surface was"
            " scanned)" % source_ledger
        ),
        "notScanned": (
            "live vacgen preflight output (no census or pinned mathlib"
            " snapshot on this working surface), gap families outside the"
            " source ledger, and anchor line pins (the C3.3 gate needs a"
            " pinned mathlib snapshot)"
        ),
        "nonAbsoluteClaim": True,
        "aliasesNotExhausted": True,
        "rescanCondition": (
            "the first real gap-cluster ledger from tools/gap_cluster.py, or"
            " a pinned mathlib snapshot becoming available for the C3.3"
            " anchor gate, re-renders this draft"
        ),
    }


def build_draft(candidates, source_ledger, host_path, host_origin):
    """Assemble the draft document from admitted candidate rows."""
    return {
        "schema": DRAFT_SCHEMA,
        "rows": candidates,
        "provenance": {
            "sourceLedger": source_ledger,
            "renderMode": "handoff-ingest",
            "renderCommand": (
                "py -I tools/row_render.py --gaps <ledger.json> --ingest"
                " <backfill.jsonl> --draft-out"
                " docs/drafts/taxonomy-candidates.json"
            ),
            "negativeFinding": negative_finding_block(source_ledger),
        },
        "admission": {
            "gate": "tools/vacgen.py validate_row (C3.4)",
            "hostVacgen": "%s (%s)" % (host_path, host_origin),
            "rowsAdmitted": len(candidates),
            "rowsRejected": 0,
            "rowsTotal": len(candidates),
            "anchorVerification": {
                "verified": False,
                "gate": (
                    "py -I tools/vacgen.py --verify-anchors --mathlib"
                    " <pinned snapshot root> (C3.3)"
                ),
                "reason": (
                    "no pinned mathlib snapshot on this working surface;"
                    " anchor line values are candidate pins"
                ),
            },
            "tenpointVerdict": VERDICT_PENDING,
        },
    }


def check_draft(doc, vacgen):
    """R6 re-acceptance face: every draft row must pass the vacgen
    admission gate; returns the list of (index, errors) failures."""
    failures = []
    for index, row in enumerate(doc.get("rows") or [], 1):
        errors = vacgen.validate_row(row)
        if errors:
            failures.append((index, errors))
    return failures


# ---------------------------------------------------------------------------
# ten-point review face (form emit, verdict ingest, frame write-back)
# ---------------------------------------------------------------------------


def emit_tenpoint(draft_path):
    """Build the ten-point review form for one draft file (the verify host
    supplies schema, vocabulary and fill rule; the engine never judges)."""
    verify = load_verify_host()
    return {
        "schema": verify.FORM_SCHEMA,
        "tool": TOOL,
        "target": draft_path,
        "face": "taxonomy-row",
        "intro": TENPOINT_INTRO_RENDER,
        "points": [
            {
                "point": idx + 1,
                "text": text,
                "verdict": "",
                "citation": "",
                "note": "",
            }
            for idx, text in enumerate(TENPOINT_ROW_POINTS)
        ],
        "fill_rule": verify.FILL_RULE,
    }


def tenpoint_problems(verdicts, expected_target):
    """Validate one verdict file against the expected draft target; returns
    (problems, frame) with every problem named."""
    verify = load_verify_host()
    problems = []
    if not isinstance(verdicts, dict):
        return ["verdict file: not a JSON object"], None
    target = verdicts.get("target")
    if target != expected_target:
        problems.append(
            "target: %r instead of the draft under review %r"
            % (target, expected_target)
        )
    more, frame = verify.validate_verdicts(verdicts)
    return problems + more, frame


def apply_tenpoint(draft_doc, frame, verdicts_ref):
    """Write the verdict frame back into the draft rows and the admission
    block; data-borne only (no synthesized timestamps)."""
    for row in draft_doc.get("rows") or []:
        row["tenpointVerdict"] = frame
    admission = draft_doc.get("admission")
    if isinstance(admission, dict):
        admission["tenpointVerdict"] = frame
        admission["tenpoint"] = {
            "frame": frame,
            "verdictsRef": verdicts_ref,
        }
    return draft_doc


# ---------------------------------------------------------------------------
# actions
# ---------------------------------------------------------------------------


def run_emit(args):
    gaps = args._gaps
    ref, template = resolve_prompt(args.prompts)
    rows = build_handoff(gaps, prompt_refs=(ref, template))
    write_jsonl(args.emit, rows)
    report = {
        "schema": SCHEMA_REPORT,
        "mode": "emit",
        "provider": "handoff",
        "gaps": len(rows),
        "promptTemplateRef": ref,
        "emit_out": args.emit,
        "exit": 0,
    }
    sys.stdout.write(
        "EMIT gaps=%d promptTemplateRef=%s out=%s\n"
        % (len(rows), ref, args.emit)
    )
    if args.json:
        write_json(args.json, report)
    return 0


REJECT_DETAIL_KEYS = {
    "missing-gap-id": "gapId",
    "unknown-gap-id": "gapId",
    "duplicate-gap-id": "gapId",
    "missing-model-id": "modelId",
    "missing-row-payload": "row",
    "prompt-template-ref-mismatch": "promptTemplateRef",
    "invalid-timestamp": "timestampUtc",
    "annotation-site-conflict": "annotationSite",
}


def _print_rejections(rejections):
    """One named line per rejection row (the contract key vocabulary)."""
    for item in rejections:
        key_name = REJECT_DETAIL_KEYS.get(item["reason"])
        detail = ""
        if item.get("errors"):
            detail = " errors: %s" % "; ".join(
                str(e) for e in item["errors"]
            )
        elif item.get("detail"):
            detail = " %s" % item["detail"]
        elif "expected" in item:
            detail = " (expected %r got %r)" % (item["expected"], item["got"])
        sys.stderr.write(
            "%s: REJECT row %s gap %s reason %s%s%s\n"
            % (
                TOOL,
                item.get("row_index"),
                item.get("gap_id"),
                item["reason"],
                " (key %s)" % key_name if key_name else "",
                detail,
            )
        )


def run_ingest(args):
    rows = load_jsonl(args.ingest, "backfill")
    ref, template = resolve_prompt(args.prompts)
    vacgen = load_vacgen_host(args.vacgen)
    try:
        candidates, ledger = ingest_rows(
            args._gaps, rows, prompt_refs=(ref, template), vacgen=vacgen
        )
    except ValueError as exc:
        die("gaps invalid for ingest: %s" % exc, 1)
    except IngestRejected as exc:
        _print_rejections(exc.rejections)
        for gap_id in exc.missing:
            sys.stderr.write(
                "%s: NO-COVERAGE gap %s (the backfill carries no row for"
                " it)\n" % (TOOL, gap_id)
            )
        if args.json:
            write_json(
                args.json,
                {
                    "schema": SCHEMA_REPORT,
                    "mode": "ingest",
                    "provider": "handoff",
                    "admitted": 0,
                    "rejections": exc.rejections,
                    "missing": exc.missing,
                    "exit": 1,
                },
            )
        return 1
    if args.ledger_out:
        write_jsonl(args.ledger_out, ledger)
    draft = build_draft(
        candidates, args.gaps, host_path_of(vacgen),
        getattr(vacgen, "_rowrender_origin", "unknown"),
    )
    if args.draft_out:
        write_json(args.draft_out, draft)
    report = {
        "schema": SCHEMA_REPORT,
        "mode": "ingest",
        "provider": "handoff",
        "admitted": len(candidates),
        "rejections": [],
        "missing": [],
        "promptTemplateRef": ref,
        "draft_out": args.draft_out,
        "ledger_out": args.ledger_out,
        "exit": 0,
    }
    sys.stdout.write(
        "INGEST admitted=%d validate_row=100pct draft=%s\n"
        % (len(candidates), args.draft_out or "(not written)")
    )
    if args.json:
        write_json(args.json, report)
    return 0


def run_check_draft(args):
    vacgen = load_vacgen_host(args.vacgen)
    doc = load_json_file(args.check_draft, "draft")
    if isinstance(doc, dict):
        schema = doc.get("schema")
        if schema is not None and schema != DRAFT_SCHEMA:
            die("draft schema %r instead of %s" % (schema, DRAFT_SCHEMA), 1)
    failures = check_draft(doc, vacgen)
    total = len(doc.get("rows") or [])
    for index, errors in failures:
        sys.stderr.write(
            "%s: DRAFT-REJECT row %d reason admission-validate-row"
            " errors: %s\n"
            % (TOOL, index, "; ".join(str(e) for e in errors))
        )
    admitted = total - len(failures)
    exit_code = 1 if failures or not total else 0
    report = {
        "schema": SCHEMA_REPORT,
        "mode": "check-draft",
        "rowsTotal": total,
        "rowsAdmitted": admitted,
        "rowsRejected": len(failures),
        "admissionPct": (admitted * 100 // total) if total else 0,
        "exit": exit_code,
    }
    sys.stdout.write(
        "CHECK-DRAFT rows=%d admitted=%d rejected=%d\n"
        % (total, admitted, len(failures))
    )
    if args.json:
        write_json(args.json, report)
    return exit_code


def run_emit_tenpoint(args):
    form = emit_tenpoint(args.emit_tenpoint)
    if args.json:
        write_json(args.json, form)
    else:
        sys.stdout.write(
            json.dumps(form, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n"
        )
    sys.stdout.write(
        "EMIT-TENPOINT target=%s points=%d\n"
        % (args.emit_tenpoint, len(form["points"]))
    )
    return 0


def run_ingest_tenpoint(args):
    verdicts = load_json_file(args.ingest_tenpoint, "verdicts")
    problems, frame = tenpoint_problems(verdicts, args.draft_out)
    if problems:
        for problem in problems:
            sys.stderr.write("%s: VERDICT-REJECT %s\n" % (TOOL, problem))
        if args.json:
            write_json(
                args.json,
                {
                    "schema": SCHEMA_REPORT,
                    "mode": "ingest-tenpoint",
                    "problems": problems,
                    "exit": 1,
                },
            )
        return 1
    draft_doc = load_json_file(args.draft_out, "draft")
    if not isinstance(draft_doc, dict) or not isinstance(
        draft_doc.get("rows"), list
    ):
        die(
            "draft %s carries no rows list; nothing to write back to"
            % args.draft_out,
            1,
        )
    draft_doc = apply_tenpoint(draft_doc, frame, args.ingest_tenpoint)
    write_json(args.draft_out, draft_doc)
    report = {
        "schema": SCHEMA_REPORT,
        "mode": "ingest-tenpoint",
        "frame": frame,
        "rowsRewritten": len(draft_doc["rows"]),
        "draft_out": args.draft_out,
        "exit": 0,
    }
    sys.stdout.write(
        "INGEST-TENPOINT frame=%s rowsRewritten=%d draft=%s\n"
        % (frame, len(draft_doc["rows"]), args.draft_out)
    )
    if args.json:
        write_json(args.json, report)
    return 0


def run_http(args):
    host = load_i18n_host()
    refusal = host.check_net_env(os.environ)
    if refusal:
        die("http provider refused: %s" % refusal, 2)
    endpoint = os.environ["ROCQWASH_LLM_ENDPOINT"]
    model_name = os.environ["ROCQWASH_LLM_MODEL"]
    api_key = os.environ["ROCQWASH_LLM_KEY"]
    ref, template = resolve_prompt(args.prompts)
    vacgen = load_vacgen_host(args.vacgen)
    backfill_rows = []
    failures = []
    netred_lines = 0
    for gap in args._gaps:
        prompt_text = render_prompt(template, gap)
        content, error, status = host.http_translate_segment(
            endpoint, model_name, api_key, prompt_text, args.timeout
        )
        entry = {
            "utc": utc_now(),
            "tool": TOOL,
            "action": "row-render-http",
            "gapId": gap["gapId"],
            "httpStatus": status,
        }
        if error is not None:
            entry["status"] = "error"
            entry["error"] = error
            failures.append({"gapId": gap["gapId"], "error": error})
        else:
            entry["status"] = "ok"
            try:
                payload = json.loads(content)
            except ValueError as exc:
                entry["status"] = "error"
                entry["error"] = "row-not-json (%s)" % exc
                failures.append(
                    {"gapId": gap["gapId"], "error": entry["error"]}
                )
            else:
                backfill_rows.append(
                    {
                        "gapId": gap["gapId"],
                        "row": payload,
                        "modelId": model_name,
                        "promptTemplateRef": ref,
                        "timestampUtc": utc_now(),
                    }
                )
        host.append_netred(args.netred_ledger, entry)
        netred_lines += 1
        sys.stdout.write(
            "HTTP gap %s verdict %s (http_status %s)\n"
            % (gap["gapId"], "ok" if error is None else "failed", status)
        )
    admitted = 0
    if backfill_rows:
        try:
            candidates, ledger = ingest_rows(
                args._gaps, backfill_rows, prompt_refs=(ref, template),
                vacgen=vacgen,
            )
        except IngestRejected as exc:
            _print_rejections(exc.rejections)
            for gap_id in exc.missing:
                sys.stderr.write(
                    "%s: NO-COVERAGE gap %s\n" % (TOOL, gap_id)
                )
            failures.append(
                {"error": "ingest-rejected", "detail": exc.rejections}
            )
        else:
            admitted = len(candidates)
            if args.ledger_out:
                write_jsonl(args.ledger_out, ledger)
            if args.draft_out:
                draft = build_draft(
                    candidates, args.gaps, host_path_of(vacgen),
                    getattr(vacgen, "_rowrender_origin", "unknown"),
                )
                write_json(args.draft_out, draft)
    sys.stdout.write(
        "HTTP rendered=%d failed=%d netred_lines=%d ledger=%s\n"
        % (admitted, len(failures), netred_lines, args.netred_ledger)
    )
    report = {
        "schema": SCHEMA_REPORT,
        "mode": "render-http",
        "provider": "http",
        "modelId": model_name,
        "promptTemplateRef": ref,
        "admitted": admitted,
        "failed": len(failures),
        "failures": failures,
        "netred_ledger": args.netred_ledger,
        "netred_lines": netred_lines,
        "draft_out": args.draft_out,
        "exit": 1 if failures else 0,
    }
    if args.json:
        write_json(args.json, report)
    return 1 if failures else 0


# ---------------------------------------------------------------------------
# selftest (fully offline)
# ---------------------------------------------------------------------------

PROBE_TS_FORMAT = "%04d-%02d-%02dT%02d:%02d:%02dZ"
PROBE_TS = PROBE_TS_FORMAT % (1970, 1, 1, 0, 0, 0)


def _probe_gaps():
    return [
        {
            "gapId": "g0001",
            "cluster": "annum",
            "status": "clustered",
            "occurrences": 2,
            "sampleFaces": ["(1 / 2 : R) < z.abs"],
            "keywords": ["modulus"],
            "policyPrecheckRef": "probe-policy",
        },
        {
            "gapId": "g0002",
            "cluster": "physics-misc",
            "occurrences": 1,
            "sampleFaces": [],
            "keywords": [],
            "policyPrecheckRef": "probe-policy",
        },
    ]


def _probe_row_regex():
    # probe faces use ASCII-only spellings so the selftest stays ASCII-safe
    return r"^\s*\(\s*1\s*/\s*2\s*:\s*R\s*\)\s*<\s*[A-Za-z_][\w'.!]*\s*\.\s*abs\s*$"


def _probe_payload(regex=None, overrides=None):
    payload = {
        "schemaVersion": 2,
        "familyId": "probe.family.row",
        "cluster": "annum",
        "match": {"target": "assumption.type",
                  "regex": regex or _probe_row_regex(), "flags": ""},
        "priority": 40,
        "confidence": "MID",
        "witnessStrategy": "probe-point bite with a declared boundary block",
        "witnessTemplate": {
            "bites": ["theorem {p}_probe : True := trivial"],
            "boundary": {"kind": "numeric-constant",
                         "template": "{num} / {den}"},
        },
        "mathlibAnchors": [{"symbol": "Probe.sym", "relPath": "Mathlib/X.lean",
                            "line": 1}],
        "refutationForms": ["full", "point"],
        "boundaryApplicability": "numeric-constant",
        "gapKeywords": ["modulus"],
        "notes": "probe row for the contract selftest",
    }
    if overrides:
        for key, value in overrides.items():
            if value is None:
                payload.pop(key, None)
            else:
                payload[key] = value
    return payload


def _probe_g0002_payload():
    # a valid row for the sample-face-free gap: the trace check is vacuous
    return _probe_payload(
        regex=r"^\s*True$",
        overrides={"cluster": "physics-misc", "familyId": "probe.family.g2",
                   "gapKeywords": []},
    )


def _probe_backfill(payloads, model_id="probe-renderer", ref=None):
    rows = []
    for gap_id, payload in payloads:
        rows.append(
            {
                "gapId": gap_id,
                "row": payload,
                "modelId": model_id,
                "promptTemplateRef": ref or BUILTIN_PROMPT_RENDER[0],
                "timestampUtc": PROBE_TS,
            }
        )
    return rows


def run_selftest(out):
    """Offline probes over the pure faces, the admission delegation, the
    ten-point face and the refusal branches."""
    failures = []
    counter = [0]

    def check(name, condition, detail=""):
        counter[0] += 1
        if condition:
            out.write("SELFTEST PASS %s\n" % name)
        else:
            failures.append(name)
            out.write("SELFTEST FAIL %s %s\n" % (name, detail))

    vacgen = load_vacgen_host()
    check(
        "constants",
        TOOL == "row_render.py"
        and len(ANNOTATION_KEYS) == 9
        and len(EMIT_KEYS) == 7
        and len(BACKFILL_KEYS) == 5
        and W6_REFUTATION_FORMS
        == ("full", "point", "tactics", "noclassic", "band")
        and len(RENDER_ROW_FIELDS) == 13,
        "module constants drifted",
    )
    check(
        "vacgen-host",
        hasattr(vacgen, "validate_row") and hasattr(vacgen, "MATCH_TARGETS"),
        "vacgen host faces absent",
    )
    gaps = _probe_gaps()
    try:
        check_gaps(gaps)
        check("gap-shape-ok", True)
    except ValueError as exc:
        check("gap-shape-ok", False, str(exc))
    for name, mutate in (
        ("gap-shape-missing-id", lambda g: g[0].pop("gapId")),
        ("gap-shape-dup-id", lambda g: g[1].update(gapId=g[0]["gapId"])),
        ("gap-shape-bad-occurrences", lambda g: g[0].update(occurrences=0)),
        ("gap-shape-bad-status", lambda g: g[0].update(status="zombie")),
    ):
        broken = _probe_gaps()
        mutate(broken)
        try:
            check_gaps(broken)
            check(name, False, "defect accepted")
        except ValueError:
            check(name, True)
    try:
        check_gaps(_probe_gaps(), need_policy=True)
        check("gap-shape-policy-ok", True)
    except ValueError as exc:
        check("gap-shape-policy-ok", False, str(exc))
    no_policy = _probe_gaps()
    for gap in no_policy:
        gap.pop("policyPrecheckRef")
    try:
        check_gaps(no_policy, need_policy=True)
        check("gap-shape-policy-required", False, "missing policy accepted")
    except ValueError:
        check("gap-shape-policy-required", True)

    packet = build_handoff(gaps)
    check(
        "handoff-keys",
        all(set(r) == set(EMIT_KEYS) for r in packet)
        and len(packet) == len(gaps),
        "emit rows lost the contract keys",
    )
    check(
        "handoff-determinism",
        json.dumps(build_handoff(gaps)) == json.dumps(packet),
        "build_handoff not byte-stable",
    )

    good = _probe_backfill(
        [("g0001", _probe_payload()), ("g0002", _probe_g0002_payload())]
    )
    try:
        candidates, ledger = ingest_rows(gaps, good, vacgen=vacgen)
        check(
            "ingest-happy",
            len(candidates) == 2
            and all(set(r) == set(ANNOTATION_KEYS) for r in ledger)
            and all(r["tenpointVerdict"] == VERDICT_PENDING for r in ledger)
            and all(r["annotationSite"] == SITE_MODEL for r in ledger)
            and all(
                c["tenpointVerdict"] == VERDICT_PENDING for c in candidates
            )
            and all(
                c["sourceGapId"] in ("g0001", "g0002") for c in candidates
            ),
            "ingest happy path drifted",
        )
    except IngestRejected as exc:
        check("ingest-happy", False, json.dumps(exc.rejections)[:160])
    human = _probe_backfill(
        [("g0001", _probe_payload()), ("g0002", _probe_g0002_payload())],
        model_id="human",
    )
    try:
        _candidates, ledger = ingest_rows(gaps, human, vacgen=vacgen)
        check(
            "ingest-human-site",
            all(r["annotationSite"] == SITE_HUMAN for r in ledger),
            "human modelId did not annotate site human",
        )
    except IngestRejected as exc:
        check("ingest-human-site", False, json.dumps(exc.rejections)[:160])

    def _expect_reject(name, rows, reason_part):
        try:
            ingest_rows(gaps, rows, vacgen=vacgen)
            check(name, False, "defect accepted")
        except IngestRejected as exc:
            reasons = json.dumps(exc.rejections) + json.dumps(exc.missing)
            check(name, reason_part in reasons, reasons[:220])

    # admission delegation: the regex fails to compile, which the
    # renderer-side shape check passes and only validate_row catches
    _expect_reject(
        "ingest-reject-admission",
        _probe_backfill(
            [
                ("g0001", _probe_payload(regex="^(unclosed")),
                ("g0002", _probe_g0002_payload()),
            ]
        ),
        "admission-validate-row",
    )
    bad_priority = _probe_payload()
    bad_priority["priority"] = "high"
    _expect_reject(
        "ingest-reject-priority-type",
        _probe_backfill(
            [("g0001", bad_priority), ("g0002", _probe_g0002_payload())]
        ),
        "admission-validate-row",
    )
    missing_field = _probe_payload()
    missing_field.pop("boundaryApplicability")
    _expect_reject(
        "ingest-reject-shape",
        _probe_backfill(
            [("g0001", missing_field), ("g0002", _probe_g0002_payload())]
        ),
        "row-shape",
    )
    bad_forms = _probe_payload()
    bad_forms["refutationForms"] = ["full", "wat"]
    _expect_reject(
        "ingest-reject-w6",
        _probe_backfill(
            [("g0001", bad_forms), ("g0002", _probe_g0002_payload())]
        ),
        "row-shape",
    )
    trace_miss = _probe_payload(regex=r"^\s*9\s*<\s*9$")
    _expect_reject(
        "ingest-reject-trace",
        _probe_backfill(
            [("g0001", trace_miss), ("g0002", _probe_g0002_payload())]
        ),
        "trace-sample-faces",
    )
    _expect_reject(
        "ingest-reject-coverage",
        _probe_backfill([("g0001", _probe_payload())]),
        "g0002",
    )
    _expect_reject(
        "ingest-reject-prompt-ref",
        _probe_backfill(
            [("g0001", _probe_payload()), ("g0002", _probe_g0002_payload())],
            ref="prompts/other-v9",
        ),
        "prompt-template-ref-mismatch",
    )
    stale = _probe_backfill(
        [("g0001", _probe_payload()), ("g0002", _probe_g0002_payload())]
    )
    stale[0]["timestampUtc"] = "not-a-stamp"
    _expect_reject("ingest-reject-stamp", stale, "invalid-timestamp")

    tmp = tempfile.mkdtemp(prefix="rowrender_selftest_")
    ledger_path = os.path.join(tmp, "ledger.jsonl")
    draft_path = os.path.join(tmp, "draft.json")
    backfill_path = os.path.join(tmp, "backfill.jsonl")
    write_jsonl(backfill_path, good)
    ingest_args = argparse.Namespace(
        _gaps=gaps, gaps="(probe)", ingest=backfill_path,
        draft_out=draft_path, ledger_out=ledger_path, json=None,
        prompts=None, vacgen=vacgen.__file__, timeout=60,
        netred_ledger=None, emit=None, check_draft=None,
        emit_tenpoint=None, ingest_tenpoint=None, policy_ref=None,
        provider="handoff",
    )
    code = run_ingest(ingest_args)
    check(
        "cli-ingest-green",
        code == 0 and os.path.isfile(draft_path),
        "run_ingest rc=%d" % code,
    )
    check_args = argparse.Namespace(
        vacgen=vacgen.__file__, check_draft=draft_path, json=None,
    )
    code = run_check_draft(check_args)
    check("cli-check-draft-green", code == 0, "run_check_draft rc=%d" % code)
    broken_doc = json.loads(read_text(draft_path, "draft"))
    broken_doc["rows"][0]["match"]["regex"] = "(unclosed"
    broken_path = os.path.join(tmp, "broken.json")
    write_json(broken_path, broken_doc)
    check_args.check_draft = broken_path
    code = run_check_draft(check_args)
    check("cli-check-draft-red", code == 1, "broken draft rc=%d" % code)

    # byte-stable draft on equal inputs (the render-side determinism face)
    first = read_text(draft_path, "draft")
    draft_path_two = os.path.join(tmp, "draft2.json")
    ingest_args.draft_out = draft_path_two
    ingest_args.ledger_out = None
    run_ingest(ingest_args)
    check(
        "draft-determinism",
        read_text(draft_path_two, "draft") == first,
        "equal inputs produced different draft bytes",
    )

    verify = load_verify_host()
    form = emit_tenpoint("draft.json")
    check(
        "tenpoint-form",
        form["schema"] == verify.FORM_SCHEMA
        and len(form["points"]) == verify.POINT_COUNT
        and "face" in form
        and "fill_rule" in form,
        "ten-point form shape drifted",
    )
    good_points = [
        {"point": idx + 1, "verdict": "PASS", "citation": str(idx + 1),
         "note": ""}
        for idx in range(verify.POINT_COUNT)
    ]
    verdicts = {
        "schema": verify.VERDICT_SCHEMA,
        "target": "draft.json",
        "frame": "ALL-PASS",
        "points": good_points,
    }
    probs, frame = tenpoint_problems(verdicts, "draft.json")
    check(
        "tenpoint-ingest-good",
        not probs and frame == "ALL-PASS",
        "good verdicts rejected: %r" % (probs,),
    )
    verdicts["frame"] = "N-FAIL"
    probs, _frame = tenpoint_problems(verdicts, "draft.json")
    check(
        "tenpoint-ingest-frame-conflict",
        any("frame" in p for p in probs),
        "ALL-PASS points under an N-FAIL frame were accepted",
    )
    probs, _frame = tenpoint_problems(verdicts, "other.json")
    check(
        "tenpoint-ingest-target",
        any("target" in p for p in probs),
        "wrong target accepted",
    )

    refusal = check_net_env({})
    check(
        "net-default-deny",
        refusal is not None and "default deny" in refusal,
        "closed gate did not refuse",
    )
    gate_on = {name: "x" for name in NET_CONFIG_ENVS}
    gate_on[NET_GATE_ENV] = "1"
    refusal = check_net_env(gate_on)
    check(
        "net-gate-open-shape",
        refusal is None,
        "fully-open gate refused: %r" % refusal,
    )
    partial = {
        "ROCQWASH_LLM_ENDPOINT": "x",
        "ROCQWASH_LLM_MODEL": "x",
        NET_GATE_ENV: "1",
    }
    refusal = check_net_env(partial)
    check(
        "net-gate-missing-var",
        refusal is not None and "ROCQWASH_LLM_KEY" in refusal,
        "missing variable not named",
    )

    out.write(
        "SELFTEST %s (%d checks)\n"
        % ("GREEN" if not failures else "RED", counter[0])
    )
    return 0 if not failures else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _stamp_policy_ref(gaps, policy_ref):
    """Stamp --policy-ref into gaps that lack their own policyPrecheckRef;
    a carried reference conflicting with the flag is a usage refusal."""
    working = []
    for gap in gaps:
        item = dict(gap)
        carried = item.get("policyPrecheckRef")
        if carried and policy_ref and carried != policy_ref:
            die(
                "gap %s carries policyPrecheckRef %r conflicting with"
                " --policy-ref %r" % (item["gapId"], carried, policy_ref),
                2,
            )
        if not carried and policy_ref:
            item["policyPrecheckRef"] = policy_ref
        working.append(item)
    return working


def build_parser():
    parser = argparse.ArgumentParser(
        prog=TOOL,
        description=(
            "Refinery W2 row renderer: gap ledger to candidate taxonomy"
            " rows through the E4 P2 handoff form (zero network by"
            " default); every drafted row passes the vacgen validate_row"
            " admission gate (C3.4)."
        ),
    )
    parser.add_argument(
        "--gaps",
        help="gap-cluster ledger JSON file (array, or object with a gaps"
             " key)",
    )
    parser.add_argument(
        "--emit",
        help="write the render packet as JSONL to this path (zero network)",
    )
    parser.add_argument(
        "--ingest",
        help="validate a backfill JSONL file at this path (zero network)",
    )
    parser.add_argument(
        "--check-draft",
        help="re-run the vacgen admission gate over a draft JSON (the R6"
             " re-acceptance face)",
    )
    parser.add_argument(
        "--emit-tenpoint",
        help="emit the ten-point first-admission form for this draft file",
    )
    parser.add_argument(
        "--ingest-tenpoint",
        help="ingest a ten-point verdicts JSON file at this path",
    )
    parser.add_argument(
        "--draft-out",
        help="the draft JSON file an action operates on: ingest writes it,"
             " ingest-tenpoint reviews it and writes the frame back",
    )
    parser.add_argument(
        "--provider",
        choices=list(PROVIDERS),
        default="handoff",
        help="handoff (default, zero network) or http (default-deny gate)",
    )
    parser.add_argument(
        "--vacgen",
        help="admission host path (default: ROW_RENDER_VACGEN env, then"
             " the sibling tools/vacgen.py)",
    )
    parser.add_argument(
        "--prompts",
        help="render prompt dir with render*.txt/.md files"
             " (default: built-in constant)",
    )
    parser.add_argument(
        "--policy-ref",
        help="layer-law first-admission reference stamped into gaps at"
             " ingest/http time",
    )
    parser.add_argument(
        "--ledger-out",
        help="write the nine-key render ledger rows JSONL here",
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
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        return run_selftest(sys.stdout)

    actions = []
    if args.emit:
        actions.append("emit")
    if args.ingest:
        actions.append("ingest")
    if args.check_draft:
        actions.append("check-draft")
    if args.emit_tenpoint:
        actions.append("emit-tenpoint")
    if args.ingest_tenpoint:
        actions.append("ingest-tenpoint")
    if args.provider == "http":
        actions.append("http")
    if not actions:
        die(
            "no action requested: give --emit, --ingest, --check-draft,"
            " --emit-tenpoint, --ingest-tenpoint, --provider http, or"
            " --selftest",
            2,
        )
    if len(actions) > 1 or (
        args.provider == "http"
        and (args.emit or args.ingest or args.check_draft
             or args.emit_tenpoint or args.ingest_tenpoint)
    ):
        die(
            "actions %s conflict: choose one of --emit, --ingest,"
            " --check-draft, --emit-tenpoint, --ingest-tenpoint,"
            " --provider http" % "+".join(actions),
            2,
        )
    if actions[0] == "check-draft":
        return run_check_draft(args)
    if actions[0] == "emit-tenpoint":
        return run_emit_tenpoint(args)
    if actions[0] == "ingest-tenpoint":
        if not args.draft_out:
            die(
                "--ingest-tenpoint needs --draft-out <draft.json>: the"
                " verdicts must target the draft under review and the"
                " frame is written back to it",
                2,
            )
        return run_ingest_tenpoint(args)
    if not args.gaps:
        die("--gaps <json> is required for %s" % actions[0], 2)
    raw_gaps = load_gaps(args.gaps)
    try:
        check_gaps(raw_gaps)
    except ValueError as exc:
        die("gaps invalid: %s" % exc, 1)
    if actions[0] in ("ingest", "http"):
        try:
            check_gaps(raw_gaps, need_policy=True)
        except ValueError as exc:
            die("gaps invalid for %s: %s" % (actions[0], exc), 1)
    args._gaps = _stamp_policy_ref(raw_gaps, args.policy_ref)
    if actions[0] == "emit":
        return run_emit(args)
    if actions[0] == "ingest":
        return run_ingest(args)
    if not args.netred_ledger:
        die("--provider http needs --netred-ledger <p>", 2)
    return run_http(args)


if __name__ == "__main__":
    sys.exit(main())
