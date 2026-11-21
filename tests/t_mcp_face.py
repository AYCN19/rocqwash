#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_mcp_face.py - tests/ suite shell for the RQW13 MCP face expansion
(tools/mcp_server.py).

Purpose.  Spawn the expanded MCP stdio server as a child process and drive
  one newline-delimited JSON-RPC session line by line, asserting the
  48-capability face: the RQW08 legacy 8, the RQW13 batch-1 zero-network 13,
  the engine-body ticket's three capabilities (graduated from
  docs/drafts/mcp-tool-specs-engine-body.md by the integration agent), the
  symbiosis ticket's one read-only capability (symbiosis_status, a
  capability_index-style file face over docs/symbiosis_sop.md, registered
  from the symbiosis ticket's spec section 1.1), the MCP
  roster-expansion work stream 1's six capabilities (the M1 ticket, five
  INDEX entries already standing plus the gap_cluster entry that lands with
  the
  same increment), the MCP roster-expansion work stream 2's eleven
  read/plan/partial capabilities (the M2 ticket, survey table 2 rows 7-17:
  all eleven INDEX entries already standing), the tree_audit
  registration increment's one capability (tree_audit, a read-only audit
  face over the landed census CLI tools/tree_audit.py), the
  axiom_sweep registration increment's one capability (axiom_sweep, a
  read/plan face over the landed Lean axiom-closure classifier
  tools/lean_axiom_sweep.py; its spec description is transcribed from the
  tool's frozen CLI contract header, the INDEX entry awaiting its own
  lane), and the claim_watch registration increment's one capability
  (claim_watch, the net-gated live watch face over the landed native
  resident watch CLI tools/claim_watch.py, ticket 13; its spec
  description is likewise transcribed from the tool's frozen CLI
  contract header), and the v2-B audit-line registration increment's
  three capabilities (source_fetch, the net-gated pinned dual-source
  trap-sniffing fetch face over the landed CLI tools/source_fetch.py;
  sweep_verdict, the zero-network mechanical verdict judge over the
  landed CLI tools/sweep_verdict.py; release_chain, the net-gated
  release chain face over the landed CLI tools/release_chain.py, whose
  schema carries dry_run default true and whose confirm_publish
  description warns it is the publish stop-gate key; each spec
  transcribed from its tool's own frozen CLI contract header, the
  INDEX entries awaiting their own lane), each new capability
  transcribed from its docs/CAPABILITY-INDEX.md section 2 entry line or,
  for the later increments, from the tool's frozen CLI contract header (the
  symbiosis INDEX entry line lands with the integration increment).

Interface.  `python3 tests/t_mcp_face.py` (rostered in tests/run_tests.sh
  as case t_mcp_face on 20261115, audit finding P0-6; the roster count is
  derived one-way from the CASES block in tests/run_tests.sh by doc_lint's
  second check).

Probes (zero network; probes 1-6 run one session in order, probe 7 is a
  separate --help invocation and probes 8-9 separate allow-net sessions
  of the same child shape):
  1  initialize -> protocolVersion echo plus serverInfo name rocqwash-mcp
  2  notifications/initialized -> no response line
  3  tools/list -> exactly the 48 expected names in registration order,
     each with a description and a closed-object inputSchema; plus the
     micro-ticket schema-face vectors over three faces (schema-only):
     exp_append carries the optional actor string
     property outside the required list (mu-1); vacgen_generate mirrors
     the full 20-flag argparse face of tools/vacgen.py one-to-one
     (mu-3); the render_events spec and its events property declare both
     accepted row shapes, rocqwash-sentinel-event/1 and rocqwash-exp/1
     (mu-4)
  4  live-call spot checks (three of the new batch, all zero network):
     4a http_backoff (no arguments; fixed --selftest) -> exit code: 0 with
        the frozen-vector pass face
     4b norm_lint {"selftest": true} -> exit code: 0 with the selftest
        final PASS line
     4c chain_graph {"ledgers": [a.json, b.json]} on two synthetic tmp
        ledgers -> exit code: 0 and a chain root in the markdown output
        (evidence for the array positional path: two array elements land
        as two positional LEDGER.json paths in one call)
     4d tree_audit {"selftest": true} -> exit code: 0 with the
        fixture-vector green face (the selftest final PASS line)
     4e axiom_sweep {"selftest": true} -> exit code: 0 with the
        fixture-vector green face (the canned offline vectors; zero
        toolchain launch)
     4f sweep_verdict {"lanes": <one synthetic tmp lane dir>, "out":
        <tmp json>} -> exit code: 0 with the GREEN verdict face (the
        v2-B audit-line judge on a temporary fixture; zero network, the
        only write is the caller-named tmp out path)
  5  default deny -> tools/call net_probe returns isError true and names
     ROCQWASH_MCP_ALLOW_NET (the env is removed from the child); the
     same deny face is asserted for claim_watch (probe 5b), the net-gated
     registration increment, whose only ungated face is the offline
     selftest, and for source_fetch and release_chain (probes 5c/5d),
     the two net-gated v2-B audit-line faces, whose live faces are the
     network faces and whose offline faces stay outside the wire face
     (source_fetch's --selftest route) or behind the gate (release_chain
     probe 9)
  6  error faces -> resources/list -32601; unknown tool -32602; unknown
     argument on a new capability -32602; an array item starting with "-"
     -32602; a withheld enum choice on a command-shaped capability (the
     red_dispatch auto preset) -32602; a malformed line -32700 with id null
  7  help gate -> the server's own --help invocation exits 0 with the
     argparse usage face on stdout (the "usage" anchor word and the prog
     name; locks the argparse flag gate against regression)
  8  claim_watch offline-selftest face under the gate (the face vector of
     the claim_watch registration increment, the offline-selftest face
     only): a separate session with ROCQWASH_MCP_ALLOW_NET=1 calls
     claim_watch {"offline_selftest": true} -> exit code: 0 with the
     CLAIM-WATCH-SELFTEST PASS line (canned transport, virtual clock,
     zero network; no live watch face is exercised by this suite)
  9  release_chain offline dry-run face under the gate (the face vector
     of the v2-B audit-line increment, the offline face only): a separate
     session with ROCQWASH_MCP_ALLOW_NET=1 calls release_chain
     {"issue": 7, "release_title": ..., "assets": <tmp dir>} without
     confirm_publish -> exit code: 0 with the dry-run plan face (the
     dry_run schema default true keeps the face offline; zero network,
     "zero calls sent"; no publish face is exercised by this suite)

