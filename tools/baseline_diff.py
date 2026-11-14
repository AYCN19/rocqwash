#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""baseline_diff.py: compare two unclog blockage baselines into a blockage delta report (rocqwash tools/, pure JSON logic).

Purpose.  Read two `unclog --audit` blockage baselines (schema `rocqwash-unclog/1`, audit form; argv order old
  then new, chronological order owned by the caller) and emit a blockage delta report. Read-only by default: the
  only disk writes are the explicit --json/--md report files. A self-consistency precheck rejects hand-edited or
  mixed-in input fail-loud (rc=2, no report); the candidates_key four-tuple (mode.source, args.src, args.candidates,
  args.chain_ledgers) must match item by item, otherwise verdict=incomparable (lists empty, score_delta null, rc=1;
  cross-set deltas are spurious, never force-fit). Comparable runs report new_blocks / resolved_blocks / persistent
  (wall roots aligned cause by cause; failing files carry a chain-root attribution from the new chain_top dependents,
  null when absent, no guessing) plus score_delta {n_red, wall_count}; the verdict reads only the failing count
  (fewer improved, more degraded, equal stable); timing is excluded (excluded_fields=["timing"], the only
  non-deterministic baseline segment).

Interface.  python3 tools/baseline_diff.py OLD.json NEW.json [--json out.json] [--md out.md], or --selftest. Report
  schema rocqwash-baseline-diff/1; verdict in improved|degraded|stable|incomparable. Deterministic: sort_keys, reruns
  byte-identical, no wall-clock and no absolute paths in the report (basenames only, full paths on stdout); cw.sh
  route baseline-diff.

Dependencies.  Python 3 stdlib only; pure JSON logic, zero network, zero build step; both inputs read-only.

Evidence.  --selftest six vectors on tmp-synthesized baselines (improved / degraded / stable / incomparable / md
  output / CLI exit codes) asserting byte-identical reruns and unwritten inputs; suite tests/test_baseline_diff.py;
  companion procedure examples/baselines/README.md.

Exit-codes.  0 = improved/stable; 1 = degraded/incomparable (a failing result is data, not a tool failure; verdict
  loud on stdout); 2 = usage error or malformed input; 9 = missing path or report write failure. --selftest:
  0 = all pass, 2 = assertion failure.
