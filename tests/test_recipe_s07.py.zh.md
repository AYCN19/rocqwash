#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_recipe_s07.py — recipes/S07_projection_reanchor_E5.md 处方件自测
（tests/·五课反馈轮·agent rqsupport·20261101）

五课夹具⑤【三判例剧本·S07 投影重锚 E5】：Class 字段投影承载语句面 → 提取
Obj.magic（判例基线 293）；处方＝语句面重锚具体面 req→real_eq／lt→real_lt／
le→real_le。判例源：seat_reanchor/账/迁移账-六件重锚.md（UpReqSampling 判例：
magic 293→0·118 token 三映射·96 行脉冲·语句名 51=51/67=67 零漂移）。

  1 处方件在册  recipes/S07_projection_reanchor_E5.md 在盘且判例锚词面齐
                （E5／S07_RealSetoidExpLog.v:8075／S02 三定义位／293→0／96 行／
                三映射对／验收四证词）
  2 E5 病面负例 夹具 .v 语句面裸投影（`req (f s) (g s)`·Lemma 签名位）→ 机检命中
  3 注释掩蔽负例 同 token 在 (*…*) 注释内（含嵌套注释）→ 机检不命中
                （剥注释状态机=冻结件 scan/mac_stmt_scan.py:104 词面核同款；
                 经 wash/wash_engine.py 只读 import 复用·零字节触冻结伴）
  4 愈面正判    重锚后夹具（real_eq/real_lt/real_le 具体面）→ 机检零命中
  5 冻结旁证    wash/wash_engine.py md5 == 在册冻结值 664446bc…（只读 import 面零触）

幂等：临时目录即写即清·零仓库写盘·零编译零网络。
退出码：0=五判全过；1=任一红。
"""
import hashlib
import io
import os
import re
import sys
import tempfile
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECIPE = os.path.join(REPO, "recipes", "S07_projection_reanchor_E5.md")
ENGINE = os.path.join(REPO, "wash", "wash_engine.py")
ENGINE_FROZEN_MD5 = "664446bc717395d8496c8c30a5af9ccf"  # 更新账.md §三在册值

RECIPE_ANCHORS = [
    "E5", "S07_RealSetoidExpLog.v:8075", "S07_RealSetoidExpLog.v:8740",
    "S02_CauchyComplete.v", "293", "96 lines", "118",
    "real_eq", "real_lt", "real_le",
    "436f7121", "UpReqSampling", "cure",  # 验收四证段词 (anchor migrated to the English face token, unit u8)
]

# 语句面命令词（处方刀面：签名面语句含 Variable/Hypothesis 槽·E5 判例 51 条口径）
STMT_HEAD = re.compile(r"^\s*(Theorem|Lemma|Corollary|Proposition|Example|Remark|Fact|"
                       r"Definition|Fixpoint|Function|Instance|"
                       r"Variable|Variables|Hypothesis|Hypotheses)\b")
BARE_PROJ = re.compile(r"(?<![A-Za-z0-9_'])(req|lt|le)(?![A-Za-z0-9_'])")


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def statement_bare_hits(text):
    """E5 病面机检：注释/字符串掩蔽后（冻结引擎状态机·只读 import），语句面找裸投影
    token。语句面＝自语句头行起、至句点收束的整段（判例签名面系多行连排——
    `forall …` 续行与头行同治）。返回命中 [(行号, token)]。愈面（real_eq 等具体面）
    不含裸 token 形，天然零命中。"""
    sys.path.insert(0, os.path.dirname(ENGINE))
    import wash_engine  # noqa: E402（在役冻结件·只 import 不改）
    clean = wash_engine.strip_comments_strings(text)
    lines = clean.split("\n")
    hits = []
    in_stmt = False
    for lineno, line in enumerate(lines, 1):
        if STMT_HEAD.match(line):
            in_stmt = True
        if in_stmt:
            for m in BARE_PROJ.finditer(line):
                hits.append((lineno, m.group(1)))
            if line.rstrip().endswith("."):
                in_stmt = False  # 句点收束（Proof./Qed. 同形收束）
    return hits


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_trecipes07_")
    try:
        # 1 处方件在册＋判例锚词面齐
        ok1 = os.path.isfile(RECIPE)
        if ok1:
            with io.open(RECIPE, encoding="utf-8") as fh:
                doc = fh.read()
            missing = [a for a in RECIPE_ANCHORS if a not in doc]
            ok1 = not missing
        else:
            missing = ["<处方件整缺>"]
        check("处方件锚词面", ok1, "缺锚=%s" % missing)

        # 2【E5 病面负例】语句面裸投影 → 命中
        sick = ("(* req lt le 注释位裸 token 不算 *)\n"
                "Section S.\n"
                "Variable sumf : (Real -> Real) -> Real.\n"
                "Lemma row_norm : forall (f : Real -> Real),\n"
                "  (forall s : Real, req (f s) (f s)) -> req (sumf f) (sumf f).\n"
                "Proof. intros. apply H. Qed.\n"
                "End S.\n")
        hits = statement_bare_hits(sick)
        check("E5_病面负例_命中", len(hits) == 2 and all(t == "req" for _, t in hits)
              and hits[0][0] == 5,  # 跨行语句连排同治（L5 续行两枚裸投影）
              "hits=%s" % hits)

        # 3 注释掩蔽负例：整句裸投影全在嵌套注释内 → 零命中（含子串不误咬）
        masked = ("(* Lemma ghost : req x y -> lt a b. （病面示范·注释位不进提取面） *)\n"
                  "(* 外 (* 内嵌 lt le req *) 注释 *)\n"
                  "Lemma fine : mult one one = one. (* mult 内含 lt 子串·全词律不咬 *)\n"
                  "Proof. reflexivity. Qed.\n")
        hits_m = statement_bare_hits(masked)
        check("注释掩蔽负例_零命中", hits_m == [], "hits=%s" % hits_m)

        # 4【愈面正判】重锚后夹具（三映射落刀·判例 UpReqSampling 同形）→ 零命中
        cured = sick.replace("req (f s) (f s)) -> req (sumf f) (sumf f)",
                             "real_eq (f s) (f s)) -> real_eq (sumf f) (sumf f)")
        hits_c = statement_bare_hits(cured)
        check("E5_愈面正判_零命中", hits_c == [] and "real_eq" in cured,
              "hits=%s" % hits_c)

        # 5 冻结旁证：引擎 md5 仍=在册冻结值（只读 import 面零触）
        check("冻结件零触", md5_of(ENGINE) == ENGINE_FROZEN_MD5,
              "md5=%s" % md5_of(ENGINE))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-18s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-RECIPE-S07 FAIL: %d/%d 红" % (len(fails), len(checks)))
            return 1
        print("TEST-RECIPE-S07 PASS: 处方件锚/E5病面负例/注释掩蔽负例/愈面正判/"
              "冻结旁证 五判全过（五课夹具⑤三判例剧本·S07 投影重锚 E5）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
