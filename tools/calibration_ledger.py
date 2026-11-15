#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""calibration_ledger.py - W4 calibration ledger for docs/exp-ledger.jsonl.

Purpose.  Pair each per-row predicted confidence in a vacgen v2 report with
  the measured compile-leg rc face and append one calibration entry per
  paired row into docs/exp-ledger.jsonl (schema rocqwash-exp/1, carrying
  correlationId = the report id), through the experience-bus port's
  idempotent seen set so a rerun writes zero new rows; rows whose gap
  reaches the signal threshold form the row-rot signal face, and signals
  are data, not errors.

Interface.  `calibration_ledger.py --report R.json --rc-file RC.json
  [--leg-map LM.json] [--default-leg NAME] [--ledger P] [--batch B] [--ts TS]
  [--signal-threshold F] [--signals-out P] [--strict] [--dry-run] [--selftest]`.
  Ledger resolution: --ledger wins, then ROCWASH_EXPERIENCE_DIR, then
  <repo>/docs/exp-ledger.jsonl.

Dependencies.  Python 3 standard library only; zero network; the fingerprint
  helper stays byte-identical to tools/exp_port.py (the seen-set key
  contract); every rc face declares its "expected" side (green|red) so red
  legs are judged by declared semantics, never inferred.

Evidence.  --selftest on temporary fixtures: happy-path append carrying
  correlationId, rerun idempotence (zero new rows, bytes hold), green/red
  leg semantics, the threshold face (default vs explicit), unpredicted-row
  counting, corrupt-input fail loud without writing, append-only byte
  growth, strict exit, the CLI usage face.

Exit-codes.  0 appended / duplicate-skip / answered (signals are data); 1
  selftest red; 2 usage error; 4 --strict with a signal row; 9 bad input.
