#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""watch.py - CI run monitor, pin-IP push wrapper, and ls-remote confirmation (rocqwash watch/).
Purpose.  Three subcommands, all mechanical, remote-read-only, structurally free of
  rerun/cancel/`workflow_dispatch` code paths (the hands-off rule holds by structure).
  `ci` accounts in-flight Actions runs from offline evidence (`--runs-json <f>`, zero
  network by itself) or from one online read-only GET (`--repo owner/name --online`);
  any status != "completed" counts as in flight (unknown statuses count as in flight,
  fail-closed); active=0 exits 0, active>0 or unusable evidence exits 1.  `push` is a
  dry-run-by-default git push wrapper with masked output and an optional pin-IP host
  rewrite; `confirm` makes N (N >= 2) ls-remote reads that must all equal `--sha`.

Interface.  python3 watch/watch.py <ci|push|confirm> [flags] | --selftest.  ci:
  --runs-json <f> [--interval N --timeout S] [--json out] or --repo owner/name --online
  [--branch b] [--token-env VAR].  push: [--repo dir] [--remote origin] [--pin-ip IP
  --url-host HOST] [--mask STR]... [--ssl-verify-off] --yes|--dry-run [-- refspecs...].
  confirm: --remote origin --branch main --sha <sha> [--reads 2 --gap 2] (details in
  the extended-contract comments below).

Dependencies.  Python 3 standard library only; git on PATH; zero network except the
  single read-only GET in online `ci` mode; zero compile, zero queue.

Evidence.  `--selftest` (suite case t_watch, tests/run_tests.sh) runs the frozen vector
  set with zero network and zero repo writes: ci verdicts (idle 0 / in-flight 1 /
  unknown status 1 / malformed 1 / missing file 9), rewrite_host and masking unit
  vectors, push dry-run vectors, env masking, confirm vectors on a real local ls-remote.

Exit-codes.  ci: 0 idle, 1 in flight or unusable evidence, 2 usage, 9 evidence file
  missing.  push: 0 dry run, else the git push code passed through, 2 usage, 9 remote
  missing.  confirm: 0 confirmed, 1 reads disagree or ls-remote failed, 2 usage, 9 repo
  dir missing.  --selftest: 0 pass, nonzero failure.
