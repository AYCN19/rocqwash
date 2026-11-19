"""test_snippet.py: seed completeness checks for the ai_flavor word map.

Purpose.  Asserts the data contract of seeds/ai_flavor/word-map.json (engine
  E1, seed work stream RQW12, 36 faces) and the transcription of the four
  battery pattern literals: structure, coverage (face set equals the 36
  instrument faces, both directions), battery mix (10 zh + 15 en stems + 8
  en sentence + 3 en paragraph-initial), candidate presence and typing, the
  per-battery no-coinage kind rules, English-only JSON keys at any depth,
  and the soft instrument anchor.  This file embeds the face constants by
  design (it is the assertion corpus for them), so the wording batteries
  fire on this file itself and the em-dash count must stay 0.  Provenance
  and the replacement-closure gap: the adjacent SPEC.md.

Interface.  Standalone: python -I test_snippet.py.  Module surface:
  load_word_map(path=None), the test_* functions, run_all(), main(argv=None);
  the suite integrator merges this segment into tests/t_engines_seeds.py,
  pointing WORD_MAP_PATH at seeds/ai_flavor/word-map.json in-tree and
  keeping DETECTOR_PATH as a skip-if-missing anchor (the instrument lives
  in the attn workspace and may be absent on other machines;
  test_detector_anchor then skips with a printed notice).

Dependencies.  Python 3 standard library only (json, re, sys, pathlib); reads
  word-map.json and, when reachable, the instrument source at DETECTOR_PATH.

Evidence.  run_all() prints one PASS/FAIL line per check with a detail line,
  so failures are itemized, not aggregated.

Exit-codes.  0 = no FAIL; 1 = at least one FAIL (listed, fail-loud); a missing
  instrument yields a loud SKIP line, never a silent pass.
"""

import json
import re
import sys
from pathlib import Path

WORD_MAP_PATH = Path(__file__).resolve().parent / "word-map.json"
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


def main(argv=None):
    results = run_all()
    failed = 0
    for name, ok, detail in results:
        print("%-40s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if not ok:
            failed += 1
    total = len(results)
    print("ai_flavor word-map seed: %d/%d checks passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
