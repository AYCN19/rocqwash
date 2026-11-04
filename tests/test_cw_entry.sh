#!/bin/bash
# test_cw_entry.sh — cw.sh 统一入口自测（tests/·v33 工具化·20261104）
#
# cw.sh = v29-v32 工具波统一入口（repo 根·bash 3.2 兼容·相对仓根路由）。
# 本例四节判：
#   1 帮助与路由冒烟   help 全工具表／无参 usage／help <tool> 一行提示／
#                      help 未知工具 2／未知工具 2／七工具 --help 透传冒烟
#                      （断言输出含各目标脚本 basename 标记）
#   2 功能透传         scan4 --json 落账／dual-scan --out 落账／chain 合成台账
#                      --json 落账／sync-ledger 合成 probe×状态台账同步
#                      （rc=1 系 ledger_sync 文档口径「同步完成带发现·新台账
#                      仍已落盘」——tools/ledger_sync.py 头注退出码节）／
#                      cure --selftest／erasure --selftest／probe 无参
#                      FAIL-LOUD 透传 rc=2
#   3 零硬编码行为证   cw.sh 拷入空目录后 scan4 路由应 rc=9（目标脚本缺失）——
#                      若入口硬编码绝对路径则该例必 rc=0，故本例是
#                      「路径全部相对仓根」的行为级证明
#   4 bash 3.2 兼容    /bin/bash -n 语法检（macOS 自带 bash 3.2 即 /bin/bash）
#
# 零触律：全部输入临时合成或只读仓内夹具（tests/fixtures/names_sample.v 只读）；
# 输出全落 mktemp 目录，trap 清理；零真编译零网络零触真仓。
# 幂等：重复运行结果恒同。退出码：0=全过；1=任一红。
set -u

REPO=$(cd "$(dirname "$0")/.." && pwd)
CW="$REPO/cw.sh"
FIX="$REPO/tests/fixtures"
PY=python3

TMP=$(mktemp -d /tmp/rocqwash_cw_entry.XXXXXX)
trap 'rm -rf "$TMP"' EXIT INT TERM

PASS=0
FAIL=0

expect_rc() {  # $1=描述 $2=期望rc $3=实测rc
  if [ "$3" -eq "$2" ]; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
    echo "FAIL: $1 — 期望 rc=$2 实测 rc=$3" >&2
  fi
}

expect_grep() {  # $1=描述 $2=期望次数 $3=实测次数
  if [ "$3" -eq "$2" ]; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
    echo "FAIL: $1 — 期望命中 $2 次 实测 $3 次" >&2
  fi
}

expect_file_nonempty() {  # $1=描述 $2=路径
  if [ -s "$2" ]; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
    echo "FAIL: $1 — 文件缺失或空: $2" >&2
  fi
}

# ---------- 节 1：帮助与路由冒烟 ----------

bash "$CW" help >"$TMP/help.out" 2>&1
expect_rc "help rc" 0 $?
expect_grep "help 含七工具目标脚本路径" 7 \
  $(grep -c "scan_v4_token\.py\|cure_applier\.py\|probe_engine\.py\|chain_graph\.py\|ledger_sync\.py\|erasure_classifier\.py\|dual_scan\.py" "$TMP/help.out")

bash "$CW" >"$TMP/noargs.out" 2>&1
expect_rc "无参 usage rc" 0 $?
expect_grep "无参输出含 Usage" 1 $(grep -c "Usage" "$TMP/noargs.out")

bash "$CW" help scan4 >"$TMP/hs4.out" 2>&1
expect_rc "help scan4 rc" 0 $?
expect_grep "help scan4 一行提示含目标脚本" 1 $(grep -c "scan_v4_token\.py" "$TMP/hs4.out")

bash "$CW" help bogus >/dev/null 2>&1
expect_rc "help 未知工具 rc=2" 2 $?

bash "$CW" bogus >/dev/null 2>"$TMP/unk.err"
expect_rc "未知工具 rc=2" 2 $?
expect_grep "未知工具 stderr 含 unknown tool" 1 $(grep -c "unknown tool" "$TMP/unk.err")

# 七工具 --help 透传冒烟（断言 argparse usage 行含目标脚本 basename 标记）
for pair in \
  "scan4 scan_v4_token.py" \
  "cure cure_applier.py" \
  "probe probe_engine" \
  "chain chain_graph" \
  "sync-ledger ledger_sync" \
  "erasure erasure_classifier.py" \
  "dual-scan dual_scan.py"
