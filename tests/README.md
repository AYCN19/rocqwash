# tests/ — rocqwash 自测套件

## 运行

```bash
bash tests/run_tests.sh          # 全绿 EXIT 0；任一红 EXIT 1；幂等可重复
```

套件自检（验证「任一红 EXIT 1」契约，注入一恒红例）：

```bash
ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh   # 预期 41 过 / 1 红 / EXIT 1
```

## 覆盖面（43 例）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 1 | `t_scan_selftest` | `scan/mac_stmt_scan.py --selftest` | E364 冻结向量组全过，exit 0 |
| 2 | `t_names_expect_pos` | `names/mac_stmt_names.py --expect` | fixture census 口径 7=7，exit 0 |
| 3 | `t_names_expect_let` | 同上 `--include-let` | 会师口径 8=8，exit 0 |
| 4 | `t_names_expect_neg` | 同上（负判） | 6≠7 → exit 2（CONTRIBUTING §4 口径） |
| 5 | `t_gate4_clean` | `verify/gate4_comment_guard.py --file` | 净样例五字段齐 → PASS，exit 0 |
| 6 | `t_gate4_dirty` | 同上（负判） | 脏样例禁词/缺字段齐发 → FAIL，exit 1 |
| 7 | `t_retrofit_dryrun` | `verify/retrofit_gate7_irr.py` | 干跑（写请求全截获·零落盘）过其全部内建断言 |
| 8 | `t_wash_judgments` | `wash/_abl1_wash.py` | exact-string+count 正判/幂等重放/破坏反判三判 |
| 9 | `t_wash_engine` | `wash/wash_engine.py`（通用逐件引擎） | `tests/test_wash_engine.py` 六判：pos（APPLY·count 断言·嵌套注释保留）／幂等（applied=0 skipped=N·逐字节恒等）／neg（FAIL·NOT-WRITTEN）／括号反判 2／写隔离 2／CLI 契约 3·3·2·9·9 |
| 10 | `t_verify_vo` | `verify/verify_vo.py --selftest` | 绿判四件套九判：魔数正负/陈vo负/log双判/exit双判/互斥/缺件 |
| 11 | `t_seam_probe` | `seam/seam_probe.py --selftest` | W13 四机制各一正例＋注释掩蔽/前奏册负例 |
| 12 | `t_freeze_manifest` | `certify/freeze_manifest.py --selftest` | freeze 幂等/零漂移/三漂移（changed/added/removed 各1·exit 1）/tier2 篡改必现形 |
| 13 | `t_push_gate` | `certify/push_gate.py --selftest` | UNION v2 六判（幂等/零漂移/漂移/tier1 篡改/union 层篡改/侧册篡改）＋window 四判（c1 双源 PASS/c1 零证据与封顶窗未到 NOT-RUN/c2 behind=1 CLOSED/c4 红套件 CLOSED·本地 path 远端·零网络） |
| 14 | `t_watch` | `watch/watch.py --selftest` | ci 离线四判（idle 0/在飞 1/未知状态保守计在飞/畸形 1/缺件 9）＋rewrite_host·遮蔽单元＋push 干跑四判（改写 URL/extraheader 入账·url-host 不符 2·缺对 2·原样出账）＋env 遮蔽＋confirm 三判（双读全等 0/不一致 1/单读拒 2·真 ls-remote 本地 path 远端） |
| 15 | `t_cpu_guard_direct_smoke` | `tools/cpu_guard.sh -Direct` | 探针一发即退 + `DIRECT bypass` 横幅 |
| 16 | `t_cpu_guard_direct_rc` | 同上 | 探针退出码传播（rc=7） |
| 17 | `t_scan_station` | `wrapper/scan_station.py` | `tests/test_scan_station.py` 九判（裸调指认卡/断言正负/嵌记/透传 rc=9/正本缺失 9/站自检/文件面透传） |
| 18 | `t_gate7_wrapper` | `wrapper/gate7_probe.sh` ＋ `wrapper/coqc_shim.sh` | `tests/test_gate7_wrapper.py` 十三判（双 bash -n/shim argv `c` 注入＋逐字透传/shim 缺 rocq 9/probe 用法 2×3/缺件 9×4/`--dry-run` guard 档位与形装账＋order 装配·零编译零写盘） |
| 19 | `t_verify_born` | `wrapper/verify_born.py` | `tests/test_verify_born.py` 九判（裸调哑成功禁律 2/--help/站自检九判/正本指认 pin/裸形 born.rc 原件直喂正判/前缀形 BORN_RC=0 归一化正判/BORN_RC=1 负判透传 1/--json 逐件账/伪断言败拒 2·临时目录驱动零仓写） |
| 20 | `t_frozen8` | `certify/frozen8.py --selftest` | 账载四判（判① 账载≡文档·机械收割更新账.md 八件在册值逐件咬合/判② 盘≡账·现盘八件 md5 全等 8/8/判③ 名单≡账·幂等·freeze 名单 tier1/tier2 与账载逐字咬合＋重产逐字节恒同/判④ 对账闭环·篡改现形·名单 md5 篡改与侧册篡改各 rc=1） |
| 21 | `t_frozen8_check` | `certify/frozen8.py check` | 在册名单四环咬合对账随套件在跑（名单 tier2 自洽/名单≡账载/tier2 侧册咬合/盘≡账载·rc 0 全咬合·只读零写盘·名单与侧册=`certify/frozen8_manifest.json`＋`frozen8_tier2.md5`） |
| 22 | `t_quad8` | `wrapper/quad8_reconcile.py`（四仓同 md5 副本群对账） | `--selftest` 夹具八判：freeze 咬合幂等/零漂移＋audit 只录/群漂移现形/UNREGISTERED 扫出/tier2·侧册·缺失三现形（零触真仓） |
| 23 | `t_quad8_check` | `wrapper/quad8_reconcile.py check` | 在册四仓名单随套件在跑对账（11 副本/六环咬合/audit 域只录不判·零写盘） |
| 24 | `t_frozen_call` | `wrapper/frozen_call.py`（逐调断言层） | `--selftest` 夹具五判：PASS 透传入账/在册外拒执 rc 8/tier2 先验 2/缺件 9/账行双见（临时账面） |
| 25 | `t_gate6_born_wrapper` | `wrapper/gate6_census.sh`＋`wrapper/born_world.sh` | `tests/test_gate6_born_wrapper.py`（启动层形制判·零编译零写盘） |

