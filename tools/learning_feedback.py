#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""learning_feedback.py - scheduling feedback face over the three standing ledgers.
Purpose.  Read the round ledger (docs/round-ledger.jsonl, schema
  rocqwash-round/1), the round state (docs/round-state.json, schema
  rocqwash.round-state/1), and the experience ledger (docs/exp-ledger.jsonl,
  schema rocqwash-exp/1) strictly read-only, and cast the scheduling
  feedback face (schema rocqwash.scheduling-feedback/1) into
  docs/scheduling-feedback.json: the round admission face (total / auto /
  human_approved / approval_rate_auto / per-class breakdown) and the repair
  outcome face (repaired / escalated / watch_only_guard_correct /
  unrecorded / repair_action_rate).  The approval rate becomes a readable
  number here; scheduling does not yet consume it (the feedback_edge face
  declares that boundary).  Missing or corrupt inputs are recorded per
  account in the "errors" list and named on stdout, never guessed: the run
  continues on the remaining valid rows and exits 1 so the red name is loud.
Interface.  `python -I tools/learning_feedback.py [--selftest]`; the default
  zero-argument run resolves the three inputs and the output against the
  repository root (the parent of tools/) and writes exactly one file,
  docs/scheduling-feedback.json (the three inputs are never written).
Dependencies.  Python 3 stdlib only (argparse/json/os/shutil/sys/tempfile);
  zero network by design; zero eval/exec; deterministic: the runtime clock
  never enters the logic, and reruns over identical inputs are
  byte-identical.
Evidence.  --selftest on temporary fixtures, four vectors: two rounds one
  auto one human-approved; corrupt-line tolerance plus an absent round-state
  file; empty ledgers; every repair row outside the four-state vocabulary.
  Each vector asserts the computed face and never touches repository paths.
Exit-codes.  0 = face produced, every account error-free; 1 = at least one
  account error (missing input, invalid JSON, non-round row) or the output
  write failed, each named on stdout; 2 = usage error (argparse face).
"""

# Field notes (the reading rules this tool implements; consumers of the
# scheduling-feedback JSON rely on these exact definitions):
# - rounds.total counts valid round-ledger rows.  auto counts rounds with at
#   least one admission whose decision is "admitted" (the auto gear).
#   human_approved counts rounds with no admitted admission whose applied
#   classes carry a human approval in the round state (the basis names a
#   human approval).  A round with neither stays in total only (a rollback
#   or salvage shape is data, not an error).
# - approval_rate_auto = auto / total; the denominator includes
#   human-approved rounds; None when total is 0; rounded to 4 decimals.
# - by_class: one entry per class seen in classes_applied, sorted by name.
#   gear is "auto" when the class entered through an admitted admission,
#   "human" when it entered through a human-approved round-state entry, and
#   "mixed" (plus an error line) when both paths occur.  confidence comes
#   from the admission for auto and from the round-state entry for human;
#   null stays null, never guessed.
# - repair_outcomes classify each valid experience-ledger row by the action
#   vocabulary inside its points text: "action=fix-content" -> repaired;
#   "action=escalated" or "action=escalate" -> escalated;
#   "action=watch-only" -> watch_only_guard_correct.  Any other row
#   (including "action=rerun-after-stable-window" and rows without an
#   action token) stays unrecorded.  The vocabulary mirrors the outcome
#   words the repair ledger already uses; a row outside it is never forced
#   into a state (honest unrecorded, no filling).
# - repair_action_rate = repaired / total valid rows; None when total is 0.
# - errors: per-account strings in deterministic order; an empty list is a
#   clean account.

import argparse
import json
import os
import shutil
import sys
import tempfile

PROG = "learning_feedback"
SCHEMA = "rocqwash.scheduling-feedback/1"
TOOL_VERSION = "1.0.0"
ROUNDS_DEFAULT = ("docs", "round-ledger.jsonl")
STATE_DEFAULT = ("docs", "round-state.json")
EXP_DEFAULT = ("docs", "exp-ledger.jsonl")
OUT_DEFAULT = ("docs", "scheduling-feedback.json")
NOTE = ("approval-rate now readable; scheduling does not yet consume it"
        " (declared blank)")

# The action-token table, in priority order (first match wins).
REPAIR_TOKENS = (
    ("action=fix-content", "repaired"),
    ("action=escalated", "escalated"),
    ("action=escalate", "escalated"),
    ("action=watch-only", "watch_only_guard_correct"),
)


def _repo_root():
    """The repository root: the parent of the tools/ directory holding this file."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read_jsonl(path, label):
    """Read a JSONL ledger -> (rows as (lineno, obj) pairs, errors)."""
    errors = []
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return [], ["%s not found or unreadable: %s (%s)" % (label, path, exc)]
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append("%s line %d: invalid JSON (%s)" % (label, lineno, exc))
            continue
        if not isinstance(obj, dict):
            errors.append("%s line %d: not a JSON object" % (label, lineno))
            continue
        rows.append((lineno, obj))
    return rows, errors


