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
t_precedent_station"
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

t_fail_probe() {
  echo "（套件自检注入例：恒红）"
  return 1
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
