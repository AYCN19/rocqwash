#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pin_repair.py - re-sign drifted provenance md5 pins in the jargon seed.

Purpose.  R15 auto-repair executor.  A jargon-seed provenance pin
  drifts when a pinned source is edited without re-signing its snapshot
  md5 in the same commit.  Flow: gate IN-SYNC verdict, re-sign drifted
  md5 values from current source bytes, verify, roll back
  byte-identically on red.  Unreadable sources block; gates escalate.

Interface.  python3 tools/pin_repair.py --selftest | --plan | --apply
  [--seed P] (default seeds/jargon/jargon-map.json).  One JSON result
  line on stdout, narrative on stderr; --plan writes nothing, --apply
  touches only md5 values in provenance.sources.

Dependencies.  Standard library only; zero network face.  Subprocesses
  run tools/jargon_map_sync.py (plan gate, cwd = repository root, the
  seed under test forwarded on --map; the default seed forwards its own
  default path, so the repository-wide judgment is unchanged) and
  tests/t_engines_seeds.py (post-apply verification).  The selftest
  rides the same gate form on fixture seeds (temp directories only).

Evidence.  --selftest vectors: standing-entry copies, pins matched
  (none); drift (plan reports pinned vs current; apply re-signs only
  the md5 value, other bytes survive); absent source (listed, apply
  refused); synthetic single entry, gate PENDING (exit 3, zero write);
  red verify (exit 4, rollback); usage (2).

Exit-codes.  0 green / plan / none / apply verified; 1 red named
  (unreadable seed, apply refused, rewrite refused, selftest red);
  2 usage; 3 gate not IN-SYNC; 4 red verification, seed rolled back.
"""

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SCHEMA = "rocqwash-pin-repair/1"
TOOL = "pin_repair"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SEED_PATH = os.path.join(REPO_ROOT, "seeds", "jargon",
                                 "jargon-map.json")
SYNC_TOOL_PATH = os.path.join(REPO_ROOT, "tools", "jargon_map_sync.py")
SEED_SUITE_PATH = os.path.join(REPO_ROOT, "tests", "t_engines_seeds.py")

# the gate passes only when the sync tool's zero-write plan reports this
# verdict prefix (tools/jargon_map_sync.py, plan mode tail line)
SYNC_VERDICT_OK = "VERDICT IN-SYNC"

GATE_TIMEOUT_S = 120
SUITE_TIMEOUT_S = 300

SEGMENT_RE = re.compile(r"^SEGMENT jargon: (\d+) checks, (\d+) FAIL")


def fail(msg, code):
    sys.stderr.write(TOOL + ": " + msg + "\n")
    raise SystemExit(code)


def _vec(results, name, ok, detail):
    results.append((name, bool(ok), detail))


def resolve_path(path):
    """Repository-relative paths resolve against the repository root."""
    if os.path.isabs(path):
        return path
    return os.path.join(REPO_ROOT, path)


def file_md5(path):
    """Current md5 of a file's bytes; None when the file cannot be read."""
    try:
        with io.open(path, "rb") as fh:
            return hashlib.md5(fh.read()).hexdigest()
    except OSError:
        return None