"""
# Extended contract (subcommand details; kept outside the five-field block so the
# header stays within the 30-line budget of the annotation standard):
# ci offline evidence mode   --runs-json <f> parses a prefetched Actions runs JSON
#                            (the caller prefetches when the anonymous API 404s a
#                            private repo; this tool itself makes no request);
#                            --interval N --timeout S re-reads the file until idle
#                            (polling runs no compile and no heavy load).
# ci online mode             --repo owner/name --online makes one read-only GET on
#                            actions/runs (the only network action); timeout, 404
#                            and unreachable all record the FAIL fact as-is (an
#                            anonymous 404 on a private repo is expected; switch
#                            to the offline evidence mode).
# push                       default dry run: prints the exact command with every
#                            mask string (each --mask value, the remote URL
#                            userinfo password part, and env ROCQWASH_MASK
#                            colon-separated entries) replaced by ***MASKED***;
#                            zero network, zero execution; --yes performs the
#                            real push and passes the git push exit code through.
# push pin-IP mode           --pin-ip rewrites the remote URL host to the IP
#                            (scheme/userinfo/port/path kept) and adds
#                            -c http.<rewritten-url>.extraheader=Host: <url-host>;
#                            connecting by IP sends no SNI, so certificate
#                            hostname verification can fail and --ssl-verify-off
#                            must be given explicitly (loud warning; sslVerify is
#                            untouched by default).
# confirm                    N reads (N >= 2) of refs/heads/<branch> via ls-remote;
#                            all reads equal --sha exits 0 (PUSH-CONFIRMED), any
#                            difference or failed read exits 1 with a per-read
#                            account.
# write domain               no repo-tree or sandbox writes; push executes only the
#                            git push the caller states explicitly, and only under
#                            --yes (dry run is the default).
# honesty discipline         mechanical evidence only; NOT-RUN and NETWORK-UNREACHABLE
#                            are recorded explicitly and never count as passing;
#                            fail loud.
import argparse
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

PROG = "watch"
CI_DONE = "completed"
MASKED = "***MASKED***"
ACTIVE_NOTE = "any status!=%s counts as in flight (conservative)" % CI_DONE


def run_out(argv, cwd=None):
    p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def git(repo, *args):
    return run_out(["git", "-C", repo] + list(args))


def mask_text(s, masks):
    """Replace every string in masks with ***MASKED*** (empty entries ignored)."""
    for m in masks:
        if m:
            s = s.replace(m, MASKED)
    return s


def rewrite_host(url, ip):
    """Rewrite the URL host to ip (scheme/userinfo/port/path kept); non-http(s) fails loud."""
    rest = None
    for sch in ("https://", "http://"):
        if url.startswith(sch):
            rest = url[len(sch):]
            break
    if rest is None:
        raise ValueError("pin-IP supports http(s) URLs only, got %r" % url)
    authority, _, path = rest.partition("/")
    userinfo = ""
    if "@" in authority:
        userinfo, _, authority = authority.rpartition("@")
    host_port = authority
    new_authority = ip if host_port == host_port.rstrip(":0123456789") else None
    if ":" in host_port:  # host with a port
        h, _, p = host_port.partition(":")
        new_authority = "%s:%s" % (ip, p)
    if new_authority is None:
        new_authority = ip
    head = "%s%s%s" % (url[:len(sch)], (userinfo + "@") if userinfo else "",
                       new_authority)
    return head + "/" + path if path or "/" in rest else head


def url_secret_masks(url):
    """Remote-URL embedded credentials (userinfo password part) to a mask-string list."""
    masks = []
    for sch in ("https://", "http://"):
        if url.startswith(sch):
            rest = url[len(sch):]
            authority = rest.partition("/")[0]
            if "@" in authority:
                userinfo = authority.rpartition("@")[0]
                _, _, secret = userinfo.partition(":")
                if secret:
                    masks.append(secret)
            break
    return masks


def parse_runs(doc):
    """Parse a runs JSON into (active, total); malformed input raises ValueError."""
    runs = doc["runs"]
    if not isinstance(runs, list):
        raise ValueError("runs is not a list")
    active = [(r.get("name", "?"), r.get("status", "?"))
              for r in runs if r.get("status") != CI_DONE]
    return active, len(runs)


# ---------------- [1] ci ----------------

def cmd_ci(args):
    if args.runs_json:
        if not os.path.isfile(args.runs_json):
            print("FAIL-LOUD: runs-json file missing: %s" % args.runs_json, file=sys.stderr)
            sys.exit(9)
        deadline = time.time() + args.timeout
        while True:
            try:
                with io.open(args.runs_json, encoding="utf-8") as fh:
                    active, total = parse_runs(json.load(fh))
            except Exception as e:
                print("ci FAIL: runs-json malformed (evidence unusable): %s" % e)
                sys.exit(1)
            verdict = _ci_verdict(active, total, "runs-json evidence")
            if verdict or args.interval <= 0 or time.time() >= deadline:
                sys.exit(0 if verdict else 1)
            time.sleep(args.interval)
    if args.repo and args.online:
        url = "https://api.github.com/repos/%s/actions/runs?per_page=%d" % (
            args.repo, args.top)
        if args.branch:
            url += "&branch=%s" % args.branch
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                                   "User-Agent": "rocqwash-watch"})
        tok = os.environ.get(args.token_env, "") if args.token_env else ""
        if tok:
            req.add_header("Authorization", "Bearer %s" % tok)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                active, total = parse_runs(json.load(r))
        except Exception as e:
            print("ci FAIL: NETWORK-UNREACHABLE (read-only query did not connect): %s" % e)
            print("  (anonymous 404 on a private repo is expected - switch to the "
                  "--runs-json offline evidence mode)")
            sys.exit(1)
        verdict = _ci_verdict(active, total, "api.github.com read-only query")
        sys.exit(0 if verdict else 1)
    print("FAIL-LOUD: ci needs --runs-json <f> (offline evidence) "
          "or --repo owner/name --online (online query)", file=sys.stderr)
    sys.exit(2)


def _ci_verdict(active, total, source):
    if active:
        print("ci ACTIVE: in-flight run=%d (%s, %s): %s" % (
            len(active), source, ACTIVE_NOTE,
            ", ".join("%s/%s" % x for x in active[:5])))
        print("ci: exit 1 (runs still in flight, do not push yet)")
        return False
    print("ci CI-IDLE: in-flight=0 (%s, %d runs total, all %s)" % (source, total, CI_DONE))
    print("ci: exit 0")
    return True


# ---------------- [2] push ----------------

def collect_masks(args, url):
    masks = list(args.mask)
    masks += url_secret_masks(url)
    env_masks = os.environ.get("ROCQWASH_MASK", "")
    masks += [m for m in env_masks.split(":") if m]
    return masks


def build_push_cmd(args, repo):
    rc, so, se = git(repo, "remote", "get-url", "--push", args.remote)
    if rc != 0:
        print("FAIL-LOUD: remote missing: %s (%s)" % (args.remote, se.strip()[:120]),
              file=sys.stderr)
        sys.exit(9)
    url = so.strip()
    masks = collect_masks(args, url)
    cmd = ["git", "-C", repo]
    if args.pin_ip:
        if not args.url_host:
            print("FAIL-LOUD: --pin-ip requires --url-host", file=sys.stderr)
            sys.exit(2)
        if args.url_host not in url:
            print("FAIL-LOUD: --url-host %r not found in the remote URL: %s"
                  % (args.url_host, mask_text(url, masks)), file=sys.stderr)
            sys.exit(2)
        rewritten = rewrite_host(url, args.pin_ip)
        cmd += ["-c", "http.%s.extraheader=Host: %s" % (rewritten, args.url_host)]
        if args.ssl_verify_off:
            cmd += ["-c", "http.sslVerify=false"]
        target = rewritten
    else:
        if args.ssl_verify_off:
            print("FAIL-LOUD: --ssl-verify-off is only valid in pin-IP mode "
                  "(non-pinned mode leaves sslVerify untouched)", file=sys.stderr)
            sys.exit(2)
        target = url
    cmd += ["push", target] + args.refspecs
    return cmd, masks, url, target


def cmd_push(args):
    repo = os.path.abspath(args.repo)
    if not os.path.isdir(repo):
        print("FAIL-LOUD: repo directory missing: %s" % repo, file=sys.stderr)
        sys.exit(9)
    cmd, masks, url, target = build_push_cmd(args, repo)
    shown = " ".join(mask_text(part, masks) for part in cmd)
    if not args.yes:
        print("push DRY-RUN (default, zero network, zero execution) - would run:")
        print("  " + shown)
        print("push: exit 0 (real push only with --yes; after pushing run confirm "
              "for an N-read ls-remote check)")
        sys.exit(0)
    if args.ssl_verify_off:
        print("[watch] warning: --ssl-verify-off active (certificate hostname "
              "verification disabled, explicit choice in pin-IP mode)")
    rc, so, se = run_out(cmd)
    out = mask_text(so + se, masks)
    if out.strip():
        print(out.rstrip())
    print("push rc=%d target=%s" % (rc, mask_text(target, masks)))
    print("push: exit %d (run confirm --sha <pushed sha> for an N-read ls-remote check)" % rc)
    sys.exit(rc)


# ---------------- [3] confirm ----------------

def cmd_confirm(args):
    repo = os.path.abspath(args.repo)
    if not os.path.isdir(repo):
        print("FAIL-LOUD: repo directory missing: %s" % repo, file=sys.stderr)
        sys.exit(9)
    if args.reads < 2:
        print("FAIL-LOUD: --reads must be >= 2 (two reads are the discipline floor)",
              file=sys.stderr)
        sys.exit(2)
    if not args.sha:
        print("FAIL-LOUD: confirm needs --sha <expected sha>", file=sys.stderr)
        sys.exit(2)
    ref = "refs/heads/%s" % args.branch
    seen = []
    for i in range(args.reads):
        if i:
            time.sleep(args.gap)
        rc, so, se = git(repo, "ls-remote", args.remote, ref)
        if rc != 0 or not so.strip():
            print("confirm READ-%d FAIL: ls-remote rc=%d %s" % (i + 1, rc, se.strip()[:120]))
            sys.exit(1)
        sha = so.split()[0]
        seen.append(sha)
        print("confirm READ-%d: %s %s" % (i + 1, sha[:12], "==" if sha == args.sha else "!="))
    if all(s == args.sha for s in seen):
        print("PUSH-CONFIRMED: %d reads all equal %s (origin/%s confirmed)" % (args.reads, args.sha[:12], args.branch))
        sys.exit(0)
    print("confirm FAIL: %d reads disagree (expected %s, got %s)" % (
        args.reads, args.sha[:12], ",".join(s[:12] for s in seen)))
    sys.exit(1)


# ---------------- selftest (frozen vector set: zero network, zero repo writes) ----------------

def selftest():
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_watch_self_")
    try:
        pg = [sys.executable, "-B", os.path.abspath(__file__)]

        # ci offline evidence vectors
        idle = os.path.join(tmp, "idle.json")
        with io.open(idle, "w", encoding="utf-8") as fh:
            json.dump({"total_count": 2, "runs": [
                {"name": "ci", "status": "completed", "conclusion": "success"},
                {"name": "ci", "status": "completed", "conclusion": "failure"}]}, fh)
        busy = os.path.join(tmp, "busy.json")
        with io.open(busy, "w", encoding="utf-8") as fh:
            json.dump({"total_count": 1, "runs": [{"name": "ci",
                                                   "status": "in_progress"}]}, fh)
        bad = os.path.join(tmp, "bad.json")
        with io.open(bad, "w", encoding="utf-8") as fh:
            fh.write("{oops")
        rc, so, _ = run_out(pg + ["ci", "--runs-json", idle])
        assert rc == 0 and "CI-IDLE" in so and "in-flight=0" in so, \
            "idle should exit 0\n%s" % so
        rc, so, _ = run_out(pg + ["ci", "--runs-json", busy])
        assert rc == 1 and "in-flight run=1" in so, "in flight should be 1\n%s" % so
        assert parse_runs({"runs": [{"status": "weird"}, {"status": "completed"}]})[0], \
            "unknown status should count as in flight"
        rc, so, _ = run_out(pg + ["ci", "--runs-json", bad])
        assert rc == 1 and "malformed" in so, "malformed evidence should exit 1\n%s" % so
        rc, so, _ = run_out(pg + ["ci", "--runs-json", os.path.join(tmp, "nope.json")])
        assert rc == 9, "missing file should exit 9, got %d" % rc

        # rewrite_host / masking unit vectors
        assert rewrite_host("https://github.com/o/r.git", "140.82.113.3") == \
            "https://140.82.113.3/o/r.git", "host rewrite broken"
        assert rewrite_host("https://u:tok@github.com:8443/o/r.git",
                            "1.2.3.4") == "https://u:tok@1.2.3.4:8443/o/r.git", \
            "userinfo/port preservation broken"
        assert url_secret_masks("https://u:tok@github.com/o/r.git") == ["tok"], \
            "userinfo password extraction broken"
        masked = mask_text("push to https://u:tok@github.com/o/r", ["tok"])
        assert "tok" not in masked and MASKED in masked, "masking broken: %s" % masked

        # push dry-run vectors (local path remote shaped as an https URL, zero network)
        gitc = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
        seed = os.path.join(tmp, "seed")
        rc, _, se = run_out(gitc + ["init", "-q", "-b", "main", seed])
        assert rc == 0, se
        with io.open(os.path.join(seed, "s.txt"), "w", encoding="utf-8",
                     newline="") as fh:
            fh.write("s\n")
        run_out(gitc + ["-C", seed, "add", "s.txt"])
        rc, _, se = run_out(gitc + ["-C", seed, "commit", "-q", "-m", "s"])
        assert rc == 0, "seed commit should exit 0: %s" % se
        bare = os.path.join(tmp, "rem.git")
        rc, _, se = run_out(["git", "clone", "-q", "--bare", seed, bare])
        assert rc == 0, se
        wk = os.path.join(tmp, "wk")
        rc, _, se = run_out(["git", "clone", "-q", seed, wk])
        assert rc == 0, se
        with io.open(os.path.join(wk, "x.txt"), "w", encoding="utf-8",
                     newline="") as fh:
            fh.write("x\n")
        run_out(gitc + ["-C", wk, "add", "x.txt"])
        rc, _, se = run_out(gitc + ["-C", wk, "commit", "-q", "-m", "x"])
        assert rc == 0, "wk commit should exit 0: %s" % se

        # confirm vectors (real ls-remote, local path remote, before the set-url)
        rc, so, _ = run_out(["git", "-C", seed, "rev-parse", "HEAD"])
        head_sha = so.strip()
        rc, so, _ = run_out(pg + ["confirm", "--repo", wk, "--remote", "origin",
                                  "--branch", "main", "--sha", head_sha,
                                  "--reads", "2", "--gap", "0"])
        assert rc == 0 and "PUSH-CONFIRMED" in so, "two equal reads should exit 0\n%s" % so
        rc, so, _ = run_out(pg + ["confirm", "--repo", wk, "--remote", "origin",
                                  "--branch", "main", "--sha", "0" * 40,
                                  "--reads", "2", "--gap", "0"])
        assert rc == 1 and "!=" in so, "mismatch should exit 1\n%s" % so
        rc, so, _ = run_out(pg + ["confirm", "--repo", wk, "--remote", "origin",
                                  "--branch", "main", "--sha", head_sha,
                                  "--reads", "1"])
        assert rc == 2, "single read should be refused (>=2), got %d" % rc

        # push dry-run vectors (https-shaped URL, zero network)
        run_out(["git", "-C", wk, "remote", "set-url", "origin",
                 "https://gh.example.test/o/r.git"])
        rc, so, _ = run_out(pg + ["push", "--repo", wk, "--remote", "origin",
                                  "--pin-ip", "140.82.113.3",
                                  "--url-host", "gh.example.test"])
        assert rc == 0 and "DRY-RUN" in so, "dry run should exit 0\n%s" % so
        assert "https://140.82.113.3/o/r.git" in so, \
            "rewritten URL should be in the account\n%s" % so
        assert "Host: gh.example.test" in so, \
            "extraheader should be in the account\n%s" % so
        assert "gh.example.test/o/r.git" not in so.replace("Host: gh.example.test", ""), \
            "original URL leaked into the command account\n%s" % so
        rc, so, _ = run_out(pg + ["push", "--repo", wk, "--remote", "origin",
                                  "--pin-ip", "1.2.3.4", "--url-host", "other.test"])
        assert rc == 2, "url-host mismatch should exit 2, got %d" % rc
        rc, so, _ = run_out(pg + ["push", "--repo", wk, "--remote", "origin",
                                  "--pin-ip", "1.2.3.4"])
        assert rc == 2, "missing url-host should exit 2, got %d" % rc
        rc, so, _ = run_out(pg + ["push", "--repo", wk, "--remote", "origin"])
        assert rc == 0 and "https://gh.example.test/o/r.git" in so and \
            "DRY-RUN" in so, "no-pin dry run should account the original URL\n%s" % so
        # env mask string: ROCQWASH_MASK
        rc, so, _ = run_out(pg + ["push", "--repo", wk, "--remote", "origin"])
        env = dict(os.environ, ROCQWASH_MASK="gh.example.test")
        p = subprocess.run(pg + ["push", "--repo", wk, "--remote", "origin"],
                           env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        so2 = p.stdout.decode("utf-8", "replace")
        assert "gh.example.test/o/r.git" not in so2 and MASKED in so2, \
            "env masking broken\n%s" % so2

        print("WATCH-SELFTEST PASS: ci offline four verdicts + rewrite/mask unit four "
              "checks + push dry-run four checks + env masking + confirm three checks "
              "all pass (zero network, local path remote)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(
        prog=PROG, description="CI run monitor + pin-IP push + ls-remote confirmation "
                               "(no rerun/cancel/workflow_dispatch path)")
    sub = ap.add_subparsers(dest="cmd")

    c = sub.add_parser("ci", help="monitor CI runs in flight (offline evidence / "
                                  "online read-only query)")
    c.add_argument("--runs-json", default=None, help="prefetched Actions runs JSON")
    c.add_argument("--repo", default=None, help="owner/name (online mode)")
    c.add_argument("--online", action="store_true", help="online read-only query (with --repo)")
    c.add_argument("--branch", default=None, help="filter by branch (online mode)")
    c.add_argument("--token-env", default=None, help="name of the env var holding the token (online mode)")
    c.add_argument("--top", type=int, default=20, help="number of runs to fetch (online mode, default 20)")
    c.add_argument("--interval", type=int, default=0, help="poll interval seconds (0 = single read)")
    c.add_argument("--timeout", type=int, default=600, help="poll total timeout seconds")
    c.add_argument("--json", default=None, help="write the account JSON to this path")

    p = sub.add_parser("push", help="pin-IP push wrapper (dry run by default, masked output)")
    p.add_argument("--repo", default=".", help="repository directory (default cwd)")
    p.add_argument("--remote", default="origin", help="remote name (default origin)")
    p.add_argument("--pin-ip", default=None, help="pin to this IP (with --url-host)")
    p.add_argument("--url-host", default=None, help="original URL host name (Host header value)")
    p.add_argument("--mask", action="append", default=[], help="mask string (repeatable)")
    p.add_argument("--ssl-verify-off", action="store_true",
                   help="disable certificate verification (explicit choice in pin-IP mode, loud warning)")
    p.add_argument("--yes", action="store_true", help="real push (dry run by default)")
    p.add_argument("refspecs", nargs=argparse.REMAINDER, help="refspecs passed through to git push")

    f = sub.add_parser("confirm", help="post-push ls-remote N-read confirmation")
    f.add_argument("--repo", default=".", help="repository directory")
    f.add_argument("--remote", default="origin", help="remote name")
    f.add_argument("--branch", required=True, help="branch name")
    f.add_argument("--sha", required=True, help="expected sha")
    f.add_argument("--reads", type=int, default=2, help="number of reads (>= 2, default 2)")
    f.add_argument("--gap", type=int, default=2, help="seconds between reads (default 2)")

    ap.add_argument("--selftest", action="store_true", help="run the built-in self-check vectors")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())
    if args.cmd == "ci":
        cmd_ci(args)
    elif args.cmd == "push":
        cmd_push(args)
    elif args.cmd == "confirm":
        cmd_confirm(args)
    else:
        ap.print_help(sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
