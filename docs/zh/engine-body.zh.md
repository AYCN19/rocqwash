# 引擎本体能力条目（Engine Body Capability Entries · 中文镜像）

> 镜像注记：本文件是 [`docs/engine-body-capabilities.md`](../engine-body-capabilities.md) 的中文镜像（双语面惯例）。主文件为契约面正本（工单 GD-20261114-ENGMAX-01 第 8 道交付稿件）；两文件内容同源，条目字段一一对应，版本锚同快照 HEAD `523e7d4`（2026-11-14）。接线与 INDEX 转录归合流席（契约卷 §5）。本文件为稿件，零接线，不创建任何 `.py` 件，不修改任何既有文件。
>
> Mirror note: this file is the Chinese mirror of [`docs/engine-body-capabilities.md`](../engine-body-capabilities.md) (the bilingual-face convention). The primary file is the contract face (the lane 8 draft deliverable of work order GD-20261114-ENGMAX-01); the two files share one source with entry fields in one-to-one correspondence, and the version anchor is snapshot HEAD `523e7d4` (2026-11-14). Wiring and the INDEX transcription belong to the integration seat (contract volume section 5). This file is a draft with zero wiring: it creates no `.py` file and modifies no existing file.

## 0. 定位与读法（Positioning and How to Read）

本文件预先转录三引擎本体＋termbase 薄层的能力条目，条目形照 `docs/CAPABILITY-INDEX.md` §2 七字段（路径／用途 Purpose／调用形 Invocation／示例 Example／依赖 Imports／网络 Network face／SKIP 面），每条目增一行「状态 Status」为稿件自加行（照录行之外的单列增行声明，惯例同 INDEX §2）。所描述的引擎本体文件由同工单道 1 至道 6 交付、合流席落岸；每面标 `[live]` 指合流落岸后的树内状态，合流前快照树内这些文件尚未在场；合流席按契约卷 §5 验证线（`--help`／`--selftest` 活跑）逐条复验后方可转录进 INDEX §2。

示例行沿用仓内记载形 `python -I`；实际以调用环境解释器为准（本机勘定为 `py -I`，`python` 为商店 stub，见 `OUT/p0-baseline-report.md` §4）。器械族退出码契约 0／1／2／9（0=净或合法结果、1=命中或验证红、2=用法错、9=外部件缺席），逐道以契约卷 §2 钉面为准；命中是数据非错误。

## 1. 总表（Summary Table）

| 文件 | 引擎槽位 | CLI 面（简） | 退出码 | 网络面 | 依据 |
|---|---|---|---|---|---|
| tools/ai_flavor.py | E1 检测 | `--file` / `--tree` / `--selftest` / `--json` | 0 / 1 / 2 | zero | 契约卷 §2 道1 |
| tools/ai_flavor_apply.py | E1 施加 | `--emit-handoff` / `--apply-handoff` / `--apply` / `--state` | 0 / 1 / 2 | http 腿 default-deny | 道3 |
| tools/jargon_apply.py | E2 施加 | `--file` / `--tree` / `--plan` / `--apply` / `--guarded-interactive` / `--json` | 0 / 1 / 2（9=装载件不可读·loader 族） | zero | 道2 |
| tools/i18n_pipeline.py | E4 P0/P1/P3/P6 | `--manifest` / `--stage p0\|p1\|p3\|p6` / `--json` | 0 / 1 / 2 | zero | 道4 |
| tools/i18n_translate.py | E4 P2 | `--emit` / `--ingest` / `--prompts` | 0 / 1 / 2 | http 腿 default-deny | 道5 |
| tools/i18n_verify.py | E4 P4/P5 | `--emit-tenpoint` / `--ingest-tenpoint` | 0 / 1 / 2 | zero | 道6 |
| tools/termbase.py | E3 离线 | `--selftest` ＋ `lookup(term)` 纯函数 | 0 / 2（schema fail-loud） | 离线 zero | 道6 |

表注：INDEX §1 总表的 Bytes/Lines 计量列属普查时点事实；本稿描述落岸前契约面，落岸后由合流席随 INDEX 转录补记普查面。

## 2. 逐件条目（Per-Item Entries）

### tools/ai_flavor.py

