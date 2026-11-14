#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registry_audit.py: registry hygiene auditor for the order.txt/_CoqProject book pair: four read-only audits plus a deterministic fix plan (rocqwash tools/).

Purpose.  Read-only hygiene audits over the order.txt/_CoqProject registry pair: duplicate
  rows under one key; order-book anchor defects (anchor-text collisions, seq-form,
  malformed, missing anchors); cross-book orphans on the .v base-name basis; optional
  --live-src topology reconciliation. Findings are data, not tool failures: loud stdout
  report, still exit 0; the only writes are the explicit --json/--md output paths.

Interface.  python3 tools/registry_audit.py --order ORDER.txt --project _CoqProject
  [--live-src DIR] [--anchor-src DIR] [--json FILE] [--md FILE] [--fix-plan], or --git REPO
  --ref REF [--git-path-order PATH] [--git-path-project PATH] (exclusive input forms), or
  --selftest. Key/anchor canonical forms come from registry_union; findings carry exactly
  {key, lines, kind, evidence}; --json emits schema rocqwash-registry-audit/1 (sections
  {duplicates, anchors, orphans, live}, live null without --live-src, summary.by_kind);
  --md the markdown form. --fix-plan grammar (plan-executor contract, defined here): DEDUP
  book=<book> key='<key>' keep=L<first> drop=L<rest>; ORPHAN-ADD book=<book> key='<base>'
  template='<row>'; reanchor via the registry_union --reanchor command.

Dependencies.  Python 3 stdlib only; no third-party imports, no network, no build step. Peer
  tools/registry_union.py supplies key/anchor canonical definitions and md5 helpers
  (imported, never modified; import failure exits 9); bash 3.2 compatible via cw.sh.

Evidence.  --selftest: full finding-class spectrum on tmp fixtures; frozen registry_union md5
  vector "module A content alpha\\n" -> 77c2b9a8; read-only proof via before/after md5 equality;
  --git form on a tmp clone (bad ref exits 9); CLI exit codes; byte-identical reruns.

Exit-codes.  0 = audit reported (findings are data; total > 0 still exits 0); 1 = --selftest
  failed; 2 = usage error (forms mixed, no input, one book of the pair missing, unknown flag,
  nonexistent --apply); 9 = missing input (book, git show, --live-src, --anchor-src missing).
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
try:
    import registry_union as _ru  # noqa: E402  (key/anchor canonical source; import only, never modify)
except Exception as _e:  # pragma: no cover
    print("FAIL-LOUD: peer tools/registry_union.py not importable (key/anchor canonical "
          "dependency): %s" % _e, file=sys.stderr)
    sys.exit(9)

PROG = "registry_audit"
SCHEMA = "rocqwash-registry-audit/1"

KIND_ORDER = _ru.KIND_ORDER          # "order"
KIND_COQPROJECT = _ru.KIND_COQPROJECT  # "coqproject"

# canonical anchor: #R<seq>-<md5 first 8 hex lowercase> (the form registry_union --reanchor produces)
CANONICAL_ANCHOR_RE = re.compile(r"^#R\d+-[0-9a-f]{8}$")
# seq-form read (no fingerprint slot): ANCHOR_RE reads #R<seq> with no '-'
MD5_PLACEHOLDER = "<MD5_8>"          # plan md5 placeholder (source not given / file missing / ambiguous; wash_shape plan-miss convention)
SEQ_PLACEHOLDER = "<SEQ>"            # orphan add-row template sequence placeholder (decided at registration; not mechanically fabricable)
GIT_PATH_ORDER_DEFAULT = "order.txt"
GIT_PATH_PROJECT_DEFAULT = "_CoqProject"

# finding kind spectrum (each finding carries exactly {key,lines,kind,evidence}; kind encodes book and defect class)
K_DUP_ORDER = "dup-order"
K_DUP_PROJECT = "dup-coqproject"
K_ANCHOR_COLLISION = "anchor-collision"
K_ANCHOR_SEQ = "anchor-seq-form"
K_ANCHOR_MALFORMED = "anchor-malformed"
K_ANCHOR_MISSING = "anchor-missing"
K_ORPHAN_ORDER_ONLY = "orphan-order-only"
K_ORPHAN_PROJECT_ONLY = "orphan-project-only"
K_LIVE_MISSING = "live-missing"
K_LIVE_EXTRA = "live-extra"

EVIDENCE_LINE_CAP = 120  # raw-line clip length inside evidence (deterministic clipping)


class UsageError(Exception):
    """Usage error (exit 2)."""


class MissingInput(Exception):
    """Missing input (exit 9)."""


# ---------- read surface ----------

def read_book_file(path, what):
    """Book file -> line list (same reading as registry_union read_side: strip terminators
    and surrounding whitespace, trailing blank lines not counted). A missing file fails
    loudly with exit 9."""
    try:
        lines, _eol, _final = _ru.read_side(path, what)
    except _ru.MissingInput as e:
        raise MissingInput(str(e))
    return lines


def read_book_git(repo, ref, path, what):
    """Read a book directly via git show (same helpers as registry_union
    git_show/read_side_text)."""
    try:
        text = _ru.git_show(repo, ref, path)
    except _ru.MissingInput as e:
        raise MissingInput(str(e))
    return _ru.read_side_text(text, what)


def clip(s, cap=EVIDENCE_LINE_CAP):
    """Deterministic clipping of a raw line for evidence."""
    return s if len(s) <= cap else s[:cap] + "…"


# ---------- ① duplicate rows ----------

