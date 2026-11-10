#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""net_probe.py — 网络窗探针（rocqwash tools/·双探稳窗律 20261110 判例工具化·
20261111 入账）

背景判例（20261110）：GitHub Actions artifact 上传端点 DNS 死窗（ENOTFOUND/
Upload progress stalled）→ rerun 发射前须「双探稳窗」：连续两轮（默认 60s 间隔）
全端点可达才准发射——单探 UP 禁发射（单轮假窗）。

可达性判据（纯代码化·裸 GET 语义）：
  urllib.request.urlopen(url, timeout=12)；拿到任何 HTTP 状态码（含 500/400 等
  HTTPError）＝TLS/DNS/HTTP 栈通＝可达即健康；URLError/超时/DNS 解析失败＝
  不可达（http_code=null）。HTTPError 是 URLError 子类——异常一律先过
  classify_error 分类（isinstance HTTPError→可达）再落码。

用法（端点全参数化·除下述缺省四端点外零硬编码·selftest 零网络）：
  python3 tools/net_probe.py [--endpoints URL[,URL...]] [--rounds N]
      [--interval S] [--stable-window] [--jitter S] [--seed N]
      [--json out.json]
  python3 tools/net_probe.py --selftest

--jitter S（韧性层 v37·缺省 0=关·须≥0）：每端点探测前随机微抖 sleep
  uniform(0, S) 秒（抖散对齐性重试风暴·每端点独立一抖）；--seed N 固定
  jitter 随机 seed（缺省系统熵·selftest 用固定 seed 保证确定性）。抖值如实
  入报告 endpoints[].jitter_sec（加法式键·--jitter 缺省 0 时零键零行为
  变化——既有报告面逐字节不漂）。

缺省四端点（判例 artifact 上传面＋API 面·--endpoints 逗号分隔可覆盖）：
  https://results-receiver-actions.githubusercontent.com
  https://productionresultssa1.blob.core.windows.net
  https://api.github.com
  https://github.com

--rounds N（默认 1·须≥1）·--interval S（默认 60·轮间 sleep·末轮不 sleep·须≥0）。
--stable-window：须 --rounds ≥2（否则用法错 2——双探稳窗·单探禁发射）；每轮每
端点全可达 → STABLE（exit 0），任一轮任一端点掉 → UNSTABLE（exit 1·每轮每端点
码如实报）。无 --stable-window：probe 完成即 exit 0（exit 0 仅＝probe 完成·
可达性看 verdict 字段），verdict 报三档 all-up|partial|all-down（跨轮汇总）。

退出码：0=probe 完成且（若 --stable-window）稳窗成立；1=不稳窗；2=用法错／
报告落盘失败。--json 报告 schema=rocqwash-net-probe/1：
  rounds[{at, endpoints[{url, http_code, ok(, jitter_sec)}]}] / verdict
  （jitter_sec 仅 --jitter>0 时在册·加法式）
