王小哥（rocqwash英文化线·tests断言普查席）

# i18n_output_strings_census.md — cross-file output-string census, six-module Englishization work stream (baseline HEAD 523e7d4)

Purpose: for the six translated items (`tools/cw_sentinel.py`, `tools/registry_audit.py`, `tools/pushci.py`, `tools/registry_fix.py`, `tools/red_dispatch.py`, `tools/baseline_diff.py`, HEAD = pre-translation Chinese versions), extract every Chinese-bearing runtime output string (print / log / write / argparse help / exception / assert message), then grep `tests/` and `docs/` tree-wide for reference sites of these Chinese substrings, producing the cross-file assertion and doc-reference list the merge agent needs. This agent wrote only this file; zero `.py`/`.sh` writes; zero writes to the real tree `D:/ComplexAnalysis/rocqwash`; zero push; zero network.

## 0. Zeroth-step record (three passes, as run)

1. **Skill `dynamic-workflows`**: not on this side's registered skill list (available-skill scan at session start: cw-ci-sop, cw-wf-route, coq-toy-replacement, cw-deep-mining, cw-paper-sop, cw-tail-supply + plugin skills; no dynamic-workflows). Per 「在册则载·缺席不停工」: registered-as-absent, work continued.
2. **Card library** `C:/Users/Live/.zcode/cli/memories/projects/attn-02af0b93b49c9dc1/memory/` — all three present, read in full: `rocqwash-repo-eval-20261112.md` (operative takeaways: Windows `python3` store-stub fake-red precedent, `tests/run_tests.sh:203` `PY=python3`; cards are not truth — tree governs and conflicts are named), `reporting-honesty-formats.md` (checks reported only as run; no silent denominator change; process-language boundary — internal engineering docs may use internal language), `workflow-ask-zeroth-step-law.md` (typed standards block; card-vs-reality conflicts named; zeroth step = skill + cards + techdocs).
3. **Techdocs**, all four read in full from this sandbox snapshot: `docs/annotation-standard-v1.0-20261113.md` (five fields `Purpose./Interface./Dependencies./Evidence./Exit-codes.`; §5.4 zero-change boundary), `docs/jargon-to-standard-mapping-v1.md` (per-word replacements + §6 identifier exemption register), `seeds/ai_flavor/word-map.json` (36 faces; em-dash quota), `seeds/jargon/jargon-map.json` (62-entry prefix cut).

Baseline report read first, as ordered: `D:/ComplexAnalysis/rqw_i18n_out_20261114/OUT/p0-gate-report.md` (its §6.2 vector-15 finding and §5.4 registry_audit assert-sync findings are re-confirmed independently by this census, see §3/§6).

## 1. Method (all commands run this session)

1. Sandbox clone: `git clone D:/ComplexAnalysis/rocqwash .../trees/lane6-tests-census/rocqwash && git checkout 523e7d4` → HEAD `523e7d49c3a7a68628f639d6dadae985d4559065`, `git status --porcelain` = 0 before work.
2. String extraction (zero file writes): inline `python -I -B -X utf8 -c` AST walk over the six modules; every `ast.Constant` str / f-string `JoinedStr` containing CJK recorded with syntactic context class (`print` / `log` / `write` / `raise` / `assert` / `argparse` / `call` / `compare` / `cond` / `stored-*`) and enclosing def. Result: **928 records** — 781 non-docstring (runtime pool) + 147 docstring records (docstrings are not runtime output; counted, excluded from the fragment pool).
3. Actual-English alignment: for the two modules already translated in the real tree's in-flight working copies (read-only access), all string constants aligned 1:1 by order with `difflib` (cw_sentinel 1391↔1391, registry_audit 819↔819, zero unaligned, zero gap mismatches) → every one of their 223 + 118 CJK records carries the **actual** translated English below (source label 「实测」). The other four modules are not yet translated in the real tree → their English is this agent's **suggestion** (label 「建议」, advisory per `docs/jargon-to-standard-mapping-v1.md`; merge agent must reconcile against the actual translated strings when those lanes land).
4. Reference-site grep: fragment pool = maximal CJK runs (≥2 chars) of the runtime pool; scanned 215 files under `tests/` + `docs/` (primary) and `examples/` + `tools/` + `verify/` (supplementary). Raw hits 6370; tier-attributed (A = fragment unique to one module 3159 / B = 2–3 modules 1021 / C = ≥4 modules 406) and kind-classified (ASSERT 231, SHELL 158, DOCBLOCK 46, DOC-PROSE 1050, ARCH 1017, OTHER 1684). Every ASSERT/SHELL/DOCBLOCK line and every line of the six dedicated test files was reviewed individually; a complementary scan enumerated all 231 `assert`-context lines with CJK in `tests/*.py` (coverage against fragments the pool could miss) and all CJK grep/expect-context lines in `tests/*.sh`.

