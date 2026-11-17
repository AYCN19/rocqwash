#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_snippet.py — E2 jargon seed checks (seeds/jargon suite section).

Purpose.  Asserts the seed data contract and the detection round-trip for
  seeds/jargon/jargon-map.json (SPEC.md is the contract text): schema shape,
  the exact count label with the mandated 62-entry seed prefix (J001..J062)
  preserved under the md-table sync growth, unique ids and faces; per-entry
  verbatim transcription against the pinned sources; snapshot md5 pinning;
  the projection onto the norm_lint jargon-map loader and per-face detection
  of every mapped face with transcribed suggestions; the preserve carve-out
  exemption; clean-fixture silence; fail-loud raw-JSON loader behavior; the
  wash_shape absence probe behind SPEC section 3.

Interface.  Standalone: python -B seeds/jargon/test_snippet.py.  The module
  exposes CHECKS and main() for the suite integrator.  Optional environment:
  ROCWASH_ROOT (repository root while the seed lives outside the tree;
  default discovery walks up looking for tools/norm_lint.py);
  RQW_SOURCE_ROOT (directory of the pinned source originals; default is the
  path recorded in the JSON provenance).

Dependencies.  Python 3 standard library only.  Reads tools/norm_lint.py and
  the pinned source originals.  Missing externals produce loud SKIP lines,
  never silent passes.  Writes only inside a temporary directory.

Evidence.  Every check prints PASS/FAIL/SKIP with a detail line.  The
  62-face coverage check iterates every entry individually, so coverage is
  per-face, not per-count.

Exit-codes.  0 = no FAIL; 1 = at least one FAIL (listed).  SKIP lines are
  reported and do not fail the run.
