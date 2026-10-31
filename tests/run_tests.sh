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
#       watch/watch.py CI 监控＋钉 IP 推送＋confirm（--selftest 零网络向量组）
#       tools/cpu_guard.sh -Direct 冒烟（探针一发即退＋退出码传播）
#
# 用法：
#   bash tests/run_tests.sh
#   ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh   # 套件自检：注入必红例，应 EXIT 1
#
# 退出码口径承 CONTRIBUTING §4：0=全绿；1=任一红。
set -u

REPO=$(cd "$(dirname "$0")/.." && pwd)
FIX="$REPO/tests/fixtures"
PY=python3

PASS=0; FAIL=0; TOTAL=0; REDS=""
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
t_cpu_guard_direct_rc"
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
    FAIL=$((FAIL + 1)); REDS="$REDS $c"
    printf '[%d/%d] %-26s FAIL (rc=%s)\n' "$TOTAL" "$NCASES" "$c" "$rc"
    echo "-------- $c 输出（前 40 行）--------"
    sed -n '1,40p' "$LOG"
    echo "------------------------------------"
  fi
done

echo "== 汇总: $PASS 过 / $FAIL 红 / 共 $TOTAL 例 =="
if [ "$FAIL" -ne 0 ]; then
  echo "红例:$REDS"
  exit 1
fi
exit 0
