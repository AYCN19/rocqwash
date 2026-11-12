<!-- cli/rocqwash.zh.md — cli/rocqwash 原中文帮助面留档（bilingual transition archive · 20261113）-->
<!-- English-first 正版在 cli/rocqwash 本体（头注/usage）；工具名/旗标/退出码语义两版一致 -->

> **English-first version:** the `cli/rocqwash` script itself (header comment + usage heredocs), English-first since
> the 20261113 translation wave. 本文件留档其原中文头注与三份 usage 帮助面原文（双语过渡期互引）。

## 原头注（original header comment）

#!/usr/bin/env bash
# cli/rocqwash — rocqwash 统一 CLI 入口（bash）· Unified CLI entry (bash)
#
# 子命令 Subcommands: scan | names | wash | verify | seam | certify | watch
#
# 路由契约 Routing contract:
#   1. 通用逐件入口（模块目录下唯一一个不带前导下划线的 .py）→ 自动路由，参数与
#      退出码 1:1 透传（fail-loud，不改写）。
#   2. 前导下划线 .py（如 wash/_abl1_wash.py）＝战役/席位专用工装：路径硬编码、
#      不接逐件 argv——统一入口**不代跑**（防误触外部沙箱写），直接 python3 调用。
#   3. 模块无通用入口 → exit 3（NOT-IMPLEMENTED，fail-loud，不模拟任何行为）。
#   4. 多个通用入口 → exit 4（入口不唯一，列清单要求人工指认）。
#
# 退出码 Exit codes:
#   0 = 通过   2 = 断言失败/未知子命令（含 certify/verify 未知子动词）   3 = 无通用逐件入口   4 = 通用入口不唯一（certify/verify 无子动词亦走此口径）
#   9 = 文件缺失   其余 = 各子工具自身口径透传（如 scan --selftest 向量失败 exit 2）

## 原主 usage（original main usage heredoc）

rocqwash — Coq/Rocq Constructive Proof Unblocking Engine（统一 CLI 入口 / unified CLI entry）

用法 Usage: rocqwash <subcommand> [args...]

子命令 Subcommands:
  scan     语句面 Prop 裸形扫描器              -> scan/mac_stmt_scan.py
           (--file/--json/--manifest/--hits-csv/--baseline/--selftest)
  names    顶层语句名有序清单 + N=N 有序全等断言 -> names/mac_stmt_names.py
           (<file>/--compare/--expect/--kinds/--include-let/--json/--names-out)
  wash     规范洗引擎＋世界基钩子（双通用入口·exit 4 请直接指认）
           -> wash/wash_engine.py | wash/world_hook.py
  verify   绿判四件套＋gate6 普查薄包装      -> verify/  显式分派 (verify gate4|verify_vo|verify_gate6|retrofit ...)
  seam     代际缝探针（W13 four-mechanism）           -> seam/seam_probe.py
  certify  两层冻结＋推窗四判据＋UNION v2＋八件冻结名单      -> certify/  显式分派 (certify freeze|push_gate|frozen8 ...)
  watch    CI 监控＋钉 IP 推送＋ls-remote 确证        -> watch/watch.py (ci/push/confirm)
  help     本帮助

路由说明 Routing notes:
  - 模块目录下唯一非 "_" 前缀 .py = 通用逐件入口，自动路由（参数/退出码透传）。
  - certify 三通用件（freeze_manifest＋push_gate＋frozen8）与 verify 四通用件（gate4＋
    verify_vo＋verify_gate6＋retrofit）走显式子动词分派：`rocqwash certify freeze|push_gate|frozen8 [args...]`、
    `rocqwash verify gate4|verify_vo|verify_gate6|retrofit [args...]` 1:1 透传；无子动词＝入口
    不唯一 → exit 4 列清单人工指认；未知子动词 → exit 2。
  - "_" 前缀 .py = 战役/席位专用工装（路径硬编码·无逐件接口），统一入口不代跑；
    需要时直接 `python3 wash/_abl1_wash.py` 等方式调用。
  - 无通用入口 → exit 3；多个通用入口 → exit 4（列清单人工指认）。

退出码 Exit codes: 0=pass  2=assertion-fail/unknown-subcommand  3=no-generic-entry  4=ambiguous-entry  9=file-missing

## 原 certify_usage（original certify sub-help heredoc）

rocqwash certify — 两层冻结＋推窗四判据＋UNION v2＋八件冻结名单机检（显式分派 / explicit dispatch）

用法 Usage: rocqwash certify <sub-verb> [args...]

子动词 Sub-verbs:
  freeze     两层冻结清单机检（tier1 逐件 md5＋tier2 清单 md5）  -> certify/freeze_manifest.py
             (<dir> freeze|check --out/--tier2/--manifest/--json/--selftest)
  push_gate  推窗四判据＋UNION v2 多世界清单                      -> certify/push_gate.py
             (window|union-freeze|union-check ... / --selftest)
  frozen8    在役八组件冻结名单机检（--selftest/--check/--list）   -> certify/frozen8.py
             (check --list certify/frozen8_manifest.json --tier2 certify/frozen8_tier2.md5 / --selftest)

路由说明 Routing notes:
  - 子动词后参数与退出码 1:1 透传（fail-loud，不改写）。
  - 无子动词＝三通用件入口不唯一 → exit 4 列清单人工指认（与 verify/ 同款契约形）。
  - 未知子动词 → exit 2（列合法子动词）。

退出码 Exit codes: 0=pass  2=unknown-sub-verb  4=ambiguous-entry  其余=子工具自身口径透传

## 原 verify_usage（original verify sub-help heredoc）

rocqwash verify — 绿判四件套（green-verdict four-pack·显式分派 / explicit dispatch）

用法 Usage: rocqwash verify <sub-verb> [args...]

子动词 Sub-verbs:
  gate4      头注五字段机检守卫 v2.1（注释卫生三域扫描）        -> verify/gate4_comment_guard.py
             (--file/--tree/--tree-recursive/--baseline/--json/--emit-ledger/--selftest 无·单件/树扫)
  verify_vo  通用逐件绿判四件套（exit/log/魔数/新鲜度）         -> verify/verify_vo.py
             (--v <f.v> --vo <f.vo> [--rc N|--exit-file F] [--log L] [--json out] / --selftest)
  verify_gate6 gate6 census 薄包装＋eum 判例器化               -> verify/verify_gate6.py
             (--tree <dir>/--judge-before/--judge-after/--selftest / 形参 rc 1:1 透传正本)
  retrofit   gate7 英化 retrofit（战役工装·硬编码席位路径）     -> verify/retrofit_gate7_irr.py
             (无 argv 接口——统一入口只 1:1 透传，不代跑战役写)

路由说明 Routing notes:
  - 子动词后参数与退出码 1:1 透传（exec 直转·fail-loud，不改写）。
  - 无子动词＝四通用件入口不唯一 → exit 4 列清单人工指认（与 certify/ 同款契约形）。
  - 未知子动词 → exit 2（列合法子动词）。

退出码 Exit codes: 0=pass  1/2=子工具自身口径透传（gate4 违规=1·复核=2）  2=unknown-sub-verb  4=ambiguous-entry  9=file-missing
