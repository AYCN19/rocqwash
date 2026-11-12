# -*- coding: utf-8 -*-
"""cure_applier.py — applier for the consumer-cure canonical pack (cure_pack.json).

    Purpose.  Applies the deterministic rewrite patterns of cure_pack.json to a Rocq/Coq source
      file; dry run by default (the file is written only under --apply).  The pack's
      consumer-position cures — bridge wraps, goal-opening bridges, opaque-reflexivity replacement,
      qualified successor references, NatLe supply bridges, statement-face downshifts, import-shadow
      qualification, lineage adaptation forms, extraction-defect cures, connective qualification —
      are canonical, idempotent rewrites: a second application changes nothing, and every --apply
      asserts idempotence mechanically (fail-loud).

    Interface.  python3 wash/cure_applier.py --file f.v [--pack cure_pack.json] [--only id1,id2]
      [--json out.json] [--apply] | --selftest.  stdout report per pattern (matches, engine); --json
      report {file, mode, md5_before, md5_after, report{pattern_id: {matches, engine}},
      idempotence_ok}.  Patterns may declare exclusive_group: two selected patterns of one group both
      matching is a variant-choice conflict and fails loud — the caller picks one variant via --only.
      Engines: line-regex, proof-first-tactic, token-station, face-regex (face/proof-scoped triggers
      with per-face token guards), line-insert, station-report (report-only advisory stations, never
      rewritten, excluded from the idempotence residual); routed as `cure` in cw.sh.

    Dependencies.  Python 3 standard library only; scan/scan_v4_token.py (sys.path injection, same repository) for the token-station engine; the pattern pack is data next to this script.

    Evidence.  --selftest in-memory vector groups over the shipped pack: every canonical pattern
      fires, skips guarded positions and is idempotent as specified, the exclusive-group conflict
      fails loud, whole-pack second passes report zero matches; tests/test_cure_pack.py reruns them.

    Exit-codes.  0 = ran (dry run, or applied with idempotence verified); 1 = idempotence assertion
      failed (fail-loud, file not written); 2 = usage; 4 = exclusive-group conflict (two variants of
      one group matched — pick one via --only); 5 = unknown pattern id; 9 = file or pack missing."""
import argparse, hashlib, io, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir, "scan"))
from scan_v4_token import scan_text  # token-station engine (cure4)

DECL_FACE_RE = re.compile(
    r"(?m)^[ \t]*(?:#\[[^\]]*\][ \t]*\r?\n?[ \t]*|(?:Local|Global|Export|Declare)[ \t]+)*"
    r"(Lemma|Theorem|Definition|Corollary|Fixpoint|Proposition|Instance)[ \t]+"
    r"[A-Za-z_'][A-Za-z0-9_']*[^\n]*")
PROOF_RE = re.compile(r"(?m)^[ \t]*Proof\b")


def statement_faces(text):
    """[(face_text, proof_region, proof_start_offset, region_end)] —
    face = declaration keyword through the line before Proof (the statement
    face, where the carrier names live); proof region = Proof line through
    the next declaration keyword (exclusive)."""
    decls = [(m.start(), m.end()) for m in DECL_FACE_RE.finditer(text)]
    out = []
    for k, (s, e) in enumerate(decls):
        nxt = decls[k + 1][0] if k + 1 < len(decls) else len(text)
        pm = PROOF_RE.search(text, e, nxt)
        face = text[s:pm.start()] if pm else text[s:nxt]
        body = text[pm.start():nxt] if pm else ""
        out.append((face, body, s if pm else e, nxt))
    return out


def apply_line_regex(text, pat, fid):
    trig = re.compile(pat["trigger_regex"])
    ctx = pat.get("context", "")
    faces = statement_faces(text) if ("statement face" in ctx) else None
    matches = []
    for m in trig.finditer(text):
        if faces is not None:
            rel = None
            for face, _body, ps, pe in faces:
                if ps <= m.start() < pe:
                    rel = face
                    break
            if rel is None:
                continue
            gate = "QeqT" if "QeqT" in ctx else ("NatLe" if "NatLe" in ctx else None)
            if gate and gate not in rel:
                continue
        # cure5 idempotence guard: never wrap an already-wrapped exact
        if fid == "cure5_natle_drop_bridge" and "NatLe_drop" in text[m.start():m.end() + 40]:
            continue
        matches.append(m)
    out = text
    if matches:
        out = []
        last = 0
        for m in matches:
            out.append(text[last:m.start()])
            out.append(m.expand(pat["template"]))
            last = m.end()
        out.append(text[last:])
        out = "".join(out)
    return out, len(matches)


def apply_proof_first_tactic(text, pat, fid):
    """cure2 engine: prefix apply qeq_imp_qeqT to the first ==-face closing
    tactic inside proofs of QeqT-face statements."""
    trig = re.compile(pat["trigger_regex"])
    out_lines = text.split("\n")
    faces = statement_faces(text)
    # map: line index -> (face, proof region)
    n = len(out_lines)
    offs = [0]
    for l in out_lines:
        offs.append(offs[-1] + len(l) + 1)
    line_face = [None] * n
    for face, body, ps, pe in faces:
        for i in range(n):
            if offs[i] >= ps and offs[i] < pe:
                line_face[i] = (face, body)
    changed = 0
    for i in range(n):
        lf = line_face[i]
        if lf is None or "QeqT" not in lf[0]:
            continue
        m = trig.match(out_lines[i])
        if m and "apply qeq_imp_qeqT" not in out_lines[i]:
            out_lines[i] = m.expand(pat["template"])
            changed += 1
    return "\n".join(out_lines), changed


def apply_token_station(text, pat, fid, ids=("S",)):
    """cure4 engine: qualify bare successor references at census stations."""
    res = scan_text(text, ids)
    if not res["stations"]:
        return text, 0
    lines = text.split("\n")
    edits = []
    for st in res["stations"]:
        ln, col = st["line"], st["col"]
        l = lines[ln - 1]
        if l[col - 1:col - 1 + len(st["token"])] != st["token"]:
            continue  # coordinate guard: never rewrite a drifted token
        edits.append((ln, col, st["token"]))
    for ln, col, tok in sorted(edits, reverse=True):
        l = lines[ln - 1]
        lines[ln - 1] = l[:col - 1] + "Datatypes." + l[col - 1:]
    return "\n".join(lines), len(edits)


