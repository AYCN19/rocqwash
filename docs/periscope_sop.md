# SOP · periscope 六源外围情报采集与判读草案工具 / SOP: Periscope Six-Source Peripheral-Intelligence Sweep and Judgment-Draft Tool

> **一句话 One-liner**: periscope 把 2026-11-13 首轮外围情报采集的 as-built 工艺（六源观察清单·窗口协议·哨伴飞·判读草案五段模板）固化为一支可复跑的命令行工具；判读升级（撞车三态裁定·C1 重扫·对外披露）永远不在工具内自动发生。
> periscope freezes the as-built craft of the 2026-11-13 round-1 peripheral-intelligence sweep (six-source watchlist, window protocol, sentinel companion, five-section judgment draft) into one re-runnable CLI; adjudication upgrades (three-state collision verdicts, C1 rescans, external disclosure) never happen automatically inside the tool.

---

## 〇、适用域、前置闸与总判定语义 Scope, Pre-Flight Gates, and Verdict Semantics

### 0.1 适用域与输入输出面 Scope and I/O Surface

- **适用域 Scope**: 对一份可配置观察清单（schema `rocqwash-periscope-config/1`，缺省=六源 as-built 表）执行只读 GET 采集，落盘 raw 体＋逐发 NETRED 账＋哨窗口账，并产出五段式判读草案 `intel-ledger-draft.md`。
- **输入 Inputs**: `--config`（六源 JSON，缺省内置）、`--out`（输出目录，真跑必填）、`--rounds`（哨轮数）、`--netrc`（凭据文件，直传 curl，工具本身零读凭据）。
- **输出 Outputs**: `<out>/raw/<key>.json`（取件体）、`raw/<key>.retry.json`（404 定谳负发现证据体）、`raw/<key>.a<n>.json`（逐发体）、`raw/<key>.netred.txt`＋`raw/netred-master.txt`（逐发账含失败）、`raw/windowsniff.netred.txt`（哨窗口账）、`intel-ledger-draft.md`（判读草案）。
- **真跑前置门 Pre-flight gates (fail-loud)**:
  1. `--out` 缺席即拒绝发射（exit 2）——禁隐式网络扫；
  2. `--config` 文件缺席 exit 9，schema 漂移 exit 2（未知顶层键/未知 kind/越界 cap/非 hex 冻结前缀皆拒）；
  3. 只读承诺 GET-only：curl 实参构造器结构上不可能产出写动词，每次发射前 `assert_read_only` 复断言。

### 0.2 总判定语义 Top-Level Verdict Semantics

- **一切发现皆数据 Data, never errors**: 负发现（404 已证结论/帽尽未取/窗口死）与 C1 触发都响亮登记、exit 0——升级通道（重扫/披露）候令不自动。
- **草案≠裁定 Draft ≠ verdict**: 草案的机械行（初筛三态/哨判/排窗建议）是初筛；裁定是判读方的事。哨判词效力只及实测轮（负发现自划边界律同款）。

## 一、CLI 面 CLI Face（六旗标）

| Flag | Meaning | Default |
|---|---|---|
| `--config FILE` | six-source JSON (schema `rocqwash-periscope-config/1`) | built-in as-built list |
| `--out DIR` | output directory; **required for a real run** (implicit sweeps refused, exit 2) | — |
| `--rounds N` | sentinel companion rounds; one beat always fires after the sweep closes | 10 |
| `--netrc FILE` | passed to `curl --netrc-file`; the token is never read/logged by the tool | none |
| `--dry-run` | validate + plan + render the draft skeleton; zero network, zero writes | off |
| `--selftest` | offline frozen vector group (canned transport + virtual clock) | off |

Exit-codes: `0` run/dry-run/selftest green (negative findings and C1 triggers included) · `1` selftest red or draft invariant red · `2` usage/schema error · `9` missing input (config absent, output root not creatable).

