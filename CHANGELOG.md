# Changelog

rocqwash 对外可见器面变更总账（Keep a Changelog 简式·`[Unreleased]` 段蒸馏
v35-v39 五波要点）。逐轮细账以 [`更新账.md`](更新账.md) 各段与各器 docstring／
`--help` 为正本，本文件只作蒸馏索引；与器不一致视为 bug（CONTRIBUTING §1.5
同律）。版本号沿用仓库「vNN 波次」口径，commit 哈希随附。

## [Unreleased]

### v35 — CI 诊断工具链波（2026-11-11·acf9fe6）

**Added**

- `tools/toolchain_dyld_doctor.py` — dyld 工具链断链诊断器：otool -L 解析
  rocqworker 外部硬引用→逐条 exists/missing 判定→missing 件按 donor 根溯源→
  restore 建议只打印禁代执行；`--smoke` 可选冒烟（SMOKERC＋.vo 魔数报数）；
  schema `rocqwash-dyld-doctor/1`·退出码 0 healthy/1 missing-libs/2 用法/9
  worker·otool 缺。
- `tools/net_probe.py` — 上传端点网络窗探针：缺省四端点裸 GET（HTTPError
  500/400＝可达即健康·URLError/timeout＝不可达）；双探稳窗律（连续两轮全过
  才 STABLE·单探禁发射）。
- `tools/ci_triage.py` — CI 红炉分诊器：五族判类谱（A 内容红／B NETRED／
  C 工具链断链／D 排队资源墙／E coqchk-skipped）＋绿炉 watch-only·
  UNRECOGNIZED 不充谱；判类序 UNRECOGNIZED>C>A>E>B>D；`--logs` 十三族关键行；
  红是数据非器红。
- `tools/registry_union.py` — 注册册 union 手术器：main 为底＋对 merge-base
  真独有行尾插·A1/A2/A3 断言 fail-loud·`--reanchor` md5-8 正典形·CRLF 保全·
  缺省干跑 `--apply` 才写盘。

**Changed**

- `cw.sh` 增 doctor/net-probe/triage/union 四路由（十一工具）·透传契约未动；
  本地映射 cw_paths v1.0→v1.1（八根新段＋移根监察表）。
- 自测套件 47 例（43 过／0 红／4 SKIP·EXIT 0）。

### v36 — 编排层：pushci 一键流水线（2026-11-11·4026051）

**Added**

- `tools/pushci.py` — 修复后推送 CI 一键流水线（五段：preflight
  doctor＋net_probe 双闸＋可选 gate4 头注预扫→push HTTP/1.1 三发＋ghproxy
  换路→resolve+watch（head_branch+head_sha 咬合）→heal（ci_triage 判类分派·
  有界 rerun 帽 3）→verdict±merge（409 重拉 tip 重试 ≤3））。v35 四器
  subprocess 编排零新引擎；verdict 七态封册（success/dry-run=0·
  heal-exhausted/unstable/toolchain=1·fix-content/gate4-block=2·9=目标缺失）。
- `tests/test_pushci.py` ＋ 六场景 canned 夹具（绿径／NETRED 愈合／内容红零
  rerun／heal 耗尽／merge 200／dry-run 零副作用）·15 过 0 红；离线可测硬要求：
  `--injector` 双形＋`--git-caller` 成对·`--sleep-scale 0`·api_calls/git-caller
  调用流水逐位对拍。

**Changed**

- `cw.sh` 十二工具；README-cw.md 主流水线升级 doctor→net-probe→pushci→triage
  （诚实旁注：推窗四判据仍归 `certify/push_gate.py`·双门并立）。
- 自测套件 48 例（44 过／0 红／4 SKIP）。

### v37 — 服务层：实时动态三器（2026-11-11·41e74b0）

**Added**

- `tools/unclog.py` — 疏通堵塞闭环引擎：probe 归集→chain_graph 链根（self
  washable 判·frozen8 红拒 fail-closed）→cure_applier 只正典包落刀→scan_v4
  复扫＋probe 复探（md5 咬合）→verdict unclogged／诚实墙 wall（逐根列因禁
  硬凑）／rounds-exhausted；缺省干跑；`--injector` canned 探针下 chain/cure/
  scan/frozen8 照旧真跑（真编排非傀儡）。