"""
import argparse
import io
import json
import os
import sys

PROG = "baseline_diff"
SCHEMA = "rocqwash-baseline-diff/1"
UNCLOG_SCHEMA = "rocqwash-unclog/1"
# data verdict -> exit code (a failing result is data, not a tool failure; loud
# stdout; same law as unclog VERDICT_EXIT)
VERDICT_EXIT = {"improved": 0, "stable": 0, "degraded": 1, "incomparable": 1}
# the baseline's only non-deterministic segment (measured wall-clock, differs
# every run) is excluded from the comparison and registered in the report
EXCLUDED_FIELDS = ["timing"]
# candidates_key four-tuple compared item by item; any difference means
# incomparable
CK_FIELDS = (("source", "candidates_key.source"),
             ("src", "candidates_key.src"),
             ("candidates", "candidates_key.candidates"),
             ("chain_ledgers", "candidates_key.chain_ledgers"))
CLIP_MD = 100  # --md table detail clip width (long records must not break the table; deterministic clip)


class FormError(Exception):
    """Malformed input form (rc=2; fail-loud, refuse to judge, emit no report)."""


class MissingPath(Exception):
    """Missing input path (rc=9; fail-loud, no simulation)."""


# ---- baseline loading and record self-consistency precheck ---------------------

def load_baseline(path, tag):
    """Load one blockage baseline into a record dict (missing file rc=9; JSON
    parse failure rc=2; fail-loud)."""
    if not os.path.isfile(path):
        raise MissingPath("%s baseline file missing: %s" % (tag, path))
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            rep = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise FormError("%s baseline JSON parse failure: %s (%s)" % (tag, path, e))
    return account_of(rep, path, tag)


def account_of(rep, path, tag):
    """Record structure validation (fail-loud on malformed form) plus blockage
    extraction.

    Self-consistency checks (hand-edited or mixed-in records are rejected):
    final.red_files a duplicate-free string list; final.wall_count == |wall|;
    in audit form (verdict=audit plus mode.audit) rounds is a single round,
    the probe_summary failing set equals the final failing set, and the
    chain_top list is present. Blockages = failing files (deduplicated,
    sorted) union wall roots ({reason, detail} extracted); candidates_key =
    the candidate-surface four-tuple."""
    where = "%s baseline %s" % (tag, os.path.basename(path))
    if not isinstance(rep, dict):
        raise FormError("%s malformed: top level is not a JSON object" % where)
    if rep.get("schema") != UNCLOG_SCHEMA:
        raise FormError("%s malformed: schema=%r is not %s (this tool compares"
                        " only unclog blockage baselines)"
                        % (where, rep.get("schema"), UNCLOG_SCHEMA))
    mode, args = rep.get("mode"), rep.get("args")
    wall, final, rounds = rep.get("wall"), rep.get("final"), rep.get("rounds")
    if not isinstance(mode, dict):
        raise FormError("%s malformed: mode segment missing" % where)
    if not isinstance(args, dict):
        raise FormError("%s malformed: args segment missing" % where)
    if not isinstance(wall, dict) or \
            not all(isinstance(v, dict) for v in wall.values()):
        raise FormError("%s malformed: wall segment missing or values not objects" % where)
    if not isinstance(rounds, list) or not rounds:
        raise FormError("%s malformed: rounds segment missing or empty" % where)
    if not isinstance(final, dict):
        raise FormError("%s malformed: final segment missing" % where)
    red_raw = final.get("red_files")
    if not isinstance(red_raw, list) or \
            not all(isinstance(x, str) for x in red_raw):
        raise FormError("%s malformed: final.red_files missing or not a list of strings" % where)
    if len(set(red_raw)) != len(red_raw):
        raise FormError("%s malformed: final.red_files has duplicates"
                        " (record self-consistency broken)" % where)
    wc = final.get("wall_count")
    if not isinstance(wc, int) or isinstance(wc, bool) or wc != len(wall):
        raise FormError("%s malformed: final.wall_count=%r != |wall|=%d"
                        " (record self-consistency broken)"
                        % (where, wc, len(wall)))
    verdict = final.get("verdict")
    if not isinstance(verdict, str):
        raise FormError("%s malformed: final.verdict missing" % where)
    audit_form = (verdict == "audit" and mode.get("audit") is True)
    chain_top = []
    if audit_form:
        if len(rounds) != 1:
            raise FormError("%s malformed: audit form is single-round, rounds=%d"
                            % (where, len(rounds)))
        r0 = rounds[0]
        ps = r0.get("probe_summary") if isinstance(r0, dict) else None
        if not isinstance(ps, dict):
            raise FormError("%s malformed: audit form requires rounds[0].probe_summary present"
                            % where)
        ps_red = ps.get("red_files")
        if not isinstance(ps_red, list) or ps.get("n_red") != len(red_raw) \
                or set(ps_red) != set(red_raw):
            raise FormError("%s malformed: probe_summary failing set inconsistent with"
                            " final.red_files (record self-consistency broken)" % where)
        ct = r0.get("chain_top")
        if not isinstance(ct, list) or not all(isinstance(t, dict) for t in ct):
            raise FormError("%s malformed: audit form requires rounds[0].chain_top to be a list"
                            % where)
        chain_top = ct
    red = sorted(set(red_raw))
    return {
        "path": os.path.basename(path),
        "verdict": verdict,
        "audit_form": audit_form,
        "mode_audit": mode.get("audit"),
        "n_red": len(red),
        "wall_count": len(wall),
        "red_files": red,
        "wall": {k: {"reason": v.get("reason"), "detail": v.get("detail")}
                 for k, v in wall.items()},
        "wall_roots": sorted(wall),
        "chain_top": chain_top,
        "candidates_key": {
            "source": mode.get("source"),
            "src": args.get("src"),
            "candidates": args.get("candidates"),
            "chain_ledgers": list(args.get("chain_ledgers") or []),
        },
    }


# ---- comparison core (pure JSON logic; deterministic; zero wall-clock) ---------

def comparability_reasons(old, new):
    """Comparability precheck -> reason list (empty = comparable). Two
    audit-form judgments plus an item-by-item candidates_key four-tuple
    comparison: a differing candidate set is incomparable, stated as is;
    cross-set deltas are never force-fit."""
    rs = []
    if not old["audit_form"]:
        rs.append("old baseline is not audit-form (final.verdict=%s,"
                  " mode.audit=%r); this tool compares only blockage baselines"
                  " produced by unclog --audit"
                  % (old["verdict"], old["mode_audit"]))
    if not new["audit_form"]:
        rs.append("new baseline is not audit-form (final.verdict=%s,"
                  " mode.audit=%r); this tool compares only blockage baselines"
                  " produced by unclog --audit"
                  % (new["verdict"], new["mode_audit"]))
    for field, label in CK_FIELDS:
        vo, vn = old["candidates_key"][field], new["candidates_key"][field]
        if vo != vn:
            rs.append("%s differs: old %r != new %r (a differing candidate set"
                      " is incomparable, stated as is)"
                      % (label, vo, vn))
    return rs


def entries_of(acc):
    """Record -> blockage entry dict[(kind, key)] -> entry: red-file entries
    {kind, key}; wall-root entries {kind, key, reason, detail} (wall causes
    travel with their entry)."""
    out = {}
    for k in acc["red_files"]:
        out[("red-file", k)] = {"kind": "red-file", "key": k}
    for root in acc["wall_roots"]:
        e = acc["wall"][root]
        out[("wall-root", root)] = {"kind": "wall-root", "key": root,
                                    "reason": e["reason"],
                                    "detail": e["detail"]}
    return out


def sorted_entries(entries):
    """Entries -> (kind, key)-sorted list (deterministic; for equal keys
    red-file sorts before wall-root)."""
    return [entries[k] for k in sorted(entries)]


def root_of(chain_top, name):
    """Failing file -> chain-root attribution: scan the dependents tables of
    the chain_top roots, first hit is the root. No hit -> None (generation-gap
    failures, tool-caused failures, roots beyond the reported top list: null
    as is, no guessing)."""
    for t in chain_top or []:
        if name in (t.get("dependents") or []):
            return t.get("lib")
    return None


def persistent_of(old, new, old_e, new_e):
    """Entries blocked in both baselines ((kind, key) order): wall roots
    aligned cause by cause by chain-root key (old/new reason and detail plus
    reason_changed/detail_changed); red-file entries carry the new baseline's
    chain_top chain-root attribution."""
    out = []
    for k in sorted(set(old_e) & set(new_e)):
        kind, key = k
        if kind == "wall-root":
            o, n = old_e[k], new_e[k]
            out.append({"kind": "wall-root", "key": key,
                        "old": {"reason": o["reason"], "detail": o["detail"]},
                        "new": {"reason": n["reason"], "detail": n["detail"]},
                        "reason_changed": o["reason"] != n["reason"],
                        "detail_changed": o["detail"] != n["detail"]})
        else:
            out.append({"kind": "red-file", "key": key,
                        "root": root_of(new["chain_top"], key)})
    return out


def diff(old, new):
    """Two records -> diff report dict (schema rocqwash-baseline-diff/1; zero
    wall-clock). Incomparable -> three lists empty, score_delta null, verdict
    incomparable (as is); comparable -> the three blockage lists plus
    score_delta plus verdict (reading only the n_red movement)."""
    reasons = comparability_reasons(old, new)
    rep = {
        "schema": SCHEMA,
        "old": summary_of(old),
        "new": summary_of(new),
        "comparable": not reasons,
        "incomparable_reasons": reasons,
        "excluded_fields": list(EXCLUDED_FIELDS),
        "verdict": None,
        "score": {"old": score_of(old), "new": score_of(new)},
    }
    if reasons:
        rep.update({"new_blocks": [], "resolved_blocks": [], "persistent": [],
                    "score_delta": None, "verdict": "incomparable"})
        return rep
    old_e, new_e = entries_of(old), entries_of(new)
    rep["new_blocks"] = sorted_entries(
        {k: e for k, e in new_e.items() if k not in old_e})
    rep["resolved_blocks"] = sorted_entries(
        {k: e for k, e in old_e.items() if k not in new_e})
    rep["persistent"] = persistent_of(old, new, old_e, new_e)
    d_red = new["n_red"] - old["n_red"]
    d_wall = new["wall_count"] - old["wall_count"]
    rep["score_delta"] = {"n_red": d_red, "wall_count": d_wall}
    rep["verdict"] = ("improved" if d_red < 0
                      else "degraded" if d_red > 0 else "stable")
    return rep


def score_of(acc):
    """Record -> score summary (failing-file count plus wall-root count; the
    two blockage quantities)."""
    return {"n_red": acc["n_red"], "wall_count": acc["wall_count"]}


def summary_of(acc):
    """Record -> report old/new summary (path as basename, full failing list,
    wall-root keys, candidate surface)."""
    return {"path": acc["path"], "verdict": acc["verdict"],
            "audit_form": acc["audit_form"], "n_red": acc["n_red"],
            "wall_count": acc["wall_count"], "red_files": acc["red_files"],
            "wall_roots": acc["wall_roots"],
            "candidates_key": acc["candidates_key"]}


# ---- markdown report (human reading face; deterministic) -----------------------

def _md_cell(s):
    """Markdown table cell: None -> "-", pipe escaped, overlong clipped
    (deterministic)."""
    if s is None:
        return "-"
    s = str(s).replace("|", "\\|")
    if len(s) > CLIP_MD:
        s = s[:CLIP_MD - 3] + "..."
    return s


def _delta_table(rep):
    """Score table (delta column "-" when incomparable, as is)."""
    o, n = rep["old"], rep["new"]
    sd = rep["score_delta"]
    d_red = _md_cell(sd["n_red"]) if sd else "-"
    d_wall = _md_cell(sd["wall_count"]) if sd else "-"
    return ["| metric | old | new | delta (new - old) |", "|---|---|---|---|",
            "| n_red | %d | %d | %s |" % (o["n_red"], n["n_red"], d_red),
            "| wall_count | %d | %d | %s |" % (o["wall_count"], n["wall_count"],
                                               d_wall)]


def report_md(rep):
    """Diff report -> markdown (deterministic; same input byte-identical)."""
    o, n = rep["old"], rep["new"]
    lines = ["# Baseline Diff (blockage baseline comparison, %s)" % rep["schema"], ""]
    lines.append("- old: %s (verdict=%s, audit form=%s, failing %d, wall %d)"
                 % (o["path"], o["verdict"], str(o["audit_form"]).lower(),
                    o["n_red"], o["wall_count"]))
    lines.append("- new: %s (verdict=%s, audit form=%s, failing %d, wall %d)"
                 % (n["path"], n["verdict"], str(n["audit_form"]).lower(),
                    n["n_red"], n["wall_count"]))
    ck = n["candidates_key"]
    lines.append("- candidate surface: source=%s src=%s candidates=%s chain_ledgers=%s"
                 % (ck["source"], ck["src"], ck["candidates"],
                    ",".join(ck["chain_ledgers"]) or "-"))
    lines.append("")
    lines.append("**verdict: %s**" % rep["verdict"])
    if rep["verdict"] == "incomparable":
        lines.append("")
        lines.append("Comparison refused as is (delta lists empty, score_delta null); reasons:")
        lines.extend("- %s" % r for r in rep["incomparable_reasons"])
    else:
        sd = rep["score_delta"]
        lines.append("")
        lines.append("score_delta: n_red %+d (%d -> %d), wall_count %+d (%d -> %d)"
                     % (sd["n_red"], o["n_red"], n["n_red"],
                        sd["wall_count"], o["wall_count"], n["wall_count"]))
    lines.append("")
    lines.append("## new_blocks (%d)" % len(rep["new_blocks"]))
    lines.append("")
    lines.append("| kind | key | reason | detail |")
    lines.append("|---|---|---|---|")
    for e in rep["new_blocks"]:
        lines.append("| %s | %s | %s | %s |"
                     % (e["kind"], _md_cell(e["key"]),
                        _md_cell(e.get("reason")), _md_cell(e.get("detail"))))
    lines.append("")
    lines.append("## resolved_blocks (%d)" % len(rep["resolved_blocks"]))
    lines.append("")
    lines.append("| kind | key | reason | detail |")
    lines.append("|---|---|---|---|")
    for e in rep["resolved_blocks"]:
        lines.append("| %s | %s | %s | %s |"
                     % (e["kind"], _md_cell(e["key"]),
                        _md_cell(e.get("reason")), _md_cell(e.get("detail"))))
    lines.append("")
    lines.append("## persistent (%d) (chain-root keyed, wall causes aligned one by one)"
                 % len(rep["persistent"]))
    lines.append("")
    lines.append("| kind | key | old reason | new reason | changed | chain-root attribution |")
    lines.append("|---|---|---|---|---|---|")
    for e in rep["persistent"]:
        if e["kind"] == "wall-root":
            chg = "+".join([t for t, c in (("reason", e["reason_changed"]),
                                           ("detail", e["detail_changed"]))
                            if c]) or "none"
            lines.append("| %s | %s | %s | %s | %s | - |"
                         % (e["kind"], _md_cell(e["key"]),
                            _md_cell(e["old"]["reason"]),
                            _md_cell(e["new"]["reason"]), chg))
        else:
            lines.append("| %s | %s | - | - | still failing | %s |"
                         % (e["kind"], _md_cell(e["key"]),
                            _md_cell(e.get("root"))
                            if e.get("root") is not None else "- (not attributable on the report face)"))
    lines.append("")
    lines.append("## score (delta = new - old; fewer failures is negative)")
    lines.append("")
    lines.extend(_delta_table(rep))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("Notes:")
    lines.append("- the timing segment (per-stage measured wall-clock, differs every run) is"
                 " excluded from the comparison: the baseline file's only non-deterministic"
                 " segment (excluded_fields=%s)." % json.dumps(rep["excluded_fields"]))
    lines.append("- the verdict reads only the failing-file count n_red (fewer improved /"
                 " more degraded / equal stable); wall movement lands in the three lists above"
                 " and never drives the verdict.")
    lines.append("- exit codes: 0=improved/stable, 1=degraded/incomparable (a failing result"
                 " is data, not a tool failure; loud stdout), 2=malformed input, 9=missing"
                 " path.")
    lines.append("")
    return "\n".join(lines)


# ---- loud stdout progress -------------------------------------------------------

def _brief(entries, persistent=False, limit=8):
    """Entry list -> one-line brief (tail elided past 8 items; deterministic)."""
    if not entries:
        return "-"
    parts = []
    for e in entries[:limit]:
        if e["kind"] == "wall-root":
            tag = ", cause-changed" if (e.get("reason_changed")
                                        or e.get("detail_changed")) else ""
            parts.append("%s(wall-root%s)" % (e["key"], tag))
        elif persistent and e.get("root") is not None:
            parts.append("%s(red-file -> %s)" % (e["key"], e["root"]))
        else:
            parts.append("%s(red-file)" % e["key"])
    if len(entries) > limit:
        parts.append("...+%d" % (len(entries) - limit))
    return ", ".join(parts)


def print_report(rep, old_path, new_path):
    """Loud stdout progress (full paths on stdout; verdict finale)."""
    o, n = rep["old"], rep["new"]
    print("=== BASELINE-DIFF blockage baseline comparison ===")
    print("old: %s failing %d wall %d (verdict=%s, audit form=%s)"
          % (old_path, o["n_red"], o["wall_count"], o["verdict"],
             str(o["audit_form"]).lower()))
    print("new: %s failing %d wall %d (verdict=%s, audit form=%s)"
          % (new_path, n["n_red"], n["wall_count"], n["verdict"],
             str(n["audit_form"]).lower()))
    ck = n["candidates_key"]
    print("candidate surface: source=%s src=%s candidates=%s chain_ledgers=%s"
          % (ck["source"], ck["src"], ck["candidates"],
             ",".join(ck["chain_ledgers"]) or "-"))
    if rep["verdict"] == "incomparable":
        print("INCOMPARABLE: comparison refused as is (%d reasons; delta lists empty,"
              " score_delta null):" % len(rep["incomparable_reasons"]))
        for r in rep["incomparable_reasons"]:
            print("  - %s" % r)
    else:
        print("new_blocks %d: %s" % (len(rep["new_blocks"]), _brief(rep["new_blocks"])))
        print("resolved_blocks %d: %s" % (len(rep["resolved_blocks"]),
                                          _brief(rep["resolved_blocks"])))
        print("persistent %d: %s" % (len(rep["persistent"]),
                                     _brief(rep["persistent"], persistent=True)))
    sd = rep["score_delta"]
    if sd is None:
        print("VERDICT: incomparable (refused as is, e.g. differing candidate sets)")
    else:
        print("VERDICT: %s (n_red %d -> %d delta%+d, wall_count %d -> %d delta%+d)"
              % (rep["verdict"], o["n_red"], n["n_red"], sd["n_red"],
                 o["wall_count"], n["wall_count"], sd["wall_count"]))


# ---- selftest (embedded vectors; tmp-synthesized baselines; zero network, zero build, zero real-repo touch) ----

def _mk_audit(red, wall, chain_top, src="src", candidates=None, ledgers=None,
              timing=None, verdict="audit", audit_mode=True, extra_args=None):
    """Synthesize one unclog --audit-form baseline (fixture grade; shape as
    produced by unclog.py run_audit, fields taken from its report
    construction)."""
    red = sorted(set(red))
    source = "chain-ledgers" if ledgers else "probe"
    args = {"rounds": 5, "top": 25, "scan_ids": None, "apply": False,
            "loop": False, "loop_max": 0, "interval": 60, "sleep_scale": 1.0,
            "probe_resume": False, "src": src, "world": None, "repo_path": ".",
            "candidates": candidates, "chain_ledgers": list(ledgers or []),
            "pack": "cure_pack.json", "injector": None, "guard": None,
            "rocq_cmd": None, "timeout": 900}
    if extra_args:
        args.update(extra_args)
    ps = {"source": "merge" if ledgers else "probe",
          "n_records": len(red) + 2, "n_red": len(red), "red_files": red,
          "ledgers": list(ledgers) if ledgers else ["audit.probe.json"]}
    return {"schema": UNCLOG_SCHEMA,
            "mode": {"source": source, "apply": False, "audit": audit_mode,
                     "injector": False, "loop": False},
            "args": args,
            "rounds": [{"round": 1, "probe_summary": ps,
                        "chain_top": chain_top, "root": None, "root_file": None,
                        "cure": None, "cures_planned": 0, "cures_applied": 0,
                        "rescan": None, "resprobe": None}],
            "wall": wall,
            "timing": timing or {"enumerate_s": 0.001, "manifest_s": 0.002,
                                 "probe_chain_s": 0.003, "total_s": 0.004},
            "final": {"verdict": verdict, "rounds_run": 1, "red_files": red,
                      "cures_planned_total": 0, "cures_applied_total": 0,
                      "wall_count": len(wall)},
            "verdict": verdict}


def _top1(lib, dependents, washable=True):
    """chain_top entry (chain_graph libs shape; self tri-state)."""
    return {"lib": lib, "n": len(dependents), "dependents": list(dependents),
            "self": {"probed": True, "rc": 0 if washable else 1,
                     "verdict": "GREEN" if washable else "RED-OTHER",
                     "washable": washable}}


def _wall1(root, reason, detail):
    """wall entry (unclog wall_add shape)."""
    return {"root": root, "reason": reason, "detail": detail}


def selftest():
    """Embedded vector group (tmp-synthesized baselines; zero real-repo touch,
    zero network, zero build): improved (fewer failures) / degraded (more
    failures plus wall cause change) / stable (equal; differing timing proves
    exclusion) plus byte-identical idempotence plus unwritten inputs /
    incomparable (differing candidate set plus non-audit form) / malformed
    rc=2 / missing rc=9 / md output / CLI four exit codes."""
    import shutil
    import subprocess
    import tempfile

    def run(argv):
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         PROG + ".py")] + argv,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def dump(path, obj):
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1, sort_keys=True)

    tmp = tempfile.mkdtemp(prefix="rocqwash_baslinediff_self_")
    try:
        W_UNPROBED = _wall1("Y", "unprobed", "root file not in candidate set (UNPROBED; pending probe)")
        W_SELFUN = _wall1("Y", "self-unwashable",
                          "root file itself blocked rc=1 verdict=RED-OTHER (cycle in the chain; treat the root cause first)")
        W_FROZEN = _wall1("Z", "frozen-in-service",
                          "root name/root file collides with the frozen8 register (preflight failing refusal; human-review domain)")

        # vector 1 improved (fewer failures): failing 3 -> 1; wall equal (Y same
        #   reason and detail, aligned per cause, reason_changed=False); resolved
        #   C1/D1; persistent B attributed to chain root A; rc=0
        old1 = _mk_audit(["B", "C1", "D1"], {"Y": W_SELFUN},
                         [_top1("A", ["B", "C1", "D1"])],
                         candidates="cands.tsv")
        new1 = _mk_audit(["B"], {"Y": W_SELFUN},
                         [_top1("A", ["B", "C1", "D1"])],
                         candidates="cands.tsv")
        fo, fn = os.path.join(tmp, "audit-wash-20261101.json"), \
            os.path.join(tmp, "audit-wash-20261111.json")
        dump(fo, old1)
        dump(fn, new1)
        j1 = os.path.join(tmp, "diff1.json")
        p = run([fo, fn, "--json", j1])
        assert p.returncode == 0, "fewer failures should give rc=0, got %d\n%s" % (p.returncode, p.stdout)
        r = json.load(io.open(j1, encoding="utf-8"))
        assert r["schema"] == SCHEMA and r["verdict"] == "improved", r["verdict"]
        assert r["comparable"] is True and r["incomparable_reasons"] == [], r
        assert r["excluded_fields"] == ["timing"], r
        assert r["score_delta"] == {"n_red": -2, "wall_count": 0}, r["score_delta"]
        assert r["new_blocks"] == [], r["new_blocks"]
        assert r["resolved_blocks"] == [{"kind": "red-file", "key": "C1"},
                                        {"kind": "red-file", "key": "D1"}], \
            r["resolved_blocks"]
        assert r["persistent"] == [
            {"kind": "red-file", "key": "B", "root": "A"},
            {"kind": "wall-root", "key": "Y",
             "old": {"reason": "self-unwashable",
                     "detail": W_SELFUN["detail"]},
             "new": {"reason": "self-unwashable",
                     "detail": W_SELFUN["detail"]},
             "reason_changed": False, "detail_changed": False}], r["persistent"]
        assert r["old"]["path"] == "audit-wash-20261101.json" \
            and r["new"]["path"] == "audit-wash-20261111.json", "paths must be basenames only"
        assert "VERDICT: improved" in p.stdout, p.stdout
        print("vector 1 improved (fewer failures, resolved C1/D1, wall causes aligned unchanged, rc0): PASS")

        # vector 2 degraded (more failures): failing 1 -> 3; wall Y reason changed
        #   (unprobed -> self-unwashable) plus new wall root Z (frozen);
        #   new_blocks carries both red-file and wall-root kinds; rc=1 (a failing
        #   result is data, not a tool failure)
        old2 = _mk_audit(["B"], {"Y": W_UNPROBED}, [_top1("A", ["B"])],
                         candidates="cands.tsv")
        new2 = _mk_audit(["B", "C1", "D1"], {"Y": W_SELFUN, "Z": W_FROZEN},
                         [_top1("A", ["B", "C1", "D1"])],
                         candidates="cands.tsv")
        fo2, fn2 = os.path.join(tmp, "old2.json"), os.path.join(tmp, "new2.json")
        dump(fo2, old2)
        dump(fn2, new2)
        j2 = os.path.join(tmp, "diff2.json")
        p = run([fo2, fn2, "--json", j2])
        assert p.returncode == 1, "more failures should give rc=1, got %d\n%s" % (p.returncode, p.stdout)
        r2 = json.load(io.open(j2, encoding="utf-8"))
        assert r2["verdict"] == "degraded", r2["verdict"]
        assert r2["score_delta"] == {"n_red": 2, "wall_count": 1}, r2["score_delta"]
        assert r2["new_blocks"] == [
            {"kind": "red-file", "key": "C1"},
            {"kind": "red-file", "key": "D1"},
            {"kind": "wall-root", "key": "Z", "reason": "frozen-in-service",
             "detail": W_FROZEN["detail"]}], r2["new_blocks"]
        assert r2["resolved_blocks"] == [], r2["resolved_blocks"]
        assert r2["persistent"] == [
            {"kind": "red-file", "key": "B", "root": "A"},
            {"kind": "wall-root", "key": "Y",
             "old": {"reason": "unprobed", "detail": W_UNPROBED["detail"]},
             "new": {"reason": "self-unwashable", "detail": W_SELFUN["detail"]},
             "reason_changed": True, "detail_changed": True}], r2["persistent"]
        assert "INCOMPARABLE" not in p.stdout and "VERDICT: degraded" in p.stdout, \
            p.stdout
        print("vector 2 degraded (more failures, wall reason change unprobed -> self-unwashable, new wall root, rc1): PASS")

        # vector 3 stable (equal) plus timing excluded plus byte-identical
        #   idempotence plus unwritten inputs: both records carry the same
        #   blockages; timing differs (total_s 1.111 vs 9.999) and args timeout
        #   differs; neither enters the candidate surface nor the comparison ->
        #   stable; chain-root attribution proved on both faces (B -> A,
        #   C1 -> null); --json/--md reruns byte-identical; inputs untouched
        old3 = _mk_audit(["B", "C1"], {"Y": W_SELFUN},
                         [_top1("A", ["C1"], washable=False)],
                         candidates="cands.tsv",
                         timing={"enumerate_s": 0.5, "manifest_s": 0.6,
                                 "probe_chain_s": 1.0, "total_s": 1.111},
                         extra_args={"timeout": 900})
        new3 = _mk_audit(["B", "C1"], {"Y": W_SELFUN},
                         [_top1("A", ["C1"], washable=False)],
                         candidates="cands.tsv",
                         timing={"enumerate_s": 3.5, "manifest_s": 0.9,
                                 "probe_chain_s": 5.4, "total_s": 9.999},
                         extra_args={"timeout": 1200})
        fo3, fn3 = os.path.join(tmp, "old3.json"), os.path.join(tmp, "new3.json")
        dump(fo3, old3)
        dump(fn3, new3)
        j3, m3 = os.path.join(tmp, "diff3.json"), os.path.join(tmp, "diff3.md")
        cmd3 = [fo3, fn3, "--json", j3, "--md", m3]
        raw_o, raw_n = io.open(fo3, "rb").read(), io.open(fn3, "rb").read()
        p = run(cmd3)
        assert p.returncode == 0, p.stdout
        r3 = json.load(io.open(j3, encoding="utf-8"))
        assert r3["verdict"] == "stable", r3["verdict"]
        assert r3["score_delta"] == {"n_red": 0, "wall_count": 0}, r3["score_delta"]
        assert r3["new_blocks"] == [] and r3["resolved_blocks"] == [], r3
        assert r3["persistent"] == [
            {"kind": "red-file", "key": "B", "root": None},
            {"kind": "red-file", "key": "C1", "root": "A"},
            {"kind": "wall-root", "key": "Y",
             "old": {"reason": "self-unwashable", "detail": W_SELFUN["detail"]},
             "new": {"reason": "self-unwashable", "detail": W_SELFUN["detail"]},
             "reason_changed": False, "detail_changed": False}], r3["persistent"]
        assert "timing" not in r3, "timing segment must not enter the comparison report"
        # idempotence: reruns byte-identical (json and md faces)
        before_j, before_m = io.open(j3, "rb").read(), io.open(m3, "rb").read()
        p = run(cmd3)
        assert p.returncode == 0, p.stdout
        assert io.open(j3, "rb").read() == before_j, "json byte drift = violation"
        assert io.open(m3, "rb").read() == before_m, "md byte drift = violation"
        # unwritten inputs: either baseline changed in bytes is a violation
        assert io.open(fo3, "rb").read() == raw_o \
            and io.open(fn3, "rb").read() == raw_n, "baseline input written = violation"
        print("vector 3 stable (equal; differing timing and timeout excluded; json/md"
              " byte-identical reruns; inputs untouched): PASS")

        # vector 4 incomparable (differing candidate set, as is): differing
        #   candidate list -> rc1, delta lists empty, score_delta null, reasons
        #   name the differing four-tuple items; non-audit-form input judged
        #   incomparable likewise
        fn4 = os.path.join(tmp, "new4_othercands.json")
        dump(fn4, _mk_audit(["B", "C1"], {"Y": W_SELFUN},
                            [_top1("A", ["B", "C1"], washable=False)],
                            candidates="other.tsv"))
        j4 = os.path.join(tmp, "diff4.json")
        p = run([fo3, fn4, "--json", j4])
        assert p.returncode == 1, "differing candidate set should give rc=1, got %d\n%s" \
            % (p.returncode, p.stdout)
        r4 = json.load(io.open(j4, encoding="utf-8"))
        assert r4["verdict"] == "incomparable" and r4["comparable"] is False, r4
        assert any("candidates" in x for x in r4["incomparable_reasons"]), \
            r4["incomparable_reasons"]
        assert r4["new_blocks"] == [] and r4["resolved_blocks"] == [] \
            and r4["persistent"] == [], "incomparable delta lists must be empty"
        assert r4["score_delta"] is None, r4["score_delta"]
        assert r4["score"]["old"]["n_red"] == 2, "record summary must still be present (as is)"
        # vector 4b non-audit form mixed in (closed-loop live run report, verdict=wall)
        fn4b = os.path.join(tmp, "new4b_closedloop.json")
        dump(fn4b, _mk_audit(["B", "C1"], {"Y": W_SELFUN},
                             [_top1("A", ["B", "C1"], washable=False)],
                             verdict="wall", audit_mode=False))
        j4b = os.path.join(tmp, "diff4b.json")
        p = run([fo3, fn4b, "--json", j4b])
        assert p.returncode == 1, p.stdout
        r4b = json.load(io.open(j4b, encoding="utf-8"))
        assert r4b["verdict"] == "incomparable" and \
            any("not audit-form" in x for x in r4b["incomparable_reasons"]), \
            r4b["incomparable_reasons"]
        assert r4b["score_delta"] is None, r4b["score_delta"]
        print("vector 4 incomparable (differing candidate list rc1, delta lists empty,"
              " score_delta null, non-audit form refused as is): PASS")

        # vector 5 md output: improved record --md written; all reading-face
        #   sections present (verdict / three lists / score table / timing note /
        #   exit codes); basenames registered; pipe escaping protects the table
        m5 = os.path.join(tmp, "diff1.md")
        p = run([fo, fn, "--md", m5])
        assert p.returncode == 0, p.stdout
        md = io.open(m5, encoding="utf-8").read()
        assert "verdict: improved" in md and "## new_blocks (0)" in md \
            and "## resolved_blocks (2)" in md \
            and "## persistent (2) (chain-root keyed, wall causes aligned one by one)" in md, md[:400]
        assert "| n_red | 3 | 1 | -2 |" in md, "score table delta row missing\n" + md
        assert "timing segment" in md and "excluded from the comparison" in md, "timing note missing"
        assert "audit-wash-20261101.json" in md \
            and "audit-wash-20261111.json" in md, "basenames must appear in md"
        assert "exit codes: 0=improved/stable" in md, "exit-code caliber missing"
        print("vector 5 md output (verdict / three lists / score table / timing note / exit codes): PASS")

        # vector 6 CLI four exit codes plus malformed-input refusal with no
        #   report: --help 0 / unknown flag 2 / missing args 2 / malformed (wrong
        #   schema or broken self-consistency) 2 with --json not written /
        #   missing file 9
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag should give rc=2, got %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "missing both baselines should give rc=2, got %d" % p.returncode
        p = run([fo])
        assert p.returncode == 2, "missing the new baseline should give rc=2, got %d" % p.returncode
        fbad_schema = os.path.join(tmp, "bad_schema.json")
        dump(fbad_schema, {"schema": "rocqwash-other/1", "verdict": "audit"})
        jbad = os.path.join(tmp, "bad_out.json")
        p = run([fo, fbad_schema, "--json", jbad])
        assert p.returncode == 2 and "FAIL-LOUD" in p.stdout, p.stdout
        assert not os.path.exists(jbad), "malformed input must emit no report (fail-loud)"
        fbad_integ = os.path.join(tmp, "bad_integ.json")
        bad = _mk_audit(["B"], {"Y": W_SELFUN}, [_top1("A", ["B"])])
        bad["final"]["wall_count"] = 5  # self-consistency broken: |wall|=1 != 5
        dump(fbad_integ, bad)
        p = run([fo, fbad_integ])
        assert p.returncode == 2 and "self-consistency broken" in p.stdout, p.stdout
        fbad_json = os.path.join(tmp, "bad.json")
        with io.open(fbad_json, "w", encoding="utf-8") as fh:
            fh.write("{not JSON garbage")
        p = run([fo, fbad_json])
        assert p.returncode == 2 and "parse failure" in p.stdout, p.stdout
        p = run([fo, os.path.join(tmp, "nope.json")])
        assert p.returncode == 9, "missing new baseline file should give rc=9, got %d" % p.returncode
        p = run([os.path.join(tmp, "nope.json"), fn])
        assert p.returncode == 9, "missing old baseline file should give rc=9, got %d" % p.returncode
        print("vector 6 CLI exit codes (0/2/9, malformed refusal emits nothing, self-consistency blocks hand-edited records): PASS")

        print("BASELINE-DIFF-SELFTEST PASS: six vectors all pass (improved fewer"
              " failures / degraded more failures plus wall cause change / stable"
              " equal plus timing excluded plus byte-identical reruns plus unwritten"
              " inputs / incomparable differing candidate set plus non-audit form /"
              " md output / CLI four exit codes plus malformed refusal)")
        return 0
    except AssertionError as e:
        print("BASELINE-DIFF-SELFTEST FAIL: %s" % e)
        return 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="compare two unclog --audit blockage baselines"
                               " into a blockage delta report (new_blocks /"
                               " resolved_blocks / persistent, score_delta,"
                               " four-state verdict, --md report)")
    ap.add_argument("old", metavar="OLD.json",
                    help="old blockage baseline (argv order old then new;"
                         " chronological order owned by the caller)")
    ap.add_argument("new", metavar="NEW.json", help="new blockage baseline")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="write the diff report as JSON (schema"
                         " rocqwash-baseline-diff/1)")
    ap.add_argument("--md", default=None, metavar="out.md",
                    help="write the diff report as markdown (human reading face)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        old_acc = load_baseline(args.old, "old")
        new_acc = load_baseline(args.new, "new")
    except MissingPath as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    except FormError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    rep = diff(old_acc, new_acc)
    print_report(rep, args.old, args.new)

    for path, text in ((args.json, json.dumps(rep, ensure_ascii=False,
                                               indent=1, sort_keys=True) + "\n"),
                       (args.md, report_md(rep))):
        if path:
            try:
                with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
                print("%s -> %s" % ("json" if path == args.json else "md", path))
            except OSError as e:
                print("FAIL-LOUD: report write failure: %s (%s)" % (path, e),
                      file=sys.stderr)
                sys.exit(9)

    sys.exit(VERDICT_EXIT[rep["verdict"]])


if __name__ == "__main__":
    main()
