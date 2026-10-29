# -*- coding: utf-8 -*-
r"""mac_stmt_scan.py — 语句面 Prop 裸形扫描器 Mac 形（S 系 Prop 清除战役·工具链 Mac 适配席·20261022）

词面核＝扫卡器 v3（attn_set1557_scan.py·席 1557·20261016）**1:1 冻结继承**——扫描道/分类四分/
Unicode 名道/implyM 守卫/属性前缀道/混合面判据全部原样继承，等价性由 --selftest 冻结向量组
（v3 全量正负证+名道+CAPTURE+混合面向量逐字内嵌）机械背书。本文件只做 Mac 适配壳：

  1. 删除 v3 --regression 的 Windows 路径靶（D:\ 系）——Mac 端无此盘面，回归以
     --baseline S09（Set 树 worldT_mac 基准试射）替代。
  2. E364 盲区律落地「报清单不报清白」：输出永不出现「CLEAN=无泄露」判词——只出命中清单＋
     逐 hit 归类注记（lawful-keep 候选提示），真命中定谳唯内核 census（SortAlive __-census，
     红线②第六关）。任何 0 命中须另过负证对照（--selftest 内嵌 E364 向量）方可采信。
  3. --manifest 保留（§1·E 律 4 pocket 吞名对账断言：swallowed/blind/kind_drift/line_drift
     四账逐项出，blind=∅ 断言）。

扫描道（全部语句面 scoped；语句面＝声明行起至 Proof. 或边界句点·总纲 §三词面映射）：
  冻结道：P1_Qlt / P1_Qle（独立词·词界排除 QltT/QleT'/QeqT/Qlt_bool 续名）
          P2_==  （Q 域裸相等·(?<![=<>])==(?!>) implyM 守卫）
          P3_exists/and/or/not/false（exists、/\、\/、~、-> False 按 False token 位分类）
          P4_bareeq（裸 = ·排除 :=/==/<=/>=/=>/<>/ 邻接）
          P5_ord（<= < >= > ·bool 值 <=?/<?/>=? 不咬）
  负捕获道（候裁档）：P6_In / P8_True / P9_proper（结论位 CAPTURE／前提位 EXEMPT）
分类四分：RED / WHITELIST / EXEMPT / CAPTURE（gate4 判读兼容）。

用法：
  python3 mac_stmt_scan.py --file <path.v> [--json out.json] [--manifest m.json]
  python3 mac_stmt_scan.py --baseline                          # S09 worldT_mac 基准试射
  python3 mac_stmt_scan.py --file <path.v> --hits-csv out.csv  # 命中清单＋归类注记 CSV
  python3 mac_stmt_scan.py --selftest                          # E364 负证律冻结向量组
"""
import os, re, sys, json, io, hashlib, argparse

# ---------------- 词面注册表（v3 冻结继承·15 位判例登记） ----------------
VOCAB_NOTE = "词表登记册见 v3 原器 attn_set1557_scan.py VOCAB（15 位·S02 十+S03 三+S03 Instance 二+S12 一）——本 Mac 形不再复制，判例登记以 v3 为正本。"

# 白名单/例外登记（sanctioned·非泄露·v3 冻结继承）
WHITELIST = [
    dict(name="QltT_to_Qlt", kind="Lemma", reason="W0 案一 sanctioned 回向桥（1489 §6.1 预言·1506/1528 两代 census 逐位吻合）"),
    dict(name="QleT'_to_Qle", kind="Lemma", reason="W0 案一 sanctioned 回向桥（同上）"),
    dict(name="qeqT_imp_qeq", kind="Lemma", reason="W0 案一 sanctioned 回向桥（同上）"),
    dict(name="Qle_plus_nonneg_r", kind="Lemma", reason="M34 [WAVE-DEBT] 波序归属在账（裁 A1·停洗冻结·非例外扩册）"),
]

SUMBOOL_WHITELIST = [
    dict(name="sc_nat_parity", kind="Lemma", reason="sumbool 括形 {..}+{..} Set 承载合法（1550 S11 判例）"),
    dict(name="b5i_qle_dec", kind="Lemma", reason="sumbool 括形 {..}+{..} Set 承载合法（1550 S11 判例）"),
]

BRIDGE_FAMILY = ("QltT_to_Qlt", "QleT'_to_Qle", "qeqT_imp_qeq",
                 "Qlt_to_QltT", "Qle_to_QleT'", "qeq_imp_qeqT")

# ---------------- 扫描道 pattern（v3 1:1 冻结继承） ----------------
DECL_RE = re.compile(
    r"[ \t]*(?:(?:#\[[^\]]*\])[ \t]*(?:\r?\n)?[ \t]*|(?:Local|Global|Export|Declare)[ \t]+)*"
    r"(Lemma|Theorem|Definition|Corollary|Fixpoint|CoFixpoint|Proposition|Instance)\b")
ATTR_PREFIX_RE = re.compile(r"^\s*(?:(?:#\[[^\]]*\])[ \t]*(?:\r?\n)?[ \t]*|(?:Local|Global|Export|Declare)[ \t]+)+")
PROOF_RE = re.compile(r"[ \t]*Proof\b")
HYP_RE = re.compile(r"[ \t]*(Hypothesis|Variable|Variables|Hypotheses|Context)\b")
DEFKINDS = ("Definition", "Fixpoint", "CoFixpoint")