- `tools/wash_shape.py` — 洗形器·正典形五洗流水（词面洗/token 洗/头注形洗/
  行尾洗/锚形洗）：plan/apply 两段·plan 缺省零写盘·apply 后复跑五洗复核→
  shaped/partial 如实；冻结名册自动排除＋显式指认红拒。
- `tools/cw_sentinel.py` — 实时动态哨：三路信号源（CI 新红炉→ci_triage 判类／
  本地新堵账→chain_graph TOP／构建日志增量词面）→JSONL 事件流（append＋
  fsync＋stdout 镜像）·`--state-file` seen 幂等·缺省 report-only 零动作。
- 接口五纪律三器贯通：schema 钦名（rocqwash-unclog/1·rocqwash-shape/1·
  rocqwash-sentinel/1）·退出码 0/1/2/9（红是数据非器红）·`--once/--loop` 双模·
  `--injector`/`--sleep-scale` 离线可测·编排零新引擎（全 subprocess）。

**Changed**

- `cw.sh` 十五工具；README-cw.md 新增「工作流配合接口」节（五纪律速查＋
  三典型后台哨命令行＋pushci/unclog/wash_shape 三典型工作流嵌段）。
- 自测套件 51 例（47 过／0 红／4 SKIP）。

### v38 — 接驳与体检层（2026-11-11·c205ea0）

**Added**

- `tools/cw_doctor.py` — 综合体检器四域聚合：环境（dyld doctor）40／网络
  （net_probe）20／注册（order.txt 锚正典形审计）25／堵账（probe 抽样→
  chain_graph TOP）15→综合健康分 0-100＋verdict healthy/degraded＋advice 逐
  非绿域指向对应器；只诊断禁代执行；`--injector` 离线可测（缺键 9 绝不静默
  走真）。
- `tools/_http_backoff.py` — 韧性层公共件：403/429/5xx 指数退避（Retry-After
  秒数头尊重·4xx 语义面不重试）·ci_triage/cw_sentinel/pushci 三器共享；
  injector canned 路径一律零重试零真网络。
- `examples/workflows/` 三正典嵌段（backend-sentinel／step-pushci／
  loop-unclog·样例为 tmp 注入演练实跑所产非手写）＋
  [`docs/workflow-integration-whitepaper-v1.0-20261111.md`](docs/workflow-integration-whitepaper-v1.0-20261111.md)
  （五纪律／三嵌段／后台任务与主会话让路五机制／push_gate 推窗四判据×pushci
  发射闸双门并立）。

**Changed**

- cw_sentinel 增 `--on-red-preset`（预设 unclog＝干跑疏通／pushci＝dry-run·
  与 `--on-red` 同一执行器零新路径·两者互斥 rc=2·`--on-red-arg K=V` 透传）。
- unclog 增 `--audit` 只读堵账基线（零写盘硬保证＝`--src` 全文件 md5 跑前跑后
  自证恒同·与 `--apply`/`--loop` 互斥 rc=2·timing 段为唯一非确定段）。
- 防挂帽：pushci `--timeout`·cw_sentinel `--subproc-timeout`（缺省 120s·超时
  杀＋fail-loud 报调用名）；net_probe 增 `--jitter/--seed`（抖散重试风暴·
  固定 seed 确定性）。
- `cw.sh` 十六工具；自测套件 52 例（48 过／0 红／4 SKIP·基线回归改前改后同绿）。

### v39 — 语料滚扩波·文档收口（2026-11-11·caa3a28）

**Added**

- `tests/fixtures/header_map_v1.json` — 头注模板库 v1（preset
  campaign_set_diamond·Set 仓 20261110 正典五字段形蒸馏·占位 6 枚全带引据·
  身内容绝不合成·缺 evidence 拒载——「无据不铸」由代码执行；
  schema `rocqwash-header-map/1`）。
- `tools/doc_lint.py` — 文档←→实现一致性三查器：①cw.sh 四处工具表互检＋
  tools/ 通用入口对账 ②CASES vs tests/README.md vs README.md 计数三处对账
  ③doc 引用旗标逐枚对照各器 `--help` 实出；schema `rocqwash-doclint/1`·
  verdict consistent|drift（红是数据非器红·响亮 stdout）。
