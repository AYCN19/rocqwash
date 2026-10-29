#!/usr/bin/env python3
# retrofit_gate7_irr.py — gate7 英化 retrofit（验证员·UpReqIrrationalCriterion·20261029）
# 只动注释不动物义 token；头注重建两段式五字段（30 行帽）；CJK→0·中文标点→0·非 ASCII→0。
# fail-loud：md5 冻结断言、逐行底账断言、token 流恒等断言、行数/字符断言，任一失败即退出非零不落盘。
import hashlib, io, re, sys

SEAT = "/Users/apple/Desktop/S系Prop清除战役工单/work_Main_full/sandbox/wf_irr2"
SRC = SEAT + "/UpReqIrrationalCriterion.v"
OUT = SEAT + "/r4verify_irr/src_final/UpReqIrrationalCriterion.v"
FROZEN_MD5 = "40d4a3b7adf9316ccbbed49ec86ab3ea"
HEADER_OLD_LINES = 34  # lines 1-34 (two comment blocks) replaced wholesale

CJK = re.compile(r"[\u4e00-\u9fff]")
CJKPUNCT = re.compile(r"[\u3000-\u303f\uff00-\uffef\u2018\u2019\u201c\u201d\u2026\u00b7\u2190-\u2193\u21d0-\u21d4\u2200-\u2203\u2207\u2212\u2208\u220b\u2264\u2265\u2260\u2248\u2211\u221a\u221e\u2229\u222a\u2295\u2297\u2550\u2500\u27f6\u27fa]")

def md5_of(path):
    return hashlib.md5(io.open(path, "rb").read()).hexdigest()

def strip_comments(text):
    out, depth, i = [], 0, 0
    while i < len(text):
        if depth == 0 and text.startswith("(*", i):
            depth = 1; i += 2; out.append(" ")
        elif depth > 0 and text.startswith("(*", i):
            depth += 1; i += 2
        elif depth > 0 and text.startswith("*)", i):
            depth -= 1; i += 2
        else:
            if depth > 0:
                if text[i] == "\n":
                    out.append("\n")
            else:
                out.append(text[i])
            i += 1
    assert depth == 0, "unbalanced comments"
    return "".join(out)

def toks(text):
    return re.findall(r"\S+", strip_comments(text))

# ---- new header: two-part five-field, <=30 lines, pure ASCII ----
HEADER = [
"(* ConstructiveWorld-Main -> Set - UpReqIrrationalCriterion: a constructive",
"   irrationality criterion for limits of rational approximation sequences. *)",
"(** * UpReqIrrationalCriterion: constructive irrationality criterion.",
"",
"    Mission.  Generalize the engine \"partial sums of e escape every rational\"",
"      (SumInvFactEscape) to a constructive irrationality criterion: for an",
"      approximation sequence x_n with error window e_n, if (i) the tail is",
"      controlled (|x_k - x_n| < e_n for n >= 1), (ii) every rational q escapes",
"      the e_n window at some n >= 1, and (iii) e_n -> 0 on the Q layer, then",
"      X := lim x_n admits, for every q : Q, a positive Q-layer separation",
"      constant c with real_const c < |X - q| (real_lt sigT witness form).",
"      Main statement: lic_irrational_criterion; companions lic_seq_cauchy (the",
"      Cauchy property) and lic_e_irrational_criterion (the e instance, through",
"      the mother theorem). The engine's escape witness may sit at n = 0; the",
"      n >= 1 witness comes from lic_enum (reusing sif_dec_pt) + lic_window_shift",
"      (clone of sif_window on [1, 2b+2]) + sif_zero_escape; no new content.",
"    Dependencies.  This development [S01_BaseRing], [S02_CauchyComplete],",
"      [S03_QExp], [SumInvFactEscape], [UpReqBanachNormOpp]; Stdlib [QArith],",
"      [ZArith], [Arith.Factorial], [Lia], [Setoid], [Morphisms], [Qfield].",
"    References.  The instance engine [SumInvFactEscape] (sif_escape witness for",
"      the partial sums of e); classical irrationality of e, constructively stated:",
"      separation from each rational is explicitly witnessed.",
"    Constructivity.  Statements on the Set face ([QltT], [QleT'], [QeqT],",
"      [NatLe], [real_lt] sigT form); no classical logic, no excluded middle,",
"      no admitted goals; in-proof Prop ([Qlt]/[Qle]) is Q-layer scaffolding",
"      only, never a conclusion face; every statement closes by Qed/Defined;",
"      both tail [Print Assumptions] audits read Closed. Declaration face",
"      verbatim; toy-proof bodies: [lic_e_irrational_criterion], [lic_qltt_comp_r].",
"    Build.  [rocq c -native-compiler no -q -Q . \"\" UpReqIrrationalCriterion.v]",
"      exits 0 against the S01/S02/S03 + SumInvFactEscape + UpReqBanachNormOpp artifacts. *)",
]

