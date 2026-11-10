#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cw_doctor.py — 综合体检器·四域聚合（rocqwash tools/·v37 工装席任务书·
20261111 入账）

一键全面健康评估：四域逐域 subprocess 编排**既有一器**（编排而非重造——先读
各器 CLI 与 JSON schema 再接线·器红/形坏 fail-loud·零新引擎），聚合为综合
健康分 0-100＋per-domain verdict＋advice 处置清单（每非绿域一条·指向对应器）：
  ①环境域(40)＝subprocess toolchain_dyld_doctor（worker 缺省探测：flag/env
    ROCWASH_ROCQWORKER/判例机缺省·器内自决）→ 报告 verdict healthy|
    missing-libs|worker-missing → healthy=100 分·余=0 分（红是数据非器红）。
  ②网络域(20)＝subprocess net_probe --rounds 1 --interval 0（缺省四端点）→
    报告 verdict all-up|partial|all-down（无 --stable-window 时 net_probe
    exit 0 仅＝探完成——可达性读报告 verdict 字段非退出码）→ score=可达率×100。
  ③注册域(25)＝--registry PATH 显传（缺册 fail-loud 9）> env CW_SET/
    ConstructiveWorld_Live/order.txt 探测（缺册如实 skip）> 全无 skip →
    锚正典形审计：#R<序>-<md5_8> 形合规率（正典指纹＝md5 前 8 位小写 hex·
    registry_union.md5_8_of 产物形；ANCHOR_RE 1:1 承 registry_union.py:81；
    注释行/空行不审计——key_of 同款语义；无锚表体行计入 no_anchor 不入合规
    率分母；非形清单帽 20·总数如实）→ score=合规率×100。
  ④堵账域(15)＝--src DIR（缺省跳过）＋--sample N（缺省 0=不抽样→域如实
    skip；域活须 --src 且 --sample>0）→ 全树典序枚举 .v（unclog 同款）→
    --sample N 等距抽样（i*total//N 索引·N≥树大＝全量普查）→ 候选 TSV →
    subprocess probe_engine --fresh（真探必 --world·--guard 缺省
    ConstructiveWorld cpu_guard.sh 温控——sanctioned 缺省承
    toolchain_dyld_doctor 同款·可 --guard 覆盖）→ 台账 → chain_graph --top 1
    恒真跑（纯 stdlib 零编译零网络·真编排非傀儡·unclog 同款）→ 红账率
    （stats.rc1∪stats.other）→ score=(1-红账率)×100 → 有缺库链根时附 TOP
    一名（top_order 首名·n＋self 可洗性）。

综合分＝Σ(域分×权重)/Σ(在域权重)（skip 域权重剔除归一·round 2 位）；
verdict healthy(≥90)｜degraded(<90)。advice：env→toolchain_dyld_doctor 溯源
还原（只建议·禁代执行）·net→net_probe --stable-window 双探稳窗·registry→
registry_union --reanchor 重锚正典形·clog→unclog 闭环疏通·skip 域→显传
对应开关后重跑体检。

离线可测（v37 纪律·全 subprocess 层 canned 注入）：--injector 场景 JSON
（DIR/scenario.json）＝{引擎键: {"rc": int, "stdout": str, "report": dict}}·
键集固定 dyld/net/probe（wash_shape Injector 同款契约·键不识 2）·canned 表
须覆盖本次将发的全部器件调用（dyld/net 恒需·probe 须于堵账域活时——缺键
9·绝不静默走真器真网·cw_sentinel 同律）。canned rc 语义随真器：dyld rc∈
{0,1,9} 带报告可解析（1/9=数据红）·rc=2/报告缺/形坏=器红 9；net/probe
rc≠0=器红 9。probe canned 台账原样落 workdir 后仍喂真 chain_graph（真编排
非傀儡·unclog 同款）。本器自身零 sleep 零 loop（--sleep-scale 无涉·net 轮
间隔恒 0）。

确定性：report 无墙钟字段·路径一律 basename（绝对路径证据在 stdout 与
workdir 工件）·sort_keys 落盘·同输入同环境重跑字节级恒同。

用法（全部路径参数化·除 --guard sanctioned 缺省外零硬编码）：
  python3 tools/cw_doctor.py [--json OUT] [--workdir DIR]
      [--registry PATH] [--src DIR --sample N [--world DIR]]
      [--worker PATH] [--donor DIR] [--endpoints URL[,URL...]]
      [--guard PATH] [--guard-reg DIR] [--guard-maxwait S] [--timeout S]
      [--rocq-cmd TPL] [--injector DIR]
  python3 tools/cw_doctor.py --selftest

退出码：0=healthy（综合分 ≥90）；1=degraded（<90·红响亮出账——域红是数据
非器红）；2=用法错（argparse/--sample 负/--timeout 非/injector 场景形坏·键
不识）；9=缺（器件缺失/--registry 显传缺册/--src 缺目录/--world 真探缺/
--guard 缺/--src 零候选/injector 场景缺·canned 未覆盖/子进程器红/报告
schema 不识/注册册解码失败）。--json report schema=rocqwash-cwdoctor/1。
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

PROG = "cw_doctor"
SCHEMA = "rocqwash-cwdoctor/1"

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
TOOL_DYLD = os.path.join(TOOLS_DIR, "toolchain_dyld_doctor.py")
TOOL_NET = os.path.join(TOOLS_DIR, "net_probe.py")
TOOL_PROBE = os.path.join(REPO_ROOT, "wash", "probe_engine.py")
TOOL_CHAIN = os.path.join(TOOLS_DIR, "chain_graph.py")

SCHEMA_DYLD = "rocqwash-dyld-doctor/1"
SCHEMA_NET = "rocqwash-net-probe/1"
SCHEMA_PROBE = "rocqwash-probe-ledger/1"
SCHEMA_CHAIN = "rocqwash-chain-graph/1"

DOMAIN_ORDER = ("env", "net", "registry", "clog")
WEIGHTS = {"env": 40, "net": 20, "registry": 25, "clog": 15}
HEALTHY_MIN = 90.0
NON_FORM_CAP = 20

# 锚形 1:1 承 registry_union.py:81 ANCHOR_RE；正典形＝#R<序>-<md5 前 8 位
# 小写 hex（registry_union.md5_8_of=hexdigest()[:8] 产物形·:80 注记「重锚后
# 恒为 #R<序号>-<md5 前 8 hex>」）
ANCHOR_RE = re.compile(r"#(R\d+(?:-[0-9A-Fa-f]+)?)")
CANON_ANCHOR_RE = re.compile(r"R\d+-[0-9a-f]{8}")

