# 审计卷 · tools/vacgen.py 专项审计（批次 3 · 补审席 G4）/ Audit Scroll: vacgen.py Specialized Audit (Batch 3)

> **审计单号 Audit ID**: audit-vacgen-20261116
> **审计对象 Subject**: `tools/vacgen.py`（2877 行·本仓最大单件·TOOL_VERSION 2.1.0）及配套面（两 selftest、refinery segment、run_tests.sh 接线、docs/vacgen_sop.md、tools/vacgen_env_note.md、tools/mcp_server.py vacgen_generate 接线、tools/taxonomy.json）
> **审计席位 Seat**: 批次 3 补审席 G4（只读审计·零改动：本卷是本次作业唯一落盘面）
> **方法 Method**: 逐行通读（vacgen.py 全文 2877 行）＋ 配套面全读 ＋ 实跑探针 14 组（selftest 三件、t_refinery 聚合、CLI rc/互斥/幂等/force/损坏 taxonomy/def 头门/voided 行/anchor drift/preflight 端到端/census 面闸/--report/--exp-draft）＋ grep 引用面扫描
> **判读语义 Verdict semantics**: 本卷全部发现系只读登记（candidate repair·候修），未对仓做任何修复；行号以 2026-11-16 实勘时点为准；severity 分级＝HIGH（守卫承诺落空/契约断裂）/ MEDIUM（检查面空转、口径分裂、fail-loud 形破损）/ LOW（死代码、措辞、指针漂移）。

---

## 〇、总判 Top Verdict

- 工具本体健康：三件 selftest 实跑全绿（t_vacgen_shape PASS 8 文件、t_vacgen_expectedred 3 pass/0 red、refinery vacgen segment 14 pass/0 fail），t_refinery 聚合 59 pass/0 fail；CLI 三模式主干契约（互斥、缺参 fail-loud、幂等 no-op、差异 FAIL-LOUD、--force 覆盖、census 面闸、voided 行 admission、anchor drift rc=1）实跑全部符合设计。
- 守卫面有一处 HIGH 缺口：SOP §2.5 勘误登记为「隐式 binder 引擎债唯一机检守卫」的 `tests/t_vacgen_envelope_shape.py` **文件不在盘**，run_tests.sh 只有函数体（:1039-1045）且名册未挂（:383-384）。
- 其余 5 项 MEDIUM、11 项 LOW 候修，见 §六总表。

---

## 一、面清单 Surface Inventory（实勘 2026-11-16）

### 1.1 CLI 面（main，vacgen.py:2790-2873）

| Mode（模式） | Flags | rc 语义 |
|---|---|---|
| cast（缺省） | `--in --out --toolchain --snapshot --audit-id --name --worktree --lake --guard --core --force`（v1 面 11）＋`--taxonomy --report --exp-draft`（v2 additive） | ok=0；checks red=1；fail-loud（parse/taxonomy/bare-limb/diff targets/写盘验证）=1；缺 `--in` =2 |
| preflight（--preflight-all） | `--census --root --cluster-table --report` | ok=0；缺 census/root=1；与 `--in` 互斥=1；census 面闸失配=1 |
| verify-anchors（--verify-anchors） | `--mathlib --taxonomy` | ok=0；drift=1；缺 `--mathlib` =1 |

v2 九 flags（--taxonomy/--preflight-all/--census/--root/--cluster-table/--report/--exp-draft/--verify-anchors/--mathlib）中，`--verify-anchors` 与 `--preflight-all` 同给时前者被静默吞没（见 L1）。

### 1.2 产物面（cast 八文件＋可选 JSON）

- 八文件（vacgen.py:2241-2243）：witness.lean / falsify_{full,point,tactics,noclassic,band}.lean / boundary.lean / gap_anchors.txt。
- 边界账双形（emit_boundary:1853-1858）：numeric（BOUNDARY_SEATS C-1..C-6，vacgen.py:1611-1676）/ shape-registration（B-R＋B-Sn，:1777-1850）。
- `--report` JSON schema（do_cast:2343-2378）：reportId/tool/in/taxonomy/l1/assumptions/coverage/cast/negativeFinding/experience/verdict{checks(17), ok, strength}。
- `--exp-draft` JSON（build_exp_draft:2456-2493）：draftId/tool/date/entries（todo 族坑条目＋正形条目）。
- preflight 产物 difficulty map（:2678-2701）：mapId/censusId/headPin/taxonomy/calibration/bandDefinitionBytes/files/aggregate/negativeFinding/generatedAt。

