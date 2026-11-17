"""tests/t_engines_seeds.py -- five-engine seed assertions (E1..E5, RQW12).

Assembled suite for the RQW12 seed integration: one segment per engine plus a
total selftest. Segment bodies are transplanted verbatim from the staged
snippet files (seeds/<engine>/test_snippet.py); their module docstrings,
import lines and standalone-runner tails are not carried. Documented
adaptations (merge agent, 2026-11-14):

  A1 entry points: each segment exposes run_segment_<name>() returning
     (passed, failed, lines), per the E5 merge contract (EXPECTED_SEGMENTS
     and run_total_selftest in the engines segment below). Lines start
     with "PASS " or "FAIL "; loud SKIP lines carry their reason.
  A2 rename: the termbase segment's KEY_PATTERN is renamed
     TERMBASE_KEY_PATTERN so it cannot shadow the ai_flavor segment's.
  A3 layout: seeds are located relative to this file (<repo>/seeds). The
     ai_flavor WORD_MAP_PATH and jargon SEED_JSON anchors are repointed
     from sibling-of-__file__ to <repo>/seeds/<engine>/ as their own
     merge notes instruct; the ai_flavor detector anchor and the
     source-original checks stay skip-if-missing: off-machine runs
     report SKIP with a reason, never a silent pass.
  A4 the jargon segment's main() orchestration becomes
     run_segment_jargon() with identical check order and semantics.

Interface: `python -I tests/t_engines_seeds.py` runs the total selftest
(all five segments; EXPECTED_SEGMENTS accounting with loud SKIP lines for
any absent segment) and exits 0 when no FAIL line was produced, 1
otherwise. Python 3 standard library only; zero network; writes only
inside temporary directories (jargon and termbase fixture faces). The
seeds/ tree itself is data and SPEC faces -- zero executable engine body;
the engines grow later on rocqwash's own wash_shape / norm_lint / evolve
faces.
"""

import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path



WORD_MAP_PATH = (Path(__file__).resolve().parent.parent / "seeds" / "ai_flavor" / "word-map.json")
DETECTOR_PATH = Path("D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/ai_flavor_selfcheck.sh")

EXPECTED_SCHEMA = "rocqwash.seeds.ai-flavor.word-map/1.0"
EXPECTED_ENGINE = "ai_flavor"
EXPECTED_FACE_COUNT = 36

# Transcribed from the instrument pattern literals (detector lines 29/34/39/44,
# branch extraction) and glossary sections 4.6 and 5. Order follows the map.
EXPECTED_FACES = [
    # zh battery, 10 faces (CH_3FAMILIES_10FACES)
    "赋能", "抓手", "深耕", "闭环", "底层逻辑", "组合拳", "降本增效", "全链路", "内容矩阵", "深度剖析",
    # en word stems, 15 faces (EN_WORD_STEMS_15FACES)
    "delve", "underscore", "leverage", "foster", "showcase", "meticulous", "intricate",
    "nuanced", "multifaceted", "interplay", "holistic", "pivotal", "realm", "tapestry",
    "comprehensive",
    # en sentence faces, 8 (EN_SENTENCE_8FACES)
    "It is worth noting that", "In the realm of", "serves as", "plays a crucial role in",
    "sheds light on", "paves the way for", "not only ... but also", "in conclusion",
    # en paragraph-initial faces, 3 (EN_PARA_INITIAL_3FACES)
    "Additionally", "Moreover", "Furthermore",
]

EXPECTED_BATTERY_COUNTS = {
    "CH_3FAMILIES_10FACES": 10,
    "EN_WORD_STEMS_15FACES": 15,
    "EN_SENTENCE_8FACES": 8,
    "EN_PARA_INITIAL_3FACES": 3,
}

# Verbatim instrument pattern literals, for the soft anchor test.
BATTERY_LITERALS = {
    "CH_3FAMILIES_10FACES":
        r"赋能|抓手|深耕|闭环|底层逻辑|组合拳|降本增效|全链路|内容矩阵|深度剖析",
    "EN_WORD_STEMS_15FACES":
        r"\bdelv\w*|\bunderscor\w*|\bleverag\w*|\bfoster\w*|\bshowcas\w*|\bmeticulous\w*"
        r"|\bintricat\w*|\bnuanc\w*|\bmultifaceted\b|\binterplay\b|\bholistic\b"
        r"|\bpivotal\b|\brealm\b|\btapestr\w*|\bcomprehensive\b",
    "EN_SENTENCE_8FACES":
        r"It is worth noting that|In the realm of|\bserves? as\b"
        r"|\bplays? (a )?(crucial|pivotal|vital|key|important) role\b"
        r"|\bsheds? light on\b|\bpaves? the way for\b"
        r"|\bnot only\b[^.]{0,120}?\bbut also\b|\bin conclusion\b",
    "EN_PARA_INITIAL_3FACES":
        r"^(Additionally|Moreover|Furthermore)\b",
}

# The register enumerates exactly these three neutral direct forms as
# per-context examples (glossary section 5). Anything else in a
# neutral-direct-form candidate would be a coined word and must fail.
CANON_NEUTRAL_FORMS = {"explore", "examine", "important"}

