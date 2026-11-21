#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""push_gate.py — certify 深件：推送窗四判据机检＋UNION v2 多世界清单
（rocqwash certify/·20261031 席 rqwash2·与冻结件 freeze_manifest.py v1 并存）

certify 模块第二件（v2 接口并存·冻结件零改动）。两块职责：

[一] `window` — 推送窗四判据（承战役推送窗铁律的机械落地：
     参照 ConstructiveWorld 战役 wf_land.dwf.ts:40「推送窗四判据：
     ①runs in_progress=0 ②本地≥云端 ③fetch 干净 ④认证绿已坐实」）：

      c1 ci-idle    CI 在飞 run=0。证据源任择其一（无证据=NOT-RUN=窗不开·fail-closed）：
                      --runs-json <f>   预取的 GitHub Actions runs JSON（本工具自身零网络：
                                        匿名 404 私库不可达时由调用方预取，本器只做机械判读——
                                        status!="completed" 一律计在飞·未知状态保守计在飞）；
                      --ci-capped-min N 时间线证据：remote-tracking reflog 最近一条
                                        `update by push` 距今 ≥ N 分钟＋CI 时长封顶（ci.yml
                                        timeout-minutes）⇒ 在飞 run 不可能存在（承更新账 §五判例）。
      c2 local≥remote  fetch 后 `rev-list --count HEAD..<remote>/<branch>`（behind）==0
                      （ahead 不设上限——本地领先正是待推状态）。
      c3 fetch-clean  ls-remote 前后双读同 sha ＋ fetch rc=0 ＋ 远端 sha 是本地 HEAD
                      祖先（merge-base --is-ancestor）。窗内无人动云端才算干净；
                      fetch 失败（含网络死窗）＝FAIL——推不动也判不出，窗如实关。
      c4 cert-green   本仓认证绿机械复核：bash tests/run_tests.sh rc==0（--suite 可指认
                      他脚本）；可另加 --freeze-manifest <m.json> → 冻结件 freeze_manifest.py
                      check 零漂移亦须 rc==0。任一红＝FAIL。

      账面：逐判据 PASS/FAIL/NOT-RUN 行＋总结论 `push-window: OPEN|CLOSED`；
      OPEN（四判据全 PASS）exit 0，否则 exit 1（NOT-RUN=关窗·诚实律：缺席旁证不计绿）。
      本器只判窗不开推——push 动作在调用方（钉 IP 推送见 watch/watch.py push）。

[二] `union-freeze` / `union-check` — UNION v2 多世界清单（freeze_manifest v1 的
     多世界泛化·schema rocqwash-union-manifest/2）：

      tier1 逐文件 md5 与 tier2（=tier1 账文 md5）逐字承 v1 冻结口径（import
      freeze_manifest 的 tier1_lines/tier2_of 只读复用——冻结件零改动）；在此之上
      增第三层：world 层 tier2 逐世界入账，union 层 union_tier2 = 逐世界
      `name  tier2\n` 行账文的 md5——任一世界的 tier1/tier2 被改，union 层即现形。
      --tier2 侧册把 union_tier2 落盘外置（v1 同款两层冻结语义：动清单即发现）。
      check 逐世界三分对账（changed/added/removed）＋逐世界 tier2＋union 层＋可选
      侧册四方咬合；零漂移 exit 0、有漂移 exit 1、清单畸形 exit 2。

诚实律（承 CONTRIBUTING §0，一票否决）：
  - 只认机械证据（退出码/md5/count），不出口头判词；
  - NOT-RUN 显式出账且不计绿，禁把缺席证据标成 PASS；
  - fail-loud：证据畸形/路径缺失一律非零＋响亮输出；
  - 幂等可重放：union-freeze 无时间戳无环境噪声，同盘面重产逐字节恒同。

写域声明：本器只写调用方显式指认的 --out/--tier2/--json 出路径，不碰仓库树、
不碰外部沙箱；window 全程只读（fetch/ls-remote 均为远端只读操作）。

依赖：Python ≥3.9 纯标准库＋git 在 PATH；冻结同侪 freeze_manifest.py 在场。
一切涉编译的调用（如 --suite 命中的套件内编译段）必经 tools/cpu_guard.sh 温控包裹
——本器自身零编译，套件内的 cpu_guard -Direct 冒烟例自带包裹。

