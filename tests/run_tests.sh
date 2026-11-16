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
#         cure_examples.v 编译 rc=0（ROCWASH_ROCQ 门控·cpu_guard 包裹·v47 ⑧A 案
#         总开关缺省探测自动跑）＋不透明 reflexivity 负证 rc!=0）
#       verify/erasure_classifier.py 擦除位分类器六簇（tests/test_erasure_classifier.py·
#         十三判·W15 工具化③：六簇判定/coq_ 前缀/多行 inner-component/premise 位/
#         CAPTURE 交叉对拍/resolve 状态；真件回放经 ROCWASH_ERASURE_MLI/SCAN 门控）
#       wash/probe_engine.py 批量闭包相容探针引擎（tests/test_probe_engine.py·九节·
#         v30 工具化①·承 W13 probe_batch.py：stub 全链 rc 三分 WASHABLE/BORN-CLEAN/
#         RED-MISSING_LIB·NO-SRC/TIMEOUT 124·resume 幂等同账字节恒同·guard 包裹
#         rc 真取·RED 缺列 RC0·CLI 四码·真 rocq 全链 ROCWASH_ROCQ 门控·套件缺省
#         探测自动跑（v47 ⑧A 案）·env 缺且 9.3 缺卷仍 SKIP）
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
#       cw.sh v29-v32 工具波统一入口（tests/test_cw_entry.sh·v33 工具化·
#         四节：帮助/路由冒烟＋七工具 --help 透传＋功能透传（scan4/dual-scan/
#         chain/sync-ledger 合成台账/cure/erasure selftest/probe 无参 FAIL-LOUD）
#         ＋零硬编码行为证（空目录副本 rc=9）＋/bin/bash 3.2 语法检·
#         夹具只读输出全落 mktemp·零触真仓）
#       tools/toolchain_dyld_doctor.py dyld 工具链断链诊断器（tests/
#         test_toolchain_dyld_doctor.py·最小自测壳两判：--selftest 冻结标记
#         DYLD-DOCTOR-SELFTEST PASS＋--help 冒烟·零真 otool 零编译零网络零写盘）
#       tools/ci_triage.py CI 红炉分诊器（tests/test_ci_triage.py·最小自测壳
#         两判：--selftest 冻结标记 CI-TRIAGE-SELFTEST PASS＋--help 冒烟·
#         零网络零写盘；selftest〔十〕gate2-only E 变体矢直挂
#         tests/fixtures/ci_triage_gate2_only_{cancelled,failure}.json
#         真形两件（v50 20261112 工装席入谱·retro 台账 run#7/#10 誊录·
#         fixtures 九件套＝六件套＋Main 形＋gate2-only 两件；v51 20261112
#         集成席登记：复核台账 token 二分限形——#10 认证态形转正 UNREC·
#         banner-absent 形保持 E·两 fixture 增 canned job_logs 真执行行
#         誊录＋dump 行滤除矢＋五 token 在册矢）
#       tools/net_probe.py 网络窗探针（tests/test_net_probe.py·最小自测壳两判：
#         --selftest 冻结标记 NET-PROBE-SELFTEST PASS＋--help 冒烟·零网络零写盘）
#       tools/registry_union.py 注册册 union 手术器（tests/test_registry_union.py·
#         九节：selftest/coq 夹具组/陷阱组同名不同形/重锚 md5 冻结向量/干跑-
#         apply-幂等/json 确定性/CLI 四码＋git 三 ref 直读·零触真仓零网络零编译）
#       tools/pushci.py 推送 CI 一键流水线编排器（tests/test_pushci.py·
#         六场景壳十节：selftest 冻结矢量/tmp 仓 helper/S1 绿径/S2 NETRED 愈合/
#         S3 内容红零 rerun/S4 heal 耗尽/S5 merge/S6 dry-run/幂等字节恒同/
#         CLI 五码·全离线全注入零真网络零真 push 零编译·v41 波器面零新矢量
#         ——本波 pushci 相关新产出＝双门归一评估 docs/push-gate-dual-door-
#         assessment-v1.0-20261111.md 只评估零代码变更）
#       tools/cw_sentinel.py 实时动态哨（tests/test_cw_sentinel.py·最小自测壳
#         两判：--selftest 冻结标记 CW-SENTINEL-SELFTEST PASS＋--help 冒烟·
#         哨自身 --selftest 十五矢量 canned 注入零真网络零编译·v41 波⑨on-red
#         双路同守卫/⑬预设表扩展五预设链式·v51 波⑭韧性层传输层瞬断有界重试
#         （--net-retries 退避 5s/15s/45s）＋loop 逐源 skip 宁跳轮不崩驻/
#         ⑮监督壳部署形冒烟 examples/sentinel_supervisor.sh bash -n＋关键行
#         静态断言零执行零网络）
#       tools/wash_shape.py 洗形器·正典形五洗流水（tests/test_wash_shape.py·
#         最小自测壳三判：--selftest 冻结标记 WASH-SHAPE-SELFTEST PASS
#         十六判向量（plan/apply/幂等/锚/冻结红拒/CLI/--loop/确定性＋preset
#         链：模板库装载·preset/--header-map 胜 env·占位渲染→apply 端到端·
#         同槽互斥 rc2·无源 plan-miss）＋--help 冒烟＋退出码口径抽验 2/2/9·
#         零编译零网络·v39 轮洗形席扩容）
#       tools/unclog.py 疏通堵塞闭环引擎（tests/test_unclog.py·最小自测壳
#         三判：--selftest 冻结标记 UNCLOG-SELFTEST PASS（十四矢量全 --injector
#         canned 罐装零真编译·v41 波⑬--jobs 维度）＋--help 冒烟＋退出码口径
#         抽验 2/2/9·零网络零触真仓）
#       tools/cw_doctor.py 综合体检器·四域聚合（tests/test_cw_doctor.py·最小
#         自测壳两判：--selftest 冻结标记 CW-DOCTOR-SELFTEST PASS（九节向量全
#         --injector canned 罐装 tmp fixture·零真 otool 零真网络零真编译）＋
#         --help 冒烟·20261111 v38 集成席挂接）
#       tests/test_relay_e2e.py 接驳实战核 e2e（v39 工装席铸件·集成席挂接·
#         cw_sentinel --on-red-preset unclog 全链三判：①哨 --once＋injector
#         canned CI 红炉→ci-red 事件→preset 代跑 unclog rc=9 如实入账·哨退
#         出码仍 0 ②unclog --audit 干跑 rc=0·--src 全文件 md5 清单跑前跑后
#         自证零写盘 ③JSONL 同盘 unclog report 路径与实落文件逐字节对拍·
#         全 canned 罐装零真网络零真编译）
#       tools/doc_lint.py 文档←→实现一致性三查器（tests/test_doc_lint.py·
#         最小自测壳三判：--selftest 冻结标记 DOC-LINT-SELFTEST PASS（tmp
#         迷你仓六矢量 V1-V6 由铸席 --selftest 自证）＋--help 冒烟＋退出码
#         口径抽验 2/2/9·零网络零写盘·20261111 v39 集成席缺壳自补挂接）
#       tests/test_destructive_matrix.py 破坏面复核矩阵（20261111 v40 破坏面席
#         铸件·集成席挂接·17 行拒写判据一行一拒写：器×写面×护栏锚 file:line
#         ——unclog×4（缺 --apply 零写盘/--audit 零写盘＋互斥/frozen 红拒/
#         非链根件零被动）＋wash_shape×4（plan 零写盘/rescan partial 不谎报
#         shaped/冻结名红拒/同槽互斥）＋pushci×3（dry-run 零副作用/内容红零
#         rerun/heal 帽尽停）＋cw_sentinel×2（缺省 report-only/preset 缺
#         --emit rc=2）＋registry_union×2＋cure_applier×2（干跑零写盘/
#         --apply 才落刀＋幂等断言拒写）·全 tmp fixture＋injector 罐装零真
#         网络零真仓零真编译·矩阵红＝护栏破响亮列破口）
#       tools/baseline_diff.py 堵账基线对比器（tests/test_baseline_diff.py·
#         最小自测壳三判：--selftest 冻结标记 BASELINE-DIFF-SELFTEST PASS
#         （六矢量 improved/degraded＋墙因变/stable＋timing 不入对比＋幂等/
#         incomparable/md 输出/CLI 四码＋形坏拒判由铸席自证）＋--help 冒烟
#         ＋退出码口径抽验 2/2/9·零网络零编译零触真仓·20261111 v40 集成席
#         缺壳自补挂接）
#       tools/red_dispatch.py 红事件路由器（tests/test_red_dispatch.py·
#         最小自测壳三判：--selftest 冻结标记 RED-DISPATCH-SELFTEST PASS
#         （十二矢量路由全族/占位/auto 执行实证/state 防重/cooldown/
#         report-only 零执行/stdin 多事件/fail-loud/rc≠0 不改退出码/fix 清单/
#         确定性/单对象兜底由铸席 --selftest 自证）＋--help 冒烟＋退出码
#         口径抽验 2/2/9·零网络零编译零触真仓·20261112 v46 集成席缺壳自补
#         挂接）
#       tools/registry_audit.py 注册册卫生审计器（tests/test_registry_audit.py·
#         最小自测壳三判：--selftest 冻结标记 REGISTRY-AUDIT-SELFTEST PASS
#         （四账判类全谱/处方保首＋md5 冻结向量/只读实证/确定性/git 直读/
#         CLI 四码由铸席 --selftest 自证）＋--help 冒烟＋退出码口径抽验
#         2/2/9·零网络零编译零触真仓·20261112 v46 集成席缺壳自补挂接）
#       tools/registry_fix.py 注册册处方执行器（tools/registry_fix.py --selftest
#         直挂八矢量：①干跑零写盘＋逐条 md5 账＋skip 清单全谱＋干跑 report 重跑
#         字节恒同②--apply 12 重复块→0＋断言三过＋md5 账对盘③77c2b9a8 锚刷
#         md5 冻结向量＋同输同出④注入炸点回滚⑤自然炸点 A-fix-2 回滚⑥staging
#         炸零写盘⑦CLI 四码⑧落刀确定性——registry_audit --fix-plan 处方逐条
#         落刀·缺省干跑·20261112 v47 集成席直挂）
#       tools/norm_lint.py 注释面规范化检查器·report-only 首形（tests/
#         test_norm_lint.py 最小自测壳三判：--selftest 六矢量 map-load/
#         jargon-hit/fields-missing/substring-exemption/whitelist-exemption/
#         english-clean 由器自证＋--help 冒烟＋退出码口径抽验 2/9（bogus/
#         缺 tree/--selftest 与扫描旗标同用/非 .py/.sh/.md 扩展名=2·
#         缺 jargon-map=9）＋基线账报告出账（norm-lint-baseline json/md 两
#         报告·全仓注释面现状如实）·套件挂接·零网络零编译零触真仓）
#       tools/contrib_intake.py contribution intake inspector (tests/
#         test_contrib_intake.py minimal shell, three checks: --selftest
#         rc=0 with the CONTRIB-INTAKE-SELFTEST PASS frozen marker — the
#         tool's own dual-git-clone four-gate vectors are attested by the
#         tool, the suite shell is self-supplemented — plus --help smoke
#         plus exit-code spot checks bogus=2/no-input=2/missing-face=9/
#         bad-ref=9; tmp fixtures only, zero writes, zero network)
#       tools/registry_regen.py contribution registration-row regenerator
#         (tests/test_registry_regen.py minimal shell, three checks:
#         --selftest rc=0 with the REGISTRY-REGEN-SELFTEST PASS frozen
#         marker — the tool's own tmp-fixture vectors attest topological
#         regeneration, missing-dependency BLOCK, the frozen md5 vector,
#         dry-run zero-write, blast/divergence and rerun-identity — plus
#         --help smoke plus exit-code spot checks bogus=2/no-input=2/
#         apply-without-out=2/negative-seq=2/missing-base=9; tmp fixtures
#         only, zero writes, zero network)
#       tools/symbiosis_bus.py + tools/bus_feeder.py + tools/uplink.py +
#         tools/evolution_dashboard.py + tools/mcp_server.py + tools/exp_port.py
#         + tools/periscope.py shape shells (tests/t_symbiosis_shape.py +
#         t_bus_feeder_shape.py + t_uplink_shape.py +
#         t_evolution_dashboard_shape.py + t_mcp_face.py + t_exp_port.py +
#         t_periscope_shape.py · 20261115 roster hookup, audit finding P0-6:
#         the five new tool faces and the two bus-family shells were cast
#         with a standing "not rostered" note; each shell drives its tool's
#         real argparse face in subprocesses, offline by construction, tmp
#         fixtures only, zero repository writes; t_mcp_face drives one
#         newline-delimited JSON-RPC session over the 25-capability stdio
#         server face; t_evolution_dashboard_shape adds one read-only live
#         check over the standing account paths)
#       engine-body contract suites (tests/t_engines_body.py nine segments
#         60 checks over ai_flavor / jargon_apply / ai_flavor_apply /
#         i18n_pipeline / i18n_translate / i18n_verify + termbase, and
#         tests/t_engines_seeds.py five seed segments 40 checks E1..E5 ·
#         20261115 roster hookup; modules load dynamically from tools/, a
#         not-yet-landed module is one loud SKIP line, never a silent pass;
#         zero network, zero writes outside mkdtemp)
#       negative-vector pins (tests/test_evolve_flag_contract.py four checks
#         pinning the evolve.py user-facing flag contract, and
#         tests/test_watch_repo_form.py three checks pinning the
#         cw_sentinel --watch-repo ORG/REPO form refusal · 20261115 roster
#         hookup; the form check fires before any fetch, zero network,
#         tmpdir fixtures, zero repository writes)
#       repair-guard hookups (E2 repair classes; each guard imports the
#         shared exclusion table tools/repair_scope.py and appends
#         rocqwash-repair ledger rows; tmp fixtures only, dry-run faces in
#         the suite, zero real-repo writes, zero network)
#       roster count drift guard hookup (tools/roster_resync.py, E2 repair
#         class 2, tests/test_roster_resync.py four checks: --selftest
#         rc=0 with the ROSTER-RESYNC-SELFTEST PASS frozen marker (the
#         guard's own vectors attest the real doc_lint consistent flip as
#         the green criterion, the one-way CASES roster discipline, the
#         budget cap, and the shared repair_scope gate), --help rc=0, and
#         exit-code spot checks 2/9; 20261116 roster hookup)
#       auto-merge gate judge hookup (tools/auto_merge.py, X5 gate;
#         tests/test_auto_merge.py five checks: --selftest rc=0 with the
#         AUTO-MERGE-SELFTEST PASS frozen marker (24 vectors: the five
#         calibration samples S-1..S-5 pinned to already-landed /
#         superseded-landed-elsewhere / merge-ok / superseded-
#         landed-elsewhere / hold-red, the unrecognized-family escalation,
#         the merged-anchor-beats-red and containment-beats-conflict
#         ordering pins, the supply/* whitelist both ways, the daily budget cap,
#         dry-run zero-write, the duplicate refusals, the post-merge
#         revert arc four families, byte-identical reports, CLI codes),
#         --help face, exit-code spots 2/9, the five calibration fixtures
#         judged through the real CLI face, and the dry-run zero-write
#         pledge; tmp fixtures only, zero network, zero repository
#         writes; 20261116 roster hookup)
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
PY=${ROCWASH_PY:-python3}
# Force UTF-8 I/O for every case and every child process they spawn: on a
# Windows host the default stdout codepage (charmap on the hosted runner
# image, gbk on a zh-CN host) makes a tool that prints Chinese prose or math
# symbols die with UnicodeEncodeError, which the suite then reads as a red
# case. Pinned here, in the suite's own entry point, so the guarantee holds
# for every caller and not only for the CI job environment.
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# ---------- 正本环境探针（CI 准入）----------
# 四例（t_gate7_wrapper/t_quad8_check/t_gate6_born_wrapper/t_verify_gate6）的
# 在跑判据依赖本机正本：Set 仓 gates 正本脚本＋CW rocq 工具链＋四仓副本群。
# 正本缺卷 → 诸例 exit 2=SKIP；路径可用 ROCWASH_CANON_* 覆写（CI 演练用）。
CANON_SET=${ROCWASH_CANON_SET:-/Users/apple/Desktop/ConstructiveWorld-Set}
CANON_CW=${ROCWASH_CANON_CW:-/Users/apple/Desktop/ConstructiveWorld}
CANON_W1=${ROCWASH_CANON_W1:-/Users/apple/Desktop/S系Prop清除战役工单}
CANON=0
# Clean mode (ROCWASH_CLEAN=1): canonical-environment auto-detection is
# disabled and explicit canonical pointers are not applied; the canonical
# paths resolve to a non-existent sentinel so the canonical-dependent cases
# SKIP by their standing contract (docs/clean-mode-manual-20261114.md).
if [ "${ROCWASH_CLEAN:-0}" = "1" ]; then
  CANON_SET="${TMPDIR:-/tmp}/rocqwash-clean-no-canonical"
  CANON_CW="$CANON_SET"
  CANON_W1="$CANON_SET"
  echo "(clean-mode note) ROCWASH_CLEAN=1: canonical-environment auto-detection disabled; canonical faces report 'requires canonical environment' and canonical-dependent cases SKIP"
