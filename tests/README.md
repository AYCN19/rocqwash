# tests/ — rocqwash 自测套件

## 运行

```bash
bash tests/run_tests.sh          # 全绿 EXIT 0；任一红 EXIT 1；幂等可重复
```

套件自检（验证「任一红 EXIT 1」契约，注入一恒红例）：

```bash
ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh   # 预期 31 过 / 1 红 / EXIT 1
```

## 覆盖面（31 例）

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
  （`--expect` 等）、`9`=缺件；套件层 `0`=全绿、`1`=任一红。

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
