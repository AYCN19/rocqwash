"""rocqwash MCP stdio server.

Mission:
    Expose the rocqwash tool capability surface over the Model Context
    Protocol (MCP) stdio transport. Capability true names and call forms
    follow the entry lines of docs/CAPABILITY-INDEX.md, the single tool
    capability contract surface of this repository. Landing note: RQW08
    (2026-11-14); the protocol and security face is documented in
    docs/mcp.md.

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
            "(tools/exp_port.py append). Pending capability: the CLI lands with the "
            "experience-bus package; until then calls return an explicit not-found result."
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
]

TOOLS_BY_NAME = {spec["name"]: spec for spec in TOOL_SPECS}

_TYPE_CHECKS = {
    "string": lambda value: isinstance(value, str),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
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
    for key in spec["schema"]["required"]:
        if key not in arguments:
            raise InvalidParams("Invalid params: missing required argument '{0}'".format(key))


def _build_argv(spec, arguments, cli_path):
    """Map schema arguments onto the INDEX entry-line call form.

    Booleans: True appends the flag, False omits it. Values marked '@N' are
    positional. Everything else is a value flag passed as --flag value.
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
            return _tool_result(msg_id, "capability_index: file not found: {0}".format(path), True)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError as exc:
            return _tool_result(msg_id, "capability_index: read failed: {0}".format(exc), True)
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