### 1.3 引擎层（L1-L4）

- L1 decomposer：lean_strip_comments/iter_code_lines（双实现注释剥离，:105-162）、scan_balanced/find_decl_end/find_top_colon（:165-224）、parse_binders/split_instance_binder（:493-545）、looks_like_type 族（:243-340）、collect_variable_commands（G1，:404-447）、relevant_scope_binders（R-1 v3，:360-401）、decompose_head（C4.2 前闸，:569-633）。
- L2 taxonomy-as-data：validate_row/load_table/load_taxonomy/resolve_taxonomy_path（:834-952，四优先链 flag > VACGEN_TAXONOMY env > tool-adjacent > builtin starter row）、classify_record（first-match＋hole 拦截＋requireVarBinding，:978-1015）。
- L3 scoring：tier_of/tier 阈 80/50（:1032-1040）、band_of（S/M/L，:1052-1057）、budget_minutes（:1060-1061）、negative_finding_block 四要素（:1064-1077）。
- L4 cast：Cast 类＋emit_witness/emit_refutation×5/emit_boundary×2/emit_gap_anchors（:1270-1956）、run_checks v1 十一检（:1965-2026）、run_checks_v2 六检（:2029-2079）、幂等（cast-epoch masking，:2284-2323）、strength_face/W6 电池（:1088-1167）。
- preflight：preflight_all（:2528-2741）、load_cluster_table/classify_cluster（stratify.py parity，:2498-2525）。
- verify-anchors：do_verify_anchors（:2744-2785）。

### 1.4 数据面与消费面

- `tools/taxonomy.json`（实勘 2 rows：ineq.real.const-lt-field-re / concl.real.const-lt-field-re-exists；anchorVerifiedAt 键缺省）。
- `tools/mcp_server.py:207-247` vacgen_generate（arg_map 11 参，见 M4）。
- `tests/run_tests.sh`：名册 :383-384（t_vacgen_shape / t_vacgen_expectedred）＋ t_refinery；函数 :1023-1045（含悬空的 t_vacgen_envelope_shape，见 H1）。
- `tests/refinery_segments/vacgen.py`（402 行·refinery 测试段·同名非副本·动态加载 tools/vacgen.py；14 checks）。
- 文档面：docs/vacgen_sop.md（判读规程正本＋§2.5 勘误）、tools/vacgen_env_note.md（部署常量注记）、docs/mcp.md:55、docs/en/vacgen.md、README 族、更新账.md。

---

## 二、死代码扫描 Dead Code

| # | 符号 | 位置 | 实勘证据 | 分级 |
|---|---|---|---|---|
| L4 | `PREMISE_INEQ_RE`、`CONST_ALT` | vacgen.py:266-272 | `grep -n "PREMISE_INEQ_RE\|CONST_ALT" tools/vacgen.py` 仅 4 命中：定义 2 行＋注释文字 3 处（:795/:822/:824，均为「v1 转录出处」说明），零代码引用。v2 数据化后解析走 resolve_numeric_boundary 的 `_top_level_char` 手工切分＋parse_const_fraction 自带正则 | LOW |
| L5 | `envelope_prefix_segments` | vacgen.py:699-704 | 主流程（do_cast/run_checks_v2/envelope_statement）零调用；唯一消费者是 tests/refinery_segments/vacgen.py:185/197/209（p25 三钉）。属测试专用导出面，非严格死码，但工具内无消费位且无注释声明该身份 | LOW |
| — | 其余全量 def 扫描 | 全文件 | 逐函数对消费位（do_cast/preflight/verify/main/run_checks 族/emit 族/测试段）核对，其余符号均有活引用，无未接产出 | — |

---

## 三、异常处理审计 Exception Handling

