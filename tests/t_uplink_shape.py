#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_uplink_shape.py - tests/ suite shell for tools/uplink.py.

    Purpose.  Hook the uplink standard intake gate into the tests/ suite and smoke
      its three faces offline: `verify` (zip plus md5sum-style manifest; fail-loud
      red on any digest mismatch or missing member, per-file evidence), `intake`
      (append exactly one docs/uplink-intake.jsonl row, schema rocqwash-uplink/1,
      nothing else written), and `pr-prep` (a PR description draft file; it never
      opens a pull request).  The repository-tree checksum must stay unchanged.

    Interface.  `python3 tests/t_uplink_shape.py` (run directly; deliberately not
      rostered in tests/run_tests.sh, same standing decision as tests/t_exp_port.py
      and tests/t_periscope_shape.py: roster insertion belongs to a work stream
      holding that authorization).  Faces pinned by the uplink ticket: `verify
      --package P.zip --manifest M.md5`; `intake --package P.zip --manifest M.md5
      [--registry F]` (it re-verifies; the source provenance pair lands in the
      registry row); `pr-prep --registry F --package NAME --out DRAFT.md`;
      `--register` defaults to docs/uplink-intake.jsonl; rows are `<hex>  <name>`.

    Dependencies.  Python 3 stdlib only; the inspected tool is stdlib-only; every
      check runs on temporary fixtures or nonexistent scratch paths; zero network
      by construction.

    Evidence.  Every check asserts the exit code and output face of a real
      subprocess on this machine; the fixture package and manifest derive from
      member bytes built here; the read-only oath is a double full-tree checksum
      (git metadata and __pycache__ pruned) around the run.

    Exit-codes.  0 = all checks pass; 1 = any check red (fail-loud, each red
      check printed; no silent downgrade).
