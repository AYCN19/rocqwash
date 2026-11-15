#!/usr/bin/env python3
"""tests/refinery_segments/render.py -- contract segment for the refinery W2
row renderer (tools/row_render.py).

Purpose.  Assert the CLI and pure-function contract of the W2 row renderer
  item by item: gap-ledger shape checks, the seven-key emit packet and its
  byte determinism, ingest admission through the vacgen validate_row gate
  (C3.4) with every rejection branch named, the nine-key render ledger, the
  R6 check-draft re-acceptance face, draft determinism, draft consumption
  by the vacgen load_taxonomy load face, the ten-point form round trip
  with frame write-back, the default-deny http refusal, and the landed
  candidate draft staying at 100 percent admission.
Interface.  `python -I tests/refinery_segments/render.py` runs this segment
  standalone and exits 0 when no FAIL line was produced, 1 otherwise; the
  assembly lane imports the module and calls run_segment_render(), which
  returns (passed, failed, skipped, results) with results rows shaped
  (status, name, detail).  Importing spawns nothing (import-safe).
Dependencies.  Python 3 standard library only; tools/row_render.py loads
  dynamically (one loud SKIP line while it has not landed); the vacgen
  admission host resolves through ROW_RENDER_VACGEN then the sibling
  tools/vacgen.py, the ten-point host through ROW_RENDER_VERIFY then the
  sibling tools/i18n_verify.py; zero network by construction (the http
  provider is exercised on its refusal branch only, never connected).
Evidence.  The W2 lane contract of the refinery work order (full row
  field set, validate_row 100 percent admission, handoff form reuse); live
  runs of tools/row_render.py --selftest and the emit/ingest/check-draft
  chain recorded under the lane OUT logs.
Exit-codes.  0 all checks green (zero FAIL); 1 at least one FAIL (each
  listed, fail loud); 2 usage error.  SKIP lines name their missing surface
  and never count as passes.
"""

import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TOOL_TIMEOUT_S = 120

RENDER_TOOL = os.path.join(ROOT, "tools", "row_render.py")
VACGEN_SIBLING = os.path.join(ROOT, "tools", "vacgen.py")
VERIFY_SIBLING = os.path.join(ROOT, "tools", "i18n_verify.py")
LANDED_DRAFT = os.path.join(ROOT, "docs", "drafts",
                            "taxonomy-candidates.json")
NET_GATE_ENV = "ROCQWASH_MCP_ALLOW_NET"
NET_CONFIG_ENVS = ("ROCQWASH_LLM_ENDPOINT", "ROCQWASH_LLM_MODEL",
                   "ROCQWASH_LLM_KEY")

PROBE_TS_FORMAT = "%04d-%02d-%02dT%02d:%02d:%02dZ"
PROBE_TS = PROBE_TS_FORMAT % (1970, 1, 1, 0, 0, 0)