WB = r"[\w']"
CH_P1_QLT = re.compile(r"(?<!%s)Qlt(?!%s)" % (WB, WB))
CH_P1_QLE = re.compile(r"(?<!%s)Qle(?!%s)" % (WB, WB))
CH_P2 = re.compile(r"(?<![=<>])==(?!>)")
CH_P3_EXISTS = re.compile(r"(?<!%s)exists(?!%s)" % (WB, WB))
CH_P3_AND = re.compile(r"/\\")
CH_P3_OR = re.compile(r"\\/")
CH_P3_NOT = re.compile(r"(?<!%s)~(?!%s)" % (WB, WB))
CH_P3_FALSE = re.compile(r"->\s*(False)\b")
CH_P4 = re.compile(r"(?<![=<>:])=(?![=<>])")
CH_P5_LE = re.compile(r"(?<![<>])<=(?![?=])")
CH_P5_LT = re.compile(r"(?<![<>])<(?![=>?-])")
CH_P5_GE = re.compile(r"(?<![<>=])>=(?![?=])")
CH_P5_GT = re.compile(r"(?<![<>=-])>(?![=?])")
CH_P6_IN = re.compile(r"(?<!%s)In(?!%s)" % (WB, WB))
CH_P8_TRUE = re.compile(r"(?<!%s)True(?!%s)" % (WB, WB))
CH_P9_PROPER = re.compile(r"(?<!%s)Proper(?!%s)" % (WB, WB))

FROZEN_CATS = ("P1_Qlt", "P1_Qle", "P2_==", "P3_exists", "P3_and", "P3_or", "P3_not", "P3_false",
               "P4_bareeq", "P5_le", "P5_lt", "P5_ge", "P5_gt")
CAPTURE_CATS = ("P6_In", "P8_True", "P9_proper")
CAPTURE_REASON = {
    "P6_In": "结论位 stdlib In（A -> list A -> Prop 谓词·非 Set 承载）＝泄露候选族（1552 S12 In 桥三站判例）·候裁档禁擅裁",
    "P3_false": "结论位 False（空 Prop·非 Set 承载）＝泄露候选族（1552 S12 口径差判例·按 False token 位重判）·候裁档禁擅裁",
    "P8_True": "结论位 True（单点 Prop·vacuous 语句族·非 Set 承载）＝泄露候选族（1552 S12 判例）·候裁档禁擅裁",
    "P9_proper": "Proper 注册面（Morphisms Prop 类·1549 kernel census RED 判例/1550 S11 活注册）·候裁档禁擅裁禁误删",
}

CHANNELS = [
    ("P1_Qlt", CH_P1_QLT), ("P1_Qle", CH_P1_QLE), ("P2_==", CH_P2),
    ("P3_exists", CH_P3_EXISTS), ("P3_and", CH_P3_AND), ("P3_or", CH_P3_OR),
    ("P3_not", CH_P3_NOT), ("P3_false", CH_P3_FALSE),
    ("P4_bareeq", CH_P4),
    ("P5_le", CH_P5_LE), ("P5_lt", CH_P5_LT), ("P5_ge", CH_P5_GE), ("P5_gt", CH_P5_GT),
    ("P6_In", CH_P6_IN), ("P8_True", CH_P8_TRUE), ("P9_proper", CH_P9_PROPER),
]

CARRIER_TOKENS = ("QleT'", "QltT", "QeqT", "NatLe", "InT")
CARRIER_RES = [re.compile(r"(?<!%s)%s(?!%s)" % (WB, re.escape(t), WB)) for t in CARRIER_TOKENS]
BARE_CATS = ("P1_Qlt", "P1_Qle", "P2_==", "P4_bareeq", "P5_le", "P5_lt", "P5_ge", "P5_gt")


# ---------------- 状态机（v3 1:1 冻结继承） ----------------
def strip_comments_strings(text):
    """状态机剥嵌套注释与字符串字面量；被剥区域替换为空格保持行号（E364 T8/T3）"""
    out = []
    i, n = 0, len(text)
    depth = 0
    while i < n:
        c = text[i]
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1; out.append("  "); i += 2; continue
            if text.startswith("*)", i):
                depth -= 1; out.append("  "); i += 2; continue
            out.append(c if c == "\n" else " "); i += 1; continue
        if text.startswith("(*", i):
            depth = 1; out.append("  "); i += 2; continue
        if c == '"':
            out.append(" "); i += 1
            while i < n and text[i] != '"':
                out.append(text[i] if text[i] == "\n" else " "); i += 1
            if i < n: out.append(" "); i += 1
            continue
        out.append(c); i += 1
    return "".join(out)


def stmt_end(clean, start_idx):
    """语句终止：行首 Proof. 或边界句号（前后空白/行界的 '.'）"""
    i, n = start_idx, len(clean)
    line_start = True
    while i < n:
        c = clean[i]
        if c == "\n":
            line_start = True; i += 1; continue
        if line_start:
            m = re.match(r"\s*Proof\b", clean[i:i+200])
            if m:
                return i + m.end(), "Proof"
            line_start = False
        if c == ".":
            prev = clean[i-1] if i > 0 else " "
            nxt = clean[i+1] if i+1 < n else " "
            if prev != "." and (nxt in " \t\r\n" or nxt == ""):
                return i+1, "Dot"
        i += 1
    return n, "EOF"


def line_start_at(s, i):
    return i == 0 or s[i-1] == "\n"