def audit_duplicates(lines, kind):
    """Group line numbers per key for keys carrying multiple rows. Returns findings
    (kind=dup-order|dup-coqproject)."""
    groups = {}
    for i, ln in enumerate(lines, 1):
        k = _ru.key_of(ln, kind)
        if k is not None:
            groups.setdefault(k, []).append(i)
    findings = []
    for k in sorted(groups):
        nos = groups[k]
        if len(nos) < 2:
            continue
        if kind == KIND_ORDER:
            anchors = sorted({_ru.anchor_of(lines[n - 1]) or "" for n in nos})
            if len(anchors) > 1:
                ev = ("same key %d rows L%s with differing anchors: %s"
                      % (len(nos), ",".join(str(x) for x in nos),
                         " | ".join(clip(lines[n - 1]) for n in nos)))
            else:
                ev = ("same key %d rows L%s with identical anchors (verbatim duplicate rows): %s"
                      % (len(nos), ",".join(str(x) for x in nos),
                         clip(lines[nos[0] - 1])))
            findings.append({"key": k, "lines": nos, "kind": K_DUP_ORDER,
                             "evidence": ev})
        else:
            findings.append({
                "key": k, "lines": nos, "kind": K_DUP_PROJECT,
                "evidence": "same key %d rows L%s: %s"
                            % (len(nos), ",".join(str(x) for x in nos),
                               clip(lines[nos[0] - 1]))})
    return findings


# ---------- ② anchors ----------

def classify_anchor(line):
    """order row -> (anchor token|None, form class).

    form class: 'canonical' (#R<seq>-<8 lowercase hex>) / 'seq-form' (read without a
    fingerprint) / 'malformed' (fingerprint slot not 8 lowercase hex) / None (no readable
    #R token, anchor missing).
    """
    tok = _ru.anchor_of(line)
    if tok is None:
        return None, None
    if CANONICAL_ANCHOR_RE.match(tok):
        return tok, "canonical"
    if "-" not in tok:
        return tok, "seq-form"
    return tok, "malformed"


def audit_anchors(order_lines):
    """order-book anchor audit: anchor-text collisions / seq-form / malformed / missing,
    one class each."""
    keyed = []  # (line_no, key, raw, tok, form)
    for i, ln in enumerate(order_lines, 1):
        k = _ru.key_of(ln, KIND_ORDER)
        if k is None:
            continue  # comment/blank rows carry no key and stay out of the anchor audit (registry_union key None rule)
        tok, form = classify_anchor(ln)
        keyed.append((i, k, ln, tok, form))

    findings = []
    # anchor-text collision: read token -> keys carrying it (more than one key is a collision; same reading as registry_union dup_pairs)
    by_tok = {}
    for i, k, ln, tok, form in keyed:
        if tok is not None:
            by_tok.setdefault(tok, []).append((i, k, form))
    for tok in sorted(by_tok):
        rows = by_tok[tok]
        keys = sorted({k for _i, k, _f in rows})
        if len(keys) > 1:
            forms = sorted({f for _i, _k, f in rows})
            findings.append({
                "key": tok,
                "lines": sorted(i for i, _k, _f in rows),
                "kind": K_ANCHOR_COLLISION,
                "evidence": "cross-key anchor collision: anchor text %s shared by %d keys"
                            " (%s; forms %s)"
                            % (tok, len(keys), ",".join(keys), "/".join(forms))})
    # form classes per key (the three non-canonical classes)
    for cls, kind_id, why in (
            ("seq-form", K_ANCHOR_SEQ,
             "anchor %s reads without a fingerprint (seq-form; registry_union ANCHOR_RE reading)"),
            ("malformed", K_ANCHOR_MALFORMED, None),  # evidence built per case
            (None, K_ANCHOR_MISSING,
             "keyed row carries no anchor (no readable #R token)")):
        per_key = {}
        for i, k, ln, tok, form in keyed:
            if form == cls:
                per_key.setdefault(k, []).append(i)
        for k in sorted(per_key):
            nos = per_key[k]
            raw = clip(order_lines[nos[0] - 1])
            if cls == "malformed":
                tok0 = _ru.anchor_of(order_lines[nos[0] - 1])
                fp = tok0.split("-", 1)[1]
                ev = ("anchor %s fingerprint %r is not canonical md5-8 (%d hex digits; must be "
                      "#R<seq>-<8 lowercase hex>): %s"
                      % (tok0, fp, len(fp), raw))
            else:
                ev = (why % (_ru.anchor_of(order_lines[nos[0] - 1]),)
                      if cls == "seq-form" else why) + ": " + raw
            findings.append({"key": k, "lines": nos, "kind": kind_id,
                             "evidence": ev})
    return findings


# ---------- ③ orphans ----------

def order_base_name(key):
    """order key -> .v base name (strip .v, take the last path component; Local/LW0.v -> LW0)."""
    bare = _ru.bare_name(key)
    return bare.rsplit("/", 1)[-1]


def audit_orphans(order_lines, project_lines):
    """Orphans between the order and coqproject books (.v base-name basis; flag/comment rows
    filtered out). Returns (findings, stats_extra); stats_extra carries the filter counts.
    """
    order_base = {}   # base name -> [line numbers]
    order_keyed = 0
    order_nonv = 0
    for i, ln in enumerate(order_lines, 1):
        k = _ru.key_of(ln, KIND_ORDER)
        if k is None:
            continue
        order_keyed += 1
        if not k.endswith(".v"):
            order_nonv += 1  # non-.v keyed rows do not join base-name matching
            continue
        order_base.setdefault(order_base_name(k), []).append(i)
    proj_keys = {}    # base name -> [line numbers]
    proj_module = 0
    flag_filtered = 0
    proj_raw = {}     # base name -> first raw row (for add-row templates)
    for i, ln in enumerate(project_lines, 1):
        if not ln.endswith(".v"):
            flag_filtered += 1  # flag/comment rows (-Q . "" and the like) filtered out of matching
            continue
        k = _ru.key_of(ln, KIND_COQPROJECT)
        proj_module += 1
        proj_keys.setdefault(k, []).append(i)
        proj_raw.setdefault(k, ln)
    findings = []
    for base in sorted(set(order_base) - set(proj_keys)):
        findings.append({
            "key": base, "lines": order_base[base],
            "kind": K_ORPHAN_ORDER_ONLY,
            "evidence": "order has .v base name %r (key form %s) with no matching "
                        "coqproject module row (base-name basis; %d flag rows filtered)"
                        % (base, clip(order_lines[order_base[base][0] - 1]),
                           flag_filtered)})
    for base in sorted(set(proj_keys) - set(order_base)):
        findings.append({
            "key": base, "lines": proj_keys[base],
            "kind": K_ORPHAN_PROJECT_ONLY,
            "evidence": "coqproject has module %r (%s) with no matching order row"
                        % (base, clip(proj_raw[base]))})
    stats_extra = {"order_keyed": order_keyed, "order_keyed_nonv": order_nonv,
                   "project_module_rows": proj_module,
                   "flag_filtered": flag_filtered}
    return findings, stats_extra


