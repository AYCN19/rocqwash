#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""i18n_verify.py - P4 verification matrix plus the P5 human ten-point gate (E4).

Purpose.  P4 runs the mechanical verify instruments over one target file
  as subprocesses (ai-flavor detector, norm_lint with the jargon map,
  doc_lint) and aggregates exit codes and reports into one matrix, schema
  rocqwash.i18n.verify/1; findings are data.  P5 emits the human
  ten-point form (face-variant: .v targets carry the verbatim i18n-seed
  transcription; py/sh/md targets the annotation-standard five-field
  variant) and ingests the verdict file fail-loud with an append-only
  tenpoint_verdict write-back.  The engine never judges.

Interface.  --verify-target P | --emit-tenpoint P | --ingest-tenpoint P
  | --selftest; --faces LIST (default jargon,cjk,ai_flavor,doc_lint),
  tool paths, --repo, --jargon-map, --ledger, --timestamp, --json per
  the extended contract below.  One mode per run.  Verdict values
  PASS or FAIL per point; frame ALL-PASS, N-FAIL, or BLOCKED.

Dependencies.  Python 3 standard library only; instruments run under
  sys.executable with -I; paths parameterized, defaults beside this
  file; temporary report files never named in output.

Evidence.  --selftest: form shape for both variants; ingest accept and
  reject vectors; ledger append and idempotent rerun over pipeline
  policy and close records; stub matrix; zero em-dash face.

Exit-codes.  0 accounted (clean matrix, emitted form, accepted ingest,
  selftest green); 1 data findings or rejected verdict file (named
  problems); 2 usage; 9 missing input (target, instrument, ledger,
  verdict file).
