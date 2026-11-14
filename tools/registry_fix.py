#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registry_fix.py: registry fix-plan executor for the registry_audit fix-plan (rocqwash tools/).

Purpose.  Execute the deterministic fix plan produced by `tools/registry_audit.py --fix-plan` over the
  audited order.txt/_CoqProject book pair: DEDUP keeps the first row of each duplicate group and drops
  the rest; REANCHOR rewrites anchor rows through the `registry_union.apply_reanchor` engine;
  non-mechanical prescriptions pass through to the skip list; opt-in `--orphan-add` executes the
  mechanically solvable ORPHAN-ADD subset. Dry run by default, writes only under `--apply`,
  per-item md5 accounting, in-memory staging, a same-parameter re-audit after the write, and rollback
  from the pre-write backups on any assertion breach.

Interface.  python3 tools/registry_fix.py --audit-json FILE --order PATH --project PATH [--anchor-src
  DIR] [--json FILE] [--apply] [--orphan-add] [--work-dir DIR] [--audit-tool PATH], or --selftest.
  The audit JSON (schema rocqwash-registry-audit/1) must carry a fix_plan and match --order/--project
  verbatim (plan line numbers bind to the audited books); report schema rocqwash-registry-fix/1 is
  sort_keys deterministic, byte-identical on reruns, written even on a blast (rollback evidence inside).

Dependencies.  Python 3 stdlib only, no third-party imports, no network, no build step; peer
  tools/registry_union.py supplies keying, anchor canonical forms, reanchor and A3 engines (imported, never modified; import failure exits 9).

Evidence.  --selftest: eight vectors on canned tmp fixtures (dry-run zero-write; apply with re-audit;
  frozen vector "module A content alpha\\n" -> 77c2b9a8 byte-equal to the registry_union CLI on the
  same input; blast rollback; CLI exit codes; determinism); suite members tests/test_registry_fix_dedup.py,
  test_registry_fix_orphan_add.py, test_registry_fix_anchor.py.

Exit-codes.  0 = dry-run report, or apply with all assertions passing; 1 = --selftest failed; 2 = usage
  error (schema mismatch, no fix_plan, same-parameter breach, entry missing keys) or AssertBlast
  (line out of range, key mismatch, md5 drift, ambiguity, no anchor, A-fix-1..6 breach, write
  integrity), with rollback evidence in the report; 9 = missing input (audit JSON, either book, the
  audit tool, or the anchor-src directory).
"""

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
try:
    import registry_union as _ru  # noqa: E402  (keying/anchor-canonical/reanchor/A3 engines: import only, never modified)
except Exception as _e:  # pragma: no cover
    print("FAIL-LOUD: peer tools/registry_union.py not importable (keying/anchor-canonical/"
          "reanchor engines are imported, never reimplemented): %s" % _e, file=sys.stderr)
    sys.exit(9)

PROG = "registry_fix"
SCHEMA = "rocqwash-registry-fix/1"
AUDIT_SCHEMA = "rocqwash-registry-audit/1"

MD5_PLACEHOLDER = "<MD5_8>"   # audit fix_plan placeholder form (same constant semantics as registry_audit)
SEQ_PLACEHOLDER = "<SEQ>"     # orphan-row sequence placeholder (registry_audit
                              # SEQ_PLACEHOLDER, same constant semantics)
BOOK_KINDS = {"order": _ru.KIND_ORDER, "coqproject": _ru.KIND_COQPROJECT}
DUP_KIND_TO_BOOK = {"dup-order": "order", "dup-coqproject": "coqproject"}
# ORPHAN-ADD prescription direction -> target book (registry_audit
# build_fix_plan contract: order-only rows land in the coqproject book,
# project-only rows would land in the order book).
ORPHAN_DIRECTION_BOOK = {"order-only": "coqproject", "project-only": "order"}
PLACEHOLDER_TOKENS = (MD5_PLACEHOLDER, SEQ_PLACEHOLDER)
# Anchor finding kinds the reanchor stage treats (registry_audit
# build_fix_plan reanchor target face: K_ANCHOR_SEQ / K_ANCHOR_MALFORMED).
REANCHOR_TREATED_KINDS = ("anchor-seq-form", "anchor-malformed")

INJECT_ENV = "ROCWASH_REGISTRY_FIX_INJECT_BLAST"  # injected blast point (selftest only; never set in real runs)


class FailLoud(Exception):
    """Usage error (exit 2, no report; the registry_audit-style FAIL-LOUD short report face)."""


def md5_bytes(b):
    """Full hex md5 of a byte string (basis of the per-item md5 account)."""
    return hashlib.md5(b).hexdigest()


def md5_file(path):
    """Full hex md5 of a file (basis of the on-disk truth account)."""
    h = hashlib.md5()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def dump_json(path, obj):
    """Deterministic JSON write (sort_keys + indent=1, same form as the registry_audit dump_json)."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


# ---------- input loading ----------

def load_audit_payload(path):
    """Load --audit-json and validate its schema (missing input = 9; unparseable or schema mismatch = usage 2)."""
    if not os.path.isfile(path):
        raise _ru.MissingInput("--audit-json file missing: %s" % path)
    try:
        with io.open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception as e:
        raise FailLoud("--audit-json is not parseable JSON: %s" % e)
    if not isinstance(payload, dict):
        raise FailLoud("--audit-json top level must be a JSON object: %s" % path)
    if payload.get("schema") != AUDIT_SCHEMA:
        raise FailLoud("--audit-json schema mismatch: %r (expected %s, as "
                       "produced by registry_audit --fix-plan)"
                       % (payload.get("schema"), AUDIT_SCHEMA))
    return payload


def validate_audit(payload, args):
    """Same-parameter discipline plus audit/plan structure validation (fail-loud usage 2). Returns the fix_plan."""
    inputs = payload.get("inputs") or {}
    if payload.get("mode") != "files" \
            or inputs.get("order") != args.order \
            or inputs.get("project") != args.project:
        raise FailLoud(
            "same-parameter discipline breached: the audit inputs must equal "
            "the executor's two books verbatim (plan line numbers bind to the "
            "audited books) - audit mode=%r inputs.order=%r inputs.project=%r;"
            " executor --order=%r --project=%r"
            % (payload.get("mode"), inputs.get("order"), inputs.get("project"),
               args.order, args.project))
    sections = payload.get("sections")
    if not isinstance(sections, dict):
        raise FailLoud("audit sections missing or not an object (audit self-consistency breached)")
    for k in ("duplicates", "anchors", "orphans"):
        if not isinstance(sections.get(k), list):
            raise FailLoud("audit sections.%s missing or not a list (audit self-consistency breached)" % k)
    plan = payload.get("fix_plan")
    if not isinstance(plan, dict):
        raise FailLoud("audit carries no fix_plan (registry_audit must have "
                       "run with --fix-plan) - the executor has no plan to apply")
    for k in ("dedup", "reanchor", "orphan", "unresolvable"):
        if not isinstance(plan.get(k), list):
            raise FailLoud("fix_plan.%s missing or not a list (audit self-consistency breached)" % k)
    return plan


# ---------- book state ----------

class BookState(object):
    """One book's state: the original read form plus plan evolution (slots
    preserves the original line-number basis; cur is the current form).

    Line endings and the final newline follow the original (probed by
    read_side, rebuilt by render_output; the registry_union engine
    semantics used directly); md5_staged = staged-render byte account of
    the plan evolution.
    """

    def __init__(self, path, label):
        self.path = path
        self.label = label
        self.kind = BOOK_KINDS[label]
        self.orig_lines, self.eol, self.final_nl = _ru.read_side(
            path, "--%s" % label)  # missing input: MissingInput -> exit 9
        self.slots = list(enumerate(self.orig_lines, 1))  # (original audit line number, line)
        self.deleted = set()     # original line numbers already removed by the plan
        self.cur = list(self.orig_lines)

    def apply_deletes(self, orig_nos):
        """Delete rows by the original line-number basis (dedup keep-first; rebuilt once over slots)."""
        self.deleted.update(orig_nos)
        self.cur = [ln for (no, ln) in self.slots if no not in self.deleted]

    def render(self):
        return _ru.render_output(self.cur, self.eol, self.final_nl)

    def md5_staged(self):
        return md5_bytes(self.render())

    def touched(self):
        return self.cur != self.orig_lines


# ---------- plan staging (in memory, zero writes) ----------