# ---------- ④ live topology references ----------

def audit_live(order_lines, live_src):
    """Reconcile order keyed rows against the actual .v files under --live-src, both
    directions (exact relpath equality)."""
    if not os.path.isdir(live_src):
        raise MissingInput("--live-src directory missing: %s" % live_src)
    disk = set()
    for dirpath, _dirs, fnames in os.walk(live_src):
        rel_dir = os.path.relpath(dirpath, live_src)
        for fn in fnames:
            if fn.endswith(".v"):
                rel = fn if rel_dir == "." else os.path.join(rel_dir, fn)
                disk.add(rel.replace(os.sep, "/"))
    table = {}  # relpath in the order table -> [line numbers]
    for i, ln in enumerate(order_lines, 1):
        k = _ru.key_of(ln, KIND_ORDER)
        if k is None:
            continue
        rel = k if k.endswith(".v") else k + ".v"
        table.setdefault(rel, []).append(i)
    findings = []
    for rel in sorted(set(table) - disk):
        findings.append({
            "key": rel, "lines": table[rel], "kind": K_LIVE_MISSING,
            "evidence": ".v file listed in the order table but missing under live-src: %s"
                        % os.path.join(live_src, rel)})
    for rel in sorted(disk - set(table)):
        findings.append({
            "key": rel, "lines": [], "kind": K_LIVE_EXTRA,
            "evidence": ".v file present under live-src but absent from the order table: %s" % rel})
    return findings


# ---------- fix plan (--fix-plan; no disk writes; executor contract) ----------

def shq(s):
    """Shell-quote a path value for the plan (deterministic: single-quote escaping when
    empty or carrying whitespace/quotes; bare otherwise)."""
    if s and re.fullmatch(r"[A-Za-z0-9_./@+=,:^-]+", s):
        return s
    return "'" + s.replace("'", "'\\''") + "'"


def shq_always(s):
    """Always single-quote plan data values (key/template) for a uniform grammar with
    deterministic escaping."""
    return "'" + s.replace("'", "'\\''") + "'"


def resolve_md5_8(bare, anchor_src):
    """Resolve the md5-8 of the actual file for a bare name under --anchor-src
    (registry_union resolve_entity/md5_8_of used directly).

    Source not given / file missing / ambiguous -> (MD5_PLACEHOLDER, note) (same
    convention as wash_shape plan-miss; never fabricated; the audit does not fail when
    a plan md5 cannot be resolved).
    """
    if not anchor_src:
        return MD5_PLACEHOLDER, "--anchor-src not given"
    try:
        entity = _ru.resolve_entity(bare, anchor_src)
    except _ru.UsageError as e:
        return MD5_PLACEHOLDER, "ambiguous entity (%s)" % str(e).strip()
    if entity is None:
        return MD5_PLACEHOLDER, "no matching .v file under anchor-src"
    return _ru.md5_8_of(entity), "file %s" % entity


def build_fix_plan(order_lines, project_lines, sections, args):
    """Deterministic fix plan (dedup keep-first / reanchor / orphan add-row templates /
    unresolvable; no disk writes)."""
    plan = {"dedup": [], "reanchor": [], "orphan": [], "unresolvable": []}

    # dedup keep-first (keep = min line number; drop = remaining lines ascending)
    for f in sections["duplicates"]:
        book = "order" if f["kind"] == K_DUP_ORDER else "coqproject"
        nos = sorted(f["lines"])
        keep, drop = nos[0], nos[1:]
        cmd = ("DEDUP book=%s key=%s keep=L%d drop=%s"
               % (book, shq_always(f["key"]), keep,
                  ",".join("L%d" % n for n in drop)))
        plan["dedup"].append({"book": book, "key": f["key"],
                              "keep_line": keep, "drop_lines": drop,
                              "command": cmd})

    # reanchor targets: the seq-form/malformed keys (canonical-form collisions are not
    # targeted; recomputation would not change their value).
    # plan lines = every table row under the key (registry_union apply_reanchor rewrites all
    # rows of the key; well-formed rows under the same key are recomputed too; expected_anchor
    # taken from the first affected row).
    reanchor_src = args.anchor_src
    for f in sections["anchors"]:
        if f["kind"] not in (K_ANCHOR_SEQ, K_ANCHOR_MALFORMED):
            continue
        k = f["key"]
        bare = _ru.bare_name(k)
        affected = sorted(f["lines"])
        nos = sorted(i for i, ln in enumerate(order_lines, 1)
                     if _ru.key_of(ln, KIND_ORDER) == k)
        raw = order_lines[affected[0] - 1]
        tok = _ru.anchor_of(raw)
        seq = tok[2:].split("-", 1)[0] if tok else ""
        md5_8, how = resolve_md5_8(bare, reanchor_src)
        if md5_8 == MD5_PLACEHOLDER:
            expected = "#R%s-%s" % (seq, MD5_PLACEHOLDER)
        else:
            expected = "#R%s-%s" % (seq, md5_8)
        src_part = reanchor_src if reanchor_src else "<ANCHOR_SRC>"
        if args.git is not None:
            head = ("python3 tools/registry_union.py --git %s --ref-base %s "
                    "--ref-main %s --ref-branch %s --kind order"
                    % (shq(args.git), shq(args.ref), shq(args.ref), shq(args.ref)))
        else:
            head = ("python3 tools/registry_union.py --main %s --base %s "
                    "--branch %s --kind order"
                    % (shq(args.order), shq(args.order), shq(args.order)))
        cmd = ("%s --reanchor %s --anchor-src %s --out <OUT> --apply"
               % (head, shq(bare), shq(src_part)))
        plan["reanchor"].append({
            "key": k, "bare": bare, "lines": nos, "seq": seq,
            "old_anchor": tok, "md5_8": md5_8, "expected_anchor": expected,
            "md5_source": how, "command": cmd})

    # orphan add-row templates
    for f in sections["orphans"]:
        if f["kind"] == K_ORPHAN_ORDER_ONLY:
            base = f["key"]
            # raw order key form (the added _CoqProject row is the key's own path form)
            raw = order_lines[sorted(f["lines"])[0] - 1]
            template = raw.split("#", 1)[0].strip()
            cmd = ("ORPHAN-ADD book=coqproject key=%s template=%s"
                   % (shq_always(base), shq_always(template)))
            plan["orphan"].append({"direction": "order-only", "key": base,
                                   "template": template, "command": cmd})
        else:
            base = f["key"]
            raw = project_lines[sorted(f["lines"])[0] - 1]
            md5_8, _how = resolve_md5_8(base, args.anchor_src)
            template = "%s#R%s-%s" % (raw, SEQ_PLACEHOLDER, md5_8)
            cmd = ("ORPHAN-ADD book=order key=%s template=%s"
                   % (shq_always(base), shq_always(template)))
            plan["orphan"].append({"direction": "project-only", "key": base,
                                   "template": template, "command": cmd})

    # not mechanically resolvable: canonical-form anchor collisions (identical md5 signature
    # means identical content or a transcription slip; reanchoring cannot change the value;
    # manual triage)
    for f in sections["anchors"]:
        if f["kind"] != K_ANCHOR_COLLISION:
            continue
        tok = f["key"]
        if CANONICAL_ANCHOR_RE.match(tok):
            plan["unresolvable"].append({
                "reason": "canonical-anchor-collision", "anchor": tok,
                "lines": f["lines"], "evidence": f["evidence"],
                "note": "canonical-form anchor collision: identical md5 signature means "
                        "identical content or a slip under the same signature; --reanchor "
                        "recomputation cannot change the value; manual triage required "
                        "(wash_shape plan-miss convention)"})
    return plan


