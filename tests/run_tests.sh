#!/bin/bash
# run_tests.sh — rocqwash tests/ 自测套件总入口（rocqwash tests/·20261030）
#
# 形制：
#   - 逐例 PASS/FAIL 汇总；全绿 EXIT 0；任一红 EXIT 1。
#   - 幂等：不向仓库写任何字节（python3 -B 禁 __pycache__；临时日志 mktemp+trap 清理；
#     wash/retrofit 测试只在临时目录/内存驱动，硬编码席位路径永不被触碰）。重复运行结果恒同。
#   - 覆盖面（每例正/负两判优先）：
#       scan/mac_stmt_scan.py   --selftest（E364 冻结向量组）
#       names/mac_stmt_names.py --expect 形（fixture 正判/含-Let/负判 exit 2）
#       verify/gate4_comment_guard.py --file（净样例 PASS=0 / 脏样例 FAIL=1 两判）
#       verify/retrofit_gate7_irr.py 干跑（tests/test_retrofit_dryrun.py·零落盘）
#       wash/_abl1_wash.py exact-string+count（tests/test_wash_fixture.py·正/幂等/负三判）
#       wash/wash_engine.py 通用逐件引擎（tests/test_wash_engine.py·六判 subprocess）
#       verify/verify_vo.py 绿判四件套（--selftest 九判）
#       seam/seam_probe.py W13 四机制（--selftest 四正例＋掩蔽负例）
#       certify/freeze_manifest.py 两层冻结（--selftest 四判）
#       certify/push_gate.py 推窗四判据＋UNION v2（--selftest UNION 六判＋window 四判）
#       certify/frozen8.py 八件冻结名单（--selftest 账载四判＋在册名单对账·账载≡文档/盘≡账/篡改现形）
#       watch/watch.py CI 监控＋钉 IP 推送＋confirm（--selftest 零网络向量组）
#       tools/cpu_guard.sh -Direct 冒烟（探针一发即退＋退出码传播）
#       wrapper/scan_station.py 正本指认包装（tests/test_scan_station.py·九判零写盘）
#       wrapper/gate7_probe.sh＋coqc_shim.sh gate7 探针链适配层（tests/test_gate7_wrapper.py·十三判零编译零写盘）
#       wrapper/gate6_census.sh＋born_world.sh gate6 普查闸启动层＋born 世界基正形
#         （tests/test_gate6_born_wrapper.py·二十一判零编译零写盘）
#       wrapper/verify_born.py born 轮判绿接线（tests/test_verify_born.py·九判零写盘）
#       wrapper/quad8_reconcile.py 四仓同 md5 副本群对账（--selftest 夹具八判＋
#         在册四仓名单对账 t_quad8_check·11 副本/六环咬合/audit 只录不判·零写盘）
#       wrapper/frozen_call.py 逐调断言（--selftest 夹具五判·PASS 透传入账/拒执四向）
#       wash/world_hook.py 世界基校验钩子（tests/test_world_hook.py·五判·五课负例①nw5）
#       tools/select_audit.py 选件审计器（tests/test_select_audit.py·二十判·五课负例②nw6＋③enbig7
#         ＋v6 判据 nw10/abl6 空账：parse_requires 全形式/STDLIB_ROOTS 豁免/
#         audit_requires 世界 .v/.vo 存在性闭包/实盘补件面＋CLI 四码）
#       verify/verify_gate6.py gate6 薄包装＋eum 判例器化（tests/test_verify_gate6.py·五判·五课夹具④）
#       recipes/S07 处方件＋E5 病面机检（tests/test_recipe_s07.py·五判·五课夹具⑤）
#       tools/netname_normalize.py .v.v 双后缀名净名归一器（tests/test_netname_normalize.py·
#         九节·本轮实战判例工具化①：干跑默认零落盘/--apply md5 前后验讫/COLLIDE 拒覆写/CLI 四码）
#       verify/verify_vo.py --require-fresh fresh-compile 防线（tests/test_verify_fresh.py·
#         八节·本轮实战判例工具化②：divmod_gen 陈旧 vo 假绿判例——魔数＋新鲜度双判 rc=9 fail-loud）
#       verify/extract_magic_check.py gate7 提取面 Obj.magic 逐件机检闸（tests/test_extract_magic.py·
#         十一节·本轮实战判例工具化③：run97/98 gate7 三件涨账 28/4/1 坑账第十笔工具化——
#         Separate Extraction 解析→rocq 提取→ocamlc→grep -c Obj.magic→--max 判红绿·假桩全链零真编译；
#         v15 增盲区补全节：首战 G09 Class/G13 Extraction 双红→DECL_SKIP_EXT 声明/命令
#         vernacular 就地扩补·Class 声明夹具 census 不误判·未知 vernacular 仍红 9）
#       scan/scan_v4_token.py token 级限定名普查（tests/test_scan_v4_token.py·十一判·
#         W15 实战判例工具化①：混合行遮蔽夹具三站复现＋旧法盲区机械实证＋binder 追踪
#         零误报；真树抽查经 ROCWASH_TREE_SAMPLES 环境门控·缺省跳过不充红）
#       wash/cure_pack.json＋cure_applier.py 消费位治愈正典包五式（tests/test_cure_pack.py·
#         十一判·W15 工具化②：五式触发/幂等/门控自检＋fixture 干跑-apply-二次零变更＋
#         cure_examples.v 编译 rc=0（ROCWASH_ROCQ 门控·cpu_guard 包裹）＋不透明
#         reflexivity 负证 rc!=0）
#       verify/erasure_classifier.py 擦除位分类器六簇（tests/test_erasure_classifier.py·
#         十三判·W15 工具化③：六簇判定/coq_ 前缀/多行 inner-component/premise 位/
#         CAPTURE 交叉对拍/resolve 状态；真件回放经 ROCWASH_ERASURE_MLI/SCAN 门控）
#       wash/probe_engine.py 批量闭包相容探针引擎（tests/test_probe_engine.py·九节·
#         v30 工具化①·承 W13 probe_batch.py：stub 全链 rc 三分 WASHABLE/BORN-CLEAN/
#         RED-MISSING_LIB·NO-SRC/TIMEOUT 124·resume 幂等同账字节恒同·guard 包裹
#         rc 真取·RED 缺列 RC0·CLI 四码·真 rocq 全链 ROCWASH_ROCQ 门控缺省 SKIP）
#       tools/chain_graph.py 多账合并链根图（tests/test_chain_graph.py·七节·
#         v30 工具化②·承 W25 w25_merge_ledgers.py：双形通吃/后批覆盖/batches 累积/
#         链根自身可洗性三分/missing 双源/TOP 榜排序截断＋确定性字节恒同/CLI 四码）
#       tools/ledger_sync.py probe×状态台账合并同步（tests/test_ledger_sync.py·
#         十节·v30 工具化③·v2.1 增补：CLEAN 升格全链/E1 去重/E3 幽灵/MD5-DRIFT/
#         NO-MD5/timeout·no-src 特异 tag/report JSON/列校验 fail-loud/幂等字节恒同/
#         CLI 四码/items 子键壳＋元数据滤除/GEN-DIVERGENCE 分歧出账）
#       wash/comment_pack.json＋comment_sweep.py 注释域 sweep 旁车（tests/test_comment_pack.py·
#         六节·v31 工具化：嵌套注释+字符串感知状态机/旗词换形/头注换代/
#         w7 code 行全等/幂等/CLI 四码）
#       scan/dual_scan.py 双器对拍驱动（tests/test_dual_scan.py·十节·
#         v32 工具化：scan_v4_token＋mac_stmt_scan 双扫×逐件差异报告
#         only_v4/only_stmt/common·确定字节恒同·CLI 四码·零触真仓）
#       wash/cure_pack v1.2 S07 适配式（tests/test_cure_pack.py 扩节·
#         cure32 壳除/记号重绑/投影桥/谓词面收敛/binder 站型·干跑-apply-
#         手术-全零复跑＋conflict --json rc4 回归＋门控 S07 编译弧红→绿→提取 0/0）
#
# 用法：
#   bash tests/run_tests.sh
#   ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh   # 套件自检：注入必红例，应 EXIT 1
#
# 退出码口径承 CONTRIBUTING §4：0=全绿（SKIP 不计红）；1=任一红。
# 例级 exit 111=SKIP：正本环境缺卷（CI runner 无本机正本）时，依赖正本的
# 对账/包装例让席不充红不假绿；正本在卷（真本机）恒全量真扫。
set -u