ENV_REGISTRY = "CW_SET"
REGISTRY_REL = ("ConstructiveWorld_Live", "order.txt")
# sanctioned 判例机缺省（toolchain_dyld_doctor.py DEFAULT_GUARD 同款·任务书
# 钦定路径·--guard 可覆盖）
DEFAULT_GUARD = "/Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh"


class UsageError(Exception):
    """用法错/场景形坏（exit 2）。"""


class MissingInput(Exception):
    """输入缺失（exit 9）。"""


class ToolError(Exception):
    """编排器件器红/报告形坏（exit 9·fail-loud 禁静默降级）。"""


# ---- 小件（确定性 helpers·unclog/wash_shape 同款本地副本·无包结构不互 import）--

def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def basename_of(p):
    return os.path.basename(p.rstrip(os.sep)) if p else p


def dump_json(obj, path):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)


def load_json(path, what):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (ValueError, UnicodeDecodeError, OSError) as e:
        raise ToolError("%s JSON 形坏: %s (%s)" % (what, path, e))


def run_py(tool_path, cli):
    """python3 -B <tool> <cli> 子进程单点（stdout+stderr 合流·unclog 同款）。
    缺件→9。"""
    if not os.path.isfile(tool_path):
        raise MissingInput("工具链件缺失: %s" % tool_path)
    p = subprocess.run([sys.executable, "-B", tool_path] + list(cli),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p.returncode, out


def write_cands_tsv(path, pairs):
    """候选清单 TSV（件名/md5 双列·probe_engine 必需列形制·unclog 同款）。"""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("件名\tmd5\n")
        for name, md5 in pairs:
            fh.write("%s\t%s\n" % (name, md5))


def enumerate_tree(src):
    """--src 全树枚举 *.v → [(件名(相对路径·/分隔·去 .v), md5)]（确定性·
    双排序·unclog 同款）。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames.sort()
        for fn in sorted(filenames):
            if fn.endswith(".v"):
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, src).replace(os.sep, "/")
                out.append((rel[:-2], md5_of(fp)))
    return out


def sample_pairs(pairs, n):
    """确定性等距抽样：典序枚举上取 i*total//N 索引（span 长 total>n 必含
    n 的倍数→索引严格递增不重复）；N≥total 时全量普查（不抽样）。"""
    total = len(pairs)
    if n >= total:
        return list(pairs)
    out, seen = [], set()
    for i in range(n):
        idx = i * total // n
        if idx not in seen:
            seen.add(idx)
            out.append(pairs[idx])
    return out


# ---- 注入点：子进程调用层罐装（v37 离线可测纪律·wash_shape Injector 同款）----

class Injector(object):
    """--injector DIR：子进程调用层罐装（DIR/scenario.json·unclog 同款形）。
    场景 JSON {引擎键: {"rc": int, "stdout": str, "report": dict}}；键集＝
    dyld/net/probe；命中键的器件调用恒定返付 canned·不真 subprocess。canned
    表须覆盖本次将发的全部器件调用（run() 预检·缺键 9——绝不静默走真器真
    网·cw_sentinel 同律）。"""

    KEYS = ("dyld", "net", "probe")

    def __init__(self, dirpath):
        sj = os.path.join(dirpath, "scenario.json")
        if not os.path.isfile(sj):
            raise MissingInput("injector 场景缺失: %s" % sj)
        try:
            with io.open(sj, "r", encoding="utf-8") as fh:
                scen = json.load(fh)
        except Exception as e:
            raise UsageError("injector 场景 JSON 畸形: %s (%s)" % (sj, e))
        if not isinstance(scen, dict):
            raise UsageError("injector 场景须 dict: %s" % sj)
        bad = [k for k in scen if k not in self.KEYS]
        if bad:
            raise UsageError("injector 场景键不识（须 %s）: %s"
                             % (",".join(self.KEYS), sorted(bad)))
        for k, ent in sorted(scen.items()):
            rc = ent.get("rc") if isinstance(ent, dict) else None
            if (not isinstance(ent, dict)
                    or not isinstance(rc, int) or isinstance(rc, bool)
                    or not isinstance(ent.get("stdout", ""), str)
                    or not isinstance(ent.get("report", {}), dict)):
                raise UsageError("injector 罐装项 %r 形坏（须 {rc:int, "
                                 "stdout?:str, report?:dict}）: %r" % (k, ent))
        self.scen = scen

    def require(self, keys):
        """canned 全覆盖预检（缺键 9·防半罐装静默走真器真网）。"""
        miss = [k for k in keys if k not in self.scen]
        if miss:
            raise MissingInput("injector canned 未覆盖 %s（canned 表须全覆盖"
                               "将发的器件调用·绝不静默走真器真网）"
                               % ",".join(miss))

    def take(self, key):
        ent = self.scen[key]
        return ent.get("rc", 0), ent.get("stdout", ""), ent.get("report")


# ---- ①环境域 -----------------------------------------------------------------

def domain_env(args, workdir, inj):
    """①环境域：subprocess toolchain_dyld_doctor --json（worker 缺省探测器
    内自决·--worker/--donor 可透传）。verdict healthy=100 分·余=0 分；
    rc∈{0,1,9} 带报告＝数据（1/9 数据红）·rc=2/报告缺/形坏=器红 9。"""
    report_path = os.path.join(workdir, "dyld.json")
    if inj is not None:
        rc, out, rep = inj.take("dyld")
        dump_json(rep, report_path)
    else:
        cli = ["--json", report_path]
        if args.worker:
            cli += ["--worker", args.worker]
        if args.donor:
            cli += ["--donor", args.donor]
        rc, out = run_py(TOOL_DYLD, cli)
        rep = load_json(report_path, "dyld 报告") \
            if os.path.isfile(report_path) else None
    if rep is None:
        raise ToolError("toolchain_dyld_doctor 器红 rc=%d（报告未落盘）: %s"
                        % (rc, out[-300:]))
    if rc not in (0, 1, 9):
        raise ToolError("toolchain_dyld_doctor 器红 rc=%d: %s" % (rc, out[-300:]))
    if not isinstance(rep, dict) or rep.get("schema") != SCHEMA_DYLD:
        raise ToolError("dyld 报告 schema 不识: %r（期待 %s）"
                        % (rep.get("schema") if isinstance(rep, dict) else rep,
                           SCHEMA_DYLD))
    verdict = rep.get("verdict")
    if verdict not in ("healthy", "missing-libs", "worker-missing"):
        raise ToolError("dyld 报告 verdict 不识: %r" % (verdict,))
    refs = rep.get("external_refs")
    if not isinstance(refs, list):
        raise ToolError("dyld 报告 external_refs 形坏: %r" % (refs,))
    for e in refs:
        if not isinstance(e, dict) or not isinstance(e.get("path"), str) \
                or not isinstance(e.get("exists"), bool):
            raise ToolError("dyld 报告 external_refs 项形坏: %r" % (e,))
    missing = [e["path"] for e in refs if not e["exists"]]
    return {"status": "ok", "weight": WEIGHTS["env"],
            "tool": "tools/toolchain_dyld_doctor.py", "rc": rc,
            "worker": basename_of(rep.get("worker")), "verdict": verdict,
            "score": 100.0 if verdict == "healthy" else 0.0,
            "external_refs": len(refs), "missing_refs": missing}


# ---- ②网络域 -----------------------------------------------------------------

def domain_net(args, workdir, inj):
    """②网络域：subprocess net_probe --rounds 1 --interval 0（缺省四端点·
    --endpoints 可覆盖）。无 --stable-window 时 net_probe exit 0 仅＝探完成
    ——可达性读报告 verdict 字段；score=可达率×100。"""
    report_path = os.path.join(workdir, "net.json")
    if inj is not None:
        rc, out, rep = inj.take("net")
        dump_json(rep, report_path)
    else:
        cli = ["--rounds", "1", "--interval", "0", "--json", report_path]
        if args.endpoints:
            cli += ["--endpoints", args.endpoints]
        rc, out = run_py(TOOL_NET, cli)
        rep = load_json(report_path, "net 报告") \
            if os.path.isfile(report_path) else None
    if rc != 0:
        raise ToolError("net_probe 器红 rc=%d: %s" % (rc, out[-300:]))
    if not isinstance(rep, dict) or rep.get("schema") != SCHEMA_NET:
        raise ToolError("net 报告 schema 不识: %r（期待 %s）"
                        % (rep.get("schema") if isinstance(rep, dict) else rep,
                           SCHEMA_NET))
    verdict = rep.get("verdict")
    if verdict not in ("all-up", "partial", "all-down"):
        raise ToolError("net 报告 verdict 不识: %r" % (verdict,))
    rounds = rep.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        raise ToolError("net 报告 rounds 形坏: %r" % (rounds,))
    entries = []
    for r in rounds:
        if not isinstance(r, dict) or not isinstance(r.get("endpoints"), list):
            raise ToolError("net 报告轮形坏: %r" % (r,))
        for e in r["endpoints"]:
            if not isinstance(e, dict) or not isinstance(e.get("url"), str) \
                    or not isinstance(e.get("ok"), bool):
                raise ToolError("net 报告端点项形坏: %r" % (e,))
            entries.append(e)
    total = len(entries)
    if total == 0:
        raise ToolError("net 报告零端点探针")
    ups = sum(1 for e in entries if e["ok"])
    rate = float(ups) / total
    return {"status": "ok", "weight": WEIGHTS["net"],
            "tool": "tools/net_probe.py", "verdict": verdict,
            "score": round(rate * 100.0, 2), "up": ups, "total": total,
            "rate": round(rate, 4),
            "down_endpoints": [e["url"] for e in entries if not e["ok"]]}


# ---- ③注册域 -----------------------------------------------------------------

def resolve_registry(args):
    """注册册三择：--registry 显传（缺册 fail-loud 9·显传输入禁静默 skip）
    > env CW_SET 探测（缺册如实 skip）> 全无 skip。
    → (path|None, source|None, skip_reason|None)。"""
    if args.registry:
        if not os.path.isfile(args.registry):
            raise MissingInput("--registry 显传册缺失: %s" % args.registry)
        return args.registry, "flag", None
    cw = os.environ.get(ENV_REGISTRY)
    if cw:
        cand = os.path.join(cw, *REGISTRY_REL)
        if os.path.isfile(cand):
            return cand, "CW_SET", None
        return None, None, ("env %s=%s 下缺册（%s 不在盘）"
                            % (ENV_REGISTRY, cw, "/".join(REGISTRY_REL)))
    return None, None, "--registry 未显传且 env %s 未设" % ENV_REGISTRY


def audit_registry(path):
    """册锚正典形审计（纯读零子进程）：非空非注释行（registry_union key_of
    同款语义——首 # 前空＝注释/空行跳过）上取 ANCHOR_RE 首锚（anchor_of 同款
    逐行首中）→ 正典形 #R<序>-<md5_8> 全match判定。非形清单帽 NON_FORM_CAP
    条·总数如实。"""
    try:
        with io.open(path, "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise MissingInput("注册册不可读/解码失败: %s (%s)" % (path, e))
    lines = [ln.rstrip("\r\n").strip() for ln in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    scanned = anchored = canonical = no_anchor = non_form_total = 0
    non_form = []
    for idx, ln in enumerate(lines, start=1):
        if not ln:
            continue
        if not ln.split("#", 1)[0].strip():
            continue          # 注释行（首 # 前空·key_of 同款语义·非表体）
        scanned += 1
        m = ANCHOR_RE.search(ln)
        if m is None:
            no_anchor += 1
            continue
        anchored += 1
        if CANON_ANCHOR_RE.fullmatch(m.group(1)):
            canonical += 1
        else:
            non_form_total += 1
            if len(non_form) < NON_FORM_CAP:
                non_form.append({"line_no": idx, "anchor": m.group(0),
                                 "line": ln[:120]})
    rate = (float(canonical) / anchored) if anchored else 0.0
    return {"lines_scanned": scanned, "anchored": anchored,
            "canonical": canonical, "rate": rate, "no_anchor": no_anchor,
            "non_form_total": non_form_total, "non_form": non_form}


def domain_registry(reg_path, reg_source, skip_reason):
    """③注册域：锚正典形审计→合规率×100。anchored==0（册内零锚）＝rate 0
    如实 non-canonical；skip 域权重剔除归一。"""
    if reg_path is None:
        return {"status": "skip", "weight": WEIGHTS["registry"],
                "reason": skip_reason}
    st = audit_registry(reg_path)
    rate = st["rate"]
    out = {"status": "ok", "weight": WEIGHTS["registry"],
           "tool": "tools/registry_union.py", "source": reg_source,
           "registry": basename_of(reg_path),
           "verdict": "healthy"
                      if (st["anchored"] and st["canonical"] == st["anchored"])
                      else "non-canonical",
           "score": round(rate * 100.0, 2),
           "lines_scanned": st["lines_scanned"], "anchored": st["anchored"],
           "canonical": st["canonical"], "rate": round(rate, 4),
           "no_anchor": st["no_anchor"],
           "non_form_total": st["non_form_total"], "non_form": st["non_form"]}
    return out


# ---- ④堵账域 -----------------------------------------------------------------

def domain_clog(args, workdir, inj):
    """④堵账域：--src 且 --sample>0 才活（缺省 0=不抽样→如实 skip）。
    全树典序枚举→等距抽样→候选 TSV→probe_engine --fresh（真探必 --world·
    --guard 温控）→台账→chain_graph --top 1 恒真跑→红账率→TOP 一名。"""
    if not args.src:
        return {"status": "skip", "weight": WEIGHTS["clog"],
                "reason": "--src 未给（堵账域缺省跳过）"}
    if args.sample <= 0:
        return {"status": "skip", "weight": WEIGHTS["clog"],
                "reason": "--src 在册但 --sample 0（缺省不抽样·真探须 "
                          "--sample N>0）"}
    ledger_path = os.path.join(workdir, "probe.json")
    graph_path = os.path.join(workdir, "chain.json")
    source = "injector" if inj is not None else "probe"
    out = ""
    if inj is not None:
        rc, out, rep = inj.take("probe")
        dump_json(rep, ledger_path)   # canned 台账原样落 workdir·仍喂真 chain_graph
    else:
        pairs = enumerate_tree(args.src)
        if not pairs:
            raise MissingInput("--src 全树枚举零 .v 候选: %s" % args.src)
        pairs = sample_pairs(pairs, args.sample)
        tsv = os.path.join(workdir, "cands.tsv")
        write_cands_tsv(tsv, pairs)
        print("堵账候选面: 全树枚举抽样 %d 件（--sample %d）-> %s"
              % (len(pairs), args.sample, tsv))
        if not args.world:
            raise MissingInput("--world 必给（堵账真探针；离线请 --injector）")
        if not os.path.isfile(args.guard):
            raise MissingInput("--guard 缺失: %s" % args.guard)
        cli = ["--candidates", tsv, "--src", args.src,
               "--world", args.world, "--out", ledger_path,
               "--logdir", os.path.join(workdir, "probe-logs"),
               "--timeout", str(args.timeout), "--fresh",
               "--guard", args.guard, "--guard-reg", args.guard_reg,
               "--guard-maxwait", str(args.guard_maxwait)]
        if args.rocq_cmd:
            cli += ["--rocq-cmd", args.rocq_cmd]
        rc, out = run_py(TOOL_PROBE, cli)
    if rc != 0:
        raise ToolError("probe_engine 器红 rc=%d: %s" % (rc, out[-300:]))
    ledger = load_json(ledger_path, "probe 台账")
    if not isinstance(ledger, dict) or ledger.get("schema") != SCHEMA_PROBE \
            or not isinstance(ledger.get("records"), dict):
        raise ToolError("probe 台账 schema/形不识: %r（期待 %s＋records dict）"
                        % (ledger.get("schema")
                           if isinstance(ledger, dict) else ledger,
                           SCHEMA_PROBE))
    # 链根图恒真跑（纯 stdlib·零编译零网络·真编排非傀儡）·TOP 一名
    rc2, out2 = run_py(TOOL_CHAIN, [ledger_path, "--json", graph_path,
                                    "--top", "1"])
    if rc2 != 0:
        raise ToolError("chain_graph 器红 rc=%d: %s" % (rc2, out2[-300:]))
    graph = load_json(graph_path, "链根图")
    if not isinstance(graph, dict) or graph.get("schema") != SCHEMA_CHAIN:
        raise ToolError("链根图 schema 不识: %r（期待 %s）"
                        % (graph.get("schema")
                           if isinstance(graph, dict) else graph,
                           SCHEMA_CHAIN))
    stats = graph.get("stats")
    if not isinstance(stats, dict) or not isinstance(stats.get("merged_total"),
                                                     int):
        raise ToolError("链根图 stats 形坏: %r" % (stats,))
    merged = stats["merged_total"]
    red = sorted(set(stats.get("rc1") or []) | set(stats.get("other") or []))
    red_rate = (float(len(red)) / merged) if merged else 0.0
    top1 = None
    for lib in list(graph.get("top_order") or [])[:1]:
        e = (graph.get("libs") or {}).get(lib)
        if e:
            top1 = {"lib": lib, "n": e.get("n"),
                    "self": dict(e.get("self") or {})}
    return {"status": "ok", "weight": WEIGHTS["clog"],
            "tool": "tools/unclog.py", "source": source,
            "sample": args.sample, "probed": merged,
            "verdict": "healthy" if not red else "clogged",
            "score": round((1.0 - red_rate) * 100.0, 2),
            "red": len(red), "red_rate": round(red_rate, 4),
            "red_files": red, "chain_top1": top1}


# ---- 聚合：综合分＋verdict＋advice ---------------------------------------------

def compute_score(domains):
    """综合分＝Σ(域分×权重)/Σ(在域权重)（skip 域权重剔除归一·round 2 位）。
    env/net 恒跑→分母 ≥60；全 skip 为内部不变量炸（fail-loud）。"""
    num = 0.0
    den = 0
    for d in DOMAIN_ORDER:
        dom = domains[d]
        if dom["status"] != "ok":
            continue
        num += dom["score"] * WEIGHTS[d]
        den += WEIGHTS[d]
    if den <= 0:
        raise UsageError("内部不变量炸：四域全 skip（env/net 恒跑不应发生）")
    return round(num / den, 2), den


def advice_of(domains):
    """advice 清单：每非绿域一条处置建议（固定域序·指向对应器·skip 域指
    开关）。全绿→空表。"""
    out = []
    env = domains["env"]
    if env["status"] == "ok" and env["verdict"] != "healthy":
        out.append({"domain": "env",
                    "tool": "tools/toolchain_dyld_doctor.py",
                    "text": "环境域 verdict=%s（外部硬引用缺 %d 条）——运行 "
                            "python3 tools/toolchain_dyld_doctor.py "
                            "[--donor DIR] 溯源缺失库并按 restore 建议手工"
                            "还原（只建议·禁代执行）"
                            % (env["verdict"], len(env["missing_refs"]))})
    net = domains["net"]
    if net["status"] == "ok" and net["verdict"] != "all-up":
        out.append({"domain": "net", "tool": "tools/net_probe.py",
                    "text": "网络域 %s（%d/%d up）——发射前运行 python3 "
                            "tools/net_probe.py --rounds 2 --stable-window "
                            "取双探稳窗"
                            % (net["verdict"], net["up"], net["total"])})
    reg = domains["registry"]
    if reg["status"] == "skip":
        out.append({"domain": "registry", "tool": "--registry",
                    "text": "注册域 skip（%s）——显传 --registry PATH（如 "
                            "$CW_SET/ConstructiveWorld_Live/order.txt）后"
                            "重跑体检" % reg["reason"]})
    elif reg["verdict"] != "healthy":
        out.append({"domain": "registry", "tool": "tools/registry_union.py",
                    "text": "注册域锚形合规率 %.4f（非形 %d 条·帽 %d 已列）"
                            "——运行 python3 tools/registry_union.py "
                            "--reanchor <件名> --anchor-src <DIR> 重锚 "
                            "#R<序>-<md5_8> 正典形"
                            % (reg["rate"], reg["non_form_total"],
                               NON_FORM_CAP)})
    clog = domains["clog"]
    if clog["status"] == "skip":
        out.append({"domain": "clog", "tool": "--src",
                    "text": "堵账域 skip（%s）——显传 --src DIR --sample N "
                            "真探（受 cpu_guard 温控）后重跑体检"
                            % clog["reason"]})
    elif clog["verdict"] != "healthy":
        top1 = clog.get("chain_top1")
        top_txt = ("TOP1=%s(n=%d)" % (top1["lib"], top1["n"])) if top1 \
            else "TOP1=无（红无缺库链根）"
        out.append({"domain": "clog", "tool": "tools/unclog.py",
                    "text": "堵账域红账率 %.4f（红 %d/%d·链根 %s）——运行 "
                            "python3 tools/unclog.py --src <DIR> "
                            "--world <DIR> 闭环疏通"
                            % (clog["red_rate"], clog["red"],
                               clog["probed"], top_txt)})
    return out


# ---- 总控 ---------------------------------------------------------------------

def args_summary(args, reg_source):
    """args 摘要（路径一律 basename——绝对路径不进 report·确定性纪律）。"""
    return {"sample": args.sample,
            "src": basename_of(args.src),
            "world": basename_of(args.world) if args.world else None,
            "registry": basename_of(args.registry) if args.registry else None,
            "registry_source": reg_source,
            "worker": basename_of(args.worker) if args.worker else None,
            "donor": basename_of(args.donor) if args.donor else None,
            "guard": basename_of(args.guard),
            "injector": basename_of(args.injector) if args.injector else None,
            "endpoints_source": "flag" if args.endpoints else "default"}


def run(args):
    """总控：值校验（2）→器件先验（9）→注册册三择→canned 全覆盖预检→
    四域逐域跑→综合分→verdict→advice→report（0=healthy/1=degraded）。"""
    # 值校验（2）
    if args.sample < 0:
        raise UsageError("--sample 须≥0（0=不抽样）实测 %d" % args.sample)
    if args.timeout < 1:
        raise UsageError("--timeout 须≥1 实测 %d" % args.timeout)
    if args.guard_maxwait < 1:
        raise UsageError("--guard-maxwait 须≥1 实测 %d" % args.guard_maxwait)
    # 器件先验（9·编排零新引擎——四器在位性先验）
    for label, p in (("toolchain_dyld_doctor", TOOL_DYLD),
                     ("net_probe", TOOL_NET),
                     ("probe_engine", TOOL_PROBE),
                     ("chain_graph", TOOL_CHAIN)):
        if not os.path.isfile(p):
            raise MissingInput("器件缺失: %s (%s)" % (label, p))
    if args.src is not None and not os.path.isdir(args.src):
        raise MissingInput("--src 目录缺失: %s" % args.src)
    if args.world is not None and not os.path.isdir(args.world):
        raise MissingInput("--world 目录缺失: %s" % args.world)
    reg_path, reg_source, reg_skip = resolve_registry(args)
    clog_active = bool(args.src) and args.sample > 0
    inj = Injector(args.injector) if args.injector else None
    if inj is not None:
        inj.require(["dyld", "net"] + (["probe"] if clog_active else []))
        print("injector: %s（canned %s·子进程调用层罐装不真 subprocess）"
              % (args.injector, ",".join(sorted(inj.scen))))
    # workdir
    if args.workdir:
        os.makedirs(args.workdir, exist_ok=True)
        workdir = args.workdir
    else:
        workdir = tempfile.mkdtemp(prefix="rocqwash_cwdoctor_")
    print("workdir -> %s" % workdir)

    domains = {
        "env": domain_env(args, workdir, inj),
        "net": domain_net(args, workdir, inj),
        "registry": domain_registry(reg_path, reg_source, reg_skip),
        "clog": domain_clog(args, workdir, inj),
    }
    score, active_w = compute_score(domains)
    verdict = "healthy" if score >= HEALTHY_MIN else "degraded"
    advice = advice_of(domains)
    report = {"schema": SCHEMA, "verdict": verdict, "score": score,
              "healthy_min": HEALTHY_MIN, "weights": dict(WEIGHTS),
              "active_weight": active_w, "domains": domains,
              "advice": advice, "args": args_summary(args, reg_source)}

    # stdout 响亮（确定性域序）
    print("=== CW-DOCTOR（综合体检·四域聚合）===")
    for d in DOMAIN_ORDER:
        dom = domains[d]
        if dom["status"] == "skip":
            print("[%-8s] skip  weight=%d（%s）" % (d, dom["weight"],
                                                    dom["reason"]))
            continue
        print("[%-8s] ok    weight=%d verdict=%s score=%s"
              % (d, dom["weight"], dom["verdict"], dom["score"]))
        if d == "env":
            print("    worker=%s external=%d missing=%d"
                  % (dom["worker"], dom["external_refs"],
                     len(dom["missing_refs"])))
        elif d == "net":
            print("    up=%d/%d rate=%.4f down=%d"
                  % (dom["up"], dom["total"], dom["rate"],
                     len(dom["down_endpoints"])))
        elif d == "registry":
            print("    source=%s registry=%s anchored=%d/%d rate=%.4f "
                  "no_anchor=%d non_form=%d"
                  % (dom["source"], dom["registry"], dom["canonical"],
                     dom["anchored"], dom["rate"], dom["no_anchor"],
                     dom["non_form_total"]))
        elif d == "clog":
            top1 = dom["chain_top1"]
            print("    source=%s probed=%d red=%d rate=%.4f top1=%s"
                  % (dom["source"], dom["probed"], dom["red"],
                     dom["red_rate"],
                     ("%s(n=%d)" % (top1["lib"], top1["n"])) if top1
                     else "无"))
    print("--- 评分 ---")
    print("active weight %d/%d · SCORE=%s · verdict: %s"
          % (active_w, sum(WEIGHTS.values()), score, verdict))
    if advice:
        print("--- advice（每非绿域一条）---")
        for a in advice:
            print("  [%s] %s\n    -> %s" % (a["domain"], a["tool"],
                                            a["text"]))
    else:
        print("--- advice：全绿零处置 ---")
    if args.json:
        dump_json(report, args.json)
        print("json -> %s" % args.json)
    print("VERDICT: %s (exit %d)" % (verdict, 0 if verdict == "healthy" else 1))
    return 0 if verdict == "healthy" else 1


# ---- --selftest（内嵌冻结向量组·tmp fixture 树·全 subprocess 层 canned 注入）----

def selftest():
    """矢量组（tmp fixture＋injector 子进程调用层罐装·零真 otool 零真网络
    零真编译·chain_graph/注册审计真跑——纯 stdlib 零编译零网络）：
    V1 四域全绿 100 分（exit 0·advice 空·active weight 100）
    V2 环境红降分（missing-libs→env 0 分→60.0·degraded·advice 指 dyld）
    V3 注册缺册 skip 归一（CW_SET 剥离＋net partial→86.67·active weight 75·
       advice 含 net＋registry 两条）＋CW_SET 缺册如实 skip
    V4 堵账 TOP 注入（canned 红账 3/4→clog 25.0→88.75·chain TOP1=A(n=2)·
       advice 指 unclog）
    V5 advice 生成（V2/V3/V4 逐条断言·全绿空表已在 V1）
    V6 JSON 幂等（同场景两跑异 workdir 字节恒同）
    V7 CLI 四码（--help 0·--bogus 2·--sample 负 2·--registry 缺册 9·--src
       缺目录 9·--injector 场景缺 9·场景键不识 2·canned 未覆盖 9）
    V8 注册审计单元（混形 rate 2/6·注释/空行/无锚行计数·帽 25→20·7/8/9 位
       指纹与大写 hex 皆非形·零锚册·CW_SET 正探 source=CW_SET）
    """
    tmp = tempfile.mkdtemp(prefix="rocqwash_cwdoctor_self_")
    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, PROG + ".py")

    def run(aargs, env_extra=None, strip_cw=True):
        e = dict(os.environ)
        if strip_cw:
            e.pop("CW_SET", None)
        if env_extra:
            e.update(env_extra)
        p = subprocess.run([sys.executable, "-B", script] + list(aargs),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           env=e)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def wtext(path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def wjson(path, obj):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        dump_json(obj, path)

    def scenario(name, dyld_rep, net_rep, probe_rep=None):
        d = os.path.join(tmp, "inj_" + name)
        scen = {"dyld": {"rc": 0 if dyld_rep["verdict"] == "healthy" else 1,
                         "stdout": "", "report": dyld_rep},
                "net": {"rc": 0, "stdout": "", "report": net_rep}}
        if probe_rep is not None:
            scen["probe"] = {"rc": 0, "stdout": "", "report": probe_rep}
        wjson(os.path.join(d, "scenario.json"), scen)
        return d

    def rec0(f):
        return {"file": f, "md5": None, "rc": 0, "red": "", "missing": None,
                "red_class": None, "verdict": "RC0", "red_count": None,
                "md5_match": None}

    def rec1(f, lib):
        return {"file": f, "md5": None, "rc": 1,
                "red": "Error: Unable to locate library | %s (while searching"
                       " for a .vos file)." % lib,
                "missing": lib, "red_class": "MISSING_LIB",
                "verdict": "RED-MISSING_LIB", "red_count": None,
                "md5_match": None}

    # canned 报告（冻结向量·路径全假·零机器依赖）
    DYLD_OK = {"schema": SCHEMA_DYLD, "worker": "/fake/rocqworker",
               "external_refs": [
                   {"path": "/fake/Live/toolchain/gmp/lib/libgmp.10.dylib",
                    "exists": True},
                   {"path": "/fake/Live/toolchain/zmq/lib/libzmq.5.dylib",
                    "exists": True}],
               "verdict": "healthy"}
    DYLD_MISS = {"schema": SCHEMA_DYLD, "worker": "/fake/rocqworker",
                 "external_refs": [
                     {"path": "/fake/Live/toolchain/gmp/lib/libgmp.10.dylib",
                      "exists": False}],
                 "verdict": "missing-libs"}

    def net_rep(pairs):
        eps = [{"url": u, "http_code": (200 if ok else None), "ok": ok}
               for u, ok in pairs]
        ups = sum(1 for e in eps if e["ok"])
        verdict = "all-up" if ups == len(eps) else \
            ("all-down" if ups == 0 else "partial")
        return {"schema": SCHEMA_NET,
                "rounds": [{"at": "2026-11-11T00:00:00Z", "endpoints": eps}],
                "verdict": verdict}

    NET_UP = net_rep([("https://a.example", True), ("https://b.example", True),
                      ("https://c.example", True), ("https://d.example",
                                                    True)])
    NET_PART = net_rep([("https://a.example", True), ("https://b.example",
                                                      True),
                        ("https://c.example", False),
                        ("https://d.example", False)])

    def probe_rep(records):
        return {"schema": SCHEMA_PROBE, "n_records": len(records),
                "records": records}

    PROBE_GREEN = probe_rep({"A": rec0("A"), "B": rec0("B")})
    # 红账向量：A 可洗链根·B/C 缺 A·D 缺 B → TOP1=A(n=2)·红 3/4
    PROBE_RED = probe_rep({"A": rec0("A"), "B": rec1("B", "A"),
                           "C": rec1("C", "A"), "D": rec1("D", "B")})

    SCEN_OK = scenario("ok", DYLD_OK, NET_UP, PROBE_GREEN)
    SCEN_ENVRED = scenario("envred", DYLD_MISS, NET_UP, PROBE_GREEN)
    SCEN_NETPART = scenario("netpart", DYLD_OK, NET_PART, PROBE_GREEN)
    SCEN_CLOGRED = scenario("clogred", DYLD_OK, NET_UP, PROBE_RED)

    def make_registry(path, lines):
        wtext(path, "\n".join(lines) + "\n")
        return path

    REG_GREEN = make_registry(
        os.path.join(tmp, "reg_green.txt"),
        ["# 正典册 fixture（全 #R<序>-<md5_8> 形）",
         "S01_BaseRing.v#R0-d66910ab",
         "S02_Cauchy.v#R1-0123abcd",
         "S03_QExp.v#R2-deadbeef",
         ""])
    REG_MIX = make_registry(
        os.path.join(tmp, "reg_mix.txt"),
        ["A.v#R0-d66910ab",            # 正典
         "B.v#R1-0123abcd",            # 正典
         "C.v#R2",                     # 非形·裸序号
         "D.v#R3-abcdef",              # 非形·5 位
         "E.v#R4-D66910AB",            # 非形·大写 8 位（md5_8 恒小写）
         "F.v#R5-d66910abc",           # 非形·9 位
         "G.v",                        # 表体无锚→no_anchor
         "# 注释 #R9-d66910ab",         # 注释行→不审计
         ""])                          # 空行→不审计
    src_empty = os.path.join(tmp, "src_empty")
    os.makedirs(src_empty)

    try:
        # ---- V1 四域全绿 100 分 ----
        j1 = os.path.join(tmp, "v1.json")
        wd1 = os.path.join(tmp, "wd_v1a")
        p = run(["--json", j1, "--workdir", wd1, "--registry", REG_GREEN,
                 "--src", src_empty, "--sample", "2", "--injector", SCEN_OK])
        assert p.returncode == 0, p.stdout[-800:]
        rep = json.loads(io.open(j1, encoding="utf-8").read())
        assert rep["schema"] == SCHEMA and rep["verdict"] == "healthy", rep
        assert rep["score"] == 100.0 and rep["active_weight"] == 100, rep
        doms = rep["domains"]
        for d in DOMAIN_ORDER:
            assert doms[d]["status"] == "ok", (d, doms[d])
        assert doms["env"]["verdict"] == "healthy" and \
            doms["env"]["score"] == 100.0, doms["env"]
        assert doms["net"]["verdict"] == "all-up" and \
            doms["net"]["up"] == 4, doms["net"]
        assert doms["registry"]["verdict"] == "healthy" and \
            doms["registry"]["rate"] == 1.0, doms["registry"]
        assert doms["clog"]["verdict"] == "healthy" and \
            doms["clog"]["red"] == 0 and \
            doms["clog"]["chain_top1"] is None, doms["clog"]
        assert rep["advice"] == [], rep["advice"]
        assert "SCORE=100.0" in p.stdout, p.stdout[-400:]
        # 域名固定四键（确定性形制）
        assert sorted(doms) == ["clog", "env", "net", "registry"], sorted(doms)

        # ---- V2 环境红降分（0×40 → 60.0·degraded·advice 指 dyld）----
        j2 = os.path.join(tmp, "v2.json")
        p = run(["--json", j2, "--registry", REG_GREEN, "--src", src_empty,
                 "--sample", "2", "--injector", SCEN_ENVRED])
        assert p.returncode == 1, p.stdout[-800:]
        rep = json.loads(io.open(j2, encoding="utf-8").read())
        assert rep["verdict"] == "degraded" and rep["score"] == 60.0, rep
        env = rep["domains"]["env"]
        assert env["verdict"] == "missing-libs" and env["score"] == 0.0, env
        assert env["missing_refs"] == \
            ["/fake/Live/toolchain/gmp/lib/libgmp.10.dylib"], env
        assert rep["advice"][0]["domain"] == "env" and \
            rep["advice"][0]["tool"] == "tools/toolchain_dyld_doctor.py", \
            rep["advice"]
        assert "toolchain_dyld_doctor" in p.stdout, p.stdout[-400:]

        # ---- V3 注册缺册 skip 归一（CW_SET 剥离·net partial→86.67）----
        j3 = os.path.join(tmp, "v3.json")
        p = run(["--json", j3, "--src", src_empty, "--sample", "2",
                 "--injector", SCEN_NETPART])
        assert p.returncode == 1, p.stdout[-800:]
        rep = json.loads(io.open(j3, encoding="utf-8").read())
        assert rep["verdict"] == "degraded" and rep["score"] == 86.67, rep
        assert rep["active_weight"] == 75, rep["active_weight"]
        reg = rep["domains"]["registry"]
        assert reg["status"] == "skip" and "reason" in reg, reg
        assert rep["domains"]["net"]["verdict"] == "partial" and \
            rep["domains"]["net"]["score"] == 50.0, rep["domains"]["net"]
        assert [a["domain"] for a in rep["advice"]] == ["net", "registry"], \
            rep["advice"]
        # CW_SET 设而缺册→如实 skip（reason 含「缺册」）
        cw_empty = os.path.join(tmp, "cwset_empty")
        os.makedirs(cw_empty)
        j3b = os.path.join(tmp, "v3b.json")
        p = run(["--json", j3b, "--src", src_empty, "--sample", "2",
                 "--injector", SCEN_OK], env_extra={"CW_SET": cw_empty})
        assert p.returncode == 0, p.stdout[-800:]
        rep = json.loads(io.open(j3b, encoding="utf-8").read())
        reg = rep["domains"]["registry"]
        assert reg["status"] == "skip" and "缺册" in reg["reason"], reg

        # ---- V4 堵账 TOP 注入（红 3/4→clog 25.0→88.75·TOP1=A）----
        j4 = os.path.join(tmp, "v4.json")
        p = run(["--json", j4, "--registry", REG_GREEN, "--src", src_empty,
                 "--sample", "2", "--injector", SCEN_CLOGRED])
        assert p.returncode == 1, p.stdout[-800:]
        rep = json.loads(io.open(j4, encoding="utf-8").read())
        assert rep["verdict"] == "degraded" and rep["score"] == 88.75, rep
        clog = rep["domains"]["clog"]
        assert clog["verdict"] == "clogged" and clog["score"] == 25.0, clog
        assert clog["red"] == 3 and clog["probed"] == 4 and \
            clog["red_rate"] == 0.75, clog
        assert clog["red_files"] == ["B", "C", "D"], clog
        top1 = clog["chain_top1"]
        assert top1["lib"] == "A" and top1["n"] == 2 and \
            top1["self"]["washable"] is True, top1
        adv = [a for a in rep["advice"] if a["domain"] == "clog"]
        assert len(adv) == 1 and adv[0]["tool"] == "tools/unclog.py" and \
            "TOP1=A(n=2)" in adv[0]["text"], rep["advice"]

        # ---- V6 JSON 幂等：同场景两跑异 workdir 字节恒同 ----
        j6a = os.path.join(tmp, "v6a.json")
        j6b = os.path.join(tmp, "v6b.json")
        p = run(["--json", j6a, "--workdir", os.path.join(tmp, "wd6a"),
                 "--registry", REG_GREEN, "--src", src_empty, "--sample", "2",
                 "--injector", SCEN_OK])
        assert p.returncode == 0, p.stdout[-400:]
        p = run(["--json", j6b, "--workdir", os.path.join(tmp, "wd6b"),
                 "--registry", REG_GREEN, "--src", src_empty, "--sample", "2",
                 "--injector", SCEN_OK])
        assert p.returncode == 0, p.stdout[-400:]
        ba = io.open(j6a, "rb").read()
        bb = io.open(j6b, "rb").read()
        assert ba == bb, "json 字节漂移＝违例"
        rep = json.loads(ba.decode("utf-8"))
        assert rep["schema"] == SCHEMA, rep["schema"]

        # ---- V7 CLI 四码 ----
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run(["--sample", "-1"])
        assert p.returncode == 2, "--sample 负应 rc=2 实测 %d" % p.returncode
        p = run(["--registry", os.path.join(tmp, "nope.txt")])
        assert p.returncode == 9, "显传缺册应 rc=9 实测 %d" % p.returncode
        p = run(["--src", os.path.join(tmp, "no_dir")])
        assert p.returncode == 9, "--src 缺目录应 rc=9 实测 %d" % p.returncode
        p = run(["--injector", os.path.join(tmp, "no_inj")])
        assert p.returncode == 9, "injector 场景缺应 rc=9 实测 %d" \
            % p.returncode
        bad_scen = os.path.join(tmp, "inj_bad")
        wjson(os.path.join(bad_scen, "scenario.json"), {"bogus_key": {}})
        p = run(["--injector", bad_scen])
        assert p.returncode == 2, "场景键不识应 rc=2 实测 %d" % p.returncode
        half_scen = os.path.join(tmp, "inj_half")
        wjson(os.path.join(half_scen, "scenario.json"),
              {"dyld": {"rc": 0, "report": DYLD_OK}})
        p = run(["--injector", half_scen])
        assert p.returncode == 9, "canned 未覆盖应 rc=9 实测 %d" \
            % p.returncode
        # --src 在册而 --sample 0（缺省不抽样）→堵账域如实 skip 不真探
        j7 = os.path.join(tmp, "v7.json")
        p = run(["--json", j7, "--src", src_empty, "--injector", SCEN_OK])
        assert p.returncode == 0, p.stdout[-400:]
        rep = json.loads(io.open(j7, encoding="utf-8").read())
        assert rep["domains"]["clog"]["status"] == "skip" and \
            "--sample 0" in rep["domains"]["clog"]["reason"], \
            rep["domains"]["clog"]

        # ---- V8 注册审计单元 ----
        st = audit_registry(REG_MIX)
        assert st["lines_scanned"] == 7 and st["anchored"] == 6 and \
            st["canonical"] == 2, st
        assert abs(st["rate"] - 2.0 / 6) < 1e-12, st
        assert st["no_anchor"] == 1 and st["non_form_total"] == 4, st
        assert [e["anchor"] for e in st["non_form"]] == \
            ["#R2", "#R3-abcdef", "#R4-D66910AB", "#R5-d66910abc"], st
        # 帽 20：25 条非形→清单 20·总数 25
        cap_lines = ["X%d.v#R%d" % (i, i) for i in range(25)]
        cap_path = make_registry(os.path.join(tmp, "reg_cap.txt"), cap_lines)
        st = audit_registry(cap_path)
        assert st["non_form_total"] == 25 and len(st["non_form"]) == 20, \
            (st["non_form_total"], len(st["non_form"]))
        # 零锚册→rate 0·non-canonical
        z_path = make_registry(os.path.join(tmp, "reg_noanchor.txt"),
                               ["A.v", "B.v"])
        st = audit_registry(z_path)
        assert st["anchored"] == 0 and st["rate"] == 0.0, st
        dom = domain_registry(z_path, "flag", None)
        assert dom["verdict"] == "non-canonical" and dom["score"] == 0.0, dom
        # CW_SET 正探：册在 CW_SET/ConstructiveWorld_Live/order.txt
        cw_ok = os.path.join(tmp, "cwset_ok")
        make_registry(os.path.join(cw_ok, "ConstructiveWorld_Live",
                                   "order.txt"),
                      ["S01.v#R0-d66910ab", "S02.v#R1-0123abcd"])
        j8 = os.path.join(tmp, "v8.json")
        p = run(["--json", j8, "--src", src_empty, "--sample", "2",
                 "--injector", SCEN_OK], env_extra={"CW_SET": cw_ok})
        assert p.returncode == 0, p.stdout[-800:]
        rep = json.loads(io.open(j8, encoding="utf-8").read())
        reg = rep["domains"]["registry"]
        assert reg["status"] == "ok" and reg["source"] == "CW_SET" and \
            reg["verdict"] == "healthy" and reg["anchored"] == 2, reg
        assert rep["args"]["registry_source"] == "CW_SET", rep["args"]

        print("CW-DOCTOR-SELFTEST PASS: 四域全绿100/环境红降60/注册skip归一"
              "86.67＋CW_SET缺册/堵账TOP注入88.75/advice 生成/JSON 幂等字节"
              "恒同/CLI 四码＋罐装全覆盖/注册审计单元（混形2of6·帽20·零锚·"
              "CW_SET 正探） 九节全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="综合体检器·四域聚合：环境/网络/注册/堵账 逐域 subprocess"
                    " 编排既有一器→综合健康分 0-100＋per-domain verdict＋"
                    "advice（schema rocqwash-cwdoctor/1）")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="体检报告出账（rocqwash-cwdoctor/1·sort_keys 确定性）")
    ap.add_argument("--workdir", default=None, metavar="DIR",
                    help="工件目录（dyld/net 报告·probe 台账·链根图·缺省 "
                         "mkdtemp·stdout 响亮路径）")
    ap.add_argument("--registry", default=None, metavar="PATH",
                    help="注册册显传（order.txt 形；缺省探测 env %s/"
                         "ConstructiveWorld_Live/order.txt·均无→注册域 skip）"
                         % ENV_REGISTRY)
    ap.add_argument("--src", default=None, metavar="DIR",
                    help="堵账域源树（缺省跳过堵账域）")
    ap.add_argument("--sample", type=int, default=0, metavar="N",
                    help="堵账抽样帽（缺省 0=不抽样→堵账域 skip·N>0 等距"
                         "抽样·N≥树大=全量普查）")
    ap.add_argument("--world", default=None, metavar="DIR",
                    help="堵账真探世界目录（真探必给·离线请 --injector）")
    ap.add_argument("--worker", default=None, metavar="PATH",
                    help="透传 toolchain_dyld_doctor --worker（缺省器内探测 "
                         "flag/env/判例机缺省）")
    ap.add_argument("--donor", default=None, metavar="DIR",
                    help="透传 toolchain_dyld_doctor --donor（missing 件溯源）")
    ap.add_argument("--endpoints", default=None, metavar="URL[,URL...]",
                    help="透传 net_probe --endpoints（缺省四端点）")
    ap.add_argument("--guard", default=DEFAULT_GUARD, metavar="PATH",
                    help="cpu_guard.sh 透传 probe_engine（堵账真探温控·"
                         "sanctioned 判例机缺省）")
    ap.add_argument("--guard-reg", dest="guard_reg",
                    default="/tmp/cw_reg_cw_doctor", metavar="DIR")
    ap.add_argument("--guard-maxwait", dest="guard_maxwait", type=int,
                    default=600, metavar="S")
    ap.add_argument("--timeout", type=int, default=1500, metavar="S",
                    help="probe_engine 单件超时秒透传")
    ap.add_argument("--rocq-cmd", dest="rocq_cmd", default=None, metavar="TPL",
                    help="探针命令模板透传 probe_engine（缺省用其内置默认）")
    ap.add_argument("--injector", default=None, metavar="DIR",
                    help="离线罐装场景（DIR/scenario.json·键 dyld/net/probe·"
                         "子进程调用层罐装 {rc,stdout,report}·canned 表须"
                         "全覆盖将发的器件调用）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        code = run(args)
    except UsageError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)
    except (MissingInput, ToolError) as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    sys.exit(code)


if __name__ == "__main__":
    main()
