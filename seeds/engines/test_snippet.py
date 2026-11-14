#!/usr/bin/env python3
"""test_snippet.py — E5 segment for tests/t_engines_seeds.py (engines registry
and total selftest).

Merge contract (for the seat that assembles tests/t_engines_seeds.py).
  The assembled file has five segments plus a total selftest:
    1 run_segment_ai_flavor  (E1 seat)
    2 run_segment_jargon     (E2 seat)
    3 run_segment_termbase   (E3 seat)
    4 run_segment_i18n       (E4 seat)
    5 run_segment_engines    (this segment; also carries the total selftest)
  Each segment function takes no arguments and returns a tuple
    (passed, failed, lines)
  where lines are check results, one per check, each starting with
  "PASS <check-name>" or "FAIL <check-name>: <detail>".  The total selftest
  (run_total_selftest, called by main) collects every module-level callable
  whose name starts with "run_segment_", runs each one, aggregates the counts,
  and emits a SKIP line for every expected segment name listed in
  EXPECTED_SEGMENTS that is absent from the module namespace (honest absence,
  not a silent pass).  Exit code: 0 when no FAIL line was produced, 1
  otherwise.

Layout handling (python -I safe, stdlib only, no sibling imports).
  Merged form   <root>/tests/t_engines_seeds.py      seeds at <root>/seeds
  Snippet form  <root>/seeds/engines/test_snippet.py seeds at <root>/seeds
  The seeds root is derived from __file__; in snippet form the four engine
  segments are expected to be absent, so their SKIP lines are normal there.

Checks in this segment (prefix "engines."): ENGINES.md present; exactly five
entry headings; exactly the seven CAPABILITY-INDEX fields per entry, non-
empty; four roadmap steps each with acceptance criteria; source-original
markers in the verbatim path block; version anchor present; register face
(zero CJK outside fenced code blocks, zero em-dash, zero AI-flavor battery
hits); seed paths referenced by entries exist (FAIL on absence in merged
form, SKIP in snippet form while sibling seeds are still staging).

Source of truth: seeds/engines/ENGINES.md (same directory as this snippet in
snippet form; seeds/engines/ENGINES.md under the repository root in merged
form).  Evidence base: the current-state audit cited in ENGINES.md section 0.
"""
import os
import re
import sys

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
