# verify_gate6 中文原面留档（archive）

- 源文件：`verify/verify_gate6.py`（英化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 prose 全文移此留档而非删除；英文正本见
  `verify/verify_gate6.py`。本文件为历史存档（annotation-standard-v1.0 §5.2），内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。
- 覆盖面：模块 docstring（ast 逐字提取）＋全部含中文行的注释/输出字面（按行号）
---


## 模块 docstring（ast 逐字提取）

```
verify_gate6.py — gate6 census 薄包装＋EntropyUnsatMark 判例器化（rocqwash verify/·
20261101 席 rqsupport）

五课反馈轮打磨件③（gate6 ch1 课工具化）。定位承仓内双层分工：
  - `wrapper/gate6_census.sh`（rqadapt 轮·guard 接线启动层）＝正典启动面——**判据零复制**，
    census/gate 红绿唯一出处仍是仓外正本 `ConstructiveWorld-Set/scripts/gates/
    gate6_statement_census.py`（在其仓只读禁改）；
  - 本件＝verify/ 逐件绿判入口面（verify_vo.py 同款形）：①**薄调**正本（subprocess
    `python3 -B`·rc 1:1 透传·零判据复制）；②**EntropyUnsatMark 判例器化**——把
    seat_eum 判例（语句面裸 Prop 量词 ch1 治理）机械化成可复用判读。

判例源（只读已核在盘）：`sandbox/seat_eum/账/gate6_report_before.json`（EntropyUnsatMark.v
ch1=1·L135 Theorem eum_EntropyDiffReal_section_vacuous·语句面 `forall (Omega_A : forall
(E_A : Real), …)` 嵌套裸 Prop 量词）→ `gate6_report_after.json`（ch1=0·**statement_names
5=5 零漂移**·ch2/ch3 恒 0）。判例语义（EUM-VERDICT）：
  治必降      ch1 总量 after < before，或两侧恒 0；ch1 反升＝红（R15 存量冻结只罚增长同律）
  治不摇名    逐文件 statement names 有序全等 before→after（签名稳定律）；名单漂移＝红
  旁道零涨    ch2/ch3 零增长；after 新现文件（before 无）各通道须全零（born-clean）
  退役不罚    before 有 after 无的文件＝INFO 不计红（存量退役合法·正本 gate 同律）

用法：
  # ① 薄调正本（形参 1:1 对齐正本 argparse·rc 透传）：
  python3 verify/verify_gate6.py --tree <.v 树目录> [--json o] [--text]
                                 [--gate --baseline B] [--baseline-out O]
                                 [--script <gate6.py>]
  # ② 判例器化（对两份 census JSON 报告机械判读）：
  python3 verify/verify_gate6.py --judge-before before.json --judge-after after.json
                                 [--judge-json out.json]
  # ③ 自证：
  python3 verify/verify_gate6.py --selftest

退出码：0=判例绿/正本 census 报告或闸绿透传；1=判例红/正本闸红透传；2=用法或报告畸形；
        9=路径缺失（正本/--tree/--judge-* 文件——fail-loud 不模拟）。
零网络零编译：正本为纯静态词面扫描（其头注自述），本件 subprocess 亦零编译；
不内建 guard 接线（启动面归 wrapper/gate6_census.sh·调用者按需套温控）。
```

## 全部含中文行（逐字·原行号）