else
if [ -f "$CANON_SET/scripts/gates/gate6_statement_census.py" ] \
   && [ -f "$CANON_SET/scripts/gates/gate7_extract_run.py" ] \
   && [ -x "$CANON_CW/Live/toolchain/opam/live/bin/rocq" ]; then
  CANON=1
fi
fi

# ---------- 门控编译弧总开关（v47 波⑧A 案·缺省探测 20261112）----------
# env 已设则尊（外部 clone 显式指认不受扰）；否则探测在卷正典/代役路径即 export
# ——诸闸位判据语义不变（在即跑·缺才 SKIP），只翻缺省面：
#   ROCWASH_ROCQ        t_cure_pack 编译 check 段＋t_probe_engine 真 rocq 节
#                       （探测 9.3 多路器·v43 第三发 27/27 同源实证 更新账.md:3753）
#   GATE7_PROBE_SCRIPT  t_gate7_wrapper（Set 仓 gate7 正本·judge13 缺省解析同路径）
#   GATE6_SCRIPT        t_verify_gate6＋t_gate6_born_wrapper census 段（Set 仓 gate6 正本）
#   BORN_WORLD_ROCQ     t_gate6_born_wrapper born 段（born_world.sh:114 存在性闸·
#                       该测试零编译不触代差语义；CW Live rocq 缺卷→9.3 代役）
GATE93_ROCQ=/Users/apple/Desktop/mac93_install_work/opam93/rocq93/bin/rocq
# Clean mode skips the whole default-pointer block below (auto-detection off;
# ROCWASH_ROCQ/GATE7_PROBE_SCRIPT/GATE6_SCRIPT/BORN_WORLD_ROCQ stay unset so
# the env-gated compile sections SKIP by contract).
if [ "${ROCWASH_CLEAN:-0}" != "1" ]; then
if [ -z "${ROCWASH_ROCQ:-}" ] && [ -x "$GATE93_ROCQ" ]; then
  export ROCWASH_ROCQ="$GATE93_ROCQ"
  echo "（探测注记）ROCWASH_ROCQ 未设→9.3 多路器在卷·缺省指认 ${ROCWASH_ROCQ}（⑧A 案）"