REPO=$(cd "$(dirname "$0")/.." && pwd)
FIX="$REPO/tests/fixtures"
PY=python3

# ---------- 正本环境探针（CI 准入）----------
# 四例（t_gate7_wrapper/t_quad8_check/t_gate6_born_wrapper/t_verify_gate6）的
# 在跑判据依赖本机正本：Set 仓 gates 正本脚本＋CW rocq 工具链＋四仓副本群。
# 正本缺卷 → 诸例 exit 2=SKIP；路径可用 ROCWASH_CANON_* 覆写（CI 演练用）。
CANON_SET=${ROCWASH_CANON_SET:-/Users/apple/Desktop/ConstructiveWorld-Set}
CANON_CW=${ROCWASH_CANON_CW:-/Users/apple/Desktop/ConstructiveWorld}
CANON_W1=${ROCWASH_CANON_W1:-/Users/apple/Desktop/S系Prop清除战役工单}
CANON=0
if [ -f "$CANON_SET/scripts/gates/gate6_statement_census.py" ] \
   && [ -f "$CANON_SET/scripts/gates/gate7_extract_run.py" ] \
   && [ -x "$CANON_CW/Live/toolchain/opam/live/bin/rocq" ]; then
  CANON=1
fi

PASS=0; FAIL=0; SKIP=0; TOTAL=0; REDS=""; SKIPS=""
LOG=$(mktemp /tmp/rocqwash_tests.XXXXXX)
trap 'rm -f "$LOG"' EXIT INT TERM