# ---- body line map: line_no -> (must_contain, new_line) ----
M = {
 47:  ("S0：Q 层通用小件", "(* S0. Small Q-layer utilities                                   *)"),
 50:  ("洗形站1：结论面 Qlt→QltT·Qlt_to_QltT 提升桥", "(* Right composition of Qlt along Qeq; conclusion face QltT via the Qlt_to_QltT lift. *)"),
 68:  ("洗形引用面适配：lic_qlt_comp_r 已 QltT 直供", "(* QltT right composition along Qeq: lic_qlt_comp_r supplies the QltT face directly. *)"),
 96:  ("洗形站5：结论面 Qle→QleT'", "(* Linear Qle assembly: u+v <= w and t <= v imply u+t <= w (conclusion face QleT'). *)"),
 105: ("Q 序小件（全 destruct-Q 机械模式，零 micromega-on-Q 依赖）", "(* Q-order utilities: mechanical destruct-Q pattern throughout, no micromega-on-Q dependency. *)"),
 107: ("洗形站6：结论面 Qlt→QltT", "(* Right addition preserves order (conclusion face QltT). *)"),
 126: ("洗形站7：结论面 Qlt→QltT", "(* Left addition preserves order (conclusion face QltT). *)"),
 145: ("洗形站8：结论面 Qlt→QltT", "(* Strictness by addition: 0 < b implies a < a + b (conclusion face QltT). *)"),
 152: ("洗形站9：结论面 Qlt→QltT", "(* Positivity of subtraction: E < A implies 0 < A - E (conclusion face QltT). *)"),
 159: ("Qlt_bool 桥（全序可判定，destruct-Q 机械模式；洗形站10：结论面 Qlt→QltT）", "(* Qlt_bool bridge: the order on Q is decidable (destruct-Q pattern; conclusion face QltT). *)"),
 168: ("洗形站11：结论面 Qle→QleT'", "(* Conclusion face QleT'. *)"),
 181: ("洗形站12：结论面 ==→QeqT", "(* Subtract then add back: ((B - c) + c) == B (conclusion face QeqT). *)"),
 189: ("洗形站13：结论面 Qlt→QltT；false_le 经 QleT'_to_Qle 回落", "(* Left-addition cancellation (conclusion face QltT; false branch lowered via QleT'_to_Qle). *)"),
 203: ("洗形站14：结论面 Qlt→QltT；lic_qlt_add_l_cancel QltT 直供", "(* Right-addition cancellation (conclusion face QltT; lic_qlt_add_l_cancel supplies QltT directly). *)"),
 212: ("洗形站15：结论面 ==→QeqT", "(* Triangle decomposition: q - a == (q - b) + (b - a) (conclusion face QeqT). *)"),
 220: ("洗形站16：结论面 Qle→QleT'", "(* Total-order completion: not (y < x) implies x <= y (conclusion face QleT'). *)"),
 227: ("洗形站17：结论面 ==→QeqT", "(* Half-value bridge: c == (A - E)/2 implies c + c == A - E (conclusion face QeqT). *)"),
 240: ("S1：母定理（构造性无理性判据）", "(* S1. The mother theorem (constructive irrationality criterion) *)"),
 243: ("尾控：n≥1 起，序列尾部 n 之后的项都在以 x_n 为心、e_n 为半径的窗内", "(* Tail control: from n >= 1 on, every term after n lies in the window centered at x_n of radius e_n. *)"),
 248: ("逃逸窗：每个有理数 q 都在某 n≥1 处逃出 e_n 窗（Q 层显式见证）", "(* Escape window: every rational q escapes the e_n window at some n >= 1 (explicit Q-layer witness). *)"),
 253: ("窗宽消失：e_n -> 0（逐 eps 显式 N）", "(* Vanishing window width: e_n -> 0 (explicit N for each eps). *)"),
 258: ("柯西性推导：尾控 + 窗宽消失 ⟹ x 柯西（N 取 max N 1 避开 n=0 区）", "(* Cauchy property: tail control + vanishing width imply x is Cauchy (N := max N 1 avoids the n = 0 region). *)"),
 282: ("real_metric 逐点投影（real_abs/real_plus/real_opp/real_const 全 Defined 可归约）", "(* Pointwise projection of real_metric (real_abs/real_plus/real_opp/real_const are all"),
 283: ("洗形站18：结论面 ==→QeqT） *", "   Defined, hence reducible; conclusion face QeqT). *)"),
 292: ("===== 母定理主件 =====", "(* ===== The mother theorem ===== *)"),
 293: ("语义：q 若总在有限窗外逃逸而极限被窗罩住，则 X 与 q 有正间隔。", "(* Reading: if q escapes every finite window while the limit is trapped by the window, X and q have a positive gap. *)"),
 388: ("S2：e 实例的 Q 层供给（尾控 + 窗宽消失）", "(* S2. Q-layer supply for the e instance (tail control + vanishing width) *)"),
 391: ("尾部尾和：Σ_{i=1}^{K} 1/(n+i)! *", "(* Trailing tail sum: sum_{i=1}^{K} 1/(n+i)!. *)"),
 398: ("洗形站19：结论面 Qle→QleT'；q_fact_pos/sif_qfact_Z 经 Set 树 QltT/QeqT 面）", "(* Conclusion face QleT'; q_fact_pos/sif_qfact_Z are consumed on their QltT/QeqT faces,"),
 399: ("适配（QltT_to_Qlt 回落＋qeqT_imp_qeq 转写） *)", "   lowered by QltT_to_Qlt and transported by qeqT_imp_qeq. *)"),
 417: ("exp_series 差 = 尾和（bno_exp_series_succ_frac 递推 + 归纳）", "(* exp_series difference = tail sum (bno_exp_series_succ_frac recurrence + induction;"),
 418: ("洗形站20：结论面 ==→QeqT；bno_exp_series_succ_frac Set 树 QeqT 面转写） *)", "   conclusion face QeqT, consuming bno_exp_series_succ_frac on its QeqT face). *)"),
 435: ("核心归纳：C·(A·Σ) + A ≤ C，其中 A=n!、C=(n+K)!（r_{K+1}=r_K/(n+K+1) 倍增形）", "(* Core induction: C*(A*sum) + A <= C with A = n!, C = (n+K)! (step form r_{K+1} = r_K/(n+K+1);"),
 436: ("洗形站21：结论面 Qle→QleT'；bno_mul_div_self/q_fact_pos Set 树面适配） *)", "   conclusion face QleT'; bno_mul_div_self/q_fact_pos consumed on their Set faces). *)"),
 461: ("目标：((z#1)*B) * (A * (L + V)) + A ≤ (z#1)*B，V := 1/((z#1)*B)", "    (* Goal: ((z#1)*B) * (A * (L + V)) + A <= (z#1)*B with V := 1/((z#1)*B). *)"),
 505: ("形状重排：c*(a*b) < c ⟹ (c*a)*b < c*1（destruct-Q 机械模式）", "(* Shape reshuffle: c*(a*b) < c implies (c*a)*b < c*1 (destruct-Q pattern;"),
 506: ("洗形站22：结论面 Qlt→QltT） *)", "   conclusion face QltT). *)"),
 520: ("尾和 < 1/n!（n ≥ 1） *", "(* Tail sum < 1/n! (n >= 1). *)"),
 521: ("辅助：1/x 的正性（洗形站23：结论面 Qlt→QltT）", "(* Auxiliary: positivity of 1/x (conclusion face QltT). *)"),
 529: ("尾和 < 1/n!（n ≥ 1）（洗形站24：结论面 Qlt→QltT；lic_core/lic_core 面", "(* Tail sum < 1/n! (n >= 1; conclusion face QltT; lic_core consumed on its QleT' face"),
 530: ("经 QleT'_to_Qle/QltT_to_Qlt 回落；bno_mul_div_self Set 树面预证零化） *)", "   via QleT'_to_Qle; the bno_mul_div_self vanishing premise pre-proved on the Set face). *)"),
 538: ("严格化：qf·(n!·X) < qf（加 n! 严格增，再 ≤ qf，n! > 0）", "  (* Strictification: qf*(n!*X) < qf (adding n! strictly increases, then <= qf as n! > 0). *)"),
 548: ("除以 (n+K)!：n!·X < 1", "  (* Divide by (n+K)!: n!*X < 1. *)"),
 554: ("除以 n!：X < 1/n!", "  (* Divide by n!: X < 1/n!. *)"),
 564: ("尾控实例：|exp_series k 1 − exp_series n 1| = 尾和 < 1/n!（n ≥ 1）", "(* Tail-control instance: |exp_series k 1 - exp_series n 1| = tail sum < 1/n! (n >= 1)."),
 565: ("（QltT 目标先降 Qlt Prop 层再做 Qeq 换元——lic_qltt_comp_r 同款 idiom；", "   The QltT goal is first lowered to the Qlt Prop layer, then Qeq-substituted (the"),
 566: ("lic_rsum_lt/lic_exp_diff/lic_rsum_ge0 洗后 Set 面经桥件回落 Prop 脚手架） *)", "   lic_qltt_comp_r idiom; the Set-face inputs are lowered to Prop scaffolding by bridges). *)"),
 584: ("窗宽消失实例：1/n! -> 0（显式 N := den(eps)+1：n > den ⟹ 1/n ≤ 1/n! < eps；", "(* Vanishing instance: 1/n! -> 0 (explicit N := den(eps)+1: n > den implies 1/n <= 1/n! < eps;"),
 585: ("Q 层链：1/eps ≤ den(eps) < n ≤ n! ，末步 Qinv_lt_contravar 转置）", "   Q-layer chain 1/eps <= den(eps) < n <= n!, last step by Qinv_lt_contravar)."),
 586: ("lic_fact_ge_self 洗后 NatLe 面经 NatLe_drop 回落） *)", "   (lic_fact_ge_self is consumed on its NatLe face, lowered by NatLe_drop.) *)"),
 625: ("S3：e 实例的窗口供给（见证 n ≥ 1 升级：枚举 + 平移窗 + 零点两步逃逸）", "(* S3. Window supply for the e instance (witness upgrade to n >= 1: enumeration)   *)"),
 628: ("sif 逃逸见证的窗形式换算：1 < |n!·(q − s_n)| ⟺ 1/n! < |q − s_n|", "(* Window-form conversion of the sif escape witness: 1 < |n!*(q - s_n)| iff 1/n! < |q - s_n|"),
 629: ("（q_fact_pos/bno_mul_div_self Set 树面适配：QltT_to_Qlt 回落＋qeqT_imp_qeq", "   (q_fact_pos/bno_mul_div_self consumed on their Set faces: lowered by QltT_to_Qlt and"),
 630: ("转写，零化前提预证 Hqf0 前置） *)", "   transported by qeqT_imp_qeq, with the vanishing premise Hqf0 pre-proved up front) *)"),
 661: ("平移窗引理（sif_window 的 [1,2b+2] 克隆）：d_k 序列若在 k ∈ [1,2b+2]", "(* Shifted-window lemma (clone of sif_window on [1, 2b+2]): if the sequence d_k is"),
 662: ("全程非零且 |d_k| ≤ b，则矛盾。负支一步逃逸（k≥1 保系数 ≥2）、", "   nonzero throughout k in [1, 2b+2] with |d_k| <= b, contradiction. Negative branch:"),
 663: ("正支回溯窗 (2b+2)·d_{2b+1} = d_{2b+2} + b ≤ 2b 与 d_{2b+1} ≥ 1 矛盾。", "   one-step escape (k >= 1 keeps the factor >= 2); positive branch: tracing back the"),
 664: ("（候裁档 P3_false 结论面原样保留（禁擅裁）；证内 sif_d_succ/sif_posZ", "   window, (2b+2)*d_{2b+1} = d_{2b+2} + b <= 2b contradicts d_{2b+1} >= 1."),
 665: ("Set 树 Id 面经 J-消去桥（match id_refl）落 eq 层） *)", "   (sif_d_succ/sif_posZ are consumed on their Id faces via J-elimination (match id_refl) onto eq.) *)"),
 712: ("终局矛盾：d_{N-1} ≥ 1 ⟹ N·d_{N-1} ≥ N = 2b+2 > 2b ≥ N·d_{N-1}", "  (* Final contradiction: d_{N-1} >= 1 implies N*d_{N-1} >= N = 2b+2 > 2b >= N*d_{N-1}. *)"),
 724: ("Type 层有界枚举（n 从 1 起；判定件复用 sif_dec_pt；", "(* Type-layer bounded enumeration (n from 1; decider reused from sif_dec_pt;"),
 725: ("洗形站2：界谓词 (≤)%nat→NatLe（sif_enum Set 树判例同款）） *)", "   bound predicate (<=)%nat on the NatLe face, as in the sif_enum instance) *)"),
 772: ("e 实例窗口供给：每个 q 有 n ≥ 1 使 1/n! < |q − s_n|。", "(* Window supply for the e instance: every q has some n >= 1 with 1/n! < |q - s_n|."),
 773: ("枚举失败支由平移窗 + 零点两步逃逸（复用 sif_zero_escape/sif_hit_of_dd/", "   The failed-enumeration branch derives a contradiction from the shifted window + two-step"),
 774: ("sif_abs_frac）导出矛盾——构造性 exfalso（Empty_set 消去）。", "   zero escape (reusing sif_zero_escape/sif_hit_of_dd/sif_abs_frac): a constructive"),
 775: ("lic_enum 洗后 NatLe 面经 NatLe_lift 进位；sif_zero_escape Set 树 Id 面", "   exfalso (Empty_set elimination); the NatLe bounds carry through NatLe_lift, and"),
 776: ("经 J-消去桥＋Z.ltb_lt 回落 Prop 严格序） *)", "   sif_zero_escape is consumed on its Id face via J-elimination + Z.ltb_lt onto the Prop strict order) *)"),
 817: ("S4：e 实例回验装配（真走母定理）+ 提取检验 + 公理面自审", "(* S4. e-instance verification assembly (through the mother theorem) + extraction   *)"),
 820: ("e 的无理性（判据形）：X := lim Σ_{j≤n} 1/j!，对任意有理数 q 存在", "(* Irrationality of e (criterion form): X := lim sum_{j<=n} 1/j!; for every rational q"),
 821: ("Q 层正分离常数 c 使 real_const c < |X − q|。 *)", "   there is a Q-layer positive separation constant c with real_const c < |X - q|. *)"),
}

