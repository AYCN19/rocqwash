#!/usr/bin/env bash
# cw.sh — rocqwash v29-v32 七工具＋20261111 五工具＋v37 三器＋v38 一器＋v39 一器＋v40 一器（共二十）
#         统一入口（repo 根·bash 3.2 兼容）
# cw.sh — unified entry for the rocqwash v29-v32 seven-tool wave plus the
#         20261111 five-tool wave plus the v37 three-tool wave plus the v38
#         aggregate doctor, the v39 doc-lint plus netname-normalize/select-audit routing fixes plus the v40
#         baseline-diff and the v45 render-events ledger renderer, twenty-one tools in total
#         (repo root, bash 3.2)
#
# 用法 Usage: bash cw.sh <tool> [args...]
#
# 工具表 Tools（每工具一行用法提示 + 目标脚本；参数与退出码 1:1 透传）:
#   scan4       token 级限定名普查                  -> scan/scan_v4_token.py
#               cw.sh scan4 --file <f.v> [--json out.json] [--ids S] [--text]
#   cure        消费位治愈正典包（缺省干跑）         -> wash/cure_applier.py
#               cw.sh cure --file <f.v> [--pack P] [--only IDS] [--json out] [--apply]
#   probe       批量闭包相容探针引擎                 -> wash/probe_engine.py
#               cw.sh probe --candidates <tsv> --src DIR --world DIR --out ledger.json [--fresh]
#   chain       多账合并链根图                       -> tools/chain_graph.py
#               cw.sh chain <ledger.json...> [--json out] [--md out] [--top N]
#   sync-ledger probe 台账×状态台账合并同步           -> tools/ledger_sync.py
#               cw.sh sync-ledger --probe <json> --ledger <tsv> --out <tsv> [--report r.json]
#   erasure     擦除位分类顾问                       -> verify/erasure_classifier.py
#               cw.sh erasure --mli <f.mli> [--json scan.json] [--resolve N1,N2] [--md-out f.md]
#   dual-scan   双器对拍驱动                         -> scan/dual_scan.py
#               cw.sh dual-scan --dir DIR | --file <f.v> [--out report.json]
#   doctor      dyld 工具链断链诊断（只诊断＋restore 建议·禁代执行）
#                                                    -> tools/toolchain_dyld_doctor.py
#               cw.sh doctor [--worker PATH] [--donor DIR] [--json out.json] [--smoke --coqc PATH]
#   net-probe   网络窗探针（双探稳窗·单探禁发射）     -> tools/net_probe.py
#               cw.sh net-probe [--endpoints URL,..] [--rounds N] [--interval S] [--stable-window] [--json out]
#   triage      CI 红炉分诊（五族+绿炉判类谱）       -> tools/ci_triage.py
#               cw.sh triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]
#   union       注册册 union 手术（缺省干跑）         -> tools/registry_union.py
#               cw.sh union --base B --main M --branch X --kind order [--out o --apply] | --git REPO --ref-*
#   pushci      修复后推送 CI 一键流水线（发射闸→push→watch→heal→verdict±merge）
#                                                    -> tools/pushci.py
#               cw.sh pushci --repo-path DIR --branch B [--pre-scan-gate4] [--merge] [--max-heal N] [--json out] [--dry-run]
#   sentinel    实时动态哨（三路信号源→JSONL 事件流·once/loop 双模）
#                                                    -> tools/cw_sentinel.py
#               cw.sh sentinel --once | --loop [--interval S] [--watch-repo ORG/REPO [--branch B]...] [--watch-ledgers DIR] [--watch-buildlog FILE] [--state-file F] [--emit F] [--on-red 'CMD'] [--on-red-preset NAME]... [--on-red-arg K=V] [--injector F] [--json out]
#   wash-shape  洗形器·正典形五洗流水（词面/token/头注/行尾/锚·plan 缺省零写盘）
#                                                    -> tools/wash_shape.py
#               cw.sh wash-shape --file A.v [--file B.v...] | --dir TREE [--only KINDS] [--apply] [--header-map M] [--header-map-preset NAME] [--anchor-src DIR] [--json OUT] [--loop --interval S --events F] [--injector SCEN.json]
#   unclog      疏通堵塞闭环引擎（probe 归集→链根挑根→cure 落刀→复核→verdict·缺省干跑）
#                                                    -> tools/unclog.py
#               cw.sh unclog --src DIR --world DIR [--candidates TSV | --chain-ledgers JSON...] [--apply] [--audit] [--probe-parallel K] [--rounds N] [--json out] [--events F] [--loop --interval S] [--injector DIR]
#   cw-doctor   综合体检器·四域聚合（环境/网络/注册/堵账→健康分＋advice·只诊断）
#                                                    -> tools/cw_doctor.py
#               cw.sh cw-doctor [--json out.json] [--registry PATH] [--src DIR --sample N] [--injector DIR]
#   doc-lint    文档←→实现一致性三查器（工具表/计数/旗标·verdict consistent|drift）
#                                                    -> tools/doc_lint.py
#               cw.sh doc-lint [--repo DIR] [--json OUT] [--help-cap N]
#   netname-normalize  .v.v 双后缀名净名归一（映射表＋--apply 改名 md5 验讫）
#                                                    -> tools/netname_normalize.py
#               cw.sh netname-normalize [--dir DIR] [--apply] [--map out.tsv] [--json out]
#   select-audit 批选审计器（批选清单对 order.txt 全表 grep 剔重＋Require 面审计 v6）
#                                                    -> tools/select_audit.py
#               cw.sh select-audit [--order ORDER] [--select 清单] [--grep RX] [--requires F.v] [--json out]
#   baseline-diff 堵账基线对比（两份 unclog --audit 基线→增减三清单＋verdict 四态·argv 序=旧→新）
#                                                    -> tools/baseline_diff.py
#               cw.sh baseline-diff OLD.json NEW.json [--json out.json] [--md out.md]
#   render-events  哨事件 JSONL→markdown 台账（三维分布＋逐事件表·坏行容错）
#                                                    -> tools/render_events.py
#               cw.sh render-events --events F.jsonl [--dir DIR] [--md out.md] [--json out] [--top N]
#   help        本帮助（help <tool> = 该工具一行提示）
#
# 路由契约 Routing contract:
#   1. 路径全部相对仓根（ROOT 取自本脚本所在目录）——零硬编码绝对路径，仓随迁随用。
#   2. 参数与退出码 1:1 透传（exec 直转·fail-loud 不改写）；与 cli/rocqwash 同款契约。
#   3. 退出码：0=通过；2=未知工具；9=目标脚本缺失；其余=各工具自身口径透传
#      （工具自身口径：--help/--selftest=0；argparse 用法错/FAIL-LOUD 断言=2；目标文件缺失=9）。
#      pushci 透传 verdict 封册（success/dry-run=0·heal-exhausted/unstable/toolchain=1·
#      fix-content/gate4-block=2·9=目标缺失）。v37 三器口径同形：0=绿/巡检完成/
#      unclogged；1=数据性未竟（洗未尽 partial/plan-miss·墙 wall/轮尽
#      rounds-exhausted——红是数据非器红·响亮 stdout）；2=用法错；9=缺/fail-loud。
#      cw-doctor 同形：0=healthy（综合分≥90）·1=degraded（红是数据非器红·
#      响亮 stdout）；2=用法错；9=缺/fail-loud。
#      doc-lint 同形：0=consistent（三查零漂）·1=drift（任一条漂·红是数据
#      非器红·响亮 stdout）；2=用法错（--help-cap<1）；9=缺（必需输入缺失/
#      器 --help 红或超时 fail-loud）。
#      baseline-diff 同形：0=improved/stable（红减/持平）·1=degraded/
#      incomparable（红增/候选集异如实拒判·红是数据非器红·响亮 stdout）；
#      2=用法错/输入形坏（schema 不对/账面自洽破）；9=路径缺失。
#   4. bash 3.2 兼容（无关联数组、无 bash4+ 特性）；只读路由层，自身零写盘。
#
# 覆盖面注 Coverage note: cli/rocqwash routes the pre-v29 modules (scan/names/
# wash/verify/seam/certify/watch). The v29-v32 tools and the 20261111 five tools
# (doctor/net-probe/triage/union/pushci in tools/) plus the v37 three tools
# (cw_sentinel/wash_shape/unclog) plus the v38 aggregate doctor (cw_doctor)
# live in module directories that now
# hold several generic entries each, where the auto-router's ambiguity guard
# (exit 4) deliberately declines to guess — this entry fills that gap by
# explicit tool name. The two entries are complementary.

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
cw.sh — rocqwash v29-v32＋20261111 五工具＋v37 三器＋v38 一器＋v39 一器＋v40 一器统一入口（二十工具·bash 3.2 兼容）

