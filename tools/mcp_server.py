"""rocqwash MCP stdio server.

Mission:
    Expose the rocqwash tool capability surface over the Model Context
    Protocol (MCP) stdio transport. Capability true names and call forms
    follow the entry lines of docs/CAPABILITY-INDEX.md, the single tool
    capability contract surface of this repository. Landing note: RQW08
    (2026-11-14); the protocol and security face is documented in
    docs/mcp.md. Expansion note: RQW13 batch 1 (2026-11-14) appends
    thirteen zero-network capability specs in the expansion ticket order,
    each transcribed from its docs/CAPABILITY-INDEX.md entry line; the
    network-or-heavy candidates stay unregistered awaiting batch 2 (the
    batch-2 register in docs/mcp.md section 3). Engine-body batch note:
    the engine-body ticket appends three further zero-network
    capability specs graduated from docs/drafts/mcp-tool-specs-engine-body.md
    (tools/list carries 24 tools); the i18n http provider leg stays
    default-deny and unregistered. Symbiosis batch note: the symbiosis
    ticket's spec (section 1.1, named in docs/symbiosis_sop.md) appends one
    read-only file capability, symbiosis_status over docs/symbiosis_sop.md,
    on the capability_index wiring (tools/list carries 25 tools).

Protocol:
    Newline-delimited JSON-RPC 2.0 over stdin and stdout, hand written on
    the Python standard library. Served methods: initialize, tools/list,
    tools/call. Notifications carry no id and get no response. Each response
    is one compact JSON line on stdout; diagnostics go to stderr only. The
    process exits 0 when stdin reaches end of file.

Dependencies:
    Standard library only: json, os, subprocess, sys. No third-party
    package, no MCP SDK, no transport import (zero-dependency law).

Security face:
    1. Default deny for network and heavy capabilities. net_probe,
       ci_triage, pushci_status and sentinel_status return a failed tool
       result naming ROCQWASH_MCP_ALLOW_NET=1 as the explicit opt-in until
       that environment variable is set to 1. sentinel_status is gated
       beyond the three the landing ticket names because
       tools/cw_sentinel.py carries a non-zero network face in
       CAPABILITY-INDEX (registration note in docs/mcp.md section 5).
    2. Credential zero contact: this server reads no credential store, no
       token file, no netrc path, and exposes no credential-shaped
       argument; child environments pass through unchanged and credential
       handling stays with the underlying command line tools.
    3. Child stdout and stderr are captured and never merged into the
       protocol stream. Every tool call runs under a hard timeout
       (ROCQWASH_MCP_TIMEOUT seconds, default 300); a timed-out child is
       killed and reported as a failed tool result.

Build:
    python -I mcp_server.py
    Tool calls additionally require ROCQWASH_HOME to point at the rocqwash
    repository root; see docs/mcp.md for the full face.
"""

import json
import os
import subprocess
import sys

PROTOCOL_VERSION_DEFAULT = "2024-11-05"
SERVER_NAME = "rocqwash-mcp"
SERVER_VERSION = "0.1.0"
DEFAULT_TIMEOUT_S = 300
ALLOW_NET_ENV = "ROCQWASH_MCP_ALLOW_NET"
TIMEOUT_ENV = "ROCQWASH_MCP_TIMEOUT"
HOME_ENV = "ROCQWASH_HOME"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class InvalidParams(Exception):
    """Raised when tools/call parameters fail validation."""


def _object_schema(properties, required=()):
    """Build an inputSchema: an object with a closed property set."""
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