fi
if [ -z "${GATE7_PROBE_SCRIPT:-}" ] && [ -f "$CANON_SET/scripts/gates/gate7_extract_run.py" ]; then
  export GATE7_PROBE_SCRIPT="$CANON_SET/scripts/gates/gate7_extract_run.py"
  echo "（探测注记）GATE7_PROBE_SCRIPT 未设→Set 仓 gate7 正本在卷·缺省指认（t_gate7_wrapper 解锁）"
fi
if [ -z "${GATE6_SCRIPT:-}" ] && [ -f "$CANON_SET/scripts/gates/gate6_statement_census.py" ]; then
  export GATE6_SCRIPT="$CANON_SET/scripts/gates/gate6_statement_census.py"
  echo "（探测注记）GATE6_SCRIPT 未设→Set 仓 gate6 正本在卷·缺省指认（t_verify_gate6/t_gate6_born_wrapper census 段解锁）"
fi
if [ -z "${BORN_WORLD_ROCQ:-}" ]; then
  if [ -x "$CANON_CW/Live/toolchain/opam/live/bin/rocq" ]; then
    export BORN_WORLD_ROCQ="$CANON_CW/Live/toolchain/opam/live/bin/rocq"
  elif [ -x "$GATE93_ROCQ" ]; then
    export BORN_WORLD_ROCQ="$GATE93_ROCQ"
    echo "（探测注记）BORN_WORLD_ROCQ 未设且 CW Live rocq 缺卷→9.3 多路器代役（t_gate6_born_wrapper 解锁·该测试零编译仅存在性闸）"
  fi
fi
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
t_dual_scan \
 t_cw_entry \
 t_registry_union \
 t_toolchain_dyld_doctor \
 t_ci_triage \
 t_net_probe \
 t_pushci \
 t_cw_sentinel \
 t_wash_shape \
 t_unclog \
 t_cw_doctor \
 t_relay_e2e \
 t_doclint \
 t_destructive_matrix \
 t_baseline_diff \
 t_red_dispatch \
 t_registry_audit \
 t_registry_fix \
 t_registry_fix_dedup \
 t_registry_fix_orphan_add \
 t_registry_fix_anchor \
 t_norm_lint \
 t_contrib_intake \
 t_registry_regen \
 t_evolve \
 t_clean_mode \
 t_vacgen_shape \
 t_vacgen_expectedred \
 t_refinery \
 t_symbiosis_shape \
 t_bus_feeder_shape \
 t_uplink_shape \
 t_evolution_dashboard_shape \
 t_mcp_face \
 t_exp_port \
 t_periscope_shape \
 t_engines_body \
 t_engines_seeds \
 t_evolve_flag_contract \
 t_watch_repo_form \
 t_flaky_guard \
 t_roster_resync \
 t_auto_merge \
 t_selfheal_guards"