## 2. Inventory summary (per module, HEAD 523e7d4)

| module | total CJK string consts | runtime pool (non-docstring) | docstrings | by class (all records; the `stored` bucket absorbs docstring records — they carry no call/raise/assert ancestors) |
|---|---|---|---|---|
| tools/cw_sentinel.py | 223 | 189 | 34 | assert 76·raise 64·stored 43·argparse 24·write 10·call 5·print 1 |
| tools/registry_audit.py | 118 | 95 | 23 | call 32·stored 41·print 14·argparse 12·assert 16·raise 3 |
| tools/pushci.py | 195 | 163 | 32 | raise 73·stored 36·argparse 22·assert 41·call 19·print 3·write 1 |
| tools/registry_fix.py | 138 | 117 | 21 | print 30·raise 33·stored 28·assert 26·call 12·argparse 9 |
| tools/red_dispatch.py | 129 | 114 | 15 | call 68·stored 27·raise 19·argparse 10·write 5 |
| tools/baseline_diff.py | 125 | 103 | 22 | call 25·stored 31·assert 29·print 17·raise 17·argparse 5·write 1 |

Class notes: `assert` = AssertionError message (output only on failure; still synced where it quotes output tokens); `stored`/`stored-coll`/`stored-assign` = string constants held in variables/dicts/tuples and emitted later (treated as runtime output for census purposes); `call` = argument to a non-print call, incl. evidence/plan-line builders and report templates. Parse-time facts observed (pre-existing, both unchanged by this agent): `SyntaxWarning: invalid escape sequence '\$'` at cw_sentinel.py:2134 and `'\.'` at one module line 3 — identical on baseline (p0-gate-report §5.5 already registered the former).

## 3. Cross-file TEST assertion sites (in scope — the merge agent's sync list)

Six sites in `tests/` assert on the six modules' Chinese output substrings. Everything else Chinese in the test files is the tests' own prose (docstrings / fail-messages / case names) and is NOT output-coupled — it breaks nothing when the modules' outputs change; it is the test files' own translation face, out of this census's sync list.

| # | test site | assertion | module string (file:line, class) | Chinese substring asserted | English to sync to (source) |
|---|---|---|---|---|---|
| T1 | tests/test_pushci.py:355 | `any("flat 注入形" in e for e in report.evidence)` (S1) | tools/pushci.py:821, call — evidence note `flat 注入形：preflight toolchain/net 双闸按缺省绿施（flat 形未携闸 canned·测试契约形·真发射闸走 steps 形或真模式）` | `flat 注入形` | 建议: `flat injection form` (full note: "flat injection form: preflight toolchain/net both gates apply default-green (canned carries no gates; test-contract form; the real preflight gate runs via steps form or real mode)") |
| T2 | tests/test_pushci.py:428 | `any("零 rerun" in e for e in report.evidence + last_triage.evidence)` (S3) | tools/pushci.py:1034, raise — `heal: family=A-content-red（内容红·禁代修——修复是席/人职责）·判类证据在册 stages.heal.last_triage.evidence·零 rerun` | `零 rerun` | 建议: `zero rerun` |
| T3 | tests/test_pushci.py:455 | `any("帽" in e for e in report.evidence)` (S4) | tools/pushci.py:1017, raise — `heal 帽达（--max-heal=%d·已 %d 轮）` | `帽` | 建议: `heal cap reached (--max-heal=%d, %d rounds used)`; test side must switch from the single char `帽` to a distinctive token, e.g. `any("cap reached" in e ...)` |
| T4 | tests/test_pushci.py:507 | `any("[1] preflight.gate4" in ln and "未启" in ln for ln in report.plan)` (S7) | tools/pushci.py:1181, call — plan line `[1] preflight.gate4: 未启（--pre-scan-gate4 未给）` | `未启` | 建议: `[1] preflight.gate4: not enabled (--pre-scan-gate4 not given)`; test side: `and "not enabled" in ln` |
| T5 | tests/test_destructive_matrix.py:487 | `any("禁代修" in e for e in rep["evidence"])` (row P2) | tools/pushci.py:1034, raise (same string as T2) | `禁代修` | 建议: `no auto-fix` (one canonical English for both T2/T5 from the same sentence, e.g. "heal: family=A-content-red (content red; no auto-fix — fixing is the maintainer's job); classification evidence recorded in stages.heal.last_triage.evidence; zero rerun") |
| T6 | tests/test_registry_fix_dedup.py:282 | `assert "同参纪律破" in out or "same-param" in out` | tools/registry_fix.py:221, raise — `同参纪律破：audit 输入面与执行器双册须逐字同（处方行号系绑定被审册面）——audit mode=%r inputs.order=%r inputs.project=%r；执行器 --order=%r --project=%r` | `同参纪律破` | 建议: `same-parameter discipline broken: ...` — **T6 needs no test edit** if the translation keeps the `same-param` prefix (the test already ORs the English fallback); keep that property |