用法：
  python3 certify/push_gate.py window --repo <dir> [--branch B] [--remote origin]
        [--runs-json f | --ci-capped-min N] [--freeze-manifest m.json]
        [--suite <path>] [--json out.json]
  python3 certify/push_gate.py union-freeze --world name=path [--world name=path ...]
        --out union.json [--tier2 t2.md5]
  python3 certify/push_gate.py union-check --manifest union.json [--tier2 t2.md5] [--json out]
  python3 certify/push_gate.py --selftest

退出码：window 0=OPEN／1=CLOSED（含 NOT-RUN）／2=用法错／9=路径缺失；
union-freeze 0=成／2=用法错／9=世界根缺失；union-check 0=零漂移／1=有漂移／
2=清单畸形／9=清单或侧册缺失；--selftest 0=全过／2=向量失败。
"""
import argparse
import io
import json
import os
import subprocess
import sys

PROG = "push_gate"
UNION_SCHEMA = "rocqwash-union-manifest/2"

# 与冻结 v1 同侪只读复用（tier1_lines/tier2_of 承冻结口径·本文件零改动传递）
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
try:
    import freeze_manifest as _v1  # noqa: E402  （冻结件·只 import 不改）
except Exception as _e:  # pragma: no cover
    print("FAIL-LOUD: 冻结同侪 certify/freeze_manifest.py 不可导入: %s" % _e,
          file=sys.stderr)
    sys.exit(9)

# CI runs JSON 里视为「不在飞」的唯一终态；其余一切状态保守计在飞（fail-closed）
CI_DONE = "completed"


def run_out(argv, cwd=None):
    """子进程跑一条命令→(rc, stdout, stderr)。零外壳注入（argv 直传）。"""
    p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def git(repo, *args):
    return run_out(["git", "-C", repo] + list(args))


# ---------------- [一] 推送窗四判据 ----------------

def c1_ci_idle(args, repo, branch_full):
    """判据①：CI 在飞 run=0。返回 (verdict, detail)。verdict∈PASS/FAIL/NOT-RUN。"""
    if args.runs_json:
        if not os.path.isfile(args.runs_json):
            return "FAIL", "runs-json 缺失: %s" % args.runs_json
        try:
            with io.open(args.runs_json, encoding="utf-8") as fh:
                doc = json.load(fh)
            runs = doc["runs"]
            if not isinstance(runs, list):
                raise ValueError("runs 非列表")
        except Exception as e:
            return "FAIL", "runs-json 畸形（不可采信）: %s" % e
        active = [(r.get("name", "?"), r.get("status", "?"))
                  for r in runs if r.get("status") != CI_DONE]
        if active:
            return "FAIL", ("在飞 run=%d（status!=%s 保守计在飞）: %s"
                            % (len(active), CI_DONE,
                               ", ".join("%s/%s" % x for x in active[:5])))
        return "PASS", "runs-json 实证在飞=0（共 %d 条·全 %s）" % (len(runs), CI_DONE)
    if args.ci_capped_min is not None:
        rc, so, _ = git(repo, "log", "-g", "--format=%ct|%gs", branch_full)
        if rc != 0:
            return "NOT-RUN", ("reflog 不可读（rc=%d）——时间线证据缺席" % rc)
        push_ts = None
        for line in so.splitlines():
            if "|" not in line:
                continue
            ts, _, subject = line.partition("|")
            if "update by push" in subject:
                push_ts = ts.strip()
                break  # log -g 新→旧·首中即最近一次本机推送
        if push_ts is None:
            return "NOT-RUN", "reflog 无 `update by push` 条目——本机推送时间线缺席"
        import time
        age_min = (time.time() - float(push_ts)) / 60.0
        if age_min >= args.ci_capped_min:
            return "PASS", ("最近本机推送距今 %.1f 分钟 ≥ 封顶窗 %d 分钟——在飞 run "
                            "不可能存在（时间线证据·ci.yml timeout 封顶）"
                            % (age_min, args.ci_capped_min))
        return "NOT-RUN", ("最近本机推送距今 %.1f 分钟 < 封顶窗 %d 分钟——可能仍在飞"
                           % (age_min, args.ci_capped_min))
    return "NOT-RUN", "无证据源（--runs-json / --ci-capped-min 均未给）"


def c2_local_ge_remote(repo, remote_branch):
    """判据②：本地≥云端（fetch 后 behind==0）。"""
    rc, so, se = git(repo, "rev-list", "--count", "HEAD..%s" % remote_branch)
    if rc != 0:
        return "FAIL", "rev-list behind 计数失败: %s" % se.strip()[:120]
    behind = int(so.strip() or "0")
    rc2, so2, _ = git(repo, "rev-list", "--count", "%s..HEAD" % remote_branch)
    ahead = int(so2.strip() or "0") if rc2 == 0 else -1
    if behind != 0:
        return "FAIL", "behind=%d（云端有本地缺的 commit——本地<云端）·ahead=%s" % (
            behind, ahead)
    return "PASS", "behind=0 ahead=%s（本地≥云端）" % ahead


def c3_fetch_clean(repo, remote, branch, remote_branch):
    """判据③：fetch 干净——ls-remote 前后双读同 sha＋fetch 成＋远端 sha 为 HEAD 祖先。"""
    rc, so, se = git(repo, "ls-remote", remote, "refs/heads/%s" % branch)
    if rc != 0 or not so.strip():
        return "FAIL", "ls-remote 前读失败（网络/远端缺枝）: %s" % se.strip()[:120]
    sha_before = so.split()[0]
    rc, so, se = git(repo, "fetch", "--quiet", remote)
    if rc != 0:
        return "FAIL", "fetch 失败: %s" % se.strip()[:120]
    rc, so, se = git(repo, "ls-remote", remote, "refs/heads/%s" % branch)
    if rc != 0 or not so.strip():
        return "FAIL", "ls-remote 后读失败: %s" % se.strip()[:120]
    sha_after = so.split()[0]
    if sha_before != sha_after:
        return "FAIL", ("窗内云端移动 %s..%s——有人推过，窗脏"
                        % (sha_before[:8], sha_after[:8]))
    grc, _, _ = git(repo, "merge-base", "--is-ancestor", sha_after, "HEAD")
    if grc != 0:
        return "FAIL", "远端 sha %s 非本地 HEAD 祖先（本地缺远端 commit）" % sha_after[:8]
    return "PASS", "双读同 %s·fetch rc=0·远端为 HEAD 祖先（窗内无人动）" % sha_after[:8]


def c4_cert_green(args, repo, here):
    """判据④：认证绿已坐实——套件 rc==0（必检）＋冻结清单零漂移（可选）。"""
    suite = args.suite or os.path.join(repo, "tests", "run_tests.sh")
    if not os.path.isfile(suite):
        return "FAIL", "认证套件缺失: %s（--suite 可指认）" % suite
    rc, so, se = run_out(["bash", suite], cwd=repo)
    if rc != 0:
        tail = (so + se).strip().splitlines()
        return "FAIL", "套件 rc=%d: %s" % (rc, tail[-1][:120] if tail else "(无输出)")
    line = ""
    for ln in so.splitlines():
        if ln.startswith("== 汇总"):
            line = ln.strip()
    if args.freeze_manifest:
        fz = os.path.join(here, "freeze_manifest.py")
        rc2, so2, se2 = run_out([sys.executable, "-B", fz, "check", repo,
                                 "--manifest", args.freeze_manifest])
        if rc2 != 0:
            tail = (so2 + se2).strip().splitlines()
            return "FAIL", ("冻结清单 check rc=%d（有漂移/畸形）: %s"
                            % (rc2, tail[-1][:120] if tail else "(无输出)"))
        return "PASS", "套件 %s ＋冻结清单零漂移" % (line or "rc=0")
    return "PASS", "套件 %s（未给 --freeze-manifest·冻结对账段未跑）" % (line or "rc=0")


def cmd_window(args, here):
    if not os.path.isdir(args.repo):
        print("FAIL-LOUD: 仓库目录缺失: %s" % args.repo, file=sys.stderr)
        sys.exit(9)
    if args.runs_json and args.ci_capped_min is not None:
        print("FAIL-LOUD: --runs-json 与 --ci-capped-min 互斥（单证据源判读）",
              file=sys.stderr)
        sys.exit(2)
    repo = os.path.abspath(args.repo)
    branch = args.branch
    if not branch:
        rc, so, se = git(repo, "symbolic-ref", "--short", "HEAD")
        if rc != 0:
            print("FAIL-LOUD: 不能解析当前分支（detached HEAD?）: %s" % se.strip()[:120],
                  file=sys.stderr)
            sys.exit(9)
        branch = so.strip()
    remote_branch = "%s/%s" % (args.remote, branch)
    branch_full = "refs/remotes/%s" % remote_branch

    # c3 先行（fetch 落定 remote-tracking ref，c1 时间线证据/c2 计数方有据）
    c3_v, c3_d = c3_fetch_clean(repo, args.remote, branch, remote_branch)
    c1_v, c1_d = c1_ci_idle(args, repo, branch_full)
    c2_v, c2_d = c2_local_ge_remote(repo, remote_branch)
    c4_v, c4_d = c4_cert_green(args, repo, here)

    rows = [("c1 ci-idle", c1_v, c1_d), ("c2 local>=remote", c2_v, c2_d),
            ("c3 fetch-clean", c3_v, c3_d), ("c4 cert-green", c4_v, c4_d)]
    for name, v, d in rows:
        print("  %-18s %-7s %s" % (name, v, d))
    open_ = all(v == "PASS" for _, v, _ in rows)
    print("push-window: %s" % ("OPEN（四判据全 PASS）" if open_ else
                               "CLOSED（%s）" % "；".join(
                                   "%s=%s" % (n.split()[0], v)
                                   for n, v, _ in rows if v != "PASS")))
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"repo": repo, "branch": branch, "remote": args.remote,
                       "criteria": [{"name": n, "verdict": v, "detail": d}
                                    for n, v, d in rows],
                       "verdict": "OPEN" if open_ else "CLOSED"},
                      fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)
    sys.exit(0 if open_ else 1)


# ---------------- [二] UNION v2 多世界清单 ----------------

def union_tier2_of(worlds):
    """union 层：逐世界 `name  tier2\n` 行账文（按世界名排序）的 md5。"""
    text = "".join("%s  %s\n" % (w["name"], w["tier2"])
                   for w in sorted(worlds, key=lambda w: w["name"]))
    return _v1.md5_bytes(text.encode("utf-8"))


def cmd_union_freeze(args):
    if not args.world:
        print("FAIL-LOUD: union-freeze 需至少一个 --world name=path", file=sys.stderr)
        sys.exit(2)
    if not args.out:
        print("FAIL-LOUD: union-freeze 需 --out 清单出路径", file=sys.stderr)
        sys.exit(2)
    worlds = []
    seen = set()
    for spec in args.world:
        name, _, path = spec.partition("=")
        if not name or not path:
            print("FAIL-LOUD: --world 形制须 name=path，实测 %r" % spec, file=sys.stderr)
            sys.exit(2)
        if name in seen:
            print("FAIL-LOUD: 世界名重复: %s" % name, file=sys.stderr)
            sys.exit(2)
        seen.add(name)
        if not os.path.isdir(path):
            print("FAIL-LOUD: 世界根缺失: %s (=%s)" % (name, path), file=sys.stderr)
            sys.exit(9)
        rows = _v1.tier1_lines(path)
        worlds.append({"name": name, "root": os.path.abspath(path),
                       "n_files": len(rows),
                       "tier1": [[r, m] for r, m in rows],
                       "tier2": _v1.tier2_of(rows)})
    worlds.sort(key=lambda w: w["name"])
    u2 = union_tier2_of(worlds)
    doc = {"schema": UNION_SCHEMA, "worlds": worlds, "union_tier2": u2,
           "n_worlds": len(worlds)}
    for path in ([args.out] + ([args.tier2] if args.tier2 else [])):
        parent = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(parent):
            print("FAIL-LOUD: 出路径父目录缺失: %s" % parent, file=sys.stderr)
            sys.exit(2)
    with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    for w in worlds:
        print("  world %-12s n=%-4d tier2=%s" % (w["name"], w["n_files"], w["tier2"]))
    print("union-freeze OK: %d 世界入账 -> %s" % (len(worlds), args.out))
    print("union_tier2=%s（逐世界 tier2 行账文的 md5·第三层）" % u2)
    if args.tier2:
        with io.open(args.tier2, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(u2 + "\n")
        print("union_tier2 侧册 ->", args.tier2)
    # 幂等自证：重产与在盘逐字节对照
    with io.open(args.out, encoding="utf-8", newline="") as fh:
        first = fh.read()
    again = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    assert first == again, "union-freeze 幂等自证失败（清单非确定性）"
    print("idempotent replay: 清单重产逐字节恒同 PASS")
    sys.exit(0)


def cmd_union_check(args):
    if not args.manifest:
        print("FAIL-LOUD: union-check 需 --manifest 在册清单", file=sys.stderr)
        sys.exit(2)
    if not os.path.isfile(args.manifest):
        print("FAIL-LOUD: 清单缺失: %s" % args.manifest, file=sys.stderr)
        sys.exit(9)
    if args.tier2 and not os.path.isfile(args.tier2):
        print("FAIL-LOUD: 侧册缺失: %s" % args.tier2, file=sys.stderr)
        sys.exit(9)
    try:
        with io.open(args.manifest, encoding="utf-8") as fh:
            doc = json.load(fh)
        if doc.get("schema") != UNION_SCHEMA:
            raise ValueError("schema 不识: %r（期望 %s）" % (doc.get("schema"),
                                                           UNION_SCHEMA))
        worlds = doc["worlds"]
        if not isinstance(worlds, list) or not worlds:
            raise ValueError("worlds 非非空列表")
    except Exception as e:
        print("FAIL-LOUD: 清单畸形: %s" % e, file=sys.stderr)
        sys.exit(2)

    drift = False
    # 侧册先验（最强：清单在盘者改 union_tier2 也现形）
    side_ok = True
    if args.tier2:
        with io.open(args.tier2, encoding="utf-8") as fh:
            side = fh.read().strip()
        side_ok = (side == doc.get("union_tier2"))
        print("union_tier2 侧册咬合: %s" % ("PASS" if side_ok else "FAIL"))
        drift = drift or not side_ok
    # 逐世界对账
    total = {"changed": 0, "added": 0, "removed": 0}
    for w in doc["worlds"]:
        name = w.get("name", "?")
        root = w.get("root", "")
        if not os.path.isdir(root):
            print("  world %-12s ROOT-MISSING %s" % (name, root))
            drift = True
            continue
        now = dict(_v1.tier1_lines(root))
        base = {r: m for r, m in w.get("tier1", [])}
        changed = sorted(r for r, m in now.items() if r in base and base[r] != m)
        added = sorted(r for r in now if r not in base)
        removed = sorted(r for r in base if r not in now)
        for label, lst in (("changed", changed), ("added", added), ("removed", removed)):
            for r in lst:
                print("  world %-12s DRIFT %-8s %s" % (name, label, r))
        t2_now = _v1.tier2_of([tuple(x) for x in w.get("tier1", [])])
        t2_ok = (t2_now == w.get("tier2"))
        print("  world %-12s tier2 %s · %d changed / %d added / %d removed"
              % (name, "PASS" if t2_ok else "FAIL",
                 len(changed), len(added), len(removed)))
        drift = drift or bool(changed or added or removed or not t2_ok)
        for k in total:
            total[k] += len(dict(changed=changed, added=added, removed=removed)[k])
    # union 层先验
    u2_now = union_tier2_of(doc["worlds"])
    u_ok = (u2_now == doc.get("union_tier2"))
    print("union_tier2 层自洽: %s" % ("PASS" if u_ok else "FAIL"))
    drift = drift or not u_ok
    print("union-check %s: %d 世界 · %d changed / %d added / %d removed"
          % ("FAIL" if drift else "OK", len(doc["worlds"]),
             total["changed"], total["added"], total["removed"]))
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"manifest": args.manifest, "side_tier2_ok": side_ok,
                       "union_ok": u_ok, "drift": drift, "totals": total},
                      fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)
    sys.exit(1 if drift else 0)


# ---------------- 自证（冻结向量组·零网络零仓库写） ----------------

def selftest():
    """向量组：UNION 幂等/零漂移/漂移/tier1 篡改/union 层篡改/侧册；
    window c1 双源＋c2 behind＋c4 红套件＋本地 path 远端全判据开窗。"""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_pushgate_self_")
    try:
        gitc = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]

        def w(rel, content):
            with io.open(os.path.join(tmp, rel), "w", encoding="utf-8",
                         newline="") as fh:
                fh.write(content)

        # —— UNION v2 向量 ——
        for d in ("wa", "wb/sub"):
            os.makedirs(os.path.join(tmp, d))
        w("wa/a.v", "Lemma a : True.\n")
        w("wb/sub/b.v", "Lemma b : True.\n")
        um = os.path.join(tmp, "u.json")
        rc, so, _ = run_out([sys.executable, "-B", os.path.abspath(__file__),
                             "union-freeze", "--world", "wa=%s" % os.path.join(tmp, "wa"),
                             "--world", "wb=%s" % os.path.join(tmp, "wb"),
                             "--out", um, "--tier2", os.path.join(tmp, "u.t2")])
        assert rc == 0, "union-freeze 应 0 实测 %d\n%s" % (rc, so)
        first = open(um, "rb").read()
        rc, so, _ = run_out([sys.executable, "-B", os.path.abspath(__file__),
                             "union-freeze", "--world", "wa=%s" % os.path.join(tmp, "wa"),
                             "--world", "wb=%s" % os.path.join(tmp, "wb"), "--out", um])
        assert rc == 0 and open(um, "rb").read() == first, "union-freeze 幂等失守"

        def ucheck(extra=()):
            return run_out([sys.executable, "-B", os.path.abspath(__file__),
                            "union-check", "--manifest", um] + list(extra))

        def crit(so, name, v):
            """账面行断言（免 %-对齐空格耦合）：`c1 ci-idle PASS ...`。"""
            for ln in so.splitlines():
                parts = ln.split()
                if len(parts) >= 3 and parts[0] + " " + parts[1] == name \
                        and parts[2] == v:
                    return True
            return False
        rc, so, _ = ucheck(("--tier2", os.path.join(tmp, "u.t2")))
        assert rc == 0 and "union-check OK" in so, "零漂移 check 应 0\n%s" % so

        w("wb/sub/b.v", "Lemma b : False.\n")  # 漂移 B
        rc, so, _ = ucheck()
        assert rc == 1 and "1 changed" in so, "漂移应 1·账面应记 changed\n%s" % so
        w("wb/sub/b.v", "Lemma b : True.\n")

        doc = json.load(io.open(um, encoding="utf-8"))
        doc["worlds"][0]["tier1"][0][1] = "0" * 32  # tier1 篡改（tier2 未随改）
        with io.open(um, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        rc, so, _ = ucheck()
        assert rc == 1 and "tier2 FAIL" in so, "tier1 篡改应经 world tier2 现形\n%s" % so
        rc, _, _ = run_out([sys.executable, "-B", os.path.abspath(__file__),
                            "union-freeze", "--world", "wa=%s" % os.path.join(tmp, "wa"),
                            "--world", "wb=%s" % os.path.join(tmp, "wb"), "--out", um])
        doc = json.load(io.open(um, encoding="utf-8"))
        doc["union_tier2"] = "f" * 32  # union 层篡改
        with io.open(um, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        rc, so, _ = ucheck()
        assert rc == 1 and "union_tier2 层自洽: FAIL" in so, "union 层篡改应现形\n%s" % so
        rc, _, _ = run_out([sys.executable, "-B", os.path.abspath(__file__),
                            "union-freeze", "--world", "wa=%s" % os.path.join(tmp, "wa"),
                            "--world", "wb=%s" % os.path.join(tmp, "wb"), "--out", um,
                            "--tier2", os.path.join(tmp, "u.t2")])
        rc, so, _ = ucheck(("--tier2", os.path.join(tmp, "u.t2")))
        assert rc == 0, "重产零漂移应 0\n%s" % so
        with io.open(os.path.join(tmp, "u.t2"), "w", encoding="utf-8") as fh:
            fh.write("0" * 32 + "\n")  # 侧册篡改
        rc, so, _ = ucheck(("--tier2", os.path.join(tmp, "u.t2")))
        assert rc == 1 and "侧册咬合: FAIL" in so, "侧册篡改应现形\n%s" % so

        # —— window 向量（本地 path 远端·零网络） ——
        def wabs(path, content):
            with io.open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(content)

        gitc = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
        seed = os.path.join(tmp, "seedw")
        rc, _, se = run_out(gitc + ["init", "-q", "-b", "main", seed])
        assert rc == 0, se
        wabs(os.path.join(seed, "s.txt"), "seed\n")
        run_out(gitc + ["-C", seed, "add", "s.txt"])
        run_out(gitc + ["-C", seed, "commit", "-q", "-m", "s"])
        remote = os.path.join(tmp, "rem.git")  # bare——远端角色（push 允许）
        rc, _, se = run_out(["git", "clone", "-q", "--bare", seed, remote])
        assert rc == 0, se
        wk = os.path.join(tmp, "wk")  # origin=bare path（零网络）
        rc, _, se = run_out(["git", "clone", "-q", remote, wk])
        assert rc == 0, se
        # wk：commit x → push（造 `update by push` reflog）→ commit y（本地领先 ahead=1）
        wabs(os.path.join(wk, "x.txt"), "x\n")
        run_out(gitc + ["-C", wk, "add", "x.txt"])
        run_out(gitc + ["-C", wk, "commit", "-q", "-m", "x"])
        rc, _, se = run_out(gitc + ["-C", wk, "push", "-q", "origin", "main"])
        assert rc == 0, "push 应 0: %s" % se
        wabs(os.path.join(wk, "y.txt"), "y\n")
        run_out(gitc + ["-C", wk, "add", "y.txt"])
        run_out(gitc + ["-C", wk, "commit", "-q", "-m", "y"])

        suite_ok = os.path.join(tmp, "suite_ok.sh")
        with io.open(suite_ok, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\nexit 0\n")
        runs_idle = os.path.join(tmp, "runs_idle.json")
        with io.open(runs_idle, "w", encoding="utf-8") as fh:
            json.dump({"total_count": 2, "runs": [
                {"name": "ci", "status": "completed", "conclusion": "success"},
                {"name": "ci", "status": "completed", "conclusion": "failure"}]}, fh)
        runs_busy = os.path.join(tmp, "runs_busy.json")
        with io.open(runs_busy, "w", encoding="utf-8") as fh:
            json.dump({"total_count": 1, "runs": [{"name": "ci",
                                                   "status": "in_progress"}]}, fh)

        def window(extra):
            return run_out([sys.executable, "-B", os.path.abspath(__file__),
                            "window", "--repo", wk, "--suite", suite_ok] + list(extra))

        rc, so, _ = window(["--runs-json", runs_idle])
        assert rc == 0 and "push-window: OPEN" in so, "runs-json 源应 OPEN\n%s" % so
        assert crit(so, "c1 ci-idle", "PASS") and "runs-json 实证在飞=0" in so, so
        assert "behind=0 ahead=1" in so, "ahead/behind 应记账\n%s" % so
        rc, so, _ = window(["--ci-capped-min", "0"])
        assert rc == 0 and "push-window: OPEN" in so, "时间线源应 OPEN\n%s" % so
        assert crit(so, "c1 ci-idle", "PASS") and "在飞 run 不可能存在" in so, so
        rc, so, _ = window(["--runs-json", runs_busy])
        assert rc == 1 and "在飞 run=1" in so, "在飞>0 应 CLOSED\n%s" % so
        rc, so, _ = window([])
        assert rc == 1 and crit(so, "c1 ci-idle", "NOT-RUN") and \
            "无证据源" in so, "零证据应 NOT-RUN 关窗\n%s" % so
        rc, so, _ = window(["--ci-capped-min", "525600"])
        assert rc == 1 and crit(so, "c1 ci-idle", "NOT-RUN") and \
            "可能仍在飞" in so, "封顶窗未到应 NOT-RUN\n%s" % so
        # c2：远端独走一 commit（经第三 clone 推 bare）→ behind=1 → CLOSED
        adv = os.path.join(tmp, "adv")
        rc, _, se = run_out(["git", "clone", "-q", remote, adv])
        assert rc == 0, se
        wabs(os.path.join(adv, "z.txt"), "z\n")
        run_out(gitc + ["-C", adv, "add", "z.txt"])
        run_out(gitc + ["-C", adv, "commit", "-q", "-m", "z"])
        rc, _, se = run_out(gitc + ["-C", adv, "push", "-q", "origin", "main"])
        assert rc == 0, se
        rc, so, _ = window(["--runs-json", runs_idle])
        assert rc == 1 and "behind=1" in so, "behind=1 应 CLOSED\n%s" % so
        # c4：红套件 → CLOSED
        suite_bad = os.path.join(tmp, "suite_bad.sh")
        with io.open(suite_bad, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\nexit 3\n")
        rc, so, _ = window(["--runs-json", runs_idle, "--suite", suite_bad])
        assert rc == 1 and crit(so, "c4 cert-green", "FAIL") and \
            "rc=3" in so, "红套件应 CLOSED\n%s" % so
        # runs-json 畸形 → FAIL（证据不可采信）
        bad = os.path.join(tmp, "bad.json")
        with io.open(bad, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        rc, so, _ = window(["--runs-json", bad])
        assert rc == 1 and "runs-json 畸形" in so, "畸形证据应 FAIL\n%s" % so

        print("PUSH-GATE-SELFTEST PASS: UNION 幂等/零漂移/漂移/tier1 篡改/union 层/"
              "侧册六判＋window c1 双源/c2 behind/c4 红套件/零证据 NOT-RUN 四判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def main():
    ap = argparse.ArgumentParser(
        prog=PROG, description="certify 深件：推送窗四判据＋UNION v2 多世界清单")
    sub = ap.add_subparsers(dest="cmd")

    w = sub.add_parser("window", help="推送窗四判据机检（只判窗不开推）")
    w.add_argument("--repo", default=".", help="仓库目录（默认 cwd）")
    w.add_argument("--branch", default=None, help="分支（默认当前分支）")
    w.add_argument("--remote", default="origin", help="远端名（默认 origin）")
    w.add_argument("--runs-json", default=None,
                   help="c1 证据：预取的 Actions runs JSON（本器零网络）")
    w.add_argument("--ci-capped-min", type=int, default=None,
                   help="c1 证据：CI 时长封顶分钟数（reflog 推送时间线证据）")
    w.add_argument("--freeze-manifest", default=None,
                   help="c4 附加：冻结清单（freeze_manifest.py check 须零漂移）")
    w.add_argument("--suite", default=None,
                   help="c4 套件脚本（默认 <repo>/tests/run_tests.sh）")
    w.add_argument("--json", default=None, help="判据账目 JSON 出账路径")

    uf = sub.add_parser("union-freeze", help="UNION v2 多世界清单冻结")
    uf.add_argument("--world", action="append", default=[], metavar="NAME=PATH",
                    help="世界（可重复）")
    uf.add_argument("--out", default=None, help="清单出路径")
    uf.add_argument("--tier2", default=None, help="union_tier2 侧册出路径（可省）")

    uc = sub.add_parser("union-check", help="UNION v2 多世界清单对账")
    uc.add_argument("--manifest", default=None, help="在册清单路径")
    uc.add_argument("--tier2", default=None, help="union_tier2 侧册（可省·给了就咬合）")
    uc.add_argument("--json", default=None, help="对账账目 JSON 出账路径")

    ap.add_argument("--selftest", action="store_true", help="冻结向量组自证")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())
    here = _HERE
    if args.cmd == "window":
        cmd_window(args, here)
    elif args.cmd == "union-freeze":
        cmd_union_freeze(args)
    elif args.cmd == "union-check":
        cmd_union_check(args)
    else:
        ap.print_help(sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