- `tests/test_relay_e2e.py` — cw_sentinel `--on-red-preset unclog` 端到端三判
  （事件触发／unclog 干跑 rc=0 零写盘／JSONL 同盘 report 路径）＋
  [`docs/ops-realtime-service-v1.0-20261111.md`](docs/ops-realtime-service-v1.0-20261111.md)
  运行手册（后台哨标准命令与 JSONL 使用／on-red 预设三式对照／真实树活跑
  规程 audit 基线→人审→apply 白名单／主会话让路配合）。

**Changed**

- `wash/cure_pack.json` v1.3→v1.4（24→25 式）：evidence-gated 扩容——三源
  勘察得候选 11 条，收 1 式（cure39_ifq_connective_qualify·引据 Set 仓洗波锚
  commit 9a51c74 diff 逐字 25 站）·拒 10 条逐条因（宁缺毋滥代码化）。
- wash_shape 增 `--header-map-preset NAME` 钦名模板接线（与 `--header-map`
  同槽互斥 rc=2·模板源探测次序 `--header-map` > preset > env）。
- `cw.sh` 十七→十九工具：doc-lint 路由＋netname-normalize/select-audit 两路由
  补齐（doc_lint 真仓初跑 drift=3 的主会话裁决＝补而非另册·六处同步）；
  doc_lint 复跑 consistent drift=0。
- 自测套件 54 例（50 过／0 红／4 SKIP）。

### v53 — 注释面规范化波：规范卡＋norm_lint＋入口面/四器英文化（2026-11-13·工作树未发版）

**Added**

- `docs/annotation-standard-v1.0-20261113.md` — 注释规范卡 v1.0：两段式头注
  （banner＋五字段 Purpose./Interface./Dependencies./Evidence./Exit-codes.
  逐字）＋禁词面四族＋双语过渡规则（翻译替换为正·原中文入 `.zh.md` 留档
  而非删除·代码标识符/CLI 旗标/JSON schema 字段/退出码语义零改动）＋
  error/warn 分级与检查器退出码口径（0/1/2/9）。
- `docs/jargon-to-standard-mapping-v1.md` — 黑话→标准表述对照表 v1（规范卡
  Appendix A·142 活跃词面＝核心 16 行＋JARGON v0.9/v1.1 基座承袭＋工具仓
  sweep 扩充＋短语级＋英语口语族·语境注记逐行·标识符豁免登记）。
- `tools/norm_lint.py` — 注释面规范化检查器 report-only 首形：`--tree`/`--file`
  扫 .py/.sh/.md 散文面·五查（头注形/黑话词面/CJK 残留/禁类/头注行数帽）·
  schema `rocqwash-norm-lint/1`·findings 是数据退出码不升级（0/1/2/9）·
  `--selftest` 六矢量·`*.zh.md` 与 `docs/zh/` 归档面免扫。
- `docs/zh/ci_triage-docstring.zh.md` 等 — 核心四器中文 docstring 原档留档
  （cw_sentinel/pushci/unclog/ci_triage·程序化逐字提取）＋`README-cw.zh.md`／
  `cli/rocqwash.zh.md` 双语过渡留档。

**Changed**

- 入口面英文化（翻译替换·接口零改动）：`cw.sh`／`cli/rocqwash`／`README-cw.md`
  头注/帮助面英文重写·标识符/旗标/退出码逐字未动；`tools/ci_triage.py`／
  `tools/pushci.py`／`tools/unclog.py`／`tools/cw_sentinel.py` 模块 docstring
  英文化（行内注释残留如实登记，为递归消减基线）。
- `cw.sh` 二十五工具：norm-lint 路由入册（六处同步）；README-cw.md 工具表
  增 norm-lint 行。
- `tools/doc_lint.py`：DEFAULT_HELP_CAP 24→25（norm_lint 入册后 25 器·帽溢出
  probe_engine 按 v38/v46 同 precedent 换代）；doc 面收集免扫 `*.zh.md` 与
  `docs/zh/` 归档面（规范卡 §5.2 归档件非正本面）。
- tests/：t_norm_lint 挂接（`tests/test_norm_lint.py` 最小自测壳三判）·
  自测套件 59→60 例；README.md/tests/README.md 计数行同步。

**Verification**