Adjacent-scope note (same method, other lanes' tools — registered here because the scan surfaced them; NOT this work stream's six): test_registry_union.py:75 `"八判全过"` / :135 `"缺件"` / :136 `"不在全表"` / :215 `"干跑未写盘"` (registry_union output); test_destructive_matrix.py:630 `"须配 --out"` (registry_union); test_ledger_sync.py Chinese report column names `["状态"]["备注"]["行数"]` and value prefix `首行` (ledger_sync report schema — the report KEYS themselves are Chinese); test_wash_engine.py:101 `"嵌套括号感知"` / :108 `"写隔离"` (wash_engine stderr); test_gate6_born_wrapper.py `"用法 Usage"`/`"未知形参"`/`"目录缺失"`/`"gate6 正本缺失"`/`"baseline 文件缺失"`/`"不得同给"`/`"源树缺失"`/`"不合法"`/`"认证代源缺失"`/`"代际断言败"`/`"源断言行"`; test_extract_magic.py `"魔数行上下文"`/`"提取面红"`/`"未产出"`/`"先编后检"`/`"语句清单异常"`; test_verify_born.py `"判绿三路径必填"`/`"born 判绿例"`/`"裸形"`/`"原件直喂"`/`"归一化 rc=0"`/`"FAIL（md5 断言不符"`; test_scan_station.py:82 `"正本缺失"`. If those tools get their own translation lanes, their tests carry the same sync obligation.

## 4. Doc reference sites (canonical docs — in scope)

Verbatim output quotes found in canonical `docs/*.md` code blocks (DOCBLOCK class). Each is a doc-sync obligation: the quoted text must be updated to the module's post-translation English output.