NCASES=$(echo $CASES | wc -w | tr -d ' ')
if [ "${ROCQWASH_TESTS_FAIL_PROBE:-0}" = "1" ]; then
  CASES="$CASES t_fail_probe"
  NCASES=$((NCASES + 1))
fi

# ---------- advisory roster: flaky quarantine (repair class E2-3) ----------
#   tools/flaky_guard.py --move writes an order-dependent case into
#   tests/advisory_roster.txt (repair-ledger row class/target/outcome;
#   budget <= 2 per class per branch; scope-checked against the shared
#   tools/repair_scope.py exclusion table).  The default suite then drops
#   the case here (main roster shrinks, one loud ADVISORY-OUT line each)
#   and the CI flaky-watch lane keeps running quarantined cases in its
#   own observation step.  ROCWASH_TESTS_ONLY wins over the quarantine (a
#   watch lane can name a quarantined case explicitly); unknown advisory
#   names print one loud note and are ignored (rosters evolve, same
#   contract as EXCLUDE).  Restore is the guard's --restore face with
#   green-round evidence (ledger row outcome=restored).
ADVISORY_ROSTER=${ROCWASH_ADVISORY_ROSTER:-"$REPO/tests/advisory_roster.txt"}
_advisory=""
if [ -f "$ADVISORY_ROSTER" ]; then
  for _n in $(grep -v '^[[:space:]]*#' "$ADVISORY_ROSTER" | tr '\n\r' '  '); do
    [ -z "$_n" ] && continue
    _hit=0
    for _c in $CASES; do
      [ "$_c" = "$_n" ] && _hit=1 && break
    done
    if [ "$_hit" = "1" ]; then
      _advisory="$_advisory $_n"
    else
      echo "ADVISORY-NOTE: advisory-roster name is not in the roster (ignored): $_n"
    fi
  done
fi

# ---------- roster selection: platform-sensitive / flaky separation ----------
#   ROCWASH_TESTS_ONLY     space-separated case names; run ONLY these.
#   ROCWASH_TESTS_EXCLUDE  space-separated case names; run the default roster
#                          minus these (each excluded case prints one loud
#                          SELECTED-OUT line and is not counted).
#   Carried by the CI matrix (ci.yml): ubuntu/windows jobs exclude the
#   platform-sensitive roster for the blocking job and run it alone in the
#   advisory flaky-watch job, so a platform-bound red cannot mask a real
#   regression and cannot fail the run either (failure-rate target <5%).
#   Unknown ONLY names are a loud rc=2 (the caller named a case that does
#   not exist); unknown EXCLUDE names print one loud note and are ignored
#   (rosters evolve). The exit contract (0 all green / 1 any red) is
#   unchanged; selection never turns a red into a pass.
if [ -n "${ROCWASH_TESTS_ONLY:-}" ] || [ -n "${ROCWASH_TESTS_EXCLUDE:-}" ] || [ -n "$_advisory" ]; then
  _sel_all="$CASES"
  if [ -n "${ROCWASH_TESTS_ONLY:-}" ]; then
    for _want in $ROCWASH_TESTS_ONLY; do
      _hit=0
      for _c in $_sel_all; do
        [ "$_c" = "$_want" ] && _hit=1 && break
      done
      if [ "$_hit" != "1" ]; then
        echo "SELECTION-ERROR: ROCWASH_TESTS_ONLY name is not in the roster: $_want"
        exit 2
      fi
    done
  fi
  _selected=""
  for _c in $_sel_all; do
    _drop=0
    if [ -n "${ROCWASH_TESTS_ONLY:-}" ]; then
      _drop=1
      for _want in $ROCWASH_TESTS_ONLY; do
        [ "$_c" = "$_want" ] && _drop=0 && break
      done
    else
      for _ex in ${ROCWASH_TESTS_EXCLUDE:-}; do
        if [ "$_c" = "$_ex" ]; then
          _drop=1
          printf 'SELECTED-OUT %-26s (platform-sensitive roster; advisory watch job covers it)\n' "$_c"
        fi
      done
      for _ax in $_advisory; do
        if [ "$_c" = "$_ax" ]; then
          _drop=1
          printf 'ADVISORY-OUT %-26s (flaky quarantine; the advisory watch lane covers it)\n' "$_c"
        fi
      done
    fi
    [ "$_drop" != "1" ] && _selected="$_selected $_c"
  done
  CASES="$_selected"
  NCASES=$(echo $CASES | wc -w | tr -d ' ')
  if [ -z "$(echo $CASES | tr -d ' ')" ]; then
    echo "SELECTION-ERROR: case selection is empty (ONLY matched nothing usable)"
    exit 2
  fi
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
  # 幂等；编译验证 ROCWASH_ROCQ 门控且经 tools/cpu_guard.sh 包裹·套件缺省探测
  # 自动跑（v47 ⑧A 案·run_tests.sh 总开关）·env 缺且 9.3 缺卷仍 SKIP）
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
  # guard 包裹 rc 真取/RED 缺列/CLI 四码·真 rocq 全链 ROCWASH_ROCQ 门控·套件缺省
  # 探测自动跑（v47 ⑧A 案）·env 缺且 9.3 缺卷仍 SKIP·
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

t_cw_entry() {
  # v33 工具化：cw.sh v29-v32 工具波统一入口（tests/test_cw_entry.sh·四节：
  # 帮助/路由冒烟＋七工具 --help 透传＋功能透传（scan4/dual-scan/chain/
  # sync-ledger 合成台账/cure/erasure selftest/probe 无参 FAIL-LOUD）＋
  # 零硬编码行为证（空目录副本 rc=9）＋/bin/bash 3.2 语法检·
  # 夹具只读输出全落 mktemp·零触真仓零网络）
  bash "$REPO/tests/test_cw_entry.sh"
}

t_registry_union() {
  # 20261110 实战手术工具化：注册册 union 手术器（tools/registry_union.py·
  # tests/test_registry_union.py 九节：selftest 八判/coq 夹具组/陷阱组同名不同形
  # 对 merge-base 必过滤/重锚 md5 冻结向量 1414cddb/A2·A3 负判零写盘/干跑-apply-
  # 幂等/json 确定性/CLI 四码＋用法对偶/git 三 ref 直读·夹具只读输出全落 mktemp·
  # 零触真仓零网络零编译）
  "$PY" -B "$REPO/tests/test_registry_union.py"
}

t_toolchain_dyld_doctor() {
  # 20261111 集成席挂接：dyld 工具链断链诊断器（tools/toolchain_dyld_doctor.py·
  # 铸席 --selftest 全链离线向量组已自证·tests/test_toolchain_dyld_doctor.py
  # 最小自测壳两判：--selftest 冻结标记＋--help 冒烟·零真 otool 零编译零网络）
  "$PY" -B "$REPO/tests/test_toolchain_dyld_doctor.py"
}

t_ci_triage() {
  # 20261111 集成席挂接：CI 红炉分诊器（tools/ci_triage.py·五族+绿炉判类谱·
  # 铸席 --selftest 离线样张已自证·tests/test_ci_triage.py 最小自测壳两判：
  # --selftest 冻结标记＋--help 冒烟·零网络零写盘）
  "$PY" -B "$REPO/tests/test_ci_triage.py"
}