CASES="\
t_scan_selftest \
t_names_expect_pos \
t_names_expect_let \
t_names_expect_neg \
t_gate4_clean \
t_gate4_dirty \
t_retrofit_dryrun \
t_wash_judgments \
t_wash_engine \
t_verify_vo \
t_seam_probe \
t_freeze_manifest \
t_push_gate \
t_watch \
t_cpu_guard_direct_smoke \
t_cpu_guard_direct_rc \
t_scan_station \
t_gate7_wrapper \
t_verify_born \
t_frozen8 \
t_frozen8_check \
t_quad8 \
t_quad8_check \
t_frozen_call \
t_gate6_born_wrapper \
t_world_hook \
t_select_audit \
t_verify_gate6 \
t_recipe_s07 \
t_recipe_pw1 \
t_precedent_station \
t_netname_normalize \
t_verify_fresh \
t_extract_magic \
t_scan_v4_token \
t_cure_pack \
t_erasure_classifier \
t_probe_engine \
t_chain_graph \
t_ledger_sync \
t_comment_pack \
t_dual_scan"
NCASES=$(echo $CASES | wc -w | tr -d ' ')
if [ "${ROCQWASH_TESTS_FAIL_PROBE:-0}" = "1" ]; then
  CASES="$CASES t_fail_probe"
  NCASES=$((NCASES + 1))
fi

# ---------- 用例（每例自管退出码；0=该例绿） ----------

t_scan_selftest() {
  "$PY" -B "$REPO/scan/mac_stmt_scan.py" --selftest
}

t_names_expect_pos() {
  "$PY" -B "$REPO/names/mac_stmt_names.py" "$FIX/names_sample.v" --expect 7
}

t_names_expect_let() {
  "$PY" -B "$REPO/names/mac_stmt_names.py" "$FIX/names_sample.v" --include-let --expect 8
}

t_names_expect_neg() {
  "$PY" -B "$REPO/names/mac_stmt_names.py" "$FIX/names_sample.v" --expect 6 >/dev/null 2>&1
  local rc=$?
  [ "$rc" -eq 2 ] || { echo "负判应 exit 2（CONTRIBUTING §4 口径），实测 $rc"; return 1; }
}

t_gate4_clean() {
  "$PY" -B "$REPO/verify/gate4_comment_guard.py" --file "$FIX/gate4_clean_sample.v"
}

t_gate4_dirty() {
  "$PY" -B "$REPO/verify/gate4_comment_guard.py" --file "$FIX/gate4_dirty_sample.v" >/dev/null 2>&1
  local rc=$?
  [ "$rc" -eq 1 ] || { echo "脏样例应 FAIL exit 1，实测 $rc"; return 1; }
}

t_retrofit_dryrun() {
  "$PY" -B "$REPO/tests/test_retrofit_dryrun.py"
}

t_wash_judgments() {
  "$PY" -B "$REPO/tests/test_wash_fixture.py"
}

