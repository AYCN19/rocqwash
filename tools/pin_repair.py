#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pin_repair.py - re-sign drifted provenance v2 pins in the jargon seed.

Purpose.  R15 auto-repair executor over the provenance v2 pins.  Judgment
  is per pin kind: a repo source by its committed blob sha (git
  rev-parse HEAD:<path>); an external source by its in-repo snapshot
  md5 (consistency layer) plus the upstream original's md5 where this
  machine carries it (freshness layer).  Re-sign only from bytes this
  tool has read; an absent upstream is recorded, never fatal.

Interface.  python3 tools/pin_repair.py --selftest | --plan | --apply
  [--seed P] (default seeds/jargon/jargon-map.json).  One JSON result
  line on stdout, narrative on stderr; --plan writes nothing; --apply
  rewrites pin values in provenance.sources and refreshes external
  sources' in-repo snapshot bytes from their upstream originals.

Dependencies.  Standard library only; zero network face.  Subprocesses:
  git rev-parse / git hash-object, tools/jargon_map_sync.py (plan gate,
  seed forwarded on --map), tests/t_engines_seeds.py (post-apply
  verification); the selftest rides a fixture git repository in temp.

Evidence.  --selftest vectors: matched pins (none); repo pin drift (plan
  reports head vs pinned blob, apply re-signs the working bytes');
  snapshot corruption refreshed from upstream; upstream drift re-signed;
  upstream absence recorded while the rest applies; blocked red in plan;
  gate PENDING (exit 3, zero write); red verify rolls the seed and snapshots back (exit 4); usage (2).

Exit-codes.  0 green / plan / none / apply verified; 1 red named
  (unreadable seed, apply refused, rewrite refused, selftest red);
  2 usage; 3 gate not IN-SYNC; 4 red verify rolled back.
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
import tempfile

SCHEMA = "rocqwash-pin-repair/1"
TOOL = "pin_repair"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SEED_PATH = os.path.join(REPO_ROOT, "seeds", "jargon",
                                 "jargon-map.json")
SYNC_TOOL_PATH = os.path.join(REPO_ROOT, "tools", "jargon_map_sync.py")
SEED_SUITE_PATH = os.path.join(REPO_ROOT, "tests", "t_engines_seeds.py")

# the gate passes only when the sync tool's zero-write plan reports this
# verdict prefix (tools/jargon_map_sync.py, plan mode tail line)
SYNC_VERDICT_OK = "VERDICT IN-SYNC"

# the declared-skip notice an external source carries when this machine
# does not hold its upstream original (the honest-skip contract text)
UPSTREAM_ABSENT_NOTICE = ("SKIP (declared, freshness unverifiable"
                          " off-canonical: upstream absent)")

GATE_TIMEOUT_S = 120
SUITE_TIMEOUT_S = 300
GIT_TIMEOUT_S = 30

SEGMENT_RE = re.compile(r"^SEGMENT jargon: (\d+) checks, (\d+) FAIL")

REPO_PIN_KIND = "git-blob-sha"
EXTERNAL_PIN_KIND = "md5"
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX32 = re.compile(r"^[0-9a-f]{32}$")


def fail(msg, code):
    sys.stderr.write(TOOL + ": " + msg + "\n")
    raise SystemExit(code)


def _vec(results, name, ok, detail):
    results.append((name, bool(ok), detail))


def resolve_path(path):
    """Repository-relative paths resolve against the repository root."""
    if os.path.isabs(path):
        return path
    return os.path.join(REPO_ROOT, path)


def resolve_against(root, rel):
    """A provenance v2 path is repository-relative; resolve it against
    the judgment root (the tool's repository in production, a fixture
    repository in the selftest)."""
    return os.path.join(root, rel.replace("\\", "/"))


def file_md5(path):
    """Current md5 of a file's bytes; None when the file cannot be read."""
    try:
        with io.open(path, "rb") as fh:
            return hashlib.md5(fh.read()).hexdigest()
    except OSError:
        return None


def file_bytes(path):
    """Raw bytes of a file; raises OSError when it cannot be read."""
    with io.open(path, "rb") as fh:
        return fh.read()


def git_out(root, args):
    """One read-only git query over the object database; returns
    (rc, stdout, stderr) with rc None when git could not be launched."""
    try:
        proc = subprocess.run(["git"] + list(args), cwd=root,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=GIT_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, "", "%s: %s" % (type(exc).__name__, exc)
    return proc.returncode, proc.stdout.strip(), (proc.stderr or "").strip()


def head_blob_sha(root, rel):
    """The committed blob sha of a repository path, or (None, reason).

    A pure object-database query: it reads the committed bytes, so it
    answers identically on every machine that holds the repository,
    which is what makes the repo-source judgment real on hosted
    runners instead of structurally blind."""
    rc, out, err = git_out(root, ["rev-parse",
                                  "HEAD:" + rel.replace("\\", "/")])
    if rc != 0:
        return None, err or out or "git rev-parse failed"
    return out, ""


def work_blob_sha(root, abs_path):
    """The blob sha of a working-tree file's bytes (git hash-object)."""
    rc, out, err = git_out(root, ["hash-object", "--", abs_path])
    if rc != 0:
        return None, err or out or "git hash-object failed"
    return out, ""


def load_seed(seed_path):
    """Read the seed JSON; return (raw bytes, dict, provenance sources).

    Fails loud on an unreadable file, invalid JSON, or a provenance
    block not in the provenance v2 form (locator, repository-relative
    path, a pin object whose kind matches the locator); a repair
    executor never guesses, and the v2 pin contract has no legacy
    reading."""
    try:
        with io.open(seed_path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        fail("seed unreadable: " + seed_path + " (" + str(exc) + ")", 1)
    try:
        doc = json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        fail("seed is not valid UTF-8 JSON: " + seed_path
             + " (" + str(exc) + ")", 1)
    prov = doc.get("provenance") if isinstance(doc, dict) else None
    sources = prov.get("sources") if isinstance(prov, dict) else None
    if not isinstance(sources, list) or not sources:
        fail("seed carries no provenance.sources list: " + seed_path, 1)
    for src in sources:
        if not isinstance(src, dict) \
                or not isinstance(src.get("path"), str) \
                or not src["path"]:
            fail("provenance source without a path string in "
                 + seed_path, 1)
        if os.path.isabs(src["path"]):
            fail("provenance source path must be repository relative: "
                 + src["path"], 1)
        loc = src.get("locator")
        pin = src.get("pin")
        if loc not in ("repo", "external"):
            fail("provenance source %s is not in the v2 form (locator"
                 " must be repo or external)" % src["path"], 1)
        if not isinstance(pin, dict) \
                or not isinstance(pin.get("kind"), str) \
                or not isinstance(pin.get("value"), str):
            fail("provenance source %s carries no pin object"
                 % src["path"], 1)
        if loc == "repo":
            if pin["kind"] != REPO_PIN_KIND \
                    or _HEX40.match(pin["value"]) is None:
                fail("repo source %s pin must be a 40-hex git-blob-sha"
                     % src["path"], 1)
        else:
            if pin["kind"] != EXTERNAL_PIN_KIND \
                    or _HEX32.match(pin["value"]) is None:
                fail("external source %s pin must be a 32-hex md5"
                     % src["path"], 1)
            if not isinstance(src.get("upstream_path"), str) \
                    or not src["upstream_path"]:
                fail("external source %s carries no upstream_path"
                     % src["path"], 1)
    return raw, doc, sources


def survey_sources(sources, root):
    """Per-source provenance v2 judgment.

    repo row: blob judgment -- the committed blob sha of the path (git
    rev-parse HEAD:<path>) against pin.value; state matched / drifted /
    not-in-head.  external row: consistency layer (in-repo snapshot
    bytes vs pin.value; matched / drifted / snapshot-absent) plus
    freshness layer (upstream bytes vs pin.value where this machine
    carries the original; fresh / drifted / upstream-absent /
    upstream-unreadable)."""
    rows = []
    for src in sources:
        loc = src["locator"]
        path = src["path"]
        value = src["pin"]["value"]
        if loc == "repo":
            head, _err = head_blob_sha(root, path)
            if head is None:
                state = "not-in-head"
            elif head.lower() == value.lower():
                state = "matched"
            else:
                state = "drifted"
            rows.append({"locator": "repo", "path": path,
                         "kind": REPO_PIN_KIND, "pinned_blob_sha": value,
                         "head_blob_sha": head, "state": state})
            continue
        snap_abs = resolve_against(root, path)
        snap_md5 = file_md5(snap_abs)
        if snap_md5 is None:
            consistency = "snapshot-absent"
        elif snap_md5 == value.lower():
            consistency = "matched"
        else:
            consistency = "drifted"
        upstream = src.get("upstream_path") or ""
        if not os.path.exists(upstream):
            freshness = "upstream-absent"
            up_md5 = None
        else:
            up_md5 = file_md5(upstream)
            if up_md5 is None:
                freshness = "upstream-unreadable"
            elif up_md5 == value.lower():
                freshness = "fresh"
            else:
                freshness = "drifted"
        rows.append({"locator": "external", "path": path,
                     "kind": EXTERNAL_PIN_KIND, "upstream_path": upstream,
                     "pinned_md5": value, "snapshot_md5": snap_md5,
                     "upstream_md5": up_md5, "consistency": consistency,
                     "freshness": freshness})
    return rows


def needs_repair(row):
    """Whether this tool can re-sign the source from bytes it can read
    here.  A repo pin re-signs from the working tree; an external pin
    re-signs from the upstream original.  A consistency red whose
    upstream is absent (or unreadable) is not repairable here and is
    reported as a blocked red instead."""
    if row["locator"] == "repo":
        return row["state"] in ("drifted", "not-in-head")
    if row["freshness"] in ("upstream-absent", "upstream-unreadable"):
        return False
    return (row["consistency"] in ("drifted", "snapshot-absent")
            or row["freshness"] == "drifted")


def blocked_red(row):
    """A red this machine cannot re-sign: the snapshot disagrees with
    the pin while the upstream original is absent, or the upstream
    exists but its bytes cannot be read."""
    if row["locator"] != "external":
        return False
    if row["freshness"] == "upstream-unreadable":
        return True
    if row["freshness"] == "upstream-absent":
        return row["consistency"] in ("drifted", "snapshot-absent")
    return False


def absent_row(row):
    """The report face of an upstream-absent source: recorded with the
    declared notice, never fatal."""
    return {"locator": "external", "path": row["path"],
            "pinned_md5": row["pinned_md5"],
            "consistency": row["consistency"],
            "declared": UPSTREAM_ABSENT_NOTICE}


def run_gate(gate_cmd):
    """Run the sync tool's zero-write plan; return (verdict line, detail).

    A callable gate (the selftest's stub form) is invoked directly and
    returns the same (verdict, detail) pair; a command list runs as one
    subprocess.  verdict is the last VERDICT line of stdout, or None
    when the gate could not be established (launch failure, timeout, no
    verdict line); detail then carries the failure text for the
    escalation report."""
    if callable(gate_cmd):
        return gate_cmd()
    try:
        proc = subprocess.run(gate_cmd, cwd=REPO_ROOT, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=GATE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, "sync plan timed out after %ds" % GATE_TIMEOUT_S
    except OSError as exc:
        return None, "sync plan failed to launch: " + str(exc)
    verdict = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("VERDICT "):
            verdict = line.strip()
    if verdict is None:
        tail = ((proc.stderr or "") + " " + (proc.stdout or "")).strip()
        tail = " ".join(tail.split())[:200]
        return None, tail or "no VERDICT line in the sync plan output"
    return verdict, verdict


def default_gate_cmd(seed_path):
    """The contract gate: the sync tool's zero-write plan with the seed
    under test forwarded on --map.  Forwarding is what lets a --seed
    input own the verdict; with the default seed the forwarded path is
    the sync tool's own default, so the repository-wide judgment stays
    the bare call's."""
    return [sys.executable, "-I", SYNC_TOOL_PATH, "--map", seed_path]


def run_seed_suite():
    """Run the seed test suite; return (rc, output, failure detail)."""
    try:
        proc = subprocess.run([sys.executable, "-I", SEED_SUITE_PATH],
                              cwd=REPO_ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=SUITE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, "", "seed suite timed out after %ds" % SUITE_TIMEOUT_S
    except OSError as exc:
        return None, "", "seed suite failed to launch: " + str(exc)
    return proc.returncode, proc.stdout or "", ""


def suite_jargon_green(rc, output):
    """Green means: a jargon segment line with zero FAIL and suite exit 0."""
    segment = None
    for line in output.splitlines():
        found = SEGMENT_RE.match(line.strip())
        if found:
            segment = found
    if segment is None:
        return False, "no 'SEGMENT jargon:' line in the seed suite output"
    if int(segment.group(2)) != 0:
        return False, ("jargon segment reports %s FAIL"
                       % segment.group(2))
    if rc != 0:
        return False, ("seed suite exit code %s while the jargon segment"
                       " reports 0 FAIL" % rc)
    return True, ("jargon segment: %s checks, 0 FAIL; suite exit 0"
                  % segment.group(1))


def real_verify():
    """Default post-apply verification: run the seed suite, judge it."""
    rc, output, detail = run_seed_suite()
    if detail:
        return False, detail
    return suite_jargon_green(rc, output)


def dumps_seed(doc):
    """The seed serialization: the file's own key order, indent 2, trailing
    newline.  Verified byte-stable against the seed file before any write."""
    return (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8")


def restore_snapshots(backups):
    """Restore pre-apply snapshot bytes; returns (restored, failed) as
    named lists -- a failed restore is reported, never swallowed."""
    done, failed = [], []
    for path, data in backups.items():
        try:
            if data is None:
                os.remove(path)
            else:
                with io.open(path, "wb") as fh:
                    fh.write(data)
            done.append(path)
        except OSError as exc:
            failed.append("%s: %s" % (path, exc))
    return done, failed


def flow(mode, seed_path, gate_cmd, verify=None, root=None):
    """Shared front for --plan and --apply; returns (report, exit code).

    root is the repository the sources resolve against and the working
    directory of the git blob queries; production passes the tool's own
    repository root, the selftest passes a fixture repository."""
    if verify is None:
        verify = real_verify
    if root is None:
        root = REPO_ROOT
    raw, doc, sources = load_seed(seed_path)
    verdict, gate_detail = run_gate(gate_cmd)
    sys.stderr.write("%s: seed=%s sources=%d\n"
                     % (TOOL, seed_path, len(sources)))
    sys.stderr.write("%s: gate %s\n" % (TOOL, gate_detail))
    if verdict is None or not verdict.startswith(SYNC_VERDICT_OK):
        shown = verdict if verdict else gate_detail
        return {"ok": False, "stage": "plan", "verdict": shown,
                "seed": seed_path}, 3
    rows = survey_sources(sources, root)
    drifted = [r for r in rows if needs_repair(r)]
    blocked = [r for r in rows if blocked_red(r)]
    absent = [r for r in rows if r["locator"] == "external"
              and r["freshness"] == "upstream-absent"]
    sys.stderr.write("%s: repairs=%d blocked=%d upstream-absent=%d\n"
                     % (TOOL, len(drifted), len(blocked), len(absent)))
    if mode == "plan":
        action = "plan" if (drifted or blocked) else "none"
        return {"ok": True, "action": action,
                "drifted": drifted, "blocked": blocked,
                "absent": [absent_row(r) for r in absent],
                "sources": rows, "seed": seed_path,
                "verdict": verdict}, 0
    if not drifted and not blocked:
        return {"ok": True, "action": "none", "drifted": [],
                "blocked": blocked,
                "absent": [absent_row(r) for r in absent],
                "sources": rows, "seed": seed_path,
                "verdict": verdict}, 0
    # --apply: refuse before any write when a repo pin would have to be
    # re-signed from bytes nobody can read
    refused = []
    for row in drifted:
        if row["locator"] != "repo":
            continue
        abs_path = resolve_against(root, row["path"])
        if not os.path.isfile(abs_path):
            refused.append("repo %s: no working-tree bytes to hash"
                           % row["path"])
            continue
        sha, err = work_blob_sha(root, abs_path)
        if sha is None:
            refused.append("repo %s: git hash-object failed (%s)"
                           % (row["path"], (err or "unknown")[:80]))
    if refused:
        return {"ok": False, "stage": "apply",
                "reason": ("a pin is only re-signed from bytes this tool"
                           " has actually read"),
                "refused": refused, "seed": seed_path}, 1
    # byte-stability is judged on the seed as read, before any pin value
    # is mutated: the rewrite may touch the pin values and nothing else
    if dumps_seed(doc) != raw:
        return {"ok": False, "stage": "apply",
                "reason": ("seed is not byte-stable under the key-order"
                           " indent-2 rewrite; refusing a write that could"
                           " touch more than the pin values"),
                "seed": seed_path}, 1
    snapshot_backups = {}
    plan_writes = []
    resigned = []
    for idx, row in enumerate(rows):
        if not needs_repair(row):
            continue
        src = doc["provenance"]["sources"][idx]
        old = src["pin"]["value"]
        if row["locator"] == "repo":
            sha, _err = work_blob_sha(root, resolve_against(root,
                                                            row["path"]))
            src["pin"]["value"] = sha
            resigned.append({"locator": "repo", "path": row["path"],
                             "kind": REPO_PIN_KIND,
                             "pinned_blob_sha": old,
                             "resigned_blob_sha": sha})
        else:
            upstream = row["upstream_path"]
            try:
                with io.open(upstream, "rb") as fh:
                    up_bytes = fh.read()
            except OSError as exc:
                return {"ok": False, "stage": "apply",
                        "reason": ("a pin is only re-signed from bytes"
                                   " this tool has actually read"),
                        "refused": ["external %s: upstream unreadable"
                                    " (%s)" % (row["path"], exc)],
                        "seed": seed_path}, 1
            snap_abs = resolve_against(root, row["path"])
            snapshot_backups[snap_abs] = (
                file_bytes(snap_abs) if os.path.exists(snap_abs) else None)
            plan_writes.append((snap_abs, up_bytes))
            new_md5 = hashlib.md5(up_bytes).hexdigest()
            src["pin"]["value"] = new_md5
            resigned.append({"locator": "external", "path": row["path"],
                             "kind": EXTERNAL_PIN_KIND,
                             "pinned_md5": old, "resigned_md5": new_md5,
                             "snapshot_refreshed": True})
    for snap_abs, up_bytes in plan_writes:
        with io.open(snap_abs, "wb") as fh:
            fh.write(up_bytes)
    with io.open(seed_path, "wb") as fh:
        fh.write(dumps_seed(doc))
    sys.stderr.write("%s: re-signed %d pin(s); verifying\n"
                     % (TOOL, len(resigned)))
    ok, verify_detail = verify()
    if ok:
        return {"ok": True, "action": "apply", "resigned": resigned,
                "absent": [absent_row(r) for r in absent],
                "snapshots_refreshed": [os.path.relpath(p, root)
                                        for p, _b in plan_writes],
                "verify": "seeds-suite-green", "seed": seed_path,
                "verdict": verdict}, 0
    with io.open(seed_path, "wb") as fh:
        fh.write(raw)
    restored = True
    try:
        with io.open(seed_path, "rb") as fh:
            restored = fh.read() == raw
    except OSError:
        restored = False
    snap_done, snap_failed = restore_snapshots(snapshot_backups)
    rollback = ("byte-identical"
                if (restored and not snap_failed) else "FAILED")
    sys.stderr.write("%s: verification red (%s); rollback %s (seed %s,"
                     " snapshots restored %d, failed %d)\n"
                     % (TOOL, verify_detail, rollback,
                        "byte-identical" if restored else "FAILED",
                        len(snap_done), len(snap_failed)))
    return {"ok": False, "stage": "verify", "action": "apply-rolled-back",
            "verify": verify_detail, "resigned": resigned,
            "rollback": rollback,
            "rollback_snapshots": {"restored": len(snap_done),
                                   "failed": snap_failed},
            "seed": seed_path, "verdict": verdict}, 4


def emit(report):
    print(json.dumps(report, ensure_ascii=False))


# --- selftest (offline, temporary fixtures; a fixture git repository
# holds the repo-pin faces, stub gates stand in for the sync tool so the
# vectors isolate this tool's pin semantics, and nothing outside the
# temp directory is written) ---

# synthetic single entry: a shape-realistic entry body for the fixture
# seed (the stub gate does not judge entries, so no standing-seed
# coupling is needed)
FX_ENTRY = {
    "id": "J001", "face": "alpha", "standard": "one",
    "standard_language": "en",
    "standard_source": ("rocqwash docs/jargon-to-standard-mapping-v1.md"
                        " (in-repo-md-v1)"),
    "source_line": 1, "disposition": "replace", "exempts": [],
    "cross_track_note": None, "note": "clean note.",
}

FX_SEED_DOC = {
    "schema": "rocqwash-jargon-map/1",
    "engine": "jargon",
    "count": 0,
    "note": "fixture seed for the pin repair selftest",
    "provenance": {
        "transcription": "fixture map for the pin repair selftest",
        "sources": [],
    },
    "entries": [],
}


def _fixture_repo(tmp):
    """A throwaway git repository inside the temp directory: the sandbox
    the repo-pin vectors judge against.  git init/add/commit are local
    object-database operations; the whole fixture stays offline."""
    repo = os.path.join(tmp, "pinrepo")
    os.makedirs(repo)

    def git(*args):
        proc = subprocess.run(["git"] + list(args), cwd=repo,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=60)
        if proc.returncode != 0:
            raise AssertionError("fixture git %s failed: %s"
                                 % (args[0], (proc.stderr or "").strip()))
        return proc.stdout.strip()

    git("init", "-q")
    git("config", "core.autocrlf", "false")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "fixture")
    return repo, git


def run_selftest(args):
    results = []
    tmp = tempfile.mkdtemp(prefix="rqw_pin_repair_")
    try:
        repo, git = _fixture_repo(tmp)
        seed_path = os.path.join(tmp, "seed.json")
        repo_rel_path = "mapping-fixture.md"
        repo_file = os.path.join(repo, repo_rel_path)
        upstream = os.path.join(tmp, "upstream-original.md")
        snapshot_rel = "snapshot-fixture-source.md"
        snapshot_abs = os.path.join(repo, snapshot_rel)

        def write_bytes(path, data):
            with io.open(path, "wb") as fh:
                fh.write(data)

        def read_bytes(path):
            with io.open(path, "rb") as fh:
                return fh.read()

        def md5_bytes(data):
            return hashlib.md5(data).hexdigest()

        def repo_source(sha):
            return {"locator": "repo", "path": repo_rel_path,
                    "role": "fixture repo source",
                    "pin": {"kind": REPO_PIN_KIND, "value": sha}}

        def external_source(md5v):
            return {"locator": "external", "path": snapshot_rel,
                    "role": "fixture external source",
                    "upstream_path": upstream,
                    "pin": {"kind": EXTERNAL_PIN_KIND, "value": md5v}}

        def make_seed(repo_sha, snap_bytes, ext_md5):
            write_bytes(snapshot_abs, snap_bytes)
            doc = json.loads(json.dumps(FX_SEED_DOC))
            doc["count"] = 1
            doc["entries"] = json.loads(json.dumps([FX_ENTRY]))
            doc["provenance"]["sources"] = [repo_source(repo_sha),
                                            external_source(ext_md5)]
            write_bytes(seed_path, dumps_seed(doc))

        def in_sync_gate():
            return ("VERDICT IN-SYNC (fixture stub)",
                    "VERDICT IN-SYNC (fixture stub)")

        def pending_gate():
            return ("VERDICT PENDING (fixture stub)",
                    "VERDICT PENDING (fixture stub)")

        def green_verify():
            return True, "stub verification pass (fixture)"

        def red_verify():
            return False, "stub verification failure (fixture)"

        def plan():
            return flow("plan", seed_path, in_sync_gate, root=repo)

        def apply(verify=green_verify):
            return flow("apply", seed_path, in_sync_gate,
                        verify=verify, root=repo)

        # fixture content, committed so the blob judgment has a HEAD face
        repo_v1 = b"repo fixture bytes v1\n"
        write_bytes(repo_file, repo_v1)
        git("add", repo_rel_path)
        git("commit", "-q", "-m", "fixture content v1")
        head_sha = git("rev-parse", "HEAD:" + repo_rel_path)
        wrong_sha = "0123456789abcdef0123456789abcdef01234567"
        upstream_v1 = b"upstream original bytes v1\n"
        write_bytes(upstream, upstream_v1)
        md5_v1 = md5_bytes(upstream_v1)
        corrupt = b"corrupted snapshot bytes\n"

        # vector 1: every pin matches its judged face -> action none
        make_seed(head_sha, upstream_v1, md5_v1)
        rep, code = plan()
        rep2, code2 = apply()
        ok = (code == 0 and rep.get("action") == "none"
              and rep.get("drifted") == []
              and code2 == 0 and rep2.get("action") == "none")
        _vec(results, "insync-matching-pins-none", ok,
             "IN-SYNC gate over matching repo blob and snapshot md5 pins"
             " reports action none in both modes"
             if ok else "plan=%r apply=%r" % (rep, rep2))

        # vector 2: repo pin drift; plan reports head vs pinned blob sha
        make_seed(wrong_sha, upstream_v1, md5_v1)
        rep, code = plan()
        drift = rep.get("drifted") or []
        ok = (code == 0 and rep.get("action") == "plan" and len(drift) == 1
              and drift[0]["locator"] == "repo"
              and drift[0]["state"] == "drifted"
              and drift[0]["head_blob_sha"] == head_sha
              and drift[0]["pinned_blob_sha"] == wrong_sha)
        _vec(results, "repo-drift-plan-reports-blob-judgment", ok,
             "plan lists the drifted repo pin with its committed and"
             " pinned blob shas"
             if ok else "rc=%d report=%r" % (code, rep))

        # vector 3: apply re-signs the repo pin to the working bytes'
        # blob sha; every other byte of the seed file survives
        raw_before = read_bytes(seed_path)
        rep, code = apply()
        raw_after = read_bytes(seed_path)
        expected = (raw_before.replace(wrong_sha.encode("ascii"),
                                       head_sha.encode("ascii"))
                    if raw_before.count(wrong_sha.encode("ascii")) == 1
                    else None)
        ok = (code == 0 and rep.get("action") == "apply"
              and rep.get("verify") == "seeds-suite-green"
              and expected is not None and raw_after == expected)
        _vec(results, "repo-drift-apply-resigns-blob-sha", ok,
             "apply rewrote exactly the drifted pin value to the working"
             " bytes' blob sha; all other bytes survived; verification"
             " green"
             if ok else "rc=%d report=%r" % (code, rep))

        # vector 4: corrupted snapshot; consistency red, freshness green;
        # apply refreshes the snapshot from the upstream bytes
        make_seed(head_sha, corrupt, md5_v1)
        rep, code = plan()
        drift = rep.get("drifted") or []
        ok_plan = (code == 0 and rep.get("action") == "plan"
                   and len(drift) == 1
                   and drift[0]["locator"] == "external"
                   and drift[0]["consistency"] == "drifted"
                   and drift[0]["freshness"] == "fresh")
        rep, code = apply()
        ok = (ok_plan and code == 0 and rep.get("action") == "apply"
              and read_bytes(snapshot_abs) == upstream_v1)
        _vec(results, "snapshot-corruption-refreshed-from-upstream", ok,
             "consistency drift with a fresh upstream refreshes the"
             " snapshot bytes from the upstream original"
             if ok else "plan=%r apply=%r" % (rep, ok_plan))

        # vector 5: upstream drift; apply re-signs the md5 from the
        # upstream bytes and refreshes the snapshot to them
        upstream_v2 = b"upstream original bytes v2\n"
        write_bytes(upstream, upstream_v2)
        md5_v2 = md5_bytes(upstream_v2)
        make_seed(head_sha, upstream_v1, md5_v1)
        rep, code = plan()
        drift = rep.get("drifted") or []
        ok_plan = (code == 0 and rep.get("action") == "plan"
                   and len(drift) == 1
                   and drift[0]["consistency"] == "matched"
                   and drift[0]["freshness"] == "drifted")
        rep, code = apply()
        doc_after = json.loads(read_bytes(seed_path).decode("utf-8"))
        ok = (ok_plan and code == 0 and rep.get("action") == "apply"
              and read_bytes(snapshot_abs) == upstream_v2
              and doc_after["provenance"]["sources"][1]["pin"]["value"]
              == md5_v2)
        _vec(results, "upstream-drift-resigned-from-upstream-bytes", ok,
             "freshness drift re-signs the pin from the upstream bytes"
             " and refreshes the snapshot to them"
             if ok else "plan=%r apply=%r" % (rep, ok_plan))

        # vector 6: upstream absent; the source is recorded absent with
        # the declared notice while the drifted repo pin still applies
        os.remove(upstream)
        make_seed(wrong_sha, upstream_v2, md5_v2)
        rep, code = apply()
        doc_after = json.loads(read_bytes(seed_path).decode("utf-8"))
        absent = rep.get("absent") or []
        ok = (code == 0 and rep.get("action") == "apply"
              and len(absent) == 1
              and absent[0].get("declared") == UPSTREAM_ABSENT_NOTICE
              and doc_after["provenance"]["sources"][0]["pin"]["value"]
              == head_sha
              and doc_after["provenance"]["sources"][1]["pin"]["value"]
              == md5_v2)
        _vec(results, "upstream-absent-recorded-apply-continues", ok,
             "an upstream-absent source is recorded absent with the"
             " declared notice while the repo pin still re-signs; apply"
             " does not refuse"
             if ok else "rc=%d report=%r" % (code, rep))

        # vector 7: snapshot red with the upstream gone is a blocked red
        # the plan names without crashing
        make_seed(head_sha, corrupt, md5_v2)
        rep, code = plan()
        blocked = rep.get("blocked") or []
        ok = (code == 0 and rep.get("action") == "plan"
              and len(blocked) == 1
              and blocked[0]["consistency"] == "drifted"
              and blocked[0]["freshness"] == "upstream-absent")
        _vec(results, "blocked-red-named-by-plan", ok,
             "a consistency red whose upstream is absent is reported as"
             " a blocked red, not silently dropped"
             if ok else "rc=%d report=%r" % (code, rep))

        # vector 8: a PENDING gate verdict escalates exit 3, zero write
        make_seed(head_sha, upstream_v2, md5_v2)
        raw_before = read_bytes(seed_path)
        rep, code = flow("plan", seed_path, pending_gate, root=repo)
        ok = (code == 3 and rep.get("ok") is False
              and rep.get("stage") == "plan"
              and (rep.get("verdict") or "").startswith("VERDICT PENDING")
              and read_bytes(seed_path) == raw_before)
        _vec(results, "gate-pending-exit-3-zero-write", ok,
             "PENDING gate verdict escalates exit 3 with the raw verdict"
             " line and the seed untouched"
             if ok else "rc=%d report=%r" % (code, rep))

        # vector 9: a red verification rolls the seed and every refreshed
        # snapshot back byte-identically
        upstream_v3 = b"upstream original bytes v3\n"
        write_bytes(upstream, upstream_v3)
        md5_v3 = md5_bytes(upstream_v3)
        make_seed(wrong_sha, corrupt, md5_v3)
        raw_before = read_bytes(seed_path)
        snap_before = read_bytes(snapshot_abs)
        rep, code = apply(verify=red_verify)
        ok = (code == 4 and rep.get("action") == "apply-rolled-back"
              and rep.get("rollback") == "byte-identical"
              and read_bytes(seed_path) == raw_before
              and read_bytes(snapshot_abs) == snap_before)
        _vec(results, "verify-red-rolls-back-byte-identical", ok,
             "a red verification restored the seed bytes and the"
             " refreshed snapshot bytes exactly, exit 4"
             if ok else "rc=%d report=%r" % (code, rep))

        # vector 10: CLI usage conflicts exit 2 before any file is read
        proc = subprocess.run(
            [sys.executable, "-I", os.path.abspath(__file__),
             "--plan", "--apply", "--seed", seed_path],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60)
        ok = proc.returncode == 2
        _vec(results, "usage-conflict-exit-2", ok,
             "combining --plan with --apply is a usage error, exit 2"
             if ok else "rc=%d out=%r" % (proc.returncode,
                                          proc.stderr[:120]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = 0
    for name, ok, detail in results:
        if ok:
            tag = "PASS"
        else:
            tag = "FAIL"
            failed += 1
        print("%s %s - %s" % (tag, name, detail))
    print("summary: %d vectors, %d FAIL" % (len(results), failed))
    if failed:
        print("PIN-REPAIR-SELFTEST RED (%d)" % failed)
        return 1
    print("PIN-REPAIR-SELFTEST PASS")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog=TOOL)
    ap.add_argument("--selftest", action="store_true",
                    help="run the selftest vectors; standalone")
    ap.add_argument("--plan", action="store_true",
                    help="report drifted pins per provenance v2;"
                         " writes nothing")
    ap.add_argument("--apply", action="store_true",
                    help="re-sign drifted pins (blob sha for repo"
                         " sources, snapshot refresh plus md5 for"
                         " external sources), then verify and roll back"
                         " on a red verification")
    ap.add_argument("--seed", metavar="P", default=DEFAULT_SEED_PATH,
                    help="seed map JSON (default: seeds/jargon/jargon-map"
                         ".json)")
    args = ap.parse_args(argv)
    modes = [flag for flag in (args.selftest, args.plan, args.apply) if flag]
    if len(modes) != 1:
        fail("pick exactly one of --selftest / --plan / --apply", 2)
    if args.selftest:
        return run_selftest(args)
    mode = "apply" if args.apply else "plan"
    seed = resolve_path(args.seed)
    report, code = flow(mode, seed, default_gate_cmd(seed))
    emit(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