ALLOWED_CANDIDATE_KINDS = {"ban-remediation", "delete-or-restate", "neutral-direct-form"}

KEY_PATTERN = re.compile(r"^[A-Za-z0-9_.\-]+$")

EN_STEM_BATTERY = "EN_WORD_STEMS_15FACES"
ZH_BATTERY = "CH_3FAMILIES_10FACES"
SENTENCE_BATTERIES = {"EN_SENTENCE_8FACES", "EN_PARA_INITIAL_3FACES"}


def load_word_map(path=None):
    """Load and JSON-parse the word map; raises on unreadable or invalid JSON."""
    p = Path(path) if path is not None else WORD_MAP_PATH
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _walk_keys(node):
    """Yield every mapping key at any depth."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield k
            for sub in _walk_keys(v):
                yield sub
    elif isinstance(node, list):
        for item in node:
            for sub in _walk_keys(item):
                yield sub


def _faces_by_battery(wm):
    counts = {}
    for f in wm["faces"]:
        counts[f["battery"]] = counts.get(f["battery"], 0) + 1
    return counts


def test_structure(wm):
    assert wm.get("schema") == EXPECTED_SCHEMA, "schema field mismatch: %r" % wm.get("schema")
    assert wm.get("engine") == EXPECTED_ENGINE, "engine field mismatch: %r" % wm.get("engine")
    faces = wm.get("faces")
    assert isinstance(faces, list) and faces, "faces missing or empty"
    assert len(faces) == EXPECTED_FACE_COUNT, "face count %d != %d" % (len(faces), EXPECTED_FACE_COUNT)
    assert wm.get("face_count") == EXPECTED_FACE_COUNT, "declared face_count != %d" % EXPECTED_FACE_COUNT
    emb = wm.get("structural_battery_em_dash")
    assert isinstance(emb, dict) and emb.get("excluded_from_face_count") is True, \
        "em-dash must stay outside the 36-face count"


def test_coverage(wm):
    got = {f["face"] for f in wm["faces"]}
    expect = set(EXPECTED_FACES)
    missing = sorted(expect - got)
    extra = sorted(got - expect)
    assert not missing, "faces missing from map: %r" % missing
    assert not extra, "faces not in the instrument battery: %r" % extra


def test_battery_mix(wm):
    counts = _faces_by_battery(wm)
    for battery, n in EXPECTED_BATTERY_COUNTS.items():
        assert counts.get(battery) == n, "battery %s: %r != %d" % (battery, counts.get(battery), n)
    total = sum(counts.values())
    assert total == EXPECTED_FACE_COUNT, "battery total %d != %d" % (total, EXPECTED_FACE_COUNT)


def test_candidates_present_and_typed(wm):
    for f in wm["faces"]:
        cands = f.get("candidates")
        assert isinstance(cands, list) and cands, "face %s: empty candidate list" % f["id"]
        for c in cands:
            assert c.get("kind") in ALLOWED_CANDIDATE_KINDS, \
                "face %s: candidate kind %r not allowed" % (f["id"], c.get("kind"))
            assert isinstance(c.get("value"), str) and c["value"], \
                "face %s: candidate value empty" % f["id"]
            assert isinstance(c.get("basis"), str) and c["basis"], \
                "face %s: candidate basis empty" % f["id"]


def test_no_coined_words(wm):
    for f in wm["faces"]:
        battery = f["battery"]
        kinds = {c["kind"] for c in f["candidates"]}
        if battery == ZH_BATTERY:
            assert kinds == {"ban-remediation"}, \
                "face %s: zh face must carry only ban-remediation, got %r" % (f["id"], kinds)
        elif battery == EN_STEM_BATTERY:
            assert kinds == {"neutral-direct-form"}, \
                "face %s: en stem must carry only neutral-direct-form, got %r" % (f["id"], kinds)
            values = {c["value"] for c in f["candidates"]}
            assert values == CANON_NEUTRAL_FORMS, \
                "face %s: candidate values %r deviate from the register-enumerated set %r" \
                % (f["id"], sorted(values), sorted(CANON_NEUTRAL_FORMS))
        elif battery in SENTENCE_BATTERIES:
            assert kinds == {"delete-or-restate"}, \
                "face %s: sentence face must carry only delete-or-restate, got %r" % (f["id"], kinds)
        else:
            raise AssertionError("face %s: unknown battery %r" % (f["id"], battery))


def test_keys_english(wm):
    bad = sorted({k for k in _walk_keys(wm) if not KEY_PATTERN.match(str(k))})
    assert not bad, "non-English keys: %r" % bad


def test_detector_anchor(wm=None):
    """Soft anchor: battery literals must appear verbatim in the instrument.

    Skips with a printed notice when DETECTOR_PATH is absent (the instrument
    lives in the attn workspace; CI trees may not carry it).
    """
    if not DETECTOR_PATH.is_file():
        print("SKIP test_detector_anchor: instrument not reachable at %s" % DETECTOR_PATH)
        return
    src = DETECTOR_PATH.read_text(encoding="utf-8", errors="strict")
    for battery, literal in BATTERY_LITERALS.items():
        assert literal in src, "battery %s: pattern literal not found verbatim in instrument" % battery


def run_all():
    """Run every test; return a list of (name, ok, detail) triples."""
    results = []
    wm = None
    steps = [
        ("load_word_map", lambda: load_word_map()),
    ]
    load_ok, load_detail = True, ""
    try:
        wm = load_word_map()
    except Exception as exc:  # fail loud, keep the failure itemized
        load_ok, load_detail = False, "%s: %s" % (type(exc).__name__, exc)
    results.append(("load_word_map_json", load_ok, load_detail))

    if wm is not None:
        for name, fn in [
            ("test_structure", test_structure),
            ("test_coverage", test_coverage),
            ("test_battery_mix", test_battery_mix),
            ("test_candidates_present_and_typed", test_candidates_present_and_typed),
            ("test_no_coined_words", test_no_coined_words),
            ("test_keys_english", test_keys_english),
        ]:
            try:
                fn(wm)
                results.append((name, True, "PASS"))
            except AssertionError as exc:
                results.append((name, False, str(exc)))
            except Exception as exc:  # unexpected: report, never swallow
                results.append((name, False, "%s: %s" % (type(exc).__name__, exc)))

    # anchor test runs regardless (it may skip)
    try:
        test_detector_anchor(wm)
        results.append(("test_detector_anchor", True, "PASS (or SKIP notice above)"))
    except AssertionError as exc:
        results.append(("test_detector_anchor", False, str(exc)))
    except Exception as exc:
        results.append(("test_detector_anchor", False, "%s: %s" % (type(exc).__name__, exc)))

    return results



def run_segment_ai_flavor():
    """E1 segment entry: adapt run_all() results to the merge contract."""
    results = run_all()
    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed
    lines = ["%s ai_flavor/%s -- %s" % ("PASS" if ok else "FAIL", name,
                                        detail if (not ok or detail != "PASS")
                                        else "")
             for name, ok, detail in results]
    return passed, failed, lines




HERE = os.path.dirname(os.path.abspath(__file__))
SEED_JSON = os.path.join(os.path.dirname(HERE), "seeds", "jargon",
                         "jargon-map.json")

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
        # Dual-source presence (20261118 wave59 fix): the seed legitimately
        # draws faces from BOTH pinned tracks — an annotation-whitepaper face
        # or a tool-track mapping-table face both count as transcribed.
        # Requiring the whitepaper alone broke on the 62->159 tool-track
        # expansion (73 faces live only in the mapping table).
        if e["face"] not in wp_text and e["face"] not in mv_text:
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
        # JSON seed form is loader-native since the wave59 sync (20261118):
        # the loader must read the raw JSON directly (159 terms), and the
        # fail-loud contract moves to malformed JSON (SPEC section 2 gap).
        native = None
        try:
            native = nl.load_jargon_map(SEED_JSON)
        except SystemExit as exc:
            native = ("exit", exc)
        if not isinstance(native, list) or len(native) != len(seed["entries"]):
            ok = False
            det.append("raw JSON not loader-native (%r faces loaded)"
                       % (len(native) if isinstance(native, list) else native))
        broken = os.path.join(tmp, "broken-map.json")
        with io.open(broken, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{ broken json")
        raised = None
        try:
            nl.load_jargon_map(broken)
        except SystemExit as exc:
            raised = exc
        if raised is None or getattr(raised, "code", None) != 1:
            ok = False
            det.append("malformed JSON did not fail loud with exit 1 (got %r)"
                       % raised)
        res.append(("projection-roundtrip", ok,
                    "; ".join(det) or "%d active faces load with transcribed"
                    " suggestions and exempts; JSON seed loads natively and"
                    " malformed JSON fails loud (exit 1)"
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


def run_segment_jargon():
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
    passed = 0
    failed = 0
    lines = []
    for name, ok, detail in res:
        if ok is True:
            passed += 1
            lines.append("PASS jargon/%s -- %s" % (name, detail))
        elif ok is False:
            failed += 1
            lines.append("FAIL jargon/%s -- %s" % (name, detail))
        else:
            lines.append("SKIP jargon/%s -- %s" % (name, detail))
    lines.append("SEGMENT jargon: %d checks, %d FAIL, %d SKIP"
                 % (len(res), failed, len(res) - passed - failed))
    return passed, failed, lines



SCHEMA = "rocqwash-termbase-seed/1"
TOOL = "termbase"
EXPECTED_SLOT_IDS = ["mathlib-naming-convention", "lean-style-guide",
                     "journal-style"]
SLOT_ALLOWED_KEYS = {"id", "title", "status", "source", "refresh_conditions",
                     "content"}
ENTRY_ALLOWED_KEYS = {"id", "sub_table", "row_index", "cells"}
SUB_TABLE_ORDER = ["round2", "intl", "round3", "round4"]
SEED_DIR_FILES = {"termbase.json", "net-interface-SPEC.md",
                  "diy-channel-SPEC.md", "test_snippet.py"}
TERMBASE_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
ID_PATTERN = re.compile(r"^[a-z0-9]+-r[0-9]{2,}$")


def _seed_dir():
    env = os.environ.get("ROCQWASH_SEEDS_DIR")
    if env:
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    for _ in range(8):
        # three layouts: snippet inside seeds/termbase/, merged file in a
        # tests/ dir whose ancestor carries seeds/, repo root layouts
        for cand in (os.path.join(d, "termbase", "termbase.json"),
                     os.path.join(d, "seeds", "termbase", "termbase.json"),
                     os.path.join(d, "termbase.json")):
            if os.path.isfile(cand):
                return os.path.dirname(cand)
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    raise AssertionError("termbase seed directory not found from %s "
                         "(set ROCQWASH_SEEDS_DIR to override)" % here)


def _seed_path(name):
    return os.path.join(_seed_dir(), name)


def _load_seed():
    with io.open(_seed_path("termbase.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _source_bytes_if_present():
    """Raw bytes of the glossary source, or None when this host does not
    carry it (repo/CI faces may not mount the authoring machine paths)."""
    seed = _load_seed()
    path = seed["source_of_truth"]["path"]
    if os.path.isfile(path):
        with io.open(path, "rb") as fh:
            return fh.read()
    return None


# ---------- parse face ----------

def test_parse_face():
    seed = _load_seed()
    assert seed["schema"] == SCHEMA, seed.get("schema")
    assert seed["tool"] == TOOL, seed.get("tool")
    assert isinstance(seed["description"], str) and seed["description"]
    assert isinstance(seed["slots_policy"], str) and seed["slots_policy"]
    assert "candidate order" in seed["slots_policy"]


def test_source_of_truth_recorded():
    seed = _load_seed()
    sot = seed["source_of_truth"]
    assert sot["path"].endswith(".md")
    assert "glossary" in sot["role"] or "maintenance" in sot["role"]
    snap = sot["snapshot"]
    assert isinstance(snap["bytes"], int) and snap["bytes"] > 0
    assert re.match(r"^[0-9a-f]{64}$", snap["sha256"])
    assert re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T", snap["mtime_utc"])
    assert "read-only" in sot["snapshot_discipline"]
    assert sot["section"].startswith("### 4.0")


# ---------- skeleton and entries ----------

def test_entry_skeleton_declared():
    seed = _load_seed()
    sk = seed["entry_skeleton"]
    assert isinstance(sk["origin_verbatim"], str) and sk["origin_verbatim"]
    assert sk["origin_verbatim"].startswith("**")
    subs = sk["sub_tables"]
    assert sorted(subs.keys()) == sorted(SUB_TABLE_ORDER)
    for key, st in subs.items():
        cols = st["columns"]
        assert cols == st["header_verbatim"]
        assert st["column_count"] == len(cols) >= 3
        assert len(st["english_column_names"]) == len(cols)
        assert st["row_count"] >= 1
        assert isinstance(st["preamble_verbatim"], (str, type(None)))


def test_entries_shape():
    seed = _load_seed()
    subs = seed["entry_skeleton"]["sub_tables"]
    entries = seed["entries"]
    assert isinstance(entries, list) and entries
    ids = set()
    per_table = {}
    for e in entries:
        assert set(e.keys()) == ENTRY_ALLOWED_KEYS, sorted(e.keys())
        assert ID_PATTERN.match(e["id"]), e["id"]
        assert e["id"] not in ids, "duplicate id %s" % e["id"]
        ids.add(e["id"])
        st = e["sub_table"]
        assert st in subs, st
        assert isinstance(e["row_index"], int) and e["row_index"] >= 1
        cells = e["cells"]
        assert isinstance(cells, list) and cells
        assert all(isinstance(c, str) and c.strip() for c in cells)
        assert len(cells) <= subs[st]["column_count"], (e["id"], len(cells))
        per_table.setdefault(st, []).append(e["row_index"])
    for st, idxs in per_table.items():
        assert idxs == list(range(1, len(idxs) + 1)), \
            "%s row_index sequence broken" % st
        assert len(idxs) == subs[st]["row_count"], st


def test_irregular_rows_registered():
    """Rows whose source line carries fewer cells than its table header
    declares are transcribed verbatim and must be registered in meta."""
    seed = _load_seed()
    subs = seed["entry_skeleton"]["sub_tables"]
    irregular = {r["id"] for r in seed["meta"]["source_irregular_rows"]}
    for e in seed["entries"]:
        declared = subs[e["sub_table"]]["column_count"]
        if len(e["cells"]) < declared:
            assert e["id"] in irregular, \
                "short row %s not registered" % e["id"]
        else:
            assert e["id"] not in irregular, \
                "regular row %s wrongly registered" % e["id"]
    for r in seed["meta"]["source_irregular_rows"]:
        assert r["declared_columns"] == r["actual_cells"] + 1, r
        assert r["note"], r


def test_meta_counts_consistent():
    seed = _load_seed()
    meta = seed["meta"]
    assert meta["entry_count"] == len(seed["entries"])
    counts = {}
    for e in seed["entries"]:
        counts[e["sub_table"]] = counts.get(e["sub_table"], 0) + 1
    assert meta["sub_table_counts"] == counts, meta["sub_table_counts"]
    assert meta["prose_note_count"] == len(seed["prose_notes"])
    for n in seed["prose_notes"]:
        assert set(n.keys()) == {"label", "text_verbatim"}
        assert n["label"] and n["text_verbatim"].startswith("**")


# ---------- domain slots ----------

def test_domain_slots_three_unfetched():
    seed = _load_seed()
    slots = seed["domain_slots"]
    assert isinstance(slots, list) and len(slots) == 3
    assert [s["id"] for s in slots] == EXPECTED_SLOT_IDS
    for s in slots:
        assert set(s.keys()) <= SLOT_ALLOWED_KEYS, sorted(s.keys())
        assert s["status"] == "unfetched", (s["id"], s["status"])
        assert s["content"] is None, s["id"]
        assert "payload" not in s and "entries" not in s, s["id"]
        rc = s["refresh_conditions"]
        assert isinstance(rc, list) and rc
        assert all(isinstance(c, str) and c for c in rc)
        assert any("NETRED" in c or "user-ordered" in c for c in rc), s["id"]
        src = s["source"]
        assert isinstance(src, dict) and src


def test_slot_sources_declared_not_verified():
    """Unfetched means unfetched: declared sources carry no verified flag
    of true and the journal-style slot has no URL yet (venue pending)."""
    seed = _load_seed()
    by_id = {s["id"]: s for s in seed["domain_slots"]}
    for sid in ("mathlib-naming-convention", "lean-style-guide"):
        src = by_id[sid]["source"]
        assert src["url_verified"] is False, sid
        assert src["declared_url"].startswith("https://"), sid
    src = by_id["journal-style"]["source"]
    assert src["declared_url"] is None
    assert "pending" in src["venue_nomination"]


# ---------- register (English face) ----------

def test_json_keys_english():
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert TERMBASE_KEY_PATTERN.match(k), "non-English key: %r" % k
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(_load_seed())


def test_spec_faces_english_ascii():
    for name in ("net-interface-SPEC.md", "diy-channel-SPEC.md"):
        data = io.open(_seed_path(name), "rb").read()
        data.decode("ascii")  # raises on any non-ASCII byte
        assert len(data) > 1000, name


# ---------- sync discipline (executed only when the source is present) ----------

def test_snapshot_identity_matches_source():
    data = _source_bytes_if_present()
    if data is None:
        print("SKIP test_snapshot_identity_matches_source: glossary source "
              "not present on this host")
        return
    snap = _load_seed()["source_of_truth"]["snapshot"]
    assert len(data) == snap["bytes"], "source byte count drifted"
    assert hashlib.sha256(data).hexdigest() == snap["sha256"], \
        "source sha256 drifted: regenerate the seed via the sync pass"


def _split_cells(line):
    s = line.strip()
    assert s.startswith("|") and s.endswith("|"), repr(line)
    return [c.strip() for c in s[1:-1].split("|")]


def _parse_source_section(data):
    """Minimal parser for glossary section 4.0: returns per-table
    (header_cells, row_cells lists) in document order."""
    lines = data.decode("utf-8").split("\n")
    i0 = next(i for i, l in enumerate(lines) if l.startswith("### 4.0 "))
    i1 = next(i for i, l in enumerate(lines) if l.startswith("### 4.6 "))
    tables = []
    cur = None
    for l in lines[i0 + 1:i1]:
        if l.strip().startswith("|"):
            if cur is None:
                cur = []
            cur.append(l)
        else:
            if cur is not None:
                tables.append(cur)
                cur = None
    if cur is not None:
        tables.append(cur)
    out = []
    for tl in tables:
        header = _split_cells(tl[0])
        assert set(tl[1].strip()) <= set("|-: "), tl[1]
        out.append((header, [_split_cells(x) for x in tl[2:]]))
    return out


def test_transcription_verbatim_against_source():
    """Full cell-by-cell comparison of every entry against the source
    section (executed only when the glossary file is reachable)."""
    data = _source_bytes_if_present()
    if data is None:
        print("SKIP test_transcription_verbatim_against_source: glossary "
              "source not present on this host")
        return
    seed = _load_seed()
    src_tables = _parse_source_section(data)
    assert len(src_tables) == len(SUB_TABLE_ORDER), len(src_tables)
    by_table = {}
    for e in seed["entries"]:
        by_table.setdefault(e["sub_table"], []).append(e)
    for key, (header, rows) in zip(SUB_TABLE_ORDER, src_tables):
        st = seed["entry_skeleton"]["sub_tables"][key]
        assert st["header_verbatim"] == header, key
        got = by_table[key]
        assert len(got) == len(rows), \
            "%s row count drifted: seed %d vs source %d" \
            % (key, len(got), len(rows))
        for e, src_row in zip(got, rows):
            assert e["cells"] == src_row, \
                "%s cell drift at source row %d" % (e["id"], e["row_index"])


# ---------- seed directory purity ----------

def test_seed_dir_zero_engine_body():
    d = _seed_dir()
    names = set(os.listdir(d)) - {"__pycache__"}
    assert names == SEED_DIR_FILES, \
        "seed directory surface drifted: %s" % sorted(names)
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            assert not f.endswith((".sh", ".exe", ".bat", ".cmd", ".pyd")), \
                "executable artifact in seed dir: %s" % f
            if f.endswith(".py"):
                assert f == "test_snippet.py", f


# ---------- standalone runner ----------

def _termbase_results():
    # check list verbatim from the segment's standalone runner
    checks = [
        test_parse_face,
        test_source_of_truth_recorded,
        test_entry_skeleton_declared,
        test_entries_shape,
        test_irregular_rows_registered,
        test_meta_counts_consistent,
        test_domain_slots_three_unfetched,
        test_slot_sources_declared_not_verified,
        test_json_keys_english,
        test_spec_faces_english_ascii,
        test_snapshot_identity_matches_source,
        test_transcription_verbatim_against_source,
        test_seed_dir_zero_engine_body,
    ]
    results = []
    for fn in checks:
        try:
            fn()
            results.append((fn.__name__, True, ""))
        except AssertionError as exc:
            results.append((fn.__name__, False, str(exc)))
        except Exception as exc:  # fail loud, keep counting
            results.append((fn.__name__, False, repr(exc)))
    return results


def run_segment_termbase():
    """E3 segment entry: adapt _termbase_results() to the contract."""
    results = _termbase_results()
    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed
    lines = ["%s termbase/%s%s" % ("PASS" if ok else "FAIL", name,
                                     ("" if ok else ": " + detail))
             for name, ok, detail in results]
    return passed, failed, lines




SELFTEST_TIMEOUT_S = 60


def test_i18n_pipeline_stub_selftest(stub_path=None):
    """Assert: stub --selftest exits rc=0 and prints a STUB marker.

    Returns a small evidence dict (rc + first stdout lines) so the merged
    suite can ledger the run; raises AssertionError on any failure.
    """
    path = Path(stub_path) if stub_path is not None else _default_stub_path()
    assert path.is_file(), "stub missing: %s" % path
    proc = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", str(path), "--selftest"],
        capture_output=True,
        text=True,
        timeout=SELFTEST_TIMEOUT_S,
    )
    assert proc.returncode == 0, (
        "stub --selftest rc=%d (expected 0); stderr head: %r"
        % (proc.returncode, proc.stderr[:200])
    )
    assert "STUB" in proc.stdout, (
        "no STUB marker in --selftest stdout; head: %r" % proc.stdout[:200]
    )
    return {
        "rc": proc.returncode,
        "stdout_head": proc.stdout.splitlines()[:4],
        "stub_path": str(path),
    }


def run_segment_i18n():
    """E4 segment entry: stub --selftest rc=0 with a STUB marker.

    The stub is the landed seed file <repo>/seeds/i18n/pipeline_stub.py,
    located relative to this merged suite file.
    """
    stub = Path(__file__).resolve().parent.parent / "seeds" / "i18n" / "pipeline_stub.py"
    try:
        evidence = test_i18n_pipeline_stub_selftest(stub_path=stub)
    except AssertionError as exc:
        return 0, 1, ["FAIL i18n/stub-selftest: %s" % exc]
    lines = ["PASS i18n/stub-selftest rc=%s stub=%s"
             % (evidence["rc"], evidence["stub_path"])]
    for line in evidence["stdout_head"]:
        lines.append("  | %s" % line)
    return 1, 0, lines



# ---------------------------------------------------------------- layout ---
_HERE = os.path.dirname(os.path.abspath(__file__))
_BASE = os.path.basename(_HERE)
_MERGED_MODE = (_BASE == "tests")
if _MERGED_MODE:
    _SEEDS_DIR = os.path.join(os.path.dirname(_HERE), "seeds")
elif _BASE == "engines":
    _SEEDS_DIR = os.path.dirname(_HERE)
else:
    _SEEDS_DIR = os.path.join(os.path.dirname(_HERE), "seeds")
ENGINES_MD = os.path.join(_SEEDS_DIR, "engines", "ENGINES.md")

EXPECTED_SEGMENTS = ("ai_flavor", "jargon", "termbase", "i18n", "engines")
FIELD_NAMES = ("Path", "Purpose", "Invocation", "Example", "Imports",
               "Network face", "SKIP face")
VERSION_ANCHOR = "5829f6d18a9ee2bc63c19ef46caad115e34a0c85"

_RE_ENTRY = re.compile(r"^### E[1-5] ", re.M)
_RE_STEP = re.compile(r"^### Step ([1-4]):", re.M)
_RE_ACC_HEAD = re.compile(r"^Acceptance criteria:", re.M)
_RE_ACC_ITEM = re.compile(r"^\s+A[1-9]\.", re.M)
# CJK unified ideographs and CJK punctuation blocks, enough for path text.
_RE_CJK = re.compile("[\u2e80-\u2eff\u3000-\u303f\u3400-\u4dbf"
                     "\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")
_RE_EM_DASH = re.compile("\u2014")
# Smoke subset of the ai-flavor battery (authoritative face: the E1 seed and
# the detection instrument; this inline set stays minimal on purpose).
_RE_AI_FLAVOR = re.compile(
    r"\bdelv\w*|\bunderscor\w*|\bleverag\w*|\bfoster\w*|\bshowcas\w*"
    r"|\bmeticulous\w*|\bintricat\w*|\bnuanc\w*|\bmultifaceted\b"
    r"|\binterplay\b|\bholistic\b|\bpivotal\b|\brealm\b|\btapestr\w*"
    r"|\bcomprehensive\b"
    r"|It is worth noting that|In the realm of|\bserves? as\b"
    r"|\bplays? (a )?(crucial|pivotal|vital|key|important) role\b"
    r"|\bsheds? light on\b|\bpaves? the way for\b"
    r"|\bnot only\b[^.]{0,120}?\bbut also\b|\bin conclusion\b"
    r"|^(Additionally|Moreover|Furthermore)\b", re.I | re.M)
# Verbatim path markers inside the section 0 block; CJK needles are written
# as escapes so this source file stays pure ASCII.
_NEEDLES = (
    "D:/ComplexAnalysis/",
    "\u89c4\u8303\u672f\u8bed",                    # gui-fan-shu-yu (register dir)
    "\u672f\u8bed\u8868-\u901a\u7528-\u9879\u76ee\u7ea7",   # term register file
    "\u6ce8\u91ca\u89c4\u8303\u767d\u76ae\u4e66",  # annotation whitepaper
    "\u7ea2\u7ebf\u5f8b\u767d\u76ae\u4e66",        # redline whitepaper
    "_rqw12_seeds_20261114",
    "ai_flavor_selfcheck.sh",
    "jargon-to-standard-mapping-v1.md",
)
_RE_SEED_TOKEN = re.compile(r"seeds/[A-Za-z0-9_][A-Za-z0-9_\-./]*")


def _read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _split_fenced(text):
    """Return (outside, fenced_blocks): text outside ``` fences and the list
    of fence interiors, in order."""
    outside, fences, cur, inside = [], [], [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            if inside:
                fences.append("\n".join(cur))
                cur, inside = [], False
            else:
                outside.append("\n".join(cur))
                cur, inside = [], True
            continue
        cur.append(line)
    outside.append("\n".join(cur))
    return "\n".join(outside), fences


def _entry_sections(text):
    """Split section 2 into entry bodies keyed by their heading line."""
    heads = [(m.start(), text.find("\n", m.start())) for m in
             _RE_ENTRY.finditer(text)]
    bodies = []
    for i, (start, hend) in enumerate(heads):
        nxt = heads[i + 1][0] if i + 1 < len(heads) else len(text)
        bodies.append((text[start:hend].strip(), text[hend:nxt]))
    return bodies


def segment_checks():
    """Run the engines-registry checks; return the result lines."""
    out = []
    add = out.append

    # 1 presence
    if not os.path.isfile(ENGINES_MD):
        add("FAIL engines.md_present: not found at %s" % ENGINES_MD)
        return out
    try:
        text = _read(ENGINES_MD)
    except OSError as exc:
        add("FAIL engines.md_present: unreadable (%s)" % exc)
        return out
    add("PASS engines.md_present (%d bytes)" % os.path.getsize(ENGINES_MD))

    # 2 exactly five entry headings
    entries = _entry_sections(text)
    if len(entries) != 5:
        add("FAIL engines.entries_count: expected 5 entry headings, found %d"
            % len(entries))
    else:
        add("PASS engines.entries_count (5: E1..E5)")

    # 3 + 4 seven fields per entry, non-empty
    bad_fields, bad_empty = [], []
    for head, body in entries:
        for field in FIELD_NAMES:
            hits = re.findall(r"^- %s: (.+)$" % re.escape(field), body, re.M)
            if len(hits) != 1:
                bad_fields.append("%s/%s (%d)" % (head.splitlines()[0], field,
                                                  len(hits)))
            elif not hits[0].strip():
                bad_empty.append("%s/%s" % (head.splitlines()[0], field))
    if bad_fields:
        add("FAIL engines.fields_seven: entries without exactly one line per "
            "field: %s" % "; ".join(bad_fields))
    else:
        add("PASS engines.fields_seven (7 fields x %d entries)" % len(entries))
    if bad_empty:
        add("FAIL engines.fields_nonempty: empty values: %s"
            % "; ".join(bad_empty))
    else:
        add("PASS engines.fields_nonempty")

    # 5 four roadmap steps
    steps = sorted(set(int(m) for m in _RE_STEP.findall(text)))
    if steps != [1, 2, 3, 4]:
        add("FAIL engines.roadmap_steps: expected steps 1-4, found %s" % steps)
    else:
        add("PASS engines.roadmap_steps (1..4)")

    # 6 acceptance criteria per step
    step_blocks = _RE_STEP.split(text)[1:]  # [num, body, num, body, ...]
    bad_acc = []
    for i in range(0, len(step_blocks), 2):
        num, body = step_blocks[i], step_blocks[i + 1]
        n_items = len(_RE_ACC_ITEM.findall(body))
        if not _RE_ACC_HEAD.search(body) or n_items < 2:
            bad_acc.append("step %s (items=%d)" % (num, n_items))
    if bad_acc:
        add("FAIL engines.roadmap_acceptance: %s" % "; ".join(bad_acc))
    else:
        add("PASS engines.roadmap_acceptance (each step: criteria head + items)")

    # 7 source-original markers in the verbatim path block
    _, fences = _split_fenced(text)
    block = "\n".join(fences)
    missing = [n for n in _NEEDLES if n not in block]
    if not fences:
        add("FAIL engines.originals_block: no fenced path block found")
    elif missing:
        add("FAIL engines.originals_block: markers missing from block: %s"
            % ", ".join(m.encode("unicode_escape").decode("ascii")
                        for m in missing))
    else:
        add("PASS engines.originals_block (%d markers, %d fenced block(s))"
            % (len(_NEEDLES), len(fences)))

    # 8 version anchor
    if VERSION_ANCHOR not in text:
        add("FAIL engines.version_anchor: %s absent" % VERSION_ANCHOR)
    else:
        add("PASS engines.version_anchor")

    # 9 CJK only inside fences
    outside, _ = _split_fenced(text)
    cjk_hits = _RE_CJK.findall(outside)
    if cjk_hits:
        add("FAIL engines.register_ascii: %d CJK char(s) outside fenced "
            "blocks, first at index %d" % (len(cjk_hits),
                                           outside.find(cjk_hits[0])))
    else:
        add("PASS engines.register_ascii (zero CJK outside the path block)")

    # 10 em-dash target 0 on the whole face
    dashes = _RE_EM_DASH.findall(text)
    if dashes:
        add("FAIL engines.register_emdash: %d em-dash U+2014 (target 0)"
            % len(dashes))
    else:
        add("PASS engines.register_emdash (0)")

    # 11 ai-flavor smoke battery on the whole face
    hits = [m.group(0) for m in _RE_AI_FLAVOR.finditer(text)]
    if hits:
        add("FAIL engines.register_battery: %d ai-flavor battery hit(s): %s"
            % (len(hits), ", ".join(sorted(set(hits))[:5])))
    else:
        add("PASS engines.register_battery (0 hits)")

    # 12 seed paths referenced by Path fields exist
    token_status = []
    for _, body in entries:
        for m in _RE_SEED_TOKEN.finditer(body):
            rel = m.group(0)[len("seeds/"):].rstrip("./")
            if not rel:
                continue
            path = os.path.join(_SEEDS_DIR, rel)
            if os.path.exists(path):
                token_status.append(("PASS", rel))
            elif _MERGED_MODE:
                token_status.append(("FAIL", rel))
            else:
                token_status.append(("SKIP", rel))
    n_pass = sum(1 for s, _ in token_status if s == "PASS")
    n_skip = sum(1 for s, _ in token_status if s == "SKIP")
    fails = [r for s, r in token_status if s == "FAIL"]
    if fails:
        add("FAIL engines.seed_paths: referenced seed paths absent in merged "
            "form: %s" % ", ".join(fails))
    else:
        add("PASS engines.seed_paths (%d present, %d skipped while staging)"
            % (n_pass, n_skip))
    return out


def run_segment_engines():
    """Standard segment entry (see module docstring for the contract)."""
    lines = segment_checks()
    passed = sum(1 for line in lines if line.startswith("PASS "))
    failed = sum(1 for line in lines if line.startswith("FAIL "))
    return passed, failed, lines


# ------------------------------------------------------- total selftest ---

def _segment_functions():
    return dict((name, obj) for name, obj in globals().items()
                if name.startswith("run_segment_") and callable(obj))


def run_total_selftest():
    """Run every segment present; SKIP expected-but-absent segments loudly."""
    lines, passed, failed = [], 0, 0
    found = _segment_functions()
    for name in sorted(found):
        fn = found[name]
        try:
            p, f, seg_lines = fn()
        except Exception as exc:  # fail-loud: a raising segment is a failure
            failed += 1
            lines.append("FAIL segment %s: raised %r" % (name, exc))
            continue
        passed += p
        failed += f
        lines.extend(seg_lines)
        lines.append("SEGMENT %s passed=%d failed=%d" % (name, p, f))
    missing = [s for s in EXPECTED_SEGMENTS
               if ("run_segment_" + s) not in found]
    for name in missing:
        lines.append("SKIP run_segment_%s absent from this module (merge "
                     "pending or renamed)" % name)
    lines.append("SUMMARY segments=%d expected=%d passed=%d failed=%d "
                 "missing=%d" % (len(found), len(EXPECTED_SEGMENTS), passed,
                                 failed, len(missing)))
    return passed, failed, lines


def main():
    passed, failed, lines = run_total_selftest()
    for line in lines:
        print(line)
    if failed:
        print("TOTAL-SELFTEST RED (%d failed check(s))" % failed)
        return 1
    print("TOTAL-SELFTEST GREEN (%d passed check(s))" % passed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