t_wash_engine() {
  "$PY" -B "$REPO/tests/test_wash_engine.py"
}

t_verify_vo() {
  "$PY" -B "$REPO/verify/verify_vo.py" --selftest
}

t_seam_probe() {
  "$PY" -B "$REPO/seam/seam_probe.py" --selftest
}

t_freeze_manifest() {
  "$PY" -B "$REPO/certify/freeze_manifest.py" --selftest
}

t_push_gate() {
  "$PY" -B "$REPO/certify/push_gate.py" --selftest
}

t_watch() {
  "$PY" -B "$REPO/watch/watch.py" --selftest
}

t_cpu_guard_direct_smoke() {
  local out rc
  out=$("$REPO/tools/cpu_guard.sh" -Direct -- true 2>&1)  # 探针一发即退（不排队不注册）
  rc=$?
  [ "$rc" -eq 0 ] || { echo "探针应 rc=0，实测 $rc"; echo "$out"; return 1; }
  case "$out" in
    *"DIRECT bypass"*) : ;;
    *) echo "缺 [cpu_guard] DIRECT bypass 横幅"; echo "$out"; return 1 ;;
  esac
}

t_cpu_guard_direct_rc() {
  "$REPO/tools/cpu_guard.sh" -Direct -- sh -c 'exit 7' >/dev/null 2>&1
  local rc=$?
  [ "$rc" -eq 7 ] || { echo "退出码应传播探针 rc=7，实测 $rc"; return 1; }
}

t_scan_station() {
  "$PY" -B "$REPO/tests/test_scan_station.py"
}

t_gate7_wrapper() {
  # judge11/13 依赖 Set 仓 gate7 正本；缺卷让席（正判/GATE7_PROBE_SCRIPT 覆写在卷则照跑）
  [ "$CANON" = "1" ] || [ -n "${GATE7_PROBE_SCRIPT:-}" ] || { echo "SKIP: gate7 正本不在卷（$CANON_SET/scripts/gates/gate7_extract_run.py）"; return 111; }
  "$PY" -B "$REPO/tests/test_gate7_wrapper.py"
}

t_verify_born() {
  "$PY" -B "$REPO/tests/test_verify_born.py"
}

t_frozen8() {
  "$PY" -B "$REPO/certify/frozen8.py" --selftest
}

t_frozen8_check() {
  # 在册八件冻结名单随套件在跑对账（推送轮 c4 套件绿即含八件对账绿·只读零写盘）
  "$PY" -B "$REPO/certify/frozen8.py" check \
    --list "$REPO/certify/frozen8_manifest.json" \
    --tier2 "$REPO/certify/frozen8_tier2.md5"
}

t_quad8() {
  # 四仓同 md5 副本群对账器夹具八判（零触真仓·20261031 席 rqadapt）
  "$PY" -B "$REPO/wrapper/quad8_reconcile.py" --selftest
}

t_quad8_check() {
  # 在册四仓对账名单随套件在跑对账（11 副本·audit 域只录不判·只读零写盘）
  # 副本群横跨四仓正本；缺卷让席（夹具八判 t_quad8 无依赖恒跑）
  [ -d "$CANON_CW" ] && [ -d "$CANON_SET" ] && [ -d "$CANON_W1" ] || { echo "SKIP: 四仓副本群不在卷（quad8 在跑对账仅真本机）"; return 111; }
  "$PY" -B "$REPO/wrapper/quad8_reconcile.py" check \
    --list "$REPO/wrapper/quad8_manifest.json" \
    --tier2 "$REPO/wrapper/quad8_tier2.md5"
}

t_frozen_call() {
  # wrapper 层逐调断言夹具五判（零触真仓真组件·临时账面）
  "$PY" -B "$REPO/wrapper/frozen_call.py" --selftest
}

t_gate6_born_wrapper() {
  # wrapper 层 gate6 普查闸启动层＋born 世界基正形十六判（零编译零写盘）
  # census 判据依赖 Set 仓 gate6 正本；born 判据依赖 CW rocq 工具链；缺卷让席
  [ "$CANON" = "1" ] || [ -n "${GATE6_SCRIPT:-}" ] || [ -n "${BORN_WORLD_ROCQ:-}" ] || { echo "SKIP: gate6 正本/rocq 工具链不在卷（$CANON_SET/scripts/gates/＋$CANON_CW/Live/toolchain）"; return 111; }
  "$PY" -B "$REPO/tests/test_gate6_born_wrapper.py"
}

