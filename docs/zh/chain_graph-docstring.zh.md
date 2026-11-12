# chain_graph.py 模块 docstring 中文原档（留档）

- 源文件：`tools/chain_graph.py` 模块 docstring（英文化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 docstring 全文移此留档而非删除；英文正本见
  `tools/chain_graph.py` 模块 docstring。本文件为历史存档，内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。

---

chain_graph.py — 多份 probe 台账合并→链根图→TOP 榜（rocqwash tools/·v30 实战
判例工具化·承 seat_wash25/w25_merge_ledgers.py 1:1 泛化·20261103 入账）

输入 N 份 probe 台账 JSON（argv 序＝合并序；probe_engine 的
rocqwash-probe-ledger/1「records」壳与 W13 式裸 {件名: 记录} 双形通吃）：
  1 合并：并集；重复键保留后批记录（后批覆盖前批·战役口径），batches 字段
    累积全历史标签（标签＝文件名去 .json·重名自动缀序号）。
  2 缺库提取：记录已有 missing 字段（probe_engine 产出）直用；否则对 red 原文
    跑缺库 regex `(?:Unable to locate library|Cannot find library)`。
  3 链根图：rc1 件按所缺库分组 → lib → dependents/n/batches；每根附**自身
    可洗性字段** self——根件自身在合并账中的 rc/verdict：
      washable=true（rc=0）＝洗此根即解锁全部 dependents（链根正典）；
      washable=false（rc!=0）＝根件自身亦被阻（链中环·先治根的因）；
      probed=false＝根件未在候选集（UNPROBED·候补探）。
  4 TOP 榜：dependents 数降序（同数按库名典序）出 markdown＋json。

输出全部确定性（sorted 迭代＋sort_keys 落盘）：同输入重跑字节级恒同。

用法（全部路径参数化·零硬编码·零网络）：
  python3 tools/chain_graph.py LEDGER1.json LEDGER2.json [...]       [--json chain_graph.json] [--md chain_top.md] [--top 25]
  python3 tools/chain_graph.py --selftest

退出码：0=出账完成（rc1 计数是数据非器红·响亮入 stdout）；2=用法错；9=任一
输入台账缺失。图 schema=rocqwash-chain-graph/1。