"""

import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SEED_JSON = os.path.join(HERE, "jargon-map.json")

# fixed suggestion string for rewrite_or_delete entries in the projected
# table (SPEC section 2, projection rule)
UNMAPPED_SUGGEST = "rewrite per context or delete (no fixed standard recorded)"

# loader skip rules (norm_lint load_jargon_map): a row is skipped when its
# first cell is empty, a dash run, or carries the loader's CJK header marker;
# the separator-first form keeps this file ASCII-only
TABLE_HEAD = "|---|---|---|---|\n"


def load_seed():
    with io.open(SEED_JSON, "r", encoding="utf-8") as fh:
        return json.load(fh)


def repo_root():
    env = os.environ.get("ROCWASH_ROOT")
    if env and os.path.isfile(os.path.join(env, "tools", "norm_lint.py")):
        return env
    d = HERE
    for _ in range(6):
        if os.path.isfile(os.path.join(d, "tools", "norm_lint.py")):
            return d
        d = os.path.dirname(d)
    return None


def source_root(seed):
    env = os.environ.get("RQW_SOURCE_ROOT")
    cands = [env] if env else []
    for s in seed.get("provenance", {}).get("sources", []):
        cands.append(os.path.dirname(s["path"]))
    for c in cands:
        if c and os.path.isdir(c):
            return c
    return None


def load_norm_lint(root):
    path = os.path.join(root, "tools", "norm_lint.py")
    spec = importlib.util.spec_from_file_location("rqw_norm_lint_seed", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def project_table(seed, out_path):
    """SPEC section 2 projection: one data row per entry."""
    rows = [TABLE_HEAD]
    for e in seed["entries"]:
        std = e["standard"] if e["disposition"] == "replace" else UNMAPPED_SUGGEST
        tag = "annotation-track" if "annotation-whitepaper" in (e["standard_source"] or "") \
            else ("tool-track" if e["standard_source"] else "rewrite-or-delete")
        cells = [e["face"], std, tag, ";".join(e.get("exempts") or [])]
        rows.append("| " + " | ".join(cells) + " |\n")
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(rows))
    return out_path


def check_json_contract(seed, res):
    ok, det = True, []
    if seed.get("schema") != "rocqwash-jargon-map/1":
        ok = False
        det.append("schema mismatch: %r" % seed.get("schema"))
    ents = seed.get("entries", [])
    # the P1 md sync grew the map; the count label must stay exact and the
    # 62-entry seed prefix (J001..J062) must survive every sync
    seed_ids = set("J%03d" % i for i in range(1, 63))
    if seed.get("count") != len(ents) or len(ents) != 159:
        ok = False
        det.append("count label %r != %d entries or map size != 159"
                   % (seed.get("count"), len(ents)))
    if not seed_ids <= set(e.get("id") for e in ents):
        ok = False
        det.append("the 62-entry seed prefix (J001..J062) is not preserved")
    ids = [e.get("id") for e in ents]
    faces = [e.get("face") for e in ents]
    if len(set(ids)) != len(ids) or len(set(faces)) != len(faces):
        ok = False
        det.append("duplicate id or face")
    for e in ents:
        if e.get("disposition") not in ("replace", "rewrite_or_delete"):
            ok = False
            det.append("%s bad disposition %r" % (e.get("id"), e.get("disposition")))
        elif e["disposition"] == "replace" and not (isinstance(e.get("standard"), str) and e["standard"]):
            ok = False
            det.append("%s replace without standard" % e["id"])
        elif e["disposition"] == "rewrite_or_delete" and e.get("standard") is not None:
            ok = False
            det.append("%s rewrite_or_delete carries a standard" % e["id"])
        if not isinstance(e.get("exempts"), list):
            ok = False
            det.append("%s exempts not a list" % e["id"])
    srcs = seed.get("provenance", {}).get("sources", [])
    if len(srcs) != 3 or any(not s.get("md5") or not s.get("path") for s in srcs):
        ok = False
        det.append("provenance sources incomplete: %d" % len(srcs))
    res.append(("json-contract", ok, "; ".join(det) or "159 entries with the"
                " 62-entry seed prefix preserved, unique ids/faces, exact"
                " count label, disposition rules hold, provenance pinned"))


def check_transcription(seed, sroot, res):
    if sroot is None:
        res.append(("transcription", None,
                    "SKIP — source originals not on this machine (set RQW_SOURCE_ROOT)"))
        return
    wp_name = [s["path"] for s in seed["provenance"]["sources"]
               if s["role"].startswith("annotation-track")]
    if not wp_name:
        res.append(("transcription", False, "whitepaper not pinned in provenance"))
        return
    wp_path = os.path.join(sroot, os.path.basename(wp_name[0]))
    try:
        wp_text = io.open(wp_path, encoding="utf-8").read()
    except OSError as exc:
        res.append(("transcription", None, "SKIP — whitepaper unreadable: %s" % exc))
        return
    mv_src = [s for s in seed["provenance"]["sources"] if s["path"].endswith("jargon-to-standard-mapping-v1.md")]
    mv_text = ""
    if mv_src:
        try:
            mv_text = io.open(mv_src[0]["path"], encoding="utf-8").read()
        except OSError:
            mv_text = ""
    bad = []
    for e in seed["entries"]:
        if e["face"] not in wp_text:
            bad.append("%s face absent from whitepaper" % e["id"])
            continue
        if e["disposition"] != "replace":
            continue
        if e["standard_source"].startswith("annotation-whitepaper"):
            if e["standard"] not in wp_text:
                bad.append("%s standard not verbatim in whitepaper" % e["id"])
        else:
            if not mv_text or e["standard"] not in mv_text:
                bad.append("%s standard not verbatim in tool-track table" % e["id"])
    res.append(("transcription", not bad,
                "every face verbatim in the whitepaper; standards verbatim in their pinned sources"
                if not bad else "; ".join(bad)))


def check_snapshot_md5(seed, res):
    drifted, missing = [], []
    for s in seed["provenance"]["sources"]:
        try:
            import hashlib
            cur = hashlib.md5(io.open(s["path"], "rb").read()).hexdigest()
        except OSError:
            missing.append(s["path"])
            continue
        if cur != s["md5"]:
            drifted.append("%s (pinned %s / current %s)" % (s["path"], s["md5"][:8], cur[:8]))
    if missing:
        res.append(("snapshot-md5", None,
                    "SKIP — %d of 3 pinned sources absent: %s" % (len(missing), missing[0])))
    elif drifted:
        res.append(("snapshot-md5", False,
                    "source drifted from the pinned snapshot; re-transcribe the seed per the sync discipline: " + "; ".join(drifted)))
    else:
        res.append(("snapshot-md5", True, "all 3 pinned sources match their md5 snapshots"))


def check_projection_roundtrip(seed, root, res):
    nl = _norm_lint(root, res)
    if nl is None:
        return
    tmp = tempfile.mkdtemp(prefix="rqw_jargon_seed_")
    try:
        table = project_table(seed, os.path.join(tmp, "jargon-map.table.md"))
        terms = nl.load_jargon_map(table)
        names = sorted(t.term for t in terms)
        want = sorted(e["face"] for e in seed["entries"])
        ok, det = True, []
        if len(terms) != len(seed["entries"]) or names != want:
            ok = False
            det.append("loader active faces %d != %d entries or set mismatch"
                       % (len(terms), len(seed["entries"])))
        by_face = dict((e["face"], e) for e in seed["entries"])
        for t in terms:
            e = by_face[t.term]
            want_suggest = e["standard"] if e["disposition"] == "replace" else UNMAPPED_SUGGEST
            if t.suggest != want_suggest:
                ok = False
                det.append("%s suggest mismatch" % e["id"])
            want_ex = [re.compile(x) for x in (e.get("exempts") or [])]
            if len(t.exempts) != len(want_ex):
                ok = False
                det.append("%s exempt count mismatch" % e["id"])
        # fail-loud: raw JSON is not loader-readable (SPEC section 2 gap)
        raised = None
        try:
            nl.load_jargon_map(SEED_JSON)
        except SystemExit as exc:
            raised = exc
        if raised is None or getattr(raised, "code", None) != 1:
            ok = False
            det.append("raw JSON did not fail loud with exit 1 (got %r)" % raised)
        res.append(("projection-roundtrip", ok,
                    "; ".join(det) or "%d active faces load with transcribed"
                    " suggestions and exempts; raw JSON fails loud (exit 1)"
                    % len(seed["entries"])))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_detection_coverage(seed, root, res):
    nl = _norm_lint(root, res)
    if nl is None:
        return
    tmp = tempfile.mkdtemp(prefix="rqw_jargon_seed_")
    try:
        table = project_table(seed, os.path.join(tmp, "jargon-map.table.md"))
        terms = nl.load_jargon_map(table)
        header = ('"""fixture: one banned face per comment line.\n\n'
                  "Purpose.  Seed detection coverage fixture.\n"
                  "Interface.  None (fixture).\n"
                  "Dependencies.  None.\n"
                  "Evidence.  Seed test vector.\n"
                  "Exit-codes.  0.\n"
                  '"""\n')
        lines = [header]
        phys = header.count("\n")  # physical lines the docstring header occupies
        expect = {}
        for k, e in enumerate(seed["entries"]):
            # ASCII prefix/suffix so the CJK whole-word adjacency rule sees a
            # plain occurrence; the preserve carve-out word is never adjacent
            phys += 1
            lines.append("# face %03d: %s\n" % (k + 1, e["face"]))
            expect[e["face"]] = phys
        fx = os.path.join(tmp, "fixture_faces.py")
        with io.open(fx, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("".join(lines))
        rec = nl.scan_file("fixture_faces.py", fx, "py", terms, 0.0, set(), table)
        fired = {}
        for f in rec["findings"]:
            if f["kind"] == "jargon":
                fired.setdefault(f["term"], f)
        missing = [e["id"] + ":" + e["face"] for e in seed["entries"] if e["face"] not in fired]
        extra = [t for t in fired if t not in expect]
        wrong_line = [t for t, f in fired.items() if f["line"] != expect[t]]
        bad_suggest = [t for t, f in fired.items()
                       if f["suggest"] != (by_face_suggest(seed, t))]
        ok = not (missing or extra or wrong_line or bad_suggest)
        det = []
        if missing:
            det.append("not detected: %s" % ", ".join(missing))
        if extra:
            det.append("unexpected hits: %s" % ", ".join(extra))
        if wrong_line:
            det.append("wrong line: %s" % ", ".join(wrong_line))
        if bad_suggest:
            det.append("suggestion mismatch: %s" % ", ".join(bad_suggest))
        res.append(("detection-full-face-coverage", ok,
                    "; ".join(det) or "each mapped face fires exactly once on its own fixture line, with its transcribed suggestion"))
        # carve-out exemption: the preserved compound never triggers its face
        fx2 = os.path.join(tmp, "fixture_exempt.py")
        carve = [e for e in seed["entries"] if e.get("exempts")]
        if carve:
            with io.open(fx2, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(header + "# the preserved compound stays: %s\nx = 1\n" % carve[0]["exempts"][0])
            rec2 = nl.scan_file("fixture_exempt.py", fx2, "py", terms, 0.0, set(), table)
            hits = [f["term"] for f in rec2["findings"] if f["kind"] == "jargon"]
            res.append(("carveout-exemption", hits == [],
                        "preserved compound '%s' silent for face '%s'" % (carve[0]["exempts"][0], carve[0]["face"])
                        if hits == [] else "unexpected hits: %s" % ", ".join(hits)))
        # clean fixture: zero jargon findings
        fx3 = os.path.join(tmp, "fixture_clean.py")
        with io.open(fx3, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(header + "# the invariant holds because the bound is monotone\ny = 2\n")
        rec3 = nl.scan_file("fixture_clean.py", fx3, "py", terms, 0.0, set(), table)
        hits3 = [f["term"] for f in rec3["findings"] if f["kind"] == "jargon"]
        res.append(("clean-fixture", hits3 == [],
                    "no jargon findings on a clean English fixture" if hits3 == [] else "unexpected hits: %s" % ", ".join(hits3)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def by_face_suggest(seed, face):
    for e in seed["entries"]:
        if e["face"] == face:
            return e["standard"] if e["disposition"] == "replace" else UNMAPPED_SUGGEST
    return None


def check_wash_shape_gap(root, res):
    # Landed form (the engine-body ticket's integration, SPEC section 3
    # integration note holds: the application face exists as the jargon
    # wash stage, and the sentinel fails if the wiring is removed.
    if root is None:
        res.append(("washshape-gap-probe", None,
                    "SKIP — repository root not found (set ROCWASH_ROOT)"))
        return
    text = io.open(os.path.join(root, "tools", "wash_shape.py"), encoding="utf-8").read()
    if "jargon" in text and "KIND_JARGON" in text:
        res.append(("washshape-gap-probe", True,
                    "wash_shape carries the jargon wash stage; the SPEC section 3 integration note holds"))
    else:
        res.append(("washshape-gap-probe", False,
                    "tools/wash_shape.py lost the jargon wash stage; the SPEC section 3 integration "
                    "note no longer matches the tree: restore the wiring or update the SPEC"))


_NL_CACHE = {}


def _norm_lint(root, res):
    if root in _NL_CACHE:
        return _NL_CACHE[root]
    if root is None:
        res.append(("norm-lint", None,
                    "SKIP — repository root not found; loader-dependent checks skipped (set ROCWASH_ROOT)"))
        _NL_CACHE[root] = None
        return None
    try:
        mod = load_norm_lint(root)
    except Exception as exc:  # noqa: BLE001 — fail-loud below
        res.append(("norm-lint", False, "cannot load tools/norm_lint.py: %r" % (exc,)))
        _NL_CACHE[root] = None
        return None
    _NL_CACHE[root] = mod
    return mod


CHECKS = ("json-contract", "transcription", "snapshot-md5", "projection-roundtrip",
          "detection-full-face-coverage", "carveout-exemption", "clean-fixture",
          "washshape-gap-probe")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = repo_root()
    seed = load_seed()
    res = []
    check_json_contract(seed, res)
    sroot = source_root(seed)
    check_transcription(seed, sroot, res)
    check_snapshot_md5(seed, res)
    check_projection_roundtrip(seed, root, res)
    check_detection_coverage(seed, root, res)
    check_wash_shape_gap(root, res)
    failed = 0
    skipped = 0
    for name, ok, detail in res:
        if ok is True:
            tag = "PASS"
        elif ok is False:
            tag = "FAIL"
            failed += 1
        else:
            tag = "SKIP"
            skipped += 1
        print("%s %s — %s" % (tag, name, detail))
    print("summary: %d checks, %d FAIL, %d SKIP" % (len(res), failed, skipped))
    if skipped:
        print("skip note: skipped checks need external inputs; see their reasons above")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