- 状态 Status：[live]（工单道 1 交付件；E1 检测本体）
- 用途 Purpose：AI 味词面检测本体：36 词面电池（中文 3 族 10 面、英文词干 15、句式 8、段首 3）＋独立 em-dash 电池（U+2014 计数，目标 0），词表只读 `seeds/ai_flavor/word-map.json`（36 面 detector_regex_branch 逐字转录，禁改写正则字面）；命中是数据非错误（exit 1=有命中、0=净、2=用法错，承 shell 器械 exit 契约）；`--selftest` 出净/污染双探针（本件与词表数据件按数据豁免律自排除，em-dash 全域 0 不豁免）；输出 JSON 键英文（`schema:"rocqwash.ai-flavor.report/1"`、`file`、`batteries{}`、`em_dash_count`、`hits[{line,battery,face_id,before,after}]`，before/after 各 40 字符窗口）；纯函数导出 `detect_text(text, word_map) -> report_dict` 与 `load_word_map(path) -> dict` 供施加面与管线面 import。
- 调用形 Invocation：`python -I tools/ai_flavor.py --file <p> [--json <out>]` [live]；`python -I tools/ai_flavor.py --tree <dir> [--json <out>]`（*.py *.sh *.md *.json *.ts 五扩展）[live]；`python -I tools/ai_flavor.py --selftest` [live]
- 示例 Example：`python -I tools/ai_flavor.py --file docs/report.md --json out/ai-flavor-report.json`
- 依赖 Imports：Python 3 标准库（工单 stdlib-only 硬闸，零第三方 import）；词表经 stdlib json 只读装载。
- 网络 Network face：zero（词面与词表均为本地数据与本地文本读，E1 无任何网络 I/O）。
- SKIP 面：报告态先行，默认零写；exit 1 报命中清单而非错误；em-dash 目标 0 全域适用含本件自身；`--selftest` 的自排除仅覆盖词面电池（数据豁免律），不覆盖 em-dash。

### tools/ai_flavor_apply.py

- 状态 Status：[live]（工单道 3 交付件；E1 施加面）
- 用途 Purpose：AI 味施加面：全部写入建议性（advisory）＋`--apply` 门后，改写一律经「改写提供者」；三类处置照 candidate kinds：中文 10 面＝ban-remediation（无固定替代词，只标人工改述，永不上机改）、英文词干 15 面＝neutral-direct-form（explore/examine/important 三选一，语境选择交改写提供者）、句式/段首 11 面＝delete-or-restate；handoff 形（默认·零网络）：`--emit-handoff` 出段包（每行 `{finding_id, face_id, lang, before, candidates, instruction}`），外部模型席回填 `{finding_id, choice, after_text, model_id}` 后 `--apply-handoff` 校验（finding_id 全对上、choice 合法、model_id 非空，缺一拒收 fail-loud）＋结构守卫（分隔符计数不变、行级结构核，承 gate4_autofix 参考件）后写入；预算帽每目标文件每类一轮（`--state` 状态件）；改写后重跑检测，残留=0 方 GREEN；幂等（二次 apply 零 would-fix）；纯函数导出 `plan_suggestions(text, report) -> entries[]`、`emit_handoff(entries) -> str`、`ingest_handoff(text, handoff_rows) -> (new_text, applied[], rejected[])`。
- 调用形 Invocation：`python -I tools/ai_flavor_apply.py --file <p> --emit-handoff <out.jsonl>` [live]；`python -I tools/ai_flavor_apply.py --file <p> --apply-handoff <in.jsonl>` [live]；`--apply-handoff <in.jsonl>`（写入门）＋`--state <p>`（预算帽状态件；缺省落目标件旁）[live]
- 示例 Example：`python -I tools/ai_flavor_apply.py --file docs/report.md --emit-handoff out/handoff.jsonl --state out/state.json`
- 依赖 Imports：Python 3 标准库（stdlib-only 硬闸）；handoff 默认面零网络；可选 http 提供者腿的传输 import 在落岸时声明（契约面不钉具体模块名）。
- 网络 Network face：handoff 面 zero；http 提供者腿 non-zero·default-deny：环境门 `ROCQWASH_MCP_ALLOW_NET=1` ＋ `ROCQWASH_LLM_ENDPOINT`／`ROCQWASH_LLM_MODEL`／`ROCQWASH_LLM_KEY` 三缺一即响亮拒绝并命名缺项（OpenAI 兼容 chat/completions 形）；逐次调用写 NETRED ledger 行（URL/时间/verdict，失败含）。
- SKIP 面：中文 10 面永不机改（处置=human）；handoff ingest 拒收分支 fail-loud（拒收清单 `rejected[]` 如实回报）；无模型配置时 handoff 形仍全功能（执行智能体＝模型处）；http 腿无环境门时拒绝而非降级。

