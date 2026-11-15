# -*- coding: utf-8 -*-
"""comment_sweep.py — comment-domain sweep sidecar (comment_pack.json applier).

    Purpose.  Applies the comment_pack.json sweeps to a Rocq/Coq source file: flag-word exchange
      inside comment spans only (nested-comment and string-literal aware state machine — never
      inside strings, never in code positions, never before the first code character), plus an
      optional leading-header replacement from a --header-map JSON file ({basename: header text};
      the leading comment region before the first code character is replaced wholesale with the
      mapped data).  Code lines are never touched: every application asserts mechanically that the
      code-strip projection is byte-identical before and after, and that a second application
      changes nothing (idempotence, fail-loud).  Dry run by default (writes only under --apply).

    Interface.  python3 wash/comment_sweep.py --file f.v [--pack comment_pack.json]
      [--header-map map.json] [--json out.json] [--apply] | --selftest.  stdout report: flag swaps,
      header replacement, header shape validation, code-line equality; --json report {file, mode,
      md5_before, md5_after, report{flag_swaps, header_replaced, header_ok, header_problems,
      header_end_line, code_lines_equal}, idempotence_ok}.

    Dependencies.  Python 3 standard library only; the sweep pack comment_pack.json sits next to this script (data face).

    Evidence.  --selftest vectors: comment-domain flag exchange with string, nested-comment and
      idempotence guards; header replacement with a byte-equal code projection; dotted-field header
      shape validation (positive and negative); clean-file zero-change; tests/test_comment_pack.py
      reruns them end to end.

    Exit-codes.  0 = ran (dry run, or applied with idempotence verified); 1 = code-line drift or
      idempotence failure (fail-loud, file not written); 2 = usage; 9 = file, pack or header-map
      missing."""
import argparse, hashlib, io, json, os, re, sys

PROG = "comment_sweep"


def walk(text):
    """Nested-comment and string-literal aware scanner.  Returns the comment
    spans [(start, end)] (end exclusive).  A "(" inside a string never opens
    a comment; a nested "(*" inside a comment raises the depth."""
    n = len(text)
    i = 0
    depth = 0
    in_str = False
    spans = []
    cur_start = None
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if depth > 0:
            if cur_start is None:
                cur_start = i
            if text.startswith("(*", i):
                depth += 1
                i += 2
                continue
            if text.startswith("*)", i):
                depth -= 1
                i += 2
                if depth == 0:
                    spans.append((cur_start, i))
                    cur_start = None
                continue
            i += 1
            continue
        if text.startswith("(*", i):
            depth += 1
            i += 2
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        i += 1
    return spans


def first_code_offset(text):
    """Offset of the first code character (depth==0, not in a string, not
    whitespace) — the boundary of the leading-header region."""
    n = len(text)
    i = 0
    depth = 0
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1
                i += 2
                continue
            if text.startswith("*)", i):
                depth -= 1
                i += 2
                continue
            i += 1
            continue
        if text.startswith("(*", i):
            depth += 1
            i += 2
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if not c.isspace():
            return i
        i += 1
    return None


def strip_comments(text):
    """Nested-comment and string-literal aware comment stripper (w7
    criterion): comment characters removed, newlines inside comment regions
    preserved.  Returns the code-bearing text."""
    out = []
    i, n = 0, len(text)
    depth = 0
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1
                i += 2
                continue
            if text.startswith("*)", i):
                depth -= 1
                i += 2
                continue
            if c == "\n":
                out.append(c)
            i += 1
            continue
        if text.startswith("(*", i):
            depth += 1
            i += 2
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def code_lines(text):
    """The code-line-equality witness (w7 criterion): comment-stripped,
    per-line rstrip, empty lines dropped, compared as line sequences."""
    stripped = strip_comments(text)
    lines = [ln.rstrip() for ln in stripped.split("\n")]
    return [ln for ln in lines if ln]


def sweep(text, flag_words, after_first_code=True):
    """Flag-word exchange inside comment spans.  Returns (new_text, swaps)."""
    off = first_code_offset(text) if after_first_code else len(text)
    if off is None:
        off = len(text)
    head, tail = text[:off], text[off:]
    spans = walk(tail)
    out = []
    prev = 0
    swaps = 0
    for s, e in spans:
        out.append(tail[prev:s])
        seg = tail[s:e]
        for src, dst in flag_words.items():
            cnt = seg.count(src)
            swaps += cnt
            seg = seg.replace(src, dst)
        out.append(seg)
        prev = e
    out.append(tail[prev:])
    return head + "".join(out), swaps