def stage_dedup(plan, books, items):
    """① Stage 1 DEDUP keep-first: validate and evolve fix_plan.dedup item by item (original line-number basis; keep=min untouched)."""
    for e in plan["dedup"]:
        if not isinstance(e, dict):
            raise FailLoud("fix_plan.dedup entry is not an object: %r" % (e,))
        book = e.get("book")
        key = e.get("key")
        keep = e.get("keep_line")
        drops = e.get("drop_lines")
        if book not in BOOK_KINDS:
            raise FailLoud("fix_plan.dedup book invalid: %r (must be "
                           "order|coqproject)" % (book,))
        if not isinstance(key, str) or not key:
            raise FailLoud("fix_plan.dedup entry missing key: %r" % (e,))
        if not isinstance(keep, int) or not isinstance(drops, list) \
                or not drops or not all(isinstance(n, int) for n in drops):
            raise FailLoud("fix_plan.dedup entry missing keep_line/drop_lines: "
                           "key=%r" % key)
        bs = books[book]
        for n in [keep] + list(drops):
            if not 1 <= n <= len(bs.slots):
                raise _ru.AssertBlast(
                    "DEDUP-LINE-OUT-OF-RANGE",
                    ["book=%s key=%r line L%d out of range (1..%d) - "
                     "audit-vs-book drift (a stale audit is never silently "
                     "tolerated)" % (book, key, n, len(bs.slots))])
        if _ru.key_of(bs.slots[keep - 1][1], bs.kind) != key:
            raise _ru.AssertBlast(
                "DEDUP-KEEP-KEY-MISMATCH",
                ["book=%s keep=L%s current key %r != plan key %r "
                 "(audit-vs-book drift)"
                 % (book, keep, _ru.key_of(bs.slots[keep - 1][1], bs.kind),
                    key)])
        for n in drops:
            if _ru.key_of(bs.slots[n - 1][1], bs.kind) != key:
                raise _ru.AssertBlast(
                    "DEDUP-DROP-KEY-MISMATCH",
                    ["book=%s drop=L%s current key %r != plan key %r "
                     "(audit-vs-book drift)"
                     % (book, n, _ru.key_of(bs.slots[n - 1][1], bs.kind), key)])
        if keep in drops:
            raise _ru.AssertBlast(
                "DEDUP-KEEP-IN-DROP",
                ["book=%s key=%r keep=L%d is also listed in drop (audit plan "
                 "self-consistency breached)"
                 % (book, key, keep)])
        overlap = sorted(set(drops) & bs.deleted)
        if overlap:
            raise _ru.AssertBlast(
                "DEDUP-DROP-ALREADY-DELETED",
                ["book=%s key=%r drop lines already treated (overlapping plan "
                 "line numbers, audit self-consistency breached): L%s"
                 % (book, key, ",".join(str(n) for n in overlap))])
        before = bs.md5_staged()
        bs.apply_deletes(set(drops))
        items.append({"no": len(items) + 1, "kind": "DEDUP", "book": book,
                      "key": key, "keep_line": keep,
                      "drop_lines": sorted(drops),
                      "md5_before": before, "md5_after": bs.md5_staged()})


def stage_reanchor(plan, books, items, skips, anchor_src):
    """② Stage 2 reanchor: each fix_plan.reanchor item via a direct call to the same registry_union.apply_reanchor engine."""
    bs = books["order"]
    for e in plan["reanchor"]:
        if not isinstance(e, dict):
            raise FailLoud("fix_plan.reanchor entry is not an object: %r" % (e,))
        key = e.get("key")
        if not isinstance(key, str) or not key:
            raise FailLoud("fix_plan.reanchor entry missing key: %r" % (e,))
        bare = _ru.bare_name(key)
        if anchor_src is None:
            skips.append({"kind": "REANCHOR-SKIP-NO-ANCHOR-SRC", "key": key,
                          "reason": "no --anchor-src given to the executor "
                                    "(no md5 source; the row stays as-is on "
                                    "the skip list, the same honesty rule as "
                                    "the wash_shape plan-miss listing)"})
            continue
        before = bs.md5_staged()
        # same-engine reanchor (ambiguous -> UsageError, no anchor ->
        # AssertBlast, both raised as-is: engine semantics)
        out, rewrites, missing, not_in_table = _ru.apply_reanchor(
            bs.cur, [bare], anchor_src, _ru.KIND_ORDER)
        if not_in_table:
            raise _ru.AssertBlast(
                "REANCHOR-KEY-NOT-IN-TABLE",
                ["plan key %r not in the current table (audit-vs-book drift, "
                 "never silently tolerated): %s"
                 % (key, not_in_table)])
        if missing:
            skips.append({"kind": "REANCHOR-SKIP-MISSING-ENTITY", "key": key,
                          "bare": bare,
                          "reason": "no same-named .v entity under anchor-src "
                                    "(row stays as-is on the skip list; "
                                    "nothing is fabricated)"})
            continue
        entity = _ru.resolve_entity(bare, anchor_src)  # missing is empty here, so the entity is not None
        engine_md5 = rewrites[0]["md5_8"] if rewrites else _ru.md5_8_of(entity)
        audit_md5 = e.get("md5_8")
        if audit_md5 and audit_md5 != MD5_PLACEHOLDER and audit_md5 != engine_md5:
            raise _ru.AssertBlast(
                "REANCHOR-MD5-DRIFT",
                ["plan key %r: audit records md5_8=%s but the entity re-hash "
                 "gives %s (audit-vs-entity drift, never silently tolerated)"
                 % (key, audit_md5, engine_md5)])
        bs.cur = out
        items.append({"no": len(items) + 1, "kind": "REANCHOR", "book": "order",
                      "key": key, "bare": bare,
                      "old_anchor": e.get("old_anchor"), "md5_8": engine_md5,
                      "entity": entity,
                      "rewrites": [{"line_no": r["line_index"] + 1,
                                    "old_anchor": r["old_anchor"],
                                    "new_anchor": r["new_anchor"]}
                                   for r in rewrites],
                      "md5_before": before, "md5_after": bs.md5_staged()})


def stage_nons(plan, payload, skips):
    """③ Stage 3 non-mechanical -> skip list, passed through as-is (orphan templates / unresolvable / missing anchors)."""
    for o in plan["orphan"]:
        if not isinstance(o, dict) or not o.get("key"):
            raise FailLoud("fix_plan.orphan entry missing key: %r" % (o,))
        skips.append({"kind": "ORPHAN-ADD-SKIP-NON-MECHANICAL",
                      "key": o.get("key"), "direction": o.get("direction"),
                      "template": o.get("template"),
                      "reason": "the appended-row sequence <SEQ> is a "
                                "registry-side decision; anchors are never "
                                "fabricated mechanically (template passed "
                                "through, same form as the audit prescription)"})
    for u in plan["unresolvable"]:
        skips.append({"kind": "UNRESOLVABLE-PASSTHROUGH", "anchor": u.get("anchor"),
                      "lines": u.get("lines"), "note": u.get("note")})
    for f in (payload.get("sections") or {}).get("anchors") or []:
        if isinstance(f, dict) and f.get("kind") == "anchor-missing":
            skips.append({"kind": "ANCHOR-MISSING-SKIP", "key": f.get("key"),
                          "lines": f.get("lines"),
                          "reason": "the key row carries no anchor (no "
                                    "sequence to inherit; the sequence is a "
                                    "registry-side decision, anchors are "
                                    "never fabricated mechanically)"})


# ---------- ④ ORPHAN-ADD apply path (opt-in --orphan-add) ----------

