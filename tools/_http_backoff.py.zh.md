#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_http_backoff.py — 三器共享 HTTP 限流退避小模块（rocqwash tools/·v37 韧性层
20261111 入账）

被 ci_triage.py／pushci.py／cw_sentinel.py 的 _api（或等价 HTTP 客户端）import：
tools/ 平铺脚本无 __init__ 包结构——各器 import 前以 sys.path 注入自身目录
（同目录共享·承 cw_sentinel netrc_token 副本先例的同一诉求·本模块化消除三份
副本漂移）。

纯函数三件（零 IO 零钟零随机·同参重跑恒同·--selftest 冻结向量）：
  is_retry_status(code)   403/429/5xx → True（限流/瞬断重试面·判例 403 Forbidden
                          /429 rate limit/5xx 服务端瞬断）；其余（含 401/404/
                          409 等 4xx 语义面）→ False——语义面交调用方裁决不重试。
  backoff_delays(retry_max, base=2.0)
                          重试帽 n → 指数退避延迟秒表 [base·2^0, base·2^1, …]
                          长度恰 n（判例 n=3·base=2 → [2,4,8]；n=0 → []·零重试
                          零等待）；负 n/非 int → ValueError（fail-loud）。
  parse_retry_after(val)  Retry-After 头秒数形（RFC 7231 delay-seconds）→ float
                          ≥0；None/空/非数/负数/HTTP-date 形 → None——HTTP-date
                          须墙钟换算故不猜（诚实律：解析不了的尊重形式落回指数
                          延迟·调用方响亮可查）。

runner 惯例（循环各器自持·本模块只供判定与延迟计算·注入器 canned 路径一律
不重试——离线可测铁律：canned 响应即确定性测试面）：
  逐 attempt：响应码∈重试面且重试未耗尽 → 延迟=parse_retry_after(头) 优先·
  无可解析头落 backoff_delays(retry_max)[attempt] → sleep → 重发；重试耗尽 →
  原错误原样上抛（fail-loud 口径各器自裁：ci_triage 9·pushci (code,body) 交
  语义裁决·cw_sentinel 9）。

用法：
  python3 tools/_http_backoff.py --selftest   # 纯函数冻结向量（零网络零 IO）
"""
import sys

PROG = "_http_backoff"

DEFAULT_BASE = 2.0            # 指数退避基秒（任务书钦定 base 2s）
RETRY_STATUSES = frozenset((403, 429))


def is_retry_status(code):
    """响应码 → 是否重试面（403/429/5xx）。非 int/None → False。"""
    if not isinstance(code, int) or isinstance(code, bool):
        return False
    return code in RETRY_STATUSES or (500 <= code <= 599)


def backoff_delays(retry_max, base=DEFAULT_BASE):
    """重试帽 n → 指数退避延迟秒表（长 n·第 i 次重试前睡 base·2^i）。
    判例：retry_max=3·base=2 → [2.0, 4.0, 8.0]（任务书 403×3→[2,4,8]）。
    n=0 → []；负 n/非 int → ValueError（fail-loud）。"""
    if not isinstance(retry_max, int) or isinstance(retry_max, bool) \
            or retry_max < 0:
        raise ValueError("retry_max 须非负 int·实测 %r" % (retry_max,))
    return [float(base) * (2 ** i) for i in range(retry_max)]


def parse_retry_after(value):
    """Retry-After 头秒数形 → float ≥0；None/空/非数/负/HTTP-date 形 → None
    （调用方落回指数延迟）。纯字符串解析·零墙钟。"""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    if f < 0:
        return None
    return f


def selftest():
    """内嵌冻结向量组（纯函数·零网络零 IO）：退避序列判例 403×3→[2,4,8]／
    边界 0/1/负/非 int／重试面正负判／Retry-After 秒数·HTTP-date·负·空。"""
    assert backoff_delays(3) == [2.0, 4.0, 8.0], backoff_delays(3)
    assert backoff_delays(0) == []
    assert backoff_delays(1) == [2.0]
    assert backoff_delays(2, base=1.0) == [1.0, 2.0]
    for bad in (-1, "3", 1.5, None, True):
        try:
            backoff_delays(bad)
            assert False, "retry_max=%r 应 ValueError" % (bad,)
        except ValueError:
            pass
    assert is_retry_status(403) and is_retry_status(429)
    for c in (500, 502, 503, 504, 599):
        assert is_retry_status(c), c
    for c in (200, 201, 301, 400, 401, 404, 409, 422, 499, 600, None, "503"):
        assert not is_retry_status(c), c
    assert parse_retry_after("60") == 60.0
    assert parse_retry_after(" 15 ") == 15.0
    assert parse_retry_after("0") == 0.0
    for bad in (None, "", "-5", "abc",
                "Wed, 21 Oct 2026 07:28:00 GMT"):
        assert parse_retry_after(bad) is None, bad
    print("_HTTP-BACKOFF-SELFTEST PASS: 退避序列 403×3→[2,4,8]/帽 0·1·负·非 int"
          " fail-loud/重试面 403·429·5xx 正负判/Retry-After 秒数尊重·HTTP-date"
          " 不猜落回指数 全过")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    print("FAIL-LOUD: 须 --selftest（本模块为共享库·无 CLI 面）", file=sys.stderr)
    sys.exit(2)