Dependencies.  Python 3 stdlib only; the server and every called CLI are
  stdlib-only; probes 4a/4b/4c/4f and probe 9 run selftest faces or
  temporary fixtures only; no repository byte is written; zero network.

Evidence.  Every probe asserts a first-hand response line from the child
  server on this machine; nothing is inferred from source reading.

Exit-codes.  0 = all probes pass; 1 = any probe red (fail-loud, the red
  probe is printed; no silent downgrade).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(REPO, "tools", "mcp_server.py")

EXPECTED_TOOLS = [
    # RQW08 legacy 8 (integration order)
    "sentinel_status", "net_probe", "baselinediff", "ci_triage",
    "vacgen_generate", "exp_append", "pushci_status", "capability_index",
    # RQW13 batch-1 zero-network 13 (expansion-ticket order)
    "chain_graph", "doc_lint", "ledger_sync", "netname_normalize",
    "norm_lint", "render_events", "select_audit", "registry_audit",
    "registry_fix", "registry_regen", "registry_union", "abl1_4b_compile",
    "http_backoff",
    # the engine-body ticket's batch (3, graduated from the lane-8
    # draft docs/drafts/mcp-tool-specs-engine-body.md by the integration agent)
    "ai_flavor_detect", "jargon_plan", "i18n_pipeline_dryrun",
    # the symbiosis ticket's one read-only capability (spec section 1.1:
    # a capability_index-style file face over docs/symbiosis_sop.md; its
    # INDEX entry line lands with the integration increment)
    "symbiosis_status",
    # the MCP roster-expansion work stream 1 (the M1 ticket's six read/plan
    # faces:
    # termbase/verdict_diff/learning_feedback/b_gate_audit read,
    # evolution_dashboard/gap_cluster plan; each spec transcribed from its
    # docs/CAPABILITY-INDEX.md section 2 entry line)
    "termbase", "verdict_diff", "learning_feedback", "b_gate_audit",
    "evolution_dashboard", "gap_cluster",
    # the MCP roster-expansion work stream 2 (the M2 ticket's eleven
    # read/plan/partial faces, survey table 2 rows 7-17: repair_weekly /
    # roster_resync / scheduler_lite plan, axiom_guard read,
    # symbiosis_bus_export / uplink_verify / i18n_translate_handoff /
    # i18n_verify / red_dispatch_report / ai_flavor_apply_plan /
    # row_render_check partial; the three http provider legs stay
    # unregistered, and the apply, import, intake, ingest, and auto-tier
    # faces stay CLI-side per the plan-first layer law; each spec
    # transcribed from its docs/CAPABILITY-INDEX.md section 2 entry line)
    "repair_weekly", "roster_resync", "scheduler_lite", "axiom_guard",
    "symbiosis_bus_export", "uplink_verify", "i18n_translate_handoff",
    "i18n_verify", "red_dispatch_report", "ai_flavor_apply_plan",
    "row_render_check",
    # the tree_audit registration increment (one read-only audit face over
    # the landed census CLI tools/tree_audit.py)
    "tree_audit",
    # the axiom_sweep registration increment (one read/plan face over the
    # landed Lean axiom-closure classifier tools/lean_axiom_sweep.py)
    "axiom_sweep",
    # the claim_watch registration increment (ticket 13 rocqwash side: the
    # net-gated live watch face over the landed native resident watch CLI
    # tools/claim_watch.py; default deny, the offline selftest face is the
    # only ungated face)
    "claim_watch",
    # the v2-B audit-line registration increment (three faces over the
    # landed audit-line CLIs: source_fetch, the net-gated pinned
    # dual-source trap-sniffing fetch face; sweep_verdict, the
    # zero-network mechanical verdict judge; release_chain, the
    # net-gated release chain face whose schema carries dry_run default
    # true and whose confirm_publish description warns it is the publish
    # stop-gate key; each spec transcribed from its tool's own frozen
    # CLI contract header, the INDEX entries awaiting their own lane)
    "source_fetch", "sweep_verdict", "release_chain",
]