| # | 位点 | 行为实勘 | 分级 |
|---|---|---|---|
| M1 | `load_taxonomy` vacgen.py:926-927 | `json.load(fh)` 与文件 open 不在 TaxonomyError 封装内。实跑：`--taxonomy <损坏 JSON>` → rc=1 但是裸 `json.decoder.JSONDecodeError: Expecting value` traceback（探针 f），无 `FAIL-LOUD: taxonomy:` 标记行；main:2860-2864 与 do_cast:2103-2107 的 except 只接 TaxonomyError。同族 OSError（权限/占用）同裸逃。违反自declare契约「row admission fail-loud (rc=1, section 6.2)」的可 grep 标记形 | MEDIUM |
| L9 | `do_cast` vacgen.py:2087-2091 | `os.path.isfile` 检查后 open 的 TOCTOU 竞态窗：isfile 过、open 前被删则 OSError 裸逃（UnicodeDecodeError 已封装 :2093-2097）。概率极低，登记即可 | LOW |
| L8 | `classify_record` vacgen.py:995-998 | `except re.error: hit = False`：entry["rx"] 在 load_table:892 已 compile 成功，search 阶段 re.error 不可达，属防御死分支（若真发生则吞错静默 miss）。无害，登记 | LOW |
| — | 其余异常面 | 实跑核验健康：UnicodeDecodeError（fail-loud 行）、preflight per-file OSError/UnicodeDecodeError（计 UNPARSED 不中止，:2571-2577/:2652-2656）、cluster table（OSError/ValueError/re.error，:2546-2550）、do_verify_anchors OSError（:2766-2767）、refinery segment check 外科（:157-166 fail loud 列示） | — |

---

## 四、CLI 契约审计 CLI Contract

### 4.1 实跑探针台账（全部本次亲跑）

| 探针 | 命令形（节选） | 实测 rc | 实测输出 | 判读 |
|---|---|---|---|---|
| a 无参 | `py -B tools/vacgen.py` | 2 | `FAIL-LOUD: --in is required in cast mode` | 符合（usage=2） |
| b preflight 缺参 | `--preflight-all` | 1 | `FAIL-LOUD: --preflight-all requires --census ... (usage error, rc=1)` | 符合但自称 usage 却 rc=1（L2） |
| c 互斥 | `--preflight-all --in x --census c --root r` | 1 | `FAIL-LOUD: ... mutually exclusive with --in` | 符合 |
| d verify 缺 mathlib | `--verify-anchors` | 1 | `FAIL-LOUD: --verify-anchors requires --mathlib <root>` | 符合 |
| e 双模式同给 | `--verify-anchors --preflight-all` | 1 | 只出 preflight 缺参错，verify-anchors 零提示 | **L1：静默吞没** |
| f 损坏 taxonomy | `--in ok.lean --taxonomy <broken>` | 1 | 裸 JSONDecodeError traceback | **M1** |
| g def-only 头 | `--in <def foo ...>` | 1 | `non-theorem-declaration: head 'def foo' ... C4.2 front gate` | 符合（C4.2 闸活） |
| h 幂等 | 同参二跑 | 0/0 | `re-cast detected ... no-op (zero rewrite)` | 符合 |
| i 差异拒写 | 改盘上 witness.lean 后重跑 | 1 | `FAIL-LOUD: existing target files differ ... witness.lean` | 符合 |
| h4 force | 加 `--force` | 0 | `cast complete: 8 file(s) written` | 符合 |
| j report/exp-draft | `--report --exp-draft` | 0 | checks:17 ok:True strength.grade:full；exp entries:1（正形） | 符合（但注释面见 L6） |
| k preflight 端到端 | census+root 小树 | 0 | tierCounts C=1、difficulty map 落盘、ok=true | 符合（口径见 M3） |
| l census 面闸 | summary=2 vs list=1 | 1 | `FAIL-LOUD: census face mismatch` | 符合 |
| m voided admission | 1 坏行+1 好行 taxonomy | 0 | `rowsLoaded: 1 \| rowsVoided: 1`＋逐行错误 | 符合 |
| n anchor drift | 伪 mathlib root | 1 | `anchors checked: 2 \| drifted: 2` 逐行 DRIFT | 符合（措辞缺口 L3） |