## 形制说明

- **fixture 最小化**：`fixtures/` 全部为本套件自造样例，不引外部大件。
  `retrofit_cn_sample.v`（842 行＋末换行）例外说明：`retrofit_gate7_irr.py` 的
  行形断言（843 split·L34 分隔行·L36 Require 行·`mod.M` 逐行锚）为硬编码，
  该 fixture 由 `mod.M` 锚表机械合成（`python3 tests/test_retrofit_dryrun.py --regen`
  可重建），内容零外部素材。
- **席位硬编码件的驱动方式**：`retrofit_gate7_irr.py` 与 `_abl1_wash.py` 无 CLI、
  路径硬编码席位（`retrofit_gate7_irr.py:7-11`、`_abl1_wash.py:10`）。测试以模块
  导入＋常量补丁把真实 `main()` 驱动到 fixture 上；硬编码席位路径永不被触碰
  （retrofit 干跑的写请求全部截获到内存——不落盘的机械化证明；wash 只写 mkdtemp
  临时目录，测毕即删）。
- **幂等**：`python3 -B` 禁 `__pycache__`；临时日志 mktemp+trap 清理；对仓库零写入。
  重复运行输出逐字节恒同。
- **已知实测行为（非缺陷猜测）**：`_abl1_wash.py` 重放时 `abl_audit_base_v7.v:require`
  会再 APPLY 一次——其 `new` 以 `old` 为前缀，工具 SKIP 判据要求 `c_old==0`，
  该 tag 恒不满足（`test_wash_fixture.py` 幂等判按 old⊂new 集合动态断言）。