## 二、Config Schema 与六源 as-built 表 Config Schema and the Six-Source As-Built List

Schema `rocqwash-periscope-config/1` 顶层键：`schema` / `sentinel` / `defaults` / `deposit_anchors` / `sources`（未知键 fail-loud）。每源键位：`key` / `kind`（`github_search`｜`github_api`｜`github_issue`｜`github_commits`｜`arxiv`）/ `url` / `auth`（`netrc`｜`none`）/ `cap`（1–16，缺省 8）/ `days_window`（arXiv 滚动窗，URL 带 `{WINDOW}` 占位）/ `comments`（issue 子面 `{enabled, per_page}`）/ `c1_frozen_prefix`（仅 `github_commits`，hex 前缀）/ `screening`（`keywords` / `own_markers` / `anchor`）/ `retry_param_overrides`（逐次重试的 URL 参数覆盖表）。

缺省六源（2026-11-13 首轮 as-built watchlist；可整表替换·端点改动只需改 config）：

| # | Key | Kind | Endpoint (as-built) | 判读面 Reading face |
|---|---|---|---|---|
| 1 | `mathlibpr` | github_search | `api.github.com/search/issues?q=repo:leanprover-community/mathlib4+is:pr+zeta&per_page=10` | 同题在先/竞速发现 |
| 2 | `pr45912` | github_api | `api.github.com/repos/leanprover-community/mathlib4/pulls/45912` | state/mergeable/CI 动态 |
| 3 | `arxiv-dzeta` | arxiv | `export.arxiv.org/api/query?...all:"Dedekind zeta"...{WINDOW}` · days_window=30 | 文献竞速面 |
| 4 | `arxiv-quasir` | arxiv | 同型（"quasi-Riemann"）· days_window=30 | 文献竞速面 |
| 5 | `issues` | github_issue | `api.github.com/repos/hy7pc8gfmf-dotcom/ConstructiveWorld-Main/issues/3` ＋ `/comments?per_page=30` 子面（可配置） | 自家派单帖动态 |
| 6 | `dzzftip` | github_commits | `api.github.com/repos/AxiomMath/DedekindZetaZeroFree/commits?per_page=3` · `c1_frozen_prefix=09afbb4` | C1 触发判定 |

`deposit_anchors` 缺省值：`mathlib_pr45912_closed_at=2026-11-11T22:19:13Z`、`dzzf_tip_frozen_prefix=09afbb4`、`dzzf_freeze_observed_at=2026-11-10T17:42:11Z`——初筛时点对表的锚。

## 三、三坑烧入 The Three Burned-In Behaviors

首轮（2026-11-13）三项实测坑已烧入工具本体，逐坑「判例 → 烧入行为 → 验证」：

### 坑 a · arXiv 腿第 1 发即带 `-L`

- **判例 Precedent**: 首轮 quasir 腿 8/8 发全 301（帽尽零收成），dzeta/leanrh 腿改参（补 `-L`）后一发即 200——重定向病烧掉 16.7% 的发数预算。
- **烧入 Burn-in**: `build_curl_args` 对 `kind=arxiv` 无条件在第 1 发即追加 `-L`（且任何 attempt 都带）；非 arXiv 源缺省不带（可用 `follow` 配置位打开）。
- **验证 Verification**: selftest V3——arXiv 源 attempt 1–8 的实参矢量逐发断言含 `-L`；GitHub 源矢量断言缺省无 `-L`。

### 坑 b · 哨前台伴飞零静默洞（轮距 60s·让渡必写 SUSPEND 行）

