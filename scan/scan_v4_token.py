# -*- coding: utf-8 -*-
"""scan_v4_token.py — token-level qualified-identifier census for .v sources.

    Purpose.  Statement-face scanners see declaration segments only: a line
      carrying BOTH a qualified constructor reference (``Datatypes.S``) and a
      bare ``S`` token escapes any line-level ``grep -v``-style filter that drops
      qualified-carrying lines, so the bare token on that line is never reported.
      This scanner works at token granularity: strip nested comments and string
      literals (line/col preserving); treat dotted qualified names as single
      tokens; classify each bare occurrence of a configured identifier via binder
      tracking (``forall x``, ``(x : T)``, ``{x : T}``, ``fun x``, ``let x :=``,
      Section ``Variable/Context/Hypothesis``), so a locally re-bound short name
      (e.g. a Class parameter named ``S``) is not flagged as a successor reference.

    Interface.  ``python3 scan/scan_v4_token.py --file <f.v> [--json out.json]
      [--ids S] [--text]`` (cw.sh route ``scan4``).  ``--json`` writes the census
      report: ``stations`` list of {line, col, token, cls, grade, mixed_line,
      context} (``cls`` shadow-hazard or unqualified-global; ``mixed_line`` = the
      same line also carries the qualified form), ``context`` per-identifier
      counters, ``shadow_sources`` record/class fields or constructors named like
      a tracked identifier.  ``--text`` prints the station list.

    Dependencies.  Python 3 standard library only; one Rocq/Coq source file (.v) as input.

    Evidence.  Suite case ``t_scan_v4_token`` (tests/run_tests.sh) runs
      ``tests/test_scan_v4_token.py`` over ``tests/fixtures/scan_v4_shadow_fixture.v`` (station,
      masking-blindness, binder vectors); ``tools/unclog.py`` uses it as its re-scan stage.

    Exit-codes.  0 = ran clean (stations may exist; this tool reports, never
      blesses), 2 = CLI usage error, 9 = input file missing.
"""
import argparse, io, json, os, re, sys

# Dotted-qualified identifier: one token per full dotted path.
TOKEN_RE = re.compile(r"[A-Za-z_'][A-Za-z0-9_']*(?:\.[A-Za-z_'][A-Za-z0-9_']*)*")

# Default tracked identifier set: short constructor names most often shadowed
# by record/class fields in this codebase family.  Extendable via --ids.
DEFAULT_IDS = ("S",)

# Top-level vernacular keywords that terminate a binder's enclosing scope.
DECL_START_RE = re.compile(
    r"^[ \t]*(?:(?:#\[[^\]]*\])[ \t]*(?:\r?\n)?[ \t]*|"
    r"(?:Local|Global|Export|Declare)[ \t]+)*"
    r"(Lemma|Theorem|Definition|Corollary|Fixpoint|CoFixpoint|Proposition|"
    r"Instance|Record|Inductive|CoInductive|Class|Context|Variable|Variables|"
    r"Hypothesis|Hypotheses|Section|Module|Let)\b", re.MULTILINE)

# Binder binding sites:  forall x   forall (x : T)   (x : T)   {x : T}
#                        fun x      fun (x : T)    let x :=
BINDER_RES = [
    re.compile(r"\bforall\s+\(?([A-Za-z_'][A-Za-z0-9_']*)"),
    re.compile(r"[(\{]\s*([A-Za-z_'][A-Za-z0-9_']*)\s*:"),
    re.compile(r"\bfun\s+\(?([A-Za-z_'][A-Za-z0-9_']*)"),
    re.compile(r"\blet\s+([A-Za-z_'][A-Za-z0-9_']*)\s*:="),
]

# Record/class field or constructor declaration positions whose name would
# shadow a tracked identifier:  "{ S : T;" field lists, "| S : T" constructors.
FIELD_DECL_RES = [
    re.compile(r"[(\{]\s*([A-Za-z_'][A-Za-z0-9_']*)\s*:"),
    re.compile(r"\|\s*([A-Za-z_'][A-Za-z0-9_']*)\s*:"),
]