- 退出码口径承 [CONTRIBUTING.md §4](../CONTRIBUTING.md)：`0`=通过、`2`=断言失败
  （`--expect` 等）、`9`=缺件；套件层 `0`=全绿（**含 SKIP**——SKIP 不计红）、
  `1`=任一红；例级 `111`=SKIP（正本环境缺卷让席·正本机恒全量真扫）。

> **gate4 预扫三铁则（口径段旁注·20261101 v10 轮入册）**——gate4
> （`verify/gate4_comment_guard.py`）对 Set 仓树预扫描必守三则：
> ① **预扫必须自 Set 仓根用绝对路径跑**（cwd 错位伪绿判例）：相对 `--tree` 在错位
> cwd 下解析到别棵在盘树即扫错面出伪绿——工具侧仅对「树不存在」设防（FATAL rc=2，
> `gate4_comment_guard.py:747-750`），对「存在但非目标树」不设防；
> ② **头注 ≤30 行硬上限（CI 全树口径）**：`--length-cap` 默认 30
> （`gate4_comment_guard.py:732`、`check_file` 形参 `:379`、超标检 `:527-534`）；
> ③ **五字段带点形** `Mission.`／`Dependencies.`／`References.`／`Constructivity.`／
> `Build.`（`FIELD_SPECS` 五字段英文带点正则：`gate4_comment_guard.py:188-194`）。
> 〔给料属性：判例面①与「CI 全树口径」承 v10 轮工单；②③上限值与五字段词形为
> 工具侧在卷锚点。详见 `更新账.md` v10 节。〕

## 五课反馈轮补记（20261101·席 rqsupport·用例 26–29）

> 编号承接套件现势（run_tests.sh 已在册 25 例——其中 22–25（`t_quad8`/`t_quad8_check`/
> `t_frozen_call`/`t_gate6_born_wrapper`）四行为前轮新增、本表未及同步；本席只补本轮
> 四行，不代前轮补表。〔rqsup4 巡检打磨轮补注：上四行已由该席据 run_tests.sh 用例
> 注释与前账账段于 20261101 补齐如上——非前轮原笔，判据描述以 run_tests.sh 为准。〕）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 26 | `t_world_hook` | `wash/world_hook.py`（世界基校验钩子·新件①） | `tests/test_world_hook.py` 五判：工具 selftest 十二判／**五课负例①nw5**：偏斜世界 WDIFF→rc 9·引擎零落盘（born 前断言拦下）／WMISS→9／pos 透传洗刀→产物落盘／冻结引擎 md5=`664446bc…` 零触旁证 |
| 27 | `t_select_audit` | `tools/select_audit.py`（选件审计器·新件②·v6 判据轮扩） | `tests/test_select_audit.py` 二十判：selftest 十一判／**五课负例②nw6**：批内重复→rc 1·DUP-BATCH／**负例③enbig7**：双批同名→rc 1·DUP-CROSS／树外名→NOT-IN-ORDER／pos（含 #代签与 / 路径形）→AUDIT-CLEAN／**v6 判据（nw10/abl6 空账·20261030）15 判**：parse_requires 全形式解析（From X Require Import/Export 多名多行·裸 Require·注释 Ghost 剥·动词/From 逐名在账）→STDLIB_ROOTS 白名单豁免（判例六件对空世界零缺口）→audit_requires 世界 .v/.vo 存在性闭包（缺口恰二·UpReqBanach 不误咬 UpReqBanachExp.v·计数面 8/3/5）→fail-loud 两向（MissingPath）→CLI 四码 0/1/2/9→**实盘补件面**：字符串散文 Require 剥（UpReqIndex.v:2821 判例形）＋裸形 Stdlib 白名单→缺口恰一 LW0QPoly |
| 28 | `t_verify_gate6` | `verify/verify_gate6.py`（gate6 薄包装＋eum 判例器化·新件③） | `tests/test_verify_gate6.py` 五判：selftest 十判／**五课夹具④gate6 ch1**：eum before(ch1=1)→after(ch1=0·名 5=5)→GREEN／ch1 滞治→RED／薄调正判（正本真扫·夹具树 ch1≥1）／judge 单翼→2 |
| 29 | `t_recipe_s07` | `recipes/S07_projection_reanchor_E5.md`＋E5 病面机检（新件④⑤） | `tests/test_recipe_s07.py` 五判：处方件判例锚词面齐／**五课夹具⑤**：E5 病面（语句面裸投影·跨行连排）→命中／注释掩蔽→零命中／愈面（real_eq/real_lt/real_le）→零命中／冻结引擎 md5 零触旁证 |