def stage_orphan_add(plan, books, items, skips):
    """④ ORPHAN-ADD apply path: execute the mechanically solvable subset.

    An order-only prescription (target book coqproject, whose rows carry
    no anchor) with a placeholder-free template is executed by appending
    the template row to the coqproject book tail, one row per
    prescription, in plan order, with the same per-item md5 accounting as
    the DEDUP/REANCHOR stages. Guards (fail-loud):
      - plan contract: template must be a ".v" row and must hash to the
        prescription key under the coqproject keying (FailLoud on breach);
      - audit-vs-book drift: the key must be present in the order book
        (.v basename criterion, the audit orphan account source), else
        AssertBlast ORPHAN-ADD-KEY-NOT-IN-ORDER (stale-audit discipline
        of the DEDUP stage);
      - already-registered signature: a coqproject row already hashing
        to the key under the coqproject keying (for example an
        extension-less module row that the audit .v-suffix criterion
        cannot see) routes the entry to the skip list as
        ORPHAN-ADD-SKIP-KEY-PRESENT for human adjudication instead of
        double-registering the module;
      - suffix-typo signature: a project-only entry whose key equals the
        order-only key after stripping repeated ".v" suffixes (e.g. order
        "X.v" vs coqproject "X.v.v") means the module is already
        registered under a misspelled row; the entry is skipped as
        ORPHAN-ADD-SKIP-SUFFIX-TWIN for human adjudication instead of
        double-registering the module.
    Order-only entries carrying placeholders and every project-only entry
    are left in the returned residual list, so the existing non-mechanical
    passthrough (stage_nons) reports them with its own skip kind
    unchanged. Callers must invoke this stage after stage_dedup /
    stage_reanchor and feed the residual list to stage_nons, because the
    appended rows live in books["coqproject"].cur outside the original
    line-number slots that apply_deletes rebuilds from.
    Returns the residual (non-executed) orphan entry list.
    """
    bs = books["coqproject"]
    order_bases = set()
    for _no, ln in books["order"].slots:
        k = _ru.key_of(ln, _ru.KIND_ORDER)
        if k is not None and k.endswith(".v"):
            order_bases.add(_ru.bare_name(k).rsplit("/", 1)[-1])
    twins = {}
    for o in plan["orphan"]:
        if not isinstance(o, dict) or not o.get("key"):
            raise FailLoud("fix_plan.orphan entry missing key: %r" % (o,))
        if o.get("direction") == "project-only":
            k = o["key"]
            while isinstance(k, str) and k.endswith(".v"):
                k = k[:-2]
            if k in order_bases:
                twins[k] = o["key"]
    residual = []
    for o in plan["orphan"]:
        key = o["key"]
        direction = o.get("direction")
        template = o.get("template")
        if key in twins:
            skips.append({"kind": "ORPHAN-ADD-SKIP-SUFFIX-TWIN",
                          "key": key, "direction": direction,
                          "template": template, "twin_key": twins[key],
                          "reason": "paired project-only registration under "
                                    "a repeated-.v spelling (e.g. X.v.v): "
                                    "the module is already registered, "
                                    "appending a second spelling would "
                                    "double-register it; left for human "
                                    "adjudication"})
            continue
        if direction == "order-only" \
                and ORPHAN_DIRECTION_BOOK.get(direction) == "coqproject":
            if not isinstance(template, str) or not template.endswith(".v"):
                raise FailLoud("fix_plan.orphan order-only template must be "
                               "a .v row: key=%r template=%r"
                               % (key, template))
            if any(ph in template for ph in PLACEHOLDER_TOKENS):
                residual.append(o)   # non-mechanical passthrough (stage_nons)
                continue
            if _ru.key_of(template, _ru.KIND_COQPROJECT) != key:
                raise FailLoud("fix_plan.orphan template/key mismatch under "
                               "the coqproject keying: key=%r template=%r"
                               % (key, template))
            if key not in order_bases:
                raise _ru.AssertBlast(
                    "ORPHAN-ADD-KEY-NOT-IN-ORDER",
                    ["book=order has no .v basename %r (audit orphan account "
                     "source face) - audit-vs-book drift, stale audit is not "
                     "silently tolerated" % key])
            present = [i for i, ln in enumerate(bs.cur, 1)
                       if _ru.key_of(ln, _ru.KIND_COQPROJECT) == key]
            if present:
                skips.append({"kind": "ORPHAN-ADD-SKIP-KEY-PRESENT",
                              "key": key, "direction": direction,
                              "template": template, "present_lines": present,
                              "reason": "the target book already carries a "
                                        "row hashing to this key under the "
                                        "coqproject keying (for example an "
                                        "extension-less module row that the "
                                        "audit .v-suffix criterion cannot "
                                        "see); appending would "
                                        "double-register the module; left "
                                        "for human adjudication"})
                continue
            before = bs.md5_staged()
            bs.cur.append(template)
            items.append({"no": len(items) + 1, "kind": "ORPHAN-ADD",
                          "book": "coqproject", "key": key, "row": template,
                          "line_no": len(bs.cur),
                          "md5_before": before, "md5_after": bs.md5_staged()})
        else:
            residual.append(o)       # project-only: non-mechanical passthrough
    return residual


# ---------- write / assertions / rollback ----------

def backup_and_write(books, work_dir):
    """The --apply write face: back up each book, write it, then reconcile the
    on-disk md5 against the staged account.

    The write face is exactly the two books named on the command line plus
    the work-dir backups; a write-integrity blast is an AssertBlast (the
    main flow rolls back).
    """
    os.makedirs(work_dir, exist_ok=True)
    out = []
    for label in sorted(BOOK_KINDS):  # coqproject < order (deterministic order)
        bs = books[label]
        if not bs.touched():
            continue
        on_disk_before = md5_file(bs.path)
        backup = os.path.join(work_dir, "%s.%s.bak" % (label,
                                                       os.path.basename(bs.path)))
        shutil.copy2(bs.path, backup)
        if md5_file(backup) != on_disk_before:
            raise _ru.AssertBlast("BACKUP-INTEGRITY",
                                  ["%s backup md5 != md5 of the original "
                                   "on-disk file (backup integrity breached; "
                                   "write refused)" % bs.path])
        with io.open(bs.path, "wb") as fh:
            fh.write(bs.render())
        on_disk_after = md5_file(bs.path)
        if on_disk_after != bs.md5_staged():
            raise _ru.AssertBlast("WRITE-INTEGRITY",
                                  ["%s on-disk md5 after write %s != staged "
                                   "account %s (write integrity breached)"
                                   % (bs.path, on_disk_after, bs.md5_staged())])
        out.append({"book": label, "path": bs.path, "eol": bs.eol,
                    "final_nl": bs.final_nl,
                    "rows_before": len(bs.orig_lines),
                    "rows_after": len(bs.cur),
                    "md5_on_disk_before": on_disk_before,
                    "md5_on_disk_after": on_disk_after,
                    "backup": backup, "backup_md5": md5_file(backup)})
    return out


def rollback(writes):
    """Restore on any blast: copy each book back from its backup byte-for-byte and reconcile the md5 against the pre-write value (evidence goes into the report)."""
    restored = {}
    all_ok = True
    for w in writes:
        shutil.copy2(w["backup"], w["path"])
        m = md5_file(w["path"])
        ok = (m == w["md5_on_disk_before"])
        all_ok = all_ok and ok
        restored[w["book"]] = {"path": w["path"], "md5_restored": m,
                               "match": ok}
    return {"backups": {w["book"]: w["backup"] for w in writes},
            "restored": restored, "all_restored": all_ok}


def run_assertions(audit_payload, books, treated, args, audit_tool, work_dir):
    """The three assertions (after --apply): the A3 engine called directly, plus a registry_audit re-run at the same parameters."""
    # A-fix-2 no new anchor-text collisions (registry_union A3 engine called
    # directly; post vs pre)
    _ru.assert_anchor_no_new_dups(books["order"].cur, books["order"].orig_lines)
    # re-run registry_audit at the same parameters (no --fix-plan re-emission;
    # the assertions read the four accounts only)
    if not os.path.isfile(audit_tool):
        raise _ru.MissingInput("audit tool missing: %s" % audit_tool)
    post_path = os.path.join(work_dir, "post_audit.json")
    cmd = [sys.executable, "-B", audit_tool,
           "--order", args.order, "--project", args.project]
    if args.anchor_src:
        cmd += ["--anchor-src", args.anchor_src]
    cmd += ["--json", post_path]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        raise _ru.AssertBlast("ASSERT-REAUDIT-FAILED",
                              ["registry_audit re-run rc=%d: %s"
                               % (p.returncode,
                                  p.stdout.decode("utf-8", errors="replace")
                                  [-800:])])
    with io.open(post_path, encoding="utf-8") as fh:
        post = json.load(fh)
    if post.get("schema") != AUDIT_SCHEMA:
        raise _ru.AssertBlast("ASSERT-REAUDIT-SCHEMA",
                              ["re-run audit schema mismatch: %r"
                               % post.get("schema")])
    # A-fix-1 treated keys have duplicates=0 after the re-audit
    hits = ["%s/%s" % (f["kind"], f["key"])
            for f in post["sections"]["duplicates"]
            if (DUP_KIND_TO_BOOK.get(f["kind"]), f.get("key")) in treated]
    if hits:
        raise _ru.AssertBlast("ASSERT-TREATED-DUP-NONZERO",
                              ["treated keys still carry duplicate findings "
                               "after the re-audit: %s" % h for h in hits])
    # A-fix-3 the orphan account does not grow
    pre_keys = {(f.get("kind"), f.get("key"))
                for f in audit_payload["sections"]["orphans"]}
    post_keys = {(f.get("kind"), f.get("key"))
                 for f in post["sections"]["orphans"]}
    new = sorted("%s/%s" % kv for kv in (post_keys - pre_keys))
    if new:
        raise _ru.AssertBlast("ASSERT-ORPHAN-NEW",
                              ["the orphan account gained new entries: %s"
                               % k for k in new])
    return {"ran": True, "anchor_text_no_new_dups": "PASS",
            "treated_duplicates_zero": "PASS", "orphans_no_new": "PASS",
            "reaudit_summary": post["summary"], "reaudit_inputs": post["inputs"]}


