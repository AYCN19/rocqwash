#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_events.py — cw_sentinel JSONL event-stream renderer (markdown ledger + JSON summary).

    Purpose.  Render event streams in the `rocqwash-sentinel-event/1` schema (emitted
      by `cw_sentinel.py`) into a deterministic markdown ledger plus a
      `rocqwash-render-events/1` JSON summary; pure consumer face, zero network, the
      stream rendered as it stands.  A failing result is data, not a tool failure.

    Interface.  Exactly one input mode: `--events FILE.jsonl` (single file; line order
      is stream order) or `--dir DIR` (all `*.jsonl` merged in filename order, then
      sorted by (seq, ts, source order, line order)).  `--md out.md` and
      `--json out.json` select outputs; `--top N` truncates the markdown family
      table (default 0 = all rows); `--selftest` runs the canned vector set.  Bad
      lines (non-JSON or non-object) are skipped, counted, warned per line;
      rendering continues; unknown kinds count as `other`, missing family/action
      as `(none)`.

    Dependencies.  Python 3 standard library only (`argparse`, `io`, `json`, `os`,
      `sys`); zero third-party dependencies; zero network.

    Evidence.  `--selftest` covers seven canned vectors on temporary fixtures:
      three-dimensional counts, md-table rows with pipe escaping and evidence
      truncation, empty-file and all-bad-line verdicts, cross-file seq+ts ordering
      under `--dir`, `--top` truncation, byte-identical reruns, CLI exit codes.

    Exit-codes.  0 = rendered with zero bad lines (`verdict` ok or empty); 1 = rendered
      but bad_lines > 0, outputs still written (the `baseline_diff.py:50` degraded
      discipline); 2 = usage error (both or neither of `--events`/`--dir`, negative
      `--top`, argparse error); 9 = input or output unreachable (missing stream file
      or directory, no `*.jsonl` in it, unwritable target)."""
import argparse
import io
import json
import os
import sys

PROG = "render_events"
SCHEMA = "rocqwash-render-events/1"
EVENT_SCHEMA = "rocqwash-sentinel-event/1"
# full kind spectrum of the three `cw_sentinel.py` signal sources
# (`cw_sentinel.py:17/22/28`) - kinds outside the spectrum count as `other`
KNOWN_KINDS = ("ci-red", "blocking", "build-signal")
OTHER_KEY = "other"
NONE_KEY = "(none)"
EVIDENCE_MAX = 2


def fail(code, msg):
    """Fail loud and exit at once (2 = usage error, 9 = input or output
    unreachable); the message goes to stderr."""
    print("FAIL-LOUD: %s" % msg, file=sys.stderr)
    sys.exit(code)


def md_cell(value):
    """Sanitize one markdown table cell: escape pipes, flatten CR/LF to
    spaces (keeps the table intact, deterministic)."""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def seq_key(ev):
    """Primary sort key: int seq used directly (bool excluded), decimal
    strings accepted, missing or malformed values sort first (-1)."""
    s = ev.get("seq")
    if isinstance(s, bool):
        return -1
    if isinstance(s, int):
        return s
    if isinstance(s, str) and s.lstrip("-").isdigit():
        return int(s)
    return -1


def ts_of(ev):
    """Event timestamp; only a non-empty string counts (a clock-less stream
    carries no ts)."""
    t = ev.get("ts")
    return t if isinstance(t, str) and t else ""


def kind_of(ev):
    """kind used for counting: verbatim when inside the spectrum, `other`
    otherwise."""
    k = ev.get("kind")
    return k if k in KNOWN_KINDS else OTHER_KEY


def verbatim(ev, key):
    """Verbatim cell value for the per-event row (str as-is; int/float
    stringified; bool or missing as the empty string)."""
    v = ev.get(key)
    if isinstance(v, str):
        return v
    if isinstance(v, bool) or v is None:
        return ""
    if isinstance(v, (int, float)):
        return str(v)
    return ""


def load_events(path):
    """One JSONL file -> (events, bad_lines).  Bad lines are skipped and
    counted, loudly, without stopping."""
    try:
        fh = io.open(path, "r", encoding="utf-8", errors="replace")
    except OSError as e:
        fail(9, "event stream unreadable: %s (%s)" % (path, e))
    events, bad = [], 0
    with fh:
        for lineno, line in enumerate(fh, 1):
            s = line.strip()
            if not s:
                continue  # blank line: skipped (neither a bad line nor an event)
            try:
                obj = json.loads(s)
            except ValueError:
                bad += 1
                print("WARN: %s:%d non-JSON bad line (skipped, counted in "
                      "bad_lines)" % (path, lineno), file=sys.stderr)
                continue
            if not isinstance(obj, dict):
                bad += 1
                print("WARN: %s:%d JSON value is not an object - bad line "
                      "(skipped, counted in bad_lines)"
                      % (path, lineno), file=sys.stderr)
                continue
            events.append(obj)
    return events, bad


def read_inputs(args):
    """Read either input form -> (events, bad_lines, sources, input_desc).

    `--events` reads one file in line order; `--dir` merges all `*.jsonl`
    files and re-sorts by (seq, ts, source order, line order).  A missing
    input face fails with 9 (a directory present but carrying no `*.jsonl`
    is also 9 - a missing input face is an instrument state, while an empty
    stream is the `empty` verdict).
    """
    events, bad, sources = [], 0, []
    if args.events:
        if not os.path.isfile(args.events):
            fail(9, "event stream file missing: %s" % args.events)
        sources = [args.events]
        events, bad = load_events(args.events)
        desc = "--events %s (single file; line order = stream order)" % args.events
        return events, bad, sources, desc
    if not os.path.isdir(args.dir):
        fail(9, "event stream directory missing: %s" % args.dir)
    names = sorted(n for n in os.listdir(args.dir) if n.endswith(".jsonl"))
    paths = [os.path.join(args.dir, n) for n in names
             if os.path.isfile(os.path.join(args.dir, n))]
    if not paths:
        fail(9, "no *.jsonl file in directory: %s" % args.dir)
    sources = paths
    tagged = []
    for src_idx, path in enumerate(paths):
        evs, b = load_events(path)
        bad += b
        for line_idx, ev in enumerate(evs):
            tagged.append((ev, src_idx, line_idx))
    tagged.sort(key=lambda t: (seq_key(t[0]), ts_of(t[0]), t[1], t[2]))
    events = [ev for ev, _, _ in tagged]
    desc = "--dir %s (%d files merged; seq+ts order)" % (args.dir, len(paths))
    return events, bad, sources, desc


def tally(events):
    """Three-dimensional counts (unknown kind -> `other`; missing or empty
    family/action -> `(none)`).  The three tables always sum to events_total:
    count additivity is the mechanical self-consistency check."""
    counts = {"kind": {}, "family": {}, "action": {}}
    for ev in events:
        k = kind_of(ev)
        counts["kind"][k] = counts["kind"].get(k, 0) + 1
        for dim in ("family", "action"):
            v = ev.get(dim)
            if v is None or (isinstance(v, str) and not v):
                v = NONE_KEY
            elif not isinstance(v, str):
                v = str(v)
            counts[dim][v] = counts[dim].get(v, 0) + 1
    return counts


def span_of(events):
    """span = min/max over all non-empty ts values (lexicographic order =
    ISO 8601 UTC order); both null when the stream carries no ts."""
    ts = sorted(t for t in (ts_of(ev) for ev in events) if t)
    return {"first_ts": ts[0] if ts else None,
            "last_ts": ts[-1] if ts else None}


def render_md(events, counts, span, verdict, bad_lines, input_desc, top):
    """The ledger markdown (deterministic: counts n-descending with ties in
    key order, per-event rows in stream order, zero clock, zero randomness)."""
    lines = ["# cw_sentinel event ledger (%s)" % SCHEMA, ""]
    lines.append("- input: %s" % input_desc)
    lines.append("- events_total=%d bad_lines=%d" % (len(events), bad_lines))
    lines.append("")
    lines.append("## Count distribution (kind / family / action; n descending, "
                 "ties in key order)")
    for dim in ("kind", "family", "action"):
        rows = sorted(counts[dim].items(), key=lambda kv: (-kv[1], kv[0]))
        head = "### %s" % dim
        if dim == "family" and top > 0 and len(rows) > top:
            head += " (--top %d truncated; %d more families not shown)" \
                    % (top, len(rows) - top)
        lines.append("")
        lines.append(head)
        lines.append("| %s | n |" % dim)
        lines.append("|---|---|")
        for key, n in (rows[:top] if (dim == "family" and top > 0) else rows):
            lines.append("| %s | %d |" % (md_cell(key), n))
    lines.append("")
    lines.append("## Per-event (seq/kind/family/action/repo/run/branch/sha8/"
                 "evidence first 2)")
    lines.append("| seq | kind | family | action | repo | run | branch | sha8 "
                 "| evidence(first 2) |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for ev in events:
        sha = ev.get("sha")
        sha8 = sha[:8] if isinstance(sha, str) else ""
        evidence = ev.get("evidence")
        if isinstance(evidence, list):
            ev_txt = "; ".join(md_cell(x) for x in evidence[:EVIDENCE_MAX])
        else:
            ev_txt = ""
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            md_cell(verbatim(ev, "seq")), md_cell(verbatim(ev, "kind")),
            md_cell(verbatim(ev, "family")), md_cell(verbatim(ev, "action")),
            md_cell(verbatim(ev, "repo")), md_cell(verbatim(ev, "run")),
            md_cell(verbatim(ev, "branch")), md_cell(sha8), ev_txt))
    lines.append("")
    lines.append("---")
    span_txt = ("%s..%s" % (span["first_ts"], span["last_ts"])
                if span["first_ts"] else "no ts (clock-less stream)")
    lines.append("- verdict=%s (events_total=%d bad_lines=%d span=%s)"
                 % (verdict, len(events), bad_lines, span_txt))
    lines.append("")
    return "\n".join(lines)


def write_text(path, text):
    """Write the markdown output (unwritable -> 9, fail loud)."""
    try:
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError as e:
        fail(9, "markdown output not writable: %s (%s)" % (path, e))


def write_json(path, obj):
    """Write the JSON summary (indent 2, sort_keys, ensure_ascii=False,
    trailing newline)."""
    try:
        with io.open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
    except OSError as e:
        fail(9, "json output not writable: %s (%s)" % (path, e))


def selftest():
    """Embedded canned vector set (temporary fixtures only; zero repository
    writes, zero network): three-dimensional counts, md-table rows with
    escaping and truncation, bad-line tolerance with exit 1, empty file with
    exit 0, all-bad-lines with exit 1, cross-file seq+ts ordering under
    `--dir`, `--top` truncation, byte-identical reruns, CLI exit codes."""
    import re
    import shutil
    import subprocess
    import tempfile

    def run(args):
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(
                                os.path.abspath(__file__)),
                                PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def dump_jsonl(path, lines):
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write("".join(x + "\n" if not x.endswith("\n") else x
                             for x in lines))

    def ev(seq, ts, kind, family, action, run_id, evidence=None):
        e = {"schema": EVENT_SCHEMA, "seq": seq, "ts": ts, "kind": kind,
             "family": family, "action": action, "repo": "org/repo",
             "run": run_id, "branch": "br%d" % seq,
             "sha": "%08x" % seq + "1" * 32,
             "evidence": (["ev%d-a" % seq, "ev%d-b" % seq, "ev%d-c" % seq]
                          if evidence is None else evidence)}
        return json.dumps(e, sort_keys=True, ensure_ascii=False)

    tmp = tempfile.mkdtemp(prefix="rocqwash_render_events_self_")
    try:
        # vector 1: mixed stream - three known kinds + one unknown kind + one
        # non-JSON bad line + evidence containing a pipe
        mixed = os.path.join(tmp, "mixed.jsonl")
        dump_jsonl(mixed, [
            ev(1, "2026-11-10T00:00:01Z", "ci-red", "A-content-red",
               "fix-content", 111, ["fail-item 1/2 ids=[1]",
                                    "families on record: A"]),
            "<<<not JSON>>>",  # bad line, sandwiched in the middle
            ev(2, "2026-11-10T00:00:02Z", "ci-red", "B-netred",
               "rerun-after-stable-window", 222),
            ev(3, "2026-11-10T00:00:03Z", "blocking", "X-root",
               "wash-root", 333, []),
            ev(4, "2026-11-10T00:00:04Z", "build-signal", "Y-sig",
               "watch-only", 444, ["a|b", "c", "d"]),
            ev(5, "2026-11-10T00:00:05Z", "future-kind", "Z-unk",
               "probe-it", 555),
        ])
        jf = os.path.join(tmp, "mixed.json")
        mf = os.path.join(tmp, "mixed.md")
        p = run(["--events", mixed, "--json", jf, "--md", mf])
        assert p.returncode == 1, "bad lines must yield exit 1 (degraded " \
            "data, outputs still written); got %d\n%s" \
            % (p.returncode, p.stdout)
        g = json.load(io.open(jf, encoding="utf-8"))
        assert g["schema"] == SCHEMA and g["verdict"] == "ok", g
        assert g["events_total"] == 5 and g["bad_lines"] == 1, g
        assert g["counts"]["kind"] == {"blocking": 1, "build-signal": 1,
                                       "ci-red": 2, "other": 1}, g["counts"]
        assert g["counts"]["family"] == {"A-content-red": 1, "B-netred": 1,
                                         "X-root": 1, "Y-sig": 1,
                                         "Z-unk": 1}, g["counts"]
        assert g["counts"]["action"] == {"fix-content": 1,
                                         "probe-it": 1,
                                         "rerun-after-stable-window": 1,
                                         "wash-root": 1,
                                         "watch-only": 1}, g["counts"]
        assert g["span"] == {"first_ts": "2026-11-10T00:00:01Z",
                             "last_ts": "2026-11-10T00:00:05Z"}, g["span"]
        assert sum(g["counts"]["kind"].values()) == 5, \
            "dimension sums must equal events_total"
        md = io.open(mf, encoding="utf-8").read()
        # md-table rows: the full column set of seq 1 (sha8; first 2 evidence
        # entries joined by "; "; the third entry must not appear)
        assert "| 1 | ci-red | A-content-red | fix-content | org/repo | 111 " \
               "| br1 | 00000001 | fail-item 1/2 ids=[1]; families on " \
               "record: A |" in md, md
        assert "| 3 | blocking | X-root | wash-root | org/repo | 333 | br3 | " \
               "00000003 |  |" in md, "row with empty evidence did not render"
        assert "a\\|b; c |" in md, "pipe not escaped"
        assert "; c; d" not in md, \
            "evidence not truncated to the first 2 entries (the third entry " \
            "must not appear)"
        assert "future-kind" in md, \
            "kind column must reflect the stream value verbatim"
        assert "RENDER-EVENTS: verdict=ok events_total=5 bad_lines=1" \
            in p.stdout, p.stdout
        print("vector 1 three-dimensional counts + md-table rows + "
              "escaping/truncation + bad lines exit 1: PASS")

        # vector 2: empty file - verdict empty, exit 0, reported faithfully
        empty = os.path.join(tmp, "empty.jsonl")
        dump_jsonl(empty, [])
        je = os.path.join(tmp, "empty.json")
        me = os.path.join(tmp, "empty.md")
        p = run(["--events", empty, "--json", je, "--md", me])
        assert p.returncode == 0, "empty file must exit 0; got %d\n%s" \
            % (p.returncode, p.stdout)
        g = json.load(io.open(je, encoding="utf-8"))
        assert g["verdict"] == "empty" and g["events_total"] == 0, g
        assert g["span"] == {"first_ts": None, "last_ts": None}, g["span"]
        assert "verdict=empty" in io.open(me, encoding="utf-8").read(), me
        print("vector 2 empty file verdict=empty exit 0: PASS")

        # vector 3: all bad lines - verdict empty and exit 1 (emptiness is a
        # stream state, dirt is degraded data; both facts reported)
        garbage = os.path.join(tmp, "garbage.jsonl")
        dump_jsonl(garbage, ["garbage one", "garbage two"])
        p = run(["--events", garbage, "--json", os.path.join(tmp, "g.json")])
        assert p.returncode == 1, "all-bad-lines must exit 1; got %d" \
            % p.returncode
        g = json.load(io.open(os.path.join(tmp, "g.json"), encoding="utf-8"))
        assert g["verdict"] == "empty" and g["bad_lines"] == 2 \
            and g["events_total"] == 0, g
        print("vector 3 all-bad-lines empty exit 1, both facts reported: PASS")

        # vector 4: --dir out-of-order merge - seq 1,2 live in b, 3,4,5 in a;
        # cross-file placement by seq
        d = os.path.join(tmp, "streams")
        os.makedirs(d)
        dump_jsonl(os.path.join(d, "a_late.jsonl"), [
            ev(3, "2026-11-10T00:00:03Z", "blocking", "X-root",
               "wash-root", 333, []),
            ev(4, "2026-11-10T00:00:04Z", "build-signal", "Y-sig",
               "watch-only", 444, ["a|b", "c", "d"]),
            ev(5, "2026-11-10T00:00:05Z", "future-kind", "Z-unk",
               "probe-it", 555),
        ])
        dump_jsonl(os.path.join(d, "b_early.jsonl"), [
            ev(1, "2026-11-10T00:00:01Z", "ci-red", "A-content-red",
               "fix-content", 111, ["fail-item 1/2 ids=[1]",
                                    "families on record: A"]),
            "<<<bad>>>",
            ev(2, "2026-11-10T00:00:02Z", "ci-red", "B-netred",
               "rerun-after-stable-window", 222),
        ])
        jd = os.path.join(tmp, "dir.json")
        mdir = os.path.join(tmp, "dir.md")
        p = run(["--dir", d, "--json", jd, "--md", mdir])
        assert p.returncode == 1, p.stdout
        md = io.open(mdir, encoding="utf-8").read()
        # extract the per-event rows in seq order (^\| N \| - escaped pipes
        # inside evidence do not disturb column parsing)
        sec = md.split("## Per-event", 1)[1]
        seqs = re.findall(r"^\| (\d+) \|", sec, re.M)
        assert seqs == ["1", "2", "3", "4", "5"], \
            "cross-file seq+ts ordering broken: %s" % seqs
        g = json.load(io.open(jd, encoding="utf-8"))
        assert g["events_total"] == 5 and g["bad_lines"] == 1, g
        assert g["sources"] == [os.path.join(d, "a_late.jsonl"),
                                os.path.join(d, "b_early.jsonl")], g["sources"]
        print("vector 4 --dir cross-file seq+ts ordering: PASS")

        # vector 5: --top truncation - two family rows plus a remainder note;
        # the json counts stay complete
        mt = os.path.join(tmp, "top.md")
        jt = os.path.join(tmp, "top.json")
        p = run(["--dir", d, "--json", jt, "--md", mt, "--top", "2"])
        assert p.returncode == 1, p.stdout
        md = io.open(mt, encoding="utf-8").read()
        assert "### family (--top 2 truncated; 3 more families not shown)" \
            in md, md
        assert "| A-content-red | 1 |" in md and "| B-netred | 1 |" in md, md
        assert "| X-root | 1 |" not in md, \
            "truncation broken (the third family must not be shown)"
        g = json.load(io.open(jt, encoding="utf-8"))
        assert len(g["counts"]["family"]) == 5, "json counts must stay complete"
        print("vector 5 --top truncation (md truncated, json complete): PASS")

        # vector 6: byte-identical reruns on the same input (json and md alike)
        p = run(["--dir", d, "--json", jd, "--md", mdir])
        assert p.returncode == 1, p.stdout
        b1 = (io.open(jd, "rb").read(), io.open(mdir, "rb").read())
        p = run(["--dir", d, "--json", jd, "--md", mdir])
        b2 = (io.open(jd, "rb").read(), io.open(mdir, "rb").read())
        assert b1 == b2, "byte drift between two runs is a violation"
        print("vector 6 byte-identical reruns: PASS")

        # vector 7: CLI exit codes - 0 = help / clean stream, 1 = bad lines
        # (vectors 1 and 3), 2 = usage, 9 = missing input
        clean = os.path.join(tmp, "clean.jsonl")
        dump_jsonl(clean, [ev(1, "2026-11-10T00:00:01Z", "ci-red",
                              "A-content-red", "fix-content", 111)])
        p = run(["--events", clean, "--json", os.path.join(tmp, "c.json")])
        assert p.returncode == 0, "clean stream must exit 0; got %d" \
            % p.returncode
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag must exit 2; got %d" \
            % p.returncode
        p = run([])
        assert p.returncode == 2, "both flags missing must exit 2; got %d" \
            % p.returncode
        p = run(["--events", mixed, "--dir", d])
        assert p.returncode == 2, "both flags given must exit 2; got %d" \
            % p.returncode
        p = run(["--events", clean, "--top", "-1"])
        assert p.returncode == 2, "negative --top must exit 2; got %d" \
            % p.returncode
        p = run(["--events", os.path.join(tmp, "nope.jsonl")])
        assert p.returncode == 9, "missing event stream must exit 9; got %d" \
            % p.returncode
        p = run(["--dir", os.path.join(tmp, "nope_dir")])
        assert p.returncode == 9, "missing directory must exit 9; got %d" \
            % p.returncode
        empty_d = os.path.join(tmp, "no_jsonl_dir")
        os.makedirs(empty_d)
        p = run(["--dir", empty_d])
        assert p.returncode == 9, "directory without jsonl must exit 9; " \
            "got %d" % p.returncode
        print("vector 7 CLI exit codes (0/1/2/9; help 0, clean stream 0, bad "
              "lines 1, both-missing/both-given/negative-top 2, missing 9)"
              ": PASS")

        print("RENDER-EVENTS-SELFTEST PASS: all seven vectors pass (three-"
              "dimensional counts / md-table rows with escaping and truncation"
              " / bad-line tolerance exit 1 / empty file exit 0 / all-bad-lines"
              " exit 1 / --dir seq+ts ordering / --top truncation / byte-"
              "identical reruns / CLI exit codes)")
        return 0
    except AssertionError as e:
        print("RENDER-EVENTS-SELFTEST FAIL: %s" % (e,), file=sys.stderr)
        return 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="cw_sentinel JSONL event stream -> markdown ledger + "
                    "rocqwash-render-events/1 summary (pure rendering; zero "
                    "network, nothing re-created)")
    ap.add_argument("--events", default=None, metavar="FILE.jsonl",
                    help="single event stream JSONL (rocqwash-sentinel-event/"
                         "1; line order is stream order)")
    ap.add_argument("--dir", default=None, metavar="DIR",
                    help="merge all *.jsonl in DIR (filename order; sorted by "
                         "seq+ts to restore the global order)")
    ap.add_argument("--md", default=None, metavar="out.md",
                    help="markdown ledger output")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="JSON summary output (rocqwash-render-events/1)")
    ap.add_argument("--top", type=int, default=0, metavar="N",
                    help="row cap for the family distribution table "
                         "(0 = all rows, the default)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # usage guard (exit 2)
    if args.events and args.dir:
        fail(2, "--events and --dir are mutually exclusive (giving both is a "
                "usage ambiguity; fail loud, never pick one silently)")
    if not args.events and not args.dir:
        fail(2, "one of --events and --dir is required (neither given means "
                "no input face)")
    if args.top < 0:
        fail(2, "--top must be >= 0 (0 = all rows, the default); got %d"
                % args.top)

    # read inputs (missing input face -> 9; bad lines warn loudly, no stop)
    events, bad_lines, sources, input_desc = read_inputs(args)

    counts = tally(events)
    span = span_of(events)
    verdict = "ok" if events else "empty"
    summary = {"schema": SCHEMA,
               "events_total": len(events),
               "bad_lines": bad_lines,
               "verdict": verdict,
               "counts": counts,
               "span": span,
               "sources": sources}
    if args.json:
        write_json(args.json, summary)
    if args.md:
        write_text(args.md, render_md(events, counts, span, verdict,
                                      bad_lines, input_desc, args.top))

    span_txt = ("%s..%s" % (span["first_ts"], span["last_ts"])
                if span["first_ts"] else "no-ts")
    print("RENDER-EVENTS: verdict=%s events_total=%d bad_lines=%d span=%s "
          "sources=%d md=%s json=%s"
          % (verdict, len(events), bad_lines, span_txt, len(sources),
             args.md or "-", args.json or "-"))
    # 0 = zero bad lines (ok and empty alike report 0) - 1 = bad_lines > 0
    # (degraded data; the outputs were still written)
    sys.exit(1 if bad_lines else 0)


if __name__ == "__main__":
    main()