t_net_probe() {
  # 20261111 集成席挂接：网络窗探针（tools/net_probe.py·双探稳窗律·铸席
  # --selftest 零网络向量组已自证·tests/test_net_probe.py 最小自测壳两判：
  # --selftest 冻结标记＋--help 冒烟·零网络零写盘）
  "$PY" -B "$REPO/tests/test_net_probe.py"
}

t_pushci() {
  # 20261111 集成席挂接：推送 CI 一键流水线编排器（tools/pushci.py·五段管线
  # preflight 发射闸→push→watch→heal→verdict±merge·v35 四器 subprocess 编排
  # 零新引擎·tests/test_pushci.py 六场景壳十节：selftest 冻结矢量＋tmp 仓
  # helper＋S1 绿径＋S2 NETRED 愈合＋S3 内容红零 rerun＋S4 heal 耗尽＋S5
  # merge＋S6 dry-run＋六场景幂等字节恒同＋CLI 五码——全离线全注入零真网络
  # 零真 push 零编译零写盘）
  # v41 波登记：pushci 器面零新矢量——本波 pushci 相关新产出＝护栏席
  # push_gate 推窗四判据×pushci preflight 发射闸双门归一评估（docs/
  # push-gate-dual-door-assessment-v1.0-20261111.md·只评估零代码变更·
  # 发射闸三闸 toolchain/net/gate4 与 verdict 七态不变；pushci P1-P3 矩阵
  # 三判照旧在 t_destructive_matrix 在册随套件复跑）
  "$PY" -B "$REPO/tests/test_pushci.py"
}

t_cw_sentinel() {
  # 20261111 v37 挂接：实时动态哨（tools/cw_sentinel.py·三路信号源 CI runs/
  # 本地台账链根/buildlog 词面→JSONL 事件流·once/loop 双模·ci_triage/
  # chain_graph subprocess 编排零新引擎·tests/test_cw_sentinel.py 最小自测壳
  # 两判：--selftest 冻结标记 CW-SENTINEL-SELFTEST PASS＋--help 冒烟·
  # 哨自身 --selftest 十三矢量 canned 注入零真网络零编译（v40 稳态席扩容
  # ⑪--state-file 崩溃恢复/⑫--emit-max-bytes JSONL 轮转·v41 护栏/预设席
  # 扩容⑨on-red 双路同守卫 plain --on-red 缺 --emit rc=2〔破坏面矩阵 S2
  # 转正〕/⑬预设表数据化扩展五预设 wash-shape/triage/cw-doctor＋triage
  # repo/run 事件直替族＋链式双预设全链并集面按序一败续行）·零真网络零编译
  # 零触真仓）
  "$PY" -B "$REPO/tests/test_cw_sentinel.py"
}

t_wash_shape() {
  # 20261111 v37 洗形席挂接·v39 扩容·v40 稳态席再扩：洗形器·正典形五洗流水
  # （tools/wash_shape.py·gate4 词面/scan_v4+cure_applier 正典包/头注模板补写/
  # 行尾归一/registry_union 重锚五洗 subprocess 编排·两段 plan→apply 复跑复核·
  # schema rocqwash-shape/1·tests/test_wash_shape.py 最小自测壳三判：--selftest
  # 冻结标记 WASH-SHAPE-SELFTEST PASS（十八判向量全 tmp 夹具·v39 轮增 preset
  # 链四判：模板库装载在位/preset 胜 env/占位渲染→apply 端到端/同槽互斥 rc2
  # ＋模板库缺失 rc9·v40 轮增判17 --loop 事件流同形对齐（rocqwash-sentinel-event/1·
  # seq 跨进程续号）/判18 plan 缓存失效语义（源件 md5 变→重算·恒同→hit 复用））
  # ＋--help 冒烟＋退出码口径抽验 2/2/9·零编译零网络零写盘）
  "$PY" -B "$REPO/tests/test_wash_shape.py"
}

t_unclog() {
  # 20261111 v37 集成席挂接·v40 稳态席扩容·v41 性能波扩容：疏通堵塞闭环引擎
  # （tools/unclog.py·手工五步闭环 probe 归集→chain_graph 挑根→cure_applier
  # 落刀→rescan/resprobe 复核→verdict 判定·schema rocqwash-unclog/1·
  # tests/test_unclog.py 最小自测壳三判：--selftest 冻结标记 UNCLOG-SELFTEST
  # PASS（十四矢量全 --injector canned 罐装·v40 轮增⑪--state-file 同形哨态
  # seen 差分（red-new 事件 only-new·损坏 state 红拒 9 禁静默重建）⑫--rounds/
  # --loop 与 --audit/--state-file 两组互斥 rc=2·v41 波⑫扩容 --probe-parallel
  # 0 用法闸 rc=2／⑬--jobs 维度 audit timing 段 jobs=K 入账（缺省 1/K=2 各录
  # 其值·同候选面异 K 前后跑可比））＋--help 冒烟＋退出码口径抽验 2/2/9（bogus/
  # 无参/缺路本集成席实跑验证）·零真编译零网络零触真仓）
  "$PY" -B "$REPO/tests/test_unclog.py"
}

t_cw_doctor() {
  # 20261111 v38 集成席挂接：综合体检器·四域聚合（tools/cw_doctor.py·四域
  # subprocess 编排既有一器（dyld/net_probe/probe_engine+chain_graph/注册册锚
  # 审计）→综合健康分 0-100＋verdict healthy/degraded＋advice·schema
  # rocqwash-cwdoctor/1·tests/test_cw_doctor.py 最小自测壳两判：--selftest
  # 冻结标记 CW-DOCTOR-SELFTEST PASS（九节向量全 --injector canned 罐装）＋
  # --help 冒烟·缺壳由本集成席自补·零真 otool 零真网络零真编译零触真仓）
  "$PY" -B "$REPO/tests/test_cw_doctor.py"
}

t_relay_e2e() {
  # 20261111 v39 工装席铸件·集成席挂接：接驳实战核 e2e（tests/test_relay_e2e.py·
  # cw_sentinel --on-red-preset unclog 全链三判：①哨 --once＋injector canned
  # CI 红炉→ci_triage 真判类 A-content-red→ci-red 事件→preset 代跑 unclog
  # rc=9 如实入账·旁路动作非器面·哨退出码仍 0 ②unclog --audit 干跑 rc=0·
  # --src 全文件 md5 清单跑前跑后自证零写盘·见红 red_files=["B"]·出可洗链根·
  # 墙空 ③JSONL 同盘 unclog report 路径与实落文件逐字节对拍 schema/verdict
  # 咬合——全 canned 罐装零真网络零真编译零触真仓）
  "$PY" -B "$REPO/tests/test_relay_e2e.py"
}

t_doclint() {
  # 20261111 v39 集成席缺壳自补挂接：文档←→实现一致性三查器（tools/doc_lint.py·
  # 工装席铸件·schema rocqwash-doclint/1·tests/test_doc_lint.py 最小自测壳
  # 三判：--selftest 冻结标记 DOC-LINT-SELFTEST PASS（tmp 迷你仓六矢量 V1-V6
  # 由铸席 --selftest 自证）＋--help 冒烟＋退出码口径抽验 2/2/9（bogus/
  # --help-cap 0/缺仓·本集成席实跑验证）·零网络零写盘零触真仓）
  "$PY" -B "$REPO/tests/test_doc_lint.py"
}

