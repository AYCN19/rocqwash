#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_chain.py - the release chain face (issue -> GitHub Release ->
Zenodo) with separately gated publish steps (rocqwash tools/, v2-B).

Purpose.  Emit the three-layer plan (issue body update -> GitHub Release
  per-asset upload -> Zenodo deposit create + bucket PUTs + publish) as
  a checklist with exact API calls.  DEFAULT dry-run (zero network);
  actual steps need --confirm-publish, each layer stopping for
  verification before the next (publish stop-gates, never bundled).
  Minted URLs/DOIs are read verbatim from responses, never assembled.
Interface.  python -I tools/release_chain.py --issue <n> --release-title
  <t> --assets <dir> [--zenodo-metadata <json>] [--confirm-publish]
  [--dry-run] [--repo <owner/name>] [--stage <1|2|3|4>] [--release-id <n>]
  [--deposit-id <n>] | --selftest.  One JSON report line (schema
  rocqwash-release-chain/1); every counter wrapped {value, basis};
  top-level scan_face.  Stages: 1 issue body; 2 Release + uploads; 3
  deposit + bucket PUTs; 4 publish (irreversible; needs --deposit-id).
Dependencies.  Python 3 standard library plus the in-tree `_http_backoff`
  and `net_probe` (retry/backoff + transport classes) via explicit
  sys.path injection so `python -I` is clean; the network face is
  env-gated (ROCQWASH_MCP_ALLOW_NET=1); credentials pre-flight from
  GH_TOKEN/GITHUB_TOKEN and ZENODO_TOKEN/ZENODO_ACCESS_TOKEN.
Evidence.  --selftest drives offline plan-shape vectors (layer order,
  exact API calls, no-DOI-concatenation guard, asset pinning) plus
  injected-transport stage vectors (stop-gates, verbatim minted fields,
  publish interlock, honest gates, red 422); precedent zen_mint_wave1.py.
Exit-codes.  0 dry-run plan, or stage 4 complete (chain closed); 1 red
  data (non-2xx, transport failure, or drift; JSON carries the excerpt);
  2 usage; 3 stop-gate (next layer needs verification + re-invocation);
  9 missing path/credential/handle; 111 gated.
"""
# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard):
#   * One stage per invocation: --confirm-publish never runs two stages in
#     a row - the operator verifies each layer's result on the service side
#     and re-invokes with the next --stage.  Stage 4 additionally demands
#     --deposit-id, so the irreversible publish cannot run without carrying
#     stage 3's minted handle (the mechanical form of the stop-gate).
#   * Minted-value discipline: response fields are read through
#     mint_from()/mint_path(), which fail loud when a field is absent -
#     a missing field never degrades into a constructed URL or DOI string.
#     Request targets assembled from caller inputs or minted ids (repo
#     paths, /actions/publish) are request shapes, not minted values.
#   * Asset pin discipline: every asset's bytes and sha256 are recorded at
#     plan time; the upload re-reads the file, re-hashes, and refuses to
#     upload drifted bytes (rc=1, the drift registered).
#   * Retry discipline (NETRED): 403/429/5xx and the transient transport
#     faces dns/timeout retry per _http_backoff with a 2s base, 3 attempts;
#     4xx semantic faces (401/404/422) answer once and land rc=1 with the
#     response excerpt; no call is ever simulated.
#   * Dry-run needs no gate, no credentials, no network: it is a pure
#     computation over local inputs (assets dir + metadata file).

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
import _http_backoff  # noqa: E402  (retry face + exponential backoff)
import net_probe  # noqa: E402  (classify_unverifiable + reason constants)

PROG = "release_chain"
SCHEMA = "rocqwash-release-chain/1"
NET_GATE_ENV = "ROCQWASH_MCP_ALLOW_NET"
GATED_RC = 111
STOP_GATE_RC = 3
DEFAULT_TIMEOUT = 120
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_BASE = 2.0
EXCERPT_CAP = 400
GH_API = "https://api.github.com"
GH_UPLOAD = "https://uploads.github.com"
ZENODO_API = "https://zenodo.org/api"
USER_AGENT = "rocqwash-release-chain/1 (release face)"

STAGE_NAMES = {
    1: "issue-body-update",
    2: "github-release-upload",
    3: "zenodo-deposit-upload",
    4: "zenodo-publish",
}


class UsageError(Exception):
    """Bad invocation form (rc=2; fail loud)."""


class PreflightError(Exception):
    """Missing credential or minted handle before any call (rc=9)."""


class MintError(Exception):
    """A minted field was absent from a response - refused to assemble
    it (rc=1; the DOI-concatenation-error precedent)."""


def w(value, basis):
    """Wrap one field as {value, basis}: no bare counter leaves the tool."""
    return {"value": value, "basis": basis}


def gate_enabled(env=None):
    """env -> whether the live network face is unlocked (the gate variable
    equals "1"; absent or any other value keeps the face denied)."""
    env = os.environ if env is None else env
    return env.get(NET_GATE_ENV) == "1"


def read_cred(env, names):
    """env x candidate variable names -> the first non-empty value or
    None (the caller pre-flights and names the missing variable)."""
    env = os.environ if env is None else env
    for name in names:
        val = env.get(name)
        if val:
            return name, val
    return None, None


def slugify_tag(title):
    """Release title -> the deterministic tag slug (lowercase, runs of
    non-alphanumerics collapsed to one '-', trimmed).  Empty result = the
    caller's usage error (the title carries no taggable characters)."""
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    return slug


def scan_assets(assets_dir):
    """Flat, non-recursive listing of the assets dir -> ordered
    [{name, bytes, sha256}] (sorted by name; files only).  Raises
    PreflightError when the dir is missing."""
    if not os.path.isdir(assets_dir):
        raise PreflightError("--assets directory missing: %s" % assets_dir)
    names = sorted(fn for fn in os.listdir(assets_dir)
                   if os.path.isfile(os.path.join(assets_dir, fn)))
    assets = []
    for name in names:
        with open(os.path.join(assets_dir, name), "rb") as fh:
            data = fh.read()
        assets.append({"name": name, "bytes": len(data),
                       "sha256": hashlib.sha256(data).hexdigest()})
    return assets


def load_metadata(path):
    """Parse the --zenodo-metadata JSON file -> the dict payload verbatim.
    Raises UsageError on malformed JSON or a missing title key (the
    deposit create has no valid payload without it)."""
    if not os.path.isfile(path):
        raise PreflightError("--zenodo-metadata file missing: %s" % path)
    with io_open(path) as fh:
        text = fh.read()
    try:
        meta = json.loads(text)
    except ValueError as exc:
        raise UsageError("--zenodo-metadata is not valid JSON: %s (%s)"
                         % (path, exc))
    if not isinstance(meta, dict) or not meta.get("title"):
        raise UsageError("--zenodo-metadata must be a JSON object with a"
                         " 'title' key: %s" % path)
    return meta


def io_open(path):
    return open(path, "r", encoding="utf-8", errors="replace")


