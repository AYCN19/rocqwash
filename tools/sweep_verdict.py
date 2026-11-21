#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sweep_verdict.py - mechanical verdict face over per-lane sweep ledgers
(rocqwash tools/, v2-B micro-bundle; the judge of batch audits).

Purpose.  Union every per-lane result .tsv in the --lanes directory into
  one judgment table with dedup on (idx, probe), then emit the GREEN /
  EXCEPTION / MISSING verdict table with listings.  Per-lane split ledgers
  are the canonical semantics - the shared append ledger was the root cause
  of the first audit sweep, so that anti-shape is refused at the front
  door (a file path where a directory is required is a usage error, not an
  input).  The --expected-red file interlocks with the baselinediff
  semantics: a by-design-fail row (rc != 0 expected) matched against the
  expected list does NOT count as EXCEPTION (baselined red is not failing,
  no false alarm); an unmatched by-design-fail row is a live alarm.
Interface.  python -I tools/sweep_verdict.py --lanes <dir>
  [--expected-red <file>] [--out <json>] | --selftest.  One JSON report
  line (schema rocqwash-sweep-verdict/1); every counter wrapped
  {value, basis}; top-level scan_face.  Lane ledger columns: idx | probe |
  status | note (an optional header line names the columns, any order).
Dependencies.  Python 3 standard library only; zero network, zero compile,
  deterministic (no wall clock on the report face).
Evidence.  --selftest drives synthetic lane fixtures reproducing the GREEN
  / EXCEPTION / MISSING shape: cross-lane dedup, a conflict pair (later
  lane wins, listed loud), the expected-red interlock (matched rows stay
  out of EXCEPTION; unmatched ones count), a ghost baseline row recorded
  MISSING, an unexpected token, a malformed row, header order, rc 2/9.
Exit-codes.  0 verdict clean (no exception/missing/conflict/malformed);
  1 failing data (loud, JSON still emitted); 2 usage error (no --lanes, a
  file where the per-lane directory is required, a bad header); 9 missing
  input path (lanes dir absent, no .tsv inside, expected-red file absent).