"""
# Extended contract (kept outside the five-field block per the header
# budget of the annotation standard):
# P4 matrix rows carry {face, instrument, argv_shape, rc, status,
# findings_total, by_kind, report, note}; status is pass, findings,
# not-applicable, missing-instrument, missing-input, or instrument-error.
# A face whose target extension the instrument does not document is
# not-applicable (registered loudly, never silently skipped); on a .v
# target every mechanical face is blind by design and the matrix verdict
# reads blind-mechanical, because the human ten-point gate is the
# substitute on that face.  The jargon and cjk faces share one norm_lint
# run.  Exit aggregation: any missing-instrument or missing-input row
# exits 9; any findings or instrument-error row exits 1; otherwise 0.
# P5 write-back is append-only: one superseding ledger row per segment
# id, latest state copied, only tenpoint_verdict (and timestamp_utc when
# the run carries one) changed; rerun with the same frame appends zero
# rows.  Ledger rows carrying a pipeline record_type other than segment
# (the P0 policy row and the P6 close record of i18n_pipeline.py) are
# skipped, not judged and never rewritten; the ingest report counts them
# under ledger_records_skipped.  Rows with no record_type key keep the
# segment-row contract.  Without --ledger nothing is written.
# Verbatim transcription note: the ten-point constants below are seed
# source text carried as data, byte-faithful to the transcription source;
# the em-dash pair inside point 8 is written as escape sequences so the
# file face itself stays at the zero em-dash target (the selftest asserts
# both the file face and the decoded data).

import argparse
import copy
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

TOOL = "i18n_verify"
MATRIX_SCHEMA = "rocqwash.i18n.verify/1"
FORM_SCHEMA = "rocqwash.tenpoint.form/1"
VERDICT_SCHEMA = "rocqwash.tenpoint.verdicts/1"
INGEST_SCHEMA = "rocqwash.tenpoint.ingest/1"
POINT_COUNT = 10
VERDICT_VALUES = ("PASS", "FAIL")
FRAME_VALUES = ("ALL-PASS", "N-FAIL", "BLOCKED")
REPO_FACES = (".py", ".sh", ".md")
AI_FLAVOR_FACES = (".py", ".sh", ".md", ".json", ".ts")
DEFAULT_FACES = ("jargon", "cjk", "ai_flavor", "doc_lint")
ALL_FACES = DEFAULT_FACES + ("selftests",)
CITATION_PATTERN = re.compile(r"^[0-9][0-9,; -]*$")
LEDGER_FLUSH_KEYS = ("segment_id", "tenpoint_verdict")

REPO_INTRO = ("Ten-point review on the annotation-standard face: one "
              "verdict and one source-line citation per point.")
FILL_RULE = ("Set verdict to PASS or FAIL per point, citation to the "
             "source line number, and frame to ALL-PASS, N-FAIL, or "
             "BLOCKED; the engine does not judge.")

# Verbatim transcription of the human ten-point single-face gate (seed
# text; intro line plus ten numbered points, carried as data, not prose).
TENPOINT_INTRO = "十点单（逐件逐点给 PASS/FAIL+原文行引用·缺一不可）："
TENPOINT_V = [
    "1. 五字段英文头齐且序正：①Mission ②Dependencies ③References ④Constructivity ⑤Build（⑥许可与归属行可选·仅外部投递件）。",
    "2. 头注五字段各一行业务句：使命一句话（数学内容）、依赖清单一行（本库 Require）、对标行（无则整行省略）、构造性注记一行（Set 层承载/零承认/可提取）、编译配方一行。",
    "3. 头注剔除面：席次战役流水/日志路径/坑卡引用/预算耗时/修订历史＝0。",
    "4. 横幅形：`(* ==== Section n. <math topic> ==== *)` 英文形（§ 形仅内部沙箱件合法）；主题名＝数学内容（禁战役名/「第一部分」类空洞名）。",
    "5. 步进注释语言：提交面/投递模块＝英文陈述句（中文限内部沙箱件·按派单申报的件面属性判）。",
    "6. 步进注释引用真实标识符（真名引用·禁绰号）；证明段落注释写数学理由。",
    "7. 过程语黑话＝0（落刀/台账/回执/工单/席位/挂账/消费（「零消费」代码引用语境除外）/在飞/冻结令类全查·按白皮书 §4 映射判）。",
    "8. 承认式英文词面（admit/axiom/parameter/conjecture/abort/hypothesis 作自述）＝0（含英文头注自述句 \"no Admitted\" 类\u2014\u2014裸 grep 假阳高发位·看语境判）。",
    "9. Statement provenance 语句级迁移账＝外置（件内仅留 References 名级出处·fully qualified name·行号至多括注）。",
    "10. 头注行数 1:1 与 30 行帽冲突处置：超帽事实须已在 REVIEW 档登记放行（无登记＝FAIL）。",
]

# Repository-face variant of the ten points, cut on the annotation
# standard card: the five-field header shape and the machine-checkable
# register faces, phrased for py/sh/md targets.
TENPOINT_REPO = [
    "1. Five-field header block present with the field names verbatim and in order: Purpose. / Interface. / Dependencies. / Evidence. / Exit-codes.",
    "2. Each of the five fields carries one business sentence (purpose names the single job, interface lists the flags and modes, dependencies stays stdlib-only, evidence names the selftest vectors, exit-codes enumerates every code).",
    "3. Header exclusion face zero: no process narrative, log paths, pitfall-card references, budget or timing notes, or revision history.",
    "4. Banner form: the first header line names the file and its one-line role, and it is not a field name.",
    "5. Stepping comments are English declarative sentences; the CJK register stays confined to data literals.",
    "6. Comments cite real identifiers by name; no nicknames, and comments next to proof steps state the mathematical reason.",
    "7. Process-jargon faces are zero, judged against the annotation-standard mapping table.",
    "8. Admission-form and AI-flavor English word faces are zero, judged in context (bare pattern scans over-report; read the line).",
    "9. Statement-level provenance stays external; in-file references remain name-level with at most a line note.",
    "10. Header stays within the 30-line budget; over budget only with a registered REVIEW waiver.",
]


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tool_path(name):
    return os.path.join(repo_root(), "tools", name)


def default_jargon_map():
    return os.path.join(repo_root(), "docs", "jargon-to-standard-mapping-v1.md")


def utcnow():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class VerifyError(Exception):
    """Fail-loud carrier: kind is "missing" (exit 9) or "rejected" (exit 1)."""

    def __init__(self, kind, detail):
        super().__init__(detail)
        self.kind = kind


# ---------- rendering ----------

def render(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_output(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


# ---------- P5: ten-point form (pure) ----------

def variant_for(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".v":
        return "v"
    if ext in REPO_FACES:
        return "tool-repo"
    return None


def emit_form(target, variant):
    if variant == "v":
        texts, intro = TENPOINT_V, TENPOINT_INTRO
    else:
        texts, intro = TENPOINT_REPO, REPO_INTRO
    points = [{"point": idx + 1, "text": text, "verdict": "",
               "citation": "", "note": ""}
              for idx, text in enumerate(texts)]
    return {"schema": FORM_SCHEMA, "tool": TOOL, "target": target,
            "face": variant, "intro": intro, "points": points,
            "fill_rule": FILL_RULE}


# ---------- P5: verdict ingestion (pure validators) ----------

def validate_verdicts(verdicts, line_count=None):
    """Return (problems, frame); problems is a list of named strings."""
    problems = []
    if not isinstance(verdicts, dict):
        return ["verdict file: not a JSON object"], None
    if verdicts.get("schema") != VERDICT_SCHEMA:
        problems.append("schema: %r instead of %s"
                        % (verdicts.get("schema"), VERDICT_SCHEMA))
    target = verdicts.get("target")
    if not (isinstance(target, str) and target.strip()):
        problems.append("target: missing or empty")
    frame = verdicts.get("frame")
    if frame not in FRAME_VALUES:
        problems.append("frame: %r outside %s" % (frame, ", ".join(FRAME_VALUES)))
    points = verdicts.get("points")
    if not isinstance(points, list) or len(points) != POINT_COUNT:
        problems.append("points: expected a list of %d rows"
                        % POINT_COUNT)
        return problems, frame
    seen = set()
    fail_count = 0
    for pos, row in enumerate(points):
        where = "points[%d]" % pos
        if not isinstance(row, dict):
            problems.append("%s: not an object" % where)
            continue
        number = row.get("point")
        if not (isinstance(number, int) and 1 <= number <= POINT_COUNT):
            problems.append("%s: point %r outside 1..%d"
                            % (where, number, POINT_COUNT))
        elif number in seen:
            problems.append("%s: duplicate point %d" % (where, number))
        else:
            seen.add(number)
        verdict = row.get("verdict")
        if verdict not in VERDICT_VALUES:
            problems.append("%s: verdict %r outside %s"
                            % (where, verdict, "/".join(VERDICT_VALUES)))
        elif verdict == "FAIL":
            fail_count += 1
        citation = row.get("citation")
        if not (isinstance(citation, str) and citation.strip()):
            problems.append("%s: citation empty (source line required)"
                            % where)
        elif not CITATION_PATTERN.match(citation.strip()):
            problems.append("%s: citation %r is not a line reference"
                            % (where, citation))
        elif line_count is not None:
            numbers = [int(x) for x in re.findall(r"[0-9]+", citation)]
            if any(n < 1 or n > line_count for n in numbers):
                problems.append("%s: citation %r outside the target "
                                "(%d lines)" % (where, citation, line_count))
    if frame == "ALL-PASS" and fail_count:
        problems.append("frame ALL-PASS against %d FAIL row(s)" % fail_count)
    if frame == "N-FAIL" and not fail_count:
        problems.append("frame N-FAIL without any FAIL row")
    return problems, frame


def ledger_plan(lines, frame, timestamp=None):
    """Plan the append-only write-back; returns (latest, rows, already,
    skipped, problems).

    Rows carrying a record_type other than segment are the pipeline's own
    bookkeeping (the P0 policy row and the P6 close record written by
    i18n_pipeline.py): they are skipped, never judged and never rewritten,
    and the skip count is returned so the ingest report can register it
    loudly.  A row with no record_type key keeps the legacy treatment."""
    problems = []
    latest = {}
    skipped = 0
    for pos, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except ValueError as exc:
            problems.append("ledger line %d: not JSON (%s)" % (pos, exc))
            continue
        if isinstance(row, dict) \
                and row.get("record_type") not in (None, "segment"):
            skipped += 1
            continue
        if not isinstance(row, dict) or not isinstance(row.get("segment_id"), str) \
                or not isinstance(row.get("tenpoint_verdict"), str):
            problems.append("ledger line %d: not a segment row (missing %s)"
                            % (pos, " or ".join(LEDGER_FLUSH_KEYS)))
            continue
        latest[row["segment_id"]] = row
    if problems:
        return {}, [], False, 0, problems
    if not latest:
        return {}, [], False, skipped, ["ledger: no segment rows to write back"]
    already = all(row["tenpoint_verdict"] == frame for row in latest.values())
    rows = []
    if not already:
        for segment_id in sorted(latest):
            row = dict(latest[segment_id])
            row["tenpoint_verdict"] = frame
            if timestamp:
                row["timestamp_utc"] = timestamp
            rows.append(row)
    return latest, rows, already, skipped, []


def read_lines(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read().splitlines()


# ---------- P4: instrument orchestration ----------

def _run(cmd, timeout_seconds=120):
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        return None, "", "timeout after %ds" % timeout_seconds
    except OSError as exc:
        return None, "", "spawn failed: %s" % exc
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), \
        proc.stderr.decode("utf-8", "replace")


def _load_report(path):
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return json.load(handle), None
    except (OSError, ValueError) as exc:
        return None, str(exc)


def _row(face, instrument, argv_shape, rc, status, report=None, note=None,
         findings_total=0, by_kind=None):
    return {"face": face, "instrument": instrument, "argv_shape": argv_shape,
            "rc": rc, "status": status, "findings_total": findings_total,
            "by_kind": by_kind or {}, "report": report, "note": note}


def _extension(target):
    return os.path.splitext(target)[1].lower()


def _run_normlint(target, tool, jargon_map, selected, report_dir):
    """One norm_lint run serving the jargon and cjk faces; rows per face."""
    instrument = tool
    shape = [sys.executable, "-I", instrument, "--file", target,
             "--jargon-map", jargon_map, "--json", "<tmp-report>"]
    rows = []
    if not os.path.isfile(tool):
        for face in selected:
            rows.append(_row(face, instrument, shape, None,
                             "missing-instrument",
                             note="instrument file not found on disk"))
        return rows, "missing"
    if _extension(target) not in REPO_FACES:
        for face in selected:
            rows.append(_row(face, instrument, shape, None,
                             "not-applicable",
                             note="norm_lint documents %s faces only; on "
                                  "this target the human gate substitutes"
                             % "/".join(REPO_FACES)))
        return rows, "blind"
    tmp = os.path.join(report_dir, "norm_lint_report.json")
    argv = [sys.executable, "-I", instrument, "--file", target,
            "--jargon-map", jargon_map, "--json", tmp]
    rc, out, err = _run(argv)
    if rc == 9:
        for face in selected:
            rows.append(_row(face, instrument, shape, rc, "missing-input",
                             note=(err or out).strip()[:200]
                                  or "norm_lint reports missing input"))
        return rows, "missing"
    if rc != 0:
        for face in selected:
            rows.append(_row(face, instrument, shape, rc, "instrument-error",
                             note=(err or out).strip()[:200]
                                  or "norm_lint exited %s" % rc))
        return rows, "error"
    report, parse_error = _load_report(tmp)
    if report is None:
        for face in selected:
            rows.append(_row(face, instrument, shape, rc, "instrument-error",
                             note="report unreadable: %s" % parse_error))
        return rows, "error"
    findings = []
    for record in report.get("files", []):
        findings.extend(record.get("findings", []))
    ratio = report.get("summary", {}).get("cjk_ratio")
    for face in selected:
        mine = [f for f in findings if f.get("kind") == face]
        status = "findings" if mine else "pass"
        slice_report = {"kind": face, "findings": mine}
        if face == "cjk":
            slice_report["cjk_ratio"] = ratio
        rows.append(_row(face, instrument, shape, rc, status,
                         report=slice_report, findings_total=len(mine),
                         by_kind={face: len(mine)}))
    return rows, "ok"


def _run_ai_flavor(target, tool, report_dir):
    instrument = tool
    shape = [sys.executable, "-I", instrument, "--file", target,
             "--json", "<tmp-report>"]
    if not os.path.isfile(tool):
        return _row("ai_flavor", instrument, shape, None,
                    "missing-instrument",
                    note="instrument file not found on disk"), "missing"
    if _extension(target) not in AI_FLAVOR_FACES:
        return _row("ai_flavor", instrument, shape, None, "not-applicable",
                    note="detector documents %s faces; on this target the "
                         "human gate substitutes"
                    % "/".join(AI_FLAVOR_FACES)), "blind"
    tmp = os.path.join(report_dir, "ai_flavor_report.json")
    rc, out, err = _run([sys.executable, "-I", instrument, "--file", target,
                         "--json", tmp])
    if rc == 2:
        return _row("ai_flavor", instrument, shape, rc, "instrument-error",
                    note=(err or out).strip()[:200]
                         or "detector exited 2 (usage face drift)"), "error"
    report, parse_error = _load_report(tmp)
    hits = (report or {}).get("hits", [])
    em_dash = (report or {}).get("em_dash_count")
    if report is None:
        if rc in (0, 1):
            return _row("ai_flavor", instrument, shape, rc,
                        "instrument-error",
                        note="report unreadable: %s" % parse_error), "error"
        return _row("ai_flavor", instrument, shape, rc, "instrument-error",
                    note=(err or out).strip()[:200]
                         or "detector exited %s without a report" % rc), "error"
    status = "findings" if (hits or em_dash) else "pass"
    return _row("ai_flavor", instrument, shape, rc, status, report=report,
                findings_total=len(hits) + (em_dash or 0),
                by_kind={"hits": len(hits), "em_dash": em_dash}), "ok"


def _run_doc_lint(repo, tool, report_dir):
    instrument = tool
    shape = [sys.executable, "-I", instrument, "--repo", repo,
             "--json", "<tmp-report>"]
    if not os.path.isfile(tool):
        return _row("doc_lint", instrument, shape, None, "missing-instrument",
                    note="instrument file not found on disk"), "missing"
    tmp = os.path.join(report_dir, "doc_lint_report.json")
    rc, out, err = _run([sys.executable, "-I", instrument, "--repo", repo,
                         "--json", tmp])
    if rc == 9:
        return _row("doc_lint", instrument, shape, rc, "missing-input",
                    note=(err or out).strip()[:200]
                         or "doc_lint reports missing repo inputs"), "missing"
    if rc not in (0, 1):
        return _row("doc_lint", instrument, shape, rc, "instrument-error",
                    note=(err or out).strip()[:200]
                         or "doc_lint exited %s" % rc), "error"
    report, parse_error = _load_report(tmp)
    if report is None:
        return _row("doc_lint", instrument, shape, rc, "instrument-error",
                    note="report unreadable: %s" % parse_error), "error"
    checks = report.get("checks", [])
    drifted = [c for c in checks if c.get("status") == "drift"]
    status = "findings" if drifted else "pass"
    return _row("doc_lint", instrument, shape, rc, status, report=report,
                findings_total=len(drifted),
                by_kind={"drift": len(drifted)}), "ok"


def _run_selftests(tools, report_dir):
    rows = []
    worst = "ok"
    for name, tool in sorted(tools.items()):
        shape = [sys.executable, "-I", tool, "--selftest"]
        if not os.path.isfile(tool):
            rows.append(_row("selftests", tool, shape, None,
                             "missing-instrument", note="subject %s" % name,
                             findings_total=0))
            worst = "missing"
            continue
        rc, out, err = _run(shape)
        status = "pass" if rc == 0 else "instrument-error"
        if rc != 0:
            worst = "error"
        rows.append(_row("selftests", tool, shape, rc, status,
                         note=((err or out).strip()[:200] or None),
                         findings_total=0,
                         by_kind={"selftest_fail": 0 if rc == 0 else 1}))
    return rows, worst


def run_matrix(target, faces, opts, report_dir):
    """Run the selected faces; returns (matrix dict, exit kind)."""
    rows = []
    worst = "ok"
    selected_norm = [f for f in ("jargon", "cjk") if f in faces]
    if selected_norm:
        face_rows, kind = _run_normlint(target, opts["norm_lint_tool"],
                                        opts["jargon_map"], selected_norm,
                                        report_dir)
        rows.extend(face_rows)
        worst = _worse(worst, kind)
    if "ai_flavor" in faces:
        row, kind = _run_ai_flavor(target, opts["ai_flavor_tool"], report_dir)
        rows.append(row)
        worst = _worse(worst, kind)
    if "doc_lint" in faces:
        row, kind = _run_doc_lint(opts["repo"], opts["doc_lint_tool"],
                                  report_dir)
        rows.append(row)
        worst = _worse(worst, kind)
    if "selftests" in faces:
        face_rows, kind = _run_selftests(
            {"ai_flavor": opts["ai_flavor_tool"],
             "norm_lint": opts["norm_lint_tool"],
             "doc_lint": opts["doc_lint_tool"]}, report_dir)
        rows.extend(face_rows)
        worst = _worse(worst, kind)
    live = [r for r in rows if r["status"] != "not-applicable"]
    if worst == "missing":
        verdict = "missing-input"
    elif worst == "error":
        verdict = "instrument-error"
    elif any(r["status"] == "findings" for r in rows):
        verdict = "findings"
    elif not live:
        verdict = "blind-mechanical"
    else:
        verdict = "clean"
    matrix = {"schema": MATRIX_SCHEMA, "tool": TOOL, "target": target,
              "faces": sorted(faces), "rows": rows, "verdict": verdict}
    return matrix, verdict


def _worse(current, kind):
    order = {"ok": 0, "blind": 0, "error": 1, "missing": 2}
    return kind if order.get(kind, 0) > order.get(current, 0) else current


VERDICT_EXIT = {"clean": 0, "blind-mechanical": 0, "findings": 1,
                "instrument-error": 1, "missing-input": 9}


# ---------- selftest ----------

def _write_stub(path, rc, payload):
    source = (
        "import json\n"
        "import sys\n"
        "RC = %d\n"
        "PAYLOAD = json.loads(%r)\n"
        "argv = sys.argv[1:]\n"
        "out = None\n"
        "for i, arg in enumerate(argv):\n"
        "    if arg == '--json' and i + 1 < len(argv):\n"
        "        out = argv[i + 1]\n"
        "if out:\n"
        "    with open(out, 'w', encoding='utf-8') as handle:\n"
        "        json.dump(PAYLOAD, handle)\n"
        "sys.exit(RC)\n"
    ) % (rc, json.dumps(payload))
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(source)


def _write_fixture(path, line_count):
    body = ["fixture line %d for the verify selftest" % (i + 1)
            for i in range(line_count)]
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(body) + "\n")


def _fill_verdicts(form, frame, fails=(), citation_map=None):
    # deep copy first: the emitted form's point rows stay untouched
    form = copy.deepcopy(form)
    for row in form["points"]:
        row["verdict"] = "FAIL" if row["point"] in fails else "PASS"
        row["citation"] = (citation_map or {}).get(row["point"],
                                                   str(row["point"]))
    form["frame"] = frame
    form["schema"] = VERDICT_SCHEMA
    form["target"] = form.get("target", "")
    return form


def _ledger_line(segment_id):
    return json.dumps({
        "segment_id": segment_id, "direction": "zh2en",
        "source_span": {"start_line": 1, "end_line": 3},
        "model_id": "human", "annotation_site": "model",
        "prompt_template_ref": "prompts/zh2en-repo-v1",
        "linkages_run": ["normalization"],
        "policy_precheck_ref": "P0-repo-face-run-1",
        "tenpoint_verdict": "PENDING",
        "timestamp_utc": "2000-01-01T00:00:00Z",
    }, ensure_ascii=False, sort_keys=True)


def selftest(out):
    """Vectors on temporary fixtures; 0 green, 1 red."""
    import shutil
    problems = []
    work = tempfile.mkdtemp(prefix="i18n-verify-selftest-")

    def check(name, condition, detail=""):
        if condition:
            out.write("PASS %s\n" % name)
        else:
            problems.append(name)
            out.write("FAIL %s%s\n" % (name, (": " + detail) if detail else ""))

    try:
        v_target = os.path.join(work, "fixture.v")
        py_target = os.path.join(work, "fixture.py")
        _write_fixture(v_target, 12)
        _write_fixture(py_target, 12)

        form_v = emit_form(v_target, variant_for(v_target))
        check("form-v-variant", form_v["face"] == "v")
        check("form-v-ten-slots", len(form_v["points"]) == POINT_COUNT)
        check("form-v-empty-verdicts",
              all(row["verdict"] == "" and row["citation"] == ""
                  for row in form_v["points"]))
        check("form-v-verbatim-intro", form_v["intro"] == TENPOINT_INTRO)
        form_py = emit_form(py_target, variant_for(py_target))
        check("form-repo-variant", form_py["face"] == "tool-repo")
        check("form-unsupported-face", variant_for(
            os.path.join(work, "fixture.txt")) is None)

        emitted = os.path.join(work, "form.json")
        check("cli-emit-exit", main(["--emit-tenpoint", v_target,
                                     "--json", emitted]) == 0)
        with io.open(emitted, "r", encoding="utf-8") as handle:
            check("cli-emit-form-schema",
                  json.load(handle)["schema"] == FORM_SCHEMA)
        again = os.path.join(work, "form2.json")
        main(["--emit-tenpoint", v_target, "--json", again])
        check("determinism-form",
              io.open(emitted, "rb").read() == io.open(again, "rb").read())

        verdicts_path = os.path.join(work, "verdicts.json")
        filled = _fill_verdicts(dict(form_v), "ALL-PASS")
        filled["schema"] = VERDICT_SCHEMA
        filled["target"] = v_target
        write_output(verdicts_path, render(filled))
        check("ingest-all-pass", main(["--ingest-tenpoint", verdicts_path,
                                       "--json", os.path.join(work, "i1.json")]) == 0)
        filled = _fill_verdicts(dict(form_v), "N-FAIL", fails=(3, 7))
        filled["schema"] = VERDICT_SCHEMA
        filled["target"] = v_target
        write_output(verdicts_path, render(filled))
        check("ingest-n-fail", main(["--ingest-tenpoint", verdicts_path,
                                     "--json", os.path.join(work, "i2.json")]) == 0)
        filled = _fill_verdicts(dict(form_v), "BLOCKED")
        filled["schema"] = VERDICT_SCHEMA
        filled["target"] = v_target
        write_output(verdicts_path, render(filled))
        check("ingest-blocked", main(["--ingest-tenpoint", verdicts_path,
                                      "--json", os.path.join(work, "i3.json")]) == 0)

        problems_cases = []
        bad = dict(form_v)
        bad["schema"] = "rocqwash.tenpoint.verdicts/0"
        problems_cases.append(("schema-drift", bad, None))
        bad = dict(form_v)
        bad["points"] = list(bad["points"])
        bad["points"] = bad["points"][:9]
        problems_cases.append(("point-count", bad, None))
        bad = _fill_verdicts(form_v, "ALL-PASS")
        bad["points"][2]["verdict"] = "MAYBE"
        problems_cases.append(("verdict-enum", bad, None))
        bad = _fill_verdicts(form_v, "ALL-PASS")
        bad["points"][4]["citation"] = ""
        problems_cases.append(("citation-empty", bad, None))
        bad = _fill_verdicts(form_v, "ALL-PASS")
        bad["points"][4]["citation"] = "9999"
        problems_cases.append(("citation-range", bad, 12))
        bad = _fill_verdicts(form_v, "ALL-PASS", fails=(2,))
        problems_cases.append(("frame-inconsistent", bad, None))
        for name, case, lines in problems_cases:
            case.setdefault("target", v_target)
            found, _frame = validate_verdicts(case, lines)
            check("reject-" + name, bool(found),
                  "rejection must name a problem")
        broken = os.path.join(work, "broken.json")
        write_output(broken, "{ not json")
        check("reject-not-json",
              main(["--ingest-tenpoint", broken]) == 1)
        check("reject-exit-missing-verdicts",
              main(["--ingest-tenpoint",
                    os.path.join(work, "absent.json")]) == 9)

        ledger_path = os.path.join(work, "segment-ledger.jsonl")
        with io.open(ledger_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(_ledger_line("s0001") + "\n")
            handle.write(_ledger_line("s0002") + "\n")
        before = io.open(ledger_path, "rb").read()
        filled = _fill_verdicts(dict(form_v), "N-FAIL", fails=(1,))
        filled["schema"] = VERDICT_SCHEMA
        filled["target"] = v_target
        write_output(verdicts_path, render(filled))
        report_path = os.path.join(work, "ingest-ledger.json")
        rc = main(["--ingest-tenpoint", verdicts_path, "--ledger",
                   ledger_path, "--timestamp", "2000-01-02T00:00:00Z",
                   "--json", report_path])
        with io.open(report_path, "r", encoding="utf-8") as handle:
            report = json.load(handle)
        after_lines = read_lines(ledger_path)
        superseded = [json.loads(line) for line in after_lines[2:]]
        check("ledger-append-rc", rc == 0)
        check("ledger-append-count",
              report["appended"] == 2 and report["wrote"] is True)
        check("ledger-append-frame",
              len(superseded) == 2
              and all(row["tenpoint_verdict"] == "N-FAIL" for row in superseded))
        check("ledger-append-keys",
              all(set(row.keys()) == set(json.loads(_ledger_line("s0001")).keys())
                  for row in superseded))
        check("ledger-append-originals-intact",
              io.open(ledger_path, "rb").read().startswith(before))
        rc = main(["--ingest-tenpoint", verdicts_path, "--ledger",
                   ledger_path, "--json", report_path])
        with io.open(report_path, "r", encoding="utf-8") as handle:
            rerun = json.load(handle)
        check("ledger-idempotent",
              rc == 0 and rerun["appended"] == 0
              and rerun["already_consistent"] is True
              and len(read_lines(ledger_path)) == 4)
        corrupt = os.path.join(work, "corrupt-ledger.jsonl")
        with io.open(corrupt, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(_ledger_line("s0001") + "\nnot-json\n")
        check("reject-corrupt-ledger",
              main(["--ingest-tenpoint", verdicts_path,
                    "--ledger", corrupt]) == 1)
        check("exit-missing-ledger",
              main(["--ingest-tenpoint", verdicts_path,
                    "--ledger", os.path.join(work, "absent.jsonl")]) == 9)
        headless = os.path.join(work, "headless-ledger.jsonl")
        with io.open(headless, "w", encoding="utf-8", newline="\n") as handle:
            handle.write('{"unrelated": true}\n')
        check("reject-headless-ledger",
              main(["--ingest-tenpoint", verdicts_path,
                    "--ledger", headless]) == 1)

        # the seam vector: a real pipeline ledger carries a P0 policy row
        # (record_type "policy") and can carry a P6 close record; the
        # write-back must skip both, leave their bytes untouched, and append
        # superseding rows for the segment rows only
        policy_row = json.dumps({
            "schema": "rocqwash.i18n.pipeline.policy/1",
            "record_type": "policy", "run_id": "seam-vector",
            "policy_precheck_ref": "P0-repo-seam-vector",
            "target": "fixture.py", "face": "repo", "direction": "zh2en",
            "regime_ref": "SPEC-7-E-repo-face", "disclosure_required": True,
            "refusal": False, "disclosure_form": [], "red_lines": [],
            "verdict": "accepted", "timestamp_utc": "2000-01-01T00:00:00Z",
        }, sort_keys=True)
        close_row = json.dumps({
            "schema": "rocqwash.i18n.pipeline.close/1",
            "record_type": "close", "run_id": "seam-vector",
            "segments_total": 2, "machine_segments": 2, "human_segments": 0,
            "verdict": "closed", "timestamp_utc": "2000-01-01T00:00:00Z",
        }, sort_keys=True)
        mixed = os.path.join(work, "mixed-ledger.jsonl")
        with io.open(mixed, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(policy_row + "\n")
            handle.write(_ledger_line("s0001") + "\n")
            handle.write(_ledger_line("s0002") + "\n")
            handle.write(close_row + "\n")
        policy_bytes = (policy_row + "\n").encode("utf-8")
        filled = _fill_verdicts(dict(form_v), "N-FAIL", fails=(2,))
        filled["schema"] = VERDICT_SCHEMA
        filled["target"] = v_target
        write_output(verdicts_path, render(filled))
        report_path = os.path.join(work, "ingest-mixed.json")
        rc = main(["--ingest-tenpoint", verdicts_path, "--ledger", mixed,
                   "--timestamp", "2000-01-02T00:00:00Z",
                   "--json", report_path])
        with io.open(report_path, "r", encoding="utf-8") as handle:
            report = json.load(handle)
        after = [json.loads(line) for line in read_lines(mixed)]
        check("ledger-skips-record-type-rows", rc == 0)
        check("ledger-skip-count-registered",
              report["ledger_records_skipped"] == 2 and report["appended"] == 2)
        check("ledger-policy-row-byte-intact",
              io.open(mixed, "rb").read().startswith(policy_bytes))
        check("ledger-write-back-carries-segment-rows-only",
              len(after) == 6
              and all(row.get("record_type") is None for row in after[4:]))
        rc = main(["--ingest-tenpoint", verdicts_path, "--ledger", mixed,
                   "--json", report_path])
        with io.open(report_path, "r", encoding="utf-8") as handle:
            rerun = json.load(handle)
        check("ledger-mixed-idempotent",
              rc == 0 and rerun["appended"] == 0
              and rerun["ledger_records_skipped"] == 2
              and len(read_lines(mixed)) == 6)
        policy_only = os.path.join(work, "policy-only-ledger.jsonl")
        with io.open(policy_only, "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write(policy_row + "\n")
        check("reject-ledger-without-segment-rows",
              main(["--ingest-tenpoint", verdicts_path,
                    "--ledger", policy_only]) == 1)

        stub_a_clean = os.path.join(work, "stub_a_clean.py")
        _write_stub(stub_a_clean, 0, {"hits": [], "em_dash_count": 0})
        stub_a_red = os.path.join(work, "stub_a_red.py")
        _write_stub(stub_a_red, 1, {"hits": [{"line": 3}, {"line": 7}],
                                    "em_dash_count": 1})
        stub_n_clean = os.path.join(work, "stub_n_clean.py")
        _write_stub(stub_n_clean, 0,
                    {"files": [], "summary": {"files": 1, "error": 0,
                                              "warn": 0, "cjk_ratio": 0.0}})
        stub_n_red = os.path.join(work, "stub_n_red.py")
        _write_stub(stub_n_red, 0,
                    {"files": [{"path": "fixture.py",
                                "findings": [{"line": 5, "kind": "jargon",
                                              "term": "term",
                                              "suggest": "fix"}],
                                "cjk_chars": 0, "face_chars": 100}],
                     "summary": {"files": 1, "error": 1, "warn": 0,
                                 "cjk_ratio": 0.0}})
        stub_d_clean = os.path.join(work, "stub_d_clean.py")
        _write_stub(stub_d_clean, 0, {"verdict": "consistent", "checks": []})
        stub_d_red = os.path.join(work, "stub_d_red.py")
        _write_stub(stub_d_red, 1,
                    {"verdict": "drift",
                     "checks": [{"kind": "tool_table", "status": "drift",
                                 "detail": "missing route", "target": "cw.sh"}]})
        matrix_path = os.path.join(work, "matrix.json")

        def run_matrix_cli(tool_map, faces, out_path):
            argv = ["--verify-target", py_target, "--faces", faces,
                    "--json", out_path]
            argv += tool_map
            return main(argv)

        rc = run_matrix_cli(["--ai-flavor-tool", stub_a_clean], "ai_flavor",
                            matrix_path)
        with io.open(matrix_path, "r", encoding="utf-8") as handle:
            matrix = json.load(handle)
        check("matrix-clean", rc == 0 and matrix["verdict"] == "clean"
              and matrix["rows"][0]["status"] == "pass")
        rc = run_matrix_cli(["--ai-flavor-tool", stub_a_red], "ai_flavor",
                            matrix_path)
        with io.open(matrix_path, "r", encoding="utf-8") as handle:
            matrix = json.load(handle)
        check("matrix-findings", rc == 1 and matrix["verdict"] == "findings"
              and matrix["rows"][0]["findings_total"] == 3)
        rc = run_matrix_cli(["--ai-flavor-tool",
                             os.path.join(work, "absent.py")], "ai_flavor",
                            matrix_path)
        with io.open(matrix_path, "r", encoding="utf-8") as handle:
            matrix = json.load(handle)
        check("matrix-missing-instrument",
              rc == 9 and matrix["rows"][0]["status"] == "missing-instrument")
        rc = run_matrix_cli(["--norm-lint-tool", stub_n_red], "jargon,cjk",
                            matrix_path)
        with io.open(matrix_path, "r", encoding="utf-8") as handle:
            matrix = json.load(handle)
        by_face = {row["face"]: row for row in matrix["rows"]}
        check("matrix-normlint-split",
              rc == 1 and by_face["jargon"]["status"] == "findings"
              and by_face["cjk"]["status"] == "pass")
        rc = run_matrix_cli(["--doc-lint-tool", stub_d_red], "doc_lint",
                            matrix_path)
        with io.open(matrix_path, "r", encoding="utf-8") as handle:
            matrix = json.load(handle)
        check("matrix-doclint-drift", rc == 1
              and matrix["rows"][0]["status"] == "findings")
        rc = main(["--verify-target", py_target, "--faces", "selftests",
                   "--ai-flavor-tool", stub_a_clean,
                   "--norm-lint-tool", stub_n_clean,
                   "--doc-lint-tool", stub_d_clean, "--json", matrix_path])
        with io.open(matrix_path, "r", encoding="utf-8") as handle:
            matrix = json.load(handle)
        check("matrix-selftests-face",
              rc == 0
              and all(row["status"] == "pass" for row in matrix["rows"]))
        rc = run_matrix_cli(
            ["--ai-flavor-tool", stub_a_clean, "--norm-lint-tool", stub_n_clean,
             "--doc-lint-tool", stub_d_clean],
            "jargon,cjk,ai_flavor,doc_lint", matrix_path)
        with io.open(matrix_path, "r", encoding="utf-8") as handle:
            matrix = json.load(handle)
        check("matrix-all-faces-clean",
              rc == 0 and matrix["verdict"] == "clean"
              and all(row["status"] == "pass" for row in matrix["rows"]))
        rc = main(["--verify-target", v_target, "--faces", "jargon,cjk",
                   "--json", matrix_path])
        with io.open(matrix_path, "r", encoding="utf-8") as handle:
            matrix_v = json.load(handle)
        check("matrix-v-blind", rc == 0
              and matrix_v["verdict"] == "blind-mechanical"
              and all(row["status"] == "not-applicable"
                      for row in matrix_v["rows"]))
        matrix2 = os.path.join(work, "matrix2.json")
        run_matrix_cli(["--ai-flavor-tool", stub_a_red], "ai_flavor",
                       matrix_path)
        run_matrix_cli(["--ai-flavor-tool", stub_a_red], "ai_flavor", matrix2)
        check("determinism-matrix",
              io.open(matrix_path, "rb").read()
              == io.open(matrix2, "rb").read())

        check("exit-usage-no-mode", main([]) == 2)
        check("exit-usage-two-modes",
              main(["--verify-target", py_target,
                    "--emit-tenpoint", py_target]) == 2)
        check("exit-usage-unknown-face",
              main(["--verify-target", py_target,
                    "--faces", "bogus"]) == 2)
        check("exit-missing-target",
              main(["--verify-target",
                    os.path.join(work, "absent.py")]) == 9)
        txt_target = os.path.join(work, "fixture.txt")
        _write_fixture(txt_target, 2)
        check("exit-usage-unsupported-face",
              main(["--emit-tenpoint", txt_target]) == 2)

        check("verbatim-ten-items",
              len(TENPOINT_V) == POINT_COUNT
              and all(text.strip() for text in TENPOINT_V))
        check("verbatim-em-dash-pair-carried",
              TENPOINT_V[7].count("\u2014") == 2)
        raw = io.open(__file__, "rb").read()
        check("file-face-zero-em-dash", b"\xe2\x80\x94" not in raw)
        check("repo-variant-ten-items",
              len(TENPOINT_REPO) == POINT_COUNT
              and all(text.strip() for text in TENPOINT_REPO))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if problems:
        out.write("I18N-VERIFY-SELFTEST: FAIL (%d vector(s))\n" % len(problems))
        return 1
    out.write("I18N-VERIFY-SELFTEST: PASS (matrix, ten-point emit and "
              "ingest, ledger write-back, zero em-dash file face)\n")
    return 0


# ---------- CLI ----------

def usage(parser, message):
    sys.stderr.write("i18n_verify: %s\n" % message)
    parser.print_usage(sys.stderr)
    return 2


def _emit(target, json_out):
    variant = variant_for(target)
    if variant is None:
        return "usage", ("unsupported target face %r (use .v or %s)"
                         % (os.path.splitext(target)[1],
                            "/".join(REPO_FACES)))
    form = emit_form(target, variant)
    _write_or_print(form, json_out)
    return 0, None


def _write_or_print(obj, json_out):
    text = render(obj)
    if json_out:
        write_output(json_out, text)
    else:
        sys.stdout.write(text)


def _ingest(verdict_path, ledger_path, timestamp, json_out):
    if not os.path.isfile(verdict_path):
        raise VerifyError("missing", "verdict file not found: %s" % verdict_path)
    try:
        with io.open(verdict_path, "r", encoding="utf-8") as handle:
            verdicts = json.load(handle)
    except ValueError as exc:
        raise VerifyError("rejected", "verdict file not valid JSON: %s" % exc)
    target = verdicts.get("target") if isinstance(verdicts, dict) else None
    line_count = None
    if isinstance(target, str) and os.path.isfile(target):
        line_count = len(read_lines(target))
    problems, frame = validate_verdicts(verdicts, line_count)
    appended = 0
    already = None
    skipped = 0
    wrote = False
    if problems:
        raise VerifyError("rejected",
                          "verdict file rejected (%d problem(s)):\n  "
                          % len(problems) + "\n  ".join(problems))
    if ledger_path:
        if not os.path.isfile(ledger_path):
            raise VerifyError("missing", "ledger not found: %s" % ledger_path)
        latest, rows, already, skipped, ledger_problems = ledger_plan(
            read_lines(ledger_path), frame, timestamp)
        if ledger_problems:
            raise VerifyError("rejected",
                              "ledger rejected (%d problem(s)):\n  "
                              % len(ledger_problems)
                              + "\n  ".join(ledger_problems))
        if rows:
            with io.open(ledger_path, "a", encoding="utf-8",
                         newline="\n") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False,
                                            sort_keys=True) + "\n")
            appended = len(rows)
            wrote = True
    report = {"schema": INGEST_SCHEMA, "tool": TOOL,
              "verdict_file": verdict_path, "target": target,
              "frame": frame, "points": POINT_COUNT,
              "citation_range_checked": line_count is not None,
              "ledger": ledger_path, "appended": appended,
              "ledger_records_skipped": skipped,
              "already_consistent": already, "wrote": wrote}
    _write_or_print(report, json_out)
    return 0


def _verify(target, faces, opts, json_out):
    if not os.path.isfile(target):
        raise VerifyError("missing", "target file not found: %s" % target)
    work = tempfile.mkdtemp(prefix="i18n-verify-")
    try:
        matrix, verdict = run_matrix(target, faces, opts, work)
    finally:
        _cleanup(work)
    _write_or_print(matrix, json_out)
    return VERDICT_EXIT[verdict]


def _cleanup(path):
    import shutil
    shutil.rmtree(path, ignore_errors=True)


def _parse_faces(raw):
    faces = [f.strip() for f in raw.split(",") if f.strip()]
    unknown = [f for f in faces if f not in ALL_FACES]
    if unknown or not faces:
        return None, unknown
    return faces, []


def main(argv=None):
    # stream faces are UTF-8 by contract; the console codepage on Windows
    # hosts must not gate what a report may carry
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    parser = argparse.ArgumentParser(
        prog="i18n_verify.py",
        description="E4 P4 verification matrix plus the P5 human ten-point "
                    "gate (emit form, ingest verdicts, append-only ledger "
                    "write-back; the engine does not judge)")
    parser.add_argument("--verify-target", metavar="P",
                        help="run the P4 mechanical faces over target P")
    parser.add_argument("--emit-tenpoint", metavar="P",
                        help="emit the ten-point review form for target P")
    parser.add_argument("--ingest-tenpoint", metavar="P",
                        help="ingest and validate the verdict file P")
    parser.add_argument("--selftest", action="store_true",
                        help="run the selftest vectors")
    parser.add_argument("--faces", default=",".join(DEFAULT_FACES),
                        metavar="LIST",
                        help="comma list from %s" % ",".join(ALL_FACES))
    parser.add_argument("--ai-flavor-tool", default=tool_path("ai_flavor.py"),
                        metavar="P")
    parser.add_argument("--norm-lint-tool", default=tool_path("norm_lint.py"),
                        metavar="P")
    parser.add_argument("--doc-lint-tool", default=tool_path("doc_lint.py"),
                        metavar="P")
    parser.add_argument("--repo", default=None, metavar="P",
                        help="repo root for the doc_lint face "
                             "(default: the tree containing this tool)")
    parser.add_argument("--jargon-map", default=default_jargon_map(),
                        metavar="P")
    parser.add_argument("--ledger", default=None, metavar="P",
                        help="segment ledger for the tenpoint_verdict "
                             "write-back (append-only)")
    parser.add_argument("--timestamp", default=None, metavar="UTC",
                        help="timestamp for appended ledger rows "
                             "(default: run time)")
    parser.add_argument("--json", default=None, metavar="P",
                        help="write the report to P instead of stdout")
    args = parser.parse_args(argv)

    modes = [name for name, given in
             (("verify", args.verify_target is not None),
              ("emit", args.emit_tenpoint is not None),
              ("ingest", args.ingest_tenpoint is not None),
              ("selftest", args.selftest)) if given]
    if len(modes) != 1:
        return usage(parser, "exactly one of --verify-target, "
                             "--emit-tenpoint, --ingest-tenpoint, "
                             "--selftest is required (got %s)"
                     % (", ".join(modes) or "none"))
    try:
        if args.selftest:
            return selftest(sys.stdout)
        if args.emit_tenpoint:
            code, message = _emit(args.emit_tenpoint, args.json)
            if code == "usage":
                return usage(parser, message)
            return code
        if args.ingest_tenpoint:
            return _ingest(args.ingest_tenpoint, args.ledger,
                           args.timestamp, args.json)
        faces, unknown = _parse_faces(args.faces)
        if faces is None:
            return usage(parser, "unknown or empty --faces list (%s)"
                         % ",".join(unknown))
        opts = {"ai_flavor_tool": args.ai_flavor_tool,
                "norm_lint_tool": args.norm_lint_tool,
                "doc_lint_tool": args.doc_lint_tool,
                "repo": args.repo or repo_root(),
                "jargon_map": args.jargon_map}
        return _verify(args.verify_target, faces, opts, args.json)
    except VerifyError as exc:
        sys.stderr.write("i18n_verify: %s\n" % exc)
        return 9 if exc.kind == "missing" else 1


if __name__ == "__main__":
    sys.exit(main())