# ---- transport (injected send point behind the selftest) --------------------

def _default_send(method, url, data, headers, timeout):
    """One raw HTTP send via urllib -> (status, body_bytes).  HTTPError is
    an answer (its code and body return); transport failures raise (the
    caller classifies)."""
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        status = getattr(resp, "status", None)
        body = resp.read()
        close = getattr(resp, "close", None)
        if close:
            close()
        return status, body
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return exc.code, body


def api_call(method, url, token, payload=None, data=None, content_type=None,
             timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES,
             backoff_base=DEFAULT_BACKOFF_BASE, _send=None, _sleep=None):
    """One API call under the NETRED retry discipline -> {status, body,
    json, error, reason_class, attempts, statuses, backoff_applied}.
    Retry face = _http_backoff.is_retry_status (403/429/5xx) plus the
    transient transport faces dns/timeout; every 4xx semantic face answers
    once.  payload = JSON-serializable dict (sent as application/json);
    data = raw bytes (content_type names them)."""
    sender = _send if _send is not None else _default_send
    sleeper = _sleep if _sleep is not None else (lambda _s: None)
    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = "Bearer %s" % token
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        content_type = "application/json"
    if content_type:
        headers["Content-Type"] = content_type
    schedule = _http_backoff.backoff_delays(retries, base=backoff_base)
    attempts = 0
    statuses = []
    applied = []
    result = None
    for attempt in range(retries + 1):
        attempts += 1
        try:
            status, body = sender(method, url, data, headers, timeout)
            reason_class = None
            error = None
        except Exception as exc:  # noqa: BLE001 - classified, never swallowed
            status, body = None, b""
            error = "%s: %s" % (type(exc).__name__, exc)
            reason_class = net_probe.classify_unverifiable(exc)
        result = {"status": status, "body": body, "json": None,
                  "error": error, "reason_class": reason_class}
        marker = status if status is not None else (reason_class or "error")
        statuses.append(marker)
        if isinstance(body, bytes):
            try:
                result["json"] = json.loads(body.decode("utf-8",
                                                        errors="replace")
                                            or "null")
            except ValueError:
                result["json"] = None
        retryable = (status is None
                     and reason_class in (net_probe.REASON_DNS,
                                          net_probe.REASON_TIMEOUT)) \
            or _http_backoff.is_retry_status(status)
        if not retryable or attempt >= retries:
            break
        delay = schedule[attempt]
        applied.append(delay)
        sleeper(delay)
    result.update({"attempts": attempts, "statuses": statuses,
                   "backoff_applied": applied})
    return result


def excerpt(body):
    """Response body -> the capped decoded excerpt carried on a red record
    (the zen_mint precedent: 400 chars, errors replaced)."""
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) \
        else str(body or "")
    return text[:EXCERPT_CAP]


def mint_from(resp_json, field, source_desc):
    """Read one minted value verbatim from a response; fail loud when the
    field is absent - a missing minted field never degrades into an
    assembled string (the DOI link-string concatenation-error precedent)."""
    if not isinstance(resp_json, dict) \
            or resp_json.get(field) in (None, ""):
        raise MintError("the response carried no %r field (%s); refusing"
                        " to assemble the value" % (field, source_desc))
    return resp_json[field]


def mint_path(resp_json, path, source_desc):
    """Read one nested minted value verbatim (path like ["links",
    "bucket"]); same fail-loud discipline as mint_from."""
    node = resp_json
    walked = []
    for key in path:
        walked.append(key)
        if not isinstance(node, dict) or key not in node:
            raise MintError("the response carried no %r field (%s);"
                            " refusing to assemble the value"
                            % (".".join(walked), source_desc))
        node = node[key]
    if node in (None, ""):
        raise MintError("the response carried an empty %r field (%s);"
                        " refusing to assemble the value"
                        % (".".join(walked), source_desc))
    return node


def resolve_repo(repo_flag, use_git=True):
    """--repo flag or `git remote get-url origin` -> owner/name; None when
    unresolved (dry-run carries {owner}/{repo} placeholders; execution
    fails loud rc=9 instead of guessing)."""
    if repo_flag:
        m = re.fullmatch(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)",
                         repo_flag.strip())
        if not m:
            raise UsageError("--repo must be owner/name, got %r" % repo_flag)
        return m.group(1) + "/" + m.group(2)
    if not use_git:
        return None
    try:
        out = subprocess.run(["git", "remote", "get-url", "origin"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=10)
        url = out.stdout.decode("utf-8", errors="replace").strip()
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"[:/]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$",
                  url)
    return (m.group(1) + "/" + m.group(2)) if m else None


# ---- plan builder (pure, offline) -------------------------------------------

SCAN_SCANNED = (
    "the --assets directory listing (flat, non-recursive; per-file bytes"
    " and sha256 computed at plan time), and the --zenodo-metadata JSON"
    " file when given; nothing else is read"
)
SCAN_NOT_SCANNED = (
    "every network face in dry-run (no request is sent), the git tree,"
    " subdirectories under --assets, and the services' response state"
    " (only execution-stage records carry responses)"
)
SCAN_NEGATIVE_FINDING = (
    "the plan is a checklist of intended calls, not evidence any call"
    " succeeded; a green execution record is limited to the responses this"
    " invocation actually received"
)
SCAN_EQUIVALENTS = (
    "not exhaustive; asset bytes are hashed at plan time and re-read and"
    " re-hashed at upload time, and minted values are only ever read from"
    " responses this tool received"
)