def _read_json(path, label):
    """Read one JSON document -> (obj or None, errors)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), []
    except OSError as exc:
        return None, ["%s not found or unreadable: %s (%s)" % (label, path, exc)]
    except json.JSONDecodeError as exc:
        return None, ["%s invalid JSON: %s (%s)" % (label, path, exc)]


def _basis_is_human(basis):
    """A round-state basis counts as a human approval when it names one."""
    if not isinstance(basis, str):
        return False
    low = basis.lower()
    return "human" in low and "approv" in low


def compute_rounds(rounds_path, state_path):
    """Cast the rounds face from the round ledger plus the round state."""
    errors = []
    rows, read_errors = _read_jsonl(rounds_path, "round-ledger")
    errors.extend(read_errors)

    state = None
    state_rows, state_errors = _read_json(state_path, "round-state")
    errors.extend(state_errors)
    state_map = {}
    if state_rows is not None:
        state = state_rows
    if isinstance(state, dict):
        for entry in state.get("admitted_classes") or []:
            if not isinstance(entry, dict) or not entry.get("class"):
                errors.append("round-state: admitted_classes entry without a"
                              " class skipped")
                continue
            state_map[entry["class"]] = entry
    elif state is not None:
        errors.append("round-state: not a JSON object")

    total = 0
    auto = 0
    human = 0
    classes = {}
    for lineno, row in rows:
        round_id = row.get("round_id")
        if round_id is None or "mode" not in row:
            errors.append("round-ledger line %d: not a round row (missing"
                          " round_id or mode)" % lineno)
            continue
        total += 1
        admissions = row.get("admissions") or []
        admitted = {}
        for adm in admissions:
            if not isinstance(adm, dict):
                errors.append("round-ledger line %d: admission is not an"
                              " object, skipped" % lineno)
                continue
            cls = adm.get("class")
            if not cls:
                errors.append("round-ledger line %d: admission without a"
                              " class, skipped" % lineno)
                continue
            if adm.get("decision") == "admitted":
                admitted[cls] = adm
        applied = row.get("classes_applied") or []
        auto_classes = set(admitted)
        human_classes = set()
        for cls in applied:
            if cls in auto_classes:
                continue
            entry = state_map.get(cls)
            if entry is not None and _basis_is_human(entry.get("basis")):
                human_classes.add(cls)
            else:
                errors.append("round-ledger line %d: class %s has neither an"
                              " admitted admission nor a human-approved"
                              " round-state entry; excluded from by_class"
                              % (lineno, cls))
        if auto_classes:
            auto += 1
        elif human_classes:
            human += 1
        for cls in sorted(auto_classes):
            conf = admitted[cls].get("confidence")
            stats = classes.setdefault(cls, {"rounds": 0, "gears": set(),
                                             "confidence": None})
            stats["rounds"] += 1
            stats["gears"].add("auto")
            if conf is not None:
                stats["confidence"] = conf
        for cls in sorted(human_classes):
            entry = state_map.get(cls)
            conf = entry.get("confidence") if entry else None
            stats = classes.setdefault(cls, {"rounds": 0, "gears": set(),
                                             "confidence": None})
            stats["rounds"] += 1
            stats["gears"].add("human")
            if conf is not None:
                stats["confidence"] = conf
    by_class = []
    for cls in sorted(classes):
        stats = classes[cls]
        gears = stats["gears"]
        if len(gears) == 1:
            gear = sorted(gears)[0]
        else:
            gear = "mixed"
            errors.append("by_class: class %s entered through both gears;"
                          " gear reported as mixed" % cls)
        by_class.append({"class": cls, "rounds": stats["rounds"],
                         "gear": gear, "confidence": stats["confidence"]})
    rate = round(auto / total, 4) if total else None
    return {"total": total, "auto": auto, "human_approved": human,
            "approval_rate_auto": rate, "by_class": by_class,
            "errors": errors}


def compute_repair(exp_path):
    """Cast the repair outcome face from the experience ledger."""
    errors = []
    rows, read_errors = _read_jsonl(exp_path, "exp-ledger")
    errors.extend(read_errors)
    counts = {"repaired": 0, "escalated": 0, "watch_only_guard_correct": 0,
              "unrecorded": 0}
    total = 0
    for _lineno, row in rows:
        total += 1
        points = row.get("points")
        text = points if isinstance(points, str) else ""
        state = "unrecorded"
        for token, name in REPAIR_TOKENS:
            if token in text:
                state = name
                break
        counts[state] += 1
    rate = round(counts["repaired"] / total, 4) if total else None
    face = dict(counts)
    face["repair_action_rate"] = rate
    face["errors"] = errors
    return face


def build_face(rounds_path, state_path, exp_path):
    """Cast the full scheduling feedback face from the three input paths."""
    rounds = compute_rounds(rounds_path, state_path)
    repair = compute_repair(exp_path)
    return {"schema": SCHEMA,
            "rounds": rounds,
            "repair_outcomes": repair,
            "feedback_edge": {"status": "open", "note": NOTE}}


def summarize(face, out_display):
    """One stdout summary block over a computed face."""
    rounds = face["rounds"]
    repair = face["repair_outcomes"]
    lines = ["scheduling-feedback: schema %s" % SCHEMA,
             "rounds: total=%d auto=%d human_approved=%d approval_rate_auto=%s"
             % (rounds["total"], rounds["auto"], rounds["human_approved"],
                rounds["approval_rate_auto"]),
             "repair: repaired=%d escalated=%d watch_only_guard_correct=%d"
             " unrecorded=%d repair_action_rate=%s"
             % (repair["repaired"], repair["escalated"],
                repair["watch_only_guard_correct"], repair["unrecorded"],
                repair["repair_action_rate"]),
             "feedback_edge: %s" % face["feedback_edge"]["status"]]
    for msg in rounds["errors"]:
        lines.append("ERROR %s" % msg)
    for msg in repair["errors"]:
        lines.append("ERROR %s" % msg)
    error_count = len(rounds["errors"]) + len(repair["errors"])
    lines.append("errors: %d" % error_count)
    lines.append("wrote: %s" % out_display)
    return "\n".join(lines)


def run(rounds_path, state_path, exp_path, out_path):
    """Default run: build the face, write the JSON, print the summary -> exit code."""
    face = build_face(rounds_path, state_path, exp_path)
    try:
        text = json.dumps(face, indent=2, sort_keys=True, ensure_ascii=False)
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
    except OSError as exc:
        sys.stdout.write("ERROR output write failed: %s (%s)\n" % (out_path, exc))
        return 1
    sys.stdout.write(summarize(face, out_path) + "\n")
    clean = not face["rounds"]["errors"] and not face["repair_outcomes"]["errors"]
    return 0 if clean else 1


def _write_fixture(path, lines):
    """Write one fixture file (JSONL or JSON document) into the temp root."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def _check(failures, vector, name, cond, detail):
    """Record one failed assertion for a selftest vector."""
    if not cond:
        failures.append("vector %d %s: %s" % (vector, name, detail))