## 五课打磨轮补记（20261101·席 rqsup4·用例 30–31）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 30 | `t_recipe_pw1` | `recipes/ENBIG7_same_domain_collision_PW1.md`＋PW1 链机检（五课件③） | `tests/test_recipe_enbig7_pw1.py` 五判：处方件判例锚词面齐（PW1/仲裁 36c35816/五步词）／**前兆负例**：双批同名→`select_audit` DUP-CROSS rc 1／**入侵置换负例**：fixture 世界错代→`world_hook` WDIFF rc 9·引擎零落盘／**愈面正判**：认证代世界→WORLD-BASE-OK·透传引擎落盘／冻结引擎 md5 零触旁证 |
| 31 | `t_precedent_station` | `wrapper/precedent_station.py`（三判例验收站·五课件⑤） | `tests/test_precedent_station.py` 七判：`--station-selftest` 十判／轻链正判烟（fixture 语句面全等·证明体异→exit 0·站账 verdict PASS·knife 记名）／负判（语句面多一句→①rc 2→exit 1·不短路仍出②账）／REVIEW 升格（`--gate4-length-cap 5`→exit 2）／gate7 形制（缺 module→2·缺 .v→9·零开步）／未知刀面拒→2／names·gate4 冻结 md5 零触旁证（gate7 实跑为真编译重步·E2E 归席位沙箱不入套件） |

## 实战判例工具化轮补记（20261101·用例 32–33）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 32 | `t_netname_normalize` | `tools/netname_normalize.py`（.v.v 双后缀名净名归一器·本轮工具化①） | `tests/test_netname_normalize.py` 九节：selftest 八判／干跑默认（MAP 映射表 `<净名>.v.v→<净名>.v` 逐条·零字节落盘）→rc 1 PENDING／`--apply` 归一落盘→rc 0·源亡标在／md5 前后验讫在账（RENAME 行 md5=＋VERIFY-OK·改名不改字节逐字节断言）／COLLIDE 拒覆写（X.v 与 X.v.v 并存→rc 1·对侧件内容保全）／净世界→rc 0 CLEAN／CLI 四码（help 0·未知形参 2·缺 --dir 2·--dir 缺失 9）／`--map` TSV＋`--json` 出账咬合／`.v.v.v` 形一层一归一（临时目录夹具·零触真仓） |
| 33 | `t_verify_fresh` | `verify/verify_vo.py --require-fresh`（fresh-compile 防线·本轮工具化②） | `tests/test_verify_fresh.py` 八节：verify_vo selftest 十三判（原九判＋防线四判）／正判（9.1 魔数＋vo 新鲜）→rc 0 FRESH-OK／陈 vo 负例（v 拨未来）→rc 9 fail-loud／坏魔数（头 8 字节非 `436f712100015ff4`）→rc 9（新鲜也拦·非本链产物）／缺 v·缺 vo→9／单参与混用→2／help 0·未知形参 2／魔数冻结口径对 `verify_vo.py` VO_MAGIC_HEX 模块级咬合（divmod_gen 陈旧 vo 假绿判例工具化·临时目录夹具零编译零触真仓） |