verdict：--stable-window 时＝STABLE|UNSTABLE；否则＝all-up|partial|all-down。
落盘 json.dump(indent=1, ensure_ascii=False, sort_keys=True)＋newline="\\n"；
诚实注记：rounds[].at 为墙钟 UTC（活体探测逐轮可变——本轮报告即本轮证据·不跨
轮恒同）；端点序＝入参序确定性·其余字段确定性。
"""
import argparse
import io
import json
import os
import random
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

PROG = "net_probe"
SCHEMA = "rocqwash-net-probe/1"
TIMEOUT_SEC = 12
DEFAULT_ENDPOINTS = [
    "https://results-receiver-actions.githubusercontent.com",
    "https://productionresultssa1.blob.core.windows.net",
    "https://api.github.com",
    "https://github.com",
]


def classify_error(exc):
    """可达性分类：HTTPError（拿到 HTTP 状态码·TLS/DNS 已通）→ 可达；其余
    （URLError/超时/DNS 失败/裸 OSError/任何异常）→ 不可达。canned 异常实例
    可直接注入判定（selftest 零网络向量）。"""
    return isinstance(exc, urllib.error.HTTPError)


def probe_once(url, timeout=TIMEOUT_SEC, _open=None):
    """单端点裸 GET 探测 → (http_code:int|None, ok:bool, reason:str)。
    _open 可注入 canned urlopen（selftest 零网络·canned 异常类注入位）。"""
    opener = _open if _open is not None else urllib.request.urlopen
    try:
        resp = opener(url, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 — 一切异常交 classify_error 裁决
        ok = classify_error(exc)
        code = getattr(exc, "code", None) if ok else None
        return code, ok, "%s: %s" % (type(exc).__name__, exc)
    code = getattr(resp, "status", None)
    if code is None and hasattr(resp, "getcode"):
        code = resp.getcode()
    close = getattr(resp, "close", None)
    if close:
        close()
    return code, True, ""


def probe_round(endpoints, timeout=TIMEOUT_SEC, _open=None, jitter=0.0,
                rng=None, _sleep=None):
    """一轮全端点探测（入参序）→ (entries[{url,http_code,ok(,jitter_sec)}],
    reasons{url:原因})（reasons 只收 down·仅诊断 stdout 用·不入 JSON）。
    韧性层 v37：jitter>0 时每端点探测前随机微抖 sleep uniform(0, jitter) 秒
    （每端点独立一抖·rng 缺省 random 模块·_sleep 注入位供 selftest 固定
    seed 确定性矢量）；抖值入 entry jitter_sec（加法式·jitter=0 零键零睡
    零行为变化）。"""
    entries, reasons = [], {}
    do_sleep = _sleep if _sleep is not None else time.sleep
    r = rng if rng is not None else random
    for url in endpoints:
        jit = 0.0
        if jitter and jitter > 0:
            jit = r.uniform(0, jitter)
            do_sleep(jit)
        code, ok, reason = probe_once(url, timeout=timeout, _open=_open)
        entry = {"url": url, "http_code": code, "ok": ok}
        if jitter and jitter > 0:
            entry["jitter_sec"] = jit
        entries.append(entry)
        if not ok:
            reasons[url] = reason
    return entries, reasons


def summarize_verdict(rounds):
    """跨轮全探针汇总三档：all-up | partial | all-down（空集防御归 all-down·
    CLI 侧已禁空端点表）。"""
    probes = [e for r in rounds for e in r["endpoints"]]
    if not probes:
        return "all-down"
    ups = sum(1 for e in probes if e["ok"])
    if ups == len(probes):
        return "all-up"
    if ups == 0:
        return "all-down"
    return "partial"


def stable_window_holds(rounds):
    """双探稳窗判据：非空轮集且每轮每端点全可达。"""
    if not rounds:
        return False
    return all(e["ok"] for r in rounds for e in r["endpoints"])


def now_iso():
    """轮墙钟（UTC ISO·秒精度）。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_report(path, report):
    """确定性落盘（indent=1·ensure_ascii=False·sort_keys·newline=\\n）。"""
    try:
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1, ensure_ascii=False, sort_keys=True)
    except OSError as exc:
        print("FAIL-LOUD: 报告落盘失败 %s: %s" % (path, exc), file=sys.stderr)
        sys.exit(2)


def run_args(argv, env=None):
    """selftest 辅助：子进程跑本器（stdout+stderr 合流）。"""
    import subprocess
    e = dict(os.environ) if env is None else dict(env)
    p = subprocess.run([sys.executable, "-B",
                        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     PROG + ".py")] + list(argv),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=e)
    p.stdout = p.stdout.decode("utf-8", errors="replace") \
        if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p