# Frozen micro-ticket vector (mu-3): the full argparse flag face of
# tools/vacgen.py in argparse declaration order; the vacgen_generate
# schema properties must match this list one-to-one (the schema was
# expanded from the previous 11-flag subset; a roster change would
# re-freeze EXPECTED_TOOLS, a vacgen flag change re-freezes this list).
EXPECTED_VACGEN_ARGS = [
    "input", "out", "toolchain", "snapshot", "audit_id", "name",
    "worktree", "lake", "guard", "core", "force", "taxonomy",
    "preflight_all", "census", "root", "cluster_table", "report",
    "exp_draft", "verify_anchors", "mathlib",
]

# Frozen tree_audit vector: the full argparse flag face of
# tools/tree_audit.py in argparse declaration order (--root, --json,
# --selftest, main()); the tree_audit schema properties must match this
# list one-to-one, exactly the EXPECTED_VACGEN_ARGS discipline.
EXPECTED_TREE_AUDIT_ARGS = ["root", "json_out", "selftest"]

# Frozen axiom_sweep vector: the full argparse flag face of
# tools/lean_axiom_sweep.py (root, json, allow_axiom, selftest, timeout)
# in the registration contract's arg_map order; the axiom_sweep schema
# properties must match this list one-to-one, exactly the
# EXPECTED_TREE_AUDIT_ARGS discipline (the contract order differs from the
# argparse declaration order by the last two flags).
EXPECTED_AXIOM_SWEEP_ARGS = ["root", "json_out", "allow_axiom", "selftest",
                             "timeout"]

# Frozen claim_watch vector: the full argparse flag face of
# tools/claim_watch.py (config, round_label, ledger, actor,
# offline_selftest) in the registration contract's arg_map order; the
# claim_watch schema properties must match this list one-to-one, exactly
# the EXPECTED_AXIOM_SWEEP_ARGS discipline.
EXPECTED_CLAIM_WATCH_ARGS = ["config", "round_label", "ledger", "actor",
                             "offline_selftest"]

# Frozen source_fetch vector: the full argparse flag face of
# tools/source_fetch.py (url, sha256, sha256_source, mirror, trap_sniff,
# out, timeout, retries, backoff_base) in argparse declaration order;
# the source_fetch schema properties must match this list one-to-one,
# exactly the EXPECTED_CLAIM_WATCH_ARGS discipline (the tool's --selftest
# route is pre-argparse, so it is not an argparse flag and stays out of
# the vector).
EXPECTED_SOURCE_FETCH_ARGS = [
    "url", "sha256", "sha256_source", "mirror", "trap_sniff", "out",
    "timeout", "retries", "backoff_base",
]

# Frozen sweep_verdict vector: the full argparse flag face of
# tools/sweep_verdict.py (lanes, expected_red, out) in argparse
# declaration order; the sweep_verdict schema properties must match this
# list one-to-one, exactly the EXPECTED_CLAIM_WATCH_ARGS discipline (the
# tool's --selftest route is pre-argparse, so it is not an argparse flag
# and stays out of the vector).
EXPECTED_SWEEP_VERDICT_ARGS = ["lanes", "expected_red", "out"]

# Frozen release_chain vector: the full argparse flag face of
# tools/release_chain.py (issue, release_title, assets, zenodo_metadata,
# confirm_publish, dry_run, repo, stage, release_id, deposit_id,
# timeout) in argparse declaration order; the release_chain schema
# properties must match this list one-to-one, exactly the
# EXPECTED_CLAIM_WATCH_ARGS discipline (the tool's --selftest route is
# pre-argparse, so it is not an argparse flag and stays out of the
# vector; deposit_id rides as a string, the CLI declares no int type).
EXPECTED_RELEASE_CHAIN_ARGS = [
    "issue", "release_title", "assets", "zenodo_metadata",
    "confirm_publish", "dry_run", "repo", "stage", "release_id",
    "deposit_id", "timeout",
]


def _child_env():
    """Child environment shared by every server invocation."""
    env = dict(os.environ)
    env["ROCQWASH_HOME"] = REPO
    env.pop("ROCQWASH_MCP_ALLOW_NET", None)  # probe 5 exercises default deny
    return env