"""
# Extended contract (kept outside the five-field block; annotation budget):
#
# Tool exit-code convention pinned by the uplink ticket: 0 = face green; 1 =
#   fail-loud red (digest mismatch, missing member, failed verification); 2 =
#   usage error; 9 = missing input.
# Suite-shell imports: subprocess/tempfile/shutil/zipfile stand in this family
#   already (tests/t_periscope_shape.py, tests/t_exp_port.py); the tool itself
#   is stdlib-only with zero dynamic execution and zero network.
# The intake face takes the source provenance pair as two flags spelled in the
#   check bodies below; the header prose cites only the registry fields the
#   pair lands in, per the annotation scanner's identifier rules.
# Flag spellings: docs/uplink_sop.md section 0.1 cites the register-path flag
#   as `--register` and this shell follows it; the SOP leaves the remaining
#   flag spellings to the implementation, and this shell pins the minimal
#   forms it drives.
# Registry reading rule: a first line opening with `#` is the schema comment
#   the register schema pins by design; row counting skips `#` lines.
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "uplink.py")

# member bytes of the fixture return package; the manifest derives from
# exactly these bytes, so every digest the tool sees is first-hand
MEMBERS = {
    "alpha.txt": b"alpha payload line\n",
    "beta/data.txt": b"beta payload bytes\n",
    "gamma.md": b"# gamma draft note\n",
}
SCHEMA = "rocqwash-uplink/1"
FIELDS = ("package", "source-seat", "md5", "verified", "landed-ref", "exit")
FACES = ("verify", "intake", "pr-prep")


def run(args):
    """Run the tool in a subprocess (stdout and stderr merged).  `-X utf8`
    pins the stdio encoding so member names reach the pipe byte-stable on
    a cp936 console."""
    p = subprocess.run([sys.executable, "-B", "-I", "-X", "utf8", TOOL]
                       + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       cwd=REPO)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def build_package(tmp, stem, tamper=None, missing=None):
    """Materialize a fixture return package plus its md5sum-style manifest
    in the scratch directory and return both paths.  `tamper` flips one
    member digest to all zeros; `missing` adds a manifest row for a name
    the zip does not carry."""
    zip_path = os.path.join(tmp, stem + ".zip")
    man_path = os.path.join(tmp, stem + ".md5")
    rows = []
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name in sorted(MEMBERS):
            digest = hashlib.md5(MEMBERS[name]).hexdigest()
            if name == tamper:
                digest = "0" * 32
            rows.append("%s  %s" % (digest, name))
            zf.writestr(name, MEMBERS[name])
    if missing:
        rows.append("%s  %s"
                    % (hashlib.md5(MEMBERS["alpha.txt"]).hexdigest(),
                       missing))
    with open(man_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(rows) + "\n")
    return zip_path, man_path


def tree_digest():
    """Full-tree checksum of the repository working tree: a sorted walk with
    each file's relative path bound into the digest before its bytes.  Git
    metadata and __pycache__ directories are pruned, because the oath is
    over the working tree, not over concurrent version-control bookkeeping
    or interpreter cache churn this process never causes."""
    h = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in (".git", "__pycache__"))
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, REPO).replace("\\", "/")
            h.update(rel.encode("utf-8"))
            with open(full, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def main():
    fails = []
    if not os.path.exists(TOOL):
        sys.stderr.write(
            "T_UPLINK_SHAPE NOTE %s is not on this tree yet; the "
            "implementation face has not landed, so every tool-facing "
            "check below stays red until it does (honest test-first "
            "state, no fake green).\n" % TOOL)
    digest0 = tree_digest()
    tmp = tempfile.mkdtemp(prefix="t_uplink_shape_")
    package_key = ""
    try:
        # check1: usage face names the three faces of the uplink ticket
        rc, out = run(["--help"])
        flat = re.sub(r"-\s*\n\s*", "-", out)
        if rc != 0:
            fails.append("check1 --help should be rc=0 (rc=%d)\n%s"
                         % (rc, out))
        for face in FACES:
            if face not in flat:
                fails.append("check1 --help should name the face %r\n%s"
                             % (face, flat))

        # check2: exit-code convention on the usage surface only
        rc, _ = run(["--bogus"])
        if rc != 2:
            fails.append("check2 --bogus should exit 2, got %d" % rc)
        rc, _ = run([])
        if rc != 2:
            fails.append("check2 a bare run should exit 2, got %d" % rc)

        # check3: a green package verifies rc=0 with per-member evidence
        green_zip, green_man = build_package(tmp, "pkg")
        rc, out = run(["verify", "--package", green_zip,
                       "--manifest", green_man])
        if rc != 0:
            fails.append("check3 verify on a green package should be rc=0 "
                         "(rc=%d)\n%s" % (rc, out))
        for name in sorted(MEMBERS):
            if name not in out:
                fails.append("check3 verify should list member %r in its "
                             "evidence\n%s" % (name, out))

        # check4: a tampered digest fails loud rc=1 and names the member
        bad_zip, bad_man = build_package(tmp, "pkg_bad",
                                         tamper="beta/data.txt")
        rc, out = run(["verify", "--package", bad_zip,
                       "--manifest", bad_man])
        if rc != 1:
            fails.append("check4 verify on a tampered digest should fail "
                         "loud with rc=1, got %d\n%s" % (rc, out))
        if "beta/data.txt" not in out:
            fails.append("check4 the red evidence should name the tampered "
                         "member\nrc=%d\n%s" % (rc, out))

        # check5: a manifest row absent from the zip fails loud rc=1
        gap_zip, gap_man = build_package(tmp, "pkg_gap", missing="delta.txt")
        rc, out = run(["verify", "--package", gap_zip,
                       "--manifest", gap_man])
        if rc != 1:
            fails.append("check5 verify with a manifest row absent from the "
                         "zip should fail loud with rc=1, got %d\n%s"
                         % (rc, out))
        if "delta.txt" not in out:
            fails.append("check5 the red evidence should name the missing "
                         "member\nrc=%d\n%s" % (rc, out))

        # check6: a missing package file is missing input, exit 9
        rc, out = run(["verify", "--package",
                       os.path.join(tmp, "absent.zip"),
                       "--manifest", green_man])
        if rc != 9:
            fails.append("check6 verify on an absent package file should "
                         "exit 9, got %d\n%s" % (rc, out))

        # check7: a green intake appends exactly one registry row with the
        # pinned schema and the six pinned fields, at --registry
        reg = os.path.join(tmp, "uplink-intake.jsonl")
        rc, out = run(["intake", "--package", green_zip,
                       "--manifest", green_man,
                       "--source-seat", "fixture-source",
                       "--landed-ref", "refs/heads/supply/fixture",
                       "--register", reg])
        if rc != 0:
            fails.append("check7 intake on a green package should be rc=0 "
                         "(rc=%d)\n%s" % (rc, out))
        entry = None
        if os.path.exists(reg):
            with open(reg, "r", encoding="utf-8") as fh:
                lines = [ln for ln in fh.read().splitlines()
                         if ln.strip() and not ln.lstrip().startswith("#")]
            if len(lines) != 1:
                fails.append("check7 a green intake should append exactly "
                             "one registry row, found %d" % len(lines))
            else:
                try:
                    entry = json.loads(lines[0])
                except ValueError as err:
                    fails.append("check7 the registry row should parse as "
                                 "JSON: %s" % err)
        else:
            fails.append("check7 a green intake should materialize the "
                         "registry file")
        if entry is not None:
            if entry.get("schema") != SCHEMA:
                fails.append("check7 the registry row should carry schema "
                             "%r, found %r" % (SCHEMA, entry.get("schema")))
            for field in FIELDS:
                if field not in entry:
                    fails.append("check7 the registry row misses field %r"
                                 % field)
            if not re.fullmatch(r"[0-9a-f]{32}", str(entry.get("md5", ""))):
                fails.append("check7 the md5 field should be a lowercase "
                             "hex digest, found %r" % entry.get("md5"))
            if entry.get("exit") != 0:
                fails.append("check7 the exit field should record 0 on a "
                             "green intake, found %r" % entry.get("exit"))
            for field in ("package", "source-seat", "landed-ref"):
                value = entry.get(field)
                if not isinstance(value, str) or not value:
                    fails.append("check7 the %s field should be a non-empty "
                                 "string" % field)
            if isinstance(entry.get("package"), str):
                package_key = entry["package"]

        # check8: intake on a failed verification appends nothing; the
        # registry bytes stay exactly what the green run left
        reg_snapshot = read_bytes(reg) if os.path.exists(reg) else b""
        rc, out = run(["intake", "--package", bad_zip,
                       "--manifest", bad_man,
                       "--source-seat", "fixture-source",
                       "--landed-ref", "refs/heads/supply/fixture",
                       "--register", reg])
        if rc != 1:
            fails.append("check8 intake on a tampered package should fail "
                         "loud with rc=1, got %d\n%s" % (rc, out))
        reg_now = read_bytes(reg) if os.path.exists(reg) else b""
        if reg_now != reg_snapshot:
            fails.append("check8 a red intake must not touch the registry")

        # check9: pr-prep renders the draft at --out from the intake row
        draft = os.path.join(tmp, "pr-draft.md")
        rc, out = run(["pr-prep", "--registry", reg,
                       "--package", package_key, "--out", draft])
        if rc != 0:
            fails.append("check9 pr-prep on a registered package should be "
                         "rc=0 (rc=%d)\n%s" % (rc, out))
        if not os.path.isfile(draft):
            fails.append("check9 pr-prep should materialize the draft file")
        elif package_key:
            if package_key not in read_bytes(draft).decode(
                    "utf-8", errors="replace"):
                fails.append("check9 the draft should name the package %r"
                             % package_key)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # check10: the read-only oath, mechanical form: the whole working tree
    # hashes identically before and after the run, intake included
    digest1 = tree_digest()
    if digest0 != digest1:
        fails.append("check10 the repository-tree checksum changed across "
                     "the shell run (read-only oath red)")

    if fails:
        for line in fails:
            sys.stderr.write("T_UPLINK_SHAPE FAIL %s\n" % line)
        return 1
    sys.stdout.write("T-UPLINK-SHAPE SUITE SHELL PASS (10 checks)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