用法 Usage: bash cw.sh <tool> [args...]

工具 Tools:
  scan4       token 级限定名普查                  -> scan/scan_v4_token.py
              cw.sh scan4 --file <f.v> [--json out.json] [--ids S] [--text]
  cure        消费位治愈正典包（缺省干跑）         -> wash/cure_applier.py
              cw.sh cure --file <f.v> [--pack P] [--only IDS] [--json out] [--apply]
  probe       批量闭包相容探针引擎                 -> wash/probe_engine.py
              cw.sh probe --candidates <tsv> --src DIR --world DIR --out ledger.json [--fresh]
  chain       多账合并链根图                       -> tools/chain_graph.py
              cw.sh chain <ledger.json...> [--json out] [--md out] [--top N]
  sync-ledger probe 台账×状态台账合并同步           -> tools/ledger_sync.py
              cw.sh sync-ledger --probe <json> --ledger <tsv> --out <tsv> [--report r.json]
  erasure     擦除位分类顾问                       -> verify/erasure_classifier.py
              cw.sh erasure --mli <f.mli> [--json scan.json] [--resolve N1,N2] [--md-out f.md]
  dual-scan   双器对拍驱动                         -> scan/dual_scan.py
              cw.sh dual-scan --dir DIR | --file <f.v> [--out report.json]
  doctor      dyld 工具链断链诊断（只诊断＋restore 建议·禁代执行）
                                                   -> tools/toolchain_dyld_doctor.py
              cw.sh doctor [--worker PATH] [--donor DIR] [--json out.json] [--smoke --coqc PATH]
  net-probe   网络窗探针（双探稳窗·单探禁发射）     -> tools/net_probe.py
              cw.sh net-probe [--endpoints URL,..] [--rounds N] [--interval S] [--stable-window] [--json out]
  triage      CI 红炉分诊（五族+绿炉判类谱）       -> tools/ci_triage.py
              cw.sh triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]
  union       注册册 union 手术（缺省干跑）         -> tools/registry_union.py
              cw.sh union --base B --main M --branch X --kind order [--out o --apply] | --git REPO --ref-*
  pushci      修复后推送 CI 一键流水线（发射闸→push→watch→heal→verdict±merge）
                                                   -> tools/pushci.py
              cw.sh pushci --repo-path DIR --branch B [--pre-scan-gate4] [--merge] [--max-heal N] [--json out] [--dry-run]
  sentinel    实时动态哨（三路信号源→JSONL 事件流·once/loop 双模）
                                                   -> tools/cw_sentinel.py
              cw.sh sentinel --once | --loop [--interval S] [--watch-repo ORG/REPO [--branch B]...] [--watch-ledgers DIR] [--watch-buildlog FILE] [--state-file F] [--emit F] [--on-red 'CMD'] [--on-red-preset NAME]... [--on-red-arg K=V] [--injector F] [--json out]
  wash-shape  洗形器·正典形五洗流水（词面/token/头注/行尾/锚·plan 缺省零写盘）
                                                   -> tools/wash_shape.py
              cw.sh wash-shape --file A.v [--file B.v...] | --dir TREE [--only KINDS] [--apply] [--header-map M] [--header-map-preset NAME] [--anchor-src DIR] [--json OUT] [--loop --interval S --events F] [--injector SCEN.json]
  unclog      疏通堵塞闭环引擎（probe 归集→链根挑根→cure 落刀→复核→verdict·缺省干跑）
                                                   -> tools/unclog.py
              cw.sh unclog --src DIR --world DIR [--candidates TSV | --chain-ledgers JSON...] [--apply] [--audit] [--probe-parallel K] [--rounds N] [--json out] [--events F] [--loop --interval S] [--injector DIR]
  cw-doctor   综合体检器·四域聚合（环境/网络/注册/堵账→健康分＋advice·只诊断）
                                                   -> tools/cw_doctor.py
              cw.sh cw-doctor [--json out.json] [--registry PATH] [--src DIR --sample N] [--injector DIR]
  doc-lint    文档←→实现一致性三查器（工具表/计数/旗标·verdict consistent|drift）
                                                   -> tools/doc_lint.py
              cw.sh doc-lint [--repo DIR] [--json OUT] [--help-cap N]
  netname-normalize  .v.v 双后缀名净名归一（映射表＋--apply 改名 md5 验讫）
                                                   -> tools/netname_normalize.py
              cw.sh netname-normalize [--dir DIR] [--apply] [--map out.tsv] [--json out]
  select-audit 批选审计器（批选清单对 order.txt 全表 grep 剔重＋Require 面审计 v6）
                                                   -> tools/select_audit.py
              cw.sh select-audit [--order ORDER] [--select 清单] [--grep RX] [--requires F.v] [--json out]
  baseline-diff 堵账基线对比（两份 unclog --audit 基线→增减三清单＋verdict 四态·argv 序=旧→新）
                                                   -> tools/baseline_diff.py
              cw.sh baseline-diff OLD.json NEW.json [--json out.json] [--md out.md]
  render-events  哨事件 JSONL→markdown 台账（三维分布＋逐事件表·坏行容错）
                                                   -> tools/render_events.py
              cw.sh render-events --events F.jsonl [--dir DIR] [--md out.md] [--json out] [--top N]
  help        本帮助（help <tool> = 该工具一行提示）