### tools/jargon_apply.py

- 状态 Status：[live]（工单道 2 交付件；E2 施加面＋纯函数库）
- 用途 Purpose：黑话到标准术施加面：数据只读 `seeds/jargon/jargon-map.json`（62 条映射）；硬规则承 jargon SPEC §3 逐条：只机改 `disposition:"replace"` 条目；`rewrite_or_delete` 永不机改（findings 列出，处置=human）；`note` 载义项分裂/语境守卫的行＝guarded，apply 前逐行处理钩子（`--guarded-interactive` 出逐行问询文件，默认拒改上报）；preserve 豁免走 exempt 机制（`;` 分隔正则、行作用域）；标识符位永不改写（反引号跨段遮蔽，承 loader 范式 `tools/norm_lint.py:154-189`）；默认 plan 零写并列 before/after 对，`--apply` 后自动重扫（残留=0 方可 exit 0）；幂等（二次 apply 零 would-fix）；纯函数导出 `load_map(path) -> dict`、`project_table(map) -> str`（JSON 到 pipe 表的行行相等投影器）、`plan_rewrites(text, map) -> entries[]`（零写）、`apply_rewrites(text, entries) -> (new_text, applied[])`。
- 调用形 Invocation：`python -I tools/jargon_apply.py --file <p> [--plan] [--json <out>]` [live]；`python -I tools/jargon_apply.py --tree <dir> [--plan] [--json <out>]` [live]；`--apply`（写入门）＋`--guarded-interactive <q>`（逐行问询文件）[live]
- 示例 Example：`python -I tools/jargon_apply.py --tree docs --plan --json out/jargon-plan.json`
- 依赖 Imports：Python 3 标准库（stdlib-only 硬闸）；映射数据经 stdlib json 只读装载。
- 网络 Network face：zero（映射与改写均为本地数据与本地文本编辑）。
- SKIP 面：默认零写；`rewrite_or_delete` 行处置=human；guarded 行默认拒改上报；重扫残留非零即 exit 非 0（验证红）；`standard_language` 单轨律照 jargon SPEC §6（标准列只出自单一轨道，跨轨行仅注记）。

### tools/i18n_pipeline.py

- 状态 Status：[live]（工单道 4 交付件；E4 编排本体 P0/P1/P3/P6）
- 用途 Purpose：zh↔en 双向四联动管线的编排本体：六操作签名不可变（承 `seeds/i18n/pipeline_stub.py` §10：segment_document／translate_segments／apply_linkages／verify_faces／tenpoint_review／sync_ledger_append），本道实现 P0/P1/P3/P6 并 import 道5/道6 模块组装 translate_segments／verify_faces／tenpoint_review；P0 政策预查：目标面 regime 表 `repo`／`paper`／`supplement` 三面（承 i18n SPEC §7 D/E 三轨分级的模块内常数 `P0_REGIMES`），评审敏感面默认 `disclosure_required:true`，`refusal:true` 的面拒绝即合法结果（exit 0，段账记 refusal 行），P0 注记行（`policy_precheck_ref`）先于任何翻译落段账；P1 分段器：保护名单（代码块/行内反引号/CLI 旗标/--形 token/标识符/数学/引文/路径/URL），段＝连续散文行区间，出段账行（SPEC §9 九键形，`source_span` 行号）；P3 四联动编排 L1（termbase 查词，道6）→L2（jargon_apply 投影＋plan，道2）→L3（CJK 零残留＋em-dash 密度每千字符 ≤1＋保护名单零漂移 diff）→L4（ai_flavor 检测，命中=finding 走道3 同款建议流），联动改写落同一段账（`annotation_site` 照实）；P6 段账：JSONL 追加式、English keys、行内禁过程叙事，闭合校验每机器段九键齐＋`annotation_site=="model"`＋`tenpoint_verdict` 非 PENDING 才准闭合。
- 调用形 Invocation：`python -I tools/i18n_pipeline.py --manifest <run.json> --stage p0|p1|p3|p6 [--json <out>]` [live]（分段执行，断点续跑）
- 示例 Example：`python -I tools/i18n_pipeline.py --manifest out/run.json --stage p1 --json out/segments.json`
- 依赖 Imports：Python 3 标准库（stdlib-only 硬闸）＋仓内道2/道5/道6 模块（jargon_apply／i18n_translate／i18n_verify 组装面）；manifest 与段账经 stdlib json。
- 网络 Network face：zero（本道自身零网络面；P2 的网络面全在道5 provider 内，不在本道）。
- SKIP 面：P0 refusal 是合法结果非故障（exit 0，段账有行）；闭合校验不满足即 fail-loud 拒绝闭合；P2 模型处不在本道（缺模型配置时 translate_segments 组装腿由道5 handoff 形承接）。

