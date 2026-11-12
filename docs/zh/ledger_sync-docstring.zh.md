# ledger_sync.py 模块 docstring 中文原档（留档）

- 源文件：`tools/ledger_sync.py` 模块 docstring（英文化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 docstring 全文移此留档而非删除；英文正本见
  `tools/ledger_sync.py` 模块 docstring。本文件为历史存档，内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。

---

ledger_sync.py — probe 台账×状态台账 TSV 合并同步器（rocqwash tools/·v30 实战
判例工具化·承 20261103 台账 v2 底册工艺·20261103 入账；v2.1 20261103 承 W59 支撑
席合账草案发现增补：items 子键识别＋批量元数据键滤除＋双代分歧出账）

probe 台账（probe_engine 产出 rocqwash-probe-ledger/1「records」壳、席位冻结账
「items」子键壳、或 W13 式裸 {件名: 记录}）×状态台账 TSV（表头含 件名/行数/md5/
RED/状态/备注 列族）→逐件对账合并 → 新状态台账 TSV。五机制（战役 E1/E3 伤口码
工具化＋v2.1 分歧出账）：

  E1 去重      状态台账内同「件名」多行 → 去重保留首行（确定性·后现重复逐笔
              计数响亮入账·不静默丢弃）。
  E3 幽灵      probe 台账有名而状态台账无行 → 幽灵响亮出账（只记账不落行——
              台账缺行属底册完整性事件·禁静默补行）。
  MD5-DRIFT   probe 记录带 md5 且 ≠ 台账行 md5 → 该行**不升格**只注记（探针
              凭据不为此代源件作保·响亮计数）。
  NO-MD5      probe 记录无 md5 字段（W13 老式账/冻结账 washed_md5 记录）→
              只注记不升格·响亮计数。
  GEN-DIVERGENCE (v2.1)  probe 记录携带 divergence_with/divergence_md5（多源
              合成双代分歧）→ 该行注记 probe:gen-div:<dropped>＋逐笔响亮出
              账——dropped 代不弃账·候落位批裁定·禁静默吞分歧。

分歧优先序（v2.1 成文——W59 支撑席双代分歧判例工具化）：多源合成 probe 同名双
代（两席各自洗出不同代）→ kept 代＝下游冻结账 ledger_basis 榜系所引用的源席代
（下游消费代）；dropped 代不入 probe 但以分歧字段留痕（合成器职责），同步侧见
分歧字段即出账。两职分立：合成侧按优先序排 records；同步侧对携带分歧字段的记
录逐笔响亮——工具面永不静默裁决代际。

probe 台账形态识别（v2.1）：顶层「records」dict → 直用；顶层「items」dict（席
位冻结账形）→ 直用；其余裸 dict → 按记录形（携带 md5/rc/red/file/washed_md5
任一字段的 dict 值）滤取，非记录形键（batch_meta/schema 等元数据）逐键响亮计入
meta_skipped·滤后零记录 → fail-loud 拒同步。

同步动作（逐匹配行）：
  1 注记：备注列追加探针凭据 tag（幂等——tag 已在即不重复）：
      rc=0     → probe:rc0        rc=1     → probe:rc1[:红因分类]
      rc=124   → probe:timeout    NO_SRC   → probe:no-src
      分歧字段 → probe:gen-div:<dropped>（幂等同上）
  2 升格（--policy unprobed-only 缺省·仅当行状态=UNPROBED 且 md5 咬合）：
      probe rc0 → 状态=WASHABLE；probe rc1 → 状态=DRIFT-BLOCKED
      （承台账 v2 判定口径：WASHABLE＝探针 rc0 闭包相容·DRIFT-BLOCKED＝探针
       rc1 红因在账——LANDED/FROZEN/OCCUPIED/GIANT 等上级状态永不降格改写）
    --policy annotate-only：只注记不动状态列。

列校验（fail-loud·exit 2·不产出）：缺必需列（件名/md5/RED/状态/备注）／行宽
≠表头列数／probe 台账形态不识别——一律响亮拒同步。

幂等：同 probe×同台账重跑 → 新台账字节级恒同（tag 在盘即跳过＋确定性遍历）。

用法（全部路径参数化·零硬编码·零网络）：
  python3 tools/ledger_sync.py --probe probe_ledger.json --ledger status.tsv       --out new_status.tsv [--report sync_report.json] [--policy unprobed-only]
  python3 tools/ledger_sync.py --selftest

退出码：0=SYNC-CLEAN（零发现）；1=SYNC-FINDINGS（E1/E3/MD5-DRIFT/NO-MD5/
GEN-DIVERGENCE 任一非零·新台账仍已落盘）；2=列校验/用法错（--help rc=0／缺必需
参数）；9=输入文件缺失。报告 schema=rocqwash-ledger-sync/1（v2.1 增 meta_skipped
字段·增量兼容）。