def assert_orphan_add_resolved(post_audit_path, executed_keys):
    """ORPHAN-ADD post-apply assertions (A-fix-4 / A-fix-5).

    Reads the post-apply audit JSON that run_assertions re-ran at the same
    parameters (work-dir post_audit.json) and asserts, for every executed
    orphan key:
      A-fix-4  orphans_resolved            no orphan-order-only finding
                                           survives for the key;
      A-fix-5  orphan_add_duplicates_zero  the appended row created no
                                           duplicate-key finding.
    Any breach is an AssertBlast like the other assertion blasts (the
    caller's rollback path applies unchanged).
    """
    with io.open(post_audit_path, encoding="utf-8") as fh:
        post = json.load(fh)
    resid = sorted(f.get("key") for f in post["sections"]["orphans"]
                   if f.get("kind") == "orphan-order-only"
                   and f.get("key") in executed_keys)
    dups = sorted(f.get("key") for f in post["sections"]["duplicates"]
                  if f.get("kind") == "dup-coqproject"
                  and f.get("key") in executed_keys)
    if resid:
        raise _ru.AssertBlast(
            "ASSERT-ORPHAN-ADD-RESIDUAL",
            ["treated orphan key still unresolved post-apply: %s" % k
             for k in resid])
    if dups:
        raise _ru.AssertBlast(
            "ASSERT-ORPHAN-ADD-DUP",
            ["appended row created a duplicate-key finding: %s" % k
             for k in dups])
    return {"orphans_resolved": "PASS",
            "orphan_add_duplicates_zero": "PASS"}


def assert_treated_anchors_canonical(post, treated_keys):
    """REANCHOR post-apply residual gate (A-fix-6 treated_anchors_canonical).

    Reads the same post-apply audit JSON the A-fix face already re-ran at
    the same parameters and asserts, for every executed REANCHOR key, that
    no anchor finding of the reanchor target kinds (anchor-seq-form /
    anchor-malformed, registry_audit build_fix_plan's own target face)
    survives. The audit producer's classification is the whole oracle; no
    anchor semantics are defined here. Scope is the executed keys only:
    skip-list keys (missing entity, missing anchor) keep their rows by
    design and the collision face stays owned by A-fix-2. Any breach is
    an AssertBlast (ASSERT-TREATED-ANCHOR-NONZERO) and the caller's
    rollback path applies unchanged.
    """
    resid = sorted("%s/%s" % (f.get("kind"), f.get("key"))
                   for f in post["sections"]["anchors"]
                   if f.get("kind") in REANCHOR_TREATED_KINDS
                   and f.get("key") in treated_keys)
    if resid:
        raise _ru.AssertBlast(
            "ASSERT-TREATED-ANCHOR-NONZERO",
            ["treated anchor key still carries an anchor finding "
             "(audit-vs-book drift or reanchor regression): %s" % k
             for k in resid])
    return {"treated_anchors_canonical": "PASS"}


# ---------- report ----------

def build_report(args, audit_payload, plan, books, items, skips, writes,
                 assertions, blast):
    """The report (schema rocqwash-registry-fix/1, sort_keys deterministic)."""
    summ = audit_payload.get("summary") or {}
    executed_dedup = sum(1 for it in items if it["kind"] == "DEDUP")
    executed_reanchor = sum(1 for it in items if it["kind"] == "REANCHOR")
    executed_orphan_add = sum(1 for it in items if it["kind"] == "ORPHAN-ADD")
    skip_by_kind = {}
    for s in skips:
        skip_by_kind[s["kind"]] = skip_by_kind.get(s["kind"], 0) + 1
    touched = sorted(label for label, bs in books.items() if bs.touched())
    report = {
        "schema": SCHEMA,
        "mode": "APPLY" if args.apply else "DRY-RUN",
        "inputs": {"audit_json": args.audit_json, "order": args.order,
                   "project": args.project,
                   "anchor_src": args.anchor_src,
                   "audit_tool": args.audit_tool,
                   "orphan_add": bool(args.orphan_add)},
        "audit_input_meta": {"schema": audit_payload.get("schema"),
                             "mode": audit_payload.get("mode"),
                             "anchor_src": audit_payload.get("anchor_src"),
                             "summary": summ},
        "engine": ("direct calls into registry_union.apply_reanchor / "
                   "assert_anchor_no_new_dups (keying/anchor-canonical/"
                   "reanchor/A3 engines reused, none reimplemented)"),
        "stats": {
            "planned": {"dedup": len(plan["dedup"]),
                        "reanchor": len(plan["reanchor"]),
                        "orphan": len(plan["orphan"]),
                        "unresolvable": len(plan["unresolvable"])},
            "items_total": len(items),
            "items_executed_dedup": executed_dedup,
            "items_executed_reanchor": executed_reanchor,
            "items_executed_orphan_add": executed_orphan_add,
            "skips_total": len(skips),
            "skips_by_kind": {k: skip_by_kind[k] for k in sorted(skip_by_kind)},
            "rows": {"order_before": len(books["order"].orig_lines),
                     "order_after": len(books["order"].cur),
                     "coqproject_before": len(books["coqproject"].orig_lines),
                     "coqproject_after": len(books["coqproject"].cur)},
            "md5_basis": "per-item md5 = staged-render bytes of the plan "
                         "evolution (read_side/render_output engine semantics; "
                         "line endings and the final newline follow the "
                         "original); writes.books md5 = on-disk truth",
        },
        "items": items,
        "skip": skips,
        "writes": writes,
        "assertions": assertions,
        "blast": blast,
        "summary": {
            "mode": "APPLY" if args.apply else "DRY-RUN",
            "items_total": len(items),
            "items_executed": (executed_dedup + executed_reanchor
                               + executed_orphan_add),
            "skips_total": len(skips),
            "books_touched": sorted(touched),
            "rolled_back": bool(writes and writes.get("rolled_back")),
            "assertions": ("PASS" if assertions and assertions.get("ran")
                           else "NOT-RUN (dry run writes nothing; assertions "
                                "not applicable)"
                           if not args.apply else "BLAST"),
        },
    }
    return report