t_destructive_matrix() {
  # 20261111 v40 破坏面席铸件·集成席挂接：破坏面复核矩阵·一行一拒写判据
  # （tests/test_destructive_matrix.py·现役 33 行会写盘器×写面×护栏锚
  # file:line 逐行断言拒写护栏：unclog×4/wash_shape×4/pushci×3/
  # cw_sentinel×2/registry_union×2/cure_applier×4/frozen8×2/axiom_guard×1/
  # jargon_apply×1——干跑零写盘/--apply 才落刀/frozen 红拒/内容红零 rerun/
  # heal 帽尽停/report-only 缺省零动作等；X6 波谁写谁进阵新入 10 行：
  # scheduler_lite×2（SL1 缺 --out 零写盘·dryRun 恒真／SL2 唯一写面=显式
  # --out 两跑字节恒同）＋auto_merge×3（AM1 缺 --apply 零写盘／AM2 hold 永不
  # 授权＋越权分支白名单红拒／AM3 日预算帽＋重复拒）＋repair_scope×1
  # （RS1 --check 查询面零写盘＋共享名册判词咬合）＋E 波四守卫×4
  # （E2A lane-extract／E2B roster-resync／E2C flaky-quarantine／E2D
  # doc-count·四类皆干跑零写零账＋排除闸＋预算帽只落升格行）；全 tmp
  # fixture＋injector 罐装·零真网络零真仓零真编译（唯一例外 W3 递真在册件
  # 路径·收件即拒零读零写）·矩阵红＝护栏破·exit 1 响亮列破口 file:line＋违据）
  "$PY" -B "$REPO/tests/test_destructive_matrix.py"
}

t_baseline_diff() {
  # 20261111 v40 工装席铸件·集成席缺壳自补挂接：堵账基线对比器（tools/
  # baseline_diff.py·两份 unclog --audit 基线 argv 序=旧→新→new_blocks/
  # resolved_blocks/persistent 三清单＋score_delta·verdict improved/degraded/
  # stable/incomparable·账面自洽预检拒手编·候选面四元组比对·timing 段不入
  # 对比·schema rocqwash-baseline-diff/1·tests/test_baseline_diff.py 最小自测壳
  # 三判：--selftest 冻结标记 BASELINE-DIFF-SELFTEST PASS（六矢量由铸席
  # --selftest 自证）＋--help 冒烟＋退出码口径抽验 2/2/9（bogus/缺参=2·
  # 缺账文件=9·本集成席实跑验证）·零网络零编译零触真仓）
  "$PY" -B "$REPO/tests/test_baseline_diff.py"
}

t_red_dispatch() {
  # 20261112 v46 铸席铸件·集成席缺壳自补挂接：红事件路由器（tools/
  # red_dispatch.py·哨红事件→动作预设路由·三档 preset report-only/suggest/
  # auto·缺省零执行·auto 显式代跑 60s 帽 rc≠0 入账不改退出码·防重 state
  # ＋cooldown·路由全挂既有 cw.sh 路由零新引擎·A 族内容红禁代修出 fix 清单·
  # schema rocqwash-red-dispatch/1·tests/test_red_dispatch.py 最小自测壳
  # 三判：--selftest 冻结标记 RED-DISPATCH-SELFTEST PASS（十二矢量由铸席
  # --selftest 自证）＋--help 冒烟＋退出码口径抽验 2/2/9（bogus/dry-run
  # 误档=2·事件文件缺=9·本集成席实跑验证）·零网络零编译零触真仓）
  "$PY" -B "$REPO/tests/test_red_dispatch.py"
}

t_registry_audit() {
  # 20261112 v46 铸席铸件·集成席缺壳自补挂接：注册册卫生审计器（tools/
  # registry_audit.py·order.txt/_CoqProject 双册只读四账出账：重复行/锚撞/
  # 顺序号形/形怪/缺锚/孤儿/live 拓扑＋--fix-plan 确定性处方零写盘·--apply
  # 不存在·键式/锚正典直用 registry_union 零重造·病灶是数据恒 exit 0·
  # schema rocqwash-registry-audit/1·tests/test_registry_audit.py 最小自测壳
  # 三判：--selftest 冻结标记 REGISTRY-AUDIT-SELFTEST PASS（五判矢量由铸席
  # --selftest 自证）＋--help 冒烟＋退出码口径抽验 2/2/9（bogus/无输入面/
  # 半册=2·缺册=9·本集成席实跑验证）·零网络零编译零触真仓）
  "$PY" -B "$REPO/tests/test_registry_audit.py"
}

t_registry_fix() {
  # 20261112 v47 集成席直挂：注册册处方执行器（tools/registry_fix.py·
  # registry_audit --fix-plan 处方逐条落刀·三类处方 DEDUP 保首/锚刷/ORPHAN-ADD
  # skip·缺省干跑·--apply 落刀后断言含 dup 零残留/锚撞零增/孤儿不增/被治锚
  # 键锚残量零（A-fix-6·--orphan-add 时另加孤儿两判）任一炸即回滚·
  # staging 全内存零写盘·同参纪律 audit↔执行器逐字咬合·schema
  # rocqwash-registry-fix/1——器 --selftest 八矢量全 canned tmp fixture·
  # 零网络零编译零触真仓）
  "$PY" -B "$REPO/tools/registry_fix.py" --selftest
}

t_registry_fix_dedup() {
  # RQW09 duplicates-family executor seat (20261114): DEDUP contract unit
  # tests for tools/registry_fix.py — keep-first fix_plan direction pinned
  # from the registry_audit --fix-plan producer semantics, dry-run
  # zero-write, apply keep-first with exact per-item diff and post
  # re-audit duplicates=0, INJECT_BLAST post-write rollback, stale-plan
  # staging blast, CLI exit-code spot checks. tmp fixtures only, zero
  # real-repository contact, zero network, zero compile.
  "$PY" -B "$REPO/tests/test_registry_fix_dedup.py"
}

t_registry_fix_orphan_add() {
  # ORPHAN-ADD apply-path tests for tools/registry_fix.py
  # (tests/test_registry_fix_orphan_add.py): the opt-in --orphan-add face
  # executes the mechanically solvable order-only orphan prescriptions
  # (placeholder-free template appended to the coqproject book) - eight
  # fixture-based checks: default-off parity pin, dry run, apply with the
  # full assertion face, project-only skip stability, suffix-typo guard
  # (paired .v.v registration left for human adjudication), blast-hook
  # rollback (ROCWASH_REGISTRY_FIX_INJECT_BLAST=post-write), stale-
  # prescription guard, determinism. All on mkdtemp fixtures, zero
  # real-repo touch, zero network, zero compile.
  "$PY" -B "$REPO/tests/test_registry_fix_orphan_add.py"
}

t_registry_fix_anchor() {
  # REANCHOR-face tests for tools/registry_fix.py
  # (tests/test_registry_fix_anchor.py): the anchor residual gate
  # (A-fix-6 treated_anchors_canonical) plus the suite shell face — the
  # frozen --selftest marker, --help smoke, exit-code spot checks
  # (bogus=2/no-input=2/missing-audit-json=9), dry-run zero-write, apply
  # with the four assertion fields green, re-audit with executed keys
  # residual-free while skip-class keys stay by design, and six unit
  # vectors on the residual gate (blast on treated seq-form/malformed;
  # silent for untreated/collision/missing kinds). All on mkdtemp
  # fixtures, zero real-repo touch, zero network, zero compile.
  "$PY" -B "$REPO/tests/test_registry_fix_anchor.py"
}