def header_end_line(header_text):
    """gate4-style header end line (trailing blank lines excluded)."""
    lines = header_text.split("\n")
    while lines and lines[-1].strip() == "":
        lines.pop()
    return len(lines)


def validate_header(header_text, header_spec):
    """Five-field dotted shape validation → (ok, problems[])."""
    problems = []
    for field in header_spec.get("fields", []):
        if field not in header_text:
            problems.append("missing field %r" % field)
    end_line = header_end_line(header_text)
    max_end = header_spec.get("max_end_line")
    if max_end is not None and end_line > max_end:
        problems.append("header end line %d > %d" % (end_line, max_end))
    return (not problems), problems, end_line


def run(text, pack, header_map=None, name=None):
    """One sweep pass → (new_text, report dict).  Never writes.  The header
    map is keyed by file basename with or without the .v suffix (both forms
    are tried)."""
    flag_words = pack.get("flag_words", {})
    header_spec = pack.get("header_spec", {})
    report = {}
    new_text, swaps = sweep(text, flag_words)
    report["flag_swaps"] = swaps
    report["header_replaced"] = False
    mapped = None
    for key in ([name, name[:-2]] if (name and name.endswith(".v")) else [name]):
        if header_map and key in header_map:
            mapped = header_map[key]
            break
    if mapped is not None:
        # replace against the SWEPT text (the leading region is untouched by
        # the flag-word pass, but the tail must stay the swept one)
        off2 = first_code_offset(new_text)
        if off2 is None:
            off2 = len(new_text)
        if new_text[:off2] != mapped:
            new_text = mapped + new_text[off2:]
            report["header_replaced"] = True
        ok, problems, end_line = validate_header(mapped, header_spec)
    else:
        off = first_code_offset(text)
        cur = text[:off] if off is not None else ""
        ok, problems, end_line = validate_header(cur, header_spec) \
            if cur.strip() else (True, [], 0)
    report["header_ok"] = ok
    report["header_problems"] = problems
    report["header_end_line"] = end_line
    report["code_lines_equal"] = code_lines(text) == code_lines(new_text)
    return new_text, report