TOOL_SPECS = [
    {
        "name": "sentinel_status",
        "kind": "cli",
        "cli": os.path.join("tools", "cw_sentinel.py"),
        "net_gated": True,
        "fixed_args": ["--once"],
        "arg_map": (
            ("watch_repo", "--watch-repo"),
            ("branch", "--branch"),
            ("state_file", "--state-file"),
            ("timeout", "--timeout"),
            ("sleep_scale", "--sleep-scale"),
        ),
        "schema": _object_schema(
            {
                "watch_repo": {"type": "string", "description": "repository path to watch; CLI flag --watch-repo"},
                "branch": {"type": "string", "description": "branch to watch; CLI flag --branch"},
                "state_file": {"type": "string", "description": "sentinel state file path; CLI flag --state-file"},
                "timeout": {"type": "number", "description": "per step timeout in seconds; CLI flag --timeout"},
                "sleep_scale": {"type": "number", "description": "sleep scale factor; CLI flag --sleep-scale"},
            }
        ),
        "description": (
            "Run one watch round of the resident sentinel over a repo, ledgers and the "
            "build log (tools/cw_sentinel.py --once, event stream output). Default deny: "
            "the tool carries a non-zero network face in CAPABILITY-INDEX; requires "
            "ROCQWASH_MCP_ALLOW_NET=1."
        ),
    },
    {
        "name": "net_probe",
        "kind": "cli",
        "cli": os.path.join("tools", "net_probe.py"),
        "net_gated": True,
        "fixed_args": [],
        "arg_map": (
            ("endpoints", "--endpoints"),
            ("rounds", "--rounds"),
            ("interval", "--interval"),
            ("stable_window", "--stable-window"),
            ("seed", "--seed"),
        ),
        "schema": _object_schema(
            {
                "endpoints": {"type": "string", "description": "comma separated endpoint list; CLI flag --endpoints"},
                "rounds": {"type": "integer", "description": "number of probe rounds; CLI flag --rounds"},
                "interval": {"type": "number", "description": "seconds between rounds; CLI flag --interval"},
                "stable_window": {
                    "type": "integer",
                    "description": "consecutive all-pass rounds for a stable window; CLI flag --stable-window",
                },
                "seed": {"type": "integer", "description": "jitter seed; CLI flag --seed"},
            }
        ),
        "description": (
            "Probe bare GET reachability over endpoints for N rounds with a two round "
            "stable window rule (tools/net_probe.py). Default deny: network probing is "
            "the tool's own subject; requires ROCQWASH_MCP_ALLOW_NET=1."
        ),
    },
    {
        "name": "baselinediff",
        "kind": "cli",
        "cli": os.path.join("tools", "baseline_diff.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("old", "@0"),
            ("new", "@1"),
            ("json_out", "--json"),
            ("md_out", "--md"),
        ),
        "schema": _object_schema(
            {
                "old": {"type": "string", "description": "path of the old baseline JSON file (positional OLD)"},
                "new": {"type": "string", "description": "path of the new baseline JSON file (positional NEW)"},
                "json_out": {"type": "string", "description": "write the JSON report to this path; CLI flag --json"},
                "md_out": {"type": "string", "description": "write the markdown report to this path; CLI flag --md"},
            },
            required=("old", "new"),
        ),
        "description": (
            "Compare two baseline JSON files and report additions and removals "
            "(tools/baseline_diff.py OLD NEW, JSON and markdown output). Zero network face."
        ),
    },
    {
        "name": "ci_triage",
        "kind": "cli",
        "cli": os.path.join("tools", "ci_triage.py"),
        "net_gated": True,
        "fixed_args": [],
        "arg_map": (
            ("repo", "--repo"),
            ("run", "--run"),
            ("logs", "--logs"),
            ("offline", "--offline"),
            ("timeout", "--timeout"),
            ("retry_max", "--retry-max"),
        ),
        "schema": _object_schema(
            {
                "repo": {"type": "string", "description": "repository slug for the CI query; CLI flag --repo"},
                "run": {"type": "integer", "description": "CI run number to triage; CLI flag --run"},
                "logs": {"type": "boolean", "description": "include fetched log dumps in the output; bare CLI flag --logs"},
                "offline": {"type": "string", "description": "path to a jobs JSON file to triage from local input instead of fetching (CLI --offline JOBS.json)"},
                "timeout": {"type": "number", "description": "network timeout in seconds; CLI flag --timeout"},
                "retry_max": {"type": "integer", "description": "maximum retries; CLI flag --retry-max"},
            }
        ),
        "description": (
            "Fetch and triage logs of failing CI runs and emit a verdict (tools/ci_triage.py). "
            "Default deny: requires ROCQWASH_MCP_ALLOW_NET=1; the gate is tool level, so "
            "--offline calls are gated here too."
        ),
    },
    {
        "name": "vacgen_generate",
        "kind": "cli",
        "cli": os.path.join("tools", "vacgen.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("input", "--in"),
            ("out", "--out"),
            ("toolchain", "--toolchain"),
            ("snapshot", "--snapshot"),
            ("audit_id", "--audit-id"),
            ("name", "--name"),
            ("worktree", "--worktree"),
            ("lake", "--lake"),
            ("core", "--core"),
            ("force", "--force"),
            ("preflight_all", "--preflight-all"),
        ),
        "schema": _object_schema(
            {
                "input": {"type": "string", "description": "input Lean source file; CLI flag --in"},
                "out": {"type": "string", "description": "output skeleton path; CLI flag --out"},
                "toolchain": {"type": "string", "description": "Lean toolchain pin; CLI flag --toolchain"},
                "snapshot": {"type": "string", "description": "toolchain snapshot; CLI flag --snapshot"},
                "audit_id": {"type": "string", "description": "audit identifier stamped into the skeleton; CLI flag --audit-id"},
                "name": {"type": "string", "description": "probe name; CLI flag --name"},
                "worktree": {"type": "string", "description": "Lean worktree path for the compile leg; CLI flag --worktree"},
                "lake": {"type": "string", "description": "lake executable for the compile leg; CLI flag --lake"},
                "core": {"type": "integer", "description": "core count for the compile leg; CLI flag --core"},
                "force": {"type": "boolean", "description": "overwrite an existing skeleton; CLI flag --force"},
                "preflight_all": {"type": "boolean", "description": "run the zero-compile coverage preflight; CLI flag --preflight-all"},
            }
        ),
        "description": (
            "Cast a Lean vacuity probe skeleton with the four layer shape recognition engine "
            "(tools/vacgen.py, zero-compile casting face). Zero network face. The compile "
            "verification leg needs a Lean toolchain and stays a design SKIP face when the "
            "toolchain is absent."
        ),
    },
    {
        "name": "exp_append",
        "kind": "cli",
        "cli": os.path.join("tools", "exp_port.py"),
        "net_gated": False,
        "fixed_args": ["append"],
        "arg_map": (
            ("tool", "--tool"),
            ("points", "--points"),
            ("evidence", "--evidence"),
            ("batch", "--batch"),
        ),
        "schema": _object_schema(
            {
                "tool": {"type": "string", "description": "tool name of the entry"},
                "points": {"type": "string", "description": "one-line takeaways of the entry"},
                "evidence": {"type": "string", "description": "evidence pointer of the entry"},
                "batch": {"type": "string", "description": "batch label of the entry"},
            },
            required=("tool", "points"),
        ),
        "description": (
            "Append one structured experience entry to the in-repo experience ledger "
            "(tools/exp_port.py append, schema rocqwash-exp/1, idempotent seen set: "
            "re-appending an already-seen entry returns the existing id and writes "
            "nothing). The returned text carries the entry id of the ledger line."
        ),
    },
    {
        "name": "pushci_status",
        "kind": "cli",
        "cli": os.path.join("tools", "pushci.py"),
        "net_gated": True,
        "fixed_args": [],
        "arg_map": (
            ("repo_path", "--repo-path"),
            ("branch", "--branch"),
            ("base_ref", "--base-ref"),
            ("dry_run", "--dry-run"),
            ("watch_interval", "--watch-interval"),
            ("watch_max_rounds", "--watch-max-rounds"),
            ("timeout", "--timeout"),
        ),
        "schema": _object_schema(
            {
                "repo_path": {"type": "string", "description": "local repository path to push; CLI flag --repo-path"},
                "branch": {"type": "string", "description": "branch to push and watch; CLI flag --branch"},
                "base_ref": {"type": "string", "description": "base ref for comparison; CLI flag --base-ref"},
                "dry_run": {"type": "boolean", "description": "plan without pushing; CLI flag --dry-run"},
                "watch_interval": {"type": "number", "description": "watch poll interval in seconds; CLI flag --watch-interval"},
                "watch_max_rounds": {"type": "integer", "description": "maximum watch rounds; CLI flag --watch-max-rounds"},
                "timeout": {"type": "number", "description": "network timeout in seconds; CLI flag --timeout"},
            }
        ),
        "description": (
            "One-shot push then CI orchestration: push, ls-remote confirmation, run watching, "
            "verdict reading and heal rounds (tools/pushci.py). Default deny: network and "
            "remote write face; requires ROCQWASH_MCP_ALLOW_NET=1."
        ),
    },
    {
        "name": "capability_index",
        "kind": "file",
        "path": os.path.join("docs", "CAPABILITY-INDEX.md"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (),
        "schema": _object_schema({}),
        "description": (
            "Return the full text of docs/CAPABILITY-INDEX.md, the single tool capability "
            "contract surface, resolved from ROCQWASH_HOME. Zero network face, no side effects."
        ),
    },
    # ---- RQW13 batch 1 (2026-11-14): thirteen zero-network capabilities,
    # appended in expansion-ticket order; each spec is transcribed from its
    # docs/CAPABILITY-INDEX.md section 2 entry line. baseline_diff was
    # already on this face as baselinediff (above) and is not re-registered.
    {
        "name": "chain_graph",
        "kind": "cli",
        "cli": os.path.join("tools", "chain_graph.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("ledgers", "@0"),
            ("json_out", "--json"),
            ("md_out", "--md"),
            ("top", "--top"),
        ),
        "schema": _object_schema(
            {
                "ledgers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "probe ledger JSON paths, merged into one chain-root graph (positional LEDGER.json list)",
                },
                "json_out": {"type": "string", "description": "write the rocqwash-chain-graph/1 JSON report to this path; CLI flag --json"},
                "md_out": {"type": "string", "description": "write the markdown report to this path; CLI flag --md"},
                "top": {"type": "integer", "description": "ranked-list length cap; CLI flag --top"},
            },
            required=("ledgers",),
        ),
        "description": (
            "Merge probe ledgers into a chain-root graph and a ranked list (tools/chain_graph.py, "
            "graph schema rocqwash-chain-graph/1; the ledgers array carries one LEDGER.json path "
            "per element). Zero network face. The CLI also dispatches a --selftest frozen-vector "
            "face before argparse; it is not part of the INDEX entry line and not exposed here."
        ),
    },
    {
        "name": "doc_lint",
        "kind": "cli",
        "cli": os.path.join("tools", "doc_lint.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("repo", "--repo"),
            ("json_out", "--json"),
            ("help_cap", "--help-cap"),
        ),
        "schema": _object_schema(
            {
                "repo": {"type": "string", "description": "audited repository root; CLI flag --repo (defaults to the repo holding the tool)"},
                "json_out": {"type": "string", "description": "write the rocqwash-doclint/1 report to this path; CLI flag --json"},
                "help_cap": {"type": "integer", "description": "check-3 real --help run cap; CLI flag --help-cap"},
            }
        ),
        "description": (
            "Docs-versus-implementation consistency three-check over a repository: the tool table "
            "(cw.sh four-place mutual inspection plus the tools/ generic-entry reconciliation), the "
            "count check (suite roster versus README count lines) and the flag check (doc-cited "
            "flags versus real --help output, capped) (tools/doc_lint.py, schema rocqwash-doclint/1). "
            "Zero network face; the flag check runs in-repo tools with --help only (read-only)."
        ),
    },
    {
        "name": "ledger_sync",
        "kind": "cli",
        "cli": os.path.join("tools", "ledger_sync.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("probe", "--probe"),
            ("ledger", "--ledger"),
            ("out", "--out"),
            ("report", "--report"),
            ("policy", "--policy"),
        ),
        "schema": _object_schema(
            {
                "probe": {"type": "string", "description": "probe ledger TSV path; CLI flag --probe"},
                "ledger": {"type": "string", "description": "status ledger TSV path; CLI flag --ledger"},
                "out": {"type": "string", "description": "merged TSV output path; CLI flag --out"},
                "report": {"type": "string", "description": "sync report output path; CLI flag --report"},
                "policy": {"type": "string", "description": "merge policy name; CLI flag --policy"},
            }
        ),
        "description": (
            "TSV merge synchronizer between the probe ledger and the status ledger, with the "
            "merge policy parameterized (tools/ledger_sync.py). Zero network face."
        ),
    },
    {
        "name": "netname_normalize",
        "kind": "cli",
        "cli": os.path.join("tools", "netname_normalize.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("dir", "--dir"),
            ("apply", "--apply"),
            ("map", "--map"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "dir": {"type": "string", "description": "world directory indexed by os.walk; CLI flag --dir"},
                "apply": {"type": "boolean", "description": "apply the renames instead of reporting only; bare CLI flag --apply"},
                "map": {"type": "string", "description": "write the rename mapping table to this TSV path; CLI flag --map"},
                "json_out": {"type": "string", "description": "write the audit JSON to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Normalize doubled .v.v file suffixes over a world directory; the mapping table can be "
            "emitted (--map) or applied (--apply, the write face) (tools/netname_normalize.py). "
            "Zero network face; --apply renames only inside the directory given by --dir."
        ),
    },
    {
        "name": "norm_lint",
        "kind": "cli",
        "cli": os.path.join("tools", "norm_lint.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("tree", "--tree"),
            ("file", "--file"),
            ("jargon_map", "--jargon-map"),
            ("cjk_threshold", "--cjk-threshold"),
            ("cjk_whitelist", "--cjk-whitelist"),
            ("json_out", "--json"),
            ("md_out", "--md"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "tree": {"type": "string", "description": "directory to lint (mutually exclusive with file); CLI flag --tree"},
                "file": {"type": "string", "description": "single file to lint (mutually exclusive with tree); CLI flag --file"},
                "jargon_map": {"type": "string", "description": "jargon mapping file path; CLI flag --jargon-map"},
                "cjk_threshold": {"type": "number", "description": "CJK ratio threshold; CLI flag --cjk-threshold"},
                "cjk_whitelist": {"type": "string", "description": "CJK whitelist file path; CLI flag --cjk-whitelist"},
                "json_out": {"type": "string", "description": "write the rocqwash-norm-lint/1 report to this path; CLI flag --json"},
                "md_out": {"type": "string", "description": "write the human-readable report to this path; CLI flag --md"},
                "selftest": {"type": "boolean", "description": "run the built-in frozen-vector selftest; bare CLI flag --selftest"},
            }
        ),
        "description": (
            "Annotation-face normalization lint in report-first form over one tree or one file, "
            "with the jargon map, CJK threshold and whitelist parameterized (tools/norm_lint.py, "
            "schema rocqwash-norm-lint/1). Zero network face; the built-in --selftest "
            "frozen-vector face is on the INDEX entry line and exposed here."
        ),
    },
    {
        "name": "render_events",
        "kind": "cli",
        "cli": os.path.join("tools", "render_events.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("events", "--events"),
            ("dir", "--dir"),
            ("md_out", "--md"),
            ("json_out", "--json"),
            ("top", "--top"),
        ),
        "schema": _object_schema(
            {
                "events": {"type": "string", "description": "event stream JSONL path; CLI flag --events"},
                "dir": {"type": "string", "description": "event directory alternative input; CLI flag --dir"},
                "md_out": {"type": "string", "description": "markdown ledger output path; CLI flag --md"},
                "json_out": {"type": "string", "description": "JSON report output path; CLI flag --json"},
                "top": {"type": "integer", "description": "ranked-list length cap; CLI flag --top"},
            }
        ),
        "description": (
            "Render a JSONL event stream into a markdown ledger (tools/render_events.py; input "
            "via --events or --dir, output via --md or --json). Zero network face."
        ),
    },
    {
        "name": "select_audit",
        "kind": "cli",
        "cli": os.path.join("tools", "select_audit.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("order", "--order"),
            ("select", "--select"),
            ("grep", "--grep"),
            ("requires", "--requires"),
            ("world", "--world"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "order": {"type": "string", "description": "certification tree order.txt full table (read-only); CLI flag --order"},
                "select": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "batch selection list paths, repeatable (one array element per --select occurrence)",
                },
                "grep": {"type": "string", "description": "single-name full-table grep name; CLI flag --grep"},
                "requires": {"type": "string", "description": "requires file (.v) to audit against; CLI flag --requires"},
                "world": {"type": "string", "description": "world directory for the closure face; CLI flag --world"},
                "json_out": {"type": "string", "description": "write the audit JSON to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Audit a batch selection against the tree order file by full-table grep (tools/"
            "select_audit.py; the select array carries one selection-list path per element and "
            "maps to repeated --select occurrences). Zero network face."
        ),
    },
    {
        "name": "registry_audit",
        "kind": "cli",
        "cli": os.path.join("tools", "registry_audit.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("order", "--order"),
            ("project", "--project"),
            ("git", "--git"),
            ("ref", "--ref"),
            ("git_path_order", "--git-path-order"),
            ("git_path_project", "--git-path-project"),
            ("live_src", "--live-src"),
            ("anchor_src", "--anchor-src"),
            ("fix_plan", "--fix-plan"),
            ("json_out", "--json"),
            ("md_out", "--md"),
        ),
        "schema": _object_schema(
            {
                "order": {"type": "string", "description": "order.txt path; CLI flag --order"},
                "project": {"type": "string", "description": "_CoqProject path; CLI flag --project"},
                "git": {"type": "string", "description": "repository to read the registry pair from; CLI flag --git"},
                "ref": {"type": "string", "description": "git ref to read; CLI flag --ref"},
                "git_path_order": {"type": "string", "description": "order.txt path inside the git tree; CLI flag --git-path-order"},
                "git_path_project": {"type": "string", "description": "_CoqProject path inside the git tree; CLI flag --git-path-project"},
                "live_src": {"type": "string", "description": "live source directory; CLI flag --live-src"},
                "anchor_src": {"type": "string", "description": "anchor source directory; CLI flag --anchor-src"},
                "fix_plan": {"type": "boolean", "description": "emit the deterministic fix plan; bare CLI flag --fix-plan"},
                "json_out": {"type": "string", "description": "write the audit JSON to this path; CLI flag --json"},
                "md_out": {"type": "string", "description": "write the markdown report to this path; CLI flag --md"},
            }
        ),
        "description": (
            "Read-only hygiene audit over the two registry files, emitting a deterministic fix "
            "plan with --fix-plan (tools/registry_audit.py, the producer side of the audit-fix "
            "pair). Zero network face; local git reads only. Aimed at serviced Coq books: on a "
            "repository whose tree carries no order.txt or _CoqProject the audit exits nonzero "
            "with its REGISTERED fail-loud face (measured; CAPABILITY-INDEX section 4.1)."
        ),
    },
    {
        "name": "registry_fix",
        "kind": "cli",
        "cli": os.path.join("tools", "registry_fix.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("audit_json", "--audit-json"),
            ("order", "--order"),
            ("project", "--project"),
            ("anchor_src", "--anchor-src"),
            ("apply", "--apply"),
            ("work_dir", "--work-dir"),
            ("audit_tool", "--audit-tool"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "audit_json": {"type": "string", "description": "fix-plan JSON produced by registry_audit; CLI flag --audit-json"},
                "order": {"type": "string", "description": "order.txt path; CLI flag --order"},
                "project": {"type": "string", "description": "_CoqProject path; CLI flag --project"},
                "anchor_src": {"type": "string", "description": "anchor source directory; CLI flag --anchor-src"},
                "apply": {"type": "boolean", "description": "write the plan instead of dry running; bare CLI flag --apply"},
                "work_dir": {"type": "string", "description": "scratch work directory; CLI flag --work-dir"},
                "audit_tool": {"type": "string", "description": "registry_audit path for the same-parameter re-audit; CLI flag --audit-tool"},
                "json_out": {"type": "string", "description": "write the execution JSON to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Apply the fix plan produced by registry_audit (tools/registry_fix.py, the executor "
            "side of the audit-fix pair; dry run by default, --apply writes under staged "
            "in-memory assertions with rollback). Zero network face. The opt-in --orphan-add face "
            "is not exposed here: it is absent from the INDEX entry line transcribed above."
        ),
    },
    {
        "name": "registry_regen",
        "kind": "cli",
        "cli": os.path.join("tools", "registry_regen.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("base_repo", "--base-repo"),
            ("base_ref", "--base-ref"),
            ("contrib_repo", "--contrib-repo"),
            ("contrib_ref", "--contrib-ref"),
            ("pieces", "--pieces"),
            ("anchor_src", "--anchor-src"),
            ("dep_source", "--dep-source"),
            ("seq", "--seq"),
            ("base_path_order", "--base-path-order"),
            ("base_path_project", "--base-path-project"),
            ("contrib_path_order", "--contrib-path-order"),
            ("contrib_path_project", "--contrib-path-project"),
            ("out", "--out"),
            ("apply", "--apply"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "base_repo": {"type": "string", "description": "base repository; CLI flag --base-repo"},
                "base_ref": {"type": "string", "description": "base ref; CLI flag --base-ref"},
                "contrib_repo": {"type": "string", "description": "contribution repository; CLI flag --contrib-repo"},
                "contrib_ref": {"type": "string", "description": "contribution ref; CLI flag --contrib-ref"},
                "pieces": {"type": "string", "description": "piece table, comma separated module names; CLI flag --pieces"},
                "anchor_src": {"type": "string", "description": "anchor source directory; CLI flag --anchor-src"},
                "dep_source": {"type": "string", "description": "dependency source selector; CLI flag --dep-source"},
                "seq": {"type": "integer", "description": "row sequence number; CLI flag --seq"},
                "base_path_order": {"type": "string", "description": "order.txt path in the base repo; CLI flag --base-path-order"},
                "base_path_project": {"type": "string", "description": "_CoqProject path in the base repo; CLI flag --base-path-project"},
                "contrib_path_order": {"type": "string", "description": "order.txt path in the contribution repo; CLI flag --contrib-path-order"},
                "contrib_path_project": {"type": "string", "description": "_CoqProject path in the contribution repo; CLI flag --contrib-path-project"},
                "out": {"type": "string", "description": "output directory for the apply face; CLI flag --out"},
                "apply": {"type": "boolean", "description": "write the regenerated rows (requires out); bare CLI flag --apply"},
                "json_out": {"type": "string", "description": "write the regeneration JSON to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Regenerate contribution registration rows onto the merge-target line (tools/"
            "registry_regen.py; base and contribution repos, refs, piece table and path table "
            "parameterized; dry run by default, --apply writes only under an explicit out). "
            "Zero network face; local git reads only."
        ),
    },
    {
        "name": "registry_union",
        "kind": "cli",
        "cli": os.path.join("tools", "registry_union.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("base", "--base"),
            ("main", "--main"),
            ("branch", "--branch"),
            ("git", "--git"),
            ("ref_base", "--ref-base"),
            ("ref_main", "--ref-main"),
            ("ref_branch", "--ref-branch"),
            ("git_path", "--git-path"),
            ("kind", "--kind"),
            ("reanchor", "--reanchor"),
            ("anchor_src", "--anchor-src"),
            ("out", "--out"),
            ("apply", "--apply"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "base": {"type": "string", "description": "base registry file; CLI flag --base"},
                "main": {"type": "string", "description": "main registry file; CLI flag --main"},
                "branch": {"type": "string", "description": "branch registry file; CLI flag --branch"},
                "git": {"type": "string", "description": "repository to read the registries from; CLI flag --git"},
                "ref_base": {"type": "string", "description": "ref for the base registry; CLI flag --ref-base"},
                "ref_main": {"type": "string", "description": "ref for the main registry; CLI flag --ref-main"},
                "ref_branch": {"type": "string", "description": "ref for the branch registry; CLI flag --ref-branch"},
                "git_path": {"type": "string", "description": "registry path inside the git tree; CLI flag --git-path"},
                "kind": {"type": "string", "description": "kind selection name; CLI flag --kind"},
                "reanchor": {"type": "string", "description": "re-anchor name list, comma separated; CLI flag --reanchor"},
                "anchor_src": {"type": "string", "description": "anchor source directory; CLI flag --anchor-src"},
                "out": {"type": "string", "description": "merged output file; CLI flag --out"},
                "apply": {"type": "boolean", "description": "write the merged file; bare CLI flag --apply"},
                "json_out": {"type": "string", "description": "write the union JSON to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Three-way union merger for the registry (tools/registry_union.py; base/main/branch "
            "inputs with re-anchoring and kind selection parameterized; dry run by default, "
            "--apply writes). Zero network face; local git reads only."
        ),
    },
    {
        "name": "abl1_4b_compile",
        "kind": "cli",
        "cli": os.path.join("tools", "_abl1_4b_compile.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("extract_dir", "@0"),
            ("driver", "@1"),
        ),
        "schema": _object_schema(
            {
                "extract_dir": {"type": "string", "description": "extracted module directory to compile (positional EXTRACT_DIR)"},
                "driver": {"type": "string", "description": "optional driver .ml to link and run (positional DRIVER.ML)"},
            },
            required=("extract_dir",),
        ),
        "description": (
            "Internal helper: incremental OCaml compilation of an extracted module directory in "
            "dependency fixpoint order, interface files first, optionally linking and running a "
            "driver (tools/_abl1_4b_compile.py, positional EXTRACT_DIR plus optional DRIVER.ML). "
            "Zero network face. Design SKIP face: the tool exits loudly when ocamlc/ocamldep are "
            "absent from PATH, so this capability needs an OCaml toolchain on the host."
        ),
    },
    {
        "name": "http_backoff",
        "kind": "cli",
        "cli": os.path.join("tools", "_http_backoff.py"),
        "net_gated": False,
        "fixed_args": ["--selftest"],
        "arg_map": (),
        "schema": _object_schema({}),
        "description": (
            "Internal shared helper: pure-function HTTP rate-limit backoff with a frozen-vector "
            "selftest, no transport and no IO (tools/_http_backoff.py). This capability exposes "
            "the --selftest face only; the helper's other face is module import by ci_triage, "
            "cw_sentinel and pushci. Zero network face."
        ),
    },
    # ---- engine-body batch (the engine-body ticket): three
    # zero-network capability specs graduated from the lane-8 draft
    # docs/drafts/mcp-tool-specs-engine-body.md; additive after the RQW13
    # batch-1 block (the 21 existing specs and schemas untouched); the
    # ticket's only network face (the i18n http provider leg) is not part
    # of this batch and stays unregistered.
    {
        "name": "ai_flavor_detect",
        "kind": "cli",
        "cli": os.path.join("tools", "ai_flavor.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("file", "--file"),
            ("tree", "--tree"),
            ("json_out", "--json"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "file": {"type": "string", "description": "target file to scan; CLI flag --file"},
                "tree": {"type": "string", "description": "target directory to scan (*.py *.sh *.md *.json *.ts); CLI flag --tree"},
                "json_out": {"type": "string", "description": "write the rocqwash.ai-flavor.report/1 report to this path; CLI flag --json"},
                "selftest": {"type": "boolean", "description": "run the clean and polluted probe pair; bare CLI flag --selftest"},
            }
        ),
        "description": (
            "Run the 36-face AI-flavor wording battery plus the em-dash battery over a file "
            "or a directory tree (tools/ai_flavor.py, schema rocqwash.ai-flavor.report/1). "
            "Zero network face, zero writes, report-first. Exit codes: 0 clean, 1 hits "
            "(findings are data, not errors), 2 usage."
        ),
    },
    {
        "name": "jargon_plan",
        "kind": "cli",
        "cli": os.path.join("tools", "jargon_apply.py"),
        "net_gated": False,
        "fixed_args": ["--plan"],
        "arg_map": (
            ("file", "--file"),
            ("tree", "--tree"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "file": {"type": "string", "description": "target file to plan; CLI flag --file"},
                "tree": {"type": "string", "description": "target directory to plan; CLI flag --tree"},
                "json_out": {"type": "string", "description": "write the zero-write plan report (before/after pairs) to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Plan jargon-to-standard rewrites over a file or a tree with zero writes "
            "(tools/jargon_apply.py --plan; before/after pairs from the 62-entry map "
            "seeds/jargon/jargon-map.json). Zero network face. The apply face is not "
            "exposed over MCP; callers carrying write duty use the CLI directly, where "
            "plan also stays the default."
        ),
    },
    {
        "name": "i18n_pipeline_dryrun",
        "kind": "cli",
        "cli": os.path.join("tools", "i18n_pipeline.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("manifest", "--manifest"),
            ("stage", "--stage"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "manifest": {"type": "string", "description": "run manifest path (i18n SPEC section 9 run manifest shape); CLI flag --manifest"},
                "stage": {"type": "string", "enum": ["p0", "p1"], "description": "dry-run stage: p0 policy pre-check (a refusal is a legal exit-0 outcome with its ledger row) or p1 segmentation with the protection list; p3/p6 are write-bearing and withheld from this face; CLI flag --stage"},
                "json_out": {"type": "string", "description": "write the stage report to this path; CLI flag --json"},
            },
            required=("manifest", "stage"),
        ),
        "description": (
            "Dry-run the analysis stages of the i18n pipeline over a run manifest "
            "(tools/i18n_pipeline.py --stage p0|p1): p0 policy pre-check and p1 "
            "segmentation with the protection list (segment ledger rows, i18n SPEC "
            "section 9 nine-key shape). Zero network face (the P2 model stage lives in "
            "tools/i18n_translate.py and is not part of this face). Write face: stage "
            "account rows go to the ledger path named by the manifest; the target face "
            "is never written at the exposed stages."
        ),
    },
    # ---- symbiosis batch (the symbiosis ticket, section 1.1): one
    # read-only capability registered on the capability_index wiring (a
    # file-kind spec; no subprocess, no gate); additive after the
    # engine-body block (the 24 existing specs and schemas untouched).
    {
        "name": "symbiosis_status",
        "kind": "file",
        "path": os.path.join("docs", "symbiosis_sop.md"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (),
        "schema": _object_schema({}),
        "description": (
            "Return the full text of docs/symbiosis_sop.md, the single "
            "symbiosis-bus contract surface, resolved from ROCQWASH_HOME. "
            "Read-only file face on the capability_index wiring: zero "
            "network face, no subprocess, no side effects."
        ),
    },
]

TOOLS_BY_NAME = {spec["name"]: spec for spec in TOOL_SPECS}

_TYPE_CHECKS = {
    "string": lambda value: isinstance(value, str),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "array": lambda value: isinstance(value, list)
    and all(isinstance(item, str) for item in value),
}


def _log(message):
    """Diagnostics go to stderr; stdout carries protocol lines only."""
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def _emit(payload):
    """Write one compact JSON-RPC line in UTF-8 and flush."""
    data = json.dumps(payload, ensure_ascii=False)
    sys.stdout.buffer.write((data + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def _result(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _tool_result(msg_id, text, is_error):
    return _result(
        msg_id,
        {"content": [{"type": "text", "text": text}], "isError": bool(is_error)},
    )


def _deny_text(name):
    return (
        "denied by default security face: capability '{0}' drives network or heavy "
        "tooling and is disabled unless the environment variable {1}=1 is set. "
        "See docs/mcp.md section 5 for the security face."
    ).format(name, ALLOW_NET_ENV)


def _timeout_s():
    raw = os.environ.get(TIMEOUT_ENV, "")
    if not raw:
        return DEFAULT_TIMEOUT_S
    try:
        value = int(raw)
    except ValueError:
        _log("invalid {0}={1!r}; using default {2}s".format(TIMEOUT_ENV, raw, DEFAULT_TIMEOUT_S))
        return DEFAULT_TIMEOUT_S
    return value if value > 0 else DEFAULT_TIMEOUT_S


def _validate_arguments(spec, arguments):
    if not isinstance(arguments, dict):
        raise InvalidParams("Invalid params: arguments must be an object")
    properties = spec["schema"]["properties"]
    for key, value in arguments.items():
        if key not in properties:
            raise InvalidParams("Invalid params: unknown argument '{0}'".format(key))
        expected = properties[key]["type"]
        if not _TYPE_CHECKS[expected](value):
            raise InvalidParams(
                "Invalid params: argument '{0}' must be of type {1}".format(key, expected)
            )
        if expected == "string" and value.startswith("-"):
            raise InvalidParams(
                "Invalid params: argument '{0}' must not start with '-'".format(key)
            )
        if expected == "array" and any(item.startswith("-") for item in value):
            raise InvalidParams(
                "Invalid params: array argument '{0}' must not contain "
                "items starting with '-'".format(key)
            )
    for key in spec["schema"]["required"]:
        if key not in arguments:
            raise InvalidParams("Invalid params: missing required argument '{0}'".format(key))


def _build_argv(spec, arguments, cli_path):
    """Map schema arguments onto the INDEX entry-line call form.

    Booleans: True appends the flag, False omits it. Values marked '@N' are
    positional. Arrays (RQW13 batch 1): for a positional target the items
    extend the argv in order (an argparse nargs="*" face); for a value flag
    the flag is repeated once per item (an argparse action="append" face).
    Everything else is a value flag passed as --flag value.
    """
    argv = [sys.executable, cli_path]
    argv.extend(spec["fixed_args"])
    for key, flag in spec["arg_map"]:
        if key not in arguments:
            continue
        value = arguments[key]
        if isinstance(value, bool):
            if value:
                argv.append(flag)
        elif isinstance(value, list):
            if flag.startswith("@"):
                argv.extend(str(item) for item in value)
            else:
                for item in value:
                    argv.extend([flag, str(item)])
        elif flag.startswith("@"):
            argv.append(str(value))
        else:
            argv.extend([flag, str(value)])
    return argv


def _run_cli(argv, cwd):
    """Run a tool CLI with captured streams and a hard timeout."""
    timeout_s = _timeout_s()
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "", "tool call timed out after {0}s; child process killed".format(timeout_s)
    except OSError as exc:
        return None, "", "tool call failed to start: {0}".format(exc)
    out = completed.stdout.decode("utf-8", "replace")
    err = completed.stderr.decode("utf-8", "replace")
    code = completed.returncode
    if code is None:
        return None, out, err
    return code, out, err


def _handle_initialize(msg_id, params):
    requested = ""
    if isinstance(params, dict):
        value = params.get("protocolVersion")
        if isinstance(value, str) and value:
            requested = value
    version = requested or PROTOCOL_VERSION_DEFAULT
    return _result(
        msg_id,
        {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        },
    )


def _tools_listing():
    return [
        {
            "name": spec["name"],
            "description": spec["description"],
            "inputSchema": spec["schema"],
        }
        for spec in TOOL_SPECS
    ]


def _handle_tools_call(msg_id, params):
    name = params.get("name")
    if not isinstance(name, str) or not name:
        raise InvalidParams("Invalid params: params.name must be a non-empty string")
    spec = TOOLS_BY_NAME.get(name)
    if spec is None:
        raise InvalidParams("Unknown tool: {0}".format(name))
    arguments = params.get("arguments")
    if arguments is None:
        arguments = {}
    if spec["net_gated"] and os.environ.get(ALLOW_NET_ENV) != "1":
        return _tool_result(msg_id, _deny_text(name), True)
    _validate_arguments(spec, arguments)
    home = os.environ.get(HOME_ENV, "")
    if not home:
        return _tool_result(
            msg_id,
            "capability '{0}' cannot run: environment variable {1} is not set; set it to "
            "the rocqwash repository root and restart the server (docs/mcp.md section 4).".format(name, HOME_ENV),
            True,
        )
    if spec["kind"] == "file":
        path = os.path.join(home, spec["path"])
        if not os.path.isfile(path):
            return _tool_result(
                msg_id,
                "capability '{0}': file not found: {1}".format(name, path),
                True,
            )
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError as exc:
            return _tool_result(
                msg_id,
                "capability '{0}': read failed: {1}".format(name, exc),
                True,
            )
        return _tool_result(msg_id, text, False)
    cli_path = os.path.join(home, spec["cli"])
    if not os.path.isfile(cli_path):
        return _tool_result(
            msg_id,
            "capability '{0}': underlying CLI not found: {1}. Registered ahead of its "
            "landing; see docs/mcp.md section 6.".format(name, cli_path),
            True,
        )
    argv = _build_argv(spec, arguments, cli_path)
    code, out, err = _run_cli(argv, home)
    if code is None:
        return _tool_result(msg_id, err or "tool call failed", True)
    chunks = []
    if out:
        chunks.append(out.rstrip("\r\n"))
    if err:
        chunks.append("[stderr] " + err.rstrip("\r\n"))
    text = "\n".join(chunks) if chunks else "(no output)"
    return _tool_result(msg_id, "exit code: {0}\n{1}".format(code, text), code != 0)


def _dispatch(message):
    if not isinstance(message, dict):
        return _error(None, INVALID_REQUEST, "Invalid Request: expected one JSON object per line")
    msg_id = message.get("id")
    if "id" not in message:
        # A notification gets no response under JSON-RPC 2.0 and MCP.
        _log("notification consumed without response: {0!r}".format(message.get("method")))
        return None
    method = message.get("method")
    if not isinstance(method, str):
        return _error(msg_id, INVALID_REQUEST, "Invalid Request: method must be a string")
    if method == "initialize":
        return _handle_initialize(msg_id, message.get("params"))
    if method == "tools/list":
        return _result(msg_id, {"tools": _tools_listing()})
    if method == "tools/call":
        params = message.get("params")
        if not isinstance(params, dict):
            return _error(msg_id, INVALID_PARAMS, "Invalid params: params must be an object")
        try:
            return _handle_tools_call(msg_id, params)
        except InvalidParams as exc:
            return _error(msg_id, INVALID_PARAMS, str(exc))
        except OSError as exc:
            return _error(msg_id, INTERNAL_ERROR, "Internal error: {0}".format(exc))
    return _error(msg_id, METHOD_NOT_FOUND, "Method not found: {0}".format(method))


def main():
    _log(
        "rocqwash MCP stdio server ready: methods initialize/tools/list/tools/call; "
        "allow-net={0}".format(os.environ.get(ALLOW_NET_ENV) == "1")
    )
    for raw in sys.stdin.buffer:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            _emit(_error(None, PARSE_ERROR, "Parse error: line is not valid UTF-8"))
            continue
        line = text.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            _emit(_error(None, PARSE_ERROR, "Parse error: line is not valid JSON"))
            continue
        try:
            response = _dispatch(message)
        except Exception as exc:  # fail loud on the wire, keep serving
            msg_id = message.get("id") if isinstance(message, dict) else None
            _log("internal error: {0!r}".format(exc))
            response = _error(msg_id, INTERNAL_ERROR, "Internal error: {0}".format(exc))
        if response is not None:
            _emit(response)
    return 0


if __name__ == "__main__":
    sys.exit(main())