t_norm_lint() {
  # 注释面规范化检查器挂接（tools/norm_lint.py·tests/test_norm_lint.py
  # 最小自测壳三判：--selftest 六矢量＋--help 冒烟＋退出码口径抽验 2/9
  # ——report-only 首形·基线账报告出账·零网络零编译零触真仓）
  "$PY" -B "$REPO/tests/test_norm_lint.py"
}

t_contrib_intake() {
  # contribution intake inspector (tools/contrib_intake.py): the protocol
  # four-check pipeline in one read-only run — registry/norm/gate
  # expectation/isolation gates never short-circuit, a BLOCK verdict is
  # data and the exit code stays 0. tests/test_contrib_intake.py minimal
  # shell, three checks: --selftest rc=0 with the CONTRIB-INTAKE-SELFTEST
  # PASS frozen marker (the tool's own dual-git-clone vectors attest the
  # four gates), --help smoke, exit-code spot checks bogus=2/no-input=2/
  # missing-face=9/bad-ref=9; tmp fixtures only, zero writes, zero
  # network, zero real-repository contact.
  "$PY" -B "$REPO/tests/test_contrib_intake.py"
}

t_evolve() {
  # autonomous evolution engine hook (tools/evolve.py):
  # harvest signal classes by subprocess of the existing engines, derive
  # scored candidates by fixed rules, draft the human-gated next-round task
  # brief (constitution three-law preamble auto-carried). tests/test_evolve.py
  # minimal shell, three checks: --selftest rc=0 with ten PASS vector groups
  # (canned signal injection via real subprocesses, candidate rules, draft
  # formation, frozen exclusion, sentinel seen-idempotence, deterministic
  # double run), --help smoke, exit-code contract spot checks bogus=2/
  # no-draft=2/no-signal=2/watch-without-state=2/two-suite-sources=2/
  # missing-baseline=9/missing-parent=9; tmp fixtures only, zero writes,
  # zero network, zero real-repository contact, draft-only (never executes
  # a candidate).
  "$PY" -B "$REPO/tests/test_evolve.py"
}

t_registry_regen() {
  # contribution registration-row regenerator (tools/registry_regen.py):
  # merge-target books verbatim as the draft bottom plus canonical
  # #R<seq>-<md5-8> rows tail-appended in dependency order, dry run by
  # default, --apply writes only under an explicit --out.
  # tests/test_registry_regen.py minimal shell, three checks: --selftest
  # rc=0 with the REGISTRY-REGEN-SELFTEST PASS frozen marker (the tool's
  # own tmp-fixture vectors attest the regeneration semantics), --help
  # smoke, exit-code spot checks bogus=2/no-input=2/apply-without-out=2/
  # negative-seq=2/missing-base=9; tmp fixtures only, zero writes, zero
  # network, zero real-repository contact.
  "$PY" -B "$REPO/tests/test_registry_regen.py"
}

t_clean_mode() {
  # clean-mode switch selftest (tests/test_clean_mode.py · ROCWASH_CLEAN=1):
  # canonical-dependency faces report "requires canonical environment" and
  # refuse; default mode (env unset) stays unchanged; clean-available
  # selftest faces still pass under the switch. Zero compile, zero network,
  # zero writes outside mkdtemp. Census: docs/clean-mode-manual-20261114.md.
  "$PY" -B "$REPO/tests/test_clean_mode.py"
}

t_vacgen_shape() {
  # 20261114 递归自愈席补挂接：vacgen 四账骨架形状自测（tests/t_vacgen_shape.py
  # ·zeta 面 fixture 铸形·四账 8 文件在盘断言·零编译零网络）。此例与
  # t_vacgen_expectedred 自 20261113 落位起即未接线（run_tests.sh 零提及＝
  # 套件不可见·RQW12 判例同款缺口），本轮一并补挂；subprocess 读取面补
  # encoding=utf-8（GBK locale 读线程解码破·对齐 expectedred 读形）。
  "$PY" -B "$REPO/tests/t_vacgen_shape.py"
}

t_vacgen_expectedred() {
  # 20261114 递归自愈席补挂接：vacgen 预期红契约自测（tests/t_vacgen_expectedred.py
  # ·三判：EXPECTED-FAIL 逐面登记/反判契约向量/红绿边界·预期红=数据非器红·
  # 未登记红才是缺陷·零编译零网络）。
  "$PY" -B "$REPO/tests/t_vacgen_expectedred.py"
}

t_vacgen_envelope_shape() {
  # 20261114 递归自愈席新铸：witness 包络词面形状自测（tests/t_vacgen_envelope_shape.py
  # ·fixture A 良形面契约钉（无裸型连言肢）＋fixture B 隐式 binder 面已知债钉
  # （债签名 ∧ Set ( 在场=钉绿·引擎修后钉红=按 SOP §2.5 勘误更新钉）·
  # 20261114 登记引擎债的唯一机检守卫·零编译零网络）。
  "$PY" -B "$REPO/tests/t_vacgen_envelope_shape.py"
}

t_refinery() {
  # refinery merge contract suite (tests/t_refinery.py): aggregates the six
  # lane segments under tests/refinery_segments/ (seam / vacgen / gap /
  # render / calib / sweep) into one SUMMARY + TOTAL line. Import-safe,
  # zero network, zero compile; an absent segment file is one loud SKIP.
  "$PY" -B "$REPO/tests/t_refinery.py"
}

t_symbiosis_shape() {
  # 20261115 roster hookup (audit finding P0-6): cross-repository
  # experience bus shape shell (tests/t_symbiosis_shape.py over
  # tools/symbiosis_bus.py) - seven subprocess checks: the export schema
  # matrix (rocqwash-symbio/1 envelope), import through the single
  # exp_port append face (rocqwash-exp/1 rows), idempotent re-import,
  # status and diff faces, exit-code convention, dry-run zero-write.
  # Offline by construction, tmp fixtures only. Supersedes the file's
  # earlier standing "not rostered" note.
  "$PY" -B "$REPO/tests/t_symbiosis_shape.py"
}

t_bus_feeder_shape() {
  # 20261115 roster hookup (audit finding P0-6): gap-ledger feeder shape
  # shell (tests/t_bus_feeder_shape.py over tools/bus_feeder.py) - seven
  # checks: the tool's own frozen selftest group, the real sample
  # docs/symbiosis-swap-round1.jsonl through the dry-run face (read-only),
  # the export-to-gap-rows end-to-end leg, idempotent re-feed, damaged
  # package refusals, usage and exit codes, status mapping and the write
  # surface. Offline, tmp fixtures.
  "$PY" -B "$REPO/tests/t_bus_feeder_shape.py"
}

t_uplink_shape() {
  # 20261115 roster hookup (audit finding P0-6): external return-package
  # intake gate shell (tests/t_uplink_shape.py over tools/uplink.py) -
  # three faces on tmp zip+md5 fixtures: verify (fail-loud red on any
  # digest mismatch or missing member, per-file evidence), intake (exactly
  # one docs/uplink-intake.jsonl row, schema rocqwash-uplink/1, nothing
  # else written) and pr-prep (a draft file only, never opens a pull
  # request); the repository-tree checksum must stay unchanged.
  "$PY" -B "$REPO/tests/t_uplink_shape.py"
}