### 4.2 契约缺口

| # | 发现 | 证据 | 分级 |
|---|---|---|---|
| M3 | **L3 覆盖分母跨模式口径分裂**：cast 分母＝records+conclusion+附加 degraded（:2181，单计）；preflight 分母＝file_total+file_todo＝r+2u+e（:2615/:2618，未识别面双计）。实勘：同一族 zeta 面 cast coverage=50%（1/2，探针 j），preflight 对 A.lean 报 0/6（探针 k）。difficulty map 的 coverageLowerPct/tier 与 cast 报告同面不同值，「lower bound」自称在 preflight 侧只是口径差而非更保守界 | vacgen.py:2181 vs :2615/:2618；探针 j/k | MEDIUM |
| M2 | **scanned_vs_declared_upper_bound 恒绿（检查面空转）**：fill_ledger 的 declared_sorry 与 scanned_sorry 是同一表达式两次求值（:2269-2270），run_checks:1988-1990 的 `scanned > declared` 恒 False，v1 十一检之一永远 PASS，真实「扫描面 sorry 超声明」缺陷不可检 | vacgen.py:2269-2270/:1988-1990 | MEDIUM |
| L1 | `--verify-anchors`＋`--preflight-all` 同给：preflight 分支（:2851-2865）先行 return，verify-anchors 被静默吞没 | vacgen.py:2851-2867；探针 e | LOW |
| L2 | usage 错误 rc 语义不一致：缺 `--in` → rc=2（:2868-2871）；缺 `--census/--root` → rc=1 且自称 "usage error, rc=1"（:2856-2858）。同族 sweep 段契约习惯 usage=rc2 | vacgen.py:2851-2871；探针 a/b | LOW |
| L3 | do_verify_anchors 输出「affected rows are voided per C3.3」但实现只打印报告，无任何 void 落盘动作（表静态，后续 cast 仍全量加载 drifted 行） | vacgen.py:2779-2783；探针 n | LOW |
| M4 | **MCP vacgen_generate 参数面缺 v2 九面**：arg_map 仅 11 参（mcp_server.py:213-225），无 --census/--root/--taxonomy/--cluster-table/--report/--exp-draft/--verify-anchors/--mathlib。实勘探针 b 坐实 `--preflight-all` 无 census/root 必 rc=1，故 MCP 侧 preflight_all=true 无任何传参途径，必败。docs/mcp.md:55 参数表与接线一致地缺（文档-接线一致但双双断）。候修须 additive（补 arg_map＋同步 docs/mcp.md），禁动现有签名（勿扰清单规则 1） | mcp_server.py:213-225；docs/mcp.md:55；探针 b | MEDIUM |

---

## 五、selftest 覆盖审计 Selftest Coverage

### 5.1 实跑结果（本次亲跑）

| 件 | 命令 | 结果 |
|---|---|---|
| t_vacgen_shape.py | `py -B tests/t_vacgen_shape.py` | PASS：four-account skeleton present（8 files）·rc=0 |
| t_vacgen_expectedred.py | `py -B tests/t_vacgen_expectedred.py` | 3 pass / 0 red·rc=0（Lean compile leg design-SKIP） |
| refinery_segments/vacgen.py | `py -B tests/refinery_segments/vacgen.py` | 14 pass / 0 fail（import-face＋p25×5＋w5×5＋w6×3） |
| t_refinery.py（聚合） | `py -B tests/t_refinery.py` | SUMMARY segments=6 passed=59 failed=0 skipped=0 |

### 5.2 守卫缺口