L3: """verify_gate6.py — gate6 census 薄包装＋EntropyUnsatMark 判例器化（rocqwash verify/·
L4: 20261101 席 rqsupport）
L6: 五课反馈轮打磨件③（gate6 ch1 课工具化）。定位承仓内双层分工：
L7:   - `wrapper/gate6_census.sh`（rqadapt 轮·guard 接线启动层）＝正典启动面——**判据零复制**，
L8:     census/gate 红绿唯一出处仍是仓外正本 `ConstructiveWorld-Set/scripts/gates/
L9:     gate6_statement_census.py`（在其仓只读禁改）；
L10:   - 本件＝verify/ 逐件绿判入口面（verify_vo.py 同款形）：①**薄调**正本（subprocess
L11:     `python3 -B`·rc 1:1 透传·零判据复制）；②**EntropyUnsatMark 判例器化**——把
L12:     seat_eum 判例（语句面裸 Prop 量词 ch1 治理）机械化成可复用判读。
L14: 判例源（只读已核在盘）：`sandbox/seat_eum/账/gate6_report_before.json`（EntropyUnsatMark.v
L15: ch1=1·L135 Theorem eum_EntropyDiffReal_section_vacuous·语句面 `forall (Omega_A : forall
L16: (E_A : Real), …)` 嵌套裸 Prop 量词）→ `gate6_report_after.json`（ch1=0·**statement_names
L17: 5=5 零漂移**·ch2/ch3 恒 0）。判例语义（EUM-VERDICT）：
L18:   治必降      ch1 总量 after < before，或两侧恒 0；ch1 反升＝红（R15 存量冻结只罚增长同律）
L19:   治不摇名    逐文件 statement names 有序全等 before→after（签名稳定律）；名单漂移＝红
L20:   旁道零涨    ch2/ch3 零增长；after 新现文件（before 无）各通道须全零（born-clean）
L21:   退役不罚    before 有 after 无的文件＝INFO 不计红（存量退役合法·正本 gate 同律）
L23: 用法：
L24:   # ① 薄调正本（形参 1:1 对齐正本 argparse·rc 透传）：
L25:   python3 verify/verify_gate6.py --tree <.v 树目录> [--json o] [--text]
L28:   # ② 判例器化（对两份 census JSON 报告机械判读）：
L31:   # ③ 自证：
L34: 退出码：0=判例绿/正本 census 报告或闸绿透传；1=判例红/正本闸红透传；2=用法或报告畸形；
L35:         9=路径缺失（正本/--tree/--judge-* 文件——fail-loud 不模拟）。
L36: 零网络零编译：正本为纯静态词面扫描（其头注自述），本件 subprocess 亦零编译；
L37: 不内建 guard 接线（启动面归 wrapper/gate6_census.sh·调用者按需套温控）。
L52: # 判例器（EUM-VERDICT）
L56:     """读 census JSON 报告并做形校（正本 reports 形）。畸形＝JudgeError。"""
L58:         raise MissingPath("报告文件缺失: %s" % path)
L63:         raise JudgeError("报告 JSON 解析失败 %s: %s" % (path, e))
L65:         raise JudgeError("报告须 {\"files\": {…}} 形: %s" % path)
L68:             raise JudgeError("报告 files[%s] 须对象: %s" % (fname, path))
L71:                 raise JudgeError("报告 files[%s] 缺 %s 键: %s" % (fname, k, path))
L76:     """EntropyUnsatMark 判例四判。返回 (ok, rows)。
L78:     rows 每项 dict(judge/ok/detail)；judge ∈ 治必降/治不摇名/旁道零涨/退役不罚。
L86:     # 判一 治必降（ch1）
L89:     rows.append({"judge": "治必降", "ok": ok1,
L90:                  "detail": "ch1 before=%d after=%d（须降或两侧恒零）" % (b1, a1)})
L91:     # 判二 治不摇名（逐文件 names 有序全等·只在「存活文件」上判——
L92:     #   整文件退役随件带名属退役不罚面，不算漂移；新现文件的语句名属正常增长面）
L101:     rows.append({"judge": "治不摇名", "ok": ok2,
L102:                  "detail": "names 存活文件 before=%d after=%d 漂移文件=%s（须有序全等·总量恒等）"
L103:                            % (nb, na, drift or "无")})
L104:     # 判三 旁道零涨（ch2/ch3）＋新现文件 born-clean
L113:                 grows.append("新现文件 %s %s=%d（born-clean 须全零）" % (f, ch, len(af[f][ch])))
L114:     rows.append({"judge": "旁道零涨", "ok": not grows,
L115:                  "detail": "；".join(grows) if grows else "ch2/ch3 零增长·新现文件全零"})
L116:     # 判四 退役不罚（INFO）
L118:     rows.append({"judge": "退役不罚", "ok": True,
L119:                  "detail": ("退役文件=%s（INFO·不计红）" % gone) if gone else "无退役"})
L120:     return all(r["ok"] for r in rows if r["judge"] != "退役不罚"), rows
L132: # 薄调正本
L136:     """subprocess python3 -B 正本·rc 1:1 透传（零判据复制）。"""
L138:         print("FAIL-LOUD: gate6 正本缺失: %s (可用 --script/GATE6_SCRIPT 覆写)" % script,
L147: # 自证（判例向量用 seat_eum 实测报告形·wrapper 用夹具脚本·零真仓写）
L159:     """seat_eum 报告形夹具（EntropyUnsatMark.v·ch1 按 before/after 给）。"""
L168:     """内嵌向量组：eum before/after 判例绿·ch1 未降红·名漂移红·旁道涨红·新现文件
L169:     红/绿·退役 INFO·报告畸形 2·缺件 9·正本缺失 9·透传 rc 双判（夹具脚本零真仓）。"""
L190:         # ① eum 判例正判：before(ch1=1)→after(ch1=0·names 5=5) → GREEN rc 0
L193:         assert p.returncode == 0, "eum 判例应绿 rc=0 实测 %d\n%s" % (p.returncode, p.stdout)
L194:         assert "EUM-VERDICT-GREEN" in p.stdout and "治必降" in p.stdout, p.stdout
L196:         # ② ch1 未降负判（before=after·存量冻结只罚增长与滞治）→ RED rc 1
L198:         assert p.returncode == 1 and "治必降" in p.stdout, p.stdout
L200:         # ③ 名漂移负判（names 改序）→ RED rc 1·治不摇名
L205:         assert p.returncode == 1 and "治不摇名" in p.stdout, p.stdout
L207:         # ④ 旁道涨负判（ch2 出现）→ RED rc 1·旁道零涨
L213:         assert p.returncode == 1 and "旁道零涨" in p.stdout, p.stdout
L215:         # ⑤ 新现文件：带 ch1 → 红；全零 → 绿（born-clean 同律）
L222:         assert p.returncode == 1 and "新现文件" in p.stdout, p.stdout
L227:         assert p.returncode == 0, "新现文件全零应绿 rc=0 实测 %d\n%s" % (p.returncode, p.stdout)
L229:         # ⑥ 退役 INFO 不罚：after 少一文件 → 仍绿（判四 INFO 行在账）
L234:         assert p.returncode == 0 and "退役不罚" in p.stdout, p.stdout
L236:         # ⑦ 报告畸形 → rc 2；judge 文件缺失 → rc 9
L241:         assert p.returncode == 2, "报告畸形应 rc=2 实测 %d" % p.returncode
L243:         assert p.returncode == 9, "judge 缺件应 rc=9 实测 %d" % p.returncode
L245:         # ⑧ 薄调正本：缺 --tree → 2；tree 缺失 → 9；正本缺失 → 9（fail-loud 先于运行）
L247:         assert p.returncode == 2, "缺 --tree 应 rc=2 实测 %d" % p.returncode
L249:         assert p.returncode == 9, "tree 缺失应 rc=9 实测 %d" % p.returncode
L252:         assert p.returncode == 9 and "正本缺失" in p.stdout, p.stdout
L254:         # ⑨ 透传 rc 双判（夹具脚本替身·零真仓零真 census）
L266:         print("VERIFY-GATE6-SELFTEST PASS: eum判例绿/ch1未降红/名漂移红/旁道涨红/"
L267:               "新现文件红绿/退役INFO/畸形2/缺件9/正本缺9/透传rc双判 十判全过")
L278:         prog=PROG, description="gate6 census 薄包装＋EntropyUnsatMark 判例器化")
L279:     ap.add_argument("--tree", default=None, help="被普查 .v 树目录（薄调形）")
L280:     ap.add_argument("--json", dest="json_out", default=None, help="1:1 透传正本")
L281:     ap.add_argument("--text", action="store_true", help="1:1 透传正本")
L282:     ap.add_argument("--gate", action="store_true", help="1:1 透传正本")
L283:     ap.add_argument("--baseline", default=None, help="1:1 透传正本")
L284:     ap.add_argument("--baseline-out", dest="baseline_out", default=None, help="1:1 透传正本")
L286:                     help="gate6 正本路径（缺省 ConstructiveWorld-Set 正典路径）")
L287:     ap.add_argument("--judge-before", default=None, help="census 报告 before（判例形）")
L288:     ap.add_argument("--judge-after", default=None, help="census 报告 after（判例形）")
L289:     ap.add_argument("--judge-json", default=None, help="判读账 JSON 出账路径")
L297:     # —— 判例形 ——
L300:             print("FAIL-LOUD: --judge-before 与 --judge-after 必成对", file=sys.stderr)
L321:         print("EUM-VERDICT-%s（EntropyUnsatMark 判例：治必降·治不摇名·旁道零涨·退役不罚）"
L325:     # —— 薄调形 ——
L327:         print("FAIL-LOUD: 缺 --tree <.v 树目录>（或走 --judge-before/--judge-after 判例形）",
L331:         print("FAIL-LOUD: --tree 目录缺失: %s" % args.tree, file=sys.stderr)
L334:         print("FAIL-LOUD: --gate 需配 --baseline（正本 GATE6-USAGE 同律·此处前置）",