## gate7 涨账工具化轮补记（20261101·用例 34）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 34 | `t_extract_magic` | `verify/extract_magic_check.py`（gate7 提取面 Obj.magic 逐件机检闸·本轮工具化③） | `tests/test_extract_magic.py` 十一节 23 判：selftest 十二判／E2E 红判（假 rocq/ocamlc 桩全链·默认 max=0 魔数 2→rc 1·上下文逐行 L1/L2·VERDICT: FAIL）＋台账咬合（verdict/magic_ml/max/magic_lines/ocamlc status）／E2E 绿判（--max 2→rc 0 PASS·mode=driver·targets 咬合·md5_v 对模块级）／inline 形（.v 自带 Separate Extraction→mode=inline·commands 逐名）／driver 形（本仓自带 `fixtures/names_sample.v` 只读兜底收 census 7 名含 Unicode 名道＋driver 稿词面 Stdlib Extraction 前奏在盘）／提取红（假 rocq rc=1→fail-loud·rocq_tail 随账）／ml 未产出红（不可计数≠绿）／ocamlc 面红（在卷实跑红→rc 1）＋缺卷让席（NOT-RUN 不计红·魔数面独立判）／CLI 四码（help 0·未知形参 2·缺 --world 2·缺 v 9·world .vo 未编译 9）／grep -c 口径（行计数·一行多魔数计一）模块级咬合／**v15 盲区补全节（首战判例·gate7 四件 2 PASS/2 Class 盲区 fail-loud）**：Class 声明夹具（Class/Record/Scheme/Canonical/Context/Declare/Extraction/About/Close 全形）census 不再误判异常——声明/命令 vernacular 不入目标·唯真主定义 cls_pick/req_inst 入账·DECL_SKIP_EXT 十五 token 在册／G13 形裸 Extraction 命令同治／未知 vernacular 仍 fail-loud rc=9（盲区收窄≠静默扩容·token 集常量定位＝冻结件 names/mac_stmt_names.py:38–51 frozen8 tier1·扩补落工具 import 面·冻结件字节零触碰）。假桩全链零真编译零触真仓（真链 E2E 归席位沙箱不入套件·承 precedent_station 判例口径） |


## v29 判例工具化轮补记（20261103·用例 35–37·v30 轮代补记）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 35 | `t_scan_v4_token` | `scan/scan_v4_token.py`（token 级限定名普查·W15 工具化①） | `tests/test_scan_v4_token.py` 十一判：混合行遮蔽夹具三站复现＋旧法（行级 grep -v 式）同夹具漏站＝盲区机械实证＋binder 追踪零误报＋已洗参照件零站；真树抽查 `ROCWASH_TREE_SAMPLES` 环境门控缺省跳过不充红 |
| 36 | `t_cure_pack` | `wash/cure_pack.json`＋`cure_applier.py`（消费位治愈正典包·五式存量＋v1.1 九式＋v1.2 五式·W15 工具化②·v31/v32 扩） | `tests/test_cure_pack.py`：legacy 五式触发/幂等/门控自检＋v1.1 face-regex 九式自检（face/proof 域守卫·intros-tail guard·exclusive-group rc4）＋v1.2 S07 五式自检（壳除/记号重绑/桥裸名/谓词面收敛/binder 站型·binding-right 守卫·file_include 门）＋fixture 干跑-apply-二次零变更（qle/natle/shadow 三夹具·守卫负例逐字断言）＋S07 夹具流程（术前站数 1 report-only·干跑 A=2/B=1/C(a)=5/C(b)=2·apply＋binder 手术＋全零复跑·conflict --json rc4 器修回归）＋`cure_examples.v` 编译 rc=0（`ROCWASH_ROCQ` 门控·cpu_guard 包裹）＋门控 S07 编译弧（world 绿→base 红面 Illegal application→cured＋手术绿→Separate Extraction .ml/.mli 双面 Obj.magic 0/0·裸字段经全局实例解析）＋不透明 reflexivity 负证 rc≠0 |
| 37 | `t_erasure_classifier` | `verify/erasure_classifier.py`（擦除位六簇分类器·W15 工具化③） | `tests/test_erasure_classifier.py` 十三判：六簇判定/coq_ 前缀/多行 inner-component/premise 位/CAPTURE 交叉对拍/resolve 状态；真件回放 `ROCWASH_ERASURE_MLI/SCAN` 门控缺省跳过 |