def build_plan(issue, title, tag, assets, repo, metadata_path, metadata,
               stage):
    """The three-layer checklist with exact API calls (pure, offline; no
    request is sent and no minted value exists at plan time - the publish
    face only names the response fields it will read verbatim)."""
    owner_repo = repo or "{owner}/{repo}"
    resolved = bool(repo)
    layer1_calls = [
        {"step": "1.1", "method": "GET",
         "url": "%s/repos/%s/issues/%d" % (GH_API, owner_repo, issue),
         "purpose": "read the current issue body (the PATCH appends to"
                    " it, never overwrites blind)",
         "requires": ["GH_TOKEN or GITHUB_TOKEN"]},
        {"step": "1.2", "method": "PATCH",
         "url": "%s/repos/%s/issues/%d" % (GH_API, owner_repo, issue),
         "purpose": "append the release section to the issue body",
         "requires": ["GH_TOKEN or GITHUB_TOKEN"],
         "payload_summary": {"body": "current body + release section"
                                     " (title, tag, asset count) + the"
                                     " minted handles when"
                                     " --release-id/--deposit-id are"
                                     " supplied"}},
    ]
    layer2_calls = [
        {"step": "2.1", "method": "POST",
         "url": "%s/repos/%s/releases" % (GH_API, owner_repo),
         "purpose": "create the Release (the tag is created on the default"
                    " branch when absent)",
         "requires": ["GH_TOKEN or GITHUB_TOKEN"],
         "payload_summary": {"tag_name": tag, "name": title,
                             "body": "issue reference + per-asset sha256"
                                     " manifest"}},
    ]
    for i, asset in enumerate(assets, 1):
        layer2_calls.append(
            {"step": "2.%d" % (i + 1), "method": "POST",
             "url": "%s/repos/%s/releases/{release_id}/assets?name=%s"
                    % (GH_UPLOAD, owner_repo,
                       urllib.parse.quote(asset["name"])),
             "purpose": "upload %s (%d bytes, sha256 pinned at plan time"
                        " and re-verified at upload; the release id comes"
                        " verbatim from call 2.1's response)"
                        % (asset["name"], asset["bytes"]),
             "requires": ["GH_TOKEN or GITHUB_TOKEN"],
             "content_type": "application/octet-stream"})
    if metadata is not None:
        layer3_calls = [
            {"step": "3.1", "method": "POST",
             "url": "%s/deposit/depositions" % ZENODO_API,
             "purpose": "create the deposit (legacy deposit API, the"
                        " working form per project law)",
             "requires": ["ZENODO_TOKEN or ZENODO_ACCESS_TOKEN"],
             "payload_summary": {"metadata_keys": sorted(metadata)}},
        ]
        for i, asset in enumerate(assets, 1):
            layer3_calls.append(
                {"step": "3.%d" % (i + 1), "method": "PUT",
                 "url": "{bucket_url}/%s (the bucket URL comes verbatim"
                        " from call 3.1's response links.bucket - never"
                        " assembled)" % urllib.parse.quote(asset["name"]),
                 "purpose": "upload %s (%d bytes, sha256 re-verified at"
                            " upload)" % (asset["name"], asset["bytes"]),
                 "requires": ["ZENODO_TOKEN or ZENODO_ACCESS_TOKEN"],
                 "content_type": "application/octet-stream"})
        layer3_calls.append(
            {"step": "3.%d" % (len(assets) + 2), "method": "POST",
             "url": "%s/deposit/depositions/{deposit_id}/actions/publish"
                    % ZENODO_API,
             "purpose": "PUBLISH the deposit - irreversible; separately"
                        " gated as --stage 4 and run only after the"
                        " stage-3 stop-gate is verified",
             "requires": ["ZENODO_TOKEN or ZENODO_ACCESS_TOKEN",
                          "the --deposit-id minted by stage 3"],
             "minted_fields_read_verbatim": ["doi", "latest_html_url"],
             "gate": "--stage 4 (publish is its own stop-gate)"})
    else:
        layer3_calls = []
    layers = [
        {"layer": 1, "name": STAGE_NAMES[1], "calls": layer1_calls,
         "stop_gate": "after this layer: verify the issue body on the"
                      " service, then re-run with --stage 2"
                      " --confirm-publish"},
        {"layer": 2, "name": STAGE_NAMES[2], "calls": layer2_calls,
         "stop_gate": "after this layer: verify the Release page and its"
                      " assets, then re-run with --stage 3"
                      " --confirm-publish"},
        {"layer": 3, "name": STAGE_NAMES[3],
         "calls": layer3_calls,
         "blocked": metadata is None,
         "blocked_reason": None if metadata is not None else
         "--zenodo-metadata not provided (the deposit create has no"
         " payload); the layer shape is listed for completeness and runs"
         " only once the metadata file is supplied",
         "stop_gate": "after this layer: verify the deposit files, then"
                      " re-run with --stage 4 --confirm-publish (publish"
                      " is irreversible)"},
    ]
    return layers, owner_repo, resolved


# ---- run core ----------------------------------------------------------------

def build_report(issue, title, tag, assets_dir, assets, repo, resolved,
                 metadata_path, metadata, mode, stage, layers,
                 execution=None, minted=None, stop_gate=None,
                 chain_complete=False):
    """Assemble the single JSON report line (schema
    rocqwash-release-chain/1): every counter wrapped {value, basis} except
    scan_face (four fixed fields) and the structural listings."""
    return {
        "schema": SCHEMA,
        "mode": w(mode, "dry-run = plan only (the default, zero network);"
                       " execute = one gated stage ran against the live"
                       " services"),
        "issue": w(issue, "the --issue number the chain hangs off"),
        "release_title": w(title, "the --release-title as given; rides the"
                                  " Release payload verbatim"),
        "tag_name": w(tag, "deterministic tag slug of --release-title"
                           " (lowercase, non-alphanumeric runs collapsed to"
                           " '-', trimmed); created by the Release POST"
                           " when absent"),
        "repo": w(repo,
                  "owner/name carrying the issue and Release; resolved"
                  " from --repo (or git remote origin at execution time);"
                  " the {owner}/{repo} placeholder in dry-run call URLs"
                  " marks an unresolved repo honestly"
                  if resolved else
                  "unresolved: no --repo flag and dry-run does not invoke"
                  " git; call URLs carry the {owner}/{repo} placeholder"
                  " and execution would fail loud rc=9 rather than"
                  " guess"),
        "assets_dir": w(assets_dir, "the --assets directory as given"),
        "assets": w(assets,
                    "files in --assets (flat, non-recursive, sorted);"
                    " bytes = raw byte counts; sha256 = hex digests pinned"
                    " at plan time and re-verified at upload"),
        "zenodo_metadata": w(metadata_path,
                             "the --zenodo-metadata JSON file as given;"
                             " null = the Zenodo layer is listed blocked"),
        "plan": w(layers,
                  "the three-layer checklist (issue body update -> GitHub"
                  " Release with per-asset upload -> Zenodo deposit"
                  " create/bucket PUTs/publish) with exact API calls and"
                  " the stop-gate between layers"),
        "execution": w(execution,
                       "records of the calls this invocation actually"
                       " sent, with verbatim response excerpts; null ="
                       " dry-run sent nothing"
                       if execution is not None else
                       "dry-run: zero calls sent (the plan is the"
                       " deliverable; nothing is simulated)"),
        "minted": w(minted or [],
                    "values returned verbatim from API responses, each"
                    " with its source field; never assembled by string"
                    " concatenation (the DOI link-string concatenation"
                    "-error precedent)"),
        "stop_gate": w(stop_gate,
                       "the verification boundary now in force: the next"
                       " stage runs only as an explicit re-invocation"
                       " with --confirm-publish"
                       if stop_gate else
                       "no open stop-gate (dry-run, or the chain closed"
                       " with the publish stage)"),
        "chain_complete": w(chain_complete,
                            "true only when stage 4 (the irreversible"
                            " publish) answered success"),
        "scan_face": {
            "scanned": SCAN_SCANNED,
            "not_scanned": SCAN_NOT_SCANNED,
            "negative_finding": SCAN_NEGATIVE_FINDING,
            "equivalents": SCAN_EQUIVALENTS,
        },
    }


