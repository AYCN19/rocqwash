#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""baseline_diff.py — 两份堵账基线对比→堵账增减报告（rocqwash tools/·20261111
工装席铸·纯 JSON 逻辑）

输入两份 unclog --audit 堵账基线（schema rocqwash-unclog/1·audit 形·argv 序＝
旧→新·时间序由调用方自保证），出「堵账增减报告」：

  1 账面自洽预检（fail-loud 形坏 rc=2·拒判不出账）：schema＝rocqwash-unclog/1
    ＋final.red_files 字符串列表无重＋final.wall_count≡|wall|＋audit 形全检
    （final.verdict=audit·mode.audit=true·rounds 单轮·probe_summary 红账≡
    final 红账·chain_top 在）——手编账/混入账零容忍·染污对比不出账。
  2 候选面对齐：candidates_key 四元组（mode.source／args.src／args.candidates
    ／args.chain_ledgers）两账逐项比对——任一异即 verdict=incomparable 如实
    拒判（new/resolved/persistent 恒空·score_delta=null·rc=1 响亮——跨候选
    集的增减是伪信号·禁硬凑）。非 audit 形（闭环活跑报告混入）同判
    incomparable 并列明理由。args 其余键（timeout/rounds 等）不入候选面——
    调参不改候选集·增减仍可比。
  3 堵账增减（可比时）：堵账条目＝红账文件（final.red_files）∪墙账根
    （wall 键·各带 reason/detail）——
      new_blocks       新账有旧账无（红文件新堵／墙根新入·kind 分形）
      resolved_blocks  旧账有新账无（红文件清账／墙根出墙·墙根带旧因）
      persistent       两账同堵——墙根条目**按链根键·墙账逐因对齐**（old/new
                       的 reason·detail 逐项＋reason_changed/detail_changed——
                       因变即战役把墙挪了的响亮面·如 unprobed→self-unwashable）；
                       红文件条目附新账 chain_top 链根归因（dependents 全表查·
                       查无即 null——代差型/器因红/根出 TOP 榜者如实 null 禁猜）。
  4 score_delta＝{n_red, wall_count}（新−旧·红减为负）；verdict 只认红账：
    红减=improved／红增=degraded／同=stable（墙账增减入三清单不驱动 verdict
    ——红账是堵账主指标·判读单凭墙账会漏红文件面）。
  5 timing 段不入对比：耗时各段＝实测墙钟逐跑必异＝基线文件唯一非确定段
    （excluded_fields=["timing"]·stable 矢量以异 timing 双账实证「同输入
    重跑字节恒同」对 timing 之外全成立）。

输出确定性（sort_keys·同输入重跑 --json/--md 字节恒同·报告零墙钟零绝对路径
——路径只出基名·全路径走 stdout 响亮·chain_graph/unclog 同律）：
  --json report·schema=rocqwash-baseline-diff/1：
    {schema, old/new{path,verdict,audit_form,n_red,wall_count,red_files,
     wall_roots,candidates_key}, comparable, incomparable_reasons?,
     new_blocks[], resolved_blocks[], persistent[], score{old,new},
     score_delta?（incomparable 时 null）, excluded_fields, verdict}
    verdict ∈ improved|degraded|stable|incomparable。
  --md 同报告 markdown（人类判读面·含 timing 注记与退出码口径·detail 截断
    100 字·管柱转义）。

用法（零网络零编译纯 JSON 逻辑·两入参只读·唯一写盘面＝显式 --json/--md 出账）：
  python3 tools/baseline_diff.py OLD.json NEW.json [--json out.json] [--md out.md]
  python3 tools/baseline_diff.py --selftest

退出码：0=improved/stable；1=degraded/incomparable（红是数据非器红·响亮
stdout·verdict 在账在屏——基线回退/不可判都是判读面要接的信号）；2=用法错/
输入形坏（schema 不对/段缺失/账面自洽破）；9=路径缺失。--selftest：0=全过/
2=断言失败。