退出码 Exit codes: 0=pass  2=unknown-tool  9=target-script-missing  其余=各工具自身口径透传
路由说明 Routing notes:
  - 参数与退出码 1:1 透传（exec 直转·fail-loud 不改写）；与 cli/rocqwash 同款契约。
  - 路径全部相对仓根（ROOT 取自本脚本所在目录）——仓随迁随用，零硬编码绝对路径。
  - `cw.sh <tool>`（无参）先打该工具一行提示再透传；`cw.sh help <tool>` 只看提示不执行。
EOF
}

# 一行用法提示（help <tool> 与无参透传前置提示共用同一份措辞）
hint_for() {  # $1=tool
  case "$1" in
    scan4)       echo "cw.sh scan4 --file <f.v> [--json out.json] [--ids S] [--text]   # token 级限定名普查 -> scan/scan_v4_token.py" ;;
    cure)        echo "cw.sh cure --file <f.v> [--pack P] [--only IDS] [--json out] [--apply]   # 消费位治愈正典包（缺省干跑）-> wash/cure_applier.py" ;;
    probe)       echo "cw.sh probe --candidates <tsv> --src DIR --world DIR --out ledger.json [--fresh]   # 批量闭包相容探针 -> wash/probe_engine.py" ;;
    chain)       echo "cw.sh chain <ledger.json...> [--json out] [--md out] [--top N]   # 多账合并链根图 -> tools/chain_graph.py" ;;
    sync-ledger) echo "cw.sh sync-ledger --probe <json> --ledger <tsv> --out <tsv> [--report r.json]   # probe 台账×状态台账合并 -> tools/ledger_sync.py" ;;
    erasure)     echo "cw.sh erasure --mli <f.mli> [--json scan.json] [--resolve N1,N2] [--md-out f.md]   # 擦除位分类顾问 -> verify/erasure_classifier.py" ;;
    dual-scan)   echo "cw.sh dual-scan --dir DIR | --file <f.v> [--out report.json]   # 双器对拍 -> scan/dual_scan.py" ;;
    doctor)      echo "cw.sh doctor [--worker PATH] [--donor DIR] [--json out.json] [--smoke --coqc PATH]   # dyld 工具链断链诊断（只诊断＋restore 建议·禁代执行）-> tools/toolchain_dyld_doctor.py" ;;
    net-probe)   echo "cw.sh net-probe [--endpoints URL,..] [--rounds N] [--interval S] [--stable-window] [--json out]   # 网络窗探针（双探稳窗）-> tools/net_probe.py" ;;
    triage)      echo "cw.sh triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]   # CI 红炉分诊（五族+绿炉）-> tools/ci_triage.py" ;;
    union)       echo "cw.sh union --base B --main M --branch X --kind order [--out o --apply] | --git REPO --ref-base RB --ref-main RM --ref-branch XB   # 注册册 union 手术（缺省干跑）-> tools/registry_union.py" ;;
    pushci)      echo "cw.sh pushci --repo-path DIR --branch B [--pre-scan-gate4] [--merge] [--max-heal N] [--json out] [--dry-run]   # 修复后推送 CI 一键流水线（发射闸→push→watch→heal→verdict±merge·七态 success/fix-content/toolchain/unstable/heal-exhausted/gate4-block/dry-run）-> tools/pushci.py" ;;
    sentinel)    echo "cw.sh sentinel --once | --loop [--interval S] [--watch-repo ORG/REPO [--branch B]...] [--watch-ledgers DIR] [--watch-buildlog FILE] [--state-file F] [--emit F] [--on-red 'CMD'] [--on-red-preset NAME]... [--on-red-arg K=V] [--injector F] [--json out]   # 实时动态哨（三路信号源 CI runs/台账链根/buildlog 词面→JSONL 事件流·红是数据非器红·零动作是缺省·--on-red-preset 五预设 unclog/pushci/wash-shape/triage/cw-doctor 可重复链式按序一败续行·与 --on-red 互斥·旁路动作必伴 --emit 双路同守卫）-> tools/cw_sentinel.py" ;;
    wash-shape)  echo "cw.sh wash-shape --file A.v [--file B.v...] | --dir TREE [--only KINDS] [--apply] [--header-map M] [--header-map-preset NAME] [--anchor-src DIR] [--json OUT] [--loop --interval S --events F] [--injector SCEN.json]   # 洗形器·正典形五洗流水（词面/token/头注/行尾/锚·plan 缺省零写盘·--apply 落刀后复跑五洗复核·--header-map-preset 钦名头注模板库 tests/fixtures/header_map_v1.json 与 --header-map 同槽互斥）-> tools/wash_shape.py" ;;
    unclog)      echo "cw.sh unclog --src DIR --world DIR [--candidates TSV | --chain-ledgers JSON...] [--apply] [--audit] [--probe-parallel K] [--rounds N] [--top N] [--pack FILE] [--json out] [--events F] [--loop --interval S --loop-max N] [--injector DIR]   # 疏通堵塞闭环引擎（probe 归集→chain_graph 挑根→cure_applier 落刀→rescan/resprobe 复核→verdict unclogged/wall/rounds-exhausted/audit·缺省干跑·frozen 在册红拒·--audit 只读堵账基线零写盘自证与 --apply/--loop 互斥·--probe-parallel K 探针并行度透传 timing 段 jobs 维度入账）-> tools/unclog.py" ;;
    cw-doctor)   echo "cw.sh cw-doctor [--json out.json] [--workdir DIR] [--registry PATH] [--src DIR --sample N [--world DIR]] [--worker PATH] [--donor DIR] [--endpoints URL,..] [--guard PATH] [--timeout S] [--injector DIR]   # 综合体检器·四域聚合（环境 dyld/网络 net_probe/注册册锚审计/堵账 probe＋chain_graph→综合健康分 0-100＋verdict healthy/degraded＋advice·只诊断禁代执行·--injector 离线可测）-> tools/cw_doctor.py" ;;
    doc-lint)    echo "cw.sh doc-lint [--repo DIR] [--json OUT] [--help-cap N]   # 文档←→实现一致性三查器（①cw.sh 四处工具表互检＋tools/ 通用入口对账 ②CASES vs tests/README.md vs README.md 计数 ③doc 引用旗标 vs 各器 --help 实出·verdict consistent|drift·红是数据非器红）-> tools/doc_lint.py" ;;
    netname-normalize) echo "cw.sh netname-normalize [--dir DIR] [--apply] [--map out.tsv] [--json out]   # .v.v 双后缀名净名归一器（映射表＋--apply 改名 md5 验讫）-> tools/netname_normalize.py" ;;
    select-audit) echo "cw.sh select-audit [--order ORDER] [--select 清单] [--grep RX] [--requires F.v] [--json out]   # 批选审计器（批选清单对树 order.txt 全表 grep 剔重＋Require 面审计 v6 判据）-> tools/select_audit.py" ;;
    render-events) echo "cw.sh render-events --events F.jsonl [--dir DIR] [--md out.md] [--json out] [--top N]   # 哨事件 JSONL→markdown 台账（kind/family/action 三维分布＋逐事件表·坏行容错 rc1·红是数据非器红）-> tools/render_events.py" ;;
    baseline-diff) echo "cw.sh baseline-diff OLD.json NEW.json [--json out.json] [--md out.md]   # 堵账基线对比器（两份 unclog --audit 堵账基线 argv 序=旧→新→new_blocks/resolved_blocks/persistent 三清单＋score_delta·verdict improved/degraded/stable/incomparable·账面自洽预检拒手编·timing 不入对比·红是数据非器红）-> tools/baseline_diff.py" ;;
    *) return 1 ;;
  esac
}

