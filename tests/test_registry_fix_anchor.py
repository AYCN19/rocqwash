#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_registry_fix_anchor.py — tests/ suite shell + anchor-face oracle
vectors for tools/registry_fix.py (REANCHOR class).

Purpose.  Hook the registry fix-plan executor into the tests/ suite next to
  its sibling shells (test_registry_audit.py, test_registry_regen.py), and
  pin the anchor-face apply contract that the executor's own --selftest
  leaves at unit level: after a treated --apply, every executed REANCHOR
  key must leave zero residual anchor findings (anchor-seq-form /
  anchor-malformed) in the same-parameter re-audit. The residual gate is
  the anchor-face twin of the existing treated-duplicates gate (A-fix-1);
  the oracle is the audit producer's own classification, so no anchor
  semantics are defined here.

Interface.  `python3 tests/test_registry_fix_anchor.py` (suite entry:
  tests/run_tests.sh case t_registry_fix_anchor).  Four checks:
  check1 --selftest rc=0 with the `REGISTRY-FIX-SELFTEST PASS` frozen
  marker; check2 --help rc=0 with a usage face; check3 exit-code
  convention spot checks (--bogus=2, no input=2, missing --audit-json=9);
  check4 the anchor-face oracle vectors on a canned tmp fixture built with
  the tool's own fixture builder: dry-run zero-write, --apply with the
  four assertions green (treated_anchors_canonical included), re-audit
  duplicates=0, and unit-level blast vectors for the residual gate
  (residual seq-form on a treated key, residual malformed on a treated
  key, residual on an untreated key stays silent, anchor-collision kind
  stays owned by the A-fix-2 gate).

Dependencies.  Python 3 stdlib only; the executor and the audit producer
  are stdlib-only; all fixture faces run under tempfile.mkdtemp and are
  removed on exit; zero network, zero compile, no real repository is
  read or written.

Evidence.  Every check runs the real tool in a subprocess or imports the
  real module and asserts observable behavior on this machine; nothing is
  inferred from source text.

Exit-codes.  0 = all four checks pass; 1 = any check red (fail-loud,
  the red check is printed; no silent downgrade).
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, "tools")
TOOL = os.path.join(TOOLS, "registry_fix.py")
AUDIT = os.path.join(TOOLS, "registry_audit.py")
MARK = "REGISTRY-FIX-SELFTEST PASS"

sys.path.insert(0, TOOLS)
import registry_fix as rf        # noqa: E402  (unit vectors; stdlib-only module)
import registry_union as _ru     # noqa: E402  (AssertBlast shape only)


