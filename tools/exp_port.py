#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""exp_port: experience-bus port for docs/exp-ledger.jsonl (append + query).

Purpose.  Single write/read port of docs/exp-ledger.jsonl (one JSON
  object per line, schema rocqwash-exp/1).  `append` validates a
  four-field entry (tool / points / evidence / batch) and appends exactly
  one line under an entry id; a repeat of an already-seen entry (same
  explicit id, or same content fingerprint) is a loud no-op returning the
  existing id, so retries stay idempotent.  `query` reads entries back by
  id, tool or batch substring; a finding (duplicate, zero matches) is
  data and never escalates the exit code; corruption is loud.

Interface.  `append --tool T --points P [--evidence E] [--batch B] [--actor A]
  [--id ID] [--ts TS] [--source-file P] [--correlation-id ID] [--ledger P]
  [--dry-run]` | `query [--id ID] [--tool SUB] [--batch SUB] [--limit N]
  [--ledger P]` | `--selftest`.  Ledger resolution and stdout faces:
  see the extended contract below.

Dependencies.  Python 3 standard library only; zero network; plain JSONL
  with one-process-at-a-time discipline.

Evidence.  --selftest on temporary fixtures: minted-id persistence,
  idempotent re-append, explicit-id duplicate, dry-run zero-write, carried
  id/ts/provenance, corrupt-ledger fail loud without writing, query
  vectors, the minted-id sequence, the actor schema-increment field
  (see the extended contract below), CLI exit codes.

Exit-codes.  0 appended / duplicate-skip / query answered (matches are
  data); 1 selftest red; 2 usage error; 9 missing or corrupt input.