| # | doc site | quotes | module string (file:line) | English to sync to (source) |
|---|---|---|---|---|
| D1 | docs/ops-realtime-service-v1.0-20261111.md:149 | `on-red 注记: cmd rc=9（旁路动作·不改哨退出码）` | tools/cw_sentinel.py:995 (write) | 实测: `on-red note: cmd rc=%d (side action; does not change the sentinel's exit code)` |
| D2 | docs/ops-sentinel-长驻手册-v1.0-20261112.md:334 | rotation diagram `FILE.1 → FILE.2（旧 FILE.2 覆盖弃·保留 2 代）→ FILE → FILE.1 → 新 FILE 空` — semantics quoted from the `--emit-max-bytes` help | tools/cw_sentinel.py:1285 (argparse help) | 实测: `event stream rotation cap (rotate before append when over the cap; .1/.2 keep two generations; seq continues across generations; must be given with --emit)` — the diagram may stay graphical, but its 保留 2 代 wording should match "keep two generations" |
| D3 | docs/验证-Main档案位实用化-20261112.md:132 | `PLAN [1] preflight.toolchain: python3 tools/toolchain_dyld_doctor.py（--worker 缺省探测·gate verdict=healthy）` | tools/pushci.py:1169 (call) | 建议: `PLAN [1] preflight.toolchain: python3 tools/toolchain_dyld_doctor.py (--worker default probe; gate verdict=healthy)` |
| D4 | docs/验证-Main档案位实用化-20261112.md:134 | `PLAN [1] preflight.gate4: 未启（--pre-scan-gate4 未给）` | tools/pushci.py:1181 | 建议: `PLAN [1] preflight.gate4: not enabled (--pre-scan-gate4 not given)` (must stay consistent with T4's chosen wording) |
| D5 | docs/验证-Main档案位实用化-20261112.md:135 | `PLAN [2] push: git -C <repo> -c http.version=HTTP/1.1 push origin main（重试 3 发×45s；三败且 remote host=github.com → ghproxy 换路 2 发）` | tools/pushci.py:1183 | 建议: preserve all tokens; Chinese glosses → English (e.g. "3 attempts x 45s backoff; after 3 failures with remote host=github.com, reroute via ghproxy, 2 attempts") |
| D6 | docs/验证-Main档案位实用化-20261112.md:136 | `PLAN [3] watch: GET /repos/<org/repo>/actions/runs?per_page=30（head_branch=main 且 head_sha=<pushed_sha>·间隔 150s·status-only（updated_at 冻结非僵尸判据·以 status 为准） 至 completed）` | tools/pushci.py:1189 | 建议: keep `GET /repos/...` verbatim; translate the parenthetical semantics |
| D7 | docs/验证-Main档案位实用化-20261112.md:137 | `PLAN [4] heal: python3 tools/ci_triage.py --repo <org/repo> --run <id>（帽 3）→ B/E→probe+rerun（403 幂等接受）·A→fix-content 停·C→toolchain 停·表外→人工` | tools/pushci.py:1193 | 建议: `（帽 3）` → `(cap 3)` etc.; `表外→人工` → `off-spectrum -> manual` |
| D8 | docs/验证-Main档案位实用化-20261112.md:138 | `PLAN [5] verdict: report schema rocqwash-pushci/1·退出码 0/1/2/9` | tools/pushci.py:1197 | 建议: keep `rocqwash-pushci/1` and `0/1/2/9` verbatim; `退出码` → `exit codes` |

Canonical docs whose hits are narrative prose only (no verbatim output quotes of the six modules): docs/CAPABILITY-INDEX.md (architecture diagram + per-tool invocation rows quoting flag lists — flag names are identifiers and stay; but see §6.5 for its data columns), docs/mcp.md, docs/ops-evolve-手册-v1.0-20261113.md, docs/service-layer-overview-v1.0-20261111.md, docs/workflow-integration-whitepaper-v1.0-20261111.md, docs/rocqwash-service-campaign-total-v1/v2, docs/ops-live-run-log-20261111.md, docs/评估-push_gate推窗四判据与pushcinormalize-20261111.md, docs/演练-哨事件消费-20261113.md, docs/判例-R3复发-route2tierAautomatic recovery-20261113.md, docs/复核-UNREC-14事件-20261112.md, docs/retro-triage-Main仓全史-20261112.md, docs/勘形-*.md, docs/perf-profile-v1.0-20261111.md, docs/roadmap-v43-plus-20261111.md, docs/periscope_sop.md, docs/push-gate-dual-door-assessment-v1.0-20261111.md, docs/clean-mode-manual-20261114.md, docs/vacgen_sop.md, docs/exp-ledger.jsonl. Their Chinese is the docs' own translation face (docs lane); their quoted sample outputs of OTHER tools (ci_triage evidence 红件 N/M：ids=[…], 在册族：…（判类序取先） at ops-realtime-service:92, ops-sentinel:207, backend-sentinel.md:97; chain_graph TOP 链根 notes; probe FAIL-LOUD/候选面/frozen 在册 blocks) become sync obligations in those tools' own lanes, not this one.

Archive files (exempt per annotation standard §5.2 — archives preserve the pre-translation original by design, no sync): docs/zh/** (incl. zh/cw_sentinel-docstring.zh.md, zh/pushci-docstring.zh.md, zh/architecture.md, ...) and any *.zh.md siblings. Aggregate hit counts recorded in the work digest; per-site listing deliberately omitted.

## 5. Same-file (in-module) assertion couplings

Selftest asserts inside a module that quote that module's own output strings — the translation agent must sync both sides in the same file (already done for the two translated modules; verified green by p0-gate-report §5.4 and re-confirmed here from the aligned working copies):

- tools/registry_audit.py: assert:895 `锚异` ↔ finding evidence wording → 实测 `differing anchors`; assert:906 `7 位` → 实测 `7 hex digits`; assert:909 `正典锚不得列病灶` → `canonical anchors must not be listed as findings`; assert:964 `只读违例：册/树字节漂移` → `read-only violation: book/tree bytes changed`; assert:966/968/977/978/1024/1031/1033/1035/1037/1040/1043 likewise all English in the translated copy (full list in the work align file).
- tools/pushci.py: assert:1741 `flat 注入形` ↔ evidence note :821 (T1); assert:1611 `禁代修` ↔ raise :1034 (T5); assert:1605/1610/1613 `零 rerun …` ↔ raise :1034 (T2). Selftest-internal — one file, one translation agent, but the T1/T2/T5 test-side syncs must use the SAME English.
- tools/baseline_diff.py: assert:696 `仍堵 persistent（2）·按链根键·墙账逐因对齐` ↔ md-report template call :366 — the selftest asserts the exact md heading the tool generates; template translation must keep both in step.
- tools/cw_sentinel.py: selftest vector-15 asserts :2113/2115/2116/2121 grep the supervisor script (cross-file — see §6.1); asserts :2104 `监督壳部署形脚本缺库` → 实测 `supervisor deployment script missing`, :2111 → `the deployment shape should start with a bash shebang`, :2123 → `supervisor shell key line missing`, :2127 → `the deployment shape forbids hardcoded absolute paths (path parameterization rule): /Users/ hit`.
- tools/registry_fix.py: the raise :221 同参纪律破 is also reached by the selftest's CLI probes; T6's dual-language assert is the guard.
- tools/red_dispatch.py: selftest banners/asserts (12 vectors) contain no output-text self-coupling beyond the PASS banner.

## 6. Supplementary register (beyond the ask's tests/+docs/ scope, flagged as such — merge-agent awareness)

### 6.1 examples/sentinel_supervisor.sh ↔ cw_sentinel selftest vector 15 (the #1 cross-file sync)

cw_sentinel's selftest greps four prose phrases against this script (HEAD assert lines :2113/:2115/:2116/:2121; p0-gate-report §6.2 statically confirmed the coupling). The script is NOT among the six translated files:

| HEAD Chinese token (script lines) | translated cw_sentinel greps for (实测) | script hit count at HEAD |
|---|---|---|
| 重启预算耗尽 (:34 comment, :81 echo) | `restart budget exhausted` | 2 |
| 退避 (:7,:18,:25,:49,:50,:73,:111) | `backoff` | 7 Chinese hits; English `backoff` ALREADY present 7× via identifiers (SUPERVISOR_BACKOFF_BASE / backoff var) |
| state 续接 (:20 comment, :72 echo) | `state continuation` | 3 Chinese hits; English phrase 0 |
| rc=2 用法错 (:106 echo) | `rc=2 usage error` | 1 Chinese hit; English phrase 0 |

Consequence (p0-confirmed, re-stated): once cw_sentinel.py's translation lands, vector 15 fails until `examples/sentinel_supervisor.sh` is translated with exactly these English phrases (or the lane order is reversed). The supervisor's own echo lines (:81 `[supervisor] 重启预算耗尽（帽 …）`, :111 `[supervisor] 退避 …s 后重启（rc=…）`, :72 `state 续接：…`) are runtime output of the script itself — its translation is its own lane's job, but the four phrase-level English tokens are contract.

### 6.2 examples/ quotes of the six modules' outputs (same sync obligation as §4, outside tests/+docs/)

- examples/workflows/step-pushci.md:40 `=== ROCQWASH PUSHCI（修复后推送 CI 一键流水线·v36 旗舰）===` ← pushci.py:1285 (print); :42–:48 the five PLAN lines ← pushci.py:1169/1181/1183/1189/1193/1197 (same strings as D3–D8).
- examples/workflows/backend-sentinel.md:97/:104/:105 sample events carry the note field `ts=off（--sleep-scale 0·确定性输出）` ← cw_sentinel.py:596 (stored-assign, event note) → 实测 `ts=off (--sleep-scale 0; deterministic output)`; :134/:138/:139 exit-code tables quote `--help`/docstring semantics (advisory sync).
- examples/baselines/README.md:50 `## 5. 对比（堵账增减报告）` heading family, :60 persistent 墙账逐因对齐 row, :61 链根归因 column note, :67 verdict 只认红账, :68–:69 exit-code lines ← baseline_diff.py md-report template :366/:369/:386/:393/:395/:397 (advisory English: e.g. :366 → `## still-blocked persistent (%d) · keyed by chain root · wall causes aligned`; :369 header `旧因/新因/变化/链根归因` → `old cause/new cause/change/chain-root attribution`; :397 → `- exit codes: 0=improved/stable, 1=degraded/incomparable (a failing result is data, not a tool failure; loud stdout), 2=malformed input, 9=missing path`).
- examples/README.md:66–71 prose describing the supervisor assertions (uses the four §6.1 tokens) — sync advisory.
- examples/workflows/loop-unclog.md quotes unclog/probe outputs — not the six.

### 6.3 Cross-module import couplings (blast radius)

- tools/registry_fix.py:144 `import registry_union as _ru` (键式/锚正典/重锚 engine, import-only) — registry_fix's runtime output can surface registry_union's Chinese exception texts (UsageError/MissingInput at registry_union.py:88/92/117/286/334). Translating registry_fix does NOT remove those texts; translating registry_union later changes registry_fix's observable output. The merge agent should treat registry_union's exception messages as part of registry_fix's effective output surface.
- tools/cw_sentinel.py:281 and tools/pushci.py:225 `import _http_backoff` — helper's selftest output is already English, zero CJK: no action.

### 6.4 Line-number citation register (drift on translation)

130 lines cite the six modules' internal `file.py:NNN` line numbers; docstring rearrangement (≤30-line five-field blocks) and any line reflow makes them stale. tests: test_destructive_matrix.py ×10 (e.g. :704 `"tools/pushci.py:1163-1164,1116"` as row-anchor metadata), test_relay_e2e.py ×9 (:12,:14,:28,:31,:42,:55,:107,:193,:197). Canonical docs: ops-sentinel-长驻手册 ×30, push-gate-dual-door ×14, ops-realtime-service ×12, ops-evolve-手册 ×9, 验证-Main档案位 ×9, workflow-integration-whitepaper ×9, 演练-哨事件消费 ×7, contrib-isolation-protocol ×3, 勘形-Main新内容预热 ×3, campaign-total-v2 ×4, 评估-push_gate ×5, campaign-total-v1 ×2, ops-live-run-log ×2, retro-triage ×2, roadmap ×1. These are prose anchors (behavior-neutral in tests), but the docs lane should re-point them post-work stream.

### 6.5 Data-surface couplings (not prose, register-only)

- docs/CAPABILITY-INDEX.md:34–49 carries per-file byte/line-count columns for all six modules (e.g. `registry_fix.py | 60,064 | 1,161` vs HEAD 75,956 B / 1,447 lines — already stale before this work stream); translation changes them again. INDEX refresh is its own lane; invocation rows (:94-95, :132-135, :189-192, :197-200, :205-208, :213-216) quote flag lists = identifiers, stay verbatim.
- docs/norm-lint-baseline-20261113.{md,json} (227+227 hits) is a machine-generated norm_lint report snapshot (jargon/CJK findings for the whole repo) — a regenerated artifact, not a hand-sync target; it must be re-cast after the work stream lands.

## 7. Protocol-token inventory (zero-drift reference)

Tokens that must survive translation byte-identical (all ASCII, all verified present in the aligned translated copies where available):

- Selftest PASS banners (asserted by tests via MARK constants): `CW-SENTINEL-SELFTEST PASS` (tests/test_cw_sentinel.py:30 ↔ cw_sentinel.py:2137), `REGISTRY-AUDIT-SELFTEST PASS` (test_registry_audit.py:33 ↔ registry_audit.py:1047), `PUSHCI-SELFTEST PASS` (test_pushci.py:608 ↔ pushci.py:2022), `REGISTRY-FIX-SELFTEST PASS` (test_registry_fix_anchor.py:54 ↔ registry_fix.py:1438), `RED-DISPATCH-SELFTEST PASS` (test_red_dispatch.py:35 ↔ red_dispatch.py:928), `BASELINE-DIFF-SELFTEST PASS` (test_baseline_diff.py:34 ↔ baseline_diff.py:737). Banner prose after the token translates (实测: both translated banners already carry English prose, token intact).
- Schema tokens: `rocqwash-sentinel/1`, `rocqwash-sentinel-event/1`, `rocqwash-sentinel-state/1`, `rocqwash-sentinel-injector/1`, `rocqwash-registry-audit/1`, `rocqwash-registry-fix/1`, `rocqwash-pushci/1`, `rocqwash-red-dispatch/1`, `rocqwash-red-dispatch-state/1`, `rocqwash-baseline-diff/1` (plus consumed `rocqwash-unclog/1`, `rocqwash-ci-triage/1`, `rocqwash-chain-graph/1`, `rocqwash-other/1`).
- Event kinds `ci-red`/`blocking`/`build-signal`/`sentinel-error`; verdict tokens `success`/`fix-content`/`toolchain`/`unstable`/`heal-exhausted`/`gate4-block`/`dry-run`; family tokens `A-content-red`/`B-netred`/`C-toolchain`; triage actions `rerun-after-stable-window`/`fix-content`; presets `report-only`/`suggest`/`auto`; verdict tokens of baseline_diff `improved`/`degraded`/`stable`/`incomparable`.
- Exit-code semantics 0/1/2/9 (semantics unchanged everywhere; only the descriptive prose translates, e.g. 用法错 → usage error, 输入形坏 → malformed input, 路径缺失 → missing path).

Zero-drift statement for THIS agent: the agent wrote zero `.py`/`.sh` bytes anywhere (only this census md inside the sandbox tree), so exit-code contract and protocol tokens cannot drift through this agent; §7 is recorded as the reference inventory for the merge agent's post-merge check.

## 8. Self-checks (all run this session)

1. `git -C <sandbox> rev-parse HEAD` → `523e7d49c3a7a68628f639d6dadae985d4559065`; `git status --porcelain | wc -l` = 0 pre-work; post-work shows only the new `tests/i18n_output_strings_census.md` (see below).
2. `python -I -B` py_compile over all six modules with bytecode redirected outside the repo → total=6 fail=0 (output below).
3. CJK counts: the six modules' CJK string-constant record counts are the census datum itself (928); the census md contains CJK by design (it quotes the Chinese substrings being censused) — the zero-CJK gate belongs to the translated runtime faces, which this agent does not write; registered in limitations.
4. Real tree `D:/ComplexAnalysis/rocqwash`: reads only (`git status`, working-copy reads for alignment); porcelain unchanged (7 M + 7 untracked, same set as p0-gate-report §1 recorded).

## 9. Coverage boundaries (honest)

- The fragment pool derives from string constants; output text assembled from pieces spanning constants, or from fixture-borne data, could in principle be missed. Mitigation run: the complementary scan enumerated every CJK-bearing assert-context line in all `tests/*.py` (231 lines, all reviewed) and every CJK grep/expect line in `tests/*.sh`; no additional in-scope coupling exists beyond §3's six sites.
- docs DOC-PROSE narrative hits (1050 lines) are registered in aggregate (§4 list), not enumerated per-site: they are the docs' own translation face, not output-string references.
- `run_tests.sh` / `tests/README.md` lines containing pool fragments are case-description prose and the wrappers' own echo text; the wrappers assert only rc values and English PASS banners (verified per-section).
- Suggestions labeled 「建议」 for pushci/registry_fix/red_dispatch/baseline_diff are advisory; the binding English is whatever the translation lanes actually produce (reconcile at merge). 实测-labeled strings for cw_sentinel/registry_audit are byte-exact from the in-flight translated working copies at read time (real-tree HEAD was 523e7d4 throughout; in-flight files may still change before integration — re-verify at merge).
- NETRED register: empty — zero network operations this session (offline ticket; no fetch, no LLM call).

## 10. Work artifacts (session scratch, outside the repo tree)

`trees/lane6-tests-census/_work/`: cjk_extract.jsonl (928 records), cjk_grep_hits.jsonl (6370), digest_*.txt ×6, merged_digest.txt, classified_digest.txt, compl_assert_scan.txt (231), align_cw_sentinel.json, align_registry_audit.json, plus the py_compile pycache dir. In-repo writes: exactly this file.
