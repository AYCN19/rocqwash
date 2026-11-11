#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_events.py — cw_sentinel JSONL 事件流→markdown 台账渲染器（rocqwash
tools/·工装席单件迷你波·纯消费端零网络零重造——承 cw_sentinel.py 事件流
rocqwash-sentinel-event/1（cw_sentinel.py:32·三路信号源 kind 全谱见
cw_sentinel.py:17/22/28）与 chain_graph.py 渲染判例（计数降序 top_md·
sort_keys 落盘 chain_graph.py:298）·20261111 入账）

输入二形（互斥——--events 与 --dir 双给/双缺均 2）：
  ① --events FILE：单份 JSONL 事件流（逐行一事件·行序即流序——哨 --emit
    append 产出序·seq 事件流内单调跨进程续号·消费端不重排如实照映）；
  ② --dir DIR：目录下全部 *.jsonl（文件名典序读入）合并＝一条事件流，按
    (seq, ts, 来源序, 行序) 排序恢复全局序（seq 主键 ts 次键——轮转代/
    多文件分片按 seq 跨代续号同属一条流·同键以来源序行序定·确定性）。
  不去重：流里有什么渲染什么（重复是流的真相非器的错·如实）。
  行容错（任务书④）：非 JSON 行／JSON 而非 dict 形坏行＝坏行→跳过＋计
    bad_lines＋stderr 逐行 WARN 响亮不中断（渲染继续出账照常·退出码 1
    表数据残缺）；空行跳过不计坏行不计事件。kind 非 ci-red/blocking/
    build-signal（cw_sentinel 三路信号源全谱）或缺失→计数归 other；
    family/action 缺失或空→计数归 (none) 桶——三维计数恒可加·和恒等
    events_total。

渲染 --md 台账（确定性·同输入重跑字节级恒同）：
  标题→输入行（模式＋份数＋序口径）→events_total/bad_lines 行→三维分布
  表（kind/family/action 各一表·n 降序同数键典序·family 表 --top N 截断
  缺省全量）→逐事件 md 表（seq/kind/family/action/repo/run/branch/sha 前
  8/evidence 首 2 条「；」连——kind 列 verbatim 照映流内真值·other 只进
  统计；单元格竖线转义换行压空防冲表；缺字段空串）→verdict 注记
  （verdict/events_total/bad_lines/span）。

--json summary（rocqwash-render-events/1·indent 2＋sort_keys 落盘）：
  {schema, events_total, bad_lines, verdict(ok|empty), counts{kind,family,
   action}, span{first_ts,last_ts|null}, sources[实读文件·读入序/典序]}
  span＝流内全部非空 ts 的 min/max（字典序=ISO 8601 UTC 时序；全流无 ts
  ——哨 --sleep-scale 0 关钟流→双双 null·--selftest 确定性同源）。
  counts 恒全量（--top 截断只是 md family 表面·summary 不截）。
verdict 口径：events_total>0→ok；=0（空文件/全坏行/空目录流）→empty。
  空与红都是数据·如实渲染不装红（exit 0 如实——任务书④）。

--top N：family 分布表截前 N 行（n 降序同数典序）＋「余 X 族未示」注记；
  缺省 0＝全量；N<0→2。

退出码（0/1/2/9 四码）：0=渲染完成零坏行（verdict ok 或 empty 皆 0——
  红是数据非器红·空也如实 0）；1=渲染完成但 bad_lines>0（出账照常不中断
  ·数据残缺响亮——baseline_diff.py:50 degraded/ledger_sync.py:56
  SYNC-FINDINGS 同律）；2=用法错（--events/--dir 双给或双缺/--top 负/
  argparse 形错）；9=输入不可达（--events 文件缺·--dir 目录缺·目录无任何
  *.jsonl·文件不可读·出账不可写）。stdout 恒响亮一行 RENDER-EVENTS 总账
  （fail-loud 错误 stderr FAIL-LOUD 即断·ci_triage.py:174 同款）。