def main():
    md5 = md5_of(SRC)
    assert md5 == FROZEN_MD5, "FROZEN MD5 MISMATCH: %s" % md5
    text = io.open(SRC, encoding="utf-8", newline="").read()
    assert "\r" not in text, "unexpected CR"
    lines = text.split("\n")
    assert len(lines) == 843 and lines[-1] == "", "line shape %d" % len(lines)  # 842 newline-terminated lines

    # assert header zone boundary: line 34 is the closing separator, line 35 blank, line 36 first Require
    assert lines[33].startswith("(* ===="), lines[33][:60]
    assert lines[34] == "", repr(lines[34])
    assert lines[35] == "Require Import S01_BaseRing.", repr(lines[35])

    # fail-loud: every mapped line must contain its must_contain anchor
    for ln, (anchor, _new) in sorted(M.items()):
        assert anchor in lines[ln - 1], "line %d anchor mismatch: %r" % (ln, lines[ln - 1][:90])

    # fail-loud coverage: every CJK/CJKPUNCT line outside the header zone is mapped
    need = {i + 1 for i, l in enumerate(lines) if (CJK.search(l) or CJKPUNCT.search(l))}
    unmapped = sorted(n for n in need if n > HEADER_OLD_LINES and n not in M)
    assert not unmapped, "UNMAPPED CJK lines: %r" % unmapped[:20]
    unused = sorted(n for n in M if n not in need)
    assert not unused, "MAPPED-ON-CLEAN lines: %r" % unused
    print("coverage: %d body CJK lines mapped, header zone %d lines replaced" % (len(M), HEADER_OLD_LINES))

    # header assertions: <=30 cap, pure ASCII, five fields present
    assert len(HEADER) <= 30, "HEADER CAP BLOWN: %d lines" % len(HEADER)
    assert all(ord(ch) < 128 for l in HEADER for ch in l), "non-ASCII in header"
    for field in ["Mission.", "Dependencies.", "References.", "Constructivity.", "Build."]:
        assert any(field in l for l in HEADER), "missing field %s" % field
    hdr = "\n".join(HEADER)
    assert hdr.count("(*") == 2 and hdr.count("*)") == 2, "header comment structure"

    out_lines = HEADER + [M[n][1] if n in M else l for n, l in enumerate(lines[HEADER_OLD_LINES:], HEADER_OLD_LINES + 1)]
    out_text = "\n".join(out_lines)

    # gate assertions on output
    assert not CJK.search(out_text), "residual CJK"
    assert not CJKPUNCT.search(out_text), "residual CJK punct"
    assert all(ord(ch) < 128 for ch in out_text), "residual non-ASCII"
    assert len(out_lines) == len(HEADER) - HEADER_OLD_LINES + 843, "line arithmetic"

    # comment-stripped token-stream identity (statement face untouched)
    t_old, t_new = toks(text), toks(out_text)
    if t_old != t_new:
        for i, (a, b) in enumerate(zip(t_old, t_new)):
            if a != b:
                print("TOKEN DIVERGENCE at %d: %r != %r" % (i, a, b))
                print("ctx old: %r" % t_old[max(0, i - 6):i + 6])
                print("ctx new: %r" % t_new[max(0, i - 6):i + 6])
                break
        assert False, "TOKEN STREAM NOT IDENTICAL (%d vs %d tokens)" % (len(t_old), len(t_new))
    print("token identity: %d tokens identical (comment-stripped, whitespace-normalized)" % len(t_old))

    io.open(OUT, "w", encoding="utf-8", newline="\n").write(out_text)
    out_md5 = md5_of(OUT)
    print("header: %d lines (cap 30); old 34 -> shift %+d for body" % (len(HEADER), len(HEADER) - HEADER_OLD_LINES))
    print("WROTE %s" % OUT)
    print("NEW MD5: %s" % out_md5)

if __name__ == "__main__":
    main()
