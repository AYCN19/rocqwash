# tests/ — rocqwash 自测套件

## 运行

```bash
bash tests/run_tests.sh          # 全绿 EXIT 0；任一红 EXIT 1；幂等可重复
```

套件自检（验证「任一红 EXIT 1」契约，注入一恒红例）：

```bash
ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh   # 预期 16 过 / 1 红 / EXIT 1
```

## 覆盖面（16 例）

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