## v30 探测战役工具化轮补记（20261103·用例 38–40）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 38 | `t_probe_engine` | `wash/probe_engine.py`（批量闭包相容探针引擎·承 W13 probe_batch.py·v30 工具化①） | `tests/test_probe_engine.py` 九节：工具 selftest 四判／stub 全链三分（WASHABLE rc0+RED>0／BORN-CLEAN rc0+RED=0／RED-MISSING_LIB rc1·missing 库名捕获·red_count/md5_match 回填）＋清场五件出世界入 logdir／NO-SRC 不编译如实出账／TIMEOUT（--timeout 2→rc=124）／resume 幂等（重跑 SKIP(done)＋台账字节恒同）＋--fresh 确定性同账／guard 队列制包裹（rc=7 真取透传＋留证日志 [cpu_guard] 横幅）／RED 缺列→RC0 三分不可判如实出／CLI 四码（help 0·未知形参 2·缺参 2·缺件 9）＋坏清单（缺 md5 列）rc2／真 rocq 全链门控节（`ROCWASH_ROCQ` 缺省 SKIP 不充红；门控轮：fixtures 一绿一红经 cpu_guard 包裹实编译→BORN-CLEAN＋RED-MISSING_LIB＋世界纯度＋logdir 留证全过）。夹具 `fixtures/probe_pass_sample.v`＋`probe_red_sample.v`（临时目录驱动零触真仓·stub 节零真编译） |
| 39 | `t_chain_graph` | `tools/chain_graph.py`（多账合并链根图·承 W25 w25_merge_ledgers.py·v30 工具化②） | `tests/test_chain_graph.py` 七节：selftest 六判／双形通吃（probe_engine records 壳×W13 裸 dict 混并）／合并语义（后批覆盖·batches 累积·标签取文件名去 .json）／链根自身可洗性三分（washable true/false/UNPROBED 逐字段）／missing 双源（字段直用·red regex 兜底 raw 空格形与「 | 」拼接形双咬合）／TOP 榜（n 降序·`--top` 截断·表头行·json top_order 保秩）＋json/md 重跑字节恒同／CLI 四码。合成双账临时目录夹具零触真仓零网络 |
| 40 | `t_ledger_sync` | `tools/ledger_sync.py`（probe×状态台账合并同步·v30 工具化③·v2.1 增补） | `tests/test_ledger_sync.py` 十节：selftest 十三判／CLEAN 全链（全覆盖 probe＋零发现 exit 0·UNPROBED 升格 rc0→WASHABLE／rc1→DRIFT-BLOCKED 逐行咬合·probe_engine 全字段记录直吞）／E1 去重（同件名多行保首行·逐笔 FINDING·行数正确）／E3 幽灵（只记账不落行·名单响亮）／特异 tag（rc=124→probe:timeout·NO_SRC→probe:no-src·UNPROBED 不升格）／NO-MD5（W13 老式账只注记不升格）／报告面（--report JSON schema/counts/逐笔发现咬合）／CLI 四码＋列校验两变体（缺必需列 rc2 不产出·行宽不齐 rc2）＋幂等重跑字节恒同／items 子键壳＋元数据滤除（PROBE-META-SKIP·全元数据零记录 rc2 拒同步）／GEN-DIVERGENCE 分歧出账（divergence_with 记录逐笔响亮＋行注记 probe:gen-div 洗代名·幂等·md5 咬合升格照常）。合成夹具临时目录零触真仓零网络 |
| 41 | `t_comment_pack` | `wash/comment_pack.json`＋`comment_sweep.py`（注释域 sweep 旁车·v31 工具化） | `tests/test_comment_pack.py` 六节：selftest 四判（旗词注释域换形＋字符串/嵌套注释免疫＋头注换代＋w7 code 行全等投影＋幂等）／pack 完整（engine=comment-state-machine·旗词表 载体→carrier·header_spec 五字段英形＋行上界 30）／fixture 流程（干跑零写→apply 换形 2 处·字符串字面量逐字保留·嵌套深度可达→重跑零变更）／头注换代（--header-map 数据驱动·换代后 code 行全等·重跑零变更）／头注形校验（五字段缺一报 problem report-only）／CLI 三码（help 0／缺参 2／缺件 9）。夹具临时目录副本驱动·零触真仓零网络 |