def run(opts, env=None, _send=None, _sleep=None):
    """The release-chain core.  opts keys: issue, release_title, assets,
    zenodo_metadata, confirm_publish, dry_run, repo, stage, release_id,
    deposit_id.  Returns (report, exit_code).  env/_send/_sleep are the
    injection points (offline selftest)."""
    issue = opts.get("issue")
    title = opts.get("release_title")
    if not title:
        raise UsageError("--release-title is required (the chain plan is"
                         " computed from it)")
    tag_probe = slugify_tag(title)
    if not tag_probe:
        raise UsageError("--release-title %r produces an empty tag slug"
                         " (no taggable characters)" % title)
    assets_dir = opts.get("assets")
    metadata_path = opts.get("zenodo_metadata")
    metadata = load_metadata(metadata_path) if metadata_path else None
    assets = scan_assets(assets_dir)
    tag = tag_probe
    stage = opts.get("stage")
    execute = bool(opts.get("confirm_publish")) and not opts.get("dry_run")

    layers, owner_repo, resolved = build_plan(
        issue, title, tag, assets, opts.get("repo"), metadata_path,
        metadata, stage)

    if not execute:
        report = build_report(issue, title, tag, assets_dir, assets,
                              owner_repo, resolved, metadata_path, metadata,
                              "dry-run", stage, layers)
        return report, 0

    # ---- execution preflight (fail loud before any call) ----
    if not gate_enabled(env):
        report = build_report(issue, title, tag, assets_dir, assets,
                              owner_repo, resolved, metadata_path, metadata,
                              "execute", stage, layers,
                              stop_gate="the network face is gated off"
                                        " (%s is not 1): the publish faces"
                                        " were not reached and nothing was"
                                        " sent (reported, not simulated)"
                                        % NET_GATE_ENV)
        return report, GATED_RC
    if stage not in STAGE_NAMES:
        raise UsageError("--stage must be 1, 2, 3 or 4 (one layer per"
                         " invocation; the layers are separately gated),"
                         " got %r" % (stage,))
    if not resolved:
        live_repo = resolve_repo(None, use_git=True)
        if not live_repo:
            raise PreflightError(
                "the repo is unresolved: pass --repo owner/name (execution"
                " mode does not guess; dry-run carries the"
                " {owner}/{repo} placeholder)")
        owner_repo, resolved = live_repo, True
        layers, _, _ = build_plan(issue, title, tag, assets, live_repo,
                                  metadata_path, metadata, stage)
    gh_needed = stage in (1, 2)
    zen_needed = stage in (3, 4)
    gh_name, gh_token = (read_cred(env, ("GH_TOKEN", "GITHUB_TOKEN"))
                         if gh_needed else (None, None))
    zen_name, zen_token = (read_cred(env, ("ZENODO_TOKEN",
                                           "ZENODO_ACCESS_TOKEN"))
                           if zen_needed else (None, None))
    if gh_needed and not gh_token:
        raise PreflightError("stage %d needs a GitHub credential: set"
                             " GH_TOKEN (or GITHUB_TOKEN)" % stage)
    if zen_needed and not zen_token:
        raise PreflightError("stage %d needs a Zenodo credential: set"
                             " ZENODO_TOKEN (or ZENODO_ACCESS_TOKEN)"
                             % stage)
    if stage == 4 and not opts.get("deposit_id"):
        raise PreflightError(
            "stage 4 (publish) requires --deposit-id: the irreversible"
            " publish cannot run without carrying stage 3's minted handle"
            " (the publish stop-gate)")

    call_kw = dict(timeout=opts.get("timeout", DEFAULT_TIMEOUT),
                   retries=opts.get("retries", DEFAULT_RETRIES),
                   backoff_base=opts.get("backoff_base",
                                         DEFAULT_BACKOFF_BASE),
                   _send=_send, _sleep=_sleep)
    execution = []
    minted = []

    def record(step, method, url, call):
        entry = {"step": step, "method": method, "url": url,
                 "status": call["status"],
                 "attempts": call["attempts"],
                 "statuses": call["statuses"],
                 "response_excerpt": excerpt(call["body"]) if call["status"] is None or call["status"] >= 300 else None,
                 "error": call["error"]}
        return entry

    def require_ok(call, step, method, url):
        """Non-2xx or transport failure -> red rc=1 with the excerpt
        registered (a failing result is data; no further call runs)."""
        if call["status"] is None or not (200 <= call["status"] < 300):
            execution.append(record(step, method, url, call))
            return False
        return True

    if stage == 1:
        url_get = "%s/repos/%s/issues/%d" % (GH_API, owner_repo, issue)
        get_call = api_call("GET", url_get, gh_token, **call_kw)
        if not require_ok(get_call, "1.1", "GET", url_get):
            return build_report(issue, title, tag, assets_dir, assets,
                                owner_repo, resolved, metadata_path,
                                metadata, "execute", stage, layers,
                                execution), 1
        current = get_call["json"] or {}
        body_now = current.get("body") or ""
        section = ("\n\n## Release\n\n- title: %s\n- tag: %s\n"
                   "- assets: %d file(s), sha256 pinned in the"
                   " release-chain log\n"
                   % (title, tag, len(assets)))
        if opts.get("release_id"):
            section += ("- release id: %s (minted by stage 2, carried"
                        " from its verbatim log)\n" % opts["release_id"])
        if opts.get("deposit_id"):
            section += ("- deposit id: %s (minted by stage 3, carried"
                        " from its verbatim log)\n" % opts["deposit_id"])
        patch_call = api_call("PATCH",
                              "%s/repos/%s/issues/%d" % (GH_API, owner_repo,
                                                         issue),
                              gh_token,
                              payload={"body": body_now + section},
                              **call_kw)
        url_patch = "%s/repos/%s/issues/%d" % (GH_API, owner_repo, issue)
        if not require_ok(patch_call, "1.2", "PATCH", url_patch):
            return build_report(issue, title, tag, assets_dir, assets,
                                owner_repo, resolved, metadata_path,
                                metadata, "execute", stage, layers,
                                execution), 1
        execution.append(record("1.1", "GET", url_get, get_call))
        execution.append(record("1.2", "PATCH", url_patch, patch_call))
        minted.append({"field": "issues.html_url",
                       "value": mint_from(current, "html_url",
                                          "GET the issue"),
                       "response": "GET /repos/%s/issues/%d"
                                   % (owner_repo, issue)})
        return build_report(issue, title, tag, assets_dir, assets,
                            owner_repo, resolved, metadata_path, metadata,
                            "execute", stage, layers, execution, minted,
                            "layer 1 (issue body update) executed; verify"
                            " the issue body, then re-run with --stage 2"
                            " --confirm-publish"), STOP_GATE_RC

    if stage == 2:
        manifest = "\n".join("- %s: sha256 %s" % (a["name"], a["sha256"])
                             for a in assets)
        release_payload = {
            "tag_name": tag,
            "name": title,
            "body": ("Independent audit release for issue #%d.\n\n"
                     "Asset manifest (sha256):\n%s\n" % (issue, manifest)),
        }
        url_rel = "%s/repos/%s/releases" % (GH_API, owner_repo)
        create = api_call("POST", url_rel, gh_token,
                          payload=release_payload, **call_kw)
        if not require_ok(create, "2.1", "POST", url_rel):
            return build_report(issue, title, tag, assets_dir, assets,
                                owner_repo, resolved, metadata_path,
                                metadata, "execute", stage, layers,
                                execution), 1
        execution.append(record("2.1", "POST", url_rel, create))
        release_json = create["json"] or {}
        release_id = mint_from(release_json, "id", "POST the Release")
        minted.append({"field": "releases.id", "value": release_id,
                       "response": "POST /repos/%s/releases" % owner_repo})
        minted.append({"field": "releases.html_url",
                       "value": mint_from(release_json, "html_url",
                                          "POST the Release"),
                       "response": "POST /repos/%s/releases" % owner_repo})
        for i, asset in enumerate(assets, 1):
            with open(os.path.join(assets_dir, asset["name"]), "rb") as fh:
                data = fh.read()
            got = hashlib.sha256(data).hexdigest()
            if got != asset["sha256"]:
                execution.append({
                    "step": "2.%d" % (i + 1), "method": "UPLOAD-SKIP",
                    "url": asset["name"], "status": None,
                    "attempts": 0, "statuses": [],
                    "response_excerpt": "asset drifted since plan time:"
                                        " plan sha256 %s, upload-time"
                                        " sha256 %s; refused to upload"
                                        % (asset["sha256"], got),
                    "error": None})
                return build_report(issue, title, tag, assets_dir, assets,
                                    owner_repo, resolved, metadata_path,
                                    metadata, "execute", stage, layers,
                                    execution), 1
            up = api_call("POST",
                          "%s/repos/%s/releases/%s/assets?name=%s"
                          % (GH_UPLOAD, owner_repo, release_id,
                             urllib.parse.quote(asset["name"])),
                          gh_token, data=data,
                          content_type="application/octet-stream",
                          **call_kw)
            url_up = ("%s/repos/%s/releases/%s/assets?name=%s"
                      % (GH_UPLOAD, owner_repo, release_id,
                         urllib.parse.quote(asset["name"])))
            if not require_ok(up, "2.%d" % (i + 1), "POST", url_up):
                return build_report(issue, title, tag, assets_dir, assets,
                                    owner_repo, resolved, metadata_path,
                                    metadata, "execute", stage, layers,
                                    execution), 1
            execution.append(record("2.%d" % (i + 1), "POST", url_up,
                                    up))
            asset_json = up["json"] or {}
            minted.append({"field": "release_assets.browser_download_url",
                           "value": mint_from(asset_json,
                                              "browser_download_url",
                                              "upload %s" % asset["name"]),
                           "response": "upload %s" % asset["name"]})
        return build_report(issue, title, tag, assets_dir, assets,
                            owner_repo, resolved, metadata_path, metadata,
                            "execute", stage, layers, execution, minted,
                            "layer 2 (Release create + per-asset upload)"
                            " executed; verify the Release page and its"
                            " assets, then re-run with --stage 3"
                            " --confirm-publish"), STOP_GATE_RC

    if stage == 3:
        url_dep = "%s/deposit/depositions" % ZENODO_API
        create = api_call("POST", url_dep, zen_token,
                          payload={"metadata": metadata}, **call_kw)
        if not require_ok(create, "3.1", "POST", url_dep):
            return build_report(issue, title, tag, assets_dir, assets,
                                owner_repo, resolved, metadata_path,
                                metadata, "execute", stage, layers,
                                execution), 1
        execution.append(record("3.1", "POST", url_dep, create))
        create_json = create["json"] or {}
        deposit_id = mint_from(create_json, "id", "POST the deposit")
        bucket = mint_path(create_json, ("links", "bucket"),
                           "POST the deposit")
        minted.append({"field": "deposits.id", "value": deposit_id,
                       "response": "POST /deposit/depositions"})
        minted.append({"field": "deposits.links.bucket", "value": bucket,
                       "response": "POST /deposit/depositions"})
        for i, asset in enumerate(assets, 1):
            with open(os.path.join(assets_dir, asset["name"]), "rb") as fh:
                data = fh.read()
            got = hashlib.sha256(data).hexdigest()
            if got != asset["sha256"]:
                execution.append({
                    "step": "3.%d" % (i + 1), "method": "UPLOAD-SKIP",
                    "url": asset["name"], "status": None,
                    "attempts": 0, "statuses": [],
                    "response_excerpt": "asset drifted since plan time:"
                                        " plan sha256 %s, upload-time"
                                        " sha256 %s; refused to upload"
                                        % (asset["sha256"], got),
                    "error": None})
                return build_report(issue, title, tag, assets_dir, assets,
                                    owner_repo, resolved, metadata_path,
                                    metadata, "execute", stage, layers,
                                    execution), 1
            put = api_call("PUT",
                           "%s/%s" % (bucket,
                                      urllib.parse.quote(asset["name"])),
                           zen_token, data=data,
                           content_type="application/octet-stream",
                           **call_kw)
            url_put = "%s/%s" % (bucket,
                                 urllib.parse.quote(asset["name"]))
            if not require_ok(put, "3.%d" % (i + 1), "PUT", url_put):
                return build_report(issue, title, tag, assets_dir, assets,
                                    owner_repo, resolved, metadata_path,
                                    metadata, "execute", stage, layers,
                                    execution), 1
            execution.append(record("3.%d" % (i + 1), "PUT", url_put,
                                    put))
        return build_report(issue, title, tag, assets_dir, assets,
                            owner_repo, resolved, metadata_path, metadata,
                            "execute", stage, layers, execution, minted,
                            "layer 3 (deposit create + bucket PUTs)"
                            " executed; verify the deposit files, then"
                            " re-run with --stage 4 --confirm-publish"
                            " (publish is irreversible)"), STOP_GATE_RC

    # stage 4: the irreversible publish, separately gated
    publish = api_call("POST",
                       "%s/deposit/depositions/%s/actions/publish"
                       % (ZENODO_API, opts["deposit_id"]),
                       zen_token, **call_kw)
    url_pub = ("%s/deposit/depositions/%s/actions/publish"
               % (ZENODO_API, opts["deposit_id"]))
    if not require_ok(publish, "4.1", "POST", url_pub):
        return build_report(issue, title, tag, assets_dir, assets,
                            owner_repo, resolved, metadata_path, metadata,
                            "execute", stage, layers, execution), 1
    execution.append(record("4.1", "POST", url_pub, publish))
    publish_json = publish["json"] or {}
    minted.append({"field": "deposits.doi",
                   "value": mint_from(publish_json, "doi",
                                      "POST actions/publish"),
                   "response": "POST /deposit/depositions/%s/actions"
                               "/publish" % opts["deposit_id"]})
    minted.append({"field": "deposits.latest_html_url",
                   "value": mint_from(publish_json, "latest_html_url",
                                      "POST actions/publish"),
                   "response": "POST /deposit/depositions/%s/actions"
                               "/publish" % opts["deposit_id"]})
    report = build_report(issue, title, tag, assets_dir, assets,
                          owner_repo, resolved, metadata_path, metadata,
                          "execute", stage, layers, execution, minted,
                          None, True)
    return report, 0