| # | 发现 | 证据 | 分级 |
|---|---|---|---|
| H1 | **t_vacgen_envelope_shape 三重缺口（known-debt 唯一机检守卫落空）**：(a) 文件 `tests/t_vacgen_envelope_shape.py` 不在盘（`find` 全仓 `*envelope*` 零命中）；(b) run_tests.sh:1039-1045 有函数体执行该路径，名册 CASES（:383-384）未挂，函数为悬空死代码；(c) docs/vacgen_sop.md:283-293（§2.5 勘误）声称该测试 landed 并为「登记引擎债的唯一机检守卫」（run_tests.sh:1041-1043 注释同）。后果：隐式 binder envelope 引擎债（SOP §2.5 在册未修）现处零机检状态；fixture B 的 known-debt 钉（`∧ Set (` 签名）缺位，若未来引擎修复将无红信号提示更新钉 | run_tests.sh:1039-1045/:383-384；vacgen_sop.md:283-293；find 实勘 | HIGH |
| M5 | **SOP §2.5 声称的 taxonomy geo 行不在盘**：勘误第 1 条（vacgen_sop.md:275-283）称 `tools/taxonomy.json` 已落「builtin starter row carried verbatim + geo.symmetric-set-premise row」。实勘 tools/taxonomy.json rows=2：`ineq.real.const-lt-field-re`＋`concl.real.const-lt-field-re-exists`（后者 SOP 未提，前者与 builtin 同 id 非「carried verbatim 之外新增」的表述形）。geo 行无、Mahler 族 L3 提升（0/5 → 1/5）路径现盘不可复现，SOP 勘误面与盘面失配且无日期勘误块 | vacgen_sop.md:275-283；taxonomy.json 实勘输出 | MEDIUM |

### 5.3 覆盖缺口清单（零测试面·候修排序参考）

1. `--preflight-all` 全模式零覆盖（census 加载/面一致性闸/band/tier/cluster-table/difficulty-map schema）；M3 口径分裂正处此无钉区。
2. `--verify-anchors` 全模式零覆盖（drift 闸、缺 --mathlib 用法错）；L3 措辞缺口无钉。
3. taxonomy admission 面零覆盖（voided 行计数、全无效 fail-loud、空表 builtin 回退、损坏 JSON 应有的 FAIL-LOUD 形）；M1 无钉。
4. C4.2 non-theorem-declaration 前闸零钉（def-only rc=1 marker 形）。
5. 幂等 no-op/差异 FAIL-LOUD/--force 路径零钉（实跑行为正确，但无回归守卫）。
6. usage rc=2 面与双模式互斥面零钉（L1/L2 无钉）。
7. `--exp-draft` schema 面零钉。
8. envelope 债钉（即 H1 文件本体）。

---

## 六、severity 分级候修总表 Candidate Repair Ledger

| Severity | # | 一句话 | 候修形（最小 diff 优先） |
|---|---|---|---|
| HIGH | H1 | envelope 债钉文件缺盘、函数悬空、名册未挂 | 落位 tests/t_vacgen_envelope_shape.py（fixture A 良形钉＋fixture B 债钉 `∧ Set (`）＋挂名册；或先在 run_tests.sh 函数处登记缺口 |
| MEDIUM | M1 | 损坏 taxonomy JSON 裸 traceback | load_taxonomy 内 `except (json.JSONDecodeError, OSError) as exc: raise TaxonomyError(...)` 封装；零 CLI 面变化 |
| MEDIUM | M2 | scanned_vs_declared 检查恒绿 | declared_sorry 改从 TODO-SEAT 声明注释计数，恢复两字段独立性（属 v1 检查面语义恢复，行为变更须登记） |
| MEDIUM | M3 | cast/preflight 覆盖分母口径分裂 | preflight 改 `total_all = file_total + extras` 对齐，或 difficulty map 字段改名区分口径（行为变更须登记） |
| MEDIUM | M4 | MCP arg_map 缺 v2 九面（preflight_all 经 MCP 必败） | additive 补 arg_map 九条＋schema 九字段＋同步 docs/mcp.md 表；勿动现有签名（mcp 勿扰规则） |
| MEDIUM | M5 | SOP §2.5 geo 行登记与盘面失配 | SOP §2.5 加日期勘误块登记现状，或 taxonomy.json additive 落 geo 行（taxonomy-as-data 正形） |
| LOW | L1 | verify-anchors 被 preflight 静默吞没 | preflight 分支加互斥 FAIL-LOUD（additive） |
| LOW | L2 | usage rc 语义不一致（2 vs 1） | 统一 usage=rc2 或登记例外 |
| LOW | L3 | verify-anchors「voided」措辞无动作 | 措辞改 REPORTED 或 --report 落 drift 名单（additive） |
| LOW | L4 | PREMISE_INEQ_RE/CONST_ALT 死代码 | 删除或加 v1 provenance 注释标记（:795/:822/:824 文字引用同步改注） |
| LOW | L5 | envelope_prefix_segments 工具内零消费 | 加「exported for refinery segment test face」注释（保留，segment 依赖它） |
| LOW | L6 | 注释「v1 eleven + v2 five」实为 6 检（实测 checks:17） | vacgen.py:2325 注释改 six（一词 diff） |
| LOW | L7 | env_note 行号指针漂移（:67/:68/:70/:66-72/:784-795/:789 全失效；实位 82-88/898-909/903） | 行号更新或改符号名指针（防再漂） |
| LOW | L8 | classify_record 的 except re.error 不可达死分支 | 可留（防御无害）或删，登记即可 |
| LOW | L9 | do_cast --in open 的 TOCTOU 竞态窗 | open 包 try OSError → FAIL-LOUD 行 |
| LOW | L10 | `--exp-draft` 输出措辞 "entrie(s)"（:2446） | 一词 diff 改 entry/entries |
| LOW | L11 | preflight band M/L 空档打印 tiers=None（:2719-2723） | 空档打印零值字典（cosmetic） |