def print_stdout(rep):
    """The loud stdout account (deterministic; items / skip list / writes / assertions all listed)."""
    print("=== REGISTRY-FIX (%s·%s) ===" % (rep["mode"], SCHEMA))
    for k in sorted(rep["inputs"]):
        print("  %s=%s" % (k, rep["inputs"][k] or "(not given)"))
    aim = rep["audit_input_meta"]["summary"] or {}
    print("audit side evidence: duplicates=%s anchors=%s orphans=%s "
          "total=%s (mode=%s)"
          % (aim.get("duplicates"), aim.get("anchors"), aim.get("orphans"),
             aim.get("total"), rep["audit_input_meta"].get("mode")))
    st = rep["stats"]
    print("plan: dedup=%d reanchor=%d (planned orphan=%d unresolvable=%d)"
          % (st["planned"]["dedup"], st["planned"]["reanchor"],
             st["planned"]["orphan"], st["planned"]["unresolvable"]))
    print("--- plan items (%d items; md5 account = staged-render bytes) ---"
          % len(rep["items"]))
    for it in rep["items"]:
        if it["kind"] == "DEDUP":
            print("  #%d %s DEDUP book=%s key=%s keep=L%d drop=L%s  "
                  "md5 %s->%s"
                  % (it["no"], "APPLIED" if rep["mode"] == "APPLY"
                     else "DRY-STAGED", it["book"], it["key"], it["keep_line"],
                     ",".join("L%d" % n for n in it["drop_lines"]),
                     it["md5_before"][:8], it["md5_after"][:8]))
        elif it["kind"] == "ORPHAN-ADD":
            print("  #%d %s ORPHAN-ADD book=%s key=%s row=%s ->L%d  "
                  "md5 %s->%s"
                  % (it["no"], "APPLIED" if rep["mode"] == "APPLY"
                     else "DRY-STAGED", it["book"], it["key"], it["row"],
                     it["line_no"], it["md5_before"][:8],
                     it["md5_after"][:8]))
        else:
            rws = it["rewrites"]
            print("  #%d %s REANCHOR key=%s %s->%s (entity %s, %d rows "
                  "rewritten)  md5 %s->%s"
                  % (it["no"], "APPLIED" if rep["mode"] == "APPLY"
                     else "DRY-STAGED", it["key"],
                     rws[0]["old_anchor"] if rws else it["old_anchor"],
                     rws[0]["new_anchor"] if rws else "(already canonical)",
                     it["entity"], len(rws),
                     it["md5_before"][:8], it["md5_after"][:8]))
    print("--- skip list (%d items, passed through as-is) ---" % len(rep["skip"]))
    for s in rep["skip"]:
        if s["kind"] == "REANCHOR-SKIP-MISSING-ENTITY":
            print("  %s %s: %s" % (s["kind"], s["key"], s["reason"]))
        elif s["kind"] == "ORPHAN-ADD-SKIP-NON-MECHANICAL":
            print("  %s %s (%s): template=%s"
                  % (s["kind"], s["key"], s.get("direction") or "-",
                     s.get("template")))
        elif s["kind"] == "ORPHAN-ADD-SKIP-SUFFIX-TWIN":
            print("  %s %s (twin %s): template=%s"
                  % (s["kind"], s["key"], s.get("twin_key") or "-",
                     s.get("template")))
        elif s["kind"] == "ORPHAN-ADD-SKIP-KEY-PRESENT":
            print("  %s %s (present L%s): template=%s"
                  % (s["kind"], s["key"],
                     ",".join(str(x) for x in s.get("present_lines") or []),
                     s.get("template")))
        elif s["kind"] == "UNRESOLVABLE-PASSTHROUGH":
            print("  %s anchor %s L%s: %s"
                  % (s["kind"], s.get("anchor"),
                     ",".join(str(x) for x in (s.get("lines") or [])),
                     s.get("note") or ""))
        elif s["kind"] == "ANCHOR-MISSING-SKIP":
            print("  %s %s L%s: %s"
                  % (s["kind"], s.get("key"),
                     ",".join(str(x) for x in (s.get("lines") or [])),
                     s.get("reason") or ""))
        else:
            print("  %s %s: %s" % (s["kind"], s.get("key"),
                                   s.get("reason") or ""))
    if rep["writes"] is not None:
        wr = rep["writes"]
        print("--- writes (%d books%s) ---"
              % (len(wr.get("books") or []),
                 ", rolled back" if wr.get("rolled_back") else ""))
        for w in wr.get("books") or []:
            print("  %s %s rows %d->%d md5 %s->%s (backup %s)"
                  % (w["book"], w["path"], w["rows_before"], w["rows_after"],
                     w["md5_on_disk_before"][:8], w["md5_on_disk_after"][:8],
                     w["backup"]))
    else:
        print("--- writes: zero writes (dry run, or staging blast before any "
              "write) ---")
    an = rep["assertions"]
    if an is None:
        print("--- assertions: NOT-RUN (%s) ---"
              % ("dry run writes nothing; assertions not applicable (same "
                 "honesty rule as the push_gate NOT-RUN entry)"
                 if rep["mode"] == "DRY-RUN" else
                 "staging blast before any write; assertions not reached"))
    elif an.get("ran"):
        print("--- assertions (registry_audit re-run at the same parameters) "
              "---")
        print("  treated_duplicates_zero=PASS anchor_text_no_new_dups=PASS "
              "orphans_no_new=PASS")
        if an.get("orphans_resolved"):
            print("  orphans_resolved=%s orphan_add_duplicates_zero=%s"
                  % (an["orphans_resolved"],
                     an["orphan_add_duplicates_zero"]))
        if an.get("treated_anchors_canonical"):
            print("  treated_anchors_canonical=%s"
                  % an["treated_anchors_canonical"])
    else:
        print("--- assertions: NOT-RUN (%s) ---" % an.get("reason"))
    bl = rep["blast"]
    if bl:
        print("BLAST %s (%s, rc=2):" % (bl.get("code"), bl.get("phase")))
        for it in bl.get("items") or []:
            print("  - %s" % it)
    summ = rep["summary"]
    print("REGISTRY-FIX: executed=%d skipped=%d books_touched=%s "
          "rolled_back=%s assertions=%s"
          % (summ["items_executed"], summ["skips_total"],
             ",".join(summ["books_touched"]) or "-", summ["rolled_back"],
             summ["assertions"]))


# ---------- main flow ----------