t_world_hook() {
  # 五课反馈轮·负例①nw5 世界偏斜：born 前断言拦下＋冻结引擎零触旁证（零编译零写盘）
  "$PY" -B "$REPO/tests/test_world_hook.py"
}

t_select_audit() {
  # 五课反馈轮·负例②nw6 批内重复＋③enbig7 跨批撞名＋v6 判据 nw10/abl6 空账
  # Require 面（parse_requires/STDLIB_ROOTS/audit_requires·零仓库写盘零网络）
  "$PY" -B "$REPO/tests/test_select_audit.py"
}

t_verify_gate6() {
  # 五课反馈轮·夹具④gate6 ch1：eum 判例正判/滞治负例/正本真扫（正本只读·-B 禁 pycache）
  # 「正本真扫」子判依赖 Set 仓 gate6 正本；缺卷让席（自检夹具两子判无依赖恒跑）
  [ "$CANON" = "1" ] || [ -n "${GATE6_SCRIPT:-}" ] || { echo "SKIP: gate6 正本不在卷（$CANON_SET/scripts/gates/gate6_statement_census.py）"; return 111; }
  "$PY" -B "$REPO/tests/test_verify_gate6.py"
}

t_recipe_s07() {
  # 五课反馈轮·夹具⑤S07 投影重锚 E5：处方件锚词面＋病面/掩蔽/愈面机检（冻结引擎只读 import）
  "$PY" -B "$REPO/tests/test_recipe_s07.py"
}

t_recipe_pw1() {
  # 五课打磨轮·课件③dver2-enbig7 同域撞：PW1 处方件锚词面＋前兆 DUP-CROSS/
  # 入侵置换 WDIFF 拦截（零落盘）＋私占重建 WORLD-BASE-OK（零编译零写盘）
  "$PY" -B "$REPO/tests/test_recipe_enbig7_pw1.py"
}

t_precedent_station() {
  # 五课打磨轮·课件⑤三判例剧本 toolify：三判例验收站十判自检＋轻链正负判
  # （names 对表/gate4/REVIEW 升格/gate7 形制/刀面记名·零编译零写盘·gate7 实跑不入套件）
  "$PY" -B "$REPO/tests/test_precedent_station.py"
}

t_netname_normalize() {
  # 本轮实战判例工具化①：.v.v 双后缀名净名归一器（tests/test_netname_normalize.py·
  # 九节：干跑默认零落盘/--apply md5 前后验讫（改名不改字节）/COLLIDE 拒覆写/
  # CLI 四码 help0·未知形参2·缺dir2·9——零触真仓）
  "$PY" -B "$REPO/tests/test_netname_normalize.py"
}

t_verify_fresh() {
  # 本轮实战判例工具化②：divmod_gen 陈旧 vo 假绿判例 fresh-compile 防线
  # （tests/test_verify_fresh.py·八节：--require-fresh 9.1 魔数＋新鲜度双判·
  # 任一不过 rc=9 fail-loud——零触真仓零编译）
  "$PY" -B "$REPO/tests/test_verify_fresh.py"
}

t_extract_magic() {
  # 本轮实战判例工具化③：gate7 提取面 Obj.magic 逐件机检闸（坑账第十笔工具化·
  # run97/98 三件涨账 28/4/1 承工单给料）。tests/test_extract_magic.py 十一节：
  # Separate Extraction 解析（inline/driver 双形）→rocq 提取→ocamlc→grep -c
  # Obj.magic→--max 判红绿＋--json 台账·假 rocq/ocamlc 桩全链（零真编译零触真仓·
  # 夹具含本仓自带 names_sample.v 只读）；v15 增盲区补全节（首战 G09 Class/
  # G13 Extraction 双红→声明/命令 vernacular 就地扩补·Class 夹具 census 不误判·
  # 未知 vernacular 仍红 9）
  "$PY" -B "$REPO/tests/test_extract_magic.py"
}

t_fail_probe() {
  echo "（套件自检注入例：恒红）"
  return 1
}