# ---------- reporting ----------

def sort_findings(findings):
    """Deterministic finding order: (kind, key). lines are already ascending."""
    return sorted(findings, key=lambda f: (f["kind"], f["key"]))


def build_payload(mode, inputs, stats, sections, fix_plan, want_fix):
    """Build the report (schema rocqwash-registry-audit/1; deterministic via sort_keys)."""
    by_kind = {}
    total = 0
    for sec in ("duplicates", "anchors", "orphans", "live"):
        for f in sections.get(sec) or []:
            by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
            total += 1
    payload = {
        "schema": SCHEMA,
        "mode": mode,
        "inputs": inputs,
        "live_src": sections.get("_live_src"),
        "anchor_src": sections.get("_anchor_src"),
        "stats": stats,
        "sections": {
            "duplicates": sections["duplicates"],
            "anchors": sections["anchors"],
            "orphans": sections["orphans"],
            "live": sections["live"],  # null when not enabled (absence recorded as-is)
        },
        "summary": {
            "duplicates": len(sections["duplicates"]),
            "anchors": len(sections["anchors"]),
            "orphans": len(sections["orphans"]),
            "live": len(sections["live"] or []),
            "total": total,
            "by_kind": {k: by_kind[k] for k in sorted(by_kind)},
        },
    }
    if want_fix:
        payload["fix_plan"] = fix_plan
    return payload