- norm_lint 全仓基线账（`--tree` 全仓·无白名单·现状如实）：files=140·
  error=2441·warn=1036·cjk_ratio=0.248597·同输入重跑字节恒同
  （`docs/norm-lint-baseline-20261113.{json,md}`）。
- doc_lint consistent（help_run=25/25·drift=0）；总套两遍绿（60 例 59 过
  0 红 1 略×2）；bash -n 全 sh 过；黑话终扫在册＝入口面叙述类词面清偿约
  26 处（wave/campaign/seat 叙述·日期戳·席名·叙述义 dispatch 改写），余量
  如实登记＝标识符引形类（cw.sh `dispatch` 路由名×5·README-cw.md 例命令/
  文档链接文件名日期×6·cli/rocqwash `retrofit` 子动词名×4）＋四器行内注释
  残留（jargon 2-14·cjk_ratio 0.11-0.19）。

### v58 — self-evolution guardrail wave: wash-map self-reference guard (2026-11-16)

**Fixed**

- `docs/jargon-to-standard-mapping-v1.md`: restored the 27 rows rewritten by the
  `e04f2f6` E2 jargon mechanical pass (收编→并入, 定谳→已证结论, 缝合→splice
  and 24 more). That pass rewrote the banned faces *themselves* inside the
  mapping table, which (a) dropped 11 of the 13 faces the seed contract says
  this table supplies (清盘/增薄/机判/摘牌/计功/缝合/双杀/环账/卸出/击坠/翻牌)
  and (b) wrote plain English standard terms into the face column of 10 rows,
  so `norm_lint`'s default map started treating delisted / machine ruling /
  cyclic account and 7 more ordinary English phrases as banned jargon. After
  the restore the file md5 is exactly the seed-pinned value
  `9440fbd102187e15e01183e853242e30` (the seed needs no edit), the contract
  faces are back 13/13, and every corrupted English face is gone from the
  loader.
- `tools/jargon_apply.py`: new **self-reference guard** — the wash map's own
  source table (`--a2-table`, default
  `docs/jargon-to-standard-mapping-v1.md`) is never a wash target. `--tree`
  excludes it from the target set; `--file` on it is refused rc=1 loud. This
  closes the recurrence vector: before the fix `--tree . --plan` still
  reported would_fix=28 on that table (the next autonomous round would have
  washed its own map source again); after the fix the table leaves the scan
  face (files 232→231, would_fix 73→45).

**Added**

- `tests/test_destructive_matrix.py`: destructive-surface matrix gains row J1
  ("wash-map self-reference guard": tree exclusion + file refusal, both paths
  zero-write). The matrix goes 22→23 rows.

**Verification**

- Full local suite: 72 pass / 5 red / 4 skip over 81 cases (before the fix:
  70 pass / 7 red). All 5 remaining reds are platform-dependent and sit in
  the CI Linux/Windows platform roster (t_cpu_guard_direct_smoke /
  t_cpu_guard_direct_rc / t_extract_magic / t_probe_engine /
  t_toolchain_dyld_doctor).
- `t_engines_body` 60/60 green and `t_engines_seeds` 42/42 green (both were
  red on the `jargon/snapshot-md5` drift).
- Destructive-surface matrix 23/23 green (new row J1 PASS).

### v59 — platform-reproducible CI wave: three independent red causes (2026-11-16)