用法：
  python3 tools/render_events.py --events FILE.jsonl [--md out.md] \\
      [--json out.json] [--top N]
  python3 tools/render_events.py --dir DIR [--md out.md] \\
      [--json out.json] [--top N]
  python3 tools/render_events.py --selftest

--selftest：canned JSONL tmp fixture（三 kind 混合＋未知 kind＋坏行＋空
  文件＋全坏行＋干净流＋双文件乱序 --dir 合并）矢量组：三维统计正确/md
  表成行＋竖线转义＋evidence 首 2 截断/坏行容错（rc1 出账照常）/空文件
  verdict=empty rc0/全坏行 empty rc1/--dir seq+ts 跨文件归位/--top 截断
  /幂等两跑字节恒同/CLI 四码（0/1/2/9）。0=全过／2=断言失败。
"""
import argparse
import io
import json
import os
import sys

PROG = "render_events"
SCHEMA = "rocqwash-render-events/1"
EVENT_SCHEMA = "rocqwash-sentinel-event/1"
# cw_sentinel 三路信号源 kind 全谱（cw_sentinel.py:17/22/28）——谱外归 other
KNOWN_KINDS = ("ci-red", "blocking", "build-signal")
OTHER_KEY = "other"
NONE_KEY = "(none)"
EVIDENCE_MAX = 2


def fail(code, msg):
    """fail-loud 即断（code: 2=用法错·9=输入/出账不可达）——stderr 响亮。"""
    print("FAIL-LOUD: %s" % msg, file=sys.stderr)
    sys.exit(code)


def md_cell(value):
    """md 表格单元消毒：竖线转义＋回车换行压空（防冲表·确定性）。"""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def seq_key(ev):
    """排序主键：seq int 直用（bool 剔除）·十进制串收整·缺失/形异排前(-1)。"""
    s = ev.get("seq")
    if isinstance(s, bool):
        return -1
    if isinstance(s, int):
        return s
    if isinstance(s, str) and s.lstrip("-").isdigit():
        return int(s)
    return -1


def ts_of(ev):
    """事件 ts（非空串才有效——哨 --sleep-scale 0 关钟流无 ts）。"""
    t = ev.get("ts")
    return t if isinstance(t, str) and t else ""


def kind_of(ev):
    """计数用 kind：谱内 verbatim·谱外/缺失归 other（任务书④）。"""
    k = ev.get("kind")
    return k if k in KNOWN_KINDS else OTHER_KEY


def verbatim(ev, key):
    """逐事件行 verbatim 取值（str 直用·int/float str 化·bool/缺失→空串）。"""
    v = ev.get(key)
    if isinstance(v, str):
        return v
    if isinstance(v, bool) or v is None:
        return ""
    if isinstance(v, (int, float)):
        return str(v)
    return ""


def load_events(path):
    """单份 JSONL → (events, bad_lines)。坏行跳过计响亮不中断（任务书④）。"""
    try:
        fh = io.open(path, "r", encoding="utf-8", errors="replace")
    except OSError as e:
        fail(9, "事件流不可读: %s（%s）" % (path, e))
    events, bad = [], 0
    with fh:
        for lineno, line in enumerate(fh, 1):
            s = line.strip()
            if not s:
                continue  # 空行容错跳过（不计坏行不计事件）
            try:
                obj = json.loads(s)
            except ValueError:
                bad += 1
                print("WARN: %s:%d 非 JSON 坏行（跳过计入 bad_lines）"
                      % (path, lineno), file=sys.stderr)
                continue
            if not isinstance(obj, dict):
                bad += 1
                print("WARN: %s:%d JSON 非 dict 形坏行（跳过计入 bad_lines）"
                      % (path, lineno), file=sys.stderr)
                continue
            events.append(obj)
    return events, bad


def read_inputs(args):
    """输入二形统一读入 → (events, bad_lines, sources, input_desc)。

    --events 单份：行序即流序（不重排如实照映）；--dir 合并：按
    (seq, ts, 来源序, 行序) 排序恢复全局序。缺输入面 fail 9（目录在而无
    *.jsonl 同 9——输入面不存在是器况非流况·流内容空才是 empty）。
    """
    events, bad, sources = [], 0, []
    if args.events:
        if not os.path.isfile(args.events):
            fail(9, "事件流文件缺失: %s" % args.events)
        sources = [args.events]
        events, bad = load_events(args.events)
        desc = "--events %s（单份·行序即流序）" % args.events
        return events, bad, sources, desc
    if not os.path.isdir(args.dir):
        fail(9, "事件流目录缺失: %s" % args.dir)
    names = sorted(n for n in os.listdir(args.dir) if n.endswith(".jsonl"))
    paths = [os.path.join(args.dir, n) for n in names
             if os.path.isfile(os.path.join(args.dir, n))]
    if not paths:
        fail(9, "目录无任何 *.jsonl: %s" % args.dir)
    sources = paths
    tagged = []
    for src_idx, path in enumerate(paths):
        evs, b = load_events(path)
        bad += b
        for line_idx, ev in enumerate(evs):
            tagged.append((ev, src_idx, line_idx))
    tagged.sort(key=lambda t: (seq_key(t[0]), ts_of(t[0]), t[1], t[2]))
    events = [ev for ev, _, _ in tagged]
    desc = "--dir %s（%d 份合并·seq+ts 序）" % (args.dir, len(paths))
    return events, bad, sources, desc


def tally(events):
    """三维分布计数（kind 谱外归 other·family/action 缺失归 (none)）——
    三表和恒等 events_total（计数可加性=统计自洽的机械判据）。"""
    counts = {"kind": {}, "family": {}, "action": {}}
    for ev in events:
        k = kind_of(ev)
        counts["kind"][k] = counts["kind"].get(k, 0) + 1
        for dim in ("family", "action"):
            v = ev.get(dim)
            if v is None or (isinstance(v, str) and not v):
                v = NONE_KEY
            elif not isinstance(v, str):
                v = str(v)
            counts[dim][v] = counts[dim].get(v, 0) + 1
    return counts


def span_of(events):
    """span＝流内全部非空 ts 的 min/max（字典序=ISO 时序）·全流无 ts 双 null。"""
    ts = sorted(t for t in (ts_of(ev) for ev in events) if t)
    return {"first_ts": ts[0] if ts else None,
            "last_ts": ts[-1] if ts else None}


def render_md(events, counts, span, verdict, bad_lines, input_desc, top):
    """台账 markdown（确定性：计数 n 降序同数典序·逐事件流序·零时钟零随机）。"""
    lines = ["# cw_sentinel 事件台账（%s）" % SCHEMA, ""]
    lines.append("- 输入：%s" % input_desc)
    lines.append("- events_total=%d·bad_lines=%d" % (len(events), bad_lines))
    lines.append("")
    lines.append("## 分布计数（kind／family／action·n 降序同数键典序）")
    for dim in ("kind", "family", "action"):
        rows = sorted(counts[dim].items(), key=lambda kv: (-kv[1], kv[0]))
        head = "### %s" % dim
        if dim == "family" and top > 0 and len(rows) > top:
            head += "（--top %d 截断·余 %d 族未示）" % (top, len(rows) - top)
        lines.append("")
        lines.append(head)
        lines.append("| %s | n |" % dim)
        lines.append("|---|---|")
        for key, n in (rows[:top] if (dim == "family" and top > 0) else rows):
            lines.append("| %s | %d |" % (md_cell(key), n))
    lines.append("")
    lines.append("## 逐事件（seq/kind/family/action/repo/run/branch/sha 前 8"
                 "/evidence 首 2 条）")
    lines.append("| seq | kind | family | action | repo | run | branch | sha8 "
                 "| evidence(首2) |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for ev in events:
        sha = ev.get("sha")
        sha8 = sha[:8] if isinstance(sha, str) else ""
        evidence = ev.get("evidence")
        if isinstance(evidence, list):
            ev_txt = "；".join(md_cell(x) for x in evidence[:EVIDENCE_MAX])
        else:
            ev_txt = ""
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            md_cell(verbatim(ev, "seq")), md_cell(verbatim(ev, "kind")),
            md_cell(verbatim(ev, "family")), md_cell(verbatim(ev, "action")),
            md_cell(verbatim(ev, "repo")), md_cell(verbatim(ev, "run")),
            md_cell(verbatim(ev, "branch")), md_cell(sha8), ev_txt))
    lines.append("")
    lines.append("---")
    span_txt = ("%s..%s" % (span["first_ts"], span["last_ts"])
                if span["first_ts"] else "无 ts（关钟流）")
    lines.append("- verdict=%s（events_total=%d·bad_lines=%d·span=%s）"
                 % (verdict, len(events), bad_lines, span_txt))
    lines.append("")
    return "\n".join(lines)


def write_text(path, text):
    """md 出账（不可写→9 fail-loud）。"""
    try:
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError as e:
        fail(9, "md 出账不可写: %s（%s）" % (path, e))


def write_json(path, obj):
    """summary 出账（indent 2＋sort_keys＋ensure_ascii=False·尾换行）。"""
    try:
        with io.open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
    except OSError as e:
        fail(9, "json 出账不可写: %s（%s）" % (path, e))


def selftest():
    """内嵌冻结矢量组（canned JSONL tmp fixture·零触真仓零网络）：三维统计
    ＋md 表成行（转义/截断）＋坏行容错 rc1＋空文件 empty rc0＋全坏行 empty
    rc1＋--dir seq+ts 跨文件归位＋--top 截断＋幂等字节恒同＋CLI 四码。"""
    import re
    import shutil
    import subprocess
    import tempfile

    def run(args):
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(
                                os.path.abspath(__file__)),
                                PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def dump_jsonl(path, lines):
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write("".join(x + "\n" if not x.endswith("\n") else x
                             for x in lines))

    def ev(seq, ts, kind, family, action, run_id, evidence=None):
        e = {"schema": EVENT_SCHEMA, "seq": seq, "ts": ts, "kind": kind,
             "family": family, "action": action, "repo": "org/repo",
             "run": run_id, "branch": "br%d" % seq,
             "sha": "%08x" % seq + "1" * 32,
             "evidence": (["ev%d-a" % seq, "ev%d-b" % seq, "ev%d-c" % seq]
                          if evidence is None else evidence)}
        return json.dumps(e, sort_keys=True, ensure_ascii=False)

    tmp = tempfile.mkdtemp(prefix="rocqwash_render_events_self_")
    try:
        # 矢量① 混合流：三 kind＋未知 kind＋坏行（非 JSON）＋evidence 含竖线
        mixed = os.path.join(tmp, "mixed.jsonl")
        dump_jsonl(mixed, [
            ev(1, "2026-11-10T00:00:01Z", "ci-red", "A-content-red",
               "fix-content", 111, ["红件 1/2 ids=[1]", "在册族：A"]),
            "<<<这不是 JSON>>>",  # 坏行·夹心
            ev(2, "2026-11-10T00:00:02Z", "ci-red", "B-netred",
               "rerun-after-stable-window", 222),
            ev(3, "2026-11-10T00:00:03Z", "blocking", "X-root",
               "wash-root", 333, []),
            ev(4, "2026-11-10T00:00:04Z", "build-signal", "Y-sig",
               "watch-only", 444, ["a|b", "c", "d"]),
            ev(5, "2026-11-10T00:00:05Z", "future-kind", "Z-unk",
               "probe-it", 555),
        ])
        jf = os.path.join(tmp, "mixed.json")
        mf = os.path.join(tmp, "mixed.md")
        p = run(["--events", mixed, "--json", jf, "--md", mf])
        assert p.returncode == 1, "坏行应 rc=1（数据残缺·出账照常）实得 %d\n%s" \
            % (p.returncode, p.stdout)
        g = json.load(io.open(jf, encoding="utf-8"))
        assert g["schema"] == SCHEMA and g["verdict"] == "ok", g
        assert g["events_total"] == 5 and g["bad_lines"] == 1, g
        assert g["counts"]["kind"] == {"blocking": 1, "build-signal": 1,
                                       "ci-red": 2, "other": 1}, g["counts"]
        assert g["counts"]["family"] == {"A-content-red": 1, "B-netred": 1,
                                         "X-root": 1, "Y-sig": 1,
                                         "Z-unk": 1}, g["counts"]
        assert g["counts"]["action"] == {"fix-content": 1,
                                         "probe-it": 1,
                                         "rerun-after-stable-window": 1,
                                         "wash-root": 1,
                                         "watch-only": 1}, g["counts"]
        assert g["span"] == {"first_ts": "2026-11-10T00:00:01Z",
                             "last_ts": "2026-11-10T00:00:05Z"}, g["span"]
        assert sum(g["counts"]["kind"].values()) == 5, "三维和≠events_total"
        md = io.open(mf, encoding="utf-8").read()
        # md 表成行：seq1 全列（sha 前 8·evidence 首 2「；」连·第 3 条不现）
        assert "| 1 | ci-red | A-content-red | fix-content | org/repo | 111 " \
               "| br1 | 00000001 | 红件 1/2 ids=[1]；在册族：A |" in md, md
        assert "| 3 | blocking | X-root | wash-root | org/repo | 333 | br3 | " \
               "00000003 |  |" in md, "空 evidence 行不成行"
        assert "a\\|b；c |" in md, "竖线未转义"
        assert "；c；d" not in md, "evidence 未截首 2（第 3 条不应现）"
        assert "future-kind" in md, "kind 列应 verbatim 照映流内真值"
        assert "RENDER-EVENTS: verdict=ok events_total=5 bad_lines=1" \
            in p.stdout, p.stdout
        print("矢量① 三维统计＋md 表成行＋转义/截断＋坏行 rc1: PASS")

        # 矢量② 空文件：verdict empty·rc0 如实（任务书④）
        empty = os.path.join(tmp, "empty.jsonl")
        dump_jsonl(empty, [])
        je = os.path.join(tmp, "empty.json")
        me = os.path.join(tmp, "empty.md")
        p = run(["--events", empty, "--json", je, "--md", me])
        assert p.returncode == 0, "空文件应 rc0 实得 %d\n%s" % (p.returncode,
                                                               p.stdout)
        g = json.load(io.open(je, encoding="utf-8"))
        assert g["verdict"] == "empty" and g["events_total"] == 0, g
        assert g["span"] == {"first_ts": None, "last_ts": None}, g["span"]
        assert "verdict=empty" in io.open(me, encoding="utf-8").read(), me
        print("矢量② 空文件 verdict=empty rc0: PASS")

        # 矢量③ 全坏行：verdict empty 且 rc1（空是流况·脏是数据残缺·两如实）
        garbage = os.path.join(tmp, "garbage.jsonl")
        dump_jsonl(garbage, ["垃圾一", "垃圾二"])
        p = run(["--events", garbage, "--json", os.path.join(tmp, "g.json")])
        assert p.returncode == 1, "全坏行应 rc1 实得 %d" % p.returncode
        g = json.load(io.open(os.path.join(tmp, "g.json"), encoding="utf-8"))
        assert g["verdict"] == "empty" and g["bad_lines"] == 2 \
            and g["events_total"] == 0, g
        print("矢量③ 全坏行 empty rc1 两如实: PASS")

        # 矢量④ --dir 乱序合并：seq 1,2 在 b 前·3,4,5 在 a——按 seq 跨文件归位
        d = os.path.join(tmp, "streams")
        os.makedirs(d)
        dump_jsonl(os.path.join(d, "a_late.jsonl"), [
            ev(3, "2026-11-10T00:00:03Z", "blocking", "X-root",
               "wash-root", 333, []),
            ev(4, "2026-11-10T00:00:04Z", "build-signal", "Y-sig",
               "watch-only", 444, ["a|b", "c", "d"]),
            ev(5, "2026-11-10T00:00:05Z", "future-kind", "Z-unk",
               "probe-it", 555),
        ])
        dump_jsonl(os.path.join(d, "b_early.jsonl"), [
            ev(1, "2026-11-10T00:00:01Z", "ci-red", "A-content-red",
               "fix-content", 111, ["红件 1/2 ids=[1]", "在册族：A"]),
            "<<<坏>>>",
            ev(2, "2026-11-10T00:00:02Z", "ci-red", "B-netred",
               "rerun-after-stable-window", 222),
        ])
        jd = os.path.join(tmp, "dir.json")
        mdir = os.path.join(tmp, "dir.md")
        p = run(["--dir", d, "--json", jd, "--md", mdir])
        assert p.returncode == 1, p.stdout
        md = io.open(mdir, encoding="utf-8").read()
        # 逐事件节 seq 序抽取（^\| N \|——evidence 内转义竖线不扰列解析）
        sec = md.split("## 逐事件", 1)[1]
        seqs = re.findall(r"^\| (\d+) \|", sec, re.M)
        assert seqs == ["1", "2", "3", "4", "5"], "seq+ts 跨文件归位破: %s" \
            % seqs
        g = json.load(io.open(jd, encoding="utf-8"))
        assert g["events_total"] == 5 and g["bad_lines"] == 1, g
        assert g["sources"] == [os.path.join(d, "a_late.jsonl"),
                                os.path.join(d, "b_early.jsonl")], g["sources"]
        print("矢量④ --dir seq+ts 跨文件归位: PASS")

        # 矢量⑤ --top 截断：family 表两行＋余 3 注记·json counts 恒全量
        mt = os.path.join(tmp, "top.md")
        jt = os.path.join(tmp, "top.json")
        p = run(["--dir", d, "--json", jt, "--md", mt, "--top", "2"])
        assert p.returncode == 1, p.stdout
        md = io.open(mt, encoding="utf-8").read()
        assert "### family（--top 2 截断·余 3 族未示）" in md, md
        assert "| A-content-red | 1 |" in md and "| B-netred | 1 |" in md, md
        assert "| X-root | 1 |" not in md, "截断破（第 3 族不应示）"
        g = json.load(io.open(jt, encoding="utf-8"))
        assert len(g["counts"]["family"]) == 5, "json counts 应恒全量"
        print("矢量⑤ --top 截断（md 截 json 不截）: PASS")

        # 矢量⑥ 幂等：同输入两跑字节恒同（json＋md 双面）
        p = run(["--dir", d, "--json", jd, "--md", mdir])
        assert p.returncode == 1, p.stdout
        b1 = (io.open(jd, "rb").read(), io.open(mdir, "rb").read())
        p = run(["--dir", d, "--json", jd, "--md", mdir])
        b2 = (io.open(jd, "rb").read(), io.open(mdir, "rb").read())
        assert b1 == b2, "两跑字节漂移＝违例"
        print("矢量⑥ 幂等两跑字节恒同: PASS")

        # 矢量⑦ CLI 四码：0=help/干净流·1=坏行（矢量①③已证）·2=用法·9=缺
        clean = os.path.join(tmp, "clean.jsonl")
        dump_jsonl(clean, [ev(1, "2026-11-10T00:00:01Z", "ci-red",
                              "A-content-red", "fix-content", 111)])
        p = run(["--events", clean, "--json", os.path.join(tmp, "c.json")])
        assert p.returncode == 0, "干净流应 rc0 实得 %d" % p.returncode
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "双缺应 rc=2 实测 %d" % p.returncode
        p = run(["--events", mixed, "--dir", d])
        assert p.returncode == 2, "双给应 rc=2 实测 %d" % p.returncode
        p = run(["--events", clean, "--top", "-1"])
        assert p.returncode == 2, "--top 负应 rc=2 实测 %d" % p.returncode
        p = run(["--events", os.path.join(tmp, "nope.jsonl")])
        assert p.returncode == 9, "缺事件流应 rc=9 实测 %d" % p.returncode
        p = run(["--dir", os.path.join(tmp, "nope_dir")])
        assert p.returncode == 9, "缺目录应 rc=9 实测 %d" % p.returncode
        empty_d = os.path.join(tmp, "no_jsonl_dir")
        os.makedirs(empty_d)
        p = run(["--dir", empty_d])
        assert p.returncode == 9, "目录无 jsonl 应 rc=9 实测 %d" % p.returncode
        print("矢量⑦ CLI 四码（0/1/2/9·help0/干净0/坏行1/双缺双给负top2/缺9）"
              ": PASS")

        print("RENDER-EVENTS-SELFTEST PASS: 七矢量全过（三维统计/md 表成行＋"
              "转义截断/坏行容错 rc1/空文件 empty rc0/全坏行 empty rc1/--dir "
              "seq+ts 归位/--top 截断/幂等字节恒同/CLI 四码）")
        return 0
    except AssertionError as e:
        print("RENDER-EVENTS-SELFTEST FAIL: %s" % (e,), file=sys.stderr)
        return 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="cw_sentinel JSONL 事件流→markdown 台账＋rocqwash-"
                    "render-events/1 summary（纯渲染·零网络零重造）")
    ap.add_argument("--events", default=None, metavar="FILE.jsonl",
                    help="单份事件流 JSONL（rocqwash-sentinel-event/1·行序"
                         "即流序）")
    ap.add_argument("--dir", default=None, metavar="DIR",
                    help="目录全部 *.jsonl 合并（文件名典序读入·按 seq+ts "
                         "排序恢复全局序）")
    ap.add_argument("--md", default=None, metavar="out.md",
                    help="台账 markdown 出账")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="summary（rocqwash-render-events/1）出账")
    ap.add_argument("--top", type=int, default=0, metavar="N",
                    help="family 分布表截断行数（0=全量·缺省）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # 用法守卫（2）
    if args.events and args.dir:
        fail(2, "--events 与 --dir 互斥（双给即用法歧义·fail-loud 禁静默择一）")
    if not args.events and not args.dir:
        fail(2, "--events 与 --dir 必给其一（双缺无输入面）")
    if args.top < 0:
        fail(2, "--top 须 ≥0（0=全量缺省）·实得 %d" % args.top)

    # 读入（缺输入面 9·坏行响亮不中断）
    events, bad_lines, sources, input_desc = read_inputs(args)

    counts = tally(events)
    span = span_of(events)
    verdict = "ok" if events else "empty"
    summary = {"schema": SCHEMA,
               "events_total": len(events),
               "bad_lines": bad_lines,
               "verdict": verdict,
               "counts": counts,
               "span": span,
               "sources": sources}
    if args.json:
        write_json(args.json, summary)
    if args.md:
        write_text(args.md, render_md(events, counts, span, verdict,
                                      bad_lines, input_desc, args.top))

    span_txt = ("%s..%s" % (span["first_ts"], span["last_ts"])
                if span["first_ts"] else "无ts")
    print("RENDER-EVENTS: verdict=%s events_total=%d bad_lines=%d span=%s "
          "sources=%d md=%s json=%s"
          % (verdict, len(events), bad_lines, span_txt, len(sources),
             args.md or "-", args.json or "-"))
    # 0=零坏行（ok/empty 皆 0 如实）·1=bad_lines>0（数据残缺·出账已照常）
    sys.exit(1 if bad_lines else 0)


if __name__ == "__main__":
    main()