def dump_json(path, obj):
    """Deterministic JSON write to disk (sort_keys plus indent=1; same form as
    registry_union dump_json)."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def render_md(payload):
    """Human-readable markdown report (same order as the JSON; deterministic)."""
    secs = payload["sections"]
    summ = payload["summary"]
    out = ["# Registry hygiene report (%s)" % SCHEMA, ""]
    out.append("- mode: %s" % payload["mode"])
    for k in sorted(payload["inputs"]):
        out.append("- %s: %s" % (k, payload["inputs"][k]))
    out.append("- live_src: %s" % (payload["live_src"] or "(not enabled)"))
    out.append("- anchor_src: %s" % (payload["anchor_src"] or "(not given)"))
    st = payload["stats"]
    out.append("- rows: order total %d, keyed %d (non-.v keyed %d); coqproject total %d"
               ", module rows %d (flag/comment rows filtered %d)"
               % (st["order_rows"], st["order_keyed"], st["order_keyed_nonv"],
                  st["project_rows"], st["project_module_rows"],
                  st["flag_filtered"]))
    out.append("")
    titles = {
        "duplicates": "① duplicate rows",
        "anchors": "② anchors (order book; coqproject rows carry no anchors)",
        "orphans": "③ orphans (.v base-name basis; flag rows filtered)",
        "live": "④ live topology references",
    }
    for sec in ("duplicates", "anchors", "orphans", "live"):
        rows = secs[sec]
        if rows is None:
            out.append("## %s (not enabled; --live-src not given)" % titles[sec])
            out.append("")
            continue
        out.append("## %s (%d findings)" % (titles[sec], len(rows)))
        out.append("")
        if not rows:
            out.append("(no findings)")
            out.append("")
            continue
        out.append("| # | kind | key | lines | evidence |")
        out.append("|---|------|-----|-------|----------|")
        for n, f in enumerate(rows, 1):
            ev = f["evidence"].replace("|", "\\|").replace("\n", " ")
            out.append("| %d | %s | %s | %s | %s |"
                       % (n, f["kind"], f["key"].replace("|", "\\|"),
                          ",".join(str(x) for x in f["lines"]) or "-", ev))
        out.append("")
    if "fix_plan" in payload:
        fp = payload["fix_plan"]
        out.append("## Fix plan (--fix-plan; no disk writes; no --apply; consumed by the plan executor)")
        out.append("")
        out.append("### dedup keep-first")
        out.append("")
        if fp["dedup"]:
            for d in fp["dedup"]:
                out.append("- `%s`" % d["command"])
        else:
            out.append("(none)")
        out.append("")
        out.append("### reanchor (registry_union --reanchor; md5 computed against --anchor-src files)")
        out.append("")
        if fp["reanchor"]:
            for r in fp["reanchor"]:
                out.append("- `%s` (expected `%s` <- `%s`; md5_8=%s; %s)"
                           % (r["command"], r["expected_anchor"],
                              r["old_anchor"], r["md5_8"], r["md5_source"]))
        else:
            out.append("(no reanchor targets)")
        out.append("")
        out.append("### orphan add-row templates")
        out.append("")
        if fp["orphan"]:
            for o in fp["orphan"]:
                out.append("- `%s` (%s)" % (o["command"], o["direction"]))
        else:
            out.append("(none)")
        out.append("")
        out.append("### not mechanically resolvable (manual triage)")
        out.append("")
        if fp["unresolvable"]:
            for u in fp["unresolvable"]:
                out.append("- anchor `%s` (L%s): %s"
                           % (u["anchor"], ",".join(str(x) for x in u["lines"]),
                              u["note"]))
        else:
            out.append("(none)")
        out.append("")
    out.append("---")
    out.append("total findings %d (duplicates=%d anchors=%d orphans=%d live=%d)"
               "; findings are data, the auditor exits 0 (same rule as ci_triage)"
               % (summ["total"], summ["duplicates"], summ["anchors"],
                  summ["orphans"], summ["live"]))
    out.append("")
    return "\n".join(out)


def print_stdout(payload):
    """Loud stdout report (findings are data; rc always 0)."""
    secs = payload["sections"]
    summ = payload["summary"]
    print("=== REGISTRY-AUDIT (%s·%s) ===" % (payload["mode"], SCHEMA))
    for k in sorted(payload["inputs"]):
        print("  %s=%s" % (k, payload["inputs"][k]))
    st = payload["stats"]
    print("rows: order=%d(keyed=%d nonv=%d) coqproject=%d(module=%d "
          "flag_filtered=%d)"
          % (st["order_rows"], st["order_keyed"], st["order_keyed_nonv"],
             st["project_rows"], st["project_module_rows"],
             st["flag_filtered"]))
    for sec, label in (("duplicates", "① duplicate rows"), ("anchors", "② anchors"),
                       ("orphans", "③ orphans"), ("live", "④ live topology references")):
        rows = secs[sec]
        if rows is None:
            print("--- %s: not enabled (--live-src not given) ---" % label)
            continue
        print("--- %s: %d findings ---" % (label, len(rows)))
        for f in rows:
            print("  [%s] key=%s lines=%s" % (f["kind"], f["key"],
                                              ",".join(str(x) for x in f["lines"]) or "-"))
            print("      %s" % f["evidence"])
    if "fix_plan" in payload:
        fp = payload["fix_plan"]
        print("--- fix plan (--fix-plan; no disk writes; plan executor) ---")
        for d in fp["dedup"]:
            print("  %s" % d["command"])
        for r in fp["reanchor"]:
            print("  %s  # expected %s<-%s (md5_8=%s; %s)"
                  % (r["command"], r["expected_anchor"], r["old_anchor"],
                     r["md5_8"], r["md5_source"]))
        for o in fp["orphan"]:
            print("  %s" % o["command"])
        for u in fp["unresolvable"]:
            print("  UNRESOLVED anchor %s: %s" % (u["anchor"], u["note"]))
    print("REGISTRY-AUDIT: total=%d findings (duplicates=%d anchors=%d orphans=%d "
          "live=%d); findings are data; exit 0"
          % (summ["total"], summ["duplicates"], summ["anchors"],
             summ["orphans"], summ["live"]))


# ---------- main flow ----------

def run_audit(args):
    """Main audit flow (read surface -> four audits -> payload). Raises
    UsageError/MissingInput."""
    if args.live_src is not None and not os.path.isdir(args.live_src):
        raise MissingInput("--live-src directory missing: %s" % args.live_src)
    if args.anchor_src is not None and not os.path.isdir(args.anchor_src):
        raise MissingInput("--anchor-src directory missing: %s" % args.anchor_src)

    if args.git is not None:
        git_po = args.git_path_order or GIT_PATH_ORDER_DEFAULT
        git_pp = args.git_path_project or GIT_PATH_PROJECT_DEFAULT
        inputs = {"git": args.git, "ref": args.ref,
                  "git_path_order": git_po, "git_path_project": git_pp}
        order_lines = read_book_git(args.git, args.ref, git_po, "order(ref)")
        project_lines = read_book_git(args.git, args.ref, git_pp,
                                      "project(ref)")
        mode = "git"
    else:
        inputs = {"order": args.order, "project": args.project}
        order_lines = read_book_file(args.order, "--order")
        project_lines = read_book_file(args.project, "--project")
        mode = "files"

    sections = {
        "duplicates": sort_findings(audit_duplicates(order_lines, KIND_ORDER)
                                    + audit_duplicates(project_lines,
                                                       KIND_COQPROJECT)),
        "anchors": sort_findings(audit_anchors(order_lines)),
    }
    orphan_findings, stats_extra = audit_orphans(order_lines, project_lines)
    sections["orphans"] = sort_findings(orphan_findings)
    if args.live_src is not None:
        sections["live"] = sort_findings(audit_live(order_lines, args.live_src))
        sections["_live_src"] = args.live_src
    else:
        sections["live"] = None
        sections["_live_src"] = None
    sections["_anchor_src"] = args.anchor_src

    stats = {"order_rows": len(order_lines),
             "project_rows": len(project_lines)}
    stats.update(stats_extra)

    fix_plan = None
    if args.fix_plan:
        fix_plan = build_fix_plan(order_lines, project_lines, sections, args)
    payload = build_payload(mode, inputs, stats, sections, fix_plan,
                            args.fix_plan)
    return payload


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="registry hygiene auditor: four read-only audits over the "
                    "order.txt/_CoqProject book pair plus a deterministic fix plan "
                    "(no --apply, no disk writes)")
    ap.add_argument("--order", default=None, metavar="PATH",
                    help="order.txt book (paired with --project)")
    ap.add_argument("--project", default=None, metavar="PATH",
                    help="_CoqProject book (paired with --order)")
    ap.add_argument("--git", default=None, metavar="REPO",
                    help="git direct read: repository path (--ref required; exclusive "
                         "with the book-file form)")
    ap.add_argument("--ref", default=None, metavar="REF",
                    help="ref for the git direct read (audits the book snapshot at that ref)")
    ap.add_argument("--git-path-order", default=None, metavar="PATH",
                    help="in-repository path of order.txt (default order.txt)")
    ap.add_argument("--git-path-project", default=None, metavar="PATH",
                    help="in-repository path of _CoqProject (default _CoqProject)")
    ap.add_argument("--live-src", default=None, metavar="DIR",
                    help="directory of actual .v files for the live topology audit "
                         "(optional; .v files collected via os.walk)")
    ap.add_argument("--anchor-src", default=None, metavar="DIR",
                    help="source directory for plan md5 values (optional; matching .v "
                         "files recomputed via os.walk)")
    ap.add_argument("--fix-plan", action="store_true",
                    help="attach the deterministic fix plan (no disk writes; no --apply; "
                         "consumed by the plan executor)")
    ap.add_argument("--json", default=None, metavar="FILE",
                    help="JSON report output (schema rocqwash-registry-audit/1)")
    ap.add_argument("--md", default=None, metavar="FILE",
                    help="human-readable markdown report output")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # ---- flag pairing (fail-loud usage surface) ----
    def die_usage(msg):
        print("FAIL-LOUD: %s" % msg, file=sys.stderr)
        sys.exit(2)

    file_mode = args.order is not None or args.project is not None
    git_mode = args.git is not None
    if file_mode and git_mode:
        die_usage("--order/--project (book files) and --git (direct read) are exclusive; "
                  "both forms given")
    if not file_mode and not git_mode:
        die_usage("no input surface: give --order plus --project, or --git plus --ref"
                  " (--selftest excepted)")
    if file_mode and (args.order is None or args.project is None):
        die_usage("--order and --project must be given as a pair (both books; one alone "
                  "is a usage error)")
    if git_mode and args.ref is None:
        die_usage("--git direct read requires --ref (audits the book snapshot at that ref)")
    if not git_mode and (args.git_path_order or args.git_path_project):
        die_usage("--git-path-order/--git-path-project are valid only with --git direct read")
    if args.ref is not None and not git_mode:
        die_usage("--ref is valid only with --git direct read")

    # ---- audit (missing read input -> 9; everything else fails loudly) ----
    try:
        payload = run_audit(args)
    except MissingInput as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    except _ru.UsageError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    # ---- report (writes go only to the explicit --json/--md paths) ----
    print_stdout(payload)
    if args.json:
        dump_json(args.json, payload)
        print("json -> %s" % args.json)
    if args.md:
        with io.open(args.md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_md(payload))
        print("md -> %s" % args.md)
    sys.exit(0)


# ---------- selftest ----------

def selftest():
    """Embedded vector set (synthesized under tmp; shaped like real registry rows; no real
    repository touched, no network, no build):

    1  full finding-class spectrum of the four audits (duplicates / anchor collisions /
       seq-form / malformed / missing anchors / orphans / flag-row filtering / live missing
       and extra files) plus fix-plan command correctness (dedup keep-first; reanchor
       command carries the correct md5, the 77c2b9a8 frozen vector, and placeholder forms)
    2  read-only proof (book and live-tree md5 unchanged before/after; no --apply, rc 2)
    3  determinism (rerun json/md byte-identical)
    4  --git direct read (local tmp clone; same findings as the file form; bad ref 9)
    5  CLI exit codes (help 0 / bogus 2 / no input 2 / half book 2 / mixed --ref 2 /
       missing book 9 / missing --live-src 9)
    """
    import tempfile

    def run(argv):
        p = subprocess.run(
            [sys.executable, "-B",
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          PROG + ".py")] + argv,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def wf(path, text):
        with io.open(path, "wb") as fh:
            fh.write(text.encode("utf-8"))
        return path

    def md5_of(path):
        h = hashlib.md5()
        with io.open(path, "rb") as fh:
            h.update(fh.read())
        return h.hexdigest()

    tmp = tempfile.mkdtemp(prefix="rocqwash_ra_self_")
    try:
        # ---- fixture rows shaped like real registry rows (same key with differing anchors / shared anchor text / seq-form / seven-digit signature) ----
        order_text = ("\n".join([
            "A.v#R0-d66910",          # L1 malformed (6-hex legacy fingerprint), collides on anchor text, same key as L8 with a different anchor
            "B.v#R0-d66910",          # L2 anchor-text collision (different key, same anchor text)
            "C.v#R97",                # L3 seq-form (no fingerprint)
            "D.v#R43a003",            # L4 seq-form (reads as #R43)
            "E.v#R97-b48a001",        # L5 malformed (seven-hex-digit signature)
            "F.v",                    # L6 anchor missing
            "G.v#R0-11111111",        # L7 canonical (8 lowercase hex)
            "A.v#R40-22222222",       # L8 same key as L1 with a different anchor (the anchor itself is canonical)
            "# comment row",          # L9 comment row (key None, not audited)
        ]) + "\n")
        project_text = ("\n".join([
            "-Q . \"\"",              # L1 flag row (filtered out of matching)
            "A.v",                    # L2
            "A.v",                    # L3 duplicate under the same key
            "C.v",                    # L4
            "E.v",                    # L5
            "H.v",                    # L6 orphan (project-only)
        ]) + "\n")
        d1 = os.path.join(tmp, "case")
        os.makedirs(d1)
        order_f = wf(os.path.join(d1, "order.txt"), order_text)
        project_f = wf(os.path.join(d1, "_CoqProject"), project_text)
        live = os.path.join(d1, "live")
        os.makedirs(live)
        for name, content in (("A.v", "module A.\n"), ("C.v", "module C.\n"),
                              ("E.v", "module E.\n"), ("H.v", "module H.\n")):
            wf(os.path.join(live, name), content)
        world = os.path.join(d1, "world")
        os.makedirs(world)
        # registry_union frozen md5 vector: "module A content alpha\n" -> 77c2b9a8
        wf(os.path.join(world, "A.v"), "module A content alpha\n")
        assert _ru.md5_8_of(os.path.join(world, "A.v")) == "77c2b9a8"

        j1 = os.path.join(d1, "r.json")
        m1 = os.path.join(d1, "r.md")
        p = run(["--order", order_f, "--project", project_f,
                 "--live-src", live, "--anchor-src", world,
                 "--json", j1, "--md", m1, "--fix-plan"])
        assert p.returncode == 0, "expected rc=0 (findings are data), got %d\n%s" % (
            p.returncode, p.stdout)
        rep = json.load(io.open(j1, encoding="utf-8"))
        assert rep["schema"] == SCHEMA, rep["schema"]
        secs = rep["sections"]
        summ = rep["summary"]

        # ① duplicates: order A [1,8] (differing-anchors note) plus coqproject A [2,3]
        dups = {(f["kind"], f["key"]): f for f in secs["duplicates"]}
        assert (K_DUP_ORDER, "A.v") in dups and dups[(K_DUP_ORDER, "A.v")]["lines"] == [1, 8], secs["duplicates"]
        assert "differing anchors" in dups[(K_DUP_ORDER, "A.v")]["evidence"], dups[(K_DUP_ORDER, "A.v")]
        assert (K_DUP_PROJECT, "A") in dups and dups[(K_DUP_PROJECT, "A")]["lines"] == [2, 3], secs["duplicates"]

        # ② anchors: collision / seq-form / malformed / missing each detected; canonical G not listed
        an = {(f["kind"], f["key"]): f for f in secs["anchors"]}
        assert (K_ANCHOR_COLLISION, "#R0-d66910") in an, secs["anchors"]
        assert sorted(an[(K_ANCHOR_COLLISION, "#R0-d66910")]["lines"]) == [1, 2], an
        assert (K_ANCHOR_SEQ, "C.v") in an and an[(K_ANCHOR_SEQ, "C.v")]["lines"] == [3], an
        assert (K_ANCHOR_SEQ, "D.v") in an and "#R43" in an[(K_ANCHOR_SEQ, "D.v")]["evidence"], an
        assert (K_ANCHOR_MALFORMED, "A.v") in an and an[(K_ANCHOR_MALFORMED, "A.v")]["lines"] == [1], an
        assert (K_ANCHOR_MALFORMED, "B.v") in an and an[(K_ANCHOR_MALFORMED, "B.v")]["lines"] == [2], an
        assert (K_ANCHOR_MALFORMED, "E.v") in an and "7 hex digits" in an[(K_ANCHOR_MALFORMED, "E.v")]["evidence"] \
            and "b48a001" in an[(K_ANCHOR_MALFORMED, "E.v")]["evidence"], an
        assert (K_ANCHOR_MISSING, "F.v") in an and an[(K_ANCHOR_MISSING, "F.v")]["lines"] == [6], an
        assert all("G.v" != f["key"] for f in secs["anchors"]), "canonical anchors must not be listed as findings"

        # ③ orphans: order-only {B,D,F,G}; project-only {H}; flag rows filtered 1
        orph = {(f["kind"], f["key"]): f for f in secs["orphans"]}
        assert {(k, ) for (kd, k) in orph if kd == K_ORPHAN_ORDER_ONLY} == {("B",), ("D",), ("F",), ("G",)}, secs["orphans"]
        assert [k for (kd, k) in orph if kd == K_ORPHAN_PROJECT_ONLY] == ["H"], secs["orphans"]
        assert rep["stats"]["flag_filtered"] == 1, rep["stats"]
        assert rep["stats"]["project_module_rows"] == 5, rep["stats"]

        # ④ live: missing {B,D,F,G}; extra {H.v}
        lv = {(f["kind"], f["key"]): f for f in secs["live"]}
        assert {k for (kd, k) in lv if kd == K_LIVE_MISSING} == {"B.v", "D.v", "F.v", "G.v"}, secs["live"]
        assert {k for (kd, k) in lv if kd == K_LIVE_EXTRA} == {"H.v"}, secs["live"]
        assert summ["total"] == 19, summ
        # exact counts: duplicates=2 anchors=7 (collisions 1 + malformed 3 + seq 2 + missing 1) orphans=5 live=5
        assert summ["duplicates"] == 2 and summ["anchors"] == 7 \
            and summ["orphans"] == 5 and summ["live"] == 5, summ

        # fix-plan command correctness
        fp = rep["fix_plan"]
        dd = {(d["book"], d["key"]): d for d in fp["dedup"]}
        assert dd[("order", "A.v")]["command"] == \
            "DEDUP book=order key='A.v' keep=L1 drop=L8", fp["dedup"]
        assert dd[("coqproject", "A")]["command"] == \
            "DEDUP book=coqproject key='A' keep=L2 drop=L3", fp["dedup"]
        ra = {r["key"]: r for r in fp["reanchor"]}
        assert set(ra) == {"A.v", "B.v", "C.v", "D.v", "E.v"}, fp["reanchor"]
        # reanchor command carries the correct md5 (77c2b9a8 frozen vector; A has a real file) plus the expected anchor form
        assert ra["A.v"]["md5_8"] == "77c2b9a8", ra["A.v"]
        assert ra["A.v"]["expected_anchor"] == "#R0-77c2b9a8", ra["A.v"]
        assert "--reanchor A" in ra["A.v"]["command"] and "--apply" in ra["A.v"]["command"], ra["A.v"]
        # reanchor plan lines = every table row under the key (apply_reanchor reading; well-formed L8 is recomputed too)
        assert ra["A.v"]["lines"] == [1, 8], ra["A.v"]
        # source not given / file missing -> <MD5_8> placeholder (never fabricated)
        assert ra["C.v"]["md5_8"] == MD5_PLACEHOLDER \
            and ra["C.v"]["expected_anchor"] == "#R97-<MD5_8>", ra["C.v"]
        assert ra["D.v"]["seq"] == "43" and ra["E.v"]["seq"] == "97", fp["reanchor"]
        orz = {(o["direction"], o["key"]): o for o in fp["orphan"]}
        assert orz[("order-only", "B")]["template"] == "B.v", fp["orphan"]
        assert orz[("project-only", "H")]["template"] == "H.v#R<SEQ>-<MD5_8>", fp["orphan"]
        # canonical-form collisions are not reanchor targets; none here -> unresolvable empty
        assert fp["unresolvable"] == [], fp["unresolvable"]
        b_json = io.open(j1, "rb").read()  # determinism baseline (captured before the step-2 overwrite)
        b_md = io.open(m1, "rb").read()
        print("  [1/5] four-audit class spectrum OK (duplicates/collision/seq-form/"
              "malformed/missing/orphans/flag filter/live missing+extra; total=19) plus "
              "plan dedup keep-first / reanchor 77c2b9a8 / placeholders")

        # ---- read-only proof: book and live-tree md5 unchanged before/after ----
        before = ([md5_of(order_f), md5_of(project_f)]
                  + [md5_of(os.path.join(live, n)) for n in sorted(os.listdir(live))])
        p = run(["--order", order_f, "--project", project_f,
                 "--live-src", live, "--json", j1, "--md", m1])
        assert p.returncode == 0, p.stdout
        after = ([md5_of(order_f), md5_of(project_f)]
                 + [md5_of(os.path.join(live, n)) for n in sorted(os.listdir(live))])
        assert before == after, "read-only violation: book/tree bytes changed"
        assert "fix_plan" not in json.load(io.open(j1, encoding="utf-8")), \
            "fix_plan must be absent without --fix-plan"
        p = run(["--order", order_f, "--project", project_f, "--apply"])
        assert p.returncode == 2, "--apply does not exist (argparse rc=2 expected), got %d" % p.returncode
        print("  [2/5] read-only proof OK (book+live tree md5 unchanged; no --fix-plan no "
              "plan; --apply absent rc2)")

        # ---- determinism: same input rerun, json/md byte-identical (baseline from step 1) ----
        p = run(["--order", order_f, "--project", project_f,
                 "--live-src", live, "--anchor-src", world,
                 "--json", j1, "--md", m1, "--fix-plan"])
        assert p.returncode == 0, p.stdout
        assert io.open(j1, "rb").read() == b_json, "json bytes changed (violation)"
        assert io.open(m1, "rb").read() == b_md, "md bytes changed (violation)"
        print("  [3/5] determinism OK (json/md byte-identical on rerun)")

        # ---- --git direct read (local tmp clone; same findings as the file form; bad ref 9) ----
        if shutil.which("git") is None:
            print("  [4/5] git direct read SKIP (git not on PATH; skipped, not counted as a failure)")
        else:
            d4 = os.path.join(tmp, "repo")
            os.makedirs(d4)
            env = dict(os.environ)
            env.update({"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t",
                        "GIT_AUTHOR_DATE": "2026-11-11T00:00:00 +0000",
                        "GIT_COMMITTER_DATE": "2026-11-11T00:00:00 +0000"})

            def g(*a):
                p4 = subprocess.run(["git", "-C", d4] + list(a), env=env,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
                assert p4.returncode == 0, p4.stdout
                return p4.stdout.decode("utf-8", errors="replace").strip()

            g("init")
            branch = g("symbolic-ref", "--short", "HEAD")
            wf(os.path.join(d4, "order.txt"), order_text)
            wf(os.path.join(d4, "_CoqProject"), project_text)
            g("add", "order.txt", "_CoqProject")
            g("commit", "-m", "registry snapshot")
            j4 = os.path.join(tmp, "r4.json")
            p = run(["--git", d4, "--ref", branch, "--json", j4, "--fix-plan"])
            assert p.returncode == 0, p.stdout
            rep4 = json.load(io.open(j4, encoding="utf-8"))
            assert rep4["mode"] == "git", rep4["mode"]
            assert rep4["summary"]["duplicates"] == 2 \
                and rep4["summary"]["anchors"] == 7 \
                and rep4["summary"]["orphans"] == 5 \
                and rep4["summary"]["live"] == 0 \
                and rep4["summary"]["total"] == 14, rep4["summary"]
            assert any(f["kind"] == K_DUP_ORDER and f["key"] == "A.v"
                       for f in rep4["sections"]["duplicates"]), rep4
            # git-form reanchor plans go through the registry_union --git surface (shq-form match;
            # paths with spaces or backslashes are shq-quoted; the bare POSIX tmp path quotes to
            # its literal self)
            assert any(("--git %s" % shq(d4)) in r["command"]
                       for r in rep4["fix_plan"]["reanchor"]), rep4["fix_plan"]
            p = run(["--git", d4, "--ref", "no-such-ref", "--json", j4])
            assert p.returncode == 9, "bad ref must give rc=9, got %d" % p.returncode
            print("  [4/5] git direct read OK (tmp clone same findings; reanchor plan "
                  "--git form; bad ref 9)")

        # ---- CLI exit codes plus schema surface ----
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag must give rc=2, got %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "no input must give rc=2, got %d" % p.returncode
        p = run(["--order", order_f])
        assert p.returncode == 2, "half book pair must give rc=2, got %d" % p.returncode
        p = run(["--order", order_f, "--project", project_f, "--ref", "x"])
        assert p.returncode == 2, "--ref mixed into file form must give rc=2, got %d" % p.returncode
        p = run(["--order", os.path.join(tmp, "nope.txt"),
                 "--project", project_f])
        assert p.returncode == 9, "missing book must give rc=9, got %d" % p.returncode
        p = run(["--order", order_f, "--project", project_f,
                 "--live-src", os.path.join(tmp, "nolive")])
        assert p.returncode == 9, "missing --live-src must give rc=9, got %d" % p.returncode
        print("  [5/5] CLI exit codes OK (help0/bogus2/no-input2/half-book2/mixed-ref2/"
              "missing-book9/missing-live-src9)")

        print("REGISTRY-AUDIT-SELFTEST PASS: four-audit class spectrum / plan "
              "keep-first+md5 vector+placeholders / read-only proof / determinism / git "
              "direct read / CLI exit codes, all checks passed")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
