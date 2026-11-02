# -*- coding: utf-8 -*-
"""cure_applier.py — applier for the consumer-cure canonical pack (5 patterns).

Purpose:
    Applies the deterministic rewrite patterns from cure_pack.json to a Rocq/Coq
    source file.  Consumer-position cures (bridge wraps, goal-opening bridges,
    opaque-reflexivity replacement, qualified successor references, NatLe
    supply bridges) exist as canonical, idempotent rewrites: applying the pack
    twice changes nothing on the second run — the applier asserts this
    mechanically after every --apply.

Inputs:
    --file path/to/file.v           target source (never modified on dry-run)
    --pack path/to/cure_pack.json   pattern pack (default: cure_pack.json
                                    next to this script)
    --only id1,id2                  restrict to a subset of pattern ids
    --json out.json                 write an application report
    --apply                         write the cured file (default: dry-run)

Outputs:
    stdout report — per pattern: trigger matches found, rewrites applied.
    --json report — {pattern_id: {matches: n, applied: n}} plus file md5s.
    Exit codes: 0 = ran (dry-run or applied with idempotence verified),
    1 = idempotence assertion failed (fail-loud), 2 = usage,
    5 = pattern id unknown, 9 = file missing.

Minimal usage:
    python3 cure_applier.py --file path/to/file.v              # dry-run
    python3 cure_applier.py --file path/to/file.v --apply      # cure + verify
    python3 cure_applier.py --selftest                          # in-memory vectors
"""
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


def run_pack(text, patterns):
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
    new_text, report = run_pack(text, patterns)
    total = sum(v["matches"] for v in report.values())
    mode = "APPLIED" if args.apply else "DRY-RUN"
    print("file: %s" % args.file)
    print("mode: %s  pack: %s v%s  patterns: %d" % (
        mode, pack.get("pack", "?"), pack.get("version", "?"), len(patterns)))
    print("md5 before: %s  after: %s" % (before, md5s(new_text)))
    for pid, v in report.items():
        print("  %-36s engine=%-18s matches=%d" % (pid, v["engine"], v["matches"]))
    print("total matches: %d" % total)

    rc = 0
    if args.apply:
        # idempotence assertion: second pass must find nothing (fail-loud)
        _t2, report2 = run_pack(new_text, patterns)
        resid = dict((k, v["matches"]) for k, v in report2.items())
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