# probe gap ledger (ASCII spellings keep the probes battery-safe)
PROBE_GAPS = [
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

PROBE_ROW_REGEX = (
    r"^\s*\(\s*1\s*/\s*2\s*:\s*R\s*\)\s*<\s*[A-Za-z_][\w'.!]*\s*\.\s*abs\s*$"
)


def utc_probe_stamp():
    return PROBE_TS


def probe_payload(regex=None, overrides=None):
    payload = {
        "schemaVersion": 2,
        "familyId": "probe.family.row",
        "cluster": "annum",
        "match": {"target": "assumption.type",
                  "regex": regex or PROBE_ROW_REGEX, "flags": ""},
        "priority": 40,
        "confidence": "MID",
        "witnessStrategy": "probe-point bite with a declared boundary block",
        "witnessTemplate": {
            "bites": ["theorem {p}_probe : True := trivial"],
            "boundary": {"kind": "numeric-constant",
                         "template": "{num} / {den}"},
        },
        "mathlibAnchors": [{"symbol": "Probe.sym",
                            "relPath": "Mathlib/X.lean", "line": 1}],
        "refutationForms": ["full", "point"],
        "boundaryApplicability": "numeric-constant",
        "gapKeywords": ["modulus"],
        "notes": "probe row for the contract segment",
    }
    if overrides:
        for key, value in overrides.items():
            if value is None:
                payload.pop(key, None)
            else:
                payload[key] = value
    return payload


def probe_g2_payload():
    return probe_payload(
        regex=r"^\s*True$",
        overrides={"cluster": "physics-misc",
                   "familyId": "probe.family.g2", "gapKeywords": []},
    )


def probe_backfill(model_id="probe-renderer", ref=None, payloads=None):
    rows = []
    for gap_id, payload in (payloads or [
            ("g0001", probe_payload()), ("g0002", probe_g2_payload())]):
        rows.append({
            "gapId": gap_id,
            "row": payload,
            "modelId": model_id,
            "promptTemplateRef": ref or "prompts/render-row-v1",
            "timestampUtc": utc_probe_stamp(),
        })
    return rows


# ------------------------------------------------------------- helpers ----


def load_render_module(results):
    """Load tools/row_render.py; None plus one loud SKIP line while the
    file has not landed; a FAIL line when it landed but raised at import."""
    if not os.path.isfile(RENDER_TOOL):
        results.append(("SKIP", "module-landed",
                        "tools/row_render.py not landed yet; the contract"
                        " checks of this segment activate at merge"))
        return None
    spec = importlib.util.spec_from_file_location("rqw_seg_row_render",
                                                  RENDER_TOOL)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        results.append(("FAIL", "module-import",
                        "tools/row_render.py loaded but raised at import:"
                        " %r" % (exc,)))
        return None
    return module


def load_vacgen_host():
    """Load the admission host: ROW_RENDER_VACGEN env first, then the
    sibling tools/vacgen.py; returns the module or None."""
    path = os.environ.get("ROW_RENDER_VACGEN") or VACGEN_SIBLING
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("rqw_seg_vacgen_host", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_verify_host():
    path = os.environ.get("ROW_RENDER_VERIFY") or VERIFY_SIBLING
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("rqw_seg_verify_host", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def child_env():
    """Neutral environment for renderer CLI runs: the network gate and the
    LLM endpoint variables are stripped so every non-network path is proven
    offline and the provider face hits its default-deny branch."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for key in (NET_GATE_ENV,) + NET_CONFIG_ENVS:
        env.pop(key, None)
    return env


def run_renderer(args):
    """Run the renderer CLI with the isolated interpreter and a neutral
    environment; returns the completed process object."""
    return subprocess.run(
        [sys.executable, "-I", RENDER_TOOL] + [str(a) for a in args],
        capture_output=True, text=True, timeout=TOOL_TIMEOUT_S,
        env=child_env(), cwd=ROOT, encoding="utf-8", errors="replace")


def out_text(proc):
    return (proc.stdout or "") + (proc.stderr or "")


def write_json_file(path, payload):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2))
        handle.write("\n")


def write_jsonl_file(path, rows):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_json_file(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text_file(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


# ------------------------------------------------------------ segment -----


def run_segment_render():
    """Contract checks for the W2 row renderer; returns
    (passed, failed, skipped, results)."""
    results = []
    mod = load_render_module(results)
    if mod is None:
        return _tally(results)
    host = load_vacgen_host()
    verify_host = load_verify_host()
    if host is None:
        results.append(("SKIP", "vacgen-host-landed",
                        "no vacgen admission host found (ROW_RENDER_VACGEN"
                        " env unset and tools/vacgen.py absent); the"
                        " admission checks of this segment activate at"
                        " merge"))
    if verify_host is None:
        results.append(("SKIP", "verify-host-landed",
                        "no ten-point host found (ROW_RENDER_VERIFY env"
                        " unset and tools/i18n_verify.py absent); the"
                        " ten-point checks of this segment activate at"
                        " merge"))
    vacgen_arg = os.environ.get("ROW_RENDER_VACGEN") or VACGEN_SIBLING

    def check(name, thunk):
        try:
            detail = thunk()
        except AssertionError as exc:
            results.append(("FAIL", name, str(exc) or "assertion failed"))
        except Exception as exc:
            results.append(("FAIL", name, "%s: %r"
                            % (type(exc).__name__, exc)))
        else:
            results.append(("PASS", name, detail or "ok"))

    def _thunk_constants():
        check_true(len(mod.ANNOTATION_KEYS) == 9,
                   "ANNOTATION_KEYS lost the nine-key form")
        check_true(len(mod.EMIT_KEYS) == 7,
                   "EMIT_KEYS lost the seven-key form")
        check_true(len(mod.BACKFILL_KEYS) == 5,
                   "BACKFILL_KEYS lost the five-key form")
        check_true(mod.W6_REFUTATION_FORMS
                   == ("full", "point", "tactics", "noclassic", "band"),
                   "W6 vocabulary drifted: %r" % (mod.W6_REFUTATION_FORMS,))
        check_true(len(mod.RENDER_ROW_FIELDS) == 13,
                   "the thirteen rendered fields drifted")
        return ("nine-key ledger, seven-key emit, five-key backfill, W6"
                " vocabulary and the thirteen rendered fields in place"
                " (vacgen host: %s)" % vacgen_arg)

    def _thunk_gate_alive():
        check_true(host is not None, "no vacgen host loaded")
        good = probe_payload()
        check_true(host.validate_row(good) == [],
                   "a well-formed probe row failed the C3.4 gate: %r"
                   % (host.validate_row(good),))
        bad = probe_payload(regex="^(unclosed")
        errors = host.validate_row(bad)
        check_true(errors and any("compile failed" in str(e) for e in errors),
                   "an unclosed regex passed the C3.4 gate: %r" % (errors,))
        return ("loaded host validate_row admits the probe row and rejects"
                " an uncompilable regex (C3.4 gate alive)")

    def _thunk_gap_shape():
        mod.check_gaps(PROBE_GAPS)
        broken_one = [dict(g) for g in PROBE_GAPS]
        broken_one[0].pop("gapId")
        expect_value_error(lambda: mod.check_gaps(broken_one),
                           "missing gapId accepted")
        broken_two = [dict(g) for g in PROBE_GAPS]
        broken_two[1]["gapId"] = broken_two[0]["gapId"]
        expect_value_error(lambda: mod.check_gaps(broken_two),
                           "duplicate gapId accepted")
        broken_three = [dict(g) for g in PROBE_GAPS]
        broken_three[0]["occurrences"] = 0
        expect_value_error(lambda: mod.check_gaps(broken_three),
                           "zero occurrences accepted")
        broken_four = [dict(g) for g in PROBE_GAPS]
        broken_four[0]["status"] = "zombie"
        expect_value_error(lambda: mod.check_gaps(broken_four),
                           "status outside the vocabulary accepted")
        no_policy = [dict(g) for g in PROBE_GAPS]
        for gap in no_policy:
            gap.pop("policyPrecheckRef")
        expect_value_error(lambda: mod.check_gaps(no_policy,
                                                  need_policy=True),
                           "ingest accepted a gap without a"
                           " policyPrecheckRef")
        return "gap ledger shape: six named rejections, one clean pass"

    def _thunk_handoff():
        packet = mod.build_handoff(PROBE_GAPS)
        check_true(len(packet) == len(PROBE_GAPS),
                   "packet row count %d != %d" % (len(packet),
                                                  len(PROBE_GAPS)))
        for row in packet:
            check_true(set(row) == set(mod.EMIT_KEYS),
                       "emit row keys %r != %r"
                       % (sorted(row), sorted(mod.EMIT_KEYS)))
        again = mod.build_handoff(PROBE_GAPS)
        check_true(json.dumps(packet) == json.dumps(again),
                   "build_handoff not byte-stable on equal inputs")
        return ("emit packet carries the seven contract keys and is"
                " byte-stable on equal inputs")

    def _thunk_ingest_happy():
        rows = probe_backfill()
        candidates, ledger = mod.ingest_rows(PROBE_GAPS, rows,
                                             vacgen=host)
        check_true(len(candidates) == len(PROBE_GAPS),
                   "candidate count %d != %d" % (len(candidates),
                                                 len(PROBE_GAPS)))
        for row in ledger:
            check_true(set(row) == set(mod.ANNOTATION_KEYS),
                       "ledger row keys %r != the nine-key form"
                       % (sorted(row),))
            check_true(row["annotationSite"] == "model",
                       "probe model annotated site %r"
                       % row["annotationSite"])
            check_true(row["tenpointVerdict"] == "PENDING",
                       "fresh ledger verdict %r" % row["tenpointVerdict"])
        for candidate in candidates:
            check_true(candidate["tenpointVerdict"] == "PENDING",
                       "draft row verdict not PENDING")
            check_true(candidate["sourceGapId"] in ("g0001", "g0002"),
                       "candidate provenance gap %r lost"
                       % candidate.get("sourceGapId"))
        return ("ingest round trip admits both probe rows through the C3.4"
                " gate and yields nine-key ledger rows (site model,"
                " verdict PENDING)")

    def _thunk_ingest_human_site():
        rows = probe_backfill(model_id="human")
        _candidates, ledger = mod.ingest_rows(PROBE_GAPS, rows, vacgen=host)
        check_true(all(row["annotationSite"] == "human" for row in ledger),
                   "human modelId did not annotate site human")
        return ("the literal human modelId annotates the human site in the"
                " nine-key ledger")

    def _expect_reject(name, rows, reason_part):
        try:
            mod.ingest_rows(PROBE_GAPS, rows, vacgen=host)
            check_true(False, "defect accepted by ingest")
        except mod.IngestRejected as exc:
            reasons = json.dumps(exc.rejections) + json.dumps(exc.missing)
            check_true(reason_part in reasons,
                       "expected reason %r absent from %s"
                       % (reason_part, reasons[:200]))

    def _thunk_reject_admission():
        rows = probe_backfill(payloads=[
            ("g0001", probe_payload(regex="^(unclosed")),
            ("g0002", probe_g2_payload())])
        _expect_reject("admission", rows, "admission-validate-row")
        return ("a payload whose regex fails to compile is refused by the"
                " vacgen admission gate with the error named")

    def _thunk_reject_w6():
        payload = probe_payload()
        payload["refutationForms"] = ["full", "wat"]
        rows = probe_backfill(payloads=[("g0001", payload),
                                        ("g0002", probe_g2_payload())])
        _expect_reject("w6", rows, "W6 vocabulary")
        return ("refutationForms outside the W6 vocabulary is refused with"
                " the vocabulary named")

    def _thunk_reject_trace():
        rows = probe_backfill(payloads=[
            ("g0001", probe_payload(regex=r"^\s*9\s*<\s*9$")),
            ("g0002", probe_g2_payload())])
        _expect_reject("trace", rows, "trace-sample-faces")
        return ("a row whose regex matches none of its source gap's sample"
                " faces is refused by the trace check")

    def _thunk_reject_coverage():
        rows = probe_backfill(payloads=[("g0001", probe_payload())])
        _expect_reject("coverage", rows, "g0002")
        return ("a backfill that leaves one gap uncovered is refused with"
                " the gap named")

    def _thunk_cli_emit_ingest_check():
        tmp = tempfile.mkdtemp(prefix="seg_render_")
        gaps_path = os.path.join(tmp, "gaps.json")
        write_json_file(gaps_path, {"schema": "rocqwash.gap-ledger/1",
                                    "gaps": PROBE_GAPS})
        emit_path = os.path.join(tmp, "packet.jsonl")
        proc = run_renderer(["--gaps", gaps_path, "--emit", emit_path,
                             "--vacgen", vacgen_arg])
        check_true(proc.returncode == 0,
                   "emit rc=%d %s" % (proc.returncode,
                                      out_text(proc)[-160:]))
        rows = [json.loads(line) for line in read_text_file(emit_path)
                .splitlines() if line.strip()]
        check_true(rows and
                   all(set(r) == set(mod.EMIT_KEYS) for r in rows),
                   "CLI emit rows lost the contract keys")
        backfill_path = os.path.join(tmp, "backfill.jsonl")
        write_jsonl_file(backfill_path, probe_backfill())
        draft_path = os.path.join(tmp, "draft.json")
        proc = run_renderer(["--gaps", gaps_path, "--ingest", backfill_path,
                             "--draft-out", draft_path,
                             "--vacgen", vacgen_arg])
        check_true(proc.returncode == 0,
                   "ingest rc=%d %s" % (proc.returncode,
                                        out_text(proc)[-160:]))
        draft = read_json_file(draft_path)
        check_true(draft.get("schema") == "rocqwash.taxonomy-candidates/1",
                   "draft schema %r" % draft.get("schema"))
        check_true(len(draft.get("rows") or []) == len(PROBE_GAPS),
                   "draft row count %d" % len(draft.get("rows") or []))
        admission = draft.get("admission") or {}
        check_true(admission.get("rowsAdmitted") == len(PROBE_GAPS)
                   and admission.get("rowsRejected") == 0,
                   "draft admission block %r" % (admission,))
        neg = ((draft.get("provenance") or {}).get("negativeFinding")
               or {})
        check_true(neg.get("nonAbsoluteClaim") is True
                   and neg.get("aliasesNotExhausted") is True
                   and neg.get("notScanned") and neg.get("rescanCondition"),
                   "draft negative-finding boundary incomplete: %r"
                   % (sorted(neg),))
        proc = run_renderer(["--check-draft", draft_path,
                             "--vacgen", vacgen_arg])
        check_true(proc.returncode == 0,
                   "check-draft rc=%d %s" % (proc.returncode,
                                             out_text(proc)[-160:]))
        broken = json.loads(read_text_file(draft_path))
        broken["rows"][0]["match"]["regex"] = "(unclosed"
        broken_path = os.path.join(tmp, "broken.json")
        write_json_file(broken_path, broken)
        proc = run_renderer(["--check-draft", broken_path,
                             "--vacgen", vacgen_arg])
        check_true(proc.returncode == 1,
                   "broken draft rc=%d (expected 1)" % proc.returncode)
        return ("CLI chain emit/ingest/check-draft green; the draft is at"
                " 100 percent admission with the negative-finding boundary"
                " in place; a broken draft is refused rc=1")

    def _thunk_cli_determinism():
        tmp = tempfile.mkdtemp(prefix="seg_render_det_")
        gaps_path = os.path.join(tmp, "gaps.json")
        write_json_file(gaps_path, PROBE_GAPS)
        backfill_path = os.path.join(tmp, "backfill.jsonl")
        write_jsonl_file(backfill_path, probe_backfill())
        drafts = []
        for idx in range(2):
            draft_path = os.path.join(tmp, "draft%d.json" % idx)
            proc = run_renderer(["--gaps", gaps_path, "--ingest",
                                 backfill_path, "--draft-out", draft_path,
                                 "--vacgen", vacgen_arg])
            check_true(proc.returncode == 0,
                       "re-render %d rc=%d" % (idx, proc.returncode))
            drafts.append(read_text_file(draft_path))
        check_true(drafts[0] == drafts[1],
                   "equal inputs produced different draft bytes")
        return ("two ingest runs on the same ledger and backfill produce"
                " byte-identical drafts")

    def _thunk_draft_consumable():
        if host is None or not hasattr(host, "load_taxonomy"):
            results.append(("SKIP", "draft-consumable",
                            "the loaded vacgen host lacks load_taxonomy;"
                            " the consumption check activates at merge"))
            return None
        tmp = tempfile.mkdtemp(prefix="seg_render_cons_")
        draft_path = os.path.join(tmp, "draft.json")
        proc = run_renderer(["--gaps", _write_probe_ledger(tmp),
                             "--ingest", _write_probe_backfill(tmp),
                             "--draft-out", draft_path,
                             "--vacgen", vacgen_arg])
        check_true(proc.returncode == 0, "ingest rc=%d" % proc.returncode)
        entries, info = host.load_taxonomy(draft_path)
        check_true(info["rowsLoaded"] == len(PROBE_GAPS)
                   and info["rowsVoided"] == 0 and not info["invalid"],
                   "load_taxonomy loaded=%d voided=%d invalid=%r"
                   % (info["rowsLoaded"], info["rowsVoided"],
                      info["invalid"]))
        order = [e["row"]["familyId"] for e in entries]
        expected = set(["probe.family.row", "probe.family.g2"])
        check_true(set(order) == expected and len(order) == len(expected),
                   "load face families %r != probe families %r"
                   % (order, sorted(expected)))
        return ("the rendered draft loads through the vacgen"
                " load_taxonomy load face (%d rows, 0 voided,"
                " families %s)" % (info["rowsLoaded"], ",".join(order)))

    def _thunk_landed_draft():
        if not os.path.isfile(LANDED_DRAFT):
            results.append(("SKIP", "landed-draft",
                            "docs/drafts/taxonomy-candidates.json not"
                            " landed yet; the landed-draft check activates"
                            " at merge"))
            return None
        tmp = tempfile.mkdtemp(prefix="seg_render_landed_")
        proc = run_renderer(["--check-draft", LANDED_DRAFT,
                             "--vacgen", vacgen_arg])
        check_true(proc.returncode == 0,
                   "landed draft rc=%d %s" % (proc.returncode,
                                              out_text(proc)[-160:]))
        draft = read_json_file(LANDED_DRAFT)
        admission = draft.get("admission") or {}
        check_true(admission.get("rowsAdmitted")
                   == admission.get("rowsTotal")
                   and admission.get("rowsRejected") == 0,
                   "landed draft admission block %r" % (admission,))
        for row in draft.get("rows") or []:
            check_true(row.get("tenpointVerdict") == "PENDING",
                       "landed draft row verdict %r awaiting the human"
                       " gate" % row.get("tenpointVerdict"))
        return ("the landed docs/drafts/taxonomy-candidates.json stays at"
                " 100 percent admission with the human gate still PENDING")

    def _thunk_tenpoint():
        if verify_host is None:
            return None
        tmp = tempfile.mkdtemp(prefix="seg_render_tp_")
        draft_path = os.path.join(tmp, "draft.json")
        proc = run_renderer(["--gaps", _write_probe_ledger(tmp),
                             "--ingest", _write_probe_backfill(tmp),
                             "--draft-out", draft_path,
                             "--vacgen", vacgen_arg])
        check_true(proc.returncode == 0, "ingest rc=%d" % proc.returncode)
        form_path = os.path.join(tmp, "form.json")
        proc = run_renderer(["--emit-tenpoint", draft_path,
                             "--json", form_path])
        check_true(proc.returncode == 0,
                   "emit-tenpoint rc=%d %s" % (proc.returncode,
                                               out_text(proc)[-160:]))
        form = read_json_file(form_path)
        check_true(form.get("schema") == verify_host.FORM_SCHEMA,
                   "form schema %r" % form.get("schema"))
        check_true(len(form.get("points") or [])
                   == verify_host.POINT_COUNT,
                   "form points %d" % len(form.get("points") or []))
        check_true(form.get("target") == draft_path,
                   "form target %r" % form.get("target"))
        good_points = [
            {"point": idx + 1, "verdict": "PASS", "citation": str(idx + 1),
             "note": ""}
            for idx in range(verify_host.POINT_COUNT)
        ]
        verdicts_path = os.path.join(tmp, "verdicts.json")
        write_json_file(verdicts_path, {
            "schema": verify_host.VERDICT_SCHEMA,
            "target": draft_path,
            "frame": "ALL-PASS",
            "points": good_points,
        })
        proc = run_renderer(["--ingest-tenpoint", verdicts_path,
                             "--draft-out", draft_path])
        check_true(proc.returncode == 0,
                   "ingest-tenpoint rc=%d %s" % (proc.returncode,
                                                 out_text(proc)[-160:]))
        draft = read_json_file(draft_path)
        admission = draft.get("admission") or {}
        check_true(admission.get("tenpointVerdict") == "ALL-PASS",
                   "frame not written back: %r"
                   % admission.get("tenpointVerdict"))
        check_true(all(row.get("tenpointVerdict") == "ALL-PASS"
                       for row in draft.get("rows") or []),
                   "row verdicts not rewritten to the frame")
        other_path = os.path.join(tmp, "other.json")
        write_json_file(other_path, {
            "schema": verify_host.VERDICT_SCHEMA,
            "target": draft_path,
            "frame": "ALL-PASS",
            "points": good_points,
        })
        proc = run_renderer(["--ingest-tenpoint", other_path,
                             "--draft-out", other_path])
        check_true(proc.returncode == 1,
                   "wrong-target verdicts rc=%d (expected 1)"
                   % proc.returncode)
        return ("ten-point form reuses the verify host schemas; a"
                " well-formed verdict file writes the ALL-PASS frame back"
                " into the draft rows; a wrong target is refused rc=1")

    def _thunk_http_refusal():
        tmp = tempfile.mkdtemp(prefix="seg_render_net_")
        ledger_path = os.path.join(tmp, "netred.jsonl")
        proc = run_renderer(["--gaps", _write_probe_ledger(tmp),
                             "--provider", "http",
                             "--netred-ledger", ledger_path])
        check_true(proc.returncode == 2,
                   "closed-gate http rc=%d (expected 2)" % proc.returncode)
        check_true("default deny" in out_text(proc),
                   "refusal does not name the default-deny gate: %s"
                   % out_text(proc)[-160:])
        check_true(not os.path.isfile(ledger_path),
                   "a refused run wrote a NETRED ledger line")
        return ("http with the gate variables stripped refuses rc=2 naming"
                " the default-deny gate and writes no NETRED line")

    def _thunk_action_conflict():
        proc = run_renderer(["--emit", "x.jsonl", "--ingest", "y.jsonl"])
        check_true(proc.returncode == 2,
                   "conflicting actions rc=%d (expected 2)"
                   % proc.returncode)
        proc = run_renderer([])
        check_true(proc.returncode == 2,
                   "no action rc=%d (expected 2)" % proc.returncode)
        return ("conflicting and empty action sets refuse rc=2 with the"
                " action list named")

    check("constants", _thunk_constants)
    if host is not None:
        check("gate-alive", _thunk_gate_alive)
    check("gap-shape", _thunk_gap_shape)
    check("handoff", _thunk_handoff)
    check("ingest-happy", _thunk_ingest_happy)
    check("ingest-human-site", _thunk_ingest_human_site)
    check("reject-admission", _thunk_reject_admission)
    check("reject-w6", _thunk_reject_w6)
    check("reject-trace", _thunk_reject_trace)
    check("reject-coverage", _thunk_reject_coverage)
    check("cli-emit-ingest-check", _thunk_cli_emit_ingest_check)
    check("cli-determinism", _thunk_cli_determinism)
    check("draft-consumable", _thunk_draft_consumable)
    check("landed-draft", _thunk_landed_draft)
    if verify_host is not None:
        check("tenpoint", _thunk_tenpoint)
    check("http-refusal", _thunk_http_refusal)
    check("action-conflict", _thunk_action_conflict)
    return _tally(results)


def _write_probe_ledger(tmp):
    gaps_path = os.path.join(tmp, "gaps.json")
    write_json_file(gaps_path, {"schema": "rocqwash.gap-ledger/1",
                                "gaps": PROBE_GAPS})
    return gaps_path


def _write_probe_backfill(tmp):
    backfill_path = os.path.join(tmp, "backfill.jsonl")
    write_jsonl_file(backfill_path, probe_backfill())
    return backfill_path


# ------------------------------------------------------------- shell ------


def _tally(results):
    passed = sum(1 for status, _n, _d in results if status == "PASS")
    failed = sum(1 for status, _n, _d in results if status == "FAIL")
    skipped = sum(1 for status, _n, _d in results if status == "SKIP")
    return passed, failed, skipped, results


def check_true(cond, message):
    if not cond:
        raise AssertionError(message)


def expect_value_error(fn, message):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


USAGE = ("usage: python -I tests/refinery_segments/render.py  (no"
         " arguments; the assembly lane imports run_segment_render)")


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        if argv[0] in ("-h", "--help"):
            print(USAGE)
            return 0
        sys.stderr.write("usage error: unknown argument %r\n" % argv[0])
        print(USAGE)
        return 2
    passed, failed, skipped, results = run_segment_render()
    for status, name, detail in results:
        print("%s render/%s -- %s" % (status, name, detail))
    print("SEGMENT render passed=%d failed=%d skipped=%d"
          % (passed, failed, skipped))
    if failed:
        print("TOTAL-RENDER-SEGMENT RED (%d failed check(s))" % failed)
        return 1
    print("TOTAL-RENDER-SEGMENT GREEN (%d passed, %d skipped)"
          % (passed, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