ENGINES = {
    "line-regex": apply_line_regex,
    "proof-first-tactic": apply_proof_first_tactic,
    "token-station": apply_token_station,
}


# ---------------------------------------------------------------------------
# v31: face-scoped regex engine (cure_pack v1.1 patterns cure6..cure14).
# ---------------------------------------------------------------------------

class ExclusiveGroupConflict(Exception):
    """Two selected patterns of one exclusive_group both produced matches —
    the pack carries alternative cures for one red family and the caller
    must choose a variant (--only).  Never applied silently."""

    def __init__(self, groups):
        self.groups = groups
        super(ExclusiveGroupConflict, self).__init__(
            "exclusive-group conflict: %s" % groups)


def _skip_comment_string(text, i):
    """At a code position: if text[i:] opens a nested comment or string, return
    the offset just past it; else None.  Comment/string aware period scan."""
    if text.startswith("(*", i):
        depth = 0
        while i < len(text):
            if text.startswith("(*", i):
                depth += 1
                i += 2
            elif text.startswith("*)", i):
                depth -= 1
                i += 2
                if depth == 0:
                    return i
            else:
                i += 1
        return len(text)
    if text.startswith('"', i):
        i += 1
        while i < len(text):
            if text[i] == "\\":
                i += 2
            elif text[i] == '"':
                return i + 1
            else:
                i += 1
        return len(text)
    return None


