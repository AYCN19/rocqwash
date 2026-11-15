#!/usr/bin/env python3
"""tests/refinery_segments/seam.py -- refinery segment: the i18n seam vector.

Purpose.  Pin the seam between tools/i18n_pipeline.py (stages p0 to p6) and
  tools/i18n_verify.py (P5 verdict ingest): a run ledger that already
  carries the P0 policy row and the P6 close record must still accept the
  ten-point write-back, skipping the non-segment records without rewriting
  their bytes, and the whole chain must close green over the real corpus
  pair transcribed in tests/fixtures/refinery_seam/seam_corpus.json.
Interface.  run_segment_seam() -> (passed, failed, skipped, results) per
  the t_engines_body segment form; `python -I tests/refinery_segments/seam.py`
  runs the segment standalone; `--chain-out DIR` additionally copies the
  full-chain run directory (manifest, ledger, stage reports, chain log)
  into DIR as the evidence run; importing this module spawns nothing.
Dependencies.  Python 3 standard library only; the two pipeline tools are
  driven by subprocess under sys.executable -I from the repository root;
  docs/zh/engine-body.zh.md supplies the corpus fidelity check at run
  time; zero network by construction.
Evidence.  The pre-fix red reproduction and the full-chain green log of
  the OUT evidence run; tests/t_engines_body.py stays green alongside
  these vectors; tools/i18n_verify.py --selftest carries the unit-level
  seam vectors.
Exit-codes.  0 all checks green; 1 at least one FAIL (each named); 2
  usage error.
"""
# Vector conventions: the fill rows carry model_id "human" (the fill is a
# human-composed translation assembled from the en half of the corpus pair,
# see the fixture provenance field) and the fixed stamp 2000-01-01T00:00:00Z
# (a vector stamp, not a wall-clock claim).  The P4 matrix inside the pinned
# chain runs the three file-local faces (jargon, cjk, ai_flavor); the
# doc_lint face is repo-state dependent and belongs to the evidence run and
# the suite gates, not to this segment.

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
FIXTURE = os.path.join(HERE, os.pardir, "fixtures", "refinery_seam",
                       "seam_corpus.json")
CORPUS = os.path.join(REPO, "docs", "zh", "engine-body.zh.md")
PIPELINE_TOOL = os.path.join(REPO, "tools", "i18n_pipeline.py")
VERIFY_TOOL = os.path.join(REPO, "tools", "i18n_verify.py")
SEGMENT_NAME = "seam"
VECTOR_STAMP = "2000-01-01T00:00:00Z"
TARGET_NAME = os.path.join("target", "engine-body-seam.zh.md")
ARTIFACT_NAME = os.path.join("translated", "engine-body-seam.zh.md")


class ChainError(Exception):
    """A chain step exited nonzero; carries the step name and stderr."""


def _run(cmd, timeout_s=120):
    proc = subprocess.run([sys.executable, "-I", "-X", "utf8"] + cmd, cwd=REPO,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=timeout_s)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), \
        proc.stderr.decode("utf-8", "replace")


def _read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=1,
                                sort_keys=True) + "\n")


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False,
                                    sort_keys=True) + "\n")