CI was red on all three hosted platforms (runs #89/#90/#91) for three
independent reasons, none of them caused by the v58 wash-map fix.

**Fixed**

- `tools/bus_feeder.py`: the selftest located its scratch directory through
  `TMP` or `TEMP` only and exited 9 when neither was set. GitHub runners
  expose `RUNNER_TEMP`/`TMPDIR`, not `TMP`, so `t_bus_feeder_shape` failed on
  every POSIX runner while passing on Windows (where `TMP` always exists).
  The scratch root now falls back through TMP/TEMP/TMPDIR to
  `tempfile.gettempdir()`.
- `certify/frozen8.py`: selftest judgment 9 amends a scratch commit and
  expects the git-anchor ring to report drift. An amend landing inside the
  same commit-timestamp granularity as the original commit reproduces the
  identical SHA (same tree, same message, same author and committer second),
  so no drift is visible and the assertion fails on fast machines (observed on
  the Linux and Windows runners). The amended commit now carries a pinned
  author date, so the new SHA cannot collide with the original.
- `.gitattributes` (new): the Windows checkout is CRLF while every committed
  blob and every recorded md5 pin is LF, so the byte-level assertions never
  matched the committed bytes — fourteen cases red on the Windows lane
  (t_gate4_clean, t_wash_judgments, t_wash_engine, t_scan_station,
  t_verify_born, t_frozen8, t_frozen8_check, t_frozen_call, t_world_hook,
  t_select_audit, t_recipe_s07, t_recipe_pw1, t_precedent_station,
  t_netname_normalize). The checkout is now pinned to LF on every platform.
  Every blob in the repository is already LF, so there is no renormalization
  churn.

**Added**

- `.github/workflows/ci.yml`: a local self-hosted lane
  (`runs-on: [self-hosted, Windows, X64]`, runner LIVE-ROCQWASH on this
  machine) runs the same stable roster locally instead of on a hosted runner,
  so a long suite is not bound by the hosted runner's job duration wall and a
  flaky hosted runner cannot block the signal.

**Verification**

- CI-shaped reproduction (a fresh clone with the system `core.autocrlf=true`
  setting: the checkout is LF only because of the new `.gitattributes`): the
  local suite went from 60 pass / 17 red / 4 skip to 70 pass / 7 red / 4 skip.
  Six of the seven remaining reds are platform-dependent and already sit in
  the CI Linux/Windows platform roster; the seventh (`t_frozen8_check`) was
  caused by this wave's own edit to `certify/frozen8.py` and was closed by
  re-issuing the frozen roster through the tool's own `freeze` face
  (idempotent replay byte-identical, `frozen8 check` OK, 0 changed).

### v60 — Windows stdout-codepage wave: UTF-8 I/O forced on every lane (2026-11-16)

After v59 the macOS and Linux lanes were green, but both Windows lanes were
still red — the hosted one across 34 cases, the local self-hosted one across
5.

**Fixed**

- `.github/workflows/ci.yml`: Windows runners default to an ANSI stdout
  codepage (charmap on the hosted image, gbk on a zh-CN host). The suite
  prints Chinese prose and math symbols, so `print()` raised
  `UnicodeEncodeError` and took whole cases down with it — the hosted Windows
  lane lost 34 cases to it. Both jobs now set `PYTHONIOENCODING=utf-8` and
  `PYTHONUTF8=1`. Reproduced byte-identically before the fix
  (`PYTHONIOENCODING=gbk` raises `UnicodeEncodeError: 'gbk' codec can't
  encode character '\u2282' in position 59`, the same message the runner
  logged).
- `verify/erasure_classifier.py`: the selftest wrote its scratch file to the
  hardcoded POSIX path `/tmp/erasure_selftest_<pid>.mli`, which does not
  exist on a Windows runner. It now uses `tempfile.gettempdir()`.

### v61 — Windows lane closure wave: quoting, autocrlf and encoding (2026-11-16)

After v60 the macOS and Linux lanes were green and the hosted Windows lane
had dropped from 34 red cases to 2, with one more red on the local
self-hosted lane.

**Fixed**

- `wrapper/frozen_call.py`: the child was launched with `os.execv(argv[0],
  argv)`. On Windows `os.execv` rebuilds the command line by joining the argv
  with spaces and does not quote it, so an interpreter path containing a space
  (`C:\Program Files\Python313\python.exe`) was split and the child died on
  `argv[0]="C:\Program"` ("can't open file '...Files\Python313\python.exe'").
  The child is now spawned through the list form, which keeps the exit-code
  passthrough without the quoting hazard.
- `tools/registry_regen.py`: the CRLF-preservation vector of the selftest
  builds a scratch git repository whose base books carry CRLF and asserts the
  regenerated draft preserves it. On a Windows host whose git has
  `core.autocrlf=true` the CRLF base books are normalized to LF on commit, so
  the vector failed for a reason that has nothing to do with the tool. Every
  git call of the selftest now runs with an injected `core.autocrlf=false`
  (config injected into the environment, not written into the repository).
- `tests/run_tests.sh`: the suite entry point now exports `PYTHONIOENCODING`
  and `PYTHONUTF8` itself, so the UTF-8 guarantee holds for every caller and
  not only for the CI job environment.
- `tests/t_engines_body.py`: `base_env` forces the same two variables into
  every child it spawns, so a child that prints Chinese prose or math symbols
  cannot die with `UnicodeEncodeError` on an ANSI-codepage host.

### v62 — isolated-mode encoding wave: `-X utf8` reaches every child (2026-11-16)

**Fixed**

- The encoding guarantee from v60 did not reach the children: Python's
  isolated mode (`-I`) implies `-E`, which ignores every `PYTHON*`
  environment variable — so `PYTHONIOENCODING` and `PYTHONUTF8` were dropped
  exactly where they were needed, in the children that print Chinese prose or
  math symbols. The hosted Windows lane still raised
  `UnicodeEncodeError: 'charmap' codec ...` and the `norm_lint` selftest
  reported zero PASS lines.
- `-X utf8` is a command-line switch, so `-E` cannot discard it. Five test
  files already used that form (`t_bus_feeder_shape`, `t_periscope_shape`,
  `t_symbiosis_shape`, `t_uplink_shape`, `t_evolution_dashboard_shape`); this
  extends the same form to the remaining 29 isolated-mode call sites across
  18 files, so the whole repository now spawns children in UTF-8 mode. The two
  non-Python `-I` sites (the `ocamlc` include-directory flag in
  `verify/extract_magic_check.py` and `tools/_abl1_4b_compile.py`) are left
  untouched.

**Verification**

- CI run #95 on `b9dd1a7`: **success**. All four blocking lanes green —
  Self-test suite (macOS), (Linux), (Windows) and
  (Windows (local self-hosted), the runner LIVE-ROCQWASH on this machine).
  The two platform-sensitive roster watch jobs stay red by design (they run
  exactly the cases the blocking roster excludes, and the job carries
  `continue-on-error: true`).

### v63 — platform-sensitive roster wave: guard exit-code passthrough (2026-11-16)

The two platform-sensitive roster watch jobs stay red by design (they run
exactly the cases the blocking roster excludes). Two of their reds were real
defects rather than environment noise, and are closed here.

**Fixed**

- `tools/cpu_guard.sh`: the guard launched the wrapped command through
  `taskpolicy`, which is a macOS-only binary. On a Linux or Windows host the
  command is not found, so the shell reported 127 and the wrapped command's
  real exit code was swallowed — the probe's "the guard must pass the child's
  exit code through unchanged" judgment saw 127 where it expected 7. The
  guard now degrades in steps (taskpolicy → nice → direct exec); every step
  still passes the child's exit code through unchanged.
- `tools/toolchain_dyld_doctor.py`: the selftest injects a canned `otool`
  written as a POSIX shell script. A Windows host cannot execute it (chmod
  does not set the execute bit there), so the CLI vector failed for a reason
  that has nothing to do with the tool. The selftest now reports the honest
  skip (rc 111) on a non-POSIX host instead of a false red.
- `tests/test_toolchain_dyld_doctor.py`: the harness still judged that
  honest skip as a failure, because it only accepted rc=0 plus the pass
  marker. It now accepts rc 111 with a skip banner and exits 111 itself, so
  the suite records the case as SKIP (the suite's standing rc 111 contract)
  rather than red.

### v64 — destructive-matrix write-face judgment: git metadata out of scope (2026-11-16)

**Fixed**

- `tests/test_destructive_matrix.py`: the write-face judgment compared a full
  directory manifest, `.git` included. Git legitimately rewrites its own
  metadata (reflog, index, gc.log) when it resolves HEAD or refreshes the
  index, so on a runner whose git touches that metadata during the freeze the
  row read it as "the freeze wrote outside its write face" and went red
  (observed on the macOS lane; the judgment passed on every other platform and
  in every earlier run, which is what made it a flake rather than a defect).
  The manifest now skips the `.git` directory, so the row states what it
  means: the tool's own write face. The rows that guard git-object writes
  assert on the object store explicitly.

[Unreleased] 注：v35-v39 五波均落 2026-11-11·随仓库主线演进未单独发版；
下一波 v40（正典化巩固波）已排程（长跑矢量＋冻结面复核＋INDEX/README 全表
对齐＋push_gate 双门归一评估·见更新账 v39 段待办）。