## v32 S07 适配式工具化轮补记（20261103·新增用例 42＋用例 36 扩节·W66 支撑席提案实装）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 42 | `t_dual_scan` | `scan/dual_scan.py`（双器对拍驱动·v32 工具化·承 seat_wash66 w66_dual_scan.py） | `tests/test_dual_scan.py` 十节：净样例双器 0/0＋双端空 diff／语句面站 only_stmt 非空 only_v4 空（单侧情·报而不决——器共识非全集证）／token 站 only_v4 非空 only_stmt 空／确定性（同目标两跑报告字节恒同）／CLI 四码（无目标 2·缺 dir 2·缺 file 9·缺器 9·help 0）。临时目录夹具驱动零触真仓零网络 |
| 36（v32 扩节） | `t_cure_pack` | `wash/cure_pack.json` v1.2＋`cure_applier.py`（S07 世系适配五式＋line-insert/station-report 两引擎＋exclusive-group --json 器修） | cure32_A 壳除（型注＋binder 双站·:=-binding-right 右位排除）／cure32_B 记号重绑（末个 Import 行后插 Notation 行·file_include＋裸 R 门·幂等跳过）／cure32_C(a) 桥裸名（face+proof 域·8 名交替）／cure32_C(b) 谓词面收敛（lt→real_lt/req→real_eq·mult 等含 lt 子串词零触碰·收敛目标=供给引理结论常量名机械断言）／cure32_station binder 壳站（report-only·术前 1/术后残差 0·--apply 幂等残差排除 report 型）／conflict 器修回归（--json 落盘＋rc=4＋零 traceback） |

## v34 E2/E3 提取面缺陷族 cure 扩节（20261104·用例 36 扩节·CI #178 逆向修订轮）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 36（v34 扩节） | `t_cure_pack` | `wash/cure_pack.json` v1.3＋`cure_applier.py`（E2/E3 缺陷族五式·零新引擎全复用 v32） | pack 完整（5+9+5+5=24·v34_lineage 在册·cure34_E2_station report-only·E3 对式序=站改写先于 shim 插入机械断言）＋selftest v34 向量（E3 站改写 2/shim 插入/shim 体 face_exclude 护体二遍零残差；E2 标注/元数/report 站/幂等；v34 whole-pack 幂等）＋夹具流程（E3 干跑 stations=2 shim=1→apply rc0→shim 行在·站改写·shim 体原样→全零复跑；E2 术前站数 1 report-only→apply→中间件面＋元数随行→全零复跑含 station 残差）＋门控 E2/E3 编译弧（`ROCWASH_ROCQ` 门控·cpu_guard 包裹：world 绿→**pre-fix 消费件编译绿＝提取时缺陷族实锤**→cure→cured 绿→Separate Extraction：E3 消费单元 magic 0/0＋`val ufx_nat : coq_Real -> coq_Real` 单态 shim 站；E2 修前 .mli `'a1 -> 'a1` 多态面→修后 `val unann : nat -> nat` 单态面→消费单元 magic 0/0→**world 访问器债=1 机械钉**〔实体修复工作流域·fixture world 头注与 canonical_note 记界〕）。夹具 `fixtures/cure34_e23_world.v`＋`cure34_e3_fixture.v`＋`cure34_e2_fixture.v`（临时目录驱动零触真仓·干跑永不编译） |