"""
# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard):
#   * Status vocabulary (case-insensitive tokens): green = ok | green |
#     pass; by-design-fail = expected-red | expected-fail | by-design-fail
#     | red-by-design; anything else (including a bare "red"/"fail") is an
#     unexpected token -> EXCEPTION with the verbatim token quoted.
#   * Conflict resolution caliber: the later lane in sorted-file order wins
#     (the max-lane seed caliber of verdict_diff), and the full kept/dropped
#     pair is listed loud - a lane divergence never passes silently.
#   * MISSING is computable only over the expected-red universe (the only
#     expected-universe input this CLI carries): an expected-red entry with
#     zero matching rows in the union is MISSING.  Without the file the
#     missing count is declared not-computed (value null, basis says so) -
#     never fabricated as zero.
#   * Malformed rows (fewer than three cells, empty idx/probe) are counted
#     loud and listed, never dropped silently; they push the exit code to 1.

import argparse
import json
import os
import sys
import io

PROG = "sweep_verdict"
SCHEMA = "rocqwash-sweep-verdict/1"

GREEN_TOKENS = frozenset(("ok", "green", "pass"))
BY_DESIGN_TOKENS = frozenset(("expected-red", "expected-fail",
                              "by-design-fail", "red-by-design"))

SCAN_SCANNED = (
    "every *.tsv lane ledger inside the --lanes directory (flat,"
    " non-recursive, sorted), plus the --expected-red file when given;"
    " nothing else is read"
)
SCAN_NOT_SCANNED = (
    "the probes' raw outputs, rc logs and artifact directories (the lane"
    " ledgers are the only input and are trusted as written),"
    " subdirectories under the lanes dir, and any .tsv outside it"
)
SCAN_NEGATIVE_FINDING = (
    "a GREEN verdict is a negative finding of this judge over the lane"
    " ledgers' status tokens, not an absolute claim about the probes"
    " themselves"
)
SCAN_EQUIVALENTS = (
    "not exhaustive; the judge reads status tokens only and never re-derives"
    " a probe's rc from artifacts"
)


class FormError(Exception):
    """Unusable input form (rc=2; fail loud, no report emitted)."""


class MissingPath(Exception):
    """Missing input path (rc=9; fail loud, no simulation)."""


def w(value, basis):
    """Wrap one field as {value, basis}: no bare counter leaves the tool."""
    return {"value": value, "basis": basis}


def read_rows(path, what):
    """One ledger file -> (rows, malformed).  rows carry
    (idx, probe, status, note, line_no); malformed carries
    (line_no, text, reason).  Comment (#) and blank lines are skipped; an
    optional first data line naming the columns fixes the column order
    (any order; idx/probe/status required, note optional, unknown extra
    names tolerated positionally)."""
    rows = []
    malformed = []
    colmap = None  # name -> position; None = positional caliber
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for line_no, raw in enumerate(fh, 1):
            line = raw.rstrip("\r\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            cells = [c.strip() for c in line.split("\t")]
            if colmap is None \
                    and set(("idx", "probe", "status")) \
                    <= set(c.lower() for c in cells):
                names = [c.lower() for c in cells]
                colmap = {name: pos for pos, name in enumerate(names)}
                continue
            if colmap is not None:
                row = []
                for name in ("idx", "probe", "status"):
                    pos = colmap.get(name)
                    row.append(cells[pos] if pos is not None
                               and pos < len(cells) else "")
                note = cells[colmap["note"]] if "note" in colmap \
                    and colmap["note"] < len(cells) else ""
                idx, probe, status = row
            else:
                if len(cells) < 3:
                    malformed.append(
                        {"line_no": line_no, "text": line,
                         "reason": "expected idx|probe|status|note (>= 3"
                                   " tab cells), got %d" % len(cells)})
                    continue
                idx, probe, status = cells[0], cells[1], cells[2]
                note = "\t".join(cells[3:])
            if not idx or not probe or not status:
                malformed.append(
                    {"line_no": line_no, "text": line,
                     "reason": "empty idx, probe or status cell"})
                continue
            rows.append({"idx": idx, "probe": probe, "status": status,
                         "note": note, "line_no": line_no})
    return rows, malformed


def read_expected_red(path):
    """The expected-red file -> (entries, malformed, dupes_dropped).
    entries = ordered distinct (idx, probe) pairs; two tab cells minimum,
    further cells ignored; comment/blank lines skipped; an optional header
    naming idx/probe is skipped."""
    entries = []
    seen = set()
    malformed = []
    dupes = 0
    header_seen = False
    if not os.path.isfile(path):
        raise MissingPath("expected-red file missing: %s" % path)
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for line_no, raw in enumerate(fh, 1):
            line = raw.rstrip("\r\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            cells = [c.strip() for c in line.split("\t")]
            if not header_seen and cells[0].lower() == "idx":
                header_seen = True
                continue
            if len(cells) < 2 or not cells[0] or not cells[1]:
                malformed.append(
                    {"line_no": line_no, "text": line,
                     "reason": "expected idx<TAB>probe (>= 2 tab cells),"
                               " got %d" % len(cells)})
                continue
            key = (cells[0], cells[1])
            if key in seen:
                dupes += 1
                continue
            seen.add(key)
            entries.append(key)
    return entries, malformed, dupes


def judge(lanes_dir, expected_red_path):
    """The verdict core -> (report, exit_code).  Union every .tsv lane
    ledger with dedup, judge each row's status token, interlock the
    expected-red list (baselinediff semantics: matched by-design red is
    not failing), and emit the wrapped report."""
    if os.path.isfile(lanes_dir):
        # the anti-shape: a single shared append ledger was the root
        # cause of the first audit sweep - per-lane split ledgers are the
        # canonical input
        raise FormError(
            "--lanes takes a directory of per-lane ledgers, got the file"
            " %s (the shared append ledger is the anti-shape that caused"
            " the first audit sweep's failure and is refused here)"
            % lanes_dir)
    try:
        names = sorted(fn for fn in os.listdir(lanes_dir)
                       if fn.endswith(".tsv")
                       and os.path.isfile(os.path.join(lanes_dir, fn)))
    except OSError as exc:
        raise MissingPath("lanes directory unreadable: %s (%s)"
                          % (lanes_dir, exc))
    if not names:
        raise MissingPath("no lane ledger (.tsv) inside: %s" % lanes_dir)

    union = {}      # (idx, probe) -> row dict (kept)
    raw_rows = 0
    dedup_dropped = 0
    conflicts = []
    malformed_all = []
    for name in names:
        path = os.path.join(lanes_dir, name)
        rows, malformed = read_rows(path, name)
        malformed_all.extend(
            dict(m, lane=name) for m in malformed)
        raw_rows += len(rows)
        for row in rows:
            key = (row["idx"], row["probe"])
            if key not in union:
                row = dict(row, lane=name)
                union[key] = row
                continue
            kept = union[key]
            if (kept["status"], kept["note"]) == (row["status"], row["note"]):
                dedup_dropped += 1
                continue
            # conflict: same key, differing status or note across lanes;
            # max-lane caliber - the later lane in sorted order wins, and
            # the divergence is listed loud (never silent)
            conflicts.append({
                "idx": key[0], "probe": key[1],
                "kept": {"status": row["status"], "note": row["note"],
                         "lane": name},
                "dropped": {"status": kept["status"], "note": kept["note"],
                            "lane": kept["lane"]},
            })
            union[key] = dict(row, lane=name)

    expected = []
    expected_malformed = []
    expected_dupes = 0
    if expected_red_path:
        expected, exp_malformed, expected_dupes = \
            read_expected_red(expected_red_path)
        expected_malformed.extend(
            dict(m, lane=os.path.basename(expected_red_path))
            for m in exp_malformed)
    expected_set = set(expected)

    green = []
    exception = []
    matched = []
    unmatched = []
    for (idx, probe), row in sorted(union.items()):
        token = row["status"].lower()
        if token in GREEN_TOKENS:
            green.append(row)
        elif token in BY_DESIGN_TOKENS:
            if (idx, probe) in expected_set:
                matched.append(row)
                green.append(row)
            else:
                unmatched.append(row)
                exception.append(dict(
                    row, reason="by-design-fail token %r without an"
                                " expected red entry: a baselined red is"
                                " not failing, an unbaselined one is a"
                                " live alarm" % row["status"]))
        else:
            exception.append(dict(
                row, reason="unexpected status token %r (vocabulary:"
                            " ok/green/pass green; expected-red/"
                            "expected-fail/by-design-fail/red-by-design"
                            " by-design-fail)" % row["status"]))
    matched_keys = set((r["idx"], r["probe"]) for r in matched)
    missing = [key for key in expected if key not in union]
    # note: an expected-red entry whose key exists in the union but whose
    # row is NOT by-design-fail is a green-listing row and also counts as
    # a stale baseline entry; it is listed, not counted as exception
    stale = [key for key in expected
             if key in union and key not in matched_keys]

    missing_value = None
    if expected_red_path:
        missing_value = len(missing)

    report = {
        "schema": SCHEMA,
        "lanes_dir": w(lanes_dir,
                       "the --lanes directory as given; every *.tsv inside"
                       " is one lane ledger (per-lane split ledgers are the"
                       " canonical semantics; the shared append ledger was"
                       " the root cause of the first audit sweep and is"
                       " refused at the front door)"),
        "lane_files": w(names,
                        "sorted *.tsv basenames inside the lanes dir; the"
                        " union order is the sort order (max-lane caliber:"
                        " the later lane wins a conflict)"),
        "rows_raw": w(raw_rows,
                      "lane rows parsed before dedup (comment and header"
                      " lines excluded)"),
        "rows_union": w(len(union),
                        "distinct (idx, probe) keys after the cross-lane"
                        " union dedup"),
        "dedup_dropped": w(dedup_dropped,
                           "rows dropped by the dedup: same key with"
                           " identical status and note seen again"),
        "conflicts": w(len(conflicts),
                       "same key with differing status or note across"
                       " lanes; each is listed loud with the kept/dropped"
                       " pair and pushes the exit code to 1"),
        "malformed_rows": w(len(malformed_all),
                            "rows failing the idx|probe|status|note shape"
                            " (both lanes and the expected-red file);"
                            " counted loud, never dropped silently"),
        "expected_red": w(len(expected) if expected_red_path else None,
                          "not parsed: no --expected-red file was given"
                          if not expected_red_path else
                          "distinct (idx, probe) entries parsed from %s"
                          % expected_red_path),
        "expected_red_dupe_drops": w(expected_dupes,
                                     "duplicate expected-red lines dropped"
                                     " (same idx and probe seen again)"),
        "expected_red_malformed": w(len(expected_malformed),
                                    "expected-red lines failing the"
                                    " idx<TAB>probe shape"),
        "verdict_green": w(len(green),
                           "rows whose status token is ok/green/pass, plus"
                           " by-design-fail rows matched against the"
                           " expected-red list (baselinediff interlock: a"
                           " baselined red is not failing)"),
        "verdict_exception": w(len(exception),
                               "unexpected status tokens, plus unmatched"
                               " by-design-fail rows (an unbaselined red is"
                               " a live alarm; no false alarm for the"
                               " matched ones)"),
        "verdict_missing": w(missing_value,
                             "expected-red entries with zero matching rows"
                             " in the union (MISSING is computable only"
                             " over the expected-red universe, the only"
                             " expected-universe input; declared"
                             " not-computed as null without the file)"
                             if expected_red_path else
                             "not computed: no --expected-red file was"
                             " given, so there is no expected universe to"
                             " diff against"),
        "listings": {
            "green": [{"idx": r["idx"], "probe": r["probe"],
                       "status": r["status"], "lane": r["lane"],
                       "note": r["note"]} for r in green],
            "exception": [{"idx": r["idx"], "probe": r["probe"],
                           "status": r["status"], "lane": r["lane"],
                           "note": r["note"], "reason": r["reason"]}
                          for r in exception],
            "missing": [{"idx": k[0], "probe": k[1]} for k in missing],
            "expected_red_matched": [{"idx": r["idx"], "probe": r["probe"],
                                      "status": r["status"],
                                      "lane": r["lane"]} for r in matched],
            "expected_red_unmatched": [{"idx": r["idx"], "probe": r["probe"],
                                        "status": r["status"],
                                        "lane": r["lane"]} for r in unmatched],
            "expected_red_stale": [{"idx": k[0], "probe": k[1]}
                                   for k in stale],
            "conflicts": conflicts,
            "malformed": malformed_all,
        },
        "scan_face": {
            "scanned": SCAN_SCANNED,
            "not_scanned": SCAN_NOT_SCANNED,
            "negative_finding": SCAN_NEGATIVE_FINDING,
            "equivalents": SCAN_EQUIVALENTS,
        },
    }
    red = (len(exception) > 0 or (missing_value or 0) > 0
           or len(conflicts) > 0 or len(malformed_all) > 0
           or len(expected_malformed) > 0)
    return report, (1 if red else 0)


# ---- selftest ----------------------------------------------------------------

def selftest():
    """Synthetic lane-fixture vectors (tempfile driven, offline): the
    GREEN/EXCEPTION/MISSING shape, the expected-red interlock, conflicts,
    malformed rows, header order tolerance, usage/missing paths."""
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="sweep_verdict_self_")
    fails = []

    def check(name, ok, detail=""):
        if ok:
            print("[PASS] %s" % name)
        else:
            fails.append(name)
            print("[FAIL] %s %s" % (name, detail))

    def lane(path, text):
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    try:
        lanes = os.path.join(tmp, "lanes")
        os.mkdir(lanes)
        lane(os.path.join(lanes, "lane-1.tsv"),
             "# lane 1 (first lane)\n"
             "idx\tprobe\tstatus\tnote\n"
             "1\twitness\tok\tclean fill\n"
             "1\trefute_full\texpected-red\trc=1 by design\n"
             "2\twitness\tok\tclean\n"
             "3\twitness\tred\tfirst lane saw red\n")
        lane(os.path.join(lanes, "lane-2.tsv"),
             "idx\tprobe\tstatus\tnote\n"
             "1\twitness\tok\tclean fill\n"
             "1\trefute_full\texpected-red\trc=1 by design\n"
             "2\twitness\tok\tclean\n"
             "3\twitness\tok\tsecond lane saw green\n"
             "4\twitness\texpected-red\tby design\n")
        lane(os.path.join(lanes, "zz-headerless.tsv"),
             "5\twitness\tpass\theaderless positional lane\n")
        exp_file = os.path.join(tmp, "expected-red.tsv")
        lane(exp_file,
             "# expected by-design reds (idx<TAB>probe)\n"
             "idx\tprobe\n"
             "1\trefute_full\n"
             "4\twitness\n"
             "9\tghost_probe\n")

        rep, rc = judge(lanes, exp_file)
        check("interlock rc", rc == 1,
              "expected rc=1 (missing ghost + conflict), got %s" % rc)
        check("union counts",
              rep["rows_raw"]["value"] == 10
              and rep["rows_union"]["value"] == 6
              and rep["dedup_dropped"]["value"] == 3,
              "raw=%s union=%s dedup=%s" % (rep["rows_raw"]["value"],
                                            rep["rows_union"]["value"],
                                            rep["dedup_dropped"]["value"]))
        check("conflict count+pair",
              rep["conflicts"]["value"] == 1
              and rep["listings"]["conflicts"][0]["idx"] == "3"
              and rep["listings"]["conflicts"][0]["kept"]["lane"] == "lane-2.tsv",
              rep["listings"]["conflicts"])
        check("interlock matched-green",
              rep["verdict_green"]["value"] == 6
              and len(rep["listings"]["expected_red_matched"]) == 2,
              "green=%s matched=%s" % (rep["verdict_green"]["value"],
                                       rep["listings"]["expected_red_matched"]))
        check("interlock no-false-alarm",
              rep["verdict_exception"]["value"] == 0
              and rep["listings"]["exception"] == [],
              rep["verdict_exception"])
        check("missing ghost",
              rep["verdict_missing"]["value"] == 1
              and rep["listings"]["missing"] == [{"idx": "9",
                                                  "probe": "ghost_probe"}],
              rep["verdict_missing"])
        shape_bare = [k for k in rep
                      if k not in ("scan_face", "schema", "listings")
                      and not (isinstance(rep[k], dict)
                               and "value" in rep[k]
                               and "basis" in rep[k])]
        check("value-basis-shape", shape_bare == [],
              "bare keys: %s" % shape_bare)
        check("verdict-counters-wrapped",
              all(isinstance(rep[k], dict)
                  and "value" in rep[k] and "basis" in rep[k]
                  for k in ("verdict_green", "verdict_exception",
                            "verdict_missing")),
              "verdict counter shape")
        face = rep["scan_face"]
        check("scan-face-fields",
              sorted(face) == ["equivalents", "negative_finding",
                               "not_scanned", "scanned"], sorted(face))
        check("scan-face-lanes-only",
              "lanes directory" in face["scanned"]
              and "not an absolute claim" in face["negative_finding"]
              and face["equivalents"].startswith("not exhaustive"),
              face)

        # 2. no expected-red file: by-design rows become live alarms
        #    (no baseline = no forgiveness), missing declared not-computed
        rep, rc = judge(lanes, None)
        check("no-baseline alarms",
              rc == 1 and rep["verdict_exception"]["value"] >= 2
              and rep["verdict_missing"]["value"] is None,
              (rc, rep["verdict_exception"]))
        check("no-baseline token quote",
              any("expected-red" in (r.get("reason") or "")
                  for r in rep["listings"]["exception"]),
              rep["listings"]["exception"])

        # 3. unexpected status token recorded in EXCEPTION verbatim
        lanes_bad = os.path.join(tmp, "lanes_bad")
        os.mkdir(lanes_bad)
        lane(os.path.join(lanes_bad, "one.tsv"),
             "1\twitness\texploded\tunexpected token face\n")
        rep, rc = judge(lanes_bad, None)
        check("unexpected-token",
              rc == 1 and rep["verdict_exception"]["value"] == 1
              and "'exploded'" in rep["listings"]["exception"][0]["reason"],
              rep["listings"]["exception"])

        # 4. unmatched by-design red is a live alarm even with the file
        exp_partial = os.path.join(tmp, "exp-partial.tsv")
        lane(exp_partial, "1\twitness\n")
        lanes_two = os.path.join(tmp, "lanes_two")
        os.mkdir(lanes_two)
        lane(os.path.join(lanes_two, "one.tsv"),
             "1\twitness\tok\tclean\n"
             "2\twitness\tby-design-fail\tnot in the baseline\n")
        rep, rc = judge(lanes_two, exp_partial)
        check("unmatched-by-design alarm",
              rc == 1 and rep["verdict_exception"]["value"] == 1
              and rep["verdict_green"]["value"] == 1
              and len(rep["listings"]["expected_red_unmatched"]) == 1,
              (rc, rep["verdict_exception"]))

        # 5. malformed row counted loud, never dropped silently
        lanes_mal = os.path.join(tmp, "lanes_mal")
        os.mkdir(lanes_mal)
        lane(os.path.join(lanes_mal, "one.tsv"),
             "1\twitness\tok\tclean\n"
             "only\ttwo cells here\n")
        rep, rc = judge(lanes_mal, None)
        check("malformed loud",
              rc == 1 and rep["malformed_rows"]["value"] == 1
              and len(rep["listings"]["malformed"]) == 1,
              (rc, rep["malformed_rows"]))

        # 6. header column order tolerance (probe first) + clean rc=0 face
        lanes_ord = os.path.join(tmp, "lanes_ord")
        os.mkdir(lanes_ord)
        lane(os.path.join(lanes_ord, "one.tsv"),
             "probe\tidx\tstatus\tnote\n"
             "witness\t7\tgreen\treordered header parses\n")
        rep, rc = judge(lanes_ord, None)
        check("header-order rc0",
              rc == 0 and rep["verdict_green"]["value"] == 1
              and rep["listings"]["green"][0]["idx"] == "7",
              (rc, rep["listings"]["green"]))

        # 7. green-only lanes with a matched baseline stay rc=0 end to end
        lanes_ok = os.path.join(tmp, "lanes_ok")
        os.mkdir(lanes_ok)
        lane(os.path.join(lanes_ok, "one.tsv"),
             "idx\tprobe\tstatus\tnote\n"
             "10\twitness\tok\tclean\n"
             "10\trefute_point\texpected-fail\trc=1 by design\n")
        exp_ok = os.path.join(tmp, "exp-ok.tsv")
        lane(exp_ok, "10\trefute_point\n")
        rep, rc = judge(lanes_ok, exp_ok)
        check("interlock rc0",
              rc == 0 and rep["verdict_green"]["value"] == 2
              and rep["verdict_exception"]["value"] == 0
              and rep["verdict_missing"]["value"] == 0,
              (rc, rep["verdict_exception"]))

        # 8. stale baseline entry: expected-red row present but green ->
        #    listed as stale, not counted as missing
        exp_stale = os.path.join(tmp, "exp-stale.tsv")
        lane(exp_stale, "10\twitness\n10\trefute_point\n")
        rep, rc = judge(lanes_ok, exp_stale)
        check("stale-baseline listed",
              rep["verdict_missing"]["value"] == 0
              and rep["listings"]["expected_red_stale"] == [{"idx": "10",
                                                             "probe": "witness"}],
              rep["listings"]["expected_red_stale"])

        # 9. the anti-shape: a FILE path where the per-lane dir is
        #    required is a usage error (the shared append ledger was the
        #    root cause of the first audit sweep - refused at the front
        #    door)
        single = os.path.join(lanes, "lane-1.tsv")
        try:
            judge(single, None)
            check("anti-shape refused", False, "no FormError raised")
        except FormError:
            check("anti-shape refused", True)

        # 10. missing paths: absent lanes dir rc 9, empty dir rc 9,
        #     absent expected-red file rc 9
        try:
            judge(os.path.join(tmp, "no_such_dir"), None)
            check("missing-dir rc9", False, "no MissingPath raised")
        except MissingPath:
            check("missing-dir rc9", True)
        empty = os.path.join(tmp, "lanes_empty")
        os.mkdir(empty)
        try:
            judge(empty, None)
            check("empty-dir rc9", False, "no MissingPath raised")
        except MissingPath:
            check("empty-dir rc9", True)
        try:
            judge(lanes_ok, os.path.join(tmp, "no_such_exp.tsv"))
            check("missing-exp rc9", False, "no MissingPath raised")
        except MissingPath:
            check("missing-exp rc9", True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("[SELFTEST] sweep_verdict red: %d vector(s) failed: %s"
              % (len(fails), ", ".join(fails)))
        return 1
    print("[SELFTEST] sweep_verdict green: union dedup+conflict max-lane/"
          "expected-red interlock no-false-alarm/missing ghost/no-baseline"
          " alarms/unexpected token/unmatched by-design alarm/malformed"
          " loud/header-order tolerance/interlock rc0/stale baseline/"
          "anti-shape refused/missing paths - all vectors pass offline")
    return 0


def main(argv=None):
    """CLI entry; returns the process exit code."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="mechanical verdict face: union per-lane sweep ledgers"
                    " with dedup, judge GREEN/EXCEPTION/MISSING, interlock"
                    " the expected-red baseline (no false alarm); one JSON"
                    " report line")
    ap.add_argument("--lanes", default=None, metavar="DIR",
                    help="directory of per-lane result .tsv files (one"
                         " lane per file, idx|probe|status|note; required)")
    ap.add_argument("--expected-red", default=None, metavar="FILE",
                    help="expected by-design-fail rows (idx<TAB>probe"
                         " lines); matched rows stay out of EXCEPTION"
                         " (baselinediff interlock), and their absent"
                         " rows recorded MISSING")
    ap.add_argument("--out", default=None, metavar="JSON",
                    help="write the stdout JSON payload to this path too")
    args = ap.parse_args(argv)

    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not args.lanes:
        print("FAIL-LOUD: --lanes <dir> is required (the judge reads"
              " per-lane ledgers only)", file=sys.stderr)
        return 2
    if os.path.isfile(args.lanes):
        print("FAIL-LOUD: --lanes takes a directory, not a file: %s (the"
              " per-lane split ledgers are the canonical semantics; the"
              " shared append ledger was the root cause of the first"
              " audit sweep and is refused here)" % args.lanes,
              file=sys.stderr)
        return 2

    try:
        report, rc = judge(args.lanes, args.expected_red)
    except FormError as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        return 2
    except MissingPath as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        return 9

    payload = json.dumps(report, ensure_ascii=False)
    print(payload)
    if args.out:
        try:
            with io.open(args.out, "w", encoding="utf-8",
                         newline="\n") as fh:
                fh.write(payload)
                fh.write("\n")
        except OSError as exc:
            print("FAIL-LOUD: --out write failed: %s" % exc,
                  file=sys.stderr)
            return 1
        print("json -> %s" % args.out)
    if rc == 1:
        print("FAIL-LOUD: verdict red as data: green=%s exception=%s"
              " missing=%s conflicts=%s malformed=%s (the JSON line above"
              " carries the listings)"
              % (report["verdict_green"]["value"],
                 report["verdict_exception"]["value"],
                 report["verdict_missing"]["value"],
                 report["conflicts"]["value"],
                 report["malformed_rows"]["value"]),
              file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