def strip_comments_strings(text):
    """State-machine comment/string stripper; stripped bytes become spaces so
    that line and column coordinates of surviving text stay exact."""
    out = []
    i, n = 0, len(text)
    depth = 0
    while i < n:
        c = text[i]
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1
                out.append("  ")
                i += 2
                continue
            if text.startswith("*)", i):
                depth -= 1
                out.append("  ")
                i += 2
                continue
            out.append(c if c == "\n" else " ")
            i += 1
            continue
        if text.startswith("(*", i):
            depth = 1
            out.append("  ")
            i += 2
            continue
        if c == '"':
            out.append(" ")
            i += 1
            while i < n and text[i] != '"':
                out.append(text[i] if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append(" ")
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def decl_spans(clean):
    """Spans of top-level declarations: [(start_offset, end_offset)].  A span
    runs from one top-level vernacular keyword to the next."""
    starts = []
    for m in DECL_START_RE.finditer(clean):
        starts.append(m.start())
    spans = []
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(clean)
        spans.append((s, e))
    return spans


def collect_binders(clean, spans):
    """All binder binding sites as (name_offset, name, scope_start, scope_end).
    Scope = enclosing declaration span (span_of of the binder site)."""
    binders = []
    for s, e in spans:
        seg = clean[s:e]
        for pat in BINDER_RES:
            for m in pat.finditer(seg):
                binders.append((s + m.start(1), m.group(1), s, e))
    return binders


def scan_text(text, ids, name="<text>"):
    """Token-level census on an in-memory source text (see scan_file)."""
    clean = strip_comments_strings(text)
    lines = clean.split("\n")

    def line_col(offset):
        ln = clean.count("\n", 0, offset)
        col = offset - (clean.rfind("\n", 0, offset) + 1) + 1
        return ln + 1, col

    spans = decl_spans(clean)
    binders = collect_binders(clean, spans)
    binder_by_name = {}
    for off, nm, s, e in binders:
        binder_by_name.setdefault(nm, []).append((off, s, e))

    # Shadow sources: declaration positions whose name equals a tracked id.
    shadow_sources = []
    seen_src = set()
    for pat in FIELD_DECL_RES:
        for m in pat.finditer(clean):
            nm = m.group(1)
            if nm in ids and nm not in seen_src:
                ln, col = line_col(m.start(1))
                ctx = clean[max(0, m.start(1) - 60):m.start(1)].lower()
                kind = ("record/class field" if ("record" in ctx or "class" in ctx)
                        else "declaration")
                shadow_sources.append(dict(line=ln, col=col, name=nm, kind=kind))
                seen_src.add(nm)

    stations = []
    context = dict((i, dict(qualified=0, binder_bound=0, binding_site=0,
                            shadow_hazard=0, unqualified_global=0)) for i in ids)
    shadow_by_name = set(s["name"] for s in shadow_sources)

    for m in TOKEN_RE.finditer(clean):
        tok = m.group(0)
        if "." in tok:
            # qualified dotted form (e.g. Datatypes.S) — counted, never a station
            last = tok.split(".")[-1]
            if last in ids:
                context[last]["qualified"] += 1
            continue
        if tok not in ids:
            continue
        off = m.start()
        ln, col = line_col(off)
        line_text = lines[ln - 1]

        # binding site itself (binder declaration, not a reference)
        is_binding = any(boff <= off < boff + len(bnm)
                         for boff, bnm, _s, _e in binders)
        if is_binding:
            context[tok]["binding_site"] += 1
            continue

        # locally re-bound within the enclosing declaration?
        bound = any(s <= off < e for _off, s, e in binder_by_name.get(tok, ()))
        if bound:
            context[tok]["binder_bound"] += 1
            continue

        # field/constructor declaration position (name being *declared*)
        if any(d["line"] == ln and abs(d["col"] - col) < 2 for d in shadow_sources):
            continue

        if shadow_by_name:
            cls, grade = "shadow-hazard", 1
            context[tok]["shadow_hazard"] += 1
        else:
            cls, grade = "unqualified-global", 2
            context[tok]["unqualified_global"] += 1
        # W5 mixed-line masking marker: does this same source line also carry
        # the qualified dotted form (e.g. Datatypes.S)?  Line-level filters
        # that drop lines containing the qualified form would lose this
        # station — the exact historic blind spot this scanner closes.
        mixed_line = bool(re.search(
            r"[A-Za-z_'][A-Za-z0-9_']*\.%s\b" % re.escape(tok), line_text))
        stations.append(dict(line=ln, col=col, token=tok, cls=cls, grade=grade,
                             mixed_line=mixed_line,
                             context=line_text.strip()[:120]))

    stations.sort(key=lambda d: (d["line"], d["col"]))
    return dict(file=name, md5=None, stations=stations,
                context=context, shadow_sources=shadow_sources,
                tracked_ids=list(ids),
                station_count=len(stations))


def scan_file(fp, ids):
    try:
        raw = io.open(fp, "r", encoding="utf-8", errors="replace").read()
    except OSError as e:
        return dict(file=fp, error=str(e), stations=[], context={})
    res = scan_text(raw, ids, name=os.path.basename(fp))
    res["md5"] = md5_of(fp)
    return res


def md5_of(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(
        description="Token-level qualified-identifier census for .v sources.")
    ap.add_argument("--file", required=True, help="input .v source")
    ap.add_argument("--json", help="write census report JSON here")
    ap.add_argument("--ids", default=",".join(DEFAULT_IDS),
                    help="comma-separated bare identifiers to track "
                         "(default: %s)" % ",".join(DEFAULT_IDS))
    ap.add_argument("--text", action="store_true", help="print station list")
    args = ap.parse_args()

    if not os.path.exists(args.file):
        print("FILE-MISSING:", args.file)
        sys.exit(9)

    ids = tuple(t.strip() for t in args.ids.split(",") if t.strip())
    res = scan_file(args.file, ids)
    res["md5"] = md5_of(args.file)

    print("file: %s" % res["file"])
    print("md5: %s" % res["md5"])
    print("tracked ids: %s" % ",".join(res["tracked_ids"]))
    print("shadow sources: %s" % res["shadow_sources"])
    print("context: %s" % json.dumps(res["context"], sort_keys=True))
    print("station_count: %d  (census reports; classification is advisory)"
          % res["station_count"])
    if args.text:
        for st in res["stations"]:
            print("  L%d C%d %s %s grade=%d mixed_line=%s | %s"
                  % (st["line"], st["col"], st["token"], st["cls"],
                     st["grade"], st["mixed_line"], st["context"]))
    if args.json:
        with io.open(args.json, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
        print("census json -> %s" % args.json)
    sys.exit(0)


if __name__ == "__main__":
    main()