# ---- selftest ----------------------------------------------------------------

def subprocess_run(argv, env=None):
    """Run one child (the suite convention: merged stdout/stderr, decoded
    leniently)."""
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=env)
    p.stdout = p.stdout.decode("utf-8", errors="replace") \
        if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p


class CannedZen(object):
    """Injected send point: an ordered script of (method-prefix, status,
    json-body) answers; a canned miss fails loud (the test must match the
    call sequence exactly)."""

    def __init__(self, script):
        self.script = list(script)
        self.seen = []

    def __call__(self, method, url, data, headers, timeout):
        if not self.script:
            raise AssertionError("canned send exhausted at %s %s"
                                 % (method, url))
        want_method, status, payload = self.script[0]
        if not method.startswith(want_method):
            raise AssertionError("canned script wanted %s, got %s %s"
                                 % (want_method, method, url))
        self.script.pop(0)
        self.seen.append((method, url, len(data or b"")))
        body = json.dumps(payload).encode("utf-8") if payload is not None \
            else b""
        return status, body


def selftest():
    """Offline vector set: plan-shape faces (zero network) over canned
    fixtures, injected-transport execution faces for all four stages, and
    the honest gate/usage faces."""
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="release_chain_self_")
    fails = []

    def check(name, ok, detail=""):
        if ok:
            print("[PASS] %s" % name)
        else:
            fails.append(name)
            print("[FAIL] %s %s" % (name, detail))

    try:
        PINS = b"alpha 31337\nbeta 31338\n"
        RECEIPT = b"# audit receipt fixture\n\nverdict: clean\n"
        assets_dir = os.path.join(tmp, "assets")
        os.mkdir(assets_dir)
        with open(os.path.join(assets_dir, "receipt.md"), "wb") as fh:
            fh.write(RECEIPT)
        with open(os.path.join(assets_dir, "pins.txt"), "wb") as fh:
            fh.write(PINS)
        meta_path = os.path.join(tmp, "zenodo-meta.json")
        with open(meta_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"title": "Audit wave-1 evidence volume (fixture)",
                       "creators": [{"name": "Fixture, Test"}],
                       "upload_type": "publication"}, fh)

        base = {"issue": 21, "release_title": "Wave 1: Evidence Volume!",
                "assets": assets_dir, "zenodo_metadata": meta_path,
                "dry_run": True}

        # 1. dry-run default: the three-layer plan, exact order, rc 0
        rep, rc = run(dict(base))
        check("dryrun rc0", rc == 0, rc)
        layer_names = [l["name"] for l in rep["plan"]["value"]]
        check("plan three layers in order",
              layer_names == ["issue-body-update",
                              "github-release-upload",
                              "zenodo-deposit-upload"], layer_names)
        check("plan execution null",
              rep["execution"]["value"] is None
              and "zero calls sent" in rep["execution"]["basis"],
              rep["execution"])
        check("dryrun no stop-gate claim",
              rep["stop_gate"]["value"] is None
              and "no open stop-gate" in rep["stop_gate"]["basis"],
              rep["stop_gate"])

        # 2. exact API-call strings present in the checklist
        blob = json.dumps(rep["plan"]["value"])
        for needle in (
                '"method": "GET", "url": "https://api.github.com/repos/'
                '{owner}/{repo}/issues/21"',
                '"method": "PATCH", "url": "https://api.github.com/repos/'
                '{owner}/{repo}/issues/21"',
                '"method": "POST", "url": "https://api.github.com/repos/'
                '{owner}/{repo}/releases"',
                "https://uploads.github.com/repos/{owner}/{repo}"
                "/releases/{release_id}/assets?name=",
                '"method": "POST", "url": "https://zenodo.org/api/deposit'
                '/depositions"',
                "links.bucket", "/actions/publish"):
            check("plan call %s" % needle.split("?")[0][-40:], needle in blob,
                  needle)

        # 3. the no-DOI-concatenation guard: no assembled doi.org URL in
        #    the plan; minted fields are declared response-field reads
        check("plan no doi assembly", "doi.org" not in json.dumps(rep),
              "a doi.org string leaked into the plan")
        publish_calls = [c for l in rep["plan"]["value"]
                         for c in l["calls"]
                         if "minted_fields_read_verbatim" in c]
        check("plan minted-field pointers",
              len(publish_calls) == 1
              and publish_calls[0]["minted_fields_read_verbatim"]
              == ["doi", "latest_html_url"],
              publish_calls)
        check("plan zenodo layer shape",
              len([c for l in rep["plan"]["value"] if l["layer"] == 3
                   for c in l["calls"]]) == 4,
              "create + 2 asset PUTs + publish expected")

        # 4. explicit --dry-run == the default dry-run (byte-equal plans)
        rep_explicit, rc = run(dict(base, dry_run=True))
        check("explicit-dryrun equal",
              rc == 0 and rep_explicit["plan"] == rep["plan"], rc)

        # 5. tag slug determinism + assets pinned with wrapped counters
        check("tag slug",
              rep["tag_name"]["value"] == "wave-1-evidence-volume",
              rep["tag_name"])
        names = [a["name"] for a in rep["assets"]["value"]]
        check("assets pinned",
              names == ["pins.txt", "receipt.md"]
              and all(isinstance(a["bytes"], int) and len(a["sha256"]) == 64
                      for a in rep["assets"]["value"]),
              rep["assets"]["value"])
        shape_bare = [k for k in rep
                      if k not in ("scan_face", "schema", "plan",
                                   "assets")
                      and not (isinstance(rep[k], dict)
                               and "value" in rep[k]
                               and "basis" in rep[k])]
        check("value-basis-shape", shape_bare == [],
              "bare keys: %s" % shape_bare)
        check("scan-face-fields",
              sorted(rep["scan_face"]) == ["equivalents",
                                           "negative_finding",
                                           "not_scanned", "scanned"],
              sorted(rep["scan_face"]))
        check("scan-face assets-dir claim",
              "assets directory listing" in rep["scan_face"]["scanned"]
              and "no request is sent" in rep["scan_face"]["not_scanned"],
              rep["scan_face"])

        # 6. dry-run without metadata: the Zenodo layer lists blocked
        rep_nometa, rc = run(dict(base, zenodo_metadata=None))
        zen = [l for l in rep_nometa["plan"]["value"] if l["layer"] == 3][0]
        check("blocked zenodo layer honest",
              rc == 0 and zen["blocked"] is True
              and "--zenodo-metadata not provided" in zen["blocked_reason"]
              and zen["calls"] == [],
              zen)

        # 7. execution faces (injected transport, scrubbed env):
        #    gate off -> rc 111; gate on without creds -> rc 9
        env_off = {"PATH": os.environ.get("PATH", "")}
        rep, rc = run(dict(base, confirm_publish=True, stage=1, dry_run=False),
                      env=env_off)
        check("gate rc111", rc == GATED_RC
              and "gated off" in (rep["stop_gate"]["value"] or ""),
              (rc, rep["stop_gate"]))
        env_gh = {"ROCQWASH_MCP_ALLOW_NET": "1", "GH_TOKEN": "fixture-t"}
        env_zen = {"ROCQWASH_MCP_ALLOW_NET": "1", "ZENODO_TOKEN": "fixture-z"}
        try:
            run(dict(base, confirm_publish=True, stage=1, dry_run=False),
                env={"ROCQWASH_MCP_ALLOW_NET": "1"})
            check("creds rc9", False, "no PreflightError raised")
        except PreflightError as exc:
            check("creds rc9", "GH_TOKEN" in str(exc), str(exc))
        try:
            run(dict(base, confirm_publish=True, stage=3, dry_run=False), env=env_gh)
            check("zenodo-creds rc9", False, "no PreflightError raised")
        except PreflightError as exc:
            check("zenodo-creds rc9", "ZENODO_TOKEN" in str(exc), str(exc))

        # 8. stage 1 executed: GET + PATCH, minted html_url verbatim,
        #    rc 3 stop-gate naming --stage 2
        issue_json = {"number": 21, "html_url": "https://example.invalid/"
                                              "repo/issues/21",
                      "body": "original body"}
        patch_json = {"number": 21, "html_url": "https://example.invalid/"
                                                "repo/issues/21"}
        send1 = CannedZen([("GET", 200, issue_json),
                           ("PATCH", 200, patch_json)])
        rep, rc = run(dict(base, confirm_publish=True, stage=1, dry_run=False),
                      env=env_gh, _send=send1)
        check("stage1 rc3", rc == STOP_GATE_RC, rc)
        check("stage1 steps",
              [e["step"] for e in rep["execution"]["value"]] == ["1.1",
                                                                 "1.2"],
              rep["execution"]["value"])
        check("stage1 minted verbatim",
              rep["minted"]["value"][0]["value"]
              == "https://example.invalid/repo/issues/21"
              and rep["minted"]["value"][0]["field"] == "issues.html_url",
              rep["minted"]["value"])
        check("stage1 stop-gate names next",
              "--stage 2" in rep["stop_gate"]["value"],
              rep["stop_gate"])
        check("stage1 append not overwrite",
              send1.seen[1][1].endswith("/issues/21")
              and send1.seen[0][0] == "GET", send1.seen)

        # 9. stage 2: Release create + per-asset uploads, minted
        #    browser_download_url verbatim, rc 3 naming --stage 3
        rel_json = {"id": 777,
                    "html_url": "https://example.invalid/repo/releases/"
                                "tag/wave-1-evidence-volume"}
        asset_tpl = {"browser_download_url":
                     "https://example.invalid/repo/releases/download/"
                     "wave-1-evidence-volume/%s"}
        send2 = CannedZen([
            ("POST", 201, rel_json),
            ("POST", 201, dict(asset_tpl,
                               browser_download_url=asset_tpl[
                                   "browser_download_url"] % "pins.txt")),
            ("POST", 201, dict(asset_tpl,
                               browser_download_url=asset_tpl[
                                   "browser_download_url"] % "receipt.md")),
        ])
        rep, rc = run(dict(base, confirm_publish=True, stage=2, dry_run=False,
                           repo="fixture/audit"),
                      env=env_gh, _send=send2)
        check("stage2 rc3", rc == STOP_GATE_RC, rc)
        check("stage2 minted ids+downloads",
              [m["field"] for m in rep["minted"]["value"]]
              == ["releases.id", "releases.html_url",
                  "release_assets.browser_download_url",
                  "release_assets.browser_download_url"]
              and rep["minted"]["value"][0]["value"] == 777,
              rep["minted"]["value"])
        check("stage2 upload byte counts",
              send2.seen[1][2] == len(PINS)
              and send2.seen[2][2] == len(RECEIPT),
              send2.seen[1:])
        check("stage2 stop-gate names next",
              "--stage 3" in rep["stop_gate"]["value"], rep["stop_gate"])

        # 10. stage 3: deposit create + bucket PUTs, bucket URL verbatim
        #     from links.bucket, rc 3 naming --stage 4
        dep_json = {"id": 42,
                    "links": {"bucket": "https://zenodo.example/api/files"
                                        "/canned-bucket-id"}}
        send3 = CannedZen([("POST", 201, dep_json),
                           ("PUT", 200, {"id": "f1"}),
                           ("PUT", 200, {"id": "f2"})])
        rep, rc = run(dict(base, confirm_publish=True, stage=3, dry_run=False,
                           repo="fixture/audit"),
                      env=env_zen, _send=send3)
        check("stage3 rc3", rc == STOP_GATE_RC, rc)
        check("stage3 bucket verbatim",
              rep["minted"]["value"][1]["value"]
              == "https://zenodo.example/api/files/canned-bucket-id"
              and send3.seen[1][1].startswith(
                  "https://zenodo.example/api/files/canned-bucket-id/"),
              (rep["minted"]["value"], send3.seen[1]))
        check("stage3 stop-gate names publish",
              "--stage 4" in rep["stop_gate"]["value"]
              and "irreversible" in rep["stop_gate"]["value"],
              rep["stop_gate"])

        # 11. stage 4 interlock: publish without the minted deposit id is
        #     refused before any call; with it, the DOI comes back
        #     verbatim and the chain closes rc 0
        try:
            run(dict(base, confirm_publish=True, stage=4, dry_run=False,
                     repo="fixture/audit"), env=env_zen, _send=CannedZen([]))
            check("publish interlock", False, "no PreflightError raised")
        except PreflightError as exc:
            check("publish interlock", "--deposit-id" in str(exc), str(exc))
        pub_json = {"doi": "10.5281/zenodo.999999",
                    "latest_html_url": "https://zenodo.example/records/999999"}
        send4 = CannedZen([("POST", 202, pub_json)])
        rep, rc = run(dict(base, confirm_publish=True, stage=4, dry_run=False,
                           repo="fixture/audit", deposit_id=42),
                      env=env_zen, _send=send4)
        check("stage4 rc0", rc == 0, rc)
        check("stage4 doi verbatim",
              rep["minted"]["value"][0]["value"] == "10.5281/zenodo.999999"
              and rep["minted"]["value"][1]["value"]
              == "https://zenodo.example/records/999999",
              rep["minted"]["value"])
        check("stage4 chain complete",
              rep["chain_complete"]["value"] is True
              and rep["stop_gate"]["value"] is None,
              (rep["chain_complete"], rep["stop_gate"]))
        check("stage4 no doi assembly",
              "doi.org" not in json.dumps(rep),
              "a doi.org string was assembled instead of read")

        # 12. red data: a 422 semantic face answers once and lands rc=1
        #     with the excerpt, and no further call runs
        send_red = CannedZen([("POST", 422, {"message": "validation failed"
                                                     " (fixture)"})])
        rep, rc = run(dict(base, confirm_publish=True, stage=2, dry_run=False,
                           repo="fixture/audit"), env=env_gh,
                      _send=send_red)
        check("red422 rc1", rc == 1, rc)
        check("red422 excerpt registered",
              "validation failed" in
              rep["execution"]["value"][0]["response_excerpt"]
              and len(rep["execution"]["value"]) == 1,
              rep["execution"]["value"])

        # 13. usage / missing-path faces
        try:
            run(dict(base, release_title=None))
            check("usage rc2 title", False, "no UsageError raised")
        except UsageError:
            check("usage rc2 title", True)
        try:
            run(dict(base, stage=9, confirm_publish=True, dry_run=False), env=env_gh)
            check("stage range rc2", False, "no UsageError raised")
        except UsageError:
            check("stage range rc2", True)
        try:
            run(dict(base, assets=os.path.join(tmp, "no_assets")))
            check("missing assets rc9", False, "no PreflightError raised")
        except PreflightError:
            check("missing assets rc9", True)
        bad_meta = os.path.join(tmp, "bad-meta.json")
        with open(bad_meta, "w", encoding="utf-8") as fh:
            fh.write('{"notitle": true}')
        try:
            run(dict(base, zenodo_metadata=bad_meta))
            check("metadata title rc2", False, "no UsageError raised")
        except UsageError:
            check("metadata title rc2", True)

        # 14. CLI faces: gate rc=111 (subprocess, env sans the gate);
        #     missing --issue rc=2
        script = os.path.join(_TOOLS_DIR, PROG + ".py")
        env = dict(os.environ)
        env.pop(NET_GATE_ENV, None)
        p = subprocess_run([sys.executable, "-I", "-B", script,
                            "--issue", "21",
                            "--release-title", "t",
                            "--assets", assets_dir,
                            "--confirm-publish", "--stage", "1"], env=env)
        check("cli gate rc111", p.returncode == GATED_RC,
              "rc=%s out=%s" % (p.returncode, p.stdout[:200]))
        p = subprocess_run([sys.executable, "-I", "-B", script,
                            "--release-title", "t",
                            "--assets", assets_dir], env=env)
        check("cli usage rc2", p.returncode == 2, "rc=%s" % p.returncode)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("[SELFTEST] release_chain red: %d vector(s) failed: %s"
              % (len(fails), ", ".join(fails)))
        return 1
    print("[SELFTEST] release_chain green: three-layer plan order/exact"
          " API-call strings/no-DOI-concatenation guard/tag slug/asset"
          " pinning/blocked zenodo honesty/gate rc111/credential rc9/stage"
          " 1-3 stop-gate carries with verbatim minted fields/publish"
          " interlock + verbatim DOI/red 422 with excerpt/usage faces -"
          " all vectors pass offline")
    return 0