### tools/i18n_translate.py

- 状态 Status：[live]（工单道 5 交付件；E4 模型处层 P2）
- 用途 Purpose：模型处层（P2）：handoff 形（默认·零网络）：`--emit` 出段包（每行 segment_id／direction／source_text／protected_tokens／prompt_template_ref／instruction），外部模型席回填 `{segment_id, translated_text, model_id, prompt_template_ref, timestamp_utc}` 后 `--ingest` 九键校验（缺 model_id 或 annotation 缺失＝违规拒收 fail-loud）；http 形（可选·default-deny·环境门同道3 三变量）：OpenAI 兼容端点，逐段调用，逐段标注（model_id=端点模型名，`annotation_site="model"`），NETRED ledger 逐次含失败；prompt 模板 `--prompts <dir>`（缺省用内置模板常数，`prompt_template_ref:"prompts/zh2en-repo-v1"` 形命名）；纯函数导出 `build_handoff(segments, direction) -> rows`、`ingest_translations(segments, rows) -> (translated, ledger_rows[])`。
- 调用形 Invocation：`python -I tools/i18n_translate.py --emit <out.jsonl> [--prompts <dir>]` [live]；`python -I tools/i18n_translate.py --ingest <in.jsonl>` [live]；http 腿旗标面以落岸 usage 面为准（本稿转录契约面）[live]
- 示例 Example：`python -I tools/i18n_translate.py --emit out/segments-handoff.jsonl --prompts prompts/`
- 依赖 Imports：Python 3 标准库（stdlib-only 硬闸）；handoff 默认面零网络；http 腿传输 import 在落岸时声明。
- 网络 Network face：handoff 面 zero；http 腿 non-zero·default-deny（环境门 `ROCQWASH_MCP_ALLOW_NET=1` ＋ `ROCQWASH_LLM_ENDPOINT`／`ROCQWASH_LLM_MODEL`／`ROCQWASH_LLM_KEY` 三缺一响亮拒绝并命名缺项；NETRED ledger 行逐次含失败）。
- SKIP 面：全票唯一网络面＝http 提供者腿（default-deny），无环境门时拒绝而非降级；handoff 形零网络全功能（执行智能体＝模型处）；零标注机器段＝管线违规（九键校验拒收）。

### tools/i18n_verify.py