t_scan_v4_token() {
  # W15 工具化①：token 级普查（混合行遮蔽夹具三站＋旧法盲区实证＋binder 零误报；
  # 真树抽查 ROCWASH_TREE_SAMPLES 环境门控·零硬编码路径·缺省夹具级恒跑）
  "$PY" -B "$REPO/tests/test_scan_v4_token.py"
}

t_cure_pack() {
  # W15 工具化②：消费位治愈正典包五式（applier 自检＋pack 完整性＋干跑/apply/
  # 幂等；编译验证 ROCWASH_ROCQ 门控且经 tools/cpu_guard.sh 包裹·缺省跳过）
  "$PY" -B "$REPO/tests/test_cure_pack.py"
}

t_erasure_classifier() {
  # W15 工具化③：擦除位六簇分类器（自检＋合成 interface＋CAPTURE 交叉对拍；
  # 真件回放 ROCWASH_ERASURE_MLI/SCAN 门控·缺省跳过）
  "$PY" -B "$REPO/tests/test_erasure_classifier.py"
}

t_probe_engine() {
  # v30 工具化①：批量闭包相容探针引擎（承 W13 probe_batch.py·tests/
  # test_probe_engine.py 九节：stub 全链 rc 三分/NO-SRC/TIMEOUT/resume 幂等/
  # guard 包裹 rc 真取/RED 缺列/CLI 四码·真 rocq 全链 ROCWASH_ROCQ 门控缺省 SKIP·
  # 零触真仓零网络）
  "$PY" -B "$REPO/tests/test_probe_engine.py"
}

t_chain_graph() {
  # v30 工具化②：多账合并链根图（承 W25 w25_merge_ledgers.py·合成双账七节：
  # 双形通吃/后批覆盖/链根自身可洗性三分/missing 双源/TOP 榜＋确定性/CLI 四码·
  # 零触真仓零网络）
  "$PY" -B "$REPO/tests/test_chain_graph.py"
}

t_ledger_sync() {
  # v30 工具化③：probe×状态台账合并同步（E1 去重/E3 幽灵/MD5-DRIFT/NO-MD5/
  # 升格策略/列校验 fail-loud/幂等字节恒同/CLI 四码·合成夹具八节·零触真仓零网络）
  "$PY" -B "$REPO/tests/test_ledger_sync.py"
}

t_comment_pack() {
  # v31 工具化：注释域 sweep 旁车（comment_pack.json＋comment_sweep.py·
  # 嵌套注释+字符串感知状态机/旗词换形/头注换代/w7 code 行全等/幂等·六节零触真仓）
  "$PY" -B "$REPO/tests/test_comment_pack.py"
}

t_dual_scan() {
  # v32 工具化：双器对拍驱动（scan/dual_scan.py·scan_v4_token＋mac_stmt_scan
  # 双扫×逐件差异报告 only_v4/only_stmt/common·确定字节恒同·CLI 四码·
  # tests/test_dual_scan.py 十节·零触真仓零网络）
  "$PY" -B "$REPO/tests/test_dual_scan.py"
}

# ---------- 汇总执行 ----------

echo "== rocqwash tests/ 自测套件（repo=${REPO}）=="
for c in $CASES; do
  TOTAL=$((TOTAL + 1))
  if "$c" >"$LOG" 2>&1; then
    PASS=$((PASS + 1))
    printf '[%d/%d] %-26s PASS\n' "$TOTAL" "$NCASES" "$c"
  else
    rc=$?
    if [ "$rc" -eq 111 ]; then
      SKIP=$((SKIP + 1)); SKIPS="$SKIPS $c"
      printf '[%d/%d] %-26s SKIP (正本环境缺·rc=111)\n' "$TOTAL" "$NCASES" "$c"
    else
      FAIL=$((FAIL + 1)); REDS="$REDS $c"
      printf '[%d/%d] %-26s FAIL (rc=%s)\n' "$TOTAL" "$NCASES" "$c" "$rc"
      echo "-------- $c 输出（前 40 行）--------"
      sed -n '1,40p' "$LOG"
      echo "------------------------------------"
    fi
  fi
done

echo "== 汇总: $PASS 过 / $FAIL 红 / $SKIP 略 / 共 $TOTAL 例 =="
if [ "$SKIP" -ne 0 ]; then
  echo "略例（正本环境缺·真本机全跑）:$SKIPS"
fi
if [ "$FAIL" -ne 0 ]; then
  echo "红例:$REDS"
  exit 1
fi
exit 0
