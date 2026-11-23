#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pipeline_lite.py - gap-to-admission pipeline executor, D2-2 data layer.

Purpose.  Joins the standing chain into one run: scheduler_lite (trigger
  plan, verdict imported, never re-derived) -> gap_cluster (clusters) ->
  row_render (emit packet, ingest backfill, draft rows carry
  tenpointVerdict PENDING).  Automation ends at the first code-layer
  boundary: ten-point review, taxonomy row integration, apply passes and
  auto_round commit/approve stay human-gated, never composed (D2-2, open
  item 2).
Interface.  `py -I tools/pipeline_lite.py run [--plan FILE | re-derive via
  scheduler_lite] [--gap-ledger P]... [--reports P]... [--rounds P]
  [--autonomy P] [--state P] [--ef-marker P] [--threshold N]
  [--now-utc ISO8601Z] [--gap-out/--render-gaps/--packet-out FILE]
  [--backfill/--draft-out FILE] [--b-gate-audit P] [--policy-ref S]
  [--stop-at {data,human}] [--json]` or --selftest; one summary line
  (--json: the rocqwash.pipeline-lite.run/1 run report).  Quiet or
  blocked writes nothing; pending stops are data (exit 0); report paths
  are basenames only (no wall clock).
Dependencies.  Python 3 standard library only; subprocess calls to the
  sibling scheduler_lite.py, gap_cluster.py and row_render.py (absent
  sibling exits 9; a sibling failure exits with the sibling's code); the
  report carries docs/b-gate-audit.json read-only when present.
Evidence.  --selftest tmp vectors: quiet/blocked/plan-import no-ops, due
  data steps, ingest-to-PENDING with the gate boundary asserted, stop-at
  matrix, fail-loud exit 9, determinism, zero-network hook, source probe.
Exit-codes.  0 = the run face answered (quiet, blocked, pending-backfill
  and pending-human are data); 1 = selftest red or a gate refusal;
  2 = usage; 9 = corrupt or explicitly missing input.
"""

import argparse
import json
import os
import re
import subprocess
import sys

PROG = "pipeline_lite"
TOOL_VERSION = "1"
SCHEMA = "rocqwash.pipeline-lite.run/1"
PLAN_SCHEMA = "rocqwash.scheduler-lite.plan/1"
GAP_LEDGER_SCHEMA = "rocqwash.gap-ledger/1"
AGG_SCHEMA = "rocqwash-gap-ledger/1"
DRAFT_SCHEMA = "rocqwash.taxonomy-candidates/1"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VERDICT_QUIET = "quiet"
VERDICT_DUE = "due"
VERDICT_BLOCKED = "blocked"
PLAN_VERDICTS = (VERDICT_QUIET, VERDICT_DUE, VERDICT_BLOCKED)

DEFAULT_GAP_LEDGER = ("docs", "gap-feed-ledger.jsonl")
DEFAULT_REPORTS_DIR = ("docs", "vacgen-reports")
DEFAULT_GAP_OUT = ("docs", "gap-ledger-latest.json")
DEFAULT_RENDER_GAPS = ("docs", "drafts", "gap-ledger-render-input.json")
DEFAULT_PACKET_OUT = ("docs", "drafts", "render-packet-latest.jsonl")
DEFAULT_DRAFT_OUT = ("docs", "drafts", "taxonomy-candidates-pipeline.json")
DEFAULT_B_GATE_AUDIT = ("docs", "b-gate-audit.json")

# The D2-2 gate-strength boundary (review card open item 2): the run face
# composes commands for DATA_STEPS only.  Every face named in
# CODE_LAYER_FACES stays human-gated; the selftest asserts on every report
# the vectors produce that no code-layer face was composed and that ingested
# rows carry tenpointVerdict PENDING only.
DATA_STEPS = ("plan", "cluster", "render-gaps", "emit", "ingest")
CODE_LAYER_FACES = (
    "row_render --emit-tenpoint (the review form goes out to the human)",
    "row_render --ingest-tenpoint (consumes human verdicts)",
    "tools/taxonomy.json row integration (a human PR face)",
    "apply pass (tools/jargon_apply.py or a future per-family face)",
    "auto_round commit / approve / anchor --promote / rollback revert",
)
GATE_RULING = ("auto-approval is limited to the data layer (review card "
               "direction-review-d1d5-20261123, rows D2-2 and open item 2); "
               "code-layer faces stay human-gated and are never composed "
               "by this tool")
DEFAULT_POLICY_REF = ("layer-law first-admission ref: D2-2 gate-strength "
                      "ruling (direction-review-d1d5-20261123): data-layer "
                      "automation drafts PENDING rows only; the human "
                      "ten-point review precedes any admission")

NETWORK_ATTEMPT_EVENTS = ("socket.connect", "urllib.Request")
_CJK_RE = re.compile(u"[\u4e00-\u9fff\u3400-\u4dbf]")
_EM_DASH = u"\u2014"

STOP_BACKFILL = "external model-side backfill"
STOP_HUMAN = "human ten-point review"


class PipelineInputError(Exception):
    """Corrupt or explicitly missing input (the exit-9 face)."""


def fail(message, code):
    sys.stderr.write(PROG + ": " + message + "\n")
    raise SystemExit(code)


def default_path(parts):
    return os.path.join(REPO_ROOT, *parts)


def basename_of(path):
    return os.path.basename(str(path).replace("\\", "/")) if path else None


def read_json_doc(path, label):
    """Read one JSON document (fail loud on corrupt or absent content)."""
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except OSError as exc:
        raise PipelineInputError("%s is unreadable: %s" % (label, exc))
    except ValueError as exc:
        raise PipelineInputError("%s is not valid JSON: %s" % (label, exc))
    if not isinstance(doc, dict):
        raise PipelineInputError("%s is not a JSON object" % label)
    return doc


def write_text(path, text):
    """One data write face; unwritable output is fail loud (exit 9)."""
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    except OSError as exc:
        fail("output not writable: %s (%s)" % (path, exc), 9)


def run_tool(name, tail):
    """Run one sibling tool face; a nonzero sibling exit propagates."""
    path = os.path.join(REPO_ROOT, "tools", name)
    if not os.path.isfile(path):
        fail("sibling tools/%s is absent" % name, 9)
    proc = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", path]
        + [str(item) for item in tail],
        capture_output=True)
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", "replace").strip()
        lines = [line for line in err.splitlines() if line][-3:]
        suffix = ": " + " | ".join(lines) if lines else ""
        sys.stderr.write("%s: tools/%s exited rc=%d%s\n"
                         % (PROG, name, proc.returncode, suffix))
        raise SystemExit(proc.returncode)
    return proc


def first_stdout_value(text, key):
    """The value of key= on the first stdout line that carries it."""
    match = re.search(key + r"=(\S+)", text or "")
    return match.group(1) if match else None


def step_record(step, tool, artifact, note):
    return {"step": step, "tool": tool, "exit": 0,
            "artifact": basename_of(artifact), "note": note}


def stop_record(face, layer, note, command=None):
    return {"face": face, "layer": layer, "note": note, "command": command}


# ------------------------------------------------------------- plan face ----

PLAN_PASSTHROUGH = (
    ("--gap-ledger", "gap_ledger", True),
    ("--reports", "reports", True),
    ("--rounds", "rounds", False),
    ("--autonomy", "autonomy", False),
    ("--state", "state", False),
    ("--ef-marker", "ef_marker", False),
    ("--threshold", "threshold", False),
    ("--interval-seconds", "interval_seconds", False),
    ("--now-utc", "now_utc", False),
)


def read_plan_document(path):
    """Validate one --plan document (schema, verdict, reasons shapes)."""
    if not os.path.isfile(path):
        raise PipelineInputError("plan path %s does not exist" % path)
    doc = read_json_doc(path, "plan document")
    if doc.get("schema") != PLAN_SCHEMA:
        raise PipelineInputError("plan schema %r instead of %s"
                                 % (doc.get("schema"), PLAN_SCHEMA))
    if doc.get("verdict") not in PLAN_VERDICTS:
        raise PipelineInputError("plan verdict %r outside %s"
                                 % (doc.get("verdict"), "/".join(PLAN_VERDICTS)))
    if not isinstance(doc.get("reasons") or [], list):
        raise PipelineInputError("plan reasons is not a list")
    return doc


def derive_plan(args):
    """The plan document: read --plan when given, else re-derive it through
    scheduler_lite (the verdict is imported, never re-implemented)."""
    if args.plan:
        doc = read_plan_document(args.plan)
        return doc, "plan document %s (verdict imported)" % basename_of(args.plan)
    tail = ["plan", "--json"]
    for flag, dest, _repeatable in PLAN_PASSTHROUGH:
        value = getattr(args, dest)
        if not value:
            continue
        items = list(value) if isinstance(value, list) else [value]
        for item in items:
            tail += [flag, str(item)]
    proc = run_tool("scheduler_lite.py", tail)
    try:
        doc = json.loads((proc.stdout or b"").decode("utf-8"))
    except ValueError as exc:
        raise PipelineInputError("scheduler_lite plan stdout is not valid "
                                 "JSON: %s" % exc)
    if not isinstance(doc, dict) or doc.get("schema") != PLAN_SCHEMA:
        raise PipelineInputError("scheduler_lite plan stdout is not a %s "
                                 "document" % PLAN_SCHEMA)
    return doc, "verdict re-derived through scheduler_lite plan (dry-run)"


# ---------------------------------------------------------- cluster face ----

def cluster_input_faces(args):
    """The gap_cluster input faces: explicitly flagged paths ride as given
    (the sibling validates them); a default face rides only when present
    (default-absent is a data state, mirroring scheduler_lite)."""
    ledgers = list(args.gap_ledger)
    reports = list(args.reports)
    if not ledgers:
        path = default_path(DEFAULT_GAP_LEDGER)
        if os.path.exists(path):
            ledgers.append(path)
    if not reports:
        path = default_path(DEFAULT_REPORTS_DIR)
        if os.path.exists(path):
            reports.append(path)
    return ledgers, reports


def run_cluster(args, gap_out, steps):
    """The cluster step: gap_cluster --out, then the aggregate is read back."""
    ledgers, reports = cluster_input_faces(args)
    tail = ["--out", gap_out]
    for path in ledgers:
        tail += ["--ledger", path]
    for path in reports:
        tail += ["--reports", path]
    proc = run_tool("gap_cluster.py", tail)
    aggregate = read_json_doc(gap_out, "gap ledger aggregate")
    if aggregate.get("schema") != AGG_SCHEMA:
        raise PipelineInputError("aggregate schema %r instead of %s"
                                 % (aggregate.get("schema"), AGG_SCHEMA))
    totals = aggregate.get("totals") or {}
    note = "clusters=%d gaps=%d" % (len(aggregate.get("clusters") or []),
                                    totals.get("gaps") or 0)
    _ = proc
    steps.append(step_record("cluster", "gap_cluster.py", gap_out, note))
    return aggregate


def clusters_to_gaps(aggregate, policy_ref, gap_out):
    """Transform the aggregate clusters into row_render gap rows (one gap
    per cluster; deterministic order and content; the layer-law
    policyPrecheckRef is stamped on every row)."""
    gaps = []
    for index, cluster in enumerate(aggregate.get("clusters") or [], 1):
        gaps.append({
            "gapId": "gap-%04d" % index,
            "cluster": cluster.get("shapeKey"),
            "occurrences": cluster.get("count"),
            "files": sorted({m.get("file")
                             for m in cluster.get("members") or []
                             if m.get("file")}),
            "sampleFaces": list(cluster.get("variants") or []),
            "status": "clustered",
            "notes": "pipeline_lite aggregation of %s (%s)" % (
                basename_of(gap_out), aggregate.get("inputFingerprint")),
            "policyPrecheckRef": policy_ref,
        })
    return gaps


def run_render_gaps(args, aggregate, gap_out, steps):
    """The render-gaps step: write the row_render gap input (in-process)."""
    render_gaps = args.render_gaps or default_path(DEFAULT_RENDER_GAPS)
    policy_ref = args.policy_ref or DEFAULT_POLICY_REF
    gaps = clusters_to_gaps(aggregate, policy_ref, gap_out)
    doc = {"schema": GAP_LEDGER_SCHEMA, "source": basename_of(gap_out),
           "inputFingerprint": aggregate.get("inputFingerprint"),
           "gaps": gaps}
    write_text(render_gaps, json.dumps(doc, sort_keys=True, indent=2,
                                       ensure_ascii=False) + "\n")
    steps.append(step_record("render-gaps", "pipeline_lite.py", render_gaps,
                             "gaps=%d policyPrecheckRef=stamped" % len(gaps)))
    return render_gaps


# ---------------------------------------------------- render + ingest ----

def run_emit(render_gaps, packet_out, steps):
    """The emit step: row_render --emit (zero network, handoff provider)."""
    proc = run_tool("row_render.py",
                    ["--gaps", render_gaps, "--emit", packet_out])
    text = (proc.stdout or b"").decode("utf-8", "replace")
    steps.append(step_record("emit", "row_render.py", packet_out,
                             "gaps=%s" % (first_stdout_value(text, "gaps")
                                          or "unknown")))


def run_ingest(args, render_gaps, draft_out, steps):
    """The ingest step: row_render --ingest --draft-out; rows enter PENDING;
    this is the pipeline's last unattended step."""
    proc = run_tool("row_render.py",
                    ["--gaps", render_gaps, "--ingest", args.backfill,
                     "--draft-out", draft_out])
    text = (proc.stdout or b"").decode("utf-8", "replace")
    steps.append(step_record("ingest", "row_render.py", draft_out,
                             "admitted=%s rowsPending"
                             % (first_stdout_value(text, "admitted")
                                or "unknown")))
    return stop_record(
        STOP_HUMAN, "code",
        "rows carry tenpointVerdict PENDING; the code layer starts here "
        "(ten-point verdicts, taxonomy row integration, apply pass, commit "
        "stay human-gated)",
        command="python3 -I tools/row_render.py --emit-tenpoint %s "
                "--draft-out %s" % (basename_of(draft_out),
                                    basename_of(draft_out)))


# ---------------------------------------------------------- b-gate face ----

def read_b_gate(args):
    """The per-window b-gate counter: the standing audit file read-only
    (absent default is a data state; an explicitly flagged absent path is
    an exit-9 input error)."""
    explicit = args.b_gate_audit is not None
    path = args.b_gate_audit or default_path(DEFAULT_B_GATE_AUDIT)
    if not os.path.isfile(path):
        if explicit:
            raise PipelineInputError("b-gate audit path %s does not exist"
                                     % path)
        return None, ("b-gate audit file absent (run tools/b_gate_audit.py"
                      " to cast it)")
    doc = read_json_doc(path, "b-gate audit file")
    if not isinstance(doc.get("verdict"), str):
        raise PipelineInputError("b-gate audit file carries no verdict")
    face = {"source": basename_of(path), "verdict": doc["verdict"],
            "remainingToB": doc.get("remaining_to_b"),
            "readyClasses": doc.get("ready_classes") or []}
    return face, None


# ----------------------------------------------------------- run report ----

def build_report(args, plan, steps, next_step, b_gate, b_gate_note):
    return {
        "schema": SCHEMA,
        "tool": {"name": PROG, "version": TOOL_VERSION},
        "now": plan.get("now"),
        "verdict": plan.get("verdict"),
        "reasons": plan.get("reasons") or [],
        "stopAt": args.stop_at,
        "steps": steps,
        "nextStep": next_step,
        "bGate": b_gate,
        "bGateNote": b_gate_note,
        "gateRuling": GATE_RULING,
        "dataLayerSteps": list(DATA_STEPS),
        "codeLayerFaces": list(CODE_LAYER_FACES),
        "writeFace": "data faces only; code-layer faces are never composed",
        "zeroNetwork": True,
    }


def render_line(report):
    names = ",".join(step["step"] for step in report["steps"])
    nxt = report["nextStep"]
    tail = ("next=%s" % nxt["face"]) if nxt else "next=none"
    gate = report["bGate"]
    gate_part = (" bGate=%s/%s" % (gate["verdict"], gate["remainingToB"])
                 if gate else "")
    return ("pipeline-lite run: verdict=%s stopAt=%s steps=[%s] %s%s"
            % (report["verdict"], report["stopAt"], names, tail, gate_part))


def emit_output(args, report, tool_lines):
    if args.json:
        sys.stdout.write(json.dumps(report, sort_keys=True, indent=2,
                                    ensure_ascii=False) + "\n")
        return
    sys.stdout.write(render_line(report) + "\n")
    for line in tool_lines:
        if line:
            sys.stdout.write("  | %s\n" % line)


# ------------------------------------------------------------- run face ----

def run_face(args):
    steps = []
    tool_lines = []
    plan, plan_note = derive_plan(args)
    steps.append({"step": "plan", "tool": "scheduler_lite.py", "exit": 0,
                  "artifact": None, "note": plan_note})
    b_gate, b_gate_note = read_b_gate(args)
    verdict = plan.get("verdict")
    if verdict != VERDICT_DUE:
        # quiet or blocked: write nothing, carry the reason tokens (data).
        report = build_report(args, plan, steps, None, b_gate, b_gate_note)
        emit_output(args, report, tool_lines)
        return 0
    gap_out = args.gap_out or default_path(DEFAULT_GAP_OUT)
    aggregate = run_cluster(args, gap_out, steps)
    totals = aggregate.get("totals") or {}
    if not totals.get("gaps"):
        report = build_report(
            args, plan, steps,
            stop_record("zero gap-class clusters", "data",
                        "nothing to render (a zero-cluster data state); "
                        "check the gap feed inputs"),
            b_gate, b_gate_note)
        emit_output(args, report, tool_lines)
        return 0
    render_gaps = run_render_gaps(args, aggregate, gap_out, steps)
    packet_out = args.packet_out or default_path(DEFAULT_PACKET_OUT)
    run_emit(render_gaps, packet_out, steps)
    if args.stop_at == "data":
        report = build_report(
            args, plan, steps,
            stop_record(STOP_BACKFILL, "data",
                        "stop-at data: the packet is on disk; supply "
                        "--backfill FILE and rerun with the default "
                        "--stop-at human"),
            b_gate, b_gate_note)
        emit_output(args, report, tool_lines)
        return 0
    if not args.backfill:
        report = build_report(
            args, plan, steps,
            stop_record(STOP_BACKFILL, "data",
                        "no backfill supplied (pending-backfill is data); "
                        "fill the packet and rerun with --backfill FILE"),
            b_gate, b_gate_note)
        emit_output(args, report, tool_lines)
        return 0
    if not os.path.isfile(args.backfill):
        raise PipelineInputError("explicit backfill path %s does not exist"
                                 % args.backfill)
    draft_out = args.draft_out or default_path(DEFAULT_DRAFT_OUT)
    next_step = run_ingest(args, render_gaps, draft_out, steps)
    report = build_report(args, plan, steps, next_step, b_gate, b_gate_note)
    emit_output(args, report, tool_lines)
    return 0


# ------------------------------------------------------------ selftest ----

def selftest():
    """Fixture vectors on tmp inputs; fail loud, one line per vector."""
    import shutil
    import tempfile

    tool = os.path.abspath(__file__)
    failures = []
    reports = {}

    # V18 instrument: an audit hook records network-attempt events for the
    # whole selftest run of this process.  The sibling tool faces run in
    # child processes and are guarded by their own postures (row_render
    # handoff provider default-deny, gap_cluster pure file aggregation,
    # scheduler_lite dry-run); the criterion here observes this process.
    net_events = []
    sys.addaudithook(
        lambda event, args_: net_events.append(event)
        if event in NETWORK_ATTEMPT_EVENTS
        else None
    )

    def check(name, fn):
        try:
            fn()
        except Exception as exc:  # vector boundary: report, do not raise
            failures.append("%s -- %s: %r" % (name, type(exc).__name__, exc))
        else:
            print("PASS %s" % name)

    def run_cli(argv):
        return subprocess.run(
            [sys.executable, "-I", "-X", "utf8", tool]
            + [str(item) for item in argv],
            capture_output=True)

    def write(path, text):
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    # Fixtures mirror the repo shapes (copied from the standing scheduler
    #_lite and row_render selftest corpora): one gap-class feed row, the
    # measured round tail pair, the standing gear config, an all-green EF
    # marker, and a backfill row that passes the vacgen admission gate.
    GAP_LINE = json.dumps({
        "schema": "rocqwash-exp/1", "id": "fix-001", "ts": "T0",
        "tool": "fixture", "batch": "b",
        "points": "uncovered face (TODO-SEAT counted, no silent "
                  "degradation): (1 / 2 : R) < z.abs",
        "evidence": "status=todo_seat", "fingerprint": "4" * 64}) + "\n"
    ROUND_ROWS = (
        json.dumps({"schema": "rocqwash-round/1", "round_id": 1,
                    "timestamp_utc": "2026-11-15T04:49:24Z",
                    "verify_rc": 0, "mode": "auto"}) + "\n"
        + json.dumps({"schema": "rocqwash-round/1", "round_id": 2,
                      "timestamp_utc": "2026-11-15T16:05:30Z",
                      "verify_rc": 0, "mode": "auto"}) + "\n")
    AUTONOMY = json.dumps({"mode": "auto", "admission_threshold": 0.8}) + "\n"
    STATE = json.dumps({"schema": "rocqwash.round-state/1",
                        "admitted_classes": [
                            {"class": "jargon", "confidence": 1.0,
                             "basis": "fixture gear auto"}]}) + "\n"
    B_GATE = json.dumps({"schema": "rocqwash.b-gate/1", "verdict":
                         "not-ready", "remaining_to_b": 3,
                         "ready_classes": []}) + "\n"

    def probe_payload():
        return {
            "schemaVersion": 2,
            "familyId": "probe.family.pipeline",
            "cluster": "pipeline-probe",
            "match": {"target": "assumption.type",
                      "regex": r"1 / 2 : R", "flags": ""},
            "priority": 40,
            "confidence": "MID",
            "witnessStrategy": "probe-point bite with a declared boundary "
                               "block",
            "witnessTemplate": {
                "bites": ["theorem {p}_probe : True := trivial"],
                "boundary": {"kind": "numeric-constant",
                             "template": "{num} / {den}"}},
            "mathlibAnchors": [{"symbol": "Probe.sym",
                                "relPath": "Mathlib/X.lean", "line": 1}],
            "refutationForms": ["full", "point"],
            "boundaryApplicability": "numeric-constant",
            "gapKeywords": ["modulus"],
            "notes": "pipeline_lite selftest probe row",
        }

    def backfill_rows():
        return [json.dumps({
            "gapId": "gap-0001", "row": probe_payload(),
            "modelId": "probe-renderer",
            "promptTemplateRef": "prompts/render-row-v1",
            "timestampUtc": "2026-11-20T00:00:00Z"}) + "\n"]

    def make_fixtures(root, gap_text=GAP_LINE):
        os.makedirs(root, exist_ok=True)
        paths = {
            "gap": os.path.join(root, "gap.jsonl"),
            "rounds": os.path.join(root, "rounds.jsonl"),
            "autonomy": os.path.join(root, "autonomy.json"),
            "state": os.path.join(root, "state.json"),
            "marker": os.path.join(root, "ef-done.marker"),
            "bgate": os.path.join(root, "b-gate.json"),
            "gap_out": os.path.join(root, "gap-ledger-latest.json"),
            "render_gaps": os.path.join(root, "render-input.json"),
            "packet": os.path.join(root, "packet.jsonl"),
            "draft": os.path.join(root, "draft.json"),
            "backfill": os.path.join(root, "backfill.jsonl"),
        }
        write(paths["gap"], gap_text)
        write(paths["rounds"], ROUND_ROWS)
        write(paths["autonomy"], AUTONOMY)
        write(paths["state"], STATE)
        write(paths["marker"], "abcdef1234567890\n")
        write(paths["bgate"], B_GATE)
        write(paths["backfill"], "".join(backfill_rows()))
        return paths

    NOW = "2026-11-17T00:00:00Z"

    def run_scenarios(paths, extra=(), json_mode=True):
        argv = ["run", "--gap-ledger", paths["gap"],
                "--rounds", paths["rounds"], "--ef-marker", paths["marker"],
                "--autonomy", paths["autonomy"], "--state", paths["state"],
                "--now-utc", NOW, "--b-gate-audit", paths["bgate"],
                "--gap-out", paths["gap_out"],
                "--render-gaps", paths["render_gaps"],
                "--packet-out", paths["packet"],
                "--draft-out", paths["draft"]] + list(extra)
        if json_mode:
            argv.append("--json")
        return run_cli(argv)

    def read_report(proc):
        assert proc.returncode == 0, proc.stderr[-400:]
        return json.loads(proc.stdout.decode("utf-8"))

    def v_quiet_noop():
        root = os.path.join(TMP, "quiet")
        paths = make_fixtures(root, gap_text="")
        proc = run_scenarios(paths)
        report = read_report(proc)
        assert report["verdict"] == "quiet", report["verdict"]
        assert report["steps"] and report["steps"][0]["step"] == "plan"
        assert len(report["steps"]) == 1, report["steps"]
        assert report["nextStep"] is None, report["nextStep"]
        assert report["bGate"]["verdict"] == "not-ready", report["bGate"]
        for key in ("gap_out", "render_gaps", "packet", "draft"):
            assert not os.path.exists(paths[key]), key
        reports["quiet"] = report

    def v_blocked_noop():
        root = os.path.join(TMP, "blocked")
        paths = make_fixtures(root)
        argv = ["run", "--gap-ledger", paths["gap"],
                "--rounds", paths["rounds"],
                "--ef-marker", os.path.join(root, "absent.marker"),
                "--autonomy", paths["autonomy"], "--state", paths["state"],
                "--now-utc", NOW, "--b-gate-audit", paths["bgate"],
                "--gap-out", paths["gap_out"], "--json"]
        proc = run_cli(argv)
        report = read_report(proc)
        assert report["verdict"] == "blocked", report["verdict"]
        assert report["reasons"] == ["ef-gate-closed"], report["reasons"]
        assert len(report["steps"]) == 1, report["steps"]
        assert not os.path.exists(paths["gap_out"]), "wrote on blocked"
        reports["blocked"] = report

    def v_plan_import_noop():
        root = os.path.join(TMP, "planimport")
        os.makedirs(root, exist_ok=True)
        plan_path = os.path.join(root, "plan.json")
        write(plan_path, json.dumps({
            "schema": PLAN_SCHEMA, "tool": {"name": "scheduler_lite",
                                            "version": "1"},
            "now": NOW, "verdict": "quiet", "reasons": [],
            "fireReady": False, "dryRun": True}) + "\n")
        packet = os.path.join(root, "packet.jsonl")
        proc = run_cli(["run", "--plan", plan_path,
                        "--packet-out", packet, "--json"])
        report = read_report(proc)
        assert report["verdict"] == "quiet", report["verdict"]
        assert report["steps"][0]["note"].startswith("plan document"), \
            report["steps"]
        assert not os.path.exists(packet), "wrote on plan import"
        reports["plan-import"] = report

    def v_due_pending_backfill():
        root = os.path.join(TMP, "pendingbf")
        paths = make_fixtures(root)
        proc = run_scenarios(paths)
        report = read_report(proc)
        assert report["verdict"] == "due", report["verdict"]
        names = [step["step"] for step in report["steps"]]
        assert names == ["plan", "cluster", "render-gaps", "emit"], names
        assert not os.path.exists(paths["draft"]), "draft without backfill"
        assert report["nextStep"]["face"] == STOP_BACKFILL, report["nextStep"]
        assert report["nextStep"]["layer"] == "data", report["nextStep"]
        with open(paths["render_gaps"], encoding="utf-8") as fh:
            gaps_doc = json.load(fh)
        assert gaps_doc["schema"] == GAP_LEDGER_SCHEMA, gaps_doc["schema"]
        gap_row = gaps_doc["gaps"][0]
        assert gap_row["gapId"] == "gap-0001", gap_row
        assert gap_row["policyPrecheckRef"] == DEFAULT_POLICY_REF, gap_row
        assert gap_row["status"] == "clustered", gap_row
        assert gap_row["sampleFaces"], gap_row
        assert os.path.exists(paths["packet"]), "packet missing"
        reports["pending-backfill"] = report

    def v_due_ingest_pending():
        root = os.path.join(TMP, "ingest")
        paths = make_fixtures(root)
        proc = run_scenarios(paths,
                             ["--backfill", paths["backfill"]])
        report = read_report(proc)
        assert report["verdict"] == "due", report["verdict"]
        names = [step["step"] for step in report["steps"]]
        assert names == ["plan", "cluster", "render-gaps", "emit",
                         "ingest"], names
        with open(paths["draft"], encoding="utf-8") as fh:
            draft = json.load(fh)
        assert draft["schema"] == DRAFT_SCHEMA, draft["schema"]
        assert draft["rows"], "empty draft"
        assert all(row["tenpointVerdict"] == "PENDING"
                   for row in draft["rows"]), "non-PENDING row in the draft"
        nxt = report["nextStep"]
        assert nxt["face"] == STOP_HUMAN and nxt["layer"] == "code", nxt
        assert "--emit-tenpoint" in nxt["command"], nxt
        assert report["bGate"] == {"source": "b-gate.json",
                                   "verdict": "not-ready",
                                   "remainingToB": 3,
                                   "readyClasses": []}, report["bGate"]
        reports["ingest"] = report

    def v_gate_boundary():
        # The D2-2 boundary asserted over every report the vectors cast:
        # composed steps are data steps only and carry no code-layer face
        # token; the human-facing nextStep pointer may NAME the boundary
        # (its command composes only the review-form emission).
        for name in ("quiet", "blocked", "plan-import", "pending-backfill",
                     "ingest"):
            report = reports[name]
            steps = report["steps"]
            assert all(step["step"] in DATA_STEPS for step in steps), name
            tools = {step["tool"] for step in steps}
            assert tools <= {"scheduler_lite.py", "gap_cluster.py",
                             "pipeline_lite.py", "row_render.py"}, name
            for token in ("ingest-tenpoint", "auto_round", "jargon_apply",
                          "approve", "commit"):
                assert token not in json.dumps(steps), (name, token)
            nxt = report.get("nextStep")
            if nxt:
                assert nxt["layer"] in ("data", "code"), nxt
                command = nxt.get("command") or ""
                for token in ("ingest-tenpoint", "auto_round",
                              "jargon_apply", "approve", "commit"):
                    assert token not in command, (name, token)
        nxt = reports["ingest"]["nextStep"]
        assert nxt["face"] == STOP_HUMAN and nxt["layer"] == "code", nxt
        assert "--emit-tenpoint" in nxt["command"], "boundary pointer lost"
        assert reports["ingest"]["codeLayerFaces"], "face register lost"
        assert reports["ingest"]["gateRuling"] == GATE_RULING, "ruling lost"

    def v_stop_at_data():
        root = os.path.join(TMP, "stopdata")
        paths = make_fixtures(root)
        proc = run_scenarios(paths, ["--backfill", paths["backfill"],
                                     "--stop-at", "data"])
        report = read_report(proc)
        names = [step["step"] for step in report["steps"]]
        assert "ingest" not in names, names
        assert not os.path.exists(paths["draft"]), "draft on stop-at data"
        assert report["nextStep"]["face"] == STOP_BACKFILL, report["nextStep"]

    def v_fail_loud():
        root = os.path.join(TMP, "fail")
        paths = make_fixtures(root)
        # Every probe pins all four output faces into tmp: a due verdict on
        # the fixtures must never resolve a repo default write path.  The
        # b-gate audit flag stays out of the shared tail: the explicit-face
        # probe relies on its own flag being the last occurrence.
        out_flags = ["--gap-out", paths["gap_out"],
                     "--render-gaps", paths["render_gaps"],
                     "--packet-out", paths["packet"],
                     "--draft-out", paths["draft"]]
        corrupt = os.path.join(root, "corrupt.json")
        write(corrupt, "{not json}")
        proc = run_cli(["run", "--plan", corrupt, "--json"] + out_flags)
        assert proc.returncode == 9, proc.returncode
        wrong = os.path.join(root, "wrong.json")
        write(wrong, json.dumps({"schema": "other/1", "verdict": "due",
                                 "reasons": []}))
        proc = run_cli(["run", "--plan", wrong, "--json"] + out_flags)
        assert proc.returncode == 9, proc.returncode
        proc = run_cli(["run", "--gap-ledger", paths["gap"],
                        "--rounds", paths["rounds"],
                        "--ef-marker", paths["marker"],
                        "--autonomy", paths["autonomy"],
                        "--state", paths["state"], "--now-utc", NOW,
                        "--backfill", os.path.join(root, "absent.jsonl"),
                        "--b-gate-audit", paths["bgate"],
                        "--json"] + out_flags)
        assert proc.returncode == 9, proc.returncode
        proc = run_cli(["run", "--gap-ledger", os.path.join(root, "no.jsonl"),
                        "--now-utc", NOW, "--json"] + out_flags)
        assert proc.returncode == 9, proc.returncode
        proc = run_cli(["run", "--b-gate-audit",
                        os.path.join(root, "no-audit.json"),
                        "--gap-ledger", paths["gap"], "--now-utc", NOW,
                        "--json"] + out_flags)
        assert proc.returncode == 9, proc.returncode

    def v_determinism():
        out = []
        for tag in ("d1", "d2"):
            root = os.path.join(TMP, tag)
            paths = make_fixtures(root)
            proc = run_scenarios(paths, ["--backfill", paths["backfill"]])
            assert proc.returncode == 0, proc.stderr[-300:]
            out.append(proc.stdout)
        assert out[0] == out[1], "run report bytes differ across reruns"

    def v_zero_network():
        assert not net_events, net_events

    def v_repo_default_faces_untouched():
        # The four default write faces: an existing mtime must be unchanged
        # and an absent face must stay absent after the whole vector set.
        for parts in (DEFAULT_GAP_OUT, DEFAULT_RENDER_GAPS,
                      DEFAULT_PACKET_OUT, DEFAULT_DRAFT_OUT):
            path = default_path(parts)
            before = REPO_FACES_BEFORE.get(path, "absent")
            if not os.path.exists(path):
                assert before == "absent", (path, "appeared")
                continue
            assert before != "absent", (path, "created")
            assert before == os.path.getmtime(path), (path, "mtime moved")

    def v_source_language_surface():
        with open(tool, encoding="utf-8") as fh:
            text = fh.read()
        assert not _CJK_RE.search(text), "CJK found in source"
        assert _EM_DASH not in text, "em-dash found in source"

    REPO_FACES_BEFORE = {}
    for parts in (DEFAULT_GAP_OUT, DEFAULT_RENDER_GAPS,
                  DEFAULT_PACKET_OUT, DEFAULT_DRAFT_OUT):
        path = default_path(parts)
        if os.path.exists(path):
            REPO_FACES_BEFORE[path] = os.path.getmtime(path)

    TMP = tempfile.mkdtemp(prefix="pipeline_lite_selftest_")
    try:
        check("quiet-noop", v_quiet_noop)
        check("blocked-noop", v_blocked_noop)
        check("plan-import-noop", v_plan_import_noop)
        check("due-pending-backfill", v_due_pending_backfill)
        check("due-ingest-pending-gate-stop", v_due_ingest_pending)
        check("gate-boundary-data-layer-only", v_gate_boundary)
        check("stop-at-data-matrix", v_stop_at_data)
        check("fail-loud-exit9", v_fail_loud)
        check("determinism-basename-report", v_determinism)
        check("repo-default-faces-untouched", v_repo_default_faces_untouched)
        check("zero-network-audit-hook", v_zero_network)
        check("source-cjk-free-em-dash-free", v_source_language_surface)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    if failures:
        for line in failures:
            sys.stdout.write("FAIL %s\n" % line)
        return 1
    return 0


# ------------------------------------------------------------------ main ----

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="gap-to-admission pipeline executor (D2-2 data layer; "
                    "trigger verdict imported from scheduler_lite; rows "
                    "enter PENDING; code-layer faces stay human-gated)")
    parser.add_argument("command", nargs="?", default="run",
                        choices=("run",), help="the run face (default)")
    parser.add_argument("--plan", default=None, metavar="FILE",
                        help="scheduler_lite plan document to consume "
                             "(default: re-derive via scheduler_lite)")
    parser.add_argument("--gap-ledger", action="append", default=[],
                        metavar="PATH",
                        help="gap feed ledger input (repeatable; default "
                             "docs/gap-feed-ledger.jsonl when present)")
    parser.add_argument("--reports", action="append", default=[],
                        metavar="PATH",
                        help="vacgen report file or directory (repeatable; "
                             "default docs/vacgen-reports when present)")
    parser.add_argument("--rounds", action="append", default=[],
                        metavar="PATH",
                        help="round ledger (default docs/round-ledger.jsonl)")
    parser.add_argument("--autonomy", action="append", default=[],
                        metavar="PATH",
                        help="autonomy gear config (default autonomy.json)")
    parser.add_argument("--state", action="append", default=[],
                        metavar="PATH",
                        help="round state roster (default "
                             "docs/round-state.json)")
    parser.add_argument("--ef-marker", default=None, metavar="PATH",
                        help="EF all-green marker file (the ignition gate)")
    parser.add_argument("--threshold", type=int, default=None, metavar="N",
                        help="TODO-SEAT trigger threshold (scheduler_lite "
                             "default applies)")
    parser.add_argument("--interval-seconds", type=int, default=None,
                        metavar="N",
                        help="round spacing override (scheduler_lite "
                             "default applies)")
    parser.add_argument("--now-utc", default=None, metavar="ISO8601Z",
                        help="plan clock override (default: real UTC now)")
    parser.add_argument("--gap-out", default=None, metavar="FILE",
                        help="gap_cluster aggregate output (default "
                             "docs/gap-ledger-latest.json)")
    parser.add_argument("--render-gaps", default=None, metavar="FILE",
                        help="row_render gap input written by this tool "
                             "(default docs/drafts/"
                             "gap-ledger-render-input.json)")
    parser.add_argument("--packet-out", default=None, metavar="FILE",
                        help="render packet JSONL (default docs/drafts/"
                             "render-packet-latest.jsonl)")
    parser.add_argument("--backfill", default=None, metavar="FILE",
                        help="model-side backfill JSONL for the packet "
                             "(absent = pending-backfill stop)")
    parser.add_argument("--draft-out", default=None, metavar="FILE",
                        help="candidate draft JSON (default docs/drafts/"
                             "taxonomy-candidates-pipeline.json)")
    parser.add_argument("--b-gate-audit", default=None, metavar="PATH",
                        help="b-gate audit JSON to carry in the report "
                             "(default docs/b-gate-audit.json)")
    parser.add_argument("--policy-ref", default=None, metavar="S",
                        help="layer-law first-admission reference stamped "
                             "into the gap rows (a D2-2 default applies)")
    parser.add_argument("--stop-at", choices=("data", "human"),
                        default="human",
                        help="stop after the pure data steps or run ingest "
                             "to the PENDING draft (default human)")
    parser.add_argument("--json", action="store_true",
                        help="print the run report JSON on stdout")
    args = parser.parse_args(argv)
    # One member per single-file face keeps the resolution rules simple;
    # repeats beyond the first are a usage error rather than a silent pick.
    for flag in ("rounds", "autonomy", "state"):
        if len(getattr(args, flag)) > 1:
            parser.error("--%s takes one path" % flag)
    try:
        return run_face(args)
    except PipelineInputError as exc:
        fail(str(exc), 9)


if __name__ == "__main__":
    sys.exit(main())