def _session(requests):
    """Run one stdio session; requests are dicts or raw (malformed) strings."""
    env = _child_env()
    payload = "".join(
        (r if isinstance(r, str) else json.dumps(r)) + "\n" for r in requests
    )
    proc = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-B", SERVER],
        input=payload.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=REPO, env=env, timeout=120,
    )
    lines = []
    for raw in proc.stdout.decode("utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if raw:
            lines.append(json.loads(raw))
    return proc.returncode, lines, proc.stderr.decode("utf-8", errors="replace")


def _by_id(lines, msg_id):
    for line in lines:
        if line.get("id") == msg_id and ("result" in line or "error" in line):
            return line
    return None


def _result_text(line):
    try:
        return line["result"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return ""


def _make_ledgers(tmp):
    """Two synthetic ledgers in the W13 shape (chain_graph selftest shape)."""
    la = {"LibX": {"file": "LibX", "rc": 0, "red": ""},
          "B1": {"file": "B1", "rc": 1,
                 "red": "Error: Unable to locate library | LibX"}}
    lb = {"B2": {"file": "B2", "rc": 0, "red": ""},
          "D1": {"file": "D1", "rc": 1,
                 "red": "Error: Unable to locate library | LibX"}}
    fa = os.path.join(tmp, "ledgerA.json")
    fb = os.path.join(tmp, "ledgerB.json")
    with open(fa, "w", encoding="utf-8") as h:
        json.dump(la, h)
    with open(fb, "w", encoding="utf-8") as h:
        json.dump(lb, h)
    return fa, fb, os.path.join(tmp, "graph.json"), os.path.join(tmp, "top.md")


def main():
    fails = []
    tmp = tempfile.mkdtemp(prefix="t_mcp_face_")
    try:
        fa, fb, jf, mf = _make_ledgers(tmp)
        # synthetic offline fixtures for the v2-B audit-line probes: one
        # clean sweep_verdict lane (probe 4f) and one one-file release
        # assets dir (probe 9's dry-run plan inputs)
        lanes_dir = os.path.join(tmp, "lanes")
        os.mkdir(lanes_dir)
        with open(os.path.join(lanes_dir, "lane-1.tsv"), "w",
                  encoding="utf-8", newline="\n") as h:
            h.write("idx\tprobe\tstatus\tnote\n7\twitness\tok\tclean\n")
        sv_out = os.path.join(tmp, "sweep-verdict.json")
        rc_assets = os.path.join(tmp, "rc-assets")
        os.mkdir(rc_assets)
        with open(os.path.join(rc_assets, "receipt.md"), "wb") as h:
            h.write(b"# fixture receipt\n")
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "t_mcp_face"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "http_backoff", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
             "params": {"name": "norm_lint",
                        "arguments": {"selftest": True}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
             "params": {"name": "chain_graph",
                        "arguments": {"ledgers": [fa, fb],
                                      "json_out": jf, "md_out": mf}}},
            {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
             "params": {"name": "net_probe", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 7, "method": "resources/list"},
            {"jsonrpc": "2.0", "id": 8, "method": "tools/call",
             "params": {"name": "no_such_tool", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 9, "method": "tools/call",
             "params": {"name": "chain_graph",
                        "arguments": {"ledgers": [fa], "bogus": True}}},
            {"jsonrpc": "2.0", "id": 10, "method": "tools/call",
             "params": {"name": "chain_graph",
                        "arguments": {"ledgers": ["-x"]}}},
            {"jsonrpc": "2.0", "id": 11, "method": "tools/call",
             "params": {"name": "red_dispatch_report",
                        "arguments": {"preset": "auto"}}},
            {"jsonrpc": "2.0", "id": 12, "method": "tools/call",
             "params": {"name": "tree_audit",
                        "arguments": {"selftest": True}}},
            {"jsonrpc": "2.0", "id": 13, "method": "tools/call",
             "params": {"name": "axiom_sweep",
                        "arguments": {"selftest": True}}},
            {"jsonrpc": "2.0", "id": 14, "method": "tools/call",
             "params": {"name": "claim_watch", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 15, "method": "tools/call",
             "params": {"name": "sweep_verdict",
                        "arguments": {"lanes": lanes_dir,
                                      "out": sv_out}}},
            {"jsonrpc": "2.0", "id": 16, "method": "tools/call",
             "params": {"name": "source_fetch", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 17, "method": "tools/call",
             "params": {"name": "release_chain", "arguments": {}}},
            "this line is not json",
        ]
        rc, lines, err = _session(requests)

        # Probe 1: initialize
        init = _by_id(lines, 1)
        info = (init or {}).get("result", {}).get("serverInfo", {})
        if not init or "result" not in init:
            fails.append("probe1 initialize should return a result")
        elif info.get("name") != "rocqwash-mcp":
            fails.append("probe1 serverInfo.name should be rocqwash-mcp, "
                         "got %r" % (info.get("name"),))
        elif not init["result"].get("protocolVersion"):
            fails.append("probe1 protocolVersion echo missing")

        # Probe 2: the notification gets no response line
        responses = [l for l in lines if "id" in l or "error" in l]
        if any(l.get("id") is None and l.get("error", {}).get("code")
               not in (None, -32700) for l in lines):
            fails.append("probe2 unexpected response for the notification")
        for l in lines:
            if l.get("method") == "notifications/initialized":
                fails.append("probe2 notification echoed back")

        # Probe 3: tools/list carries exactly the expected names in
        # registration order (the count is the EXPECTED_TOOLS data, never a
        # frozen literal)
        listing = _by_id(lines, 2)
        tools = (listing or {}).get("result", {}).get("tools", [])
        names = [t.get("name") for t in tools]
        if names != EXPECTED_TOOLS:
            fails.append("probe3 tools/list face drift\nexpected=%r\nactual=%r"
                         % (EXPECTED_TOOLS, names))
        for t in tools:
            if not t.get("description"):
                fails.append("probe3 %s missing description" % t.get("name"))
            schema = t.get("inputSchema")
            if not isinstance(schema, dict) or schema.get("type") != "object" \
                    or schema.get("additionalProperties") is not False:
                fails.append("probe3 %s inputSchema not a closed object"
                             % t.get("name"))

        # Probe 3b: micro-ticket schema-face vectors (schema-only).
        by_name = {t.get("name"): t for t in tools}
        exp_spec = by_name.get("exp_append") or {}
        exp_schema = exp_spec.get("inputSchema") or {}
        exp_props = exp_schema.get("properties") or {}
        if exp_props.get("actor", {}).get("type") != "string":
            fails.append("probe3b exp_append actor should be a first-class "
                         "string property (mu-1)")
        if "actor" in (exp_schema.get("required") or []):
            fails.append("probe3b exp_append actor must stay optional "
                         "(empty default, mu-1)")
        vac_props = list((by_name.get("vacgen_generate") or {})
                         .get("inputSchema", {}).get("properties") or {})
        if vac_props != EXPECTED_VACGEN_ARGS:
            fails.append("probe3b vacgen_generate schema flags must match the "
                         "argparse face one-to-one (mu-3)\nexpected=%r\nactual=%r"
                         % (EXPECTED_VACGEN_ARGS, vac_props))
        re_spec = by_name.get("render_events") or {}
        re_events_desc = ((re_spec.get("inputSchema") or {})
                          .get("properties", {}).get("events", {})
                          .get("description", ""))
        if "rocqwash-sentinel-event/1" not in re_events_desc \
                or "rocqwash-exp/1" not in re_events_desc:
            fails.append("probe3b render_events events description should "
                         "declare both accepted shapes, sentinel-event/1 "
                         "and exp/1 (mu-4)")
        if "rocqwash-sentinel-event/1" not in re_spec.get("description", "") \
                or "rocqwash-exp/1" not in re_spec.get("description", ""):
            fails.append("probe3b render_events spec description should "
                         "declare both accepted shapes, sentinel-event/1 "
                         "and exp/1 (mu-4)")

        # Probe 3c: tree_audit schema-face vectors (schema shape mirrors the
        # tool's real argparse flag face one-to-one; the spec description
        # declares the basis annotations and the top-level scan_face field).
        ta_spec = by_name.get("tree_audit") or {}
        ta_props = list((ta_spec.get("inputSchema") or {})
                        .get("properties") or {})
        if ta_props != EXPECTED_TREE_AUDIT_ARGS:
            fails.append("probe3c tree_audit schema flags must match the "
                         "argparse face one-to-one\nexpected=%r\nactual=%r"
                         % (EXPECTED_TREE_AUDIT_ARGS, ta_props))
        if "root" in ((ta_spec.get("inputSchema") or {}).get("required")
                      or []):
            fails.append("probe3c tree_audit root must stay optional (the "
                         "tool usage-errors rc 2 without --root; --selftest "
                         "runs without it)")
        ta_desc = ta_spec.get("description") or ""
        if "basis" not in ta_desc or "scan_face" not in ta_desc:
            fails.append("probe3c tree_audit description should declare the "
                         "per-field {value, basis} annotations and the "
                         "top-level scan_face field")

        # Probe 3d: axiom_sweep schema-face vectors (schema shape mirrors
        # the tool's real argparse flag face one-to-one; the spec
        # description declares the five-class classifier face and the
        # rc-112 toolchain gate).
        as_spec = by_name.get("axiom_sweep") or {}
        as_props = list((as_spec.get("inputSchema") or {})
                        .get("properties") or {})
        if as_props != EXPECTED_AXIOM_SWEEP_ARGS:
            fails.append("probe3d axiom_sweep schema flags must match the "
                         "argparse face one-to-one\nexpected=%r\nactual=%r"
                         % (EXPECTED_AXIOM_SWEEP_ARGS, as_props))
        if "root" in ((as_spec.get("inputSchema") or {}).get("required")
                      or []):
            fails.append("probe3d axiom_sweep root must stay optional (the "
                         "tool usage-errors rc 2 without --root; --selftest "
                         "runs without it)")
        as_desc = as_spec.get("description") or ""
        for token in ("BENIGN-STANDARD", "SORRY-ALARM", "CUSTOM-AXIOM-ALARM",
                      "UNPARSED", "112"):
            if token not in as_desc:
                fails.append("probe3d axiom_sweep description should name "
                             "the classification face token %s" % token)

        # Probe 3e: claim_watch schema-face vectors (schema shape mirrors
        # the tool's real argparse flag face one-to-one; the spec
        # description declares the default-deny net gate and the
        # offline-selftest face, the ticket 13 registration increment).
        cw_spec = by_name.get("claim_watch") or {}
        cw_props = list((cw_spec.get("inputSchema") or {})
                        .get("properties") or {})
        if cw_props != EXPECTED_CLAIM_WATCH_ARGS:
            fails.append("probe3e claim_watch schema flags must match the "
                         "argparse face one-to-one\nexpected=%r\nactual=%r"
                         % (EXPECTED_CLAIM_WATCH_ARGS, cw_props))
        if "config" in ((cw_spec.get("inputSchema") or {}).get("required")
                        or []):
            fails.append("probe3e claim_watch config must stay optional "
                         "(the live face usage-errors rc 9 without it; "
                         "--offline-selftest runs without it)")
        cw_desc = cw_spec.get("description") or ""
        for token in ("ROCQWASH_MCP_ALLOW_NET", "offline", "append-only",
                      "verbatim", "unverifiable"):
            if token not in cw_desc:
                fails.append("probe3e claim_watch description should name "
                             "the contract token %s" % token)

        # Probe 3f: the v2-B audit-line schema-face vectors (each schema
        # shape mirrors its tool's real argparse flag face one-to-one;
        # the release_chain schema carries dry_run default true and the
        # confirm_publish description warning that it is the publish
        # stop-gate key; stage pins its four gated layers in the enum).
        sf_spec = by_name.get("source_fetch") or {}
        sf_props = list((sf_spec.get("inputSchema") or {})
                        .get("properties") or {})
        if sf_props != EXPECTED_SOURCE_FETCH_ARGS:
            fails.append("probe3f source_fetch schema flags must match the "
                         "argparse face one-to-one\nexpected=%r\nactual=%r"
                         % (EXPECTED_SOURCE_FETCH_ARGS, sf_props))
        sv_spec = by_name.get("sweep_verdict") or {}
        sv_props = list((sv_spec.get("inputSchema") or {})
                        .get("properties") or {})
        if sv_props != EXPECTED_SWEEP_VERDICT_ARGS:
            fails.append("probe3f sweep_verdict schema flags must match the "
                         "argparse face one-to-one\nexpected=%r\nactual=%r"
                         % (EXPECTED_SWEEP_VERDICT_ARGS, sv_props))
        rc_spec = by_name.get("release_chain") or {}
        rc_schema = rc_spec.get("inputSchema") or {}
        rc_props = list(rc_schema.get("properties") or {})
        if rc_props != EXPECTED_RELEASE_CHAIN_ARGS:
            fails.append("probe3f release_chain schema flags must match the "
                         "argparse face one-to-one\nexpected=%r\nactual=%r"
                         % (EXPECTED_RELEASE_CHAIN_ARGS, rc_props))
        rc_dry = (rc_schema.get("properties") or {}).get("dry_run") or {}
        if rc_dry.get("default") is not True:
            fails.append("probe3f release_chain dry_run should carry the "
                         "schema default true (the default face is the "
                         "offline dry-run plan)")
        rc_cpd = ((rc_schema.get("properties") or {})
                  .get("confirm_publish") or {}).get("description", "")
        if "STOP-GATE" not in rc_cpd:
            fails.append("probe3f release_chain confirm_publish description "
                         "should warn that it is the publish stop-gate key")
        rc_stage = (rc_schema.get("properties") or {}).get("stage") or {}
        if rc_stage.get("enum") != [1, 2, 3, 4]:
            fails.append("probe3f release_chain stage should pin the four "
                         "gated layers in the schema enum")

        # Probe 4a: http_backoff live call
        r3 = _by_id(lines, 3)
        text3 = _result_text(r3)
        if not r3 or r3.get("result", {}).get("isError"):
            fails.append("probe4a http_backoff should not be an error\n%s"
                         % text3)
        elif "exit code: 0" not in text3 or "SELFTEST PASS" not in text3:
            fails.append("probe4a http_backoff exit 0 + pass face missing\n%s"
                         % text3)

        # Probe 4b: norm_lint selftest live call
        r4 = _by_id(lines, 4)
        text4 = _result_text(r4)
        if not r4 or r4.get("result", {}).get("isError"):
            fails.append("probe4b norm_lint selftest should not be an error\n%s"
                         % text4)
        elif "exit code: 0" not in text4 or "PASS english-clean" not in text4:
            fails.append("probe4b norm_lint exit 0 + english-clean face "
                         "missing\n%s" % text4)

        # Probe 4c: chain_graph two-ledger merge (array positional path)
        r5 = _by_id(lines, 5)
        text5 = _result_text(r5)
        if not r5 or r5.get("result", {}).get("isError"):
            fails.append("probe4c chain_graph merge should not be an error\n%s"
                         % text5)
        elif "exit code: 0" not in text5:
            fails.append("probe4c chain_graph exit 0 missing\n%s" % text5)
        else:
            with open(mf, "r", encoding="utf-8") as h:
                md = h.read()
            if "LibX" not in md:
                fails.append("probe4c chain root LibX missing from md face")

        # Probe 4d: tree_audit selftest live call (fixture vectors on
        # temporary directories, zero network, zero repository writes)
        r12 = _by_id(lines, 12)
        text12 = _result_text(r12)
        if not r12 or r12.get("result", {}).get("isError"):
            fails.append("probe4d tree_audit selftest should not be an "
                         "error\n%s" % text12)
        elif "exit code: 0" not in text12 or "tree_audit green" not in text12:
            fails.append("probe4d tree_audit exit 0 + fixture-vector green "
                         "face missing\n%s" % text12)

        # Probe 4e: axiom_sweep selftest live call (canned fixture vectors,
        # zero network, zero toolchain launch, zero repository writes)
        r13 = _by_id(lines, 13)
        text13 = _result_text(r13)
        if not r13 or r13.get("result", {}).get("isError"):
            fails.append("probe4e axiom_sweep selftest should not be an "
                         "error\n%s" % text13)
        elif "exit code: 0" not in text13 \
                or "lean_axiom_sweep green" not in text13:
            fails.append("probe4e axiom_sweep exit 0 + fixture-vector green "
                         "face missing\n%s" % text13)

        # Probe 4f: sweep_verdict live call on one synthetic clean lane
        # (the v2-B audit-line judge's offline face; zero network, the
        # only write is the caller-named tmp out path)
        r15 = _by_id(lines, 15)
        text15 = _result_text(r15)
        if not r15 or r15.get("result", {}).get("isError"):
            fails.append("probe4f sweep_verdict clean lane should not be "
                         "an error\n%s" % text15)
        elif "exit code: 0" not in text15 \
                or "rocqwash-sweep-verdict/1" not in text15 \
                or '"verdict_exception": {"value": 0' not in text15:
            fails.append("probe4f sweep_verdict exit 0 + GREEN verdict "
                         "face missing\n%s" % text15)
        else:
            with open(sv_out, "r", encoding="utf-8") as h:
                sv_json = h.read()
            if "rocqwash-sweep-verdict/1" not in sv_json:
                fails.append("probe4f sweep_verdict out face missing the "
                             "report schema token")

        # Probe 5: default deny negative sample
        r6 = _by_id(lines, 6)
        text6 = _result_text(r6)
        if not r6 or not r6.get("result", {}).get("isError"):
            fails.append("probe5 net_probe should be denied by default\n%s"
                         % text6)
        elif "ROCQWASH_MCP_ALLOW_NET" not in text6:
            fails.append("probe5 denial should name ROCQWASH_MCP_ALLOW_NET\n%s"
                         % text6)

        # Probe 5b: the claim_watch registration increment is net-gated
        # too (the same default-deny face; the offline selftest face is
        # its only ungated face and is exercised under the gate in
        # probe 8)
        r14 = _by_id(lines, 14)
        text14 = _result_text(r14)
        if not r14 or not r14.get("result", {}).get("isError"):
            fails.append("probe5b claim_watch should be denied by "
                         "default\n%s" % text14)
        elif "ROCQWASH_MCP_ALLOW_NET" not in text14:
            fails.append("probe5b denial should name ROCQWASH_MCP_ALLOW_NET"
                         "\n%s" % text14)

        # Probe 5c/5d: the two net-gated v2-B audit-line faces carry the
        # same default-deny face (the live faces are the network faces;
        # source_fetch's only other face is its pre-argparse --selftest
        # route, not exposed over the wire, and release_chain's offline
        # dry-run face is exercised under the gate in probe 9)
        r16 = _by_id(lines, 16)
        text16 = _result_text(r16)
        if not r16 or not r16.get("result", {}).get("isError"):
            fails.append("probe5c source_fetch should be denied by "
                         "default\n%s" % text16)
        elif "ROCQWASH_MCP_ALLOW_NET" not in text16:
            fails.append("probe5c denial should name ROCQWASH_MCP_ALLOW_NET"
                         "\n%s" % text16)
        r17 = _by_id(lines, 17)
        text17 = _result_text(r17)
        if not r17 or not r17.get("result", {}).get("isError"):
            fails.append("probe5d release_chain should be denied by "
                         "default\n%s" % text17)
        elif "ROCQWASH_MCP_ALLOW_NET" not in text17:
            fails.append("probe5d denial should name ROCQWASH_MCP_ALLOW_NET"
                         "\n%s" % text17)

        # Probe 6: error faces
        r7 = _by_id(lines, 7)
        if not r7 or r7.get("error", {}).get("code") != -32601:
            fails.append("probe6a resources/list should be -32601")
        r8 = _by_id(lines, 8)
        if not r8 or r8.get("error", {}).get("code") != -32602:
            fails.append("probe6b unknown tool should be -32602")
        r9 = _by_id(lines, 9)
        if not r9 or r9.get("error", {}).get("code") != -32602:
            fails.append("probe6c unknown argument should be -32602")
        r10 = _by_id(lines, 10)
        if not r10 or r10.get("error", {}).get("code") != -32602:
            fails.append("probe6d array item starting with '-' should be "
                         "-32602")
        r11 = _by_id(lines, 11)
        if not r11 or r11.get("error", {}).get("code") != -32602:
            fails.append("probe6f a withheld enum choice (the red_dispatch "
                         "auto preset) should be refused at the guard "
                         "-32602, never forwarded to the CLI")
        parse_errors = [l for l in lines
                        if l.get("error", {}).get("code") == -32700]
        if len(parse_errors) != 1 or parse_errors[0].get("id") is not None:
            fails.append("probe6e malformed line should be exactly one "
                         "-32700 with id null")

        if rc != 0:
            fails.append("server process should exit 0 on stdin EOF, got %d"
                         % rc)
        if err and "Traceback" in err:
            fails.append("server stderr carries a traceback\n%s" % err[-500:])

        # Probe 7: --help gate (separate invocation, same child shape)
        help_run = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", "-B", SERVER, "--help"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=REPO, env=_child_env(), timeout=120,
        )
        help_out = help_run.stdout.decode("utf-8", errors="replace")
        if help_run.returncode != 0:
            fails.append("probe7 --help should exit 0, got %d\n%s"
                         % (help_run.returncode, help_out))
        elif "usage" not in help_out or "mcp_server.py" not in help_out:
            fails.append("probe7 --help output should carry the argparse "
                         "usage face (usage anchor word plus prog name)\n%s"
                         % help_out)

        # Probe 8: claim_watch offline-selftest face under the gate (the
        # registration increment's face vector, the offline-selftest face
        # only): a separate allow-net session, one call, canned fixtures,
        # zero network; no live watch face is exercised by this suite.
        gated_env = _child_env()
        gated_env["ROCQWASH_MCP_ALLOW_NET"] = "1"
        gated_requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "t_mcp_face"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
             "params": {"name": "claim_watch",
                        "arguments": {"offline_selftest": True}}},
        ]
        payload = "".join(
            (r if isinstance(r, str) else json.dumps(r)) + "\n"
            for r in gated_requests
        )
        gated_run = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", "-B", SERVER],
            input=payload.encode("utf-8"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=REPO, env=gated_env, timeout=120,
        )
        gated_lines = []
        for raw in gated_run.stdout.decode("utf-8", errors="replace") \
                .splitlines():
            raw = raw.strip()
            if raw:
                gated_lines.append(json.loads(raw))
        g2 = _by_id(gated_lines, 2)
        g2_text = _result_text(g2)
        if not g2 or g2.get("result", {}).get("isError"):
            fails.append("probe8 claim_watch offline_selftest should not "
                         "be an error\n%s" % g2_text)
        elif "exit code: 0" not in g2_text \
                or "CLAIM-WATCH-SELFTEST PASS" not in g2_text:
            fails.append("probe8 claim_watch exit 0 + offline-selftest "
                         "pass face missing\n%s" % g2_text)

        # Probe 9: release_chain offline dry-run face under the gate (the
        # v2-B audit-line registration increment's face vector, the
        # offline face only): a separate allow-net session, one call
        # without confirm_publish on temporary fixtures, the dry_run
        # schema default true keeps the face at the plan (zero network,
        # "zero calls sent"); no publish face is exercised by this suite.
        rc_requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "t_mcp_face"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
             "params": {"name": "release_chain",
                        "arguments": {"issue": 7,
                                      "release_title": "Fixture Release",
                                      "assets": rc_assets}}},
        ]
        rc_payload = "".join(
            (r if isinstance(r, str) else json.dumps(r)) + "\n"
            for r in rc_requests
        )
        rc_run = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", "-B", SERVER],
            input=rc_payload.encode("utf-8"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=REPO, env=gated_env, timeout=120,
        )
        rc_lines = []
        for raw in rc_run.stdout.decode("utf-8", errors="replace") \
                .splitlines():
            raw = raw.strip()
            if raw:
                rc_lines.append(json.loads(raw))
        p2 = _by_id(rc_lines, 2)
        p2_text = _result_text(p2)
        if not p2 or p2.get("result", {}).get("isError"):
            fails.append("probe9 release_chain dry-run should not be an "
                         "error\n%s" % p2_text)
        elif "exit code: 0" not in p2_text \
                or "rocqwash-release-chain/1" not in p2_text \
                or "zero calls sent" not in p2_text:
            fails.append("probe9 release_chain exit 0 + offline dry-run "
                         "plan face missing\n%s" % p2_text)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for line in fails:
            sys.stderr.write("T_MCP_FACE FAIL %s\n" % line)
        return 1
    sys.stdout.write("T-MCP-FACE SUITE SHELL PASS (9 probe groups, "
                     "%d capabilities, 8 live-call spot checks)\n"
                     % len(EXPECTED_TOOLS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