- 状态 Status：[live]（工单道 6 交付件；E4 P4 机械验证编排＋P5 十点单面）
- 用途 Purpose：P4 编排：子进程调 `tools/ai_flavor.py`／`tools/norm_lint.py --jargon-map`／`tools/doc_lint.py`，收集 rc 与报告，汇成验证矩阵 JSON（`schema:"rocqwash.i18n.verify/1"`）；P5 十点单面：`--emit-tenpoint <target>` 出审读表单（逐件逐点十行槽位，各带原文行引用位，按目标面形态取变体：.v 面用 i18n SPEC §6 原文十点，工具仓 py/sh/md 面按 annotation-standard 卡五字段变体）；`--ingest-tenpoint <verdicts.json>` 校验（逐件逐点 verdict∈{PASS,FAIL}＋行引用齐全，汇总 `ALL-PASS|N-FAIL|BLOCKED`）→写回段账 `tenpoint_verdict`；引擎不替人判。
- 调用形 Invocation：`python -I tools/i18n_verify.py --emit-tenpoint <target>` [live]；`python -I tools/i18n_verify.py --ingest-tenpoint <verdicts.json>` [live]；P4 编排面的旗标面以落岸 usage 面为准（本稿转录契约面）[live]
- 示例 Example：`python -I tools/i18n_verify.py --emit-tenpoint docs/report.en.md --json out/tenpoint-form.json`
- 依赖 Imports：Python 3 标准库（stdlib-only 硬闸；subprocess 用于本地子进程编排）；判词文件经 stdlib json。
- 网络 Network face：zero（子进程均为本地工具只读探跑）。
- SKIP 面：P5 十点单为人工门（引擎出表单与写回，不产 verdict）；子进程目标件缺席＝fail-loud；判词文件 schema＝契约卷 §3 `rocqwash.tenpoint.verdicts/1`（逐件 10 行，frame 三值）。

### tools/termbase.py

- 状态 Status：[live]（工单道 6 交付件；E3 离线查词薄层）
- 用途 Purpose：术语库只读薄层：`seeds/termbase/termbase.json` 只读（stdlib json，schema 校验 fail-loud）＋`lookup(term) -> entries` ＋`--selftest`；零网络（E3 联网接口与 DIY 条目通道不在本票，仍为 candidate，见 `seeds/termbase/net-interface-SPEC.md` 与 `seeds/termbase/diy-channel-SPEC.md`）。
- 调用形 Invocation：`python -I tools/termbase.py --selftest` [live]；纯函数 `lookup(term) -> entries` 供管线 L1 import [live]
- 示例 Example：`python -I tools/termbase.py --selftest`
- 依赖 Imports：Python 3 标准库（stdlib json；stdlib-only 硬闸）。
- 网络 Network face：离线 zero（本票内零 fetch；联网接口为 E3 candidate，default-deny，启用时每次 fetch 写 NETRED ledger 行含失败，照 ENGINES.md E3 条目）。
- SKIP 面：内置快照永不原位编辑（上游术语表为唯一维护点，同步义务随件）；DIY 条目只走 intake 四闸；无环境门时联网接口拒绝并点名 `ROCQWASH_MCP_ALLOW_NET`。

## 3. 语域自查（Register Self-Check）

本文件全件经器械 `ai_flavor_selfcheck.sh`（36 词面电池＋em-dash U+2014 电池；词表源＝术语表 §4.6/§5）自查，实测输出见下（收工时点）。

```
CH_3FAMILIES_10FACES lines=0
EN_WORD_STEMS_15FACES lines=0
EN_SENTENCE_8FACES lines=0
EN_PARA_INITIAL_3FACES lines=0
EM_DASH_U2014 count=0 (target 0)
TOTAL_WORDING_LINES=0
VERDICT CLEAN (36 faces = 0; em-dash = 0)
```

执行形 Execution：`sh ai_flavor_selfcheck.sh docs/zh/engine-body.zh.md`，exit 0（2026-11-14 本席活跑；器械副本＝工单包 `techdocs/ai_flavor_selfcheck.sh`）。

凭据词面自查（值形 grep 于本文件）：0 命中，全件无任何凭据值或凭据词面。

## 4. 边界（Boundaries）

- 本文件是稿件，零接线：`tools/` 下七件引擎本体由工单道 1 至道 6 交付、合流席落岸；本文件不创建任何 `.py` 件，不修改任何既有文件。
- 落岸登记义务：合流席按契约卷 §5 验证线复验后，将条目转录进 `docs/CAPABILITY-INDEX.md` §2（候选转在册），并同步 `docs/mcp.md` 能力表（MCP 注册稿见 [`docs/drafts/mcp-tool-specs-engine-body.md`](../drafts/mcp-tool-specs-engine-body.md)：三候选，tools/list 21→24）。
- stdlib-only 硬闸与零网络默认为本票替代性硬闸（全部新增 `.py` 件零编译面；唯 i18n http 提供者腿为 default-deny 显式例外）。
- 设计变更四处的登记归合流席，照契约卷 §4（E4 升格完整管线／E3 离线子集入票／E1·E2 stage 形与合流接线／E1 写入全经改写提供者）。