def depth0_colon_after(s, start):
    depth = 0
    i = start
    while i < len(s):
        c = s[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == ":" and depth == 0:
            if i+1 < len(s) and s[i+1] == "=":
                return -1
            return i
        i += 1
    return -1


def forall_strip_end(s, start=0):
    i, n = start, len(s)
    while True:
        while i < n and s[i].isspace():
            i += 1
        if s.startswith("forall", i) and (i+6 >= n or not (s[i+6].isalnum() or s[i+6] in "_'")):
            depth = 0
            j = i
            found = -1
            while j < n:
                c = s[j]
                if c in "([{":
                    depth += 1
                elif c in ")]}":
                    depth -= 1
                elif c == "," and depth == 0:
                    found = j
                    break
                j += 1
            if found < 0:
                return i
            i = found + 1
            continue
        return i


def last_depth0_arrow(s, start=0):
    depth = 0
    last = -1
    i = start
    n = len(s)
    while i < n:
        c = s[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "-" and i+1 < n and s[i+1] == ">" and depth == 0 and (i == 0 or s[i-1] != "<"):
            last = i
            i += 2
            continue
        i += 1
    return last


def brace_zones(s, start, end):
    zones = []
    depth = 0
    zs = -1
    for i in range(start, min(end, len(s))):
        c = s[i]
        if c == "{":
            depth += 1
            if depth == 1:
                zs = i
        elif c == "}":
            depth -= 1
            if depth == 0 and zs >= 0:
                zones.append((zs, i+1))
                zs = -1
    return zones


SIG_RE = re.compile(r"(?<![A-Za-z0-9_'])(sigT|sig)(?![A-Za-z0-9_'])")


def sig_payload_zones(s, start, end):
    zones = []
    for m in SIG_RE.finditer(s, start, end):
        j = m.end()
        while j < end and s[j].isspace():
            j += 1
        if j < end and s[j] == "(":
            depth = 0
            k = j
            while k < end:
                c = s[k]
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        zones.append((j, k+1))
                        break
                k += 1
    return zones


def split_face(face):
    m = re.match(r"\s*\w+\s+([^\W\d][\w']*)", face)
    if not m:
        nm = re.match(r"\s*(\w+)", face)
        return (nm.group(1) if nm else "?"), (nm.end() if nm else 0), len(face), len(face)
    name = m.group(1)
    name_end = m.end()
    colon = depth0_colon_after(face, name_end)
    binders_end = colon+1 if colon >= 0 else name_end
    typ = forall_strip_end(face, binders_end)
    arrow = last_depth0_arrow(face, typ)
    concl_start = arrow+2 if arrow >= 0 else typ
    return name, name_end, binders_end, concl_start


def classify_pos(idx, name_end, binders_end, concl_start):
    if idx < binders_end:
        return "premise", "binder 区（binders/forall 前缀）"
    if idx < concl_start:
        return "premise", "前提位（forall 前缀/末个 -> 之前）"
    return "conclusion", "结论位"


def lawful_keep_hint(cls, tag, pos, zone):
    """E364 盲区律·归类注记（Mac 新增·仅注记不改 v3 分类）——报清单不报清白。"""
    if cls == "RED":
        return "真命中候选——人工定谳＋内核 census（SortAlive __-census）复核必经"
    if cls == "WHITELIST":
        return "白名单在册（sanctioned 回向桥/波债在账）＝合法保留"
    if cls == "CAPTURE":
        return "候裁档（%s）禁擅裁禁擅赦——独立账候裁" % tag
    if "sigT/sig" in zone:
        return "假阳性（ lawful keep）：sigT payload 合法位（Set 承载语句内 Prop 系前提位·红线②合法）"
    if "括形" in zone:
        return "假阳性（lawful keep）：Set 承载括形 {..}（sig/sumbool 记法）内"
    if zone.startswith("binder"):
        return "假阳性（lawful keep）：binder 区（红线②前提位合法）"
    return "假阳性（lawful keep）：前提位（红线② Prop 前提合法）"


def scan_face(face, kind, decl_line, name_hint=None):
    attrs = ""
    am = ATTR_PREFIX_RE.match(face)
    if am:
        attrs = face[:am.end()].strip()
        face_core = face[am.end():]
        base_shift = am.end()
    else:
        face_core = face
        base_shift = 0
    name, name_end, binders_end, concl_start = split_face(face_core)
    bz = brace_zones(face_core, concl_start, len(face_core))
    sz = sig_payload_zones(face_core, concl_start, len(face_core))
    wl = next((w for w in WHITELIST if w["name"] == name), None)
    sb = next((w for w in SUMBOOL_WHITELIST if w["name"] == name), None)
    hits = []
    for tag, pat in CHANNELS:
        for pm in pat.finditer(face_core):
            hstart = pm.start(1) if tag == "P3_false" else pm.start()
            pos, why = classify_pos(hstart, name_end, binders_end, concl_start)
            in_brace = any(a <= hstart < b for a, b in bz)
            in_sig = any(a <= hstart < b for a, b in sz)
            if wl:
                cls, reason = "WHITELIST", wl["reason"]
            elif sb:
                cls, reason = "EXEMPT", sb["reason"]
            elif in_sig:
                cls, reason = "EXEMPT", "sigT/sig Set 承载面 payload 内（语句 Set 排序·payload 内 Prop 系前提位·红线②合法）"
            elif in_brace:
                cls, reason = "EXEMPT", "Set 承载括形 {..}（sig/sumbool 记法）内·非语句位 Prop"
            elif tag == "P9_proper":
                cls, reason = "CAPTURE", CAPTURE_REASON["P9_proper"]
            elif tag in ("P6_In", "P8_True", "P3_false"):
                if pos == "conclusion":
                    cls, reason = "CAPTURE", CAPTURE_REASON[tag]
                else:
                    cls, reason = "EXEMPT", why + "（红线②前提位 Prop 合法·%s 前提位不捕获）" % tag
            elif pos == "conclusion":
                cls, reason = "RED", "结论位 Prop 面命中"
            else:
                cls, reason = "EXEMPT", why + "（红线②前提位 Prop 合法）"
            hits.append(dict(cat=tag, line=decl_line, pos=pos, zone=why,
                             cls=cls, reason=reason,
                             hint=lawful_keep_hint(cls, tag, pos, why),
                             _idx=hstart, _in_sig=bool(in_sig or in_brace),
                             tok=face_core[max(0, pm.start()-40):pm.end()+40].replace("\n", " ")))
    sides = dict(binder=[], premise=[], conclusion=[])
    for h in hits:
        if h["pos"] == "conclusion":
            sides["conclusion"].append(h["cat"])
        elif h["zone"].startswith("binder"):
            sides["binder"].append(h["cat"])
        else:
            sides["premise"].append(h["cat"])
    sides = dict((k, sorted(set(v))) for k, v in sides.items())
    carriers = []
    for tok, cre in zip(CARRIER_TOKENS, CARRIER_RES):
        for cm in cre.finditer(face_core):
            cpos, cwhy = classify_pos(cm.start(), name_end, binders_end, concl_start)
            carriers.append(dict(tok=tok, pos=cpos, zone=cwhy))
    bare_hits = [h for h in hits if h["cat"] in BARE_CATS]
    typ = forall_strip_end(face_core, binders_end)
    bare_conc = False
    bare_binderdef = False
    bare_prem = False
    for h in bare_hits:
        if h.get("_in_sig"):
            continue
        if h["pos"] == "conclusion":
            bare_conc = True
        elif h["_idx"] < typ:
            bare_binderdef = True
        else:
            bare_prem = True
    is_bridge_family = name in BRIDGE_FAMILY
    mixed = False
    mixed_kind = None
    if wl is None and sb is None and not is_bridge_family and carriers and \
            (bare_conc or bare_binderdef or bare_prem):
        mixed = True
        if bare_conc:
            mixed_kind = "载体并现·结论位仍裸（前提已迁结论未迁）"
        elif bare_binderdef:
            mixed_kind = "载体并现·binder 默认位仍裸（签名位半迁）"
        else:
            mixed_kind = "载体并现·前提位裸（桥件形/反向半迁候裁档）"
    meta = dict(attrs=attrs, sides=sides, carriers=carriers,
                mixed=mixed, mixed_kind=mixed_kind)
    return name, hits, meta


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_file(fp):
    try:
        raw = io.open(fp, "r", encoding="utf-8", errors="replace").read()
    except Exception as e:
        return dict(file=fp, error=str(e), hits=[])
    clean = strip_comments_strings(raw)
    lines = clean.split("\n")
    n_lines = clean.count("\n") + (1 if clean and not clean.endswith("\n") else 0)
    offs = [0]
    for ln in lines:
        offs.append(offs[-1] + len(ln) + 1)

    def line_of(idx):
        lo, hi = 0, len(offs)-1
        while lo < hi:
            mid = (lo+hi+1)//2
            if offs[mid] <= idx:
                lo = mid
            else:
                hi = mid-1
        return lo

    hits = []
    hyp_hits = []
    decls = []
    i, n = 0, len(clean)
    while i < n:
        m = DECL_RE.match(clean, i) if line_start_at(clean, i) else None
        if m:
            kind = m.group(1)
            end, how = stmt_end(clean, m.start())
            seg = clean[m.start():end]
            base_line = line_of(m.start(1)) + 1
            name, fhits, meta = scan_face(seg, kind, base_line)
            decls.append(dict(name=name, kind=kind, decl_line=base_line, face_end=end, end_kind=how,
                              attrs=meta["attrs"], sides=meta["sides"],
                              mixed=meta["mixed"], mixed_kind=meta["mixed_kind"],
                              carriers=[c["tok"]+"@"+c["pos"] for c in meta["carriers"]]))
            hits.extend(fhits)
            i = end
            continue
        if line_start_at(clean, i):
            hm = HYP_RE.match(clean, i)
            if hm:
                eol = clean.find("\n", i)
                if eol == -1:
                    eol = n
                seg = clean[i:eol]
                for tag, pat in CHANNELS:
                    for pm in pat.finditer(seg):
                        hyp_hits.append(dict(cat="H_" + tag, line=line_of(i+pm.start())+1,
                                             cls="EXEMPT", reason="Hypothesis/Variable 附加信息层（红线②同拒收·信息级）",
                                             hint="Hypothesis 位＝拒收级信息注记（非语句面泄露）",
                                             tok=seg[max(0, pm.start()-40):pm.end()+40].replace("\n", " ")))
                i = eol
                continue
        i += 1
    bycls = dict(RED=[], WHITELIST=[], EXEMPT=[], CAPTURE=[])
    for h in hits:
        bycls[h["cls"]].append(h)
    red_stations = sorted(set((h["line"],) for h in bycls["RED"]))
    wl_stations = sorted(set((h["line"],) for h in bycls["WHITELIST"]))
    station_names = {}
    for d in decls:
        station_names[d["decl_line"]] = (d["name"], d["kind"])
    red_names = sorted(set(station_names.get(r[0], ("?", "?"))[0] for r in red_stations))
    wl_names = sorted(set(station_names.get(r[0], ("?", "?"))[0] for r in wl_stations))
    instance_ledger = [dict(name=d["name"], decl_line=d["decl_line"], attrs=d["attrs"],
                            channels=d["sides"]["conclusion"] + d["sides"]["premise"] + d["sides"]["binder"])
                       for d in decls if d["kind"] == "Instance"]
    mixed_faces = [dict(name=d["name"], decl_line=d["decl_line"], kind=d["kind"],
                        mixed_kind=d["mixed_kind"], carriers=d["carriers"],
                        prem_channels=d["sides"]["premise"], conc_channels=d["sides"]["conclusion"],
                        binder_channels=d["sides"]["binder"])
                   for d in decls if d["mixed"]]
    frozen_hits = [h for h in hits if h["cat"] in FROZEN_CATS]
    capture_hits = [h for h in hits if h["cls"] == "CAPTURE"]
    capture_stations = {}
    for h in capture_hits:
        capture_stations.setdefault(h["cat"], set()).add(station_names.get(h["line"], ("?",))[0])
    capture_stations = dict((k, sorted(v)) for k, v in capture_stations.items())
    sb_names = sorted(set(d["name"] for d in decls
                          if any(h["line"] == d["decl_line"] and h["cls"] == "EXEMPT"
                                 and h["reason"].startswith("sumbool 括形") for h in hits)))
    return dict(
        file=os.path.abspath(fp), md5=md5_of(fp), lines=n_lines, decls_total=len(decls),
        decls=decls, hits=hits, hyp_hits=hyp_hits,
        red_stations=red_stations, wl_stations=wl_stations,
        red_names=red_names, wl_names=wl_names,
        clean_count=len(decls) - len(red_stations) - len(wl_stations),
        frozen_hits_n=len(frozen_hits), frozen_by_cat={},
        capture_hits_n=len(capture_hits), capture_by_cat={}, capture_stations=capture_stations,
        instance_ledger=instance_ledger, mixed_faces=mixed_faces,
        sumbool_exempt_names=sb_names,
        by_cat={},
    )


def summarize(res):
    by_cat = {}
    frozen = {}
    cap = {}
    for h in res["hits"]:
        by_cat[h["cat"]] = by_cat.get(h["cat"], 0) + 1
        if h["cat"] in FROZEN_CATS:
            frozen[h["cat"]] = frozen.get(h["cat"], 0) + 1
        if h["cls"] == "CAPTURE":
            cap[h["cat"]] = cap.get(h["cat"], 0) + 1
    res["by_cat"] = by_cat
    res["frozen_by_cat"] = frozen
    res["capture_by_cat"] = cap
    kinds = {}
    for d in res["decls"]:
        kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
    res["kinds"] = kinds
    res["decls_v2kinds"] = sum(v for k, v in kinds.items() if k != "Instance")
    return res


# ---------------- manifest 出口对账（§1·E 律 4·v3 1:1 继承） ----------------
def reconcile_manifest(res, manifest_path):
    man = json.load(io.open(manifest_path, "r", encoding="utf-8"))
    man_rows = [(s["name"], s.get("kind", "?"), s.get("decl_line", -1)) for s in man["statements"]]
    scan_rows = [(d["name"], d["kind"], d["decl_line"]) for d in res["decls"]]
    man_names = dict((n, (k, l)) for n, k, l in man_rows)
    scan_names = dict((n, (k, l)) for n, k, l in scan_rows)
    swallowed = sorted(set(scan_names) - set(man_names))
    blind = sorted(set(man_names) - set(scan_names))
    common = sorted(set(man_names) & set(scan_names))
    kind_drift = [dict(name=n, manifest=man_names[n][0], scanner=scan_names[n][0])
                  for n in common if man_names[n][0] != scan_names[n][0]]
    line_drift = [dict(name=n, manifest=man_names[n][1], scanner=scan_names[n][1])
                  for n in common if man_names[n][1] != scan_names[n][1]]
    return dict(manifest=manifest_path, manifest_n=len(man_rows), scanner_n=len(scan_rows),
                swallowed=swallowed, blind=blind,
                kind_drift=kind_drift, line_drift=line_drift,
                loud_ok=(len(blind) == 0 and len(kind_drift) == 0),
                note="swallowed 非空＝manifest 侧吞名（器伤响亮·pocket 名单即本列）；blind 非空＝扫描器盲区（器伤响亮）")


# ---------------- E364 负证律自检（v3 冻结向量组逐字内嵌·等价性背书） ----------------
SELFTEST_POS = [
    ("forall x y, 0 <= y -> x <= x + y.", ["P5_le"]),
    ("forall m : nat, (1 <= 2 ^ m)%nat.", ["P5_le"]),
    ("forall m : nat, (m <= 2 ^ m)%nat.", ["P5_le"]),
    ("forall m : nat, (m < 2 ^ m)%nat.", ["P5_lt"]),
    ("forall a b : nat, (a <= b)%nat -> Nat.min a b = a.", ["P4_bareeq"]),
    ("forall a b : nat, (b <= a)%nat -> Nat.min a b = b.", ["P4_bareeq"]),
    ("forall (fmod : nat -> nat) (a b : nat), (a <= b)%nat -> (reg_index fmod a <= reg_index fmod b)%nat.", ["P5_le"]),
    ("forall (fmod : nat -> nat) (k : nat), (k <= reg_index fmod k)%nat.", ["P5_le"]),
    ("forall (fmod : nat -> nat) (k : nat), (fmod k <= reg_index fmod k)%nat.", ["P5_le"]),
    ("forall (N a b : nat), (N <= a)%nat -> (N <= b)%nat -> (N <= Nat.min a b)%nat.", ["P5_le"]),
    ("forall p : positive, Z.of_nat (Pos.to_nat p) = Z.pos p.", ["P4_bareeq"]),
    ("forall x : Q, Qlt 0 x -> ~ (x == 0).", ["P2_==", "P3_not"]),
    ("Lemma b5n_2S_kδ_le : forall x : Q, Qle x x.", ["P1_Qle"]),
    ("Lemma sf_inT_in : forall (x : nat) (l : list nat), InT x l -> In x l.", ["P6_In"]),
    ("Lemma sf_id_true_false : Id true false -> False.", ["P3_false"]),
    ("Theorem sf_kmeans_nonincrease : forall (points : list nat), True.", ["P8_True"]),
]
SELFTEST_POS_CONCL = [
    ("forall p : positive, Z.of_nat (Pos.to_nat p) = Z.pos p.", "P4_bareeq", "conclusion"),
    ("forall x : Q, Qlt 0 x -> ~ (x == 0).", "P2_==", "conclusion"),
    ("forall x : Q, Qlt 0 x -> ~ (x == 0).", "P3_not", "conclusion"),
    ("forall x y, 0 <= y -> x <= x + y.", "P5_le", "conclusion"),
    ("forall m : nat, (m < 2 ^ m)%nat.", "P5_lt", "conclusion"),
    ("forall a b : nat, (a <= b)%nat -> Nat.min a b = a.", "P4_bareeq", "conclusion"),
    ("forall x y : Q, QltT x y -> Qlt x y.", "P1_Qlt", "conclusion"),
    ("Lemma sf_inT_in : forall (x : nat) (l : list nat), InT x l -> In x l.", "P6_In", "conclusion"),
    ("Lemma sf_id_true_false : Id true false -> False.", "P3_false", "conclusion"),
    ("Theorem sf_kmeans_nonincrease : forall (points : list nat), True.", "P8_True", "conclusion"),
]
SELFTEST_NEG = [
    ("forall m : nat, NatLe 1 (2 ^ m).", []),
    ("forall a b : nat, (a <= b)%nat -> Id a (Nat.min a b).", []),
    ("forall x y : Q, QltT x y -> QltT x y.", []),
    ("forall x : Q, QltT 0 x -> Not (QeqT x 0).", []),
    ("forall x y : Q, QeqT a b -> QeqT a b.", []),
    ("forall a b : nat, {a = b} + {a <> b}.", []),
    ("forall (u : Qseq), sigT (fun N : nat => NatLe N m).", []),
    ("Definition QltT (x y : Q) : Set := Id (Qlt_bool x y) true.", []),
    ("forall x y : Q, Qlt x y -> QltT x y.", []),
    ("forall m n : nat, NatLe m n.", []),
    ("forall A : Q, sigT (fun N : nat => forall t : nat, NatLe N t -> QleT' (Qmult (1 + 1)%Q A) (Z.of_nat (t + 1) # 1)).", []),
    ("forall (x : Q) (eps : Q), QltT 0 eps -> sigT (fun N : nat => forall m n : nat, (N <= m)%nat -> (N <= n)%nat -> QltT (Qabs (exp_partial m x - exp_partial n x)) eps).", []),
    ("#[global] Instance Qplus_morph : Proper (Qeq ==> Qeq ==> Qeq) Qplus.", []),
    ("Lemma δ粘名 : forall x : Q, δQlt 0 x -> QltT 0 x.", []),
    ("Lemma keepf : forall (H : False), Id H H.", []),
    ("Lemma lowerin : forall l : list nat, in_none l -> True_prop_thing l.", []),
    ("Lemma inneg : forall x : nat, InT x nil -> NatLe x 0.", []),
]
SELFTEST_NAMES = [
    ("Lemma b5n_2S_kδ_le : nat.", "b5n_2S_kδ_le"),
    ("#[export] Instance Qinv_comp_proper : Proper (Qeq ==> Qeq) Qinv := Qinv_comp.", "Qinv_comp_proper"),
    ("#[global]\nInstance Qplus_morph : Proper (Qeq ==> Qeq ==> Qeq) Qplus.", "Qplus_morph"),
    ("Local Instance foo_bar : Nat.", "foo_bar"),
    ("Lemma alpha_α : nat.", "alpha_α"),
]
SELFTEST_CAPTURE = [
    ("Lemma sf_in_nodup : forall (l : list nat) (x : nat), In x (nodup Nat.eq_dec l) -> In x l.",
     "P6_In", 2, 1),
    ("Lemma bridge_bwd : forall x y : Q, QltT x y -> Qlt x y.", "P9_proper", 0, 0),
]
SELFTEST_MIXED = [
    ("Lemma mmix : forall n B, QleT' 0 B -> Qle n B.", True),
    ("Fixpoint cscan (a b : Q) (Hab : Qlt a b) : sigT (fun ab : Q => QltT (fst ab) (snd ab)) * bool.", True),
    ("Lemma revmix : forall (eps : Q), Qlt 0 eps -> sigT (fun N : nat => QltT N eps).", True),
    ("Lemma mbridge : forall x y : Q, Qlt x y -> QltT x y.", True),
    ("Lemma mclean : forall x y : Q, QleT' x y -> QleT' x y.", False),
    ("Lemma mfull : forall x y : Q, Qlt x y -> Qle x y.", False),
    ("Lemma mwash : forall a b : nat, (a <= b)%nat -> Id a b.", False),
    ("Lemma mpayload : forall eps : Q, QltT 0 eps -> sigT (fun N : nat => (N <= 3)%nat -> QltT N eps).", False),
]


def _scan_seg(face, kind="Lemma"):
    seg = "%s selftest_x : %s Proof." % (kind, face) if not face.lstrip().startswith(("Lemma", "Theorem", "Definition", "Fixpoint", "Instance", "#", "Local", "Global")) else face + " Proof."
    return scan_face(seg, kind, 1)


def _scan_seg_kind(face, kind):
    if face.lstrip().startswith(("Lemma", "Theorem", "Definition", "Fixpoint", "Instance", "#", "Local", "Global")):
        seg = face + " Proof."
    else:
        seg = "%s selftest_x : %s Proof." % (kind, face)
    return scan_face(seg, kind, 1)


def selftest():
    ok = True
    report = dict(positive=[], positive_concl=[], negative=[], names=[], capture=[], mixed=[], pass_=True)
    for idx, (face, want) in enumerate(SELFTEST_POS, 1):
        _, hits, _ = _scan_seg(face)
        got = sorted(set(h["cat"] for h in hits))
        hit_ok = all(w in got for w in want)
        report["positive"].append(dict(face=face, want=want, got=got, ok=hit_ok))
        if not hit_ok:
            ok = False
    for face, want_cat, want_pos in SELFTEST_POS_CONCL:
        _, hits, _ = _scan_seg(face)
        h = next((x for x in hits if x["cat"] == want_cat and x["pos"] == want_pos), None)
        pos_ok = h is not None
        got_pos = [x["pos"] for x in hits if x["cat"] == want_cat]
        report["positive_concl"].append(dict(face=face, cat=want_cat, want_pos=want_pos,
                                             got_pos=got_pos, ok=pos_ok))
        if not pos_ok:
            ok = False
    for face, want_reds in SELFTEST_NEG:
        _, hits, _ = _scan_seg(face)
        reds = [h for h in hits if h["cls"] == "RED"]
        neg_ok = len(reds) == len(want_reds)
        report["negative"].append(dict(face=face, red_count=len(reds), ok=neg_ok,
                                       reds=[h["cat"]+"/"+h["pos"] for h in reds]))
        if not neg_ok:
            ok = False
    for face, want_name in SELFTEST_NAMES:
        name, _, _ = scan_face(face + " Proof.", "Lemma", 1)
        nm_ok = (name == want_name)
        report["names"].append(dict(face=face[:60], want=want_name, got=name, ok=nm_ok))
        if not nm_ok:
            ok = False
    for face, cat, want_total, want_cap in SELFTEST_CAPTURE:
        _, hits, _ = _scan_seg(face)
        tot = len([h for h in hits if h["cat"] == cat])
        capn = len([h for h in hits if h["cat"] == cat and h["cls"] == "CAPTURE"])
        cap_ok = (tot == want_total and capn == want_cap)
        report["capture"].append(dict(face=face[:70], cat=cat, want=(want_total, want_cap),
                                      got=(tot, capn), ok=cap_ok))
        if not cap_ok:
            ok = False
    for face, want_mixed in SELFTEST_MIXED:
        kind = "Fixpoint" if face.startswith("Fixpoint") else "Lemma"
        _, _, meta = _scan_seg_kind(face, kind)
        mx_ok = (meta["mixed"] == want_mixed)
        report["mixed"].append(dict(face=face[:70], want=want_mixed, got=meta["mixed"],
                                    kind=meta["mixed_kind"], ok=mx_ok))
        if not mx_ok:
            ok = False
    report["pass_"] = ok
    return report


# ---------------- 基准试射靶（Mac 形：S09 worldT_mac·census 100/100 已证） ----------------
BASELINE_S09 = "/Users/apple/Desktop/S系Prop清除战役工单/work_S10_finish/worldT_mac/S09_EntropyReal.v"
BASELINE_S09_NOTE = ("S09_EntropyReal（Set 树·worldT_mac 805c7642c6ddfc181db20efc2222b6f2）——"
                     "内核 census 100/100 clean red=0 已证（_包消化台账-20261022：multiset 100==100·"
                     "静态 lawful keeps=3·提取 .ml/.mli=0 双世界同 md5·PA 25/25 Closed·coqchk Axioms<none>）。"
                     "本器词面试射预期＝RED≈0＋lawful keeps 注记≈3；任何 RED≠0 即人工定谳义务（报清单不报清白）。")


def print_inventory(res, hits_csv=None):
    """E364 盲区律：只出清单＋归类注记，禁出「清白」判词。"""
    rows = []
    for h in res["hits"]:
        rows.append((h["line"], h["cat"], h["cls"], h["pos"], h["hint"], h["tok"][:100]))
    print("== 命中清单（词面预筛·非清白判词——真命中定谳唯内核 census）==")
    for (ln, cat, cls, pos, hint, tok) in rows:
        print("  L%-6d %-10s %-9s %-10s %s" % (ln, cat, cls, pos, hint))
        print("         tok: %s" % tok.replace("\t", " "))
    if hits_csv:
        import csv
        with io.open(hits_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["line", "cat", "cls", "pos", "hint", "tok"])
            for r in rows:
                w.writerow(r)
        print("hits csv ->", hits_csv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="单件扫描目标 .v")
    ap.add_argument("--json", help="输出 JSON 路径")
    ap.add_argument("--manifest", help="SortAlive manifest json（--file 对账·§1·E 律4）")
    ap.add_argument("--hits-csv", help="命中清单＋归类注记 CSV 落盘")
    ap.add_argument("--baseline", action="store_true", help="S09 worldT_mac 基准试射（census 100/100 已证）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if args.selftest:
        rep = selftest()
        print("SELFTEST (E364 冻结向量组·v3 1:1 等价背书):", "PASS" if rep["pass_"] else "FAIL")
        for r in rep["positive"]:
            if not r["ok"]:
                print("  POS-MISS:", r["face"], "want", r["want"], "got", r["got"])
        for r in rep["positive_concl"]:
            if not r["ok"]:
                print("  POSPOS-MISS:", r["face"], r["cat"], "want", r["want_pos"], "got", r["got_pos"])
        for r in rep["negative"]:
            if not r["ok"]:
                print("  NEG-FP:", r["face"], "reds:", r["reds"])
        for r in rep["names"]:
            if not r["ok"]:
                print("  NAME-MISS:", r["face"], "want", r["want"], "got", r["got"])
        for r in rep["capture"]:
            if not r["ok"]:
                print("  CAP-MISS:", r["face"], r["cat"], "want", r["want"], "got", r["got"])
        for r in rep["mixed"]:
            if not r["ok"]:
                print("  MIX-MISS:", r["face"], "want", r["want"], "got", r["got"], r["kind"])
        sys.exit(0 if rep["pass_"] else 2)
    if args.baseline:
        if not os.path.exists(BASELINE_S09):
            print("BASELINE-S09-MISSING:", BASELINE_S09)
            sys.exit(9)
        res = scan_file(BASELINE_S09)
        summarize(res)
        print("== S09 基准试射（mac_stmt_scan.py·词面预筛）==")
        print("file:", res["file"])
        print("md5:", res["md5"], " lines:", res["lines"], " decls:", res["decls_total"],
              " (v2kinds:", res["decls_v2kinds"], " instance:", len(res["instance_ledger"]), ")")
        print("RED stations:", res["red_names"])
        print("WHITELIST stations:", res["wl_names"])
        print("CAPTURE stations:", res["capture_stations"])
        print("by_cat:", res["by_cat"])
        print("frozen hits:", res["frozen_hits_n"], " capture hits:", res["capture_hits_n"])
        print("mixed faces:", len(res["mixed_faces"]), [(m["name"], m["decl_line"]) for m in res["mixed_faces"]])
        print("exempt hits:", len([h for h in res["hits"] if h["cls"] == "EXEMPT"]),
              " hyp hits:", len(res["hyp_hits"]))
        print()
        print(BASELINE_S09_NOTE)
        print()
        print_inventory(res, hits_csv=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "_s09_baseline_hits.csv"))
        sys.exit(0)
    if args.file:
        if not os.path.exists(args.file):
            print("FILE-MISSING:", args.file)
            sys.exit(9)
        res = scan_file(args.file)
        summarize(res)
        print("file:", res.get("file"))
        print("md5:", res.get("md5"), " lines:", res.get("lines"), " decls:", res.get("decls_total"),
              " (v2kinds:", res.get("decls_v2kinds"), " instance:", len(res.get("instance_ledger", [])), ")")
        print("RED stations:", res["red_names"])
        print("WHITELIST stations:", res["wl_names"])
        print("CAPTURE stations:", res["capture_stations"])
        print("clean stations（器账口径·非清白判词）:", res["clean_count"])
        print("by_cat:", res["by_cat"])
        print("frozen_by_cat:", res["frozen_by_cat"], " frozen hits:", res["frozen_hits_n"])
        print("mixed faces:", len(res["mixed_faces"]),
              [(m["name"], m["decl_line"]) for m in res["mixed_faces"]][:20])
        print()
        print_inventory(res, hits_csv=args.hits_csv)
        if args.manifest:
            if os.path.exists(args.manifest):
                rec = reconcile_manifest(res, args.manifest)
                print("RECONCILE manifest:", rec["manifest"])
                print("  manifest_n=%d scanner_n=%d" % (rec["manifest_n"], rec["scanner_n"]))
                print("  SWALLOWED (manifest 吞名·器伤响亮·pocket 名单):", rec["swallowed"])
                print("  BLIND (扫描器盲区·器伤响亮):", rec["blind"])
                print("  kind_drift:", rec["kind_drift"], " line_drift_n:", len(rec["line_drift"]))
                res["reconcile"] = rec
            else:
                print("RECONCILE manifest missing:", args.manifest)
        if args.json:
            json.dump(res, io.open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        sys.exit(0)
    ap.print_help()


if __name__ == "__main__":
    main()