def _statement_period(text, start, limit):
    """Offset of the first depth-0 statement terminator '.' (followed by
    whitespace/EOF), skipping nested comments and string literals — the
    deterministic end of a Proof-less declaration's statement face."""
    depth = 0
    i = start
    while i < limit:
        sk = _skip_comment_string(text, i)
        if sk is not None:
            i = sk
            continue
        c = text[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth = max(0, depth - 1)
        elif c == "." and depth == 0:
            if i + 1 >= limit or text[i + 1] in " \t\r\n":
                return i
        i += 1
    return None


def _face_regions(text):
    """[(decl_start, face_end, proof_span, decl_line)] — statement face spans
    declaration keyword through the Proof line (or, for Proof-less
    declarations, through the first depth-0 statement terminator); proof_span
    = (start, end) when a Proof line exists, else None."""
    decls = [(m.start(), m.end()) for m in DECL_FACE_RE.finditer(text)]
    out = []
    for k, (s, e) in enumerate(decls):
        nxt = decls[k + 1][0] if k + 1 < len(decls) else len(text)
        pm = PROOF_RE.search(text, e, nxt)
        if pm:
            face_end = pm.start()
            proof_span = (pm.start(), nxt)
        else:
            p = _statement_period(text, s, nxt)
            face_end = (p + 1) if p is not None else nxt
            proof_span = None
        decl_line = text[s:text.find("\n", s, face_end)
                         if text.find("\n", s, face_end) != -1 else face_end]
        out.append((s, face_end, proof_span, decl_line))
    return out


def _paren_term(t):
    """Single-token terms stay bare; multi-token applications get parens
    (mirrors the canonical patched forms, e.g. NatLe (gnPrf f pf) k)."""
    return "(%s)" % t if " " in t else t


def _fn_qle_notation(m, pat):
    """`X <= Y%Q` -> `QleT' (X) Y%Q`: carrier predicate application with the
    scope mark retained on the literal RHS operand."""
    target = pat.get("target", "QleT'")
    lhs = m.group("lhs").strip()
    rhs = m.group("rhs").strip()
    return "%s %s %s%%Q" % (target, _paren_term(lhs), _paren_term(rhs))


def _fn_natle_premise_lift(m, pat):
    """`(X <= Y)%nat` -> `S01_BaseRing.NatLe (X) Y`: premise lifted to the
    Set-carrier order (scope mark dropped; qualified name per REQNOEXPORT)."""
    qual = pat.get("qualified_name", "S01_BaseRing.NatLe")
    lhs = m.group("lhs").strip()
    rhs = m.group("rhs").strip()
    return "%s %s %s" % (qual, _paren_term(lhs), _paren_term(rhs))


def _fn_ifq_conn_qualify(m, pat):
    """v39: bare interface-projection connective -> the @-qualified
    S01_BaseRing projection applied to the section context variable.
    The replacement branches on WHICH connective matched (token_targets
    map keyed by the trigger's named group `conn`); the RI0 context name
    is part of each target and is pinned by the pattern's file_include
    gate (the exact `Context {RI0 : RealInterfaceEnhanced}` face)."""
    targets = pat["token_targets"]
    return targets[m.group("conn")]


TEMPLATE_FNS = {
    "qle_notation_downshift": _fn_qle_notation,
    "natle_premise_lift": _fn_natle_premise_lift,
    "ifq_conn_qualify": _fn_ifq_conn_qualify,
}


def _expand_piece(pat, m):
    fn = pat.get("template_fn")
    if fn:
        return TEMPLATE_FNS[fn](m, pat)
    return m.expand(pat["template"])


def _sub_before_marker(trig, repl, seg, marker):
    """v32: per-match binding-right guard.  A match whose start lies at or
    after the first occurrence of `marker` (e.g. ":=") on its enclosing line
    sits on the right side of a binding and is skipped; matches before the
    marker survive.  Deterministic; used by cure32_A to keep type-annotation
    stations (``: Class carrier :=``) while excluding :=-binding right sides
    on the same line."""
    out = []
    last = 0
    n = 0
    for m in trig.finditer(seg):
        line_start = seg.rfind("\n", 0, m.start()) + 1
        line_end = seg.find("\n", m.start())
        if line_end == -1:
            line_end = len(seg)
        cut = seg[line_start:line_end].find(marker)
        if cut != -1 and (m.start() - line_start) >= cut:
            continue
        out.append(seg[last:m.start()])
        out.append(repl(m))
        last = m.end()
        n += 1
    out.append(seg[last:])
    return "".join(out), n


def apply_face_regex(text, pat, fid):
    """face/proof-scoped trigger with per-face token guards.

    Pattern fields beyond trigger_regex/template:
      scope         "face" (default) rewrites inside statement faces only;
                    "proof" rewrites inside Proof regions only;
                    "all" (v32) rewrites inside both.
      face_include  list of regexes; every one must match the statement face.
      face_exclude  list of regexes; any match skips the face (guards against
                    rewriting bridge definitions and already-cured faces).
      decl_exclude  list of regexes tested against the declaration line
                    (e.g. skip Definition/Fixpoint faces where binder-shadow
                    risk is structural — the station scanner owns those).
      guard         "intros-tail": in proof scope, a match fires only when its
                    last group names the tail identifier of an `intros ...`
                    tactic in the same proof region (the hypothesis actually
                    introduced from the lifted premise) — other exact-call
                    stations with constant tails are left untouched.
      file_include  regex that must match the whole file once (precondition,
                    e.g. the shadowing Import is present).
      token_map     {bare_token: qualified_form} — builds the trigger from the
                    map keys (longest-first) and rewrites via the map.
      target        carrier predicate name used by template_fn.
      qualified_name  fully-qualified carrier name used by template_fn.
      binding_right_exclude  (v32) marker string (e.g. ":="): a match at or
                    after the first marker occurrence on its enclosing line
                    is on a binding right side and is skipped (per-match, not
                    per-line — type annotations on the same line survive).
    """
    fi = pat.get("file_include")
    if fi and not re.search(fi, text):
        return text, 0
    if "token_map" in pat:
        toks = sorted(pat["token_map"], key=len, reverse=True)
        trig = re.compile(r"(?<![A-Za-z0-9_.'])(%s)(?![A-Za-z0-9_'])"
                          % "|".join(re.escape(t) for t in toks))
        tmap = pat["token_map"]
        repl = lambda m: tmap[m.group(1)]
    else:
        trig = re.compile(pat["trigger_regex"])
        repl = lambda m: _expand_piece(pat, m)
    incl = [re.compile(rx) for rx in pat.get("face_include", [])]
    excl = [re.compile(rx) for rx in pat.get("face_exclude", [])]
    dexcl = [re.compile(rx) for rx in pat.get("decl_exclude", [])]
    guard = pat.get("guard")
    scope = pat.get("scope", "face")
    bre = pat.get("binding_right_exclude")
    pieces = []
    total = 0
    for s, face_end, proof_span, decl_line in _face_regions(text):
        if any(rx.search(decl_line) for rx in dexcl):
            continue
        face = text[s:face_end]
        if any(not rx.search(face) for rx in incl):
            continue
        if any(rx.search(face) for rx in excl):
            continue
        if scope == "proof":
            if proof_span is None:
                continue
            spans = [(proof_span[0], text[proof_span[0]:proof_span[1]])]
        elif scope == "all":
            spans = [(s, face)]
            if proof_span is not None:
                spans.append((proof_span[0],
                              text[proof_span[0]:proof_span[1]]))
        else:
            spans = [(s, face)]
        for seg_off, seg in spans:
            if guard == "intros-tail":
                intros_tails = set()
                for im in re.finditer(r"(?m)^[ \t]*intros\b[ \t]+([^\n.]*)",
                                      seg):
                    toks = re.findall(r"[A-Za-z_'][A-Za-z0-9_']*", im.group(1))
                    if toks:
                        intros_tails.add(toks[-1])
                fires = []
                for m in trig.finditer(seg):
                    groups = m.groups()
                    tail = groups[-1] if groups else None
                    if tail is None or tail not in intros_tails:
                        continue  # guarded out: not an introduced hypothesis
                    fires.append(m)
                n = len(fires)
                if fires:
                    parts = []
                    last = 0
                    for m in fires:
                        parts.append(seg[last:m.start()])
                        parts.append(repl(m))
                        last = m.end()
                    parts.append(seg[last:])
                    new_seg = "".join(parts)
                else:
                    new_seg = seg
            elif bre is not None:
                new_seg, n = _sub_before_marker(trig, repl, seg, bre)
            else:
                new_seg, n = trig.subn(repl, seg)
            if n:
                pieces.append((seg_off, seg_off + len(seg), new_seg))
                total += n
    if not pieces:
        return text, 0
    out = text
    for seg_off, seg_end, new_seg in sorted(pieces, reverse=True):
        out = out[:seg_off] + new_seg + out[seg_end:]
    return out, total


ENGINES["face-regex"] = apply_face_regex


# ---------------------------------------------------------------------------
# v32: S07-lineage adaptation engines (cure_pack v1.2 patterns cure32_*).
# ---------------------------------------------------------------------------

def apply_line_insert(text, pat, fid):
    """Insertion engine (v32): insert one verbatim line after the last
    top-level Require/Import line — the canonical anchor of the S07
    notation-rebind cure (``Notation R := Real.`` after the world imports;
    UpReqSumD.v L58 precedent).  Fields:
      insert_line         the exact line to insert.
      insert_after        anchor policy, only "last-import" is defined: after
                          the last line matching ``^[ \\t]*(From x )?Require|
                          Import``; a file with no such line inserts at the
                          top (first line).
      file_include        regex that must match the whole file once (e.g. the
                          interface Class name — insertion is scoped to the
                          lineage that needs the rebind).
      require_token_regex regex that must occur somewhere (e.g. a bare ``R``
                          use position — no rebind without a consumer).
    Idempotent: when insert_line is already present the count is 0.
    """
    fi = pat.get("file_include")
    if fi and not re.search(fi, text):
        return text, 0
    line = pat["insert_line"]
    if re.search(r"(?m)^[ \t]*%s[ \t]*\r?$" % re.escape(line), text):
        return text, 0
    req = pat.get("require_token_regex")
    if req and not re.search(req, text):
        return text, 0
    anchor_re = re.compile(
        r"(?m)^[ \t]*(?:From[ \t]+\S+[ \t]+)?(?:Require|Import)\b")
    last_end = None
    for m in anchor_re.finditer(text):
        last_end = m.end()
    lines = text.split("\n")
    if last_end is None:
        lines.insert(0, line)
    else:
        lines.insert(text.count("\n", 0, last_end) + 1, line)
    return "\n".join(lines), 1


ENGINES["line-insert"] = apply_line_insert


def apply_station_report(text, pat, fid):
    """Report-only station scanner (v32).  Never rewrites: the text comes
    back unchanged and the station count surfaces in the dry-run report —
    the positions needing the manual binder surgery of the S07 lineage
    (argumented Class binders like ``(RIS : Class carrier)`` / ``{RIS : Class
    carrier}``, whose full removal touches intros lines and call sites and
    is therefore NOT a safe single-regex rewrite).  After the surgery the
    count must return to zero: that is the count assertion.  Fields:
      station_regex  the station trigger (scanned over statement faces, or
                     proof regions with "scope": "proof"/"all").
      file_include   regex that must match the whole file once.
    Patterns with "mode": "report" never contribute to the --apply
    idempotence residual (advisory stations, not cures).
    """
    fi = pat.get("file_include")
    if fi and not re.search(fi, text):
        return text, 0
    rx = re.compile(pat["station_regex"])
    scope = pat.get("scope", "face")
    n = 0
    for s, face_end, proof_span, _decl_line in _face_regions(text):
        if scope in ("face", "all"):
            n += len(rx.findall(text[s:face_end]))
        if scope in ("proof", "all") and proof_span is not None:
            n += len(rx.findall(text[proof_span[0]:proof_span[1]]))
    return text, n


ENGINES["station-report"] = apply_station_report


def run_pack(text, patterns):
    # variant-conflict pre-pass: exclusive groups are judged against the
    # ORIGINAL text — sequential application could mask a variant (e.g. the
    # variant-(a) deletion removing the Import precondition of variant (b)).
    # Both variants matching the original file is a caller decision (rc 4),
    # never a silent sequential resolution.
    groups = {}
    for pat in patterns:
        g = pat.get("exclusive_group")
        if not g:
            continue
        eng = ENGINES[pat["engine"]]
        _t, n = eng(text, pat, pat["id"])
        if n:
            groups.setdefault(g, []).append(pat["id"])
    conflicts = dict((g, ids) for g, ids in groups.items() if len(ids) > 1)
    if conflicts:
        raise ExclusiveGroupConflict(conflicts)
    report = {}
    for pat in patterns:
        eng = ENGINES[pat["engine"]]
        new_text, n = eng(text, pat, pat["id"])
        report[pat["id"]] = dict(matches=n, engine=pat["engine"])
        text = new_text
    return text, report


def apply_one(text, pat):
    """Single-pattern application: (new_text, match_count)."""
    eng = ENGINES[pat["engine"]]
    return eng(text, pat, pat["id"])


def count_all(text, patterns):
    """Dry-run pass: recompute trigger match counts without rewriting."""
    counts = {}
    for pat in patterns:
        eng = ENGINES[pat["engine"]]
        _t, n = eng(text, pat, pat["id"])
        counts[pat["id"]] = n
    return counts


def md5s(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def selftest():
    ok = True
    pack = json.load(io.open(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "cure_pack.json"),
        encoding="utf-8"))
    pats = dict((p["id"], p) for p in pack["patterns"])

    # cure1: wrap / already-wrapped skip / in-H form
    p1 = pats["cure1_qeqT_imp_qeq_rewrite_wrap"]
    t1, n1 = apply_one("rewrite (g_step k).", p1)
    e1 = "rewrite (qeqT_imp_qeq _ _ (g_step k))."
    c1 = n1 == 1 and t1 == e1
    t1b, n1b = apply_one(e1, p1)
    c1b = n1b == 0 and t1b == e1
    t1c, n1c = apply_one("rewrite (g_step k) in Hx.", p1)
    c1c = n1c == 1 and t1c == "rewrite (qeqT_imp_qeq _ _ (g_step k)) in Hx."
    print("cure1 wrap/skip/in-H:", c1, c1b, c1c)
    ok = ok and c1 and c1b and c1c

    # cure2: QeqT statement gate / non-QeqT no-fire / already-doored no-fire
    p2 = pats["cure2_qeq_imp_qeqT_goal_open"]
    q = ("Lemma s : QeqT a b.\nProof.\n  intro.\n  reflexivity.\nQed.\n"
         "Lemma t : nat.\nProof.\n  reflexivity.\nQed.\n")
    t2, n2 = apply_one(q, p2)
    c2 = (n2 == 1
          and "apply qeq_imp_qeqT. reflexivity." in t2
          and t2.split("Qed.")[2].count("apply qeq_imp_qeqT") == 0)
    t2b, n2b = apply_one(t2, p2)
    c2b = n2b == 0
    print("cure2 gate/idempotent:", c2, c2b)
    ok = ok and c2 and c2b

    # cure3: door-prefixed reflexivity -> Qeq_refl; plain reflexivity untouched
    p3 = pats["cure3_qeq_refl_replace_reflexivity"]
    t3, n3 = apply_one("apply qeq_imp_qeqT. reflexivity.", p3)
    c3 = n3 == 1 and t3 == "apply qeq_imp_qeqT. apply Qeq_refl."
    t3b, n3b = apply_one("  reflexivity.", p3)
    c3b = n3b == 0
    print("cure3 cure/no-fire:", c3, c3b)
    ok = ok and c3 and c3b

    # cure4: station cure / binder-bound untouched / idempotent
    p4 = pats["cure4_datatypes_s_qualify"]
    t4_in = ("Record Sp := MkSp { S : Set; sz : nat }.\n"
             "Definition f (p : Sp) (n : nat) := sz p + Datatypes.S n + S n.\n"
             "Definition g (S : Set) (x : S) := x.\n")
    t4, n4 = apply_one(t4_in, p4)
    c4 = (n4 == 1
          and "+ Datatypes.S n + Datatypes.S n." in t4
          and "Definition g (S : Set) (x : S) := x." in t4)
    t4b, n4b = apply_one(t4, p4)
    c4b = n4b == 0 and t4b == t4
    print("cure4 station/binder/idempotent:", c4, c4b)
    ok = ok and c4 and c4b

    # cure5: NatLe statement gate / already-wrapped skip / non-NatLe no-fire
    p5 = pats["cure5_natle_drop_bridge"]
    q5 = ("Lemma h : forall n m, NatLe n m -> NatLe (g n) (g m).\n"
          "Proof.\n  intros n m H.\n  exact H.\nQed.\n"
          "Lemma k : forall n, n <= n.\nProof.\n  intros. apply Nat.le_refl.\nQed.\n")
    t5, n5 = apply_one(q5, p5)
    c5 = n5 == 1 and "exact (NatLe_drop _ _ H)." in t5
    t5b, n5b = apply_one(t5, p5)
    c5b = n5b == 0
    print("cure5 gate/idempotent:", c5, c5b)
    ok = ok and c5 and c5b

    # whole-pack idempotence on a combined sample
    sample = (q + "Lemma w : QeqT (g 3) (g 3).\nProof.\n  intros.\n"
              "  apply qeq_imp_qeqT. reflexivity.\nQed.\n" + q5)
    p1, r1 = run_pack(sample, pack["patterns"])
    p2, r2 = run_pack(p1, pack["patterns"])
    c6 = (p2 == p1 and all(v["matches"] == 0 for v in r2.values()))
    print("whole-pack idempotence:", c6, {k: v["matches"] for k, v in r2.items()})
    ok = ok and c6

    # ---- v31 vectors (cure6..cure14) ----
    v = dict((p["id"], p) for p in pack["patterns"]
             if int(p["id"].split("_")[0][4:]) >= 6)

    # cure6/cure8: bare Qle/Qlt token downshift; binder decls, binder uses in
    # Definition bodies (decl_exclude), declared names, trailing comments and
    # already-cured faces are all guarded.
    p6 = v["cure6_qle_token_downshift"]
    f6 = ("Theorem t1 : forall a b : Q, Qle a b -> Qle (f a) (f b).\n"
          "Proof. intros. apply Qle_refl. Qed.\n"
          "Definition bnd (Qle : nat) (n : nat) := n + Qle.\n"
          "Theorem Qle_pair : forall x : Q, Qle x x.\n"
          "(* comment mentions Qle freely *)\n"
          "Definition Qle := 3.\n")
    t6, n6 = apply_one(f6, p6)
    c7 = (n6 == 3
          and "QleT' a b -> QleT' (f a) (f b)" in t6
          and "QleT' x x." in t6
          and "Definition bnd (Qle : nat) (n : nat) := n + Qle." in t6
          and "Definition Qle := 3." in t6
          and "comment mentions Qle freely" in t6)
    t6b, n6b = apply_one(t6, p6)
    c7b = n6b == 0
    print("cure6 face downshift/guards/idempotent:", c7, c7b)
    ok = ok and c7 and c7b

    p8 = v["cure8_qlt_token_downshift"]
    t8, n8 = apply_one("Theorem t2 : forall a b : Q, Qlt a b -> Qlt a a.\n"
                       "Proof. intros. apply Qlt_refl. Qed.\n"
                       "Definition bnd2 (Qlt : nat) := Qlt.\n", p8)
    c8 = (n8 == 2 and "QltT a b -> QltT a a." in t8
          and "Definition bnd2 (Qlt : nat) := Qlt." in t8)
    t8b, n8b = apply_one(t8, p8)
    c8b = n8b == 0
    print("cure8 Qlt downshift/guards/idempotent:", c8, c8b)
    ok = ok and c8 and c8b

    # cure7: scoped notation downshift (premise arrow must not be swallowed;
    # unmarked comparison stays uncovered — station-scanner territory)
    p7 = v["cure7_qle_notation_downshift"]
    f7 = ("Theorem t3 : forall x : Q, In x [0; 0; 2] -> Qabs x <= 2%Q.\n"
          "Proof. intros. apply xq_Qle_bool_le. vm_compute. reflexivity. Qed.\n"
          "Theorem t4 : forall a y : Q, In y (P0 [a]) -> Qabs y <= Qabs a.\n"
          "Proof. intros. apply Qle_refl. Qed.\n")
    t7, n7 = apply_one(f7, p7)
    c9 = (n7 == 1
          and "QleT' (Qabs x) 2%Q." in t7
          and "Qabs y <= Qabs a." in t7)
    t7b, n7b = apply_one(t7, p7)
    c9b = n7b == 0
    print("cure7 notation downshift/unmarked-skip/idempotent:", c9, c9b)
    ok = ok and c9 and c9b

    # cure9: Qlt scoped-notation variant
    p9 = v["cure9_qlt_notation_downshift"]
    t9, n9 = apply_one("Theorem t5 : forall x : Q, P x -> Qabs x < 1%Q.\n"
                       "Proof. intros. apply xq_Qlt_bool_lt. Qed.\n", p9)
    c10 = n9 == 1 and "QltT (Qabs x) 1%Q." in t9
    t9b, n9b = apply_one(t9, p9)
    c10b = n9b == 0
    print("cure9 Qlt notation downshift/idempotent:", c10, c10b)
    ok = ok and c10 and c10b

    # cure10: refl bridge opener inside proofs of already-downshifted faces
    p10 = v["cure10_qle_refl_bridge_open"]
    f10 = ("Theorem t6 : forall a b : Q, QleT' a b -> QleT' (f a) (f b).\n"
           "Proof.\n  intros a b H.\n  apply Qle_refl.\nQed.\n"
           "Theorem t7 : forall n : nat, n <= n.\n"
           "Proof. intros. apply Qle_refl. Qed.\n")
    t10, n10 = apply_one(f10, p10)
    c11 = (n10 == 1
           and "apply Qle_to_QleT'. apply Qle_refl." in t10
           and t10.count("apply Qle_refl.") == 2)
    t10b, n10b = apply_one(t10, p10)
    c11b = n10b == 0
    print("cure10 refl opener/gate/idempotent:", c11, c11b)
    ok = ok and c11 and c11b

    # cure11/cure12: import-shadow pair, mutually exclusive variants
    p11 = v["cure11_import_shadow_delete"]
    shadow = ("Require Import S02_CauchyComplete.\n"
              "Import RealInterfaceEnhancedMod.\n"
              "Theorem r1 : forall u : Real, req u (opp u).\n"
              "Proof. intros. apply r0. Qed.\n")
    t11, n11 = apply_one(shadow, p11)
    c12 = n11 == 1 and "Import RealInterfaceEnhancedMod." not in t11 \
        and "Require Import S02_CauchyComplete." in t11
    t11b, n11b = apply_one(t11, p11)
    c12b = n11b == 0
    print("cure11 import delete/idempotent:", c12, c12b)
    ok = ok and c12 and c12b

    p12 = v["cure12_shadow_direct_face_qualify"]
    t12, n12 = apply_one(shadow, p12)
    c13 = (n12 == 2
           and "S02_CauchyComplete.real_eq u (S02_CauchyComplete.real_opp u)."
           in t12
           and "Import RealInterfaceEnhancedMod." in t12)
    t12b, n12b = apply_one(t12, p12)
    c13b = n12b == 0
    # no-import precondition: bare tokens in a non-shadow file are untouched
    plain = ("Theorem r2 : forall u : Real, req u (opp u).\n"
             "Proof. intros. apply r0. Qed.\n")
    t12c, n12c = apply_one(plain, p12)
    c13c = n12c == 0 and t12c == plain
    print("cure12 direct-face qualify/idempotent/no-import guard:", c13, c13b, c13c)
    ok = ok and c13 and c13b and c13c

    # exclusive-group conflict: variant a + variant b in one run -> fail loud
    try:
        run_pack(shadow, [p11, p12])
        c14 = False
    except ExclusiveGroupConflict as e:
        c14 = sorted(e.groups["import-shadow"]) == \
            ["cure11_import_shadow_delete", "cure12_shadow_direct_face_qualify"]
    print("exclusive-group conflict fail-loud:", c14)
    ok = ok and c14

    # cure13/cure14: nat-le premise lift + drop wrap
    p13 = v["cure13_natle_premise_lift"]
    f13 = ("Theorem t8 : forall f pf k,\n"
           "  (gnPrf f pf <= k)%nat -> NatOK f pf k.\n"
           "Proof. intros. apply g0. Qed.\n"
           "Theorem t9 : forall n m : nat, (n <= m)%nat -> n < m.\n"
           "Proof. intros. apply Nat.lt_le_trans. Qed.\n")
    t13, n13 = apply_one(f13, p13)
    c15 = (n13 == 2
           and "S01_BaseRing.NatLe (gnPrf f pf) k -> NatOK f pf k." in t13
           and "S01_BaseRing.NatLe n m -> n < m." in t13)
    t13b, n13b = apply_one(t13, p13)
    c15b = n13b == 0
    print("cure13 premise lift/idempotent:", c15, c15b)
    ok = ok and c15 and c15b

    p14 = v["cure14_natle_drop_wrap"]
    f14 = ("Theorem t10 : forall f pf k,\n"
           "  S01_BaseRing.NatLe (gnPrf f pf) k -> NatOK f pf k.\n"
           "Proof.\n  intros f pf k Hk.\n"
           "  split.\n"
           "  - exact (gnPrf_replay f pf k Hk).\n"
           "  - apply loeb_tid_eq. exact (gnPrf_replay_eq abg_fzz abg_axz).\n"
           "Qed.\n"
           "Theorem t11 : forall x : nat, x = x.\n"
           "Proof. intros. exact (eq_refl x). Qed.\n")
    t14, n14 = apply_one(f14, p14)
    c16 = (n14 == 1
           and "exact (gnPrf_replay f pf k (S01_BaseRing.NatLe_drop _ _ Hk))."
           in t14
           and "exact (gnPrf_replay_eq abg_fzz abg_axz)." in t14
           and "exact (eq_refl x)." in t14)
    t14b, n14b = apply_one(t14, p14)
    c16b = n14b == 0
    print("cure14 drop wrap/intros-tail guard/idempotent:", c16, c16b)
    ok = ok and c16 and c16b

    # v31 whole-pack idempotence on a conflict-free sample
    vsample = f6 + f7 + f13 + f14
    v1, vr1 = run_pack(vsample, pack["patterns"])
    v2, vr2 = run_pack(v1, pack["patterns"])
    c17 = (v2 == v1 and all(x["matches"] == 0 for x in vr2.values()))
    print("v31 whole-pack idempotence:", c17,
          {k: x["matches"] for k, x in vr2.items() if x["matches"]})
    ok = ok and c17

    # ---- v32 vectors (cure32 pack: S07-lineage adaptation forms) ----
    v32 = dict((p["id"], p) for p in pack["patterns"]
               if p["id"].startswith("cure32"))

    # cure32_A: shell drop on annotation + binder; :=-binding right side kept
    pA = v32["cure32_A_param_shell_drop"]
    fA = ("Definition ren : RealInterfaceEnhancedSetoid Real :=\n"
          "  mkRIES.\n"
          "Theorem t : forall (R : Set) {RIS : RealInterfaceEnhancedSetoid R}"
          ", P R.\n"
          "Definition body_right := RealInterfaceEnhancedSetoid Real.\n")
    tA, nA = apply_one(fA, pA)
    c18 = (nA == 2
           and ": RealInterfaceEnhancedSetoid :=" in tA
           and "{RIS : RealInterfaceEnhancedSetoid}," in tA
           and "Definition body_right := RealInterfaceEnhancedSetoid Real."
           in tA)
    tAb, nAb = apply_one(tA, pA)
    c18b = nAb == 0 and tAb == tA
    print("cure32_A shell drop/binding-right guard/idempotent:", c18, c18b)
    ok = ok and c18 and c18b

    # cure32_B: notation line after the last import; idempotent; gated
    pB = v32["cure32_B_notation_rebind"]
    fB = ("Require Import W.\n"
          "Import W2.\n"
          "Definition u : RealInterfaceEnhancedSetoid := mk.\n"
          "Theorem s : P R.\nProof. exact e. Qed.\n")
    tB, nB = apply_one(fB, pB)
    c19 = (nB == 1 and "Import W2.\nNotation R := Real.\nDefinition u :"
           in tB)
    tBb, nBb = apply_one(tB, pB)
    c19b = nBb == 0 and tBb == tB
    tBc, nBc = apply_one("Definition q := R + 1.\n", pB)
    c19c = nBc == 0 and tBc == "Definition q := R + 1.\n"
    print("cure32_B notation rebind/last-import anchor/gated/idempotent:",
          c19, c19b, c19c)
    ok = ok and c19 and c19b and c19c

    # cure32_C(a): @field carrier instance -> bare field, faces and proofs
    pC = v32["cure32_C_atfield_bridge_bare"]
    fC = ("Definition ren : RealInterfaceEnhancedSetoid := mk.\n"
          "Theorem c : lt zero (@Z_align_req Real ren unit) -> P.\n"
          "Proof.\n"
          "  intros H.\n"
          "  exact (mult_positive (@exp_neg Real ren zero) "
          "(@one_pos Real ren)).\n"
          "Qed.\n")
    tC, nC = apply_one(fC, pC)
    c20 = (nC == 3
           and "lt zero (Z_align_req unit) -> P." in tC
           and "exact (mult_positive (exp_neg zero) (one_pos))." in tC)
    tCb, nCb = apply_one(tC, pC)
    c20b = nCb == 0
    print("cure32_C(a) bridge bare/face+proof scope/idempotent:", c20, c20b)
    ok = ok and c20 and c20b

    # cure32_C(b): predicate-face convergence; file gate; mult survives
    pCb = v32["cure32_C_predicate_face_converge"]
    fCb = ("Require Import W.\n"
           "Theorem t2 : RealInterfaceEnhancedSetoid -> req x y.\n"
           "Proof. intros. apply s. Qed.\n"
           "Definition keeper := mult 1 2.\n")
    tCd, nCd = apply_one(fCb, pCb)
    c21 = (nCd == 1 and "real_eq x y." in tCd
           and "Definition keeper := mult 1 2." in tCd)
    tCdb, nCdb = apply_one(tCd, pCb)
    c21b = nCdb == 0
    plainb = "Theorem v : req a b.\nProof. apply r. Qed.\n"
    tCc, nCc = apply_one(plainb, pCb)
    c21c = nCc == 0 and tCc == plainb
    print("cure32_C(b) predicate converge/mult-survives/file gate/idempotent:",
          c21, c21b, c21c)
    ok = ok and c21 and c21b and c21c

    # binder-shell station: report-only (text unchanged, count asserted)
    pS = v32["cure32_station_binder_shell"]
    fS = ("Theorem a : forall (R : Set) {RIS : RealInterfaceEnhancedSetoid R}"
          " (x : R), P x.\n"
          "Proof. intros. apply p. Qed.\n"
          "Definition keeper2 (R : Set) := R.\n")
    tS, nS = apply_one(fS, pS)
    c22 = nS == 1 and tS == fS
    tSb, nSb = apply_one(tA, pS)  # post-cure text: shell gone -> 0 stations
    c22b = nSb == 0 and tSb == tA
    print("cure32 station binder-shell/report-only/residual-zero:", c22, c22b)
    ok = ok and c22 and c22b

    # v32 whole-pack idempotence on a combined S07 sample
    s32 = fA + fB + fC
    w1, wr1 = run_pack(s32, pack["patterns"])
    w2, wr2 = run_pack(w1, pack["patterns"])
    c23 = (w2 == w1 and all(x["matches"] == 0 for x in wr2.values()))
    print("v32 whole-pack idempotence:", c23,
          {k: x["matches"] for k, x in wr2.items() if x["matches"]})
    ok = ok and c23

    # ---- v34 vectors (cure34 pack: E2/E3 extraction-defect families) ----
    v34 = dict((p["id"], p) for p in pack["patterns"]
               if p["id"].startswith("cure34"))

    # cure34 E3: abstract-carrier stations -> shim call; the shim Definition
    # is inserted after the last import; the shim's own body (which keeps the
    # abstract application) is face-excluded on every later pass; idempotent
    pE3u = v34["cure34_E3_use_station_spec"]
    pE3s = v34["cure34_E3_spec_shim"]
    fE3 = ("Require Import Cure34E23World.\n"
           "Definition ufx_nat (n : Real) : Real := gstep Real natIF n.\n"
           "Theorem ufx_gstep_mul : forall n : Real,\n"
           "  gstep Real natIF n = Nat.mul n n.\n"
           "Proof. intro n. reflexivity. Qed.\n")
    tE3, nE3u = apply_one(fE3, pE3u)
    c24 = (nE3u == 2
           and "gstep_spec n = Nat.mul n n." in tE3
           and "gstep_spec n." in tE3)
    tE3b, nE3s = apply_one(tE3, pE3s)
    c24b = (nE3s == 1
            and "Require Import Cure34E23World.\n"
                "Definition gstep_spec (x : Real) : Real := "
                "gstep Real natIF x." in tE3b)
    tE3c, rE3 = run_pack(tE3b, [pE3u, pE3s])
    c24c = (tE3c == tE3b
            and rE3["cure34_E3_use_station_spec"]["matches"] == 0
            and rE3["cure34_E3_spec_shim"]["matches"] == 0)
    print("cure34 E3 station/shim/idempotent:", c24, c24b, c24c)
    ok = ok and c24 and c24b and c24c

    # cure34 E2: the un-annotated field consumption becomes the annotated
    # middleware; downstream arity stations follow; the report-only station
    # counts the pre-form and drops to zero after the cure
    pE2a = v34["cure34_E2_field_annot"]
    pE2r = v34["cure34_E2_use_arity"]
    pE2s = v34["cure34_E2_station_unannot"]
    fE2 = ("Require Import Cure34E23World.\n"
           "Definition unann := wf theW.\n"
           "Definition use_unann (n : nat) : nat := unann nat n.\n")
    tE2, nE2a = apply_one(fE2, pE2a)
    c25 = (nE2a == 1
           and "Definition unann (n : nat) : nat := wf theW nat n." in tE2)
    tE2b, nE2r = apply_one(tE2, pE2r)
    c25b = (nE2r == 1 and ":= unann n." in tE2b)
    tE2c, nE2s = apply_one(fE2, pE2s)
    c25c = (nE2s == 1 and tE2c == fE2)
    tE2d, rE2 = run_pack(tE2b, [pE2a, pE2r, pE2s])
    c25d = (tE2d == tE2b
            and rE2["cure34_E2_field_annot"]["matches"] == 0
            and rE2["cure34_E2_use_arity"]["matches"] == 0
            and rE2["cure34_E2_station_unannot"]["matches"] == 0)
    print("cure34 E2 annot/arity/station/idempotent:", c25, c25b, c25c, c25d)
    ok = ok and c25 and c25b and c25c and c25d

    # v34 whole-pack idempotence on a combined E2+E3 sample
    s34 = fE3 + fE2
    x1, xr1 = run_pack(s34, pack["patterns"])
    x2, xr2 = run_pack(x1, pack["patterns"])
    c26 = (x2 == x1 and all(x["matches"] == 0 for x in xr2.values()))
    print("v34 whole-pack idempotence:", c26,
          {k: x["matches"] for k, x in xr2.items()})
    ok = ok and c26

    # ---- v39 vector (cure39: interface-quantified connective qualification) ----
    v39 = dict((p["id"], p) for p in pack["patterns"]
               if p["id"].startswith("cure39"))

    # fire: five bare connective stations in the RI0-context compat face;
    # the keeper Definition face (decl_exclude), the binder declaration
    # (colon guard), the @-qualified face (lookbehind) and the proof's
    # @-qualified witness call (proof scope out of range) all survive
    # verbatim; second pass zero
    pQ = v39["cure39_ifq_connective_qualify"]
    fQ = ("Require Import S01_BaseRing.\n"
          "Section Q.\n"
          "Context {RI0 : RealInterfaceEnhanced}.\n"
          "Context {DO0 : DecidableOrder RI0}.\n"
          "Theorem compat : forall a b c d : @S01_BaseRing.R RI0,\n"
          "  lt a b -> le c d -> lt (plus a c) (plus b d).\n"
          "Proof. intros. exact (@fa53_lt_plus_compat_lt_le_dec RI0 DO0 "
          "a b c d). Qed.\n"
          "Definition keeper (le : nat) (n : nat) := n + le.\n"
          "Lemma bnd_guard (lt : nat) : True.\n"
          "Proof. exact I. Qed.\n"
          "Theorem qualified_face : @S01_BaseRing.lt RI0 1 2.\n"
          "Proof. apply q. Qed.\n"
          "End Q.\n")
    tQ, nQ = apply_one(fQ, pQ)
    c27 = (nQ == 5
           and "@S01_BaseRing.lt RI0 a b -> @S01_BaseRing.le RI0 c d ->"
               in tQ
           and "@S01_BaseRing.lt RI0 (@S01_BaseRing.plus RI0 a c) "
               "(@S01_BaseRing.plus RI0 b d)." in tQ
           and "Definition keeper (le : nat) (n : nat) := n + le." in tQ
           and "Lemma bnd_guard (lt : nat) : True." in tQ
           and "Theorem qualified_face : @S01_BaseRing.lt RI0 1 2." in tQ
           and "exact (@fa53_lt_plus_compat_lt_le_dec RI0 DO0 a b c d)."
               in tQ)
    tQb, nQb = apply_one(tQ, pQ)
    c27b = nQb == 0 and tQb == tQ
    # gate: a differently-named context variable (RI, not RI0) is outside
    # the pattern's scope — the file_include precondition keeps it at zero
    plainQ = ("Section P.\n"
              "Context {RI : RealInterfaceEnhanced}.\n"
              "Theorem plain_compat : forall a b c d : @S01_BaseRing.R RI,\n"
              "  lt a b -> le c d -> lt (plus a c) (plus b d).\n"
              "Proof. intros. exact w. Qed.\n"
              "End P.\n")
    tQc, nQc = apply_one(plainQ, pQ)
    c27c = nQc == 0 and tQc == plainQ
    print("cure39 ifq qualify/guards/idempotent/gate:", c27, c27b, c27c)
    ok = ok and c27 and c27b and c27c

    # v39 whole-pack idempotence on the RI0 sample (no Import line, so the
    # import-shadow variants stay out of this sample's face)
    q1, qr1 = run_pack(fQ, pack["patterns"])
    q2, qr2 = run_pack(q1, pack["patterns"])
    c28 = (q2 == q1 and all(x["matches"] == 0 for x in qr2.values()))
    print("v39 whole-pack idempotence:", c28,
          {k: x["matches"] for k, x in qr2.items() if x["matches"]})
    ok = ok and c28


    print("SELFTEST:", "PASS" if ok else "FAIL")
    return ok


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(
        description="Apply the consumer-cure canonical pack (5 patterns).")
    ap.add_argument("--file", help="target .v file")
    ap.add_argument("--pack", default=os.path.join(here, "cure_pack.json"))
    ap.add_argument("--only", help="comma-separated pattern-id subset")
    ap.add_argument("--json", help="write application report JSON here")
    ap.add_argument("--apply", action="store_true",
                    help="write the cured file (default dry-run)")
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
    pack = json.load(io.open(args.pack, "r", encoding="utf-8"))
    patterns = pack["patterns"]
    if args.only:
        want = set(t.strip() for t in args.only.split(","))
        known = set(p["id"] for p in patterns)
        unknown = want - known
        if unknown:
            print("UNKNOWN-PATTERN:", sorted(unknown))
            sys.exit(5)
        patterns = [p for p in patterns if p["id"] in want]

    text = io.open(args.file, "r", encoding="utf-8", errors="replace").read()
    before = md5s(text)
    mode = "APPLIED" if args.apply else "DRY-RUN"
    try:
        new_text, report = run_pack(text, patterns)
    except ExclusiveGroupConflict as e:
        print("EXCLUSIVE-GROUP-CONFLICT: %s" % e.groups)
        print("variant cures for one red family both matched — pick one "
              "via --only (file untouched)")
        if args.json:
            out = dict(file=args.file, mode=mode, md5_before=before,
                       md5_after=before, report={}, idempotence_ok=False,
                       exclusive_group_conflict=e.groups)
            with io.open(args.json, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=1)
            print("report json -> %s" % args.json)
        sys.exit(4)
    total = sum(v["matches"] for v in report.values())
    print("file: %s" % args.file)
    print("mode: %s  pack: %s v%s  patterns: %d" % (
        mode, pack.get("pack", "?"), pack.get("version", "?"), len(patterns)))
    print("md5 before: %s  after: %s" % (before, md5s(new_text)))
    for pid, v in report.items():
        print("  %-36s engine=%-18s matches=%d" % (pid, v["engine"], v["matches"]))
    print("total matches: %d" % total)

    rc = 0
    if args.apply:
        # idempotence assertion: second pass must find nothing (fail-loud).
        # report-mode patterns (engine station-report) are advisory stations,
        # not cures — they never rewrite and are excluded from the residual.
        report_ids = set(p["id"] for p in patterns
                         if p.get("mode") == "report")
        _t2, report2 = run_pack(new_text, patterns)
        resid = dict((k, v["matches"]) for k, v in report2.items()
                     if k not in report_ids)
        if any(resid.values()):
            print("IDEMPOTENCE-FAIL residual matches after apply: %s" % resid)
            print("file NOT written; report the residual to the caller")
            rc = 1
        else:
            with io.open(args.file, "w", encoding="utf-8") as f:
                f.write(new_text)
            print("idempotence verified (second pass zero matches); file written")
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