def selftest():
    """Four offline vectors on temporary fixtures; never touches repository paths."""
    root = tempfile.mkdtemp(prefix="learning_feedback_selftest_")
    failures = []
    try:
        # Vector 1: two rounds, one auto one human-approved; the repair face
        # covers all four states once.
        v1 = os.path.join(root, "v1")
        os.mkdir(v1)
        rounds1 = os.path.join(v1, "round-ledger.jsonl")
        _write_fixture(rounds1, [
            json.dumps({"round_id": 1, "mode": "auto", "verify_rc": 0,
                        "classes_applied": ["alpha"],
                        "admissions": [{"class": "alpha",
                                        "decision": "admitted",
                                        "confidence": 1.0,
                                        "basis": "gear auto: confidence 1.00"
                                                 " >= threshold 0.80"}]},
                       sort_keys=True),
            json.dumps({"round_id": 2, "mode": "auto", "verify_rc": 0,
                        "classes_applied": ["beta"], "admissions": []},
                       sort_keys=True),
        ])
        state1 = os.path.join(v1, "round-state.json")
        _write_fixture(state1, [json.dumps({
            "schema": "rocqwash.round-state/1",
            "admitted_classes": [
                {"class": "alpha", "confidence": 1.0,
                 "basis": "gear auto: confidence 1.00 >= threshold 0.80"},
                {"class": "beta", "confidence": None,
                 "basis": "human point-order approved (unconditional)"},
            ]}, sort_keys=True)])
        exp1 = os.path.join(v1, "exp-ledger.jsonl")
        _write_fixture(exp1, [
            json.dumps({"id": "EXP-1-0001", "points": "run 1: family=A"
                        " action=fix-content (auto triage)"}, sort_keys=True),
            json.dumps({"id": "EXP-1-0002", "points": "run 2: family=B"
                        " action=escalated"}, sort_keys=True),
            json.dumps({"id": "EXP-1-0003", "points": "run 3: family=U"
                        " action=watch-only"}, sort_keys=True),
            json.dumps({"id": "EXP-1-0004", "points": "run 4: plain note"},
                       sort_keys=True),
        ])
        face1 = build_face(rounds1, state1, exp1)
        expect1 = {
            "schema": SCHEMA,
            "rounds": {"total": 2, "auto": 1, "human_approved": 1,
                       "approval_rate_auto": 0.5,
                       "by_class": [
                           {"class": "alpha", "rounds": 1, "gear": "auto",
                            "confidence": 1.0},
                           {"class": "beta", "rounds": 1, "gear": "human",
                            "confidence": None}],
                       "errors": []},
            "repair_outcomes": {"repaired": 1, "escalated": 1,
                                "watch_only_guard_correct": 1,
                                "unrecorded": 1, "repair_action_rate": 0.25,
                                "errors": []},
            "feedback_edge": {"status": "open", "note": NOTE},
        }
        _check(failures, 1, "face", face1 == expect1,
               "face %r != expected %r" % (face1, expect1))

        # Vector 2: corrupt-line tolerance plus an absent round-state file;
        # the run continues on the valid rows and records every error.
        v2 = os.path.join(root, "v2")
        os.mkdir(v2)
        rounds2 = os.path.join(v2, "round-ledger.jsonl")
        _write_fixture(rounds2, [
            json.dumps({"round_id": 7, "mode": "auto", "verify_rc": 0,
                        "classes_applied": ["gamma"],
                        "admissions": [{"class": "gamma",
                                        "decision": "admitted",
                                        "confidence": 0.9}]}, sort_keys=True),
            "this line is not json {{{",
        ])
        state2 = os.path.join(v2, "round-state.json")  # deliberately absent
        exp2 = os.path.join(v2, "exp-ledger.jsonl")
        _write_fixture(exp2, [
            json.dumps({"id": "EXP-2-0001", "points": "action=fix-content"},
                       sort_keys=True),
            "not a row ]]]",
        ])
        face2 = build_face(rounds2, state2, exp2)
        _check(failures, 2, "round totals", face2["rounds"]["total"] == 1
               and face2["rounds"]["auto"] == 1
               and face2["rounds"]["approval_rate_auto"] == 1.0,
               "rounds face %r" % face2["rounds"])
        _check(failures, 2, "round errors", len(face2["rounds"]["errors"]) == 2
               and any("round-ledger line 2" in m
                       for m in face2["rounds"]["errors"])
               and any("round-state" in m for m in face2["rounds"]["errors"]),
               "rounds errors %r" % face2["rounds"]["errors"])
        _check(failures, 2, "repair", face2["repair_outcomes"]["repaired"] == 1
               and face2["repair_outcomes"]["repair_action_rate"] == 1.0
               and len(face2["repair_outcomes"]["errors"]) == 1,
               "repair face %r" % face2["repair_outcomes"])

        # Vector 3: empty ledgers; zero denominators give null rates, not crashes.
        v3 = os.path.join(root, "v3")
        os.mkdir(v3)
        rounds3 = os.path.join(v3, "round-ledger.jsonl")
        state3 = os.path.join(v3, "round-state.json")
        exp3 = os.path.join(v3, "exp-ledger.jsonl")
        for path in (rounds3, exp3):
            _write_fixture(path, [])
        _write_fixture(state3, [json.dumps({"schema": "rocqwash.round-state/1",
                                            "admitted_classes": []},
                                           sort_keys=True)])
        face3 = build_face(rounds3, state3, exp3)
        expect3 = {
            "schema": SCHEMA,
            "rounds": {"total": 0, "auto": 0, "human_approved": 0,
                       "approval_rate_auto": None, "by_class": [],
                       "errors": []},
            "repair_outcomes": {"repaired": 0, "escalated": 0,
                                "watch_only_guard_correct": 0,
                                "unrecorded": 0, "repair_action_rate": None,
                                "errors": []},
            "feedback_edge": {"status": "open", "note": NOTE},
        }
        _check(failures, 3, "face", face3 == expect3,
               "face %r != expected %r" % (face3, expect3))

        # Vector 4: every repair row outside the four-state vocabulary stays
        # unrecorded; no row is forced into a state.
        v4 = os.path.join(root, "v4")
        os.mkdir(v4)
        rounds4 = os.path.join(v4, "round-ledger.jsonl")
        _write_fixture(rounds4, [
            json.dumps({"round_id": 9, "mode": "auto", "verify_rc": 0,
                        "classes_applied": ["delta"],
                        "admissions": [{"class": "delta",
                                        "decision": "admitted",
                                        "confidence": 0.9}]}, sort_keys=True),
        ])
        state4 = os.path.join(v4, "round-state.json")
        _write_fixture(state4, [json.dumps({"schema": "rocqwash.round-state/1",
                                            "admitted_classes": []},
                                           sort_keys=True)])
        exp4 = os.path.join(v4, "exp-ledger.jsonl")
        _write_fixture(exp4, [
            json.dumps({"id": "EXP-4-0001", "points": "run A: family=E"
                        " action=rerun-after-stable-window"}, sort_keys=True),
            json.dumps({"id": "EXP-4-0002", "points": "no action vocabulary"
                        " in this row"}, sort_keys=True),
            json.dumps({"id": "EXP-4-0003", "points": "action=unknown-thing"},
                       sort_keys=True),
        ])
        face4 = build_face(rounds4, state4, exp4)
        expect4_repair = {"repaired": 0, "escalated": 0,
                          "watch_only_guard_correct": 0, "unrecorded": 3,
                          "repair_action_rate": 0.0, "errors": []}
        _check(failures, 4, "repair", face4["repair_outcomes"] == expect4_repair,
               "repair face %r != expected %r"
               % (face4["repair_outcomes"], expect4_repair))
        _check(failures, 4, "rounds", face4["rounds"]["total"] == 1
               and face4["rounds"]["auto"] == 1
               and not face4["rounds"]["errors"],
               "rounds face %r" % face4["rounds"])
    finally:
        shutil.rmtree(root, ignore_errors=True)
    for line in failures:
        sys.stdout.write("FAIL %s\n" % line)
    if failures:
        red_vectors = len(set(line.split()[1] for line in failures))
        sys.stdout.write("selftest: %d of 4 vectors red (%d assertions)\n"
                         % (red_vectors, len(failures)))
        return 1
    sys.stdout.write("selftest: 4/4 vectors green (temp fixtures only,"
                     " zero repository paths)\n")
    return 0


def main(argv=None):
    """CLI entry: --selftest or the default zero-argument run."""
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=("scheduling feedback face over the three standing"
                     " ledgers (schema %s; reads docs/round-ledger.jsonl,"
                     " docs/round-state.json, docs/exp-ledger.jsonl"
                     " read-only; writes docs/scheduling-feedback.json)"
                     % SCHEMA))
    parser.add_argument("--selftest", action="store_true",
                        help="run the four selftest vectors on temporary"
                             " fixtures (zero repository paths)")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    root = _repo_root()
    return run(os.path.join(root, *ROUNDS_DEFAULT),
               os.path.join(root, *STATE_DEFAULT),
               os.path.join(root, *EXP_DEFAULT),
               os.path.join(root, *OUT_DEFAULT))


if __name__ == "__main__":
    sys.exit(main())
