#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""watch.py — watch 模块首件：CI 监控＋钉 IP 推送＋ls-remote 确证
（rocqwash watch/·20261031 agent rqwash2·承台账第 4 项「CI 监控＋pin-IP 推送＋温控」）

watch 模块三职责，全机械、只读远端、结构性零 route（无 rerun/cancel/
workflow_dispatch 任何代码路径——停手律由结构保证，非口头承诺）：

[一] `ci` — CI 监控（runs 在飞账）：
      离线证据模式  --runs-json <f>     判读预取的 GitHub Actions runs JSON
                                      （私库匿名 API 404 时由调用方预取；本器零网络）；
      在线查询模式  --repo owner/name --online [--branch b] [--token-env VAR]
                                      urllib 只读 GET actions/runs（唯一网络动作＝只读
                                      查询；超时/404/不可达＝FAIL 账面如实记）。
      口径：status!="completed" 一律计在飞（未知状态保守计在飞·fail-closed）；
      active=0 → CI-IDLE exit 0；active>0 或证据不可用 → exit 1；文件缺失 → 9。
      可选 --interval N --timeout S 轮询到 idle（温控：轮询零编译零重负载）。

[二] `push` — 钉 IP 推送包装器（承战役推送员铁律的机械面）：
      watch.py push [--repo dir] [--remote origin] [--pin-ip IP --url-host HOST]
                    [--mask STR]... [--ssl-verify-off] --yes|--dry-run [-- refspecs...]
      - 默认 DRY-RUN：只出将执行命令账（逐参数遮蔽后打印），零网络零执行；
      - --yes 才真推；远端 URL 主机改写为 --pin-ip（保留 scheme/userinfo/port/path），
        加 `-c http.<改写URL>.extraheader=Host: <url-host>`（承战役 extraHeader Host 口径）；
      - 输出遮蔽：stdout/stderr 捕获后把所有 --mask 串＋远端 URL userinfo 密码部
        ＋env ROCQWASH_MASK（冒号分隔）替换为 ***MASKED*** 再出账；
      - TLS 注记：按 IP 连接时不发 SNI，证书主机名核验可能失败——
        --ssl-verify-off 须显式给（账面响亮警告），默认不动 sslVerify（诚实优先）；
      - 退出码＝git push 退出码透传（DRY-RUN=0）。

[三] `confirm` — 推送后 ls-remote N 读确证（承「真 rc＋ls-remote 复核」纪律）：
      watch.py confirm [--repo dir] --remote origin --branch main --sha <sha>
                       [--reads 2 --gap 2]
      N 读（N≥2·默认 2）全等 --sha → PUSH-CONFIRMED exit 0；任一异 → exit 1 逐读出账。

诚实律（承 CONTRIBUTING §0）：只认机械证据；NOT-RUN/NETWORK-UNREACHABLE 显式出账
不计绿；fail-loud；本器自身零编译零队列——一切编译仍必经冻结件
tools/cpu_guard.sh 温控包裹（本模块不代包、不代跑编译）。

写域声明：本器不写仓库树、不写外部沙箱；push 仅在 --yes 下执行调用方显式指认的
git push（dry-run 默认）。依赖 Python ≥3.9 纯标准库＋git 在 PATH。

用法：
  python3 watch/watch.py ci --runs-json f [--interval N --timeout S] [--json out]
  python3 watch/watch.py ci --repo owner/name --online [--branch b] [--token-env VAR]
  python3 watch/watch.py push [选项] --yes|--dry-run [-- refspecs...]
  python3 watch/watch.py confirm --remote origin --branch main --sha <sha> [选项]
  python3 watch/watch.py --selftest