def _ledger_lines(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def _load_fixture():
    with open(FIXTURE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _corpus_fidelity(fixture):
    with open(CORPUS, "r", encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    drifted = []
    for seg in fixture["segments"]:
        line_no = seg["corpus_line"]
        if lines[line_no - 1] != seg["source_text"]:
            drifted.append("line %d" % line_no)
    return drifted


def run_chain(run_dir):
    """Drive p0, p1, p3 phase A, the fill, p3 phase B, the P5 emit and
    ingest, the P4 matrix and p6 over the corpus fixture; returns the
    evidence dict.  Any nonzero stage raises ChainError."""
    fixture = _load_fixture()
    target = os.path.join(run_dir, TARGET_NAME.replace("/", os.sep))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n\n".join(s["source_text"]
                                 for s in fixture["segments"]) + "\n")
    manifest_path = os.path.join(run_dir, "run.json")
    manifest = {
        "run_id": "refinery-seam-fullchain",
        "target": {"path": target, "face": "repo"},
        "direction": "zh2en",
        "linkages": ["normalization", "standardization",
                     "internationalization", "de_ai_flavor"],
        "ledger_path": os.path.join(run_dir, "segment-ledger.jsonl"),
    }
    _write_json(manifest_path, manifest)
    ledger = manifest["ledger_path"]
    log = []
    steps = []

    def step(name, cmd):
        rc, out, err = _run(cmd)
        log.append("[stage %s] rc=%d%s" % (name, rc,
                   (" " + (err or out).strip()[:160]) if rc else ""))
        steps.append({"stage": name, "rc": rc})
        if rc != 0:
            raise ChainError("%s exited %d: %s" % (name, rc,
                                                   (err or out)[:400]))
        return rc, out, err

    def stage(name, stage_id, report_name):
        report = os.path.join(run_dir, report_name)
        step(name, [PIPELINE_TOOL, "--manifest", manifest_path,
                    "--stage", stage_id, "--json", report])
        return _read_json(report)

    p0 = stage("p0", "p0", "report-p0.json")
    p1 = stage("p1", "p1", "report-p1.json")
    p3a = stage("p3a", "p3", "report-p3a.json")
    if p3a.get("phase") != "handoff-emitted":
        raise ChainError("p3 phase A reports phase %r, expected "
                         "handoff-emitted" % p3a.get("phase"))
    handoff = os.path.join(run_dir, "translation-handoff.jsonl")
    rows = [json.loads(line) for line in _ledger_lines(handoff) if line]
    fills = {s["segment_id"]: s["fill"] for s in fixture["segments"]}
    filled = []
    for row in rows:
        item = dict(row)
        item["translated_text"] = fills[row["segment_id"]]
        item["model_id"] = "human"
        item["timestamp_utc"] = VECTOR_STAMP
        filled.append(item)
    _write_jsonl(os.path.join(run_dir, "translation-filled.jsonl"), filled)
    p3b = stage("p3b", "p3", "report-p3b.json")
    if p3b.get("phase") != "applied":
        raise ChainError("p3 phase B reports phase %r, expected applied"
                         % p3b.get("phase"))
    artifact = os.path.join(run_dir, ARTIFACT_NAME.replace("/", os.sep))
    if not os.path.isfile(artifact):
        raise ChainError("p3 phase B wrote no translated artifact at %s"
                         % artifact)
    with open(artifact, "r", encoding="utf-8") as handle:
        line_count = len(handle.read().splitlines())
    form_path = os.path.join(run_dir, "tenpoint-form.json")
    step("p5-emit", [VERIFY_TOOL, "--emit-tenpoint", artifact,
                     "--json", form_path])
    form = _read_json(form_path)
    verdicts = {"schema": "rocqwash.tenpoint.verdicts/1",
                "target": artifact, "frame": "ALL-PASS",
                "points": [{"point": row["point"], "verdict": "PASS",
                            "citation": str(min(row["point"], line_count)),
                            "note": ""}
                           for row in form["points"]]}
    verdicts_path = os.path.join(run_dir, "tenpoint-verdicts.json")
    _write_json(verdicts_path, verdicts)
    ingest_report = os.path.join(run_dir, "report-p5-ingest.json")
    step("p5-ingest", [VERIFY_TOOL, "--ingest-tenpoint", verdicts_path,
                       "--ledger", ledger, "--timestamp", VECTOR_STAMP,
                       "--json", ingest_report])
    ingest = _read_json(ingest_report)
    matrix_path = os.path.join(run_dir, "report-p4-matrix.json")
    step("p4-matrix", [VERIFY_TOOL, "--verify-target", artifact,
                       "--faces", "jargon,cjk,ai_flavor",
                       "--json", matrix_path])
    matrix = _read_json(matrix_path)
    p6 = stage("p6", "p6", "report-p6.json")
    rerun_report = os.path.join(run_dir, "report-p5-rerun.json")
    step("p5-rerun", [VERIFY_TOOL, "--ingest-tenpoint", verdicts_path,
                      "--ledger", ledger, "--json", rerun_report])
    rerun = _read_json(rerun_report)
    return {
        "run_dir": run_dir, "manifest": manifest_path, "ledger": ledger,
        "log": log, "steps": steps, "p0": p0, "p1": p1, "p3a": p3a,
        "p3b": p3b, "ingest": ingest, "matrix": matrix, "p6": p6,
        "rerun": rerun, "form": form, "artifact": artifact,
        "line_count": line_count, "fixture": fixture,
    }


def _assert_chain(evidence):
    """Named assertions over one completed chain run."""
    fixture = evidence["fixture"]
    ledger = evidence["ledger"]
    policy_line = _ledger_lines(ledger)[0] + "\n"
    policy_bytes = policy_line.encode("utf-8")
    rows = [json.loads(line) for line in _ledger_lines(ledger) if line]
    details = {}
    details["p0-accepted"] = evidence["p0"]["verdict"] == "accepted"
    details["policy-row-first"] = rows[0].get("record_type") == "policy"
    segments = _read_json(os.path.join(evidence["run_dir"],
                                       "segments.json"))["segments"]
    details["p1-two-segments"] = (
        len(segments) == len(fixture["segments"])
        and all(s["source_text"] == f["source_text"]
                for s, f in zip(segments, fixture["segments"])))
    written = evidence["p3b"].get("ledger_rows_written")
    details["p3b-ledger-rows"] = written == len(fixture["segments"])
    findings = evidence["p3b"].get("findings_tally", {})
    harmful = [k for k in findings
               if k.split("/", 1)[-1] in ("protection-drift", "cjk-residue",
                                          "em-dash-density")]
    details["p3b-register-clean"] = not harmful
    ingest = evidence["ingest"]
    details["p5-ingest-green"] = (
        ingest["appended"] == len(fixture["segments"])
        and ingest["ledger_records_skipped"] == 1
        and ingest["already_consistent"] is False)
    after = [json.loads(line) for line in _ledger_lines(ledger) if line]
    details["policy-bytes-intact"] = \
        open(ledger, "rb").read().startswith(policy_bytes)
    count = len(fixture["segments"])
    write_back = after[1 + count:-1]
    details["write-back-segment-rows-only"] = (
        len(after) == 1 + 2 * count + 1
        and all(row.get("record_type") is None for row in write_back)
        and all(row["tenpoint_verdict"] == "ALL-PASS"
                for row in write_back))
    details["p4-matrix-clean"] = (evidence["matrix"]["verdict"] == "clean"
                                  and evidence["steps"][-3]["rc"] == 0)
    details["p6-closed"] = evidence["p6"]["verdict"] == "closed"
    close_rows = [row for row in after if row.get("record_type") == "close"]
    details["close-row-last"] = (
        len(close_rows) == 1 and after[-1].get("record_type") == "close")
    rerun = evidence["rerun"]
    details["ingest-idempotent"] = (
        rerun["appended"] == 0 and rerun["already_consistent"] is True
        and rerun["ledger_records_skipped"] == 2
        and len(_ledger_lines(ledger)) == 1 + 2 * count + 1)
    return details


def run_segment_seam():
    """The seam segment: corpus fidelity, the full-chain green vector and
    the headless-row negative control; returns the segment tally."""
    results = []

    def check(name, thunk):
        try:
            detail = thunk()
        except AssertionError as exc:
            results.append(("FAIL", name, str(exc)))
        except ChainError as exc:
            results.append(("FAIL", name, str(exc)))
        except Exception as exc:
            results.append(("FAIL", name,
                            "%s: %s" % (type(exc).__name__, exc)))
        else:
            if detail is None:
                results.append(("SKIP", name, "precondition absent"))
            else:
                results.append(("PASS", name, detail))

    def _thunk_corpus_fidelity():
        fixture = _load_fixture()
        drifted = _corpus_fidelity(fixture)
        assert not drifted, (
            "corpus fixture out of sync with %s (%s); regenerate the "
            "fixture" % (CORPUS, ", ".join(drifted)))
        return "fixture paragraphs byte-match %s lines %s" % (
            os.path.relpath(CORPUS, REPO),
            ", ".join(str(s["corpus_line"]) for s in fixture["segments"]))

    def _thunk_fullchain():
        work = tempfile.mkdtemp(prefix="seam_fullchain_")
        try:
            evidence = run_chain(work)
            details = _assert_chain(evidence)
            red = [k for k, ok in details.items() if not ok]
            assert not red, "chain assertions red: %s" % ", ".join(red)
            return ("p0 accepted, policy row first; p1 %d real-prose "
                    "segments; p3 handoff and applied (register clean); "
                    "p5 ingest skipped=%d appended=%d; policy row bytes "
                    "intact; p4 matrix clean; p6 closed; rerun idempotent"
                    % (len(evidence["fixture"]["segments"]),
                       evidence["ingest"]["ledger_records_skipped"],
                       evidence["ingest"]["appended"]))
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def _thunk_headless_rejection():
        work = tempfile.mkdtemp(prefix="seam_headless_")
        try:
            fixture = _load_fixture()
            target = os.path.join(work, "doc.md")
            with open(target, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join("line %d" % n for n in range(1, 13))
                         + "\n")
            ledger = os.path.join(work, "ledger.jsonl")
            with open(ledger, "w", encoding="utf-8", newline="\n") as fh:
                fh.write('{"unrelated": true}\n')
                fh.write(json.dumps(
                    {"segment_id": "s0001", "direction": "zh2en",
                     "source_span": {"start_line": 1, "end_line": 1},
                     "model_id": "human", "annotation_site": "human",
                     "prompt_template_ref": "prompts/zh2en-repo-v1",
                     "linkages_run": ["normalization"],
                     "policy_precheck_ref": "P0-repo-headless-vector",
                     "tenpoint_verdict": "PENDING",
                     "timestamp_utc": VECTOR_STAMP}, sort_keys=True) + "\n")
            verdicts = {"schema": "rocqwash.tenpoint.verdicts/1",
                        "target": target, "frame": "ALL-PASS",
                        "points": [{"point": n, "verdict": "PASS",
                                    "citation": str(min(n, 12)), "note": ""}
                                   for n in range(1, 11)]}
            verdicts_path = os.path.join(work, "verdicts.json")
            _write_json(verdicts_path, verdicts)
            rc, _out, err = _run([VERIFY_TOOL, "--ingest-tenpoint",
                                  verdicts_path, "--ledger", ledger])
            assert rc == 1, "headless row accepted (rc=%d)" % rc
            assert "not a segment row" in err, (
                "rejection does not name the headless row: %r" % err[:160])
            return "ledger row with no record_type still rejected (rc=1, " \
                   "named)"
        finally:
            shutil.rmtree(work, ignore_errors=True)

    check("corpus-fidelity", _thunk_corpus_fidelity)
    check("fullchain-p0-to-p6-green", _thunk_fullchain)
    check("headless-row-still-rejected", _thunk_headless_rejection)
    passed = sum(1 for status, _n, _d in results if status == "PASS")
    failed = sum(1 for status, _n, _d in results if status == "FAIL")
    skipped = sum(1 for status, _n, _d in results if status == "SKIP")
    return passed, failed, skipped, results


def _write_chain_out(out_dir):
    """Evidence run: rerun the chain in a fresh directory and copy the run
    directory plus the chain log into out_dir."""
    work = tempfile.mkdtemp(prefix="seam_evidence_")
    try:
        evidence = run_chain(work)
        details = _assert_chain(evidence)
        os.makedirs(out_dir, exist_ok=True)
        keep = ("run.json", "segments.json", "segment-ledger.jsonl",
                "translation-handoff.jsonl", "translation-filled.jsonl",
                "tenpoint-form.json", "tenpoint-verdicts.json",
                "report-p0.json", "report-p1.json", "report-p3a.json",
                "report-p3b.json", "report-p5-ingest.json",
                "report-p4-matrix.json", "report-p6.json",
                "report-p5-rerun.json")
        # a rerun regenerates exactly the files this face owns; anything
        # else under out_dir is left untouched
        stale = keep + ("chain-log.md",)
        for name in stale:
            candidate = os.path.join(out_dir, name)
            if os.path.isfile(candidate):
                os.remove(candidate)
        stale_artifacts = os.path.join(out_dir, "translated")
        if os.path.isdir(stale_artifacts):
            shutil.rmtree(stale_artifacts)
        for name in keep:
            source = os.path.join(work, name)
            if os.path.isfile(source):
                shutil.copy2(source, os.path.join(out_dir, name))
        artifact_dir = os.path.dirname(evidence["artifact"])
        if os.path.isdir(artifact_dir):
            shutil.copytree(artifact_dir,
                            os.path.join(out_dir, "translated"))
        red = [k for k, ok in details.items() if not ok]
        lines = [
            "# seam full-chain evidence run (p0 -> p6 over the real corpus)",
            "",
            "Corpus: tests/fixtures/refinery_seam/seam_corpus.json",
            "(verbatim paragraphs of docs/zh/engine-body.zh.md; fills from",
            "docs/engine-body-capabilities.md, see the fixture provenance).",
            "",
            "## Stage log",
            "",
        ]
        lines.extend(evidence["log"])
        lines.extend(["", "## Assertion details", ""])
        for name in sorted(details):
            lines.append("- %s: %s" % (
                "PASS" if details[name] else "FAIL", name))
        lines.extend(["", "VERDICT: %s" % (
            "GREEN" if not red else "RED (%s)" % ", ".join(red))])
        with open(os.path.join(out_dir, "chain-log.md"), "w",
                  encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines) + "\n")
        return 0 if not red else 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


USAGE = (
    "usage: python -I tests/refinery_segments/seam.py [--chain-out DIR]\n"
    "  bare          run the seam segment (exit 0 green, 1 red)\n"
    "  --chain-out D run the chain and copy the evidence run into D"
)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    chain_out = None
    if argv and argv[0] == "--chain-out":
        if len(argv) != 2:
            sys.stderr.write(USAGE + "\n")
            return 2
        chain_out = os.path.abspath(argv[1])
    elif argv:
        sys.stderr.write("usage error: unknown argument %r\n" % (argv[0],))
        sys.stderr.write(USAGE + "\n")
        return 2
    if chain_out is not None:
        return _write_chain_out(chain_out)
    passed, failed, skipped, results = run_segment_seam()
    for status, name, detail in results:
        print("%s %s/%s -- %s" % (status, SEGMENT_NAME, name, detail))
    print("SEGMENT %s passed=%d failed=%d skipped=%d"
          % (SEGMENT_NAME, passed, failed, skipped))
    if failed:
        print("TOTAL-SEAM RED (%d failed check(s))" % failed)
        return 1
    print("TOTAL-SEAM GREEN (%d passed, %d skipped)" % (passed, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