def md5s(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def selftest():
    ok = True
    here = os.path.dirname(os.path.abspath(__file__))
    pack = json.load(io.open(os.path.join(here, "comment_pack.json"),
                             encoding="utf-8"))

    # 1. flag-word exchange in comments; string literal and code untouched
    src = ('(* the 载体 word sits here *)\n'
           'Definition f (x : nat) := x + 0. (* second 载体 note *)\n'
           'Definition s := "载体 inside a string".\n'
           'Definition g := 1.  (* nested (* 载体 deep *) still 载体 *)\n')
    t, r1 = run(src, pack)
    c1 = (r1["flag_swaps"] == 3
          and t.count("carrier") == 3
          and '"载体 inside a string"' in t
          and "Definition f (x : nat) := x + 0." in t
          and "(* nested (* carrier deep *) still carrier *)" in t)
    t2, r1b = run(t, pack)
    c1b = r1b["flag_swaps"] == 0 and t2 == t
    print("flag-word comment-domain exchange / string+nested+idempotent:",
          c1, c1b)
    ok = ok and c1 and c1b

    # 2. leading-header replacement; code projection byte-equal; idempotent
    hdr = ("(* Module header. *)\n\n"
           "(** * demo: demo file.\n\n"
           "    Mission.  demonstrate the header replacement.\n\n"
           "    Dependencies.  none.\n\n"
           "    References.  none.\n\n"
           "    Constructivity.  all proofs close by Qed.\n\n"
           "    Build.  compiles cleanly. *)\n\n")
    src2 = ("(* 旧头注\n   多行\n   载体一词在此 *)\n"
            "Definition k := 0. (* 载体 *)\n")
    t3, r3 = run(src2, pack, header_map={"demo": hdr}, name="demo")
    c2 = (r3["header_replaced"] and t3.startswith(hdr)
          and r3["code_lines_equal"]
          and "Definition k := 0. (* carrier *)" in t3
          and "旧头注" not in t3)
    t4, r4 = run(t3, pack, header_map={"demo": hdr}, name="demo")
    c2b = (not r4["header_replaced"]) and t4 == t3 and r4["flag_swaps"] == 0
    print("header replace / code-projection equal / idempotent:", c2, c2b)
    ok = ok and c2 and c2b

    # 3. header shape validation: five dotted fields + end-line bound
    ok_good, prob_good, el = validate_header(hdr, pack["header_spec"])
    bad = "(* short header, no fields *)\nDefinition z := 0.\n"
    ok_bad, prob_bad, el_bad = validate_header(bad, pack["header_spec"])
    c3 = (ok_good and not prob_good and el <= 30
          and not ok_bad and len(prob_bad) >= 5)
    print("header shape validation pos/neg:", c3, prob_bad[:2])
    ok = ok and c3

    # 4. no-flag-word file: zero swaps, zero changes
    src4 = "Definition q := 2.\n"
    t5, r5 = run(src4, pack)
    c4 = r5["flag_swaps"] == 0 and t5 == src4
    print("clean file zero-change:", c4)
    ok = ok and c4

    print("COMMENT-SWEEP-SELFTEST:", "PASS" if ok else "FAIL")
    return ok


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="Comment-domain sweep sidecar (comment_pack.json): "
                    "flag-word exchange + optional header replacement, "
                    "code-line equality asserted.")
    ap.add_argument("--file", help="target .v file")
    ap.add_argument("--pack", default=os.path.join(here, "comment_pack.json"))
    ap.add_argument("--header-map", default=None,
                    help="JSON file {basename: header text}")
    ap.add_argument("--json", help="write sweep report JSON here")
    ap.add_argument("--apply", action="store_true",
                    help="write the swept file (default dry-run)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(0 if selftest() else 2)
    if not args.file:
        ap.print_help()
        sys.exit(2)
    if not os.path.exists(args.file):
        print("FILE-MISSING:", args.file)
        sys.exit(9)
    if not os.path.exists(args.pack):
        print("PACK-MISSING:", args.pack)
        sys.exit(9)
    header_map = None
    if args.header_map:
        if not os.path.exists(args.header_map):
            print("HEADER-MAP-MISSING:", args.header_map)
            sys.exit(9)
        header_map = json.load(io.open(args.header_map, encoding="utf-8"))

    pack = json.load(io.open(args.pack, "r", encoding="utf-8"))
    text = io.open(args.file, "r", encoding="utf-8", errors="replace").read()
    before = md5s(text)
    new_text, report = run(text, pack, header_map=header_map,
                           name=os.path.basename(args.file))
    mode = "APPLIED" if args.apply else "DRY-RUN"
    print("file: %s" % args.file)
    print("mode: %s  pack: %s v%s" % (mode, pack.get("pack", "?"),
                                      pack.get("version", "?")))
    print("md5 before: %s  after: %s" % (before, md5s(new_text)))
    print("  flag_swaps=%d header_replaced=%s header_ok=%s header_end_line=%s"
          % (report["flag_swaps"], report["header_replaced"],
             report["header_ok"], report["header_end_line"]))
    for p in report["header_problems"]:
        print("  header-finding: %s" % p)
    rc = 0
    if not report["code_lines_equal"]:
        print("CODE-LINE-DRIFT: code projection changed — the sweep touched "
              "code; file NOT written (fail-loud)")
        rc = 1
    elif args.apply:
        if new_text != text:
            # newline="" pins the byte face (the T0-5 md5-caliber contract,
            # same fix as cure_applier.py): on-disk bytes are exactly
            # new_text.encode("utf-8") on every platform, so the reported
            # md5_after always describes the file actually written; the
            # unpinned default let Windows text mode translate \n to \r\n,
            # which then also re-flagged the eol wash on rescan.
            with io.open(args.file, "w", encoding="utf-8", newline="") as f:
                f.write(new_text)
        t2, r2 = run(new_text, pack, header_map=header_map,
                     name=os.path.basename(args.file))
        resid = r2["flag_swaps"] + (1 if r2["header_replaced"] else 0)
        if resid or t2 != new_text:
            print("IDEMPOTENCE-FAIL: second pass residual=%d" % resid)
            print("file NOT written; report the residual to the caller")
            rc = 1
        else:
            print("idempotence verified (second pass zero-change); "
                  "code-line equality holds; file written")
    else:
        print("dry-run: no file written (code-line equality: %s)"
              % report["code_lines_equal"])
    if args.json:
        out = dict(file=args.file, mode=mode, md5_before=before,
                   md5_after=md5s(new_text), report=report,
                   idempotence_ok=(rc == 0))
        with io.open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("report json -> %s" % args.json)
    sys.exit(rc)


if __name__ == "__main__":
    main()