- **判例 Precedent**: 首轮哨后台档轮距 97s，且 R2→R3 出现 15min46s 零采样洞——「无采样」与「测得死」分不了账。
- **烧入 Burn-in**: 哨伴飞内建于采集同进程：beat 1 开扫前采样→采集扫（可能超时越过多拍）→被越过的每一拍显式写 `SUSPEND|<beat>|<UTC>|collection-sweep-in-flight`（禁静默跳轮）→扫毕后一拍必采样→余轮按 60s 节距补齐。`_assert_no_silent_gap` 机械断言 beat 序号 1..N 连续无缺；windowsniff 账落盘后回读断言（行数==beat 数·头行在位），漂移即 exit 9。
- **验证 Verification**: selftest V5——虚拟时钟下采集扫越拍 2 拍 → 恰 2 条 SUSPEND，序号连续，末拍为采样拍，回读对账过。

### 坑 c · 源④端点＝Main issue#3＋comments 子面（可配置）

- **判例 Precedent**: 首轮源④按五源表钉到 `rocqwash/issues/3` 吃 404 定谳负发现；根因＝派单协调台实在 `ConstructiveWorld-Main` issue#3（GET 200 · 87 comments 实证）——端点定装必须先经存在性 GET 验明。
- **烧入 Burn-in**: 缺省 config 的 `issues` 源 URL 钉 Main repository issue#3，`comments.enabled=true`＋`per_page=30` 子面在同源帽内随单点后取（发间 ≥2s、逐发入 NETRED）；单点 404 时子面不起飞（负发现四要素先行）。端点退役件（rocqwash repository issue 面单点）不入缺省表。
- **验证 Verification**: selftest V4——缺省 issues 端点==Main issue#3 且不含 rocqwash/issues；罐装两发（单点 200→comments 200）断言子面 URL 形、两发皆入账、comments count 解析在卷。

## 四、窗口协议 Window Protocol（帽 8·取到即停·sleep60 改参重试）

| 规则 Rule | 行为 Behavior |
|---|---|
| 帽 Cap | 每源 8 发（config `cap` 可改 1–16）；哨拍与 comments 子面发同样逐发入账 |
| 取到即停 Stop-when-obtained | 任一发 HTTP 200 且体可解析 → 该源终态 `obtained`，剩余帽不烧 |
| 失败重试 Retry | 非 200 非 404 → sleep 60s → **改参**重发：每次重试的有效超时放宽 30s（`curl-timeout:NNs` 记入 NETRED `changed=`），config `retry_param_overrides` 的逐次覆盖一并记 `config-override:n` |
| 404 已证结论 Negative-definite | 404 即停（不退避·保帽），404 体保全为 `raw/<key>.retry.json` 作四要素证据 |
| 帽尽未取 Cap-exhausted | 终态 `cap-exhausted-registered`＝登记非失败，四要素草案强制 |
| 解析败 Parse-error | 200 但体不可解析 → `parse-error-retryable`，照失败重试面走（首轮判例：体解析败＝管道数据非窗口数据） |

## 五、哨伴飞协议 Sentinel Companion Protocol

- 节距 `ROUND_SECONDS=60` 烧入不可配（改节距=改三坑 b 的语义，须改工具本体并过 selftest）。
- 窗口账行形：`R<n>|<UTC>|<code>|LIVE|DEAD` ＋ `SUSPEND|<n>|<UTC>|<reason>`；哨探活端点缺省 `api.github.com/rate_limit`。
- 哨判词边界（写死进草案第 5 段第 1 条）：只覆盖实测轮；未测段不能定谳死活——首轮判例「26 分钟连续活证不足以证伪碎片化假设」。

## 六、判读草案模板 The Judgment-Draft Template（五段·强制形）

`render_draft` 产出 `intel-ledger-draft.md`，五段结构对齐首轮判读卷：