def run_fix(args):
    """Main flow -> (report, exit_code). AssertBlast is contained here (rollback already done; evidence in the report)."""
    audit_payload = load_audit_payload(args.audit_json)
    if args.anchor_src is not None and not os.path.isdir(args.anchor_src):
        raise _ru.MissingInput("--anchor-src directory missing: %s" % args.anchor_src)
    books = {"order": BookState(args.order, "order"),
             "coqproject": BookState(args.project, "coqproject")}
    plan = validate_audit(audit_payload, args)  # same-parameter check runs after the books load (missing book = 9 before same-parameter breach = 2)
    if args.apply:
        if not os.path.isfile(args.audit_tool):
            raise _ru.MissingInput("audit tool missing: %s" % args.audit_tool)

    items, skips = [], []
    writes = None
    assertions = None
    executed_orphan_keys = set()
    try:
        stage_dedup(plan, books, items)
        stage_reanchor(plan, books, items, skips, args.anchor_src)
        if args.orphan_add:
            residual_orphans = stage_orphan_add(plan, books, items, skips)
            executed_orphan_keys = {
                it["key"] for it in items if it["kind"] == "ORPHAN-ADD"}
            stage_nons(dict(plan, orphan=residual_orphans), audit_payload,
                       skips)
        else:
            stage_nons(plan, audit_payload, skips)
    except _ru.AssertBlast as e:
        blast = {"code": e.code, "phase": "stage (zero writes; books untouched)",
                 "items": list(e.items)}
        report = build_report(args, audit_payload, plan, books, items, skips,
                              None, None, blast)
        print("ASSERT-BLAST %s (staging, exit 2, zero writes):" % e.code,
              file=sys.stderr)
        for it in e.items:
            print("  - %s" % it, file=sys.stderr)
        return report, 2

    if not args.apply:
        report = build_report(args, audit_payload, plan, books, items, skips,
                              None,
                              {"ran": False,
                               "reason": "dry run writes nothing; assertions "
                                         "not applicable (they run only after "
                                         "--apply, re-running the audit at the "
                                         "same parameters)"},
                              None)
        return report, 0

    work_dir = args.work_dir or tempfile.mkdtemp(prefix="rocqwash_rf_")
    treated = {(it["book"], it["key"]) for it in items if it["kind"] == "DEDUP"}
    try:
        writes = {"books": backup_and_write(books, work_dir),
                  "rolled_back": False}
        if os.environ.get(INJECT_ENV, "").strip() == "post-write":
            raise _ru.AssertBlast(
                "INJECTED-POST-WRITE-BLAST",
                ["injected blast point (%s=post-write; selftest only, never "
                 "set in real runs)" % INJECT_ENV])
        assertions = run_assertions(audit_payload, books, treated, args,
                                    args.audit_tool, work_dir)
        # A-fix-6: executed reanchor keys leave no residual anchor findings
        # (same post_audit.json the assertion face just re-ran)
        executed_anchor_keys = {it["key"] for it in items
                                if it["kind"] == "REANCHOR"}
        if executed_anchor_keys:
            with io.open(os.path.join(work_dir, "post_audit.json"),
                         encoding="utf-8") as fh:
                assertions.update(assert_treated_anchors_canonical(
                    json.load(fh), executed_anchor_keys))
        if executed_orphan_keys:
            assertions.update(assert_orphan_add_resolved(
                os.path.join(work_dir, "post_audit.json"),
                executed_orphan_keys))
    except _ru.AssertBlast as e:
        ev = rollback(writes["books"]) if writes["books"] else {
            "backups": {}, "restored": {}, "all_restored": True}
        writes["rolled_back"] = True
        blast = {"code": e.code, "phase": "apply (written, then rolled back)",
                 "items": list(e.items)}
        report = build_report(args, audit_payload, plan, books, items, skips,
                              writes,
                              {"ran": False,
                               "reason": "assertion blast; no PASS after "
                                         "rollback (%s)" % e.code},
                              blast)
        report["rollback_evidence"] = ev
        print("ASSERT-BLAST %s (exit 2, rolled back):" % e.code, file=sys.stderr)
        for it in e.items:
            print("  - %s" % it, file=sys.stderr)
        print("rollback: %s (all_restored=%s)"
              % (sorted(ev["backups"]), ev["all_restored"]), file=sys.stderr)
        return report, 2
    except OSError as e:
        ev = rollback(writes["books"]) if writes["books"] else {
            "backups": {}, "restored": {}, "all_restored": True}
        writes["rolled_back"] = True
        blast = {"code": "IO-BLAST", "phase": "apply (written, then rolled back)",
                 "items": ["OSError: %s" % e]}
        report = build_report(args, audit_payload, plan, books, items, skips,
                              writes,
                              {"ran": False,
                               "reason": "IO blast; no PASS after rollback"},
                              blast)
        report["rollback_evidence"] = ev
        print("ASSERT-BLAST IO-BLAST (exit 2, rolled back): %s" % e, file=sys.stderr)
        return report, 2

    report = build_report(args, audit_payload, plan, books, items, skips,
                          writes, assertions, None)
    return report, 0


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="registry fix-plan executor: applies the registry_audit "
                    "fix-plan item by item (DEDUP keep-first, reanchor via "
                    "the registry_union engine, non-mechanical prescriptions "
                    "passed through to the skip list), then re-runs the "
                    "assertions; any blast rolls back (dry run by default, "
                    "writes only under --apply)")
    ap.add_argument("--audit-json", default=None, metavar="FILE",
                    help="registry_audit output (rocqwash-registry-audit/1, "
                         "must come from --fix-plan)")
    ap.add_argument("--order", default=None, metavar="PATH",
                    help="order.txt book (paired with --project; must match "
                         "the audit parameters)")
    ap.add_argument("--project", default=None, metavar="PATH",
                    help="_CoqProject book (paired with --order; must match "
                         "the audit parameters)")
    ap.add_argument("--anchor-src", default=None, metavar="DIR",
                    help="entity source directory for reanchor md5 (keys "
                         "with missing entities stay as-is on the skip list)")
    ap.add_argument("--apply", action="store_true",
                    help="allow writing (dry run by default with zero writes; "
                         "pre-write backups; rollback on any blast)")
    ap.add_argument("--orphan-add", action="store_true",
                    help="execute the mechanically solvable ORPHAN-ADD "
                         "prescriptions (order-only direction: append the "
                         "template row to the coqproject book); default off "
                         "keeps every ORPHAN-ADD prescription on the skip "
                         "list (frozen legacy behavior)")
    ap.add_argument("--work-dir", default=None, metavar="DIR",
                    help="directory for the backups and the re-run audit "
                         "output (--apply only; mkdtemp by default)")
    ap.add_argument("--audit-tool", default=None, metavar="PATH",
                    help="path to registry_audit.py (default: the peer "
                         "tools/ directory)")
    ap.add_argument("--json", default=None, metavar="FILE",
                    help="report output path (schema rocqwash-registry-fix/1; "
                         "written even on a blast, carrying rollback evidence)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    def die(msg, code):
        print("FAIL-LOUD: %s" % msg, file=sys.stderr)
        sys.exit(code)

    if not args.audit_json:
        die("no input: --audit-json is required (output of registry_audit "
            "--fix-plan)", 2)
    if (args.order is None) != (args.project is None):
        die("--order and --project must be given as a pair (two-book "
            "convention; neither may be omitted)", 2)
    if not args.order:
        die("no input: both books --order and --project are required", 2)
    args.audit_tool = args.audit_tool or os.path.join(
        _TOOLS_DIR, "registry_audit.py")

    try:
        report, code = run_fix(args)
    except _ru.MissingInput as e:
        die(str(e), 9)
    except FailLoud as e:
        die(str(e), 2)
    except _ru.UsageError as e:
        die("engine usage error: %s" % e, 2)

    print_stdout(report)
    if args.json:
        try:
            dump_json(args.json, report)
            print("json -> %s" % args.json)
        except OSError as e:
            die("failed to write the --json report: %s" % e, 2)
    sys.exit(code)


# ---------- selftest ----------

FIXTURE_ORDER = [
    "ToyA.v#R3-ffffff",        # L1  malformed 6-hex form -> reanchor (entity = frozen vector 77c2b9a8)
    "SeqB.v#R7",               # L2  seq form -> reanchor (entity present)
    "Ghost.v#R9-abcabc",       # L3  malformed, entity missing -> skip list
    "NoEnt.v#R11",             # L4  seq form, entity missing -> skip list
    "CollA.v#R0-d66910",       # L5  malformed anchor collision -> resolved by reanchor
    "CollB.v#R0-d66910",       # L6  malformed anchor collision -> resolved by reanchor (distinct content)
    "MissAnchor.v",            # L7  no anchor -> skip list (non-mechanical)
    "CanA.v#R0-11111111",      # L8  canonical anchor collision -> unresolvable passthrough
    "CanB.v#R0-11111111",      # L9  canonical anchor collision -> unresolvable passthrough
    "OrphO.v#R5-aaaa0001",     # L10 orphan (order-only) -> ORPHAN-ADD skip
    "# comment line",          # L11 comment (key None, not in the account)
] + ["M%02d.v#R21-aaaa%04x" % (i, i) for i in range(1, 13)]  # L12-L23

FIXTURE_PROJECT_HEAD = [
    '-Q . ""',                 # L1  flag line (filtered out)
    "ToyA.v", "SeqB.v", "Ghost.v", "NoEnt.v", "CollA.v", "CollB.v",
    "MissAnchor.v", "CanA.v", "CanB.v", "OrphP.v",     # L2-L11 (OrphP is the project-only orphan)
]
FIXTURE_PROJECT_DUP = ["M%02d.v" % i for i in range(1, 13)]  # 12 verbatim duplicate rows


def build_fixture(base, shared=False):
    """The canned audit-demo fixture shape (world entities plus the two books; zero real-repo contact, zero network).

    shared=True adds SameC/SameD (same content under two keys, distinct
    malformed anchors): the natural A-fix-2 blast-point fixture.
    Returns (order_path, project_path, world_dir).
    """
    world = os.path.join(base, "world")
    os.makedirs(world)
    ents = {"ToyA.v": "module A content alpha\n",   # registry_union frozen vector
            "SeqB.v": "module SeqB beta\n",
            "CollA.v": "module CollA one\n",
            "CollB.v": "module CollB two\n",
            "OrphP.v": "module OrphP\n"}
    if shared:
        ents["SameC.v"] = "module Same shared\n"
        ents["SameD.v"] = "module Same shared\n"   # same content = the reanchor new-collision blast point
    for name in sorted(ents):
        with io.open(os.path.join(world, name), "wb") as fh:
            fh.write(ents[name].encode("utf-8"))
    order_rows = list(FIXTURE_ORDER)
    project_rows = list(FIXTURE_PROJECT_HEAD) + FIXTURE_PROJECT_DUP * 2
    if shared:
        order_rows += ["SameC.v#R0-aaaaaa", "SameD.v#R0-bbbbbb"]
        project_rows += ["SameC.v", "SameD.v"]
    order_path = os.path.join(base, "order.txt")
    project_path = os.path.join(base, "_CoqProject")
    with io.open(order_path, "wb") as fh:
        fh.write(("\n".join(order_rows) + "\n").encode("utf-8"))
    with io.open(project_path, "wb") as fh:
        fh.write(("\n".join(project_rows) + "\n").encode("utf-8"))
    return order_path, project_path, world


def selftest():
    """Embedded vector set (tmp fixtures in the canned audit-demo shape;
    zero real-repo contact, zero network, zero compile):

    1 dry-run zero-write, per-item md5 account, full skip-class spectrum,
      byte-identical dry-run report on re-run
    2 --apply: the 12 duplicate rows -> 0, three assertions pass, the md5
      account reconciles against the on-disk books
    3 reanchor frozen md5 vector 77c2b9a8 plus same-input-same-output
      (byte-equal against the registry_union CLI)
    4 rollback proof with the injected blast point (post-write -> restored)
    5 natural blast point (same-content reanchor new collision -> the A3
      engine raises -> rolled back)
    6 staging blast (audit-vs-book drift, zero writes, no work-dir)
    7 CLI exit-code matrix plus the schema face
    8 apply determinism (two fresh fixtures: identical book bytes and md5
      accounts)
    """
    import tempfile

    here = os.path.dirname(os.path.abspath(__file__))
    fix_py = os.path.join(here, PROG + ".py")
    audit_py = os.path.join(here, "registry_audit.py")
    union_py = os.path.join(here, "registry_union.py")

    def run(argv, env_extra=None):
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        p = subprocess.run([sys.executable, "-B", fix_py] + argv,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           env=env)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def run_audit(order_p, project_p, world, json_p, fix_plan=True):
        argv = [sys.executable, "-B", audit_py, "--order", order_p,
                "--project", project_p, "--anchor-src", world,
                "--json", json_p]
        if fix_plan:
            argv.append("--fix-plan")
        p = subprocess.run(argv, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        assert p.returncode == 0, "audit run should rc=0, got %d\n%s" % (
            p.returncode, p.stdout)
        with io.open(json_p, encoding="utf-8") as fh:
            return json.load(fh)

    def wf(path, text):
        with io.open(path, "wb") as fh:
            fh.write(text.encode("utf-8"))
        return path

    def md5_of(path):
        return md5_file(path)

    def tree_md5(root):
        """Content fingerprint of a directory tree (zero-write side evidence; the sorted (relpath, md5) sequence)."""
        rows = []
        for dirpath, _dirs, fnames in os.walk(root):
            for fn in sorted(fnames):
                p = os.path.join(dirpath, fn)
                rows.append((os.path.relpath(p, root), md5_of(p)))
        return sorted(rows)

    tmp = tempfile.mkdtemp(prefix="rocqwash_rf_self_")
    try:
        # frozen-vector guard (engine md5 precondition: the registry_union
        # frozen sample content hashes to 77c2b9a8)
        d0 = os.path.join(tmp, "vec0")
        os.makedirs(d0)
        wf(os.path.join(d0, "ToyA.v"), "module A content alpha\n")
        assert _ru.md5_8_of(os.path.join(d0, "ToyA.v")) == "77c2b9a8", \
            "registry_union frozen vector broken (content -> md5-8)"

        # ---- vector 1: dry-run zero-write + per-item md5 account + full skip spectrum + determinism ----
        d1 = os.path.join(tmp, "vec1")
        os.makedirs(d1)
        o1, p1, w1 = build_fixture(d1)
        a1 = run_audit(o1, p1, w1, os.path.join(d1, "audit.json"))
        pre_tree = tree_md5(d1)  # zero-write baseline (taken after the audit writes its json, which is included)
        assert a1["summary"]["duplicates"] == 12, a1["summary"]
        assert a1["summary"]["anchors"] == 9, a1["summary"]
        assert a1["summary"]["orphans"] == 2, a1["summary"]
        assert a1["summary"]["total"] == 23, a1["summary"]
        r1 = os.path.join(tmp, "rep1.json")
        p = run(["--audit-json", os.path.join(d1, "audit.json"),
                 "--order", o1, "--project", p1, "--anchor-src", w1,
                 "--json", r1])
        assert p.returncode == 0, "dry run should rc=0, got %d\n%s" % (
            p.returncode, p.stdout)
        assert tree_md5(d1) == pre_tree, "dry run wrote to disk (fixture tree drift)"
        rep1 = json.load(io.open(r1, encoding="utf-8"))
        assert rep1["schema"] == SCHEMA, rep1["schema"]
        assert rep1["mode"] == "DRY-RUN", rep1["mode"]
        assert rep1["writes"] is None, rep1["writes"]
        assert rep1["assertions"]["ran"] is False, rep1["assertions"]
        assert rep1["stats"]["items_total"] == 16, rep1["stats"]  # 12+4
        kinds = {s["kind"] for s in rep1["skip"]}
        assert kinds == {"REANCHOR-SKIP-MISSING-ENTITY",
                         "ORPHAN-ADD-SKIP-NON-MECHANICAL",
                         "UNRESOLVABLE-PASSTHROUGH",
                         "ANCHOR-MISSING-SKIP"}, rep1["skip"]
        assert len(rep1["skip"]) == 6, rep1["skip"]  # 2+2+1+1
        assert rep1["items"][0]["kind"] == "DEDUP" \
            and rep1["items"][0]["book"] == "coqproject" \
            and rep1["items"][0]["keep_line"] == 12 \
            and rep1["items"][0]["drop_lines"] == [24], rep1["items"][0]
        # reanchor targets: ToyA placeholder audit md5 resolved for real (77c2b9a8); Ghost skipped, entity missing
        ra = {it["key"]: it for it in rep1["items"] if it["kind"] == "REANCHOR"}
        assert set(ra) == {"ToyA.v", "SeqB.v", "CollA.v", "CollB.v"}, \
            sorted(ra)
        assert ra["ToyA.v"]["md5_8"] == "77c2b9a8", ra["ToyA.v"]
        # dry-run determinism: the re-run report is byte-identical
        r1b = os.path.join(tmp, "rep1b.json")
        p = run(["--audit-json", os.path.join(d1, "audit.json"),
                 "--order", o1, "--project", p1, "--anchor-src", w1,
                 "--json", r1b])
        assert p.returncode == 0, p.stdout
        assert io.open(r1b, "rb").read() == io.open(r1, "rb").read(), \
            "the dry-run report drifted byte-wise"
        print("  [1/8] dry-run zero-write OK (fixture tree identical, "
              "items=16 skip=6 full spectrum, ToyA md5=77c2b9a8, report "
              "byte-identical on re-run)")

        # ---- vector 2: --apply, the 12 duplicate rows -> 0, three assertions pass, account vs disk ----
        d2 = os.path.join(tmp, "vec2")
        os.makedirs(d2)
        o2, p2, w2 = build_fixture(d2)
        run_audit(o2, p2, w2, os.path.join(d2, "audit.json"))
        wd2 = os.path.join(d2, "work")
        r2 = os.path.join(d2, "rep.json")
        p = run(["--audit-json", os.path.join(d2, "audit.json"),
                 "--order", o2, "--project", p2, "--anchor-src", w2,
                 "--apply", "--work-dir", wd2, "--json", r2])
        assert p.returncode == 0, "--apply should rc=0, got %d\n%s" % (
            p.returncode, p.stdout)
        rep2 = json.load(io.open(r2, encoding="utf-8"))
        assert rep2["mode"] == "APPLY", rep2["mode"]
        assert rep2["assertions"]["ran"] is True \
            and rep2["assertions"]["treated_duplicates_zero"] == "PASS" \
            and rep2["assertions"]["anchor_text_no_new_dups"] == "PASS" \
            and rep2["assertions"]["orphans_no_new"] == "PASS" \
            and rep2["assertions"]["treated_anchors_canonical"] == "PASS", \
            rep2["assertions"]
        assert rep2["summary"]["books_touched"] == ["coqproject", "order"], \
            rep2["summary"]
        wr = {w["book"]: w for w in rep2["writes"]["books"]}
        assert wr["coqproject"]["rows_before"] == 35 \
            and wr["coqproject"]["rows_after"] == 23, wr["coqproject"]
        assert wr["order"]["rows_before"] == 23 \
            and wr["order"]["rows_after"] == 23, wr["order"]
        # account vs disk: the last per-book md5_after == the on-disk md5 (clean fixture, faithful render)
        for label, path in (("coqproject", p2), ("order", o2)):
            last = [it for it in rep2["items"] if it["book"] == label][-1]
            assert last["md5_after"] == wr[label]["md5_on_disk_after"] \
                == md5_of(path), (label, last, wr[label])
        assert rep2["writes"]["rolled_back"] is False, rep2["writes"]
        assert os.path.isfile(wr["order"]["backup"]), "backup evidence should be on record"
        # independent re-audit proof: duplicates=0, all 12 treated keys residue-free
        post = run_audit(o2, p2, w2, os.path.join(d2, "post_check.json"),
                         fix_plan=False)
        assert post["summary"]["duplicates"] == 0, post["summary"]
        assert post["summary"]["orphans"] == 2, post["summary"]
        print("  [2/8] --apply OK (12 duplicate rows -> 0, three assertions "
              "pass, md5 account == on-disk, re-audit duplicates=0 "
              "orphans=2 unchanged)")

        # ---- vector 3: reanchor frozen md5 vector + same-input-same-output (differential run against the registry_union CLI) ----
        seqb_md5 = _ru.md5_8_of(os.path.join(w2, "SeqB.v"))
        colla_md5 = _ru.md5_8_of(os.path.join(w2, "CollA.v"))
        collb_md5 = _ru.md5_8_of(os.path.join(w2, "CollB.v"))
        with io.open(o2, encoding="utf-8") as fh:
            got = [ln.strip() for ln in fh.read().split("\n") if ln.strip()]
        assert got[0] == "ToyA.v#R3-77c2b9a8", got[0]     # frozen vector in canonical form
        assert got[1] == "SeqB.v#R7-%s" % seqb_md5, got[1]
        assert got[4] == "CollA.v#R0-%s" % colla_md5, got[4]
        assert got[5] == "CollB.v#R0-%s" % collb_md5, got[5]
        assert got[2] == "Ghost.v#R9-abcabc" \
            and got[3] == "NoEnt.v#R11", "keys with missing entities must stay as-is"
        # same-input-same-output: the registry_union CLI at the same parameters
        # (three identical books + the same name list) must match byte for byte
        d3 = os.path.join(tmp, "vec3")
        os.makedirs(d3)
        o3, p3, w3 = build_fixture(d3)
        pre_o3 = wf(os.path.join(d3, "pre_order.txt"),
                    io.open(o3, "rb").read().decode("utf-8"))
        run_audit(o3, p3, w3, os.path.join(d3, "audit.json"))
        r3 = os.path.join(d3, "rep.json")
        p = run(["--audit-json", os.path.join(d3, "audit.json"),
                 "--order", o3, "--project", p3, "--anchor-src", w3,
                 "--apply", "--work-dir", os.path.join(d3, "work"),
                 "--json", r3])
        assert p.returncode == 0, p.stdout
        u3 = os.path.join(d3, "union_out.txt")
        pu = subprocess.run(
            [sys.executable, "-B", union_py,
             "--main", pre_o3, "--base", pre_o3, "--branch", pre_o3,
             "--kind", "order",
             "--reanchor", "CollA,CollB,Ghost,ToyA,NoEnt,SeqB",
             "--anchor-src", w3, "--out", u3, "--apply"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert pu.returncode == 0, pu.stdout.decode("utf-8", errors="replace")
        assert io.open(u3, "rb").read() == io.open(o3, "rb").read(), \
            "same-input-same-output violated: the registry_union CLI output != the book written by this tool"
        print("  [3/8] reanchor vectors OK (ToyA -> 77c2b9a8 frozen, "
              "SeqB/CollA/CollB re-hashed from entities, missing entities "
              "left as-is, byte-identical to the registry_union CLI on the "
              "same input)")

        # ---- vector 4: rollback proof, injected blast point (post-write -> restored) ----
        d4 = os.path.join(tmp, "vec4")
        os.makedirs(d4)
        o4, p4, w4 = build_fixture(d4)
        run_audit(o4, p4, w4, os.path.join(d4, "audit.json"))
        pre4 = (md5_of(o4), md5_of(p4))
        wd4 = os.path.join(d4, "work")
        r4 = os.path.join(d4, "rep.json")
        p = run(["--audit-json", os.path.join(d4, "audit.json"),
                 "--order", o4, "--project", p4, "--anchor-src", w4,
                 "--apply", "--work-dir", wd4, "--json", r4],
                env_extra={INJECT_ENV: "post-write"})
        assert p.returncode == 2, "the injected blast should rc=2, got %d\n%s" % (
            p.returncode, p.stdout)
        assert "INJECTED-POST-WRITE-BLAST" in p.stdout, p.stdout[-400:]
        assert (md5_of(o4), md5_of(p4)) == pre4, "rollback violated: the books were not restored byte-for-byte"
        rep4 = json.load(io.open(r4, encoding="utf-8"))
        assert rep4["writes"]["rolled_back"] is True, rep4["writes"]
        assert rep4["rollback_evidence"]["all_restored"] is True, \
            rep4["rollback_evidence"]
        for w in rep4["writes"]["books"]:
            assert os.path.isfile(w["backup"]), w
            assert rep4["rollback_evidence"]["restored"][w["book"]]["match"] \
                is True, rep4["rollback_evidence"]
        print("  [4/8] rollback proof OK (injected post-write blast -> rc=2, "
              "books restored byte-for-byte, backup and restored md5 "
              "evidence in the report)")

        # ---- vector 5: natural blast point (same-content reanchor -> a new A-fix-2 collision -> the A3 engine raises) ----
        d5 = os.path.join(tmp, "vec5")
        os.makedirs(d5)
        o5, p5, w5 = build_fixture(d5, shared=True)
        a5 = run_audit(o5, p5, w5, os.path.join(d5, "audit.json"))
        assert a5["summary"]["duplicates"] == 12 \
            and a5["summary"]["anchors"] == 11, a5["summary"]  # +2 malformed, +1 collision
        pre5 = (md5_of(o5), md5_of(p5))
        r5 = os.path.join(d5, "rep.json")
        p = run(["--audit-json", os.path.join(d5, "audit.json"),
                 "--order", o5, "--project", p5, "--anchor-src", w5,
                 "--apply", "--work-dir", os.path.join(d5, "work"),
                 "--json", r5])
        assert p.returncode == 2, "the natural A-fix-2 blast should rc=2, got %d\n%s" % (
            p.returncode, p.stdout)
        assert "A3-ANCHOR-TEXT-NEW-DUP" in p.stdout, p.stdout[-400:]
        assert (md5_of(o5), md5_of(p5)) == pre5, "rollback violated (natural blast point)"
        rep5 = json.load(io.open(r5, encoding="utf-8"))
        assert rep5["writes"]["rolled_back"] is True, rep5["writes"]
        assert rep5["blast"]["code"] == "A3-ANCHOR-TEXT-NEW-DUP", rep5["blast"]
        print("  [5/8] natural blast OK (same-content reanchor creates a new "
              "collision -> A3-ANCHOR-TEXT-NEW-DUP, rc=2, rollback restored)")

        # ---- vector 6: staging blast (audit-vs-book drift, zero writes, no work-dir) ----
        d6 = os.path.join(tmp, "vec6")
        os.makedirs(d6)
        o6, p6, w6 = build_fixture(d6)
        run_audit(o6, p6, w6, os.path.join(d6, "audit.json"))
        wf(p6, 'ZZZ.v#R9-99999999\n' + io.open(p6, "rb").read()
            .decode("utf-8"))  # insert a row at the top -> the keep=L12 key drifts
        pre6 = (md5_of(o6), md5_of(p6))
        wd6 = os.path.join(d6, "work")
        r6 = os.path.join(d6, "rep.json")
        p = run(["--audit-json", os.path.join(d6, "audit.json"),
                 "--order", o6, "--project", p6, "--anchor-src", w6,
                 "--apply", "--work-dir", wd6, "--json", r6])
        assert p.returncode == 2, "the staging blast should rc=2, got %d\n%s" % (
            p.returncode, p.stdout)
        assert "DEDUP-KEEP-KEY-MISMATCH" in p.stdout, p.stdout[-400:]
        assert (md5_of(o6), md5_of(p6)) == pre6, "a staging blast must not touch the books"
        assert not os.path.exists(wd6), "a staging blast must not create the work-dir (zero writes)"
        rep6 = json.load(io.open(r6, encoding="utf-8"))
        assert rep6["writes"] is None and rep6["blast"]["code"] \
            == "DEDUP-KEEP-KEY-MISMATCH", rep6
        print("  [6/8] staging blast OK (audit-vs-book drift -> "
              "DEDUP-KEEP-KEY-MISMATCH, zero writes, work-dir not created)")

        # ---- vector 7: CLI exit codes + schema face ----
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "an unknown flag should rc=2, got %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "no input should rc=2, got %d" % p.returncode
        p = run(["--audit-json", os.path.join(tmp, "nope.json"),
                 "--order", o1, "--project", p1])
        assert p.returncode == 9, "a missing --audit-json should rc=9, got %d" % p.returncode
        p = run(["--audit-json", os.path.join(d1, "audit.json"),
                 "--order", os.path.join(tmp, "nope.txt"), "--project", p1])
        assert p.returncode == 9, "a missing book should rc=9, got %d" % p.returncode
        bad = wf(os.path.join(tmp, "badschema.json"),
                 json.dumps({"schema": "bogus/9"}))
        p = run(["--audit-json", bad, "--order", o1, "--project", p1])
        assert p.returncode == 2, "a bad schema should rc=2, got %d" % p.returncode
        nofp = os.path.join(tmp, "nofix.json")
        run_audit(o1, p1, w1, nofp, fix_plan=False)
        p = run(["--audit-json", nofp, "--order", o1, "--project", p1])
        assert p.returncode == 2, "a missing fix_plan should rc=2, got %d" % p.returncode
        d7 = os.path.join(tmp, "vec7")
        os.makedirs(d7)
        o7, p7, w7 = build_fixture(d7)
        a7 = run_audit(o7, p7, w7, os.path.join(d7, "audit.json"))
        p = run(["--audit-json", os.path.join(d1, "audit.json"),
                 "--order", o7, "--project", p7])   # different books: same-parameter breach
        assert p.returncode == 2, "a same-parameter breach should rc=2, got %d\n%s" % (
            p.returncode, p.stdout)
        p = run(["--audit-json", os.path.join(d1, "audit.json"),
                 "--order", o1, "--project", p1,
                 "--anchor-src", os.path.join(tmp, "noworld")])
        assert p.returncode == 9, "a missing anchor-src directory should rc=9, got %d" % (
            p.returncode)
        print("  [7/8] CLI exit codes OK (help0/bogus2/no-input2/"
              "missing-audit9/missing-book9/bad-schema2/no-fix_plan2/"
              "same-param-breach2/missing-anchor-src9)")

        # ---- vector 8: apply determinism (two fresh fixtures processed the same way -> identical books/accounts) ----
        outs = []
        for tag in ("a", "b"):
            d8 = os.path.join(tmp, "vec8" + tag)
            os.makedirs(d8)
            o8, p8, w8 = build_fixture(d8)
            run_audit(o8, p8, w8, os.path.join(d8, "audit.json"))
            r8 = os.path.join(d8, "rep.json")
            p = run(["--audit-json", os.path.join(d8, "audit.json"),
                     "--order", o8, "--project", p8, "--anchor-src", w8,
                     "--apply", "--work-dir", os.path.join(d8, "work"),
                     "--json", r8])
            assert p.returncode == 0, p.stdout
            with io.open(r8, encoding="utf-8") as fh:
                items8 = json.load(fh)["items"]
            outs.append((io.open(o8, "rb").read(),
                         io.open(p8, "rb").read(),
                         [(it["kind"], it["key"], it["md5_before"],
                           it["md5_after"]) for it in items8]))
        assert outs[0][0] == outs[1][0] and outs[0][1] == outs[1][1], \
            "the written books drifted byte-wise"
        assert outs[0][2] == outs[1][2], "the per-item md5 accounts drifted"
        print("  [8/8] apply determinism OK (two fresh fixtures -> identical "
              "book bytes and identical per-item md5 accounts)")

        print("REGISTRY-FIX-SELFTEST PASS: dry-run zero-write / 12 duplicate "
              "rows -> 0 with three assertions passing / 77c2b9a8 "
              "same-input-same-output / injected-blast rollback / natural-blast "
              "rollback / staging zero-write / CLI exit codes / apply "
              "determinism, all 8 vectors passed")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