# 透传执行（tool→脚本相对仓根路径映射；缺脚本 exit 9；无参先打一行提示再透传）
run_tool() {  # $1=tool  $2=target-script (relative to ROOT)  rest=args passthrough
  local tool="$1" rel="$2"
  shift 2
  local script="$ROOT/$rel"
  if [ ! -f "$script" ]; then
    echo "cw.sh $tool: missing $rel" >&2
    exit 9
  fi
  if [ "$#" -eq 0 ]; then
    hint_for "$tool" >&2
  fi
  exec python3 "$script" "$@"
}

case "${1:-}" in
  scan4)       shift; run_tool scan4       "scan/scan_v4_token.py"        "$@" ;;
  cure)        shift; run_tool cure        "wash/cure_applier.py"         "$@" ;;
  probe)       shift; run_tool probe       "wash/probe_engine.py"         "$@" ;;
  chain)       shift; run_tool chain       "tools/chain_graph.py"         "$@" ;;
  sync-ledger) shift; run_tool sync-ledger "tools/ledger_sync.py"         "$@" ;;
  erasure)     shift; run_tool erasure     "verify/erasure_classifier.py" "$@" ;;
  dual-scan)   shift; run_tool dual-scan   "scan/dual_scan.py"            "$@" ;;
  doctor)      shift; run_tool doctor      "tools/toolchain_dyld_doctor.py" "$@" ;;
  net-probe)   shift; run_tool net-probe   "tools/net_probe.py"           "$@" ;;
  triage)      shift; run_tool triage      "tools/ci_triage.py"           "$@" ;;
  union)       shift; run_tool union       "tools/registry_union.py"      "$@" ;;
  pushci)      shift; run_tool pushci      "tools/pushci.py"              "$@" ;;
  sentinel)    shift; run_tool sentinel    "tools/cw_sentinel.py"         "$@" ;;
  wash-shape)  shift; run_tool wash-shape  "tools/wash_shape.py"          "$@" ;;
  unclog)      shift; run_tool unclog      "tools/unclog.py"              "$@" ;;
  cw-doctor)   shift; run_tool cw-doctor   "tools/cw_doctor.py"           "$@" ;;
  doc-lint)    shift; run_tool doc-lint    "tools/doc_lint.py"            "$@" ;;
  netname-normalize) shift; run_tool netname-normalize "tools/netname_normalize.py" "$@" ;;
  select-audit) shift; run_tool select-audit "tools/select_audit.py"        "$@" ;;
  render-events) shift; run_tool render-events "tools/render_events.py"     "$@" ;;
  baseline-diff) shift; run_tool baseline-diff "tools/baseline_diff.py"     "$@" ;;
  help|-h|--help)
    if [ "$#" -ge 2 ]; then
      if hint_for "$2"; then
        exit 0
      else
        echo "cw.sh help: 未知工具 unknown tool: $2（合法 legal: scan4|cure|probe|chain|sync-ledger|erasure|dual-scan|doctor|net-probe|triage|union|pushci|sentinel|wash-shape|unclog|cw-doctor|doc-lint|netname-normalize|select-audit|baseline-diff|render-events）" >&2
        exit 2
      fi
    fi
    usage
    exit 0 ;;
  "") usage; exit 0 ;;
  *)
    echo "cw.sh: 未知工具 unknown tool: $1（合法 legal: scan4|cure|probe|chain|sync-ledger|erasure|dual-scan|doctor|net-probe|triage|union|pushci|sentinel|wash-shape|unclog|cw-doctor|doc-lint|netname-normalize|select-audit|baseline-diff|render-events|help）" >&2
    usage >&2
    exit 2 ;;
esac