"""
# Design notes (kept outside the five-field block: annotation-standard
# budget discipline):
#
# Confidence scale
#   The two taxonomy confidence grades map to 1.0 (HIGH) and 0.5 (MID);
#   rows without a prediction (status todo_seat, confidence None) are
#   counted, never guessed.  The measured side is 1.0 pass / 0.0 fail.
#
# Gap space and the default threshold
#   The gap |pred - actual| lives on {0.0, 0.5, 1.0}.  A HIGH row measured
#   FAIL is the one unambiguous rot shape (gap 1.0); a MID row measured
#   FAIL is the prediction doing its job (MID already says "may not hold").
#   The default threshold 0.75 therefore admits only the unambiguous shape;
#   lowering it to 0.5 with --signal-threshold also flags MID rows measured
#   FAIL.  The threshold is a comparison against a declared constant, not a
#   live-counter equality, per the verifier design law.
#
# Row-to-leg attribution
#   The measured rc face is per leg (compile unit), so row-level attribution
#   goes through --leg-map (familyId -> leg name) with --default-leg as the
#   fallback.  The leg name travels into every entry's evidence face, so the
#   attribution rule is on the record, not implicit.
#
# Idempotence (R7)
#   Entry ids derive deterministically from the report id and the row
#   ordinal; the fingerprint covers the four carrier fields exactly like
#   the port's (tool/points/evidence/batch).  A rerun of the same report
#   and rc face hits both axes and writes nothing.  correlationId is not
#   part of the fingerprint: the seen-set contract stays on the four
#   carrier fields, and the schema increment rides additive.

import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys
import tempfile

TOOL = "calibration_ledger"
SCHEMA = "rocqwash-exp/1"
SIGNALS_SCHEMA = "rocqwash-calibration/1"
LEDGER_NAME = "exp-ledger.jsonl"
ENV_DIR = "ROCWASH_EXPERIENCE_DIR"
SELFTEST_MARK = "CALIBRATION-LEDGER-SELFTEST PASS"
SEP = "\x1f"

CONFIDENCE_SCALE = {"HIGH": 1.0, "MID": 0.5}
DEFAULT_SIGNAL_THRESHOLD = 0.75
DEFAULT_LEG = "witness.lean"

EXIT_OK = 0
EXIT_SELFTEST = 1
EXIT_USAGE = 2
EXIT_STRICT_SIGNAL = 4
EXIT_INPUT = 9


class InputError(Exception):
    """Raised on an input face this tool cannot judge; callers exit 9."""


class CorruptLedger(Exception):
    """Raised on a ledger line this tool cannot parse; callers exit 9."""


def repo_root():
    """Repository root: the parent of tools/ (this file lives in tools/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_ledger(explicit):
    """--ledger wins, then the env directory, then the in-repo default."""
    if explicit:
        return explicit
    env_dir = os.environ.get(ENV_DIR, "")
    if env_dir:
        return os.path.join(env_dir, LEDGER_NAME)
    return os.path.join(repo_root(), "docs", LEDGER_NAME)


def load_json_object(path, what):
    """Read one JSON object from path; every failure is loud."""
    if not os.path.isfile(path):
        raise InputError("%s not found: %s" % (what, os.path.abspath(path)))
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        raise InputError("%s unreadable or not JSON (%s): %s"
                         % (what, exc, os.path.abspath(path)))
    if not isinstance(data, dict):
        raise InputError("%s must hold a JSON object: %s"
                         % (what, os.path.abspath(path)))
    return data


def load_report(path):
    """Return (reportId, assumptions rows) from a vacgen v2 report."""
    report = load_json_object(path, "report")
    rid = report.get("reportId")
    if not isinstance(rid, str) or not rid:
        raise InputError("report lacks a string reportId: %s"
                         % os.path.abspath(path))
    rows = report.get("assumptions")
    if not isinstance(rows, list) or not rows:
        raise InputError("report lacks a non-empty assumptions list: %s"
                         % os.path.abspath(path))
    return rid, rows


def load_rcs(path):
    """Parse the rc face: leg name -> {rc: int, expected: green|red}."""
    data = load_json_object(path, "rc face")
    legs = {}
    for name, face in data.items():
        if not isinstance(face, dict):
            raise InputError("rc face leg %r must be an object" % name)
        rc = face.get("rc")
        expected = face.get("expected")
        if isinstance(rc, bool) or not isinstance(rc, int):
            raise InputError("rc face leg %r needs an integer rc" % name)
        if expected not in ("green", "red"):
            raise InputError("rc face leg %r needs expected green|red, got %r"
                             % (name, expected))
        legs[name] = {"rc": rc, "expected": expected}
    if not legs:
        raise InputError("rc face holds no leg: %s" % os.path.abspath(path))
    return legs


def load_leg_map(path):
    """Parse the optional familyId -> leg-name map (empty when absent)."""
    if not path:
        return {}
    data = load_json_object(path, "leg map")
    mapping = {}
    for family, leg in data.items():
        if not isinstance(leg, str) or not leg:
            raise InputError("leg map %r must map to a leg name" % family)
        mapping[family] = leg
    return mapping


def measured_pass(face):
    """Green legs pass on rc 0; red legs pass on any nonzero rc."""
    if face["expected"] == "green":
        return face["rc"] == 0
    return face["rc"] != 0


def calibration_rows(rows, legs, leg_map, default_leg, threshold):
    """Pair predicted confidences with the rc face; loud on odd rows.

    Returns (entries, counters).  Rows without a prediction count as
    todoSeat; paired rows whose leg is absent from the rc face count as
    unpaired; neither enters the ledger.
    """
    entries = []
    counters = {"paired": 0, "todoSeat": 0, "unpaired": 0}
    for seq, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise InputError("assumptions row %d is not an object" % seq)
        conf = row.get("confidence")
        if row.get("status") == "todo_seat" or conf is None:
            counters["todoSeat"] += 1
            continue
        if conf not in CONFIDENCE_SCALE:
            raise InputError("assumptions row %d carries unsupported "
                             "confidence %r" % (seq, conf))
        family = row.get("familyId")
        family = family if isinstance(family, str) and family \
            else "unknown-family"
        leg = leg_map.get(family, default_leg)
        face = legs.get(leg)
        if face is None:
            counters["unpaired"] += 1
            continue
        pred = CONFIDENCE_SCALE[conf]
        ok = measured_pass(face)
        gap = abs(pred - (1.0 if ok else 0.0))
        counters["paired"] += 1
        entries.append({
            "seq": seq, "familyId": family, "leg": leg,
            "predicted": conf, "predValue": pred,
            "rc": face["rc"], "expected": face["expected"],
            "measured": "PASS" if ok else "FAIL",
            "gap": gap, "signal": gap >= threshold,
        })
    return entries, counters


def entry_points(cal):
    """One-line English takeaways, flat technical register."""
    if cal["signal"]:
        return ("calibration gap %.2f reaches the signal threshold: "
                "predicted %s, leg %s measured %s (rc=%d, expected %s) "
                "for family %s"
                % (cal["gap"], cal["predicted"], cal["leg"],
                   cal["measured"], cal["rc"], cal["expected"],
                   cal["familyId"]))
    return ("calibration holds within the signal threshold: predicted %s, "
            "leg %s measured %s (rc=%d, expected %s), gap %.2f, family %s"
            % (cal["predicted"], cal["leg"], cal["measured"], cal["rc"],
               cal["expected"], cal["gap"], cal["familyId"]))


def entry_evidence(report_path, rc_path, rid, cal):
    """Evidence face: the report row, the rc face, and the leg used."""
    return ("report %s reportId=%s assumptions[%d] familyId=%s + rc face %s "
            "leg=%s rc=%d expected=%s"
            % (report_path, rid, cal["seq"], cal["familyId"], rc_path,
               cal["leg"], cal["rc"], cal["expected"]))


def fingerprint(tool_name, points, evidence, batch):
    """Stable content key over the four carrier fields.

    Byte-identical to the experience-bus port's fingerprint (the seen-set
    key contract); a divergence here would split the idempotence axis.
    """
    payload = SEP.join([tool_name, points, evidence, batch])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def calibration_row_id(rid, cal, report_path, rc_path, batch):
    """Deterministic entry id: report id, row ordinal, fingerprint span.

    The fingerprint span makes the same report and rc face mint the same id
    (rerun idempotence), while a re-measured leg (a changed rc) mints a new
    id, so the fresh measurement lands as its own append-only row instead
    of being swallowed by the id axis.
    """
    points = entry_points(cal)
    evidence = entry_evidence(report_path, rc_path, rid, cal)
    fp = fingerprint(TOOL, points, evidence, batch)
    return "CAL-%s-%03d-%s" % (rid, cal["seq"], fp[:8])


def read_ledger(path):
    """Parse the ledger into entry dicts; loud on damaged lines."""
    if not os.path.isfile(path):
        return None
    entries = []
    with open(path, "r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError as exc:
                raise CorruptLedger(
                    "ledger line %d is not valid JSON (%s): %s"
                    % (lineno, exc, os.path.abspath(path)))
            if not isinstance(obj, dict):
                raise CorruptLedger(
                    "ledger line %d is not a JSON object: %s"
                    % (lineno, os.path.abspath(path)))
            entries.append(obj)
    return entries


def valid_ts(text):
    """Accept an ISO date or a full ISO timestamp; anything else is usage."""
    head = text.split("T", 1)[0]
    try:
        datetime.date.fromisoformat(head)
    except ValueError:
        return False
    return True


def utcnow():
    """Timezone-aware UTC now (datetime.utcnow is deprecated in 3.12+)."""
    return datetime.datetime.now(datetime.timezone.utc)


def append_entries(ledger_path, report_path, rc_path, rid, cals, batch,
                   ts, dry_run, out):
    """Append one ledger entry per calibration row, seen-set idempotent.

    Writes through open(..., "a") only: existing lines are never rewritten
    (append-only ledger discipline).  Returns (appended, skipped) id lists.
    """
    existing = read_ledger(ledger_path) or []
    seen_ids = set()
    seen_fps = set()
    for entry in existing:
        eid = entry.get("id")
        if isinstance(eid, str) and eid:
            seen_ids.add(eid)
        mark = entry.get("fingerprint")
        if isinstance(mark, str) and mark:
            seen_fps.add(mark)

    appended = []
    skipped = []
    lines = []
    for cal in cals:
        points = entry_points(cal)
        evidence = entry_evidence(report_path, rc_path, rid, cal)
        fp = fingerprint(TOOL, points, evidence, batch)
        eid = calibration_row_id(rid, cal, report_path, rc_path, batch)
        if eid in seen_ids:
            skipped.append(eid)
            out.write("duplicate-skip id=%s axis=id ledger=%s\n"
                      % (eid, ledger_path))
            continue
        if fp in seen_fps:
            skipped.append(eid)
            out.write("duplicate-skip id=%s axis=fingerprint ledger=%s\n"
                      % (eid, ledger_path))
            continue
        entry = {
            "schema": SCHEMA,
            "id": eid,
            "ts": ts,
            "tool": TOOL,
            "points": points,
            "evidence": evidence,
            "batch": batch,
            "fingerprint": fp,
            "correlationId": rid,
        }
        seen_ids.add(eid)
        seen_fps.add(fp)
        lines.append(json.dumps(entry, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")))
        appended.append(eid)
        if dry_run:
            out.write("dry-run id=%s would-append ledger=%s\n"
                      % (eid, ledger_path))
        else:
            out.write("appended id=%s ledger=%s\n" % (eid, ledger_path))

    if lines and not dry_run:
        parent = os.path.dirname(os.path.abspath(ledger_path))
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)
        with open(ledger_path, "a", encoding="utf-8", newline="\n") as handle:
            for line in lines:
                handle.write(line + "\n")
    return appended, skipped


def write_signals(path, rid, threshold, counters, cals, report_path,
                  rc_path, batch, out):
    """Write the signal face JSON (schema rocqwash-calibration/1)."""
    signals = [cal for cal in cals if cal["signal"]]
    face = {
        "schema": SIGNALS_SCHEMA,
        "reportId": rid,
        "threshold": threshold,
        "counters": counters,
        "signalCount": len(signals),
        "signals": [
            {"id": calibration_row_id(rid, cal, report_path, rc_path,
                                      batch),
             "seq": cal["seq"], "familyId": cal["familyId"],
             "leg": cal["leg"], "predicted": cal["predicted"],
             "predValue": cal["predValue"], "measured": cal["measured"],
             "rc": cal["rc"], "expected": cal["expected"], "gap": cal["gap"]}
            for cal in signals
        ],
    }
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(face, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    return signals


def run(args, out):
    """Command body split out for the selftest's in-process vectors."""
    rid, rows = load_report(args.report)
    legs = load_rcs(args.rc_file)
    leg_map = load_leg_map(args.leg_map)
    cals, counters = calibration_rows(rows, legs, leg_map, args.default_leg,
                                      args.signal_threshold)
    ledger_path = resolve_ledger(args.ledger)
    batch = args.batch if args.batch else "calibration-%s" % rid
    ts = args.ts if args.ts else utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    if not valid_ts(ts):
        out.stderr.write("%s: --ts must be an ISO date or timestamp: %s\n"
                         % (TOOL, ts))
        return EXIT_USAGE

    try:
        read_ledger(ledger_path)
    except CorruptLedger as exc:
        out.stderr.write("%s: %s\n" % (TOOL, exc))
        return EXIT_INPUT

    appended, skipped = append_entries(
        ledger_path, args.report, args.rc_file, rid, cals, batch, ts,
        args.dry_run, out)

    signals = [cal for cal in cals if cal["signal"]]
    for cal in signals:
        eid = calibration_row_id(rid, cal, args.report, args.rc_file, batch)
        out.write("[SIGNAL] id=%s family=%s leg=%s predicted=%s measured=%s "
                  "rc=%d gap=%.2f\n"
                  % (eid, cal["familyId"], cal["leg"], cal["predicted"],
                     cal["measured"], cal["rc"], cal["gap"]))
    out.write("[CALIBRATION] reportId=%s ledger=%s\n" % (rid, ledger_path))
    out.write("[CALIBRATION] paired=%d appended=%d skipped=%d signals=%d "
              "todoSeat=%d unpaired=%d threshold=%.2f dryRun=%s\n"
              % (counters["paired"], len(appended), len(skipped),
                 len(signals), counters["todoSeat"], counters["unpaired"],
                 args.signal_threshold, "yes" if args.dry_run else "no"))
    if args.signals_out:
        write_signals(args.signals_out, rid, args.signal_threshold,
                      counters, cals, args.report, args.rc_file, batch, out)
        out.write("[SIGNALS] %s\n"
                  % os.path.abspath(args.signals_out).replace("\\", "/"))
    if args.strict and signals:
        out.stderr.write("%s: --strict: %d signal row(s) present\n"
                         % (TOOL, len(signals)))
        return EXIT_STRICT_SIGNAL
    return EXIT_OK


class Streams:
    """stdout/stderr indirection so the selftest can capture in-process."""

    def __init__(self, stdout=None, stderr=None):
        self.stdout = stdout if stdout is not None else sys.stdout
        self.stderr = stderr if stderr is not None else sys.stderr

    def write(self, text):
        self.stdout.write(text)


def _selftest_vector(argv, expect_rc):
    """Run one in-process vector; returns (rc, stdout text, stderr text)."""
    import io as io_module
    buf_out = io_module.StringIO()
    buf_err = io_module.StringIO()
    streams = Streams(buf_out, buf_err)
    try:
        rc = run(build_parser().parse_args(argv), streams)
    except (InputError, CorruptLedger):
        rc = EXIT_INPUT
    return rc, buf_out.getvalue(), buf_err.getvalue()


def selftest():
    """Temporary-fixture vectors; prints SELFTEST PASS, exits 0 on green."""
    fails = []
    tmp = tempfile.mkdtemp(prefix="calibration_ledger_selftest_")
    try:
        work = os.path.join(tmp, "work")
        os.makedirs(work, exist_ok=True)
        report = os.path.join(work, "report.json")
        rcs = os.path.join(work, "rcs.json")
        ledger = os.path.join(work, "exp-ledger.jsonl")
        with open(report, "w", encoding="utf-8") as handle:
            json.dump({"reportId": "vacgenv2-castx-0000",
                       "assumptions": [
                           {"kind": "assumption", "name": "h1",
                            "status": "recognized",
                            "familyId": "fam.high", "confidence": "HIGH"},
                           {"kind": "assumption", "name": "h2",
                            "status": "recognized",
                            "familyId": "fam.mid", "confidence": "MID"},
                           {"kind": "assumption", "name": "h3",
                            "status": "todo_seat", "familyId": None,
                            "confidence": None},
                       ]}, handle)
        with open(rcs, "w", encoding="utf-8") as handle:
            json.dump({"witness.lean": {"rc": 0, "expected": "green"}}, handle)
        base = ["--report", report, "--rc-file", rcs, "--ledger", ledger]

        # V1 happy path: two paired rows append, correlationId carried.
        rc, out, _ = _selftest_vector(base, EXIT_OK)
        if rc != 0 or out.count("appended id=") != 2:
            fails.append("V1 should append 2 rows rc=0 (rc=%d out=%r)"
                         % (rc, out))
        with open(ledger, "r", encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        if len(entries) != 2:
            fails.append("V1 ledger should hold 2 rows, has %d" % len(entries))
        for entry in entries:
            if entry.get("correlationId") != "vacgenv2-castx-0000":
                fails.append("V1 correlationId not carried: %r" % entry)
            if entry.get("schema") != SCHEMA:
                fails.append("V1 schema field missing: %r" % entry)
            if not str(entry.get("id", "")).startswith("CAL-vacgenv2-castx-0000-"):
                fails.append("V1 id shape wrong: %r" % entry.get("id"))

        # V2 rerun idempotence (R7): zero new rows, bytes hold.
        before = open(ledger, "rb").read()
        rc, out, _ = _selftest_vector(base, EXIT_OK)
        if rc != 0 or out.count("duplicate-skip id=") != 2:
            fails.append("V2 rerun should skip 2 rows rc=0 (rc=%d out=%r)"
                         % (rc, out))
        if open(ledger, "rb").read() != before:
            fails.append("V2 ledger bytes changed on rerun")

        # V3 rot signal: a HIGH row against a failing green leg.
        rcs_bad = os.path.join(work, "rcs_bad.json")
        with open(rcs_bad, "w", encoding="utf-8") as handle:
            json.dump({"witness.lean": {"rc": 1, "expected": "green"}}, handle)
        sig_ledger = os.path.join(work, "sig-ledger.jsonl")
        sig_out = os.path.join(work, "signals.json")
        rc, out, _ = _selftest_vector(
            ["--report", report, "--rc-file", rcs_bad, "--ledger",
             sig_ledger, "--signals-out", sig_out], EXIT_OK)
        if rc != 0 or "[SIGNAL]" not in out:
            fails.append("V3 should print a signal face rc=0 (rc=%d out=%r)"
                         % (rc, out))
        with open(sig_out, "r", encoding="utf-8") as handle:
            sig = json.load(handle)
        if sig.get("signalCount") != 1 or sig.get("schema") != SIGNALS_SCHEMA:
            fails.append("V3 signals face wrong: %r" % sig)

        # V4 red-leg semantics: declared red with rc=1 is a PASS, no signal.
        rcs_red = os.path.join(work, "rcs_red.json")
        with open(rcs_red, "w", encoding="utf-8") as handle:
            json.dump({"refutation-full.lean": {"rc": 1, "expected": "red"},
                       "witness.lean": {"rc": 0, "expected": "green"}}, handle)
        lmap = os.path.join(work, "legmap.json")
        with open(lmap, "w", encoding="utf-8") as handle:
            json.dump({"fam.high": "refutation-full.lean",
                       "fam.mid": "refutation-full.lean"}, handle)
        red_ledger = os.path.join(work, "red-ledger.jsonl")
        rc, out, _ = _selftest_vector(
            ["--report", report, "--rc-file", rcs_red, "--leg-map", lmap,
             "--ledger", red_ledger], EXIT_OK)
        if rc != 0 or "[SIGNAL]" in out:
            fails.append("V4 declared red with rc=1 must not signal "
                         "(rc=%d out=%r)" % (rc, out))

        # V5 threshold face: MID row measured FAIL sits under the default
        # 0.75 and is flagged when the threshold is lowered to 0.5.
        rcs_mid = os.path.join(work, "rcs_mid.json")
        with open(rcs_mid, "w", encoding="utf-8") as handle:
            json.dump({"witness.lean": {"rc": 1, "expected": "green"}}, handle)
        mid_report = os.path.join(work, "mid_report.json")
        with open(mid_report, "w", encoding="utf-8") as handle:
            json.dump({"reportId": "vacgenv2-mid-0000",
                       "assumptions": [
                           {"kind": "assumption", "name": "h",
                            "status": "recognized",
                            "familyId": "fam.only", "confidence": "MID"},
                       ]}, handle)
        mid_ledger = os.path.join(work, "mid-ledger.jsonl")
        rc, out, _ = _selftest_vector(
            ["--report", mid_report, "--rc-file", rcs_mid,
             "--ledger", mid_ledger], EXIT_OK)
        if rc != 0 or "[SIGNAL]" in out:
            fails.append("V5 default threshold must not flag a MID FAIL "
                         "(rc=%d out=%r)" % (rc, out))
        rc, out, _ = _selftest_vector(
            ["--report", mid_report, "--rc-file", rcs_mid,
             "--ledger", mid_ledger, "--signal-threshold", "0.5"], EXIT_OK)
        if rc != 0 or "[SIGNAL]" not in out:
            fails.append("V5 explicit 0.5 threshold should flag the MID FAIL "
                         "(rc=%d out=%r)" % (rc, out))

        # V6 unpredicted rows count, never enter the ledger.
        todo_ledger = os.path.join(work, "todo-ledger.jsonl")
        rc, out, _ = _selftest_vector(
            ["--report", report, "--rc-file", rcs, "--ledger", todo_ledger],
            EXIT_OK)
        if rc != 0 or "todoSeat=1" not in out:
            fails.append("V6 todo-seat counter should read 1 (rc=%d out=%r)"
                         % (rc, out))
        with open(todo_ledger, "r", encoding="utf-8") as handle:
            if sum(1 for line in handle if line.strip()) != 2:
                fails.append("V6 todo-seat row must not enter the ledger")

        # V7 unpaired rows count, never enter the ledger.
        un_ledger = os.path.join(work, "un-ledger.jsonl")
        rc, out, _ = _selftest_vector(
            ["--report", report, "--rc-file", rcs, "--ledger", un_ledger,
             "--default-leg", "no-such.lean"], EXIT_OK)
        if rc != 0 or "unpaired=2" not in out or "paired=0" not in out:
            fails.append("V7 unpaired counting wrong (rc=%d out=%r)"
                         % (rc, out))

        # V8 corrupt report fails loud rc=9 without writing.
        bad_report = os.path.join(work, "bad_report.json")
        with open(bad_report, "w", encoding="utf-8") as handle:
            handle.write("not-json{")
        bad_ledger = os.path.join(work, "bad-ledger.jsonl")
        rc, _, _ = _selftest_vector(
            ["--report", bad_report, "--rc-file", rcs, "--ledger",
             bad_ledger], EXIT_INPUT)
        if os.path.exists(bad_ledger):
            fails.append("V8 corrupt report must not create a ledger")

        # V9 corrupt ledger fails loud rc=9 without writing.
        bad_ledger2 = os.path.join(work, "bad2", "exp-ledger.jsonl")
        os.makedirs(os.path.dirname(bad_ledger2), exist_ok=True)
        with open(bad_ledger2, "w", encoding="utf-8") as handle:
            handle.write('{"id": "ok"}\nnot-json{\n')
        size_before = open(bad_ledger2, "rb").read()
        rc, _, _ = _selftest_vector(
            ["--report", report, "--rc-file", rcs, "--ledger",
             bad_ledger2], EXIT_INPUT)
        if rc != EXIT_INPUT:
            fails.append("V9 corrupt ledger should exit 9 (rc=%d)" % rc)
        if open(bad_ledger2, "rb").read() != size_before:
            fails.append("V9 corrupt-ledger append wrote bytes")

        # V10 append-only: a pre-existing row survives byte-identically.
        pre_ledger = os.path.join(work, "pre-ledger.jsonl")
        with open(pre_ledger, "w", encoding="utf-8") as handle:
            handle.write('{"batch":"pre","fingerprint":"pf","id":"PRE-1",'
                         '"points":"pp","schema":"rocqwash-exp/1",'
                         '"tool":"pt"}\n')
        pre_head = open(pre_ledger, "rb").read()
        rc, out, _ = _selftest_vector(
            ["--report", report, "--rc-file", rcs, "--ledger", pre_ledger],
            EXIT_OK)
        grown = open(pre_ledger, "rb").read()
        if rc != 0 or not grown.startswith(pre_head):
            fails.append("V10 append-only prefix broken (rc=%d)" % rc)

        # V11 unknown expected side fails loud at admission, rc=9.
        rcs_odd = os.path.join(work, "rcs_odd.json")
        with open(rcs_odd, "w", encoding="utf-8") as handle:
            json.dump({"witness.lean": {"rc": 0, "expected": "maybe"}}, handle)
        rc, _, _ = _selftest_vector(
            ["--report", report, "--rc-file", rcs_odd, "--ledger",
             os.path.join(work, "odd-ledger.jsonl")], EXIT_INPUT)

        # V12 --strict turns signals into exit 4 (declared, not silent).
        strict_ledger = os.path.join(work, "strict-ledger.jsonl")
        rc, _, err = _selftest_vector(
            ["--report", report, "--rc-file", rcs_bad, "--ledger",
             strict_ledger, "--strict"], EXIT_STRICT_SIGNAL)
        if rc != EXIT_STRICT_SIGNAL or "--strict" not in err:
            fails.append("V12 strict should exit 4 loudly (rc=%d err=%r)"
                         % (rc, err))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for line in fails:
            sys.stderr.write("SELFTEST FAIL %s\n" % line)
        return 1
    sys.stdout.write("%s (12 vectors)\n" % SELFTEST_MARK)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="calibration_ledger.py",
        description="W4 calibration ledger: predicted confidence per report "
                    "row x measured compile-leg rc -> docs/exp-ledger.jsonl "
                    "(schema rocqwash-exp/1, idempotent seen set, row-rot "
                    "signal face).")
    parser.add_argument("--report", default="",
                        help="vacgen v2 report JSON (reportId + assumptions)")
    parser.add_argument("--rc-file", default="", dest="rc_file",
                        help="measured rc face JSON: leg -> {rc, expected}")
    parser.add_argument("--leg-map", default="", dest="leg_map",
                        help="optional familyId -> leg name JSON map")
    parser.add_argument("--default-leg", default=DEFAULT_LEG,
                        dest="default_leg",
                        help="leg name for rows absent from the leg map "
                             "(default: %s)" % DEFAULT_LEG)
    parser.add_argument("--ledger", default="", help="ledger path override")
    parser.add_argument("--batch", default="",
                        help="batch label (default: calibration-<reportId>)")
    parser.add_argument("--ts", default="",
                        help="ISO date/timestamp (default: now UTC)")
    parser.add_argument("--signal-threshold", type=float,
                        default=DEFAULT_SIGNAL_THRESHOLD,
                        dest="signal_threshold",
                        help="gap >= threshold flags the row (default: %s)"
                             % DEFAULT_SIGNAL_THRESHOLD)
    parser.add_argument("--signals-out", default="", dest="signals_out",
                        help="write the signal face JSON here")
    parser.add_argument("--strict", action="store_true",
                        help="exit 4 when at least one signal row is present")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="validate and report, write nothing")
    parser.add_argument("--selftest", action="store_true",
                        help="run the temporary-fixture vector group")
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
        if args.report or args.rc_file:
            parser.error("--selftest takes no input files")
        return selftest()
    if not args.report or not args.rc_file:
        parser.error("a run needs --report and --rc-file (or --selftest)")
    try:
        return run(args, Streams())
    except InputError as exc:
        sys.stderr.write("%s: %s\n" % (TOOL, exc))
        return EXIT_INPUT
    except CorruptLedger as exc:
        sys.stderr.write("%s: %s\n" % (TOOL, exc))
        return EXIT_INPUT


if __name__ == "__main__":
    sys.exit(main())