def main(argv=None):
    """CLI entry; returns the process exit code."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="release chain face: issue -> GitHub Release -> Zenodo"
                    " as a three-layer plan (default dry-run); actual"
                    " publish steps are separately gated, one layer per"
                    " invocation, minted values verbatim from responses")
    ap.add_argument("--issue", type=int, default=None, metavar="N",
                    help="the issue number the chain hangs off (required)")
    ap.add_argument("--release-title", default=None, metavar="TITLE",
                    help="the Release title (required; also pins the tag"
                         " slug)")
    ap.add_argument("--assets", default=None, metavar="DIR",
                    help="directory of release assets, uploaded per-asset"
                         " to both faces (required)")
    ap.add_argument("--zenodo-metadata", default=None, metavar="JSON",
                    help="Zenodo deposit metadata JSON file (a JSON object"
                         " with a title key); without it the Zenodo layer"
                         " is listed blocked")
    ap.add_argument("--confirm-publish", action="store_true",
                    help="execute ONE stage against the live services"
                         " (requires ROCQWASH_MCP_ALLOW_NET=1 and the"
                         " stage credentials); without it the tool stays"
                         " in dry-run")
    ap.add_argument("--dry-run", action="store_true",
                    help="explicit dry-run (the default already); plan"
                         " only, zero network")
    ap.add_argument("--repo", default=None, metavar="OWNER/NAME",
                    help="the repository carrying the issue and Release;"
                         " execution mode resolves it from this flag or"
                         " git remote origin, and fails loud rc=9"
                         " otherwise")
    ap.add_argument("--stage", type=int, default=None, metavar="1|2|3|4",
                    help="which gated layer to execute: 1 issue body"
                         " update, 2 Release create + uploads, 3 deposit"
                         " create + bucket PUTs, 4 publish (irreversible,"
                         " needs --deposit-id)")
    ap.add_argument("--release-id", type=int, default=None, metavar="N",
                    help="a stage-2 minted Release id carried into a"
                         " stage-1 finalize re-run (verbatim from its log)")
    ap.add_argument("--deposit-id", default=None, metavar="N",
                    help="the stage-3 minted deposit id; REQUIRED for"
                         " stage 4 (the publish stop-gate carry)")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    metavar="SEC", help="per-call timeout seconds"
                    " (default %s)" % DEFAULT_TIMEOUT)
    args = ap.parse_args(argv)

    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    missing = [flag for flag, val in (
        ("--issue", args.issue is not None),
        ("--release-title", bool(args.release_title)),
        ("--assets", bool(args.assets))) if not val]
    if missing:
        print("FAIL-LOUD: missing required flags: %s (the chain plan is"
              " computed from these three inputs)" % ", ".join(missing),
              file=sys.stderr)
        return 2
    if args.stage is not None and not args.confirm_publish:
        print("FAIL-LOUD: --stage selects an execution layer and only"
              " means something with --confirm-publish (dry-run always"
              " plans all layers)", file=sys.stderr)
        return 2

    opts = {"issue": args.issue, "release_title": args.release_title,
            "assets": args.assets, "zenodo_metadata": args.zenodo_metadata,
            "confirm_publish": args.confirm_publish,
            "dry_run": args.dry_run, "repo": args.repo,
            "stage": args.stage, "release_id": args.release_id,
            "deposit_id": args.deposit_id, "timeout": args.timeout}
    try:
        report, rc = run(opts)
    except UsageError as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        return 2
    except PreflightError as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        return 9
    except MintError as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        return 1
    payload = json.dumps(report, ensure_ascii=False)
    print(payload)
    if rc == GATED_RC:
        print("FAIL-LOUD: the publish faces are unreachable: set %s=1 to"
              " execute stage %s (reported, not simulated)"
              % (NET_GATE_ENV, args.stage), file=sys.stderr)
    elif rc == STOP_GATE_RC:
        print("STOP-GATE: %s" % report["stop_gate"]["value"],
              file=sys.stderr)
    elif rc == 1:
        print("FAIL-LOUD: red data: an execution call answered non-2xx or"
              " an asset drifted (the JSON line above carries the"
              " excerpt)", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