def selftest():
    """内嵌冻结向量组（零网络·canned 异常类/响应体注入·零编译）：
    V1 classify_error/probe_once 分类：HTTPError(503/500/400)→可达带码·
       URLError→不可达·socket.timeout→不可达·canned 响应体 200/500→可达带码
    V2 probe_round canned 双端点混装：entries 形制与序·reasons 只收 down
    V3 verdict 三档：all-up/partial/all-down（单轮＋跨轮混装＋空集防御）
    V4 稳窗三判：两轮全过→True·首轮掉→False·次轮掉→False（空集→False）
    V5 CLI 用法码：--help→0·--bogus→2·--rounds 0→2·--stable-window --rounds 1→2·
       --endpoints 空表→2·--endpoints 缺 scheme→2·--interval 负→2·--jitter 负→2
    V6 报告落盘确定性：canned 定轮报告两写字节恒同
    V7 jitter 固定 seed 确定性：同 seed 同抖序·异 seed 异抖序·界 [0,S]·
       每端点一抖·抖值入账 jitter_sec·缺省 jitter=0 零键零睡零行为变化
    """
    import shutil
    import tempfile

    class FakeResp(object):
        """canned 响应体（urlopen 假件·零网络）。"""
        def __init__(self, status):
            self.status = status

        def close(self):
            pass

    def canned_open(resp=None, exc=None):
        def _open(url, timeout=None):
            if exc is not None:
                raise exc
            return resp
        return _open

    tmp = tempfile.mkdtemp(prefix="rocqwash_net_self_")
    try:
        # ---- V1 分类 ----
        for code in (503, 500, 400):
            he = urllib.error.HTTPError("https://x", code,
                                        "HTTP Error %d" % code, None, None)
            assert classify_error(he) is True, "HTTPError 须可达: %d" % code
            got = probe_once("https://x", _open=canned_open(exc=he))
            assert got[0] == code and got[1] is True, got
        ue = urllib.error.URLError("[Errno 8] nodename nor servname provided")
        assert classify_error(ue) is False, "URLError 须不可达"
        got = probe_once("https://x", _open=canned_open(exc=ue))
        assert got[0] is None and got[1] is False and "URLError" in got[2], got
        to = socket.timeout("timed out")
        got = probe_once("https://x", _open=canned_open(exc=to))
        assert got[0] is None and got[1] is False, got
        got = probe_once("https://x", _open=canned_open(resp=FakeResp(200)))
        assert got[0] == 200 and got[1] is True, got
        got = probe_once("https://x", _open=canned_open(resp=FakeResp(500)))
        assert got[0] == 500 and got[1] is True, "500 可达即健康"

        # ---- V2 probe_round 形制 ----
        ok_url, dead_url = "https://ok.example", "https://dead.example"

        def mixed_open(url, timeout=None):
            if url == ok_url:
                return FakeResp(200)
            raise ue
        entries, reasons = probe_round([ok_url, dead_url], _open=mixed_open)
        assert entries == [
            {"url": ok_url, "http_code": 200, "ok": True},
            {"url": dead_url, "http_code": None, "ok": False}], entries
        assert list(reasons) == [dead_url] and "URLError" in reasons[dead_url], \
            reasons

        # ---- V3 verdict 三档 ----
        up = {"endpoints": [{"url": "a", "http_code": 200, "ok": True}]}
        down = {"endpoints": [{"url": "b", "http_code": None, "ok": False}]}
        assert summarize_verdict([up]) == "all-up"
        assert summarize_verdict([up, up]) == "all-up"
        assert summarize_verdict([up, down]) == "partial"
        assert summarize_verdict([down]) == "all-down"
        assert summarize_verdict([]) == "all-down"

        # ---- V4 稳窗三判 ----
        assert stable_window_holds([up, up]) is True, "两轮全过须 STABLE"
        assert stable_window_holds([up, down]) is False, "次轮掉须 UNSTABLE"
        assert stable_window_holds([down, up]) is False, "首轮掉须 UNSTABLE"
        assert stable_window_holds([]) is False, "空集防御"

        # ---- V5 CLI 用法码 ----
        p = run_args(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        for vec in (["--bogus"],
                    ["--rounds", "0"],
                    ["--stable-window", "--rounds", "1"],
                    ["--endpoints", "  "],
                    ["--endpoints", "ftp://x.example,https://y.example"],
                    ["--interval", "-1"],
                    ["--jitter", "-1"]):
            p = run_args(vec)
            assert p.returncode == 2, "用法错应 rc=2 实测 %d: %s" \
                % (p.returncode, vec)

        # ---- V6 报告落盘确定性 ----
        fixed = {"schema": SCHEMA,
                 "rounds": [{"at": "2026-11-11T00:00:00Z", "endpoints": [
                     {"url": "https://a", "http_code": 200, "ok": True}]}],
                 "verdict": "all-up"}
        j1 = os.path.join(tmp, "n1.json")
        j2 = os.path.join(tmp, "n2.json")
        write_report(j1, fixed)
        write_report(j2, fixed)
        assert io.open(j1, "rb").read() == io.open(j2, "rb").read(), \
            "json 字节漂移＝违例"
        rep = json.load(io.open(j1, encoding="utf-8"))
        assert rep["schema"] == SCHEMA and rep["verdict"] == "all-up", rep

        # ---- V7 jitter 固定 seed 确定性（零网络·canned 全通探针）----
        eps = ["https://a.example", "https://b.example", "https://c.example"]

        def up_open(url, timeout=None):
            return FakeResp(200)

        slept_a, slept_b, slept_c = [], [], []
        ea, _ = probe_round(eps, _open=up_open, jitter=0.5,
                            rng=random.Random(2026), _sleep=slept_a.append)
        eb, _ = probe_round(eps, _open=up_open, jitter=0.5,
                            rng=random.Random(2026), _sleep=slept_b.append)
        ec, _ = probe_round(eps, _open=up_open, jitter=0.5,
                            rng=random.Random(7), _sleep=slept_c.append)
        assert slept_a == slept_b, "同 seed 须同抖序: %s vs %s" \
            % (slept_a, slept_b)
        assert slept_c != slept_a, "异 seed 须异抖序"
        assert len(slept_a) == 3, "每端点一抖·实测 %d" % len(slept_a)
        assert all(0.0 <= s <= 0.5 for s in slept_a), slept_a
        assert [e["jitter_sec"] for e in ea] == slept_a, "抖值须入账"
        assert all(set(e) == {"url", "http_code", "ok", "jitter_sec"}
                   for e in ea), ea
        ed, _ = probe_round(eps, _open=up_open)   # 缺省 jitter=0
        assert all(set(e) == {"url", "http_code", "ok"} for e in ed), \
            "缺省零键零行为变化"
        assert ed == [{"url": u, "http_code": 200, "ok": True} for u in eps], ed

        print("NET-PROBE-SELFTEST PASS: 分类（HTTPError 可达/URLError·超时不可达/"
              "canned 200·500）/round 形制＋reasons/verdict 三档/稳窗三判/"
              "CLI 用法八码/落盘字节恒同/jitter 固定 seed 确定性 八节全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="网络窗探针：裸 GET 全端点可达性 N 轮探测＋双探稳窗判定"
                    "（发射闸：--stable-window 连续全轮全端点可达才 exit 0）")
    ap.add_argument("--endpoints", default=None, metavar="URL[,URL...]",
                    help="端点表（缺省四端点·逗号分隔覆盖）")
    ap.add_argument("--rounds", type=int, default=1, metavar="N",
                    help="探测轮数（默认 1·须≥1）")
    ap.add_argument("--interval", type=float, default=60.0, metavar="S",
                    help="轮间隔秒（默认 60·末轮不 sleep）")
    ap.add_argument("--stable-window", action="store_true",
                    dest="stable_window",
                    help="稳窗闸：rounds≥2 且全轮全端点可达才 exit 0")
    ap.add_argument("--jitter", type=float, default=0.0, metavar="S",
                    help="每端点探测前随机微抖秒（uniform(0,S)·默认 0=关·"
                         "须≥0）")
    ap.add_argument("--seed", type=int, default=None, metavar="N",
                    help="jitter 随机 seed（缺省系统熵·固定 seed 保证确定性）")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="探测报告出账（schema rocqwash-net-probe/1）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    endpoints = list(DEFAULT_ENDPOINTS)
    if args.endpoints is not None:
        endpoints = [u.strip() for u in args.endpoints.split(",") if u.strip()]
        if not endpoints:
            print("FAIL-LOUD: --endpoints 展开后为空", file=sys.stderr)
            sys.exit(2)
        for u in endpoints:
            if not (u.startswith("http://") or u.startswith("https://")):
                print("FAIL-LOUD: 端点缺 http(s) scheme: %s" % u,
                      file=sys.stderr)
                sys.exit(2)
    if args.rounds < 1:
        print("FAIL-LOUD: --rounds 须≥1 实测 %d" % args.rounds, file=sys.stderr)
        sys.exit(2)
    if args.interval < 0:
        print("FAIL-LOUD: --interval 须≥0 实测 %s" % args.interval,
              file=sys.stderr)
        sys.exit(2)
    if args.stable_window and args.rounds < 2:
        print("FAIL-LOUD: --stable-window 须 --rounds ≥2（双探稳窗·单探禁发射）",
              file=sys.stderr)
        sys.exit(2)
    if args.jitter < 0:
        print("FAIL-LOUD: --jitter 须≥0 实测 %s" % args.jitter, file=sys.stderr)
        sys.exit(2)
    rng = random.Random(args.seed)

    print("=== NET-PROBE ===")
    print("rounds=%d interval=%ss timeout=%ss stable_window=%s endpoints=%d"
          % (args.rounds, args.interval, TIMEOUT_SEC, args.stable_window,
             len(endpoints))
          + (" jitter=%gs seed=%s" % (args.jitter, args.seed)
             if args.jitter > 0 else ""))
    rounds = []
    for i in range(args.rounds):
        if i > 0:
            time.sleep(args.interval)
        at = now_iso()
        entries, reasons = probe_round(endpoints, jitter=args.jitter, rng=rng)
        rounds.append({"at": at, "endpoints": entries})
        ups = sum(1 for e in entries if e["ok"])
        print("round %d @%s: %d/%d up" % (i + 1, at, ups, len(entries)))
        for e in entries:
            mark = " UP " if e["ok"] else "DOWN"
            code = str(e["http_code"]) if e["http_code"] is not None else "--"
            reason = (" (%s)" % reasons[e["url"]]) if not e["ok"] else ""
            print("  [%s] %s %s%s" % (mark, code, e["url"], reason))

    verdict = ("STABLE" if stable_window_holds(rounds) else "UNSTABLE") \
        if args.stable_window else summarize_verdict(rounds)
    if args.json:
        write_report(args.json, {"schema": SCHEMA, "rounds": rounds,
                                 "verdict": verdict})
        print("json ->", args.json)
    print("verdict: %s" % verdict)
    if args.stable_window:
        if verdict == "UNSTABLE":
            print("FAIL: 稳窗不成立（UNSTABLE·任一轮任一端点掉线即禁发射）",
                  file=sys.stderr)
            sys.exit(1)
        print("STABLE-WINDOW OK（双探全过·准发射口径）")
    sys.exit(0)


if __name__ == "__main__":
    main()