配套规程：examples/baselines/README.md（基线入仓·命名 audit-<域>-<yyyymmdd>.json·
真树干跑产·timing 注记）。
"""
import argparse
import io
import json
import os
import sys

PROG = "baseline_diff"
SCHEMA = "rocqwash-baseline-diff/1"
UNCLOG_SCHEMA = "rocqwash-unclog/1"
# 数据 verdict → 退出码（红是数据非器红·响亮 stdout·unclog VERDICT_EXIT 同律）
VERDICT_EXIT = {"improved": 0, "stable": 0, "degraded": 1, "incomparable": 1}
# 基线唯一非确定段（实测墙钟·逐跑必异）不入对比——报告内显式在册
EXCLUDED_FIELDS = ["timing"]
# 候选面四元组（candidates_key）逐项比对字段·任一异即 incomparable
CK_FIELDS = (("source", "候选面 source"), ("src", "候选树 src"),
             ("candidates", "候选清单 candidates"),
             ("chain_ledgers", "链台账 chain_ledgers"))
CLIP_MD = 100  # --md 表格 detail 截断宽（防长账冲表·确定性截断）


class FormError(Exception):
    """输入形坏（rc=2·fail-loud 拒判不出账）。"""


class MissingPath(Exception):
    """输入路径缺失（rc=9·fail-loud 不模拟）。"""


# ---- 账载入＋账面自洽预检 ------------------------------------------------------

def load_baseline(path, tag):
    """读一份堵账基线 → 账 dict（缺件 rc=9·JSON 解析失败 rc=2·fail-loud）。"""
    if not os.path.isfile(path):
        raise MissingPath("%s账文件缺失: %s" % (tag, path))
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            rep = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise FormError("%s账 JSON 解析失败: %s（%s）" % (tag, path, e))
    return account_of(rep, path, tag)


def account_of(rep, path, tag):
    """账面结构校验（fail-loud 形坏）＋堵账抽取。

    自洽校验（手编账/混入账零容忍）：final.red_files 字符串列表无重·
    final.wall_count≡|wall|·audit 形（verdict=audit＋mode.audit）时 rounds
    单轮·probe_summary 红账≡final 红账·chain_top 列表在。堵账＝红账文件
    （去重排序）∪墙账根（{reason,detail} 抽取）·candidates_key＝候选面
    四元组。"""
    where = "%s账 %s" % (tag, os.path.basename(path))
    if not isinstance(rep, dict):
        raise FormError("%s 形坏：顶层非 JSON object" % where)
    if rep.get("schema") != UNCLOG_SCHEMA:
        raise FormError("%s 形坏：schema=%r 非 %s（本器只对比 unclog 堵账基线）"
                        % (where, rep.get("schema"), UNCLOG_SCHEMA))
    mode, args = rep.get("mode"), rep.get("args")
    wall, final, rounds = rep.get("wall"), rep.get("final"), rep.get("rounds")
    if not isinstance(mode, dict):
        raise FormError("%s 形坏：mode 段缺失" % where)
    if not isinstance(args, dict):
        raise FormError("%s 形坏：args 段缺失" % where)
    if not isinstance(wall, dict) or \
            not all(isinstance(v, dict) for v in wall.values()):
        raise FormError("%s 形坏：wall 段缺失或值非 object" % where)
    if not isinstance(rounds, list) or not rounds:
        raise FormError("%s 形坏：rounds 段缺失或空" % where)
    if not isinstance(final, dict):
        raise FormError("%s 形坏：final 段缺失" % where)
    red_raw = final.get("red_files")
    if not isinstance(red_raw, list) or \
            not all(isinstance(x, str) for x in red_raw):
        raise FormError("%s 形坏：final.red_files 缺失或非字符串列表" % where)
    if len(set(red_raw)) != len(red_raw):
        raise FormError("%s 形坏：final.red_files 有重（账面自洽破）" % where)
    wc = final.get("wall_count")
    if not isinstance(wc, int) or isinstance(wc, bool) or wc != len(wall):
        raise FormError("%s 形坏：final.wall_count=%r ≠ |wall|=%d（账面自洽破）"
                        % (where, wc, len(wall)))
    verdict = final.get("verdict")
    if not isinstance(verdict, str):
        raise FormError("%s 形坏：final.verdict 缺失" % where)
    audit_form = (verdict == "audit" and mode.get("audit") is True)
    chain_top = []
    if audit_form:
        if len(rounds) != 1:
            raise FormError("%s 形坏：audit 形单轮·rounds=%d" % (where, len(rounds)))
        r0 = rounds[0]
        ps = r0.get("probe_summary") if isinstance(r0, dict) else None
        if not isinstance(ps, dict):
            raise FormError("%s 形坏：audit 形须 rounds[0].probe_summary 在" % where)
        ps_red = ps.get("red_files")
        if not isinstance(ps_red, list) or ps.get("n_red") != len(red_raw) \
                or set(ps_red) != set(red_raw):
            raise FormError("%s 形坏：probe_summary 红账与 final.red_files 不一致"
                            "（账面自洽破）" % where)
        ct = r0.get("chain_top")
        if not isinstance(ct, list) or not all(isinstance(t, dict) for t in ct):
            raise FormError("%s 形坏：audit 形须 rounds[0].chain_top 列表" % where)
        chain_top = ct
    red = sorted(set(red_raw))
    return {
        "path": os.path.basename(path),
        "verdict": verdict,
        "audit_form": audit_form,
        "mode_audit": mode.get("audit"),
        "n_red": len(red),
        "wall_count": len(wall),
        "red_files": red,
        "wall": {k: {"reason": v.get("reason"), "detail": v.get("detail")}
                 for k, v in wall.items()},
        "wall_roots": sorted(wall),
        "chain_top": chain_top,
        "candidates_key": {
            "source": mode.get("source"),
            "src": args.get("src"),
            "candidates": args.get("candidates"),
            "chain_ledgers": list(args.get("chain_ledgers") or []),
        },
    }


# ---- 对比本体（纯 JSON 逻辑·确定性·零墙钟）------------------------------------

def comparability_reasons(old, new):
    """可比性预检 → 理由列表（空＝可比）。audit 形两判＋候选面四元组逐项
    比对——候选集不同即 incomparable 如实·禁跨集硬凑 delta。"""
    rs = []
    if not old["audit_form"]:
        rs.append("旧账非 audit 基线形（final.verdict=%s·mode.audit=%r）"
                  "——本器只对比 unclog --audit 产堵账基线"
                  % (old["verdict"], old["mode_audit"]))
    if not new["audit_form"]:
        rs.append("新账非 audit 基线形（final.verdict=%s·mode.audit=%r）"
                  "——本器只对比 unclog --audit 产堵账基线"
                  % (new["verdict"], new["mode_audit"]))
    for field, label in CK_FIELDS:
        vo, vn = old["candidates_key"][field], new["candidates_key"][field]
        if vo != vn:
            rs.append("%s 异：旧 %r ≠ 新 %r（候选集不同即 incomparable 如实）"
                      % (label, vo, vn))
    return rs


def entries_of(acc):
    """账 → 堵账条目 dict[（kind,key)]→entry：red-file 条目 {kind,key}·
    wall-root 条目 {kind,key,reason,detail}（墙账因面随条走）。"""
    out = {}
    for k in acc["red_files"]:
        out[("red-file", k)] = {"kind": "red-file", "key": k}
    for root in acc["wall_roots"]:
        e = acc["wall"][root]
        out[("wall-root", root)] = {"kind": "wall-root", "key": root,
                                    "reason": e["reason"],
                                    "detail": e["detail"]}
    return out


def sorted_entries(entries):
    """条目 → (kind,key) 典序列表（确定性·同键 red-file 先于 wall-root）。"""
    return [entries[k] for k in sorted(entries)]


def root_of(chain_top, name):
    """红文件 → 链根归因：chain_top 各根 dependents 全表查·首中即根。查无
    即 None（代差型/器因红/根出 TOP 榜——如实 null 禁猜）。"""
    for t in chain_top or []:
        if name in (t.get("dependents") or []):
            return t.get("lib")
    return None


def persistent_of(old, new, old_e, new_e):
    """两账同堵条目（(kind,key) 典序）：墙根**按链根键·墙账逐因对齐**（old/
    new 的 reason·detail＋reason_changed/detail_changed）·红文件附新账
    chain_top 链根归因。"""
    out = []
    for k in sorted(set(old_e) & set(new_e)):
        kind, key = k
        if kind == "wall-root":
            o, n = old_e[k], new_e[k]
            out.append({"kind": "wall-root", "key": key,
                        "old": {"reason": o["reason"], "detail": o["detail"]},
                        "new": {"reason": n["reason"], "detail": n["detail"]},
                        "reason_changed": o["reason"] != n["reason"],
                        "detail_changed": o["detail"] != n["detail"]})
        else:
            out.append({"kind": "red-file", "key": key,
                        "root": root_of(new["chain_top"], key)})
    return out


def diff(old, new):
    """两账 → diff 报告 dict（schema rocqwash-baseline-diff/1·零墙钟）。
    不可比 → 三清单恒空·score_delta=null·verdict=incomparable（如实）；
    可比 → 堵账三清单＋score_delta＋verdict（只认红账 n_red 增减）。"""
    reasons = comparability_reasons(old, new)
    rep = {
        "schema": SCHEMA,
        "old": summary_of(old),
        "new": summary_of(new),
        "comparable": not reasons,
        "incomparable_reasons": reasons,
        "excluded_fields": list(EXCLUDED_FIELDS),
        "verdict": None,
        "score": {"old": score_of(old), "new": score_of(new)},
    }
    if reasons:
        rep.update({"new_blocks": [], "resolved_blocks": [], "persistent": [],
                    "score_delta": None, "verdict": "incomparable"})
        return rep
    old_e, new_e = entries_of(old), entries_of(new)
    rep["new_blocks"] = sorted_entries(
        {k: e for k, e in new_e.items() if k not in old_e})
    rep["resolved_blocks"] = sorted_entries(
        {k: e for k, e in old_e.items() if k not in new_e})
    rep["persistent"] = persistent_of(old, new, old_e, new_e)
    d_red = new["n_red"] - old["n_red"]
    d_wall = new["wall_count"] - old["wall_count"]
    rep["score_delta"] = {"n_red": d_red, "wall_count": d_wall}
    rep["verdict"] = ("improved" if d_red < 0
                      else "degraded" if d_red > 0 else "stable")
    return rep


def score_of(acc):
    """账 → score 摘要（红账数＋墙根数·堵账两量面）。"""
    return {"n_red": acc["n_red"], "wall_count": acc["wall_count"]}


def summary_of(acc):
    """账 → 报告 old/new 摘要（路径只出基名·红账全列·墙根键列·候选面）。"""
    return {"path": acc["path"], "verdict": acc["verdict"],
            "audit_form": acc["audit_form"], "n_red": acc["n_red"],
            "wall_count": acc["wall_count"], "red_files": acc["red_files"],
            "wall_roots": acc["wall_roots"],
            "candidates_key": acc["candidates_key"]}


# ---- markdown 出账（人类判读面·确定性）----------------------------------------

def _md_cell(s):
    """md 表格单元格：None→—·管柱转义·超长截断（确定性）。"""
    if s is None:
        return "—"
    s = str(s).replace("|", "\\|")
    if len(s) > CLIP_MD:
        s = s[:CLIP_MD - 3] + "..."
    return s


def _delta_table(rep):
    """score 表（incomparable 时 Δ 列如实 —）。"""
    o, n = rep["old"], rep["new"]
    sd = rep["score_delta"]
    d_red = _md_cell(sd["n_red"]) if sd else "—"
    d_wall = _md_cell(sd["wall_count"]) if sd else "—"
    return ["| 指标 | 旧账 | 新账 | Δ（新−旧） |", "|---|---|---|---|",
            "| n_red | %d | %d | %s |" % (o["n_red"], n["n_red"], d_red),
            "| wall_count | %d | %d | %s |" % (o["wall_count"], n["wall_count"],
                                               d_wall)]


def report_md(rep):
    """diff 报告 → markdown（确定性·同输入字节恒同）。"""
    o, n = rep["old"], rep["new"]
    lines = ["# Baseline Diff（堵账基线对比·%s）" % rep["schema"], ""]
    lines.append("- 旧账: %s（verdict=%s·audit 形=%s·红 %d·墙 %d）"
                 % (o["path"], o["verdict"], str(o["audit_form"]).lower(),
                    o["n_red"], o["wall_count"]))
    lines.append("- 新账: %s（verdict=%s·audit 形=%s·红 %d·墙 %d）"
                 % (n["path"], n["verdict"], str(n["audit_form"]).lower(),
                    n["n_red"], n["wall_count"]))
    ck = n["candidates_key"]
    lines.append("- 候选面: source=%s src=%s candidates=%s chain_ledgers=%s"
                 % (ck["source"], ck["src"], ck["candidates"],
                    ",".join(ck["chain_ledgers"]) or "-"))
    lines.append("")
    lines.append("**verdict: %s**" % rep["verdict"])
    if rep["verdict"] == "incomparable":
        lines.append("")
        lines.append("如实拒判（delta 恒空·score_delta=null）——理由：")
        lines.extend("- %s" % r for r in rep["incomparable_reasons"])
    else:
        sd = rep["score_delta"]
        lines.append("")
        lines.append("score_delta: n_red %+d（%d→%d）· wall_count %+d（%d→%d）"
                     % (sd["n_red"], o["n_red"], n["n_red"],
                        sd["wall_count"], o["wall_count"], n["wall_count"]))
    lines.append("")
    lines.append("## 新堵 new_blocks（%d）" % len(rep["new_blocks"]))
    lines.append("")
    lines.append("| kind | key | reason | detail |")
    lines.append("|---|---|---|---|")
    for e in rep["new_blocks"]:
        lines.append("| %s | %s | %s | %s |"
                     % (e["kind"], _md_cell(e["key"]),
                        _md_cell(e.get("reason")), _md_cell(e.get("detail"))))
    lines.append("")
    lines.append("## 清账 resolved_blocks（%d）" % len(rep["resolved_blocks"]))
    lines.append("")
    lines.append("| kind | key | reason | detail |")
    lines.append("|---|---|---|---|")
    for e in rep["resolved_blocks"]:
        lines.append("| %s | %s | %s | %s |"
                     % (e["kind"], _md_cell(e["key"]),
                        _md_cell(e.get("reason")), _md_cell(e.get("detail"))))
    lines.append("")
    lines.append("## 仍堵 persistent（%d）·按链根键·墙账逐因对齐"
                 % len(rep["persistent"]))
    lines.append("")
    lines.append("| kind | key | 旧因 | 新因 | 变化 | 链根归因 |")
    lines.append("|---|---|---|---|---|---|")
    for e in rep["persistent"]:
        if e["kind"] == "wall-root":
            chg = "+".join([t for t, c in (("reason变", e["reason_changed"]),
                                           ("detail变", e["detail_changed"]))
                            if c]) or "无"
            lines.append("| %s | %s | %s | %s | %s | — |"
                         % (e["kind"], _md_cell(e["key"]),
                            _md_cell(e["old"]["reason"]),
                            _md_cell(e["new"]["reason"]), chg))
        else:
            lines.append("| %s | %s | — | — | 仍红 | %s |"
                         % (e["kind"], _md_cell(e["key"]),
                            _md_cell(e.get("root"))
                            if e.get("root") is not None else "—（报告面不可归因）"))
    lines.append("")
    lines.append("## score（Δ＝新−旧·红减为负）")
    lines.append("")
    lines.extend(_delta_table(rep))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("注：")
    lines.append("- timing 段（耗时各段·实测墙钟逐跑必异）不入对比＝基线文件"
                 "唯一非确定段（excluded_fields=%s）。" % json.dumps(rep["excluded_fields"]))
    lines.append("- verdict 只认红账 n_red 增减（红减 improved／红增 degraded／"
                 "同 stable）；墙账增减入上三清单不驱动 verdict。")
    lines.append("- 退出码：0=improved/stable·1=degraded/incomparable"
                 "（红是数据非器红·响亮 stdout）·2=输入形坏·9=路径缺失。")
    lines.append("")
    return "\n".join(lines)


# ---- stdout 响亮进度 -----------------------------------------------------------

def _brief(entries, persistent=False, limit=8):
    """条目列表 → 单行简报（超 8 项缩尾·确定性）。"""
    if not entries:
        return "-"
    parts = []
    for e in entries[:limit]:
        if e["kind"] == "wall-root":
            tag = "·因变" if (e.get("reason_changed")
                              or e.get("detail_changed")) else ""
            parts.append("%s(wall-root%s)" % (e["key"], tag))
        elif persistent and e.get("root") is not None:
            parts.append("%s(red-file→%s)" % (e["key"], e["root"]))
        else:
            parts.append("%s(red-file)" % e["key"])
    if len(entries) > limit:
        parts.append("…+%d" % (len(entries) - limit))
    return ", ".join(parts)


def print_report(rep, old_path, new_path):
    """响亮 stdout 进度（全路径走 stdout·verdict 收尾）。"""
    o, n = rep["old"], rep["new"]
    print("=== BASELINE-DIFF 堵账基线对比 ===")
    print("old: %s 红 %d 墙 %d (verdict=%s·audit 形=%s)"
          % (old_path, o["n_red"], o["wall_count"], o["verdict"],
             str(o["audit_form"]).lower()))
    print("new: %s 红 %d 墙 %d (verdict=%s·audit 形=%s)"
          % (new_path, n["n_red"], n["wall_count"], n["verdict"],
             str(n["audit_form"]).lower()))
    ck = n["candidates_key"]
    print("候选面: source=%s src=%s candidates=%s chain_ledgers=%s"
          % (ck["source"], ck["src"], ck["candidates"],
             ",".join(ck["chain_ledgers"]) or "-"))
    if rep["verdict"] == "incomparable":
        print("INCOMPARABLE: 如实拒判（%d 项理由·delta 恒空·score_delta=null）:"
              % len(rep["incomparable_reasons"]))
        for r in rep["incomparable_reasons"]:
            print("  - %s" % r)
    else:
        print("新堵 %d: %s" % (len(rep["new_blocks"]), _brief(rep["new_blocks"])))
        print("清账 %d: %s" % (len(rep["resolved_blocks"]),
                               _brief(rep["resolved_blocks"])))
        print("仍堵 %d: %s" % (len(rep["persistent"]),
                               _brief(rep["persistent"], persistent=True)))
    sd = rep["score_delta"]
    if sd is None:
        print("VERDICT: incomparable（候选集异等如实拒判）")
    else:
        print("VERDICT: %s（n_red %d→%d Δ%+d·wall_count %d→%d Δ%+d）"
              % (rep["verdict"], o["n_red"], n["n_red"], sd["n_red"],
                 o["wall_count"], n["wall_count"], sd["wall_count"]))


# ---- selftest（内嵌矢量组·tmp 合成账·零网络零编译零触真仓）---------------------

def _mk_audit(red, wall, chain_top, src="src", candidates=None, ledgers=None,
              timing=None, verdict="audit", audit_mode=True, extra_args=None):
    """合成一份 unclog --audit 形基线（fixture 级·形同 unclog.py:794 run_audit
    产出·字段取自其 report 构造）。"""
    red = sorted(set(red))
    source = "chain-ledgers" if ledgers else "probe"
    args = {"rounds": 5, "top": 25, "scan_ids": None, "apply": False,
            "loop": False, "loop_max": 0, "interval": 60, "sleep_scale": 1.0,
            "probe_resume": False, "src": src, "world": None, "repo_path": ".",
            "candidates": candidates, "chain_ledgers": list(ledgers or []),
            "pack": "cure_pack.json", "injector": None, "guard": None,
            "rocq_cmd": None, "timeout": 900}
    if extra_args:
        args.update(extra_args)
    ps = {"source": "merge" if ledgers else "probe",
          "n_records": len(red) + 2, "n_red": len(red), "red_files": red,
          "ledgers": list(ledgers) if ledgers else ["audit.probe.json"]}
    return {"schema": UNCLOG_SCHEMA,
            "mode": {"source": source, "apply": False, "audit": audit_mode,
                     "injector": False, "loop": False},
            "args": args,
            "rounds": [{"round": 1, "probe_summary": ps,
                        "chain_top": chain_top, "root": None, "root_file": None,
                        "cure": None, "cures_planned": 0, "cures_applied": 0,
                        "rescan": None, "resprobe": None}],
            "wall": wall,
            "timing": timing or {"enumerate_s": 0.001, "manifest_s": 0.002,
                                 "probe_chain_s": 0.003, "total_s": 0.004},
            "final": {"verdict": verdict, "rounds_run": 1, "red_files": red,
                      "cures_planned_total": 0, "cures_applied_total": 0,
                      "wall_count": len(wall)},
            "verdict": verdict}


def _top1(lib, dependents, washable=True):
    """chain_top 条目（chain_graph libs 形·self 三态）。"""
    return {"lib": lib, "n": len(dependents), "dependents": list(dependents),
            "self": {"probed": True, "rc": 0 if washable else 1,
                     "verdict": "GREEN" if washable else "RED-OTHER",
                     "washable": washable}}


def _wall1(root, reason, detail):
    """wall 条目（unclog wall_add 形）。"""
    return {"root": root, "reason": reason, "detail": detail}


def selftest():
    """内嵌矢量组（tmp 合成基线·零触真仓零网络零编译）：improved（红减）/
    degraded（红增＋墙因变）/stable（同·异 timing 实证不入对比）＋幂等字节
    恒同＋零写输入/incomparable（候选集异＋非 audit 形）＋形坏 rc2／缺件 rc9/
    md 输出/CLI 四码。"""
    import shutil
    import subprocess
    import tempfile

    def run(argv):
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         PROG + ".py")] + argv,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def dump(path, obj):
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1, sort_keys=True)

    tmp = tempfile.mkdtemp(prefix="rocqwash_baslinediff_self_")
    try:
        W_UNPROBED = _wall1("Y", "unprobed", "根件未入候选集（UNPROBED·候补探）")
        W_SELFUN = _wall1("Y", "self-unwashable",
                          "根件自身被阻 rc=1 verdict=RED-OTHER（链中环·先治根的因）")
        W_FROZEN = _wall1("Z", "frozen-in-service",
                          "根名/根件撞 frozen8 在册（预检红拒·人审域）")

        # 矢量① improved（红减）：红 3→1·墙账同（Y 同因同 detail·逐因对齐
        #   reason_changed=False）·清账 C1/D1·仍堵 B 归因链根 A·rc=0
        old1 = _mk_audit(["B", "C1", "D1"], {"Y": W_SELFUN},
                         [_top1("A", ["B", "C1", "D1"])],
                         candidates="cands.tsv")
        new1 = _mk_audit(["B"], {"Y": W_SELFUN},
                         [_top1("A", ["B", "C1", "D1"])],
                         candidates="cands.tsv")
        fo, fn = os.path.join(tmp, "audit-wash-20261101.json"), \
            os.path.join(tmp, "audit-wash-20261111.json")
        dump(fo, old1)
        dump(fn, new1)
        j1 = os.path.join(tmp, "diff1.json")
        p = run([fo, fn, "--json", j1])
        assert p.returncode == 0, "红减应 rc=0 实测 %d\n%s" % (p.returncode, p.stdout)
        r = json.load(io.open(j1, encoding="utf-8"))
        assert r["schema"] == SCHEMA and r["verdict"] == "improved", r["verdict"]
        assert r["comparable"] is True and r["incomparable_reasons"] == [], r
        assert r["excluded_fields"] == ["timing"], r
        assert r["score_delta"] == {"n_red": -2, "wall_count": 0}, r["score_delta"]
        assert r["new_blocks"] == [], r["new_blocks"]
        assert r["resolved_blocks"] == [{"kind": "red-file", "key": "C1"},
                                        {"kind": "red-file", "key": "D1"}], \
            r["resolved_blocks"]
        assert r["persistent"] == [
            {"kind": "red-file", "key": "B", "root": "A"},
            {"kind": "wall-root", "key": "Y",
             "old": {"reason": "self-unwashable",
                     "detail": W_SELFUN["detail"]},
             "new": {"reason": "self-unwashable",
                     "detail": W_SELFUN["detail"]},
             "reason_changed": False, "detail_changed": False}], r["persistent"]
        assert r["old"]["path"] == "audit-wash-20261101.json" \
            and r["new"]["path"] == "audit-wash-20261111.json", "路径应只出基名"
        assert "VERDICT: improved" in p.stdout, p.stdout
        print("矢量① improved（红减·清账 C1/D1·墙因对齐无变·rc0）: PASS")

        # 矢量② degraded（红增）：红 1→3·墙 Y 因变（unprobed→self-unwashable）
        #   ＋新墙根 Z（frozen）·新堵含红文件与墙根两形·rc=1（红是数据非器红）
        old2 = _mk_audit(["B"], {"Y": W_UNPROBED}, [_top1("A", ["B"])],
                         candidates="cands.tsv")
        new2 = _mk_audit(["B", "C1", "D1"], {"Y": W_SELFUN, "Z": W_FROZEN},
                         [_top1("A", ["B", "C1", "D1"])],
                         candidates="cands.tsv")
        fo2, fn2 = os.path.join(tmp, "old2.json"), os.path.join(tmp, "new2.json")
        dump(fo2, old2)
        dump(fn2, new2)
        j2 = os.path.join(tmp, "diff2.json")
        p = run([fo2, fn2, "--json", j2])
        assert p.returncode == 1, "红增应 rc=1 实测 %d\n%s" % (p.returncode, p.stdout)
        r2 = json.load(io.open(j2, encoding="utf-8"))
        assert r2["verdict"] == "degraded", r2["verdict"]
        assert r2["score_delta"] == {"n_red": 2, "wall_count": 1}, r2["score_delta"]
        assert r2["new_blocks"] == [
            {"kind": "red-file", "key": "C1"},
            {"kind": "red-file", "key": "D1"},
            {"kind": "wall-root", "key": "Z", "reason": "frozen-in-service",
             "detail": W_FROZEN["detail"]}], r2["new_blocks"]
        assert r2["resolved_blocks"] == [], r2["resolved_blocks"]
        assert r2["persistent"] == [
            {"kind": "red-file", "key": "B", "root": "A"},
            {"kind": "wall-root", "key": "Y",
             "old": {"reason": "unprobed", "detail": W_UNPROBED["detail"]},
             "new": {"reason": "self-unwashable", "detail": W_SELFUN["detail"]},
             "reason_changed": True, "detail_changed": True}], r2["persistent"]
        assert "INCOMPARABLE" not in p.stdout and "VERDICT: degraded" in p.stdout, \
            p.stdout
        print("矢量② degraded（红增＋墙因变 unprobed→self-unwashable＋新墙根·rc1）: PASS")

        # 矢量③ stable（同）＋timing 不入对比＋幂等字节恒同＋零写输入：
        #   双账同堵账·timing 异（total_s 1.111 vs 9.999）·args 异 timeout——
        #   均不入候选面不入对比 → stable·链根归因 B→A/C1→null 两面全证·
        #   重跑 --json/--md 字节恒同·输入零被动
        old3 = _mk_audit(["B", "C1"], {"Y": W_SELFUN},
                         [_top1("A", ["C1"], washable=False)],
                         candidates="cands.tsv",
                         timing={"enumerate_s": 0.5, "manifest_s": 0.6,
                                 "probe_chain_s": 1.0, "total_s": 1.111},
                         extra_args={"timeout": 900})
        new3 = _mk_audit(["B", "C1"], {"Y": W_SELFUN},
                         [_top1("A", ["C1"], washable=False)],
                         candidates="cands.tsv",
                         timing={"enumerate_s": 3.5, "manifest_s": 0.9,
                                 "probe_chain_s": 5.4, "total_s": 9.999},
                         extra_args={"timeout": 1200})
        fo3, fn3 = os.path.join(tmp, "old3.json"), os.path.join(tmp, "new3.json")
        dump(fo3, old3)
        dump(fn3, new3)
        j3, m3 = os.path.join(tmp, "diff3.json"), os.path.join(tmp, "diff3.md")
        cmd3 = [fo3, fn3, "--json", j3, "--md", m3]
        raw_o, raw_n = io.open(fo3, "rb").read(), io.open(fn3, "rb").read()
        p = run(cmd3)
        assert p.returncode == 0, p.stdout
        r3 = json.load(io.open(j3, encoding="utf-8"))
        assert r3["verdict"] == "stable", r3["verdict"]
        assert r3["score_delta"] == {"n_red": 0, "wall_count": 0}, r3["score_delta"]
        assert r3["new_blocks"] == [] and r3["resolved_blocks"] == [], r3
        assert r3["persistent"] == [
            {"kind": "red-file", "key": "B", "root": None},
            {"kind": "red-file", "key": "C1", "root": "A"},
            {"kind": "wall-root", "key": "Y",
             "old": {"reason": "self-unwashable", "detail": W_SELFUN["detail"]},
             "new": {"reason": "self-unwashable", "detail": W_SELFUN["detail"]},
             "reason_changed": False, "detail_changed": False}], r3["persistent"]
        assert "timing" not in r3, "timing 段不得入对比报告"
        # 幂等：重跑字节恒同（json＋md 双面）
        before_j, before_m = io.open(j3, "rb").read(), io.open(m3, "rb").read()
        p = run(cmd3)
        assert p.returncode == 0, p.stdout
        assert io.open(j3, "rb").read() == before_j, "json 字节漂移＝违例"
        assert io.open(m3, "rb").read() == before_m, "md 字节漂移＝违例"
        # 零写输入：两份基线字节被动即违例
        assert io.open(fo3, "rb").read() == raw_o \
            and io.open(fn3, "rb").read() == raw_n, "基线输入被写＝违例"
        print("矢量③ stable（同·异 timing 异 timeout 不入对比·json/md 幂等"
              "字节恒同·输入零被动）: PASS")

        # 矢量④ incomparable（候选集异如实）：候选清单异 → rc1·delta 恒空·
        #   score_delta=null·理由列明四元组异项；非 audit 形混入同判 incomparable
        fn4 = os.path.join(tmp, "new4_othercands.json")
        dump(fn4, _mk_audit(["B", "C1"], {"Y": W_SELFUN},
                            [_top1("A", ["B", "C1"], washable=False)],
                            candidates="other.tsv"))
        j4 = os.path.join(tmp, "diff4.json")
        p = run([fo3, fn4, "--json", j4])
        assert p.returncode == 1, "候选集异应 rc=1 实测 %d\n%s" \
            % (p.returncode, p.stdout)
        r4 = json.load(io.open(j4, encoding="utf-8"))
        assert r4["verdict"] == "incomparable" and r4["comparable"] is False, r4
        assert any("candidates" in x for x in r4["incomparable_reasons"]), \
            r4["incomparable_reasons"]
        assert r4["new_blocks"] == [] and r4["resolved_blocks"] == [] \
            and r4["persistent"] == [], "不可比 delta 应恒空"
        assert r4["score_delta"] is None, r4["score_delta"]
        assert r4["score"]["old"]["n_red"] == 2, "账面摘要应仍在（如实）"
        # ④b 非 audit 形混入（闭环活跑报告·verdict=wall）
        fn4b = os.path.join(tmp, "new4b_closedloop.json")
        dump(fn4b, _mk_audit(["B", "C1"], {"Y": W_SELFUN},
                             [_top1("A", ["B", "C1"], washable=False)],
                             verdict="wall", audit_mode=False))
        j4b = os.path.join(tmp, "diff4b.json")
        p = run([fo3, fn4b, "--json", j4b])
        assert p.returncode == 1, p.stdout
        r4b = json.load(io.open(j4b, encoding="utf-8"))
        assert r4b["verdict"] == "incomparable" and \
            any("audit 基线形" in x for x in r4b["incomparable_reasons"]), \
            r4b["incomparable_reasons"]
        assert r4b["score_delta"] is None, r4b["score_delta"]
        print("矢量④ incomparable（候选清单异 rc1·delta 恒空 score_delta=null·"
              "非 audit 形如实拒判）: PASS")

        # 矢量⑤ md 输出：improved 账 --md 落盘·判读面全段在（verdict/三清单/
        #   score 表/timing 注记/退出码口径）·基名在册·管柱转义防冲表
        m5 = os.path.join(tmp, "diff1.md")
        p = run([fo, fn, "--md", m5])
        assert p.returncode == 0, p.stdout
        md = io.open(m5, encoding="utf-8").read()
        assert "verdict: improved" in md and "新堵 new_blocks（0）" in md \
            and "清账 resolved_blocks（2）" in md \
            and "仍堵 persistent（2）·按链根键·墙账逐因对齐" in md, md[:400]
        assert "| n_red | 3 | 1 | -2 |" in md, "score 表 Δ 面缺失\n" + md
        assert "timing 段" in md and "不入对比" in md, "timing 注记缺失"
        assert "audit-wash-20261101.json" in md \
            and "audit-wash-20261111.json" in md, "基名应入 md"
        assert "退出码：0=improved/stable" in md, "退出码口径缺失"
        print("矢量⑤ md 输出（verdict/三清单/score 表/timing 注记/退出码口径）: PASS")

        # 矢量⑥ CLI 四码＋形坏拒判不出账：--help 0／未知形参 2／缺参 2／
        #   形坏（schema 错/账面自洽破）2 且 --json 不落盘／缺件 9
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "缺两账应 rc=2 实测 %d" % p.returncode
        p = run([fo])
        assert p.returncode == 2, "缺新账应 rc=2 实测 %d" % p.returncode
        fbad_schema = os.path.join(tmp, "bad_schema.json")
        dump(fbad_schema, {"schema": "rocqwash-other/1", "verdict": "audit"})
        jbad = os.path.join(tmp, "bad_out.json")
        p = run([fo, fbad_schema, "--json", jbad])
        assert p.returncode == 2 and "FAIL-LOUD" in p.stdout, p.stdout
        assert not os.path.exists(jbad), "形坏拒判应零出账（fail-loud）"
        fbad_integ = os.path.join(tmp, "bad_integ.json")
        bad = _mk_audit(["B"], {"Y": W_SELFUN}, [_top1("A", ["B"])])
        bad["final"]["wall_count"] = 5  # 账面自洽破：|wall|=1≠5
        dump(fbad_integ, bad)
        p = run([fo, fbad_integ])
        assert p.returncode == 2 and "账面自洽破" in p.stdout, p.stdout
        fbad_json = os.path.join(tmp, "bad.json")
        with io.open(fbad_json, "w", encoding="utf-8") as fh:
            fh.write("{非 JSON 垃圾")
        p = run([fo, fbad_json])
        assert p.returncode == 2 and "解析失败" in p.stdout, p.stdout
        p = run([fo, os.path.join(tmp, "nope.json")])
        assert p.returncode == 9, "缺新账文件应 rc=9 实测 %d" % p.returncode
        p = run([os.path.join(tmp, "nope.json"), fn])
        assert p.returncode == 9, "缺旧账文件应 rc=9 实测 %d" % p.returncode
        print("矢量⑥ CLI 四码（0/2/9·形坏拒判零出账·账面自洽拦手编）: PASS")

        print("BASELINE-DIFF-SELFTEST PASS: 六矢量全过（improved 红减/degraded"
              " 红增＋墙因变/stable 同＋timing 不入对比＋幂等字节恒同＋零写输入/"
              "incomparable 候选集异＋非 audit 形/md 输出/CLI 四码＋形坏拒判）")
        return 0
    except AssertionError as e:
        print("BASELINE-DIFF-SELFTEST FAIL: %s" % e)
        return 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="两份 unclog --audit 堵账基线对比→堵账增减报告"
                               "（new_blocks/resolved_blocks/persistent·"
                               "score_delta·verdict 四态·--md 报告）")
    ap.add_argument("old", metavar="OLD.json",
                    help="旧堵账基线（argv 序＝旧→新·时间序调用方自保证）")
    ap.add_argument("new", metavar="NEW.json", help="新堵账基线")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="diff 报告 JSON 出账（schema rocqwash-baseline-diff/1）")
    ap.add_argument("--md", default=None, metavar="out.md",
                    help="diff 报告 markdown 出账（人类判读面）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        old_acc = load_baseline(args.old, "旧")
        new_acc = load_baseline(args.new, "新")
    except MissingPath as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    except FormError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    rep = diff(old_acc, new_acc)
    print_report(rep, args.old, args.new)

    for path, text in ((args.json, json.dumps(rep, ensure_ascii=False,
                                               indent=1, sort_keys=True) + "\n"),
                       (args.md, report_md(rep))):
        if path:
            try:
                with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
                print("%s -> %s" % ("json" if path == args.json else "md", path))
            except OSError as e:
                print("FAIL-LOUD: 出账写盘失败: %s（%s）" % (path, e),
                      file=sys.stderr)
                sys.exit(9)

    sys.exit(VERDICT_EXIT[rep["verdict"]])


if __name__ == "__main__":
    main()