"""
# Extended contract (help face; kept outside the five-field block so the
# header stays within the 30-line budget of the annotation standard):
#
# Entry shape (rocqwash-exp/1)
#   schema       constant "rocqwash-exp/1"
#   id           caller-supplied verbatim, or minted EXP-<YYYYMMDD>-<NNNN>
#                (per-date sequence continues from existing entries)
#   ts           caller-supplied ISO date/timestamp, or the current UTC time
#   tool         required, non-empty: the tool or workflow the entry is about
#   points       required, non-empty: one-line takeaways
#   evidence     optional: pointer to the evidence surface (path:lines, run id)
#   batch        optional: batch label grouping related entries
#   fingerprint  sha256 of the four carrier fields; the seen-set key that
#                makes repeated appends idempotent without an explicit id
#   correlationId  optional schema-increment field (additive): a run
#                report id threading exp/round/event accounts together; the
#                fingerprint does not cover it, so the idempotent seen set
#                stays on the four carrier fields exactly as before
#   actor        optional schema-increment field (additive): the actor
#                (agent or operator name) of the entry, carried verbatim on
#                the appended row when provided (empty default: the key is
#                omitted); the fingerprint does not cover it either, so
#                actor-bearing and actor-less re-appends of the same four
#                carrier fields stay one idempotent entry
#   source       optional: verbatim import provenance (--source-file JSON
#                object), so a foreign draft's extra fields survive the ride
#
# Idempotent seen set
#   On append the port reads the whole ledger and refuses nothing silently:
#   an explicit --id already present, or a fingerprint already present,
#   prints `duplicate-skip id=<existing>` and exits 0 without writing.
#
# Ledger resolution and stdout faces
#   --ledger wins, then ROCWASH_EXPERIENCE_DIR, then
#   <repo>/docs/exp-ledger.jsonl.  Stdout carries `appended id=<ID>`,
#   `duplicate-skip id=<ID>` or `dry-run id=<ID>` (nothing written).
#
# Fail-loud face
#   A ledger line that is not a JSON object exits 9 naming the line number,
#   before any write is attempted (no partial append, no silent rebuild).
#   A ledger absent at query time exits 9; at append time it is created.

import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys
import tempfile

SCHEMA = "rocqwash-exp/1"
LEDGER_NAME = "exp-ledger.jsonl"
ENV_DIR = "ROCWASH_EXPERIENCE_DIR"
SELFTEST_MARK = "EXP-PORT-SELFTEST PASS"
SEP = "\x1f"


def repo_root():
    """Repository root: the parent of tools/ (this file lives in tools/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_ledger(explicit):
    """--ledger wins, then the env directory, then the in-repo default."""
    if explicit:
        return explicit
    env_dir = os.environ.get(ENV_DIR, "")
    if env_dir:
        return os.path.join(env_dir, LEDGER_NAME)
    return os.path.join(repo_root(), "docs", LEDGER_NAME)


def read_ledger(path):
    """Parse the ledger into a list of entry dicts; fail loud on damage."""
    if not os.path.isfile(path):
        return None
    entries = []
    with open(path, "r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError as exc:
                raise CorruptLedger(
                    "ledger line %d is not valid JSON (%s): %s"
                    % (lineno, exc, os.path.abspath(path)))
            if not isinstance(obj, dict):
                raise CorruptLedger(
                    "ledger line %d is not a JSON object: %s"
                    % (lineno, os.path.abspath(path)))
            entries.append(obj)
    return entries


class CorruptLedger(Exception):
    """Raised on a ledger the port cannot parse; callers exit 9."""


def fingerprint(tool, points, evidence, batch):
    """Stable content key over the four carrier fields."""
    payload = SEP.join([tool, points, evidence, batch])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def mint_id(entries, now):
    """EXP-<YYYYMMDD>-<NNNN>, continuing the per-date sequence on disk."""
    prefix = "EXP-" + now.strftime("%Y%m%d") + "-"
    top = 0
    for entry in entries:
        eid = entry.get("id", "")
        if isinstance(eid, str) and eid.startswith(prefix):
            tail = eid[len(prefix):]
            if tail.isdigit():
                top = max(top, int(tail))
    return "%s%04d" % (prefix, top + 1)


def valid_ts(text):
    """Accept an ISO date or a full ISO timestamp; anything else is usage."""
    head = text.split("T", 1)[0]
    try:
        datetime.date.fromisoformat(head)
    except ValueError:
        return False
    return True


def _utcnow():
    """Timezone-aware UTC now (datetime.utcnow is deprecated in 3.12+)."""
    return datetime.datetime.now(datetime.timezone.utc)


def cmd_append(args):
    path = resolve_ledger(args.ledger)
    try:
        entries = read_ledger(path)
    except CorruptLedger as exc:
        sys.stderr.write("exp_port append: %s\n" % exc)
        return 9
    existing = entries if entries is not None else []

    source = None
    if args.source_file:
        try:
            with open(args.source_file, "r", encoding="utf-8") as handle:
                source = json.load(handle)
        except (OSError, ValueError) as exc:
            sys.stderr.write(
                "exp_port append: --source-file unreadable: %s\n" % exc)
            return 9
        if not isinstance(source, dict):
            sys.stderr.write(
                "exp_port append: --source-file must hold a JSON object\n")
            return 2

    fp = fingerprint(args.tool, args.points, args.evidence, args.batch)
    seen_ids = {}
    seen_fps = {}
    for entry in existing:
        eid = entry.get("id")
        if isinstance(eid, str) and eid:
            seen_ids.setdefault(eid, entry)
        mark = entry.get("fingerprint")
        if isinstance(mark, str) and mark:
            seen_fps.setdefault(mark, entry)

    entry = {
        "schema": SCHEMA,
        "id": args.id,
        "ts": args.ts,
        "tool": args.tool,
        "points": args.points,
        "evidence": args.evidence,
        "batch": args.batch,
        "fingerprint": fp,
    }
    if source is not None:
        entry["source"] = source
    if args.correlation_id:
        entry["correlationId"] = args.correlation_id
    # actor rides the row only when provided (empty default omits the key);
    # it is outside the fingerprint, so the seen-set behavior above is
    # unchanged for every pre-actor caller.
    if getattr(args, "actor", ""):
        entry["actor"] = args.actor

    if args.id and args.id in seen_ids:
        sys.stdout.write("duplicate-skip id=%s axis=id ledger=%s\n"
                         % (args.id, path))
        return 0
    if fp in seen_fps:
        sys.stdout.write("duplicate-skip id=%s axis=fingerprint ledger=%s\n"
                         % (seen_fps[fp].get("id", "?"), path))
        return 0

    if not args.id:
        entry["id"] = mint_id(existing, _utcnow())
    if not valid_ts(entry["ts"]):
        sys.stderr.write(
            "exp_port append: --ts must be an ISO date or timestamp: %s\n"
            % entry["ts"])
        return 2

    line = json.dumps(entry, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))
    if args.dry_run:
        sys.stdout.write("dry-run id=%s would-append ledger=%s\n"
                         % (entry["id"], path))
        return 0

    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
    sys.stdout.write("appended id=%s ledger=%s\n" % (entry["id"], path))
    return 0


def cmd_query(args):
    path = resolve_ledger(args.ledger)
    try:
        entries = read_ledger(path)
    except CorruptLedger as exc:
        sys.stderr.write("exp_port query: %s\n" % exc)
        return 9
    if entries is None:
        sys.stderr.write("exp_port query: ledger not found: %s\n"
                         % os.path.abspath(path))
        return 9
    picked = []
    for entry in entries:
        if args.id and entry.get("id") != args.id:
            continue
        if args.tool and args.tool.lower() not in \
                str(entry.get("tool", "")).lower():
            continue
        if args.batch and args.batch.lower() not in \
                str(entry.get("batch", "")).lower():
            continue
        picked.append(entry)
    if args.limit is not None and args.limit >= 0:
        picked = picked[:args.limit]
    for entry in picked:
        sys.stdout.write(json.dumps(entry, ensure_ascii=False,
                                    sort_keys=True, separators=(",", ":")) + "\n")
    sys.stderr.write("query: %d/%d entries matched (ledger=%s)\n"
                     % (len(picked), len(entries), path))
    return 0


def selftest():
    """Temporary-fixture vectors; prints SELFTEST PASS, exits 0 on green."""
    fails = []
    tmp = tempfile.mkdtemp(prefix="exp_port_selftest_")
    try:
        ledger = os.path.join(tmp, "ledgers", "exp-ledger.jsonl")

        # V1: append mints an id and persists the four carrier fields.
        rc, out = _run(["append", "--tool", "toolA", "--points", "p1",
                        "--evidence", "e1", "--batch", "b1",
                        "--ledger", ledger])
        first_id = None
        if rc != 0 or not out.startswith("appended id="):
            fails.append("V1 append should exit 0 with 'appended id=' (rc=%d out=%r)" % (rc, out))
        else:
            first_id = out.split("id=", 1)[1].split()[0]
            entry = _last_entry(ledger)
            if (entry.get("tool"), entry.get("points"), entry.get("evidence"),
                    entry.get("batch")) != ("toolA", "p1", "e1", "b1"):
                fails.append("V1 carrier fields not persisted: %r" % entry)
            if entry.get("schema") != SCHEMA or not entry.get("fingerprint"):
                fails.append("V1 envelope fields missing: %r" % entry)

        # V2: idempotent re-append (same content) skips byte-identically.
        before = _bytes(ledger)
        rc, out = _run(["append", "--tool", "toolA", "--points", "p1",
                        "--evidence", "e1", "--batch", "b1",
                        "--ledger", ledger])
        if rc != 0 or not out.startswith("duplicate-skip id="):
            fails.append("V2 re-append should skip rc=0 (rc=%d out=%r)" % (rc, out))
        if _bytes(ledger) != before:
            fails.append("V2 ledger changed on duplicate append")
        if first_id and first_id not in out:
            fails.append("V2 skip line should name the existing id: %r" % out)

        # V3: an explicit id already present skips on the id axis.
        rc, out = _run(["append", "--tool", "other", "--points", "x",
                        "--id", first_id or "EXP-X", "--ledger", ledger])
        if rc != 0 or "axis=id" not in out:
            fails.append("V3 explicit-id duplicate should skip axis=id (rc=%d out=%r)" % (rc, out))

        # V4: dry-run writes nothing (absent ledger stays absent, bytes hold).
        dry_ledger = os.path.join(tmp, "dry", "exp-ledger.jsonl")
        rc, out = _run(["append", "--tool", "t", "--points", "p",
                        "--ledger", dry_ledger, "--dry-run"])
        if rc != 0 or not out.startswith("dry-run id="):
            fails.append("V4 dry-run should report dry-run id= rc=0 (rc=%d out=%r)" % (rc, out))
        if os.path.exists(dry_ledger):
            fails.append("V4 dry-run created the ledger file")
        rc, out = _run(["append", "--tool", "t2", "--points", "p2",
                        "--ledger", ledger, "--dry-run"])
        if _bytes(ledger) != before:
            fails.append("V4 dry-run on a live ledger changed bytes")

        # V5: a carried id and import provenance survive the ride.
        src = os.path.join(tmp, "src.json")
        with open(src, "w", encoding="utf-8") as handle:
            json.dump({"orig_id": "RQW04-20261113-001", "extra": "kept"},
                      handle)
        rc, out = _run(["append", "--tool", "draftTool", "--points", "dp",
                        "--id", "RQW04-20261113-001", "--ts", "2026-11-13",
                        "--source-file", src, "--ledger", ledger])
        if rc != 0 or "appended id=RQW04-20261113-001" not in out:
            fails.append("V5 carried-id append failed (rc=%d out=%r)" % (rc, out))
        else:
            entry = _last_entry(ledger)
            if entry.get("ts") != "2026-11-13":
                fails.append("V5 ts not carried: %r" % entry)
            if entry.get("source", {}).get("orig_id") != "RQW04-20261113-001":
                fails.append("V5 source provenance lost: %r" % entry)

        # V6: a corrupt ledger line fails loud rc=9 and nothing is written.
        bad = os.path.join(tmp, "bad", "exp-ledger.jsonl")
        os.makedirs(os.path.dirname(bad), exist_ok=True)
        with open(bad, "w", encoding="utf-8") as handle:
            handle.write('{"id": "ok-1", "fingerprint": "f"}\n')
            handle.write("not-json{\n")
        size_before = _bytes(bad)
        rc, out = _run(["append", "--tool", "t", "--points", "p",
                        "--ledger", bad])
        if rc != 9:
            fails.append("V6 corrupt ledger should exit 9 (rc=%d out=%r)" % (rc, out))
        if _bytes(bad) != size_before:
            fails.append("V6 corrupt-ledger append wrote bytes")
        rc, out = _run(["query", "--ledger", bad])
        if rc != 9:
            fails.append("V6 corrupt ledger query should exit 9 (rc=%d)" % rc)

        # V7: query by id / tool / batch; zero match is data, exit 0.
        rc, out = _run(["query", "--id", "RQW04-20261113-001",
                        "--ledger", ledger])
        if rc != 0 or "draftTool" not in out:
            fails.append("V7 query --id failed (rc=%d out=%r)" % (rc, out))
        rc, out = _run(["query", "--tool", "toolA", "--ledger", ledger])
        if rc != 0 or "toolA" not in out:
            fails.append("V7 query --tool failed (rc=%d)" % rc)
        rc, out = _run(["query", "--batch", "b1", "--ledger", ledger])
        if rc != 0 or "toolA" not in out:
            fails.append("V7 query --batch failed (rc=%d)" % rc)
        rc, out = _run(["query", "--id", "no-such-id", "--ledger", ledger])
        if rc != 0:
            fails.append("V7 zero match should stay exit 0 (rc=%d)" % rc)

        # V8: query on an absent ledger exits 9 (fail loud, no silent empty).
        absent = os.path.join(tmp, "absent", "exp-ledger.jsonl")
        rc, out = _run(["query", "--ledger", absent])
        if rc != 9:
            fails.append("V8 absent-ledger query should exit 9 (rc=%d)" % rc)

        # V9: minted ids continue the per-date sequence on disk.
        rc, out = _run(["append", "--tool", "t3", "--points", "p3",
                        "--ledger", ledger])
        if rc != 0 or not out.startswith("appended id=EXP-"):
            fails.append("V9 minted id should follow EXP-<date>-<seq> (rc=%d out=%r)" % (rc, out))
        else:
            minted = out.split("id=", 1)[1].split()[0]
            if first_id and minted == first_id:
                fails.append("V9 minted id collided with the first id")

        # V10: the actor schema-increment field rides the row verbatim when
        # provided, is omitted without it, and stays outside the fingerprint
        # seen set (same four carrier fields with a different actor still
        # duplicate-skips, so pre-actor idempotence is preserved).
        rc, out = _run(["append", "--tool", "actorTool", "--points", "ap",
                        "--actor", "seat-A", "--ledger", ledger])
        if rc != 0 or not out.startswith("appended id="):
            fails.append("V10 actor append should exit 0 (rc=%d out=%r)" % (rc, out))
        else:
            entry = _last_entry(ledger)
            if entry.get("actor") != "seat-A":
                fails.append("V10 actor not carried verbatim: %r" % entry)
        before_v10 = _bytes(ledger)
        rc, out = _run(["append", "--tool", "actorTool", "--points", "ap",
                        "--actor", "seat-B", "--ledger", ledger])
        if rc != 0 or "axis=fingerprint" not in out:
            fails.append("V10 actor change should still duplicate-skip on the "
                         "carrier fingerprint (rc=%d out=%r)" % (rc, out))
        if _bytes(ledger) != before_v10:
            fails.append("V10 actor-only re-append changed the ledger")
        rc, out = _run(["append", "--tool", "bareTool", "--points", "bp",
                        "--ledger", ledger])
        if rc != 0 or not out.startswith("appended id="):
            fails.append("V10 no-actor append should exit 0 (rc=%d out=%r)" % (rc, out))
        else:
            entry = _last_entry(ledger)
            if "actor" in entry:
                fails.append("V10 default append must omit the actor key: %r" % entry)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for line in fails:
            sys.stderr.write("SELFTEST FAIL %s\n" % line)
        return 1
    sys.stdout.write("%s (10 vectors)\n" % SELFTEST_MARK)
    return 0


def _run(args):
    """Run this tool in-process via the CLI parser (fixture vectors only)."""
    argv = list(args)
    saved = (sys.stdout, sys.stderr)
    sys.stdout = io_bytes = StringIO()
    sys.stderr = io_err = StringIO()
    try:
        rc = main(argv)
    finally:
        sys.stdout, sys.stderr = saved
    return rc, io_bytes.getvalue()


class StringIO:
    """Minimal text sink (stdlib io.StringIO keeps module imports tight)."""

    def __init__(self):
        self.parts = []

    def write(self, text):
        self.parts.append(text)

    def getvalue(self):
        return "".join(self.parts)


def _bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def _last_entry(path):
    with open(path, "r", encoding="utf-8") as handle:
        lines = [raw for raw in handle if raw.strip()]
    return json.loads(lines[-1])


def build_parser():
    parser = argparse.ArgumentParser(
        prog="exp_port.py",
        description="Experience-bus port: append/query docs/exp-ledger.jsonl "
                    "(schema rocqwash-exp/1, idempotent seen set).")
    parser.add_argument("--selftest", action="store_true",
                        help="run the temporary-fixture vector group")
    parser.add_argument("command", nargs="?", choices=("append", "query"),
                        help="append one entry (idempotent) | read the ledger back")
    parser.add_argument("--tool", default="",
                        help="append: tool or workflow name (required); query: tool substring")
    parser.add_argument("--points", default="",
                        help="append: one-line takeaways (required)")
    parser.add_argument("--evidence", default="", help="append: evidence pointer")
    parser.add_argument("--batch", default="",
                        help="append: batch label; query: batch substring")
    parser.add_argument("--actor", default="",
                        help="append: optional actor (seat or operator name) "
                             "carried verbatim as the actor field (schema "
                             "increment, not part of the fingerprint seen "
                             "set)")
    parser.add_argument("--id", default="",
                        help="append: carry an explicit entry id; query: exact entry id")
    parser.add_argument("--ts", default="",
                        help="append: ISO date/timestamp (default: now UTC)")
    parser.add_argument("--source-file", default="", dest="source_file",
                        help="append: JSON object kept verbatim as import provenance")
    parser.add_argument("--correlation-id", default="", dest="correlation_id",
                        help="append: optional run report id carried as "
                             "correlationId (schema increment, not part of "
                             "the fingerprint seen set)")
    parser.add_argument("--ledger", default="", help="ledger path override")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="append: validate and report the would-be id, write nothing")
    parser.add_argument("--limit", type=int, default=None,
                        help="query: cap the number of printed entries")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        if args.command:
            parser.error("--selftest takes no subcommand")
        return selftest()
    if args.command == "append":
        if not args.tool or not args.points:
            parser.error("append requires --tool and --points")
        if not args.ts:
            args.ts = _utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        return cmd_append(args)
    if args.command == "query":
        return cmd_query(args)
    parser.print_usage(sys.stderr)
    sys.stderr.write("exp_port: a subcommand is required: append | query\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