def load_seed(seed_path):
    """Read the seed JSON; return (raw bytes, dict, provenance sources).

    Fails loud on an unreadable file, invalid JSON, or a provenance block
    without a usable sources list; a repair executor never guesses."""
    try:
        with io.open(seed_path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        fail("seed unreadable: " + seed_path + " (" + str(exc) + ")", 1)
    try:
        doc = json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        fail("seed is not valid UTF-8 JSON: " + seed_path
             + " (" + str(exc) + ")", 1)
    prov = doc.get("provenance") if isinstance(doc, dict) else None
    sources = prov.get("sources") if isinstance(prov, dict) else None
    if not isinstance(sources, list) or not sources:
        fail("seed carries no provenance.sources list: " + seed_path, 1)
    for src in sources:
        if not isinstance(src, dict) \
                or not isinstance(src.get("path"), str) \
                or not isinstance(src.get("md5"), str):
            fail("provenance source without path/md5 strings in "
                 + seed_path, 1)
    return raw, doc, sources


def survey_sources(sources):
    """Classify each pinned source: matched / drifted / absent."""
    rows = []
    for src in sources:
        current = file_md5(resolve_path(src["path"]))
        if current is None:
            state = "absent"
        elif current == src["md5"]:
            state = "matched"
        else:
            state = "drifted"
        rows.append({"path": src["path"], "pinned_md5": src["md5"],
                     "current_md5": current, "state": state})
    return rows


def run_gate(gate_cmd):
    """Run the sync tool's zero-write plan; return (verdict line, detail).

    verdict is the last VERDICT line of stdout, or None when the gate could
    not be established (launch failure, timeout, no verdict line); detail
    then carries the failure text for the escalation report."""
    try:
        proc = subprocess.run(gate_cmd, cwd=REPO_ROOT, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=GATE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, "sync plan timed out after %ds" % GATE_TIMEOUT_S
    except OSError as exc:
        return None, "sync plan failed to launch: " + str(exc)
    verdict = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("VERDICT "):
            verdict = line.strip()
    if verdict is None:
        tail = ((proc.stderr or "") + " " + (proc.stdout or "")).strip()
        tail = " ".join(tail.split())[:200]
        return None, tail or "no VERDICT line in the sync plan output"
    return verdict, verdict


def default_gate_cmd(seed_path):
    """The contract gate: the sync tool's zero-write plan with the seed
    under test forwarded on --map.  Forwarding is what lets a --seed
    input own the verdict; with the default seed the forwarded path is
    the sync tool's own default, so the repository-wide judgment stays
    the bare call's."""
    return [sys.executable, "-I", SYNC_TOOL_PATH, "--map", seed_path]


def run_seed_suite():
    """Run the seed test suite; return (rc, output, failure detail)."""
    try:
        proc = subprocess.run([sys.executable, "-I", SEED_SUITE_PATH],
                              cwd=REPO_ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=SUITE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, "", "seed suite timed out after %ds" % SUITE_TIMEOUT_S
    except OSError as exc:
        return None, "", "seed suite failed to launch: " + str(exc)
    return proc.returncode, proc.stdout or "", ""


def suite_jargon_green(rc, output):
    """Green means: a jargon segment line with zero FAIL and suite exit 0."""
    segment = None
    for line in output.splitlines():
        found = SEGMENT_RE.match(line.strip())
        if found:
            segment = found
    if segment is None:
        return False, "no 'SEGMENT jargon:' line in the seed suite output"
    if int(segment.group(2)) != 0:
        return False, ("jargon segment reports %s FAIL"
                       % segment.group(2))
    if rc != 0:
        return False, ("seed suite exit code %s while the jargon segment"
                       " reports 0 FAIL" % rc)
    return True, ("jargon segment: %s checks, 0 FAIL; suite exit 0"
                  % segment.group(1))


def real_verify():
    """Default post-apply verification: run the seed suite, judge it."""
    rc, output, detail = run_seed_suite()
    if detail:
        return False, detail
    return suite_jargon_green(rc, output)


def dumps_seed(doc):
    """The seed serialization: the file's own key order, indent 2, trailing
    newline.  Verified byte-stable against the seed file before any write."""
    return (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8")


def flow(mode, seed_path, gate_cmd, verify=None):
    """Shared front for --plan and --apply; returns (report, exit code)."""
    if verify is None:
        verify = real_verify
    raw, doc, sources = load_seed(seed_path)
    verdict, gate_detail = run_gate(gate_cmd)
    sys.stderr.write("%s: seed=%s sources=%d\n"
                     % (TOOL, seed_path, len(sources)))
    sys.stderr.write("%s: gate %s\n" % (TOOL, gate_detail))
    if verdict is None or not verdict.startswith(SYNC_VERDICT_OK):
        shown = verdict if verdict else gate_detail
        return {"ok": False, "stage": "plan", "verdict": shown,
                "seed": seed_path}, 3
    rows = survey_sources(sources)
    drifted = [r for r in rows if r["state"] == "drifted"]
    absent = [r for r in rows if r["state"] == "absent"]
    sys.stderr.write("%s: matched=%d drifted=%d absent=%d\n"
                     % (TOOL, len(rows) - len(drifted) - len(absent),
                        len(drifted), len(absent)))
    if not drifted and not absent:
        return {"ok": True, "action": "none", "drifted": [],
                "seed": seed_path, "verdict": verdict}, 0
    if mode == "plan":
        return {"ok": True, "action": "plan",
                "drifted": [{"path": r["path"], "pinned_md5": r["pinned_md5"],
                             "current_md5": r["current_md5"]}
                            for r in drifted],
                "absent": [{"path": r["path"], "pinned_md5": r["pinned_md5"],
                            "current_md5": None} for r in absent],
                "seed": seed_path, "verdict": verdict}, 0
    # --apply: an absent source cannot be re-signed from bytes nobody can
    # read; refuse the whole apply instead of guessing the missing value
    if absent:
        return {"ok": False, "stage": "apply",
                "reason": ("absent pinned sources block the rewrite; a pin"
                           " is only re-signed from bytes this tool has"
                           " actually read"),
                "absent": [{"path": r["path"], "pinned_md5": r["pinned_md5"],
                            "current_md5": None} for r in absent],
                "seed": seed_path}, 1
    if dumps_seed(doc) != raw:
        return {"ok": False, "stage": "apply",
                "reason": ("seed is not byte-stable under the key-order"
                           " indent-2 rewrite; refusing a write that could"
                           " touch more than the md5 values"),
                "seed": seed_path}, 1
    resigned = []
    for idx, row in enumerate(rows):
        if row["state"] == "drifted":
            doc["provenance"]["sources"][idx]["md5"] = row["current_md5"]
            resigned.append({"path": row["path"],
                             "pinned_md5": row["pinned_md5"],
                             "resigned_md5": row["current_md5"]})
    new_bytes = dumps_seed(doc)
    with io.open(seed_path, "wb") as fh:
        fh.write(new_bytes)
    sys.stderr.write("%s: re-signed %d pin(s); verifying\n"
                     % (TOOL, len(resigned)))
    ok, verify_detail = verify()
    if ok:
        return {"ok": True, "action": "apply", "resigned": resigned,
                "verify": "seeds-suite-green", "seed": seed_path,
                "verdict": verdict}, 0
    with io.open(seed_path, "wb") as fh:
        fh.write(raw)
    restored = True
    try:
        with io.open(seed_path, "rb") as fh:
            restored = fh.read() == raw
    except OSError:
        restored = False
    sys.stderr.write("%s: verification red (%s); seed rollback %s\n"
                     % (TOOL, verify_detail,
                        "byte-identical" if restored else "FAILED"))
    return {"ok": False, "stage": "verify", "action": "apply-rolled-back",
            "verify": verify_detail, "resigned": resigned,
            "rollback": "byte-identical" if restored else "FAILED",
            "seed": seed_path, "verdict": verdict}, 4


def emit(report):
    print(json.dumps(report, ensure_ascii=False))


# --- selftest (offline, temporary fixtures; reads the standing seed
# entries, writes nothing outside the temp directory) ---

# synthetic single entry: no admitted face of the repository md table
# lives in this map, so the gate reports PENDING for it - the fixture
# shape of the exit-3 vector
FX_ENTRY = {
    "id": "J001", "face": "alpha", "standard": "one",
    "standard_language": "en",
    "standard_source": ("rocqwash docs/jargon-to-standard-mapping-v1.md"
                        " (in-repo-md-v1)"),
    "source_line": 1, "disposition": "replace", "exempts": [],
    "cross_track_note": None, "note": "clean note.",
}

FX_SEED_DOC = {
    "schema": "rocqwash-jargon-map/1",
    "engine": "jargon",
    "count": 0,
    "note": "fixture seed for the pin repair selftest",
    "provenance": {
        "transcription": "fixture map for the pin repair selftest",
        "sources": [],
    },
    "entries": [],
}


def fixture_entries():
    """Deep copies of the standing seed's entry list, read-only.

    The gate judges a seed's entries against the repository's own md
    table, and the standing seed is in sync with that table, so a
    fixture seed carrying these entries verbatim is IN-SYNC by
    construction, while a synthetic single entry is PENDING (every
    admitted md face is missing from it)."""
    _raw, doc, _sources = load_seed(DEFAULT_SEED_PATH)
    return json.loads(json.dumps(doc["entries"]))


def run_selftest(args):
    results = []
    tmp = tempfile.mkdtemp(prefix="rqw_pin_repair_")
    try:
        src_a = os.path.join(tmp, "src_a.txt")
        src_b = os.path.join(tmp, "src_b.txt")
        seed_path = os.path.join(tmp, "seed.json")

        def write_bytes(path, data):
            with io.open(path, "wb") as fh:
                fh.write(data)

        def md5_of(path):
            return file_md5(path)

        def make_seed(entries, md5_a, md5_b):
            doc = json.loads(json.dumps(FX_SEED_DOC))
            doc["count"] = len(entries)
            doc["entries"] = json.loads(json.dumps(entries))
            doc["provenance"]["sources"] = [
                {"path": src_a, "role": "fixture source one",
                 "md5": md5_a},
                {"path": src_b, "role": "fixture source two",
                 "md5": md5_b},
            ]
            write_bytes(seed_path, dumps_seed(doc))

        def gate_cmd():
            # the production gate form: the real sync tool, zero-write
            # plan, the seed under test forwarded on --map
            return default_gate_cmd(seed_path)

        def green_verify():
            return True, "stub verification pass (fixture)"

        def red_verify():
            return False, "stub verification failure (fixture)"

        entries = fixture_entries()

        write_bytes(src_a, b"alpha source bytes v1\n")
        write_bytes(src_b, b"beta source bytes v1\n")

        # vector 1: standing-entry copies (gate IN-SYNC by construction),
        # every pin matches -> action none
        make_seed(entries, md5_of(src_a), md5_of(src_b))
        rep, code = flow("plan", seed_path, gate_cmd())
        rep2, code2 = flow("apply", seed_path, gate_cmd(),
                           verify=green_verify)
        ok = (code == 0 and rep.get("action") == "none"
              and rep.get("drifted") == []
              and code2 == 0 and rep2.get("action") == "none")
        _vec(results, "insync-matching-pins-none", ok,
             "IN-SYNC gate over standing-entry copies plus matching pins"
             " reports action none in both modes"
             if ok else "plan=%r apply=%r" % (rep, rep2))

        # vector 2: drifted pin, plan face reports pinned vs current
        write_bytes(src_a, b"alpha source bytes v2\n")
        current_a = md5_of(src_a)
        rep, code = flow("plan", seed_path, gate_cmd())
        drift = rep.get("drifted") or []
        ok = (code == 0 and rep.get("action") == "plan" and len(drift) == 1
              and drift[0]["path"] == src_a
              and drift[0]["current_md5"] == current_a
              and drift[0]["pinned_md5"] != current_a
              and rep.get("absent") == [])
        _vec(results, "drift-plan-reports-pinned-vs-current", ok,
             "plan lists the drifted source with its pinned and current md5"
             if ok else "rc=%d report=%r" % (code, rep))

        # vector 3: apply re-signs only the md5 value, every other byte
        # of the seed file survives
        raw_before = io.open(seed_path, "rb").read()
        rep, code = flow("apply", seed_path, gate_cmd(),
                         verify=green_verify)
        raw_after = io.open(seed_path, "rb").read()
        pinned_old = drift[0]["pinned_md5"].encode("utf-8")
        expected = (raw_before.replace(pinned_old, current_a.encode("utf-8"))
                    if raw_before.count(pinned_old) == 1 else None)
        doc_after = json.loads(raw_after.decode("utf-8"))
        ok = (code == 0 and rep.get("action") == "apply"
              and rep.get("verify") == "seeds-suite-green"
              and expected is not None and raw_after == expected
              and doc_after["provenance"]["sources"][0]["md5"] == current_a
              and doc_after["provenance"]["sources"][1]["md5"]
              == md5_of(src_b))
        _vec(results, "drift-apply-resigns-value-only", ok,
             "apply rewrote exactly the drifted md5 value; all other bytes"
             " survived; verification green"
             if ok else "rc=%d report=%r" % (code, rep))

        # vector 4: absent source is listed; apply refuses without writing
        os.remove(src_b)
        raw_before = io.open(seed_path, "rb").read()
        rep, code = flow("plan", seed_path, gate_cmd())
        absent = rep.get("absent") or []
        ok_plan = (code == 0 and rep.get("action") == "plan"
                   and len(absent) == 1 and absent[0]["path"] == src_b
                   and absent[0]["current_md5"] is None)
        rep, code = flow("apply", seed_path, gate_cmd(),
                         verify=green_verify)
        raw_after = io.open(seed_path, "rb").read()
        ok = (ok_plan and code == 1 and rep.get("ok") is False
              and rep.get("stage") == "apply" and raw_after == raw_before)
        _vec(results, "absent-source-listed-apply-refused", ok,
             "absent source listed with a null current md5; apply refused"
             " exit 1 and the seed stayed byte-identical"
             if ok else "plan=%r apply=%r" % (rep, absent))

        # vector 5: a synthetic single entry is PENDING at the gate (no
        # admitted md face lives in it) -> exit 3, zero write
        make_seed([FX_ENTRY], md5_of(src_a),
                  "not-a-real-md5-value-but-32-chars-ok00")
        write_bytes(src_b, b"beta source bytes v1\n")
        raw_before = io.open(seed_path, "rb").read()
        rep, code = flow("plan", seed_path, gate_cmd())
        raw_after = io.open(seed_path, "rb").read()
        ok = (code == 3 and rep.get("ok") is False
              and rep.get("stage") == "plan"
              and (rep.get("verdict") or "").startswith("VERDICT PENDING")
              and raw_after == raw_before)
        _vec(results, "synthetic-entry-pending-exit-3", ok,
             "PENDING gate verdict over the synthetic single entry"
             " escalates exit 3 with the raw verdict line and the seed"
             " untouched"
             if ok else "rc=%d report=%r" % (code, rep))

        # vector 6: red post-apply verification rolls the seed back
        make_seed(entries, md5_of(src_a), md5_of(src_b))
        write_bytes(src_a, b"alpha source bytes v3\n")
        raw_before = io.open(seed_path, "rb").read()
        rep, code = flow("apply", seed_path, gate_cmd(),
                         verify=red_verify)
        raw_after = io.open(seed_path, "rb").read()
        ok = (code == 4 and rep.get("action") == "apply-rolled-back"
              and rep.get("rollback") == "byte-identical"
              and raw_after == raw_before)
        _vec(results, "verify-red-rolls-back-byte-identical", ok,
             "a red verification restored the seed bytes exactly, exit 4"
             if ok else "rc=%d report=%r" % (code, rep))

        # vector 7: CLI usage conflicts exit 2 before any file is read
        proc = subprocess.run(
            [sys.executable, "-I", os.path.abspath(__file__),
             "--plan", "--apply", "--seed", seed_path],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60)
        ok = proc.returncode == 2
        _vec(results, "usage-conflict-exit-2", ok,
             "combining --plan with --apply is a usage error, exit 2"
             if ok else "rc=%d out=%r" % (proc.returncode,
                                          proc.stderr[:120]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = 0
    for name, ok, detail in results:
        if ok:
            tag = "PASS"
        else:
            tag = "FAIL"
            failed += 1
        print("%s %s - %s" % (tag, name, detail))
    print("summary: %d vectors, %d FAIL" % (len(results), failed))
    if failed:
        print("PIN-REPAIR-SELFTEST RED (%d)" % failed)
        return 1
    print("PIN-REPAIR-SELFTEST PASS")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog=TOOL)
    ap.add_argument("--selftest", action="store_true",
                    help="run the selftest vectors; standalone")
    ap.add_argument("--plan", action="store_true",
                    help="report drifted pins; writes nothing")
    ap.add_argument("--apply", action="store_true",
                    help="re-sign drifted pins, then verify and roll back"
                         " on a red verification")
    ap.add_argument("--seed", metavar="P", default=DEFAULT_SEED_PATH,
                    help="seed map JSON (default: seeds/jargon/jargon-map"
                         ".json)")
    args = ap.parse_args(argv)
    modes = [flag for flag in (args.selftest, args.plan, args.apply) if flag]
    if len(modes) != 1:
        fail("pick exactly one of --selftest / --plan / --apply", 2)
    if args.selftest:
        return run_selftest(args)
    mode = "apply" if args.apply else "plan"
    seed = resolve_path(args.seed)
    report, code = flow(mode, seed, default_gate_cmd(seed))
    emit(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