do
  set -- $pair
  tool="$1"; marker="$2"
  bash "$CW" "$tool" --help >"$TMP/th.out" 2>&1
  expect_rc "$tool --help 透传 rc" 0 $?
  expect_grep "$tool --help 输出含 $marker 标记" 1 \
    $(grep -c "$marker" "$TMP/th.out")
done

# ---------- 节 2：功能透传 ----------

bash "$CW" scan4 --file "$FIX/names_sample.v" --json "$TMP/s4.json" >/dev/null 2>&1
expect_rc "scan4 --file fixture --json rc" 0 $?
expect_file_nonempty "scan4 census JSON 落账" "$TMP/s4.json"
expect_grep "scan4 JSON 含 md5 指纹" 1 $(grep -c '"md5"' "$TMP/s4.json")

bash "$CW" dual-scan --file "$FIX/names_sample.v" --out "$TMP/ds.json" >/dev/null 2>&1
expect_rc "dual-scan --file --out rc" 0 $?
expect_file_nonempty "dual-scan 报告 JSON 落账" "$TMP/ds.json"
expect_grep "dual-scan JSON 含 diff 域" 1 $(grep -c '"diff"' "$TMP/ds.json")

# chain：合成单件 probe 台账（rocqwash-probe-ledger/1 records 壳·missing 字段直用）
printf '{"records": {"A1.v": {"file": "A1.v", "rc": 1, "red": "Unable to locate library FooBar", "missing": "FooBar"}}}' >"$TMP/p.json"
bash "$CW" chain "$TMP/p.json" --json "$TMP/cg.json" >/dev/null 2>&1
expect_rc "chain 合成台账 rc" 0 $?
expect_file_nonempty "chain 链根图 JSON 落账" "$TMP/cg.json"
expect_grep "chain JSON 含 schema 域" 1 $(grep -c '"schema"' "$TMP/cg.json")

# sync-ledger：合成 probe×状态台账（必需列 件名/md5/RED/状态/备注）。
# 期望 rc=1＝ledger_sync 文档口径「同步完成带发现（NO-MD5 等）·新台账仍已落盘」。
printf '件名\tmd5\tRED\t状态\t备注\nA1.v\tdeadbeef\t1\t待洗\t-\n' >"$TMP/l.tsv"
bash "$CW" sync-ledger --probe "$TMP/p.json" --ledger "$TMP/l.tsv" \
  --out "$TMP/o.tsv" --report "$TMP/r.json" >/dev/null 2>&1
expect_rc "sync-ledger 合成同步 rc=1（完成带发现）" 1 $?
expect_file_nonempty "sync-ledger 新台账落盘" "$TMP/o.tsv"
expect_file_nonempty "sync-ledger 报告 JSON 落盘" "$TMP/r.json"

bash "$CW" cure --selftest >/dev/null 2>&1
expect_rc "cure --selftest 透传 rc" 0 $?

bash "$CW" erasure --selftest >/dev/null 2>&1
expect_rc "erasure --selftest 透传 rc" 0 $?

bash "$CW" probe >"$TMP/pn.out" 2>"$TMP/pn.err"
expect_rc "probe 无参 FAIL-LOUD 透传 rc=2" 2 $?
# 命中 2 次＝cw.sh 无参一行提示＋probe_engine FAIL-LOUD「--candidates 必给」各一次
expect_grep "probe 无参 stderr 含 --candidates（提示＋FAIL-LOUD 双源）" 2 \
  $(grep -c -- "--candidates" "$TMP/pn.err")

# ---------- 节 3：零硬编码行为证 ----------

mkdir -p "$TMP/lonely"
cp "$CW" "$TMP/lonely/cw.sh"
bash "$TMP/lonely/cw.sh" scan4 --help >/dev/null 2>"$TMP/lonely.err"
expect_rc "空目录副本路由 scan4 应 rc=9（目标脚本缺失＝相对路径行为证）" 9 $?
expect_grep "rc=9 stderr 指名缺失相对路径" 1 \
  $(grep -c "missing scan/scan_v4_token.py" "$TMP/lonely.err")

# ---------- 节 4：bash 3.2 兼容 ----------

/bin/bash -n "$CW" 2>/dev/null
expect_rc "/bin/bash -n 语法检（3.2 兼容）" 0 $?

# ---------- 汇总 ----------

echo "== test_cw_entry: $PASS 过 / $FAIL 红 =="
if [ "$FAIL" -ne 0 ]; then
  exit 1
fi
exit 0