观察项（登记不修）：preflight `s1_names` 跨声明共享使 requireVarBinding 检查比 cast 模式宽（:2596-2597，fail-open 方向）；内嵌扫描无 Lean 字符串态机（字符串字面量内 `sorry`/`--` 会误读，属词面 lower bound 的 declared honest boundary 内）；SOP §2.5 引 `vacgen.py:640-650` 标注 2.0.1 revision 现位 681-696（历史注记）。

---

## 七、实跑台账 Provenance（全部本次亲跑·2026-11-16）

```
py -B -c "import sys; print(sys.version)"                  -> 3.12.5
py -B tests/t_vacgen_shape.py                              -> PASS (8 files) rc=0
py -B tests/t_vacgen_expectedred.py                        -> 3 pass / 0 red rc=0
py -B tests/refinery_segments/vacgen.py                    -> 14 pass / 0 fail rc=0
py -B tests/t_refinery.py                                  -> 59 pass / 0 fail rc=0
py -B tools/vacgen.py                                      -> rc=2 (usage)
py -B tools/vacgen.py --preflight-all                      -> rc=1 (usage error rc=1)
py -B tools/vacgen.py --preflight-all --in x --census c --root r -> rc=1 (mutual excl)
py -B tools/vacgen.py --verify-anchors                     -> rc=1 (requires --mathlib)
py -B tools/vacgen.py --verify-anchors --preflight-all     -> rc=1 (verify swallowed, L1)
py -B tools/vacgen.py --in ok.lean --taxonomy <broken>     -> rc=1 裸 JSONDecodeError (M1)
py -B tools/vacgen.py --in <def-only>                      -> rc=1 non-theorem-declaration
py -B tools/vacgen.py cast×2 / diff / --force              -> no-op / FAIL-LOUD / overwrite 全符合
py -B tools/vacgen.py --in --out --report --exp-draft      -> checks:17 ok:True grade:full; 1 entry
py -B tools/vacgen.py --preflight-all --census --root --report -> rc=0 C=1, 0/6 (M3)
py -B tools/vacgen.py --preflight-all <census mismatch>    -> rc=1 face mismatch
py -B tools/vacgen.py --in --taxonomy <1坏1好>              -> rc=0, loaded 1 voided 1
py -B tools/vacgen.py --verify-anchors --mathlib <伪root>   -> rc=1 drifted 2 (L3 措辞)
find /d/ComplexAnalysis/rocqwash -name "*envelope*"        -> 零命中 (H1)
grep -n "PREMISE_INEQ_RE|CONST_ALT" tools/vacgen.py        -> 定义 2 行+注释 3 处 (L4)
grep -n "envelope_prefix_segments" ...                     -> 工具内 0 消费位 (L5)
```

*本卷零改动声明：以上全部为只读实勘与临时目录探针；仓内唯一落盘面即本卷。行号口径 2026-11-16 实勘。*