| 段 Section | 内容 Content | 强制点 Mandatory face |
|---|---|---|
| 一 逐源 digest | per-source 表：fetched-at（UTC）/ shots / state / key facts（time-bound） | 逐源必有一行；raw 文件指引随附 |
| 二 撞车初筛三态 | 逐条目行：created/published vs deposit anchor＋关键词重叠 → `prior-registered` / `suspected-collision(adjudicate)` / `no-bearing` / `ours(registered)` | 机械初筛行必带判据说明；疑似撞车升格永不自动 |
| 三 C1 触发判定 | tip sha vs 冻结前缀 → `C1-CLEAN` / `C1-TRIGGERED` / `UNDETERMINED` | 触发=响亮登记，重扫候令 |
| 四 负发现四要素 | 每个未取到源一节：①scanned ②not scanned ③not an absolute claim ④aliased equivalents not exhausted | **强制 mandatory**：渲染器对任一 `negative-definite`/`cap-exhausted` 源缺任一要素即 AssertionError（exit 1，fail-loud）——四要素措辞正形承 negative-finding 边界律卡 |
| 五 排窗建议五条 | ①首发放行相位（哨实测＋边界句）②哨伴飞（beat/SUSPEND 计数＋零静默洞验证）③席间错峰（first-shot 取件面＋arXiv 错后）④帽与协议（逐源发数对帽）⑤改钉与跟进（C1 态/404 重钉候选/疑似撞车计数） | 五条形固定，逐条带 as-run 机械数据 |

**样例 Worked sample**: 首轮判读卷＝`attn/_periscope_20261113/intel-ledger-20261113.md`（25 发总账＋三态初筛 11 行＋C1 判定＋issues 404 四要素范文＋排窗五条原文）——工具产出的草案即该卷的骨架预填形，裁定句由判读方续写。

## 七、NETRED 与只读承诺 NETRED and the Read-Only Pledge

- 逐发账（含失败发）一行一发：`<UTC>|<key>|attempt=<n>|GET <url>|HTTP <code>|<bytes>B|<verdict>[|changed=…]`；per-source 账＋master 账双落。
- 只读承诺机械面：实参构造器无写动词位；`assert_read_only` 对每矢量扫描 `-d/--data*`（ outright 拒）与 `-X` 非 GET（拒）；selftest V7 对五种 kind×三档 attempt 全扫。
- 凭据排除：工具零读零存零回显 token——netrc 路径直传 curl；NETRED 行不含凭据字段。
- hosts 钉（本机 DNS 污染域）属环境面：操作者按 hosts 卡维护 `hosts` 文件，工具不代管。

## 八、离线自测与套件位 Offline Selftest and Suite Membership

- `--selftest`＝10 矢量冻结组：V1 CLI 面（六旗标＋裸跑拒绝）· V2 schema 矩阵（缺席 9/漂移 2×5 形）· V3 坑 a `-L` 逐发 · V4 坑 c 端点＋子面 · V5 坑 b SUSPEND＋零静默洞＋回读 · V6 帽/停/重试三分 · V7 只读全扫 · V8 草案五段＋四要素＋C1 双枝＋初筛四态 · V9 dry-run 零写入 · V10 NETRED 逐发对账。罐装 transport＋虚拟时钟——**零网络零写盘**（临时目录外零字节）。
- `tests/t_periscope_shape.py`＝套件壳（subprocess 四查：selftest 标记/--help 面/退出码口径/dry-run 骨架与零写入）。**不进 `run_tests.sh` 名册**：名册计数与 README.md 行三处机械对账（doc_lint ②计数查），README 归名册授权波管辖——承 `t_exp_port.py` 判例（tests/t_exp_port.py:11-14 同款登记）。

## 九、操作序 Operating Order（真跑三步）

1. **干跑验装**：`python tools/periscope.py --dry-run [--config my.json]`——读 plan 六行与草案骨架，确认端点/帽/锚无漂移（零网络零写盘）；
2. **真跑**：`python tools/periscope.py --out <dir> [--netrc <file>] [--rounds 10]`——产出 raw 体＋三账＋草案；哨拍先行探路；
3. **判读续写**：以 `intel-ledger-draft.md` 为骨架，按样例卷五段形续写裁定句（三态裁定/C1 处置/四要素补全②④要素），终卷按日期另名落盘；疑似撞车披露与重扫皆候令。