t_evolution_dashboard_shape() {
  # 20261115 roster hookup (audit finding P0-6): self-evolution dashboard
  # shape shell (tests/t_evolution_dashboard_shape.py over
  # tools/evolution_dashboard.py) - seven fixture checks (three-source
  # aggregation over rocqwash-exp/1 + rocqwash-round/1 + vacgen v2 report
  # faces, conversion math, coverageLowerPct curve ordering with the
  # TODO-SEAT delta, default/explicit absence rule, exit codes,
  # determinism of both output faces) plus one read-only live check over
  # the standing account paths.
  "$PY" -B "$REPO/tests/t_evolution_dashboard_shape.py"
}

t_mcp_face() {
  # 20261115 roster hookup (audit finding P0-6): MCP stdio server face
  # shell (tests/t_mcp_face.py spawning tools/mcp_server.py) - one
  # newline-delimited JSON-RPC session asserting the 25-capability face
  # (legacy 8 + batch-1 zero-network 13 + engine-body 3 + symbiosis 1)
  # plus live-call spot checks; zero network by construction.
  "$PY" -B "$REPO/tests/t_mcp_face.py"
}

t_exp_port() {
  # 20261115 roster hookup (audit finding P0-6): experience-bus port
  # shell (tests/t_exp_port.py over tools/exp_port.py) - four checks:
  # --selftest rc=0 with the EXP-PORT-SELFTEST PASS frozen marker, --help
  # usage face, exit-code spot checks (bogus=2, append without
  # --points=2, query on an absent ledger=9), copy dry-run reports a
  # would-be id and writes nothing.
  "$PY" -B "$REPO/tests/t_exp_port.py"
}

t_periscope_shape() {
  # 20261115 roster hookup (audit finding P0-6): periscope sweep shell
  # (tests/t_periscope_shape.py over tools/periscope.py) - six checks:
  # --selftest rc=0 with the PERISCOPE-SELFTEST PASS frozen marker, --help
  # naming the six CLI flags, exit-code convention spot checks, a valid
  # six-source config dry-run, the draft-template invariants (five
  # judgment-template sections plus four negative-finding element labels),
  # and the dry-run writing zero bytes.
  "$PY" -B "$REPO/tests/t_periscope_shape.py"
}

t_engines_body() {
  # 20261115 roster hookup (audit finding P0-6): engine-body contract
  # suite (tests/t_engines_body.py, nine segments / 60 checks over the
  # ai_flavor, jargon_apply, ai_flavor_apply, i18n_pipeline,
  # i18n_translate, i18n_verify and termbase modules) - clean and polluted
  # probes, exit codes, idempotence, zero-write defaults, nine-key ledger
  # validation, the default-deny network gate, the budget cap and the
  # legal refusal path; modules load dynamically from tools/ and a
  # not-yet-landed module is one loud SKIP line, never a silent pass.
  "$PY" -B "$REPO/tests/t_engines_body.py"
}

t_engines_seeds() {
  # 20261115 roster hookup (audit finding P0-6): five-engine seed
  # assertions (tests/t_engines_seeds.py, E1..E5 segments / 40 checks with
  # EXPECTED_SEGMENTS accounting); seeds are located relative to the file,
  # and off-machine anchors report SKIP with a reason, never a silent
  # pass; zero network, zero writes.
  "$PY" -B "$REPO/tests/t_engines_seeds.py"
}

t_evolve_flag_contract() {
  # 20261115 roster hookup (audit finding P0-6): evolve.py flag-face
  # contract pin (tests/test_evolve_flag_contract.py, four checks: the six
  # cycle-3 ask flags verbatim in the --help face, the
  # --sentinel-events/--sentinel-state pair accepted without --watch-repo,
  # a no-signal-source round exits 2 fail-loud, the registry pair against
  # a book-less repository exits 9 fail-loud); tmpdir fixtures, zero
  # network, zero repository writes.
  "$PY" -B "$REPO/tests/test_evolve_flag_contract.py"
}

t_watch_repo_form() {
  # 20261115 roster hookup (audit finding P0-6): cw_sentinel --watch-repo
  # ORG/REPO form negative vectors (tests/test_watch_repo_form.py, three
  # checks: a local-directory form and a bare token are both refused with
  # rc=2 and the ORG/REPO message, and the REPO_RE match gate stays
  # anchored in tools/cw_sentinel.py; the form check fires before any
  # fetch, zero network reached).
  "$PY" -B "$REPO/tests/test_watch_repo_form.py"
}

t_flaky_guard() {
  # 20261116 repair-class E2-3 hookup: flaky quarantine guard
  # (tools/flaky_guard.py; tests/test_flaky_guard.py four checks: the
  # tool's 32-vector sandbox --selftest (order-dependent vs content-red
  # verdicts / dry-run zero-write / apply with ledger row / idempotent
  # re-apply / three green rounds with ADVISORY-OUT / budget and
  # frozen-target refusals / restore both ways / scope invariant / CLI
  # codes) plus --help plus exit-code spots plus one read-only --status
  # against the standing repo; zero writes outside mkdtemp, zero network,
  # zero compile).
  "$PY" -B "$REPO/tests/test_flaky_guard.py"
}

t_roster_resync() {
  # 20261116 repair-class E2-2 hookup: roster count drift guard
  # (tools/roster_resync.py; tests/test_roster_resync.py four checks:
  # --selftest rc=0 with the ROSTER-RESYNC-SELFTEST PASS frozen marker,
  # --help rc=0, --bogus=2, a missing --repo directory=9; the guard's own
  # tmp-fixture selftest attests the real doc_lint consistent flip as the
  # green criterion, the one-way CASES roster derivation (the roster file
  # is never written), the per-class per-branch budget cap at 2, and the
  # shared repair_scope exclusion gate; zero writes outside mkdtemp, zero
  # network, zero compile).
  "$PY" -B "$REPO/tests/test_roster_resync.py"
}

t_auto_merge() {
  # 20261116 X5-gate hookup: auto-merge gate judge plus safety rail
  # (tools/auto_merge.py; tests/test_auto_merge.py five checks: --selftest
  # rc=0 with the AUTO-MERGE-SELFTEST PASS frozen marker (24 vectors incl.
  # the five calibration samples S-1..S-5 pinned to their verdicts, the
  # supply/* whitelist both ways, the daily budget cap, dry-run zero-write,
  # the duplicate refusals, the post-merge revert arc four families),
  # --help face, exit-code spots 2/9, the five calibration fixtures judged
  # through the real CLI face, dry-run zero-write plus the rail refusal
  # exit contract; tmp fixtures only, zero network, zero repository
  # writes).
  "$PY" -B "$REPO/tests/test_auto_merge.py"
}

t_selfheal_guards() {
  # 20261116 X6-seat hookup: the three self-heal guardrail reinforcement
  # points as frozen vectors (.github/scripts/selfheal_rocqwash.py;
  # tests/test_selfheal_guards.py five vector groups 20 checks: the
  # attempt cap skipped(attempt-cap) at-most-once budget, the
  # cancel-intent never-revive gate plus its cap-outranks-intent order
  # pin, the live re-check before the rerun POST (in-progress/cancelled/
  # transport-error all skip; only a still-completed run reaches exactly
  # one rerun-failed-jobs POST), the transient-only family whitelist, and
  # the reconcile intent recording (cancelled=intent, never revived, zero
  # POSTs).  The script module loads by path with gh_api/time stubbed
  # in-process: zero network, zero real sleep, zero repository writes.
  "$PY" -B "$REPO/tests/test_selfheal_guards.py"
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