退出码：ci 0=idle／1=在飞>0 或证据不可用／2=用法错／9=文件缺失；
push 0=DRY-RUN／其余＝git push rc 透传／2=用法错／9=远端缺失；
confirm 0=CONFIRMED／1=不一致／2=用法错／9=远端缺失；--selftest 0／2。
"""
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
ACTIVE_NOTE = "status!=%s 保守计在飞" % CI_DONE


def run_out(argv, cwd=None):
    p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def git(repo, *args):
    return run_out(["git", "-C", repo] + list(args))


def mask_text(s, masks):
    """把 masks 中每串替换为 ***MASKED***（空串忽略）。"""
    for m in masks:
        if m:
            s = s.replace(m, MASKED)
    return s


def rewrite_host(url, ip):
    """URL 主机改写为 ip（保留 scheme/userinfo/port/path）。非 http(s) fail-loud。"""
    rest = None
    for sch in ("https://", "http://"):
        if url.startswith(sch):
            rest = url[len(sch):]
            break
    if rest is None:
        raise ValueError("钉 IP 仅支持 http(s) 远端，实测 %r" % url)
    authority, _, path = rest.partition("/")
    userinfo = ""
    if "@" in authority:
        userinfo, _, authority = authority.rpartition("@")
    host_port = authority
    new_authority = ip if host_port == host_port.rstrip(":0123456789") else None
    if ":" in host_port:  # 带 port
        h, _, p = host_port.partition(":")
        new_authority = "%s:%s" % (ip, p)
    if new_authority is None:
        new_authority = ip
    head = "%s%s%s" % (url[:len(sch)], (userinfo + "@") if userinfo else "",
                       new_authority)
    return head + "/" + path if path or "/" in rest else head


def url_secret_masks(url):
    """远端 URL 内嵌凭据（userinfo 密码部）→ 遮蔽串清单。"""
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
    """runs JSON → (active, total)。畸形 raise ValueError。"""
    runs = doc["runs"]
    if not isinstance(runs, list):
        raise ValueError("runs 非列表")
    active = [(r.get("name", "?"), r.get("status", "?"))
              for r in runs if r.get("status") != CI_DONE]
    return active, len(runs)


# ---------------- [一] ci ----------------

def cmd_ci(args):
    if args.runs_json:
        if not os.path.isfile(args.runs_json):
            print("FAIL-LOUD: runs-json 缺失: %s" % args.runs_json, file=sys.stderr)
            sys.exit(9)
        deadline = time.time() + args.timeout
        while True:
            try:
                with io.open(args.runs_json, encoding="utf-8") as fh:
                    active, total = parse_runs(json.load(fh))
            except Exception as e:
                print("ci FAIL: runs-json 畸形（不可采信）: %s" % e)
                sys.exit(1)
            verdict = _ci_verdict(active, total, "runs-json 实证")
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
            print("ci FAIL: NETWORK-UNREACHABLE（只读查询未达）: %s" % e)
            print("  （私库匿名 404 属预期——改用 --runs-json 预取证据模式）")
            sys.exit(1)
        verdict = _ci_verdict(active, total, "api.github.com 只读查询")
        sys.exit(0 if verdict else 1)
    print("FAIL-LOUD: ci 需 --runs-json <f>（离线证据）或 --repo owner/name --online（在线查询）",
          file=sys.stderr)
    sys.exit(2)


def _ci_verdict(active, total, source):
    if active:
        print("ci ACTIVE: 在飞 run=%d（%s·%s）: %s" % (
            len(active), source, ACTIVE_NOTE,
            ", ".join("%s/%s" % x for x in active[:5])))
        print("ci: exit 1（在飞未清——push 窗判据①未坐实）")
        return False
    print("ci CI-IDLE: 在飞=0（%s·共 %d 条·全 %s）" % (source, total, CI_DONE))
    print("ci: exit 0")
    return True


# ---------------- [二] push ----------------

def collect_masks(args, url):
    masks = list(args.mask)
    masks += url_secret_masks(url)
    env_masks = os.environ.get("ROCQWASH_MASK", "")
    masks += [m for m in env_masks.split(":") if m]
    return masks


def build_push_cmd(args, repo):
    rc, so, se = git(repo, "remote", "get-url", "--push", args.remote)
    if rc != 0:
        print("FAIL-LOUD: 远端缺失: %s（%s）" % (args.remote, se.strip()[:120]),
              file=sys.stderr)
        sys.exit(9)
    url = so.strip()
    masks = collect_masks(args, url)
    cmd = ["git", "-C", repo]
    if args.pin_ip:
        if not args.url_host:
            print("FAIL-LOUD: --pin-ip 需配对 --url-host", file=sys.stderr)
            sys.exit(2)
        if args.url_host not in url:
            print("FAIL-LOUD: --url-host %r 不在远端 URL 中: %s"
                  % (args.url_host, mask_text(url, masks)), file=sys.stderr)
            sys.exit(2)
        rewritten = rewrite_host(url, args.pin_ip)
        cmd += ["-c", "http.%s.extraheader=Host: %s" % (rewritten, args.url_host)]
        if args.ssl_verify_off:
            cmd += ["-c", "http.sslVerify=false"]
        target = rewritten
    else:
        if args.ssl_verify_off:
            print("FAIL-LOUD: --ssl-verify-off 仅限钉 IP 模式（非钉 IP 不动 sslVerify）",
                  file=sys.stderr)
            sys.exit(2)
        target = url
    cmd += ["push", target] + args.refspecs
    return cmd, masks, url, target


def cmd_push(args):
    repo = os.path.abspath(args.repo)
    if not os.path.isdir(repo):
        print("FAIL-LOUD: 仓库目录缺失: %s" % repo, file=sys.stderr)
        sys.exit(9)
    cmd, masks, url, target = build_push_cmd(args, repo)
    shown = " ".join(mask_text(part, masks) for part in cmd)
    if not args.yes:
        print("push DRY-RUN（默认·零网络零执行）——将执行：")
        print("  " + shown)
        print("push: exit 0（--yes 才真推；推后请跑 confirm 做 ls-remote N 读确证）")
        sys.exit(0)
    if args.ssl_verify_off:
        print("[watch] 警告：--ssl-verify-off 生效（证书主机名核验关闭·钉 IP 模式显式选择）")
    rc, so, se = run_out(cmd)
    out = mask_text(so + se, masks)
    if out.strip():
        print(out.rstrip())
    print("push rc=%d target=%s" % (rc, mask_text(target, masks)))
    print("push: exit %d（请跑 confirm --sha <推送后 sha> 做 ls-remote N 读确证）" % rc)
    sys.exit(rc)


# ---------------- [三] confirm ----------------

def cmd_confirm(args):
    repo = os.path.abspath(args.repo)
    if not os.path.isdir(repo):
        print("FAIL-LOUD: 仓库目录缺失: %s" % repo, file=sys.stderr)
        sys.exit(9)
    if args.reads < 2:
        print("FAIL-LOUD: --reads 须 ≥2（双读确证是纪律下限）", file=sys.stderr)
        sys.exit(2)
    if not args.sha:
        print("FAIL-LOUD: confirm 需 --sha <期望 sha>", file=sys.stderr)
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
        print("PUSH-CONFIRMED: %d 读全等 %s（origin/%s 已坐实）" % (args.reads, args.sha[:12], args.branch))
        sys.exit(0)
    print("confirm FAIL: %d 读不齐（期望 %s·实测 %s）" % (
        args.reads, args.sha[:12], ",".join(s[:12] for s in seen)))
    sys.exit(1)


# ---------------- 自证（冻结向量组·零网络零仓库写） ----------------

def selftest():
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_watch_self_")
    try:
        pg = [sys.executable, "-B", os.path.abspath(__file__)]

        # —— ci 离线证据向量 ——
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
        assert rc == 0 and "CI-IDLE" in so and "在飞=0" in so, "idle 应 0\n%s" % so
        rc, so, _ = run_out(pg + ["ci", "--runs-json", busy])
        assert rc == 1 and "在飞 run=1" in so, "在飞应 1\n%s" % so
        assert parse_runs({"runs": [{"status": "weird"}, {"status": "completed"}]})[0], \
            "未知状态应保守计在飞"
        rc, so, _ = run_out(pg + ["ci", "--runs-json", bad])
        assert rc == 1 and "畸形" in so, "畸形证据应 1\n%s" % so
        rc, so, _ = run_out(pg + ["ci", "--runs-json", os.path.join(tmp, "nope.json")])
        assert rc == 9, "缺文件应 9 实测 %d" % rc

        # —— rewrite_host / 遮蔽单元向量 ——
        assert rewrite_host("https://github.com/o/r.git", "140.82.113.3") == \
            "https://140.82.113.3/o/r.git", "主机改写失守"
        assert rewrite_host("https://u:tok@github.com:8443/o/r.git",
                            "1.2.3.4") == "https://u:tok@1.2.3.4:8443/o/r.git", \
            "userinfo/port 保留失守"
        assert url_secret_masks("https://u:tok@github.com/o/r.git") == ["tok"], \
            "userinfo 密码部提取失守"
        masked = mask_text("push to https://u:tok@github.com/o/r", ["tok"])
        assert "tok" not in masked and MASKED in masked, "遮蔽失守: %s" % masked

        # —— push 干跑向量（本地 path 远端造 https 形 URL·零网络） ——
        gitc = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
        seed = os.path.join(tmp, "seed")
        rc, _, se = run_out(gitc + ["init", "-q", "-b", "main", seed])
        assert rc == 0, se
        with io.open(os.path.join(seed, "s.txt"), "w", encoding="utf-8",
                     newline="") as fh:
            fh.write("s\n")
        run_out(gitc + ["-C", seed, "add", "s.txt"])
        rc, _, se = run_out(gitc + ["-C", seed, "commit", "-q", "-m", "s"])
        assert rc == 0, "seed commit 应 0: %s" % se
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
        assert rc == 0, "wk commit 应 0: %s" % se

        # —— confirm 向量（真 ls-remote·本地 path 远端·在 set-url 之前） ——
        rc, so, _ = run_out(["git", "-C", seed, "rev-parse", "HEAD"])
        head_sha = so.strip()
        rc, so, _ = run_out(pg + ["confirm", "--repo", wk, "--remote", "origin",
                                  "--branch", "main", "--sha", head_sha,
                                  "--reads", "2", "--gap", "0"])
        assert rc == 0 and "PUSH-CONFIRMED" in so, "双读全等应 0\n%s" % so
        rc, so, _ = run_out(pg + ["confirm", "--repo", wk, "--remote", "origin",
                                  "--branch", "main", "--sha", "0" * 40,
                                  "--reads", "2", "--gap", "0"])
        assert rc == 1 and "!=" in so, "不一致应 1\n%s" % so
        rc, so, _ = run_out(pg + ["confirm", "--repo", wk, "--remote", "origin",
                                  "--branch", "main", "--sha", head_sha,
                                  "--reads", "1"])
        assert rc == 2, "单读应拒（≥2）实测 %d" % rc

        # —— push 干跑向量（换 https 形 URL·零网络） ——
        run_out(["git", "-C", wk, "remote", "set-url", "origin",
                 "https://gh.example.test/o/r.git"])
        rc, so, _ = run_out(pg + ["push", "--repo", wk, "--remote", "origin",
                                  "--pin-ip", "140.82.113.3",
                                  "--url-host", "gh.example.test"])
        assert rc == 0 and "DRY-RUN" in so, "干跑应 0\n%s" % so
        assert "https://140.82.113.3/o/r.git" in so, "改写 URL 应入账\n%s" % so
        assert "Host: gh.example.test" in so, "extraheader 应入账\n%s" % so
        assert "gh.example.test/o/r.git" not in so.replace("Host: gh.example.test", ""), \
            "原 URL 泄漏进命令账\n%s" % so
        rc, so, _ = run_out(pg + ["push", "--repo", wk, "--remote", "origin",
                                  "--pin-ip", "1.2.3.4", "--url-host", "other.test"])
        assert rc == 2, "url-host 不符应 2 实测 %d" % rc
        rc, so, _ = run_out(pg + ["push", "--repo", wk, "--remote", "origin",
                                  "--pin-ip", "1.2.3.4"])
        assert rc == 2, "缺 url-host 应 2 实测 %d" % rc
        rc, so, _ = run_out(pg + ["push", "--repo", wk, "--remote", "origin"])
        assert rc == 0 and "https://gh.example.test/o/r.git" in so and \
            "DRY-RUN" in so, "无钉 IP 干跑应原样出账\n%s" % so
        # 环境遮蔽串：ROCQWASH_MASK
        rc, so, _ = run_out(pg + ["push", "--repo", wk, "--remote", "origin"])
        env = dict(os.environ, ROCQWASH_MASK="gh.example.test")
        p = subprocess.run(pg + ["push", "--repo", wk, "--remote", "origin"],
                           env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        so2 = p.stdout.decode("utf-8", "replace")
        assert "gh.example.test/o/r.git" not in so2 and MASKED in so2, \
            "env 遮蔽失守\n%s" % so2

        print("WATCH-SELFTEST PASS: ci 离线四判＋rewrite/mask 单元四判＋push 干跑四判"
              "＋env 遮蔽＋confirm 三判全过（零网络·本地 path 远端）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(
        prog=PROG, description="CI 监控＋钉 IP 推送＋ls-remote 确证（零 dispatch）")
    sub = ap.add_subparsers(dest="cmd")

    c = sub.add_parser("ci", help="CI runs 在飞监控（离线证据/在线只读查询）")
    c.add_argument("--runs-json", default=None, help="预取的 Actions runs JSON")
    c.add_argument("--repo", default=None, help="owner/name（在线模式）")
    c.add_argument("--online", action="store_true", help="在线只读查询（配 --repo）")
    c.add_argument("--branch", default=None, help="过滤分支（在线模式）")
    c.add_argument("--token-env", default=None, help="token 所在环境变量名（在线模式）")
    c.add_argument("--top", type=int, default=20, help="拉取条数（在线模式·默认 20）")
    c.add_argument("--interval", type=int, default=0, help="轮询间隔秒（0=单读）")
    c.add_argument("--timeout", type=int, default=600, help="轮询总时限秒")
    c.add_argument("--json", default=None, help="账目 JSON 出账路径")

    p = sub.add_parser("push", help="钉 IP 推送包装器（默认干跑·输出遮蔽）")
    p.add_argument("--repo", default=".", help="仓库目录（默认 cwd）")
    p.add_argument("--remote", default="origin", help="远端名（默认 origin）")
    p.add_argument("--pin-ip", default=None, help="钉 IP（配 --url-host）")
    p.add_argument("--url-host", default=None, help="原 URL 主机名（Host 头值）")
    p.add_argument("--mask", action="append", default=[], help="遮蔽串（可重复）")
    p.add_argument("--ssl-verify-off", action="store_true",
                   help="关证书核验（钉 IP 模式显式选择·账面警告）")
    p.add_argument("--yes", action="store_true", help="真推（默认干跑）")
    p.add_argument("refspecs", nargs=argparse.REMAINDER, help="git push 透传 refspecs")

    f = sub.add_parser("confirm", help="推送后 ls-remote N 读确证")
    f.add_argument("--repo", default=".", help="仓库目录")
    f.add_argument("--remote", default="origin", help="远端名")
    f.add_argument("--branch", required=True, help="分支名")
    f.add_argument("--sha", required=True, help="期望 sha")
    f.add_argument("--reads", type=int, default=2, help="读数（≥2·默认 2）")
    f.add_argument("--gap", type=int, default=2, help="读间隔秒（默认 2）")

    ap.add_argument("--selftest", action="store_true", help="冻结向量组自证")
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