def run(args, env_extra=None):
    """Run the executor in a subprocess (stdout+stderr merged, decoded)."""
    env = dict(os.environ)
    env.pop("ROCWASH_REGISTRY_FIX_INJECT_BLAST", None)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def run_audit(order_p, project_p, world, json_p):
    """Produce a files-mode fix plan for a fixture (audit producer CLI)."""
    p = subprocess.run([sys.executable, "-B", AUDIT, "--order", order_p,
                        "--project", project_p, "--anchor-src", world,
                        "--fix-plan", "--json", json_p],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", errors="replace")
    assert p.returncode == 0, "audit producer should be rc=0 (data not tool red): %s" % out
    with io.open(json_p, encoding="utf-8") as fh:
        return json.load(fh)


def tree_md5(root):
    """Content fingerprint of a directory tree (zero-write side proof)."""
    rows = []
    for dirpath, _dirs, fnames in os.walk(root):
        for fn in sorted(fnames):
            p = os.path.join(dirpath, fn)
            with io.open(p, "rb") as fh:
                rows.append((os.path.relpath(p, root), hashlib.md5(fh.read()).hexdigest()))
    return sorted(rows)


def anchor_post(kind, key, lines, evidence="evidence"):
    return {"kind": kind, "key": key, "lines": lines, "evidence": evidence}


def main():
    fails = []

    # ---- check1: frozen selftest marker ----
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("check1 --selftest should be rc=0 with %r (rc=%d)" % (MARK, rc))
        print(out)
    else:
        print("check1 OK: --selftest rc=0 with frozen marker")

    # ---- check2: usage face ----
    rc, out = run(["--help"])
    if rc != 0 or "usage" not in out:
        fails.append("check2 --help should be rc=0 with a usage face (rc=%d)" % rc)
        print(out)
    else:
        print("check2 OK: --help rc=0 usage face")

    # ---- check3: exit-code convention spot checks (no fixtures needed) ----
    rc, _ = run(["--bogus"])
    if rc != 2:
        fails.append("check3 --bogus should be rc=2 (got %d)" % rc)
    rc, _ = run([])
    if rc != 2:
        fails.append("check3 no input should be rc=2 (got %d)" % rc)
    rc, _ = run(["--audit-json", os.path.join(REPO, "no-such-audit.json"),
                 "--order", os.path.join(REPO, "no-such-order.txt"),
                 "--project", os.path.join(REPO, "no-such-project.txt")])
    if rc != 9:
        fails.append("check3 missing --audit-json should be rc=9 (got %d)" % rc)
    if not fails or not [f for f in fails if f.startswith("check3")]:
        print("check3 OK: bogus=2 no-input=2 missing-audit-json=9")

    # ---- check4: anchor-face oracle vectors on a canned tmp fixture ----
    tmp = tempfile.mkdtemp(prefix="rw_fix_unit_")
    try:
        d = os.path.join(tmp, "fx")
        os.makedirs(d)
        o, p, w = rf.build_fixture(d)
        audit_json = os.path.join(d, "audit.json")
        run_audit(o, p, w, audit_json)

        # dry run: zero write, plan staged, assertions honestly NOT-RUN
        # (report paths live outside the fixture dir so the zero-write proof
        # covers the fixture tree itself)
        pre = tree_md5(d)
        r1 = os.path.join(tmp, "dry.json")
        rc, out = run(["--audit-json", audit_json, "--order", o, "--project", p,
                       "--anchor-src", w, "--json", r1])
        if rc != 0 or tree_md5(d) != pre:
            fails.append("check4 dry run should be rc=0 and write nothing (rc=%d)" % rc)
            print(out)
        else:
            rep = json.load(io.open(r1, encoding="utf-8"))
            if rep["mode"] != "DRY-RUN" or rep["writes"] is not None:
                fails.append("check4 dry-run report face: mode=%s writes=%r"
                             % (rep["mode"], rep["writes"]))
            if rep["assertions"].get("ran") is not False:
                fails.append("check4 dry-run assertions should be NOT-RUN")
            else:
                print("check4 OK: dry-run rc=0 zero-write, assertions NOT-RUN")

        # apply: four assertions green, executed keys leave no residual anchors
        r2 = os.path.join(tmp, "apply.json")
        rc, out = run(["--audit-json", audit_json, "--order", o, "--project", p,
                       "--anchor-src", w, "--apply", "--work-dir",
                       os.path.join(d, "work"), "--json", r2])
        if rc != 0:
            fails.append("check4 apply should be rc=0 (rc=%d)" % rc)
            print(out)
        else:
            rep = json.load(io.open(r2, encoding="utf-8"))
            a = rep["assertions"]
            for field in ("treated_duplicates_zero", "anchor_text_no_new_dups",
                          "orphans_no_new", "treated_anchors_canonical"):
                if a.get(field) != "PASS":
                    fails.append("check4 apply assertion %s should be PASS, got %r"
                                 % (field, a.get(field)))
            # the residual gate means it: re-audit the written books; the
            # fixture intentionally keeps skip-class keys (missing entity,
            # missing anchor, canonical collision), so the assertion scope is
            # the executed REANCHOR keys, not the whole anchor account
            post = run_audit(o, p, w, os.path.join(tmp, "post.json"))
            treated = {it["key"] for it in rep["items"] if it["kind"] == "REANCHOR"}
            residual = {f["key"] for f in post["sections"]["anchors"]
                        if f["kind"] in ("anchor-seq-form", "anchor-malformed")}
            if post["summary"]["duplicates"] != 0:
                fails.append("check4 re-audit duplicates should be 0: %s"
                             % post["summary"])
            if treated & residual:
                fails.append("check4 executed keys left residual anchor findings: %s"
                             % sorted(treated & residual))
            if residual != {"Ghost.v", "NoEnt.v"}:
                fails.append("check4 skip-class residuals should be exactly the "
                             "missing-entity keys, got %s" % sorted(residual))
            if not [f for f in fails if f.startswith("check4")]:
                print("check4 OK: apply rc=0 with four assertions green "
                      "(treated_anchors_canonical included); re-audit "
                      "duplicates=0, executed keys residual-free, skip-class "
                      "keys stay as designed")

        # unit vectors for the residual gate (blast path)
        treated = {"ToyA.v", "SeqB.v"}
        cases = [
            ("clean payload", [], None),
            ("residual seq-form on treated key",
             [anchor_post("anchor-seq-form", "ToyA.v", [1])],
             "ASSERT-TREATED-ANCHOR-NONZERO"),
            ("residual malformed on treated key",
             [anchor_post("anchor-malformed", "SeqB.v", [2])],
             "ASSERT-TREATED-ANCHOR-NONZERO"),
            ("residual on untreated key stays silent",
             [anchor_post("anchor-seq-form", "Untouched.v", [3])], None),
            ("collision kind stays owned by A-fix-2",
             [anchor_post("anchor-collision", "#R0-deadbeef", [1, 2])], None),
            ("missing kind stays owned by the skip list",
             [anchor_post("anchor-missing", "ToyA.v", [1])], None),
        ]
        for name, anchors, want_code in cases:
            payload = {"sections": {"anchors": anchors}}
            try:
                rf.assert_treated_anchors_canonical(payload, treated)
                got = None
            except _ru.AssertBlast as e:
                got = e.code
            except AttributeError:
                fails.append("check4 residual gate function missing "
                             "(assert_treated_anchors_canonical): %s" % name)
                continue
            if got != want_code:
                fails.append("check4 unit vector %r: want blast=%r got %r"
                             % (name, want_code, got))
        if not [f for f in fails if f.startswith("check4")]:
            print("check4 OK: residual-gate unit vectors 6/6 (blast on treated "
                  "seq-form/malformed; silent for untreated/collision/missing)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("== test_registry_fix: %d red check(s) ==" % len(fails))
        for f in fails:
            print("FAIL: %s" % f)
        return 1
    print("== test_registry_fix_anchor: 4 checks pass ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
